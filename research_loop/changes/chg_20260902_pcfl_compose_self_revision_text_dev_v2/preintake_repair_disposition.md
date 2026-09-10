# v2 pre-intake repair disposition for P1–P14

**Status:** proposal-byte reconciliation ledger only. The P1–P14 contract and
its scientifically material fixture semantics are reconciled in proposal
bytes, but static validation, fresh exact-byte review, and exact human
ratification remain required. This ledger does not itself initialize or
authorize architecture intake, implementation, a run, or a claim. Separate
non-authorizing intake/deliberation through `human_required` is permitted; this
ledger does not approve a `ratify` transition,
`human_approved` state, implementation, CPU/model/GPU/network work, or a claim.

| finding | repaired static contract | mandatory negative/fixture |
|---|---|---|
| P1 typed protocol | `semantic_dsl.schema.json` is a closed 21-branch root union with phase/op-specific READ/node/PREDICT/COMMIT/USE/LOCK/ABSTAIN; all five one-shot output branches reach only dedicated closed one-shot candidate/record/provenance/citation definitions and cannot reach a node/object capability definition; `resolver_reducer.md` binds ownership, ancestry, cardinality, prediction sets, phase legality, capability rejection, and total failure | F01 positive min/max for every branch; arbitrary-root/private-field/wrong-phase/stale/unread/reordered/candidate-REVISE/ABSTAIN-content negatives; exact D2 RETAIN trace; F03.01 output capability-reachability and injection negatives |
| P2 receipts/delivery | `event_catalog.schema.json` is a closed 17-branch root union separating model-visible event/candidate/memory/NOT_FOUND/target values from audit-only digests; candidate reads mint D2-local capabilities only in recurrent Dream; all three one-shot input roots use dedicated closed capability-free state, pool, AST-record, provenance, and citation definitions; one-shot batch is mechanically charged | F02 every branch and wrong-kind/unread/open-payload/cap/identity/audit-visibility/target-time injection/batch-order negatives; F02.02 input capability-reachability, property-name, value, and recurrent-record substitution negatives |
| P3 one-shot/prompt chronology | six closed input-envelope modes and all eight single-marker prompts bind exact budgets/state/read results; the three one-shot prompts require the dedicated capability-free input/output schema branches; one-shot D1 uses response-local C slots; D2 RETAIN selects immutable D1 slot with B predictions/no candidate, while REPLACE carries sole D2C01; one-shot plan is four USE + LOCK | F03 marker inventory, response chronology, dedicated one-shot branch/type enforcement, RETAIN-with-candidate, missing/wrong raw-A provenance, post-response capability, D2 multiplicity, short/fifth/missing-LOCK, and factor/null diff negatives |
| P4 common randomness | `rng_contract.json` separates audit row from treatment-invariant seed key; excludes h/q, descriptive lane, condition, cut, and memory variant while retaining topology `sampling_lane`; defines COMMON_SEED/ANALYSIS_PAIR_ONLY, exact JCS-HMAC bytes, uint32 big-endian mapping, namespaces, sampler binding, and golden digest | F04 treatment mutation, retained-field reject, paired rows, topology mismatch, endian/domain vectors |
| P5 actor/identity firewall | `private_field_registry.json` exhaustively inventories IPC data; `visibility_contract.md` splits TARGET_READER/TARGET_THINK/PUBLIC_ACTOR, removes all memory/identity/treatment/score access from actor, fixes target-time handle values/count/order, and assigns digest checks to a noncognitive process | F05 exhaustive taint, actor transducer, identity-channel diff, digest-owner cases |
| P6 opaque identity/capacity | `semantic_contract.md` selects valid-Unicode NOTE text with closed-object JCS UTF-8 identity, audit-only raw response, exact domain bytes, 256/512/2,510/3,072 byte hierarchy, pinned Unicode/JCS boundary, and schema/reducer caps | F06 Unicode/JCS/domain vectors, arbitrary/duplicate/invalid input, every container cap±1, K=2/K=1 live state, and maximum tokenizer/context cases |
| P7 resources/runtime | `runtime_envelope.json` freezes proposal-chosen stack, source resolution, sampler, seed mapping, flags, TP/bf16/no-quantization, timeout, context, and >=96-GiB hardware eligibility without claiming compatibility/availability; `resource_manifest.md` defines raw/accepted accounting, prospective Dream caps, competing stops, and a complete 1,540-minute Stage-0 ledger under a 1,560-minute cap | F07 arithmetic, every cap±1, malformed charge, maximum context, executable mutation, whole-roster forecast/NOT_RUN |
| P8 Stage-1 gate/revision | `gate_receipt.schema.json` and `gate_receipt_contract.md` bind exact receipt IDs/kinds and a typed total evaluation; G04 additionally binds exactly one charged raw-A read and one charged pre-A candidate-parent read, their exact receipt/handle/capability joins into a decisive REPLACE PREDICT, an identical-provenance terminal REPLACE COMMIT selecting only that PREDICT capability, selected bytes unequal to every shared pre-A pool member, and paired clone/seed/pool equality with h-selected inequality; `analysis_contract.md` and `experiment_spec.md` use only that nonsemantic predicate | F08 all 2^11 vectors plus one negative per G04 schema field and cross-invariant: read count/charge/order, raw receipt/handle provenance, candidate receipt/parent capability/pool membership, PREDICT/COMMIT decision, terminal capability/provenance, pre/post equality, paired pool/clone/seed inequality, h-selected equality, and existing gate/corpus/oracle/roster cases |
| P9 pre-target sham | `experiment_spec.md` freezes domain, inputs, 32-word alphabet, HMAC counter stream, eight buckets, match fields, 65,536-attempt limit, first-match rule, total exhaustion receipt, and retained-zero consequence without opaque falsity | F09 determinism, target/result mutation, forbidden input, first-match, match/nonmatch/exhaustion receipts and lint |
| P10 manifest/denominator/replay | operative `assignment_manifest.schema.json`, `assignment_generator_contract.md`, and `experiment_call_ledger.schema.json` define total source-commitment mapping, exact IDs/topologies/factors/couplings/statuses, exact G01–G11 receipt bindings, replay eligibility/allocation, denominator weights, 15,872-token Think-D4 remainder, orthogonal process/science status, and validation/cardinality | F10 two independent 3,414 expansions; arbitrary gate-pointer, wrong-kind receipt, duplicate/missing/extra/stage/cut/lane/status/third-replay/adaptive/legal-wrong-drop/null-misuse negatives |
| P11 q reconciliation | `analysis_contract.md` and `experiment_spec.md` separately define ANY_INDEPENDENT_SUCCESS and compound SPECIFICITY_CONCERN, same-q controls, exact finite vector/policy enumeration, consequences, and always-HUMAN terminal | F11 singleton, 3-of-4, one-q contrast, both-q contrast, and full vector-product cases |
| P12 report/claim access | `visibility_contract.md` seals raw opaque bytes from reducer/reporter until report hash freeze; later access is logged exploratory and non-mutating; `analysis_contract.md` freezes positive descriptor and exact forbidden claims/next step | F12 field projection, pre-freeze access failure, forbidden-claim lint, positive descriptor |
| P13 extractor boundary | `event_extractor_contract.md` freezes closed event input, pure position-map algorithm, exclusions, interactive recurrent and charged sealed-batch one-shot delivery, Think nonexposure, and supplied-local-permutation claim | F13 full S6/equivariance/locality, malformed/extra fields, unread extraction, batch ledger parity, q-null, Think injection |
| P14 roster/scope | assignment generator and ledgers prove 910 + 2,504 = 3,414, only two diagnostic replays = 3,416, four AST one-shot rows, h=0-only cuts, no optional/adaptive/baseline rows, and Stage-2-only-through-G01–G11 | F14 independent expansion and extra/missing/h=1/opaque-one-shot/adaptive/stage-order/replacement negatives |

