# PPC5r4 systems closure draft

Status: **integration draft only**. This document has no normative authority,
does not amend PPC5r3, and authorizes no implementation, static seal, model,
tokenizer, embedding, trainer, canary, behavioral, GPU, or claim action. A
successor may use this text only as proposal input to the durable architecture
intake required by `AGENTS.md` and `research_loop/ARCHITECTURE_INTAKE.md`.

## 1. Binding and scope

This draft translates the following exact PPC5r3 rework chain into candidate
implementation-ready replacement language:

- architecture change SHA-256
  `460f37b0f78be15bc900151fb84eb38184fde10a1362ce927d29965b63888da1`;
- systems interpretation SHA-256
  `ce50f2f72c100ee39a6f5fd50e4de1f6091b637e8464934ed77f3471746fb835`;
- science interpretation SHA-256
  `17e3e5d90a70a2a25d4c458d00886f049b182b814207c015b0524b8fd6beb9a6`;
- adversarial critique SHA-256
  `f3217cb9237a198bb63d7d3ca16037f3295bbf0c3f0775cb23c4302a57148212`;
- consensus file SHA-256
  `94564b5be5ddb15b5190f12946ce08480a1e665c2332aac581e925eee8b1cf3a`.

The binding consensus recommendation is `rework`; its state is
`human_required`, its human decision is pending, and
`implementation_forbidden` is true. PPC5r2 and older material remains
provenance only. This draft closes only the systems surfaces required by
D01-D03, D07, and D09-D12, including their interfaces to D04-D06, D08, and
D13. It preserves the four separate assays, the frozen THINK/DREAM/ACT model,
the READ-provider-only learned adapter, the r3 freeze matrix, the nominee-first
evidence gate, D1A-only prospective wrong-life matching, D1D total-policy
treatment, exact claim boundaries, and the architecture-versus-run authority
split.

All names ending in `.v4` below are proposed successor names, not existing
contracts. All numeric counts, capacities, model artifacts, seeds, margins,
thresholds, and recipes remain populated run-lock values unless an algorithmic
constant is stated here.

## 2. Consensus defects and explicit draft choices

The r3 consensus gives the right closure direction, but four points cannot be
implemented literally without a successor decision. They must be visible in
the r4 proposal and disposed by its fresh interpretations and consensus.

1. **D02 makes mutually exclusive queue endings conjunctive.** It says every
   queued slot binds provider, intervention, public-flush, *and* discard
   receipts. A slot executed by a provider cannot also be discarded
   unexecuted. This draft replaces that sentence with an exclusive terminal
   lifecycle: every `QUEUED` slot has exactly one successor, either `FLUSHED`
   (provider, intervention, and public flush event non-null; discard null) or
   `DISCARDED` (discard non-null; provider, intervention, and flush event null).

2. **D02 does not select D1C/D1D behavioral READ cardinality or failed-slot
   progress.** This draft makes the count a prospective run-lock integer
   `behavior_read_slots >= 0`, identical across paired arms of an assay/item.
   Each D1C/D1D behavioral slot is one attempt: an error occupies and advances
   the slot, with no retry. D1B AUTHENTIC retains r3's distinct rule that its
   counter advances only after a syntactically and semantically valid READ
   request; the third error or a budget terminal bounds retries. This choice is
   provisional architecture, not an implication of the r3 words.

3. **D03 does not say whether an early missing required call remains missing
   after a later observed action.** This draft selects missing dominance at the
   affected endpoint: after integrity-blocker precedence, any missing required
   model/provider/DREAM dependency makes that endpoint `MISSING` with null raw
   value and the registered adverse analysis bound even if later work produced
   an outcome. Controls that do not consume a missing shared DREAM result are
   not marked missing. This is conservative and total, but requires r4
   adjudication.

4. **The inherited pre-claim language can recreate a hash cycle.** If
   `PRE_SCIENTIFIC_CLAIM` consumes a final claim-release receipt while the
   claim-release receipt consumes `PRE_SCIENTIFIC_CLAIM`, neither hash is
   computable. This draft splits pure `claim_decision_receipt` from final
   `claim_release_receipt`: reduction produces the former, pre-claim authority
   consumes it, and final release consumes that authority. No release receipt
   is a predecessor of its own authority.

These four choices are the only intentional additions needed to make the
specified systems closure total. Any successor that chooses differently must
change its controller/status/authority fixtures accordingly; an implementer
may not choose a default.

## 3. Canonical representation and common schema rules

### 3.1 Canonical JSON and digests

Retain r3 canonical JSON exactly: one UTF-8 JSON value, no BOM, duplicate key,
comment, prefix, suffix, NaN, or infinity; keys sorted lexicographically;
compact separators; base-ten integers; finite JSON numbers; no escaped solidus;
one trailing LF. Arrays retain their contract order. Parsing is atomic.

For every v4 object with contract string `C`, schema version integer `4`, and
self-hash field `h`, define:

```text
payload = canonical(object with h omitted)
h = SHA256(UTF8(C) || 0x00 || UTF8("4") || 0x00 || payload)
```

The contract string domain-separates object types. A validator rejects a hash
under the wrong contract even when payload bytes are identical. Raw byte blobs
use ordinary `SHA256(raw_bytes)` in their `raw_sha256`; their enclosing
manifest is domain-separated and self-hashed as above.

Every object schema has `additionalProperties:false`; every listed field is
required, including fields whose value may be null. No field is optional.
Integers are nonnegative unless stated. Arrays carry explicit ordinal fields,
are strictly increasing by ordinal from zero, and have no duplicate semantic
keys. A hash array with no role is forbidden.

### 3.2 Shared closed definitions

```text
artifact_ref := {
  role: SYMBOL,
  ordinal: integer,
  artifact_type: SYMBOL,
  sha256: HASH
}

byte_ref := {
  role: SYMBOL,
  ordinal: integer,
  media_type: SYMBOL,
  relative_path: repository-relative string,
  byte_length: integer,
  raw_sha256: HASH
}

human_evidence := {
  relative_path: repository-relative string,
  file_sha256: HASH,
  excerpt_utf8: nonempty string,
  excerpt_start_byte: integer,
  excerpt_end_byte_exclusive: integer
}
```

`artifact_ref` arrays are ordered by the exact role registry of their enclosing
schema, then ordinal. Roles not in that registry, duplicate roles, missing
roles, wrong artifact types, and extra references fail. `byte_ref` is valid
only if the path stays within the sealed bundle, the file exists, byte length
and raw hash recompute, and the role/media type is allowed by the enclosing
schema. Thus prompt, output, context, row, corpus, and artifact receipts bind
available bytes rather than unattached digests. Model/adaptor directories are
represented by a `byte_artifact_manifest` containing every regular file in
strict relative-path order; symlinks, devices, absolute paths, traversal, and
unlisted files fail.

Opaque IDs retain r3's monotone post-commit allocation and forbidden-substring
casefold check. An opaque runtime ID is per instance and is not a stable code
for an arm or condition.

## 4. Minimal closed object inventory

The following are the top-level, independently stored objects. Records named
inside parentheses are closed nested records, not additional top-level
artifacts. Removing any object would erase a distinct byte, status, execution,
or authority boundary required by D01-D12.

| Group | Top-level objects |
|---|---|
| Bytes/configuration | `byte_artifact_manifest`, `generator_manifest`, `life_sample_receipt`, `populated_run_lock`, `semantic_table`, `assay_assignment`, `overlap_manifest`, `construction_scope_receipt` |
| Path construction | `path_suite_manifest`, `path_proof` (edge, subset, full-set, path-universe, intervention-proof records) |
| Public machine | `model_view`, `private_controller_receipt`, `queue_slot_receipt`, `queue_effect_receipt`, `operation_envelope`, `operation_result`, `state_body`, `transition_event`, `state_receipt` |
| Provider/intervention | `provider_ingress`, `provider_receipt`, `descriptive_provider_ingress`, `descriptive_provider_receipt`, `intervention_route_receipt`, `resolved_response_projection`, `intervention_emission_receipt` |
| DREAM/context | `dream_input`, `dream_render`, `dream_receipt`, `context_install_receipt` |
| Evidence/SLEEP | `eligibility_receipt`, `root_selection_receipt`, `sleep_row`, `corpus_manifest`, `trainer_execution_receipt`, `adapter_validation_receipt`, `publication_receipt`, `adapter_manifest` |
| Analysis/release | `stage_outcome`, `observation`, `paired_gate_result`, `one_sample_safety_result`, `missingness_result`, `power_receipt`, `resource_receipt`, `assay_result`, `holm_result`, `dependency_map_receipt`, `claim_decision_receipt`, `claim_release_receipt` |
| Acceptance | `implementation_identity_receipt`, `implementation_independence_receipt`, `fixture_universe_manifest`, `test_coverage_receipt`, `test_result` |
| Authority | `architecture_ratification_receipt`, `conformance_receipt`, exactly two `static_seal_receipt`s, `independent_review_receipt`, `advocate_receipt`, `human_run_ratification_receipt`, `pre_model_authority_receipt`, one `dispatch_preflight_receipt` per attempted dispatch, `canary_receipt`, `runtime_integrity_receipt`, `runtime_authority_receipt`, `preclaim_authority_receipt` |

