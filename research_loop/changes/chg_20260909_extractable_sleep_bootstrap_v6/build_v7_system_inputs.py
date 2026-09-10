"""Build the proposal-only V7 capability registry and action DAG.

This is a mechanical successor transform over the independently reviewed V6
systems inputs.  It creates descriptions of later guards; it performs no
protected action and grants no implementation, execution, GPU, science,
claim, publication, push, or release authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V5 = ROOT / "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v5"
BASE_REGISTRY = V5 / "v6_capability_registry.json"
BASE_DAG = V5 / "v6_action_prerequisite_dag.json"
REGISTRY_OUT = HERE / "v7_capability_registry.json"
DAG_OUT = HERE / "v7_action_prerequisite_dag.json"

V7_TESTS = [
    "V7_ES01_EXACT_EXTERNAL_AUTHORITY_AND_CLASS_BOUND_RELEASE",
    "V7_ES02_EPOCH_ATTENUATED_AUTHORSHIP_GROUNDING_AND_REPETITION",
    "V7_ES03_FRESH_FROM_BIRTH_CONSTRUCTOR_MASK_DOSE_AND_TAINT",
    "V7_ES04_ZERO_EFFECTIVE_DELTA_INITIALIZER",
    "V7_ES05_BIRTH_MERGE_CONTRACT_AND_CONTENT_IDENTITY",
    "V7_ES06_ATOMIC_LINEAGE_PROMOTION_AND_RETRY_FAULTS",
    "V7_ES07_BOOTSTRAP_CONTROL_TARGET_BLINDNESS_AND_SEMANTIC_AUDIT",
    "V7_ES08_PRODUCER_CLOSED_AUDIT_TARGET_BLINDNESS",
    "V7_ES09_SPLIT_EXECUTOR_STANDARDIZED_ADVICE_RECEPTIVITY",
    "V7_ES10_FIXED_CURRICULUM_DEVELOPMENTAL_AUC_INTERACTION",
    "V7_ES11_ADAPTIVE_PACKAGE_DEVELOPMENTAL_AUC_INTERACTION",
    "V7_ES12_CURSOR_REPETITION_CONTROL_AND_ENACTMENT",
    "V7_ES13_CHILD_AUTHORED_STORAGE_EXTRACTION_NATIVE_USE",
    "V7_ES14_FRESH_FROM_BIRTH_REPLAY_DEPENDENCE",
    "V7_ES15_RANK_BY_EXPOSURE_ONLY",
    "V7_ES16_FRESH_FROM_BIRTH_CADENCE_TOTAL_PACKAGE",
    "V7_ES17_PREGENERATION_STATISTICS_RECEIPTS_AND_REPORT_LABELS",
    "V7_ES19_PRODUCER_CLOSED_EPOCH_CAPABILITY_NONINTERFERENCE",
    "V7_ES20_POSTCLOSURE_STAGING_ATOMIC_CAS_AND_LIFE_PRESERVATION",
    "V7_ES18_FRESH_REVIEW_AND_SEPARATE_TERMINAL_AUTHORITIES",
    "V7_ES21_PRODUCER_CLOSED_NONCIRCULAR_ACTION_DAG",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def artifact(name: str, producer: str, lifetime: str = "IMMUTABLE_SEALED_V1") -> dict:
    return {
        "artifact_class": name,
        "payload_schema_id": f"DOWNSTREAM_{name}_SCHEMA",
        "lifetime_id": lifetime,
        "producer_policy": producer,
    }


def capability(capability_id: str, operation: str, artifact_class: str,
               producer: str, consumer: str, namespace: str, epoch: str,
               use_rule: str = "single_use") -> dict:
    return {
        "capability_id": capability_id,
        "operation": operation,
        "artifact_class": artifact_class,
        "artifact_producer_id": producer,
        "allowed_consumers": [consumer],
        "namespace": namespace,
        "epoch": epoch,
        "use_rule": use_rule,
        "request_schema_id": f"CAPABILITY_REQUEST_{operation}_V1",
        "result_schema_id": f"CAPABILITY_RESULT_{operation}_V1",
    }


def bridge(transition_id: str, source: str, cap: dict, from_epoch: str) -> dict:
    return {
        "transition_id": transition_id,
        "source_id": source,
        "target_capability_id": cap["capability_id"],
        "artifact_class": cap["artifact_class"],
        "from_epoch": from_epoch,
        "to_epoch": cap["epoch"],
    }


def upsert(items: list[dict], key: str, value: str, row: dict) -> None:
    items[:] = [item for item in items if item.get(key) != value]
    items.append(row)


def build_registry() -> dict:
    r = copy.deepcopy(load(BASE_REGISTRY))
    r.update(
        registry_id="extractable_sleep_bootstrap_v7_capability_registry_v1",
        state="successor_proposal_input_only",
        bindings={
            "v6_change_path": str((HERE / "change.json").relative_to(ROOT)),
            "v6_change_sha256": sha(HERE / "change.json"),
            "v6_consensus_path": str((HERE / "consensus.json").relative_to(ROOT)),
            "v6_consensus_sha256": sha(HERE / "consensus.json"),
            "v7_resolution_path": str((HERE / "v7_blocker_resolution.md").relative_to(ROOT)),
            "v7_resolution_sha256": sha(HERE / "v7_blocker_resolution.md"),
            "v7_science_path": str((HERE / "v7_scientific_core.json").relative_to(ROOT)),
            "v7_science_sha256": sha(HERE / "v7_scientific_core.json"),
        },
    )

    operations = {o["operation"] for o in r["registered_operations"]}
    if "PROMOTE_CAS_ATOMIC" not in operations:
        r["registered_operations"].append({
            "operation": "PROMOTE_CAS_ATOMIC",
            "request_schema_id": "CAPABILITY_REQUEST_PROMOTE_CAS_ATOMIC_V1",
            "result_schema_id": "CAPABILITY_RESULT_PROMOTE_CAS_ATOMIC_V1",
            "semantics": (
                "In one linearizable store transaction equality-bind expected full "
                "active head, staged candidate, promotion verdict, replacement root, "
                "life/transaction namespace, nonce, and one-shot idempotency; either "
                "replace the active root and emit the bound receipt or change nothing."
            ),
        })

    old_principal = "E4_SLEEP_COMPILER_WRITER"
    constructor = "E4_CANDIDATE_CONSTRUCTOR"
    stager = "E4_CANDIDATE_STAGER"
    r["registered_principals"] = [
        constructor if p == old_principal else p
        for p in r["registered_principals"]
    ]
    for p in (stager, "G0_ACTION_DAG_GATE"):
        if p not in r["registered_principals"]:
            r["registered_principals"].append(p)

    new_artifacts = [
        artifact("ZERO_EFFECTIVE_DELTA_INITIALIZER", "X0_FROZEN_CONTRACT_SOURCE only."),
        artifact("FROZEN_SUPPORT_RESOLVER_CONTRACT", "X0_FROZEN_CONTRACT_SOURCE only."),
        artifact("FROZEN_CUMULATIVE_COVERAGE_DOSE_CONTRACT", "X0_FROZEN_CONTRACT_SOURCE only."),
        artifact("FROZEN_MATCHED_SOLO_RESOURCE_OPPORTUNITY_CONTRACT", "X0_FROZEN_CONTRACT_SOURCE only."),
        artifact("MATCHED_SOLO_RESOURCE_OPPORTUNITY_RECEIPT", "X0_FROZEN_CONTRACT_SOURCE only."),
        artifact("FROZEN_SCIENTIFIC_ANALYSIS_PACKET", "X0_FROZEN_CONTRACT_SOURCE only."),
        artifact("CANDIDATE_CONSTRUCTION_TRACE", "E4_CANDIDATE_CONSTRUCTOR only."),
        artifact("SEALED_CANDIDATE_DESCRIPTOR", "E4_CANDIDATE_CONSTRUCTOR only."),
        artifact("STAGED_CANDIDATE_DESCRIPTOR", "E4_CANDIDATE_STAGER only."),
        artifact("TYPED_ACCEPTANCE_TEST_PHASE_RECEIPT", "The exact registered phase-runner action only."),
        artifact("G0_EXACT_HARNESS_MANIFEST", "X0_FROZEN_CONTRACT_SOURCE only."),
    ]
    for row in new_artifacts:
        upsert(r["artifact_classes"], "artifact_class", row["artifact_class"], row)
    for row in r["artifact_classes"]:
        if row["artifact_class"] == "ACTIVE_WEIGHT_ARTIFACT":
            row["producer_policy"] = "Genesis is the immutable birth; successors only by X0_COMMITTED_LINEAGE_STORE through PROMOTE_CAS_ATOMIC."
        if row["artifact_class"] == "CANDIDATE_CLOSURE":
            row["producer_policy"] = "E4_CANDIDATE_CONSTRUCTOR only; bytes close before any staging or head access."
        if row["artifact_class"] == "CANDIDATE_TRANSACTION_RECEIPT":
            row["producer_policy"] = "E4_CANDIDATE_STAGER only, after candidate closure."
        if row["artifact_class"] == "PROMOTION_TRANSACTION_RECEIPT":
            row["producer_policy"] = "X0_COMMITTED_LINEAGE_STORE only, atomically with active-head replacement."
        if row["artifact_class"] == "RELEASE_TARGET_ARTIFACT":
            row["producer_policy"] = "X0_REGISTERED_RELEASE_ARTIFACT_STORE only; sealed wrapper equality-binds concrete payload class and underlying root to the full release tuple."

    id_map: dict[str, str] = {}
    removed = {
        "E4_COMPILER_BIND_COMMITTED_SNAPSHOT",
        "E4_COMPILER_WRITE_TRANSACTION_RECEIPT",
        "E5_GATE_BIND_CANDIDATE_ROOT",
        "E5_GATE_BIND_COMMITTED_CAS",
        "E5_GATE_WRITE_ACTIVE_WEIGHT",
        "E5_GATE_WRITE_TRANSACTION_RECEIPT",
    }
    caps = []
    for c0 in r["capabilities"]:
        if c0["capability_id"] in removed:
            continue
        c = copy.deepcopy(c0)
        if c["allowed_consumers"] == [old_principal]:
            old_id = c["capability_id"]
            c["capability_id"] = old_id.replace("E4_COMPILER_", "E4_CONSTRUCTOR_")
            id_map[old_id] = c["capability_id"]
            c["allowed_consumers"] = [constructor]
            c["artifact_producer_id"] = (
                constructor if c["artifact_producer_id"] == old_principal
                else c["artifact_producer_id"]
            )
            c["epoch"] = "E4_CONSTRUCTOR_INVOCATION"
            c["namespace"] = c["namespace"].replace("compiler", "constructor")
        if c["artifact_producer_id"] == old_principal:
            c["artifact_producer_id"] = constructor
        caps.append(c)
    for c in caps:
        if c["capability_id"] == "E4_COMPILER_MONITOR_READ_EVENTS":
            c["artifact_producer_id"] = constructor

    additions = [
        capability("E4_SUPPORT_READ_FROZEN_RESOLVER_CONTRACT", "READ",
                   "FROZEN_SUPPORT_RESOLVER_CONTRACT", "X0_FROZEN_CONTRACT_SOURCE",
                   "E4_EVIDENCE_SUPPORT_RESOLVER", "e4/frozen-contract/support-resolver",
                   "E4_SUPPORT_INVOCATION"),
        capability("E4_CONSTRUCTOR_READ_ZERO_INITIALIZER", "READ",
                   "ZERO_EFFECTIVE_DELTA_INITIALIZER", "X0_FROZEN_CONTRACT_SOURCE",
                   constructor, "e4/frozen-contract/zero-initializer", "E4_CONSTRUCTOR_INVOCATION"),
        capability("E4_CONSTRUCTOR_READ_SUPPORT_CONTRACT", "READ",
                   "FROZEN_SUPPORT_RESOLVER_CONTRACT", "X0_FROZEN_CONTRACT_SOURCE",
                   constructor, "e4/frozen-contract/support-resolver", "E4_CONSTRUCTOR_INVOCATION"),
        capability("E4_CONSTRUCTOR_READ_COVERAGE_DOSE_CONTRACT", "READ",
                   "FROZEN_CUMULATIVE_COVERAGE_DOSE_CONTRACT", "X0_FROZEN_CONTRACT_SOURCE",
                   constructor, "e4/frozen-contract/coverage-dose", "E4_CONSTRUCTOR_INVOCATION"),
        capability("E4_CONSTRUCTOR_WRITE_CONSTRUCTION_TRACE", "WRITE",
                   "CANDIDATE_CONSTRUCTION_TRACE", constructor, constructor,
                   "e4/candidate/construction-trace", "E4_CONSTRUCTOR_INVOCATION"),
        capability("E4_CONSTRUCTOR_WRITE_SEALED_DESCRIPTOR", "WRITE",
                   "SEALED_CANDIDATE_DESCRIPTOR", constructor, constructor,
                   "e4/candidate/sealed-descriptor", "E4_CONSTRUCTOR_INVOCATION"),
        capability("E4_STAGER_READ_SEALED_DESCRIPTOR", "READ",
                   "SEALED_CANDIDATE_DESCRIPTOR", constructor, stager,
                   "e4/candidate/sealed-descriptor", "E4_STAGER_INVOCATION"),
        capability("E4_STAGER_BIND_COMMITTED_SNAPSHOT", "BIND_EQUALITY",
                   "COMMITTED_TRANSACTION_CAS_TOKEN", "X0_COMMITTED_LINEAGE_STORE", stager,
                   "e4/lineage/snapshot", "E4_STAGER_INVOCATION"),
        capability("E4_STAGER_WRITE_STAGED_DESCRIPTOR", "WRITE",
                   "STAGED_CANDIDATE_DESCRIPTOR", stager, stager,
                   "e4/candidate/staged-descriptor", "E4_STAGER_INVOCATION"),
        capability("E4_STAGER_WRITE_TRANSACTION_RECEIPT", "WRITE",
                   "CANDIDATE_TRANSACTION_RECEIPT", stager, stager,
                   "e4/lineage/candidate-receipt", "E4_STAGER_INVOCATION"),
        capability("E5_GATE_READ_STAGED_DESCRIPTOR", "READ",
                   "STAGED_CANDIDATE_DESCRIPTOR", stager, "E5_LINEAGE_PROMOTION_GATE",
                   "e4/candidate/staged-descriptor", "E5_PROMOTION_INVOCATION"),
        capability("E5_GATE_PROMOTE_CAS_ATOMIC", "PROMOTE_CAS_ATOMIC",
                   "PROMOTION_TRANSACTION_RECEIPT", "X0_COMMITTED_LINEAGE_STORE",
                   "E5_LINEAGE_PROMOTION_GATE", "e5/lineage/atomic-promotion",
                   "E5_PROMOTION_INVOCATION"),
        capability("E6_REPORTER_READ_ANALYSIS_PACKET", "READ",
                   "FROZEN_SCIENTIFIC_ANALYSIS_PACKET", "X0_FROZEN_CONTRACT_SOURCE",
                   "E6_SCIENTIFIC_REPORTER", "e6/frozen-analysis-packet",
                   "E6_REPORTER_INVOCATION"),
        capability("G0_GATE_READ_MATCHED_SOLO_RECEIPT", "READ",
                   "MATCHED_SOLO_RESOURCE_OPPORTUNITY_RECEIPT", "X0_FROZEN_CONTRACT_SOURCE",
                   "G0_ACTION_DAG_GATE", "g0/matched-solo-receipt", "G0_GATE_INVOCATION",
                   "multi_use_bounded_by_contract"),
    ]
    caps.extend(additions)
    r["capabilities"] = sorted(caps, key=lambda x: x["capability_id"])

    # Retarget preserved bridges after the compiler principal/capability split.
    bridges = []
    cap_ids = {c["capability_id"] for c in r["capabilities"]}
    for b0 in r["epoch_bridges"]:
        b = copy.deepcopy(b0)
        b["target_capability_id"] = id_map.get(
            b["target_capability_id"], b["target_capability_id"]
        )
        source_replacements = {
            "E4_COMPILER_WRITE_TRANSACTION_RECEIPT":
                "E4_STAGER_WRITE_TRANSACTION_RECEIPT",
            "E5_GATE_WRITE_TRANSACTION_RECEIPT":
                "E5_GATE_PROMOTE_CAS_ATOMIC",
        }
        b["source_id"] = source_replacements.get(
            b["source_id"], id_map.get(b["source_id"], b["source_id"])
        )
        if b["target_capability_id"] not in cap_ids:
            continue
        if b["source_id"] in removed:
            continue
        target = next(c for c in r["capabilities"]
                      if c["capability_id"] == b["target_capability_id"])
        b["to_epoch"] = target["epoch"]
        bridges.append(b)

    new_bridge_specs = [
        ("X0_FROZEN_CONTRACT_SOURCE", "E4_SUPPORT_READ_FROZEN_RESOLVER_CONTRACT", "FROZEN_EXTERNAL"),
        ("X0_FROZEN_CONTRACT_SOURCE", "E4_CONSTRUCTOR_READ_ZERO_INITIALIZER", "FROZEN_EXTERNAL"),
        ("X0_FROZEN_CONTRACT_SOURCE", "E4_CONSTRUCTOR_READ_SUPPORT_CONTRACT", "FROZEN_EXTERNAL"),
        ("X0_FROZEN_CONTRACT_SOURCE", "E4_CONSTRUCTOR_READ_COVERAGE_DOSE_CONTRACT", "FROZEN_EXTERNAL"),
        ("E4_CONSTRUCTOR_WRITE_SEALED_DESCRIPTOR", "E4_STAGER_READ_SEALED_DESCRIPTOR", "E4_CONSTRUCTOR_INVOCATION"),
        ("X0_COMMITTED_LINEAGE_STORE", "E4_STAGER_BIND_COMMITTED_SNAPSHOT", "COMMITTED_LINEAGE"),
        ("E4_STAGER_WRITE_STAGED_DESCRIPTOR", "E5_GATE_READ_STAGED_DESCRIPTOR", "E4_STAGER_INVOCATION"),
        ("X0_FROZEN_CONTRACT_SOURCE", "E6_REPORTER_READ_ANALYSIS_PACKET", "FROZEN_EXTERNAL"),
        ("X0_FROZEN_CONTRACT_SOURCE", "G0_GATE_READ_MATCHED_SOLO_RECEIPT", "FROZEN_EXTERNAL"),
    ]
    next_id = 1 + max(int(b["transition_id"][1:]) for b in bridges)
    for source, cap_id, from_epoch in new_bridge_specs:
        cap = next(c for c in r["capabilities"] if c["capability_id"] == cap_id)
        bridges.append(bridge(f"T{next_id:03d}", source, cap, from_epoch))
        next_id += 1
    r["epoch_bridges"] = bridges

    r["internal_invariants"] = [
        {"invariant_id": "V7CR01_REGISTERED_SINGLE_CONSUMER_CLOSURE", "predicate": "Every capability uses one registered operation, artifact class, principal, invocation epoch, and exactly one consumer."},
        {"invariant_id": "V7CR02_READLIKE_BRIDGE_CLOSURE", "predicate": "Every READ, DEREFERENCE, BIND_EQUALITY, TRANSFER_OPAQUE, and ADVANCE capability has exactly one matching close/reissue bridge."},
        {"invariant_id": "V7CR03_SUPPORT_RESOLVER_CONTRACT_BOUND", "predicate": "The resolver alone receives the frozen model-free support contract and cannot infer a missing child conclusion."},
        {"invariant_id": "V7CR04_CONSTRUCTOR_ISOLATED", "predicate": "The candidate constructor has no active-head, CAS, verdict, evaluation, parent, repetition, DREAM, science, audit, authority, or release capability."},
        {"invariant_id": "V7CR05_POSTCLOSURE_STAGER_ONLY", "predicate": "The stager receives only a sealed non-dereferenceable candidate descriptor plus equality-only committed snapshot after candidate closure."},
        {"invariant_id": "V7CR06_ATOMIC_PROMOTION_ONLY", "predicate": "Exactly one PROMOTE_CAS_ATOMIC capability exists and the promotion gate has no generic active-weight WRITE."},
        {"invariant_id": "V7CR07_ANALYSIS_PACKET_ONLY_REPORTER", "predicate": "Only the scientific reporter reads the frozen analysis packet and it receives no hidden truth, transcript, model, feedback, or release authority through that packet."},
        {"invariant_id": "V7CR08_MATCHED_SOLO_GATE", "predicate": "The action gate alone reads the immutable matched-solo receipt; the DAG makes it a prerequisite of every covered action."},
        {"invariant_id": "V7CR09_WRAPPER_CLASS_ROOT_RELEASE", "predicate": "TRANSFER_OPAQUE binds the sealed release wrapper, concrete payload class and root, and all nine release-tuple fields."},
        {"invariant_id": "V7CR10_QUARANTINED_FINDINGS", "predicate": "Detailed audit findings have no bridge to authority or release; only fixed-size attestations may cross."},
        {"invariant_id": "V7CR11_COMPLETE_VISIBILITY_PRODUCT", "predicate": "The successor proposal generates every principal-by-capability cell from these exact bytes."},
        {"invariant_id": "V7CR12_PROPOSAL_ONLY", "predicate": "This registry grants no handle, implementation, execution, GPU, science, claim, publication, push, release, ratification, or intake authority."},
    ]
    validate_registry(r)
    return r


def validate_registry(r: dict) -> None:
    principals = set(r["registered_principals"])
    classes = {a["artifact_class"] for a in r["artifact_classes"]}
    operations = {o["operation"] for o in r["registered_operations"]}
    caps = r["capabilities"]
    ids = [c["capability_id"] for c in caps]
    assert len(ids) == len(set(ids))
    for c in caps:
        assert len(c["allowed_consumers"]) == 1
        assert c["allowed_consumers"][0] in principals
        assert c["artifact_class"] in classes
        assert c["operation"] in operations
    readlike = {"READ", "DEREFERENCE", "BIND_EQUALITY", "TRANSFER_OPAQUE", "ADVANCE"}
    targets = [b["target_capability_id"] for b in r["epoch_bridges"]]
    for c in caps:
        if c["operation"] in readlike:
            assert targets.count(c["capability_id"]) == 1, c["capability_id"]
    constructor = "E4_CANDIDATE_CONSTRUCTOR"
    forbidden = {"ACTIVE_WEIGHT_ARTIFACT", "COMMITTED_TRANSACTION_CAS_TOKEN",
                 "PROMOTION_VERDICT", "PRESERVATION_EVIDENCE", "DREAM_CACHE",
                 "LIVE_PARENT_MESSAGE", "SCIENTIFIC_SCORE_RECORD", "SCIENTIFIC_REPORT",
                 "AUTHORITY_VERDICT", "EXTERNAL_HUMAN_AUTHORIZATION", "RELEASE_TARGET_ARTIFACT"}
    assert not {c["artifact_class"] for c in caps
                if c["allowed_consumers"] == [constructor]} & forbidden
    atomic = [c for c in caps if c["operation"] == "PROMOTE_CAS_ATOMIC"]
    assert len(atomic) == 1
    assert atomic[0]["allowed_consumers"] == ["E5_LINEAGE_PROMOTION_GATE"]
    assert not any(c["operation"] == "WRITE" and
                   c["artifact_class"] == "ACTIVE_WEIGHT_ARTIFACT" for c in caps)


def external_receipt(receipt_id: str, bindings: list[str],
                     source: str = "external_human") -> dict:
    return {"receipt_id": receipt_id, "source": source,
            "required_bindings": bindings}


def build_dag(registry: dict) -> dict:
    d = copy.deepcopy(load(BASE_DAG))
    d.update(
        dag_id="extractable_sleep_bootstrap_v7_action_prerequisite_dag_v1",
        state="successor_proposal_input_only",
        bindings={
            "v6_change_path": str((HERE / "change.json").relative_to(ROOT)),
            "v6_change_sha256": sha(HERE / "change.json"),
            "v6_consensus_path": str((HERE / "consensus.json").relative_to(ROOT)),
            "v6_consensus_sha256": sha(HERE / "consensus.json"),
            "v7_resolution_path": str((HERE / "v7_blocker_resolution.md").relative_to(ROOT)),
            "v7_resolution_sha256": sha(HERE / "v7_blocker_resolution.md"),
            "v7_science_path": str((HERE / "v7_scientific_core.json").relative_to(ROOT)),
            "v7_science_sha256": sha(HERE / "v7_scientific_core.json"),
            "v7_capability_registry_path": str(REGISTRY_OUT.relative_to(ROOT)),
            "v7_capability_registry_sha256": sha(REGISTRY_OUT),
        },
    )
    receipts = d["external_prerequisite_receipts"]
    for row in receipts:
        if row["receipt_id"] == "R_SUCCESSOR_V6_ARCHITECTURE_HUMAN_RATIFICATION":
            row["receipt_id"] = "R_SUCCESSOR_V7_ARCHITECTURE_HUMAN_RATIFICATION"
        if row["receipt_id"] == "R_AUTH_G0_HARNESS_EXACT":
            row["required_bindings"] = [
                "action_id", "capability_registry_root", "action_dag_root",
                "parser_root", "capability_issuer_root", "epoch_bridge_root",
                "receipt_validator_root", "action_gate_root", "fake_artifacts_root",
                "fake_dispatchers_root", "fault_fixtures_root",
                "allowed_path_manifest_root", "forbidden_scope_root",
                "expected_static_output_manifest_root",
                "expected_fault_output_manifest_root",
                "expected_installed_gate_output_manifest_root",
                "scope", "nonce", "expiry",
            ]
    new_external = [
        external_receipt("R_MATCHED_SOLO_RESOURCE_OPPORTUNITY_FROZEN",
                         ["contract_root", "receipt_root", "arm_root_identities",
                          "covered_action_ids", "resource_and_opportunity_fields",
                          "scope", "nonce", "expiry"], "frozen_contract_source"),
        external_receipt("R_SUPPORT_RESOLVER_CONTRACT_FROZEN",
                         ["contract_root", "representation_root", "rules_root",
                          "threshold_root", "dispute_policy_root", "scope", "nonce", "expiry"],
                         "frozen_contract_source"),
        external_receipt("R_CUMULATIVE_COVERAGE_DOSE_CONTRACT_FROZEN",
                         ["contract_root", "eligible_closure_root", "order_root",
                          "coverage_rule_root", "dose_root", "ceiling_root",
                          "overflow_and_missingness_root", "scope", "nonce", "expiry"],
                         "frozen_contract_source"),
        external_receipt("R_SCIENTIFIC_ANALYSIS_PACKET_FROZEN",
                         ["packet_root", "assignment_root", "endpoint_root",
                          "estimand_root", "missingness_root", "safety_root",
                          "multiplicity_root", "analysis_code_root", "label_root",
                          "scope", "nonce", "expiry"], "frozen_contract_source"),
    ]
    existing = {r["receipt_id"] for r in receipts}
    receipts.extend(r for r in new_external if r["receipt_id"] not in existing)

    for action in d["actions"]:
        action["prerequisite_receipt_ids"] = [
            "R_SUCCESSOR_V7_ARCHITECTURE_HUMAN_RATIFICATION"
            if x == "R_SUCCESSOR_V6_ARCHITECTURE_HUMAN_RATIFICATION" else x
            for x in action["prerequisite_receipt_ids"]
        ]
        if action["action_id"] == "A_G1_05_IMPLEMENT_CANDIDATE_EVALUATION_PROMOTION":
            action["action_id"] = "A_G1_05_IMPLEMENT_CONSTRUCTOR_STAGER_EVALUATOR_ATOMIC_PROMOTION"
            action["action_class"] = "domain_constructor_stager_evaluator_atomic_promotion_implementation"
        if action["action_id"] == "A_G2_11_RUN_PERSONAL_SLEEP_WRITER":
            action["action_id"] = "A_G2_11_CONSTRUCT_PERSONAL_SLEEP_CANDIDATE"
            action["action_class"] = "personal_sleep_candidate_construction"
            action["produces_receipt_id"] = "R_G2_CANDIDATE_CONSTRUCTED"
            action["prerequisite_receipt_ids"].extend([
                "R_SUPPORT_RESOLVER_CONTRACT_FROZEN",
                "R_CUMULATIVE_COVERAGE_DOSE_CONTRACT_FROZEN",
            ])
        if action["action_id"] == "A_G2_12_COMPILE_CANDIDATE":
            action["action_id"] = "A_G2_12_STAGE_CLOSED_CANDIDATE"
            action["action_class"] = "postclosure_candidate_staging"
            action["prerequisite_receipt_ids"] = [
                "R_G2_CANDIDATE_CONSTRUCTED" if x == "R_G2_PERSONAL_SLEEP_WRITER_PASS" else x
                for x in action["prerequisite_receipt_ids"]
            ]
            action["produces_receipt_id"] = "R_G2_CANDIDATE_STAGED"
        if action["action_id"] == "A_G2_13_EVALUATE_CANDIDATE":
            action["prerequisite_receipt_ids"] = [
                "R_G2_CANDIDATE_STAGED" if x == "R_G2_CANDIDATE_COMPILED" else x
                for x in action["prerequisite_receipt_ids"]
            ]
        if action["action_id"] == "A_G2_14_PROMOTE_CANDIDATE":
            action["action_id"] = "A_G2_14_PROMOTE_CANDIDATE_ATOMIC"
            action["action_class"] = "atomic_candidate_promote_or_quarantine"

    # Exact opportunity equality is a prerequisite of every affected execution.
    for action in d["actions"]:
        if action["authority_layer"] in {
            "G2_GUARDED_DOMAIN_EXECUTION", "G3_GPU_AND_EXTERNAL_SCIENCE"
        } and "R_MATCHED_SOLO_RESOURCE_OPPORTUNITY_FROZEN" not in action["prerequisite_receipt_ids"]:
            action["prerequisite_receipt_ids"].append(
                "R_MATCHED_SOLO_RESOURCE_OPPORTUNITY_FROZEN"
            )

    g1_receipt = "R_V7_G1_IMPLEMENTATION_REVIEW_PHASE_PASS"
    g2_receipt = "R_V7_G2_CPU_DOMAIN_PHASE_PASS"
    g3_receipt = "R_V7_G3_GPU_SCIENCE_PHASE_PASS"
    g4_receipt = "R_V7_G4_CLAIM_PHASE_PASS"
    g1_outputs = [a["produces_receipt_id"] for a in d["actions"]
                  if a["authority_layer"] == "G1_GUARDED_DOMAIN_IMPLEMENTATION"]
    g2_outputs = [a["produces_receipt_id"] for a in d["actions"]
                  if a["authority_layer"] == "G2_GUARDED_DOMAIN_EXECUTION"]
    d["actions"].extend([
        {"action_id": "A_G1_08_RUN_IMPLEMENTATION_REVIEW_PHASE",
         "topological_rank": 150, "authority_layer": "G1_GUARDED_DOMAIN_IMPLEMENTATION",
         "action_class": "typed_implementation_review_phase",
         "guarded_domain_action": True,
         "prerequisite_receipt_ids": ["R_AUTH_G1_IMPLEMENTATION_EXACT",
             "R_G0_FAIL_CLOSED_GATE_INSTALLED", *g1_outputs],
         "produces_receipt_id": g1_receipt},
        {"action_id": "A_G2_17_RUN_CPU_DOMAIN_TEST_PHASE",
         "topological_rank": 350, "authority_layer": "G2_GUARDED_DOMAIN_EXECUTION",
         "action_class": "typed_cpu_domain_test_phase",
         "guarded_domain_action": True,
         "prerequisite_receipt_ids": ["R_AUTH_CPU_EXECUTION_EXACT",
             "R_G0_FAIL_CLOSED_GATE_INSTALLED", g1_receipt,
             "R_MATCHED_SOLO_RESOURCE_OPPORTUNITY_FROZEN", *g2_outputs],
         "produces_receipt_id": g2_receipt},
        {"action_id": "A_G3_04_RUN_GPU_SCIENCE_TEST_PHASE",
         "topological_rank": 450, "authority_layer": "G3_GPU_AND_EXTERNAL_SCIENCE",
         "action_class": "typed_gpu_science_test_phase",
         "guarded_domain_action": True,
         "prerequisite_receipt_ids": ["R_AUTH_EXTERNAL_SCIENCE_EXACT",
             "R_G0_FAIL_CLOSED_GATE_INSTALLED", g2_receipt,
             "R_MATCHED_SOLO_RESOURCE_OPPORTUNITY_FROZEN",
             "R_G3_EXTERNAL_SCIENCE_COMPLETE"],
         "produces_receipt_id": g3_receipt},
        {"action_id": "A_G4_00_RUN_CLAIM_TEST_PHASE",
         "topological_rank": 490, "authority_layer": "G4_TERMINAL_ACTION",
         "action_class": "typed_claim_test_phase",
         "guarded_domain_action": True,
         "prerequisite_receipt_ids": ["R_AUTH_CLAIM_EXACT",
             "R_G0_FAIL_CLOSED_GATE_INSTALLED", g3_receipt,
             "R_SCIENTIFIC_ANALYSIS_PACKET_FROZEN"],
         "produces_receipt_id": g4_receipt},
    ])

    # Each later layer requires the immediately constructible typed phase.
    for action in d["actions"]:
        layer = action["authority_layer"]
        if layer == "G2_GUARDED_DOMAIN_EXECUTION" and action["action_id"] != "A_G2_17_RUN_CPU_DOMAIN_TEST_PHASE":
            action["prerequisite_receipt_ids"].append(g1_receipt)
        if layer == "G3_GPU_AND_EXTERNAL_SCIENCE" and action["action_id"] != "A_G3_04_RUN_GPU_SCIENCE_TEST_PHASE":
            action["prerequisite_receipt_ids"].append(g2_receipt)
        if action["action_id"] == "A_G4_01_MAKE_SCIENTIFIC_CLAIM":
            action["prerequisite_receipt_ids"].extend([g3_receipt, g4_receipt,
                                                       "R_SCIENTIFIC_ANALYSIS_PACKET_FROZEN"])
        action["prerequisite_receipt_ids"] = sorted(set(action["prerequisite_receipt_ids"]))

    # Six constructible phases; each manifest contains one typed, root-bound
    # receipt row per V7 obligation.
    phase_specs = [
        ("STATIC_SCHEMA", "A_G0_08_RUN_STATIC_COMPLETENESS", "R_G0_STATIC_COMPLETENESS_PASS",
         ["A_G0_10_INSTALL_FAIL_CLOSED_GATE"]),
        ("G0_FAKE_RUNTIME", "A_G0_09_RUN_FAKE_TRANSACTION_FAULTS", "R_G0_FAKE_FAULTS_PASS",
         ["A_G0_10_INSTALL_FAIL_CLOSED_GATE"]),
        ("G1_IMPLEMENTATION_REVIEW", "A_G1_08_RUN_IMPLEMENTATION_REVIEW_PHASE", g1_receipt,
         ["A_G2_01_REGISTER_TREATMENT_SOURCES"]),
        ("G2_CPU_DOMAIN", "A_G2_17_RUN_CPU_DOMAIN_TEST_PHASE", g2_receipt,
         ["A_G3_01_DISPATCH_GPU_RESOURCE"]),
        ("G3_GPU_SCIENCE", "A_G3_04_RUN_GPU_SCIENCE_TEST_PHASE", g3_receipt,
         ["A_G4_00_RUN_CLAIM_TEST_PHASE"]),
        ("G4_CLAIM", "A_G4_00_RUN_CLAIM_TEST_PHASE", g4_receipt,
         ["A_G4_01_MAKE_SCIENTIFIC_CLAIM"]),
    ]
    d["test_phase_receipt_schema"] = {
        "artifact_class": "TYPED_ACCEPTANCE_TEST_PHASE_RECEIPT",
        "required_bindings": ["test_id", "phase_id", "subject_root",
            "input_roots", "fixture_or_implementation_or_result_roots", "pass_fail",
            "reviewer_identity_when_applicable", "expiry", "replay_policy",
            "exact_downstream_action_ids"],
        "failure_policy": "Any missing, failed, stale, replayed, wrong-root, or wrong-action row fails closed.",
    }
    d["test_phase_receipt_mappings"] = {
        test_id: [
            {"phase_id": phase, "producer_action_id": producer,
             "typed_pass_receipt": receipt,
             "exact_downstream_action_ids": downstream}
            for phase, producer, receipt, downstream in phase_specs
        ] for test_id in V7_TESTS
    }
    d["analysis_and_evidence_prerequisites"] = {
        "GPU_dispatch_requires": [
            "R_MATCHED_SOLO_RESOURCE_OPPORTUNITY_FROZEN",
            "R_SUPPORT_RESOLVER_CONTRACT_FROZEN",
            "R_CUMULATIVE_COVERAGE_DOSE_CONTRACT_FROZEN",
            g1_receipt, g2_receipt,
            "typed target-blindness and bootstrap semantic-audit rows",
            "typed producer-closed noninterference rows",
        ],
        "scientific_claim_requires": [
            g3_receipt, g4_receipt, "R_SCIENTIFIC_ANALYSIS_PACKET_FROZEN",
            "powered root-level endpoints and intervals", "multiplicity and missingness",
            "safety", "child authorship", "held-out extraction and native use",
            "claim-specific semantic receipts",
        ],
        "generic_completion_receipt_is_sufficient": False,
        "human_authority_substitutes_for_evidence": False,
    }
    d["first_affected_action_classes"] = sorted({
        a["action_class"] for a in d["actions"] if a["guarded_domain_action"]
    })
    d["lowest_gpu_sequence"] = [a["action_id"] for a in sorted(
        d["actions"], key=lambda a: (a["topological_rank"], a["action_id"])
    ) if a["topological_rank"] <= 450]
    d["internal_invariants"] = [
        {"invariant_id": "V7AD01_UNIQUE_AND_RECEIPT_CLOSED", "predicate": "Action, produced-receipt, and external-receipt IDs are unique; every prerequisite is external or produced by exactly one earlier action."},
        {"invariant_id": "V7AD02_ACYCLIC", "predicate": "Every produced prerequisite has a strictly lower topological rank; all actions topologically sort."},
        {"invariant_id": "V7AD03_G0_EXACT_BYTE_TRUST_ROOT", "predicate": "G0 authorization binds registry, DAG, parser, issuer, bridge, validator, gate, fakes, dispatchers, faults, path/scope manifests, expected outputs, action, scope, nonce, and expiry."},
        {"invariant_id": "V7AD04_CONSTRUCTIBLE_PHASE_ORDER", "predicate": "STATIC_SCHEMA, G0_FAKE_RUNTIME, G1_IMPLEMENTATION_REVIEW, G2_CPU_DOMAIN, G3_GPU_SCIENCE, and G4_CLAIM receipts guard only later constructible actions."},
        {"invariant_id": "V7AD05_MATCHED_SOLO_FIRST_ACTION", "predicate": "Every covered G2/G3 generation or execution action requires the exact matched-solo opportunity receipt before it begins."},
        {"invariant_id": "V7AD06_GPU_AFTER_CPU_AND_AUDITS", "predicate": "GPU dispatch requires G1 and G2 phase manifests plus target-blindness, semantic, and noninterference rows under exact GPU authority."},
        {"invariant_id": "V7AD07_CLAIM_AFTER_POWERED_EVIDENCE", "predicate": "A claim requires G3 and G4 manifests, frozen analysis packet, powered root-level evidence, uncertainty, multiplicity, missingness, safety, extraction/use, and separate exact claim authority."},
        {"invariant_id": "V7AD08_ATOMIC_PROMOTION", "predicate": "The candidate sequence is construct, close/stage, evaluate, then one atomic promote-or-no-change action."},
        {"invariant_id": "V7AD09_NO_SELF_GATE", "predicate": "No protected action constructs or runs its own G0 gate prerequisite."},
        {"invariant_id": "V7AD10_TERMINAL_AUTHORITIES_SEPARATE", "predicate": "External science, claim, publication, push, and release retain separate exact human authorities."},
        {"invariant_id": "V7AD11_RELEASE_CLASS_ROOT_TUPLE", "predicate": "Opaque release equality-binds wrapper, concrete payload class/root, destination, operation, protocol, scope, nonce, expiry, and idempotency."},
        {"invariant_id": "V7AD12_PROPOSAL_ONLY", "predicate": "This DAG authorizes no implementation, execution, GPU, science, claim, publication, push, release, ratification, or intake transition."},
    ]
    d["present_authority"] = {
        "status": "none",
        "allowed_now": ["successor_proposal_drafting"],
        "all_actions_in_this_dag": "not_authorized",
    }
    validate_dag(d)
    return d


def validate_dag(d: dict) -> None:
    actions = d["actions"]
    action_ids = [a["action_id"] for a in actions]
    produced = [a["produces_receipt_id"] for a in actions]
    external = [r["receipt_id"] for r in d["external_prerequisite_receipts"]]
    assert len(action_ids) == len(set(action_ids))
    assert len(produced) == len(set(produced))
    assert len(external) == len(set(external))
    producers = {a["produces_receipt_id"]: a for a in actions}
    allowed = set(produced) | set(external)
    for a in actions:
        assert set(a["prerequisite_receipt_ids"]) <= allowed, (
            a["action_id"], set(a["prerequisite_receipt_ids"]) - allowed
        )
        for receipt in a["prerequisite_receipt_ids"]:
            if receipt in producers:
                assert producers[receipt]["topological_rank"] < a["topological_rank"], (
                    producers[receipt]["action_id"], a["action_id"]
                )
    assert len(d["test_phase_receipt_mappings"]) == 21
    assert set(d["test_phase_receipt_mappings"]) == set(V7_TESTS)
    ids = set(action_ids)
    for rows in d["test_phase_receipt_mappings"].values():
        assert len(rows) == 6
        for row in rows:
            assert row["producer_action_id"] in ids
            assert set(row["exact_downstream_action_ids"]) <= ids
    for a in actions:
        if a["authority_layer"] in {"G2_GUARDED_DOMAIN_EXECUTION",
                                    "G3_GPU_AND_EXTERNAL_SCIENCE"}:
            assert "R_MATCHED_SOLO_RESOURCE_OPPORTUNITY_FROZEN" in a["prerequisite_receipt_ids"]
    assert d["present_authority"]["status"] == "none"
    assert d["present_authority"]["all_actions_in_this_dag"] == "not_authorized"


def main() -> None:
    registry = build_registry()
    REGISTRY_OUT.write_text(json.dumps(registry, indent=2) + "\n")
    dag = build_dag(registry)
    DAG_OUT.write_text(json.dumps(dag, indent=2) + "\n")
    # Re-read exact outputs after serialization and validate again.
    validate_registry(load(REGISTRY_OUT))
    validate_dag(load(DAG_OUT))


if __name__ == "__main__":
    main()
