# PPC5 v5r1 controls contracts — drafting aid only

Status: non-normative insertion draft. This file has no execution or
ratification authority. `MUST`, `MUST NOT`, and `SHALL` below are proposed exact
repairs for the next normative `protocol.md` and `change.json` bytes.

## 1. Small confirmatory design

PPC5 SHALL remain four separate assays. D1A tests candidate-conditioned record
recognition; D1B tests causal use of a presealed local path by frozen recurrent
cognition; D1C tests frozen same-model DREAM context reconciliation; D1D tests
frozen same-model DREAM selection of evidence for SLEEP. No assay may substitute
for another. The confirmatory experiment MUST use only the conditions in section
6 plus the assigned interventions in sections 4 and 5. Any additional baseline,
factor, or exploratory sensitivity MUST be labeled exploratory and MUST NOT enter
a PPC5 promotion gate.

Assignment for every life, item, target, context-pressure point, DREAM branch,
provider-return branch, donor, and condition MUST be committed before the first
model-visible byte for the affected unit. Every assigned unit remains in its
intention-to-treat universe.

## 2. DREAM context and DREAM-to-SLEEP projection

### 2.1 Frozen DREAM context treatment

DREAM is frozen same-model reconciliation, not a learned operation. One
`ppc5.dream.v1` call is made from one immutable pre-call snapshot. The call,
input bytes, decoding contract, logical allowances, and charged call/dream/token
budgets are identical across cloned D1C branches. Realized output length and
semantic cardinality are outcomes and MUST NOT be equalized.

The D1C branches are:

* `PUBLISH`: validate the authentic output and, only for valid `PUBLISH`, install
  its working set.
* `WITHHOLD`: quarantine the authentic output and install the presealed
  recipient-local deterministic-recency working set generated from the same
  pre-call snapshot under the same maximum record and token allowances.
* `MISMATCH`: quarantine the authentic output and install only the presealed
  recipient-local remap defined in section 3. No donor ID or donor content is
  exposed.
* `CUT(slot_id)`: derive from the valid authentic publication, remove exactly
  the registered retained decisive item without replacement, and make no other
  change. Its smaller realized count and token total are part of the
  intervention.

`CUT` is defined only for a prospectively sealed decisive retained slot. A
target lacking such a slot is ineligible before assignment; after assignment it
MUST NOT be replaced by a different slot or target.

### 2.2 Private root projection

Only the ordered `retain_record_ids` array in a valid authentic DREAM
`PUBLISH` may nominate D1D evidence. Hypothesis IDs, subgoal IDs, surprise IDs,
focus fields, request fields, ancestor closure, free-form text, and record IDs
not present in that array MUST nominate nothing.

`dream_to_sleep_projection.v1` is a private SLEEP/AUDIT receipt with this closed
shape:

```json
{"contract":"dream_to_sleep_projection.v1","dream_event_id":"ev-00000000","input_record_ids":[],"nominations":[{"input_index":0,"record_id":"rec-00000000","status":"ACCEPT|REJECT","reason":"ELIGIBLE|DUPLICATE_CLASS|MISSING_RECORD|NOT_CLOSED|NOT_ACQUIRE|PROBE_SOURCE|TARGET_DERIVED|STATUS_INELIGIBLE|NO_ELIGIBLE_CLASS_MEMBER","private_class_hash":"64hex|null","representative_record_id":"rec-00000000|null"}],"selected_record_ids":[],"status":"OK|RUN_INVALID"}
```

Projection is total and MUST execute in input-array order:

1. Validate each public record reference against the immutable DREAM prestate.
2. Through the private provenance companion only, obtain its source equivalence
   class.
3. Filter class members to closed, writer-eligible ACQUIRE public source records
   that are neither PROBE-derived, target-derived, nor finally status-ineligible.
4. If none remain, emit the single applicable rejection reason using the
   precedence shown in the enum above.
5. Otherwise select the lexicographically least eligible public source record
   ID as the representative.
6. Stable-deduplicate by private class: accept its first occurrence and reject
   later occurrences as `DUPLICATE_CLASS`.
7. Emit accepted representatives, in first-occurrence order, as
   `selected_record_ids`.

`private_class_hash`, rejection reasons, and the projection receipt MUST be
visible only to SLEEP and AUDIT. They MUST NOT alter DREAM inputs, provider
scoring bytes, public READ responses, THINK inputs, or training targets. An
invalid DREAM reference makes the projection `RUN_INVALID`; an otherwise legal
record that lacks eligible evidence is a recorded rejection, not substitute
evidence.