## Exact retained scientific boundary

The fresh one-shot capability-closure blocker is closed in proposal bytes.
`DREAM1_ONE_SHOT`, `DREAM2_ONE_SHOT`, and `THINK_ONE_SHOT` inputs use only their
dedicated capability-free state/pool/record graph, and all five atomic one-shot
output branches use only dedicated capability-free candidate, record,
provenance, and citation types. F02.02 and F03.01 bind minimum/maximum positives,
schema reachability, every capability-bearing property injection, recurrent
capability-value substitution, and recurrent-record substitution. The exact
one-shot prompts and reducer reject every capability-named field or capability
value; this adds no scientific cell or claim.

The repair adds zero scientific cells. The roster remains exactly 128 Dream +
782 recurrent Think = 910 Stage 1; 356 Dream + 2,144 recurrent Think + four
structured-only one-shot Think = 2,504 conditional Stage 2; and 484 Dream +
2,926 recurrent Think + four structured-only one-shot Think = 3,414 scientific
call opportunities. Only two non-replacing infrastructure-diagnosis slots can
raise the process opportunity count to 3,416.

The permitted result is an exact-root, selected-h, conditional pre-context DEV
record using supplied local permutations and a mechanical exactly-one raw-A
READ plus exactly-one pre-A candidate-parent READ before a decisive REPLACE
PREDICT, exact receipt/handle/capability provenance, matching terminal REPLACE,
and branch-distinct selected-object update
receipt. It is not semantic revision, h-mediated
action, factor discovery/identification, raw perception, recurrence or
efficiency evidence, replication/generalization, persistence/lifetime/LoRA,
external-memory superiority, A-MEM, or paper efficacy. The only named future
direction is a new separately designed/powered root confirmation and separate
genuine post-context/lifetime study, each requiring a new material change,
deliberation, exact ratification, review, and pre-GPU gate.

