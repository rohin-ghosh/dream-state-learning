# Developmental experiential learning v2: executable pilot protocol

**Status:** proposed replacement for note 43 after independent adjudication.
Nothing in this document authorizes implementation or a GPU run until the
exact bytes and scope pass the repository architecture intake and Rohin
ratifies them.

## 1. Claim boundary

The pilot tests one claim:

> With a frozen base and a fixed generic agent loop, sleep-compiled per-life
> parametric memory can turn an agent's own action--outcome history into
> reusable semantic and procedural associations that improve held-out actions
> after the lived stream exceeds a fixed working-memory/read budget.

It does **not** test a learned thinker, learned dreamer, outcome critic, human
development, general intelligence, or autonomous scientific taste. Those are
later learning scales.

The three parameter objects are kept separate:

```text
theta_0 = frozen pretrained base and priors
phi     = shared loop policy: how to retrieve, think, act, sleep and stop
psi_l   = per-life MEMORY adapter: what life l encountered and inferred
```

For this protocol, `phi` is a frozen prompt/state machine shared by every arm
and life. Only `psi_l` changes within a life. A future LOOP adapter may learn
`phi` across many complete lives, but it must then be frozen during evaluation.

Memory utility is expected to depend on both cumulative lived transitions `L`
and reusable causal coverage `rho(L)`, not age alone. Random or irreducible
experience should produce no crossover.

## 2. Reference organism

```text
ACT / OBSERVE
  -> WAKE RESOLVER
       bounded local memory query
       explicit DFS-like dependency traversal
       broaden/backtrack when a path fails
       one action or cognitive operation per call
       cited thought/action path and unresolved dependency
  -> VERBATIM EPISODIC STORE
       immutable public actions, observations and outcomes
  -> SLEEP at fixed checkpoints
       select ordinary lived traces and released wake paths
       DREAM with the same resolver in broader offline mode
       propose local relations, exceptions, procedures and path shortcuts
       chronologically validate against later public outcomes only
       compile multiple atomic access views
  -> PER-LIFE MEMORY LORA
       cumulative rebuild from the clean base
  -> LATER WAKE RESOLVER
       iterative local reads plus exact cited episodic support
       goal-conditioned working-path reconstruction
       better information gathering, planning and action
```

DFS/BFS are controller metaphors. The LoRA is not a literal graph and its read
is not invertible decompression. It supplies lossy local associations; the
resolver reconstructs a small explicit path under the current goal. The
provenance graph is an audit shadow, never an answer-bearing cognitive tool.

## 3. Owned state and visibility

Each `LifeRuntime(life_id)` owns exactly:

```text
EpisodicStore          immutable public action/observation/outcome events
SemanticStatusStore    immutable claims plus append-only status events
BranchStore            thinker workspaces and lifecycle status
AgendaStore            typed selection-only wake-to-sleep requests
CorpusManifest         eligible compiled examples
MemoryCheckpoint       per-life adapter and training manifest
RetrievalState         arm-specific indexes/caches
RuntimeState           RNG, optimizer, scheduler, counters and budgets
```

Separate non-cognitive processes own:

```text
AuditStore             hashes, provenance and runtime receipts
EvaluationStore        sealed held-out branch outcomes
ScorerStore            hidden world truth and post-commitment scores
```

The `SemanticStatusStore` is authoritative lifecycle state, not automatically
cognitive memory:

- sleep and the compiler may read eligible semantic records;
- after a memory checkpoint, the headline wake arm may not inspect the store;
- wake reads only through the frozen common reader backed by its assigned
  memory backend;
- text/graph arms expose their own frozen snapshot through that same reader;
- a separately labelled native-graph score may use its native interface;
- audit, evaluation and scorer stores are never model-visible or writable by
  cognition.

The exact episodic store can be fetched only through valid provenance handles
returned by the common reader, under the same retrieval budget in every arm.
It cannot be searched as an unlimited second memory.

### 3.1 Taint classes

