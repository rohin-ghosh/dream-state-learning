"""Exact-source A100 R179 staging and same-boundary handoffs; never replay."""

import argparse
import ast
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid


HERE = Path(__file__).resolve().parent
BASE_SHA = "6e4d91c9581d952924ae269d7f4831fc9840c741805ebcddf2f2c78e8d356270"
POLICY_SHA = "b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b"
SCOPE_SHA = "85441db890036947f6bc242e66ef15db750a683d73fe02d06778ebe996d4fb54"
MAIN_CPU_SHA = "be9ff6c0cbad47c6e8e5a449aa711cfdf4a6b6c31c8d462941c2cdb4104685eb"
NATIVE = "gpu/orch_r125_continual_native.py"
POLICY = "gpu/orch_r179_context_survival.py"
REMOTE = Path("/localhome/local-rohing/orch_r181_node1_20260917")
CANONICAL_SHA = "0d78d1b04ff7401dc3c56c4894b615ff5b148960391819fba332167d8c0b77f8"
PYTHON = "/localhome/local-rohing/v2/venv/bin/python"
SOURCE_CAP = 64 * 1024 * 1024
HISTORY_CAP = 4 * 1024 * 1024 * 1024
CHECKPOINT_CAP = 2 * 1024 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read(path, cap=64 * 1024 * 1024):
    path = Path(path)
    require(path.resolve() == path and not path.is_symlink(), "canonical_JSON_path")
    require(path.stat().st_size <= cap, "bounded_JSON_before_read")
    with path.open("rb") as stream:
        data = stream.read(cap + 1)
    require(len(data) <= cap, "bounded_JSON_after_read")
    return json.loads(data)


