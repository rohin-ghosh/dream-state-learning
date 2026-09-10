# RML paper experiment v1: connected experiential memory across lifetimes

**Date:** 2026-09-03  
**Status:** experiment-architecture advisory only. This file does not ratify
runtime bytes, authorize implementation, or authorize a GPU run. Any execution
must pass the repository architecture-intake, independent-review, and GPU gates.

## Decision

Run one staged RML study whose causal spine is:

```text
own public action/outcome experience
  -> target-blind recurrent DREAM proposals
  -> later public support or contradiction
  -> deterministic SLEEP compilation
  -> connected explicit text memory
  -> the identical semantics in an isolated per-life LoRA
  -> recurrent goal-conditioned THINK traversal
  -> held-out multi-step action
  -> longer lives with new/old/cross-era demands
  -> randomized memory-conditioned evidence gathering
  -> one reconsolidation
  -> improved sealed later action
```

The minimal paper-worthy object is not a single end-point comparison. It is an
evidence ladder from G2 through G5, preceded by the already specified D1/G1
world and gold-controller gates. G2 establishes that public experience can
produce useful connected text; G3 asks whether exactly that semantic memory
retains its action value in weights; G4 tests continued acquisition, retention,
and cross-era action at `2x`, `4x`, and `8x` the usable native context; G5
randomizes memory before information gathering and tests the complete positive
feedback loop.

Failure at one rung stops spending on its dependent rung. In particular, LoRA
must not repair a failed text compiler, more lifetime must not repair a failed
resolver, and a fixed-deck result must not be described as a flywheel.

## Questions and permitted claims

| Gate | Question | A positive result permits | Still forbidden |
|---|---|---|---|
| G2 | Can target-blind DREAM plus public-only admission turn the agent's executed action/outcome history into connected text that improves J/P/X action? | Provenance-conditioned experiential consolidation plus bounded reconstruction improved held-out action. | Parametric-memory advantage, continuing improvement, learned agency, flywheel. |
| G3 | Does the same admitted semantic snapshot preserve action value when transported to a clean per-life LoRA? | Recognition-assisted parametric transport of connected experiential memory. | Retrieval-free recall, LoRA discovery/reasoning, superiority to text, lifelong weights. |
| G4 | Does capability continue to rise as independent causal information grows beyond context while acquisition and retention coexist? | A lifetime/depth growth curve; baseline saturation only for baselines that satisfy the registered plateau test. | Open-ended continual learning, fixed-capacity asymptotics, general intelligence. |
| G5 | Does authentic memory cause better information actions, evidence, reconsolidated memory, and later action? | An on-policy positive feedback loop in the tested RML distribution. | Learned exploration in general, base-model self-improvement, cross-domain autonomy. |

The broad claims that agents reflect, sleep/consolidate, maintain linked memory,
store experience in LoRA, or learn procedures from outcomes are not novel.
TMEM, Auto-Dreamer, A-MEM, PEAM, Voyager, DECKARD, and fast-weight/nested-
learning work occupy those axes. The paper's contribution is the prospectively
sealed causal comparison across action, substrate, and lifetime.

## Experimental unit, worlds, and split

The independent unit is a **counterfactual world-life twin pair**. Targets,
skins, actor samples, adapter seeds, checkpoints, and repeated reads are nested
measurements, never independent replicates.

- **DEV:** two twin pairs in the fluid/thermal pack. They choose prompts,
  thresholds, retrieval parameters, and the small adapter grid. They cannot
  enter a paper estimate.
- **Locked calibration:** six new twin pairs, two per mechanism pack. They test
  the frozen end-to-end protocol and variance assumptions. They are reported
  descriptively and never used to retune.
- **Confirmation:** eight new twin pairs per pack across fluid/thermal,
  power/control, and material/biological: 24 independent pairs total. This is
  the minimum paper population. Two LoRA seeds are averaged within each life.
- **Lifetime cuts:** `0.5 L_native`, `2 L_native`, `4 L_native`, and
  `8 L_native`, where `L_native` is measured for the pinned checkpoint,
  tokenizer, system prompt, state/workspace reserve, and output reserve. The
  last three cuts must be strictly post-native.

