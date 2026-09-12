# Fresh execution and materialization audit of M-core v6

Date: 2026-09-12 UTC

Scope: fresh, independent, static review of the complete
`2026-09-12_m_core_exact_two_cycle_design_v6.md` under the repository operating
contract. I treated every package, materialized bundle, checker result, receipt,
TEXT result, qualification, and model result as a future requirement rather
than evidence. I did not inspect or modify builder code or coordination, did
not run a model or GPU, and made no scientific claim from unmaterialized
artifacts.

## Verdict: REWORK before materialization

V6 makes substantial and useful zero-fit repairs to v5. The six trained
carriers per complete root remain sufficient; the non-self-referential package
Merkle construction is coherent; rejection sampling advances counters
unambiguously; B/C/D budgets and successful traces are coherent; the source
tie and count-only live swap are scientifically well motivated; the local
TEXT extension rule, DEV S1/S2 rules, CONF per-root S2 rule, fixed-sequence
order, 12/16 cutoff, and launched-interval union principle are directionally
right.

It is nevertheless not an executable closed contract. The largest blocker is
that the object supposedly produced by `materialize` has no schema, file
manifest, namespace, or digest algorithm, while the immutable cohort manifests
already contain opaque hashes of those nonexistent objects. Flat package
tables also have no root key even though handles may legally repeat across
roots. Several schema fields cannot express the prose they are said to bind;
the program-level stopping edges are absent; endpoint and cohort-failure
receipts are incomplete; failure-code selection is not deterministic; and the
cost schema cannot represent either an invalid total or the promised
non-overlapping breakdown. Two independent implementers can therefore produce
different bundles and stopping/failure/cost records while satisfying the
present schemas.

All required repairs below are zero-fit specification and CPU-fixture work.
None requires a seventh trained carrier, a model call, or a GPU run.

## Audit disposition

| Area | Disposition | Finding |
|---|---|---|
| Six-carrier allocation | **PASS** | S1 has three fits and S2 has three fits; the per-root maximum remains six. |
| Package JCS/Merkle construction | **PASS in algorithm; REWORK in namespace/schema binding** | The leaf/node/self-exclusion rules are reproducible, but package path conventions conflict and `SchemaBinding` has no path field. |
| Materializer output and checker binding | **REWORK** | There is no closed materialized-root/cohort bundle type or directory-hash law, and `CheckerReceipt` does not bind the checked bundle. |
| RNG and root isolation | **REWORK** | Rejection advancement and the literal scalar domains are sound, but `EventStratum`, generated-handle assignment, output draw ledgers, and root scoping of concrete tables are missing. |
| Collision/capability law | **REWORK** | Root-local reuse is a defensible rule, but the flat concrete tables cannot implement lookup by `(root_seed_commitment, public_handle)`. |
| B/C/D machine and budgets | **PASS in prose; REWORK in event schema** | Successful paths and budgets close, but an actor-observable terminal frame has no type/event and autonomous C outcome/compiler transitions are not represented by `TransitionRow`. |
| Named controls | **REWORK** | All 21 IDs occur in both control enums, but the cue-swap mutation, control ordering type, and PAD carrier identity are inconsistent. |
| Failure scopes | **PASS in direction; REWORK in deterministic classification** | The 33-code scope cardinality is correct, but triggers, precedence, and pre-endpoint evidence are not closed. |
| TEXT/DEV/CONF scheduling | **REWORK** | The within-cohort predicates are largely exact; TEXT-to-DEV and DEV-to-CONF gates and auditable emission ordering are absent. |
| Gates and statistics | **REWORK** | Adverse filling, the five-test sequence, cutoff, and K=0 CP case are sound; raw endpoint binding, the R result representation, and the common indicator law are incomplete. |
| Result receipts | **REWORK** | The four named result roots exist, but required endpoint/compiler/cohort-failure evidence and non-replayable checker binding do not. |
| Cost accounting | **PASS in union principle; REWORK in schema** | Failed/partial launched work is included in prose, but mandatory numeric totals contradict “no cost total,” mixed intervals duplicate, and required breakdown dimensions are absent. |

## Root, type, and control cross-check

