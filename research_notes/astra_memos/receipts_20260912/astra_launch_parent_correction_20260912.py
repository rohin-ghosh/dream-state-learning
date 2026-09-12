import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from gpu.astra_mini_sudoku_diagnostic import check_free
from organism_v6 import parent_correction_diagnostic as diagnostic

home = Path.home()
preparation = home / "astra_diagnostics/astra_P1_fresh_correction_preparation_20260912_attempt1"
root = home / "astra_diagnostics/astra_P1_fresh_correction_20260912_attempt1"
logs = root.with_name(root.name + "_logs")
prepared, preparation_hash, config = diagnostic.validate_preparation(preparation)
if root.exists() or logs.exists():
    raise ValueError("fresh run and sibling logs required")
now = datetime.datetime.now(datetime.timezone.utc)
deadline = datetime.datetime(2026, 9, 12, 14, 15, tzinfo=datetime.timezone.utc)
if (deadline - now).total_seconds() < 3700:
    raise ValueError("insufficient prospective time for the two bounded arms")
gpu, xml = check_free("3")
source = Path(diagnostic.__file__).resolve().parents[1]
command = [sys.executable, "-B", "-m", "organism_v6.parent_correction_diagnostic",
           "--preparation", str(prepared), "--out", str(root), "--allow-gpu"]
environment = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE="1",
    PYTHONNOUSERSITE="1", CUDA_VISIBLE_DEVICES="3", V6_MODEL=config["model_path"],
    HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
    OMP_NUM_THREADS="1")
logs.mkdir()
with (logs / "prelaunch_gpu.xml").open("x") as stream:
    stream.write(xml)
with (logs / "controller.log").open("xb") as output:
    process = subprocess.Popen(command, cwd=source, env=environment,
        stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
        start_new_session=True)
receipt = dict(status="LAUNCHED_NOT_COMPLETED", pid=process.pid, node=3, device="3",
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    root=str(root), logs=str(logs), source=str(source), command=command, gpu=gpu,
    preparation_sha256=preparation_hash, continuous_reservation=True,
    arm_timeout_seconds=1800, arms=2, training=False, clean_lineage=False,
    script_sha256=diagnostic.formation._hash(Path(__file__)))
with (logs / "launch.json").open("x") as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps(receipt, sort_keys=True))
