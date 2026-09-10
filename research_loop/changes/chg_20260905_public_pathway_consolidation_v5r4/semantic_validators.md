# PPC5r4 semantic validators

Status: normative proposal. These are pure, total validators over already
materialized bytes. They perform no model, tokenizer, embedding, trainer,
environment, network, CPU-behavioral, or GPU call. `FAIL(code)` rejects the
whole subject; it never coerces, repairs, retries, or substitutes a default.

Two independently source-hashed implementations must return byte-identical
canonical outputs or the same typed first-failure code for every registered
fixture.

## 1. Common rules

`validate_schema(x,T)` applies the exact closed schema for type `T` in
`contracts.schema.json`; missing, extra, wrongly typed, nonfinite, duplicate,
or out-of-order fields fail. `validate_hash(x,T)` recomputes the domain tag and
self-hash field declared for `T` in `object_inventory.json`. A digest under the
wrong type/domain fails even when payload bytes match.

`validate_ref(ref, registry, bundle)` requires a declared role, exact ordinal,
expected artifact type, existing target, matching self hash, and exact role
cardinality. `validate_blob` additionally re-reads bytes inside the sealed
bundle, rejects path traversal/symlinks/devices, and recomputes byte length and
raw SHA-256. Arrays with semantic order must be strictly increasing by their
declared key; set-like arrays must be sorted and unique.

Opaque IDs must match the run-lock grammar, be allocated monotonically only
after their source commitment, and contain none of the case-folded forbidden
condition/provider/arm substrings. Runtime IDs are never stable condition
codes.

## 2. State/event/controller closure

`validate_genesis(body, controller, receipt)` requires state ordinal zero,
phase INITIAL, no event, the registered empty-ledger head, exact controller
hash, and exact body/receipt hashes.

`validate_transition(pre,event,post_body,post_receipt)` requires:

1. post ordinal equals pre ordinal plus one;
2. event prior hash equals pre ledger head and event pre-state hash equals the
   pre receipt hash;
3. controller-before/after, envelope/result, queue, provider, intervention,
   action, and lineage roles equal the exact registry for the event cause;
4. every debit follows the first-applicable order in `machine_contract.md`,
   never increases, and differs by exactly the executed operation;
5. event binds `post_body.body_hash` before the event hash is computed;
6. post receipt binds the post-body hash and `ledger_head=event_hash`;
7. no object contains a digest that occurs inside its own preimage.

`validate_terminal_replay` requires byte-identical stored terminal body, event,
and receipt; unchanged budgets/event count; no dispatch/preflight/provider;
and no new queue effect.

`validate_controller` executes the exact total row for D1A, every D1B program,
D1C, or D1D. D1C/D1D use the run-locked `behavior_read_slots`; every one-shot
error advances; D1B AUTHENTIC alone retains its valid-request advancement rule.
Zero slots is valid. Every reachable state has exactly one successor or one
terminal. No implementation-selected default row exists.

For every `QUEUED` slot, `validate_queue_coverage` requires exactly one effect:
FLUSHED XOR DISCARDED. FLUSHED requires provider/intervention/public-event
bindings and forbids a discard reason. DISCARDED requires a reason and forbids
provider/intervention/public-event bindings. REJECTED slots have no effect.
Effects are in slot order and cover all and only queued slots.

## 3. Provider, intervention, path, and visibility closure

`validate_semantic_table` requires complete member rows, unique candidate and
record IDs, strict candidate-ID order, and finite canonical response sequences.
`validate_provider` recomputes mean response-token log probability, EOS rule,
fp32 determinism, one half-even quantization to signed micro-units, argmax, and
candidate-ID tie break. Empty tables yield NOT_FOUND. Malformed tables are
CONSTRUCTION_FAIL before assignment and RUN_INVALID after seal.

`validate_path_proof` independently enumerates all simple directed paths within
the READ budget in `(length, edge_id_tuple)` order. It proves every nonempty
proper subset of the registered path insufficient, the full set sufficient,
and every alternate enumerated path insufficient. Every edge has a distinct
raw source-event preimage. For every edge it recomputes CUT, the unique
lexicographically selected parity-matched reversing TWIN, and the unique
lexicographically selected parity-matched outcome-preserving nonauthentic SHAM.

`validate_intervention` recomputes exactly one privileged match, then proves
the restricted projection and response stage contain only the fields allowed
by `visibility_contract.json`. Shared schemas and algorithms for causal rows
are byte-identical after condition-private fields are projected away. Low-
entropy match hashes never enter restricted ingress, model bytes, provider
ingress, writer ingress, trainer ingress, or public receipts.