The Section-1 table contains 28 manifest-listed JSON paths; every displayed
root name has a Section-12 definition, and `PackageManifest` is also defined.
All four Section-10 result-path root names are defined. The schema appendix
defines 186 named algebra entries including primitives. This is a major
improvement over v5, but name existence is not semantic closure.

The exact cross-reference defects are:

- `SchemaCatalog.bindings` contains `schema_id`, `root_type`, and schema bytes,
  but no `path`. It therefore cannot perform the promised one-to-one mapping
  from a literal manifest path to a root schema without an unstated array-order
  convention.
- Section 1 lists package-relative paths such as `protocol.json`; the final
  semantic rule requires member paths under `package/`, while result paths are
  explicitly rooted under `results/`. The bytes hashed into a package leaf are
  therefore not uniquely specified.
- The 21 control IDs match between `ControlSpec` and `ControlReceipt`, and the
  deleted no-goal and `RAW_WRONG_ROOT` controls are absent. However,
  `OrderTables.*_control_ids` and `ScheduleReceipt.*_control_order` are vectors
  of lowercase 26-character `HANDLE26`, not the literal `ControlSpec.control_id`
  enum values the generator says it shuffles. No handle-to-control-ID map
  exists.
- `FULL_OLD_PLUS_PAD` is the trained condition and mounted-control carrier,
  while `AvailabilityEntry` and the executable prose use `OLD_PLUS_PAD`. No
  normative alias/equality connects them. `CanonicalReturnEntry.carrier` and
  several carrier receipts weaken the problem further by using unconstrained
  `STRING`.
- `FULL_GOAL_CUE_SWAP_B` cannot be represented by `ControlMutation.kind`, whose
  enum has no goal/input-field mutation. Calling its mutation `NONE` would
  contradict the registered intervention; calling it another enum member would
  be false.
- `ChildPairSelectionTask` carries eight lane handles and 28 unordered-pair
  handles, while `ChildPairSelectionEvent.visible_pair_roster` carries eight
  handles and the semantic prose alternates between an “eight-pair” and an
  “8-lane/28-pair” roster. The event has no selected selection-action handle.
  The checker cannot uniquely decide whether the event field is the lane
  roster, the 28-action roster, or another pair-handle class.
- The runtime exposes an `EpisodeTerminal` frame according to Section 6.4, and
  registered expected traces contain a `TERMINAL` event kind, but no
  `EpisodeTerminal` type is defined and `PublicTraceEvent` cannot contain one.
- Section 6.4 says `reader_binding.json` binds the monotonic clock source,
  scorer count, worker image, padding construction, and exact frame. The
  `ReaderBinding`/`RpcMachine` schemas omit the clock-source binding, scorer
  count, worker image, and an exact frame/padding algorithm binding.
- `DecodeConfig.temperature_hex` and `top_p_hex` are arbitrary `STRING`, not
  the promised canonical 16-hex-digit binary64 representation.

The failure enum and table cardinality do agree: one `NONE`, 11 global, 13
root, and eight valid-endpoint codes give 33 entries. The five confirmatory
components and separate F gate are also enumerated consistently at a high
level. The remaining failures are behavioral/receipt defects described below.

## Materialization blockers and minimum zero-fit repairs

### B1. There is no defined materialized object

The required CLI writes a `<materialized-directory>`, and each
`RootManifestEntry` contains `materialized_root_sha256`. No `MaterializedRoot`,
`MaterializedRootManifest`, or `MaterializedCohortManifest` type exists; no
output path roster says which generated files occur; and no byte framing,
member table, Merkle rule, or canonical directory-hash rule defines the
preimage of `materialized_root_sha256`. The checker consequently cannot know
what an extra/missing output file is or reproduce the advertised root digest.
`CheckerReceipt` binds only the immutable package and tool/runtime hashes, not
the materialized bundle digest, cohort, root set, or output Merkle root, so it
can also be replayed against another bundle.

There is a temporal ambiguity as well. The entropy transcript is said to be
package-bound before any root is materialized, but the same immutable package
contains cohort manifests with hashes of materialized roots. Computing those
hashes requires an as-yet undefined materialization preimage. “Compute the
future bytes without writing them” is not a normative phase boundary.

