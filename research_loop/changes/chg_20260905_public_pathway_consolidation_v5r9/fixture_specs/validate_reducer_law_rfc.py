#!/usr/bin/env python3
"""Static validator for REDUCER_LAW_RFC.json.

This validates proposal bytes only. It neither authors nor executes fixtures.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RFC_PATH = HERE / "REDUCER_LAW_RFC.json"
VECTOR_PATH = HERE / "VECTOR_FIXTURE_RFC.json"

REQUIRED_LAW_FIELDS = {
    "law_id", "test_id", "suite_id", "entry_count", "input_table",
    "algorithm", "output_shape", "failure_precedence_ref", "source_bindings",
}

T08_INFLUENCE_FIELDS = [
    "emitted_public_bytes", "condition", "source", "match_keys",
    "provider_scores", "nonce", "mapping",
]

T13_STAGES = [
    "ARCHITECTURE_RATIFICATION", "PRE_ENTROPY_DESIGN",
    "ENTROPY_ACQUISITION", "PROPOSAL_REALIZATION", "LIFE_REALIZATION",
    "SAFETY_RESOLUTION", "POPULATED_RUN", "CPU_CONFORMANCE",
    "T13_TECHNICAL_GATE", "HUMAN_RUN_RATIFICATION",
    "PRE_MODEL_EXECUTION", "DISPATCH_PREFLIGHT", "RUNTIME_VALIDITY",
    "PRE_SCIENTIFIC_CLAIM",
]

T13_INBOUND_ROLES = [
    "NON_OVERRIDING_ADVOCATE", "CONDITIONAL_COMPLETE_RELEASE_POWER",
    "CPU_CONFORMANCE", "T13_FIXTURE_EXECUTION_MANIFEST_A",
    "T13_FIXTURE_EXECUTION_MANIFEST_B", "T13_FIXTURE_SET_EQUALITY",
    "FIXTURE_SPEC", "JOINT_CONSTRUCTION_RELEASE_POWER",
    "POPULATED_RUN_LOCK", "INDEPENDENT_REVIEW", "STATIC_SEAL_PAIR",
    "GENERIC_T01_INTAKE_EVIDENCE",
]

T14_ROLES = [
    *[f"PPC5R9_T{i:02d}_RESULT" for i in range(2, 14)],
    "PRE_ENTROPY_DESIGN_LOCK", "ENTROPY_ACQUISITION",
    "POPULATED_RUN_LOCK", "STATIC_SEAL_PAIR", "REVIEW_RECEIPT",
    "ADVOCATE_RECEIPT", "COMPLETE_RUN_MANIFEST", "ANALYSIS_BUNDLE",
    "D1A_CONTROL_SET_MANIFEST", "COMPLETE_MODEL_VIEW_MANIFEST",
    "ROUTE_LINEAGE_AUDIT", "PROVIDER_AUDIT",
]


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def pointer_get(document: object, pointer: str) -> object:
    current = document
    if not pointer:
        return current
    assert pointer.startswith("/"), pointer
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        else:
            assert isinstance(current, dict), (pointer, token)
            current = current[token]
    return current


def assert_source_binding(binding: str) -> None:
    filename, marker, pointer = binding.partition("#")
    path = ROOT / filename
    assert path.is_file(), binding
    if marker:
        try:
            pointer_get(load(path), pointer)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise AssertionError(f"invalid source binding {binding}: {exc}") from exc


def inventory_inbound_roles(inventory: dict, consumer_type: str) -> list[str]:
    rows = []
    for producer in inventory["objects"]:
        for edge in producer.get("reference_bindings", []):
            if edge["consumer_type"] == consumer_type:
                rows.append((edge["field_path"], str(edge["ordinal"]),
                             producer["type"], edge["role"]))
    return [row[3] for row in sorted(rows)]


def main() -> None:
    rfc = load(RFC_PATH)
    vector = load(VECTOR_PATH)
    inputs = load(HERE / "REDUCER_INPUT_ROWS_RFC.json")
    programs = load(HERE / "REDUCER_PROGRAMS_RFC.json")
    snapshots = load(HERE / "REDUCER_SOURCE_SNAPSHOTS.json")
    exact_bindings = load(HERE / "REDUCER_EXACT_SOURCE_BINDINGS_RFC.json")
    inventory = load(ROOT / "object_inventory.json")
    authority = load(ROOT / "authority_registry.json")

    assert rfc["document_kind"] == "PPC5R9_REDUCER_LAW_CATALOG_RFC"
    assert rfc["lifecycle_state"] == "PROPOSAL_ONLY"
    assert rfc["authority_conferred"] is False
    assert rfc["materializes_fixtures"] is False
    machine = rfc["normative_machine_contract"]
    for key in ("facts_only_input_catalog", "closed_output_and_program_catalog",
                "source_pointer_snapshots", "exact_source_bindings",
                "reference_semantics_validator"):
        ref = machine[key]
        path = HERE / ref["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == ref["raw_sha256"], key
    assert rfc["executor_projection"]["canonical_contract"] == \
        "VECTOR_FIXTURE_RFC.json#/executor_input_envelope"
    assert rfc["executor_projection"]["included"] == \
        vector["executor_input_envelope"]["required"]
    dispatch = programs["executable_dispatch"]
    assert dispatch["function"] == "reduce_rows"
    assert hashlib.sha256((HERE / dispatch["file"]).read_bytes()).hexdigest() == \
        dispatch["raw_sha256"]
    envelope_schema = programs["closed_output_envelope"]
    assert envelope_schema["$schema"].endswith("2020-12/schema")
    assert envelope_schema["additionalProperties"] is False

    expected = {}
    for test_id, suites in vector["suite_vectors"].items():
        if test_id < "PPC5R9_T04":
            continue
        for suite in suites:
            key = (test_id, suite["suite_id"])
            assert key not in expected, key
            expected[key] = suite["entry_count"]
    assert len(expected) == 58

    actual = {}
    law_ids = set()
    banned_input_keys = {
        "expected_output", "expected_result", "expected_first_failure",
        "oracle_output", "answer_key",
    }
    rendered = json.dumps(rfc, sort_keys=True)
    assert "relation_holds" not in rendered
    assert "generic PASS" not in rendered

    for law in rfc["laws"]:
        missing = REQUIRED_LAW_FIELDS - set(law)
        assert not missing, (law.get("law_id"), sorted(missing))
        assert law["law_id"] not in law_ids, law["law_id"]
        law_ids.add(law["law_id"])
        key = (law["test_id"], law["suite_id"])
        assert key not in actual, key
        actual[key] = law["entry_count"]
        assert isinstance(law["entry_count"], int) and law["entry_count"] > 0
        assert isinstance(law["algorithm"], list) and law["algorithm"]
        assert all(isinstance(step, str) and step.strip()
                   for step in law["algorithm"])
        assert law["output_shape"].get("additional_fields") is False
        assert law["output_shape"].get("fields")
        assert law["failure_precedence_ref"] == law["test_id"]
        assert law["failure_precedence_ref"] in rfc["test_failure_orders"]
        assert law["input_table"].get("name")
        assert law["input_table"].get("columns")
        input_text = json.dumps(law["input_table"], sort_keys=True)
        assert not any(key_name in input_text for key_name in banned_input_keys), law["law_id"]
        for binding in law["source_bindings"]:
            assert_source_binding(binding)

    assert actual == expected, {
        "missing": sorted(set(expected) - set(actual)),
        "extra": sorted(set(actual) - set(expected)),
        "wrong_counts": sorted(
            (key, expected[key], actual.get(key))
            for key in set(expected) & set(actual)
            if expected[key] != actual[key]
        ),
    }
    assert len(law_ids) == 58
    assert sum(actual.values()) == 1113
    assert rfc["self_audit_requirements"]["exact_law_count"] == 58
    assert rfc["self_audit_requirements"]["entry_count_sum"] == 1113
    assert {row["law_id"] for row in inputs["builders"]} == law_ids
    assert {row["law_id"] for row in programs["programs"]} == law_ids
    assert len(inputs["builders"]) == len(programs["programs"]) == 58
    for program in programs["programs"]:
        assert len(program["output_columns"]) == len(program["output_types"])
        assert len(program["output_columns"]) == len(set(program["output_columns"]))
        assert set(program["output_types"]) <= set(programs["type_schemas"])
    assert len({row["source_id"] for row in snapshots["snapshots"]}) == len(snapshots["snapshots"])
    law_bindings = sorted({binding for law in rfc["laws"]
                           for binding in law["source_bindings"]})
    assert exact_bindings["binding_count"] == len(law_bindings) == 110
    assert [row["binding"] for row in exact_bindings["bindings"]] == law_bindings
    for row in exact_bindings["bindings"]:
        filename, marker, pointer = row["binding"].partition("#")
        value = pointer_get(load(ROOT / filename), pointer if marker else "")
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode()
        assert hashlib.sha256(raw).hexdigest() == row["pointer_value_sha256"]

    route = next(law for law in rfc["laws"] if law["law_id"] == "T08_ROUTE_V1")
    route_text = " ".join(route["algorithm"])
    for fragment in [
        "TARGET with zero or multiple matches produces RUN_INVALID",
        "TARGET with exactly one match produces INTERVENTION",
        "NON_TARGET with zero matches produces OFF_PATH_AUTHENTIC_PASS_THROUGH",
        "public_continuation=false",
    ]:
        assert fragment in route_text, fragment

    influence = next(law for law in rfc["laws"]
                     if law["law_id"] == "T08_INFLUENCE_RELATION_V1")
    assert influence["input_table"]["one_field_pairs"] == T08_INFLUENCE_FIELDS
    queue = next(law for law in rfc["laws"]
                 if law["law_id"] == "T08_QUEUE_OUTCOME_V1")
    queue_text = " ".join(queue["algorithm"])
    assert "slot 0 discard_count=1 and slot 1 discard_count=1" in queue_text
    assert "do not reduce this to one total effect" in queue_text
    t08_builders = [row for row in inputs["builders"]
                    if row["law_id"].startswith("T08_")]
    forbidden_t08_input = {"left_emission", "right_emission", "left_public_state",
                           "right_public_state", "left_model_view", "right_model_view",
                           "terminal_intent", "discard_events"}
    def input_keys(value):
        if isinstance(value, dict):
            return set(value) | set().union(*(input_keys(v) for v in value.values()), set())
        if isinstance(value, list):
            return set().union(*(input_keys(v) for v in value), set())
        return set()
    for builder in t08_builders:
        assert not (input_keys(builder) & forbidden_t08_input), builder["law_id"]

    topology = next(law for law in rfc["laws"]
                    if law["law_id"] == "T13_AUTHORITY_TOPOLOGY_V1")
    assert topology["topology_contract"]["exact_stage_order"] == T13_STAGES
    t13_edges = topology["topology_contract"]["t13_inbound_edges"]
    assert [edge["role"] for edge in t13_edges] == T13_INBOUND_ROLES
    assert [row["row_key"] for row in authority["rows"]] == T13_STAGES
    assert [row["ordinal"] for row in authority["rows"]] == list(range(14))
    assert inventory_inbound_roles(inventory, "T13_PREMODEL_TECHNICAL_GATE") == sorted(
        T13_INBOUND_ROLES,
        key=lambda role: next(
            (edge["field_path"], str(edge["ordinal"]), producer["type"])
            for producer in inventory["objects"]
            for edge in producer.get("reference_bindings", [])
            if edge["consumer_type"] == "T13_PREMODEL_TECHNICAL_GATE"
            and edge["role"] == role
        ),
    )

    inventory_t13_edges = []
    for producer in inventory["objects"]:
        for edge in producer.get("reference_bindings", []):
            if edge["consumer_type"] == "T13_PREMODEL_TECHNICAL_GATE":
                inventory_t13_edges.append({
                    "producer_type": producer["type"],
                    "consumer_type": edge["consumer_type"],
                    "consumer_stage": edge["consumer_stage"],
                    "field_path": edge["field_path"],
                    "role": edge["role"],
                    "ordinal": edge["ordinal"],
                    "cardinality": edge["cardinality"],
                })
    assert t13_edges == sorted(inventory_t13_edges,
                               key=lambda edge: (edge["field_path"], str(edge["ordinal"]), edge["producer_type"]))
    external = topology["topology_contract"]["external_t14_authority_edge"]
    assert external in [
        {"producer_type": producer["type"], "consumer_type": edge["consumer_type"],
         "consumer_stage": edge["consumer_stage"], "field_path": edge["field_path"],
         "role": edge["role"], "ordinal": edge["ordinal"],
         "cardinality": edge["cardinality"]}
        for producer in inventory["objects"]
        for edge in producer.get("reference_bindings", [])
    ]

    replay = next(law for law in rfc["laws"]
                  if law["law_id"] == "T14_FULL_PREDECESSOR_REPLAY_V1")
    replay_predecessors = replay["replay_graph_contract"]["exact_ordered_predecessors"]
    assert [row["role"] for row in replay_predecessors] == T14_ROLES
    assert [row["ordinal"] for row in replay_predecessors] == list(range(24))
    assert all(row["cardinality"] == "ONE" for row in replay_predecessors)
    derived_edges = [
        {"producer_type": producer["type"], **edge}
        for producer in inventory["objects"]
        for edge in producer.get("reference_bindings", [])
    ]
    membership = replay["replay_graph_contract"]["schema_derived_membership"]
    cold = [edge for edge in derived_edges if edge["consumer_type"] == "COLD_REPLAY_RECEIPT"]
    final = [edge for edge in derived_edges if edge["consumer_type"] == "T14_FINAL_REPLAY_RESULT"]
    outbound = [edge for edge in derived_edges if edge["producer_type"] == "T14_FINAL_REPLAY_RESULT"
                and edge["consumer_type"] == "PRECLAIM_AUTHORITY_RECEIPT"]
    assert len(cold) == membership["cold_replay_ingress_count"] == 11
    assert sorted(edge["role"] for edge in cold) == sorted(membership["cold_replay_ingress_roles"])
    assert len(final) == membership["final_ingress_count"] == 6
    assert sorted(edge["role"] for edge in final) == sorted(membership["final_ingress_roles"])
    assert len(outbound) == membership["outbound_count"] == 1
    assert outbound[0]["role"] == membership["outbound_role"]
    assert len(T14_ROLES) == 24 and len(set(T14_ROLES)) == 24
    replay_text = " ".join(replay["algorithm"])
    for fragment in [
        "release_bytes_consumed=false", "distinct implementation hashes",
        "COLD_REPLAY_A ordinal 0", "COLD_REPLAY_B ordinal 1",
        "exactly one outbound FINAL_T14_RESULT edge",
    ]:
        assert fragment in replay_text, fragment

    digest = hashlib.sha256(RFC_PATH.read_bytes()).hexdigest()
    print(json.dumps({
        "status": "PASS",
        "law_count": len(law_ids),
        "suite_entry_count": sum(actual.values()),
        "t13_stage_count": len(T13_STAGES),
        "t13_inbound_edge_count": len(T13_INBOUND_ROLES),
        "t14_predecessor_role_count": len(T14_ROLES),
        "reducer_law_rfc_sha256": digest,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
