# Result-blind claim audit: contrastive-perception Level-1 screen

**Date:** 2026-09-13  
**Role:** independent prospective scientific auditor  
**Result visibility:** blind. I inspected the frozen protocol, generator, native
preparation receipt, plan, runner, tests, and public source definitions. I did
not open a response, adapter, fit loss, controller result, collection, score, or
other efficacy artifact, and I did not change code, a process, or GPU state.

## Verdict before outcomes

The live run is a valid, cheap **authored procedural-perception screen**. It can
test whether an equal-source/equal-target LoRA fit benefits from an input that
groups two records by field and explicitly calls attention to their differences,
relative to source-first enumeration. It is worth completing and reading.

It is **not a valid test of conditional/keyed memory discrimination in the Q0
sense**. Every evaluation answer remains visible in the prompt; no learned key
must retrieve a withheld value. More importantly, the contrastive training
fixture explicitly highlights opposite observations, while every held fixture
also makes its earlier distractor observation the exact Boolean opposite of the
selected observation. A model can therefore obtain a perfect held score without
reading the selected outcome. This is fatal to a selected-outcome-binding or
general keyed-discrimination interpretation, but not to the protocol's already
narrow descriptive screen. Do not alter the live run; bound the readout.

## Frozen identity

- Protocol SHA-256: `cc7e92d8aa3999c2ee619893cf830f2687347a39175149708886c1bf0d820ef5`.
- Material generator SHA-256:
  `b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d`.
- Canonical material SHA-256, independently rebuilt CPU-only:
  `7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66`.
- Native runner SHA-256:
  `aea1b5d84d6d79efa7dbdd43ab8e93bf0483fd4383531eae363cdbb4b7583d55`.
- Prepared plan SHA-256:
  `f0060eb8d37a61aa1d9b25ba6798f19045a8a66cca715755f5e948d216702ec4`.
- Official frozen `Qwen/Qwen2.5-7B-Instruct` base revision
  `a09a35458c702b33eeacc393d103063234e8bc28`; one learner seed (`0`).

The native preflight established identical target-plus-EOS token IDs and epoch
order across fits, no truncation, and the unequal input costs reported below.
These are preparation facts, not model outcomes.

## Exact arms and dose

There are three inference states:

1. **OFF:** frozen base, LoRA-enabled engine, no `LoRARequest`.
2. **PLAIN:** fresh rank-8 LoRA trained on source-first records.
3. **CONTRASTIVE:** separate fresh rank-8 LoRA trained on the same records and
   targets, with facts grouped by field plus an explicit difference-attention
   instruction.

Each fit has 12 assistant targets: two training triples crossed with the same
six cases (`matched_true`, `matched_false`, `mismatched_true`,
`mismatched_false`, `unavailable_true`, `unavailable_false`). Each context has
one selected and one companion transcript. They share the same triple and prior
prediction and have opposite observations. Pairing is reciprocal: the 12 unique
sources each occur once as selected and once as companion. Each prompt also
spells out all eight selected/companion field values.

Both fits use all-layer attention+MLP LoRA, rank 8, alpha 16, dropout 0.05,
learning rate `1e-4`, batch 4, four epochs, no packing, and 12 optimizer updates.
That is 48 presentations per row set and 1,488 supervised target-plus-EOS tokens
per fit. All prompt tokens are loss-masked.

The native exposure is not compute matched:

| fit | tokens/epoch | masked context+tail/epoch | padded tokens/4 epochs |
|---|---:|---:|---:|
| PLAIN | 4,806 | 4,434 | 19,460 |
| CONTRASTIVE | 4,914 | 4,542 | 19,892 |

CONTRASTIVE has nine additional input tokens per row, or 432 additional padded
tokens across the fit (about 2.2%). Its UTF-8 context is 16,692 versus 15,900
bytes (+4.98%). The treatment is therefore grouping + explicit guidance +
wording/length, not grouping alone and not an equal-compute comparison.

## Evaluation denominators

Each state receives four panels of 12 greedy calls:

- `D1`: 12 held records under an archive/distractor wrapper.
- `D2`: the exact same 12 sources and targets under a chronological wrapper.
- `C-record`: 12 previously exposed DEV records; preservation canary only.
- `C-general`: six exact additions and six exact copies.

Thus there are 48 calls/state and 144 calls total. The nominal held denominator
is 24 strict renderings/state, but it contains only **12 distinct records, two
fresh numeric triples, and two wrappers over the same records**. It is not
independent `n=24`. The canary denominator is 24/state (12 record + 12 general),
while the no-harm denominator is conditional: every canary item OFF gets right,
not necessarily all 24.

The registered exploratory screen requires all captures complete,
CONTRASTIVE >=20/24 held, >=9/12 in each wrapper, >=4 more held strict passes
than both PLAIN and OFF, OFF <21/24, and no CONTRASTIVE regression on any
OFF-correct canary. The collected report deliberately retains
`automatic_pass=false` and `scientific_pass=null`; the screen cannot promote a
scientific claim automatically.

## What PLAIN versus CONTRASTIVE identifies

If runtime custody closes, the comparison identifies the descriptive effect of
the **exact authored contrastive bundle** at this one dose and learner seed:

- same selected and companion source bytes;
- same eight explicit field facts and multiplicities;
- same 12 assistant targets, target token IDs, native EOS, group order, and
  initial seeded recipe;
- different fact ordering, instruction semantics, input wording, length,
  padding, and consequently stochastic optimization trajectory.

A clean content-level advantage would support: “making differences explicit in
authored masked context improved immediate exact-record execution on this fixed
fixture family.” It cannot isolate field grouping from the instruction or extra
tokens, and it cannot establish a general learned attention mechanism.

## Shortcut and attribution audit

