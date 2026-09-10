# RML-D0 fluid/thermal world candidate A

**Status:** exact CPU-world design candidate. This file selects benchmark
semantics; it is not implementation authority, a test result, model/GPU
authority, or scientific evidence. It requires the repository architecture
intake, fresh interpretations, critique, consensus, and exact human
ratification before any listed implementation path is created.

**Protocol literal:** `RML-D0-FT-A-V1`.

## 1. Decision and boundary

D0 is a deterministic, finite, fixed-deck fluid/thermal maintenance world. It
exists only to establish that the RML construct can be implemented and audited
on CPU:

```text
stateful public action/outcome life
-> independently growing local causal relations
-> prospectively committed higher-order laws
-> fresh N/O/J/P action targets
-> exact public-history and no-history references
-> twins, necessity, leakage, and isolation certificates
```

D0 implements `R`, `N`, `O`, `J`, and `P`. `R` is diagnostic. The primary CPU
geometry is the equal-weight mean of `N/O/J/P`. `X` is deliberately deferred:
adding exception state, recovery, and analogous-target sealing would roughly
double the engine and oracle state space. No part of J or P is shortened or
weakened to fit X. A later D0-X change must add an exception involution,
information-action necessity, backtracking, and a target sealed before the
exception outcome.

D0 makes no model choice and defines no THINK/DREAM prompt. Its four structural
cuts are not called native or post-native. A later model-stage authorization
must bind the model, tokenizer, chat template, prompt/state/workspace bytes,
output reserve, and measured `L_native`, then prove that these same complete
event cuts land at the registered `0.5x/2x/4x/8x` positions or ratify a new
schedule. Until then D0 supports causal-growth geometry only, not post-native,
developmental, crossover, or saturation language.

The following are unreachable in D0: model/provider calls, model weights,
LoRA, GPU, network, learned writers, scientific cells, locked model results,
on-policy collection, external actions, promotion, and claims.

## 2. World in one paragraph

One life is a remote heat-exchange plant. Portable single-use conditioner
cartridges set one of two coolant properties. Each loop's exchanger accepts one
exact coolant state, and its valve requires one operating mode. Public family
names and neutral descriptors are stable within the life; all consequential
bindings are sampled per life. Source work consists of ordinary, deterministic
bench actions and a few partial cross-era loop trials. Evaluation begins with a
fresh coolant charge, four cartridge instances in a locker, and a loop in the
plant. A successful maintenance mission must travel, acquire exactly the useful
cartridges, apply them, configure the valve, run the loop, and commit the goal.
Wrong loop runs trip irreversibly and never name the failed prerequisite.

## 3. Canonical public bytes and handles

All durable JSON is RFC-8785/JCS UTF-8 over NFC strings followed by exactly one
LF. Identity hashes use the canonical bytes before the LF. Duplicate or unknown
keys, floats, nulls, non-NFC strings, invalid enums, invalid handles, and
multiple actions fail closed. Integers are nonnegative and bounded by their
schema. Audit objects and public objects have disjoint schemas.

Every opaque handle is 14 ASCII bytes matching `[A-Z]{2}[0-9A-F]{12}`. Prefixes
are fixed:

| Prefix | Kind |
|---|---|
| `MF` | persistent module family |
| `CF`, `XF`, `VF` | conditioner, exchanger, valve family |
| `CI`, `LO`, `VA`, `CO` | cartridge instance, loop, valve, coolant |
| `SI`, `GO` | site, goal |
| `EP`, `EV` | episode, event |

Handles are the first 12 uppercase hex characters of SHA-256 over the relevant
namespace key, a zero byte, the ordered UTF-8 labels, a zero byte, and a
big-endian counter. A collision within a pair candidate structurally rejects
the candidate; it is never locally redrawn. World, skin, source-handle,
target-handle, source-order, target-proposal, evaluation, probe, and statistics
namespaces are independent. Both twins receive the same public handles.

The four public module descriptor classes are `D00`, `D01`, `D10`, and `D11`.
They are schema inputs, not answers. A pair-common skin independently permutes
these phrases onto the classes:

```text
ribbed brass panel
matte ceramic panel
crosshatched alloy panel
smooth graphite panel
```

The descriptor-to-phrase permutation is independent of every hidden mapping.
The public component descriptions are fixed:

```text
conditioner: "portable coolant conditioner cartridge"
exchanger:   "sealed thermal exchanger"
valve:       "recirculation valve controller"
coolant:     "water-glycol service charge"
```

Every public action result contains exactly `action`, `event_handle`,
`result_code`, `state_delta`, and `text`. The deterministic text templates are:

```text
OBSERVED:    "The {module_phrase} service board is visible."
MEASURED:    "Gauge {public_test} reads {value}."
MOVED:       "The technician is now at {site_name}."
ACQUIRED:    "Cartridge {item_handle} is now in inventory."
CONFIGURED:  "Valve {valve_handle} is set to {mode}."
APPLIED:     "The coolant gauge reads viscosity {v}; inhibitor {i}."
RUN_STABLE:  "The loop runs with stable pressure and nominal outlet temperature."
RUN_TRIPPED: "The loop trips before stabilization."
COMMITTED:   "Maintenance goal {goal_handle} is complete."
STOPPED:     "The maintenance attempt stops."
ILLEGAL:     "The maintenance attempt ends after an invalid operation."
```

