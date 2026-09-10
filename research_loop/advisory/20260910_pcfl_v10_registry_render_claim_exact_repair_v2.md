# PCFL V10 registry, rendering, and claim exact repair v2

Date: 2026-09-10  
Status: source-only advisory; no source authoring, preparation, implementation, materialization, checker execution, fixture/root/data generation, model/tokenizer execution, training, GPU use, resource acquisition, scientific execution, claim, release, or submission

## 0. Disposition and v1 preservation

This advisory supersedes v1 for a future V10 integration while preserving v1
unchanged at SHA-256
`a6c9944f6b410f75a7ac4afa152e922fd30857f5ecd4d5f32ce9b111e80317b2`.
It closes the registry cross-critiques by defining one complete active
registry, correcting the split and active resource envelope, using the exact
V7 public mode/protocol enums, separating carrier-only delayed entitlement
from baseline entitlement, and aligning the zero-V7 rule with its sole guard
exception. It changes no scientific condition, call, endpoint, gate, model,
topology, or claim.

The active IDs are exactly `-00..-19` and `-23..-34`, 32 IDs total. IDs
`-20..-22` and `-35..-37` are `DEFERRED_UNAUTHORIZED`; they are not active
tests, have no call or endpoint, and cannot be used as claim evidence.

## 1. Frozen roster, split, and active envelope

The 64 deterministic roots are exactly 16 DEV, 32 CONFIRMATION, and 16
RESERVE roots: equivalently 8/16/8 `k` blocks, each with both `h` twins.
RESERVE never rescues, replaces, or augments DEV or CONFIRMATION. The exact
per-root roster is:

| conditions | count | phases | slots each | generated-token allowance each |
|---|---:|---|---:|---:|
| `AUTH_RECURRENT`, `AUTH_SCRATCH_OFF` | 2 | P+U+D | 43 | 11,008 |
| `ATOMS_RECURRENT`, `DERANGED_RECURRENT`, `REACHOUT_OFF_RECURRENT`, `NO_MEMORY_RECURRENT`, `PASSIVE_SIGNATURE_RECURRENT`, `RAW_CONTEXT_RECURRENT`, `RAG_RAW_RECURRENT`, `NATIVE_GRAPH_RECURRENT` | 8 | P+D | 39 | 9,984 |
| `BRIDGE_CUT_RECURRENT`, `TWIN_REDIRECT_RECURRENT` | 2 | P | 26 | 6,656 |
| `UNCERTAINTY_SHAM_RECURRENT` | 1 | U | 4 | 1,024 |
| `OLD_CUT_RECURRENT`, `NEW_CUT_RECURRENT`, `NO_PERSIST_NEW_RECURRENT` | 3 | D | 13 | 3,328 |
| `TARGET_ONLY_ANSWER_PRIOR_TAPE`, `AUTH_NO_FEEDBACK_TAPE` | 2 | four phase-level calls | 4 | 11,008 |

```text
slots/root                       = 501
generated-token allowance/root  = 148224
input-token allowance/root      = 501 * 8192 = 4104192

DEV, 16 roots                   = 8016 slots; 2371584 generated
CONFIRMATION, 32 roots          = 16032 slots; 4743168 generated
active DEV+CONFIRMATION         = 24048 slots; 7114752 generated
active sentinels                = 24 slots; 6144 generated
active grand maximum            = 24072 slots; 7120896 generated
active maximum input allowance  = 24072 * 8192 = 197197824

RESERVE, 16 roots, separate     = 8016 slots; 2371584 generated
```

The 24 inherited sentinels are part of the active maximum, not new model
conditions. RESERVE is reported separately and is not included in that active
maximum. Every test below is source/conformance work or a reducer over later
separately authorized receipts and adds zero scientific calls.

## 2. Exact V7 public mode/protocol vocabulary

The only `PublicMemorySurfaceV4.mode` values are:

```text
COMMON_READER
BLOCKED_READER
PASSIVE_NULL_READER
RAW_STATIC
RAG_DETERMINISTIC
NATIVE_GRAPH_STATIC
NO_MEMORY_SURFACE
```

The only `read_protocol` values are:

```text
ANCHOR_CURSOR
BLOCKED_ANCHOR_CURSOR
PASSIVE_NULL_ANCHOR_CURSOR
RAG_AUTO
NONE
```

The legal table is exact:

| phase-local conditions | mode | static_context | rag_corpus | protocol |
|---|---|---|---|---|
| applicable P/D of `AUTH_RECURRENT`, `AUTH_SCRATCH_OFF`, `ATOMS_RECURRENT`, `DERANGED_RECURRENT`, `BRIDGE_CUT_RECURRENT`, `TWIN_REDIRECT_RECURRENT`, `OLD_CUT_RECURRENT`, `NEW_CUT_RECURRENT`, `NO_PERSIST_NEW_RECURRENT`, `AUTH_NO_FEEDBACK_TAPE` | `COMMON_READER` | null | null | `ANCHOR_CURSOR` |
| applicable P/D of `REACHOUT_OFF_RECURRENT`, `NO_MEMORY_RECURRENT` | `BLOCKED_READER` | null | null | `BLOCKED_ANCHOR_CURSOR` |
| applicable P/D of `PASSIVE_SIGNATURE_RECURRENT` | `PASSIVE_NULL_READER` | null | null | `PASSIVE_NULL_ANCHOR_CURSOR` |
| applicable P/D of `RAW_CONTEXT_RECURRENT` | `RAW_STATIC` | `RawContextPublicV4` | null | `NONE` |
| applicable P/D of `RAG_RAW_RECURRENT` | `RAG_DETERMINISTIC` | null | `RagCorpusPublicV4` | `RAG_AUTO` |
| applicable P/D of `NATIVE_GRAPH_RECURRENT` | `NATIVE_GRAPH_STATIC` | `NativeGraphPublicV4` | null | `NONE` |
| applicable P/D of `TARGET_ONLY_ANSWER_PRIOR_TAPE` | `BLOCKED_READER` | null | null | `BLOCKED_ANCHOR_CURSOR` |
| every applicable U phase | `NO_MEMORY_SURFACE` | null | null | `NONE` |

No alias such as `COMMON`, `BLOCKED`, `PASSIVE`, `RAW`, `RAG`, `NATIVE`, or
`NO_MEMORY` is a serialized enum. Those words may appear only as explanatory
condition abbreviations in equations.

## 3. Mechanically closed `AcceptanceTestSpec` registry

Each YAML item below has exactly these nine fields: `test_id`, `kind`,
`required_before`, `acceptance`, `positive_fixture_ids`,
`reject_or_mutation_fixture_ids`, `evidence_artifact`,
`failure_disposition`, and `claim_withdrawal`. Arrays are closed, literal,
ordered, and duplicate-free. An implementation may not rename, merge, omit,
or replace a record or fixture. A shared fixture still produces a separate
verdict in each test's receipt.