Every interval adds unique public causal roots, new mappings, an old/new
bridge, a prospective prediction opportunity, and an exception/recovery
opportunity. A cut is invalid if only tokens or redundant episodes increase.
The common-deck and on-policy targets are disjoint and sealed before collection.
Evaluation is side-effect free, so G4 and G5 may share a confirmation world
prefix without sharing target outcomes, scratch state, caches, or model state.

At every cut score `N` (new), `O` (old), `J` (inseparable old-to-new plan),
`P` (prospective sparse transfer), and `X` (exception, information gathering,
backtracking, and analogous recovery). `R` recall is diagnostic and excluded
from the primary behavior mean. Each J has an early-bridge necessity
certificate. Each P remains unsolved by witnessed atoms alone but is solvable
by the prospectively supported schema. Twin targets have byte-identical
model-visible targets and different valid plans.

## Information and authority boundary

The only epistemic authority available to cognition is an append-only public
ledger of ordinary executed actions, observations, and outcomes plus previously
admitted semantic rows. The environment may reveal consequences; it never
names a hidden rule, missing prerequisite, gold plan, or score.

The following are never visible to the source policy, DREAM, reflection writer,
SLEEP, memory reader, LoRA trainer, THINK, or any baseline writer/controller:

- hidden programs and per-life permutations;
- proof, shortest-path, necessity, or target manifests;
- target allocation, target-derived candidate lists, paired-twin metadata;
- scorer output, offline solver output, admission receipts based on hidden
  truth, evaluation outcomes, or future public events;
- another life's memory, cache, scratch state, or adapter.

Hidden truth and exact solvers are used only after artifacts seal, for target
generation, validity certificates, offline scoring, and labeled ceilings.
There is **no external verifier in cognition**. A DREAM proposal is committed
before its test outcome. Its later status is computed only from ordinary public
events and frozen, deterministic matching rules. Repetition, paraphrases, and
compiler views are not independent evidence.

Each semantic item records a canonical identity, type, direction, scope,
source event IDs, parent memory IDs, derivation depth, committed prediction,
confidence, status (`PROVISIONAL`, `SUPPORTED`, or `CONTRADICTED`), and status
event. All states remain append-only for audit; only supported rows enter
positive LoRA training. A prospective schema must predate its confirming
outcome. A contradiction retracts it from active reads but never deletes its
history.

## One resolver, two modes, one deterministic compiler

The recommended primary is the pinned Qwen2.5-32B-Instruct clean checkpoint
used by the RML gold-controller gate; its exact artifact/tokenizer revision is
bound only in the later ratified spec. The same checkpoint serves as writer,
resolver, and LoRA base, with no arm-specific stronger model. The base and
prompted resolver are frozen across all paper arms. One model call emits
exactly one typed operation. THINK and DREAM use the same operation family and
state/provenance interfaces; they differ only in input, objective, grounding,
and output permission.

### DREAM

DREAM is replay-driven and breadth-seeking. At each registered sleep boundary
it receives a bounded, target-independent replay bundle made from public
episodes, prior admitted local rows, and typed missing/conflict agenda records.
It may `QUERY`, `FOLLOW`, `BACKTRACK`, `PROPOSE`, `DEFER`, or `STOP`. A proposal
must be one local relation, scoped procedure, exception split, or prospective
schema with cited roots/parents and a public test condition. It cannot write a
target solution, complete plan, unsupported final answer, or a self-certified
fact.

Replay scheduling is frozen before confirmation. Each new evidence block gets
the same number of replay bundles and at most four proposal calls per bundle.
Proposal counts seal before later outcomes. Reflection and proposal arms use
the same writer checkpoint, replay chunks, call count, generated-token cap,
temperature schedule, and source prefix. Successful and failed proposal traces
are retained.

### THINK

THINK is goal-conditioned and depth-seeking. It starts from fresh scratch and
may `QUERY` one atomic dependency, `FOLLOW/UPDATE` a cited path, `BACKTRACK`,
`ACT`, `DEFER`, or `STOP`. Every query after the first must be anchored in the
public goal/state or a previous returned row. A read returns one immutable row,
`NOT_FOUND`, or `CONFLICT`; it never returns a hidden multi-hop solution.

