# Conditional root0 public-ID shortcut — independent frozen-corpus recount

2026-09-12. **CONFIRMED on the actual frozen attempt2 candidate.** A lookup
trained only on REVISE training targets using visible square suffix + OBSERVED
+ PRIOR action gets **64/64 train and 32/32 dev complete targets correct**, for
**both AUTH and DERANGED**, without reading the literal EXPECTED outcome.

This verifies the semantic allegation in
`research_notes/analysis/2026-09-12_level1_conditional_corpus_fresh_audit.md`.
It does not adopt that older document's historical runner/launch prescriptions.
The scope here is the frozen root0 `fep/nup` artifact, not a claim about every
root or any model behavior. No live/terminal model outcomes were read.

## Files, binding and reproduction

Only this report and `/tmp/astra_conditional_shortcut_recount_20260912.py` were
created/edited. No prior terminal-analysis file, source, repository state,
other agent's work, GPU, process, run, or launch was modified. No Git/network,
native tokenizer, model import, or model execution occurred.

- Candidate: `/tmp/astra_conditional_native_preps_20260912/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/material/candidate.json`.
- Candidate SHA256: `5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c`.
- Recount script: 274 lines; SHA256
  `d260aa4903311de7c423df4689a549080e56ba9152cb78d674a63715c00301a1`.

```bash
python3 -B /tmp/astra_conditional_shortcut_recount_20260912.py --self-test
python3 -B /tmp/astra_conditional_shortcut_recount_20260912.py
python3 -B /tmp/astra_conditional_shortcut_recount_20260912.py --json
```

**14 CPU tests passed, no skips, 0.094 seconds.** Default output is a compact
table. `--json` writes full projection shapes, component counts, shortcut
training lookup cells, transfer coverage, and square counts to stdout only.
No output artifact is created. Relocating `--candidate` still requires exact
frozen bytes. Tests use the permitted actual corpus, not model outcomes, plus
a small synthetic majority-count check and in-memory feature-invariance checks.

## Exact method and target

Predictor keys are extracted **only from rendered `case.context`**. They never
use `case.id`, metadata `instance_id`, `factors`, hidden corner/view indices,
row order, target text, target length, or `inputs`:

1. Find the visible string matching
   `r[0-9]+-(train|dev)-(prospect|revise)-([0-9]{2})`.
2. `instance` retains the entire visible identifier. `square` is the integer
   last two digits, discarding root/split/operation. `square_bucket` is
   `(square // 2) % 2`.
3. For REVISE read `OBSERVED: <outcome>.` and the action matched by
   `PRIOR: PREDICT <action> ->`. **The EXPECTED token after that arrow is not
   parsed by the key extractor.** A test flips that literal token in all 32
   dev contexts and verifies all extracted shortcut features remain unchanged.
4. Score against independently rule-derived complete target tuples:
   `(COMPARE, POLICY, NEXT)`. Ground-truth derivation uses public-input
   metadata EXPECTED/OBSERVED equality and map orientation; that is label
   construction, not an input to the fitted lookup. Independently rendered
   training strings match the stored AUTH/DERANGED training response strings.

For each panel, construct the exact frequency table `n(z,y)` for projected key
`z` and full target `y`. The unrestricted **per-panel lookup ceiling** is
`sum_z max_y n(z,y) / N`. This uses that panel's labels and is an exact ceiling,
not evidence of train-to-dev transfer.

Separately fit **only the training** majority table, break ties by the
lexicographically smallest target tuple, freeze it, and predict dev with no
dev fitting. Unseen keys abstain and are explicitly counted, never silently
given a best dev label. `correct_over_all_rows` counts correct covered rows
over all 32; this is not an accuracy on abstentions. Covered-only accuracy is
reported separately, or null with no coverage. The perfect REVISE shortcut
has no ties and no unseen dev keys, so neither qualification rescues it.

## REVISE concrete cell counts

