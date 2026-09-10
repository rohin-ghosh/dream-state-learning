# RML-D0 fluid/thermal world candidate B

**Status:** corrected exact CPU-world design candidate. This file is not
implementation authority, a test result, model/GPU authority, or scientific
evidence. Candidate A remains unchanged. Candidate B incorporates the finite
constructibility and adversarial-methods audits and must itself pass the full
architecture-deliberation and human-ratification path before code is written.

**Protocol literal:** `RML-D0-FT-B-V1`.

## 1. Exact scope

B preserves A's narrow role: one deterministic fluid/thermal fixed-deck CPU
instrument with stateful public actions, unique causal-era growth, fresh
`N/O/J/P` targets, R diagnostics, prospective grammar-conditioned P, exact
public-history and no-history references, counterfactual twins, necessity,
leakage, and evaluation isolation.

`X`, models, tokenizers, prompts, readers, learned DREAM/SLEEP, LoRA, GPU,
network, native-context placement, additional packs, on-policy collection,
locked model science, promotion, and scientific claims are unreachable. K0--K3
are structural cuts only. A later exact model bundle must bind `L_native`; D0
cannot call any cut native, post-native, developmental, or saturated.

The primary CPU geometry is the equal-weight mean of N/O/J/P. R is diagnostic.
No feasibility repair may weaken J/P, the `.35` shortcut ceiling, per-item
legal-history success, failure-as-zero, no replacement, or run/skip isolation.

## 2. Canonical objects and visibility

All durable records are RFC-8785/JCS UTF-8 over NFC strings followed by exactly
one LF. Hashes use the bytes before LF. Duplicate/unknown keys, floats, nulls,
invalid enums/handles, and non-NFC strings fail closed. An implementation may
encode the following definitions in JSON Schema but may not add a field or
choose a different projection.

Opaque handles match `[A-Z]{2}[0-9A-F]{12}`. Prefixes are `MF` module, `CF`
conditioner family, `XF` exchanger family, `VF` valve family, `CI` cartridge,
`LO` loop, `VA` valve, `CO` coolant, `SI` site, `GO` goal, `EP` episode, and
`EV` event. Handles are sampled uniformly without replacement from their
48-bit suffix domain by the sealed randomness ledger in section 16. Handle
draws are independent of hidden assignments, proposal attempts, and twin side.

The exact record families and key order-independent key sets are:

```text
PublicAction = {action_kind,arguments}
PublicState = {layout,position,action_count,remaining_actions,terminal,
  failure_kind,goal_handle,coolant,inventory,locker_items,consumed_items,
  loop,valve,run_stable,commit_succeeded,last_result_code}
PublicEvent = {action,event_handle,result_code,state_delta,text}
SourceEpisodeReset = {episode_handle,bench_kind,initial_public_state,
  permitted_action_count}
NextEraSchedule = {cut,next_cut,module_records,prediction_slots}
SchemaCommitment = {channel,commitment_id,cut,law_atom,predictions,
  public_root_event_handles,proposal_ordinal,status}
SchemaStatusAppend = {commitment_id,prediction_id,outcome_event_handle,
  comparison,status,append_ordinal}
TargetDescriptor = {cut,stratum,ordinal,layout_variant,initial_coolant,
  conditioner_family_handles,loop_module_family,exchanger_family,
  valve_family}
TargetPublic = {goal,initial_state,action_budget}
RecallGoal = {goal_handle,goal_kind,desired_coolant}
RecallFixture = {goal,initial_state,action_budget}
SelectionReceipt = {slot_id,attempt_count,rejection_code_counts,
  accepted_descriptor_hash,randomness_commitment_hash}
NecessityCertificate = {target_hash,variant,state_count,transition_count,
  minimum_depth,successful_plan_signatures,decisive_items,
  decisive_edge_ids,root_ids,verifier_input_hash,verifier_output_hash}
BeliefReceipt = {target_hash,projection_id,quotient_order,integer_masses,
  mass_denominator,bellman_root_hash,residual_numerators}
ScoreRecord = {target_hash,controller_id,disposition,actions,value_fraction}
ResourceRecord = {stage,workers,wall_ms,peak_rss_bytes,temp_bytes,
  sealed_bytes,states,transitions,pair_attempts,target_attempts}
GateReport = {protocol,predecessor_hashes,split_hashes,gate_values,
  failures,resource_hash,claim_firewall,passed}
```

`coolant`, `inventory`, `loop`, `valve`, FIELD_LOOP `goal`, `RecallGoal`,
prediction, and fraction are closed schema definitions, not free-form maps.
`RecallGoal.goal_kind` has the sole literal `ONE_APPLY_COOLANT`; its
`desired_coolant` is exactly `{viscosity,inhibitor}` with the enums in section
3. Fractions are reduced signed
integer numerator plus positive integer denominator. Public schemas contain no
world, pair, twin, seed/key, split, era ordinal, stratum, proof, answer,
acceptance, posterior, or score field.

Exclusive writers are: environment for public states/events; source scheduler
for resets/schedules; schema reference for commitments; comparator for status
appends; target generator for descriptors/public targets; certifier for proofs;
controllers for their own belief/action receipts; scorer for scores; supervisor
for resources/report. The target generator also exclusively writes immutable
`RecallGoal`/`RecallFixture` records. Only `PublicAction`, `PublicState`,
`PublicEvent`, `TargetPublic`, `RecallGoal`, and `RecallFixture` are
target-visible, with the recall records visible only during registered R.
Selection, hidden truth, proof, score, randomness, chronology receipts, and
audit records are never target-visible.

## 3. Public rendering and state

Descriptor classes are `D00,D01,D10,D11`. A pair-common skin independently
permutes the neutral phrases `ribbed brass panel`, `matte ceramic panel`,
`crosshatched alloy panel`, and `smooth graphite panel`. The permutation is
independent of hidden mappings. Component descriptions are fixed as in A.

Public text templates are exact:

```text
OBSERVED    "The {module_phrase} service board is visible."
MEASURED    "Gauge {public_test} reads {value}."
MOVED       "The technician is now at {site}."
ACQUIRED    "Cartridge {item} is now in inventory."
CONFIGURED  "Valve {valve} is set to {mode}."
APPLIED     "The coolant gauge reads viscosity {v}; inhibitor {i}."
RUN_STABLE  "The loop runs with stable pressure and nominal outlet temperature."
RUN_TRIPPED "The loop trips before stabilization."
COMMITTED   "Maintenance goal {goal} is complete."
STOPPED     "The maintenance attempt stops."
ILLEGAL     "The maintenance attempt ends after an invalid operation."
```

The complete public item state is:

```text
layout FIELD_LOOP|CONDITIONER_BENCH|VALVE_BENCH|EXCHANGER_BENCH
position DOCK|LOCKER|PLANT
action_count,remaining_actions 0..10
terminal boolean
failure_kind NONE|ILLEGAL|CAP|LOOP_TRIPPED|BAD_COMMIT
goal_handle GO...
coolant {handle,viscosity LOW|HIGH,inhibitor LEAN|RICH,
         outlet_temperature UNKNOWN|NOMINAL,pressure IDLE|STABLE}
inventory,locker_items ordered cartridge records
consumed_items ordered handles
loop {handle,module_family,module_descriptor,exchanger_family,
      certified_bypass boolean}
valve {handle,valve_family,mode UNSET|BYPASS|RECIRCULATE|PULSE|DIRECT}
run_stable,commit_succeeded boolean
last_result_code
```

Each cartridge record contains instance handle, conditioner family, module
family, module descriptor/phrase, location, and consumed bit. The hidden state
contains the two global laws, per-module mappings, and scorer truth only.

## 4. Actions and finite transition law

One action occurs per step:

```text
OBSERVE(object_or_site)
MEASURE(coolant,VISCOSITY|INHIBITOR|OUTLET_TEMPERATURE|PRESSURE)
MOVE(DOCK|LOCKER|PLANT)
ACQUIRE(cartridge)
CONFIGURE(valve,BYPASS|RECIRCULATE|PULSE|DIRECT)
APPLY(cartridge,coolant)
RUN(loop)
COMMIT(goal)
STOP
```

MOVE changes position; ACQUIRE at LOCKER moves one unconsumed locker item into
inventory; CONFIGURE at PLANT sets the public mode; APPLY at PLANT consumes one
inventory cartridge, applies its hidden SET transform, and exposes both coolant
bits. FIELD_LOOP RUN succeeds iff valve mode and exact coolant pair both match.
Certified-bypass EXCHANGER_BENCH RUN ignores valve and tests coolant only.
VALVE_BENCH RUN ignores exchanger and tests mode only. Success sets stable
pressure/nominal temperature; any failed RUN is terminal and emits only
RUN_TRIPPED. COMMIT succeeds only after stable RUN. OBSERVE/MEASURE repeat
public information but consume actions. Illegal, malformed, multi-action,
post-terminal, and cap-exceeding inputs terminate at value zero before partial
mutation.

## 5. Latent grammar and constructive sampler

Coolant is `(v,i) in {00,01,10,11}`. Conditioner codes are:

```text
T00=SET(v,0) T01=SET(v,1) T10=SET(i,0) T11=SET(i,1)
```

Valve modes use codes BYPASS=00, RECIRCULATE=01, PULSE=10, DIRECT=11.
Exchanger truth is one exact coolant pair.

Each module has descriptor `q` and twelve mappings:

```text
CF[m,S]    = A_C q xor b_C
CF[m,0..2] = a uniform permutation of the other three conditioner codes
XF[m,0..3] = a uniform permutation of the four coolant pairs
VF[m,S]    = A_V q xor b_V
VF[m,0..2] = a uniform permutation of the other three valve modes
```

Thus every module contains exactly one family for each conditioner code, each
exchanger truth, and each valve mode. The local choice count is
`3! * 4! * 3! = 864` per module. This is the smallest repair that makes a
four-code target inventory available in every world while retaining independent
per-module entropy.

Over GF(2), `A_C,A_V` use the six matrices M0..M5 from A and `b_C,b_V` are
independently uniform over four translations. Conditional on a matrix, each
channel therefore has four laws; the complete grammar has 24. E0 module
descriptors are D00,D01,D10. In E1--E3 the sole V-sparse module is D11 and at
least one dense module is also D11; other dense modules cycle
D00,D01,D10,D11. E0 determines each affine law; D11 is the first prospective
within-life production.

The matrix roster is fixed before any random draw. The four DEV joint pairs,
in order, are `(M0,M0),(M1,M0),(M0,M1),(M1,M1)`. For CPU pair slot
`s in 0..63`, set

```text
c_s = s mod 6
v_s = (floor(s/6) + c_s) mod 6
(A_C,A_V) = (M[c_s],M[v_s])
```

Thus C-matrix marginal counts are `[11,11,11,11,10,10]`; V-matrix marginal
counts are `[11,11,10,10,11,11]`. Every joint cell occurs one or two times.
M2..M5 are reported separately as production-holdout mechanics. This supplied
affine grammar earns only **grammar-conditioned prospective edge
reconstruction**, never learned schema discovery or compression.

The sampler draws exactly one constructive world per split slot from
`4^2 * 864^24`, conditional on that slot's fixed matrix pair. It does not scan
or replace worlds. The module grammar and literal selectors below guarantee
all source panels, four-code inventories, twins, bridge witnesses, and target
nonemptiness. There is no cross-slot orbit-uniqueness predicate: independent
slots may be structurally isomorphic, while independently sampled handles make
their records distinct. Unique causal growth means that, within a life, each
later era appends fresh module/episode/event handles and never repeats or edits
a credited root.

## 6. Corrected twin and nonemptiness theorem

The twin preserves all public bytes, initial states, source actions, target
descriptors, layouts, handles, budgets, and exchanger mappings. Hidden outputs
change by:

```text
tau_C: T00<->T01 and T10<->T11
tau_X: identity
tau_V: BYPASS<->RECIRCULATE and PULSE<->DIRECT
```

