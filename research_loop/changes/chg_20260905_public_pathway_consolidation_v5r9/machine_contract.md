# PPC5r9 canonical machine contract

Status: proposal only. Numeric run values are supplied only by a later exact
human-ratified run lock. No defaults in code have authority.

## 1. Canonical bytes and references

Canonical JSON uses UTF-8, NFC strings, sorted keys, compact separators,
integer counters, no NaN/Inf, and one terminal LF. Each top-level object has a
unique contract string and self-hash field. Its digest is:

```text
SHA256(contract_utf8 || NUL || "9" || NUL || artifact_type_utf8 || NUL ||
       canonical_json(object_without_self_hash) || LF)
```

A typed reference fixes run/architecture identity where applicable, role,
ordinal, artifact type, and SHA-256. Generic byte manifests may identify only
raw code, prompts, renderers, model/tokenizer weights, or opaque blobs; they
never establish a semantic role. No object includes its own digest in its
preimage, and the semantic reference graph must be acyclic.

## 2. State/event order

For every non-genesis transition:

```text
pre_state_receipt
  -> operation/result and typed causes
  -> post_state_body
  -> transition_event
  -> post_state_receipt(ledger_head = transition_event hash)
```

The post-state body excludes its transition event, new ledger head, and state
receipt. The event binds prior event/head, pre-state, exact ordered cause refs,
operation/result/debits, queue effects, and post-state body. Genesis uses a
fixed domain-separated EMPTY_LEDGER_HEAD. Terminal state retains the final
event as ledger head and launches no further dispatch.

## 3. Public view and private controller

The public state contains only arm-neutral task/world bytes, visible records,
last emitted READ response, live prediction, last public outcome, budgets,
public phase/index, call ordinal, consecutive-error count, latest public
error, prior public transition summary, legal actions, and operation-schema
hash. The renderer combines its verified state body with the matching ledger
head to create `MODEL_VIEW` immediately before dispatch.

The private controller holds opaque run/life/cell IDs, concrete indexed phase,
sealed schedules and limits, full debit state, outstanding queue IDs, and
typed refs to the last operation/result. It may receive an
`INTERVENTION_EMISSION_RECEIPT` to know that a public response completed. It
may never receive privileged route data or a pre-emission projection.

Nonterminal dispatch states admit consecutive-error counts 0, 1, or 2.
Success resets the count; missing results preserve it; an ordinary ERROR at 0
or 1 increments it. An ERROR at 2 sets both public and private terminal count
to exactly 3 and normalizes to ERROR_LIMIT.

## 4. One-operation dispatch

THINK output is exactly one bare JSON operation from READ, PREDICT, ACT, or
STOP. Every physical model attempt consumes one preassigned typed common-seed
entry and its frozen token/call debit, including missing, token-limit, and
parse-error outcomes. No retry is legal. First failure precedence is:

```text
INTEGRITY -> PREDISPATCH_BUDGET -> MISSING_CALL -> TOKEN_LIMIT ->
PARSE_ERROR -> LOGICAL_ALLOWANCE -> DOMAIN -> REFERENCE -> PREDICTION ->
SCHEDULE -> PROVIDER_MISSING -> ENVIRONMENT_INVALID -> SUCCESS
```

Exactly one controller transition must match each reachable tuple of assay,
program, phase, index relation, guard, accepted result, input error count, and
queue state. Zero or multiple matches is RUN_INVALID.

## 5. Result-level queue semantics

Queue effects belong to result transitions, never controller rows. A success
may enqueue or flush as specified. ERROR, missing, invalid, and rejected
results may not create a queued request/commitment.

Before any terminal state, `FINALIZE_QUEUE` computes the exact outstanding set
of QUEUED slots. If empty, terminalization is direct. Otherwise it emits one
ordered QUEUE_DISCARD transition and one `QUEUE_EFFECT_RECEIPT(effect=
DISCARDED)` for every and only outstanding slot, then emits one
HARNESS_TERMINAL transition. Already FLUSHED/DISCARDED slots are unchanged;
REJECTED slots receive no effect. The union of FLUSHED and DISCARDED slots
equals the set that ever reached QUEUED, with empty intersection and exact
one-effect cardinality.

## 6. D1B privileged and public paths

