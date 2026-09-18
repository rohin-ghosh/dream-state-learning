# Node3 kept-life recovery — 2026-09-18

## Actual recovery cut, 17:15 UTC

- Observation GPU0: LOADED3111 at17:08:31UTC, native1941202/startticks45731595,
  REQUEST3114, ACT3125, SLEEP_RECIPE3140. Actual legacy recipe has no R227 key;
  default scaffold exclusion remains a disclosed gap, not “no exclusions live.”
- Perspective GPU3: dispatched17:11:02UTC; native startup/replay underway,
  no LOADED at17:14:40 cut. Other six are not launched at that cut.
- Four caption R227 receiving gates passed. All three math R227 receiving suites
  now pass122 tests each after the missing existing dependency was copied into
  new isolated sources; failed source/gate artifacts remain preserved.
- Dispatch is serial and requires an actual live LOADED before the next launch;
  every remaining dispatch requires R227 at both plan and THINK configuration.
- Original journals/checkpoints and failed tails remain preserved. Native horizons
  are September19 04:51:09UTC (GPU0) and04:54:40UTC (others), not a lease extension.
- The resumed plain Tool relay uses original dedup cursors. GPU0 ACT3125 received
  `ConnectionResetError`/`ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY`, not a score;
  shared scorer/transport repair is requested from its owner Leibniz.
- Classroom/GPU7/debate CPU attachment gates are ready and waiting for the exact
  required natives. Scripted Astra publishers do not invoke a model provider;
  new parent publication/render is pending, not inferred from daemon startup.
- Owned CPU tests:46PASS; receiving parent-only suite31PASS. No live learner
  was stopped, no retired root was revived, and no existing publication was reset.

## Historical initial diagnosis and preparation

Initial diagnosis cut16:50:11UTC. The eight kept lives exited with code124,
5–20 seconds before their own configured operator hard walls. The guarded
launcher runs `timeout` with a ten-second margin; its subsequent
`native_failed_preserve_no_retry` error is the wrapper's refusal to retry.
The inspected native logs contain no child exception or OOM evidence. Node3
uptime starts September13,10:02:17UTC; no reboot occurred in this interval.
At16:46:09 all eight devices had1MiB used and no compute processes; available
host RAM was987GiB. GPU activity is not lease evidence.

The existing user-confirmed/Fable-reported, host-bound lease receipt specifies
September26,03:03UTC. No lease extension or purchase is performed. New recovery
budgets are finite twelve-hour horizons from each preparation, additionally
capped by the existing reservation and six-hour physical-lease margin.
The former six-hour experiment budgets are not reused.

Scope is the five exact `r213_r226_caption_*_fork` lives on0/3/5/6/7 and
`r213_math_a`, `r213_math_b_fork`, `r213_math_c` on1/2/4. No obsolete/siege root
can enter the recovery allowlist. All original journal records remain; each
failure's stream/checkpoint/control is copied privately with SHA manifests.
Recovery appends the already-established saved-boundary reconciliation event,
restoring coherent adapter/optimizer/RNG plus saved working state in the SAME
journal. Post-boundary updates, outputs and inputs are inventoried as gaps,
not advertised as exact resident continuity. No raw targets/binaries are public.

Six focused recovery CPU tests and the37-test owned suite pass. Receiving
six-test checks pass. Per-life archive replay, checkpoint integrity and
resident-runtime tests are required before one-at-a-time dispatch. GPU0's
first CPU preflight rejected an offline inbox namespace mismatch before any
live journal mutation or launch; that attempt was retained, and replay now
uses the existing confined namespace rather than rewriting historical inputs.

This initial cut is NOT a LOADED claim. Actual subsequent LOADED/REQUEST/ACT
and renewed service receipts will be recorded separately. Existing learning
recipes/filter mismatches are retained, not silently upgraded. Parent workers
resume recorded turns, not epoch openers: normal response/checkpoint cadence,
changed parent intervention after three completed cycles, genuine human
priority. Main owns P3/scoring; node3 restores only its own feedback relay.
