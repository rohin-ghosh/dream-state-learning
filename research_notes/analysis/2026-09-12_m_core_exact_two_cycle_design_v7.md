# M-core v7: executable crossed two-cycle relay contract

Date: 2026-09-12 UTC

Status: independent zero-fit design only. This complete successor supersedes
`2026-09-12_m_core_exact_two_cycle_design_v6.md`. It changes no builder,
coordination, benchmark, child, model, tokenizer, adapter, checkpoint, job,
GPU, resource, claim, release, or submission. Every package, qualification,
TEXT result, fit, and receipt below remains future evidence.

## 0. Claim, topology, and exclusions

The trained topology is fixed at exactly six fits for every root that completes
both cycles; a root killed after S1 has exactly three and is not a complete
two-cycle root:

```text
S1 triplet                         S2 triplet, iff Q_S1(root)=1
FULL_OLD                          FULL_NEW_H0
SOURCE_DERANGED_OLD               FULL_NEW_H1
DREAM_DERANGED_OLD                FULL_OLD_PLUS_PAD
```

The only releasable claim, conditional on every gate, is:

> In a finite typed benchmark, a qualified writer carried rows compiled from
> authenticated child action/outcome model turns and from a child-authenticated
> recovery, before support and link-template reveal, of the preassigned pair
> uniquely indicated by public ablation evidence. A reset clean actor used
> typed reads to complete two goal-conditioned old-memory traces. Following an
> authenticated public experimental outcome, a second clean-base cumulative
> write preserved the required old link and added the uniquely public-law-
> identified new row required for a delayed action.

This does not identify DREAM intelligence, a causal benefit of the selection
policy, native search, online/in-place growth, general retention,
generalization, recurrence, or a whole-organism effect. “Child-selected” may
describe custody only; the causal wording is “child-authenticated recovery of
the preassigned evidence-indicated pair.”

## 1. Build phases, namespaces, and immutable bytes

### 1.1 Noncircular five-phase build

The build order is mandatory:

1. **ENTROPY_SEAL:** freeze the static draft bytes required for generation,
   excluding the not-yet-created expected-root index and final package
   manifest. `entropy_seal.json` contains the 32 independent root
   seeds/commitments plus hashes of the static protocol, schema, generator,
   alias-pool, qualification, runtime, and source bytes. Address it directly
   by SHA-256 of its JCS+LF bytes.
2. **EXPECTED_GENERATION:** a pure CPU generator consumes that seal and emits
   one `ExpectedRootContentManifest` for each TEXT(8), DEV(8), CONF(16) root.
   These manifests bind only the entropy seal and their content members, never
   the not-yet-sealed final package.
3. **PACKAGE_SEAL:** `expected_roots.json` binds all 32 expected-root addresses;
   `package_manifest.json` then binds every immutable byte, including entropy
   seal, expected-root index, source, schemas, and runtime. It excludes itself.
4. **INDEPENDENT_REMATERIALIZATION:** the packaged materializer consumes the
   final package and writes fresh `MaterializedRootBundleManifest`s. Their
   content-member Merkle roots must byte-match the expected roots, and they
   additionally bind the final package address.
5. **CHECK/RESULT:** an independently implemented checker that imports no
   generator/materializer code reconstructs all bytes and emits root/cohort
   checker receipts. TEXT, qualification, or fits cannot open before phases
   1--4 pass.

This removes the future-hash cycle: expected content exists before the final
package; execution manifests that name the final package exist afterward.

### 1.2 Static package roster

Package-member paths are UTF-8 NFC POSIX-relative to the package directory and
never begin with `package/`, `/`, `results/`, or `materialized/`. The exhaustive
JSON roster is:

| literal path | closed root |
|---|---|
| `protocol.json` | Protocol |
| `schema_catalog.json` | SchemaCatalog |
| `semantic_constraints.json` | SemanticConstraints |
| `entropy_seal.json` | EntropySeal |
| `root_generator.json` | RootGeneratorSpec |
| `event_strata.json` | EventStrata |
| `draw_plan.json` | DrawPlan |
| `alias_pool.json` | AliasPool |
| `handle_codec.json` | HandleCodec |
| `rpc_machine.json` | RpcMachine |
| `failure_decisions.json` | FailureDecisionTable |
| `program_machine.json` | ProgramMachine |
| `writer_binding.json` | WriterBinding |
| `writer_qualification_spec.json` | WriterQualificationSpec |
| `reader_binding.json` | ReaderBinding |
| `reader_qualification_spec.json` | ReaderQualificationSpec |
| `actor_binding.json` | ActorBinding |
| `runtime_manifest.json` | RuntimeManifest |
| `device_eligibility.json` | DeviceEligibilityRoster |
| `expected_roots.json` | ExpectedRootIndex |

`package_manifest.json` has root `PackageManifest`. Materializer/checker source
files, dependency lock, canonical prompts, and static fixtures are non-JSON
`ManifestMember`s in the same manifest. Extra/missing/symlink/duplicate or
wrong-root files are `GLOBAL_PACKAGE_MEMBER`.

`SchemaBinding` includes the literal path or closed path-pattern; no array-order
convention is allowed. Every JSON package, materialized, and result member has
one non-null named root type; every non-JSON member has null root type.

### 1.3 Canonical manifest/Merkle law

Stored JSON is RFC-8785/JCS UTF-8 plus exactly one LF. Member paths have no
leading slash, backslash, empty component, or `.`/`..`; sort by raw UTF-8 path
bytes. For each member:

```text
leaf = SHA256("MCORE-V7-LEAF\0" || U32BE(path_bytes) || path_bytes ||
              U64BE(byte_length) || raw_sha256)
node = SHA256("MCORE-V7-NODE\0" || left || right)
```

`U32BE(path_bytes)` means the four-byte length, not the bytes themselves. An
odd node is duplicated. A manifest excludes itself and is addressed by SHA-256
of its own JCS+LF. The same law applies independently to entropy, expected-root,
materialized-root, materialized-cohort, root-result, cohort-result, and program
manifests. A parent manifest references a child only by the child's address and
does not relist child members.

Namespaces are disjoint:

```text
static package:       <package-root>/<package-relative path>
rematerialized root:  materialized/<cohort>/root-<00..15>/...
result root:          results/<cohort>/root-<00..15>/...
cohort aggregate:     results/<cohort>/aggregate/...
qualification:        results/qualification/...
program:              results/program/...
```

### 1.4 Concrete root content and checker custody

Each expected/materialized root contains exactly these JSON members:

```text
geometry.json                 RootGeometry
transitions.json              RootTransitionTable
action_rosters.json           RootActionRosters
candidate_rosters.json        RootCandidateRosters
mount_instances.json          RootMountInstances
compiler_templates.json       RootCompilerTemplates
fixtures.json                 RootFixtures
controls.json                 RootControlRegistry
orders.json                   RootOrderTables
difference_maps.json          RootDifferenceMaps
canonical_returns.json        RootCanonicalReturns
cell_roster.json              RootCellRoster
gate_rosters.json             RootGateRosters
materialization_receipt.json  RootMaterializationReceipt
```

Every root object carries the same `root_seed_commitment` and
`root_namespace_handle`. Every lookup key includes that namespace. Cross-root
lookup is absent from actor, reader, compiler, and endpoint APIs. Reused alias
bytes across roots are legal; reuse inside one root/handle class is not.

`ExpectedRootContentManifest` binds the entropy seal and these member hashes.
`MaterializedRootBundleManifest` binds the final package, expected-root
address, identical member table/Merkle, cohort, root index, and namespace.
`MaterializedCohortBundleManifest` binds exactly 8 TEXT, 8 DEV, or 16 CONF root
bundle addresses. `CheckerReceipt` binds package address, exact checked root and
cohort bundle addresses/content roots, tool/runtime hashes, and all subchecks;
it cannot replay against another root or cohort.

## 2. Root generator and exact geometry

### 2.1 Independent entropy, typed hashing, and handles

Before outcome/model work, one OS-CSPRNG call produces each 32-byte root seed.
TEXT indices 0..7, DEV 0..7, and CONF 0..15 are fixed call ordinals. Duplicate
seed or commitment is `GLOBAL_ENTROPY`; there is no replacement.

```text
root_seed_commitment = SHA256("MCORE-V7-ROOT-SEED\0" || U32BE(32) || seed)
BYTES(x)  = 0x01 || U64BE(len(x)) || x
UTF8(x)   = 0x02 || U64BE(len(utf8(x))) || utf8(x)
U64(x)    = 0x03 || U64BE(x)
U32(x)    = 0x04 || U32BE(x)
SHA(x)    = 0x05 || 32 raw digest bytes
HANDLE(x) = 0x06 || U32BE(26) || 26 ASCII handle bytes
H(tag,parts...) = SHA256(ASCII("MCORE-V7\0") ||
                         U32BE(len(utf8(tag))) || utf8(tag) || concat(parts))
R(seed,domain,counter) = U256BE(H("rng",BYTES(seed),UTF8(domain),U64(counter)))
```

For `draw(domain,n)`, read the current counter, increment before acceptance,
reject `x>=floor(2^256/n)*n`, and otherwise return `x mod n`. Every rejected
digest and final counter is receipted.

Generated handles use exactly the first 128 digest bits. Prepend two zero bits,
split the 130 bits into 26 five-bit values, and map them through
`abcdefghijklmnopqrstuvwxyz234567`; there is no `=` padding. The package
`HandleCodec` binds this rule and test vectors. A collision between distinct
objects in any one root/handle class is `GLOBAL_SCHEMA`; cross-root reuse is
legal because lookup is root-scoped.

The handle inputs are exact and deliberately not content-addressed:

```text
root_namespace_handle = CODEC(first128(H("root-namespace",BYTES(seed))))
object_handle(class,assignment_ordinal) =
  CODEC(first128(H("object-handle",BYTES(seed),UTF8(class),
                   U64(assignment_ordinal))))
```

`assignment_ordinal` is the unique ordinal prelisted for that class in
DrawPlan; payload swaps therefore retain handles without a hash exception.

### 2.2 Closed draw plan

`event_strata.json` literally enumerates every presentation population,
including decoy lanes, foundation rows, child trials, candidates, fixtures,
templates, controls, and cell order. `draw_plan.json` gives every draw in exact
ordinal order with domain, operation (`SCALAR` or descending Fisher--Yates),
population handle/cardinality, assignment target, and handle class. No runtime
domain or unreceipted draw is legal.

Required scalar domains are `b`, `z`, `lane-pair`, `pair-ab`, `u-D`,
`dream-shift`, `sigma`, `device-S1`, `device-S2`, `condition-S1`,
`condition-S2`, `candidate-rotation`, `order-B`, `order-C`, and `order-D`.
The plan additionally lists `alias/<class-id>` and `stratum/<stratum-id>` in
manifest order. `RootMaterializationReceipt` contains every counter/rejection,
permutation digest, assignment/role digest, handle-codec test, collision check,
and generated-member digest. Two independent CPU materializations must produce
identical receipt and member bytes.

For each root, the DrawPlan instantiates these operations in this exact order:

1. Fisher--Yates every AliasClass in its manifest order;
2. draw `b` and `z` from 2;
3. draw one of the lexicographically enumerated 28 unordered lane pairs;
4. draw its A/B order from 2 and then `u_D` from its two members;
5. shuffle the six remaining lanes; first three receive LEFT profiles and the
   rest RIGHT profiles;
6. draw `dream_shift=1+draw(7)` and set `pi(i)=(i+dream_shift) mod 8`;
7. Fisher--Yates `[0..31]` to obtain the root-local base slot permutation
   `sigma`;
8. shuffle every remaining EventStratum exactly once in manifest order;
9. draw the registered S1 and S2 device indices and independently draw one of
   the six triplet permutations for each stage;
10. draw `candidate_rotation` from 4; probe `j` in each four-probe block uses
    `P[(candidate_rotation+j) mod 4]`;
11. Fisher--Yates the complete applicable B, C, and D control rosters under
    their distinct domains; and
12. assign every generated handle from the typed object-role digest and record
    its class in RootMaterializationReceipt.

There is no other draw. The four reader orders are fully derived from sigma:

```text
P0 = sigma([0,1,...,31])
P1 = sigma([31,30,...,0])
P2 = sigma([13,14,...,31,0,1,...,12])
P3 = sigma([0,2,...,30,1,3,...,31])
```

Each root draws its rotation independently. Within a root each four-probe
block is balanced; across iid roots the rotation is balanced only in
expectation and realized counts are reported. Alias classes and strata are
finite package arrays, their IDs exclude `/` and NUL and are byte-unique, and
no CLI seed override or runtime-created domain exists.

The required future deterministic interfaces are exactly:

```text
python -m organism_v6.m_core_v7.materialize \
  --package-manifest <package_manifest.json> \
  --cohort TEXT|DEV|CONF --out <empty-directory>

python research_loop/checks/check_m_core_v7.py \
  --package-manifest <package_manifest.json> \
  --bundle <materialized-directory> --out <checker_receipt.json>
```

No additional seed, root, condition, role, output-policy, or permissive flag is
legal. The materializer refuses a nonempty output directory and emits exactly
the roots and files named by the selected MaterializedCohortBundleManifest.
The independently authored checker may import neither materializer/generator
modules nor generated constants; it reconstructs the typed hashes/draws,
aliases/handles, root geometry, tables, mounts/controls, compiler outputs,
bitmaps, state machine, Merkle addresses, and root/cohort receipt coverage from
the final package alone. A second run over the same inputs must be byte-exact.

### 2.3 Root variables and childhood evidence

Hidden audit-only root bits are `b,z`; `h` is a presealed intervention selector
with both h0 and h1 potential branches materialized in every root. Eight lanes contain:

```text
2 preassigned useful lanes: joint/left/right/nuisance = 1/0/0/0
3 left decoys:              1/1/0/0
3 right decoys:             1/0/1/0
```

The useful unordered pair is uniform among 28 pairs; A/B order is an
independent bit. `u_D` is uniform over its two members. `dream_shift` is uniform
1..7 and `pi(i)=(i+dream_shift) mod 8`. All endpoint syntax, action counts,
byte/token lengths, and displayed trial types are matched.

The child completes all 32 ablation actions/outcomes. It then sees eight lanes
and 28 `PairCandidate`s, each binding one selection action to its canonical two
lane members. A child model turn must emit exactly one selection action. The
selected action and two decoded lanes are stored; success requires recovery of
the preassigned evidence-indicated pair. Only after that turn is sealed does
the environment reveal a disjoint support fixture and eight typed support
slots: selected lane A/B x JOINT/LEFT/RIGHT/NUISANCE. Both lanes must reproduce
1/0/0/0. The compiler never infers slot roles from array order.

### 2.4 Source, B, C, and D geometry

The child's source evidence is a within-situation crossed contingency:

```text
b=0: L=[T,T,T,O], R=[T,O,O,O]
b=1: L=[T,O,O,O], R=[T,T,T,O]
```

SOURCE_DERANGED presealed projection assigns sorted T donor outcomes to
L0,L1,R0,R1 and O donors to L2,L3,R2,R3, yielding truthful 2/4--2/4 presented
counts while preserving eight authentic donor turns and T/O marginals. Donor
mapping is audit-only.

B has two public goals with one differing goal field:

```text
S_B --a_u--> U_u --[b_u,c0]--> C_B --t_target--> target
FULL: 3 READ, 4 actions; ATOMS: 4 READ, 4 actions
```

Their complete ActorEpisodeInput bytes share public-pair handle, actor/decode,
catalog, surfaces, and all bytes preceding the first difference under `/goal/`.
A registered GoalPairByteCutReceipt binds both hashes, exact first byte offset
and JSON pointer, and a complete bitmap whose set bits are all under `/goal/`.
The FULL-mounted goal-cue swap changes only `goal.route_cue`; its registered
map closes only over the resulting request/return/action/observation descendants
while target/terminal/catalog/tick/RNG bytes stay fixed.

C asks SOURCE_INVERSE for desired T/O. Its live experiment menu has L actions
E0/E1 and R actions E2/E3. After source choice is committed, a public
ExperimentLaw is revealed:

```text
b=0: E0=H, E1=ONE_MINUS_H, E2/E3=NUISANCE
b=1: E2=H, E3=ONE_MINUS_H, E0/E1=NUISANCE
```

This reveal occurs after source choice, so it cannot supply that choice.
OutcomeCodebook simultaneously maps the two possible public outcome handles to
bits 0/1. The same reveal exposes exactly two neutral public template
references `(hypothesis_selector,row_handle)`; their answer-bearing payloads
remain compiler-only. The actor declares one experiment and, for
H/ONE_MINUS_H only, its predicted outcome under h0/h1 plus that public
row-handle map. Dispatch is restricted to
the already selected family and cites the declaration. The world then emits y:

```text
H -> y=h; ONE_MINUS_H -> y=1-h; NUISANCE -> y=z
```

The NEW compiler can solve h from public law, dispatch, and outcome bit without
seeing b,h,z. It rejects nuisance relations.

D is:

```text
U_uD --[b_uD,c0]--> C_D --n_h--> D
2 READ, 3 actions
```

C_B/C_D and every phase are lifted into distinct states. No action family is
available outside its registered phase.

## 3. Visibility, model-turn custody, reset, and provenance

### 3.1 Capability boundary

| object | child/actor | reader model | compiler | endpoint | audit/checker |
|---|---:|---:|---:|---:|---:|
| current public input/transcript/menu/law/catalog | yes | request subset | named phase input | trace hash | yes |
| candidate row | after FOUND only | one candidate | no | cited hash | yes |
| hidden b/h/z, roles, expected answer | no | no | no | validation service | yes |
| mount/control/carrier/availability/order/timing | no | backend only | no | no | yes |
| donor map/provenance/condition/device | no | no | no | no | yes |

The compiler-facing source projection has one condition-neutral
`PresentedSourcePair` shape in FULL and SOURCE_DERANGED: presented action,
public outcome category, and neutral citation. It contains no authenticity,
derived, donor, transform, condition, or receipt field. The checker validates
projection provenance separately in `ProvenanceReceipt`; the compiler cannot
dereference it.

### 3.2 Every decision is a model turn

Every child or deployment READ, action, pair selection, and declaration has one
`ModelTurnReceipt`. It binds:

- exact pre-turn `ActorEpisodeInput` and accumulated public transcript hashes;
- actor/model, tokenizer, renderer, chat-template, engine, runtime, immutable
  birth checkpoint/state, process instance, episode, and turn ordinal;
- exact continuation bytes, token IDs, stop reason, and complete inference draw
  ledger;
- parser source/config/input hashes, parse status `EXACTLY_ONE`, and one closed
  `ParsedDecision` (`READ`, `ACTION`, `PAIR_SELECTION`, or `DECLARATION`);
- logical start/end ticks and the resulting public-object hash.

The public object cites `model_turn_handle`; its parsed payload must be
byte-equivalent to the event fields. A synthesized event, extra parsed object,
discarded continuation, parser repair, or hidden expected-trace path is
`ROOT_MALFORMED_ACTION`. Autonomous observations/compiler events never cite a
model turn and use distinct types.

### 3.3 Fresh-process reset custody