```yaml
- test_id: M0V4-EXACT-SOURCE-RATIFIABILITY-00
  kind: invariant
  required_before: implementation
  acceptance: "Accept only one closed hash-bound manifest enumerating every proposed source byte, schema, constant, dependency, fixture, test and output path, with byte-identical reread and no executable interpretation."
  positive_fixture_ids: [REGV10-POS-CLOSED-SOURCE-MANIFEST, REGV10-POS-BYTE-IDENTICAL-REREAD]
  reject_or_mutation_fixture_ids: [REGV10-REJ-UNLISTED-PATH, REGV10-REJ-GLOB-OR-DIRECTORY, REGV10-REJ-UNLISTED-DEPENDENCY, REGV10-REJ-HASH-OR-PATH-DRIFT, REGV10-REJ-EXECUTABLE-USE]
  evidence_artifact: ExactSourceRatifiabilityReceiptV1
  failure_disposition: "INCOMPLETE for a missing/duplicate member; INVALID for a hash, dependency, path, or execution-boundary breach."
  claim_withdrawal: "All source, preparation, execution, and scientific claims remain unauthorized."

- test_id: M0V4-ZERO-V7-RUNTIME-REUSE-01
  kind: invariant
  required_before: materialization
  acceptance: "Every non-boundary C10 member, provenance row, capability, import surface, runtime surface, and actor/model projection satisfies all seven V7/V5 denial predicates; independently derived ordinary coincident scalars remain permitted; the boundary exception is owned only by test 34."
  positive_fixture_ids: [V7V10-POS-CLEAN-PCFL, V7V10-POS-COINCIDENT-SCALAR]
  reject_or_mutation_fixture_ids: [V7V10-REJ-RESOLVED-PATH, V7V10-REJ-MODULE, V7V10-REJ-WHOLE-ARTIFACT, V7V10-REJ-DECLARED-PROVENANCE, V7V10-REJ-DISTINCTIVE-INTERFACE, V7V10-REJ-CAPABILITY, V7V10-REJ-ACTOR-MODEL]
  evidence_artifact: ZeroV7RuntimeReuseReceiptV1
  failure_disposition: "INVALID before materialization; emit no prepared output."
  claim_withdrawal: "Withdraw clean-room status and every scientific clause."

- test_id: M0V4-DISJOINT-CHECKER-AND-MUTATION-02
  kind: invariant
  required_before: implementation
  acceptance: "Accept iff two independently authored checkers, sharing no outcome-deciding code, table, import, or helper, agree on every positive and mutation fixture and each complete fixture list is hash-bound."
  positive_fixture_ids: [CHECKERV10-POS-DISJOINT-POSITIVE-AGREEMENT, CHECKERV10-POS-DISJOINT-NEGATIVE-AGREEMENT]
  reject_or_mutation_fixture_ids: [CHECKERV10-REJ-SHARED-DECISION-CODE, CHECKERV10-REJ-CHECKER-IMPORT, CHECKERV10-REJ-MISSING-CHECKER, CHECKERV10-REJ-VERDICT-DISAGREEMENT, CHECKERV10-REJ-MISSING-FIXTURE]
  evidence_artifact: DisjointCheckerAgreementReceiptV1
  failure_disposition: "INVALID; no checker result is accepted."
  claim_withdrawal: "Withdraw every clause depending on the affected checker contract."

- test_id: M0V4-ACTOR-NONORACLE-03
  kind: invariant
  required_before: implementation
  acceptance: "Accept iff actor-visible bytes are a pure function of the exact public allowlist and carrier grants, and paired worlds with equal public projection are byte/token/tool/parser identical before an entitled public origin."
  positive_fixture_ids: [VISV10-POS-PUBLIC-PROJECTION-TWIN, VISV10-POS-ENTITLED-ORIGIN-FIRST-DIFFERENCE]
  reject_or_mutation_fixture_ids: [VISV10-REJ-HIDDEN-H, VISV10-REJ-ANSWER-OR-SCORE, VISV10-REJ-CONDITION-OR-SPLIT, VISV10-REJ-ORACLE-OR-CHECKER, VISV10-REJ-FUTURE-EVENT, VISV10-REJ-CACHE-ERROR-PADDING-TIMING]
  evidence_artifact: ActorNonoracleProjectionReceiptV1
  failure_disposition: "INVALID actor boundary, never behavioral zero."
  claim_withdrawal: "Withdraw all behavioral and mechanistic clauses."

- test_id: M0V4-BUNDLED-READER-READ-CUT-04
  kind: invariant
  required_before: implementation
  acceptance: "Accept iff each capability-checked READ returns one frozen charged bundle, the reader closes on the first world-relation attempt, and READ_CUT makes identical carrier content unavailable without another access path."
  positive_fixture_ids: [READV10-POS-FOUND-BUNDLE, READV10-POS-NOT-FOUND-BUNDLE, READV10-POS-FIRST-ACTION-CLOSE, READV10-POS-READ-CUT]
  reject_or_mutation_fixture_ids: [READV10-REJ-PARTIAL-OR-UNMETERED, READV10-REJ-POST-ACTION-READ, READV10-REJ-REOPEN, READV10-REJ-FOREIGN-HANDLE, READV10-REJ-CURSOR-ESCAPE, READV10-REJ-PREFETCH-OR-BACKING-STORE]
  evidence_artifact: BundledReaderCutReceiptV1
  failure_disposition: "INVALID supplied-memory instrument."
  claim_withdrawal: "Withdraw supplied-memory and connected-use attribution."

- test_id: M0V4-VISIBILITY-RESET-NONINTERFERENCE-05
  kind: invariant
  required_before: model_execution
  acceptance: "Accept iff every phase starts from its registered public cut and sterile reset destroys all non-entitled scratch, messages, returns, cache, session, KV, RNG, repeat, private, branch, and condition state while preserving only named public/CAS descendants."
  positive_fixture_ids: [RESETV10-POS-STERILE-PHASE-START, RESETV10-POS-ENTITLED-CAS-SURVIVOR, RESETV10-POS-CROSS-ROOT-NONINTERFERENCE]
  reject_or_mutation_fixture_ids: [RESETV10-REJ-TRANSCRIPT-SURVIVOR, RESETV10-REJ-SCRATCH-OR-RETURN-SURVIVOR, RESETV10-REJ-CACHE-SESSION-KV-SURVIVOR, RESETV10-REJ-REPEAT-SURVIVOR, RESETV10-REJ-PRIVATE-OR-BRANCH-SURVIVOR, RESETV10-REJ-CROSS-CONDITION-OR-ROOT]
  evidence_artifact: VisibilityResetNoninterferenceReceiptV1
  failure_disposition: "INVALID affected phase and delayed assay."
  claim_withdrawal: "Withdraw all delayed-carrier and cross-phase language."

- test_id: M0V4-PROVENANCE-TRANSFORM-DAG-06
  kind: invariant
  required_before: implementation
  acceptance: "Accept iff every released atom/link has complete canonical primitive parents, a registered non-evidential transform, finite acyclic lineage, and independent support where required; transforms add no evidence, position, support, contradiction, or revocation."
  positive_fixture_ids: [PROVV10-POS-OLD-SIX-ORDER, PROVV10-POS-NEW-H0, PROVV10-POS-NEW-H1, PROVV10-POS-ALIAS-CANONICAL, PROVV10-POS-SHARED-ROOT-DIAMOND]
  reject_or_mutation_fixture_ids: [PROVV10-REJ-PARENT-UNKNOWN, PROVV10-REJ-COLLAPSED-DAG-CYCLE, PROVV10-REJ-INCOMPLETE-PRIMITIVE-PARENTS, PROVV10-REJ-SYNTH-AS-PRIMITIVE, PROVV10-REJ-TRANSFORM-EVIDENCE]
  evidence_artifact: ProvenanceTransformDagReceiptV1
  failure_disposition: "INVALID carrier provenance."
  claim_withdrawal: "Withdraw grounded-carrier and connected-memory clauses."

- test_id: M0V4-CAS-TWO-FREEZE-DURABILITY-07
  kind: invariant
  required_before: implementation
  acceptance: "Accept iff freeze one seals all source/instrument objects, freeze two seals later execution outputs, every object is immutable and independently rehashable, and no second-freeze output parents a first-freeze object."
  positive_fixture_ids: [CASV10-POS-FIRST-FREEZE-REREAD, CASV10-POS-SECOND-FREEZE-REREAD, CASV10-POS-ACYCLIC-FREEZE-ORDER]
  reject_or_mutation_fixture_ids: [CASV10-REJ-MUTABLE-OBJECT, CASV10-REJ-HASH-BYTE-COLLISION-CLAIM, CASV10-REJ-OUTPUT-TO-SOURCE-EDGE, CASV10-REJ-MISSING-DURABILITY, CASV10-REJ-NONDETERMINISTIC-REREAD]
  evidence_artifact: CasTwoFreezeDurabilityReceiptV1
  failure_disposition: "INVALID or INCOMPLETE according to corrupt versus missing freeze evidence."
  claim_withdrawal: "Withdraw all empirical clauses."

- test_id: M0V4-CPU-CONFORMANCE-08
  kind: end_to_end
  required_before: model_execution
  acceptance: "Accept iff every separately authorized deterministic preparation/checker/reducer operation is CPU-only, network-closed, model/tokenizer-free, deterministic under the frozen environment, and byte-identical across two conformance runs."
  positive_fixture_ids: [CPUV10-POS-TWO-RUN-BYTE-IDENTITY, CPUV10-POS-DEVICE-MANIFEST-CPU-ONLY]
  reject_or_mutation_fixture_ids: [CPUV10-REJ-GPU-OR-ACCELERATOR, CPUV10-REJ-MODEL-OR-TOKENIZER, CPUV10-REJ-NETWORK, CPUV10-REJ-NONDETERMINISTIC-ORDER-OR-SEED, CPUV10-REJ-PLATFORM-SERIALIZATION, CPUV10-REJ-HIDDEN-CONCURRENCY]
  evidence_artifact: CpuConformanceReceiptV1
  failure_disposition: "INVALID deterministic preparation; stop before materialization acceptance."
  claim_withdrawal: "Withdraw all downstream scientific clauses."

- test_id: MTEXTV4-RENDERED-BOUNDARY-09
  kind: invariant
  required_before: model_execution
  acceptance: "Accept iff every legal mode/protocol/phase/stage renders only allowlisted public fields and exact advertised commands, and complete system, user, template, token, tool-envelope, fingerprint, and parser artifacts pass the branch, repeat, and cross-product mutations without treating tests 31-33 as replaceable dependencies."
  positive_fixture_ids: [RENDERV10-POS-ALL-LEGAL-CROSSPRODUCT, RENDERV10-POS-ALL-TERMINALS, RENDERV10-POS-ENTITLED-FIRST-DIFFERENCE]
  reject_or_mutation_fixture_ids: [RENDERV10-REJ-PRIVATE-FIELD, RENDERV10-REJ-UNREGISTERED-TEMPLATE-OR-TOOL, RENDERV10-REJ-LENGTH-ORDER-PADDING-CHANNEL, RENDERV10-REJ-FUTURE-HANDLE, RENDERV10-REJ-MISSING-31-RECEIPT, RENDERV10-REJ-MISSING-32-RECEIPT, RENDERV10-REJ-MISSING-33-RECEIPT]
  evidence_artifact: RenderedBoundaryReceiptV1
  failure_disposition: "INVALID rendered instrument."
  claim_withdrawal: "Withdraw every scientific clause."

- test_id: MTEXTV4-ROSTER-ENDPOINT-RESOURCE-10
  kind: invariant
  required_before: model_execution
  acceptance: "Accept iff source, schema, plan and reducers agree on the exact 18-condition roster, legal phase projections, endpoint applicability, 501 slots and 148224 generated tokens per root, 16/32/16 split, active envelope, and complete per-arm resource fields."
  positive_fixture_ids: [RESOURCEV10-POS-ROSTER-GOLDEN, ENDPOINTV10-POS-18-CONDITION-MATRIX, RESOURCEV10-POS-FULL-VECTOR-ZERO-NA]
  reject_or_mutation_fixture_ids: [RESOURCEV10-REJ-ROSTER-CONDITION, RESOURCEV10-REJ-ROSTER-PHASE, RESOURCEV10-REJ-ROSTER-SLOT, RESOURCEV10-REJ-ROSTER-GENERATION, RESOURCEV10-REJ-ROSTER-SPLIT, ENDPOINTV10-REJ-BORROWED-CELL, RESOURCEV10-REJ-HIDDEN-THINKER-CALL]
  evidence_artifact: RosterEndpointResourceReceiptV1
  failure_disposition: "INVALID for drift; INCOMPLETE for a missing receipt or cell."
  claim_withdrawal: "Withdraw all empirical and efficiency clauses."

- test_id: MTEXTV4-CONFIRMATION-CLAIM-GATE-11
  kind: end_to_end
  required_before: scientific_claim
  acceptance: "Accept only a complete sealed fixed-model fixed-topology census of all 32 CONFIRMATION roots under the frozen source, rendering, resource, receipt, applicability, and noncompensatory clause gates, followed by independent evidence-to-claim review."
  positive_fixture_ids: [CLAIMV10-POS-COMPLETE-CONFIRMATION-CENSUS, CLAIMV10-POS-INDEPENDENT-CLAUSE-REVIEW]
  reject_or_mutation_fixture_ids: [CLAIMV10-REJ-SOURCE-OR-DEV-EVIDENCE, CLAIMV10-REJ-PARTIAL-CELLS, CLAIMV10-REJ-RESERVE-RESCUE, CLAIMV10-REJ-POOLED-COMPENSATION, CLAIMV10-REJ-MISSING-INVARIANT, CLAIMV10-REJ-DEFERRED-MECHANISM]
  evidence_artifact: ConfirmationClaimGateReceiptV1
  failure_disposition: "INCOMPLETE or INVALID; no generic partial-pass state exists."
  claim_withdrawal: "Release only clauses individually passing test 18; otherwise withdraw them exactly."

- test_id: M0V5-SOURCE-AUTHORING-VS-PREPARATION-AUTHORITY-12
  kind: invariant
  required_before: implementation
  acceptance: "Accept only the closed C10 SourceAuthoringGrantV1 and SourceProvenanceRowV1 bound to the exact C10 consensus, state, plan, human evidence and candidate path list; authorize only listed candidate writes, SHA-256/length computation, and the nonauthoritative manifest; stop before parse, checking, preparation, implementation or execution."
  positive_fixture_ids: [AUTHV10-POS-C10-GRANT, AUTHV10-POS-C10-PROVENANCE, AUTHV10-POS-CANDIDATE-MANIFEST-STOP]
  reject_or_mutation_fixture_ids: [AUTHV10-REJ-STALE-CHANGE-ID, AUTHV10-REJ-STALE-OR-SWAPPED-HASH, AUTHV10-REJ-OPERATION-OR-BOOLEAN, AUTHV10-REJ-PATH-ESCAPE, AUTHV10-REJ-HUMAN-EVIDENCE, AUTHV10-REJ-PROVENANCE-ROW, AUTHV10-REJ-AUTHORING-AS-RATIFICATION, AUTHV10-REJ-PARSE-CHECK-PREPARE-EXECUTE]
  evidence_artifact: SourceAuthoringAuthorityReceiptV1
  failure_disposition: "STOP with no source write for a bad grant; authored candidate bytes remain unratified and nonconsumable."
  claim_withdrawal: "No source, implementation, execution, or scientific claim is authorized."

- test_id: M0V5-DELAYED-ENTRY-OUTCOME-DESCENDANT-13
  kind: invariant
  required_before: model_execution
  acceptance: "Carrier-only test: for COMMON_READER delayed carrier conditions, fixed-k twins may differ at D entry only inside /carrier/atoms/25 and /carrier/links/6, with stable handles/order/schema/padding and every differing leaf descended from supplied O41_ACQUIRE_SUCCESS; no RAW_STATIC, RAG_DETERMINISTIC or NATIVE_GRAPH_STATIC baseline surface is tested or authorized here."
  positive_fixture_ids: [DELAYV10-POS-CARRIER-H0, DELAYV10-POS-CARRIER-H1, DELAYV10-POS-CARRIER-FIRST-RETURN, DELAYV10-POS-CARRIER-STERILE-RESET]
  reject_or_mutation_fixture_ids: [DELAYV10-REJ-CARRIER-EXTRA-POINTER, DELAYV10-REJ-CARRIER-WRONG-OR-MISSING-O41-LINEAGE, DELAYV10-REJ-CARRIER-STABLE-FIELD, DELAYV10-REJ-CARRIER-LIVE-U-STATE, DELAYV10-REJ-CARRIER-BASELINE-SURFACE-CLAIM]
  evidence_artifact: DelayedCarrierOutcomeDescendantReceiptV1
  failure_disposition: "INVALID carrier delayed treatment; baseline conditions remain governed separately by test 29."
  claim_withdrawal: "Withdraw the carrier-specific delayed clause; never infer retention, acquisition-to-use, self-write, or learning."

- test_id: MTEXTV4-TARGET-ONLY-ALGEBRA-DECODING-14
  kind: ablation
  required_before: model_execution
  acceptance: "Accept iff the exact XOR alias decoder reconstructs both A and B upper/lower paths for all 32 k without memory, has D twin-minimum zero without h, and every applicable CONFIRMATION shortcut count for TARGET_ONLY_ANSWER_PRIOR_TAPE, NO_MEMORY_RECURRENT and PASSIVE_SIGNATURE_RECURRENT is at most 5 from complete same-cell receipts."
  positive_fixture_ids: [ALGV10-POS-A-UPPER-ALL-K, ALGV10-POS-A-LOWER-ALL-K, ALGV10-POS-B-UPPER-ALL-K, ALGV10-POS-B-LOWER-ALL-K, ALGV10-POS-D-TWIN-MIN-ZERO]
  reject_or_mutation_fixture_ids: [ALGV10-REJ-K-PARSE, ALGV10-REJ-NON-XOR, ALGV10-REJ-MISSING-PARENT-PATH, ALGV10-REJ-FORBIDDEN-INPUT, ALGV10-REJ-FIFTH-RELATION, ALGV10-REJ-MISSING-NA-OR-FOREIGN-RECEIPT, ALGV10-REJ-SHORTCUT-COUNT-GT5]
  evidence_artifact: AlgebraPriorReceiptV1
  failure_disposition: "INVALID for fixture/receipt defects; SHORTCUT_BREACH for a complete count greater than 5."
  claim_withdrawal: "A path breach withdraws connected-memory specificity for that route/two-goal clause; a D breach also withdraws delayed-carrier specificity."

- test_id: M0V4-PRODUCER-SCORER-ANSWER-NEUTRALITY-15
  kind: ablation
  required_before: model_execution
  acceptance: "Accept iff all producer-goal, producer-answer, reader-goal, reader-score, path-order, score-label and scorer-absence swaps leave every upstream byte/action invariant as specified, all six legal minimum paths score symmetrically, and carrier output also passes test 30's local-edge grammar."
  positive_fixture_ids: [PQS-PRODUCER-GOAL, PQS-PRODUCER-ANSWER, PQS-READER-GOAL, PQS-READER-SCORE, PQS-PATH-ORDER, PQS-SCORE-LABEL, PQS-SCORER-ABSENCE, PQS-POS-SIX-MINIMUM-PATHS]
  reject_or_mutation_fixture_ids: [PQS-REJ-GOAL-OR-ANSWER-INPUT, PQS-REJ-SCORE-OR-ORACLE-INPUT, PQS-REJ-ROW-CURSOR-PADDING-RANK, PQS-REJ-SCORER-UPSTREAM-EFFECT, PQS-REJ-REFERENCE-PATH-PRIVILEGE, PQS-REJ-ANSWER-ONLY-TRACE, PQS-REJ-MISSING-30-RECEIPT]
  evidence_artifact: ProducerQueryScorerNeutralityReceiptV1
  failure_disposition: "INVALID before model execution."
  claim_withdrawal: "Withdraw answer-neutral production and all connected-memory attribution."

- test_id: MTEXTV4-BRIDGE-TWIN-TRACE-EQUIVALENCE-16
  kind: invariant
  required_before: model_execution
  acceptance: "Accept iff raw charged world traces have exactly one registered terminal, upper/lower paths normalize to LEG_1,LEG_2,BRIDGE,TERMINAL_RELATION_TO(goal),FINISH_OK(goal), bridge change and first-action-at-C twin switch are computed per same k,h for both goals, support deletion invalidates cited traces, and the twin-minimum confirmation numerator is at least 12 of 16."
  positive_fixture_ids: [TRACEV10-POS-A-UPPER-LOWER-EQUIVALENT, TRACEV10-POS-B-UPPER-LOWER-EQUIVALENT, TRACEV10-POS-BRIDGE-CUT-CHANGE, TRACEV10-POS-TWIN-FIRST-ACTION-SWITCH, TRACEV10-POS-SUPPORT-DELETION]
  reject_or_mutation_fixture_ids: [TRACEV10-REJ-TEXT-ONLY-DIFFERENCE, TRACEV10-REJ-VALID-ALTERNATE-UNEQUAL, TRACEV10-REJ-POST-TERMINAL-ACTION, TRACEV10-REJ-WRONG-C-OR-FIRST-ACTION, TRACEV10-REJ-MISSING-SUPPORT, TRACEV10-REJ-CROSS-ROOT-PHASE, TRACEV10-REJ-GOAL-OR-TWIN-COMPENSATION]
  evidence_artifact: BridgeTwinNormalizedTraceReceiptV1
  failure_disposition: "INVALID for structural/receipt faults; otherwise retain a complete Boolean negative."
  claim_withdrawal: "Withdraw connected-path specificity when the complete noncompensatory gate misses."

- test_id: MTEXTV4-CONDITION-PHASE-ENDPOINT-APPLICABILITY-17
  kind: invariant
  required_before: model_execution
  acceptance: "Accept iff the exact 18-condition matrix types every same-condition endpoint as Boolean or literal NA; wrong finish, abstain, budget exhaustion and registered output-invalid remain applicable zeros; NOT_REACHED is call padding only; each value comes from its own root-condition-phase receipt; and twin reduction is only min over h."
  positive_fixture_ids: [ENDPOINTV10-POS-18-CONDITION-MATRIX, ENDPOINTV10-POS-BEHAVIORAL-ZERO, ENDPOINTV10-POS-LITERAL-NA, ENDPOINTV10-POS-NOT-REACHED-CALL-ONLY, ENDPOINTV10-POS-TWIN-MINIMUM]
  reject_or_mutation_fixture_ids: [ENDPOINTV10-REJ-NA-ZERO-SUBSTITUTION, ENDPOINTV10-REJ-NOT-REACHED-ENDPOINT, ENDPOINTV10-REJ-FOREIGN-ROOT-CONDITION-PHASE-H, ENDPOINTV10-REJ-AUTH-FALLBACK, ENDPOINTV10-REJ-SYNTHESIZED-FULL-SEQUENCE, ENDPOINTV10-REJ-GATE-REQUIRED-NA, ENDPOINTV10-REJ-POOLING-OR-IMPUTATION]
  evidence_artifact: EndpointApplicabilityReceiptV1
  failure_disposition: "INVALID/INCOMPLETE for schema or origin failure; valid zero remains negative evidence."
  claim_withdrawal: "Withdraw each clause lacking complete Boolean inputs; never convert NA or NOT_REACHED into evidence."

- test_id: MTEXTV4-CLAUSE-SPECIFIC-NEGATIVE-DISPOSITION-18
  kind: end_to_end
  required_before: scientific_claim
  acceptance: "Accept iff the six permitted clauses are independently mapped to their exact G0-G10 conjunctions and clause-specific pass, complete-negative, INVALID, INCOMPLETE and withdrawal outcomes; optional gates never rescue mandatory gates; every deferred mechanism is unconditionally withdrawn."
  positive_fixture_ids: [CLAIMV10-POS-CONNECTED-CLAUSE, CLAIMV10-POS-CALIBRATION-CLAUSE, CLAIMV10-POS-DELAYED-CLAUSE, CLAIMV10-POS-PRACTICAL-CLAUSE, CLAIMV10-POS-SCRATCH-CLAUSE, CLAIMV10-POS-FEEDBACK-CLAUSE, CLAIMV10-POS-ALL-MANDATORY-CONJUNCTION]
  reject_or_mutation_fixture_ids: [CLAIMV10-REJ-GLOBAL-PASS-LABEL, CLAIMV10-REJ-OPTIONAL-RESCUE, CLAIMV10-REJ-POOLED-COMPENSATION, CLAIMV10-REJ-INVALID-AS-ZERO, CLAIMV10-REJ-SHORTCUT-AVERAGING, CLAIMV10-REJ-DEFERRED-MECHANISM]
  evidence_artifact: ClauseDispositionReceiptV1
  failure_disposition: "INVALID claim reducer; no clause may be released."
  claim_withdrawal: "Apply the exact clause-to-gate matrix in section 8; withdraw the combined maximum if any mandatory clause misses."

- test_id: MTEXTV4-BASELINE-PUBLIC-PROJECTION-AND-RESET-19
  kind: baseline
  required_before: model_execution
  acceptance: "Accept iff the exact seven V7 mode/protocol rows in section 2, typed public projection, deterministic 50-digit-Decimal BM25 and integer tie ranking, literal four-slot RAG nulls, saturated repeat state, reset destruction and per-arm charging reproduce independent goldens."
  positive_fixture_ids: [BASEV10-POS-SEVEN-MODE-TABLE, BASEV10-POS-BLOCKED-VS-PASSIVE, BASEV10-POS-RAW-STATIC, BASEV10-POS-RAG-DETERMINISTIC, BASEV10-POS-NATIVE-GRAPH-STATIC, BASEV10-POS-NO-MEMORY-SURFACE, BASEV10-POS-RESET]
  reject_or_mutation_fixture_ids: [BASEV10-REJ-MODE-PROTOCOL-PAIR, BASEV10-REJ-PRIVATE-PROJECTION, BASEV10-REJ-HIDDEN-RETRIEVAL, BASEV10-REJ-NONLITERAL-NULL, BASEV10-REJ-BM25-OR-TIE, BASEV10-REJ-REPEAT-OR-FINGERPRINT, BASEV10-REJ-RESET-SURVIVOR, BASEV10-REJ-UNCHARGED-WORK]
  evidence_artifact: BaselineProjectionResetReceiptV1
  failure_disposition: "INVALID affected baseline comparison; core mechanism arms are not rescued or defeated by it."
  claim_withdrawal: "Withdraw practical-baseline and efficiency language for an invalid or incomplete comparison."

- test_id: MTEXTV4-ROSTER-SLOT-ENVELOPE-23
  kind: invariant
  required_before: model_execution
  acceptance: "The exact 18 rows, phase projections, 501 slots/root, 148224 generated tokens/root, 4104192 input tokens/root, 16/32/16 root split, 24 sentinels, active totals, reserve separation, and REQUEST_EMITTED/NOT_REACHED partition equal section 1."
  positive_fixture_ids: [RESOURCEV10-POS-ROSTER-18, RESOURCEV10-POS-PHASE-PROJECTION, RESOURCEV10-POS-ROOT-SPLIT-ACTIVE, RESOURCEV10-POS-NOT-REACHED-PARTITION]
  reject_or_mutation_fixture_ids: [RESOURCEV10-REJ-ROSTER-ROW-DRIFT, RESOURCEV10-REJ-PHASE-PROJECTION-DRIFT, RESOURCEV10-REJ-SLOT-OR-ALLOWANCE-DRIFT, RESOURCEV10-REJ-EARLY-TERMINAL-DELETES-SLOT, RESOURCEV10-REJ-RESERVE-SUBSTITUTION, RESOURCEV10-REJ-SENTINEL-AS-ENDPOINT]
  evidence_artifact: RosterSlotEnvelopeReceiptV1
  failure_disposition: "INVALID for arithmetic/roster drift; INCOMPLETE for a missing slot receipt."
  claim_withdrawal: "Withdraw all scientific and resource-comparability clauses."

- test_id: MTEXTV4-PER-ARM-CHARGED-RESOURCE-VECTOR-24
  kind: invariant
  required_before: model_execution
  acceptance: "Every applicable root-condition-phase emits exactly one closed ChargedResourceV10; every common and reduction receipt reconciles; standalone CAS is the complete per-arm closure, physical CAS is the digest union, and every positive fixture in section 4 has its exact golden."
  positive_fixture_ids: [RESOURCEV10-POS-CLOSED-SCHEMA, RESOURCEV10-POS-FULL-VECTOR-ZERO-NA, RESOURCEV10-POS-STATIC-REPEATED, RESOURCEV10-POS-RAG-WORK, RESOURCEV10-POS-BLOCKED-READER, RESOURCEV10-POS-NOT-REACHED, RESOURCEV10-POS-CAS-STANDALONE-PHYSICAL, RESOURCEV10-POS-COMPONENT-REDUCTION, RESOURCEV10-POS-POST-ORIGIN-DESCENDANT]
  reject_or_mutation_fixture_ids: [RESOURCEV10-REJ-V5-SCHEMA-NAME, RESOURCEV10-REJ-MISSING-FIELD, RESOURCEV10-REJ-EXTRA-FIELD, RESOURCEV10-REJ-WRONG-TYPE, RESOURCEV10-REJ-ZERO-NA-MISSING, RESOURCEV10-REJ-CAS-DIVIDED-STANDALONE, RESOURCEV10-REJ-CAS-SUMMED-PHYSICAL, RESOURCEV10-REJ-CAUSAL-REALLOCATION]
  evidence_artifact: PerArmChargedResourceVectorReceiptV1
  failure_disposition: "INVALID affected arm and resource factorial; no scalar imputation is allowed."
  claim_withdrawal: "Withdraw the affected arm and every practical, componentwise-resource, or efficiency comparison."

- test_id: MTEXTV4-RESOURCE-METER-NONOMISSION-25
  kind: invariant
  required_before: model_execution
  acceptance: "The closed capability manifest and ResourceMeterEventV10 ledger attribute every allowed work, storage, device, call, reader, network, and artifact event exactly once; raw events reconcile every ChargedResourceV10 leaf and no omitted, duplicated, unowned, negative, or unattributable event exists."
  positive_fixture_ids: [RESOURCEV10-POS-METER-CAPABILITY-CLOSURE, RESOURCEV10-POS-METER-LEAF-RECONCILIATION, RESOURCEV10-POS-CAUSAL-SCOPE-RECONCILIATION]
  reject_or_mutation_fixture_ids: [RESOURCEV10-REJ-STATIC-ONCE-ONLY, RESOURCEV10-REJ-RAG-BUILD-OR-POSTINGS-FREE, RESOURCEV10-REJ-COMMON-READER-FREE, RESOURCEV10-REJ-HIDDEN-THINKER-CALL, RESOURCEV10-REJ-CAS-DIVIDED-STANDALONE, RESOURCEV10-REJ-CAS-SUMMED-PHYSICAL, RESOURCEV10-REJ-CAS-DIGEST-ALIAS, RESOURCEV10-REJ-DELETED-TEMP-FREE, RESOURCEV10-REJ-CPU-WARMUP-FREE, RESOURCEV10-REJ-GPU-UNATTRIBUTABLE, RESOURCEV10-REJ-MEMORY-UNATTRIBUTABLE, RESOURCEV10-REJ-ZERO-NA-MISSING, RESOURCEV10-REJ-SEGMENT-SUM, RESOURCEV10-REJ-REGISTERED-ACTUAL-CONFLATION, RESOURCEV10-REJ-NETWORK-OR-COST, RESOURCEV10-REJ-CAUSAL-REALLOCATION]
  evidence_artifact: ResourceMeterNonomissionReceiptV1
  failure_disposition: "INVALID affected arm and resource factorial; a global ceiling or test 19 cannot compensate."
  claim_withdrawal: "Withdraw the affected assay and every practical, componentwise-resource, or efficiency clause."

- test_id: M0V4-PROVENANCE-FINITE-ORDER-26
  kind: invariant
  required_before: implementation
  acceptance: "The finite position table, seven-pair order, canonical alias collapse, complete primitive roots, later independent support, legal shared-root diamonds, and SYNTH/re-expression non-evidence rules reproduce every section 3 positive fixture exactly."
  positive_fixture_ids: [PROVV10-POS-OLD-SIX-ORDER, PROVV10-POS-NEW-H0, PROVV10-POS-NEW-H1, PROVV10-POS-FAILED-COMMIT-ABSENCE, PROVV10-POS-ALIAS-CANONICAL, PROVV10-POS-SHARED-ROOT-DIAMOND, PROVV10-POS-SYNTH-NON-EVIDENCE]
  reject_or_mutation_fixture_ids: [PROVV10-REJ-PAIR-ORDER-DRIFT, PROVV10-REJ-POSITION-DRIFT, PROVV10-REJ-DIAMOND-FALSE-CYCLE, PROVV10-REJ-DUPLICATE-ROOT-INFLATION, PROVV10-REJ-REEXPRESSION-EVIDENCE]
  evidence_artifact: ProvenanceFiniteOrderReceiptV1
  failure_disposition: "INVALID provenance construction; false diamond rejection is also failure."
  claim_withdrawal: "Withdraw grounded-carrier, connected-memory, and connection-specificity clauses."

- test_id: M0V4-PROVENANCE-REVOCATION-CYCLE-27
  kind: invariant
  required_before: implementation
  acceptance: "Whole-batch structural validation, exact support, contradiction precedence, permanent transitive revocation, transform nonadmission, cycle rejection, corroboration, and atomic commit reproduce every section 3 fixture and rejected batches leave the store byte-identical."
  positive_fixture_ids: [PROVV10-POS-CORROBORATION, PROVV10-POS-REVOCATION-STATE, PROVV10-POS-ATOMIC-COMMIT]
  reject_or_mutation_fixture_ids: [PROVV10-REJ-ALIAS-UNKNOWN, PROVV10-REJ-ALIAS-DUPLICATE-SOURCE, PROVV10-REJ-ALIAS-SELF-OR-CYCLE, PROVV10-REJ-PARENT-UNKNOWN, PROVV10-REJ-PARENT-SELF-SAME-FORWARD, PROVV10-REJ-COLLAPSED-DAG-CYCLE, PROVV10-REJ-NONCANONICAL-PARENTS, PROVV10-REJ-NONCOMPOSABLE-PAIR, PROVV10-REJ-INCOMPLETE-PRIMITIVE-PARENTS, PROVV10-REJ-PREMATURE-VALIDATION, PROVV10-REJ-REUSED-DISCOVERY-ROOT, PROVV10-REJ-SYNTH-AS-PRIMITIVE, PROVV10-REJ-SYNTHETIC-ONLY-VALIDATION, PROVV10-REJ-UNREVOKE, PROVV10-REJ-TRANSFORM-EVIDENCE, PROVV10-REJ-BATCH-ATOMICITY]
  evidence_artifact: ProvenanceRevocationCycleReceiptV1
  failure_disposition: "INVALID provenance state; an invalid batch must leave the pre-batch store byte-identical."
  claim_withdrawal: "Withdraw every carrier-derived and connection-evidence clause."

- test_id: M0V5-HANDOFF-DELAYED-VISIBILITY-CLOSURE-28
  kind: invariant
  required_before: model_execution
  acceptance: "Accept iff the separately receipted public/private handoff, actor nonoracle, reset, carrier-only delayed test 13, baseline delayed test 29, rendered tests 09 and 31-33, and V7 tests 01/34 all pass, with no private route, truth, score, oracle, model/session, branch or V7 metadata reaching actor bytes."
  positive_fixture_ids: [HANDOFFV10-POS-PUBLIC-PRIVATE-CLOSURE, HANDOFFV10-POS-CARRIER-13-RECEIPT, HANDOFFV10-POS-BASELINE-29-RECEIPT, HANDOFFV10-POS-RENDER-09-31-32-33-RECEIPTS, HANDOFFV10-POS-V7-01-34-RECEIPTS]
  reject_or_mutation_fixture_ids: [HANDOFFV10-REJ-MISSING-DEPENDENCY-RECEIPT, HANDOFFV10-REJ-UMBRELLA-SUBSTITUTION, HANDOFFV10-REJ-PRIVATE-ROUTE-TRUTH-SCORE, HANDOFFV10-REJ-MODEL-SESSION-BRANCH, HANDOFFV10-REJ-V7-METADATA, HANDOFFV10-REJ-DELAYED-ENTITLEMENT-SPREAD]
  evidence_artifact: HandoffDelayedVisibilityClosureReceiptV1
  failure_disposition: "INVALID; this conjunction cannot substitute for any dependency receipt."
  claim_withdrawal: "Withdraw every scientific clause on any visibility or handoff failure."

- test_id: MTEXTV4-DELAYED-BASELINE-OUTCOME-DESCENDANT-29
  kind: invariant
  required_before: model_execution
  acceptance: "Baseline-only test: for RAW_STATIC, RAG_DETERMINISTIC and NATIVE_GRAPH_STATIC delayed conditions, accept iff the exact 35-row basis OLD_PUBLIC_ROWS[0..31], O41_ACQUIRE_SUCCESS at 32, O42_VALIDATE_P4 at 33, O43_VALIDATE_NH at 34 is preserved; only RAW rows 32/34, RAG document events 32/34 with stable d20/d22 handles, or native a19/l06 value leaves may differ across fixed-k twins; every difference has O41 visibility lineage; first-visible and dynamic-descendant closure, reset, registered opportunities and fixed pre-origin/static charges hold. Actual post-origin per-arm counters may differ only as receipted descendants of an entitled policy/query divergence."
  positive_fixture_ids: [DELAYV10-POS-BASELINE-35-ROW-BASIS, DELAYV10-POS-RAW-STATIC-TWINS, DELAYV10-POS-RAG-DETERMINISTIC-TWINS, DELAYV10-POS-NATIVE-GRAPH-TWINS, DELAYV10-POS-FIRST-VISIBLE-ORIGIN, DELAYV10-POS-DYNAMIC-DESCENDANT-CLOSURE, DELAYV10-POS-BASELINE-RESET, DELAYV10-POS-RESOURCE-OPPORTUNITY-EQUALITY]
  reject_or_mutation_fixture_ids: [DELAYV10-REJ-BASELINE-O40-OR-LIVE-U, DELAYV10-REJ-BASELINE-ROW-MOVE-OMIT-DUPLICATE-REORDER, DELAYV10-REJ-BASELINE-STABLE-HANDLE-RANK-COUNT-PAD, DELAYV10-REJ-BASELINE-FORBIDDEN-POINTER, DELAYV10-REJ-RAG-CORPUS-DIRECT-EXPOSURE, DELAYV10-REJ-PREORIGIN-SCORE-FINGERPRINT, DELAYV10-REJ-NONDESCENDANT-PROMPT-ERROR-CACHE-TIMING-BRANCH, DELAYV10-REJ-BASELINE-O41-LINEAGE, DELAYV10-REJ-AUTH-U-ENDPOINT-BORROW, DELAYV10-REJ-POSTORIGIN-RESOURCE-UNATTRIBUTED]
  evidence_artifact: DelayedBaselineOutcomeDescendantReceiptV1
  failure_disposition: "INVALID affected baseline delayed treatment; test 13 cannot rescue it."
  claim_withdrawal: "Withdraw the affected delayed-baseline comparison and any practical clause requiring it; never infer retention, acquisition-to-use, self-write, or learning."

- test_id: M0V4-LOCAL-EDGE-NO-PREASSEMBLED-PATH-30
  kind: invariant
  required_before: model_execution
  acceptance: "Accept iff actor-visible memory contains only one-STEP PublicAtomV4 objects and PublicAuthLinkV4 objects joining exactly two adjacent atoms; one return has at most one atom, one incident local link and its opposite endpoint atom; both A/B alternatives require sequential legal reads; no explicit or encoded route, plan, script, answer, transitive edge, multi-handle sequence, target cursor map or full-path return exists."
  positive_fixture_ids: [LOCALV10-POS-A-UPPER-SEQUENTIAL, LOCALV10-POS-A-LOWER-SEQUENTIAL, LOCALV10-POS-B-UPPER-SEQUENTIAL, LOCALV10-POS-B-LOWER-SEQUENTIAL, LOCALV10-POS-SYMMETRIC-SCORING]
  reject_or_mutation_fixture_ids: [LOCALV10-REJ-COMPLETE-SCRIPT, LOCALV10-REJ-GOAL-TO-PATH-OR-ANSWER, LOCALV10-REJ-PREFERRED-PARENT-PATH, LOCALV10-REJ-TRANSITIVE-LINK, LOCALV10-REJ-MULTI-HANDLE-OR-NEXT-POINTER, LOCALV10-REJ-TARGET-INDEXED-CURSOR, LOCALV10-REJ-FULL-PATH-RETURN, LOCALV10-REJ-PADDING-ORDER-LENGTH-HANDLE-ENCODING]
  evidence_artifact: LocalEdgeNoPreassembledPathReceiptV1
  failure_disposition: "INVALID memory instrument before model execution."
  claim_withdrawal: "Withdraw recalled-link composition and connected-route construction language."

- test_id: MTEXTV4-ABANDONED-BRANCH-NONRELEASE-31
  kind: invariant
  required_before: model_execution
  acceptance: "Accept iff paired branch/join fixtures with identical active public projection render byte-identically from join through terminal in system, user, template, token IDs, tool envelopes, parser state and cache inputs after independent mutation of every abandoned branch scratch, plan, belief, read, command, return, failure, timing, sibling handle, padding, cache, session and private score field; no abandoned object is a later provenance parent."
  positive_fixture_ids: [BRANCHV10-POS-A-UPPER-LOWER-JOIN, BRANCHV10-POS-B-UPPER-LOWER-JOIN, BRANCHV10-POS-D-TERMINAL-JOIN, BRANCHV10-POS-ALL-TERMINAL-FORMS]
  reject_or_mutation_fixture_ids: [BRANCHV10-REJ-SCRATCH-PLAN-BELIEF, BRANCHV10-REJ-READ-COMMAND-RETURN, BRANCHV10-REJ-FAILURE-ERROR-TIMING, BRANCHV10-REJ-SIBLING-HANDLE-PADDING, BRANCHV10-REJ-CACHE-SESSION, BRANCHV10-REJ-PRIVATE-SCORE-ORACLE, BRANCHV10-REJ-PROVENANCE-PARENT]
  evidence_artifact: AbandonedBranchNonreleaseReceiptV1
  failure_disposition: "INVALID actor/render boundary."
  claim_withdrawal: "Withdraw every scientific clause."

- test_id: MTEXTV4-REPEAT-STATE-POLICY-VISIBILITY-32
  kind: invariant
  required_before: model_execution
  acceptance: "Accept iff every legal memory return visibly carries repeat_count=min(3,1+n_prior byte-identical requests in the same phase), yielding 1,2,3,3,3,3,3,3 over eight identical requests; anchor identity is exact anchor_utf8 plus cursor, RAG identity is exact registered query bytes, blocked post-action RAG uses zero-length query identity; the same saturated value enters fingerprints; counters do not cross request identity, root, phase or condition and reset destroys them."
  positive_fixture_ids: [REPEATV10-POS-COMMON-READER-EIGHT, REPEATV10-POS-BLOCKED-READER-EIGHT, REPEATV10-POS-PASSIVE-NULL-READER-EIGHT, REPEATV10-POS-RAG-DETERMINISTIC-EIGHT, REPEATV10-POS-INDEPENDENT-IDENTITIES, REPEATV10-POS-RESET-RESTART]
  reject_or_mutation_fixture_ids: [REPEATV10-REJ-OMITTED-OR-HIDDEN, REPEATV10-REJ-UNSATURATED-4-THROUGH-8, REPEATV10-REJ-FINGERPRINT-MISMATCH, REPEATV10-REJ-CROSS-IDENTITY-ROOT-PHASE-CONDITION, REPEATV10-REJ-RESET-SURVIVAL, REPEATV10-REJ-FAILED-FOREIGN-NOT-REACHED-INCREMENT]
  evidence_artifact: RepeatStatePolicyVisibilityReceiptV1
  failure_disposition: "INVALID rendered memory mechanism."
  claim_withdrawal: "Withdraw memory-mechanism and rendered-boundary clauses."

- test_id: MTEXTV4-PROMPT-PROTOCOL-SCHEMA-CROSSPRODUCT-33
  kind: invariant
  required_before: model_execution
  acceptance: "Accept iff every legal row of the exact section-2 V7 mode/protocol table crossed with P/D relation-finish-abstain stages and U experiment e0..e3 then commit c0/c1/abstain stages advertises each legal PCFL_COMMAND_V4 form exactly once and prompt, schema and parser agree; all other combinations reject. TARGET_ONLY is BLOCKED_READER/BLOCKED_ANCHOR_CURSOR open-loop and AUTH_NO_FEEDBACK uses COMMON_READER/ANCHOR_CURSOR open-loop with no future handle."
  positive_fixture_ids: [PROTOCOLV10-POS-COMMON-ANCHOR-CURSOR, PROTOCOLV10-POS-BLOCKED-ANCHOR-CURSOR, PROTOCOLV10-POS-PASSIVE-NULL-ANCHOR-CURSOR, PROTOCOLV10-POS-RAW-STATIC-NONE, PROTOCOLV10-POS-RAG-DETERMINISTIC-AUTO, PROTOCOLV10-POS-NATIVE-GRAPH-NONE, PROTOCOLV10-POS-NO-MEMORY-SURFACE-NONE, PROTOCOLV10-POS-P-D-TERMINALS, PROTOCOLV10-POS-U-STAGES]
  reject_or_mutation_fixture_ids: [PROTOCOLV10-REJ-MODE-PROTOCOL-MISMATCH, PROTOCOLV10-REJ-READ-UNDER-NONE, PROTOCOLV10-REJ-RAG-READ-ARGUMENT, PROTOCOLV10-REJ-U-RELATION, PROTOCOLV10-REJ-WRONG-STAGE-COMMIT, PROTOCOLV10-REJ-POST-CLOSE-LOOKUP, PROTOCOLV10-REJ-FUTURE-HANDLE, PROTOCOLV10-REJ-UNADVERTISED-OR-UNKNOWN-COMMAND, PROTOCOLV10-REJ-PROMPT-SCHEMA-PARSER-DISAGREEMENT]
  evidence_artifact: PromptProtocolSchemaCrossproductReceiptV1
  failure_disposition: "INVALID affected condition; INCOMPLETE assay if any confirmation cell is lost."
  claim_withdrawal: "Withdraw every clause requiring the affected condition and the combined maximum if mandatory completeness fails."

- test_id: M0V4-V7-GUARD-EXCEPTION-NONEXPOSURE-34
  kind: invariant
  required_before: materialization
  acceptance: "The exact C10 boundary has only the governance-private custody accesses in section 5 and one candidate/preparation/runtime semantic consumer, V7_BOUNDARY_GUARD; its only downstream output is the exact four-field pass projection with the literal sorted 22-path allowlist; boundary metadata never crosses that projection."
  positive_fixture_ids: [V7V10-POS-BOUNDARY-C10-BINDING, V7V10-POS-GOVERNANCE-CUSTODY, V7V10-POS-SOLE-GUARD-CONSUMER, V7V10-POS-BOUNDARY-PROVENANCE, V7V10-POS-NONEXPOSURE-TWIN, V7V10-POS-FAIL-CLOSED]
  reject_or_mutation_fixture_ids: [V7V10-REJ-SECOND-SEMANTIC-CONSUMER, V7V10-REJ-GOVERNANCE-ACCESS-PROJECTION, V7V10-REJ-GUARD-OPENS-DENIED, V7V10-REJ-PROJECTION-PATHSET, V7V10-REJ-PROJECTION-EXTRA-FIELD, V7V10-REJ-FAILURE-PROJECTION, V7V10-REJ-INDIRECT-CHANNEL, V7V10-REJ-BOUNDARY-COPY, V7V10-REJ-EMBEDDED-SELF-HASH, V7V10-REJ-BOUNDARY-PROVENANCE-SOURCE]
  evidence_artifact: V7GuardExceptionNonexposureReceiptV1
  failure_disposition: "INVALID before materialization; emit no projection or prepared output."
  claim_withdrawal: "Withdraw clean-room status and every scientific clause."
```

