# M-core v5: closed crossed two-cycle relay contract

Date: 2026-09-12 UTC

Status: **superseded by**
`2026-09-12_m_core_exact_two_cycle_design_v6.md`. This v5 note is retained as
design history only and must not authorize materialization, Stage 0, TEXT,
reader-model work, or an M fit. It changes no builder source, benchmark,
child, model, tokenizer, adapter, checkpoint, job, GPU state, resource,
coordination record, scientific claim, release, or submission.

## 0. Claim, allocation, and the source-control ruling

The design retains at most six trained carriers per complete root:

```text
S1 matched triplet
  FULL_OLD
  SOURCE_DERANGED_OLD
  DREAM_DERANGED_OLD

S2 matched triplet, only after the frozen S1 gate
  FULL_NEW_h0
  FULL_NEW_h1
  FULL_OLD_PLUS_PAD
```

No additional trained condition is introduced. The releasable claim remains:

> In a finite typed benchmark, a qualified writer carried records compiled
> from a crossed contingency in a child's authentic public actions and
> outcomes and from a child-selected pre-blueprint pair set identified by a
> registered public ablation signal. A reset clean actor used typed reads to
> complete two goal-conditioned old-memory traces. After an authentic public
> outcome, a second clean-base cumulative write preserved the required old
> link and added the outcome-specific new row needed for a delayed action.

Permitted terms are compiler-mediated crossed experiential binding,
child-selected evidence-indicated pair set, typed functional traversal, and
two-cycle clean-base cumulative reconstruction. This does not identify DREAM
intelligence, native learned search, online/in-place growth, general
retention, recurrence, or a whole-organism effect.

### Source-control ruling

A `2/4` versus `2/4` source block cannot truthfully support one privileged L
or R target. V4 left that target implicit. V5 removes it.

Both source conditions compile one **complete empirical choice row** per
desired outcome. A row contains both action handles and their observed counts:

```text
FULL, b=0, desired T: [(L,3,4),(R,1,4)]
FULL, b=0, desired O: [(L,1,4),(R,3,4)]
FULL, b=1:              reverse L/R entries

SOURCE_DERANGED, desired T or O: [(L,2,4),(R,2,4)]
```

The deranged row is a truthful hit-matched tie, not an abstention/MISS and not
an arbitrarily labelled action. The actor reads the table and commits a source
choice. Source scoring remains against the authentic counterfactual label.
The comparison asks whether informative crossed evidence changes action, not
whether a privileged compiler target can be memorized. `SOURCE_READ_SWAP_C`
now swaps the FULL count-to-action binding, making the opposite action the
unique empirical maximum while preserving hit/schema/length/work.

## 1. Immutable package, actual schemas, and failure law

### 1.1 Manifest and Merkle closure

The immutable package contains:

```text
package_manifest.json
protocol.json
schema_catalog.json
semantic_constraints.json
root_entropy_transcript.json
root_generator.json
alias_pool.json
action_rosters.json
candidate_rosters.json
availability_relations.json
transition_system.json
interface_canary.json
nonharm_panel.json
rpc_machine.json
control_registry.json
failure_scope_table.json
order_tables.json
schedule_tables.json
allowed_difference_maps.json
goal_pair_byte_cut.json
canonical_returns.json
wstar_binding.json
reader_binding.json
actor_binding.json
manifests/{TEXT,DEV,CONF}.json
materializer source tree
independent checker source file
dependency lock
sterile CPU runtime/image manifest
canonical fixtures and expected digests
```

`package_manifest.json` lists every other immutable member with normalized
relative path, byte length, media type, and lowercase SHA-256. Unlisted files
are forbidden. Paths are NFC UTF-8 POSIX-relative paths: no leading slash,
backslash, empty component, `.`/`..` component, duplicate normalized path, or
symlink is legal. Entries are sorted by raw UTF-8 path bytes. For those sorted
entries define:

```text
leaf_i = SHA256(ASCII("MCORE-V5-LEAF\0") ||
                U32BE(path_len) || path_bytes ||
                U64BE(file_len) || file_sha256_bytes)
```

The Merkle tree pairs adjacent leaves as
`SHA256("MCORE-V5-NODE\0" || left || right)`; an odd final node is duplicated.
The manifest stores that Merkle root. The package address is SHA-256 of the
exact RFC-8785/JCS manifest bytes plus one LF. The manifest does not list
itself, avoiding a cycle. `protocol.json` is an ordinary listed member and
does not claim its own hash authenticates the tree.

Materializer, checker, lock, and runtime bytes are members. Both executables
reject a missing, extra, length-mismatched, hash-mismatched, or wrong-Merkle
member before doing work. Generated receipts live in a separate result bundle
whose own manifest binds `package_manifest_sha256`, applies the same
path/member/Merkle algorithm to every result member except itself, and is
addressed by SHA-256 of its exact JCS bytes plus LF. No receipt is appended to
the immutable package.

### 1.2 Canonical encoding

All stored JSON is RFC 8785/JCS UTF-8 followed by exactly one LF. Embedded
bytes use unpadded RFC-4648 base64url in a `BlobRef` that also carries raw byte
length and lowercase SHA-256. Integers are nonnegative and at most `2^53-1`.
Floats never occur in public/compiler objects; model scores use 16-character
IEEE-754 binary64 hexadecimal bytes. Handles are 26 lowercase RFC-4648 base32
characters matching `^[a-z2-7]{26}$`. Digests match `^[0-9a-f]{64}$`.

Section 12 contains the normative actual JSON-Schema catalog. Every object has
`additionalProperties:false`; every array cardinality, enum, nullability, and
referenced type is closed. The package's `schema_catalog.json` must be the
exact canonical extraction of that appendix and is itself manifest-bound.

### 1.3 Presealed failure taxonomy

Every executable termination uses exactly one `FailureCode` enumerated in
Section 12. `failure_scope_table.json` maps each code to the following one
scope before data; an executable may not supply or override a scope:

**GLOBAL_INVALID / no scientific test:** `GLOBAL_PACKAGE_MEMBER`,
`GLOBAL_MERKLE`, `GLOBAL_SCHEMA`, `GLOBAL_CHECKER`, `GLOBAL_CAPABILITY`,
`GLOBAL_SHARED_STATE`, `GLOBAL_BINDING`, `GLOBAL_PROTOCOL_MUTATION`,
`GLOBAL_ENTROPY`, `GLOBAL_COMMON_NUISANCE`, or `GLOBAL_UNKNOWN`.
A global failure invalidates the cohort. It cannot be reclassified after
outcomes; a repair is a new protocol and new manifests.

**ROOT_INVALID / indicator zero:** `ROOT_CHILD_OMISSION`,
`ROOT_MALFORMED_ACTION`, `ROOT_FIT_CRASH`, `ROOT_FIT_TIMEOUT`,
`ROOT_RPC_OVERRUN`, `ROOT_UNAVAILABLE_FOUND`,
`ROOT_INTERVENTION_MISMATCH`, `ROOT_LOCAL_DEVICE`,
`ROOT_EXTRACTION_FAILURE`, `ROOT_WORK_MISMATCH`, `ROOT_INTERFACE_FAILURE`,
`ROOT_CANARY_FAILURE`, or `ROOT_NONHARM_FAILURE`. The root remains in every
denominator and is never retried/replaced.

**VALID_ENDPOINT_FAILURE:** `VALID_WRONG_ROUTE`, `VALID_WRONG_ACTION`,
`VALID_WRONG_TERMINAL`, `VALID_BUDGET_EXHAUSTED`, `VALID_READ_MISS`,
`VALID_CUT_ENDPOINT`, `VALID_SWAP_ENDPOINT`, or
`VALID_INCOMPLETE_ENDPOINT`; every constituent process and intervention
completed with exact expected carrier rows/envelopes, but the actor did not
reach the endpoint. This is the only kind of control failure allowed to
contribute the intended zero in a causal contrast. `NONE` maps to `NONE`.

All structural checks and any GLOBAL/ROOT code are emitted before endpoint
bytes are opened. Only when none fired does the endpoint scorer open the trace
endpoint and mechanically emit either `NONE` for success or the one applicable
`VALID_*` code. Unregistered/ambiguous failures default to GLOBAL_INVALID.

## 2. Independent root entropy and complete generator

### 2.1 Independent-root sampling assumption

There is no single master seed. Before any child/model/outcome work, a
registered entropy tool makes one separate 32-byte OS-CSPRNG call per
prospective root and records call ordinal, raw seed commitment, host/runtime
digest, and success code in `root_entropy_transcript.json`. TEXT has 8, DEV 8,
and CONF 16 seeds. Its exact bytes and entropy-tool digest are package-bound
before any root is materialized.

The confirmatory probability law explicitly assumes these recorded root seeds
are independent uniform 256-bit samples and all root-local streams are pure
functions of only their own seed. The checker verifies the transcript and
absence of cross-root inputs; it does not claim that hashing proves physical
entropy independence. If this sampling assumption is unacceptable, the exact
binomial claim is withdrawn before running.

### 2.2 Typed hash codec

Every hash part is encoded as one of:

```text
BYTES: U8(0x01)||U64BE(n)||raw
UTF8:  U8(0x02)||U64BE(n)||utf8
U64:   U8(0x03)||U64BE(value)
U32:   U8(0x04)||U32BE(value)
SHA:   U8(0x05)||32 raw digest bytes
HANDLE:U8(0x06)||U32BE(26)||26 ASCII bytes
```

Then:

```text
H(tag, typed_parts...) = SHA256(
  ASCII("MCORE-V5\0") || U32BE(len(UTF8(tag))) || UTF8(tag) ||
  concat(encoded_typed_part))

R(root_seed,domain,counter) =
  U256BE(H("rand",BYTES(root_seed),UTF8(domain),U64(counter)))
```