Every episode has a `ProcessBirthReceipt` emitted by the launcher before its
first operation. It binds role, unique process instance, spawn nonce, immutable
birth checkpoint, role-appropriate actor/reader/writer binding, empty-context
bytes, initial model state, and first-operation handle. For CHILD or
DEPLOYMENT_ACTOR, `ResetReceipt` links that birth receipt to the first
ModelTurnReceipt and proves there is no predecessor transcript, parent text,
raw childhood text, adapter other than the mounted carrier, filesystem/cache
capability, or reused process. A `ProcessTeardownReceipt` closes the process
after the terminal frame. Process handles cannot repeat. Reset failure is
`ROOT_INTERFACE_FAILURE`, never a favorable endpoint.

### 3.4 Public and audit provenance

Authentic action/outcome leaves are a model-turn-cited committed action followed
at a greater tick by a public observation citing that action. SOURCE_DERANGED
and DREAM_DERANGED retain donor trees and total deterministic transform
receipts under audit only. Positive rows have authentic provenance; fitted
corrupt rows have derived-control provenance. Training and actor-visible row
bytes expose neither class. Every compiler input projection has a checker
receipt binding it to its audit tree, but that receipt is not a compiler input.

## 4. Rows and four compiler phases

### 4.1 Row modes

`ATOM` authorizes one action. `SEQUENCE` authorizes exactly two ordered actions
and maintains a cursor across the intervening public observation; any READ,
wrong, repeated, expired, or extra action invalidates it. `CHOICE_TABLE` has two
action/count/total=4 entries and authorizes either action once. Each row has a
stable public row handle that is not content-addressed; payload interventions
keep it fixed and the audit binds the alternate content hash.

### 4.2 Pure public compilers

Every compiler invocation/decision has an event handle, exact input hash,
logical tick, and cited prerequisite handles. Decisions occur later than all
prerequisites. The phase inputs are disjoint and root-local:

1. **SOURCE:** eight neutral `PresentedSourcePair`s, T/O desired handles, and
   50 complete templates (25 L/R count pairs x two outcomes). Count only the
   presented bytes and copy the two exact templates. Ties remain ties.
2. **LINK:** authenticated selection event, later reveal, and eight
   `SupportBinding`s forming an exact bijection over two selected lanes x four
   trial kinds. Admit both link templates iff both profiles are 1/0/0/0.
3. **PAD:** one authenticated p0 action and later Q observation. Emit the one
   private, disconnected, gradient-bearing PAD template.
4. **NEW:** canonical authentic neutral source projection, actual source-choice
   event, complete menu, later ExperimentLaw/OutcomeCodebook reveal,
   model-turn-cited declaration, declaration-cited dispatch, later public
   outcome, and two `NewRowTemplate`s labeled selector 0/1. Recompute preferred
   family from counts; require source/dispatch in it; require H/ONE_MINUS_H;
   validate declaration against the law; decode y; solve singleton h; copy only
   the correspondingly labeled template. NUISANCE gives NO_ADMISSION.

Template sets are revealed at fixed times: SOURCE/PAD before their evidence,
LINK only after selection is sealed, and both NEW alternatives with the public
law after source choice but before declaration/outcome. Templates are complete
and have no fill fields. Compilers cannot access endpoint, role, hidden bit,
condition, mount, provenance, or expected-admission bytes.

### 4.3 Same-handle inference interventions

`SOURCE_READ_SWAP_C` changes only the two count payload bytes in the FULL source
row. B/D old-link swaps change only ordered-action payload and mechanically
forced destination/content-hash/frame-pad descendants. D new-row swap changes
only n_h to n_(1-h) and forced descendants. Row handle, query/key, action mode,
citations, status, frame length/tick, and unrelated bytes remain identical.
Intervention identity is audit-only. Complete difference bitmaps are the
transitive closure of the named payload fields in the typed graph; an extra bit
is `ROOT_INTERVENTION_MISMATCH`.

## 5. Reader, mounts, state machine, and controls

### 5.1 Root-scoped mount projection

One closed `CarrierId` and `ControlId` is used everywhere. Every episode mounts
one root-local `MountInstance`, containing base carrier, optional inference-only
control, and a complete candidate projection for each legal request. Each
projection has exactly 32 slots. Ordinary slots map to registered rows.

A CUT replaces the target candidate **before scoring** with a presealed
schema/length/token/work-matched nonmatching filler in the same slot. A payload
swap substitutes same-handle alternate content before scoring. NO_CARRIER uses
32 fillers. The reader model sees only prompt+request+one candidate per call;
it never sees mount, carrier, control, availability, or slot provenance. Backend
receipts bind all scorer inputs to the mount projection. A filler false positive
is `ROOT_UNAVAILABLE_FOUND`, not silently filtered. This makes charged cut MISS
traces possible without a reader side channel.

`RootCanonicalReturns` and availability are keyed by
`(root_namespace_handle,mount_instance_handle,request_fingerprint)`. No flat or
unscoped lookup exists.

### 5.2 Query union and exact reader

The only requests are:

```text
ROUTE_BY_CUE(B): actual route cue
ATOM_SUCCESSOR(B): current state
LINK_SUCCESSOR(B|D): current state
TERMINAL_TO_TARGET(B): actual target
SOURCE_INVERSE(C): actual desired outcome
NEW_SUCCESSOR(D): current state + actual target
```

Each carries phase, public goal/state, candidate schema, call ordinal, and reads
remaining. The checker independently projects it from ActorEpisodeInput/state.
Ordinary B has 3 READ; legal B_ATOMS has 4; C probe/live has 1; D has 2.

The reader deterministically scores all 32 projected candidates. A unique
threshold+margin pass returns FOUND; none or a tie returns MISS. BLOCKED occurs
only at zero budget without scorer calls. RPC returns are fixed-size. A formal
BFS over the complete request/mount/transition tables must prove FULL minimum
3, ATOMS minimum 4, FULL_NEW minimum 2, every cut endpoint unreachable, and no
adaptive READ/MISS/BLOCKED/cursor bypass.

### 5.3 Exact RPC and actor-observable frames

`ReaderBinding` binds scorer model/prompt/aggregation/threshold/margin/order
test plus clock source, scorer count=32, worker image, frame algorithm, and
qualification spec—not a result receipt. `RpcMachine` binds:

```text
ASCII("MCRPC7\0")                     7 bytes
U32BE(payload_length)                 4 bytes
payload = JCS(MemoryReturn)+LF
pad = SHAKE256("MCRPC7-PAD\0" || request_fingerprint,
               16384-11-payload_length)
```

All frames are 16384 bytes and release at logical request tick+1. Overflow is
`GLOBAL_SCHEMA`; physical deadline overrun is `ROOT_RPC_OVERRUN`, the actor
never resumes, and no branchable callback/exception/timing byte exists.
Actor-observable frames are only EpisodeInput, RPC, PublicObservation,
ExperimentLawReveal, and EpisodeTerminal.

### 5.4 Typed transitions and terminal

`RootTransitionTable` is a closed union:

- `ActorActionTransition`: state + authorized action -> state/observation;
- `AutonomousOutcomeTransition`: dispatch + hidden potential-outcome branch ->
  public observation (hidden selector available only to environment/audit);
- `CompilerTransition`: invocation + decision -> admitted/no-admission state;
- `TerminalTransition`: state/failure -> typed `EpisodeTerminal` frame.

Every reachable state exposes exactly 32 token-isomorphic action surfaces.
Selection exposes 28 pair actions plus four invalid surfaces. Autonomous
transitions are never encoded as pretend actions. Exact successful traces are:

```text
B FULL: ROUTE/read,a; LINK/read,b,c; TERMINAL/read,t       3R/4A
B ATOMS: ROUTE/read,a; ATOM/read,b; ATOM/read,c;
         TERMINAL/read,t                                  4R/4A
C probe: SOURCE/read,L|R                                  1R/1A
C live: SOURCE/read,L|R; law reveal; DECLARE; ACT E; y;
        compiler invocation/decision                     1R/2A
D FULL: LINK/read,b,c; NEW/read,n_h                        2R/3A
```

The four C probes are not chosen by an implementation. For probe ordinal
`k=0..3`, desired outcomes are exactly `[T,O,T,O]`, candidate order is
`P[(candidate_rotation+k) mod 4]`, and the correct source action is:

```text
              desired T   desired O
b=0              L           R
b=1              R           L
```

FULL presents the corresponding 3/1 winner; SOURCE_DERANGED presents the
same two public actions at 2/2. Each arm executes four fresh episodes. A probe
endpoint is one exactly when the committed source action equals the table,
not when it merely follows either CHOICE_TABLE option. Hence `mean4` below is
the arithmetic mean of these four binary endpoints and all eight source-arm
episodes are mandatory. Candidate-order rotation never changes the truth.

For C live, the source row, desired outcome, preferred-family truth table,
menu, law, declaration, dispatch, public outcome, and compiler decision are
all prelisted in RootCellRoster for each h0/h1 twin. SOURCE_READ_SWAP_C uses
the same FULL carrier and changes only the registered 3/1 count payload into
1/3; its exact expected trace selects the opposite family, reaches NUISANCE,
obtains NO_ADMISSION, and ends with VALID_SWAP_ENDPOINT. No scorer or endpoint
code derives source correctness from the carrier label.

### 5.5 Exact 21 controls

```text
S1_OFF_B, S1_OFF_C, INTERFACE_CANARY, NONHARM_PANEL,
GOAL_CATALOG_NO_CARRIER, FULL_GOAL_CUE_SWAP_B,
CATALOG_PERMUTE_P0, CATALOG_PERMUTE_P1,
CATALOG_PERMUTE_P2, CATALOG_PERMUTE_P3,
B_LINK_CUT, B_LINK_PAYLOAD_SWAP, SOURCE_READ_SWAP_C,
D_OLD_LINK_CUT, D_NEW_ROW_CUT,
D_OLD_LINK_PAYLOAD_SWAP, D_NEW_ROW_PAYLOAD_SWAP,
NO_SLEEP2, FULL_OLD_PLUS_PAD_CONTROL, TEXT_FULL, TEXT_ATOMS_READ4
```

`GOAL_CUE_SWAP` is a literal mutation kind: mount FULL, alter only
`goal.route_cue_handle`, and allow only its typed causal descendants. Candidate
orders contain `ControlId`, never unrelated handles. `FULL_OLD_PLUS_PAD` is the
only PAD carrier spelling; the control ID remains
`FULL_OLD_PLUS_PAD_CONTROL`. Each root has 21 concrete ControlSpecs, each with
one to 32 cases and exact mounted instance, input, mutation, event hashes,
reads/actions, terminal, endpoint, and failure code.

Expected control endpoints are:

| controls | exact result |
|---|---|
| S1_OFF_B/C, GOAL_CATALOG_NO_CARRIER | first charged MISS, 0A, VALID_READ_MISS |
| interface/nonharm | exact registered aggregate pass, NONE |
| goal-cue swap | redirected B success, NONE |
| catalog permutations | success invariant, NONE |
| B/D cuts | charged MISS at named row, VALID_CUT_ENDPOINT |
| B/D payload swaps | same-handle wrong legal payload/action, VALID_SWAP_ENDPOINT |
| source count swap | opposite source, nuisance, NO_ADMISSION, VALID_SWAP_ENDPOINT |
| NO_SLEEP2 | FULL_OLD old FOUND/two actions, NEW MISS, VALID_READ_MISS |
| PAD control | FULL_OLD_PLUS_PAD old FOUND/two actions, NEW MISS, VALID_READ_MISS |
| TEXT FULL/ATOMS | exact success, NONE |

Any mutation/count/state-table deviation is `ROOT_INTERVENTION_MISMATCH`.
A correctly mounted control in which the actor makes a different legal choice
receives its corresponding `VALID_*` endpoint and makes the component gate
false; it is not reclassified as infrastructure failure.

## 6. Noncircular qualification and matched writing

### 6.1 Qualification comes before execution

Immutable `WriterBinding` and `ReaderBinding` contain hashes of closed
qualification **specifications**, fixtures, model/runtime, renderer/parser, and
thresholds. They contain no future result-receipt hash. Later qualification
receipts bind the already-addressed package, binding, specification, exact
fixture results, and execution cost. This direction is acyclic:

```text
package -> binding/spec -> later qualification receipt
```

The package is `UNQUALIFIED` until both receipts pass. No TEXT, model reader
acceptance, or M fit may start earlier.

Writer qualification has these eight mandatory cases:

1. ordinary ATOM render/write/extract;
2. two-action SEQUENCE render/write/extract;
3. informative 3/1 CHOICE_TABLE;
4. truthful 2/2 CHOICE_TABLE;
5. NEW selector-0 row;
6. NEW selector-1 row;
7. private gradient-bearing PAD row; and
8. cumulative old+new deck with exact old preservation and both row types
   independently extractable.

Each case requires exact model-turn/tensor/parser custody, registered absorption
threshold, interface canary, and byte-exact row extraction. Failure bars the
protocol; no current gateway is silently promoted to W*.

Reader qualification has these eight mandatory mounted-candidate cases:
positive ATOM, positive SEQUENCE, informative CHOICE_TABLE, tie CHOICE_TABLE,
positive NEW, CUT-with-filler MISS, same-handle payload-swap FOUND, and
NO_CARRIER/fillers MISS. It additionally requires four candidate orders,
unavailable-filler false-positive count zero, fixed RPC bytes, and exact margin
behavior. Qualification uses the identical runtime and mount projection as M.

### 6.2 Matched S1/S2 decks

The qualified writer W* is inherited exactly; v7 assumes no particular
paraphrase/view recipe. Its binding fixes rank, learning rate, optimizer,
steps, renderer, masks, preservation mix, and visit schedule after
qualification.

```text
S1 FULL_OLD:
  authentic 3/1 source tables + authentic selected links +
  common grounded route/terminal foundation rows

S1 SOURCE_DERANGED_OLD:
  truthful presented 2/2 source tables + identical links/foundations

S1 DREAM_DERANGED_OLD:
  pi links + identical authentic source/foundations

S2 FULL_NEW_H0: exact FULL old deck + admitted n0
S2 FULL_NEW_H1: exact FULL old deck + admitted n1
S2 FULL_OLD_PLUS_PAD: exact FULL old deck + grounded private d_pad
```

All six reconstruct from immutable birth. Each S1 triplet uses one physical
device in sterile sequential processes and a presealed random condition order;
likewise S2. Within a triplet, initial checkpoint, optimizer state/schedule,
device/image/driver/runtime/health, slot/batch ordering, dropout/data-worker
draws, tensor shapes, positions, attention/loss masks, supervised/total tokens,
forward/backward/update counts, and all stage-keyed RNG counters are equal.

For every paired example, `AllowedTensorDifference` names only the row payload
fields permitted to differ. Input IDs, labels, and resulting content hashes may
differ only at the closed bitmap and forced descendants; all masks/work are
bit-identical. PAD is an actual supervised row supported by the child's p0->Q
turn, not null padding or an ungrounded token. A mismatch is
`ROOT_WORK_MISMATCH` and makes that component invalid.

## 7. Endpoint custody, component gates, and exact results

### 7.1 Structural seal before endpoint open

Each structurally completed presealed `CellSpec` has exactly one mandatory
`EndpointReceipt` even when the valid endpoint bit is zero. A cell that selects
a GLOBAL/ROOT structural failure has only its StructuralTraceReceipt and makes
the root an AbortedRootResult; it cannot fabricate an endpoint receipt. After
the StructuralTraceReceipt selects NONE, the isolated endpoint service computes
the result from that committed trace and the presealed validation function,
writes the result bytes into a separate `SealedEndpoint`, and publishes only
its commitment. A
`StructuralTraceReceipt` binds cell, input, complete public trace **without
endpoint bytes**, turns/parses/RPC/mount/control/compiler receipts, and the
deterministic structural FailureDecisionReceipt. If any GLOBAL/ROOT trigger is
selected, the endpoint is never opened. Otherwise an `EndpointOpenReceipt`
cites both the structural receipt and later seal, then a later hash-chain event
opens the committed
endpoint bytes, and the scorer emits:

```text
(trace_valid=1, endpoint=1, NONE), or
(trace_valid=1, endpoint=0, one registered VALID_* code)
```

The impossible `(0,1)` is rejected. EndpointReceipt binds cell ID, trace/input/
environment/mount hashes, seal/open receipts, endpoint bit, and exact code.
Positive and control endpoints therefore cannot be omitted or replaced by an
anonymous blob.

CellSpec's canonical endpoint/code describes the registered canonical trace;
its allowed-observed-code vector contains NONE plus the eight VALID codes in
FailureDecisionTable order. A model choosing a wrong action is a valid zero and
makes the relevant component gate false; it is not ROOT_INTERVENTION_MISMATCH.
That root code is reserved for a mismatch in the mounted mutation, typed state
machine, fixed budget, or registered intervention closure.

### 7.2 Compiler and root-wide receipts

Every compiler invocation has a `CompilerCaseReceipt`. A root's mandatory
`CompilerAggregateReceipt` contains the exact presealed compiler-cell roster,
case receipts, counts by SOURCE/LINK/PAD/NEW and ADMIT/NO_ADMISSION, prefix
comparisons, and one aggregate bit. It fails on missing/extra invocation,
wrong template selector, forbidden input, causal-order mismatch, or output not
copied from the allowed template set.

EpisodeAuditEnvelope is episode-local: actor input, model turns, public trace,
RPC/scorer, compiler cases, structural/endpoint, and provenance hashes only.
RootAuditReceipt holds root-wide checker, ACL, BFS, clock, schedule, fit/work,
interface/nonharm, extraction, reader-acceptance, PAD-work, and inference-match
objects. Component gates and indicator isolation remain in ScienceRootResult.
RootResultBundle contains the typed process/reset/teardown, model-turn, public-
trace, runtime-mount, scorer/RPC, seal, structural, and endpoint-open objects whose hashes
appear in episode envelopes. QualificationResultBundle likewise contains its
typed process/model/tensor/scorer/RPC objects. Thus every gate input resolves
to a typed object inside the sealed result; the episode object never embeds a
root-wide receipt, eliminating duplication.

### 7.3 Noncompensatory component gates

`RootGateRosters` lists typed `GateInputSpec`s for every G gate. Each input has
one exact role, closed root type, future object identity, and required pass
value, but no future result digest. Each later `GateInputReceipt` binds that
requirement to the actual typed object's digest and observed bit.
`ComponentGateReceipt` must cover the literal roster exactly; anonymous digest
vectors and future-hash package cycles are forbidden.

- `G_S`: FULL and SOURCE fits valid/common; exact 3/1 versus 2/2 extraction;
  all eight T/O probes valid; orthogonal rows, interface, and nonharm preserved.
- `G_M`: FULL and DREAM fits valid/common; both selected authentic versus pi
  links extracted; both B goals/control swap valid; orthogonal rows preserved.
- `G_U`: FULL valid plus S1_OFF B/C exact charged MISS traces under common input
  and inference RNG.
- `G_W`: all S2 fits valid/common; exact old preservation; n0/n1/PAD extraction;
  both h FULL_NEW and both h PAD D cells valid.
- `G_F`: both h positive D traces and all separate old/new CUT and same-handle
  payload swaps complete as registered VALID failures.
- `G_R`: every package/rematerialization/checker/qualification, child-turn and
  selection/support, compiler, provenance, ACL, BFS, RPC/clock, reset,
  interface/nonharm, goal/candidate-order, component, cut/swap, and isolation
  receipt passes. Later success cannot compensate.

