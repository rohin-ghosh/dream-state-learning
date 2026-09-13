"""Main's sequential one-shot launches for six predeclared matched roots."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


prepared_path = Path("/tmp/astra_l2_lr_prepared_20260913_attempt1/prepared.json")
assert hashlib.sha256(prepared_path.read_bytes()).hexdigest() == "2cf367e16116d205eb1e938d05d786d99309d4ae4df4d7afed66863d9d1f865b"
prepared = json.loads(prepared_path.read_text())
output = Path("/tmp/astra_l2_lr_launched_20260913_attempt1")
output.mkdir()
for entry in prepared["prepared"]:
    command = [sys.executable, "-B", "/tmp/astra_launch_l2_comparison_20260913.py",
               "--root", entry["root"], "--driver", prepared["source"] + "/gpu/astra_l2_public_record_dev.py",
               "--driver-sha256", "dce8cd88b82bd51ec4f12e482ce70dc220453cb85dcaeb758206c7b5200a4277",
               "--plan-sha256", entry["plan_sha256"], "--precheck", "/tmp/astra_node3_targeted_prelaunch_20260913.py",
               "--precheck-sha256", "32d366afc432d9e8dcf0c188cbf0725cdadfcc68a1a0f8e0b11532ca7629862a",
               "--stdout", f"/tmp/astra_l2_lr_{entry['name']}_20260913_attempt1.controller.log",
               "--gpu-index", str(entry["gpu_index"]), "--gpu-uuid", entry["gpu_uuid"], "--allow-gpu"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180,
                            env=dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1"))
    for name, value in (("stdout", result.stdout), ("stderr", result.stderr)):
        with (output / (entry["name"] + "." + name)).open("x") as stream:
            stream.write(value)
    if result.returncode:
        raise RuntimeError(f"{entry['name']} launcher failed; inspect preserved claims before retry")
    receipt = json.loads(result.stdout.strip().splitlines()[-1])
    assert receipt["status"] == "LAUNCHED_NOT_SCIENTIFIC_RESULT" and receipt["root"] == entry["root"]
    print(json.dumps(dict(name=entry["name"], receipt=receipt), sort_keys=True), flush=True)
