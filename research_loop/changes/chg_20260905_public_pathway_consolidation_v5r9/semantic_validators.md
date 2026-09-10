# PPC5r9 pure semantic validators

Status: normative proposal. These are deterministic CPU/no-model rules for a
later ratified implementation. A schema-valid object can still fail any rule.
Validators return the first failure in the frozen order and never repair data.

## V01 — canonical object integrity

Recompute canonical JSON, contract/version domain, byte length where present,
self hash, every typed-reference target hash/type/run/role/ordinal, and NFC
strings. Reject generic manifests in semantic fields, unknown types, duplicate
keys, noncanonical rationals, hash self-ancestry, or cycles.
Authored registries must be `lifecycle_state=PROPOSAL_ONLY`; ratification and
runtime authority receipts must be `EXECUTED`. Schema validity, a proposal-only
artifact, or a `RATIFIED_DESIGN` artifact never grants execution authority.
For every `RAW_BYTE_MANIFEST`, recompute the exact raw-role class. Frozen
proposal-source roles are `PROPOSAL_ONLY` with no `run_id`; ratified generator
and entropy-spec source roles are `RATIFIED_DESIGN` with no `run_id`; generic
intake and generic architecture-ratification evidence are `EXECUTED` but
architecture-bound with no `run_id`; runtime corpus/entropy/model/tokenizer/
prompt/output/provider/fixture/seal/review/advocate/human-run/replay roles are
`EXECUTED` and require the exact consumer run's `run_id`. Reject a wrong role,
lifecycle, missing/extra run identifier, or same-run visibility ingress whose
target runtime manifest has a different run.

## V02 — truthful generic T01

Read only the generic `intake.state.json` bytes and bound generic code. Require
one architecture change, two distinct registered interpretations, one
critique, and one consensus; phase `human_required`; flags
`human_required=true`, `implementation_authorized=false`; and exactly one
`awaiting_consensus->human_required` history entry containing the recorded
source-state hash and exact consensus hash. Reject any architecture
ratification or PPC fixture/result/implementation/sealer artifact. Do not
claim or validate argv, exit status, stdout, or an atomic command transcript.

## V03 — temporal design/run-lock DAG

Topologically require:

```text
ARCHITECTURE_RATIFICATION_RECEIPT
 -> PRE_ENTROPY_DESIGN_LOCK
 -> ENTROPY_ACQUISITION_RECEIPT
 -> proposal traces and LIFE_SAMPLE_RECEIPTs
 -> SAFETY_KEY_RESOLUTION_MANIFEST and D1A_CONTROL_SET_MANIFEST
 -> POPULATED_RUN_LOCK
```

The architecture receipt must bind the exact proposal bytes, frozen consensus,
and verbatim human evidence while authorizing CPU/no-model implementation only.
Parse its generic human-ratification bytes under the frozen
`architecture_human_ratification.schema.json` hash. Require field-for-field
equality for ratification/change/state/consensus/human-required hashes,
ratifier, authority and decision statements, time, both scope arrays,
authorization-evidence path/hash/excerpt, and `implementation_authorized=true`.
The PPC receipt's proposal, interpretations, critique, and consensus hashes
must equal the frozen architecture ancestry; mirrored booleans confer nothing.
The design lock fixes ordinal memberships/templates and all analysis/dispatch
parameters. Entropy slices are disjoint and bound before decoding. Resolved
memberships/keys/controls equal their templates and realized identities.
Populated fields equal design fields. Reject booleans offered as timing proof,
back edges, redraws, replacement, content/outcome choice, or exhaustion
omission.

## V04 — controller totality and first failure

Enumerate the frozen reachable tuple universe. Exactly one controller
transition matches each tuple. Input error counts are 0..2; EQ_2 ERROR emits
count 3 and ERROR_LIMIT in both public and private terminal bytes. Result-level
queue effects cannot enqueue on error/missing/invalid/rejected results. Apply
the exact first-failure precedence from `machine_contract.md`.

## V05 — queue partition and terminal finalization

Reconstruct every slot. Each that reached QUEUED has exactly one later
FLUSHED XOR DISCARDED effect; rejected slots have none. Before terminal,
FINALIZE_QUEUE discards every and only outstanding queued slot in canonical
order, then one HARNESS_TERMINAL event occurs. Reject direct terminal with an
outstanding slot, missing/duplicate effects, re-finalization, or cause/order
divergence.

## V06 — transition and status closure

