# Varied perception, the compiler as "real dream," and perception-as-MCTS

Date: 2026-09-12 UTC

Status: fresh adversarial design audit only. I changed no builder source,
benchmark, model, adapter, GPU job, or scientific result. This audit reads
Rohin's raw message 21, the SEQ-098--107 record, the existing DREAM/MCTS and
provenance designs, and the full Dream--LoRA--Think paper objective.

## Verdict

Rohin's intuition contains **three different hypotheses**, only one of which
is ready for a tiny writer experiment:

1. **Surface augmentation:** show one grounded relation in several faithful
   linguistic forms so that it can be retrieved under a new cue. This is
   technically meaningful and cheap. It is dataset augmentation, not yet
   perception or dreaming.
2. **Semantic re-perception:** revisit an episode to form distinct, useful,
   supported relations, contrasts, scopes, or predictions from the same
   evidence. This could be the paper's token-level DREAM compiler, but only if
   its new propositions are separately represented and provenance-bound. It
   is not proved by paraphrases.
3. **Goal-directed search over perceptions:** notice that a branch is
   repetitive or unhelpful, choose another interpretive or information-
   seeking branch, and allocate further work by expected value. This is at
   most MCTS-like unless the system actually has states, expansions, a value
   or selection rule, and backed-up outcomes. It belongs to the final
   objective, but the current evidence has not reached it.

The dangerous collapse is:

```text
one public event
  -> 1,000 model-written sentences
  -> count 1,000 "perceptions" or evidence items
  -> train on them
  -> call improved reproduction a connected dream
```

That is paraphrase oversampling plus self-distillation. It may improve the
geometry of a LoRA write, but it adds no evidence and proves no connected
knowledge, search, or learning-to-remember.

The right invariant is:

```text
epistemic support = unique public evidence roots
training dose      = optimizer-weighted presentations of derivative views
semantic breadth   = distinct supported propositions
```

Never substitute one of these quantities for another.

## What SEQ-098--107 actually licenses

The current data isolate dose and preservation, not varied perception:

- SEQ-098/099: one global `PREDICT`-before-`ACT` convention transfers in
  `3/3` optimizer seeds (`32/32` adherence in each taught arm, `0/32` in each
  control). The sixteen device--colour bindings remain unreliable
  (`4/7/3 of 16` taught versus `4/4/4` controls). A common response pattern is
  easier than keyed separation.
- SEQ-100: the device--colour failure remains on the exact training prompts.
  This is acquisition failure under that dose, not merely a paraphrase probe
  failure.
- SEQ-101: sixteen copies inside the same averaged optimizer updates do not
  increase effective binding-gradient encounters. Its null is a packaging
  result, not evidence against repetition or diversity.
- SEQ-102/104: direct competing `ACT`-only supervision replaces the global
  habit within sixteen updates at both `3e-5` and `1e-4`, in `3/3` seeds.
  The written behavior is plastic, not permanent.
- SEQ-105: twenty dedicated encounters per binding at rank 8 and LR `3e-4`
  acquire `14/16`, `16/16`, and `16/16` on both the exact and one alternate
  wording. Yet two of three descendants lose the action interface (`0/32`,
  `0/32`, `32/32`). This establishes that enough ordinary one-form dose can
  already carry the tiny binding set under two fixed cues. It **does not show
  that varied views are necessary**, and the alternate wording is not broad
  cue generalization.
- SEQ-106: two compatible global tag-order habits coexist with rehearsal at
  `32/32`; this is not input-conditional cognition.
- SEQ-107: simple mixing preserves the old habit and action at `32/32` while
  retaining `14/16` dev and `13/16` exact bindings; memory-only reaches
  `16/16` but loses the interface at `0/32`. Since the arms differ in memory
  dose and loss allocation, this shows a practical tradeoff, not causal replay
  necessity.

Therefore the next varied-view cell should answer one precise question:

> At a memory dose already known to acquire the facts, does faithful surface
> diversity improve fresh-cue extraction or binding specificity relative to
> repeated canonical views?

It must not be advertised as a test of semantic perception, a learned dream,
or MCTS.

## Which versions of the hypothesis are meaningful

