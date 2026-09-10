#!/usr/bin/env python3
"""Materialize the PPC5r9 visibility contract from typed ingress branches.

Proposal-authoring only: this performs no fixture, model, training, behavioral,
GPU, claim, or release work.  The schema catalog and the 13x15 matrix are
independently checked for exact cell identity before any bytes are replaced.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts.schema.json"
CONTRACT = ROOT / "visibility_contract.json"


def render() -> bytes:
    source = json.loads(CONTRACT.read_text())
    schema = json.loads(SCHEMA.read_text())
    catalog = []
    for branch in schema["$defs"]["visibility_access_receipt"]["oneOf"]:
        p = branch["properties"]
        source_ref = p["source_ref"]
        edge = {
            "information_item": p["information_item"]["const"],
            "information_ordinal": p["information_ordinal"]["const"],
            "consumer_stage": p["consumer_stage"]["const"],
            "stage_ordinal": p["stage_ordinal"]["const"],
            "visibility": p["visibility"]["const"],
            "rationale": p["rationale"]["const"],
            "source_type": p["source_type"]["const"],
            "source_field_path": p["source_field_path"]["const"],
            "projection_algorithm": p["projection_algorithm"]["const"],
            "output_type": p["output_type"]["const"],
            "output_field_path": p["output_field_path"]["const"],
            "concrete_role": p["concrete_role"]["const"],
            "ordinal": p["edge_ordinal"]["const"],
            "cardinality": p["cardinality"]["const"],
        }
        if source_ref.get("x-artifact-types") != [edge["source_type"]]:
            raise SystemExit("typed visibility source mismatch")
        if source_ref.get("x-role") != edge["concrete_role"]:
            raise SystemExit("typed visibility role mismatch")
        catalog.append(edge)
    catalog.sort(key=lambda edge: edge["ordinal"])
    if catalog != schema["x-visibility-edge-catalog"]:
        raise SystemExit("schema convenience catalog differs from typed ingress branches")
    by_key = {(row["information_item"], row["consumer_stage"]): row for row in catalog}

    expected_keys = {
        (information_item, stage)
        for information_item in source["information_items"]
        for stage in source["stages"]
        if not source["matrix"][information_item][stage].startswith("forbidden")
    }
    if set(by_key) != expected_keys:
        raise SystemExit("schema catalog and nonforbidden visibility cells differ")

    result = copy.deepcopy(source)
    result["allowed_edges"] = catalog
    cells = []
    for information_ordinal, information_item in enumerate(source["information_items"]):
        for stage_ordinal, stage in enumerate(source["stages"]):
            encoded = source["matrix"][information_item][stage]
            visibility, separator, rationale = encoded.partition(":")
            visibility = visibility.strip()
            rationale = rationale.strip() if separator else "No dependency or influence is permitted."
            edge = by_key.get((information_item, stage))
            if edge is None:
                cell = {
                    "information_item": information_item,
                    "stage": stage,
                    "visibility": visibility,
                    "rationale": rationale,
                    "allowed_capability_or_projection_role": None,
                }
            else:
                if edge["information_ordinal"] != information_ordinal or edge["stage_ordinal"] != stage_ordinal:
                    raise SystemExit("schema catalog ordinal mismatch")
                cell = {
                    "information_item": information_item,
                    "stage": stage,
                    "visibility": visibility,
                    "rationale": edge["rationale"],
                    "allowed_capability_or_projection_role": edge["concrete_role"],
                    "source_type": edge["source_type"],
                    "source_field_path": edge["source_field_path"],
                    "projection_algorithm": edge["projection_algorithm"],
                    "output_type": edge["output_type"],
                    "output_field_path": edge["output_field_path"],
                    "consumer_stage": edge["consumer_stage"],
                    "information_ordinal": edge["information_ordinal"],
                    "stage_ordinal": edge["stage_ordinal"],
                    "edge_ordinal": edge["ordinal"],
                    "cardinality": edge["cardinality"],
                }
            cells.append(cell)
    if len(cells) != 195 or len(catalog) != 84:
        raise SystemExit("visibility cardinality mismatch")
    result["cells"] = cells
    return (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if CONTRACT.read_bytes() != expected:
            raise SystemExit("visibility_contract.json is stale")
        print("verified 195 visibility cells and 84 concrete allowed edges")
        return
    CONTRACT.write_bytes(expected)
    print("wrote visibility_contract.json")


if __name__ == "__main__":
    main()
