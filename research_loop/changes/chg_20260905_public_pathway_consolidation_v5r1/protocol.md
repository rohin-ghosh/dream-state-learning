# PPC5r1 — standalone public-pathway consolidation protocol

Status: proposal only. These bytes authorize no implementation, model call,
training action, canary, GPU execution, or scientific claim. PPC1–PPC5, Fable
organisms, prior notes, reviews, and runs are provenance only; none supplies an
inherited field, default, permission, test, or claim.

## 1. Authority, scope, and scientific boundary

The ratified architecture bytes bind the schemas, enum domains, algorithms,
visibility modalities, state transitions, failure precedence, treatment
semantics, claim wording, claim dependencies, and acceptance-stage ordering in
this document and `change.json`.

A later `run_lock.json` must bind, without changing those algorithms: exact
model, tokenizer, checkpoint, trainer, prompt-file hashes, decoding and training
recipe, all numeric budgets and capacities, sequence limits, LoRA rank and
placement, dtype, candidate count, resource quantities, recipient-life count,
power inputs, margins, aggregation functions, missingness limits, assignment
seeds, runtime limits, and stopping rules. Every later-bound field must be
populated, hash-bound, independently reviewed, and exactly human-ratified before
any model call. Changing an architecture-bound item requires a new architecture
change.

PPC5r1 asks four separate questions:

```text
D1A CANDIDATE RECOGNITION
    Can an isolated evidence-gated reader-LoRA causally improve selection of a
    supported public record when every complete candidate record is supplied?

D1B CONNECTED PATH USE
    Can a frozen recurrent thinker causally use every local return in a sealed
    decisive path to improve a later action?

D1C DREAM CONTEXT VALUE
    Does frozen same-model DREAM reconciliation preserve decision-relevant
    working state and improve subsequent work relative to equal-allowance
    withholding, mismatch, and retained-item cuts?

D1D DREAM→SLEEP SELECTION VALUE
    Do DREAM-selected public roots produce more useful evidence-gated READ
    writes and downstream action than mechanical and mismatched selections?
```

No assay substitutes for another. PPC5r1 freezes THINK/ACT and trains only an
isolated READ adapter. This prevents direct policy cloning from masquerading as
acquired experience or connected use. The immediate successor trains typed
DECIDE outputs while withholding final ACT targets; that is the first learned-
THINK test. Later separately ratified stages test repeated sleeps, learned
DREAM, schema compression, long-life flywheels, parenting, and populations.

## 2. One model, three verbs, one learned life artifact

* **THINK** is a recurrent public operation loop over current world state,
  public workspace, typed provider returns, outcomes, and logical budgets.
* **DREAM** is the same frozen model used under a different public context to
  select and reconcile existing working state. Its publication is reversible,
  non-evidentiary, and never loss-bearing.
* **SLEEP** is an offline evidence gate, deterministic renderer, trainer,
  validator, and atomic publisher. It alone changes the per-life LoRA.

There is no separately trained thinker, dreamer, planner, verifier, scorer, or
sleep policy. The raw public ledger is append-only. Dropping an item from active
context never deletes it. External text and graph stores are comparison
treatments. In PPC5r1 the adapter is mounted only in an isolated READ-provider
process and never in THINK, DREAM, or ACT. This is an identification
intervention, not a claim that the eventual organism needs two models or two
learned life states.

## 3. Canonical bytes, information modalities, and roles

All JSON schemas are closed (`additionalProperties:false`). Serialization is
UTF-8 canonical JSON with sorted keys, compact separators, declared array order,
and one trailing LF. Invalid data is never partially parsed. Harness IDs match
`^(it|br|sg|hy|ev|rec)-[0-9]{8}$`, allocate monotonically only after a legal
commit, contain no condition/model substring, and remap freshly per probe.

For every information item at every stage exactly one modality applies:

| Modality | Permission |
|---|---|
| `VISIBLE` | Only its declared canonical bytes may enter the model/scorer input or declared public output. |
| `DERIVED_ONLY(p)` | Raw bytes are unavailable; only deterministic ratified projection `p` may enter. Holding `p` fixed must preserve every stage input, choice, and output byte. |
| `PRIVATE_INTERNAL(use)` | A non-model harness may read it only for the named routing/integrity/audit use. It may not enter prompts, scores, selection keys, loss-bearing bytes, public IDs/errors, or timing branches. |
| `FORBIDDEN` | No stage component may read it or a proxy. Holding allowed inputs fixed, mutation must preserve all stage choices, transitions, and output bytes. |

