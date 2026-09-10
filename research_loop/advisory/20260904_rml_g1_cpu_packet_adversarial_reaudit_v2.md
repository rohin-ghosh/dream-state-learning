# RML G1 CPU packet adversarial re-audit v2

Date: 2026-09-04  
Scope: fresh read-only adversarial audit of the current original-ratified RML G1 CPU packet after repair  
Disposition: **REJECT as GPU-ready; advisory only; this is not the binding independent pre-GPU review**

## Executive judgment

The repair closes several concrete defects from the v1 advisory. The reducer now rejects the original final-COMMIT citation laundering and forged-terminal-state counterexamples. Dispatch now rejects a wrong slot/phase, wrong target, or broad wrong condition mount before calling the provider. Stale snapshot bytes are rejected. Provider `finish_reason=length` becomes `MODEL_INVALID`; provider token-count disagreement becomes `INFRASTRUCTURE_FAILURE`; a post-dispatch output overflow is retained as a typed resource event. Pretarget selection now requires a seal-shaped capability. Generated evidence now separates `local_check_passed`, `acceptance_test_satisfied`, and `gpu_prerequisite_satisfied`, and no artifact has a bare `passed: true` field.

Those are real improvements, but the packet is still not closable or GPU-ready. The principal remaining original-scope blockers are:

1. The ratified T03 structural predicate remains false (`P ATOMS` certified fixed-policy capacity is 1/2, not the ratified 0/2), and the exact deliberation input `rml_d0/stage_a_report.json` remains unavailable at its bound hash. This report does not propose or assess any unratified replacement semantics.
2. There is still no scientific 18-trajectory provider/orchestrator, real pinned-tokenizer/chat rendering path, global failure/cancellation controller, immutable model ledger/output seal, real runtime closure, or canary execution.
3. The fixed exact-gate evaluator is not roster-bound. Ten duplicated core traces, no intervention child traces, and two copies of one intervention score pass all eight exact predicates.
4. Intervention authorization remains forgeable. A one-row, unmatched SHAM mount and a made-up parent-artifact SHA-256 dispatch successfully. An overbroad CUT removing three handles instead of the two cited decisive handles also dispatches.
5. A rehashed pretarget seal whose `H:GOLD` label actually contains a `FULL_TWIN` snapshot verifies and is accepted by selection. Selection re-extracts source facts and does not consume the sealed snapshot entries, so the capability does not prove the causal dependency it names. The full ordered candidate/eligibility/first-eligible trace remains absent.
6. Anti-overcitation is incomplete: arbitrary unreturned handles can be cited in every READ record while `citations_returned_before_use` and `decisive_citations_minimal` remain true, because only ENV citations are scored.
7. Exact resource/canary closure remains false-green. A returned row counted as 257 exact tokens is accepted because only the per-trajectory row total is checked at read time. The canary validator accepts a 5,080-byte whitespace-padded output while the receipt claims one output byte and supplies zero registered target hashes.
8. Reducer outputs are caller-labelable and are not joined to the roster or ledger. A legal GOLD trace can be scored as trajectory `FAKE_TRAJECTORY`, condition `BOGUS_CONDITION`, and still receive legal-success credit. `require_complete=True` also accepts any caller-supplied subregistry; a 13-row single-trajectory ledger is “complete.”

The current packet itself truthfully reports `ratified_acceptance_tests_satisfied: false` and `gpu_dispatch_ready: false`. That disposition is correct. **Do not run the GPU canary or scientific gate from these bytes.**

## Scope boundary and audit basis

I read:

- `AGENTS.md`;
- the original ratified change, consensus, and ratification under `research_loop/changes/chg_20260903_rml_g1_gold_action_fast_v1/`;
- `research_loop/advisory/20260904_rml_g1_cpu_packet_adversarial_audit_v1.md`;
- every Python source and test file under `rml_stage_b/`;
- the Stage-B prompt, operation schema, and workflow JSON; and
- the currently generated G1 CPU artifacts.

I deliberately did **not** read any pending successor consensus and do not opine on or implement unratified control-ceiling/G1B semantics. Where this report notes the ratified P-ATOMS contradiction, it says only that the original binding predicate is false in the current packet.

The audited implementation is a dirty working-tree packet. Its current exact source hashes are:

```text
69459ceef15870b579b55009201edffec22e170122f809a197986b77a506be91  rml_stage_b/__init__.py
c6f3546419269b687e145fe72d75dc4afbcf8026ad8b0160f68b88a6c71bfd63  rml_stage_b/contract.py
2c6f612cf42c1bba743bde48e94dde7f3fc1dbe5bf851a2e49ebf096bcdc71ba  rml_stage_b/fixtures.py
ac41dc0a28e8952198395e936157b1d1e85c4a73a3dc868b59381683b01ab98e  rml_stage_b/machine.py
c0eb59108c59c7dc0545065b87145b11eac7f2cb971db41be217694ff8ff9825  rml_stage_b/memory.py
b1b3af142f91e37219d6dba81f2b2538632eb863bcc333df6a0388836fb64fb8  rml_stage_b/reducer.py
731ba149c09b1bc8848a698b538680238851d2c911cd44cace7f16808b89550d  rml_stage_b/review.py
5549d73087cc9897c066f6a95d7635f6d00d0b66f1caa73532e53d103085b307  rml_stage_b/run_cpu_preflight.py
4345ea5c5c149a8058bb8e2bfc2f6fc3810f47182af066abe9c5046492c5a5b4  rml_stage_b/runner.py
ac5283f461abd5d8adee650c54d063b7c852f0d2791be1131721ef46eabe6f17  rml_stage_b/runtime.py
06c076bf9a5b17984af7630a1b635e856f9ea654956470b3da030c0245d787e7  rml_stage_b/tests/__init__.py
a29c81259606afafd484185e2be92c265e27c90b5d7544f2ac7bbdc5ff790ab1  rml_stage_b/tests/test_g1_cpu_preflight.py
98574f8c02dee7d4bce659a9e701f59feaa33c6d558962541f5f366f5e97fbc7  research_loop/prompts/rml_stage_b_think_v1.txt
8fced9abb8f8771ed1f5ef53f467e6e114ba0ef2e1198661ff6983c53a0c65f8  research_loop/schemas/rml_stage_b_operation_v1.schema.json
6fe5bd66d42b77726c824733bc2727ebcfc5f76d8c28176aafbfb7601f0739a4  research_loop/workflows/rml_stage_b_gold_action_fast_v1.json
```

The binding documents hash to:

```text
b84bb50c172c06cacd99e810693739e4111319a2cfdeebf586faa1288478b6f7  change.json
1c27cbe6ac3adda14078f2cdbfe62785ce7161b4ae35c2fb96b899b40da53cb9  consensus.json
fa6dd830a67ba03dd336945e74759ae58ce075de201573c4037798cba2e4ab53  ratification.json
```

## Commands and results

No model, GPU, or network call was made. `PYTHONDONTWRITEBYTECODE=1` was used for repository imports. The only repository write from this re-audit is this advisory.

### Dependency-free six-test suite

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import inspect
import time
from rml_stage_b.tests import test_g1_cpu_preflight as suite
names = [name for name, value in inspect.getmembers(suite, inspect.isfunction) if name.startswith('test_RML_G1_')]
started = time.monotonic()
passed = []
for name in names:
    getattr(suite, name)()
    passed.append(name)
