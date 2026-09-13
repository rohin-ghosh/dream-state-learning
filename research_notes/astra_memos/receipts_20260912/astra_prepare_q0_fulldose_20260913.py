"""Main-only node2 model receipt and three CPU-tokenizer preparations."""
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

SOURCE = Path("/localhome/local-rohing/astra_sources/q0_fulldose_20260913_attempt2")
sys.path.insert(0, str(SOURCE))
from gpu import astra_pairwise_q0_fulldose as executor
from organism_v6 import multikey_writer_gateway_simple as gateway

assert executor.file_hash(SOURCE / "gpu/astra_pairwise_q0_fulldose.py") == "f63c77f9c371433442a204d6bd7bb10e3769a3bb709ae1d728648d765ee8ceca"
reference = Path("/tmp/astra_qwen_public_binding_reference_20260913.json")
assert executor.file_hash(reference) == "e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019"
receipt = json.loads(reference.read_bytes())
model = Path("/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28").resolve(strict=True)
started = time.monotonic()
inventory = gateway.snapshot_inventory(model)
assert dict(inventory["files"]) == {name: value["sha256"] for name, value in receipt["files"].items()}
environment = gateway.environment_identity()
node = hashlib.sha256(platform.node().encode("utf-8")).hexdigest()
receipt.update(node=node, environment=environment, model=str(model), tokenizer=str(model),
               checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               elapsed_seconds=time.monotonic() - started,
               limitation="Node2 current file inventory matches official reference; no clean-lineage or historical certification.")
binding = Path("/tmp/astra_qwen_node2_binding_20260913_attempt1.json")
executor.write_once(binding.parent, binding.name, receipt)
binding_hash = executor.file_hash(binding)
gpu_output = subprocess.run(["nvidia-smi", "--query-gpu=index,uuid,driver_version", "--format=csv,noheader,nounits"],
                            check=True, capture_output=True, text=True, timeout=60).stdout
devices = {int(parts[0]): parts[1:] for line in gpu_output.splitlines()
           for parts in [[value.strip() for value in line.split(",")]]}
expected = ["GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0", "GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4",
            "GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05"]
lease_end = datetime.datetime(2026, 9, 21, 8, 43, tzinfo=datetime.timezone.utc).timestamp()
parent = Path("/localhome/local-rohing/astra_diagnostics")
parent.mkdir(exist_ok=True)
results = []
for index, replica in enumerate(("R0", "R1", "R2")):
    uuid, driver = devices[index]
    assert uuid == expected[index]
    config = executor.native_config_template(replica)
    config.update(model_path=str(model), tokenizer_path=str(model), public_binding_path=str(binding),
                  public_binding_sha256=binding_hash, environment=environment, node=node, gpu_uuid=uuid,
                  driver_version=driver, lease_end_unix=lease_end, lease_cutoff_unix=lease_end - 21600,
                  approved_intake="Rohin standing authorization 2026-09-12T05:45Z and messages30-32; Q0-FULLDOSE-v2",
                  builder_preflight_reference="research_loop/COORDINATION.md Builder 2026-09-13 full-dose native acceptance; 282 tests zero skips")
    config_path = Path(f"/tmp/astra_q0_fulldose_{replica}_20260913_attempt1.config.json")
    executor.write_once(config_path.parent, config_path.name, config)
    root = parent / f"q0_fulldose_{replica}_20260913_attempt1"
    manifest = executor.native_prepare(root, config, "/tmp/astra_q0_fulldose_native_cpu_20260913_attempt3.json")
    assert manifest["ready"] and manifest["campaign_sha256"] == "1f29967875bb7e84fd479c25a1a54aed59405675c9bccc74305be8449d7884df"
    result = dict(replica=replica, root=str(root), manifest_sha256=executor.file_hash(root / "manifest.json"),
                  prepared_sha256=executor.file_hash(root / "prepared.json"), config_sha256=executor.file_hash(config_path),
                  campaign_sha256=manifest["campaign_sha256"], binding_sha256=binding_hash, gpu_uuid=uuid)
    results.append(result)
    print(json.dumps(result, sort_keys=True), flush=True)
executor.write_once(Path("/tmp"), "astra_q0_fulldose_preparations_20260913_attempt1.json", results)
