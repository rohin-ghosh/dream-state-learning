# F4 C112 continuation — ready for Main review/publication

Non-material R121 Level1 repair; no launch, signal, model, environment or parent
call performed by this sidecar. Frozen handoff, timer, normalizer, run files and
shared ledgers are unchanged. This is not a new life or new benchmark score.

## Exact proof and pins

- Source `gpu/orch_r140_grid_continuation.py`: `e6ac3af556de61dbd02278e6510814f6ea1b90cdd4e6fa004aa8faa4fc76aead`.
- Tests `tests/test_orch_r140_grid_continuation.py`: `7f114077790ce625712df6679964cc510e51ec6cc0422984d21fd5ad15803489`.
- Stage `/localhome/local-rohing/orch_r140_F4_continuation_source_v1`.
- Node-local `F4_CONTINUATION_PLAN.json`: `5a61a47f21ad90c6729f065d677b277611552dfc84a28a8a029495e716309cac`.
- Compact proof: `F4_CONTINUATION_PROOF.json` alongside this document. Full 355-file input hash manifest remains node-local in the plan.

21 continuation tests pass locally and against staged/frozen node sources;
57 combined local tests pass (21 continuation + 14 normalizer + 22 original
timer). Exact frozen `train_cycle` reuses 32 COMPLETE responses and 32 saved
environment receipts, with no transition/model/mailbox replay, reaching exactly
N04456's messages at task16 step16. Both experience ask receipts are reused;
the completed first open ask reconstructs only source-guaranteed direct null
guidance, not an invented timestamp or receipt. Full next-message equality proves
this projection sufficient for the native frontier.

The **actual frozen grid.Life.calls**, real tokenizer, and in-memory dispatch
stub prove STARTED and COMPLETE recorded messages equal dispatched normalized
messages: **16020 → 8338 tokens, cap384 unchanged**, originals reconstructible.
This is CPU integration evidence, not an actual model dispatch. N04456 bytes and
all 355 bound inputs are unchanged; cumulative ledger remains NATIVE4456/PARENT324.

## Same-life seam and timer

At Main launch, CPU proof/hash checks run again before model load; existing
frozen LoRA is loaded without optimizer and historical files are checked again.
OLD_CARRY is archived in the new node-local continuation directory. N04456 stays
STARTED and charged; a separate `FAILED_PREDISPATCH.json` records the overflow.
The missing frontier takes **new N04457**. No P0323/P0324 replay or mailbox poll
at that exact frontier; all subsequent mailbox calls retain **first_parent325**.
The already-running prospective Astra broker is neither relaunched nor modified.
Caps come from the unchanged existing LEASE_BUDGET; no cap allocation is added.
Live RNG state was not saved and is not claimed restored.

New timer namespace reuses frozen R139 timer primitives, with source-bound actual
INITIAL/evaluate/resume actor identities and new `current` callback. It retires
only the exact currently bound R139 controller, not original historical timers.
The original FINAL namespace, empty context, parent absence, eight-call quota,
06:00 trigger, 06:20 evaluation end, 22:02 TRAIN end and 22:04 hard wall on
September 16, 2026 UTC are unchanged. Only N04456 may be explicitly retired as
failed at a durable C112 boundary; any other STARTED call blocks release.
Post-FINAL resume retains normalization and parent floor325; evaluation is not
normalized. No second FINAL attempt or automatic model retry is added.

## Main-only exact sequence — NOT executed by sidecar

Remaining boundary: **Main publishes exact source/plan → one fresh clear F4
admission → one immutable publication → new timer ARMED (old timer retired) →
one continuation launch → actual source-registered RESUMED/current**.
The failed actor is already gone: do not release/stop a child again. Keep the
same publication bytes for timer and continuation: custody binds their hash.
Admission must still be younger than120 seconds when continuation checks it.
Do not automatically rerun a failed step or regenerate publication after arming.
If freshness expires or any stage fails, inspect and obtain Main's next decision.

After Main publication only, run this once through the existing node wrapper.
All outputs are node-local; any VM-side logs must use
`/data/home/rohing/courier/runtime`, never VM `/tmp`.

