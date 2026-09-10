# FeltCraft-Lifetimes CPU instrument contract v0

**Status:** proposal-only exact design for deterministic CPU falsification.
It does not authorize implementation or establish model usability.

## 1. Causal generation unit

The outer generated unit is a matched quadruplet:

```text
super_seed q
  x regime r in {RANDOM, MOTIF}
  x binding_twin b in {0, 1}
```

All pseudorandom draws use counter-based, namespace-separated streams derived
from `(q, namespace, era, object, episode, step)`. Regime and twin side may
enter only the registered structural-binding namespace. Rendering, handle,
descriptor, source-schedule, target-template, budget, and nuisance streams are
shared across all four cells.

The causal manipulation is the persistence of descriptor-to-role binding:

- `MOTIF`: one hidden per-life permutation `pi_q` maps descriptor classes to
  motif roles in every era;
- `RANDOM`: an independent hidden permutation `pi_q,e` is drawn for every era;
- twin side 1 composes every applicable permutation with one frozen role
  derangement `tau_q`; applying the same involution again returns side 0.

The recipe template, realized handles, descriptors, sites, target templates,
source-policy action schedule, action budgets, and nuisance text are shared.
Thus RANDOM and MOTIF differ only in cross-era descriptor--role dependence;
twin sides differ only in the hidden role binding learned from their public
lifetimes.

Generation and acceptance are joint at the quadruplet level. A super-seed is
either accepted in all four cells or rejected in all four. Rejection predicates
are symmetric under regime and twin labels, frozen before execution, and logged
with counters. They may inspect hidden worlds only through the exact registered
structural predicates below; they may not depend on any model, learned method,
or target identifier classifier.

## 2. Era template

CPU v0 uses one registered eight-role template:

```text
raw roles:       R0 R1 R2 R3
crafted roles:   C0 C1 C2 C3

C0 <- R0 + R1
C1 <- R2 + R3
C2 <- C0 + R2
C3 <- C1 + R0
```

Every era creates eight fresh opaque handles and assigns the same public
descriptor classes `D0..D7`, one per handle. Handles are sampled independently
of role, depth, goal, regime, twin side, and split. The applicable permutation
maps descriptors to roles, and the template induces four recipe triples over
the fresh handles.

Each era also creates four fresh public site handles. The four raw handles are
assigned to sites by an independent shared nuisance permutation. Site bindings
are identical across the four matched cells and therefore cannot explain a
regime or twin contrast. They provide persistent exact-memory/action costs but
are not the schema manipulation.

CPU v0 has no exceptions or rule changes. Exceptions/A4 are a separately
ratified extension after endpoint regimes pass. A descriptive mixed condition
later samples the persistent per-life permutation with probability `rho` and
an independent era permutation otherwise; `rho=.5` is not part of v0.

## 3. Life, episode, and public state

A life is an append-only sequence of eras. Recipes, descriptor strings, and
raw-site bindings never change in CPU v0. Episodes share the hidden world but
reset current location, inventory, visit flags, step count, and terminal state.
Raw resources renew at every episode reset. Memory systems persist only through
their declared life memory; the environment never carries agent memory.

Hidden life state contains:

```text
recipe triples, descriptor-role bindings, raw-site bindings,
regime, twin side, era index, target registry
```

Public episode state contains only:

```text
episode goal handle and target type,
public handles and descriptor strings declared by the target template,
public site handles,
current site or NONE,
inventory multiset,
observations produced in this episode,
actions remaining,
terminal status
```

No depth, role, recipe, era answer, hidden cohort, split, proof, oracle value,
memory label, or target answer is rendered.

## 4. Action and observation kernel

Every action costs one step. Invalid syntax/unknown public handles return
`INVALID_PUBLIC_ACTION`; this depends only on public grammar. Hidden mismatch
never returns that code.

```text
MOVE(site)
```

- precondition: `site` is a declared public site handle;
- transition: current site becomes `site`;
- observation: the public raw handles present at the site, or `EMPTY`.

```text
GATHER(raw)
```

- precondition: `raw` is a public raw handle at the current site;
- success adds one unit of `raw` to inventory and returns `GATHERED`;
- otherwise state is unchanged and returns `NOT_PRESENT`.

```text
TRY_CRAFT(output, a, b)
```

- public grammar requires three declared handles and `a != b`;
- if inventory lacks either ingredient, state is unchanged and returns
  `MISSING_INPUT` without identifying which input;
- otherwise one unit of each input is consumed;
- if the unordered pair `{a,b}` is the hidden recipe for `output`, one unit of
  `output` is added and observation is `CRAFTED`;
- otherwise no output is added and observation is `INCOMPATIBLE`;
- neither failure identifies the correct ingredient, role, edge, distance, or
  partial match.

```text
STOP
```

- ends the episode. The episode also ends on budget exhaustion or when the
  goal handle is present in inventory.

There is no manual, recipe lookup, inspect-rule action, hidden-value display,
or recipe-bearing failure. The complete renderer/serializer is frozen before
model testing; CPU v0 tests typed records and UTF-8 bytes without a scientific
tokenizer.

## 5. Source experience

The common source collector is a deterministic public policy plus private
counter RNG. At every step its next-action distribution is a function only of
the canonical public history, the predeclared era/episode schedule, and its RNG.
It cannot read world recipes, site bindings not yet observed, descriptor roles,
targets, scorers, rejection state, or later outcomes.

The CPU implementation must expose the collector as a pure function:

```text
next_action(public_history, schedule_slot, private_rng_counter)
```

