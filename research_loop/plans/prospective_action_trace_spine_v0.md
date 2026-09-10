# Prospective action-trace spine v0

Status: exact architecture proposal only. No implementation, model, tokenizer,
task, parent, dream, sleep, trainer, adapter, evaluator, GPU, claim, or release
authority. This deliberately replaces the over-broad nursery trace-contract
proposal with the smallest causal spine needed before prospective collection.

## Scope and non-claims

The spine records only:

`episode boundary -> rendered context -> model generation -> typed tool call ->
private environment receipt -> byte-exact public outcome projection`.

It contains no parent feedback, retrieval, dream, sleep example, adapter
receipt, report, or feedback-to-future edge. It does not force a memory path
and cannot evidence learning, parenting, dreaming, consolidation, transport,
or task improvement. Its sole claim is syntactic: a passing CPU fixture suite
shows that these six prospective artifact types and their local provenance,
projection, and capability rules are closed under the registered synthetic
cases. Actual tokenizer/engine/environment truth requires later live canaries.

## Byte format and bounded envelope

One life uses one append-only JSONL ledger. Every record is UTF-8 with no BOM,
no CR, valid scalar Unicode preserved byte-for-byte, canonical JSON
`sort_keys=true`, separators `(',', ':')`, `ensure_ascii=false`, and one LF.
Raw duplicate object keys, invalid UTF-8, NaN/Infinity, floats, negative zero,
and exponent numeric forms are rejected before object construction. Payload
numbers are integers or reduced rational `{numerator,denominator}` objects
with positive denominator.

Each record has exactly: `schema_version=1`, ASCII `run_id`, `life_id`,
`episode_id`, `event_id`; integer `event_seq`; closed `event_type`; closed
`actor_role`; sorted unique earlier same-life `parent_event_ids`; closed
`payload`; lowercase SHA-256 `code_manifest_sha256` and
`environment_manifest_sha256`; `previous_record_sha256`; and
`record_sha256`. The record hash covers the canonical object without
`record_sha256`; the previous hash covers the prior complete canonical object
including its record hash. Event ID is `e` plus 12 decimal digits equal to
event sequence. Event sequence starts at zero and increases exactly by one.

All payload bytes are inline base64 with exact length and SHA-256; no external
blob is permitted in this spine. Limits: 1 MiB decoded bytes per record, 32
parents, JSON depth 12, 4096 input IDs, 4096 generated IDs, 256 tool action
items, 100,000 records per life, and 30 seconds per complete validation. Any
limit breach has one stable error code and appends nothing.

Publication writes a same-directory temporary file, flushes and fsyncs it,
atomically renames it, fsyncs the directory, then appends its canonical line
to the ledger under a single-writer lock and fsyncs the ledger. Recovery keeps
only fully LF-terminated, schema-valid, hash-valid lines through the last valid
hash link; any extra/partial bytes are quarantined and never resumed through.

## Six closed artifact/event types

### 1. `EPISODE_BOUNDARY` / `HARNESS`

Payload exactly identifies `OPEN` or `CLOSE`, curriculum block ID, block
ordinal, episode ordinal, occurrence/repeat ordinal, retry ordinal, total and
remaining generated-token budget, total and remaining tool-call budget,
policy-visible clock/budget fields, immutable task-handle hash, and predecessor
boundary. Task identity bytes are outside the public record; the handle is a
run-local opaque identifier. One episode has one OPEN and at most one CLOSE;
no retry reuses an episode ID.

### 2. `CONTEXT_RENDERED` / `HARNESS`

Parents the current OPEN boundary and, if present, the immediately prior
public outcome. Payload carries exact rendered UTF-8 bytes, exact canonical
message-array JSON bytes, renderer/template/tokenizer manifest hashes,
intended integer input IDs, admitted public event IDs in render order, state
version, and requested generation budget. It may admit only public spine
events from the same life and past sequence. CPU fixtures treat IDs as opaque;
they do not claim tokenizer correctness.

### 3. `MODEL_GENERATION` / `CHILD`

Parents exactly one context. Payload carries engine/code/adapter/cache identity
strings, exact sampling-parameter canonical bytes, engine-reported consumed
input IDs, generated IDs, exact engine text bytes, independent-decode bytes,
stop reason, and integer token/time counters. Consumed IDs must equal intended
IDs exactly in the artifact. CPU fixtures prove only record consistency; a
later live canary must capture consumer-side truth independently.

### 4. `TOOL_CALL_PROPOSED` / `CHILD`

At most one may parent a generation in this spine. Payload carries the exact
structured-output channel/schema hash, tool name, canonical argument bytes,
parsed object, and parser receipt. For CompilerGym the closed argument shape is
`{"actions":[nonempty exact action-name strings]}`. An action-like substring
in generation text never dispatches. A generation with no typed call simply
has no call child.

### 5. `TOOL_RESULT_PRIVATE` / `ENVIRONMENT_PRIVATE`