The common provider is condition-blind. For each request it produces an
authentic provider receipt. A privileged router applies exactly one sealed
AUTHENTIC/CUT/TWIN/SHAM choice at the target key or authentic pass-through on
a valid non-target read. Zero target matches or multiple matches is
RUN_INVALID; non-target zero-match is `OFF_PATH_AUTHENTIC_PASS_THROUGH`.

For every route, a privileged nonce allocator consumes a unique 32-byte slice
that is disjoint from model/common-seed entropy. The route commitment is
`SHA256(domain || nonce || canonical_privileged_route_body)`. Only the opaque
commitment and arm-neutral public bytes cross into the sanitized projection.

The typed public path is exactly:

```text
PRIVILEGED_ROUTE_RECEIPT (privileged)
  -> SANITIZED_RESPONSE_PROJECTION (opaque commitment + public bytes only)
  -> INTERVENTION_EMISSION_RECEIPT
  -> VISIBILITY_ACCESS_RECEIPT(INTERVENTION_EMISSION_TO_PUBLIC_VIEW)
  -> PUBLIC_STATE_SNAPSHOT.public_view.last_read
  -> MODEL_VIEW

PRIVILEGED_NONCE_ALLOCATION + PRIVILEGED_ROUTE_RECEIPT
  + SANITIZED_RESPONSE_PROJECTION
  -> ROUTE_LINEAGE_AUDIT_RECEIPT (downstream witness only)
```

The projection consumes the privileged route directly; no route-lineage audit
is a prerequisite or capability on the causal forward path. The controller
consumes only the emission receipt. Provider and route audits remain separate,
complete, downstream privileged collections retained by runtime-integrity and
cold-replay manifests. Holding emitted public
bytes fixed, no route/condition/source/score/match/nonce/preimage mutation may
change any restricted input, output, debit, status, or timing class.

## 7. Typed seed and call closure

`COMMON_SEED_ENTRY_RECEIPT` binds the design lock, entropy slice,
life-sample receipt, run/life/sample IDs, call role/ordinal, and seed. Every
model dispatch consumes exactly one such receipt plus its matching MODEL_VIEW
and life sample. The dispatch closure proves identity of state body/head,
rendered bytes, input/output token IDs, raw output, budgets, parsed operation,
transition, and post-state.

`COMPLETE_RUN_MANIFEST` retains all required calls and views in canonical
run/life/sample/call order. Both cold replays consume it and reconstruct the
same closures from predecessor bytes.

Before every model/tokenizer/embedding/training or behavioral dispatch, a
typed `DISPATCH_PREFLIGHT_RECEIPT` recomputes the exact PRE_MODEL authority
chain and matches one allowed-dispatch row against the immediate model,
adapter, tokenizer, prompt, data, seed-entry, model-view, and run-package
hashes. A DENY launches no process. A dispatch without exactly one prior
PERMIT is invalid. `RUNTIME_INTEGRITY_RECEIPT` closes the ordered preflight,
dispatch, view, route/provider-audit, and complete-run sets before analysis or
replay can support release.

## 8. DREAM and SLEEP

DREAM receives only the sealed causally prior public slice, eligible public
record IDs, goal/world state, live prediction, and capacity. One no-retry
same-model call yields PUBLISH, PUBLISH_EMPTY, ABSTAIN, INVALID, or MISSING.
One authentic result is shared across D1C/D1D paired policy clones. Recency and
permuted controls use their prospectively fixed capacity even when DREAM is
empty or missing.

SLEEP first applies the assigned root policy, then the same evidence gate.
Only direct public ACQUIRE evidence can be admitted. Canonical dedup/order and
capacity precede one-pass runtime-matched READ-row rendering. Clean-base
training, validation, and atomic publication run once; no retry or fallback is
legal. Empty roots, no admitted roots, and TRAIN_FAILED continue downstream
with no adapter. D1D executes every sealed provider and action endpoint under
all statuses.

## 9. Status semantics

Required preassignment artifact absence is CONSTRUCTION_FAIL and blocks run
authority. Post-seal absence/mismatch is RUN_INVALID. Missing model/provider/
DREAM attempts are endpoint-local missing failures with no retry. Valid empty,
abstain, no-root, no-admitted-root, TRAIN_FAILED, and integrity-clean no-action
paths are assigned policy outcomes, not missing. No-action has normalized
action value zero. Successful provider/action endpoints retain their measured
values. Each reachable raw result maps to exactly one status, continuation,
observation/missing effect, and terminal reason under `STATUS_REGISTRY`.