The registry has no active `MTEXTV4-RESOURCE-FACTORIAL-19`; that rejected
draft alias cannot coexist with
`MTEXTV4-BASELINE-PUBLIC-PROJECTION-AND-RESET-19`. Tests 23, 24, and 25 own
roster, vector, and meter obligations separately. Test 28 is a conjunction
receipt, never a substitute for tests 01, 03, 05, 09, 13, 19, or 29–34.

The deferred identifiers are exactly:

```text
MTEXTV4-SCORER-ORACLE-NONCAUSALITY-20
FUTURE-PCFL-MULTITOPOLOGY-GENERALIZATION-21
FUTURE-PCFL-ONLINE-ACTION-OUTCOME-WRITE-ACTION-22
FUTURE-PCFL-TEXT-LORA-MATCHED-TRANSPORT-35
FUTURE-PCFL-RECALL-COMPOSITION-PLANNING-DECOMPOSITION-36
FUTURE-PCFL-LONGITUDINAL-ACTIVE-TEXT-PLATEAU-37
```

### 3.1 Exact provenance semantics and fixture corpus

This subsection is the section-3 contract referenced literally by tests 26
and 27.

The unsigned lexicographic coordinate is exactly
`Position=(major:u8,lane:u8,ordinal:u16)`. Lane 0 is the ordinary event at a
major position; lane 1 is its post-event synthesis. Reserved absent positions
never renumber. The authoritative pair registry is exactly:

| ordinal | position | pair |
|---:|---|---|
| 0 | `(24,1,0)` | `(p0,p1)` |
| 1 | `(24,1,1)` | `(p2,p3)` |
| 2 | `(24,1,2)` | `(p1,p4)` |
| 3 | `(24,1,3)` | `(p3,p4)` |
| 4 | `(24,1,4)` | `(p4,p5)` |
| 5 | `(24,1,5)` | `(p4,p6)` |
| 6 | `(41,1,6)` | `(p4,nh)` iff `nh` was admitted |

`FactKey=(src_ordinal,relation_ordinal,dst_ordinal)` and
`PairKey=(FactKey(left),FactKey(right))` use unsigned numeric tuple order.
Public aliases, semantic hashes, paths, goal, score, condition, filesystem
order, and wall time never order evidence. Alias edges must be strictly
decreasing by raw digest and are resolved transitively before node identity,
parent sorting, root calculation, support, contradiction, cycle, or render.

```text
roots(ROOT r)  = {canonical_id(r)}
roots(SYNTH s) = set_union(roots(parent) for parent in parents(s))
roots(ALIAS a) = roots(resolve(a))
```

Root sets contain only canonical primitive ROOT IDs. SYNTH and REEXPRESSION
IDs never become evidence; aliases and sinks never count twice. A shared-root
diamond is legal and root-deduplicated. A `PAIR_PROPOSAL` cites the complete
canonical primitive ROOT set for both endpoint FactKeys at the proposal cut.
Support requires strictly later independent primitive ROOT evidence disjoint
from discovery roots. A REEXPRESSION adds no root and cannot validate or
render a pair. Only SUPPORTED, non-REVOKED PAIR_PROPOSAL nodes render.

