"""Render the v6 successor proposal from the adjudicated v5 record.

Proposal construction only.  This module does not execute a model or
tokenizer, generate treatment data, write an adapter, use a GPU, make a
scientific claim, or authorize any later action.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
V5_DIR = ROOT / "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v5"
OUT = Path(__file__).with_name("change.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def by_id(items: list[dict], key: str, value: str) -> dict:
    return next(item for item in items if item[key] == value)


def replace_node(doc: dict, node_id: str, after: str, rationale: str) -> None:
    node = by_id(doc["graph_delta"]["nodes"], "node_id", node_id)
    node["after"] = after
    node["rationale"] = rationale


def replace_edge(doc: dict, edge_id: str, after: str, rationale: str) -> None:
    edge = by_id(doc["graph_delta"]["edges"], "edge_id", edge_id)
    edge["after"] = after
    edge["rationale"] = rationale


def replace_loop(
    doc: dict,
    loop_id: str,
    *,
    after: str,
    trigger: str,
    reads: list[str],
    writes: list[str],
    stop_condition: str,
    rationale: str,
) -> None:
    loop = by_id(doc["loop_delta"]["loops"], "loop_id", loop_id)
    loop.update(
        after=after,
        trigger=trigger,
        reads=reads,
        writes=writes,
        stop_condition=stop_condition,
        rationale=rationale,
    )


def build_visibility(registry: dict) -> dict:
    """Generate the complete principal x capability product from the registry."""
    stages = list(registry["registered_principals"])
    information_items = [item["capability_id"] for item in registry["capabilities"]]
    cells: list[dict] = []
    for capability in registry["capabilities"]:
        allowed = capability["allowed_consumers"]
        if len(allowed) != 1:
            raise ValueError(f"capability is not single-consumer: {capability['capability_id']}")
        consumer = allowed[0]
        for stage in stages:
            visible = stage == consumer
            cells.append(
                {
                    "information_id": capability["capability_id"],
                    "stage_id": stage,
                    "visibility": "visible" if visible else "forbidden",
                    "reason": (
                        f"Registry grants {capability['operation']} over exactly "
                        f"{capability['artifact_class']} to {consumer} for "
                        f"{capability['epoch']} under a one-consumer invocation handle."
                        if visible
                        else "No registry handle exists for this principal; direct, "
                        "derived, copied, stale, cross-epoch, ambient-path, count, "
                        "hash, identifier, ordering, timing, cache, and error-shape "
                        "access are forbidden and must fail with the constant-shape denial."
                    ),
                }
            )
    return {
        "information_items": information_items,
        "stages": stages,
        "cells": cells,
    }


TEST_REPLACEMENTS = {
    "V5_ES01_EXACT_EXTERNAL_AUTHORITY_AND_SCOPE": (
        "V6_ES01_EXACT_EXTERNAL_AUTHORITY_RELEASE_TUPLE_AND_SCOPE",
        "Bind every one of the nine release-tuple fields through external authorization, authority verdict, opaque transfer, and release receipt. Bare roots, implied authority, changed destinations, replayed nonces, and widened scope must be denied.",
        "Only a new exact external authorization plus producer-closed narrow attestations permits the one-shot tuple-bound transfer; no science or audit artifact creates authority.",
    ),
    "V5_ES02_DIRECTIONAL_EVIDENCE_AND_REPETITION_CAPABILITIES": (
        "V6_ES02_EPOCH_ATTENUATED_EVIDENCE_AUTHORSHIP_AND_REPETITION",
        "Exercise clause-level child authorship, temporal precedence, public grounding, meaning preservation, parent/repetition taint, stale handles, and every direct or derived side channel across epoch boundaries.",
        "Only independently child-authored and grounded propositions cross into eligibility; repeated parent wording, control metadata, and compiler-created semantics never do.",
    ),
    "V5_ES03_EXACT_WRITER_ROUTE_CAPABILITY_MASK_DOSE_AND_TAINT": (
        "V6_ES03_FRESH_FROM_BIRTH_WRITER_CONTRACT_MASK_DOSE_AND_TAINT",
        "Run the writer twice with identical immutable birth, fresh zero-delta initializer, cumulative eligible corpus, frozen writer contract, and seed while arbitrarily mutating prior active weights; fault masks, dose, seed, source, taint, and serialization separately.",
        "Candidate bytes and construction traces are identical under prior-weight mutation; every SLEEP begins from immutable birth plus a fresh zero-effective-delta personal adapter and uses no parent, DREAM, prior-weight, or candidate-derived input.",
    ),
    "V2_ES05_BIRTH_MERGE_AND_CONTENT_IDENTITY": (
        "V6_ES05_BIRTH_MERGE_CONTRACT_AND_CONTENT_IDENTITY",
        "Bind the exact frozen bootstrap writer, response mask, tokenizer, merge equation, dtype, serializer, toolchain, M0, seed, truncation, and receipt schemas; reconstruct each birth independently.",
        "T and D births are reproducible immutable artifacts from the same M0, and personal SLEEP starts with an empty personal adapter on the assigned birth.",
    ),
    "V5_ES06_DIRECTIONAL_LINEAGE_EVALUATION_AND_RETRY_FAULTS": (
        "V6_ES06_PRODUCER_CLOSED_LINEAGE_EVALUATION_AND_RETRY_FAULTS",
        "Trace an explicit producer for every candidate, transaction, preservation, promotion, quarantine, and audit receipt; inject stale CAS, root mismatch, crash, retry, rejection, and concurrent promotion faults.",
        "One operational retry preserves the exact snapshot; semantic rejection never retries identical evidence; no fault changes committed life or prior active weights, and every derivative of a rejected candidate is quarantined.",
    ),
    "V2_ES07_DIRECT_CONTROL_PAIR_AND_SEMANTIC_AUDIT": (
        "V6_ES07_BOOTSTRAP_CONTRACT_DIRECT_CONTROL_AND_SEMANTIC_AUDIT",
        "Audit paired T/D bootstrap rows for shared state, canonical action, public outcome, admission, action position, supervised-token and optimizer opportunity; test target blindness, structural overlap, all six computations, and M0 difficulty/damage separately.",
        "The only intended pair difference is one declared feedback-to-action computation in T versus the same direct action in D; downstream-derived information and policy-isomorphic target clones are absent.",
    ),
    "V5_ES08_SPLIT_AUDITOR_INCREMENTAL_TARGET_BLINDNESS": (
        "V6_ES08_PRODUCER_CLOSED_SPLIT_AUDITOR_TARGET_BLINDNESS",
        "Verify explicit producers for dependency manifests, taint receipts, lineage receipts, preservation projections, detailed findings, narrow attestations, authority verdicts, and release receipts; attack target leakage and auditor-created authority.",
        "Blindness and lineage auditors consume disjoint producer-closed receipts and emit quarantined findings plus fixed-size attestations only; neither reads scientific truth nor authors permission.",
    ),
    "V5_ES12_CURSOR_REPETITION_CONTROL_AND_ENACTMENT": (
        "V6_ES12_EPOCH_CURSOR_REPETITION_CONTROL_AND_ENACTMENT",
        "At ages 1, 9, 17, and 25 compare exact fixed-parent bytes under opposing child histories, close and reissue every epoch handle, and distinguish copied wording from uncued selective enactment on varied cases.",
        "The fixed parent is exogenous; repetition remains waking-only; only later qualifying child-authored behavior can become evidence, and uptake alone is not a causal repetition claim.",
    ),
    "V5_ES13_SPLIT_EVALUATION_STORAGE_EXTRACTION_USE_CONTROLS": (
        "V6_ES13_CHILD_AUTHORED_STORAGE_EXTRACTION_USE_CONTROLS",
        "Separate source fit, held-out cue extraction, native use on fresh homologous tasks, and interface preservation using adapter-off, deranged, wrong-life, and provenance controls over child-authored evidence only.",
        "Neither low training loss nor verbatim recall counts as usable experiential learning; any claimed gain requires extraction and native action without textual retrieval or interface harm.",
    ),
    "V5_ES14_FIREWALLED_PERSONAL_REPLAY_DEPENDENCE": (
        "V6_ES14_FRESH_FROM_BIRTH_REPLAY_DEPENDENCE",
        "Construct closure- and dose-matched replay versus filler candidates from the same immutable birth and fresh zero-delta adapter; preserve cumulative eligible coverage and forbid prior candidate outputs as evidence.",
        "Any difference is attributable to registered replay treatment under a fresh-from-birth writer, not incremental continuation, omitted history, changed dose, or evaluation feedback.",
    ),
    "V5_ES16_FIREWALLED_CADENCE_TOTAL_AND_STANDARDIZED_LEDGER": (
        "V6_ES16_FRESH_FROM_BIRTH_CADENCE_TOTAL_AND_STANDARDIZED_LEDGER",
        "Compare preregistered K4/K1 lives with equal total opportunity, fresh-from-birth cumulative candidates at every SLEEP, disposable checkpoint exams, and standardized terminal ledger rewrites.",
        "Cadence is reported as a randomized total package; natural-versus-standardized terminal contrasts remain descriptive and cannot be labeled direct or mediated effects.",
    ),
    "V2_ES17_PRIMARY_STATISTICS_AND_SPEND_ORDER": (
        "V6_ES17_PREGENERATION_STATISTICS_AND_ACTION_PREREQUISITES",
        "Before any treatment or benchmark generation, freeze endpoints, root-level assignment, power, intervals, multiplicity, missingness, safety comparator, stopping, spend order, and the exact action-prerequisite receipts.",
        "Tasks, ages, clones, and seeds within a root are not independent units; absent complete prospective statistics and action prerequisites, generation and downstream execution are denied.",
    ),
    "V5_ES19_COMPLETE_DIRECTIONAL_LIFECYCLE_AND_NONINTERFERENCE": (
        "V6_ES19_PRODUCER_CLOSED_EPOCH_CAPABILITY_NONINTERFERENCE",
        "Validate the registry-generated complete principal-by-capability product, all 57 close/reissue bridges, producers, lifetimes, schemas, constant-shape failures, ambient-path denial, and split evaluation noninterference.",
        "Every permitted read, write, append, dereference, equality bind, cursor advance, and opaque transfer has one producer, one consumer invocation, one epoch, and no stale or covert alternative.",
    ),
    "V5_ES20_CAPABILITY_CLASSIFIED_REJECTION_PRESERVES_LIFE": (
        "V6_ES20_FRESH_FROM_BIRTH_STALE_CAS_REJECTION_PRESERVES_LIFE",
        "Inject every classified writer, candidate, evaluator, promotion, and CAS fault while checking fresh-from-birth reconstruction, cumulative-life retention, active-head immutability, and derivative quarantine.",
        "Failure never silently falls back to prior weights during candidate construction and never erases committed child life; stale or rejected candidates cannot become active or future evidence.",
    ),
    "V5_ES18_FRESH_REVIEW_EXTERNAL_AUTHORITY_AND_GPU_GATE": (
        "V6_ES18_FRESH_REVIEW_BOUND_RELEASE_AND_GPU_AUTHORITY",
        "Require fresh independent implementation review and author-side advocate, then separately bind exact GPU/resource, external-science, claim, publication, push, and release authorities to their own roots and scopes.",
        "No passing review or earlier authorization implies GPU use, external science, a claim, publication, push, or release; each terminal action remains independently authorized.",
    ),
    "V5_ES21_EXHAUSTIVE_FIRST_AFFECTED_ACTION_GATE": (
        "V6_ES21_NONCIRCULAR_ACTION_PREREQUISITE_DAG",
        "Topologically validate all 40 actions and every prerequisite receipt; construct the G0 parser, fake artifacts, fake dispatchers, bridge, validator, gate, and fault fixtures without any protected domain action, then deny every missing, cyclic, stale, wrong-root, expired, replayed, or unknown path.",
        "G0 is model-free and noncircular; every G1-G4 domain action depends on the installed fail-closed gate plus its own exact contracts and authority, and GPU is last after CPU evidence and fresh review.",
    ),
}


def build() -> dict:
    doc = copy.deepcopy(json.loads((V5_DIR / "change.json").read_text()))
    registry = json.loads((V5_DIR / "v6_capability_registry.json").read_text())
    dag = json.loads((V5_DIR / "v6_action_prerequisite_dag.json").read_text())
    science = json.loads((V5_DIR / "v6_scientific_core.json").read_text())

    doc.update(
        change_id="chg_20260909_extractable_sleep_bootstrap_v6",
        title="Fresh-from-birth experiential SLEEP and teachability bootstrap v6",
        summary=(
            "Keep the organism to THINK, DREAM, and SLEEP, with an optional "
            "one-time target-blind teachability bootstrap. Personal SLEEP "
            "rebuilds a fresh zero-delta adapter from immutable birth and the "
            "full cumulative grounded child-authored corpus; the compiler may "
            "replay and paraphrase but may not invent a thought, correction, "
            "generalization, or relation. Exact one-consumer epoch capabilities "
            "and a noncircular action-prerequisite DAG are laboratory guards, "
            "not extra cognitive organs."
        ),
        system_thesis=(
            "THINK is the continuing child thought-action-public-outcome stream. "
            "DREAM only manages disposable waking context. SLEEP preserves and "
            "re-expresses grounded propositions the child already authored, "
            "then writes a fresh personal LoRA from immutable birth. Repeated "
            "parenting stays in waking cognition. A one-time T versus D birth "
            "comparison tests whether schooling in feedback-to-action makes the "
            "same later parenting accelerate learning without importing final-task answers."
        ),
    )

    additions = [
        ("change.json", "Adjudicated v5 predecessor proposal."),
        ("interpretation_science.json", "Fresh v5 scientific interpretation."),
        ("interpretation_systems.json", "Fresh v5 systems interpretation."),
        ("critique.json", "V5 adversarial cross-critique."),
        ("consensus.json", "V5 adjudicated rework decision and 21-test dispositions."),
        ("v6_blocker_resolution.md", "Exact prose resolution of all v5 proposal blockers."),
        ("v6_scientific_core.json", "Independent exact causal, semantic, estimand, and claim core."),
        ("v6_capability_registry.json", "Independent exact producer/consumer/epoch capability registry."),
        ("v6_action_prerequisite_dag.json", "Independent exact noncircular first-action prerequisite DAG."),
    ]
    existing = {entry["path"] for entry in doc["context_files"]}
    for name, purpose in additions:
        path = V5_DIR / name
        relative = str(path.relative_to(ROOT))
        if relative not in existing:
            doc["context_files"].append(
                {"path": relative, "sha256": sha(path), "purpose": purpose}
            )

    replace_node(
        doc,
        "SLEEP_COMPILER",
        "A closed-world compiler accepts only clause-admissible propositions already authored by the continuing child and grounded in that child's committed public actions or outcomes. It may SELECT, PARTITION, ORDER, DEDUPLICATE, REPLAY, CONTRAST, PARAPHRASE, and form RETRIEVAL_VIEW or USE_VIEW rows only without adding semantics; every loss-bearing clause retains exact proposition and support provenance.",
        "Compilation enriches the child's experience without becoming a hidden thinker or parent.",
    )
    replace_node(
        doc,
        "CHILD_LORA_WRITER",
        "At every personal SLEEP, the writer starts from the assigned immutable birth plus a new exactly zero-effective-delta personal LoRA and trains on the full cumulative eligible child-life corpus under one later-frozen response-only writer, replay, dose, rank, optimizer, tokenizer, merge, dtype, serializer, truncation, seed, and receipt contract. It cannot read prior active weights or anything derived from them.",
        "Fresh-from-birth cumulative reconstruction makes every active child a reproducible function of birth plus admitted life, rather than an uncontrolled continuation of prior adapter state.",
    )
    replace_node(
        doc,
        "MERGED_SCHOOLED_BIRTH_BUILDER",
        "Teachability T and direct-solution D adapters are produced once from the same frozen M0 and exact paired corpus, merged under a prospectively frozen materialization contract, rounded and serialized once, and sealed as distinct immutable births. M0 is retained only as a separate competence-and-damage diagnostic.",
        "The birth intervention persists while remaining separate from personal experiential memory.",
    )
    replace_node(
        doc,
        "DIRECT_SOLUTION_ACTIVE_CONTROL",
        "Every T/D pair shares one state, canonical rational action, public outcome, admission decision, action position, supervised-token opportunity, and optimizer opportunity. T demonstrates exactly one declared general feedback-to-action computation before that action; D receives the same action directly. Neither arm contains downstream-derived or policy-isomorphic final-task information.",
        "This distinguishes learning-readiness from preloaded task skill without pretending the control is semantically neutral.",
    )
    replace_node(
        doc,
        "EVIDENCE_SUPPORT_RESOLVER",
        "A model-free resolver admits a semantic clause only when exact committed records prove child authorship before compilation, required prospective or retrospective temporal order, same-life public grounding, frozen support threshold, and full semantic scope. Dispute or missing evidence rejects the clause; outcomes cannot backfill an unstated rationale.",
        "The child must first think the thought; the compiler is never allowed to create it.",
    )
    replace_node(
        doc,
        "DIRECTIONAL_CAPABILITY_REGISTRY",
        f"The exact registry {sha(V5_DIR / 'v6_capability_registry.json')} defines {len(registry['capabilities'])} one-consumer capabilities, {len(registry['artifact_classes'])} artifact classes, {len(registry['epoch_bridges'])} close-and-reissue bridges, seven registered operations including TRANSFER_OPAQUE, explicit producers, handle and artifact lifetimes, constant-shape failures, and the complete release tuple. The visibility matrix is generated from these bytes.",
        "The registry removes ambient visibility and makes every permitted information flow enumerable and testable.",
    )
    replace_node(
        doc,
        "FIRST_AFFECTED_ACTION_REGISTRY",
        f"The exact DAG {sha(V5_DIR / 'v6_action_prerequisite_dag.json')} topologically gates {len(dag['actions'])} actions from a separately authorized model-free G0 harness through guarded implementation, CPU/data/model/writer execution, fresh review, GPU/external science, claim, publication, push, and tuple-bound release. Unknown, cyclic, stale, wrong-root, wrong-scope, expired, or replayed prerequisites are denied.",
        "The gate can be built and tested without performing the protected actions it will later guard.",
    )
    replace_node(
        doc,
        "RELEASE_CONTROLLER",
        "Release is a registered one-shot TRANSFER_OPAQUE operation over the complete nine-field tuple: artifact root, artifact class, destination identity, transfer operation, protocol, requested scope, nonce, expiry, and idempotency key. It consumes a separate exact human authorization and narrow producer-closed attestations; it cannot inspect content or widen scope.",
        "A bare root or internal scientific success is not release authority.",
    )

    replace_edge(
        doc,
        "PARENT_TO_CHILD_TO_SLEEP",
        "There is no parent-to-SLEEP edge. The sole permitted causal path is parent or repetition intervention -> current waking context -> child thought -> child action -> public outcome -> committed child trace -> independent clause eligibility -> later personal SLEEP. Parent bytes or derived semantics, IDs, counts, hashes, order, timing, cache state, filenames, and error shapes are forbidden to the resolver, compiler, and writer.",
        "Parenting must change what the child itself thinks and does, not become disguised supervised targets.",
    )
    replace_edge(
        doc,
        "CANDIDATE_TO_ATOMIC_HEAD",
        "The writer closes candidate bytes before an equality-only snapshot bind. Candidate construction has immutable-birth, fresh-zero-delta, cumulative-evidence, frozen-contract, and seed inputs only. The evaluator may later dereference prior and candidate weights; the promotion gate receives only candidate-root equality, its bound verdict, and a full-head CAS binding.",
        "Prior weights may judge the candidate afterward but can never condition how it was constructed.",
    )
    replace_edge(
        doc,
        "CHILD_TRACE_TO_SUPPORT_RESOLVER",
        "Only clauses whose exact child proposition IDs, public support IDs, life ID, commit roots, grounding rule, threshold, and temporal order pass the frozen resolver become eligible evidence. A generalized or corrective clause must already have been authored by the child at that exact semantic scope.",
        "Grounding and authorship prevent the compiler from turning valid premises into new cognition.",
    )
    replace_edge(
        doc,
        "SPLIT_AUDITS_TO_EXTERNAL_AUTHORITY",
        "Detailed blindness and lineage findings remain quarantined. Only fixed-size producer-closed attestations plus a separately authored exact human authorization reach the authority verifier; the release controller receives its verdict and the identical complete release tuple.",
        "Audit evidence can establish facts but cannot manufacture permission.",
    )

    replace_loop(
        doc,
        "SLEEP_COMPILE_WRITE_COMMIT",
        after=(
            "For SLEEP event s, resolve the full cumulative eligible child-life corpus at a frozen cutoff; render only child-authored grounded semantics; initialize a new zero-effective-delta personal LoRA on immutable birth B_z; construct C_s := W(B_z, Z0_s, E_le_s, K_sleep, seed_s); close C_s; then apply the equality-only staging guard. Prior active weights are unavailable until a separate postconstruction preservation comparison."
        ),
        trigger="Only after the exact writer, support, replay, transaction, mask, dose, serialization, and statistics contracts for this action have separately frozen authority.",
        reads=[
            "E4_COMPILER_READ_ELIGIBLE_EVIDENCE",
            "E4_COMPILER_READ_IMMUTABLE_BIRTH",
            "E4_COMPILER_READ_SLEEP_WRITER_CONTRACT",
            "E4_COMPILER_BIND_COMMITTED_SNAPSHOT",
        ],
        writes=[
            "E4_COMPILER_WRITE_CANDIDATE",
            "E4_COMPILER_WRITE_TRANSACTION_RECEIPT",
            "E4_COMPILER_APPEND_CAPABILITY_EVENTS",
        ],
        stop_condition="Any unsupported clause, omitted eligible proposition, parent/DREAM/prior-weight/candidate/scientific taint, nonzero initializer, nonfinite update, dose or root mismatch, stale CAS, or undeclared handle fails closed. Rejection preserves committed life and the prior active child.",
        rationale="SLEEP writes the child's accumulated experience while preserving the thinker/compiler boundary and making every candidate reproducible from birth plus life.",
    )
    replace_loop(
        doc,
        "BOOTSTRAP_BUILD_AND_BIRTH",
        after=(
            "Build paired target-blind T and D schooling rows before downstream instances exist. T shows one general feedback-to-action computation and D shows the identical canonical rational action directly, with every other opportunity matched. Train and materialize immutable births once; keep M0 as a separate diagnostic. The exact sources, row count, domains, rank, dose, and writer bytes remain deferred to a later frozen contract."
        ),
        trigger="Only after target-blind sources, paired-control construction, statistics, writer/materialization, and semantic-audit contracts receive their own exact authority.",
        reads=[
            "E1_BUILDER_READ_STATIC_SPEC",
            "E1_BIRTH_READ_PAIRED_CORPUS",
            "E1_BIRTH_READ_FROZEN_M0",
            "E1_BIRTH_READ_BOOTSTRAP_CONTRACT",
        ],
        writes=[
            "E1_BUILDER_WRITE_PAIRED_CORPUS",
            "E1_BIRTH_WRITE_IMMUTABLE_BIRTH",
            "E1_BIRTH_APPEND_BOOTSTRAP_AUDIT",
        ],
        stop_condition="Stop for downstream-derived information, structural target overlap, unmatched action/outcome or optimizer opportunity, semantic-control failure, M0 damage, materialization drift, or nonreproducible roots.",
        rationale="The bootstrap may lower the activation energy for parenting without teaching the deployment task or replacing lived learning.",
    )
    replace_loop(
        doc,
        "PARENT_REPETITION_AND_FADE",
        after=(
            "Repeat one core process lesson across varied waking cases until the child independently restates and selectively enacts it. Fixed parenting emits the same bytes at ages 1, 9, 17, and 25 regardless of history; adaptive parenting is a separately labeled later package. Parent text stays visible only during childhood waking context and remains loss-masked and absent from personal SLEEP."
        ),
        trigger="A fixed schedule event or a separately frozen adaptive-parent policy chooses a waking intervention.",
        reads=[
            "E2_FIXED_READ_LESSON_TABLE",
            "E2_FIXED_READ_CURSOR",
            "E2_ADAPTIVE_READ_CHILD_TRACE",
            "E2_ADAPTIVE_READ_PUBLIC_OBSERVATION",
            "E2_ADAPTIVE_READ_PARENT_HISTORY",
            "E2_ADAPTIVE_READ_REPETITION_STATE",
        ],
        writes=[
            "E2_FIXED_WRITE_LIVE_PARENT_MESSAGE",
            "E2_FIXED_APPEND_PARENT_AUDIT",
            "E2_FIXED_ADVANCE_CURSOR",
            "E2_ADAPTIVE_WRITE_LIVE_PARENT_MESSAGE",
            "E2_ADAPTIVE_APPEND_PARENT_AUDIT",
            "E2_ADAPTIVE_WRITE_PARENT_HISTORY",
            "E2_ADAPTIVE_WRITE_REPETITION_STATE",
        ],
        stop_condition="Copied phrases without grounded selective enactment are not uptake. Stop on any parent/repetition path into evidence membership, compiler rendering, dose, writer control, or gradients.",
        rationale="Repetition is a teaching behavior in THINK; personal SLEEP only learns what the child subsequently makes its own through grounded life.",
    )
    replace_loop(
        doc,
        "CANDIDATE_PRESERVATION_AND_PROMOTION",
        after=(
            "After candidate closure, a fresh evaluator alone dereferences prior and candidate weights and writes root-bound preservation evidence and a verdict. A separate gate sees only the verdict, candidate-root equality, and committed full-head CAS, then either promotes the candidate root or quarantines every candidate derivative."
        ),
        trigger="After fresh-from-birth candidate construction and before any candidate is visible to waking or scientific evaluation.",
        reads=[
            "E5_EVALUATOR_DEREFERENCE_PRIOR_ACTIVE",
            "E5_EVALUATOR_DEREFERENCE_CANDIDATE",
            "E5_EVALUATOR_READ_PRESERVATION_PANEL",
            "E5_EVALUATOR_BIND_CANDIDATE_ROOT",
            "E5_GATE_READ_PROMOTION_VERDICT",
            "E5_GATE_BIND_CANDIDATE_ROOT",
            "E5_GATE_BIND_COMMITTED_CAS",
        ],
        writes=[
            "E5_EVALUATOR_WRITE_PRESERVATION_EVIDENCE",
            "E5_EVALUATOR_WRITE_PROMOTION_VERDICT",
            "E5_GATE_WRITE_ACTIVE_WEIGHT",
            "E5_GATE_WRITE_TRANSACTION_RECEIPT",
        ],
        stop_condition="Missing producer, root mismatch, stale CAS, mutated candidate, rejected verdict, replayed handle, or undeclared operation fails closed without altering prior active weights or committed life.",
        rationale="Preservation can veto a write without leaking evaluation into learning or using prior weights to construct the candidate.",
    )
    replace_loop(
        doc,
        "DISPOSABLE_SCIENTIFIC_EVALUATION",
        after=(
            "A fresh exam executor reads one public input and the current active weights, emits and closes one immutable transcript, and is destroyed. A model-free scorer then reads only that transcript and hidden truth. A reporter reads only frozen score records. No evaluation artifact returns to the child, parent, DREAM, SLEEP, candidate, promotion, or release path."
        ),
        trigger="Only at prospectively frozen ages and budgets after the noninterference fixture and action prerequisites pass under separate authority.",
        reads=[
            "E6_EXECUTOR_READ_PUBLIC_OBSERVATION",
            "E6_EXECUTOR_DEREFERENCE_ACTIVE_WEIGHT",
            "E6_SCORER_READ_TRANSCRIPT",
            "E6_SCORER_READ_HIDDEN_TRUTH",
            "E6_REPORTER_READ_SCORE_RECORD",
        ],
        writes=[
            "E6_EXECUTOR_WRITE_TRANSCRIPT",
            "E6_SCORER_WRITE_SCORE_RECORD",
            "E6_REPORTER_WRITE_REPORT",
        ],
        stop_condition="Executor truth or prior-product access, scorer model or lineage access, reporter feedback, mutable transcript, stale executor, cross-epoch handle, or undeclared operation fails closed.",
        rationale="The exam measures a continuing child without teaching or selecting it.",
    )
    replace_loop(
        doc,
        "AUDIT_EXTERNAL_AUTHORITY_AND_RELEASE",
        after=(
            "Producer-closed blindness and lineage audits emit quarantined findings and fixed-size narrow attestations. A new external human authorization binds the complete release tuple. The verifier checks only those inputs, and the controller performs exactly one registered opaque transfer under the identical tuple."
        ),
        trigger="Only after all separately authorized prerequisites complete and a human authors exact, unexpired, one-shot authority for the named action and scope.",
        reads=[
            "E7_BLINDNESS_READ_COMPILER_TAINT",
            "E7_BLINDNESS_READ_DEPENDENCY_MANIFEST",
            "E7_BLINDNESS_READ_DISPATCHER_MANIFEST",
            "E7_BLINDNESS_READ_SUPPORT_TAINT",
            "E7_LINEAGE_READ_CANDIDATE_RECEIPT",
            "E7_LINEAGE_READ_PRESERVATION_EVIDENCE",
            "E7_LINEAGE_READ_PROMOTION_RECEIPT",
            "E7_LINEAGE_READ_PROMOTION_VERDICT",
            "E8_VERIFIER_READ_BLINDNESS_ATTESTATION",
            "E8_VERIFIER_READ_LINEAGE_ATTESTATION",
            "E8_VERIFIER_READ_EXTERNAL_AUTHORIZATION",
            "E8_VERIFIER_BIND_RELEASE_TUPLE",
            "E8_RELEASE_READ_AUTHORITY_VERDICT",
            "E8_RELEASE_BIND_RELEASE_TUPLE",
            "E8_RELEASE_TRANSFER_TARGET",
        ],
        writes=[
            "E7_BLINDNESS_WRITE_FINDING",
            "E7_BLINDNESS_WRITE_ATTESTATION",
            "E7_LINEAGE_WRITE_FINDING",
            "E7_LINEAGE_WRITE_ATTESTATION",
            "E8_VERIFIER_WRITE_AUTHORITY_VERDICT",
            "E8_RELEASE_WRITE_RECEIPT",
        ],
        stop_condition="No producer, stale or failed attestation, absent/mismatched human authorization, changed tuple, replay, expiry, inspection, or widened scope denies the action with constant-shape behavior.",
        rationale="Science, audit, permission, and release are causally separate.",
    )

    claims = doc["claim_delta"]["claims"]
    by_id(claims, "claim_id", "C_EXPERIENCE_EXTRACTABLE_AND_USABLE").update(
        after="Conditional on later powered evidence, a personal LoRA reconstructed from immutable birth plus the cumulative grounded child-authored life corpus is recoverable under held-out cues and improves native action on fresh homologous tasks without textual retrieval, compiler-created cognition, or interface harm.",
        evidence_needed="Fresh-from-birth writer factorial; clause authorship and support receipts; source fit, held-out extraction, native use, adapter-off, deranged, wrong-life, replay/filler, preservation, and powered independent-root controls.",
    )
    by_id(claims, "claim_id", "C_BOOTSTRAP_IMMEDIATE_RECEPTIVITY").update(
        after="Conditional on Delta_R, T confers greater immediate selective use of novel correct process advice than paired direct-solution control D before any personal SLEEP.",
        evidence_needed="Root-randomized T/D disposable same-state clones under correct, none, irrelevant, and wrong advice, with M0 reported separately as a competence/damage diagnostic.",
    )
    by_id(claims, "claim_id", "C_BOOTSTRAP_FIXED_CURRICULUM_SLEEP_ACCELERATION").update(
        after="Conditional on Delta_F, T changes the 32-lesson learning-speed effect of the total fixed-curriculum-plus-personal-SLEEP regime relative to D; this is effect modification, not proof of parenting-only or SLEEP-only mediation.",
        evidence_needed="Primary D/T x absent/fixed root-randomized factorial, entry-normalized AUC at ages 0/8/16/24/32, exact fixed bytes at ages 1/9/17/25, matched solo opportunity, fresh-from-birth cumulative SLEEP, one-way exams, and prospective uncertainty.",
    )
    by_id(claims, "claim_id", "C_BOOTSTRAP_ADAPTIVE_PACKAGE_ACCELERATION").update(
        after="Conditional on separately run Delta_E, T changes the learning-speed effect of the full adaptive-parent-plus-child-plus-personal-SLEEP package relative to D; it does not isolate parenting or SLEEP alone.",
        evidence_needed="Separately randomized T/D x absent/adaptive roots under a prospectively frozen policy, matched nonparent opportunity, full parent effort and information receipts, clean exams, raw curves, and safety outcomes.",
    )

    for test in doc["acceptance_tests"]:
        replacement = TEST_REPLACEMENTS.get(test["test_id"])
        if replacement is None:
            continue
        new_id, setup, expected = replacement
        test.update(
            test_id=new_id,
            setup=setup,
            expected=expected,
            falsifies=(
                "Any mismatch, undeclared producer or consumer, protected-state side channel, "
                "compiler-created semantic content, cross-epoch handle reuse, hidden evaluation "
                "feedback, noncircularity failure, internally manufactured authority, or silent "
                "fallback falsifies the contract."
            ),
            evidence_artifact=(
                "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v6/"
                f"evidence/{new_id.lower()}.json"
            ),
        )
    before_impl = {
        "V6_ES01_EXACT_EXTERNAL_AUTHORITY_RELEASE_TUPLE_AND_SCOPE",
        "V6_ES02_EPOCH_ATTENUATED_EVIDENCE_AUTHORSHIP_AND_REPETITION",
        "V6_ES03_FRESH_FROM_BIRTH_WRITER_CONTRACT_MASK_DOSE_AND_TAINT",
        "V6_ES05_BIRTH_MERGE_CONTRACT_AND_CONTENT_IDENTITY",
        "V6_ES06_PRODUCER_CLOSED_LINEAGE_EVALUATION_AND_RETRY_FAULTS",
        "V6_ES08_PRODUCER_CLOSED_SPLIT_AUDITOR_TARGET_BLINDNESS",
        "V6_ES12_EPOCH_CURSOR_REPETITION_CONTROL_AND_ENACTMENT",
        "V6_ES19_PRODUCER_CLOSED_EPOCH_CAPABILITY_NONINTERFERENCE",
        "V6_ES20_FRESH_FROM_BIRTH_STALE_CAS_REJECTION_PRESERVES_LIFE",
        "V6_ES21_NONCIRCULAR_ACTION_PREREQUISITE_DAG",
    }
    before_model = {
        "V2_ES04_ZERO_EFFECTIVE_DELTA_INITIALIZER",
        "V6_ES17_PREGENERATION_STATISTICS_AND_ACTION_PREREQUISITES",
    }
    before_gpu = {
        "V6_ES07_BOOTSTRAP_CONTRACT_DIRECT_CONTROL_AND_SEMANTIC_AUDIT",
        "V6_ES18_FRESH_REVIEW_BOUND_RELEASE_AND_GPU_AUTHORITY",
    }
    for test in doc["acceptance_tests"]:
        if test["test_id"] in before_impl:
            test["required_before"] = "implementation"
        elif test["test_id"] in before_model:
            test["required_before"] = "model_execution"
        elif test["test_id"] in before_gpu:
            test["required_before"] = "gpu_run"
        else:
            test["required_before"] = "scientific_claim"

    doc["visibility_matrix"] = build_visibility(registry)
    doc["human_boundary"] = {
        "required": True,
        "decision_owner": "Rohin Ghosh",
        "decision_question": (
            "After two fresh interpretations, adversarial critique, and adjudicated "
            "consensus over these exact v6 bytes, does Rohin adopt only this architecture "
            "proposal? G0 implementation, domain implementation, model/tokenizer/data/adapter "
            "execution, GPU use, science, claims, publication, push, and release each remain "
            "separately unauthorized and prerequisite-gated."
        ),
        "forbidden_before_approval": [
            "implementation",
            "model_execution",
            "tokenizer_execution",
            "bootstrap_or_benchmark_generation",
            "adapter_or_checkpoint_work",
            "gpu_or_resource_use",
            "external_scientific_execution",
            "scientific_claim",
            "publication_or_push",
            "release",
        ],
    }

    # Proposal construction consumes these exact scientific/system inputs but
    # does not claim their self-audits authorize any downstream action.
    assert science["personal_sleep_causal_contract"]["initialization"]["continuation_from_prior_personal_adapter"] is False
    assert registry["internal_invariants"][6]["invariant_id"] == "CR07_NO_PRIOR_WEIGHT_TO_PERSONAL_SLEEP"
    assert dag["internal_invariants"][11]["invariant_id"] == "AD12_NO_SELF_GATE"
    return doc


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2) + "\n")