This is an involution and preserves the grammar. `tau_C` and `tau_V` are output
XOR translations, so affine matrices and DEV/holdout production sets remain
closed. The four public balance rows in section 7 make fixed-point-free tau_V
compatible with an exact V-sparse source marginal.

For any public initial coolant `u`, target acceptance sets the exchanger truth
to `r=u xor 11`. Because inventory contains exactly one family for each T code,
H's unique useful pair is `{SET(v,1-u_v),SET(i,1-u_i)}`. Under tau_C, the twin's
unique useful public-family pair is the two families whose H codes are
`{SET(v,u_v),SET(i,u_i)}`. The pairs are disjoint, both change both coolant bits
in their own world, and tau_V changes the correct CONFIGURE action. This proves
the paired target set is nonempty for every legal world.

The executable conditioner witness table is:

| `u` | exchanger `r=u xor 11` | H correct H-codes | twin-correct public families, named by H-code |
|---|---|---|---|
| 00 | 11 | `{T01,T11}` | `{T00,T10}` |
| 01 | 10 | `{T01,T10}` | `{T00,T11}` |
| 10 | 01 | `{T00,T11}` | `{T01,T10}` |
| 11 | 00 | `{T00,T10}` | `{T01,T11}` |

For H valve modes `[BYPASS,RECIRCULATE,PULSE,DIRECT]`, the corresponding twin
modes are `[RECIRCULATE,BYPASS,DIRECT,PULSE]`. The golden enumerator takes the
Cartesian product of these two tables, constructs all `4*4=16` targets, and
requires minimum depth nine on each side, exactly one unordered useful pair,
the displayed pair, disjoint pairs across sides, and the displayed distinct
mode. `NW_TARGET_00` is the first row with H valve BYPASS. This finite table is
also the nonemptiness proof; no sampled witness is needed.

## 7. Exact source episodes and schedule

Every source panel row is a fresh episode. Episode resets are public ordinary
initial states and do not count as actions/events.

`RESET(m,k,p,L,V,I,B)` is the literal constructor used below. It sets
`layout=L`, `position=PLANT`, `action_count=0`, `remaining_actions=k`,
`terminal=false`, `failure_kind=NONE`, a fresh diagnostic `goal_handle`, coolant
to a fresh handle with bits `p`, outlet `UNKNOWN`, pressure `IDLE`, inventory to
the ordered fresh cartridge list `I`, `locker_items=[]`, `consumed_items=[]`,
`run_stable=false`, `commit_succeeded=false`, and `last_result_code=NONE`. It
sets a fresh loop's module family/descriptor to `m`, exchanger family to the
row's named XF (otherwise the smallest XF handle in `m`), and
`certified_bypass=B`; it sets a fresh valve's family to the row's named VF
(otherwise the smallest VF handle in `m`) and mode `V`. The episode handle,
goal, coolant, loop, valve, and cartridge-instance handles are independent
source-handle-tape draws. The only permitted scheduled actions are those shown;
all omitted list fields are the empty ordered list and no hidden default exists.

```text
MODULE_OBSERVE:
  RESET(m,1,00,CONDITIONER_BENCH,UNSET,[],false);
  one OBSERVE(module).

CONDITIONER_ROW(family,start in {00,11}):
  RESET(m,1,start,CONDITIONER_BENCH,UNSET,[family cartridge],false);
  one APPLY(cartridge,coolant).

VALVE_ROW(family,mode in four canonical modes):
  RESET(m,1,00,VALVE_BENCH,mode,[],false), naming family as the row VF;
  one RUN(loop). The public reset explicitly states that the bench technician
  preconfigured the mode before the logged trial.

EXCHANGER_ROW(family,start in {00,01,10,11}):
  RESET(m,1,start,EXCHANGER_BENCH,UNSET,[],true), naming family as row XF;
  one RUN(loop).
```

Within a module, rows are MODULE_OBSERVE, conditioner family then start-state
order, valve family then mode-code order, exchanger family then coolant-code
order. Episode and event handles are allocated after the complete row schedule
is fixed, in row order, from the independent source-handle ledger.

A dense module has `1+8+16+16=41` events and 12 witnessed mappings. A V-sparse
module omits all four VF[m,S] rows: 37 events and 11 witnessed mappings. There
is no C-sparse module in B: omitting a conditioner output breaks the cutwise BE
multiset under tau_C and is unnecessary for the atoms-only P construct.

After each era's module rows, add four `VALVE_BALANCE` control episodes. Let
`mu` be the H output of the V-sparse module's omitted VF[m,S]. In the
handle-smallest dense D11 module, select the unique valve family whose H output
is mu. Run that same family once at each of all four canonical modes, using
fresh `RESET(dense_D11,1,00,VALVE_BENCH,mode,[],false)` episodes. These
already-witnessed-family repetitions credit no new mapping. The selector is
sealed with the bridge selector, reads H mappings only, and consumes no
randomness or event outcome. Because every family in the dense D11 panel
already appears at all four modes, the action-only projection learns only which
exchangeable handle is repeated; conditional on that projection, b_V remains
uniform and `Pr(mu=y)=1/4` for every mode y. The test enumerates all 4
translations, all `3!` local permutations, and all 4 selected-handle positions,
and requires integer posterior counts `[6,6,6,6]` after their common factor is
removed.

### Feasible four-event old/new bridge

After panels in E1--E3, the source builder uses E0 module 0, which is excluded
from J/O target family pools, and the era's first dense module, which is
excluded from N/J pools. Define `code(CF)` by H's sealed mapping. Enumerate
`(b,a,z)` lexicographically with `v<i`, `0<1`, `0<1`. For the first tuple
(necessarily the first enumerated tuple), let A be the unique E0-module-0
family with code `SET(b,a)`, B the unique family with code `SET(b,1-a)`, set
reset bit `u_b=0` and other reset bit `u_not_b=z`, and let
`x_b=a,x_not_b=z`. Select the unique exchanger family in the first dense module
whose truth is x. Equivalently, implementations may enumerate the finite
families, but they must return this same tuple/families. The selector reads
sealed H mappings only; it reads no event outcome, target, controller, or twin.
Its output is sealed before either trial. The source-action-string probe
receives the resulting public actions.

