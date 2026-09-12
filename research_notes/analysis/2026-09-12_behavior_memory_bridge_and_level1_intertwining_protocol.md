# Why the habit formed, why the facts did not, and the smallest level-1 bridge

**Date:** 2026-09-12
**Status:** scientific decision memo only. This memo changes no builder code,
launches no job, and does not authorize an architecture change.

## Decision in one minute

The completed result is not evidence for separate behavior and memory
adapters. It compared an easy, coherent global regularity with many unrelated
key--value bindings under radically different learning geometry:

- `PREDICT` before `ACT` was the same ordered prefix on every one of 80 rows
  and every epoch. Its gradients agreed, and the frozen base already supplied
  the arithmetic. The LoRA only had to install one high-frequency response
  disposition.
- A device colour was one arbitrary conditional association among 16. The
  one-shot run gave each association one authored view; the model instead
  learned the cheaper corpus marginal, one colour everywhere. Seed replication
  showed the same failure.
- The 16-copy sentinel then gave each fact more *identical* presentations but
  no new semantic view or countercondition. Short and long packaging both fit
  to near-zero loss and still emitted `red` for all 16 held questions. Thus
  long continuous context is not the missing ingredient, and repeated source
  likelihood is not extractable binding. The exact-training-form readout of
  these repeated adapters is still required before calling even repeated-form
  acquisition null.

Use one unified adapter next. Teach two separate dispositions in it: **predict
before acting** and **compare prediction with observed outcome before choosing
the next action**. If both are acquired, first test whether they compose with
no chained demonstrations; only if they do not, train their explicit
intertwining. Counterfactual outcome twins make the second behavior branch, so
perfect tag production cannot masquerade as conditional use.

This is the smallest useful step toward Think -> outcome -> Dream because the
second disposition consumes the first disposition's prediction and public
evidence. It is still authored open-loop post-training, not parenting, SLEEP,
H1, or a flywheel.

## What the sources actually support

Allen-Zhu and Li separate fitting source sentences from extracting their facts
under a new query. Their controlled biographies show that repeated stable
names, diverse biographies, and mixed storage/use forms matter sharply for
later QA. That supports stable keys plus several grounded views; it does not
say that duplicating one sentence 16 times inside one context will work, nor
that a LoRA on Qwen2.5-7B will inherit their result. The sentinel is therefore
consistent with, not a refutation of, their data-geometry result.

TMEM demonstrates a nearby feasible mechanism, not a fact-dose law: grounded
QA supervision updates a rank-6 FFN LoRA for five epochs, while an
outcome-trained extraction policy learns what QA data to write. It does not
show that arbitrary one-shot facts and a response habit learn equally, and its
base has been trained to be adaptation-friendly. Its useful lesson here is
that the *supervision interface* and extraction policy are part of the memory
mechanism.

Complementary learning systems (CLS) gives the correct biological analogy.
A slow, overlapping neocortical system extracts shared structure through
gradual interleaved learning; a fast, sparse hippocampal system protects new
arbitrary episodes and later reinstates them. This is not proof that the
project needs two neural adapters. It predicts exactly why one repeated global
routine is easier for a shared LoRA than 16 arbitrary bindings, and why a
written episodic record plus diverse interleaved replay is the fair unified-
adapter test. If rapid one-shot binding is eventually a requirement, the
biological analogue is an episodic buffer beside the consolidated adapter,
not automatically a second dense LoRA. Sun et al. further caution that
unregulated transfer of one-off residuals into the slow store can hurt
generalization.

