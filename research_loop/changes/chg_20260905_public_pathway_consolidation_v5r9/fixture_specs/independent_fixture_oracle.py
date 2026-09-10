#!/usr/bin/env python3
"""Independent structural/set oracle for the frozen PPC5r9 fixtures.

Root algorithm: literal relational projection into maps/sets, not the
nested-loop normative enumerator. It never imports authoring or enumeration
code. It does not execute a fixture; it validates frozen proposal bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path


COUNTS = {
    "PPC5R9_T02": (61, 168, 19), "PPC5R9_T03": (346, 1469, 25),
    "PPC5R9_T04": (40, 109, 18), "PPC5R9_T05": (34, 99, 17),
    "PPC5R9_T06": (12, 72, 17), "PPC5R9_T07": (46, 323, 22),
    "PPC5R9_T08": (19, 64, 19), "PPC5R9_T09": (118, 138, 17),
    "PPC5R9_T10": (46, 81, 22), "PPC5R9_T11": (80, 67, 22),
    "PPC5R9_T12": (543, 2924, 23), "PPC5R9_T13": (32, 238, 24),
    "PPC5R9_T14": (1, 229, 25),
}


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def independent_key(row, tid, kind):
    if kind in ("P", "Q"):
        triples = list(map(lambda x: [x["axis_id"], int(x["value_ordinal"]), x["value_id"]], row["axis_values"]))
        return canonical(dict(a=triples, k=kind, s=row["suite_id"], t=tid, v=1))
    return canonical(dict(b=sha(row["base_positive_branch_key"]), k="N", m=row["mutation_id"], t=tid, v=1))


def changed_leaf_paths(left, right, path=""):
    if type(left) is not type(right):
        return [path]
    if isinstance(left, dict):
        if set(left) != set(right):
            return [path + "/<keys>"]
        out = []
        for key in sorted(left):
            out += changed_leaf_paths(left[key], right[key], path + "/" + key.replace("~", "~0").replace("/", "~1"))
        return out
    if isinstance(left, list):
        if len(left) != len(right):
            return [path + "/<length>"]
        out = []
        for i, (a, b) in enumerate(zip(left, right)):
            out += changed_leaf_paths(a, b, path + f"/{i}")
        return out
    return [] if left == right else [path]


def pointer_get(obj, pointer):
    cur = obj
    for token in pointer.strip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        cur = cur[int(token)] if isinstance(cur, list) else cur[token]
    return cur


def verify(document, tests):
    if document["total_counts"] != {"P_positive":1378,"N_one_field_mutations":5981,"Q_precedence_probes":270,"logical_expected_count":7629,"total_planned_executions":15258}:
        raise ValueError("global counts differ from independent constants")
    report = []
    all_keys = set()
    byte_table={row["sha256"]:row["canonical_json"] for row in document["artifact_byte_table"]}
    for test in tests:
        tid = test["test_id"]
        p, n, q = COUNTS[tid]
        groups = (test["expected_branches"], test["negative_mutations"], test["precedence_probes"])
        if tuple(map(len, groups)) != (p, n, q):
            raise ValueError(f"{tid}: cardinality mismatch")
        local = {}
        expected_vector = []
        # Independent positive universe: project the separately frozen suite
        # applicability relations, rather than walking positive_cases.
        suite_keys=[]
        for suite in sorted(test["suite_applicability_tables"],key=lambda x:x["suite_ordinal"]):
            if suite["row_count"] != len(suite["rows"]):
                raise ValueError(f"{tid}: suite row count mismatch")
            if sha(canonical(suite["rows"])) != suite["ordered_rows_sha256"]:
                raise ValueError(f"{tid}: suite relation digest mismatch")
            for row in suite["rows"]:
                suite_keys.append(independent_key({"suite_id":suite["suite_id"],"axis_values":row["axis_values"]},tid,"P"))
        if suite_keys != [r["branch_key"] for r in test["expected_branches"]]:
            raise ValueError(f"{tid}: positive cases differ from applicability relations")
        mutation_relation=test["mutation_applicability_table"]
        if sha(canonical(mutation_relation)) != test["mutation_applicability_table_sha256"]:
            raise ValueError(f"{tid}: mutation applicability digest mismatch")
        if [r["mutation_id"] for r in mutation_relation] != [r["mutation_id"] for r in test["negative_mutations"]]:
            raise ValueError(f"{tid}: mutation rows differ from applicability relation")
        failure_order=test["first_failure_order"]
        expected_pairs=list(zip(failure_order,failure_order[1:]))
        actual_pairs=[tuple(r["faults"]) for r in test["precedence_probes"]]
        if actual_pairs != expected_pairs:
            raise ValueError(f"{tid}: precedence probes are not the adjacent closed order")
        for kind, rows in zip(("P", "N", "Q"), groups):
            for row in rows:
                keyrow=row
                if kind in ("P","Q"):
                    keyrow=row
                key = independent_key(keyrow, tid, kind)
                if row["branch_key"] != key or row["branch_key_sha256"] != sha(key):
                    raise ValueError(f"{tid}: key mismatch")
                if key in local or key in all_keys:
                    raise ValueError(f"{tid}: duplicate/cross-test key")
                local[key] = row
                all_keys.add(key)
                expected_vector.append({"branch_key":key,"expected_output_canonical_json":row.get("expected_output_canonical_json"),"expected_first_failure":row["expected_first_failure"]})
                if kind in ("P","Q"):
                    if row["input_sha256"] not in byte_table or sha(byte_table[row["input_sha256"]]) != row["input_sha256"]:
                        raise ValueError(f"{tid}: missing or corrupt positive/precedence input blob")
                if kind == "N":
                    before = json.loads(byte_table[row["before_input_sha256"]])
                    after = json.loads(byte_table[row["after_input_sha256"]])
                    diffs = changed_leaf_paths(before, after)
                    if set(diffs) != set(row["byte_changed_json_pointers"]):
                        raise ValueError(f"{tid}:{row['mutation_id']}: byte diffs differ from frozen target+rehash set: {diffs}")
                    if pointer_get(before,row["target_json_pointer"]) != row["before_typed_value"]["value"] or pointer_get(after,row["target_json_pointer"]) != row["after_typed_value"]["value"]:
                        raise ValueError(f"{tid}:{row['mutation_id']}: before/after mismatch")
                    if row["logical_changed_json_pointers"] != [row["target_json_pointer"]]:
                        raise ValueError(f"{tid}:{row['mutation_id']}: mutation is not one logical target")
        set_hash = sha(canonical(sorted(local)))
        vector_hash = sha(canonical(expected_vector))
        if set_hash != test["branch_key_set_sha256"] or vector_hash != test["ordered_expected_vector_sha256"]:
            raise ValueError(f"{tid}: set/vector digest mismatch")
        # Exact rational arithmetic makes dual-execution planning explicit.
        if Fraction(test["counts"]["total_planned_executions"], test["counts"]["logical_expected_count"]) != 2:
            raise ValueError(f"{tid}: not exactly two executors per logical case")
        report.append({"test_id":tid,"P":p,"N":n,"Q":q,"set_sha256":set_hash,"vector_sha256":vector_hash})
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("universe", type=Path)
    ns = ap.parse_args()
    document=json.loads(ns.universe.read_text())
    root=ns.universe.parent.parent
    tests=[json.loads((root/x["relative_path"]).read_text()) for x in document["fixture_spec_index"]]
    report = verify(document,tests)
    print(canonical(report), end="")


if __name__ == "__main__":
    main()
