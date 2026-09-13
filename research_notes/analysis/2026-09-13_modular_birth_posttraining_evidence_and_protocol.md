# Modular birth post-training: evidence and minimum experiment

**Date:** 2026-09-13
**Scope:** design and literature audit only; no implementation, model execution,
training, GPU use, or scientific claim
**Terminology:** **trained** means weights changed on researcher-prepared or
researcher-selected material. **Learned** means the child prepared the material
from its own experience. **Self-learning** is the autonomous learned case. A
birth adapter made from demonstrations or context distillation is therefore
*trained*, even if the frozen child generated some of the target continuations.

## Bottom line

Do not make one large corpus called “thinking.” Build a small set of behavioral
birth modules, test each module in isolation, and retrain one combined birth
from clean base using only the modules that pass both their own probe and the
other modules' probes. The mechanism should be ordinary response-masked SFT.
For the main data recipe, let an instruction/anchor elicit the desired behavior
on a concrete state, remove that help, and train the child to produce its own
successful continuation. This is standard context distillation, not a new
writer.

The minimum comparison is:

1. no birth;
2. lived-heavy birth: verified whole episodes;
3. structure-heavy birth: abstract explanations and idealized thinking flows;
4. context-distilled birth: state-to-thought/action continuations that were
   first elicited with help, then trained without the help.

Match these by source situations and supervised response tokens, not by row
count. Use unrelated microdomains and hold out whole microdomains, not merely
new names. This tests whether the child learned a task grammar rather than the
surface grammar of one nursery.

The birth is successful only if it changes *when and how* the child uses a
behavior, survives removal of the training anchor, and does not damage other
skills. Producing more planning words is not sufficient.

## What the repository has established so far

### 1. A prompt can repair format without teaching perception

The no-fit perception anchor changed strict score from 0/12 to 10/12, but the
unanchored model's twelve outputs were fenced correct-looking JSON. After the
descriptive fence repair, 11/12 unanchored outputs were semantically supported
versus 10/12 anchored. Eleven paired decisions were identical and the anchor
worsened one case. The anchor was an interface intervention, not evidence that
perception content improved.

### 2. A tiny fit can make that output routine prompt-independent

The first perception-only fit produced 11/12 strict correct without the anchor,
compared with base 0/12 without it; the fit trained with the anchor produced
10/12 without it. This is useful Level-1 evidence that a small behavioral SFT
can install the record-producing routine. It is still **trained**, single-seed,
and narrow-family evidence. It does not show downstream learning or a general
perception disposition. Replication seeds were still live when this memo was
written.

### 3. The first combined birth installed routines but not reliable selection

The source-authored 256-row birth reached 32/32 on the prospective routine and
58/64 on revision, but only 26/32 on the expected/observed/prior locality twins
(predeclared gate 29/32). The deranged control was also strong on several direct
readouts. Addition slipped to 15/16. This shows that a LoRA can memorize the
requested output policies, but it has not yet shown that it selects them for
the right states or preserves unrelated behavior.

### 4. Prompt grammar can conceal or manufacture a birth effect

On the original RuleGame probe, OFF scored 8/16 and AUTH 5/16 on the public
contract. Clarifying the response grammar made all outputs parse and moved the
same comparison to OFF 12/16 and AUTH 13/16. The remaining AUTH advantage was
narrow (revision 4/4 versus 2/4) and accompanied by a record error (3/4 versus
4/4). Exact-format and semantic scores must remain separate.

### 5. Downstream benchmark exposure permanently contaminates a birth lineage

Any child that has played CompilerGym cannot be used as a clean childhood
checkpoint for a later CompilerGym comparison. Birth and nursery material must
come from unrelated microdomains. Deployment must fork from a hashed clean
checkpoint with zero downstream episodes, labels, identifiers, pass names, or
repo-derived solutions in its provenance.

These observations support modular screening. They do not support adding more
complex cognition machinery.

Repository evidence used above:

- `research_notes/astra_memos/receipts_20260912/astra_perception_anchor_raw_analysis_20260913.md`
- `research_notes/analysis/2026-09-13_perception_fit_result_blind_audit.md`
- `research_loop/COORDINATION.md`, SEQ-128 seed-0 collection
- `research_notes/astra_memos/ASTRA_BIRTH_COMPONENT_RESULT_2026-09-13.md`
- `research_notes/analysis/2026-09-13_birth_protocol_probe_raw_audit.md`
- `research_loop/coordination/20260910_compilergym_bootstrap_quarantine.md`
- `research_notes/analysis/2026-09-12_level1_birth_disposition_fresh_audit.md`

## What the primary literature actually licenses

### Varied exposures make stored information more extractable

Allen-Zhu and Li show that exact training text can be memorized yet unavailable
to a differently phrased query. In their synthetic-biography setting, using
five diverse biographies per person (different wording and shuffled sentence
order) raised held-person question answering from 9.7% to 96.6%. A single
permutation could hurt; diversity, not mechanical duplication, was the lever.
This was a controlled pretraining study, not a LoRA continual-learning result,
so it is a data-design prior rather than direct validation of our writer.
([paper](https://arxiv.org/abs/2309.14316))

### Context-conditioned behavior can be distilled into unconditioned behavior

Snell, Klein, and Zhong generate an answer (and, where useful, a scratchpad)
with rich instructions or demonstrations, then train the same model to produce
it from the reduced input. Across their ten-task instruction experiment, the
context-conditioned teacher scored 43.4 ROUGE-L, the undistilled student 9.0,
and the distilled student 34.7. On SPIDER, context distillation scored
22.1/27.9 with four/eight demonstrations versus 13.4/18.9 for direct gradient
descent. Their addition experiment also transferred partially to a related
synthetic task. These are demonstrations that context can serve as temporary
scaffolding whose behavioral effect is compiled into weights; they are not
evidence that arbitrary meta-cognitive prose will become a general disposition.
([paper](https://arxiv.org/abs/2209.15189))

The same paper mixed 10,000 distillation items with 65,536 Natural Instructions
examples, and sequential distillation could overwrite associations. That
supports preservation replay, while giving no universal replay ratio for our
model or adapter.

### Selection works when the selector is tied to an external answer or reward

STaR iteratively generates rationales, keeps those that lead to correct
answers, and rationalizes failed examples using the answer before retraining
without the hint. Rejection Sampling Fine-Tuning similarly samples multiple
outputs, ranks them with a reward model, and fine-tunes on selected outputs.
These methods justify generating several candidate continuations and retaining
the grounded ones. They do **not** justify selecting fluent introspection with
another model's taste alone.
([STaR](https://arxiv.org/abs/2203.14465),
[RAFT](https://arxiv.org/abs/2304.06767))

DPO offers a direct preference-classification objective without first fitting
a separate reward model. It is appropriate only once a state has two valid,
meaningfully ranked candidate behaviors. Using it in the first birth would
confound data form and objective form, so the first comparison should keep SFT
fixed. If the SFT child later exhibits valid but badly allocated deliberation,
world- or cost-grounded chosen/rejected pairs become a narrow DPO follow-up.
([paper](https://arxiv.org/abs/2305.18290))

### Task diversity is a direct defense against nursery-specific imitation

FLAN instruction-tuned on more than sixty tasks and evaluated held-out task
types, finding benefits from the scale and diversity of instruction-tuning
tasks. The relevant lesson is modest: a claimed task grammar needs multiple
training families and whole-family holdouts. One opaque-rule game is not a
generality test. ([paper](https://arxiv.org/abs/2109.01652))

### Replay protects old behavior; it must not silently reduce the new dose

Experience replay with behavioral cloning reduced forgetting across continual
RL tasks. InstructGPT mixed pretraining-distribution data into PPO (“PPO-ptx”)
to reduce capability regressions without erasing preference gains. SDFT uses
model-generated data closer to the base distribution to mitigate forgetting
during fine-tuning. These support a native-behavior replay control, not a claim
that any particular mixture is optimal here.
([experience replay](https://arxiv.org/abs/1811.11682),
[InstructGPT](https://arxiv.org/abs/2203.02155),
[SDFT](https://arxiv.org/abs/2402.13669))

### Native/on-policy continuations are preferable when feasible

On-Policy Context Distillation trains on the student's own unconditioned
prefix distribution while matching the context-conditioned teacher. In the
reported Qwen2.5-7B experiments it outperformed off-policy context distillation
on system-prompt and text-game tasks and better preserved out-of-domain
behavior. This makes native child prefixes a good data choice. It does not mean
we should implement a new reverse-KL trainer before the ordinary SFT baseline
exists: OPCD changes the optimization objective and belongs behind a diagnosed
off-policy/exposure-bias failure.
([paper](https://arxiv.org/abs/2602.12275))

Online Experiential Learning independently reports the same two high-level
pressures in an iterative deployment setting: extracted experiential knowledge
outperforms raw trajectories, and on-policy consistency between the knowledge
source and learner matters. OEL uses a different whole-model procedure and is
evidence for the comparison, not evidence that our LoRA implementation works.
([paper](https://arxiv.org/abs/2603.16856))

The current literature therefore points to a conventional recipe: varied
concrete demonstrations, external selection, native formatting, response-only
loss, and explicit replay. Preference optimization is a later knob if the
child has learned valid alternatives but allocates thought badly; it should not
be mixed into the first writer comparison.

## The minimum modular birth

The birth should install four conditional task grammars. “Conditional” is the
important word: each module includes states where the behavior should occur and
matched states where it should not.

### M0 — record discipline (interface prerequisite)

**Behavior:** keep observation, prior prediction, and later outcome separate;
do not invent a prediction after seeing the result; emit the required native
record without wrappers.

**Why separate:** the existing perception fit says this routine is easily
trained, while the no-fit anchor says much of the apparent gap can be format.
M0 is an interface prerequisite unless multi-seed results demonstrate a
binding-specific semantic gain.

**Probe:** exact-format score and semantic field score, reported separately;
supported record versus underspecified observation; withheld whole rendering
family; no forbidden fields when evidence is absent.

### M1 — prospective experiment choice

**Behavior:** when uncertain, name a small hypothesis set, make a falsifiable
prediction, and choose an action that distinguishes likely hypotheses. When
evidence is sufficient, commit instead of manufacturing another test.

**Probe:** matched uncertain/sufficient pairs; informativeness of the chosen
action computed by the microdomain; prediction made before the outcome; correct
STOP on sufficient-information cases. Rewarding “more thoughts” would fail the
negative half of this probe.

### M2 — evidence-weighted revision and scope

**Behavior:** compare prediction with outcome, revise the implicated belief,
preserve unrelated beliefs, and skip duplicate or uninformative evidence.

**Probe:** KEEP/REVISE twins with one changed relation and one unrelated
relation; surprise/no-surprise pairs; old-belief retention; scope precision.
The output must name what changed, what stayed, and which observation warrants
the change.

### M3 — deliberation and state-transition control

**Behavior:** given a goal, current state, and generous budget, choose whether
the next useful unit is THINK, ACT, or STOP; create a subgoal and stopping rule;
after completing it, construct the next state instead of terminating the whole
life.

**Probe:** matched cases differing in one of: missing information, reversible
action availability, action latency, or completed subgoal. Score the chosen
transition and subsequent action outcome. Log token use only as a diagnostic;
the test should provide enough tokens that neither thinking nor action is
artificially starved.

### M4 — supplied-memory use and connection

**Behavior:** from a small target-blind supplied memory, retrieve the relevant
items, connect only supported relations, identify a missing edge, and ask or
act to fill it. Do not dump every memory or infer an unsupported bridge.

**Probe:** relevant/irrelevant memory twins; composable versus non-composable
sets; a case whose best action is retrieval, one whose best action is a new
experiment, and one with enough evidence to act. This teaches how to use a
memory substrate without giving the child any downstream benchmark memory.

M0 may already be ready to pool after replication. M1–M4 should be fitted and
screened separately. Do not include a module merely because its training loss
falls.

## Data construction: four matched births

Use four unrelated microdomain families, for example opaque Boolean machines,
route/map search, small scheduling/resource problems, and object-transforming
causal boxes. Each module trains on at least three families and holds out one
entire family. Names, rules, and outputs must be generated independently of the
deployment benchmark. The final provenance scan should show zero CompilerGym
program names, optimization passes, rewards, or copied repo solutions.

Freeze the same underlying states for all four arms.

### OFF — no birth

The exact base checkpoint and ordinary agent bootstrap. This establishes how
much of each task grammar pretraining already supplies.

### LIVED — lived-heavy

Whole, verified successful and recovered episodes in the child's native chat
and tool dialect. Include the action, real outcome, and the child's committed
continuation. Do not include parent commentary as a target. This controls the
idea that ordinary good experience is sufficient.

### STRUCTURE — structure-heavy

Abstract principles, plans, reviews, and idealized meta-cognitive flows about
the same underlying situations. Keep the supervised response-token dose equal
to LIVED and CD. This controls “reading about thinking.” Existing Phase-0
results predict it may reproduce prose without changing state-conditioned
action, which is precisely why it belongs in the comparison.

### CD — context-distilled behavior

For every frozen state `x`:

1. Give the frozen child `x` plus a short module anchor or demonstration `c`.
2. Sample four native continuations. A checker using the environment and the
   module contract grades the action and state transition. A stronger model may
   diagnose but does not get to replace world truth.
3. Retain up to two correct, semantically distinct continuations. Preserve
   failures as matched contrasts only when their wrongness is externally
   decidable.
4. Train the clean child on `x -> retained continuation`, with `c` removed and
   loss only on the response tokens.
5. Re-render stable relations in four surface/order variants. Cap near
   duplicates and per-domain contribution so easy families cannot dominate.

This compiles the *effect* of temporary help into state-conditioned behavior.
The parent/anchor text stays out of both training input and target. The child
must later produce the behavior without it.

If the frozen child cannot generate enough correct continuations, record the
shortage. A teacher-authored fallback is a distinct dataset and arm, not an
invisible repair.

### Replay mixture

Add native, unrelated capability/interface replay on top of the fixed new-skill
dose; do not substitute replay for new-skill tokens. For the first comparison,
use one fixed ratio—recommended pilot: one replay response token for every two
new-skill response tokens—because the repository has not established an
optimum. Hold this ratio constant across LIVED, STRUCTURE, and CD. The replay
set should cover ordinary instruction following, native tool syntax, concise
answers, addition/copy canaries, and explicit abstention. If locality still
fails, test 1:1 replay as a single follow-up rather than starting a broad sweep.

Retrain cumulative births from the same clean base. Do not average LoRA
weights, and do not continue from a failed module fit.

Keep rank 8 fixed during module and data-family screening because it is the
current tested low-capacity writer and changing rank would add a second causal
axis. Scale rank only after a selected corpus shows a capacity limit at fixed
dose; birth-recipe selection should not be mixed with a rank sweep.

## Probe matrix and stopping rules

### Stage A — no-fit headroom screen

Before training a module, run its held-out panel with and without the temporary
anchor. Use 32 paired cases: 16 where the behavior is warranted and 16 where it
is not. If the anchor changes only exact formatting and not semantic decisions,
classify the module as an interface routine or redesign the states; do not spend
a full birth run claiming semantic headroom.

### Stage B — isolated module screen

Fit one CD adapter per eligible module from clean base. A practical pilot is 64
unique training states per module, four render/order forms per state, with the
same supervised-token dose and replay rule for all modules. Evaluate every
adapter on every module panel, not only its own:

| fitted adapter | M0 | M1 | M2 | M3 | M4 | generic/interface |
|---|---:|---:|---:|---:|---:|---:|
| OFF | baseline | baseline | baseline | baseline | baseline | baseline |
| M0 | own effect | spill | spill | spill | spill | locality |
| M1 | spill | own effect | spill | spill | spill | locality |
| … | … | … | … | … | … | … |

One seed selects feasibility, not a paper result. A module advances only if:

- the anchor-absent semantic probe gains at least 8/32 paired decisions over
  OFF on its own panel;
- neither the warranted nor the unwarranted half worsens;
- no other module or generic panel worsens by more than 0.05 absolute;
- native action/record syntax and forbidden-output canaries pass; and
- the effect is not explained by a parser repair or longer output.

The 8/32 threshold is a screening rule chosen to avoid promoting tiny effects,
not a significance claim. Report the exact paired counts regardless.

### Stage C — data-family comparison

Pool only the passed modules and retrain three clean-base births: LIVED,
STRUCTURE, and CD. OFF remains unchanged. Match underlying states, new-skill
response tokens, replay tokens, update steps, rank, and optimizer settings.
This is the direct answer to “what should birth contain?”

After a winner exists, add one active control: permute state-to-continuation
bindings within each module while preserving the target-text multiset. If the
permuted adapter retains the gain, the effect is style/ritual rather than the
conditional task grammar.

### Stage D — integrated parent-free exam

Give each birth fresh held-domain tasks with an empty active context and no
anchor or parent. Primary outcomes are externally scored actions, information
gained, state transitions, and solved tasks. Thought markers are mediators:
they explain an action difference but do not replace one.

### Stage E — first actual learning test

Freeze the winning **trained** birth. On a new opaque microdomain, compare:

- `PROMOTE`: world-grounded child-generated sleep rows may update the adapter;
- `SHADOW`: identical life and sleep compilation, but the update is not loaded.

The birth itself is not the self-learning result. A better parent-absent
learning curve for PROMOTE is the first evidence that the trained task grammar
helps the child **learn** from its own experience. Re-probe M0–M4 after the
learned sleep to test retention.

## Information per GPU-hour

Do not run a factorial sweep over ranks, learning rates, data families, and
modules at once.

1. **CPU/source checks:** provenance, semantic/exact scorers, paired state
   identities, target-token counts, and contamination scans.
2. **No-fit screens:** five modules × 32 cases × anchor absent/present = 320
   short generations. This can eliminate modules before any fit.
3. **Isolated one-seed fits:** one fit per eligible module, followed by the full
   cross-module probe matrix. The cross-impact matrix is more informative than
   three ranks on one module.
4. **Data-family pilot:** only after modules pass, fit LIVED/STRUCTURE/CD once
   each. Add the permuted control only for the winner.
5. **Confirmation:** replicate only OFF, the selected birth, and its active
   control across three independent training seeds. Do not replicate every
   discarded arm.
6. **Level-2 learning:** spend the long horizon only after direct behavior,
   selectivity, locality, and retention have passed.

The repository's recent small birth fits and short readouts completed on the
scale of tens of A40-minutes per exploratory comparison, so the no-fit and
isolated-fit screen should cost hours, not days. That is only a planning
estimate: bind the actual GPU cap after the native runner forecasts tokens and
measures one fit. The expensive run should be the three-seed integrated
confirmation and subsequent PROMOTE/SHADOW learning comparison, not recipe
discovery.

## Decisions this design resolves

- **Does birth need whole lives?** LIVED versus CD answers this with matched
  situations and supervised-token dose.
- **Does reading about thinking work?** STRUCTURE versus CD distinguishes
  abstract imitation from state-conditioned behavior.
- **Does temporary scaffolding compile?** CD is evaluated after the anchor is
  fully removed.
- **Did the adapter learn a conditional mapping or merely a style?** The
  permuted state-target control answers this.
- **Did the child learn?** Only the later PROMOTE/SHADOW slope and retention
  test use that word.
- **Should we change the trainer?** Only if ordinary response-masked SFT passes
  exact reproduction but repeatedly fails free-generation or preservation.
  OPCD, preference optimization, or another objective then targets a diagnosed
  failure instead of becoming unexplained complexity.

## Recommendation

Use the perception slice as M0 if its remaining seeds replicate. Build no
monolithic birth yet. Screen M1–M4 using context-distilled, native
state-to-continuation SFT and the full cross-module probe matrix. Then compare
OFF/LIVED/STRUCTURE/CD on the pooled passed modules and carry only the winner
into the first long PROMOTE/SHADOW life.

This is enough to test the bootstrap idea without pretending to solve
parenting. Birth supplies a small meta-cognitive task grammar; parenting gives
live, richer guidance; sleep later turns the child's own grounded experience
into learned memory. The scientific boundary stays clean:

> birth is trained readiness; the life is where learning must be demonstrated.