Raw contrasts exist only when their gate is one:

```text
S = mean_k=0..3(Y_C_FULL,k) - mean_k=0..3(Y_C_SOURCE_DERANGED,k)
M = min(Y_B_FULL,g0-Y_B_DREAM_DERANGED,g0,
        Y_B_FULL,g1-Y_B_DREAM_DERANGED,g1)
U = min(Y_B_FULL,g0-Y_B_OFF,g0,
        Y_B_FULL,g1-Y_B_OFF,g1,
        mean_k=0..3(Y_C_FULL,k)-mean_k=0..3(Y_C_OFF,k))
W = min(Y_D_FULL_NEW_H0,h0-Y_D_FULL_OLD_PLUS_PAD,h0,
        Y_D_FULL_NEW_H1,h1-Y_D_FULL_OLD_PLUS_PAD,h1)
F = minimum of the eight differences obtained by pairing each FULL_NEW_Hh
    endpoint, h in {0,1}, with its four registered D old-cut, new-cut,
    old-payload-swap, and new-payload-swap endpoints
R = 1 iff every literal G_R requirement and all five component gate receipts
    S/M/U/W/F pass; otherwise 0

I_S = 1[G_S=1 and S>0]
I_M = 1[G_M=1 and M>0]
I_U = 1[G_U=1 and U>0]
I_W = 1[G_W=1 and W>0]
I_R = 1[G_R=1 and R=1]
```

S/M/U/W use `NumericComponentResult{gate,contrast,indicator}`. R uses
`RComponentResult{gate,r_value,indicator}`; it has no fictitious numeric
contrast. F is a separately typed diagnostic gate/result. Invalid/missing
positive or control cells make the relevant indicator zero, with raw contrast
null. Only a completed structurally valid `VALID_*` control supplies intended
endpoint zero.

### 7.4 Exact TEXT root rule

TEXT is a supplied-row, inference-only feasibility ceiling and never enters a
trained condition or confirmatory statistic. `T_r=1` exactly when all of these
hold in that root:

- all foundation/source/ablation/PAD child actions and later observations are
  canonical, turn-custodied, and complete;
- the child authenticates the evidence-indicated pair before support/template
  reveal and the fresh support compiler admits both links;
- TEXT_FULL, source-tie, DREAM-deranged, TEXT_ATOMS, both NEW selectors, and
  PAD mounts expose exactly their registered rows with zero unavailable FOUND;
- TEXT_FULL solves both B goals in three reads, TEXT_ATOMS in four, and the
  FULL-mounted goal-cue intervention reaches its registered redirected target;
- all four C probes, both authentic live-C outcome twins, and both live count-
  swap twins produce their exact admitted/rejected traces;
- both text NEW rows solve their D twins, while each cut, payload swap,
  FULL_OLD_PLUS_PAD, and NO_SLEEP2 case gives its registered completed valid
  failure; and
- every package/checker, model-turn/reset, schema, ACL, provenance,
  compiler/prefix/projection, BFS, RPC/clock, interface, and gate receipt in the
  literal TEXT roster passes.

No mean score or partial compensation is permitted. A TEXT root's actor and
reader work is represented by ExecutionAttemptReceipts and every device/CPU/
queue/reset interval is included once in the program CostLedger. TEXT has zero
FitAttemptReceipts and therefore exactly zero *fit* device time; this does not
mean zero total device time.

## 8. Complete program state machine and statistics

### 8.1 Hash-chained scheduling

`program_machine.json` is a finite transition table over:

```text
PACKAGE_CHECK -> QUALIFICATION -> TEXT_INITIAL ->
TEXT_EXTENSION? -> TEXT_FINAL_GATE -> DEV_D1D2_S1 -> DEV_D1D2_S2? ->
DEV_LATE_ROOTS? -> DEV_MECHANICS_GATE -> CONF_ROOTS? ->
TEST_S? -> TEST_M? -> TEST_U? -> TEST_W? -> TEST_R? -> COMPLETE
```

Every `ScheduleEvent` includes event handle, state before/after, typed named
input refs, decision, logical and monotonic tick, and preceding event hash.
Its address is `SHA256(JCS(event)||LF)` and is not a field of the event, which
avoids a self-hash. A downstream `OpenEvent` (file access, allocation, or launch)
cites the authorizing schedule-event hash and has a later tick. The append-only
head is stored in ProgramResultIndex. Reordering or backfilling is
`GLOBAL_PROTOCOL_MUTATION`.

Exact decisions:

1. Package/checker and both qualification receipts must pass or STOP.
2. Run TEXT T1..T4. 0/4 or 1/4 -> STOP; 4/4 -> TEXT pass; 2/4 or 3/4 -> run
   T5..T8 and pass only at >=6/8. Failed roots are never replaced. TEXT is not
   confirmatory evidence.
3. Only TEXT pass opens DEV. Run D1/D2 S1 (6 fits). Open both S2 triplets iff
   `Q_S1(D1)&Q_S1(D2)=1`; otherwise STOP.
4. Open D3..D8 iff `I_R(D1)&I_R(D2)=1`. Each later root runs S1 and its S2 iff
   its own Q_S1=1; a failed later root neither stops nor replaces another.
5. DEV mechanics pass iff >=6/8 I_R=1. Only that pass opens CONF.
6. CONF has 16 fixed fresh roots, no replacement/extension/retry. Every root
   runs S1 and runs S2 iff Q_S1=1; skipped downstream indicators are zero.
7. Test S->M->U->W->R in fixed order, stopping rejection at first
   non-rejection. Later component outputs are descriptive/post-stop.

The fourteen ProgramTransitionRules contain exactly these branch outcome sets, so a
binary `true/false` implementation cannot silently collapse the TEXT ternary:

| kind | predicate outcomes |
|---|---|
| PACKAGE_GATE | PASS, FAIL |
| QUALIFICATION_GATE | PASS, FAIL |
| TEXT_EXTENSION_GATE | FAIL for 0/4 or 1/4; EXTEND for 2/4 or 3/4; PASS for 4/4 |
| TEXT_FINAL_GATE | PASS for initial 4/4 or extended >=6/8; FAIL otherwise |
| DEV_S1_GATE | OPEN_S2 iff both D1/D2 Q_S1; FAIL otherwise |
| DEV_D1D2_R_GATE | OPEN_LATE_ROOTS iff both I_R; SKIP_LATE_ROOTS otherwise |
| DEV_ROOT_S2_GATE | OPEN_S2 iff that late root Q_S1; SKIP_S2 otherwise |
| DEV_MECHANICS_GATE | OPEN_CONF iff >=6/8 I_R; SKIP_CONF otherwise |
| CONF_ROOT_S2_GATE | OPEN_S2 iff that root Q_S1; SKIP_S2 otherwise |
| TEST_S_GATE | REJECT -> TEST_M; NONREJECT -> COMPLETE |
| TEST_M_GATE | REJECT -> TEST_U; NONREJECT -> COMPLETE |
| TEST_U_GATE | REJECT -> TEST_W; NONREJECT -> COMPLETE |
| TEST_W_GATE | REJECT -> TEST_R; NONREJECT -> COMPLETE |
| TEST_R_GATE | REJECT -> COMPLETE; NONREJECT -> COMPLETE |

Each branch's state/decision/open kind is literal in ProgramMachine and the
ScheduleEvent repeats the selected predicate outcome. Any missing, extra, or
inapplicable branch is GLOBAL_PROTOCOL_MUTATION.

`TEXT_FINAL_GATE` and `DEV_MECHANICS_GATE` are literal StoppingKinds.
Upstream-failed cohorts are represented by `UnscheduledCohortResult`; a
presealed but unrun root is `UnscheduledRootResult` with no fabricated Q,
component, attempt, or cost receipt. ProgramResultIndex holds a produced,
skipped, or globally invalid disposition for every cohort rather than requiring
a nonexistent manifest.

### 8.2 Q_S1 and confirmatory law

Q_S1 is a typed Boolean over a literal gate roster: all three S1 fits/work/
extraction/canary/nonharm valid, G_S=G_M=G_U=1, I_S=I_M=I_U=1, FULL solves
both B goals, and every S1-only control/compiler/provenance/ACL/RPC/reset input
passes. QS1Receipt contains typed GateInputRefs, roster hash, schedule event,
and q bit; no anonymous hashes or self-asserted “emitted before” bit.

CONF root seeds are iid uniform; every root is generated by the identical
measurable root function (root index is a label only), and every execution-noise
value is iid from one registered distribution, independent of all root seeds
and immutable common assets. Every complete indicator uses the identical
component function. Any known or uncertain cross-root cause is
`GLOBAL_SHARED_STATE` or `GLOBAL_UNKNOWN` and produces no test. This explicit
iid assumption—not hashing—is the basis for Binomial(16,p).

For each component test `H0:p<=.5`, the exact one-sided tail is used. Rejection
requires K>=12 because `sum_{j=12}^{16} C(16,j)=2517`, so
`p=2517/65536=.0384063720703125`; K=11 gives 6885/65536. Report the one-sided
95% Clopper-Pearson lower bound:

```text
L(0)=0
L(K)=Beta^-1(.05;K,17-K), 1<=K<=16
```

All decimal/binary64 encodings follow Section 11; `L(0)` is positive-zero bits.

## 9. Deterministic failures

`failure_decisions.json` exhaustively maps every finite `FailureTrigger` to one
FailureCode, scope, and strict priority. An execution collects all triggered
predicates from typed receipts; the lowest numeric priority wins. No default
choice is left to the implementation. Exact important mappings are:

| trigger | code |
|---|---|
| package member/Merkle/schema/checker mismatch | corresponding GLOBAL_PACKAGE_MEMBER/MERKLE/SCHEMA/CHECKER |
| tokenizer, alias/handle collision, tensor static shape, RPC payload overflow | GLOBAL_SCHEMA |
| capability/ACL leak | GLOBAL_CAPABILITY |
| cross-root mutable or execution cause | GLOBAL_SHARED_STATE |
| common triplet device/runtime nuisance mismatch | GLOBAL_COMMON_NUISANCE |
| uncertain ownership/release/root boundary | GLOBAL_UNKNOWN |
| fit crash/timeout | ROOT_FIT_CRASH / ROOT_FIT_TIMEOUT |
| runtime tensor/work mismatch | ROOT_WORK_MISMATCH |
| RPC physical overrun | ROOT_RPC_OVERRUN |
| unavailable/filler FOUND | ROOT_UNAVAILABLE_FOUND |
| malformed/uncustodied parse/action | ROOT_MALFORMED_ACTION |
| bad named intervention | ROOT_INTERVENTION_MISMATCH |
| interface trace failure | ROOT_INTERFACE_FAILURE |
| writer commit canary failure | ROOT_CANARY_FAILURE |
| nonharm bound failure | ROOT_NONHARM_FAILURE |
| valid endpoint misses/wrong/cut/swap | corresponding VALID_* code |

The full table has one row per trigger, not only this readable subset. Global
codes outrank root codes, root codes outrank valid endpoint codes, and within a
scope the immutable table priority decides. NONE is selected only with an empty
trigger set and successful opened endpoint.

`FailureDecisionReceipt` binds all evaluated trigger receipt hashes, triggered
set, priority-table hash, selected code, and scope. `CohortFailureReceipt`
records a global code, the schedule head at detection, finalized root manifests,
unopened roots/cells, and null scientific test. Root bundles after a global
failure contain only work completed before that schedule head; nothing is
imputed.

## 10. Deduplicated cost ledger

One program-level `CostLedger` owns every physical interval exactly once.
Fit/actor/reader/qualification attempts reference interval handles; they do not
embed intervals. Intervals are half-open `[allocation_ns,release_ns)` and bind
lease, device UUID, image, driver, runtime, exclusive owner, category, deck,
attempt, clock source, and status. Queue/reset/serialization/CPU intervals also
have status and unique handles.

For each `(lease,device)`, union all device intervals. `DeviceUnionSegment`
binds its exact contributing interval and attempt sets, contributing categories
and statuses, image/driver/runtime, and deterministic attribution:

- one category/status -> that value;
- more than one -> MIXED, retaining the complete contributor sets.

`CostBucket` binds category, status, deck, device, image/runtime, contributing
segment/interval handles, attempt count, and nanoseconds. Buckets are a
nonoverlapping partition of union segments. CPU and noncompute ledgers are
reported separately and never converted to device seconds. Crashed, timed-out,
aborted, and partial launches are included through release.

Cost output is `ONEOF[ValidCostSummary,InvalidCostSummary]`. Valid has all
numeric totals and proofs. If any ownership/release boundary is absent or
ambiguous, `InvalidCostSummary` carries `GLOBAL_UNKNOWN`, offending handles,
and **null** totals/buckets; there is no silent zero, scientific test, or
numeric cost total.

## 11. Normative closed schemas

### 11.1 Algebra and primitives

This algebra translates deterministically to Draft-2020-12 JSON Schema.
`OBJ` has exactly the required fields and `additionalProperties:false`.
`VEC[n,T]` is exact length; `VEC[a..b,T]` inclusive; `OPT[T]` is T or null;
`ONEOF` is JSON Schema oneOf; `CONST` and `ENUM` are literal. References must
resolve. Semantic constraints below are also package-bound checker rules.

```text
U53      = integer 0..9007199254740991
BIT      = integer enum 0,1
U64D     = decimal string 0..18446744073709551615, no leading zero
STRING   = UTF-8 string length 1..4096
HEX64    = lowercase 64 hex chars
F64HEX   = lowercase 16 hex chars encoding a finite IEEE-754 binary64;
           NaN/Inf forbidden; -0 normalized to +0; arithmetic is
           round-to-nearest-ties-to-even
HANDLE26 = 26 chars from [a-z2-7]
B64U     = unpadded RFC-4648 base64url
BLOB     = OBJ{bytes_b64u:B64U,byte_length:U53,sha256:HEX64}

CarrierId = ENUM[BIRTH,NO_CARRIER,FULL_OLD,SOURCE_DERANGED_OLD,
  DREAM_DERANGED_OLD,FULL_NEW_H0,FULL_NEW_H1,FULL_OLD_PLUS_PAD,
  TEXT_FULL,TEXT_ATOMS]
ControlId = ENUM[S1_OFF_B,S1_OFF_C,INTERFACE_CANARY,NONHARM_PANEL,
  GOAL_CATALOG_NO_CARRIER,FULL_GOAL_CUE_SWAP_B,
  CATALOG_PERMUTE_P0,CATALOG_PERMUTE_P1,CATALOG_PERMUTE_P2,
  CATALOG_PERMUTE_P3,B_LINK_CUT,B_LINK_PAYLOAD_SWAP,
  SOURCE_READ_SWAP_C,D_OLD_LINK_CUT,D_NEW_ROW_CUT,
  D_OLD_LINK_PAYLOAD_SWAP,D_NEW_ROW_PAYLOAD_SWAP,NO_SLEEP2,
  FULL_OLD_PLUS_PAD_CONTROL,TEXT_FULL,TEXT_ATOMS_READ4]
```

### 11.2 Package, build, generator, and materialization roots