The schedule introduces each era through a fixed mix of site visits, gathers,
and lexicographically/permutationally selected craft trials. The schedule is
shared across the four matched cells. Outcome differences arise only through
the registered binding manipulation. It is not required to solve every era.

Public source events are immutable `(pre_state, action, observation,
post_state, time, scope)` records. The engine is permitted to use hidden state
only inside the transition function. Runtime taint tests must fail if hidden
objects enter collector inputs.

## 6. Target families

Target templates and public starting states are drawn before structural
bindings and shared across the quadruplet. Targets use fresh episode states and
never duplicate a source `(state,goal)` or complete action sequence.

CPU v0 includes:

- `A0`: one witnessed recipe choice; diagnostic only;
- `A2`: choose/execute a final craft requiring two observed relations from
  different source episodes;
- `A3`: execute a two-level craft whose required relations include one
  earliest-quartile era and one newest-era component; shortest successful
  execution uses four to six actions;
- `S`: one recipe edge in a new sparse era is absent from source experience.
  In MOTIF it is identifiable from the legal-prefix persistent binding and
  template; in RANDOM it is deliberately nonidentifiable beyond the registered
  no-lifetime posterior.

Targets initialize a frozen public inventory/candidate set large enough that
brute-force craft trials exceed the action budget. Candidate handles and order
are shared across the quadruplet and contain no answer-dependent membership.
The CPU instrument computes exact no-memory, observed-atom, explicit-schema,
exact-memory, and hidden-oracle policies for each target.

The primary target action value is binary success within the budget. Every
crash, malformed output, timeout, missing result, or exhausted budget scores
zero. Shortest-path regret and action count are secondary.

## 7. Twin and target acceptance

An accepted target quadruplet must satisfy all of the following jointly:

1. canonical pre-action target bytes are identical across both twin sides and
   both regimes, excluding a separately stored opaque run ID not visible to a
   policy;
2. target public handle/descriptor/site/candidate multisets are identical;
3. registered twin-valid decisive action sets differ as intended and applying
   `tau` maps each side's set to the other;
4. hidden-oracle and authentic exact-memory success are at least `.85` over the
   target cohort in every cell;
5. exact no-lifetime success is at most `.35` in every cell;
6. brute-force public-history search under the action budget is at most `.35`;
7. shortest successful path length, candidate count, budget, and scoring
   opportunity are equal across cells;
8. the source policy has not produced the target state, goal, complete plan, or
   decisive action sequence;
9. `S` is prospectively identifiable from the legal source prefix in MOTIF and
   remains nonidentifiable in RANDOM;
10. target-only/state-only/identifier/descriptor/passive signatures are at or
    below `.35` under exact small-world enumeration and held-out CPU probes.

Acceptance is cohort-level, not favorable-method target selection. All target
templates in a registered cohort are retained or the whole super-seed is
rejected. Rejection rates and every predicate are reported.

## 8. Exact information quantities

CPU v0 reports distinct quantities rather than one ambiguous entropy:

- `N_unique_public_edges(cut)`: unique recipe/location relations actually
  identified by the public source prefix;
- `L_enum(cut)`: frozen prefix-code bits for enumerating every identified local
  binding independently;
- `L_schema(cut)`: frozen two-part MDL bits for template ID, persistent
  descriptor-role permutation, per-era deviations, explicit exceptions (zero
  in v0), provenance references, and numeric coding precision;
- `H_target_no_memory`: exact conditional entropy of the decisive action given
  target-visible bytes;
- `H_target_source`: exact conditional entropy given target-visible bytes and
  the legal public source prefix;
- `schema_action_gain`: explicit-schema policy minus observed-atoms-only policy
  on `S`.

The code is fixed before sampling. A later compression claim requires both
prospective action gain and `L_schema < L_enum` at matched predictive/action
loss over growing cohorts. Prospective action gain alone is called schema
generalization, not compression.

Reported post-native cuts later require `N_unique_public_edges` and `L_enum` to
grow. The schema-conditioned statistic is allowed to grow slowly; that is the
point of compressibility.

## 9. Evaluation isolation

Every target is evaluated in a disposable process/fork created from a sealed
life cut. The fork is destroyed after scoring. Target goal, queries, reads,
workspace, cited paths, actions, outcomes, replay priorities, RNG state, caches,
and audit traces cannot enter later source, semantic memory, compilation, or
adapter state.

The required suffix-noninterference test compares later source/compiler/memory
hashes with the target deck skipped versus executed. Hashes must be identical;
evaluation audit files live in a disjoint write-only reporting namespace.

## 10. CPU falsification gates

The first authorized scope, if ratified, is negative-only instrument
falsification. It may establish only that the world is eligible for later
known-good text/model testing.

Required CPU properties over 100--1000 super-seeds include:

- deterministic replay and namespace isolation;
- twin involution round-trip and binding equivariance;
- exact target-byte collision and registered action-set flip;
- public-policy non-psychicity under coupled public histories;
- transition multiset/inventory correctness;
- brute-force resistance and oracle/no-memory headroom;
- joint nuisance balance across the four cells;
- unique-information growth and exact MDL behavior;
- prospective schema gain only in MOTIF;
- source/target exclusion, target yield, and rejection accounting;
- graph/candidate-work curves;
- suffix noninterference when evaluation is executed versus skipped.

CPU success cannot establish tokenizer-relative cuts, generic thinker use,
model shortcut resistance, compiled-text value, LoRA transport, rank sufficiency,
baseline saturation, decision-path mediation, or any paper claim.
