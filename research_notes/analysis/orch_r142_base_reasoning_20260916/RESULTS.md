# R142 attempt3 — complete, author-side recomputation

Observed **2026-09-16 05:25:05 UTC**. Native start **05:17:03.594 UTC**;
supervisor completed **05:22:58.505 UTC**, exit 0, before the unchanged
**05:40 UTC ceiling / 06:00 UTC FINAL reservation**. Exactly this run:
`/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt3/run1`.

## Result and claim boundary

Directly requesting visible work produced prefinal text in all 12 assessable
DIRECTED_REASONING drafts; four further drafts were multiline but had invalid
final JSON. PERMISSION_ONLY had no prefinal text in its 15 assessable drafts;
one invalid-format draft was unassessable. This is observable output, not
evidence about internal reasoning, faithfulness, or a mechanism of improvement.

Strict draft / actual-feedback / neutral passes were **6 / 10 / 8** for
DIRECTED_REASONING and **8 / 9 / 8** for PERMISSION_ONLY, each out of 16.
Feedback-minus-neutral was +2 and +1 tasks respectively. Both arms showed
feedback corrections; direct elicitation did not establish a general advantage.
On the eight tasks where both drafts failed, each arm recovered two with real
feedback and zero with neutral review; one recovery task was shared and one
was unique to each arm. All failed-to-passed continuations lacked prefinal text.
Do not attribute correction to the presence of visible work.

This is a bounded PUBLIC TRAIN prompt-control experiment, not learning,
retention, a canonical/historical score comparison, or a four-way benchmark.
**No rows admitted, fitting, parents, or promotion.** No new calls during audit.

## Verified scope and denominators

- 16 fresh tasks, two task-paired prompt arms, each with its own draft shared
  exactly into real-public-feedback and neutral forks: **96/96 complete calls**.
- 96 each INTENT/CALL/PUBLIC/VERIFY/MEASURE receipts, 32 COMPLETE triplets,
  **523 hashed run artifacts**; terminal summaries recomputed and matched.
- Both arms are **BASE_NO_LORA throughout**; fixed FULL18404 loaded identity
  carrier is not an experimental FULL arm. Exact prompts, steering labels,
  public feedback, shared-draft hashes and balanced order checked.
- 2048 output-token cap per call, 32768 context; **0/96 cap hits, 0/96 incomplete**.
  Total output 8622 tokens against maximum 196608. Largest response 482 tokens.
- All 16 task pairs / 32 arm triplets are complete. No partial-result inference.
- Main's exclusion union: 134 specification / 160 ID / 5 used-seed hashes,
  including rejected attempts1/2 planned cohorts. Those attempts are not pooled.
  Main reports their admission failures were pre-dispatch, with zero GPU calls;
  timing/SSH sensitivity remains an unproven explanation, not a waived gate.

## Format, safe expression, strict pass, visible text

Every row has 16 planned, recorded and complete responses. Format means the
unchanged parser accepts the final JSON-string contract; safe expression means
the expression passes the unchanged AST validator; strict pass uses the frozen
task scorer. These are distinct outcomes. Prefinal presence is non-whitespace
text before the accepted final JSON line; invalid format is **unassessable**, not
absent. Multiline alone does not establish accepted prefinal text.

| Arm | Stage | Format /16 | Safe /16 | Strict /16 | Prefinal present / assessable | Unassessable | Output tokens |
|---|---|---:|---:|---:|---:|---:|---:|
| PERMISSION_ONLY | Draft | 15 | 10 | 8 | 0/15 | 1 | 517 |
| PERMISSION_ONLY | Real feedback | 16 | 11 | 9 | 0/16 | 0 | 531 |
| PERMISSION_ONLY | Neutral | 16 | 12 | 8 | 0/16 | 0 | 481 |
| DIRECTED_REASONING | Draft | 12 | 10 | 6 | 12/12 | 4 | 4979 |
| DIRECTED_REASONING | Real feedback | 16 | 14 | 10 | 4/16 | 0 | 1674 |
| DIRECTED_REASONING | Neutral | 16 | 14 | 8 | 0/16 | 0 | 440 |

## Before-to-after changes

All forks have 16 complete before/after pairs. Recovery denominators are failed
drafts, format-recovery denominators are invalid-format drafts, semantic-correction
denominators are safe-but-wrong drafts. Semantic correction additionally requires
a safe after-expression. Sandbox-to-pass and format-to-pass are not counted as
semantic correction. Format recovery alone need not produce a correct answer.

