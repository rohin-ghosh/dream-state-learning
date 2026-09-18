# P3 retry1 CPU attachment — actual cut September 18, 2026 19:45:42 UTC

| Component | Actual evidence | Status |
| --- | --- | --- |
| Single local CPU waiter | PID3671383, startticks186769383; started19:44:35.811UTC; same identity alive19:45:42UTC | ARMED, not a learner |
| Retry observer | Successful remote polls19:44:36.917UTC and19:45:39.407UTC; recovery receipt SHA9c35e4885feeef2a6b0d289b6db96f6fb9cc8a0308e63fe41a7d6e4bc0a95731 | CPU replay / LOAD pending |
| Retry native | No new retry LOAD, binding or WALL receipt at the observed cut | NOT claimed loaded/alive |
| Original xhigh parent | Real fixed loader/config validated in a fresh process; existing seed/turn ledger and single-writer lock checked; no parent start receipt | Attachment waits for verified retry LOAD |
| Remote endpoint | Exact host/user check and existing opening/cursor-reader preflight passed; five CPU-file hashes verified | Deployed only in existing recovery CPU directory |

Poll cadence: 30 seconds after each observation. Waiter and eventual parent
bound: **September 25, 2026 18:00 UTC**, Unix1790359200. This is an authorized
experiment horizon, not a new independent provider-expiry assertion. Local
waiter inherits its provider environment; neither tmux environment inheritance
nor persisted credentials are used. The private waiter log is empty at this cut.

The gate verifies same journal/COMPLETE5243/sleep153, the actual retry recovery
record and immutable receipt, actual new LOAD after WALL, PID/startticks/source/
command/guard and source manifest. Historical failed LOAD5299 is not current.
Original and retry recovery events are both supported by the CPU cursor reader.
Attachment preserves the original xhigh ledger and one-response cadence; no new
opener, GPU dispatch, learner signal, native source edit or journal is created.
Validation/spawn uncertainty is terminal to automatic attachment, not a reason
to duplicate a parent. Actual provider response, publication and child rendering
remain **pending**, not implied by this armed receipt.

Tests: **29 local retry tests + 5 unchanged Main lease-loader tests PASS**;
the same **29 retry tests PASS on receiving CPU**. Commands and the dated
Builder entry are in `P3_RETRY_BUILDER.md`; outputs are in
`P3_RETRY_CPU_TESTS.txt` and `P3_RETRY_RECEIVING_TESTS.txt`.

Owned implementation: `p3_retry_observe.py`, `p3_retry_endpoint.py`,
`p3_retry_parent.py`, `p3_retry_waiter.py`, `p3_retry_test_cpu.py`.
Sanitized evidence: `P3_RETRY_DEPLOYED.json`,
`P3_RETRY_ENDPOINT_PREFLIGHT.json`, `P3_RETRY_WAITER_STARTED.json`,
`P3_RETRY_STATUS.json`. This published status is a dated cut; the running
waiter updates only its local status. Future binding, full LOAD/parent manifests
and private logs remain operational artifacts, not automatic public exports.

Main's auxiliary recovery controller, correction cache, R227 source port,
native launch, lease loader, renewal helpers and attempt1 artifacts are untouched.
