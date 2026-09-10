# PPC5r6 canonical machine contract

Status: proposal only. Numeric sizes, generator parameters, seeds, margins,
capacities, model artifacts, recipes, and thresholds are populated only by a
later typed run lock and never defaulted by implementation.

## 1. Canonical bytes and the acyclic transition DAG

Canonical JSON is UTF-8, NFC strings, sorted object keys, compact separators,
integer-only exact counters, no NaN/Inf, and one terminal newline. For type T,
`H(T,x)=SHA256(UTF8(contract_T) || 0x00 || UTF8("6") || 0x00 ||
canonical_json(x_without_self_hash) || 0x0a)`. The inventory domain is audit
metadata and is not part of the preimage. A digest may not occur inside its own
preimage.

State is three objects, computed only in this order:

1. `state_body_hash = H(STATE_BODY, post_state_body)`. A state body contains
   the public-view body and a hash of the private-controller receipt, but
   excludes the event being created, the new ledger head, prior-event hash,
   state-receipt hash, and every self hash.
2. `event_hash = H(TRANSITION_EVENT, {prior_event_hash,
   pre_state_receipt_hash, operation/result/debit/queue bindings,
   post_state_body_hash})`.
3. `state_receipt_hash = H(STATE_RECEIPT,
   {state_body_hash, ledger_head:event_hash})`.

Genesis has no transition event: it computes the initial private controller,
initial state body, then a state receipt whose `ledger_head` is the fixed
domain-separated `EMPTY_LEDGER_HEAD`. Every later event binds the previous
state receipt and previous ledger head. Terminal and nonterminal state
receipts both retain `ledger_head`.
Terminal replay returns the stored terminal body/event/receipt bytes and
launches no call. This order governs ordinary, error, missing, flush, discard,
and terminal transitions; alternative hash orders are invalid.

## 2. Public state, private controller, and model view

The public-view body contains only: contract/version, assay-facing controller
phase, slot ordinal, public item/world bytes, visible record bytes or IDs,
opened record IDs, last public READ response, live prediction, last public
outcome, remaining call/read/action/input-token/output-token budgets, call
ordinal, consecutive error count, latest public error, prior public transition
summary, legal action IDs, and operation-schema hash. It contains no event hash,
ledger head, state receipt hash, or private controller field. Immediately before
dispatch, the renderer combines the verified public-view body with exactly the
`ledger_head` from its matching state receipt to form the separately hashed
`model_view`; the state body never embeds this rendered view.

The private controller contains: assay/cell opaque IDs, one concrete
`indexed_phase` (family, current index or null, bound symbol, bound value),
expected operation slot, queue entries, assignment handles, restricted matcher
handles, model/tokenizer/prompt/artifact handles, common-random seed bundle,
allowances, and terminal flags. Its receipt is hashed and may influence only
the transitions enumerated in section 5. Treatment-semantic labels never enter
public bytes or restricted stage ingress.

The model receives only the canonical model view and emits one JSON object.
Exactly one top-level JSON value and no other non-whitespace bytes are allowed.

## 3. Operations and dispatch accounting

The only operations are:

- `READ(subject_id, relation_id)`
- `PREDICT(action_id, predicted_value)` where `predicted_value` is an exact
  reduced rational in `[0,1]`
- `ACT(action_id)`
- `STOP(reason)`

Model STOP reasons are `MODEL_STOP` or `NO_VALID_ACTION`. Harness terminal
reasons are `SCHEDULE_COMPLETE`, `SCHEDULE_INCOMPLETE`,
`PROVIDER_SEQUENCE_COMPLETE`, `BUDGET_EXHAUSTED`, `ERROR_LIMIT`,
`CONSTRUCTION_FAIL`, and `RUN_INVALID`. Missing calls are typed operation or
provider results, not terminal reasons. A model cannot emit a harness reason.

For every model dispatch, in order:

1. recompute the exact active authority/preflight chain;
2. verify state, controller, cell, generator/sample, model, tokenizer, prompt,
   artifact, assignment, and run-lock hashes;
3. if any integrity check fails, append one no-call RUN_INVALID transition;
4. if the call allowance is zero, append BUDGET_EXHAUSTED with no call;
5. debit one call before dispatch;
6. dispatch exactly once with the preassigned common-random seed;
7. debit actual tokenizer input and output counts separately, clamped at zero;
8. store raw output bytes/hash and exact token IDs/counts;
9. parse one operation or emit MODEL_MISSING_NO_RETRY, TOKEN_LIMIT, or
   PARSE_ERROR;
10. apply the unique matching result-keyed row in the exact controller table;
11. debit a logical READ or ACT before provider/environment execution;
12. append exactly one event and next state receipt before a later call.

