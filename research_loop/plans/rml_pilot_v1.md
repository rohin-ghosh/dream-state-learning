# Rendered Maintenance Lifetimes (RML) pilot v1

**Status:** reconciled science design; no result is implied by this file.

## Decision

The paper-facing benchmark is a rendered, action-first lifetime world, not a
larger Candyland/FeltCraft table.  FeltCraft V7 remains a symbolic reference
for exact finite ceilings.  PCFL-13 remains a transport microscope.  Neither
is promoted to the developmental headline.

RML tests one causal chain:

```text
public action/outcome life
-> recurrent THINK traces and target-blind DREAM proposals
-> later public support/contradiction
-> deterministic SLEEP compilation
-> text / graph / LoRA lifetime memory
-> bounded goal-conditioned reconstruction
-> later executed action
-> (on-policy stage) better evidence -> later memory -> later action
```

The paper object is a lifetime phase diagram.  An exact graph, explicit program
learner, or same-corpus text memory is allowed to win.  LoRA is credited only
for persistent associative access/transport, never for discovering the rule or
performing the multi-hop reasoning supplied by the controller.

## Organism held fixed

One frozen resolver implements both modes:

```text
STATE -> QUERY/OBSERVE -> UPDATE/BACKTRACK -> ACT/PROPOSE -> STOP/DEFER
```

- **THINK** is goal-conditioned and DFS-like.  It reconstructs one small cited
  path and acts one step at a time.  Co-retrieval/traversal is logged as a
  selection signal, not truth.
- **DREAM** uses the same operations over bounded replay bundles, but is broad
  and BFS-like.  It proposes local relations, scoped procedures, exceptions,
  and prospective schemas.  It need not enumerate a global graph.
- **SLEEP** does not invent claims.  It admits chronologically supported
  proposals, preserves provisional/contradicted records, deduplicates,
  canonicalizes, interleaves old/new data, emits multiple access views, and
  rebuilds the per-life adapter from the clean base.
- **MEMORY LoRA** stores lossy local associations.  Exact public experience and
  provenance remain outside it.  Reads are one-hop; multi-hop composition is
  externalized in resolver tokens.  Recognition-assisted and unaided
  generative reads are reported separately.

The base and resolver policy are frozen within every evaluated life.  A future
LOOP adapter may learn resolver trajectories across development lives, but is
not required for this experiment.  Every successful and failed operation trace
is preserved in the public-state/operation/environment-result format needed for
that later training.

## Environment

One life is a persistent remote maintenance habitat.  It contains equipment,
routes, materials, hazards, sensors, consumables, and repair goals.  The public
language is meaningful enough for pretrained priors to parse, while all
consequential per-life bindings are sampled after pretraining.

The generic action API is:

```text
OBSERVE(object_or_site)
MEASURE(object, public_test)
MOVE(route_or_site)
ACQUIRE(object)
CONFIGURE(object, setting_or_attachment)
APPLY(tool_or_material, target)
RUN(object_or_process)
COMMIT(goal)
STOP
```

Actions cost time/resources and expose only their ordinary consequences.  No
failure message names a hidden rule or missing prerequisite.

Three non-isomorphic mechanism packs are required for confirmation:

1. fluid/thermal: valves, pumps, coolant, pressure, corrosion;
2. power/control: relays, cells, sensors, grounding, overload;
3. material/biological: coatings, cultures, reagents, temperature, containment.

The one-pack DEV pilot starts with fluid/thermal.  It is an engineering and
information-value gate, never a paper replicate.

Each life samples a connected causal program containing transformations,
compatibilities, routing preconditions, and scoped exceptions.  Each era adds
new local relations plus at least one interaction with an earlier module.
Each pack also has at least two latent higher-order laws.  DREAM must commit a
law prediction before the confirming era.  A later sparse target withholds one
local edge that the supported law predicts; a witnessed-edge graph alone is
therefore insufficient, while an explicit program-induction baseline remains
capable.

## Targets and lifetime axis

At every checkpoint use fresh handles/layouts/goals and score separately:

- `R`: witnessed recall, diagnostic only;
- `N`: newly acquired causal relations;
- `O`: early relations whose last support is outside native context;
- `J`: a connected old-to-new six-to-twelve-action plan;
- `P`: prospective sparse transfer with one unwitnessed but schema-predicted
  edge;
- `X`: exception detection, information gathering, backtracking, and later
  analogous recovery.

For `J`, removing the registered early bridge must make every legal recent-only
plan fail.  It is not two independent goals concatenated.  For `P`, all
witnessed atoms without the prospective schema must remain below the registered
ceiling.  `X`'s later analogous target is sealed before the exception outcome.

Let `L_native` be the pinned model's actual usable context after prompt, state,
workspace, and output reserve.  Evaluate at `0.5L_native`, `2L_native`,
`4L_native`, and `8L_native`.  The final three points must be strictly
post-native.  Every interval must add unique public roots, identifiable local
relations, an old/new interaction, and a prospective prediction.  If only raw
tokens grow, the checkpoint is invalid for development claims.

Primary behavior is the equal-weight mean of `N/O/J/P/X`; `R` is excluded.
Report each stratum, action value, restricted mean actions-to-success,
information gain/action, old/new relation precision/recall, effective certified
depth, false-memory use, correction half-life, and complete resource vectors.

## Two experiments

### I. Common-experience attribution

Every arm receives byte-identical ordered public events from one fixed,
nonexhaustive, target-blind source policy.  At each cut, build memory, clear all
context/cache/workspace/process state, mount a frozen read-only snapshot, run a
fresh target, destroy it, and prove that evaluation did not change the later
life.  This isolates representation/use; it is not the flywheel claim.

