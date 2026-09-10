"""Proposal replay B: role-indexed relation-order traversal. No fixture I/O."""
from __future__ import annotations

import json
from typing import Callable


def reconstruct(artifacts: list[dict], role_to_relation: dict[str, str],
                reduce_value: Callable[[str, dict], dict]) -> str:
    indexed={artifact["role"]:artifact for artifact in artifacts}
    rows=[]
    ordered_roles=sorted(role_to_relation,key=lambda role:(role_to_relation[role],role))
    for role in ordered_roles:
        kind=role_to_relation[role]
        value=reduce_value(kind,json.loads(json.dumps(indexed[role]["payload"],
            sort_keys=True,separators=(",",":"),ensure_ascii=False)))
        rows.append({"relation_kind":kind,"primary_key":role,
                     "canonical_value_json":json.dumps(value,sort_keys=True,
                        separators=(",",":"),ensure_ascii=False)})
    return json.dumps(rows,sort_keys=True,separators=(",",":"),ensure_ascii=False)
