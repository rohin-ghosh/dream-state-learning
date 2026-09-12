# M-core v4: exact crossed two-cycle relay contract

Date: 2026-09-12 UTC

Status: independent watcher design only. This note supersedes
`2026-09-12_m_core_minimal_exact_two_cycle_design_v3.md`. It is a zero-fit
specification repair responding to both fresh v3 REWORK audits. It changes no
builder source, benchmark, child, model, tokenizer, adapter, checkpoint, job,
GPU state, resource, coordination record, scientific claim, release, or
submission. Nothing here is evidence that the specified materializer,
checker, reader, or experiment exists or passes.

## 0. Exact scope, claim, and six-build allocation

This proposed defensible design uses at most six trained carriers per root:

```text
SLEEP-1 matched triplet, always first
  1. FULL_OLD
  2. SOURCE_DERANGED_OLD
  3. DREAM_DERANGED_OLD

SLEEP-2 matched triplet, only after every S1 gate passes
  4. FULL_NEW_h0
  5. FULL_NEW_h1
  6. FULL_OLD_PLUS_PAD
```

It does not claim that six is a global minimum. No corrupt S1 arm is rebuilt
at S2. Source carriage is identified at C, selected-link carriage at B,
first-write dependence at B/C, and outcome-specific old+new reconstruction at
D.

The only releasable sentence is:

> In a finite typed benchmark, a qualified writer carried records compiled
> from a crossed contingency in a child's authentic public actions and
> outcomes and from a child-selected pre-blueprint pair set identified by a
> registered public ablation signal. A reset clean actor used typed reads to
> complete two goal-conditioned old-memory traces. After an authentic public
> outcome, a second clean-base cumulative write preserved the required old
> link and added the outcome-specific new row needed for a delayed action.

Permitted terms are **compiler-mediated crossed experiential binding**,
**child-selected evidence-indicated pair set**, **typed functional
traversal**, and **two-cycle clean-base cumulative reconstruction**. The
design does not identify child-specific DREAM intelligence, mechanically
unrecoverable organization, native learned search, in-place growth,
open-world graph learning, recurrence, general retention, online learning, or
a whole-organism effect.

The public ablation evidence mechanically identifies the useful pair set.
Conditional on a complete valid evidence table, the registered necessity
rule reaches 100%. Child selection is provenance, not an intelligence claim.

## 1. Content-addressed materialization package

### 1.1 Required package and hard prerequisite

Before TEXT, reader-model acceptance, or any M fit, one immutable package must
exist at a content-addressed path of the form:

```text
m_core_v4/<protocol_sha256>/
  protocol.json
  root_generator.json
  schemas/*.schema.json
  canonical_examples/*.json
  canonical_examples/*.bin
  alias_pool.json
  action_rosters.json
  candidate_rosters.json
  availability_relations.json
  transition_system.json
  rpc_machine.json
  control_registry.json
  order_tables.json
  schedule_tables.json
  allowed_difference_maps.json
  wstar_binding.json
  reader_binding.json
  manifests/{TEXT,DEV,CONF}.json
  fixtures/*
  receipts/*
```

All JSON is RFC 8785/JCS UTF-8 with exactly one trailing LF when stored.
Embedded arbitrary bytes use unpadded RFC 4648 base64url; the JSON contains
both `bytes_b64u` and lowercase hexadecimal SHA-256. Schemas set
`additionalProperties:false`, enumerate every required field, and forbid
NaN/Infinity and implementation-dependent integer widths.

`wstar_binding.json` must bind the exact writer `W*` that already passed W0
and the old/new coexistence canary. `reader_binding.json` must bind the exact
tokenizer, renderer, reader prompt bytes, YES/NO token IDs, score equation,
normalization, tie rule, threshold, model/base digest, and RPC release rule.
Until both exist, materialization exits `UNMET_WSTAR_OR_READER_BINDING`; it
must not choose defaults.

### 1.2 Exact deterministic generator

The package binds a public 32-byte `master_seed`. Define:

```text
FRAME(tag, parts...) =
  ASCII("MCORE-V4\0") || U32BE(len(tag)) || UTF8(tag) ||
  concat(U64BE(len(part)) || part for part in parts)

H(tag, parts...) = SHA-256(FRAME(tag, parts...))
R(cohort,index,domain,counter) =
  H("rand", master_seed, UTF8(cohort), U32BE(index),
    UTF8(domain), U64BE(counter)) interpreted as unsigned U256BE
```

`randbelow(n)` consumes successive counters in its named domain, rejecting
values `x >= floor(2^256/n)*n`, and returns `x mod n`. Fisher--Yates uses
`randbelow(i+1)` for descending `i`. Domains never share counters.

For root `(cohort,index)`, materialize in this exact order:

1. `k = first_128_bits(H("root-nonce",master_seed,cohort,index))`.
2. Allocate every class-local visible alias/handle table using domains that
   depend only on `(cohort,index,object_class,slot)`. Complete all tokenizer-
   shape rejection before drawing or assigning a semantic role.
3. Draw `b`, then `z`, from separate binary domains.
4. Draw an index uniformly from the lexicographically enumerated 28 unordered
   pairs of `{0,...,7}`; call the pair `{u0,u1}`.
5. Draw one assignment bit; map the pair to `(u_A,u_B)` and
   `(q_A,q_B)=(q_uA,q_uB)`.
6. Draw one bit selecting `u_D` from `{u_A,u_B}`.
7. Fisher--Yates shuffle the six remaining lanes; first three are left-decoy
   and last three right-decoy.
8. Draw `dream_shift` uniformly from `{1,...,7}` and define the presealed
   fixed-point-free derangement `pi(i)=(i+dream_shift) mod 8`.
9. Independently shuffle each registered event/presentation stratum.
10. Draw S1 device, S2 device, S1 condition-order, S2 condition-order, and
   each inference-order permutation from the schedules in Section 8.
11. Materialize both `h=0` and `h=1` potential-outcome branches. They are
    repeated measures, not root draws.

The ablation arena's complete binary table is fixed, not sampled:

```text
useful lane:      joint=1, left=0, right=0, nuisance=0
left-decoy lane:  joint=1, left=1, right=0, nuisance=0
right-decoy lane: joint=1, left=0, right=1, nuisance=0
```

Foundation, support, source, C, and PAD outcomes are specified below. No
unlisted random draw exists. A root whose aliases fail a token-shape
precondition is rejected before semantic roles are assigned; rejection uses a
new pre-role alias-pool counter only. Once a root enters a manifest, no retry,
replacement, relabelling, or outcome-dependent regeneration is legal.

### 1.3 Visible handles and immutable provenance

Visible episode, node, action, row, and citation handles are assigned from a
pre-role table of token-isomorphic opaque aliases. Their byte allocation does
not contain `condition`, `derivation_kind`, `b`, `z`, `h`, useful-lane role,
truth, donor, or expected result. Each handle maps to exactly one byte string.

