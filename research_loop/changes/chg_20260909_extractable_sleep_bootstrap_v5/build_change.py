"""Deterministically render the v5 proposal from the hash-bound v4 proposal.

This is proposal construction only.  It performs no model, tokenizer, data,
adapter, GPU, benchmark, or scientific execution.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
V4 = ROOT / "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v4/change.json"
OUT = Path(__file__).with_name("change.json")


def _node(doc: dict, node_id: str) -> dict:
    return next(x for x in doc["graph_delta"]["nodes"] if x["node_id"] == node_id)


def _edge(doc: dict, edge_id: str) -> dict:
    return next(x for x in doc["graph_delta"]["edges"] if x["edge_id"] == edge_id)


def _loop(doc: dict, loop_id: str) -> dict:
    return next(x for x in doc["loop_delta"]["loops"] if x["loop_id"] == loop_id)


def build() -> dict:
    doc = json.loads(V4.read_text())
    doc.update(
        change_id="chg_20260909_extractable_sleep_bootstrap_v5",
        title="Extractable SLEEP writer and feedback-to-learning birth bootstrap v5",
        summary=(
            "Preserve the simple THINK-DREAM-SLEEP organism and optional "
            "target-blind learning-readiness bootstrap while replacing broad "
            "state visibility with named one-way, epoch-scoped capabilities; "
            "split exam execution, truth scoring, reporting, audit, external "
            "authority, and release; and gate every first affected action."
        ),
        system_thesis=(
            "THINK is the continuous child thought-action-outcome stream; DREAM "
            "only rebuilds finite waking context; SLEEP compiles grounded "
            "child-authored experience and writes the personal LoRA. An optional "
            "one-time target-blind bootstrap may make a birth more receptive to "
            "repeated parenting, but parent prose never becomes personal SLEEP "
            "data and the compiler never invents cognition."
        ),
    )
    for path, sha, purpose in [
        ("change.json", "63d072108be7058b43a27cf90c78d51a1a70a689ab40a31bf8b97bafea998c4c", "V4 predecessor proposal."),
        ("interpretation_science.json", "27ec0d3b46fd19febdccd7ae714d9d62c3abb3ccd67f6aea77f1899c96091909", "Fresh v4 scientific interpretation."),
        ("interpretation_systems.json", "5407e0a0f991d0b95da0e1d114f70d903b6b31bfecb9e9819c9d5500ee64106e", "Fresh v4 systems interpretation."),
        ("critique.json", "41cb6d03257d091a6c4297bd38131aa66a711d9cf4c57197e19f69a302fd5251", "V4 cross-critique identifying seven proposal-byte blockers."),
        ("consensus.json", "2eeb983a5d5a7c00745ead112d0beb62588ed4d8c1a39eb7689944d65958b4c5", "V4 adjudicated rework decision."),
        ("v5_blocker_resolution.md", "beb9d978c31bbe80af50146677fe52586326723f321ca7b88919aca1f41f08a9", "Exact successor resolution of all seven v4 blockers."),
    ]:
        doc["context_files"].append({
            "path": f"research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v4/{path}",
            "sha256": sha,
            "purpose": purpose,
        })

    n = _node(doc, "ATOMIC_LINEAGE_HEAD")
    n.update(
        node_id="LEAST_AUTHORITY_LINEAGE_CAPABILITIES",
        after=(
            "No semantic stage receives a composite lineage head. Immutable "
            "birth, active weights, eligible life evidence, staged candidate "
            "closure, non-dereferenceable candidate root, equality-only committed "
            "CAS token, parent audit, and repetition state are separate. Every "
            "capability names one operation and one lifecycle epoch; undeclared "
            "operations and cross-capability dereference are forbidden."
        ),
        rationale=(
            "A composite head can bypass the parent/repetition firewall and "
            "candidate isolation even when prose calls it opaque."
        ),
    )
    n = _node(doc, "FIXED_POLICY_DEVELOPMENT_ASSAY")
    n.update(
        after=(
            "The fixed controller receives only immutable outbound lesson bytes "
            "keyed by ages 1, 9, 17, and 25, a monotone external schedule cursor, "
            "and write-only parent-audit append. It cannot read child behavior, "
            "outcomes, adaptive state, its audit history, SLEEP, candidates, exams, "
            "or scores. Opposite mock histories receive identical bytes at the "
            "same ages."
        ),
        rationale="Fixed repetition must be exogenous; adaptive parenting is a separately labeled package.",
    )
    n = _node(doc, "DREAM_DISPOSABLE_CONTEXT")
    n.update(
        after=(
            "DREAM emits a disposable waking cache bound separately to the exact "
            "active-weight, committed-child-trace, public-observation, current-live-"
            "parent-message, and prior-cache roots it was allowed to read. It is "
            "rebuilt when any named source changes and forbidden to personal SLEEP "
            "as evidence or conditioning."
        ),
        rationale="DREAM manages waking consciousness without a composite lineage capability or persistent evidence authority.",
    )
    n = _node(doc, "LINEAGE_PROMOTION_GATE")
    n.update(
        after=(
            "The gate receives only candidate-root equality, the typed verdict "
            "bound to that root, and an equality-only CAS token over the committed "
            "transaction. It cannot dereference candidate, life, parent, repetition, "
            "DREAM, preservation, or evaluation content and may only promote the "
            "active-weight root or quarantine the candidate."
        ),
        rationale="Promotion is an equality-checked transaction, not a semantic reader or directory scan.",
    )
    n = _node(doc, "SCIENTIFIC_EVALUATION_FIREWALL")
    n.update(
        node_id="SPLIT_SCIENTIFIC_EVALUATION",
        after=(
            "Each disposable exam is split into a fresh model executor that sees "
            "public input plus active weights, a model-free truth scorer that sees "
            "the closed transcript plus hidden truth, and a reporter that sees only "
            "frozen score records. None feeds child, parent, DREAM, SLEEP, candidate, "
            "promotion, audit authority, or release."
        ),
        rationale="No component may possess model execution, hidden answers, and prior scientific products together.",
    )
    n = _node(doc, "RELEASE_CONTROLLER")
    n.update(
        after=(
            "Blindness audit, lineage-safety audit, external human authorization, "
            "authority verification, and release are separate. The verifier sees "
            "only exact external authorization and narrow attestations bound to "
            "named roots; release sees only that verdict and exact target root."
        ),
        rationale="Auditors establish narrow facts; only an external human supplies release authority.",
    )
    doc["graph_delta"]["nodes"].extend([
        {"operation":"add","node_id":"DIRECTIONAL_CAPABILITY_REGISTRY","before":"","after":"Only named READ, WRITE, APPEND, DEREFERENCE, BIND_EQUALITY, or ADVANCE capabilities exist. Each has one schema, producer/consumer set, epoch, constant-shape success/failure behavior, and no undeclared counts, hashes, identifiers, ordering, timing, filenames, cache keys, errors, or stale handles.","rationale":"Broad visible or derived-only state is an undeclared information channel."},
        {"operation":"add","node_id":"EVIDENCE_SUPPORT_RESOLVER","before":"","after":"A model-free resolver reads committed child traces and matching public observations, applies frozen support rules, and emits eligible-life evidence. It cannot read parent bytes/audit, repetition state, DREAM, hidden truth, candidate products, or scores.","rationale":"Grounded child evidence must be admitted without making the compiler a teacher or verifier."},
        {"operation":"add","node_id":"FIXED_PARENT_CONTROLLER","before":"","after":"A stateless controller emits only the immutable lesson bytes named by the monotone external cursor, appends a write-only audit event, and advances the cursor once. It has no child-conditioned or self-history input.","rationale":"The fixed arm estimates repeated teaching under a genuinely exogenous policy."},
        {"operation":"add","node_id":"EXAM_MODEL_EXECUTOR","before":"","after":"A fresh executor reads one public exam input and active weights, emits an immutable transcript, and is destroyed; it cannot read truth, scores, prior transcripts, reports, or lineage state.","rationale":"The tested model must not be conditioned on answers or prior results."},
        {"operation":"add","node_id":"TRUTH_SCORER","before":"","after":"A model-free scorer reads only a closed transcript and frozen hidden truth, emits a typed score, and cannot call a model, edit the transcript, or access continuing lineage.","rationale":"Truth can grade without teaching or selecting the learner."},
        {"operation":"add","node_id":"SCIENTIFIC_REPORTER","before":"","after":"The reporter reads frozen score records and emits reports only; reports and scores have no return edge into execution, development, lineage, audit authority, or release.","rationale":"Reporting cannot adapt the learner or choose its weights."},
        {"operation":"add","node_id":"SPLIT_AUDIT_AND_AUTHORITY","before":"","after":"A blindness auditor sees dependency manifests and taint receipts only; a lineage-safety auditor sees transaction/root/preservation receipts only; an authority verifier sees only their narrow attestations plus a new exact external human authorization. No auditor authors authority.","rationale":"The prior omniscient auditor created a protected-evidence-to-release path."},
        {"operation":"add","node_id":"FIRST_AFFECTED_ACTION_REGISTRY","before":"","after":"One fail-closed registry enumerates CPU/GPU model calls, treatment-data tokenizer use, bootstrap/benchmark generation, writer/adapter/merge/checkpoint work, candidate compile/evaluate/promote, disposable exams, resource dispatch, and external scientific release, with exact prerequisite receipts for each.","rationale":"A generic model-execution label cannot gate all experiment-affecting actions."},
    ])

    e = _edge(doc, "CANDIDATE_TO_ATOMIC_HEAD")
    e.update(
        to="LEAST_AUTHORITY_LINEAGE_CAPABILITIES",
        after=(
            "SLEEP snapshots separate active-weight, eligible-life, immutable-birth, "
            "and equality-only CAS capabilities. Candidate evaluation alone may "
            "dereference candidate weights; promotion receives only candidate-root "
            "equality, typed verdict, and CAS equality. Rejection quarantines all "
            "candidate derivatives while retaining life evidence."
        ),
        rationale="Candidate content, life evidence, and transaction equality cannot be one dereferenceable object.",
    )
    e = _edge(doc, "SCIENTIFIC_EVALUATION_TO_REPORTING_ONLY")
    e.update({
        "edge_id": "EXAM_EXECUTOR_TO_TRUTH_SCORER",
        "from": "EXAM_MODEL_EXECUTOR",
        "to": "TRUTH_SCORER",
        "after": "The executor closes an immutable transcript before the scorer receives it; hidden truth never enters the executor epoch.",
        "rationale": "Generation and grading must be causally separated.",
    })
    e = _edge(doc, "REPETITION_STATE_TO_PARENT_CONTROL_ONLY")
    e.update(
        after=(
            "No semantic edge exists. Only the adaptive parent may read its own "
            "frozen-schema acquisition/relapse state; the fixed parent cannot. "
            "Auditors receive narrow taint or transaction receipts rather than "
            "repetition content. SLEEP receives only independently supported "
            "child-grounded life evidence."
        ),
        rationale="Repetition can guide adaptive waking parenting but cannot become a teacher-to-gradient or audit-to-release channel.",
    )
    doc["graph_delta"]["edges"].extend([
        {"operation":"add","edge_id":"TRUTH_SCORER_TO_REPORTER","from":"TRUTH_SCORER","to":"SCIENTIFIC_REPORTER","before":"","after":"Only frozen typed score records cross; transcripts, hidden truth, model state, and lineage capabilities do not.","rationale":"Aggregation must not become feedback."},
        {"operation":"add","edge_id":"FIXED_TABLE_CURSOR_TO_WAKE","from":"FIXED_PARENT_CONTROLLER","to":"ADAPTIVE_PARENT_DEVELOPMENT_ASSAY","before":"","after":"In the fixed arm only, immutable age-keyed lesson bytes enter current waking context from an external cursor; child state cannot alter selection, bytes, timing, or repetition.","rationale":"Repetition is a waking intervention, not SLEEP data."},
        {"operation":"add","edge_id":"CHILD_TRACE_TO_SUPPORT_RESOLVER","from":"EVIDENCE_SUPPORT_RESOLVER","to":"SLEEP_COMPILER","before":"","after":"Only support-resolved child-authored thought/action/outcome evidence crosses; parent bytes, DREAM, repetition, audit metadata and their counts/hashes/timing do not.","rationale":"The child must enact a lesson before it becomes experiential evidence."},
        {"operation":"add","edge_id":"SPLIT_AUDITS_TO_EXTERNAL_AUTHORITY","from":"SPLIT_AUDIT_AND_AUTHORITY","to":"RELEASE_CONTROLLER","before":"","after":"Narrow attestations plus separately authored exact human authorization enter an authority verifier; release consumes only its verdict and bound target roots.","rationale":"No internal evidence processor may manufacture permission."},
    ])

    l = _loop(doc, "SLEEP_COMPILE_WRITE_COMMIT")
    l.update(
        after=(
            "In a fresh SLEEP epoch, a model-free resolver emits eligible child life "
            "evidence. The writer reads only that evidence, immutable birth, prior "
            "active weights, frozen writer contract, and equality-only CAS token; "
            "it emits a staged candidate. Parent prose/audit, repetition state, "
            "DREAM, hidden truth, scientific products, and earlier candidates are "
            "unreadable."
        ),
        reads=["E4_READ_ELIGIBLE_CHILD_LIFE_EVIDENCE","E4_READ_IMMUTABLE_BIRTH_ARTIFACT","E4_DEREFERENCE_ACTIVE_WEIGHT_ARTIFACT","E4_READ_FROZEN_SLEEP_WRITER_CONTRACT","E4_BIND_EQUALITY_COMMITTED_CAS_TOKEN"],
        writes=["E4_WRITE_CANDIDATE_CLOSURE"],
        stop_condition="Source/support/taint/dose/provenance faults fail closed. One operational retry may use the identical snapshot; behavioral/preservation rejection never retries identical evidence. Later promotion changes only active weights; rejection preserves life and quarantines all candidate derivatives.",
    )
    l = _loop(doc, "PARENT_REPETITION_AND_FADE")
    l.update(
        after=(
            "Repeat one core lesson across varied relevant waking cases until the "
            "child independently restates and selectively enacts it. The fixed arm "
            "emits immutable bytes only at ages 1, 9, 17, and 25 and never adapts. "
            "The adaptive arm may use frozen public-child-history rules. Parent bytes "
            "remain waking-only; grounded child enactments can later become evidence."
        ),
        reads=["fixed arm: E2_READ_FIXED_LESSON_TABLE plus E2_READ_FIXED_SCHEDULE_CURSOR","adaptive arm: E2_READ_COMMITTED_CHILD_TRACE plus frozen policy","E2_READ_DEVELOPMENT_PUBLIC_OBSERVATION"],
        writes=["E2_WRITE_LIVE_PARENT_MESSAGE","E2_APPEND_PARENT_AUDIT_EVENT","adaptive arm only: E2_WRITE_ADAPTIVE_PARENT_HISTORY and E2_WRITE_ADAPTIVE_REPETITION_STATE"],
        stop_condition="Stop/label failure on copied words without selective enactment, irrelevant ritual, fixed-policy dependence on child/self-history, or any direct/transitive parent/repetition route into SLEEP.",
    )
    l = _loop(doc, "CANDIDATE_PRESERVATION_AND_PROMOTION")
    l.update(
        after=(
            "A fresh candidate evaluator alone dereferences prior and candidate "
            "weights against a frozen preservation panel and binds its typed verdict "
            "to the candidate root. A separate promotion invocation sees only root "
            "equality, verdict, and committed CAS equality and may change only the "
            "active-weight root."
        ),
        reads=["E5_DEREFERENCE_PRIOR_ACTIVE_WEIGHT_ARTIFACT","E5_DEREFERENCE_CANDIDATE_WEIGHT_ARTIFACT","E5_READ_FROZEN_PRESERVATION_PANEL","E5_BIND_CANDIDATE_ROOT"],
        writes=["E5_WRITE_CANDIDATE_PRESERVATION_EVIDENCE","E5_WRITE_PROMOTION_VERDICT","E5_WRITE_ACTIVE_WEIGHT_PROMOTION"],
        stop_condition="Root mismatch, stale CAS, candidate mutation, missing/rejected verdict, or undeclared capability fails closed without changing committed life or prior active weights.",
    )
    l = _loop(doc, "DISPOSABLE_SCIENTIFIC_EVALUATION")
    l.update(
        after=(
            "Create a fresh active-weight-only model executor for one public exam, "
            "close its transcript, destroy it, score mechanically against hidden "
            "truth, then report from frozen score records. No stage sees model plus "
            "truth, and no evaluation product returns to development or release."
        ),
        reads=["executor: E6_READ_EVALUATION_PUBLIC_OBSERVATION plus E6_DEREFERENCE_ACTIVE_WEIGHT_ARTIFACT","scorer: E6_READ_IMMUTABLE_EXAM_TRANSCRIPT plus E6_READ_HIDDEN_EVALUATION_TRUTH","reporter: E6_READ_FROZEN_SCIENTIFIC_SCORE_RECORDS"],
        writes=["E6_WRITE_IMMUTABLE_EXAM_TRANSCRIPT","E6_WRITE_SCIENTIFIC_SCORE_RECORD","E6_WRITE_SCIENTIFIC_REPORT"],
        stop_condition="Abort on executor truth/prior-product access, scorer model/lineage access, reporter feedback, stale executor, mutable transcript, or cross-epoch access.",
    )
    doc["loop_delta"]["loops"].append({
        "operation":"add","loop_id":"AUDIT_EXTERNAL_AUTHORITY_AND_RELEASE","before":"",
        "after":"Run blindness and lineage auditors on disjoint receipts. A new external human authorization names exact roots and scope. Authority verification sees only that artifact plus narrow attestations; release sees only its verdict and named target.",
        "trigger":"Only after prerequisites complete and a human separately authors exact authorization.",
        "reads":["blindness: E7_READ_DECLARED_DEPENDENCY_MANIFESTS plus E7_READ_TAINT_RECEIPTS","lineage: E7_READ_LINEAGE_TRANSACTION_RECEIPTS plus E7_READ_CANDIDATE_PRESERVATION_EVIDENCE","verifier: E8_READ_EXTERNAL_HUMAN_AUTHORIZATION plus E8_READ_NARROW_AUDIT_ATTESTATIONS","release: E8_READ_AUTHORITY_VERDICT plus E8_BIND_RELEASE_ARTIFACT_ROOTS"],
        "writes":["E7_WRITE_BLINDNESS_AUDIT_FINDING","E7_WRITE_LINEAGE_AUDIT_FINDING","E8_WRITE_AUTHORITY_VERDICT","E8_WRITE_RELEASE_RECEIPT"],
        "stop_condition":"No auditor may read scientific truth/report or author permission; missing, stale, mismatched, failed, or incomplete scope fails closed.",
        "rationale":"Evidence, safety audit, human judgment, and authority are distinct.",
    })

    stages = [
        "E1_BOOTSTRAP_DATA_BUILDER","E1_BIRTH_WRITER","E2_FIXED_PARENT_CONTROLLER","E2_ADAPTIVE_PARENT_CONTROLLER","E2_WAKE_CHILD","E3_DREAM_CONTEXT_BUILDER","E4_EVIDENCE_SUPPORT_RESOLVER","E4_SLEEP_COMPILER_WRITER","E5_CANDIDATE_PRESERVATION_EVALUATOR","E5_LINEAGE_PROMOTION_GATE","E6_EXAM_MODEL_EXECUTOR","E6_TRUTH_SCORER","E6_SCIENTIFIC_REPORTER","E7_BLINDNESS_AUDITOR","E7_LINEAGE_SAFETY_AUDITOR","E8_AUTHORITY_VERIFIER","E8_RELEASE_CONTROLLER",
    ]
    allowed = {
        "E1_READ_STATIC_BOOTSTRAP_SPEC":["E1_BOOTSTRAP_DATA_BUILDER"],
        "E1_WRITE_PAIRED_BOOTSTRAP_CORPUS":["E1_BOOTSTRAP_DATA_BUILDER"],
        "E1_READ_PAIRED_BOOTSTRAP_CORPUS":["E1_BIRTH_WRITER"],
        "E1_READ_FROZEN_M0":["E1_BIRTH_WRITER"],
        "E1_WRITE_IMMUTABLE_BIRTH_ARTIFACT":["E1_BIRTH_WRITER"],
        "E1_APPEND_BOOTSTRAP_AUDIT_RECEIPT":["E1_BIRTH_WRITER"],
        "E2_READ_FIXED_LESSON_TABLE":["E2_FIXED_PARENT_CONTROLLER"],
        "E2_READ_FIXED_SCHEDULE_CURSOR":["E2_FIXED_PARENT_CONTROLLER"],
        "E2_ADVANCE_FIXED_SCHEDULE_CURSOR":["E2_FIXED_PARENT_CONTROLLER"],
        "E2_WRITE_LIVE_PARENT_MESSAGE":["E2_FIXED_PARENT_CONTROLLER","E2_ADAPTIVE_PARENT_CONTROLLER"],
        "E2_APPEND_PARENT_AUDIT_EVENT":["E2_FIXED_PARENT_CONTROLLER","E2_ADAPTIVE_PARENT_CONTROLLER"],
        "E2_READ_DEVELOPMENT_PUBLIC_OBSERVATION":["E2_ADAPTIVE_PARENT_CONTROLLER","E2_WAKE_CHILD","E3_DREAM_CONTEXT_BUILDER","E4_EVIDENCE_SUPPORT_RESOLVER"],
        "E2_READ_COMMITTED_CHILD_TRACE":["E2_ADAPTIVE_PARENT_CONTROLLER","E3_DREAM_CONTEXT_BUILDER","E4_EVIDENCE_SUPPORT_RESOLVER"],
        "E2_READ_ADAPTIVE_PARENT_HISTORY":["E2_ADAPTIVE_PARENT_CONTROLLER"],
        "E2_READ_ADAPTIVE_REPETITION_STATE":["E2_ADAPTIVE_PARENT_CONTROLLER"],
        "E2_WRITE_ADAPTIVE_PARENT_HISTORY":["E2_ADAPTIVE_PARENT_CONTROLLER"],
        "E2_WRITE_ADAPTIVE_REPETITION_STATE":["E2_ADAPTIVE_PARENT_CONTROLLER"],
        "E2_READ_CURRENT_LIVE_PARENT_MESSAGE":["E2_WAKE_CHILD","E3_DREAM_CONTEXT_BUILDER"],
        "E2_DEREFERENCE_ACTIVE_WEIGHT_ARTIFACT":["E2_WAKE_CHILD","E3_DREAM_CONTEXT_BUILDER"],
        "E2_WRITE_CHILD_GROUNDED_TRACE":["E2_WAKE_CHILD"],
        "E3_READ_PRIOR_DREAM_CACHE":["E3_DREAM_CONTEXT_BUILDER","E2_WAKE_CHILD"],
        "E3_WRITE_DREAM_CACHE":["E3_DREAM_CONTEXT_BUILDER"],
        "E4_WRITE_ELIGIBLE_CHILD_LIFE_EVIDENCE":["E4_EVIDENCE_SUPPORT_RESOLVER"],
        "E4_READ_ELIGIBLE_CHILD_LIFE_EVIDENCE":["E4_SLEEP_COMPILER_WRITER"],
        "E4_READ_IMMUTABLE_BIRTH_ARTIFACT":["E4_SLEEP_COMPILER_WRITER"],
        "E4_DEREFERENCE_ACTIVE_WEIGHT_ARTIFACT":["E4_SLEEP_COMPILER_WRITER"],
        "E4_READ_FROZEN_SLEEP_WRITER_CONTRACT":["E4_SLEEP_COMPILER_WRITER"],
        "E4_BIND_EQUALITY_COMMITTED_CAS_TOKEN":["E4_SLEEP_COMPILER_WRITER","E5_LINEAGE_PROMOTION_GATE","E7_LINEAGE_SAFETY_AUDITOR"],
        "E4_WRITE_CANDIDATE_CLOSURE":["E4_SLEEP_COMPILER_WRITER"],
        "E5_DEREFERENCE_PRIOR_ACTIVE_WEIGHT_ARTIFACT":["E5_CANDIDATE_PRESERVATION_EVALUATOR"],
        "E5_DEREFERENCE_CANDIDATE_WEIGHT_ARTIFACT":["E5_CANDIDATE_PRESERVATION_EVALUATOR"],
        "E5_READ_FROZEN_PRESERVATION_PANEL":["E5_CANDIDATE_PRESERVATION_EVALUATOR"],
        "E5_BIND_CANDIDATE_ROOT":["E5_CANDIDATE_PRESERVATION_EVALUATOR","E5_LINEAGE_PROMOTION_GATE","E7_LINEAGE_SAFETY_AUDITOR"],
        "E5_WRITE_CANDIDATE_PRESERVATION_EVIDENCE":["E5_CANDIDATE_PRESERVATION_EVALUATOR"],
        "E5_WRITE_PROMOTION_VERDICT":["E5_CANDIDATE_PRESERVATION_EVALUATOR"],
        "E5_READ_PROMOTION_VERDICT":["E5_LINEAGE_PROMOTION_GATE","E7_LINEAGE_SAFETY_AUDITOR"],
        "E5_WRITE_ACTIVE_WEIGHT_PROMOTION":["E5_LINEAGE_PROMOTION_GATE"],
        "E6_READ_EVALUATION_PUBLIC_OBSERVATION":["E6_EXAM_MODEL_EXECUTOR"],
        "E6_DEREFERENCE_ACTIVE_WEIGHT_ARTIFACT":["E6_EXAM_MODEL_EXECUTOR"],
        "E6_WRITE_IMMUTABLE_EXAM_TRANSCRIPT":["E6_EXAM_MODEL_EXECUTOR"],
        "E6_READ_IMMUTABLE_EXAM_TRANSCRIPT":["E6_TRUTH_SCORER"],
        "E6_READ_HIDDEN_EVALUATION_TRUTH":["E6_TRUTH_SCORER"],
        "E6_WRITE_SCIENTIFIC_SCORE_RECORD":["E6_TRUTH_SCORER"],
        "E6_READ_FROZEN_SCIENTIFIC_SCORE_RECORDS":["E6_SCIENTIFIC_REPORTER"],
        "E6_WRITE_SCIENTIFIC_REPORT":["E6_SCIENTIFIC_REPORTER"],
        "E7_READ_DECLARED_DEPENDENCY_MANIFESTS":["E7_BLINDNESS_AUDITOR"],
        "E7_READ_TAINT_RECEIPTS":["E7_BLINDNESS_AUDITOR"],
        "E7_WRITE_BLINDNESS_AUDIT_FINDING":["E7_BLINDNESS_AUDITOR"],
        "E7_READ_LINEAGE_TRANSACTION_RECEIPTS":["E7_LINEAGE_SAFETY_AUDITOR"],
        "E7_READ_CANDIDATE_PRESERVATION_EVIDENCE":["E7_LINEAGE_SAFETY_AUDITOR"],
        "E7_WRITE_LINEAGE_AUDIT_FINDING":["E7_LINEAGE_SAFETY_AUDITOR"],
        "E8_READ_EXTERNAL_HUMAN_AUTHORIZATION":["E8_AUTHORITY_VERIFIER"],
        "E8_READ_NARROW_AUDIT_ATTESTATIONS":["E8_AUTHORITY_VERIFIER"],
        "E8_BIND_RELEASE_ARTIFACT_ROOTS":["E8_AUTHORITY_VERIFIER","E8_RELEASE_CONTROLLER"],
        "E8_WRITE_AUTHORITY_VERDICT":["E8_AUTHORITY_VERIFIER"],
        "E8_READ_AUTHORITY_VERDICT":["E8_RELEASE_CONTROLLER"],
        "E8_TRANSFER_OPAQUE_RELEASE_TARGET_ARTIFACT":["E8_RELEASE_CONTROLLER"],
        "E8_WRITE_RELEASE_RECEIPT":["E8_RELEASE_CONTROLLER"],
    }
    cells = []
    for info, permitted in allowed.items():
        for stage in stages:
            ok = stage in permitted
            cells.append({
                "information_id": info,
                "stage_id": stage,
                "visibility": "visible" if ok else "forbidden",
                "reason": (
                    f"Exact directional capability {info} is allowed only for this named epoch invocation; it exposes no other content or side channel."
                    if ok else
                    "No capability exists for this stage/epoch; direct, transitive, stale-handle, count, identifier, hash, timing, cache, error, and cross-capability access are forbidden."
                ),
            })
    doc["visibility_matrix"] = {"information_items": list(allowed), "stages": stages, "cells": cells}

    replacements = {
        "V2_ES01_EXACT_AUTHORITY":("V5_ES01_EXACT_EXTERNAL_AUTHORITY_AND_SCOPE","external authorization, narrow attestations, roots, action registry, and scope; attack implied/model/auditor authority"),
        "V4_ES02_EVIDENCE_SUPPORT_AND_REPETITION_FIREWALL":("V5_ES02_DIRECTIONAL_EVIDENCE_AND_REPETITION_CAPABILITIES","direct/transitive parent and repetition taint through bytes, counts, IDs, hashes, order, timing, caches, errors, and stale handles"),
        "V4_ES03_EXACT_WRITER_ROUTE_MASK_DOSE_AND_TAINT":("V5_ES03_EXACT_WRITER_ROUTE_CAPABILITY_MASK_DOSE_AND_TAINT","one writer route plus exact response mask, supervised-token dose, epoch and capability inputs"),
        "V4_ES06_TYPED_LINEAGE_EVALUATION_AND_RETRY_FAULTS":("V5_ES06_DIRECTIONAL_LINEAGE_EVALUATION_AND_RETRY_FAULTS","fault every capability direction/epoch, split evaluation stage, candidate root, CAS, retry and quarantine path"),
        "V2_ES08_INCREMENTAL_TARGET_BLINDNESS":("V5_ES08_SPLIT_AUDITOR_INCREMENTAL_TARGET_BLINDNESS","blindness auditor restricted to manifests/taint receipts and unable to author authority"),
        "V2_ES09_STANDARDIZED_ADVICE_RECEPTIVITY":("V5_ES09_SPLIT_EXECUTOR_STANDARDIZED_ADVICE_RECEPTIVITY","fresh executor, closed transcript, model-free truth scoring and reporting with no feedback"),
        "V4_ES10_FIXED_CURRICULUM_SLEEP_ACCELERATION":("V5_ES10_CURSOR_FIXED_CURRICULUM_SLEEP_ACCELERATION","cursor-only immutable lessons plus split disposable exams"),
        "V2_ES11_ADAPTIVE_PACKAGE_ACCELERATION":("V5_ES11_SPLIT_EVALUATION_ADAPTIVE_PACKAGE_ACCELERATION","adaptive total-package estimand with split exams and complete parent effort log"),
        "V4_ES12_REPETITION_CONTROL_AND_ENACTMENT":("V5_ES12_CURSOR_REPETITION_CONTROL_AND_ENACTMENT","fixed cursor, opposing-history byte identity, uncued selective enactment and no SLEEP route"),
        "V2_ES13_STORAGE_EXTRACTION_USE_AND_CONTROLS":("V5_ES13_SPLIT_EVALUATION_STORAGE_EXTRACTION_USE_CONTROLS","storage/extraction/native-use separation through split exams and shuffled controls"),
        "V2_ES14_PERSONAL_REPLAY_DEPENDENCE":("V5_ES14_FIREWALLED_PERSONAL_REPLAY_DEPENDENCE","closure- and dose-matched replay/filler candidates evaluated without lineage feedback"),
        "V2_ES16_CADENCE_TOTAL_AND_STANDARDIZED_LEDGER":("V5_ES16_FIREWALLED_CADENCE_TOTAL_AND_STANDARDIZED_LEDGER","equal total opportunity plus split checkpoint exams that cannot teach/select later life"),
        "V4_ES19_COMPLETE_VISIBILITY_AND_EVALUATION_NONINTERFERENCE":("V5_ES19_COMPLETE_DIRECTIONAL_LIFECYCLE_AND_NONINTERFERENCE","complete stage x capability x operation x epoch product and every direct/transitive covert-channel attack"),
        "V4_ES20_CLASSIFIED_REJECTION_PRESERVES_LIFE":("V5_ES20_CAPABILITY_CLASSIFIED_REJECTION_PRESERVES_LIFE","separated root/CAS/candidate capabilities, concurrent commits and exact failure classes"),
        "V2_ES18_FRESH_REVIEW_AND_GPU_GATE":("V5_ES18_FRESH_REVIEW_EXTERNAL_AUTHORITY_AND_GPU_GATE","fresh reviewer and advocate followed only by separate exact external human run authority"),
        "V4_ES21_FIRST_AFFECTED_EXECUTION_GATE_ORDER":("V5_ES21_EXHAUSTIVE_FIRST_AFFECTED_ACTION_GATE","every CPU/GPU model, tokenizer, data, writer, candidate, exam, resource and release dispatcher with missing/failed/stale/valid receipts"),
    }
    pre_impl = {"V5_ES01_EXACT_EXTERNAL_AUTHORITY_AND_SCOPE","V5_ES02_DIRECTIONAL_EVIDENCE_AND_REPETITION_CAPABILITIES","V5_ES03_EXACT_WRITER_ROUTE_CAPABILITY_MASK_DOSE_AND_TAINT","V5_ES06_DIRECTIONAL_LINEAGE_EVALUATION_AND_RETRY_FAULTS","V5_ES08_SPLIT_AUDITOR_INCREMENTAL_TARGET_BLINDNESS","V5_ES12_CURSOR_REPETITION_CONTROL_AND_ENACTMENT","V5_ES19_COMPLETE_DIRECTIONAL_LIFECYCLE_AND_NONINTERFERENCE","V5_ES20_CAPABILITY_CLASSIFIED_REJECTION_PRESERVES_LIFE","V5_ES21_EXHAUSTIVE_FIRST_AFFECTED_ACTION_GATE"}
    for test in doc["acceptance_tests"]:
        if test["test_id"] not in replacements:
            continue
        old = test["test_id"]
        new, hardening = replacements[old]
        test["test_id"] = new
        test["setup"] += f" V5 hardening: exercise {hardening}."
        test["expected"] += " Every allowed operation is one-way and epoch-scoped; every undeclared or stale path fails with constant-shape behavior."
        test["falsifies"] += " Also falsified by any protected-state side channel, cross-epoch reuse, evaluation feedback, or internally manufactured authority."
        test["evidence_artifact"] = f"research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v5/evidence/{new.lower()}.json"
        if new in pre_impl:
            test["required_before"] = "implementation"

    doc["human_boundary"] = {
        "required": True,
        "decision_owner": "Rohin Ghosh",
        "decision_question": "After fresh independent interpretation, critique, and consensus, does Rohin ratify these exact v5 bytes and only a separately enumerated scope, while every model, tokenizer, data, adapter, GPU, scientific, claim, publication, and release action remains separately gated?",
        "forbidden_before_approval": ["implementation","model_execution","tokenizer_execution","bootstrap_or_benchmark_generation","adapter_or_checkpoint_work","gpu_or_resource_use","external_scientific_execution","scientific_claim","publication_or_push","release"],
    }
    return doc


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2) + "\n")
