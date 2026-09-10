# PPC5r3 machine and construction contract

This file is normative. All algorithms below are pure over sealed inputs.
Numeric sizes, model artifacts, seeds, margins, and capacities are later
run-lock values; algorithms and status meanings are fixed here.

## 1. Canonical bytes and hashes

Every object validates against `contracts.schema.json`, has no unknown fields,
and serializes as UTF-8 JSON with keys sorted lexicographically, compact
separators, integers in base ten, finite numbers only, no escaped solidus, and
one trailing LF. JSON input is exactly one value with no BOM, duplicate key,
prefix, suffix, comment, NaN, or infinity. Parsing failure never partially
applies an object.

Every digest is:

```text
SHA256(UTF8(contract_name) || 0x00 || UTF8(contract_version) || 0x00 || canonical_payload_without_digest)
```

Ledger event `e_t` binds `prior_event_hash`, `pre_state_hash`,
`operation_envelope_hash`, `result_hash`, and `post_state_hash`. The ledger hash
is the event hash of the latest event; the empty ledger hash is
`SHA256("ppc5.ledger.v3\0EMPTY\0")` over the shown UTF-8 bytes. Array orders are
never resorted except by the named algorithm.

Opaque IDs are allocated by the constructor from a monotonically increasing
counter only after a successful commit, remapped per item, and rejected if
their bytes contain any role, condition, target, truth, model, provider, arm,
probe, acquire, or future label under Unicode casefolding.

## 2. Public state and prompt

State contains: contract, phase, schedule_mode, controller_phase,
planning_slot, path_length, item_id, public world bytes, ordered workspace and
opened record IDs, last public READ response, live prediction, last public
outcome, remaining call/read/action/token budgets, call ordinal, consecutive
error count, latest public error, prior transition hash, ledger hash, and
terminal reason. A private controller contains queued READ requests, queued
provider/intervention results, and an optional committed action; these bytes
are never rendered to a model.

The model prompt is canonical JSON `ppc5.model_view.v3` containing exactly:
the public subset above, the run-locked operation schema text/hash, public legal
action catalogue, and no private controller, role, condition, target, truth,
score, provenance, eligibility, future, or assignment field. The tokenizer
input is the locked chat-template application to this single object. There is
no free-text note or hidden harness summary.

## 3. Operations and base transition

One dispatch returns one `operation_envelope`: raw byte hash, input/output token
counts, model/adapter/tokenizer/prompt hashes, call seed and ordinal, parse
status, and either exactly one operation or null. The only operations are:

```text
READ(subject_id, relation_id)
PREDICT(action_id, INCREASE|DECREASE|SAME, value_bin)
ACT(action_id)
STOP(GOAL_COMPLETE|NO_VALID_ACTION|USER_STOP)
```

Harness-forced STOP reasons are `BUDGET_EXHAUSTED|ERROR_LIMIT|INVALID_CELL|
RUN_INVALID` and have origin `HARNESS`; a model cannot emit them.

For `AUTHENTIC` schedule mode, each step uses first-applicable precedence:

1. If terminal, return the stored terminal receipt byte-for-byte; debit and
   append nothing.
2. Verify state, cell, model, tokenizer, prompt, manifest, assignment, and
   mounted-artifact hashes. Failure appends one HARNESS `RUN_INVALID` terminal
   event without model dispatch.
3. If calls=0, append one HARNESS `BUDGET_EXHAUSTED` terminal event.
4. Render and dispatch exactly once. Debit one call. Debit actual locked-
   tokenizer input plus output tokens and store `max(0,before-actual)`.
   If actual exceeds pre-dispatch remainder, append `TOKEN_LIMIT`, do not apply
   the parsed operation, and pass through error handling in step 9.
5. Missing model output appends `MODEL_MISSING_NO_RETRY` and passes through
   step 9. Otherwise parse exactly one operation. Failure appends
   `PARSE_ERROR` and passes through step 9.
6. A parsed READ debits one read, and ACT debits one action, before field,
   domain, reference, binding, or action validation. If the corresponding
   pre-debit remainder is zero, keep zero, append `READ_LIMIT` or
   `ACTION_LIMIT`, and pass through step 9.
7. Validate required fields, finite domains, public references, then ACT live-
   prediction equality, then environment action legality. First failure emits
   `INVALID_DOMAIN`, `INVALID_REFERENCE`, `PREDICTION_REQUIRED`,
   `PREDICTION_MISMATCH`, or `INVALID_ACTION` and passes through step 9.