The formal matrix is in `change.json`; each `hidden` cell names its
`PRIVATE_INTERNAL` use and each `derived_only` cell names its projection.
Noninterference tests compare semantic choices as well as serialized bytes.
They fail if a private/forbidden mutation changes a scorer input, selected
candidate, rejection reason, public response, model-visible error, or next
state.

Before model-visible bytes exist, each item receives one immutable private role:

```text
ACQUIRE  public within-item outcomes; closed eligible atoms may write later
PROBE    public within-item outcomes; forever writer-ineligible
STATIC   no model; construction and sealing only
```

Every model-visible role string is `WORK_ITEM`. Roles cannot affect prompts,
budgets, clocks, filenames, errors, IDs, or interfaces. Only closed ACQUIRE
events committed before the sleep boundary may write. PROBE scores and outcomes
remain quarantined until audit. Confirmatory effects are computed on PROBE
items.

## 4. Public records and private provenance

The public semantic candidate table contains exactly:

```text
(candidate_id, record_id, subject_id, relation_id, object_id,
 public_record_bytes)
```

It contains no equivalence/root value, role, condition, target membership,
score, truth label, or probe/future field. `candidate_id` is provider-private
and never occurs in a public response.

The sole public READ response is:

```json
{"contract":"ppc5.read.v1","object_id":"ev-00000000|null","record_id":"rec-00000000|null","relation_id":"public_relation_id|null","status":"FOUND|NOT_FOUND|MISSING_NO_RETRY|INVALID_CELL","subject_id":"ev-00000000|null"}
```

For `FOUND`, all four ID fields are non-null and equal one semantic candidate.
For every other status, all four are null. The response never exposes rank,
score, provider, condition, latency, candidate ID, provenance, or diagnostics.

`root_provenance.v1` is a private SLEEP/AUDIT companion keyed by `record_id`.
Each entry contains exactly the record ID, its public source-event ID, and an
opaque equivalence-class ID. `writer_eligibility.v1`, keyed by source-event ID,
contains immutable role, item-close event, source commit ordinal, mechanically
known source-channel kind, target-derived quarantine bit, and final eligibility
bit. Neither companion contains truth, answers, scores, condition labels, or
target identity. Entries and class members are lexicographically ordered.

Root provenance is forbidden at THINK and DREAM and at READ candidate
rendering, tokenization, scoring, tie-breaking, selection, and emission. A
provider receives only the semantic table. Holding that table fixed, every
companion relabeling must leave provider inputs, scores, choices, responses,
and THINK state byte-identical.

## 5. Total public THINK machine

### 5.1 State and initialization

The machine has phases `INITIAL`, `RUNNING`, and `TERMINAL`. Successful
`start(item, construction_manifest, run_lock)` verifies schemas and hashes,
allocates the manifest root subgoal, initializes empty ordered collections,
makes the root the only active open branch, copies locked budgets into remaining
counters, and enters `RUNNING`. Any pre-model schema/hash/cell/domain failure
enters `TERMINAL(INVALID_CELL)` without dispatch. Calls after `TERMINAL` return
the same terminal object byte-for-byte and consume/append nothing.

Closed `ppc5.state.v1` has exactly: `contract`, `phase`, `item_id`,
`world_state`, `workspace_record_ids`, `active_subgoal_id`, `subgoal_rows`,
`hypothesis_rows`, `live_prediction`, `opened_record_ids`, `focus_record_id`,
`citation_edges`, `unresolved_surprise_ids`, `prior_public_transition`,
`budgets`, `repeat_rows`, `consecutive_error_count`, `latest_error_codes`,
`ledger_hash`, `next_id_ordinals`, and `terminal_reason`. Nullable fields are
explicit null. `budgets` contains remaining `calls`, `reads`, `actions`,
`dreams`, and `tokens`; `next_id_ordinals` contains `branch`, `subgoal`,
`hypothesis`, `event`, and `record`. Environment state and transition objects
are closed construction-manifest schemas, not free JSON.

### 5.2 Closed operation domain

One THINK dispatch may emit exactly one `ppc5.op.v1` object and one operation:

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

Omitted/additional/mistyped fields, unknown finite-domain values, duplicates,
unallocated/stale IDs, closed branches, and wrong ancestry are illegal. `ACT`
requires a live prediction for the same action on the active ancestry. Legal
actions and all finite symbol domains are frozen construction-manifest content;
their numeric sizes are run-lock values. Prospective citation cycles are
illegal; diamonds are legal.

### 5.3 Step precedence and charging

For every step, the first applicable branch wins:

1. Return a frozen terminal object if already terminal.
2. Verify state, cell, model, tokenizer, adapter mount, and manifest hashes.
   Failure terminates as `INVALID_CELL` before dispatch.