Minimum repair: define a closed `MaterializedRootBundleManifest` and
`MaterializedCohortBundleManifest`, exact output paths/root types, the same
non-self Merkle/address law, and one explicit package-build sequence:
entropy seal -> deterministic expected-root generation -> immutable package
seal -> independent re-materialization. Bind cohort/root/output manifest
digests in `CheckerReceipt` and reject replay or a wrong cohort/root. If the
entropy transcript must be sealed before expected generation, give that first
seal its own address and bind it into the final package.

### B2. Root-local reuse is incompatible with the flat concrete tables

Alias reuse across roots is explicitly legal, and the private lookup key is
said to be `(root_seed_commitment, public_handle)`. Yet `TransitionRow`,
`ActionRosterEntry`, `CandidateRosterEntry`, `AvailabilityEntry`,
`CanonicalReturnEntry`, and `ControlSpec` have no root commitment, and their
root files are singleton flat package members. `CandidateRosterEntry` is keyed
only by request fingerprint; `AvailabilityEntry` only by carrier and request
fingerprint. Two roots can reuse public handles with different b/h/role
assignments, producing the same public request key with a different canonical
row. The promised root-capability lookup cannot be reconstructed from these
objects.

`ControlRegistry` makes the same mistake: it contains exactly 21 concrete
`ControlSpec`s, each already embedding complete root-specific actor inputs,
not 21 templates per root or 21 root-nested instances. The design alternates
between treating these package members as global templates and concrete
materialized rows.

Minimum repair: put all concrete tables under the materialized-root manifest,
or add a required `root_seed_commitment`/root namespace to every concrete key
and enforce uniqueness on the full root-scoped tuple. Keep only genuinely
root-independent templates in the immutable singleton package. Make the
checker enumerate every root namespace and prove that no unscoped lookup API
exists.

### B3. The generator roster is not complete enough to reproduce bytes

The scalar draw law and rejection counter advancement are exact. The complete
domain roster is not: it depends on an `EventStratum` array and
`stratum_id` order that have no manifest path or Section-12 type. There is no
typed roster mapping event strata to permutation populations, and no complete
rule assigning the many event, row, template, fixture, and control handles
from alias permutations or deterministic hashes. `k=first128(H(...))` does
not specify how those 128 bits become the required 26-character handle.
`RootGeneratorSpec.draw_order_sha256` is a digest with no typed, listed
preimage. Result receipts record schedule and inference draws but not the
complete materializer-domain counters/rejections/assignments.

Minimum repair: add a closed `EventStrata` package root, a typed draw-plan
object whose digest is `draw_order_sha256`, exact population/order/assignment
fields for every alias and stratum, an explicit 128-bit-to-handle codec, and a
`RootMaterializationReceipt` containing every final domain counter, rejection
count, permutation digest, role assignment, collision check, and generated
member digest. Define collision uniqueness over all handle classes in one root
and over all candidates in each pool, while preserving allowed cross-root
reuse.

### B4. Machine and control encodings leave real choices to implementers

The prose gives coherent successful B, C, and D traces, but `TransitionRow`
can represent only action-labelled transitions. The public outcome and
compiler transitions in C are autonomous and have no transition type. The
missing terminal-frame type prevents the complete actor-observable transcript
and exact expected `TERMINAL` step from validating against Section 12. The
pair-selection action/roster mismatch, PAD carrier-name split, cue-swap
mutation omission, and control-order handle/ID mismatch listed above are also
execution-affecting, not cosmetic.

Minimum repair: add typed environment/outcome/compiler/terminal transitions or
one closed transition union, add `EpisodeTerminal` to `PublicTraceEvent`, and
make the pair-selection event bind both the complete eight-lane/28-action
roster and the selected action plus its two lane members. Introduce one closed
`CarrierId` and one closed `ControlId` used everywhere; choose one PAD carrier
name; add `GOAL_CUE_SWAP` to the mutation union; and add the missing reader/RPC
binding fields. Regenerate all 21 zero-fit control fixtures and reject any
control that cannot round-trip its exact spec and trace.

### B5. The complete TEXT/DEV/CONF program state machine is not registered

The local rules are mostly deterministic:

- TEXT stops at 0/4 or 1/4, proceeds at 4/4, and extends at 2/4 or 3/4 with a
  final requirement of at least 6/8;
