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
}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)


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
    if kind=="dispatch_binding":
        return {"field_count":len(sources["DISPATCH"]),"ordered_rows_sha256":hashlib.sha256(canonical(sources["DISPATCH"]).encode()).hexdigest()}
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