`validate_visibility` expands the complete information-item by stage matrix,
requires every cell exactly once, rejects extra cells, and uses byte-taint
fixtures to prove forbidden inputs cannot influence restricted outputs.

## 4. DREAM, evidence, SLEEP, and publication

`validate_dream` proves one physical no-retry call per snapshot, exact public-
slice input/render/raw/token/debit bindings, allowed-ID catalogue membership,
strict publish order/uniqueness/capacity, and the total VALID/PUBLISH_EMPTY/
ABSTAIN/DREAM_INVALID_OUTPUT/DREAM_MISSING_NO_RETRY mapping. All paired policies
reference the same DREAM receipt hash.

`validate_context_install` recomputes AUTHENTIC, RECENCY, or PERMUTED order and
exact rendered bytes. Empty/abstain/invalid/missing policies follow
`status_contract.json`; only consuming arms inherit a missing shared DREAM.

`validate_eligibility` recomputes the complete nominee universe and the first
failing predicate for each nominee. It rejects target/future/PROBE/cognitive/
DREAM/scorer/policy-target influence, incomplete predicate inputs, or omitted
nominees. `validate_root_policy` recomputes DREAM, recency, or recipient-local
hash order, deduplication, capacity, admitted roots, and aggregate status.

`validate_writer` proves each row is an exact arm-neutral runtime READ input to
one witnessed supported target, with no invented prose and no inaccessible
field. `validate_corpus` checks row/source order, hashes, byte/token-class
vectors, and zero-dose status. `validate_trainer`, `validate_adapter`, and
`validate_publication` recompute clean-base initialization, target-only loss,
recipe/update/shape/finiteness/base/tokenizer constraints, quarantine, and one
atomic publication. TRAIN_FAILED publishes nothing and continues adapter-off
without altering realized dose.

## 5. Status, estimands, tests, and claims

`validate_stage_outcome` applies blocker, missing, assigned-policy, no-action,
then observed precedence. Missing dominance is endpoint-local and persists
despite a later action. No-action maps to observed normalized action value zero.
Every assigned endpoint yields exactly one observation XOR one blocker.

`validate_paired_gate` recomputes all within-life aggregations, strict
`Z_i=1[d_i>margin_g]`, exact inclusive upper Binomial tail under `pi0_g`, and
certified-rational one-sided Clopper-Pearson lower bracket. `d_i=margin_g`
fails. A missing required arm has null descriptive difference and `Z_i=0`.

`validate_safety` recomputes the one designated D1A trial per life, inclusive
lower Binomial tail under the ceiling, strict observed-rate inequality, and
one-sided Clopper-Pearson upper bracket. Missing provider output sets both
FALSE_SELECTION and NOT_FOUND adverse indicators to one. Rate equal to the
ceiling fails.

`validate_missingness` uses the same lower-tail algorithm; a rate equal to the
ceiling fails. `validate_assay` expands the sealed gate registry, including
each `(path_template_id,edge_position,edge_id)` CUT/TWIN/SHAM gate, and takes
the maximum required local p-value. `validate_holm` applies exact four-claim
step-down with claim-ID tie break. `validate_power` reuses the same critical
counts, directions, missing treatment, and N for every expanded gate, then
uses `max(0,1-sum_g(1-power_g))`; it assumes no independence.

`validate_claim_decision` applies blocker precedence and emits only a decision
plus the exact registered literal/qualification candidate. It cannot release
text. `validate_preclaim_authority` consumes claim decisions, never releases.
`validate_claim_release` runs only after passing preclaim authority and emits
exactly the registered literal plus overlap/construction qualifications. The
dependency graph is therefore reduction -> decision -> authority -> release;
no release is an ancestor of its authority.

## 6. Acceptance and authority

`validate_fixture_manifest` materializes the registered finite universe or a
ratified generator/proof, recomputes expected case count, negative mutations,
role registry, and prerequisites. `validate_test_result` derives PASS only
when expected=executed, missing/extra/duplicate/mismatch counts are zero, every
mutation returns its registered failure, exact evidence roles are present, and
required independent implementations agree.

`validate_authority_stage` dispatches to the exact stage schema and recursively
revalidates every named predecessor and subject. Architecture and run human
receipts bind exact source-file bytes and byte offsets. Review FAIL cannot be
overridden by an advocate. `validate_preflight` applies its locked first-
failure order before every dispatch; DENY proves no process was created.