`draw(domain,n)` obtains `x` from `R`, rejects
`x >= floor(2^256/n)*n`, and returns `x mod n`; each literal domain has an
independent counter initialized to zero. Fisher--Yates consumes
descending-index draws.
No call may pass an untyped string, integer, path, condition, or object.

### 2.3 Alias pool, collisions, and fixed root indexing

`alias_pool.json` enumerates canonical candidate bytes in lexicographic byte
order for each public handle/action class. W*/actor tokenization is stored for
every alias. Qualification requires fixed byte length within a class, equal
token count/position class for every role-swapped group, no reserved prompt
word, and no collision across the entire package. The pool is qualified before
root seeds are mapped to semantic roles.

Root index is transcript ordinal. There is no accepted-root filtering or root
rejection. A tokenizer/shape/collision failure is GLOBAL_INVALID, not a
request for another seed. All visible aliases are allocated by root-local
Fisher--Yates from the qualified pool before role assignment.

### 2.4 Exact root draw order

For root seed `rho_r`, consume these named domains in order:

1. allocate class-local alias permutations;
2. draw `b=draw("b",2)`, `z=draw("z",2)`;
3. draw `draw("lane-pair",28)` from the lexicographically enumerated 28
   unordered lane pairs;
4. draw A/B assignment bit for the pair;
5. set `u_D=selected_pair[draw("u-D",2)]`;
6. shuffle the six remaining lanes; first three left-decoys, last three
   right-decoys;
7. draw `dream_shift` uniformly from 1..7 and set
   `pi(i)=(i+dream_shift) mod 8`;
8. draw the 32-slot base permutation `sigma` by Fisher--Yates;
9. independently shuffle every named event/presentation stratum;
10. draw S1 and S2 device indices from their manifest rosters;
11. draw independent S1 and S2 triplet permutation indexes in 0..5;
12. draw `candidate_rotation=draw("candidate-rotation",4)`; within each
    four-probe block use `P_(candidate_rotation+j mod 4)` for probe j=0..3;
13. Fisher--Yates each complete B, C, and D control-ID roster under the
    separate domains `order-B`, `order-C`, and `order-D`.

`k=first128(H("root-nonce",BYTES(rho_r)))`. Both h branches are materialized
potential outcomes inside the root. No other draw exists. The CLI has no free
seed flag; it accepts only the manifest-bound entropy transcript and rejects a
digest mismatch.

### 2.5 Concrete materializer/checker

The required future interfaces are:

```text
python -m organism_v6.m_core_v5.materialize \
  --package-manifest <package_manifest.json> \
  --cohort TEXT|DEV|CONF --out <empty-directory>

python research_loop/checks/check_m_core_v5.py \
  --package-manifest <package_manifest.json> \
  --bundle <materialized-directory> --out <checker_receipt.json>
```

The independent checker cannot import materializer/generator modules. It
recomputes the Merkle tree, entropy mapping, typed draws, aliases, all state
transitions, availability tables, canonical bytes/offsets, compilers,
controls, tensor/work bitmaps, schedules, and expected digests. A second run
must reproduce every byte. `CheckerReceipt` is closed by Section 12 and lists
every subcheck/failure code.

## 3. Capabilities, provenance, and compilers

### 3.1 Five isolated capabilities

| bytes/object | child/actor | recognition scorer | compiler | endpoint scorer | audit |
|---|---:|---:|---:|---:|---:|
| current public input/state/menu/catalog | yes | request subset | declared compiler subset | trace subset | yes |
| one candidate row | only after FOUND | yes | no | cited row in trace | yes |
| adjacency/transition graph | current observation only | no | no | opaque read-only environment handle | yes |
| source/ablation/support/PAD public event bundles | during childhood only | no | named compiler inputs | no | yes |
| b,z,h,roles,truth,expected trace | no | no | no | validation service only | yes |
| scores/order/index/timing/availability | no | backend/scorer | no | no | yes |
| donor map/derivation/condition/device | no | no | no | no | yes |

Unique episode-instance IDs exist only in `AuditEnvelope`. Public A/B and h
twins expose one preallocated `public_pair_handle`; it is explicitly a
matched-pair handle, not unique identity. Actor/scorer/compiler schemas contain
no root ID or audit label.

### 3.2 Authentic child actions

Childhood actions use `ChildCommittedActionEvent` with authorization
`CHILD_COMMIT`. It records the public instruction handle, committed action,
pre-state, and logical tick. `PublicObservation` must cite that action-event
handle and have a strictly later tick. Foundation, source, ablation, support,
and PAD events use this pair. A0 seals only potential-outcome, handles, and
schedule; the authentic event is appended only after the A1 child action.

Deployment actions use `MemoryAuthorizedActionEvent`; Phase-C experiment
dispatch uses `ExperimentDispatchEvent`. These three types are distinct and
are the only public action-event union members.

### 3.3 Provenance classes

Positive FULL/source/support/PAD rows have `AUTHENTIC` audit receipts whose
leaf events are child-commit then later observation. Corrupt fitted rows have
`DERIVED_CONTROL` audit receipts: every donor leaf is authentic, the transform
and donor mapping were presealed, and the output bytes are reproduced exactly.
Training/public row bytes do not expose either class. Donor identity,
derivation kind, and provenance tree remain audit-only.

The two visible citation handles on a source row are bundle handles: one binds
the four L action/outcome pairs and one the four R pairs. Handle-to-eight-event
expansion exists only in audit. Link citations analogously bind the exact
support bundle. This closes the fixed-two-citation schema without discarding
evidence.

### 3.4 Four pure compiler phases

All compiler decisions are condition-blind functions of canonical input bytes:

1. `SOURCE_ROW_COMPILATION`: verify exactly four authentic/derived-view L and
   four R pairs. For desired T and O, count matching outcomes and emit one
   `CHOICE_TABLE` row containing both `(action,count,total=4)` entries. Ties
   remain ties. Missing/extra events or a non-4 denominator rejects.
2. `LINK_ADMISSION`: accept only child-selected pairs whose fresh support
   results are exactly joint/left/right/nuisance=`1/0/0/0`. Never propose,
   rank, replace, or add.
3. `PAD_ROW_COMPILATION`: after authentic `P --p_0--> Q`, emit one
   gradient-bearing outcome-shaped `d_pad` under disconnected `[P,Q]`; no
   event before A1 can satisfy it.
4. `NEW_ROW_ADMISSION`: validate declaration and dispatch, reconstruct source
   preferred family from the authentic public source bundle, enumerate the
   public posterior over h, and admit exactly the declared n_h iff singleton.

Each compiler receives only the phase-appropriate closed `CompilerInput`; b,
z, h, expected answer, environment graph, and audit origin are unavailable.
`NO_ADMISSION` never contains a replacement row.

The fitted corruptions are not additional compiler phases. The package-bound
`SOURCE_OUTCOME_REBIND` prepares the derived source view consumed above;
`DREAM_LINK_REBIND` maps an already admitted authentic link to the presealed
pi payload. Each is a total deterministic control transform with the closed
`DerivationReceipt`; neither may inspect the endpoint, hidden bits, actor
output, model score, or condition result. This is why positive rows can retain
AUTHENTIC provenance while corrupt rows truthfully carry DERIVED_CONTROL.

## 4. Phase-lifted machine and exact budgets

### 4.1 State/action roster

Every phase/state exposes exactly 32 token-isomorphic action surfaces and one
successor per action. Numeric names below are audit notation, never visible.

```text
CHILD_FOUNDATION_ROUTE(i):
  a_i -> observed U_i fact; other 31 -> route-failure observation
  1 action, 0 READ

CHILD_FOUNDATION_TERMINAL(x):
  t_x -> observed T_x fact; other 31 -> terminal-failure observation
  1 action, 0 READ

CHILD_SOURCE X(l_count,r_count,l_occ,r_occ):
  L/R legal while own count<4; nth-within-action returns presealed T/O;
  other 30 -> absorbing source failure
  terminates only at counts (4,4); 8 actions, 0 READ

CHILD_ABLATION(i,trial):
  registered TEST payload -> table bit; other 31 -> absorbing failure
  one action for each of joint,left,right,nuisance; 4/lane, 0 READ

CHILD_SUPPORT(i,trial):
  same four-trial transition under freshly revealed support fixture;
  4/selected lane, 0 READ

CHILD_PAD P:
  p_0 -> Q observation; other 31 -> absorbing failure
  1 action, 0 READ

B:
  S_B --a_j--> U_j^B for j<8; j>=8 -> F_ROUTE
  U_i^B --b_i--> B_B; other b_j -> F_(i,j)
  B_B --c_0--> C_B; other c_j -> F_SHARED_j
  C_B --t_A/t_B--> matching terminal; other t_j -> F_TERMINAL_j
  FULL budget 3 READ, 4 actions; ATOMS budget 4 READ, 4 actions

C_PROBE:
  X_P --SOURCE_CHOICE L/R--> terminal choice record;
  other 30 -> failure
  1 READ, 1 action

C_LIVE:
  X_C --SOURCE_CHOICE L/R--> FAMILY_L/FAMILY_R
  FAMILY_L --E0/E1--> DISPATCHED_E; other 30 -> failure
  FAMILY_R --E2/E3--> DISPATCHED_E; other 30 -> failure
  outcome transition emits y; compiler transition emits ADMIT/NO_ADMISSION
  1 READ, 2 actions, exactly 1 declaration

D:
  U_i^D --b_i--> B_D; other b_j -> F_(i,j)^D
  B_D --c_0--> C_D; other c_j -> F_SHARED_j^D
  C_D --n_h--> D; every n_j,j!=h -> F_D_j
  2 READ, 3 actions
```

`C_B` and `C_D` are distinct phase-lifted states; terminal and outcome action
families never coexist at one state. X and every absorbing source/PAD/support/
dispatch state are explicit package rows. A B goal is valid only if its first
action matches `route(route_cue)` as well as reaching its terminal.