| Candidate mechanism | Technically meaningful reading | What it cannot establish |
|---|---|---|
| Rephrase the same fact several ways | Cross-cue data augmentation; may shape a more accessible representation | New evidence, new knowledge, connectedness, or intelligent perception |
| Forward/inverse/prediction/contraindication views of one event | Several task-use interfaces to the same conditional, if each view is losslessly derived | Independent support; a compiler-generated inverse is not another observation |
| Different goal-conditioned readings of one episode | Semantic re-perception if each reading identifies a distinct supported relation that changes a later decision | MCTS or learned allocation unless the child chooses among readings and pays a budget |
| Cross-episode contrast or link | Connected synthesis if it cites distinct public roots and link intervention redirects action | Truth merely because the model repeated it; support counts cannot be inflated by derived views |
| Hypothesis plus later test | Real prospective DREAM edge if proposal precedes the public outcome and confirmation is ordinary experience | A fact at proposal time; positive training before support |
| Offline branch search over existing evidence | Goal-directed interpretive search; potentially useful DREAM | New information acquisition; all leaves remain functions of existing evidence |
| Branch that requests a new world action | Active perception / expansion: the branch can add a new public evidence root | Safe planning unless cost, stopping, stale-policy error, and false proposals are measured |
| Hidden-state or latent transformation | A possible future learning architecture | Anything testable by the current text compiler, provenance ledger, or ordinary LoRA recipe |

The phrase **"compiler as the real dream"** is defensible for the token-level
system only when DREAM is an offline, child-authored proposal process over
public episodes, rather than a fixed renderer. The trainer may remain ordinary
LoRA SFT. The novelty then lies in how the child revisits evidence and forms
useful supported structure. If an experimenter predefines every lens and
relation, the result is a strong compiled-data ceiling, not a learned dream.

## Provenance and false-memory hazards

### One root stays one root

Every derivative must retain one or more immutable public `event_id` roots.
Ten paraphrases of one event have training multiplicity ten and epistemic
support one. A cross-episode relation citing roots A and B has support set
`{A,B}`; a paraphrase of that relation does not create C. Statistical
uncertainty is clustered at the unique-root or life level, never at the view
level.

### Use separate semantic statuses

At minimum, keep these distinct:

- `ROOT`: a public action, observation, or outcome;
- `REEXPRESSION`: a semantics-preserving view of an existing proposition;
- `DERIVATION`: a new proposition with cited roots/parents and an auditable
  derivation rule;
- `HYPOTHESIS`: a prospective claim not yet supported;
- `SUPPORTED` / `CONTRADICTED`: status produced only by later public evidence.

A re-expression receives no new support. A derivation inherits the union of
its roots, not the number of routes by which the same model re-derived it. A
hypothesis must not enter positive memory training merely because several
correlated generations agree.

### Correlated generations are not a jury

Sampling the same checkpoint 1,000 times from nearly the same prompt produces
correlated errors. Majority vote, agreement, or semantic clustering can
increase confidence in a shared hallucination. Distinct decoding seeds,
phrases, agents, or branches are not independent evidence unless they consume
distinct external evidence roots.

### Selection can smuggle in an oracle

Generate-many-and-keep-the-correct-ones is rejection sampling. If correctness
is judged with hidden task truth, the verifier—not the child—supplies the
information. For the causal DREAM path, proposals seal before their later
public tests, and only ordinary outcomes may change status. A hidden solver may
score after sealing, but cannot choose what enters the child's experience.

### False memories are amplified more efficiently too

View diversity is epistemically neutral. It can make a wrong binding more
extractable just as efficiently as a true one. The system therefore needs
authentic, binding-shuffled/deranged, contradiction, and unsupported-hypothesis
controls. “The model remembers it under many cues” is not evidence that it was
true.

### Recursive DREAM can launder its own derivatives

If a derivative becomes the sole source for later derivatives, one error can
grow a large apparently connected graph. Preserve the full acyclic provenance
DAG, cap unsupported derivative depth, carry contradiction forward, and score
precision against unique roots. Repeated derivation can justify training dose,
not support count.

## Is “perception as MCTS” more than a metaphor?

It is a useful design metaphor, but it is not MCTS merely because the model
writes branches.

A minimally real search process needs:

1. **State:** the current evidence, interpretation graph, goal, uncertainty,
   and remaining budget.
2. **Actions:** revisit, reframe, follow a relation, contrast, backtrack, ask
   for a new observation, or stop.
3. **Expansion:** create a genuinely distinct proposition or execute an
   information-gathering action—not another synonym.
4. **Selection value:** expected downstream gain or information value minus
   token/action cost, with a novelty or visit term.
5. **Outcome/back-up:** later public outcomes update which branches were
   useful; stale values are recomputed as the policy changes.
6. **Goal counterfactual:** the same evidence under two goals must select or
   traverse different branches.

Without rollouts and backup, call it **goal-directed prioritized branching**
or **MCTS-like memory access**, not MCTS. That is still meaningful. The core
test is behavioral: does branching find supported, decision-relevant structure
and stop when more branches have negative value? More prose, more nodes, or
lower lexical similarity are not success.

