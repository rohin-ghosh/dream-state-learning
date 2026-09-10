# Interleaved dream--memory--think organism v1

Date: 2026-08-31 PT. Status: consensus architecture; implementation in
progress. This document is the controlling graph/loop interpretation of
Rohin's recurrent-memory design. It supersedes any one-way reading of
`experience -> dream -> LoRA -> terminal thinker`, but it does not authorize a
GPU science run by itself.

## First-principles claim

The system turns action/outcome experience into a progressively richer
experiential world approximation and uses that approximation to make better
later decisions. Intelligence is attributed to the recurrent trajectory, not
to one organ:

```text
public experience
  -> broad/local semantic dreaming
  -> connected semantic memory
  -> memory-specific write realizations
  -> per-life parametric memory checkpoint
  -> narrow goal-conditioned thinking
  -> release, defer, or non-evidentiary frontier
  -> later agenda-conditioned dreaming
  -> revised/enriched semantic memory and checkpoint
  -> rethink
  -> action/outcome becomes new public experience
  -> repeat
```

The complete Blendy/parent/counterfactual structure need not appear during the
first dream, or ever exist as one durable record. A dream usually adds one
local connection. A thinker temporarily assembles longer task-specific paths.
When it stalls, its missing dependency can guide a later dream. That later
dream must independently re-derive any durable connection from eligible public
experience or prior semantic memory.

## Two orthogonal dream operations

### 1. Semantic growth

Semantic dreaming changes what the life is believed to contain. One call may:

- create one concept handle;
- add one witnessed, relational, causal, operator, similarity, difference, or
  exception edge;
- revise or split one earlier edge;
- reinforce an identical edge through an independent evidence path;
- open one local uncertainty;
- pass.

It is breadth-oriented: revisit different memories, make modest fan-out, and
occasionally continue a useful child by one hop. Breadth is a scheduling bias,
not a claim that the model can never follow a deep branch while dreaming.

### 2. Write-realization growth

Realization dreaming changes how an already accepted semantic memory is
installed and queried. The dreamer selects:

```text
target semantic edge + realization lens + optional connected cue edge
```

A deterministic compiler initially renders canonical, forward-QA,
typed-cloze/partial, legal-reverse, situated, or contrast views. Free model
paraphrases are a later ablation.

Realizations are not beliefs. They never create semantic nodes, evidence,
support, derivation depth, or graph distance. If a proposed "variation"
asserts a new relation, it is routed back through semantic dreaming and needs
its own provenance.

This separates two hypotheses that otherwise confound each other:

```text
better experiential structure
versus
better LoRA supervision for the same structure
```

Touches/repetitions are write strength, not independent support. The first
recipe may use measured starting points (roughly 24 touches for simple atomic
facts and a larger allocation for relational/operator facts), but touch count,
view count, and token budget remain reported experimental axes.

## Broad dream, narrow thinker

The thinker is a goal-conditioned, DFS-like controller over an immutable
memory snapshot. One call emits one operation:

```text
FORM_SUBGOAL
QUERY
FOLLOW
HYPOTHESIZE
PREDICT
REVISE
BACKTRACK
REQUEST_DREAM
RELEASE
DEFER
```

It follows one dependency branch, retrieves one immutable semantic claim or
conflict/`NOT_FOUND`, updates a working hypothesis, and either descends,
backtracks, releases, or defers. Thinking is narrow by objective, not by
capability. It may discover a useful scratch connection; only a later dream
can promote it into durable memory after independent derivation.

## Thinker-to-dream feedback is attention, not evidence

At a think boundary, a mechanical allowlist projection may emit:

- one missing dependency;
- one conflict or weak-read record;
- one stalled-chain description;
- one provisional local hypothesis;
- one desired local relation that would unblock the branch.

The resulting agenda/frontier binds to the thinker trace hash and memory
checkpoint. It excludes released answers, expected answers, scorer/evaluator
output, free-form rationale, hidden proof material, and post-outcome state.

An agenda item may choose what a dream reactivates. It cannot be cited as
evidence. Example:

```text
thinker agenda: need(source_S, affects, target_T)       # selection only

eligible memories: V routes S; closing V changes T

later dream: S affects T, cites the two eligible memories
```

Copying the thinker proposition without those citations is invalid. Its depth
is recomputed from the cited semantic/evidence parents; no thinker depth is
inherited.

Environment feedback is different. An observed action outcome becomes a new
immutable public experience at the next WAKE boundary. Cognitive feedback and
environment feedback must never share a record type.

## Immutable phase barriers

The cyclic artifact order is:

```text
DREAM_k
  -> freeze semantic snapshot
REALIZE_k
  -> freeze realization/touch manifest
MEMORY_k
  -> freeze text/adapter checkpoint
THINK_k
  -> freeze thinker trace
COGNITIVE_FEEDBACK_k
  -> freeze non-evidentiary agenda
DREAM_(k+1)
```

If an action is executed after thinking:

```text
ACT_k -> ENVIRONMENT_FEEDBACK_k -> public EXPERIENCE_(k+1)
```

No artifact may be retroactively edited after a later phase has seen its hash.
No adapter, graph, KV cache, optimizer, retrieval index, or working state may
cross `(world_id, skin_id, life_id)` boundaries.

## Required ontology

The new contract keeps distinct IDs and ledgers for:

1. immutable public experience events;
2. semantic concepts;
3. canonical semantic edges;
4. derivation events;
5. append-only epistemic status events;
6. realization specifications;
7. touch plans;
8. memory checkpoints;
9. thinker states and steps;
10. working hypotheses;
11. confusion/desire/dependency records;
12. non-evidentiary dream agenda items;
13. immutable phase barriers.

The graph is an audit shadow. The model sees bounded local content, stable
citation handles, and allowed epistemic status—not global topology, hidden
proof paths, or scorer-side depth.

## Depth and growth are separate measurements

No single `depth` number is sufficient. Report:

- `derivation_lineage_depth`: transformations in the provenance DAG;
- `supported_derivation_depth`: lineage using model-supported parents;
- `semantic_structural_hops`: unique semantic edges on a concept path;
- `independent_support_depth`: depth supported by disjoint evidence sets;
- `task_dependency_path_coverage`: scorer-side proof components connected
  after commitment, reporting-only;
- `thinker_compositional_depth`: distinct memory edges and scratch
  hypotheses on the released answer path;
- `realization_count` and touches, always separate.

Same-endpoint paraphrases, repeated hub facts, cyclic reformulations,
revisions, duplicate derivations, and realization fan-out do not demonstrate
structural growth.

## First calibrated schedule

Counterfactual Confluence v0.3-R is a small interface instrument. For its 46
atomic experiences, the target fixed budget is:

```text
46 WAKE semantic calls
+ 22 periodic breadth/depth REACTIVATE calls
= 68 intake calls

+ 16 target-blind sleep calls
-> MEMORY_0
-> identical intermediate THINK_0 in every arm
+ 16 final sleep/daydream calls
-> MEMORY_1
-> untouched final paired goal
```

Conditions differ only in how the final 16 dream calls are selected:

1. `no_feedback`: discard the think agenda; intrinsic breadth selector;
2. `agenda_feedback`: use the typed agenda for selection;
3. `shuffled_feedback`: use a paired other-world agenda;
4. optional oracle agenda, labeled ceiling.

Every arm pays for the same intermediate thinker and has matched maximum
dream/think calls and reported tokens. Early release is not padded with fake
calls; actual compute is also reported.

The scheduler must support arbitrary repeated cycles even when the first
experiment instantiates only one feedback transition.

## Benchmark ladder

### Rung 0: original v0.3 preservation

Preserve the current generator and its findings. It is an 8/10 causal
interface calibration, not a recurrent or scale benchmark. It contains only
46 episodes (about 669 words/~1.1k tokens), a development-fitted passive
signature lookup reaches about 22.3% held-out versus an ~8.5% majority, and
two late intervention effects are adjacent/complementary. Do not silently
rewrite this history.

### Rung 1: v0.3-R repair

