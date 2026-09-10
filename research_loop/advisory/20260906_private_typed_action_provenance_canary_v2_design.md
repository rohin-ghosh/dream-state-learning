# Private typed-action provenance canary v2: minimal design

Date: 2026-09-06

Status: design advisory only. This is not an architecture change, exact-byte
ratification candidate, implementation authorization, execution authorization,
or scientific result. It authorizes no model, tokenizer, real tool,
environment, task inspection, trainer, adapter, GPU, or claim.

## Decision

Do not repair the six-type action-trace spine in place. Its public projector,
recurrent context path, lifecycle branches, and capability surface created most
of the unresolved proof burden. The next proposal should be a smaller, private,
single-episode canary whose only question is:

> Can one frozen child-response envelope be bound byte-for-byte to one offered
> tool schema, one parser decision, and one pure private mock transition in a
> prospectively written, atomically committed trace?

This closes the useful core of v1 concern C05 while deleting, rather than
hand-waving, the surfaces behind C01--C04 and C06--C16. It is a plumbing
canary, not a learning experiment.

## Frozen scope reduction

The canary has exactly one episode, one fixed invocation, one child response,
one parse decision, at most one accepted typed call, one pure in-memory mock
transition, and one terminal close. It has:

- one private root and one private ledger;
- no public projection, declassifier, public consumer, or secrecy claim;
- no prior outcomes, recall, selection, context admission, recurrence, retry,
  branch supersession, or feedback edge;
- no real environment side effect; the mock transition is a pure function;
- no parent, correction, restatement, dream, sleep, training example, trainer,
  adapter, evaluation, benchmark, report-to-life edge, or future writeback;
- no claim about a model, tokenizer, learned attention, behavior, improvement,
  memory, transport, or Experience Models.

The first implementable form, if later deliberated and exactly ratified, must
use a deterministic source-bound child stub and a pure mock tool. Replacing
either with a model server or real tool is a new material change.

## Canonical byte envelope

One committed artifact is a six-record UTF-8 JSONL file. Raw input must have no
BOM or CR, every record ends in one LF, and there are no bytes after record 6.
JSON objects reject duplicate keys before construction. Floats, `NaN`,
infinities, negative zero, and exponent forms are forbidden. Integers are
signed 64-bit unless a field below is more restrictive. Canonical JSON is
`sort_keys=true`, separators `(',', ':')`, and `ensure_ascii=false`.

Every inline byte string has exactly this closed object form:

```json
{"b64":"<strict RFC4648 base64>","byte_len":0,"sha256":"<64 lowercase hex>"}
```

The decoder rejects whitespace, alternate alphabets, missing or surplus
padding, and noncanonical encodings. It recomputes decoded length and SHA-256.
Where a byte string is declared canonical JSON, validators also parse it under
the raw restrictions above and require byte-for-byte canonical re-encoding.

Every record has exactly these wrapper keys:

```text
schema_version             = "private-action-canary/v2"
contract_sha256            = SHA-256 of the eventual exactly ratified contract
canary_id                   = "c" + 24 lowercase hex
event_seq                   = integer 0..5
event_id                    = "e" + six decimal digits equal to event_seq
event_type                  = one of the six types below
actor_role                  = the role fixed below
parent_event_id             = null at seq 0; immediately prior event otherwise
payload                     = closed event-specific object
previous_record_sha256      = 64 zeroes at seq 0; prior record_sha256 otherwise
record_sha256               = SHA-256 of canonical record without this field
```

This is one linear chain, not an event-type DAG. No cross-ledger parent
resolution exists. Event IDs are local to this canary and are never shown to a
policy.

## Exact six-event schema

### 0. `CANARY_OPEN` / `HARNESS`

Payload keys:

```text
execution_manifest_bytes   canonical JSON ByteString
child_stub_manifest_bytes  canonical JSON ByteString
mock_tool_manifest_bytes   canonical JSON ByteString
private_fixture_bytes      canonical JSON ByteString
generation_budget          integer, exactly 1
accepted_call_budget       integer, exactly 1
dispatch_budget            integer, exactly 1
```

The execution manifest names and hashes the contract, event schemas, harness,
parser, pure mock transition, canonicalizer, child stub, Python executable,
and dependency lock. The mock manifest contains the complete ordered action
vocabulary, integer opcodes, and transition constants. The private fixture
contains the fixed initial mock state and fixed child task. Nothing in the
canary is public, so this is an integrity boundary rather than a secrecy
boundary.

