# Architecture change consensus: interleaved organism

Change id: `chg_20260831_interleaved_organism`  
Status: `implementation_authorized` (not science-run authorized)  
Human authority: Rohin explicitly requested graph/loop interpretation,
independent-agent discussion, consensus, implementation, and ICLR-style audit.

## Raw design correction

The first dream does not have to discover a complete Blendy/parent structure.
Dreaming broadly grows local associative nodes and edges, potentially one hop
per revisit. Goal-conditioned thinking follows narrower chains and can expose
what is missing. That unresolved dependency or desired connection should feed
a later dream, allowing the organism to converge over repeated
dream--think--dream cycles.

Dreaming also enriches how accepted memories are written into LoRA: one
semantic memory may be rendered through several query, reverse, partial,
situated, or contrast views and receive repeated touches. Semantic graph
growth and write-realization fan-out are distinct operations.

Every material design idea must first be mapped onto the architecture graph,
learning loops, visibility boundaries, benchmark, and claims. Independent
agents with systems, contract, and reviewer perspectives must draft before
cross-critique and adjudication. Implementation and GPU work occur only after
the resulting delta is explicit.

## Context consulted

- `research_notes/32_v2_experiment_design.md`, especially the daydreamer,
  incremental associative dreaming, adaptive thinker, unified loop, and
  organism rulings;
- `research_notes/33_semantic_world_gpu_constraints.md`;
- `research_notes/35_goalposts_paper1.md`;
- `research_notes/41_capacity_compression_and_loop_training.md`;
- `research_notes/42_system_thesis_and_experiment_map.md`;
- `alchemy/v2_out/mini_ledger.md`;
- current microdream prompts, runner, contract, artifact publisher, scheduler,
  v0.3 generator, tests, and original organism code;
- A-MEM and TMEM primary-paper descriptions for related-work disambiguation.

Exact content hashes are intentionally deferred until the implementation is
quiescent. No current approval may be reused as a freeze receipt.

## Independent interpretations

### Architecture advocate

Interpreted the design as two orthogonal dream operations plus a recurrent
return arrow:

```text
experience -> semantic BFS-like growth -> realization fan-out -> memory
-> goal DFS-like thinker -> typed frontier -> later dream -> refreshed memory
-> rethink
```

Required typed experience, concept, edge, derivation, epistemic,
realization/touch, checkpoint, think-state, working-hypothesis, confusion,
desire, agenda, and phase-barrier objects. Recommended deterministic rendering
with the dreamer choosing the edge/lens/connected cue.

### Contract auditor

Accepted the return arrow only when thinker feedback is selection-only and can
never satisfy evidence. Required immutable phase hashes, exact call replay,
cross-life isolation, node/realization separation, answer-laundering attacks,
and multiple depth metrics. Found that the current endpoint-overlap depth can
overcount same-endpoint paraphrases and hub chains.

### Skeptical ICLR reviewer

Accepted v0.3's collision twins as a strong causal interface, but rejected the
current game as a recurrent/LoRA-scale benchmark. Evidence:

- one terminal thinker and no thinker-to-dream transition;
- 46 episodes, 669 words, roughly 1.1k tokens;
- public atomic leaves make strong iterative RAG viable;
- passive-signature lookup about 22.3% held-out versus about 8.5% majority;
- adjacent complementary late intervention events;
- semantic nodes and write realizations are not operationally separated.

Required paired-both-correct scoring, learned held-out shortcut baselines,
intervention repair, feedback arms, and a later long-life tier.

## Cross-critique and consensus

All three reviewers accepted:

1. typed non-evidentiary thinker frontiers;
2. immutable `DREAM -> REALIZE -> MEMORY -> THINK -> FEEDBACK` cycles;
3. separate semantic and realization namespaces, budgets, artifacts, metrics,
   and ablations;
4. separate derivation, structural-hop, independent-support, task-path, and
   thinker-composition metrics;
5. v0.3 as calibration only;
6. v0.3-R in new files with paired scoring and stronger shortcut audits;
7. gold text thinker before autonomous dreaming or LoRA;
8. recurrent text organism before fixed-corpus LoRA transport;
9. long-life and Action World as separate later rungs.

Resolved qualifications:

- Cognitive feedback changes attention/selection only. Environment feedback
  is an immutable new public experience. They use different record types.
