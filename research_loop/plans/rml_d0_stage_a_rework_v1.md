# RML-D0 Stage-A REWORK v1: minimal valid repair design

**Status:** design only. This document does not authorize implementation,
Stage B, the 64-pair CPU gate, a model/network/GPU call, or any scientific
claim. It repairs the Stage-A evidence design for `RML-D0-FT-B-V1`; it does not
change Candidate B's world geometry, thresholds, target counts, or claim
firewall.

**Predecessor:** Candidate B SHA-256
`bd2a3b2bc11dd0b7f9591266ca9b9094e89195a0af581e248bc09e41e481805b`.

**Reason for REWORK:** the current package has useful engineering fixtures,
but its conformance report is not admissible evidence. The expected vectors
are produced by subject functions, evaluation isolation does not contain the
real evaluator, schema chronology is synthetic, J provenance is hidden rather
than rendered, schemas and certificates are incomplete, mutations do not
mutate a disposable subject, resources are undercounted, and no frozen source
closure is bound.

## 1. Decision and minimality

Retain the following verified pieces as subject implementation material only:

- the predecessor hashes and Stage-A-only claim label;
- the 16 target/twin algebra, eight certified-bypass bridges, four-way P
  completion, reduced first-accept toy values, and headline source counts;
- the existing closed transition vocabulary and deterministic handle-tape
  interface where they conform to Candidate B.

Do not patch the current tests or report until they pass. Replace the evidence
topology:

```text
ratified binding
  -> frozen subject source manifest
  -> subject black-box CLI --------------------+
  -> frozen external oracle manifest           |
       -> literal fixtures/reference engine <--+
       -> OS-contained real evaluator
       -> disposable-copy mutations
       -> independent graph/certificate replay
       -> resource and capability supervisor
  -> one sealed Stage-A report
```

`rml_d0/tests` may remain engineering tests, but no result produced by those
tests, `rml_d0.probes`, or a subject-generated expected digest is accepted as
oracle evidence. The external oracle is the only component allowed to issue a
Stage-A verdict.

This is the least-throwaway valid repair because it preserves the finite world
and most transition/source constructors while replacing only the invalid
verification seams. Stage B remains blocked and is not implemented as part of
this repair.

## 2. Finding-by-finding closure

| Rank | Finding | Required closure |
|---|---|---|
| Fatal | M9/self-oracle | A separately executable, separately hash-bound oracle imports no `rml_d0` module and contains literal expectations/reference laws. The final binding pins its complete source manifest outside the subject. |
| Fatal | Synthetic evaluation isolation | Run the actual Stage-A evaluator inside an OS-enforced disposable filesystem/process boundary; validate its output, discard its workspace, and compare actual run/skip suffix artifacts. Limit the claim honestly to the Stage-A micro-evaluator. |
| High | Fabricated schema chronology | Parse actual source events, enumerate all 24 affine laws per channel, require a singleton posterior, predict actual scheduled families, compare actual future outcomes, and derive counts from appends. Enumerate balance posterior assignments rather than adding constants. |
| High | Hidden-only J provenance | Render two E0 cartridge module families and two current cartridge module families in `TargetPublic`; make the current module the loop module; validate all eight cases and all cuts from rendered bytes plus source records. |
| High | Incomplete schemas | Provide a closed schema for every Candidate-B record and every nested object/enum, plus an independent literal parser in the oracle. Reject invalid nested values, not just top-level keys. |
| High | Fake M1--M8 | Apply exact patches to disposable copies of the frozen subject. The unmodified external oracle must kill every mutant with the named semantic failure. |
| High | Shared planner/weak certificates | The oracle owns a literal transition law and full-state BFS independent of subject `step()`. Certificates commit to the complete reached graph, minimality, all shortest signatures, and J-cut unreachability and are recomputed independently. |
| Medium | Resource undercount | One external supervisor counts all subject, oracle, and mutation work; uses conservative parent-plus-child RSS, exact transition/state events, actual temp/sealed sizes, strict `<` limits, and OS-enforced zero network/model/GPU capability. |
| Medium | Unbound source/evidence | Freeze tracked subject and oracle closures in JCS manifests, bind both hashes through new human ratification, trace loaded code, and ship the promised schema/golden artifacts. |

No threshold, fixture, law, or test expectation may be weakened to close a
finding.

## 3. Authority and freeze sequence

This repair is material because it changes the review, visibility evidence,
schemas, and isolation claim. Before implementation:

1. submit this exact design through `architecture_intake.py` and
   `architecture_deliberation.py`;
2. obtain two fresh-context interpretations, adversarial cross-critique, and
   an adjudicated disposition of every row in section 2;