```text
ManifestMember = OBJ{path:STRING,byte_length:U53,media_type:STRING,
  sha256:HEX64,json_root_type:OPT[STRING]}
PackageManifest = OBJ{v:CONST[mcore.v7],members:VEC[1..100000,ManifestMember],
  merkle_root_sha256:HEX64,entropy_seal_sha256:HEX64,
  expected_root_index_sha256:HEX64}
SchemaBinding = OBJ{path_pattern:STRING,schema_id:HANDLE26,root_type:STRING,
  draft_2020_12_schema:BLOB}
SchemaCatalog = OBJ{v:CONST[mcore.v7],bindings:VEC[1..512,SchemaBinding]}
SemanticConstraint = OBJ{constraint_id:HANDLE26,input_path_patterns:VEC[1..64,STRING],
  checker_rule_sha256:HEX64,failure_trigger:FailureTrigger}
SemanticConstraints = OBJ{v:CONST[mcore.v7],rules:VEC[1..4096,SemanticConstraint]}
Protocol = OBJ{v:CONST[mcore.v7],protocol_handle:HANDLE26,
  trained_conditions:CONST[[FULL_OLD,SOURCE_DERANGED_OLD,DREAM_DERANGED_OLD,
    FULL_NEW_H0,FULL_NEW_H1,FULL_OLD_PLUS_PAD]],
  control_ids:VEC[21,ControlId],component_order:CONST[[S,M,U,W,R]],
  confirmatory_n:CONST[16],rejection_cutoff:CONST[12],alpha:F64HEX,
  rpc_bytes:CONST[16384]}

EntropyRoot = OBJ{cohort:ENUM[TEXT,DEV,CONF],root_index:U53,
  seed:BLOB,seed_commitment:HEX64,call_ordinal:U53}
EntropySeal = OBJ{v:CONST[mcore.v7],static_draft_member_sha256s:VEC[1..100000,HEX64],
  roots:VEC[32,EntropyRoot],entropy_tool_sha256:HEX64,
  entropy_host_sha256:HEX64,entropy_runtime_sha256:HEX64}
HandleCodecVector = OBJ{digest_prefix:BLOB,expected_handle:HANDLE26}
HandleCodec = OBJ{v:CONST[mcore.v7],digest_bits:CONST[128],
  leading_zero_bits:CONST[2],alphabet:CONST[abcdefghijklmnopqrstuvwxyz234567],
  output_chars:CONST[26],vectors:VEC[16..256,HandleCodecVector]}
DomainSpec = OBJ{domain_id:STRING,iteration_ordinal:U53,counter_initial:CONST[0]}
RootGeneratorSpec = OBJ{v:CONST[mcore.v7],typed_hash_domain:CONST[MCORE-V7-NUL],
  seed_bytes:CONST[32],entropy_call_count:CONST[32],
  root_commitment_domain:CONST[MCORE-V7-ROOT-SEED-NUL],
  draw_algorithm:CONST[REJECT_U256],typed_encoding_law_sha256:HEX64,
  handle_codec_sha256:HEX64,
  root_namespace_law_sha256:HEX64,object_handle_law_sha256:HEX64,
  event_strata_sha256:HEX64,draw_plan_sha256:HEX64,
  device_eligibility_sha256:HEX64,
  domains:VEC[1..4096,DomainSpec],root_rejection:CONST[0]}
AssignmentTarget = ENUM[ALIASES,ROOT_BITS,LANE_PAIR,PAIR_ORDER,U_D,DREAM_SHIFT,
  SIGMA,FOUNDATIONS,CHILD_TRIALS,CANDIDATE_ORDER,FIXTURE_ORDER,TEMPLATE_ORDER,
  CONTROL_ORDER,CELL_ORDER,DEVICE_S1,DEVICE_S2,CONDITION_S1,CONDITION_S2,
  CANDIDATE_ROTATION,ORDER_B,ORDER_C,ORDER_D,HANDLE_ASSIGNMENT]
EventStratum = OBJ{stratum_id:STRING,iteration_ordinal:U53,
  population_kind:ENUM[ALIASES,FOUNDATIONS,CHILD_TRIALS,CANDIDATES,FIXTURES,
    TEMPLATES,CONTROLS,CELLS,DECOY_LANES,DEVICES,CONDITION_PERMUTATIONS,
    CANDIDATE_ORDERS],population_handle:HANDLE26,
  cardinality:U53,assignment_target:AssignmentTarget,handle_class:STRING}
EventStrata = OBJ{v:CONST[mcore.v7],strata:VEC[1..4096,EventStratum]}
DrawStep = OBJ{ordinal:U53,domain_id:STRING,
  operation:ENUM[SCALAR,FISHER_YATES_DESCENDING],population_handle:HANDLE26,
  population_cardinality:U53,assignment_target:AssignmentTarget,
  handle_class:STRING}
DrawPlan = OBJ{v:CONST[mcore.v7],steps:VEC[1..100000,DrawStep]}
AliasCandidate = OBJ{alias_handle:HANDLE26,surface:BLOB,token_ids:VEC[1..64,U53],
  byte_length:U53,token_count:U53,position_class:HANDLE26}
AliasClass = OBJ{class_id:STRING,candidates:VEC[32..4096,AliasCandidate]}
AliasPool = OBJ{v:CONST[mcore.v7],classes:VEC[1..256,AliasClass],
  cross_root_reuse:CONST[1],lookup_scope:CONST[ROOT_NAMESPACE]}
RuntimeManifest = OBJ{v:CONST[mcore.v7],cpu_image_sha256:HEX64,
  os_sha256:HEX64,interpreter_sha256:HEX64,dependency_lock_sha256:HEX64,
  materializer_source_tree_sha256:HEX64,checker_source_sha256:HEX64,
  parser_source_sha256:HEX64,entropy_tool_sha256:HEX64}
DeviceEligibility = OBJ{device_handle:HANDLE26,device_uuid:STRING,
  image_sha256:HEX64,driver_sha256:HEX64,runtime_sha256:HEX64}
DeviceEligibilityRoster = OBJ{v:CONST[mcore.v7],
  devices:VEC[1..1024,DeviceEligibility]}

ExpectedRootEntry = OBJ{cohort:ENUM[TEXT,DEV,CONF],root_index:U53,
  root_seed_commitment:HEX64,root_namespace_handle:HANDLE26,
  expected_manifest_sha256:HEX64,content_merkle_root:HEX64}
ExpectedRootIndex = OBJ{v:CONST[mcore.v7],entropy_seal_sha256:HEX64,
  roots:VEC[32,ExpectedRootEntry]}
ExpectedRootContentManifest = OBJ{v:CONST[mcore.v7],entropy_seal_sha256:HEX64,
  cohort:ENUM[TEXT,DEV,CONF],root_index:U53,root_seed_commitment:HEX64,
  root_namespace_handle:HANDLE26,members:VEC[14,ManifestMember],
  content_merkle_root:HEX64}
MaterializedRootBundleManifest = OBJ{v:CONST[mcore.v7],
  package_manifest_sha256:HEX64,expected_manifest_sha256:HEX64,
  cohort:ENUM[TEXT,DEV,CONF],root_index:U53,root_seed_commitment:HEX64,
  root_namespace_handle:HANDLE26,members:VEC[14,ManifestMember],
  content_merkle_root:HEX64}
MaterializedRootRef = OBJ{root_index:U53,root_seed_commitment:HEX64,
  root_namespace_handle:HANDLE26,
  root_manifest_sha256:HEX64,content_merkle_root:HEX64}
MaterializedCohortBundleManifest = OBJ{v:CONST[mcore.v7],
  package_manifest_sha256:HEX64,cohort:ENUM[TEXT,DEV,CONF],
  roots:VEC[8..16,MaterializedRootRef],members:VEC[8..16,ManifestMember],
  merkle_root_sha256:HEX64}
CheckerSubcheck = OBJ{name:STRING,passed:BIT,
  failure_trigger:OPT[FailureTrigger],
  evidence_sha256:HEX64}
CheckerReceipt = OBJ{v:CONST[mcore.v7],package_manifest_sha256:HEX64,
  checked_cohort_manifest_sha256:HEX64,checked_root_manifest_sha256:OPT[HEX64],
  checked_content_merkle_root:HEX64,cohort:ENUM[TEXT,DEV,CONF],
  root_index:OPT[U53],checker_sha256:HEX64,runtime_sha256:HEX64,
  subchecks:VEC[1..100000,CheckerSubcheck],overall_passed:BIT,
  failure_decision:FailureDecisionReceipt}

DrawCounterReceipt = OBJ{domain_id:STRING,final_counter:U53,
  rejection_count:U53,draw_ledger_sha256:HEX64}
HandleClassReceipt = OBJ{handle_class:STRING,object_count:U53,
  assignment_sha256:HEX64,collision_free:BIT}
RootMaterializationReceipt = OBJ{v:CONST[mcore.v7],
  root_seed_commitment:HEX64,root_namespace_handle:HANDLE26,
  draw_plan_sha256:HEX64,counters:VEC[1..4096,DrawCounterReceipt],
  permutation_sha256s:VEC[1..4096,HEX64],role_assignment_sha256:HEX64,
  handle_codec_vectors_passed:BIT,handle_classes:VEC[1..4096,HandleClassReceipt],
  generated_member_sha256s:VEC[13,HEX64],generated_members_merkle_root:HEX64}
```

### 11.3 Root geometry, public inputs, and rows

```text
RootRef = OBJ{root_seed_commitment:HEX64,root_namespace_handle:HANDLE26}
PairCandidate = OBJ{candidate_handle:HANDLE26,selection_action_handle:HANDLE26,
  lane_handles:VEC[2,HANDLE26]}
LaneProfile = OBJ{lane_handle:HANDLE26,joint:BIT,left:BIT,right:BIT,nuisance:BIT}
ExperimentLawEntry = OBJ{experiment_action_handle:HANDLE26,
  family_action_handle:HANDLE26,relation:ENUM[H,ONE_MINUS_H,NUISANCE]}
ExperimentLaw = OBJ{v:CONST[mcore.v7],law_handle:HANDLE26,
  revealed_after_source_choice_handle:HANDLE26,
  entries:VEC[4,ExperimentLawEntry]}
OutcomeCode = OBJ{observation_handle:HANDLE26,bit:BIT}
OutcomeCodebook = OBJ{v:CONST[mcore.v7],codebook_handle:HANDLE26,
  entries:VEC[2,OutcomeCode]}
PublicNewTemplateRef = OBJ{hypothesis_selector:BIT,row_handle:HANDLE26}
RootGeometry = OBJ{v:CONST[mcore.v7],root:RootRef,b:BIT,z:BIT,
  h_branches:CONST[[0,1]],
  useful_pair:VEC[2,HANDLE26],u_d:HANDLE26,dream_shift:U53,
  lanes:VEC[8,LaneProfile],pair_candidates:VEC[28,PairCandidate],
  experiment_law:ExperimentLaw,outcome_codebook:OutcomeCodebook,
  audit_only_role_sha256:HEX64}

ActionSurface = OBJ{action_handle:HANDLE26,surface:BLOB}
BGoal = OBJ{kind:CONST[B],goal_handle:HANDLE26,start:HANDLE26,target:HANDLE26,
  route_cue:HANDLE26,read_budget:CONST[3],action_budget:CONST[4]}
BAtomsGoal = OBJ{kind:CONST[B_ATOMS],goal_handle:HANDLE26,start:HANDLE26,
  target:HANDLE26,route_cue:HANDLE26,read_budget:CONST[4],action_budget:CONST[4]}
CGoal = OBJ{kind:ENUM[C_PROBE,C_LIVE],goal_handle:HANDLE26,start:HANDLE26,
  target:HANDLE26,desired_outcome:HANDLE26,read_budget:CONST[1],
  action_budget:ENUM[1,2]}
DGoal = OBJ{kind:CONST[D],goal_handle:HANDLE26,start:HANDLE26,target:HANDLE26,
  read_budget:CONST[2],action_budget:CONST[3]}
PublicGoal = ONEOF[BGoal,BAtomsGoal,CGoal,DGoal]

ChildFoundationTask = OBJ{kind:ENUM[FOUNDATION_ROUTE,FOUNDATION_TERMINAL],
  instruction_handle:HANDLE26,fixture_handle:HANDLE26,instruction:BLOB}
ChildSourceTask = OBJ{kind:CONST[SOURCE],instruction_handle:HANDLE26,
  fixture_handle:HANDLE26,desired_outcomes:VEC[2,HANDLE26],instruction:BLOB}
ChildAblationTask = OBJ{kind:CONST[ABLATION],instruction_handle:HANDLE26,
  fixture_handle:HANDLE26,lane_handles:VEC[8,HANDLE26],instruction:BLOB}
ChildPairTask = OBJ{kind:CONST[PAIR_SELECTION],instruction_handle:HANDLE26,
  ablation_fixture_handle:HANDLE26,lane_handles:VEC[8,HANDLE26],
  pair_candidates:VEC[28,PairCandidate],
  evidence_event_handles:VEC[64,HANDLE26],instruction:BLOB}
SupportSlot = OBJ{lane_handle:HANDLE26,
  trial_kind:ENUM[JOINT,LEFT,RIGHT,NUISANCE],action_handle:HANDLE26}
ChildSupportTask = OBJ{kind:CONST[SUPPORT],instruction_handle:HANDLE26,
  support_fixture_handle:HANDLE26,selected_lanes:VEC[2,HANDLE26],
  slots:VEC[8,SupportSlot],instruction:BLOB}
ChildPadTask = OBJ{kind:CONST[PAD],instruction_handle:HANDLE26,
  fixture_handle:HANDLE26,instruction:BLOB}
PublicChildTask = ONEOF[ChildFoundationTask,ChildSourceTask,ChildAblationTask,
  ChildPairTask,ChildSupportTask,ChildPadTask]

PublicMenuEntry = OBJ{family_action_handle:HANDLE26,
  experiment_action_handles:VEC[2,HANDLE26]}
PublicMenu = OBJ{menu_handle:HANDLE26,entries:VEC[2,PublicMenuEntry]}
MemoryCatalog = OBJ{legal_query_types:VEC[0..6,ENUM[ROUTE_BY_CUE,
  ATOM_SUCCESSOR,LINK_SUCCESSOR,TERMINAL_TO_TARGET,SOURCE_INVERSE,
  NEW_SUCCESSOR]],candidate_schema_sha256:HEX64,reads_remaining:U53}
DecodeConfig = OBJ{algorithm:ENUM[GREEDY,TOP_P],temperature:F64HEX,
  top_p:F64HEX,top_k:U53,max_tokens:U53,stop_sequences:VEC[0..8,BLOB],
  inference_rng_rule_sha256:HEX64}
ActorEpisodeInput = OBJ{v:CONST[mcore.v7],public_pair_handle:HANDLE26,
  phase:ENUM[CHILD_FOUNDATION_ROUTE,CHILD_FOUNDATION_TERMINAL,CHILD_SOURCE,
    CHILD_ABLATION,CHILD_PAIR_SELECTION,CHILD_SUPPORT,CHILD_PAD,B,C_PROBE,
    C_LIVE,D],actor_binding_sha256:HEX64,goal:OPT[PublicGoal],
  current_state:HANDLE26,actions:VEC[32,ActionSurface],
  public_menu:OPT[PublicMenu],public_law:OPT[ExperimentLaw],
  outcome_codebook:OPT[OutcomeCodebook],
  public_new_template_refs:VEC[0..2,PublicNewTemplateRef],
  child_task:OPT[PublicChildTask],
  memory_catalog:MemoryCatalog,decode:DecodeConfig}

RouteRequest = OBJ{v:CONST[mcore.v7],kind:CONST[ROUTE_BY_CUE],phase:CONST[B],
  state:HANDLE26,goal:HANDLE26,route_cue:HANDLE26,
  candidate_schema_sha256:HEX64,call_ordinal:U53,reads_remaining:U53}
AtomRequest = OBJ{v:CONST[mcore.v7],kind:CONST[ATOM_SUCCESSOR],phase:CONST[B],
  state:HANDLE26,goal:HANDLE26,candidate_schema_sha256:HEX64,
  call_ordinal:U53,reads_remaining:U53}
LinkRequest = OBJ{v:CONST[mcore.v7],kind:CONST[LINK_SUCCESSOR],
  phase:ENUM[B,D],state:HANDLE26,goal:HANDLE26,
  candidate_schema_sha256:HEX64,call_ordinal:U53,reads_remaining:U53}
TerminalRequest = OBJ{v:CONST[mcore.v7],kind:CONST[TERMINAL_TO_TARGET],
  phase:CONST[B],state:HANDLE26,goal:HANDLE26,target:HANDLE26,
  candidate_schema_sha256:HEX64,call_ordinal:U53,reads_remaining:U53}
SourceRequest = OBJ{v:CONST[mcore.v7],kind:CONST[SOURCE_INVERSE],
  phase:ENUM[C_PROBE,C_LIVE],state:HANDLE26,goal:HANDLE26,
  desired_outcome:HANDLE26,candidate_schema_sha256:HEX64,
  call_ordinal:U53,reads_remaining:U53}
NewRequest = OBJ{v:CONST[mcore.v7],kind:CONST[NEW_SUCCESSOR],phase:CONST[D],
  state:HANDLE26,goal:HANDLE26,target:HANDLE26,
  candidate_schema_sha256:HEX64,call_ordinal:U53,reads_remaining:U53}
RecognitionRequest = ONEOF[RouteRequest,AtomRequest,LinkRequest,TerminalRequest,
  SourceRequest,NewRequest]

SourceStatistic = OBJ{action_handle:HANDLE26,desired_outcome:HANDLE26,
  matching_count:U53,total_count:CONST[4]}
MemoryRow = OBJ{v:CONST[mcore.v7],row_handle:HANDLE26,
  query_type:ENUM[ROUTE_BY_CUE,ATOM_SUCCESSOR,LINK_SUCCESSOR,
    TERMINAL_TO_TARGET,SOURCE_INVERSE,NEW_SUCCESSOR],
  mode:ENUM[ATOM,SEQUENCE,CHOICE_TABLE],keys:VEC[1..2,HANDLE26],
  actions:VEC[0..2,HANDLE26],source_statistics:VEC[0..2,SourceStatistic],
  destinations:VEC[0..2,HANDLE26],citations:VEC[2,HANDLE26]}
MemoryReturn = OBJ{v:CONST[mcore.v7],status:ENUM[FOUND,MISS,BLOCKED],
  request_sha256:HEX64,row:OPT[MemoryRow],reads_remaining:U53}
```

### 11.4 Model custody, events, compilers, and transitions

