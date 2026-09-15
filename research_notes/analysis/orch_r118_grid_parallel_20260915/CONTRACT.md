# GRID F4/A4 prospective fresh-exec successor

Status: **CPU_READY_NOT_ACTIVATED**, September 15, 2026. No current actor,
source, COMMON CONFIG, timer, broker, or allocation was changed by this work.
Main is the only Git publisher and all-eight transition authorizer.

## Current v4: authorized failed-DEV and pending-TRAIN recovery

Frozen at September 15, 2026, 15:06 UTC; **not activated or released**.
The native overlay is
`/localhome/local-rohing/orch_r118_grid_parallel_candidate_source_20260915_v4`.
`READY.json` SHA:
`e2d1ecf5fdd25c2f8906bf54eca758bf828bab4d8b5b95c3cc888fd32a2aec34`.
Native CPU: **66 passed**, plus **7 local A4 broker tests**. Local combined
GRID/recovery/FINAL tests: 140 passed before the additional guard-identity
regression; current focused suite: 73 passed.

The first v3 metadata preparation failed on the historical guard's decimal
string `start_ticks` versus central integer identity schema. Its tests/logs
remain native. v4 normalizes only positive decimal PID/ticks, preserving exact
boot/start identity; it does not waive liveness, scope, or provenance checks.

Actual native metadata/provenance preparation:
`ACTUAL_RUNTIME_CPU.json` SHA
`8096d3c1ff6eb321c80c45406a9debf5f7247c3388db816a007216bf3215dcf3`.
- F4: authentic repair FAILED after C8 gen1 reload during DEV. N565/P40,
  accepted gen0 already trained. `parallel_candidate_v4_cpu/BOUNDARY.json`
  under its original branch root binds failed DEV and NOT_ATTEMPTED OPEN,
  `postcommit_eval_disposition` plus normalized recovered cursor. No invented
  COMPLETE, no retry/recollection/resubmission. Next TRAIN cycle9.
- A4: live native1108400, C7 fresh DEV genuinely COMPLETE; C8 two TRAIN
  episodes and reflection COMPLETE and submitted to gen1, N567/P40.
  Its `parallel_candidate_v4_cpu/BOUNDARY.json` binds
  `settled_pending_consolidation` plus normalized pending cursor. Central
  validation of every TRAIN source and existing submission passed. The next
  new TRAIN cycle is9, but the fresh process must first adopt and consolidate
  pending cycle8, without new calls or duplicate submission.

Both restore the canonical gen1 child43ce68ac…, not a new seed. F1 alone
restores its AdamW/RNG; GRID has optimizerNone and explicitly new rank RNG.
All old ledgers, carry, failures, submissions and provenance remain unchanged.
This is metadata/CPU readiness, not actual fresh-process restore or performance.

New CLI modes are `crash-snapshot`, `crash-release`, and `pending-snapshot`,
in addition to the historical modes below. `crash-snapshot` needs an exact
`guard_identity` and creates disposition metadata only. `crash-release` needs
the original explicit Main all8 drain authorization plus the bound snapshot;
it verifies dead predecessor identities and never signals. A live pending
drain uses `pending_consolidation: true`, cycle8, and the same exact all8
authorization; it holds only the owned native, verifies terminal calls,
source hashes, carry and immutable COMMON submission, resumes on a busy
cursor, and releases only a settled pending actor. Do not wait for an
impossible old C8 CYCLE_COMPLETE/all8 serial sleep.

Future exec plans additionally require `common_root` and a pinned `campaign`
reference `{path,sha256}`. After canonical bootstrap and all8 collection GO,
pending A4 calls central `resume_pending_consolidation`, emits an actual
fresh-identity SAFE, then calls `await_campaign_activation`. F4 collects its
new pair first. The central method publishes SAFE and waits for Main's
campaign autoarm; no manually polled per-generation owner approval and no
alternative process group. Central source frozen with v4:
`c56bb57b69405877a65124b623316f9b8bd769aa8f51db6f2481ff65325c5cdb`.
Main still owns the all8 initial dispatch/release. No current timer or broker
has been rebound. Current A4 wait120 and F4 wait600 remain unchanged.

