"""Bounded, fresh-process ON/OFF evaluation; no training or clean-lineage claims.

Caller owns GPU reservation, source authentication and panel-selection history.
The spec names immutable local inputs, explicit budgets and a prospective order.
No model loads without --allow-gpu. Failed/partial roots are never reused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


FIELDS = {
    "model_path", "adapter_path", "expected_model_hashes", "expected_adapter_hashes",
    "families_path", "families_sha256", "probe_root", "output_dir",
    "training_life_roots", "lineage_roots", "episode_ids", "gen_seed", "seed_salt",
    "budget_ticks", "wake_max_tokens", "scratchpad_max_tokens", "total_token_budget",
    "max_episodes", "max_model_len", "worker_timeout_seconds", "order", "panel_role",
    "selection_used_episode_ids",
}
PROBE_FIELDS = {
    "model_path", "adapter_path", "expected_model_hashes", "expected_adapter_hashes",
    "probe_root", "training_life_roots", "lineage_roots", "episode_ids", "gen_seed",
    "seed_salt", "budget_ticks", "wake_max_tokens", "scratchpad_max_tokens",
    "total_token_budget", "max_episodes",
}


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _write(path, payload):
    with Path(path).open("x", encoding="utf-8") as target:
        target.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
        target.flush()
        os.fsync(target.fileno())


def selected_device():
    value = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    _require(re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", value) is not None,
             "one explicit reserved CUDA_VISIBLE_DEVICES selector is required")
    return value


def gpu_processes_absent(device):
    try:
        result = subprocess.run(["nvidia-smi", "-i", device, "-q", "-x"],
                                capture_output=True, text=True, timeout=30, check=False)
        if result.returncode != 0:
            return False
        gpus = ET.fromstring(result.stdout).findall("gpu")
        if len(gpus) != 1:
            return False
        processes = gpus[0].find("processes")
        return (processes is not None and not (processes.text or "").strip()
                and not list(processes))
    except (OSError, subprocess.SubprocessError, ET.ParseError):
        return False


def _group_alive(group):
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = path.read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == group and fields[0] not in ("Z", "X"):
                return True
        except FileNotFoundError:
            continue
    return False


def _cleanup_group(process):
    for action in (signal.SIGTERM, signal.SIGKILL):
        if not _group_alive(process.pid):
            break
        try:
            os.killpg(process.pid, action)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + 2
        while _group_alive(process.pid) and time.monotonic() < deadline:
            time.sleep(0.05)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        return False
    return not _group_alive(process.pid)


def run_worker(command, *, log_path, timeout, device):
    environment = os.environ.copy()
    environment.update(PYTHONPATH=str(Path(__file__).resolve().parents[1]), PYTHONNOUSERSITE="1",
                       PYTHONDONTWRITEBYTECODE="1", VLLM_WORKER_MULTIPROC_METHOD="spawn",
                       HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", CUDA_VISIBLE_DEVICES=device)
    with log_path.open("xb") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                   cwd=str(Path(__file__).resolve().parents[1]), env=environment,
                                   start_new_session=True)
        try:
            _write(log_path.with_suffix(".process.json"), dict(pid=process.pid, pgid=process.pid, device=device,
                   multiprocessing="spawn", source_root=environment["PYTHONPATH"]))
            status = process.wait(timeout=timeout)
            if status != 0:
                raise subprocess.CalledProcessError(status, command)
        finally:
            cleanup_error = None
            try:
                group_empty = _cleanup_group(process)
            except (OSError, ValueError, IndexError) as error:
                group_empty = False
                cleanup_error = dict(error_type=type(error).__name__, error=str(error))
            gpu_empty = gpu_processes_absent(device)
            _write(log_path.with_suffix(".cleanup.json"), dict(
                pid=process.pid, owned_group_empty=group_empty, device=device,
                gpu_processes_absent=gpu_empty, reservation_release_verified=group_empty and gpu_empty,
                cleanup_error=cleanup_error,
                scope="owned group and GPU process table; unrelated reservations remain caller-owned"))
        _require(group_empty and gpu_empty, "worker cleanup is unverified; reservation retained")
        return process.pid


def read_spec(path, expected_sha256):
    content = Path(path).read_bytes()
    _require(hashlib.sha256(content).hexdigest() == expected_sha256, "spec digest mismatch")
    spec = json.loads(content)
    _require(isinstance(spec, dict) and set(spec) == FIELDS, "unknown or missing spec fields")
    _require(spec["order"] in (["off", "on"], ["on", "off"]), "invalid prospective order")
    _require(spec["panel_role"] in ("development_validation", "untouched_confirmation", "exploratory"),
             "explicit panel role required")
    for name in ("episode_ids", "selection_used_episode_ids", "training_life_roots", "lineage_roots"):
        values = spec[name]
        _require(isinstance(values, list) and all(isinstance(value, str) and value for value in values),
                 "invalid " + name)
        _require(len(values) == len(set(values)), "duplicate " + name)
    _require(spec["episode_ids"] and spec["training_life_roots"] and spec["lineage_roots"],
             "nonempty panel and protected roots required")
    if spec["panel_role"] == "untouched_confirmation":
        _require(not set(spec["episode_ids"]) & set(spec["selection_used_episode_ids"]),
                 "confirmation panel overlaps declared selection data")
    for name in ("budget_ticks", "wake_max_tokens", "scratchpad_max_tokens", "total_token_budget",
                 "max_episodes", "max_model_len", "worker_timeout_seconds"):
        _require(type(spec[name]) is int and spec[name] > 0, "invalid " + name)
    for name in ("gen_seed", "seed_salt"):
        _require(type(spec[name]) is int and 0 <= spec[name] <= 0x7fffffff, "invalid " + name)
    _require(len(spec["episode_ids"]) <= spec["max_episodes"], "panel exceeds episode budget")
    for name in ("model_path", "adapter_path", "families_path", "probe_root", "output_dir"):
        _require(isinstance(spec[name], str) and Path(spec[name]).is_absolute(), "absolute " + name + " required")
    for name in ("model_path", "adapter_path", "families_path"):
        _require(Path(spec[name]).exists(), "missing " + name)
    _require(_digest(spec["families_path"]) == spec["families_sha256"], "families digest mismatch")
    root, output = Path(spec["probe_root"]).resolve(strict=True), Path(spec["output_dir"]).resolve()
    _require(root.is_dir() and root in output.parents, "output outside probe root")
    protected = [Path(spec[name]).resolve() for name in ("model_path", "adapter_path", "families_path")]
    protected.extend(Path(value).resolve() for value in spec["training_life_roots"] + spec["lineage_roots"])
    _require(not any(output == item or output in item.parents or item in output.parents for item in protected),
             "output overlaps protected inputs")
    from .reasoning_neutral_probe import file_hashes

    _require(file_hashes(spec["model_path"]) == spec["expected_model_hashes"], "model digest mismatch")
    _require(file_hashes(spec["adapter_path"]) == spec["expected_adapter_hashes"], "adapter digest mismatch")
    return spec


def run_condition(spec_path, spec_sha256, condition, *, allow_gpu=False):
    _require(allow_gpu is True, "explicit --allow-gpu is required")
    device = selected_device()
    _require(condition in ("on", "off"), "invalid condition")
    initial = json.loads(Path(spec_path).read_text())
    os.environ["V6_MODEL"] = initial["model_path"]
    os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    spec = read_spec(spec_path, spec_sha256)
    from . import model_backend
    from .neutral_pair_custody import verify_source_snapshot
    from .reasoning_gym_gym import ReasoningGymGym
    from .reasoning_neutral_probe import run_probe

    _require(model_backend.MODEL == spec["model_path"], "backend imported with another model")
    started = json.loads((Path(spec["output_dir"]) / "PAIR_STARTED.json").read_text())
    _require(started["spec_sha256"] == spec_sha256 and started["device"] == device,
             "worker differs from prospective pair binding")
    verify_source_snapshot(started["source_snapshot"])
    gym = ReasoningGymGym(families_path=spec["families_path"], strict_verifier=True)
    _require(all(gym.split_of(episode) in ("canary", "gate", "exam") for episode in spec["episode_ids"]),
             "panel includes non-held-out episode")
    options = {name: spec[name] for name in PROBE_FIELDS}
    if condition == "off":
        options.update(adapter_path=None, expected_adapter_hashes={})
    options["output_dir"] = str(Path(spec["output_dir"]) / condition)
    _require(not os.path.lexists(options["output_dir"]), "condition output already exists")
    model = None
    try:
        model = model_backend.VLLMBackend(adapter_path=options["adapter_path"], max_model_len=spec["max_model_len"])
        result = run_probe(model, gym, **options)
    finally:
        if not model_backend.close_backend(model):
            raise RuntimeError("backend did not close; no completion receipt")
    verify_source_snapshot(started["source_snapshot"])
    _write(Path(spec["output_dir"]) / (condition + "_WORKER_DONE.json"), dict(
        evidence_label="EVALUATION_ONLY", condition=condition, spec_sha256=spec_sha256,
        pid=os.getpid(), device=device, multiprocessing="spawn",
        results_sha256=_digest(Path(options["output_dir"]) / "results.json"),
        manifest_sha256=_digest(Path(options["output_dir"]) / "manifest.json")))
    return result


def run_pair(spec_path, spec_sha256, *, allow_gpu=False):
    _require(allow_gpu is True, "explicit --allow-gpu is required")
    device = selected_device()
    spec_path = str(Path(spec_path).resolve(strict=True))
    spec = read_spec(spec_path, spec_sha256)
    from .neutral_pair_custody import source_snapshot, validate_pair, verify_condition

    snapshot = source_snapshot()
    output = Path(spec["output_dir"])
    output.mkdir()
    _write(output / "PAIR_STARTED.json", dict(
        evidence_label="EVALUATION_ONLY", spec_sha256=spec_sha256, spec=spec,
        controller_pid=os.getpid(), wrapper_sha256=_digest(__file__), device=device,
        source_snapshot=snapshot,
        origin_verification="EXTERNAL_CALLER_REQUIRED", panel_history="CALLER_DECLARED"))
    receipts = {}
    try:
        for condition in spec["order"]:
            command = [sys.executable, "-B", "-m", "organism_v6.run_reasoning_neutral",
                       "--spec", spec_path, "--spec-sha256", spec_sha256,
                       "--condition", condition, "--allow-gpu"]
            worker_pid = run_worker(command, log_path=output / (condition + ".log"),
                                    timeout=spec["worker_timeout_seconds"], device=device)
            receipt = verify_condition(output, condition, spec_sha256)
            _require(receipt["pid"] != os.getpid(), "worker did not run in a fresh process")
            _require(receipt["pid"] == worker_pid and receipt["device"] == device
                     and receipt["multiprocessing"] == "spawn", "worker process binding mismatch")
            receipts[condition] = receipt
        _require(receipts["on"]["pid"] != receipts["off"]["pid"], "worker process identity reused")
        read_spec(spec_path, spec_sha256)
        receipt_hashes = validate_pair(output, spec_sha256, receipts, snapshot)
        _write(output / "PAIR_DONE.json", dict(
            evidence_label="EVALUATION_ONLY", spec_sha256=spec_sha256, workers=receipts,
            receipt_sha256=receipt_hashes, source_snapshot=snapshot,
            interpretation="Separate fresh-process observations; not a parenting or learning-efficiency estimate"))
    except BaseException as error:
        _write(output / "PAIR_FAILED.json", dict(error_type=type(error).__name__, error=str(error),
                reservation_release_verified=False, cleanup_evidence="inspect per-worker cleanup receipts"))
        raise
    return receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--spec-sha256", required=True)
    parser.add_argument("--condition", choices=("on", "off"))
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    if args.condition:
        run_condition(args.spec, args.spec_sha256, args.condition, allow_gpu=args.allow_gpu)
    else:
        run_pair(args.spec, args.spec_sha256, allow_gpu=args.allow_gpu)


if __name__ == "__main__":
    main()