The D1D branches clone the same closed acquisition lineage:

* `DREAM_TO_SLEEP` supplies the projection's ordered accepted representatives.
* `PUBLISH_CUT` supplies the presealed recipient-local mechanical selection.
  For each authentic accepted slot, choose the unused eligible recipient root
  minimizing, in order, `(type_mismatch, absolute_token_count_difference,
  absolute_support_count_difference, absolute_acquisition_ordinal_difference,
  record_id)`, with `type_mismatch` required to be zero. Authentic selected
  classes are excluded. Failure to construct all slots before assignment is
  `CONSTRUCTION_FAIL`; no fallback exists.
* `PUBLISH_MISMATCH` supplies the recipient-local donor-rank remap in section 3.

Every branch reruns the same mechanical evidence gate and READ-row renderer.
DREAM bytes and foreign donor roots MUST never be training targets or writer
evidence.

## 3. External donors and recipient-local remapping

The confirmatory recipient-life sample and donor pool MUST be disjoint. Before
recipient assignment, `donor_fixture.v1` SHALL seal a one-to-one mapping with
exactly one immutable donor per recipient. A donor MUST NOT be reused, be a
confirmatory recipient, or receive from its recipient; reciprocal pairs and
cycles are forbidden.

```json
{"contract":"donor_fixture.v1","recipient_life_id":"opaque","donor_life_id":"opaque","allowed_artifacts":[{"control":"WRONG_LIFE_ADAPTER|D1C_MISMATCH|D1D_PUBLISH_MISMATCH","artifact_hash":"64hex","schema_hash":"64hex"}],"recipient_local_remap_hash":"64hex"}
```

`donor_import.v1` MUST name exactly one fixture, one control, one artifact hash,
and one recipient-local remap hash. The import allowlist is:

* `WRONG_LIFE_ADAPTER`: one architecture- and recipe-compatible donor adapter;
* `D1C_MISMATCH`: the donor's ordered retained-slot descriptors only;
* `D1D_PUBLISH_MISMATCH`: the donor's ordered within-stratum selection ranks
  only.

No donor ledger event, public ID, semantic record byte, root, answer, score,
target, prompt, or workspace byte may cross the boundary.

For D1C, the sealer MUST construct a bijection from donor slot descriptors to
distinct recipient-local eligible decoy IDs. Each mapped value MUST match the
slot's field type, cardinality, token envelope, and pressure class, and MUST
preserve legal recipient-local references after remapping. For D1D, each donor
within-stratum rank MUST select that rank from the recipient's own ordered
eligible-root stratum; selected roots MUST be recipient-local and distinct.
Rank overflow, incompatible adapter, or missing bijection detected before
assignment is `CONSTRUCTION_FAIL`. Detection after assignment receives
`POST_ASSIGNMENT_MATCH_FAILURE`; no reuse, reassignment, nearest match, or
authentic fallback is permitted.

Cold-reset noninterference applies to every ambient prior-life byte. Mutating
the single allowlisted donor artifact MUST change only its declared recipient
control input and is the sole intended donor dependence; mutating any unlisted
donor or prior-life byte MUST change nothing in recipient inputs or outputs.

## 4. Total DREAM treatment status and ITT

Every assigned DREAM branch MUST emit exactly one treatment status:

| Observed event | Canonical treatment status | Primary consequence |
|---|---|---|
| valid nonempty publication | `PUBLISH_NONEMPTY` | observed, scored |
| valid publication with no retained IDs | `PUBLISH_EMPTY` | observed zero-selection, scored |
| legal abstention | `ABSTAIN` | observed zero-selection, scored |
| invalid/stale/foreign reference | `STALE_REFERENCE` | `RUN_INVALID` |
| mandatory closure exceeds locked allowance | `CLOSURE_OVERFLOW` | `MISSING` |
| output parse/schema failure | `PARSE_FAILURE` | `MISSING` |
| provider failure after dispatch | `PROVIDER_FAILURE` | `MISSING` |
| donor/remap absence after assignment | `POST_ASSIGNMENT_MATCH_FAILURE` | `MISSING` |
| atomic publication failure | `PUBLICATION_FAILURE` | `MISSING` |
| capacity overflow | `CAPACITY_OVERFLOW` | `MISSING` |