Existing r3 leaf values `operation`, `prediction`, `outcome`, `read_response`,
`candidate`, `budget`, and exact-equivalence tuple remain nested closed schema
definitions. `authority_receipt`, unlabeled `hashes`, `terminal_receipt`, and
arm-semantic `runtime_intervention`/`provider_kind`/control-row contracts are
retired. Terminal state is represented by the ordinary `state_body` plus
ordinary `transition_event` plus ordinary `state_receipt`; a second terminal
hash object is unnecessary and would invite another cycle.

## 5. Acyclic state, event, and terminal DAG (D01)

### 5.1 Exact objects

```text
state_body := {
  contract: "ppc5.state_body.v4",
  schema_version: 4,
  state_id: ID,
  state_ordinal: integer,
  phase: INITIAL | RUNNING | TERMINAL,
  public_view: model_view | null,
  private_controller_receipt_hash: HASH,
  terminal: terminal_payload | null,
  body_hash: HASH
}

terminal_payload := {
  origin: MODEL | HARNESS | CONTROLLER,
  reason: SCHEDULE_COMPLETE | PROVIDER_SEQUENCE_COMPLETE |
          SCHEDULE_INCOMPLETE | GOAL_COMPLETE | NO_VALID_ACTION |
          USER_STOP | BUDGET_EXHAUSTED | ERROR_LIMIT | RUN_INVALID,
  attempted_call_id: ID | null,
  attempted_error_code: ERROR_CODE | null,
  attempted_debits: budget,
  queue_discard_receipts: [artifact_ref role=QUEUE_DISCARD],
  endpoint_outcome_hash: HASH | null
}

transition_event := {
  contract: "ppc5.transition_event.v4",
  schema_version: 4,
  event_id: ID,
  event_ordinal: integer,
  cause: MODEL_DISPATCH | DIRECT_PROVIDER | CONTROLLER_PHASE |
         QUEUE_FLUSH | QUEUE_DISCARD | COMMITTED_ACTION |
         HARNESS_TERMINAL,
  prior_event_hash: HASH,
  pre_state_receipt_hash: HASH,
  operation_envelope_hash: HASH | null,
  operation_result_hash: HASH,
  controller_before_receipt_hash: HASH,
  controller_after_receipt_hash: HASH,
  lineage: [artifact_ref],
  debit_before: budget,
  debit_after: budget,
  post_state_body_hash: HASH,
  event_hash: HASH
}

state_receipt := {
  contract: "ppc5.state_receipt.v4",
  schema_version: 4,
  state_id: ID,
  state_ordinal: integer,
  state_body_hash: HASH,
  ledger_head: HASH,
  state_receipt_hash: HASH
}
```

`model_view` removes r3 `prior_transition_hash` and `ledger_hash`. Rendering a
model prompt takes the verified nonterminal `state_body.public_view` and adds
exactly one public `ledger_head` copied from its matching `state_receipt`.
Neither state body nor private controller contains the event that creates that
state.

Define the empty ledger head as:

```text
EMPTY_LEDGER_HEAD = SHA256(
  UTF8("ppc5.empty_ledger.v4") || 0x00 || UTF8("4") || 0x00 ||
  canonical({"contract":"ppc5.empty_ledger.v4","schema_version":4})
)
```

Genesis order is: compute initial private-controller receipt; compute initial
state body with `state_ordinal=0`; compute the initial state receipt with
`ledger_head=EMPTY_LEDGER_HEAD`. No genesis event exists. For transition `t`:

1. validate the pre-state receipt/body/controller and require
   `prior_event_hash == pre_state_receipt.ledger_head`;
2. compute the operation/result/provider/intervention receipts that precede the
   controller change and, for planning, the immutable queue-slot receipt;
3. compute the post-controller receipt (it records slot counters, not queue
   effect hashes);
4. when flushing or discarding, compute the queue-effect receipt, which may now
   bind that post-controller receipt;
5. compute the post-state body without the new event hash;
6. compute the transition event over the exact fields above;
7. compute the post-state receipt with `ledger_head=event_hash`.

The event is therefore a commitment to the post-state body, and the state
receipt is a commitment to the event; no edge points backward. Require
`event_ordinal = pre.state_ordinal`, `post.state_ordinal = pre.state_ordinal+1`,
matching `state_id`, and exactly one post receipt per event.

For a terminal transition, the same sequence applies. The terminal body has
`public_view=null`, non-null `terminal`, and a terminal private-controller
receipt in which no queued slot remains `QUEUED`. The terminal state receipt
still has `ledger_head=event_hash`. A later dispatch request returns the stored
canonical terminal `state_receipt` bytes byte-for-byte and reads its referenced
terminal body; it writes no object, increments no ordinal, and changes no
budget. `RUN_INVALID` may be the first event after genesis. Golden vectors must
cover genesis, ordinary success, each error count, direct provider, each queue
phase/flush/discard, successful terminal, integrity terminal, and cold replay.

### 5.2 Event lineage roles

The exact allowed `lineage` roles by cause are:

| cause | required roles in order | nullable/forbidden |
|---|---|---|
| `MODEL_DISPATCH` | `PROMPT_BYTES`, `OPERATION_ENVELOPE`, `OPERATION_RESULT` | queue/provider/intervention roles forbidden |
| `DIRECT_PROVIDER` | `DIRECT_REQUEST`, `PROVIDER_INGRESS`, `PROVIDER_RECEIPT`, `OPERATION_RESULT` | envelope null |
| `CONTROLLER_PHASE` | `OPERATION_RESULT` | envelope null; no external side effect |
| `QUEUE_FLUSH` | `QUEUED_SLOT`, `PROVIDER_INGRESS`, `PROVIDER_RECEIPT`, `ROUTE_RECEIPT`, `RESOLVED_PROJECTION`, `EMISSION_RECEIPT`, `QUEUE_EFFECT`, `OPERATION_RESULT` | all non-null |
| `QUEUE_DISCARD` | one `QUEUED_SLOT` and one `QUEUE_EFFECT` for each discarded slot, in slot order, then `OPERATION_RESULT` | provider/intervention roles forbidden |
| `COMMITTED_ACTION` | `COMMITTED_PREDICTION_ENVELOPE`, `COMMITTED_ACTION_ENVELOPE`, `ACTION_RESULT` | model dispatch null at execution |
| `HARNESS_TERMINAL` | `OPERATION_RESULT` plus any `QUEUE_EFFECT`s | envelope is non-null only when the terminal replaced an attempted call result |

The `operation_envelope_hash` duplicates the named envelope role only for a
model event and must match it. This deliberate local redundancy catches role
substitution.

## 6. Total controllers and queue lifecycle (D02)

### 6.1 Controller schema

```text
private_controller_receipt := {
  contract: "ppc5.private_controller.v4",
  schema_version: 4,
  assay_id: D1A | D1B | D1C | D1D,
  program: DIRECT_PROVIDER | D1B_AUTHENTIC | D1B_ONE_SHOT |
           D1B_OPEN_LOOP | FIXED_BEHAVIOR | D1D_TOTAL,
  phase: CONTROLLER_PHASE,
  required_operation: READ | PREDICT | ACT | NONE,
  slot: integer,
  slot_limit: integer,
  accepted_read_count: integer,
  queue_slots: [artifact_ref role=QUEUE_SLOT],
  next_flush_slot: integer,
  committed_prediction_envelope_hash: HASH | null,
  committed_action_envelope_hash: HASH | null,
  committed_action_id: ID | null,
  controller_hash: HASH
}
```

The run lock supplies `direct_request_count`, D1B `path_length` in `{2,3}`,
and D1C/D1D `behavior_read_slots`. Every paired arm for the same assay/item has
identical values. A controller receipt's program and phase determine every
field; no generic default program exists.

### 6.2 Program table

