#!/usr/bin/env python3
"""Print the exact local PPC5r12 proposal context; never writes fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXCLUDED = {"HANDOFF.md", "PROPOSAL_CONTEXT_RFC.json"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    paths = sorted(
        path for path in HERE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
        and path.name not in EXCLUDED
    )
    rows = [
        {"file": str(path.relative_to(HERE)), "sha256": sha(path)}
        for path in paths
    ]
    result = {
        "document_kind": "PPC5R12_PROPOSAL_CONTEXT_RFC",
        "lifecycle_state": "PROPOSAL_ONLY",
        "authority_conferred": False,
        "materialization_permitted": False,
        "namespace": (
            "research_loop/changes/"
            "chg_20260906_public_pathway_consolidation_v5r12/fixture_specs"
        ),
        "context_file_count": len(rows),
        "context_files": rows,
        "excluded_from_self_hash_closure": [
            {
                "file": "PROPOSAL_CONTEXT_RFC.json",
                "reason": "a byte string cannot contain its own SHA-256 fixed point",
            },
            {
                "file": "HANDOFF.md",
                "reason": "downstream human-readable handoff binds the completed context hash",
            },
        ],
        "local_reproduction_rule": (
            "Every proposal/source file except the context manifest itself and its "
            "downstream handoff is hash-bound here. Isolated reproduction is valid "
            "only when validate_local_closure.py passes with its original-repository "
            "open guard active."
        ),
        "excluded_legacy_bytes_ref": "QUARANTINE_RFC.json#/excluded_bytes",
        "no_authority_notice": (
            "This closes proposal source ancestry only. It creates no fixture "
            "universe, execution, conformance evidence, ratification, model or GPU "
            "authority, or release authority."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
