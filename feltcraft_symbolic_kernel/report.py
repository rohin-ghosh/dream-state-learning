"""Terminal FeltCraft V7 report construction and exact-byte validation."""

import json


GOLDEN_REPORT_BYTES = b'{"alignment_count":96,"bridge_case_count":36864,"bridge_cost":17,"bridge_deletion_check_count":73728,"bridge_dependency_failures":0,"calibration_class_histogram":[{"class_count":6,"class_size":16}],"conjunctive_cost":16,"distinct_graph_count":48,"intermediate_cost_histogram":[{"case_count":192,"cost":5}],"motif_best_value":{"denominator":1,"numerator":1},"projection_case_counts":{"local":12,"motif_schema":96,"oracle":192,"random_source":27648},"projection_negative_attempt_count":25,"projection_negative_code_histogram":[{"code":"SK08_E_ALIGNMENT","count":2},{"code":"SK08_E_ARITY","count":7},{"code":"SK08_E_ATOM","count":2},{"code":"SK08_E_GOAL","count":4},{"code":"SK08_E_MOTIF_INCOMPATIBLE","count":2},{"code":"SK08_E_ORDER","count":2},{"code":"SK08_E_SOURCE_GRAPH","count":2},{"code":"SK08_E_TYPE","count":4}],"projection_negative_mismatch_count":0,"projection_negative_rejected_count":25,"protocol_id":"feltcraft_symbolic_kernel_v7","random_best_value":{"denominator":4,"numerator":1},"random_support_count_histogram":[{"cell_count":48,"support_count":4}],"symbolic_vector_check_count":72,"symbolic_vector_mismatch_count":0,"test_receipts":[{"observed_counts":[96,48,4,10,10,0],"passed":true,"test_id":"SK01_DOMAIN_INVERSE_V7"},{"observed_counts":[6,16,6,0],"passed":true,"test_id":"SK02_CALIBRATION_VECTORS_V7"},{"observed_counts":[12,4,4,1,4,12,12,0],"passed":true,"test_id":"SK03_RANDOM_WITNESSES_V7"},{"observed_counts":[96,1,1,20,0],"passed":true,"test_id":"SK04_MOTIF_WITNESSES_V7"},{"observed_counts":[96,2,0,0,0],"passed":true,"test_id":"SK05_TWIN_WITNESSES_V7"},{"observed_counts":[192,5,192,8,16,17,0],"passed":true,"test_id":"SK06_COSTS"},{"observed_counts":[36864,73728,0],"passed":true,"test_id":"SK07_BRIDGE_DELETION"},{"observed_counts":[12,96,27648,192,72,25,25,0],"passed":true,"test_id":"SK08_PROJECTIONS_CLOSED_BOUNDARY_V7"},{"observed_counts":[1,6,0],"passed":true,"test_id":"SK09_REPORT"}],"top_cost_histogram":[{"case_count":192,"cost":8}],"twin_edge_change_failures":0,"twin_roundtrip_failures":0,"twin_top_action_change_failures":0,"verdict":"RETAIN_SYMBOLIC_KERNEL"}\n'


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _receipt(record):
    return {"test_id": record[0], "observed_counts": list(record[1]), "passed": record[2]}


def build_success_bytes(upstream_receipts, negative_histogram):
    """Construct report from SKE13 aggregate-only evidence."""
    if type(upstream_receipts) is not tuple or len(upstream_receipts) != 8:
        raise ValueError("upstream receipts")
    if any(type(record) is not tuple or len(record) != 3 or record[2] is not True for record in upstream_receipts):
        raise ValueError("upstream failure")
    counts = tuple(record[1] for record in upstream_receipts)
    receipts = [_receipt(record) for record in upstream_receipts]
    receipts.append({"test_id": "SK09_REPORT", "observed_counts": [1, 6, 0], "passed": True})
    value = {
        "alignment_count": counts[0][0],
        "bridge_case_count": counts[6][0],
        "bridge_cost": counts[5][5],
        "bridge_deletion_check_count": counts[6][1],
        "bridge_dependency_failures": counts[6][2],
        "calibration_class_histogram": [{"class_count": counts[1][0], "class_size": counts[1][1]}],
        "conjunctive_cost": counts[5][4],
        "distinct_graph_count": counts[0][1],
        "intermediate_cost_histogram": [{"case_count": counts[5][0], "cost": counts[5][1]}],
        "motif_best_value": {"denominator": counts[3][2], "numerator": counts[3][1]},
        "projection_case_counts": {"local": counts[7][0], "motif_schema": counts[7][1], "random_source": counts[7][2], "oracle": counts[7][3]},
        "projection_negative_attempt_count": counts[7][5],
        "projection_negative_code_histogram": [{"code": code, "count": count} for code, count in negative_histogram],
        "projection_negative_mismatch_count": counts[7][7],
        "projection_negative_rejected_count": counts[7][6],
        "protocol_id": "feltcraft_symbolic_kernel_v7",
        "random_best_value": {"denominator": counts[2][4], "numerator": counts[2][3]},
        "random_support_count_histogram": [{"cell_count": 48, "support_count": counts[2][1]}],
        "symbolic_vector_check_count": counts[7][4],
        "symbolic_vector_mismatch_count": counts[7][7],
        "test_receipts": receipts,
        "top_cost_histogram": [{"case_count": counts[5][2], "cost": counts[5][3]}],
        "twin_edge_change_failures": counts[4][3],
        "twin_roundtrip_failures": counts[4][2],
        "twin_top_action_change_failures": counts[4][4],
        "verdict": "RETAIN_SYMBOLIC_KERNEL",
    }
    return _canonical(value)


def validate_success_bytes(value):
    return type(value) is bytes and value == GOLDEN_REPORT_BYTES


def validate_and_return(upstream_receipts, negative_histogram):
    candidate = build_success_bytes(upstream_receipts, negative_histogram)
    if not validate_success_bytes(candidate):
        raise ValueError("golden mismatch")
    original = json.loads(candidate.decode("utf-8"))
    mutations = []
    changed = dict(original)
    del changed["protocol_id"]
    mutations.append(_canonical(changed))
    changed = dict(original)
    changed["debug"] = True
    mutations.append(_canonical(changed))
    changed = dict(original)
    changed["protocol_id"] = "feltcraft_symbolic_kernel_v6"
    mutations.append(_canonical(changed))
    changed = dict(original)
    changed["random_best_value"] = {"numerator": 2, "denominator": 8}
    mutations.append(_canonical(changed))
    changed = dict(original)
    changed["test_receipts"] = list(original["test_receipts"])
    changed["test_receipts"][0], changed["test_receipts"][1] = changed["test_receipts"][1], changed["test_receipts"][0]
    mutations.append(_canonical(changed))
    mutations.append(candidate + b"\n")
    if len(mutations) != 6 or any(validate_success_bytes(value) for value in mutations):
        raise ValueError("mutation accepted")
    return candidate
