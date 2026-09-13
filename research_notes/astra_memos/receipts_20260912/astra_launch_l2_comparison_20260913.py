"""Prospective NODE3 comparison launcher; not launch authorization or a result."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


SELF = Path(__file__).resolve()
PRECHECK_SHA256 = "32d366afc432d9e8dcf0c188cbf0725cdadfcc68a1a0f8e0b11532ca7629862a"
SCHEMA = "astra_l2_public_record_runtime_v1"
CORE_SCHEMA = "l2_public_record_dev_v0"
GPU_INDICES = frozenset((0, 1, 2, 4, 5, 6))
NODE3_BOOT_ID = "247596ab-08fe-436a-abbd-b8494c19e5d7"
BOOT_ID_PATH = Path("/proc/sys/kernel/random/boot_id")
CONTROLLER_SECONDS, COLLECTION_SECONDS, LEASE_MARGIN_SECONDS = 5400, 180, 21600
REQUIRED_LEASE_SECONDS = CONTROLLER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN_SECONDS
PRECHECK_SECONDS = 60
SOURCE_NAMES = {"organism_v6/__init__.py", "organism_v6/l2_public_record_dev.py",
                "organism_v6/train_adapter_v3.py", "gpu/astra_l2_public_record_dev.py"}
PREPARED_NAMES = {"prepare_started.json", "plan.json", "calls.json", "world.json", "model_binding.json"}
PLAN_KEYS = {"schema", "spec", "spec_sha256", "root", "python", "python_sha256", "model_files", "base_sha256",
             "seeds", "config", "engine", "params", "stages", "caps", "generic_system", "chat_template",
             "environment", "claim", "prepared_files"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_node3():
    require(BOOT_ID_PATH.read_text(encoding="ascii").strip() == NODE3_BOOT_ID, "NODE3 boot identity differs")


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


def process_identity(process):
    require(type(process.pid) is int and process.pid > 1, "invalid detached PID")
    fields = Path(f"/proc/{process.pid}/stat").read_text().rsplit(")", 1)[1].split()
    pgid = os.getpgid(process.pid)
    require(fields[0] not in ("Z", "X") and int(fields[2]) == pgid == process.pid and
            int(fields[3]) == process.pid and int(fields[19]) > 0 and process.poll() is None,
            "detached controller identity not live or isolated")
    return dict(pid=process.pid, pgid=pgid, start_ticks=int(fields[19]))


def load_runtime(driver, runtime_sha256):
    require(isinstance(runtime_sha256, str) and len(runtime_sha256) == 64 and
            all(character in "0123456789abcdef" for character in runtime_sha256) and
            digest(driver) == runtime_sha256, "runtime pin differs")
    spec = importlib.util.spec_from_file_location("_l2_launcher_final_runtime", driver)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fresh_root(root, runtime):
    require(root.is_dir() and {path.name for path in root.iterdir()} == PREPARED_NAMES,
            "prepared-only root required; prior start, run, terminal or seal forbidden")
    require(set(runtime.tree(root)) == PREPARED_NAMES, "prepared root links or inventory differ")


def lease_check(plan):
    lease_end = plan["spec"]["lease_end"]
    require(type(lease_end) in (int, float) and math.isfinite(lease_end) and
            time.time() + REQUIRED_LEASE_SECONDS <= lease_end, "six-hour margin after 5400+180 finish required")


def verify(options, root, driver, precheck, runtime):
    require(digest(driver) == runtime.pin(options.driver_sha256), "runtime pin differs")
    require(options.precheck_sha256 == PRECHECK_SHA256 and digest(precheck) == PRECHECK_SHA256,
            "final targeted precheck pin differs")
    require(digest(root / "plan.json") == runtime.pin(options.plan_sha256), "final plan pin differs")
    plan = read(root / "plan.json")
    require(set(plan) - {"learning_rate"} == PLAN_KEYS and plan["schema"] == SCHEMA and plan["root"] == str(root),
            "exact L2 plan schema/root required")
    spec = plan["spec"]
    require(spec["core_schema"] == CORE_SCHEMA and set(spec["source_files"]) == SOURCE_NAMES,
            "final core schema and four-file source pins required")
    require(spec["source_files"]["gpu/astra_l2_public_record_dev.py"] == options.driver_sha256 and
            driver == Path(spec["source"]) / "gpu/astra_l2_public_record_dev.py", "driver must be in final four-file snapshot")
    runtime.validate_spec(spec)
    check_node3()
    require(type(options.gpu_index) is int and options.gpu_index in GPU_INDICES and
            type(spec["gpu_index"]) is int and spec["gpu_index"] == options.gpu_index and
            spec["gpu_uuid"] == options.gpu_uuid, "planned index/UUID must match manifest on NODE3")
    require(plan["python"] == os.path.abspath(sys.executable) and plan["python_sha256"] == digest(sys.executable),
            "exact prepared interpreter required")
    expected = dict(engine=runtime.ENGINE, params=runtime.PARAMS, stages=list(runtime.STAGES),
                    caps=runtime.CAPS, generic_system=runtime.GENERIC_SYSTEM, claim=runtime.CLAIM)
    require(all(runtime.encoded(plan[key]) == runtime.encoded(value) for key, value in expected.items()),
            "closed L2 configuration differs")
    validated = runtime.verify(root, options.plan_sha256, native=False)[0]
    require(runtime.encoded(validated) == runtime.encoded(plan), "runtime validated plan differs")
    require(runtime.OUTER_SECONDS == CONTROLLER_SECONDS and runtime.COLLECTION_SECONDS == COLLECTION_SECONDS and
            runtime.LEASE_MARGIN == LEASE_MARGIN_SECONDS and runtime.CLEANUP_SECONDS == 40, "final runtime budgets differ")
    require(plan["base_sha256"] == runtime.value_hash(plan["model_files"]), "base map binding differs")
    runtime.pin(plan["spec_sha256"])
    require(read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"], "preparation spec pin differs")
    require(set(plan["prepared_files"]) == {"calls.json", "world.json", "model_binding.json"}, "prepared inventory differs")
    for name, checksum in plan["prepared_files"].items():
        require(digest(root / name) == runtime.pin(checksum), "prepared artifact pin differs")
    lease_check(plan)
    return plan


def launch(options):
    require(getattr(options, "allow_gpu", False) is True, "Main-only launch requires explicit --allow-gpu")
    sys.dont_write_bytecode = True
    driver = Path(os.path.abspath(options.driver))
    require(not any(path.is_symlink() for path in (driver, *driver.parents)), "symlink runtime path forbidden")
    check_node3()
    runtime = load_runtime(driver, options.driver_sha256)
    root, precheck = (runtime.plain_path(os.path.abspath(value)) for value in (options.root, options.precheck))
    runtime.launcher_output_outside(root)
    fresh_root(root, runtime)
    plan = verify(options, root, driver, precheck, runtime)
    spec = plan["spec"]
    claim = runtime.plain_path(str(root.with_name(root.name + ".launcher")))
    protected = (root, driver, precheck, SELF, spec["source"], spec["model"],
                 spec["protocol"]["path"], spec["model_binding"]["path"],
                 *[record["path"] for record in spec["helpers"].values()])
    require(not claim.exists() and all(disjoint(claim, path) for path in protected), "existing or overlapping launch claim forbidden")
    log = check_stdout(options.stdout, (*protected, claim))
    command = [plan["python"], "-B", str(driver), "controller", "--root", str(root),
               "--plan-sha256", options.plan_sha256, "--allow-gpu"]
    pins = dict(runtime_sha256=options.driver_sha256, plan_sha256=options.plan_sha256, precheck_sha256=PRECHECK_SHA256,
                launcher_sha256=digest(SELF), source_files=spec["source_files"])
    claim.mkdir(mode=0o700)
    process = None
    try:
        write(claim / "started.json", dict(root=str(root), command=command, pins=pins, stdout=str(log), time=time.time()))
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
                           HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1", WANDB_DISABLED="true",
                           HF_HUB_DISABLE_TELEMETRY="1", VLLM_NO_USAGE_STATS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
                           TOKENIZERS_PARALLELISM="false", CUBLAS_WORKSPACE_CONFIG=":4096:8", PYTHONHASHSEED="0",
                           PYTHONPATH=spec["source"])
        check_command = [plan["python"], "-B", str(precheck), "--gpu-index", str(options.gpu_index), "--gpu-uuid", options.gpu_uuid]
        result = subprocess.run(check_command, capture_output=True, text=True, check=False, timeout=PRECHECK_SECONDS,
                                stdin=subprocess.DEVNULL, env=environment)
        write(claim / "precheck.json", dict(command=check_command, pins=pins, returncode=result.returncode,
              stdout=result.stdout, stderr=result.stderr, time=time.time(), cuda_visible_devices="", timeout_seconds=PRECHECK_SECONDS))
        require(result.returncode == 0, "fresh targeted vacancy precheck failed; no launch")
        fresh_root(root, runtime)
        require(verify(options, root, driver, precheck, runtime) == plan, "plan changed during precheck")
        check_stdout(log, (*protected, claim))
        descriptor = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as output:
            lease_check(plan)
            spawned = time.time()
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=True, cwd=driver.parent,
                                       env=dict(environment, CUDA_VISIBLE_DEVICES=options.gpu_uuid))
        identity = process_identity(process)
        receipt = dict(status="LAUNCHED_NOT_SCIENTIFIC_RESULT", **identity, command=command, pins=pins,
                       root=str(root), claim_dir=str(claim), stdout=str(log), launched_unix=spawned,
                       gpu_index=options.gpu_index, gpu_uuid=options.gpu_uuid, controller_seconds=CONTROLLER_SECONDS,
                       collection_seconds=COLLECTION_SECONDS, cleanup_seconds=40, cleanup_included_in_controller=True,
                       controller_budget_reference="pinned runtime controller entry", collection_launched=False,
                       lease_end=spec["lease_end"], required_lease_seconds=REQUIRED_LEASE_SECONDS,
                       post_finish_margin_seconds=LEASE_MARGIN_SECONDS, retry=False)
        write(claim / "detached.json", receipt)
        return receipt
    except BaseException as error:
        failure = dict(status="LAUNCH_FAILED_NO_RETRY", error_type=type(error).__name__, error=str(error),
                       root=str(root), command=command, pins=pins, stdout=str(log), time=time.time(),
                       pid=None if process is None else process.pid, controller_may_be_running=process is not None,
                       action="Main must reconcile any spawned controller; do not retry or infer release")
        if isinstance(error, subprocess.TimeoutExpired):
            for key in ("stdout", "stderr"):
                value = getattr(error, key, None)
                failure["precheck_" + key] = value.decode(errors="replace") if isinstance(value, bytes) else value
        write(claim / "failure.json", failure)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "driver", "driver-sha256", "plan-sha256", "precheck", "precheck-sha256", "stdout"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--gpu-index", type=int, choices=sorted(GPU_INDICES), required=True)
    parser.add_argument("--gpu-uuid", required=True)
    parser.add_argument("--allow-gpu", action="store_true")
    print(json.dumps(launch(parser.parse_args(argv)), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
