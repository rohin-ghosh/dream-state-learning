# Prospective nursery causal-trace contract v0

Status: exact architecture proposal only. No schema implementation, model,
tokenizer, task selection, parent lesson, benchmark, trainer, GPU, scientific
claim, or release authority. This proposal defines the evidence substrate that
the next nursery life must produce prospectively.

## Question

Can one append-only event contract preserve the exact causal path

`context -> THINK -> typed action -> public outcome -> parent correction ->
child restatement -> dream successor -> admitted sleep example -> adapter`

without turning any of those event types into a separately learned cognitive
module or leaking later targets/scores into earlier roles?

This is infrastructure. THINK remains one free-flowing base-model operation.
DREAM is THINK directed at reconciliation of conscious state. SLEEP remains
selection/transformation plus a write. Typed actions separate effectful tool
use from prose; they do not create a learned planner, verifier, or controller.

## Canonical append-only envelope

One life owns one JSONL ledger. Every line is UTF-8 canonical JSON using
`sort_keys=true`, separators `(',', ':')`, `ensure_ascii=false`, no NaN or
Infinity, and exactly one terminal LF. Each record has exactly:

- `schema_version`: integer `1`;
- `run_id`, `life_id`, `episode_id`, `event_id`: nonempty ASCII identifiers;
- `event_seq`: zero-based integer, strictly increasing by one within life;
- `event_type`: one closed enum value below;
- `actor_role`: one closed enum value below;
- `parent_event_ids`: sorted unique IDs, each earlier in the same ledger;
- `payload`: event-type-specific object with no undeclared keys;
- `code_manifest_sha256`, `environment_manifest_sha256`: lowercase SHA-256;
- `previous_record_sha256`: 64 zeroes for event zero, otherwise the prior
  complete canonical line excluding its terminal LF;
- `record_sha256`: SHA-256 of the canonical object with this field omitted.

`event_id` is `e` plus the zero-padded 12-digit event sequence and is never
reused. A crash may leave an unterminated temporary file, but publication uses
atomic rename and the next process may resume only from the last fully parsed,
hash-valid LF-terminated record. Records are never edited or deleted.

## Closed event types and payloads

### `CONTEXT_RENDERED` by `HARNESS`

Carries exact rendered UTF-8 bytes, exact message-array canonical JSON bytes,
chat-template file hashes, tokenizer identity, special/stop IDs, intended
input IDs, generated-token budget, state version, and the ordered event IDs
whose content was admitted. Large bytes may live in a content-addressed blob;
the payload then carries byte length, SHA-256, MIME type, and relative blob
path under the same immutable ledger root.

### `MODEL_GENERATION` by `CHILD`

Parents exactly one `CONTEXT_RENDERED`. Carries engine identity, adapter
identity or explicit base-only value, sampling parameters, engine-reported
consumed input IDs, generated token IDs, exact engine text bytes, independent
decode bytes, stop reason, wall time, and token counts. Consumed IDs must equal
the parent intended IDs. This event is free-form THINK output and has no
effectful action merely because its text resembles one.

### `TOOL_CALL_PROPOSED` by `CHILD`

Parents one `MODEL_GENERATION`. Carries a typed JSON tool call emitted through
the bound structured-output/tool-call channel: tool schema hash, tool name,
canonical argument bytes, parsed argument object, and parser receipt. For the
CompilerGym nursery the argument is an ordered nonempty list of exact action
names. Text markers such as `ACT:` are diagnostics only and never dispatch.

### `TOOL_RESULT` by `ENVIRONMENT`

Parents exactly one `TOOL_CALL_PROPOSED`. In one atomic record it carries the
canonical target identity, reset-state module/content hash, exact parsed action
names and environment indices, pre-action integer measurement, post-action
integer measurement, exact rational score numerator/denominator, validity,
error kind, environment identity, and pre/post state hashes. The reset module
must match the episode's sealed task record before an action is applied.

### `PARENT_FEEDBACK` by `PARENT`

Parents only training-visible events from the same episode. Carries exact
feedback bytes, the ordered evidence event IDs actually viewed, one useful
behavior, one concrete process failure, one question for the child, one small
exercise/next experiment, and a closed `answer_content` declaration. It may
propose credit assignment but cannot contain an environment action answer,
unobserved outcome, held-out identifier/score, or future event. Parent identity,
prompt, model/human provenance, and consumed inputs are explicit.

### `CHILD_RESTATEMENT` by `CHILD`

Parents one `PARENT_FEEDBACK` plus its public evidence. Carries exact child
restatement bytes, a scoped lesson claim, confidence, proposed transfer test,
and—when effectful—an independently recorded typed call event rather than an
action hidden inside prose.

### `DREAM_SUCCESSOR` by `CHILD`

Parents a closed set of prior same-life events. Carries a complete candidate
successor conscious state with exactly: current goal, current environment
state reference, current working model, unresolved surprises, active plan,
scoped notes, evidence event IDs, intentionally omitted ledger event IDs, and
rollback predecessor state ID. Publication requires schema validity, all
evidence references earlier and readable, no target/role visibility violation,
and a successful restoration test for one predeclared omitted fact. Publishing
the successor changes the next context pointer but never deletes ledger bytes.

### `SLEEP_EXAMPLE` by `COMPILER`