The private mapping from visible handle to canonical object, authentic event,
donor event, derivation kind, condition, and hidden role exists only in the
`AuditEnvelope`. A changed payload receives a different preallocated visible
handle; no handle ever changes meaning. Joint noninterference is checked over
the complete tuple of simultaneously visible handles, not one marginal at a
time.

### 1.4 Materializer and independent checker contract

The future implementation must expose exactly these deterministic interfaces:

```text
python -m organism_v6.m_core_v4.materialize \
  --spec <protocol.json> --cohort TEXT|DEV|CONF \
  --master-seed-hex <64 hex> --out <empty-dir>

python research_loop/checks/check_m_core_v4.py \
  --protocol-sha256 <hex> --bundle <dir> --out <receipt.json>
```

The first command is the sole materializer. The second must be an independent
implementation: it may read only the published package and emitted bundle,
must not import the materializer/generator modules, and recomputes generator
draws, schemas, canonical bytes, graph truth, offsets, availability theorem,
PAD/S1 tensor differences, schedule, and manifest digests. Both commands must
be deterministic on a sterile CPU fixture. A byte-for-byte repeat and a
materializer-versus-checker digest match are Stage-0 gates. This memo does not
implement either command.

## 2. Capability-separated canonical schemas

### 2.1 Capability matrix

Four capabilities are disjoint OS processes with deny-by-default file/network
permissions:

| object/field class | actor | recognition scorer | compiler | endpoint scorer | audit |
|---|---:|---:|---:|---:|---:|
| `ActorEpisodeInput`, public goal/state/menu/catalog | yes | request fields only | declared public subset | trace subset | yes |
| candidate row bytes | returned row only | one candidate at a time | no | cited returned row | yes |
| reader score/order/index/threshold/timing | no | yes | no | no | yes |
| source public event slice | no after reset | no | yes | no | yes |
| child declaration/dispatch/public outcome | own public bytes | no | yes | public trace | yes |
| environment transition graph | current-state observation only | no | no | read-only opaque handle | yes |
| `b,z,h`, roles, theorem, expected trace | no | no | no | validation oracle only | yes |
| donor/provenance/derivation/condition/device labels | no | no | no | no | yes |

The endpoint scorer receives a non-branching read-only `environment_handle`
and public trace bytes. It exposes only a binary score after the episode. The
actor and neural recognition scorer never receive adjacency, slot indices,
route bijections, outcome-world transitions, hidden graph handles, or expected
traces.

### 2.2 Public schemas

Every public object has `v:"mcore.v4"`; all handles are fixed-length opaque
strings. The exact schemas have these required fields and no others:

```text
ActorEpisodeInput {
  v, episode_handle, phase:B|C|D,
  actor_model_sha256, system_prompt_b64u, system_prompt_sha256,
  goal:PublicGoal, current_state_handle,
  legal_action_surfaces:[ActionSurface], public_menu:PublicMenu|null,
  memory_catalog:MemoryCatalog, decode_config:DecodeConfig
}

PublicGoal {
  goal_handle, start_handle, target_handle, route_cue_handle|null,
  desired_source_outcome_handle|null, read_budget, action_budget
}

ActionSurface { action_handle, verb_surface }

MemoryCatalog {
  v, legal_query_types:[enum], public_anchor_handles:[string],
  candidate_schema_sha256, reads_remaining
}

RecognitionRequest {
  v, phase, query_type, public_state_handle, public_goal_handle,
  public_anchor_handles:[string], candidate_schema_sha256,
  call_ordinal, reads_remaining
}

MemoryRow {
  v, row_handle, query_type, key_handles:[string],
  ordered_action_handles:[string], destination_handles:[string],
  visible_citation_handles:[string,string]
}

MemoryReturn {
  v, status:FOUND|MISS|BLOCKED, query_fingerprint_sha256,
  row:MemoryRow|null, fixed_pad_b64u:string|null, reads_remaining
}

PublicActionEvent {
  v, event_handle, authorization:MEMORY_ROW|PUBLIC_DISPATCH,
  authorization_handle, action_handle, pre_state_handle
}

PublicObservation {
  v, event_handle, action_event_handle, observation_handle,
  outcome_surface, post_state_handle, logical_tick
}

PublicExecutionTrace {
  v, episode_handle, phase, actor_input_sha256,
  events:[PublicReadEvent|PublicActionEvent|PublicObservation|
          PublicDeclaration|PublicCompilerDecision],
  terminal_state_handle, reads_used, malformed_count
}
```

`PublicReadEvent` stores `request_b64u/request_sha256` and
`return_b64u/return_sha256`; raw bytes reside in separate immutable blobs.
`PublicExecutionTrace` contains no root ID, condition, build, h/b/z, role,
donor, provenance, device, schedule, score, expected answer, or derivation
label.

`DecodeConfig` binds algorithm, temperature, top-p/top-k if used, maximum
tokens, stop bytes, and an opaque RNG-commitment digest. It never reveals a
condition/h-specific seed. Actor-visible node/action aliases are jointly
token-isomorphic and role-independent by the package receipt.

### 2.3 Recognition-scorer and endpoint-scorer schemas

The neural recognition process receives exactly:

```text
RecognitionScorerInput {
  v, reader_prompt_b64u, reader_prompt_sha256,
  request_b64u, request_sha256,
  candidate_row_b64u, candidate_row_sha256
}

RecognitionScorerOutput {
  v, yes_logscore_hexfloat, no_logscore_hexfloat,
  aggregate_hexfloat, scorer_input_sha256
}
```

Hexadecimal IEEE-754 encodings avoid JSON float ambiguity. The output is
private to the reader backend/audit. There is no root/episode/condition/h,
graph, candidate position, availability, correct-answer, or expected-trace
field. Candidate order is held by the RPC backend, not the scorer model.

The pure endpoint scorer receives:

```text
EndpointScoreInput {
  v, public_trace_sha256, environment_handle
}
EndpointScoreOutput { v, valid:0|1, failure_code }
```

`environment_handle` is a constant-shape lookup token into an isolated
read-only validation service. It cannot be queried by actor, reader, or
compiler and cannot change actor-visible bytes.

### 2.4 Compiler and audit schemas

The compiler receives exactly:

```text
CompilerInput {
  v, compiler_phase:LINK_ADMISSION|NEW_ROW_ADMISSION,
  public_source_events:[PublicActionEvent,PublicObservation]*,
  public_ablation_events:[PublicActionEvent,PublicObservation]*,
  child_selection:PublicPairSelection|null,
  child_declaration:PublicDeclaration|null,
  dispatch_event:PublicActionEvent|null,
  public_outcome:PublicObservation|null,
  public_task_law_sha256
}

CompilerDecision {
  v, status:ADMIT|NO_ADMISSION,
  declaration_faithful:0|1, public_posterior:[0|1],
  admitted_row:MemoryRow|null,
  cited_public_event_handles:[string]
}
```