Substitutions are the exact public enum or handle strings; punctuation and
spacing above are normative. No text names a transform, desired state, valve
rule, missing prerequisite, hidden law, twin, split, target stratum, proof, or
score. Fixed-width enums and shared templates make twin byte lengths equal.

The model-facing public event projection, if later authorized, is exactly the
canonical public object plus its `text`; it excludes event origin, world/pair/
split/seed, era index, target kind, acceptance/rejection metadata, hidden state,
and all audit hashes.

## 4. Finite state

The public state of one item has exactly these variables:

```text
layout                   FIELD_LOOP | CONDITIONER_BENCH | VALVE_BENCH | EXCHANGER_BENCH
position                 DOCK | LOCKER | PLANT
action_count              0..10
remaining_actions         0..10
terminal                  false | true
failure_kind              NONE | ILLEGAL | CAP | LOOP_TRIPPED | BAD_COMMIT
goal_handle               GO...
coolant_handle            CO...
coolant.viscosity         LOW | HIGH
coolant.inhibitor         LEAN | RICH
coolant.outlet_temperature UNKNOWN | NOMINAL
coolant.pressure          IDLE | STABLE
inventory                 sorted cartridge-instance records
locker_items              sorted cartridge-instance records
consumed_items            sorted cartridge-instance handles
loop_handle               LO...
loop.module_family        MF...
loop.module_descriptor    D00 | D01 | D10 | D11
loop.exchanger_family     XF...
valve_handle              VA...
valve.valve_family        VF...
valve.mode                UNSET | BYPASS | RECIRCULATE | PULSE | DIRECT
run_stable                false | true
commit_succeeded          false | true
last_result_code          NONE or one public result code
```

Each cartridge record contains only its instance handle, public conditioner
family, module family, module descriptor, descriptor phrase, location, and
consumed bit. The hidden state contains only the two schema laws, per-module
local assignments, target truth, and source-bench kind. Audit counters and RNG
state are runtime state, not world state.

Source diagnostic episodes use the same coolant, valve, loop, and action
transition functions but may start at a public `CONDITIONER_BENCH`,
`VALVE_BENCH`, or `EXCHANGER_BENCH` layout. Bench kind is public. A valve bench
bypasses the exchanger; an exchanger bench uses a public certified bypass
valve. A target is always `FIELD_LOOP`, where both requirements apply.

## 5. Actions and transition law

Exactly one typed action is executed per step:

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

The concrete D0 arguments are closed:

- `OBSERVE` accepts the current module or current site and emits `OBSERVED`.
- `MEASURE(coolant,VISCOSITY|INHIBITOR|OUTLET_TEMPERATURE|PRESSURE)` repeats the
  already public gauge value and emits `MEASURED`; it never exposes a rule.
- `MOVE(DOCK|LOCKER|PLANT)` changes position and emits `MOVED`. Moving to the
  current position is illegal.
- `ACQUIRE(cartridge)` requires position `LOCKER`, an unconsumed named locker
  item, and inventory size below four. It moves the instance to inventory.
- `CONFIGURE(valve,BYPASS|RECIRCULATE|PULSE|DIRECT)` requires position `PLANT`;
  it sets the public mode even when wrong.
- `APPLY(cartridge,coolant)` requires position `PLANT`, the cartridge in
  inventory, and unconsumed. It applies its hidden transform, consumes it, and
  exposes both resulting coolant gauge values.
- `RUN(loop)` requires position `PLANT`. In a field loop it succeeds iff the
  valve mode equals the hidden valve requirement and the coolant pair equals
  the hidden exchanger requirement. Success sets pressure `STABLE`, outlet
  temperature `NOMINAL`, and `run_stable=true`. Any mismatch emits only
  `RUN_TRIPPED`, sets `terminal=true`, and is irreversible. Bench RUN evaluates
  only its declared bench requirement.
- `COMMIT(goal)` succeeds and terminates iff the handle is the public goal and
  `run_stable=true`; otherwise it terminates with `BAD_COMMIT`.
- `STOP` terminates with value zero.

Every parsed action, including redundant observe/measure/configure, consumes
one action. An illegal, malformed, multi-action, post-terminal, or cap-exceeding
action terminates with value zero before partial mutation. There is no undo,
counterfactual query, rule query, free inventory operation, or hidden repair.

## 6. Latent grammar and prior

Coolant state is the bit pair `(v,i)` with `LOW/LEAN=0` and `HIGH/RICH=1`.
The four conditioner transforms, in normative code order, are:

```text
T00 = SET(v,0)
T01 = SET(v,1)
T10 = SET(i,0)
T11 = SET(i,1)
```

