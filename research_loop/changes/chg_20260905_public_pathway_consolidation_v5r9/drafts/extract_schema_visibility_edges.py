#!/usr/bin/env python3
"""Extract actual typed stage-ingress edges from the contract schema.

This code never reads the visibility registry/catalog constants.  It walks
the VISIBILITY_ACCESS_RECEIPT oneOf branches, whose source_ref is a concrete
typed artifact reference and whose projected bytes are the named stage input.
"""

import json
import sys
from pathlib import Path


schema = json.loads(Path(sys.argv[1]).read_text())
receipt = schema["$defs"]["visibility_access_receipt"]
rows = []
for branch in receipt["oneOf"]:
    props = branch["properties"]
    source_ref = props["source_ref"]
    row = {
        "information_item": props["information_item"]["const"],
        "information_ordinal": props["information_ordinal"]["const"],
        "consumer_stage": props["consumer_stage"]["const"],
        "stage_ordinal": props["stage_ordinal"]["const"],
        "visibility": props["visibility"]["const"],
        "rationale": props["rationale"]["const"],
        "source_type": props["source_type"]["const"],
        "source_field_path": props["source_field_path"]["const"],
        "projection_algorithm": props["projection_algorithm"]["const"],
        "output_type": props["output_type"]["const"],
        "output_field_path": props["output_field_path"]["const"],
        "concrete_role": props["concrete_role"]["const"],
        "ordinal": props["edge_ordinal"]["const"],
        "cardinality": props["cardinality"]["const"],
    }
    if source_ref.get("x-artifact-types") != [row["source_type"]]:
        raise SystemExit("typed source target mismatch")
    if source_ref.get("x-role") != row["concrete_role"]:
        raise SystemExit("typed source role mismatch")
    if row["output_type"] != "VISIBILITY_ACCESS_RECEIPT":
        raise SystemExit("visibility edge does not terminate at stage ingress")
    rows.append(row)
keys = set()
ordered = []
for row in rows:
    key = (row["information_ordinal"], row["stage_ordinal"])
    if key in keys:
        raise SystemExit("duplicate schema visibility edge")
    keys.add(key)
    ordered.append(row)
ordered.sort(key=lambda row: (row["information_ordinal"], row["stage_ordinal"]))
if len(ordered) != 84 or [r["ordinal"] for r in ordered] != list(range(84)):
    raise SystemExit("typed schema ingress edge closure failed")
print(json.dumps(ordered, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
