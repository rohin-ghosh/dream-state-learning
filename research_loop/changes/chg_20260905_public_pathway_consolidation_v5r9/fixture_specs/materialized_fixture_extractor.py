#!/usr/bin/env python3
"""Extract a result vector without importing the expected enumerator.

The input format is one canonical FIXTURE_CASE_RESULT object per line. This
source is frozen proposal material; running fixtures remains forbidden until
ratification and the later authority gates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def extract(path):
    records = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        row = json.loads(line)
        required = {"test_id", "case_ordinal", "branch_key", "actual_output_canonical_json", "actual_first_failure"}
        if not required.issubset(row):
            raise ValueError(f"line {line_no}: missing required result field")
        records.append((row["test_id"], row["case_ordinal"], {
            "branch_key": row["branch_key"],
            "expected_output_canonical_json": row["actual_output_canonical_json"],
            "expected_first_failure": row["actual_first_failure"],
        }))
    if len({(a, b) for a, b, _ in records}) != len(records):
        raise ValueError("duplicate test/case ordinal")
    records.sort(key=lambda x: (x[0], x[1]))
    return [x[2] for x in records]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_jsonl", type=Path)
    ns = ap.parse_args()
    print(canonical(extract(ns.results_jsonl)), end="")


if __name__ == "__main__":
    main()