The exact test-26 fixture results are:

| fixture ID | exact required result |
|---|---|
| `PROVV10-POS-OLD-SIX-ORDER` | Old-cut evidence produces exactly ordinals 0--5 at `(24,1,0..5)` and exactly six supported links after positions 25--31 validate their endpoints. |
| `PROVV10-POS-NEW-H0` | Admitted `nh=C-R07->D` produces only ordinal 6 at `(41,1,6)` and renders only after independent p4/nh validations at 42/43. |
| `PROVV10-POS-NEW-H1` | Admitted `nh=C-R08->D` has the same ordinal/position and the same later-support law. |
| `PROVV10-POS-FAILED-COMMIT-ABSENCE` | With no admitted nh ROOT, `(41,1,6)` and validation 43 are reserved but absent and no seventh link exists. |
| `PROVV10-POS-ALIAS-CANONICAL` | Direct and strictly decreasing alias citations collapse to one sorted parent ID and yield identical SYNTH ID, roots, status, and rendering. |
| `PROVV10-POS-SHARED-ROOT-DIAMOND` | For `s0=[r0,r1]`, `s1=[r0,r2]`, and `s2=[s0,s1]`, accept and require `roots(s2)={r0,r1,r2}`; shared `r0` is neither doubled nor a cycle. |
| `PROVV10-POS-SYNTH-NON-EVIDENCE` | REEXPRESSION `x1=[x0]` is accepted structurally, `roots(x1)=roots(x0)`, neither synthetic ID is a root, and x1 alone supports and renders nothing. |
| `PROVV10-REJ-PAIR-ORDER-DRIFT` | Reject any swap, omission, duplicate, or eighth authoritative pair. |
| `PROVV10-REJ-POSITION-DRIFT` | Reject changed major/lane/ordinal, wall-time ordering, renumbering after absence, or nondeterministic tie. |
| `PROVV10-REJ-DIAMOND-FALSE-CYCLE` | The exact legal shared-root diamond must not be rejected as cyclic. |
| `PROVV10-REJ-DUPLICATE-ROOT-INFLATION` | Reject root multisets, alias/sink double count, or repeated shared-root support. |
| `PROVV10-REJ-REEXPRESSION-EVIDENCE` | Reject any support, Link, or TransitionRow obtained from synthetic-only evidence. |

Whole-batch alias, schema, canonical-ID, parent, position, and cycle checks
complete before support, contradiction, revocation, rendering, or write.
Rejected batches leave the pre-batch store byte-identical. For a structurally
valid batch the exact precedence is:

```text
BATCH_REJECT > REVOKED > SUPPORTED > PENDING/SUPPORT_REJECT
```

A later identical FactKey ROOT is corroboration. A later ROOT with the same
`(src,rel)` and different `dst` permanently revokes every dependent proposal
and transitive SYNTH descendant. Later matching evidence, aliasing,
rerendering, or reproposal cannot un-revoke it.

The exact test-27 dispositions are:

| fixture ID | exact disposition |
|---|---|
| `PROVV10-POS-CORROBORATION` | Valid commit; later identical FactKey ROOT supplies applicable independent support and creates no conflict. |
| `PROVV10-POS-REVOCATION-STATE` | Valid commit; contradiction makes the pair and all transitive dependents permanently REVOKED and removes rendered rows. |
| `PROVV10-POS-ATOMIC-COMMIT` | A wholly valid multi-object batch commits every canonical object exactly once. |
| `PROVV10-REJ-ALIAS-UNKNOWN` | `BATCH_REJECT`: unknown target. |
| `PROVV10-REJ-ALIAS-DUPLICATE-SOURCE` | `BATCH_REJECT`: one source has two targets. |
| `PROVV10-REJ-ALIAS-SELF-OR-CYCLE` | `BATCH_REJECT`: self, nondecreasing, or cyclic alias edge. |
| `PROVV10-REJ-PARENT-UNKNOWN` | `BATCH_REJECT`: collapsed parent absent. |
| `PROVV10-REJ-PARENT-SELF-SAME-FORWARD` | `BATCH_REJECT`: self, same-position, or later parent. |
| `PROVV10-REJ-COLLAPSED-DAG-CYCLE` | `BATCH_REJECT`: alias collapse exposes a dependency cycle. |
| `PROVV10-REJ-NONCANONICAL-PARENTS` | `BATCH_REJECT`: unresolved, duplicated, unsorted, or ID-mismatched parent array. |
| `PROVV10-REJ-NONCOMPOSABLE-PAIR` | `SUPPORT_REJECT`: `left==right` or `left.dst!=right.src`. |
| `PROVV10-REJ-INCOMPLETE-PRIMITIVE-PARENTS` | `SUPPORT_REJECT`: missing endpoint ROOT, foreign FactKey, or SYNTH substitution. |
| `PROVV10-REJ-PREMATURE-VALIDATION` | `SUPPORT_REJECT`: validation is not strictly later. |
| `PROVV10-REJ-REUSED-DISCOVERY-ROOT` | `SUPPORT_REJECT`: proposal and validation root sets intersect. |
| `PROVV10-REJ-SYNTH-AS-PRIMITIVE` | `BATCH_REJECT`: synthetic node declared primitive. |
| `PROVV10-REJ-SYNTHETIC-ONLY-VALIDATION` | `SUPPORT_REJECT`: no later primitive evidence. |
| `PROVV10-REJ-UNREVOKE` | `VALID_REVOKED`: all attempted restoration leaves the item REVOKED. |
| `PROVV10-REJ-TRANSFORM-EVIDENCE` | `BATCH_REJECT`: transform adds evidence, support, contradiction, revocation, or position. |
| `PROVV10-REJ-BATCH-ATOMICITY` | `BATCH_REJECT`: malformed final object causes zero persistent mutation. |

## 4. Exact algebra, producer/scorer, and local-edge laws

### 4.1 Algebra-prior decoder and noncompensatory shortcut bound

The model-free decoder reads only the released start alias, released target
alias/goal label, and fixed relation catalog. Parse
`node_alias(S)="n"+lower_hex2(k)`, set `m=k mod 16`, and define:

```text
rho(j,k) = "r" + lower_hex2(j XOR m)

ALG_A_0(k) = [rho(0,k),rho(1,k),rho(4,k),rho(5,k)]
ALG_A_1(k) = [rho(2,k),rho(3,k),rho(4,k),rho(5,k)]
ALG_B_0(k) = [rho(0,k),rho(1,k),rho(4,k),rho(6,k)]
ALG_B_1(k) = [rho(2,k),rho(3,k),rho(4,k),rho(6,k)]
ALG_D_guess(q,upper,k) = [rho(0,k),rho(1,k),rho(4,k),rho(7+q,k)]
ALG_D_guess(q,lower,k) = [rho(2,k),rho(3,k),rho(4,k),rho(7+q,k)]
q in {0,1}, chosen without h
```

Both A and B alternatives must score successful for all 32 `k`. D's fixed
choice consumes all four relation attempts and has twin-minimum success zero.
The decoder may not read carrier, return, public ledger, `h`, condition,
split, score, answer, semantic ID, or checker oracle.

For
`e in {task_success_A,task_success_B,two_goal_task_success,
delayed_task_success}` and
`c in {TARGET_ONLY_ANSWER_PRIOR_TAPE,NO_MEMORY_RECURRENT,
PASSIVE_SIGNATURE_RECURRENT}`:

```text
shortcut_count(e,c) = sum_{k in 16 CONFIRMATION k-blocks}
                        min_{h in {0,1}} e(k,h,c)
accept iff every applicable shortcut_count(e,c) <= 5
```

All 32 same-cell inputs must be Boolean and terminally receipted. Missing,
foreign, invalid, or `NA` input is not a pass. `SHORTCUT_BREACH` is not
averaged away.

### 4.2 Producer/query/reader/scorer swaps

Producer and index inputs are exactly
`(instrument_version,k,h,public primitive events,frozen slot map,registered
transform,phase cut)`. Goal, target, expected answer, preferred/reference
path, score, model output, condition name, split, dispatch order, scorer, and
oracle are absent. Goal release and scorer construction occur after sealed
carrier/index hashes. The reader is a pure function of
`(carrier_sha256,anchor,cursor,reader_open,repeat_state)`. The scorer receives
only the sealed trace after its final receipt and has no upstream edge.

| Fixture | Exact invariant |
|---|---|
| `PQS-PRODUCER-GOAL` | Swap A/B/D goal and target; carrier/index bytes, handles, rows and candidate order are identical. |
| `PQS-PRODUCER-ANSWER` | Answer/path/reference fields are rejected; sealed objects remain identical. |
| `PQS-READER-GOAL` | Swap goal/target; return bytes and grants are identical. |
| `PQS-READER-SCORE` | Swap scores/split/oracle across the complete anchor/cursor agenda; returns and order are identical. |
| `PQS-PATH-ORDER` | Reverse scorer upper/lower enumeration; producer/reader/render bytes and score are identical. |
| `PQS-SCORE-LABEL` | Correct versus wrong private label changes no upstream byte/action; only private score changes or rejects. |
| `PQS-SCORER-ABSENCE` | Delete/corrupt scorer after an unscored receipt; no re-execution or request/action change; assay becomes invalid/incomplete. |

The positive paths are exactly:

```text
A: [p0,p1,p4,p5]  [p2,p3,p4,p5]
B: [p0,p1,p4,p6]  [p2,p3,p4,p6]
D: [p0,p1,p4,nh]  [p2,p3,p4,nh]
```

Each scores symmetrically only when its atoms/links were returned and cited.

### 4.3 Local-edge grammar

Actor-visible memory items are exactly:

```text
PublicAtomV4(atom_handle, public_atom_payload)             # one STEP atom
PublicAuthLinkV4(link_handle, left_atom_handle,
                 right_atom_handle, public_link_payload)   # one adjacent pair
```

One return contains at most one atom, one incident local link, and the
opposite endpoint atom needed to interpret that link. It cannot contain three
ordered atom handles, two ordered link handles, a recursive carrier, a
transitive link, or any `route`, `path`, `plan`, `script`, `answer`,
`goal_to_path`, `parent_path`, `next_steps`, `agenda`, target cursor map, or
full-path field. Route/answer bits in order, duplicates, padding, length,
aliases, cursors, errors, cache keys, or handles reject. The lawful set of
local items may support reconstruction only through successive authorized
reads within the unchanged budget.

### 4.4 Closed C10 resource contract

This subsection is the section-4 contract referenced literally by tests 24
and 25. It is reproduced here so those registry records have no unstated
schema, reduction, or fixture dependency.

#### 4.4.1 Types and scoped supersession

In this subsection:

- `u64` is a JSON integer in `[0,18446744073709551615]`;
- `measure` is `u64` or the literal JSON string `"NA"`;
- `hex64` is a lowercase 64-character hexadecimal JSON string;
- `nfc_string` is a nonempty NFC UTF-8 JSON string without control bytes;
- `condition` is exactly one of the 18 condition strings in section 1;
- `phase` is exactly `PROBE_A`, `PROBE_B`, `UNCERTAINTY_ACQUIRE`, or
  `DELAYED_GOAL`; `mode` is exactly `R`, `B`, or `T`; and
- `split` is exactly `DEV`, `CONFIRMATION`, `RESERVE`, or `SENTINEL`.

The `ChargedResourceV10.identity.mode` treatment code `R|B|T` is orthogonal
to `PublicMemorySurfaceV4.mode`; it is not a public-memory enum or alias and
cannot substitute for the exact section-2 vocabulary.

For an `ARM` record every identity value is non-`NA` and matches the C10
roster. For the sole `COMMON` record, `root_receipt_id`, `condition`, `phase`,
`mode`, and `split` are each the literal `"__COMMON__"`; every digest remains
`hex64`. All numeric leaves are `measure` unless explicitly typed `u64`.
`0` means applicable and unused. `"NA"` is legal only where the closed
applicability matrix in C10 `resource_roster_v4.json` says the resource class
does not exist; missing is never zero or NA. Arrays are ordered as stated.
Every object is closed recursively: a missing or extra key, duplicate key,
wrong type, unsorted array, duplicate array identity, negative number,
floating point number, exponent notation, or integer outside `u64` rejects.

`ChargedResourceV10` supersedes `ChargedResourceV5` only for the C10 candidate,
C10 tests 24/25, and future receipts derived from those C10 bytes. It does not
rename, modify, reinterpret, validate, or invalidate any V5--V9 artifact. A C10
registry or receipt naming `ChargedResourceV5`, accepting both versions, or
coercing one into the other rejects.

#### 4.4.2 Exact `ChargedResourceV10`

