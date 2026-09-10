# Draft transition: recurrent one-connection micro-dream organism v0

Status: design-only and GPU-blocked. A fresh review of the first implementation
found artifact-binding defects, and the subsequent game audit found a
target-signature shortcut in Semantic World v0.2. No frozen recurrent snapshot
is authorized until both classes of defect are repaired and independently
reviewed.

Architecture update (2026-08-31): this file specifies the semantic-dreaming
subsystem, not the complete organism. The controlling cyclic design is
`interleaved_organism_v1.md`, which adds semantic-node versus LoRA-realization
separation and an immutable thinker -> non-evidentiary agenda -> later dream ->
memory refresh -> rethink path. No implementation may treat the terminal
thinker in this document as the final system boundary.

This experiment supersedes interpreting v5 as a test of the intended dream
mechanism. It does not supersede v5 as a task-family-scaffolded direct-parent
proposal ceiling/reference diagnostic.

## Architectural claim under test

Dreaming does not have to solve the evaluation question or emit a complete
parent structure. It incrementally grows an experiential memory by adding or
revising roughly one local connection per cycle. A later dream can retrieve an
earlier connection and extend it by one hop, so depth grows across reactivation
like adding a leaf to a search tree. The per-life LoRA transports/compresses the
resulting connected state; it is not credited with discovering the structure.
A goal-conditioned thinker then retrieves and composes the relevant path,
forming provisional task-specific hypotheses when needed.

The causal chain is:

```text
temporally ordered public experience
  -> recurrent local memory growth
  -> connected typed corpus with provenance
  -> text or per-life LoRA transport
  -> goal-conditioned iterative retrieval/reconstruction
  -> held-out construction
```

A positive result supports this narrow information-flow claim. It does not yet
show a learned scheduler, learned dream/think policy, online action improvement,
or lifelong scaling.

## Unit of dreaming

There are two legal triggers:

```text
WAKE(E_t): a new public episode becomes available
REACTIVATE(M_j): sleep/revisit starts from an earlier memory node
```

A wake micro-dream sees only:

```text
current public episode E_t
+ bounded retrieval of prior nodes M_<t
+ persistent agenda/status
```

A reactivation micro-dream sees its triggering prior node, a bounded retrieval
of other prior nodes, and the agenda/status. It receives no fabricated current
episode. Every cited episode/node must temporally precede the micro-dream.

It must not see a flattened lifetime table, future episodes, evaluation goal,
target-parent menu, candidate parent subsets, hidden roles/parents/answers,
proof graph, offline verdict, or target-scoring evidence.

It emits exactly one operation:

```text
ADD: <one local edge/claim> | CITES: [E_t and/or M_i...]
REVISE: <one prior node> -> <one corrected local edge/claim> | CITES: [...]
OPEN_QUESTION: <one local uncertainty>
PASS
```

The claim may be a witnessed fact, similarity/difference, role/class relation,
operator regularity, causal/parent fragment, exception, or connection between
two earlier abstractions. It need not be a generalization and must not be
required to answer the eventual task. A modest connection that later becomes
useful is success.

The Semantic World claim grammar permits only one semantic edge per node. A
node may relate one entity/class/place to one other entity/class/place or add
one property/prediction. It may not serialize a source subset, name multiple
candidate parents for one target, contain a target-specific multi-parent
derivation, or contain any held-out `(target, entity)` outcome. The complete
parent set is a temporary thinker hypothesis, never a required memory node.

Every node stores:

```text
node_id, world_id, skin_id, life_id, microdream_index, trigger,
operation, claim, claim_kind, cited_episode_ids, cited_node_ids,
retrieved_node_ids, prediction, confidence, status,
depth, supersedes, raw_completion, prompt/output token counts
```

- Episode-only nodes have depth 1.
- A depth-`d+1` node must cite at least one earlier node of maximum depth `d`.
- Depth 2+ without an earlier-node citation is invalid, never silently repaired.
- The event log is append-only. `REVISE` creates a new node with
  `supersedes=[old_id]`; it never mutates or deletes the older claim. Later
  public experience may support, revise, split, or contradict a node. Offline
  truth never changes the live memory.
- Repetition of the same evidence does not create false depth. Independent new
  support increments support metadata; it is not a new semantic node.
- One local reflection over the cited, temporally available evidence is allowed.
  No FactorSolver or exact public-evidence gate may rank, erase, or steer nodes
  in the principal arm.