The controller registry uses no phase strings. Each row carries a closed
indexed-phase pattern, a boundary predicate, and an ordered exhaustive
`result_transition` array. Each transition fixes the next phase or terminal,
index update, endpoint effect, queue effect, and missing advancement. Boundary
rows explicitly materialize `READ[L]`, `PLAN_READ[L]`, `FLUSH[L]`,
`PROVIDER[Q]`, and `R=0`; the D1D provider boundary enters `READ[0]` when R>0
and PREDICT when R=0. No implementation parses an expression or supplies a
default.

Errors increment the consecutive count. A valid operation resets it. The third
consecutive error yields ERROR_LIMIT. There is no retry or seed reuse. Token
overflow discards the parsed operation and cannot execute a logical action.

## 4. Common provider

A semantic table is a canonical candidate-ID-sorted, member-complete table with
unique candidate and record IDs. Empty is valid and returns NOT_FOUND.
Malformed, duplicate, unsorted, or cross-field-inconsistent tables are
CONSTRUCTION_FAIL before assignment and RUN_INVALID after seal; no provider
receipt is emitted.

The causal READ provider has one algorithm identity:
`MEAN_RESPONSE_LOGPROB_V5`. Its ingress contains the canonical request, complete
table, tokenizer/scoring-kernel handles, and opaque mounted-artifact handle or
null. It receives no arm, provider-kind, recipient, donor, binding-shuffle, or
treatment label. Score every candidate's canonical response sequence including
EOS and excluding prefix tokens; take mean token log probability in locked
deterministic fp32; reject NaN/Inf; quantize once to signed 1e-6 units with
round-to-nearest-even; maximize; break exact ties by candidate ID. The public
response exposes only the typed FOUND tuple or all-null NOT_FOUND, never score,
rank, candidate, artifact, arm, latency, or diagnostics.

FULL_CONTEXT, RAW_RAG, and EXPLICIT_GRAPH are optional descriptive providers
with distinct arm-neutral schemas and receipts. They cannot enter D1A-D1D
causal gates. FULL_CONTEXT renders the complete table or produces
CONSTRUCTION_FAIL before assignment; it never truncates.

## 5. Total assay controllers

The exact machine table is the cross-product enumerated by the controller
fixtures; these rows are normative:

### D1A `DIRECT_PROVIDER`

No model call and no public cognition. Execute every assigned canonical request
once through the common provider, append its provider/endpoint receipt, and
terminate the endpoint. Missing provider has no retry. Any attempted cognitive
operation is RUN_INVALID.

### D1B `D1B_AUTHENTIC`

For a path of locked length L, slots `READ_0 ... READ_(L-1)` each require READ.
A valid response is public before the next slot. Then `PREDICT` requires one
PREDICT and `ACT` requires a matching ACT. Successful ACT immediately produces
SCHEDULE_COMPLETE. Any valid but wrong operation, including STOP, is
SCHEDULE_VIOLATION. Parse/token/budget/domain/reference errors occupy and
advance or finalize the slot exactly as registered; no call is retried. A
physically missing call likewise consumes its slot and seed exactly once,
advances to the next slot or boundary, and retains endpoint-level missing
dominance.

### D1B `D1B_ONE_SHOT`

Slots `PLAN_READ_0 ... PLAN_READ_(L-1)` require READ. Each valid request is
stored only in a private queue; the next public state exposes only a parity-
matched `SLOT_ACK(slot, QUEUED)`. After L slots, the no-model controller emits
one `FLUSH_READ` transition per planned slot in order. A queued slot executes
its provider and precomputed intervention and publishes its result; a rejected
slot emits `FLUSH_SKIPPED_REJECTED` without revealing private request bytes.
Only after all slot transitions are committed are the ordered responses
exposed together. Then exactly one one-attempt PREDICT and one matching
one-attempt ACT are required. Successful ACT terminates SCHEDULE_COMPLETE;
otherwise a no-model finalizer terminates SCHEDULE_INCOMPLETE.

### D1B `D1B_OPEN_LOOP`

The L private planning slots are identical to ONE_SHOT_READ. Before any flush,
one one-attempt PREDICT and one matching one-attempt ACT are privately queued
in `COMMIT_BLIND`; no response or outcome is visible and no later model call is
allowed. The no-model controller then emits the same one-transition-per-slot
flush sequence as ONE_SHOT_READ, followed by one `EXECUTE_COMMIT` transition.
A valid matching commitment executes exactly once and terminates
SCHEDULE_COMPLETE. Missing/invalid commitment terminates SCHEDULE_INCOMPLETE
without an action.

### D1C `FIXED_BEHAVIOR`

