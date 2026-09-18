"""R233 four-life retirement using existing identity and COMPLETE primitives."""

import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import select
import signal
import subprocess
import time


TARGETS = {
    "C1": (0, 2707975, "22260069", "orch_r181_node5_c1_1789683715568589680"),
    "C3": (3, 2668022, "22198740", "orch_r181_node5_c3_1789683881443707769"),
    "C4": (4, 2606742, "22116734", "orch_r181_node5_c4_1789683881443639417"),
    "C5": (5, 2761060, "22343823", "orch_r181_node5_c5_1789683715577507372"),
}
BASE = Path("/localhome/local-rohing")
SAVED_SHA = "7e0fcf8c35b72fc6fa01738446d51d8fe9e996afefae66236dd2d5c47d6a2419"
OPERATOR_SHAS = {
    "C1": "6c0f5ea6f718a77e9ab6333a39c69c4182473e3ef980d1874ff94742914def72",
    "C3": "1719634ae80de311fdcae7b04c812b0c23b4f3308ddf75fff7608fff7868dbfa",
    "C4": "1719634ae80de311fdcae7b04c812b0c23b4f3308ddf75fff7608fff7868dbfa",
    "C5": "6c0f5ea6f718a77e9ab6333a39c69c4182473e3ef980d1874ff94742914def72",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(path, value):
    with Path(path).open("x") as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        os.fchmod(handle.fileno(), 0o400)


def load_module(name, path, expected_sha):
    require(sha(path) == expected_sha, "existing_helper_hash_changed")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_scope(label, plan, actor):
    require(label in TARGETS, "only_explicit_C1_C3_C4_C5")
    physical, process_id, ticks, control_name = TARGETS[label]
    root = BASE / ("orch_r153_community_" + label + "_20260916_attempt1/life")
    require(plan["root"] == str(root) and plan["physical"] == physical, "exact_legacy_life_and_device")
    require(plan["source_root"] == str(BASE / control_name / "source"), "exact_legacy_source")
    require(actor["pid"] == process_id and actor["start_ticks"] == ticks and actor["uid"] == 2524,
            "exact_native_pid_startticks_owner")
    require(root.resolve() == root and not root.is_symlink(), "no_storage_alias")
    return root


def validate_checkpoint(saved, root, boundary):
    import torch

    document = boundary["record"]["document"]
    directory = root / "checkpoints" / ("sleep_%06d" % boundary["cycle"])
    checkpoint = read(directory / "COMMIT.json")
    require(checkpoint == document["checkpoint"], "journal_COMMIT_exact")
    adapter = directory / "adapter"
    optimizer = directory / "optimizer_rng.pt"
    require(checkpoint["adapter_path"] == str(adapter) and checkpoint["optimizer_rng_path"] == str(optimizer),
            "checkpoint_paths_under_exact_life")
    files = {path.name: sha(path) for path in sorted(adapter.iterdir()) if path.is_file()}
    require(files == checkpoint["adapter_files"], "all_adapter_files_match")
    require(saved.digest(files) == checkpoint["checkpoint_sha256"]["adapter"], "adapter_manifest_digest")
    require(sha(optimizer) == checkpoint["checkpoint_sha256"]["optimizer"]
            == checkpoint["checkpoint_sha256"]["rng"], "optimizer_rng_file_binding")
    require(saved.digest(checkpoint["checkpoint_sha256"])
            == document["resume_state"]["state"]["model_state_sha256"], "model_history_binding")
    payload = torch.load(optimizer, map_location="cpu", weights_only=False)
    require(payload["optimizer_steps"] == checkpoint["optimizer_steps"] > 0,
            "optimizer_steps_match")
    require(payload["optimizer"]["state"] and payload["optimizer"]["param_groups"]
            and payload["parameter_names"], "AdamW_state_and_parameter_names_present")
    require(len(payload["cuda_rng"]) == 1 and payload["cuda_rng"][0].device.type == "cpu",
            "single_device_saved_rng")
    torch.Generator(device="cpu").set_state(payload["cpu_rng"])
    random.Random().setstate(payload["python_rng"])
    require(not torch.cuda.is_initialized(), "validation_CPU_only")
    return dict(cycle=boundary["cycle"], checkpoint_commit_sha256=sha(directory / "COMMIT.json"),
                adapter_state_sha256=checkpoint["adapter_state_sha256"],
                optimizer_steps=checkpoint["optimizer_steps"],
                checkpoint_sha256=checkpoint["checkpoint_sha256"], state_sha256=boundary["state_sha256"],
                AdamW_CPU_deserialization_passed=True, saved_rng_CPU_validation_passed=True)


def preserve(saved, root, boundary, output):
    snapshot = output / "snapshot"
    snapshot.mkdir(mode=0o700)
    checkpoint = root / "checkpoints" / ("sleep_%06d" % boundary["cycle"])
    subprocess.run(["cp", "-a", "--reflink=auto", str(checkpoint), str(snapshot / "checkpoint")], check=True)
    subprocess.run(["cp", "-a", "--reflink=auto", str(root / "stream"), str(snapshot / "stream")], check=True)
    saved.verify_snapshot(snapshot / "stream", root, boundary)
    manifests = {}
    for kind in ("checkpoint", "stream"):
        directory = snapshot / kind
        files = {}
        for path in sorted(directory.rglob("*")):
            require(not path.is_symlink(), "snapshot_has_no_symlinks")
            if path.is_file():
                files[str(path.relative_to(directory))] = dict(sha256=sha(path), bytes=path.stat().st_size)
        write(output / (kind.upper() + "_MANIFEST.json"), files)
        manifests[kind] = dict(path=str(directory), file_count=len(files),
                               manifest_sha256=sha(output / (kind.upper() + "_MANIFEST.json")))
    for path in sorted(snapshot.rglob("*"), reverse=True):
        path.chmod(0o500 if path.is_dir() else 0o400)
    snapshot.chmod(0o500)
    return manifests


def retire(label, output, wait_seconds):
    require(label in TARGETS, "explicit_allowlist_before_any_action")
    control = BASE / TARGETS[label][3]
    saved = load_module("_r233_saved", control / "saved_primitives.py", SAVED_SHA)
    operator = load_module("_r233_existing_operator", control / "rollout_operator.py", OPERATOR_SHAS[label])
    guard_path = control / "GUARD.json"
    guard = read(guard_path)
    plan = read(guard["plan_path"])
    require(sha(guard["plan_path"]) == guard["plan_sha256"], "original_plan_pin")
    actor = saved.identity(TARGETS[label][1])
    root = validate_scope(label, plan, actor)
    request = dict(label=label, identity=actor, config_ref=saved.reference(guard_path),
                   plan_ref=saved.reference(guard["plan_path"]))
    pair = operator.owner_pair(saved, request, guard, plan)
    require(output.parent.name == "orch_r233_focus_node5_20260918" and output.name == label,
            "only_new_R233_receipt_directory")
    output.mkdir(mode=0o700)
    write(output / "IDENTITY.json", dict(observed_utc=utc(), pair=pair, request=request,
                                         helper_sha256=SAVED_SHA, operator_sha256=sha(Path(__file__))))
    descriptors = {role: os.pidfd_open(identity["pid"]) for role, identity in pair.items()}
    terminated = False
    try:
        for identity in pair.values():
            saved.same(identity)
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            saved.same(actor)
            boundary = saved.saved_boundary(root)
            metadata = saved.readout(root, guard, plan, boundary, actor) if boundary else None
            if boundary and metadata:
                with saved.pause_watchdog(descriptors["actor"], 360) as pause_deadline:
                    saved.pause_exact(actor, descriptors["actor"])
                    if saved.saved_boundary(root) != boundary:
                        continue
                    completion = saved.wait_readout(metadata, pause_deadline - 180)
                    saved.check_children(pair)
                    proof = validate_checkpoint(saved, root, boundary)
                    manifests = preserve(saved, root, boundary, output)
                    require(saved.saved_boundary(root) == boundary, "same_COMPLETE_after_preservation")
                    require(time.monotonic() + 60 < pause_deadline, "watchdog_budget_before_retirement")
                    ready = dict(observed_utc=utc(), boundary=saved.reference(boundary["reference"]["path"]),
                                 proof=proof, preservation=manifests, readout_complete=completion,
                                 pending=None, all_rows_at_sleep_frontier=True,
                                 no_checkpoint_rollback=True, original_files_deleted=0,
                                 saved_checkpoint_rng_not_post_checkpoint_resident_rng_claim=True)
                    write(output / "PRESERVED.json", ready)
                    require(operator.owner_pair(saved, request, guard, plan) == pair, "same_owned_tree_before_TERM")
                    require(saved.saved_boundary(root) == boundary, "same_COMPLETE_before_TERM")
                    write(output / "TERMINATION_INTENT.json", dict(observed_utc=utc(), target=actor,
                                                                  boundary_index=boundary["index"], signal="SIGTERM"))
                    signal.pidfd_send_signal(descriptors["actor"], signal.SIGTERM)
                    terminated = True
                    signal.pidfd_send_signal(descriptors["actor"], signal.SIGCONT)
                    exited = {}
                    for role in ("actor", "timer", "supervisor"):
                        exited[role] = bool(select.select([descriptors[role]], [], [], 30)[0])
                        require(exited[role], "owned_exit_" + role)
                    require(saved.saved_boundary(root) == boundary, "no_unsaved_suffix_after_exit")
                    write(output / "RETIRED.json", dict(schema="R233_EXACT_COMPLETE_RETIREMENT_V1",
                        label=label, retired_utc=utc(), native_pid=actor["pid"], start_ticks=actor["start_ticks"],
                        root=str(root), boundary_index=boundary["index"], proof=proof, preservation=manifests,
                        exited=exited, signals_only_exact_native_pidfd=True, scored_readout_signals=0,
                        C2_signals=0, protected_services_changed=False, new_birth=False, deleted_files=0))
                    return
            time.sleep(0.25)
        raise TimeoutError("no_COMPLETE_readout_window_before_deadline_original_left_running")
    except BaseException as error:
        write(output / "ERROR.json", dict(observed_utc=utc(), error_type=type(error).__name__,
                                         reason=str(error), termination_sent=terminated))
        raise
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label", choices=tuple(TARGETS))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wait-seconds", type=int, default=2400)
    args = parser.parse_args()
    retire(args.label, args.output, args.wait_seconds)


if __name__ == "__main__":
    main()
