# Audit: the eight Level-1 behaviours and the minimum combined birth

**Date:** 2026-09-13 PT  
**Scope:** repository-evidence and design audit only. No source implementation,
material generation, model/tokenizer call, fit, checkpoint, GPU, remote, or
scientific execution was performed.

## Bottom line

**The eight named Level-1 behaviours were never trained together in one
adapter.** SEQ142/146 ran `8 behaviours x 3 learner seeds = 24` fresh LoRA
fits. Every fit received `96` rows for exactly one named behaviour and no rows
from the other seven. Therefore the eight ceiling-like fixture results cannot
be added together and called one capable child.

But “all previous behaviour training was singular” is also too strong. Three
smaller joint-adapter precedents exist:

1. SEQ120 trained PROSPECT, REVISE, ADDITION, and COPY together in one
   `256`-row adapter. It learned the headline routines but failed the stronger
   conditional-locality and preservation conjunction.
2. SEQ106 continued one adapter on the old prediction/action habit plus a new
   input-order convention, while rehearsing old memory rows. Both output
   conventions were installed, but memory remained `4/16` and no output
   depended on a retrieved intermediate.
3. SEQ113 put authored memory lookup and arithmetic practice in one adapter.
   The adapter retained both on their separate panels, but the tasks never
   required the memory result to control the arithmetic/action.

So the missing evidence is precise: **one adapter has not yet been shown to
carry the relevant atomic behaviours and use one behaviour's returned content
to select the next behaviour or action.** That junction—not mere coexistence
and not all eight labels at once—is the minimum birth experiment.

## What was actually tested one behaviour per adapter

The frozen Level-1 runner calls `build_dataset(plan["skill"], ...)` once and
fits one fresh adapter to that returned training set. The source generators
accept one named skill at a time. The archived analyses list twelve distinct
roots in SEQ142 and twelve in SEQ146, one root for every behaviour/learner-seed
pair.

Every cell used a fresh Qwen2.5-7B-Instruct base plus one rank-8 LoRA, `96`
training rows, `320` updates, `1,280` row presentations, `48` held authored
vignettes, and `12` narrow copy/add canaries. All prompts state the local
decision policy. These are heavily rehearsed, open-book authored-procedure
screens—not free agent cognition.

| Named behaviour | Exact proxy fitted and tested | Terminal authored-fixture result | Important boundary |
|---|---|---:|---|
| perception | bind the selected final TRY, prior prediction, and public outcome, or abstain | `21 -> 47/48/48` | conditional extraction plus schema; not autonomous perception |
| contradiction | label explicit prediction/outcome as agree, disagree, or insufficient | `17 -> 48/48/48` | local classification; no belief revision across time |
| self-reflection | classify one of six supplied event conditions, copy evidence, emit its prescribed action | `0 -> 48/48/48` | action is label-governed; not reflection on the model's own cognition |
| repetition | choose rehearse/skip from explicit relevance/budget fields and copy support | `0 -> 48/48/48` | tests a stated policy, not actual rehearsal; seeds 0/1 each lost one canary |
| update judgement | admit/reject/abstain a proposed record against a supplied public source | `8 -> 48/48/48` | source-checking worksheet, not a live compiler decision |
| prediction | use a public belief card to answer Boolean/abstain | `22 -> 48/48/48` | original construction has an action-ID/target-class shortcut; do not treat `48/48` as clean evidence use |
| goal completion | complete only when supplied verified state satisfies all stated requirements | `32 -> 48/48/48` | supplied completion test; not goal creation or long-horizon planning |
| meta-reflection | classify before/after/delayed checks and emit a prescribed action | `9 -> 48/48/48` | authored vignette classification; seed 2 lost one canary; not recursive metacognition |

All three learner seeds within a behaviour used the same material seed. They
are optimizer replications, not three independent curricula. Repetition and
meta-reflection also reused their four wrapper families between train and held.
The first-roster prediction result has the later documented ID shortcut. The
results therefore justify “these output procedures are writable at high
repetition,” not “the eight cognitive faculties exist.”

Primary evidence:

- `research_notes/astra_memos/ASTRA_LEVEL1_SKILL_ROSTER_PROTOCOL_2026-09-13.md`
- `research_notes/astra_memos/receipts_20260912/astra_level1_skill_run_20260913.py`
- `research_notes/astra_memos/receipts_20260912/astra_level1_first_roster_analysis_20260913.{md,json}`
- `research_notes/astra_memos/receipts_20260912/astra_level1_second_roster_analysis_20260913.{md,json}`
- `research_notes/analysis/2026-09-13_level1_second_roster_result_blind_claim_audit.md`
- `research_notes/analysis/2026-09-13_level1_prediction_transfer_prerun_audit.md`

## The joint-adapter precedents do not close the junction

### SEQ120: a real combined birth, but not the eight-behaviour birth

`organism_v6/birth_conditional_corpus.py` builds 32 closed groups. Every group
contains two PROSPECT, two REVISE, two ADDITION, and two COPY rows: `64` rows
per operation and `256` total in one fit. Its own material explicitly records
`trained_chain_rows=0`.

The AUTH adapter scored PROSPECT `32/32` and REVISE `58/64`, but only `26/32`
on each of the expected/observed/prior-action locality twins (gate `29/32`)
and addition fell to `15/16`. This is positive evidence that several authored
routines can coexist, and negative evidence against equating top-line routine
scores with conditional selection. It is the strongest direct precedent for
using a matched deranged junction control in the next birth.

### SEQ106 and SEQ113: coexistence, not composition

SEQ106 produced correct three-line input/prediction/action outputs under two
different trained orders while retaining the inherited prediction and action
fields. The prompt-visible operands independently determine every line; no
retrieved output controls another operation.

SEQ113 stored the same sixteen memory facts and retained arithmetic in one
adapter across three fit seeds. Memory and arithmetic were tested separately.
The result proves compatible rehearsal better than isolated adapters would,
but contains no memory-conditioned action endpoint.

Primary evidence:

- `research_notes/astra_memos/ASTRA_BIRTH_COMPONENT_RESULT_2026-09-13.md`
- `research_notes/astra_memos/receipts_20260912/astra_two_habit_result_review_20260912.md`
- `research_notes/astra_memos/receipts_20260912/astra_next_composition_decision_20260913.md`
- SEQ106 and SEQ113 in `research_loop/COORDINATION.md`

## Audit of the staged composition-birth proposal

The current proposal gets four major decisions right:

1. It teaches one recurrent `current state + goal -> self-issued READ ->
   interpret -> STEP -> compare -> continue/STOP` policy rather than stacking
   eight adapters.
2. It keeps the birth content and topology disjoint from PCFL and GOAL-BRAID.
3. It tests the policy first with exact external text, before asking a LoRA to
   carry both policy and personal memory.
4. It uses one continued adapter and makes actor/reader coexistence a hard
   gate before the personal-memory factorial.

Stage 0 and Stage 1 are therefore well targeted and should stand. They are a
material/shortcut audit and a cheap base/interface sentinel, not overbuilding.

Two Stage-2 details should change before any fit:

### 1. The active sham does not fully match the atomic skills

The proposed command-card sham teaches syntax, activity, and copying, but the
composition arm alone receives the conditional atomic policies. A later
`C > S` difference could therefore mean “four useful procedures were taught”
rather than “linked examples taught the junction.” The birth comparator should
contain the same atomic transition targets and dose while withholding only
their cross-turn causal connection.

### 2. The unique-unit/dose choice is weakly anchored

The proposed Stage 2 shows `1,024` unique child turns only once at D1 and twice
at D2, at LR `3e-5`. The clean Level-1 cells repeated each of `96` rows about
`13--14` times at LR `3e-4`. SEQ120 repeated `256` joint rows four times at LR
`1e-4`; it learned headline routines but missed locality. Task difficulty is
not directly comparable, so these numbers do not prescribe a learning rate.
They do show that one or two presentations per unique linked turn is an
unjustified terminal negative test.

The cheapest repair is fewer unique junction cases with more repetitions,
using the same total update ceiling. Do not increase the full program before
testing that repair.

## Minimum scientifically justified combined curriculum

Call the module `M-COMBINE-4`. It contains four functional transitions—not
eight psychological labels:

1. **SEEK:** from current state plus goal, decide what relation is missing and
   issue the corresponding opaque READ.