| assay/program | phases and exact progression | completion |
|---|---|---|
| D1A `DIRECT_PROVIDER` | `PROVIDER[i]`, `0 <= i < Q`; no model call. Execute the sealed request once and advance after FOUND, NOT_FOUND, or PROVIDER_MISSING_NO_RETRY. Integrity failure terminates. | After `Q`, one no-model phase event terminates `PROVIDER_SEQUENCE_COMPLETE`. |
| D1B `D1B_AUTHENTIC` | `READ[k]`, `0 <= k < L`; expected READ. A valid request executes provider/intervention immediately, publishes response, and increments `k`; a nonterminal error stays at `k`. Then exactly `PREDICT`, then exactly `ACT`. | Successful ACT atomically produces outcome and terminal `SCHEDULE_COMPLETE`; third error/budget/integrity terminal, or exhausted required ACT without success, produces the specified non-success terminal. |
| D1B `D1B_ONE_SHOT` | `PLAN_READ[k]`, `0 <= k < L`; each dispatch occupies and advances one slot. Accepted READ creates `QUEUED`; error creates `REJECTED`. Then no-model `FLUSH[k]` for every slot in order: queued slots execute, rejected slots emit `FLUSH_SKIPPED_REJECTED`. Then one-attempt `PREDICT`, then one-attempt `ACT`. | Successful ACT gives `SCHEDULE_COMPLETE`; otherwise a no-model finalizer gives `SCHEDULE_INCOMPLETE`. |
| D1B `D1B_OPEN_LOOP` | Same `PLAN_READ`; then one-attempt `BLIND_PREDICT`, one-attempt `BLIND_ACT`, each exposing only an ACK and storing valid envelopes privately. No more model calls. Then `FLUSH[k]` in slot order, followed by `EXECUTE_COMMIT`. | A valid matching commitment executes once and gives `SCHEDULE_COMPLETE`; absent/invalid commitment gives `SCHEDULE_INCOMPLETE` and no action. |
| D1C `FIXED_BEHAVIOR` | Context installation precedes the controller. Exactly `R=behavior_read_slots` one-attempt public `READ[k]` slots, then one-attempt `PREDICT`, then one-attempt `ACT`. Every error occupies and advances its slot. | Same success/incomplete terminal rule. |
| D1D `D1D_TOTAL` | Root/SLEEP/publication first; then `PROVIDER[i]` for the sealed selection endpoint requests using the resulting artifact or null; then the same `R`-READ/PREDICT/ACT behavior program as D1C. Training/empty statuses do not skip either endpoint. | Provider sequence and action endpoint are both sealed before final `SCHEDULE_COMPLETE` or `SCHEDULE_INCOMPLETE`; training failure continues adapter-off. |

At `R=0`, D1C/D1D begin at PREDICT; this is an explicit run-lock value, not a
fallback. A one-attempt phase always advances after an integrity-clean result,
including an error or missing result. An authentic D1B READ advances on a valid
READ request even if the provider returns NOT_FOUND or
PROVIDER_MISSING_NO_RETRY; provider missing is not a request retry.

### 6.3 First-applicable transition precedence

For every call-capable phase, apply this exact order:

1. terminal replay;
2. schema, current-state, cell, run-lock, assignment, executable, mounted-byte,
   table, and preflight verification; preassignment absence is
   `CONSTRUCTION_FAIL` with no state, while post-seal absence/mismatch is an
   immediate `RUN_INVALID` terminal event;
3. execute every pending no-model controller phase before considering a model
   call;
4. if calls remaining is zero, append `BUDGET_EXHAUSTED` terminal;
5. render once, dispatch once, debit one call and actual input/output tokens;
   token overrun yields `TOKEN_LIMIT` and the parsed operation is ignored;
6. missing output yields `MODEL_MISSING_NO_RETRY`; otherwise parse exactly one
   operation, with parse failure `PARSE_ERROR`;
7. debit READ or ACT from the emitted operation before schedule, domain,
   reference, prediction, or action validation; zero pre-debit remainder gives
   `READ_LIMIT` or `ACTION_LIMIT`;
8. compare operation type with `required_operation`; every mismatch, including
   model STOP at READ/PREDICT/ACT, is `SCHEDULE_VIOLATION`;
9. validate fields/domains, public references, ACT prediction presence and
   equality, then environment legality, returning the first of
   `INVALID_DOMAIN`, `INVALID_REFERENCE`, `PREDICTION_REQUIRED`,
   `PREDICTION_MISMATCH`, or `INVALID_ACTION`;
10. execute or queue exactly the action named by the controller row;
11. an integrity-clean error increments the consecutive count; counts one and
    two retain that error, while count three emits one terminal `ERROR_LIMIT`
    result whose `trigger_error_code` records the replaced error. A successful
    expected operation, accepted queue entry, or successful no-model flush
    resets the count to zero. Missing is recorded separately and participates
    in the error rule only when the corresponding r4 transition table says the
    call itself failed; it never retries the missing external call.

`INVALID_CELL` is retired as an analyzable public response. A malformed table,
nonfinite score, illegal provider output, or cell mismatch is
`CONSTRUCTION_FAIL` before assignment and `RUN_INVALID` after seal. A provider
process that does not return produces the single vocabulary value
`PROVIDER_MISSING_NO_RETRY` in provider, public READ, operation, stage, and
analysis objects.

### 6.4 Queue lifecycle

```text
queue_slot_receipt := {
  contract: "ppc5.queue_slot.v4", schema_version: 4,
  slot: integer,
  state: QUEUED | REJECTED,
  controller_before_hash: HASH,
  operation_envelope_hash: HASH,
  request_hash: HASH | null,
  rejection_error: ERROR_CODE | null,
  slot_hash: HASH
}

queue_effect_receipt := {
  contract: "ppc5.queue_effect.v4", schema_version: 4,
  slot: integer,
  queued_slot_hash: HASH,
  effect: FLUSHED | DISCARDED,
  provider_receipt_hash: HASH | null,
  intervention_receipt_hash: HASH | null,
  public_result_hash: HASH | null,
  discard_reason: TERMINAL_REASON | null,
  controller_after_hash: HASH,
  effect_hash: HASH
}
```

For `QUEUED`, request is non-null and rejection error is null. For `REJECTED`,
request is non-null only when a parsed READ failed after request formation;
rejection error is non-null. Only `QUEUED` may have an effect. `FLUSHED`
requires provider, intervention, and public result; discard reason is null.
`DISCARDED` requires discard reason; provider, intervention, and public result
are null. Each queued slot occurs in exactly one effect receipt, proven by the
terminal controller and run-wide queue coverage manifest. The transition event
binds controller-before, slot, effect, controller-after, and (for FLUSHED) the
public flush event lineage. This orientation is acyclic.

No-model flush uses one transition event per planned slot. A rejected slot's
`FLUSH_SKIPPED_REJECTED` result carries only slot and prior ACK status; it does
not reveal private request bytes. On any terminal before all flushes, a single
queue-discard event carries one `DISCARDED` effect per remaining queued slot in
slot order. Empty discard lists are canonical empty arrays, never null.

## 7. Total status-to-observation mapping (D03)

### 7.1 Aggregate schema

```text
stage_outcome := {
  contract: "ppc5.stage_outcome.v4", schema_version: 4,
  recipient_life_id: ID,
  assay_id: D1A | D1B | D1C | D1D,
  arm_id: SYMBOL,
  endpoint_id: CORRECT_SUPPORTED_SELECTION | FALSE_SELECTION |
               NOT_FOUND | NORMALIZED_ACTION_VALUE,
  terminal_class: OBSERVED | NO_ACTION | MISSING | BLOCKED,
  raw_result_code: SYMBOL,
  cause_event_refs: [artifact_ref role=CAUSE_EVENT],
  installed_artifact_hash: HASH | null,
  installed_context_hash: HASH | null,
  continued: boolean,
  missing: boolean,
  claim_blocker: boolean,
  raw_value: number[0,1] | null,
  analysis_value: number[0,1] | null,
  status_hash: HASH
}
```

`observation` repeats the identity, endpoint, raw/analysis value, and missing
flag and binds exactly one `stage_outcome`. `BLOCKED` produces no observation;
every other terminal class produces exactly one. An assignment/endpoint
coverage receipt proves the exclusive `one observation XOR one blocker`
condition.

### 7.2 Deterministic precedence and values

Apply these rows first-to-last for each assigned endpoint:

| condition | terminal class | continued | missing | blocker | raw / analysis |
|---|---|---:|---:|---:|---|
| Preassignment required artifact absent, no path/twin/sham/donor/dose match, or fixture construction fails | `BLOCKED:CONSTRUCTION_FAIL` | false | false | true | null / null |
| Any post-seal hash, schema, lineage, parity, visibility, score-finiteness, cell, duplicate-event, or replay failure | `BLOCKED:RUN_INVALID` | false | false | true | null / null |
| A required DREAM call is missing for `AUTHENTIC_DREAM_CONTEXT` or `DREAM_TO_SLEEP` | `MISSING:DREAM_MISSING_NO_RETRY` | true where mechanically possible | true | false | null / registered adverse bound |
| A required THINK/ACT model call is missing | `MISSING:MODEL_MISSING_NO_RETRY` | controller-defined, no retry of that call | true | false | null / registered adverse bound |
| A required provider call is missing | `MISSING:PROVIDER_MISSING_NO_RETRY` | controller-defined, no retry of that call | true | false | null / registered adverse bound |
| D1A/D1D provider FOUND the supported member | `OBSERVED:FOUND_SUPPORTED` | true | false | false | selection=1, false=0, not-found=0; analysis identical |
| Provider FOUND another valid table member | `OBSERVED:FOUND_FALSE` | true | false | false | selection=0, false=1, not-found=0; analysis identical |
| Provider NOT_FOUND | `OBSERVED:NOT_FOUND` | true | false | false | selection=0, false=0, not-found=1; analysis identical |
| ACT executed with valid outcome | `OBSERVED:ACTION` | false after completion | false | false | normalized outcome / identical |
| No ACT outcome and no higher-precedence missing/blocker | `NO_ACTION:<final cause>` | false | false | false | normalized action=0 / 0 |

The allowed `<final cause>` values exhaust `GOAL_COMPLETE`,
`NO_VALID_ACTION`, `USER_STOP`, `BUDGET_EXHAUSTED`, `ERROR_LIMIT`,
`TOKEN_LIMIT`, `PARSE_ERROR`, `READ_LIMIT`, `ACTION_LIMIT`,
`INVALID_DOMAIN`, `INVALID_REFERENCE`, `PREDICTION_REQUIRED`,
`PREDICTION_MISMATCH`, `INVALID_ACTION`, `SCHEDULE_VIOLATION`,
`COMMITMENT_ABSENT`, `COMMITMENT_INVALID`, and `SCHEDULE_INCOMPLETE`.
When several occur, `<final cause>` is the last event's result code; the full
ordered cause list remains bound. Model STOP at a required slot appears as
`SCHEDULE_VIOLATION`, with the attempted STOP reason retained in the operation
envelope.

Policy-stage outcomes do not preempt an eventual endpoint value:

- `PUBLISH_EMPTY`, `ABSTAIN`, and `DREAM_INVALID_OUTPUT` install no authentic
  context/roots and continue; they are nonmissing assigned-policy facts.
- `NO_ROOTS_SELECTED` means the root policy emitted zero nominees.
- `NO_ADMITTED_ROOTS` means it emitted at least one nominee and all were
  rejected by the nominee-first gate.
- mixed rejected/admitted nominees yield `VALID_ROOTS`, never
  `PROJECTION_REJECTED` as an aggregate.
- an admitted root whose deterministic row cannot render is `RUN_INVALID`.
- zero roots yield a valid empty corpus and adapter-off continuation.
- `TRAIN_FAILED` publishes no artifact, continues adapter-off, is nonmissing,
  and retains actual resource dose.
- an adapter required for assignment is verified before assignment; absence is
  `CONSTRUCTION_FAIL`, disappearance/mismatch is `RUN_INVALID`, and
  `adapter_manifest.status=MISSING` is retired.

Missing dominance is endpoint-local. A shared DREAM missing event marks only
arms whose policy consumes DREAM output; RECENCY/PERMUTED controls continue
with observed outcomes. A provider missing during D1D selection need not mark
its separate action endpoint missing unless that action program required the
same provider result. The paired exceedance indicator is zero whenever either
required arm endpoint is missing. Missingness receipts count every affected
life in the prospectively registered denominator.

## 8. Closed edge-indexed path proof (D07)

### 8.1 Proof schema

```text
path_proof := {
  contract: "ppc5.path_proof.v4", schema_version: 4,
  item_id: ID,
  path_length: 2 | 3,
  read_budget: integer,
  alias_source_hash: HASH,
  alias_map_hash: HASH,
  world_variant_table_hash: HASH,
  registered_action_id: ID,
  graph_bytes: byte_ref(role=CANONICAL_MULTIGRAPH),
  graph_hash: HASH,
  path_universe: [path_member],
  selected_path_id: ID,
  edge_proofs: [edge_proof],
  proper_subset_proofs: [subset_proof],
  full_set_proof: full_set_proof,
  proof_hash: HASH
}

path_member := {
  ordinal: integer, path_id: ID, ordered_edge_ids: [ID],
  oracle_input_hash: HASH, oracle_output_hash: HASH,
  sufficient: boolean, unique_action_id: ID | null
}

edge_proof := {
  position: integer, edge_id: ID, source_event_id: ID,
  source_event_receipt_hash: HASH, source_preimage_hash: HASH,
  authentic_response: byte_ref, cut: intervention_proof,
  twin: intervention_proof, sham: intervention_proof
}

intervention_proof := {
  kind: CUT | TWIN | SHAM, intervention_id: ID,
  replacement_response: byte_ref,
  candidate_universe_hash: HASH,
  selected_candidate_ordinal: integer,
  schema_equal: boolean, debit_equal: boolean, allowance_equal: boolean,
  token_count_equal: boolean, byte_length_class_equal: boolean,
  action_effect: REMOVES_OBSERVATION | REVERSES_ACTION | PRESERVES_ACTION,
  oracle_input_hash: HASH, oracle_output_hash: HASH,
  proof_hash: HASH
}

subset_proof := {
  ordinal: integer, mask: integer, included_positions: [integer],
  observation_set_hash: HASH, oracle_input_hash: HASH,
  oracle_output_hash: HASH, sufficient: false
}

full_set_proof := {
  mask: integer, observation_set_hash: HASH,
  oracle_input_hash: HASH, oracle_output_hash: HASH,
  sufficient: true, unique_action_id: ID
}
```

The canonical multigraph lists vertices and directed multiedges in
lexicographic `(source_symbol, relation_symbol, destination_symbol, edge_id)`
order. Enumerate every simple path of lengths `1..read_budget` in
lexicographic edge-ID-sequence order. `path_universe` has exactly that
cardinality; the selected path is its only member with `sufficient=true`, and
its unique action equals the registered action. No count-only alternate-path
claim is accepted.

For length `L`, `edge_proofs` has exactly `L` entries with position `0..L-1`
and edge IDs equal to the selected path. Source event IDs are pairwise distinct
within the proof. `path_suite_manifest` lists every selected item/proof in
item-ID order and rejects any source event ID repeated across items.

`proper_subset_proofs` has exactly `2^L-2` entries. Entry ordinal `j` has
`mask=j+1`; included positions are the set bits in increasing position order;
every entry is insufficient. `full_set_proof.mask=2^L-1` and is sufficient for
exactly the registered action.

Each edge has exactly one CUT, TWIN, and SHAM. TWIN is the lexicographically
first finite candidate that reverses the action and matches schema, debit,
allowance, locked token count, and byte-length class. SHAM is the
lexicographically first response not on the selected path that preserves one
unique action and matches the same parity tuple. CUT is canonical NOT_FOUND,
has the same debit and allowance, and is not falsely required to have FOUND's
token count/byte class. Zero or multiple admissible selections after the named
lexicographic rule is construction failure. Each edge produces distinct
edge-indexed CUT/TWIN/SHAM assay arms and gate IDs; every CUT/TWIN superiority
and every `SHAM_edge - AUTHENTIC` noninferiority gate must pass separately.

## 9. Condition-free restricted projections (D09)

Treatment identity is allowed only in sealed assignment, privileged routing,
audit, and reduction. The following are the exact restricted-stage ingresses:

| stage | allowed ingress fields | explicitly absent |
|---|---|---|
| THINK/ACT | verified public model-view bytes, operation-schema bytes, legal-action catalogue, current ledger head | arm, condition, item target/truth, provider type, intervention ID, eligibility, future/probe, score/provenance |
| READ_PROVIDER causal cell | canonical request bytes, complete semantic-table bytes, constant algorithm `MEAN_RESPONSE_LOGPROB_V4`, opaque mounted-byte handle or null, scoring-kernel bytes | READER/WRONG_LIFE/SHUFFLE/ADAPTER_OFF names, arm, donor/recipient role, target, condition |
| READ_PROVIDER descriptive cell | `descriptive_provider_ingress` with exact one of `RAW_RAG_V4`, `FULL_CONTEXT_V4`, `EXPLICIT_GRAPH_V4`, its public source bytes, and opaque artifact handle | causal-arm names and hidden assignment; FULL_CONTEXT is represented, never implicit |
| RESPONSE_INTERVENTION | one `resolved_response_projection` | kind, condition, arm, item, target, truth, role, query hash, selected-response hash, source table, score |
| DREAM | one arm-neutral `dream_render`, model/tokenizer handles, seed, debit allowance | context/root-policy arm, eligibility, future, target/truth |
| EVIDENCE_GATE | ordered nominee record bytes and eligibility predicate bytes | policy/arm label; privileged root-policy selector has already chosen nominee order |
| WRITER | admitted root projections in order | policy/arm/control-row label, cognition, target, eligibility predicates |
| TRAINER | one row contract, ordered row bytes, recipe bytes, clean-base bytes, seed bundle | authentic/shuffled/control labels, provenance, arm, policy target |