3. obtain human ratification of the implementation scope and of the eventual
   binding-manifest bytes;
4. implement only the ratified paths in section 15;
5. freeze subject and oracle manifests; then run the oracle without editing
   either closure;
6. obtain a fresh independent reviewer and author-side scientific advocate;
7. keep Stage B and every GPU/model/network action blocked.

There are two freeze points. A development freeze permits unit and mutation
iteration. A final evidence freeze records exact source bytes and is mandatory
for a passing report. Changing any frozen byte returns
`NOT_RUN_WRONG_SOURCE_MANIFEST`; it never updates an expected digest in place.

## 4. True independent oracle and binding

### 4.1 Physical and import separation

Create an executable oracle package at:

```text
research_loop/oracles/rml_d0_stage_a_v1/
  run_oracle.py
  canonical_literal.py
  world_literal.py
  source_literal.py
  schema_literal.py
  bayes_literal.py
  planner_literal.py
  certificate_literal.py
  mutation_driver.py
  isolation_supervisor.py
  resource_supervisor.py
  expected_vectors.jcs
  mutations/M1.patch ... mutations/M9.patch
  mutations/M4_same_era.patch
  mutations/M6_drop_*.patch
  mutations/M6_belief_hash_only.patch
  mutations/M8_*.patch
```

The oracle process:

- is launched with isolated Python path and a standard-library-only venv;
- may not import, copy, `exec`, or dynamically load `rml_d0`, its tests, or its
  schemas;
- talks to the subject only through canonical stdin/stdout records of a
  long-lived black-box CLI subprocess;
- owns literal matrices, tables, transition templates, enumeration order,
  expected digests, and independent canonical parsing;
- validates that its runtime import trace is exactly its manifest plus the
  recorded standard-library/environment closure.

The subject may emit observations, claimed receipts, graphs, and certificates.
It may not tell the oracle what value to expect. Any subject field named
`expected`, `golden`, or equivalent is ignored and forbidden in a final
evidence record.

### 4.2 Binding that cannot co-mutate with the subject

Create three canonical manifests:

```text
research_loop/manifests/rml_d0_stage_a_subject_v1.jcs
research_loop/manifests/rml_d0_stage_a_oracle_v1.jcs
research_loop/manifests/rml_d0_stage_a_binding_v1.jcs
```

Each source-manifest entry is exactly:

```text
{path,role,sha256,size_bytes,git_blob,executable}
```

Entries are ordered by UTF-8 path bytes. Paths are repository-relative,
regular, non-symlink files. The subject manifest covers every subject source,
schema, subject unit test, workflow, and public CLI byte. The oracle manifest
covers every oracle source, literal vector, mutation patch, launcher, and
environment lock. The binding object contains the existing Candidate B/change/
consensus/human-ratification/scope hashes, both new manifest hashes, protocol,
claim label, and exact allowed report path. Avoid a ratification cycle: first
freeze and hash this binding payload; then create a new
architecture-ratification record whose `authorized_binding_sha256` names that
hash. The binding payload does not contain the new ratification record's hash.
The authorized intake state supplies the ratification record as the external
trust root at launch.

Neither the subject nor oracle contains authority to rewrite the binding or
ratification. The top-level launcher, outside `rml_d0`, verifies the intake
state, new ratification record, pinned binding, and both manifests before it
starts or imports the subject. A mismatch is `NOT_RUN_WRONG_PREDECESSOR` or
`NOT_RUN_WRONG_SOURCE_MANIFEST`, not a failed fixture and not permission to
refresh a hash.

All scoped files must be Git-tracked and the scoped worktree must match the
manifest. Unrelated repository dirt is reported but does not invalidate the
scope. A runtime loaded-file trace must be a subset of the declared closure;
an undeclared loaded source file is fatal. The report records all three
manifest hashes and the runtime trace hash.

### 4.3 Literal-vector independence

`expected_vectors.jcs` contains the bytes and digests from the reviewed
independent-oracle specification, including the two raw `RecallGoal` records.
It is never generated during a run. `canonical_literal.py` hashes those bytes
directly; it does not call a subject renderer. The subject separately renders
its output, and the oracle compares bytes.

M9 changes a subject valve/twin constant and its subject-local claimed fixture
together. Because neither mutation can reach the pinned oracle vector or
oracle code, the external comparison still fails. This co-mutation is a
mandatory final acceptance demonstration.

## 5. Closed canonical data contract

Provide `research_loop/schemas/rml_d0_objects.schema.json` as JSON Schema
2020-12 with `additionalProperties:false` at every object level. It is a
subject interface artifact, not the oracle's source of expectations. The
oracle independently implements the same key sets and enums from ratified
literal code, and cross-checks the schema's published hash.

