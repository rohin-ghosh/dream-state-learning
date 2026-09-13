import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ORIGINAL_PLANS = (
    "a5542d56e652fc2d9558d76c0b24d1d4c79abbdfad3bb5a629bd0e76e1fbe20f",
    "a60ecb13f1816563f27c3652aff17985bab2a942ae1ce02b3c5baefe2d9dfbae",
    "d5cdbefb5021b8c1b2b5698abbf4f3c208b7817e94d34cf422b9820551b26c1c",
)
ORIGINAL_COMPLETIONS = (
    "5dd90ec1198bcbd8b41da330c1f4a852781959830f79d637b9e7b0a460d783f2",
    "63e851fa4346e850b0f55fef74bfc7a1297862428f372db282ec7a17f200d251",
    "a56d9764332d03cdb839f40512f2bfd68986804d17833d1b3d1020b35282616b",
)
GPUS = (
    "GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d",
    "GPU-4b071167-a06a-773c-f947-60cb8c2f7512",
    "GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8",
)


def pin(path):
    path = Path(path).absolute()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def prepare(source, directory):
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    sys.path.insert(0, str(source))
    api = importlib.import_module("gpu.astra_level1_prediction_transfer_readout")
    lifecycle = api.lifecycle
    assert lifecycle.boot_id() == "fc5d7cca-b343-4040-9930-bbd387632f71"
    assert os.getuid() == 2524
    assert sys.executable == "/localhome/local-rohing/v2/venv/bin/python"
    directory.mkdir(exist_ok=False)
    exceptions = []
    for role, process_id, expected_hash in (
        ("user_manager", 2210434, "3127082f907652bfa48e38fddcaf16c3e73b2da5a2d64602eafe88869c222925"),
        ("pam_helper", 2210439, "971490059d839d27af3ded30a476216b92689d837b0236a700723fb13640e370"),
    ):
        process = Path("/proc") / str(process_id)
        checksum = pin(process / "cmdline")["sha256"]
        if expected_hash:
            assert checksum == expected_hash
        fields = (process / "stat").read_text().rsplit(")", 1)[1].split()
        exceptions.append({"role": role, "identity": lifecycle.identity(process_id),
            "ppid": int(fields[1]), "comm": (process / "comm").read_text().strip(),
            "cmdline_sha256": checksum, "cgroup": (process / "cgroup").read_text()})
    runner = source / "gpu/astra_level1_prediction_transfer_readout.py"
    runtime = pin("/tmp/astra_level1_skill_run_20260913.py")
    assert runtime["sha256"] == "6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e"
    entries = []
    for seed in range(3):
        original = Path(f"/localhome/local-rohing/astra_diagnostics/level1_prediction_seed{seed}_20260913_attempt1")
        original_plan, original_completion = pin(original / "plan.json"), pin(original / "capture_complete.json")
        assert original_plan["sha256"] == ORIGINAL_PLANS[seed]
        assert original_completion["sha256"] == ORIGINAL_COMPLETIONS[seed]
        allocation = {"schema": lifecycle.SCHEMA + "/allocation", "gpu_index": seed, "gpu_uuid": GPUS[seed],
            "boot_id": lifecycle.boot_id(), "uid": os.getuid(), "python": sys.executable,
            "queue_dir": "/localhome/local-rohing/queue", "queue_mode": "direct",
            "queue_allowlist": {"pending": {}, "running": {}}, "coordination_owners": [],
            "lease_end": 1789427640, "lease_margin_seconds": 21600,
            "outer_sha256": pin(runner)["sha256"], "service_exceptions": exceptions}
        lifecycle.validate_allocation(allocation)
        allocation_path = directory / f"allocation_seed{seed}.json"
        lifecycle.write(allocation_path, allocation)
        specification = {"schema": api.SCHEMA + "/spec", "self_sha256": pin(runner)["sha256"],
            "source_files": api.source_files(), "runtime": runtime,
            "original_plan": original_plan, "original_completion": original_completion,
            "original_collection": pin(str(original) + "_collected/collection.json"),
            "learner_seed": seed, "allocation": pin(allocation_path),
            "material": pin(source / "organism_v6/level1_prediction_transfer.py"),
            "protocol": pin(source / "research_notes/analysis/2026-09-13_level1_prediction_transfer_protocol.md"),
            "shutdown_binding": pin("/localhome/local-rohing/v2/venv/lib/python3.12/site-packages/vllm/v1/engine/core_client.py")}
        spec_path = directory / f"spec_seed{seed}.json"
        lifecycle.write(spec_path, specification)
        root = Path(f"/localhome/local-rohing/astra_diagnostics/prediction_transfer_seed{seed}_20260913_attempt1")
        started = time.time()
        result = api.prepare(str(root), str(spec_path), pin(spec_path)["sha256"], allow_native=True)
        entry = {"seed": seed, "root": str(root), "spec": pin(spec_path), "plan_sha256": result["plan_sha256"],
            "prepared_at": time.time(), "prepare_elapsed_seconds": time.time() - started,
            "allocation": pin(allocation_path), "source": str(source), "runner": pin(runner)}
        lifecycle.write(directory / f"prepared_seed{seed}.json", entry)
        entries.append(entry)
        print(json.dumps(entry), flush=True)
    lifecycle.write(directory / "roster.json", {"entries": entries, "setup": pin(__file__), "fits": 0, "calls": 288})


def launch(source, directory):
    sys.path.insert(0, str(source))
    api = importlib.import_module("gpu.astra_level1_prediction_transfer_readout")
    roster = json.loads((directory / "roster.json").read_text())
    launched = directory / "launch"
    launched.mkdir(exist_ok=False)
    api.write(launched / "batch_started.json", {"identity": api.lifecycle.identity(os.getpid()), "at": time.time(),
        "roster": pin(directory / "roster.json"), "setup": pin(__file__)})
    time.sleep(8)
    processes = []
    for entry in roster["entries"]:
        assert pin(entry["runner"]["path"]) == entry["runner"]
        command = [sys.executable, "-B", entry["runner"]["path"], "controller", "--root", entry["root"],
            "--plan-sha256", entry["plan_sha256"], "--allow-gpu"]
        with (launched / f"seed{entry['seed']}.stdout.log").open("xb") as stdout, (launched / f"seed{entry['seed']}.stderr.log").open("xb") as stderr:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                start_new_session=True, env={**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(source), "PYTHONDONTWRITEBYTECODE": "1"})
        api.write(launched / f"seed{entry['seed']}.json", {"identity": api.lifecycle.identity(process.pid), "argv": command,
            "root": entry["root"], "plan_sha256": entry["plan_sha256"], "at": time.time()})
        processes.append((entry, process))
    for entry, process in processes:
        returncode = process.wait(timeout=api.TOTAL_SECONDS + 120)
        result = {"seed": entry["seed"], "root": entry["root"], "returncode": returncode, "at": time.time()}
        if returncode == 0:
            completed = pin(Path(entry["root"]) / "capture_complete.json")
            try:
                result["collection"] = api.collect(entry["root"], entry["plan_sha256"], completed["sha256"], entry["root"] + "_collected")
            except Exception as error:
                result["collection_error"] = {"type": type(error).__name__, "message": str(error)}
        api.write(launched / f"seed{entry['seed']}.terminal.json", result)
    api.write(launched / "batch_complete.json", {"at": time.time(), "seeds": [entry["seed"] for entry in roster["entries"]]})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "launch"))
    parser.add_argument("source", type=Path)
    parser.add_argument("directory", type=Path)
    arguments = parser.parse_args()
    globals()[arguments.mode](arguments.source, arguments.directory)