2. **PROSPECT:** interpret the exact returned EVENT rows, predict one immediate
   consequence, and choose STEP.
3. **CHECK:** compare the predicted next state with the public CURRENT result;
   keep the working belief on match and revise only the implicated relation on
   mismatch.
4. **CONTINUE/STOP:** if the goal is verified, STOP; otherwise carry the
   updated state into the next SEEK transition.

This condenses the useful parts of the prior fixtures:

- perception and prediction feed PROSPECT;
- contradiction, update judgement, and the narrow self-reflection proxy feed
  CHECK;
- goal completion feeds CONTINUE/STOP;
- repetition belongs first in the **training/replay schedule**, not as another
  scored runtime field; and
- meta-reflection is deferred until a separate allocation task shows that the
  four-transition loop fails because it cannot decide how much to think.

### Small exact corpus

Use `32` target-disjoint causal twin pairs (`64` one-junction cases). Each case
has exactly four supervised child continuations, one per transition above:
`256` unique child-turn units total. Inputs—task, exact memory return, and
world outcome—remain loss-masked; only the child's next THINK/READ/STEP/STOP
continuation is a target.

Cross goal side, deep relation, port order, identifier position, surface skin,
and match/mismatch state. Train on at least two unrelated authored topology
families and reserve a third family for the exact-text chain readout. The
generator must use fresh opaque identifiers and must not import, inspect, or
canonicalize against any sealed PCFL/GOAL-BRAID instance. It may audit against
the public forbidden **specification** only.

At D1, present all `256` units four times: `1,024` presentations / batch 4 =
`256` updates. If acquisition and generic canaries are intact but under the
frozen chain gate, continue the same paired fits to eight presentations per
unit: `2,048` presentations / `512` total updates. D2 is terminal for this
version. This preserves the staged proposal's update ceilings while putting
repetition, rather than uncontrolled curriculum breadth, where the repository
evidence says it matters.

### Two birth arms plus base

- **LINKED:** the four targets occur in their authentic causal sequence; the
  actual returned relation determines the next target.
- **UNLINKED:** the same four atomic target classes, counts, target-token mass,
  rendering families, and update tape are trained as independent local
  vignettes. It never shows a returned result controlling a later cue/action.
- **BASE:** no fit.

The UNLINKED child is the scientifically relevant sham. It answers the exact
question left by SEQ142/146: is co-residence of the atomic procedures enough,
or are connected examples needed? A command-card copy panel can remain as an
interface canary, but it should not be the sole comparison birth.

Before chain scoring, both LINKED and UNLINKED must pass balanced atomic probes
for SEEK, PROSPECT, CHECK, and CONTINUE/STOP and preserve the same generic
actor canaries. Then use the staged proposal's `32` held exact-text chain tasks
and causal-twin requirements. The interpretable patterns are:

- LINKED and UNLINKED both succeed: co-resident atoms are enough; use the
  simpler child and do not claim link training was necessary.
- LINKED succeeds and UNLINKED/base do not: connected training taught the
  missing junction.
- atomic probes pass but every arm fails chains: the missing object is still
  composition/interface, not storage.
- atomic probes fail: acquisition/dose failed; no chain conclusion.

Only after one combined child passes exact-text chains should the staged
same-adapter EVENT writer sentinel run. Only after that should the personal
memory factorial run. None of the eight old adapters, their inspected test
rows, PCFL material, GOAL-BRAID material, or their scored outputs enter this
birth lineage.

## Ruling

**Retain current Stages 0--1. Amend Stage 2 to a repeated 256-unit LINKED versus
UNLINKED `M-COMBINE-4` screen before the 1,024-unit broad birth.** Do not first
train a monolithic union of the eight legacy curricula. That union would spend
capacity on heterogeneous JSON worksheet contracts, import a known prediction
shortcut and three known canary harms, and still contain no causal skill
junction.

The minimum paper-relevant positive is not “one adapter scored eight fixture
labels.” It is:

> One target-disjoint birth adapter preserved four atomic transitions and,
> unlike an atom-matched unlinked adapter, used an actual returned relation to
> choose the next cue/action on held causal twins.

That result would justify the later same-adapter personal-memory test. It would
still be lab-taught composition—not parenting, self-learning, personal-memory
utility, lifetime improvement, or a whole flywheel.

