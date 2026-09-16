# R140 bounded delivery audit — 2026-09-16

Event window: **02:34:26.838465–03:34:26.838465 UTC**, exactly 60 minutes.
Actor identities/start ticks verified alive at window end; controller brokers verified alive at 03:31:34 UTC. Full roots, source pins and immutable uptake witnesses are in F1.json, F2.json and A2.json.

| Lane | Queue publications in window | Native applied in window | Actual completed native-call evidence |
|---|---|---|---|
| F1 | 2 SILENT | 1 SILENT, 2 historical MISSING | 119 joined to C57 CALL_003136; SILENT consumption, **not guidance injection** |
| F2 | 4 COMPLETE | 2 COMPLETE current epoch; 2 MISSING predecessor | C46E0/E1 exact guidance in one completed C47 CALL_00001187 |
| A2 | 4 COMPLETE, 4 SILENT | 4 COMPLETE, 3 SILENT, 1 MISSING | C39–42 E1 exact guidance in four completed calls, C40–43 |

Guidance equality was checked in memory on the node against actual user-message inputs; no raw text exported. Publication counts and applied counts use their respective event timestamps, not an assumed one-to-one population. In particular, A2 C39E1 publication predates the window but uptake is inside it. F2 predecessor C43 missing events have aged out; C44 remains in-window. Historical dispositions are unchanged.

Pending at window end: F1 120 SILENT; F2 C47E0/E1 COMPLETE; A2 C43E0 SILENT / E1 COMPLETE. These are **not yet native uptake**.

| Lane | Actor / broker PID | Saved optimizer steps | Active cycle unsaved updates |
|---|---|---|---|
| F1 | 2664733 / 2281435 | 21489 at C56 (+541 since C55 resume) | C57: 170 → 291 |
| F2 | 2627464 / 2229344 | 16460 at C46 (+479 since launch) | C47: 203 → 234 → 265 |
| A2 | 4156720 / 2017450 | 16509 at C42 | C43: 70 → 113 → 182 → 225 |

Unsaved updates are not added to saved optimizer counts; sample intervals differ and do not establish an hourly update rate. No current actor terminal observed. A2 uses runtime_recovery5; the old root GUARD_TERMINAL is historical, not a present failure.

Conclusion: F2 and A2 have actual parent-guidance uptake plus continuing training. F1 has actual SILENT-disposition consumption plus continuing training. This is transport/liveness evidence only, not scientific success, behavioral improvement, reasoning evidence or retained learning.

Read-only node/controller inspection only; no model/provider calls, launches, signals, source/live-plan changes, Git/shared-ledger edits, sealed-evaluation reads or F4 work. Only this audit directory is written.

Follow-up integrity spot-check via the authorized node wrapper independently rehashed the F1 C57, F2 C47 and A2 C43 completed-call witnesses: all three match the lane receipts. A separately requested normalizer review is in NORMALIZER_REVIEW.md; that review includes only a hash check of its referenced historical F4 failed call, not a F4 delivery audit.
