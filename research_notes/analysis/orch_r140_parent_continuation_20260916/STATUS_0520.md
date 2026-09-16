# Astra segments and hourly publications — September 16, 2026

Observation: **05:19:38 UTC**. Window: **04:19:38–05:19:38 UTC**.
Source: `HOURLY_PUBLICATIONS_0520.json`; timestamps inside the receipt define the window.

F1, F2 and F4 have already completed the prospective Astra handoffs described
in `STATUS_0402.md`. Do not reset or hand them off again. At this observation,
the expected PID/start-ticks/command identities still match for F1, F2, F4
and A2. Historical Fable turns and refused/MISSING requests are unchanged;
none were replayed.

| Lane | COMPLETE publications | SILENT publications | MISSING publications |
|---|---:|---:|---:|
| F1 | 0 | 4 | 0 |
| A1 | 1 | 4 | 0 |
| F2 | 5 | 1 | 0 |
| A2 | 4 | 3 | 0 |
| F3 | 0 | 0 | 0 |
| A3 | 0 | 0 | 0 |
| F4 | 17 | 5 | 0 |
| A4 | 0 | 0 | 0 |

These are **queue publications, not measured native uptake or a delivery
rate over all requested slots**. Missing slots without a response are absent
from this denominator. SILENT is not substantive guidance. All model-attributed
publications in this window identify Astra. Earlier native-uptake proofs remain
in `STATUS_0402.md` and the linked delivery receipts; they are not new hourly counts.

F2's counters, last written **05:06:43 UTC**, show 19,460 optimizer steps,
2,806,367 child-token exposures, 364,591 anchor-token exposures, 1,348 native
calls and 146 parent entries. A2's counters, last written **05:09:49 UTC**,
show 19,515 optimizer steps, 3,096,542 child-token exposures, 365,611 anchor-token
exposures, 1,168 native calls and 122 parent entries. Both exceed their 04:02
snapshots (17,436 and 17,487 steps respectively): A2 is advancing, not stuck at
the earlier 01:51 counter. These are cumulative counters, not instantaneous
training utilization. F4 remains elicitation-only with zero optimizer steps.

No retained-learning, richness or paper-scope success is established by these
operational receipts. The research goal remains unproven.
