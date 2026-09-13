# Contrastive keyed-discrimination follow-up — prospective protocol v2

**Date:** 2026-09-13  
**Status:** design only; no source, material, tokenizer, model, training, or GPU
execution is authorized or claimed here.  
**Scientific class:** externally authored, loss-masked SFT diagnostic. This is
not child-authored SLEEP, parenting, self-learning, or an organism result.
**Supersession:** this v2 text supersedes the v1 protocol at commit `18fa1f0f`
and resolves the result-blind red-team at commit `e361daf7`. Only v2 is
eligible for later implementation.

## Decision in one paragraph

Run one small paired experiment asking whether an explicit instruction to
compare similar records helps a rank-8 LoRA learn a **four-valued joint-key
map**. PLAIN and CONTRASTIVE see the same literal observations in the same
order, have byte-identical assistant targets, and use the same optimizer
schedule and random streams. They differ only in one truthful loss-masked
instruction: ordinary record reading versus explicit comparison across the
three observed modes. There is no arm-dependent visible padding. At test time
no observation, rule reminder, outcome roster, or answer is shown on the
primary prompts. The primary score chooses among four short continuations by
conditional likelihood, so JSON or prose formatting cannot create a content
win; candidate-free native generation is separately scored permissively for
semantic content and strictly for format, with closed-set native selection only
as a diagnostic. Three paired learner seeds require six fits total.

This directly repairs the live screen's two fatal attribution defects:

1. no evaluation prompt identifies the correct outcome, and the primary
   candidate-scoring/candidate-free prompts contain no outcome string at all;
   the separately labeled closed-set diagnostic shows only a balanced roster;
   and
2. there is no Boolean/opposite event to negate. Outcomes are four opaque,
   non-ordered values and the held relations vary across families.

V2 disposes the independent rework list explicitly:

| red-team issue | v2 disposition |
|---|---|
| visible arm-dependent padding | deleted; only attention-masked tensor padding |
| false contrast wording | replaced by exact truthful three-record statements |
| coupled construction randomness | SHA-256 domain separation + bounded receipts |
| untested generator shortcuts | finite exhaustive nuisance library before OFF |
| held-only rule cue | rule absent from every evaluation route |
| native candidate bank | candidate-free primary + separately labeled closed set |
| cross-seed gate assembly | one same-seed six-part conjunction, required `2/3` |

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
and is absent from every evaluation prompt. It reveals no particular answer
during training. The held answer is identifiable from the family's three
grounded observations plus this rule; it is never an assistant target or a
stated source fact. At evaluation, using the rule therefore requires retaining
it from the authored fit rather than responding to a held-panel cue.

Opaque identifiers are deterministically generated from a frozen seed and a
bounded candidate pool. Native preparation may reject candidates solely to
make each identifier class equal in tokenizer length. It may not query model
probabilities or change the world. Record the accepted strings, attempts,
token IDs, mapping, held mask, and all hashes before OFF inference.
Freeze the permissive parser's exact boundary alphabet before identifier
selection, and reject any outcome identifier set that overlaps pairwise or
with `UNKNOWN` under that boundary rule. This makes permissive native scoring
an exact lexeme test rather than a substring accident.

### Independent construction domains and shortcut certificate

No mutable pseudorandom generator is shared across construction decisions.
Use SHA-256 counter streams with separately frozen domain strings for
`IDENTIFIERS`, `MAPPING`, `HELD_MASK`, `TRAIN_SKIN`, `ROW_ORDER`,
`CANDIDATE_ORDER`, and `CANARY`. Consuming or rejecting a value in one stream
must leave every other stream byte-identical. Identifier acceptance depends
only on the predeclared lexical/token-length constraints; mapping and held-mask
acceptance depend only on the predeclared balance/shortcut constraints. No
acceptance decision may use a model probability, generated response, or later
score. Serialize every rejected attempt and reason.

Before OFF, exhaustively enumerate the finite registered shortcut library over
all 24 observed and eight held semantic keys, and over their expanded
skin/candidate-order renderings where those features exist:

- constant outcome;
- mode only, family construction index modulo four, held position only, row
  position modulo four, skin, candidate position, and target-frequency class;
- first/last identifier byte modulo four, tokenizer length, first/last token ID
  modulo four, lexical-rank quartile, and SHA-256-prefix quartile;
- all affine ordinal rules `(a*family_index + b*mode_index + c) mod 4` for
  `a,b,c in {0,1,2,3}`; and