## Historical v2 candidate (preserved, superseded)

- Node wrapper: `gpu/ovx3_ssh.sh`.
- Overlay: `/localhome/local-rohing/orch_r118_grid_parallel_candidate_source_20260915_v2`.
- `READY.json`: `cc21c6569eb0ba2a42b66b58ef8bd6a21e72943782b6de0b8b411286ace9523c`.
- `OVERLAY_SHA256.json`: `a8e4ef58c181e7ab6723d27e66f275e29405e678156c6dc4732808e33718299f`.
- `CPU_TESTS.json`: `f722e0697f2261da1b7b538060815ea5b538c8545d55485d82ad22727174ed88` (48 passed).
- `ACTUAL_RUNTIME_CPU.json`: `db6966e6f507fd464925774ac155c2b6cb4c17f65ac4f82c64733e7bcc625af1`.
- Original readout runtime: `/localhome/local-rohing/orch_r118_grid_shared_source_20260915_attempt2`;
  closure `03a2f241f2a043da9de28d9fc6d91fa7dc240b7ce6ef9fa08b2ff2bd92face9d`.
- Frozen Herschel hook in this overlay: `adec8fa260f8e192945cb499a369a6c95ceb35bf364a2c0da70097c0cbc43f8b`.
  The candidate includes `bootstrap_fresh_actor`, `wait_fresh_collection_go`,
  and `launch_at_boundary`; merge these exact absolute source pins into Main's
  common session/activation closure. Do not substitute a later mutable file.

Both actual repaired READY documents and both existing FINAL plans passed
metadata-only native validation. No model load, provider call, GPU science,
actor signal, sealed-content inspection, or activation occurred in that check.
Local combined checks: 150 passed; separate frozen VM A4 broker checks: 7 passed.
Native tests cover CPU fixtures and real isolated toy PIDfds, not GPU training.

## Entry points and transition order

`gpu/orch_r118_grid_parallel_run.py` exposes `snapshot`, `drain`, `validate`,
`guard`, `native`, and `timer`. All take `--plan ABS_JSON --sha256 EXACT_SHA`.
Invoke the **file path**, not an old immutable actor's module callback:

```sh
/localhome/local-rohing/v2/venv/bin/python -B \
  /localhome/local-rohing/orch_r118_grid_parallel_candidate_source_20260915_v2/gpu/orch_r118_grid_parallel_run.py \
  guard --plan ABS_FUTURE_EXEC_PLAN --sha256 EXACT_FUTURE_PLAN_SHA
```

The dispatcher supplies `R118_PARALLEL_SESSION`,
`R118_PARALLEL_SESSION_SHA256`, and `R118_PARALLEL_BRANCH`. Owner command
environment includes `CUDA_VISIBLE_DEVICES=` and `PYTHONDONTWRITEBYTECODE=1`;
working directory is the original runtime above. Guard sets the original
UUID for its own fresh native child only. F4 remains physical3/Wait600;
A4 physical7/Wait120. TRAIN cutoff16:55, hard17:02, native1858/parent298 remain.

1. At actual committed shared child + resident reload + completed fresh DEV,
   `snapshot` checks the exact repaired READY, model/optimizer hashes, previous
   submission, two TRAIN episodes, CARRY, contiguous charges, parent receipts,
   and absence of any next-cycle reservation/submission. It is not a release.
2. Main's explicit `R118_GRID_PARALLEL_DRAIN_V1`, status
   `MAIN_ALL8_COORDINATED_GO`, binds all eight branches, issue/expiry times and
   each own root, READY reference, generation/checkpoint, bounds, native and
   guard identities. Identities include PID/UID/boot ID/start ticks. `drain`
   uses an exact native PIDfd, holds briefly, checks the settled snapshot,
   resumes on a busy cursor, and only terminates the authorized settled native.
   Its authentic old guard writes `R118_SHARED_REPAIR_TERMINAL.json`; the
   earlier FAILED `SHARED_TERMINAL.json` is never hidden or rewritten.
3. Successful drain writes `BOUNDARY.json`, `RELEASE.json`, and `HANDOFF.json`
   in the selected new node-local output directory. `HANDOFF.json` has the
   central envelope `{root,bounds,release,predecessors,preserved_files,next_cycle}`,
   with `release` referencing the actual status-RELEASED receipt, not the
   older guard's FAILED terminal. Main still verifies all predecessors exited.
