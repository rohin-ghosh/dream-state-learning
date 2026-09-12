# M-core v6: closed crossed two-cycle relay contract

Date: 2026-09-12 UTC

Status: independent watcher design only. This zero-fit successor supersedes
`2026-09-12_m_core_exact_two_cycle_design_v5.md`. It changes no builder source,
coordination file, benchmark, child, model, tokenizer, adapter, checkpoint,
job, GPU state, resource, claim, release, or submission. The materialization
package and every receipt below are requirements, not existing evidence.

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
or R target. The earlier privileged-target construction is therefore absent.

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
manifests/TEXT.json
manifests/DEV.json
manifests/CONF.json
materializer source tree
independent checker source file
dependency lock
runtime_manifest.json
fixtures/manifest.json and canonical fixture payloads
```

Every manifest-listed JSON path has exactly one Section-12 root schema:

| path | closed root type |
|---|---|
| `protocol.json` | Protocol |
| `schema_catalog.json` | SchemaCatalog |
| `semantic_constraints.json` | SemanticConstraints |
| `root_entropy_transcript.json` | RootEntropyTranscript |
| `root_generator.json` | RootGeneratorSpec |
| `alias_pool.json` | AliasPool |
| `action_rosters.json` | ActionRosters |
| `candidate_rosters.json` | CandidateRosters |
| `availability_relations.json` | AvailabilityRelations |
| `transition_system.json` | TransitionSystem |
| `interface_canary.json` | InterfaceCanary |
| `nonharm_panel.json` | NonharmPanel |
| `rpc_machine.json` | RpcMachine |
| `control_registry.json` | ControlRegistry |
| `failure_scope_table.json` | FailureScopeTable |
| `order_tables.json` | OrderTables |
| `schedule_tables.json` | ScheduleTables |
| `allowed_difference_maps.json` | AllowedDifferenceMaps |
| `goal_pair_byte_cut.json` | GoalPairByteCutTable |
| `canonical_returns.json` | CanonicalReturns |
| `wstar_binding.json` | WriterBinding |
| `reader_binding.json` | ReaderBinding |
| `actor_binding.json` | ActorBinding |
| `manifests/TEXT.json` | CohortManifest |
| `manifests/DEV.json` | CohortManifest |
| `manifests/CONF.json` | CohortManifest |
| `runtime_manifest.json` | RuntimeManifest |
| `fixtures/manifest.json` | FixtureManifest |

`package_manifest.json` is PackageManifest. Non-JSON source, lock, runtime,
and fixture payloads are byte members validated through PackageMember and the
corresponding source/runtime/fixture digest entry; no untyped blob substitutes for
a listed JSON root. `schema_catalog.json` maps each literal path above to its
Draft-2020-12 schema ID, so missing, duplicate, or wrong-root bindings fail.

`package_manifest.json` lists every other immutable member with normalized
relative path, byte length, media type, and lowercase SHA-256. Unlisted files
are forbidden. Paths are NFC UTF-8 POSIX-relative paths: no leading slash,
backslash, empty component, `.`/`..` component, duplicate normalized path, or
symlink is legal. Entries are sorted by raw UTF-8 path bytes. For those sorted
entries define:

```text
leaf_i = SHA256(ASCII("MCORE-V6-LEAF\0") ||
                U32BE(path_len) || path_bytes ||
                U64BE(file_len) || file_sha256_bytes)
```

The Merkle tree pairs adjacent leaves as
`SHA256("MCORE-V6-NODE\0" || left || right)`; an odd final node is duplicated.
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
bytes use unpadded RFC-4648 base64url in a `BLOB` object that also carries raw byte
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
`VALID_*` code. An unregistered or ambiguous failure is `GLOBAL_UNKNOWN` and
therefore has GLOBAL_INVALID scope; no implementation may invent a new code.

## 2. Independent root entropy and complete generator

### 2.1 Independent-root sampling assumption

There is no single master seed. Before any child/model/outcome work, a
registered entropy tool makes one separate 32-byte OS-CSPRNG call per
prospective root and records call ordinal, raw seed commitment, host/runtime
digest, and success code in `root_entropy_transcript.json`. TEXT has 8, DEV 8,
and CONF 16 seeds. Its exact bytes and entropy-tool digest are package-bound
before any root is materialized.

The commitment is exactly:

```text
root_seed_commitment = SHA256(
  ASCII("MCORE-V6-ROOT-SEED\0") || U32BE(32) || root_seed)
```

Every root seed has byte length 32. A duplicate seed or commitment anywhere in
the 32-entry transcript is `GLOBAL_ENTROPY`; no seed is replaced.

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
  ASCII("MCORE-V6\0") || U32BE(len(UTF8(tag))) || UTF8(tag) ||
  concat(encoded_typed_part))

R(root_seed,domain,counter) =
  U256BE(H("rand",BYTES(root_seed),UTF8(domain),U64(counter)))
```

`draw(domain,n)` obtains `x` from `R` at the domain's current counter, advances
that counter by one **before** testing `x`, rejects
`x >= floor(2^256/n)*n`, and repeats at the advanced counter; otherwise it
returns `x mod n`. Every listed domain has an independent counter initialized
to zero. Fisher--Yates consumes descending-index draws.
No call may pass an untyped string, integer, path, condition, or object.

The complete domain roster is literal: `b`, `z`, `lane-pair`, `pair-ab`,
`u-D`, `dream-shift`, `sigma`, one `alias/<alias_class_id>` in the exact
AliasClass order, one `stratum/<stratum_id>` in exact EventStratum order,
`device-S1`, `device-S2`, `condition-S1`, `condition-S2`,
`candidate-rotation`, `order-B`, `order-C`, and `order-D`. Alias classes and
event strata are finite manifest arrays; their IDs cannot contain `/`, NUL,
or duplicate bytes. No runtime-created domain is legal.

### 2.3 Alias pool, collisions, and fixed root indexing

`alias_pool.json` enumerates unique canonical candidate bytes in lexicographic
byte order for each public handle/action class. W*/actor tokenization is stored
for every alias. Qualification requires fixed byte length within a class,
equal token count/position class for every role-swapped group, no reserved
prompt word, and no collision **within the pool or one materialized root**.
The pool is qualified before root seeds are mapped to semantic roles.

Alias-byte reuse across different roots is legal and intentional. Every actor,
reader, compiler, environment, and checker lookup is capability-scoped to one
root bundle; the private lookup identity is
`(root_seed_commitment,public_handle)`. Cross-root lookup is absent from the
RPC/API schemas and is a `GLOBAL_CAPABILITY` failure. Thus independent roots
may permute one finite pool without root rejection or package-wide allocation.

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
4. draw `draw("pair-ab",2)` for A/B assignment within the pair;
5. set `u_D=selected_pair[draw("u-D",2)]`;
6. shuffle the six remaining lanes under `stratum/decoy-lanes`; first three
   are left-decoys, last three right-decoys;
7. set `dream_shift=1+draw("dream-shift",7)` and set
   `pi(i)=(i+dream_shift) mod 8`;
8. draw the 32-slot base permutation `sigma` by Fisher--Yates under `sigma`;
9. independently shuffle every remaining EventStratum in manifest order under
   its literal `stratum/<stratum_id>` domain (`decoy-lanes` is not repeated);
10. draw S1 and S2 device indices under `device-S1` and `device-S2`;
11. draw independent S1 and S2 triplet permutation indexes under
    `condition-S1` and `condition-S2` in 0..5;
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
python -m organism_v6.m_core_v6.materialize \
  --package-manifest <package_manifest.json> \
  --cohort TEXT|DEV|CONF --out <empty-directory>

python research_loop/checks/check_m_core_v6.py \
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

Pair choice is a fourth authenticated child output type,
`ChildPairSelectionEvent`, not a materializer annotation. It is emitted by the
same pinned child process with `CHILD_COMMIT_SELECTION`, binds the complete
ActorEpisodeInput, child/model/decode binding, inference draw ledger, all 32
preceding ablation action/observation handles, the visible eight-pair roster,
and exactly two chosen handles. Its tick must follow all 32 observations.

Only after that event is sealed does the environment emit a
`SupportFixtureRevealEvent` containing a fresh public fixture handle and the
two selected pair handles. Its fixture handle, instructions, action handles,
and observation handles are byte-disjoint from the ablation fixture. The
child then commits eight support actions—joint/left/right/nuisance for each
selected member—and receives eight later observations. LINK input cites the
selection, reveal, and those eight pairs. A pre-selection or reused
ablation/support event is schema-invalid, not fresh support.

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

All compiler decisions are condition-blind functions of canonical input bytes.
Each invocation includes a root-local `CompilerTemplateSet` of all complete
alternative rows it may emit. Templates contain public aliases, keys,
destinations, action surfaces, row handles, and citation slots, but no b/z/h,
role, expected answer, condition, donor map, or endpoint. SOURCE receives 50
complete count-specific choice-table templates (25 L/R count pairs for each
of desired T and O); LINK receives one link template per selected member only
after the authenticated selection is sealed; PAD receives d_pad;
NEW receives both n0 and n1 templates before the public outcome. SOURCE's set
enumerates every legal 0..4-by-0..4 count realization for T and O; therefore
every alternative row is complete. The compiler may copy only one or more
whole listed templates and may fill no field. The checker rejects any output
byte not selected from the closed template set by the closed evidence.

The four phases are:

1. `SOURCE_ROW_COMPILATION`: verify exactly four authentic/derived-view L and
   four R pairs. For desired T and O, count matching outcomes and emit one
   `CHOICE_TABLE` row containing both `(action,count,total=4)` entries. Ties
   remain ties. Missing/extra events or a non-4 denominator rejects.
2. `LINK_ADMISSION`: verify the child-authenticated selection, later disjoint
   support reveal, and eight later support pairs; accept both and only both
   selected members when each has joint/left/right/nuisance=`1/0/0/0`. Never
   propose, rank, replace, or add.
3. `PAD_ROW_COMPILATION`: after authentic `P --p_0--> Q`, emit one
   gradient-bearing outcome-shaped `d_pad` under disconnected `[P,Q]`; no
   event before A1 can satisfy it.
4. `NEW_ROW_ADMISSION`: receive the original authentic SourceEvidenceView,
   actual source-choice MemoryAuthorizedActionEvent, complete PublicMenu,
   declaration, dispatch, and later outcome. Recompute the preferred family
   from the authentic source events, verify every handle/hash/tick linkage,
   enumerate the public posterior over h, and admit exactly the matching n_h
   template iff the chosen/dispatch family is preferred and the posterior is
   singleton. A nuisance-family dispatch returns NO_ADMISSION.

Each `CompilerInvocationEvent` has an event handle, exact CompilerInput hash,
and logical tick later than every cited prerequisite. Each
`CompilerDecision` has its own event handle, invocation handle/input hash, and
later tick. Trace-array position is never used as causality. Each compiler
receives only the phase-appropriate closed `CompilerInput`; b, z, h, expected
answer, environment graph, and audit origin are unavailable. `NO_ADMISSION`
never contains a replacement row.

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

CHILD_PAIR_SELECTION:
  surfaces 0..27 encode the 28 unordered visible lane pairs and emit one
  ChildPairSelectionEvent; surfaces 28..31 -> malformed failure
  1 authenticated decision, 0 world actions, 0 READ

CHILD_SUPPORT(i,trial):
  entered only after SupportFixtureRevealEvent; same four-trial transition
  under the freshly revealed disjoint support fixture;
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

`TEXT_ATOMS_READ4` uses the registered `B_ATOMS` input variant with the same
goal handle, start, target, route cue, public pair handle, actions, and
surfaces, but `kind=B_ATOMS` and `read_budget=4`; every other byte matches. Its
allowed-difference bitmap permits exactly those kind/budget bytes. It is not a
FULL input and never enters an ordinary B contrast.

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

