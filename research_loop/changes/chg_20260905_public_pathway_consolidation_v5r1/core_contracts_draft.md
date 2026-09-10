# PPC5r1 core-contract repair draft

Status: deliberation input only. These bytes are not ratified architecture, do
not modify PPC5, and authorize no implementation, model call, training, or run.
They give the smallest closed contract for PPC5_RES01, RES02, RES03, RES05,
RES07, RES11, RES12, and the corresponding part of RES16.

Normative terms `MUST`, `MUST NOT`, and `ONLY` are literal. All JSON schemas are
closed (`additionalProperties:false`), use UTF-8 canonical JSON with sorted
keys, compact separators, declared array order, and one trailing LF. A value
which fails its schema is not partially parsed.

## 1. Authority split

The ratified architecture bytes MUST bind:

* schemas, enum domains, validation and precedence rules;
* the total THINK/DREAM transition algorithms and canonical statuses;
* visibility modalities and the private provenance boundary;
* cue, rendering, scoring, selection, writer-admission, deduplication, and
  publication algorithms;
* claim wording/dependencies and acceptance-stage ordering.

The later `run_lock.json` MUST bind, without changing those algorithms: exact
model, tokenizer, checkpoint, trainer and prompt-file hashes; decoding and
training recipe; all numeric budgets, candidate count, capacities, sequence
limits, LoRA ranks, dtypes, resource quantities, life count, power inputs,
margins, aggregation functions, missingness limits, assignment seeds, runtime
limits, and stopping rules. Every later-bound field MUST be populated,
hash-bound, independently reviewed, and exactly human-ratified before any model
call. A change to a current-bound item requires a new architecture change; it
cannot be made in a run lock.

Finite symbol domains and benchmark content (legal action IDs, relation IDs,
relation-template IDs, outcome IDs, value bins, environment transition tables,
and cue fixtures) MUST be present in the frozen construction manifest governed
by the ratified schemas. They are neither implementation defaults nor values an
implementer may invent. Numeric cardinalities and budgets remain run-lock
fields.

## 2. Visibility modalities

For information item `x` at stage `s`, exactly one modality applies:

| Modality | Exact permission |
|---|---|
| `VISIBLE` | The declared canonical bytes of `x` may enter the stage's model/scorer input and declared public output. No undeclared projection is implied. |
| `DERIVED_ONLY(p)` | Raw `x` is unavailable. Only the output of named, ratified deterministic projection `p(x, visible_inputs)` may enter; mutation of `x` that preserves the projection MUST preserve every stage semantic input and output byte. |
| `PRIVATE_INTERNAL` | The non-model harness may read `x` only for the named routing, integrity, or audit operation. `x` MUST NOT enter prompts, tokenizer inputs, scorer candidates, selection keys, loss-bearing bytes, model-visible state, public responses, IDs, clocks, filenames, errors, or timing-dependent branches. |
| `FORBIDDEN` | No component of the stage may read `x`, a proxy for `x`, or a value derived from `x`. Holding allowed inputs fixed, mutation of `x` MUST preserve every stage input, choice, state transition, and output byte. |

In the PPC5 matrix, legacy labels map as follows: `visible` = `VISIBLE`,
`derived_only` = `DERIVED_ONLY(named_projection)`, `hidden` =
`PRIVATE_INTERNAL(named_use)`, and `forbidden` = `FORBIDDEN`. A row lacking the
required named projection/use is invalid architecture, not an implementation
choice.

`PRIVATE_INTERNAL` is not a weaker spelling of `VISIBLE`; use in semantic
selection is forbidden unless a named architecture projection expressly makes
the result `DERIVED_ONLY`. Provider identity is `PRIVATE_INTERNAL` for mounting
the assigned provider but cannot affect a public byte except through that
provider's declared score function. Hidden truth, target membership, private
item role, probe/future outcomes, and root equivalence are `FORBIDDEN` at THINK,
DREAM, and READ-provider scoring/selection/emission.

The visibility noninterference product MUST compare semantic choices as well as
serialized bytes. It MUST fail if a forbidden/private mutation changes a
candidate score input, selected candidate, rejection reason, public response,
model-visible error, or next state.

