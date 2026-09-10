#!/usr/bin/env python3
"""Materialize PPC5r9's typed proposal registries.

This is proposal-authoring machinery only. It performs no fixture execution,
model/tokenizer/embedding call, training, behavioral work, GPU work, seal,
claim, or release. The generated registries remain PROPOSAL_ONLY.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
R8 = ROOT.parent / "chg_20260905_public_pathway_consolidation_v5r8"
ARCH = "PPC5R9_PUBLIC_PATHWAY_CONSOLIDATION"
VERSION = 9
R8_CONTROLLER_SHA = "9dd0fd25a6951517986bf77b26bc37c6daf329d2c351426b15511bbb57ca6cbe"
R8_CAUSE_SHA = "6a16a1feb37489e36b4d478d58435c5770450564cfad6471c510b514ca99abbc"
FIRST_FAILURE = [
    "INTEGRITY", "PREDISPATCH_BUDGET", "MISSING_CALL", "TOKEN_LIMIT",
    "PARSE_ERROR", "LOGICAL_ALLOWANCE", "DOMAIN", "REFERENCE",
    "PREDICTION", "SCHEDULE", "PROVIDER_MISSING", "ENVIRONMENT_INVALID",
    "SUCCESS",
]


def compact(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode()


def digest(value) -> str:
    return hashlib.sha256(compact(value)).hexdigest()


def self_hash(value: dict) -> str:
    body = copy.deepcopy(value)
    body.pop("self_hash", None)
    prefix = (value["contract"].encode() + b"\0" + str(VERSION).encode()
              + b"\0" + value["artifact_type"].encode() + b"\0")
    return hashlib.sha256(prefix + compact(body)).hexdigest()


def finish(value: dict) -> dict:
    value["self_hash"] = self_hash(value)
    return value


def registry(kind: str, rows: list[dict]) -> dict:
    value = {
        "contract": f"ppc5.{kind.lower()}.v9",
        "schema_version": VERSION,
        "artifact_type": kind,
        "lifecycle_state": "PROPOSAL_ONLY",
        "producer_role": f"{kind}_AUTHOR",
        "architecture_id": ARCH,
        "registry_kind": kind,
        "ordered_row_keys": [row["row_key"] for row in rows],
        "rows": rows,
        "row_key_set_equality": True,
    }
    return finish(value)


def row(key: str, ordinal: int, role: str, producer: str,
        consumers: list[str], content, cardinality: str = "ONE") -> dict:
    return {
        "row_key": key,
        "ordinal": ordinal,
        "role": role,
        "cardinality": cardinality,
        "producer_role": producer,
        "consumer_stages": consumers,
        "content_sha256": digest(content),
    }


def raw_manifest(raw_role: str, relative_path: str) -> dict:
    path = REPO / relative_path
    raw = path.read_bytes()
    return finish({
        "contract": "ppc5.raw_byte_manifest.v9",
        "schema_version": VERSION,
        "artifact_type": "RAW_BYTE_MANIFEST",
        "lifecycle_state": "PROPOSAL_ONLY",
        "producer_role": "RAW_MANIFEST_BUILDER",
        "raw_role": raw_role,
        "media_type": "text/x-python" if path.suffix == ".py" else "application/json",
        "relative_path": relative_path,
        "byte_length": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
    })


def r8_json(name: str, expected: str):
    path = R8 / name
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise SystemExit(f"frozen r8 source mismatch: {name}")
    return json.loads(raw)


def controller_registry() -> dict:
    old = r8_json("controller_registry.json", R8_CONTROLLER_SHA)
    rows = []
    predicate_inputs = {"ANY_0_2": [0, 1, 2], "EQ_0": [0], "EQ_1": [1], "EQ_2": [2]}
    queue_capable_programs = {
        row["program"] for row in old["rows"] if row["queue_effect"] == "QUEUE"
    }
    for source in old["rows"]:
        transitions = []
        for result in source["result_transitions"]:
            for counter_input in predicate_inputs[result["counter_predicate"]]:
                error_terminal = result["accepted_result"] == "ERROR" and counter_input == 2
                explicit_terminal = result["next_phase"]["family"] == "TERMINAL"
                terminal = error_terminal or explicit_terminal
                update = result["counter_update"]
                if error_terminal:
                    counter_output = 3
                elif update == "RESET_ZERO":
                    counter_output = 0
                elif update == "PRESERVE":
                    counter_output = counter_input
                elif update == "INCREMENT":
                    counter_output = counter_input + 1
                else:
                    raise SystemExit(f"unknown counter update {update}")

                accepted = result["accepted_result"]
                ordinary_success = accepted not in {
                    "ERROR", "MODEL_MISSING_NO_RETRY", "PROVIDER_MISSING_NO_RETRY",
                    "DREAM_MISSING_NO_RETRY", "FLUSH_SKIPPED_REJECTED",
                }
                old_effect = source["queue_effect"]
                if source["queue_effect"] == "FLUSH":
                    queue_inputs = ["NONEMPTY"]
                elif source["program"] in queue_capable_programs:
                    queue_inputs = ["EMPTY", "NONEMPTY"]
                else:
                    queue_inputs = ["EMPTY"]
                for queue_input in queue_inputs:
                    if terminal:
                        has_outstanding = queue_input == "NONEMPTY"
                        effect = "FINALIZE_QUEUE" if has_outstanding else "NONE"
                        next_phase = "FINALIZE_QUEUE" if has_outstanding else "TERMINAL"
                        queue_output_rule = (
                            "FINALIZE_ALL_TO_EMPTY" if has_outstanding else "PRESERVE"
                        )
                    elif old_effect == "QUEUE" and ordinary_success:
                        effect = "ENQUEUE"
                        next_phase = result["next_phase"]["family"]
                        queue_output_rule = "SET_NONEMPTY"
                    elif old_effect == "FLUSH" and ordinary_success:
                        effect = "FLUSH"
                        next_phase = result["next_phase"]["family"]
                        queue_output_rule = "DECREMENT_ONE"
                    else:
                        effect = "NONE"
                        next_phase = result["next_phase"]["family"]
                        queue_output_rule = "PRESERVE"
                    transitions.append({
                        "accepted_result": accepted,
                        "counter_input": counter_input,
                        "counter_output": counter_output,
                        "queue_input_class": queue_input,
                        "queue_output_rule": queue_output_rule,
                        "normalized_result": "ERROR_LIMIT" if error_terminal else result["normalized_result"],
                        "next_phase": next_phase,
                        "next_index_rule": "NONE" if terminal else result["next_phase"]["index_rule"],
                        "terminal_reason": "ERROR_LIMIT" if error_terminal else result["next_phase"]["terminal_reason"],
                        "consume_call": result["consume_call"],
                        "advance_once": result["advance_once"],
                        "retry_allowed": result["retry_allowed"],
                        "endpoint_effect": result["endpoint_effect"],
                        "terminal_intent": terminal,
                        "result_specific_queue_effect": effect,
                    })
        phase = source["phase_pattern"]
        old_effect = source["queue_effect"]
        queue_precondition = (
            "CURRENT_SLOT_QUEUED" if old_effect == "FLUSH" else
            "OUTSTANDING_SET_MAY_EXIST" if old_effect == "DISCARD" else
            "NONE_REQUIRED"
        )
        rows.append({
            "row_key": source["row_id"],
            "assay_id": source["assay_id"],
            "program": source["program"],
            "phase_family": phase["family"],
            "phase_index_relation": phase["index_relation"],
            "bound_symbol": phase["bound_symbol"],
            "index_increment": phase["increment"],
            "boundary_phase": phase["boundary_phase"],
            "guard": phase["guard"],
            "dispatch_kind": source["dispatch_kind"],
            "required_operation": source["required_operation"],
            "input_debit": source["debit"],
            "declared_queue_operation": old_effect,
            "queue_precondition": queue_precondition,
            "result_transitions": transitions,
            "first_failure_order": FIRST_FAILURE,
        })
    state_tuples = [
        {
            "row_key": row["row_key"],
            "phase_index_relation": row["phase_index_relation"],
            "bound_symbol": row["bound_symbol"],
            "guard": row["guard"],
            "queue_precondition": row["queue_precondition"],
            "accepted_result": transition["accepted_result"],
            "counter_input": transition["counter_input"],
            "counter_output": transition["counter_output"],
            "queue_input_class": transition["queue_input_class"],
            "queue_output_rule": transition["queue_output_rule"],
            "normalized_result": transition["normalized_result"],
            "next_phase": transition["next_phase"],
            "terminal_intent": transition["terminal_intent"],
            "result_specific_queue_effect": transition["result_specific_queue_effect"],
        }
        for row in rows for transition in row["result_transitions"]
    ]
    return finish({
        "contract": "ppc5.controller_registry.v9",
        "schema_version": VERSION,
        "artifact_type": "CONTROLLER_REGISTRY",
        "lifecycle_state": "PROPOSAL_ONLY",
        "producer_role": "CONTROLLER_REGISTRY_AUTHOR",
        "architecture_id": ARCH,
        "terminal_error_count": 3,
        "dispatch_input_counts": [0, 1, 2],
        "queue_effect_is_result_specific": True,
        "rows": rows,
        "reachable_state_universe_sha256": digest(state_tuples),
        "reachable_state_count": len(state_tuples),
        "phase_rule_count": len(rows),
        "reachable_state_definition": "ONE_ROW_X_ONE_EXPLICIT_COUNTER_INPUT_X_ONE_ACCEPTED_RESULT_X_ONE_REACHABLE_QUEUE_CLASS",
        "zero_or_multiple_transition_matches_rejected": True,
    })


def cause_registry() -> dict:
    old = r8_json("transition_cause_registry.json", R8_CAUSE_SHA)
    rows = []
    for ordinal, source in enumerate(old["cause_roles"]):
        roles = [entry["role"] for entry in source["ordered_roles"]]
        rows.append({
            "cause": source["cause"],
            "ordinal": ordinal,
            "ordered_lineage_roles": roles,
            "content_sha256": digest(source),
        })
    return finish({
        "contract": "ppc5.transition_cause_registry.v9",
        "schema_version": VERSION,
        "artifact_type": "TRANSITION_CAUSE_REGISTRY",
        "lifecycle_state": "PROPOSAL_ONLY",
        "producer_role": "TRANSITION_CAUSE_REGISTRY_AUTHOR",
        "architecture_id": ARCH,
        "rows": rows,
        "cause_order": [row["cause"] for row in rows],
        "exact_cardinality": True,
    })


def generic_registries() -> dict[str, dict]:
    status = json.loads((ROOT / "status_contract.json").read_text())
    analysis = json.loads((ROOT / "analysis_contract.json").read_text())
    claims = json.loads((ROOT / "claim_dependency_map.json").read_text())
    authority = json.loads((ROOT / "authority_contract.json").read_text())
    inventory = json.loads((ROOT / "object_inventory.json").read_text())

    status_rows = [
        row(rule["rule_id"], i, rule["status"], "STATUS_CONTRACT_AUTHOR",
            ["CONTROLLER", "ANALYSIS", "COLD_REPLAY"], rule)
        for i, rule in enumerate(status["rules"])
    ]

    gate_source = []
    for assay in ("D1A", "D1B", "D1C", "D1D"):
        for gate in analysis["gates"][assay]:
            gate_source.append((assay, gate))
    gate_rows = []
    for i, (assay, gate) in enumerate(gate_source):
        key = gate["gate_id"].split("[")[0] + ("_TEMPLATE" if "[" in gate["gate_id"] else "")
        gate_rows.append(row(key, i, assay, "GATE_REGISTRY_AUTHOR",
                             ["PRE_ENTROPY_DESIGN", "ANALYSIS", "T13", "COLD_REPLAY"], gate,
                             "ORDERED_EXACT" if "[" in gate["gate_id"] else "ONE"))

    evidence_specs = [
        ("DIRECT_PUBLIC_ACQUIRE", "POSITIVE_EVIDENCE", ["EVIDENCE_GATE", "WRITER"]),
        ("DREAM_NOMINEE", "ROOT_POLICY_INPUT", ["EVIDENCE_GATE"]),
        ("DREAM_PROSE", "FORBIDDEN_POSITIVE_EVIDENCE", ["EVIDENCE_GATE", "WRITER", "TRAINER"]),
        ("PROBE_FUTURE_TARGET", "FORBIDDEN_POSITIVE_EVIDENCE", ["EVIDENCE_GATE", "WRITER", "TRAINER"]),
        ("SCORER_OUTPUT", "FORBIDDEN_POSITIVE_EVIDENCE", ["EVIDENCE_GATE", "WRITER", "TRAINER"]),
        ("LIFE_GATE_AGGREGATE", "ANALYSIS_UNIT", ["ANALYSIS", "T13", "COLD_REPLAY"]),
        ("D1A_CONTROL_SET_MANIFEST", "CONTROL_CLOSURE", ["JOINT_POWER", "T13", "COLD_REPLAY"]),
        ("MODEL_VIEW_MANIFEST", "REPLAY_CLOSURE", ["COLD_REPLAY"]),
    ]
    evidence_rows = [
        row(key, i, role, "EVIDENCE_ROLE_REGISTRY_AUTHOR", consumers,
            {"key": key, "role": role, "consumers": consumers})
        for i, (key, role, consumers) in enumerate(evidence_specs)
    ]

    dependency_specs = [
        ("DESIGN_TO_ENTROPY", "PRE_ENTROPY_DESIGN_LOCK", "ENTROPY_ACQUISITION_RECEIPT"),
        ("ENTROPY_TO_LIFE", "ENTROPY_ACQUISITION_RECEIPT", "LIFE_SAMPLE_RECEIPT"),
        ("LIFE_TO_POPULATED", "LIFE_SAMPLE_RECEIPT", "POPULATED_RUN_LOCK"),
        ("POPULATED_TO_TESTS", "POPULATED_RUN_LOCK", "TEST_RESULT"),
        ("TESTS_TO_T13", "TEST_RESULT", "T13_PREMODEL_TECHNICAL_GATE"),
        ("T13_TO_HUMAN_RUN", "T13_PREMODEL_TECHNICAL_GATE", "HUMAN_RUN_RATIFICATION_RECEIPT"),
        ("HUMAN_RUN_TO_PREMODEL", "HUMAN_RUN_RATIFICATION_RECEIPT", "PRE_MODEL_AUTHORITY_RECEIPT"),
        ("ROUTE_TO_PROJECTION", "PRIVILEGED_ROUTE_RECEIPT", "SANITIZED_RESPONSE_PROJECTION"),
        ("PROJECTION_TO_EMISSION", "SANITIZED_RESPONSE_PROJECTION", "INTERVENTION_EMISSION_RECEIPT"),
        ("EMISSION_TO_VIEW", "INTERVENTION_EMISSION_RECEIPT", "MODEL_VIEW"),
        ("ANALYSIS_TO_CANDIDATE", "ANALYSIS_BUNDLE", "CANDIDATE_DECISION_RECEIPT"),
        ("CANDIDATE_TO_REPLAY", "CANDIDATE_DECISION_RECEIPT", "COLD_REPLAY_RECEIPT"),
        ("REPLAYS_TO_T14", "COLD_REPLAY_RECEIPT", "T14_FINAL_REPLAY_RESULT"),
        ("T14_TO_PRECLAIM", "T14_FINAL_REPLAY_RESULT", "PRECLAIM_AUTHORITY_RECEIPT"),
        ("PRECLAIM_TO_RELEASE", "PRECLAIM_AUTHORITY_RECEIPT", "CLAIM_RELEASE_PACKAGE"),
    ]
    dependency_rows = [
        row(key, i, key, "DEPENDENCY_REGISTRY_AUTHOR", [target],
            {"source": source, "target": target})
        for i, (key, source, target) in enumerate(dependency_specs)
    ]

    claim_source = [*claims["claims"], claims["intersection"]]
    claim_rows = [
        row(item["claim_id"], i, "CLAIM_LITERAL", "CLAIM_REGISTRY_AUTHOR",
            ["CANDIDATE_DECISION", "CLAIM_RELEASE", "AUDIT"], item["release_text"])
        for i, item in enumerate(claim_source)
    ]

    resource_names = [
        "MODEL_CALLS", "PROVIDER_CALLS", "INPUT_TOKENS", "OUTPUT_TOKENS",
        "TRAINING_TOKENS", "TRAINING_UPDATES", "CPU_SECONDS", "GPU_SECONDS",
        "WALL_SECONDS", "PERSISTED_BYTES",
    ]
    resource_rows = [
        row(name, i, "DESCRIPTIVE_COST_ONLY", "RESOURCE_REGISTRY_AUTHOR",
            ["RESOURCE_ACCOUNTING", "ANALYSIS", "CLAIM_RELEASE"], name)
        for i, name in enumerate(resource_names)
    ]

    dispatch_rows = [
        row(name, i, "ALLOWED_DISPATCH_CLASS", "ALLOWED_DISPATCH_REGISTRY_AUTHOR",
            ["PRE_MODEL_AUTHORITY", "PREFLIGHT"], name)
        for i, name in enumerate(authority["dispatch_classes"])
    ]
    authority_rows = [
        row(stage["stage"], i, "AUTHORITY_STAGE", "AUTHORITY_REGISTRY_AUTHOR",
            ["T13", "PREFLIGHT", "COLD_REPLAY"], stage)
        for i, stage in enumerate(authority["stages"])
    ]

    binding_rows = []
    for artifact in inventory["objects"]:
        for binding in artifact["reference_bindings"]:
            source = artifact["type"]
            key = f'DEP_{source}_{binding["consumer_type"]}_{len(binding_rows):04d}'
            binding_rows.append(row(key, len(binding_rows), binding["role"],
                                    artifact["producer_role"], [binding["consumer_stage"]],
                                    {"source_type": source, **binding}, binding["cardinality"]))
    # The dependency registry is the complete typed reference-edge registry;
    # the small causal chain above is retained as evidence-role rows instead
    # of becoming a second authority for the same schema edges.
    dependency_rows = binding_rows

    result = {
        "status_registry.json": registry("STATUS_REGISTRY", status_rows),
        "gate_registry.json": registry("GATE_REGISTRY", gate_rows),
        "evidence_role_registry.json": registry("EVIDENCE_ROLE_REGISTRY", evidence_rows),
        "dependency_registry.json": registry("DEPENDENCY_REGISTRY", dependency_rows),
        "resource_registry.json": registry("RESOURCE_REGISTRY", resource_rows),
        "allowed_dispatch_registry.json": registry("ALLOWED_DISPATCH_REGISTRY", dispatch_rows),
        "authority_registry.json": registry("AUTHORITY_REGISTRY", authority_rows),
    }

    claim_registry = registry("CLAIM_REGISTRY", claim_rows)
    claim_variants = json.loads((ROOT / "contracts.schema.json").read_text())["$defs"]["claim_rendering"]["oneOf"]
    claim_registry["claim_renderings"] = []
    for variant in claim_variants:
        rendering = {}
        for key, spec in variant["properties"].items():
            if key == "ordered_inseparable_segments":
                rendering[key] = [item["const"] for item in spec["prefixItems"]]
            elif "const" in spec:
                rendering[key] = spec["const"]
            elif spec.get("type") == "null":
                rendering[key] = None
            else:
                raise SystemExit(f"unsupported claim-rendering field: {key}")
        claim_registry["claim_renderings"].append(rendering)
    claim_registry["self_hash"] = self_hash(claim_registry)
    result["claim_registry.json"] = claim_registry
    return result


def visibility_registry(raw_manifests: dict[str, dict]) -> dict:
    schema = json.loads((ROOT / "contracts.schema.json").read_text())
    props = schema["$defs"]["visibility_registry"]["properties"]
    def ref(name: str, role: str):
        return {"role": role, "ordinal": 0, "artifact_type": "RAW_BYTE_MANIFEST",
                "self_hash": raw_manifests[name]["self_hash"]}
    return finish({
        "contract": "ppc5.visibility_registry.v9",
        "schema_version": VERSION,
        "artifact_type": "VISIBILITY_REGISTRY",
        "lifecycle_state": "PROPOSAL_ONLY",
        "producer_role": "VISIBILITY_REGISTRY_AUTHOR",
        "architecture_id": ARCH,
        "information_item_order": props["information_item_order"]["const"],
        "stage_order": props["stage_order"]["const"],
        "cells": props["cells"]["const"],
        "allowed_edges": props["allowed_edges"]["const"],
        "allowed_edge_count": 84,
        "r8_preexisting_allowed_edge_count": 83,
        "sole_emission_to_think_role": "INTERVENTION_EMISSION_TO_PUBLIC_VIEW",
        "schema_edge_extractor_ref": ref("raw_schema_edge_extractor_manifest.json", "RAW_SCHEMA_EDGE_EXTRACTOR"),
        "inventory_edge_extractor_ref": ref("raw_inventory_edge_extractor_manifest.json", "RAW_INVENTORY_EDGE_EXTRACTOR"),
        "visibility_edge_extractor_ref": ref("raw_visibility_edge_extractor_manifest.json", "RAW_VISIBILITY_EDGE_EXTRACTOR"),
        "audit_only_exclusions": [],
    })


def contract_schema_registry(raw_manifest: dict) -> dict:
    schema = json.loads((ROOT / "contracts.schema.json").read_text())
    types = [ref.rsplit("/", 1)[1].upper() for ref in
             (entry["$ref"] for entry in schema["oneOf"])]
    return finish({
        "contract": "ppc5.contract_schema_registry.v9",
        "schema_version": VERSION,
        "artifact_type": "CONTRACT_SCHEMA_REGISTRY",
        "lifecycle_state": "PROPOSAL_ONLY",
        "producer_role": "CONTRACT_SCHEMA_EXTRACTOR",
        "architecture_id": ARCH,
        "registry_kind": "CONTRACT_SCHEMA_REGISTRY",
        "raw_schema_ref": {"role": "RAW_CONTRACT_SCHEMA", "ordinal": 0,
                           "artifact_type": "RAW_BYTE_MANIFEST",
                           "self_hash": raw_manifest["self_hash"]},
        "schema_id": "ppc5r9-contracts.schema.json",
        "top_level_artifact_types": types,
        "local_refs_recursively_closed": True,
        "unknown_type_policy": "REJECT",
    })


def all_outputs() -> dict[str, dict]:
    base = str(ROOT.relative_to(REPO))
    raw_specs = {
        "raw_contract_schema_manifest.json": ("RAW_CONTRACT_SCHEMA", f"{base}/contracts.schema.json"),
        "raw_schema_edge_extractor_manifest.json": ("RAW_SCHEMA_EDGE_EXTRACTOR", f"{base}/drafts/extract_schema_visibility_edges.py"),
        "raw_inventory_edge_extractor_manifest.json": ("RAW_INVENTORY_EDGE_EXTRACTOR", f"{base}/drafts/extract_inventory_visibility_edges.py"),
        "raw_visibility_edge_extractor_manifest.json": ("RAW_VISIBILITY_EDGE_EXTRACTOR", f"{base}/drafts/extract_contract_visibility_edges.py"),
    }
    raw = {name: raw_manifest(role, path) for name, (role, path) in raw_specs.items()}
    outputs = {
        "controller_registry.json": controller_registry(),
        "transition_cause_registry.json": cause_registry(),
        **generic_registries(),
        **raw,
    }
    outputs["visibility_registry.json"] = visibility_registry(raw)
    outputs["contract_schema_registry.json"] = contract_schema_registry(raw["raw_contract_schema_manifest.json"])
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = all_outputs()
    stale = []
    for name, value in outputs.items():
        expected = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text() != expected:
                stale.append(name)
        else:
            path.write_text(expected)
    if stale:
        raise SystemExit("stale registry outputs: " + ", ".join(stale))
    print(("verified" if args.check else "wrote") + f" {len(outputs)} typed proposal registries/manifests")


if __name__ == "__main__":
    main()
