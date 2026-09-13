# Actual-record memory: local paired analysis

Local reduction of pinned native scored evidence, not raw native replay, recollection or tensor verification. Exact-cue acquisition/persistence and paraphrase transfer remain separate. Same-learner WRITE/LR0 pairs have 14/8/8 different admitted records; no pooled causal claim. Authored held/canary retention is not H1/H2 or recursive learning. Tensor checks validate finite recorded inventories/norms only.

## Seed 0 — 14 admitted / 16 possible

| Panel | Metric | WRITE | LR0 | WRITE-only | LR0-only |
|---|---|---:|---:|---:|---:|
| exact | production_eligible | 8/14 | 0/14 | 8 | 0 |
| exact | content_correct | 8/14 | 0/14 | 8 | 0 |
| exact | strict_canonical | 3/14 | 0/14 | 3 | 0 |
| exact | exact_target_bytes | 7/14 | 0/14 | 7 | 0 |
| paraphrase | production_eligible | 6/14 | 0/14 | 6 | 0 |
| paraphrase | content_correct | 6/14 | 0/14 | 6 | 0 |
| paraphrase | strict_canonical | 0/14 | 0/14 | 0 | 0 |
| paraphrase | exact_target_bytes | 4/14 | 0/14 | 4 | 0 |
| held | content_correct | 44/48 | 47/48 | 0 | 3 |
| held | strict | 44/48 | 47/48 | 0 | 3 |
| canary | content_correct | 12/12 | 12/12 | 0 | 0 |
| canary | strict | 12/12 | 12/12 | 0 | 0 |

Retention changes versus the same original learner's post-fit receipt:

| Arm/panel | Raw changed | Content changed / regressed | Strict changed / regressed |
|---|---:|---:|---:|
| WRITE/held | 4 | 3 / 3 | 3 / 3 |
| WRITE/canary | 0 | 0 / 0 | 0 / 0 |
| LR0/held | 0 | 0 / 0 | 0 / 0 |
| LR0/canary | 0 | 0 / 0 | 0 / 0 |

Work: 176 generation calls; 224 optimizer updates across both arms (LR0 updates do not imply parameter change).
- WRITE: 112 updates; train 28.600s / wall 35.000s; supervised/context/padded tokens 3248/16240/19488; changed elements 20185084, delta L2 3.9206653; generation prompt/output tokens 19733/1952, 86.782s.
- LR0: 112 updates; train 29.600s / wall 42.900s; supervised/context/padded tokens 3248/16240/19488; changed elements 0, delta L2 0; generation prompt/output tokens 19733/2838, 117.288s.

Per-metric paired row IDs and input hashes are preserved in analysis.json. Reported native summaries reproduced exactly.

- WRITE format/content: exact-cue content failures 6, content-correct but non-strict 5; held content failures 4, content-correct but non-strict 0, length terminations 0.
- LR0 format/content: exact-cue content failures 14, content-correct but non-strict 0; held content failures 1, content-correct but non-strict 0, length terminations 0.

## Seed 1 — 8 admitted / 16 possible

| Panel | Metric | WRITE | LR0 | WRITE-only | LR0-only |
|---|---|---:|---:|---:|---:|
| exact | production_eligible | 7/8 | 0/8 | 7 | 0 |
| exact | content_correct | 7/8 | 0/8 | 7 | 0 |
| exact | strict_canonical | 0/8 | 0/8 | 0 | 0 |
| exact | exact_target_bytes | 7/8 | 0/8 | 7 | 0 |
| paraphrase | production_eligible | 5/8 | 0/8 | 5 | 0 |
| paraphrase | content_correct | 5/8 | 0/8 | 5 | 0 |
| paraphrase | strict_canonical | 0/8 | 0/8 | 0 | 0 |
| paraphrase | exact_target_bytes | 5/8 | 0/8 | 5 | 0 |
| held | content_correct | 37/48 | 48/48 | 0 | 11 |
| held | strict | 37/48 | 48/48 | 0 | 11 |
| canary | content_correct | 12/12 | 12/12 | 0 | 0 |
| canary | strict | 12/12 | 12/12 | 0 | 0 |

