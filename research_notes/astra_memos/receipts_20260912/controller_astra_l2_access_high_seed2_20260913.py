"""Main-owned finite controller for read-only saved-adapter diagnostics."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


GPU_INDEX = 3
GPU_UUID = "GPU-e1277146-04f2-c38f-d1ae-1a98132f907e"
PRECHECK_PIN = "32d366afc432d9e8dcf0c188cbf0725cdadfcc68a1a0f8e0b11532ca7629862a"
SOURCE = "/localhome/local-rohing/astra_sources/l2_lr_comparison_20260913_attempt1"
STATES = ("OFF", "fit1", "fit2_PROMOTE")
BOOT_ID_PATH = Path("/proc/sys/kernel/random/boot_id")
LEASE_MARGIN_SECONDS = 21600
TOTAL_SECONDS = 1200


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")


def identity(pid):
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return dict(pid=pid, start_ticks=int(fields[19]), pgid=int(fields[2]))


def environment(device=""):
    return dict(os.environ, CUDA_VISIBLE_DEVICES=device, PYTHONDONTWRITEBYTECODE="1",
                PYTHONNOUSERSITE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                HF_DATASETS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", WANDB_DISABLED="true",
                VLLM_NO_USAGE_STATS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
                TOKENIZERS_PARALLELISM="false", CUBLAS_WORKSPACE_CONFIG=":4096:8",
                PYTHONHASHSEED="0", PYTHONPATH=SOURCE)


def check_allocation_binding(options):
    require(isinstance(options.expected_boot_id, str) and len(options.expected_boot_id) == 36 and
            BOOT_ID_PATH.read_text(encoding="ascii").strip() == options.expected_boot_id, "current node boot binding differs")
    require(type(options.lease_end_unix) in (int, float) and math.isfinite(options.lease_end_unix) and
            time.time() + TOTAL_SECONDS + LEASE_MARGIN_SECONDS < options.lease_end_unix, "lease margin insufficient")


def precheck(options, output):
    check_allocation_binding(options)
    started = time.time()
    require(digest(options.precheck) == PRECHECK_PIN, "precheck changed")
    result = subprocess.run([sys.executable, "-B", options.precheck, "--gpu-index", str(GPU_INDEX),
                             "--gpu-uuid", GPU_UUID], stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, timeout=60, env=environment())
    write(output, dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                       checked_unix=time.time()))
    require(result.returncode == 0, "vacancy/reservation or release check failed")
    receipt = json.loads(result.stdout)
    require(receipt["gpu_index"] == GPU_INDEX and receipt["gpu_uuid"] == GPU_UUID and
            type(receipt["checked_unix"]) in (int, float) and
            started <= receipt["checked_unix"] <= time.time() and
            receipt["compute_processes"] == [] and receipt["matching_reservations"] == [] and
            receipt["unresolved_same_user"] == [], "fresh vacancy receipt differs")


def stop_owned(process, bound_identity):
    if process.poll() is not None:
        return
    require(identity(process.pid) == bound_identity and bound_identity["pgid"] == process.pid,
            "refuse cleanup of unbound process")
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        require(identity(process.pid) == bound_identity, "identity changed before kill")
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)


def run_worker(options, root, state, deadline):
    require(time.time() + 90 < deadline, "no worker/cleanup budget remains")
    require(digest(options.probe) == options.probe_sha256, "probe changed")
    precheck(options, root / f"{state}.precheck.json")
    worker_deadline = min(time.time() + 390, deadline - 60)
    require(worker_deadline > time.time(), "worker budget exhausted")
    output = root / f"{state}.json"
    command = [sys.executable, "-B", options.probe, "worker", "--source", SOURCE,
               "--collection", options.collection, "--state", state, "--output", str(output),
               "--deadline-unix", str(worker_deadline), "--allow-native"]
    with (root / f"{state}.stdout").open("xb") as stdout, (root / f"{state}.stderr").open("xb") as stderr:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                   env=environment(GPU_UUID), start_new_session=True)
        bound = identity(process.pid)
        write(root / f"{state}.launch.json", dict(command=command, identity=bound, launched_unix=time.time(),
                                                   gpu_index=GPU_INDEX, gpu_uuid=GPU_UUID))
        try:
            returncode = process.wait(timeout=max(1, worker_deadline - time.time()))
        except BaseException:
            stop_owned(process, bound)
            precheck(options, root / f"{state}.abort_release.json")
            raise
    precheck(options, root / f"{state}.release.json")
    require(returncode == 0 and output.is_file(), f"{state} failed with exit {returncode}")
    receipt = json.loads(output.read_text())
    require(receipt["state"] == state and receipt["forwards"] == 64 and receipt["updates"] == 0,
            "worker budget receipt differs")
    return [str(output), digest(output)]


def controller(options):
    require(options.allow_gpu, "explicit native permission required")
    require(not os.environ.get("CUDA_VISIBLE_DEVICES"), "controller must not reserve CUDA")
    require(digest(options.probe) == options.probe_sha256, "probe pin mismatch")
    root = Path(options.root)
    require(root.is_absolute() and root.parent.resolve() == Path("/localhome/local-rohing/astra_diagnostics"),
            "new diagnostic root required")
    require(root.name.startswith("l2_access_high_seed2_") and not root.exists(), "root already exists or wrong family")
    check_allocation_binding(options)
    root.mkdir(mode=0o700)
    started = time.time()
    write(root / "controller_started.json", dict(started_unix=started, deadline_unix=started + TOTAL_SECONDS,
          pid=os.getpid(), probe_sha256=options.probe_sha256, controller_sha256=digest(__file__),
          source=SOURCE, states=STATES, max_forwards=192, updates=0, gpu_index=GPU_INDEX, gpu_uuid=GPU_UUID,
          expected_boot_id=options.expected_boot_id, lease_end_unix=options.lease_end_unix, precheck_sha256=PRECHECK_PIN))
    try:
        workers = [run_worker(options, root, state, started + TOTAL_SECONDS) for state in STATES]
        command = [sys.executable, "-B", options.probe, "reduce", "--source", SOURCE,
                   "--collection", options.collection, "--output", str(root / "report.json")]
        for path, checksum in workers:
            command.extend(["--worker", path, checksum])
        with (root / "reduce.stdout").open("xb") as stdout, (root / "reduce.stderr").open("xb") as stderr:
            subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                           env=environment(), check=True, timeout=max(1, started + TOTAL_SECONDS - time.time()))
        require(time.time() <= started + TOTAL_SECONDS, "controller exceeded budget")
        terminal = dict(status="COMPLETE_DIAGNOSTIC_ONLY", report_sha256=digest(root / "report.json"), workers=workers)
    except BaseException as error:
        terminal = dict(status="FAILED_NO_RETRY", error_type=type(error).__name__, error=str(error))
    terminal.update(finished_unix=time.time(), elapsed_seconds=time.time() - started, updates=0)
    write(root / "terminal.json", terminal)
    print(json.dumps(terminal, sort_keys=True), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("root", "probe", "probe-sha256", "collection", "precheck", "expected-boot-id"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--lease-end-unix", type=float, required=True)
    parser.add_argument("--allow-gpu", action="store_true")
    controller(parser.parse_args())