### 4.2 Goals and full-mounted goal intervention

Public B goal pair shares all non-goal bytes and `public_pair_handle`:

```text
G_A={kind:B,start:S_B,target:T_A,route_cue:q_uA,reads:3,actions:4}
G_B={kind:B,start:S_B,target:T_B,route_cue:q_uB,reads:3,actions:4}
```

Unique episode IDs are audit-only. Stage 0 stores complete JCS
`ActorEpisodeInput` bytes, defines `o_goal` as the first A/B differing byte,
and proves all bytes `[0,o_goal)` equal. `goal_pair_byte_cut.json` binds both
complete input hashes, `o_goal`, the first-difference JSON pointer, a bitmask
over the complete concatenated bytes, and the common ordered
`memory_catalog.public_anchor_handles`. Every `1` bit lies under `/goal/`;
every byte outside that subtree, including public pair handle, catalog,
anchors, action surfaces, system prompt, decode commitment, and RNG family,
is equal. Because public_pair_handle and decode commitment are shared, no
earlier opaque episode cue exists.

`FULL_GOAL_CUE_SWAP_B` mounts FULL and changes only G_A.route_cue from q_uA to
q_uB while keeping target T_A. The registered intervention goal's valid path
is `a_uB,b_uB,c_0,t_A`. The first query/return/entrance/link must redirect to
uB while the terminal query/action remains T_A. Its paired ActorEpisodeInput
allowed-difference bitmap permits only the route-cue handle bytes and binds
the same goal handle, target, public anchors, actor input prefix, decode
configuration, and inference family. This is
the goal-only causal intervention; it adds no fit.

`CATALOG_NO_GOAL_NO_CARRIER` remains a descriptive conjunction negative only.
It is never cited as goal isolation.

The D goal is identical across h:

```text
G_D={kind:D,start:U_uD^D,target:D,route_cue:null,reads:2,actions:3}
```

Public pair handle/input/decoder state are identical across h until the second
reader return.

### 4.3 DREAM evidence

All eight lanes have one joint, left, right, nuisance child trial:

```text
useful:      1,0,0,0
3 left-dec:  1,1,0,0
3 right-dec: 1,0,1,0
```

At A2 the child sees endpoint/type/count/length-matched pair handles and emits
exactly two. The entire public byte prefix is sealed before support, B/C/D
goals, theorem, compiler result, or hidden role. Fresh support admits only a
selected `1/0/0/0` pair. The deterministic public necessity rule is a 100%
ceiling conditional on complete evidence; chance exact-two is 1/28. Only
child provenance/agreement is claimed.

DREAM_DERANGED uses presealed `pi(i)=(i+dream_shift) mod8` and compiles key
U_i with sequence `[b_pi(i),c_0]`. The first action is syntactically legal and
enters a dead state. All authentic source/foundation rows remain byte-identical.

## 5. Source compiler, probes, and full C state machine

### 5.1 Authentic and crossed evidence

The child executes four L and four R actions. Nth-action outcomes are:

```text
b0: L=[T,T,T,O], R=[T,O,O,O]
b1: L=[T,O,O,O], R=[T,T,T,O]
```

SOURCE_DERANGED deterministically rebinds the same eight authentic outcomes:
sort T donor event IDs and assign them to `[L0,L1,R0,R1]`; sort O donors and
assign to `[L2,L3,R2,R3]`. Thus both actions have T=2,O=2 while total action
and outcome marginals, visits, shapes, and work remain fixed. Donors and
derivation are audit-only.

`SOURCE_ROW_COMPILATION` receives a `SourceEvidenceView` of eight canonical
evidence bindings. FULL supplies eight `AuthenticEvidencePair` values.
SOURCE_DERANGED supplies eight `DerivedControlEvidencePair` values: each keeps
one authentic donor action and its causally later donor observation intact in
audit, but separately declares the presealed presented L/R action used for the
control count. The compiler verifies the derivation receipt before counting;
it never rewrites an authentic event. It emits desired-T and desired-O
CHOICE_TABLE rows.
Each row has two `SourceStatistic` entries and two visible citation-bundle
handles. It never emits a preferred action or tie break.

### 5.2 C-probe traces and score

Each destroyed C probe has `CProbeGoal`, one READ and one action:

```text
READ SOURCE_INVERSE(X,desired outcome) -> CHOICE_TABLE row
SOURCE_CHOICE L or R citing that row -> terminal choice record
```

The row action mode CHOICE authorizes either listed action exactly once. The
binary scorer checks the chosen semantic action against the authentic root
orientation, after reversing presentation aliases:

```text
b0: T->L,O->R; b1:T->R,O->L
```

Four probes are T/O x canonical/reversed L/R and family presentation. One
root gives one mean. SOURCE_DERANGED's tie row is scored against the same
authentic labels; no post-treatment label exists.

### 5.3 C-live transitions

```text
C0 ActorEpisodeInput: X_C, desired T, public L->{E0,E1}/R->{E2,E3},
   hypotheses h0/h1, READ=1, actions=2.
C1 READ SOURCE_INVERSE(X,T) -> CHOICE_TABLE or MISS/BLOCKED.
C2 SOURCE_CHOICE L/R cites the row and enters FAMILY_L/R.
C3 PublicDeclaration commits chosen E, predictions for h0/h1, and complete
   outcome-to-row map.
C4 ExperimentDispatchEvent cites source choice+public menu and chooses only a
   member of the selected family.
C5 clone the process/RNG snapshot after dispatch bytes.
C6 h world emits causally later public y.
C7 NEW_ROW_ADMISSION recomputes authentic preferred family from the original
   public source bundle, validates declaration/dispatch, enumerates h={0,1},
   and returns n_h iff posterior singleton; nuisance returns NO_ADMISSION.
```

Potential outcomes:

```text
b0: E0=h,E1=1-h,E2=z,E3=1-z
b1: E2=h,E3=1-h,E0=z,E1=1-z
```

Stage 0 enumerates all 32 `(b,h,z,E)` compiler fixtures. A live root contains
its one independently drawn z and both h branches only. `R_r` requires the
authentic and SOURCE_READ_SWAP outcomes for both h at that root's z; it does
not pretend both z worlds were executed.

The h twins reuse every actor-visible handle and one cloned process/RNG state.
The result bundle hashes every input/output byte through dispatch and binds
`o_C_outcome` as the first h-dependent byte in the public outcome.

### 5.4 SOURCE_READ_SWAP_C

This no-write FULL-mounted fork returns a hit-matched copy of the authentic T
CHOICE_TABLE with its L/R count bindings swapped. It changes row handle and
the two declared semantic count positions only; status, query, actions,
totals, citation cardinality, lengths, RPC envelope, and inference RNG family
match. The opposite source action becomes the unique 3/4 maximum.

The actor must choose that opposite action, enter the nuisance family,
dispatch there, receive the ordinary root-z public outcome, and obtain
NO_ADMISSION in both h branches. Ignoring the swapped statistics, entering
the original family, or admitting a row fails its validity gate and R.

## 6. Reader theorem, neural gates, and RPC bytes

### 6.1 Exact row/action modes

MemoryRow.action_mode is:

- `ATOM`: one listed action, consumed after one use;
- `SEQUENCE`: exactly two ordered actions, cursor survives intervening public
  observation and expires after action 2 or any READ;
- `CHOICE_TABLE`: exactly two `SourceStatistic` entries, either action may be
  chosen once, then the citation expires.

Wrong, expired, repeated, uncited, out-of-order, or extra action enters an
absorbing malformed state.

### 6.2 Complete query and availability tables

The only public query types are:

```text
ROUTE_BY_CUE(B,S_B): q -> 32 route-action candidates
ATOM_SUCCESSOR(B,U_i^B): U_i -> 32 b candidates
ATOM_SUCCESSOR(B,B_B): B_B -> 32 c candidates
LINK_SUCCESSOR(B|D,U_i): U_i -> 32 [b_j,c_0] candidates
TERMINAL_TO_TARGET(B,C_B): target -> 32 t candidates
SOURCE_INVERSE(C_PROBE|C_LIVE,X): desired T/O -> 32 choice-table candidates
NEW_SUCCESSOR(D,C_D): [C_D,D] -> 32 n candidates
```

For every legal canonical request, `availability_relations.json` enumerates
row SHA-256 values exactly:

```text
FULL_OLD: route/terminal foundations + two selected authentic links +
          authentic desired-T/O CHOICE_TABLE rows
SOURCE_DERANGED_OLD: same, replacing only both source rows by truthful ties
DREAM_DERANGED_OLD: same, replacing only selected links by pi payloads
ATOMS: route/terminal foundations + separate selected b and c atoms; no link
S1_OFF/NO_CARRIER: empty
FULL_NEW_h: FULL_OLD union {n_h}
OLD_PLUS_PAD: FULL_OLD; d_pad exists only under audit extract, no public NEW row
```

Each cut deletes one named SHA. Each payload swap replaces one named SHA with
one presealed matched wrong-row SHA. `canonical_returns.json` maps every
positive ideal `(carrier,request)` to its one row SHA; all other legal requests
MISS. There is no prose-only set membership.

For a schema-valid READ with budget remaining, runtime decrements the budget,
renders the exact `RecognitionScorerInput` for all 32 candidates in roster
order, and obtains deterministic YES/NO log-probability hex values. The
aggregate and tie rule, threshold, minimum margin, and candidate-order
invariance test are literal fields of `reader_binding.json`. A unique passing
candidate returns FOUND; no passing candidate or a threshold/margin tie
returns MISS. BLOCKED is reserved solely for a schema-valid request made with
zero reads remaining and consumes no scorer call. A malformed request enters
the public malformed terminal rather than being converted to MISS/BLOCKED.
Every runtime FOUND must equal the availability-listed row; otherwise
`ROOT_UNAVAILABLE_FOUND`. Thus model false positives cannot masquerade as a
charged control MISS.