The v2 mock manifest is fixed semantically to three entries in this order:
`fold_constants/opcode 0/delta 3`, `simplify_cfg/opcode 1/delta 5`, and
`prune_dead/opcode 2/delta 2`. State is exactly
`{"applied":[],"measurement":20}` initially. For every opcode in order, the
transition appends its name to `applied` and sets `measurement` to
`max(0,measurement-delta)`. The successful golden stub call is
`["simplify_cfg","fold_constants"]`, yielding measurement 12 and score
`2/5`. The exact canonical manifest, fixture, and message bytes still belong
in the eventual ratified artifact rather than being inferred from this prose.

### 1. `INVOCATION_PREPARED` / `HARNESS`

This record is appended and fsynced before the child endpoint is invoked.
Payload keys:

```text
message_array_bytes         canonical JSON ByteString; exactly the frozen
                            two-message [system,user] fixture
rendered_input_bytes        ByteString
renderer_manifest_sha256   lowercase SHA-256
intended_input_ids          array of 0..4095 integers, length 1..4096
offered_tool_schema_bytes   canonical JSON ByteString
structured_config_bytes    canonical JSON ByteString
sampling_config_bytes      canonical JSON ByteString
child_request_bytes        canonical JSON ByteString
```

`child_request_bytes` is the canonical object containing the complete
ByteString objects for the message array, rendered input, offered schema,
structured configuration, and sampling configuration, plus the complete
intended-ID array; duplicating these values inside the request is deliberate
and validators require byte/array equality with the sibling fields. The offered
schema permits exactly one tool name, `private_mock.optimize`, with arguments
`{"actions":[ACTION_NAME,...]}`. The action array length is 1..16 and every
name must occur in the ordered vocabulary from event 0. There are no optional
tools. There is no context-selection rule: the two messages are immutable
fixture bytes and contain no prior-event material.

### 2. `CHILD_RESPONSE_RECEIVED` / `CHILD_STUB`

Payload keys:

```text
received_child_request_sha256  SHA-256 computed inside the child process over
                               the exact bytes it received
child_source_sha256             must equal the `source_sha256` field parsed
                                from event-0 child-stub manifest
consumed_input_ids              exact copy of intended_input_ids
raw_response_envelope_bytes     canonical JSON ByteString
assistant_text_bytes            ByteString
assistant_text_json_pointer     exactly "/response/assistant_text"
raw_tool_channel_bytes          canonical JSON ByteString or zero-length
tool_channel_json_pointer       exactly "/response/tool_call"
generated_token_ids             array of 0..4095 integers, length 0..512
stop_reason                     one of TOOL_CALL, STOP, LENGTH, ERROR
```

The child stub receives only `child_request_bytes`. Its raw response envelope
has a closed schema. Validators independently extract the value at the frozen
JSON pointer and require its canonical bytes to equal
`raw_tool_channel_bytes`; assistant text is independently extracted and bound
the same way. No marker or action-looking assistant prose has action meaning.
`received_child_request_sha256` and consumed-ID equality are stub-runtime
receipts only; they say nothing about a real serving engine.

### 3. `TYPED_CALL_PARSED` / `PARSER`

Payload keys:

```text
response_record_sha256       complete event-2 record hash
parser_source_sha256         source hash bound in event 0
parser_input_bytes           ByteString, exactly raw_tool_channel_bytes
offered_schema_sha256        exact event-1 offered schema hash
parse_status                 ACCEPTED or REJECTED
stable_error                 NONE, EMPTY_CHANNEL, MALFORMED_JSON,
                             SCHEMA_MISMATCH, UNKNOWN_TOOL,
                             EMPTY_ACTIONS, TOO_MANY_ACTIONS,
                             UNKNOWN_ACTION, or DUPLICATE_CALL
parsed_call_bytes            canonical JSON ByteString or zero-length
canonical_arguments_bytes    canonical JSON ByteString or zero-length
action_names                 exact ordered string array or []
action_opcodes               exact ordered integer array or []
call_authorization_sha256    derived authorization hash or 64 zeroes
dispatch_request_bytes       canonical JSON ByteString or zero-length
```

For `ACCEPTED`, `stable_error=NONE`; all byte fields are nonempty; the parser
must derive one call from its input under the offered schema; `action_names`
equals the argument array; opcodes are recomputed from event 0; and the
dispatch request is exactly:

```json
{"action_opcodes":[...],"call_authorization_sha256":"<derived hash>","tool_name":"private_mock.optimize"}
```

`call_authorization_sha256` is SHA-256 of the canonical JSON array containing,
in order, the contract hash, complete event-2 record hash, offered-schema hash,
parser-source hash, parsed-call ByteString object, canonical-arguments
ByteString object, action-name array, and action-opcode array. Validators
recompute it; it has no self-reference to event 3.

For `REJECTED`, every parsed/canonical/action/dispatch field is empty and the
authorization hash is 64 zeroes; the stable error is the first applicable
condition in the order printed above. No prose-derived fallback exists.

### 4. `PRIVATE_DISPATCH_RECEIPT` / `PRIVATE_MOCK_ENV`

Payload keys:

```text
call_record_sha256          complete event-3 record hash
dispatch_request_bytes     exact event-3 dispatch request bytes or zero-length
mock_tool_manifest_sha256  exact event-0 mock manifest hash
dispatch_status            EXECUTED_VALID, NOT_EXECUTED, or EXECUTED_INVALID
stable_error               NONE, PARSE_REJECTED, REQUEST_MISMATCH,
                           STATE_MISMATCH, UNKNOWN_OPCODE, or SCORE_MISMATCH
transaction_id             1 for executed; 0 otherwise
pre_state_bytes            canonical JSON ByteString or zero-length
applied_opcodes             exact ordered integer array or []
post_state_bytes           canonical JSON ByteString or zero-length
pre_measurement            positive integer or 0
post_measurement           nonnegative integer or 0
score                      reduced rational object or null
```

The mock environment is a total pure function of event-0 fixture/manifest and
event-3 dispatch bytes. It has no filesystem, network, subprocess, device, or
external side effect. On accepted input it starts from the exact frozen state,
applies each opcode once in order, and returns the exact final state. The score
is `(pre_measurement-post_measurement)/pre_measurement`, reduced by positive
gcd with positive denominator. The two validators independently recompute the
entire transition and score. A rejected parse deterministically produces
`NOT_EXECUTED/PARSE_REJECTED`, zeros/empty fields, and no transaction.

Any request/state/opcode/score mismatch is `EXECUTED_INVALID` only in a
synthetic mutated receipt; the runtime publisher must refuse to commit such a
trace. This distinction prevents an invalid fixture from masquerading as an
observed transition.

### 5. `CANARY_CLOSE` / `HARNESS`

Payload keys:

```text
terminal_status            SUCCESS or REJECTED
stable_error               NONE or exact carried parse error
event_count                exactly 6
generation_count           exactly 1
accepted_call_count        1 iff parse accepted, else 0
dispatch_count             1 iff EXECUTED_VALID, else 0
prefix_sha256              SHA-256 of exact complete canonical lines 0..4,
                           including their LF bytes
```

`SUCCESS` requires accepted parse and `EXECUTED_VALID`; `REJECTED` requires
the parse-rejected/non-dispatched path. `EXECUTED_INVALID` has no legal close
and can never be committed. No event may follow close.

## Total lifecycle

There are exactly two legal paths:

```text
INIT -> OPEN -> INVOCATION_FSYNCED -> RESPONSE_FSYNCED
     -> PARSE_ACCEPTED_FSYNCED -> DISPATCH_VALID_FSYNCED
     -> CLOSE_SUCCESS_FSYNCED -> COMMITTED

INIT -> OPEN -> INVOCATION_FSYNCED -> RESPONSE_FSYNCED
     -> PARSE_REJECTED_FSYNCED -> NOT_DISPATCHED_FSYNCED
     -> CLOSE_REJECTED_FSYNCED -> COMMITTED
```

There are no retries, repeats, alternative parents, multiple calls,
supersession, cancellation, resume, or future episode. A crash at any state
before `COMMITTED` yields an ineligible partial artifact. Budgets are constants
and are not claimed policy-visible. A second attempted generation, accepted
call, or dispatch is a hard runtime error and no close is written.

## Prospective writing and atomic durability

All work occurs under one pre-opened private directory descriptor on one
filesystem and under one single-writer lock. The writer creates
`<canary_id>.partial.jsonl` with create-exclusive, no-follow semantics and mode
0600. Each event is canonicalized, written with a complete-write loop, and
fsynced before the operation it authorizes:

1. event 1 is durable before the child request is sent;
2. event 2 is durable before parsing;
3. event 3 is durable before pure mock dispatch;
4. event 4 is durable before close.