```text
PUBLIC_LIVED              admissible evidence
SUPPORTED_SEMANTIC        admissible derived evidence
PROVISIONAL_SEMANTIC      hypothesis input, never support by itself
SYNTHETIC_REALIZATION     training surface, never new evidence
AGENDA_SELECTION_ONLY     replay selector, never evidence
WORKSPACE_UNSUPPORTED     never positive memory
NEGATIVE_FAILURE_TRACE    negative training only
AUDIT_ONLY                never cognition
EVAL_CLONE_OUTCOME        sealed from life
HELDOUT_EVAL              sealed from life
HIDDEN_TRUTH              scorer only
SCORER_DERIVED            scorer only
UNPARSED_MODEL_OUTPUT     preserved, never admitted
```

Taint propagates to the most restrictive dependency. Any artifact depending
on evaluation, hidden truth, unsupported workspace, or an agenda field cannot
become evidence or positive corpus content.

### 3.2 Agenda schema

A wake branch may emit only:

```text
DreamAgenda:
  agenda_id, life_id, checkpoint_id, source_branch_hash
  allowed_anchor_evidence_ids[]
  missing_dependency_kind:
    CAUSE | EFFECT | RELATION | PRECONDITION | EXCEPTION | PROCEDURE
  failure_reason:
    NOT_FOUND | CONFLICT | LOW_CONFIDENCE | BUDGET_EXHAUSTED
  uncertainty_bucket
  taint = AGENDA_SELECTION_ONLY
```

Candidate answers, parent/source sets, proposed actions, plans, expected
outcomes, free-form rationales, held-out target identifiers and evaluator
outputs are forbidden. An agenda can select public evidence for replay but can
never be cited as evidence.

## 4. Claim, provenance and branch lifecycle

Claims are immutable. Changes are append-only status events or new revisions.

```text
PROPOSED
  -> PROVISIONAL   if schema/provenance is valid
  -> SUPPORTED     only for a directly witnessed public event
  -> RETRACTED     if malformed, tainted or cyclic

PROVISIONAL
  -> SUPPORTED     if its committed prediction matches a later lived outcome
  -> CONTRADICTED  if later lived outcome conflicts
  -> STALE         if world version changes first
  -> RETRACTED     if provenance becomes invalid

SUPPORTED
  -> CONTRADICTED  on later public contradiction
  -> STALE         on a world-version change
  -> SUPERSEDED    when a valid replacement claim is created

CONTRADICTED | STALE
  -> SUPERSEDED    only through a newly created revision claim
```

No old claim returns to `SUPPORTED`. Positive LoRA data may include supported
witnessed atoms, supported derived claims, and supported local shortcuts.
Provisional content stays outside the stable adapter corpus. Contradicted or
stale content may become explicitly labelled negative examples; retracted and
superseded content is excluded.

### 4.1 Chronological support

A derived proposal commits a prediction, target observable, evaluation
condition, world version/deadline, and source evidence before the relevant
later outcome exists. A mechanical comparator may attach the later public
outcome. It cannot propose, repair, normalize or rank the claim. Hidden world
truth remains offline.

### 4.2 Evidence equivalence and provenance

Every object resolves to the set of root lived events supporting it. Reverse
views, paraphrases, cloze forms, QA realizations, repeats and compiled forms
inherit exactly the parent's root set. They increase write exposure, never
epistemic support. Independent support requires disjoint root-event sets.

The typed provenance DAG is:

```text
ExperienceEvent -> DerivationEvent -> SemanticClaim -> Realization
SemanticClaim   -> DerivationEvent -> SemanticClaim
SemanticClaim   -> RevisionEvent   -> replacement SemanticClaim
```

Sources must predate the derivation. Self-citation, descendant citation,
realization-as-evidence, directed cycles and mutual support between canonical
equivalents are rejected. Shared-ancestry diamonds are valid but shared roots
count once.

### 4.3 Branches

```text
ACTIVE | RELEASED_ACTION | DEFERRED | ABANDONED | CONTRADICTED |
BUDGET_EXHAUSTED | MALFORMED | EVALUATION_ONLY
```

Only active branches mutate workspace. Released actions become sleep-selectable
only after their ordinary lived outcome arrives. A deferred branch may emit
one typed agenda. Abandoned, contradicted, exhausted and malformed branches
may be negative traces but never positive semantic content. Evaluation-only
branches never re-enter life state. Continuing a terminal branch creates a
new child ID.

## 5. Permitted memory growth