The schema must cover all 17 named Candidate-B families, not the current six:

```text
PublicAction, PublicState, PublicEvent, SourceEpisodeReset,
NextEraSchedule, SchemaCommitment, SchemaStatusAppend,
TargetDescriptor, TargetPublic, RecallGoal, RecallFixture,
SelectionReceipt, NecessityCertificate, BeliefReceipt, ScoreRecord,
ResourceRecord, GateReport
```

The exact top-level keys remain Candidate B's keys. The repair ratification
also freezes these previously implicit nested shapes:

- `Fraction={numerator,denominator}`, reduced, integer numerator, positive
  denominator;
- `Coolant={handle,viscosity,inhibitor,outlet_temperature,pressure}` with
  `LOW|HIGH`, `LEAN|RICH`, `UNKNOWN|NOMINAL`, and `IDLE|STABLE`;
- `Cartridge={instance_handle,conditioner_family,module_family,
  module_descriptor,module_phrase,location,consumed}` with closed location;
- `Loop={handle,module_family,module_descriptor,exchanger_family,
  certified_bypass}`;
- `Valve={handle,valve_family,mode}` with
  `UNSET|BYPASS|RECIRCULATE|PULSE|DIRECT`;
- `FieldGoal={goal_handle,goal_kind}` where the primary kind is exactly
  `STABLE_RUN_AND_COMMIT`;
- `RecallGoal` as Candidate B specifies;
- action arguments selected by `action_kind`, with an exact key set for every
  action and the correct handle prefix for every argument;
- `PublicEvent.state_delta` as the complete successor `PublicState`, not an
  implementation-chosen partial map;
- schedule module records, prediction slots, commitment predictions, status
  entries, descriptor enums, rejection-count entries, proof subrecords,
  integer-mass entries, Bellman residual entries, failure entries, and gate
  evidence entries as closed `$defs` rather than free maps.

Arrays whose order has meaning declare it and reject duplicates where the
protocol requires uniqueness. Every handle is prefix-specific, not merely a
generic handle. All integer ranges, booleans, enums, minimum lengths, and
cross-field rules are checked. Cross-field rules not expressible in JSON
Schema are normative semantic validators in both implementations.

Raw validation order is fixed:

```text
UTF-8 -> exactly one LF -> duplicate-key scan -> NFC -> forbidden JSON types
-> JCS byte equality -> closed schema -> cross-field invariants -> content hash
```

Floats, nulls, duplicate or unknown keys, non-NFC strings, invalid nested
enums, wrong handle prefixes, unreduced fractions, and noncanonical bytes fail
closed. Add one positive and one negative external golden for every record
family and every nested enum branch. No subject-generated golden is admitted.

## 6. Executable world and source facts

The oracle literal world is a small independent implementation of the
published action law. It uses literal conditionals and immutable records; it
does not use the subject `step`, `apply_conditioner`, `tau_*`, renderer, action
universe, or planner. At each reached state/action, the oracle queries the
subject black-box transition service and byte-compares:

```text
legality, successor PublicState, result_code, rendered text, score
```

The oracle exhaustively evaluates the 16 target pairs/32 sides, eight bridges,
four omitted valve modes, four P completions, eight J cases/16 sides, and the
closed action alphabet. Its literals are the reviewed tables and digests from
the independent-oracle plan.

The subject source builder must stop assigning sparse truth as `era % 4` or
using family index as hidden output. Each module record explicitly binds its
schema-family handle and descriptor, while hidden truth is produced by the
actual sampled affine law and local permutations. Full panels still witness
all four outputs; the V-sparse panel omits the one actual `VF[m,S]` family.

## 7. Real 24-law schema chronology

### 7.1 Literal law roster

Both subject and oracle independently encode, in this fixed order:

```text
M0=((1,0),(0,1))  M1=((0,1),(1,0))
M2=((1,1),(0,1))  M3=((1,0),(1,1))
M4=((0,1),(1,1))  M5=((1,1),(1,0))
```

For each channel the law roster is the lexicographic product
`matrix_id M0..M5` then translation `00,01,10,11`. `eval(A,b,q)` performs GF(2)
matrix multiplication followed by XOR. Descriptor codes are exactly
`D00,D01,D10,D11`.

### 7.2 Chronology algorithm

For each boundary after K0, K1, and K2 the executable path is:

1. Seal actual `PublicEvent` bytes through the cut and their Merkle root.
2. Build and seal the actual `NextEraSchedule`, including actual module,
   schema-family, and descriptor handles; do not create a target.
3. For C and V separately, parse only legal public panel events. Infer each
   observed schema-family output from APPLY results or the four-mode valve
   trial pattern. Enumerate all 24 laws and retain precisely those matching
   every observed `(descriptor,output)` pair.
