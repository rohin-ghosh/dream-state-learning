# Field information ontology contract

Status: proposal-only repair for `CONS_D01_CLOSED_VISIBILITY_ONTOLOGY` and the phase vocabulary required by `CONS_D04_PREMODEL_POSTDEV_PHASE_SPLIT`. This contract grants no implementation, fixture, model/provider call, CPU, GPU, training, scientific, publication, claim, promotion, or successor authority. It is not evidence that an ontology, serializer, or test currently exists.

## 1. Scope and retained V1 obligations

V1's 13-by-21 table is Cartesian coverage of a declared vocabulary, not a closed information universe. This repair requires a closed, hash-bound field ontology before a later proposal calls a visibility matrix exhaustive. It retains every valid V1 obligation: presealed constant-shape envelope-age cadence; realized unpadded `PAYLOAD_AGE/L_native`; OLD embargo; physical unpadded-stream-first AS-CTX; filler stop; exact Dream/snapshot/checkpoint ties; immutable lineage-local SELF instances; nonmerging equivalence; revision/addition; lifecycle/cursor/exhaustion/constant-shape returns; randomized one-probe unmount forks; common-prior-plus-delta evaluation; assignment-independent paired RNG and no-resample cuts/shams; failure-inclusive links and controls; sterility/reset; baseline/resource accounting; both AS-EXT candidates; the descriptive-only eight-root B3 terminus; and all existing claim/authority firewalls.

This repair does not convert prospective specifications into evidence or broaden a current claim.

## 2. Closed bundle and terms

`B` is the closed proposal bundle selected by a later V2 `change.json`. It includes this contract, the fork/phase contract, every V2 contract that names or serializes information, and every retained V1 contract whose fields are inherited. That `change.json` must bind, by relative path and SHA-256, every member of `B`, this contract, the canonical ontology manifest, field registry, role-policy registry, serialization-schema set, and acceptance-gate specification. A filename, Git revision alone, or implementation log hash is not a binding.

| Term | Normative meaning |
|---|---|
| **serialized field** | A named value, container, tag, key, length, count, order token, status, omission marker, error, receipt, handle, path-like identifier, hash, seed, time, or byte sequence written to, passed through, returned from, persisted by, logged by, or observable at any component/service boundary. Encoding, hashing, encryption, padding, summarization, or relocation into metadata does not stop it being a field. |
| **descendant** | A field whose value, presence, absence, shape, order, name, route, seed, timing, error, cache state, or control effect is directly or transitively derived from another field. |
| **field definition** | A canonical schema location, including every container and leaf, with a stable `field_uid`; it is not merely a runtime value. |
| **field instance** | One slot-specific occurrence of a field definition. Fixed-shape unavailable, malformed, abstained, missing, and failed slots are instances, not omissions. |
| **reader / writer** | A component or boundary that can respectively observe or create, alter, select, retain, route, suppress, or cause a field. A retry, timeout, route, rank, or omission controller is a writer of that control descendant. |
| **post-exit consumer** | The sole component, if any, allowed to receive a field after its producing phase exits. `NONE` requires destruction; terminal audit is never implicit. |

No debug channel, provider request, test harness, filesystem path, cache, metric, exception, receipt, or implementation detail may introduce an out-of-ontology field.

## 3. Required exactly-once registry record

The later hash-bound manifest must contain exactly one record for every `field_uid`, with every member below present:

```text
field_uid = SHA256(bundle_hash || source_artifact_sha256 || canonical_schema_path || wire_tag || canonical_field_version)
canonical_schema_path = absolute-within-bundle address, including containers
parent_field_uids = ordered direct containment / derivation parents
field_class = exactly one Section 4 class
taint_inputs = every direct information/control dependency
direct_writers = closed authorized writer set
direct_readers = closed authorized reader set
post_exit_consumer = one named consumer or NONE
wire_schema_digest = canonical serializer/schema digest
shape_rule = bytes, cardinality, order, status, omission, and failure rule
persistence_boundary = first legal retention boundary and last live boundary
destruction_point = mandatory erase / unmount / reset boundary
destruction_receipt_class = receipt field or NONE when serialization is prohibited
allowed_derivations = closed descendant field_uid set
forbidden_derivations = explicit denial for every otherwise reachable sink
```

`canonical_schema_path` includes nested maps, arrays, envelopes, model-call arguments, provider responses, reset receipts, and error/status alternatives. A non-finite key space is ineligible unless converted to a finite fixed-shape schema before B0. The registry must define both a field and its finite planned instance domain. An unbounded or late-created field fails closed. Inherited V1 fields must be copied into the V2 universe with their source digest and reclassified; citing a V1 class name is insufficient.

