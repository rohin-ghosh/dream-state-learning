"""Proposal replay A: direct predecessor-order semantic reconstruction.

This module owns its complete value semantics. It receives no reducer
callback and imports no implementation from replay B or the validator.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction


ROLE_KIND = {
    "PPC5R9_T02_RESULT":"controller_transition", "PPC5R9_T03_RESULT":"queue_effect_per_slot",
    "PPC5R9_T04_RESULT":"route_lineage_audit", "PPC5R9_T05_RESULT":"provider_audit",
    "PPC5R9_T06_RESULT":"emission_influence", "PPC5R9_T07_RESULT":"dispatch_binding",
    "PPC5R9_T08_RESULT":"dream_context_status", "PPC5R9_T09_RESULT":"d1d_stage",
    "PPC5R9_T10_RESULT":"life_gate_aggregate", "PPC5R9_T11_RESULT":"d1a_control_membership",
    "PPC5R9_T12_RESULT":"pointwise_power_support", "PPC5R9_T13_RESULT":"resource_accounting",
    "PRE_ENTROPY_DESIGN_LOCK":"overlap_membership", "ENTROPY_ACQUISITION":"candidate_decision",
    "POPULATED_RUN_LOCK":"dependency_decision", "STATIC_SEAL_PAIR":"claim_qualification",
    "REVIEW_RECEIPT":"presence_receipt", "ADVOCATE_RECEIPT":"presence_receipt",
    "COMPLETE_RUN_MANIFEST":"presence_receipt", "ANALYSIS_BUNDLE":"presence_receipt",
    "D1A_CONTROL_SET_MANIFEST":"presence_receipt",
    "COMPLETE_MODEL_VIEW_MANIFEST":"presence_receipt",
    "ROUTE_LINEAGE_AUDIT":"presence_receipt", "PROVIDER_AUDIT":"presence_receipt",
}

EXPECTED_DISPATCH_REGISTRY_SHA256 = "da50392428b1403836a4bbeefe3c53774f46e71f52e141af69e4c4b09ab248e9"
EXPECTED_DISPATCH_KEYS = ["MODEL_INFERENCE","TOKENIZER_EXECUTION","EMBEDDING_EXECUTION",
    "TRAINING","CANARY","CPU_BEHAVIORAL","GPU_BEHAVIORAL","GPU_JOB"]
EXPECTED_DISPATCH_CONTENT_HASHES = [
    "626135c8841910bb8322b8ad7d6d2e7c770ffb14d6b3cea1089ea14a524d6ad1",
    "93390b6d2fb543cbed8e0efbbbe6e31eeb4cff6f9e8f6d46b8cd598ecc9389c6",
    "fd6da980a5887ca8da520be9c4d262e878f8e2e0b7dec14e852437fa93988477",
    "033547039ef9027ede7ded8047cf5303adb760b261544ff5e5ad048dafc0f611",
    "ba917d9958666f69cc79a0ee5e51ff45a419174ab22a69791fb24d14020bd3bd",
    "977cf0f175c317cd60f17559b1c8553dd9b0a1b25bfdbf5ad44aceb21e4f9608",
    "d5719f192a303ffb79633e2c7a4f09d646963b1790c6568f3b0ebd421248e0b7",
    "7b54dcc23a21308b8ff398e55c4ec71a8f24baab6683a61efbe5f204f64daedd"]


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def registry_self_hash_valid(registry):
    body=dict(registry);claimed=body.pop("self_hash",None)
    if not isinstance(claimed,str): return False
    pre=(body.get("contract","")+"\0"+str(body.get("schema_version"))+"\0"+
         body.get("artifact_type","")+"\0"+canonical(body)+"\n")
    return hashlib.sha256(pre.encode()).hexdigest()==claimed


def dispatch_binding(f, sources):
    registry=sources["DISPATCH_REGISTRY"];rows=registry.get("rows",[])
    keys=[row.get("row_key") for row in rows]
    return {"declared_scope":f["dispatch_scope"],
        "scope_valid":f["dispatch_scope"]=="ALL_REGISTERED_ROWS",
        "registry_sha256":hashlib.sha256(canonical(registry).encode()).hexdigest(),
        "registry_identity_valid":hashlib.sha256(canonical(registry).encode()).hexdigest()==EXPECTED_DISPATCH_REGISTRY_SHA256,
        "registry_self_hash_valid":registry_self_hash_valid(registry),
        "row_count":len(rows),"row_count_valid":len(rows)==8,
        "row_order_valid":keys==EXPECTED_DISPATCH_KEYS and registry.get("ordered_row_keys")==EXPECTED_DISPATCH_KEYS,
        "role_binding_valid":all(row.get("ordinal")==i and row.get("role")=="ALLOWED_DISPATCH_CLASS" and
            row.get("cardinality")=="ONE" and row.get("producer_role")=="ALLOWED_DISPATCH_REGISTRY_AUTHOR"
            for i,row in enumerate(rows)),
        "consumer_stages_valid":all(row.get("consumer_stages")==["PRE_MODEL_AUTHORITY","PREFLIGHT"] for row in rows),
        "content_hashes_valid":[row.get("content_sha256") for row in rows]==EXPECTED_DISPATCH_CONTENT_HASHES}


def downstream(facts, intervention):
    target=facts["assigned_target_key"]==facts["read_key"]
    count=len(facts["matching_route_ids"])
    if target and count==1: emitted=intervention
    elif not target and count==0: emitted=facts["provider_response_bytes"]
    else: return (None,None,None,None)
    public={"last_read":emitted}
    view=canonical({"last_read":emitted,"static_context_bytes":facts["static_context_bytes"]})
    behavior=canonical({"model_view":view,"tool_space":"COMPILER_GYM"})
    return emitted,public,view,behavior


def value(kind, f, sources):
    if kind=="controller_transition":
        return {"slot_id":f["slot_id"],"next_state":"CONSUMED" if f["trigger"]=="OBSERVE" and f["route_match_count"]==1 else "INVALID"}
    if kind=="queue_effect_per_slot":
        valid=f["route_target_class"]=="TARGET" and f["route_match_count"]==1 and f["schedule_state"]=="COMPLETE"
        return {"effects":[{"slot_id":slot,"ordinal":i,"effect":"CONSUME" if valid else "DISCARD","count":1} for i,slot in enumerate(f["ordered_slots"])]}
    if kind=="route_lineage_audit":
        return {"match_count":len(f["matching_route_ids"]),"target_read":f["assigned_target_key"]==f["read_key"],"route_ids_sha256":hashlib.sha256(canonical(f["matching_route_ids"]).encode()).hexdigest()}
    if kind=="provider_audit":
        return {"status":f["provider_status"],"public_bytes_sha256":hashlib.sha256(f["provider_public_bytes"].encode()).hexdigest()}
    if kind=="emission_influence":
        left=downstream(f,f["left_intervention_payload_bytes"]);right=downstream(f,f["right_intervention_payload_bytes"])
        return {"emission_changed":left[0]!=right[0],"public_changed":left[1]!=right[1],"model_view_changed":left[2]!=right[2],"behavior_input_changed":left[3]!=right[3]}
    if kind=="dispatch_binding": return dispatch_binding(f,sources)
    if kind=="dream_context_status":
        return {"status":f["dream_status"],"continuation":"NO_RETRY" if f["dream_status"]=="MISSING_NO_RETRY" else "EXECUTE_DOWNSTREAM","context_policy":f["context_policy"]}
    if kind=="d1d_stage": return {"root_policy":f["root_policy"],"stage":f["stage"],"reachable":True}
    if kind=="life_gate_aggregate": return {"N":f["N"],"complete":f["present_required_arms"]==2*f["N"]}
    if kind=="d1a_control_membership": return {"sample_ordinal":f["sample_ordinal"],"control_count":len(f["controls"]),"unique":len(f["controls"])==len(set(f["controls"]))}
    if kind=="pointwise_power_support":
        total=sum((Fraction(*m)*Fraction(*b) for m,b in zip(f["masses"],f["conditional_bounds"])),Fraction(0))
        return {"bound_numerator":total.numerator,"bound_denominator":total.denominator}
    if kind=="resource_accounting": return {"physical_total_by_kind":{"TOKENS":sum(x["amount"] for x in f["events"] if x["kind"]=="TOKENS")},"event_count":len({x["event_id"] for x in f["events"]})}
    if kind=="overlap_membership": return {"intersection":sorted(set(f["left_ids"])&set(f["right_ids"]))}
    if kind=="candidate_decision": return {"pass":all(f["required_gates"])}
    if kind=="dependency_decision": return {"pass":f["candidate_pass"] and all(f["required_dependencies"])}
    if kind=="claim_qualification":
        rendering=next(row for row in sources["CLAIMS"]["claim_renderings"] if row["claim_id"]==f["claim_id"])
        raw="\n".join(rendering["ordered_inseparable_segments"])
        return {"claim_id":f["claim_id"],"rendered_bytes_sha256":hashlib.sha256(raw.encode()).hexdigest()}
    if kind=="presence_receipt":
        return {"present":f["present"],"accepted":f["present"] is True}
    raise AssertionError(kind)


def reconstruct(artifacts: list[dict], sources: dict) -> str:
    relation=[]
    for artifact in artifacts:
        kind=ROLE_KIND.get(artifact["role"])
        if kind is not None:
            relation.append({"relation_kind":kind,"primary_key":artifact["role"],
                             "canonical_value_json":canonical(value(kind,artifact["payload"],sources))})
    relation.sort(key=lambda row:(row["relation_kind"],row["primary_key"]))
    return canonical(relation)