## 3. Public READ bytes and private root provenance

### 3.1 Semantic candidate and public response

The public semantic candidate table contains exactly:

```text
(candidate_id, record_id, subject_id, relation_id, object_id,
 public_record_bytes)
```

It contains no root/equivalence value, role, condition, target membership,
score, truth label, or probe/future field. `candidate_id` is provider-private and
MUST NOT occur in a public response.

The sole public response schema is:

```json
{"contract":"ppc5.read.v1","object_id":"ev-00000000|null","record_id":"rec-00000000|null","relation_id":"public_relation_id|null","status":"FOUND|NOT_FOUND|MISSING_NO_RETRY|INVALID_CELL","subject_id":"ev-00000000|null"}
```

For `FOUND`, all four ID fields are non-null and equal one semantic candidate.
For every other status, all four are null. `NOT_FOUND` is a semantic selection;
`MISSING_NO_RETRY` is a post-dispatch provider absence; `INVALID_CELL` is a
pre-dispatch integrity failure. No rank, score, provider, condition, latency,
candidate ID, root hash, or diagnostic text may be emitted.

### 3.2 Private companion

`root_provenance.v1` is a private SLEEP/audit companion keyed by `record_id`.
Each entry contains exactly `record_id`, its public source event ID, and an
opaque equivalence-class ID. It contains no answers, truth, role, score,
condition, target membership, or eligibility flag. The separate private
`writer_eligibility.v1` companion, keyed by public source event ID, contains the
immutable role, item-close event ID, source-commit ordinal, mechanically known
source-channel kind, target-derived quarantine bit, and final eligibility bit
needed by the evidence gate. The quarantine bit is generated from sealed source
lineage, contains no target identity or truth, and is not readable by any model.
Entries and class-member lists are sorted lexicographically by public ID. These
hashes may occur only in private SLEEP/audit receipts.

Root provenance is `FORBIDDEN` at THINK and DREAM and at READ-provider
candidate rendering, tokenization, scoring, tie-breaking, selection, and
emission. Provider runtime MUST receive the semantic table without the private
companion. A control such as root shuffle may use the companion only during
sealed SLEEP/construction, then pass a provenance-free semantic table to the
provider. Holding the semantic table fixed, every mutation or relabeling of the
companion MUST leave provider inputs, scores, choices, responses, and THINK
state byte-identical.

### 3.3 DREAM-to-SLEEP projection

Only the ordered `retain_record_ids` field of a valid `PUBLISH` nominates D1D
roots. Hypotheses, subgoals, surprises, focus, request inputs, free-form bytes,
and ancestor closure nominate none.

`dream_to_sleep_projection.v1` executes privately and totally:

1. Validate that every retained ID is unique, public, visible in the DREAM
   input, and present in `root_provenance.v1`, in the emitted order.
2. For each ID, inspect its equivalence class and retain only members which are
   marked by `writer_eligibility.v1` as committed no later than the sealed sleep
   boundary, from a closed `ACQUIRE` item, direct public
   environment-observation atoms, not target-derived, and final-status eligible.
3. If the retained ID is missing or its eligible member set is empty, emit the
   first applicable private rejection code in this order:
   `MISSING_RECORD`, `NOT_DREAM_VISIBLE`, `NOT_ACQUIRE`, `ITEM_OPEN`,
   `AFTER_BOUNDARY`, `PROBE_OR_FUTURE`, `TARGET_DERIVED`,
   `NOT_DIRECT_PUBLIC_ATOM`, `STATUS_INELIGIBLE`, `EMPTY_CLASS`.
4. Otherwise choose the lexicographically least eligible public source
   `record_id` as representative.
5. Stable-deduplicate representatives by first retained occurrence; later
   occurrences receive `DUPLICATE_CLASS`.

The result is an ordered representative list plus a private per-input receipt.
An empty list and a partially rejected list are valid realized selections, not
grounds for reassignment, fallback, or exclusion. Neither representatives nor
rejection details return to THINK or DREAM.

## 4. Total public operation machine

### 4.1 States and initialization