```text
ParsedRead = OBJ{kind:CONST[READ],request:RecognitionRequest}
ParsedAction = OBJ{kind:CONST[ACTION],action_handle:HANDLE26}
ParsedPairSelection = OBJ{kind:CONST[PAIR_SELECTION],
  selection_action_handle:HANDLE26,selected_lanes:VEC[2,HANDLE26]}
ParsedDeclaration = OBJ{kind:CONST[DECLARATION],experiment_action:HANDLE26,
  predicted_outcomes:VEC[0..2,BIT],hypothesis_row_handles:VEC[0..2,HANDLE26]}
ParsedDecision = ONEOF[ParsedRead,ParsedAction,ParsedPairSelection,
  ParsedDeclaration]
DecisionParseReceipt = OBJ{v:CONST[mcore.v7],parse_handle:HANDLE26,
  parser_source_sha256:HEX64,parser_config_sha256:HEX64,
  parser_input_sha256:HEX64,parse_status:CONST[EXACTLY_ONE],
  parsed_decision:ParsedDecision,parsed_object_sha256:HEX64,
  repair_count:CONST[0],extra_object_count:CONST[0]}
InferenceDraw = OBJ{token_ordinal:U53,rng_counter:U64D,
  rng_word:BLOB,logits_sha256:HEX64,sampling_distribution_sha256:HEX64,
  selected_token_id:U53,draw_sha256:HEX64}
ModelTurnReceipt = OBJ{v:CONST[mcore.v7],turn_handle:HANDLE26,
  role:ENUM[CHILD,DEPLOYMENT_ACTOR],process_instance_handle:HANDLE26,
  episode_handle:HANDLE26,turn_ordinal:U53,
  actor_input_sha256:HEX64,preturn_transcript_sha256:HEX64,
  actor_binding_sha256:HEX64,model_sha256:HEX64,tokenizer_sha256:HEX64,
  renderer_sha256:HEX64,chat_template_sha256:HEX64,engine_sha256:HEX64,
  runtime_sha256:HEX64,birth_checkpoint_sha256:HEX64,
  birth_state_sha256:HEX64,continuation:BLOB,token_ids:VEC[1..65536,U53],
  stop_reason:ENUM[STOP_SEQUENCE,MAX_TOKENS,EOS],
  inference_draws:VEC[0..65536,InferenceDraw],draw_ledger_sha256:HEX64,
  decision_parse:DecisionParseReceipt,
  logical_start_tick:U53,logical_end_tick:U53,result_object_sha256:HEX64}
ProcessBirthReceipt = OBJ{v:CONST[mcore.v7],process_instance_handle:HANDLE26,
  role:ENUM[CHILD,DEPLOYMENT_ACTOR,READER,WRITER],
  spawn_nonce:HANDLE26,scope_handle:HANDLE26,birth_checkpoint_sha256:HEX64,
  process_binding_sha256:HEX64,runtime_sha256:HEX64,
  initial_state_sha256:HEX64,empty_context:BLOB,first_operation_handle:HANDLE26,
  predecessor_process_handle:CONST[null],logical_tick:U53}
ResetReceipt = OBJ{v:CONST[mcore.v7],birth_receipt_sha256:HEX64,
  first_turn_handle:HANDLE26,first_turn_sha256:HEX64,
  empty_context_match:BIT,no_parent_or_childhood_text:BIT,
  only_registered_carrier_mounted:BIT,no_external_capabilities:BIT,
  fresh_process:BIT,passed:BIT,failure_trigger:OPT[FailureTrigger]}
ProcessTeardownReceipt = OBJ{v:CONST[mcore.v7],process_instance_handle:HANDLE26,
  scope_handle:HANDLE26,terminal_operation_handle:HANDLE26,
  release_tick:U53,descendant_process_count:CONST[0],passed:BIT}

PublicReadRequestEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  model_turn_handle:HANDLE26,request:RecognitionRequest,
  logical_request_tick:U53}
PublicReadReturnEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  request_event_handle:HANDLE26,rpc_receipt_sha256:HEX64,
  logical_release_tick:U53}
ChildActionEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  model_turn_handle:HANDLE26,authorization:CONST[CHILD_COMMIT],
  instruction_handle:HANDLE26,action_handle:HANDLE26,pre_state:HANDLE26,
  logical_tick:U53}
MemoryActionEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  model_turn_handle:HANDLE26,authorization:CONST[MEMORY_ROW],
  row_handle:HANDLE26,action_handle:HANDLE26,pre_state:HANDLE26,
  logical_tick:U53}
PairSelectionEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  model_turn_handle:HANDLE26,authorization:CONST[CHILD_PAIR_SELECTION],
  actor_input_sha256:HEX64,ablation_action_handles:VEC[32,HANDLE26],
  ablation_observation_handles:VEC[32,HANDLE26],
  visible_lane_handles:VEC[8,HANDLE26],
  visible_pair_candidates:VEC[28,PairCandidate],
  selected_pair_action_handle:HANDLE26,selected_lane_handles:VEC[2,HANDLE26],
  logical_tick:U53}
SupportRevealEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  selection_event_handle:HANDLE26,ablation_fixture_handle:HANDLE26,
  support_fixture_handle:HANDLE26,selected_lanes:VEC[2,HANDLE26],
  slots:VEC[8,SupportSlot],logical_tick:U53}
PublicObservation = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  causing_event_handle:HANDLE26,observation_handle:HANDLE26,
  outcome_category_handle:HANDLE26,surface:BLOB,post_state:HANDLE26,
  logical_tick:U53}
ExperimentLawRevealEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  source_choice_event_handle:HANDLE26,law:ExperimentLaw,
  codebook:OutcomeCodebook,new_template_refs:VEC[2,PublicNewTemplateRef],
  logical_tick:U53}
DeclarationEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  model_turn_handle:HANDLE26,law_reveal_event_handle:HANDLE26,
  source_choice_event_handle:HANDLE26,experiment_action:HANDLE26,
  predicted_outcomes:VEC[0..2,BIT],hypothesis_row_handles:VEC[0..2,HANDLE26],
  logical_tick:U53}
DispatchEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  model_turn_handle:HANDLE26,declaration_event_handle:HANDLE26,
  source_choice_event_handle:HANDLE26,public_menu:PublicMenu,
  experiment_action:HANDLE26,pre_state:HANDLE26,logical_tick:U53}

PresentedSourcePair = OBJ{presented_action_handle:HANDLE26,
  public_outcome_category_handle:HANDLE26,citation_handle:HANDLE26}
PresentedSourceEvidence = OBJ{v:CONST[mcore.v7],
  pairs:VEC[8,PresentedSourcePair],desired_outcomes:VEC[2,HANDLE26]}
SupportBinding = OBJ{lane_handle:HANDLE26,
  trial_kind:ENUM[JOINT,LEFT,RIGHT,NUISANCE],
  reveal_slot_action_handle:HANDLE26,action_event:ChildActionEvent,
  observation:PublicObservation}
LinkEvidence = OBJ{v:CONST[mcore.v7],selection:PairSelectionEvent,
  reveal:SupportRevealEvent,support:VEC[8,SupportBinding]}
PadEvidence = OBJ{v:CONST[mcore.v7],action_event:ChildActionEvent,
  observation:PublicObservation}
CompilerRowTemplate = OBJ{template_handle:HANDLE26,
  phase:ENUM[SOURCE,LINK,PAD],row:MemoryRow,fill_fields:CONST[[]]}
NewRowTemplate = OBJ{template_handle:HANDLE26,phase:CONST[NEW],
  hypothesis_selector:BIT,row:MemoryRow,fill_fields:CONST[[]]}
SourceCompilerInput = OBJ{v:CONST[mcore.v7],phase:CONST[SOURCE],
  presented_evidence:PresentedSourceEvidence,
  templates:VEC[50,CompilerRowTemplate]}
LinkCompilerInput = OBJ{v:CONST[mcore.v7],phase:CONST[LINK],
  evidence:LinkEvidence,templates:VEC[2,CompilerRowTemplate]}
PadCompilerInput = OBJ{v:CONST[mcore.v7],phase:CONST[PAD],
  evidence:PadEvidence,template:CompilerRowTemplate}
NewCompilerInput = OBJ{v:CONST[mcore.v7],phase:CONST[NEW],
  canonical_source_evidence:PresentedSourceEvidence,
  source_choice_event:MemoryActionEvent,menu:PublicMenu,
  law_reveal:ExperimentLawRevealEvent,declaration:DeclarationEvent,
  dispatch:DispatchEvent,outcome:PublicObservation,
  templates:VEC[2,NewRowTemplate]}
CompilerInput = ONEOF[SourceCompilerInput,LinkCompilerInput,PadCompilerInput,
  NewCompilerInput]
CompilerInvocationEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  input:CompilerInput,input_sha256:HEX64,prerequisite_event_handles:VEC[1..128,HANDLE26],
  logical_tick:U53}
CompilerDecisionEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  invocation_event_handle:HANDLE26,input_sha256:HEX64,
  status:ENUM[ADMIT,NO_ADMISSION],code:CompilerDecisionCode,
  template_selectors:VEC[0..2,U53],admitted_rows:VEC[0..2,MemoryRow],
  cited_event_handles:VEC[0..128,HANDLE26],logical_tick:U53}
EpisodeTerminal = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  state_handle:HANDLE26,trace_valid:BIT,
  provisional_failure_trigger:OPT[FailureTrigger],logical_tick:U53}

PhaseId = ENUM[CHILD_FOUNDATION_ROUTE,CHILD_FOUNDATION_TERMINAL,CHILD_SOURCE,
  CHILD_ABLATION,CHILD_PAIR_SELECTION,CHILD_SUPPORT,CHILD_PAD,B,C_PROBE,
  C_LIVE,D]
CompilerDecisionCode = ENUM[SOURCE_ROWS,LINK_ROWS,PAD_ROW,NEW_ROW,
  REJECT_SCHEMA,REJECT_EVIDENCE,REJECT_SUPPORT,REJECT_SOURCE,
  REJECT_DECLARATION,REJECT_DISPATCH,REJECT_NUISANCE,REJECT_POSTERIOR]
ActorActionTransition = OBJ{kind:CONST[ACTOR_ACTION],phase:PhaseId,
  pre_state:HANDLE26,action_handle:HANDLE26,post_state:HANDLE26,
  observation_handle:HANDLE26,terminal:BIT}
AutonomousOutcomeTransition = OBJ{kind:CONST[AUTONOMOUS_OUTCOME],
  phase:CONST[C_LIVE],dispatch_action_handle:HANDLE26,
  hidden_branch_selector:ENUM[H0,H1,Z0,Z1],post_state:HANDLE26,
  observation_handle:HANDLE26}
CompilerTransition = OBJ{kind:CONST[COMPILER],
  phase:ENUM[CHILD_SOURCE,CHILD_SUPPORT,CHILD_PAD,C_LIVE],
  pre_state:HANDLE26,decision_code:CompilerDecisionCode,post_state:HANDLE26}
TerminalTransition = OBJ{kind:CONST[TERMINAL],phase:PhaseId,
  pre_state:HANDLE26,failure_code:FailureCode,terminal_state:HANDLE26}
Transition = ONEOF[ActorActionTransition,AutonomousOutcomeTransition,
  CompilerTransition,TerminalTransition]
RootTransitionTable = OBJ{v:CONST[mcore.v7],root:RootRef,
  transitions:VEC[1..100000,Transition]}
ActionRoster = OBJ{phase:PhaseId,state:HANDLE26,actions:VEC[32,ActionSurface]}
RootActionRosters = OBJ{v:CONST[mcore.v7],root:RootRef,
  rosters:VEC[1..100000,ActionRoster]}

PublicTraceEvent = ONEOF[PublicReadRequestEvent,PublicReadReturnEvent,
  ChildActionEvent,MemoryActionEvent,
  PairSelectionEvent,SupportRevealEvent,PublicObservation,
  ExperimentLawRevealEvent,DeclarationEvent,DispatchEvent,
  CompilerInvocationEvent,CompilerDecisionEvent,EpisodeTerminal]
PublicTrace = OBJ{v:CONST[mcore.v7],cell_handle:HANDLE26,
  actor_input_sha256:HEX64,events:VEC[1..512,PublicTraceEvent],
  reads_used:U53,actions_used:U53,terminal_event_handle:HANDLE26}
```

### 11.5 Mounts, candidates, controls, and reader/RPC

```text
CandidateSlot = OBJ{slot:U53,original_row_sha256:HEX64,
  mounted_row:MemoryRow,projection_kind:ENUM[ORIGINAL,CUT_FILLER,PAYLOAD_SWAP,
    NO_CARRIER_FILLER],available:BIT}
CandidateProjection = OBJ{request_fingerprint:HEX64,slots:VEC[32,CandidateSlot]}
MountInstance = OBJ{mount_instance_handle:HANDLE26,carrier:CarrierId,
  mount_target:ENUM[ACTOR,READER,BOTH],control:OPT[ControlId],
  projections:VEC[1..100000,CandidateProjection]}
RuntimeMountReceipt = OBJ{v:CONST[mcore.v7],root:OPT[RootRef],
  qualification_case_handle:OPT[HANDLE26],
  mount_instance_handle:HANDLE26,mount_instance_sha256:HEX64,
  carrier:CarrierId,carrier_artifact_sha256:OPT[HEX64],
  mount_target:ENUM[ACTOR,READER,BOTH],control:OPT[ControlId],
  mounted_process_handles:VEC[1..2,HANDLE26],
  candidate_projection_sha256s:VEC[1..100000,HEX64],passed:BIT}
RootMountInstances = OBJ{v:CONST[mcore.v7],root:RootRef,
  mounts:VEC[1..10000,MountInstance]}
CandidateRoster = OBJ{request_fingerprint:HEX64,rows:VEC[32,MemoryRow]}
RootCandidateRosters = OBJ{v:CONST[mcore.v7],root:RootRef,
  rosters:VEC[1..100000,CandidateRoster]}
CanonicalReturn = OBJ{mount_instance_handle:HANDLE26,request_fingerprint:HEX64,
  status:ENUM[FOUND,MISS],row_sha256:OPT[HEX64]}
RootCanonicalReturns = OBJ{v:CONST[mcore.v7],root:RootRef,
  returns:VEC[1..100000,CanonicalReturn]}

DifferenceMap = OBJ{map_handle:HANDLE26,baseline_sha256:HEX64,
  intervention_sha256:HEX64,changed_json_pointers:VEC[0..64,STRING],
  complete_byte_bitmap:BLOB,causal_parent_map_sha256:HEX64}
AllowedTensorDifference = OBJ{difference_handle:HANDLE26,stage:ENUM[S1,S2],
  baseline_example_handle:HANDLE26,comparison_example_handle:HANDLE26,
  permitted_row_json_pointers:VEC[0..64,STRING],
  input_ids_bitmap:BLOB,labels_bitmap:BLOB,
  forced_descendant_bitmap:BLOB,masks_positions_equal:BIT,
  complete:BIT}
GoalPairByteCutReceipt = OBJ{input_a_sha256:HEX64,input_b_sha256:HEX64,
  first_difference_offset:U53,first_difference_json_pointer:STRING,
  complete_byte_bitmap:BLOB,common_public_pair_handle:HANDLE26,
  common_actor_decode_catalog_sha256:HEX64,passed:BIT}
RootDifferenceMaps = OBJ{v:CONST[mcore.v7],root:RootRef,
  maps:VEC[1..100000,DifferenceMap],
  training_differences:VEC[1..100000,AllowedTensorDifference],
  goal_pair_cut:GoalPairByteCutReceipt}
Mutation = OBJ{kind:ENUM[NONE,CARRIER_OFF,CUT,PAYLOAD_SWAP,COUNT_SWAP,
    CATALOG_PERMUTE,GOAL_CUE_SWAP],target_handle:OPT[HANDLE26],
  replacement_sha256:OPT[HEX64],json_pointer:OPT[STRING],
  permutation_ordinal:OPT[U53]}
TraceEventKind = ENUM[READ_REQUEST,READ_RETURN,CHILD_ACTION,MEMORY_ACTION,PAIR_SELECTION,
  SUPPORT_REVEAL,OBSERVATION,LAW_REVEAL,DECLARATION,DISPATCH,
  COMPILER_INVOCATION,COMPILER_DECISION,TERMINAL]
ExpectedTraceStep = OBJ{ordinal:U53,event_kind:TraceEventKind,
  canonical_object_sha256:HEX64}
ControlCaseSpec = OBJ{case_handle:HANDLE26,mount_instance_handle:HANDLE26,
  actor_input:ActorEpisodeInput,expected_steps:VEC[1..64,ExpectedTraceStep],
  expected_reads:U53,expected_actions:U53,expected_terminal:HANDLE26,
  expected_endpoint:BIT,expected_failure_code:FailureCode}
ControlSpec = OBJ{control_id:ControlId,mutation:Mutation,
  difference_map_handle:HANDLE26,cases:VEC[1..32,ControlCaseSpec],
  aggregate_rule_sha256:HEX64}
RootControlRegistry = OBJ{v:CONST[mcore.v7],root:RootRef,
  controls:VEC[21,ControlSpec]}
RootCompilerTemplates = OBJ{v:CONST[mcore.v7],root:RootRef,
  source_templates:VEC[50,CompilerRowTemplate],
  link_templates:VEC[2,CompilerRowTemplate],pad_template:CompilerRowTemplate,
  new_templates:VEC[2,NewRowTemplate]}
Fixture = OBJ{fixture_handle:HANDLE26,kind:ENUM[FOUNDATION,SOURCE,ABLATION,
  SUPPORT,PAD,B_GOAL,C_GOAL,D_GOAL,CANARY,NONHARM],payload:BLOB,
  revealed_at_phase:PhaseId}
RootFixtures = OBJ{v:CONST[mcore.v7],root:RootRef,
  fixtures:VEC[1..10000,Fixture]}
RootOrderTables = OBJ{v:CONST[mcore.v7],root:RootRef,
  s1_conditions:VEC[3,CarrierId],s2_conditions:VEC[3,CarrierId],
  sigma:VEC[32,U53],candidate_orders:VEC[4,VEC[32,U53]],
  b_controls:VEC[1..21,ControlId],c_controls:VEC[1..21,ControlId],
  d_controls:VEC[1..21,ControlId],candidate_rotation:U53,
  device_s1:HANDLE26,device_s2:HANDLE26}

RecognitionScorerInput = OBJ{v:CONST[mcore.v7],reader_prompt:BLOB,
  request:RecognitionRequest,candidate:MemoryRow}
RecognitionScore = OBJ{candidate_slot:U53,input_sha256:HEX64,
  yes_logprob:F64HEX,no_logprob:F64HEX,aggregate:F64HEX}
ScorerReceipt = OBJ{v:CONST[mcore.v7],root:RootRef,
  mount_instance_handle:HANDLE26,request_sha256:HEX64,
  reader_binding_sha256:HEX64,model_sha256:HEX64,tokenizer_sha256:HEX64,
  worker_image_sha256:HEX64,candidate_order:ENUM[P0,P1,P2,P3],
  inference_draw_ledger_sha256:HEX64,
  candidate_projection_sha256:HEX64,scores:VEC[32,RecognitionScore],
  status:ENUM[FOUND,MISS],row_sha256:OPT[HEX64],
  unavailable_or_filler_found:BIT}
RpcMachine = OBJ{v:CONST[mcore.v7],magic:CONST[MCRPC7-NUL],
  rpc_bytes:CONST[16384],header_bytes:CONST[11],logical_delta:CONST[1],
  physical_deadline_ns:U64D,clock_source_sha256:HEX64,
  scorer_count:CONST[32],worker_image_sha256:HEX64,
  frame_algorithm_sha256:HEX64,padding_algorithm_sha256:HEX64}
RpcReceipt = OBJ{v:CONST[mcore.v7],request_sha256:HEX64,
  request_event_handle:HANDLE26,return_event_handle:HANDLE26,
  rpc_machine_sha256:HEX64,scorer_receipt_sha256:HEX64,payload:BLOB,frame:BLOB,
  logical_request_tick:U53,logical_release_tick:U53,
  physical_start_ns:U64D,physical_release_ns:U64D,
  frame_algorithm_sha256:HEX64,padding_algorithm_sha256:HEX64,
  overrun:BIT}
```

### 11.6 Bindings, qualification, training, and interface gates