```text
ChargedResourceV10 := {
  schema_version: 10,
  artifact_type: "pcfl_charged_resource_v10",
  identity: {
    record_kind: "ARM" | "COMMON",
    scope_id: hex64,
    root_receipt_id: nfc_string,
    condition: condition | "__COMMON__",
    phase: phase | "__COMMON__",
    mode: mode | "__COMMON__",
    split: split | "__COMMON__",
    model_sha256: hex64,
    tokenizer_sha256: hex64,
    chat_template_sha256: hex64,
    renderer_sha256: hex64,
    parser_sha256: hex64,
    controller_sha256: hex64,
    scorer_sha256: hex64,
    runtime_sha256: hex64,
    device_manifest_sha256: hex64,
    meter_manifest_sha256: hex64,
    cas_object_ledger_sha256: hex64
  },
  opportunity: {
    registered_slots: u64,
    slots_request_emitted: u64,
    slots_not_reached: u64,
    maximum_input_tokens: u64,
    registered_generation_allowance: u64,
    offered_generation_allowance: u64,
    read_opportunities: u64,
    world_action_opportunities: u64,
    terminal_opportunities: u64
  },
  stored: {
    raw_event_bytes: measure,
    atom_bytes: measure,
    link_bytes: measure,
    common_index_bytes: measure,
    rag_index_bytes: measure,
    native_graph_bytes: measure,
    static_context_bytes: measure,
    prompt_source_bytes: measure,
    raw_event_tokens: measure,
    atom_tokens: measure,
    link_tokens: measure,
    static_context_tokens: measure
  },
  build: {
    common_fixture_cpu_ns: measure,
    graph_build_cpu_ns: measure,
    index_build_cpu_ns: measure,
    cache_warmup_cpu_ns: measure,
    render_cpu_ns: measure,
    controller_cpu_ns: measure,
    scorer_cpu_ns: measure,
    common_fixture_peak_rss_bytes: measure,
    graph_build_peak_rss_bytes: measure,
    index_build_peak_rss_bytes: measure,
    cache_warmup_peak_rss_bytes: measure
  },
  reader: {
    invocations: measure,
    found_returns: measure,
    not_found_returns: measure,
    blocked_returns: measure,
    candidate_rows_examined: measure,
    postings_touched: measure,
    documents_returned: measure,
    atom_records_returned: measure,
    link_records_returned: measure,
    return_utf8_bytes: measure,
    return_tokens: measure,
    reader_cpu_ns: measure
  },
  thinker: {
    calls_attempted: u64,
    calls_completed: u64,
    calls_failed: u64,
    input_tokens: u64,
    input_system_tokens: u64,
    input_protocol_tokens: u64,
    input_state_tokens: u64,
    input_static_context_tokens: u64,
    input_reader_return_tokens: u64,
    input_prior_scratch_tokens: u64,
    input_other_tokens: u64,
    generated_tokens: u64,
    decoded_utf8_bytes: u64,
    service_latency_ns: u64,
    arm_wall_span_ns: u64,
    gpu_device_charges: [{
      physical_device_uuid: nfc_string,
      active_ns: u64,
      peak_memory_bytes: u64
    }, ...],
    peak_worker_rss_bytes: u64
  },
  behavior_work: {
    successful_world_actions: u64,
    no_effect_world_actions: u64,
    other_unsuccessful_world_actions: u64,
    total_world_actions: u64,
    terminal_commands: u64,
    controller_tool_operations: u64
  },
  artifacts: {
    request_bytes: u64,
    response_bytes: u64,
    tool_return_bytes: u64,
    trace_bytes: u64,
    receipt_bytes: u64,
    log_bytes: u64,
    other_installed_bytes: u64,
    temporary_bytes_written: u64,
    temporary_bytes_deleted: u64,
    standalone_cas_object_count: u64,
    standalone_cas_bytes: u64
  },
  external: {
    network_requests: u64,
    network_rx_bytes: u64,
    network_tx_bytes: u64,
    external_cost_microusd: u64
  }
}
```

`scope_id` is the SHA-256 identity of the canonical tuple
`(record_kind,root_receipt_id,condition,phase,mode,split)` encoded by the C10
schema. `gpu_device_charges` is bytewise sorted by UUID and has at most one
entry per physical device. In the frozen local assay all three network fields
and `external_cost_microusd` are exactly zero; any nonzero value invalidates
the proposal rather than recording an allowed resource.

#### 4.4.3 Exact component laws

The following equalities are noncompensatory:

```text
slots_request_emitted + slots_not_reached = registered_slots

calls_completed + calls_failed = calls_attempted

found_returns + not_found_returns + blocked_returns = invocations

input_tokens = input_system_tokens + input_protocol_tokens
             + input_state_tokens + input_static_context_tokens
             + input_reader_return_tokens + input_prior_scratch_tokens
             + input_other_tokens

total_world_actions = successful_world_actions
                    + no_effect_world_actions
                    + other_unsuccessful_world_actions
```

Registered allowance includes sealed `NOT_REACHED`; offered and actual
counters do not. Static content is charged once as resident storage and again
in `input_static_context_tokens` on every emitted request containing it. RAG
charges raw documents, index bytes, index build, cache warmup, query CPU,
candidate rows, postings, returned documents/envelopes/tokens, and every later
request that contains a return. Common readers charge found/null/blocked
invocations, fixed envelopes, serialization, hashing, returned records, and
reader CPU. Every attempted, failed, tape, retry, and sentinel thinker call is
metered; no retry is thereby authorized.

Actual counts, bytes, CPU, latency, GPU, memory, and artifacts remain measured
outcomes. Sums reduce by sum, peaks by `max`, wall span by
`max(end)-min(start)`, and physical GPU hours by
`sum(active_ns)/3,600,000,000,000`. No A40-equivalent conversion, imputation,
or scalar efficiency score exists.

#### 4.4.4 Standalone and physical CAS

`CasObjectChargeV10` is a closed ledger row:

```text
{
  sha256: hex64,
  nbytes: u64,
  category: "RAW_EVENT" | "ATOM" | "LINK" | "COMMON_INDEX" |
            "RAG_INDEX" | "NATIVE_GRAPH" | "STATIC_CONTEXT" |
            "PROMPT_SOURCE" | "REQUEST" | "RESPONSE" | "TOOL_RETURN" |
            "TRACE" | "RECEIPT" | "LOG" | "OTHER_INSTALLED" | "TEMPORARY",
  owner_scope_id: hex64,
  reachable_scope_ids: [hex64, ...]
}
```

Rows are sorted by `(sha256,category,owner_scope_id)` and
`reachable_scope_ids` is bytewise sorted and duplicate-free. Same bytes under
two digests or different bytes under one digest reject.

For arm scope `a` and a reduction scope `S`:

```text
Closure(a) = distinct ledger digests whose reachable_scope_ids contains a
standalone_cas_bytes(a) = sum(nbytes(o) for o in Closure(a))
physical_cas_bytes(S) = sum(nbytes(o) for o in union(Closure(a) for a in S))
```

An object counts fully for every standalone arm that needs it, never a
fraction. Physical storage counts its digest once. Common preparation is
recorded once in `COMMON`; each standalone arm reports `COMMON + arm-specific`
work, while a suite-physical reduction reports `COMMON once + arm-specific`
work. Reduction receipts are distinct artifacts, state scope membership
explicitly, and report `physical_cas_object_count` and `physical_cas_bytes`;
they are not per-arm `ChargedResourceV10` records.

`RESOURCEV10-POS-CAS-STANDALONE-PHYSICAL` has common objects of 10 and 20
bytes, A-only 7 bytes, and B-only 11 bytes. It requires:

```text
standalone(A) = 37
standalone(B) = 41
physical(A union B) = 48
```

`78`, `22`, fractional sharing, or omission is invalid.

#### 4.4.5 Raw meter events and post-origin causal descendants

Every measured contribution has exactly one closed raw row:

```text
ResourceMeterEventV10 := {
  schema_version: 10,
  artifact_type: "pcfl_resource_meter_event_v10",
  event_id: hex64,
  event_kind: "BUILD" | "STORE" | "READ" | "RENDER" | "THINKER" |
              "WORLD_ACTION" | "ARTIFACT_WRITE" | "ARTIFACT_DELETE" |
              "NETWORK" | "EXTERNAL_COST",
  charge_scope_id: hex64,
  originating_scope_id: hex64,
  slot_id: nfc_string | "NA",
  causal_parent_event_ids: [hex64, ...],
  metric_json_pointer: nfc_string,
  amount: u64,
  unit: "COUNT" | "BYTE" | "TOKEN" | "NANOSECOND" | "MICROUSD",
  source_receipt_sha256: hex64
}
```

Objects are closed; parent IDs are bytewise sorted and duplicate-free;
`metric_json_pointer` names exactly one numeric leaf in the applicable
`ChargedResourceV10` or common receipt. `event_id` hashes the canonical row
with `event_id` omitted. A row maps to exactly one leaf and one charge scope.
Every leaf equals the exact reduction of all and only its mapped rows.

Resource and evidence provenance are not interchangeable. A datum may descend
from an earlier O41/O42/O43 evidence event, but each later build, storage,
reader, render, request-token, model, action, or artifact operation is a new
meter event charged where that operation executes. Thus every D baseline use
of an outcome descendant charges its D arm's static/index/reader/render/input
work; it is not back-charged to AUTH U, hidden in `COMMON`, or assigned to the
content's provenance root. Conversely, actual common construction remains
owned once by `COMMON`; standalone closure includes it fully and physical
reduction includes it once. A descendant never erases, moves, or substitutes
for its origin event, and a causal edge never supplies a free charge.

`RESOURCEV10-POS-POST-ORIGIN-DESCENDANT` fixes one common 100-byte descendant,
one D-arm 20-ns retrieval, one 40-byte return, and two later requests each
containing 12 return tokens. Require common stored bytes 100; D reader CPU 20;
D return bytes 40; D reader-return input tokens 24; and no corresponding
charge in the originating U arm. `RESOURCEV10-REJ-CAUSAL-REALLOCATION`
independently moves each contribution to origin, COMMON, another arm, or no
arm and must reject.

#### 4.4.6 Remaining resource fixtures

- `RESOURCEV10-POS-CLOSED-SCHEMA`: all exact keys/types and no extras pass.
- `RESOURCEV10-POS-FULL-VECTOR-ZERO-NA`: legitimate zero and matrix-authorized
  NA remain distinct from missing.
- `RESOURCEV10-POS-STATIC-REPEATED`: 100 stored static tokens in three emitted
  requests gives 100 stored and 300 input-static tokens.
- `RESOURCEV10-POS-RAG-WORK`: nonzero build, warmup, query, candidates,
  postings, four-document return, return-token, later-input, and artifact
  leaves reconcile.
- `RESOURCEV10-POS-BLOCKED-READER`: one blocked call has one invocation, fixed
  return bytes/tokens, and zero candidate rows/postings.
- `RESOURCEV10-POS-NOT-REACHED`: registered ceilings include an unissued
  suffix; offered and actual counters exclude it.
- `RESOURCEV10-POS-COMPONENT-REDUCTION`: sums, maxima, wall interval, CAS
  union, and physical-device GPU conversion reproduce their goldens.
- `RESOURCEV10-POS-METER-CAPABILITY-CLOSURE`: the capability manifest names
  every process, thread, subprocess, file/CAS, index/cache, reader, model,
  device, network, and artifact-write path and no other path is reachable.
- `RESOURCEV10-POS-METER-LEAF-RECONCILIATION`: every vector numeric leaf
  equals its raw rows exactly once.
- `RESOURCEV10-POS-CAUSAL-SCOPE-RECONCILIATION`: every post-origin descendant
  retains its causal parents and charges its actual execution scope.

The negative fixtures are individual and noncompensatory:

- `RESOURCEV10-REJ-V5-SCHEMA-NAME` substitutes `ChargedResourceV5`, a dual
  version, or a compatibility coercion; reject.
- `RESOURCEV10-REJ-MISSING-FIELD`, `RESOURCEV10-REJ-EXTRA-FIELD`, and
  `RESOURCEV10-REJ-WRONG-TYPE` independently delete, add, or mistype one leaf
  at every object depth; every case rejects.
- `RESOURCEV10-REJ-ZERO-NA-MISSING` independently substitutes each member of
  the three-way distinction for another; reject.
- `RESOURCEV10-REJ-STATIC-ONCE-ONLY` charges resident static storage but omits
  one or more emitted-request static token segments; reject.
- `RESOURCEV10-REJ-RAG-BUILD-OR-POSTINGS-FREE` independently omits document
  storage, index build, warmup, query, candidates, postings, return, or
  downstream return-token input; reject each case.
- `RESOURCEV10-REJ-COMMON-READER-FREE` omits a found/null/blocked invocation,
  fixed envelope, serialization, record, hashing, or CPU contribution; reject.
- `RESOURCEV10-REJ-HIDDEN-THINKER-CALL` omits a background, retry, sentinel,
  failed, tape, or ordinary attempt; reject.
- `RESOURCEV10-REJ-CAS-DIVIDED-STANDALONE` fractionally allocates or omits a
  shared object from an arm closure; reject.
- `RESOURCEV10-REJ-CAS-SUMMED-PHYSICAL` sums standalone closures instead of
  taking the digest union; reject.
- `RESOURCEV10-REJ-CAS-DIGEST-ALIAS` admits identical bytes under two digests
  or different bytes under one digest; reject.
- `RESOURCEV10-REJ-DELETED-TEMP-FREE` deletes a written request, response,
  index, cache, trace, log, or other temporary object without both counters;
  reject.
- `RESOURCEV10-REJ-CPU-WARMUP-FREE` omits common preparation, graph/index
  construction, tokenizer/model warmup, or cache priming; reject.
- `RESOURCEV10-REJ-GPU-UNATTRIBUTABLE` lacks a unique physical-device UUID,
  active-ns owner, or separable concurrency boundary; reject.
- `RESOURCEV10-REJ-MEMORY-UNATTRIBUTABLE` lacks a resettable per-arm host or
  device peak boundary; reject.
- `RESOURCEV10-REJ-SEGMENT-SUM` changes any input segment or total so the exact
  equality fails; reject.
- `RESOURCEV10-REJ-REGISTERED-ACTUAL-CONFLATION` substitutes registered,
  offered, emitted, or actual call/token counters for one another; reject.
- `RESOURCEV10-REJ-NETWORK-OR-COST` admits a provider/network edge, network
  byte/request, or nonzero external cost; reject.
- `RESOURCEV10-REJ-CAUSAL-REALLOCATION` performs any post-origin move described
  in section 4.4.5; reject.