## 4. Closed information-class vocabulary

This is the complete class vocabulary for `B`. The named repair classes must remain named even if a later registry proves one has zero members; zero members never permits an unclassified field.

| Class | Maximum positive readers / required disposition |
|---|---|
| `PUBLIC_OPPORTUNITY` | ordinary wake actor; current ordinary operation only |
| `PUBLIC_LIVED_EVENT` | wake, Dream, target-blind sleep; declared life/sleep boundary only |
| `PUBLIC_WITNESS_ATOM` | declared memory/compiler readers; deterministic public-event extraction only |
| `SELF_SEMANTIC_CONTENT` | declared memory/compiler/reader interface, subject to lifecycle rules |
| `SELF_LIFECYCLE_STATUS` | lifecycle compiler and declared reader; never a ranking/correctness/target channel |
| `SCHEDULE_AND_CLOCK_STATE` | scheduler/renderer only; no cognition from envelope, padding, or realized-length control |
| `READER_CURSOR_AND_EXHAUSTION_STATE` | one target-local reader; destroy at item exit |
| `CANDIDATE_POSITION_AND_ALLOCATION_ORDER` | declared reader; deterministic allocation order only, never utility/rank |
| `SERIALIZATION_AND_SHAPE_METADATA` | serializer/boundary certifier only; padding/hash/header does not declassify |
| `EXPLORATION_CAPABILITY_AND_HANDLE_METADATA` | separately declared randomizer/installer/resetter roles; no semantic read; destroy at fork reset |
| `EXPLORATION_ASSIGNMENT_METADATA` | content-blind randomizer, metadata-only resetter, terminal audit; no positive cognition or compiler input |
| `EXPLORATION_MEMORY_CONTENT` | fixed-shape installer and local diagnostic reader only; unmount after one probe |
| `BRANCH_PUBLIC_EVENT` | target-blind post-unmount compiler; only permitted branch-varying compiler input |
| `BRANCH_DELTA` | evaluation installer and declared sterile reader; common authentic prior plus sealed delta only |
| `EVAL_GOAL_AND_EPHEMERAL_QUERY` | one sterile evaluation actor/reader; destroy at item exit; no life writeback |
| `EVAL_OUTCOME` | scorer/terminal audit; no cognitive, retry, life, or later-target feedback |
| `HIDDEN_TRUTH_AND_TARGET_ALLOCATION` | generator/certifier/scorer; never cognition or target-blind compiler |
| `ARM_AND_CAPACITY_ASSIGNMENT` | trusted installer/terminal audit; no policy, score, or target path |
| `FAILURE_STATUS_AND_REASON` | declared failure mapper/audit; fixed shape and no semantic retry/signal |
| `TIMING_AND_RESOURCE_TELEMETRY` | resource auditor/terminal audit; no latency/cost/cache feedback to cognition |
| `PROCESS_CACHE_AND_RESET_METADATA` | resetter/auditor only; destroy/reset; no model-visible receipt |
| `DESTRUCTION_AND_ABSENCE_RECEIPT` | reset certifier/terminal audit only; not model-visible input |
| `PRIOR_RESULTS` | terminal analysis only; no B3 cognitive or target path |
| `RESOURCE_AUDIT` | resource auditor and post-B3 selector only as Section 8 permits; no B3 retuning/abort signal |
| `A2_PREMODEL_CONFIGURATION` | declared B3 components through frozen configuration only; immutable after A2 |
| `POST_B3_DEV_DISPOSITION` | post-seal reporting/planning only; forbidden to every B3 path |
| `COMPOUND_RESTRICTED` | only the intersection of all source-class permissions when one named source class cannot represent the combined taint |

The expressly named omitted/conflated classes are `PUBLIC_WITNESS_ATOM`, `SELF_SEMANTIC_CONTENT`, `SELF_LIFECYCLE_STATUS`, `SCHEDULE_AND_CLOCK_STATE`, `READER_CURSOR_AND_EXHAUSTION_STATE`, `CANDIDATE_POSITION_AND_ALLOCATION_ORDER`, `EXPLORATION_CAPABILITY_AND_HANDLE_METADATA`, `FAILURE_STATUS_AND_REASON`, `TIMING_AND_RESOURCE_TELEMETRY`, `PROCESS_CACHE_AND_RESET_METADATA`, `DESTRUCTION_AND_ABSENCE_RECEIPT`, `PRIOR_RESULTS`, `RESOURCE_AUDIT`, `A2_PREMODEL_CONFIGURATION`, and `POST_B3_DEV_DISPOSITION`.

## 5. Most-restrictive taint