### 6.3 Formal machine and model acceptance

The BFS state contains phase-lifted state, goal and route-validity predicate,
budgets, complete request/row bytes, action mode/cursor/expiry, public event
history, declaration/dispatch status, and terminal/failure status. Formal
FOUND is legal only for a row listed in A_K(request). The checker proves:

- any availability-respecting ATOMS policy needs >=4 B reads and the
  canonical witness uses exactly 4;
- any FULL policy needs >=3 and canonical FULL uses exactly 3 for both goals;
- any FULL_NEW policy needs >=2 D reads and canonical uses exactly 2;
- each named cut makes its endpoint unreachable; and
- no repeated/MISS/BLOCKED/returned-anchor/adaptive legal policy bypasses.

This theorem says nothing about a fitted neural reader. Model acceptance
rejects a root for any unavailable FOUND, missing required FOUND, wrong anchor,
filler/bypass return, or row suppressed by a cut. Exact text carriers provide
FULL and ATOMS ceilings. These checks are constituent validity gates, not
favorable endpoint zeros.

### 6.4 Exact padded RPC

`reader_binding.json` binds `RPC_BYTES=16384`, logical `DELTA=1`, physical
`DEADLINE_NS=120000000000`, the monotonic-clock source, padding construction,
scorer count 32, worker image, and exact binary frame:

```text
ASCII("MCRPC5\0")                    7 bytes
U32BE(payload_length)                4 bytes
payload = JCS(MemoryReturn)+LF        payload_length bytes
pad = SHAKE256("MCRPC5-PAD\0" || query_fingerprint_bytes,
               RPC_BYTES-11-payload_length)
```

Every FOUND/MISS/BLOCKED/cut/swap/no-carrier return is exactly `RPC_BYTES`.
The checker proves every canonical fixture has `payload_length<=16373`.
Any overflow is GLOBAL_INVALID. The actor decodes only the framed
payload; pad bytes are observable but deterministic from its public request.

Actor-observable alphabet is EpisodeInput frame, RPC frame at logical tick,
PublicObservation frame, EpisodeTerminal frame. There is no clock, network,
file/cache/process access, callback/exception channel, or telemetry. Every
READ suspends the actor, scores exactly 32 candidates, and releases at
`t+DELTA`. On overrun the actor never resumes; audit records ROOT_INVALID and
no branchable public continuation.

`rpc_observable_allowed_diff.json` is a bitmask over concatenated complete
actor-observable bytes for each matched pair. Hit-matched controls allow only
named row payload/handle positions; availability controls additionally allow
status/null-row/pad-derived positions. All other bytes, total lengths, release
ticks, message counts, and callback order must be identical after alpha
normalization. Fake-clock tests cover multiple subdeadline delays and overrun.

### 6.5 Matched inference RNG families

`actor_binding.json` binds model, tokenizer, chat template bytes, renderer,
inference engine/runtime/image, decoding algorithm/parameters/stops, and token
RNG implementation. Recognition scoring is deterministic and sampling-free.

Actor draws use:

```text
INFER_RNG(rho_r,family_id,token_ordinal) =
 H("infer",BYTES(rho_r),UTF8(family_id),U64(token_ordinal))
```

The exact family table is:

```text
B_STANDARD: both ordinary goals under FULL, SOURCE_DERANGED,
            DREAM_DERANGED, S1_OFF, B_LINK_CUT, B_LINK_PAYLOAD_SWAP,
            every catalog order, and goal/catalog negatives
B_GOAL_CUE: G_A and FULL_GOAL_CUE_SWAP_B
C_PROBE_0..3: FULL, SOURCE_DERANGED, S1_OFF for that probe ordinal
C_LIVE: FULL h0/h1 and SOURCE_READ_SWAP h0/h1
D: FULL_NEW_h0/h1, OLD_PLUS_PAD, NO_SLEEP2, both cuts, both payload swaps,
   and no-carrier cells
INTERFACE: every fitted carrier and birth on the 32 interface cases
NONHARM: every fitted carrier and birth on the 32 generic cases
```

`B_STANDARD`, `B_GOAL_CUE`, `C_PROBE_0` through `C_PROBE_3`, `C_LIVE`, `D`,
`INTERFACE`, and `NONHARM` are the literal family IDs; none contains
condition, h, goal member, or control ID. Probe ordinal is a pre-treatment
task member, not a condition.
Each compared episode starts from the same birth actor state and draw counter
zero. C twins are additionally cloned after dispatch. The result receipt logs
every token ordinal and draw digest; any family mismatch invalidates the
component.

## 7. Common training RNG, PAD equality, and provenance

### 7.1 Common realized optimization

S1 triplet RNG is keyed only by `(rho_r,"S1",stream,step_or_slot)`; S2 uses
`"S2"`. Condition/build identity is forbidden. Triplet members share initial
checkpoint, ordered slots, batch membership/order, padding, dropout/data-worker
draws, deterministic kernels, optimizer initialization/schedule, physical
device UUID, driver/runtime/image, and health envelope. They run in sterile
sequential processes in a presealed random order. No state crosses fits.

Artifact IDs may differ; realized nuisance may not. Pairwise receipts bind
initialization, tensors, slot/batch/step, RNG counters, masks, and device/image.

### 7.2 PAD and S1 allowed-difference tensors

A0 seals PAD potential outcome/handles/schedule only. After the child commits
p_0 at A1, the later Q observation supports PAD_ROW_COMPILATION. d_pad is
truthful, gradient-bearing, outcome-shaped, keyed by disconnected `[P,Q]`, and
publicly unqueryable. Audit extraction uses the same 32-score reader envelope
through a private key; it adds no public query.

For each paired rendered example materialize:

```text
input_ids,attention_mask,position_ids,labels,loss_mask,
semantic_allowed_diff_bitmap,
view_id,visit_id,deck_slot,batch_index,optimizer_step,
dropout_stream_indices,renderer_sha256
```

Allowed semantic fields are row handle, key handles, action handles,
destinations, source counts where applicable, and visible citation handles.
All aliases are pre-role token-isomorphic. Raw identities remain distinct.
Input/label tokens may differ only at bitmap 1; after role-blind alpha
normalization they are identical. Shapes, attention/position/loss masks,
supervised-token count, render visits, deck/batch/step, dropout indices,
forward/backward calls, updates, and total token work are bit-identical.

The rule applies to FULL_NEW_h0/FULL_NEW_h1/d_pad and every differing S1 row.
An undeclared difference or mismatched work is GLOBAL_INVALID before fitting.

### 7.3 Exact S1/S2 decks

```text
S1 FULL: authentic source choice tables + authentic selected links +
         common grounded route/terminal rows
S1 SOURCE_DERANGED: truthful 2/4-2/4 choice tables + identical other rows
S1 DREAM_DERANGED: pi links + identical source/foundation rows

S2 h0: exact FULL old deck + admitted n0
S2 h1: exact FULL old deck + admitted n1
S2 PAD: exact FULL old deck + admitted d_pad
```

All reconstruct from immutable birth with exactly qualified W*. No M outcome
may change views, rank, learning rate, dose, masks, preservation, reader, or
threshold. If W* cannot render/extract CHOICE_TABLE/link/new/PAD rows, M is not
ready and no substitute is invented.

## 8. Exact controls, traces, validity gates, and estimands

### 8.1 Constructive traces and named controls

FULL B uses 3 READ/4 actions:

```text
ROUTE(q_u)->a_u; ACT ->U_u
LINK(U_u)->[b_u,c_0]; ACT,ACT ->C_B
TERMINAL(target)->t_target; ACT ->target
```

ATOMS separates b/c and uses 4 READ/4 actions. FULL D uses 2 READ/3 actions:

```text
LINK(U_uD)->[b_uD,c_0]; ACT,ACT ->C_D
NEW(C_D,D)->n_h; ACT ->D
```

Named inference-only controls:

```text
S1_OFF_B, S1_OFF_C
INTERFACE_CANARY
NONHARM_PANEL
GOAL_CATALOG_NO_CARRIER
CATALOG_NO_GOAL_NO_CARRIER             descriptive only
FULL_GOAL_CUE_SWAP_B                   FULL mounted, one goal field changed
CATALOG_PERMUTE_P0,P1,P2,P3
B_LINK_CUT
B_LINK_PAYLOAD_SWAP
SOURCE_READ_SWAP_C
D_OLD_LINK_CUT
D_NEW_ROW_CUT
D_OLD_LINK_PAYLOAD_SWAP
D_NEW_ROW_PAYLOAD_SWAP
NO_SLEEP2
OLD_PLUS_PAD
TEXT_FULL
TEXT_ATOMS_READ4
```

D old swap returns `[b_pi(uD),c_0]`; D new swap returns n_(1-h). Both are
separate hit-matched legal wrong-action interventions. Cuts are charged MISS
availability interventions. RAW_WRONG_ROOT remains an unmatched descriptive
diagnostic outside every gate/estimand/claim.

Every fitted carrier runs the same inference-only 32-case interface canary
and 32-case generic non-memory panel from birth actor reset. Interface passes
only at 32/32 canonical typed READ/action traces with zero malformed,
unavailable, or uncited event. Non-harm passes only when the paired mean
generic endpoint difference `(carrier-birth)>=-0.05`; both use package-bound
common RNG families, tasks, scorer bytes, and the same 32 cases. These are
validity gates, not mechanism endpoints, and all their launched device time is
charged to evaluation cost.

### 8.2 Component validity gates

Raw endpoint values are never imputed for an invalid subtracted control. Raw
contrasts are computed only when their component gate is true; otherwise they
are `NA` descriptively and the confirmatory indicator is zero.

`G_S(r)` requires both FULL and SOURCE_DERANGED S1 fits to launch and complete;
common RNG/device/tensor receipts; exact extraction of both FULL 3/1 choice
tables and both deranged 2/2 tie tables; orthogonal link/foundation equality;
interface/non-harm; all eight four-probe episodes complete; exact FOUND rows,
choice actions, RPC bytes, and common inference draws; no unavailable return.

