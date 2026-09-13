# Result-blind red-team: contrastive keyed-discrimination follow-up

**Date:** 2026-09-13
**Evidence cut:** `18fa1f0f`
**Object audited:**
`research_notes/analysis/2026-09-13_contrastive_keyed_discrimination_followup_protocol.md`
**Scope:** protocol text only. No source, model, tokenizer, prepared material,
result, runtime artifact, or GPU was read or used.

## Verdict: REWORK

The K4 topology, denominator arithmetic, and one-world/three-optimizer-seed
claim boundary are mostly coherent. The experiment is not yet causally
identified as **plain instruction versus contrastive instruction**, however.
The arms also receive different visible padding; the contrastive wording is
not a true statement of the K4 semantics; held and observed panels may be
distinguished by the presence of the one-of-each rule; and the success logic
can satisfy candidate and native gates in different seeds. The native prompt
also contains all four outcome strings, so it is closed-set selection, not
candidate-free recall.

These are scientific treatment/readout changes, not clerical repairs. I did
not edit the protocol or silently choose replacement wording.

## 1. What is exact and valid

### K4 arithmetic

The declared table has `8 x 4 = 32` joint keys. Holding one key per family
leaves exactly `24` observed keys and `8` held keys.

If each `(mode,outcome)` cell occurs twice in the complete table, each outcome
occurs eight times. Holding every outcome twice leaves each outcome exactly
six times among the observed targets. Therefore:

- observed fixed-outcome ceiling: `6/24 = 1/4`;
- held fixed-outcome ceiling: `2/8 = 1/4`;
- observed family-only ceiling: `1/3`, or `2/6` after two skins;
- observed mode-only ceiling: at most `1/3`;
- held mode-only ceiling: `1/2`, or `2/4` after two skins.

The per-family permutation rule makes the missing held outcome uniquely
identifiable from that family's three observations: it is the sole unused
outcome. This is valid rule completion. Because every training context exposes
the three observations, the result tests whether this completion is acquired
during training and later emitted, not necessarily whether it is recomputed at
evaluation.

### Training and evaluation counts

The training arithmetic closes:

- memory: `24 sources x 4 skins = 96` rows/epoch;
- preservation: `24 sources x 4 skins = 96` rows/epoch;
- total: `192` rows/epoch;
- batch size four: `48` updates/epoch;
- ten epochs: `480` updates and `1,920` row presentations/fit;
- six fits: `2,880` updates and `11,520` row presentations;
- every semantic source: `4 x 10 = 40` presentations/fit.

The inference inventory also closes. Each state has
`24 + 48 + 16 + 16 + 16 = 120` generations. OFF plus six fitted states gives
`7 x 120 = 840`. Candidate scoring has
`88 x 4 + 16 x 5 = 432` complete continuations/state and
`7 x 432 = 3,024` total. CANARY is generation-only.

The `4.0` aggregate A40-hour cap explicitly includes loading, fits, candidate
forwards, native generations, and cleanup, with a `3.6` no-new-stage boundary.
It is a real campaign cap. An executor still needs a finite monitor cadence or
per-stage deadline to make the `4.0` termination enforceable rather than
detecting it after an overshoot.

### Unit and claim boundary

The protocol correctly has one world/mapping root and three paired
learner/optimizer seeds. The paired fit is the optimization replication;
skins and held calls are repeated measurements. A pass can support only the
written one-frozen-mapping diagnostic, not population-of-worlds or
population-of-children generality. The exact permitted claim mostly respects
that boundary.

## 2. Hidden-answer integrity is plausible but not executable yet

The intended visibility rule is sound: the held `(family,mode,outcome)` fact
is not a source fact or assistant target, while the three observed facts and
public one-of-each rule make it derivable. Mapping, held mask, accepted
identifiers, and hashes are sealed before OFF.

The protocol does not yet define the mechanical certificate. Before model
load, require exact checks over all eight held cells:

- `0/8` held `(family,mode)` facts occur as stated source facts;
- `0/8` held answers occur paired with their held keys in any model-visible
  context, target, wrapper, metadata, or filename-derived prompt field;
- `0/96` memory targets and `0/96` preservation targets equal a held answer
  *for its held key*;
- a public-input-only oracle reconstructs exactly `8/8` held answers from the
  three same-family observations plus the shared rule;
- deleting any one of the three observations leaves at least two legal
  completions on `24/24` one-row deletion cases; and
- identifiers, mapping, held mask, row order, and candidate order use
  prospectively separate RNG domains, with no rejection conditional on an
  answer or model score.

The last two checks matter. Unique completion with all three observations does
not show all 24 facts are necessary, and one undifferentiated seed does not
exclude an accidental algebraic relation between family order, mode order,
permutation choice, held position, and outcome order.

## 3. The treatment differs in more than the intended instruction

The protocol says the arms differ only in a loss-masked instruction, then
adds a visible padding suffix to the shorter context. Context loss masking
does not make context tokens causally inert: every visible token changes the
hidden state from which the answer tokens are predicted. Token-count and
batch-shape equality remove dose/position/shape explanations; they do not make
different padding identities an inert intervention.

Thus the identified treatment is currently:

```text
CONTRASTIVE instruction + its padding realization
versus
PLAIN instruction + its different padding realization.
```

It is not contrastive semantics alone. Padding length or content could act as
a learned prompt marker or alter the target boundary state. Calling a suffix
“semantically inert” is not a model-free guarantee.

