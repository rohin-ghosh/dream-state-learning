# R232 correction evidence and manual review

Collector/queue cut: 2026-09-18T11:12:47.936379+00:00
New manual review: 2026-09-18T11:30:28.600851+00:00; separate receipt capture11:22:05–11:22:08UTC.

Eight actual post-cut ACTs newly reviewed across five lives; see `POSTCUT_SEMANTIC_REVIEW_1122.md` and its JSON.
The collector does NOT perform new semantic review. Received ranges are not semantic coverage. Unknown is not level0 failure.
No level3, checkpoint capture, lifetime-negative claim, or live-control change. Queue/cursor history remains unchanged.

| Life | Received records | ACTs received | Selected corrections reviewed | Highest bounded level | Status |
| --- | --- | ---: | ---: | --- | --- |
| C2 | 5501–9153 | 51 | 2 | 1 | REVIEWED_PARTIAL |
| P7 | 2085–3561 | 25 | 1 | 0 | REVIEWED_PARTIAL |
| C0 | 0–2219 | 36 | 2 | 0 | REVIEWED_PARTIAL |
| Astra7 | 0–837 | 10 | 0 | unknown | SEMANTIC_REVIEW_PENDING_NOT_A_LEVEL0_FAILURE |
| GAME1_P3 | 1390–2801 | 26 | 1 | 0 | REVIEWED_PARTIAL |
| MATH_A | 0–2728 | 45 | 3 | 0 | REVIEWED_PARTIAL |
| MATH_B_FORK | 0–2406 | 51 | 2 | 1 | REVIEWED_PARTIAL |
| MATH_C | 0–2459 | 56 | 3 | 1 | REVIEWED_PARTIAL |
| GAME_N3_0 | 0–1472 | 27 | 0 | unknown | SEMANTIC_REVIEW_PENDING_NOT_A_LEVEL0_FAILURE |
| GAME_N3_3 | 5–1578 | 35 | 0 | unknown | SEMANTIC_REVIEW_PENDING_NOT_A_LEVEL0_FAILURE |
| GAME_N3_5 | 0–1436 | 32 | 0 | unknown | SEMANTIC_REVIEW_PENDING_NOT_A_LEVEL0_FAILURE |
| GAME_N3_6 | 0–1472 | 30 | 0 | unknown | SEMANTIC_REVIEW_PENDING_NOT_A_LEVEL0_FAILURE |
| GAME_N3_7 | 0–1451 | 22 | 0 | unknown | SEMANTIC_REVIEW_PENDING_NOT_A_LEVEL0_FAILURE |
| GAME_UNPARENTED_N2 | 0–875 | 17 | 0 | unknown | SEMANTIC_REVIEW_PENDING_NOT_A_LEVEL0_FAILURE |
| FRESH_R231 | 0–475 | 6 | 3 | 2 | REVIEWED_PARTIAL |
| GAME_FROZEN_BASE | ?–? | ? | 0 | unknown | NON_NATIVE_LOG_CONTRACT_PENDING_OWNER |
| R232_SIBLING_LEARNER | ?–? | ? | 0 | unknown | ALIAS_OF_FRESH_R231_SAME_JOURNAL_RECOVERY_LOADED172_GAP_DECLARED |
| R232_SIBLING_FROZEN | 0–372 | 11 | 4 | 2 | REVIEWED_PARTIAL |