Each target permits at most 18 resolver operations, including at most six
memory reads and at most 12 environment actions. No hidden planning calls,
retries, or replacement trajectories are allowed. Invalid, illegal,
multi-operation, truncated, over-budget, or unsupported decisive releases stay
in the denominator and score zero. Multi-hop credit requires a valid cited
dependency DAG and the registered minimal causal cut, not merely a correct
terminal action.

### SLEEP

SLEEP makes no model call and invents no content. It deterministically:

1. applies chronological public-only support and contradiction rules;
2. preserves every proposal and status event for audit;
3. admits supported, target-independent rows to the active snapshot;
4. canonicalizes and deduplicates identities, treating repetition as support;
5. balances old/new roots and row types under a frozen replay schedule;
6. renders fixed forward, reverse, paraphrase, partial/incident, declarative,
   and QA views without adding semantics;
7. rebuilds each per-life LoRA from the pristine base and emits corpus, fit,
   hash, and isolation receipts.

The explicit snapshot remains truth/provenance authority. LoRA is a lossy read
transport, not the ledger or verifier.

## G2: experience to connected text

G2 has a shared-proposal admission factorial and a full recurrent system
comparison. The shared factorial uses one sealed proposal pool so selection is
not confounded by proposal differences:

| ID | Text memory | Purpose |
|---|---|---|
| `WITNESS-TEXT` | Deterministically parsed witnessed one-edge public atoms; no proposed schema. | Reliable episodic/atomic base and P ceiling. |
| `RAW-DREAM-TEXT` | Every syntactically valid committed DREAM proposal, regardless of later outcome. | Proposal without admission; false-memory control. |
| `SELFCHECK-TEXT` | The same pool admitted by the proposal's blind pre-outcome confidence/self-check. | Model self-verification diagnostic. |
| `PUBLIC-ADMIT-TEXT` | The same pool admitted only after frozen matching to later ordinary public outcomes. | Public-only causal admission. |
| `REFLECT-TEXT` | Outcome-aware hierarchical lessons/summary bank from the same replay and writer budget. | Auto-Dreamer/ExpeL/Generative-Agents family control. |
| `GOLD-TEXT` | Target-independent legal-history gold local rows/schema. | Labeled ceiling and denominator for recovered gain. |

The proposed full text system, `E-TEXT`, runs recurrent DREAM over its own
chronologically admitted snapshot and SLEEP-compiles it. The admission
factorial identifies filtering; `E-TEXT` identifies the full recurrent
proposal/admission/compiler/use path. Connectedness is not a wording score: a
credited row at depth two or more cites earlier memory from distinct public
roots, and a credited J/P action traverses an old/new or atom/schema path.

G2 also evaluates `NONE`, honest native `CONTEXT`, `RAW-RAG`, uncrippled public
`GRAPH`, and generator-aware `PROGRAM` so a text gain cannot be attributed to
an easy target or weak retrieval. G2 passes DEV only if:

- gold recurrent THINK action is at least `.85`, valid cited-path rate is at
  least `.80`, and no-memory/nonadaptive/open controls are at most `.35`;
- `E-TEXT` recovers at least 70% of `GOLD-TEXT` gain over `NONE`;
- `E-TEXT` is within `.10` action success of the stronger `GRAPH/PROGRAM`
  reference and beats `RAW-RAG` and `REFLECT-TEXT` directionally in both DEV
  pairs;
- public admission improves the prospective precision--coverage--downstream
  action frontier over witnessed-only, raw-proposal, and blind-self-check
  alternatives; and
- cited cuts and authentic/twin substitutions remove or redirect at least 80%
  of credited successes in the registered direction.

If exact program induction wins, it remains intact. The result becomes a
useful negative about the proposed memory moat; the program is never weakened.

## G3: identical semantics in text and LoRA

For every eligible life/cut, freeze `M`, the exact supported `E-TEXT` semantic
row set, before any target is rendered. Derive both substrates only from `M`:

- `E-TEXT` indexes the canonical rows in `M`.
- `E-LORA-R` trains on deterministic views of those same rows and uses
  recognition-assisted one-field reads.