print({'passed': len(passed), 'total': len(names), 'elapsed_seconds': round(time.monotonic()-started, 3), 'tests': passed})
PY
```

Exact result:

```text
{'passed': 6, 'total': 6, 'elapsed_seconds': 14.553, 'tests': ['test_RML_G1_T01_PRETARGET_SNAPSHOT_QUERY_AND_VISIBLE_BYTE_NONINTERFERENCE', 'test_RML_G1_T02_CLOSED_PHASE_MACHINE_AND_234_LEDGER', 'test_RML_G1_T03_D0_WORLD_PLUS_NEW_TRACE_REDUCER_AND_SLICE_CERTIFICATE', 'test_RML_G1_T04_HASHED_DETERMINISTIC_RUNTIME_AND_ABSOLUTE_RESOURCE_CANARY', 'test_RML_G1_T05_EXACT_18_TRAJECTORY_CAUSAL_GATE', 'test_RML_G1_T06_TWO_PHASE_REVIEW_AND_EXACT_CLAIM_FIREWALL']}
```

This is a regression-suite pass, not satisfaction of the ratified replacement tests. The suite itself asserts that the packet is not acceptance-complete or GPU-ready.

### Provider-free CPU preflight in a temporary directory

Exact command:

```bash
audit_tmp=$(mktemp -d /private/tmp/rml-g1-reaudit.XXXXXX) && PYTHONDONTWRITEBYTECODE=1 python3 -m rml_stage_b.run_cpu_preflight --output-dir "$audit_tmp" && python3 - "$audit_tmp" <<'PY'
import json, pathlib, sys
root=pathlib.Path(sys.argv[1])
summary=json.loads((root/'cpu_preflight_summary.json').read_text())
print({'output_dir':str(root),'artifact_count':len(list(root.glob('*.json'))),'local_check_passed':summary['local_check_passed'],'acceptance_test_satisfied':summary['acceptance_test_satisfied'],'ratified_acceptance_tests_satisfied':summary['ratified_acceptance_tests_satisfied'],'gpu_dispatch_ready':summary['gpu_dispatch_ready'],'blocker_count':len(summary['blockers'])})
PY
```

Result:

```text
{'output_dir': '/private/tmp/rml-g1-reaudit.Zf4CQV', 'artifact_count': 7, 'local_check_passed': True, 'acceptance_test_satisfied': False, 'ratified_acceptance_tests_satisfied': False, 'gpu_dispatch_ready': False, 'blocker_count': 4}
```

The four emitted blockers were the ratified P-ATOMS contradiction, missing GPU provider/orchestrator/runtime/ledger/canary, missing pre-GPU reviews, and the Stage-A context-hash mismatch.

### Focused old-counterexample repair probe

The focused probe produced exactly:

```text
{'forged_state': 'REJECTED:terminal scratch/state disagrees with replay', 'wrong_slot': 'REJECTED:dispatch registration disagrees with machine slot/phase:calls=0', 'wrong_condition': 'REJECTED:memory service projection is unauthorized for condition:calls=0', 'stale_snapshot': 'REJECTED:snapshot row serialization/integrity mismatch', 'truncated': 'MODEL_INVALID', 'accounting_mismatch': 'INFRASTRUCTURE_FAILURE'}
```

The same run's final-COMMIT mutation returned:

```text
late_commit False False
```

where the booleans are `citations_returned_before_use` and `decisive_citations_minimal`.

### Focused false-green mutation probe

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from dataclasses import replace
from rml_stage_b.contract import DECODING, MODEL_ID, MODEL_REVISION, TOKENIZER_REVISION, build_opportunity_registry, build_roster, digest
from rml_stage_b.fixtures import build_selected_cases
from rml_stage_b.machine import OpportunityEvent, OpportunityLedger, RmlActionMachine, dispatch_one, operation_bytes
from rml_stage_b.memory import ExactMemoryService, PretargetSnapshotSeal, conservative_cpu_token_count, masked_snapshot, seal_pretarget_snapshot_universe
from rml_stage_b.reducer import decisive_handles, evaluate_exact_gate, score_frozen_trace
from rml_stage_b.runner import run_scripted_cpu_gate
from rml_stage_b.runtime import REQUIRED_HASH_COMPONENTS, CanaryReceipt, RuntimeClosure, validate_canary_receipt

seal=seal_pretarget_snapshot_universe(); snaps=seal.snapshot_map(); cases=build_selected_cases(seal); scripted=run_scripted_cpu_gate()
case=cases['J_H']; snap=snaps['H:GOLD']; parent=scripted.machines['GOLD_REC:J_H']; decisive=decisive_handles(case,snap)
def recite(fn):
    rows=[]
    for i,r in enumerate(parent.records):
        c=fn(i,r)
        rows.append(replace(r,citations=c,raw_output=r.raw_output if r.operation is None else operation_bytes(r.operation,scratch=r.scratch,citations=c)))
    return score_frozen_trace('GOLD_REC:J_H','GOLD_REC',case,replace(parent,records=tuple(rows)),snap)
late=recite(lambda i,r: decisive if i==12 else ())
read_extra=recite(lambda i,r: ('RH_UNRETURNED_BOGUS',) if r.phase=='READ' else r.citations)
gold=scripted.traces['GOLD_REC:J_H']; none=scripted.traces['NONE_REC:J_TWIN']; atoms=next(x for x in scripted.traces.values() if x.condition=='ATOMS_REC' and not x.legal_commit_success)
traces={}
for i in range(4): traces[f'g{i}']=replace(gold,trajectory_id=f'FG{i}'); traces[f'n{i}']=replace(none,trajectory_id=f'FN{i}')
for i in range(2): traces[f'a{i}']=replace(atoms,trajectory_id=f'FA{i}')
inter=scripted.interventions['GOLD_REC:J_H']; duplicate_gate=evaluate_exact_gate(traces,{'x':inter,'y':inter})
registry=build_opportunity_registry(build_roster()); child='SHAM_REC:J_H'; childreg=tuple(x for x in registry if x.trajectory_id==child)
nondec=next(x.handle for x in snap.rows if x.handle not in decisive); bad_sham=masked_snapshot(snap,(nondec,),transform='SHAM'); fake=digest(b'fake-parent')
ledger=OpportunityLedger(childreg).bind_parent_artifact('GOLD_REC:J_H',fake); service=ExactMemoryService(bad_sham,authorized_trajectory_id=child,parent_artifact_sha256=fake)
key=next(x for x in RmlActionMachine.start(case).allowed_keys if x.startswith('schema:'))
def provider(payload,*,opportunity_id):
    raw=operation_bytes({'kind':'READ','key':key}); return raw,{'input_tokens':len(payload),'output_tokens':len(raw),'wall_ms':0,'finish_reason':'stop'}
child_machine,ledger=dispatch_one(RmlActionMachine.start(case),service,provider,childreg[0],ledger,token_counter=len)
entries=list(seal.entries); i=next(i for i,x in enumerate(entries) if x[0]=='H:GOLD'); j=next(i for i,x in enumerate(entries) if x[0]=='FULL_TWIN:GOLD'); entries[i]=(entries[i][0],seal.entries[j][1]); entries[j]=(entries[j][0],seal.entries[i][1]); entries=tuple(entries)
body={'snapshots':[{'name':n,'sealed_sha256':s.sealed_sha256,'query_universe':s.query_universe,'renderer_sha256':s.renderer_sha256,'tokenizer_rendering_sha256':s.tokenizer_rendering_sha256} for n,s in entries]}; swapped=PretargetSnapshotSeal(entries,digest(body)); swapped.verify(); build_selected_cases(swapped)
rowkey=next(x for x in RmlActionMachine.start(case).allowed_keys if x.startswith('exchanger:')); rowbytes=snap.row_map()[rowkey].serialized
counter=lambda b:257 if b==rowbytes else conservative_cpu_token_count(b)
row_machine=RmlActionMachine.start(case).advance(operation_bytes({'kind':'READ','key':rowkey}),ExactMemoryService(snap),token_counter=counter)
hashes={x:digest(x.encode()) for x in REQUIRED_HASH_COMPONENTS}; closure=RuntimeClosure(MODEL_ID,MODEL_REVISION,TOKENIZER_REVISION,DECODING,hashes,'FRESH_PROCESS_PER_TRAJECTORY','EMPTY_KV_BEFORE_FIRST_SLOT','EMPTY_READER_AND_BACKEND_CACHE',0.0)
raw=b' '*5000+operation_bytes({'kind':'READ','key':'schema:canary'}); receipt=CanaryReceipt(closure.validate(),digest(b'canary'),(),raw,True,True,True,0,1,1,1,1); canary=validate_canary_receipt(receipt,closure)
sub=tuple(x for x in registry if x.trajectory_id=='GOLD_REC:J_H'); first=sub[0]; partial=OpportunityLedger(sub).append(OpportunityEvent(first.opportunity_id,first.trajectory_id,0,'READ',True,'TERMINAL','MODEL_INVALID',1,1,1,1,0,'stop')).cancel_suffix(first.trajectory_id,0)
label=score_frozen_trace('FAKE_TRAJECTORY','BOGUS_CONDITION',case,parent,snap)
print('late_commit',late.citations_returned_before_use,late.decisive_citations_minimal)
print('read_overcitation',read_extra.citations_returned_before_use,read_extra.decisive_citations_minimal,'RH_UNRETURNED_BOGUS' in read_extra.cited_handles)
print('duplicate_gate',len(traces),duplicate_gate['local_check_passed'],all(duplicate_gate['exact_predicates'].values()))
print('bad_sham_fake_parent',not child_machine.terminal,len(bad_sham.masked_handles),len(decisive))
print('swapped_seal',dict(entries)['H:GOLD'].projection,'ACCEPTED')
print('row_257_tokens',row_machine.terminal,row_machine.outcome_state)
print('canary_claim_1_actual',canary['canary_valid'],receipt.output_bytes,len(raw),len(receipt.registered_target_hashes))
print('partial_complete',partial.reconcile(require_complete=True))
print('unbound_labels',label.trajectory_id,label.condition,label.legal_commit_success)
PY
```