`G_M(r)` requires FULL and DREAM_DERANGED S1 fits complete; exact authentic
and pi link extraction at both keys; common nuisance/work; source/foundation
preservation; both B goal episodes in both arms complete; expected FOUND and
legal wrong-action rows; B_LINK_PAYLOAD_SWAP correctly applied; no generic
interface/non-harm or unavailable-row failure.

`G_U(r)` requires valid FULL S1 extraction/episodes and completed S1_OFF_B/C
RPCs with exact charged MISS envelopes, identical public inputs/draw families,
no timeout/malformed path, and no unavailable FOUND. A broken OFF RPC is not a
favorable zero.

`G_W(r)` requires all three S2 fits launched/completed; common RNG/device/work
and PAD tensor receipts; exact old-row retention and n0/n1/d_pad extraction;
both h FULL_NEW and both h OLD_PLUS_PAD D episodes complete; expected
FOUND/MISS envelopes, common inference family, canonical actions, and no
unavailable return. A missing PAD fit/row cannot make W positive.

`G_F(r)` requires valid FULL_NEW h0/h1 D traces and every D old-link/new-row
cut and old-link/new-row payload swap to be applied exactly and complete under
the matched D RNG family. Each cut must yield its charged MISS, each swap its
registered legal wrong row/action, and every control must terminate as a
VALID_ENDPOINT_FAILURE without timeout, malformed action, unavailable FOUND,
or extraction/intervention defect.

`G_R(r)` requires G_S,G_M,G_U,G_W,G_F plus every named R control, compiler, prefix,
side-channel, provenance, canary, cut/swap, and reset receipt.

Define valid raw contrasts:

```text
S_r = mean4 Y_C(FULL)-mean4 Y_C(SOURCE_DERANGED) if G_S else NA
M_r = min_g[Y_B(FULL,g)-Y_B(DREAM_DERANGED,g)] if G_M else NA
U_r = min(min_g[Y_B(FULL)-Y_B(S1_OFF)],
          mean4[Y_C(FULL)-Y_C(S1_OFF)]) if G_U else NA
W_r = min_h[Y_D(FULL_NEW_h)-Y_D(OLD_PLUS_PAD,h)] if G_W else NA
F_r = min_h min(FULL_NEW_h-D_OLD_LINK_CUT_h,
                FULL_NEW_h-D_NEW_ROW_CUT_h,
                FULL_NEW_h-D_OLD_LINK_PAYLOAD_SWAP_h,
                FULL_NEW_h-D_NEW_ROW_PAYLOAD_SWAP_h) if G_F else NA
```

Confirmatory indicators are:

```text
I_S=1[G_S and S_r>0]
I_M=1[G_M and M_r>0]
I_U=1[G_U and U_r>0]
I_W=1[G_W and W_r>0]
I_R=1[G_R and R_r=1]
```

An invalid/missing positive or control cell makes its indicator 0. Only a
VALID_ENDPOINT_FAILURE in a completed valid control supplies endpoint zero.

### 8.3 D specificity and noncompensatory R

The displayed `F_r` is defined only under `G_F`; otherwise it is `NA`, never a
favorable number. For valid completed D controls:

```text
F_r=min_h min(
 FULL_NEW_h - D_OLD_LINK_CUT_h,
 FULL_NEW_h - D_NEW_ROW_CUT_h,
 FULL_NEW_h - D_OLD_LINK_PAYLOAD_SWAP_h,
 FULL_NEW_h - D_NEW_ROW_PAYLOAD_SWAP_h)
```

`R_r=1` requires:

1. all package/checker/schema/entropy/ACL/phase-machine/RPC/formal-BFS receipts;
2. exact authentic versus derived-control provenance for every row;
3. child pair seal before future bytes, correct pair, and fresh support;
4. all S1/S2 intended rows extracted with common nuisance and orthogonal
   preservation; all component gates true;
5. FULL B both goals pass, ATOMS passes at 4, exact public pair/goal byte cut
   passes, and FULL_GOAL_CUE_SWAP redirects only cue-dependent route/link;
6. every carrier-free/cut cell completes with its expected MISS; every catalog
   order preserves semantics; B payload swap returns legal wrong content;
7. source FULL score=1, deranged rows remain truthful ties, T/O reverses FULL
   action, SOURCE_READ_SWAP redirects live choice/family and blocks admission;
8. C h prefixes match through dispatch; both authentic h admissions yield n_h;
   all Stage-0 nuisance cases reject and live root-z swapped branches reject;
9. FULL_NEW retains old rows/B behavior, extracts only its h row, PAD extracts
   only privately and exposes no public D new row;
10. FULL_NEW both h D paths pass; PAD/no-sleep/cuts/separate swaps are valid
    completed failures; F_r>0 and W_r>0;
11. no forbidden byte, unavailable return, raw-context reset leak, interface/
    non-harm/canary failure, or LoRA outside recognition READ.

Later success never compensates. RAW_WRONG_ROOT is absent.

## 9. Schedule, stages, exact TEXT gate, and statistics

### 9.1 Schedule law

The package enumerates eligible `(device_uuid,image,driver,runtime)` entries,
all six S1/S2 condition permutations, exact B/C/D control ID lists, and the
four candidate orders:

```text
P0=sigma([0..31])
P1=sigma([31..0])
P2=sigma([13..31,0..12])
P3=sigma([0,2,..30,1,3,..31])
```

Each independent root seed draws one S1 device for the entire triplet, one S2
device for its triplet, condition orders, and control orders. Balance is only
in expectation over iid root seeds; realized counts are reported. Within a
root, every triplet condition occurs exactly once and every four-probe block
uses P0..P3 exactly once under its independently drawn rotation. No cohort
cycles or shares a rotation across roots. A skipped S2 schedule is unused, not
reassigned. Shared-system departures with uncertain root boundaries are
GLOBAL_INVALID.

### 9.2 Exact TEXT success

TEXT roots are separate and never promoted. `T_r=1` only when:

- all foundation/source/ablation/PAD child actions and later observations are
  canonical and complete;
- child selects exactly the evidence-indicated pair before the byte cut and
  fresh support admits both;
- text FULL, source-tie, DREAM-deranged, atoms, n0/n1, and PAD carriers expose
  exactly their registered rows with no unavailable return;
- FULL solves both B goals in 3 reads, ATOMS in 4, and goal cue swap redirects;
- all four C probes, authentic live C h twins, and SOURCE_READ_SWAP h twins
  complete with correct admission/rejection;
- FULL text n0/n1 solve both D twins, while exact text cuts/swaps/PAD/no-sleep
  give valid completed failures; and
- schemas, ACL, provenance, RPC, prefixes, model checker, and reset pass.

Stage 1 runs T1..T4. If 4/4 pass, proceed. If 2/4 or 3/4, run T5..T8 and require
at least 6/8. Fewer than 2/4 stops. A failed TEXT root is never replaced.
`T_r` is a mechanics feasibility gate, not confirmation evidence.

### 9.3 DEV/confirmation and tests

DEV `[D1..D8]` is a presealed nested prefix: S1 kill D1/D2=6 fits, then S2
kill=6 more only if both pass, then D3..D8. Require >=6/8 `I_R=1`; freeze
mechanics. CONF is 16 fresh source-disjoint roots with no replacement,
extension, early-success stop, or rerun. Frozen S1 futility may skip S2 but the
root indicators remain zero.

Test ordered nulls:

```text
Pr(I_S=1)<=.5 -> Pr(I_M=1)<=.5 -> Pr(I_U=1)<=.5 ->
Pr(I_W=1)<=.5 -> Pr(I_R=1)<=.5
```

Each uses exact one-sided Binomial(16,.5) at alpha .05; stop confirmatory
rejection at first non-rejection. This fixed sequence controls FWER. >=12/16
is required because the exact tail is `2517/65536=.0384063720703125`.
Invalid/missing controls are indicator zero by construction. Report raw valid
contrasts, all failure codes, exact p, and one-sided 95% Clopper--Pearson lower
bound `Beta^-1(.05;K,17-K)`; post-stop results are descriptive.

The iid inference is conditional on the registered independent-root entropy
sampling assumption and complete root-local schedule/draw isolation. The
mechanical DREAM ceiling/chance results are descriptive.

## 10. Fit counts and complete measured cost

Maximum M fit counts remain:

```text
3 S1/root + 3 S2/upstream survivor
two-root S1 kill 6; two-root complete kill 12
eight-root DEV <=48; confirmation <=96; combined <=144
```

These exclude writer/reader qualification and TEXT. Resource accounting never
sums only completed fits. For every launched fit attempt `a`, record exclusive
device-allocation start and release:

```text
C_fit_launched_ns = sum_a (
  u64(device_release_ns[a])-u64(device_allocation_ns[a]))
C_fit_launched_seconds = C_fit_launched_ns / 1000000000
```

Crashes, timeouts, aborts, and partial S1/S2 attempts are included. If a node
disappears, release is the provider/lease release timestamp, or the last
exclusive-allocation boundary only when independently receipted; ambiguity is
GLOBAL_INVALID for cost reporting. Report completed/failed/aborted seconds by
deck class, device UUID, and image.

Separately report all launched TEXT/reader/actor/compiler device seconds,
CPU materialization/checking seconds, queue time, reset/serialization time,
and W*/reader qualification cost. Stage-0/TEXT/kill/futility stops are named
reasons actual work can be below maxima. No generic per-fit multiplier,
unmeasured bound, ideal packing, or wall-time promise is allowed.

The exact non-fit device totals use the same exclusive-allocation intervals:

```text
C_TEXT_device = sum all launched TEXT actor/reader device intervals
C_eval_device = sum all launched DEV/CONF actor/reader device intervals
C_qual_device = sum all launched W*/reader-qualification device intervals
C_device_total = C_fit_launched_seconds+C_TEXT_device+C_eval_device+C_qual_device
```

Compiler/materializer/checker CPU intervals are summed separately from their
monotonic start/release receipts and never converted into device seconds.
Every aborted, failed, timed-out, and partial TEXT/eval/qualification launch
is included exactly as for fits. The result bundle reports counts and seconds
by `COMPLETE|CRASH|TIMEOUT|ABORT`; unknown ownership or a missing release
boundary invalidates cost reporting rather than silently charging zero.

## 11. V4 blocker disposition

V5 makes these zero-fit repairs:

- invalid subtracted controls cannot create positives: `G_*` validates every
  constituent, raw invalid contrasts are NA, and confirmatory `I_*` becomes 0;
- source deranged emits truthful hit-matched 2/4--2/4 CHOICE_TABLE rows rather
  than a privileged target; SOURCE_READ_SWAP swaps authentic count bindings;
- closed child-commit/source/PAD/link/new compiler phases and provenance split
  authentic positives from derived controls;
- public pair handle removes episode-ID leakage, exact `o_goal` spans full
  ActorEpisodeInput, and FULL_GOAL_CUE_SWAP isolates a goal field with carrier;
- package manifest transitively binds every byte through Merkle/file tables;
  actual closed schemas and result-bundle receipts are normative;
- independent root seeds come from a pre-outcome entropy transcript under an
  explicit sampling assumption; typed hash encoding, alias enumeration,
  sigma, collision and fixed index laws are complete;
- all states are phase-lifted, X/dead states exist, every state has 32 actions,
  budgets and C probe/live traces are exact, and A_K/canonical returns are
  concrete package tables;
- RPC frames have exact total bytes/padding/release and transcript bitmaps;
  inference RNG families are enumerated and actor runtime is bound;
- root-local/global failure classes are frozen before outcomes;
- every launched fit second, including crashed/partial work, is counted; and
- TEXT success and every stage stop/cost category are exact.

No Stage 0, TEXT, reader-model acceptance, or M fit is ready until the actual
manifest-bound package and independent checker exist and pass.

## 12. Normative closed schema catalog

The following schema algebra is normative and has a deterministic JSON-Schema
translation. `OBJ{...}` means JSON object with exactly the listed required
fields and `additionalProperties:false`. `VEC[n,T]` means array with
`minItems=maxItems=n`; `VEC[a..b,T]` gives inclusive bounds. `OPT[T]` means
`anyOf[T,{"type":"null"}]`. `ONEOF[...]` becomes JSON-Schema `oneOf`.
`ENUM[x...]` becomes a literal JSON enum, and `CONST[x]` a literal JSON
`const`; bare symbolic values denote JSON strings unless they are `null` or
numbers. `STRING` is the bounded string below. No unresolved reference,
omitted field, or implicit subtype is permitted.

```text
U53      = {"type":"integer","minimum":0,"maximum":9007199254740991}
BIT      = {"type":"integer","enum":[0,1]}
STRING   = {"type":"string","minLength":1,"maxLength":4096}
U64D     = {"type":"string","pattern":"^(0|[1-9][0-9]{0,19})$"}
HEX16    = {"type":"string","pattern":"^[0-9a-f]{16}$"}
HEX64    = {"type":"string","pattern":"^[0-9a-f]{64}$"}
HANDLE26 = {"type":"string","pattern":"^[a-z2-7]{26}$"}
B64U     = {"type":"string","pattern":"^[A-Za-z0-9_-]*$"}
BLOB     = OBJ{bytes_b64u:B64U,byte_length:U53,sha256:HEX64}
```

The exact closed objects are:

```text
FailureCode = ENUM[NONE,
  GLOBAL_PACKAGE_MEMBER,GLOBAL_MERKLE,GLOBAL_SCHEMA,GLOBAL_CHECKER,
  GLOBAL_CAPABILITY,GLOBAL_SHARED_STATE,GLOBAL_BINDING,
  GLOBAL_PROTOCOL_MUTATION,GLOBAL_ENTROPY,GLOBAL_COMMON_NUISANCE,
  GLOBAL_UNKNOWN,
  ROOT_CHILD_OMISSION,ROOT_MALFORMED_ACTION,ROOT_FIT_CRASH,
  ROOT_FIT_TIMEOUT,ROOT_RPC_OVERRUN,ROOT_UNAVAILABLE_FOUND,
  ROOT_INTERVENTION_MISMATCH,ROOT_LOCAL_DEVICE,
  ROOT_EXTRACTION_FAILURE,ROOT_WORK_MISMATCH,ROOT_INTERFACE_FAILURE,
  ROOT_CANARY_FAILURE,ROOT_NONHARM_FAILURE,
  VALID_WRONG_ROUTE,VALID_WRONG_ACTION,VALID_WRONG_TERMINAL,
  VALID_BUDGET_EXHAUSTED,VALID_READ_MISS,VALID_CUT_ENDPOINT,
  VALID_SWAP_ENDPOINT,VALID_INCOMPLETE_ENDPOINT]

DecodeConfig = OBJ{
  algorithm:ENUM[GREEDY,TOP_P],temperature_hex:STRING,
  top_p_hex:STRING,top_k:U53,max_tokens:U53,
  stop_blobs:VEC[0..8,BLOB],rng_commitment:HEX64,
  tokenizer_sha256:HEX64,chat_template_sha256:HEX64,
  renderer_sha256:HEX64,runtime_image_sha256:HEX64
}

ActionSurface = OBJ{action_handle:HANDLE26,verb_surface:BLOB}

BGoal = OBJ{
  kind:CONST[B],goal_handle:HANDLE26,start_handle:HANDLE26,
  target_handle:HANDLE26,route_cue_handle:HANDLE26,
  desired_source_outcome_handle:CONST[null],read_budget:CONST[3],
  action_budget:CONST[4]
}
CProbeGoal = OBJ{
  kind:CONST[C_PROBE],goal_handle:HANDLE26,start_handle:HANDLE26,
  target_handle:HANDLE26,route_cue_handle:CONST[null],
  desired_source_outcome_handle:HANDLE26,read_budget:CONST[1],
  action_budget:CONST[1]
}
CLiveGoal = OBJ{
  kind:CONST[C_LIVE],goal_handle:HANDLE26,start_handle:HANDLE26,
  target_handle:HANDLE26,route_cue_handle:CONST[null],
  desired_source_outcome_handle:HANDLE26,read_budget:CONST[1],
  action_budget:CONST[2]
}
DGoal = OBJ{
  kind:CONST[D],goal_handle:HANDLE26,start_handle:HANDLE26,
  target_handle:HANDLE26,route_cue_handle:CONST[null],
  desired_source_outcome_handle:CONST[null],read_budget:CONST[2],
  action_budget:CONST[3]
}
PublicGoal = ONEOF[BGoal,CProbeGoal,CLiveGoal,DGoal]

PublicMenuEntry = OBJ{
  source_action_handle:HANDLE26,
  experiment_action_handles:VEC[2,HANDLE26]
}
PublicMenu = OBJ{entries:VEC[2,PublicMenuEntry],menu_sha256:HEX64}

MemoryCatalog = OBJ{
  v:CONST[mcore.v5],legal_query_types:VEC[0..6,ENUM[
    ROUTE_BY_CUE,ATOM_SUCCESSOR,LINK_SUCCESSOR,TERMINAL_TO_TARGET,
    SOURCE_INVERSE,NEW_SUCCESSOR]],
  public_anchor_handles:VEC[0..4,HANDLE26],
  candidate_schema_sha256:HEX64,reads_remaining:U53
}

ActorEpisodeInput = OBJ{
  v:CONST[mcore.v5],public_pair_handle:HANDLE26,
  phase:ENUM[CHILD_FOUNDATION_ROUTE,CHILD_FOUNDATION_TERMINAL,
    CHILD_SOURCE,CHILD_ABLATION,CHILD_SUPPORT,CHILD_PAD,
    B,C_PROBE,C_LIVE,D],
  actor_model_sha256:HEX64,system_prompt:BLOB,
  goal:OPT[PublicGoal],current_state_handle:HANDLE26,
  legal_action_surfaces:VEC[32,ActionSurface],
  public_menu:OPT[PublicMenu],task_input:OPT[BLOB],
  memory_catalog:MemoryCatalog,decode_config:DecodeConfig
}

RecognitionRequest = OBJ{
  v:CONST[mcore.v5],phase:ENUM[B,C_PROBE,C_LIVE,D],
  query_type:ENUM[ROUTE_BY_CUE,ATOM_SUCCESSOR,LINK_SUCCESSOR,
    TERMINAL_TO_TARGET,SOURCE_INVERSE,NEW_SUCCESSOR],
  public_state_handle:HANDLE26,public_goal_handle:HANDLE26,
  public_anchor_handles:VEC[1..2,HANDLE26],
  candidate_schema_sha256:HEX64,call_ordinal:U53,reads_remaining:U53
}

SourceStatistic = OBJ{
  action_handle:HANDLE26,desired_outcome_handle:HANDLE26,
  matching_count:U53,total_count:CONST[4]
}
MemoryRow = OBJ{
  v:CONST[mcore.v5],row_handle:HANDLE26,
  query_type:ENUM[ROUTE_BY_CUE,ATOM_SUCCESSOR,LINK_SUCCESSOR,
    TERMINAL_TO_TARGET,SOURCE_INVERSE,NEW_SUCCESSOR],
  action_mode:ENUM[ATOM,SEQUENCE,CHOICE_TABLE],
  key_handles:VEC[1..2,HANDLE26],
  ordered_action_handles:VEC[0..2,HANDLE26],
  source_statistics:VEC[0..2,SourceStatistic],
  destination_handles:VEC[0..2,HANDLE26],
  visible_citation_handles:VEC[2,HANDLE26]
}
MemoryReturn = OBJ{
  v:CONST[mcore.v5],status:ENUM[FOUND,MISS,BLOCKED],
  query_fingerprint_sha256:HEX64,row:OPT[MemoryRow],
  reads_remaining:U53
}
PublicReadEvent = OBJ{
  v:CONST[mcore.v5],request:RecognitionRequest,response_rpc_frame:BLOB,
  logical_request_tick:U53,logical_release_tick:U53
}

ChildCommittedActionEvent = OBJ{
  v:CONST[mcore.v5],event_handle:HANDLE26,
  authorization:CONST[CHILD_COMMIT],public_instruction_handle:HANDLE26,
  action_handle:HANDLE26,pre_state_handle:HANDLE26,logical_tick:U53
}
MemoryAuthorizedActionEvent = OBJ{
  v:CONST[mcore.v5],event_handle:HANDLE26,
  authorization:CONST[MEMORY_ROW],row_handle:HANDLE26,
  action_handle:HANDLE26,pre_state_handle:HANDLE26,logical_tick:U53
}
ExperimentDispatchEvent = OBJ{
  v:CONST[mcore.v5],event_handle:HANDLE26,
  authorization:CONST[PUBLIC_DISPATCH],source_choice_event_handle:HANDLE26,
  public_menu_sha256:HEX64,experiment_action_handle:HANDLE26,
  pre_state_handle:HANDLE26,logical_tick:U53
}
PublicObservation = OBJ{
  v:CONST[mcore.v5],event_handle:HANDLE26,
  action_event_handle:HANDLE26,observation_handle:HANDLE26,
  outcome_surface:BLOB,post_state_handle:HANDLE26,logical_tick:U53
}
PublicPairSelection = OBJ{
  v:CONST[mcore.v5],pair_handles:VEC[2,HANDLE26],logical_tick:U53
}
PublicDeclaration = OBJ{
  v:CONST[mcore.v5],cited_source_row_handle:HANDLE26,
  source_choice_event_handle:HANDLE26,hypotheses:CONST[[0,1]],
  chosen_experiment_handle:HANDLE26,predicted_outcomes:VEC[2,BIT],
  outcome_row_handles:VEC[2,HANDLE26],logical_tick:U53
}

AuthenticEvidencePair = OBJ{
  binding_class:CONST[AUTHENTIC_EVENT_PAIR],
  action:ChildCommittedActionEvent,observation:PublicObservation
}
DerivedControlEvidencePair = OBJ{
  binding_class:CONST[DERIVED_CONTROL_PAIR],
  presented_action_handle:HANDLE26,
  donor_action:ChildCommittedActionEvent,
  donor_observation:PublicObservation,
  derivation_receipt_handle:HANDLE26
}
EvidencePair = ONEOF[AuthenticEvidencePair,DerivedControlEvidencePair]
SourceEvidenceView = OBJ{
  v:CONST[mcore.v5],pairs:VEC[8,EvidencePair],
  desired_outcome_handles:VEC[2,HANDLE26],
  visible_citation_bundle_handles:VEC[2,HANDLE26]
}
AblationEvidenceView = OBJ{
  v:CONST[mcore.v5],selection:PublicPairSelection,
  evidence_pairs:VEC[8,AuthenticEvidencePair]
}
PadEvidenceView = OBJ{
  v:CONST[mcore.v5],pair:AuthenticEvidencePair,
  reserved_row_handle:HANDLE26
}
CompilerInput = OBJ{
  v:CONST[mcore.v5],compiler_phase:ENUM[SOURCE_ROW_COMPILATION,
    LINK_ADMISSION,PAD_ROW_COMPILATION,NEW_ROW_ADMISSION],
  source_evidence:OPT[SourceEvidenceView],
  ablation_evidence:OPT[AblationEvidenceView],
  pad_evidence:OPT[PadEvidenceView],
  declaration:OPT[PublicDeclaration],dispatch:OPT[ExperimentDispatchEvent],
  public_outcome:OPT[PublicObservation],public_task_law:BLOB
}
CompilerDecision = OBJ{
  v:CONST[mcore.v5],status:ENUM[ADMIT,NO_ADMISSION],
  decision_code:ENUM[SOURCE_ROWS,LINK_ROWS,PAD_ROW,NEW_ROW,
    REJECT_SCHEMA,REJECT_EVIDENCE,REJECT_SUPPORT,REJECT_DECLARATION,
    REJECT_DISPATCH,REJECT_NUISANCE,REJECT_POSTERIOR],
  declaration_faithful:BIT,public_posterior:VEC[0..2,BIT],
  admitted_rows:VEC[0..2,MemoryRow],
  cited_public_event_handles:VEC[0..16,HANDLE26]
}

PublicTraceEvent = ONEOF[PublicReadEvent,ChildCommittedActionEvent,
  MemoryAuthorizedActionEvent,ExperimentDispatchEvent,PublicObservation,
  PublicPairSelection,PublicDeclaration,CompilerDecision]
PublicExecutionTrace = OBJ{
  v:CONST[mcore.v5],public_pair_handle:HANDLE26,
  phase:ENUM[CHILD_FOUNDATION_ROUTE,CHILD_FOUNDATION_TERMINAL,
    CHILD_SOURCE,CHILD_ABLATION,CHILD_SUPPORT,CHILD_PAD,
    B,C_PROBE,C_LIVE,D],actor_input_sha256:HEX64,
  events:VEC[0..256,PublicTraceEvent],terminal_state_handle:HANDLE26,
  reads_used:U53,actions_used:U53,malformed_count:U53
}

RecognitionScorerInput = OBJ{
  v:CONST[mcore.v5],reader_prompt:BLOB,request:RecognitionRequest,
  candidate_row:MemoryRow
}
RecognitionScorerOutput = OBJ{
  v:CONST[mcore.v5],yes_hex64:HEX16,no_hex64:HEX16,
  aggregate_hex64:HEX16,input_sha256:HEX64
}
EndpointScoreInput = OBJ{
  v:CONST[mcore.v5],public_trace:PublicExecutionTrace,
  environment_handle:HANDLE26
}
EndpointScoreOutput = OBJ{
  v:CONST[mcore.v5],trace_valid:BIT,endpoint_success:BIT,
  failure_code:FailureCode
}

TrainingTensorReceipt = OBJ{
  v:CONST[mcore.v5],condition_handle:HANDLE26,example_handle:HANDLE26,
  input_ids:BLOB,attention_mask:BLOB,position_ids:BLOB,labels:BLOB,
  loss_mask:BLOB,allowed_diff_bitmap:BLOB,
  view_id:HANDLE26,visit_id:HANDLE26,deck_slot:U53,batch_index:U53,
  optimizer_step:U53,dropout_stream_indices:BLOB,renderer_sha256:HEX64
}
ControlReceipt = OBJ{
  v:CONST[mcore.v5],control_id:ENUM[S1_OFF_B,S1_OFF_C,
    INTERFACE_CANARY,NONHARM_PANEL,
    GOAL_CATALOG_NO_CARRIER,CATALOG_NO_GOAL_NO_CARRIER,
    FULL_GOAL_CUE_SWAP_B,CATALOG_PERMUTE_P0,CATALOG_PERMUTE_P1,
    CATALOG_PERMUTE_P2,CATALOG_PERMUTE_P3,B_LINK_CUT,
    B_LINK_PAYLOAD_SWAP,SOURCE_READ_SWAP_C,D_OLD_LINK_CUT,
    D_NEW_ROW_CUT,D_OLD_LINK_PAYLOAD_SWAP,D_NEW_ROW_PAYLOAD_SWAP,
    NO_SLEEP2,OLD_PLUS_PAD,TEXT_FULL,TEXT_ATOMS_READ4],
  applied:BIT,completed:BIT,expected_envelope:BIT,
  public_trace_sha256:HEX64,failure_code:FailureCode
}
FailureReceipt = OBJ{
  v:CONST[mcore.v5],scope:ENUM[GLOBAL_INVALID,ROOT_INVALID,
    VALID_ENDPOINT_FAILURE,NONE],failure_code:FailureCode,
  emitted_before_endpoint_open:BIT,evidence_bundle_sha256:HEX64
}
ProvenanceNode = OBJ{
  node_handle:HANDLE26,origin:ENUM[AUTHENTIC,DERIVED_CONTROL],
  object_sha256:HEX64,
  transform:ENUM[NONE,SOURCE_OUTCOME_REBIND,DREAM_LINK_REBIND,
    LINK_PAYLOAD_SWAP,NEW_PAYLOAD_SWAP],
  donor_event_handles:VEC[0..16,HANDLE26],
  derivation_receipt_handle:OPT[HANDLE26]
}
DerivationReceipt = OBJ{
  receipt_handle:HANDLE26,
  transform:ENUM[SOURCE_OUTCOME_REBIND,DREAM_LINK_REBIND,
    LINK_PAYLOAD_SWAP,NEW_PAYLOAD_SWAP],
  donor_event_handles:VEC[1..16,HANDLE26],
  output_object_sha256:HEX64,transform_parameters:BLOB
}
ProvenanceReceipt = OBJ{
  v:CONST[mcore.v5],nodes:VEC[1..256,ProvenanceNode],
  derivations:VEC[0..64,DerivationReceipt],
  root_sha256:HEX64
}
AuditEnvelope = OBJ{
  v:CONST[mcore.v5],package_manifest_sha256:HEX64,
  root_seed_commitment:HEX64,audit_episode_instance_handle:HANDLE26,
  public_pair_handle:HANDLE26,condition_handle:HANDLE26,
  hidden_bits:VEC[3,BIT],role_map:BLOB,environment_graph_sha256:HEX64,
  provenance_receipt:ProvenanceReceipt,donor_map:BLOB,derivation_map:BLOB,
  schedule_receipt:BLOB,device_receipt:BLOB,rng_receipt:BLOB,
  scorer_receipt:BLOB,tensor_receipts:VEC[0..1024,TrainingTensorReceipt],
  control_receipts:VEC[0..128,ControlReceipt],
  failure_receipt:FailureReceipt,public_trace_sha256:HEX64
}

RootEntropyEntry = OBJ{
  cohort:ENUM[TEXT,DEV,CONF],root_index:U53,call_ordinal:U53,
  root_seed:BLOB,root_seed_commitment:HEX64,
  entropy_host_sha256:HEX64,entropy_runtime_sha256:HEX64,
  success:CONST[1]
}
RootEntropyTranscript = OBJ{
  v:CONST[mcore.v5],entries:VEC[32,RootEntropyEntry],
  entropy_tool_sha256:HEX64
}
RootManifestEntry = OBJ{
  cohort:ENUM[TEXT,DEV,CONF],root_index:U53,
  root_seed_commitment:HEX64,root_nonce_handle:HANDLE26,
  materialized_root_sha256:HEX64
}
CohortManifest = OBJ{
  v:CONST[mcore.v5],cohort:ENUM[TEXT,DEV,CONF],
  entries:VEC[1..16,RootManifestEntry]
}
DeckRowRef = OBJ{
  deck_slot:U53,row_sha256:HEX64,example_handle:HANDLE26,
  tensor_receipt_sha256:HEX64
}
DeckManifest = OBJ{
  v:CONST[mcore.v5],stage:ENUM[S1,S2],
  condition:ENUM[FULL_OLD,SOURCE_DERANGED_OLD,DREAM_DERANGED_OLD,
    FULL_NEW_h0,FULL_NEW_h1,FULL_OLD_PLUS_PAD],
  rows:VEC[1..4096,DeckRowRef]
}
DeviceIntervalReceipt = OBJ{
  device_uuid:STRING,clock_kind:ENUM[MONOTONIC_RAW,PROVIDER_LEASE],
  clock_source_sha256:HEX64,device_allocation_ns:U64D,
  device_release_ns:U64D,image_sha256:HEX64,driver_sha256:HEX64,
  runtime_sha256:HEX64
}
FitAttemptReceipt = OBJ{
  v:CONST[mcore.v5],attempt_handle:HANDLE26,
  root_seed_commitment:HEX64,stage:ENUM[S1,S2],
  condition:ENUM[FULL_OLD,SOURCE_DERANGED_OLD,DREAM_DERANGED_OLD,
    FULL_NEW_h0,FULL_NEW_h1,FULL_OLD_PLUS_PAD],
  launch_ordinal:U53,status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT],
  device_interval:DeviceIntervalReceipt,deck_manifest_sha256:HEX64,
  output_artifact_sha256:OPT[HEX64],failure_code:FailureCode
}
ExecutionAttemptReceipt = OBJ{
  v:CONST[mcore.v5],attempt_handle:HANDLE26,
  kind:ENUM[TEXT_ACTOR,TEXT_READER,EVAL_ACTOR,EVAL_READER,
    WSTAR_QUALIFICATION,READER_QUALIFICATION],
  root_seed_commitment:OPT[HEX64],launch_ordinal:U53,
  status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT],
  device_interval:DeviceIntervalReceipt,
  output_artifact_sha256:OPT[HEX64],failure_code:FailureCode
}
RpcReceipt = OBJ{
  v:CONST[mcore.v5],request_sha256:HEX64,response_frame:BLOB,
  rpc_bytes:CONST[16384],logical_request_tick:U53,
  logical_release_tick:U53,inference_rng_family:ENUM[B_STANDARD,
    B_GOAL_CUE,C_PROBE_0,C_PROBE_1,C_PROBE_2,C_PROBE_3,C_LIVE,D,
    INTERFACE,NONHARM],
  token_draw_ledger:BLOB,failure_code:FailureCode
}
FailureScopeEntry = OBJ{
  failure_code:FailureCode,
  scope:ENUM[GLOBAL_INVALID,ROOT_INVALID,VALID_ENDPOINT_FAILURE,NONE]
}
FailureScopeTable = OBJ{
  v:CONST[mcore.v5],entries:VEC[33,FailureScopeEntry]
}
GoalPairByteCutReceipt = OBJ{
  v:CONST[mcore.v5],input_a_sha256:HEX64,input_b_sha256:HEX64,
  first_difference_offset:U53,first_difference_json_pointer:STRING,
  complete_allowed_difference_bitmap:BLOB,
  common_public_anchor_handles:VEC[0..4,HANDLE26],passed:BIT
}
PackageMember = OBJ{
  path:STRING,byte_length:U53,media_type:STRING,sha256:HEX64
}
PackageManifest = OBJ{
  v:CONST[mcore.v5],members:VEC[1..100000,PackageMember],
  merkle_root_sha256:HEX64
}
CheckerSubcheck = OBJ{
  name:STRING,passed:BIT,failure_code:FailureCode,evidence_sha256:HEX64
}
CheckerReceipt = OBJ{
  v:CONST[mcore.v5],package_manifest_sha256:HEX64,
  package_merkle_root_sha256:HEX64,materializer_sha256:HEX64,
  checker_sha256:HEX64,runtime_sha256:HEX64,
  subchecks:VEC[1..100000,CheckerSubcheck],overall_passed:BIT,
  failure_code:FailureCode
}
ResultBundleManifest = OBJ{
  v:CONST[mcore.v5],package_manifest_sha256:HEX64,
  members:VEC[1..100000,PackageMember],merkle_root_sha256:HEX64,
  fit_attempts:VEC[0..6,FitAttemptReceipt],
  execution_attempts:VEC[0..100000,ExecutionAttemptReceipt]
}
```