- `E-LORA-G` trains on the same views but answers without candidate scoring;
  it is a generative-read sentinel, not the primary weights condition.

LoRA repetitions/touches create no new semantic item. Candidate rosters come
from a target-independent, registered public ontology; they are not built from
the target or hidden truth. Host code may resolve manifest cardinality but may
not select a value. On a successful read, text and LoRA pass the resolver the
same canonical row bytes. Both receive the same query schema, six-read cap,
returned-token cap, conflict/`NOT_FOUND` behavior, and clean-base composition.
The adapter is unmounted before multi-hop continuation. Thus text versus LoRA
changes storage/read transport, not information or reasoning.

The G3 transport panel is:

| ID | Training or memory | Role |
|---|---|---|
| `CANDIDATE-BASE` | No lifetime training; same candidate roster. | Recognition/candidate-construction floor. |
| `RAW-LORA` | Raw public events rendered under the same update budget. | Parametric exposure without consolidation. |
| `TMEM-QA-LORA` | Self-generated public episode QA pairs, selected by a development-frozen outcome-trained extractor. | Strong functional TMEM control; not claimed as exact reproduction. |
| `E-TEXT` | Exact frozen `M` in external text. | Identical-information reference. |
| `E-LORA-R` | Exact frozen `M`, recognition-assisted. | Primary transport arm. |
| `E-LORA-G` | Exact frozen `M`, unaided generation. | Read-interface diagnostic. |
| `S-BIND-*`, `T-SWAP-*`, `S-LIFE-*` | Type/status/length/root-matched binding shuffle, intact twin memory, and wrong-life text/adapter. | Binding and life-specificity falsifiers. |

All LoRA arms share rank, target modules, optimizer, number of update tokens,
old/new replay mix, instruction-preservation mix, and clean-base reset. One
adapter is trained per `(world_id, skin_id, life_id, cut, seed)` and is never
continued across lives. DEV screens a small preregistered rank set; confirmation
uses the frozen selected rank plus one lower-capacity sentinel, not an adaptive
per-life rank.

G3 proceeds beyond DEV only if fixed-query `E-LORA-R` row fidelity is at least
`.90`, action is no worse than `E-TEXT - .10`, it beats `RAW-LORA` and
`TMEM-QA-LORA` directionally on the connected target mean, and binding/twin
swaps redirect behavior. In confirmation the same-corpus noninferiority margin
is tightened to `-.05` with a simultaneous world-clustered bound. A text win
with failed LoRA is a valid external-memory/compiler result; it removes the
weights clause rather than invalidating G2.

## G4: common-experience lifetime confirmation

Every G4 arm receives the byte-identical ordered public chronology generated
once per life by a frozen, target-blind resolver-driven behavior policy
executing real environment actions. It is therefore the agent's own public
action/outcome experience, held common across memory arms for attribution. At
each cut, all state is cleared, a read-only memory is mounted, fresh targets
are executed, and the evaluation branch is destroyed. Run/skip suffix hashes
must prove that evaluation did not alter later life.

### Confirmation arms