Exact result:

```text
late_commit False False
read_overcitation True True False
duplicate_gate 10 True True
bad_sham_fake_parent True 1 2
swapped_seal FULL_TWIN ACCEPTED
row_257_tokens False None
canary_claim_1_actual True 1 5080 0
partial_complete {'registered': 13, 'disposed': 13, 'dispatched': 1, 'zero_attempt_resource_failures': 0, 'cancelled': 12}
unbound_labels FAKE_TRAJECTORY BOGUS_CONDITION True
```

For `read_overcitation`, the final `False` means the bogus cited handle is omitted from `TraceScore.cited_handles`, which is precisely why minimality remains green.

## Prior O1/O2 prerequisite status

### O1 — Ratified T03 structural precondition remains false

**Status: remaining blocker.**

`build_slice_certificate` still reports `atoms_best_policy_success_capacity == 1` and `ratified_atoms_zero_capacity_consistent == false` (`fixtures.py`, lines 325–382). The dependency-free test deliberately asserts those values (`test_g1_cpu_preflight.py`, lines 582–594), and `cpu_end_to_end.json` marks the contradiction as blocking (`run_cpu_preflight.py`, lines 102–119).

This re-audit makes no recommendation about a replacement threshold, capacity semantics, or any pending amendment. Under the only ratified original scope read here, T03/R07 is unsatisfied.