After the assigned reversible context is installed, execute exactly
`R=behavior_read_slots` one-attempt public READ slots, then exactly one
one-attempt PREDICT slot and one one-attempt matching ACT slot. `R` is a
prospective nonnegative run-lock integer and is identical across paired arms
for an assay/item. Every error or missing result occupies and advances its
slot; there is no retry. `R=0` begins at PREDICT. Successful ACT terminates
SCHEDULE_COMPLETE; exhaustion without a successful action terminates
SCHEDULE_INCOMPLETE. All context-policy statuses use this identical
controller.

### D1D `D1D_TOTAL`

Root policy, SLEEP, validation, and publication run first. The provider then
executes every sealed selection-endpoint request once using the resulting
artifact or null, followed by the same `R=behavior_read_slots` one-attempt
READ/PREDICT/ACT behavioral program as D1C. A missing or invalid adapter never
skips either endpoint: behavior continues adapter-off, while the assigned
training/resource dose remains the realized dose and is never padded,
truncated, or otherwise post-treatment adjusted. All root-policy arms use
this controller and the same recency context.

At every required non-STOP slot, STOP is SCHEDULE_VIOLATION. Error precedence
is: integrity RUN_INVALID; pre-dispatch budget; missing call; token/parse;
logical allowance; domain/reference/prediction/schedule; provider/environment
missing; provider/environment invalid; success. `status_contract.json` maps
each integrity-clean no-action terminal to observed normalized action zero.

Every private queue entry embeds an upstream `QUEUE_SLOT_BODY` hash. The body
binds slot, seed ordinal, original operation-envelope/request refs, and
QUEUED/REJECTED state, but never controller-after. After controller-after is
known, a downstream `QUEUE_SLOT_RECEIPT` binds the body, controller-before, and
controller-after and is referenced by the cause-specific transition lineage.
Each
`QUEUED` slot has exactly one mutually exclusive successor:

- `FLUSHED`: provider, intervention, public result, and public event bindings
  are non-null and discard is null; or
- `DISCARDED`: one typed discard receipt and reason are non-null, while
  provider, intervention, public result, and public event bindings are null.

`REJECTED` slots never have a queue effect. Flush/discard effects are emitted
in slot order and a run-wide coverage validator proves exactly one effect for
every queued slot. Terminal discard binds all and only the remaining
unexecuted queue without exposing its bytes publicly. Empty discard lists are
canonical empty arrays, never null.

After integrity-blocker precedence, a missing required model, provider, or
DREAM call dominates the affected endpoint even if a later controller branch
produces an action: the endpoint is `MISSING`, its raw value is null, and its
registered adverse analysis bound is used. A paired control that does not
consume the missing shared dependency is not marked missing.

## 6. Decisive paths and condition-free interventions

Construction uses a sealed finite world-variant table and correct action under
no-model privilege. An observation set is sufficient iff all consistent variants
have the same unique correct action. Build the canonical eligible directed
multigraph; enumerate simple paths by length then edge-ID tuple inside the READ
budget. For path length L, encode all nonempty proper subsets by ascending
L-bit mask (exactly 2^L-2) and prove each insufficient; prove the full path
sufficient and every other enumerated path insufficient.

Every ordered edge binds a distinct source_event_id and its raw source preimage
hash. Domain separation does not manufacture source disjointness. At each edge
construct: CUT=canonical NOT_FOUND; TWIN=lexicographically first parity-matched
response reversing the registered directional binding; SHAM=lexicographically
first parity-matched nonauthentic response for which replacing that edge
preserves the unique correct action. Missing construction is CONSTRUCTION_FAIL.

The privileged router alone sees condition/item/edge assignment, original
selected response, and low-entropy match hashes. For the assigned target key,
exactly one match resolves the intervention and zero or multiple matches are
RUN_INVALID. A valid non-target READ with zero assigned-target matches uses
`OFF_PATH_AUTHENTIC_PASS_THROUGH` and emits the common provider response; this
adaptive divergence remains an outcome rather than a validity filter. Its
restricted projection contains only:
opaque instance ID, already-resolved canonical public response bytes,
locked-token/debit class, byte-length class, and opaque lineage receipt hash.
It omits condition, kind, arm, item, edge, target, truth, role, query hash, and
selected-response hash. RESPONSE_INTERVENTION can only emit those bytes.

## 7. Shared DREAM and context installs

At a sealed snapshot one no-retry call to the same frozen model receives only a
canonical public-slice blob, world-state blob, live prediction, allowed public
record-ID catalogue, record capacity, and render-token ceiling. Its typed call
receipt binds the exact content-addressed input/render blobs, tokenizer, prompt,
model, raw output/token blobs and hashes, actual debit, seed, prior receipt, and
shared physical event ID. Invalid output bytes remain private but hash-bound.

Output is PUBLISH of zero through K unique allowed IDs in public commit order
plus retained-or-null focus, or ABSTAIN. Missing, invalid ID/order/focus,
cardinality, or render overflow has no retry. The one physical DREAM realization
is shared by all paired D1C/D1D policies.