The machine has exactly `INITIAL`, `RUNNING`, and `TERMINAL` phases. A successful
`start(item, construction_manifest, run_lock)` verifies hashes and schemas,
allocates the manifest's root subgoal as the first legal commit, initializes
empty ordered event, record, hypothesis, citation, repeat, error, and DREAM
collections, sets the root as the only active open branch, and copies the locked
budgets into counters. It returns `RUNNING`.

Any failed pre-model schema, hash, manifest, environment-cell, or budget-domain
check returns `TERMINAL(INVALID_CELL)` and dispatches no model. Calls after
`TERMINAL` return the same terminal object byte-for-byte, consume nothing, and
append nothing.

The closed `ppc5.state.v1` object has exactly these top-level fields:
`contract`, `phase`, `item_id`, `world_state`, `workspace_record_ids`,
`active_subgoal_id`, `subgoal_rows`, `hypothesis_rows`, `live_prediction`,
`opened_record_ids`, `focus_record_id`, `citation_edges`,
`unresolved_surprise_ids`, `prior_public_transition`, `budgets`, `repeat_rows`,
`consecutive_error_count`, `latest_error_codes`, `ledger_hash`,
`next_id_ordinals`, and `terminal_reason`. Each row is a closed object containing
only the fields named by the corresponding operation in section 4.2 plus
`status` and commit ordinal. `budgets` has exactly `calls`, `reads`, `actions`,
`dreams`, and `tokens`; `next_id_ordinals` has exactly `branch`, `subgoal`,
`hypothesis`, `event`, and `record`. Nullable fields are null, never omitted.
`terminal_reason` is null outside `TERMINAL`; `active_subgoal_id` and
`live_prediction` are null when absent. The environment's `world_state` and
`prior_public_transition` are closed construction-manifest schemas, not free
JSON.

Only IDs enumerated by the construction manifest or monotonically allocated
after a legal commit are valid. Array order is event/commit order unless an
explicit lexicographic order is stated. Reference validation precedes every
commit. Prospective citation edges are checked before commit: a directed cycle
is illegal, while a diamond is legal.

### 4.2 Closed operation domain

The existing eleven operations are the complete domain. Their arguments use
only these manifest-bound finite domains:

```text
OPEN_SUBGOAL  parent_id := open subgoal on active ancestry
QUERY         query_type := RELATION; subject_id; relation_id
FOLLOW        record_id := opened public record
HYPOTHESIZE   nonempty unique record_ids in open order;
              relation_template_id; predicted_outcome_id
PREDICT       direction := INCREASE|DECREASE|SAME;
              value_bin; action_id
ACT           action_id
REVISE        hypothesis_id; nonempty unique record_ids in open order;
              predicted_outcome_id
BACKTRACK     no fields
REQUEST_DREAM reason := CONTEXT_PRESSURE|UNRESOLVED_SURPRISE|RECONCILE;
              unique record_ids in open order
DEFER         reason := NO_PROGRESS|REPEAT_LIMIT|ERROR_LIMIT|BUDGET_BLOCKED
STOP          reason := GOAL_COMPLETE|NO_VALID_ACTION|BUDGET_EXHAUSTED|USER_STOP
```

Every omitted, additional, mistyped, unknown-domain, duplicate, stale,
unallocated, closed-branch, or wrong-ancestry reference is illegal. `ACT` is
state-legal only with a live prediction for the same action on the active open
ancestry. Environment action validity is then looked up in the sealed current
state/action table; an unavailable action is `ACTION_INVALID` and does not
change environment state.

### 4.3 Step precedence and charging

For each turn, apply exactly this order; the first terminal/failure branch wins:

1. If phase is `TERMINAL`, return its frozen object.
2. Verify pre-dispatch state, cell, model, tokenizer, adapter-mount, and manifest
   hashes. Failure commits no ID and returns terminal `INVALID_CELL`.
3. If `calls_remaining == 0`, append canonical forced
   `STOP(BUDGET_EXHAUSTED)` and enter `TERMINAL` without dispatch.
4. Dispatch exactly one THINK call and decrement calls by one. Charge actual
   locked token accounting. Model absence classifies the provisional result as
   `MISSING_NO_RETRY`; there is no retry; continue at step 9.