### O2 — Exact ratified Stage-A context remains unreconstructible

**Status: remaining blocker.**

Exact commands:

```bash
sha256sum rml_d0/stage_a_report.json
git log --all --format='%H' -- rml_d0/stage_a_report.json | while read commit; do git show "${commit}:rml_d0/stage_a_report.json" | sha256sum; done | sort -u
```

Results:

```text
e36be91f7244dd483a274a1cf350e383011a707d053a02fe753c6f982e9b47c0  rml_d0/stage_a_report.json
e36be91f7244dd483a274a1cf350e383011a707d053a02fe753c6f982e9b47c0  -
```

The ratified report hash in `change.json` and `run_cpu_preflight.py` is:

```text
346bd091e9d037b1e51c8ed735ba5ecfbee50a42d10988d02ebc28c87532855b
```

No repository JSON matched it in the audit search. The current preflight correctly makes `stage_a_context_hash_matches` false and propagates it as a blocker.

## O3–O9 re-audit

### O3 — Scientific GPU runner and runtime closure

**Status: not fixed; blocking.**

`runner.py` still ends at `run_scripted_cpu_gate` (lines 111–216). It uses host-selected plans and decisive handles and never calls a model provider. `dispatch_one` remains a one-op seam (`machine.py`, lines 616–787). There is no callable that runs the frozen 18-trajectory order, starts a fresh process per trajectory, loads the pinned model/tokenizer, composes the chat template/system prompt/schema/user bytes, creates intervention children from frozen parent citations, globally cancels undispatched identities, seals a raw prompt/output/accounting ledger, or binds post-run reviews.

`RuntimeClosure.validate` checks only that component values look like SHA-256 strings (`runtime.py`, lines 93–127); it does not recompute them. `validate_canary_receipt` uses the conservative CPU token counter, does not carry or enforce a finish reason, does not recompute the claimed byte/token counts, and trusts the caller-supplied registered-target hash tuple (`runtime.py`, lines 130–172). The 5,080-byte/claimed-one-byte mutation above passes. `cpu_runtime_manifest` truthfully says `actual_gpu_canary_run: false`, `runtime_hashes_bound: false`, and `gpu_dispatch_ready: false` (lines 175–191).

Required closure remains the v1 recommendation: a CPU fake-provider integration test of the real 18-trajectory orchestrator, using the exact same render/parser path as canary and scientific calls, with 234 precommitted identities, clean isolation, parent-derived interventions, early terminal handling, provider/resource/global failure, dependency cancellation, raw immutable ledgers, and seal/replay verification.

### O4 — Citation-deadline laundering

**Status: core counterexample fixed; original anti-overcitation requirement still incomplete and blocking.**