8. Execute: READ calls the provider once; provider absence yields public
   `MISSING_NO_RETRY` after the valid READ debit, otherwise the response is
   appended before any later call. PREDICT replaces the live prediction. ACT
   executes once, consumes the prediction, and appends outcome. Model STOP
   appends a MODEL terminal event. Each success resets consecutive errors to
   zero.
9. Every nonintegrity error increments consecutive errors. Counts one and two
   append their error/no-op result. Count three replaces that result with one
   HARNESS `ERROR_LIMIT` terminal event while retaining the attempted-call and
   debit fields inside the event. RUN_INVALID terminates immediately and does
   not enter this count.
10. Every nonterminal attempt and every transition appends exactly one event.
    Replaying sealed envelopes/results from initial state must reproduce every
    post-state and byte.

## 4. D1B schedule modes

`AUTHENTIC` is exactly section 3. Its controller phase is `INTERLEAVED`; each
valid READ response is public before the next dispatch. After exactly L valid
READs it permits one PREDICT and one matching ACT; other valid operation types
at a required slot are `SCHEDULE_VIOLATION` and use the error rule.

`ONE_SHOT_READ` starts `PLANNING_READS`, slot zero. Exactly L dispatches must
emit READ. Each dispatch debits and validates immediately as in sections 3.4–
3.7. A valid request is appended only to the private queue; the next public
model view exposes decremented budgets, incremented call ordinal and
`SLOT_ACK(slot,status)` but no request bytes, response, score, object, record,
or provider error. After slot L, controller phase becomes `FLUSH_READS` with no
model call: execute queued providers and response interventions in request
order, append one canonical public request/result event per slot, apply missing
and error-limit rules, then expose the ordered returns together. If nonterminal,
phase becomes `COMMIT`; permit one ordinary PREDICT and one ordinary ACT.

`OPEN_LOOP` uses the same L private READ-planning slots and acknowledgements,
then enters `COMMIT_BLIND`: exactly one PREDICT call and one matching ACT call
are parsed, debited, validated, and privately queued while no READ response or
outcome is visible. There are no more model calls. In `FLUSH_AND_EXECUTE`, the
harness executes queued providers/interventions in order, appends public
returns, then executes the committed action once and appends its outcome.
Missing or invalid commitment produces the corresponding error/terminal bytes
and no action. No post-outcome model call is allowed.

In both controls: parse/token/budget/domain errors occupy their assigned slot;
no retry occurs; an invalid READ is not queued; a third error terminates and
discards all unexecuted private queue contents with their hashes recorded only
in the terminal audit receipt. The opacity handicap is part of the registered
control. Every expected path intervention must match exactly one selected
response; zero or multiple matches is RUN_INVALID. Non-target provider traffic
is an explicit no-op receipt.

## 5. Candidate providers

A semantic table has unique candidate and record IDs, is sorted by candidate
ID, and each nonempty public record is a member-complete tuple. Duplicate,
unsorted, malformed, or cross-field-inconsistent tables are INVALID_CELL. An
empty valid table returns NOT_FOUND; an absent provider returns
MISSING_NO_RETRY.

READ-provider cells score the canonical target response token sequence,
including EOS and excluding prefix tokens. For each candidate compute mean
token log probability using the run-lock-bound deterministic fp32 scoring
kernel, quantize once to signed multiples of 1e-6 using round-to-nearest-even,
reject NaN/Inf as RUN_INVALID, select maximum and break exact ties by candidate
ID. ADAPTER_OFF mounts null; other cells mount their typed adapter only here.

RAW_RAG is descriptive: run-lock-bound embedding artifact, float64 cosine,
zero-vector NOT_FOUND, locked threshold, candidate-ID tie-break. FULL_CONTEXT
is descriptive: render the complete table; if it exceeds its preassigned token
allowance, construction fails before assignment; never truncate. EXPLICIT_GRAPH
uses exact or reverse-exact keys and returns NOT_FOUND for partial/paraphrase.

FOUND contains all four non-null subject/relation/object/record IDs matching one
table member. Every non-FOUND response has all four null. Candidate ID, score,
rank, provider, adapter, condition, target, latency, and diagnostics never enter
the public response.

## 6. Interventions and path construction