In addition, “attend to which mode changes the outcome” is false or undefined
for the stated K4 object. There is no reference mode and every family's four
modes map to four distinct outcomes. This can teach a different latent task,
not merely a more explicit strategy for the same task.

A rework must prospectively choose either equal-native-token truthful
instructions without visible arm-specific padding, or name the full rendered
strings as the treatment and narrow the claim. Choosing those bytes is a
scientific protocol decision, so this audit does not supply or patch them.

## 4. The current balance rules do not close every shortcut

The marginal conditions close constant outcome, mode-only, ordinary
position-only, and Boolean/polarity shortcuts. Four opaque unordered outcomes
remove the prior screen's simple negation rule, and identical targets remove
an exact-format training advantage.

They do not close these routes:

1. **Panel-conditional family lookup.** The rule is explicitly said to be
   repeated in held-key queries, while the general evaluation-query paragraph
   does not say it is present in E-TRAIN-SKIN and H-SKIN. If rule presence
   distinguishes H-KEY, the model may use `(rule-present, family)` to emit one
   stored missing value per family and use `(rule-absent, family, mode)` on
   observed keys. H-SKIN family coverage and H-KEY mode coverage both pass.
2. **Cross-family permutation algebra.** Eight distinct permutations and
   balanced columns do not prevent a simple relation involving family
   generation order, family nonce features, mode order, permutation index, or
   held position. The protocol does not state how mapping and mask are sampled
   independently of those fields.
3. **Candidate position/copy.** Fixed candidate order is balanced globally,
   but the correct outcome string is literally present in every native prompt.
   Native scoring therefore measures selecting/copying one of four visible
   strings, not recalling a symbol without candidates.
4. **Training copy.** Every observed training answer is already present in its
   fact block. This is equal across arms and therefore not an attribution
   confound, but the result is acquisition from supervised copy contexts. It
   should not be described as learning an unshown observed fact.

Require byte-identical query-template distributions across panels apart from
the registered key and skin, or explicitly audit every panel marker. The
one-of-each rule and candidate roster must appear under the same policy in all
supported-key panels. Before fitting, enumerate registered predictors over the
24 observed and eight held semantic keys: constant outcome, family only, mode
only, family/mode ordinal arithmetic, family-token features, held position,
permutation rank/class, row order, candidate position, target frequency, and
every pairwise nuisance combination. Report exact keys, support, label counts,
and Bayes-best accuracy rather than only marginal balance.

Because there is only one world, a family identifier is an intended key and
cannot be forced to collide away. The narrow assay can still pass, but any
simple generator algebra discovered by the exhaustive audit makes this root
non-diagnostic and requires a new prospectively generated root.

## 5. Candidate and native columns are separated, but native is closed-set

Teacher-forced four-way sequence scoring, including EOS and equal target-token
length, is a good formatting-insensitive primary measure. Permissive versus
strict greedy columns also correctly separate semantic selection from exact
formatting.

However, the protocol simultaneously says no candidate answer is placed in
the prompt and says all four allowed outcome identifiers are listed there.
The correct answer string is therefore visible but not designated. This is
not answer leakage in a balanced multiple-choice task, but it is a candidate
bank. The native metric must be called **closed-set native selection**.

If candidate-free native retrieval is intended, add a separately frozen
generation panel whose prompt omits the four outcomes and whose strict parser
accepts the opaque outcome vocabulary without exposing it. Do not silently
reinterpret the existing panel. In either version, define permissive matching
over exact raw identifier lexemes with boundary rules; tokenizer-token
substrings are not a semantic parser.

## 6. The joint PASS gate is not actually joint by seed

Clause 1 can qualify candidate seeds `{0,1}` while clause 4 qualifies native
seeds `{1,2}`. Both clauses pass although only seed `1` achieves acquisition
and native transfer together. The prose then claims joint three-seed
acquisition/retrieval/transfer.

Similarly, “strictly higher in at least two of three seeds” in clause 3 does
not specify whether the same two seeds must be strictly higher on both H-SKIN
and H-KEY, or whether either panel suffices. The ceiling and
`NO_CONDITIONAL_ACQUISITION` dispositions have the same seed-set ambiguity.

The rework must define one seed-level conjunction and then require it in an
exact number of paired seeds. At minimum, the same `>=2/3` seeds should pass
candidate thresholds, family/mode slices, native thresholds, and the intended
per-panel paired direction. Aggregate `12/144`, `6/48`, `9/144`, and `3/48`
deltas may remain secondary campaign-wide gates. This changes the release
criterion and therefore is not patched here.

## 7. Required disposition

Do not execute the current bytes or promote contrastive wording from a pass.
Reissue a versioned protocol that disposes all of the following before model
load:

- one truthful same-task contrastive instruction;
- instruction-only treatment isolation, with no visible padding confound;
- domain-separated mapping/mask/identifier/order generation and an exhaustive
  nuisance-projection audit;
- identical rule/candidate/template policy across observed and held panels;
- explicit closed-set-native wording or a genuinely candidate-free native
  panel;
- a raw-lexeme permissive parser; and
- a same-seed joint release gate with unambiguous per-panel directions.

Retain the existing K4 balance, 24/8 topology, 96+96 row schedule, 480 updates,
six paired fits, 840 native generations, 3,024 candidate continuations, one
world-root claim boundary, and 4.0 aggregate A40-hour cap. Those parts do not
need redesign.