Recompute state-body -> event -> state-receipt order, prior head/state links,
typed cause cardinalities, exact debits, and one status mapping per reachable
raw result. Enforce construction-failure, run-invalid, missing, assigned-policy,
observed-zero, and observed-value semantics without retry or post hoc repair.

## V07 — D1A per-life controls

For each D1A sample ordinal, require one keyed per-life control receipt and
exact AUTHENTIC/WRONG_LIFE/BINDING_DERANGED ordering. Recompute every registered
match, disjointness, and derangement predicate. Manifest sample/life keys must
equal prospective D1A membership and populated samples. Reject singleton,
cross-life, duplicate, omitted, replacement, content-matched, or tainted
controls.

## V08 — D1B capability separation and causal emission

Recompute provider, route, nonce allocation, domain-separated commitment,
sanitized projection, emitted-byte equality, transition, public last_read, and
MODEL_VIEW. The only THINK influence from response treatment is emitted public
bytes, carried by the exact `VISIBILITY_ACCESS_RECEIPT` branch before the
matching MODEL_VIEW. Every runtime ingress source reference has the same run as
its consumer; architecture-bound claim text is the sole unbound source class.
The sanitized projection contains no typed reference or capability to
the privileged route; their relationship is auditable only through the shared
opaque commitment and separated audits. Controller consumes only emission. Require complete separate provider
and route audits. Holding emission fixed, privileged route/condition/source/
score/match/nonce/preimage changes must leave restricted input/output/debit/
status/timing identical. Changing emitted bytes may change later model input
and behavior.

## V09 — common seed and dispatch replay

For every call, common-seed assignment equals design allocation, entropy
slice, life sample, call role/ordinal, and dispatch seed. Recompute state body,
head, view, input bytes/tokens, raw output/tokens, debit, parsed operation,
event, and post-state. `COMPLETE_RUN_MANIFEST` contains the exact ordered set;
both cold replays retain and consume every view and seed assignment.
Immediately before each call, resolve one `DISPATCH_PREFLIGHT_RECEIPT`,
recompute PRE_MODEL authority, select exactly one allowed-dispatch row, and
compare model, adapter, tokenizer, prompt, data, seed-entry, model-view, and
run-package hashes. A DENY starts no process; a dispatch without one prior
PERMIT is invalid.

## V10 — DREAM/SLEEP noninterference

Enforce shared no-retry DREAM, prospective control capacities, public-only
inputs, sterile forbidden data, nominee-first admission, one-pass runtime-
matched READ rows, clean-base training, and total no-adapter continuations.
Recursive taint rejects condition labels, future/probe/target bytes, hidden
truth, cognition, scorer output, or DREAM prose reaching positive evidence,
writer, trainer, provider, THINK, or analysis outside an explicitly allowed
typed projection.

## V11 — life-level aggregation

For each gate/life, expected lower-unit keys come only from prospective
membership. Treatment/control observation sets must equal those keys exactly.
Apply the frozen within-life reducer once. Missing, invalid, incomplete,
duplicate, substituted, or cross-life evidence yields `Z_i=false` and
`missing=true`; it is never excluded. Paired N equals the number of distinct
assigned life/sample keys and never a lower-unit count.

## V12 — exact inference

Recompute canonical differences, strict-margin indicators, exact Binomial
tails, one-sided Clopper–Pearson brackets, D1A Bernoulli safety denominators,
missingness, assay IUT maxima, and Holm over exactly the four registered claim
IDs. Enforce all margin/threshold domains, tie order, divisors 4..1, monotone
stop, and equality-as-failure. The four-way intersection is not a fifth test.

## V13 — pointwise joint power

For each complete N-life construction support/partition row, verify typed
proposal/life/predicate/control predecessors, exact mass, success/exhaustion,
and applicable conditional release-power computation. Sum
`mass * success_indicator * conditional_lower_bound`; failed/uncovered mass is
zero. Reject global-power substitution, construction mismatch, uncovered-mass
credit, simulation, or an independence claim.

## V14 — deterministic resources and qualifications