```text
ActorBinding = OBJ{v:CONST[mcore.v7],actor_id:HANDLE26,
  model_sha256:HEX64,birth_checkpoint_sha256:HEX64,tokenizer_sha256:HEX64,
  renderer_sha256:HEX64,chat_template_sha256:HEX64,engine_sha256:HEX64,
  runtime_image_sha256:HEX64,parser_source_sha256:HEX64,
  parser_config_sha256:HEX64,decode:DecodeConfig}
WriterBinding = OBJ{v:CONST[mcore.v7],writer_id:HANDLE26,
  model_sha256:HEX64,birth_checkpoint_sha256:HEX64,
  tokenizer_sha256:HEX64,chat_template_sha256:HEX64,
  trainer_source_sha256:HEX64,runtime_image_sha256:HEX64,
  renderer_sha256:HEX64,
  parser_sha256:HEX64,parser_config_sha256:HEX64,recipe_sha256:HEX64,rank:U53,
  learning_rate:F64HEX,optimizer_sha256:HEX64,steps:U53,
  loss_mask_sha256:HEX64,preservation_mix_sha256:HEX64,
  visit_schedule_sha256:HEX64,qualification_spec_sha256:HEX64}
ReaderBinding = OBJ{v:CONST[mcore.v7],reader_id:HANDLE26,
  model_sha256:HEX64,tokenizer_sha256:HEX64,prompt:BLOB,
  aggregate_rule_sha256:HEX64,threshold:F64HEX,margin:F64HEX,
  candidate_order_rule_sha256:HEX64,rpc_machine_sha256:HEX64,
  clock_source_sha256:HEX64,scorer_count:CONST[32],
  worker_image_sha256:HEX64,frame_algorithm_sha256:HEX64,
  padding_algorithm_sha256:HEX64,qualification_spec_sha256:HEX64}

QualificationCaseKind = ENUM[ATOM,SEQUENCE,CHOICE_3_1,CHOICE_2_2,
  NEW_H0,NEW_H1,PRIVATE_PAD,CUMULATIVE_OLD_NEW,CUT_FILLER,
  PAYLOAD_SWAP,NO_CARRIER]
QualificationCaseSpec = OBJ{case_handle:HANDLE26,kind:QualificationCaseKind,
  fixture_sha256:HEX64,expected_row_sha256s:VEC[0..8,HEX64],
  expected_status:ENUM[FOUND,MISS,EXTRACT],threshold:F64HEX}
WriterQualificationSpec = OBJ{v:CONST[mcore.v7],
  cases:VEC[8,QualificationCaseSpec],required_kinds:CONST[[ATOM,SEQUENCE,
    CHOICE_3_1,CHOICE_2_2,NEW_H0,NEW_H1,PRIVATE_PAD,CUMULATIVE_OLD_NEW]],
  canary_sha256:HEX64}
ReaderQualificationSpec = OBJ{v:CONST[mcore.v7],
  cases:VEC[8,QualificationCaseSpec],required_kinds:CONST[[ATOM,SEQUENCE,
    CHOICE_3_1,CHOICE_2_2,NEW_H0,CUT_FILLER,PAYLOAD_SWAP,NO_CARRIER]],
  candidate_orders:CONST[[P0,P1,P2,P3]],rpc_machine_sha256:HEX64}
QualificationCaseReceipt = OBJ{case_handle:HANDLE26,kind:QualificationCaseKind,
  model_turn_sha256s:VEC[0..1024,HEX64],tensor_sha256s:VEC[0..1024,HEX64],
  row_parser_sha256s:VEC[0..1024,HEX64],
  observed_row_sha256s:VEC[0..8,HEX64],
  observed_status:ENUM[FOUND,MISS,EXTRACT],score:F64HEX,passed:BIT}
QualificationReceipt = OBJ{v:CONST[mcore.v7],kind:ENUM[WRITER,READER],
  package_manifest_sha256:HEX64,binding_sha256:HEX64,
  specification_sha256:HEX64,cases:VEC[8,QualificationCaseReceipt],
  all_mandatory_kinds_present:BIT,accepted:BIT,
  failure_decision:FailureDecisionReceipt}

MemoryRowParseReceipt = OBJ{v:CONST[mcore.v7],parse_handle:HANDLE26,
  parser_source_sha256:HEX64,parser_config_sha256:HEX64,
  parser_input:BLOB,status:ENUM[EXTRACT,MISS],row:OPT[MemoryRow],
  repair_count:CONST[0],extra_object_count:CONST[0]}

TrainingTensorReceipt = OBJ{v:CONST[mcore.v7],cell_handle:HANDLE26,
  example_handle:HANDLE26,input_ids:BLOB,attention_mask:BLOB,
  position_ids:BLOB,labels:BLOB,loss_mask:BLOB,
  allowed_difference_handle:HANDLE26,allowed_difference_bitmap:BLOB,
  view_id:HANDLE26,visit_id:HANDLE26,
  deck_slot:U53,batch_index:U53,optimizer_step:U53,
  dropout_indices:BLOB,renderer_sha256:HEX64}
OptimizationStream = OBJ{kind:ENUM[SLOT,BATCH,DROPOUT,DATA_WORKER,OPTIMIZER],
  initial_counter:CONST[0],final_counter:U53,ledger_sha256:HEX64}
OptimizationReceipt = OBJ{v:CONST[mcore.v7],attempt_handle:HANDLE26,
  writer_binding_sha256:HEX64,writer_qualification_receipt_sha256:HEX64,
  initial_checkpoint_sha256:HEX64,optimizer_initial_state_sha256:HEX64,
  schedule_sha256:HEX64,deterministic_kernel_sha256:HEX64,
  deck_sha256:HEX64,streams:VEC[5,OptimizationStream],batches:U53,
  forward_calls:U53,backward_calls:U53,updates:U53,
  supervised_tokens:U53,total_tokens:U53,
  health_before_sha256:HEX64,health_after_sha256:HEX64}
PairwiseWorkReceipt = OBJ{v:CONST[mcore.v7],stage:ENUM[S1,S2],
  attempt_handles:VEC[3,HANDLE26],device_uuid:STRING,
  allowed_difference_sha256s:VEC[1..100000,HEX64],
  tensor_receipt_sha256s:VEC[1..100000,HEX64],
  initialization_equal:BIT,tensors_equal_outside_bitmap:BIT,
  masks_shapes_work_equal:BIT,rng_counters_equal:BIT,kernels_equal:BIT,
  health_equal:BIT,passed:BIT}
PadWorkReceipt = OBJ{v:CONST[mcore.v7],root:RootRef,
  pad_row_sha256:HEX64,child_action_event_sha256:HEX64,
  public_observation_sha256:HEX64,compiler_case_sha256:HEX64,
  allowed_difference_sha256:HEX64,tensor_receipt_sha256s:VEC[1..10000,HEX64],
  gradient_bearing_supervised_tokens:U53,
  matched_against_new_h0:BIT,matched_against_new_h1:BIT,
  disconnected_from_d_goal:BIT,passed:BIT}
ExtractionReceipt = OBJ{v:CONST[mcore.v7],carrier:CarrierId,
  expected_row_sha256s:VEC[0..32,HEX64],observed_row_sha256s:VEC[0..32,HEX64],
  missing:U53,unexpected:U53,exact_payload_match:BIT,passed:BIT}
InterfaceCaseReceipt = OBJ{case_handle:HANDLE26,turn_sha256s:VEC[1..128,HEX64],
  trace_sha256:HEX64,malformed:U53,unavailable_found:U53,uncited:U53,passed:BIT}
InterfaceCanaryReceipt = OBJ{v:CONST[mcore.v7],carrier:CarrierId,
  cases:VEC[32,InterfaceCaseReceipt],pass_count:U53,passed:BIT}
NonharmCaseReceipt = OBJ{case_handle:HANDLE26,birth_score:F64HEX,
  carrier_score:F64HEX,difference:F64HEX}
NonharmReceipt = OBJ{v:CONST[mcore.v7],carrier:CarrierId,
  cases:VEC[32,NonharmCaseReceipt],mean_difference:F64HEX,
  adverse_bound:CONST[bfa999999999999a],passed:BIT}
ReaderAcceptanceReceipt = OBJ{v:CONST[mcore.v7],carrier:CarrierId,
  mount_instance_handles:VEC[1..10000,HANDLE26],required_found:U53,
  observed_found:U53,required_miss:U53,observed_miss:U53,
  unavailable_found:U53,wrong_anchor:U53,bypass:U53,passed:BIT}
InferenceMatchReceipt = OBJ{v:CONST[mcore.v7],root:RootRef,
  family_handle:HANDLE26,cell_handles:VEC[2..32,HANDLE26],
  actor_input_prefix_sha256:HEX64,decode_config_sha256:HEX64,
  initial_rng_state_sha256:HEX64,draw_rule_sha256:HEX64,
  matched_until_first_registered_intervention:BIT,
  continuation_draw_ledgers:VEC[2..32,HEX64],passed:BIT}
```

`bfa999999999999a` is the canonical binary64 encoding of -0.05. The schema
checker independently recomputes it and every mean.

### 11.7 Cells, endpoint/compiler custody, provenance, and gates

```text
CellIdentity = OBJ{cell_handle:HANDLE26,cohort:ENUM[TEXT,DEV,CONF],
  root_index:U53,stage:ENUM[CHILD,TEXT,S1,S2,CONTROL,INTERFACE,NONHARM],
  carrier:CarrierId,control:OPT[ControlId],goal_ordinal:OPT[U53],
  hypothesis:OPT[BIT],probe_ordinal:OPT[U53]}
CellSpec = OBJ{identity:CellIdentity,mount_instance_handle:HANDLE26,
  actor_input_sha256:HEX64,expected_trace_sha256:HEX64,
  canonical_expected_endpoint:BIT,canonical_expected_failure_code:FailureCode,
  allowed_observed_failure_codes:VEC[9,FailureCode]}
RootCellRoster = OBJ{v:CONST[mcore.v7],root:RootRef,cells:VEC[1..100000,CellSpec]}
SealedEndpoint = OBJ{seal_handle:HANDLE26,cell_handle:HANDLE26,
  structural_receipt_sha256:HEX64,
  endpoint_bytes_sha256:HEX64,seal_nonce_commitment:HEX64,sealed_bytes:BLOB,
  sealed_at_logical_tick:U53}
FailureTriggerReceiptRef = OBJ{trigger:FailureTrigger,receipt_type:STRING,
  receipt_sha256:HEX64,triggered:BIT}
FailureDecisionReceipt = OBJ{v:CONST[mcore.v7],decision_handle:HANDLE26,
  decision_table_sha256:HEX64,decision_phase:ENUM[STRUCTURAL,ENDPOINT],
  inputs:VEC[8..24,FailureTriggerReceiptRef],
  triggered:VEC[0..24,FailureTrigger],selected_code:FailureCode,
  selected_scope:FailureScope,logical_tick:U53}
StructuralTraceReceipt = OBJ{v:CONST[mcore.v7],receipt_handle:HANDLE26,
  cell:CellIdentity,actor_input_sha256:HEX64,public_trace_without_endpoint_sha256:HEX64,
  model_turn_sha256s:VEC[1..1024,HEX64],parse_sha256s:VEC[1..1024,HEX64],
  rpc_sha256s:VEC[0..64,HEX64],mount_sha256:HEX64,control_sha256:OPT[HEX64],
  compiler_case_sha256s:VEC[0..64,HEX64],
  failure_decision:FailureDecisionReceipt,structurally_valid:BIT,
  logical_tick:U53}
EndpointOpenReceipt = OBJ{v:CONST[mcore.v7],open_handle:HANDLE26,
  endpoint_seal_sha256:HEX64,structural_receipt_sha256:HEX64,
  authorizing_schedule_event_sha256:HEX64,opened_endpoint_bytes_sha256:HEX64,
  logical_tick:U53}
EndpointReceipt = OBJ{v:CONST[mcore.v7],cell:CellIdentity,
  actor_input_sha256:HEX64,trace_sha256:HEX64,environment_sha256:HEX64,
  mount_instance_sha256:HEX64,seal_sha256:HEX64,
  structural_receipt_sha256:HEX64,open_receipt_sha256:HEX64,
  endpoint_failure_decision:FailureDecisionReceipt,
  trace_valid:CONST[1],endpoint:BIT,failure_code:FailureCode}

CompilerCaseReceipt = OBJ{v:CONST[mcore.v7],cell_handle:HANDLE26,
  invocation_sha256:HEX64,input_sha256:HEX64,decision_sha256:HEX64,
  phase:ENUM[SOURCE,LINK,PAD,NEW],status:ENUM[ADMIT,NO_ADMISSION],
  template_selectors:VEC[0..2,U53],prefix_receipt:PrefixReceipt,
  provenance_projection_receipt:ProjectionReceipt,passed:BIT}
CompilerAggregateReceipt = OBJ{v:CONST[mcore.v7],root:RootRef,
  expected_cell_handles:VEC[1..10000,HANDLE26],
  cases:VEC[1..10000,CompilerCaseReceipt],source_count:U53,link_count:U53,
  pad_count:U53,new_count:U53,admit_count:U53,no_admission_count:U53,
  missing_count:U53,extra_count:U53,passed:BIT}
ProvenanceNode = OBJ{node_handle:HANDLE26,origin:ENUM[AUTHENTIC,DERIVED_CONTROL],
  object_sha256:HEX64,transform:ENUM[NONE,SOURCE_OUTCOME_REBIND,
    DREAM_LINK_REBIND,PAYLOAD_SWAP],donor_event_handles:VEC[0..16,HANDLE26]}
ProvenanceReceipt = OBJ{v:CONST[mcore.v7],root:RootRef,
  nodes:VEC[1..10000,ProvenanceNode],projection_sha256s:VEC[1..10000,HEX64],
  root_sha256:HEX64,passed:BIT}
ProjectionReceipt = OBJ{v:CONST[mcore.v7],projection_handle:HANDLE26,
  compiler_input_sha256:HEX64,audit_provenance_sha256:HEX64,
  forbidden_field_count:CONST[0],projection_rule_sha256:HEX64,passed:BIT}
PrefixReceipt = OBJ{v:CONST[mcore.v7],left_sha256:HEX64,right_sha256:HEX64,
  identical:BIT,first_difference_offset:OPT[U53],
  first_difference_json_pointer:OPT[STRING],difference_map_handle:HANDLE26,
  exact_match_outside_bitmap:BIT,passed:BIT}
AclCase = OBJ{capability:ENUM[CHILD,ACTOR,READER,COMPILER,ENDPOINT,AUDIT],
  object_type:STRING,access:ENUM[ALLOW,DENY],passed:BIT}
AclReceipt = OBJ{v:CONST[mcore.v7],root:RootRef,
  cases:VEC[1..100000,AclCase],namespace_isolation_passed:BIT,passed:BIT}
BfsCertificate = OBJ{v:CONST[mcore.v7],root:RootRef,
  transition_table_sha256:HEX64,mount_table_sha256:HEX64,
  candidate_table_sha256:HEX64,canonical_returns_sha256:HEX64,
  legal_request_union_sha256:HEX64,adaptive_policy_grammar_sha256:HEX64,
  availability_parameter_roster_sha256:HEX64,policy_count:U64D,
  full_min_reads:CONST[3],
  atoms_min_reads:CONST[4],full_new_min_reads:CONST[2],
  every_cut_unreachable:BIT,no_adaptive_bypass:BIT,witness_sha256:HEX64,
  passed:BIT}
FakeClockCase = OBJ{delay_ns:U64D,expected:ENUM[RELEASE,OVERRUN],
  observed:ENUM[RELEASE,OVERRUN],continuation_count:U53,passed:BIT}
FakeClockReceipt = OBJ{v:CONST[mcore.v7],rpc_machine_sha256:HEX64,
  cases:VEC[3..64,FakeClockCase],passed:BIT}
EpisodeAuditEnvelope = OBJ{v:CONST[mcore.v7],cell:CellIdentity,
  actor_input_sha256:HEX64,model_turn_sha256s:VEC[1..1024,HEX64],
  public_trace_sha256:HEX64,rpc_sha256s:VEC[0..64,HEX64],
  scorer_sha256s:VEC[0..64,HEX64],compiler_case_sha256s:VEC[0..64,HEX64],
  structural_receipt_sha256:HEX64,endpoint_receipt_sha256:OPT[HEX64],
  provenance_sha256:HEX64}

GateInputRole = ENUM[PACKAGE,CHECKER,WRITER_QUALIFICATION,
  READER_QUALIFICATION,MODEL_TURN,PAIR_SELECTION,SUPPORT,COMPILER,
  PROVENANCE,ACL,BFS,RPC,CLOCK,RESET,MOUNT,INTERFACE,NONHARM,EXTRACTION,WORK,
  PAD_WORK,INFERENCE_MATCH,
  FULL_ENDPOINT,CONTROL_ENDPOINT,GOAL_CUE,CANDIDATE_ORDER,ISOLATION,
  GATE_S,GATE_M,GATE_U,GATE_W,GATE_F,GATE_R]
GateInputSpec = OBJ{requirement_handle:HANDLE26,role:GateInputRole,
  root_type:STRING,object_handle:HANDLE26,required_bit:BIT}
GateInputReceipt = OBJ{requirement_handle:HANDLE26,
  requirement_sha256:HEX64,object_sha256:HEX64,observed_bit:BIT}
GateRoster = OBJ{gate:ENUM[S,M,U,W,F,R,Q_S1,TEXT],
  inputs:VEC[1..100000,GateInputSpec]}
RootGateRosters = OBJ{v:CONST[mcore.v7],root:RootRef,
  rosters:VEC[8,GateRoster]}
ComponentGateReceipt = OBJ{v:CONST[mcore.v7],root:RootRef,
  gate:ENUM[S,M,U,W,F,R],roster_sha256:HEX64,
  inputs:VEC[1..100000,GateInputReceipt],all_present:BIT,all_passed:BIT,gate_bit:BIT,
  failure_decision:FailureDecisionReceipt}
NumericComponentResult = OBJ{component:ENUM[S,M,U,W],gate:BIT,
  contrast:OPT[F64HEX],indicator:BIT}
RComponentResult = OBJ{component:CONST[R],gate:BIT,r_value:BIT,indicator:BIT}
FDiagnosticResult = OBJ{component:CONST[F],gate:BIT,contrast:OPT[F64HEX]}
QS1Receipt = OBJ{v:CONST[mcore.v7],root:RootRef,roster_sha256:HEX64,
  inputs:VEC[1..100000,GateInputReceipt],q_s1:BIT,
  predecessor_schedule_head_sha256:HEX64,logical_tick:U53}
TextRootReceipt = OBJ{v:CONST[mcore.v7],root:RootRef,roster_sha256:HEX64,
  inputs:VEC[1..100000,GateInputReceipt],t_r:BIT,
  failure_decision:FailureDecisionReceipt}
IndicatorIsolationReceipt = OBJ{v:CONST[mcore.v7],root:RootRef,
  common_root_function_sha256:HEX64,iid_seed_law_sha256:HEX64,
  iid_noise_distribution_sha256:HEX64,common_component_function_sha256:HEX64,
  root_index_label_only:BIT,
  no_cross_root_input:BIT,no_shared_mutable_state:BIT,
  all_execution_inputs_receipted:BIT,ambiguous_shared_cause:BIT,passed:BIT}
```

### 11.8 Failure table and program schedule

```text
FailureScope = ENUM[GLOBAL_INVALID,ROOT_INVALID,VALID_ENDPOINT_FAILURE,NONE]
FailureCode = ENUM[NONE,GLOBAL_PACKAGE_MEMBER,GLOBAL_MERKLE,GLOBAL_SCHEMA,
  GLOBAL_CHECKER,GLOBAL_CAPABILITY,GLOBAL_SHARED_STATE,GLOBAL_BINDING,
  GLOBAL_PROTOCOL_MUTATION,GLOBAL_ENTROPY,GLOBAL_COMMON_NUISANCE,
  GLOBAL_UNKNOWN,ROOT_CHILD_OMISSION,ROOT_MALFORMED_ACTION,ROOT_FIT_CRASH,
  ROOT_FIT_TIMEOUT,ROOT_RPC_OVERRUN,ROOT_UNAVAILABLE_FOUND,
  ROOT_INTERVENTION_MISMATCH,ROOT_LOCAL_DEVICE,ROOT_EXTRACTION_FAILURE,
  ROOT_WORK_MISMATCH,ROOT_INTERFACE_FAILURE,ROOT_CANARY_FAILURE,
  ROOT_NONHARM_FAILURE,VALID_WRONG_ROUTE,VALID_WRONG_ACTION,
  VALID_WRONG_TERMINAL,VALID_BUDGET_EXHAUSTED,VALID_READ_MISS,
  VALID_CUT_ENDPOINT,VALID_SWAP_ENDPOINT,VALID_INCOMPLETE_ENDPOINT]
FailureTrigger = ENUM[PACKAGE_MEMBER_MISMATCH,MERKLE_MISMATCH,SCHEMA_MISMATCH,
  CHECKER_MISMATCH,CAPABILITY_LEAK,SHARED_STATE,STATIC_BINDING_MISMATCH,
  PROTOCOL_MUTATION,ENTROPY_FAILURE,COMMON_NUISANCE_MISMATCH,UNKNOWN_BOUNDARY,
  CHILD_OMISSION,MALFORMED_OR_UNCUSTODIED_ACTION,FIT_CRASH,FIT_TIMEOUT,
  RPC_OVERRUN,UNAVAILABLE_OR_FILLER_FOUND,INTERVENTION_MISMATCH,
  LOCAL_DEVICE_FAILURE,EXTRACTION_FAILURE,RUNTIME_WORK_MISMATCH,
  INTERFACE_FAILURE,CANARY_FAILURE,NONHARM_FAILURE,WRONG_ROUTE,WRONG_ACTION,
  WRONG_TERMINAL,BUDGET_EXHAUSTED,READ_MISS,CUT_ENDPOINT,SWAP_ENDPOINT,
  INCOMPLETE_ENDPOINT]
FailureDecisionRow = OBJ{priority:U53,trigger:FailureTrigger,code:FailureCode,
  scope:FailureScope,predicate_rule_sha256:HEX64,
  required_receipt_root_type:STRING}
FailureDecisionTable = OBJ{v:CONST[mcore.v7],rows:VEC[32,FailureDecisionRow],
  empty_trigger_code:CONST[NONE],selection_rule:CONST[LOWEST_PRIORITY]}

ProgramState = ENUM[PACKAGE_CHECK,QUALIFICATION,TEXT_INITIAL,TEXT_EXTENSION,
  TEXT_FINAL_GATE,DEV_D1D2_S1,DEV_D1D2_S2,DEV_LATE_ROOTS,
  DEV_MECHANICS_GATE,CONF_ROOTS,TEST_S,TEST_M,TEST_U,TEST_W,TEST_R,
  COMPLETE,STOPPED,INVALID]
StoppingKind = ENUM[PACKAGE_GATE,QUALIFICATION_GATE,TEXT_EXTENSION_GATE,
  TEXT_FINAL_GATE,DEV_S1_GATE,DEV_D1D2_R_GATE,DEV_ROOT_S2_GATE,
  DEV_MECHANICS_GATE,CONF_ROOT_S2_GATE,TEST_S_GATE,TEST_M_GATE,
  TEST_U_GATE,TEST_W_GATE,TEST_R_GATE]
ProgramPredicateOutcome = ENUM[PASS,FAIL,EXTEND,OPEN_S2,SKIP_S2,
  OPEN_LATE_ROOTS,SKIP_LATE_ROOTS,OPEN_CONF,SKIP_CONF,REJECT,NONREJECT]
ProgramBranch = OBJ{outcome:ProgramPredicateOutcome,
  state_after:ProgramState,decision:ENUM[OPEN,SKIP,STOP,CONTINUE],
  open_kind:ENUM[NONE,FILES,ALLOCATION,LAUNCH]}
ProgramTransitionRule = OBJ{rule_handle:HANDLE26,kind:StoppingKind,
  state_before:ProgramState,predicate_rule_sha256:HEX64,
  branches:VEC[2..4,ProgramBranch]}
ProgramMachine = OBJ{v:CONST[mcore.v7],initial:CONST[PACKAGE_CHECK],
  rules:VEC[14,ProgramTransitionRule],terminal_states:CONST[[COMPLETE,STOPPED,INVALID]]}
ScheduleInputRole = ENUM[PACKAGE_CHECK,WRITER_QUALIFICATION,
  READER_QUALIFICATION,TEXT_ROOT_RESULT,TEXT_PASS_COUNT,Q_S1_D1,Q_S1_D2,
  Q_S1_ROOT,I_R_D1,I_R_D2,LATE_DEV_ROOT_RESULT,DEV_I_R_COUNT,CONF_ROOT_RESULT,
  COMPONENT_STATISTIC,GLOBAL_FAILURE]
ScheduleInputRef = OBJ{role:ScheduleInputRole,root_type:STRING,
  object_sha256:HEX64}
ScheduleEvent = OBJ{v:CONST[mcore.v7],event_handle:HANDLE26,
  kind:StoppingKind,state_before:ProgramState,state_after:ProgramState,
  inputs:VEC[1..100000,ScheduleInputRef],
  predicate_outcome:ProgramPredicateOutcome,
  decision:ENUM[OPEN,SKIP,STOP,CONTINUE],
  logical_tick:U53,monotonic_ns:U64D,previous_event_sha256:OPT[HEX64]}
OpenEvent = OBJ{v:CONST[mcore.v7],open_handle:HANDLE26,
  kind:ENUM[FILES,ALLOCATION,LAUNCH],target_handle:HANDLE26,
  authorizing_schedule_event_sha256:HEX64,logical_tick:U53,
  monotonic_ns:U64D}
StoppingReceipt = OBJ{v:CONST[mcore.v7],schedule_event:ScheduleEvent,
  rule_sha256:HEX64,open_events:VEC[0..100000,OpenEvent],passed:BIT}
```