The reader returns the latest non-superseded state plus explicitly linked
conflicts; it never silently hides contradictory history. A query may return
both live conflicting nodes or `NOT_FOUND`.

The scheduler is fixed and inspectable for this paper: process each episode in
order; retrieve by entity/relation overlap plus unresolved agenda; run a bounded
number of wake micro-dreams; periodically reactivate a supported/provisional
node without inventing new evidence; stop at the predeclared per-life
call/token budget. Its trajectory is future LOOP adapter data, not evidence
that scheduling is learned.

The honesty ladder uses the same claim grammar. Conditions compared for a
causal contrast use the same wake/reactivation proposal schedule and proposal
call/token budget. Self-check conditions incur an additional, separately
reported reflection budget; they are not mislabeled as total-compute matched.
A matched-total-compute sensitivity later reallocates that overhead to ordinary
ungated proposal/reasoning calls:

1. `no_gate_no_drift`: every validly formatted wake node persists; no sleep
   reactivation (calibration only).
2. `no_gate_drift`: every validly formatted wake/reactivation node persists.
3. `self_check_no_drift`: a separate model reflection labels each wake node
   `supported/contradicted/unresolved` using only its cited, temporally available
   public evidence and earlier nodes; no sleep reactivation.
4. `self_check_drift`: the same self-check plus later `REACTIVATE` cycles over
   earlier memories (principal condition).

All formatted model-produced nodes remain in the audit log. In the `no_gate_*`
conditions, all formatted nodes enter the corpus. In the self-check conditions, model-labeled
`supported` nodes enter the durable corpus; `unresolved` nodes remain in the
live provisional/agenda state and can be revisited, while `contradicted` nodes
remain as explicit negative history. A false model-supported node stays in the
durable corpus and its downstream cost is measured. Offline truth scores only
after commitment and never selects the corpus.

Consequently, `REVISE` has deliberately different commit semantics across the
honesty ladder: an ungated revision immediately becomes the no-gate arm's live
latest claim, whereas a self-check revision leaves the prior claim live unless
the replacement is labeled `supported`. Contradicted or malformed-check
replacements remain in the audit history but cannot become reactivation
triggers. Report raw structural depth and fully supported-lineage depth
separately; only the latter can satisfy the dream-development gate.

## Memory construction and transport

The durable memory is the condition's typed, model-accepted node set, not a
free-form final summary. Only the canonical `(kind, left, relation, right)`
edge is exposed to later retrieval and text/LoRA training. The model's
free-form rationale and prediction remain in the immutable audit trace but
cannot steer retrieval or smuggle a multi-edge solution into the corpus. Each
LoRA training line maps back to one or more node IDs. Canonical atomic forms,
controlled paraphrases, reverse cues, and fixed exposure counts are allowed;
new semantic content is not. Preserve a line-to-node manifest.

Initialize a new MEMORY adapter for every `(world_id, skin_id, life_id)` and
destroy all model-visible lifetime context before evaluation. No adapter, KV
cache, retrieval store, or gradient crosses lives. The base and prompted LOOP
controller remain frozen.

Text and LoRA use one frozen typed candidate-recognition grammar. Every
candidate set is formed only from public workshop vocabulary, committed memory
claims, and fixed public distractors. It is independent of hidden parents,
target truth, scorer output, and the evaluation answer; log the complete
candidate set for every query. The LoRA is mounted only for atomic memory
reads; the clean frozen base performs working state composition after the read.
A LoRA failure is attributed to transport only when the identical
query/candidate plan succeeds against the text corpus.

The LoRA is evaluated as persistence/compression and associative access. Any
apparent generalization must be attributed to the complete dream-memory-think
trajectory unless an ablation isolates it.

The one-line-per-node corpus is now only the canonical semantic view. The
cyclic v1 contract adds a separate realization/touch manifest. Multiple QA,
partial, reverse, situated, or contrast views of one edge do not create new
nodes, support, or depth. A view that asserts new semantic content must return
to the dream proposal path with its own eligible provenance.

## Goal-conditioned thinker

The thinker is the reverse flow, but not a literal decompressor. It maintains a
working state and repeatedly chooses one operation:

```text
QUERY one dependency
UPDATE or REVISE one working hypothesis
REPLAN
ANSWER
DEFER
```

