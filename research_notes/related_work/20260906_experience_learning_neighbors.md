# Closest 2025–2026 neighbors to Experience Models

Date: 2026-09-06

Status: related-work and experiment-positioning note. This is not a novelty
claim, protocol approval, or result. Recheck final versions before submission.

## Bottom line

The broad claims that language agents can learn from their own action
outcomes, carry online fast LoRA state, selectively consolidate surprise into
LoRA, internalize embodied failure--correction trajectories, or improve a
frozen actor through an evolving textual memory are all occupied. So is the
claim that reflective recovery experience can be batch-distilled into the
acting model with the reflection removed at test time. The paper-worthy
unresolved claim is therefore causal and developmental, not simply
architectural:

> Can one target-blind parent intervention teach a single child a process of
> thinking through action such that, after the parent and all nursery-only
> state are deleted, the intervention increases the causal benefit of that
> child's later personal writes? Can those writes then carry connected
> action--outcome structure through fresh-goal traversal, information-seeking
> expansion, and still-later action beyond matched active-text and batch
> internalization controls?

That claim is not established by the papers below, but it is also not
established by our current v6 artifacts. The next protocol must compare
against their strongest relevant interfaces rather than a no-memory loop
alone. Deployment textual memory is not removed: it is held common between
write-on and write-off arms. What is removed is the parent, parental prose,
and every nursery-only ledger/context artifact. The clean parametric contrast
is therefore the write-enabled child against its own write-disabled twin on
top of the same active-text mechanism.

## TMEM / Scaling Self-Evolving Agents via Parametric Memory

Primary source: <https://arxiv.org/abs/2606.04536> (June 2026)

TMEM is the closest architectural neighbor. It formalizes a fast-weight
rollout whose policy jointly depends on working context, explicit memory, and
online LoRA state. When a context trigger fires, the acting model extracts
grounded QA-style supervision from its current session and performs a
lightweight online LoRA update; future actions in the same rollout are thus
produced by changed parameters. It also trains the base policy by RL so that
both ordinary task actions and memory-extraction actions improve outcome
reward, and uses SVD-initialized low-rank subspaces to make few-step writes
more effective. Its reported implementation uses rank 6 on FFN projections in
the final four transformer layers.

TMEM directly occupies "online parametric memory," "self-evolving agents,"
"experience distilled into LoRA during a life," and the broad claim that
working-context management plus explicit and parametric memory form one
agentic loop. Dream--LoRA--Think cannot be positioned as the first system in
that class.

The unresolved difference is the experimental intervention and the semantic
target. Our one-parent factorial asks whether target-blind process teaching
causes a larger *later* benefit from personal writes after the teacher and all
nursery state disappear. The proposed compositional relay separately asks
whether the resulting state carries connected relations that support
fresh-goal traversal, an information-seeking action that fills a missing
edge, and a still-later goal that needs both the old and new relation. TMEM's
ordinary QA extraction is therefore a mandatory writer baseline, not merely
a citation.

## PEAM / Parametric Embodied Agent Memory

Primary source: <https://arxiv.org/abs/2605.27762> (June 2026)

PEAM pairs a slow deliberative LLM with a fast parametric policy implemented
as category-isolated LoRA experts. Verified successes and matched
failure--correction trajectories are consolidated with behavioral cloning and
a contrastive objective. A parameterization-worthiness score selects what to
write, and a failure-statistics trigger selects when; future execution uses
the parametric skill and falls back to the slow tier when verification fails.

This occupies the embodied cultivate--then--consolidate story, selective and
self-triggered LoRA writes, corrected-trajectory internalization, and the
claim that parameter isolation can mitigate forgetting. Our sleep framing,
failure/recovery compilation, and periodic-versus-triggered scheduling are
not novel by themselves. The remaining distinction is one unified acting
policy accumulating an individual life, the target-blind parenting-by-later-
write estimand, and connected experiential inference rather than reflexive
category skills. A PEAM-style success-plus-correction writer is a relevant
method ablation if domain adaptation is feasible; otherwise it must be
described precisely and its missing comparison acknowledged.