Rohin's “same thought again -> change the behavior / add a new perception” is
best implemented first as a falsifiable routing rule:

```text
if the next candidate has the same canonical proposition identity,
do not count a new semantic branch;
either request a different relation to the goal, seek new evidence, or stop.
```

The canonical-identity mechanism is scaffolding. A later parented child must
learn when to invoke it and when repetition is actually valuable.

## What language-level compilation can and cannot test

Language-level DREAM is sufficient to test:

- whether surface diversity improves exact versus fresh-cue extraction;
- whether a child can author distinct supported relations from public
  action--outcome records;
- whether cross-episode links survive into LoRA and causally redirect later
  goal-conditioned action;
- whether a routed branching process outperforms equal-token fixed lenses or
  paraphrases;
- whether new public outcomes revise or retract old hypotheses; and
- whether the same semantics work in explicit text before LoRA transport.

It cannot establish:

- a latent-space or biologically analogous sleep mechanism;
- unconscious processing, phenomenology, or human hippocampal equivalence;
- learned compiler intelligence when the experimenter supplies all lenses,
  links, priorities, and stop decisions;
- physical compression merely because the text is shorter or the carrier is
  low-rank;
- new knowledge from offline replay alone; or
- independent evidence from multiple wordings of one event.

This is not a reason to move to latent space now. Token space is the only
current route with inspectable provenance and an ordinary trainer. A latent
compiler is a separate algorithm that needs its own readout, intervention, and
false-memory audit.

## Smallest immediate falsifier: `VIEW-0`

Do this only after the conditional writer primitive is qualified; otherwise a
failed view test is uninterpretable. Reuse the tiny sixteen opaque bindings
because SEQ-105 established a successful dose there.

### Fixed factors

- 16 balanced opaque keys and balanced labels;
- 20 effective optimizer encounters per binding, distributed over distinct
  updates—not duplicates averaged inside one update;
- identical total supervised target tokens, optimizer updates, rank, LR,
  initialization, preservation loss, key frequency, label frequency, and
  context-length distribution;
- common fresh evaluation cues and itemwise paired scoring.

### Four cells

| Cell | Corpus |
|---|---|
| `AUTH-REPEAT` | One canonical faithful form repeated across the 20 effective encounters |
| `AUTH-VIEWS` | Five faithful, independently held templates x four encounters; the stable opaque key and full binding appear in every view |
| `DERANGED-REPEAT` | Same dose, but one prospectively fixed complementary/binding-shuffled map |
| `DERANGED-VIEWS` | Same surface diversity, carrying the identical deranged map |

Do not use free model prose in this first cell. Mechanically generate
semantics-preserving views so the test isolates representation geometry rather
than compiler quality. Score:

1. exact trained-form binding accuracy;
2. at least four unseen cue families, including inverse/reversed and
   distractor-bearing forms;
3. both-class recall, itemwise margins, and complement flips;
4. wrong-key and wrong-condition specificity;
5. inherited interface/habit retention and spill; and
6. adapter-OFF plus seed-matched roots.

The primary contrast is the paired fresh-cue change
`AUTH-VIEWS - AUTH-REPEAT` at equal dose. The DERANGED pair measures whether
diversity is simply an equally good amplifier of false bindings, as it should
be if it only changes extractability.

### Outcome interpretations

| Result | Maximum interpretation |
|---|---|
| Both AUTH cells fail exact form | Writer/objective not qualified; no view conclusion |
| Both pass exact; VIEWS improves unseen cues and specificity | Faithful surface augmentation improves cross-cue extraction for this LoRA writer |
| Both pass and are equivalent on unseen cues | Diversity is unnecessary at this dose/scale; repeated effective encounters suffice here |
| VIEWS improves exact only | Optimization/format benefit, not extractability |
| VIEWS raises correct and wrong-key firing together | Stronger global habit or spill, not selective memory |
| DERANGED-VIEWS learns its wrong map as well as AUTH-VIEWS learns truth | Diversity is an epistemically neutral carrier amplifier; provenance remains essential |
| AUTH improves but DERANGED does not under otherwise symmetric material | Investigate hidden prior, leakage, scorer asymmetry, or unmatched corpora before any positive claim |

`VIEW-0` is deliberately a storage/extraction falsifier. Passing it justifies
using varied renderings in SLEEP. It does not validate “perception as MCTS.”

### Minimal controls for Astra's current `SINGLE_VIEW` versus `FOUR_VIEW`