Each query resolves through typed candidate recognition and returns an
immutable atomic memory claim plus provenance, an explicit conflict set, or
`NOT_FOUND`. The thinker may traverse several nodes, combine them, and form the
parent/causal hypothesis in working state. It may not ask the held-out goal
verbatim or query any answer-equivalent form of the exact held-out
`(target, entity)` outcome. It may not accept a direct final-answer memory
without prerequisite support or write the final answer into long-term memory.
The answer is released only after an explicit stopping operation or budget
exhaustion.

## Minimal matched arms

Post-design audit correction: the v0.2 D3 answer cannot be the organism
endpoint because its visible target signature determines the held-out answer
without the intended causal path. The arms below remain the intended causal
decomposition, but their headline endpoint moves to Counterfactual Confluence
v0.3 as specified in `counterfactual_confluence_v03.md`. V0.2 may be retained
only as a non-headline local-edge/parent-recovery diagnostic with an explicit
target-signature shortcut baseline.

All arms share episode order, dream calls/tokens, corpus budget, reader budget,
executor, answer format, and the twelve Semantic World v0.2 D3 goals unless the
arm definition removes a component. This first recurrent transition is scoped
to Blendyland-grade construction. The unchanged v0 D0-D2 goals return only in
the later full-organism battery; they are not silently spliced into this run.

The first implementation also undersupplied dream opportunity: it issued one
WAKE operation for an episode even when that episode contained 2--15 atomic
observations, and its reactivation policy always selected the newest eligible
node. That is a runner calibration, not the principal version of recurrent
dreaming. The repaired condition must either atomize the public stream or
predeclare multiple duplicate-guarded WAKE operations per episode, and it must
branch reactivation across a balanced uncertainty/salience frontier. Dream
opportunity, duplicate rate, node coverage, and reactivation coverage are
reported explicitly.

The principal substrate/thinker matrix uses `self_check_drift` corpora. The
same connected-text and connected-LoRA arms must also be run with
`no_gate_drift` corpora as the mandatory filter/false-memory-cost comparator at
matched reactivation compute. `self_check_no_drift` isolates the effect of
reactivation; `no_gate_no_drift` is calibration. Neither can replace the
`no_gate_drift` comparator or the `self_check_drift` principal condition.

| Arm | Purpose |
|---|---|
| `none_iterative` | Thinker-only floor with no lifetime memory. |
| `gold_text_iterative` | Correct public operator/role/source leaves, no final answer; certifies iterative thinker capability. |
| `gold_text_onepass` | Same gold leaves, one pass; isolates the benefit of recursive reconstruction. |
| `raw_text_rag_iterative` | Iterative episodic retrieval over raw public trajectories under the matched retrieved-token budget. |
| `raw_lora_iterative` | Raw episodes in a per-life LoRA; tests retention without dreamed connections. |
| `trajectory_qa_lora_iterative` | Direct trajectory-to-QA distillation under the same adapter/write budget (TMEM-style control). |
| `connected_text_iterative` | The exact connected node corpus via immutable text retrieval. |
| `connected_lora_iterative` | Principal arm: the same node corpus transported through LoRA. |
| `shuffled_lora_iterative` | Same size, templates, exposure, claim kinds, and entity frequencies, with bindings/citations rewired. |
| `connected_lora_onepass` | Same adapter and read budget, but one retrieve/compose pass instead of iterative reconstruction. |

The no-memory/raw conditions cannot literally spend dream calls on absent
dreaming. Report both component budgets and total model calls/tokens; include a
matched-total-compute sensitivity where unused dream compute is allocated to
extra standard-agent inference rather than dummy/discarded calls.

Optional, always non-headline: full public context while it fits; v5 direct
parent proposer; exhaustive branch/proof-leaf controller; oracle leaves.

Primary decomposition:

```text
connected_text_iterative vs connected_lora_iterative
  = transport conditional on matched atomic read fidelity

connected_lora_iterative vs raw_lora_iterative and shuffled_lora_iterative
  = value of connected, correctly bound dream structure

connected_lora_iterative vs connected_lora_onepass
  = value of iterative goal-conditioned reconstruction

gold_text_iterative vs gold_text_onepass
  = thinker capability at fixed known-good, non-answer memory
```

## Leakage boundary and splits

