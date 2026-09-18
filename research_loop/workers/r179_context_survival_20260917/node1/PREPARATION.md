# R179 NODE1 / A100 context-survival handoff preparation

## Status and ownership

2026-09-17: **LOCAL PREPARATION ONLY; WAITING MAIN PATCH AND CPU GO.**
Own only `research_loop/workers/r179_context_survival_20260917/node1/`.
No stop, pause, restart, signal, GPU/model/provider call, remote write, message,
old-journal mutation, sealed-content read, or COORDINATION edit in this stage.
Main owns the core context patch/tests and execution authorization. This is not
a new architecture/scientific claim, reset, replay, wall extension, or GPU GO.

`prepare_node1.py` cross-binds existing, immutable local metadata receipts and
emits a **non-executable** proposal. It has no SSH, launch, or signal interface.
Its tests validate preparation only, not the core patch or receiving runtime.
No new remote census is necessary for preparation; fresh admission is mandatory
immediately before any future execution.

## Exact six, not controls

Main census: 2026-09-17 09:52:29 PDT. Console-route observation: approximately
09:54:31 PDT. All six native actor tuples match across those bound observations
and R171 registration metadata. These are observations, not a current lock.

| Lane | Learning life | Native PID | Start ticks | Original guard exception |
|---|---|---:|---|---|
| 2 | teach_replay | 2197976 | 30656088 | normal lane2/control |
| 3 | teach_perception | 2409681 | 30796516 | normal lane3/control |
| 4 | teach_parenting | 1025183 | 29900700 | normal lane4/control |
| 5 | classroom_brain | 1072657 | 29930996 | normal lane5/control |
| 6 | classroom_creative | 1316795 | 30086561 | **lane6/readmission1/control/GUARD.json** |
| 7 | classroom_support | 1997023 | 30523369 | **orch_r147_a1007_recovery_20260916t1834z/attempt2/control/GUARD.json** |

Boot ID: `273420dc-cd6c-4760-a264-0027d2f6aede`; native UID: 1395.
Wrapper: `gpu/a100_ssh.sh`. Interpreter:
`/localhome/local-rohing/v2/venv/bin/python`.

Life roots remain
`/localhome/local-rohing/orch_r136_a100_<life>_20260916_attempt1/run1`.
All six original source roots are
`/localhome/local-rohing/orch_r144_target_rollout_a100_suffix_20260916t1643z/lane<N>/source`.
All six current PLAN references are sibling `lane<N>/control/PLAN.json`,
including lanes 6 and 7: **do not derive GUARD from PLAN's parent directory**.
The generated proposal retains exact PLAN/GUARD hashes, UUIDs, original argv
hashes, parent PID hints, actor identities, and four source-file hashes per life.
Parent PID hints are not verified timer/supervisor ownership proof.

Exclude both `orch_r139_a100_frozen_base_no_adapter_20260916_attempt1/run1`
and `orch_r139_a100_frozen_rank8_no_sleep_20260916_attempt1/run1` completely.
The six-life equality check excludes extra candidates, not merely a label filter.

## Minimal successor binding

Start from each life’s **actual complete hash-bound existing PLAN and GUARD**,
not a reconstructed plan from these partial metadata projections. Preserve:
same life/storage/inbox root, device UUID and containment, method/variant,
learning rate and optimizer settings, training and presentation schedules,
seed/experiment identity, readout revision, budgets, wall/resource reservations,
base/adapter provenance, and all existing safety/custody constraints.

Candidate PLAN change: `source_root` only, plus byte-identical relocation of an
existing source-relative `startup_context.path` if present. Any extra policy
field required by Main's exact approved patch must be enumerated and separately
bound; never quietly widen the permitted PLAN delta. Do not delete an existing
recovery annotation blindly; if it activates replay on a completed boundary,
hold for an explicit reviewed fix. New process must use normal saved `--resume`,
never reset, fresh seed, preupdate replay, or an adapter-only import.