The repaired reducer establishes pair and valve support boundaries and requires return before the supported action and citation no later than that action (`reducer.py`, lines 269–339). Final-COMMIT-only citations now retain legal D0 success but fail both timing and minimality. Boundary tests cover pair-late, valve-late, and RUN-late cases (`test_g1_cpu_preflight.py`, lines 749–821).

However, `cited_at` collects only citations from ENV records (`reducer.py`, lines 281–286). The mutation probe put the unreturned `RH_UNRETURNED_BOGUS` handle in every READ output. The trace still received:

```text
citations_returned_before_use = true
decisive_citations_minimal = true
```

and the bogus handle was omitted from `cited_handles`. That violates original R06 mechanical minimality/anti-overcitation and permits a misleading “minimal cited path” claim. Add negative tests for unreturned, late, duplicate-across-slots, and nondecisive citations in every phase, and define whether READ-phase citations are forbidden or included in the complete cited set.

### O5 — Independent D0 replay and frozen-artifact authority

**Status: D0 replay fixed for the v1 mutations; immutable-artifact/identity binding remains incomplete and blocking.**

`_validate_and_replay_artifact` now strictly parses serialized records, requires contiguous slot/phase order, replays every READ from the supplied sealed snapshot, replays every ENV action through D0, checks exact result code/text, and recomputes final state/outcome/reason (`reducer.py`, lines 117–253). The v1 copied-success-state forgery is rejected. Tests also mutate returned status/bytes, raw output, action, result, phase, order, missing COMMIT, and outcome label (`test_g1_cpu_preflight.py`, lines 675–893).

But `score_frozen_trace` still accepts a live `RmlActionMachine`, serializes it internally, then scores it (`reducer.py`, lines 256–366). It does not consume an externally persisted artifact joined to opportunity events, prompt bytes, provider receipt, snapshot seal, and a roster row. `trajectory_id` and `condition` are copied directly from caller parameters without validation. The probe scored a GOLD success as `FAKE_TRAJECTORY` / `BOGUS_CONDITION`.

This becomes an actual gate false green in `evaluate_exact_gate`: the function groups by caller-controlled condition and checks only list lengths and values (`reducer.py`, lines 450–506). It does not require the exact 18 trajectory IDs, unique target coverage, the seven exact condition cells, two unique prospective parents, the eight actual child traces, or any ledger/artifact join. Ten duplicated core traces plus two copies of one intervention score pass all eight predicates.

Required regression: build the gate report only from a sealed join keyed by the exact 18 roster entries and 234 opportunity identities; reject duplicates, omissions, extras, target substitutions, label substitutions, missing child artifacts, repeated intervention parents, and any trace whose artifact/snapshot/ledger hashes do not match the frozen manifest.

### O6 — Opportunity identity, condition mount, and dependency binding

**Status: slot/target/base-condition repair fixed; gate-order and child-binding closure remain incomplete and blocking.**

`dispatch_one` now checks registry membership, roster target, service trajectory authorization, broad condition projection, live slot/phase, prior same-trajectory slots, and global infra/resource freeze before provider execution (`machine.py`, lines 627–660). The v1 ENV-registration-on-slot-0 probe is rejected with zero provider calls. A GOLD snapshot mounted for `NONE_REC` is also rejected.

Remaining failures:

- `OpportunityLedger` accepts any unique subregistry and `reconcile(require_complete=True)` defines completeness relative to it (`machine.py`, lines 61–77 and 213–230). A 13-opportunity ledger is therefore “complete.”
- Ordering is enforced only within each trajectory. The first event can be `TWIN_REC:P_H` even though the frozen roster begins `GOLD_REC:J_H`; a focused append probe accepted that ordering.
- `bind_parent_artifact` validates only the syntax of a caller-supplied hash and requires it before any ledger event (`machine.py`, lines 79–96). It neither hashes a frozen parent artifact nor proves parent eligibility. Requiring binding before all events is also incompatible with deriving the seal after an in-run parent freezes in one global ledger.
- `_validate_service_binding` checks only broad transform/projection properties (`machine.py`, lines 535–613). It does not derive SHAM/CUT masks from the frozen parent's actually cited handles or verify SHAM count/byte/token matching. A one-row unmatched SHAM with a fabricated parent hash dispatched; an overbroad CUT with three masked handles also dispatched.