3. With no call remaining, append forced `STOP(BUDGET_EXHAUSTED)` and terminate.
4. Dispatch exactly one THINK call, decrement one call, and charge actual
   locked tokens. Absence becomes `MISSING_NO_RETRY`; there is no retry.
5. Parse exactly one complete operation. Failure becomes `PARSE_ERROR`.
6. A successfully named `QUERY`, `ACT`, or `REQUEST_DREAM` attempts its logical
   debit before semantic validation. A zero pre-debit counter yields its
   canonical budget error; counters saturate at zero.
7. Validate finite domains, references, ancestry/branch/citation legality,
   prediction binding, then environment action validity, in that order.
8. Compute repeat key from canonical `(semantic_prestate_hash,op,args)` where
   the semantic hash excludes clocks, budgets, errors, and repeat table. The
   third equal request from an unchanged semantic prestate becomes
   `DEFER(REPEAT_LIMIT)` and the requested operation is not applied.
9. Parse/budget/domain/reference/legality/action/model errors increment the
   consecutive-error count. Errors one and two append their canonical no-op or
   missing result. Error three instead appends `DEFER(ERROR_LIMIT)`. A forced or
   model-emitted DEFER enters `TERMINAL`; no subsequent call is allowed.
10. Otherwise apply exactly one legal transition, append exactly one operation
    event, reset consecutive errors, and return. IDs allocate only on commit.

Logical invalid ACT consumes an action debit but cannot change world state.
REQUEST_DREAM consumes one dream debit; the additional DREAM dispatch consumes
one additional call and actual tokens.

### 5.4 Legal transitions

| Operation | State effect |
|---|---|
| `OPEN_SUBGOAL` | Allocate one child of `parent_id`, append last among siblings, activate it. |
| `QUERY` | Dispatch READ once. FOUND appends/open the returned record once; NOT_FOUND appends only its response; failure appends its canonical status. |
| `FOLLOW` | Make the opened record the focus and add branch→record citation if absent. |
| `HYPOTHESIZE` | Allocate a PROVISIONAL hypothesis on the active branch with listed citations. |
| `PREDICT` | Replace the live prediction with an append-only prediction event; prior predictions remain history. |
| `ACT` | Valid action appends the public transition and clears the prediction; invalid action changes neither. |
| `REVISE` | Atomically supersede the source, allocate one PROVISIONAL child, and add its citations. |
| `BACKTRACK` | Close active subgoal and open descendants deepest-first; activate latest open sibling, else open parent, else append STOP(NO_VALID_ACTION) and terminate. |
| `REQUEST_DREAM` | Execute section 6; only a valid publication replaces the active working view. |
| `DEFER` | Append reason and terminate as deferred. |
| `STOP` | Append reason and terminate as stopped. |

Hypothesis statuses are append-only. `HYPOTHESIZE` creates `PROVISIONAL`;
exact public support changes it to `ACTIVE`; exact public contradiction changes
`PROVISIONAL|ACTIVE` to `CONTRADICTED`; `REVISE` makes the source `SUPERSEDED`;
branch closure makes open `PROVISIONAL|ACTIVE` hypotheses `CLOSED`. Terminal
statuses never resurrect.

For each newly committed public observation atom, the sealed construction
manifest's disjoint support/contradiction sets classify every nonterminal
hypothesis in commit order: contradiction membership wins, then support, else
neutral. Model prose, provider scores, DREAM state, hidden truth, and absence of
an event are always neutral.

### 5.5 Canonical results

Each step returns exactly:

```json
{"code":"OK|code","contract":"ppc5.step.v1","phase":"RUNNING|TERMINAL","result":"APPLIED|NO_OP|DEFERRED|STOPPED|MISSING|INVALID_CELL","state_hash":"64hex"}
```

Complete error precedence is:

```text
INVALID_CELL, CALL_BUDGET_EXHAUSTED, MISSING_NO_RETRY, PARSE_ERROR,
READ_BUDGET_EXHAUSTED, ACTION_BUDGET_EXHAUSTED, DREAM_BUDGET_EXHAUSTED,
UNKNOWN_DOMAIN_VALUE, UNALLOCATED_ID, STALE_REFERENCE,
CLOSED_BRANCH_REFERENCE, WRONG_ANCESTRY, DUPLICATE_REFERENCE,
CITATION_CYCLE, PREDICTION_REQUIRED, PREDICTION_ACTION_MISMATCH,
ACTION_INVALID, REPEAT_LIMIT, ERROR_LIMIT
```

Backend diagnostics are never public. Golden vectors cover initialization,
every operation, every state×input class, every precedence collision, and
repeated terminal calls.