Two fresh certified-bypass EXCHANGER_BENCH episodes use the same reset coolant.
Each trial reset is
`RESET(recent_m,2,u,EXCHANGER_BENCH,UNSET,[one fresh A-or-B cartridge],true)`
with the selected recent XF. The episodes have distinct reset/object handles:

```text
trial A: APPLY old conditioner A; RUN recent exchanger
trial B: APPLY old conditioner B; RUN recent exchanger
```

H emits `[APPLIED,RUN_STABLE,APPLIED,RUN_TRIPPED]`; the twin emits
`[APPLIED,RUN_TRIPPED,APPLIED,RUN_STABLE]`. Exchanger truth and initial states
are identical because tau_X is identity. Valve state is certified bypass, so
the contrast cannot be a valve artifact. Golden `NW_BRIDGE_V0` is the first
table row: reset 00, A=T00, B=T01, exchanger truth 00; H is stable/tripped and
the twin is tripped/stable.

The exhaustive selector/nonemptiness witness is below. `z` is the other-bit
value, reset target bit is canonically zero, and A always names the H-matching
setter; every row must yield H `(stable,trip)` and twin `(trip,stable)`.

| b | a | z | reset u | exchanger x | A H-code | B H-code |
|---|---:|---:|---|---|---|---|
| v | 0 | 0 | 00 | 00 | T00 | T01 |
| v | 0 | 1 | 01 | 01 | T00 | T01 |
| v | 1 | 0 | 00 | 10 | T01 | T00 |
| v | 1 | 1 | 01 | 11 | T01 | T00 |
| i | 0 | 0 | 00 | 00 | T10 | T11 |
| i | 0 | 1 | 10 | 10 | T10 | T11 |
| i | 1 | 0 | 00 | 01 | T11 | T10 |
| i | 1 | 1 | 10 | 11 | T11 | T10 |

Formally, `A_H(u)=x`, `B_H(u)_b=1-a`, tau_C swaps those results, and tau_X
leaves x fixed. These eight rows are generated and replayed by Stage A; the
production selector intentionally chooses their first canonical row.

### Era counts

| Cut | New modules | New events | Cumulative events | Cumulative witnessed mappings |
|---|---:|---:|---:|---:|
| K0 | 3 dense | 123 | 123 | 36 |
| K1 | 2 dense + V-sparse + 4 balance + bridge | 127 | 250 | 71 |
| K2 | 5 dense + V-sparse + 4 balance + bridge | 250 | 500 | 142 |
| K3 | 11 dense + V-sparse + 4 balance + bridge | 496 | 996 | 285 |

No padding event exists. The schedule is the literal row expansion above and
is target-, outcome-, memory-, admission-, and controller-blind. It never
COMMITs and never contains a target state/goal or complete nine-action plan.

## 8. Cutwise twin-marginal equality

Define `BE(event,reset)` by replacing every opaque handle with its two-letter
kind, removing episode/event ordinal and chronology, and replacing persistent
family handles with relation kind plus descriptor class. Retain bench kind,
action kind, non-handle arguments, complete initial coolant/valve state,
result code, complete state delta, every public enum, and rendered text after
the same handle-kind replacement.

For every prefix K0,K1,K2,K3 and separately for each
`(era,bench_kind,action_kind,relation_kind)`, form the sorted multiset of
RFC-8785 bytes of BE. H and twin multisets must be exactly equal. Equality of
counts or byte lengths alone is insufficient. Dense conditioner panels contain
every T code twice, so tau_C merely permutes their BE rows. Dense valve panels
are balanced. For a V-sparse panel omitting mode `mu`, at configured mode y its
H stable count is `I[y!=mu]` and its twin stable count is
`I[y!=tau_V(mu)]`. Repeating the selected dense family at all four modes adds H
stable `I[y=mu]` and twin stable `I[y=tau_V(mu)]`. Each side therefore has one
stable and three trips at every y. This proves equality of the complete
`(configured_mode,result,state_delta,text)` multiset, not merely outcome totals.
tau_X is identity, module observations are byte-identical, and each bridge
contributes one stable and one trip on both sides. These facts prove equality
for every row class and hence every cut prefix; the implementation still
constructs and byte-compares the multisets. A mismatch invalidates the world
before targets.
ACTION_FREQUENCY and SOURCE_ACTION_STRING probes are run both on their declared
projections and on this complete BE multiset.

## 9. Prospective schema bytes and chronology

At each boundary, seal `NextEraSchedule` before invoking the deterministic
schema reference. The reference sees public history and the 24-law grammar,
enumerates all laws, and, only when the posterior set has size one, emits
exactly two immutable `SchemaCommitment`s at the boundary: one C and one V.
Each has `status=SEALED` and an ordered `predictions` array with one entry for
the channel's schema family in every scheduled next-era module. Thus each
channel has 3, 6, and 12 predictions after K0, K1, and K2; the across-channel
totals are 6, 12, and 24. A prediction entry is
`{prediction_id,module_handle,family_handle,descriptor,predicted_output}` in
module-handle order. The V-sparse module's V prediction is present even though
its outcome will be held out.

For each ordinary dense-panel schema-family outcome, the comparator appends
exactly one `SchemaStatusAppend` with comparison MATCH or CONTRADICTION. It
cannot append for an absent row, propose, normalize, repair, rank, resample, or
reveal distance. For a channel/commitment, define support as at least two MATCH
appends naming distinct next-era module handles and zero CONTRADICTION appends.
This derived status is `PROSPECTIVELY_SUPPORTED`; commitment bytes never
change. A P target may use the V-sparse prediction only when the V commitment
is supported by two distinct dense modules, the V-sparse prediction has no
outcome/status append, and the other eleven mappings in that same module have
ordinary source outcomes. Consequently the P edge is specific, precommitted,
and the only unwitnessed local edge.

The normative seal order is:

```text
source prefix seal
< next-era schedule seal
< schema commitment seal
< confirming source event seal
< status append seal
< P target descriptor creation
< P target public seal
< evaluation clone
```