Required regressions: full-registry construction only for the gate ledger; exact cross-trajectory dispatch order; child dispatch impossible before a frozen, successful, minimal parent artifact is present in the same sealed run; parent hash recomputation; exact SHAM matching proof; exact CUT cited-handle/equivalence-closure proof; and negative cases for undersized, oversized, wrong-parent, prior-run, and fabricated masks/seals.

### O7 — Durable resource failure, truncation, and exact accounting

**Status: token/byte event durability partly fixed; full R09 closure remains blocking.**

Positive repair evidence:

- provider `finish_reason=length` is persisted and becomes `MODEL_INVALID:TRUNCATED_OUTPUT` (`machine.py`, lines 707–765);
- provider input/output counts are type-checked and independently recomputed with the injected counter; a mismatch becomes `INFRASTRUCTURE_FAILURE`;
- output per-call/trajectory/gate overflow is detected after the call and the attempted event is appended with `RESOURCE_CEILING_EXCEEDED` (`machine.py`, lines 731–787);
- a zero-attempt predictable input overflow is distinguished from suffix cancellations in reconciliation (`machine.py`, lines 213–230); and
- tests exercise an exact +1 output-token crossing with a durable 234th attempted event (`test_g1_cpu_preflight.py`, lines 489–579).

Remaining blockers:

- No global cancellation method disposes every remaining registry identity. After a slot-0 predictable resource failure and current-trajectory `cancel_suffix`, the full registry was only `disposed: 13` of `registered: 234`; `require_complete=True` rejected it.
- A row is built against the conservative CPU counter, while `advance` checks only the aggregate row-token/byte totals (`machine.py`, lines 423–427). With an injected exact counter returning 257 for one row, the read remained nonterminal with no failure. The ratified 256-token per-return limit is therefore unenforced on the actual serving path.
- Wall time, A40 GPU-hours, stored artifact bytes, and USD cost are outside `dispatch_one`; `GateResourceUsage.validate` is detached from a runner (`runtime.py`, lines 55–78).
- The injected counter is not proven to be the pinned tokenizer, and the actual model input does not include a implemented chat template/system/schema rendering path.
- There is no fail-closed whole-gate uninterpretable state and typed cancellation reason for every remaining identity after infrastructure/resource failure.

Required negative tests: +1 crossings separately for each per-return/per-call/per-trajectory/whole-gate token and byte ceiling; exact pinned-tokenizer recomputation from saved complete chat bytes; wall/GPU/storage/cost crossings; current-failure plus global suffix disposition; and complete reconciliation over the immutable 234-row registry.

### O8 — Pretarget ordering and deterministic selection

**Status: call-order API partly fixed; seal semantics and first-eligible evidence remain blocking.**

`build_selected_cases` now requires a `PretargetSnapshotSeal` and verifies it before selection (`fixtures.py`, lines 140–145). `run_scripted_cpu_gate` now seals snapshots before selecting cases (`runner.py`, lines 111–118). Passing `None` or a stale manifest hash is rejected.

But `PretargetSnapshotSeal.verify` checks the set of entry names and validates each snapshot separately; it never checks that each name equals `snapshot.projection + ':' + snapshot.kind` (`memory.py`, lines 282–316). A rehashed seal with `H:GOLD` and `FULL_TWIN:GOLD` values swapped verified. `build_selected_cases` accepted it because, after verifying the capability, it discards the entries and re-runs `extract_permitted_source_facts` (`fixtures.py`, lines 145–149).

The selector also still hard-codes one D11/module/mode construction and emits only a descriptive `selection_rule` string. It does not materialize the ordered candidate universe, eligibility results, tie keys, rejected predecessors, selected index, or a proof that the first eligible candidate was chosen (`fixtures.py`, lines 72–214 and 360–382).

Required regressions: name/projection/kind binding; source and builder-output hash binding; selection must consume the verified sealed entries rather than rederive mutable inputs; swapped-entry/resealed-content/TOCTOU mutations; and a complete ordered candidate/eligibility/tie/selected-index manifest whose mutation invalidates closure.

### O9 — Misleading pass fields

**Status: fixed for the current CPU evidence labels.**

Every generated report contains `local_check_passed`, `acceptance_test_satisfied`, and `gpu_prerequisite_satisfied`; every acceptance/prerequisite value is false. No report contains `passed: true`. `fast_gate_report.json` is labeled `CPU_SCRIPTED_HARNESS_ONLY_NOT_MODEL_EVIDENCE`. The summary additionally sets `ratified_acceptance_tests_satisfied: false` and `gpu_dispatch_ready: false` (`run_cpu_preflight.py`, lines 60–186).

