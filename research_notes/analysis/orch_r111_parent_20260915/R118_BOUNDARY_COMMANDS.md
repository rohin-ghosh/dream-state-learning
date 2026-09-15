# Route handoff candidate — 2026-09-15 11:45 UTC

## Current decision: preserve running lives

F1 remains 120-second wait / max parent effort / max head effort. Hubble's
diagnosed provider safeguard refusals are not latency. There is no authorization
to retry, rephrase, reroute, or lower effort to get around those refusals.
WAIT600 is a prospective source candidate only, not active configuration.
An actual timing change requires demonstrated latency or an explicit general
transport instruction, not refusal remediation. Old request deadlines, source
records, and all consumed charges remain unchanged.

Main's visibility audit `81476887` is authoritative; no duplicate semantic or
visibility audit was performed here. No shared coordinator was initialized.

## Original v3 has no stop marker

The live F1/A1 `gpu.orch_r111_route_pair.py` does **not** poll STOP_AFTER_CYCLE.
Creating that marker on an original life does nothing. Actor-only SIGTERM is
unsafe for handoff because the existing supervisor restarts it.

The new external controller can release at a completed cycle without waiting
for the whole life. It is explicit opt-in, not a running observer or daemon:

1. Pin actor and supervisor by PID, start ticks, UID, boot ID, command hash,
   original root, CVD, first PYTHONPATH source, and hashed host binding. Recheck
   physical UUID with `nvidia-smi`; obtain the kernel minor from the matching
   `/proc/driver/nvidia/gpus/*/information` and validate the character device.
2. Wait for the last required post-sleep OPEN (and, when due, FINAL) readout to
   finish. Acquire the **existing** RESERVATIONS.jsonl flock. No source injection
   or live-plan edit is involved.
3. Let the original actor finish readout/process bookkeeping and write its own
   cycle COMPLETE. The lock blocks any next native reservation. If a next-cycle
   reservation won the race, release the lock and keep the life running.
4. Temporarily stop the exact supervisor and actor via pinned pidfds. Verify
   latest checkpoint/optimizer/adapter/carry hashes, settled current native and
   parent calls (MISSING is settled, not success), and no next-cycle charge.
5. Save BOUNDARY.json; terminate the supervisor first and verify its exit, then
   terminate the actor and verify its exit. Never SIGKILL. Preserve original
   captures and any original actor CRASH receipt; do not fabricate TERMINAL.
6. Write RELEASED.json only after exits and unchanged-ledger verification. An
   error before termination resumes stopped processes. A failure after supervisor
   termination is explicitly marked in ERROR.json and requires owned recovery;
   the controller does not claim a release or automatically replay work.

An OS SIGKILL or machine failure cannot run Python cleanup. Do not kill the
controller abruptly; use its CANCEL file or SIGTERM. Its normal SIGTERM handler
raises through cleanup. Controller expiry releases locks and leaves work running.

## Actual prepared node-local requests — NOT ARMED

Controller source root:
`/localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2`

Source SHA256:
`acb0e1b95a457ef6a88bbc7ae8cd50445d04188142361d7299e7948f17c7b508`

| Branch | Physical | Actor / supervisor | Request SHA256 |
|---|---:|---|---|
| F1 | 0 | 356208 / 356167 | 7cac4cca2fdc93ecd58462d34347e662646c144c824e6b33778e8c498fce6b20 |
| A1 | 4 | 459948 / 459875 | c34ed07b65c04b2f5f37aeb4717b42850ff2ae80ec6b0b319e206ddd6d628486 |

Requests live under `readiness/F1/REQUEST.json` and
`readiness/A1/REQUEST.json` inside that source root. Both were freshly bound at
11:45:23 UTC, expire at approximately **12:45:23 UTC on September 15, 2026**,
and contain `armed=false`. Kernel minors were 0 and 4 respectively. No controller
has been executed. No authorization file was created.

These pin the current actor attempt. If recovery changes either identity or the
expiry passes, prepare a **new** request in a new empty directory; never amend an
old request or reuse its authorization.

