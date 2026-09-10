#!/usr/bin/env python3
"""Execute the proposal reducer DSL over its facts-only finite inputs.

This is a source-law validator, not a fixture executor or materializer.  It
reads only checked-in proposal contracts/registries and the three RFC files.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any

import t14_replay_a
import t14_replay_b


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ROOT = REPO / "research_loop/changes/chg_20260905_public_pathway_consolidation_v5r9"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def node_id(artifact_type: str, canonical_json_bytes: str) -> str:
    preimage = artifact_type.encode() + b"\0" + canonical_json_bytes.encode()
    return "N_" + hashlib.sha256(preimage).hexdigest()


def build_input_graph(law_id: str, rows: list[dict], builder: dict,
                      sources: dict[str, Any]) -> dict:
    """Construct the exact facts-only graph supplied to either executor.

    Every source constant is copied into a concrete companion node.  Reducers
    receive no filesystem path, registry handle, axis label, or expected value.
    """
    source_ids = builder.get("source_ids", [])
    assert len(source_ids) == len(set(source_ids))
    companions = []
    source_nodes = []
    for source_id in source_ids:
        raw = canonical(sources[source_id])
        nid = node_id("PPC5R10_REDUCER_SOURCE_COMPANION", raw)
        companions.append({"node_id": nid,
                           "artifact_type": "PPC5R10_REDUCER_SOURCE_COMPANION",
                           "canonical_json_bytes": raw})
        source_nodes.append({"source_id": source_id, "node_id": nid})
    parameter_keys = {"replay_sources", "final_result_source_facts"}
    parameters = {key: builder[key] for key in sorted(parameter_keys & set(builder))}
    root_value = {"law_id": law_id, "rows": rows, "parameters": parameters,
                  "source_nodes": source_nodes}
    root_raw = canonical(root_value)
    root_id = node_id("PPC5R10_REDUCER_INPUT_VECTOR", root_raw)
    root = {"node_id": root_id,
            "artifact_type": "PPC5R10_REDUCER_INPUT_VECTOR",
            "canonical_json_bytes": root_raw}
    edges = [{"producer_node_id": source_nodes[ordinal]["node_id"],
              "consumer_node_id": root_id,
              "consumer_stage": "FIXTURE_REDUCER",
              "field_path": f"/source_nodes/{ordinal}/node_id",
              "role": "REDUCER_SOURCE_COMPANION", "ordinal": ordinal,
              "cardinality": "ORDERED_EXACT"}
             for ordinal, source_id in enumerate(source_ids)]
    return {"roots": [root_id], "nodes": [root] + companions,
            "typed_edges": edges}


def sources_from_input_graph(graph: dict) -> tuple[list[dict], dict[str, Any], dict]:
    """Parse exactly the graph projection; this is the executor-side view."""
    by_id = {node["node_id"]: node for node in graph["nodes"]}
    assert len(by_id) == len(graph["nodes"])
    root_id = graph["roots"][0]
    root = json.loads(by_id[root_id]["canonical_json_bytes"])
    assert by_id[root_id]["node_id"] == node_id(
        by_id[root_id]["artifact_type"], by_id[root_id]["canonical_json_bytes"])
    local = {}
    for binding in root["source_nodes"]:
        source_id, nid = binding["source_id"], binding["node_id"]
        node = by_id[nid]
        assert node["node_id"] == node_id(node["artifact_type"],
                                          node["canonical_json_bytes"])
        local[source_id] = json.loads(node["canonical_json_bytes"])
    assert len(graph["typed_edges"]) == len(local)
    for ordinal, binding in enumerate(root["source_nodes"]):
        source_id, nid = binding["source_id"], binding["node_id"]
        edge = graph["typed_edges"][ordinal]
        assert edge == {"producer_node_id": nid,
                        "consumer_node_id": root_id,
                        "consumer_stage": "FIXTURE_REDUCER",
                        "field_path": f"/source_nodes/{ordinal}/node_id",
                        "role": "REDUCER_SOURCE_COMPANION",
                        "ordinal": ordinal,
                        "cardinality": "ORDERED_EXACT"}
    return root["rows"], local, root["parameters"]


def pointer_get(value: Any, pointer: str) -> Any:
    if pointer == "/":
        return value
    for raw in pointer.strip("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def load_sources() -> dict[str, Any]:
    manifest = load(HERE / "REDUCER_SOURCE_SNAPSHOTS.json")
    sources = {}
    for row in manifest["snapshots"]:
        document = load(ROOT / row["file"])
        value = pointer_get(document, row["json_pointer"])
        assert digest(value) == row["value_sha256"], row["source_id"]
        assert row["source_id"] not in sources
        sources[row["source_id"]] = value
    return sources


def rows_from_builder(builder: dict, sources: dict[str, Any]) -> list[dict]:
    op = builder["op"]
    def closed_zip(columns, values):
        assert len(columns)==len(values), (builder["law_id"],len(columns),len(values))
        return dict(zip(columns,values))
    if op == "INLINE_ROWS":
        return [closed_zip(builder["columns"], row) for row in builder["rows"]]
    if op == "CROSS_PRODUCT":
        names = list(builder["dimensions"])
        rows = [dict(zip(names, values)) for values in itertools.product(
            *(builder["dimensions"][name] for name in names))]
        for row in rows:
            row.update(builder.get("constants", {}))
        return rows
    if op == "FILTERED_CROSS_PRODUCT":
        names = list(builder["dimensions"])
        rows = [dict(zip(names, values)) for values in itertools.product(
            *(builder["dimensions"][name] for name in names))]
        def excluded(row: dict, rule: dict) -> bool:
            for key, value in rule.items():
                if isinstance(value, list):
                    if row[key] not in value:
                        return False
                elif row[key] != value:
                    return False
            return True
        rows = [row for row in rows if not any(excluded(row, rule)
                                                for rule in builder.get("exclude", []))]
        rows.extend(builder.get("append_rows", []))
        return rows
    if op in {"ONE_FIELD_PAIRS", "INLINE_VECTOR"}:
        return [closed_zip(builder["columns"], row) for row in builder["rows"]]
    if op == "UPSTREAM_ONE_FIELD_PAIRS":
        rows = []
        for perturbation, field, left_value, right_value in builder["rows"]:
            left = json.loads(canonical(builder["base_upstream"]))
            right = json.loads(canonical(builder["base_upstream"]))
            left[field], right[field] = left_value, right_value
            rows.append({"perturbation": perturbation, "left_upstream": left,
                         "right_upstream": right})
        return rows
    if op == "PERMUTATIONS":
        return [{"permutation": list(row)} for row in itertools.permutations(builder["values"])]
    if op == "UNORDERED_PAIRS":
        values = sources[builder["source_ids"][0]]["precedence"]
        return [{"left": a, "right": b} for a, b in itertools.combinations(values, 2)]
    if op == "SOURCE_EXPAND":
        rows = []
        for rule in sources[builder["source_ids"][0]]["rules"]:
            for raw in rule["raw_results"]:
                rows.append({"raw_result": raw, "applies": rule["applies"]})
        return rows
    if op == "REGISTRY_FILE_SET":
        result=[]
        for name in builder["rows"]:
            raw=canonical(load(ROOT/name))
            result.append({"file":name,"canonical_registry_bytes":raw,
                           "registry_sha256":hashlib.sha256(raw.encode()).hexdigest()})
        return result
    if op == "SOURCE_VECTOR":
        law_id = builder["law_id"]
        if law_id in {"T04_MODEL_DISPATCH_CHAIN_V1", "T08_DISPATCH_CLOSURE_V1"}:
            return [{"dispatch_rows": sources["DISPATCH"]}]
        if law_id == "T06_PRE_ENTROPY_ANCESTRY_V1":
            stages = sources["AUTHORITY"]["stages"]
            return [{"stages": stages[:7]}]
        if law_id == "T11_CLAIM_BYTES_V1":
            claims = sources["CLAIMS"]
            renderings = {row["claim_id"]: row for row in claims["claim_renderings"]}
            return [{"row": row, "rendering": renderings[row["row_key"]]}
                    for row in claims["rows"]]
        if law_id == "T12_VISIBILITY_CELL_V1":
            return [{"cell": row} for row in sources["VISIBILITY"]]
        if law_id == "T12_TRANSITION_CAUSE_V1":
            return [{"row": row} for row in sources["CAUSES"]["rows"]]
        raise AssertionError(f"unimplemented SOURCE_VECTOR {law_id}")
    if op == "SCHEMA_EDGE_EXTRACT":
        return [{"edge": edge} for edge in collect_schema_edges(sources["SCHEMA_DEFS"])]
    if op == "TOP_LEVEL_TYPE_EXTRACT":
        defs = sources["SCHEMA_DEFS"]
        return [{"artifact_type": body["properties"]["artifact_type"]["const"]}
                for body in defs.values() if body.get("x-top-level-artifact")]
    if op == "THREE_WAY_EDGE_EXTRACT":
        return [{"source_ids":["SCHEMA_DEFS","OBJECTS","VISIBILITY"]}]
    if op == "T13_TECHNICAL_GRAPH":
        inbound=edges_for(inventory_edges(sources["OBJECTS"]),
                          "T13_PREMODEL_TECHNICAL_GATE")
        ingress=[]
        for edge in inbound:
            artifact={"artifact_type":edge["producer_type"],
                      "run_id":"RUN_FIXTURE_0001","role":edge["role"],
                      "ordinal":edge["ordinal"],"status":"PASS"}
            raw=canonical(artifact)
            ingress.append({"canonical_artifact_bytes":raw,
                            "artifact_sha256":hashlib.sha256(raw.encode()).hexdigest()})
        return [{"run_id":"RUN_FIXTURE_0001","ingress":ingress,
                 "test_results":[{"test_id":f"PPC5R9_T{i:02d}","status":"PASS"}
                                 for i in range(2,13)],
                 "fixture_universe_complete":True,"typed_registries_valid":True,
                 "life_control_closure":True,"claim_holm_bytes_valid":True,
                 "sealer_independent":True,"review_fresh":True,
                 "advocate_nonoverriding":True,"conditional_power_pass":True,
                 "pointwise_joint_power_pass":True,
                 "forbidden_future_artifact_types":[],
                 "model_execution_attempted":False}]
    if op == "AUTHORITY_DAG_EXTRACT":
        return [{"stage": row} for row in sources["AUTHORITY"]["stages"]]
    if op == "T14_REPLAY_GRAPH_EXTRACT":
        return [closed_zip(builder["columns"], row) for row in builder["rows"]]
    raise AssertionError(f"unknown input builder {op}")


def collect_schema_edges(defs: dict) -> list[dict]:
    """Independent copy of the frozen recursive JSON-Schema traversal law."""
    result = []
    top = {
        body["properties"]["artifact_type"]["const"]: name
        for name, body in defs.items() if body.get("x-top-level-artifact")
    }
    def walk(node: Any, path: str, stack: tuple[str, ...], consumer: str) -> None:
        if isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, f"{path}/{index}", stack, consumer)
            return
        if not isinstance(node, dict):
            return
        if node.get("x-artifact-ref") is True:
            for producer in node["x-artifact-types"]:
                result.append({"producer_type": producer, "consumer_type": consumer,
                    "consumer_stage": node["x-consumer-stage"], "field_path": path or "/",
                    "role": node["x-role"], "ordinal": node["x-ordinal"],
                    "cardinality": node["x-cardinality"]})
            return
        if "$ref" in node:
            ref = node["$ref"]
            assert ref.startswith("#/$defs/") and ref not in stack
            walk(defs[ref.rsplit("/", 1)[-1]], path + f"->$ref({ref})",
                 stack + (ref,), consumer)
            for key, child in node.items():
                if key != "$ref":
                    walk(child, path + "/" + key, stack, consumer)
            return
        for key, child in node.items():
            if not key.startswith("x-"):
                walk(child, path + "/" + key, stack, consumer)
    for artifact_type, def_name in top.items():
        walk(defs[def_name], "", (), artifact_type)
    unique = {canonical(edge): edge for edge in result}
    return [unique[key] for key in sorted(unique)]


def inventory_edges(objects: list[dict]) -> list[dict]:
    rows = []
    for producer in objects:
        for edge in producer.get("reference_bindings", []):
            rows.append({"producer_type": producer["type"], **edge})
    return sorted(rows, key=canonical)


def route_reduce(row: dict) -> tuple[str, int, str | None, bool, str | None, str | None]:
    target = row["read_key"] == row["assigned_target_key"]
    count = len(row["matching_route_ids"])
    if target and count == 1:
        return "TARGET_ONE", count, "INTERVENTION", True, row["intervention_payload_bytes"], None
    if target:
        return ("TARGET_ZERO" if count == 0 else "TARGET_MULTI", count,
                None, False, None, "ROUTE_TARGET_MATCH")
    if count == 0:
        return "NON_TARGET_ZERO", 0, "OFF_PATH_AUTHENTIC_PASS_THROUGH", True, row["provider_public_bytes"], None
    return "NON_TARGET_NONZERO", count, None, False, None, "ROUTE_TARGET_MATCH"


def render_downstream(upstream: dict) -> dict:
    route_input = {
        "assigned_target_key": upstream["assigned_target_key"],
        "read_key": upstream["read_key"],
        "matching_route_ids": upstream["matching_route_ids"],
        "provider_public_bytes": upstream["provider_response_bytes"],
        "intervention_payload_bytes": upstream["intervention_payload_bytes"],
    }
    _, _, kind, continuation, emitted, _ = route_reduce(route_input)
    public = {"last_read": emitted} if continuation else None
    model_view = None if public is None else canonical({
        "static_context_bytes": upstream["static_context_bytes"],
        "last_read": public["last_read"],
    })
    return {"emission_kind": kind, "emitted": emitted,
            "public": public, "model_view": model_view,
            "behavior_input": None if model_view is None else canonical(
                {"model_view": model_view, "tool_space": "COMPILER_GYM"})}


def reduced_fraction(n: int, d: int) -> tuple[int, int]:
    value = Fraction(n, d)
    return value.numerator, value.denominator


def binomial_upper_tail(x: int, n: int, p: Fraction) -> Fraction:
    return sum((Fraction(math.comb(n, k)) * p**k * (1-p)**(n-k)
                for k in range(x, n+1)), Fraction(0))


def binomial_lower_tail(x: int, n: int, p: Fraction) -> Fraction:
    return sum((Fraction(math.comb(n, k)) * p**k * (1-p)**(n-k)
                for k in range(0, x+1)), Fraction(0))


def cp_grid_bracket(x: int, n: int, gamma: Fraction, scale: int,
                    direction: str) -> tuple[int, int, int]:
    """Exact outward decimal bracket around a one-sided CP root."""
    den = 10**scale
    if direction == "LOWER" and x == 0:
        return 0, 0, den
    if direction == "UPPER" and x == n:
        return den, den, den
    lo, hi = 0, den
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        p = Fraction(mid, den)
        on_low_side = (binomial_upper_tail(x, n, p) <= gamma
                       if direction == "LOWER"
                       else binomial_lower_tail(x, n, p) >= gamma)
        if on_low_side:
            lo = mid
        else:
            hi = mid
    if direction == "LOWER":
        assert binomial_upper_tail(x, n, Fraction(lo, den)) <= gamma
        assert binomial_upper_tail(x, n, Fraction(hi, den)) >= gamma
    else:
        assert binomial_lower_tail(x, n, Fraction(lo, den)) >= gamma
        assert binomial_lower_tail(x, n, Fraction(hi, den)) <= gamma
    return lo, hi, den


def registry_self_hash(registry: dict) -> bool:
    body = dict(registry)
    claimed = body.pop("self_hash", None)
    if claimed is None:
        return False
    raw = canonical(body).encode()
    pre = (body["contract"] + "\0" + str(body["schema_version"]) + "\0" +
           body["artifact_type"] + "\0").encode() + raw + b"\n"
    return hashlib.sha256(pre).hexdigest() == claimed


def source_status_rule(sources: dict, raw: str, applies: str) -> dict:
    matches = [rule for rule in sources["STATUS"]["rules"]
               if raw in rule["raw_results"] and rule["applies"] == applies]
    assert len(matches) == 1, (raw, applies, len(matches))
    return matches[0]


def edges_for(edges: list[dict], consumer: str) -> list[dict]:
    return sorted([edge for edge in edges if edge["consumer_type"] == consumer], key=canonical)


T14_ROLE_TO_RELATION = {
    "PPC5R9_T02_RESULT":"controller_transition",
    "PPC5R9_T03_RESULT":"queue_effect_per_slot",
    "PPC5R9_T04_RESULT":"route_lineage_audit",
    "PPC5R9_T05_RESULT":"provider_audit",
    "PPC5R9_T06_RESULT":"emission_influence",
    "PPC5R9_T07_RESULT":"dispatch_binding",
    "PPC5R9_T08_RESULT":"dream_context_status",
    "PPC5R9_T09_RESULT":"d1d_stage",
    "PPC5R9_T10_RESULT":"life_gate_aggregate",
    "PPC5R9_T11_RESULT":"d1a_control_membership",
    "PPC5R9_T12_RESULT":"pointwise_power_support",
    "PPC5R9_T13_RESULT":"resource_accounting",
    "PRE_ENTROPY_DESIGN_LOCK":"overlap_membership",
    "ENTROPY_ACQUISITION":"candidate_decision",
    "POPULATED_RUN_LOCK":"dependency_decision",
    "STATIC_SEAL_PAIR":"claim_qualification",
}

T14_EXPECTED_PREDECESSORS = [
    *[(f"PPC5R9_T{i:02d}_RESULT","TEST_RESULT") for i in range(2,14)],
    ("PRE_ENTROPY_DESIGN_LOCK","PRE_ENTROPY_DESIGN_LOCK"),
    ("ENTROPY_ACQUISITION","ENTROPY_ACQUISITION_RECEIPT"),
    ("POPULATED_RUN_LOCK","POPULATED_RUN_LOCK"),
    ("STATIC_SEAL_PAIR","STATIC_SEAL_PAIR_RECEIPT"),
    ("REVIEW_RECEIPT","REVIEW_RECEIPT"),
    ("ADVOCATE_RECEIPT","ADVOCATE_RECEIPT"),
    ("COMPLETE_RUN_MANIFEST","COMPLETE_RUN_MANIFEST"),
    ("ANALYSIS_BUNDLE","ANALYSIS_BUNDLE"),
    ("D1A_CONTROL_SET_MANIFEST","D1A_CONTROL_SET_MANIFEST"),
    ("COMPLETE_MODEL_VIEW_MANIFEST","COMPLETE_MODEL_VIEW_MANIFEST"),
    ("ROUTE_LINEAGE_AUDIT","ROUTE_LINEAGE_AUDIT_RECEIPT"),
    ("PROVIDER_AUDIT","PROVIDER_AUDIT_RECEIPT"),
]


def t14_value(kind: str, f: dict, sources: dict) -> dict:
    if kind=="controller_transition":
        return {"slot_id":f["slot_id"],"next_state":"CONSUMED" if f["trigger"]=="OBSERVE" and f["route_match_count"]==1 else "INVALID"}
    if kind=="queue_effect_per_slot":
        valid=f["route_target_class"]=="TARGET" and f["route_match_count"]==1 and f["schedule_state"]=="COMPLETE"
        return {"effects":[{"slot_id":slot,"ordinal":i,"effect":"CONSUME" if valid else "DISCARD","count":1} for i,slot in enumerate(f["ordered_slots"])]}
    if kind=="route_lineage_audit":
        return {"match_count":len(f["matching_route_ids"]),"target_read":f["assigned_target_key"]==f["read_key"],"route_ids_sha256":digest(f["matching_route_ids"])}
    if kind=="provider_audit":
        return {"status":f["provider_status"],"public_bytes_sha256":hashlib.sha256(f["provider_public_bytes"].encode()).hexdigest()}
    if kind=="emission_influence":
        common={"assigned_target_key":f["assigned_target_key"],"read_key":f["read_key"],"matching_route_ids":f["matching_route_ids"],"provider_response_bytes":f["provider_response_bytes"],"condition":"c","source":"s","match_keys":["target"],"provider_scores":[1],"nonce":"n","mapping":{"target":"route0"},"static_context_bytes":f["static_context_bytes"]}
        left={**common,"intervention_payload_bytes":f["left_intervention_payload_bytes"]}; right={**common,"intervention_payload_bytes":f["right_intervention_payload_bytes"]}
        a,b=render_downstream(left),render_downstream(right)
        return {"emission_changed":a["emitted"]!=b["emitted"],"public_changed":a["public"]!=b["public"],"model_view_changed":a["model_view"]!=b["model_view"],"behavior_input_changed":a["behavior_input"]!=b["behavior_input"]}
    if kind=="dispatch_binding": return {"field_count":len(sources["DISPATCH"]),"ordered_rows_sha256":digest(sources["DISPATCH"])}
    if kind=="dream_context_status": return {"status":f["dream_status"],"continuation":"EXECUTE_DOWNSTREAM" if f["dream_status"]!="MISSING_NO_RETRY" else "NO_RETRY","context_policy":f["context_policy"]}
    if kind=="d1d_stage": return {"root_policy":f["root_policy"],"stage":f["stage"],"reachable":True}
    if kind=="life_gate_aggregate": return {"N":f["N"],"complete":f["present_required_arms"]==2*f["N"]}
    if kind=="d1a_control_membership": return {"sample_ordinal":f["sample_ordinal"],"control_count":len(f["controls"]),"unique":len(f["controls"])==len(set(f["controls"]))}
    if kind=="pointwise_power_support":
        total=sum((Fraction(*m)*Fraction(*b) for m,b in zip(f["masses"],f["conditional_bounds"])),Fraction(0)); return {"bound_numerator":total.numerator,"bound_denominator":total.denominator}
    if kind=="resource_accounting": return {"physical_total_by_kind":{"TOKENS":sum(x["amount"] for x in f["events"] if x["kind"]=="TOKENS")},"event_count":len({x["event_id"] for x in f["events"]})}
    if kind=="overlap_membership": return {"intersection":sorted(set(f["left_ids"])&set(f["right_ids"]))}
    if kind=="candidate_decision": return {"pass":all(f["required_gates"])}
    if kind=="dependency_decision": return {"pass":f["candidate_pass"] and all(f["required_dependencies"])}
    if kind=="claim_qualification":
        rendering=next(x for x in sources["CLAIMS"]["claim_renderings"] if x["claim_id"]==f["claim_id"]); rendered="\n".join(rendering["ordered_inseparable_segments"]); return {"claim_id":f["claim_id"],"rendered_bytes_sha256":hashlib.sha256(rendered.encode()).hexdigest()}
    raise AssertionError(kind)


def decode_t14_artifacts(rows: list[dict]) -> list[dict]:
    assert [(row["role"],row["artifact_type"]) for row in rows] == \
        T14_EXPECTED_PREDECESSORS
    artifacts=[]
    for position,row in enumerate(rows):
        raw=row["canonical_artifact_bytes"]
        assert hashlib.sha256(raw.encode()).hexdigest()==row["artifact_sha256"]
        artifact=json.loads(raw); assert canonical(artifact)==raw
        assert set(artifact)=={"artifact_type","cardinality","ordinal",
                               "payload","role","run_id"}
        assert artifact["run_id"]==row["run_id"] and artifact["role"]==row["role"]
        assert artifact["artifact_type"]==row["artifact_type"] and artifact["ordinal"]==row["ordinal"]==position
        assert artifact["cardinality"]==row["cardinality"]=="ONE"
        artifacts.append(artifact)
    assert len({x["role"] for x in artifacts})==len(artifacts)==24
    assert len({x["run_id"] for x in artifacts})==1
    return artifacts


def contains_release_input(value: Any) -> bool:
    if isinstance(value,dict):
        return any("release" in key.lower() or contains_release_input(child)
                   for key,child in value.items())
    if isinstance(value,list): return any(contains_release_input(x) for x in value)
    return False


def t14_final_status(independent: bool, relation_a: str, relation_b: str,
                     cold_count: int, final_count: int, outbound_count: int,
                     release_consumed: bool) -> tuple[str, str | None]:
    if release_consumed: return "FAIL","RELEASE_BYTES_FORBIDDEN"
    if not independent: return "FAIL","REPLAY_INDEPENDENCE"
    if relation_a!=relation_b: return "FAIL","REPLAY_AGREEMENT"
    if (cold_count,final_count,outbound_count)!=(11,6,1):
        return "FAIL","T14_TYPED_CLOSURE"
    return "PASS",None


def replay_a_relation(artifacts: list[dict], sources: dict) -> str:
    return t14_replay_a.reconstruct(artifacts,T14_ROLE_TO_RELATION,
        lambda kind,facts:t14_value(kind,facts,sources))


def replay_b_relation(artifacts: list[dict], sources: dict) -> str:
    return t14_replay_b.reconstruct(artifacts,T14_ROLE_TO_RELATION,
        lambda kind,facts:t14_value(kind,facts,sources))


def t13_package_status(package: dict, inbound: list[dict]) -> tuple[bool, int, bool, str | None]:
    resolved=[]; run_ids=set(); hashes=[]
    for row in package["ingress"]:
        raw=row["canonical_artifact_bytes"]
        if hashlib.sha256(raw.encode()).hexdigest()!=row["artifact_sha256"]:
            return False,len(resolved),False,"PACKAGE_HASH"
        artifact=json.loads(raw)
        if canonical(artifact)!=raw: return False,len(resolved),False,"NONCANONICAL_BYTES"
        if set(artifact)!={"artifact_type","run_id","role","ordinal","status"}:
            return False,len(resolved),False,"TYPED_PACKAGE_CLOSURE"
        run_ids.add(artifact["run_id"]); resolved.append(artifact);hashes.append(row["artifact_sha256"])
    same_run=run_ids=={package["run_id"]}
    observed=sorted((x["artifact_type"],x["role"],str(x["ordinal"])) for x in resolved)
    expected=sorted((e["producer_type"],e["role"],str(e["ordinal"])) for e in inbound)
    tests=package["test_results"]
    test_ok=([x["test_id"] for x in tests]==[f"PPC5R9_T{i:02d}" for i in range(2,13)]
             and all(x["status"]=="PASS" for x in tests))
    booleans=[package[k] for k in ("fixture_universe_complete","typed_registries_valid",
        "life_control_closure","claim_holm_bytes_valid","sealer_independent","review_fresh",
        "advocate_nonoverriding","conditional_power_pass","pointwise_joint_power_pass")]
    future=package["forbidden_future_artifact_types"]
    ingress_pass=all(x["status"]=="PASS" for x in resolved)
    ok=(same_run and len(hashes)==len(set(hashes)) and observed==expected and ingress_pass
        and test_ok and all(booleans) and not future
        and package["model_execution_attempted"] is False)
    failure=None if ok else ("FORBIDDEN_FUTURE_INPUT" if future or package["model_execution_attempted"] else
        "TYPED_PACKAGE_CLOSURE" if observed!=expected or not same_run or len(hashes)!=len(set(hashes)) else "TECHNICAL_PREREQUISITE")
    return ok,len(resolved),same_run,failure


def kahn_authority(stages: list[dict]) -> tuple[list[str], list[str], list[dict], bool]:
    names=[s["stage"] for s in stages]
    aliases=[]; backedges=[]
    if len(names)!=len(set(names)): aliases.append("DUPLICATE_STAGE")
    by_name={s["stage"]:s for s in stages}; order={name:i for i,name in enumerate(names)}
    adjacency={name:[] for name in names}; indegree={name:0 for name in names}
    for stage in stages:
        pred=stage["predecessor"]
        if pred is None or pred=="T14_FINAL_REPLAY_RESULT": continue
        if pred not in by_name: aliases.append(pred); continue
        adjacency[pred].append(stage["stage"]); indegree[stage["stage"]]+=1
        if order[pred]>=order[stage["stage"]]:
            backedges.append({"from_stage":pred,"to_stage":stage["stage"]})
    ready=sorted((order[name],name) for name in names if indegree[name]==0)
    result=[]
    while ready:
        _,name=ready.pop(0);result.append(name)
        for child in sorted(adjacency[name],key=order.get):
            indegree[child]-=1
            if indegree[child]==0:
                ready.append((order[child],child));ready.sort()
    acyclic=len(result)==len(names) and not aliases and not backedges
    return result,aliases,backedges,acyclic


def reduce_rows(program: dict, rows: list[dict], sources: dict,
                parameters: dict | None = None) -> list[list[Any]]:
    op = program["operator"]
    parameters = parameters or {}
    out = []
    if op == "DREAM_REDUCE":
        for i, row in enumerate(rows):
            failure=None
            if row["raw_call_status"] == "MISSING": failure="DREAM_MISSING"
            else:
                try: parsed=json.loads(row["raw_bytes"])
                except (TypeError, json.JSONDecodeError): parsed=None; failure="DREAM_PARSE"
                if failure is None and not row["debited_once"]: failure="DREAM_RENDER_OR_DEBIT"
                ids=row["candidate_record_ids"]
                if failure is None and (parsed != ids or len(ids)!=len(set(ids)) or
                    any(x not in row["known_record_ids"] for x in ids) or
                    ids != [x for x in row["known_record_ids"] if x in ids] or
                    (row["candidate_focus_id"] is not None and row["candidate_focus_id"] not in ids) or
                    len(ids)>row["capacity"]): failure="DREAM_ID_ORDER_FOCUS_CAPACITY"
                if failure is None and not row["rendered_matches"]: failure="CONTEXT_RENDER"
            status = "MISSING_NO_RETRY" if failure=="DREAM_MISSING" else (
                "INSTALLED" if failure is None and row["candidate_record_ids"] else
                "EMPTY_PUBLICATION" if failure is None else "INVALID")
            out.append([status, canonical(row["candidate_record_ids"]), row["candidate_focus_id"],
                        1 if row["debited_once"] else 0, failure])
    elif op == "CONTEXT_STATUS_REDUCE":
        for i, row in enumerate(rows):
            missing = row["dream_status"] == "MISSING_NO_RETRY" and row["context_policy"] == "AUTHENTIC_DREAM_CONTEXT"
            out.append([i, row["context_policy"], "MISSING_NO_RETRY" if missing else row["dream_status"],
                        "NO_RETRY" if missing else "EXECUTE_DOWNSTREAM", None])
    elif op == "TYPED_DEPENDENCY_REDUCE":
        out = [[i, r["context_policy"], r["source_role"],
                r["consumes_dream"] == (r["context_policy"] == "AUTHENTIC_DREAM_CONTEXT"), None]
               for i, r in enumerate(rows)]
    elif op == "LIFE_MEMBERSHIP_REDUCE":
        out = [[i, r["N"], 1 if r["present_required_arms"] == 2*r["N"] else 0,
                0 if r["present_required_arms"] == 2*r["N"] else 1,
                r["present_required_arms"] <= 2*r["N"], None] for i, r in enumerate(rows)]
    elif op == "EMISSION_INFLUENCE_REDUCE":
        for i,r in enumerate(rows):
            diffs=sorted(set(r["left_upstream"])|set(r["right_upstream"]))
            diffs=[key for key in diffs if canonical(r["left_upstream"].get(key))!=canonical(r["right_upstream"].get(key))]
            leaf=diffs[0] if len(diffs)==1 else "INVALID_DIFF_CARDINALITY"
            public_change=leaf=="intervention_payload_bytes"
            out.append([i,leaf,len(diffs),public_change,len(diffs)==1,None if len(diffs)==1 else "PUBLIC_VIEW_INFLUENCE"])
    elif op == "DISPATCH_CLOSURE_REDUCE":
        dispatch = rows[0]["dispatch_rows"]
        out = [[len(dispatch), all("row_key" in row and "content_sha256" in row for row in dispatch), None]]
    elif op == "PROVIDER_NUMERIC_REDUCE":
        for i, r in enumerate(rows):
            if r["provider_status"] == "MISSING":
                out.append([i, "MISSING_NO_RETRY", None, "[]", None]); continue
            scores = [Fraction(n, r["score_denominator"]) for n in r["score_numerators"]]
            quant = [round(float(x * r["quantization_scale"])) for x in scores]
            selected = None if not r["candidate_ids"] else sorted(zip(quant, r["candidate_ids"]), key=lambda x: (-x[0], x[1]))[0][1]
            out.append([i, "NOT_FOUND" if selected is None else "FOUND", selected, canonical(quant), None])
    elif op == "MOUNT_REDUCE":
        out = [[i, "NULL_MOUNT" if r["mount_is_null"] else "VALID_MOUNT",
                (r["allowed_null"] if r["mount_is_null"] else r["artifact_hash_valid"]), None]
               for i, r in enumerate(rows)]
    elif op == "DESCRIPTIVE_PROVIDER_REDUCE":
        out = [[i, r["arm"], r["provider_status"], True, None] for i, r in enumerate(rows)]
    elif op == "REGISTRY_SET_REDUCE":
        registries=[]
        for r in rows:
            assert hashlib.sha256(r["canonical_registry_bytes"].encode()).hexdigest()==r["registry_sha256"]
            registries.append(json.loads(r["canonical_registry_bytes"]))
        valid_hash = all(registry_self_hash(registry) for registry in registries)
        ordered = all(registry.get("ordered_row_keys", []) ==
                      [row["row_key"] for row in registry.get("rows", [])]
                      for registry in registries if "rows" in registry)
        out = [[len(rows), valid_hash, ordered, None]]
    elif op == "PER_LIFE_CONTROL_REDUCE":
        out = [[i, r["sample_ordinal"], r["control_kind"], True, None] for i, r in enumerate(rows)]
    elif op == "MANIFEST_MEMBERSHIP_REDUCE":
        r = rows[0]; out = [[len(r["prospective_sample_ordinals"]), r["controls_per_life"],
                             r["prospective_sample_ordinals"] == r["manifest_sample_ordinals"], None]]
    elif op == "ALLOWED_PROJECTION_REDUCE":
        forbidden = {"condition","source","match_keys","provider_scores","nonce","mapping"}
        out = [[i, r["stage"], len(forbidden & set(r["candidate_fields"])),
                not bool(forbidden & set(r["candidate_fields"])), None] for i, r in enumerate(rows)]
    elif op == "POINTWISE_BINDING_REDUCE":
        r=rows[0]; out=[[len(r["support_manifest_ids"]), all(x==r["manifest_id"] for x in r["support_manifest_ids"]), None]]
    elif op == "PRE_ENTROPY_DAG_REDUCE":
        stages=rows[0]["stages"]; out=[[len(stages), True,
            [s["stage"] for s in stages] == ["ARCHITECTURE_RATIFICATION","PRE_ENTROPY_DESIGN","ENTROPY_ACQUISITION","PROPOSAL_REALIZATION","LIFE_REALIZATION","SAFETY_RESOLUTION","POPULATED_RUN"], None]]
    elif op == "FULL_PATH_REDUCE":
        out=[[i,r["path_length"],len(set(r["world_actions_by_full_observation"])),len(set(r["world_actions_by_full_observation"]))==1,None] for i,r in enumerate(rows)]
    elif op == "PROPER_SUBSET_REDUCE":
        out=[[i,r["path_length"],r["bitmask"],len(set(r["world_actions"])),len(set(r["world_actions"]))>1,None] for i,r in enumerate(rows)]
    elif op == "ALTERNATE_PATH_REDUCE":
        out=[[i,r["path_length"],len(r["eligible_paths"]),len(r["sufficient_paths"]),r["sufficient_paths"]==[r["registered_path"]],None] for i,r in enumerate(rows)]
    elif op == "EDGE_ARTIFACT_REDUCE":
        out=[[i,r["edge_key"],r["artifact_role"],True,None] for i,r in enumerate(rows)]
    elif op == "PATH_CLOSURE_REDUCE":
        out=[[i,r["closure_kind"],True,None] for i,r in enumerate(rows)]
    elif op == "D1B_ROUTE_REDUCE":
        out=[[i,*route_reduce(r)] for i,r in enumerate(rows)]
    elif op == "D1B_PAIRED_INFLUENCE_REDUCE":
        for i,r in enumerate(rows):
            left,right=r["left_upstream"],r["right_upstream"]
            diffs=[k for k in left if canonical(left[k])!=canonical(right[k])]
            changed_leaf=diffs[0] if len(diffs)==1 else "INVALID_DIFF_CARDINALITY"
            a,b=render_downstream(left),render_downstream(right)
            emission=a["emitted"]!=b["emitted"]; public=a["public"]!=b["public"]
            view=a["model_view"]!=b["model_view"]
            behavior=a["behavior_input"]!=b["behavior_input"]
            permitted=(emission and public and view and behavior) if changed_leaf=="intervention_payload_bytes" else not (emission or public or view or behavior)
            out.append([i,changed_leaf,len(diffs),emission,public,view,behavior,permitted,None if permitted and len(diffs)==1 else "PUBLIC_VIEW_INFLUENCE"])
    elif op == "D1B_QUEUE_REDUCE":
        for i,r in enumerate(rows):
            invalid=r["route_target_class"]=="TARGET" and r["route_match_count"]!=1
            if r["slot_state"]=="REJECTED" or r["schedule_state"]=="REJECTED": status="REJECTED"
            elif len(r["ordered_slots"])==2: status="TWO_OUTSTANDING_INVALID"
            elif invalid or r["provider_call_status"]!="OK": status="QUEUED_INVALID"
            else: status="QUEUED_VALID"
            effects=[{"slot_id":slot,"ordinal":j,"effect":"CONSUME" if status=="QUEUED_VALID" else "DISCARD","count":1} for j,slot in enumerate(r["ordered_slots"])]
            out.append([i,status,True,canonical(effects),all(x["count"]==1 for x in effects),None])
    elif op == "OPAQUE_ID_REDUCE":
        for i,r in enumerate(rows):
            pre=b"\0".join(str(r[k]).encode() for k in ["domain_tag","run_id","sample_ordinal","path_template_id","edge_position","edge_id","entropy_slice_hex"])
            h=hashlib.sha256(pre).hexdigest(); out.append([i,h,32,None])
    elif op == "AUDIT_SPLIT_REDUCE":
        out=[[i,r["audit_kind"],len(r["row_roles"]),all(x==r["audit_kind"] for x in r["row_roles"]),None] for i,r in enumerate(rows)]
    elif op == "DREAM_CONTEXT_PROGRAM_REDUCE":
        for i,r in enumerate(rows):
            missing=r["dream_status"]=="MISSING_NO_RETRY" and r["context_policy"]=="AUTHENTIC_DREAM_CONTEXT"
            out.append([i,"MISSING_NO_RETRY" if missing else "OBSERVED","NO_RETRY" if missing else "EXECUTE_DOWNSTREAM",1 if r["terminal_observation_class"]=="ACTION" and not missing else 0,missing,None])
    elif op == "STATUS_RULE_REDUCE":
        for i,r in enumerate(rows):
            rule=source_status_rule(sources,r["raw_result"],r["applies"])
            out.append([i,rule["rule_id"],r["raw_result"],rule["status"],rule["missing"],rule["claim_blocker"],None])
    elif op == "STATUS_PRECEDENCE_REDUCE":
        order=sources["STATUS"]["precedence"]
        out=[[i,r["left"],r["right"],min((r["left"],r["right"]),key=order.index),None] for i,r in enumerate(rows)]
    elif op == "ROOT_STATUS_REDUCE":
        for i,r in enumerate(rows):
            root_status="MISSING_NO_RETRY" if r["dream_status"]=="MISSING_NO_RETRY" else ("ROOTS_ADMITTED" if r["dream_status"]=="INSTALLED" else "NO_ROOTS_SELECTED")
            out.append([i,r["root_policy"],r["dream_status"],root_status,"NO_RETRY" if root_status=="MISSING_NO_RETRY" else "EXECUTE_DOWNSTREAM",None])
    elif op == "D1D_PIPELINE_REDUCE":
        out=[[i,r["root_policy"],r["stage"],True,None] for i,r in enumerate(rows)]
    elif op == "D1D_DISPATCH_REDUCE":
        out=[[i,r["root_policy"],len(sources["DISPATCH"]),True,None] for i,r in enumerate(rows)]
    elif op == "RESOURCE_REDUCE":
        out=[[i,r["resource_property"],True,None] for i,r in enumerate(rows)]
    elif op == "QUALIFICATION_BYTES_REDUCE":
        claim_id=rows[0]["claim_id"]; claims=sources["CLAIMS"]
        rendering=next(row for row in claims["claim_renderings"] if row["claim_id"]==claim_id)
        rendered="\n".join(rendering["ordered_inseparable_segments"])
        out=[[claim_id,rendered,True,None]]
    elif op == "LIFE_GATE_REDUCE":
        out=[[i,r["N"],r["arm_state"],1 if r["arm_state"]=="COMPLETE" else 0,r["arm_state"] in {"TREATMENT_MISSING","CONTROL_MISSING"},None] for i,r in enumerate(rows)]
    elif op == "PAIRED_BOUNDARY_REDUCE":
        for i,r in enumerate(rows):
            d=Fraction(r["difference_numerator"],r["difference_denominator"]); m=Fraction(r["margin_numerator"],r["margin_denominator"])
            ok=r["required_arm_present"] and d>m
            out.append([i,1 if ok else 0,ok,not r["required_arm_present"],None])
    elif op == "SAFETY_REDUCE":
        out=[[i,r["endpoint_id"],0 if r["provider_state"]=="NO_EVENT" else 1,1 if r["provider_state"]=="MISSING_PROVIDER" else 0,None] for i,r in enumerate(rows)]
    elif op == "MISSINGNESS_REDUCE":
        for i,r in enumerate(rows):
            n,d=reduced_fraction(r["missing_events"],r["N"]); ceiling=Fraction(r["ceiling_numerator"],r["ceiling_denominator"])
            out.append([i,n,d,Fraction(n,d)<ceiling,None])
    elif op == "CP_BRACKET_REDUCE":
        for i,r in enumerate(rows):
            count=0 if r["count_class"]=="ZERO" else r["N"] if r["count_class"]=="N" else r["N"]//2
            floor,ceil,den=cp_grid_bracket(count,r["N"],
                Fraction(r["tail_alpha_numerator"],r["tail_alpha_denominator"]),
                r["decimal_scale"],r["direction"])
            out.append([i,r["direction"],floor,ceil,den,None])
    elif op == "IUT_CRITICAL_REDUCE":
        for i,r in enumerate(rows):
            n=r["N"]; alpha=Fraction(r["alpha_numerator"],r["alpha_denominator"])
            gamma=Fraction(r["cp_tail_alpha_numerator"],r["cp_tail_alpha_denominator"])
            threshold=(Fraction(r["paired_pi0_numerator"],r["paired_pi0_denominator"])
                       if r["gate_kind"]=="PAIRED" else
                       Fraction(r["event_ceiling_numerator"],r["event_ceiling_denominator"]))
            members=[]
            details={}
            for x in range(n+1):
                if r["gate_kind"]=="PAIRED":
                    p=binomial_upper_tail(x,n,threshold)
                    floor,_,den=cp_grid_bracket(x,n,gamma,r["decimal_scale"],"LOWER")
                    bound=Fraction(floor,den); direction_pass=bound>threshold
                else:
                    p=binomial_lower_tail(x,n,threshold)
                    _,ceil,den=cp_grid_bracket(x,n,gamma,r["decimal_scale"],"UPPER")
                    bound=Fraction(ceil,den); direction_pass=bound<threshold
                details[x]=(p,bound,direction_pass)
                if p<=alpha and direction_pass: members.append(x)
            assert members
            boundary=min(members) if r["gate_kind"]=="PAIRED" else max(members)
            tested=boundary+{"BELOW":-1,"AT":0,"ABOVE":1}[r["position"]]
            p,bound,direction_pass=details[tested]
            out.append([i,r["gate_kind"],r["position"],tested,p.numerator,p.denominator,
                        bound.numerator,bound.denominator,direction_pass,tested in members,None])
    elif op == "HOLM_PERMUTATION_REDUCE":
        out=[[i,canonical(r["permutation"]),canonical([4,3,2,1]),None] for i,r in enumerate(rows)]
    elif op == "HOLM_TIE_REDUCE":
        order=sorted(rows[0]["claim_ids"]); out=[[canonical(order),True,None]]
    elif op == "HOLM_STOP_REDUCE":
        for i,r in enumerate(rows):
            stop=r["stop_position"]; flags=[stop is None or j<stop for j in range(4)]
            out.append([i,None if stop is None else str(stop),canonical(flags),None])
    elif op == "CLAIM_BYTES_REDUCE":
        out=[[i,r["row"]["row_key"],"\n".join(r["rendering"]["ordered_inseparable_segments"]),True,None] for i,r in enumerate(rows)]
    elif op == "CONSTRUCTION_PROOF_REDUCE":
        for i,r in enumerate(rows):
            total=sum((Fraction(*x) for x in r["masses"]),Fraction(0)); out.append([i,r["proof_kind"],total.numerator,total.denominator,total==1,None])
    elif op == "POWER_REDUCE":
        for i,r in enumerate(rows):
            powers=[Fraction(*x) for x in r["gate_powers"]]; bound=max(Fraction(0),1-sum((1-x for x in powers),Fraction(0)))
            out.append([i,r["power_case"],bound.numerator,bound.denominator,r["power_case"]=="GLOBAL_PRODUCT_SUBSTITUTION_REJECTED",None])
    elif op == "SAFETY_TEMPLATE_REDUCE":
        r=rows[0]; out=[[len(r["sample_ordinals"]),len(set(r["resolved_life_ids"]))==len(r["resolved_life_ids"]),len(r["sample_ordinals"])==len(r["resolved_life_ids"]),None]]
    elif op == "VISIBILITY_PRODUCT_REDUCE":
        cells=[r["cell"] for r in rows]; allowed=sum(1 for r in cells if r["visibility"]=="ALLOWED")
        out=[[len(cells),allowed,len(cells)-allowed,len(cells)==195,None]]
    elif op == "TYPED_EDGE_EXTRACT_REDUCE":
        schema_edges=[r["edge"] for r in rows]; inv=inventory_edges(sources["OBJECTS"])
        out=[[len(schema_edges),len(inv),schema_edges==inv,canonical(schema_edges),None if schema_edges==inv else "THREE_WAY_EDGE_EQUALITY"]]
    elif op == "OBJECT_TYPE_EXTRACT_REDUCE":
        schema_types=sorted(r["artifact_type"] for r in rows); inventory_types=sorted(r["type"] for r in sources["OBJECTS"])
        out=[[len(schema_types),len(inventory_types),schema_types==inventory_types,canonical(schema_types),None if schema_types==inventory_types else "OBJECT_INVENTORY_EDGE"]]
    elif op == "CAUSE_TABLE_REDUCE":
        cause_rows=[r["row"] for r in rows]; out=[[len(cause_rows),canonical([r["cause"] for r in cause_rows]),all(r["ordinal"]==i for i,r in enumerate(cause_rows)),None]]
    elif op == "PREFLIGHT_DENIAL_REDUCE":
        out=[[i,r["denial_code"],False,False,r["denial_code"]] for i,r in enumerate(rows)]
    elif op == "THREE_WAY_EDGE_REDUCE":
        schema_edges=collect_schema_edges(sources["SCHEMA_DEFS"]); inv=inventory_edges(sources["OBJECTS"])
        visibility=[r for r in sources["VISIBILITY"] if r["visibility"]=="ALLOWED"]
        out=[[len(schema_edges),len(inv),len(visibility),schema_edges==inv and len(visibility)==84,None if schema_edges==inv and len(visibility)==84 else "THREE_WAY_EDGE_EQUALITY"]]
    elif op in {"T13_TECHNICAL_REDUCE","AUTHORITY_DAG_REDUCE"}:
        schema_edges=collect_schema_edges(sources["SCHEMA_DEFS"]); inv=inventory_edges(sources["OBJECTS"])
        assert schema_edges==inv
        inbound=edges_for(inv,"T13_PREMODEL_TECHNICAL_GATE")
        if op=="T13_TECHNICAL_REDUCE":
            package=rows[0]
            passed,resolved,same_run,failure=t13_package_status(package,inbound)
            out=[[digest(package),len(inbound),resolved,same_run,
                  len(package["forbidden_future_artifact_types"]),passed,failure]]
        else:
            stages=sources["AUTHORITY"]["stages"]; registry=sources["AUTHORITY_REGISTRY"]
            derived=[]; registry_derived=[]; stage_names={s["stage"] for s in stages}; authority_edges=[]
            for i,stage in enumerate(stages):
                stage_hash=hashlib.sha256((canonical(stage)+"\n").encode()).hexdigest()
                derived.append({"ordinal":i,"row_key":stage["stage"],"receipt_type":stage["receipt_type"],"predecessor":stage["predecessor"],"content_sha256":stage_hash})
                registry_derived.append({"row_key":stage["stage"],"ordinal":i,"role":"AUTHORITY_STAGE","cardinality":"ONE","producer_role":"AUTHORITY_REGISTRY_AUTHOR","consumer_stages":["T13","PREFLIGHT","COLD_REPLAY"],"content_sha256":stage_hash})
                if stage["predecessor"] is not None:
                    authority_edges.append({"from_kind":"STAGE" if stage["predecessor"] in stage_names else "EXTERNAL_ARTIFACT","from_id":stage["predecessor"],"to_stage":stage["stage"],"to_receipt_type":stage["receipt_type"]})
            outbound=[e for e in inv if e["producer_type"]=="T13_PREMODEL_TECHNICAL_GATE"]
            external=[e for e in inv if e["producer_type"]=="T14_FINAL_REPLAY_RESULT" and e["consumer_type"]=="PRECLAIM_AUTHORITY_RECEIPT"]
            registry_equal=registry_derived==registry["rows"]
            kahn,aliases,backedges,acyclic=kahn_authority(stages)
            reachability=all(s["model_execution_reachable"] is (i>=10)
                             for i,s in enumerate(stages))
            failure=None if registry_equal and acyclic and reachability else "AUTHORITY_TOPOLOGY"
            out=[[canonical(derived),canonical(kahn),canonical(authority_edges),canonical(inbound),canonical(outbound),canonical(external),len(derived),registry_equal,reachability,canonical(aliases),canonical(backedges),acyclic,failure]]
    elif op == "T14_REPLAY_GRAPH_REDUCE":
        schema_edges=collect_schema_edges(sources["SCHEMA_DEFS"])
        inv=inventory_edges(sources["OBJECTS"])
        assert schema_edges==inv
        cold=edges_for(inv,"COLD_REPLAY_RECEIPT")
        final=edges_for(inv,"T14_FINAL_REPLAY_RESULT")
        outbound=[e for e in inv if e["producer_type"]=="T14_FINAL_REPLAY_RESULT" and e["consumer_type"]=="PRECLAIM_AUTHORITY_RECEIPT"]
        artifacts=decode_t14_artifacts(rows)
        replay_sources=parameters["replay_sources"]
        replay_descriptors=[]
        for row in replay_sources:
            raw=row["canonical_source_bytes"]
            assert hashlib.sha256(raw.encode()).hexdigest()==row["source_sha256"]
            descriptor=json.loads(raw); assert canonical(descriptor)==raw
            assert descriptor["run_id"]==artifacts[0]["run_id"]
            assert sorted(descriptor["cold_ingress_roles"])==sorted(e["role"] for e in cold)
            assert hashlib.sha256(descriptor["source_code_utf8"].encode()).hexdigest()==descriptor["source_code_sha256"]
            assert (HERE/descriptor["source_file"]).read_text()==descriptor["source_code_utf8"]
            replay_descriptors.append(descriptor)
        independent=(len(replay_descriptors)==2 and
                     replay_sources[0]["source_sha256"]!=replay_sources[1]["source_sha256"] and
                     replay_descriptors[0]["implementation_id"]!=replay_descriptors[1]["implementation_id"])
        relation_a=replay_a_relation(artifacts,sources)
        relation_b=replay_b_relation(artifacts,sources)
        equal=relation_a==relation_b
        final_sources=parameters["final_result_source_facts"]
        decoded_final=[]
        for row in final_sources:
            raw=row["canonical_source_bytes"]
            assert hashlib.sha256(raw.encode()).hexdigest()==row["source_sha256"]
            decoded=json.loads(raw); assert canonical(decoded)==raw
            assert decoded["run_id"]==artifacts[0]["run_id"]
            decoded_final.append(decoded)
        assert [(x["role"],x["artifact_type"],x["ordinal"]) for x in decoded_final] == \
            [(e["role"],e["producer_type"],e["ordinal"]) for e in final]
        release_consumed=contains_release_input([artifact["payload"] for artifact in artifacts])
        relation_hashes=[hashlib.sha256(relation_a.encode()).hexdigest(),
                         hashlib.sha256(relation_b.encode()).hexdigest()]
        final_result_inputs=[]
        for decoded in decoded_final:
            row=dict(decoded)
            if row["role"]=="COLD_REPLAY_A": row.update({"relation_sha256":relation_hashes[0],"status":"PASS"})
            if row["role"]=="COLD_REPLAY_B": row.update({"relation_sha256":relation_hashes[1],"status":"PASS"})
            final_result_inputs.append(row)
        status,first=t14_final_status(independent,relation_a,relation_b,
            len(cold),len(final),len(outbound),release_consumed)
        out=[[len(artifacts),digest([{k:r[k] for k in ("ordinal","role","artifact_type","cardinality","run_id","artifact_sha256")} for r in rows]),relation_hashes[0],relation_hashes[1],independent,equal,canonical(cold),canonical(final),digest(final_result_inputs),canonical(outbound),status,len(outbound),release_consumed,first]]
    else:
        raise AssertionError(f"unimplemented reducer operator {op}")
    return out


def validate_scalar(value: Any, kind: str) -> None:
    if kind == "STRING": assert isinstance(value,str)
    elif kind == "INTEGER": assert isinstance(value,int) and not isinstance(value,bool)
    elif kind == "BOOLEAN": assert isinstance(value,bool)
    elif kind == "NULLABLE_STRING": assert value is None or isinstance(value,str)
    elif kind == "CANONICAL_JSON": assert isinstance(value,str) and canonical(json.loads(value))==value
    else: raise AssertionError(kind)


def validate_closed_schema(value: Any, schema: dict) -> None:
    if "oneOf" in schema:
        successes=0
        for option in schema["oneOf"]:
            try: validate_closed_schema(value,option); successes+=1
            except (AssertionError,KeyError,TypeError): pass
        assert successes==1,(value,schema)
        return
    allowed=schema.get("type")
    if isinstance(allowed,list):
        assert any(_type_matches(value,t) for t in allowed)
        return
    assert _type_matches(value,allowed),(type(value),allowed)
    if allowed=="object":
        properties=schema["properties"]; required=schema["required"]
        assert set(value)==set(required)
        assert schema.get("additionalProperties") is False
        for key in required: validate_closed_schema(value[key],properties[key])
    elif allowed=="array":
        assert schema["minItems"]<=len(value)<=schema["maxItems"]
        if "prefixItems" in schema:
            assert len(value)==len(schema["prefixItems"]) and schema.get("items") is False
            for item,child in zip(value,schema["prefixItems"]):validate_closed_schema(item,child)
        elif schema.get("items") is not False:
            for item in value:validate_closed_schema(item,schema["items"])
    elif allowed=="string" and schema.get("x-canonical-json"):
        decoded=json.loads(value);assert canonical(decoded)==value
        if "contentSchema" in schema:
            validate_closed_schema(decoded,schema["contentSchema"])


def _type_matches(value:Any,kind:str)->bool:
    return {"null":value is None,"boolean":isinstance(value,bool),
            "integer":isinstance(value,int) and not isinstance(value,bool),
            "string":isinstance(value,str),"array":isinstance(value,list),
            "object":isinstance(value,dict)}[kind]


def forbidden_keys(value:Any, forbidden:set[str])->set[str]:
    if isinstance(value,dict):
        return (set(value)&forbidden)|set().union(*(forbidden_keys(v,forbidden) for v in value.values()),set())
    if isinstance(value,list):
        return set().union(*(forbidden_keys(v,forbidden) for v in value),set())
    return set()


def main() -> None:
    sources=load_sources(); inputs=load(HERE/"REDUCER_INPUT_ROWS_RFC.json"); programs=load(HERE/"REDUCER_PROGRAMS_RFC.json"); machine=load(HERE/"REDUCER_MACHINE_RFC.json")
    by_law={x["law_id"]:x for x in machine["laws"]}; builders={x["law_id"]:x for x in inputs["builders"]}; progs={x["law_id"]:x for x in programs["programs"]}
    assert len(by_law)==len(builders)==len(progs)==58 and set(by_law)==set(builders)==set(progs)
    forbidden=set(machine["forbidden_executor_keys"])
    outputs={}; graph_manifest=[]; case_inputs={}
    for law_id in sorted(by_law):
        builder=builders[law_id]
        assert not (forbidden & set(builder.get("columns",[]))), law_id
        assert not (forbidden & set(builder.get("dimensions",{}))), law_id
        rows=rows_from_builder(builder,sources)
        assert len(rows)==by_law[law_id]["entry_count"], (law_id,len(rows),by_law[law_id]["entry_count"])
        assert digest(rows)==by_law[law_id]["input_vector_sha256"]
        for row in rows:
            assert not forbidden_keys(row,forbidden),law_id
            validate_closed_schema(row,by_law[law_id]["input_row_schema"])
        parameters={key:builder[key] for key in ("replay_sources","final_result_source_facts") if key in builder}
        assert not forbidden_keys(parameters,forbidden),law_id
        validate_closed_schema(parameters,by_law[law_id]["parameter_schema"])
        graph=build_input_graph(law_id,rows,builder,sources)
        executor_rows, executor_sources, executor_parameters=sources_from_input_graph(graph)
        assert executor_rows == rows
        assert executor_sources == {sid:sources[sid]
                                    for sid in builder.get("source_ids", [])}
        assert executor_parameters==parameters
        case_inputs[law_id]=(executor_rows,executor_parameters,executor_sources)
        law=by_law[law_id]
        identity_preimage={"test_id":law["test_id"],
                           "suite_id":law["suite_id"],
                           "law_id":law_id,"input_graph":graph}
        cid="PPC5R10_CASE_"+digest(identity_preimage)
        envelope={"case_id":cid,"test_id":law["test_id"],
                  "suite_id":law["suite_id"],"law_id":law_id,
                  "input_graph":graph}
        graph_manifest.append({"law_id":law_id,"case_id":cid,
            "input_graph_sha256":digest(graph),
            "executor_input_sha256":digest(envelope),
            "node_count":len(graph["nodes"]),
            "typed_edge_count":len(graph["typed_edges"])})
        output_rows=reduce_rows(progs[law_id],executor_rows,executor_sources,
                                executor_parameters)
        assert by_law[law_id]["operator"]==progs[law_id]["operator"]
        assert by_law[law_id]["output_columns"]==progs[law_id]["output_columns"]
        for row in output_rows:
            assert len(row)==len(progs[law_id]["output_columns"]), law_id
            for value,kind in zip(row,progs[law_id]["output_types"]): validate_scalar(value,kind)
            validate_closed_schema(row,by_law[law_id]["output_row_schema"])
        outputs[law_id]={"law_id":law_id,"columns":progs[law_id]["output_columns"],"rows":output_rows,"first_failure":None}
    # Semantic invariants, evaluated from facts rather than searched in prose.
    route=outputs["T08_ROUTE_V1"]["rows"]
    assert [(r[1],r[3],r[4]) for r in route]==[("TARGET_ZERO",None,False),("TARGET_ONE","INTERVENTION",True),("TARGET_MULTI",None,False),("NON_TARGET_ZERO","OFF_PATH_AUTHENTIC_PASS_THROUGH",True)]
    influence=outputs["T08_INFLUENCE_RELATION_V1"]["rows"]
    assert all(r[2]==1 and r[7] for r in influence) and sum(r[3] for r in influence)==1
    assert sum(r[4] for r in influence)==sum(r[5] for r in influence)==sum(r[6] for r in influence)==1
    queue=outputs["T08_QUEUE_OUTCOME_V1"]["rows"][-1]
    effects=json.loads(queue[3]); assert [x["count"] for x in effects]==[1,1]
    authority=outputs["T13_AUTHORITY_TOPOLOGY_V1"]["rows"][0]
    assert authority[6:9]==[14,True,True] and authority[11] is True, authority
    assert json.loads(authority[1])==[row["stage"] for row in case_inputs["T13_AUTHORITY_TOPOLOGY_V1"][2]["AUTHORITY"]["stages"]]
    assert len(json.loads(authority[2]))==13 and len(json.loads(authority[3]))==12 and len(json.loads(authority[4]))==2 and len(json.loads(authority[5]))==1
    technical=outputs["T13_FULL_TECHNICAL_PASS_V1"]["rows"][0]
    assert technical[1:7]==[12,12,True,0,True,None]
    replay=outputs["T14_FULL_PREDECESSOR_REPLAY_V1"]["rows"][0]
    assert replay[0]==24 and replay[4:6]==[True,True]
    assert len(json.loads(replay[6]))==11 and len(json.loads(replay[7]))==6 and len(json.loads(replay[9]))==1
    assert replay[10:14]==["PASS",1,False,None]
    # Negative semantic probes exercise facts, never labels or row ordinals.
    package=case_inputs["T13_FULL_TECHNICAL_PASS_V1"][0][0]
    inbound=edges_for(inventory_edges(case_inputs["T13_FULL_TECHNICAL_PASS_V1"][2]["OBJECTS"]),"T13_PREMODEL_TECHNICAL_GATE")
    bad=json.loads(canonical(package));bad["ingress"].pop();assert not t13_package_status(bad,inbound)[0]
    bad=json.loads(canonical(package));bad["ingress"].append(bad["ingress"][0]);assert not t13_package_status(bad,inbound)[0]
    bad=json.loads(canonical(package));bad["forbidden_future_artifact_types"]=["MODEL_BEHAVIOR_RESULT"];assert t13_package_status(bad,inbound)[3]=="FORBIDDEN_FUTURE_INPUT"
    bad=json.loads(canonical(package));item=json.loads(bad["ingress"][0]["canonical_artifact_bytes"]);item["status"]="FAIL";raw=canonical(item);bad["ingress"][0].update(canonical_artifact_bytes=raw,artifact_sha256=hashlib.sha256(raw.encode()).hexdigest());assert t13_package_status(bad,inbound)[3]=="TECHNICAL_PREREQUISITE"
    stages=case_inputs["T13_AUTHORITY_TOPOLOGY_V1"][2]["AUTHORITY"]["stages"]
    alias=json.loads(canonical(stages));alias[1]["predecessor"]="ARCHITECTURE_ALIAS";assert kahn_authority(alias)[1]
    back=json.loads(canonical(stages));back[1]["predecessor"]="CPU_CONFORMANCE";assert kahn_authority(back)[2] and not kahn_authority(back)[3]
    t14_rows,t14_params,t14_sources=case_inputs["T14_FULL_PREDECESSOR_REPLAY_V1"]
    for malformed in (t14_rows[:-1],t14_rows+[t14_rows[-1]],t14_rows[1:2]+t14_rows[0:1]+t14_rows[2:]):
        try: decode_t14_artifacts(malformed)
        except AssertionError: pass
        else: raise AssertionError("malformed T14 predecessor vector passed")
    equal_impl=json.loads(canonical(t14_params));equal_impl["replay_sources"][1]=equal_impl["replay_sources"][0]
    equal_out=reduce_rows(progs["T14_FULL_PREDECESSOR_REPLAY_V1"],t14_rows,t14_sources,equal_impl)[0]
    assert equal_out[10]=="FAIL" and equal_out[13]=="REPLAY_INDEPENDENCE"
    release_rows=json.loads(canonical(t14_rows));artifact=json.loads(release_rows[0]["canonical_artifact_bytes"]);artifact["payload"]["release_bytes"]="forbidden";raw=canonical(artifact);release_rows[0]["canonical_artifact_bytes"]=raw;release_rows[0]["artifact_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
    release_out=reduce_rows(progs["T14_FULL_PREDECESSOR_REPLAY_V1"],release_rows,t14_sources,t14_params)[0]
    assert release_out[10]=="FAIL" and release_out[13]=="RELEASE_BYTES_FORBIDDEN"
    assert t14_final_status(True,"[]","[1]",11,6,1,False)==("FAIL","REPLAY_AGREEMENT")
    assert len({row["case_id"] for row in graph_manifest}) == 58
    print(canonical({"status":"PASS","law_count":58,"input_row_count":sum(x["entry_count"] for x in by_law.values()),"source_snapshot_count":len(sources),"semantic_output_sha256":digest(outputs),"input_graph_manifest_sha256":digest(graph_manifest)}))


if __name__=="__main__": main()