P targets therefore literally do not exist at commitment. Pair viability is
not a world-acceptance filter; target generation occurs online after each
support seal and protocol failure is terminal rather than a reason to replace
the world.

Life-artifact record counts are separate from `PublicEvent` counts and are
never added to section 7. In every legal reference world all comparisons match:

| Cut seal | Cumulative NextEraSchedule | Cumulative SchemaCommitment | New / cumulative SchemaStatusAppend |
|---|---:|---:|---:|
| K0 | 1 | 2 | 0 / 0 |
| K1 | 2 | 4 | 5 / 5 (`3 C + 2 V`) |
| K2 | 3 | 6 | 11 / 16 (`6 C + 5 V`) |
| K3 | 3 | 6 | 23 / 39 (`12 C + 11 V`) |

The three omitted V-sparse predictions receive no append. A contradiction
still occupies its one append slot and makes the support/gate fail; it is not
deleted or replaced.

## 10. Pair-common target proposal kernel

K0 has no target or R item. At K1--K3, target slot order is cut, stratum
N/O/J/P, ordinal 0/1. Each descriptor is accepted once for the pair and copied
to both twins. After acceptance, the generator consumes fresh values in object-
kind/index order from the independent `target-handle` tape. The tuple
`(accepted_target_sequence_index,object_kind,index)` is only the private tape
cursor address: no handle is hashed or otherwise derived from pair, slot, cut,
stratum, ordinal, side, proposal counter, or hidden truth. The same sampled
values are copied to both twin targets.

For each proposal counter `n=0..4095`, the target-proposal tape supplies the
following independent uniform fields in this exact stratum-specific order; no
unused field is consumed:

```text
common: layout_variant in 0..3; initial_coolant u in Q
N: current_nonbridge_dense_module_index; exchanger_index in 0..3;
   valve_family_index in 0..3
O: E0_nonbridge_module_index in {module 1,module 2};
   exchanger_index in 0..3; valve_family_index in 0..3
J: E0_nonbridge_module_index in {module 1,module 2};
   current_nonbridge_dense_module_index; old_bit in {v,i};
   exchanger_index in 0..3; valve_family_index in 0..3
P: exchanger_index in 0..3
```

P fixes the loop to the current V-sparse module and valve to VF[m,S]. N and O
use their drawn module as loop, exchanger, valve, and conditioner module. For
J, `loop_module=recent_module`: its exchanger, non-schema witnessed valve, and
recent conditioner families all come from that drawn recent module; only the
other conditioner-bit families come from the drawn E0 module. Thus there is no
independent or ambiguous J loop draw. Modules used by the source bridge are
ineligible for N/J, and E0 module 0 is ineligible for O/J. Eligible module and
family lists are ordered by handle bytes.

Accept iff the selected exchanger truth equals `u xor 11`. The
`exchanger_index` addresses the four handle-ordered XF families in the selected
loop module. This has probability exactly 1/4 for every legal hidden world and
slot because those truths are a permutation of Q. No measured controller value,
Bayes value, target difficulty, prior target, or wall time enters acceptance.

Inventory construction after acceptance is deterministic and pair-common:

- N/O/P: the four conditioner families of the selected module, ordered by
  family-handle bytes. They realize all four T codes on both twins.
- J: select from the old module the two public families whose H codes set
  `old_bit` to 0/1, and from the recent module the two families whose H codes
  set the other bit to 0/1; order all four handles canonically. H and twin each
  need one old and one recent family, and their pairs are disjoint.

Explicitly, if `b=old_bit` and `c` is the other bit, H uses old
`SET(b,1-u_b)` plus recent `SET(c,1-u_c)`. The twin uses the public old/recent
families whose H codes are `SET(b,u_b)` and `SET(c,u_c)`. Those four families
are distinct, so both sides have one connected old-to-new plan and disjoint
correct pairs for every `(u,b)`; enumerating `4*2=8` cases is a required
nonemptiness golden.

The hidden-conditioned J inventory selector is part of the published kernel
and is included in BAYES-N completion counts. It reveals the bit partition but
not which family sets 0 versus 1. Fresh handles make all target public bytes
unique even if two structural descriptors coincide. No within-deck
descriptor-uniqueness rejection exists.

If 4096 attempts all reject, the protocol fails. The pair/world is not replaced
and no acceptance predicate changes.

## 11. Target semantics and J cut

Every primary item starts at DOCK, four cartridges at LOCKER, empty inventory,
fresh coolant u, and fresh FIELD_LOOP at PLANT. The unique exchanger truth is
u xor11. Minimal success is:

```text
MOVE LOCKER; ACQUIRE A; ACQUIRE B; MOVE PLANT;
APPLY A; APPLY B; CONFIGURE valve; RUN loop; COMMIT goal
```

The two APPLY actions commute. Exact state-quotient search must show minimum
depth nine, one unordered useful pair, one correct mode, and no alternative
success within ten actions.

### R diagnostic and K0

K0 registers zero primary targets and zero R fixtures; its source prefix is
used only for schema identification and engineering checks. At each K1--K3,
two pair-common R fixtures are copied to both sides. They use the handle-smallest
current dense module and a closed `RecallFixture`. Its initial state has four
fresh, unconsumed cartridge instances realizing that module's four conditioner
families already in handle-ordered `inventory`, `locker_items=[]`,
`consumed_items=[]`, `layout=CONDITIONER_BENCH`, `position=PLANT`,
`action_count=0`, and `remaining_actions=action_budget=1`; all other state
fields use the nonterminal RESET defaults. RUN and COMMIT are illegal in R.
R0 exposes initial coolant 00 and `RecallGoal(ONE_APPLY_COOLANT,10)`; R1 exposes
00 and `RecallGoal(ONE_APPLY_COOLANT,01)`. The only scoring action is exactly
one legal APPLY of one inventory instance, and value is one iff the environment
transition's resulting pair equals `desired_coolant`, else zero. Thus H respectively needs
the public families with H codes T01 and T11, while the twin needs those with H
codes T00 and T10. Each edge was witnessed in the current source panel. The
module, fixed starts/goals, family-handle ordering, and fresh handle tape fully
determine the fixtures; R consumes no proposal draw and never enters the
primary mean.

