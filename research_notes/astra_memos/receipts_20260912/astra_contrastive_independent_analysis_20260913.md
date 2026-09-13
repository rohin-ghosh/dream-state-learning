# Contrastive perception — independent stored-evidence analysis

2026-09-13 UTC. Bounded read-only analysis begun 07:44 UTC.

## Conclusion

**Real strict-score improvement, mostly interface-confounded versus OFF;
a small identifiable field-correction advantage versus PLAIN, but no robust
source-discrimination or preregistered-screen success.**

OFF/PLAIN/CONTRASTIVE held totals are **2/24, 17/24, 19/24**. All 17
CONTRASTIVE wins over OFF change a syntax-invalid response into a strict pass;
the original scorer cannot establish whether their previously unscorable
content was already correct. Thus these are not 17 demonstrated semantic
improvements, nor proof of 17 purely formatting-only improvements.

Against PLAIN, all **three wins** are schema-valid prediction/relation
corrections on D1; the **one loss** is a schema-valid wrong TRY coordinate on
D2. Net +2 is not a formatting gain: CONTRASTIVE actually has one more invalid
held response than PLAIN. This narrow field result is positive, but it does not
identify selected-outcome use, generalize across wrappers, or pass the frozen
screen. Neither a blanket success nor a blanket no-learning conclusion follows.

## Evidence identity and method

- Scores: `/tmp/astra_contrastive_scores_20260913_attempt1.json`, verified
  SHA256 `7af6484ebb72abc81d2f17d29e7ca15786599afba0b22e88139a80403f3412d0`
  at entry and after analysis.
- Candidate: `/tmp/astra_contrastive_material_native_candidate_20260913.json`,
  SHA256 `7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66`.
- Original material/scorer: `/tmp/astra_contrastive_perception_material_20260913.py`,
  SHA256 `b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d`.
- Material handoff: `/tmp/astra_contrastive_perception_material_handoff_20260913.md`,
  SHA256 `2f22e3e93e036e7e629c4366063dc7286bce5092cc73177159b9bf9414c010ff`.
- Wrapper handoff: `/tmp/astra_contrastive_perception_run_20260913_handoff.md`,
  SHA256 `75e1a1bb51e2f01c5f4ef520ad3244f9e7b8865140054200b110251717559f59`.
- Shortcut advisory: `/tmp/astra_contrastive_material_advisory_20260913.md`,
  SHA256 `6d4e3982521a8cec81f3729461a1947b266cabd8ca7088c2c3a00eb15a5d2944`.
- Plan file SHA256 `f0060eb8d37a61aa1d9b25ba6798f19045a8a66cca715755f5e948d216702ec4`
  matches the score envelope. Its completion identity is
  `9574f5b7dfe6df3bbd9b74a3afb46fd5fc1c5d4ae0b1e11f249f9076bf0c38ff`.

I loaded only the pinned stdlib material/corpus scorer, rebuilt the candidate
in memory through its original validation, and supplied each stored exact
`raw`/`finish_reason` envelope to `score_dataset`. **The entire re-reduced
`material_scores` object equals the collected object exactly**, including raw
hashes, strict decisions, error categories, field indicators, paired keys and
screen flag. No fence removal, duplicate-key repair, permissive parsing, field
salvage from invalid objects, or alternative scoring rule was used.

