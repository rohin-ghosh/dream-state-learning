"""Check or dispatch one bound job through the original transient cgroup route."""

import argparse
import fcntl
import json
import math
from pathlib import Path
import subprocess
import time

import probe_runtime as runtime


def commands(config, config_path, config_sha, launch_path, launch_sha, deadline, now):
    remaining = math.floor(deadline - now)
    runtime.require(60 < remaining <= 2400 and deadline <= runtime.HARD_END, "bounded_dispatch_window")
    result = []
    for role in ("judge", "player"):
        device = config["role_devices"][role]
        root = Path(config["root"])
        unit = "orch-reboot-probe-" + config["job_id"][:16] + "-" + role
        argv = ["sudo", "-n", "systemd-run", "--unit=" + unit,
            "--property=User=" + str(config["expected_uid"]), "--property=Group=" + str(config["expected_uid"]),
            "--property=WorkingDirectory=" + str(root / "source"),
            "--property=RuntimeMaxSec=" + str(remaining), "--property=TimeoutStopSec=15",
            "--property=KillMode=control-group", "--property=UMask=0077", "--property=DevicePolicy=closed",
            "--property=NoNewPrivileges=yes", "--property=StandardOutput=append:" + str(root / "runtime" / (role + ".log")),
            "--property=StandardError=append:" + str(root / "runtime" / (role + ".log"))]
        for device_path in ("/dev/nvidia" + str(device["physical"]), "/dev/nvidiactl", "/dev/nvidia-uvm", "/dev/nvidia-uvm-tools"):
            argv.append("--property=DeviceAllow=" + device_path + " rw")
        environment = dict(CUDA_VISIBLE_DEVICES=device["uuid"], HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
            PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(root / "source"), OMP_NUM_THREADS="2", MKL_NUM_THREADS="2",
            TOKENIZERS_PARALLELISM="false", HOME="/localhome/local-rohing")
        argv.extend("--setenv=" + name + "=" + value for name, value in environment.items())
        argv.extend(["/localhome/local-rohing/v2/venv/bin/python", "-B", str(root / "runtime/probe_runtime.py"),
            "--config", str(config_path), "--config-sha256", config_sha, "--launch", str(launch_path),
            "--launch-sha256", launch_sha, "--mode", role])
        result.append(dict(role=role, unit=unit, argv=argv))
    return result


def submit(command, runner=subprocess.run):
    completed = runner(command, check=False, capture_output=True, text=True, timeout=25)
    if completed.returncode:
        raise RuntimeError("PLATFORM_OR_LAUNCH_FAILURE_TERMINAL_NO_FALLBACK")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--deadline", type=float, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--launch", action="store_true")
    arguments = parser.parse_args()
    config = runtime.load_config(arguments.config, arguments.config_sha256)
    runtime.verify_protected(config)
    root = runtime.verify_bundle(config)
    runtime.wait_for_live_source(config)
    runtime.verify_no_attempt(root, config)
    inventory = runtime.gpu_inventory()
    runtime.validate_admission(config, inventory)
    if arguments.check:
        now = time.time()
        print(json.dumps(dict(status="CPU_SOURCE_ELIGIBLE_DEVICES_FREE_AT_CHECK_NOT_RESERVED_NOT_LAUNCHED",
            unix=now, job_id=config["job_id"], inventory=inventory, role_devices=config["role_devices"],
            source_identity=config["source_identity"], additional_human_ratification_required=False,
            proposed_commands=commands(config, arguments.config, arguments.config_sha256,
                root / "runtime/LAUNCH.json", "CREATED_AT_ACTUAL_ADMISSION", min(arguments.deadline, now + 2400, runtime.HARD_END), now),
            platform_permission_not_probed=True, confinement_enforced_by_cgroup_and_runtime_before_model_load=True,
            gpu_execution_performed=False, automatic_queue_execution_enabled=False)))
        return 0
    locks = Path(config["claims_namespace"])
    locks.mkdir(mode=0o700, exist_ok=True)
    with (locks / "DISPATCH.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        runtime.verify_no_attempt(root, config)
        runtime.verify_protected(config)
        runtime.verify_bundle(config)
        runtime.verify_live_source(config)
        runtime.validate_admission(config, runtime.gpu_inventory())
        now = time.time()
        deadline = min(arguments.deadline, now + 2400, runtime.HARD_END)
        runtime.require(deadline - now > 60, "lease_window_elapsed_during_preflight")
        for device in config["role_devices"].values():
            claim_path = locks / (device["uuid"] + ".json")
            if claim_path.exists():
                claim = runtime.read(claim_path)
                runtime.require(now > claim["hold_until_unix"], "existing_lane_claim_no_overlap")
                claim_path.rename(locks / (claim_path.stem + ".expired." + str(time.time_ns()) + ".json"))
            runtime.write_once(claim_path, dict(job_id=config["job_id"], created_unix=now, hold_until_unix=deadline + 30))
        launch_path = root / "runtime/LAUNCH.json"
        runtime.write_once(launch_path, dict(job_id=config["job_id"], config_sha256=arguments.config_sha256,
            created_unix=now, deadline_unix=deadline, no_native_signals=True))
        launched = []
        try:
            for spec in commands(config, arguments.config, arguments.config_sha256, launch_path,
                    runtime.sha(launch_path), deadline, time.time()):
                runtime.verify_protected(config)
                runtime.validate_admission(config, runtime.gpu_inventory(), roles=(spec["role"],))
                submit(spec["argv"])
                launched.append(dict(role=spec["role"], unit=spec["unit"], status="DISPATCHED_NOT_YET_LOADED"))
        except Exception as error:
            runtime.write_once(root / "runtime/DISPATCH_FAILED.json", dict(unix=time.time(),
                error_type=type(error).__name__, status="TERMINAL_NO_RETRY_NO_ALTERNATE_ROUTE", launched=launched))
            raise
        runtime.write_once(root / "runtime/DISPATCHED.json", dict(unix=time.time(), launched=launched,
            deadline_unix=deadline, status="DISPATCHED_NOT_YET_LOADED", gpu_jobs=2))
        print(json.dumps(dict(status="DISPATCHED_NOT_YET_LOADED", launched=launched, deadline_unix=deadline)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