- Develop on complete latent world seeds/families; freeze prompt, scheduler,
  retrieval, corpus rendering, adapter recipe, query grammar, and budgets before
  untouched worlds. Every skin of a latent world seed belongs to the same
  split; skins are reported conditions, not independent held-out samples.
- Remove hidden truth, solver artifacts, scorer labels, target answer cells,
  parent menus, and proof graphs from all model-visible files and targets.
- Offline scoring begins only after `episodes`, `microdreams`, corpus, adapter,
  and thinker traces commit. It cannot change the live trajectory.
- Audit both literal and canonicalized renderings so no corpus line contains an
  exact held-out `(target, entity)` answer, answer-equivalent query, or direct
  rendering of an evaluation question.
- Public workshop/calibration events are allowed only when they are genuinely
  part of the lifetime and identically available to every arm.

## Required artifacts

1. `episodes.jsonl`: exact temporal public stream and hashes.
2. `microdreams.jsonl`: visible event, retrieved IDs, operation, raw completion,
   claim/revision, citations, status, depth, agenda change, and token use.
3. `corpus_manifest.json`: every text/LoRA line to node IDs and explicit
   semantic edge, rendering, paraphrase/exposure count, adapter hash, and read
   probes. The shuffled control rewires the model-visible semantic binding—not
   audit-only citations—while preserving templates, line counts, exposure, and
   marginal entity frequencies; its query answers must actually change.
4. `thinker_traces.jsonl`: goal, working state, queries, immutable returned
   claims/IDs, revisions, stop/defer/answer, raw completions, budgets, and score.
5. `offline_scores.json`: hidden claim truth and task answers, created only
   after the four causal artifacts commit.

## Metrics and gates

Dream growth:

- one-operation compliance and temporal-citation validity;
- node/depth histogram, first-emergence episode, real depth-2+ rate;
- support, revision, contradiction, and retraction rates;
- offline precision/recall by claim kind and prerequisite-path availability;
- false-memory cost and shuffled-binding degradation.

Transport:

- exact, reverse, paraphrase, and partial-cue atomic reads by claim kind;
- text-to-LoRA agreement, prerequisite-path retention, malformed/confabulated
  read rate.

Think/organism:

- D3-v0.2 target accuracy; valid cited-chain and prerequisite-before-answer
  rates (later full-organism runs report D0-D3 separately);
- useful-query, `NOT_FOUND`, repeat-query, revision, defer, operation, and token
  budgets;
- iterative-minus-one-pass accuracy at fixed memory and read quality.

Predeclared gates:

1. **Static:** 100% temporal citation validity in deterministic fixtures; one
   operation/node limit; no forbidden target/menu/answer artifacts; every
   training line auditable.
2. **Dream development:** report depth separately from usefulness. Require
   valid depth-2+ nodes citing actual prior nodes, supported lineage across more
   than rephrasing, coverage of at least two required local claim kinds, and
   scorer-side prerequisite-path availability without a direct held-out answer.
   Offline scoring reports this but never selects the corpus. If absent, report
   a null mechanism result; do not substitute direct parent search.
3. **Transport:** atomic read recall >= .85 and malformed/confabulated reads <=
   .05 before interpreting D3-v0.2 LoRA results (or D0-D3 in the later full
   battery).
4. **Thinker:** at fixed known-good memory, iterative reconstruction improves
   over one-pass and retrieves prerequisite nodes rather than guessing.
5. **Organism:** on untouched whole worlds, `connected_lora_iterative` beats
   both raw and shuffled LoRA by >= .05 absolute under paired analysis and
   matched compute. Report every seed/skin; do not pool away failures.
6. **Promotion:** only then move to Action World. LOOP-adapter training remains
   a separate later experiment using the preserved operation trajectories.

Any claim that weights help beyond context additionally requires a later
lifetime-prefix condition whose available memory actually exceeds the frozen
context/retrieval budget. Small-memory text-vs-LoRA equality is only a transport
result.

## Relation to v5

V5 uses independent, task-family-scaffolded parent proposals followed by an
exact public-evidence gate. Its nested sample prefixes measure proposal recall
and contamination as compute increases. They are not dream cycles because one
parent call does not consume and extend the previous call's memory. V5 remains
useful as a ceiling, failure diagnostic, and possible curriculum source. The
recurrent experiment above tests whether the architecture can grow useful
intermediate structure without directly requesting the final latent structure.