| ID | Native persistent mechanism | Prior-art objection answered |
|---|---|---|
| `NONE` | Current target/state only; no lifetime memory. | Frozen-agent prior floor. |
| `CONTEXT` | Raw chronological history up to measured native capacity, then honest truncation. | Direct long context. |
| `RAW-RAG` | Iterative hybrid retrieval over raw action/outcome episodes, with query rewriting and fixed top-k/token cap. | Strong episodic RAG, not a one-shot strawman. |
| `REFLECT` | Hierarchical outcome-aware reflected/lesson text bank with frozen offline rewrite. | Auto-Dreamer/ExpeL/Generative Agents. |
| `A-MEM` | Native linked notes with dynamic relation creation and query-conditioned graph traversal over public experience. | A-MEM/HippoRAG-style structured retrieval. |
| `GRAPH` | Exact witnessed-event factor/transition graph, built only from public events; no unwitnessed schema edge. | Explicit structural storage/traversal. |
| `PROGRAM` | Generator-aware explicit program induction over the same public events, including prospective laws when identifiable. | Strong DECKARD/program reference; legitimate winner. |
| `VOYAGER-SKILL` | External library of successful public action macros with induced descriptions, preconditions, effects, and failure repairs; macro expansion counts as environment actions. | Voyager-style procedural reuse. |
| `PEAM-PROC` | Per-life, category-isolated procedural LoRA trained on public failure/correction/success traces under a frozen worthiness rule. | Functional PEAM control; not an exact reproduction. |
| `RAW-LORA` | Raw-event next-token/atomic views under the common adapter budget. | Parametric storage without DREAM. |
| `TMEM-QA-LORA` | Public self-generated QA with a development-frozen outcome-trained extraction policy. | Closest parametric-memory baseline. |
| `BATCH-SFT` | End-of-prefix action-trajectory SFT on the same lifetime/update budget, with no connected semantic compiler. | Ordinary post-training/self-imitation. |
| `E-TEXT` | Recurrent public-admitted DREAM snapshot in text. | Proposed semantic mechanism independent of weights. |
| `E-LORA-R` | The identical `E-TEXT` semantics in per-life LoRA. | Proposed recognition-assisted transport. |
| `LEGAL-HISTORY-ORACLE` | Hidden legal-history/program solution. | Labeled construct/headroom ceiling only. |

`TMEM-QA-LORA`, `PEAM-PROC`, and `VOYAGER-SKILL` are strong functional
implementations of their decisive mechanisms and must be labeled as such, not
as paper reproductions. A native implementation is used only if frozen and
validated before confirmation; a rushed imitation is not an acceptable
baseline.

### Fairness contract

1. **Evidence:** all arms receive the same public prefix; no future event,
   target, hidden state, or arm-specific repair is visible.
2. **Freeze:** every memory, graph, index, adapter, cache, candidate roster, and
   schedule seals before target rendering.
3. **Actor:** one frozen base/resolver, action API, prompt envelope, context
   cap, sampling schedule, operation cap, and scoring rule are used everywhere.
4. **Writer:** generative text arms share writer checkpoint, replay windows,
   calls, generated tokens, and temperature. Deterministic arms disclose their
   lower write cost rather than burning dummy compute.
5. **Weights:** LoRA arms share parameters, train tokens/steps, optimizer,
   preservation data, replay balance, initialization, and two nested seeds.
6. **Three budget currencies:** report writer/train compute, persistent
   capacity (tokens, nodes/edges/index bytes, trainable parameters), and reader
   work (calls, returned tokens, latency) separately. No false claim of perfect
   equivalence between bytes and parameters is made.
7. **Two interfaces:** run a common one-atom reader factorial for mechanism
   attribution and each system's uncrippled native interface under the same
   total reader-token and resolver-operation caps. Primary system comparisons
   use the native interface; text/LoRA substrate comparison uses the common
   channel.
8. **Failures:** writer, fit, read, parse, and action failures remain in the
   intent-to-treat denominator. There are no replacement runs.
9. **Isolation:** processes, KV caches, indexes, scratch, RNG streams, and
   adapters are life-scoped; clean-base hashes and run/skip suffix hashes are
   mandatory.
10. **Interventions:** equivalent whole-memory swaps/cuts apply to every
    substrate, including derived indexes for text/graph and whole adapters for
    LoRA.

### G4 estimands and gate

Primary behavior is the equal-weight `N/O/J/P/X` mean. Primary longitudinal
evidence is post-native AUC plus the `2x -> 8x` paired change. The proposed
text system must have a positive simultaneous lower bound versus `NONE`,
`CONTEXT`, `RAW-RAG`, `REFLECT`, `A-MEM`, `GRAPH`, `VOYAGER-SKILL`,
`PEAM-PROC`, `RAW-LORA`, `TMEM-QA-LORA`, and `BATCH-SFT` on post-native AUC;
it must be within `.10` of `PROGRAM`. `E-LORA-R` must be noninferior to
`E-TEXT` at margin `-.05`.

Continued-improvement wording additionally requires:

- at least `.10` paired improvement from `2x` to `8x`;
- no adjacent-interval drop worse than `-.05`;
- positive simultaneous lower bounds for new acquisition, old retention, and
  J/P cross-era action at `8x`;
