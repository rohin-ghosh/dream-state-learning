# 46 — PCFL constructive experiential-memory assay v1

**Date:** 2026-09-01

**Status:** design candidate for fresh architecture deliberation. It does not
authorize implementation or GPU use. It replaces note 45 as the proposed first
calibration, while preserving the full developmental system in notes 42 and 44.

## 1. Scientific purpose

The full project asks whether an agent can turn its own action--outcome history
into a compressed per-life world approximation that improves later action, then
use those better actions to acquire better future experience.

The first assay isolates the smallest unproven causal chain:

```text
ordinary action--outcome experience
-> target-independent local causal claims
-> chronological support or contradiction
-> multi-view sleep compilation
-> bounded memory backend
-> recurrent goal-conditioned reconstruction
-> novel multi-step action
```

The near-term estimand is deliberately narrower than the complete flywheel:

> Given byte-identical action--outcome experience and a frozen controller, does
> recurrent consolidation of provenance-supported local causal structure improve
> held-out multi-step action over raw episodic access, independently organized
> text memory, and direct-QA LoRA; does the identical compiled corpus retain its
> action value in a per-life LoRA; and does shuffling action--outcome bindings
> destroy the gain?

The system may earn that claim only as a complete pipeline. This assay does not
identify dreaming, compilation, the reader, the thinker, or LoRA as sufficient
alone.

## 2. Full architecture is not reduced

The project still contains three nested loops and three parameter/state scales:

```text
theta_0  frozen pretrained priors
phi      shared THINK/DREAM operation policy, prompted and frozen in Paper 1
psi_l    fast per-life MEMORY LoRA, rebuilt during sleep

wake     state -> retrieve -> compose -> act -> observe -> revise
sleep    replay -> dream locally -> validate -> compile -> rebuild psi_l
outer    complete-life trajectories -> later training of phi
```

This assay temporarily fixes the source action stream and excludes on-policy
reconsolidation so memory representation and use can be identified. Passing it
promotes to the fixed-deck developmental curve, then memory-assignment clones,
then the on-policy flywheel, then an external lifetime wrapper. Failure stops
that promotion; it does not erase the architecture.

## 3. Persistent Causal Field Lab (PCFL)

PCFL is a finite, semantically rendered field-lab/rescue environment. It is a
mechanism microscope, not a memory trivia game and not the external-validity
headline.

### 3.1 Per-life latent model

Each life samples one stable hidden causal model with:

- four binary functional traits per specimen/material;
- six preparation operators, each applying one stable trait transformation;
- four site-family acceptance predicates drawn from bounded conjunction,
  disjunction, exclusive-or, and negated-condition families;
- three route families, each with one stable trait/equipment precondition;
- two sparse class-or-site exceptions that override one local default;
- fresh entity, site, route and mission handles in every episode.

The public semantic skin uses meaningful but non-decisive attributes such as
wet, hot, corrosive, dark, brittle, insulated and oxygen-poor. Counterfactual
twins share all names, descriptions, visible-state marginals, action counts and
outcome counts while swapping selected preparation and route mappings. A model's
world priors can scaffold reasoning, but cannot identify which twin it inhabits.

### 3.2 Actions

One typed action is executed at a time:

```text
SURVEY(site)
ASSAY(specimen, trait_or_condition)
PREPARE(specimen, preparation)
TRAVERSE(route, specimen)
INTERVENE(specimen, site)
COMMIT(mission)
```

Every action returns an ordinary public observation, cost and outcome. The
hidden engine never emits a rule, proof, target answer or memory label to a
cognitive process.

### 3.3 What recurs and what does not

Reusable across a life:

- preparation-to-transformation relations;
- transformed-trait-to-site-compatibility relations;
- route preconditions;
- local exceptions;
- bounded causal subprocedures.

Never reused as an answer key:

- entity/site/mission handles;
- exact initial states;
- exact goals;
- complete ordered action sequences;
- terminal answers.