Known infeasibility before assignment is `CONSTRUCTION_FAIL`, not a runtime
status. An integrity violation, forbidden import, wrong assignment, or status
that cannot arise under the ratified transition function is `RUN_INVALID`.
`MISSING` statuses use only the prospectively locked life-level missingness rule.
No status permits reassignment, branch deletion, target replacement, retry,
imputation from authentic content, or conditioning the primary analysis on
publication, nonempty selection, successful projection, or successful sleep.

All assigned branches remain in the ITT status census and reducer input. Equal
compute means equal prospective allowances and debit rules; it never means
padding or truncating realized semantic output.

## 5. Every-edge provider-return interventions

For every D1B target with decisive path edges `e[0..L-1]`, the sealer MUST
create `AUTHENTIC`, `CUT(e[i])`, and `TWIN(e[i])` for every `i`, plus one
`SHAM` branch using a presealed nonpath edge. `intervention_assignment.v1` is
committed before target prompt construction and contains target ID, life ID,
arm, edge ID or sham ID, exact triggering query key, authentic record ID,
substitute kind, substitute record ID if any, and hashes of canonical authentic
and substituted response bytes.

The provider always renders and scores all `N` semantic candidates plus
`NOT_FOUND` and completes ordinary deterministic selection first. A valid
assignment then acts after selection and before public emission, without
changing candidate rows, scores, scan order, work count, adapter, acquisition,
training, or global provider state:

* `AUTHENTIC`: emit the selected canonical response unchanged.
* `CUT(e)`: if and only if both the triggering query key and selected record ID
  equal the sealed edge, emit canonical `NOT_FOUND`.
* `TWIN(e)`: under the same exact match, emit the canonical public response for
  the presealed directional-twin record.
* `SHAM`: apply the identical substitution machinery to the sealed nonpath edge.

A provider scan/count/non-finite failure takes precedence and is `RUN_INVALID`;
an invalid assignment or response-hash mismatch is `RUN_INVALID`; ordinary
`NOT_FOUND` remains an observed provider outcome. The intervention MUST be
blind to whether the model queried, opened, cited, predicted from, or acted on
the assigned edge. No arm may be selected or repaired using the realized trace.

The registered causal directions are: each `CUT(e)` removes the authentic
action advantage; each `TWIN(e)` redirects action/value to the sealed twin
direction; `SHAM` preserves the authentic solution. Passing requires the
predeclared every-edge conjunction. Opening and citation order are adherence
and mediation outcomes only.

## 6. Reduced executable comparison set

The confirmatory baseline set is exactly:

```text
BASE_AGENT, FULL_CONTEXT, RAW_RAG, LINKED_TEXT, EXPLICIT_GRAPH,
DIRECT_ACTION_LORA, RAW_BATCH_LORA, READER_LORA
```

The causal/identity controls are exactly:

```text
ADAPTER_OFF_CANDIDATE_ONLY, WRONG_LIFE_ADAPTER, READER_ROOT_SHUFFLE,
ONE_SHOT_QUERY, OPEN_LOOP, AUTHENTIC, every CUT(edge), every TWIN(edge), SHAM
```

The removed `TARGET_STATE_ONLY`, `NATIVE_CONTEXT_THEN_TRUNCATION`,
`REFLECTION_LESSON_TEXT`, `ENDPOINT_LORA`, and `DIRECT_QA_LORA` cells are not
mandatory and their omission cannot be described as a favorable result.

All cells use the identical target state, action set, action scorer, frozen base
THINK/ACT weights, decoding, and public budgets except where a named control
removes one mechanism. Their closed dataflows are:

* `BASE_AGENT`: target state and ordinary current-item public state only; no
  acquisition corpus, provider, store, or adapter is mounted.
* `FULL_CONTEXT`: all writer-eligible acquisition `public_record_bytes`, ordered
  by `(acquisition_ordinal, record_id)`, are placed in the declared memory slot;
  no retrieval provider is mounted. The common locked input allowance MUST fit
  the complete payload or the dependent comparison is `CONSTRUCTION_FAIL`.
* `RAW_RAG`: embed the canonical cue renderer and every candidate's
  `public_record_bytes` with the later-hash-bound frozen embedding model; score
  all `N` by cosine similarity, also score the canonical `NOT_FOUND` candidate,
  reject zero-norm or non-finite values as `RUN_INVALID`, and apply the common
  tie rule before emitting `ppc5.read.v1`. Embedding-model identity is a later
  run-lock value; this full-scan cosine algorithm is not.
