# SEQ142 prediction scaffold-withdrawal: independent pre-run audit

Date: 2026-09-13 PT  
Scope: documentation and frozen-source inspection only. No source/runtime
authoring, tokenizer/model call, GPU action, remote mutation, or scientific
execution was performed.

## Verdict in one paragraph

**REWORK, THEN GO.** The readout is worth a small inference-only run because
the three adapters already exist and it asks the next honest question after
SEQ142: does the acquired *conditional evidence-to-answer mapping* survive when
the explicit decision recipe is withdrawn? It does **not** test spontaneous
prediction-before-action, a self-initiated habit, parenting, child experience,
or prospective intelligence. The proposed 288 calls are acceptable if the
three OFF passes are deliberately retained as same-device/runtime controls;
otherwise they contain only 48 unique baseline prompts and the scientific
content fits in **192 calls** (one 48-call OFF panel plus three 48-call adapter
panels). Do not launch the current prose specification unchanged. Two concrete
implementation assumptions are false, and the original authored fixture has
an unblocked action-ID/label shortcut which the new material must break.

## What the inherited evidence actually establishes

The archived SEQ142 reduction is unusually clear:

- All three prediction fits used the same 96 authored rows (`material_seed=0`)
  and differed only in learner/fit seed.
- Each moved held typed content from 22/48 OFF to 48/48 post, with 26 wins and
  no losses; all three preserved or improved the 12 narrow canaries.
- OFF's substantive failure was over-abstention: uniquely supported cards went
  7/32 to 32/32. Missing evidence was already 8/8 OFF and conflict was 7/8.
- The recipe was rank 8, LR `3e-4`, 320 updates, 1,280 presentations over 96
  rows, with about 355k actual training tokens per fit. This is a very heavily
  rehearsed authored worksheet, not a lived-experience sleep.
- The original material itself correctly says prediction is consequence lookup
  under explicit local facts, not hidden-rule induction or calibrated
  forecasting.

Thus a fresh scaffold-withdrawal panel is a sensible *robustness diagnostic*.
Three matching fit seeds measure optimizer stability on one curriculum. They
are not three independent task distributions or three independently parented
children.

## Launch blockers

### 1. A new `material_seed` cannot create fresh facts

The existing `build_dataset(skill, seed)` explicitly changes ordering only.
`_prediction_sources` deterministically creates the same 96 train and 48 held
situations for every seed. Its regression test requires the sorted rows for
seed 0 and seed 71 to be identical. Therefore the new 24 cases require a newly
versioned, prospectively frozen material definition; calling the old builder
with another seed would silently re-read inspected cases.

### 2. The old scorer cannot score a new MINIMAL prompt unchanged

The current `score_row` reconstructs the exact old `_render` output and one of
the four exact `SKINS`, then emits `row_integrity_error` if
`row["input_messages"]` differs. A procedure-withdrawn prompt necessarily
differs. Reuse the old *typed scoring policy*, but bind a new scorer version
which reconstructs both FULL and MINIMAL views. Do not edit, replace, or
retroactively apply it to the frozen SEQ142 evidence.

### 3. The original fixture encodes the target class in the selected action ID

This is the largest scientific risk. In `_prediction_sources`, the selected
action base is

`split_base + 60 * family + 20 * outcome_index`,

where `outcome_index` is False, True, then unknown. Both train and held use the
same modulo-60 residues for those three targets. The tests cross earlier
prediction, earlier outcome, skin, and target, but do not counterbalance this
selected-action residue. Consequently 48/48 is compatible with learning some
combination of the supplied procedure, card lookup, response schema, and an
action-ID/label shortcut. It is not evidence that the adapter necessarily reads
the card. Merely choosing numerically disjoint new triples does not remove the
shortcut if the same construction is reused.

**Required repair:** make the 24 cases six disclosed four-case counterfactual
families. Within each family, reuse the same selected action identity under
four exercise-local public cards whose correct targets are respectively true,
false, absent, and conflict. The correct answer then changes while the selected
action string stays fixed. Counterbalance skin, card order, earlier prediction,
earlier outcome, integer magnitude/token length, and selected/distractor
positions across the six families. The unit of generalization is six families,
not 24 independent worlds. This design simultaneously defeats constant-answer,
action-identity, modulo/range, and first-card-entry shortcuts while retaining
exactly 24 cases.

