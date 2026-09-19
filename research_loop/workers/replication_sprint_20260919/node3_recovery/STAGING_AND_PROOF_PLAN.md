# MathB receiving-runtime proof plan — September19, 2026

## Implementation now present

`ws6_math_b_pending_entry.py` keeps the original r233→r226→r205 chain, uses the
same original guard, supervisor, peer hook, device confinement and privileged
admission, then installs the narrow source-bound pending-sleep startup.
`math_b_startup.py` and `math_b_runtime_candidate.py` complete the missing runtime
seam. `checkpoint_tail_runtime.py` is the unchanged existing raw-prefix-hash /
exact-COMPLETE / semantic-tail scanner, explicitly not full historical JSON
transition replay. `recovery_primitives.py` freezes the original strict recorder
and durable-write helper bodies; live changes in another workstream cannot
silently alter this recovery kernel.

The original native, guard, confinement, curriculum, decoder, row policy and
driver source files need **no edits**. Add the five top-level support files plus
`gpu/ws6_math_b_pending_entry.py` to a new source copy. All original source pins
must remain byte-identical. The execution PLAN differs only in `source_root`.
No original PLAN, GUARD, failed checkpoint or no-retry receipt is overwritten.

## Before staging or admission

1. Finish the approved archive copy and filesystem-restore verification. Source
   replacement/coalescing requires Main's separate explicit review. Confirm
   actual owner-available `f_bavail` afterward; reserved blocks do not count.
2. Freshly inspect PID/start identity and GPU2 occupancy. Do not signal any
   healthy native. Original node3 only; no use of ovx4 probe GPUs2/7.
3. Verify original guard→plan and all source pins, lease bytes, old no-retry exit,
   the full adapter/optimizer/RNG file hashes for sleep192 and the current head.
   Expected old head9555, COMPLETE9476, SLEEP_REQUEST9505. If changed, stop and
   inspect; do not reuse stale evidence or append any recovery/reset record.
4. Keep original execution ceiling1790272800 (2026-09-24 18:00UTC), original
   lease1790391780 and GPU2 UUID. No wall extension is proposed. The old PLAN's
   already-consumed wall declaration is recorded, not reapplied.

## New source-bound receiving artifacts

Use unique direct children of the original `r213_math_b_fork` directory:
`source_ws6_pending_math_b_<UTC>` and `control_ws6_pending_math_b_<UTC>`.
The unique source name is checked by startup and remains compatible with the
original r233/r226 identity resolution. Preserve all original guest-root→host
raw BindPaths exactly.

- Copy the original source; add the five support modules and entrypoint. Preserve
  a source-delta manifest showing original pins unchanged and only additions.
- In the new control, preserve byte-identical original PLAN separately and
  generate the original three-row pending-sleep candidate from actual retained
  COMPLETE/request/suffix records. Pin candidate bytes and content digest.
- Generate a new PLAN with only `source_root` changed. Do not remove the
  already-consumed wall declaration or add a preupdate-recovery flag.
- Selection uses guest `plan.root/stream`, actual journal ID, original COMPLETE
  index+hash and positive measured tail bounds. **The correction ledger life ID
  is `R213_NEW_MATH_B`, not the directory name.** Its required sidecar is
  `correction_ledger.json` / `R197_CORRECTION_CYCLE`. Never replace or skip it.
- Manifest schema `NODE3_MATH_B_INTERRUPTED_SLEEP_STARTUP_V1` binds original PLAN,
  execution PLAN SHA, staged source, candidate and selection. Add its byte-bound
  descriptor as new GUARD `pending_sleep_recovery`. All original guard checks
  still apply to the complete staged Python closure, lease, allocation, CPU
  receipt, host, GPU, wall, namespace and dispatch identity.
- Run source-bound receiving CPU tests/import checks in the original interpreter
  with CUDA hidden; publish real CPU/provenance receipts and dated Builder entry.
  Main must integrate the scoped Builder line into project COORDINATION before
  an actual GPU launch; this workstream does not edit outside its assigned scope.
- Use the normal original dispatch/probe/privileged scan/child/native chain with
  the new module. A nonroot/stale/unclear admission remains a hard failure;
  no guard relaxation, alternate credentials, seal bypass or implicit retry.

## Expected proof sequence, not yet observed on a real GPU

1. Existing exclusive WRITER lock acquired; every retained prefix record's
   bytes/chain/intents hashed, original COMPLETE pinned, full tail replayed,
   pending580 rows/frontier577 retained; correction sidecar source-bound.
2. Exclusive stable recovery-attempt claim; actual saved step9740 optimizer,
   adapter and RNG loaded. The lost resident post-generation/post-update RNG is
   **not** claimed preserved. All48 old UPDATE receipts remain historical.
3. Original full48-update sleep executes once on all three pending rows. This
   is new recovery compute9740→9788, not a continuation from an unsaved9788.
   No generation, tool action or provider request is replayed.
4. New unique checkpoint with exact durable COMMIT → original SLEEP_COMPLETE
   → paired R184_LEARN_COMPLETE → LOADED → original resident Think–Act loop.
   No second model reload, discarded rows, replayed wall declaration or filters.
5. Capture actual LOADED→REQUEST→RESPONSE→ACT record IDs/times and source hashes;
   report outage from the05:56:19UTC exit to real LOADED and first response.
6. Only then perform source-bound parent rebind with preserved ledgers. Keep the
   protected-seven-native prerequisite unchanged. No duplicate publisher and
   no retry of prior401 requests. If that prerequisite prevents attachment until
   peers recover, report it rather than silently running a substitute parent.

Failure after attempt creation preserves everything and consumes the attempt.
Saved-but-unpublished COMMIT or COMPLETE-without-LEARN requires explicit
reconciliation, never another automatic48-update run.

## Current CPU evidence and honest limitations

`CPU_TESTS_INTEGRATED.txt`:62 tests pass at13:49:52UTC, including9 actual-journal
startup tests,5 original-confinement-chain tests and6 archive/restore tests.
The receiving startup test reaches synthetic LOADED→REQUEST→RESPONSE→ACT while
preserving old journal bytes, pending rows and correction sidecar. This is a
CPU child fixture, **not** a real native/model or fresh privileged admission.
No source staging on node3, actual LOADED, parent rebind or GPU recovery is
claimed while owner-available storage remains zero.