The six report hashes in the current summary match the six JSON files byte-for-value. These clearer labels do not cure the local-check gaps above, but they no longer represent a local scripted pass as acceptance or GPU readiness.

## New false-green paths and missing negative tests

The following are not covered by the current 996-line CPU test file and should be treated as original-scope negative-test requirements:

1. **Exact roster join:** reject duplicated trace objects, duplicate IDs, missing conditions, missing child traces, wrong target IDs, unknown conditions, extra traces, repeated intervention parents, and fewer/more than 18 artifacts.
2. **Artifact/ledger join:** reject caller-controlled trajectory/condition labels, live-dataclass-only scoring, trace hashes absent from ledger events, wrong snapshot seal, wrong prompt/output receipt, and artifacts not sealed before scoring.
3. **All-phase citation accounting:** reject unreturned/nondecisive/late citations in READ as well as ENV; assert the complete cited set, not an ENV-only projection.
4. **Parent-derived interventions:** reject made-up parent hashes, prior-run parent hashes, parent-nonsuccess, parent-nonminimal, SHAM count mismatch, SHAM byte/token mismatch, CUT under/overmask, and masks unrelated to actual parent citations.
5. **Global opportunity order/completeness:** reject any subregistry as a gate registry, any first event outside frozen order, any child before eligible parent, and any resource/infra failure leaving one of 234 identities undisposed.
6. **Pretarget seal meaning:** reject name/projection/kind swaps even when rehashed, alternative internally valid snapshot content, source-hash mismatch, builder-output mismatch, and selection that merely verifies then ignores the seal.
7. **Exact resource enforcement:** reject a single exact-token 257-row return, each separate +1 limit crossing, unbounded wall time, and any counter not bound to the pinned tokenizer/chat bytes.
8. **Canary integrity:** recompute raw output bytes/tokens; use strict duplicate-key/output-size parsing; require `finish_reason=stop`; independently bind the complete registered target manifest; reject missing target hashes, whitespace padding, truncated output, fake component hashes, and claimed/actual accounting mismatch.
9. **Runtime/review persistence:** recompute every runtime component hash from named bytes, persist reset evidence, bind approvals to a complete packet manifest, and require a real immutable output artifact before post-run review.

## Fixed versus remaining blockers

| Issue | Fresh disposition | GPU impact |
|---|---|---|
| O1 ratified P-ATOMS structural precondition | Remaining | Blocking |
| O2 missing ratified Stage-A report bytes | Remaining | Blocking |
| O3 scientific runner/runtime closure | Remaining | Blocking |
| O4 final-COMMIT laundering | Fixed for ENV support deadlines; READ anti-overcitation remains | Blocking |
| O5 D0 replay | Fixed for tested field mutations; artifact/identity/ledger binding remains | Blocking |
| O6 wrong opportunity/condition mount | Fixed for slot/target/broad base mount; child derivation, order, and registry closure remain | Blocking |
| O7 resource durability/truncation/accounting | Partly fixed; exact row/global/non-token resource closure remains | Blocking |
| O8 selection-before-seal | API order fixed; seal meaning and deterministic candidate evidence remain | Blocking |
| O9 pass fields | Fixed | Not independently blocking |

## GPU-ready disposition

**REJECT. Do not launch the GPU canary or any scientific opportunity from the current packet.**

The dependency-free regression suite is green, and several important counterexamples now fail closed, but the exact ratified acceptance tests remain false. Before a binding independent reviewer can assess GPU readiness, the original-scope packet still needs:

- governance closure for the two pre-existing binding prerequisites, without silently adopting unratified semantics;
- one real, fake-provider-tested 18-trajectory/234-opportunity orchestrator;
- sealed roster/ledger/trace/snapshot/provider joins;
- parent-derived exact SHAM/CUT/TWIN dependency enforcement;
- complete citation accounting;
- exact tokenizer/chat/canary/resource enforcement and global cancellation; and
- replayable deterministic selection evidence bound to the actual pretarget seal.

After repairs, freeze and hash the exact packet, regenerate CPU evidence, and obtain a fresh binding independent pre-GPU review plus the distinct author-side scientific-advocate review required by the ratified consensus. This advisory cannot supply either approval.
