"""Collect only this operator's metadata receipts, never learner text/readouts."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[3]
CODE = '''import hashlib,json,re,time
from pathlib import Path
root=Path("/localhome/local-rohing/orch_r179_node1_20260917_attempt2/lanes")
names=("ARMED.json","NOOP_RECEIPT.json","RECEIVING_CPU.json","BOUNDARY.json", "BOUNDARY_RECEIVING_CPU.json",
       "RETIRED.json","DISPATCHED.json","LOADED_RECEIPT.json","HANDOFF_COMPLETE.json","NO_BOUNDARY.json")
rows=[]
for lane in range(2,8):
 directory=root/("lane"+str(lane))
 if lane==7: directory=Path("/localhome/local-rohing/orch_r179_node1_20260917_attempt1/lanes/lane7")
 result={"physical":lane,"attempt_root":str(directory),"receipts":{},"failures":[]}
 for name in names:
  path=directory/name
  if path.exists():
   assert not path.is_symlink() and path.stat().st_size<1048576
   raw=path.read_bytes()
   result["receipts"][name]={"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"document":json.loads(raw)}
 for path in directory.glob("FAILURE_*.json"):
  assert path.stat().st_size<1048576
  result["failures"].append(json.loads(path.read_bytes()))
 source_proof=directory/"SOURCE_PROOF.json"
 if source_proof.exists():
  assert source_proof.stat().st_size<4*1048576
  raw=source_proof.read_bytes(); proof=json.loads(raw); native="gpu/orch_r125_continual_native.py"
  result["source_proof"]={"path":str(source_proof),"sha256":hashlib.sha256(raw).hexdigest(),
    "original_native_sha256":proof["before"][native]["sha256"],
    "successor_native_sha256":proof["after"][native]["sha256"],"policy_sha256":proof["policy_sha256"],
    "original_source":proof["original_source"],"successor_source":proof["successor_source"],
    "original_files":len(proof["before"]),"successor_files":len(proof["after"]),
    "noncode_content_read":proof["noncode_content_read"]}
 admission=directory/"control/ADMISSION.json"
 if admission.exists():
  assert admission.stat().st_size<4*1048576
  raw=admission.read_bytes(); document=json.loads(raw)
  result["admission"]={"sha256":hashlib.sha256(raw).hexdigest(),"clear":document.get("clear"),
    "scanner_euid":document.get("scanner_euid"),"blocking_reasons":document.get("blocking_reasons"),
    "gpu_uuid":document.get("gpu",{}).get("uuid")}
 result["control_receipt_names"]=sorted(path.name for path in (directory/"control").glob("*.json"))
 readmission=directory/"readmission1"
 if readmission.exists():
  result["readmission"]={"path":str(readmission),"files":sorted(path.name for path in readmission.glob("*.json"))}
  for name in ("REQUEST.json","DISPATCHED.json","LOADED_RECEIPT.json","DENIED.json"):
   path=readmission/name
   if path.exists():
    assert path.stat().st_size<1048576
    raw=path.read_bytes()
    result["readmission"][name]={"sha256":hashlib.sha256(raw).hexdigest(),"document":json.loads(raw)}
  path=readmission/"ADMISSION.json"
  if path.exists():
   assert path.stat().st_size<4*1048576
   raw=path.read_bytes(); document=json.loads(raw)
   result["readmission"]["admission"]={"clear":document.get("clear"),"blocking_reasons":document.get("blocking_reasons"),
     "scanner_euid":document.get("scanner_euid"),"sha256":hashlib.sha256(raw).hexdigest()}
 armed=result["receipts"].get("ARMED.json",{}).get("document",{})
 if armed:
  process=Path("/proc")/str(armed["operator_pid"])/"stat"
  result["operator_state"]=process.read_text().rsplit(") ",1)[1].split()[0] if process.exists() else "ABSENT"
 log=directory/"OPERATOR.log"
 if log.exists():
  with log.open("rb") as stream:
   stream.seek(max(0,log.stat().st_size-4096)); tail=stream.read(4096).decode("utf-8","replace")
  result["operator_exception_lines"]=[line for line in tail.splitlines()
    if re.match(r"^(ValueError|RuntimeError|TimeoutError|FileNotFoundError|PermissionError|KeyError):",line)]
 rows.append(result)
print(json.dumps({"observed_unix":time.time(),"rows":rows,"sealed_content_reads":0}))
'''


def main():
    command = shlex.join(["env", "CUDA_VISIBLE_DEVICES=", "PYTHONDONTWRITEBYTECODE=1",
        "/localhome/local-rohing/v2/venv/bin/python", "-B", "-c", CODE])
    result = subprocess.run(["bash", "gpu/a100_ssh.sh", command], cwd=REPOSITORY,
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError("operator_metadata_collection_failed:" + result.stderr[-1000:])
    document = json.loads(result.stdout)
    path = HERE / ("EXECUTION_STATUS_" + str(time.time_ns()) + ".json")
    with path.open("x") as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), rows=[
        dict(physical=row["physical"], phases=list(row["receipts"]),
             operator_state=row.get("operator_state"), failures=row["failures"],
             exceptions=row.get("operator_exception_lines", []),
             readmission=({key: row["readmission"].get(key) for key in
                 ("path", "files", "admission", "LOADED_RECEIPT.json", "DENIED.json")}
                 if row.get("readmission") else None)) for row in document["rows"]])))


if __name__ == "__main__":
    main()