There are 32 nonempty triggers and 33 FailureCodes including NONE. Static
tokenizer/alias/handle collision, tensor-shape, and RPC-overflow checks use
`SCHEMA_MISMATCH`; physical RPC overrun uses `RPC_OVERRUN`; runtime matched-work
uses `RUNTIME_WORK_MISMATCH`. The semantic checker requires one-to-one trigger
coverage and the exact scope/code mapping in Section 9.

### 11.9 Root/cohort/program results

```text
FitAttemptReceipt = OBJ{v:CONST[mcore.v7],attempt_handle:HANDLE26,
  root:RootRef,stage:ENUM[S1,S2],carrier:CarrierId,
  launch_event_sha256:HEX64,status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT],
  device_interval_handles:VEC[1..64,HANDLE26],deck_sha256:HEX64,
  optimization_receipt_sha256:OPT[HEX64],artifact_sha256:OPT[HEX64],
  failure_decision:FailureDecisionReceipt}
ExecutionAttemptReceipt = OBJ{v:CONST[mcore.v7],attempt_handle:HANDLE26,
  root:OPT[RootRef],kind:ENUM[TEXT_ACTOR,TEXT_READER,EVAL_ACTOR,EVAL_READER,
    WRITER_QUALIFICATION,READER_QUALIFICATION,CPU_MATERIALIZER,CPU_CHECKER,
    CPU_COMPILER],launch_event_sha256:HEX64,
  status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT],
  interval_handles:VEC[1..64,HANDLE26],artifact_sha256:OPT[HEX64],
  failure_decision:FailureDecisionReceipt}
ScienceRootResult = OBJ{v:CONST[mcore.v7],cohort:ENUM[DEV,CONF],root:RootRef,
  q_s1:QS1Receipt,numeric_components:VEC[4,NumericComponentResult],
  r_component:RComponentResult,f_diagnostic:FDiagnosticResult,
  component_gate_receipts:VEC[6,ComponentGateReceipt],
  endpoint_receipts:VEC[1..100000,EndpointReceipt],
  compiler_aggregate:CompilerAggregateReceipt,
  indicator_isolation:IndicatorIsolationReceipt,
  fit_attempts:VEC[0..6,FitAttemptReceipt],
  execution_attempts:VEC[0..100000,ExecutionAttemptReceipt],
  terminal_failure:FailureDecisionReceipt}
TextRootResult = OBJ{v:CONST[mcore.v7],cohort:CONST[TEXT],root:RootRef,
  text_receipt:TextRootReceipt,endpoint_receipts:VEC[1..100000,EndpointReceipt],
  compiler_aggregate:CompilerAggregateReceipt,
  execution_attempts:VEC[0..100000,ExecutionAttemptReceipt],
  terminal_failure:FailureDecisionReceipt}
AbortedRootResult = OBJ{v:CONST[mcore.v7],cohort:ENUM[TEXT,DEV,CONF],
  root:RootRef,detected_at_schedule_head_sha256:HEX64,
  fit_attempts:VEC[0..6,FitAttemptReceipt],
  execution_attempts:VEC[0..100000,ExecutionAttemptReceipt],
  completed_endpoint_receipts:VEC[0..100000,EndpointReceipt],
  completed_compiler_case_receipts:VEC[0..100000,CompilerCaseReceipt],
  terminal_failure:FailureDecisionReceipt}
UnscheduledRootResult = OBJ{v:CONST[mcore.v7],cohort:ENUM[TEXT,DEV,CONF],
  root:RootRef,reason:ENUM[TEXT_STOP,DEV_S1_STOP,DEV_D1D2_R_STOP,
    DEV_MECHANICS_STOP,UPSTREAM_GLOBAL_FAILURE,ROOT_Q_S1_FALSE],
  authorizing_schedule_event_sha256:HEX64,fit_attempts:CONST[[]],
  execution_attempts:CONST[[]]}
RootResult = ONEOF[ScienceRootResult,TextRootResult,AbortedRootResult,
  UnscheduledRootResult]
RootAuditReceipt = OBJ{v:CONST[mcore.v7],root:RootRef,
  checker:CheckerReceipt,acl:AclReceipt,bfs:BfsCertificate,
  clock:FakeClockReceipt,schedule_receipts:VEC[1..1000,StoppingReceipt],
  work_receipts:VEC[0..2,PairwiseWorkReceipt],
  pad_work_receipt:OPT[PadWorkReceipt],
  interface_receipts:VEC[0..10,InterfaceCanaryReceipt],
  nonharm_receipts:VEC[0..10,NonharmReceipt],
  extraction_receipts:VEC[0..10,ExtractionReceipt],
  reader_acceptance_receipts:VEC[0..10,ReaderAcceptanceReceipt],
  inference_match_receipts:VEC[0..1000,InferenceMatchReceipt]}
RootResultBundleManifest = OBJ{v:CONST[mcore.v7],
  package_manifest_sha256:HEX64,materialized_root_manifest_sha256:HEX64,
  root:RootRef,cohort:ENUM[TEXT,DEV,CONF],members:VEC[1..100000,ManifestMember],
  merkle_root_sha256:HEX64,root_result:RootResult,
  process_births:VEC[0..100000,ProcessBirthReceipt],
  reset_receipts:VEC[0..100000,ResetReceipt],
  process_teardowns:VEC[0..100000,ProcessTeardownReceipt],
  model_turns:VEC[0..100000,ModelTurnReceipt],
  public_traces:VEC[0..100000,PublicTrace],
  runtime_mount_receipts:VEC[0..100000,RuntimeMountReceipt],
  scorer_receipts:VEC[0..100000,ScorerReceipt],
  rpc_receipts:VEC[0..100000,RpcReceipt],
  provenance_receipts:VEC[0..100000,ProvenanceReceipt],
  training_tensor_receipts:VEC[0..100000,TrainingTensorReceipt],
  optimization_receipts:VEC[0..6,OptimizationReceipt],
  sealed_endpoints:VEC[0..100000,SealedEndpoint],
  structural_receipts:VEC[0..100000,StructuralTraceReceipt],
  endpoint_open_receipts:VEC[0..100000,EndpointOpenReceipt],
  episode_audits:VEC[0..100000,EpisodeAuditEnvelope],
  root_audit:OPT[RootAuditReceipt]}

CohortFailureReceipt = OBJ{v:CONST[mcore.v7],target:ENUM[PROGRAM,TEXT,DEV,CONF],
  failure_decision:FailureDecisionReceipt,schedule_head_sha256:HEX64,
  finalized_root_result_manifest_sha256s:VEC[0..16,HEX64],
  unopened_root_indices:VEC[0..16,U53],
  unopened_cell_handles:VEC[0..100000,HANDLE26],scientific_test:CONST[null]}
ComponentStatistic = OBJ{component:ENUM[S,M,U,W,R],n:CONST[16],
  successes:U53,tail_numerator:U53,tail_denominator:CONST[65536],
  p_value:F64HEX,cp_lower:F64HEX,rejected:BIT,post_stop:BIT}
CohortResultBundleManifest = OBJ{v:CONST[mcore.v7],
  package_manifest_sha256:HEX64,materialized_cohort_manifest_sha256:HEX64,
  cohort:ENUM[TEXT,DEV,CONF],members:VEC[8..100000,ManifestMember],
  merkle_root_sha256:HEX64,root_result_manifest_sha256s:VEC[8..16,HEX64],
  stopping_receipt_sha256s:VEC[1..1000,HEX64],
  statistics:VEC[0..5,ComponentStatistic],
  cohort_failure:OPT[CohortFailureReceipt]}
UnscheduledCohortResult = OBJ{cohort:ENUM[TEXT,DEV,CONF],
  reason:ENUM[PACKAGE_FAILED,QUALIFICATION_FAILED,TEXT_FAILED,DEV_FAILED,
    GLOBAL_FAILURE],authorizing_schedule_event_sha256:HEX64,
  cohort_manifest_sha256:CONST[null]}
ProducedCohortResult = OBJ{cohort:ENUM[TEXT,DEV,CONF],
  cohort_manifest_sha256:HEX64}
InvalidCohortResult = OBJ{cohort:ENUM[TEXT,DEV,CONF],
  failure:CohortFailureReceipt,cohort_manifest_sha256:OPT[HEX64]}
CohortDisposition = ONEOF[UnscheduledCohortResult,ProducedCohortResult,
  InvalidCohortResult]
QualificationResultBundleManifest = OBJ{v:CONST[mcore.v7],
  package_manifest_sha256:HEX64,members:VEC[1..100000,ManifestMember],
  merkle_root_sha256:HEX64,receipts:VEC[2,QualificationReceipt],
  process_births:VEC[0..100000,ProcessBirthReceipt],
  reset_receipts:VEC[0..100000,ResetReceipt],
  process_teardowns:VEC[0..100000,ProcessTeardownReceipt],
  model_turns:VEC[0..100000,ModelTurnReceipt],
  runtime_mount_receipts:VEC[0..100000,RuntimeMountReceipt],
  row_parse_receipts:VEC[0..100000,MemoryRowParseReceipt],
  tensor_receipts:VEC[0..100000,TrainingTensorReceipt],
  scorer_receipts:VEC[0..100000,ScorerReceipt],
  rpc_receipts:VEC[0..100000,RpcReceipt]}
ProgramResultIndex = OBJ{v:CONST[mcore.v7],package_manifest_sha256:HEX64,
  qualification_manifest_sha256:OPT[HEX64],
  cohort_dispositions:VEC[3,CohortDisposition],schedule_head_sha256:HEX64,
  stopping_receipt_sha256s:VEC[1..1000,HEX64],
  program_failure:OPT[CohortFailureReceipt],cost_ledger:CostLedger,
  cost_report:CostReport,members:VEC[1..100000,ManifestMember],
  merkle_root_sha256:HEX64}
```

### 11.10 Central cost types

```text
DeckId = ENUM[NONE,S1,S2,TEXT,EVAL,WRITER_QUAL,READER_QUAL,MIXED]
DeviceInterval = OBJ{interval_handle:HANDLE26,lease_handle:HANDLE26,
  device_uuid:STRING,image_sha256:HEX64,driver_sha256:HEX64,
  runtime_sha256:HEX64,owner_process_handle:HANDLE26,ownership:CONST[EXCLUSIVE],
  category:ENUM[FIT,TEXT,EVAL,QUALIFICATION,MIXED],deck:DeckId,
  attempt_handle:HANDLE26,clock_source_sha256:HEX64,
  allocation_ns:U64D,release_ns:U64D,
  status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT]}
CpuInterval = OBJ{interval_handle:HANDLE26,process_handle:HANDLE26,
  category:ENUM[MATERIALIZER,CHECKER,COMPILER],attempt_handle:HANDLE26,
  clock_source_sha256:HEX64,start_ns:U64D,release_ns:U64D,
  status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT]}
DurationInterval = OBJ{interval_handle:HANDLE26,
  category:ENUM[QUEUE,RESET,SERIALIZATION],attempt_handle:HANDLE26,
  clock_source_sha256:HEX64,start_ns:U64D,release_ns:U64D,
  status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT]}
CostLedger = OBJ{v:CONST[mcore.v7],device_intervals:VEC[0..100000,DeviceInterval],
  cpu_intervals:VEC[0..100000,CpuInterval],
  duration_intervals:VEC[0..100000,DurationInterval],
  unique_interval_handles:BIT,all_attempt_references_resolve:BIT}
DeviceUnionSegment = OBJ{segment_handle:HANDLE26,lease_handle:HANDLE26,
  device_uuid:STRING,start_ns:U64D,release_ns:U64D,
  image_sha256:HEX64,driver_sha256:HEX64,runtime_sha256:HEX64,
  contributing_interval_handles:VEC[1..100000,HANDLE26],
  contributing_attempt_handles:VEC[1..100000,HANDLE26],
  contributing_categories:VEC[1..5,ENUM[FIT,TEXT,EVAL,QUALIFICATION,MIXED]],
  contributing_statuses:VEC[1..4,ENUM[COMPLETE,CRASH,TIMEOUT,ABORT]],
  attributed_category:ENUM[FIT,TEXT,EVAL,QUALIFICATION,MIXED],
  attributed_status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT,MIXED]}
CostBucket = OBJ{bucket_handle:HANDLE26,
  category:ENUM[FIT,TEXT,EVAL,QUALIFICATION,MIXED,CPU,QUEUE,RESET,SERIALIZATION],
  status:ENUM[COMPLETE,CRASH,TIMEOUT,ABORT,MIXED],deck:DeckId,
  device_uuid:OPT[STRING],image_sha256:OPT[HEX64],runtime_sha256:OPT[HEX64],
  contributor_handles:VEC[1..100000,HANDLE26],attempt_count:U53,
  nanoseconds:U64D}
ValidCostSummary = OBJ{v:CONST[mcore.v7],valid:CONST[1],
  union_segments:VEC[0..100000,DeviceUnionSegment],
  buckets:VEC[0..100000,CostBucket],device_total_ns:U64D,cpu_total_ns:U64D,
  queue_total_ns:U64D,reset_total_ns:U64D,serialization_total_ns:U64D,
  nonoverlap_passed:CONST[1],partition_passed:CONST[1]}
InvalidCostSummary = OBJ{v:CONST[mcore.v7],valid:CONST[0],
  failure_code:CONST[GLOBAL_UNKNOWN],offending_handles:VEC[1..100000,HANDLE26],
  device_total_ns:CONST[null],cpu_total_ns:CONST[null],
  queue_total_ns:CONST[null],reset_total_ns:CONST[null],
  serialization_total_ns:CONST[null],buckets:CONST[null]}
CostReport = ONEOF[ValidCostSummary,InvalidCostSummary]
```

### 11.11 Mandatory semantic constraints

The independent checker enforces every rule below from typed objects; no rule
may read a raw log blob or ambient path.

- The package JSON paths in Section 1.2 map one-to-one to their displayed root
  schemas through `SchemaBinding.path_pattern`. Package members are
  package-relative and lack a `package/` prefix. Materialized/result path
  patterns map to `ExpectedRootContentManifest`,
  `MaterializedRootBundleManifest`, `MaterializedCohortBundleManifest`,
  `RootResultBundleManifest`, `CohortResultBundleManifest`,
  `QualificationResultBundleManifest`, and `ProgramResultIndex`. Every JSON
  member has the exact non-null root type; non-JSON has null.
- Build phases occur exactly in Section-1.1 order. The entropy seal excludes
  its own bytes plus expected/final package hashes; its static-draft digest
  vector is the exact predeclared roster of every other phase-1 input. Its 32
  roots occur in fixed `[TEXT0..7,DEV0..7,CONF0..15]` call order, each seed is
  exactly 32 bytes, and seed/commitment values are unique. Expected roots bind
  the entropy seal; final
  package binds expected roots; rematerialized roots bind final package and
  byte-match expected content. Each 14-member root manifest contains exactly
  the literal Section-1.4 paths/types. The RootMaterializationReceipt binds the
  other 13 members only, so neither its digest nor either Merkle root is
  self-referential.
- The root generator's DomainSpecs equal DrawPlan domains exactly. DrawStep
  ordinals are consecutive, all population handles resolve to EventStrata or
  AliasPool, every rejection advances its counter, and receipts expose every
  draw/rejection/final counter. Every draw and stratum uses one closed
  AssignmentTarget and a package-enumerated handle class; no free-form target
  or ambient draw exists. Handle test vectors implement the two-leading-
  zero/26-symbol codec. Handles are unique within `(root namespace,handle
  class)`; every concrete table lookup includes the root namespace; cross-root
  reuse is legal and no API accepts an unscoped handle. device_s1/device_s2
  resolve to distinct draw results in DeviceEligibilityRoster (they may name
  the same physical device only if the independent draws coincide); every
  realized DeviceInterval and PairwiseWorkReceipt exactly matches the selected
  roster entry's UUID/image/driver/runtime. The DEVICES EventStratum is a
  byte-identical indexed projection of DeviceEligibilityRoster; the six
  condition permutations are the lexicographically ordered permutations of
  the stage's displayed triplet, and candidate orders are exactly P0..P3.
- RootGeometry contains exactly two 1/0/0/0 lanes, three 1/1/0/0, and three
  1/0/1/0. PairCandidates are the 28 unordered pairs exactly once, selection
  action handles are distinct, useful pair matches the preassigned draw, u_d
  is one member, dream_shift is 1..7, and both h branches exist.