5. Parse one complete `ppc5.op.v1` object. On failure, classify the provisional
   result as `PARSE_ERROR` and continue at step 9.
6. From a successfully parsed op name, attempt its logical debit before semantic
   validation: `QUERY` one read, `ACT` one action, `REQUEST_DREAM` one dream.
   Counters saturate at zero. A zero pre-debit counter classifies respectively
   `READ_BUDGET_EXHAUSTED`, `ACTION_BUDGET_EXHAUSTED`, or
   `DREAM_BUDGET_EXHAUSTED`; the attempted operation does not commit; continue
   at step 9.
7. Validate domains, references, branch/citation legality, prediction binding,
   and environment action validity, in that order. Return the first canonical
   error from the ordering in section 4.5; do not partially mutate; continue at
   step 9.
8. Form the repeat key from canonical `(semantic_prestate_hash,op,args)`, where
   `semantic_prestate_hash` excludes clocks, budgets, error history, and the
   repeat table. Increment its count. On count three, replace the requested op
   with canonical `DEFER(REPEAT_LIMIT)`; do not apply the requested op.
9. A provisional parse, budget, domain, reference, legality, action-validity,
   or THINK-model error increments the consecutive-error count. Counts one and
   two return the classified no-op/missing result. On count three, append
   canonical `DEFER(ERROR_LIMIT)` instead, reset the count to zero, and return
   `DEFERRED`. A validated repeat-limit result appends
   `DEFER(REPEAT_LIMIT)`, resets the error count, and returns `DEFERRED`;
   repeat-limit DEFER wins if both limits coincide.
10. Otherwise apply exactly one legal transition below, append exactly one
    operation event, reset the consecutive-error count, and return. IDs are
    allocated only by this commit.

The semantic state hash includes public world state, workspace, active branch,
subgoal/hypothesis/prediction status, opened records, citations, and unresolved
surprises. Thus mere budget/error changes cannot evade the repeat limit.

### 4.4 Legal transitions

| Operation | Sole state effect after its event is appended |
|---|---|
| `OPEN_SUBGOAL` | Allocate one child of `parent_id`, append it last among siblings, and make it the active leaf. |
| `QUERY` | Dispatch the READ provider exactly once. `FOUND` appends the returned record once to opened records; `NOT_FOUND` appends only the response event; failure statuses append only their canonical response/error event. |
| `FOLLOW` | Set the cited opened record as active focus and append the branch-to-record citation if absent. |
| `HYPOTHESIZE` | Allocate a `PROVISIONAL` hypothesis on the active branch and the listed record citations. |
| `PREDICT` | Replace the live prediction on the active branch with the new append-only prediction event; prior predictions remain history. |
| `ACT` | On a valid environment action, append its public transition and clear the live prediction. On `ACTION_INVALID`, environment and prediction are unchanged. |
| `REVISE` | Append `SUPERSEDED` for the source hypothesis, allocate one `PROVISIONAL` child, and append its citations atomically. |
| `BACKTRACK` | Close the active subgoal and its open descendants deepest-first; activate the most recently opened still-open sibling, else the still-open parent, else append `STOP(NO_VALID_ACTION)` and enter `TERMINAL`. |
| `REQUEST_DREAM` | Run section 5. Only valid publication replaces the active working-set view; the ledger never changes except by appended request/status/publication events. |
| `DEFER` | Append the reason; make no semantic-state change. |
| `STOP` | Append the reason and enter `TERMINAL`. |

Hypothesis status events are append-only. `HYPOTHESIZE` creates
`PROVISIONAL`; exact public support changes `PROVISIONAL` to `ACTIVE`; exact
public contradiction changes `PROVISIONAL|ACTIVE` to `CONTRADICTED`; `REVISE`
changes its source to `SUPERSEDED`; BACKTRACK/STOP changes open
`PROVISIONAL|ACTIVE` hypotheses on closed branches to `CLOSED`. No other source
or transition is legal, and terminal statuses never resurrect.