For a field `f`, `T(f)` contains its declared class, every containment-ancestor class, and every direct/transitive input/control class in `taint_inputs`. Taint is transitive and non-declassifying:

```text
effective_readers(f) = intersection(allowed_readers(c) for c in T(f))
effective_writers(f) = intersection(allowed_writers(c) for c in T(f))
effective_exit(f) = earliest mandatory destruction/exit in T(f)
effective_shape(f) = strongest fixed-shape rule in T(f)
```

The registry class is the unique most-restrictive class representing this policy. If no source class represents the exact intersection, the field is classified once as `COMPOUND_RESTRICTED`, with its source-class set and intersection recorded; if that cannot express the policy, the bundle fails. Hashes, encrypted blobs, padding, opaque handles, aggregates, Booleans, error codes, and receipts retain source taint. `direct_readers`, `direct_writers`, and the post-exit consumer must be subsets of the effective policy. Shape, persistence, destruction, and derivations may be stricter than class defaults, never weaker.

## 6. Shape, retention, and destruction

Every row fixes container tags/keys, byte or bucket width, cardinality, order, placeholders, status/error alternatives, omission behavior, and retry count. Unavailable content must emit the registered fixed-shape placeholder; changed length, order, absence, or special error path is a violation unless itself registered with the same or stricter policy. Persistence includes process cache, provider session, temporary path, index, environment variable, queue, log tail, and timing record. `destruction_point` removes every descendant, including keys, cursor/order, handles, caches, errors, timing state, and derived seeds. A destruction receipt can prove removal but cannot contain semantic content, reach a model, alter RNG, or drive retries.

After the diagnostic probe, the only exploration-treatment/assignment descendant that may reach the delta compiler is the ordinary public action/outcome in `BRANCH_PUBLIC_EVENT`. Capabilities, handles, labels, registry state, receipts, errors, timing, cache state, and assignment-derived seeds are prohibited. Evaluation goal/query/return/cursor state is destroyed at item exit and cannot persist to life memory or another target.

## 7. Exact set-equality gate

Let `U_def` be all field definitions found by canonical traversal of every bound schema, contract-declared serialization, boundary message, log, cache, receipt, status/error alternative, and derived-field declaration; let `R_def` be registry `field_uid`s. Let `U_inst` be all finite legal preallocated instances across roots, sides, checkpoints, arms, lanes, calls, sample slots, targets, failure paths, and exits; let `E_inst` be all instances emitted, retained, routed, or observed in an execution.

A newly registered ontology-closure acceptance gate (no identifier is invented here) fails closed unless:

```text
U_def = R_def
for every r in R_def: count_registry_records(r) = 1 and count(field_class(r)) = 1
U_inst = E_inst
for every i in E_inst: field_uid(i) in R_def
every emitted derivation is in allowed_derivations(source)
every reader, writer, consumer, shape, retention, and destruction event equals or is stricter than its row
every effective policy is the Section 5 intersection
```

Equality is canonical-ID set equality, not counts, samples, schema-name matching, or “all known fields” prose. The gate reports and fails on each symmetric difference: `U_def \ R_def`, `R_def \ U_def`, `U_inst \ E_inst`, and `E_inst \ U_inst`. A duplicate, unregistered field, dynamic key, omitted unavailable slot, unlogged cache/receipt/error field, unregistered serializer, or unmatched emitted instance is failure; it may not be silently classified, padded, discarded, or repaired.

Static traversal and adversarial dynamic runs must cover success, NULL, malformed, abstained, timeout, denied, reset, crash, unavailable, and terminal-seal paths. Mutations of target, truth, scorer, result, assignment, label/order, capability, handle, timing, error, resource, cache, path, packet length, schedule, cursor, and failure fields must prove the registered most-restrictive policy/noninterference or fail. This is additive to retained V1 mutation, reset, sterility, paired-seed, and independent reproduction requirements.

## 8. A2 implementation boundary

This document defines a protocol, not actual implementation fields. Exact schema fields, tags, serializers, runtime instance domains, discovery output, gate code, fixtures, and golden vectors may be added only in one separately reviewed A2 implementation package. That package must be hash-bound into the later V2 bundle, independently reviewed, and explicitly authorized under the retained premodel freeze before any scientific model call. It may refine only by adding exactly-once rows and rerunning set equality; it may not create an unreviewed side channel or silently weaken an inherited field's class, access, shape, persistence, or destruction rule.

Until that package, binding, review, equality evidence, and exact human scope exist, conformance is absent. Missing evidence is `NOT_RUN`; this proposal opens no B0/B3, Stage C/D, LoRA, or claim.