The former `CATALOG_NO_GOAL_NO_CARRIER` diagnostic is deleted from the
protocol, control registry, RNG table, gates, results, and claim. B inputs
always carry a legal B goal. `GOAL_CATALOG_NO_CARRIER` remains the one legal
carrier-free goal-present control.

The D goal is identical across h:

```text
G_D={kind:D,start:U_uD^D,target:D,route_cue:null,reads:2,actions:3}
```

Public pair handle/input/decoder state are identical across h until the second
reader return.

### 4.3 DREAM evidence

All eight lanes have one joint, left, right, nuisance child trial:

```text
2 useful:    1,0,0,0
3 left-dec:  1,1,0,0
3 right-dec: 1,0,1,0
```

At A2 the child sees endpoint/type/count/length-matched pair handles and emits
exactly two. Those two useful members are the root's selected pair; 2+3+3=8
lanes. The entire public byte prefix is sealed before support, B/C/D goals,
theorem, compiler result, or hidden role. Fresh support admits both and only
the two selected `1/0/0/0` members. The deterministic public necessity rule is a 100%
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
   hypotheses h0/h1, READ=1, actions=2. Compiler-visible public prefix also
   seals AuthenticSourceEvidenceView and complete n0/n1 CompilerTemplateSet.
C1 READ SOURCE_INVERSE(X,T) -> CHOICE_TABLE or MISS/BLOCKED.
C2 SOURCE_CHOICE L/R cites the row and enters FAMILY_L/R.
C3 PublicDeclaration commits chosen E, predictions for h0/h1, and complete
   outcome-to-row map.
C4 ExperimentDispatchEvent cites source choice+public menu and chooses only a
   member of the selected family.
C5 clone the process/RNG snapshot after dispatch bytes.
C6 h world emits causally later public y.
C7 CompilerInvocationEvent binds the authentic source view, actual C2 source
   choice event, complete C0 PublicMenu, declaration, dispatch, outcome,
   public law, and the pre-outcome n0/n1 templates.
C8 NEW_ROW_ADMISSION recomputes authentic preferred family from those source
   events, validates every linkage, enumerates h={0,1}, and returns n_h iff
   the family is preferred and posterior singleton; nuisance returns
   NO_ADMISSION. CompilerDecision tick is later than C7 and every cited event.
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

This no-write FULL-mounted fork returns the authentic T CHOICE_TABLE with only
its two `matching_count` values swapped. The public row handle is deliberately
unchanged; query, row ordering, key, actions, desired outcome, totals,
citations, destinations, status, lengths, RPC envelope, and inference RNG
family are byte-identical. Intervention identity and the altered content hash
are audit-only. The observable allowed-difference bitmap permits exactly the
two one-digit count bytes plus their mechanically forced JCS/RPC digest and
pad descendants. The opposite source action becomes the unique 3/4 maximum.

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

These are six distinct closed request payloads, not one generic anchor vector.
The deterministic ActorEpisodeInput/state-to-request projection is:

```text
ROUTE:    (phase B, goal_handle, current S_B, goal.route_cue_handle)
ATOM:     (phase B, goal_handle, current U_i^B or B_B)
LINK:     (phase B or D, goal_handle, current U_i)
TERMINAL: (phase B, goal_handle, current C_B, goal.target_handle)
SOURCE:   (phase C_PROBE or C_LIVE, goal_handle, current X,
           goal.desired_source_outcome_handle)
NEW:      (phase D, goal_handle, current C_D, goal.target_handle)
```