Unattributable concurrency invalidates resource evidence; it is never imputed.

## 5. Exact delayed entitlement partition

### 5.1 Carrier-only test 13

Test 13 applies only to delayed conditions whose phase-local public memory
mode is `COMMON_READER`. For fixed `k`, the only D-entry twin-divergence
containers are:

```text
/carrier/atoms/25
/carrier/links/6
```

Only h-specific public FactKey/value leaves may differ. Handles `a19`/`l06`,
indices, counts, schema, order, padding, and all other leaves are equal. Every
differing leaf has the supplied public `O41_ACQUIRE_SUCCESS(k,h)` visibility
ancestor. The first actor-visible difference is inside a legal carrier return
exposing a19 or l06. Test 13 neither examines nor licenses RAW, RAG, or native
baseline surfaces.

### 5.2 Baseline-only test 29

For every `k` and `h`, define:

```text
OLD_PUBLIC_ROWS(k) = 32 primitive public ROOT rows at (00,0,0)..(31,0,0)
O41_ACQUIRE_SUCCESS(k,h) = supplied ordinary ACQUIRED outcome at (41,0,0)
O42_VALIDATE_P4(k) = independent p4 validation ROOT at (42,0,0)
O43_VALIDATE_NH(k,h) = independent nh validation ROOT at (43,0,0)

D_BASELINE_ROWS(k,h) = OLD_PUBLIC_ROWS(k) ||
  [O41_ACQUIRE_SUCCESS(k,h),O42_VALIDATE_P4(k),O43_VALIDATE_NH(k,h)]
```

The array has exactly 35 rows. A/B execution rows, `O40`, the SYNTH proposal,
live U rows/outputs, transcripts, scratch, sessions, and caches are absent.
Rows 0..31 and 33 are twin-equal. Only h-specific value leaves in rows 32 and
34 may differ, and both have visibility lineage to O41. O42/O43 remain
independent evidential ROOTs; visibility lineage does not turn SYNTH into
evidence.

Mode-specific D-entry pointers are exactly:

| Mode | Allowed differing containers | Stable fields |
|---|---|---|
| `RAW_STATIC` | `/memory_surface/static_context/rows/32`, `/memory_surface/static_context/rows/34` | order, row count, schema, padding, other rows |
| `RAG_DETERMINISTIC` | `/memory_surface/rag_corpus/documents/32/event`, `/memory_surface/rag_corpus/documents/34/event` | handles `d20`/`d22`, ranks, count, schema, order, scores, padding before entitled return |
| `NATIVE_GRAPH_STATIC` | `/memory_surface/static_context/atoms/25`, `/memory_surface/static_context/links/6` | handles `a19`/`l06`, indices, count, schema, order, padding |

RAW and native may first differ only inside the rendered identity projection
of their allowed containers. RAG's corpus is never rendered directly. Before
an entitled `d20` or `d22` return, query, tokens, fingerprint, repeat, score,
rank, handles, null slots, padding, and actor bytes are twin-equal. The first
RAG difference is only inside
`/last_public_result/slots/j/document/event`, `j in 0..3`, for an unchanged
`d20` or `d22` handle.

After an entitled origin becomes visible, response, parsed public command,
ordinary public transition/outcome, view, same-phase scratch, policy-selected
query, reached ranking/return, later reached reader return, and sealed
same-phase behavioral receipt may differ as causal descendants. Static
surfaces remain confined to their origin pointers. Source/authority data,
routing, scoring rules, oracle/checker state, abandoned branches, timing,
padding, errors, filenames, and cross-phase state never become descendants.
Reset destroys dynamic state.

Registered slots, allowances, READ/action opportunities, fixed static
storage/build charges, and pre-origin work remain twin-equal. Actual
post-origin query, postings, return-token, input-token, latency, and artifact
counters may differ only when caused by an entitled policy/query divergence;
they must be attributed to their own arm under tests 24/25. “Unchanged
resource charges” never means suppressing or equalizing such actual work.

### 5.3 Test 28 conjunction

Test 28 passes only with separate terminal receipts for both tests 13 and 29
and all other named dependencies in its record. Carrier pointers cannot
authorize baseline surfaces, baseline pointers cannot authorize common-reader
carrier returns, and an umbrella pass cannot replace either receipt.

### 5.4 Exact C10 boundary custody, provenance, guard, and projection

The exact integration constants are:

```text
C10 = "chg_20260910_pcfl_m0_mtext_bound_v10"
PLAN_PATH =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source_authoring_plan.json"
MANIFEST_PATH =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/normative_source_manifest.json"
BOUNDARY_PATH =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/v7_boundary_v4.json"
DENIAL_CORPUS_PATH =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/governance/v10_normative_denial_corpus.json"
```

The C10 plan has exactly 24 sorted rows: 23
`manifest_member:true` source rows, including exactly one `BOUNDARY_PATH` row
with `role:"V7_BOUNDARY"`, schema `V7BoundaryV1`, and maximum 65,536 bytes;
and exactly one `MANIFEST_PATH` row with
`role:"NORMATIVE_SOURCE_MANIFEST"` and `manifest_member:false`. It also has
exactly one closed `governance_inputs` entry for `DENIAL_CORPUS_PATH`, role
`V10_NORMATIVE_DENIAL_CORPUS`, media type `application/json`, a `hex64` digest,
and access `GOVERNANCE_ONLY`. That entry is neither a plan row, source member,
manifest output, preparation/runtime input, nor scientific artifact.

The exact order and access classes are:

1. separately human-ratified corpus bytes and exact C10
   `SourceAuthoringGrantV1` bind the complete plan and corpus digest;
2. `AUTHORITY_S_SOURCE_WRITER_HASHER`, governance-private under only that
   grant, writes/hashes the 23 paths and the nonauthoritative external
   manifest but does not import, execute, syntax-check, prepare, materialize,
   run a checker, or emit a preparation/runtime projection;
3. `INDEPENDENT_EXACT_BYTE_REVIEWER`, read-only, governance-private, and
   distinct from writer and guard, rehashes the exact plan, corpus, 23
   members, external provenance rows, and manifest and emits only
   `GovernanceExactByteReviewGrantV1[C10]` evidence;
4. a human separately ratifies the exact candidate bytes and manifest and
   later grants one exact `PreparationExecutionGrantV1` attempt; and
5. `V7_BOUNDARY_GUARD` is substage zero of that attempt and the sole
   candidate/preparation/runtime semantic consumer of `BOUNDARY_PATH`. It
   compares registered metadata only and never resolves, opens, imports,
   hashes, or executes a denied target. Passage produces only the projection
   below for later substages of the same grant. Failure consumes the attempt,
   produces no projection/prepared output, and permits neither retry nor
   reserve substitution.

Writer and reviewer custody are not semantic-consumer exceptions. They cannot
change any candidate, preparation, runtime, public, model, cache, receipt, or
claim byte. No step implies authority for the next, guard passage cannot
issue its authorizing grant, and source-authoring authority cannot authorize
the guard or any source parsing/test execution.

Each member's already-closed digest is recorded in exactly one external
`SourceProvenanceRowV1[C10]` in the nonmember manifest. No member embeds a
provenance row holding its own digest. Every row cites at least one exact,
human-bound `PCFL_V10_NORMATIVE` source and states
`v7_runtime_derivation:false` and `v7_oracle_derivation:false`. The boundary
row alone cites exactly the plan-bound `DENIAL_CORPUS_PATH` and digest, with no
second derivation entry. The corpus contains only the seven sorted negative
denial classes and no positive semantic value, answer, score, expected output,
carrier content, or model-visible field.

On pass the guard emits exactly this closed four-field object and no other
output:

```text
V7GuardProjectionV1 := {
  schema_version: 1,
  artifact_type: "pcfl_v7_guard_projection",
  passed: true,
  pcfl_read_allowlist: [
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/acceptance_tests.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/cas_freeze_contract_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/check_axiomatic_v4.py",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/check_constructive_v4.py",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/claim_disposition_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/delayed_twin_entitlement_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/endpoint_gate_registry_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/failure_precedence_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/handoff_consumer_graph_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/handoff_projection_allowlist_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/handoff_public_v4.schema.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/integrated_contract.md",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/materialize_v4.py",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/mtext_handoff_v4.schema.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/mutation_fixtures.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/object_schemas_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/prepare_v4.py",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/provenance_contract_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/resource_roster_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/runtime_manifest_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/semantic_table_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/transition_table_v4.json"
  ]
}
```

The allowlist is the literal bytewise UTF-8 sort of the 22 non-boundary
members. `BOUNDARY_PATH`, `MANIFEST_PATH`, `DENIAL_CORPUS_PATH`, `PLAN_PATH`,
directories, globs, aliases, and symlinks are excluded. No boundary path or
digest, denied value, V7/V5 identifier, provenance row, violation detail,
corpus/manifest hash, timing, error, expected value, or fifth field may cross
the projection. At equal pass/pathset, changing private boundary or corpus
metadata changes no downstream byte or behavior; a pass-to-fail mutation has
only one allowed downstream effect, absence of the projection.

Tests 01 and 34 are conjunctive. Test 01 owns all seven denial predicates for
every non-boundary member, provenance row, capability, import/runtime surface,
and actor/model projection. Test 34 alone owns this one boundary exception,
the two governance custody readers, external boundary provenance, sole guard
consumer, literal pathset, and fail-closed nonexposure. Neither receipt can
replace the other.

## 6. Exact rendered branch, repeat, and protocol boundary

### 6.1 Abandoned branches

At every branch/join, paired fixtures hold the active branch, public events,
entitled memory projection, public state, repeat state, and terminal status
equal. They independently mutate abandoned scratch, plans, beliefs, reads,
commands, tool returns, failures, timing buckets, sibling handles, padding,
temporary objects, cache/session IDs, and private scorer/oracle fields.
Acceptance requires byte identity from join to terminal in rendered system,
user and chat-template bytes; token and tool-boundary IDs; tool advertisements
and envelopes; parser state and accepted-command set; and public fingerprint/
cache inputs. No abandoned object may parent the active branch, join, later
render, trace, or score.

### 6.2 Saturated visible repeat and literal RAG null

The closed field is `repeat_count:1|2|3`. For any legal memory request:

```text
repeat_count = min(3, 1 + n_prior)
```

`n_prior` counts prior legal requests in the same phase whose request identity
is byte-identical. For `ANCHOR_CURSOR`, `BLOCKED_ANCHOR_CURSOR`, and
`PASSIVE_NULL_ANCHOR_CURSOR`, identity is the exact ordered pair
`(anchor_utf8,cursor)`. For zero-argument `RAG_READ`, identity is the exact
registered public query UTF-8 bytes. A blocked post-action RAG_READ uses the
registered zero-length query, so those requests share an identity. Malformed
requests reject before increment. Counters reset at phase, condition, and root
boundaries. Visible and fingerprint values over eight identical requests are
exactly `[1,2,3,3,3,3,3,3]`; no unsaturated ordinal enters padding,
tokenization, resource charge, or another actor-visible byte.

Every RAG return has four `RagSlotPublicV4` entries with ranks 0..3. A null
slot is exactly `document:null`, `score_e12:0`, and its fixed inert padding.
Real slots precede nulls. `NOT_FOUND` and `BLOCKED` have four null slots;
`FOUND` has one to four real slots then nulls. Omitted document, `{}`, empty
string, sentinel handle, null rank, nonzero null score, wrong order/count, or
alternate padding rejects.

### 6.3 Prompt/protocol/schema cross-product

The section-2 table is the only legal mode/protocol relation. Its instruction
map is:

```text
ANCHOR_CURSOR              -> advertise READ(anchor,cursor)
BLOCKED_ANCHOR_CURSOR      -> advertise READ(anchor,cursor), documented BLOCKED
PASSIVE_NULL_ANCHOR_CURSOR -> advertise READ(anchor,cursor), documented NOT_FOUND
RAG_AUTO                   -> advertise zero-argument RAG_READ
NONE                       -> advertise no memory command
```

For P/D, enumerate each legal relation, finish, abstain, and memory form for
the current protocol/stage. For U, enumerate experiment `e0..e3`, abstain,
then commit `c0`/`c1`/abstain only at the commit stage; no relation or memory
command exists in U. The tagged union is exactly `PCFL_COMMAND_V4`.
TARGET_ONLY uses `BLOCKED_READER/BLOCKED_ANCHOR_CURSOR` open-loop; its listed
READs are executed only after the one-shot response and cannot feed it.
AUTH_NO_FEEDBACK uses `COMMON_READER/ANCHOR_CURSOR` open-loop and exposes no
future handle. A legal post-close memory command produces its exact BLOCKED
envelope and performs no lookup; `PROTOCOLV10-REJ-POST-CLOSE-LOOKUP` rejects
lookup or carrier/index access, not the legal BLOCKED command itself.

For every cross-product fixture, prompt advertisement, serialized schema, and
parser verdict/semantics must agree. Evidence binds source fragment, rendered
system/user/template bytes, token IDs, tool envelope, schema verdict, parser
verdict, and normalized command/result. No model call occurs in this test.

## 7. Exact trace and endpoint applicability

### 7.1 Terminal and normalization law

A raw trace records each charged world-relation attempt as
`(pre_state,semantic_relation,public_outcome,post_state)` and then exactly one
terminal:

```text
FINISH_OK(goal)
WRONG_FINISH(state)
ABSTAIN(state)
BUDGET_EXHAUSTED
OUTPUT_INVALID(code)
```

Wrong finish, abstain, budget exhaustion, and registered output-invalid are
ordinary behavioral zeros. `NO_EFFECT` consumes a relation attempt, closes
the reader if first, and is nonterminal. A fourth attempt without a correct
finish opportunity yields `BUDGET_EXHAUSTED`. Calls after a terminal are
`NOT_REACHED` receipt padding, not actions or endpoints. Illegal/private
commands, foreign/missing receipts, controller exceptions, and oracle leaks
are instrument faults, not terminals.

Discard `NO_EFFECT` from the effective skeleton but retain its budget and
terminal effect. Map:

```text
p0 or p2 -> LEG_1
p1 or p3 -> LEG_2
p4       -> BRIDGE
p5       -> TERMINAL_RELATION_R05(destination_role)
p6       -> TERMINAL_RELATION_R06(destination_role)
nh       -> TERMINAL_RELATION_R07_OR_R08(destination_role)
other    -> OTHER_EFFECTIVE(pre_role,relation,post_role)
```

