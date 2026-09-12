# Fresh execution-closure audit of M-core v7

Date: 2026-09-12 UTC

Scope: independent, adversarial, static review of the complete
`2026-09-12_m_core_exact_two_cycle_design_v7.md` under `AGENTS.md`. I treated
all packages, roots, qualifications, receipts, fits, and results as future
requirements, not evidence. I inspected the prior v6 execution audit only as a
cross-check. I did not inspect or change builder code, run a model, use a GPU,
or authorize execution.

## Verdict: REWORK before package construction or materialization

V7 closes most of v6's architectural omissions. The six-fit maximum, narrowed
claim, five-phase anti-cycle, root-scoped tables, 8-lane/28-pair geometry,
typed autonomous/terminal transitions, 21 control IDs, source/NEW visibility
law, fixed RPC size, component formulas, exact 12/16 binomial cutoff, failure
scope cardinalities, and central interval-union principle are coherent.

It is not yet an executable closed contract. Several ordinary required paths
cannot inhabit the normative schemas: a root stopped after S1 has no result
variant; malformed model output cannot have a parse receipt; reader
qualification cannot have a legal `ScorerReceipt`; and BLOCKED/overrun RPCs
cannot have a legal `RpcReceipt`. Other hashes name objects or ledgers whose
typed preimages and storage paths do not exist. A materializer and checker
would therefore have to invent object rosters, assignments, linkages, and
failure/storage rules.

## Disposition by audited area

| Area | Disposition | Reason |
|---|---|---|
| Schema/type/cardinality closure | **REWORK** | Important success-path types exist, but partial, invalid-parse, qualification, and RPC variants are unrepresentable. |
| Package/Merkle/noncircular build | **PASS in construction; REWORK in file closure** | The entropy -> expected -> package -> rematerialized direction and leaf/node law are acyclic; expected-manifest and result/qualification paths and the non-JSON roster are not closed. |
| Draw domains/materializer | **REWORK** | Scalar domains are mostly named, but strata contain metadata rather than population members, and handle assignments/draw-ledger preimages are absent. |
| Turn/reset/process/mount/RPC custody | **REWORK** | Actor success custody is strong; malformed turns, reader/writer operations, qualification mounts, BLOCKED, and overrun are not serializable. |
| State machine/schedule/stopping | **REWORK** | B/C/D successful traces close, but the program machine cannot exit repeated late-DEV/CONF root processing, and completed S1-only roots have no result. |
| Failure precedence | **REWORK** | The 32/33 trigger/code counts and scope ordering close; literal within-scope priorities and several exposed attempt failures do not. |
| Results/endpoints/gate references | **REWORK** | Endpoint/result types exist, but endpoint opening has no verifiable payload preimage and most gate-addressed receipts have no resolvable object identity/bit selector. |
| Matched work | **REWORK** | Tensor bitmap concepts are sound, but no typed deck or tensor-to-attempt mapping exists. |
| Cost ledger | **REWORK** | Deduplicated device union is sound in principle; incomplete boundaries and pre-root/qualification attempts cannot be represented exactly. |

## Blocking defects and smallest repairs

### B1. Generated populations and handle assignment are not materializable

`EventStratum` stores only a population kind, handle, cardinality, target, and
handle class. It does not enumerate the population members that
`event_strata.json` is said to enumerate. `DrawStep` likewise has no member or
field destination and no `assignment_ordinal`. Its operation union contains
only `SCALAR` and `FISHER_YATES_DESCENDING`, although mandatory step 12 is a
handle derivation. Consequently the broad targets `FOUNDATIONS`, `CELLS`,
`HANDLE_ASSIGNMENT`, and similar values do not determine which generated value
lands in which object field. The useful pair's A/B draw also has no exact rule
for ordering the two members of each `PairCandidate`, especially non-useful
pairs.

`DrawCounterReceipt.draw_ledger_sha256`, the permutation digest vector, and
`role_assignment_sha256` have no typed preimage or hashing law, despite the
claim that every draw, rejection, permutation, and assignment is receipted.

Smallest repair: add a package-bound typed population-member/object-role table
with stable member and per-class assignment ordinals; add either
`DERIVE_HANDLE` to `DrawStep` or a separate `HandleAssignmentPlan`; give every
draw/assignment its exact destination; define pair-member/A-B ordering; and
replace the opaque ledger/digest vectors with typed, step-keyed draw,
rejection, permutation, and handle-assignment records plus their exact JCS hash
law. Constrain every scalar population to positive cardinality and use the
literal `u-D` domain spelling everywhere.

### B2. Manifest namespaces and output member rosters remain open