The privileged router writes:

```text
intervention_route_receipt := {
  contract: "ppc5.intervention_route.v4", schema_version: 4,
  route_instance_id: ID,
  assignment_hash: HASH,
  item_id: ID,
  edge_position: integer,
  condition: AUTHENTIC | CUT | TWIN | SHAM,
  query_hash: HASH,
  selected_response_hash: HASH,
  expected_match_count: 1,
  actual_match_count: integer,
  resolved_response: byte_ref,
  shared_parity_class_id: ID,
  projection_hash: HASH,
  route_hash: HASH
}

resolved_response_projection := {
  contract: "ppc5.resolved_response.v4", schema_version: 4,
  instance_id: ID,
  resolved_response: read_response,
  resolved_response_bytes: byte_ref,
  parity_commitment_id: ID,
  opaque_lineage_receipt_hash: HASH,
  projection_hash: HASH
}
```

The projection omits all condition-semantic and low-entropy match fields. The
`parity_commitment_id` is a high-entropy opaque ID allocated once per
item/edge parity set and is byte-identical across AUTHENTIC/CUT/TWIN/SHAM; it
does not encode token or byte counts and RESPONSE_INTERVENTION does not branch
on it. The restricted stage validates the projection and emits the resolved
bytes exactly. Its emission receipt binds input projection and output bytes,
but contains no treatment kind. Non-target traffic is resolved to its original
bytes by the router; the privileged route receipt records the no-op. Any
expected match count other than one is immediate `RUN_INVALID` and produces no
restricted projection.

`provider_receipt` replaces `provider_kind` with constant
`algorithm=MEAN_RESPONSE_LOGPROB_V4` and an opaque nullable mount handle.
Provider scores remain private. `sleep_row.contract` is only
`ppc5.sleep_row.v4`; authentic and shuffled role maps exist solely in a
privileged corpus-routing manifest. FULL_CONTEXT is retained through the
separate arm-neutral descriptive schema and must fail construction, rather
than truncate, on render overflow.

For every one of the 154 visibility cells, the successor schema registry names
one ingress and one egress projection. Field mutation holds all allowed
projection bytes fixed. Hidden/forbidden mutations must preserve ingress,
egress, scores, selections, operations, debits, errors, statuses, timing class,
token accounting, and public bytes. A derived-only mutation may change only
its named projection. Low-entropy matcher hashes are never in public/model
bytes.

## 10. Complete byte-bearing receipt DAG (D10)

### 10.1 DREAM and context

```text
dream_input := {
  contract: "ppc5.dream_input.v4", schema_version: 4,
  shared_call_id: ID, snapshot_state_receipt_hash: HASH,
  public_slice_bytes: byte_ref, world_state_bytes: byte_ref,
  live_prediction_bytes: byte_ref | null,
  allowed_record_ids: [ID], allowed_record_bytes: [byte_ref],
  capacity_records: integer, render_token_ceiling: integer,
  input_hash: HASH
}

dream_render := {
  contract: "ppc5.dream_render.v4", schema_version: 4,
  dream_input_hash: HASH, chat_template_hash: HASH,
  tokenizer_hash: HASH, prompt_bytes: byte_ref,
  prompt_token_ids_bytes: byte_ref, input_token_count: integer,
  render_hash: HASH
}

dream_receipt := {
  contract: "ppc5.dream_receipt.v4", schema_version: 4,
  shared_call_id: ID, dream_input_hash: HASH, dream_render_hash: HASH,
  preflight_hash: HASH, model_hash: HASH, tokenizer_hash: HASH,
  seed: integer, debit_before: budget, debit_after: budget,
  status: VALID | PUBLISH_EMPTY | ABSTAIN |
          DREAM_INVALID_OUTPUT | DREAM_MISSING_NO_RETRY,
  raw_output_bytes: byte_ref | null,
  parsed_result: dream_result | null,
  shared_resource_receipt_hash: HASH,
  receipt_hash: HASH
}
```

One DREAM receipt is shared physically and referenced by every paired policy
clone. Invalid output retains exact raw bytes privately; missing output has no
raw bytes. `context_install_receipt` binds the DREAM receipt, the source record
receipts, exact ordered IDs/focus, exact rendered context bytes, token IDs and
count, and status. Control context computation binds the same snapshot and
allowed-record universe even though it does not consume DREAM result bytes.

### 10.2 Root, corpus, training, and publication

```text
root_selection_receipt := {
  contract: "ppc5.root_selection.v4", schema_version: 4,
  recipient_life_id: ID, assay_id: D1A | D1D,
  privileged_policy_id: SYMBOL,
  policy_source_hash: HASH,
  nominee_record_ids: [ID],
  projection_refs: [artifact_ref role=NOMINEE_PROJECTION],
  eligible_representatives_before_capacity: [ID],
  capacity: integer,
  selected_representative_ids: [ID],
  status: VALID_ROOTS | NO_ROOTS_SELECTED | NO_ADMITTED_ROOTS |
          CONSTRUCTION_FAIL | RUN_INVALID,
  receipt_hash: HASH
}

corpus_manifest := {
  contract: "ppc5.corpus_manifest.v4", schema_version: 4,
  root_selection_hash: HASH,
  row_refs: [artifact_ref role=SLEEP_ROW],
  corpus_bytes: byte_ref,
  row_count: integer, token_count: integer, update_count: integer,
  status: VALID | VALID_EMPTY | RUN_INVALID,
  corpus_hash: HASH
}
```

There is one `eligibility_receipt` per nominee in nominee order. It carries the
complete predicate values, first failure, exact-equivalence tuple bytes/hash,
and nullable representative ID. Rejection happens before equivalence lookup.
The aggregate root receipt proves projection cardinality equals nominee
cardinality, recomputes first-failure order, exact dedup, policy order, and one
capacity application. D1A omits DREAM visibility from the predicate; D1D does
not. Mixed rejection/admission is valid. Construction-only family fields stay
in eligibility/overlap audit and never enter row equivalence or claims.

Each `sleep_row` binds exact request bytes, target-response bytes, combined
training-render bytes, locked token-ID bytes, root source hash, token count,
and byte class. Writer output order equals selected root order. `corpus_bytes`
is the canonical concatenation manifest of those exact row blobs; empty is a
real canonical empty blob.

`trainer_execution_receipt` binds corpus, recipe bytes, clean-base artifact
manifest, seed bundle, preflight, executable, start/end resource receipts,
process exit status, raw trainer output/log bytes, and nullable produced
artifact manifest. `adapter_validation_receipt` binds expected/actual schemas,
every file/tensor shape and finiteness result, base/tokenizer/recipe/mount
hashes, and the locked no-model structural check. `publication_receipt` binds
the pre-publication target state, temporary artifact, atomic rename operation,
post-publication directory manifest, and status. `adapter_manifest` is
self-hashed and binds all three receipts.

The status chain is exact:

| corpus/trainer/validation | publication | adapter manifest |
|---|---|---|
| `VALID_EMPTY` | `NOT_ATTEMPTED_EMPTY`, no artifact | `VALID_EMPTY`, artifact null, row/token/update/artifact-byte counts zero; declared run-lock rank retained |
| trainer or validation failure | `NOT_ATTEMPTED_FAILED`, no artifact | `TRAIN_FAILED`, artifact null, actual dose retained |
| trainer+validation valid | `PUBLISHED`, one post-rename artifact | `VALID`, artifact non-null, row count > 0, finite and structural true |
| any hash/schema/atomicity mismatch | `RUN_INVALID` | `RUN_INVALID`; dependent claim blocked |

No `MISSING` adapter-manifest status is allowed after assignment.

### 10.3 Analysis and release DAG

```text
raw events/statuses -> stage_outcome -> observation
observations -> paired_gate_result / one_sample_safety_result / missingness_result
gate results -> assay_result -> holm_result
all of the above + resources + T01..T14 + overlap + scope
  -> dependency_map_receipt -> claim_decision_receipt
claim_decision_receipt + preclaim_authority_receipt
  -> claim_release_receipt
```

