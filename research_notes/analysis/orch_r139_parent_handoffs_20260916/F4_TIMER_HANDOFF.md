# F4 successor timer custody — staged, not armed

2026-09-16 03:01 UTC handoff. **No timer/child signals, model calls or runtime
controller launches performed.** 22 local and 22 native CPU tests passed.
Node preflight and exact-plan validation passed. Both original timers were
live and the original morning FINAL remained unattempted at preflight.

## Pins and concrete seam

- Timer: `8dd31979a4ca1cafbf2a3dc9d7724adf2cb5ccb4c25610480d0add2730ebc10a`.
- Tests: `6ccdd01d8542f1743ae051de9074282c2f529e50f171d1a7778ad47d3cbb78ff`.
- Timer plan: `e09bd25ca7bca2089526a966ce1a34e678d350793911e3ea32ef262d0727d6b3`.
- Frozen handoff/plan remain `adc2598e89e3917840129c319a58de122ebda832af7e1acae3dce77562c3c778` / `21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546`.
- Node source: `/localhome/local-rohing/orch_r139_F4_timer_source_v1`.
- VM staging/logs: `/data/home/rohing/courier/runtime/orch_r139_F4_timer_source_v1`.
- Live receipt, **only after authorized arm**: `/localhome/local-rohing/orch_r115_grid_pair_20260915/F4/r139_timer_custody_v1/ARMED.json`.

`arm` retires only old timer identities 3545939/3545940 with pidfd checks and
observed exits. It does not release the child. It then supervises initial
restoration, morning readout, post-readout restoration and the original wall.
Partial retirement never emits ARMED; controller retains wall custody.

**Use `initial-resume`, not the previous bare frozen resume command.** It
registers the actual Python/native PID and exact source identity before calling
the unchanged frozen resume implementation. `current` resolves the actual
restored native identity; it never returns a timeout wrapper or startup PID.

At 06:00 UTC the original inotify/completed-two-episode/carry release function
targets that actual successor. The morning plan changes only predecessor
identity; the original PLAN is untouched. Original FINAL event directory,
irrevocable claim, 8-call quota, held panel/prompt/decoder, empty StageContext,
no parent/carry, 06:20 evaluation end, 22:02 TRAIN end and 22:04 hard wall remain.
Original evaluate/resume function code objects are reused with explicit bound
callbacks. Post-FINAL training preserves Astra, frozen LoRA, cumulative caps,
carry/cycle, original mailbox and **initial** prospective parent boundary.
No live optimizer/RNG restoration is claimed; this remains frozen elicitation.

One morning attempt, one evaluation launch, one restoration; no model retry.
Failed capture still allows the one authorized same-life restoration. A prior
FINAL claim prevents capture/release. Missing initial restored actor at 06:00
fails closed without capture; wall custody remains. Loading/evaluation actors
are registered before model loading and independently deadline-wrapped.

## Main commands — NOT executed by sidecar

Only after Main publishes these exact bytes. All commands run through the
existing node5 wrapper; all new runtime raw remains node-local. VM files/logs
must stay under `/data/home/rohing/courier/runtime`, not VM `/tmp`.

### 1. Publish timer handshake and arm CPU custody

```bash
bash gpu/ovx3_ssh.sh 'bash -s' <<'NODE'
set -euo pipefail
S=/localhome/local-rohing/orch_r139_F4_timer_source_v1
T=$S/gpu/orch_r139_grid_timer_custody.py
test "$(sha256sum "$T" | cut -d' ' -f1)" = 8dd31979a4ca1cafbf2a3dc9d7724adf2cb5ccb4c25610480d0add2730ebc10a
test "$(sha256sum "$S/F4_TIMER_PLAN.json" | cut -d' ' -f1)" = e09bd25ca7bca2089526a966ce1a34e678d350793911e3ea32ef262d0727d6b3
python3 -B - <<'PY'
import json,time
from pathlib import Path
root=Path('/localhome/local-rohing/orch_r139_F4_timer_source_v1')
document=json.loads((root/'F4_TIMER_PUBLICATION_TEMPLATE.json').read_text())
assert document['authorized'] is False
document.update(authorized=True, published_by='Main', not_before_unix=time.time())
with (root/'F4_TIMER_PUBLICATION.json').open('x') as stream:
    json.dump(document,stream,sort_keys=True,indent=2)
PY
nohup env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B "$T" arm --expected-self-sha256 8dd31979a4ca1cafbf2a3dc9d7724adf2cb5ccb4c25610480d0add2730ebc10a --plan "$S/F4_TIMER_PLAN.json" --plan-sha256 e09bd25ca7bca2089526a966ce1a34e678d350793911e3ea32ef262d0727d6b3 --publication "$S/F4_TIMER_PUBLICATION.json" > "$S/TIMER.log" 2>&1 < /dev/null &
NODE
```

### 2. Bind actual ARMED and release at next durable completed cycle

Do not repeat after any BOUNDARY/RELEASED artifact or error without inspection.
This uses the unchanged 600-second release window, not a call replay.