After event 5 and file fsync, both independent validators must accept the
bytes. Under the same lock, the writer atomically renames the partial file to
`<canary_id>.committed.jsonl` without replacement and fsyncs the directory.
Only the committed suffix plus a valid close is eligible. On restart, partial
files are never resumed or promoted; they are renamed into a private
quarantine directory and remain non-evidence. A committed file is immutable.

The pure mock transition is what makes whole-canary durability honest: there
is no external effect that could occur between dispatch and ledger commit. A
real environment would require an idempotent transaction or two-phase commit
contract and is explicitly deferred.

## Evidence binding

No canary supports even the narrow claim until a separate, canonical
`evidence_receipt.json` exists. It must bind:

- the eventual ratified contract bytes and SHA-256;
- all event-schema bytes;
- execution, stub, parser, mock-transition, canonicalizer, and validator
  source bytes;
- dependency lock and interpreter/platform manifest bytes;
- declarative fixture-oracle bytes and every mutation fixture hash;
- committed canary file bytes and SHA-256;
- both independent validator outputs;
- the comparator output and complete test-registry hash.

The evidence receipt is written to a partial file, fsynced, atomically renamed
without replacement, and directory-fsynced. A committed canary without a
valid evidence receipt is an engineering artifact, not evidence. Validators
share only the ratified schemas, standard JSON/base64/SHA-256 primitives, and
the declarative oracle; they may not import canary implementation helpers.

## Deterministic resource envelope

Limits are checked before allocation where possible and before semantic use:

- exactly 6 records and exactly 6 LF bytes;
- at most 262,144 encoded bytes for the complete ledger; read at most 262,145;
- at most 131,072 aggregate decoded ByteString bytes;
- at most 65,536 decoded bytes in any ByteString;
- at most 131,072 encoded bytes in any record line;
- maximum JSON nesting depth 8, measured with the root object at depth 1;
- at most 32 ByteString objects across the ledger;
- input-ID length 1..4096; generated-ID length 0..512;
- action-name count 1..16 when accepted; each name printable ASCII length
  1..64 and present in the frozen vocabulary;
- all arrays and objects are closed by schema; unknown keys are errors;
- validation performs at most 6 record parses, 32 base64 decodes, 6 record
  hashes, 5 chain comparisons, one response extraction, one parse, and one
  mock transition of at most 16 opcodes.

There is deliberately no wall-clock SLA or memory-usage claim. Over-limit
input is rejected before publication with `E_RESOURCE`; it is never truncated.

## Validation order and stable failures

Both validators apply the same documented phase order and return the first
failure class:

```text
E_RESOURCE -> E_UTF8 -> E_JSON_RAW -> E_CANONICAL -> E_WRAPPER_SCHEMA
-> E_EVENT_ORDER -> E_HASH_CHAIN -> E_BYTESTRING -> E_PAYLOAD_SCHEMA
-> E_INVOCATION_BINDING -> E_RESPONSE_BINDING -> E_PARSE_BINDING
-> E_DISPATCH_BINDING -> E_TRANSITION -> E_SCORE -> E_TERMINAL
-> E_EVIDENCE_BINDING
```

Agreement means only that both source-distinct implementations conform to the
registered oracle for the registered fixtures. It does not establish schema
completeness, semantic security, or model/environment truth.

## Required synthetic tests

An eventual exact change must register all of these before implementation:

1. **PC1 golden_success_and_rejection:** one exact successful six-record trace
   and one exact rejected/non-dispatched trace; both validators reproduce every
   byte, binding, terminal count, and stable status.
2. **PC2 structured_channel_provenance:** mutate offered schema, structured
   config, child request, received-request hash, JSON pointer, raw envelope,
   raw channel, parser input, parsed call, arguments, action names/opcodes, and
   dispatch bytes individually; every mutation is rejected.
3. **PC3 prose_is_inert:** place valid-looking actions in assistant text while
   leaving the tool channel empty or malformed; require rejected parse,
   `NOT_EXECUTED`, dispatch count zero, and unchanged pure mock state.
4. **PC4 transition_and_order:** permute, duplicate, omit, and replace action
   names/opcodes; mutate pre/post state, measurements, transaction ID, rational
   reduction, denominator sign, and action order; independently recompute and
   reject all mismatches.