- Every child/deployment parsed decision is the sole object in one
  ModelTurnReceipt. Continuation bytes retokenize to token_ids, the draw ledger
  reproduces them, DecisionParseReceipt input equals continuation, its parser
  produces exactly one closed ParsedDecision with no repair/extra object, and
  result_object_sha256 is the one corresponding
  request/action/selection/declaration event. That event cites the turn handle
  and matches the parsed fields. logical_end_tick is strictly greater than
  logical_start_tick and turn ordinals are consecutive within the named fresh
  process. READ request and later RPC return are distinct
  events; no turn receipt contains a future return.
- ActorEpisodeInput has exactly one child task and null goal/menu/law/codebook
  plus an empty public-new-template-ref vector in childhood; B/D have the
  matching goal and null child task; C has CGoal and menu with null child task.
  C_PROBE pairs only with action_budget=1 and C_LIVE only with action_budget=2.
  Experiment law/codebook and public NEW references are absent/empty until the
  typed post-source-choice reveal and are then copied byte-identically into
  later C inputs. The reveal has selectors 0/1 exactly once and its row handles
  equal the compiler-only NewRowTemplate handles, but exposes no row payload.
  Every phase exposes only its registered query/action families.
- Each process's unique ProcessBirthReceipt precedes and names its first
  operation; actor/child first operations are their ResetReceipt's first turn,
  reader/writer first operations are their first Scorer/Optimization receipt;
  ResetReceipt recomputes empty context/fresh process/birth checkpoint and
  allowed carrier; ProcessTeardownReceipt follows the typed terminal. A
  process, turn, or episode handle cannot be reused, and no raw child/parent
  text survives into deployment.
  For CHILD/DEPLOYMENT_ACTOR, scope_handle equals ModelTurnReceipt.episode_handle
  and terminal_operation_handle equals the PublicTrace terminal event; for
  READER/WRITER it equals the qualification/fit or scoring-attempt scope and
  the last typed operation. RuntimeMountReceipt process handles resolve these
  births and match its mount_target.
- PairSelectionEvent binds eight distinct lane handles, all 28 PairCandidates,
  the selected action, and the exact two lanes mapped by that candidate. It
  follows all 32 ablation action/observation pairs. SupportRevealEvent is later,
  its fixture/action handles are disjoint from ablation, and SupportBindings
  form one bijection over selected lanes x four trial kinds. Each binding's
  action matches its reveal slot and its later observation cites that action.
- The compiler-facing Source evidence is always eight PresentedSourcePairs of
  one identical shape. No provenance tag/donor/condition byte is serializable.
  The checker alone verifies FULL projection from authenticated leaves and the
  presealed SOURCE_DERANGED donor mapping. SOURCE emits the two exact templates
  mechanically selected by displayed counts.
- ExperimentLawReveal follows source choice and precedes declaration/dispatch/
  outcome. Its four entries biject the menu: the authentic preferred family is
  H and ONE_MINUS_H once each and the other two are NUISANCE. The codebook has
  exactly two observation handles mapped 0/1. For H/ONE_MINUS_H, declaration
  predictions and row map have length two in h0/h1 order and equal the public
  law; for NUISANCE both arrays are empty. Dispatch cites declaration and is in
  the committed source family. NEW templates have selectors 0 and 1 exactly
  once; compiler derives h from relation+outcome and copies that template, or
  emits NO_ADMISSION for nuisance. No hidden b/h/z or declaration-only mapping
  is consulted.
- Every PrefixReceipt recomputes both canonical byte strings. `identical=1`
  iff both first-difference fields are null; otherwise both fields identify
  the actual first differing byte/pointer and all other differences are
  exactly the named complete bitmap.
- Transition tables contain every state/action surface exactly once plus all
  autonomous outcome, compiler, and terminal edges. Every actor state has 32
  token-isomorphic surfaces; pair selection has 28 valid+4 invalid. C outcome
  and compiler edges are autonomous, EpisodeTerminal is present in every
  completed trace, and registered B/C/D budgets/traces equal Section 5.4.
- Every legal request is the deterministic query-specific projection of goal
  and current state. Each root/mount/request has exactly one 32-slot candidate
  projection. CUT replaces the target before scoring with a registered matched
  filler; NO_CARRIER uses fillers; payload/count swaps retain row handle and all
  nonpayload bytes. ScorerReceipt enumerates exactly those 32 inputs. Any filler
  or unavailable FOUND is invalid. CanonicalReturns is total over every legal
  mount/request. The BFS binds the request union, adaptive-policy grammar,
  mount-specific availability-parameter roster, and canonical-return table;
  it enumerates every adaptive legal READ policy for every roster member and proves
  FULL=3, ATOMS=4, FULL_NEW=2 minima and all cuts unreachable.
  Every RuntimeMountReceipt for a trained carrier has an artifact hash equal
  to its sole COMPLETE
  FitAttemptReceipt artifact; BIRTH/NO_CARRIER use null, and TEXT carrier
  hashes resolve to the sealed supplied-row artifact. Controls never change
  this hash unless their literal carrier is NO_CARRIER. Its mount/projection
  hashes equal the pre-materialized MountInstance and it names the episode's
  fresh process; StructuralTraceReceipt.mount_sha256 resolves to this typed
  runtime receipt rather than to an ambient mount claim.
  Scientific/TEXT mount receipts have non-null root and null qualification
  case; qualification mounts have null root and the exact non-null case handle.
  mount_target ACTOR or READER has exactly one role-matching process handle;
  BOTH has exactly two in `[ACTOR,READER]` order.
- GoalPairByteCutReceipt recomputes the exact first differing byte/pointer of
  the two ordinary B inputs; that pointer and every set bit are under `/goal/`,
  every byte outside `/goal/` is equal, and the common public-pair/actor/decode/
  catalog digest matches. The FULL goal-cue mount changes only the route-cue
  field plus the registered mechanically derived closure and still uses the
  original target/terminal path.
- CarrierId and ControlId are used everywhere. S1 condition order is a
  permutation of FULL_OLD/SOURCE_DERANGED_OLD/DREAM_DERANGED_OLD; S2 is a
  permutation of FULL_NEW_H0/FULL_NEW_H1/FULL_OLD_PLUS_PAD. Per-phase control
  order contains each applicable ControlId exactly once. The registry contains
  all 21 IDs once. FULL_GOAL_CUE_SWAP_B uses GOAL_CUE_SWAP mutation; its complete
  difference closure permits only route-cue and descendants. All CUT/swap/PAD/
  NO_SLEEP2 endpoints equal Section 5.5.
- ReaderBinding/RpcMachine clock, worker image, scorer count, frame, padding,
  threshold, and margin fields match. All numeric F64HEX values are finite,
  canonical, and recomputed; no arbitrary STRING encodes a number. Every RPC
  frame is 16384 bytes, request+return ticks differ by one, and overrun has no
  continuation. Every registered positive/control comparison has an
  InferenceMatchReceipt: identical decode and initial RNG state, identical
  draw rule and public prefix through the first registered intervention, and
  complete post-intervention draw-ledger addresses. A missing or false match
  receipt invalidates its component rather than becoming a zero.
- Every BLOB base64url-decodes canonically without padding; decoded length and
  SHA-256 equal its byte_length and sha256 fields. U64D has no leading zero
  except literal `0`; HANDLE26/HEX64/F64HEX are lowercase canonical byte
  encodings. Any mismatch is GLOBAL_SCHEMA.
- Writer/Reader bindings point to specs that contain no binding/result hash.
  Specs are hashed into bindings; later receipts bind package+binding+spec.
  ActorBinding, WriterBinding, ReaderBinding, and AliasPool use one identical
  tokenizer SHA; every AliasCandidate token_ids vector is its exact encoding.
  Writer and reader qualification contain exactly their eight mandatory kinds,
  occur in `[WRITER,READER]` receipt order, every case passes, and no
  TEXT/reader/M open event precedes both acceptances. Every case hash resolves
  one-to-one to the typed turn/tensor/scorer/RPC objects in the qualification
  bundle; every row_parser_sha256 resolves to one MemoryRowParseReceipt and
  every actor parser hash resolves to the embedded DecisionParseReceipt. No
  unlisted execution output can satisfy acceptance.
- Each triplet has exactly three fit attempts on its registered common device
  and order. PairwiseWorkReceipt checks all optimizer/RNG/tensor/mask/work fields.
  S1/S2 deck membership equals Section 6.2; d_pad is gradient-bearing and
  grounded; every tensor names one complete AllowedTensorDifference and its
  stored bitmap is identical to that object. PadWorkReceipt binds the child
  action, later observation, PAD compiler case, every PAD tensor, nonzero
  supervised tokens, equality against both NEW twins outside the permitted
  payload closure, and disconnection from D. W* is exactly the qualified
  writer recipe and is never guessed.
  A COMPLETE FitAttempt has non-null OptimizationReceipt and artifact hashes;
  the optimization receipt names the accepted WriterBinding/qualification and
  is stored in the root bundle. A COMPLETE ExecutionAttempt has non-null
  artifact hash. Failed attempts retain whatever hashes and all intervals were
  actually produced, never synthesized completion objects.
  A root opened for S1 has exactly three FitAttemptReceipts regardless of their
  status. If and only if its authorized S2 open occurs it has exactly six.
  There is no retry/replacement attempt; a failed launch remains the sole
  receipt for that carrier and drives the applicable gate to zero or abort.
- RootCellRoster is complete. Every executed cell has exactly one typed
  StructuralTraceReceipt; each structurally valid completed cell has exactly
  one EndpointReceipt, while the first structurally failed cell has none and
  aborts the root. No endpoint opens before a valid structure receipt. Every
  completed compiler cell appears exactly once in
  CompilerAggregateReceipt. RootResultBundle contains every typed object named
  by its episode/fit hashes exactly once, including provenance, training
  tensors, and optimization receipts; QualificationResultBundle does the same
  for qualification hashes. EpisodeAuditEnvelope contains episode-local hashes
  only; RootAuditReceipt embeds root-wide typed receipts without duplication.
  EpisodeAuditEnvelope.endpoint_receipt_sha256 is null iff that envelope is
  the root-aborting structurally failed cell.
  Every CellSpec.allowed_observed_failure_codes is exactly `[NONE]` followed by
  the eight VALID FailureCodes in table-priority order; its canonical endpoint
  and code equal the canonical expected trace, not an assertion that a model
  must follow that trace.
  Scheduled ScienceRootResult/TextRootResult bundles have non-null RootAuditReceipt
  with the identical RootRef and exhaustive, duplicate-free typed arrays;
  UnscheduledRootResult alone may omit it.
- A StructuralTraceReceipt's FailureDecisionReceipt evaluates only GLOBAL/ROOT
  triggers and must select NONE before an EndpointOpenReceipt can exist. After
  open, EndpointReceipt contains a second FailureDecisionReceipt over NONE or
  the one applicable VALID endpoint trigger; its selected code equals
  EndpointReceipt.failure_code. No valid-endpoint trigger is evaluated from
  sealed bytes before open. The StructuralTraceReceipt tick precedes the
  SealedEndpoint tick, which precedes EndpointOpenReceipt; the seal cites that
  structural receipt and opened bytes hash to both the seal's endpoint digest
  and the open receipt's digest. No endpoint result or seal hash is a
  StructuralTraceReceipt input.
- RootGateRosters have exact `[S,M,U,W,F,R,Q_S1,TEXT]` order and literal typed
  role lists. Each runtime GateInputReceipt matches one static requirement
  handle/hash, resolves the named closed root type and object handle to its
  later object SHA, and records its required observed bit. Runtime inputs cover
  their roster in exact order with no omission/extra; a missing/false input
  cannot be replaced. Science roots
  contain numeric components exactly `[S,M,U,W]`, one R bit object, one F
  diagnostic, and six gate receipts `[S,M,U,W,F,R]`. R has no numeric contrast.
- Program transitions and schedule events reproduce Section 8 exactly. Every
  ScheduleEvent address is computed over the event without an address field
  and links to its predecessor; only the first has null predecessor, event
  handles are unique, and both logical_tick and monotonic_ns strictly increase.
  Every downstream OpenEvent cites
  an earlier authorizing event. TEXT_FINAL_GATE and DEV_MECHANICS_GATE are
  mandatory. Every cohort has one produced/skipped/invalid disposition;
  unscheduled roots contain no fabricated attempts/Q/components. QS1Receipt
  binds the predecessor schedule head; the later DEV/CONF root-S2 ScheduleEvent
  cites QS1Receipt as input and is the only object that authorizes an S2 open.
- FailureDecisionTable contains all 32 FailureTriggers exactly once, priorities
  are unique/consecutive, and mappings/scopes equal Section 9. Every decision
  includes all evaluated typed triggers and chooses the lowest priority.
  Structural failure precedes endpoint open. Any global selection creates a
  CohortFailureReceipt, stops downstream opens, retains already incurred work,
  and yields no scientific test. A root interrupted after any open is an
  AbortedRootResult containing every completed attempt/endpoint/compiler case;
  only a never-opened root is UnscheduledRootResult.
  FailureDecisionReceipt.inputs occur in the table's 32-row priority order,
  restricted by phase: STRUCTURAL has exactly the 24 GLOBAL/ROOT rows and
  ENDPOINT exactly the eight VALID rows. triggered is the ordered triggered
  subsequence, and selected_code/scope are NONE/NONE exactly when that
  subsequence is empty. An ENDPOINT decision is illegal until a STRUCTURAL
  decision over all 24 rows selected NONE.
- CONF seeds/noise and component functions satisfy the identical-distribution
  premise in Section 8.2. Indicators include all failure/adverse-fill behavior.
  ComponentStatistic has 0<=K<=16, exact binomial numerator/65536, correct
  fixed-sequence post-stop bit, and `cp_lower=0000000000000000` at K=0.
- CostLedger has globally unique interval handles and every attempt reference
  resolves. Device intervals are unioned by lease/device; contributors appear
  once, segments do not overlap, and buckets partition them. CPU/noncompute
  intervals are separate. Unknown boundary selects InvalidCostSummary with
  every total null and causes GLOBAL_UNKNOWN/no test; valid cost includes all
  failed/aborted/timed-out/partial work.
- MaterializedCohortBundleManifest and CohortResultBundleManifest contain
  exactly roots 0..7 for TEXT/DEV and roots 0..15 for CONF, in root-index
  order; their vector range is not permission to choose an intermediate
  cardinality. ProgramResultIndex cohort dispositions occur exactly in
  `[TEXT,DEV,CONF]` order, and a ProducedCohortResult is legal only when its
  corresponding sealed cohort manifest exists.

## 12. Root counts, promotion, and audit dispositions

### 12.1 Staged root and fit counts

```text
TEXT: 4 roots initially; optionally 4 more; 0 fits
DEV initial: D1/D2 S1 = 6 fits
DEV initial complete through S2 = 12 fits
DEV maximum: 8 roots x <=6 = 48 fits
CONF maximum: 16 roots x <=6 = 96 fits
DEV+CONF maximum: 144 fits
```

Qualification and TEXT/model-reader device work are excluded from fit counts
but included in the central cost ledger. No GPU-hour estimate is asserted
before measured device intervals exist.

### 12.2 Promotion rule

V7 authorizes no execution. Promotion requires actual static/package/root/
result JSON Schemas generated from Section 11, a deterministic CPU
materializer, and an independent checker. Before any model work:

1. two independent materializations from the same final package must yield
   byte-identical 32 expected/rematerialized root content manifests; and
2. the checker must reconstruct all roots, tables, controls, schedules,
   failure decisions, typed gate rosters, bundle/Merkle hashes, and test-vector
   cost unions without importing generator/materializer code or generated
   constants.

### 12.3 Audit-disposition matrix

| v6 audit blocker | v7 exact disposition |
|---|---|
| no action/reset custody | Sections 3.2--3.3; ModelTurnReceipt, ProcessBirthReceipt, ResetReceipt, ProcessTeardownReceipt; all decision events cite turns |
| 8-lane/28-pair mismatch and untyped support | Sections 2.3/4.2; PairCandidate, PairSelectionEvent, SupportSlot/Binding and bijection rule |
| SOURCE sees provenance/condition | Sections 3.1/4.2; identical PresentedSourcePair projection; provenance checker-only |
| NEW lacks outcome law/codebook/selector | Sections 2.4/4.2; ExperimentLawRevealEvent, OutcomeCodebook, NewRowTemplate selector, declaration/dispatch custody |
| cuts impossible under reader input | Section 5.1; MountInstance and 32-slot pre-scoring CandidateProjection with matched fillers |
| payload swaps change public label | Section 4.3 and mount semantic rule; same row handle, payload-only descendants |
| writer/reader qualification circular/weak | Section 6.1; spec->binding->later receipt direction and mandatory eight-case suites |
| pre-blueprint overclaim | Section 0; narrowed preassigned-pair recovery claim |
| no materialized object/checker replay | Sections 1.1/1.4; Expected/Materialized Root+Cohort manifests and checker binding |
| flat root lookup | Sections 1.4/5.1; RootRef in every concrete root plus root/mount/request lookup |
| incomplete strata/draw/handle codec | Sections 2.1--2.2; EventStrata, DrawPlan, HandleCodec, RootMaterializationReceipt |
| missing autonomous/terminal transitions | Sections 5.3--5.4; transition union and EpisodeTerminal |
| carrier/control/PAD/cue/order inconsistencies | Sections 5.5/11.1; unified CarrierId/ControlId, FULL_OLD_PLUS_PAD, GOAL_CUE_SWAP, typed order vectors |
| incomplete program schedule/order custody | Section 8; ProgramMachine, hash-chained ScheduleEvent/OpenEvent, final TEXT/DEV gates, unscheduled variants |
| nondeterministic failure/code precedence | Sections 7.1/9; 32-trigger priority table, structural endpoint seal/open, cohort failure |
| missing endpoint/compiler/gate/R value | Section 7 and schemas 11.7/11.9; mandatory EndpointReceipt, CompilerAggregateReceipt, typed rosters, RComponentResult |
| receipt hashes lack typed custody | Sections 7.2/11.9; RootResultBundle and QualificationResultBundle embed exhaustive typed turn/reset/trace/scorer/RPC/provenance/tensor/optimization objects; RootAudit embeds root-wide checks |
| PAD/control work not exactly representable | Sections 6.2/11.5--11.6; AllowedTensorDifference, TrainingTensorReceipt, PadWorkReceipt, PairwiseWorkReceipt and exact FULL_OLD_PLUS_PAD spelling |
| common realized device/RNG not receipted | Sections 6.2/11.6/11.10; DeviceEligibilityRoster, PairwiseWorkReceipt, DeviceInterval, InferenceMatchReceipt |
| source probe/TEXT success left implicit | Sections 5.4/7.4; exact four-probe desired-outcome/order/truth table and noncompensatory T_r rule with zero-fit/nonzero-inference cost distinction |
| non-IID exact binomial premise | Section 8.2; iid seeds+noise+identical root/component functions or global no-test |
| duplicate/unrepresentable cost | Section 10 and 11.10; central interval handles, union contributors/buckets, InvalidCostSummary null totals |
| SchemaBinding/path/numeric/RPC exact defects | Sections 1.2/5.3/11; path_pattern, package-relative namespace, F64HEX, exact reader/RPC fields |

### 12.4 Source lineage

- `research_notes/analysis/2026-09-12_m_core_exact_two_cycle_design_v6.md`;
- `research_notes/analysis/2026-09-12_m_core_v6_fresh_causal_audit.md`;
- `research_notes/analysis/2026-09-12_m_core_v6_fresh_execution_audit.md`.
