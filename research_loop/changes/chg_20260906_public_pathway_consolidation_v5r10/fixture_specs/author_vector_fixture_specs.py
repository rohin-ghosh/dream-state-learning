#!/usr/bin/env python3
"""Proposal-only contract for the PPC5r9 vector fixture replacement.

This source does not materialize or execute fixtures.  It freezes exact
P/N/Q counts, suite-vector coverage, safe negative pruning, case identity,
and the executor-only projection.  Concrete graph/output bytes remain a
hard precondition; absent bytes cause refusal rather than runtime invention.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
RFC = HERE / "VECTOR_FIXTURE_RFC.json"

COUNTS = {
    "PPC5R9_T02": (61, 168, 19),
    "PPC5R9_T03": (346, 1469, 25),
    "PPC5R9_T04": (6, 109, 1),
    "PPC5R9_T05": (4, 27, 1),
    "PPC5R9_T06": (5, 72, 1),
    "PPC5R9_T07": (5, 71, 1),
    "PPC5R9_T08": (6, 64, 1),
    "PPC5R9_T09": (3, 138, 1),
    "PPC5R9_T10": (5, 81, 1),
    "PPC5R9_T11": (13, 67, 1),
    "PPC5R9_T12": (7, 43, 1),
    "PPC5R9_T13": (3, 62, 1),
    "PPC5R9_T14": (1, 96, 1),
}

SUITE_ENTRY_COUNTS = {
    "PPC5R9_T04": [("DREAM_REDUCER", 10), ("CONTEXT_STATUS", 15),
                    ("TYPED_DEPENDENCY", 3), ("LIFE_AGGREGATE_MEMBERSHIP", 4),
                    ("EMISSION_METAMORPHIC", 7), ("MODEL_DISPATCH_CHAIN", 1)],
    "PPC5R9_T05": [("CAUSAL_NUMERIC", 9), ("CAUSAL_MOUNT", 2),
                    ("DESCRIPTIVE_PROVIDER", 10), ("TYPED_REGISTRY", 13)],
    "PPC5R9_T06": [("PER_LIFE_CONTROL", 6), ("MANIFEST_CLOSURE", 1),
                    ("ALLOWED_PROJECTION", 3), ("POINTWISE_POWER_BINDING", 1),
                    ("PRE_ENTROPY_ANCESTRY", 1)],
    "PPC5R9_T07": [("FULL_PATH", 2), ("PROPER_SUBSET", 8),
                    ("ALTERNATE_PATH", 2), ("EDGE_ARTIFACT", 30), ("CLOSURE", 4)],
    "PPC5R9_T08": [("ROUTE", 4), ("INFLUENCE_RELATION", 7),
                    ("QUEUE_OUTCOME", 4), ("OPAQUE_ALLOCATION", 1),
                    ("AUDIT_SPLIT", 2), ("DISPATCH_CLOSURE", 1)],
    "PPC5R9_T09": [("DREAM_CONTEXT_PROGRAM", 60), ("STATUS_RULE", 43),
                    ("STATUS_PRECEDENCE", 15)],
    "PPC5R9_T10": [("ROOT_STATUS", 13), ("REACHABLE_D1D_PIPELINE", 24),
                    ("DISPATCH_CHAIN", 3), ("RESOURCE", 5), ("D1D_QUALIFICATION", 1)],
    "PPC5R9_T11": [("LIFE_GATE_AGGREGATE", 8), ("PAIRED_BOUNDARY", 4),
                    ("SAFETY", 6), ("MISSINGNESS", 3), ("CP_BRACKET", 6),
                    ("IUT_CRITICAL_COUNT", 9), ("HOLM_PERMUTATION", 24),
                    ("HOLM_TIE", 1), ("HOLM_STOP", 5), ("CLAIM_BYTES", 5),
                    ("CONSTRUCTION_PROOF", 2), ("POWER", 6),
                    ("SAFETY_TEMPLATE_RESOLUTION", 1)],
    "PPC5R9_T12": [("VISIBILITY_CELL", 195), ("TYPED_SCHEMA_EDGE", 363),
                    ("OBJECT_TYPE", 84), ("TYPED_REGISTRY", 13),
                    ("TRANSITION_CAUSE", 7), ("PREFLIGHT_DENIAL", 8),
                    ("THREE_WAY_EQUALITY", 1)],
    "PPC5R9_T13": [("FULL_TECHNICAL_PASS", 1), ("PREFLIGHT_DENIAL", 8),
                    ("AUTHORITY_TOPOLOGY", 14)],
    "PPC5R9_T14": [("FULL_PREDECESSOR_REPLAY", 24)],
}

NEGATIVE_FAMILIES = {
    "PPC5R9_T04": [("DREAM_BRANCH",10),("CONTEXT_CELL",45),("TYPED_CONTEXT_REF",12),
                    ("LIFE_MEMBERSHIP",7),("EMISSION_INFLUENCE",7),
                    ("RAW_RENDER_DEBIT_STATUS",5),("DISPATCH_BINDING",23)],
    "PPC5R9_T05": [("NUMERIC_TABLE",12),("MOUNT",4),("DESCRIPTIVE_CAUSAL_FIELD",3),
                    ("PROVIDER_AUDIT",2),("REGISTRY_PROPERTY_OPERATION_VECTOR",6)],
    "PPC5R9_T06": [("WRONG_LIFE_DIMENSION",16),("FORBIDDEN_MATCH_INPUT",5),
                    ("STERILE_SOURCE",7),("DERANGEMENT_PRESERVATION",9),
                    ("PER_LIFE_MANIFEST",8),("MANIFEST_SHAPE",4),
                    ("DESCENDANT_BACKREF",3),("DOSE_MISMATCH",4),
                    ("POINTWISE_BINDING",1),("TEMPORAL",3),("PRIVILEGED_TAINT",12)],
    "PPC5R9_T07": [("ORACLE_FLIP",12),("SOURCE_ID_PREIMAGE",10),("CUT_BYTES",5),
                    ("TWIN",15),("SHAM",20),("SOURCE_COLLISION",1),("CLOSURE",4),
                    ("REF_OMIT_VECTOR",1),("REF_EXTRA_VECTOR",1),
                    ("REF_REORDER_VECTOR",1),("REF_WRONG_TARGET_VECTOR",1)],
    "PPC5R9_T08": [("ROUTE",6),("FORBIDDEN_PROJECTION_FIELD",6),
                    ("NONCE_COMMITMENT",5),("EMISSION",4),("AUDIT",6),
                    ("QUEUE",8),("SCHEDULE",6),("DISPATCH_VIEW_BINDING",23)],
    "PPC5R9_T09": [("STATUS_RAW_RESULT",43),("PROGRAM_CELL",60),
                    ("DISPATCH_BINDING",23),("DEPENDENCY_REF",12)],
    "PPC5R9_T10": [("PIPELINE_ADJUSTMENT",24),("DISPATCH_BINDING",23),
                     ("PRIVILEGED_INFLUENCE",6),("RESOURCE",6),
                     ("ROOT_STATUS",13),("QUALIFICATION",9)],
    "PPC5R9_T11": [("AGGREGATE",9),("SAFETY_TEMPLATE",5),("POINTWISE_SUPPORT",13),
                     ("RATIONAL",6),("PAIRED",4),("SAFETY",4),("MISSINGNESS",3),
                     ("HOLM",8),("CLAIM_LITERAL",10),("CONSTRUCTION_PROOF",4),
                     ("GLOBAL_POWER",1)],
    "PPC5R9_T12": [("VISIBILITY_OPERATION_VECTOR",8),("TYPED_EDGE_OPERATION_VECTOR",7),
                     ("OBJECT_INVENTORY_OPERATION_VECTOR",4),("REGISTRY_PROPERTY_OPERATION_VECTOR",6),
                     ("TRANSITION_CAUSE_OPERATION_VECTOR",3),("DISTINCT_PREFLIGHT_DENIALS",8),
                     ("CROSS_CONTRACT_CLOSURE",7)],
    "PPC5R9_T13": [("NARROW_T01",7),("T02_T12_SET_VECTOR_OPERATION",5),
                     ("REGISTRY_PROPERTY_OPERATION_VECTOR",6),("TEMPORAL_DESIGN_EDGE",12),
                     ("CLOSURE",12),("SEAL_REVIEW",8),("FORBIDDEN_FUTURE_INPUT",2),
                     ("AUTHORITY_ALIAS",1),("AUTHORITY_BACKEDGE",1),("DENIAL",8)],
    "PPC5R9_T14": [("PREDECESSOR_VECTOR_OPERATION",5),("CAUSE_TABLE_OPERATION",3),
                     ("QUEUE",6),("AUDIT",6),("INFLUENCE",7),("DISPATCH_BINDING",23),
                     ("DREAM_SLEEP",5),("LIFE_ANALYSIS",8),("CANDIDATE",15),
                     ("QUALIFICATION",9),("RELEASE_FORBIDDEN",4),("INDEPENDENCE",5)],
}


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")) + "\n"


def canonical_value(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def case_id(test_id: str, suite_id: str, law_id: str, input_graph: dict) -> str:
    """Content identity over executor facts only; author order cannot leak."""
    preimage = {"test_id": test_id, "suite_id": suite_id,
                "law_id": law_id, "input_graph": input_graph}
    return "PPC5R10_CASE_" + hashlib.sha256(
        canonical_value(preimage).encode()).hexdigest()


def executor_input_projection(case: dict) -> dict:
    """Return the sole facts-only executor envelope shared by both RFCs."""
    graph = case["input_graph"]
    projected = {
        "case_id": case["case_id"],
        "test_id": case["test_id"],
        "suite_id": case["suite_id"],
        "law_id": case["law_id"],
        "input_graph": {
            "roots": graph["roots"],
            "nodes": graph["nodes"],
            "typed_edges": graph["typed_edges"],
        },
    }
    forbidden = {
        "branch_key", "axis_values", "mutation_descriptor", "mutation_operation",
        "expected_output", "expected_result", "expected_first_failure", "answer_key",
    }
    def walk(value):
        if isinstance(value, dict):
            leaked = forbidden & set(value)
            if leaked:
                raise ValueError(f"executor input leaks author/oracle fields: {sorted(leaked)}")
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(projected)
    for node in projected["input_graph"]["nodes"]:
        raw = node.get("canonical_json_bytes")
        if not isinstance(raw, str):
            raise ValueError("every executor node must carry actual canonical JSON bytes")
        json.loads(raw)
    return projected


def validate_rfc() -> dict:
    rfc = json.loads(RFC.read_text())
    rows = {row["test_id"]: row for row in rfc["per_test_counts"]}
    for tid, (p, n, q) in COUNTS.items():
        row = rows[tid]
        if (row["P"], row["N"], row["Q"], row["logical"]) != (p, n, q, p+n+q):
            raise ValueError(f"{tid}: count drift")
        if tid in SUITE_ENTRY_COUNTS and len(SUITE_ENTRY_COUNTS[tid]) != p:
            raise ValueError(f"{tid}: suite-vector count drift")
        if tid in NEGATIVE_FAMILIES and sum(count for _, count in NEGATIVE_FAMILIES[tid]) != n:
            raise ValueError(f"{tid}: negative-family count drift")
    totals = tuple(sum(row[i] for row in COUNTS.values()) for i in range(3))
    if totals != (465, 2467, 55):
        raise ValueError(f"global count drift: {totals}")
    if rfc["materialization_status"] != "BLOCKED_PROPOSAL_ONLY_NO_FIXTURE_BYTES_AUTHORIZED":
        raise ValueError("RFC must refuse materialization")
    identity = rfc["case_identity"]
    if identity["semantic_role"] != ("input-only content identity: SHA-256 of canonical "
            "{test_id,suite_id,law_id,input_graph}; no author order, case class, "
            "mutation provenance, or expectation participates"):
        raise ValueError("case identity is not input-only")
    if any(token not in identity["forbidden_preimage_material"] for token in
           ("branch_key", "axis_value", "mutation_operation", "mutation_target",
            "expected_output", "expected_result", "expected_first_failure")):
        raise ValueError("case identity still admits author/oracle material")
    required = rfc["executor_input_envelope"]["required"]
    if required != ["case_id", "test_id", "suite_id", "law_id", "input_graph"]:
        raise ValueError("executor envelope drift")
    if rfc["post_execution_expectation_join"]["join_key"] != "case_id":
        raise ValueError("expectations must join after execution by opaque case_id")
    return {"rfc_sha256": hashlib.sha256(RFC.read_bytes()).hexdigest(),
            "P": totals[0], "N": totals[1], "Q": totals[2],
            "logical": sum(totals), "planned_executions": 2*sum(totals)}


if __name__ == "__main__":
    print(canonical(validate_rfc()), end="")