Parents exactly one tool call. Payload carries opaque task handle plus private
canonical target identity bytes, reset-state module bytes hash, parsed action
names and exact environment indices, pre/post state hashes, pre/post integer
measurements, reduced rational score, validity/error, environment code and
dependency manifests, and a monotonically increasing environment transaction
ID. Score law is exactly `(pre-post)/pre`, requires `pre>0` and `post>=0`, and
is independently recomputed from integers. The environment resets, hashes the
state, applies exactly the recorded indices once in order, observes post, and
publishes one transaction atomically. Any mismatch produces a private invalid
receipt and no public success value.

### 6. `TOOL_RESULT_PUBLIC` / `ENVIRONMENT_PUBLIC`

Parents exactly one private result but is stored in a separate public ledger.
Payload carries private-record SHA-256, tool-call event ID and action hash,
validity, public error class, pre/post integer measurements, reduced rational
score, and exact public outcome text bytes. It contains no target identity,
URI, module/state hash, environment path, action indices, source code path, or
private filename. The projection is a pure allowlist function from the private
record; recomputation must be byte-identical. Public consumers receive only
this record. A failed/invalid private receipt projects validity/error but no
measurement or score fields.

## Capability and lifecycle rules

`HARNESS` reads episode metadata and prior public records; `CHILD` reads one
rendered context; `ENVIRONMENT_PRIVATE` reads the opaque task map, typed call,
and private state; `ENVIRONMENT_PUBLIC` reads one private result and writes one
public projection. No role gets a directory containing both private task map
and public consumer inputs except the one-way projector, whose output root is
write-only to it. Later parent/dream/compiler/trainer roles do not exist here.

Private and public ledgers have separate roots, manifests, hashes, locks, and
writers. Context may reference public event IDs only. The private event ID and
hash are opaque provenance anchors, not policy-visible target identity. There
is no edge from any output back into a future life, parent, dream, compiler,
trainer, adapter, evaluator, or research intake.

## Registered CPU acceptance tests

All tests are required after authorized implementation and before a later
integration proposal. A third declarative fixture oracle defines exact
accept/reject and error codes; two validators share only Python/JSON/SHA-256
and the written schemas, import no common project helper, run in distinct
processes, and must agree.

- **ST1_canonical_chain_and_recovery:** golden chain plus duplicate keys,
  invalid UTF-8/BOM/CRLF, number edge forms, wrong IDs/sequences/hashes,
  partial line, fsync/rename interruption, concurrent writer, size/depth/count
  limits, and deterministic resume/quarantine.
- **ST2_episode_budget_lifecycle:** accept OPEN->events->CLOSE and explicit
  repeat/retry/remaining-budget transitions; reject missing/duplicate/open-
  after-close, reused retry ID, invisible budget mutation, and over-budget
  generation/call.
- **ST3_context_generation_local_roundtrip:** intended/consumed ID equality,
  exact byte/hash fields, one-context cardinality, adapter/cache identity, and
  deterministic mismatch errors, explicitly labeled CPU self-consistency only.
- **ST4_typed_call_cardinality:** zero-or-one typed call per generation; reject
  text-only actions, multiple calls, wrong schema/tool, empty/unknown actions,
  duplicate dispatch, and malformed canonical arguments.
- **ST5_private_dispatch_score_atomicity:** synthetic environment state machine
  recomputes indices, pre/post hashes, integers, reduced rationals, transaction
  uniqueness, atomic invalid result, and no retry under injected wrong state,
  index, action order, score, crash, or partial publication.
- **ST6_public_projection_noninterference:** recompute the exact public allowlist
  projection; reject every forbidden private field/byte, symlink/path escape,
  alternate encoding, covert extra key, stale private hash, invalid-success
  measurement, or public/private mismatch.
- **ST7_role_capability_fixture:** role-specific roots plus inherited-FD,
  environment, symlink, path traversal, IPC, network, stdout/log-name, cache,
  and timing/error-channel fixtures. CPU scope claims only that registered
  synthetic channels are denied; live runtime noninterference is deferred.
- **ST8_closed_graph_and_no_feedback:** accept the exact six-type DAG including
  valid shared-ancestry diamonds; reject true back edges, abandoned/private
  release, undeclared artifacts/roles, and every output-to-future edge.
- **ST9_dual_validator_mutation:** one-sided mutations of every field class,
  projection, edge, limit, and expected error must make the comparator reject;
  the receipt discloses the shared trust base and cannot claim truth beyond
  the fixture universe.

## Human and promotion boundary

Exact ratification would authorize only schema files, two CPU validators, the
declarative synthetic fixture/oracle, and ST1--ST9 execution. It would not
authorize a tokenizer, engine, real environment, real task, life collection,
parent, dream, sleep compiler, trainer, adapter, evaluator, GPU, or scientific
claim. After tests pass, a fresh independent reviewer and author-side advocate
may propose—not authorize—live integration under a new exact change.