- growing unique supported causal coverage, rather than only raw tokens; and
- no hidden linear total-life scan presented as constant-cost memory use.

A baseline is called saturated only if both later-interval improvement upper
bounds are at most `.02`, oracle headroom at `8x` is at least `.10`, and new
unique causal information continues to enter the life. If these conditions do
not hold, omit all saturation language even if the proposed arm wins.

## G5: randomized on-policy positive feedback loop

For the powered test, use the preregistered `8 L_native` boundary: clone the
same canonical public state and randomly assign one of four read-only memories
before a fixed ordinary information-gathering block. A `2 L_native` relay may
be used only as an unscored wiring sentinel; repeating the full factorial at
all three post-native cuts is roadmap evidence, not necessary to identify one
causal loop in Paper 1.

1. `AUTH`: authentic admitted memory from that life;
2. `NULL`: no lifetime memory;
3. `BIND`: type/status/length/root-count-matched binding-shuffled memory;
4. `TWIN`: intact memory from the counterfactual twin behind unchanged
   target-visible bytes.

Assignment is balanced within pack/cut and concealed from the agent. The
collector has the same resolver, query/action cap, costs, and available public
tests in every arm. It chooses real actions; no scripted action deck is inserted
after assignment. The resulting actions and ordinary outcomes append to that
clone's public ledger. Exactly one frozen DREAM/SLEEP cycle follows. Then a
fresh resolver acts on a later target that was generated and sealed before the
collection block. No target outcome is fed back before scoring.

To separate **experience quality** from **representation quality**, each sealed
collector trace is compiled offline through `RAW-RAG`, `A-MEM/GRAPH`,
`TMEM-QA-LORA`, `E-TEXT`, and `E-LORA-R` without further environment actions.
This collector-by-compiler cross is secondary; the primary intention-to-treat
contrast is assigned `AUTH` versus the registered pooled corrupt-memory
controls, with `AUTH` versus `TWIN` the binding-sensitive contrast.

Flywheel credit requires all four prospectively ordered links:

1. assignment changes information-seeking actions, not merely wording;
2. those actions increase target-relevant information gain/causal coverage;
3. the one subsequent SLEEP produces more supported, relevant memory without
   a false-memory increase; and
4. sealed later action success/return improves.

The powered G5 gate requires positive simultaneous intention-to-treat lower
bounds for links 2 and 4, same-direction point effects for links 1 and 3 in all
three packs, and no pack with a harmful action effect below `-.05`. Mediation
through links 2 and 3 is reported descriptively; later action ITT is the causal
headline. A one-pair relay sentinel may validate wiring after G2 but is never
an effect estimate.

## Interventions and negative controls

Every credited mechanism faces the following registered tests:

- **source shuffle:** shuffle action/outcome binding before DREAM;
- **binding shuffle:** preserve corpus type/status/length/root counts while
  permuting decisive bindings;
- **whole twin/life swap:** mount an intact twin or wrong-life memory behind
  unchanged target bytes;
- **minimal cited cut:** remove every row/index derivative cited as decisive;
- **matched sham cut:** remove equal-size, equal-age, equal-type nondecisive
  material;
- **twin-atom substitution:** replace decisive rows with matched twin rows in
  an isolated decision fork;
- **adapter swap:** intervene on the whole adapter, never pretend that deleting
  a citation ablates parametric state;
- **negative-law target:** require defer/chance behavior where public evidence
  does not support the prospective law;
- **reader controls:** candidate-only clean base, path-excluded retrieval,
  `NOT_FOUND`/`CONFLICT`, generative-read sentinel, and wrong-life adapter;
- **shortcut probes:** no-life Bayes, target-only, state-only, identifier-only,
  renderer-only, passive-signature, source-action-string, and action-frequency
  predictors.

Credited G2--G4 successes must lose validity or redirect under complete causal
cuts/twin substitutions while remaining stable under matched sham cuts. At
least 80% of credited DEV successes and a positive confirmation lower bound on
the intervention rate are required. Unsupported decisive release, hidden-field
exposure, target leakage, evaluation-to-life mutation, or cross-life residue
must equal zero.