Held-out missions use fresh handles and unseen combinations. No source episode
matches a held-out `(state, goal)` pair.

### 3.4 Capability ladder

- `A0 INSTALL`: recover one witnessed transition. Diagnostic only.
- `A1 TRANSFER`: apply one learned operator to a fresh entity with the same
  functional traits.
- `A2 COMPOSE`: combine a preparation effect and a site predicate acquired in
  distinct intervention clusters.
- `A3 PLAN`: combine two transformations and a route precondition into a
  four-to-six-action execution.
- `A4 REVISE`: encounter a controlled exception, gather one discriminating
  observation, backtrack, and improve on a later analogous target.

The minimal first assay uses A0--A3. A4 enters immediately after the clean
composition gate because it requires within-evaluation replanning.

## 4. The corrected stored-solution boundary

The prior rule that no legal set of records may close an A2/A3 plan was wrong:
if the records are never jointly sufficient, composition cannot succeed.

Define three closure predicates.

### 4.1 Direct-record closure — forbidden

A single legitimate record or one reader return must never contain:

- a held-out goal or target handle;
- a terminal action;
- the decisive route--tool pair;
- a complete ordered plan;
- more than one declared ontology edge;
- a relation from which the target plan can be copied without joining distinct
  premises.

The legitimate direct-record closure rate must be exactly zero.

### 4.2 Non-adaptive bounded closure — diagnostic

The controller commits all memory queries before any read. It cannot use a
newly retrieved value to choose the next query. This condition should remain
near the no-memory floor.

### 4.3 Interactive proof closure — required

The same atomic memories may become jointly sufficient through legal recurrent
queries and workspace updates. A representative path is:

```text
q1(site)                -> hazard
q2(hazard)              -> required procedure class
q3(procedure class)     -> route precondition
q4(procedure, role)     -> compatible preparation
typed plan              -> sequential environment actions
```

For every edge after the first, the query must contain a canonical value first
introduced by an earlier read or public outcome. A successful constructive
trace has a mechanically valid dependency DAG of the required depth. A lucky
correct action without that DAG remains an action success and a composition
failure.

Pre-GPU closure gates:

- leaked copy ceiling `>= 0.95`;
- oracle atomic memory plus recurrent thinker `>= 0.85` A2/A3 value;
- oracle atomic memory plus non-adaptive queries `<= 0.35`;
- valid constructive-proof rate in the oracle recurrent arm `>= 0.80`.

## 5. Lifetime and chronological evidence

Let `C` be the fixed working-context/read budget measured by the pinned resolver
tokenizer over all model-visible input.

The source life is generated once by a fixed scripted experimental policy and
replayed byte-for-byte to every memory arm. This identifies memory under common
experience; it is not on-policy learning.

Checkpoints occur at `0.5C`, `1C`, and `2C` for the first assay. The larger
paper protocol retains `4C`, `8C`, and `16C`. Each checkpoint adds genuinely new
causal coverage rather than filler.

Every A2/A3 post-context target requires:

- one decisive root whose last support is more than `C` tokens old;
- one decisive recent root;
- for A3, at least one intermediate relation from a third source block.

The writer at `0.5C` proposes target-independent local relations using only the
prefix. The `0.5C..1C` suffix can support or contradict committed predictions.
The writer repeats at `1C`, and `1C..2C` supplies later confirmation. Claims
created at the terminal `2C` boundary without later public evidence remain
provisional and cannot enter positive LoRA data.

Episodes are called provenance-distinct, not causally independent. Synthetic
views, paraphrases and repeated exposure never add epistemic support.

## 6. THINK, DREAM and SLEEP roles in this assay

### 6.1 THINK

The frozen recurrent resolver receives the current goal and public state, a
bounded workspace, policy-visible repeat state, and at most one local memory
read per query. It emits exactly one operation:

```text
QUERY_LOCAL | UPDATE_PATH | BACKTRACK | EXECUTE_ACTION | DEFER | STOP
```

