#!/usr/bin/env python3
"""Prove that superseded PPC5r9 fixture bytes are excluded from v5r10."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]


def main():
    quarantine=json.loads((HERE/"QUARANTINE_RFC.json").read_text())
    vector=json.loads((HERE/"VECTOR_FIXTURE_RFC.json").read_text())
    context=json.loads((HERE/"PROPOSAL_CONTEXT_RFC.json").read_text())
    old=REPO/quarantine["superseded_namespace"]
    excluded=set()
    for row in quarantine["excluded_bytes"]:
        path=old/row["file"];assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row["sha256"]
        excluded.add(row["file"])
    assert vector["exact_counts"]["logical_expected_count"]==2987
    assert quarantine["replacement_scope"]["logical_case_count"]==2987
    assert quarantine["replacement_scope"]["materialized_universe"] is None
    assert quarantine["replacement_scope"]["materialization_permitted"] is False
    assert context["lifecycle_state"]=="PROPOSAL_ONLY"
    assert context["authority_conferred"] is False and context["materialization_permitted"] is False
    context_names=[]
    for row in context["context_files"]:
        context_names.append(row["file"])
        assert hashlib.sha256((HERE/row["file"]).read_bytes()).hexdigest()==row["sha256"]
    assert len(context_names)==len(set(context_names))
    assert not (excluded & set(context_names))
    # Only the quarantine declaration, its validator, and explanatory README may
    # name old files. No executable/spec source may consume them.
    allowed={"QUARANTINE_RFC.json","validate_quarantine.py","README.md",
             "VECTOR_FIXTURE_RFC.json"}
    for path in HERE.iterdir():
        if not path.is_file() or path.name in allowed:continue
        text=path.read_text(errors="ignore")
        assert not any(name in text for name in excluded),(path.name,excluded)
    print(json.dumps({"status":"PASS","excluded_file_count":len(excluded),
        "proposal_context_file_count":len(context_names),
        "replacement_logical_count":2987,"old_universe_sha256":quarantine["excluded_bytes"][0]["sha256"]},sort_keys=True,separators=(",",":")))


if __name__=="__main__":main()