Parents only admitted training-life events. Carries one class from
`THOUGHT_CONTINUATION`, `TOOL_CALL_CONTINUATION`, or
`DREAM_STATE_CONTINUATION`; exact source event IDs; admission-rule ID and
public support receipt; rendered training input IDs; exact target IDs; full
label array; target-aligned projection; masked-input spans; supervised-target
spans; EOS policy; and scaffold level. Tool results, parent text, ledger
evidence, and old transcript are masked inputs. Only validated child thought,
typed call, or dream-successor bytes may be supervised targets. Zero-target,
truncated-target, missing-EOS, unsupported, cross-role, or target-visible
examples are rejected with a separate immutable rejection event in the later
writer design; this contract never silently drops them.

### `ADAPTER_RECEIPT` by `TRAINER`

Parents the exact ordered `SLEEP_EXAMPLE` set. Carries frozen base/model/
tokenizer identities, target-module inventory, rank/alpha/dropout, optimizer
and schedule, seeds, deterministic flags, ordered example hashes, input/label
hashes, supervised-token and update counts, loss trajectory, nonfinite checks,
generic-preservation receipt reference, and canonical raw adapter-tensor hash.
It never contains or reads evaluation targets, outputs, or scores.

## Actor roles and capability boundaries

Closed roles are `HARNESS`, `CHILD`, `ENVIRONMENT`, `PARENT`, `DREAM`,
`COMPILER`, `TRAINER`, `EVALUATOR`, and `REPORTER`. `DREAM` is an execution
role using the same child model/weights, not a learned module.

- HARNESS renders only the current state and explicitly admitted event bytes.
- CHILD reads its rendered context and emits free thought or typed calls.
- ENVIRONMENT reads only one sealed training task and one typed call.
- PARENT reads only the public training trace and its fixed process rubric.
- DREAM reads only same-life training events selected by a separately bound
  context-reconciliation request.
- COMPILER reads only closed training-life events and admission receipts.
- TRAINER reads only frozen `SLEEP_EXAMPLE` artifacts and training manifests.
- EVALUATOR reads only the sealed evaluation task, ordinary birth state, and
  exact adapter; it cannot read parent, corpus, training ledger, or source task.
- REPORTER reads immutable aggregate receipts, never raw target-bearing data
  unless the later benchmark explicitly authorizes it.

Implementations run with role-specific input roots and one role-specific
output root. A path/capability manifest enumerates every readable/writable
artifact. Merely omitting a field from a prompt is not a visibility guarantee.

## State and ordering invariants

1. A generation has exactly one context parent and records actual consumed IDs.
2. A tool call has exactly one generation parent; a tool result has exactly one
   call parent; `(life, episode, call)` is unique.
3. Parent feedback cannot precede or reference an unseen event.
4. A restatement must reference its exact feedback and evidence.
5. A dream successor cannot become current until validation and rollback pass.
6. A sleep example cannot reference evaluation-role or future events.
7. An adapter receipt cannot precede or omit any ordered example it claims.
8. No result, report, or evaluation event is automatically eligible for later
   life, dream, compilation, parenting, or training.

## Proposal-level acceptance tests

This change authorizes only CPU schema/validator/fixture implementation after
exact human ratification. It registers:

- **NT1_canonical_hash_chain:** golden encode/decode plus tamper, reordering,
  duplicate-ID, bad-parent, partial-line, NaN, and resume fault injections.
- **NT2_event_schema_closure:** reject every undeclared event type, actor,
  field, parent cardinality, cross-life reference, and invalid state edge.
- **NT3_context_generation_roundtrip_fixture:** synthetic intended/consumed
  IDs and text/decode receipts; reject any mismatch without a model call.
- **NT4_typed_tool_atomic_join:** synthetic typed call/result fixtures cover
  wrong schema, hidden text action, wrong module, wrong index, duplicate call,
  nonfinite/rational mismatch, partial result, and stale environment state.
- **NT5_role_visibility_noninterference:** per-role capability fixtures prove
  permitted reads succeed and parent/trainer/evaluator cross-boundary reads and
  writes fail, including indirect symlink/path traversal.
- **NT6_parent_temporal_blindness:** reject future, evaluation, unobserved,
  hidden-answer, and undeclared evidence references; accept process-only public
  trace feedback.
- **NT7_dream_reversible_successor:** validate complete successor state,
  immutable predecessor, omission manifest, restoration, pointer swap, and
  rollback under injected invalid/missing evidence.
- **NT8_sleep_label_projection:** synthetic examples prove masked inputs,
  identical target-aligned IDs/labels, target/EOS retention, nonzero supervised
  tokens, no right-truncation, and class-specific target types.
- **NT9_adapter_provenance_fixture:** synthetic trainer receipt closes exactly
  over ordered examples and rejects missing/reordered examples, wrong masks,
  target visibility, nonfinite loss, or tensor identity mismatch.
- **NT10_no_feedback_edge:** graph reachability and filesystem fixtures prove
  evaluator/report outputs have no permitted edge into life, dream, compiler,
  parent, trainer, or future intake.

All fixtures are synthetic and contain no benchmark target, model output, or
GPU result. Two source-distinct validators with no shared project helper module
must agree on golden and adversarial fixtures. A third declarative oracle
specifies expected accept/reject and error codes.

## Exact human boundary

Ratifying this proposal would authorize only:

1. JSON schemas for the envelope and nine event types;
2. two CPU/no-model/no-tokenizer validators;
3. a third declarative synthetic fixture/oracle pack;
4. NT1--NT10 CPU execution and a static role-capability manifest candidate;
5. a later exact nursery benchmark proposal built on the passing receipts.

It would not authorize collecting a life, choosing a gym/task split, writing a
parent lesson, running a model/tokenizer/trainer/evaluator, mounting an adapter,
using a GPU, or making a scientific claim. Those require a new hash-bound
benchmark deliberation and exact human ratification.

