# Contrastive keyed-discrimination follow-up — prospective protocol

**Date:** 2026-09-13  
**Status:** design only; no source, material, tokenizer, model, training, or GPU
execution is authorized or claimed here.  
**Scientific class:** externally authored, loss-masked SFT diagnostic. This is
not child-authored SLEEP, parenting, self-learning, or an organism result.

## Decision in one paragraph

Run one small paired experiment asking whether an explicit instruction to
compare similar records helps a rank-8 LoRA learn a **four-valued joint-key
map**. PLAIN and CONTRASTIVE see the same literal observations in the same
order, have byte-identical assistant targets, and use the same optimizer
schedule and random streams. They differ only in a loss-masked instruction:
ordinary record reading versus explicit comparison across modes. At test time
no outcome is shown. The primary score chooses among four short continuations
by conditional likelihood, so JSON or prose formatting cannot create a content
win; native generation is separately scored permissively for semantic content
and strictly for format. Three paired learner seeds require six fits total.

This directly repairs the live screen's two fatal attribution defects:

1. there is no answer in any evaluation prompt; and
2. there is no Boolean/opposite event to negate. Outcomes are four opaque,
   non-ordered values and the held relations vary across families.

## Evidence that fixes the design

- The result-blind audit at commit `d6de454a` found that the live screen can be
  solved by negating an earlier Boolean and can win through exact-JSON practice.
- Q0-FULLDOSE-v2 lowered loss but learned nearly identical global action motion
  for opposite maps (final adapter-delta cosine `.9961/.9973`); keyed XOR
  separation remained tiny. A new test therefore needs balanced multi-valued
  conditional structure, not more dose on a binary action surface.
- SEQ-113/116 established a locally working authored-memory recipe: rank 8,
  LR `3e-4`, distinct-source interleaving, 320 updates, and 40 presentations per
  semantic source. FOUR_VIEW was robust in `3/3` optimizer seeds, while a
  grouped schedule failed. This protocol preserves the supported source dose
  and interleaving rather than inventing another writer recipe.

## K4 world: exact semantic object

Freeze one world before any model call:

- eight opaque family identifiers, `F[0..7]`;
- four opaque mode identifiers, `M[0..3]`;
- four opaque outcome identifiers, `V[0..3]`;
- one mapping `Y(F,M) -> V`.

For every family, its four mode outcomes are a permutation of the four values.
The eight family permutations must be distinct. Across the full `8 x 4` table,
each `(mode,outcome)` cell occurs exactly twice.

Hold out exactly one joint key per family. The eight held positions must satisfy:

- each mode is held twice;
- each outcome is held twice;
- the two held outcomes under the same mode differ.

Thus there are exactly **24 observed facts and 8 held joint keys**. Observed
targets contain each outcome six times. A fixed outcome obtains `1/4`; on the
observed panel a family-only or mode-only constant obtains at most `1/3`; on
the held panel a mode-only constant obtains at most `1/2`. Slice gates below
force performance beyond these nuisance rules.

The public structural rule is: “Within one family, the four modes produce each
of the four outcomes exactly once.” It is shown equally to both training arms
and repeated in held-key queries. It reveals no particular answer. The held
answer is identifiable from the family's three grounded observations plus this
rule; it is never an assistant target or a stated source fact.

Opaque identifiers are deterministically generated from a frozen seed and a
bounded candidate pool. Native preparation may reject candidates solely to
make each identifier class equal in tokenizer length. It may not query model
probabilities or change the world. Record the accepted strings, attempts,
token IDs, mapping, held mask, and all hashes before OFF inference.

## Training material

Each of the 24 observed `(family,mode,outcome)` facts is one semantic source.
For a selected source, its prompt contains:

1. the public one-of-each rule;
2. the same family's three observed records in canonical mode order;
3. the held mode marked only as `outcome unobserved`;
4. a request for the selected observed mode; and
5. one arm-specific, loss-masked instruction.

The literal fact block, public rule, selected key, order, and target are
identical between arms. The target is exactly:

```text
ANSWER: <opaque-outcome>
```

including the same native EOS treatment. Four pre-frozen lexical skins render
each semantic source, giving 96 memory rows. The skins change wrappers, never
IDs, values, fact order, or semantic content.

The instructions are:

- **PLAIN:** read the supplied records and return the requested record.
- **CONTRASTIVE:** explicitly compare the four modes, attend to which mode
  changes the outcome, and distinguish the selected joint key before returning
  it.

PLAIN is not told to avoid comparison. CONTRASTIVE is a positive additional
cognitive cue, not PLAIN sabotage. Neither instruction contains an outcome,
derived held answer, mnemonic, or mapping rule beyond the shared public rule.