N uses a current dense module. O uses E0 module 1/2 and has no later direct
support. J uses one E0 and one current conditioner on the same coolant later
consumed by the current loop. P uses the current V-sparse module: all
conditioner/exchanger edges are witnessed; exactly `VF[m,S]` is unwitnessed and
predicted by the prospectively supported valve law.

The J registered dependency is not the source bridge. For each side it is the
exact target-local tuple:

```text
(old cartridge instance,
 old CF->T mapping edge,
 APPLY state transition setting old_bit,
 state-flow of that coolant bit into the recent RUN predicate)
```

`J_REGISTERED_OLD_TRANSFORM_CUT` runs four counterfactual variants:

1. remove that old cartridge instance from locker;
2. retain the instance but make its APPLY illegal for this target only;
3. delete the two original old instances, retaining only the target's two
   original recent instances (both set the recent bit);
4. delete the two original recent instances, retaining only the target's two
   original E0 instances (both set the old bit).

The same state-quotient planner must find no success within ten actions in all
four. Variants 1--2 remove the registered useful old transform; variants 3--4
leave setters for only one of the two required bits. A deletion removes the
named instance from both `locker_items` and the four-position item map before
the initial state is sealed; it does not renumber remaining positions, refund
actions, substitute a family, or change mappings. The hidden world is otherwise
unchanged; no global mapping is deleted, and source history/source bridge are
untouched. This is the exact J necessity semantics.

## 12. P atoms-only measure

`ATOMS_ONLY_COMPLETION` is an explicit model-class ablation, not the actual
affine-world posterior. For one sealed accepted P target, hold fixed all public
bytes, witnessed atoms, target conditioner/exchanger truth, target logistics,
twin side, and selection receipt. Delete only the schema atom/grammar and
replace the omitted `VF[m,S]` edge by each mode in canonical order with integer
weight one. Do not rerun target or pair selection and do not require the four
completions to extend an affine law.

Target acceptance is invariant because it depends only on exchanger truth and
u; all public projections are identical because valve truth is hidden. The
four completion weights are therefore exactly `[1,1,1,1]`. A wrong RUN is
terminal, while the nine-action plan has room for only one RUN, so the optimal
WITNESS-GRAPH value is exactly 1/4. SCHEMA-GOLD and PROGRAM-SEARCH must be 1.

Golden `NW_P4` fixes u=00, exchanger=11, inventory all four T codes, and
enumerates BYPASS/RECIRCULATE/PULSE/DIRECT: exactly one of four minimal plans
succeeds in each completion and all target-visible bytes hash identically.

## 13. Exact public-history and no-life controllers

HW-SOLVE sees hidden target truth. LH-ORACLE sees only legal public source
events through the cut, the published grammar, supported prospective records,
target public bytes, and its own item outcomes. PROGRAM-SEARCH receives the
same legal history and grammar; SCHEMA-GOLD receives witnessed atoms plus the
supported schema atom. LH/PROGRAM may decode an edge only from its complete
panel and must derive P only through the precommitted law. Every accepted item
must score 1.

BAYES-N knows the ex-ante generative measure, target kernel, twin involution,
and action law. It sees target public bytes and its own item outcomes, but no
source outcomes, random tapes, slot/cut/stratum/ordinal, side, proposal counter,
rejection receipt, other target, or audit record.

### Ex-ante sample space

Before any split is drawn, the public roster fixes matrices and independently
uniform finite tapes select global translations, local permutations, skins,
target proposal fields, handles, and evaluation side. The deterministic bridge
selector consumes no random row. The
revealed replay ledger is scorer-only until all CPU decisions seal. BAYES-N
integrates the uniform tapes and uniform hidden registry role; it may not
enumerate the later-revealed realized ledger. The public protocol hash is only
a domain tag and is not a random seed.

For one target, the sufficient hidden truth class is the mapping of four public
inventory positions to T codes (at most 24 legal permutations), exchanger truth
(fixed by accepted visible u for the generator-aware controller), and valve
mode (4), plus the J old/recent bit partition already public through inventory
ages. The loose schema-independent envelope remains 4096; the implementation
must enumerate only positive-mass classes.

### First-accept counting recurrence

For hidden class h and slot j, let `p_j(d)` be the exact product of reciprocal
field-domain sizes for descriptor d, and `A_j(h,d)` the structural acceptance
indicator. Define integer/rational recurrence:

```text
R_0(h)=1
W_0(h,d)=0
R_{n+1}(h)=R_n(h) * sum_d p_j(d)*(1-A_j(h,d))
W_{n+1}(h,d)=W_n(h,d)+R_n(h)*p_j(d)*A_j(h,d)
for n=0..4095
```

Here `sum_d p_j(d)A_j(h,d)=1/4` for every h, proved by the exchanger-permutation
golden. Hence `R_n=(3/4)^n`, total acceptance mass is
`1-(3/4)^4096`, and conditional first-accepted descriptor mass is
`W_4096(h,d)/(1-(3/4)^4096)`. Equivalently it is
`4*p_j(d)*A_j(h,d)`; the cap cancels only because the exact acceptance
probability is h-invariant. The implementation must compute the recurrence,
the closed form, and equality as reduced rationals. There is no pair-level
first-accept: exactly one constructive world is drawn per slot, and target
exhaustion fails rather than selecting another world.

Let hidden registry role rho range uniformly over the 3,072 scored CPU entries
`(slot,cut,stratum,ordinal,side)`; rho's matrix pair is fixed by section 5's
roster but rho is not visible to BAYES-N. For visible target bytes v and
within-item outcome history o, the exact unnormalized mass is:

```text
M(h;v,o) = sum_rho sum_d prior_count(rho,h) * W_4096(h,d) *
  I[Render(rho,h,d)=v] * I[Outcome(rho,h,d)=o]
Pr(h|v,o) = M(h;v,o) / sum_h' M(h';v,o)
```

