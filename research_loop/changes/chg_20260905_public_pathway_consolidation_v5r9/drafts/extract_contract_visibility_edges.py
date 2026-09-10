#!/usr/bin/env python3
"""Independent visibility-contract-side edge extractor (proposal source only)."""

import json
import sys
from pathlib import Path


contract = json.loads(Path(sys.argv[1]).read_text())
rows = []
for cell in contract["cells"]:
    if cell["visibility"] == "forbidden":
        if cell["allowed_capability_or_projection_role"] is not None:
            raise SystemExit("forbidden cell carries a role")
        continue
    rows.append({
        "information_item": cell["information_item"],
        "information_ordinal": cell["information_ordinal"],
        "consumer_stage": cell["consumer_stage"],
        "stage_ordinal": cell["stage_ordinal"],
        "visibility": cell["visibility"].upper(),
        "rationale": cell["rationale"],
        "source_type": cell["source_type"],
        "source_field_path": cell["source_field_path"],
        "projection_algorithm": cell["projection_algorithm"],
        "output_type": cell["output_type"],
        "output_field_path": cell["output_field_path"],
        "concrete_role": cell["allowed_capability_or_projection_role"],
        "ordinal": cell["edge_ordinal"],
        "cardinality": cell["cardinality"],
    })
rows.sort(key=lambda row: (row["information_ordinal"], row["stage_ordinal"]))
if len(rows) != 84 or [row["ordinal"] for row in rows] != list(range(84)):
    raise SystemExit("visibility contract edge closure failed")
print(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
