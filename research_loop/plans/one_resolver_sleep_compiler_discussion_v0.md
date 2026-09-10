# One resolver, two traversal modes, and an evidence-bound sleep compiler

Date: 2026-08-31 PT. Status: **discussion proposal only**. This file records
Rohin's afterimage/compression insight and the independent systems,
benchmark, and adversarial interpretations. It does not supersede
`interleaved_organism_v1.md`, authorize implementation, or promote a model or
GPU run. Material adoption requires a new architecture-intake chain and
explicit human ratification.

## Motivation, stated conservatively

Recall and perception can be reconstructive rather than literal playback.
Under finite working context, memory capacity, and transfer bandwidth, a
system may benefit from retaining task-relevant invariances while discarding
episode-specific detail. The pink-pig/green-frog afterimage is an intuition
pump for state-dependent reconstruction, not biological evidence for semantic
memory consolidation or dreaming.

The hypothesis is not that arbitrary loss creates intelligence. Useful
compression depends on which invariances survive, the model's prior, and the
future task distribution. Misaligned compression can alias facts, regress to
priors, and create confident intrusions.

## Candidate loop

```text
EXPERIENCE
  -> SLEEP_TRAVERSE(mode, bounded checkpoint)
       -> traversal_record
       -> connection_candidate*                 # non-evidentiary
       -> traversal_statistics                  # non-evidentiary
  -> SLEEP_COMPILE(eligible evidence, candidates, frozen public rules)
       -> consolidation_plan
       -> semantic commit and/or retrieval shortcut
       -> realization/touch/GC plan
  -> MEMORY_CHECKPOINT (explicit authority + optional text/LoRA access view)
  -> THINK_TRAVERSE(mode, goal, bounded checkpoint)
       -> release/action/defer
       -> traversal candidates/statistics       # selection only
  -> COGNITIVE_FEEDBACK
  -> next SLEEP_TRAVERSE

ENVIRONMENT OUTCOME
  -> new immutable public EXPERIENCE            # the only new evidence
```

### Discussion amendment: associative fan-out and local checking

Rohin's refinement is that the parametric memory may supply much of the
breadth implicitly, while the explicit thinker follows a narrow path through
what becomes salient.  The formal proposal calls this an **associative
neighborhood**, not BFS.  Literal BFS would require an observable frontier,
visited set, depth ordering, and coverage guarantee; a LoRA read may instead
be blended completion, recognition scores, or prior-driven intrusion.

```text
THINK_TRAVERSE
  goal + bounded checkpoint
  -> ASSOCIATIVE_READ(cue, top_k)              # proposals/known handles
  -> QUERY / FOLLOW / BACKTRACK                # explicit, auditable DFS
  -> HYPOTHESIZE / PREDICT / CHECK
  -> RELEASE / DEFER

SLEEP_TRAVERSE / DREAM
  episode, anomaly, confusion, or residual cue
  -> ASSOCIATIVE_READ(cue, top_k)
  -> replay / cross-episode comparison / local re-derivation
  -> HYPOTHESIZE / PREDICT / CHECK
  -> connection candidates + traversal statistics

SLEEP_COMPILE
  exact eligible evidence + candidates + frozen public rules
  -> deterministic evidence-bound consolidation plan
```

DREAM therefore need not enumerate every branch.  Its residual scientific
job is to test whether broad offline replay, cross-episode reorganization,
contradiction revisiting, or local re-derivation adds useful structure beyond
wake traversal plus deterministic compilation.  `no dream`, `replay only`,
`cross-episode re-derivation`, and `breadth-biased dream` remain required
ablations; DREAM is allowed to turn out unnecessary as a distinct content
generator.

`CHECK` is model metacognition, never an oracle or source of evidence:

```text
candidate + bounded committed snapshot (candidate excluded)
  -> predict a consequence or seek a counterexample
  -> CONSISTENT | CONTRADICTED | UNRESOLVED
  -> continue / revise / defer / request evidence
```

A same-model CHECK is explicitly a correlated critic.  `CONSISTENT` means
only that this bounded check found no contradiction.  It may guide search,
stopping, and calibration, but cannot promote a claim.  Reserve
**verification** for deterministic entailment from cited public evidence or
for an external outcome observed after a prediction/action was committed.

The ledger must keep these non-collapsible statuses: `PROPOSED`,
`WELL_FORMED`, `GROUNDED`, `MECHANICALLY_ENTAILED`,
`EMPIRICALLY_SUPPORTED`, `CRITIC_APPROVED`, `COMMITTED`, and `RELEASED`.
Critic approval alone is excluded from factual LoRA training.  Any retained
provisional hypothesis belongs in a separately typed hypothesis store/view
and cannot authorize a factual release until independently promoted.

THINK and SLEEP_TRAVERSE may share a typed transition kernel:
`retrieve -> follow -> hypothesize -> predict -> revise/backtrack -> stop`.
They still differ in invocation, objective, grounding, budget, and output
permissions. Whether they should share weights is an experiment, not an
architectural fact.