```bash
bash gpu/ovx3_ssh.sh 'bash -s' <<'NODE'
set -euo pipefail
set -C
S=/localhome/local-rohing/orch_r140_F4_continuation_source_v1
T=$S/gpu/orch_r140_grid_continuation.py
P=$S/F4_CONTINUATION_PLAN.json
U=$S/F4_CONTINUATION_PUBLICATION.json
R=/localhome/local-rohing/orch_r115_grid_pair_20260915/F4
SOURCE_SHA=e6ac3af556de61dbd02278e6510814f6ea1b90cdd4e6fa004aa8faa4fc76aead
PLAN_SHA=5a61a47f21ad90c6729f065d677b277611552dfc84a28a8a029495e716309cac
test "$(sha256sum "$T" | cut -d' ' -f1)" = "$SOURCE_SHA"
test "$(sha256sum "$P" | cut -d' ' -f1)" = "$PLAN_SHA"
test ! -e "$R/r140_continuation_v1"
test ! -e "$R/r140_timer_custody_v1"
test ! -e "$U"
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B \
  /localhome/local-rohing/orch_r119_grid_independent_source_20260915_v1/gpu/orch_r119_grid_independent.py \
  scan --branch F4 > "$S/F4_CONTINUATION_ADMISSION.json"
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import hashlib, json, time
from pathlib import Path
stage = Path('/localhome/local-rohing/orch_r140_F4_continuation_source_v1')
def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
plan_path = stage / 'F4_CONTINUATION_PLAN.json'
plan = json.loads(plan_path.read_text())
admission_path = stage / 'F4_CONTINUATION_ADMISSION.json'
admission = json.loads(admission_path.read_text())
assert admission['clear'] is True and admission['scanner_euid'] == 0 and not admission['blocking_reasons']
config = json.loads((Path(plan['root']) / 'CONFIG.json').read_text())
assert admission['gpu']['uuid'] == config['uuid']
now = time.time()
publication = dict(authorized=True, published_by='Main', timer_plan=ref(plan_path),
    controller_source=plan['controller_source'], actions=plan['actions'],
    approved_intake=plan['approved_intake'], requested_scope=plan['requested_scope'],
    not_before_unix=now, hard_end_unix=plan['hard_end_unix'],
    R140_C112_continuation=True, normalizer=plan['normalizer'],
    continuation_admission=ref(admission_path), admission_observed_unix=now)
with (stage / 'F4_CONTINUATION_PUBLICATION.json').open('x') as stream:
    json.dump(publication, stream, sort_keys=True, indent=2)
PY
nohup env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B "$T" timer \
  --expected-self-sha256 "$SOURCE_SHA" --plan "$P" --plan-sha256 "$PLAN_SHA" \
  --publication "$U" > "$S/F4_TIMER.log" 2>&1 < /dev/null &
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import hashlib, json, time
from pathlib import Path
stage = Path('/localhome/local-rohing/orch_r140_F4_continuation_source_v1')
plan = json.loads((stage / 'F4_CONTINUATION_PLAN.json').read_text())
armed_path = Path(plan['output']) / 'ARMED.json'
for attempt in range(20):
    if armed_path.exists():
        break
    time.sleep(1)
armed = json.loads(armed_path.read_text())
assert armed['status'] == 'ARMED_SUCCESSOR_AWARE'
assert armed['controller_source'] == plan['controller_source']
publication = stage / 'F4_CONTINUATION_PUBLICATION.json'
assert armed['timer_publication']['sha256'] == hashlib.sha256(publication.read_bytes()).hexdigest()
assert time.time() - json.loads(publication.read_text())['admission_observed_unix'] < 120
PY
GPU_UUID=$(python3 -B -c 'import json; print(json.load(open("/localhome/local-rohing/orch_r115_grid_pair_20260915/F4/CONFIG.json"))["uuid"])')
REMAINING=$((1789596240-$(date +%s)-4)); test "$REMAINING" -gt 0
nohup env CUDA_VISIBLE_DEVICES="$GPU_UUID" PYTHONDONTWRITEBYTECODE=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  timeout --signal=TERM --kill-after=3s "${REMAINING}s" \
  /localhome/local-rohing/v2/venv/bin/python -B "$T" continue \
  --expected-self-sha256 "$SOURCE_SHA" --plan "$P" --plan-sha256 "$PLAN_SHA" \
  --publication "$U" > "$S/F4_CONTINUE.log" 2>&1 < /dev/null &
NODE
```

Only after `r140_continuation_v1/RESUMED.json` exists, verify the actual actor
with the read-only callback (also valid after morning restoration):

```bash
bash gpu/ovx3_ssh.sh 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /localhome/local-rohing/orch_r140_F4_continuation_source_v1/gpu/orch_r140_grid_continuation.py current --expected-self-sha256 e6ac3af556de61dbd02278e6510814f6ea1b90cdd4e6fa004aa8faa4fc76aead --plan /localhome/local-rohing/orch_r140_F4_continuation_source_v1/F4_CONTINUATION_PLAN.json --plan-sha256 5a61a47f21ad90c6729f065d677b277611552dfc84a28a8a029495e716309cac --publication /localhome/local-rohing/orch_r140_F4_continuation_source_v1/F4_CONTINUATION_PUBLICATION.json'
```

After actual execution, Main should inspect only compact metadata: N04456 hash
unchanged, N04457 fresh with lossless metadata, sent/recorded token counts,
preserved cumulative counters, actual current actor, and future parent delivery.
No raw transcript or sealed evaluator inspection is required.