Upper/lower paths for goal `g` are equivalent exactly when they normalize to
`(LEG_1,LEG_2,BRIDGE,TERMINAL_RELATION_TO(g),FINISH_OK(g))`. AUTH terminals
at public C are A=`R05`, B=`R06`; TWIN terminals are A=`R06`, B=`R05`.
Bridge change and the first relation from C under TWIN are computed separately
for A and B at each `(k,h)`. Then:

```text
bridge_pair = bridge_behavior_change_A & bridge_behavior_change_B
twin_pair = twin_terminal_switch_A & twin_terminal_switch_B
connected_trace_dependence = connected_two_goal_use(AUTH)
  & trace_support_integrity_A(AUTH)
  & trace_support_integrity_B(AUTH)
  & bridge_pair & twin_pair
```

The confirmation numerator is
`sum_k min_h connected_trace_dependence(k,h) >= 12` over the 16 confirmation
`k` blocks. No goal or twin compensates for its mate.

### 7.2 Complete condition/phase/endpoint matrix

`PB` is path behavior; `PM` path connected mechanism; `UI` uncertainty,
information, and acquisition; `DB` delayed behavior; `DM` delayed connected
carrier; `2B` two-goal behavior; `2M` connected two-goal use; `F/R` the four
full-sequence, retention, acquisition-to-delayed-use, and online-learning
endpoints.

| Condition | A.PB | A.PM | B.PB | B.PM | U.UI | D.DB | D.DM | 2B | 2M | F/R |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `AUTH_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA |
| `AUTH_SCRATCH_OFF` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA |
| `ATOMS_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `DERANGED_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `REACHOUT_OFF_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA |
| `NO_MEMORY_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `PASSIVE_SIGNATURE_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `RAW_CONTEXT_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `RAG_RAW_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `NATIVE_GRAPH_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `BRIDGE_CUT_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA | NA | NA | 0\|1 | 0\|1 | NA |
| `TWIN_REDIRECT_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA | NA | NA | 0\|1 | 0\|1 | NA |
| `UNCERTAINTY_SHAM_RECURRENT` | NA | NA | NA | NA | 0\|1 | NA | NA | NA | NA | NA |
| `OLD_CUT_RECURRENT` | NA | NA | NA | NA | NA | 0\|1 | 0\|1 | NA | NA | NA |
| `NEW_CUT_RECURRENT` | NA | NA | NA | NA | NA | 0\|1 | 0\|1 | NA | NA | NA |
| `NO_PERSIST_NEW_RECURRENT` | NA | NA | NA | NA | NA | 0\|1 | 0\|1 | NA | NA | NA |
| `TARGET_ONLY_ANSWER_PRIOR_TAPE` | 0\|1 | NA | 0\|1 | NA | 0\|1 | 0\|1 | NA | 0\|1 | NA | NA |
| `AUTH_NO_FEEDBACK_TAPE` | 0\|1 | NA | 0\|1 | NA | 0\|1 | 0\|1 | NA | 0\|1 | NA | NA |

Each record binds root, `k`, `h`, condition, phase, endpoint, applicability,
value, phase receipt, trace, and scorer hashes. A `0|1` cell requires an
integer Boolean from its own receipt. An `NA` cell requires literal `NA` and
null-sentinel hashes. Behavioral failure stays applicable zero.
`NOT_REACHED` is call padding only. No AUTH fallback, foreign cell, cached
summary, imputation, or pooling is legal. `2B`/`2M` are Boolean only when both
same-condition operands are Boolean. `F/R` is always `NA`. The only twin
reduction is `min(e(k,0,c),e(k,1,c))`.

## 8. Exact noncompensatory gates and claim dispositions

Counts are integer counts over 16 CONFIRMATION `k` blocks after twin minimum.
Every required input must be Boolean and terminally receipted.

```text
G0 INSTRUMENT_VALID
  Every required source, authority, V7 guard, handoff, carrier-13,
  baseline-29, render-09/31/32/33, local-edge-30, producer/query/scorer,
  reset/session, CAS, provenance, receipt, applicability, and resource
  invariant passes; the 32-ID registry and confirmation cells are complete.

G1 AUTH_HEADROOM
  count(two_goal_task_success, AUTH_RECURRENT) >= 12
  count(delayed_task_success, AUTH_RECURRENT) >= 12

G2 CONNECTED_BENEFIT
  for c in {ATOMS_RECURRENT,DERANGED_RECURRENT,
            BRIDGE_CUT_RECURRENT,REACHOUT_OFF_RECURRENT}:
    count(two_goal_task_success,AUTH_RECURRENT)
      - count(two_goal_task_success,c) >= 4
  count(connected_two_goal_use,AUTH_RECURRENT) >= 12
  count(connected_trace_dependence) >= 12

G3 PUBLIC_CALIBRATION
  for e in {separating_choice,realized_information,
            belief_revision,acquisition_success}:
    count(e,AUTH_RECURRENT) >= 12
  for e in {realized_information,belief_revision,acquisition_success}:
    count(e,UNCERTAINTY_SHAM_RECURRENT) <= 4
  count(acquisition_success,AUTH_RECURRENT)
    - count(acquisition_success,UNCERTAINTY_SHAM_RECURRENT) >= 8

G4 DELAYED_CARRIER
  count(delayed_connected_integration,AUTH_RECURRENT) >= 12
  for c in {OLD_CUT_RECURRENT,NEW_CUT_RECURRENT,
            NO_PERSIST_NEW_RECURRENT}:
    count(delayed_task_success,c) <= 4
    count(delayed_task_success,AUTH_RECURRENT)
      - count(delayed_task_success,c) >= 8

G5 SHORTCUT_PATH
  Every test-14 count for task_success_A, task_success_B, and
  two_goal_task_success is <= 5.

G6 SHORTCUT_DELAYED
  Every test-14 delayed_task_success count is <= 5.

G7 ZERO_NET_ATOMS
  for e in {task_success_A,task_success_B,two_goal_task_success,
            plan_valid_A,plan_valid_B,first_action_correct_A,
            first_action_correct_B,plan_execution_consistent_A,
            plan_execution_consistent_B,delayed_task_success,
            delayed_plan_valid,delayed_first_action_correct,
            delayed_plan_execution_consistent}:
    count(e,AUTH_RECURRENT) - count(e,ATOMS_RECURRENT) >= 0

G8 BEST_TEXT (optional)
  for e in {two_goal_task_success,delayed_task_success}:
    sum_k [b_e(k,AUTH_RECURRENT)
           - max(b_e(k,RAW_CONTEXT_RECURRENT),
                 b_e(k,RAG_RAW_RECURRENT))] >= 1
  and AUTH has zero net loss to that root-wise maximum on every other
  endpoint in G7. NATIVE_GRAPH_RECURRENT is a reported ceiling, not in max.

G9 CARRIED_SCRATCH (optional)
  count(acquisition_success,AUTH_RECURRENT)
    - count(acquisition_success,AUTH_SCRATCH_OFF) >= 4
  count(delayed_task_success,AUTH_RECURRENT)
    - count(delayed_task_success,AUTH_SCRATCH_OFF) >= 4
  and AUTH has zero net loss to AUTH_SCRATCH_OFF on every other mutually
  applicable PB, UI, DB, and 2B endpoint.

G10 CLOSED_LOOP_FEEDBACK (optional)
  count(acquisition_success,AUTH_SCRATCH_OFF)
    - count(acquisition_success,AUTH_NO_FEEDBACK_TAPE) >= 4
  count(delayed_task_success,AUTH_SCRATCH_OFF)
    - count(delayed_task_success,AUTH_NO_FEEDBACK_TAPE) >= 4
  and AUTH_SCRATCH_OFF has zero net loss to AUTH_NO_FEEDBACK_TAPE on every
  other mutually applicable PB, UI, DB, and 2B endpoint.
```

| Claim clause | Required gate | Complete valid negative | Invalid/incomplete evidence | Exact exclusion |
|---|---|---|---|---|
| Supplied connected memory supported two goal-dependent route constructions. | `G0 & G1(two-goal) & G2 & G5 & G7`; report AUTH constructive-use and bridge/twin numerators. | Withdraw connected-memory specificity and the combined maximum; retain exact task/intervention counts as bounded negative or mixed evidence. | No clause. | No DREAM authorship, spontaneous connection creation, or general composition. |
| Calibrated public evidence supported separating choice and belief revision. | `G0 & G3`, public U endpoints only. | Withdraw calibration and the combined maximum only; it neither rescues nor defeats path evidence. | No clause. | No DREAM, memory causality, learning, or U-to-D retention. |
| A supplied old-plus-new carrier supported delayed task completion and connected integration after sterile reset. | `G0 & G1(delayed) & G4 & G6 & applicable G7`, including tests 13 and 29 only where each applies. | Withdraw delayed-carrier specificity and the combined maximum. | No clause. | No retention, acquisition-to-use, self-write, or online learning, even on pass. |
| AUTH practically outperformed the strongest honest unstructured text baseline. | All mandatory gates for the named endpoint plus `G8` and tests 23–25. | Withdraw practical-superiority and efficiency only; RAW/RAG success is an honest alternative. | No practical clause. | Cannot rescue or defeat core mechanism clauses by itself. |
| Carried structured scratch improved behavior. | `G0 & G9`. | Withdraw carried-scratch benefit only. | No scratch clause. | No recurrence necessity, persistence, SLEEP, retention, or learning. |
| Closed-loop within-phase feedback improved behavior. | `G0 & G10`. | Withdraw feedback benefit only. | No feedback clause. | Not pure recurrence and no U-to-D retention. |

An integrity breach is `INVALID`; missing/duplicate/nonterminal evidence is
`INCOMPLETE`; neither is zero. A complete valid gate miss remains negative
evidence and is not dropped, retried, reserve-replaced, or compensated. A
shortcut breach is a specificity failure. `NA`, zero, and `NOT_REACHED` are
disjoint.

Unconditionally withdrawn are DREAM connection authorship/re-expression,
SLEEP validation, LoRA storage/transport, model-authored persistent write,
retention, acquisition-to-delayed use, online learning, continued-life
improvement, accumulation, compression, parenting, recall/composition/
planning decomposition, topology/model/population generalization,
longitudinal plateau, baseline saturation, and complete-organism/flywheel
behavior.

Only if all three mandatory rows pass may independent claim review consider:

> In one fixed finite topology under one exact frozen text policy, supplied
> grounded atom-plus-connection memory supported two goal-dependent route
> constructions under registered connection and binding interventions;
> separately, calibrated public evidence supported separating choice and
> belief revision; and a model-independent supplied old-plus-new carrier
> supported delayed task completion and connected integration after sterile
> reset.

## 9. Registry validation and evidence receipts

The source registry validator must require exactly 32 IDs, exact nine-field
key closure, exact literal arrays, unique IDs, unique terminal receipts, and
no active/deferred collision. Each receipt binds source-manifest hash,
test-spec hash, checker identities, the complete positive and negative fixture
arrays in order, per-fixture verdict/reason, and evidence hashes. Every
positive must accept and every mutation must reject for its registered reason.
Missing, extra, duplicate, renamed, aliased, skipped, umbrella-only, or
nonterminal tests make the proposal/assay `INCOMPLETE`.

Required named evidence artifacts include all 32 `evidence_artifact` values
above. In particular test 29 and test 34 each receive their own terminal
receipt; neither can be represented by test 28, 19, or 01.

## 10. Exact companion integration binding and remaining caveat

The prior C10 authority-path and boundary-lineage issue is resolved exactly,
not left to an implementer. Section 5.4 fixes the single C10 identity, four
paths, 24-row plan, 23/1 member/nonmember split, one governance-only denial
corpus, external noncircular provenance, custody principals, independent
exact-byte review, later human preparation grant, guard-as-substage-zero, and
literal four-field/22-path projection. Section 4.4 fixes the C10-only
`ChargedResourceV10`; tests 01, 23--27, and 34 copy the companion provenance/
resource registry records exactly after JSON-to-YAML value mapping. Test 29
copies the authority/delayed companion record exactly. No V9 plan/path hash,
`ChargedResourceV5`, receipt alias, alternate stage, inferred directory, or
umbrella test may substitute.

The one remaining integration caveat is documentary and non-discretionary: a
future C10 deliberation packet must enumerate and hash-bind this file together
with the exact current bytes of
`20260910_pcfl_v10_provenance_resource_guard_exact_repair_v2.md` at SHA-256
`f7275453054e76080cd72b0f57bc75d805756114cc62034efd06f940a35c2d79` and
`20260910_pcfl_v10_authority_delayed_baseline_exact_repair_v2.md` at SHA-256
`27668f5816958342b84a322c317281dc10131732153eeee387a228f67eea86ae`.
Any later byte change to either companion reopens cross-review; it is not
silently incorporated. This binding creates no source-authoring, import,
preparation, test, implementation, execution, model, GPU, claim, or release
authority.

## 11. Source basis and stop boundary

This v2 is based on the V9 consensus
`9e2066e1782a627e3fab15e179f1e15c33dc829b51076dbdd52556c5053176cf`,
V9 critique
`e92e461fe8e37ed22353ffdefe0929afb98e1d59bb62643d138093a95ffbd4a5`,
V9 candidate
`8a47d30909e0e171fe6dc1d6f92640fb7ed6d2bdab6642cabe57f91a5d549f59`,
the V5 endpoint repair
`bfc4ae363a47f9825193e0783ef6d5f9f84b4741a6c73a3effad1d9140ea9ec4`,
the V7 baseline exact closure
`6ca612e41e3462ca6997cabcd089439a8d24be06ca7d37b5e29183ec362dd272`,
the V8 repeat/null closure
`5c5321a7d208830a4f1c2fd5b04669ca56207e6403d57a68483954fe2057d597`,
and the two V10 companion advisories as cross-critiqued. A future packet must
hash-bind their current exact bytes; this prose does not silently incorporate
later edits.

This file is advisory text only. It authorizes no source authoring, source
import or parsing, checker/test run, preparation, implementation,
materialization, fixture/root/data generation, benchmark/model/tokenizer
execution, training, LoRA/adapter/checkpoint work, parenting, GPU use,
resource acquisition, scientific execution, claim, release, or submission.