Dreaming may propose multiple local candidates, but it need not independently
solve a whole held-out goal or build a global graph. Wake paths supply much of
the useful connectivity.

A materialized shortcut is permitted only when:

1. it comes from an actually traversed wake path of length two or three;
2. every edge was already supported;
3. the path was independently traversed in at least two wake episodes;
4. at least one later ordinary public outcome succeeded or matched prediction;
5. the complete source path and root provenance are preserved;
6. it denotes one local relation or bounded subprocedure;
7. it is not tied to a held-out goal instance;
8. it contains no exact held-out answer, complete parent set, terminal action
   label, or full solution plan;
9. it passes chronological support.

A shortcut's maximum action scope is two actions. Every A3/A4 evaluation goal
requires at least four actions, so one shortcut cannot terminate the task from
its initial state.

## 6. Common wake reader

Every memory arm receives the same typed query:

```text
MemoryQuery:
  life_id, checkpoint_id, branch_id, query_id
  query_kind:
    WITNESSED | RELATION | CAUSE | EFFECT |
    PRECONDITION | PROCEDURE | EXCEPTION | SHORTCUT
  subject_handle, predicate, direction, expected_value_type
  candidate_policy_id, top_k, query_token_budget
```

It returns:

```text
MemoryRead:
  query_id
  result = FOUND | NOT_FOUND | CONFLICT | UNPARSEABLE
  candidates[]:
    canonical_value, claim_handle, epistemic_status, calibrated_confidence
  actual_tokens, backend_receipt_hash
```

One query returns at most one local operation, never a chain or full solution.
The candidate universe is generated from the public ontology before evaluation
and contains every legal value plus `NOT_FOUND`; it is never constructed around
the correct answer. Query, candidate policy, top-k, token budget and thinker
protocol are frozen across common-interface arms. The thinker sees returned
records, never index scores or global topology.

The transport contrast uses an identical accepted semantic corpus for text
and LoRA. Active bytes, retained bytes, build compute, query compute and thinker
compute are reported separately. Native graph/skill performance is reported
separately, never pooled with common-interface results.

## 7. Controlled Persistent Causal Action-World v0

This is a mechanism microscope, not the external-validity headline. It is a
semantic field-expedition/lab life rather than a color/nonce lookup game.

Each world contains:

- eight named sites with public conditions such as dark, flooded, hot, cold,
  corrosive and low-oxygen;
- eight organisms/materials with public semantic traits;
- four preparation/equipment families;
- four latent causal mechanism families: exposure, compatibility,
  transformation and route safety;
- two stable seed-specific exceptions.

The generator preserves sensible semantic priors but samples the operative
per-life mapping and exceptions. Paired counterfactual twins share names,
descriptions, visible states and marginal action frequencies while requiring
different explanations and actions.

Legal actions are:

```text
SURVEY(site)
ASSAY(item, condition)
PREPARE(equipment)
TRAVERSE(route)
INTERVENE(item, equipment)
COMMIT(goal)
```

Survey, assay and intervention expose action-conditioned evidence at a cost.
Traverse and commit succeed or fail and produce a public causal outcome. No
target answer is emitted as a memory label. The hidden engine exports causal
graphs and minimal successful paths only to the offline scorer.

### 7.1 Capability families

Every held-out deck has equal quotas:

- `A0`: recover one witnessed transition; installation diagnostic only.
- `A1`: apply one learned relation to a new entity with the same publicly
  observed functional role.
- `A2`: choose a novel information/action plan from two relations acquired in
  different episodes.
- `A3`: compose two or three learned dependencies into a four- to six-action
  plan.
- `A4`: detect one controlled exception/rule change, gather disambiguating
  evidence, revise and recover.

The primary behavioral endpoint excludes A0: normalized A1--A4 action value,
with A2--A4 and each family reported separately.

### 7.2 Shortcut and leakage audits

For every family and checkpoint, freeze these predictors before model runs:

- target text only;
- current public state only;
- entity/site identifier only;
- passive signature without action outcomes;
- global action-frequency prior;
- public semantic prior without life experience.

Reject a generated deck when any predictor exceeds `0.35` normalized A1--A4
action value or when a target twin shares the same correct action. Shuffling
action--outcome bindings must reduce an exact-memory oracle by at least `0.30`.
An oracle given the true supported life graph must score at least `0.85`.

