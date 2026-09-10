"""Proposal replay A: predecessor-order traversal. No fixture I/O."""
from __future__ import annotations

import json
from typing import Callable


def reconstruct(artifacts: list[dict], role_to_relation: dict[str, str],
                reduce_value: Callable[[str, dict], dict]) -> str:
    rows=[]
    for artifact in artifacts:
        kind=role_to_relation.get(artifact["role"])
        if kind is not None:
            value=reduce_value(kind,artifact["payload"])
            rows.append({"relation_kind":kind,"primary_key":artifact["role"],
                         "canonical_value_json":json.dumps(value,sort_keys=True,
                            separators=(",",":"),ensure_ascii=False)})
    rows.sort(key=lambda row:(row["relation_kind"],row["primary_key"]))
    return json.dumps(rows,sort_keys=True,separators=(",",":"),ensure_ascii=False)
