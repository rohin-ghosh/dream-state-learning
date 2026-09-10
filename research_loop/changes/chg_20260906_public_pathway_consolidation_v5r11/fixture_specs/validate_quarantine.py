#!/usr/bin/env python3
"""Enforce PPC5r11 quarantine by byte identity, recursively.

This is a proposal-source validator. Basenames and directory positions are
irrelevant: a renamed or nested copy of any excluded byte is rejected.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path


HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recursive_byte_hits(root:Path, excluded_hashes:set[str])->list[tuple[str,str]]:
    hits=[]
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            value=sha(path)
            if value in excluded_hashes:
                hits.append((str(path.relative_to(root)),value))
    return hits


def embedded_excluded_hashes(value, excluded_hashes:set[str], pointer=""):
    hits=[]
    if isinstance(value,dict):
        for key,child in value.items():
            child_pointer=pointer+"/"+key.replace("~","~0").replace("/","~1")
            if (key.lower().endswith("sha256") and isinstance(child,str)
                    and child in excluded_hashes):
                hits.append((child_pointer,child))
            hits.extend(embedded_excluded_hashes(child,excluded_hashes,child_pointer))
    elif isinstance(value,list):
        for index,child in enumerate(value):
            hits.extend(embedded_excluded_hashes(child,excluded_hashes,
                                                  pointer+f"/{index}"))
    return hits


def main():
    quarantine=json.loads((HERE/"QUARANTINE_RFC.json").read_text())
    vector=json.loads((HERE/"VECTOR_FIXTURE_RFC.json").read_text())
    context=json.loads((HERE/"PROPOSAL_CONTEXT_RFC.json").read_text())
    old=REPO/quarantine["superseded_namespace"]
    excluded_hashes=set()
    excluded_bytes=[]
    for row in quarantine["excluded_bytes"]:
        path=old/row["file"]
        assert path.is_file() and sha(path)==row["sha256"]
        excluded_hashes.add(row["sha256"]);excluded_bytes.append(path.read_bytes())
    assert len(excluded_hashes)==len(quarantine["excluded_bytes"])==4
    assert vector["exact_counts"]["logical_expected_count"]==2987
    assert quarantine["replacement_scope"]["logical_case_count"]==2987
    assert quarantine["replacement_scope"]["materialized_universe"] is None
    assert quarantine["replacement_scope"]["materialization_permitted"] is False
    assert context["lifecycle_state"]=="PROPOSAL_ONLY"
    assert context["authority_conferred"] is False and context["materialization_permitted"] is False
    context_names=[]
    for row in context["context_files"]:
        context_names.append(row["file"])
        path=(HERE/row["file"]).resolve()
        assert HERE.resolve() in path.parents and path.is_file()
        assert sha(path)==row["sha256"] and row["sha256"] not in excluded_hashes
    assert len(context_names)==len(set(context_names))
    assert not recursive_byte_hits(HERE,excluded_hashes)
    # Source/identity manifests cannot smuggle an excluded artifact by hash.
    embedded=[]
    for path in sorted(HERE.rglob("*.json")):
        if path.name=="QUARANTINE_RFC.json":
            continue
        for pointer,value in embedded_excluded_hashes(json.loads(path.read_text()),
                                                       excluded_hashes):
            embedded.append((str(path.relative_to(HERE)),pointer,value))
    assert not embedded,embedded
    # Adversarial proof: both a rename and a nested rename are detected solely
    # from bytes. Temporary files live outside the proposal namespace.
    with tempfile.TemporaryDirectory(prefix="ppc5r11_quarantine_") as temp:
        temp_root=Path(temp)
        renamed=temp_root/"innocent_name.bin";renamed.write_bytes(excluded_bytes[0])
        nested=temp_root/"a"/"b"/"unrelated.json";nested.parent.mkdir(parents=True)
        nested.write_bytes(excluded_bytes[-1])
        hits=recursive_byte_hits(temp_root,excluded_hashes)
        assert {name for name,_ in hits}=={"innocent_name.bin","a/b/unrelated.json"}
    print(json.dumps({"status":"PASS","excluded_file_count":len(excluded_hashes),
        "proposal_context_file_count":len(context_names),
        "replacement_logical_count":2987,
        "recursive_rename_probe_count":2},sort_keys=True,separators=(",",":")))


if __name__=="__main__":main()