## 8. External benchmark selection rule

The frozen candidate roster is:

1. DiscoveryWorld-Lifetimes;
2. ScienceWorld-Lifetimes fallback.

Selection uses development data and simulator audits only, before any
Dream--LoRA--Think comparison. If both pass, DiscoveryWorld wins because its
native loop is hypothesis--experiment--outcome--explanation--action. If only
ScienceWorld passes, it becomes the external scale result. If neither passes,
the external headline is removed rather than contorting a benchmark.

### 8.1 One-day DiscoveryWorld fit gate

Pin a commit and run headless CPU checks on Plant Nutrients, Reactor Lab and
Combinatorial Chemistry.

Required gates:

1. **Determinism:** for three themes x three seeds, two 100-step replays have
   identical canonical observation/score hashes at every tick. Prefix replay
   at steps 25 and 75 yields identical pre-branch hashes and repeatable branch
   outcomes.
2. **Throughput:** 1,000 evaluation-only steps finish within five minutes and
   policy observation is below 8k tokens at the 99th percentile.
3. **Persistent-life factorization:** at least two themes expose 20 valid
   generated parameterizations of stable operator schema + per-life parameters
   + per-episode entities/objectives.
4. **Active evidence:** at least two source interventions produce
   outcome-dependent information relevant to a later task; instructions alone
   are insufficient.
5. **Reuse:** an injected exact memory from three evidence episodes changes a
   deterministic held-out task outcome, while shuffled action--outcome memory
   removes at least half the gain.
6. **Headroom:** no-memory performance is between 0.05 and 0.85.
7. **Non-procedurality:** held-out tasks differ in both parameters and required
   explanatory relation; replaying source action strings cannot solve them.
8. **Isolation:** scorer critical questions, hypotheses and hidden task state
   never enter the agent channel.

DiscoveryWorld lacks a supported state restore. Branches therefore use seeded
action-prefix replay plus a canonical semantic-state hash. Any mismatch fails
closed. Explanatory-knowledge scores that require model judging are secondary;
exact task/procedure metrics remain primary.

Failure of gates 3--7 sends the same fixed tests to ScienceWorld. A failure is
reported and the roster is not expanded post hoc.

## 9. Frozen pilot schedule

### 9.1 Models and budgets

- resolver/dream/compiler: `Qwen/Qwen2.5-32B-Instruct`, frozen pinned revision;
- memory model: `Qwen/Qwen2.5-7B-Instruct`, frozen pinned revision plus a
  per-life LoRA;
- primary working budget `C = 16,384` input tokens per decision, including
  system, public state, scratchpad and injected memory;
- native-long-context diagnostic: the same 32B model up to its pinned supported
  maximum, reported separately;
- at most eight resolver operations and four memory queries per environment
  decision;
- each read returns at most four records and 2,048 total memory tokens;
- one environment action per released wake branch;
- sleep after each geometric lifetime checkpoint;
- malformed output consumes budget and is never silently repaired.

LoRA rank candidates are `{8, 32, 64}`. Development worlds select the rank
maximizing A2--A4 value at `2C`; ties choose the smaller rank. The selected
rank and all training hyperparameters freeze before locked worlds. The
existing measured r=64 recipe is included but not assumed optimal.

### 9.2 Life scale

Checkpoint the non-repeated public lived stream near:

```text
0, 0.5C, 1C, 2C, 4C, 8C, 16C
```

where token counts use the pinned 32B tokenizer over canonical public events.
New causal coverage must increase between checkpoints; filler cannot qualify.
At every checkpoint, freeze all writes, clear working context/KV caches, mount
the checkpoint memory, evaluate a fresh read-only held-out deck, discard all
evaluation outcomes, and verify byte-identical pre/post life-state hashes.

The calibration pilot uses four development and four locked world-lives at
`0, 1C, 2C, 4C`. It is exploratory and cannot support a paper p-value. The
confirmation phase, if promoted, uses 24 new locked paired world-lives and the
full checkpoint schedule. World-life is the replication unit.

## 10. Sleep corpus

At each checkpoint, sleep receives only the new ordinary action/outcome block,
released wake paths, eligible prior semantic records and typed agendas.