### 1. Fixture-polarity shortcut (strongest)

During training, selected and companion observations are always opposites, and
CONTRASTIVE explicitly says to notice that opposition. During held evaluation,
the earlier distractor observation is always the opposite of the selected final
observation. A solver can copy the final action and prediction, **negate the
earlier observation**, compute relation from those values, and ignore the final
outcome entirely. That procedure scores 24/24 under the frozen scorer.

This is especially consequential because the shortcut is aligned with the
treatment: it is not merely a cue both arms happen to see; CONTRASTIVE directly
rehearses the relevant “opposite” relation. A positive contrastive effect can be
fixture-specific polarity transfer.

### 2. Formatting can satisfy the strict screen

Strict credit requires an exact four-field JSON object. A semantically correct
record inside a Markdown fence gets zero; the same bytes without the fence pass.
Therefore CONTRASTIVE can beat PLAIN and OFF by the registered >=4 margin with
no improvement in source values. When parsing/schema fails, all field indicators
are `null`, so content comparisons need an explicitly reported eligible
denominator; outputs must never be silently repaired.

### 3. Grouping is bundled and target facts are already annotated

PLAIN lists Selected's four fields then Companion's four fields. CONTRASTIVE
places Selected and Companion values adjacent field-by-field and tells the model
what is shared and what differs. Both contexts already contain the correct
selected answer as four explicit labeled note lines in addition to the raw
transcript. The experiment therefore tests how authored scaffolding conditions
an output, not whether a child discovers or compiles the record from experience.

### 4. Fixed roles and tiny support

Training always targets the explicitly labeled Selected/first box. Evaluation
always targets the last event. The six prediction/observation/relation cases are
the same authored factorial in train and held; only two numeric triples and the
wrapper change. Numeric triples do not determine outcomes. Consequently no
conditional key-value map is learned or queried, and wrapper-specific or
position-specific behavior can dominate.

### 5. Repeated rather than independent evidence

`D1` and `D2` duplicate semantic cases. One fit per arm means the fit—not each
row—is the learner-level experimental unit. C-record is exposed DEV and
C-general is only arithmetic/copy locality. Neither can certify broad no-harm.

## Prospective interpretation table

| Observed outcome | Permitted reading | Forbidden reading / next implication |
|---|---|---|
| Any missing, truncated, wrongly routed, mutated, nonfinite, or incomplete stage | Operationally nonreportable; preserve artifacts. | Do not score missing as zero or compare efficacy. |
| OFF >=21/24 held | Panel is ceiling-limited. | No contrastive success claim even if absolute CONTRASTIVE is high. |
| CONTRASTIVE clears the strict screen, but gains are only malformed->valid JSON | Interface/format practice improved. | No discrimination, perception, or keyed-memory claim. |
| CONTRASTIVE has source-field gains on items schema-valid in both states, in both wrappers, with no canary loss | The bundled authored contrastive presentation improved immediate fixed-fixture record execution; worth fresh seeds, source families, and varied event relations. | Not selected-outcome binding, conditional/keyed memory, child learning, or a general attention mechanism. |
| CONTRASTIVE reaches 24/24 | It mastered the registered fixed fixtures descriptively. | Perfect score still does not show it read the final outcome because negate-earlier is perfect. |
| PLAIN and CONTRASTIVE both beat OFF similarly | Authored record-target practice helped; no resolved incremental contrastive value. | Do not credit explicit difference-attention. |
| PLAIN beats CONTRASTIVE | This bundled contrastive rendering is worse at this dose. | Does not falsify contrastive perception generally; length/order/guidance remain bundled. |
| All three are similar below ceiling | No detectable immediate effect of either 12-row recipe on this panel. | Does not show LoRA storage, sleep, or parenting cannot work. |
| D1 gain without D2, or vice versa | Wrapper-specific transfer/elicitation. | No wrapper-general discrimination claim. |
| Relation improves only after copied fields are correct | Better execution of the explicitly supplied Boolean comparison rule. | Not hidden-rule induction, reflection, or connected reasoning. |
| Field copying improves but relation does not | Better extraction/selection of visible public fields. | Not relational comparison. |
| C-record improves but held does not | Rehearsal of an exposed schema/fixture family. | No held generalization. |
| Any OFF-correct canary regresses | Adverse/interference signal under the registered screen. | Do not promote the treatment despite held gains. |

In every outcome, report raw strict scores, syntax/schema/source/completion
failures, per-field correctness, paired wins **and losses**, and the eligible
denominator for content-only comparisons. Do not compute learner-level
significance from repeated rows.

## Direct answer to Rohin's hypothesis

This screen is adjacent to Rohin's idea but does not decisively test it. It asks
whether explicit difference salience in authored training context changes a
LoRA's immediate handling of fully visible, fixed public records. That is a
reasonable Level-1 curriculum screen.

It does not ask whether explicit difference-attention lets a learner store and
later retrieve distinct values under similar keys: the held answer is visible,
the numeric key does not govern it, the training notes explicitly state every
field, and the polarity shortcut can solve the panel. At best, a content-clean
win is motivation for the real test: varied, non-deterministic event relations
and withheld key-conditioned values across fresh learner seeds, followed later
by child-authored records. At worst, it is authored-sentence/interface fit. The
present run can distinguish those two only partially through error decomposition;
it cannot resolve the underlying keyed-memory hypothesis by itself.

## Disposition

**Continue and read as bounded exploratory triage; no redesign of the live
run.** There is no fatal defect for its declared authored-screen scope. There is
a fatal identification defect for any stronger claim that it proves selected
outcome use or conditional/keyed discrimination. The frozen protocol already
warns about this; the terminal report must make the limitation operational by
separating formatting from mutually schema-valid source-field transitions.