The compiler has no h/b/z/role/answer field. Its public task-law blob contains
the finite algorithms in Sections 3 and 5, not a root instance. Capability
tests deny access to environment truth, endpoint scorer, reader scores,
expected traces, donor maps, and audit objects.

PAD extraction is not a public READ. The audit-only interface is:

```text
AuditExtractRequest { v, carrier_sha256, audit_key_handle }
AuditExtractReceipt { v, status, extracted_row_sha256, scorer_receipt_sha256 }
```

P/Q never become actor anchors and no seventh public query type is introduced.

`AuditEnvelope` alone contains root/condition/h/b/z, roles, schedule/device,
fit RNG, donor/derivation/provenance mappings, raw scorer vectors/order/timing,
environment graph digest, expected trace, compiler capability log, tensor/work
receipts, and digests of all public objects. Forbidden-field tests serialize
each lower-capability object and prove no audit key/name/value appears.

## 3. Typed world, evidence, and source crossing

### 3.1 Complete action/state geometry

The hidden environment has states:

```text
S; U_0...U_7; B; C; T_A; T_B; D;
F_ROUTE; F_(i,j); F_SHARED_j; F_TERMINAL_j; F_D_j; P; Q
```

At each state the public actor sees only current observation and 32
token-isomorphic action surfaces, never transitions or slot numbers.
Environment semantics are:

```text
S --a_j--> U_j for j<8;  S --a_j--> F_ROUTE for j>=8

U_i --b_j--> B iff j=i;
U_i --b_j--> F_(i,j) otherwise                 j=0..31

B --c_0--> C;
B --c_j--> F_SHARED_j otherwise                j=1..31

C --t_A--> T_A; C --t_B--> T_B;
t_0 and t_1 are the pre-role aliases assigned to t_A and t_B;
C --t_j--> F_TERMINAL_j for j=2..31

in outcome world h:
C --n_h--> D;
C --n_j--> F_D_j for every j!=h                 j=0..31

P --p_0--> Q; all other pad-family actions -> a dead state

X exposes source-family actions s_0...s_31;
two pre-role aliases are assigned to L and R and emit Section 3.3 outcomes;
the other 30 are syntactically legal, enter a dead source state, and
authorize no experiment family
```

Action aliases do not reveal the numeric subscripts above. Every wrong action
used by a binding swap is syntactically legal and reaches a public dead state;
no parser/legality shortcut exists.

The two B goals are ordinary alpha-renamed repeated measures, not a separate
`GOAL_TWIN` intervention:

```text
G_A={start:S,target:T_A,route_cue:q_uA,budget:3 READs}
G_B={start:S,target:T_B,route_cue:q_uB,budget:3 READs}

validity additionally requires first action route(q_goal):
G_A: a_uA,b_uA,c_0,t_A
G_B: a_uB,b_uB,c_0,t_B
```

Reaching the nominal terminal through another entrance is invalid even if a
graph path exists. This route predicate is part of the endpoint scorer's
finite truth table.

The D goal is identical across h twins:

```text
G_D={start:U_uD,target:D,route_cue:null,budget:2 READs}
valid h trace: b_uD,c_0,n_h
```

### 3.2 Grounded foundation and DREAM evidence

Before any B/C/D goal or support blueprint, the child acts through a matched
foundation block that grounds all eight `q_i -> a_i` route rows and both
`T_A -> t_A`, `T_B -> t_B` terminal rows. Every route receives equal views,
visits, and presentation strata; the future goal cues are not marked.

For each lane the child then performs exactly four committed public trials in
ablation arena `A_i`:

```text
TEST([b_i,c_0]); TEST([b_i]); TEST([c_0]); TEST(nuisance_i)
```

Each action is followed by one later public binary observation using Section
1.2's full table. The arena exposes no necessity bit, partial score, theorem,
future goal, or free-text hint. Missing child acts are adverse and never filled
by the harness.

At exact cut A2 the child receives the eight endpoint/type/count/length-
matched pair handles in a presealed order and emits:

```text
PublicPairSelection { v, exactly_two_pair_handles:[string,string] }
```

The complete actor-input byte stream is sealed before the first support-
blueprint, future-goal, compiler, expected-trace, or hidden-role byte. Fresh
support trials are then revealed only for the selected pairs. The link
compiler admits a selected pair iff new outcomes are exactly `(joint,left,
right,nuisance)=(1,0,0,0)`. It cannot propose, rank, replace, or add a pair.

The registered mechanical necessity rule uses the same public table and is a
100% ceiling conditional on the child completing that registered evidence
table. Endpoint/joint-frequency policies tie; uniform
exact-two chance is `1/C(8,2)=1/28`. Only agreement/provenance is reported.

`DREAM_DERANGED_OLD` uses the exact child pair handles but applies a presealed
fixed-point-free lane permutation: at key `U_i`, payload `[b_i,c_0]` becomes
`[b_pi(i),c_0]`. `b_pi(i)` is legal at `U_i` and reaches `F_(i,pi(i))`. Source
and all common foundation rows are identical to FULL.

### 3.3 Authentic source block and derangement

One opaque public source situation X permits child actions L/R. The child must
execute each four times; nth-within-action outcomes are fixed before action:

```text
b=0: L=[T,T,T,O], R=[T,O,O,O]
b=1: L=[T,O,O,O], R=[T,T,T,O]
```

These are empirical occurrence frequencies, not stochastic-environment
probabilities. Each outcome follows and cites its authentic committed action.
Draft, parent, harness, or reordered actions are ineligible.

`SOURCE_DERANGED_OLD` uses the presealed within-X donor permutation:

```text
L=[T,T,O,O], R=[T,T,O,O].
```

Its mapping is deterministic: sort the four authentic T event handles and
four authentic O event handles by their audit-only raw bytes; assign the T
donors in order to destination slots `[L0,L1,R0,R1]` and the O donors in order
to `[L2,L3,R2,R3]`. Every authentic outcome is used exactly once. The mapping
and raw handles stay in AuditEnvelope; training sees only the preallocated
token-isomorphic visible citations.

It preserves the realized eight actions, four L/R and four T/O marginals,
visible schema/citation counts, token-shape classes, views, visits, deck/batch
positions, masks, optimizer work, and the common realized S1 RNG/device. Only
the action--outcome binding, derived target tokens, and preallocated visible
row/citation handles in the allowed-difference projection change. Donor event
and derivation data remain audit-only. Path/DREAM rows are identical to FULL;
source rows are identical between FULL and DREAM_DERANGED.

The public source-action menu is fixed:

```text
L authorizes experiment family {E0,E1}
R authorizes experiment family {E2,E3}
```

It does not reveal which family is informative.