Every gate result uses the D04-D06 successor statistic selected by the r3
consensus: direct paired exceedance indicators and exact upper-tail binomial,
or the separate D1A one-sample lower-tail safety result. `power_receipt` binds
the identical gate registry, `N`, `pi0`/ceiling, critical count, tail, equality
rule, margin, missing rule, worst-case probabilities, each exact gate power,
and the union lower bound. It contains no independent alternative statistic.

`dependency_map_receipt` has exact role registries rather than hash arrays:
T01-T14 once each in test-ID order; all registered gates in gate-registry
order; D1A-D1D assay results once each; Holm once; every assigned endpoint
coverage receipt; all resource receipts; current authority, overlap, and
construction-scope receipts. A component decision includes only its local
assay plus all globals; the intersection includes all four. Extra, missing,
duplicate, stale, or wrong-role refs fail.

`claim_decision_receipt` contains `decision=ELIGIBLE|BLOCKED`, nullable exact
registered text, nullable first blocker, fixed qualifications, and forbidden
claims. It does not contain authority. `claim_release_receipt` contains the
decision hash and preclaim-authority hash; RELEASED requires eligible decision
and passing current authority, while BLOCKED requires null release text and the
derived blocker. Every release/export also binds `overlap_manifest_hash` and
`construction_scope_receipt_hash` as required by D13.

## 11. Status-dependent nullability

All fields exist. The following table is exhaustive for nullable payloads; any
nullable field not listed here is a schema error.

| object/status | required non-null | required null/empty |
|---|---|---|
| nonterminal `state_body` | public view | terminal |
| terminal `state_body` | terminal | public view; controller has no QUEUED slots |
| `operation_envelope:PARSED` | raw output bytes/hash, operation | none |
| `operation_envelope:PARSE_ERROR` | raw output bytes/hash | operation |
| `operation_envelope:MODEL_MISSING_NO_RETRY` | none | raw output bytes/hash, operation |
| `operation_result:READ_SUCCESS` | read response | outcome, error, stop, ACK |
| `operation_result:PREDICT_SUCCESS` | none beyond identity/hash | all payloads |
| `operation_result:ACT_SUCCESS` | outcome | read, error, stop, ACK |
| `operation_result:ERROR` | error code | read, outcome, stop, ACK; `trigger_error_code` null |
| `operation_result:ERROR_LIMIT` | stop=`ERROR_LIMIT`, trigger error | read, outcome, ACK |
| `operation_result:TERMINAL` | stop reason | read, outcome, error, ACK except attempted error carried separately |
| `operation_result:SLOT_ACK/COMMIT_ACK` | ACK | read, outcome, stop; error non-null iff ACK rejected |
| queue `QUEUED` | request | rejection error |
| queue `REJECTED` | rejection error | request null only if no READ request was formable |
| effect `FLUSHED` | provider, intervention, public result | discard reason |
| effect `DISCARDED` | discard reason | provider, intervention, public result |
| provider `FOUND` | selected candidate, score vector, FOUND response | none |
| provider `NOT_FOUND` | NOT_FOUND response | selected candidate; score vector is empty only for an empty valid table |
| provider `PROVIDER_MISSING_NO_RETRY` | missing response | selected candidate, scores |
| provider integrity failure | no provider receipt is emitted | transition is RUN_INVALID |
| route valid | resolved bytes/projection, match count exactly one | none |
| route mismatch | no restricted projection | route status RUN_INVALID |
| DREAM `VALID` | nonempty PUBLISH, raw bytes | none |
| DREAM `PUBLISH_EMPTY` | empty PUBLISH, raw bytes | focus |
| DREAM `ABSTAIN` | ABSTAIN result, raw bytes | publish payload |
| DREAM `DREAM_INVALID_OUTPUT` | raw bytes | parsed result |
| DREAM `DREAM_MISSING_NO_RETRY` | none | raw bytes, parsed result |
| context `VALID` | nonempty IDs, render bytes, installed=true | focus may be null only if policy definition permits |
| context `VALID_EMPTY` | canonical empty render, installed=true | IDs empty, focus null |
| context ABSTAIN/INVALID/MISSING | installed=false | IDs empty, focus/render null |
| root `VALID_ROOTS` | nominees, at least one selected representative | none |
| root `NO_ROOTS_SELECTED` | none | nominees, projections, representatives, selected all empty |
| root `NO_ADMITTED_ROOTS` | nominees/projections | representatives and selected empty |
| root BLOCKED | blocker evidence | selected empty |
| corpus `VALID` | rows and corpus bytes; row count > 0 | none |
| corpus `VALID_EMPTY` | canonical empty corpus bytes | rows empty; counts zero |
| trainer `SUCCEEDED` | output artifact, logs, exit code zero | failure reason |
| trainer `SKIPPED_EMPTY` | empty corpus | process/output artifact/failure reason |
| trainer `FAILED` | failure reason and any available logs | output artifact |
| validation `VALID` | artifact and complete checks | failure reason |
| validation `VALID_EMPTY` | empty corpus | artifact, failure reason |
| validation `TRAIN_FAILED` | failure evidence | valid artifact |
| publication `PUBLISHED` | temp and final manifests, atomic transition | failure reason |
| publication not attempted | reason EMPTY or FAILED | temp/final manifests |
| adapter `VALID` | artifact hash/manifest; positive dose; finite/structural true | failure reason |
| adapter `VALID_EMPTY` | no artifact; all dose/size zero | artifact/failure reason |
| adapter `TRAIN_FAILED` | failure receipt, actual dose | artifact |
| adapter `RUN_INVALID` | blocker receipt | artifact is not mountable |
| stage `OBSERVED` | raw and analysis values equal | blocker |
| stage `NO_ACTION` | raw=analysis=0 | installed payload may reflect policy; blocker null |
| stage `MISSING` | adverse analysis value | raw value, blocker |
| stage `BLOCKED` | blocker | raw and analysis values; no observation |
| assay unblocked | assay p-value and complete gate refs | blocker |
| assay blocked | blocker | assay p-value |
| claim decision ELIGIBLE | exact text, no blocker | blocker |
| claim decision BLOCKED | first blocker | release text |
| final claim RELEASED | exact text, passing authority | blocker |
| final claim BLOCKED | blocker | release text |
| fixture ENUMERATED | explicit cases and expected outputs | completeness proof optional and null by default |
| fixture GENERATED_PROVEN_COMPLETE | generator and completeness proof | explicit cases still materialized; none omitted |
| coverage PASS | zero missing/extra/duplicate/mismatch counts | failure ref |
| coverage FAIL | nonzero derived count and failure refs | pass assertion is absent |
| authority PASS | all exact subjects, predecessor as stage requires | denial reason |
| authority FAIL | first denial reason | reachable=false except no failed receipt is accepted as predecessor |
| preflight PERMIT | recomputed current pre-model authority | denial reason |
| preflight DENY | first denial reason | process ID, child-process receipt, model/trainer output |

Human decision objects always require `human_evidence`; nonhuman authority
objects require it to be null. Architecture stage predecessor is null; every
later authority predecessor is non-null. Reachability is always false for
architecture ratification and conformance, and is derived true only for a
passing pre-model/runtime/preclaim receipt.

## 12. Exact cross-field validators

The successor `semantic_validators` must expose pure functions with these
postconditions. Each returns one typed success or one failure code and never
coerces or fills a default.

1. `validate_canonical_object` rejects unknown/missing fields, wrong contract,
   wrong ordering, noncanonical bytes, nonfinite numbers, invalid opaque IDs,
   stale self hash, and unavailable/mismatched byte refs.
2. `validate_state_dag` reconstructs genesis or the six-step transition order,
   validates ordinals and both controller hashes, proves
   `prior_event_hash=pre.ledger_head`, proves
   `post.ledger_head=event_hash`, and verifies terminal replay performs zero
   writes/debits.
3. `validate_controller` looks up the exact assay/program/phase row; validates
   slot bounds, required operation, queue cardinality, public opacity,
   one-attempt versus accepted-read progression, and success/incomplete
   terminal reason. No unlisted tuple is accepted.
4. `validate_queue_coverage` proves each planned slot has exactly one
   QUEUED/REJECTED receipt and each QUEUED slot has exactly one exclusive
   FLUSHED/DISCARDED successor; it recomputes every event lineage.
5. `validate_debits` recomputes call, actual token, READ, and ACT debits in the
   stated precedence and proves no no-model phase debits a call/token/read/action.
6. `validate_provider` recomputes complete-table membership, fixed scoring,
   quantization, ties, common response, opaque mount, and missing vocabulary;
   it rejects every arm-semantic provider field. `validate_descriptive_provider`
   separately closes RAW_RAG, FULL_CONTEXT, and EXPLICIT_GRAPH.