## Runnable handoff command — only after Main coordinates all eight

Main must first confirm all eight clients are ready, the latest shared successor
including empty-cycle resume is bound/tested, and the common handoff is
coordinated. Then create an **AUTH.json beside each selected REQUEST.json**:

```json
{
  "request_sha256": "COPY_THE_EXACT_BRANCH_REQUEST_SHA_ABOVE",
  "purpose": "SHARED_ADOPTION",
  "authorized": true,
  "all_eight_ready": true,
  "common_handoff_coordinated": true
}
```

Do not set those booleans speculatively. The following is the exact command for
F1; change both `readiness/F1` segments to `readiness/A1` for A1:

```bash
bash gpu/ovx3_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/gpu/orch_r111_route_boundary.py execute --request /localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/readiness/F1/REQUEST.json --authorization /localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/readiness/F1/AUTH.json'
```

Run the branch commands concurrently in separate terminals if both are being
handed over; a foreground invocation waits for that branch's safe boundary.
Inspect ARMED.json for controller PID, BOUNDARY.json for original completion and
latest checkpoint references, and RELEASED.json for actual exits. The command
does **not** initialize the shared learner or launch its successor. Before the
next GPU process, use the existing strict privileged admission path.

To cancel before release, create `CANCEL` beside the branch REQUEST.json.
Preparation, authorization, arming, and actual release are separate states.

Fresh preparation, if the current request expires (choose a new empty directory
and an expiry within the original lease/call wall), uses:

```bash
bash gpu/ovx3_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/gpu/orch_r111_route_boundary.py prepare --root /localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1 --request /ABSOLUTE/NEW/EMPTY/DIRECTORY/REQUEST.json --expires-unix ACTUAL_FUTURE_UNIX_WITHIN_LIFE --purpose SHARED_ADOPTION'
```

## Empty next-cycle START and shared activation

An original actor can write the next START before blocking on the reservation
lock. That START is preserved verbatim; it is **not** a consumed task or a reason
to skip its two task IDs. New local shared successor code accepts this top-level
addition to its prospectively published PLAN:

```json
{
  "route_boundary_release": {
    "path": "/absolute/selected/handoff/RELEASED.json",
    "sha256": "ACTUAL_RELEASED_FILE_SHA256"
  }
}
```

It verifies the exact release/boundary and unchanged empty-cycle ledger, resumes
that same cycle/task cursor, and writes RESUMED_START_<time>.json instead of
overwriting the original START. Nonempty partial cycles are never replayed.
Original caps, cycle ceiling, optimizer history and actual consumed counters are
not reset. The shared source now imports the new boundary helper and its readiness
source closure includes that helper. The already published node-local v1 READY
files are unchanged; **they do not by themselves attest to this v2 integration**.
Publish/test a fresh successor closure before arming a common handoff.

Use the latest original COMPLETE/checkpoint captured at actual release for
adoption, never the historical cycle2 candidate. Existing adoption_inputs can
read it because original COMPLETE is retained, not externally fabricated.

## Test evidence and limitations

- Local: **174 passed, 56 subtests passed, 1 skipped** across boundary/wait,
  original route, v4, shared client/readiness, and Main coordinator tests. The
  local skip is Torch/PEFT absent; prior native shared CPU coverage is preserved.
- Node-local boundary v2: **21 passed**, CUDA hidden. Includes real owned CPU
  subprocess pidfd release and failure cleanup, actual flock blocking, identity
  drift, settled MISSING, pending native/parent rejection, next-reservation race,
  FINAL crossing, checkpoint drift, and empty-cycle cursor preservation.
- Native v1 prepare failed on unsupported `nvidia-smi minor_number` query before
  any request or signal. V2 uses supported index/UUID query plus kernel mapping;
  regression tested and both actual branch preparations passed.
- No actual GPU handoff, new GPU launch, WAIT600 uptake, or pooled update is
  claimed by these CPU and read-only preparation receipts.