## 4. Exact reader, availability theorem, and side-channel machine

### 4.1 Six public query types and candidate banks

No free-text, suffix, ID, slot, reverse, wildcard, or enumeration query exists.

| query | legal phase/state | public anchor | 32 candidate payloads |
|---|---|---|---|
| `ROUTE_BY_CUE` | B at S | current goal cue | `q -> a_j`, j=0..31 |
| `ATOM_SUCCESSOR` | B at U_i | current state | `U_i -> b_j`, j=0..31 |
| `ATOM_SUCCESSOR` | B at B | current state | `B -> c_j`, j=0..31 |
| `LINK_SUCCESSOR` | B/D at U_i | current state | `U_i -> [b_j,c_0]`, j=0..31 |
| `TERMINAL_TO_TARGET` | B at C | current target | target -> `t_j`, j=0..31 |
| `SOURCE_INVERSE` | C at X | X + desired T/O | L,R plus 30 reserved source actions |
| `NEW_SUCCESSOR` | D at C | C + target D | `C -> n_j`, j=0..31 |

The roster is a Cartesian product of public types and pre-role action aliases,
not selected using truth, outcomes, theorem, child selection, or future trace.
The actor sees only the common schema digest. One READ returns at most one row.
A link row is one payload authorizing its two actions in order.

### 4.2 Ideal carrier availability

For query `q`, `A_K(q)` is the exact set of rows semantically present in ideal
carrier K:

```text
A_FULL_OLD: all grounded route/terminal rows, authentic source rows,
            and the two admitted selected links
A_SOURCE_DERANGED: same except crossed source rows
A_DREAM_DERANGED: same except the two binding-swapped link rows
A_ATOMS: route/terminal rows and separate b_i and c_0 atoms; no link rows
A_S1_OFF / GOAL_CATALOG_NO_CARRIER: empty
A_FULL_NEW_h: A_FULL_OLD union {n_h}
A_OLD_PLUS_PAD: A_FULL_OLD union {d_pad under audit-only key};
                no public NEW_SUCCESSOR row
```

Cuts subtract only their named row. Hit-matched swaps replace exactly one
available row by a named, same-envelope wrong row. The raw wrong-root
diagnostic has no matched availability claim.

### 4.3 Availability-parameterized formal READ theorem

The formal reader relation is parameterized by `A_K`:

```text
FOUND(row) is a legal formal return only if row in A_K(request);
MISS is always legal;
BLOCKED is legal only for an invalid query transition.
```

The finite state is:

```text
(phase, public goal, public state, reads remaining,
 request/return history including full row payloads,
 live citations with ordered action cursor and expiry,
 executed action prefix, route-validity bit,
 declaration/dispatch state, terminal/failure state)
```

A row citation is live only until its authorized ordered actions are consumed
or another READ occurs. An atom authorizes one action. A link authorizes
exactly `b_j` then `c_0`; either mismatch enters absorbing malformed failure.
Every READ consumes one unit whether FOUND/MISS/BLOCKED. Initial budgets are
B=3, C=1, D=2, and the atoms ceiling B=4.

An independent BFS explores every legal query, every availability-respecting
FOUND payload, MISS, BLOCKED, every cited action, repeated query, early stop,
and branch. It proves two distinct objects:

1. **Safety/lower bounds for all availability-respecting returns:** no
   atoms-only B completion in <=3; no FULL B completion in <3; no D completion
   in <2; and cut carriers cannot complete their named endpoint.
2. **Constructive upper bounds under canonical ideal return `R*_K`:** FULL
   completes A and B in exactly 3, ATOMS in exactly 4, and FULL_NEW_h completes
   D in exactly 2.

The checker publishes witness histories and shortest-path/unreachability
certificates. It never quantifies over arbitrary unavailable FOUND rows.

### 4.4 Model false-positive and positive-return gates

The theorem is not a neural-reader theorem. At model level, every registered
query and adversarial legal query is compared with `A_K`. A root fails if the
reader returns any row outside availability, including:

- a link from ATOMS;
- a row removed by LINK/OLD/NEW cut;
- a new D row from OLD_PLUS_PAD, FULL_OLD, or carrier-free cells;
- a correct row under the wrong anchor; or
- any filler/bypass row that completes an endpoint.

FULL positive rows must also be FOUND with exact bytes; false negatives fail
the root. TEXT_FULL/ATOMS supply the assay ceilings. These are inference
acceptance tests, not Stage-0 proofs and not additional trained M arms.

### 4.5 Padded-RPC observable machine

The actor-observable alphabet is exactly:

```text
EpisodeInput(bytes)
MemoryReturn(bytes, logical_tick)
PublicObservation(bytes, logical_tick)
EpisodeTerminal(bytes, logical_tick)
```

There is no actor wall/monotonic clock, file/process/cache/network access,
callback enumeration, exception channel, GPU telemetry, or scheduler state.

Every READ, including no-carrier, MISS, cuts, and swaps, executes this RPC:

```text
IDLE --request at logical tick t--> SUSPENDED
SUSPENDED --score exactly 32 candidates--> SEALED(result)
SEALED --at registered logical tick t+DELTA--> RELEASE one MemoryReturn
```

`DELTA`, physical deadline, worker image, scoring count, and padding bytes are
bound in `reader_binding.json`. The actor process is suspended and has no clock
while scoring. All sub-deadline physical delays release the same bytes at the
same logical tick. On overrun/crash, the actor never resumes; audit alone emits
`RPC_OVERRUN`, the root is adverse-filled, and no public continuation exists
on which the actor can branch.

The backend hides candidate order, scores, winner index, availability map,
threshold, retries, and physical timing. The pre-role root draw supplies base
permutation `sigma` of slot indices `0..31`. The four registered candidate
orders are exactly:

```text
P0 = sigma([0,1,...,31])
P1 = sigma([31,30,...,0])
P2 = sigma([13,14,...,31,0,1,...,12])
P3 = sigma([0,2,...,30,1,3,...,31])
```

No other order is called registered. All four must return identical FULL
semantic payloads. A fake-clock fixture injects distinct backend delays and
verifies alpha-normalized public transcripts are identical.

Actor-side noninterference is exact equality, not MI: catalog/request/hash/
counter/pad/error bytes are pure functions of allowed public history and
budget; hit-matched twins differ only in their registered row projection;
opaque alias tuples are role-independent; availability controls are explicitly
allowed to differ in FOUND/MISS.

## 5. Full Phase-C state machine and source intervention

### 5.1 C task law

The environment potential outcomes are:

```text
b=0: E0=h, E1=1-h, E2=z, E3=1-z
b=1: E2=h, E3=1-h, E0=z, E1=1-z
```

The compiler never sees b/h/z labels. From the authentic public source events
it mechanically identifies the unique 3/4 action for desired T, then maps that
action through the public L/R family menu. It enumerates possible h values
consistent with the chosen family/member and observed public y. Target-family
direct/inverse makes the posterior singleton; nuisance family leaves `{0,1}`
even when `z==h`.