def write(path, document):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(document, stream, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def module(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(loaded)
    return loaded


def legacy():
    path = HERE / "r144_base.py"
    if not path.exists():
        path = HERE.parents[3] / "gpu/orch_r144_a100_a40r_target_rollout.py"
    require(sha(path) == BASE_SHA, "exact_tested_A100_base_machinery")
    return module(path, "r179_exact_a100_base")


def authorize():
    require(HERE == REMOTE / "operator" and os.getuid() == 1395
            and os.environ.get("CUDA_VISIBLE_DEVICES") == "", "A100_CPU_operator_namespace")
    bindings = read(HERE / "R181_BINDINGS.json")
    for name, expected in bindings["operator_files"].items():
        require(Path(name).name == name and sha(HERE / name) == expected, "bound_existing_handoff_source:" + name)
    require(sha(HERE / "canonical_native.py") == CANONICAL_SHA, "Main_exact_R181_native")
    base = legacy()
    base.current_node("a100")
    return base


def source_inventory(root):
    root = Path(root)
    require(root.is_absolute() and root.resolve() == root, "canonical_source")
    paths = sorted(root.rglob("*"))
    total = 0
    inventory = {}
    for path in paths:
        metadata = path.lstat()
        require(stat.S_ISDIR(metadata.st_mode) or stat.S_ISREG(metadata.st_mode), "no_source_links_or_special_files")
        if path.is_file():
            total += metadata.st_size
            require(total <= SOURCE_CAP, "source_byte_reservation")
            inventory[str(path.relative_to(root))] = dict(size=metadata.st_size,
                mode=stat.S_IMODE(metadata.st_mode), device=metadata.st_dev, inode=metadata.st_ino)
    for relative, metadata in inventory.items():
        if relative.endswith(".py"):
            metadata["sha256"] = sha(root / relative)
    return inventory


def source_pins(inventory):
    return {relative: metadata["sha256"] for relative, metadata in inventory.items()
            if relative.endswith(".py")}


def copy_source(original, destination, inventory, patched):
    require(not destination.exists(), "new_source_only")
    destination.mkdir()
    for directory in original.rglob("*"):
        if directory.is_dir():
            (destination / directory.relative_to(original)).mkdir(parents=True, exist_ok=True)
    for relative, metadata in inventory.items():
        old_path, new_path = original / relative, destination / relative
        new_path.parent.mkdir(parents=True, exist_ok=True)
        if relative.endswith(".py"):
            if relative == NATIVE:
                new_path.write_text(patched)
            else:
                shutil.copyfile(old_path, new_path)
            new_path.chmod(0o444)
        else:
            os.link(old_path, new_path, follow_symlinks=False)
    for path in sorted(destination.rglob("*"), reverse=True):
        if path.is_dir():
            path.chmod(0o555)
    destination.chmod(0o555)


def verify_source_copy(original, copied, before, after):
    require(set(after) == set(before), "same_source_closure_only_native_delta")
    for relative, metadata in before.items():
        candidate = after[relative]
        if relative.endswith(".py") and relative != NATIVE:
            require(candidate["sha256"] == metadata["sha256"], "unchanged_Python_closure")
        elif not relative.endswith(".py"):
            require(candidate == metadata, "opaque_noncode_same_inode_size_mode")
    if POLICY in before:
        require(after[POLICY]["sha256"] == before[POLICY]["sha256"], "R179_policy_unchanged")
    require(source_inventory(original) == before, "original_source_unchanged")


def environment(source):
    require(not any(name in os.environ for name in ("PYTORCH_CUDA_ALLOC_CONF", "PYTORCH_ALLOC_CONF")),
            "no_new_allocator_environment")
    return dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(source))


def bound_life(physical):
    require(physical in range(2, 8), "six_learners_no_controls")
    row = next(row for row in read(HERE / "R181_BINDINGS.json")["rows"] if row["physical"] == physical)
    actor = legacy().identity(row["pid"])
    require(str(actor["start_ticks"]) == str(row["start_ticks"]), "same_current_R179_or_support_actor")
    return dict(physical=physical, life_root=row["root"], source_root=row["source_root"], original_actor=actor,
                original_guard=dict(path=row["guard_path"], sha256=row["guard_sha256"]),
                original_plan=dict(path=row["plan_path"], sha256=row["plan_sha256"]))


def original_binding(base, physical):
    life = bound_life(physical)
    config_path = Path(life["original_guard"]["path"])
    require(sha(config_path) == life["original_guard"]["sha256"]
            and sha(life["original_plan"]["path"]) == life["original_plan"]["sha256"], "original_plan_guard_pins")
    config, plan, imported = base.originals(config_path)
    base.check_scope("a100", config, plan)
    require(plan["root"] == life["life_root"] and plan["source_root"] == life["source_root"], "same_saved_life_source")
    pair = base.process_pair(life["original_actor"]["pid"], "a100", config_path, config, plan)
    require(all(pair["actor"][key] == life["original_actor"][key]
                for key in ("pid", "start_ticks", "uid", "boot_id")), "live_original_actor")
    device = base.actual_device(plan)
    require(config["device_containment"]["minor"] == device["minor"], "existing_strict_device_minor")
    return life, config, plan, imported, pair, device


def stage(physical):
    base = authorize()
    life, config, plan, imported, pair, device = original_binding(base, physical)
    output = REMOTE / "lanes" / ("lane" + str(physical))
    require(not output.exists(), "never_overwrite_prior_stage")
    output.mkdir(parents=True)
    source = Path(plan["source_root"])
    before = source_inventory(source)
    require(source_pins(before) == config["source_pins"], "actual_original_entire_python_closure")
    delta = module(HERE / "r181_native_delta.py", "r181_exact_native_delta")
    original_text = (source / NATIVE).read_text()
    entry = base.verify_resume_entrypoint(source)
    patched = delta.patch(original_text, (HERE / "canonical_native.py").read_text())
    successor = output / "source"
    copy_source(source, successor, before, patched)
    after = source_inventory(successor)
    verify_source_copy(source, successor, before, after)
    proof = dict(original_source=str(source), successor_source=str(successor), before=before, after=after,
                 policy_sha256=POLICY_SHA, noncode_content_read=False, source_cap_bytes=SOURCE_CAP)
    write(output / "SOURCE_PROOF.json", proof)
    control = output / "control"
    control.mkdir()
    proposed = base.relocated_plan(plan, successor)
    proposed["rehearsal_presentations"] = 0
    write(control / "PLAN.json", proposed)
    allocation = read(config["allocation_path"])
    require(allocation["plan_sha256"] == config["plan_sha256"], "existing_allocation_binding")
    allocation.update(plan_sha256=sha(control / "PLAN.json"), r181_native_sha256=CANONICAL_SHA)
    write(control / "ALLOCATION.json", allocation)
    updated = deepcopy(config)
    updated.update(attempt_dir=str(control), resume=True, plan_path=str(control / "PLAN.json"),
        plan_sha256=sha(control / "PLAN.json"), allocation_path=str(control / "ALLOCATION.json"),
        allocation_sha256=sha(control / "ALLOCATION.json"), source_pins=source_pins(after))
    updated["device_containment"]["unit"] = "orch-r136-native-" + uuid.uuid4().hex
    write(control / "GUARD.json", updated)
    subprocess.run([PYTHON, "-B", "-c", "from gpu.orch_r125_continual_guard import validate;import sys;validate(sys.argv[1])",
                    str(control / "GUARD.json")], cwd=successor, env=environment(successor), check=True, timeout=120)
    receiving = subprocess.run([PYTHON, "-B", str(HERE / "receiving_cpu.py"), str(successor), str(output)],
        cwd=successor, env=environment(successor), text=True, capture_output=True, timeout=120)
    require(receiving.returncode == 0, "actual_receiving_CPU_failed:" + receiving.stderr[-2000:])
    cpu = json.loads(receiving.stdout)
    require(cpu["passed"] >= 3 and cpu["cuda_initialized"] is False
            and cpu["native_sha256"] == after[NATIVE]["sha256"], "receiving_actual_staged_source")
    write(output / "RECEIVING_CPU.json", cpu)
    require(base.verify_resume_entrypoint(successor) == entry, "unchanged_guard_resume_entrypoint")
    request = dict(status="STAGED_RECEIVING_CPU_PASS", physical=physical, node="a100",
        original_guard=life["original_guard"], original_plan=life["original_plan"], processes=pair,
        device=device, original_source=str(source), source_root=str(successor),
        new_config=str(control / "GUARD.json"), new_config_sha256=sha(control / "GUARD.json"),
        source_proof_sha256=sha(output / "SOURCE_PROOF.json"), receiving_cpu_sha256=sha(output / "RECEIVING_CPU.json"),
        operator_sha256=sha(Path(__file__)), scope_sha256=SCOPE_SHA, entrypoint=entry,
        handler=base.launcher("a100", config), old_plan=plan, staged_unix=time.time())
    write(output / "STAGED.json", request)
    return dict(status=request["status"], physical=physical, output=str(output),
                receiving_cpu_sha256=request["receiving_cpu_sha256"], signals_sent=0)


def watchdog(actor_fd, pipe_fd, seconds):
    ready = select.select([pipe_fd], [], [], seconds)[0]
    if not ready or os.read(pipe_fd, 1) != b"D":
        try:
            signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
        except ProcessLookupError:
            pass


@contextmanager
def pause_watchdog(actor_fd, seconds):
    reader, writer = os.pipe()
    process = subprocess.Popen([PYTHON, "-B", str(Path(__file__)), "watchdog", "--actor-fd", str(actor_fd),
        "--pipe-fd", str(reader), "--seconds", str(seconds)], pass_fds=(actor_fd, reader),
        start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.close(reader)
    try:
        yield time.monotonic() + seconds
    finally:
        try:
            signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
        except ProcessLookupError:
            pass
        try:
            os.write(writer, b"D")
        except BrokenPipeError:
            pass
        os.close(writer)
        process.wait(timeout=5)


def reserve_tree(root, cap):
    total = 0
    for path in Path(root).rglob("*"):
        metadata = path.lstat()
        require(stat.S_ISREG(metadata.st_mode) or stat.S_ISDIR(metadata.st_mode), "opaque_copy_regular_tree")
        if stat.S_ISREG(metadata.st_mode):
            total += metadata.st_size
            require(total <= cap, "precharged_preservation_cap")
    return total


def readout_ready(base, plan, config, saved, actor, native):
    directory = Path(plan["root"]) / "readouts" / native.readout_name(plan, saved["cycle"])
    path = directory / "REQUEST.json"
    if not path.exists():
        return None
    request = read(path, 1024 * 1024)
    checkpoint = Path(plan["root"]) / "checkpoints" / ("sleep_%06d" % saved["cycle"]) / "COMMIT.json"
    require(request["ppid"] == actor["pid"] and request["plan_path"] == config["plan_path"]
            and request["plan_sha256"] == config["plan_sha256"] and request["gpu_uuid"] == plan["gpu_uuid"]
            and request["checkpoint_path"] == str(checkpoint)
            and request["checkpoint_commit_sha256"] == sha(checkpoint), "exact_started_readout_boundary_metadata")
    try:
        child = base.identity(request["pid"])
    except (FileNotFoundError, ProcessLookupError, ValueError):
        require((directory / "COMPLETE.json").exists(), "readout_missing_without_completion")
        child = None
    if child is not None:
        require(child["parent"] == actor["pid"] and child["group"] == child["pid"]
                and child["group"] != actor["group"] and child["cgroup"] == actor["cgroup"]
                and child["argv"] == [PYTHON, "-B", "-m", "gpu.orch_r125_continual_readout",
                    "--plan", config["plan_path"], "--checkpoint", str(checkpoint), "--output", str(directory)],
                "actual_independent_readout_child_started")
    return dict(request_sha256=sha(path), child=child, offload_and_spawn_completed=True)


def handoff(physical, seconds):
    base = authorize()
    require(physical in range(2, 8) and 1 <= seconds <= 14400, "six_learning_lives_current_wall_bounded_wait")
    output = REMOTE / "lanes" / ("lane" + str(physical))
    request = read(output / "STAGED.json")
    require(request["operator_sha256"] == sha(Path(__file__))
            and request["scope_sha256"] == SCOPE_SHA
            and request["receiving_cpu_sha256"] == sha(output / "RECEIVING_CPU.json")
            and request["new_config_sha256"] == sha(request["new_config"]), "bound_staged_successor_before_pause")
    life, config, plan, original, pair, device = original_binding(base, physical)
    require(pair == request["processes"] and device == request["device"], "same_staged_live_ownership_device")
    proof = read(output / "SOURCE_PROOF.json")
    require(sha(output / "SOURCE_PROOF.json") == request["source_proof_sha256"], "pinned_source_proof")
    require(source_inventory(proof["original_source"]) == proof["before"]
            and source_inventory(proof["successor_source"]) == proof["after"], "immutable_source_closures_before_pause")
    require(base.verify_resume_entrypoint(request["source_root"]) == request["entrypoint"], "normal_saved_resume_only")
    lock = os.open(REMOTE / ("lane" + str(physical) + ".lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    descriptors = {}
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (output / "HANDOFF_ONCE").mkdir()
        for role, expected in pair.items():
            require(base.identity(expected["pid"]) == expected, "exact_original_identity_before_pidfd")
            descriptors[role] = os.pidfd_open(expected["pid"])
            require(base.identity(expected["pid"]) == expected, "exact_original_identity_after_pidfd")
        deadline = min(time.monotonic() + seconds, time.monotonic() + plan["hard_end_unix"] - time.time() - 600)
        write(output / "ARMED.json", dict(operator_pid=os.getpid(), physical=physical, deadline_monotonic=deadline,
                                          signals_sent=0, observed_unix=time.time()))
        while time.monotonic() < deadline:
            saved = base.sleep_boundary(plan["root"])
            if saved is None:
                time.sleep(.2)
                continue
            dispatch = Path(plan["root"]) / "readouts" / (original.native.readout_name(plan, saved["cycle"]) + "_DISPATCH.json")
            if not dispatch.exists():
                time.sleep(.2)
                continue
            metadata = read(dispatch, 1024 * 1024)
            require(metadata["resident_pid"] == pair["actor"]["pid"] and metadata["cycle"] == saved["cycle"],
                    "owned_current_readout_dispatch")
            ready = readout_ready(base, plan, config, saved, pair["actor"], original.native)
            if ready is None:
                time.sleep(.2)
                continue
            with pause_watchdog(descriptors["actor"], 900) as pause_deadline:
                base.pause_exact(pair["actor"], descriptors["actor"])
                if base.sleep_boundary(plan["root"]) != saved:
                    continue
                drained = False
                while time.monotonic() + 120 < pause_deadline:
                    drained = base.readout_drained(plan, saved, pair["actor"]["pid"], config["plan_path"], original.native)
                    if drained:
                        break
                    time.sleep(.2)
                require(drained, "readout_drain_deadline_original_resumes")
                stream_root = Path(plan["root"]) / "stream"
                checkpoint_root = Path(plan["root"]) / "checkpoints" / ("sleep_%06d" % saved["cycle"])
                history_bytes = reserve_tree(stream_root, HISTORY_CAP)
                checkpoint_bytes = reserve_tree(checkpoint_root, CHECKPOINT_CAP)
                require(shutil.disk_usage(output).free > history_bytes + checkpoint_bytes + 512 * 1024 * 1024,
                        "preservation_disk_admission")
                evidence = base.saved_evidence(plan, saved, original)
                snapshot = output / "preserved_stream"
                shutil.copytree(stream_root, snapshot)
                base.verify_snapshot(snapshot, plan["root"], saved["state_sha256"], original)
                checkpoint_copy = output / "preserved_checkpoint"
                shutil.copytree(checkpoint_root, checkpoint_copy)
                require(base.inventory_files(checkpoint_copy) == base.inventory_files(checkpoint_root), "full_checkpoint_preserved")
                require(base.sleep_boundary(plan["root"]) == saved
                        and base.saved_evidence(plan, saved, original) == evidence, "exact_boundary_after_preservation")
                boundary_cpu = subprocess.run([PYTHON, "-B", str(HERE / "receiving_cpu.py"), request["source_root"],
                    str(output), "--boundary", saved["path"]], cwd=request["source_root"], env=environment(request["source_root"]),
                    capture_output=True, text=True, timeout=90)
                require(boundary_cpu.returncode == 0, "successor_actual_boundary_CPU_restore")
                receiving = json.loads(boundary_cpu.stdout)
                require(receiving["state_sha256"] == saved["state_sha256"] and receiving["cuda_initialized"] is False,
                        "successor_full_saved_state_bound")
                write(output / "BOUNDARY_RECEIVING_CPU.json", receiving)
                require(time.monotonic() + 45 < pause_deadline
                        and base.sleep_boundary(plan["root"]) == saved, "pre_retirement_time_and_boundary")
                for role, expected in pair.items():
                    require(base.identity(expected["pid"]) == expected, "exact_ownership_before_retirement")
                write(output / "BOUNDARY.json", dict(saved=evidence, readout=drained,
                    started_readout=ready,
                    receiving_cpu_sha256=sha(output / "BOUNDARY_RECEIVING_CPU.json"),
                    history_bytes=history_bytes, checkpoint_bytes=checkpoint_bytes, full_history_preserved=True,
                    observed_unix=time.time()))
                write(output / "RETIREMENT_STARTED.json", dict(physical=physical, observed_unix=time.time()))
                signal.pidfd_send_signal(descriptors["actor"], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors["actor"], signal.SIGCONT)
                for role in ("actor", "timer", "supervisor"):
                    require(select.select([descriptors[role]], [], [], 30)[0], "natural_owned_exit:" + role)
                require(base.sleep_boundary(plan["root"]) == saved, "no_unsaved_suffix_after_exit")
                write(output / "RETIRED.json", dict(saved=evidence, physical=physical, observed_unix=time.time()))
            command = base.launch_command(request)
            with (output / "SUCCESSOR_SUPERVISOR.log").open("xb") as log:
                process = subprocess.Popen(command, cwd=request["source_root"], env=environment(request["source_root"]),
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            write(output / "DISPATCHED.json", dict(supervisor_pid=process.pid, observed_unix=time.time(), no_retry=True))
            return observe(physical, 600)
        write(output / "NO_BOUNDARY.json", dict(original_left_running=True, observed_unix=time.time()))
        return dict(status="NO_BOUNDARY_ORIGINAL_RUNNING", physical=physical)
    except BaseException as error:
        write(output / ("FAILURE_" + str(time.time_ns()) + ".json"), dict(error_type=type(error).__name__,
              reason=str(error) if isinstance(error, ValueError) else "operator_runtime_failure",
              retired=(output / "RETIRED.json").exists(), no_retry=True, observed_unix=time.time()))
        raise
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)


def observe(physical, seconds):
    base = authorize()
    output = REMOTE / "lanes" / ("lane" + str(physical))
    request = read(output / "STAGED.json")
    boundary = read(output / "BOUNDARY.json")["saved"]
    old_record = read(boundary["record_path"])
    old_state = old_record["document"]["resume_state"]["state"]
    original_index = old_record["index"]
    deadline = time.monotonic() + seconds
    loaded = None
    while time.monotonic() < deadline:
        for path in base.records(request["old_plan"]["root"]):
            if int(path.stem) <= original_index:
                continue
            record = read(path)
            document = record["document"]
            if record["kind"] == "LOADED" and loaded is None:
                require(document["resume"] is True and document["optimizer_steps"] == boundary["optimizer_steps"]
                        and document["adapter_sha256"] == boundary["adapter_state_sha256"], "actual_saved_LOADED")
                actor = base.identity(document["pid"])
                require(actor["cwd"] == request["source_root"]
                        and actor["argv"] == [PYTHON, "-B", "-m", "gpu.orch_r125_continual_guard", "native",
                                               "--config", request["new_config"]], "actual_new_source_native")
                admission = read(output / "control/ADMISSION.json")
                containment = read(output / "control/CONTAINMENT_VERIFIED.json")
                require(admission["clear"] is True and admission["scanner_euid"] == 0
                        and not admission["blocking_reasons"] and admission["gpu"]["uuid"] == request["device"]["gpu_uuid"],
                        "unchanged_privileged_device_admission")
                denied = containment.get("denied_foreign_minors", containment.get("denied_devices"))
                require(isinstance(denied, list) and len(denied) == 7
                        and containment["policy"]["minor"] == request["device"]["minor"], "seven_foreign_device_denials")
                loaded = dict(status="R181_NEW_ONLY_SAME_BOUNDARY_LOADED", physical=physical,
                    actor_pid=actor["pid"], actor_start_ticks=actor["start_ticks"], source_root=request["source_root"],
                    record_sha256=record["sha256"], saved_cycle=boundary["cycle"], policy_sha256=POLICY_SHA,
                    adapter_state_sha256=boundary["adapter_state_sha256"], optimizer_steps=boundary["optimizer_steps"],
                    admission_sha256=sha(output / "control/ADMISSION.json"), observed_unix=time.time())
                if not (output / "LOADED_RECEIPT.json").exists():
                    write(output / "LOADED_RECEIPT.json", loaded)
            if loaded and record["kind"] == "COMMITTED":
                envelope = document["state"]
                require(envelope["sha256"] == base.digest(envelope["state"]), "actual_commit_envelope")
                state = envelope["state"]
                require(state["rows"][:len(old_state["rows"])] == old_state["rows"], "all_prior_training_rows_preserved")
                receipt = dict(loaded, status="LOADED_AND_FIRST_GENERATION_COMMITTED", first_commit_sha256=record["sha256"],
                    full_saved_history_receiving_cpu_sha256=sha(output / "BOUNDARY_RECEIVING_CPU.json"),
                    retained_sleep_observed=False, observed_unix=time.time())
                if not (output / "HANDOFF_COMPLETE.json").exists():
                    write(output / "HANDOFF_COMPLETE.json", receipt)
                return receipt
        failure = [name for name in ("FAILED.json", "EXIT.json", "SERVICE_EXIT.json")
                   if (output / "control" / name).exists()]
        require(not failure, "successor_exit_or_admission_failure_no_retry")
        time.sleep(1)
    return loaded or dict(status="NO_LOAD_WITHIN_BOUND", physical=physical)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "handoff", "observe", "watchdog"))
    parser.add_argument("--physical", type=int)
    parser.add_argument("--seconds", type=int, default=14400)
    parser.add_argument("--actor-fd", type=int)
    parser.add_argument("--pipe-fd", type=int)
    arguments = parser.parse_args()
    if arguments.action == "watchdog":
        watchdog(arguments.actor_fd, arguments.pipe_fd, arguments.seconds)
        return
    if arguments.action == "stage":
        result = stage(arguments.physical)
    elif arguments.action == "handoff":
        result = handoff(arguments.physical, arguments.seconds)
    else:
        result = observe(arguments.physical, arguments.seconds)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
