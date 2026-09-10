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
FUTURE-PCFL-MULTITOPOLOGY-GENERALIZATION-21
FUTURE-PCFL-ONLINE-ACTION-OUTCOME-WRITE-ACTION-22
FUTURE-PCFL-TEXT-LORA-MATCHED-TRANSPORT-35
FUTURE-PCFL-RECALL-COMPOSITION-PLANNING-DECOMPOSITION-36
FUTURE-PCFL-LONGITUDINAL-ACTIVE-TEXT-PLATEAU-37
```

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

## 10. Required integration caveat

The V10 integration must resolve one authority-path issue outside this
advisory's five original scientific-boundary items. The exact boundary member,
guard read closure, source plan, grant, and provenance rows must all bind one
and the same C10 plan identity. A V9 path/plan hash cannot silently substitute
for that C10 identity. The sole guard runs only as the first validation
substage named by a later exact human `PreparationExecutionGrantV1`; its
success projection can feed only later substages of that same grant, and its
failure produces no projection or materialization. It does not gate issuance
of the grant that authorizes it. Source-authoring authority never permits
guard parsing or test execution.

The V7 boundary member also needs a closed boundary-only governance provenance
rule for its denied values, or an exact C10 normative denial source. Requiring
every member to cite only ordinary C10 semantic sources while also confining
the actual denied values to the boundary/governance records is unsatisfiable.
The exception may establish negative governance lineage only; it must not
become executable semantics, a checker oracle, or an actor/model channel.
This integration caveat adds no source-authoring or execution authority.

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
```