### 5.2 Canonical C transitions

The complete C machine is:

```text
C0 INPUT:
  ActorEpisodeInput has X, desired outcome T, hypotheses {h0,h1},
  public L/R-to-family menu, one READ, and one dispatch.

C1 SOURCE READ:
  REQ SOURCE_INVERSE(X,T)
  RET one L/R propensity row or MISS/BLOCKED.

C2 DECLARATION:
  PublicDeclaration {
    v, cited_source_row_handle, hypotheses:[0,1],
    chosen_experiment:E0|E1|E2|E3,
    prediction_h0:0|1, prediction_h1:0|1,
    outcome0_row_handle, outcome1_row_handle
  }
  Legal maps:
    E0/E2: h0->0,h1->1, outcome0->n0,outcome1->n1
    E1/E3: h0->1,h1->0, outcome0->n1,outcome1->n0

C3 PUBLIC DISPATCH:
  DISPATCH_EXPERIMENT cites both the FOUND source row and public menu.
  It may select only a member of the family authorized by the returned L/R.
  This is `authorization=PUBLIC_DISPATCH`, the sole exception to direct
  MEMORY_ROW action authorization.

C4 TWIN FORK:
  After the declaration and dispatch bytes are committed, clone the actor
  process/RNG snapshot. h0 and h1 histories, process inputs, and RNG state are
  byte-identical through the committed experiment action.

C5 OUTCOME:
  Environment emits the causally later public y in each h world.

C6 COMPILER:
  CompilerInput contains authentic public source events, declaration,
  dispatch, public outcome, and public task-law digest. It checks declaration
  syntax/map, reconstructs target family from the 3/4 source evidence,
  computes posterior by enumerating h={0,1}, and admits the declared row iff
  posterior is singleton and every citation/action/outcome is authentic.

C7 RESULT:
  ADMIT exactly n_h or NO_ADMISSION. No repair/substitution is possible.
```

All 32 `(b,h,z,E)` cases are materialized, capability-tested, and independently
checked. `DECLARATION_FAITHFUL` and `WORLD_TRUE` are separate bits. Nuisance
experiments always yield `NO_ADMISSION`.

### 5.3 Common decode and exact twin prefix

Actor/child decode configuration is frozen. Random draws are keyed by
`(protocol,root,phase,episode_role,token_ordinal)` and exclude condition/build
and h. Compared inference cells receive common draws. C twins are literal
clones of one process and RNG snapshot at C4, not separately seeded calls.
They reuse the same actor-visible episode, goal, state, action, row, citation,
and menu handles; h exists only in the private environment branch and
AuditEnvelope.

The package hashes every actor process input, output token, reader return,
declaration, and dispatch event through C4. It binds `o_C_outcome`, the first
different byte, inside C5's public observation. Any earlier h-dependent byte
is a global structural failure.

### 5.4 `SOURCE_READ_SWAP_C`

This destroyed no-write inference fork mounts FULL_OLD but replaces the live
C1 FOUND source row with the opposite L/R row. The swap is presealed and
hit/status/query-count/serialized-length/token-length/citation/action-class-
matched. It changes only the visible row handle and semantic L/R payload under
the allowed projection.

The child must cite the swapped row, declare/dispatch within the opposite
nuisance family, receive the ordinary public outcome, and the compiler must
return `NO_ADMISSION` for every h/z case. Ignoring the returned row, selecting
the original target family, or admitting a row fails `R_r`. This directly
crosses source read -> live action -> outcome -> admission without another fit.

## 6. Exact training nuisance and writer decks

### 6.1 Qualified writer inheritance

M uses exactly `W*` from the prerequisite binding. It adds no view,
paraphrase, replay, mask, rank, learning rate, dose, preservation, threshold,
or reader choice. Every build reconstructs from the same immutable birth
checkpoint. If `W*` cannot render the source inverse, link, atomic, terminal,
and outcome rows required here under its qualified format, M is not ready; M
does not invent a representation repair.

### 6.2 Common realized S1 and S2 optimization nuisance

Training randomness excludes condition/build identity:

```text
TRAIN_RNG(root,stage,stream,step_or_slot) =
  H("train-rng",protocol_sha256,root_handle,stage,stream,step_or_slot)
```

All three S1 members use the same initialization bytes, ordered deck slots,
batch membership/order, padding, dropout draws, data-worker seeds,
deterministic-kernel settings, optimizer-state initialization, step schedule,
physical device, driver/runtime/software image, and health envelope. All three
S2 members separately share the same realized S2 values. Artifact IDs may
contain build identity; optimization RNG may not.

Each matched triplet runs as three sterile processes sequentially on its one
assigned physical device. Condition order is an iid root-level permutation.
No process/model/optimizer/cache state crosses members. Device health,
temperature class, clocks, image digest, deterministic-kernel status, and
reset are receipted; a departure invalidates the triplet rather than becoming
root-local scientific noise.

Pairwise S1/S2 receipts materialize and compare initialization hash, every
deck slot, input/label/mask tensor, batch index, dropout/RNG counter, optimizer
step, and device/image digest. Common-nuisance fields must be bit-identical;
only the registered semantic token projection may differ.

### 6.3 S1 decks

Every S1 deck contains identical grounded route/terminal foundation rows.

| build | source | selected links | treatment |
|---|---|---|---|
| FULL_OLD | authentic 3:1/1:3 | authentic supported | positive |
| SOURCE_DERANGED_OLD | crossed 2:2/2:2 | identical authentic | source binding only |
| DREAM_DERANGED_OLD | identical authentic | fixed-point-free matched payloads | link binding only |

For each paired row, the package emits the tensor/allowed-difference receipt
defined below. Visible citation handles are pre-role opaque aliases; donor and
derivation maps are audit-only. Source/DREAM orthogonal rows must be byte-
identical, not merely equal in count.

### 6.4 Exact S2 PAD projection and work receipt

At A0 the root seals a disconnected authentic child event `P --p_0--> Q`.
Its truthful row `d_pad` is withheld from compilation until the S2 control.
It uses the same public row `query_type` as an outcome row but the disconnected
key `[P,Q]`. Neither P nor Q is a public B/C/D anchor. PAD extraction occurs
only through the audit interface.

The canonical memory-row semantic projection is:

```text
SEMANTIC_PAYLOAD_FIELDS = {
  row_handle,
  key_handles[*],
  ordered_action_handles[*],
  destination_handles[*],
  visible_citation_handles[*]
}
```

Raw n0, n1, and d_pad identities remain distinct. The alias pool makes every
corresponding projected field token-isomorphic. For every rendered training
example, construct a bit vector `allowed_diff` of length `L` with 1 exactly at
token positions occupied by these fields and 0 elsewhere. Publish both raw
diffs and diffs after registered role-blind alpha-normalization.