SLEEP_COMPILE is not a hidden reasoner or oracle. It may enforce schemas,
scope, citations, deduplication, and explicitly public executable rules. It
may reject or defer. Where a claim cannot be mechanically derived from
eligible evidence, it remains provisional/non-authoritative.

## Candidate audit objects

1. `resolver_invocation`: mode, scope/checkpoint hashes, goal or target-blind
   trigger, visible handles, budgets, permissions, model/reset provenance.
2. `traversal_record`: append-only typed reads, misses, hypotheses,
   backtracks, and terminal operation; invocation-bound and replayable.
3. `connection_candidate`: typed local proposition with cited eligible
   handles; always `NON_EVIDENTIARY_CANDIDATE` until independently derived.
4. `traversal_statistics`: mechanically recomputable visits, co-retrieval,
   stalls, recency, goal diversity, and successful-path counts.
5. `consolidation_plan`: compiler/version/input hashes and typed items:
   `SEMANTIC_COMMIT`, `RETRIEVAL_SHORTCUT`, `REALIZATION`, `TOUCH`, `DEFER`,
   or `GC`.

## Two kinds of connection

- A `retrieval_shortcut` records that a path or cue is useful for finding
  related material. Co-retrieval and traversal frequency may create or weight
  it. It is never a belief, premise, support event, or derivation-depth unit.
- A `semantic_shortcut` is a new world claim such as `a -> z`. It requires a
  licensed composition rule, supported premises, provenance, scope and
  preconditions, counterexample handling, and invalidation dependencies.

`a -> b` and `b -> z` do not generically entail `a -> z`; transitivity is a
property of a typed relation, not of graph shape. Frequently retrieving a
claim also does not make it true. Traversal may choose what to re-examine or
how many write touches to allocate, but it cannot support its own promotion.

The explicit semantic graph/epistemic ledger remains authoritative. LoRA,
RAG, and retrieval indexes are derived access or transport artifacts. An
uncited relation generated from an adapter is not authoritative memory.

## Minimal decisive ablations

At matched base model, calls, tokens, retrieval views, candidate budgets,
admission rules, semantic capacity, and write touches:

1. `compiler_only`: witnessed/accepted semantics -> dedup/multi-view writes;
   no resolver-created semantic edge.
2. `specialized_resolvers`: distinct DREAM connector and THINK controller.
3. `shared_resolver`: one operation kernel/weights with an explicit mode.
4. `shared_no_durable_write`: shared search, but candidates remain scratch.

First run these with explicit text/graph memory. Then transport the identical
frozen semantic corpora through LoRA. This separates reasoning, connection
formation, consolidation format, and parametric transport.

Cross these with three additional matched ladders:

- `CHECK`: none; same-model correlated check; fresh/separate critic check;
  deterministic public mechanical check as an offline ceiling.
- content/substrate: atomic-only; the same atoms in multi-view realizations;
  dream-connected licensed shortcuts; shuffled connected controls -- each
  through explicit text/graph access and LoRA.
- DREAM residual: no dream; replay/selection only; cross-episode
  re-derivation; breadth-biased; depth-biased; shuffled episode grouping.

The associative-memory claim is measured as next-node/frontier recall@k,
false branches, rare-branch recall, missing-edge abstention, supported-path
completion, and final action value at matched read and controller budgets.
Direct-answer accuracy alone cannot distinguish associative fan-out from
memorized recipes or base-model priors. End-to-end compute includes dream
generation, compilation, LoRA training, checks, retries, and final traversal.

Required attacks include shuffled/frequency-matched co-retrieval, forged
candidate/statistics, thinker-answer laundering, public-evidence removal,
counterexamples after shortcut creation, rearranged goals where cached final
recipes fail, mode swapping, cross-life state, snapshot mutation, and
objective interference between THINK and SLEEP_TRAVERSE.

Report exact leaf recall, intrusion/confabulation, grounded edge
precision/coverage, defer calibration, fixed-budget reasoning cost,
cross-goal shortcut reuse, conflict/revision behavior, constructive accuracy,
and downstream action value separately.

## Claim boundary

Proposal-level hypothesis:

> A shared resolver interface may support goal-conditioned online traversal
> and broad offline connection search, while an evidence-bound consolidation
> compiler converts independently supported semantics and licensed hot paths
> into compact explicit and parametric access views.

Not currently supported:

- that THINK and dreaming are fundamentally the same cognitive process;
- that afterimages explain dreaming or memory consolidation;
- that compression or parameter reduction inherently improves generalization;
- that co-retrieval is evidence;
- that unified weights avoid objective interference;
- that LoRA implicitly replaces a reliable semantic graph;
- that current v0.3-R or Blendy instruments establish long-life compression,
  action improvement, beyond-context value, or baseline saturation.

## Preserved dissent

A specialized dreamer may outperform a shared resolver. Compiler-only may
explain the gain. Explicit declarative memory may remain the primary useful
substrate. LoRA may add no value on short games. Apparent generalization may
come from pretrained priors and structured supervision rather than the
proposed bottleneck. These alternatives are first-class experimental
outcomes, not implementation failures.