Successor GUARD: preserve the original guard's invariant fields while rebinding
only new source closure, PLAN path/hash, allocation/control receipts, same-life
boundary reference, unique attempt/containment identity and explicit resume.
Do not manufacture posted/pushed/CPU-pass flags for compatibility. Existing wall
`1790442300` and all resource ceilings remain unchanged; this is not R157's
deadline extension. Proposed remote paths in the manifest are **not created**
and must pass nonexistence/symlink/collision checks when staging is authorized.

## Existing machinery: reuse checks, not entrypoints

- `gpu/orch_r157_community_wall_extension.py:215`: immutable original-source copy,
  pinned operator/tests and inputs; this hardcodes community/node5 authorization,
  UID and wall changes, so **not an A100 command to run**.
- `gpu/orch_r157_community_wall_extension.py:256`: terminal SLEEP_COMPLETE,
  verified record and resume-envelope hashes, pending=None, frontier=len(rows),
  completed receipt. At the actual frozen boundary also check full journal chain,
  unique checkpoint binding and all pending/intent consistency.
- `gpu/orch_r157_community_wall_extension.py:305`: useful receiving CPU pattern:
  restore the full saved stream/history envelope; verify checkpoint bundle,
  AdamW moments/groups/order/steps and Python/CPU/CUDA RNG payload without CUDA
  initialization. Do **not** run its wall-extension call for R179.
- `gpu/orch_r157_community_wall_extension.py:358`: exact native pidfd pause,
  all-thread stop check and independently surviving auto-resume watchdog. Its
  `:627` handoff rechecks boundary before retiring and preserves full stream and
  checkpoint. Reuse these properties only after A100-specific tests and GO.
- `gpu/orch_r152_a40r7_stage.py:81`: source-only relocation plus unchanged startup
  bytes is the relevant plan pattern. Its hardcoded failed-life entrypoints do
  not apply to these six lives.
- `gpu/orch_r152_a40r7_recovery.py:84`, `:269`, `:359`: adapter-file inventory,
  exact AdamW parameter order/state/steps and all RNG restore verification.
  **Never invoke replay_generations/finish_pending_sleep/recover_admitted_sleep**:
  those repair an unsaved suffix, which this task expressly prohibits.
- `gpu/orch_r131_saved_boundary_handoff.py:80`: older helper changes deadlines,
  signals an entire process group, and assumes old launch bindings. Do not run
  it directly against these mixed readmission/recovery guards.

## Per-life coordination after Main GO, not now

1. Bind Main's final patch/source manifest and actual CPU receipt. Build/test the
   A100-specific operator locally, then obtain **actual receiving CPU proof**
   against the staged source closure. Reject cold/stale tests or a boolean claim.
2. Acquire a per-life exclusive handoff lock/one-shot reservation; revalidate
   original actor boot/PID/ticks/UID/argv/cwd/cgroup, exact supervisor/timer/readout
   ownership, original complete PLAN/GUARD/source hashes, device isolation and
   current budgets/reservations. No all-six or all-fleet synchronization barrier.
3. Observe the next exact completed, quiescent saved boundary. Bind index/hash,
   full resume-envelope hash, sleep frontier/cycle, checkpoint COMMIT and bundle,
   optimizer steps, readout request/completion **metadata only**, consumed-inbox
   identities, and full saved history. Do not open response/map/score files.
4. Only after GO, pause the exact native actor under an independent watchdog;
   do not pause its independently running readout or parents. Recheck the exact
   terminal record, wait for owned readout completion/exit, preserve full saved
   stream/history and checkpoint opaquely and verify copies. Reserve explicit
   per-life byte/time limits **before** any large hash/copy/deserialization; if
   insufficient, resume original and hold rather than widening limits silently.
5. Execute receiving CPU restore verification on that exact boundary, emit only
   hashes/counts/status, and assert no CUDA initialization. Include full history,
   pending=None/frontiers, one checkpoint, adapter hash, AdamW parameter order,
   moments/steps, and all RNG state. CPU pass is not runtime loaded-state proof.
