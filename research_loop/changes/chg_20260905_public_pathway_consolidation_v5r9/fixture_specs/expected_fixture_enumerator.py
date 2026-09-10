#!/usr/bin/env python3
"""Normative expected-set enumerator for PPC5r9 T02--T14.

The algorithm starts only from each frozen spec's finite axis values,
closed suite-applicability relations, mutation-applicability relation, and
first-failure order. It never reads expected_branches,
negative_mutations, or precedence_probes. Those separately materialized
rows can therefore be checked against this derived vector rather than
re-emitted circularly.

Proposal authoring only: this source executes no fixture and touches no
model, tokenizer, trainer, environment, CPU-behavioral, or GPU pathway.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")) + "\n"


def positive_key(test_id, suite_id, axes, kind="P"):
    return canonical({
        "a": [[a["axis_id"], int(a["value_ordinal"]), a["value_id"]]
              for a in axes],
        "k": kind, "s": suite_id, "t": test_id, "v": 1,
    })


def negative_key(test_id, base_key, mutation_id):
    return canonical({
        "b": hashlib.sha256(base_key.encode()).hexdigest(),
        "k": "N", "m": mutation_id, "t": test_id, "v": 1,
    })


def semantic_scenario(test_id, suite_id, axes):
    facts=[{"name":a["axis_id"],"ordinal":a["value_ordinal"],
            "value_type":a["value_type"],"value":copy.deepcopy(a["value"])}
           for a in axes]
    payload=axes[0]["value"] if len(axes)==1 and axes[0]["value_type"]=="OBJECT" else None
    subject=copy.deepcopy(payload) if payload is not None else {"tokens":[str(a["value"]).split(":") for a in axes]}
    worlds=[]
    if test_id=="PPC5R9_T08" and suite_id=="ROUTE":
        target,count=str(axes[0]["value"]).split(":"); emitted={"ZERO":0,"ONE":1,"MULTI":2}[count]
        worlds=[{"world_id":"BEFORE","target_class":target,"emitted_public_records":0},
                {"world_id":"AFTER","target_class":target,"emitted_public_records":emitted}]
        outcome=("INTERVENTION" if target=="TARGET" and count=="ONE" else
                 "OFF_PATH_AUTHENTIC_PASS_THROUGH" if target=="NON_TARGET" and count=="ZERO" else
                 "RUN_INVALID")
        result={"target_class":target,"emitted_public_records":emitted,
                "route_outcome":outcome,"public_continuation":outcome!="RUN_INVALID"}
    elif test_id=="PPC5R9_T08" and suite_id=="INFLUENCE_RELATION":
        changed=str(axes[0]["value"]); permitted=changed=="EMITTED_PUBLIC_BYTES"
        worlds=[{"world_id":"BEFORE","changed_input":None,"emitted_public_bytes":"PUBLIC_BASE",
                 "condition":"C0","source":"S0","match_keys":"K0","provider_scores":"P0","nonce":"N0","mapping":"M0"},
                {"world_id":"AFTER","changed_input":changed,
                 "emitted_public_bytes":"PUBLIC_EMITTED" if permitted else "PUBLIC_BASE",
                 "condition":"C1" if changed=="condition" else "C0",
                 "source":"S1" if changed=="source" else "S0",
                 "match_keys":"K1" if changed=="match_keys" else "K0",
                 "provider_scores":"P1" if changed=="provider_scores" else "P0",
                 "nonce":"N1" if changed=="nonce" else "N0",
                 "mapping":"M1" if changed=="mapping" else "M0"}]
        result={"changed_input":changed,"public_output_changed":permitted,
                "influence_class":"PERMITTED" if permitted else "FORBIDDEN_NONINFLUENCE"}
    elif test_id=="PPC5R9_T08" and suite_id=="QUEUE_OUTCOME":
        row=axes[0]["value"]; route=row["queue_state"]
        outcome=("FLUSHED" if route=="QUEUED" and row["terminal_class"]=="VALID" else
                 "DISCARDED" if route=="QUEUED" else
                 "ORDERED_DISCARD" if route=="TWO_OUTSTANDING" else "NONE")
        slots=([{"slot_id":"SLOT_0","effect":"DISCARD","effect_count":1},
                {"slot_id":"SLOT_1","effect":"DISCARD","effect_count":1}]
               if route=="TWO_OUTSTANDING" else
               [{"slot_id":"SLOT_0","effect":outcome,"effect_count":1}])
        result={"route_state":route,"terminal_effect":outcome,"slot_effects":slots,
                "queue_exactly_once":all(row["effect_count"]==1 for row in slots)}
        worlds=[{"world_id":"QUEUE_INPUT","route_state":route,"terminal_class":row["terminal_class"],
                 "slot_ids":["SLOT_0","SLOT_1"] if route=="TWO_OUTSTANDING" else ["SLOT_0"]}]
    else:
        result={"relation_holds":True,"fact_count":len(facts),
                "subject_sha256":hashlib.sha256(canonical(subject).encode()).hexdigest()}
    relation={"facts":facts,"subject":subject,"worlds":worlds}
    return {"expected_result":result,
            "input_relation_sha256":hashlib.sha256(canonical(relation).encode()).hexdigest(),
            "law_id":f"{test_id}_{suite_id}_RELATION_V1"}


def pass_output(test_id, suite_id, axes, branch_key):
    scenario=semantic_scenario(test_id,suite_id,axes)
    return canonical({
        "branch_key_sha256": hashlib.sha256(branch_key.encode()).hexdigest(),
        "decision": "PASS", "derived_result":scenario["expected_result"],
        "input_relation_sha256":scenario["input_relation_sha256"],
        "law_id":scenario["law_id"],"test_id": test_id,
    })


def enumerate_spec(spec):
    tid = spec["test_id"]
    out = []
    axis_values = {}
    for axis in spec["finite_axes"]:
        for encoded in axis["finite_values"]:
            value = json.loads(encoded)
            if value["axis_id"] != axis["axis_id"]:
                raise ValueError(f"{tid}: finite-axis identity mismatch")
            coordinate = (value["axis_id"], int(value["value_ordinal"]),
                          value["value_id"])
            if coordinate in axis_values:
                raise ValueError(f"{tid}: duplicate finite-axis coordinate")
            axis_values[coordinate] = value

    def realize(coordinates):
        try:
            return [axis_values[(axis_id, int(ordinal), value_id)]
                    for axis_id, ordinal, value_id in coordinates]
        except KeyError as exc:
            raise ValueError(f"{tid}: applicability names a non-axis value {exc}") from exc

    positive_count = 0
    for suite in sorted(spec["suite_applicability_tables"],
                        key=lambda row: row["suite_ordinal"]):
        if suite["positive_expected_result_law"] != "PASS_WITH_BRANCH_KEY_SHA256_AND_DERIVED_RELATION_V1":
            raise ValueError(f"{tid}: unknown positive result law")
        for row in sorted(suite["rows"], key=lambda item: item["row_ordinal"]):
            axes = realize(row["axis_value_coordinates"])
            key = positive_key(tid, suite["suite_id"], axes)
            out.append({"branch_key": key,
                        "expected_output_canonical_json": pass_output(tid, suite["suite_id"], axes, key),
                        "expected_first_failure": None})
            positive_count += 1
    if positive_count != spec["expected_positive_count"]:
        raise ValueError(f"{tid}: positive applicability cardinality drift")

    mutations = sorted(spec["mutation_applicability_table"],
                       key=lambda row: row["mutation_ordinal"])
    for row in mutations:
        base = positive_key(tid, row["base_suite_id"],
                            realize(row["base_axis_value_coordinates"]))
        out.append({
            "branch_key": negative_key(tid, base, row["mutation_id"]),
            "expected_output_canonical_json": None,
            "expected_first_failure": row["expected_first_failure"],
        })
    if len(mutations) != spec["expected_mutation_count"]:
        raise ValueError(f"{tid}: mutation applicability cardinality drift")

    order = spec["first_failure_order"]
    for ordinal, (first, second) in enumerate(zip(order, order[1:])):
        axes = [
            {"axis_id": "EARLIER_FAILURE", "value_ordinal": ordinal,
             "value_id": first},
            {"axis_id": "LATER_FAILURE", "value_ordinal": ordinal,
             "value_id": second},
        ]
        key = positive_key(tid, "PRECEDENCE_PROBE", axes, "Q")
        out.append({"branch_key": key,
                    "expected_output_canonical_json": None,
                    "expected_first_failure": first})
    if len(order) - 1 != spec["expected_precedence_probe_count"]:
        raise ValueError(f"{tid}: precedence cardinality drift")
    if len(out) != spec["logical_expected_count"]:
        raise ValueError(f"{tid}: logical cardinality drift")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("universe", type=Path)
    ns = ap.parse_args()
    universe = json.loads(ns.universe.read_text())
    root = ns.universe.parent.parent
    vector = []
    for entry in universe["fixture_spec_index"]:
        vector.extend(enumerate_spec(json.loads((root / entry["relative_path"]).read_text())))
    print(canonical(vector), end="")


if __name__ == "__main__":
    main()
