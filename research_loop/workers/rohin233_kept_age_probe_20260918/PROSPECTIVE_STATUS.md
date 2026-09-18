# R233 prospective priority and capacity — 2026-09-18T12:23:03.372403+00:00

**Every-sleep metadata enrollment is NOT every-sleep testing.** The original
12:13:19UTC published cut remains unchanged in `QUEUE_COVERAGE.{json,md}`.
This supplement uses the two ledger snapshots bound in `CAPTURE_ROUND_LATEST.json`;
it is not a simultaneous fleet census.

## Current bound accounting

- 16 distinct native journals;590 enrolled ages;42 coherent captures;
5 eligible native ages;5 evaluated;0 probes running after age2 completed.
- 508 await capture;37 copied ages await exposure eligibility;
40 registered old C2 paths unavailable, not proven lost from all archives.
- 585 ages remain unevaluated. All metadata and explicit pending ages remain.
- First prospective-priority round actually captured14 ages across14 lives; the
other2 lives had no available post-frontier completion in these bound ledgers.
No life receives a second capture within a round before other eligible lives.
- Age2 COMPLETE 2026-09-18T12:13:25.037309+00:00:6144 actual child tokens,
53 raw accepted,15 independent-seed new-pixel events; parent0,updates0,unchanged
base/adapter. This supplements, not rewrites, the original four-evaluated cut.

| Life | Enrolled | Coherent captures | Eligible | Evaluated | Pending capture | Unavailable |
|---|---:|---:|---:|---:|---:|---:|
| C2 | 94 | 4 | 2 | 2 | 50 | 40 |
| P7 | 73 | 2 | 0 | 0 | 71 | 0 |
| GAME1_P3 | 58 | 2 | 0 | 0 | 56 | 0 |
| C0 | 46 | 3 | 1 | 1 | 43 | 0 |
| Astra7 | 16 | 1 | 0 | 0 | 15 | 0 |
| MATH_A | 49 | 2 | 0 | 0 | 47 | 0 |
| MATH_B_FORK | 56 | 2 | 0 | 0 | 54 | 0 |
| MATH_C | 62 | 2 | 0 | 0 | 60 | 0 |
| GAME_N3_0 | 19 | 2 | 0 | 0 | 17 | 0 |
| GAME_N3_3 | 17 | 2 | 0 | 0 | 15 | 0 |
| GAME_N3_5 | 16 | 2 | 0 | 0 | 14 | 0 |
| GAME_N3_6 | 16 | 2 | 0 | 0 | 14 | 0 |
| GAME_N3_7 | 21 | 2 | 0 | 0 | 19 | 0 |
| FRESH_R231 | 12 | 11 | 2 | 2 | 1 | 0 |
| R232_SIBLING_FROZEN | 25 | 2 | 0 | 0 | 23 | 0 |
| GAME_UNPARENTED_N2 | 10 | 1 | 0 | 0 | 9 | 0 |

## Scheduling policy applied now

`PROSPECTIVE_POLICY.json` freezes the16 source frontiers from the published
12:13:19UTC cut as the operational forward-capture baseline. Prospective means
COMPLETE record index strictly beyond that life's frontier. This is a new
scheduling boundary, not an invented time of the original R233 directive or a
claim that the ledgers contain usable completion timestamps.

`capture_priority.py` chooses the oldest available prospective completed source
per life, at most one per finite round, least-recently attempted life first.
`run_capture_round.py --execute` performed the first CPU-only round. Missing or
mismatched sources remain visibly pending; failed copies receive no capture
credit. Optional deep historical work is disabled by default and cannot outrank
available prospective sources. No powers-of-two or hidden age subsampling.
The independent old fresh-learner capture queue remains running unchanged; its
later copies require their own receipt before receiving aggregate capture credit.
No automatic all-backlog GPU dispatcher is claimed. Future prospective capture
rounds and source-exposure admission remain explicit operator work.

## Measured expansion plan, not a dispatch

At 2026-09-18T12:20:31.084517+00:00, physical6 and7 each had0MiB allocated and no GPU
processes after age2 completed. Devices0–5 still have protected workloads and
are not candidates, even when their instantaneous utilization is zero.
**One existing two-GPU probe lane; zero verified additional parallel lanes.**

The two completed sources took365.335s and378.830s including
load/verification: pooled observed9.68sources/hour, not a guaranteed steady
rate. The present unevaluated backlog would need60.5hours
at that rate before source/exposure delays. About15
further completions fit before13:59:30UTC only as a point estimate. This finite
allocation cannot clear the queue; do not say every-sleep testing is complete.

Expansion order: (1) retain6/7 for the existing serial battery; (2) have Main
identify an additional unreserved GPU pair within an existing allocation;
(3) obtain its owner acknowledgement and fresh physical/process census;
(4) validate exact runtime, base, adapter, judge, private DEVELOPMENT battery,
context and token-budget bindings; (5) measure one complete6144-token probe
with the same3 scenes/2 seeds before promising throughput or opening another
lane. Report load time, total time and peak memory. No hardware equivalence or
linear speedup is assumed. No new pair was assigned or dispatched here.

Do not repurpose0–5, change a production scorer's novelty state, colocate merely
because utilization is low, expose private panels, or trade the fixed-budget
parent-free evaluation for in-life parenting. No learner/scorer signals,
restarts, leases or utilization refills. Base and pair actual parenting evidence
remains in `PARENT_RENDER_LATEST.json` and `PAIR_PARENT_LATEST.json`; its guidance
is not added to age probes. Raw game acceptance is not certified humor, and
cross-lineage sources are not a causal age series.

Validation:28 focused CPU tests PASS, including fairness, journal identity,
prospective priority, explicit historical opt-in and preservation of all entries.