`prior_count` is the exact number of uniform translation/local-permutation tape
completions compatible with rho and h, including the published J
age/bit-conditioned inventory selector. Hidden cut, stratum, ordinal, side, and
production-roster position are summed, not inferred from handles. Handle and
skin factors cancel because their tapes are independent and target handles are
fresh post-acceptance draws. For fixed rho, unused modules integrate to
`864^k`; enumerate its fixed `(A_C,A_V)`, all `4*4` translation pairs, and
target-local module assignments at separator
`(b_C,b_V,target-local assignments)`. Every other module is a leaf with summed
factor 864. Summing rho performs the required six-matrix roster mixture. No
pair-wide target-existence or orbit-distinctness factor is present because
worlds are never accepted/rejected by target outcomes or cross-slot matches,
and the constant target exhaustion probability is h-invariant.

Test the recurrence against brute-force reduced grammars with two transforms,
two modes, two proposal values, caps 1..4, both sides, and every hidden slot
mixture. Production code must also enumerate all positive target-local classes
and agree with the factorized count exactly.

Bellman state is `(public_target_state, reduced_integer_mass_vector,
remaining_actions)`. Enumerate every legal action; update by exact canonical
outcome bytes; maximize terminal item score with canonical action-byte ties.
All posterior sums equal one and every Bellman residual numerator is zero.

## 14. History/state quotient and compact certificates

No controller or certifier enumerates history strings. For fixed hidden truth,
the exact planner key is:

```text
(position,remaining_actions,coolant_bits,
 item_status[4] where status is LOCKER|INVENTORY|CONSUMED,
 valve_mode,run_stable,terminal,failure_kind,necessity_mask)
```

Action count is `10-remaining`; outlet/pressure/commit are deterministic from
run/terminal and need not duplicate the key. Handles map bijectively to the
four item positions and are restored only when rendering an action. For Bayes,
append the reduced belief vector hash plus its content-addressed mass object.

This quotient is bisimulation-preserving because future legality, public
outcome, score, used cartridge set, valve mode, and every J/P intervention are
functions of the key and fixed truth/belief only. A proof test exhaustively
compares quotient and literal histories through depth six on all 16 small
target/twin goldens, then inducts one step over the closed action transition.

Certificates store one canonical predecessor/action per reached key, minimum
depth, exact count and hashes of alternative shortest signatures, and aggregate
transition counts. They do not store every successor byte. The verifier
replays canonical actions from target bytes and truth/ablation hash, checks all
reached-state hashes and necessity variants, and reproduces the root hash.
Maximum sealed certificate size is 64 KiB per target plus one shared 4 MiB
transition-template dictionary per protocol.

## 15. Leakage probes, scoring, cardinalities, and gates

Target-only, state-only, identifier-only, renderer-only, passive-signature,
action-frequency, source-action-string, and full adaptive BAYES-N use exact
Bayes-optimal decisive-plan prediction/action under their named projection.
Each projection conditions on the kernel above. Injecting the decisive pair and
mode separately into every projection must make its scorer-tainted fork value
1. TWIN-HISTORY and fixed-point-free within-type/era BIND-SHUFFLE remain binding
controls. Scorer forks cannot write any source/target artifact.

Per item: nine-action success=1, ten-action success=9/10, everything else=0.
Aggregation is two targets within side, twins within pair, equal strata.

Exact shapes:

```text
DEV predecessor pairs                         4
CPU pairs                                    64
dormant reserve ledgers                      16
target cuts                         K1,K2,K3 only
K0 targets/R                                  0
primary strata                                4
pair-common target slots/CPU 64*3*4*2      1536
evaluated target copies       1536*2        3072
R pair-common fixtures        64*3*2         384
R evaluated copies            384*2          768
proposal cap/target slot                    4096
CPU accepted-slot proposal-attempt ceiling 6,291,456
DEV accepted-slot proposal-attempt ceiling   393,216
combined DEV+CPU ceiling                    6,684,672
world draws/attempts DEV+CPU                       68
```

Every rejected target proposal, including those before accepted descriptors,
counts. R fixtures are deterministic from witnessed transitions and consume no
proposal attempts. Reserves are unopened and absent from these counts.

Pass requires: every HW/LH/PROGRAM/applicable SCHEMA item=1; every named
shortcut and BAYES-N mean <=7/20 separately per cut/stratum and nearest-rank
p90 <=9/20; WITNESS-GRAPH P=1/4 and schema/program P=1; twin-history and binding
controls <=7/20 with the A loss formula; every twin target byte collides and
correct pair/mode differs; every `J_REGISTERED_OLD_TRANSFORM_CUT` variant=0;
source PublicEvent counts `[123,250,500,996]`, witnessed mappings
`[36,71,142,285]`, and cutwise BE
multisets match; schema chronology and exactly-one-unwitnessed-edge P pass;
answer injections=1; run/skip hashes match; resource stages pass.

Failure invalidates B. No cell, key, world, target, threshold, or reserve is
replaced.

## 16. Randomness ledger and replay

The seed policy literal is `INDEPENDENT-PACKED-LEDGER-NO-PUBLIC-SEED-V1`. There
is no shared master seed and no deterministic derivation from the protocol
hash. The authoritative replay seed is the complete revealed ledger itself.
The protocol hash is public domain separation only. Before construction, the
supervisor samples independent finite uniform tapes for `world-law`,
`world-local`, `skin`, `source-selector`, `source-handle`, `target-proposal`,
`target-handle`, `evaluation`, `probe`, and `statistics`. Each tape row is
`{namespace,draw_index,domain_size,value}` with `0<=value<domain_size`; draws
are uniform in their declared finite domain. The ledger is sealed and its hash
published before generation, but values remain scorer-only until the terminal
CPU report. Afterward it may be revealed for exact replay.

The row object above is logical, not repeated JSON. Serialization is one JCS
manifest containing namespace order, row count, and ordered domain sizes, then
one binary payload per namespace: proposal values are `uint16be`, handle
available-set indices are `uint48be`, booleans are one byte, and other domains
use the smallest of `uint8be,uint16be,uint32be,uint64be` that holds
`domain_size-1`. Payload hashes are in the manifest. All 4 DEV, 64 CPU, and 16
dormant-reserve proposal rows through cap 4096 are prepacked; the fixed maximum
proposal payload is `84*3*2*4096*(5+5+7+3)*2 = 82,575,360` bytes. Stage A uses
only its micro-fixture tape; the complete production randomness bundle must be
below 100 MiB or Stage B fails. `source-selector` is a committed
zero-row namespace, proving that the bridge used no random or outcome-adaptive
choice.

