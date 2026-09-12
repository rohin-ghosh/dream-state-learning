#!/usr/bin/env bash
set -euo pipefail
set -C

usage() {
    printf '%s\n' \
      'Usage: astra_capture_replications_20260912.sh --repo DIR --capture-dir NEW_LOCAL_DIR --remote-capsule-dir NEW_REMOTE_DIR [--source-archive FILE]' \
      'Checks existing terminal/cleanup receipts once; hashes remote adapters; captures both fixed seed1/2 roots excluding weights.' \
      'No launch, polling loop, GPU query, kill, or reservation release. Destinations must not exist.'
}

repo=
capture=
remote_capsule=
source_archive=/tmp/astra_mini_sudoku_source_bc4250ed.tar
while (($#)); do
    case "$1" in
        --repo|--capture-dir|--remote-capsule-dir|--source-archive)
            if (($# < 2)); then usage >&2; exit 2; fi
            case "$1" in
                --repo) repo=$2 ;;
                --capture-dir) capture=$2 ;;
                --remote-capsule-dir) remote_capsule=$2 ;;
                --source-archive) source_archive=$2 ;;
            esac
            shift 2
            ;;
        --help|-h) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done
if [[ -z "$repo" || -z "$capture" || -z "$remote_capsule" ]]; then usage >&2; exit 2; fi
test ! -e "$capture" && test ! -L "$capture"
test -f "$source_archive"
printf -v remote_command 'bash -se -- %q' "$remote_capsule"
timeout 180 bash "$repo/gpu/ovx2_ssh.sh" "$remote_command" <<'REMOTE'
set -eu
set -C
umask 077
base=/localhome/local-rohing/astra_diagnostics
capsule=$1
test ! -e "$capsule" && test ! -L "$capsule"
python3 -B - <<'PY'
import json
from pathlib import Path
base = Path('/localhome/local-rohing/astra_diagnostics')
for seed, device in ((1, '1'), (2, '3')):
    root = base / f'astra_mini_sudoku_seed{seed}_20260912_attempt1'
    def read(relative):
        return json.loads((root / relative).read_text())
    paired = read('logs/paired/result.json')
    assert paired['status'] == 'BOTH_ARMS_COMPLETED' and paired['training_seed'] == seed
    assert not (root / 'logs/paired/failure.json').exists()
    launch = read('logs/paired/launch_receipt.json')
    assert launch['training_seed'] == seed and launch['device'] == device
    assert launch['selection'] == 'paired' and launch['same_device_sequential_arms'] is True
    for arm in ('useful', 'corrupt'):
        result = read(f'logs/{arm}/result.json')
        assert result['status'] == 'COMPLETED' and result['training_seed'] == seed
        assert read(f'probes/{arm}/PAIR_DONE.json')['evidence_label'] == 'EVALUATION_ONLY'
        for operation in ('train', 'pair'):
            cleanup = read(f'logs/{arm}/{operation}.cleanup.json')
            assert cleanup['device'] == device and cleanup['cleanup_error'] is None
            assert all(cleanup[key] is True for key in
                       ('owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
    print('TERMINAL_NATIVE_LABELS', seed, paired['finished_utc'])
PY
mkdir "$capsule"
python3 -B - > "$capsule/remote_adapter_rehash.json" <<'PY'
import datetime
import hashlib
import json
from pathlib import Path
base = Path('/localhome/local-rohing/astra_diagnostics')
records = []
def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()
for seed in (1, 2):
    root = base / f'astra_mini_sudoku_seed{seed}_20260912_attempt1'
    for arm in ('useful', 'corrupt'):
        spec_path = root / f'logs/{arm}/probe_spec.json'
        spec_hash = digest(spec_path)
        spec = json.loads(spec_path.read_text())
        adapter = root / f'training/{arm}_seed{seed}'
        assert spec['adapter_path'] == str(adapter)
        expected = spec['expected_adapter_hashes']
        assert len(set(expected) & {'adapter_model.safetensors', 'adapter_model.bin'}) == 1
        actual = {}
        for name, expected_hash in expected.items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts
            path = adapter / relative
            assert path.is_file() and not path.is_symlink()
            actual[name] = digest(path)
            assert actual[name] == expected_hash, (seed, arm, name, 'hash mismatch')
        assert digest(spec_path) == spec_hash
        records.append(dict(training_seed=seed, arm=arm, adapter_path=str(adapter),
                            spec_sha256=spec_hash, expected_adapter_hashes=expected,
                            actual_adapter_hashes=actual))
print(json.dumps(dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='Remote CPU byte rehash after terminal markers; not loaded-runtime authentication',
    records=records), indent=2, sort_keys=True))
PY
tar --exclude='adapter_model.safetensors' --exclude='adapter_model.bin' \
    -czf "$capsule/runs.tgz" -C "$base" \
    astra_mini_sudoku_seed1_20260912_attempt1 \
    astra_mini_sudoku_seed2_20260912_attempt1
(cd "$capsule" && sha256sum runs.tgz remote_adapter_rehash.json > SHA256SUMS)
printf 'CAPSULE_READY %s\n' "$capsule"
REMOTE

mkdir "$capture"
timeout 120 bash "$repo/gpu/ovx2_scp.sh" \
    "NODE:$remote_capsule/runs.tgz" \
    "NODE:$remote_capsule/remote_adapter_rehash.json" \
    "NODE:$remote_capsule/SHA256SUMS" "$capture/"
(cd "$capture" && sha256sum -c SHA256SUMS)
tar -tzf "$capture/runs.tgz"
tar --no-same-owner -xzf "$capture/runs.tgz" -C "$capture"
cp "$source_archive" "$capture/"
sha256sum "$capture/$(basename "$source_archive")"
printf 'CAPTURE_READY %s\n' "$capture"