4. Require a posterior set of size one. An empty or plural set emits no
   commitment and fails; hidden truth is never consulted.
5. Use the singleton law to construct immutable predictions for every actual
   next-era schema family, including the V-sparse family.
6. Seal the two commitments before generating confirming events.
7. Generate the actual next-era source rows from the presealed schedule.
8. The comparator independently decodes each witnessed schema-family outcome
   from its source event, compares it with the sealed prediction, and appends
   exactly one MATCH or CONTRADICTION. It skips only the absent V-sparse row.
9. Derive support from at least two distinct-module MATCH appends and zero
   contradictions. Only afterward create and seal the P descriptor and public
   target, then create the evaluation snapshot.

No fixed status counts, `index % 4` predictions, placeholder event handles, or
prewritten `AFFINE_*_UNIQUE` labels are allowed. Counts `[5,11,23]` and
`[5,16,39]` must emerge from the actual append ledger. The oracle recomputes
the chain from raw records and checks the normative ordinal inequality.

### 7.3 Exhaustive law and balance checks

Stage A runs all 24 laws independently for C and all 24 independently for V.
For each law, the E0 observations at `D00,D01,D10` must reduce the 24-law
posterior to that exact law; the D11 prediction must equal literal GF(2)
evaluation. At least one integrated full K0--K3 chronology uses the production
schedule and actual source records. Channel factorization is checked by a
small cross-channel Cartesian set containing every matrix and translation in
both positions; no channel may read the other's events.

For valve balance, enumerate actual assignments:

```text
b_V in 00..11
x in all 3! permutations of the non-schema outputs
selected_dense_handle_position in 0..3
```

For each assignment, construct the V-sparse panel, selected dense-family
repetition, and action-only projection, then condition by exact projection
bytes. Reduce posterior integer counts by their gcd and require
`[6,6,6,6]` for every selected-handle position. The two-mode mutant must yield
the forbidden event totals and two-mode support. Adding six to four bins is
not an enumeration and is rejected.

## 8. Target-visible J provenance

Replace the single target-level conditioner module handle with one module
reference per conditioner family. This changes internal structures only; the
Candidate-B public cartridge shape already has `module_family`,
`module_descriptor`, and `module_phrase`.

For J, rendered `TargetPublic.initial_state.locker_items` must contain:

- exactly two cartridges whose conditioner families and module family occur
  in the selected E0 module's sealed source panel;
- exactly two cartridges whose families and module family occur in the
  selected current dense module's sealed panel;
- a loop whose `module_family` is that same current dense module;
- four fresh cartridge-instance handles, with family/module handles preserved
  from source, canonical handle-byte ordering, and pair-common H/twin bytes.

The old group contains both setters of `old_bit`; the recent group contains
both setters of the other bit. No public field says `OLD`, `RECENT`, cut,
stratum, or side. Provenance is established by joining public family/module
handles to sealed legal source records. N/O/P render four families from their
one selected loop module.

The oracle parses rendered `TargetPublic` and the source snapshot to validate
the eight `(u,old_bit)` rows. It then derives the unique useful H and twin
pairs independently and requires one old and one recent cartridge in each.
The four J variants mutate a fresh target copy before sealing:

1. remove the registered useful old instance;
2. keep it rendered but make only its APPLY illegal;
3. remove both old instances, leaving the original two recent instances;
4. remove both recent instances, leaving the original two old instances.

No variant may rewrite source history, mapping truth, handles, action budget,
or remaining positions. The independent literal planner must prove base depth
nine and no success through depth ten for all four variants on both sides.
M4 changes the subject target renderer/selector, not a hidden provenance tuple;
the external rendered-byte/source-join check must kill it.

## 9. Exact Bayes and registry-role marginalization

### 9.1 One reusable exact engine

Replace the current toy-only evidence with a data-driven rational engine used
unchanged by Stage A and later Stage B. Integers and reduced `Fraction`s are
the only numeric types. Its input is a closed registry/roster record, proposal
kernel, visible target, and within-item outcome history.

For every hidden class `h`, descriptor `d`, and attempt, compute Candidate B's
`R_n` and `W_n` recurrence literally. Compare it to:

- the closed form only when the implementation has separately proved
  acceptance probability is exactly `1/4` for every positive-mass `h`;
- brute-force caps 1--4 for the homogeneous and heterogeneous reduced toys.

The cap is never canceled for a heterogeneous class.

### 9.2 Actual `rho` sum

The Stage-A exact fixture constructs the complete 3,072-role roster:

```text
64 slots * 3 cuts * 4 strata * 2 ordinals * 2 sides
```

