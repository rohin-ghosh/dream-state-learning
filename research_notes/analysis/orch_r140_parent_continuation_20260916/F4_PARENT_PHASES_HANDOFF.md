# F4 TRAIN parent phase routing — staged, not launched

Non-material request-routing repair, R121 Level1 only. Child and timer untouched.
The frozen native producer legitimately asks `experience`, `open_turn`, and
`presleep_metacognition`; the frozen transport already validates those phases.
R139's narrower `prospective()` rejects the latter two at preclaim and evaluator
guards. This wrapper binds exactly those three phases at **both actual production
sites**, retaining head-field repair, Astra transport/model, floor324, original
segment ledger/allocation, cap1024/low policy, scratch, shared HTTP slots, prompt
bytes, cutoff and wall. `reflection` remains unsupported as a parent request.

## Pins and evidence

- Source `gpu/orch_r140_grid_parent_phases.py`: `8e352fed5539dd3eabf66c5dc59942e581bd9d8081a2109ec1b75b14115bc4c2`.
- Tests `tests/test_orch_r140_grid_parent_phases.py`: `0a0a65d1376554e8e65fb7bedb4440db4c86c01490f6181f6a41bc3f01379ddd`.
- VM stage `/data/home/rohing/courier/runtime/orch_r140_F4_parent_phases_source_v1`.
- Staged frozen `F4_PLAN.json`: `21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546`.
- Existing head wrapper SHA `2401d5708abec95e655bc572cb55122b507f076617eea868526f0312ca0a9262`.
- Previous live publication observed SHA `aff2fda6abd21b4d340a09ff52b8a4451029cdee0d38b9c977c9dce49ea1fdc7`.
- Actual R140 native RESUMED SHA `e8cb6f3cd4bcc676b335a237c15dcb7703d5be30713d3b952aae531c6f74853d`.
- **13 local + 13 staged CPU tests PASS**. Production factory tests exercise all three preclaim routes, verify evaluator binding, unchanged prompt assembly, historical floor, expired/unknown/DEV/FINAL rejection, any prior claim/response/disposition rejection, unchanged cap ceiling, and immutable previous-publication binding.
- Staged `check` PASS; zero provider calls, signals, broker launches or prompt changes by sidecar.

P0325 metadata-only inspection found C112/open_turn/TRAIN, no Claude/Astra claim,
no received disposition and no response. Request SHA
`a32d24c2e7d72c320535bc29965aff02ced7a2a9c6ed522a13362f29c289aa0f`.
Its original deadline is `1789531296.494066`; dispatch cutoff is 30 seconds
earlier, approximately **September 16, 2026 04:01:06 UTC**. Eligibility is checked
again live at both guards. If elapsed, **leave P0325 unchanged and skip it**;
only future eligible requests may dispatch. Never advance the repair floor to325:
the unchanged authorized floor is324. This is not a refused/MISSING request retry.

## Main-only replacement — not executed

Main publishes exact source/tests/doc first. Then archive the old authorization
bytes **before** atomically revoking the old live publication, let its existing
poll/finally release the runner lock, create a new authorization in the new stage,
and launch once. No child/timer operation, direct provider call, lock deletion,
claim deletion, re-enqueue or prompt mutation is involved. If quiescence fails,
stop here for Main inspection; do not force-clear the lock or auto-retry.

### 1. Preserve old publication, then revoke only that broker authorization

Run on VM from this worktree, once, after publication:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import hashlib,json,os
from pathlib import Path
stage=Path('/data/home/rohing/courier/runtime/orch_r140_F4_parent_phases_source_v1')
old=Path('/data/home/rohing/courier/runtime/orch_r139_F4_head_fields_source_v1/F4_BROKER_PUBLICATION.json')
raw=old.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='aff2fda6abd21b4d340a09ff52b8a4451029cdee0d38b9c977c9dce49ea1fdc7'
document=json.loads(raw)
assert document['authorized'] is True and document['repair_after_parent']==324
with (stage/'F4_PREVIOUS_BROKER_PUBLICATION.json').open('xb') as stream:
    stream.write(raw); stream.flush(); os.fsync(stream.fileno())
document['authorized']=False
temporary=old.with_name('F4_BROKER_PUBLICATION.phase_revoke.tmp')
with temporary.open('x') as stream:
    json.dump(document,stream,sort_keys=True,indent=2)
    stream.flush(); os.fsync(stream.fileno())
