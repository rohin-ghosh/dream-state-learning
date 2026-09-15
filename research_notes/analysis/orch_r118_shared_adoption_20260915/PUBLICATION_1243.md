# R118 publication checkpoint — September 15, 2026, 12:43 UTC

This checkpoint publishes operational evidence, not a successful learning claim.

- Shared initialization: actual at12:23:54; generation0 and zero shared updates
  still verified by Main at12:39:28. Prior F1cycle6 state is preserved, not newly
  earned joint-learning credit. See `INITIALIZED_ACTUAL_1224.json`.
- Open turns: Main reverified the exact historical F1/A1 TRAIN and F1 DEV hashes
  at12:39:28. Actual artifacts use `OPEN_TRAIN_*.json` and
  `open_readouts/readout_*/OPEN.json`, not `open_turn*`. The audit includes
  executed inspections, full continuation storage, and transient/protocol-only
  checkpoint distinctions. See `../R118_ROUTE_VISIBILITY_20260915_1136.md`.
- Grid failure and recovery: both initial shared runners failed because their
  immutable bundle omitted a runtime document. The repair includes the exact
  predecessor-pinned document, not current mutable prompt bytes. F4/A4 produced
  new continuations at12:38:52/54 using the already completed parent guidance;
  original charged calls and failures are retained. Broker successor delivery
  remains separately unverified. See the grid `R118_GRID_REPAIR_LIVE_1239.json`.
- Parent delivery: F1/F3 shared responses consumed COMPLETE at12:30:56; F2's
  second opportunity consumed COMPLETE at12:37:29. A3's first shared provider
  COMPLETE arrived after the child's deadline and remains child-MISSING. No
  retrospective rescore/retry or provider-refusal workaround is authorized.
- Fleet: `FLEET_1242.json` stores actual12:40:45–46 measurements:39/40 resident
  above1GiB,18/40 positive instantaneous utilization. These are not sustained
  throughput measurements. Node3physical0's confirmed math failure is assigned
  to its owner, not blindly overwritten with another job.
- Fresh L1 feed: only four unique admitted rows as of the12:29 owner audit,
  unchanged since09:52. Training updates exist; continuous fresh ingestion does
  not. TRAIN-only parented-derived candidates are being audited separately.

## Author-side validation

Seven worker allowlists were read and their source/test/receipt hashes checked.
The only changed-since-manifest path was the append-only R109_L1 journal; newer
grid recovery receipts are kept alongside the earlier failure evidence.

Main's system Python has no pytest. The initial pytest invocation therefore
did not run tests; the first unittest discovery also failed because `tests/`
is not an importable package for that explicit top-level setting. Corrected
standard-library discovery then ran **151 tests successfully in3.270seconds**:
shared adoption; grid ready/run/repair; math handoff/admission/broker; Claude
broker unit and integration tests. No new model/provider/GPU calls were needed.
Pytest-only route/code/release tests were not rerun by Main; their dated worker
local/native receipts remain separately attributed, not counted in the151.

At12:44, Hubble supplied a prospective F4 repair-terminal allowlist change and
its exact source/test hashes in COORDINATION. Main reran the broker unit and
integration suite:91 tests passed in0.562seconds. This later validation is a
separate run, not91 additional distinct tests. Only the named repair terminal
is admitted; old failures remain, and no old parent slot is retried.

Raw captures, weights, archives and provider transcripts remain node-local.
This publication does not change live prompts, held sets, shared CONFIG,
optimizer ownership, schedules, source eligibility or scientific claim bounds.
