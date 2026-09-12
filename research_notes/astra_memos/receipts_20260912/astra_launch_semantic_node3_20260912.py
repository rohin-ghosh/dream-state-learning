import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from gpu.astra_mini_sudoku_diagnostic import check_free
from organism_v6 import semantic_carrier_diagnostic as diagnostic


parser = argparse.ArgumentParser()
parser.add_argument("--run", required=True, type=Path)
parser.add_argument("--logs", required=True, type=Path)
args = parser.parse_args()
root = args.run.resolve(strict=True)
logs = args.logs.absolute()
spec, requests, tokenizer = diagnostic.validate(root)
if logs.exists() or logs.is_relative_to(root) or root.is_relative_to(logs):
    raise ValueError("fresh sibling logs required")
if (root / "STARTED.json").exists() or (root / "FAILED.json").exists():
    raise ValueError("run already attempted")
gpu, xml = check_free("0")
if gpu["gpu_uuid"] != spec["config"]["gpu_uuid"]:
    raise ValueError("selected GPU differs from preparation")
logs.mkdir()
with (logs / "prelaunch_gpu.xml").open("x") as stream:
    stream.write(xml)
source = Path(diagnostic.__file__).resolve().parents[1]
command = [sys.executable, "-B", "-m", "organism_v6.semantic_carrier_diagnostic",
           "execute", "--run", str(root), "--allow-gpu"]
environment = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE="1",
    PYTHONNOUSERSITE="1", CUDA_VISIBLE_DEVICES=gpu["gpu_uuid"], OMP_NUM_THREADS="1",
    HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
with (logs / "controller.log").open("xb") as output:
    process = subprocess.Popen(command, cwd=source, env=environment,
        stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(status="LAUNCHED_NOT_COMPLETED", pid=process.pid, node=3, device="0",
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    run=str(root), logs=str(logs), source=str(source), command=command, gpu=gpu,
    manifest_sha256=diagnostic.w0.file_hash(root / "manifest.json"), continuous_reservation=True,
    max_seconds=diagnostic.MAX_SECONDS, deadline_unix=spec["config"]["deadline_unix"],
    training=False, clean_lineage=False)
with (logs / "launch.json").open("x") as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps(receipt, sort_keys=True))
