#!/usr/bin/env python3
"""Prove proposal reproduction is closed inside the PPC5r12 namespace.

This proposal-only validator performs a static forbidden-path scan, verifies
the local source manifest/context closure, then copies only this fixture_specs
tree to an isolated temporary root and reruns every author and validator there.
It does not materialize or execute a fixture.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE=Path(__file__).resolve().parent
ORIGINAL_REPO_ROOT=HERE.parents[3]
FORBIDDEN_PATH_TOKENS=(
    "chg_20260905_public_pathway_"+"consolidation_v5r9",
    "chg_20260906_public_pathway_"+"consolidation_v5r10",
    "chg_20260906_public_pathway_"+"consolidation_v5r11",
)


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(script_root:Path,name:str,instrument_root:Path)->bytes:
    env=guarded_environment(script_root,instrument_root)
    return subprocess.check_output([sys.executable,str(script_root/name)],
                                   cwd=script_root,env=env)


def guarded_environment(script_root:Path,instrument_root:Path)->dict[str,str]:
    env=dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"]="1"
    env["PYTHONPATH"]=str(instrument_root)
    env["PPC5R12_ALLOWED_ROOT"]=str(script_root.resolve())
    env["PPC5R12_DENIED_REPO_ROOT"]=str(ORIGINAL_REPO_ROOT.resolve())
    return env


def main():
    manifest=json.loads((HERE/"SOURCE_INPUT_MANIFEST_RFC.json").read_text())
    context=json.loads((HERE/"PROPOSAL_CONTEXT_RFC.json").read_text())
    context_by={row["file"]:row["sha256"] for row in context["context_files"]}
    assert len(context_by)==len(context["context_files"])
    assert context["context_file_count"]==len(context_by)
    # HANDOFF is downstream of this manifest and the manifest cannot contain
    # its own hash. Every other proposal/source byte is in the exact closure.
    expected_context={str(path.relative_to(HERE)) for path in HERE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and
        path.name not in {"HANDOFF.md","PROPOSAL_CONTEXT_RFC.json"}}
    assert set(context_by)==expected_context,(set(context_by)^expected_context)
    for name,value in context_by.items():
        assert sha(HERE/name)==value
    assert manifest["source_root"]=="source_inputs"
    assert manifest["source_file_count"]==len(manifest["files"])==19
    for row in manifest["files"]:
        path=HERE/row["file"]
        assert path.is_file() and sha(path)==row["raw_sha256"]
        assert context_by[row["file"]]==row["raw_sha256"]
    # Executable proposal sources may contain legacy architecture/test IDs, but
    # never a path to an older change namespace.
    scanned=[]
    for path in sorted(HERE.glob("*.py")):
        text=path.read_text();scanned.append(path.name)
        assert not any(token in text for token in FORBIDDEN_PATH_TOKENS),path.name
        compile(text,str(path),"exec")
    with tempfile.TemporaryDirectory(prefix="ppc5r12_isolated_") as temp:
        temp_root=Path(temp)
        isolated=temp_root/"fixture_specs"
        shutil.copytree(HERE,isolated,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
        # sitecustomize is inherited by child Python processes (including the
        # machine validator's reproduction subprocess).  Any attempted open
        # under the original repository outside the isolated copy is denied.
        # Thus a passing reproduction cannot silently resolve an older live
        # change namespace even if a path were assembled dynamically.
        instrument=temp_root/"instrument"
        instrument.mkdir()
        (instrument/"sitecustomize.py").write_text(
            "import os\n"
            "from pathlib import Path\n"
            "allowed=Path(os.environ['PPC5R12_ALLOWED_ROOT']).resolve()\n"
            "denied=Path(os.environ['PPC5R12_DENIED_REPO_ROOT']).resolve()\n"
            "def audit(event,args):\n"
            "    if event!='open' or not args or not isinstance(args[0],(str,bytes)): return\n"
            "    try: path=Path(os.fsdecode(args[0])).resolve()\n"
            "    except (OSError,ValueError): return\n"
            "    in_denied=(path==denied or denied in path.parents)\n"
            "    in_allowed=(path==allowed or allowed in path.parents)\n"
            "    if in_denied and not in_allowed:\n"
            "        raise PermissionError('nonlocal proposal read/write denied: '+str(path))\n"
            "import sys\n"
            "sys.addaudithook(audit)\n")
        # Prove the inherited guard is active before trusting the reproduction.
        probe=("from pathlib import Path; import os\n"
               "try: (Path(os.environ['PPC5R12_DENIED_REPO_ROOT'])/'README.md').read_bytes()\n"
               "except PermissionError: print('DENIED')\n"
               "else: raise SystemExit('open guard inactive')\n")
        guarded=subprocess.check_output([sys.executable,"-c",probe],cwd=isolated,
            env=guarded_environment(isolated,instrument))
        assert guarded==b"DENIED\n"
        context_bytes=run(isolated,"author_context_rfc.py",instrument)
        assert context_bytes==(isolated/"PROPOSAL_CONTEXT_RFC.json").read_bytes()
        vector=json.loads(run(isolated,"author_vector_fixture_specs.py",instrument))
        assert (vector["P"],vector["N"],vector["Q"],vector["logical"],
                vector["planned_executions"])==(465,2467,55,2987,5974)
        authored=run(isolated,"author_machine_rfc.py",instrument)
        assert authored==(isolated/"REDUCER_MACHINE_RFC.json").read_bytes()
        results=[]
        for name in ("validate_reducer_semantics.py","validate_machine_rfc.py",
                     "validate_quarantine.py"):
            result=json.loads(run(isolated,name,instrument));assert result["status"]=="PASS"
            results.append(name)
    print(json.dumps({"status":"PASS","local_source_file_count":19,
        "context_file_count":len(context_by),"static_python_file_count":len(scanned),
        "isolated_author_count":3,"isolated_validator_count":len(results),
        "original_repository_open_guard":"ACTIVE_AND_PROBED"},
        sort_keys=True,separators=(",",":")))


if __name__=="__main__":main()