## 6. Frozen DREAM and working-context treatments

A legal `REQUEST_DREAM` receives one immutable pre-call snapshot containing
only requested visible records, visible hypotheses/surprises on the active
branch, full public ancestor closure, and then most-recent causal public events
within one allowance. Mandatory closure is assembled first and never truncated.

DREAM emits either closed `ABSTAIN` or closed `PUBLISH` with exactly:
`contract`, `status`, ordered unique `retain_record_ids`, ordered unique
`retain_hypothesis_ids`, ordered unique `retain_subgoal_ids`, ordered unique
`resolved_surprise_ids`, and `next_focus_relation_id`. Every ID must be in the
allowed input slice and obey active-branch constraints. DREAM cannot create a
claim, fact, action, query, record, evidence atom, or loss-bearing byte.

Valid PUBLISH atomically appends `DREAM_STATE` and replaces only the working
view. All ledger events remain addressable. Resolving a surprise changes only
workspace status. Later contradictions append; history is never rewritten.

Every assigned branch remains in intention-to-treat analysis. The total status
table is:

| First applicable event | Status | Effect | Evidence state |
|---|---|---|---|
| valid PUBLISH, retained records nonempty | `PUBLISH_NONEMPTY` | publish working view; D1D projection may select | observed |
| valid PUBLISH, retained records empty | `PUBLISH_EMPTY` | publish working view; D1D zero selection | observed |
| legal ABSTAIN | `ABSTAIN` | publish nothing; zero selection | observed |
| stale/foreign/wrong-branch output reference | `STALE_REFERENCE` | no publication | MISSING |
| mandatory closure exceeds allowance | `CLOSURE_OVERFLOW` | no publication | MISSING |
| no call for DREAM dispatch | `DREAM_CALL_BUDGET_EXHAUSTED` | no publication | MISSING |
| provider/model absent after dispatch | `PROVIDER_FAILURE` | no retry/publication | MISSING |
| schema/semantic parse failure | `PARSE_FAILURE` | no publication | MISSING |
| required recipient match absent after assignment | `POST_ASSIGNMENT_MATCH_FAILURE` | no content installed | MISSING |
| atomic append/view/hash failure | `PUBLICATION_FAILURE` | roll back | RUN_INVALID |

Known infeasibility before assignment is `CONSTRUCTION_FAIL`. No branch is
reassigned, dropped, retried, or given authentic fallback content. Equal compute
means equal prospective allowance and debit rules, not equal realized semantic
length. A registered retained-item cut removes its item without replacement.

D1C clones the pre-call snapshot into:

* `PUBLISH`: install valid authentic output.
* `WITHHOLD`: quarantine authentic output and install the prospectively sealed
  recipient-local deterministic-recency set under the same maximum allowances.
* `MISMATCH`: quarantine authentic output and install only the recipient-local
  typed remap defined in section 9.
* `CUT(slot_id)`: from valid authentic publication, remove exactly one
  prospectively registered decisive retained slot without replacement.

An item without a sealable decisive slot is ineligible before assignment;
after assignment neither slot nor target may be replaced.

## 7. READ cue, scoring, selection, and writer

### 7.1 Cue and request

Every provider request has fixed keys; inapplicable values are null:

```text
{"candidate_count":N,"candidate_table_hash":"64hex","contract":"ppc5.read.request.v1","cue_family":"EXACT|REVERSE|PARAPHRASE|PARTIAL","cue_id":"cue-00000000","cue_text":"string|null","max_returns":1,"object_id":"ev-00000000|null","relation_id":"public_relation_id|null","subject_id":"ev-00000000|null"}
```

EXACT exposes subject+relation; REVERSE exposes object+relation; PARAPHRASE and
PARTIAL expose only presealed cue text. Cue construction is condition-blind and
receives no withheld response field, candidate order, truth, or future outcome.
Paraphrase/partial text contains no complete response or withheld ID. `N` is a
positive run-lock value equal to sealed table length; `max_returns` is one.

### 7.2 Reader renderer and selector

For each FOUND candidate and the synthetic all-null NOT_FOUND candidate, prefix
bytes are exactly:

```text
PPC5_READ_V1\nREQUEST\n<canonical request bytes>CANDIDATE_RESPONSE\n
```

Target bytes are exactly one canonical section-4 response plus LF. Tokenize
prefix and target separately with locked tokenizer and
`add_special_tokens=false`, concatenate IDs, and score every target token and no
prefix token. Zero target tokens, truncation, implicit BOS/EOS, or byte
reconstruction mismatch is `READER_SPAN_INVALID`. Candidate score is mean
left-to-right target-token log probability. All `N+1` candidates are scored
exactly once in manifest order with no early exit.

