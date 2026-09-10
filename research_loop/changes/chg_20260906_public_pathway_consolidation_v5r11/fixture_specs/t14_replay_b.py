"""Proposal replay B: role-indexed, handler-table semantic reconstruction.

The complete semantic implementation is local to this module. No callback or
code is shared with replay A or the validator.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction


ROLE_KIND = dict([
    ("PPC5R9_T02_RESULT","controller_transition"),("PPC5R9_T03_RESULT","queue_effect_per_slot"),
    ("PPC5R9_T04_RESULT","route_lineage_audit"),("PPC5R9_T05_RESULT","provider_audit"),
    ("PPC5R9_T06_RESULT","emission_influence"),("PPC5R9_T07_RESULT","dispatch_binding"),
    ("PPC5R9_T08_RESULT","dream_context_status"),("PPC5R9_T09_RESULT","d1d_stage"),
    ("PPC5R9_T10_RESULT","life_gate_aggregate"),("PPC5R9_T11_RESULT","d1a_control_membership"),
    ("PPC5R9_T12_RESULT","pointwise_power_support"),("PPC5R9_T13_RESULT","resource_accounting"),
    ("PRE_ENTROPY_DESIGN_LOCK","overlap_membership"),("ENTROPY_ACQUISITION","candidate_decision"),
    ("POPULATED_RUN_LOCK","dependency_decision"),("STATIC_SEAL_PAIR","claim_qualification")])


def cj(value): return json.dumps(value,ensure_ascii=False,separators=(",",":"),sort_keys=True)
def sha(value): return hashlib.sha256(value.encode()).hexdigest()


def emission_tuple(f, payload):
    matches=len(f["matching_route_ids"])
    if f["read_key"]==f["assigned_target_key"] and matches==1: leaf=payload
    elif f["read_key"]!=f["assigned_target_key"] and matches==0: leaf=f["provider_response_bytes"]
    else: return [None,None,None,None]
    public={"last_read":leaf};view=cj({"last_read":leaf,"static_context_bytes":f["static_context_bytes"]})
    return [leaf,public,view,cj({"model_view":view,"tool_space":"COMPILER_GYM"})]


def semantic(kind, f, sources):
    handlers={
        "controller_transition":lambda:{"next_state":"CONSUMED" if (f["trigger"],f["route_match_count"])==("OBSERVE",1) else "INVALID","slot_id":f["slot_id"]},
        "route_lineage_audit":lambda:{"match_count":len(f["matching_route_ids"]),"route_ids_sha256":sha(cj(f["matching_route_ids"])),"target_read":f["read_key"]==f["assigned_target_key"]},
        "provider_audit":lambda:{"public_bytes_sha256":sha(f["provider_public_bytes"]),"status":f["provider_status"]},
        "dispatch_binding":lambda:{"field_count":len(sources["DISPATCH"]),"ordered_rows_sha256":sha(cj(sources["DISPATCH"]))},
        "dream_context_status":lambda:{"context_policy":f["context_policy"],"continuation":"NO_RETRY" if f["dream_status"]=="MISSING_NO_RETRY" else "EXECUTE_DOWNSTREAM","status":f["dream_status"]},
        "d1d_stage":lambda:{"reachable":True,"root_policy":f["root_policy"],"stage":f["stage"]},
        "life_gate_aggregate":lambda:{"N":f["N"],"complete":f["present_required_arms"]//2==f["N"] and f["present_required_arms"]%2==0},
        "d1a_control_membership":lambda:{"control_count":len(f["controls"]),"sample_ordinal":f["sample_ordinal"],"unique":len(set(f["controls"]))==len(f["controls"])},
        "resource_accounting":lambda:{"event_count":len(dict.fromkeys(x["event_id"] for x in f["events"])),"physical_total_by_kind":{"TOKENS":sum(x["amount"] for x in f["events"] if x["kind"]=="TOKENS")}},
        "overlap_membership":lambda:{"intersection":sorted(x for x in f["left_ids"] if x in set(f["right_ids"]))},
        "candidate_decision":lambda:{"pass":False not in f["required_gates"]},
        "dependency_decision":lambda:{"pass":bool(f["candidate_pass"] and False not in f["required_dependencies"])},
    }
    if kind=="queue_effect_per_slot":
        effect="CONSUME" if f["route_target_class"]=="TARGET" and f["route_match_count"]==1 and f["schedule_state"]=="COMPLETE" else "DISCARD"
        return {"effects":[{"count":1,"effect":effect,"ordinal":n,"slot_id":slot} for n,slot in enumerate(f["ordered_slots"])]}
    if kind=="emission_influence":
        a=emission_tuple(f,f["left_intervention_payload_bytes"]);b=emission_tuple(f,f["right_intervention_payload_bytes"])
        return dict(zip(["emission_changed","public_changed","model_view_changed","behavior_input_changed"],[a[i]!=b[i] for i in range(4)]))
    if kind=="pointwise_power_support":
        total=sum((Fraction(m[0],m[1])*Fraction(b[0],b[1]) for m,b in zip(f["masses"],f["conditional_bounds"])),Fraction())
        return {"bound_denominator":total.denominator,"bound_numerator":total.numerator}
    if kind=="claim_qualification":
        by_id={row["claim_id"]:row for row in sources["CLAIMS"]["claim_renderings"]}
        text="\n".join(by_id[f["claim_id"]]["ordered_inseparable_segments"])
        return {"claim_id":f["claim_id"],"rendered_bytes_sha256":sha(text)}
    if kind not in handlers: raise AssertionError(kind)
    return handlers[kind]()


def reconstruct(artifacts: list[dict], sources: dict) -> str:
    indexed={row["role"]:row["payload"] for row in artifacts};result=[]
    for role in sorted(ROLE_KIND,key=lambda r:(ROLE_KIND[r],r)):
        kind=ROLE_KIND[role]
        result.append({"canonical_value_json":cj(semantic(kind,indexed[role],sources)),
                       "primary_key":role,"relation_kind":kind})
    return cj(result)
