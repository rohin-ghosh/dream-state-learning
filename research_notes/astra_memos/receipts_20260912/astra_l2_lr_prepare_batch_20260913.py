"""CPU-only six-root preparation with preserved per-root receipts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


roster_path = Path("/tmp/astra_l2_lr_specs_20260913_attempt1/roster.json")
assert hashlib.sha256(roster_path.read_bytes()).hexdigest() == "13ec2a14118adc4389ec86e8e858c2a4a535978cd3e99f2fb1a11d558e9cfbd3"
roster = json.loads(roster_path.read_text())
output = Path("/tmp/astra_l2_lr_prepared_20260913_attempt1")
output.mkdir()
prepared = []
for entry in roster["specs"]:
    command = [sys.executable, "-B", roster["source"] + "/gpu/astra_l2_public_record_dev.py", "prepare",
               "--spec", entry["spec_path"], "--spec-sha256", entry["spec_sha256"],
               "--root", entry["root"], "--allow-native"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180,
                            env=dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1"))
    for name, value in (("stdout", result.stdout), ("stderr", result.stderr)):
        with (output / (entry["name"] + "." + name)).open("x") as stream:
            stream.write(value)
    if result.returncode:
        raise RuntimeError(f"{entry['name']} preparation failed; original logs preserved")
    receipt = json.loads(result.stdout.strip().splitlines()[-1])
    assert receipt["root"] == entry["root"] and receipt["learner_seed"] == entry["learner_seed"]
    assert receipt["learning_rate"] == entry["learning_rate"]
    prepared.append(dict(entry, **receipt))
    print(json.dumps(prepared[-1], sort_keys=True), flush=True)
with (output / "prepared.json").open("x") as stream:
    stream.write(json.dumps(dict(source=roster["source"], prepared=prepared), sort_keys=True) + "\n")
