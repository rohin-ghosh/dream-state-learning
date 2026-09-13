"""One read-only targeted NVML sample; no workload or process mutation."""
import json
import subprocess
import time
import xml.etree.ElementTree as ET


started = time.monotonic()
result = dict(gpu_index=1, expected_uuid="GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821",
              started_unix=time.time(), query="nvidia-smi -i 1 -q -x", timeout_seconds=30)
try:
    completed = subprocess.run(["nvidia-smi", "-i", "1", "-q", "-x"], capture_output=True,
                               text=True, timeout=30, check=True)
    devices = ET.fromstring(completed.stdout).findall("gpu")
    result["identity_matches"] = len(devices) == 1 and devices[0].findtext("uuid") == result["expected_uuid"]
    processes = devices[0].find("processes") if len(devices) == 1 else None
    result["original_free_predicate"] = processes is not None and not (processes.text or "").strip() and not list(processes)
    result["status"] = "QUERY_COMPLETE"
except Exception as error:
    result.update(status="QUERY_FAILED", error_type=type(error).__name__, error=str(error))
result["elapsed_seconds"] = time.monotonic() - started
print(json.dumps(result, sort_keys=True), flush=True)