An exchanger requirement is one exact pair in `Q={00,01,10,11}`. Valve modes,
in normative two-bit order, are `BYPASS=00`, `RECIRCULATE=01`, `PULSE=10`, and
`DIRECT=11`.

Each module `m` has one public descriptor `q_m in Q` and contributes exactly
twelve persistent local edges:

```text
CF[m,0..2] -> an ordered injection of three distinct T codes
CF[m,S]    -> conditioner_schema(q_m)
XF[m,0..3] -> a permutation of the four Q states
VF[m,0..2] -> an ordered injection of three distinct valve modes
VF[m,S]    -> valve_schema(q_m)
```

The conditioner injection, exchanger permutation, and valve injection are
sampled independently per module: `4P3 * 4! * 4P3 = 13,824` local assignments
per module. They are the genuinely new per-era information; learning the global
schemas does not determine them.

There are exactly two higher-order laws. Over `GF(2)`, for a public descriptor
column vector `q`:

```text
conditioner_schema(q) = A_C q xor b_C   # a T code
valve_schema(q)       = A_V q xor b_V   # a valve-mode code
```

`A_C` and `A_V` are independently uniform over these six invertible matrices,
in this order:

```text
M0=[[1,0],[0,1]]  M1=[[0,1],[1,0]]
M2=[[1,1],[0,1]]  M3=[[1,0],[1,1]]
M4=[[0,1],[1,1]]  M5=[[1,1],[1,0]]
```

`b_C` and `b_V` are independently uniform over `Q`. Thus each schema has 24
laws. Local assignments are uniform over their stated finite sets. Descriptor
codes are a public schedule, independent of hidden laws: E0 is exactly
`D00,D01,D10`; in E1--E3 the C-sparse and V-sparse modules are `D11`, and all
remaining dense modules take `D00,D01,D10,D11` cyclically in module order.
Only the descriptor-to-phrase skin permutation is random.

The complete prior is the product of the two 24-law priors and all module-local
13,824-way priors, conditioned only on the structural pair and target acceptance
rules below. No semantic phrase or handle changes this measure.

### Production and within-life holdouts

`D0_DEV` law matrices are restricted to `M0,M1`. CPU pair slots are balanced
over all matrices and reported separately as fit productions `M0,M1` and
complete-production holdouts `M2..M5`; translations remain uniform. Future
model DEV may use only fresh `M0,M1` lives, and any future locked model study
must use fresh `M2..M5` lives. D0 does not create or authorize those model
splits.

Within every life, era 0 exposes schema components at descriptors `D00,D01,D10`
only. Those three noncollinear points identify each affine law exactly.
`D11` is the first prospective descriptor holdout and appears in era 1. A P
edge is additionally held out at the component-handle level even after its
descriptor production has been confirmed elsewhere.

## 7. Counterfactual twin involution

For hidden world `H`, `dagger(H)` preserves every public descriptor, phrase,
handle, module order, source action, target proposal, layout, initial coolant
state, inventory order, goal, and budget. It transforms hidden outputs:

```text
tau_C: T00<->T01 and T10<->T11
tau_X: 00<->10 and 01<->11
tau_V: BYPASS<->RECIRCULATE and PULSE<->DIRECT
```

Apply `tau_C` to every local and schema conditioner output, `tau_X` to every
local exchanger output, and `tau_V` to every local and schema valve output. This
maps legal injections, affine laws, and valve permutations to legal objects and
is an involution. Both schema matrices are unchanged; their translations change
by the respective xor constant, and the valve output flips. The DEV matrix set
`{M0,M1}` and heldout set `{M2..M5}` are therefore each closed under this map.

A pair candidate is valid only if:

1. `dagger(dagger(H))` equals H exactly;
2. all pre-action target-visible bytes, schemas, discrete timing class, and
   initial error class collide exactly;
3. full source action-kind counts, result-code counts, event byte lengths, and
   module/descriptor counts match across twins;
4. every accepted target has a different required valve mode and disjoint
   correct unordered cartridge pairs across twins;
5. legal public source history identifies the authentic side well enough for
   the legal-history oracle to solve both, while no target-visible side bit
   exists.

Public source outcomes may differ in content and order; that difference is the
life evidence. They may not differ in the matched marginals above.

## 8. Deterministic, nonexhaustive source life

The four structural eras introduce modules as follows:

| Era/cut | New modules | Cumulative modules | New source events | Cumulative events | Cumulative witnessed local edges |
|---|---:|---:|---:|---:|---:|
| `E0/K0` | 3 dense | 3 | 123 | 123 | 36 |
| `E1/K1` | 1 dense + 1 C-sparse + 1 V-sparse | 6 | 122 | 245 | 70 |
| `E2/K2` | 4 dense + 1 C-sparse + 1 V-sparse | 12 | 245 | 490 | 140 |
| `E3/K3` | 10 dense + 1 C-sparse + 1 V-sparse | 24 | 491 | 981 | 282 |

For each module, action order is `OBSERVE`, conditioner panel, valve panel,
exchanger panel. Families and panel rows use canonical handle/enum order.

