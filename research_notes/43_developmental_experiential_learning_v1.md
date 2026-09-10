# Developmental experiential learning v1 (proposal only)

**Status:** unratified research proposal. This document does not authorize a
benchmark implementation, GPU run, or paper claim.

## Governing question

Can a fixed pretrained agent turn its own action--outcome history into a
progressively more useful, compressed experiential model, such that its later
actions continue improving after the lived history no longer fits in working
context and strong external-memory agents begin to flatten?

This is not primarily a fact-recall question. The target is **constructive
experiential learning**: experience should change later information gathering,
causal reconstruction, planning, recovery, and action on situations whose exact
solution was never present in an earlier episode.

The developmental prediction is allowed to be non-monotone. Context or RAG may
win early. Parametric consolidation earns its cost only after enough repeated,
diverse structure has accumulated. The paper must measure the onset of useful
memory, not assume an advantage from episode one.

## Reference architecture

The mature reference system is one recurrent resolver invoked in two regimes,
plus an explicit compiler and two different forms of memory:

```text
ACT / OBSERVE
  -> WAKE RESOLVER
       goal-conditioned retrieval
       associative breadth + explicit dependency traversal
       hypothesis / plan / action
       cited thought-action path + unresolved dependencies
  -> VERBATIM EPISODIC STORE
       immutable observations, actions, outcomes, and provenance
  -> SLEEP SCHEDULE
       select surprising, rewarded, contradicted, repeated, traversed,
       or currently useful traces
  -> DREAM RESOLVER
       replay traces; propose local relations, procedures, exceptions,
       alternative views, and path shortcuts
  -> SLEEP COMPILER
       deduplicate, canonicalize, preserve provenance and uncertainty,
       generate multiple access views, and prepare training examples
  -> PER-LIFE MEMORY LORA
       lossy semantic/procedural associations and tested hot-path shortcuts
  -> LATER WAKE RESOLVER
       iterative local adapter queries + exact episodic support
       -> goal-conditioned working-path reconstruction -> better action
```

Operationally, wake is narrower and DFS-like; dream is broader and BFS-like.
Those are controller metaphors, not a claim that a literal graph is stored in
the adapter. The explicit provenance/dependency graph is an **audit shadow**.
It measures what was co-retrieved, traversed, reinforced, revised, or
materialized without becoming a solver available to cognition.

The adapter read is **goal-conditioned reconstruction**, not literal
decompression. LoRA is lossy and not invertible. Exact observations remain in
the episodic store; the adapter supplies learned associations, likely relevant
relations, procedures, and shortcuts. Multi-hop composition stays explicit in
tokens and working state.

### Learned objects and isolation

- The base model is frozen.
- The prompted resolver/sleep policy is fixed across all evaluated lives. It is
  an amortized reference controller, not a within-life learning result.
- The **MEMORY adapter** is the only per-life learned parameter object. It is
  rebuilt cumulatively from the clean base at sleep checkpoints and reset for
  every new life/world.
- The verbatim episodic store and bounded working state are non-parametric and
  reset with the life.
- A future **LOOP adapter** may learn how to retrieve, explore, dream, compile,
  stop, and act from many successful and failed lives. It must be trained only
  across development worlds and frozen inside every evaluation life. It is a
  later extension, not required for the Paper-1 claim.

## Honest verification

No hidden rule solver, answer-bearing graph, or perfect verifier may steer the
headline system.

Claims earn support chronologically:

1. At time `t`, the resolver commits a prediction and cites only evidence
   available by `t`.
2. Later lived evidence or an executed intervention is hidden at commitment.
3. The environment returns the public outcome.
4. A mechanical comparator records agreement or contradiction; it does not
   propose the claim or expose an answer.
5. Unsupported claims remain provisional. Contradicted claims remain in the
   append-only audit log and trigger revision/reconsolidation.

Fresh-context reflection and exact offline scoring are diagnostic arms. They
are not truth sources in the cognitive loop.

## Two-level evaluation suite

No existing benchmark alone identifies the full causal claim. Use two linked
levels, with one secondary compatibility result.

### Level 1: controlled persistent causal action-life

This is the mechanism microscope. It must be semantic and action-first, not a
nonce color-memory puzzle. Each generated life contains stable local causal
regularities over entities, conditions, tools, hazards, interventions, and
outcomes. Evidence is dispersed across episodes; no witnessed trajectory gives
the exact held-out solution.