7. `validate_path_proof` rebuilds alias map, graph, complete path universe,
   every subset/full-set oracle result, edge/source mapping, lexicographic
   TWIN/SHAM selection, parity, and per-edge intervention cardinality.
   `validate_path_suite` enforces cross-item source-event disjointness.
8. `validate_route` performs expected matching and condition resolution only
   in the privileged object; `validate_resolved_projection` field-whitelists
   the restricted object and proves the emitter copied exact bytes without
   branching. Projection and public bytes must be invariant to arm-label
   mutations that hold resolved bytes fixed.
9. `validate_dream` recomputes public-slice eligibility, render/chat template,
   token IDs/count, debit, raw parse, status, shared physical event, and
   no-retry cardinality. `validate_context_install` recomputes each policy and
   exact rendered bytes.
10. `validate_evidence` recomputes the exact first-failure order and performs
    equivalence lookup only after no failure. `validate_root_selection`
    recomputes nominee universe, one projection per nominee, dedup, order,
    capacity once, and aggregate status.
11. `validate_corpus` reconstructs every row and exact ordered corpus bytes.
    `validate_trainer`, `validate_adapter`, and `validate_publication` recompute
    no-retry execution, shape/finiteness/base/tokenizer/recipe checks, and
    exactly-one atomic publication transition.
12. `validate_stage_outcome` applies blocker, missing, observed, and no-action
    precedence; `validate_assignment_endpoint_coverage` proves every assigned
    endpoint has exactly one observation XOR blocker. It rejects an analyzable
    missing adapter.
13. `validate_gate`, `validate_safety`, `validate_missingness`,
    `validate_power`, `validate_assay`, and `validate_holm` recompute the exact
    D04-D06 algorithms, gate registry, edge indices, equality rules, and
    cardinalities from observations. Free p-values, booleans, or alternative
    statistics fail.
14. `validate_dependency_map` proves every and only current T01-T14, gate,
    assay, endpoint, resource, authority, overlap, scope, and claim predecessor
    occurs in its registered role. `validate_claim_decision` applies blocker
    precedence and literal strings; `validate_claim_release` additionally
    requires current passing preclaim authority and fixed qualifications.
15. `validate_fixture_manifest` recomputes the finite universe or ratified
    generator/completeness proof, expected bytes, negative mutations, role
    registry, and case count. `validate_test_result` derives status solely from
    the coverage receipt.
16. `validate_authority_stage` dispatches to a stage-specific schema and
    recursively revalidates source artifacts. It never trusts `passed` or
    `reachable` from the object under test. `validate_preflight` applies the
    exact first-failure order in section 14 and proves DENY spawned no process.

Two separately source-hashed validators must agree on every fixture. Agreement
means equal canonical output bytes or equal typed failure code for every case,
not merely equal booleans.

## 13. Executable T01-T14 fixture and coverage manifests (D12)

### 13.1 Schemas

```text
fixture_universe_manifest := {
  contract: "ppc5.fixture_universe.v4", schema_version: 4,
  test_id: exactly PPC5R3_T01 .. PPC5R3_T14,
  declared_stage: AUTHORITY_STAGE,
  generator_name: SYMBOL, generator_version: nonempty string,
  generator_source_hash: HASH,
  coverage_mode: ENUMERATED | GENERATED_PROVEN_COMPLETE,
  coverage_axes: [closed axis{name, ordered values}],
  expected_case_count: integer,
  cases: [case{ordinal, case_id, inputs:[artifact_ref],
               expected_output:artifact_ref, expected_failure_code:SYMBOL|null}],
  negative_mutations: [mutation{ordinal, mutation_id, case_id, field_path,
                      before_hash, after_hash, expected_failure_code,
                      allowed_changed_roles}],
  prerequisite_refs: [artifact_ref],
  evidence_role_registry: [SYMBOL],
  reduction_algorithm_hash: HASH,
  completeness_proof: byte_ref | null,
  manifest_hash: HASH
}

test_coverage_receipt := {
  contract: "ppc5.test_coverage.v4", schema_version: 4,
  test_id: SYMBOL, fixture_manifest_hash: HASH,
  implementation_refs: [artifact_ref role=IMPLEMENTATION],
  case_results: [case_result{ordinal, case_id, expected_hash,
                             actual_hash, expected_failure, actual_failure}],
  mutation_results: [mutation_result],
  expected_count: integer, executed_count: integer,
  missing_count: integer, extra_count: integer, duplicate_count: integer,
  mismatch_count: integer, independence_receipt_hash: HASH | null,
  status: PASS | FAIL,
  coverage_hash: HASH
}

test_result := {
  contract: "ppc5.test_result.v4", schema_version: 4,
  test_id: SYMBOL, declared_stage: AUTHORITY_STAGE,
  fixture_manifest_hash: HASH, coverage_receipt_hash: HASH,
  evidence_refs: [artifact_ref], status: PASS | FAIL,
  result_hash: HASH
}
```

`status=PASS` is derived iff executed equals expected, all four defect counts
are zero, every negative mutation returns its expected failure, evidence roles
are exact, and any required independence receipt validates. There is no
`passed` input Boolean. Every generated case is materialized in the manifest,
so `expected_case_count=len(cases)` is independently checkable; the
completeness proof shows that the materialized list equals the declared finite
cross-product/branch abstraction.

`implementation_identity_receipt` binds implementation ID, repository-relative
source files, transitive source hashes, language/runtime, build recipe and
executable hash. For agreement tests, exactly two identities are required;
their implementation IDs, executable hashes, and root algorithm source hashes
must differ. `implementation_independence_receipt` records this evidence and
shared dependencies. It is procedural evidence, not a claim of statistically
independent errors; shared canonicalization/schema libraries are disclosed.

### 13.2 Per-test exact coverage rules

| test | declared stage | finite universe / completeness obligation | implementation cardinality |
|---|---|---|---:|
| T01 | PRE_RATIFICATION_SPECIFICATION | Every normative successor file/ref; every intake phase edge; missing/stale/extra/reordered role; rework/defer/reject/unresolved/removed-test cases; exact scope and human-evidence mutations. | 2 validators |
| T02 | POST_RATIFICATION_PRE_STATIC_SEAL_CONFORMANCE | Each first-failure predicate as the first failing predicate; no failure; mixed nominees; equivalence group sizes 1/2; all policy orders; capacity boundary; zero nominees; all rejected; PROBE/future/target quarantine; every overlap stratum. | 2 validators |
| T03 | same | Reachable-state BFS over every controller row, L=2/3, R boundary classes 0/1/positive, every operation/parse/token/logical/domain/reference/prediction/action/provider result, error count 0/1/2, queue ending, genesis/ordinary/terminal/cold replay. Branch registry coverage must be exactly once or explicitly multi-case by axis. | 2 machine implementations |
| T04 | same | Five DREAM statuses crossed with exact input/render/raw/debit branches; three context policies; three root policies; shared-call cardinality one; render/token/capacity boundaries; stale/missing byte refs. | 2 validators |
| T05 | same | Empty/single/multiple/duplicate/unsorted/cross-invalid tables; score finite/nonfinite, quantization half-even boundaries and ties; FOUND/NOT_FOUND/provider missing; mount null/non-null; RAW_RAG zero/threshold/tie; FULL_CONTEXT fit/overflow; graph exact/reverse/partial. | 2 provider implementations |
| T06 | same | Every forbidden mount location; valid/invalid artifact manifests; recipient-disjoint donor graph with unique/no perfect matching; every D08 dose/opportunity field equal/mismatch; derangement existence/failure and each invariant mutation; common row/provider schema leakage mutations. | 2 validators/sealers |
| T07 | same | L=2 and 3; all `2^L-2` subset masks; full set; zero/one/multiple sufficient alternate paths; within/across-item source collision; every edge CUT/TWIN/SHAM; zero/one/multiple candidate selection; every parity and oracle mutation. | 2 path constructors |
| T08 | same | AUTHENTIC plus each edge CUT/TWIN/SHAM, ONE_SHOT, OPEN_LOOP; every controller phase/op mismatch; match counts 0/1/>1; queue FLUSHED/DISCARDED exclusivity; commitment absent/invalid/valid; opacity and exact-once mutations. | 2 machine implementations |
| T09 | same | Five DREAM statuses x three context policies x R boundary classes x endpoint terminal classes; exact cardinality/order/focus/render/token mutations; shared DREAM missing affects only consuming arm. | 2 validators |
| T10 | same | Three root policies x root statuses VALID/NO_ROOTS/NO_ADMITTED/mixed x corpus VALID/EMPTY/RUN_INVALID x trainer success/fail/empty x validation/publication states x selection/action endpoint classes; any D1D matching/padding/truncation/adjustment mutation fails. | 2 validators |
| T11 | same | Every D03 status row for every allowed assay/arm/endpoint; adverse bounds; paired exact-binomial critical counts below/at/above boundary; strict-margin ties; D1A safety lower tails and CP upper bounds; missing ceilings; each edge IUT; all Holm orders/ties/stops; power union bound; resource dedup; every registered literal. | 2 reducers |
| T12 | same | Exactly 11x14=154 visibility cells, every field mutation, every ingress/egress schema, low-entropy hash/arm/provider/control-row leaks, five authority transitions, every preflight denial code, stale predecessor, forged reachability, and no-process-on-denial. | 2 validators |
| T13 | PRE_MODEL_EXECUTION | Populated run lock and every construction/analysis manifest; exactly two distinct static seal identities/receipts; independence evidence; all hash agreement and one-bit disagreement cases; review pass/fail; advocate non-override; run-ratification binding/staleness. | exactly 2 sealers plus fresh reviewer |
| T14 | PRE_SCIENTIFIC_CLAIM | Cold replay of every sampled life/event/queue/DREAM/SLEEP/outcome; every observation or blocker; every dependency role and blocker precedence; four component decisions/intersection; overlap/scope attachment; each alternate, average-ITT, novelty, mechanism, learned-cognition, or overbroad release mutation. | 2 replay/reducer implementations |

