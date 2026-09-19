# Pair retention receiver — CPU-tested, review required, not dispatched

2026-09-19 UTC. Non-material same-deadline continuity repair, preserving the
architecture, scientific claims, controls, visibility, and evidence. Worker-only
implementation; no live signals, dispatch, remote
writes, source staging, native restart, GPU/model load, commit, or push performed.
Boundary regression: 83 tests OK. Pair sidecar/preparer regression:
63 tests OK; 14 additional actual-source CPU integration tests pass against
each reconstructed epoch2 closure (28 executions). These are synthetic CPU
tests, NOT receipts claiming the
actual remote receiving source or checkpoint has passed validation.

**Epoch3 prepared locally, not delivered/admitted:** `prepared_epoch3_v1/SUMMARY.json`
and `EPOCH3_HANDOFF.md`. Exactly one existing history file changes relative to
epoch2, to the approved `8d44b459…16315` bytes. Each 209-file closure passes the
14 actual-source synthetic tests plus exact legacy/optimized history parity.
All epoch2/epoch1 bytes remain unchanged.

**Optional reserved preflight:** `RESERVED_PREFLIGHT_HANDOFF.md` documents the
executable opt-in path, distinct strategy approval, static receipt requirements,
same-handle race handling, hard 30-second cap and terminal expiry/retry gate.
Default coordinator ordering is unchanged. No live feasibility/admission is
claimed until all-in cost, actual owner transport/fence and confinement gates pass.

**Local epoch2 is now prepared:** use `prepared_epoch2_v2/SUMMARY.json` and
`EPOCH2_HANDOFF.md`. Both sealed sources contain 209 exact pinned Python files
plus the unchanged pinned startup text. `prepared_epoch2_v1` is retained earlier
local preparation evidence, not the selected transport input. Remote epoch1 is
untouched. No live receiving plan, checkpoint, guard admission, or parent rebind
is claimed by these source-preparation artifacts.

## Ready interface

`receiver.PairReceiver(...).hooks()` supplies all seven `ReceivingHooks`:
`verify_prepared`, `dependents_clear`, `verify_checkpoint`, `prepare_receiver`,
`recheck_checkpoint`, `verify_receiver`, and `dispatch_once`. Construction/import
does not activate anything. Main alone may pass the hooks to LinuxOperations and
the reviewed boundary coordinator after the remaining gates below are satisfied.

Constructor arguments:

```text
binding: exact boundary binding (boot/PID/start/UID/command/guard/journal/deadline)
staged: FINAL staged receipt, including new_source, new_source_pins,
        old_guard_sha256, changed (full old-to-new per-file delta)
cpu_receipt_path: real receiving-source CPU receipt described below
consumed_wall_receipt: {record: original WALL_EXTENDED, intent: exact intent}
python_executable: the already approved pair venv Python
parent_dependency_receipt_path: Kuhn/parent owner's exact fenced-delivery and
        durable existing-ledger proof; required before verify_prepared succeeds
```

`checkpoint_probe` is an optional test injection, not an operational bypass.
Operational instances leave it unset and execute the supplied `cpu_probe.py` with
CUDA visibility empty. No GPU API is initialized by that probe. Do not use a
synthetic callback or test receipt to authorize a real handoff.

Main prepares `prepared.new_plan` with only source-root/startup-path relocation
and omission of the consumed `authorized_wall_extension`. The pair plans do not
currently have checkpoint_tail_recovery: no new plan field is introduced. Tail
enrollment is an explicitly source-authorized receiving journal wrapper, with
the exact selection in the new source's `../control/PRESERVATION.json`.

Preparation makes per-attempt PLAN/GUARD/LEASE/ALLOCATION/CPU/RECEIVER artifacts,
and publishes PRESERVATION at the exact path required by ReceivingChild. Every
previous preservation version remains as PRESERVATION.<digest>.json. Before any
dispatch claim, another candidate can replace only the current sidecar pointer;
old artifacts remain. It refuses replacement after a handoff/dispatch is armed.
The checkpoint includes the same adapter, optimizer and Python/CPU/CUDA RNG;
saved state, prompts, rows, controls, root, and deadline remain unchanged.

Confinement is NOT replaced: guards are copied, with only artifact references,
their hashes, attempt directory and separately approved source pins changed.
copy_raw, host/device/allocation scope, resume flag, lease bounds, reservation
deadline and other guard fields remain unchanged. The new source's original
`gpu.orch_r125_continual_guard.validate` must pass in a CPU subprocess before
preparation returns. Dispatch uses exactly the existing `gpu.r232_recovery
dispatch --config ...` path, including its fresh privileged admission and original
systemd/device/UID confinement. There is no root/admission or management-policy
bypass. Existing provenance flags are preserved, never manufactured.

`dispatch_once` requires the exact exited token and still-live original deadline,
publishes an exclusive fsynced claim, then the handoff token before launch. A
failed/uncertain launch leaves the claim for main to reconcile; no blind retry.
This method was NOT executed against a real process. The unit test substitutes
Popen with an exception to exercise claim durability without launching anything.

## CPU-parent owner handoff

Restored parent services remain bound to their exact original native identities;
neither a new process with the same PID nor the dispatch supervisor is a valid
replacement. This receiver never changes a parent binding or delivery ledger.
See `TO_KUHN.md` for the concrete pre-handoff proof and post-LOADED responsibilities.