For `FULL_NEW_h0`, `FULL_NEW_h1`, and `FULL_OLD_PLUS_PAD`, materialize:

```text
input_ids[L]
attention_mask[L]
position_ids[L]
labels[L]
loss_mask[L]
allowed_diff[L]
view_id, visit_id, deck_slot, batch_index, optimizer_step,
dropout_stream_indices, renderer_sha256
```

Required equalities are:

- identical shapes and L;
- `input_ids`/`labels` may differ only where `allowed_diff=1`;
- `attention_mask`, `position_ids`, `loss_mask`, supervised-token count,
  view/visit IDs, deck slot, batch index, optimizer step, render count,
  batch shape, and dropout-stream indices are bit-identical;
- alpha-normalized input/label tensors are bit-identical everywhere;
- every projected alias/citation position is declared in the bitmap; and
- forward/backward calls, supervised tokens, optimizer updates, and total
  token work are identical across the S2 triplet.

The same tensor/bitmap/work receipt is required for every differing S1 paired
row. An undeclared difference, missing projected position, or work mismatch is
a structural failure before fitting. PAD is gradient-bearing and truthful,
not masked filler or repeated old material.

The audit PAD extractor invokes the same bound reader scorer, 32-candidate
count, token renderer, and fixed-release RPC envelope as a new-row validation,
but through its private audit key. Its request/return never enters an actor
process. The receipt proves equal scorer-call shape without inventing a public
query.

All S2 builds reconstruct from birth with the exact FULL old deck plus one
reserved-slot row:

```text
FULL_NEW_h0       + n0 from authentic h0 C admission
FULL_NEW_h1       + n1 from authentic h1 C admission
FULL_OLD_PLUS_PAD + d_pad from authentic disconnected P outcome
```

## 7. Exact traces and named inference controls

### 7.1 Constructive traces and byte cuts

FULL B-A:

```text
READ ROUTE_BY_CUE(q_A) -> q_A:a_uA; ACT a_uA -> U_uA
READ LINK_SUCCESSOR(U_uA) -> [b_uA,c_0]; ACT both -> C
READ TERMINAL_TO_TARGET(T_A) -> t_A; ACT -> T_A
```

FULL B-B substitutes the registered q_B/u_B/T_B aliases and reaches T_B.
The first A/B difference is in the complete `ActorEpisodeInput.goal` byte
stream, not request 1. Under JCS and fixed-length preceding fields, Stage 0
binds zero-based `o_goal` and proves complete prefix equality before it.

FULL D h0/h1:

```text
READ LINK_SUCCESSOR(U_uD) -> [b_uD,c_0]; ACT both -> C
READ NEW_SUCCESSOR(C,D) -> n_h; ACT n_h -> D
```

Every process input, request, return, and action byte is identical across h
through request 2. Stage 0 binds `o_D_outcome` at the first differing byte in
return 2's row payload and proves prefix equality. Raw C outcome/history and h
are absent after reset.

ATOMS uses route, `b_u`, `c_0`, terminal in exactly four B reads.

### 7.2 Named controls

These are inference-only unless the six trained builds table says otherwise:

| ID | exact intervention | required result |
|---|---|---|
| `S1_OFF_B` | no carrier; same B public input/RPC | dependent B trace fails |
| `S1_OFF_C` | no carrier; same C public input/RPC | dependent C trace fails |
| `GOAL_CATALOG_NO_CARRIER` | full goal+catalog/API, no carrier | B/D fails |
| `CATALOG_ONLY_NO_GOAL` | goal-neutral input+catalog, no carrier | target trace fails |
| `CATALOG_PERMUTE_P0..P3` | one of four registered backend orders | FULL semantic return/action invariant |
| `B_LINK_CUT` | suppress selected B link to charged MISS | B fails |
| `B_LINK_PAYLOAD_SWAP` | FULL hit -> `[b_pi(u),c_0]` | legal wrong action, semantic B failure |
| `SOURCE_READ_SWAP_C` | FULL source hit -> opposite L/R row | nuisance dispatch and NO_ADMISSION |
| `D_OLD_LINK_CUT` | suppress old D link to charged MISS | D fails |
| `D_NEW_ROW_CUT` | suppress new D row to charged MISS | D fails |
| `D_OLD_LINK_PAYLOAD_SWAP` | old hit -> `[b_pi(uD),c_0]` | legal wrong first action, D fails |
| `D_NEW_ROW_PAYLOAD_SWAP` | new hit `n_h` -> hit-matched `n_(1-h)` | legal wrong final action, D fails |
| `NO_SLEEP2` | FULL_OLD at D | diagnostic D failure; not equal-work |
| `OLD_PLUS_PAD` | trained matched baseline at D | NEW query unavailable; both h fail |
| `TEXT_FULL` | exact FULL rows behind identical reader/API | all constructive endpoints pass |
| `TEXT_ATOMS_READ4` | exact atoms, B budget 4 | both B goals pass in exactly 4 |

For a branch-specific control, append `[h0]` or `[h1]` to its table ID; these
are repeated-measure instances, not new conditions or roots. The ordinary A/B
goal pair replaces the undefined `GOAL_TWIN` label; its
required route/query/action redirection is part of R. D old and new swaps are
separate, so failure of one cannot stand in for the other.

`RAW_WRONG_ROOT` is demoted to an explicitly unmatched descriptive
specificity diagnostic. Raw donor aliases may MISS and a donor may coincide in
semantic role. It is excluded from `F_r`, `R_r`, and all causal/reliability
claims; no failure is required. Carrier origin is established by immutable
event->row->target->adapter->raw-return receipts and the hit-matched swaps.

Availability cuts may expose FOUND/MISS and support necessity only.
SOURCE/DREAM/PAD and named payload swaps are the matched content/equal-work
comparisons and therefore carry the content claims.

## 8. Schedule, chronology, and clean resets

### 8.1 Instantiated iid schedule in expectation

`schedule_tables.json` contains:

```text
eligible_devices = sorted list of (device_uuid,image_sha256,driver,runtime)
S1_conditions = [FULL_OLD,SOURCE_DERANGED_OLD,DREAM_DERANGED_OLD]
S2_conditions = [FULL_NEW_h0,FULL_NEW_h1,FULL_OLD_PLUS_PAD]
S1_orders = all 6 lexicographic permutations
S2_orders = all 6 lexicographic permutations
B_control_order = fixed ID list from Section 7, Fisher-Yates per root
C_control_order = fixed ID list from Section 7, Fisher-Yates per root
D_control_order = fixed ID list from Section 7, Fisher-Yates per root
catalog_orders = P0..P3
```