Every consuming algorithm above gives its draw order. A draw is consumed even
when its proposal rejects. No runtime RNG, retry draw, modulo reduction,
shared master seed, or handle derivation from hidden/attempt metadata exists.
Unused reserve tapes remain sealed. Exact Bayes is defined over the product
uniform tape distribution, not over knowledge of the realized replay ledger.

## 17. Evaluation isolation

The only graph is:

```text
SourcePrefix -> ReadOnlySnapshot -> DisposableEvaluation -> AuditOnlySink
SourcePrefix -> DeterministicSuffix ----------------------> SourceSeal
```

At every cut, seal source bytes/state, schedule, schema commitments/status,
random-tape cursor, and suffix intent. Compare evaluation-run versus skip.
Source events/state, commitments/status, future target descriptors/handles,
all tape cursors, and final hashes must match exactly. Evaluation processes have
read-only snapshots, fresh caches/workspaces, write-denied source descriptors,
and no generator/scorer imports. Cross-life canaries cover events, handles,
caches, temp paths, processes, and file descriptors.

## 18. Two-stage resource preflight and gate ceiling

Feasibility is a hypothesis until both stages pass; a preflight pass is
engineering evidence only.

### Stage A — exhaustive micro-preflight

Run all 16 `NW_TARGET` twin/mode goldens, 8 bridge goldens, all 4
V-sparse/balance marginals and action-only `[6,6,6,6]` counts, `NW_P4`, reduced
first-accept caps 1..4, quotient-vs-history tests, all J cuts, and canonical
record goldens with one worker. Limits: 60 seconds, 512 MiB RSS, 50 MiB temp,
25 MiB sealed, 2 million transitions. Any failure blocks Stage B.

### Stage B — four-pair DEV preflight

The four immutable DEV pairs run through the exact production generator,
source, all K1--K3 targets, certificates, Bayes/probes, isolation, and sealing
using the same executable paths and four-worker process model as CPU. Limits:
10 minutes, 4 GiB aggregate RSS, 250 MiB temp, 125 MiB sealed, 10 million live
states, and 40 million transitions.

Let `t_max`, `b_max`, `s_max`, and `x_max` be maximum per-pair worker wall,
sealed bytes, peak worker RSS, and transitions. CPU release additionally
requires:

```text
16*t_max + supervisor_stage_B_wall <= 90 minutes
4*s_max + measured_supervisor_peak <= 6 GiB
64*b_max + fixed_protocol_bytes <= 1.5 GiB
64*x_max <= 160 million transitions
maximum simultaneous live states extrapolates <= 12 million
```

The 90-minute/6-GiB/1.5-GiB bounds preserve at least 25% margin under the hard
gate limits. No mean-rate extrapolation is allowed; use maxima.

### CPU gate hard limits

```text
network/model/GPU calls                  0
workers                                  4
wall                                     2 hours
aggregate RSS                            8 GiB
temporary bytes                          2 GiB
sealed bytes                             2 GiB
simultaneous live states                16 million
total transitions                      200 million
world draws                             64 (CPU; DEV already sealed)
CPU target proposal attempts     <=6,291,456
```

Counters are checked before dispatch. Hitting a limit yields a nonpassing
resource receipt. It never permits approximation, pruning of positive mass,
fewer pairs/targets/controllers, weaker proofs, or a longer unregistered run.

## 19. Proposed paths and tests

After separate ratification, implementation authority is limited to these
paths (this plan does not create them):

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
research_loop/goldens/rml_d0/nonemptiness_targets.json
research_loop/goldens/rml_d0/nonemptiness_bridges.json
research_loop/goldens/rml_d0/first_accept_toys.json
research_loop/goldens/rml_d0/canonical_records.json
```

No model, prompt, provider, GPU, paper, promotion, or network path is allowed.
Required tests are:

```text
RMLD0B_01_SCHEMA_AND_CANONICAL_RECORD_GOLDENS
RMLD0B_02_SOURCE_RESET_ROWS_COUNTS_AND_CUTWISE_BE
RMLD0B_03_TAU_X_IDENTITY_TARGET_NONEMPTINESS
RMLD0B_04_COMPLEMENTARY_CERTIFIED_BYPASS_BRIDGE
RMLD0B_05_PAIR_COMMON_PROPOSAL_DRAW_LEDGER
RMLD0B_06_P_ATOMS_ONLY_COMPLETION_FOUR_WAY
RMLD0B_07_FIRST_ACCEPT_RECURRENCE_AND_FACTOR_COUNTS
RMLD0B_08_J_REGISTERED_OLD_TRANSFORM_CUT
RMLD0B_09_STATE_QUOTIENT_BISIMULATION_AND_COMPACT_PROOFS
RMLD0B_10_K0_R_CARDINALITY_AND_ATTEMPT_ACCOUNTING
RMLD0B_11_LEGAL_HISTORY_BAYES_AND_LEAKAGE_GATES
RMLD0B_12_SCHEMA_CHRONOLOGY_HASH_CHAIN
RMLD0B_13_RUN_SKIP_AND_CAPABILITY_ISOLATION
RMLD0B_14_STAGE_A_STAGE_B_RESOURCE_PREFLIGHT
RMLD0B_15_CPU_GATE_AND_CLAIM_FIREWALL
```

## 20. Meaning of pass

A pass establishes only deterministic conformance of a finite CPU instrument:
public source mechanics, local causal growth, connected J, grammar-conditioned
prospective P headroom, target/twin nonemptiness, exact references, leakage,
necessity, isolation, and bounded execution. It is not evidence that a model
learned, remembered, dreamed, composed, crossed context, improved with age, or
supports an RML paper claim. Every model/text/LoRA or X step remains a new
predecessor-bound human decision.