Slot matrix pairs are computed from Candidate B's roster. For every compatible
role, the counter enumerates the 16 translation pairs and every positive-mass
target-local assignment; unused modules contribute the exact `864^k` factor.
It evaluates the published J bit/age-conditioned inventory selector and sums
the role before normalization. No handle, cut, stratum, ordinal, side,
proposal position, or revealed ledger value is passed to the posterior as an
observed role label.

For each query the oracle independently computes:

```text
M(h;v,o) = sum_rho sum_d prior_count(rho,h) * W_cap(h,d)
           * I[Render(rho,h,d)=v] * I[Outcome(rho,h,d)=o]
```

It enumerates only positive-mass local classes, but records the exact summed
factor for every analytically integrated leaf. The subject and oracle must
match the complete ordered integer mass vector, denominator, canonical action
tie, posterior sum, and every Bellman residual numerator. A hash without the
mass object is insufficient.

To keep Stage A bounded, the exact counter operates on structural handle
variables and proves that fresh independent 48-bit handle factors are common
and cancel. Two metamorphics then validate the proof against concrete target
bytes:

- permute all registry metadata labels while preserving the roster multiset;
  the posterior mass vector and action are unchanged;
- substitute one valid independent target-handle tape value; only the target
  hash/handle bytes change, while structural posterior masses and action role
  are unchanged.

M5c alters the disposable subject's actual `rho`/belief path to classify role
from a handle. The resulting `BeliefReceipt` must disagree with the independent
mass vector under one or both metamorphics. A dummy handle classifier is not a
mutation kill.

## 10. Independent literal planning and complete certificates

### 10.1 Literal planner

The oracle planner stores the complete literal public state, not the subject's
nine-field quotient and not a subject state object. It enumerates the complete
closed public action alphabet, applies its independent transition law, and
uses breadth-first search with canonical action-byte ties. Deduplication is
allowed only by byte-identical complete literal state plus, for Bayes, the
complete reduced mass object.

For all 32 target sides it compares, through depth six:

```text
reached literal-state bytes
legal action bytes
rendered successor bytes
terminal value
canonical tie
```

It then searches through the action budget to establish depth nine, uniqueness
of pair/mode, and all shortest successful signatures. The subject quotient
planner runs separately. Equality of results does not reuse `step()` on either
side.

M6 is nine real subject mutations, one deleting each quotient field, plus a
Bayes mutation retaining only a mass hash. For each mutation the oracle must
produce a concrete pair of complete literal states merged by the mutant key
but distinguished by legality, successor bytes, value, or necessity result.

### 10.2 Certificate content and verification

Emit the actual Candidate-B `NecessityCertificate`, not a one-plan transcript.
For each base or cut target the subject performs exhaustive quotient BFS and
canonicalizes:

- every reached quotient-state byte and minimum depth;
- every explored legal edge as `(source_hash,action_bytes,outcome_bytes,
  successor_hash)`;
- all shortest successful action-signature hashes and their exact count;
- registered decisive item handles, mapping-edge IDs, state-flow edge IDs, and
  source/target root IDs;
- for cuts, the variant identifier and zero-success disposition through depth
  ten;
- verifier input hash over target public bytes, hidden truth or P-ablation
  bytes, action-law hash, and variant bytes;
- verifier output hash over the ordered state/edge/signature roots.

The compact certificate stores counts and Merkle roots plus canonical
predecessor/action witnesses; it need not store every edge. The external oracle
recomputes the entire literal graph from raw target/truth inputs, checks every
count/root/signature and the J dependency, and reproduces
`verifier_output_hash`. Merely replaying one plan or matching a stored root is
failure. Enforce 64 KiB per target and the shared 4 MiB dictionary ceiling from
Candidate B.

## 11. Actual Stage-A evaluation isolation

### 11.1 Honest claim boundary

Stage A can establish only:

```text
STAGE_A_MICRO_EVALUATOR_DISPOSABLE_OS_ISOLATION
```

It does not establish Stage-B or production-life isolation. Stage B must rerun
the same boundary with the production evaluator before its own release. The
overall verdict label remains `CPU_STAGE_A_INSTRUMENT_CONFORMANCE`, with the
isolation subclaim explicitly scoped as above.

### 11.2 Real evaluator path

Split subject operation into black-box roles:

```text
source-build -> readonly snapshot
controller-evaluate(snapshot,target) -> action/belief receipts
audit-score(snapshot,receipts) -> audit-only scores
source-suffix(snapshot) -> future source artifacts
```