Each complete root independently and uniformly draws one eligible device for
the whole S1 triplet, one for the whole S2 triplet, one S1/S2 order, and each
control order. Conditions within a matched triplet share the physical device;
there is no claim of exact condition/device balance within one root. Across
iid roots, positions/devices are balanced **in expectation**, and realized
counts are reported. S2 skip leaves its presealed draws unused and never
reassigns them.

The confirmatory target probability is over the complete iid root object,
including aliases, common random streams, and schedule draws. A shared device,
image, filesystem, scheduler, or service departure affecting multiple roots
is a global instrument invalidation, not correlated root-local noise.

### 8.2 Chronology

```text
A0 seal package/root/h twins/orders/future objects and PAD control event
A1 child performs grounded foundation, source, ablation and P/PAD actions;
   authentic public outcomes append immutable events
A2 seal child exact pair selection before support/future visibility
A3 reveal support trials; compiler admits only selected supported links
S1 run common-RNG/common-device matched triplet from birth
B  sterile A/B actors; all B controls
C-p four destroyed source-label probes; no writes
C  FULL authentic twin and SOURCE_READ_SWAP_C destroyed forks
S2 run common-RNG/common-device matched triplet from birth
D  sterile h-twin actors; all named D controls
```

Sterile reset destroys raw events, child/DREAM/C text, outcome bytes, context,
KV/cache, process, filesystem/workspace, and prior query state. Only the bound
carrier may enter the reader process; LoRA is mounted only inside recognition
scoring, never actor planning/action.

## 9. Scoring, root estimands, and noncompensatory R

### 9.1 Exact public-trace scoring

The endpoint scorer validates only canonical public events plus the isolated
environment handle. An action is valid when either:

- `MEMORY_ROW`: the immediately live FOUND row authorizes that action at its
  current cursor; or
- `PUBLIC_DISPATCH`: in Phase C only, a FOUND source row plus the public menu
  authorizes the selected experiment family/member.

Wrong goal-route entrance, malformed object, permissive parse, extra/uncited/
expired/out-of-order action, wrong state, budget overrun, semantic repair, or
wrong terminal scores 0.

Define:

```text
Y_B(r,K,g) binary valid B trace, g in {A,B}
Y_C(r,K,j) binary authentic counterfactual source label, j=1..4
Y_D(r,K,h) binary valid D trace, h in {0,1}
```

The four C label probes are:

```text
j1 desired T, L/R display canonical, families canonical
j2 desired O, L/R display canonical, families canonical
j3 desired T, L/R display reversed, families registered rotation
j4 desired O, L/R display reversed, same rotation
```

Authentic scoring labels never change for SOURCE_DERANGED:

```text
b0: T->L, O->R
b1: T->R, O->L
```

One root supplies one four-probe mean.

### 9.2 Root scalars

Missing, skipped, timeout, malformed, and failed cells receive endpoint zero.

```text
S_r = mean_j Y_C(FULL_OLD,j) - mean_j Y_C(SOURCE_DERANGED_OLD,j)

M_r = min_g [Y_B(FULL_OLD,g) - Y_B(DREAM_DERANGED_OLD,g)]

U_r = min(
        min_g[Y_B(FULL_OLD,g)-Y_B(S1_OFF_B,g)],
        mean_j Y_C(FULL_OLD,j)-mean_j Y_C(S1_OFF_C,j)
      )

W_r = min_h [Y_D(FULL_NEW_h,h)-Y_D(FULL_OLD_PLUS_PAD,h)]

F_r = min_h min(
        Y_D(FULL_NEW_h,h)-Y_D(D_OLD_LINK_CUT_h,h),
        Y_D(FULL_NEW_h,h)-Y_D(D_NEW_ROW_CUT_h,h),
        Y_D(FULL_NEW_h,h)-Y_D(D_OLD_LINK_PAYLOAD_SWAP_h,h),
        Y_D(FULL_NEW_h,h)-Y_D(D_NEW_ROW_PAYLOAD_SWAP_h,h)
      )
```

### 9.3 Root reliability conjunction

`R_r=1` only if every item passes on that same presealed root:

1. generator/materializer/independent-checker, schemas/ACL, immutable-handle,
   graph, tensor/work, RNG/device, RPC, reset, and formal READ receipts pass;
2. every admitted source/ablation/support/PAD row follows the child's committed
   action and causally later public outcome;
3. the pair selection seal precedes support/future bytes, equals the two
   evidence-indicated lanes, and fresh support admits exactly those links;
4. all three S1 carriers extract their intended rows, preserve orthogonal rows,
   pass interface/non-harm/canary gates, and produce no unavailable-row false
   positive under every registered/adversarial legal query;
5. FULL solves both ordinary B goals in three exact reads; TEXT_ATOMS does so
   in four; the A/B episode input, first-byte offset, route/query/action
   redirection, and goal-validity predicate all pass;
6. S1_OFF, GOAL_CATALOG_NO_CARRIER, CATALOG_ONLY_NO_GOAL, B_LINK_CUT fail;
   every P0..P3 catalog order preserves FULL; B_LINK_PAYLOAD_SWAP redirects to
   the named legal wrong action and fails semantically without interface harm;
7. DREAM_DERANGED fails both link-dependent B traces but preserves source C;
   SOURCE_DERANGED preserves both B traces; `M_r>0`;
8. FULL source score is 1.0; T/O reverses semantic source action/family;
   SOURCE_DERANGED uses the frozen authentic labels and is at least .25 lower;
   DREAM_DERANGED preserves source; `S_r>0` and `U_r>0`;
9. the full C twin prefix is byte-identical through dispatch; authentic FULL
   selects a target family and admits exactly n_h for both h; all nuisance
   cases reject; SOURCE_READ_SWAP_C redirects to the nuisance family and
   yields NO_ADMISSION for every h/z;
10. all three S2 carriers share realized RNG/device/work; FULL_NEW_h extracts
    only n_h while retaining every registered old row and B behavior;
    OLD_PLUS_PAD extracts d_pad only through audit, retains old rows, and has
    no public D new row;
11. both FULL_NEW h traces reach D in two reads with different final actions;
    OLD_PLUS_PAD, NO_SLEEP2, both D cuts, and both separately named D payload
    swaps fail; `W_r>0` and `F_r>0`;
12. TEXT_FULL passes; every positive return has immutable carrier origin; raw
    experience/DREAM/C bytes do not cross reset; all side-channel fake-clock,
    overrun, forbidden-field, and false-positive gates pass.

Later success cannot rescue any item. A cross-root/shared-service structural
failure invalidates the instrument. A demonstrably root-local child, action,
fit, or process failure is adverse-filled and stays in every denominator.
RAW_WRONG_ROOT is never part of R.

## 10. Stages, statistics, and measured cost

### 10.1 Frozen manifests and stopping

`TEXT=[T1..T8]`, `DEV=[D1..D8]`, and `CONF=[C1..C16]` are source-disjoint and
presealed. TEXT is descriptive and never becomes DEV. DEV is one nested
prefix: two-root kill D1/D2, then D3..D8. Confirmation is fresh.

