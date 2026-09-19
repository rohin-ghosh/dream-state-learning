# Independent selected-checkpoint sampling accounting

Snapshot: 2026-09-19T14:29:40.638953+00:00. Block: **COMPLETE**. Generated tokens: 18432. Expected cells: 18.

## Per-seed results

| Arm | Seed | Complete cells | Scored | Accepted | New pixels | Generated tokens | Source verified |
|---|---:|---:|---:|---:|---:|---:|---|
| base | 23301 | 3 | 55 | 42 | 23 | 3072 | True |
| base | 23302 | 3 | 50 | 39 | 25 | 3072 | True |
| c2sleep51 | 23301 | 3 | 67 | 44 | 28 | 3072 | True |
| c2sleep51 | 23302 | 3 | 84 | 35 | 29 | 3072 | True |
| c2sleep117 | 23301 | 3 | 74 | 37 | 15 | 3072 | True |
| c2sleep117 | 23302 | 3 | 94 | 44 | 23 | 3072 | True |

## All cells

| Arm | Seed | Scene | Status | Scored | Accepted | New pixels | Tokens |
|---|---:|---|---|---:|---:|---:|---:|
| base | 23301 | agentdev_621cb5d0bdea9584dc9f | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 20 | 19 | 5 | 1024 |
| base | 23302 | agentdev_621cb5d0bdea9584dc9f | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 23 | 17 | 8 | 1024 |
| base | 23301 | agentdev_769e881d85fc5d27cb4c | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 18 | 17 | 14 | 1024 |
| base | 23302 | agentdev_769e881d85fc5d27cb4c | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 15 | 13 | 11 | 1024 |
| base | 23301 | agentdev_92a6a32f99def322d70e | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 17 | 6 | 4 | 1024 |
| base | 23302 | agentdev_92a6a32f99def322d70e | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 12 | 9 | 6 | 1024 |
| c2sleep51 | 23301 | agentdev_621cb5d0bdea9584dc9f | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 22 | 16 | 9 | 1024 |
| c2sleep51 | 23302 | agentdev_621cb5d0bdea9584dc9f | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 18 | 11 | 10 | 1024 |
| c2sleep51 | 23301 | agentdev_769e881d85fc5d27cb4c | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 23 | 13 | 11 | 1024 |
| c2sleep51 | 23302 | agentdev_769e881d85fc5d27cb4c | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 27 | 17 | 15 | 1024 |
| c2sleep51 | 23301 | agentdev_92a6a32f99def322d70e | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 22 | 15 | 8 | 1024 |
| c2sleep51 | 23302 | agentdev_92a6a32f99def322d70e | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 39 | 7 | 4 | 1024 |
| c2sleep117 | 23301 | agentdev_621cb5d0bdea9584dc9f | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 30 | 19 | 6 | 1024 |
| c2sleep117 | 23302 | agentdev_621cb5d0bdea9584dc9f | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 34 | 13 | 6 | 1024 |
| c2sleep117 | 23301 | agentdev_769e881d85fc5d27cb4c | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 21 | 7 | 6 | 1024 |
| c2sleep117 | 23302 | agentdev_769e881d85fc5d27cb4c | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 21 | 18 | 9 | 1024 |
| c2sleep117 | 23301 | agentdev_92a6a32f99def322d70e | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 23 | 11 | 3 | 1024 |
| c2sleep117 | 23302 | agentdev_92a6a32f99def322d70e | COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET | 39 | 13 | 8 | 1024 |

## Every matched-seed contrast

| Seed | Contrast | New-pixel delta | Sign |
|---:|---|---:|---|
| 23301 | c2sleep51_minus_base | 5 | positive |
| 23301 | c2sleep117_minus_base | -8 | negative |
| 23301 | c2sleep51_minus_c2sleep117 | 13 | positive |
| 23302 | c2sleep51_minus_base | 4 | positive |
| 23302 | c2sleep117_minus_base | -2 | negative |
| 23302 | c2sleep51_minus_c2sleep117 | 6 | positive |

## Reconciliation and limitations

Runtime report comparison: **MATCH**. See JSON for every comparison discrepancy.
Complete-only subtotals, partial cells, duplicate returns, rankless outcomes, and provenance issues are retained in JSON.
Tokens include THINK and ACT, not prompts, training compute, or judge compute. THINK candidates are also scored.
Across-seed totals are sums of independent seed-local novelty archives, not a union of distinct ideas.
Acceptance is the operational adopted-judge rule, not certified literal humor.
Selected-checkpoint sampling is NOT independent training replication, held-out transfer, or evidence isolating parenting/consolidation.
Weight provenance is checked from source-bound pre/post receipts, not by rereading tensors. No authentic rows or training policy changed.

