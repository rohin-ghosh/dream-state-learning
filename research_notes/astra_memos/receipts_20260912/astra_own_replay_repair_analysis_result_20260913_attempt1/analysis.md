# Own-source replay repair: independent local reduction

| Seed | Arm | Exact eligible | Paraphrase eligible | Held content | Canary content | LR0 losses held/canary | Exploratory screen |
|---|---|---|---|---|---|---|---|
| 0 | REPLAY | 10/14 | 10/14 | 47/48 | 12/12 | 0/0 | True |
| 0 | EXTRA_MEMORY | 13/14 | 10/14 | 47/48 | 12/12 | 0/0 | True |
| 1 | REPLAY | 6/8 | 6/8 | 48/48 | 12/12 | 0/0 | False |
| 1 | EXTRA_MEMORY | 7/8 | 6/8 | 46/48 | 12/12 | 2/0 | False |
| 2 | REPLAY | 5/8 | 3/8 | 48/48 | 12/12 | 0/0 | True |
| 2 | EXTRA_MEMORY | 7/8 | 7/8 | 42/48 | 12/12 | 6/0 | False |

## Dose and cost
- Seed 0 REPLAY: 304 updates; lineage/token costs and itemwise paired labels in JSON.
- Seed 0 EXTRA_MEMORY: 304 updates; lineage/token costs and itemwise paired labels in JSON.
- Seed 1 REPLAY: 256 updates; lineage/token costs and itemwise paired labels in JSON.
- Seed 1 EXTRA_MEMORY: 256 updates; lineage/token costs and itemwise paired labels in JSON.
- Seed 2 REPLAY: 256 updates; lineage/token costs and itemwise paired labels in JSON.
- Seed 2 EXTRA_MEMORY: 256 updates; lineage/token costs and itemwise paired labels in JSON.

Incremental totals: {"calls":480,"fits":6,"updates":1632}

- Three learner pairs, not independent rows, presentations or episodes; no pooled causal claim.
- EXTRA_MEMORY matches steps, not memory exposure, context/target tokens or wall time.
- LOWER/HIGH/LR0 are historical noncontemporaneous references, not new executed controls.
- Constant-record comparison is evaluator-only same-panel oracle, not an executed control.
- Frozen CPU source scorer replay and archived native receipts, not native re-execution or tensor payload verification.
- Exposed exploratory DEV; no fresh confirmation, parenting, H1/H2, clean ancestry or automatic promotion.