For each selected trace it may propose up to four local claims. Supported
claims compile into six frozen views: forward QA, reverse QA where logically
valid, cloze, paraphrase, scoped contrast and provenance query. Re-expression
does not add evidence. Old and new records are interleaved.

The cumulative adapter is rebuilt from the clean base at every checkpoint.
The training budget is frozen per retained semantic record and reported as
examples, tokens, optimizer steps and FLOPs. Direct/raw-LoRA arms receive the
same number of examples, tokens, steps, rank and schedule. No condition gets
extra hidden retries because its corpus is harder to train.

## 11. Mandatory comparison set

All arms use the same base resolver, public experience, action budget, C,
query limit and think budget.

- `P0` no persistent memory.
- `P1` chronological recent/full context within C.
- `P1L` strongest feasible native-long-context control.
- `P2` raw episodic BM25/embedding RAG.
- `P3C` accepted semantic text/graph corpus through the common reader.
- `P3N` the same graph through a fair declared native interface, separately
  labelled.
- `P4` raw/direct trajectory-to-QA LoRA with matched adapter training.
- `P5T` sleep-compiled text memory.
- `P5L` identical sleep corpus in LoRA.
- `P5A` compiled LoRA with atoms only.
- `P5S` compiled LoRA with supported trace-selected shortcuts.
- `P6` P5S with within-world action--outcome attachments shuffled while
  language, counts, actions and compute are preserved.
- `P7` cross-life adapter control.
- matched batch SFT on accumulated life as an upward reference, not an online
  matched method.

`P0/P1/P2/P3C/P4/P5T/P5L/P6` are mandatory in the calibration pilot. The
remaining arms enter confirmation. Any failed mandatory arm is reported and
blocks a positive comparative claim; it cannot be silently omitted.

Resource equality is enforced where causal comparison requires it; otherwise
active memory bytes, retained bytes, environment/model calls, input/output
tokens, retrievals, sleep tokens, adapter training tokens/steps/FLOPs and wall
time are reported separately. Idle reflection may equalize model-call budgets
but its output cannot enter memory.

## 12. Fixed-deck and on-policy experiments

### 12.1 Fixed common deck

Every arm receives the same ordered public action--observation--outcome stream.
Checkpoint evaluation is read-only. This identifies representation/use while
holding experience distribution fixed.

### 12.2 On-policy flywheel

For each paired world and checkpoint, deterministically replay the ordinary
prefix to a canonical state hash, clone it into isolated processes, mount the
assigned memory condition and allow the same remaining action budget. Reject
impossible or mismatched clone states. Branch outcomes are sealed and cannot
train the source life. All conditions then face the same independent read-only
deck.

Use randomized memory intervention at the branch boundary and paired seeds.
The causal estimands are the effect of assigned memory on later evidence
quality and action value. A cross-system experience swap is allowed only by
replaying a valid public event sequence from the same counterfactual-compatible
world; arbitrary final-state swapping is forbidden.

## 13. Estimands and statistics

For method `j`, life length `L`, dependency depth `d` and world `w`, let
`A_j(w,L,d)` be normalized held-out action value.

Primary per-world endpoint:

```text
mean A1--A4 action value at 8C
```

Primary contrast:

```text
P5S - max(P1L, P2, P3N, P4)
```

Primary developmental contrast:

```text
[P5S(8C) - P5S(1C)] -
[best baseline(8C) - best baseline(1C)]
```

Define useful-memory onset as the first checkpoint where the paired 95%
lower confidence bound over world-lives is above zero and remains positive at
the next two checkpoints. Also report post-context AUC, slope, final value,
effective dependency depth at fixed think budget, success@8 actions,
restricted mean actions to success with failures censored at 8, exact recall,
false-memory rate, correction half-life, `rho(L)` and shortcut coverage.

Confirmation uses all 24 paired world-lives, paired bootstrap confidence
intervals over world-lives, a paired randomization test for the primary
contrast, Holm correction for separately tested A2/A3/A4 secondary families,
and every-world plots. Missing/failed cells remain failures at their action
cap unless an infrastructure failure occurred before any science call; partial
science cells are preserved and reported but not silently rerun.