```text
Stage 0: deterministic package/materializer/checker/RPC/graph/tensor closure;
         zero fits; any failure stops
Stage 1: TEXT T1..T4; require 4/4 or, if 2/4 or 3/4, extend to T5..T8 and
         require >=6/8; <2/4 stops
Stage 2a: D1,D2 S1 triplets only = 6 fits; both roots pass all S1 gates
Stage 2b: only then D1,D2 S2 triplets = 6 more; both roots pass all S2 gates
Stage 3: D3..D8, S1 first and S2 only for upstream survivors; require >=6/8 R
Stage 4: all C1..C16, no replacement/extension/early-success/rerun
```

Skipped S2 after frozen futility remains an adverse root zero. DEV mechanics
freeze before confirmation.

### 10.2 Exact tests and multiplicity

For confirmation compute S/M/U/W/F/R once per root. Ordered co-primary nulls:

```text
H_S: Pr(S_r>0)<=.5
H_M: Pr(M_r>0)<=.5
H_U: Pr(U_r>0)<=.5
H_W: Pr(W_r>0)<=.5
H_R: Pr(R_r=1)<=.5
```

Test in fixed order `S -> M -> U -> W -> R`, exact one-sided binomial at
alpha .05; stop confirmatory rejection at first non-rejection. This fixed
sequence controls FWER at .05. F and named controls are mandatory within R
and reported descriptively. With n=16, each component needs >=12 positive
roots because:

```text
P[Binomial(16,.5)>=12]=2517/65536=.0384063720703125.
```

Zero/missing/skipped/failure is non-success. Treatment labels are not
randomized, so no sign-flip/randomization test is claimed. Report exact p,
all 16 magnitudes/failures, and componentwise one-sided 95% Clopper--Pearson
lower endpoint `Beta^-1(.05;K,17-K)` (0 if K=0); at K=12 it is approximately
.5156035789. Post-stop p-values are descriptive. `12/16 R` does not replace
the four causal components.

This inference targets the complete iid root generator, including independent
schedule draws. Realized device/order counts are reported; exact balance is
not asserted. Child exact-pair counts are descriptive against conditional
mechanical 100% and chance 1/28 only.

### 10.3 Fit counts and measured-only cost

```text
S1/root=3; S2/upstream-survivor=3; complete root<=6
two-root S1 kill=6; two-root full kill=12
eight-root DEV maximum=48
sixteen-root confirmation maximum=96
DEV+confirmation M-fit maximum=144
```

These counts exclude W*/reader qualification and TEXT. Actual training device
cost is only:

```text
C_train_actual = sum over completed fits f measured_device_seconds(f).
```

Report it from immutable job receipts stratified by exact deck class, physical
device UUID, and software image. A prospective bound is permitted only after
every registered deck/device class has a measured bound, and is the sum of
class-specific bound times maximum class count. Action, inference, reset,
validation, serialization, queueing, and process startup are separately
measured. No generic `N_fit*t_fit`, GPU-hour range, ideal packing, or wall-time
promise is valid.

## 11. Fatal shortcuts and v3-audit disposition

Any of these is fatal globally unless proven isolated to one root, in which
case that root is adverse-filled:

1. unbound package/W*/reader/schema/generator/checker or non-reproducible bytes;
2. role/root/alias/order/device/seed regenerated after child behavior;
3. fitted contrast members differ in realized RNG, device/image, deck/batch
   schedule, masks, or work outside the allowed semantic projection;
4. actor/recognition scorer/compiler receives forbidden graph/truth/audit bytes;
5. adjacency/slot/alias/future-goal/blueprint/expected trace leaks before its
   registered cut;
6. unavailable FOUND/bypass row, undeclared query, unmodelled action, or failed
   formal shortest-path/cut certificate;
7. actor clock/network/cache/process/timing/exception channel or unpadded RPC;
8. source/ablation/support/PAD event lacks authentic child action then outcome;
9. compiler proposes/repairs/replaces content or admits non-singleton nuisance;
10. SOURCE_READ_SWAP_C does not redirect live family and block admission;
11. PAD is ungrounded/masked/queryable publicly, or bitmap/tensor/work differs
    outside declared payload positions;
12. audit provenance/condition/derivation handle enters gradient/scorer/public
    bytes except through declared token-isomorphic visible payload positions;
13. combined/ambiguous D swap substitutes for separate old/new swaps;
14. RAW_WRONG_ROOT is promoted into a matched or causal claim;
15. raw context/event/outcome/cache/workspace crosses reset or LoRA is mounted
    outside recognition READ;
16. M changes W*, rank, dose, mask, renderer, reader, threshold, or any knob on
    M results;
17. failed root is retried/replaced/dropped/permissively reparsed, or repeated
    measures are counted as roots; or
18. clean-base reconstruction is described as in-place/online learning, or
    the narrow M result is promoted to DREAM intelligence/general recurrence.

This v4 closes the two v3 audits without another trained condition:

- S1/S2 triplets share common realized RNG and one physical device/image;
- the formal READ theorem is availability-parameterized and neural false
  positives are separate model gates;
- exact ActorEpisodeInput/public trace/scorer/compiler/audit schemas and ACLs
  separate every capability;
- the full C declaration/dispatch/twin/outcome/posterior/admission machine and
  SOURCE_READ_SWAP_C are explicit;
- RAW_WRONG_ROOT is honestly demoted and removed from F/R;
- PAD uses an exact semantic projection, allowed-difference bitmap, full
  tensor/batch/RNG/work receipts, distinct raw identities, and audit extraction;
- the deterministic SHA-256 generator, draw order, materializer interface,
  independent checker, action/candidate rosters, and manifest prerequisites
  are concrete;
- the padded-RPC observable transducer defines clock, release, and overrun;
- schedule tables use iid per-root device/order draws and claim balance only
  in expectation;
- GOAL_TWIN is replaced by the ordinary A/B pair; B/D swaps and D cuts have
  exact separate IDs;
- actual cost is the measured sum over completed fits; and
- the unsupported global-minimality statement is removed.

No TEXT, reader-model acceptance, or M fit is ready until the package,
materializer, independent checker, W*/reader bindings, Stage-0 closure, and
exact-text feasibility exist and pass.

## Source lineage

- `research_notes/analysis/2026-09-12_m_core_v3_causal_graph_mechanism_audit.md`;
- `research_notes/analysis/2026-09-12_m_core_v3_fresh_statistics_visibility_execution_audit.md`;
- `research_notes/analysis/2026-09-12_m_core_minimal_exact_two_cycle_design_v3.md`;
- `research_notes/analysis/2026-09-12_m_core_v2_statistics_visibility_audit.md`;
- `research_notes/analysis/2026-09-12_m_core_v2_fresh_adversarial_audit.md`.