Astra's proposed fixed-question pair is a useful cheaper precursor to the
four-cell `VIEW-0`. Its exact estimand is:

> Does training on four fixed faithful question phrasings of each binding
> improve binding recall under unseen question wording relative to repeating
> one fixed question phrasing at the same effective dose?

It needs these controls before its result is interpretable:

1. **Separate optimizer encounters.** Scatter each source's four appearances
   across separate, seed-paired optimizer steps in both arms (batch size 1 is
   the clearest implementation). Do not place all four same-source rows in one
   mean-loss batch. Otherwise `SINGLE_VIEW` nearly collapses four identical
   gradients into one while `FOUR_VIEW` averages four different gradients;
   the result is within-update gradient geometry, not repeated replay.
2. **Equal effective dose.** Match source-specific optimizer steps, label+EOS
   target tokens, total updates, rank, LR, initialization, replay/preservation
   objective, and source/label frequency. Report both raw presentations and
   distinct optimizer steps per source. Different prompt/context token counts
   may remain part of the view intervention, but must be disclosed rather than
   called compute-matched.
3. **Same immutable truth.** All views of a key must carry the identical
   prospectively bound source label and the same `event_id`. Four phrasings
   remain one evidence event. No model-generated semantic additions belong in
   this lexical test.
4. **No evaluation-template overlap.** Freeze at least one exact/canonical
   readout and several unseen cue families before fitting. None may be a train
   template with cosmetic punctuation changes. Include reversed/inverse and a
   distractor-bearing query if the tokenizer audit keeps the answer surface
   matched.
5. **Binding specificity, not aggregate color preference.** Keep labels
   balanced; score per-key correctness, every-label recall, raw gold-versus-
   competitor margins, and complement/wrong-key flips. A constant color is
   chance (`4/16`) and fails even if aggregate output validity rises.
6. **Shared parent and OFF controls.** Both arms fork the exact same warm-start
   adapter with a fresh optimizer and named paired stochastic streams. Probe
   that parent/OFF state on the same inputs, and retain the old
   behavior/interface panel so a memory gain cannot hide another `0/32`
   interface loss.
7. **Fail-fast interpretation order.** First require exact trained-form
   acquisition in both arms. Only then may a `FOUR_VIEW` advantage on unseen
   cues be called lexical extraction robustness. If only `FOUR_VIEW` acquires
   the exact map, the result is a diversity-assisted acquisition/optimization
   effect. If neither acquires it, the writer failed and the view hypothesis
   remains untested.
8. **Replication unit.** Sixteen bindings and their prompt variants are paired
   items, not independent learners. Treat seed 0 as a gate and replicate a
   surviving contrast over fresh optimizer/root seeds before reporting a
   robust view effect.

The minimal current pair does **not** need a free-form child compiler, semantic
links, or MCTS machinery. Adding those would destroy localization. It would be
valuable to add the deranged pair later, but it is not required to answer the
current narrow lexical-robustness question if balanced per-key and wrong-key
specificity checks pass.

**Claim boundary:** even a perfect `FOUR_VIEW > SINGLE_VIEW` result tests fixed
lexical augmentation authored by the experimenter. It does not test varied
perception in Rohin's stronger sense, because the child did not choose what
else to notice, form a new supported relation, compare branches, seek evidence,
or learn when to stop. Call it a **fixed multi-view storage/extraction
scout**, never “perception as MCTS” or “the real dream.”

## Smallest falsifier of the stronger real-DREAM claim: `DREAM-BRANCH-0`

After `VIEW-0` and the conditional writer gate, use a tiny typed causal world
with 24 public action--outcome bundles. Each bundle has:

- two immutable evidence roots that can support one two-hop relation;
- one matched distractor root;
- two counterfactual goals that require different first actions; and
- no model-visible hidden rule, answer, proof, or score.

Give the same frozen child and equal generated-token budget to:

1. `PARAPHRASE`: re-express source atoms only;
2. `FIXED-LENSES`: the experimenter requests a fixed menu of relation views;
3. `SELF-BRANCH`: the child chooses `FOLLOW`, `CONTRAST`, `BACKTRACK`,
   `SEEK-EVIDENCE`, or `STOP`, while duplicate canonical propositions do not
   count as expansion.

For every authored proposal, seal it before any confirming outcome. Build the
same three semantic carriers from each proposal pool:

- `AUTH-LINK`: publicly supported link;
- `NO-LINK`: equal atoms, bytes, and dose but the link is absent;
- `DERANGED-LINK`: equal atoms and dose with the link redirected.