* `LINKED_TEXT`: the same semantic records plus only public subject/relation ID
  links are serialized as canonical text; exact public key lookup still scans
  all `N` and emits the common READ envelope.
* `EXPLICIT_GRAPH`: the same records are canonical
  `(subject_id,relation_id,object_id,record_id)` tuples; exact public key lookup
  scans all `N` and emits the common READ envelope.
* `DIRECT_ACTION_LORA`: train from clean base only on eligible acquisition
  state-to-observed-action rows, mount only in the terminal action-policy
  comparator process, and expose no READ provider. It is a policy-learning
  alternative and cannot support a memory-substrate claim.
* `RAW_BATCH_LORA`: train from clean base on the same eligible public acquisition
  examples rendered in chronological batches under the locked generic
  next-token recipe, mount only in its comparator policy process, and expose no
  READ provider. Unsupported, future, PROBE, target-derived, and scorer bytes
  receive zero loss.
* `READER_LORA`: train only canonical evidence-gated READ output spans, mount
  only in the isolated READ process, full-scan `N+1`, and never mount in
  THINK/DREAM/ACT.

Each mandatory cell MUST bind eligible source bytes, renderer and loss span,
mount, query/return and action interface, deterministic order/truncation rule,
clean-base lifecycle, and construction receipt. A missing or infeasible
mandatory cell makes only its dependent claim `CONSTRUCTION_FAIL`; omission,
renaming, post-result substitution, and fake padding are forbidden.

## 7. Dose, mediators, and resources

For the D1A/D1B trained-baseline comparison, the run lock MUST prospectively
match real positive target tokens, effective example touches, active trainable
parameter bytes, optimizer update count, clean-base rebuild, and publication
lifecycle across trained cells. Only loss-bearing supported target tokens count.
Prospectively specified deterministic cycling or down-selection is allowed only
when every sealed example receives the locked minimum coverage; synthetic,
unsupported, or loss-masked padding is forbidden. Infeasible matching is
`CONSTRUCTION_FAIL`.

For primary D1D ITT, the lock fixes selection and training capacity ceilings,
but the harness MUST NOT truncate, oversample, cycle, pad, or condition on
realized selected roots, admitted rows, target tokens, examples, or updates.
SLEEP makes one deterministic pass over all admitted rows if they fit the
preselection cap. Overflow emits `CAPACITY_OVERFLOW`, trains nothing, and
follows the locked missingness rule. Realized root count, admitted-row count,
positive target tokens, examples, optimizer updates, publication outcome, and
training cost are mediators/resource outcomes, not matching constraints. A
separately labeled dose-normalized sensitivity is permitted only if sealed
before execution and cannot replace the ITT result.

`resource_manifest.v1` MUST enumerate `(condition_id, owner_process_id,
artifact_hash, artifact_kind, realized_dtype, shape_or_length, padding_bytes,
retained_bytes, accounting_class)`. Primary retained bytes count every
condition-readable inference payload, semantic table, required metadata/index,
adapter tensor at realized dtype and padding, and process-private retained copy
exactly once for its owner. Common base and tokenizer bytes MUST be reported
both inclusive and marginal. Shared physical storage does not erase a readable
logical copy; aliases within one owner are counted once by artifact hash.
Transient cache/KV, construction and training FLOPs/time, optimizer state,
checkpoints, storage, latency, environment work, and failures are mandatory
secondary-ledger fields. Accounting rules and ownership are architecture bytes;
capacities, dtypes, and quantities are later run-lock bytes.

The D1A/D1B primary cross-substrate view MUST prospectively equalize total
active retained bytes. Non-readable reserved padding is allowed only when
declared, hashed, counted at realized size, and byte-invariant across targets;
it never counts as training dose or semantic payload. Failure to meet the
locked byte equality is `CONSTRUCTION_FAIL`. D1D instead equalizes only
preselection capacity: realized retained bytes after DREAM selection are a
reported resource mediator and MUST NOT be post-treatment padded or truncated.

## 8. All-assigned-target life-level analysis

No item, cue, edge, branch, pressure point, or donor is an independent
replicate. Independent recipient lives are the only sampling units. Every
assigned target and every canonical success/failure status MUST enter exactly
one raw life value. Per-protocol subsets based on correct query, complete path
opening/citation, valid publication, nonempty selection, admitted rows, or
successful training are descriptive only and MUST NOT promote a claim.

Before model execution, every contrast MUST include one closed
`life_reducer.v1` object:

```json
{"contract":"life_reducer.v1","contrast_id":"opaque","recipient_life_id":"opaque","assignment_universe_hash":"64hex","ordered_input_keys":[],"pairing_keys":[],"donor_fixture_id":"opaque|null","weights":[],"denominator_rule":"ENUM","zero_eligible_rule":"ENUM","status_map":[{"status":"ENUM","disposition":"VALUE|ZERO|MISSING|INVALID|CONSTRUCTION_FAIL"}],"nested_pair_rule":"ENUM","every_edge_rule":"ENUM","metric_transform":"ENUM","output_schema":"raw_life_value.v1","multiplicity_family":"opaque","promotion_consequence":"ENUM"}
```

The run lock MUST bind the exhaustive ordered inputs; deterministic weights;
denominator; zero-eligible behavior; within-life pairing and nested paired-item
handling; donor ID; status/missingness mapping; every-edge conjunction; metric
transform; numeric margins and thresholds; multiplicity family; and promotion
consequence. `every_edge_rule` MUST require all registered edges, not an average
over successful edges. `status_map` MUST contain every status allowed by the
ratified assay exactly once. Reducers MUST serialize their input-status census
and one raw value or canonical non-value status per life. T21 MUST recompute
every reducer byte-for-byte from the assignment manifests and raw events.

## 9. Literal claims and successor non-substitution

The machine-readable dependency graph SHALL contain only these release edges:

```text
D1A passing gates -> PPC5_SUPPORTED_CANDIDATE_RECOGNITION
D1B passing gates -> PPC5_CONNECTED_PATH_USE
D1C passing gates -> PPC5_DREAM_CONTEXT_VALUE
D1D passing gates -> PPC5_DREAM_SLEEP_SELECTION_VALUE
all four literal claims -> PPC5_FINITE_MECHANISM_ONLY
```

`PPC5_SUPPORTED_CANDIDATE_RECOGNITION` means adapter-conditioned selection from
externally supplied semantic candidates. It MUST NOT be reported as closed-book
storage, transport of complete record bytes, absorption, reproduction, or a
stored worldview.

D1C and D1D mean causal utility of frozen same-model reconciliation for context
or evidence selection. They MUST NOT be reported as learned DREAM. There is no
promotion edge from any PPC5 status or claim to learned THINK/DECIDE/DREAM,
closed-book storage, continual learning, retention across sleeps, lossy schema,
flywheel improvement, saturation/asymptote, parenting, population inheritance,
or scaling. Those claims remain `FORBIDDEN_SUCCESSOR_CLAIM` even when all PPC5
gates pass.

A future separately ratified PPC6 MUST decide and test whether and how READ and
learned DECIDE coexist in an integrated per-life artifact while preserving
evidence admission, probe quarantine, and final-ACT exclusion. PPC5 neither
selects nor authorizes that architecture.

## 10. Independent dual sealers

Exactly two no-model static sealers MUST independently produce every assignment,
role/split/ID manifest, donor fixture/remap, DREAM projection, provider
intervention, path/twin/sham oracle, baseline construction manifest, resource
manifest, transition golden vector, and scripted reducer closure.

They may share only: (a) the exact ratified normative bytes; (b) public schema
standards; (c) OS/runtime primitives; and (d) frozen raw input manifests. They
MUST NOT share project parser, canonicalizer, seed expander/RNG, matcher,
projection, generator, path oracle, transition, resource-accounting or reducer
code; project utility libraries; generated intermediate artifacts; source
authorship context; or outputs before both sealers commit hashes.

Each emits:

```json
{"contract":"sealer_provenance.v1","sealer_id":"opaque","author_or_fresh_agent_id":"opaque","normative_hash":"64hex","source_tree_hash":"64hex","dependency_lock_hash":"64hex","build_runtime_hash":"64hex","frozen_input_manifest_hash":"64hex","allowed_shared_inputs":[],"import_graph":[],"output_commit_hash":"64hex","no_generated_artifact_import":true,"no_shared_project_logic":true}
```

Each sealer MUST independently implement canonical JSON, seed expansion,
matching, projection, path/twin/sham construction, transitions, resource
accounting, and life-reducer golden vectors. T17 passes only if both provenance
receipts satisfy the allowlist and independently committed canonical outputs
agree exactly. Missing provenance, a forbidden dependency/import, precommit
output exchange, or any byte disagreement fails T17 without adjudication or
fallback. Neither sealer may be replaced by an additional sealer after outputs
are opened.