- the Bayes-best lookup for every pair of the preceding **coarsened nuisance**
  features.

For each predictor preserve its definition, prediction on every key, support,
label counts, best accuracy, ties, and digest. Full family identity plus mode is
the intended key and is not mislabeled a nuisance. Latent permutation identity
plus mode is an oracle encoding of the answer; report its `100%` value but do
not call it a visible shortcut. H-KEY has one held cell per family, so family
identity alone can encode the family's completed missing value; consequently
H-KEY supports **family-level withheld-cell completion compatible with the
rule**, not by itself rule use or joint-key use. The joint-key claim comes from
H-SKIN's within-family mode coverage.

Accept the first mapping/held-mask candidate that satisfies the structural
balances above and for which no registered visible single, affine, or
coarsened-pair nuisance exceeds `12/24` on observed keys or `4/8` on held keys,
except the prospectively disclosed H-KEY family-identity route. Abort after 256
candidates rather than relaxing a bound. This deterministic filter is part of
the frozen task distribution, not post-result tuning.

The hidden-answer certificate must additionally prove:

- `0/8` held `(family,mode,outcome)` triples occur as stated source facts;
- `0/8` held key-answer pairs occur in any model-visible context, target,
  wrapper, metadata-derived prompt, or filename-derived prompt field;
- `0/96` memory targets and `0/96` preservation targets attach an answer to
  its held key;
- a public-input-only oracle reconstructs `8/8` held answers from the three
  same-family observations and the shared rule; and
- deleting any one observed row leaves at least two legal completions in all
  `24/24` one-row deletion cases.

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

- **PLAIN:** “Review the three observed mode records. Each names its mode and
  its recorded outcome. Identify the selected family-mode pair before returning
  its recorded outcome.”
- **CONTRASTIVE:** “Compare the three observed mode records side by side. Each
  names a different mode and a different recorded outcome. Distinguish the
  selected family-mode pair before returning its recorded outcome.”

PLAIN is not told to avoid comparison. CONTRASTIVE is a positive additional
cognitive cue, not PLAIN sabotage. The CONTRASTIVE statement is exactly true:
the three observed modes and their three outcomes are distinct under a
permutation. Neither instruction contains an outcome, derived held answer,
mnemonic, or mapping rule beyond the shared public rule.

There is **no visible arm-specific padding**. Preserve each instruction exactly
as written and report its natural token cost. To equalize tensor/batch shapes,
the collator right-pads both arms only after the native EOS to the paired
batch's joint maximum, using the same pad ID with `attention_mask=0` and label
`-100`; those positions are neither attended to nor supervised. A pre-fit
isolation check must hold tensor shape, non-padding tokens, labels, RNG state,
and attention mask fixed, replace every masked pad ID with a different legal
token ID, and require bit-identical non-padding/answer-prefix logits,
supervised loss, and LoRA-parameter gradients. It must also assert that every
zero-mask position is a trailing suffix after EOS and has label `-100`.
Failure aborts. Natural input-token counts and target positions may differ as
part of the two frozen instruction renderings and must be reported; padded
tensor shapes, target token IDs, row counts, and optimizer steps are matched.
Targets must be token-for-token identical within every PLAIN/CONTRASTIVE pair.

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
fit**, and **40 selected-target presentations per semantic source**, preserving
SEQ-113's supported target dose. Because each row also contains its family's
complete three-record observed block, each observed fact occurs loss-masked in
`3 selected sources * 4 skins * 10 epochs = 120` memory contexts. Both counts
are arm-identical and must be reported separately. This modestly raises update
count only because there are 24 rather than 16 memory sources.

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

## Evaluation: answer-hidden primary routes

Every supported-key query names only a family and mode and requests one answer.
It contains no observation, case file, earlier outcome, public one-of-each rule,
target statement, worked example, or outcome roster. The template distribution
is byte-identical across E-TRAIN-SKIN, H-SKIN, and H-KEY apart from the
registered key and skin; panel identity and `held` status never enter a prompt.
Thus the held panel cannot be solved by a held-only rule cue. A successful
answer must be carried from training, but this panel alone cannot distinguish
retention/use of the structural rule from an induced family-level association.

Per inference state:

| panel | unique semantics | renderings | denominator per native route |
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