6. Recheck identities, ownership, source closure, unchanged boundary/checkpoint
   and watchdog deadline before graceful retirement. Await exact owned actor,
   timer and supervisor exit; require no new journal suffix. Never kill another
   lane's process, readout, parent, frozen control or shared reservation.
7. Launch one same-root successor under the existing guard/admission policy and
   preserved resource limits. Require actual loaded/resumed receipts bound to
   original adapter/optimizer/RNG/history/checkpoint and new source. Do not infer
   exact resume from a successful launch or CPU tests. Preserve old source and
   journal bytes; only the authorized continuing life appends new records.

No-boundary timeout leaves the original running. Before retirement, every abort
must release the exact paused actor via watchdog; after retirement, failed
admission/dispatch is a recorded hold, **not automatic retry or reset**. Any
retry requires fresh Main authorization, exact unchanged unconsumed boundary,
and proof no successor owner exists. Receive each lane independently.

Active parents may continue publishing to the unchanged inbox. Publication is
not consumption; preserve original consumed IDs/frontier, do not replay inbox
files or mistake total file count for pending work. Do not require a concurrently
growing inbox directory to stop changing as a substitute for native-boundary
integrity. Do not expose child text while verifying opaque history continuity.

## Evidence and reproduction

Local input hashes are enforced in `prepare_node1.py`; they refer to metadata,
not sealed/evaluator output. The original native SHA across all six is
`bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6`.
The Main census verifies relevant function ASTs; that is not full source closure
equality. Main's core patch/testing work is intentionally not duplicated here.

```sh
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python -B research_loop/workers/r179_context_survival_20260917/node1/test_prepare_node1.py
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python -B research_loop/workers/r179_context_survival_20260917/node1/prepare_node1.py --output research_loop/workers/r179_context_survival_20260917/node1/PREPARED_NODE1.json
```

The preparation command creates a new local receipt exclusively and refuses to
overwrite an existing one. It does not stage remote source or arm a handoff.

### R162 interim retained for Main

Actual attributed CLI:
`python -B -m gpu.orch_r127_pilot_console parent --root LIFE_ROOT --speaker Rohin --text TEXT`.
All five C1–C5 routes and 18 legacy routes have independent sidecar metadata;
Main census independently reports **24 LIVE training identities**, excluding
two frozen controls. The unresolved continual_run1 sidecar path check is not
evidence of death. No ingestion/request inclusion/reply is proven by publication
or an open inbox descriptor. The old `orch_r125_console.sh` is unattributed and
its raw-response follow mode is outside this audit.

Receipts: `research_loop/workers/rohin162_console_route_20260917/`.
C1–C5 use `gpu/ovx3_ssh.sh`, the same interpreter above, and original
`/localhome/local-rohing/orch_r153_community_C<N>_20260916_attempt1/life` roots.
Current sources: C1/C3/C4 use corresponding
`orch_r157_community_C<N>_20260917_attempt1/source`; C2 uses
`orch_r166_retelling_C2_20260917_activation4/source`; C5 uses
`orch_r166_retelling_C5_20260917_recovery2/source`, all under
`/localhome/local-rohing/`. Never replace original life inbox roots with recovery
source paths. Console SHA on all 23 verified routes:
`be7cfab563dcfe31590329e930b73238e26d39c7b03eb16c1859cc3e91f0b683`.

For Main's future authorized use only, **not executed here**, for example C2:

```sh
bash gpu/ovx3_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r166_retelling_C2_20260917_activation4/source /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r127_pilot_console parent --root /localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life --speaker Rohin --text "REPLACE WITH AUTHORIZED MESSAGE"'
```

This publishes rather than acknowledges ingestion. Never auto-retry an ambiguous
publication error, broadcast to controls, or assume authorization for an
unparented arm just because its inbox is technically reachable.