os.replace(temporary,old)
PY
S=/data/home/rohing/courier/runtime/orch_r140_F4_parent_phases_source_v1
test ! -e "$S/F4_OLD_BROKER_QUIESCED.json"
bash gpu/ovx3_ssh.sh 'PYTHONDONTWRITEBYTECODE=1 python3 -B -' > "$S/F4_OLD_BROKER_QUIESCED.json" <<'PY'
import json,time
from pathlib import Path
lock=Path('/localhome/local-rohing/orch_r115_grid_pair_20260915/F4/parent_astra_r139/RUNNER.lock')
for attempt in range(30):
    if not lock.exists():
        break
    time.sleep(1)
assert not lock.exists(), 'old_broker_not_quiesced_no_force_unlock'
print(json.dumps(dict(old_broker_lock_absent=True,observed_unix=time.time())))
PY
```

### 2. Publish replacement authorization using preserved bytes and actual actor receipt

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import hashlib,json,time
from pathlib import Path
stage=Path('/data/home/rohing/courier/runtime/orch_r140_F4_parent_phases_source_v1')
def ref(path):
    return dict(path=str(path.resolve()),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
wrapper=stage/'gpu/orch_r140_grid_parent_phases.py'
assert ref(wrapper)['sha256']=='8e352fed5539dd3eabf66c5dc59942e581bd9d8081a2109ec1b75b14115bc4c2'
assert ref(stage/'F4_PLAN.json')['sha256']=='21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546'
assert json.loads((stage/'F4_OLD_BROKER_QUIESCED.json').read_text())['old_broker_lock_absent']
archive=stage/'F4_PREVIOUS_BROKER_PUBLICATION.json'
assert ref(archive)['sha256']=='aff2fda6abd21b4d340a09ff52b8a4451029cdee0d38b9c977c9dce49ea1fdc7'
publication=json.loads(archive.read_text())
assert publication['authorized'] is True and publication['repair_after_parent']==324
publication.update(modes=['broker'],not_before_unix=time.time(),phase_wrapper=ref(wrapper),
    allowed_TRAIN_phases=['experience','open_turn','presleep_metacognition'],
    P0324_preserved_no_retry=True,prompt_text_unchanged=True,previous_publication=ref(archive),
    resumed=dict(path='/localhome/local-rohing/orch_r115_grid_pair_20260915/F4/r140_continuation_v1/RESUMED.json',
                 sha256='e8cb6f3cd4bcc676b335a237c15dcb7703d5be30713d3b952aae531c6f74853d'))
with (stage/'F4_BROKER_PUBLICATION.json').open('x') as stream:
    json.dump(publication,stream,sort_keys=True,indent=2)
print('PUBLICATION_SHA256',ref(stage/'F4_BROKER_PUBLICATION.json')['sha256'])
PY
```

All original model/scope/scratch/head-wrapper/cap fields stay unchanged. The
published `resumed` binding now points to the actual R140 restoration; its
original parent segment boundary still yields the same allocation/config bytes.
The new wrapper checks the preserved pre-revocation publication hash on every
authorization check. Never edit that archived publication.

### 3. One broker launch; child/timer remain running unchanged

```bash
S=/data/home/rohing/courier/runtime/orch_r140_F4_parent_phases_source_v1
REMAINING=$((1789596240-$(date +%s)-4))
test "$REMAINING" -gt 0 && test -f "$S/F4_BROKER_PUBLICATION.json" && test ! -e "$S/BROKER.log" &&
nohup env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 TMPDIR=/data/home/rohing/courier/runtime \
  timeout --signal=TERM --kill-after=3s "${REMAINING}s" python3 -B \
  "$S/gpu/orch_r140_grid_parent_phases.py" broker \
  --expected-self-sha256 8e352fed5539dd3eabf66c5dc59942e581bd9d8081a2109ec1b75b14115bc4c2 \
  --plan "$S/F4_PLAN.json" --plan-sha256 21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546 \
  --publication "$S/F4_BROKER_PUBLICATION.json" > "$S/BROKER.log" 2>&1 < /dev/null &
```

Main verifies fresh claim/result metadata and later native consumption; no
success is claimed until observed. Prior MISSING/refused/disposed slots remain
immutable, even if the new phase filter would otherwise admit them.