`controller-evaluate` is the same Stage-A target/planner/Bayes path whose
outputs are graded by the oracle. Its output is consumed: the oracle validates
actions/beliefs with the independent planner and passes receipts to the
audit-only scorer. The scorer result is recorded but is never an input to
`source-suffix`.

At each K0--K3 cut, create one sealed source snapshot and fork two trials:

- **skip:** invoke the deterministic suffix directly;
- **run:** mount the snapshot and evaluator code read-only, run the real
  evaluator on every registered Stage-A fixture for that cut, validate and
  score its outputs into a separate audit sink, destroy its writable workspace,
  then invoke the deterministic suffix from the original source snapshot.

Byte-compare source events/state, schedules, commitments/status, future target
descriptors/handles, every tape cursor, suffix intent, and final root. Evaluator
output must be nonempty, schema-valid, independently correct, and represented
in the audit hash; ignoring dummy output is a failure.

K0 has no registered target or R fixture. Its evaluator output is therefore a
schema-valid `NO_REGISTERED_EVALUATION` audit receipt with zero action/belief
receipts, not a fabricated target evaluation. K1--K3 must each contain and
validate the actual nonempty registered evaluator outputs.

### 11.3 Enforceable boundary

Use an OS boundary, not self-installed Python hooks:

- Linux: user/mount/PID/network namespaces with a read-only bind mount and no
  network interface, plus a cgroup for process/RSS accounting;
- macOS: a deny-by-default sandbox profile that denies network, device/GPU
  access, writes outside the evaluator temp and audit pipe, and reads of
  generator/scorer source not explicitly mounted.

Only evaluator/controller files and the snapshot are visible. Generator and
scorer modules are absent from the mount, so import denial is structural.
Snapshot and subject-source mounts are read-only at the OS layer; ownership or
`chmod` cannot make them writable. The evaluator receives a fresh process,
empty cache, private temp directory, closed inherited descriptors, fixed
environment, and no inherited random state. Canary attempts cover network,
source write, generator/scorer read, GPU device, cross-life temp/cache,
processes, and file descriptors. If a supported OS boundary is unavailable,
the result is `NOT_RUN_NO_OS_ISOLATION`, never a monkeypatch-based pass.

## 12. Disposable-copy mutation protocol

Mutations are run after the clean baseline passes and never change the frozen
checkout or oracle:

1. Create a fresh temporary directory.
2. Copy only files named by the frozen subject manifest; copy predecessor
   inputs read-only. Do not copy oracle source into the subject tree.
3. Verify the baseline manifest in the copy.
4. Apply one hash-bound patch with an exact preimage. Require the changed-path
   set to equal the mutation declaration and to exclude tests, oracle files,
   expected vectors, schemas, and frozen evidence.
5. Record the baseline hash, patch hash, mutated file hashes, and diff hash.
6. Run the same external oracle and OS boundary. A mutation is killed only if
   it reaches the intended gate and yields its named semantic failure. Syntax,
   import, manifest, timeout, or unrelated setup failure is `MUTATION_NOT_RUN`.
7. Destroy the copy and verify the original subject/oracle manifests again.

Required patches and dispositions are:

| ID | Actual subject change | Required external failure |
|---|---|---|
| M1 | `tau_X(r)=r xor 10` | literal 16-target twin table/depth/disjoint-pair check |
| M2 | emit only `mu,tau_V(mu)` balance rows | exact source totals plus enumerated action-only posterior |
| M3a | include side in one target-handle draw | H/twin target-public byte collision |
| M3b | derive handle from slot/cut/stratum/ordinal/proposal metadata | fixed-tape metadata permutation and tape-substitution metamorphics |
| M4 | render four current families, and separately place both useful setters in one era | rendered J source-provenance join, useful-pair, and cut checks |
| M5a | ignore rejection survival or make first position uniform | cap 2--4 recurrence/brute-force vectors |
| M5b | cancel the cap for all classes | heterogeneous exact posterior vectors |
| M5c | condition actual `rho`/BeliefReceipt on target handle | independent 3,072-role mass vector and handle metamorphics |
| M6 | nine quotient-field deletions and one belief-hash-only key | independent literal collision witnesses and graph mismatch |
| M7 | retain affine grammar or rerun acceptance in atoms-only P | four equal completions, common visible hash, exact `1/4` value |
| M8 | three subject variants: valve-sensitive bridge, shared trial reset/object handle, seven rows | literal bridge results, certified-bypass semantics, handle independence, enumeration count |
| M9 | co-change a subject valve/twin table and its subject-local claimed fixture/digest | pinned external literal vector still rejects |

All variants are mandatory. The report includes a mutation receipt per patch
with expected and actual failure code. No `killed:true` literal may be emitted
without the corresponding disposable-run evidence hash.

## 13. Exact resource and capability accounting