## Measurements and analysis

### Write and semantic memory

- proposal syntax/newness, prospective precision/recall, supported precision,
  contradiction rate, independent-root diversity, schema coverage;
- witnessed versus proposed rows, unique supported mappings, false-row use,
  correction half-life, retained provenance, certified derivation depth;
- connected-path availability, old/new bridges, and P schemas committed before
  support;
- active and total snapshot tokens/bytes, graph/index bytes, and rows by age.

### Transport and read

- exact forward, reverse, paraphrase, partial/incident, and QA row fidelity;
- `NOT_FOUND`/`CONFLICT` calibration, binding fidelity, held-out-cue behavior;
- adapter rank/bytes, fit failures, seed spread, training tokens/steps/time;
- reader calls, returned tokens, latency, candidate roster size, and any host
  search work.

### Traversal and action

- useful/anchored query rate, query selection, backtracks, defers, illegal and
  unsupported releases, valid cited DAG/path, effective path depth;
- unconditional and compilation/read-conditional `N/O/J/P/X` success;
- normalized return/regret, plan completion, restricted mean actions to
  success, recovery after exception, false-memory-caused action, and twin
  redirection.

### Lifetime and flywheel

- new acquisition, old retention, cross-era J/P value, post-native AUC,
  interval slopes, and oracle headroom;
- writer/dream/compiler/train/read/think calls, tokens, wall time, and GPU time;
- information-action distribution, exact offline information gain, target-
  relevant coverage, supported-memory delta, and later action ITT.

Analyze paired world-level differences with sign-flip/randomization inference
and simultaneous world-clustered confidence bounds. Adapter seeds and targets
are averaged inside worlds. Report pack-specific effects and leave-one-pack-out
sensitivity; one pack cannot carry the headline. All tests, margins, primary
contrasts, exclusions, and multiplicity families freeze before confirmation.

## Stop rules and compute-efficient staging

| Stage | Minimum work | Stop condition | What it licenses |
|---|---|---|---|
| D1/G1, CPU plus gold controller | World validity, shortcuts, twins, necessity, isolation; gold recurrent versus open/nonadaptive. | Any validity failure; gold action `<.85`; valid trace `<.80`; or shortcut/open `>.35`. | G2 DEV only. |
| G2 DEV, two pairs/one `2x` cut | Cache shared proposals once; run text/admission factorial and strong text/graph/program controls. | Any G2 gate fails or cuts/swaps do not redirect. | G3 transport micro. |
| G3 DEV | Fit `E` and raw/QA adapters once per frozen snapshot; one seed screens the branch. | Fidelity `<.90`, action `< E-TEXT-.10`, or no authentic binding effect. | Locked calibration. |
| Six-pair calibration | Frozen three-pack protocol; no retuning after observation. | Mean pipeline gain `<.10` in four of six pairs, RMS seed spread `>.10`, or leakage/isolation failure. | Confirmation registration. |
| G4 confirmation | 24 new pairs, four cuts; deterministic/text baselines first, then adapters only for sealed eligible snapshots. | Validity/headroom failure stops the affected world; aggregate gate failure removes the associated claim. | Fixed-deck paper result and G5. |
| G5 confirmation | Reuse sealed prefixes, but new cloned collection branches and disjoint targets. | Any required causal link fails. | Flywheel clause only. |

Efficiency rules:

- render worlds, targets, legal histories, and CPU ceilings once; hash and reuse;
- generate each DREAM/reflection proposal pool once per life/cut and cache it
  across admission/substrate arms;
- compile one `M` and reuse it for text, graph projections, all reads, and LoRA
  views; never pay writer calls per target;
- fit one adapter per life/cut/seed and evaluate all sealed targets from it;
- batch independent model calls across worlds while preserving within-trace
  order; use first-call timings to reduce, never expand, the ratified cap;
- run cheap deterministic, text, and fidelity gates before LoRA/action grids;
- use one DEV seed to reject and two nested confirmation seeds to estimate
  transport variance;
- stop dependent branches immediately, but retain every failure and receipt.