At evaluation it executes one world action at a time. A3 is not submitted as a
single opaque `COMMIT(plan)` payload. Every subsequent action sees only the
ordinary new public state, bounded workspace and legal memory reads, then may
replan.

### 6.2 DREAM

Dream uses the same operation machinery offline to propose target-independent
one-edge relations with root public-event citations and a falsifiable prediction.
It may broaden across replayed episodes, but it cannot promote its own claims,
see a held-out evaluation target, or write a whole solution. Multiple proposals
are search, not independent evidence.

Free-form wake workspaces are omitted from the minimal assay. Later recurrent
PCFL uses declassified traversal projections only as replay selectors; they do
not confer evidence and every descendant claim must be supported independently
by public roots.

### 6.3 SLEEP compiler

The compiler is not a truth oracle and does not generate new claims. It:

1. admits only chronologically supported target-independent atoms;
2. preserves contradicted/provisional records outside positive training;
3. canonicalizes duplicate claims and provenance;
4. emits fixed multi-view training realizations;
5. interleaves old and new supported claims;
6. rebuilds `psi_l` cumulatively from `theta_0`.

No materialized shortcuts enter the first assay. Trace-selected two-edge
shortcuts and garbage collection enter only after atomic composition works.

## 7. Exact evaluation timeline and stage credit

Each held-out item starts in a fresh process with a read-only memory checkpoint.
Source life, scorer state, prior evaluation items, caches and workspaces are
inaccessible.

For each decision:

```text
public goal/state
-> up to four local queries and eight resolver operations
-> optional typed provisional plan
-> one environment action
-> ordinary public outcome
-> update/backtrack/requery
-> next action or stop
```

The item ends on success, irreversible failure, explicit defer, malformed
operation, or six executed actions. Evaluation outcomes are sealed and never
train or mutate the source life.

Score separately:

1. fixed-query atomic read accuracy;
2. next-query correctness;
3. adaptive dependency rate: later query uses a newly read value;
4. recovered causal-edge precision/recall;
5. certified proof completion and depth;
6. ordered-plan validity;
7. executed mission success, normalized return and action regret;
8. revision after contradiction;
9. false-memory use;
10. text-to-LoRA transport loss.

## 8. Strong no-lifetime-memory control

PCFL is finite, so the environment gate includes an exact finite-horizon
Bayes-optimal adaptive controller. It knows the generator family and prior,
observes every public current-item field, may select information-gathering
actions, and receives the full six-action budget, but receives no outcomes from
earlier episodes. It is an upper bound on active reacquisition without lifetime
memory.

Also freeze a 32B adaptive no-persistent-memory controller with within-item
scratch, exact prompt/schema, action policy, tie-breaking and budget. Reject a
world if either registered no-lifetime-memory controller exceeds the declared
headroom ceiling.

## 9. Conditions and causal contrasts

Run text conditions before adapter training.

| ID | Memory | Controller | Scientific role |
|---|---|---|---|
| `L` | scorer-injected leaked goal-to-plan record | one-query copy | executor ceiling only |
| `N` | none/recent context | recurrent | frozen-agent floor |
| `O-open` | oracle target-independent atoms | non-adaptive queries | composition-negative control |
| `O-rec` | identical oracle atoms | recurrent queries | composition ceiling |
| `R-rec` | raw source episodes/RAG | recurrent queries | episodic baseline |
| `A-text` | independent A-MEM-style builder | recurrent queries | organized external baseline |
| `E-text` | supported experience-derived atoms | recurrent queries | compilation/structure test |
| `S-text` | outcome-shuffled life through same writer | recurrent queries | causal binding control |
| `O-LoRA` | identical `O-rec` atoms in LoRA | recurrent queries | transport ceiling |
| `E-LoRA` | identical `E-text` corpus in LoRA | recurrent queries | complete assay pipeline |
| `S-LoRA` | identical shuffled corpus in LoRA | recurrent queries | parametric causal control |
| `D-LoRA` | direct trajectory-to-atomic-QA LoRA | recurrent queries | matched direct-write baseline |

