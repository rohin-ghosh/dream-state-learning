"""Render the v7 successor proposal from the adjudicated v6 rework record.

Proposal construction only.  This module requires the independently prepared
v7 scientific core, capability registry, and action-prerequisite DAG.  It does
not implement the proposal or execute models, tokenizers, data generation,
adapters, GPUs, scientific analysis, claims, publication, or release.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
V6_DIR = ROOT / "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v6"
OUT = Path(__file__).with_name("change.json")
SCIENCE_PATH = V6_DIR / "v7_scientific_core.json"
REGISTRY_PATH = V6_DIR / "v7_capability_registry.json"
DAG_PATH = V6_DIR / "v7_action_prerequisite_dag.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"required independent V7 input is absent: {path}")
    return json.loads(path.read_text())


def by_id(items: list[dict], key: str, value: str) -> dict:
    return next(item for item in items if item[key] == value)


def upsert(items: list[dict], key: str, value: str, body: dict) -> None:
    matches = [i for i, item in enumerate(items) if item.get(key) == value]
    if len(matches) > 1:
        raise ValueError(f"duplicate {key}: {value}")
    if matches:
        items[matches[0]] = body
    else:
        items.append(body)


def node(node_id: str, before: str, after: str, rationale: str,
         operation: str = "modify") -> dict:
    return dict(operation=operation, node_id=node_id, before=before,
                after=after, rationale=rationale)


def edge(edge_id: str, source: str, target: str, before: str, after: str,
         rationale: str, operation: str = "modify") -> dict:
    return dict(operation=operation, edge_id=edge_id, **{"from": source}, to=target,
                before=before, after=after, rationale=rationale)


def principal(registry: dict, fragment: str) -> str:
    hits = [p for p in registry["registered_principals"] if fragment in p]
    if len(hits) != 1:
        raise ValueError(f"expected one principal containing {fragment!r}; got {hits}")
    return hits[0]


def principal_caps(registry: dict, principal_id: str,
                   *, reads: bool) -> list[str]:
    read_ops = {"READ", "DEREFERENCE", "BIND_EQUALITY"}
    caps = []
    for cap in registry["capabilities"]:
        if cap["allowed_consumers"] != [principal_id]:
            continue
        is_read = cap["operation"] in read_ops
        if is_read == reads:
            caps.append(cap["capability_id"])
    return caps


def build_visibility(registry: dict) -> dict:
    stages = list(registry["registered_principals"])
    information_items = [c["capability_id"] for c in registry["capabilities"]]
    cells = []
    for cap in registry["capabilities"]:
        consumers = cap["allowed_consumers"]
        if len(consumers) != 1:
            raise ValueError(f"capability is not single-consumer: {cap['capability_id']}")
        consumer = consumers[0]
        for stage in stages:
            visible = stage == consumer
            cells.append({
                "information_id": cap["capability_id"],
                "stage_id": stage,
                "visibility": "visible" if visible else "forbidden",
                "reason": (
                    f"Registry grants {cap['operation']} over exactly "
                    f"{cap['artifact_class']} to {consumer} for {cap['epoch']} "
                    "under one invocation-scoped handle."
                    if visible else
                    "No registry handle exists for this principal; direct, derived, "
                    "copied, stale, cross-epoch, ambient-path, count, hash, identifier, "
                    "ordering, timing, cache, and error-shape access fail closed."
                ),
            })
    return {"information_items": information_items, "stages": stages, "cells": cells}


TEST_SPECS = {
    "V7_ES01_EXACT_EXTERNAL_AUTHORITY_AND_CLASS_BOUND_RELEASE":
        ("Exercise exact nine-field authorization, concrete wrapper/payload class-root equality, opaque transfer, nonce, expiry, idempotency, and every substitution.",
         "Only one exact external authorization plus valid producer-closed attestations permits the tuple-bound transfer."),
    "V7_ES02_EPOCH_ATTENUATED_AUTHORSHIP_GROUNDING_AND_REPETITION":
        ("Exercise child authorship, temporal order, same-life public grounding, resolver-root binding, meaning preservation, parent/repetition taint, stale handles, and undecidable clauses.",
         "Only mechanically established child-authored grounded clauses become eligible; parent/repetition information never crosses into SLEEP."),
    "V7_ES03_FRESH_FROM_BIRTH_CONSTRUCTOR_MASK_DOSE_AND_TAINT":
        ("Hold birth, zero-delta initializer, cumulative evidence, contracts, and seed fixed while mutating prior head and faulting mask, dose, taint, truncation, and serialization.",
         "Constructor inputs, branches, errors, gradients, bytes, and trace remain identical; only later staging status may differ."),
    "V7_ES04_ZERO_EFFECTIVE_DELTA_INITIALIZER":
        ("Materialize the declared initializer across seeds, dtypes, devices, serializers, reloads, and merge boundaries.",
         "The personal adapter's effective delta is exactly zero before every fresh-from-birth write."),
    "V7_ES05_BIRTH_MERGE_CONTRACT_AND_CONTENT_IDENTITY":
        ("Reconstruct D and T births from the exact M0, paired corpus, writer, mask, tokenizer, merge, dtype, serializer, toolchain, seed, and truncation roots.",
         "Births are reproducible immutable artifacts and personal SLEEP starts with empty personal adapter state."),
    "V7_ES06_ATOMIC_LINEAGE_PROMOTION_AND_RETRY_FAULTS":
        ("Inject concurrent, crash, retry, replay, stale-head, verdict-substitution, candidate-substitution, nonce, namespace, and idempotency faults into PROMOTE_CAS_ATOMIC.",
         "Promotion changes the active root and emits its bound receipt in one transaction, or changes nothing."),
    "V7_ES07_BOOTSTRAP_CONTROL_TARGET_BLINDNESS_AND_SEMANTIC_AUDIT":
        ("Audit D/T pairs for shared state, action, outcome, admission, position, dose, opportunity, exact one-computation difference, target blindness, structural overlap, and M0 damage.",
         "T differs from D only by the declared feedback-to-action computation; no downstream-derived or policy-isomorphic target content exists."),
    "V7_ES08_PRODUCER_CLOSED_AUDIT_TARGET_BLINDNESS":
        ("Trace real manifest, taint, lineage, finding, attestation, verdict, wrapper, and release producers while attacking target leakage and auditor-created authority.",
         "Audits are producer-closed, detailed findings remain quarantined, and narrow attestations never manufacture permission."),
    "V7_ES09_SPLIT_EXECUTOR_STANDARDIZED_ADVICE_RECEPTIVITY":
        ("Randomize independent disposable D/T clones at birth under correct, none, irrelevant, and wrong process advice before personal SLEEP; score through the split executor.",
         "Any Delta_R claim uses powered root-level correct-versus-none evidence with irrelevant/wrong safety controls and M0 diagnostic only."),
    "V7_ES10_FIXED_CURRICULUM_DEVELOPMENTAL_AUC_INTERACTION":
        ("Run the primary root-randomized D/T by absent/fixed factorial at ages 0,8,16,24,32 under identical fixed bytes and matched solo opportunity.",
         "Delta_F is reported only as an entry-normalized developmental AUC interaction or total-regime performance-curve acceleration."),
    "V7_ES11_ADAPTIVE_PACKAGE_DEVELOPMENTAL_AUC_INTERACTION":
        ("Separately randomize D/T by absent/adaptive roots under the frozen adaptive policy, matched nonparent opportunity, and full effort/information receipts.",
         "Delta_E is a separately reported entry-normalized developmental AUC interaction for the total adaptive package, never mediation."),
    "V7_ES12_CURSOR_REPETITION_CONTROL_AND_ENACTMENT":
        ("At ages 1,9,17,25 compare fixed-parent bytes under opposing histories, close/reissue handles, and distinguish copied wording from uncued selective enactment.",
         "Fixed parenting is exogenous; repetition stays in THINK; no repetition-benefit claim exists without its own randomized factor."),
    "V7_ES13_CHILD_AUTHORED_STORAGE_EXTRACTION_NATIVE_USE":
        ("Separate source fit, held-out cue extraction, native use on fresh homologous tasks, and interface preservation with adapter-off, deranged, wrong-life, and provenance controls.",
         "Training loss or verbatim recall is insufficient; usable experience requires held-out extraction and native action without retrieval or interface harm."),
    "V7_ES14_FRESH_FROM_BIRTH_REPLAY_DEPENDENCE":
        ("Construct closure-, coverage-, and dose-matched replay versus filler candidates from immutable birth with no prior-candidate evidence.",
         "Any difference is attributable to the registered replay treatment, not omitted life, continuation, or changed opportunity."),
    "V7_ES15_RANK_BY_EXPOSURE_ONLY":
        ("Compare ranks under the frozen coverage/dose contract with identical eligible propositions, supervised-token and optimizer opportunities, and prospective capacity ceilings.",
         "Rank is interpreted only as capacity by exposure; overflow stops before writing and follows frozen missingness."),
    "V7_ES16_FRESH_FROM_BIRTH_CADENCE_TOTAL_PACKAGE":
        ("Compare preregistered K4/K1 lives with equal total opportunity, cumulative fresh-from-birth candidates, disposable exams, and standardized terminal rewrites.",
         "Cadence is a randomized total-package contrast; standardized-ledger contrasts remain descriptive."),
    "V7_ES17_PREGENERATION_STATISTICS_RECEIPTS_AND_REPORT_LABELS":
        ("Before generation freeze assignment, power, endpoints, intervals, multiplicity, missingness, safety, stopping, spend order, analysis code, labels, and exact action receipts.",
         "Tasks, ages, clones, and within-root seeds are not independent; forbidden intrinsic-learning-rate labels fail closed."),
    "V7_ES19_PRODUCER_CLOSED_EPOCH_CAPABILITY_NONINTERFERENCE":
        ("Validate the complete registry product, all bridges, producers, lifetimes, schemas, constant-shape failures, ambient denial, matched opportunity, resolver, reporter, and split-evaluation isolation.",
         "Every information flow has one producer, one consumer invocation, one epoch, and no covert or stale alternative."),
    "V7_ES20_POSTCLOSURE_STAGING_ATOMIC_CAS_AND_LIFE_PRESERVATION":
        ("Fault constructor closure, sealed-descriptor staging, evaluator binding, and atomic promotion while checking life retention and derivative quarantine.",
         "Prior-head mutation cannot alter candidate bytes; rejection or atomic-CAS failure preserves committed life and the prior active child."),
    "V7_ES18_FRESH_REVIEW_AND_SEPARATE_TERMINAL_AUTHORITIES":
        ("Require fresh implementation review and separate author advocate, then independently bind GPU, external science, claim, publication, push, and release scopes.",
         "No review, scientific evidence, or earlier authorization implies any terminal authority."),
    "V7_ES21_PRODUCER_CLOSED_NONCIRCULAR_ACTION_DAG":
        ("Topologically validate every action and prerequisite; bind exact G0 registry, DAG, parser, issuer, bridge, validator, gate, fake inputs, faults, manifests, roots, scope, nonce, and expiry.",
         "G0 is model-free and exact-byte bound; no protected action produces its own prerequisite and every missing or substituted path fails closed."),
}


def action_id(action: dict) -> str:
    for key in ("action_id", "id"):
        if key in action:
            return action[key]
    raise ValueError(f"action lacks ID: {action}")


def phase_rows(test_id: str, science: dict, dag: dict) -> list[dict]:
    """Bind each test phase to exact producer and guarded-action IDs in the DAG.

    The systems input owns the concrete mapping.  The builder accepts either a
    dict or list representation but refuses to invent missing phase receipts.
    """
    mappings = dag.get("test_phase_receipt_mappings") or dag.get("test_phase_receipts")
    if mappings is None:
        raise ValueError("V7 DAG lacks test_phase_receipt_mappings")
    if isinstance(mappings, dict):
        rows = mappings.get(test_id)
    else:
        rows = [r for r in mappings if r.get("test_id") == test_id]
    if not rows:
        raise ValueError(f"V7 DAG lacks phase receipt mapping for {test_id}")
    if isinstance(rows, dict):
        rows = list(rows.values())
    phase_order = [p["phase_id"] for p in science[
        "acceptance_test_and_claim_receipt_contract"]["ordered_phases"]]
    out = []
    seen = set()
    for row in rows:
        phase_id = row["phase_id"]
        if phase_id not in phase_order or phase_id in seen:
            raise ValueError(f"bad or duplicate phase {phase_id} for {test_id}")
        seen.add(phase_id)
        producer = row.get("producer_action_id")
        downstream = row.get("exact_downstream_action_ids") or row.get("guarded_action_ids")
        receipt = row.get("typed_pass_receipt") or row.get("receipt_type")
        if not producer or not downstream or not receipt:
            raise ValueError(f"incomplete phase mapping for {test_id}/{phase_id}")
        out.append({
            "phase_id": phase_id,
            "producer_action_id": producer,
            "typed_pass_receipt": receipt,
            "exact_downstream_action_ids": downstream,
            "required_receipt_bindings": science[
                "acceptance_test_and_claim_receipt_contract"][
                    "typed_phase_receipt_required_bindings"],
        })
    return sorted(out, key=lambda r: phase_order.index(r["phase_id"]))


def acceptance_test(test_id: str, science: dict, dag: dict) -> dict:
    """Render a schema-valid test while keeping the exact phase map in the DAG.

    The repository's architecture-change schema deliberately exposes only one
    coarse ``required_before`` field.  V7's exact constructible phase ordering
    therefore remains machine-readable in the bound action DAG; the proposal
    records that exact mapping in its setup without extending or weakening the
    shared schema.
    """
    rows = phase_rows(test_id, science, dag)
    phase_rank = {
        "STATIC_SCHEMA": 0,
        "G0_FAKE_RUNTIME": 0,
        "G1_IMPLEMENTATION_REVIEW": 1,
        "G2_CPU_DOMAIN": 2,
        "G3_GPU_SCIENCE": 3,
        "G4_CLAIM": 3,
    }
    required_before = [
        "implementation", "model_execution", "gpu_run", "scientific_claim"
    ][min(phase_rank[row["phase_id"]] for row in rows)]
    exact_map = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return {
        "test_id": test_id,
        "kind": "invariant",
        "setup": f"{TEST_SPECS[test_id][0]} Exact phase map: {exact_map}",
        "expected": TEST_SPECS[test_id][1],
        "falsifies": (
            "Any missing producer, prerequisite, exact root, phase receipt, "
            "action binding, scope, expiry/replay rule, child-grounding invariant, "
            "atomicity invariant, or claim-specific powered evidence falsifies "
            "the applicable contract."
        ),
        "evidence_artifact": (
            "research_loop/changes/"
            "chg_20260909_extractable_sleep_bootstrap_v7/evidence/"
            f"{test_id.lower()}.json"
        ),
        "required_before": required_before,
    }


def replace_loop(doc: dict, loop_id: str, after: str, trigger: str,
                 principals: list[str], registry: dict, stop: str,
                 rationale: str) -> None:
    reads, writes = [], []
    for p in principals:
        reads.extend(principal_caps(registry, p, reads=True))
        writes.extend(principal_caps(registry, p, reads=False))
    loop = by_id(doc["loop_delta"]["loops"], "loop_id", loop_id)
    loop.update(after=after, trigger=trigger, reads=reads, writes=writes,
                stop_condition=stop, rationale=rationale)


def build() -> dict:
    doc = copy.deepcopy(load(V6_DIR / "change.json"))
    science = load(SCIENCE_PATH)
    registry = load(REGISTRY_PATH)
    dag = load(DAG_PATH)

    expected_sources = {b["sha256"] for b in science["source_bindings"]}
    for name in ("change.json", "interpretation_science.json",
                 "interpretation_systems.json", "critique.json", "consensus.json",
                 "v7_blocker_resolution.md"):
        if sha(V6_DIR / name) not in expected_sources:
            raise ValueError(f"scientific core does not bind exact V6 source: {name}")
    if science["self_audit"]["status"] != "pass":
        raise ValueError("scientific-core self-audit is not pass")

    doc.update(
        change_id="chg_20260909_extractable_sleep_bootstrap_v7",
        title="Extractable SLEEP and teachability bootstrap v7",
        summary=(
            "Preserve exactly THINK, DREAM, and SLEEP. A one-time target-blind "
            "T-versus-D birth bootstrap may prepare the child to use later "
            "parenting; repetition stays in waking THINK. Personal SLEEP resolves "
            "only mechanically established child-authored grounded propositions, "
            "constructs a fresh-from-birth candidate under finite cumulative "
            "coverage and dose, closes it before staging, and promotes it only by "
            "one atomic full-head compare-and-swap."
        ),
        system_thesis=(
            "THINK is the continuing waking thought-action-public-outcome stream. "
            "DREAM only manages disposable waking context. SLEEP re-expresses and "
            "writes grounded propositions the child already authored into its "
            "personal LoRA. Parenting and repetition can affect SLEEP only by "
            "changing what the child itself later thinks, does, and grounds in the world."
        ),
    )

    additions = [
        ("change.json", "Exact v6 proposal returned for rework."),
        ("interpretation_science.json", "Fresh v6 scientific interpretation."),
        ("interpretation_systems.json", "Fresh v6 systems interpretation."),
        ("critique.json", "V6 adversarial cross-critique."),
        ("consensus.json", "V6 adjudicated rework decision and blocker dispositions."),
        ("v7_blocker_resolution.md", "Exact successor resolution for every v6 blocker."),
        ("v7_scientific_core.json", "Independent exact V7 scientific core."),
        ("v7_capability_registry.json", "Mechanically validated exact V7 capability registry."),
        ("v7_action_prerequisite_dag.json", "Mechanically validated exact V7 noncircular action DAG."),
    ]
    existing = {e["path"] for e in doc["context_files"]}
    for name, purpose in additions:
        path = V6_DIR / name
        rel = str(path.relative_to(ROOT))
        if rel not in existing:
            doc["context_files"].append({"path": rel, "sha256": sha(path),
                                         "purpose": purpose})

    nodes = doc["graph_delta"]["nodes"]
    replacements = [
        node("SLEEP_COMPILER", "V6 did not give the resolver its complete frozen decision contract.",
             "SLEEP selects, orders, deduplicates, contrasts, replays, paraphrases, and renders only clauses mechanically admitted under the exact support and coverage-dose contracts; it never invents missing child semantics.",
             "Compilation enriches the child's experience without becoming a thinker."),
        node("CHILD_LORA_WRITER", "V6 combined candidate construction with preclosure snapshot binding.",
             "E4_CANDIDATE_CONSTRUCTOR receives only immutable birth, a fresh zero-effective-delta initializer, the full cumulative eligible child corpus, frozen writer/support/coverage-dose contracts, and the bound seed; it seals candidate bytes and construction trace without active-head, CAS, verdict, evaluation, parent, repetition, DREAM, science, audit, authority, or release access.",
             "Candidate construction is a pure reproducible function of birth plus admitted life."),
        node("CANDIDATE_STAGER", "No separately closed postconstruction staging principal existed.",
             "Only after candidate closure, E4_CANDIDATE_STAGER receives a non-dereferenceable sealed descriptor and equality-only committed-snapshot handle. It may stage or reject the already closed candidate but cannot read, alter, or reconstruct candidate bytes.",
             "Prior-head mutation can change only staging status, never candidate construction.", "add"),
        node("EVIDENCE_SUPPORT_RESOLVER", "V6 left semantic support authority ambient.",
             "A model-free resolver consumes the committed child trace, matching public observation, and exact FROZEN_SUPPORT_RESOLVER_CONTRACT. The contract fully defines authorship, commit identity, temporal order, same-life grounding, semantic dimensions, bidirectional meaning preservation, clause thresholds, disputes, missing evidence, and undecidable rejection. It cannot infer a missing conclusion.",
             "Eligibility becomes constructible, content-addressed, and fail closed."),
        node("MATCHED_SOLO_RESOURCE_OPPORTUNITY_CONTRACT", "Matched solo opportunity was prose rather than an action prerequisite.",
             "FROZEN_MATCHED_SOLO_RESOURCE_OPPORTUNITY_CONTRACT and R_MATCHED_SOLO_RESOURCE_OPPORTUNITY_FROZEN equality-bind arm/root identities, exposure/order, parent and nonparent opportunities, tools, affordances, generated tokens, actions, wall time, retries, calls, CPU/GPU allocation, initialized optimizer/write opportunities, and every covered action.",
             "Resource or opportunity inequality stops the affected generation or execution before it begins.", "add"),
        node("CUMULATIVE_COVERAGE_DOSE_CONTRACT", "Full coverage and finite matched dose could conflict silently.",
             "FROZEN_CUMULATIVE_COVERAGE_DOSE_CONTRACT fixes the eligible closure, deterministic order, at least one loss-bearing inclusion per proposition, meaning-preserving render rules, mask, tokenizer, truncation, batches, updates, optimizer, rank, exposure accounting, equality rules, finite ceilings, missingness, and stopping. Overflow stops before a writer call.",
             "The life may be capacity-limited, but evidence may never be silently omitted or budgets increased post hoc.", "add"),
        node("LINEAGE_PROMOTION_GATE", "V6 used equality followed by a separate generic weight write.",
             "The lineage store exposes one PROMOTE_CAS_ATOMIC operation binding expected complete head, staged candidate, preservation verdict, replacement root, life/transaction namespace, nonce, and one-shot idempotency. Success changes the active root and emits its receipt in one linearizable transaction; failure changes nothing.",
             "There is no check-then-write race."),
        node("SCIENTIFIC_REPORTER", "V6 reporter assignment and labels were not producer-closed.",
             "The reporter reads frozen score records plus a separately delivered FROZEN_SCIENTIFIC_ANALYSIS_PACKET binding assignment, arms, age, endpoint, estimand, missingness, safety, multiplicity, analysis code, and allowed labels; it receives no truth, transcript, model, feedback, or authority.",
             "Reports cannot invent assignments, analyses, intrinsic-learning-rate labels, or development feedback."),
        node("RELEASE_CONTROLLER", "V6 did not bind the wrapper's concrete artifact class and underlying root through the transfer.",
             "Release is a one-shot TRANSFER_OPAQUE over a sealed RELEASE_TARGET_ARTIFACT wrapper that equality-binds the complete nine-field tuple to its concrete payload class and root. It consumes a separate exact external authorization and producer-closed narrow attestations.",
             "Every wrapper, class, root, destination, protocol, scope, nonce, expiry, or idempotency substitution fails closed."),
        node("FIRST_AFFECTED_ACTION_REGISTRY", "V6 test ordering and G0 root binding were incomplete.",
             f"The exact DAG {sha(DAG_PATH)} gates {len(dag['actions'])} actions in constructible STATIC_SCHEMA, G0_FAKE_RUNTIME, G1_IMPLEMENTATION_REVIEW, G2_CPU_DOMAIN, G3_GPU_SCIENCE, and G4_CLAIM order. Exact G0 authorization binds registry, DAG, parser, issuer, bridge, validator, gate, fake fixtures/dispatchers, fault fixtures, path/scope manifests, expected outputs, action, scope, nonce, and expiry.",
             "No dynamic test precedes its implementation and no protected action produces its own prerequisite."),
        node("DIRECTIONAL_CAPABILITY_REGISTRY", "V6 lacked the new resolver, stager, analysis, opportunity, and atomic-promotion capabilities.",
             f"The exact registry {sha(REGISTRY_PATH)} defines {len(registry['capabilities'])} single-consumer capabilities, {len(registry['artifact_classes'])} artifact classes, {len(registry['epoch_bridges'])} explicit bridges, PROMOTE_CAS_ATOMIC, exact producers/lifetimes/failures, and the complete release tuple. The full visibility matrix is generated from these bytes.",
             "All repaired flows are enumerable; ambient and cross-epoch access remains impossible."),
    ]
    for item in replacements:
        upsert(nodes, "node_id", item["node_id"], item)

    edges = doc["graph_delta"]["edges"]
    edge_replacements = [
        edge("PARENT_TO_CHILD_TO_SLEEP", "FIXED_PARENT_CONTROLLER", "SLEEP_COMPILER", "Parent influence could be mistaken for writer input.",
             "There is no direct edge: parent/repetition -> waking context -> child thought -> child action -> public outcome -> committed child trace -> independent eligibility -> later SLEEP. All parent/repetition bytes and side channels are forbidden from evidence, compilation, dose, candidates, and gradients.",
             "Repetition remains parenting in THINK, never disguised post-training."),
        edge("CHILD_TRACE_TO_SUPPORT_RESOLVER", "CANONICAL_EXPERIENCE_INDEX", "EVIDENCE_SUPPORT_RESOLVER", "Support decisions lacked an exact resolver-contract root.",
             "The resolver admits a clause only from exact child proposition IDs, public support IDs, life/commit roots, temporal classification, semantic scope, threshold, and the matching FROZEN_SUPPORT_RESOLVER_CONTRACT root; missing or undecidable support is rejection.",
             "The compiler cannot backfill rationale from outcomes."),
        edge("CANDIDATE_CONSTRUCTOR_TO_POSTCLOSURE_STAGER", "CHILD_LORA_WRITER", "CANDIDATE_STAGER", "V6 exposed snapshot equality before candidate closure.",
             "A sealed-candidate bridge transfers only a non-dereferenceable candidate descriptor after candidate bytes and construction trace close; only then does the stager receive an equality-only head snapshot.",
             "Candidate bytes and trace are invariant to prior-head mutation.", "add"),
        edge("STAGED_CANDIDATE_TO_ATOMIC_PROMOTION", "CANDIDATE_STAGER", "LINEAGE_PROMOTION_GATE", "V6 checked equality and then wrote active weights separately.",
             "After independent preservation evaluation, one store-mediated PROMOTE_CAS_ATOMIC request binds expected full head, staged candidate, verdict, replacement root, namespace, nonce, and idempotency.",
             "Promotion is linearizable and retry safe.", "add"),
        edge("MATCHED_SOLO_RECEIPT_TO_COVERED_ACTIONS", "MATCHED_SOLO_RESOURCE_OPPORTUNITY_CONTRACT", "FIRST_AFFECTED_ACTION_REGISTRY", "Opportunity equality was not executable.",
             "Every fixed/adaptive generation, parent, wake, writer, exam, CPU, GPU, and external-science action requires the exact matched-solo receipt naming that action and its equal resources/opportunities.",
             "Substitution or inequality fails before the first affected action.", "add"),
        edge("ANALYSIS_PACKET_TO_REPORTER", "FIRST_AFFECTED_ACTION_REGISTRY", "SCIENTIFIC_REPORTER", "Reporter labels and assignments were ambient.",
             "A separate READ capability supplies the exact immutable analysis packet; score records and packet are the reporter's only inputs.",
             "Scientific reporting is producer-closed and label-restricted.", "add"),
    ]
    for item in edge_replacements:
        upsert(edges, "edge_id", item["edge_id"], item)

    resolver = principal(registry, "EVIDENCE_SUPPORT_RESOLVER")
    constructor = principal(registry, "CANDIDATE_CONSTRUCTOR")
    stager = principal(registry, "CANDIDATE_STAGER")
    evaluator = principal(registry, "PRESERVATION_EVALUATOR")
    promoter = principal(registry, "PROMOTION")
    reporter = principal(registry, "SCIENTIFIC_REPORTER")
    replace_loop(doc, "SLEEP_COMPILE_WRITE_COMMIT",
                 "At SLEEP s the model-free resolver closes the full cumulative eligible corpus under K_support and K_coverage_dose. The constructor computes C_s := W(B_z,Z0_s,E_le_s,K_writer,K_support,K_coverage_dose,seed_s), then seals bytes and trace. Only afterward may the stager compare an equality-only head snapshot. No prior head or staging information reaches construction.",
                 "After the frozen cutoff and all writer, resolver, finite-coverage/dose, matched-opportunity, statistics, and phase-receipt prerequisites exist.",
                 [resolver, constructor, stager], registry,
                 "Unsupported semantics, missing cumulative coverage, parent/repetition/DREAM/prior-head/evaluation taint, nonzero initializer, overflow, or any root/dose mismatch denies the writer or stage and preserves life.",
                 "SLEEP remains a fresh-from-birth compile-and-write over the child's own grounded life.")
    replace_loop(doc, "CANDIDATE_PRESERVATION_AND_PROMOTION",
                 "A fresh evaluator may inspect the sealed candidate and prior active child only after closure and emits a candidate-root-bound verdict. The lineage store then performs one PROMOTE_CAS_ATOMIC transaction or changes nothing.",
                 "Only after candidate closure and postclosure staging under exact preservation and atomic-promotion contracts.",
                 [evaluator, promoter], registry,
                 "A missing producer, stale head, changed candidate/verdict/root/namespace/nonce/idempotency, crash, retry, replay, or rejection leaves active weights and committed life unchanged and quarantines derivatives.",
                 "Preservation may veto learning without conditioning candidate construction; activation is atomic.")
    replace_loop(doc, "DISPOSABLE_SCIENTIFIC_EVALUATION",
                 "Fresh executors close transcripts before model-free scoring; the reporter reads only frozen score records and FROZEN_SCIENTIFIC_ANALYSIS_PACKET. No artifact returns to child, parent, DREAM, SLEEP, lineage, audit, or release.",
                 "Only at prospectively frozen ages after the exact matched-opportunity, split-evaluation, statistics, implementation, CPU, and authorized GPU phase receipts required for that action.",
                 [principal(registry, "EXAM_MODEL_EXECUTOR"),
                  principal(registry, "TRUTH_SCORER"), reporter], registry,
                 "Truth access by executor, model access by scorer, ambient analysis/label state, feedback, stale handles, or missing phase receipt fails closed.",
                 "The exam measures rather than teaches the continuing child.")
    replace_loop(doc, "SLEEP_CADENCE_EVALUATION",
                 "Compare prospectively assigned K4 and K1 lifetime roots through the same disposable executor, model-free scorer, and frozen analysis packet. Report checkpoint curves and the terminal total-package contrast; any standardized-ledger rewrite remains explicitly descriptive.",
                 "Only at preregistered ages after matched opportunity, cumulative coverage/dose, one-way evaluation, statistics, and the exact phase receipts for the affected action.",
                 [principal(registry, "EXAM_MODEL_EXECUTOR"),
                  principal(registry, "TRUTH_SCORER"), reporter], registry,
                 "Unequal life opportunity, unregistered cadence changes, feedback from exams, missing roots, or an attempt to label a descriptive standardized-ledger contrast causal fails closed.",
                 "Cadence is measured as a randomized total package without inventing a writer-only or history-only effect.")

    claims = doc["claim_delta"]["claims"]
    by_id(claims, "claim_id", "C_EXPERIENCE_EXTRACTABLE_AND_USABLE").update(
        after="Conditional on later powered evidence, a personal LoRA freshly reconstructed from immutable birth plus cumulative grounded child-authored life supports held-out cue extraction and native action on fresh homologous tasks without textual retrieval, compiler-created cognition, or interface harm.",
        evidence_needed="Powered independent-root source-fit, held-out extraction, native-use, adapter-off, deranged, wrong-life, replay/filler, preservation, provenance, uncertainty, multiplicity, missingness, and safety receipts.")
    fixed = by_id(claims, "claim_id", "C_BOOTSTRAP_FIXED_CURRICULUM_SLEEP_ACCELERATION")
    fixed.update(claim_id="C_BOOTSTRAP_FIXED_CURRICULUM_DEVELOPMENTAL_AUC_INTERACTION",
                 after="Conditional on powered Delta_F evidence, T modifies the entry-normalized developmental AUC of the total fixed-parent-plus-personal-SLEEP regime relative to D. This may be called an entry-normalized developmental AUC interaction or total-regime performance-curve acceleration, never an intrinsic or latent learning-rate change.",
                 evidence_needed="Powered primary D/T by absent/fixed independent-root factorial at ages 0,8,16,24,32 with matched opportunity, fixed bytes, clean one-way exams, raw curves, prospective uncertainty, multiplicity, missingness, stopping, and safety.")
    adaptive = by_id(claims, "claim_id", "C_BOOTSTRAP_ADAPTIVE_PACKAGE_ACCELERATION")
    adaptive.update(claim_id="C_BOOTSTRAP_ADAPTIVE_PACKAGE_DEVELOPMENTAL_AUC_INTERACTION",
                    after="Conditional on separately powered Delta_E evidence, T modifies the entry-normalized developmental AUC of the total adaptive-parent-plus-child-plus-personal-SLEEP package relative to D. It is separately reported total-regime effect modification, not intrinsic learning rate or mediation.",
                    evidence_needed="Powered separately randomized D/T by absent/adaptive independent roots under the frozen policy, matched opportunity, full effort/information receipts, clean exams, raw curves, uncertainty, multiplicity, missingness, stopping, and safety.")

    phases = science["acceptance_test_and_claim_receipt_contract"]["ordered_phases"]
    doc["acceptance_tests"] = [
        acceptance_test(test_id, science, dag)
        for test_id in science["acceptance_test_and_claim_receipt_contract"]
        ["v7_acceptance_test_ids"]
    ]

    doc["visibility_matrix"] = build_visibility(registry)
    doc["human_boundary"] = {
        "required": True,
        "decision_owner": "Rohin Ghosh",
        "decision_question": (
            "After two fresh interpretations, adversarial critique, and adjudicated "
            "consensus over these exact v7 bytes, does Rohin adopt only this architecture "
            "proposal? G0, implementation, model/tokenizer/data/bootstrap/writer execution, "
            "adapter/checkpoint work, CPU/GPU/resource use, science, result evaluation, "
            "claims, publication, push, and release remain separately unauthorized."
        ),
        "forbidden_before_approval": science["scope"]["excluded_actions"],
    }

    validate(doc, science, registry, dag)
    return doc


def validate(doc: dict, science: dict, registry: dict, dag: dict) -> None:
    expected_tests = science["acceptance_test_and_claim_receipt_contract"][
        "v7_acceptance_test_ids"]
    actual_tests = [t["test_id"] for t in doc["acceptance_tests"]]
    if actual_tests != expected_tests or len(set(actual_tests)) != 21:
        raise ValueError("V7 acceptance obligations do not exactly match scientific core")
    caps = {c["capability_id"] for c in registry["capabilities"]}
    loop_caps = {c for loop in doc["loop_delta"]["loops"]
                 for c in loop["reads"] + loop["writes"]}
    if not loop_caps <= caps:
        raise ValueError(f"loop references unregistered capabilities: {loop_caps - caps}")
    matrix = doc["visibility_matrix"]
    if len(matrix["cells"]) != len(registry["capabilities"]) * len(
            registry["registered_principals"]):
        raise ValueError("visibility matrix is not the complete registry product")
    operation_ids = {
        op["operation"] if isinstance(op, dict) else op
        for op in registry["registered_operations"]
    }
    if "PROMOTE_CAS_ATOMIC" not in operation_ids:
        raise ValueError("registry lacks PROMOTE_CAS_ATOMIC")
    classes = {a["artifact_class"] if isinstance(a, dict) else a
               for a in registry["artifact_classes"]}
    required_classes = {
        "FROZEN_MATCHED_SOLO_RESOURCE_OPPORTUNITY_CONTRACT",
        "FROZEN_SUPPORT_RESOLVER_CONTRACT",
        "FROZEN_CUMULATIVE_COVERAGE_DOSE_CONTRACT",
        "FROZEN_SCIENTIFIC_ANALYSIS_PACKET",
    }
    if not required_classes <= classes:
        raise ValueError(f"registry lacks required artifact classes: {required_classes-classes}")
    constructor = principal(registry, "CANDIDATE_CONSTRUCTOR")
    forbidden_constructor_classes = {
        "ACTIVE_WEIGHT_ARTIFACT", "COMMITTED_TRANSACTION_CAS_TOKEN",
        "PROMOTION_VERDICT", "PRESERVATION_EVIDENCE", "DREAM_CACHE",
        "LIVE_PARENT_MESSAGE", "SCIENTIFIC_SCORE_RECORD", "SCIENTIFIC_REPORT",
        "AUTHORITY_VERDICT", "EXTERNAL_HUMAN_AUTHORIZATION", "RELEASE_TARGET_ARTIFACT",
    }
    seen = {c["artifact_class"] for c in registry["capabilities"]
            if c["allowed_consumers"] == [constructor]}
    if seen & forbidden_constructor_classes:
        raise ValueError(f"constructor has forbidden inputs/capabilities: {seen & forbidden_constructor_classes}")
    labels = " ".join(c["after"] for c in doc["claim_delta"]["claims"])
    if "intrinsic learning" in labels.lower() and "never" not in labels.lower():
        raise ValueError("claims use forbidden intrinsic-learning-rate label")
    action_ids = {action_id(a) for a in dag["actions"]}
    for test in doc["acceptance_tests"]:
        for phase in phase_rows(test["test_id"], science, dag):
            if phase["producer_action_id"] not in action_ids:
                raise ValueError("phase receipt producer is not a registered action")
            if not set(phase["exact_downstream_action_ids"]) <= action_ids:
                raise ValueError("phase receipt guards an unregistered action")
    if doc["state"] != "proposed":
        raise ValueError("successor must remain a proposal")


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2) + "\n")