The 32 `ExpectedRootContentManifest` objects are emitted and addressed but
have no storage namespace or literal paths and are not package members.
Likewise, no exact filename is given for a root-bundle or cohort-bundle
manifest. Saying that the CLI emits the files named by the cohort manifest
does not say where the newly created manifest itself lives. The package's
non-JSON source/lock/prompt/fixture members also lack an exhaustive literal
path roster, and `materializer_source_tree_sha256` lacks a tree-hash preimage
law. Qualification, root-result, cohort-result, and program `members` vectors
have no deterministic member-path/type roster; typed receipts are embedded in
the manifest while unspecified external members also contribute to its
Merkle root. The qualification manifest is omitted from the list of manifests
to which the common Merkle law applies.

Smallest repair: publish literal expected/root/cohort/result/qualification/
program manifest filenames and relative-path rules; either include expected
manifests as final-package members or define a package-bound content-addressed
store and lookup law; exhaustively list non-JSON package members; define the
source-tree hash; and define a deterministic one-file-per-object result layout
(or remove external result members and their Merkle tables). Explicitly apply
the common law to `QualificationResultBundleManifest`.

### B3. Qualification and process custody cannot satisfy their own schemas

Reader qualification is required to contain scorer/RPC/mount evidence, but
`QualificationCaseReceipt` has no scorer, RPC, or mount hashes.
`ScorerReceipt.root` is mandatory even though qualification mounts are
normatively root-null, and `ScorerReceipt` has neither a receipt/operation
handle nor a process handle. `OptimizationReceipt` also lacks a process
handle. Thus `ProcessBirthReceipt.first_operation_handle` and reader/writer
teardown cannot resolve to the asserted first/last typed operations.

Writer qualification is said to have model-turn, optimization/tensor, parser,
and cost custody, but `ModelTurnReceipt.role` excludes WRITER,
`QualificationResultBundleManifest` contains neither optimization nor
execution-attempt receipts, and every `TrainingTensorReceipt` requires a
root-local `AllowedTensorDifference` that qualification cannot contain.
Qualification-specific `MountInstance`s are also not stored in a typed package
or result object.

Smallest repair: give scorer/optimization operations stable receipt and
process handles; make scorer scope an exact XOR of root and qualification case;
add scorer/RPC/mount/process hashes to each qualification case; add a typed
writer-turn or writer-operation receipt; store qualification mount instances,
allowed differences, optimization receipts, and execution attempts in the
qualification bundle; and state the exact first/last-operation linkage.

### B4. Required invalid turn and RPC branches are unrepresentable

`DecisionParseReceipt` hard-codes `EXACTLY_ONE`, zero repairs, zero extras, and
a mandatory parsed decision. It therefore cannot receipt the malformed,
missing, multiple, extra, or uncustodied output that must trigger
`ROOT_MALFORMED_ACTION`. `MemoryRowParseReceipt` has the analogous inability to
retain extra/malformed writer output.

`RpcReceipt` always requires a scorer hash, return-event handle, payload,
frame, and release tick. BLOCKED explicitly has no scorer call, while physical
overrun explicitly has no actor return/continuation. Neither required branch
can be encoded without fabricating an object.

Smallest repair: replace both parse receipts with valid/invalid closed unions
that always preserve parser input/output evidence but require a parsed object
only on success. Replace `RpcReceipt` with `ReturnedRpcReceipt |
BlockedRpcReceipt | OverrunRpcReceipt`: BLOCKED has no scorer; overrun has no
public return event or delivered frame; only returned RPCs bind the 16,384-byte
actor frame.

### B5. The program and root-result state machines have missing states

A root that ran its three S1 fits but has `Q_S1=0` is neither unscheduled nor a
structural abort. `ScienceRootResult` nevertheless requires W/F/R component
objects and six gate receipts whose S2 inputs do not exist;
`UnscheduledRootResult` requires zero attempts; and `AbortedRootResult` claims
a structural failure. This occurs necessarily when either D1/D2 fails the
joint S1 gate and whenever a later DEV or CONF root skips S2.

TEXT also requires eight root-result addresses even when 4/4 makes extension
unnecessary, but there is no reason for an unrun T5--T8 root other than
`TEXT_STOP`.

The single parameter-free `DEV_ROOT_S2_GATE` rule can loop in
`DEV_LATE_ROOTS` or advance to `DEV_MECHANICS_GATE`, but cannot do both based on
root ordinal. The same defect prevents `CONF_ROOT_S2_GATE` from processing 16
roots and then advancing to `TEST_S`. No late-DEV-complete or CONF-complete
transition exists among the exact 14 rules.