Native preparation appends a frozen semantically inert padding suffix to the
shorter member of each paired row until the two rendered contexts have equal
token length. Reject the run if a bounded, predeclared padding grammar cannot
equalize every pair without truncation. Report both unpadded and padded token
counts. Targets must be token-for-token identical within every PLAIN/CONTRASTIVE
pair.

### Preservation/replay sources

Add 24 arm-identical sources: eight integer additions, eight exact-copy tasks,
and eight unsupported-key tasks whose target is `ANSWER: UNKNOWN`. Give each
four skins, producing 96 replay rows. Training therefore has exactly:

- 96 memory rows;
- 96 preservation rows;
- 192 rows/epoch; and
- byte-identical targets, semantic sources, group order, and row multiplicity
  across PLAIN and CONTRASTIVE.

Every optimizer batch has exactly two memory rows from distinct semantic
sources and two preservation rows from distinct sources. No batch may contain
two skins of one source. Ten epochs give `48 updates/epoch`, **480 updates per
fit**, and **40 presentations per semantic source**, preserving SEQ-113's
supported source dose. This modestly raises update count only because there are
24 rather than 16 memory sources.

## Arms, fits, and optimization contract

Inference states are `OFF`, `PLAIN`, and `CONTRASTIVE`. OFF is one contemporary
fresh-base capture shared as the deterministic reference. There are three
paired learner/optimizer seeds, `0,1,2`:

```text
PLAIN_s0       CONTRASTIVE_s0
PLAIN_s1       CONTRASTIVE_s1
PLAIN_s2       CONTRASTIVE_s2
```

That is exactly **six fresh clean-base fits**; no warm start, adapter merge, or
checkpoint selection.

- frozen official `Qwen/Qwen2.5-7B-Instruct` revision already used by the
  diagnostic series;
- all-layer attention+MLP LoRA, rank 8, alpha 16, dropout `.05`;
- AdamW, LR `3e-4`, batch 4, accumulation 1, ten epochs / 480 updates;
- response-only loss; every context and padding token masked;
- no packing and no truncation;
- same initial LoRA tensors within each paired seed;
- same semantic source at every paired update, same row order, target IDs,
  batch shapes, pre-forward CPU/CUDA RNG hashes, and optimizer defaults.

The treatment changes input token identities, so the two trajectories cannot
be bit-identical. The paired contract removes dose, target, shape, ordering,
initialization, and random-stream explanations; it identifies the two frozen
masked instruction renderings.

## Evaluation: no answer visible

Every query names a family and mode, lists the four allowed outcome identifiers
in a root-neutral order, and requests one answer. It contains no observation,
case file, earlier outcome, target statement, or worked example.

Per inference state:

| panel | unique semantics | renderings | denominator |
|---|---:|---:|---:|
| `E-TRAIN-SKIN` diagnostic | 24 observed keys | 1 seen-style neutral query | 24 |
| `H-SKIN` primary | 24 observed keys | 2 unseen query skins | 48 |
| `H-KEY` primary | 8 never-targeted keys | 2 unseen query skins | 16 |
| `LOCALITY` | 8 unseen families + 8 invalid modes | 1 held skin | 16 |
| `CANARY` | 8 new additions + 8 new copies | 1 held skin | 16 |

`H-SKIN`'s 48 rows are 24 facts rendered twice, not 48 independent facts;
`H-KEY`'s 16 rows are eight keys rendered twice. Report both rendering counts
and semantic-key counts. Report H-KEY by mode (`4` calls/mode: two held facts x
two skins) and H-SKIN by family (`6` calls/family).

With one OFF state and six fitted states, the frozen inventory is **840 native
generations** (`7 x 120`). Candidate scoring evaluates four continuations on
the 88 supported-key rows and five on the 16 LOCALITY rows: **432 scored
continuations/state, 3,024 total**. CANARY uses native exact scoring only.

### Three separate scoring columns

1. **Candidate content (primary).** Teacher-force the four complete legal
   `ANSWER: V` continuations (and `UNKNOWN` on LOCALITY), without placing any
   candidate answer in the prompt. Choose maximum summed conditional log
   probability including EOS. Equal-length outcome tokens are a preparation
   gate. Record all logits, choice, correct-minus-best-wrong margin, and legal
   mass.
2. **Permissive native semantics.** Greedy generation, max 32 tokens. Credit an
   answer only when exactly one allowed outcome appears as a complete token and
   no competing value/UNKNOWN appears. Prose or a code fence may receive
   semantic credit.
