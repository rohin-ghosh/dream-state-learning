# 42 — System thesis and experiment-to-claim map

Date: 2026-08-31. This note is a navigation invariant, not authorization for a
new run. Frozen experiment plans, leakage gates, and human authority boundaries
still apply.

## First-principles objective

The project is not trying to build a better fact register. It tests a continual
agent flywheel:

```text
action
  -> outcome-bearing experience
  -> recurrent dream: compress, connect, revise, preserve provenance
  -> persistent per-life experiential world approximation
  -> goal-conditioned retrieval and multi-hop planning
  -> better action
  -> better and more informative future experience
  -> repeat
```

The memory is useful only if it changes a later decision that no individual
stored episode directly answers. Exact recollection is a necessary diagnostic,
not the behavioral claim. Likewise, a high reasoning ceiling, a pure verified
corpus, or a faithful LoRA read is only one organ of the system.

Action is epistemic as well as instrumental. At the full-system stage the
policy must sometimes act to resolve a structural uncertainty, not merely use a
fixed replay deck to choose a better known action. The resulting observation
must alter later dreaming, memory, and behavior. A scripted common lifetime is
useful for causal attribution, but by construction it cannot demonstrate this
self-improving experience-distribution loop.

## Three nested learning timescales

1. **Cognitive loop — within an episode.** State -> retrieve -> think -> plan ->
   act/observe -> update/replan -> release, defer, or stop. The current prompted
   loop is an amortized controller and data generator.
2. **Experience/dream loop — within a life.** Episodes and outcomes -> local
   abstractions, causal/action conditions, exception splits, higher-order
   connections -> per-life memory. Working state changes fastest; the lifetime
   adapter is fast parametric state and resets for every distinct evaluation
   life `(world_id, skin_id, life_id)`.
3. **Outer learning loop — across lives.** Successful and failed operational
   trajectories train a reusable LOOP policy: what to retrieve, hypothesize,
   test, revise, plan, act, and when to stop. This adapter must be distinct from
   the per-life MEMORY adapter. Outcome-filtered SFT is the first method; RL is
   optional until supervised distillation demonstrably fails.

The eventual outcome/value model is not a perfect thought verifier. It estimates
whether a state or next operation is likely to improve the long-horizon outcome
enough to justify its compute.

Dreamer and thinker are two regimes of one recurrent machine, not unrelated
architectures. Both implement `state -> choose operation -> retrieve -> one
cognitive step -> update -> optional write -> repeat`. Thinking is narrow,
goal-conditioned dependency resolution followed by action; dreaming is broad,
surprise/uncertainty-conditioned connection, compression, and agenda creation.
The scheduler and objective differ, while the state, retrieval, provenance, and
update interfaces should remain shared. Training both regimes from the same
kind of causal trajectory is a future amortization design; the current prompted
controllers are teachers/ceilings and trajectory generators, not evidence that
this shared policy has been learned.

The target rate hierarchy is: fast working state and plans; medium dream
connections and the per-life MEMORY adapter; slow reusable controller/scheduler
skill; very slow base capability and broad outcome critic. These levels learn
different things: world learning estimates what is true, connected, and causal;
controller learning estimates what to retrieve, test, plan, and spend compute
on. The critic evaluates progress and eventual utility, not whether an
individual thought is metaphysically true. Today the working state is explicit,
the per-life adapter is the trained component, and the prompted controller
traces are prospective training data; the learned scheduler and broad critic
remain future work.

## What each current rung actually tests

| Rung | Causal link isolated | A positive result permits | It does **not** prove |
|---|---|---|---|
| L0 / atomic write probes | formatted claim -> LoRA -> recognition read | parametric experiential facts can be installed and recovered | autonomous dreaming, connected construction, action gain, scale |
| Semantic D0–D2 | public experience / supplied structure -> composition | the clean reasoner can use recognized leaves for held-out inference | higher-order hypothesis generation or online improvement |
| v0.2 exhaustive branch ceiling | public evidence -> inspectable atomic search -> exact parents | exact parent recovery is computable inside the declared subset family | final-answer causal attribution: a target-signature shortcut bypasses parents, roles, dreaming, and LoRA |
| Counterfactual Confluence v0.3 (implemented calibration) | dispersed intervention edges -> connected memory -> counterfactual reconstruction | causal interface and public-edge solvability; after v0.3-R, one thinker-agenda -> later-dream -> rethink transition | LoRA necessity, deep recurrent growth, policy-selected exploration, or lifelong scaling; the current life is only ~1.1k tokens and a passive-signature lookup is above majority |
| v5 prefix-nested direct-parent proposals | task-family-scaffolded independent proposals -> public-evidence-gated connected text memory | measured negative: recall plateaued at 3/12; supported precision 0/5; retained parent corpus 0/12 true, so transport is barred | recurrent micro-dreaming; autonomous structure discovery; the verifier-free headline; LoRA memory; full continual learning |
| Fixed-corpus text vs LoRA | identical accepted claims -> two substrates -> identical reads | whether parametric transport is faithful under a matched resolution protocol | that LoRA beats external memory at small scale |
| Atomic-call thinker probe | goal/state -> memory questions -> workspace updates -> chain -> halt | the controller retrieves the right dependencies and composes them at fixed memory quality | dream quality or parametric write quality |
| Full Semantic organism | experience -> dream -> memory -> adaptive think -> held-out construction | the complete amortized information flow works without a stored final answer | improved environment action or lifelong growth |
| Action World A0–A3 | past action/outcome experience -> new multi-step choice and feedback | experiential memory improves novel behavior, recovery, and planning | continued improvement with lifetime by itself |
| Lifetime/depth/capacity curves | repeated online cycles -> increasing constructive/action capability | the continual system keeps acquiring useful structure and identifies where baselines saturate or degrade | baseline saturation unless it is actually measured |
| LOOP-adapter training | many operational trajectories -> reusable controller -> unseen worlds | dream/think scheduling and query selection are learnable across lives | per-life world knowledge in the shared controller |