Smallest repair: add a `PartialScienceRootResult` (or explicit NOT_RUN variants)
that preserves S1 attempts/Q/S-M-U evidence and carries typed skipped W/F/R
results; add `TEXT_EXTENSION_NOT_NEEDED`; and add explicit
`DEV_LATE_COMPLETE` and `CONF_COMPLETE` transitions, or put a closed root
counter/last-root predicate into the applicable rules. Give every branch an
exact literal state-after, decision, and open kind.

### B6. Endpoint and gate references are not independently checkable

`SealedEndpoint` has opaque `sealed_bytes` and a nonce commitment, but no
sealing/commitment algorithm or typed endpoint payload. `EndpointOpenReceipt`
contains only the opened payload hash, not the opened bytes or nonce. The
checker cannot verify opening, parse the bit/code from those bytes, or prove
that `EndpointReceipt` is the opened value.

`GateInputSpec.object_handle` cannot resolve many gate-addressed objects:
`CheckerReceipt`, both qualification receipts, interface/nonharm/extraction/
work receipts, and component-gate receipts generally have no object handle.
The spec also lacks a bit-field selector, so `(root type, object handle,
required bit)` does not determine whether to read `accepted`, `passed`,
`endpoint`, `gate_bit`, or another bit. The promised literal gate roster is
therefore not enough to recompute a gate.

Smallest repair: define a closed `EndpointPayload`, exact commitment/sealing
and open law, and store opened payload bytes plus opening material. Give every
gate-addressable object a stable receipt handle, or replace `object_handle`
with a closed typed locator; add an exact observed-bit JSON pointer/field enum
to each gate requirement. Predeclare the complete cell/control/gate roster,
including exact case cardinalities, rather than accepting `1..32` cases with a
semantic assertion of completeness.

### B7. Matched writing lacks a typed deck and attempt mapping

`deck_sha256` in fit/optimization receipts has no closed `TrainingDeck`
preimage stored in a result bundle. `TrainingTensorReceipt` has no attempt,
carrier, or stage identity, and `OptimizationReceipt` does not list its tensor
receipts. `PairwiseWorkReceipt` contains one flat tensor-hash vector for three
attempts, so it cannot prove which example/tensor/visit belongs to which fit or
that the six exact decks were rendered once under the required pairing.

Smallest repair: define and store typed `TrainingDeck` and `TrainingExample`
objects with row/citation/view/visit/order fields; add attempt/stage/carrier to
each tensor receipt; make every optimization receipt list its exact tensors;
and make `PairwiseWorkReceipt` carry an exact per-attempt/per-example pairing
matrix before applying `AllowedTensorDifference`.

### B8. Failure and cost closure is incomplete off the happy path

The design fixes global-before-root-before-valid scope precedence, but does not
publish the literal 32-row priority order within scopes. The checker therefore
cannot verify that the future `failure_decisions.json` chose the intended winner.
`ExecutionAttemptReceipt` exposes CRASH/TIMEOUT for actor, reader,
qualification, materializer, checker, and compiler attempts, while the trigger
table gives crash/timeout predicates only for fits and RPC. Failed or incomplete
qualification also cannot produce its mandatory eight complete case receipts.

`InvalidCostSummary` allows an unknown ownership/release boundary, but every
ledger interval requires non-null owner and release fields. Recording the
offending interval thus requires either omission or invented timestamps.
Furthermore, qualification and pre-root materializer/checker execution
attempts have no guaranteed result container, so their interval
`attempt_handle`s cannot always resolve. Device attribution defines MIXED for
category/status, but not for deck, and CPU/duration bucket deck/null-field rules
are not literal.

Smallest repair: enumerate all 32 failure rows in exact priority order; map
every non-COMPLETE attempt status and incomplete qualification to one exact
trigger/code; add typed incomplete qualification results; add a program-level
attempt registry that owns qualification/materializer/checker/compiler
attempts; make interval records a valid complete/incomplete union with nullable
unknown boundaries only in the incomplete variant; and state exact deck/MIXED
and CPU/noncompute bucket attribution rules.

## Promotion consequence

These are zero-fit schema/protocol repairs. They require no seventh carrier,
model call, GPU work, or change to the scientific contrasts. Package
construction, qualification, TEXT, and fits should remain closed until the
repaired schemas can round-trip fixtures for at least: malformed turn, BLOCKED,
RPC overrun, failed qualification, S1-only root, unextended TEXT roots, root
failure with continuation to the next root, global stop, endpoint open, and
unknown interval boundary. Only then can two independent materializers and a
non-importing checker demonstrate byte-exact closure without inventing rules.