5. **PC5 total_linear_lifecycle:** reject missing, duplicated, reordered, extra,
   cross-canary, non-immediate-parent, post-close, retry, recurrence, second
   generation, second accepted call, and second-dispatch records.
6. **PC6 crash_publication_matrix:** inject a crash before and after every
   create/write/fsync/parse/dispatch/close/validate/rename/directory-fsync step;
   recovery must expose either no committed artifact or one complete valid
   immutable artifact, never promote a partial, and never execute an external
   effect (the mock has none).
7. **PC7 coordinated_relational_mutations:** recompute all downstream record
   hashes after coordinated changes to schema+response, response+parser,
   parser+dispatch, transition+score, manifests+payload, and close counts. The
   declarative oracle must still reject unless the entire bundle is a distinct
   registered fixture.
8. **PC8 resource_boundaries:** exact-limit and one-over-limit cases for file,
   line, decoded aggregate, individual ByteString, depth, ByteString count,
   token IDs, actions, action-name length, integer ranges, and canonical base64;
   require deterministic `E_RESOURCE` or the earlier raw-byte error.
9. **PC9 evidence_receipt_binding:** mutate or omit every bound source, schema,
   manifest, oracle, fixture, canary, validator, comparator, and registry hash;
   no narrow claim is eligible.

Every test fixture is immutable and named by content hash. The mutation matrix
includes single-field and coordinated relational mutations; it does not rely
only on one-sided edits.

## Claim ceiling

If this design later completes deliberation, exact human ratification,
implementation, PC1--PC9, and fresh independent audit, the maximum defensible
claim is:

> In the registered deterministic-stub/private-mock fixture, the committed
> six-event trace prospectively bound one exact child request and response to
> one offered typed-tool schema, one parser decision, and one recomputable pure
> private transition, under the registered byte, lifecycle, durability, and
> resource checks.

It must not be called a learning result, causal action benchmark, runtime model
receipt, private/public noninterference result, or real-tool atomicity result.
It does not show that a model consumed a prompt, intended an action, reasoned,
improved, remembered, learned from correction, changed via LoRA, or will behave
differently later.

## Explicitly deferred work

Each item below requires a new directive-to-ratification workflow:

- a real tokenizer or serving engine and independent consumer-side receipt;
- a real CompilerGym or other effectful environment transaction;
- public outcome projection or any semantic secrecy/noninterference claim;
- recurrent context, context selection/admission, recall, or policy-visible
  clocks/budgets;
- retries, multiple actions, multiple episodes, abandoned branches, or resume;
- parent feedback, child restatement, dreaming, sleep compilation, adapters,
  absorption assays, evaluation, benchmarks, statistics, and GPUs;
- any feedback edge into future context, weights, reports, or research intake.

## Disposition of action-trace-spine v1 blockers

- C01/C02: removed by one private root, one linear ledger, and no cross-root
  publication; PC6 covers its remaining local commit boundary.
- C03: removed with the public declassifier and every noninterference claim.
- C04/C08: removed with recurrence, admission, prior context, and
  policy-visible state; the input is one frozen fixture.
- C05: closed directly by event-1 offered bytes, event-2 raw channel bytes,
  event-3 parser bytes/prehash, event-4 dispatch bytes, and PC2/PC3.
- C06/C07/C09: reduced to the two total six-event linear paths; no branch,
  retry, or event-type recurrence exists; PC5/PC6 cover them.
- C10: closed for this bounded artifact by the evidence receipt and PC9.
- C11: removed by making no capability or side-channel claim.
- C12: addressed by coordinated relational mutations in PC7 while preserving
  the explicitly limited validator-agreement interpretation.
- C13: replaced with deterministic encoded/decoded/operation bounds and no
  wall-clock claim; PC8 covers boundaries.
- C14: wording is structural/runtime plumbing in a deterministic stub and pure
  mock only, never a causal model/tool claim.
- C15/C16: preserved as absolute out-of-scope boundaries; no behavioral or
  benchmark inference is permitted.
- C17: still open by design. This advisory is not ratification. Any authoring
  or execution requires a new hash-bound change, two fresh interpretations,
  critique, consensus, and exact human approval.

## Recommended next gate

Turn this advisory into a new architecture-change proposal only if the team
agrees the resulting evidence is worth its deliberately tiny claim. If it is
deliberated successfully, ask Rohin to ratify the exact contract bytes and CPU
stub/mock scope only. Do not bundle model integration, CompilerGym, parenting,
LoRA, or a GPU experiment into that approval.