- The dreamer chooses a realization target/lens/connected cue; a deterministic
  compiler emits the principal training line. Free model prose is an ablation.
- Clean adapter rebuilds are called cumulative reconsolidation. They isolate
  corpus causality but do not demonstrate efficient incremental online update.
- V0.3-R merits a bounded development calibration after repair, not a
  paper-headline or LoRA-necessity interpretation.
- Both collision twins must be answered correctly as the primary paired
  metric. This does not require both twin interventions to have the same
  CHANGE/STABLE status.

Preserved reviewer warning: one hundred hand-scheduled calls over a ~1.1k-token
life are an overengineered ceiling/interface test, not evidence of efficient or
scalable dreaming.

## Authorized graph delta

Add audit-level objects and edges:

```text
ExperienceEvent -> DerivationEvent -> SemanticEdge
SemanticEdge -> RealizationSpec -> TouchPlan -> MemoryCheckpoint
MemoryCheckpoint -> ThinkState -> WorkingHypothesis/Confusion/Desire
ThinkState -> DreamAgendaItem (selection_only)
DreamAgendaItem -> later DerivationEvent (motivation only)
later eligible Experience/SemanticEdge -> later DerivationEvent (evidence)
MemoryCheckpoint_k -> PhaseBarrier -> MemoryCheckpoint_(k+1)
```

No thinker hypothesis, agenda item, realization, touch, scorer value, hidden
answer, or offline proof may become evidentiary support.

## Authorized loop delta

Implement a repeatable phase machine, initially instantiated as:

```text
46 WAKE + 22 periodic REACTIVATE
-> 16 target-blind sleep calls
-> MEMORY_0
-> identical intermediate THINK_0 in every arm
-> agenda kept/discarded/shuffled
-> 16 final dream calls
-> MEMORY_1
-> untouched paired final goal
```

The runtime must support additional cycles without redesign. Every condition
reports actual and maximum model calls, tokens, reads, realizations, touches,
and checkpoints.

## Authorized claim delta

Permitted after a positive v0.3-R result:

> Goal-conditioned, non-evidentiary thinker feedback can guide later broad
> consolidation toward missing local causal connections; those connections
> can be encoded in a per-life adapter and reconstructed by a later thinker for
> paired counterfactual decisions.

Forbidden at this rung:

- learned dream/think scheduling;
- LoRA discovering the semantic structure;
- LoRA necessity or scaling while the life fits context;
- efficient incremental online weight updates under clean rebuilds;
- policy-selected exploration or an improved experience distribution;
- baseline saturation, lifelong growth, or the complete continual flywheel.

## Authorized implementation sequence

1. architecture-intake schemas/validator/tests;
2. new cyclic organism schemas/contracts/adversarial tests;
3. v0.3-R generator, paired scorer, shortcut predictors, and CPU audits;
4. gold typed DFS thinker;
5. recurrent semantic text organism and feedback ladder;
6. realization compiler and matched realization ablation;
7. fixed-corpus text/LoRA transport;
8. interleaved cumulative-rebuild LoRA development calibration;
9. fresh artifact, science, and ICLR reviews plus author advocate;
10. frozen replication only after final adjudication;
11. separately designed long-life benchmark;
12. Action World flywheel.

## Current file authorization

Implementation may add new files under `research_loop/`, `lands/`, and
`research_loop/changes/chg_20260831_interleaved_organism/`; update controlling
research-plan documentation; and add tests. Existing v0.3 files and completed
run artifacts are preservation-only. No GPU launch, remote sync, lease action,
result tuning, holdout inspection, push, or paper claim promotion is authorized
by this record.

## Promotion gates

- all schemas/contracts pass adversarial CPU tests;
- v0.3-R passes at least 1,000 paired-world audits and declared shortcut gates;
- gold text thinker solves paired goals and defers on missing-edge fixtures;
- recurrent text feedback closes at least one agenda via independent evidence
  and improves its own post-dream path/decision relative to pre-dream;
- shuffled feedback does not give the same gain;
- fixed-corpus text and LoRA use identical semantic/query plans and achieve
  interpretable read-fidelity agreement;
- fresh contract, science, and ICLR-style reviews approve the exact frozen
  bytes.

Until then, GPU execution remains blocked.