## EVAF / Memory Depth, Not Memory Access

Primary source: <https://arxiv.org/abs/2606.26806> (June 2026)

EVAF evaluates surprise- and goal-valence-gated LoRA consolidation in a
loop-drift protocol where retrieval remains available but working context is
unloaded. It reports that selective parametric writes preserve goal-conditioned
behavior better than indiscriminate LoRA, while routed EVAF plus RAG exposes
complementarity between shallow factual access and deeper parametric state.

This occupies surprise-gated event selection, persistent behavior after
context unload, and the argument that the key question is what and how
strongly to write rather than parametric memory alone. Our surprise ledger and
selective sleep cannot be claimed as first. The clean distinction must be
typed action--outcome provenance, parent-caused later learnability, and a
multi-phase relay requiring connected structure and active expansion. EVAF's
selective-vs-naive LoRA comparison is a required conceptual baseline for the
writer study.

## Learning on the Job / Spark

Primary source: <https://arxiv.org/abs/2607.22157> (July 2026)

Learning on the Job shows that ordinary deployment feedback can continually
improve frozen-weight agents through an external memory of verified natural-
language rules. Its Spark store persists across sessions and models; outcome
verdicts or corrections are converted into scoped WHEN--THEN rules, with
write-time validation and explicit handling of look-alike situations. The
paper evaluates retention and cross-model portability against a static-RAG
policy-corpus control.

This is a stronger and closer active-text comparator than raw RAG. It occupies
"continual learning from deployment feedback with frozen weights" and makes
scope-aware rule writing a baseline capability, not a proposed LoRA-only
advantage. Our public `R0` must pass a prospective active-memory certificate
and implement the functional strengths of this family under the same
deployment tools and token budget before it may be called strong.

## LEAFE / Internalizing Agency from Reflective Experience

Primary source: <https://arxiv.org/abs/2603.16843> (March 2026)

LEAFE is the closest mechanism-level neighbor found so far. During experience
generation, the model periodically reflects on a trajectory, chooses an
earlier failure point, writes a diagnosis/fix summary, rolls the environment
back, and explores a revised branch. During experience distillation it trains
on two datasets:

- behavior rehearsal from successful trajectories;
- counterfactual experience-to-policy pairs that map the original history,
  *without the explicit experience summary*, to the improved post-rollback
  action.

It uses ordinary next-token SFT, reports Qwen2.5-7B among its model families,
and evaluates ALFWorld, ScienceWorld, WebShop, Sokoban, and CodeContests. Its
central claim is internalized feedback-grounded recovery agency, including
stronger Pass@k than outcome-RL and Early Experience baselines.

This directly falsifies novelty sentences such as “the model edits its
weights by thinking,” “reflection has not been learned into the acting model,”
“explicit guidance has not been faded before testing,” or “agents have not
internalized recovery from their own action feedback.” Our proposed scaffold
fading, fail/recover pathways, rehearsal guard, and parent-absent probe have a
clear precedent here and should be described as adopted/extended, not new.

The unresolved difference is *continual individuality*: LEAFE collects a
training corpus and produces a post-trained policy in a batch pipeline. Our
target is one deployed agent repeatedly writing a small personal adapter from
its own accumulating life, preserving old competence while context, goals,
environments, and human corrections change. That distinction requires a
lifetime curve, intermediate write checkpoints, forward/backward transfer,
and a direct comparison to one final LEAFE-style batch consolidation at the
same accepted rows, supervised tokens, and optimization budget. Merely
replicating LEAFE with LoRA or calling its reflection step a dream is not a new
paper.

Implementation lesson: LEAFE's published recipe is much cooler than v6's
writer (`1e-6`, batch 128, 2–3 epochs) and includes explicit successful-policy
rehearsal. We should treat this as a serious prior for writer calibration,
while separately measuring whether that heat remains sufficient for a small
rank-8 per-life adapter and much smaller incremental corpora.