No GPU estimate in this advisory is authorization. Exact calls, model revision,
rank grid, wall-time ceiling, and GPU-hour cap must be bound in the eventual
ratified experiment spec after D1 and first-call timing.

## Experience memory versus agency/procedure learning

Two adapters must never be conflated:

| Object | Symbol | Learns | Lifetime | Paper role |
|---|---|---|---|---|
| **Fact/experience adapter** | `psi_l` | This life's supported local entities, causal/action relations, exceptions, and prospective schemas, rendered as one-hop associations. | Freshly reset for each life; rebuilt from clean base at sleep cuts. | Proposed Paper-1 LoRA transport. |
| **Agency/procedure adapter** | `phi` | Cross-life policy for what to query, traverse, propose, test, backtrack, act, and stop. It contains no life-specific facts. | Trained only on development lives; frozen and shared across unseen evaluation lives. | Roadmap; Paper 1 uses a frozen prompted resolver instead. |

`PEAM-PROC` is a baseline per-life procedural memory trained on public
failure/correction traces. It is not `phi`: it tests whether storing action
habits is a better lifetime adaptation than storing a connected world model.
`VOYAGER-SKILL` is the analogous explicit-library control. `BATCH-SFT` is an
upper/downstream confound control. None permits the proposed method to mix
world facts and controller skill.

All successful and failed Paper-1 traces are saved as:

```text
PUBLIC_STATE -> ASSISTANT_OPERATION -> TOOL/ENV_RESULT -> NEXT_PUBLIC_STATE
```

with hidden truth, proof paths, scorers, and evaluator artifacts removed and
loss masks prepared for later `phi` training. Training `phi`, co-adapting it as
memory grows, learning an exploration allowance, using rejection-SFT/
preference/RL, or measuring whether a learned controller avoids retrieval
saturation are Paper-2 questions.

Rank pyramids/cascades, data- versus weight-mediated promotion, continual base
updates, multi-sandbox trajectory promotion, learned outcome critics, and
species-level self-training are Paper-3-scale roadmap items. They are neither
needed for nor implied by Paper 1.

## Paper-1 boundary

Paper 1 consists of:

- public action/outcome experience and an auditable explicit ledger;
- recurrent but prompted/frozen DREAM and THINK modes;
- deterministic public-only SLEEP admission/compilation;
- G2 connected text with strong writer and external-memory controls;
- G3 identical-corpus per-life LoRA transport;
- G4 three-pack post-native growth and causal interventions; and
- G5 randomized on-policy confirmation **only if the paper uses the flywheel
  clause**.

If G5 is absent or fails, publish only the fixed-deck
consolidation/transport/growth claim. If G3 fails, remove the weights clause.
If G4 lacks three post-native points or registered baseline plateaus, remove
continued/saturation language. If graph/program wins, report it and narrow the
claim to the measured compiler/benchmark result. A defensible full-pass claim
is:

> Across prospectively sealed rendered maintenance world-lives, a frozen
> language agent used target-blind, public-outcome-conditioned consolidation
> of its own action experience to build connected lifetime memory and improve
> held-out multi-step action after native context was exceeded. The identical
> semantic memory retained action value in isolated per-life LoRA weights, and
> randomized authentic memory improved subsequent evidence acquisition,
> reconsolidation, and sealed action while named baselines satisfied a
> prespecified plateau test.

Every clause is conditional on its corresponding gate. The experiment does not
establish a learned resolver, retrieval-free reasoning, first parametric agent
memory, open-ended continual learning, or general intelligence.

## Inputs reconciled

- `AGENTS.md`
- `research_notes/49_rml_paper_architecture_and_next_experiment.md`
- `research_notes/42_system_thesis_and_experiment_map.md`
- `research_notes/IDEAS.md`, especially the ALIVE distinctions among one-system
  THINK/DREAM, shortcut materialization, experience versus agency adapters,
  the on-policy flywheel, and rank-cascade deferral
- `research_loop/plans/rml_pilot_v1.md`
- `research_loop/advisory/20260903_paper_learning_architect.md`
- `research_loop/advisory/20260903_paper_prior_baseline_audit.md`
- `research_loop/advisory/20260903_paper_design_crosscritique.md`
