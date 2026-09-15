"""Separate evaluation-only reference for the canonical initial adapter."""

import argparse
from dataclasses import asdict
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


MAX_CALLS = 72
MAX_NEW_TOKENS = 512
GROUPS = tuple(range(1, 7))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    hashed = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hashed.update(block)
    return hashed.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def checked(reference):
    path = Path(reference["path"])
    require(path.is_absolute() and sha(path) == reference["sha256"], "exact_input_reference")
    return read(path)


def validate_plan(plan, clock=time.time):
    require(plan["schema"] == "R118_FROZEN_SEED_REFERENCE_V1", "reference_schema")
    require(plan["cycles"] == list(GROUPS), "exact_original_six_groups")
    require(plan["max_native_calls"] == MAX_CALLS and plan["max_new_tokens"] == MAX_NEW_TOKENS,
            "fixed_new_reference_budget")
    require(plan["context_limit"] == 8192 and plan["optimizer_steps"] == 0
            and plan["parent_calls"] == 0 and plan["retries"] == 0, "evaluation_only_contract")
    require(clock() < plan["deadline_unix"] <= plan["lease_end_unix"] - 21600
            and 0 < plan["deadline_unix"] - plan["started_unix"] <= 3600, "bounded_reference_wall")
    require(Path(plan["output_root"]).is_absolute() and Path(plan["canonical_root"]).is_absolute(),
            "absolute_reference_roots")
    output, original = Path(plan["output_root"]).resolve(), Path(plan["canonical_root"]).resolve()
    require(output.is_absolute() and original.is_absolute()
            and not output.is_relative_to(original) and not original.is_relative_to(output),
            "separate_reference_and_historical_roots")
    require(str(plan["gpu_uuid"]).startswith("GPU-"), "explicit_device_uuid")
    require(Path(plan["model_dir"]).is_absolute(), "explicit_local_model")
    feasibility = checked(plan["feasibility"])
    require(feasibility["canonical_root"] == str(original), "exact_canonical_root")
    require([group["cycle"] for group in feasibility["task_source"]] == list(GROUPS), "original_task_selectors")
    require(all(group["cohort_selector"] == f'held[{group["cycle"]}]'
                and len(group["task_hashes"]) == 2 for group in feasibility["task_source"]),
            "two_original_tasks_per_group")
    require(plan["initial_state_sha256"] == feasibility["initial_adapter"]["state_sha256"],
            "seed_matched_frozen_adapter_not_bare_BASE")
    source_root = Path(plan["source_root"])
    require(source_root.is_absolute() and bool(plan["source_files"]), "frozen_source_closure_required")
    require(plan["source_files"].get("gpu/orch_r118_frozen_seed_reference.py") == sha(__file__),
            "reference_entrypoint_pinned")
    for name, expected in plan["source_files"].items():
        path = (source_root / name).resolve()
        require(path.is_relative_to(source_root.resolve()) and sha(path) == expected, "source_closure_drift")
    for name, expected in feasibility["historical_source_hashes"].items():
        require(plan["source_files"].get(name) == expected, "historical_decoder_gym_source_drift")
    prepared = checked(feasibility["prepare"])
    checked(feasibility["cohort"])
    require(sha(feasibility["source_store_file"]["path"]) == feasibility["source_store_file"]["sha256"],
            "original_event_store_unchanged")
    require(prepared["initial"]["state_sha256"] == plan["initial_state_sha256"], "historical_initial_identity")
    for reference in feasibility["initial_adapter"]["files"]:
        require(sha(reference["path"]) == reference["expected_sha256"], "initial_adapter_file_drift")
    return feasibility, prepared