The deterministic translator rejects unresolved names and emits literal
Draft-2020-12 JSON Schema with `$defs`, `required` equal to every listed field,
and `additionalProperties:false`. The manifest-bound semantic constraint file
adds the following finite rules, each independently recomputed by the checker:

- child ActorEpisodeInput phases require `goal=null`, non-null `task_input`,
  null menu, zero legal READ types, and their displayed exact budgets; B/C/D
  require their matching goal, null task_input, the Section-6 query subset,
  and C alone requires PublicMenu;
- the two PublicMenu entries have distinct source actions L/R and four
  pairwise-distinct experiment actions, with the public menu hash recomputed;
- catalog query types and anchors are duplicate-free in canonical byte order;
- ATOM has one ordered action/no statistics; SEQUENCE has two ordered
  actions/no statistics; CHOICE_TABLE has no ordered actions and exactly two
  statistics with distinct actions, one common desired outcome, and counts in
  0..4; query type, mode, key, destination, and citation arities must equal
  the canonical-row table for that row class;
- an AuthenticEvidencePair requires its observation's action-event handle to
  equal its child action and a later tick; a DerivedControlEvidencePair
  requires an exact derivation receipt whose donor observation refers to its
  donor action, whose transform is SOURCE_OUTCOME_REBIND, and whose presented
  action differs only as presealed by the donor map;
- LINK evidence contains exactly four ordered trials for each of exactly two
  selected lanes; PAD contains one p_0 then-Q authentic pair; source evidence
  contains four L and four R pairs and exactly the T/O desired handles;
- CompilerInput SOURCE has only source evidence non-null; LINK only ablation
  evidence; PAD only pad evidence; NEW only declaration, dispatch, and outcome.
  `public_task_law` is the package's root-independent public C law and contains
  no b/z/h, role map, expected row, donor map, or condition byte;
- SOURCE decisions admit two CHOICE_TABLE rows; LINK two SEQUENCE rows; PAD
  one ATOM row; NEW zero or one ATOM row. Decision code, status, posterior,
  cited handles, and declaration flag have one canonical combination per
  compiler branch;
- PublicDeclaration hypotheses are `[0,1]`, its two prediction and row entries
  are indexed in that order, its chosen experiment is in the selected public
  family, and all cited event handles precede the declaration tick;
- every public observation refers to exactly one earlier action-event union
  member; child, memory-authorized, and dispatch authorizations are disjoint;
- every PublicReadEvent/RpcReceipt frame is exactly 16384 bytes, has the exact
  magic/length/JCS/pad split in Section 6.4, and releases at request tick+1;
- entropy entries contain exactly 32 seed bytes, ordinals 0..31, and cohort/
  root indexes TEXT 0..7, DEV 0..7, CONF 0..15 exactly once; cohort manifests
  have respectively 8, 8, and 16 matching entries;
- FailureScopeTable is a bijection over all 33 FailureCode literals with the
  mapping in Section 1.3; `NONE` iff scope NONE; success/checker subchecks use
  NONE, while non-success uses the presealed non-NONE code;
- FailureReceipt.emitted_before_endpoint_open is 1 exactly for GLOBAL_* or
  ROOT_* and 0 for NONE or VALID_*;
- EndpointScoreOutput is `(trace_valid=1,endpoint_success=1,NONE)` for success,
  `(1,0,VALID_*)` only for a completed scientific endpoint failure, and
  `(0,0,ROOT_*|GLOBAL_*)` otherwise; `(0,1)` is impossible;
- U64D parses as an unsigned integer at most 18446744073709551615; device
  release and allocation use one receipted clock and release is not earlier
  than allocation; every result-bundle fit
  attempt is a listed member or hash-bound object, and the sum in Section 10
  is recomputed over all and only these attempt receipts; and
- package/result member paths are unique normalized paths, sorted by raw path
  bytes, and their file/Merkle hashes are recomputed without either manifest
  hashing itself.

## Source lineage

- `research_notes/analysis/2026-09-12_m_core_v4_fresh_causal_mechanism_audit.md`;
- `research_notes/analysis/2026-09-12_m_core_v4_fresh_statistics_visibility_execution_audit.md`;
- `research_notes/analysis/2026-09-12_m_core_exact_two_cycle_design_v4.md`.