Create new files. Require paired-twin scoring, independently generated and
temporally dispersed control interventions, held-out shortcut predictors,
local-window ambiguity, proof-edge removal ablations, and an intermediate
non-answer operational probe that can create a useful agenda. The final paired
goal remains unseen until after the final checkpoint.

V0.3-R tests causal information flow and recurrence. Raw iterative RAG solving
it is not a failure. No LoRA-necessity or beyond-context claim is permitted.

### Rung 2: gold text thinker

With gold local semantic edges and no final-answer memory, certify dependency
queries, backtracking, request-dream/defer behavior, paired reconstruction,
and cited release chains. A missing-edge fixture must defer or request a dream,
not fabricate.

### Rung 3: recurrent text organism

Compare no feedback, agenda feedback, shuffled feedback, and labeled oracle
agenda. Measure agenda consumption/closure, semantic growth, proof-path
availability, paired-both-correct, CHANGE/STABLE accuracy, read-plan quality,
and defer calibration. Do not proceed merely because the gold thinker works.

### Rung 4: fixed-corpus realization and transport

Freeze one known-good semantic snapshot. At equal semantic content and total
touches compare canonical repetition, surface variation, relational lenses,
and shuffled cue edges; then compare identical connected text and per-life
LoRA reads. LoRA is mounted only for atomic recognition reads and unmounted for
clean-base composition.

### Rung 5: interleaved LoRA organism

Rebuild the causal-reference adapter from the clean base at every checkpoint
using the cumulative eligible semantic snapshot and frozen realization/touch
plan. This is cumulative reconsolidation, not yet an efficient incremental
online update. Compare with no refresh, raw episodic LoRA, shuffled LoRA,
connected text, and raw iterative RAG.

### Rung 6: long-life Confluence

Use many reusable targets, valves, goals, distractors, exceptions, and
sequential goal revelation. Evaluate at measured lifetime points around and
beyond the frozen model's actual context capacity. Sweep strong RAG read and
compute budgets; measure saturation rather than assuming it. This is the first
rung that can support persistence/scaling claims.

### Rung 7: Action World

The agent chooses information-seeking actions; their outcomes change later
dreaming and memory; improved memory changes future actions and therefore the
future experience distribution. This is the complete online-learning flywheel.

## Required ablations

At minimum:

- raw experience, wake-only transcription, recurrent target-blind dreaming,
  recurrent agenda dreaming, shuffled agenda, direct-structure ceiling;
- no second-order edges, no revision/reinforcement;
- one canonical realization repeated, surface variations, relational lenses,
  shuffled connected cues, graph-only, realization-only;
- connected text, raw iterative RAG, raw LoRA, trajectory-to-QA LoRA,
  connected LoRA, shuffled-binding LoRA;
- one-pass thinker, DFS thinker, no backtracking, no request-dream, agenda with
  no execution, daydream with no memory refresh, gold read plan;
- clean cumulative rebuild versus later incremental replay.

## Claim boundary

A positive v0.3-R result may support:

> Goal-conditioned, non-evidentiary thinker feedback can guide later broad
> dream consolidation toward missing local causal connections; those
> connections can be encoded through a per-life adapter and reconstructed by a
> later thinker for paired counterfactual decisions.

It does not show learned scheduling, LoRA-native structure discovery, LoRA
necessity while the life fits context, efficient incremental updating,
policy-selected exploration, continued improvement with lifetime, or baseline
saturation.

## Implementation and review order

```text
architecture-change intake record
-> new cyclic schemas/contracts and adversarial tests
-> v0.3-R generator and shortcut audit
-> gold DFS thinker
-> recurrent text organism
-> realization compiler
-> fixed-corpus LoRA transport
-> interleaved LoRA development run
-> fresh contract/science/ICLR review + author advocate
-> frozen replication
-> long-life benchmark
```

Every material Rohin idea first produces a graph delta, loop delta, claim
delta, information-visibility matrix, independent interpretations,
cross-critiques, preserved dissent, and an adjudicated implementation
allowlist. Executable science cannot bypass that intake record. A reviewer
attacks the work; an author advocate states the strongest defensible case but
cannot erase findings or authorize promotion.