Every request repeats the candidate-schema digest, call ordinal, and reads
remaining. No actor-chosen extra anchor is serializable. The checker derives
the request bytes independently from the stored episode input and public state
and rejects a mismatch before reader scoring.

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
ASCII("MCRPC6\0")                    7 bytes
U32BE(payload_length)                4 bytes
payload = JCS(MemoryReturn)+LF        payload_length bytes
pad = SHAKE256("MCRPC6-PAD\0" || query_fingerprint_bytes,
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

The `rpc_observable` section of manifest-listed
`allowed_difference_maps.json` is a bitmask over concatenated complete
actor-observable bytes for each matched pair. Hit-matched controls allow only
named row payload/handle positions; availability controls additionally allow
status/null-row/pad-derived positions. All other bytes, total lengths, release
ticks, message counts, and callback order must be identical after alpha
normalization. Fake-clock tests cover multiple subdeadline delays and overrun.

For `FULL_GOAL_CUE_SWAP_B`, a separate descendant mask starts with the single
`/goal/route_cue_handle` input field and closes mechanically over the typed
causal graph. It permits only the ROUTE request cue/fingerprint, resulting
route return, selected route action/observation/state, consequent LINK
request/return/actions/observations, their event hashes, and RPC pad bytes
derived from those changed payloads. It forbids goal handle/target, terminal
request/row/action, catalog, unrelated anchors, system/decode/RNG bytes,
message counts, ticks, or any non-descendant. The checker computes the closure;
a hand-expanded extra bit is `GLOBAL_SCHEMA`.

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
            every catalog order, and GOAL_CATALOG_NO_CARRIER
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

`NO_SLEEP2` mounts the root's valid FULL_OLD S1 carrier without any S2 write.
On the ordinary D input it READs the old link (FOUND), executes `b_uD,c_0`,
then READs NEW_SUCCESSOR and receives the charged fixed-size MISS because
FULL_OLD has no new row. It terminates after 2 reads/2 actions with
`VALID_READ_MISS`. Relative to FULL_NEW, its allowed-difference map permits
only carrier identity, NEW availability/return, and descendants of that MISS;
the old link, input, first return/actions/observations, RNG family, and budgets
are identical. It is inference-only and adds no fit.

Every fitted carrier runs the same inference-only 32-case interface canary
and 32-case generic non-memory panel from birth actor reset. Interface passes
only at 32/32 canonical typed READ/action traces with zero malformed,
unavailable, or uncited event. Non-harm passes only when the paired mean
generic endpoint difference `(carrier-birth)>=-0.05`; both use package-bound
common RNG families, tasks, scorer bytes, and the same 32 cases. These are
validity gates, not mechanism endpoints, and all their launched device time is
charged to evaluation cost.

`control_registry.json` contains one `ControlSpec` for every normative control,
not a prose wildcard. Each root-local instantiation binds mounted carrier,
one to 32 `ControlCaseSpec`s containing complete ActorEpisodeInputs and request
sequences, the availability/content mutation, allowed-difference-map ID, exact
ordered public event types and canonical handles, per-case read/action counts,
terminal state, `trace_valid`, endpoint bit, terminal FailureCode, and one
presealed aggregate rule. The exhaustive expected disposition is:

| controls | exact expected terminal disposition |
|---|---|
| S1_OFF_B, S1_OFF_C, GOAL_CATALOG_NO_CARRIER | first READ charged MISS; 0 actions; `VALID_READ_MISS` |
| INTERFACE_CANARY, NONHARM_PANEL | registered thresholds pass; `NONE` |
| FULL_GOAL_CUE_SWAP_B | redirected valid B success; `NONE` |
| CATALOG_PERMUTE_P0..P3 | ordinary task success invariant; `NONE` |
| B_LINK_CUT | route FOUND/action, link charged MISS; `VALID_CUT_ENDPOINT` |
| B_LINK_PAYLOAD_SWAP | route FOUND/action, wrong legal link/action; `VALID_SWAP_ENDPOINT` |
| SOURCE_READ_SWAP_C | count-swapped row, opposite source/family, nuisance outcome, NO_ADMISSION; `VALID_SWAP_ENDPOINT` |
| D_OLD_LINK_CUT | first READ charged MISS; `VALID_CUT_ENDPOINT` |
| D_NEW_ROW_CUT | old link FOUND/two actions, NEW charged MISS; `VALID_CUT_ENDPOINT` |
| D_OLD_LINK_PAYLOAD_SWAP | wrong legal link/action; `VALID_SWAP_ENDPOINT` |
| D_NEW_ROW_PAYLOAD_SWAP | old link/two actions, wrong legal n action; `VALID_SWAP_ENDPOINT` |
| NO_SLEEP2, OLD_PLUS_PAD | old link/two actions, NEW charged MISS; `VALID_READ_MISS` |
| TEXT_FULL, TEXT_ATOMS_READ4 | registered successful trace; `NONE` |

Any other event, count, terminal, or code is `ROOT_INTERVENTION_MISMATCH`, not
a valid zero. `G_R` quantifies exactly over the manifest-bound ControlSpec
array; removed or extra IDs are `GLOBAL_PROTOCOL_MUTATION`.

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
`GLOBAL_UNKNOWN` and stop the cohort without a test.

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

The presealed S1 eligibility Boolean is:

```text
Q_S1(r)=1 iff no GLOBAL/ROOT failure has fired;
             all three S1 fits completed with common nuisance/work receipts;
             G_S(r)=G_M(r)=G_U(r)=1;
             I_S(r)=I_M(r)=I_U(r)=1;
             FULL solved both ordinary B goals; and
             every S1-only ControlSpec, canary, non-harm, extraction,
             provenance, ACL, RPC, and reset receipt passed.
```

`Q_S1Receipt` binds every named input and is emitted before any S2 artifact is
opened. DEV always launches the D1 and D2 S1 triplets (6 fits). It launches
both D1/D2 S2 triplets (6 more fits) iff `Q_S1(D1)&Q_S1(D2)=1`; otherwise the
DEV program stops and every unrun downstream indicator is zero. After those
S2 triplets, define `Q_FULL_KILL=I_R(D1)&I_R(D2)`. D3..D8 launch iff
`Q_FULL_KILL=1`; each runs S1, and launches its S2 triplet iff its own
`Q_S1(r)=1`. No failed later root stops or replaces another. Require >=6/8
`I_R=1` to freeze mechanics.

CONF contains 16 fresh source-disjoint roots with no replacement, extension,
early-success stop, or rerun. Every root launches S1; root r launches S2 iff
`Q_S1(r)=1`. If false, its I_W and I_R are zero and no S2 attempt/cost receipt
is invented. `schedule_tables.json` contains this exact Boolean state machine;
no scheduler discretion or post-outcome futility rule exists.

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
bound:

```text
L(K)=0                         if K=0
L(K)=Beta^-1(.05;K,17-K)       if 1<=K<=16
```

Post-stop results are descriptive.

The exact-binomial reference is conditional on a registered assumption over
the **complete indicators**, not merely seed hashes: conditional on immutable
common package/model/runtime assets, every generated input, fit/actor/reader
draw, physical execution event, failure classification, and final indicator
for root r is a measurable function only of r's independent root seed and an
explicitly independent root-local execution-noise variable. Root-local noise
variables are mutually independent and independent of all root seeds.

An `IndicatorIsolationReceipt` proves the observable engineering half: sterile
root namespaces, no shared mutable cache/service/process, root-scoped leases
and RNG ledgers, no cross-root input, and no ambiguous disturbance. Any known
cross-root cause, uncertain boundary, node-wide health event, shared daemon, or
unreceipted execution input is presealed `GLOBAL_SHARED_STATE` or
`GLOBAL_UNKNOWN`, terminates the cohort, and produces no test—not a collection
of root zeros. The receipt cannot prove physical stochastic independence; it
records the assumption. If that assumption is not defensible before CONF, the
exact-binomial claim is withdrawn or replaced before execution. The mechanical
DREAM ceiling/chance results remain descriptive.

## 10. Fit counts and complete measured cost

Maximum M fit counts remain:

```text
3 S1/root + 3 S2/upstream survivor
two-root S1 kill 6; two-root complete kill 12
eight-root DEV <=48; confirmation <=96; combined <=144
```

These exclude writer/reader qualification and TEXT. Resource accounting never
sums only completed fits. Every device interval is half-open
`[allocation_ns,release_ns)` and carries lease ID, device UUID, and exclusive
ownership receipt. For each `(lease_id,device_uuid)`, sort all launched fit,
actor, reader, and qualification intervals and take their interval union.
Overlapping actor/reader reservations on one device are therefore counted once;
simultaneously occupied distinct devices each accrue device time.

```text
C_fit_launched_ns = measure(union of all launched fit-attempt intervals,
                            grouped by lease_id and device_uuid)
C_fit_launched_seconds = C_fit_launched_ns / 1000000000
```

Crashes, timeouts, aborts, and partial S1/S2 attempts are included. If a node
disappears, release is the provider/lease release timestamp, or the last
exclusive-allocation boundary only when independently receipted; ambiguity is
`GLOBAL_UNKNOWN`, terminates the cohort, and yields neither a scientific test
nor a cost total. Report completed/failed/aborted seconds by
deck class, device UUID, and image.

Separately report all launched TEXT/reader/actor/compiler device seconds,
CPU materialization/checking seconds, queue time, reset/serialization time,
and W*/reader qualification cost. Stage-0/TEXT/kill/futility stops are named
reasons actual work can be below maxima. No generic per-fit multiplier,
unmeasured bound, ideal packing, or wall-time promise is allowed.

The exact non-fit device totals use disjoint category projections of that same
union. If one physical interval serves two categories, charge it only to
`MIXED` and include it once in total:

```text
C_TEXT_device_seconds =
  measure(union of all launched TEXT actor/reader device intervals)/1e9
C_eval_device_seconds =
  measure(union of all launched DEV/CONF actor/reader device intervals)/1e9
C_qual_device_seconds =
  measure(union of all launched W*/reader-qualification device intervals)/1e9
C_device_total_seconds = measure(union of every validated device interval)/1e9
```

Compiler/materializer/checker CPU intervals use typed `CpuIntervalReceipt`s;
queue, reset, and serialization use typed non-compute duration receipts. They
are reported separately and never converted into device seconds. Every
aborted, failed, timed-out, and partial launch is included. `CostSummary`
reports interval-union nanoseconds by lease/device/category/status and proves
membership/non-overlap. Unknown ownership or a missing release boundary is
`GLOBAL_UNKNOWN`: it terminates the scientific cohort and cost report rather
than silently charging zero.

Result granularity is fixed. One `RootResultBundleManifest` exists for every
presealed root, including unscheduled TEXT extension roots and roots with zero
S2 attempts; an unscheduled root has zero attempts and an explicit skipped-cell
record. A root bundle permits at most six fit attempts. One
`CohortResultBundleManifest` for TEXT, DEV, or CONF binds the ordered root
bundles, stopping receipts, cohort statistics, all cohort-level
execution/CPU/duration receipts, and cohort CostSummary. `ProgramResultIndex`
binds the three cohort manifests and qualification bundle. Immutable package
paths and result paths occupy disjoint roots (`package/` versus `results/`),
and neither manifest lists itself.

The result schema roots are likewise one-to-one:

| result path | closed root type |
|---|---|
| `results/<cohort>/root-<index>/manifest.json` | RootResultBundleManifest |
| `results/<cohort>/manifest.json` | CohortResultBundleManifest |
| `results/qualification/manifest.json` | QualificationResultBundleManifest |
| `results/index.json` | ProgramResultIndex |

ScienceRootResult exposes every G/I/contrast/F/Q_S1/skipped-cell/failure field;
TextRootResult exposes its exact T receipt and contains no fit or component
statistic field;
ControlReceipt, OptimizationReceipt, PairwiseWorkReceipt, AclReceipt,
PrefixComparisonReceipt, BfsCertificate, FakeClockReceipt, ScorerReceipt,
InterfaceCanaryReceipt, NonharmReceipt, ReaderModelAcceptanceReceipt,
ExtractionReceipt, ResetReceipt, ComponentGateReceipt,
IndicatorIsolationReceipt, StoppingReceipt, and CostSummary expose every gate
input. Raw blobs may preserve logs, but no gate reads an untyped blob field.

The gate-to-receipt map is exhaustive:

| result/gate | required closed receipt |
|---|---|
| TEXT `T_r` | TextRootReceipt |
| `G_S,G_M,G_U,G_W,G_F,G_R` | six ordered ComponentGateReceipts |
| `I_S,I_M,I_U,I_W,I_R` and raw contrasts | ScienceRootResult |
| S1 eligibility | QS1Receipt |
| interface preservation | InterfaceCanaryReceipt |
| generic no-harm | NonharmReceipt |
| neural FOUND/MISS validity | ReaderModelAcceptanceReceipt + ScorerReceipt |
| row carriage/content | ExtractionReceipt |
| empty-context/cross-episode reset | ResetReceipt |
| common training nuisance/work | OptimizationReceipt + PairwiseWorkReceipt |
| common inference nuisance | InferenceRngReceipt + RpcReceipt |
| ACL/prefix/compiler/BFS/clock/control/provenance | their correspondingly named typed receipts |
| root isolation | IndicatorIsolationReceipt |
| schedule/fixed sequence | StoppingReceipt |
| exact p/CP result | ComponentStatistic |
| cost completeness/non-overlap | CostSummary and its typed interval receipts |

## 11. V5 blocker disposition

V6 makes these zero-fit repairs, without adding a trained condition:

- each compiler now has a closed phase-specific input and complete public,
  root-local alternative templates; NEW receives the authentic source view,
  actual authorized source choice, complete menu, declaration, dispatch, and
  post-dispatch outcome, while invocation and decision handles/hashes/ticks
  make the causal order checkable;
- the selected pair is a child-authenticated decision over a complete visible
  roster after all ablation evidence, and its separately revealed support
  fixture is event- and handle-disjoint from selection evidence;
- `SOURCE_READ_SWAP_C` is count-only at the actor interface: it retains the
  authentic row handle and every non-count byte, with only required hash/pad
  descendants admitted by the registered bitmap;
- recognition is a query-specific union, ordinary and ATOMS B inputs are both
  legal, and the FULL-mounted goal-cue intervention has a mechanically closed
  descendant mask;
- the illegal no-goal diagnostic is deleted; `NO_SLEEP2` and every remaining
  control have exact mounted carriers, availability, reads/actions, endpoint,
  trace, and failure code in the 21-entry registry;
- `Q_S1`, DEV's two-root S1 kill and full kill, confirmation's per-root skip,
  and TEXT's five schedule rows are deterministic receipt-level Booleans;
- every manifest-listed JSON member has one named closed root schema, and every
  gate reads a typed receipt rather than an opaque blob; entropy commitments,
  per-domain advancement/order, root-scoped alias reuse, result manifests, and
  collision/failure laws are closed;
- confirmatory exact-binomial validity now states the needed assumption over
  complete root indicators and independent root-local execution noise, with
  uncertain cross-root causes causing a global no-test; the Clopper--Pearson
  endpoint is explicitly zero for `K=0`;
- all launched device intervals are unioned by lease/device, including failed
  and partial work, while CPU and queue/reset/serialization intervals are
  disjoint typed ledgers; every presealed root has a root bundle and cohort
  bundles cannot overlap package or other result namespaces; and
- the selected-lane count is consistently eight: two selected useful lanes and
  six decoys, with each selected lane's evidence profile fixed to `1/0/0/0`.

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

Protocol = OBJ{
  v:CONST[mcore.v6],protocol_handle:HANDLE26,
  trained_conditions:VEC[6,ENUM[FULL_OLD,SOURCE_DERANGED_OLD,
    DREAM_DERANGED_OLD,FULL_NEW_h0,FULL_NEW_h1,FULL_OLD_PLUS_PAD]],
  component_order:CONST[[S,M,U,W,R]],confirmatory_n:CONST[16],
  rejection_cutoff:CONST[12],alpha_hex:HEX16,rpc_bytes:CONST[16384],
  logical_delta:CONST[1],deadline_ns:U64D
}
SchemaBinding = OBJ{
  schema_id:HANDLE26,root_type:STRING,draft_2020_12_schema:BLOB
}
SchemaCatalog = OBJ{
  v:CONST[mcore.v6],bindings:VEC[1..512,SchemaBinding]
}
SemanticConstraintSpec = OBJ{
  constraint_id:HANDLE26,input_paths:VEC[1..64,STRING],
  checker_rule_sha256:HEX64,failure_code:FailureCode
}
SemanticConstraints = OBJ{
  v:CONST[mcore.v6],constraints:VEC[1..1024,SemanticConstraintSpec]
}
DomainSpec = OBJ{
  domain_id:STRING,counter_initial:CONST[0],iteration_ordinal:U53
}
RootGeneratorSpec = OBJ{
  v:CONST[mcore.v6],seed_bytes:CONST[32],
  seed_commitment_domain:CONST[MCORE-V6-ROOT-SEED-NUL],
  typed_hash_domain:CONST[MCORE-V6-NUL],draw_algorithm:CONST[REJECT_U256],
  domains:VEC[1..1024,DomainSpec],draw_order_sha256:HEX64,
  alias_reuse_scope:CONST[ROOT_CAPABILITY],root_rejection:CONST[0]
}
AliasCandidate = OBJ{
  alias_handle:HANDLE26,surface:BLOB,token_ids:BLOB,
  byte_length:U53,token_count:U53,position_class:HANDLE26
}
AliasClass = OBJ{
  alias_class_id:STRING,candidates:VEC[32..4096,AliasCandidate]
}
AliasPool = OBJ{
  v:CONST[mcore.v6],classes:VEC[1..256,AliasClass],
  cross_root_reuse:CONST[1],lookup_scope:CONST[ROOT_CAPABILITY]
}
TransitionRow = OBJ{
  phase:ENUM[CHILD_FOUNDATION_ROUTE,CHILD_FOUNDATION_TERMINAL,
    CHILD_SOURCE,CHILD_ABLATION,CHILD_PAIR_SELECTION,CHILD_SUPPORT,
    CHILD_PAD,B,C_PROBE,C_LIVE,D],state_handle:HANDLE26,
  action_handle:HANDLE26,next_state_handle:HANDLE26,
  observation_handle:HANDLE26,terminal:BIT
}
TransitionSystem = OBJ{
  v:CONST[mcore.v6],rows:VEC[1..100000,TransitionRow]
}
ActionRosterEntry = OBJ{
  phase:ENUM[CHILD_FOUNDATION_ROUTE,CHILD_FOUNDATION_TERMINAL,
    CHILD_SOURCE,CHILD_ABLATION,CHILD_PAIR_SELECTION,CHILD_SUPPORT,
    CHILD_PAD,B,C_PROBE,C_LIVE,D],
  state_handle:HANDLE26,surfaces:VEC[32,ActionSurface]
}
ActionRosters = OBJ{
  v:CONST[mcore.v6],entries:VEC[1..100000,ActionRosterEntry]
}
CandidateRosterEntry = OBJ{
  query_type:ENUM[ROUTE_BY_CUE,ATOM_SUCCESSOR,LINK_SUCCESSOR,
    TERMINAL_TO_TARGET,SOURCE_INVERSE,NEW_SUCCESSOR],
  request_fingerprint_sha256:HEX64,candidate_rows:VEC[32,MemoryRow]
}
CandidateRosters = OBJ{
  v:CONST[mcore.v6],entries:VEC[1..100000,CandidateRosterEntry]
}
AvailabilityEntry = OBJ{
  carrier:ENUM[FULL_OLD,SOURCE_DERANGED_OLD,DREAM_DERANGED_OLD,
    ATOMS,S1_OFF,NO_CARRIER,FULL_NEW_h0,FULL_NEW_h1,OLD_PLUS_PAD,
    TEXT_FULL,TEXT_ATOMS],
  request_fingerprint_sha256:HEX64,available_row_sha256s:VEC[0..1,HEX64]
}
AvailabilityRelations = OBJ{
  v:CONST[mcore.v6],entries:VEC[1..100000,AvailabilityEntry]
}
InterfaceCanaryCase = OBJ{
  case_handle:HANDLE26,actor_input:ActorEpisodeInput,
  expected_trace_sha256:HEX64
}
InterfaceCanary = OBJ{
  v:CONST[mcore.v6],cases:VEC[32,InterfaceCanaryCase],required_pass:CONST[32]
}
NonharmCase = OBJ{
  case_handle:HANDLE26,actor_input:ActorEpisodeInput,score_rule_sha256:HEX64
}
NonharmPanel = OBJ{
  v:CONST[mcore.v6],cases:VEC[32,NonharmCase],adverse_bound_hex:HEX16
}
RpcMachine = OBJ{
  v:CONST[mcore.v6],magic:BLOB,rpc_bytes:CONST[16384],
  header_bytes:CONST[11],logical_delta:CONST[1],deadline_ns:U64D,
  padding_domain:CONST[MCRPC6-PAD-NUL],fake_clock_cases:VEC[3..64,U64D]
}
ControlMutation = OBJ{
  kind:ENUM[NONE,CARRIER_OFF,CUT,PAYLOAD_SWAP,COUNT_SWAP,CATALOG_PERMUTE],
  target_row_handle:OPT[HANDLE26],replacement_row:OPT[MemoryRow],
  permutation_ordinal:OPT[U53]
}
ExpectedTraceStep = OBJ{
  ordinal:U53,event_kind:ENUM[READ,ACTION,OBSERVATION,DECLARATION,
    DISPATCH,COMPILER_INVOCATION,COMPILER_DECISION,TERMINAL],
  canonical_object_sha256:HEX64
}
ControlCaseSpec = OBJ{
  case_handle:HANDLE26,actor_input:ActorEpisodeInput,
  expected_steps:VEC[1..64,ExpectedTraceStep],expected_reads:U53,
  expected_actions:U53,expected_terminal_state_handle:HANDLE26,
  expected_trace_valid:CONST[1],expected_endpoint_success:BIT,
  expected_failure_code:FailureCode
}
ControlSpec = OBJ{
  control_id:ENUM[S1_OFF_B,S1_OFF_C,INTERFACE_CANARY,NONHARM_PANEL,
    GOAL_CATALOG_NO_CARRIER,FULL_GOAL_CUE_SWAP_B,CATALOG_PERMUTE_P0,
    CATALOG_PERMUTE_P1,CATALOG_PERMUTE_P2,CATALOG_PERMUTE_P3,
    B_LINK_CUT,B_LINK_PAYLOAD_SWAP,SOURCE_READ_SWAP_C,D_OLD_LINK_CUT,
    D_NEW_ROW_CUT,D_OLD_LINK_PAYLOAD_SWAP,D_NEW_ROW_PAYLOAD_SWAP,
    NO_SLEEP2,OLD_PLUS_PAD,TEXT_FULL,TEXT_ATOMS_READ4],
  mounted_carrier:ENUM[BIRTH,FULL_OLD,SOURCE_DERANGED_OLD,
    DREAM_DERANGED_OLD,FULL_NEW_h0,FULL_NEW_h1,FULL_OLD_PLUS_PAD,
    TEXT_FULL,TEXT_ATOMS,NO_CARRIER],cases:VEC[1..32,ControlCaseSpec],
  mutation:ControlMutation,allowed_difference_map_handle:HANDLE26,
  aggregate_rule_sha256:HEX64
}
ControlRegistry = OBJ{
  v:CONST[mcore.v6],controls:VEC[21,ControlSpec]
}
CandidateOrder = OBJ{
  order_id:ENUM[P0,P1,P2,P3],candidate_ordinals:VEC[32,U53]
}
OrderTables = OBJ{
  v:CONST[mcore.v6],candidate_orders:VEC[4,CandidateOrder],
  s1_condition_orders:VEC[6,VEC[3,U53]],
  s2_condition_orders:VEC[6,VEC[3,U53]],
  b_control_ids:VEC[1..64,HANDLE26],c_control_ids:VEC[1..64,HANDLE26],
  d_control_ids:VEC[1..64,HANDLE26]
}
ScheduleRule = OBJ{
  rule_id:ENUM[DEV_S1_KILL,DEV_FULL_KILL,DEV_ROOT_S2,CONF_ROOT_S2],
  predicate:ENUM[QS1_D1_AND_D2,IR_D1_AND_D2,ROOT_QS1],
  launch_cells:VEC[0..18,ENUM[S1_TRIPLET,S2_TRIPLET,DEV_D3_D8]],
  false_effect:ENUM[STOP_DEV,ZERO_ROOT_W_R,NO_EFFECT]
}
TextScheduleRow = OBJ{
  initial_passes:ENUM[0,1,2,3,4],
  decision:ENUM[STOP,EXTEND_T5_T8,PROCEED],
  extended_total_required:ENUM[0,6]
}
EligibleDevice = OBJ{
  device_handle:HANDLE26,device_uuid:STRING,image_sha256:HEX64,
  driver_sha256:HEX64,runtime_sha256:HEX64
}
ScheduleTables = OBJ{
  v:CONST[mcore.v6],eligible_devices:VEC[1..1024,EligibleDevice],
  text_rows:VEC[5,TextScheduleRow],rules:VEC[4,ScheduleRule]
}
AllowedDifferenceMap = OBJ{
  map_handle:HANDLE26,baseline_sha256:HEX64,intervention_sha256:HEX64,
  complete_bitmap:BLOB,causal_parent_map_handle:OPT[HANDLE26]
}
AllowedDifferenceMaps = OBJ{
  v:CONST[mcore.v6],maps:VEC[1..100000,AllowedDifferenceMap]
}
CanonicalReturnEntry = OBJ{
  carrier:STRING,request_fingerprint_sha256:HEX64,
  status:ENUM[FOUND,MISS],row_sha256:OPT[HEX64]
}
CanonicalReturns = OBJ{
  v:CONST[mcore.v6],entries:VEC[1..100000,CanonicalReturnEntry]
}
WriterBinding = OBJ{
  v:CONST[mcore.v6],writer_id:HANDLE26,writer_model_sha256:HEX64,
  qualification_receipt_sha256:HEX64,recipe_sha256:HEX64,
  rank:U53,learning_rate_hex:HEX16,steps:U53,
  loss_mask_sha256:HEX64,preservation_mix_sha256:HEX64
}
ReaderBinding = OBJ{
  v:CONST[mcore.v6],reader_id:HANDLE26,model_sha256:HEX64,
  prompt:BLOB,aggregate_rule_sha256:HEX64,threshold_hex:HEX16,
  margin_hex:HEX16,candidate_order_invariance_sha256:HEX64,
  rpc_machine_sha256:HEX64,qualification_receipt_sha256:HEX64
}
ActorBinding = OBJ{
  v:CONST[mcore.v6],actor_id:HANDLE26,model_sha256:HEX64,
  tokenizer_sha256:HEX64,chat_template_sha256:HEX64,renderer_sha256:HEX64,
  engine_sha256:HEX64,runtime_image_sha256:HEX64,
  decode_config:DecodeConfig,inference_rng_rule_sha256:HEX64
}
FixtureDigest = OBJ{
  fixture_handle:HANDLE26,path:STRING,byte_length:U53,sha256:HEX64
}
FixtureManifest = OBJ{
  v:CONST[mcore.v6],fixtures:VEC[1..100000,FixtureDigest]
}
RuntimeManifest = OBJ{
  v:CONST[mcore.v6],cpu_image_sha256:HEX64,os_sha256:HEX64,
  interpreter_sha256:HEX64,dependency_lock_sha256:HEX64,
  materializer_source_tree_sha256:HEX64,checker_source_sha256:HEX64,
  entropy_tool_sha256:HEX64
}

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
BAtomsGoal = OBJ{
  kind:CONST[B_ATOMS],goal_handle:HANDLE26,start_handle:HANDLE26,
  target_handle:HANDLE26,route_cue_handle:HANDLE26,
  desired_source_outcome_handle:CONST[null],read_budget:CONST[4],
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
PublicGoal = ONEOF[BGoal,BAtomsGoal,CProbeGoal,CLiveGoal,DGoal]

PublicMenuEntry = OBJ{
  source_action_handle:HANDLE26,
  experiment_action_handles:VEC[2,HANDLE26]
}
PublicMenu = OBJ{entries:VEC[2,PublicMenuEntry],menu_sha256:HEX64}

ChildFoundationTask = OBJ{
  kind:ENUM[FOUNDATION_ROUTE,FOUNDATION_TERMINAL],
  public_instruction_handle:HANDLE26,fixture_handle:HANDLE26,
  start_state_handle:HANDLE26,instruction:BLOB
}
ChildSourceTask = OBJ{
  kind:CONST[SOURCE_EVIDENCE],public_instruction_handle:HANDLE26,
  fixture_handle:HANDLE26,desired_outcome_handles:VEC[2,HANDLE26],
  trial_handles:VEC[8,HANDLE26],instruction:BLOB
}
ChildAblationTask = OBJ{
  kind:CONST[ABLATION_EVIDENCE],public_instruction_handle:HANDLE26,
  ablation_fixture_handle:HANDLE26,lane_handles:VEC[8,HANDLE26],
  trial_kind_order:CONST[[JOINT,LEFT,RIGHT,NUISANCE]],instruction:BLOB
}
ChildPairSelectionTask = OBJ{
  kind:CONST[PAIR_SELECTION],public_instruction_handle:HANDLE26,
  ablation_fixture_handle:HANDLE26,
  completed_evidence_pairs:VEC[32,AuthenticEvidencePair],
  visible_lane_handles:VEC[8,HANDLE26],
  visible_pair_handles:VEC[28,HANDLE26],instruction:BLOB
}
ChildSupportTask = OBJ{
  kind:CONST[SUPPORT_EVIDENCE],public_instruction_handle:HANDLE26,
  support_reveal:SupportFixtureRevealEvent,
  trial_kind_order:CONST[[JOINT,LEFT,RIGHT,NUISANCE]]
}
ChildPadTask = OBJ{
  kind:CONST[PAD_EVIDENCE],public_instruction_handle:HANDLE26,
  fixture_handle:HANDLE26,start_state_handle:HANDLE26,instruction:BLOB
}
PublicChildTask = ONEOF[ChildFoundationTask,ChildSourceTask,
  ChildAblationTask,ChildPairSelectionTask,ChildSupportTask,ChildPadTask]

MemoryCatalog = OBJ{
  v:CONST[mcore.v6],legal_query_types:VEC[0..6,ENUM[
    ROUTE_BY_CUE,ATOM_SUCCESSOR,LINK_SUCCESSOR,TERMINAL_TO_TARGET,
    SOURCE_INVERSE,NEW_SUCCESSOR]],
  public_anchor_handles:VEC[0..4,HANDLE26],
  candidate_schema_sha256:HEX64,reads_remaining:U53
}

ActorEpisodeInput = OBJ{
  v:CONST[mcore.v6],public_pair_handle:HANDLE26,
  phase:ENUM[CHILD_FOUNDATION_ROUTE,CHILD_FOUNDATION_TERMINAL,
    CHILD_SOURCE,CHILD_ABLATION,CHILD_PAIR_SELECTION,CHILD_SUPPORT,CHILD_PAD,
    B,C_PROBE,C_LIVE,D],
  actor_model_sha256:HEX64,system_prompt:BLOB,
  goal:OPT[PublicGoal],current_state_handle:HANDLE26,
  legal_action_surfaces:VEC[32,ActionSurface],
  public_menu:OPT[PublicMenu],task_input:OPT[PublicChildTask],
  memory_catalog:MemoryCatalog,decode_config:DecodeConfig
}

RouteRequest = OBJ{
  v:CONST[mcore.v6],phase:CONST[B],query_type:CONST[ROUTE_BY_CUE],
  public_state_handle:HANDLE26,public_goal_handle:HANDLE26,
  route_cue_handle:HANDLE26,candidate_schema_sha256:HEX64,
  call_ordinal:U53,reads_remaining:U53
}
AtomRequest = OBJ{
  v:CONST[mcore.v6],phase:CONST[B],query_type:CONST[ATOM_SUCCESSOR],
  public_state_handle:HANDLE26,public_goal_handle:HANDLE26,
  candidate_schema_sha256:HEX64,call_ordinal:U53,reads_remaining:U53
}
LinkRequest = OBJ{
  v:CONST[mcore.v6],phase:ENUM[B,D],query_type:CONST[LINK_SUCCESSOR],
  public_state_handle:HANDLE26,public_goal_handle:HANDLE26,
  candidate_schema_sha256:HEX64,call_ordinal:U53,reads_remaining:U53
}
TerminalRequest = OBJ{
  v:CONST[mcore.v6],phase:CONST[B],query_type:CONST[TERMINAL_TO_TARGET],
  public_state_handle:HANDLE26,public_goal_handle:HANDLE26,
  target_handle:HANDLE26,candidate_schema_sha256:HEX64,
  call_ordinal:U53,reads_remaining:U53
}
SourceRequest = OBJ{
  v:CONST[mcore.v6],phase:ENUM[C_PROBE,C_LIVE],
  query_type:CONST[SOURCE_INVERSE],public_state_handle:HANDLE26,
  public_goal_handle:HANDLE26,desired_outcome_handle:HANDLE26,
  candidate_schema_sha256:HEX64,call_ordinal:U53,reads_remaining:U53
}
NewRequest = OBJ{
  v:CONST[mcore.v6],phase:CONST[D],query_type:CONST[NEW_SUCCESSOR],
  public_state_handle:HANDLE26,public_goal_handle:HANDLE26,
  target_handle:HANDLE26,candidate_schema_sha256:HEX64,
  call_ordinal:U53,reads_remaining:U53
}
RecognitionRequest = ONEOF[RouteRequest,AtomRequest,LinkRequest,
  TerminalRequest,SourceRequest,NewRequest]

SourceStatistic = OBJ{
  action_handle:HANDLE26,desired_outcome_handle:HANDLE26,
  matching_count:U53,total_count:CONST[4]
}
MemoryRow = OBJ{
  v:CONST[mcore.v6],row_handle:HANDLE26,
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
  v:CONST[mcore.v6],status:ENUM[FOUND,MISS,BLOCKED],
  query_fingerprint_sha256:HEX64,row:OPT[MemoryRow],
  reads_remaining:U53
}
PublicReadEvent = OBJ{
  v:CONST[mcore.v6],request:RecognitionRequest,response_rpc_frame:BLOB,
  logical_request_tick:U53,logical_release_tick:U53
}

ChildCommittedActionEvent = OBJ{
  v:CONST[mcore.v6],event_handle:HANDLE26,
  authorization:CONST[CHILD_COMMIT],public_instruction_handle:HANDLE26,
  action_handle:HANDLE26,pre_state_handle:HANDLE26,logical_tick:U53
}
MemoryAuthorizedActionEvent = OBJ{
  v:CONST[mcore.v6],event_handle:HANDLE26,
  authorization:CONST[MEMORY_ROW],row_handle:HANDLE26,
  action_handle:HANDLE26,pre_state_handle:HANDLE26,logical_tick:U53
}
ExperimentDispatchEvent = OBJ{
  v:CONST[mcore.v6],event_handle:HANDLE26,
  authorization:CONST[PUBLIC_DISPATCH],source_choice_event_handle:HANDLE26,
  public_menu_sha256:HEX64,experiment_action_handle:HANDLE26,
  pre_state_handle:HANDLE26,logical_tick:U53
}
PublicObservation = OBJ{
  v:CONST[mcore.v6],event_handle:HANDLE26,
  action_event_handle:HANDLE26,observation_handle:HANDLE26,
  outcome_surface:BLOB,post_state_handle:HANDLE26,logical_tick:U53
}
ChildPairSelectionEvent = OBJ{
  v:CONST[mcore.v6],event_handle:HANDLE26,
  authorization:CONST[CHILD_COMMIT_SELECTION],
  actor_input_sha256:HEX64,actor_binding_sha256:HEX64,
  decode_config_sha256:HEX64,draw_ledger_sha256:HEX64,
  ablation_action_event_handles:VEC[32,HANDLE26],
  ablation_observation_event_handles:VEC[32,HANDLE26],
  visible_pair_roster:VEC[8,HANDLE26],
  selected_pair_handles:VEC[2,HANDLE26],logical_tick:U53
}
SupportFixtureRevealEvent = OBJ{
  v:CONST[mcore.v6],event_handle:HANDLE26,
  selection_event_handle:HANDLE26,support_fixture_handle:HANDLE26,
  disjoint_from_ablation_fixture_handle:HANDLE26,
  selected_pair_handles:VEC[2,HANDLE26],instruction:BLOB,
  support_action_handles:VEC[8,HANDLE26],logical_tick:U53
}
PublicDeclaration = OBJ{
  v:CONST[mcore.v6],event_handle:HANDLE26,
  cited_source_row_handle:HANDLE26,
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
  v:CONST[mcore.v6],pairs:VEC[8,EvidencePair],
  desired_outcome_handles:VEC[2,HANDLE26],
  visible_citation_bundle_handles:VEC[2,HANDLE26]
}
AuthenticSourceEvidenceView = OBJ{
  v:CONST[mcore.v6],pairs:VEC[8,AuthenticEvidencePair],
  desired_outcome_handles:VEC[2,HANDLE26],
  visible_citation_bundle_handles:VEC[2,HANDLE26]
}
AblationEvidenceView = OBJ{
  v:CONST[mcore.v6],selection:ChildPairSelectionEvent,
  support_reveal:SupportFixtureRevealEvent,
  evidence_pairs:VEC[8,AuthenticEvidencePair]
}
PadEvidenceView = OBJ{
  v:CONST[mcore.v6],pair:AuthenticEvidencePair,
  reserved_row_handle:HANDLE26
}
CompilerRowTemplate = OBJ{
  template_handle:HANDLE26,
  compiler_phase:ENUM[SOURCE_ROW_COMPILATION,LINK_ADMISSION,
    PAD_ROW_COMPILATION,NEW_ROW_ADMISSION],
  row:MemoryRow,evidence_fill_fields:CONST[[]]
}
CompilerTemplateSet = OBJ{
  v:CONST[mcore.v6],template_set_handle:HANDLE26,
  compiler_phase:ENUM[SOURCE_ROW_COMPILATION,LINK_ADMISSION,
    PAD_ROW_COMPILATION,NEW_ROW_ADMISSION],
  revealed_logical_tick:U53,templates:VEC[1..64,CompilerRowTemplate],
  public_prefix_sha256:HEX64
}
PublicTaskLaw = OBJ{
  v:CONST[mcore.v6],source_actions_per_family:CONST[2],
  source_trials_per_action:CONST[4],source_rows_emitted:CONST[2],
  link_selected_count:CONST[2],
  link_trial_order:CONST[[JOINT,LEFT,RIGHT,NUISANCE]],
  link_required_profile:CONST[[1,0,0,0]],pad_pairs_required:CONST[1],
  new_hypothesis_order:CONST[[0,1]],
  new_admission_rule:CONST[SINGLETON_AUTHENTIC_SOURCE_POSTERIOR],
  transition_system_sha256:HEX64,compiler_algorithm_sha256:HEX64
}
SourceCompilerInput = OBJ{
  v:CONST[mcore.v6],compiler_phase:CONST[SOURCE_ROW_COMPILATION],
  source_evidence:SourceEvidenceView,templates:CompilerTemplateSet,
  public_task_law:PublicTaskLaw
}
LinkCompilerInput = OBJ{
  v:CONST[mcore.v6],compiler_phase:CONST[LINK_ADMISSION],
  ablation_evidence:AblationEvidenceView,templates:CompilerTemplateSet,
  public_task_law:PublicTaskLaw
}
PadCompilerInput = OBJ{
  v:CONST[mcore.v6],compiler_phase:CONST[PAD_ROW_COMPILATION],
  pad_evidence:PadEvidenceView,templates:CompilerTemplateSet,
  public_task_law:PublicTaskLaw
}
NewCompilerInput = OBJ{
  v:CONST[mcore.v6],compiler_phase:CONST[NEW_ROW_ADMISSION],
  authentic_source_evidence:AuthenticSourceEvidenceView,
  source_choice_event:MemoryAuthorizedActionEvent,public_menu:PublicMenu,
  declaration:PublicDeclaration,dispatch:ExperimentDispatchEvent,
  public_outcome:PublicObservation,templates:CompilerTemplateSet,
  public_task_law:PublicTaskLaw
}
CompilerInput = ONEOF[SourceCompilerInput,LinkCompilerInput,
  PadCompilerInput,NewCompilerInput]
CompilerInvocationEvent = OBJ{
  v:CONST[mcore.v6],event_handle:HANDLE26,compiler_input:CompilerInput,
  compiler_input_sha256:HEX64,cited_prerequisite_event_handles:VEC[1..64,HANDLE26],
  logical_tick:U53
}
CompilerDecision = OBJ{
  v:CONST[mcore.v6],event_handle:HANDLE26,
  invocation_event_handle:HANDLE26,compiler_input_sha256:HEX64,
  status:ENUM[ADMIT,NO_ADMISSION],
  decision_code:ENUM[SOURCE_ROWS,LINK_ROWS,PAD_ROW,NEW_ROW,
    REJECT_SCHEMA,REJECT_EVIDENCE,REJECT_SUPPORT,REJECT_DECLARATION,
    REJECT_DISPATCH,REJECT_NUISANCE,REJECT_POSTERIOR],
  declaration_faithful:BIT,public_posterior:VEC[0..2,BIT],
  admitted_rows:VEC[0..2,MemoryRow],
  cited_public_event_handles:VEC[0..64,HANDLE26],logical_tick:U53
}

PublicTraceEvent = ONEOF[PublicReadEvent,ChildCommittedActionEvent,
  MemoryAuthorizedActionEvent,ExperimentDispatchEvent,PublicObservation,
  ChildPairSelectionEvent,SupportFixtureRevealEvent,PublicDeclaration,
  CompilerInvocationEvent,CompilerDecision]
PublicExecutionTrace = OBJ{
  v:CONST[mcore.v6],public_pair_handle:HANDLE26,
  phase:ENUM[CHILD_FOUNDATION_ROUTE,CHILD_FOUNDATION_TERMINAL,
    CHILD_SOURCE,CHILD_ABLATION,CHILD_PAIR_SELECTION,CHILD_SUPPORT,CHILD_PAD,
    B,C_PROBE,C_LIVE,D],actor_input_sha256:HEX64,
  events:VEC[0..256,PublicTraceEvent],terminal_state_handle:HANDLE26,
  reads_used:U53,actions_used:U53,malformed_count:U53
}

RecognitionScorerInput = OBJ{
  v:CONST[mcore.v6],reader_prompt:BLOB,request:RecognitionRequest,
  candidate_row:MemoryRow
}
RecognitionScorerOutput = OBJ{
  v:CONST[mcore.v6],yes_hex64:HEX16,no_hex64:HEX16,
  aggregate_hex64:HEX16,input_sha256:HEX64
}
EndpointScoreInput = OBJ{
  v:CONST[mcore.v6],public_trace:PublicExecutionTrace,
  environment_handle:HANDLE26
}
EndpointScoreOutput = OBJ{
  v:CONST[mcore.v6],trace_valid:BIT,endpoint_success:BIT,
  failure_code:FailureCode
}

TrainingTensorReceipt = OBJ{
  v:CONST[mcore.v6],condition_handle:HANDLE26,example_handle:HANDLE26,
  input_ids:BLOB,attention_mask:BLOB,position_ids:BLOB,labels:BLOB,
  loss_mask:BLOB,allowed_diff_bitmap:BLOB,
  view_id:HANDLE26,visit_id:HANDLE26,deck_slot:U53,batch_index:U53,
  optimizer_step:U53,dropout_stream_indices:BLOB,renderer_sha256:HEX64
}
TrainingRngStream = OBJ{
  stream_id:ENUM[SLOT,BATCH,DROPOUT,DATA_WORKER,OPTIMIZER],
  initial_counter:CONST[0],final_counter:U53,draw_ledger_sha256:HEX64
}
OptimizationReceipt = OBJ{
  v:CONST[mcore.v6],attempt_handle:HANDLE26,
  initial_checkpoint_sha256:HEX64,optimizer_name:STRING,
  optimizer_initial_state_sha256:HEX64,schedule_sha256:HEX64,
  deterministic_kernel_flags_sha256:HEX64,deck_manifest_sha256:HEX64,
  rng_streams:VEC[5,TrainingRngStream],batch_count:U53,
  forward_calls:U53,backward_calls:U53,update_count:U53,
  supervised_tokens:U53,total_tokens:U53,
  device_health_before_sha256:HEX64,device_health_after_sha256:HEX64
}
PairwiseWorkReceipt = OBJ{
  v:CONST[mcore.v6],stage:ENUM[S1,S2],
  attempt_handles:VEC[3,HANDLE26],common_device_uuid:STRING,
  initialization_equal:CONST[1],slot_batch_step_equal:CONST[1],
  masks_shapes_work_equal:CONST[1],rng_counters_equal:CONST[1],
  kernel_flags_equal:CONST[1],health_envelope_equal:CONST[1],
  tensor_pair_receipt_sha256s:VEC[3,HEX64]
}
InferenceDrawEntry = OBJ{
  token_ordinal:U53,draw_sha256:HEX64
}
InferenceRngReceipt = OBJ{
  v:CONST[mcore.v6],family_id:ENUM[B_STANDARD,B_GOAL_CUE,
    C_PROBE_0,C_PROBE_1,C_PROBE_2,C_PROBE_3,C_LIVE,D,
    INTERFACE,NONHARM],counter_initial:CONST[0],
  draws:VEC[0..100000,InferenceDrawEntry],ledger_sha256:HEX64
}
ScorerCandidateReceipt = OBJ{
  candidate_ordinal:U53,input_sha256:HEX64,output:RecognitionScorerOutput
}
ScorerReceipt = OBJ{
  v:CONST[mcore.v6],request_sha256:HEX64,
  candidates:VEC[32,ScorerCandidateReceipt],chosen_status:ENUM[FOUND,MISS],
  chosen_row_sha256:OPT[HEX64],threshold_hex:HEX16,margin_hex:HEX16
}
ScheduleReceipt = OBJ{
  v:CONST[mcore.v6],root_seed_commitment:HEX64,s1_device_handle:HANDLE26,
  s2_device_handle:HANDLE26,s1_order:VEC[3,HANDLE26],
  s2_order:VEC[3,HANDLE26],candidate_rotation:U53,
  b_control_order:VEC[1..64,HANDLE26],c_control_order:VEC[1..64,HANDLE26],
  d_control_order:VEC[1..64,HANDLE26]
}
AclCheck = OBJ{
  capability:ENUM[ACTOR,READER,COMPILER,ENDPOINT_SCORER,AUDIT],
  object_type:STRING,access:ENUM[ALLOW,DENY],passed:CONST[1]
}
AclReceipt = OBJ{
  v:CONST[mcore.v6],checks:VEC[1..100000,AclCheck],
  namespace_isolation_passed:CONST[1]
}
PrefixComparisonReceipt = OBJ{
  v:CONST[mcore.v6],left_sha256:HEX64,right_sha256:HEX64,
  first_difference_offset:U53,allowed_difference_map_handle:HANDLE26,
  exact_match_outside_bitmap:CONST[1]
}
BfsCertificate = OBJ{
  v:CONST[mcore.v6],transition_system_sha256:HEX64,
  availability_sha256:HEX64,policy_count:U64D,
  full_min_reads:CONST[3],atoms_min_reads:CONST[4],
  full_new_min_reads:CONST[2],all_named_cuts_unreachable:CONST[1],
  witness_sha256:HEX64
}
FakeClockCaseReceipt = OBJ{
  delay_ns:U64D,expected_kind:ENUM[RELEASE,OVERRUN],
  observed_kind:ENUM[RELEASE,OVERRUN],public_continuation_count:U53,
  passed:CONST[1]
}
FakeClockReceipt = OBJ{
  v:CONST[mcore.v6],cases:VEC[3..64,FakeClockCaseReceipt]
}
CompilerPrefixReceipt = OBJ{
  v:CONST[mcore.v6],left_input_sha256:HEX64,right_input_sha256:HEX64,
  first_outcome_dependent_offset:U53,
  prefix_identical:CONST[1],allowed_difference_map_handle:HANDLE26
}
ControlCaseReceipt = OBJ{
  case_handle:HANDLE26,actor_input_sha256:HEX64,
  expected_trace_sha256:HEX64,observed_trace_sha256:HEX64,
  reads_used:U53,actions_used:U53,trace_valid:BIT,
  endpoint_success:BIT,failure_code:FailureCode,passed:BIT
}
ControlReceipt = OBJ{
  v:CONST[mcore.v6],control_id:ENUM[S1_OFF_B,S1_OFF_C,
    INTERFACE_CANARY,NONHARM_PANEL,
    GOAL_CATALOG_NO_CARRIER,
    FULL_GOAL_CUE_SWAP_B,CATALOG_PERMUTE_P0,CATALOG_PERMUTE_P1,
    CATALOG_PERMUTE_P2,CATALOG_PERMUTE_P3,B_LINK_CUT,
    B_LINK_PAYLOAD_SWAP,SOURCE_READ_SWAP_C,D_OLD_LINK_CUT,
    D_NEW_ROW_CUT,D_OLD_LINK_PAYLOAD_SWAP,D_NEW_ROW_PAYLOAD_SWAP,
    NO_SLEEP2,OLD_PLUS_PAD,TEXT_FULL,TEXT_ATOMS_READ4],
  control_spec_sha256:HEX64,applied:BIT,completed:BIT,
  cases:VEC[1..32,ControlCaseReceipt],aggregate_passed:BIT,
  failure_code:FailureCode
}
InterfaceCanaryCaseReceipt = OBJ{
  case_handle:HANDLE26,actor_input_sha256:HEX64,
  expected_trace_sha256:HEX64,observed_trace_sha256:HEX64,
  malformed_count:U53,unavailable_found_count:U53,
  uncited_event_count:U53,passed:BIT
}
InterfaceCanaryReceipt = OBJ{
  v:CONST[mcore.v6],carrier:STRING,
  cases:VEC[32,InterfaceCanaryCaseReceipt],pass_count:U53,passed:BIT,
  failure_code:FailureCode
}
NonharmCaseReceipt = OBJ{
  case_handle:HANDLE26,actor_input_sha256:HEX64,
  birth_score_hex:HEX16,carrier_score_hex:HEX16,difference_hex:HEX16,
  passed:BIT
}
NonharmReceipt = OBJ{
  v:CONST[mcore.v6],carrier:STRING,cases:VEC[32,NonharmCaseReceipt],
  paired_mean_difference_hex:HEX16,adverse_bound_hex:HEX16,
  passed:BIT,failure_code:FailureCode
}
ReaderModelAcceptanceReceipt = OBJ{
  v:CONST[mcore.v6],carrier:STRING,
  required_found_count:U53,observed_required_found_count:U53,
  required_miss_count:U53,observed_required_miss_count:U53,
  unavailable_found_count:U53,wrong_anchor_count:U53,
  cut_suppression_failure_count:U53,bypass_count:U53,
  scorer_receipt_sha256s:VEC[1..100000,HEX64],passed:BIT,
  failure_code:FailureCode
}
ExtractionReceipt = OBJ{
  v:CONST[mcore.v6],carrier:STRING,stage:ENUM[S1,S2,TEXT],
  expected_row_sha256s:VEC[0..32,HEX64],
  observed_row_sha256s:VEC[0..32,HEX64],missing_count:U53,
  unexpected_count:U53,exact_content_match:BIT,passed:BIT,
  failure_code:FailureCode
}
ResetReceipt = OBJ{
  v:CONST[mcore.v6],carrier:STRING,actor_input_sha256:HEX64,
  birth_actor_state_sha256:HEX64,empty_context_sha256:HEX64,
  no_raw_child_context:BIT,no_parent_context:BIT,
  no_cross_episode_mutable_state:BIT,passed:BIT,failure_code:FailureCode
}
ComponentGateReceipt = OBJ{
  v:CONST[mcore.v6],component:ENUM[S,M,U,W,F,R],
  required_receipt_sha256s:VEC[1..100000,HEX64],
  all_required_present:BIT,all_required_passed:BIT,
  raw_contrast_available:BIT,gate:BIT,failure_code:FailureCode
}
TextRootReceipt = OBJ{
  v:CONST[mcore.v6],root_seed_commitment:HEX64,
  required_receipt_sha256s:VEC[1..100000,HEX64],
  all_required_present:BIT,all_required_passed:BIT,t_r:BIT,
  failure_code:FailureCode
}
FailureReceipt = OBJ{
  v:CONST[mcore.v6],scope:ENUM[GLOBAL_INVALID,ROOT_INVALID,
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
  v:CONST[mcore.v6],nodes:VEC[1..256,ProvenanceNode],
  derivations:VEC[0..64,DerivationReceipt],
  root_sha256:HEX64
}
RoleAssignment = OBJ{
  semantic_role:STRING,public_handle:HANDLE26
}
AuditEnvelope = OBJ{
  v:CONST[mcore.v6],package_manifest_sha256:HEX64,
  root_seed_commitment:HEX64,audit_episode_instance_handle:HANDLE26,
  public_pair_handle:HANDLE26,condition_handle:HANDLE26,
  hidden_bits:VEC[3,BIT],role_assignments:VEC[1..256,RoleAssignment],
  environment_graph_sha256:HEX64,provenance_receipt:ProvenanceReceipt,
  schedule_receipt:ScheduleReceipt,
  device_intervals:VEC[0..100000,DeviceIntervalReceipt],
  optimization_receipts:VEC[0..6,OptimizationReceipt],
  pairwise_work_receipts:VEC[0..2,PairwiseWorkReceipt],
  inference_rng_receipts:VEC[0..100000,InferenceRngReceipt],
  rpc_receipts:VEC[0..100000,RpcReceipt],
  scorer_receipts:VEC[0..100000,ScorerReceipt],
  prefix_receipts:VEC[0..100000,PrefixComparisonReceipt],
  compiler_prefix_receipts:VEC[0..100000,CompilerPrefixReceipt],
  acl_receipt:AclReceipt,bfs_certificate:BfsCertificate,
  fake_clock_receipt:FakeClockReceipt,
  tensor_receipts:VEC[0..4096,TrainingTensorReceipt],
  control_receipts:VEC[0..128,ControlReceipt],
  failure_receipt:FailureReceipt,public_trace_sha256:HEX64,
  raw_evidence:BLOB
}

RootEntropyEntry = OBJ{
  cohort:ENUM[TEXT,DEV,CONF],root_index:U53,call_ordinal:U53,
  root_seed:BLOB,root_seed_commitment:HEX64,
  entropy_host_sha256:HEX64,entropy_runtime_sha256:HEX64,
  success:CONST[1]
}
RootEntropyTranscript = OBJ{
  v:CONST[mcore.v6],entries:VEC[32,RootEntropyEntry],
  entropy_tool_sha256:HEX64
}
RootManifestEntry = OBJ{
  cohort:ENUM[TEXT,DEV,CONF],root_index:U53,
  root_seed_commitment:HEX64,root_nonce_handle:HANDLE26,
  materialized_root_sha256:HEX64
}
CohortManifest = OBJ{
  v:CONST[mcore.v6],cohort:ENUM[TEXT,DEV,CONF],
  entries:VEC[1..16,RootManifestEntry]
}
DeckRowRef = OBJ{
  deck_slot:U53,row_sha256:HEX64,example_handle:HANDLE26,
  tensor_receipt_sha256:HEX64
}
DeckManifest = OBJ{
  v:CONST[mcore.v6],stage:ENUM[S1,S2],
  condition:ENUM[FULL_OLD,SOURCE_DERANGED_OLD,DREAM_DERANGED_OLD,
    FULL_NEW_h0,FULL_NEW_h1,FULL_OLD_PLUS_PAD],
  rows:VEC[1..4096,DeckRowRef]
}
DeviceIntervalReceipt = OBJ{
  interval_handle:HANDLE26,lease_handle:HANDLE26,device_uuid:STRING,
  ownership:CONST[EXCLUSIVE],category:ENUM[FIT,TEXT,EVAL,QUALIFICATION,MIXED],
  clock_kind:ENUM[MONOTONIC_RAW,PROVIDER_LEASE],
  clock_source_sha256:HEX64,device_allocation_ns:U64D,
  device_release_ns:U64D,image_sha256:HEX64,driver_sha256:HEX64,
  runtime_sha256:HEX64
}
FitAttemptReceipt = OBJ{
  v:CONST[mcore.v6],attempt_handle:HANDLE26,
  root_seed_commitment:HEX64,stage:ENUM[S1,S2],
  condition:ENUM[FULL_OLD,SOURCE_DERANGED_OLD,DREAM_DERANGED_OLD,
    FULL_NEW_h0,FULL_NEW_h1,FULL_OLD_PLUS_PAD],
  launch_ordinal:U53,status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT],
  device_interval:DeviceIntervalReceipt,deck_manifest_sha256:HEX64,
  optimization_receipt_sha256:HEX64,
  output_artifact_sha256:OPT[HEX64],failure_code:FailureCode
}
ExecutionAttemptReceipt = OBJ{
  v:CONST[mcore.v6],attempt_handle:HANDLE26,
  kind:ENUM[TEXT_ACTOR,TEXT_READER,EVAL_ACTOR,EVAL_READER,
    WSTAR_QUALIFICATION,READER_QUALIFICATION],
  root_seed_commitment:OPT[HEX64],launch_ordinal:U53,
  status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT],
  device_interval:DeviceIntervalReceipt,
  output_artifact_sha256:OPT[HEX64],failure_code:FailureCode
}
CpuIntervalReceipt = OBJ{
  interval_handle:HANDLE26,kind:ENUM[MATERIALIZER,COMPILER,CHECKER],
  process_handle:HANDLE26,clock_source_sha256:HEX64,
  start_ns:U64D,release_ns:U64D,status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT],
  failure_code:FailureCode
}
DurationReceipt = OBJ{
  interval_handle:HANDLE26,kind:ENUM[QUEUE,RESET,SERIALIZATION],
  clock_source_sha256:HEX64,start_ns:U64D,release_ns:U64D,
  failure_code:FailureCode
}
DeviceUnionSegment = OBJ{
  lease_handle:HANDLE26,device_uuid:STRING,start_ns:U64D,release_ns:U64D,
  category:ENUM[FIT,TEXT,EVAL,QUALIFICATION,MIXED]
}
CostBucket = OBJ{
  category:ENUM[FIT,TEXT,EVAL,QUALIFICATION,MIXED,CPU,QUEUE,RESET,SERIALIZATION],
  status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT,NOT_APPLICABLE],
  attempt_count:U53,nanoseconds:U64D
}
CostSummary = OBJ{
  v:CONST[mcore.v6],cost_valid:BIT,failure_code:FailureCode,
  device_union_segments:VEC[0..100000,DeviceUnionSegment],
  buckets:VEC[1..1000,CostBucket],device_total_ns:U64D,
  cpu_total_ns:U64D,queue_total_ns:U64D,reset_total_ns:U64D,
  serialization_total_ns:U64D
}
SkippedCell = OBJ{
  cell_id:HANDLE26,reason:ENUM[TEXT_STOP,DEV_S1_KILL,DEV_FULL_KILL,
    ROOT_Q_S1_FALSE,CONF_COMPLETE],attempt_created:CONST[0]
}
QS1Receipt = OBJ{
  v:CONST[mcore.v6],root_seed_commitment:HEX64,
  named_input_sha256s:VEC[1..10000,HEX64],q_s1:BIT,
  emitted_before_s2_open:CONST[1],failure_code:FailureCode
}
IndicatorIsolationReceipt = OBJ{
  v:CONST[mcore.v6],root_seed_commitment:HEX64,
  immutable_assets_sha256:HEX64,root_namespace_handle:HANDLE26,
  no_shared_mutable_state:BIT,no_cross_root_input:BIT,
  root_scoped_leases:BIT,all_execution_inputs_receipted:BIT,
  independent_noise_assumption_registered:BIT,
  ambiguous_shared_cause:BIT,failure_code:FailureCode
}
RootComponentResult = OBJ{
  component:ENUM[S,M,U,W,R],gate:BIT,
  contrast_hex:OPT[HEX16],indicator:BIT
}
TextRootResult = OBJ{
  v:CONST[mcore.v6],cohort:CONST[TEXT],root_index:U53,
  root_seed_commitment:HEX64,text_root_receipt:TextRootReceipt,
  skipped_cells:VEC[0..6,SkippedCell],fit_attempt_handles:CONST[[]],
  execution_attempt_handles:VEC[0..100000,HANDLE26],
  terminal_failure:FailureReceipt,cost_summary_sha256:HEX64
}
ScienceRootResult = OBJ{
  v:CONST[mcore.v6],cohort:ENUM[DEV,CONF],root_index:U53,
  root_seed_commitment:HEX64,q_s1_receipt:QS1Receipt,
  components:VEC[5,RootComponentResult],f_gate:BIT,
  f_contrast_hex:OPT[HEX16],skipped_cells:VEC[0..6,SkippedCell],
  component_gate_receipts:VEC[6,ComponentGateReceipt],
  fit_attempt_handles:VEC[0..6,HANDLE26],
  execution_attempt_handles:VEC[0..100000,HANDLE26],
  isolation_receipt:IndicatorIsolationReceipt,
  terminal_failure:FailureReceipt,cost_summary_sha256:HEX64
}
RootResult = ONEOF[TextRootResult,ScienceRootResult]
ComponentStatistic = OBJ{
  component:ENUM[S,M,U,W,R],n:CONST[16],successes:U53,
  tail_numerator:U53,tail_denominator:CONST[65536],p_value_hex:HEX16,
  cp_lower_hex:HEX16,rejected:BIT,post_stop:BIT
}
StoppingReceipt = OBJ{
  v:CONST[mcore.v6],stage:ENUM[TEXT_EXTENSION,DEV_S1_KILL,
    DEV_FULL_KILL,DEV_ROOT_S2,CONF_ROOT_S2,FIXED_SEQUENCE],
  root_indices:VEC[1..16,U53],input_result_sha256s:VEC[1..16,HEX64],
  predicate_sha256:HEX64,decision:ENUM[LAUNCH,SKIP,STOP,CONTINUE],
  emitted_before_downstream_open:CONST[1]
}
RpcReceipt = OBJ{
  v:CONST[mcore.v6],request_sha256:HEX64,response_frame:BLOB,
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
  v:CONST[mcore.v6],entries:VEC[33,FailureScopeEntry]
}
GoalPairByteCutReceipt = OBJ{
  v:CONST[mcore.v6],input_a_sha256:HEX64,input_b_sha256:HEX64,
  first_difference_offset:U53,first_difference_json_pointer:STRING,
  complete_allowed_difference_bitmap:BLOB,
  common_public_anchor_handles:VEC[0..4,HANDLE26],passed:BIT
}
GoalPairByteCutTable = OBJ{
  v:CONST[mcore.v6],entries:VEC[32,GoalPairByteCutReceipt]
}
PackageMember = OBJ{
  path:STRING,byte_length:U53,media_type:STRING,sha256:HEX64
}
ResultMember = OBJ{
  member:PackageMember,json_root_type:OPT[STRING]
}
PackageManifest = OBJ{
  v:CONST[mcore.v6],members:VEC[1..100000,PackageMember],
  merkle_root_sha256:HEX64
}
CheckerSubcheck = OBJ{
  name:STRING,passed:BIT,failure_code:FailureCode,evidence_sha256:HEX64
}
CheckerReceipt = OBJ{
  v:CONST[mcore.v6],package_manifest_sha256:HEX64,
  package_merkle_root_sha256:HEX64,materializer_sha256:HEX64,
  checker_sha256:HEX64,runtime_sha256:HEX64,
  subchecks:VEC[1..100000,CheckerSubcheck],overall_passed:BIT,
  failure_code:FailureCode
}
QualificationReceipt = OBJ{
  v:CONST[mcore.v6],kind:ENUM[WSTAR,READER],
  binding_sha256:HEX64,checks:VEC[1..100000,CheckerSubcheck],
  accepted:BIT,failure_code:FailureCode
}
RootResultBundleManifest = OBJ{
  v:CONST[mcore.v6],package_manifest_sha256:HEX64,
  cohort:ENUM[TEXT,DEV,CONF],root_index:U53,
  root_seed_commitment:HEX64,members:VEC[1..100000,ResultMember],
  merkle_root_sha256:HEX64,root_result:RootResult,
  fit_attempts:VEC[0..6,FitAttemptReceipt],
  execution_attempts:VEC[0..100000,ExecutionAttemptReceipt],
  public_traces:VEC[0..100000,PublicExecutionTrace],
  audit_envelopes:VEC[0..100000,AuditEnvelope],
  checker_receipts:VEC[1..100000,CheckerReceipt],
  interface_canary_receipts:VEC[0..7,InterfaceCanaryReceipt],
  nonharm_receipts:VEC[0..7,NonharmReceipt],
  reader_acceptance_receipts:VEC[0..8,ReaderModelAcceptanceReceipt],
  extraction_receipts:VEC[0..8,ExtractionReceipt],
  reset_receipts:VEC[0..100000,ResetReceipt],
  cpu_intervals:VEC[0..100000,CpuIntervalReceipt],
  duration_intervals:VEC[0..100000,DurationReceipt],cost_summary:CostSummary
}
CohortRootBundleEntry = OBJ{
  root_index:U53,root_seed_commitment:HEX64,
  root_bundle_manifest_sha256:HEX64,scheduled:BIT,s2_launched:BIT
}
CohortResultBundleManifest = OBJ{
  v:CONST[mcore.v6],package_manifest_sha256:HEX64,
  cohort:ENUM[TEXT,DEV,CONF],members:VEC[1..100000,ResultMember],
  merkle_root_sha256:HEX64,roots:VEC[8..16,CohortRootBundleEntry],
  stopping_receipts:VEC[1..1000,StoppingReceipt],
  statistics:VEC[0..5,ComponentStatistic],
  cohort_execution_attempts:VEC[0..100000,ExecutionAttemptReceipt],
  cohort_cpu_intervals:VEC[0..100000,CpuIntervalReceipt],
  cohort_duration_intervals:VEC[0..100000,DurationReceipt],
  cost_summary:CostSummary
}
QualificationResultBundleManifest = OBJ{
  v:CONST[mcore.v6],package_manifest_sha256:HEX64,
  members:VEC[1..100000,ResultMember],merkle_root_sha256:HEX64,
  qualification_receipts:VEC[2,QualificationReceipt],
  checker_receipts:VEC[1..100000,CheckerReceipt],
  execution_attempts:VEC[0..100000,ExecutionAttemptReceipt],
  cpu_intervals:VEC[0..100000,CpuIntervalReceipt],
  duration_intervals:VEC[0..100000,DurationReceipt],
  cost_summary:CostSummary
}
ProgramResultIndex = OBJ{
  v:CONST[mcore.v6],package_manifest_sha256:HEX64,
  text_cohort_manifest_sha256:HEX64,dev_cohort_manifest_sha256:HEX64,
  conf_cohort_manifest_sha256:HEX64,
  qualification_manifest_sha256:HEX64
}
```

The deterministic translator rejects unresolved names and emits literal
Draft-2020-12 JSON Schema with `$defs`, `required` equal to every listed field,
and `additionalProperties:false`. The manifest-bound semantic constraint file
adds the following finite rules, each independently recomputed by the checker:

- every manifest-listed JSON path in Section 1.1 maps to exactly its displayed
  root type; every result path in Section 10 maps to exactly its result root;
  all referenced `$defs` resolve and no gate reads an untyped raw-evidence blob;
- child ActorEpisodeInput phases require `goal=null`, non-null task_input,
  null menu, and zero legal READ types. CHILD_FOUNDATION_ROUTE/TERMINAL map to
  their matching ChildFoundationTask kind; CHILD_SOURCE to ChildSourceTask;
  CHILD_ABLATION to ChildAblationTask; CHILD_PAIR_SELECTION to
  ChildPairSelectionTask; CHILD_SUPPORT to ChildSupportTask; and CHILD_PAD to
  ChildPadTask. Pair-selection task bytes contain all 32 completed authentic
  action/observation pairs and the complete 8-lane/28-pair public roster;
  support task bytes contain the later committed reveal event. B accepts
  BGoal or BAtomsGoal only;
  C_PROBE/C_LIVE/D accept exactly their matching goal and null task_input; C
  alone requires PublicMenu. BAtomsGoal differs from its paired BGoal only in
  kind/read-budget under the registered bitmap;
- the six RecognitionRequest variants equal the deterministic projection in
  Section 6.2. RouteRequest carries the current goal's actual route cue;
  TerminalRequest/NewRequest carry its actual target; SourceRequest its actual
  desired outcome. An extra, missing, actor-selected, or reordered anchor is
  not schema-valid;
- the two PublicMenu entries have distinct L/R source actions and four
  pairwise-distinct experiment actions, with menu hash recomputed; catalog
  query types and anchors are duplicate-free in canonical byte order;
- ATOM has one ordered action/no statistics; SEQUENCE has two/no statistics;
  CHOICE_TABLE has no ordered actions and exactly two statistics with distinct
  actions, one common desired outcome, and counts 0..4. Every row class has
  the exact canonical key/destination/citation arity;
- each AuthenticEvidencePair observation cites its child action and later
  tick. Each DerivedControlEvidencePair has an exact SOURCE_OUTCOME_REBIND
  receipt whose donor observation cites its donor action; donor identity is
  audit-only and the presented action is exactly the presealed rebind;
- ChildPairSelectionEvent binds the complete input/bindings/draw ledger, all
  32 ablation action and 32 later observation handles, and the eight visible
  pair handles; its two distinct choices are roster members and its tick is
  later than every cited observation;
- SupportFixtureRevealEvent cites that exact selection at a later tick and a
  new fixture namespace disjoint from every ablation instruction/action/
  observation handle. LINK evidence contains the reveal plus exactly eight
  later authentic pairs: joint/left/right/nuisance for each selected member;
  both selected profiles must equal 1/0/0/0;
- PAD contains one authentic p_0-then-Q pair; source contains exactly four L
  and four R pairs and T/O desired handles. AuthenticSourceEvidenceView admits
  only authentic bindings;
- template sets match compiler phase. SOURCE has exactly the 50 complete
  T/O-by-L/R count alternatives, LINK exactly two post-selection revealed
  links, PAD exactly one d_pad, and NEW exactly n0/n1 revealed before outcome.
  Every template has empty fill fields; admitted rows are byte-identical to a
  listed complete template;
- SourceCompilerInput, LinkCompilerInput, PadCompilerInput, and NewCompilerInput
  are disjoint. NEW links its authentic source view, actual source-choice
  MemoryAuthorizedActionEvent, complete menu, declaration, dispatch, later
  observation, and pre-outcome templates by exact handles/hashes/ticks. Its
  compiler can recompute preferred family and posterior from those bytes;
- every CompilerInvocationEvent input hash is recomputed and its tick follows
  all prerequisites; every CompilerDecision cites that invocation/input at a
  later tick. SOURCE admits two choice rows, LINK two sequences, PAD one atom,
  NEW zero/one atom, with one canonical status/code/posterior/citation tuple;
- `public_task_law` is the package's root-independent public C law and contains
  no b/z/h, role, expected row, donor, condition, or endpoint byte. Templates
  carry root-local aliases without revealing which alternative is correct;
- PublicDeclaration hypotheses equal `[0,1]`; prediction/row entries use that
  order, its source row/choice/menu/experiment handles link exactly, and every
  cited event precedes it. PublicObservation likewise cites exactly one earlier
  authorized action; child, memory, selection, and dispatch authorizations are
  disjoint;
- SOURCE_READ_SWAP_C retains the exact FULL public row handle and all non-count
  bytes. Only the two count bytes and mechanically computed content-hash/pad
  descendants may differ; intervention identity is audit-only;
- TransitionSystem and ActionRosters contain exactly one transition for each
  phase/state and each of 32 surfaces, including selection/support/dead states;
  C_PROBE/C_LIVE and B/B_ATOMS/D budgets and terminal predicates equal Sections
  4--5. CandidateRosters contain 32 complete MemoryRows per request;
- AvailabilityRelations and CanonicalReturns form one total finite relation
  over all legal requests/carriers/controls. The BFS, cuts, swaps, and model
  false-positive gates recompute only from these complete rows;
- every RPC frame is exactly 16384 bytes with the Section-6 magic/length/JCS/
  pad split and releases at request tick+1. AllowedDifferenceMaps contains the
  RPC maps and mechanically closed cue-descendant mask; FakeClockReceipt
  contains all bound subdeadline/overrun cases;
- ControlRegistry contains exactly the 21 IDs and complete expected traces in
  Section 8.1; ControlReceipt must match its ControlSpec byte-for-byte. The
  deleted no-goal diagnostic occurs in no generated package/result artifact.
  NO_SLEEP2 mounts FULL_OLD and has the exact old-FOUND/new-MISS trace;
- RootEntropyEntry seed blobs are 32 bytes and commitment equals the Section-2
  equation. Entries are ordinals 0..31 with TEXT 0..7, DEV 0..7, CONF 0..15,
  no duplicate seed/commitment, and exact cohort manifest cardinalities;
- RootGeneratorSpec contains the complete literal DomainSpec roster in the
  exact iteration order; rejection advances the per-domain counter on every
  attempt. Alias candidates are unique within pool/root, cross-root reuse is
  legal only through root-capability lookup, and no root is rejected;
- Protocol's six condition entries are each present once in displayed order;
  OrderTables are true permutations. ScheduleTables has the five exact TEXT
  rows `(0,STOP,0)`, `(1,STOP,0)`, `(2,EXTEND_T5_T8,6)`,
  `(3,EXTEND_T5_T8,6)`, and `(4,PROCEED,0)`, plus the four exact S1/S2 rules
  from Section 9; QS1Receipt and StoppingReceipt
  mechanically reproduce every launch/skip and precede downstream opening;
- FailureScopeTable is a bijection over all 33 FailureCodes. NONE iff scope
  NONE; structural GLOBAL/ROOT receipts precede endpoint opening, and VALID_*
  is emitted only after a structurally valid completed trace. Endpoint output
  is `(1,1,NONE)`, `(1,0,VALID_*)`, or `(0,0,ROOT_*|GLOBAL_*)`, never `(0,1)`;
- PairwiseWorkReceipt recomputes equality of checkpoint/optimizer/device/
  health/kernel/tensor/mask/work and every stage-keyed RNG counter. Scorer,
  prefix, ACL, BFS, fake-clock, compiler-prefix, control, interface/non-harm,
  isolation, and cost gates each read their named typed receipt;
- each ControlCaseReceipt matches its registered ControlCaseSpec exactly and
  ControlReceipt.aggregate_passed is the registered aggregate over all cases.
  InterfaceCanaryReceipt passes iff all 32 cases pass with zero malformed,
  unavailable, or uncited events. NonharmReceipt recomputes all 32 paired
  differences and passes iff their binary64 mean is at least `-0.05` under the
  package's exact arithmetic rule. ReaderModelAcceptanceReceipt passes iff all
  required FOUND/MISS counts match and every error count is zero.
  ExtractionReceipt passes iff expected and observed row-SHA multisets are
  identical; ResetReceipt passes iff all three isolation bits are one;
- ComponentGateReceipt binds the complete literal constituent-receipt list for
  its named G gate and cannot pass if any constituent is missing or false.
  TextRootReceipt binds the complete Section-9.2 constituent list and equals
  one iff all are present and pass. A generic receipt hash cannot substitute
  for any of these typed objects;
- ScienceRootResult contains S/M/U/W/R exactly once, F separately, the six
  ComponentGateReceipts exactly once in `[S,M,U,W,F,R]` order, NA iff its gate
  is false, indicator zero on invalid/skipped cells, and one terminal failure.
  TextRootResult contains one TextRootReceipt, no fit attempts, and no science
  components. ComponentStatistic has `0<=K<=16`,
  `tail_numerator=sum_{j=K}^{16} C(16,j)`, the exact rational denominator
  65536, binary64 round-to-nearest-ties-to-even encodings for reported values,
  and `cp_lower_hex=0000000000000000` exactly at K=0;
- U64D parses as an unsigned integer <=18446744073709551615. Every interval is
  half-open with release>=start. DeviceUnionSegments equal the union grouped by
  lease/device with no overlaps; all launched attempts, including failures,
  appear once. CPU and queue/reset/serialization intervals are disjoint typed
  ledgers, and CostSummary recomputes every bucket/total; and
- package/result member paths are unique normalized sorted paths under disjoint
  `package/` and `results/` namespaces. Every member/Merkle hash is recomputed
  without a manifest hashing itself; every presealed root, scheduled or not,
  has one root bundle, unscheduled roots contain zero attempts plus explicit
  skipped cells, root bundles contain <=6 fits, cohort
  bundles contain exactly 8 TEXT/DEV or 16 CONF root entries, and ProgramResultIndex
  binds all cohort and qualification manifests. Root-bundle members occupy
  only `results/<cohort>/root-<index>/`; cohort members occupy only
  `results/<cohort>/aggregate/` and bind root manifests by digest without
  relisting their members; qualification members occupy only
  `results/qualification/`. No receipt or interval is duplicated across a root,
  cohort aggregate, or qualification bundle. Every result member whose media
  type is JSON has non-null `json_root_type` naming one closed Section-12 type
  and validates against it; every non-JSON member has null `json_root_type`.

## Source lineage

- `research_notes/analysis/2026-09-12_m_core_exact_two_cycle_design_v5.md`;
- `research_notes/analysis/2026-09-12_m_core_v5_fresh_causal_mechanism_audit.md`;
- `research_notes/analysis/2026-09-12_m_core_v5_fresh_statistics_visibility_execution_audit.md`.
