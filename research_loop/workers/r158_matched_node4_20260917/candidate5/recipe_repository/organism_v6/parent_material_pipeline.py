"""Explicit exploratory formation -> child-only fits -> parent-free observations.

Preparation is CPU/tokenizer-only. Execution requires caller-reserved devices;
there is no polling, retry, clean ancestry, admission or H1 decision here.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

from . import parent_material_write as writer
from . import run_reasoning_neutral as neutral
from .neutral_pair_custody import source_snapshot, validate_pair, verify_condition, verify_source_snapshot
from .reasoning_neutral_probe import file_hashes


ARMS = ("lesson", "sham")
ROOT = Path(__file__).resolve().parents[1]
TRAIN_TIMEOUT = 600
PROBE_TIMEOUT = 3600
LIMITS = dict(gen_seed=6103, seed_salt=6103, budget_ticks=3, wake_max_tokens=400,
              scratchpad_max_tokens=100, total_token_budget=20000, max_episodes=4,
              max_model_len=16384, worker_timeout_seconds=PROBE_TIMEOUT)
BOUNDARY = dict(evidence_label="EXPLORATORY_LOCAL_CHILD_WRITE_AND_PARENT_FREE_PROBE",
                model_provenance="LOCAL_HASHES_ONLY", official_base_authentication="UNRESOLVED",
                clean_lineage=False, admission_certificate=False,
                interpretation="Descriptive observations only; no H1 success gate or parenting-effect claim",
                token_budget_equivalence="NOT_ASSERTED; equal 64 examples and 48 steps, report child tokens")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _write(path, value):
    neutral._write(path, value)
    Path(path).chmod(0o444)


def _device(value):
    _require(isinstance(value, str) and re.fullmatch(
        r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", value) is not None,
        "one explicit reserved GPU selector per arm required")
    return value


def _panel(families):
    config = writer._read(families)
    names = config["gate_families"]
    _require(len(names) == 2 and len(set(names)) == 2, "exactly two gate families required")
    episodes = []
    for family in names:
        matches = [episode for episode in config["gate_set"] if episode.startswith(f"rg/{family}/")]
        _require(len(matches) >= 2, "missing gate episodes")
        episodes.extend(matches[:2])
    _require(len(set(episodes)) == 4 and not set(episodes) & set(config["canary_set"]),
             "gate panel overlaps actual canary or repeats episodes")
    return episodes, config["canary_set"]


def prepare_pipeline(pair_root, lesson_out, sham_out, output_dir, *, devices):
    """Prepare both arms, never fit one arm when its partner lacks 64 records."""
    pair_root = writer._path(pair_root)
    output = writer._path(output_dir, fresh=True)
    _require(set(devices) == set(ARMS), "both caller GPU selectors required")
    devices = {arm: _device(devices[arm]) for arm in ARMS}
    inputs = dict(zip(ARMS, map(writer._path, (lesson_out, sham_out))))
    _require(inputs["lesson"] != inputs["sham"] and
             all(pair_root in path.parents for path in inputs.values()), "formations must be distinct under pair root")
    snapshots = {arm: writer._formation_snapshot(path) for arm, path in inputs.items()}
    for arm in ARMS:
        _require(snapshots[arm]["config"]["mode"] == arm, "wrong formation arm")
    _require(snapshots["lesson"]["local_pins"] == snapshots["sham"]["local_pins"] and
             snapshots["lesson"]["schedule"] == snapshots["sham"]["schedule"], "unmatched model or formation schedule")
    model = Path(snapshots["lesson"]["config"]["model_path"])
    _require(all(not writer._overlap(output, protected) for protected in (pair_root, ROOT, model)),
             "pipeline output overlaps protected pair/source/model inputs")
    families = ROOT / "organism_v6/reasoning_gym_families.json"
    episodes, canary = _panel(families)
    snapshot = source_snapshot()
    output.mkdir()
    for name in ("preparations", "adapters", "logs", "probes"):
        (output / name).mkdir()
    reports = {}
    try:
        for arm in ARMS:
            reports[arm] = writer.prepare_write(inputs[arm], output / "preparations" / arm,
                adapter_dir=output / "adapters" / arm, trainer_log=output / "logs" / (arm + "_train.log"))
        ready = all(report["status"] == "READY" and report["selected_records"] == 64
                    for report in reports.values())
        plan = dict(**BOUNDARY, status="READY" if ready else "PAIRED_SKIP_INSUFFICIENT_MATERIAL",
            output_dir=str(output), pair_root=str(pair_root), formations={arm: str(path) for arm, path in inputs.items()},
            devices=devices, reports=reports, model_path=str(model), model_hashes=file_hashes(model),
            preparation_hashes={arm: writer._hash(output / "preparations" / arm / "artifact_hashes.json") for arm in ARMS},
            families_path=str(families), families_sha256=writer._hash(families), episode_ids=episodes,
            selection_used_episode_ids=canary, probe_limits=LIMITS, probe_order=["off", "on"],
            source_snapshot=snapshot, pipeline_sha256=writer._hash(Path(__file__)),
            python_executable=sys.executable, training_timeout_seconds=TRAIN_TIMEOUT,
            execution_order=["lesson_train", "sham_train", "lesson_probe_off_on", "sham_probe_off_on"])
        _write(output / "pipeline.json", plan)
        _write(output / "pipeline_digest.json", dict(sha256=writer._hash(output / "pipeline.json")))
        return plan
    except BaseException as error:
        _write(output / "PREPARATION_FAILED.json", dict(**BOUNDARY, error_type=type(error).__name__,
            error=str(error), completed_preparations=reports, fits_started=False))
        raise


def _verify_inputs(output, plan):
    _require(str(output) == plan["output_dir"], "prepared output moved")
    _require(writer._hash(Path(__file__)) == plan["pipeline_sha256"], "pipeline source changed")
    _require(plan["python_executable"] == sys.executable, "execute with the preparation Python interpreter")
    verify_source_snapshot(plan["source_snapshot"])
    _require(writer._hash(Path(plan["families_path"])) == plan["families_sha256"], "panel source changed")
    _require(file_hashes(plan["model_path"]) == plan["model_hashes"], "local base changed")
    for arm in ARMS:
        prep = output / "preparations" / arm
        _require(writer._hash(prep / "artifact_hashes.json") == plan["preparation_hashes"][arm], "preparation changed")
        inventory = writer._read(prep / "artifact_hashes.json")["files"]
        for name, digest in inventory.items():
            _require(Path(name).name == name and name not in (".", ".."), "unsafe preparation artifact")
            _require(not (prep / name).is_symlink() and writer._hash(prep / name) == digest, "preparation artifact changed")
        source = writer._formation_snapshot(Path(plan["formations"][arm]))
        original = writer._read(prep / "formation_inputs.json")
        _require(source["artifact_manifest_sha256"] == original["artifact_manifest_sha256"], "formation changed")
        for name, digest in writer._read(prep / "source_hashes.json")["files"].items():
            _require(writer._hash(Path(name)) == digest, "writer source changed")


def _environment(model, device):
    retained = ("PATH", "HOME", "USER", "LOGNAME", "TMPDIR", "LD_LIBRARY_PATH", "CUDA_HOME",
                "VIRTUAL_ENV", "CONDA_PREFIX", "HF_HOME", "HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "XDG_CACHE_HOME")
    environment = {key: os.environ[key] for key in retained if key in os.environ}
    environment.update(V6_MODEL=str(model), CUDA_VISIBLE_DEVICES=_device(device), PYTHONPATH=str(ROOT),
        PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", VLLM_WORKER_MULTIPROC_METHOD="spawn",
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    return environment


@contextmanager
def _execution_environment(model, device):
    previous = os.environ.copy()
    environment = _environment(model, device)
    os.environ.clear()
    os.environ.update(environment)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(previous)

def run_training(command, *, device, popen=None, occupancy=None, timeout=TRAIN_TIMEOUT):
    """One shell-free session; CPU tests may inject Popen and the process-table query."""
    occupancy = occupancy or neutral.gpu_processes_absent
    popen = popen or subprocess.Popen
    _require(0 < timeout <= TRAIN_TIMEOUT and math.isfinite(timeout), "invalid training timeout")
    _require(occupancy(device) is True, "GPU has processes or query failed; reservation retained")
    log_path = Path(command["stdout_path"])
    with log_path.open("xb") as log:
        process = popen(command["argv"], stdout=log, stderr=subprocess.STDOUT, shell=False,
            cwd=str(ROOT), env=_environment(command["env"]["V6_MODEL"], device), start_new_session=True)
        try:
            _write(log_path.with_suffix(".process.json"), dict(pid=process.pid, pgid=process.pid, device=device,
                argv=command["argv"], cwd=str(ROOT), timeout_seconds=timeout))
            status = process.wait(timeout=timeout)
            if status != 0:
                raise subprocess.CalledProcessError(status, command["argv"])
        finally:
            group_empty = False
            gpu_empty = False
            try:
                group_empty = neutral._cleanup_group(process)
                gpu_empty = occupancy(device) is True
            finally:
                _write(log_path.with_suffix(".cleanup.json"), dict(pid=process.pid, device=device,
                    owned_group_empty=group_empty, gpu_processes_absent=gpu_empty,
                    reservation_release_verified=group_empty and gpu_empty))
            _require(group_empty and gpu_empty, "training cleanup unverified; reservation retained")
    return process.pid


def _training_result(report):
    adapter = writer._path(report["adapter_dir"])
    _require((adapter / "DONE").is_file() and not (adapter / "EMPTY_CORPUS").exists(), "missing training DONE or empty corpus")
    metadata = writer._read(adapter / "train_meta.json")
    expected = report["metadata_equals"]
    _require(writer._bytes({key: metadata.get(key) for key in expected}) == writer._bytes(expected), "training metadata mismatch")
    loss = metadata.get("final_loss")
    _require(type(loss) in (int, float) and math.isfinite(loss), "nonfinite or missing training loss")
    _require((adapter / "adapter_config.json").is_file() and any(
        (adapter / name).is_file() and (adapter / name).stat().st_size > 0
        for name in ("adapter_model.safetensors", "adapter_model.bin")), "missing adapter config/weights")
    _require(not any(path.is_symlink() for path in adapter.rglob("*")), "symlink in trained adapter")
    return dict(metadata=metadata, adapter_hashes=file_hashes(adapter))


def _probe_spec(output, plan, arm, training):
    return dict(model_path=plan["model_path"], adapter_path=plan["reports"][arm]["adapter_dir"],
        expected_model_hashes=plan["model_hashes"], expected_adapter_hashes=training["adapter_hashes"],
        families_path=plan["families_path"], families_sha256=plan["families_sha256"],
        probe_root=str(output / "probes"), output_dir=str(output / "probes" / arm),
        training_life_roots=[plan["pair_root"], str(output / "preparations"), str(output / "adapters")],
        lineage_roots=[plan["pair_root"], str(ROOT)], episode_ids=plan["episode_ids"],
        **plan["probe_limits"], order=plan["probe_order"], panel_role="exploratory",
        selection_used_episode_ids=plan["selection_used_episode_ids"])


def _probe_results(spec_path, digest, receipts, snapshot):
    spec = neutral.read_spec(spec_path, digest)
    output = Path(spec["output_dir"])
    done = writer._read(output / "PAIR_DONE.json")
    _require(done["spec_sha256"] == digest and done["workers"] == receipts, "missing or mismatched probe completion")
    hashes = validate_pair(output, digest, receipts, snapshot)
    _require(done["receipt_sha256"] == hashes, "probe receipt hashes changed")
    results = {}
    for condition in ("off", "on"):
        verify_condition(output, condition, digest, receipts[condition])
        config = writer._read(output / condition / "configuration.json")
        for name in ("episode_ids", "gen_seed", "seed_salt", "budget_ticks", "wake_max_tokens",
                     "scratchpad_max_tokens", "total_token_budget", "max_episodes"):
            _require(config[name] == spec[name], "probe configuration differs from prechosen panel/budget")
        results[condition] = writer._read(output / condition / "results.json")
    return results


@contextmanager
def _termination_cleanup():
    previous = signal.getsignal(signal.SIGTERM)

    def terminate(signum, frame):
        raise InterruptedError("pipeline received SIGTERM; unwinding owned workers")

    signal.signal(signal.SIGTERM, terminate)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def execute_pipeline(output_dir, *, allow_gpu=False, popen=None, occupancy=None):
    """Execute once, sequentially; never launch a nested neutral controller process."""
    _require(allow_gpu is True, "explicit execution/allow_gpu required")
    output = writer._path(output_dir)
    _require(writer._hash(output / "pipeline.json") == writer._read(output / "pipeline_digest.json")["sha256"],
             "pipeline plan changed")
    plan = writer._read(output / "pipeline.json")
    if plan["status"] == "PAIRED_SKIP_INSUFFICIENT_MATERIAL":
        return dict(**BOUNDARY, status=plan["status"], reports=plan["reports"], fits_started=False)
    _require(plan["status"] == "READY", "pipeline not ready")
    occupancy = occupancy or neutral.gpu_processes_absent
    training, probes, originals = {}, {}, {}
    _write(output / "EXECUTION_STARTED.json", dict(**BOUNDARY, pipeline_sha256=writer._hash(output / "pipeline.json")))
    stage = "input_verification"
    try:
        with _termination_cleanup():
            _verify_inputs(output, plan)
            for arm in ARMS:
                writer._path(plan["reports"][arm]["adapter_dir"], fresh=True)
                writer._path(plan["reports"][arm]["trainer_log"], fresh=True)
            for arm in ARMS:
                stage = arm + "_train"
                _verify_inputs(output, plan)
                command = writer._read(output / "preparations" / arm / "training_command.json")
                run_training(command, device=plan["devices"][arm], popen=popen, occupancy=occupancy)
                training[arm] = _training_result(plan["reports"][arm])
                _write(output / (arm + "_TRAIN_DONE.json"), training[arm])
            for arm in ARMS:
                stage = arm + "_probe"
                _verify_inputs(output, plan)
                _require(_training_result(plan["reports"][arm]) == training[arm], "adapter changed after training")
                device = plan["devices"][arm]
                _require(occupancy(device) is True, "GPU not released before probe")
                spec = _probe_spec(output, plan, arm, training[arm])
                spec_path = output / (arm + "_probe_spec.json")
                _write(spec_path, spec)
                digest = writer._hash(spec_path)
                with _execution_environment(plan["model_path"], device):
                    receipts = neutral.run_pair(spec_path, digest, allow_gpu=True)
                _require(occupancy(device) is True, "GPU not released after probe")
                originals[arm] = (spec_path, digest, receipts)
                probes[arm] = _probe_results(spec_path, digest, receipts, plan["source_snapshot"])
            stage = "final_revalidation"
            _verify_inputs(output, plan)
            for arm in ARMS:
                _require(_training_result(plan["reports"][arm]) == training[arm], "trained adapter changed")
                probes[arm] = _probe_results(*originals[arm], plan["source_snapshot"])
            result = dict(**BOUNDARY, status="COMPLETE", training=training, probes=probes,
                          episode_ids=plan["episode_ids"], limits=plan["probe_limits"])
            _write(output / "results.json", result)
            return result
    except BaseException as error:
        _write(output / "PARTIAL.json", dict(**BOUNDARY, status="INCOMPLETE", stage=stage,
            error_type=type(error).__name__, error=str(error), validated_training=training,
            validated_probes=probes, cleanup_evidence="inspect logs/*.cleanup.json and probes/*/*.cleanup.json",
            reservation_release_verified=False, retry_policy="no retry or output reuse"))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    prepare = subparsers.add_parser("prepare")
    for name in ("pair-root", "lesson-out", "sham-out", "out", "lesson-device", "sham-device"):
        prepare.add_argument("--" + name, required=True)
    execute = subparsers.add_parser("execute")
    execute.add_argument("--out", required=True)
    execute.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "prepare":
        result = prepare_pipeline(args.pair_root, args.lesson_out, args.sham_out, args.out,
            devices=dict(lesson=args.lesson_device, sham=args.sham_device))
    else:
        result = execute_pipeline(args.out, allow_gpu=args.allow_gpu)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