- Conditioner panel: apply each witnessed family to reset coolant `00` and
  `11`; the pair of public deltas uniquely identifies its T code.
- Valve panel: for each witnessed valve family, run a reset valve bench once in
  each of the four modes; exactly one stabilizes.
- Exchanger panel: for each witnessed exchanger family, run certified-bypass
  benches at coolant `00,01,10,11`; exactly one stabilizes.
- A dense module therefore emits `1+8+16+16=41` events and witnesses all twelve
  edges. A C-sparse module omits both tests of `CF[m,S]` and emits 39. A
  V-sparse module omits all four tests of `VF[m,S]` and emits 37. No other edge
  is omitted.

After module panels in each of E1--E3, exactly one five-event bridge block runs
two reset partial trials using canonical `CF[E0,module0,0]`, the first new
module's `XF[...,0]` and `VF[...,0]`, and fixed BYPASS configuration:

```text
trial A: APPLY old conditioner; CONFIGURE new valve; RUN new loop
trial B: CONFIGURE the same new valve; RUN the new loop from the matched untreated state
```

Pair acceptance requires the two RUN outcomes to differ on both twins. The
block witnesses an old/new interaction but has no goal, COMMIT, target handle,
complete maintenance plan, or target initial state.

The source policy is the literal schedule above. It is target-blind,
outcome-blind, memory-blind, admission-blind, and nonadaptive: no outcome,
token count, proposal, status, target, controller, or score may stop, skip,
repeat, reorder, or replace an action. It is nonexhaustive over legal histories:
it contains only 981 of more than `10^9` legal ten-action sequences, never runs
a source goal, never COMMITs, never reproduces a target state/goal, and omits
the registered P edges.

The schedule yields exact causal growth rather than text growth. At K0--K3 the
unique root-event counts are `[123,245,490,981]`, witnessed family-edge counts
are `[36,70,140,282]`, cumulative module-local sufficient-statistic entropy is
strictly increasing, and E1--E3 each add one cross-era bridge root plus committed
predictions for the next era. Views, repeats, phrases, and event length never
count as roots or edges.

## 9. Prospective schema lifecycle

Next-era module descriptors and handles are sealed in an audit-only schedule
before a schema commitment, but target manifests remain invisible to the
schema process. At each boundary after E0, the deterministic gold program
reference:

1. receives only the legal public prefix and the published 24-law grammar;
2. enumerates all laws independently for C and V;
3. emits no commitment unless exactly one law remains;
4. commits exactly one law atom per channel and one prediction for every
   next-era schema component, including family handle, descriptor, predicted
   local edge, evaluation action panel, and deadline;
5. seals the fixed proposal count before any next-era outcome exists.

The comparator later appends only `MATCH` or `CONTRADICTION` by exact comparison
with scheduled ordinary bench outcomes. It cannot generate, normalize, repair,
rank, resample, reveal distance, or guide search. A schema becomes
`PROSPECTIVELY_SUPPORTED` only after at least two predictions in distinct new
modules match and none contradict. Earlier commitment bytes never change.

E0 commits 6 E1 component predictions, E1 commits 12 E2 predictions, and E2
commits 24 E3 predictions. E1--E3 each contain at least one witnessed
confirmation for both schema channels while retaining one C-sparse and one
V-sparse family edge. P targets are generated from the V-sparse family only
after the relevant schema was committed and prospectively supported. Exactly
one decisive local edge in each P target has no source outcome at or before its
cut.

This deterministic schema path is a CPU gold reference, not DREAM credit. A
future learned proposal must obey the same commitment bytes and fixed proposal
budget under a new authorization.

## 10. Target generation

K0 contains R and engineering fixtures only. K1, K2, and K3 each contain two
targets per primary stratum per twin. All target handles and instance handles
are fresh; goal bytes, initial-state tuples, and complete action sequences are
absent from source and unique within a pair.

Every primary target begins at DOCK with four cartridge instances at LOCKER,
an empty inventory, a fresh coolant charge whose two bits are public, and a
fresh FIELD_LOOP at PLANT. Structural acceptance requires exactly one unordered
pair among the six inventory pairs to make the coolant equal the exchanger
requirement, with its two transforms setting different bits to values different
from the initial state. The registered valve mode is unique. The minimal plan
has nine actions:

```text
MOVE LOCKER
ACQUIRE cartridge A
ACQUIRE cartridge B
MOVE PLANT
APPLY A
APPLY B
CONFIGURE valve
RUN loop
COMMIT goal
```

The two APPLY actions may commute. All other successful paths are found by the
exact enumerator; the target is rejected unless no path shorter than nine
succeeds and no alternative cartridge pair succeeds within ten actions.

Target proposals enumerate cut, stratum order `N,O,J,P`, target ordinal, then
counter `0..4095`. Public descriptor/layout proposals come only from the
pair-common target namespace. The first candidate satisfying both twins and
all structural predicates is accepted once and copied to both sides. Rejection
uses hidden structure only, never controller/model output or wall time. Counter
4095 exhaustion invalidates the protocol version; no rule or threshold is
relaxed.