## Gate-tranche audit disposition

| audit finding | exact repair bytes | acceptance/static evidence |
|---|---|---|
| science B3; contract material gate; adversarial `V2_PRE_B10`/`M06`; matrix P8; fresh G04 parent-chain blocker | `gate_receipt.schema.json`, `gate_receipt_contract.md`, `analysis_contract.md`, experiment §§1/2/4 | T02/T10/T15/T18/T17; F08 mask 0..2047 and one-negative-per-field/invariant coverage for exact raw/candidate reads, receipt/handle/capability joins, ordering, decisions, pool membership, selected-byte differences, and pair coupling |
| adversarial `V2_PRE_B14`/`M02`; matrix P10/P14 | `assignment_manifest.schema.json`, `experiment_call_ledger.schema.json`, experiment §4 | T13/T15/T16/T18/T19; F10 exact counts, ID bijection, status/null, replay, and no-extra-cell negatives |
| adversarial `V2_PRE_M03`; matrix P11 | `analysis_contract.md` independent-q section and experiment §5 | T04/T15/T19/T17; F11 singleton/3-of-4/one-q/both-q/full-vector cases |
| parent actor/ordinal catches | experiment §§2–3 and both ledger schemas | T10/T14/T15; actor receives USE only, LOCK stays local, and stored ordinal/report number mapping is 0-based/+1 |

The scientifically material dimensions, mutations, expected decisions, and
failure routes of F01--F14 are exact proposal semantics. Under
`research_loop/advisory/20260902_pcfl_v2_fixture_authority_adjudication.md`,
incidental implementation witnesses (for example a harmless minimum Unicode
scalar or temporary object address) are deliberately not implemented before
ratification. If these exact proposal bytes are ratified, scoped implementation
must materialize and hash-freeze a complete literal fixture catalog and fresh
executable snapshot before Stage 0, and T17 must independently review every
realized receipt before separate pre-GPU approval. Materialization may not
choose or change a scientific value; any such need returns to a new intake.

## Proposal-byte reconciliation status

The P1–P14 proposal-byte reconciliation is complete. This ledger is not
evidence that any fixture has run, does not itself initialize intake, and
grants no implementation, CPU/model/GPU/network, or claim authority. Separate
non-authorizing proposal intake and deliberation may proceed only through
`human_required`. Static validation must be repeated against the final exact
bytes during fresh review; exact human ratification remains mandatory before
`ratify`, `human_approved`, or any scoped implementation authority, and T17
plus separate pre-GPU approval remain mandatory before any scientific call.