First test all carriers as explicit text through the same reader. Only if the
text lane works, transport the identical admitted semantics through LoRA. The
gates are:

- unique-root-clustered supported-proposition precision and coverage;
- no rise in unsupported or contradicted memory;
- both goals redirect first action in the registered direction;
- cutting the authentic link or substituting the deranged link removes or
  redirects the credited action while a matched sham cut does not;
- SELF-BRANCH improves the action/information-gain frontier over FIXED-LENSES
  and PARAPHRASE at equal generated tokens; and
- stopping avoids useless expansion when source atoms are already sufficient.

### Stronger-test interpretations

- `FIXED-LENSES > PARAPHRASE`, but `SELF-BRANCH ~= FIXED-LENSES`: structural
  compilation helps, but the search policy is supplied by the experimenter.
- `SELF-BRANCH > FIXED-LENSES` with authentic-link mediation and goal flips:
  bounded evidence for child-routed, goal-directed offline semantic DREAM.
- All three carriers work in explicit text but fail in LoRA: compiler works;
  parametric transport fails.
- LoRA and text both work, but AUTH/NO-LINK/DERANGED interventions do not
  redirect action: a generic policy or cue shortcut explains the gain; no
  connected-memory claim.
- Branching produces more unsupported propositions or only lexical novelty:
  the proposed “real dream” is confabulatory self-distillation at this scale.
- An active `SEEK-EVIDENCE` branch later causes a new public root and improves
  a sealed action: active expansion is supported. Offline rewording alone can
  never earn that statement.

## Relation to the full paper objective

These small tests do not replace the full goal; they protect it from an easy
but wrong surrogate. The complete sequence remains:

```text
qualified conditional writer
  -> VIEW-0: extractable grounded representations
  -> DREAM-BRANCH-0: child-authored supported links and goal routing
  -> own action/outcome -> DREAM -> SLEEP -> sterile later action
  -> OLD+NEW retention and contradiction repair across sleeps
  -> parent-deleted H1
  -> continued-SLEEP lifetime H2
  -> strong evolving text/graph/program/TMEM-style baselines
```

The paper-worthy insight is not that “many phrasings help.” It is the possible
transition from **externally compiled views** to a child that allocates its own
offline perception, forms supported structure, knows when another branch is
worth the cost, and turns the resulting experience into better future action.
The experiments must keep those stages separate so the final claim, if it
passes, is actually about Dream--LoRA--Think rather than a large synthetic SFT
corpus.

## Recommendation

1. Treat varied views as a **representation/dose knob**, not a settled memory
   law. SEQ-105 already shows they are not necessary for the tiny two-cue
   binding endpoint.
2. Run the smallest equal-dose `VIEW-0` only after the conditional writer
   qualifies. Do not spend on 1,000 free-form views first.
3. Preserve unique-root, derivative-view, and unique-proposition counts as
   separate columns in every compiler receipt.
4. Keep the first view deck mechanical. A later child-authored deck is a new
   experiment whose failure can then be assigned to DREAM quality rather than
   the LoRA writer.
5. Use explicit text as the first oracle for every connected semantic object;
   LoRA is the transport comparison. If text fails, more parametric training
   cannot rescue the claim.
6. Reserve “MCTS” for the later routing test; use “MCTS-like prioritized
   branching” until selection, expansion, outcome backup, goal flips, and
   learned stopping are all measured.

## Internal evidence read

- `research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, messages 20--21.
- `research_loop/COORDINATION.md`, SEQ-098--107 and watcher adjudications.
- `research_notes/astra_memos/ASTRA_FUNDAMENTAL_SEED0_TERMINAL_2026-09-12.md`.
- `research_notes/astra_memos/ASTRA_FUNDAMENTAL_REPLICATION_TERMINAL_2026-09-12.md`.
- `research_notes/astra_memos/receipts_20260912/astra_memory_only_result_review_20260912.md`.
- `research_notes/astra_memos/receipts_20260912/astra_memory_replay_seed0_review_20260912.md`.
- `research_notes/astra_memos/receipts_20260912/astra_two_habit_result_review_20260912.md`.
- `research_notes/analysis/2026-09-12_knowledge_storage_extraction_paper_implications.md`.
- `research_notes/10_world_models_value_mcts.md`.
- `research_notes/26_fact_salience_design.md`.
- `research_notes/32_v2_experiment_design.md`.
- `research_notes/56_pcfl_compression_feasibility_adjudication_v1.md`.
- `research_loop/advisory/20260903_rml_paper_experiment_v1.md`.
- `research_loop/advisory/20260909_learnability_bootstrap_lineage_scale_fresh_attack_v1.md`.