- DEV runs D1/D2 S1, runs their S2 only if both Q_S1 values pass, and opens
  D3--D8 only if both first-root I_R values pass; and
- CONF runs every S1 and each root's S2 iff that root's Q_S1 passes.

But `ScheduleTables.rules` contains only `DEV_S1_KILL`, `DEV_FULL_KILL`,
`DEV_ROOT_S2`, and `CONF_ROOT_S2`. It has no TEXT-pass -> DEV rule and no DEV
`>=6/8 I_R` mechanics-freeze -> CONF rule. `StoppingReceipt.stage` likewise
has no final TEXT gate or DEV-mechanics gate. `ProgramResultIndex` nevertheless
requires all three cohort manifests. A CONF root skipped because DEV failed
has no exact skipped reason (`CONF_COMPLETE` is not that reason), and the
mandatory science-root Q_S1/gate fields have no registered unscheduled-state
semantics.

Moreover, `QS1Receipt.emitted_before_s2_open` and
`StoppingReceipt.emitted_before_downstream_open` are constant assertions, not
evidence of time/order: neither object has an event handle, logical/monotonic
tick, append-only log predecessor, or downstream-open commitment. They can be
created after downstream results are known and still validate.

Minimum repair: publish one finite program transition table covering
package/qualification, initial TEXT, TEXT extension/final gate, DEV D1/D2,
both DEV kills, later DEV roots, DEV >=6/8 freeze, CONF roots, and fixed
sequence. Add `TEXT_FINAL_GATE` and `DEV_MECHANICS_GATE` stopping types,
upstream skip reasons, and a closed unscheduled science-root representation.
Bind every decision to typed named inputs and to a hash-chained append-only
schedule event that precedes a downstream allocation/open event; do not use a
self-asserted constant as the proof.

### B6. Failure scope is closed, but failure selection is not

`FailureScopeTable` can map all 33 codes to scopes, but it does not say which
code wins when multiple checks fail or which exact predicate emits each code.
Several normative passages name only a scope where one exact code is required:
tokenizer/shape/collision failures and RPC overflow are called
`GLOBAL_INVALID`; an overrun is called `ROOT_INVALID`. Tensor/work mismatch is
called `GLOBAL_INVALID` in Section 7 even though `ROOT_WORK_MISMATCH` exists
and `GLOBAL_COMMON_NUISANCE` is also available. Interface and canary failures
similarly have two plausible root codes. A materializer and checker can choose
different legal codes.

The claimed structural-before-endpoint law is not receiptable. An endpoint is
inside `PublicExecutionTrace`, `EndpointScoreInput` receives that complete
trace, and `FailureReceipt.emitted_before_endpoint_open` is only a bit. There
is no sealed endpoint commitment/open event or priority transcript proving
that structural classification occurred first. `CohortResultBundleManifest`
also has no cohort-level `FailureReceipt`, although a shared-state or unknown
global event terminates the whole cohort rather than one root.

Minimum repair: add an ordered `FailureDecisionTable` mapping every finite
trigger to exactly one code, including tie/priority rules. Separate a committed
structural trace from a sealed endpoint object and receipt its open order. Add
one cohort/program failure receipt for global termination and define how root
bundles are finalized after it. Resolve work/tensor, interface/canary,
collision, overflow, and overrun to literal codes rather than scopes.

### B7. Gates and result receipts do not expose all recomputation inputs

`EndpointScoreOutput` exists but is not a mandatory, cell-identified root
receipt and has no episode/control identity or input hashes. Positive FULL,
SOURCE, DREAM, and FULL_NEW episode outcomes therefore need not be stored in a
typed object from which S/M/U/W/F can be recomputed. A `ResultMember` could
optionally contain such an object, but no cardinality or cell roster requires
it. There is also no aggregate compiler-correctness receipt despite the
gate-to-receipt table promising a correspondingly named compiler receipt.

`ComponentGateReceipt` and `QS1Receipt` use anonymous vectors of SHA-256 values
rather than typed `(role, root type, digest)` inputs. Their pass bits and
“complete literal list” cannot be established from the schema alone.
`AuditEnvelope` is episode-labelled but embeds root-wide schedule, ACL, BFS,
clock, optimization, and interval objects, forcing either duplication across
episodes or selective empty arrays; both conflict with the final no-duplicate
result law.