## Agent Learning via Early Experience

Primary source: <https://arxiv.org/abs/2510.08558> (v3, May 2026; ICML 2026)

This is the closest conceptual neighbor. It explicitly uses interaction data
generated by an agent's own alternative actions and the resulting future
states as supervision. It studies:

- implicit world modeling: train the same policy to predict the next state
  from a state/action pair, then fine-tune on expert demonstrations;
- self-reflection: compare an expert action and agent-proposed alternatives,
  generate a rationale from their observed next states, and train the policy
  to emit the rationale plus expert action;
- eight agent environments, out-of-domain evaluation, and early-experience
  checkpoints as a warm start for later RL.

It directly falsifies any novelty sentence of the form “existing agents do
not learn from their own actions/outcomes” or “nobody trains the acting model
on self-reflection grounded in future states.”

The remaining distinction is architectural and temporal: Early Experience is
dataset/mid-training anchored at expert-visited states and expert actions. Our
target is an online, per-life, recurrent agent whose own history, corrections,
and self-generated connections are periodically consolidated into a small
personal adapter during deployment. That distinction only matters if we show
parent/expert-text removal, genuine prospective logging, lifetime scaling,
and transfer beyond a repeated finite curriculum.

Experiment consequence: include an Early-Experience-style batch SFT control
using the same accepted transitions and supervised-token budget. The LoRA
life arm must beat or mechanistically differ from “collect first, train once.”

## MemoPilot / From Player to Master

Primary source: <https://arxiv.org/abs/2606.08656> (June 2026)

MemoPilot trains a separate memory model with multi-turn RL. At test time it
updates a bounded textual memory from each trajectory and gives that memory to
a frozen, stateless player. Its memory representation explicitly separates
identification, maintenance, and actionable guidance; it reports gains on
RPS, Limit Hold'em, CoSQL, and DS-1000. It also reports that full history can
hurt, structured learned memory beats prompted memory, one-step credit is more
stable than cumulative credit, and learned wording affects executability.

It directly falsifies any novelty sentence of the form “memory updating is
currently hand-written rather than learned” or “no deployed frozen agent can
improve across interactions via a learned experience compiler.”

Our intended difference is that MemoPilot's learned component is a centrally
trained textual-memory copilot, while the player's parameters never change.
The proposed Experience Model writes a particular life into the acting
policy's own low-rank parameters and treats explicit text as a reversible
ledger/scaffold rather than the sole learned state. Better base players should
remain compatible, but cross-player transfer is already a MemoPilot strength,
not ours to claim for free.

Experiment consequence: a strong textual-memory updater is a required
baseline. At minimum, compare a structured identification/maintenance/
guidance memory produced under matched model-call and token budgets. If a
reproducible MemoPilot checkpoint/interface is available, use it or clearly
explain any domain incompatibility.

## Evo-Memory

Primary source: <https://arxiv.org/abs/2511.20857> (November 2025)

Evo-Memory is a streaming benchmark for self-evolving external memory and
implements more than ten memory modules across diverse sequential tasks. Its
ReMem baseline integrates action, thought, and memory refinement. It makes a
plain retrieval baseline insufficient for our paper: external-memory
competition should include an active refinement system, not only raw RAG.

Experiment consequence: borrow its streaming evaluation language and include
at least one action-think-refine external-memory baseline under the same
acting model and context budget.

## When Continual Learning Moves to Memory

Primary source: <https://arxiv.org/abs/2604.27003> (April 2026)

This study shows that external memory relocates rather than removes the
stability/plasticity problem. Across ALFWorld and BabyAI, abstract procedural
insights transfer more safely than raw trajectories; negative transfer is
concentrated on hard cases; and a representation that wins within one task
can lose across tasks.

This independently supports three design choices we had reached from v6:

1. race raw trajectories against abstraction/connection-rich compilation;
2. scope specific memories and separately measure cross-environment transfer;
3. report difficulty-stratified negative transfer, not only mean performance.

