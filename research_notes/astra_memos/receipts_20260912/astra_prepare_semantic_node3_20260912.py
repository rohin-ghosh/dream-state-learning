import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess

from organism_v6 import semantic_carrier_diagnostic as diagnostic


parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True, type=Path)
parser.add_argument("--config", required=True, type=Path)
args = parser.parse_args()
home = Path.home()
prior_path = home / "astra_diagnostics/astra_W0_interface_calibration_20260912_attempt1/manifest.json"
prior = json.loads(prior_path.read_text())["config"]
config = diagnostic.config_template()
for field in ("model", "model_path", "tokenizer_path", "model_revision", "tokenizer_revision",
              "model_sha256", "tokenizer_sha256", "environment", "node", "lease_end_unix"):
    config[field] = prior[field]
hardware = subprocess.run(
    ["nvidia-smi", "-i", "0", "--query-gpu=uuid,driver_version", "--format=csv,noheader,nounits"],
    capture_output=True, text=True, check=True, timeout=30,
)
gpu_uuid, driver = [part.strip() for part in hardware.stdout.strip().split(",")]
config.update(
    gpu_uuid=gpu_uuid,
    driver_version=driver,
    compiler_python=str(home / "cgym_test/venv/bin/python"),
    compiler_library_path=str(home / "cgym_test/lib"),
    protected_paths=[str(home / "v6_out")],
    approved_intake="Rohin 2026-09-12 standing authorization; simple-hygiene DEV surface diagnostic",
    builder_preflight_reference="ASTRA_SEMANTIC_CARRIER_COMPARISON_2026-09-12.md; exact prepared bytes reviewed before launch",
    requested_scope=diagnostic.config_template()["requested_scope"],
    lease_cutoff_unix=prior["lease_end_unix"] - 6 * 3600,
    deadline_unix=datetime.datetime(2026, 9, 12, 14, 0, tzinfo=datetime.timezone.utc).timestamp(),
)
diagnostic.validate_config(config)
with args.config.open("x") as stream:
    json.dump(config, stream, sort_keys=True, indent=2, allow_nan=False)
    stream.write("\n")
os.environ["CUDA_VISIBLE_DEVICES"] = ""
print(json.dumps(diagnostic.prepare(args.out, config), sort_keys=True))