## 10. Complete per-life aggregation

For gate g and sample i, `LIFE_GATE_AGGREGATE` consumes the prospective
membership entry and exact complete ordered lower-unit keys in both arms. It
requires set equality with observations in `COMPLETE_RUN_MANIFEST`, applies
the registered within-life reducer, and emits:

```text
treatment_value, control_value, d_i, Z_i, missing
```

If any required lower unit is missing, invalid, duplicated, substituted, or
cross-life, descriptive values are null, Z_i=false, and missing=true. Paired
gate results consume only these aggregates. N equals the number of distinct
prospectively assigned sample ordinals, not their lower-unit counts.

## 11. D1A control closure

Each per-life D1A control receipt consumes exactly three ordered origin/corpus
pairs plus the wrong-life, derangement, and dose/opportunity proofs. The
run-level control manifest contains one keyed receipt per D1A sample ordinal
and proves exact membership equality with D1A assignments and populated life
samples. The manifest—not a singleton—is required by construction support,
power, locks, seals, T13, replays, preclaim authority, and release.

## 12. Exact analysis and joint power

All arithmetic uses canonical reduced rationals. Strict superiority and
noninferiority indicators, exact Binomial tails, one-sided Clopper–Pearson
bounds, safety, missingness, assay intersection-union maxima, and four-member
Holm step-down are computed from LIFE_GATE_AGGREGATE rows. Missing required
evidence is failure. Equality to a margin or threshold does not pass.

Every construction support row names typed proposal/life/control/predicate
evidence, exact mass, success/exhaustion status, and the conditional
complete-release power applicable to that same construction. The joint bound
is the exact pointwise mass sum in `protocol.md`; failed/uncovered mass is
zero. Global substitution, simulation, and independence assumptions are
forbidden.

Resources are mandatory descriptive downstream costs only and cannot affect
analysis or release. The exact D1D-specific and global qualifications are
bound as ordered claim-rendering segments.

## 13. Registries, fixtures, and independent equality

Typed self-hashed registries are authoritative for controller transitions,
transition causes, status, visibility, gates, claims, resources, allowed
dispatch, authority, fixtures, and object inventory. Fixed named schema fields
replace redundant generic role registries.

Each T02–T14 `FIXTURE_SPEC` is frozen before intake and contains exact axes,
inclusion rules, canonical row keys, one-field mutations, expected bytes or
first failure, and counts. A separately source-hashed oracle enumerates the
expected set without importing the normative enumerator. Two independent
post-ratification executors must produce identical complete row results.

Schema edges are extracted from the actual typed
`VISIBILITY_ACCESS_RECEIPT` stage-ingress branches, inventory edges from the
independently materialized producer/consumer bindings, and policy edges from
the visibility contract. The three canonical 84-edge sets must be byte equal;
none may be a registry-only pseudo-edge, self-edge, backward ingress, or
wrong-run source. The visibility matrix remains exactly 195 cells. Audit-only
edges are explicit exclusions, not silently ignored.

## 14. Authority and release

The sole stage order is the DAG in `protocol.md`. T02--T12 reduce into one
typed CONFORMANCE receipt. Fresh review consumes that conformance result and
both seals. T13 PASS requires their resolved PASS states and is the final
technical premodel result; it does not consume run ratification or PRE_MODEL
authority. Human run ratification consumes passing T13. PRE_MODEL authority
consumes that exact human receipt and is revalidated by preflight before every
dispatch.

Runtime reduction first writes one passing runtime-integrity receipt, then a
claim-blind analysis bundle and five candidate plus five dependency decisions.
Two independent predecessor-only cold replays consume the same runtime
integrity and no release bytes. One T14 result consumes exactly those two
receipts and their independence proof. PRECLAIM GRANT has exactly one passing
final-T14 predecessor and requires runtime PASS plus all five eligible/pass
decision pairs. Release consumes authority once. Export consumes only a
RELEASED package; optional audit consumes release+export, repeats the exact
inseparable rendering, and has no authority.