Required properties:

- partial observations produced by actions;
- reusable world-specific causal structure anchored in pretrained semantics;
- inspect/experiment/prepare/act/recover operations with costs;
- active information gathering;
- one- through four-dependency held-out action goals;
- counterfactual twin worlds that share superficial signatures but require
  different explanations/actions;
- exceptions and a later controlled rule change;
- programmatic ground truth available only to offline analysis;
- deterministic replay and whole-world replication.

This world proves whether trace-conditioned sleep, compilation, and per-life
LoRA cause later action gains. It does not by itself establish external
generality.

### Level 2: DiscoveryWorld-Lifetimes

DiscoveryWorld is the leading external target because its stock tasks already
require hypotheses, experiments, outcome analysis, explanatory discovery, and
action. It provides 120 parameterized tasks across eight topics, three
difficulties, and five official seeds, with automatic completion, procedural,
and explanatory-knowledge scores.

The stock protocol is per scenario, not lifelong. Before adoption, a fit gate
must establish that within-topic variants share reusable structure while
retaining seed-specific discoveries. If so:

- order related scenarios/segments into reset-isolated lives;
- preserve only the declared episodic state and MEMORY adapter;
- sleep at geometric action/episode checkpoints;
- evaluate frozen memory on held-out continuation branches or target variants;
- never feed checkpoint outcomes back into the life;
- report both fixed-experience and on-policy conditions.

If the reuse/branching gate fails, DiscoveryWorld becomes external qualitative
validation and ScienceWorld-Lifetimes becomes the fallback. ScienceWorld is
cheaper, deterministic, language-native, and directly comparable to
Auto-Dreamer, but it needs persistent per-life local laws to avoid measuring
only ordinary science/procedure distillation.

Primary sources:

- DiscoveryWorld paper and code: <https://arxiv.org/abs/2406.06769>,
  <https://github.com/allenai/discoveryworld>
- ScienceWorld: <https://arxiv.org/abs/2203.07540>,
  <https://github.com/allenai/ScienceWorld>
- Auto-Dreamer: <https://arxiv.org/abs/2605.20616>

### Secondary: EvoMemBench CrossEp-Emb

EvoMemBench supplies a useful compatibility result and a strong baseline suite.
Its CrossEp-Emb track has an explicit memory backend interface and ALFWorld
baselines including BM25, GraphRAG, A-MEM-like memory, workflow/skill memories,
ACE, and ReasoningBank. Its stock source-memory to read-only-target protocol is
not the developmental on-policy claim, so it is secondary rather than the
headline.

Sources: <https://arxiv.org/abs/2605.18421> and
<https://github.com/DSAIL-Memory/EvoMemBench>.

## The two causal experiments

### A. Fixed common-deck attribution

For each world/life seed, every method receives the same ordered
action--observation--outcome stream. At geometric checkpoints:

1. consolidate according to the method;
2. clear working context and caches;
3. freeze the life memory;
4. evaluate a fresh read-only deck of held-out action tasks;
5. discard evaluation outcomes.

This isolates the effect of representation and use from exploration quality.

### B. On-policy developmental flywheel

Agents choose what to inspect, test, attempt, revisit, or defer. Better memory
may produce better evidence, which may produce better later memory and action.
Use paired world seeds, the same action budget, and hidden read-only checkpoint
evaluations.

Add a cross-system experience swap: consolidate system A's life with system B's
memory pipeline and vice versa. This decomposes gains into better experience
collection versus better representation/use of the same experience.

## Developmental scale

Let `C` be the disclosed working-context budget used by every primary method.
Tokenize the full lived stream and evaluate near:

```text
0.5C, 1C, 2C, 4C, 8C, 16C
```

Also run the strongest feasible native-long-context control so the result is
not an artifact of choosing a small `C`. New causal coverage must continue
after `C`; repeated filler does not constitute a long life.

Define the useful-memory threshold as the first checkpoint where the paired
advantage over the strongest matched external-memory baseline exceeds a
pre-registered practical margin and remains positive for two later
checkpoints. Report:

- threshold location;
- post-context area under the lifetime curve;
- post-threshold slope;
- final capability;
- correction half-life after a rule change.