Count/mapping/reconstruction mismatch or any nonfinite score makes the assigned
cell `RUN_INVALID`. Otherwise choose greatest score; an exact tie containing
NOT_FOUND selects NOT_FOUND, and any other tie selects lexicographically least
`candidate_id`. Emit only the public response.

`READER_LORA` uses the assigned reader adapter. `ADAPTER_OFF_CANDIDATE_ONLY`
uses the identical clean base and algorithm without an adapter.
`WRONG_LIFE_ADAPTER` uses only the assigned compatible donor adapter.
`READER_ROOT_SHUFFLE` uses a presealed fixed-point-free permutation of public
object/record targets within exact relation/token strata; runtime sees no root
provenance. Failure to seal a derangement is `CONSTRUCTION_FAIL`.

TEXT, GRAPH, and RAG scan the same `N` semantic rows plus NOT_FOUND, use their
ratified finite selectors, and emit the same public envelope. Normalized
provider failures are `INVALID_CELL`, `READER_COUNT_MISMATCH`,
`READER_SPAN_INVALID`, `READER_MAPPING_MISMATCH`, `READER_NONFINITE`, and
`MISSING_NO_RETRY`.

### 7.3 DREAM-to-SLEEP projection

Only ordered `retain_record_ids` from a valid authentic PUBLISH nominate D1D
roots. Hypotheses, subgoals, surprises, focus, request fields, free-form bytes,
and ancestor closure nominate none.

`dream_to_sleep_projection.v1` executes privately and totally:

1. Validate each retained ID is unique, public, DREAM-visible, and present in
   private provenance, in emitted order.
2. Within its equivalence class retain only members committed by the boundary
   from closed ACQUIRE items, direct public environment-observation atoms,
   non-target/probe/future lineage, and final-status eligible.
3. Reject using first applicable reason:
   `MISSING_RECORD`, `NOT_DREAM_VISIBLE`, `NOT_ACQUIRE`, `ITEM_OPEN`,
   `AFTER_BOUNDARY`, `PROBE_OR_FUTURE`, `TARGET_DERIVED`,
   `NOT_DIRECT_PUBLIC_ATOM`, `STATUS_INELIGIBLE`, `EMPTY_CLASS`.
4. Otherwise choose lexicographically least eligible public source record.
5. Stable-deduplicate representatives by first occurrence; later equivalents
   receive `DUPLICATE_CLASS`.

The private receipt contains the ordered representatives and per-input status.
Empty/partially rejected selections are valid realized outcomes. No provenance,
representative, or rejection detail returns to THINK or DREAM.

### 7.4 Evidence-only SLEEP writer

SLEEP receives the selected representatives, closed acquisition ledger at one
exact boundary, private companions, sealed cue fixtures, and a run-locked
capacity. It receives no probe/future/target truth. For every representative it
applies this first-failure order:

```text
MISSING_PROVENANCE, NOT_ACQUIRE, ITEM_OPEN, AFTER_BOUNDARY,
PROBE_OR_FUTURE, TARGET_DERIVED, NOT_PUBLIC_ENV_OBSERVATION,
NOT_DIRECT_RELATION_ATOM, SOURCE_HASH_MISMATCH, STATUS_INELIGIBLE,
DUPLICATE_ROOT_CLASS
```

An admissible atom is exactly `(record_id,subject_id,relation_id,object_id,
public_record_bytes)` committed by the environment in a closed ACQUIRE item.
Hypotheses, predictions, rationales, summaries, DREAM bytes, scorer labels,
confidence, agendas, imagined outcomes, descendant claims, and any DECIDE/ACT/
DREAM target never establish or modify support.

For each admissible atom the writer renders every required sealed cue-family
fixture. Input is the exact runtime request/prefix; target is the exact FOUND
response. Loss is zero on prefix and one on separately tokenized target tokens.
Root IDs, roles, scores, candidate IDs, condition labels, model proposal bytes,
and provenance never occur in input, target, or loss mask. Rows order by root
first occurrence, cue-family `EXACT,REVERSE,PARAPHRASE,PARTIAL`, then cue ID.
Duplicate `(cue bytes,target bytes)` rows stable-deduplicate.

Writer statuses are total:

| Case | Status | Effect |
|---|---|---|
| valid rows within capacity | `READY` | one deterministic pass; no cycling/truncation/oversampling/padding |
| no valid rows | `VALID_EMPTY` | no training/new adapter; retain prior/none |
| rows exceed preselection capacity | `CAPACITY_OVERFLOW` | no partial training; MISSING in ITT |
| schema/source/hash failure | `SLEEP_INVALID_CELL` | no training; RUN_INVALID |
| trainer/provider absent | `FAILED_SLEEP_MISSING` | discard candidate; retain prior; MISSING |
| nonfinite/recipe/count/hash mismatch | `FAILED_SLEEP_INVALID` | discard candidate; retain prior; RUN_INVALID |
| validation/publication failure | `PUBLICATION_FAILED` | roll back; retain prior; RUN_INVALID |
| validation + cold remount succeed | `PUBLISHED` | publish exactly one complete adapter in READ only |

Realized roots, rows, positive tokens, examples, updates, publication, and cost
are D1D mediators/outcomes, never post-treatment matching variables.

## 8. D1B path world and provider-return intervention

Each target has one sealed unique minimal decisive length-2/3 path over directly
witnessed atoms and no budget-feasible alternative. Target handles and complete
combinations never occur in acquisition, writer, or training bytes. Correct
action requires composing the path rather than one record or passive signature.

For every decisive edge `e[i]`, assignment before target prompt construction
creates `AUTHENTIC`, `CUT(e[i])`, and `TWIN(e[i])`, plus one `SHAM` on a nonpath
edge. Provider scoring completes normally. After selection and before public
emission, without changing candidates, scores, work, adapter, training, or
global state:

* AUTHENTIC emits the selected response.
* CUT emits canonical NOT_FOUND iff query key and selected record equal the
  assigned edge.
* TWIN emits the sealed directional-twin response under the same exact match.
* SHAM runs identical substitution machinery on its nonpath edge.

Invalid assignment/response hash or provider integrity failure is RUN_INVALID;
ordinary NOT_FOUND is observed. Intervention is blind to whether the thinker
queried, opened, cited, predicted from, or acted on the edge. Each cut must
remove the authentic registered action advantage, each twin redirect its
registered action/value direction, and sham preserve it. Passing requires the
predeclared every-edge conjunction.

Ordered openings/citations are adherence and mediation only; they never define
the analyzed subset. `ONE_SHOT_QUERY` commits every query before returns but
permits recurrent post-return thought. `OPEN_LOOP` commits the entire operation
and action sequence before any return/outcome, after which no model call occurs.

## 9. D1C/D1D donor controls and selection controls

Confirmatory recipients and donors are disjoint. Before recipient assignment,
one immutable donor is sealed per recipient. A donor is never reused, is not a
recipient, receives nothing from its recipient, and belongs to no reciprocal
pair or cycle.

The typed allowlist is exact:

* `WRONG_LIFE_ADAPTER`: one architecture/recipe-compatible donor adapter.
* `D1C_MISMATCH`: donor ordered retained-slot descriptors only.
* `D1D_PUBLISH_MISMATCH`: donor ordered within-stratum selection ranks only.

No donor ledger event, public ID, semantic bytes, root, answer, score, target,
prompt, or workspace crosses the boundary. D1C maps slot descriptors bijectively
to distinct recipient-local decoys matching field type, cardinality, token
envelope, and pressure class. D1D maps donor rank to recipient-local eligible
roots in the same sealed stratum. Rank overflow, incompatible adapter, or
missing pre-assignment bijection is `CONSTRUCTION_FAIL`; post-assignment absence
is `POST_ASSIGNMENT_MATCH_FAILURE`; there is no fallback.

D1D clones one closed acquisition lineage into:

* `DREAM_TO_SLEEP`: authentic projected representatives.
* `PUBLISH_CUT`: recipient-local mechanical selection matching each authentic
  slot by `(type, token-count distance, support-count distance, acquisition-
  ordinal distance, record_id)`, excluding authentic classes.
* `PUBLISH_MISMATCH`: recipient-local roots chosen by donor within-stratum ranks.

All branches rerun the same evidence gate and row renderer. Foreign roots and
DREAM bytes never become evidence. Assignment for every life, item, target,
pressure point, branch, donor, condition, and edge is committed before the
first affected model-visible byte. Every assigned unit remains ITT.

## 10. Reduced confirmatory comparisons

The mandatory baseline conditions are exactly:

```text
BASE_AGENT, FULL_CONTEXT, RAW_RAG, LINKED_TEXT, EXPLICIT_GRAPH,
DIRECT_ACTION_LORA, RAW_BATCH_LORA, READER_LORA
```

Causal/identity controls are exactly:

```text
ADAPTER_OFF_CANDIDATE_ONLY, WRONG_LIFE_ADAPTER, READER_ROOT_SHUFFLE,
ONE_SHOT_QUERY, OPEN_LOOP, AUTHENTIC, every CUT(edge), every TWIN(edge), SHAM
```