```bash
bash gpu/ovx3_ssh.sh 'bash -s' <<'NODE'
set -euo pipefail
S=/localhome/local-rohing/orch_r139_F4_timer_source_v1
H=/tmp/orch_r139_F4_handoff_v1
python3 -B - <<'PY'
import hashlib,json,time
from pathlib import Path
source=Path('/localhome/local-rohing/orch_r139_F4_timer_source_v1')
frozen=json.loads(Path('/tmp/orch_r139_F4_handoff_v1/F4_PLAN.json').read_text())
timer=Path(frozen['root'])/'r139_timer_custody_v1/ARMED.json'
for attempt in range(30):
    if timer.exists(): break
    time.sleep(1)
assert json.loads(timer.read_text())['status']=='ARMED_SUCCESSOR_AWARE'
document=dict(authorized=True,published_by='Main',plan_sha256='21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546',approved_intake=frozen['approved_intake'],requested_scope=frozen['requested_scope'],modes=['release'],not_before_unix=time.time(),new_parent_model=frozen['requested_model'],no_reset=True,no_historical_redispatch=True,timer_custody=dict(path=str(timer),sha256=hashlib.sha256(timer.read_bytes()).hexdigest()))
with (source/'F4_RELEASE_PUBLICATION.json').open('x') as stream:
    json.dump(document,stream,sort_keys=True,indent=2)
PY
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B "$H/gpu/orch_r139_grid_astra_handoff.py" release --expected-self-sha256 adc2598e89e3917840129c319a58de122ebda832af7e1acae3dce77562c3c778 --plan "$H/F4_PLAN.json" --plan-sha256 21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546 --publication "$S/F4_RELEASE_PUBLICATION.json" > "$S/RELEASE.log" 2>&1
NODE
```

### 3. Fresh admission, then source-registered initial successor

Only after actual RELEASED. Admission is checked again by frozen resume;
false/foreign/stale reports cannot authorize loading. No fresh model call is
performed by the scan. Run this promptly so its 120-second freshness holds.

```bash
bash gpu/ovx3_ssh.sh 'bash -s' <<'NODE'
set -euo pipefail
S=/localhome/local-rohing/orch_r139_F4_timer_source_v1
test -f /localhome/local-rohing/orch_r115_grid_pair_20260915/F4/r139_astra_handoff_v1/RELEASED.json
test ! -e "$S/F4_RESUME_ADMISSION.json"
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /localhome/local-rohing/orch_r119_grid_independent_source_20260915_v1/gpu/orch_r119_grid_independent.py scan --branch F4 > "$S/F4_RESUME_ADMISSION.json"
python3 -B - <<'PY'
import hashlib,json,time
from pathlib import Path
source=Path('/localhome/local-rohing/orch_r139_F4_timer_source_v1')
admission=source/'F4_RESUME_ADMISSION.json'
report=json.loads(admission.read_text())
assert report['clear'] is True and report['scanner_euid']==0 and not report['blocking_reasons']
document=json.loads((source/'F4_RELEASE_PUBLICATION.json').read_text())
document.update(modes=['resume'],not_before_unix=time.time(),admission_observed_unix=time.time(),resume_admission=dict(path=str(admission),sha256=hashlib.sha256(admission.read_bytes()).hexdigest()))
with (source/'F4_RESUME_PUBLICATION.json').open('x') as stream:
    json.dump(document,stream,sort_keys=True,indent=2)
PY
GPU_UUID=$(python3 -B -c 'import json; print(json.load(open("/localhome/local-rohing/orch_r115_grid_pair_20260915/F4/CONFIG.json"))["uuid"])')
REMAINING=$((1789596240-$(date +%s)-4)); test "$REMAINING" -gt 0
nohup env CUDA_VISIBLE_DEVICES="$GPU_UUID" PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=3s "${REMAINING}s" /localhome/local-rohing/v2/venv/bin/python -B "$S/gpu/orch_r139_grid_timer_custody.py" initial-resume --expected-self-sha256 8dd31979a4ca1cafbf2a3dc9d7724adf2cb5ccb4c25610480d0add2730ebc10a --plan "$S/F4_TIMER_PLAN.json" --plan-sha256 e09bd25ca7bca2089526a966ce1a34e678d350793911e3ea32ef262d0727d6b3 --publication "$S/F4_TIMER_PUBLICATION.json" --handoff-publication "$S/F4_RESUME_PUBLICATION.json" > "$S/INITIAL_RESUME.log" 2>&1 < /dev/null &
NODE
```

### 4. Read-only current-native callback

Use after restoration, and after morning restoration. It returns actual
identity plus source/checkpoint/RESUMED hashes, or fails if absent/ambiguous.

```bash
bash gpu/ovx3_ssh.sh 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /localhome/local-rohing/orch_r139_F4_timer_source_v1/gpu/orch_r139_grid_timer_custody.py current --expected-self-sha256 8dd31979a4ca1cafbf2a3dc9d7724adf2cb5ccb4c25610480d0add2730ebc10a --plan /localhome/local-rohing/orch_r139_F4_timer_source_v1/F4_TIMER_PLAN.json --plan-sha256 e09bd25ca7bca2089526a966ce1a34e678d350793911e3ea32ef262d0727d6b3 --publication /localhome/local-rohing/orch_r139_F4_timer_source_v1/F4_TIMER_PUBLICATION.json'
```

Remaining boundary: **Main publication → real ARMED → real durable RELEASED →
fresh same-GPU admission → actual source-registered RESUMED**. No unspecified
timer receipt remains. Subsequent morning phases are handled once by this
published custody, without another model retry or manual model launch.
Broker publication remains separately Main-owned; no broker is launched or
modified here, including its existing VM temporary-storage policy.