For every newly committed public environment observation atom, classify every
nonterminal hypothesis using the construction manifest's sealed, disjoint
`support_atoms` and `contradiction_atoms` sets: exact membership in the latter
is `CONTRADICTION`; else exact membership in the former is `SUPPORT`; else
`NEUTRAL`. Process observations then hypotheses in commit order. Model prose,
READ scores, DREAM state, hidden truth, and absence of an event are always
`NEUTRAL`.

### 4.5 Canonical results and error order

Every step returns exactly one closed object:

```json
{"code":"OK|code","contract":"ppc5.step.v1","phase":"RUNNING|TERMINAL","result":"APPLIED|NO_OP|DEFERRED|STOPPED|MISSING|INVALID_CELL","state_hash":"64hex"}
```

`code` is `OK` only for `APPLIED`. The complete non-DREAM precedence is:

```text
INVALID_CELL
CALL_BUDGET_EXHAUSTED
MISSING_NO_RETRY
PARSE_ERROR
READ_BUDGET_EXHAUSTED
ACTION_BUDGET_EXHAUSTED
DREAM_BUDGET_EXHAUSTED
UNKNOWN_DOMAIN_VALUE
UNALLOCATED_ID
STALE_REFERENCE
CLOSED_BRANCH_REFERENCE
WRONG_ANCESTRY
DUPLICATE_REFERENCE
CITATION_CYCLE
PREDICTION_REQUIRED
PREDICTION_ACTION_MISMATCH
ACTION_INVALID
REPEAT_LIMIT
ERROR_LIMIT
```

All codes are normalized exactly as written and expose no backend diagnostic.
The closed `code` domain is `OK`, the operation-reason enums in section 4.2,
and the error/status names in this section; no backend string is permitted.
`INVALID_CELL` and `CALL_BUDGET_EXHAUSTED` are terminal. `MISSING_NO_RETRY`
maps to `MISSING`; other nonterminal failures map to `NO_OP`; forced DEFERs map
to `DEFERRED`; STOP maps to `STOPPED`. Golden vectors MUST cover every state ×
input class, every precedence collision, initialization, and repeated terminal
call.

## 5. Total DREAM result table

A legal `REQUEST_DREAM` may reference only visible records, hypotheses, and
surprises on the active open branch. Its DREAM inference is a separate model
dispatch and therefore consumes one additional call and its actual locked token
charge; the dream debit was already charged by the request. If no call remains,
its status is `DREAM_CALL_BUDGET_EXHAUSTED`.

The DREAM model may emit only the existing closed `ABSTAIN` object or a
`PUBLISH` object with exactly `contract`, `status`, ordered unique
`retain_record_ids`, ordered unique `retain_hypothesis_ids`, ordered unique
`retain_subgoal_ids`, ordered unique `resolved_surprise_ids`, and
`next_focus_relation_id`. All IDs must occur in its allowed input slice and
satisfy the active-branch rule. Null, omitted, additional, duplicate, stale, or
wrong-kind values are semantically illegal.

Mandatory public ancestor closure is assembled before recency fill and is never
truncated. The same locked allowance is used in every assigned arm; realized
semantic output length need not match. The total status table is:

| First applicable case | Canonical status | State effect | Evidence class |
|---|---|---|---|
| Valid PUBLISH, nonempty retained-record list | `PUBLISHED` | Atomically append `DREAM_STATE`; replace active working view only | observed assigned outcome |
| Valid PUBLISH, empty retained-record list | `PUBLISHED_EMPTY` | Same publication rule; D1D selection is zero | observed assigned outcome |
| Valid ABSTAIN | `ABSTAIN` | Append status only; publish nothing | observed assigned outcome |
| Stale/closed/wrong-branch reference | `STALE_REFERENCE` | No publication | `MISSING` |
| Mandatory closure exceeds allowance | `CLOSURE_OVERFLOW` | No publication | `MISSING` |
| No remaining call for DREAM dispatch | `DREAM_CALL_BUDGET_EXHAUSTED` | No publication | `MISSING` |
| DREAM provider/model absence after dispatch | `DREAM_PROVIDER_FAILURE` | No publication, no retry | `MISSING` |
| Non-schema or semantically illegal output | `DREAM_PARSE_FAILURE` | No publication | `MISSING` |
| Assigned control has no required recipient-local match | `MATCH_UNAVAILABLE_POST_ASSIGNMENT` | No content installed | `MISSING` |
| Atomic append/view replacement fails or hashes disagree | `DREAM_PUBLICATION_FAILURE` | Roll back the whole publication | `RUN_INVALID` |