Sources: [Allen-Zhu & Li, *Physics of Language Models: Part 3.1*](https://arxiv.org/abs/2309.14316),
[Ren et al., TMEM](https://arxiv.org/abs/2606.04536),
[McClelland, McNaughton & O'Reilly, CLS](https://doi.org/10.1037/0033-295X.102.3.419),
and [Sun et al., organized consolidation](https://doi.org/10.1038/s41593-023-01382-9).

## The smallest two-behavior test

### Competencies

Use a two-action, two-outcome nonce micro-world. Action strings and outcome
strings must each be native-token-length matched. Every prompt contains a
small public belief card, so this stage tests a taught procedure rather than
requiring stored world facts.

1. **PROSPECT:** given a belief card and goal, state the predicted consequence
   of the selected action before emitting the action.
2. **REVISE:** given that exact prediction, action, and a public observed
   outcome, classify `MATCH` versus `MISMATCH` and choose `KEEP` versus
   `SWITCH` for the next attempt.

Canonical scored surfaces are:

```text
USER: CASE <id>. BELIEF: <a0> -> <o0>; <a1> -> <o1>. GOAL: <o0>.
      Make one attempt.
ASSISTANT: PREDICT: <a0> -> <o0>
           ACT: <a0>
```

and, separately,

```text
USER: CASE <id>. PRIOR: PREDICT <a0> -> <o0>; ACT <a0>.
      OBSERVED: <observed>. Review before the next attempt.
ASSISTANT: COMPARE: <MATCH|MISMATCH>
           POLICY: <KEEP|SWITCH>
           NEXT: <a0|a1>
```

`MATCH` requires `KEEP` and the same action; `MISMATCH` requires `SWITCH` and
the other action. Half the rows are each branch. This rule is deliberately
elementary. The scientific content is conditional expression after
post-training, not discovering an advanced strategy.

### Training material and controls

One corpus has **128 isolated rows**:

- 64 PROSPECT rows: 16 independent semantic cards x four surface renderings;
- 64 REVISE rows: 16 counterfactual outcome pairs x two surface renderings.

Every case identifier is repeated in its grounded views. Action, outcome,
branch, template, row position, and target length are balanced. Rows from the
two behaviors are deterministically interleaved, never concatenated into a
chain. No evaluation sentence occurs in training.

Use exactly three states:

- **AUTH:** the correct prospective and revision targets above;
- **DERANGED:** identical prompts, schemas, complete target-token multiset,
  row count, batch count, and branch marginals, but predictions/actions are
  swapped within card-matched quartets and `MATCH/KEEP` versus
  `MISMATCH/SWITCH` targets are swapped within counterfactual pairs;
- **OFF:** the frozen base, with no adapter.

DERANGED is an experimental adapter, not a proposed child. Score it on both
the authentic map and its own assigned complementary map. If it cannot learn
its own map, an AUTH advantage could be a base prior rather than evidence that
the writer carries conditional supervision. No separate PROSPECT and REVISE
adapters are used. Separate substrates are the hypothesis under test, not an
assumption built into the treatment.

Before fitting, the tokenizer audit must prove AUTH/DERANGED equality of
unmasked target tokens, per-batch input/target length multisets, action and
outcome marginals, EOS positions, and absence of truncation or loss-bearing
padding. Constant-action, constant-branch, template-only, and position-only
policies must each have a ceiling of `.50`.

### Dose and plasticity

Keep the established frozen Qwen2.5-7B-Instruct base and the canary-qualified
rank-8 LoRA stack (alpha 16, dropout `.05`, same attention+MLP target modules,
optimizer, chat renderer, and target-only loss). Batch size is 4, four epochs,
no packing, warm start, merge, checkpoint selection, or retry. Each adapter
therefore sees `128 x 4 = 512` row presentations and exactly `128` optimizer
steps; each semantic case receives 16 grounded-view presentations.

Do not choose learning rate from these outcomes. Set it to **the lowest member
of `{1e-4, 3e-4}` that has already passed the independent acquisition-plus-
update-persistence sentinel**: it must acquire a new disposition while
retaining at least `.90` of the old habit after the registered unrelated
updates. If both pass, use `1e-4`; if neither passes, this test does not start.
This is an exact prospective selection rule and honors “plasticity before
adding more” without making this experiment another LR sweep.

Use material/optimizer roots `{0,1,2}`, paired AUTH/DERANGED within root. Run
root 0 first; expand only under the gate below. Maximum stage-A work is six
trained adapters and `768` optimizer steps.

### Readout and gate

After serialization, reload each state in a fresh process. Each request has a
fresh conversation and no feedback. Per root, use:

- 32 held PROSPECT cases: 16 unseen cards x two unseen forms, balanced so
  swapping the card swaps the optimal action;
- 32 held REVISE cases: 16 matched counterfactual twins differing only in the
  observed outcome;
- 16 no-phase/task-only controls and 16 unrelated native-interface cases;
- exact training-prefix readout as a diagnostic, never as the transfer claim.

Report four separate quantities, never one “adherence” aggregate:

1. **surface carriage:** required fields and order, with forbidden extra phase
   fields absent;
2. **semantic correctness:** predicted consequence, action, comparison, policy,
   and next action separately;
3. **counterfactual sensitivity:** fraction of outcome twins whose
   `COMPARE`, `POLICY`, and `NEXT` all flip correctly;
4. **task/interface preservation:** legal action, ordinary-task correctness,
   invalidity, and tag spill on no-phase prompts.

Also score candidate-normalized log odds. For REVISE, register

`I_R = logodds(KEEP : SWITCH | expected outcome) - logodds(KEEP : SWITCH | unexpected outcome)`.

For PROSPECT, use the analogous paired action interaction when the card/mode
swaps the optimal action. These interactions diagnose movement below greedy
accuracy; they do not replace strict generation.

Root 0 releases roots 1--2 only if both AUTH and DERANGED reach `.90` on their
own exact assigned maps, AUTH surface carriage is at least `30/32` for each
behavior, AUTH semantic correctness is at least `28/32` for each behavior,
at least `14/16` REVISE twins flip completely, and interface validity is at
least `.95` with no more than `.05` absolute loss from OFF.

The final two-behavior qualification requires **every root** to satisfy:

- surface carriage `>=.95` for each behavior;
- PROSPECT and REVISE semantic correctness `>=.875`, with each action/outcome/
  branch stratum `>=.75`;
- at least `14/16` complete counterfactual flips and `I_R >= 1.0` nat;
- AUTH and DERANGED own-map exact acquisition `>=.90`, and paired own-map
  redirection in the registered direction in both strict generation and log
  odds;
- no-phase tag spill `<=.05`, unrelated/interface degradation `<=.05`, and
  strict validity `>=.95`.

OFF may already make sensible choices. That does not invalidate procedural
carriage; it means the base supplied the reasoning. The only permissible
claim is that AUTH installed a form which *expressed* correct conditional use.
Claim increased conditional competence only if AUTH improves the predeclared
semantic endpoint over OFF as well. A DERANGED model that emits beautiful
fields but does not redirect on outcome is the explicit format-only result.

## Then test the intertwining

First run a **zero-additional-training composition probe** on the qualified
stage-A AUTH adapter. Each of 16 held dialogues per root (eight
counterfactual twin pairs) is a stateless three-turn exchange:

```text
card + goal -> PREDICT, ACT
public outcome -> COMPARE, POLICY, NEXT
fresh object under the updated belief -> PREDICT, ACT
```

Within each twin, one dialogue receives the expected outcome and the other the
unexpected outcome; all bytes before `OBSERVED` are identical. A chain
passes only when all three assistant turns are well formed, the first
prediction/action is correct, the revision branch is correct, and the final
prediction/action follows that branch. Require at least `14/16` whole-chain
passes in every root, both outcome branches at least `.75`, and no interface
gate regression. If it passes, stop: two isolated taught behaviors composed,
and adding chained examples would answer nothing new.

If both isolated behaviors qualify but this untrained composition fails,
train exactly one successor comparison from the frozen base:

- **CHAIN-AUTH:** the same 128 isolated rows plus 64 two-turn training
  dialogues (16 new cards x four surface families), with loss only on the two
  assistant turns;
- **CHAIN-DERANGED:** byte/token-dose matched, with the card/action and
  outcome/revision bindings complemented exactly as in stage A.

Reconstruct rather than warm-start, use the same selected learning rate and
four epochs, and replay the complete isolated corpus. Each successor sees 192
training units x four epochs and 192 optimizer steps at batch 4. The
AUTH/DERANGED target-token multisets and per-batch lengths must again be
identical. Use the same three roots, root 0 first. The same whole-chain gate
applies, plus stage-A PROSPECT and REVISE scores may fall by at most `.05`.

This staged rule distinguishes three outcomes cleanly:

- **separate pass + zero-shot chain pass:** the unified adapter carries both
  dispositions and their interface is compositional;
- **separate pass + chain-training pass:** the unified adapter works, but the
  linkage itself must be taught/replayed;
- **surface pass + conditional/chain fail:** only ritual carriage; do not call
  it level-1 conditional learning and do not spend a parented H1 lineage.

If authentic and complementary conditional maps both fail after diverse,
balanced views at the selected plasticity while global forms remain strong,
then—and only then—open a mechanism comparison: unified LoRA plus explicit
episodic text/retrieval versus a modular/routed fast store. A pair of separate
behavior/memory LoRAs is not the first fallback because it does not itself
solve one-shot binding and removes the very interaction Dream--LoRA--Think is
meant to learn.

## How the result changes the next step

- **Full chain qualification:** freeze this corpus, renderer, plasticity, and
  scorer as the level-1 birth primitive. The next experiment is the bounded
  parent -> child-authored grounded comparison -> SLEEP -> parent-free action
  bridge, using one adapter and an authentic-versus-binding-swapped write.
- **Two behaviors pass, chain fails even after chain teaching:** teach the
  interface as its own level-1 behavior or revise the training objective; do
  not add a compiler, parent, or more cognitive skills.
- **AUTH surface passes but counterfactual semantics fail:** preserve the
  result as a second global-habit positive. Repair condition-bearing training
  surfaces; more identical repetition and longer packing are ruled out by the
  sentinel.
- **Exact own-map passes but held forms fail:** add new grounded views at equal
  supervised target-token dose, following the Physics-of-LMs prediction.
- **Exact own-map fails:** the issue is acquisition/objective/capacity, not
  paraphrase extraction. Test the predeclared writer mechanism, not separate
  cognitive adapters.
- **Interface harm or no plasticity setting qualifies:** stop level-1
  accumulation. The current writer is too rigid or too destructive for a
  continuing Dream--LoRA--Think loop.

The promotion criterion is therefore not eloquent formatting. It is one
unified adapter whose first learned disposition creates a prediction, whose
second learned disposition changes action as a function of the observed
prediction error, and whose behavior remains bounded outside that causal
surface.