Recompute inclusive, marginal, and physical-total resources from canonical
coverage keys with deterministic least-key ownership and componentwise
conservation. No resource value may enter efficacy, gates, Holm, power,
adjustment, conditioning, stratification, normalization, mediation, or rescue.
Require exact ordered claim segments: canonical literal, D1D-specific
descriptive-cost sentence where applicable, then global accepted-constructible
qualification. Reject omission, paraphrase, detachment, or reorder.
At every downstream boundary, recompute `claim_id` and the exact rendering
bytes through typed references. A dependency decision's rendering must equal
its referenced candidate rendering. A released package's rendering must equal
both its referenced candidate and dependency decision. Export and audit must
repeat the released bytes exactly. Reject cross-claim substitution, including
D1D-to-non-D1D or non-D1D-to-D1D swaps, even when every substituted rendering
is independently registry-valid.

## V15 — typed registry closure

Require exactly one self-hashed instance of each semantic registry named by
the contract. Every registered row, producer, consumer, type, role, ordinal,
cardinality, and order equals the corresponding schema/lock field. Raw byte
manifests confer no semantic authority.

## V16 — independent schema/inventory/visibility equality

Run three separately source-hashed extractors:

1. derive the 84 concrete typed source/projection/stage-ingress branches from
   `VISIBILITY_ACCESS_RECEIPT` in `contracts.schema.json`, without reading the
   registry constants;
2. derive the same producer/consumer edges from `object_inventory.json`
   without using extractor 1 or its intermediate table;
3. derive allowed projection/ingress edges from `visibility_contract.json`
   without using either prior extractor.

Compare exact canonical sets after applying an explicit frozen audit-only
exclusion registry. All 195 cells occur exactly once. Every allowed cell names
a concrete typed source field, projection, output field, consumer, ordinal,
and cardinality; forbidden cells name none. Reject self/backward ingress,
wrong-run runtime sources, registry-only pseudo-edges, or a projection not
materialized as a typed ingress receipt. MODEL_VIEW is retained by both
cold replays or by their exact shared complete-run manifest.

## V17 — exact finite fixtures

For each T02–T14, derive normative row IDs from its frozen axes and inclusion
predicate in canonical order. Independently derive oracle IDs without
importing/calling the normative enumerator. Require both sets, the frozen
materialized rows, exact positive/negative counts, one-field mutation set,
expected bytes/first failures, and two executor outputs to be identical. No
post-ratification row, axis, count, or expected-result choice is legal.
T13 and T14 are not exceptions: each gate consumes its matching source-
distinct A/B fixture-execution manifests and set-equality receipt. T13 fixture
execution may consume only the technical predecessors that T13 evaluates;
T14 fixture execution may consume only the two cold-replay predecessors and
other already-complete runtime evidence. Neither fixture path may consume the
gate result it is validating.

## V18 — authority and release DAG

Require exactly:

```text
architecture ratification -> design/entropy/realization/populated lock
-> T02..T12 -> CONFORMANCE -> seal pair/fresh review/advocate/joint power
-> T13 -> human run ratification -> PRE_MODEL authority -> per-dispatch
preflight -> runtime integrity/analysis/candidates -> two independent cold
replays -> one T14 -> one PRECLAIM authority edge -> release -> optional audit
```

T13 PASS requires CONFORMANCE PASS, both seals, fresh-review PASS,
non-overriding advocate, and power closure; it cannot consume run ratification
or PRE_MODEL authority. Human run ratification requires T13 PASS; PRE_MODEL
GRANT requires that exact ratification. Runtime integrity requires the exact
ordered set of prior PERMIT preflights and proves every denial launched no
process. Both replays consume the same passing runtime receipt and no release
bytes; T14 PASS requires both passing independent replays. PRECLAIM GRANT
requires T14 PASS, runtime PASS, and exactly five eligible candidate and five
passing dependency decisions, with one final-T14 predecessor only. Export can
consume only RELEASED claim packages; audit is strictly downstream.
Any missing, duplicate, stale, wrong-run/type/role/order/cardinality, back-edge,
or optional-audit ancestor fails.

## Global first-failure order

Across bundle validation, report only the first applicable code in this order:

```text
CANONICAL_INTEGRITY
T01_GENERIC_STATE
TEMPORAL_LOCK_DAG
REGISTRY_CLOSURE
FIXTURE_UNIVERSE
CONTROLLER_TOTALITY
QUEUE_CLOSURE
TRANSITION_STATUS
D1A_CONTROL_CLOSURE
D1B_CAPABILITY
SEED_DISPATCH_REPLAY
DREAM_SLEEP_TAINT
LIFE_AGGREGATION
EXACT_INFERENCE
JOINT_POWER
RESOURCE_QUALIFICATION
VISIBILITY_INVENTORY
AUTHORITY_DAG
```
