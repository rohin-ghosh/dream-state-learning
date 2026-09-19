# Bounded C2 continuation — READY is not launch authorization

## Scope and frozen behavior

This is a small, standard-library read-only measurement wrapper, not a life
controller, service, new scientific test, training change, or policy change.
It reuses **unchanged** `observe.py` binding/capture/merge/select functions.
The existing 17-test files and their receipt remain byte-for-byte fixed.
Only this sidecar and its `continuation_run/` child may receive writes.
No watcher is launched while preparing this package.

Main must review the monitor, tests, this plan and `CONTINUATION_REVIEW.json`,
then supply a separate hash-bound approval. The READY review is deliberately
not sufficient to run. No Main approval file is created by this task.

## Exact starting point

- Baseline: **all nine** CAPTURE_01–CAPTURE_09, each individually hash/size pinned.
- Exact cursor: journal `260be8b8710a42559b291797c6e14983`, record **15917**,
  SHA256 `4b6f603b0132af327eeae5e00aefe4dae643672a2b031fd52bbec430ce1a3cc2`.
- Original native PID/start **1139778/30025875**, unchanged identity, original
  ovx3 route, helpers, policy/addendum and receiving-source checks.
- Last measured result remains **1/6 available; artifact 0/1 assessed; correct
  checked action 0/1; five future outcomes unknown**, at September 19, 2026,
  15:52:17 UTC. This package does not claim a fresher live observation.

`validate` is offline. It verifies every source/baseline pin, reconstructs the
contiguous baseline and reruns the existing selection against the saved binding.
It neither contacts ovx3 nor reads a new parent/provider result.

## Finite operation

Stop on the first of:

1. **Six** committed hash-linked ACTs under the unchanged first-six selection.
2. **At most 7,200 seconds** from this observer's initial start, including resumes.
3. **At most 25,000,000 bytes** of newly exported/generated observer receipts.
4. Any changed pin/identity, discontinuity, incomplete join, failed collection,
   competing collector, uncertain resume, or receipt-validation error.

Cadence is 90 seconds **after each completed poll**, including when catching up;
each poll requests at most 12 contiguous journal records. The cursor never jumps
to the live tail, and every successful capture participates in future selection.
An empty poll retains its exact cursor. Sleep UPDATE records are preserved, not
mistaken for ACTs. There is no semantic grading in this monitor.

Both the original wall deadline and monotonic deadline are durably retained.
A different local boot fails closed. The observer admits no read with 300 seconds
or less remaining; the frozen collector's SSH call has its existing 240-second
timeout, leaving local checkpoint allowance. Thus it normally stops early,
not by launching a final read at the two-hour boundary. No life/native runtime
deadline, lease, process, provider setting or learning recipe is changed.

The byte ceiling uses **conservative accounting**, not an estimate of actual
artifact success: reserve three receipts below 1,900,000 bytes plus 65,536 bytes
of bookkeeping before a poll. On success, charge their actual serialized sizes
plus that bookkeeping reserve. Failed/incomplete export attempts remain charged
at the full reservation and terminate. Startup/terminal bookkeeping also has a
65,536-byte reserve. Pre-existing baseline files are referenced, never recopied.
This can stop before the nominal 25 MB limit; it never admits an export without
headroom. Each saved JSON remains below 2 MB. Raw remote journal files, model
weights, checkpoints, credentials and sealed readouts are not copied.

## Durable receipts, failures and duplicate exclusion

- `CONTINUATION.lock`: nonblocking advisory exclusive lock held for the full run.
- Also check `/proc` argv for an already-running direct `observe.py capture` or
  `select` against this sidecar. Fail rather than launching a competitor. **Main
  must not start direct interactive collection after transferring ownership to
  the watcher**: the frozen standalone CLI does not participate in this new lock.
- `continuation_run/START.json`: exclusive durable initial budget/deadline.
- Per poll: exclusive `INTENT_NNNN.json`, `BINDING_NNNN.json`, `CAPTURE_NNNN.json`,
  `SELECTION_NNNN.json`, `STATE_NNNN.json`, with fsync and hash references.
- `LATEST.json`: fsynced temporary file plus atomic replacement; points to one
  immutable state/stop receipt. Existing captures and states are never overwritten.
- On restart, verify the immutable state/intent chain, every capture reference,
  exact cursor/hash continuity, deadline, accounting and saved selection. A
  completed state survives a lost/stale latest pointer; caps do not reset.
- An interrupted intent/export without a committed state is retained and produces
  a terminal **PARTIAL_INCOMPLETE_RESUME**, not a replay or skipped opportunity.
- A failed selection preserves the capture and any ACT-stage receipts as an
  **unknown failed slot**. Stop; do not replace it with a later easier ACT.
- `STOP.json`: terminal receipt and latest pointer. Restarting a stopped run does
  not begin another window or reset the two-hour/byte allowances.

Source/config pins are intentionally strict. In particular, a changed shared
collector registry requires review even if a different entry was edited. There
is no source-identity bypass, auto-rebinding, provider retry or runtime repair.
Storage failure can prevent a final pointer write; already-fsynced snapshots and
intents remain the recovery evidence, not evidence of successful completion.

## CLI and Main's review binding

From this directory, use the full review SHA printed in `CONTINUATION_READY.md`:

```bash
python3 -B continuation.py validate --review-sha256 REVIEW_SHA256
python3 -B -m unittest discover -s . -p 'test_continuation.py' -v
```

Only after review, **Main** creates `MAIN_CONTINUATION_APPROVAL.json` containing:

```json
{
  "status": "APPROVED_TO_RUN",
  "approved_by": "Main",
  "scope": "C2_READ_ONLY_FIRST_SIX_ACT_CONTINUATION",
  "review_sha256": "REVIEW_SHA256",
  "monitor_sha256": "MONITOR_SHA256"
}
```

Main hashes that exact approval file and starts the finite observer:

```bash
python3 -B continuation.py run --review-sha256 REVIEW_SHA256 --approval MAIN_CONTINUATION_APPROVAL.json --approval-sha256 APPROVAL_SHA256
```

No `nohup`, service install, timer, launch, or approval is performed by this
implementation task. The approval fields are an explicit operational review
binding, not a claim of cryptographic signer authentication. Parent consistency,
artifact correctness, checks and retention remain **manual evidence judgments**.