### II. Randomized on-policy flywheel

At each post-native boundary clone the same canonical state and randomize
authentic, null, binding-shuffled, or counterfactual-twin memory before an
ordinary information-gathering block.  The selected public actions/outcomes
enter that clone's life, one fixed consolidation follows, and a pre-generated
sealed target measures later action.  Cross collector trace with compiled,
RAG, native graph, and direct-QA representations to separate experience quality
from representation/use.  Flywheel credit requires all of:

1. assigned memory changes information-seeking actions;
2. those actions improve target-relevant information gain/coverage;
3. later supported memory improves;
4. later sealed action improves.

## Baselines and causal controls

Mandatory native baselines are: no memory; actual native context with honest
truncation; hybrid raw-episode RAG; hierarchical reflection/summary; native
A-MEM linked memory; exact witnessed-event graph; explicit generator-aware
program induction; procedural skill memory; raw-event LoRA; direct-QA LoRA;
DREAM-compiled text; identical-corpus LoRA; batch SFT; and hidden legal-history
oracle.  Report both a common one-atom channel factorial and each system's
uncrippled native interface.

Distinct falsifiers are: action/outcome life shuffle before DREAM; type/status/
length/root-count-matched corpus-binding shuffle after compilation; intact twin
memory assignment; and cross-life adapter assignment.  For credited traces,
mask the full cited memory cut and substitute matched twin atoms in isolated
decision forks.  Whole-memory randomization is the primary causal evidence;
trace masks are secondary mechanism evidence.

## Leakage and validity gates

Before model work, across generated twin worlds:

- legal-history/gold-memory action value is at least `.85` in every primary
  stratum;
- generator-aware no-life Bayes, target-only, state-only, identifier-only,
  renderer-only, passive-signature, action-frequency, and source-action-string
  predictors are each at most `.35`;
- each target is solvable and has a necessity certificate;
- counterfactual twins have identical target-visible bytes but different valid
  plans, and prior authentic history identifies the twin;
- no source state-goal, complete plan, or terminal sequence is reused;
- evaluation run/skip suffix hashes match;
- proposal counts are fixed before outcomes; the comparator can append only
  match/contradiction after a committed prediction and can never guide search.

THINK/DREAM never see hidden programs, proof/shortest paths, target manifests,
scorer outputs, paired metadata, acceptance receipts, or evaluation outcomes.
Repeated wording/views do not add evidentiary support.

## Promotion ladder

1. **CPU world gate:** one fluid/thermal pack, deterministic replay, Bayes/
   oracle/headroom, twins, target necessity, leakage probes, isolation, and
   growing causal coverage.
2. **Gold thinker gate:** gold atoms/schema crossed with nonadaptive, generic
   recurrent, and explicit program-search controllers on `J/P/X`.  Generic
   recurrent gold must score at least `.85`, and nonadaptive must remain at or
   below `.35`.
3. **Text compiler gate:** learned DREAM/SLEEP text versus raw RAG, native graph,
   A-MEM, reflection, and program induction on DEV.  Stop weight work if learned
   compiled text does not recover at least 70% of gold memory's gain or trail
   the strongest external baseline by more than `.10`.
4. **Transport gate:** freeze one admitted corpus; compare text, recognition-
   assisted LoRA, and unaided generative LoRA at one post-native cut.  Require
   fixed-query read fidelity at least `.90` and same-corpus LoRA noninferiority
   margin `-.05` before any weights headline.
5. **Three-pack common-deck confirmation:** three post-native cuts, honest
   native baselines, world-life replication.
6. **Randomized on-policy confirmation:** only after fixed-deck success.

The CPU gate should run locally.  The first GPU work is the gold-thinker and
text-only DEV factorial.  LoRA training is conditional on those results.

## Estimands and falsifiers

The independent unit is a counterfactual world-life pair.  Targets, calls,
dream samples, and adapter seeds are nested.  Use at most four DEV pairs per
pack, six locked descriptive calibration pairs, and at least eight new pairs
per pack for confirmation; average two adapter seeds within each world.

Primary gates are validity; full-system post-native AUC versus every declared
primary native baseline; continued `2x -> 8x` development with new acquisition,
old retention, and connected/prospective action all preserved; same-corpus
LoRA/text noninferiority; authentic-binding dependence; then the randomized
on-policy effect.  Use paired world-level sign-flip/randomization inference and
simultaneous world-clustered bounds.  A comparator is called saturated only
when both later-interval improvement upper bounds are at most `.02`, oracle
headroom remains at least `.10`, and unique causal information keeps growing.

The headline is narrowed if graph/program induction wins, LoRA loses to the
same corpus in text, rank/bytes or hidden query work grow linearly, only recall
or near transfer improves, post-native value is flat, authentic binding does
not matter, one pack drives the result, or on-policy assignment does not improve
evidence and later action.  These are findings, not reasons to weaken controls.

## Paper claim if every applicable gate passes

> Across rendered causal world-lives, sleep-compiled lifetime memory allowed a
> fixed agent to continue acquiring, retaining, and combining action-relevant
> structure after native context was exceeded; the admitted corpus retained its
> value in per-life weights, and randomized authentic memory improved later
> evidence acquisition, reconsolidation, and sealed action where declared
> memory baselines had empirically saturated.

Without the on-policy stage, remove the flywheel clause.  Without LoRA/text
noninferiority, remove the weights clause.  Without three post-native cuts,
remove growth/saturation language.  RML does not establish a learned resolver,
open-ended continual learning, or general intelligence.