| Arm | Fork | Failed→pass | Format recovered | Semantic corrected | Pass→fail / passed drafts | Raw changed /16 | AST changed / comparable |
|---|---|---:|---:|---:|---:|---:|---:|
| PERMISSION_ONLY | Real feedback | 2/8 | 1/1 | 1/2 | 1/8 | 8 | 1/8 |
| PERMISSION_ONLY | Neutral | 0/8 | 1/1 | 0/2 | 0/8 | 6 | 0/10 |
| DIRECTED_REASONING | Real feedback | 4/10 | 4/4 | 2/4 | 0/6 | 16 | 3/10 |
| DIRECTED_REASONING | Neutral | 2/10 | 4/4 | 0/4 | 0/6 | 16 | 0/10 |

Expression-text changes numbered 7/5 for permission feedback/neutral and 4/1
for directed feedback/neutral (only format-comparable pairs can register these).
Visible prefixes changed in 12/12 comparable directed pairs for each fork,
versus 0/15 for permission; output changes alone are not functional corrections.

## Paired outcomes

Within each arm, compare real feedback versus neutral from the **same draft**:

| Arm | Both pass | Feedback only | Neutral only | Both fail | Pairs |
|---|---:|---:|---:|---:|---:|
| PERMISSION_ONLY | 7 | 2 | 1 | 6 | 16 |
| DIRECTED_REASONING | 8 | 2 | 0 | 6 | 16 |

Task-paired DIRECTED_REASONING versus PERMISSION_ONLY, not independent samples:

| Stage | Both pass | Directed only | Permission only | Both fail | Pairs |
|---|---:|---:|---:|---:|---:|
| Draft | 6 | 0 | 2 | 8 | 16 |
| Real feedback | 8 | 2 | 1 | 5 | 16 |
| Neutral | 8 | 0 | 0 | 8 | 16 |

The arms have different failed-draft denominators (10 versus 8); do not interpret
4/10 versus 2/8 as a matched recovery advantage. The jointly-failed subset has
eight tasks: feedback recovery both/ directed-only/ permission-only/ neither =
1/1/1/5; neutral = 0/0/0/8. Counts are descriptive, with no significance claim.

## Provenance and audit limits

Independent **metric recomputation by the implementation author**, not a fresh
independent reviewer. Frozen safe parser/scorer/public executor reused; prompts,
measurements and paired summaries reconstructed without using producer measurement
or correction functions as the oracle. Source closure (2653 Python files) checked
before and after. Raw responses remained on ovx3; only compact counts/hashes left.
No launches, signals, retries, source changes, held reads, or ledger edits.

| Object | SHA256 |
|---|---|
| PLAN | `bfc75853d179cc086a703f7d3b79645da765c70201b7d471dfef662a72202c4e` |
| GUARD | `1e4b1d501345e8b8421d48a9b1eb2a8cba58c4d806f097abcb6109eaa9f3abd2` |
| Clear root admission | `1428a66aa39f2841316a92621423849098646b162ef0f31536e359d5fec2d025` |
| Source set | `af88a2a03b7680d8036a7d0875981fdc2d9ac5e30932ebad74b6ed8f7faf11db` |
| Recorded launch argv hash | `1346f3970542eeeb261730ee60805da8542d1e5750e38ddbb49316c07b555cbc` |

The argv hash is preserved from LAUNCH, not independently reconstructed by this
reducer. Native unchanged-weight terminal and bound loaded identity verified;
the audit did not rehash model weights. Full input/terminal/evidence hashes and
machine-readable metric tables are in `RESULT_VERIFICATION.json`.

### Durable node-local audit source

All three unchanged scripts reside at
`/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt3/audit_source_author_20260916/`,
outside unchanged production `attempt1/source_r142_v1`:

| File | SHA256 |
|---|---|
| `reducer.py` | `ff79de217e38e0d4002f1ad7b6289852eb59442f09460c128e4f9c31fb0f9e61` |
| `test_reducer.py` | `fff0d207406f17f8202412b8bb4a74871a2343035d85e2094bfac346ebb907fd` |
| `r141_reducer_dependency.py` | `1309e9b31a32d0f9750ba953a314b48631693ccdb2c2d423a298ffaf40d5d52e` |

CPU tests: **15 local PASS (19.409s), 15 staged PASS (7.713s)**. Tests cover
96-cell recomputation, shared forks and prompts, arm/model/steering tampering,
stored metrics, retry artifacts, truncation/caps, visibility anchoring,
terminal barriers and snapshot drift. Exact local invocation:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= PYTHONPATH=/data/home/rohing/dream-state-orch python3 -B /tmp/orch_r142_attempt3_audit_20260916/test_reducer.py -q
```

Durable node-local test and reduction commands (CPU-only, no dispatch):

```bash
AUDIT=/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt3/audit_source_author_20260916
SOURCE=/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt1/source_r142_v1
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SOURCE" python3 -B "$AUDIT/test_reducer.py" -q
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SOURCE" python3 -B "$AUDIT/reducer.py"
```