Retention changes versus the same original learner's post-fit receipt:

| Arm/panel | Raw changed | Content changed / regressed | Strict changed / regressed |
|---|---:|---:|---:|
| WRITE/held | 11 | 11 / 11 | 11 / 11 |
| WRITE/canary | 0 | 0 / 0 | 0 / 0 |
| LR0/held | 0 | 0 / 0 | 0 / 0 |
| LR0/canary | 0 | 0 / 0 | 0 / 0 |

Work: 152 generation calls; 128 optimizer updates across both arms (LR0 updates do not imply parameter change).
- WRITE: 64 updates; train 16.700s / wall 24.600s; supervised/context/padded tokens 1592/9296/10888; changed elements 20185085, delta L2 3.589591; generation prompt/output tokens 18033/1519, 65.109s.
- LR0: 64 updates; train 26.400s / wall 46.100s; supervised/context/padded tokens 1592/9296/10888; changed elements 0, delta L2 0; generation prompt/output tokens 18033/1492, 60.810s.

Per-metric paired row IDs and input hashes are preserved in analysis.json. Reported native summaries reproduced exactly.

- WRITE format/content: exact-cue content failures 1, content-correct but non-strict 7; held content failures 11, content-correct but non-strict 0, length terminations 0.
- LR0 format/content: exact-cue content failures 8, content-correct but non-strict 0; held content failures 0, content-correct but non-strict 0, length terminations 0.

## Seed 2 — 8 admitted / 16 possible

| Panel | Metric | WRITE | LR0 | WRITE-only | LR0-only |
|---|---|---:|---:|---:|---:|
| exact | production_eligible | 5/8 | 0/8 | 5 | 0 |
| exact | content_correct | 5/8 | 0/8 | 5 | 0 |
| exact | strict_canonical | 0/8 | 0/8 | 0 | 0 |
| exact | exact_target_bytes | 5/8 | 0/8 | 5 | 0 |
| paraphrase | production_eligible | 5/8 | 0/8 | 5 | 0 |
| paraphrase | content_correct | 5/8 | 0/8 | 5 | 0 |
| paraphrase | strict_canonical | 0/8 | 0/8 | 0 | 0 |
| paraphrase | exact_target_bytes | 5/8 | 0/8 | 5 | 0 |
| held | content_correct | 17/48 | 48/48 | 0 | 31 |
| held | strict | 17/48 | 48/48 | 0 | 31 |
| canary | content_correct | 12/12 | 12/12 | 0 | 0 |
| canary | strict | 12/12 | 12/12 | 0 | 0 |

Retention changes versus the same original learner's post-fit receipt:

| Arm/panel | Raw changed | Content changed / regressed | Strict changed / regressed |
|---|---:|---:|---:|
| WRITE/held | 31 | 31 / 31 | 31 / 31 |
| WRITE/canary | 0 | 0 / 0 | 0 / 0 |
| LR0/held | 0 | 0 / 0 | 0 / 0 |
| LR0/canary | 0 | 0 / 0 | 0 / 0 |

Work: 152 generation calls; 128 optimizer updates across both arms (LR0 updates do not imply parameter change).
- WRITE: 64 updates; train 17.200s / wall 24.600s; supervised/context/padded tokens 1936/9296/11232; changed elements 20185085, delta L2 3.1796801; generation prompt/output tokens 18033/1955, 81.322s.
- LR0: 64 updates; train 22.400s / wall 32.100s; supervised/context/padded tokens 1936/9296/11232; changed elements 0, delta L2 0; generation prompt/output tokens 18033/1661, 68.519s.

Per-metric paired row IDs and input hashes are preserved in analysis.json. Reported native summaries reproduced exactly.

- WRITE format/content: exact-cue content failures 3, content-correct but non-strict 5; held content failures 31, content-correct but non-strict 0, length terminations 0.
- LR0 format/content: exact-cue content failures 8, content-correct but non-strict 0; held content failures 0, content-correct but non-strict 0, length terminations 0.

No automatic pass; no pooled success rate or causal promotion.