## 14. Runtime and reset contract

Every cognitive call receives policy-visible last-operation fingerprint,
repeat count, remaining operation/query budget and branch status. Exactly one
operation is accepted. The harness may stop at a hard budget but cannot
invisibly redirect behavior.

Every call records prompt, schema and parser versions, model revision,
tokenizer hash, generation config and attention-mask presence. Unknown fields,
multiple operations, truncated JSON and extra prose are malformed. Raw bytes
are preserved; there is no repair-and-score path.

Each phase validates into a unique temporary directory, writes a
content-addressed manifest, then atomically renames to a sealed phase. The
manifest includes code/dirty patch, environment, models/tokenizer, prompts,
schemas/parsers, seeds/RNG state, public inputs, all life stores, corpus,
adapter, optimizer/scheduler, reads/generations, failures/repairs and
predecessor manifest. Resume is allowed only from the latest valid sealed
predecessor; partial directories are quarantined.

Before a new life, reset every per-life store, adapter, optimizer/scheduler,
retrieval index/cache, KV/prefix cache, prompt history, RNG, temporary path,
process registry, audit handle and clone handle. Inject previous-life canaries
into event text, semantic claim, adapter cue, cache key and temp path; the new
life must return `NOT_FOUND`, have the clean-base adapter hash and hold no old
file descriptors/processes.

## 15. Pre-GPU gates

All must pass:

1. selected external benchmark fit gate or frozen failure disposition;
2. controlled-world oracle, shuffle, counterfactual and shortcut audits;
3. provenance diamond/cycle and evidence-equivalence fixtures;
4. agenda-answer laundering rejection;
5. scorer/evaluator write denial and byte-identical post-evaluation state;
6. abandoned-branch and complete-solution compilation rejection;
7. same-corpus common-reader fixture;
8. malformed/multi-operation fail-closed tests;
9. crash-at-every-phase deterministic resume;
10. cross-life canary contamination test;
11. direct atomic writer/read battery for facts, relations, exceptions and one
    legal shortcut;
12. independent fresh reviewer plus author-side scientific advocate over the
    exact frozen code, inputs, prompts, models, budgets and claim boundary.

The first GPU run is the four-development-world calibration at `1C` and `2C`
for `P2/P3C/P4/P5T/P5L/P6`. No model-comparative scale run occurs before the
CPU gates.

## 16. Negative-result decision table

- Controlled world fails action/reuse/context/leakage gates: kill or rewrite
  the world; no GPU interpretation.
- P5L/P5S does not beat P4: sleep compilation has not added useful structure.
- P5L/P5S beats P4 but not P3N: compiler may work, but the parametric substrate
  has not earned the paper claim.
- P5S beats baselines only before context pressure: reject the scaling claim.
- Benefit survives P6 shuffle or P7 cross-life adapter: treat as leakage,
  generic prompting or compute; no experiential claim.
- Gains occur only on A0/A1: ordinary retention/procedure transfer only.
- Fixed-deck gain without on-policy gain: memory use works but the flywheel is
  unsupported; report the claims separately.
- Recurrent sleep does not beat one final batch: sleep cadence is unsupported.
- Shortcuts do not reduce reads/hops at matched action accuracy: shortcut
  materialization is unsupported.
- False-memory accumulation exceeds correction: reject continual-learning
  viability at that scale.
- Only one backbone/order succeeds: report a bounded interaction, not a
  general mechanism.
- DiscoveryWorld/ScienceWorld fail their fit gate: retain controlled causal
  evidence only and remove external-development language.

## 17. Required acceptance tests

- `AT01_environment_and_leakage_fit`
- `AT02_atomic_memory_contract`
- `AT03_common_deck_isolation`
- `AT04_mechanism_and_baseline_suite`
- `AT05_constructive_action_and_revision`
- `AT06_on_policy_flywheel`
- `AT07_independent_review_gate`
- `AT08_semantic_lifecycle_and_provenance`
- `AT09_visibility_taint_and_reset`
- `AT10_reader_substrate_thinker_factorial`
- `AT11_statistics_splits_and_negative_decisions`
- `AT12_runtime_artifact_and_resume_integrity`

Passing these tests establishes protocol fidelity, not scientific success.