No removed or unlisted baseline is required or may be claimed as beaten.

* `BASE_AGENT`: current-item public state only; no acquisition corpus, provider,
  store, or adapter.
* `FULL_CONTEXT`: every eligible acquisition public record in
  `(acquisition_ordinal,record_id)` order in the memory slot; no provider. The
  common allowance must fit all bytes or its dependent comparison fails
  construction.
* `RAW_RAG`: frozen run-locked embedding model embeds the canonical cue and all
  N public records plus canonical NOT_FOUND; cosine full scan, common tie rule,
  common envelope; zero-norm/nonfinite is RUN_INVALID.
* `LINKED_TEXT`: canonical record text plus public subject/relation links;
  deterministic full scan and exact public-key score.
* `EXPLICIT_GRAPH`: canonical `(subject,relation,object,record)` tuples;
  deterministic full scan and exact public-key score.
* `DIRECT_ACTION_LORA`: clean-base training only on eligible acquisition
  state→observed-action rows; mounted only in terminal action comparator; no
  READ provider.
* `RAW_BATCH_LORA`: clean-base generic next-token training on the same eligible
  public acquisition examples in chronological batches; unsupported/future/
  PROBE/target/scorer bytes have zero loss; mounted only in comparator policy.
* `READER_LORA`: exact evidence-gated READ output spans; mounted only in READ;
  full scan of N+1.

Every cell binds eligible source bytes, renderer/loss span, mount, interface,
order/truncation, clean-base lifecycle, and construction receipt. Missing or
infeasible mandatory cells make only dependent claims `CONSTRUCTION_FAIL`;
omission, substitution, and fake padding are forbidden.

## 11. Dose, resources, reducers, and literal claims

For trained D1A/D1B comparisons, the run lock prospectively matches real
positive target tokens, effective example touches, active trainable parameter
bytes, optimizer updates, clean-base rebuild, and publication lifecycle.
Deterministic cycling/down-selection is allowed only if presealed and every
example gets minimum coverage. Unsupported or masked padding never counts.

Primary D1D fixes only selection/training capacity ceilings. It does not pad,
truncate, oversample, cycle, or condition on realized selected/admitted rows.
Overflow trains nothing. A separate dose-normalized sensitivity is allowed only
if prospectively run-locked and cannot replace ITT.

`resource_manifest.v1` enumerates condition, owner process, artifact hash/kind,
realized dtype, shape/length, padding bytes, retained bytes, and accounting
class. Count every condition-readable payload, candidate table, required index/
metadata, adapter tensor, padding, and process-private retained copy once per
owner. Report common base/tokenizer both inclusive and marginal. Shared physical
storage does not erase logical readable copies; within-owner aliases count once
by hash. Cache/KV, construction/training FLOPs/time, optimizer state,
checkpoints, storage, latency, environment work, and failures are mandatory
secondary fields. D1A/D1B primary resource-matched comparisons equalize active
retained bytes; D1D reports realized bytes as mediators.

Independent recipient lives are the only sampling units. Every assigned item,
cue, edge, branch, pressure point, donor, and canonical status contributes to
exactly one raw life value. Each contrast's later `life_reducer.v1` must bind
exhaustive ordered inputs, denominators, zero-eligible behavior, within-life and
nested pairing, donor ID, every-edge conjunction, status/missing mapping,
metric transform, margins, thresholds, multiplicity family, and promotion
consequence. Trace-adherent subsets are descriptive only.

Evidence states are disjoint:

```text
CONSTRUCTION_FAIL  required artifact cannot be sealed before assignment
RUN_INVALID        assigned execution violates integrity/contract
MISSING            assigned outcome absent under a declared total failure
VALID_NULL         valid locked analysis misses positive gate
VALID_ADVERSE      valid locked analysis moves adversely
VALID_POSITIVE     valid locked analysis passes its literal conjunction
```

No retry, fallback, reassignment, post-result relabeling, or per-protocol subset
may improve an evidence state.

Literal release graph:

```text
D1A gates -> PPC5_SUPPORTED_CANDIDATE_RECOGNITION
D1B gates -> PPC5_CONNECTED_PATH_USE
D1C gates -> PPC5_DREAM_CONTEXT_VALUE
D1D gates -> PPC5_DREAM_SLEEP_SELECTION_VALUE
all four -> PPC5_FINITE_MECHANISM_ONLY
```