The pinned source hashes also match: `organism_v6/birth_skill_corpus.py`
`078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`;
`organism_v6/rulegame_parenting_diagnostic.py`
`e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.
`score_row` at material line 219 leaves all fields null on malformed records;
`assess_source` at corpus line 128 derives the selected final event's proofs;
`score_response` at corpus line 338 retains the original grammar/judgment.

This is **not another native collection**. The existing collection log records
`COLLECTED_AUTHORED_LEVEL0_1_ONLY` and the same score hash. I did not execute the
wrapper, connect to any node, or independently replay producer custody.

## Recorded native work and costs

The stored generation-cost entries sum to **144 calls**: three states by four
12-item panels. The two fit manifests record **12 updates each, 24 total**,
12 rows each and four epochs: 48 presentations per arm, 96 total.
All 144 scored completions terminate with `stop`; none has a completion error.
Controller elapsed time is 1323.156319 seconds. These are completed stored
measurements, not inference from the planned budget.

Both arms have 1488 supervised tokens over four epochs. PLAIN/CONTRASTIVE total
training tokens are 19224/19656; padded totals are 19460/19892. Context and
masked-tail tokens per epoch are 4434/4542. Equal source facts, targets, update
counts and seed do **not** establish equal context cost or stochastic paths.
The treatment bundles grouping, explicit relational/attention guidance and
length, not grouping alone. One recorded timing is not a speed comparison.

## Strict totals and interface/source separation

F = syntax/schema/completion-invalid, with source fields unevaluable.
S = interface-valid but strict/source-wrong. P = strict pass.
Here every F is a syntax error; no schema or completion errors occur.

| State | Panel | P | S | F | Denominator |
| --- | --- | ---: | ---: | ---: | ---: |
| OFF | D1 | 0 | 0 | 12 | 12 |
| OFF | D2 | 2 | 0 | 10 | 12 |
| PLAIN | D1 | 9 | 3 | 0 | 12 |
| PLAIN | D2 | 8 | 2 | 2 | 12 |
| CONTRASTIVE | D1 | 12 | 0 | 0 | 12 |
| CONTRASTIVE | D2 | 7 | 2 | 3 | 12 |
| OFF | C-record | 0 | 0 | 12 | 12 |
| PLAIN | C-record | 8 | 3 | 1 | 12 |
| CONTRASTIVE | C-record | 9 | 3 | 0 | 12 |
| OFF | C-general | 11 | 1 | 0 | 12 |
| PLAIN | C-general | 12 | 0 | 0 | 12 |
| CONTRASTIVE | C-general | 12 | 0 | 0 | 12 |

All 22 invalid OFF held responses start with Markdown fences and fail the
original decoder. PLAIN's two and CONTRASTIVE's three invalid held responses
are duplicate-key objects, all on D2. Their potentially readable fragments
receive **no** source-field credit. OFF C-record similarly has 12 syntax failures;
PLAIN C-record has one duplicate-key failure.

| State, held only | Interface-valid | TRY correct | Observed correct | Predicted correct | Relation correct | Unevaluable rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OFF | 2/24 | 2/2 | 2/2 | 2/2 | 2/2 | 22 |
| PLAIN | 22/24 | 21/22 | 22/22 | 17/22 | 17/22 | 2 |
| CONTRASTIVE | 21/24 | 20/21 | 21/21 | 20/21 | 20/21 | 3 |

Conditional denominators differ; these percentages alone are not a paired
causal estimate. OFF's 2/2 is not evidence of universal semantic mastery.

## Exact paired transitions

All counts below retain the original 24 renderings, without treating them as
independent samples.

| Comparison, baseline to treatment | F→P | F→S | F→F | S→P | S→S | S→F | P→P | P→S | Strict wins/losses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| OFF→PLAIN | 15 | 5 | 2 | 0 | 0 | 0 | 2 | 0 | 15 / 0 |
| OFF→CONTRASTIVE | 17 | 2 | 3 | 0 | 0 | 0 | 2 | 0 | 17 / 0 |
| PLAIN→CONTRASTIVE | 0 | 0 | 2 | 3 | 1 | 1 | 16 | 1 | 3 / 1 |

For OFF comparisons, only two held pairs are valid in both states and all four
fields remain correct on both. **Zero wrong-source→correct-source transitions
are measurable among those jointly valid OFF pairs.** The much larger gain
occurs where OFF field correctness is undefined. Causally apportioning that
gain into formatting versus latent content learning is not identified.

For PLAIN→CONTRASTIVE, **21/24 pairs are valid in both**:

- `observed`: 21 correct→correct, no changes.
- `predicted`: 17 correct→correct, three wrong→correct, one wrong→wrong.
- `relation`: identical transition counts; relation is coupled to prediction,
  so this is three corrected records, not six independent gains.
- `try`: 19 correct→correct, one wrong→correct, one correct→wrong.
  The corrected TRY occurs on a record whose prediction/relation remain wrong,
  so it does not add a strict win.

### Exactly which held rows changed strict status

Three D1 wins all correct an invented Boolean prediction to `null`, and the
relation to `unavailable`, when the selected event has **no explicit prediction**.
TRY and observed were already right under PLAIN:

| Full source ID after `D1/perception:` | Case / triple |
| --- | --- |
| `5cc7ba90aa459dbd2cf6ced99e11be58103099e997f8334ff04a39e38332bb49` | unavailable_false; [13, 7, -19] |
| `82af6762ed0a3b32965b46226109796b57bdf7dcc515d467030e1075bbfe3e40` | unavailable_false; [-10, 21, -17] |
| `d7358ea228d9f57060009ade48b9526cb9264bd4db7a6fc24e1d74d76bcdf6c6` | unavailable_true; [-10, 21, -17] |

The single D2 loss is
`D2/perception:73674efcc082eb2b69968680ae94c682d308bd8eb62b61317217c9a53e813198`:
CONTRASTIVE emits TRY `[13, 7, 19]` instead of `[13, 7, -19]` while observed,
prediction and relation remain correct. This is a source-coordinate error,
not malformed JSON. D1's three source-valid wins minus D2's one source-valid
loss explain the entire +2 strict advantage.

One additional D2 source-wrong PLAIN response becomes duplicate-key invalid
under CONTRASTIVE (`d7358...` above); it is not a strict loss because both fail,
but it is a format regression hidden by aggregate strict wins/losses.

## Canaries and the frozen screen

There are **zero OFF-correct canary regressions**. Precisely, OFF has zero
C-record passes and 11 C-general passes; both fitted states retain those 11.
Thus record-canary preservation versus OFF is vacuous, and the observed no-harm
set is only 11 items. The remaining arithmetic item improves in both arms.
No broad retention guarantee follows.

Against PLAIN, CONTRASTIVE C-record has **two wins and one loss** (net +1):
one format-invalid→pass, one source-wrong→pass, one pass→source-wrong.
The loss concerns predicted/relation fields on source
`454aa6fa2a4dd66f24bd1544d9b59fa3cff35676abfc3e46411b763d271b7330`.
C-general PLAIN/CONTRASTIVE are tied 12/12. The registered no-harm comparator
is OFF, not PLAIN; do not silently substitute or suppress this distinction.

**Preregistered exploratory screen: FALSE**, independently reproduced:

- Held minimum 20/24: **fails**, 19/24.
- Each wrapper minimum 9/12: D1 passes at 12; **D2 fails at 7**.
- Advantage at least four over each control: OFF passes (+17);
  **PLAIN fails (+2)**.
- Complete outputs, OFF below ceiling, and OFF-correct canary preservation:
  pass. None compensates for the three failed conditions.

The outer receipt remains `automatic_pass=false`, `scientific_pass=null`.
Do not lower thresholds, select D1, or convert a near miss into promotion.

## Dependence, shortcut and uncertainty

D1/D2 are exactly the same 12 source cases and targets in two wrappers, on
only **two fresh triples**. I checked equality of their keyed source objects.
The six cases per triple reuse an authored factorial and DEV ancestry.
They are not 24 independent trials, nor 12 independently sampled worlds.

- Cases passing **both** wrappers: OFF 0/12, PLAIN 8/12, CONTRASTIVE 7/12.
- Cases passing at least one wrapper: OFF 2/12, PLAIN 9/12, CONTRASTIVE 12/12.
- By triple, PLAIN→CONTRASTIVE changes 8→10 of 12 renderings for
  [-10,21,-17], and 9→9 for [13,7,-19]. These are descriptive paired cuts,
  not replacement endpoints or independent replications.

Consequently +2 overall does not show consistent wrapper-robust superiority:
D1 improves +3 while D2 worsens -1, and both-wrapper success declines by one
case. One learner seed, two triples, shared prompts/targets and a bundled
instruction/length intervention do not support an independent-n=24 binomial
interval, sign-test claim, reliable population effect, or mechanism attribution.
No formal significance or population uncertainty interval is asserted.

The advisory's counterexample is specifically relevant to this same frozen
candidate: the earlier outcome always opposes the selected final outcome.
Reading the final action/prediction but **negating the earlier outcome** can
score perfectly without reading the selected outcome. This does not prove
the model uses that shortcut or imply a hidden-answer leak; it shows that
selected-outcome provenance is not identified by this instrument. The observed
prediction-null fixes are genuine source-scored output corrections, not proof
of the advertised source-binding mechanism. Observed is already correct on
every jointly valid PLAIN/CONTRASTIVE held pair.

## Useful next decision

Keep this as a **completed, failed-screen diagnostic** with two useful signals:
authored fitting greatly improves strict interface compliance over OFF, and
contrastive grouping-plus-guidance improves missing-prediction handling on D1.
Do not promote CONTRASTIVE as a robust source-discrimination winner over PLAIN,
but do not discard its real three field corrections as mere formatting.

For Main's next prospectively authorized diagnostic, prioritize whether those
absence-of-prediction corrections survive wrapper changes while eliminating
duplicate-key and signed-coordinate regressions. Any experiment intended to
establish selected-outcome discrimination also needs the earlier/final-outcome
relationship counterbalanced so the demonstrated negation shortcut cannot solve
every case. Preserve an equal-source/equal-target PLAIN control, joint-valid
field transitions, fixed screen and canary reporting, with independent seeds
and fresh cases for uncertainty. These are recommendations only: no dataset,
threshold, learner, launcher or live run is changed here.

No child SLEEP, clean ancestry, mechanism freeze, general G1, L2/P1/H1/H2,
mission completion, or scientific promotion follows. No native recollection,
GPU operation, network, live Level1 inspection, repository/Git edit, test-suite
run, or archive transfer occurred. Only this requested analysis file is written;
Main retains archival and operational ownership.