AUTHENTIC installs up to the prospectively locked `context_capacity` selected
records in published order. RECENCY installs that same locked capacity from the
most recent eligible records under the predeclared total order. PERMUTED uses
that locked capacity under recipient-local hash order. Control capacity never
comes from realized DREAM cardinality and those controls do not consume DREAM.
Empty/abstain/invalid installs the exact no-view policy from
`status_contract.json`; only AUTHENTIC inherits missing DREAM. Every install
receipt binds exact content-addressed rendered-context bytes and its declared
dependency kind.

## 8. Evidence, roots, rows, training, and publication

Before DREAM, a deterministic target-blind selector emits the complete eligible
ACQUIRE nominee universe. Eligibility is direct, public, closed, pre-boundary,
non-PROBE, nonfuture, nontarget-derived, noncognitive, non-DREAM, nonscorer, and
nonpolicy-target. Each nominee is tested in DREAM order; first failing predicate
and all predicate inputs are recorded. Equality/dedup uses canonical semantic
tuples and the run-locked target-blind capacity order.

DREAM_TO_SLEEP considers DREAM nominees in order. RECENCY_TO_SLEEP and
HASH_PERMUTED_TO_SLEEP are total policies over the same universe and the
prospectively locked `root_capacity`; they do not consume DREAM. Only
DREAM_TO_SLEEP inherits a missing DREAM. No realized policy cardinality changes
the control capacity, provider endpoint schedule, or training rule.
The aggregate root receipt binds the complete universe, all nominee projections,
order, dedup, capacity, selected roots, admitted roots, and one aggregate status.

The writer is arm-neutral. It receives only ordered admitted projections and
emits one canonical READ row per root: exact runtime request/table template to
one supported FOUND response. It invents no prose and has no access to arm,
truth, target, future, PROBE, cognition, DREAM text, scores, or outcomes beyond
the admitted public response. Authentic and binding-shuffled rows share one row
schema. An ordered corpus manifest binds every row, row/source hash, token and
byte-class vector, corpus hash, and zero-dose status.

Training starts from the same clean base. Only response target tokens carry
loss. The trainer receives arm-neutral corpus bytes, recipe, tokenizer, and
seed handles; validates finite tensors, base/tokenizer/shape/recipe/mount
compatibility, and declared update counts; and writes to quarantine. Atomic
publication occurs only after validation and produces a self-hashed adapter
manifest plus transition receipt. TRAIN_FAILED publishes no adapter, preserves
resource dose, and continues adapter-off. Post-seal disappearance/mismatch is
RUN_INVALID.

## 9. Closed receipts, tests, and authority

`object_inventory.json` lists every normative ingress, egress, manifest, result,
and receipt with its schema reference, contract/domain tag, producer, and self-
hash field. Consumer roles and cardinalities are encoded at the consuming
object's schema boundary rather than repeated as free inventory prose.
`contracts.schema.json` supplies inline closed fields for every inventory type;
there is no generic semantic `payload_ref`. Semantic rules in
`semantic_validators.md` close cross-field role, predecessor, state/status, and
visibility constraints. Hashes are role-labeled and ordinal where repeated;
unlabeled dependency arrays are forbidden. A static reference-reachability
audit requires every semantic hash/ref to resolve to exactly one inventoried
type, producer, and permitted consumer stage.

The populated run lock binds, without defaults: initial call/read/action/input-
token/output-token budgets; THINK and DREAM prompts; model-view, state, DREAM,
context, provider, row, and release renderers; scoring kernel; operation parser;
indexed-controller evaluator and registry; seed derivation inputs and
algorithm; environment and action schemas; endpoint reducer; every allowed
dispatch executable; and every source/manifest rechecked by preflight.

T01 is only the already-authorized generic intake command result plus its
awaiting-consensus state/history; it consumes no PPC-specific fixture or
implementation. Every PPC-specific T02-T14 test has a manifest binding
generator/version/source hash, finite universe or completeness proof, expected
outputs/hashes, negative mutations, prerequisite/evidence roles, coverage
count, reducer, and result hash. A pass is derived, never asserted. Independent
agreement binds distinct implementation identities and source hashes.

T14 is acyclic: exactly two independent cold-replay receipts consume only
T01-T13, runtime, complete-life/event/queue/DREAM/SLEEP/endpoint/reducer,
candidate-decision, qualification, forbidden-claim, overlap, scope, dependency,
and resource evidence. The final T14 result consumes those two receipts and
their independence proof. It contains no release or preclaim-authority input.

Stage-specific authority receipts and dispatch preflight are defined by
`authority_contract.json`. No Boolean inside the artifact being checked can
make itself reachable. Current authority is NONE_PROPOSAL_ONLY.