An unavailable match detected before assignment is `CONSTRUCTION_FAIL`, and
the cell is never assigned. After assignment, every row above remains in the
intention-to-treat denominator under the later locked missingness mapping. No
branch is reassigned, dropped, retried, or given authentic or mechanical
fallback content. A registered retained-item cut removes that item without
replacement; its changed realized count/tokens are part of the intervention.

## 6. Cue, score, and selection contract

### 6.1 Cue requests

Every request has fixed keys; inapplicable values are null:

```text
{"candidate_count":<N>,"candidate_table_hash":"64hex","contract":"ppc5.read.request.v1","cue_family":"EXACT|REVERSE|PARAPHRASE|PARTIAL","cue_id":"cue-00000000","cue_text":"string|null","max_returns":1,"object_id":"ev-00000000|null","relation_id":"public_relation_id|null","subject_id":"ev-00000000|null"}
```

`N` is the positive run-lock value and MUST equal the sealed table length;
`max_returns` is architecturally fixed at one. Field legality is exact:

| Family | Non-null fields | Null fields |
|---|---|---|
| `EXACT` | `subject_id`, `relation_id` | `object_id`, `cue_text` |
| `REVERSE` | `object_id`, `relation_id` | `subject_id`, `cue_text` |
| `PARAPHRASE` | `cue_text` | all three semantic IDs |
| `PARTIAL` | `cue_text` | all three semantic IDs |

`cue_id` and the exact UTF-8 `cue_text` bytes are presealed construction
content. Cue construction receives only the fields declared non-null for its
family (or their prospectively sealed public textual rendering). It MUST be
condition-blind and cannot read hidden truth, any withheld response field,
candidate order, or future outcomes. PARAPHRASE/PARTIAL bytes MUST contain
neither a complete candidate response nor a withheld ID. Mutating a withheld
field while allowed cue-side fields and the cue manifest are fixed MUST preserve
request bytes. Mutating target assignment while the common public acquisition
history is fixed MUST preserve candidate-table bytes.

### 6.2 Normative renderer

For each candidate, the scorer prefix bytes are exactly:

```text
PPC5_READ_V1\nREQUEST\n<canonical request bytes>CANDIDATE_RESPONSE\n
```

The target bytes are exactly one canonical section-3.1 response plus its LF.
Each FOUND row supplies one target; one additional synthetic `NOT_FOUND`
candidate supplies the canonical all-null NOT_FOUND response. There are exactly
`N+1` scores. Candidate strings differ only in target response bytes.

Tokenize prefix and target separately with the locked tokenizer using
`add_special_tokens=false`; concatenate their token-ID arrays. The scored span
is every target token and no prefix token. Zero target tokens, truncation,
automatic BOS/EOS insertion, or a reconstructed byte mismatch is
`READER_SPAN_INVALID`. For target tokens `t[0..k-1]`, score:

```text
sum_i log P(t[i] | prefix_tokens, t[0..i-1]) / k
```

using the run-locked inference dtype/backend and left-to-right order. Every
candidate is scored exactly once in manifest order; no cache-dependent early
exit is permitted.

### 6.3 Selection and controls

If candidate count, scan count, target reconstruction, or mapping disagrees,
the assigned cell is `RUN_INVALID`. If any of the `N+1` scores is NaN or
infinite, the assigned cell is `RUN_INVALID`. Otherwise select the greatest
score. An exact numerical tie containing NOT_FOUND selects NOT_FOUND; any other
tie selects the lexicographically least `candidate_id`. Emit the selected
candidate's section-3.1 response and nothing else.