D1A may say only: “the assigned READ adapter causally improves selection of
supported public records conditional on an external full semantic candidate
table.” Candidate semantics reside externally, so PPC5r1 cannot say storage,
transport, absorption, reproduction, or stored worldview. Adapter-off,
wrong-life, and root-shuffle must remove the registered effect; false-memory and
abstention gates must pass. FULL_CONTEXT/TEXT/GRAPH are oracle/reference
ceilings: READER_LORA must satisfy the prospectively locked noninferiority
margin where a substrate comparison is claimed, but need not outperform exact
symbolic lookup.

D1B requires life-level ITT authentic action advantage, every-edge cut removal,
every-edge twin redirection, sham preservation, no replacement path, and the
registered one-shot/open-loop sensitivities. Frozen-policy isolation and trace
adherence are necessary controls, never sufficient causal evidence.

D1C requires PUBLISH to beat WITHHOLD and MISMATCH on registered state and
downstream measures and each decisive retained-item cut to remove the benefit.
D1D requires DREAM_TO_SLEEP to beat mechanical and mismatch branches under
all-assigned ITT on registered writer, recognition, path, and action outcomes.

No PPC5r1 status promotes learned THINK/DREAM, closed-book storage, continual
learning, retention across sleeps, lossy schema, flywheel, asymptote,
parenting, population inheritance, or scaling. A separately ratified optional
closed-book assay would need cue-only input, no table/index/retrieval process,
exact record generation, and false-memory/adapter-off/wrong-life controls.

## 12. Resets, independent sealers, and acceptance stages

Each life cold-resets model process, base, adapter, corpus, workspace, ledger,
external stores, candidate tables/indexes, cache/KV, RNG streams, IDs,
environment, filenames, and output directory. Only the exact typed donor import
may intentionally cross lives. Mutating any unlisted prior-life byte changes no
recipient input/output; mutating the allowlisted donor artifact changes only its
declared treatment input.

Exactly two no-model sealers independently generate all role/split/ID manifests,
donor maps, DREAM projections, path/twin/sham oracles, provider interventions,
baseline/resource manifests, transition golden vectors, and reducer closures.
They may share only ratified normative bytes, public schema standards, OS
primitives, and frozen raw inputs. They may not share project parser,
canonicalizer, RNG/seed expansion, matcher, projection, path oracle, transition,
resource/reducer code, project utilities, intermediate artifacts, authorship
context, or outputs before both commit. Provenance receipts bind source tree,
dependency lock, build runtime, inputs, import graph, and committed outputs.
Any forbidden dependency or byte disagreement fails the seal.

Acceptance order is strict for one immutable byte set:

1. `pre_ratification_specification`: standalone hashes/scope and fresh
   interpretations, critique, and consensus; then exact human architecture and
   proposal-scope ratification. Before it, implementation is forbidden.
2. `post_ratification_pre_static_seal_conformance`: implement only ratified
   contracts and run deterministic CPU/no-model conformance plus the run-lock
   schema fixture. No model call.
3. `pre_model_execution`: populate/hash-bind run lock; obtain two dependency-
   audited static seals; obtain fresh reviewer plus author-side advocate; obtain
   separate exact human run ratification. All bind identical hashes. Before the
   final decision, model calls, canaries, training, and behavioral execution are
   forbidden.
4. `runtime_validity`: only within the authorized run, execute real runtime
   perturbations and assignment/failure checks. Affected comparisons cannot
   advance unless valid.
5. `pre_scientific_claim`: independent audit recomputes all-assigned ITT life
   values, statuses, and literal dependencies from frozen raw artifacts.

Current ratification, if eventually granted, authorizes only isolated PPC5r1
contract implementation, deterministic CPU/no-model fixtures, and exactly two
independent static no-model sealers. It authorizes no model call, canary, LoRA
training, GPU work, behavioral treatment, or scientific claim.

## 13. Successor ladder

```text
PPC6 TEACHABILITY
  Train typed DECIDE rows while excluding final ACT targets. Test held-out
  action changes and operation-order/outcome-binding shuffles.

PPC7 STREAM
  Repeated sleeps with new, old, and cross-era panels; test retention and
  continuing acquisition.

PPC8 SCHEMA
  Prospective DREAM commitments, later independent support, fresh-cohort
  composition utility at fixed bytes, and episodic-detail controls.

PPC9 FLYWHEEL
  On-policy epistemic action, repeated mediation, utility-gym transfer, and
  improvement-versus-lifetime curves.

PPC10 PARENTING
  Transferable learning priors, wrong-parent controls, learning acceleration,
  autonomy, asymptote, outgrowability, and population inheritance.
```

PPC5r1 answers only whether the finite public experience→DREAM→SLEEP→READ→
recurrent action pathway exists cleanly enough to make those stages
scientifically interpretable.