All action triples used anywhere in a new source—selected, belief-card,
distractor, and earlier action—must be checked against the union of *all* such
triples in old train and held material. The old test checks train/held
disjointness only for selected actions, which is weaker than the new protocol's
stated requirement. New action IDs should also match the old held set's digit
and token-length distribution; moving to a new numerical magnitude would add
an avoidable tokenization/OOD confound.

### 4. FULL and MINIMAL currently change too many things

The proposal gives FULL “new facts/framing” while MINIMAL removes the procedure,
reminders, and classroom framing. That is a scaffold-*package* withdrawal, not
an isolated procedure withdrawal. For a clean comparison:

- use exactly the same old classroom skin/wrapper in both views;
- use byte-identical public facts, selected action, response-field names,
  value vocabulary, and surrounding instructions;
- let one delimited procedure block be the only semantic difference;
- FULL uses the old procedure text exactly;
- MINIMAL lists the permitted typed values but does not state which evidence
  condition maps to which value.

Prompt-token counts and the exact deleted bytes should be in the receipt. An
equal-length inert paragraph is unnecessary unless the claim is specifically
that semantic content, rather than the whole removed block including its
length/position, caused the difference. If classroom framing is intentionally
removed too, rename the treatment “broad scaffold-package withdrawal” and do
not attribute the contrast to the procedure alone.

### 5. The current 20/24 rule does not exclude the answer prior

The proposed panel has six true, six false, and twelve null/abstain targets.
Always abstaining earns 12/24. Total accuracy can therefore hide a collapsed
supported or conflict subgroup. The result must report the four groups and use
them in the continuation criterion, not merely as diagnostics.

A bounded, prospectively fixed continuation rule is:

1. **FULL manipulation check:** every adapter gets at least 20/24, at least
   5/6 in each of true, false, absent, and conflict, and no negative paired net
   against its contemporaneous OFF state. If FULL fails, MINIMAL cannot be
   interpreted as scaffold withdrawal.
2. **MINIMAL robustness check:** every adapter gets at least 20/24 and at least
   5/6 in every group; its paired post-minus-OFF net is at least +4/24, with a
   positive net on uniquely supported true+false jointly and no negative net
   on absent+conflict jointly.
3. **Evidence-dependence check:** at least 5/6 counterfactual families have all
   four target conditions correct post-adapter. This is the direct defense
   against action identity and answer-prior shortcuts.
4. If MINIMAL OFF itself is at least 20/24 with at least 5/6 in all groups,
   label the panel `BASE_CEILING_INCONCLUSIVE`; do not select harder items after
   seeing outputs and call the replacement confirmatory.

The precise +4 is a DEV decision threshold, not a confidence interval. It
prevents the same one marginal item changing in all three shared-material fits
from being promoted as a robust effect. No binomial test should treat the 288
calls as independent observations.

### 6. Score the behavior separately from the declared reason token

The frozen typed joint remains useful for continuity, but “prediction
behavior” is the exact typed pair `(decision, prediction)`. The `reason` field
is a declared fixture label, and strict format is a motor/schema measurement.
The new scorer should prospectively emit, without repairing prose:

- exact typed decision+prediction correctness;
- exact reason-label correctness;
- full typed joint correctness;
- strict canonical bytes and format class.

Use decision+prediction for the semantic group/family checks above and retain
full typed joint as a co-primary continuity endpoint. This is factorization,
not permissive semantic rescoring.

## Material and leakage freeze

Before any new model output exists, bind and test all of the following:

1. exactly six family IDs, four target conditions/family, and exactly two views
   per condition;
2. identical source facts and target bytes across the FULL/MINIMAL view pair;
3. target reconstruction from only public facts and selected action;
4. no target, case label, proof, source ID, split label, or target hash in model
   messages;
5. exhaustive old/new action-union checks, not selected-action-only checks;
6. counterbalance tables for skin, card order, earlier values, numerical/token
   shape, and target condition;
7. deterministic fixed enumeration and a prospectively hash-bound order—no
   model-generated material, output-based filtering, or favorable case
   replacement;
8. one fresh versioned scorer with mutation tests for wrong fields, types,
   values, duplicate keys, non-stop endings, view mismatch, and row-integrity
   mismatch;
9. constant-output floors (abstain 12/24; true and false 6/24 each), reported
   explicitly.

The same public belief card directly states the selected action's consequence
in the supported condition. Calling the task “prospective” only means the
selected action has not been executed in this vignette. It is still supplied-
memory lookup. The most defensible endpoint name is:

> **fresh authored evidence-use under procedure withdrawal**

It is not “self-initiated prediction,” “installed prospective behavior,” or
“the child learned to predict before acting.” A later native stream assay must
leave the decision to predict unsolicited if that stronger habit is the target.

## Baselines, calls, and pseudo-replication

There are 48 unique prompts: 24 underlying cases × two paired views. With
temperature 0 and seed 0, three OFF runs over the same prompts are technical
replicates of one frozen base. The options are:

- **192 calls (preferred for pure information efficiency):** one authenticated
  OFF pass plus one post pass for each of three adapters;
- **288 calls (acceptable for execution control):** retain one OFF pass on the
  same physical device/environment immediately paired to each adapter pass.
  Predeclare exact-output reproducibility across OFF passes as a runtime
  diagnostic and never count them as `n=3` baseline learners.

At the stated maximum of 1.5 allocated GPU-hours and zero fits, 288 is not a
scientific-budget problem. Six cold loads rather than the 288 short generations
dominate the cost. The extra 96 calls are justified only by device/runtime
matching. Cases are paired views; four cases are siblings within each of six
families; three adapters are stochastic fits on one shared curriculum. Report
all three levels explicitly and make no 288-trial significance claim.

## Custody and node-expiry gate

The node-1 archive already protects the original three prediction roots, but a
readout runner cannot blindly reuse the old absolute-path receipt on another
node: the old runner requires its fitted adapter to exist below that run's own
`run/fit/adapter` path and checks that literal path. A relocated read-only
adapter needs a new custody receipt which proves the copied inventory and
weight/config hashes equal the archived original, then proves the actual LoRA
route used those relocated bytes. Do not modify adapter files or manufacture a
fake old fit path.

Do not spend node 1's preservation window on this DEV assay. Copy and
authenticate the three adapters on a surviving node first, bind the identical
base-model/source/environment hashes, run only after GPU+process vacancy checks,
and archive the fresh raw requests, responses, routes, completion, cleanup, and
release receipts off-node. A missing adapter copy, path-only identity, lease
margin miss, or incomplete OFF/post pair is a hard stop, not a reason to use a
partially expired root.

## Exact go/no-go disposition

**NO-GO as currently written.** It would either reuse non-fresh cases, fail the
old scorer's integrity check, or require an unacknowledged new scorer; it also
does not rule out the original action-ID shortcut and bundles several prompt
changes.

**GO after the following six items are all prospectively closed:**

1. newly versioned six-quartet counterfactual material, frozen before outputs;
2. FULL/MINIMAL differ only by the declared procedure block (or the claim is
   renamed to broad package withdrawal);
3. newly versioned typed/factorized scorer and material tests pass without
   model use;
4. subgroup, family, headroom, and FULL manipulation criteria above are bound;
5. archived adapters are content-authenticated in immutable read-only mounts on
   a surviving node, with actual route checks;
6. OFF replication policy is chosen: 192 information-efficient calls or 288
   same-device controls, with the independence language fixed.

If those close, the assay is a good small DEV experiment. A positive result
would show that a heavily rehearsed LoRA can use fresh, supplied public facts
after an explicit recipe is removed. A null would remain ambiguous among
scaffold dependence, failure to use the belief card, and the old curriculum's
action-ID shortcut; it would not show that experience models cannot learn to
predict.

## Evidence inspected

- `research_notes/analysis/2026-09-13_level1_prediction_transfer_protocol.md`
- `research_notes/astra_memos/receipts_20260912/astra_level1_prediction_goal_material_20260913.py`
- `research_notes/astra_memos/receipts_20260912/test_astra_level1_prediction_goal_material_20260913.py`
- `research_notes/astra_memos/receipts_20260912/astra_level1_skill_run_20260913.py`
- `research_notes/astra_memos/receipts_20260912/astra_level1_prediction_goal_handoff_20260913.md`
- `research_notes/astra_memos/receipts_20260912/astra_level1_skill_run_20260913_handoff.md`
- `research_notes/astra_memos/receipts_20260912/astra_level1_first_roster_analysis_20260913.{md,json}`
- `research_notes/astra_memos/receipts_20260912/astra_post_pcfl_existing_behavior_options_20260913.md`
- relevant SEQ142/SEQ188 entries in `research_loop/COORDINATION.md`