### R — witnessed recall diagnostic

Two fresh one-action fixtures per cut reproduce one witnessed conditioner
transition on a fresh coolant/item handle. R is scored separately and never
enters the primary mean.

### N — new acquisition

All decisive conditioner, exchanger, and valve families belong to modules
introduced in the current era; all decisive local edges are witnessed in that
era. At least two provenance-distinct panel episodes are needed to identify the
plan. No schema edge is decisive.

### O — old retention

All decisive families belong to E0, and their last direct source support is in
E0. No E1--E3 source event repeats those local edges. The target layout, item
handles, loop, coolant state, and goal are fresh. A future model-stage overlay
must additionally certify that E0's final decisive support lies outside
`L_native`; D0 calls this age-stratified retention only.

### J — connected old-to-new join

The target loop, exchanger, valve, and one correct conditioner are from the
current era. The other correct conditioner is a portable E0 family. Acceptance
requires:

- the two correct transformations set different coolant bits;
- deleting the E0 conditioner instance or its registered transform makes every
  legal plan fail within ten actions;
- using only current-era inventory makes every legal plan fail;
- using only E0 inventory makes the recent loop fail;
- the E0 and recent roots are distinct, and the recent loop's schema is not
  needed;
- both twins have disjoint correct cartridge pairs.

The old conditioner changes the same coolant charge later consumed by the
recent RUN. J is therefore one connected plan, not two goals concatenated.

### P — prospective sparse transfer

Both target ordinals use the current era's V-sparse module with different fresh
layouts and cartridge inventories. `VF[m,S]` has no source RUN. Both correct
conditioners and the exchanger are witnessed. The prospectively supported
valve law predicts the one missing four-way valve-mode edge. A wrong mode is
not revealed until the terminal RUN, so a witnessed-edge graph cannot actively
test all modes inside the registered plan.

The target is rejected if any second decisive edge is unwitnessed, if witnessed
atoms alone determine the missing edge without applying the law grammar, if the
schema does not select exactly one edge, or if exact structural completion
counts do not leave four equiprobable missing-edge values when the schema
grammar and atom are removed. No measured controller value participates in
target acceptance. No P target handle or layout exists at schema proposal time.

## 11. Exact controllers and inference

All controllers below are deterministic local CPU references. They emit legal
world actions only; none is evidence that a model can THINK.

### Hidden-world solver

`HW-SOLVE` sees latent truth and breadth-first enumerates all legal histories in
canonical action-byte order through depth ten. It proves solvability and
minimality only.

### Legal-history oracle

`LH-ORACLE` sees the published grammar, public source action/outcome bytes
through the cut, target goal/state, and current-item public outcomes. It never
sees latent assignments, target truth, target acceptance receipts, twin side,
or scorer output. It:

1. decodes a local edge only when its complete separating panel is present;
2. enumerates the 24 schema laws and admits one only through the prospective
   lifecycle above;
3. enumerates all legal target plans from those public-history consequences;
4. selects the shortest plan, with canonical action-byte ties.

For P, it may instantiate only the single missing edge from the supported law.
For other strata it may use witnessed local edges only. `LH-ORACLE` must solve
every accepted item with value 1; aggregate success cannot hide an unsolved
target.

### Witnessed graph and explicit program references

`WITNESS-GRAPH` receives every witnessed local edge but no schema grammar or
schema atom. Missing P edges remain four-way unknown. `PROGRAM-SEARCH` receives
the published affine grammar and legal public history and must agree exactly
with LH-ORACLE. `SCHEMA-GOLD` receives the prospectively supported schema atom
plus witnessed edges. These distinguish a valid P instrument from learned
schema discovery.

### Generator-aware no-life Bayes

`BAYES-N` knows the complete grammar, prior, source/target schedule, twin rule,
first-accept target algorithm, and split production roster. It sees the current
target's public goal/state and its own within-item public outcomes, but no source
outcome, source-derived edge, schema commitment, rejection count/code, proposal
counter, pair slot, twin side, seed, target ordinal, other target, or audit
metadata.

The target-local quotient key is:

```text
transform of each of four inventory positions
target exchanger required pair
target valve required mode
```

It has at most `4^4 * 4 * 4 = 4,096` positive-mass classes. Nuisance modules
and unused laws are marginalized by exact integer completion counts. The
initial mass conditions on the complete first-accepted structural selection
kernel. The implementation must compute both the unsimplified finite geometric
first-accept likelihood and the symmetry-simplified completion-count posterior
and prove equality. Rejection counts and codes are marginalized, never treated
as absent information.

After each action outcome, inconsistent quotient mass is set to zero and the
remaining integer ratios are reduced exactly. Bellman recursion enumerates all
legal actions through the remaining ten-action horizon:

```text
Q(b,s,a) = sum_o P(o|b,s,a) V(update(b,a,o), transition(s,a,o))
V(b,s)   = max_a Q(b,s,a)
```

