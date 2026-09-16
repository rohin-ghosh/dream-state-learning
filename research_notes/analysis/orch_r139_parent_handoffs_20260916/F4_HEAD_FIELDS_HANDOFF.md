# F4 optional NEXT_GUIDANCE repair — staged, not launched

## Diagnosis and scope

Actual F4 `head_binding` and `build_system` both reproduce
`ValueError: head_fields_keys` using the pinned A4 runtime. The settings contain
the five original fields plus optional NEXT_GUIDANCE (268 UTF-8 bytes).
The settings prompt hash matches, and rendering the five original fields
matches the actual prompt. This is a local compatibility failure, not a model
refusal. The same optional-field policy was already repaired for A2.

The repaired CPU assembly returns BOUND_REQUESTED_SETTINGS with unchanged
prompt bytes and principles/transport contract. It accepts only optional string
NEXT_GUIDANCE <=1024 UTF-8 bytes, appends its exact bound text at the existing
asynchronous-head position, and records its hash and head_waited=false.
Unknown keys, invalid reflection, drifted prompts and unbound settings remain
rejected or report-only as before. No prompt rephrasing, cropping or model retry.

P0323 is preserved MISSING, provider_dispatched=false, retry=false,
prompt_binding=null. Its RESULT SHA256 is
`bbd79ba876204963a63de2fd30075935744ba122be613f77ab1bb77cd4da967e`.
No actual request/transcript or hidden evaluator was read. Diagnostic assembly
uses a synthetic position only. Raw prompt/system content was not exported.

## Ready bytes

- New wrapper: `gpu/orch_r139_grid_head_fields.py`, SHA256 `2401d5708abec95e655bc572cb55122b507f076617eea868526f0312ca0a9262`.
- Tests: `tests/test_orch_r139_grid_head_fields.py`, SHA256 `93a695b87907b9be3f85916c4b511b18e790d5a532a0d9cae218c10fce3932ab`.
- Stage: `/data/home/rohing/courier/runtime/orch_r139_F4_head_fields_source_v1`.
- 14 repository and 14 staged-VM CPU tests passed; actual live-file diagnostic
  passed with prompt/settings/config/principles hashes unchanged before/after.
- Frozen scratch/handoff/timer files unchanged. Same raw scratch, HTTP slots,
  provider, policy, original segment ledger/config, cumulative cap and wall.

## Main-only transition and publication

**Do not change the native child or timer.** Main first publishes this wrapper
and quiesces only the old broker using Main's existing supervision. Wait for its
clean runner-lock release. Do not erase locks, claims, responses or P0323.
No stop/start/signal/dispatch was performed by the sidecar.

### 1. Capture metadata-only repair high-water after old broker is gone

Run from repository on VM. This reads queue filenames and ledger reservation
numbers only; it does not send a request or read a transcript. The native life
continues; later slots above the sampled high-water remain prospective.

```bash
S=/data/home/rohing/courier/runtime/orch_r139_F4_head_fields_source_v1
bash gpu/ovx3_ssh.sh 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -' > "$S/F4_REPAIR_BOUNDARY.json" <<'PY'
import json,re,time
from pathlib import Path
root=Path('/localhome/local-rohing/orch_r115_grid_pair_20260915/F4')
assert not (root/'parent_astra_r139/RUNNER.lock').exists(), 'old_broker_still_owns_lock'
numbers=[]
with (root/'LEDGER.jsonl').open() as stream:
    for line in stream:
        if line.strip():
            row=json.loads(line)
            if row['kind']=='PARENT': numbers.append(row['number'])
for path in (root/'parent_queue').glob('P*.request.json'):
    assert re.fullmatch(r'P[0-9]{4,}\.request\.json',path.name)
    numbers.append(int(path.name.split('.')[0][1:]))
floor=max(numbers)
assert floor>=323
assert not (root/'parent_astra_r139/RUNNER.lock').exists()
print(json.dumps(dict(repair_after_parent=floor,observed_unix=time.time(),old_broker_lock_absent=True,P0323_preserved_no_retry=True)))
PY
```

### 2. Main publishes new broker authorization, preserving initial binding

Copy the existing broker authorization's plan/model/RESUMED/scratch fields;
add this exact wrapper and the sampled high-water. This does NOT change the
original segment allocation or reset its claim count. Wrapper skips every
slot <=repair_after_parent before any queue read; existing claim/response/expiry
guards still apply above that boundary.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import hashlib,json,time
from pathlib import Path
source=Path('/data/home/rohing/courier/runtime/orch_r139_F4_head_fields_source_v1')
old=Path('/data/home/rohing/courier/runtime/orch_r139_F4_broker_source_v1/F4_BROKER_PUBLICATION.json')
wrapper=source/'gpu/orch_r139_grid_head_fields.py'
assert hashlib.sha256(wrapper.read_bytes()).hexdigest()=='2401d5708abec95e655bc572cb55122b507f076617eea868526f0312ca0a9262'
assert hashlib.sha256((source/'F4_PLAN.json').read_bytes()).hexdigest()=='21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546'
boundary=json.loads((source/'F4_REPAIR_BOUNDARY.json').read_text())
assert boundary['old_broker_lock_absent'] and boundary['P0323_preserved_no_retry']
assert 0<=time.time()-boundary['observed_unix']<=120
publication=json.loads(old.read_text())
assert publication['authorized'] is True and publication['published_by']=='Main'
publication.update(modes=['broker'],not_before_unix=time.time(),head_fields_wrapper=dict(path=str(wrapper.resolve()),sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest()),repair_after_parent=boundary['repair_after_parent'],P0323_preserved_no_retry=True)
with (source/'F4_BROKER_PUBLICATION.json').open('x') as stream:
    json.dump(publication,stream,sort_keys=True,indent=2)
print('PUBLICATION_SHA256',hashlib.sha256((source/'F4_BROKER_PUBLICATION.json').read_bytes()).hexdigest())
PY
```

### 3. Main launches once; no child restart and no historical replay

```bash
S=/data/home/rohing/courier/runtime/orch_r139_F4_head_fields_source_v1
REMAINING=$((1789596240-$(date +%s)-4))
test "$REMAINING" -gt 0 && test -f "$S/F4_BROKER_PUBLICATION.json" &&
nohup env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 TMPDIR=/data/home/rohing/courier/runtime timeout --signal=TERM --kill-after=3s "${REMAINING}s" python3 -B "$S/gpu/orch_r139_grid_head_fields.py" broker --expected-self-sha256 2401d5708abec95e655bc572cb55122b507f076617eea868526f0312ca0a9262 --plan "$S/F4_PLAN.json" --plan-sha256 21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546 --publication "$S/F4_BROKER_PUBLICATION.json" > "$S/BROKER.log" 2>&1 < /dev/null &
```

Live success remains unclaimed until Main observes a genuinely new slot above
the repair boundary. No provider call was used to test or select this repair.

Read-only CPU diagnostic, already passed:

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /data/home/rohing/courier/runtime/orch_r139_F4_head_fields_source_v1/gpu/orch_r139_grid_head_fields.py diagnose --expected-self-sha256 2401d5708abec95e655bc572cb55122b507f076617eea868526f0312ca0a9262
```
