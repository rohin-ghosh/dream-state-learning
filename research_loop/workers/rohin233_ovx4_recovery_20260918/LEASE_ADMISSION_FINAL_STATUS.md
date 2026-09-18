# Non-material enrollment lease-admission repair

**Actually live:** successor CPU PID3524450, outer timeout3524448, on the operator
VM; LOADED **2026-09-18 19:11:08.991879UTC**. Only prior CPU enrollment3046824 was
replaced after its complete polling round, with no active subprocess. No native,
pair, scorer or parent was signalled. Metadata-only handoff gap: **0.059679s**.

Both existing ledger locks, registrations, sixteen exact roots/journal identities,
all **968 prior enrolled entries**, and prior cursors are preserved. First complete
poll reports969 entries, zero changed historical entries and zero cursor regressions.
No adapter capture, evaluation or backlog probe dispatcher was started. Subsequent
polls remain healthy; counts beyond this cut belong to their timestamped receipts.

## Source admission now enforced

|Source alias|Source cutoff (UTC)|Registered roots|
|---|---|---:|
|node2|2026-09-20 18:00|3|
|node5|2026-09-20 18:00|1|
|node3|2026-09-24 18:00|8|
|node4|2026-09-25 18:00|2|
|ovx4|2026-09-30 18:00|2|

These are the supplied existing-allocation operational cutoffs, already including
the six-hour lease margin; no lease was purchased, extended or inferred.

- Before **each** remote read and again immediately before dispatch, require
  `now < min(source_cutoff, service_end) - 35 seconds`.
- Caller timeout remains30seconds. The receiving **read-only metadata subprocess**
  checks its own clock before reading, and arms a maximum30-second alarm that
  expires no later than effective cutoff minus5seconds. No learner receives it.
- Unknown wrappers fail closed. Existing wrapper bytes, registrations, driver and
  reader sources are hash-bound. Roots,64-record pages, journal/COMMIT verification
  and measurement semantics are unchanged.
- Expired/too-close sources become `SOURCE_LEASE_CLOSED_NO_REMOTE_READ`; retained
  ages/cursors are not erased or zeroed, and other in-allocation sources continue.
- The operator-VM process retains its existing September30 17:59:30 application
  bound; the actual outer timeout is slightly earlier. This is distinct from
  each target's earlier access cutoff.

Sixteen focused tests passed before handoff. Final focused suite: **20 PASS**
(17 admission/handoff tests plus3 support-census tests), including mixed expired/
live targets, zero-contact denial, clock advance before dispatch, receiver-side
expiry, exact old-PID/start/command identity, retained entries and monotone cursors.

## Main integration contract

Use `SUPPORT_COMPONENT_TABLE.json`, schema **R233_SUPPORT_COMPONENT_TABLE_V2**.
The machine-readable contract is `SUPPORT_COMPONENT_SCHEMA.json`.

Required top-level fields: `schema`, `unix` (Unix seconds), `rows`.
Each row requires `name`, `actual_host_alias`, `pid` (integer/null), `start_utc`
(UTC ISO8601/null), `actual_deadline` (UTC ISO8601/null), and `proof` (object array).
Optional `start_ticks` and `observed_unix` bind process identity/read time.

The `every_sleep_enrollment` row adds `source_admission` with policy,30-second
caller timeout, receiver-alarm flag,5-second cleanup margin, unchanged-root count,
registration hashes and sixteen `targets`. Each target includes `life`,
`source_host_alias`, `source_cutoff_utc`, `effective_cutoff_utc`, `latest_start_utc`
(exclusive admission boundary), and `receiver_finish_utc`.
Any `allowed`/`observed_unix` fields describe that observation cut, not a promise
of future access. Integrators should use the cutoff fields and latest poll receipt.

Only enrollment is freshly replaced/observed in this update. Other support rows
retain their earlier evidence: top-level `baseline_census_unix`, `updated_components`
and `update_kind` make that distinction explicit. The retired enrollment row is
preserved under `superseded_components`; do not count it as an active process.

Actual rollout evidence: `LEASE_ADMISSION_RENEWED.json`.
Post-handoff continuity/source verification: `LEASE_ADMISSION_VERIFIED_CUT.json`.
Do not interpret the enrollment total as captured/evaluated ages. **A bounded
backlog probe dispatcher remains absent and is outside this repair.**