The manifest's `coverage_axes` carries the exact enumerated values summarized
above; its completeness verifier computes the Cartesian product after removing
only combinations proven unreachable by the controller/schema predicate. That
predicate's source hash is itself bound. “Exhaust” without the materialized
case list, cardinality, and proof is not a passing fixture.

## 14. Stage-specific authority and dispatch preflight (D11)

### 14.1 Authority artifacts

Each schema fixes its stage constant, decision enum, exact subject-role
registry, predecessor rule, scope, reachability, and self hash.

1. `architecture_ratification_receipt` (`PRE_RATIFICATION_SPECIFICATION`):
   predecessor null; binds the complete successor normative-file manifest, two
   fresh interpretation receipts, critique, a `proceed_to_implementation`
   consensus with no unresolved/removed/underspecified disposition, paused
   intake state, exact scope proposal, architecture human ratification, and
   human evidence. PASS has reachability false.
2. `conformance_receipt`
   (`POST_RATIFICATION_PRE_STATIC_SEAL_CONFORMANCE`): exact passing architecture
   predecessor; implementation/source manifest limited to ratified scope; all
   CPU/no-model schema, semantic, canonical, golden, replay, visibility,
   reducer, power, and run-lock-schema coverage receipts at this stage. PASS
   has reachability false.
3. `populated_run_lock`: exact generator, life count and entropy algorithm,
   path/read counts, capacities, tables, models/tokenizers/embeddings, recipes,
   margins, pi0/ceilings/alpha/power floor, gate registry, seeds, artifacts,
   executable allowlist, dispatch graph, fixtures, scopes, and hashes. No null
   placeholder is populated.
4. Exactly two `static_seal_receipt`s: each binds run lock, conformance,
   implementation identity, complete construction outputs, and exact output
   manifest. Their output hashes must agree role-for-role. An
   `implementation_independence_receipt` proves distinct IDs/executables/root
   algorithm sources and discloses shared dependencies.
5. `independent_review_receipt`: fresh reviewer identity, read-only input
   manifest, verdict PASS/FAIL, concerns, and evidence. `advocate_receipt` binds
   that review and may explain or request rework; it has no override field and
   cannot change FAIL to PASS.
6. `human_run_ratification_receipt`: separate human evidence binds exact run
   lock, conformance predecessor, both seals, independence, passing review,
   advocate, T01-T13 results, authorized run/dispatch scope, and forbidden
   scope. It is not the architecture ratification.
7. `pre_model_authority_receipt` (`PRE_MODEL_EXECUTION`): binds the passing
   conformance predecessor, populated run lock, exactly T01-T13 in ID order,
   two seals, independence, passing review, advocate, and human run
   ratification. PASS/reachable true is recomputed; failed review always denies.
8. `runtime_authority_receipt` (`RUNTIME_VALIDITY`): binds passing pre-model
   predecessor, the complete dispatch-preflight manifest, passing canary, and
   every registered perturbation/integrity receipt. PASS is reachable true.
9. `preclaim_authority_receipt` (`PRE_SCIENTIFIC_CLAIM`): binds passing runtime
   predecessor, T14, endpoint coverage, resources, gates, assay/Holm,
   dependency map, and claim-decision receipts. PASS is reachable true and
   authorizes only literal release construction.

Architecture/run human receipts use `human_evidence` with exact byte offsets;
the validator re-reads the evidence file and compares the exact UTF-8 slice.
Scopes are sorted unique arrays. Requested scope must be a literal subset of
authorized scope and disjoint from forbidden scope. The existing durable
architecture intake remains the authority root; this PPC-local DAG may bind
its validated outputs but cannot replace or weaken it.

### 14.2 Preflight schema and algorithm

```text
dispatch_preflight_receipt := {
  contract: "ppc5.dispatch_preflight.v4", schema_version: 4,
  dispatch_id: ID, dispatch_ordinal: integer,
  dispatch_class: MODEL_INFERENCE | TOKENIZER_EXECUTION |
                  EMBEDDING_EXECUTION | TRAINING | CANARY |
                  CPU_BEHAVIORAL | GPU_BEHAVIORAL | GPU_JOB,
  executable_hash: HASH, populated_run_lock_hash: HASH,
  pre_model_authority_hash: HASH, immediate_state_receipt_hash: HASH,
  mounted_artifact_refs: [artifact_ref],
  decision: PERMIT | DENY,
  denial_reason: SYMBOL | null,
  process_id: integer | null,
  process_start_receipt_hash: HASH | null,
  receipt_hash: HASH
}
```

Preflight recursively re-reads and rehashes sources; it does not trust a
reachable Boolean. Apply first failure:

1. `MALFORMED_INPUT`;
2. `STALE_OR_INVALID_ARCHITECTURE_INTAKE`;
3. `STALE_OR_INVALID_PRE_MODEL_AUTHORITY`;
4. `FAILED_REVIEW_OR_HUMAN_RUN_AUTHORITY`;
5. `RUN_LOCK_HASH_MISMATCH`;
6. `DISPATCH_NOT_ALLOWLISTED` (class/ordinal absent or already consumed);
7. `EXECUTABLE_HASH_MISMATCH`;
8. `IMMEDIATE_STATE_HASH_MISMATCH` or terminal state;
9. `MOUNTED_ARTIFACT_HASH_MISMATCH`;
10. `REQUIRED_PREDECESSOR_MISSING` (including canary when the run-lock dispatch
    graph requires it).

PERMIT requires no failure and has null denial reason. The preflight receipt is
committed before process creation; only then may process ID/start receipt be
recorded in a separate dispatch-start event. DENY requires non-null first
reason and null process/start fields; OS/process audit must prove no child was
started. A stale or denied preflight cannot be retried under the same dispatch
ID. Every dispatch class, including tokenizer-only, embedding-only, training,
CPU behavioral, and canary, uses this same algorithm.

## 15. Required normative replacement set

An r4 proposal adopting this draft must replace, in one newly hash-bound
deliberation chain, at least:

1. machine contract: sections on hashes/state, base transition, every assay
   controller, queue lifecycle, provider/intervention, DREAM, evidence/SLEEP,
   and publication;
2. closed JSON schemas: every object in section 4 and every conditional branch
   in section 11;
3. semantic validators: all sixteen validators in section 12;
4. assay contract: D1B arm `SHAM` becomes `SHAM_EACH`, D1C/D1D bind identical
   `behavior_read_slots`, D1A/D1D direct provider request counts are explicit,
   and restricted interfaces use no arm-semantic labels;
5. analysis/status contract: exhaustive D03 endpoint precedence, no-action
   zero, missing dominance decision, named root statuses, missing adapter
   retirement, edge-indexed SHAM gates, and the D04-D06 binomial objects;
6. visibility contract: exact ingress/egress schema name in every one of 154
   cells and the condition-free projections in section 9;
7. authority contract: the stage-specific DAG and preflight in section 14;
8. claim dependency map: typed role registry, two-phase claim
   decision/release, overlap/scope qualifications, and revised D04 claim
   semantics;
9. T01-T14 definitions: the fixture, coverage, identity, independence, and
   derived-result manifests in section 13;
10. architecture change/scope/intake artifacts: exact new context hashes,
    fresh interpretations, critique, proceed-only consensus, human architecture
    ratification, and later separate run ratification.

Until every replacement is present, schema-valid, independently interpreted,
adversarially critiqued, adjudicated without a rework blocker, and explicitly
human-ratified at the appropriate boundary, the correct authority and release
result is `BLOCKED`.
