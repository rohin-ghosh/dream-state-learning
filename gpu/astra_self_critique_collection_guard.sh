#!/bin/bash
set -eu
test "$#" -eq 12
root="$1"
source_dir="$2"
commit="$3"
index="$4"
uuid="$5"
arm="$6"
initial="$7"
scanner="$8"
exceptions="$9"
lease_end="${10}"
python="${11}"
prepare="${12}"
case "$index:$arm" in
    4:SELF_CRITIQUE_REVISE) ;;
    5:REPEAT_NO_FEEDBACK) ;;
    *) exit 2 ;;
esac
started=$(date +%s)
deadline=$(( started + 7200 ))
test "$(cat "$root/source_commit.txt")" = "$commit"
test -f "$scanner"
test -f "$exceptions"
test -x "$python"
test ! -e "$root/$arm"
mkdir "$root/launch"
trap 'printf "%s\n" "$?" > "$root/launch/exit_code.txt"; date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/finished_utc.txt"' EXIT
export PYTHONPATH="$source_dir" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
env CUDA_VISIBLE_DEVICES= python3 - "$prepare" "$commit" "$lease_end" "$deadline" > "$root/launch/arguments.bin" <<'PY'
import json
from pathlib import Path
import sys
import time
from gpu import astra_self_critique_collection as driver
directory = Path(sys.argv[1])
result = json.loads((directory/'RESULT.json').read_text())
assert not (directory/'FAILED.json').exists()
assert result['schema'] == driver.SCHEMA and result['phase'] == 'prepare'
assert result['status'] == 'PREPARED_NO_MODEL'
assert result['model_calls'] == result['fits'] == result['updates'] == 0
assert result['entry_sha256'] == driver.source.file_hash(driver.__file__)
assert result['protocol_sha256'] == driver.PROTOCOL_SHA
assert result['binding']['helpers'] == driver.helpers()
assert len(sys.argv[2]) == 40 and all(character in '0123456789abcdef' for character in sys.argv[2])
assert time.time() < int(sys.argv[4]) < int(sys.argv[3])-21600
for name in ('bundle', 'bundle_sha', 'model_dir', 'exposure'):
    for value in ('--'+name.replace('_', '-'), result['arguments'][name]):
        assert '\0' not in value
        sys.stdout.buffer.write(value.encode()+b'\0')
PY
mapfile -d '' -t common < "$root/launch/arguments.bin"
printf '%s\n' "$$" > "$root/launch/guardian_pid.txt"
printf '%s\n' "$commit" > "$root/launch/source_commit.txt"
printf '%s\n' "$deadline" > "$root/launch/deadline_epoch.txt"
printf '%s\n' "$lease_end" > "$root/launch/lease_end_epoch.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/started_utc.txt"
admit() {
    label="$1"
    env CUDA_VISIBLE_DEVICES= timeout 30 python3 "$scanner" "$index" "$uuid" < "$exceptions" > "$root/launch/resource_$label.json"
}
run_phase() {
    phase="$1"
    destination="$2"
    shift 2
    admit "$phase"
    now=$(date +%s)
    native_deadline=$(( deadline - 60 ))
    if test "$native_deadline" -gt "$(( now + 6900 ))"; then native_deadline=$(( now + 6900 )); fi
    remaining=$(( native_deadline - now ))
    test "$remaining" -gt 0
    env CUDA_VISIBLE_DEVICES="$uuid" timeout --signal=INT --kill-after=60 "$remaining" "$python" -B -m gpu.astra_self_critique_collection \
        "${common[@]}" --gpu-uuid "$uuid" --deadline-epoch "$native_deadline" --phase "$phase" --output "$destination" "$@"
}
test "$(( $(date +%s) - started ))" -le 240
if test "$arm" = SELF_CRITIQUE_REVISE; then
    test ! -e "$initial"
    run_phase COMMON_INITIAL "$initial"
else
    while test ! -f "$initial/RESULT.json"; do
        test ! -f "$initial/FAILED.json"
        test "$(date +%s)" -lt "$(( deadline - 60 ))"
        sleep 5
    done
fi
env CUDA_VISIBLE_DEVICES= timeout 120 python3 -B -m gpu.astra_self_critique_collection \
    "${common[@]}" --phase prepare --initial "$initial" --output "$root/prepare_arm"
run_phase "$arm" "$root/$arm" --initial "$initial"
date -u +%Y-%m-%dT%H:%M:%SZ > "$root/launch/completed_utc.txt"