Before native handoff, the parent owner supplies a
`PAIR_RETENTION_PARENT_DEPENDENCIES_V1` receipt bound to `digest(binding)` and the
source epoch, fences deliveries, drains in-flight delivery, and pins all existing
delivery ledgers. The hooks rehash those ledgers and the proof before dispatch.
An absent receipt or changed ledger refuses the handoff; the receiver does not
manufacture the proof, fence parents, or relax dependency checks.

Preparation emits `attempt/PARENT_REBIND_REQUIRED.json` with the exact old native,
receiving plan/guard/source hashes, dependency proof, and required post-LOADED
evidence. It explicitly sets `new_native=null`, `automatic_pid_adoption=false`,
and `parent_rebind_allowed=false`. `RECEIVER.json` and the immutable handoff token
carry its path/hash. `DISPATCHED.json`, if main later dispatches, labels its PID
`DISPATCH_SUPERVISOR_NOT_NATIVE`, `loaded=false`, and `parent_rebind_allowed=false`.
Only the parent owner may issue a separate, exact post-LOADED rebind receipt;
these preparation/dispatch receipts never authorize parent adoption themselves.

## Source additions main must stage and authorize

The existing epoch1 staged receipts cover only the original three retention
changes and are insufficient for this receiver. Do not mutate those immutable
sources in place. `ports.proposed_ports(source, tested_tail_runtime)` returns
new bytes and a separate exact delta; it does not write the source tree.

It proposes only:

1. `gpu/r232_recovery.py`: one checked journal-install seam adds bind_journal;
   all original admission, confinement, learner/frozen classes and probes remain.
2. `gpu/pair_retention_runtime.py`: this worker's receiving journal wrapper.
3. `gpu/checkpoint_tail_runtime.py`: unchanged bytes supplied from the already
   tested rohin233 recovery worker implementation.

The wrapper subclasses the original learner or frozen journal. Its normal base
constructor acquires the original WRITER.lock before scan and before model load.
It verifies exact saved state and COMPLETE+LEARN plus INBOX-only tail, then records
a distinct RETENTION_SOURCE_ADOPTED epoch before the first THINK. It neither
extends the wall nor changes the saved-state payload. All original INBOX files
remain and the original native reader rescans them.

**Performance boundary:** this uses the tested checkpoint_tail_runtime scanner,
which hashes all retained prefix bytes but decodes only relevant INBOX/anchor
records and the current tail. It does not run historical stream-body replay.
The CPU preflight has a 120-second timeout, with no fallback to full replay.
It is NOT an O(tail) trusted-anchor open: startup hashes prefix bytes again.
The user accepts this correct existing hash-prefix path; O(tail) optimization is
not a preparation prerequisite. Main must measure the real scan cost with the
bounded CPU probe and retain timeout/failure evidence, without falling back to
historical body replay or changing deadlines. Tiny synthetic timings are not
pair-host startup estimates.

## Exact remaining gates / main handoff

1. Local preparation is complete in `prepared_epoch2_v2`. Main transports the
   selected new immutable sources (or exact overlay onto verified epoch1 copies),
   verifies their full pins plus startup hash, and binds the six-entry old-to-new
   delta into source-epoch authority. Main retains epoch1 without modification.
2. Run the real receiving source's guard, learner/frozen checkpoint+tail parity,
   source-epoch-before-THINK, pending-tail rejection, control/optimizer invariance,
   and restore/provenance tests. The 63 worker tests include mocked CPU probes;
   the additional 14-per-source tests execute the actual learner/frozen journal,
   scanner and wrapper using synthetic saved streams. Neither validates an actual
   host checkpoint or substitutes for existing admission.
3. Publish a real CPU receipt with `passed=True`, exact `source_pins`,
   `no_GPU_calls=True`, `checkpoint_tail_port_passed=True`, and
   `pair_controls_passed=True`, plus test logs/commands and hashes. The hook
   refuses absent/mismatched evidence. Do NOT copy the synthetic fixture receipt.
4. Supply the original consumed WALL_EXTENDED record/intent by known retained
   reference, not a full history replay. The boundary code verifies the consumed
   transition and point-rechecks the original record/intent while reserved.
5. Exercise `verify_prepared` and read-only `verify_checkpoint` / `prepare_receiver`
   on the actual fresh candidate before arming. Confirm scan time and byte counts;
   retain bounded failure/cost evidence if slow; O(tail) is not required.
   Keep the original native running; no signals are needed for these CPU probes.
6. Kuhn supplies the bound parent dependency proof and owns the post-LOADED exact
   native rebind, retaining all ledgers and delivered-message identities. No
   native handoff is permitted without that complete dependency proof.
7. Main reviews artifacts and activates the existing coordinator only after all
   gates pass. This worker has no CLI that automatically coordinates or dispatches.

## Tests

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s research_loop/workers/post_recovery_pair_retention_receiver_20260919 \
  -p 'test_*.py' -v
```

Tests cover seven-hook availability, exact checkpoint and sidecar preservation,
candidate re-anchoring without evidence deletion, unchanged guard/copy mapping,
source/CPU closure rejection, no replay fallback or guard bypass, durable
at-most-once dispatch claims, the narrow separate source delta, checkpoint
rechecks, source-epoch publication under the existing writer lock, mandatory
parent-owner dependency proof, refusal of ledger drift, and no automatic parent
PID adoption. Fixtures
stay inside this worker; signal/dispatch calls are prohibited or mocked.

Local source CPU receipts contain `live_handoff_authorization=false`; receiving
preflight rejects them as live-handoff proof. Main must obtain separately bound
actual-host evidence, not flip a flag in these immutable local receipts.
