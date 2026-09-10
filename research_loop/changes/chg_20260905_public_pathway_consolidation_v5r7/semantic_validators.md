# PPC5r7 semantic validators

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
or out-of-order fields fail. `validate_hash(x,T)` recomputes the self-hash field
declared for `T` in `object_inventory.json` using exactly
`SHA256(contract_T || NUL || "6" || NUL || canonical_without_self_hash || LF)`;
the inventory domain is audit metadata, not a preimage field. A digest under
the wrong contract fails even when payload bytes match.

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

`validate_generator` re-executes the exact pure ordinal-blind `G(theta,E)`
from its sealed source manifest and finite parameter law. It verifies disjoint
counter-expanded typed entropy slices and raw bytes, every decoded proposal,
ordered acceptance-predicate input/result and first-failure rejection, the
prospective proposal limit, fixed pre-entropy memberships/lower units,
common-seed derivation preimage, and the typed recipient plus recipient-disjoint donor inside
each draw. It forbids cross-draw matching, remapping, deduplication, exclusion,
or redraw and retains natural identity or entropy collisions. Proposal
exhaustion blocks construction before run authority.

`validate_controller` executes the unique result-keyed row over the closed
indexed-phase AST for D1A, every D1B program, D1C, or D1D. It materializes all
L/R/Q boundaries including R=0 and D1D provider-to-behavior transfer. Every
physical missing result consumes and advances or finalizes its slot once with
no seed reuse. Other errors follow their registered transition. Every reachable
state has exactly one successor or one terminal. No expression parser, alias,
retry, or implementation-selected default exists.

`validate_queue_dag` proves QUEUE_SLOT_BODY precedes controller-after and the
downstream QUEUE_SLOT_RECEIPT, with no body/receipt/controller self or mutual
ancestry. For every `QUEUED` slot, `validate_queue_coverage` requires exactly one effect:
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

`validate_d1a_controls` reconstructs the typed D1A corpus origin, within-draw
wrong-life match, binding derangement, and dose/opportunity receipts. It checks
every preserved multiset/vector/histogram, every destroyed binding, forbidden
matching input, exact row/token/update opportunity, and preassignment artifact
while proving downstream provider/writer/trainer projections are arm-neutral.
It then constructs exactly one downstream D1A control-set receipt from the
ordered AUTHENTIC, WRONG_LIFE, and BINDING_DERANGED origins and corpora plus the
two proofs and dose receipt. No origin or corpus may reference this descendant;
the dose receipt has no other consumer. The control set is required by power,
run lock, both seals, T06/T13/T14, authority, and release.

`validate_path_proof` independently enumerates all simple directed paths within
the READ budget in `(length, edge_id_tuple)` order. It proves every nonempty
proper subset of the registered path insufficient, the full set sufficient,
and every alternate enumerated path insufficient. Every edge has a distinct
raw source-event preimage. For every edge it recomputes CUT, the unique
lexicographically selected parity-matched reversing TWIN, and the unique
lexicographically selected parity-matched outcome-preserving nonauthentic SHAM.
All world variants, oracle inputs/results, source preimages, interventions,
parity universes, and within/cross-item disjointness are typed referenced bytes,
never asserted booleans or dangling digests.

`validate_intervention` requires exactly one match for the assigned target key.
A valid non-target request with zero assigned-target matches emits
OFF_PATH_AUTHENTIC_PASS_THROUGH from the common provider and remains an observed
adaptive outcome; zero target matches or multiple matches is RUN_INVALID. It then proves
the restricted projection and response stage contain only the fields allowed
by `visibility_contract.json`. Shared schemas and algorithms for causal rows
are byte-identical after condition-private fields are projected away. Low-
entropy match hashes never enter restricted ingress, model bytes, provider
ingress, writer ingress, trainer ingress, or public receipts. A privileged
route/audit chain binds assignment, actual provider receipt, selected source,
parity, match count, and resolved bytes. The restricted projection contains
only public bytes, length/debit classes, and a fresh uniformly random 256-bit
commitment; its nonce/preimage and semantic mapping remain privileged. The
typed emission proves byte equality. Recursive taint rejects every direct or
nested privileged-to-restricted path.

`validate_visibility` expands the complete information-item by stage matrix,
requires every cell exactly once, rejects extra cells, and uses byte-taint
fixtures to prove forbidden inputs cannot influence restricted outputs.

## 4. DREAM, evidence, SLEEP, and publication

`validate_dream` proves one physical no-retry call per snapshot, exact public-
slice input/render/raw/token/debit bindings, allowed-ID catalogue membership,
strict publish order/uniqueness/capacity, and the total VALID/PUBLISH_EMPTY/
ABSTAIN/DREAM_INVALID_OUTPUT/DREAM_MISSING_NO_RETRY mapping. All paired policies
reference the same typed DREAM receipt.

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
Privileged root selection is projected into policy-free admitted public
evidence before the writer. Privileged corpus provenance is projected into a
condition-free training corpus before the trainer. One-way audit receipts bind
both projections; sanitized objects never reference privileged objects.

## 5. Status, estimands, tests, and claims

