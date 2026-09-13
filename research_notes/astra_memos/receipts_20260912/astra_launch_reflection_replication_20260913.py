"""Main-only detachment of a paired learner-seed 1/2 reflection replica."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


SELF = Path(__file__).resolve()
SCOPE = "authored_reflection_12train_24dev_learner_seed_replication_v1"
LEARNER_SEEDS = (1, 2)
PARENT_DRIVER_SHA256 = "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc"
PARENT_LAUNCHER_SHA256 = "56fef18cf9102721548e769100e8368c3432d484fade1e564ad074743165841b"
CONTROLLER_SECONDS, COLLECTION_SECONDS, CLEANUP_SECONDS = 3600, 180, 40
LEASE_MARGIN_SECONDS, PRECHECK_SECONDS = 21600, 60
FINISH_RESERVE_SECONDS = CONTROLLER_SECONDS + COLLECTION_SECONDS + CLEANUP_SECONDS
REQUIRED_LEASE_SECONDS = FINISH_RESERVE_SECONDS + LEASE_MARGIN_SECONDS
STAGES = ["fit_withdrawn", "fit_present"] + [
    state + "__" + arm for state in ("OFF", "fitWithdrawn", "fitPresent") for arm in ("withdrawn", "present")]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique_object,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def write(path, value):
    data = (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def disjoint(left, right):
    left, right = Path(left).resolve(), Path(right).resolve()
    return left != right and left not in right.parents and right not in left.parents


def check_stdout(path, protected):
    path = Path(os.path.abspath(path))
    require(not any(part.is_symlink() for part in (path, *path.parents)), "symlink stdout path forbidden")
    require(not path.exists() and path.parent.is_dir(), "existing stdout or missing stdout parent")
    require(all(disjoint(path, other) for other in protected), "overlapping stdout forbidden")
    return path


def check_fresh(root, own_claim=False):
    require(not (root / "run").exists() and not (root / "run").is_symlink(), "started run root forbidden")
    for path in root.rglob("*"):
        require(not path.is_symlink(), "symlink in prepared root")
        name = path.name
        allowed = path == root / "prepare_started.json" or (own_claim and path == root / "launcher_started.json")
        require(not ((name.endswith("started.json") and not allowed) or "failure" in name or
                     name in ("capture_complete.json", "launcher_detached.json") or name.endswith(".pending")),
                "started, failed, completed, or pending root forbidden")


def check_pins(options, root, driver, precheck):
    learner_seed = getattr(options, "learner_seed", None)
    require(type(learner_seed) is int and learner_seed in LEARNER_SEEDS, "learner_seed must be integer 1 or 2")
    for path, expected in ((driver, options.driver_sha256), (root / "plan.json", options.plan_sha256),
                           (precheck, options.precheck_sha256)):
        require(isinstance(expected, str) and len(expected) == 64 and
                all(character in "0123456789abcdef" for character in expected), "final SHA256 pin required")
        require(path.is_file() and not path.is_symlink() and digest(path) == expected,
                "final runtime, plan, or precheck pin changed")
    plan = read(root / "plan.json")
    require(type(plan.get("learner_seed")) is int and plan["learner_seed"] == learner_seed and
            type(plan.get("config", {}).get("seed")) is int and plan["config"]["seed"] == learner_seed,
            "selected learner seed differs from paired prepared root")
    require(plan.get("parent_driver_sha256") == PARENT_DRIVER_SHA256, "replication parent source differs")
    require(plan["self_sha256"] == options.driver_sha256 and plan["root"] == str(root), "bound root or runtime differs")
    require(plan["python"] == os.path.abspath(sys.executable), "use the exact prepared native interpreter")
    require(plan["scope"] == SCOPE and plan["stages"] == STAGES and plan["calls"] == 144,
            "not the selected reflection comparison")
    require(plan["outer_seconds"] == CONTROLLER_SECONDS and plan["collection_seconds"] == COLLECTION_SECONDS and
            plan["gpu_query_seconds"] == 30 and plan["fit_seconds"] == 600 and plan["readout_seconds"] == 300,
            "changed reflection experiment budget")
    require(type(plan["gpu_index"]) is int and plan["gpu_index"] >= 0 and
            isinstance(plan["gpu_uuid"], str) and plan["gpu_uuid"].startswith("GPU-"), "GPU identity missing")
    require(type(plan["lease_end"]) in (int, float) and math.isfinite(plan["lease_end"]) and
            plan["lease_end"] >= time.time() + REQUIRED_LEASE_SECONDS,
            "six-hour lease margin after reserved run finish required")
    return plan


def process_identity(process):
    require(type(process.pid) is int and process.pid > 1, "invalid detached PID")
    fields = Path(f"/proc/{process.pid}/stat").read_text().rsplit(")", 1)[1].split()
    pgid = os.getpgid(process.pid)
    require(fields[0] not in ("Z", "X") and int(fields[2]) == pgid == process.pid and
            int(fields[3]) == process.pid and int(fields[19]) > 0 and process.poll() is None,
            "detached controller identity not live or isolated")
    return dict(pid=process.pid, pgid=pgid, start_ticks=int(fields[19]))


def launch(options):
    require(getattr(options, "allow_gpu", False) is True, "Main-only launch requires explicit --allow-gpu")
    root, driver, precheck = (Path(value).resolve() for value in (options.root, options.driver, options.precheck))
    require(root.is_dir(), "existing prepared root required")
    check_fresh(root)
    plan = check_pins(options, root, driver, precheck)
    protected = (root, driver, precheck, SELF, plan["source"], plan["model"], plan["log_dir"], plan["probe_driver"])
    log = check_stdout(options.stdout, protected)
    command = [plan["python"], "-B", str(driver), "controller", "--root", str(root),
               "--plan-sha256", options.plan_sha256, "--allow-gpu"]
    precheck_command = [plan["python"], "-B", str(precheck), "--gpu-index", str(plan["gpu_index"]),
                        "--gpu-uuid", plan["gpu_uuid"]]
    pins = dict(driver_sha256=options.driver_sha256, plan_sha256=options.plan_sha256,
                precheck_sha256=options.precheck_sha256, launcher_sha256=digest(SELF))
    write(root / "launcher_started.json", dict(status="LAUNCH_ATTEMPT_NO_RETRY", learner_seed=plan["learner_seed"], started_unix=time.time(),
          root=str(root), driver=str(driver), precheck=str(precheck), stdout=str(log), command=command, pins=pins))
    process = None
    identity = None
    try:
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1",
                           PYTHONNOUSERSITE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                           HF_DATASETS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", VLLM_NO_USAGE_STATS="1",
                           OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", TOKENIZERS_PARALLELISM="false",
                           CUBLAS_WORKSPACE_CONFIG=":4096:8", PYTHONHASHSEED="0", PYTHONPATH=plan["source"])
        checked = subprocess.run(precheck_command, check=False, capture_output=True, text=True,
                                 timeout=PRECHECK_SECONDS, env=environment, stdin=subprocess.DEVNULL)
        write(root / "launcher_precheck.json", dict(learner_seed=plan["learner_seed"], command=precheck_command, pins=pins,
              finished_unix=time.time(), cuda_visible_devices="", timeout_seconds=PRECHECK_SECONDS,
              returncode=checked.returncode, stdout=checked.stdout, stderr=checked.stderr))
        require(checked.returncode == 0, "fresh allocation/vacancy precheck failed; no launch")
        require(check_pins(options, root, driver, precheck) == plan, "plan changed during precheck")
        check_fresh(root, own_claim=True)
        check_stdout(log, protected)
        descriptor = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        spawn_unix = time.time()
        with os.fdopen(descriptor, "wb") as stream:
            require(plan["lease_end"] >= spawn_unix + REQUIRED_LEASE_SECONDS,
                    "six-hour lease margin after reserved run finish lost before spawn")
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                                       cwd=driver.parent, env=dict(environment, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"]),
                                       start_new_session=True)
        identity = process_identity(process)
        receipt = dict(status="LAUNCHED_NOT_SCIENTIFIC_RESULT", learner_seed=plan["learner_seed"],
                       parent_driver_sha256=PARENT_DRIVER_SHA256, parent_launcher_sha256=PARENT_LAUNCHER_SHA256, **identity, command=command, pins=pins,
                       root=str(root), stdout=str(log), driver=str(driver), precheck=str(precheck),
                       **{key: value for key, value in pins.items() if key != "launcher_sha256"},
                       launched_unix=spawn_unix, gpu_uuid=plan["gpu_uuid"], gpu_index=plan["gpu_index"],
                       controller_seconds=CONTROLLER_SECONDS, controller_work_seconds=CONTROLLER_SECONDS - CLEANUP_SECONDS,
                       collection_seconds=COLLECTION_SECONDS, cleanup_seconds=CLEANUP_SECONDS,
                       cleanup_included_in_controller=True,
                       ceiling=dict(controller_seconds=CONTROLLER_SECONDS, cleanup_seconds=CLEANUP_SECONDS,
                                    cleanup_included=True, collection_seconds=COLLECTION_SECONDS, collection_separate=True),
                       controller_budget_reference="pinned runtime controller entry, not launcher/precheck start",
                       controller_and_separate_collection_seconds=CONTROLLER_SECONDS + COLLECTION_SECONDS,
                       collection_launched=False, precheck_timeout_seconds=PRECHECK_SECONDS,
                       lease_end=plan["lease_end"], minimum_lease_margin_seconds=LEASE_MARGIN_SECONDS,
                       lease_margin_reference="after controller + collection + additional cleanup reserve",
                       finish_reserve_seconds=FINISH_RESERVE_SECONDS, required_lease_seconds=REQUIRED_LEASE_SECONDS,
                       reserved_finish_unix=spawn_unix + FINISH_RESERVE_SECONDS,
                       lease_margin_after_reserved_finish_seconds=plan["lease_end"] - spawn_unix - FINISH_RESERVE_SECONDS,
                       lease_margin_at_spawn_seconds=plan["lease_end"] - spawn_unix, retry=False)
        write(root / "launcher_detached.json", receipt)
        return receipt
    except BaseException as error:
        failure = dict(status="LAUNCH_FAILED_NO_RETRY", learner_seed=plan["learner_seed"], error_type=type(error).__name__, error=str(error),
                       time=time.time(), command=command, pins=pins, stdout=str(log),
                       pid=None if process is None else process.pid, identity=identity,
                       controller_may_be_running=process is not None,
                       action="Main must reconcile any spawned controller; do not relaunch or infer GPU release")
        if isinstance(error, subprocess.TimeoutExpired):
            for key in ("stdout", "stderr"):
                value = getattr(error, key, None)
                failure["precheck_" + key] = value.decode(errors="replace") if isinstance(value, bytes) else value
        write(root / "launcher_failure.json", failure)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "driver", "stdout", "driver-sha256", "plan-sha256", "precheck", "precheck-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--learner-seed", type=int, choices=LEARNER_SEEDS, required=True)
    parser.add_argument("--allow-gpu", action="store_true")
    print(json.dumps(launch(parser.parse_args(argv)), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