The replication unit is a world-life, never a probe or episode.

## Capability ladder and endpoints

- `A0`: exact witnessed transition recall (installation diagnostic only).
- `A1`: near-transfer of a local procedure (control).
- `A2`: select a novel action from a regularity distributed across episodes.
- `A3`: compose two or more learned dependencies into a new multi-step plan.
- `A4`: revise a stale model after an exception/change and recover.

The primary endpoint is normalized A2--A4 action value at a post-context
checkpoint plus post-context AUC. Secondary endpoints include first-attempt
success, regret/actions-to-goal, explanatory knowledge, information-gathering
quality, old-task retention, dependency depth resolved at fixed think budget,
memory/query tokens, adapter bytes/training FLOPs, false-memory rate, and
correction half-life.

## Minimum comparison set

- fixed agent with no persistent memory;
- recent/full context and strongest feasible native-long-context control;
- raw trajectory BM25/embedding RAG;
- linked A-MEM/GraphRAG-style external memory;
- reflection/lesson or procedural skill memory;
- direct trajectory-to-QA LoRA;
- raw-trajectory LoRA;
- sleep-compiled text memory;
- the identical sleep corpus in LoRA;
- atomic sleep writes without materialized shortcuts;
- atomic writes plus trace-selected shortcuts;
- the full recurrent Sleep--LoRA--Think reference system;
- shuffled action--outcome, shuffled binding, and cross-life adapter controls;
- batch SFT on the same accumulated life as an explicitly labelled upward
  reference, not a matched online method.

Match base model, environment actions, working-context/retrieval budget, agent
thought budget, memory bytes or report both budgets, and consolidation compute.

## Existing evidence and remaining claim

Current project evidence supports only the following prerequisites:

- constrained atomic experience can be installed into LoRA and read
  associatively;
- under the same recognition protocol, text and LoRA are equal at small memory;
- structured search can solve the Semantic/Blendy computation ceiling;
- standalone direct-parent dreaming is not an adequate model of the recurrent
  system and failed honestly;
- false structural writes can poison an otherwise functioning downstream path.

Still unproven:

- trace-conditioned sleep produces more useful action memory than direct
  replay, reflection, or structured external memory;
- per-life LoRA crosses over after context saturation;
- hot-path materialization reduces later reasoning cost without destroying
  transfer;
- better memory changes exploration and compounds into better experience;
- the mechanism revises rather than merely preserves stale associations.

## Hard falsifiers

Narrow or reject the headline claim if any of these hold:

1. After context overflow, the system does not sustain an advantage over the
   strongest matched organized external-memory baseline.
2. The advantage disappears under the identical common deck.
3. Shuffling action--outcome bindings or cross-life adapters does not hurt.
4. Gains occur only on A0/A1 lookup/procedure tasks, not A2--A4 action.
5. Sleep compilation does not improve action over direct-QA/raw LoRA.
6. Materialized shortcuts do not reduce later query/hop cost at matched action
   accuracy.
7. Recurrent sleeps add compute but do not beat a single end-of-life batch.
8. Results are explained by extra environment actions, thought/retrieval
   tokens, adapter capacity, or consolidation compute.
9. False-memory accumulation outruns correction.
10. A target-only/current-state/identifier probe predicts held-out answers
    above its registered floor.

## Immediate decision gates

1. **Environment fit, CPU-first:** inspect and smoke DiscoveryWorld; quantify
   within-topic structural reuse, trajectory length/token density, state
   cloning/continuation feasibility, and decision-time memory injection.
2. **Mechanism-world validity:** generate small candidate lives and reject any
   world with target leakage, weak oracle ceiling, no RAG saturation, or no
   action value for cross-episode structure.
3. **Atomic writer gate:** install varied witnessed atoms, reverse/paraphrase
   reads, exceptions, and one tested shortcut before an end-to-end run.
4. **Common-deck pilot:** compare the smallest decisive arms at `1C` and `2C`
   on cheap development worlds.
5. Scale worlds, lifetime, model, and GPU only after these gates pass.

The proposed paper claim is behavioral and falsifiable:

> Sleep-compiled lifetime parametric memory allows a fixed agent to continue
> improving on held-out actions as experience exceeds its working context,
> where matched episodic, linked-text, and direct-parametric baselines flatten.