def reserve(root, cycle, metadata, clock=time.time):
    root = Path(root)
    require(cycle in GROUPS, "original_group_only")
    with (root / "BUDGET.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        folder = root / "claims"
        folder.mkdir(exist_ok=True)
        claims = sorted(folder.glob("CALL_*.json"))
        require(len(claims) < MAX_CALLS, "reference_call_budget_exhausted")
        number = len(claims) + 1
        require([path.name for path in claims] == [f"CALL_{index:04d}.json" for index in range(1, number)],
                "contiguous_preserved_claims")
        path = folder / f"CALL_{number:04d}.json"
        write_new(path, dict(number=number, cycle=cycle, metadata=metadata, status="CHARGED",
                             started_unix=clock(), parent_present=False, training_allowed=False))
    return number, path


def run_episodes(worlds, task_builder, episode, generate, store, expected_hashes, digest, on_record=None):
    tasks = [(world, task) for world in worlds for task in task_builder(world)]
    require(len(tasks) == 2 and [digest(task) for unused, task in tasks] == expected_hashes,
            "exact_original_task_order")
    records = []
    for world, task in tasks:
        record = episode(world, task, generate, store, parent=None, rich_contract=False)
        require(record["task"] == task and not record.get("parent_messages"), "parent_absent_original_task")
        records.append(record)
        if on_record is not None:
            on_record(len(records), record)
    return records


def group(plan_path, cycle):
    plan = read(plan_path)
    feasibility, prepared = validate_plan(plan)
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"], "exact_CVD")
    require(os.environ.get("HF_HUB_OFFLINE") == os.environ.get("TRANSFORMERS_OFFLINE") == "1", "offline_only")
    require(cycle in GROUPS, "original_group_only")
    root = Path(plan["output_root"])
    output = root / f"group_{cycle:02d}"
    output.mkdir(exist_ok=False)
    from gpu import orch_guided_native as native
    from gpu import orch_route_parent_campaign_canonical as canonical
    from organism_v6 import orch_guided_bridge as bridge
    canonical.configure()
    run = canonical.run
    require(Path(run.__file__).resolve().is_relative_to(Path(plan["source_root"]).resolve()), "frozen_runtime_import")
    identity = bridge.AdapterIdentity.from_document(prepared["initial"])
    predecessor = tuple(read(root / "SUPERVISOR.json")["process"])
    binding = bridge.StageBinding(root.name, bridge.ARMS[1], cycle, "sealed_readout", identity,
                                   False, True, sha(plan_path))
    write_new(output / "BINDING.json", asdict(binding))

    def check(phase):
        require(time.time() < plan["deadline_unix"], "reference_deadline:" + phase)

    try:
        loaded = native.load_stage(binding, model_dir=plan["model_dir"], device="cuda:0",
            gpu_uuid=plan["gpu_uuid"], context=native.StageContext(), check=check,
            predecessor_processes=(predecessor,), engine_factory=run.Engine)
        require(loaded.optimizer is None and loaded.observed == identity, "frozen_exact_initial_adapter")
        write_new(output / "LOADED.json", dict(process=loaded.process, observed=loaded.observed.document(),
                    runtime=loaded.engine.runtime, parent_present=False, optimizer_steps=0))

        def generate(messages, **metadata):
            check("dispatch")
            number, claim = reserve(root, cycle, metadata)
            result = dict(number=number, messages=messages, metadata=metadata,
                          claim_sha256=sha(claim), started_unix=time.time())
            try:
                result["response"] = loaded.engine.generate(messages, max_new_tokens=MAX_NEW_TOKENS)
                result["response"]["generated_text_tokens"] = len(result["response"]["token_ids"]) - int(
                    result["response"]["terminal"])
                result["status"] = "COMPLETE"
                return result["response"]
            except BaseException as error:
                result.update(status="FAILED", error_type=type(error).__name__)
                raise
            finally:
                result["finished_unix"] = time.time()
                write_new(output / f"CALL_{number:04d}.json", result)

        cohort = checked(feasibility["cohort"])
        store = run.source_store(Path(plan["canonical_root"]), cohort)
        records = run_episodes(cohort["held"][cycle], run.shared_run.shared.tasks, run.guided.episode,
            generate, store, feasibility["task_source"][cycle - 1]["task_hashes"], run.digest,
            on_record=lambda index, record: write_new(output / f"EPISODE_{index:02d}.json", record))
        loaded.verify_unchanged()
        write_new(output / "COMPLETE.json", dict(status="COMPLETE", cycle=cycle, episodes=len(records),
            correct=sum(record["correct"] for record in records), process=loaded.process,
            input_adapter=identity.document(), output_adapter=loaded.observed.document(),
            parent_present=False, fresh_process=True, optimizer_steps=0, training_rows=0,
            finished_unix=time.time(), semantic_improvement="UNASSESSED"))
    except BaseException as error:
        write_new(output / "FAILED.json", dict(status="FAILED", cycle=cycle,
                  error_type=type(error).__name__, finished_unix=time.time(), retries=0))
        raise


def supervise(plan_path):
    plan = read(plan_path)
    validate_plan(plan)
    from gpu import orch_guided_native as native
    root = Path(plan["output_root"])
    root.mkdir(parents=True, exist_ok=False)
    write_new(root / "SUPERVISOR.json", dict(process=native.process_identity(), plan_sha256=sha(plan_path),
               started_unix=time.time(), allocation_and_strict_admission_external=True))
    results = []
    for cycle in GROUPS:
        if time.time() >= plan["deadline_unix"]:
            break
        with (root / f"group_{cycle:02d}.log").open("x") as stream:
            command = [sys.executable, "-B", str(Path(__file__).resolve()), "group", "--plan", str(plan_path),
                       "--cycle", str(cycle)]
            child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL, start_new_session=True)
            timed_out = False
            try:
                child.wait(timeout=max(0.001, plan["deadline_unix"] - time.time()))
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait()
            results.append(dict(cycle=cycle, pid=child.pid, returncode=child.returncode, timed_out=timed_out,
                                complete=(root / f"group_{cycle:02d}" / "COMPLETE.json").exists()))
    write_new(root / "TERMINAL.json", dict(status="COMPLETE" if len(results) == 6 and all(
        item["complete"] and item["returncode"] == 0 for item in results) else "INCOMPLETE",
        groups=results, finished_unix=time.time(), retries=0, optimizer_steps=0, parent_calls=0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", choices=("validate", "group", "supervise"))
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--cycle", type=int, choices=GROUPS)
    args = parser.parse_args()
    if args.entry == "validate":
        validate_plan(read(args.plan))
        print(json.dumps(dict(status="CPU_METADATA_VALID", GPU_launched=False)))
    elif args.entry == "group":
        require(args.cycle is not None, "explicit_group_required")
        group(args.plan, args.cycle)
    else:
        supervise(args.plan)


if __name__ == "__main__":
    main()
