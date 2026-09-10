#!/usr/bin/env python3
"""Independent inventory-side visibility-edge extractor (proposal source only)."""

import json
import sys
from pathlib import Path


inventory = json.loads(Path(sys.argv[1]).read_text())
by_ordinal = {}
for artifact in inventory["objects"]:
    for edge in artifact["visibility_bindings"]:
        ordinal = edge["ordinal"]
        if ordinal in by_ordinal:
            raise SystemExit("duplicate inventory visibility edge")
        if edge["output_type"] != artifact["type"]:
            raise SystemExit("visibility edge stored under wrong output type")
        by_ordinal[ordinal] = edge
if sorted(by_ordinal) != list(range(len(by_ordinal))):
    raise SystemExit("noncontiguous inventory visibility ordinals")
print(json.dumps([by_ordinal[i] for i in sorted(by_ordinal)], ensure_ascii=False,
                 sort_keys=True, separators=(",", ":")))