Each map has 64 training REVISE rows and 32 dev REVISE rows. Both maps use the
same inputs; these are not independent replicated datasets.

| Visible suffix | Literal EXPECTED in all its rows | Train rows | Dev rows | Distinct (OBSERVED, PRIOR) cells |
|---|---|---:|---:|---:|
| 00, 01, 04, 05 | fep | 8 each | 4 each | 4 each |
| 02, 03, 06, 07 | nup | 8 each | 4 each | 4 each |

Thus `(square, observed, prior)` has **32 cells** on each panel. Each training
cell contains **2 identical targets** from the two training views; each dev
cell contains **1 target**. All 32 dev keys already occur in training. There
are no conflicting labels in either panel, for either map.

Even the compressed `(square_bucket, observed, prior)` has only **8 cells**:
8 rows/cell in train, 4 rows/cell in dev, one distinct target/cell throughout.
Its train-only dev lookup is also **32/32** on both maps.

The following exact counts are identical for AUTH and DERANGED:

| Projection | Train ceiling correct/64; cells | Dev ceiling correct/32; cells | Train-only dev correct / covered; unseen |
|---|---:|---:|---:|
| constant | 16/64; 1 | 8/32; 1 | 8/32; 0 |
| literal instance | 16/64; 8 | 8/32; 8 | 0/0; 32 |
| square | 16/64; 8 | 8/32; 8 | 8/32; 0 |
| observed | 16/64; 2 | 8/32; 2 | 8/32; 0 |
| prior | 32/64; 2 | 16/32; 2 | 16/32; 0 |
| observed + prior | 32/64; 4 | 16/32; 4 | 16/32; 0 |
| instance + observed | 32/64; 16 | 16/32; 16 | 0/0; 32 |
| instance + prior | 32/64; 16 | 16/32; 16 | 0/0; 32 |
| instance + observed + prior | **64/64; 32** | **32/32; 32** | **0/0; 32** |
| square + observed | 32/64; 16 | 16/32; 16 | 16/32; 0 |
| square + prior | 32/64; 16 | 16/32; 16 | 16/32; 0 |
| square + observed + prior | **64/64; 32** | **32/32; 32** | **32/32; 0** |
| square_bucket + observed + prior | **64/64; 8** | **32/32; 8** | **32/32; 0** |

**Important distinction:** literal `r0-train-revise-XX` and
`r0-dev-revise-XX` differ. Literal-instance memorization has a 1.0 per-panel
ceiling with OBSERVED+PRIOR, but **zero train-to-dev coverage**. Extracting the
visible numeric suffix is the concrete transferable shortcut, not merely an
unrestricted dev memorizer.

For `(square, observed)` alone, COMPARE/POLICY component ceilings are already
64/64 train and 32/32 dev; NEXT is only 32/64 and 16/32. Adding PRIOR makes
**all three components and the complete joint target perfect**. It predicts
**16/16 outcome twins and 16/16 prior-action twins**, both endpoints correct,
on each map. Rendering the predicted tuple gives the exact registered syntax.

An equivalent human-readable rule is: recover the expected label from the
square bucket (`0 -> fep`, `1 -> nup`), compare OBSERVED to this recovered label,
and KEEP the visible PRIOR on a match, otherwise SWITCH to the other action.
For DERANGED invert match/keep. The trained lookup need not explicitly recover
or represent expected; it maps its three visible key components directly to
the entire target tuple. It never needs the actual expected token in the
prompt. The numeric bucket expression is a simpler additional witness, not
required to obtain the train-only exact-suffix result.

## Is PROSPECT affected?

**Not by this same omitted-factor public-ID shortcut.** Its belief and goal
are both crossed within each exposed instance. On both maps:

| Projection | Train ceiling correct/64; cells | Dev ceiling correct/32; cells | Train-only dev correct / covered; unseen |
|---|---:|---:|---:|
| instance + goal | 32/64; 8 | 16/32; 16 | 0/0; 32 |
| instance + belief | 32/64; 8 | 16/32; 16 | 0/0; 32 |
| square + goal | 32/64; 8 | 16/32; 16 | 8/16; 16 |
| square + belief | 32/64; 8 | 16/32; 16 | 8/16; 16 |
| belief + goal, no ID | 64/64; 4 | 32/32; 4 | 32/32; 0 |
| dax's public binding + goal, no ID | 64/64; 4 | 32/32; 4 | 32/32; 0 |

For either square+goal or square+belief, the train cells each have 8 rows split
4/4 across two full targets. Dev cells each have 2 rows split 1/1. Thus the
per-panel full-target ceiling is exactly **0.50**, not 1.0. PROSPECT train
suffixes are 00..03; dev uses 00..07, explaining the 16 unseen rows for a
literal square-key train lookup. This must not be conflated with the 0.50
per-panel ceiling.

For square+goal, PREDICT_OUTCOME alone is determined (64/64, 32/32); selected
action and joint target are not. One public binding plus GOAL legitimately
determines this two-action bijective card task. That finite lookup is a valid
registered computation, not proof of broader reasoning. This recount does
not certify PROSPECT against every possible shortcut or supply a learning,
L1/H1, composition or model-origin claim.

## Smallest compatible crossed-factor diagnostic — recommendation only

**Do not alter, kill, retry, extend, or relabel the running bound experiment.**
Preserve its provenance and raw evidence; mark the intended-comparison
interpretation of REVISE **UNQUALIFIED**. Existing generation correctness,
outcome/prior twins, complementary-map redirection, and their likelihood
contrasts cannot disambiguate the intended EXPECTED comparison from this
shortcut. This identifies an assay confound, not evidence that the model
actually used the shortcut, and not an instruction to treat outcomes as zero.

For a prospectively specified separate diagnostic, the smallest complete
factorial block has **8 corners**:

`PRIOR action (2) x EXPECTED outcome (2) x OBSERVED outcome (2)`.

To retain the registered **32-row REVISE dev denominator**, use **four such
blocks**, each with a shared opaque nuisance ID (or no ID). Within each block,
hold template/action order/nuisance cues fixed while crossing all three
factors. Do not give corners unique public IDs or let another visible cue
encode EXPECTED. This preserves 16 outcome pairs and 16 prior-action pairs,
and additionally exposes **16 EXPECTED-flip pairs** with PRIOR and OBSERVED
unchanged. Full joint `(instance, observed, prior)`-restricted ceilings are
then exactly 0.50 by balanced construction; require that audit before use.
Changing EXPECTED alone must flip COMPARE/POLICY/NEXT under each map.

Leave PROSPECT and unrelated controls unchanged in this proposal. Keep the
diagnostic separate from the live run: it measures the saved policy's use of
EXPECTED on new crossed inputs; it does not retroactively repair the training
material. A later training successor would also need EXPECTED crossed within
its public-instance/view blocks and fresh parity/provenance qualification.
Opaque IDs alone are not sufficient if some other nuisance still reveals
EXPECTED. This report implements **neither** the crossed panel nor a source,
scorer, training, launch, or protocol repair; Main owns any prospective scope
and approvals. **No L1 promotion.**

## Test inventory

The 14 passing tests cover exact frozen counts/hash; public versus hidden ID
visibility; exclusion of EXPECTED and hidden metadata from predictor features;
invariance to literal EXPECTED changes; both-map perfect shortcut ceilings;
actual train-only held-dev prediction; nontransfer of literal-instance keys;
the eight-cell compressed shortcut; no-ID 0.50 baseline; both registered twin
families; PROSPECT omitted-factor 0.50 ceilings; valid binding+goal transfer;
PROSPECT unseen square coverage; and a nonuniform majority-ceiling calculation.

**EDITSTOP. Only the two assigned files were written. No analysis outcomes
were accessed and no live-run action was taken.**