4. Main publishes/dispatches the common fresh session only after all eight
   releases. Each grid native loads the canonical committed adapter with
   `optimizer=None`, calls Herschel `bootstrap_fresh_actor`, then
   `wait_fresh_collection_go` before any new TRAIN call. Initial peer RNG is a
   declared NEW deterministic session/rank stream; it is not old peer RNG.
   Subsequent parallel checkpoints use the all-eight RNG sidecar. F1 alone
   restores and retains AdamW; this grid code never constructs an optimizer.
5. Two sequential original TRAIN episodes and reflection use the unchanged
   grid client. A real `PARTICIPANT_NNNNNN.json` is emitted after submission.
   Main writes `activation_directory/generation_NNNNNN.ref.json` containing
   the existing hook's exact activation `{path,sha256}`. No alternative Gloo
   rendezvous or serial fallback is created here.
6. `launch_at_boundary` receives the raw engine and peer `optimizer=None`.
   On return, require COMPLETE plus all-eight in-place ACKs, verify actual
   adapter identity, and update the read-only stage binding **without a second
   adapter load**. Preserve object identity within the new process.
7. Offload the same resident model to CPU around the original fresh-process
   DEV call, restore it afterward, and advance the cursor only on completion.
   Failed work is terminal for that era; no collection/update/readout retry.

Snapshot/drain plan fields: `runtime`, `candidate` reference, `root`, `branch`,
`repair_ready` reference, `common_root`, `common_config_sha256`, `cycle`,
`native_identity`, `output`; drain additionally has `drain_authorization`.

Future exec plan schema is `R118_GRID_PARALLEL_EXEC_V1`, with `runtime`,
`candidate`, `root`, `branch`, new root-local `directory`, `repair_ready`,
`boundary`, `release`, unchanged `bounds`, `activation_directory`,
`anchor_root`, `previous_final_plan`, two exact `old_final_identities`, and a
new separate `final_output`. All `*_reference`/reference values are
`{path,sha256}`; no plan for current actors has been written.

For Main's owner entry, `bootstrap_path` is a new root-local path reserved for
Herschel's bootstrap writer. `boundary.fresh_dev` references the prior cycle's
`readouts/NNNN/dev/COMPLETE.json`; `boundary.settled_cursor` references its
`cycles/NNNN/CYCLE_COMPLETE.json`. Both are included in preserved files.
Mounted/committed checkpoint hashes must equal the canonical shared child.

## Supervision, FINAL, and brokers

The new strict guard records its real identity and native PID, binds a new
`R118_GRID_PARALLEL_TERMINAL.json`, and enforces the original TRAIN cutoff.
Its new CPU timer starts before retiring exactly the old branch's two CPU
FINAL timers. No timer identity is inferred from a PID alone: require original
plan argument, command hash, UID, boot/start identity and empty CVD.
No current timer has been retired or rebound yet.

FINAL reuses the pinned original evaluator and Main's read-only
`R118_FINAL_SELECTION_V1` validator. Only output directory and actual
predecessor references change; same sealed8, decoder,17:00–17:20 eval-only
window and8calls. No FINAL call is added to TRAIN/parent ledgers. No latest-STATE
fallback, early FINAL, duplicate morning attempt, or parent access is permitted.

New `gpu/orch_r118_grid_parallel_a4_broker.py` is a future-only A4 binding over
the frozen existing HTTP transport. `--handoff` and `--handoff-sha256` bind the
actual node HANDOFF; every previously charged parent number and every received
request is skipped, without replay. It uses the new parallel terminal while
leaving both old failures intact. Frozen VM source is
`/tmp/orch_r118_grid_parallel_a4_broker_source_20260915_v1`; it is **not running**.
Hubble owns the corresponding F4 broker rebind. Neither current broker changes.

The algorithm is prospective average-gradient batch8 AdamW, **not serial-AdamW
equivalence** or proof of improved behavior. Actual future launch/release/PIDs,
settled boundary, bootstrap and collective performance remain unobserved.