Candidate scoring and candidate-free native generation use those roster-free
prompts. A second **closed-set native** route adds a common line containing all
four outcomes (and UNKNOWN for LOCALITY) in a candidate order generated from
the independent `CANDIDATE_ORDER` domain and balanced for correct position by
panel and skin exactly where the denominator permits, otherwise with position
counts differing by at most one. Closed-set and candidate-free results are
never pooled.

With one OFF state and six fitted states, the frozen inventory is **1,568
native generations**: per state, candidate-free and closed-set generation each
cover the 104 key/locality rows (`2 x 104`), while CANARY is generated once
(`16`), for `224/state` and `7 x 224`. Candidate scoring evaluates four
continuations on the 88 supported-key rows and five on the 16 LOCALITY rows:
**432 scored continuations/state, 3,024 total**. CANARY uses native exact
scoring only.

### Separate content, native-route, and format columns

1. **Candidate content (primary).** Teacher-force the four complete legal
   `ANSWER: V` continuations (and `UNKNOWN` on LOCALITY) after the roster-free
   prompt. Choose maximum summed conditional log probability including EOS.
   All five complete continuations must have equal token length. Record all
   logits, choice, correct-minus-best-wrong margin, and legal mass.
2. **Candidate-free native semantics (primary native).** Greedy generation
   from the roster-free prompt, max 32 tokens.
3. **Closed-set native semantics (diagnostic).** Greedy generation from the
   otherwise identical prompt containing the balanced candidate roster. This
   measures selection/copy assistance and cannot satisfy the primary native
   gate.
4. **Permissive semantic column.** On either native route, credit only when
   exactly one allowed identifier occurs as a boundary-delimited literal byte
   string and no competing value/UNKNOWN occurs. Prose or a code fence can
   receive semantic credit; substrings, tokenizer-token overlap, normalization,
   fuzzy match, or repair cannot.
5. **Strict format column.** Credit only the exact canonical
   `ANSWER: <value>` bytes (allow only the runner's prospectively fixed
   terminal-newline convention).

No output is repaired. Missing, truncated, multi-valued, or nonfinite output is
retained and fails the relevant column. A strict gain without candidate and
candidate-free permissive-semantic gains is **FORMAT_ONLY**. A closed-set gain
without candidate-free gain is **ROSTER_ASSISTED_SELECTION_ONLY**.

## Prospective success and disposition rules

All six fits and all panels are mandatory unless an integrity/resource stop
fires. The fit, not a rendered row, is the treatment replication unit. Report
all seed-level paired differences; do not compute significance by pretending
the repeated skins are independent learners.

Define a `JOINT_SEED_PASS` separately for each paired learner seed. One seed
passes only if **that same seed** satisfies all of the following:

1. **Candidate acquisition:** CONTRASTIVE candidate content is at least
   `40/48` H-SKIN and `12/16` H-KEY, with positive median
   correct-vs-best-wrong margin in each.
2. **Conditional slices:** CONTRASTIVE is at least `4/6` in every family on
   H-SKIN and at least `3/4` in every mode on H-KEY. H-SKIN supplies the joint
   family-and-mode discrimination result; H-KEY supplies family-level
   withheld-cell completion compatible with the supplied one-of-each rule,
   not evidence that the rule was the model's causal procedure.
3. **Candidate direction:** on this seed, CONTRASTIVE exceeds its paired PLAIN
   by at least `2/48` H-SKIN and `1/16` H-KEY. A tie in either panel is not a
   seed pass.
4. **Candidate-free native transfer:** CONTRASTIVE permissive semantics is at
   least `36/48` H-SKIN and `10/16` H-KEY, with at least `4/6` in every H-SKIN
   family and `3/4` in every H-KEY mode.
5. **Candidate-free native direction:** on this same seed, CONTRASTIVE exceeds
   paired PLAIN by at least `2/48` H-SKIN and `1/16` H-KEY. Closed-set native
   scores and strict formatting cannot satisfy this condition.
6. **Scope and no harm:** CONTRASTIVE candidate and candidate-free native score
   at least `14/16` and `13/16` LOCALITY respectively. Both fitted arms retain
   at least `15/16` CANARY, at least `7/8` in each canary class, and incur at
   most one itemwise regression among OFF-correct cases.

The campaign is `CONTRASTIVE_KEYED_SCREEN_PASS` only if at least **two of the
same three paired learner seeds** are `JOINT_SEED_PASS`, all outputs/captures
are complete, and the across-seed summed CONTRASTIVE-minus-PLAIN advantages are
at least:

- candidate H-SKIN `12/144` and H-KEY `6/48`; and
- candidate-free native H-SKIN `9/144` and H-KEY `3/48`.

The remaining seed may not show an adverse reversal worse than `-2/48` on
H-SKIN or `-1/16` on H-KEY in either candidate or candidate-free native
semantics. Report closed-set native and strict format for every seed, but they
are never part of the treatment-pass numerator.

These are intentionally joint gates. A content improvement that does not
survive unseen skins is rehearsal; direct-key success without H-KEY is keyed
memorization without withheld-cell completion; H-KEY success without direct
coverage is an anomalous slice, not a general win; candidate-only success is a
native extraction-interface gap; strict-only success is formatting.

If the same two PLAIN seeds are already at least `44/48` H-SKIN and `14/16`
H-KEY in both candidate and candidate-free semantic columns, label the
incremental comparison `CEILING_LIMITED`, not a contrastive failure. If OFF
reaches those same bounds on the shared prompts, label the task leaked or
non-diagnostic and do not fit. `NO_CONDITIONAL_ACQUISITION` requires that in
fewer than two individual seeds does either fitted arm beat OFF by both
`8/48` H-SKIN candidate and `3/16` H-KEY candidate. Never assemble a verdict
from candidate success in one seed and native success in another.

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
Every fit and inference stage owns exactly one A40; tensor/pipeline parallelism
is forbidden. Parallel wall-clock execution does not reduce aggregate device
accounting.
CPU materialization is outside GPU accounting but finite. Before launching the
second learner-seed pair, use the completed seed-0 pair plus OFF timing to
project the full campaign; continue only if the conservative projection is at
most `3.6 A40-hours`.
At `3.6` actual aggregate hours, launch no new stage; at `4.0`, terminate the
owned stage, preserve it as operationally incomplete, and release the GPU.
The controller samples owned-process/device reservation time every 15 seconds
and persists the cumulative sum after every sample. Each worker also enforces a
monotonic deadline inclusive of model load, work, and cleanup: 1,200 seconds per
fit and 900 seconds per inference-state capture. Their total maximum allocation
is `6*1200 + 7*900 = 13,500` GPU-seconds (`3.75 A40-hours`), leaving 900
GPU-seconds below the campaign cap. The controller refuses any stage whose
remaining allocation cannot cover its entire deadline and never reallocates
unused budget after a scientific failure. Thus the cap is enforced before
launch rather than discovered after an unbounded worker.

SEQ-113's measured two-fit worker time and this campaign's short outputs make
the cap plausible, but that is a planning estimate, not permission to overrun.
Report device-active time and full reservation time separately and never sum
nested clocks.

## V2 arithmetic self-check

| object | exact calculation | total |
|---|---:|---:|
| semantic table | `8 families * 4 modes` | 32 keys |
| split | `24 observed + 8 held` | 32 keys |
| memory rows/fit | `24 sources * 4 skins` | 96 |
| replay rows/fit | `24 sources * 4 skins` | 96 |
| updates/fit | `(96+96)/4 * 10 epochs` | 480 |
| all fit updates | `480 * 6` | 2,880 |
| row presentations/fit | `192 * 10` | 1,920 |
| all row presentations | `1,920 * 6` | 11,520 |
| key/locality rows/state | `24+48+16+16` | 104 |
| native generations/state | `104 candidate-free + 104 closed + 16 canary` | 224 |
| all native generations | `224 * (1 OFF + 6 fitted)` | 1,568 |
| candidate continuations/state | `(24+48+16)*4 + 16*5` | 432 |
| all candidate continuations | `432 * 7` | 3,024 |
| maximum GPU allocation | `6*1,200 + 7*900` | 13,500 s = 3.75 A40-h |

Every equality is a preparation assertion to be mechanically reconstructed;
the implementation must abort rather than repair a mismatch.

## Exact permitted claim

If and only if the joint screen passes:

> On one frozen balanced four-valued authored mapping, an explicit
> difference-attention instruction in otherwise matched loss-masked training
> contexts improved paired-seed LoRA acquisition and candidate-free held-skin
> retrieval of family-by-mode bindings, and improved family-level completion of
> withheld cells compatible with a one-of-each rule supplied during training,
> relative to ordinary
> record reading, without detectable scope or canary harm under the registered
> panels.

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