`READER_LORA` uses the assigned compatible reader adapter.
`ADAPTER_OFF_CANDIDATE_ONLY` uses the identical clean base, prefix, tokenizer,
candidate targets, work, and reducer with no adapter. `WRONG_LIFE_ADAPTER` uses
the identical algorithm and only the single compatible donor adapter declared
by the sealed typed donor import. `READER_ROOT_SHUFFLE` receives a semantic table
constructed by the presealed fixed-point-free within-relation/token-stratum
permutation; it never receives root provenance at runtime. Failure to construct
that permutation before assignment is `CONSTRUCTION_FAIL`, with no fallback.

TEXT and GRAPH MUST scan the same N semantic rows plus NOT_FOUND and use this
same reducer and public envelope. Their provider-specific finite score
functions and indexes MUST be closed in their ratified baseline cell contracts;
an absent function is `CONSTRUCTION_FAIL`, not permission to imitate the reader
score or use early exit.

Canonical provider failures are:

```text
INVALID_CELL                         pre-dispatch integrity; no work charged
READER_COUNT_MISMATCH                RUN_INVALID
READER_SPAN_INVALID                  RUN_INVALID
READER_MAPPING_MISMATCH              RUN_INVALID
READER_NONFINITE                     RUN_INVALID
MISSING_NO_RETRY                     post-dispatch absence; MISSING
```

## 7. Evidence-only READ writer

SLEEP receives an ordered representative list, the closed public acquisition
ledger at one exact boundary, the two private provenance companions, the cue
manifest, the capacity from the run lock, and no probe/future/target truth.
It evaluates every selected representative and emits a private census entry.

After whole-input schema/hash validation, the first applicable per-root result
wins in this order:

```text
MISSING_PROVENANCE
NOT_ACQUIRE
ITEM_OPEN
AFTER_BOUNDARY
PROBE_OR_FUTURE
TARGET_DERIVED
NOT_PUBLIC_ENV_OBSERVATION
NOT_DIRECT_RELATION_ATOM
SOURCE_HASH_MISMATCH
STATUS_INELIGIBLE
DUPLICATE_ROOT_CLASS
```

An admissible atom is exactly `(record_id, subject_id, relation_id, object_id,
public_record_bytes)` committed by the environment in a closed ACQUIRE item no
later than the boundary. Model hypotheses, predictions, rationales, summaries,
DREAM bytes, scorer labels, confidence, agendas, imagined outcomes, descendant
claims, and any DECIDE/ACT/DREAM target can never establish or modify support.
Branch/hypothesis text is never a source atom. Final status is rechecked at the
boundary; a model proposal may at most select/group already admissible atoms
and cannot change this oracle.

For each admissible atom, render one row for each required cue-family fixture in
the sealed cue manifest. Its request table hash/count refer only to the sealed
acquisition-derived training semantic table, never a PROBE, future, or target
table. The input is the section-6.1 request/prefix. The target
is exactly the section-3.1 FOUND response for that atom, with loss zero on all
prefix tokens and one on all separately tokenized target tokens. Root IDs,
roles, scores, candidate IDs, condition labels, proposal bytes, and provenance
never occur in input, target, or loss mask. Missing or invalid required cue data
rejects that row as `CUE_INVALID`; exact duplicate `(cue bytes,target bytes)` is
stable-deduplicated as `DUPLICATE_ROW`. Rows are ordered by representative first
occurrence, cue-family order `EXACT,REVERSE,PARAPHRASE,PARTIAL`, then cue ID.

The writer is total:

| Case | Canonical SLEEP status | Effect |
|---|---|---|
| Valid rows within locked capacity | `READY` | One deterministic pass over every row; no cycling, truncation, oversampling, or padding |
| No valid rows | `VALID_EMPTY` | No training and no new adapter; retain prior published adapter/none |
| Rows exceed the preselection capacity | `CAPACITY_OVERFLOW` | No training or partial corpus; `MISSING` in ITT |
| Input/schema/source hash failure | `SLEEP_INVALID_CELL` | No training; `RUN_INVALID` |
| Trainer/provider absence before completion | `FAILED_SLEEP_MISSING` | Discard candidate artifact; retain prior adapter; `MISSING` |
| Non-finite loss/weights, recipe/count/hash mismatch | `FAILED_SLEEP_INVALID` | Discard candidate artifact; retain prior adapter; `RUN_INVALID` |
| Validation or atomic publication failure | `PUBLICATION_FAILED` | Roll back publication; retain prior adapter; `RUN_INVALID` |
| Validation and atomic remount succeed | `PUBLISHED` | Publish exactly one complete adapter and cold-remount it only in READ |