There is a result-shape contradiction for R. `RootComponentResult` requires an
optional `contrast_hex` for every S/M/U/W/R component, and the semantic rule
says it is non-null whenever the gate passes. The design defines numeric raw
contrasts only for S/M/U/W/F; `R_r` is a Boolean conjunction. No value for the
R `contrast_hex` is defined.

Minimum repair: require one typed `EndpointReceipt` for every presealed
positive/control cell, binding cell ID, trace/input/environment hashes,
structural validity, endpoint bit, and exact failure code. Add a typed compiler
aggregate receipt. Replace anonymous gate hash vectors with typed role
references and exact per-gate rosters. Split root-wide audit receipts from
episode envelopes and reference them by digest. Represent R with a `r_value`
BIT (or explicitly define its binary64 encoding) rather than an undefined raw
contrast. Add a cohort failure result as in B6.

The exact-binomial engineering assumption also needs one word-level repair.
The text requires root-local noise variables to be mutually independent, but
not identically distributed or governed by a common root function. That does
not literally yield an exact Binomial law for the 16 indicators. Either require
IID root-local noise plus the same measurable indicator function for all CONF
roots, or state the componentwise null `p_r<=.5` and predeclare the valid
Poisson-binomial/binomial-dominance argument. The 12/16 tail
`2517/65536`, fixed sequence, and piecewise K=0 Clopper--Pearson expression are
otherwise correct.

### B8. The cost schema cannot implement the stated accounting law

The union-by-lease/device principle correctly avoids double counting and
includes failed, aborted, timed-out, and partial work. Its types are not
closed enough to carry that result:

- When ownership or release is unknown, prose requires no cost total, but
  `CostSummary` always requires numeric device/CPU/queue/reset/serialization
  totals and at least one bucket. Setting them to zero would violate the
  explicit no-silent-zero rule.
- Every `FitAttemptReceipt` and `ExecutionAttemptReceipt` embeds a complete
  `DeviceIntervalReceipt`. If one physical interval serves two attempts or
  categories, it must be repeated in both attempts, while the final semantic
  rule forbids duplicated intervals. Marking it `MIXED` does not create a
  unique central interval reference.
- `DeviceUnionSegment` has no status, deck class, image, driver, or runtime;
  `CostBucket` has no device, image, runtime, deck, or receipt membership.
  Thus the promised status-by-deck/device/image report and proof of union
  membership cannot be represented.
- Overlapping intervals of different status/category have no deterministic
  attribution rule. `MIXED` records neither the set of contributing categories
  nor their attempt handles. `DurationReceipt` also lacks the status needed by
  `CostBucket.status`.

Minimum repair: store a deduplicated central interval ledger and let attempts
reference interval handles. Give union segments their contributing attempt
set and a deterministic category/status attribution law; add the dimensions
needed for the promised breakdown and explicit member/non-overlap proofs. Add
an `InvalidCostSummary` variant with null totals (or make totals conditionally
nullable) for `GLOBAL_UNKNOWN`, and add status to non-compute duration
receipts. Preserve the rule that no unknown boundary produces a scientific
test or a numeric cost total.

## What can be retained unchanged

The narrow scientific architecture does not need another trained arm. Retain
the three S1 carriers, the two FULL_NEW branches plus grounded PAD S2 carrier,
truthful 3/1 versus 2/2 source rows, child-visible evidence selection, fresh
support requirement, FULL-mounted count and goal-cue interventions, separate
old/new cuts and payload swaps, clean-base reconstruction, adverse filling,
and the fixed five-component sequence. The repairs are about making those
choices serializable, independently recomputable, and auditably ordered.

Materialization should remain closed until the repaired package can pass two
CPU-only tests: (1) two independent materializer executions produce the same
typed root/cohort bundle bytes from the same sealed package, and (2) a checker
with no generator/materializer import or shared generated constants recomputes
every root table, schedule transition, failure decision, gate input, result
digest, and cost union while binding the exact checked bundle. Only after that
would TEXT or any qualification/fit gate have an object to evaluate.