Terminal item score is the reward. Ties use canonical action bytes. Integers
and reduced rational fractions are authoritative; floats, pruning, Monte Carlo,
epsilon ties, and fallback priors are forbidden. Every reachable Bellman
residual numerator must be zero. A zero initial or updated mass invalidates the
generator/replay rather than installing a uniform fallback.

## 12. Leakage probes

Each probe is the exact Bayes-optimal decisive-plan predictor under its named
projection, followed by the fixed minimal logistics executor. Its output is the
unordered inventory-position pair plus valve mode. This avoids confusing
missing syntax with information leakage.

```text
TARGET_ONLY         public goal fields only
STATE_ONLY          public initial state only
IDENTIFIER_ONLY     typed handles, inventory positions, and object kinds only
RENDERER_ONLY       public text with all opaque handles replaced by their kinds
PASSIVE_SIGNATURE   descriptors, module phrases, and initial coolant gauges
ACTION_FREQUENCY    target bytes plus source action/family counts, no outcomes
SOURCE_ACTION_STRING target bytes plus chronological source action bytes, no outcomes/state deltas
```

`BAYES-N` is the stronger adaptive source-free controller and is gated too. All
probe priors condition on target acceptance. Identifier, renderer, schedule,
length, and proposal-selection effects therefore count against the world even
when their receipts are hidden.

For sensitivity, a separate scorer-tainted fork injects the decisive pair and
mode into each projection in turn. The corresponding probe must score exactly
1. This fork is destroyed and can never produce a source, target, memory, or
gate input.

`TWIN-HISTORY` runs LH-ORACLE with the intact opposite-twin public history.
`BIND-SHUFFLE` applies a fixed-point-free within-relation, within-era object
derangement to decoded legal-history edges while preserving types, edge counts,
descriptor counts, source-root-count bins, action/result marginals, and byte
lengths. These are CPU content-dependence controls, not learned-memory results.

## 13. Necessity certificates

Every accepted target carries an audit-only exhaustive certificate generated
after target sealing. Certificates never enter target generation beyond a
boolean structural predicate and never enter cognition.

The enumerator records all reachable states through depth ten, every legal
action, canonical successor bytes, shortest successful histories, and the
registered decisive edge set. It must prove:

- shortest success length is exactly nine;
- the registered unordered cartridge pair and valve mode are unique across all
  successful histories of length at most ten;
- removing each decisive component instance, mapping edge, valve edge, or
  exchanger edge eliminates all success within the cap;
- no source state/goal, complete plan, or terminal sequence equals the target;
- every decisive witnessed edge resolves to a distinct source intervention
  root where required;
- N uses current-era roots, O uses E0-only roots, and J uses both E0 and current
  roots;
- J bridge deletion, recent-only, and early-only plan sets are empty;
- P has exactly one absent local edge, its atoms-only structural completion has
  four equiprobable missing-edge values, SCHEMA-GOLD and PROGRAM-SEARCH solve,
  and masking the schema prediction makes the registered plan underdetermined;
- replacing decisive edges/schema with type-matched twin edges changes the
  registered pair/mode toward the twin-valid plan;
- both twins collide publicly before action and have disjoint decisive pairs.

Any failed certificate rejects that target proposal structurally. A target is
never accepted or replaced because a learned or scripted controller happened
to score poorly.

## 14. Scoring, cardinalities, and CPU gates

Per primary item:

- success in nine actions has value `1`;
- success in ten actions has value `9/10`;
- failure, defer, stop, malformed/illegal action, trip, bad commit, cap,
  missing, crash, or indeterminate disposition has value `0`.

R exact transition reproduction has value 1 or 0. Success, restricted mean
actions to success with failures at 10, and information actions are reported
separately.

Frozen D0 shapes are:

```text
D0_DEV pairs                         4
D0_CPU_GATE pairs                  64
ordered structural reserves        16
twins per pair                       2
primary scored cuts                  3  (K1,K2,K3)
primary strata                       4  (N,O,J,P)
targets per stratum/cut/twin         2
R fixtures per cut/twin              2
CPU primary target items          3072
CPU R diagnostic items             768
target proposal cap per slot      4096
pair candidate cap per split slot 65536
```

DEV exists only for parser, runtime, and performance engineering. It never
contributes to a gate. CPU pairs are preassigned and uncurated; reserves may be
used only for pre-science structural exhaustion under a new explicit authority,
never for a difficult value.

For controller `c`, pair `p`, cut `k`, stratum `s`, average two targets within
each twin, then average twins. No target, cut, twin, or failed item is deleted.
All comparisons use reduced rationals. The CPU world passes only if all gates
hold:

1. deterministic replay, target generation, renderer bytes, and namespace
   independence pass for all 64 pairs;
2. every HW-SOLVE, LH-ORACLE, PROGRAM-SEARCH, and applicable SCHEMA-GOLD item
   has value 1;
3. `BAYES-N` and every named leakage probe have mean pair value at most `7/20`
   separately for every `(cut,stratum)`, and their nearest-rank 90th percentile
   over 64 pair values is at most `9/20` (sorted element 58, one-indexed);
4. WITNESS-GRAPH P mean is at most `7/20` at every cut, while SCHEMA-GOLD P is
   exactly 1;