BENCHMARK_CONSTRUCTION may read a sealed finite hidden world-variant table and
registered correct action. Before outcomes, build a target-blind alias map from
the public ontology: group identical declared alias keys and choose the
lexicographically least public symbol as representative. Hash source and map.

An observation set is action-sufficient iff every sealed world variant
consistent with exactly those observations has the same unique correct action.
A path is decisive iff its full ordered edge set is sufficient, every proper
subset is insufficient, its length is two or three, and no other sufficient
simple path exists within the locked READ budget. Construct the canonical
directed multigraph from direct eligible public atoms; enumerate edges and all
simple paths lexicographically. Hash domain-separated prompt, action, handle,
source-event, and edge preimages; any overlap is construction failure.

From a finite sealed alternative-response set, TWIN is the lexicographically
first response reversing the registered directional binding while matching
schema, debit, allowance, locked token count, and byte-length class. SHAM is the
lexicographically first nonpath substitution for which the finite-world oracle
preserves the unique action with identical parity constraints. If no candidate
exists, construction fails. Both independent sealers recompute the proof object.

A privileged router reads sealed condition/item/target assignment and emits
only `runtime_intervention_projection`: opaque intervention ID, query hash,
selected-response hash, replacement response or null, parity fields, and
lineage hash. RESPONSE_INTERVENTION never receives condition, item, target,
truth, or role. AUTHENTIC emits unchanged; CUT emits NOT_FOUND; TWIN/SHAM emit
replacement. Exactly one expected match is mandatory.

## 7. DREAM context policies

At a sealed snapshot, one shared frozen call receives only the canonical public
slice, public world state, live prediction, and allowed record-ID catalogue.
Capacity `K_context` is a record count; a separate token ceiling applies to the
exact canonical context rendering. The call and actual tokens are debited once
as a shared physical event. Output is PUBLISH of zero through K_context unique
visible record IDs in public commit order plus null/or-retained focus, or
ABSTAIN. Missing has no retry; invalid IDs/order/focus/cardinality or render
overflow is DREAM_INVALID_OUTPUT.

AUTHENTIC installs valid PUBLISH exactly and honors focus; empty installs an
empty view; ABSTAIN/invalid/missing installs none. RECENCY selects descending
commit ordinal then record ID, first K_context, and focuses its first record or
null. PERMUTED sorts allowed IDs by
`SHA256("PPC5R3_CONTEXT" || 0x00 || recipient_life_id || 0x00 || seed || 0x00 || record_id)`,
then record ID, takes K_context, and focuses first/null. Control render overflow
is preassignment CONSTRUCTION_FAIL. All branches continue unless an independent
runtime failure occurs.

## 8. Evidence, root policies, writer, and publication

For every nominee, EVIDENCE_GATE checks first failure in order: record exists;
was visible to shared DREAM; ACQUIRE role; item closed; source ordinal before
boundary; no PROBE/future lineage; not target-derived; direct public environment
observation; direct-relation shape; exact source hash; final eligibility. D1A
uses the same checks except DREAM visibility. Rejection precedes equivalence
lookup. Exact equivalence is the canonical tuple; choose least eligible record
ID. Construction-only semantic/alias/item/donor family fields are reported but
never enter equivalence or primary claims.

Root capacity `K_root` is representative rows. DREAM_TO_SLEEP preserves valid
admitted nominee order then applies K_root. RECENCY_TO_SLEEP sorts eligible
representatives by descending commit ordinal then record ID and takes K_root.
HASH_PERMUTED_TO_SLEEP sorts by
`SHA256("PPC5R3_ROOT" || 0x00 || recipient_life_id || 0x00 || seed || 0x00 || record_id)`,
then record ID, and takes K_root. Control cardinality never depends on authentic
output.

WRITER receives admitted root projections only and renders one atomic READ
request/exact supported FOUND response per representative in policy order. It
does not cycle, downsample, pad, paraphrase, add rationale, or include cognition
or policy targets. TRAINER receives only rows, sealed recipe, clean base, and
seed bundle. Validation requires expected schema, finite tensors, exact shape,
base/tokenizer/recipe hashes, and a successful locked no-model structural
adapter check; otherwise TRAIN_FAILED. Publication is atomic rename of one
manifest-bound artifact or none. TRAIN_FAILED continues adapter-off and is an
observed assigned policy consequence. No retry or fallback occurs.
