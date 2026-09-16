# F4 scratch-only broker wrapper — ready for Main publication

No broker/provider launch, queue read, claim, signal, Git or shared-ledger write
was performed. Main alone handles timer/release/admission/resume.

## Pins and changes

- Wrapper SHA256: `790d65d1e69b4dd6d514ed3572fb458b1e7d6d748cea3feddd373333e6b3300b`.
- Tests SHA256: `6c4a1f352baec21bab2e1ed31de7614851cb6c1f7bb29a9302fdf5bea098a2f4`.
- Existing plan SHA256: `21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546`.
- VM stage: `/data/home/rohing/courier/runtime/orch_r139_F4_broker_source_v1`.
- Raw scratch: `/data/home/rohing/courier/runtime/orch_r139_F4_broker_scratch_v1`.

Three exact constant substitutions in fresh function objects only:
1. Existing broker buffer allocator `/tmp` → private raw scratch.
2. Existing Astra evaluator directory gate `/tmp` → that same scratch.
3. Existing 10-GiB disk-floor probe `/` → scratch filesystem; threshold unchanged.

Provider request/response bodies, prompts, error responses, binding files and
temporary archive inputs follow the supplied call/buffer directories. Successful
archive verification and cleanup remain unchanged; failure scratch is retained
under the new root. Publication/config/log files also use courier/runtime.

Frozen handoff, timer and existing A4 files are unchanged. This wrapper retains
the original HTTP slots at `/tmp/orch_astra_http_slots/{0,1,2,3}`: these are empty
shared coordination locks, **not raw transcripts**. Moving them independently
would incorrectly create a second concurrency pool. Frozen `/tmp` source reads
remain unchanged; no provider configuration or credential was read during tests.

No prompt, model, effort, token cap, timeout, visibility, claim/history, deadline
or retry policy changes. Original 298 Claude claims and the initial prospective
boundary remain authoritative; Astra segment allocation remains the existing
cumulative ceiling minus the actual initial handoff high-water.

13 repository CPU tests and 13 staged-runtime CPU tests passed against the actual
pinned VM transport, including synthetic raw writes, scratch escapes, refusal
without retry, historical-request exclusion, exact constant diffs, shared slots,
real serve allocation and unchanged disk threshold. Staged `check` reports
`CPU_COMPILED_NO_DISPATCH`; it creates no actual broker scratch directory.

## Exact Main publication and launch — NOT executed by sidecar

Run only after Main publishes the wrapper bytes and completes actual F4 native
restoration. Do not start broker before `initial-resume` has produced RESUMED.
The callback verifies the current actual native PID and its source identity.
These commands do not change any timer/release/resume files.

### 1. Capture verified actual current-native reference

Run from the repository on the VM; output is compact metadata, not transcripts.

```bash
S=/data/home/rohing/courier/runtime/orch_r139_F4_broker_source_v1
bash gpu/ovx3_ssh.sh 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /localhome/local-rohing/orch_r139_F4_timer_source_v1/gpu/orch_r139_grid_timer_custody.py current --expected-self-sha256 8dd31979a4ca1cafbf2a3dc9d7724adf2cb5ccb4c25610480d0add2730ebc10a --plan /localhome/local-rohing/orch_r139_F4_timer_source_v1/F4_TIMER_PLAN.json --plan-sha256 e09bd25ca7bca2089526a966ce1a34e678d350793911e3ea32ef262d0727d6b3 --publication /localhome/local-rohing/orch_r139_F4_timer_source_v1/F4_TIMER_PUBLICATION.json' > "$S/F4_CURRENT_NATIVE.json"
```

If this fails, **do not publish or launch broker**. No fallback to a startup,
timeout-wrapper, released or unverified PID. This recipe is the first broker
launch after initial restoration, not an automatic later restart.

### 2. Main publishes separate broker authorization

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import hashlib,json,time
from pathlib import Path
source=Path('/data/home/rohing/courier/runtime/orch_r139_F4_broker_source_v1')
wrapper=source/'gpu/orch_r139_grid_broker_scratch.py'
plan_path=source/'F4_PLAN.json'
assert hashlib.sha256(wrapper.read_bytes()).hexdigest()=='790d65d1e69b4dd6d514ed3572fb458b1e7d6d748cea3feddd373333e6b3300b'
assert hashlib.sha256(plan_path.read_bytes()).hexdigest()=='21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546'
plan=json.loads(plan_path.read_text())
current=json.loads((source/'F4_CURRENT_NATIVE.json').read_text())
assert current['role']=='initial' and current['parent_model']==plan['requested_model']
assert current['checkpoint']==plan['references']['checkpoint']
assert current['restored_receipt']['path']==plan['output']+'/RESUMED.json'
assert current['controller_source']['sha256']=='8dd31979a4ca1cafbf2a3dc9d7724adf2cb5ccb4c25610480d0add2730ebc10a'
publication=dict(authorized=True,published_by='Main',plan_sha256='21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546',approved_intake=plan['approved_intake'],requested_scope=plan['requested_scope'],modes=['broker'],not_before_unix=time.time(),new_parent_model=plan['requested_model'],no_reset=True,no_historical_redispatch=True,resumed=current['restored_receipt'],scratch_wrapper=dict(path=str(wrapper.resolve()),sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest()),raw_scratch_root='/data/home/rohing/courier/runtime/orch_r139_F4_broker_scratch_v1',shared_HTTP_slots_unchanged=True)
with (source/'F4_BROKER_PUBLICATION.json').open('x') as stream:
    json.dump(publication,stream,sort_keys=True,indent=2)
print('F4_BROKER_PUBLICATION_SHA256',hashlib.sha256((source/'F4_BROKER_PUBLICATION.json').read_bytes()).hexdigest())
PY
```

The frozen broker rechecks the referenced actual RESUMED/boundary, old config,
budget, source pins, consumer model/checkpoint and absence of the old Claude
runner lock. It preserves historical/missing/expired/disposed exclusions.
The new scratch binding is checked both at startup and by per-call authorization.

### 3. Launch once under the existing hard wall

```bash
S=/data/home/rohing/courier/runtime/orch_r139_F4_broker_source_v1
REMAINING=$((1789596240-$(date +%s)-4))
test "$REMAINING" -gt 0 && test -f "$S/F4_BROKER_PUBLICATION.json" &&
nohup env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 TMPDIR=/data/home/rohing/courier/runtime timeout --signal=TERM --kill-after=3s "${REMAINING}s" python3 -B "$S/gpu/orch_r139_grid_broker_scratch.py" broker --expected-self-sha256 790d65d1e69b4dd6d514ed3572fb458b1e7d6d748cea3feddd373333e6b3300b --plan "$S/F4_PLAN.json" --plan-sha256 21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546 --publication "$S/F4_BROKER_PUBLICATION.json" > "$S/BROKER.log" 2>&1 < /dev/null &
```

No automatic retry or reset on failure. Preserve scratch and node-local claim
receipts for inspection. Existing per-lane runner lock prevents a second broker.

Read-only staged compile check (already passed):

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /data/home/rohing/courier/runtime/orch_r139_F4_broker_source_v1/gpu/orch_r139_grid_broker_scratch.py check --expected-self-sha256 790d65d1e69b4dd6d514ed3572fb458b1e7d6d748cea3feddd373333e6b3300b
```