One external supervisor starts before any subject/oracle dispatch and owns all
children in one process group/job. The accounting domain includes baseline,
all independent oracle enumeration, isolation run/skip branches, certificate
replay, and every mutation. The report separates core Stage-A conformance from
mutation-review cost, because Candidate B's 60-second/two-million-transition
ceiling applies to the core Stage-A run; both totals are still recorded.

Definitions are exact:

- `transitions`: one for every evaluated action edge in either subject or
  oracle, including literal BFS, quotient BFS, Bayes Bellman edges, J variants,
  P completions, bridge/source execution, certificate recomputation, and
  isolation evaluator runs. Each process writes an append-only counter segment;
  the supervisor sums segments and rejects gaps/duplicates.
- `states`: one for every first insertion into any planner/Bellman reached set;
  separate searches count separately.
- `pair_attempts` and `target_attempts`: actual fixture/proposal attempts from
  append-only receipts, never headline literals.
- `temp_bytes`: high-water total allocated bytes below all run-owned temporary
  roots, measured from file allocation blocks after each write/rename and at
  child exit; disposable mutations are reported separately.
- `sealed_bytes`: exact final byte sum of every retained run artifact named by
  the evidence manifest. Intermediate overwritten bytes do not count.
- `wall_ms`: monotonic elapsed time from post-binding verification through the
  terminal core gate decision. Report serialization is explicitly outside this
  interval and cannot alter a pass decision.
- `peak_rss_bytes`: a conservative aggregate upper bound. On Linux use cgroup
  peak memory for the complete job. On macOS record maximum supervisor RSS plus
  the sum of per-child `RUSAGE_CHILDREN` maxima; sequential-child overcount is
  allowed, undercount is not. `RUSAGE_SELF` alone is forbidden.
- `workers`: maximum simultaneous evaluation workers observed by the
  supervisor, not a constant.

Before every dispatch, add the operation's ratified worst-case reservation to
the already consumed amount. Dispatch only when the result is strictly below
the limit. At or above (`>=`) a limit is a nonpassing resource receipt. Runtime
counters are checked during loops and before adding an edge/state; hitting a
limit stops cleanly without partial pass.

Zero capability counts are enforced rather than printed:

- the whole gate uses the OS network-deny boundary; a network canary must be
  denied before subject dispatch;
- GPU devices are absent/denied and accelerator environment variables are
  cleared; a device-open canary must be denied;
- the frozen import/exec allowlist excludes model/provider/trainer packages and
  executables;
- an OS audit receipt records attempted denied operations. Any successful
  network/model/GPU capability or undeclared executable makes the count
  nonzero and fails.

Core Stage A retains Candidate B's strict limits: one worker, `<60,000 ms`,
`<512 MiB` RSS bound, `<50 MiB` temp, `<25 MiB` sealed, and `<2,000,000`
transitions. Predicted values are never substituted for actual values.

## 14. Evidence bundle and report

Add the promised independent artifacts:

```text
research_loop/goldens/rml_d0/nonemptiness_targets.jcs
research_loop/goldens/rml_d0/nonemptiness_bridges.jcs
research_loop/goldens/rml_d0/first_accept_toys.jcs
research_loop/goldens/rml_d0/canonical_records.jcs
research_loop/goldens/rml_d0/schema_24_laws.jcs
research_loop/goldens/rml_d0/j_public_provenance.jcs
research_loop/schemas/rml_d0_objects.schema.json
```

They are authored/reviewed as oracle inputs and included in the oracle
manifest; the subject does not generate them.

To avoid a hash cycle, the leaf evidence manifest names every retained evidence
artifact except itself and the final `GateReport`, with path, size, and
SHA-256. The closed `GateReport` stores the leaf-manifest hash and evidence by
hash, not arbitrary nested maps. `sealed_bytes` is the exact sum of leaf
artifacts, leaf manifest, and final report. The report's own SHA-256 is computed
by the launcher after close and printed in a non-authoritative terminal
receipt; it is not embedded back into the report. Compute `sealed_bytes` by
serializing until the integer and resulting report length reach the least
stable fixed point; failure to stabilize is a gate failure.

The report's predecessor-hash object includes the binding, new ratification,
subject manifest, oracle manifest, independent-oracle plan, and Candidate-B
authority hashes. Its gate-value object has one closed entry for each required
Stage-A gate, containing `{gate_id,evidence_hash,passed}`. `split_hashes` is
the closed empty object for Stage A. Failures are closed records with code,
gate ID, expected, actual, and evidence hash.

The report must include or hash-bind:

- every expected and actual literal-vector digest;
- actual enumerated fixture counts and schema posterior sets;
- full chronology roots and append counts;
- J rendered-provenance joins and all cut certificates;
- Bayes mass objects, recurrence comparisons, rho mixtures, and Bellman
  residuals;
- literal/quotient graph roots and all shortest-signature counts;
- isolation sandbox profile/backend hash, canary results, evaluator output
  hash, and run/skip roots;
- every mutation patch/diff/run/failure receipt;
- core and mutation resource ledgers and enforced capability receipts;
- source/oracle/runtime/evidence manifest hashes.

The only passing top-level label is
`CPU_STAGE_A_INSTRUMENT_CONFORMANCE`. The report explicitly denies learning,
memory, DREAM/SLEEP, native-context, model, LoRA, developmental, benchmark,
promotion, paper, and scientific-claim conclusions.

## 15. Ratified implementation scope

The minimal expected subject changes are limited to:

```text
rml_d0/canonical.py
rml_d0/world.py
rml_d0/source.py
rml_d0/schema_reference.py
rml_d0/targets.py
rml_d0/planner.py
rml_d0/bayes.py
rml_d0/certificates.py
rml_d0/isolation.py
rml_d0/run_cpu_gate.py
rml_d0/subject_cli.py                    # new black-box protocol
rml_d0/evaluator_cli.py                  # real Stage-A evaluator
rml_d0/tests/...                         # engineering/regression only
research_loop/oracles/rml_d0_stage_a_v1/... # independent executable oracle
research_loop/schemas/rml_d0_objects.schema.json
research_loop/goldens/rml_d0/...
research_loop/manifests/rml_d0_stage_a_*.jcs
research_loop/workflows/rml_d0_cpu_gate_v1.json
```

Delete or make non-authoritative `rml_d0.probes.EXPECTED_VECTOR_DIGESTS`,
`actual_vector_digests`, in-process `mutation_kills`, the dummy
`isolation_worker`, and the current passing `stage_a_report.json`. Preserve the
old report as rejected historical evidence if desired, but never overwrite it
as though it were a valid baseline.

No model, prompt, provider, trainer, GPU, paper, promotion, or network path is
in scope.

## 16. Required external acceptance tests

The final oracle run is green only if all of these pass in one bound core run
and one bound mutation campaign:

```text
RMLD0_REWORK_01_BINDING_MANIFEST_AND_LOADED_SOURCE_CLOSURE
RMLD0_REWORK_02_ALL_17_CLOSED_SCHEMAS_AND_RAW_CANONICAL_BYTES
RMLD0_REWORK_03_INDEPENDENT_LITERAL_WORLD_AND_16_TWIN_TARGETS
RMLD0_REWORK_04_EIGHT_LITERAL_CERTIFIED_BYPASS_BRIDGES
RMLD0_REWORK_05_ACTUAL_SOURCE_ROWS_COUNTS_AND_COMPLETE_CUTWISE_BE
RMLD0_REWORK_06_ENUMERATED_BALANCE_POSTERIOR
RMLD0_REWORK_07_ALL_24_LAWS_AND_ACTUAL_SCHEMA_CHRONOLOGY
RMLD0_REWORK_08_RENDERED_J_PROVENANCE_AND_ALL_NECESSITY_CUTS
RMLD0_REWORK_09_P_ATOMS_ONLY_FIXED_ACCEPTED_TARGET
RMLD0_REWORK_10_EXACT_FIRST_ACCEPT_RHO_BAYES_AND_BELLMAN
RMLD0_REWORK_11_INDEPENDENT_LITERAL_PLANNER_QUOTIENT_AND_CERTIFICATES
RMLD0_REWORK_12_REAL_MICRO_EVALUATOR_OS_ISOLATION_AND_RUN_SKIP
RMLD0_REWORK_13_DISPOSABLE_SUBJECT_MUTATIONS_M1_THROUGH_M9
RMLD0_REWORK_14_EXACT_RESOURCE_AND_ZERO_CAPABILITY_RECEIPTS
RMLD0_REWORK_15_CLAIM_FIREWALL_AND_FAIL_CLOSED_REPORT
```

Missing evidence is failure. A mutation setup error is not a kill. An
unavailable OS sandbox is not isolation. A hash-only belief is not a Bayes
state. A replayed successful plan is not a minimality certificate. A subject
self-check is not an independent oracle.

## 17. Release condition

Completion of this repair means only that a new, source-bound external review
finds the finite Stage-A CPU micro-instrument conformant. It does not revive the
current report, auto-release Stage B, authorize the 64-pair CPU gate, or permit
a model/network/GPU action. Any later Stage-B implementation requires the
newly passing evidence hash, a fresh independent verdict over that exact hash,
and the existing human-controlled release gate.