5. let `G_LH=mean(LH-ORACLE)-mean(BAYES-N)` over the same registered cells;
   TWIN-HISTORY and BIND-SHUFFLE each have mean at most `7/20`, and authentic
   LH loss against each is at least `max(3/20,G_LH/2)`;
6. every J deletion/recent-only/early-only certificate has success value zero;
7. every target-visible twin byte collides, every decisive plan differs, and
   source marginals match;
8. exact growth counts are `[123,245,490,981]` roots and
   `[36,70,140,282]` witnessed edges, with one new bridge block in each of
   E1--E3 and no repeated root credited;
9. every P target has exactly one unwitnessed decisive edge and a schema
   commitment predating all confirming outcomes and target visibility;
10. run/skip evaluation-isolation hashes match at every cut;
11. every answer-injected probe scores exactly 1;
12. the complete run stays inside the resource envelope in section 18.

Failure invalidates `RML-D0-FT-A-V1` as a CPU instrument. It never triggers a
threshold relaxation, pair/target/seed replacement, model call, or narrower J/P
definition.

## 15. Evaluation isolation and visibility

The acyclic runtime graph is:

```text
SourcePrefix -> ReadOnlySnapshot -> DisposableEvaluationClone -> AuditOnlySink
SourcePrefix -> DeterministicSourceSuffix ---------------------> SourceSeal
```

There is no edge from evaluation or audit back to source, schema status,
compiler input, future RNG, or later target generation.

At each cut, seal canonical source events/state, prospective commitments and
statuses, RNG counters, target manifest hash, and later source-suffix intent.
Run one branch with all disposable evaluations and another with evaluations
skipped. Continue the fixed suffix from the same sealed predecessor. Source
event bytes, state bytes, schema commitment/status bytes, target bytes, RNG
counters, and final hashes must match exactly.

Process capabilities are separated:

| Process | Public source | Target | Hidden world | Acceptance/proofs | Eval outcomes | May write source |
|---|---:|---:|---:|---:|---:|---:|
| environment/source | yes | no | transition-only | no | no | yes |
| schema reference/comparator | eligible prefix only | no | no | no | no | status log only |
| target generator | no | audit construction | yes | structural boolean | no | no |
| LH/program/Bayes/probes | declared projection only | yes | no | no | own current item only | no |
| scorer/certifier | no | yes | yes | yes | yes | no |
| report | hashes/aggregates | no raw target | no | aggregate receipts | aggregate only | no |

Generator, scorer, proof, posterior, rejection, and audit modules must not be
importable by any future cognition/provider process. Public schemas contain no
world, pair, side, seed, split, era, stratum, depth, answer, proof, or score
field. Backend errors are failures, not NOT_FOUND. Wall time and error details
are audit-only and target twins share a preassigned timing class.

## 16. Seeds and split construction

The 32-byte protocol root is:

```text
a340ca5bbdcb529b46f699f4b3adde78d2bbb9b9ec0af46433a53600f952a359
```

It is SHA-256 of the exact ASCII bytes
`RML-D0-FLUID-THERMAL-CANDIDATE-A-V1\n`. For namespace `n`, ordered labels
`l[0..r-1]`, and uint64 counter `c`, define:

```text
K = SHA256(root || 0x00 || UTF8(n) || 0x00 ||
           join(0x00,UTF8(labels)) || 0x00 || uint64be(c))
```

Random words are `SHA256(K || uint64be(word_index))`, consumed as unsigned
big-endian uint64 values. Sampling `0..m-1` uses rejection below
`floor(2^64/m)*m`, then modulo m. Fisher-Yates consumes one accepted word per
position. No language/runtime RNG is authoritative.

Namespaces are exactly:

```text
world-law, world-local, skin, source-handle, source-order,
target-proposal, target-handle, evaluation, probe, statistics
```

Split slot `i` scans candidate counters from zero to 65535 and accepts the
first pair satisfying grammar, involution, source-marginal, target-existence,
collision, and certificate predicates, excluding any previously used unordered
twin orbit. Scan order is `D0_DEV`, then `D0_CPU_GATE`, then dormant RESERVE.
No controller value enters acceptance. The split manifest records every
counter and sorted rejection-code set, but these are audit-only and explicitly
marginalized by BAYES-N.

CPU law-matrix coverage is balanced as closely as integer 64 permits across
the six matrices for both schema channels and is exact within one count per
matrix. The first-accept filter may not change this: matrix roster is assigned
by slot before scanning, while translations and local maps are sampled.

## 17. Proposed implementation, artifact, and test allowlist

If separately ratified, D0 implementation authority should be limited to these
new paths:

```text
rml_d0/__init__.py
rml_d0/canonical.py
rml_d0/rng.py
rml_d0/world.py
rml_d0/source.py
rml_d0/schema_reference.py
rml_d0/targets.py
rml_d0/planner.py
rml_d0/bayes.py
rml_d0/probes.py
rml_d0/certificates.py
rml_d0/isolation.py
rml_d0/run_cpu_gate.py
rml_d0/tests/test_canonical_renderer.py
rml_d0/tests/test_rng_and_splits.py
rml_d0/tests/test_world_transitions.py
rml_d0/tests/test_source_schedule_growth.py
rml_d0/tests/test_schema_commitment.py
rml_d0/tests/test_targets_twins_necessity.py
rml_d0/tests/test_legal_history_oracles.py
rml_d0/tests/test_no_life_bayes.py
rml_d0/tests/test_leakage_probes.py
rml_d0/tests/test_evaluation_isolation.py
research_loop/schemas/rml_d0_objects.schema.json
research_loop/workflows/rml_d0_cpu_gate_v1.json
```

No prompt, provider, model, training, adapter, GPU, remote, paper, or promotion
file belongs in that scope. Implementation tests must include:

```text
RMLD0_01_CANONICAL_BYTES_AND_STRICT_SCHEMA
RMLD0_02_STATE_TRANSITIONS_AND_GOLDENS
RMLD0_03_NAMESPACE_INDEPENDENCE_AND_NO_COLLISIONS
RMLD0_04_SOURCE_COUNTS_NONEXHAUSTION_AND_GROWTH
RMLD0_05_SCHEMA_UNIQUENESS_PRECOMMITMENT_AND_HOLDOUT
RMLD0_06_DAGGER_INVOLUTION_COLLISION_AND_MARGINALS
RMLD0_07_TARGET_UNIQUENESS_AND_NO_SOURCE_REUSE
RMLD0_08_EXHAUSTIVE_J_AND_P_NECESSITY
RMLD0_09_LEGAL_HISTORY_AND_PROGRAM_ORACLE_EXACTNESS
RMLD0_10_SELECTION_CONDITIONED_BAYES_AND_BELLMAN_RESIDUALS
RMLD0_11_SHORTCUT_PROBES_AND_ANSWER_INJECTION
RMLD0_12_TWIN_HISTORY_AND_BINDING_DERANGEMENT
RMLD0_13_RUN_SKIP_SUFFIX_ISOLATION_AND_WRITE_DENIAL
RMLD0_14_FAILURE_AS_ZERO_AGGREGATION_AND_P90
RMLD0_15_RESOURCE_CEILING_AND_CLAIM_FIREWALL
```

Artifacts are written only beneath
`artifacts/rml_d0_ft_a_v1/<protocol_sha256>/`. A run first validates into a
unique temporary directory, fsyncs files and directory, writes a
content-addressed manifest with predecessor hashes, atomically renames to a
read-only seal, and never rewrites a cut. Resume is allowed only from the last
valid sealed predecessor. A partial directory is quarantined. D0 has no
provider-call indeterminacy because it has no provider calls.

The sealed tree contains `protocol/`, `splits/`, `pairs/`, `certificates/`,
`gates/`, `resources/`, and one terminal `cpu_gate_report.json`. Raw hidden
truth and proofs remain under scorer-only permissions and are excluded from
every public/source projection.

## 18. Bounded CPU resource envelope

The full 64-pair gate must fail closed at any of these limits:

```text
network access                         0
model/provider calls                   0
GPU calls                              0
workers                                4
wall time                              2 hours
aggregate peak RSS                     8 GiB
sealed artifact bytes                  2 GiB
temporary bytes                        2 GiB
accepted CPU primary items          3072
accepted CPU diagnostic items         768
pair candidate attempts          4,194,304  (64 * 65,536 maximum)
target proposal attempts        12,582,912  (3072 * 4096 maximum)
Bayes quotient classes/item           4096
world-action horizon                    10
total cached Bellman states      25,000,000
total simulated transitions     200,000,000
```

Counters are checked before work is dispatched. Hitting a limit produces a
nonpassing resource receipt; it never enables approximation, sampling,
pruning, fewer targets, a smaller prior, a weaker certificate, or a longer
unregistered run. DEV may be used to optimize memoization without changing
bytes or mathematics.

The intended implementation is a small standard-library Python package with
integer bit operations, tuple states, breadth-first search, and reduced
fractions. There is no text generation, retrieval backend, database, simulator
dependency, or training loop. That is why this D0 can be implemented and
audited in hours while retaining exact J and P.

## 19. D0 pass meaning and next authority boundary

A green report means only:

> The proposed finite fluid/thermal RML-D0 instrument conforms to its
> deterministic source, causal-growth, prospective-schema, target, twin,
> exact-reference, leakage, necessity, isolation, scoring, and resource
> contracts on the registered CPU suite.

It does not mean that a model learned a rule, remembered a life, composed a
plan, used DREAM/SLEEP, crossed native context, improved with age, or supports
an RML paper claim. The next permissible design artifact is a separately
ratified gold-thinker/text-only DEV bundle that binds exact model/tokenizer
bytes, `L_native`, prompts, reader returns, operation budgets, gold atoms and
schemas, baseline implementations, target deck hashes, and compute. LoRA,
three-pack confirmation, X, and on-policy collection remain later independent
authority nodes.