## Mandatory component gates before the action headline

1. Dreamed memory contains enough local operator/causal fragments,
   role/class abstractions, witnessed leaves, and cross-memory links for the
   thinker to reconstruct a useful provisional structure, without requiring
   the dreamer to store the complete parent set or the held-out answer.
2. The same fixed corpus can be resolved from text and from the lifetime LoRA;
   exact, reverse, paraphrase, and partial-cue read failures are reported.
3. At fixed known-good memory quality, the thinker asks useful questions,
   retrieves prerequisite leaves, builds a cited chain, and defers rather than
   confidently fabricating when dependencies remain missing.
4. The end-to-end organism beats no-memory, raw-memory, and shuffled controls on
   held-out constructive goals before Action World becomes the primary result.
5. Action evaluation measures decisions, return/regret, recovery, and multi-step
   plan success—not only QA about past experience.
6. The action policy can repeatedly select information-seeking interventions;
   their outcomes change the later experience distribution, are reconsolidated,
   and improve held-out return or information gain versus fixed-deck controls.

## Baselines required by the narrow claim

At matched model, action, reflection, retrieval, and write budgets:

- stateless / standard frozen agent loop;
- full transcript while it fits, then an honestly truncated long-context arm;
- iterative episodic RAG over raw trajectories;
- organized or A-MEM-like linked external memory;
- reflection/lesson memory such as Generative Agents / ExpeL-style text;
- direct trajectory-to-QA LoRA (TMEM-style), not only raw next-token LoRA;
- raw-history and shuffled/dreamless LoRA controls;
- dreamed text memory and the identical dreamed corpus in LoRA;
- explicit graph/skill-library controls where feasible (DECKARD/Voyager class);
- batch post-training on the same lifetime;
- exhaustive/oracle conditions, always labeled ceilings.

The broad dreaming, continual-agent, connected-memory, and parametric-memory
territories are occupied by prior work. The defensible Paper-1 contribution is
a controlled systems/measurement claim about constructive experiential
parametric memory: blinded/provenance-conditioned consolidation, the
precision–coverage–downstream-decision trade-off, faithful per-life transport,
and improvement on held-out construction/action beyond the context budget.
Do not claim the first LoRA memory for agents, first parametric memory that
changes action, first embodied parametric memory, first sleep-inspired embodied
consolidation, or first outcome-trained extraction policy; TMEM, PEAM, and
neighboring systems occupy those axes.

## Planner interface invariant

The sequential thinker should expose an auditable state machine rather than a
single free-form answer:

```text
STATE(goal, observations, unresolved dependencies, workspace, budget)
  -> QUERY one typed atomic dependency
  -> MEMORY returns one immutable fact + provenance, or NOT_FOUND
  -> UPDATE / REVISE the supported workspace
  -> REPLAN, QUERY again, RELEASE with cited support,
     REQUEST_DREAM with a typed non-evidentiary frontier, or DEFER
```

`REQUEST_DREAM` does not turn a thinker guess into memory. It creates a
selection-only dependency/confusion/desire record visible to the next dream
phase. A later dream may add a durable edge only by citing eligible public
experience or prior semantic memories. The resulting semantic snapshot and
per-life adapter are frozen before the thinker retries. The controlling phase
and ontology contract is `research_loop/plans/interleaved_organism_v1.md`.

Query selection, reader fidelity, chain validity, stopping, and final action
must be scored separately. A final correct answer cannot erase a missing-parent
failure, and a wrong answer cannot automatically be blamed on the LoRA.

The resolution protocol is part of the intelligence. At small memory,
context+recognition and LoRA+recognition can match; the weights hypothesis begins
when the lifetime exceeds the prompt budget. Consequently no gain produced by
canonical candidate recognition, recursive query selection, or clean-base
composition may be attributed to the adapter alone.