3. **Strict format.** Credit only the exact canonical `ANSWER: <value>` bytes
   (allow only the runner's prospectively fixed terminal-newline convention).

No output is repaired. Missing, truncated, multi-valued, or nonfinite output is
retained and fails the relevant column. A strict gain without candidate and
permissive-semantic gains is **FORMAT_ONLY**.

## Prospective success and disposition rules

All six fits and all panels are mandatory unless an integrity/resource stop
fires. The fit, not a rendered row, is the treatment replication unit. Report
all seed-level paired differences; do not compute significance by pretending
the repeated skins are independent learners.

The result is `CONTRASTIVE_KEYED_SCREEN_PASS` only if all of the following hold:

1. **Acquisition:** in at least two of three CONTRASTIVE seeds, candidate
   content is at least `40/48` on H-SKIN and `12/16` on H-KEY, with positive
   median correct-vs-best-wrong margin in each panel.
2. **Conditional coverage:** those qualifying seeds score at least `4/6` for
   every family on H-SKIN and at least `3/4` for every mode on H-KEY. This
   rejects fixed, family-only, and mode-only success.
3. **Paired contrastive advantage:** CONTRASTIVE is not below PLAIN on either
   content-primary panel in any seed by more than one rendering; it is strictly
   higher in at least two of three seeds; summed over seeds, its candidate
   advantage is at least `12/144` on H-SKIN and `6/48` on H-KEY.
4. **Native transfer:** permissive semantic accuracy is at least `36/48`
   H-SKIN and `10/16` H-KEY in at least two CONTRASTIVE seeds, and the summed
   paired advantage over PLAIN is at least `9/144` and `3/48`, respectively.
5. **Scope:** every CONTRASTIVE seed candidate-scores at least `14/16` LOCALITY
   as UNKNOWN and natively semantic-scores at least `13/16`.
6. **No harm:** on the 16 CANARY items, every fitted arm retains at least
   `15/16`, at least `7/8` in each class, and incurs at most one itemwise
   regression among OFF-correct cases. All outputs and captures complete.

These are intentionally joint gates. A content improvement that does not
survive unseen skins is rehearsal; direct-key success without H-KEY is keyed
memorization without relational completion; H-KEY success without direct
coverage is an anomalous slice, not a general win; candidate-only success is a
native extraction-interface gap; strict-only success is formatting.

If PLAIN is already at least `44/48` H-SKIN and `14/16` H-KEY in two or more
seeds, label the incremental treatment comparison `CEILING_LIMITED`, not a
contrastive failure. If OFF reaches those same bounds, label the task leaked or
non-diagnostic and do not fit. If neither trained arm exceeds OFF by at least
`8/48` H-SKIN candidate and `3/16` H-KEY candidate in two seeds, label
`NO_CONDITIONAL_ACQUISITION`; do not tune on these held panels.

### Stop rules

Stop before model load for any topology, balance, held-answer, tokenizer,
pairing, target-ID, mask, truncation, schedule, or hash failure. Stop after OFF
for the OFF ceiling condition. Stop future stages—but preserve completed raw
artifacts—on wrong model/root/seed, missing paired RNG identity, nonfinite
training, resource-cap exhaustion, incomplete capture, or failed GPU release.
Never score missing work as zero and never replace a failed seed.

## Resource ceiling

Hard cap: **six fits and 4.0 aggregate A40-hours**, including model-load,
training, all candidate forwards, native generations, and cleanup reservation.
CPU materialization is outside GPU accounting but finite. Before launching the
second learner-seed pair, use the completed seed-0 pair plus OFF timing to
project the full campaign; continue only if the conservative projection is at
most `3.6 A40-hours`.
At `3.6` actual aggregate hours, launch no new stage; at `4.0`, terminate the
owned stage, preserve it as operationally incomplete, and release the GPU.

SEQ-113's measured two-fit worker time and this campaign's short outputs make
the cap plausible, but that is a planning estimate, not permission to overrun.
Report device-active time and full reservation time separately and never sum
nested clocks.

## Exact permitted claim

If and only if the joint screen passes:

> On one frozen balanced four-valued authored mapping, an explicit
> difference-attention instruction in otherwise matched loss-masked training
> contexts improved three-seed LoRA acquisition, held-skin retrieval, and
> rule-identified held-key completion relative to ordinary record reading,
> without detectable scope or canary harm under the registered panels.

Even a pass does **not** establish attention mediation inside the transformer,
child authorship, DREAM quality, SLEEP, parenting, recurrence, autonomous
learning, long-horizon retention, compression, or task improvement. It selects
a compiler presentation ingredient for the authentic two-sleep experiment.

## Why this is the smallest useful next test

It spends no fit on another learning-rate or rank sweep; Q0 already showed that
more optimization of the wrong binary basis is low-value. It uses the smallest
paired seed count that exposed SEQ-113's seed-2 failure, the proven
distinct-source schedule, one balanced four-valued world, a real withheld-key
relation, and independent content/semantic/format readouts. Six fits can answer
the narrow causal question. If it passes, explicit contrast is eligible for the
authored compiler used in the vertical DEV pilot. If it fails, the authentic
vertical pilot should retain ordinary EVENT/LINK material rather than spending
more GPU on contrast wording.