The leaked arm runs in a scorer-tainted isolated process and is never presented
as a memory method. The A-MEM-style builder consumes raw public episodes and is
frozen before locked worlds; it never consumes our semantic store.

Primary calibration contrasts:

```text
composition:      O-rec - O-open
structure-text:   E-text - max(R-rec, A-text)
binding-text:     E-text - S-text
transport:        E-LoRA - E-text       # non-inferiority margin -0.10
pipeline:         E-LoRA - max(N, R-rec, A-text, D-LoRA)
binding-LoRA:     E-LoRA - S-LoRA
```

These contrasts do not isolate the contribution of an individual dream or
compiler operation. The first paper-facing result is the bundled compiled
experiential-memory pipeline plus stage attribution.

## 10. Action--outcome interventions

### 10.1 Matched shuffle

Permute outcomes among source interventions matched by causal family, surface
shape, chronology bucket and token length. Preserve action counts, outcome
counts, text length and all compute. Rebuild the memory from clean state.

### 10.2 Counterfactual twins

Twins preserve public descriptions and marginals but swap selected causal
mappings. Authentic memory must beat paired-twin memory on the same goal/state.

### 10.3 Memory-assignment clones

After the fixed-deck assay passes, replay a canonical source prefix into
isolated processes, verify its semantic-state hash, then randomize assignment
of authentic, null, shuffled or twin memory. Every clone receives identical
goal, public state, RNG, action and compute budgets. Clone outcomes remain
sealed. This identifies the behavioral effect of assigned memory.

## 11. CPU gates before model or adapter science

Run at least 50 generator seeds and require:

1. exact deterministic replay and prefix hashes;
2. hidden-graph oracle action value `>= 0.85`;
3. Bayes-optimal no-lifetime-memory A2/A3 value `<= 0.35`;
4. injected exact lifetime memory materially improves held-out return;
5. shuffle and twin-memory assignment each remove at least half that gain;
6. target-only, current-state-only, identifier-only, passive-signature,
   action-frequency and source-action-string probes each remain `<= 0.35`;
7. every A2/A3 minimal proof uses at least two provenance-distinct intervention
   clusters and every post-context target uses early and recent roots;
8. no source episode matches a target state/goal;
9. causal coverage continues to grow through at least `4C`;
10. evaluation clones cannot mutate source-life state;
11. valid provenance diamonds pass while cycles, descendant citation and
    duplicate-root support fail;
12. 1,000 simulator steps complete in five minutes and model-visible state
    remains within the fixed bound.

Then run the text-only lookup/closure/thinker conditions. No LoRA is trained
until `L`, `O-open`, `O-rec`, `R-rec`, `A-text` and `E-text` establish that the
world, reader and recurrent thinker measure the intended construct.

## 12. Exploratory calibration and promotion

Development:

- two counterfactual twin-pairs for parser/runtime changes only;
- changes are allowed only before locking.

Locked calibration:

- six new twin-pairs;
- one adapter-training seed;
- evaluation at `2C` only;
- descriptive results, no p-value and no paper claim.

Promote only if:

1. `O-rec >= 0.85` and valid-proof rate `>= 0.80`;
2. `O-open <= 0.35` and legitimate single-record closure is zero;
3. `E-text - max(R-rec, A-text) >= 0.10`;
4. `E-LoRA - max(N, R-rec, A-text, D-LoRA) >= 0.10` in at least four of six
   twin-pairs;
5. `E-LoRA >= E-text - 0.10` and fixed-query read fidelity `>= 0.90`;
6. each shuffle removes at least half the intact gain over `N` and the absolute
   intact-minus-shuffled difference is at least `0.15`;
7. no leakage, reset, prefix, provenance or stage-credit gate fails.

Failure of an oracle/text gate stops GPU transport work. Failure of transport
removes LoRA from the headline and preserves a benchmark/compiler pivot.

## 13. Claim-eligible confirmation

If promoted:

- at least 12 new counterfactual twin-pairs / 24 world-lives;
- two adapter-training seeds averaged within each world, never treated as
  independent replication;
- eight A2 and eight A3 targets per world/checkpoint;
- checkpoints `0, 1C, 2C, 4C, 8C, 16C`;
- three frozen lifetime orderings balanced across worlds;
- the strongest native-long-context control through its actual pinned maximum;
- world-pair/generator seed is the clustering and randomization unit.

Use the calibration variance to increase confirmation to 16 twin-pairs if 12
pairs cannot detect a paired effect of `0.10` at the preregistered uncertainty
criterion.

Primary paper contrasts are `E-LoRA - D-LoRA` and `E-LoRA - A-text` at the
first checkpoint beyond the native long-context maximum, with mean improvement
at least `0.10` and corrected 95% lower confidence bounds above zero. The
same-corpus LoRA/text contrast is a non-inferiority test with margin `-0.10`.
Use paired bootstrap and sign-flip/randomization inference over twin-pairs, with
Holm correction for named A2/A3/A4 secondary tests. Failed scientific cells are
failures at the action cap; infrastructure failures before any science call are
separate and never silently converted into successful reruns.

## 14. Cadence and later stages

Recurrent versus batch sleep is not required for the first GPU assay. It enters
confirmation with unambiguous prefix semantics:

- at each checkpoint `L`, recurrent sleep uses its legal prior checkpoints plus
  the new delta;
- the batch arm receives exactly prefix `0..L` immediately before evaluation;
- both receive the same number of useful proposal calls and training tokens;
- any resource-only padding runs in an isolated process with no handles to
  corpus, RNG, cache, adapter or evaluation state.

After fixed-deck confirmation:

1. add A4 exception/revision and supported two-edge shortcuts;
2. run memory-assignment clones;
3. let conditions choose information-gathering actions on-policy;
4. reconsolidate only their ordinary outcomes;
5. test whether authentic memory improves evidence quality, later memory and
   later return;
6. wrap DiscoveryWorld Plant Nutrients, Reactor Lab and Combinatorial Chemistry
   under a persistent per-life rule set for external validation;
7. train the shared LOOP policy only after the prompted system produces useful
   success/failure trajectories.

## 15. Paper and pivot boundaries

If the confirmation and external/on-policy additions pass, the systems claim is
that a constructive experiential-memory system continues to acquire useful
action structure across increasing agent lifetimes after fixed context and
strong memory baselines flatten empirically.

Without the on-policy branch, do not claim the action--experience flywheel.
Without post-native-context checkpoints, do not claim beyond-context scaling.
Without external validation, present PCFL as a controlled causal instrument.

Never claim first dreaming, first parametric agent memory, first embodied LoRA
memory, first learned consolidation, first outcome-trained writer, autonomous
structure discovery, a literal graph in LoRA, or general/human-like
intelligence. A-MEM, Auto-Dreamer, TMEM, PEAM and adaptive-fast-weight work own
substantial parts of that territory.

Candyland, Blendyland, Semantic World, Counterfactual Confluence and Action
World remain calibration instruments for proposal ceilings, recurrence,
transport, composition and leakage. Their short, observational, symbolic or
shortcut-prone designs do not support the developmental action headline.

## 16. Next exact design bundle

Before implementation, a new hash-bound execution bundle must contain:

- PCFL generator, target and twin manifests;
- exact goal and public-state schemas;
- exact THINK/DREAM prompts and operation schemas;
- prefix eligibility and chronological-support schemas;
- common-reader and candidate-recognition implementation;
- Bayes-optimal and frozen 32B adaptive controls;
- independent A-MEM-style builder definition;
- exact model/tokenizer revisions and generation parameters;
- LoRA corpus views, training recipe and resource ledger;
- estimator, failure and uncertainty rules;
- every CPU/pre-GPU test named above.

That bundle receives two new fresh interpretations, adversarial critique and
valid adjudicated consensus before Rohin is asked to ratify implementation or a
GPU science run.