Dream memories must also remain epistemically typed. Generate predictions
without the target answer or target-scoring evidence visible (declared public
lived evidence remains available), compare only after commitment, and retain
`provisional`, `supported`, and `contradicted` states append-only with
provenance. A fresh or mechanical public-data check may score a committed
hypothesis, but hidden truth and offline solvers may never steer generation,
retrieval, or planning in a headline condition.

Each claim records its source observation/memory IDs, derivation depth,
prediction, confidence, and status. A depth-2+ claim must cite earlier
memories; repeated wording is not independent support, and a long transcript
does not by itself demonstrate depth. Measure local-edge formation, path
availability, and thinker-side structural reconstruction separately so a
correct final answer cannot conceal a broken information-flow chain.

## Capacity and compression are a measured response surface

Do not assume that more or fewer parameters inherently produce intelligence.
At a fixed base, vary lifetime-adapter rank and memory representation from raw
episodes through atomic leaves to connected abstractions and aggressive
procedural compression. Report separately:

1. exact experiential-leaf recall;
2. held-out constructive composition;
3. downstream action value.

Only after the fixed-base surface is understood should selected points be
repeated across base-model sizes. A proposed Goldilocks regime is falsified if
rank/compression effects are flat, are explained by failed installation, or
vanish against matched strong baselines.

Compression is directional, not just a menu of corpus formats: as lifetime
grows, useful dependency, causal, procedural, and abstraction structure should
rise while unnecessary episodic detail can fall. Measure this longitudinally
with paired gist/verbatim probes, provenance/connection retention, constructive
composition, and action value. A k0--k3 representation ablation by itself does
not show that the system learned what to compress.

The headline is a growth curve, not a single held-out score: along lifetime
length, world complexity, and required dependency depth, the connected-memory
system should still improve after strong baselines are observed—not assumed—to
flatten or degrade. The claim is better eventual capability, not merely faster
learning at an early point.

## Long-sequence controller-training contract

After the amortized organism works, preserve successful and failed causal
traces as `PUBLIC_STATE -> ASSISTANT_OPERATION -> TOOL/ENV_RESULT -> NEXT_STATE`.
Remove hidden answers, proof graphs, solvers, and checker/evaluator artifacts
entirely from model-visible inputs and targets. Apply loss masks to the allowed
public state, user, tool/environment, and offline-scorer context; train only the
model's cognitive and action-operation tokens. Start with behavior cloning of expert/exhaustive traces on development
worlds, evaluate full open-loop trajectories on whole unseen worlds without
teacher forcing, then use rejection-sampling SFT on successful efficient
self-trajectories. Preference optimization or RL is justified only if this
supervised ladder fails to explore. Throughout, the shared LOOP adapter is
frozen across an evaluation life and the MEMORY adapter is null or newly
initialized for every `(world_id, skin_id, life_id)`; no per-life state is ever
reused across evaluation lives, even within the same world.

The causal roadmap remains: world-building memory -> constructive combination
over experience -> action construction -> policy-selected evidence gathering ->
revised memory and better later action. Current Semantic World tests only
ceiling/reference versions of public-evidence composition and fixed-corpus
goal-conditioned reconstruction. Recurrent micro-dreaming, learned scheduling,
parametric transport of autonomously grown connections, action-selected
evidence gathering, and the full online flywheel remain unshown. Action World
is not promoted until fixed-corpus transport and the adaptive thinker pass
their gates.

Semantic World v0.2 D3 answer accuracy is additionally headline-ineligible:
the one- and two-visible-role target signatures deterministically identify the
held-out role under the cyclic source generator. Preserve v0.2 for exact-parent
and mechanism diagnostics, require explicit target-only shortcut baselines,
and use the collision-based Counterfactual Confluence transition in
`research_loop/plans/counterfactual_confluence_v03.md` before another
whole-organism accuracy claim.

The original Counterfactual Confluence v0.3 is also calibration-only. Its
collision twins repair the v0.2 target decoder and give a clean public-edge
oracle, but the life has 46 episodes (~1.1k tokens), all final proof leaves are
public, a fitted passive-signature lookup is materially above majority, and it
lacks a thinker -> dream -> rethink transition. Preserve it, build the repaired
v0.3-R as new files, and require paired-twin scoring plus held-out shortcut
predictors before a model run.

## Experiment-plan checklist

Every new plan must state:

1. Which arrow in the flywheel it tests.
2. What information each model, memory, checker, and scorer may see.
3. The strongest conclusion a positive result permits.
4. The conclusions that remain forbidden.
5. The matched compute, memory, action, and context budgets.
6. Whole-world development and held-out splits.
7. A predeclared stop/go rule and the next permitted transition.
8. The exact traces preserved for later LOOP-policy training.
9. Whether actions are fixed for attribution or policy-selected to gain
   information; only the latter can support the full online-learning claim.
10. Which cognition is supplied by the read/resolution protocol versus learned
    in the memory substrate.

If those ten fields are missing, the run is not ready even if its code works.