It also raises the bar: a parametric adapter does not win merely because
external memory has retrieval interference. We must measure its own
interference, forgetting, and hard-case failures under a matched lifetime.

## CL-Bench / Continual Learning Bench

Primary source: <https://arxiv.org/abs/2606.05661> (June 2026)

CL-Bench evaluates stateful agents across six expert-validated domains whose
task sequences share learnable latent structure, and introduces gain metrics
intended to separate online learning from initial model capability. Its main
finding is itself a warning for this project: dedicated memory systems can
overfit recent observations or fail to reuse knowledge, and naive in-context
learning may beat them.

This occupies broad benchmark claims about first measuring continual agent
learning in realistic stateful domains. CompilerGym gives us dense,
deterministic action value and controlled one-parent causality, but it is not a
multi-domain replacement for CL-Bench. Cite CL-Bench as the external validity
and terminology boundary; a later deployment study should run the fixed
parenting/writer policy on a CL-Bench-compatible stream rather than claiming
domain-general meta-intelligence from compiler optimization.

## Macaron-V1

Primary source: <https://arxiv.org/abs/2608.09819> (August 2026)

Macaron-V1 explicitly frames open continual learning as recursive improvement
of versioned model--harness pairs and uses a Mixture-of-LoRA architecture for
specialist capabilities. Its own report leaves compounding continual-learning
gains open, but it occupies the broad language of experiential intelligence,
self-improving model--harness systems, and extensible LoRA specialists.

Our paper should not claim the first experiential-intelligence architecture or
use a broad category name as the novelty. The fixed one-parent causal
intervention, complete teacher deletion, later write-on/off factorial, and
within-child experiential relay are the narrower testable objects.

## Required positioning and baseline correction

Do not claim:

- first agent to learn from its own experience;
- first self-reflection training from action outcomes;
- first internalization of feedback-grounded recovery into model weights;
- first reflection/rollback/improved-branch distillation;
- first removal of explicit experience guidance after distillation;
- first learned online memory updater;
- first continual test-time improvement with a frozen base player;
- first agent with online LoRA fast weights or intra-rollout parametric
  adaptation;
- first selective/surprise-gated LoRA consolidation;
- first embodied failure--correction consolidation into isolated adapters;
- first demonstration that raw histories or raw procedural memories can hurt.

Potential claim, only if the future evidence supports it:

- a target-blind one-parent intervention that increases the marginal causal
  benefit of later personal writes, measured by the registered
  `U0/U1/P0/P1` interaction and accompanied by beneficial parented writes and
  literal within-life improvement;
- parent-absent behavioral absorption localized by adapter removal and
  wrong-life/shuffled-life controls, with deployment active text held common;
- a native typed-action writer that preserves useful proposal content without
  self-reinforcing serialization drift;
- connected experiential structure that supports fresh-goal traversal,
  missing-edge information-seeking, and still-later action after the new
  outcome is written;
- continued or cross-environment improvement beyond a certified active-memory
  baseline and matched batch internalization controls under declared compute;
- measured laws connecting accepted experience volume, write heat, rank,
  abstraction level, and negative transfer.

The clean paper comparison is therefore not “memory versus no memory.” It is:

1. frozen loop;
2. full history / raw RAG;
3. active refined textual memory (ReMem/MemoPilot class);
4. Learning-on-the-Job/Spark-style verified scoped rules;
5. TMEM-style native QA fast-LoRA writes;
6. naive/native continual LoRA without Dream--State compilation;
7. batch Early-Experience-style state-prediction SFT;
8. batch LEAFE-style recovery distillation on the same accepted transitions;
9. per-life Dream--LoRA--Think consolidation;
10. the full one-parent `U0/U1/P0/P1` factorial with all parent and nursery
    artifacts deleted before deployment.

The paper earns its narrowed claim only if the parenting interaction and the
absolute-learning guards pass, and the compositional relay shows behavior
that the stronger textual, native-LoRA, and batch controls do not explain.