Realized roots, rows, target tokens, and optimizer updates are measured D1D
mediators, not matching variables. The primary D1D analysis MUST NOT condition
on, pad, or equalize them. Capacity is locked before selection; any separately
dose-normalized sensitivity must be prospectively named in the run lock.

## 8. Candidate-recognition claim and optional closed-book assay

The D1A claim ID is `PPC5_SUPPORTED_CANDIDATE_RECOGNITION`. Its maximum wording
is: “the assigned READ adapter causally improves selection of supported public
records conditional on an external full semantic candidate table.” The table
supplies complete answer semantics. PPC5 MUST NOT describe this as absorption,
transport, storage, reproduction, a stored worldview, or records written into
the adapter. Frozen-policy isolation is necessary but does not expand the
claim.

`PPC5_CLOSED_BOOK_RECORD_REPRODUCTION` is a separate optional assay and is
inactive unless separately deliberated, exactly ratified, run-locked, and added
to the claim dependency map. Its minimum contract is: cue-only input; no
candidate table/index/record bytes or retrieval tool in the process; one closed
`FOUND|NOT_FOUND` output containing the complete canonical record atom; exact
byte scoring plus false-memory, adapter-off, wrong-life, and cue-family controls;
and all-assigned-life analysis. Decoder/model/tokenizer/numeric settings belong
to that assay's run lock. Candidate-recognition success supplies no default,
gate, or evidence for this optional claim.

## 9. Canonical evidence-state precedence

Scientific evidence states are disjoint and ordered by construction/execution,
not by favorability:

```text
CONSTRUCTION_FAIL  required cell/artifact cannot be sealed before assignment
RUN_INVALID        assigned execution violates integrity or a required contract
MISSING            assigned outcome is absent under a declared total failure
VALID_NULL         valid locked analysis does not pass a positive gate
VALID_ADVERSE      valid locked analysis moves in the adverse direction
VALID_POSITIVE     valid locked analysis passes its literal conjunctive gate
```

`CONSTRUCTION_FAIL` prevents assignment. `RUN_INVALID` cannot be converted to a
null. `MISSING` remains in the ITT census and is handled only by the prospectively
locked mapping/limit. No retry, fallback, reassignment, per-protocol subset, or
post-result relabeling may move an observation to a more favorable state.

## 10. Acceptance-stage order

These stages are strict and irreversible for one byte set:

1. `pre_ratification_specification`: T01 exact standalone scope/hash authority
   and T19 fresh architecture deliberation dispose every issue; then the human
   ratifies the exact repaired architecture bytes and proposal-only scope.
   Before that decision, coding is forbidden.
2. `post_ratification_pre_static_seal_conformance`: implement only the ratified
   contracts; run deterministic/no-model conformance portions of T02R–T15R and
   the T16R run-lock-schema validator fixture. No model call is permitted.
3. `pre_model_execution`: populate and hash-bind every T16R run-lock field; obtain
   both dependency-audited T17R independent static seals; obtain the T20R fresh
   reviewer/author-advocate bundle; then obtain a separate exact human run
   ratification. All four are conjunctive and must bind the same hashes. Before
   the final decision, every model call, canary, training action, and behavioral
   execution is forbidden.
4. `runtime_validity`: during only that authorized run, execute T18R actual
   runtime perturbations and assignment/failure checks. Affected comparisons
   cannot advance unless T18R passes their locked validity gate.
5. `pre_scientific_claim`: T21R independently recomputes all-assigned ITT life
   values, statuses, and literal claim dependencies from frozen raw artifacts.
   Only then may the exact passing assay claim be released.

T16R therefore has two receipts: schema conformance at stage 2 and populated
run-lock authority at stage 3. T17R is evidence about frozen static construction,
not permission to execute. No stage authorizes learned THINK/DREAM, continual
learning, schema/compression, flywheel, parenting, asymptote, population, or
scaling claims, and no later stage cures a failure or missing prerequisite at an
earlier stage.