`validate_canonical_rational` requires denominator>0,
`gcd(abs(numerator),denominator)=1`, zero exactly `0/1`, probability numerator
between zero and denominator, field-specific sign/range, and integer cross-
multiplication. Statistical validators additionally require counts<=N,
membership/observation length N, exact reduced count/N rates, ordered CP
brackets at the locked scale with both defining inequalities,
`gate.alpha_threshold=result.alpha_threshold=run_lock.alpha`, and
`cp_tail_alpha=run_lock.alpha/4`.

`validate_stage_outcome` applies blocker, missing, assigned-policy, no-action,
then observed precedence. Missing dominance is endpoint-local and persists
despite a later action. No-action maps to observed normalized action value zero.
Every assigned endpoint yields exactly one observation XOR one blocker.
`validate_observation_membership` recomputes each canonical
`(run, assay, sample, life, condition, pair, endpoint, lower-unit,
observation)` key and requires COMPLETE_LIFE and ENDPOINT_COVERAGE observation
references to equal the prospectively locked universe exactly. Treatment,
control, and adverse inputs are typed observation references with matching
run/sample/pair/endpoint identities. D1A uses exactly the one locked
FALSE_SELECTION and one locked NOT_FOUND trial per sample. Pairing, safety,
missingness, gates, p-values, Holm, replay, and release may derive only from
this closed membership.

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
the maximum required local p-value. `validate_holm` materializes four
claim-labeled HOLM_STEP records in exact p/claim-ID order with divisor,
threshold, reject, and stop fields. `validate_power` reuses the same full
critical-count conjunction—p-value equality, strict effect or adverse-rate
direction, strict CP-bound direction, missing treatment, and N—for every
expanded gate, then uses `max(0,1-sum_g(1-power_g))`; it assumes no
independence. `validate_construction_power` includes every finite-proposal
generator/donor/path/control/overlap construction success and exhaustion event.
It independently recomputes either the complete canonical finite support with
exact masses summing to one, or a certified partition lower bound with all
uncovered mass treated as failure. Simulation, realized-success substitution,
and independence assumptions are invalid.
`validate_overall_power` combines that lower bound with conditional complete-
release power by the probability chain rule, never an independence assumption;
only this unconditional overall result may enter PRE_MODEL authority.

`validate_overlap` reconstructs ordered per-unit semantic/alias/item/donor/
exact-ACQUIRE-PROBE memberships and canonical comparison keys, rejects missing
or duplicate units and count/key/source disagreement, and derives all aggregate
counts and qualification bytes. `validate_resource_manifest` separately orders
frozen coverage keys, assigns each physical event to its lexicographically
least coverage-key owner, requires identical vectors for duplicate occurrences,
gives nonowners zero marginal mass, and reconstructs INCLUSIVE, MARGINAL, and
PHYSICAL_TOTAL views with exact componentwise conservation in arbitrary-
precision integer/reduced-rational units. Resources remain descriptive and
cannot enter membership, gates, Holm, power, or adjustment.

`validate_claim_decision` applies blocker precedence in the claim-blind REDUCER;
a separate CANDIDATE_DECISION projection emits only the exact registered
literal/qualification candidate. It cannot release text and consumes neither
T14 nor authority. Two independent `validate_t14_cold_replay` executions
reconstruct every predecessor life, reducer, candidate decision,
qualification, and forbidden-claim mutation without reading release or
authority bytes. A final T14 result consumes exactly those two receipts and
their independence proof. Only then may `validate_preclaim_authority` consume
that final result and the candidate decisions.
`validate_claim_release` runs after passing preclaim authority and emits one
closed package containing exactly the registered literal, qualification, full
forbidden list, overlap/construction scope, and evidence roles. The graph is
reduction -> decision -> non-releasing T14 -> authority -> release -> optional
audit; no later object is its own ancestor.

## 6. Acceptance and authority

`validate_fixture_manifest` materializes the registered finite universe or a
ratified generator/proof, recomputes expected case count, negative mutations,
role registry, and prerequisites. `validate_test_result` derives PASS only
when expected=executed, missing/extra/duplicate/mismatch counts are zero, every
mutation returns its registered failure, exact evidence roles are present, and
required independent implementations agree.

Pre-ratification T01 binds only the actual generic architecture-intake
lifecycle history: exact consensus command, exit code zero, parsed `ok=true`,
awaiting-consensus predecessor, and human-required successor. No PPC5 T01
fixture, coverage receipt, TEST_RESULT, implementation, or sealer exists. The
PPC-specific dual-implementation fixtures for T02-T12 run only after exact
architecture ratification and before any model, tokenizer, embedding, trainer,
canary, CPU-behavioral, or GPU process. T13 is the final PRE_MODEL_EXECUTION
gate; describing T02-T13 merely as pre-GPU is invalid.

`validate_authority_stage` dispatches to the exact stage schema and recursively
revalidates every named predecessor and subject. Architecture and run human
receipts bind exact source-file bytes and byte offsets. Review FAIL cannot be
overridden by an advocate. `validate_preflight` applies its locked first-
failure order before every dispatch; DENY proves no process was created.
