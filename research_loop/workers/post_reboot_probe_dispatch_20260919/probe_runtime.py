"""Scoped resource-scheduling repair around the byte-identical fixed-budget probe."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


MODULE = "research_loop.workers.rohin233_kept_age_probe_20260918.probe"
HARD_END = 1790791170
BOUNDARY = 1790812800
EXPECTED_BATTERY = dict(scenes=3, seeds=[23201, 23202], tokens_per_cell=1024,
    total_generated_tokens=6144, parent_tokens=0, model_updates=0,
    policy="R232_FRESH_DEVELOPMENT_FIXED_TOKENS_V1",
    game_sha256="31e3c9919524deacc1d8255caa65f5121744ef6f0465988576b2d1b7ad281274",
    panel_sha256="4adab198a81f2492fff5471d0a7a20de41c06f59c7a492d7ef35746f84d346aa",
    rule_digest="7127a82613c6c75ed561b180ad394a657acbc194cb27cca72bc3b0a686d6444a")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def inside(root, relative):
    path = root / relative
    require(not Path(relative).is_absolute() and path.resolve().is_relative_to(root.resolve()), "bound_relative_path")
    require(path.is_file() and not path.is_symlink(), "bound_regular_file")
    return path


def validate_config(config, now):
    require(config["battery"] == EXPECTED_BATTERY, "unchanged_battery_required")
    require(config["lease_end_unix"] == HARD_END and config["lease_boundary_unix"] == BOUNDARY,
        "original_lease_only")
    require(config["max_runtime_seconds"] == 2400 and now + 60 < HARD_END,
        "unexpired_finite_lease_required")
    roles = config["role_devices"]
    require(set(roles) == {"player", "judge"}, "exact_two_roles")
    physical = [row["physical"] for row in roles.values()]
    uuids = [row["uuid"] for row in roles.values()]
    require(all(type(index) is int and 0 <= index < 8 for index in physical), "physical_indices_required")
    require(len(set(physical)) == len(set(uuids)) == 2, "overlapping_devices_forbidden")
    require(set(physical) == set(config["scheduled_physical"]), "exact_scheduled_devices_no_fallback")
    require(not set(physical) & set(config["protected_physical"]), "protected_lives_or_scorers_forbidden")
    require(config["source_identity"]["absolute_sleep"] == 12
        and config["source_identity"]["journal_id"] == "038f85cbde5c4abfb749ea4d59da6897",
        "one_bound_prepared_source_only")
    source = config["source_identity"]
    identity = dict(journal_id=source["journal_id"], sleep_complete_sha256=source["sleep_complete_sha256"],
        adapter_state_sha256=source["adapter_state_sha256"], battery=EXPECTED_BATTERY)
    require(hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest() == config["job_id"],
        "canonical_idempotent_job_identity")
    return config


def load_config(path, expected_sha, now=None):
    require(sha(path) == expected_sha, "config_digest_mismatch")
    return validate_config(read(path), time.time() if now is None else now)


def verify_source_closure(root):
    source = root / "source"
    manifest = read(root / "SOURCE_MANIFEST.json")
    actual = {str(path.relative_to(source)) for path in source.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts}
    require(actual == set(manifest), "complete_frozen_source_closure_required")
    for name, expected in manifest.items():
        require(sha(inside(source, name)) == expected, "frozen_source_changed:" + name)


def verify_bundle(config):
    root = Path(config["root"])
    require(root.resolve() == root and root.parent == Path(config["worker_root"]), "disjoint_job_root_only")
    require(root.name == config["job_id"], "stable_job_root")
    for name, expected in config["input_files"].items():
        require(sha(inside(root, name)) == expected, "input_binding_changed:" + name)
    verify_source_closure(root)
    for name, expected in config["runtime_files"].items():
        require(sha(inside(root / "runtime", name)) == expected, "runtime_closure_changed:" + name)
    actual_runtime = {path.name for path in (root / "runtime").glob("*.py") if path.is_file()}
    require(actual_runtime == {name for name in config["runtime_files"] if name.endswith(".py")},
        "complete_scheduling_runtime_closure_required")
    identity = read(root / "CONDITION.json")
    provenance = read(root / "CPU_PROVENANCE.json")
    capture = read(root / "sources/CAPTURE.json")
    require(len(capture["sources"]) == 1, "single_captured_source")
    original = capture["sources"][0]
    for name, expected in config["source_identity"].items():
        require(original[name] == expected and provenance[name] == expected, "captured_provenance_join:" + name)
    require(provenance["status"] == "CPU_SOURCE_READY_NOT_LOADED", "cpu_preparation_required")
    freshness = read(root / "FRESHNESS_VERIFIED.json")
    require(freshness["eligible"] is True and freshness["source_cut_sha256"] == original["sleep_complete_sha256"],
        "eligible_exact_exposure_cut_required")
    require(identity["condition"] == config["condition"] and identity["parent_tokens"] == 0
        and identity["source_parent_text_loaded"] is False and identity["optimizer_loaded"] is False,
        "parent_free_immutable_inference_only")
    require(original["source_context_copied_or_loaded"] is False
        and original["optimizer_rng_copied_or_loaded"] is False, "source_context_not_loaded")
    for name, reference in original["copy_files"].items():
        require(sha(inside(root / "sources" / original["source_relative"], name)) == reference["sha256"],
            "immutable_adapter_custody_changed")
    require(sha(root / "GAME_MANIFEST.json") == EXPECTED_BATTERY["game_sha256"]
        and sha(root / "judge/REFERENCE_PANELS.private.json") == EXPECTED_BATTERY["panel_sha256"]
        and canonical(read(root / "assets/RULE.json")) == EXPECTED_BATTERY["rule_digest"],
        "original_scene_panel_judge_rule_required")
    lease = read(root / "runtime/LEASE_AUTHORITY.json")["bounds"]["ovx4"]
    require(lease["job_end_unix"] == HARD_END and lease["conservative_lease_end_unix"] == BOUNDARY,
        "bound_lease_authority_required")
    return root


def verify_host(config):
    require(os.getuid() == config["expected_uid"], "leased_host_user_required")
    require(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == config["receiving_boot_id"],
        "receiving_host_boot_changed_recheck_admission")
    require(os.uname().nodename == config["receiving_hostname"], "receiving_host_required")


def gpu_inventory():
    rows = subprocess.check_output(["nvidia-smi", "--query-gpu=index,uuid,memory.used",
        "--format=csv,noheader,nounits"], text=True).splitlines()
    applications = subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid",
        "--format=csv,noheader"], text=True).splitlines()
    owners = {}
    for line in applications:
        uuid, pid = [value.strip() for value in line.split(",")]
        owners.setdefault(uuid, []).append(int(pid))
    result = []
    for line in rows:
        physical, uuid, memory = [value.strip() for value in line.split(",")]
        result.append(dict(physical=int(physical), uuid=uuid, memory_used_mib=int(memory),
            compute_pids=owners.get(uuid, [])))
    return result


def validate_admission(config, inventory, roles=("judge", "player")):
    indices = {row["physical"]: row for row in inventory}
    require(len(indices) == len(inventory), "unique_physical_inventory")
    for role in roles:
        bound = config["role_devices"][role]
        actual = indices[bound["physical"]]
        require(actual["uuid"] == bound["uuid"], "device_uuid_mapping_changed")
        require(actual["memory_used_mib"] < 100 and not actual["compute_pids"], "live_or_occupied_device_no_displacement")


def validate_confinement(physical, proof, visible_uuid, expected_uuid):
    require(set(proof) == {str(index) for index in range(8)}, "all_device_open_attempts_required")
    require(proof[str(physical)]["opened"] is True and sum(row["opened"] is True for row in proof.values()) == 1,
        "one_assigned_device_open_seven_denied")
    require(visible_uuid == expected_uuid, "exact_uuid_visible_no_other_gpu")


def actual_confinement(physical, uuid):
    proof = {}
    for index in range(8):
        try:
            descriptor = os.open(f"/dev/nvidia{index}", os.O_RDWR)
        except OSError as error:
            proof[str(index)] = dict(opened=False, errno=error.errno)
        else:
            os.close(descriptor)
            proof[str(index)] = dict(opened=True)
    validate_confinement(physical, proof, os.environ.get("CUDA_VISIBLE_DEVICES"), uuid)
    return proof


def write_once(path, value):
    payload = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    with path.open("xb") as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())


def verify_no_attempt(root, config):
    require(not (root / "runtime/LAUNCH.json").exists(), "existing_launch_never_replayed")
    for name in ("player_DEVICE_PROOF.json", "judge_DEVICE_PROOF.json", "JUDGE_LOADED.json",
                 "player_DISPATCHED.json", "judge_DISPATCHED.json", "player_FAILED.json", "judge_FAILED.json"):
        require(not (root / name).exists(), "existing_attempt_never_replayed")
    require(not (root / "players" / config["condition"]).exists(), "prior_player_state_never_replayed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--launch", type=Path, required=True)
    parser.add_argument("--launch-sha256", required=True)
    parser.add_argument("--mode", choices=("player", "judge"), required=True)
    arguments = parser.parse_args()
    config = load_config(arguments.config, arguments.config_sha256)
    verify_host(config)
    root = verify_bundle(config)
    require(arguments.launch == root / "runtime/LAUNCH.json" and sha(arguments.launch) == arguments.launch_sha256,
        "bound_launch_required")
    launch = read(arguments.launch)
    deadline = launch["deadline_unix"]
    require(launch["config_sha256"] == arguments.config_sha256 and launch["job_id"] == config["job_id"], "launch_identity_join")
    require(time.time() < deadline <= min(HARD_END, launch["created_unix"] + 2400), "finite_launch_deadline_required")
    role = arguments.mode
    assigned = config["role_devices"][role]
    with (root / "runtime" / (role + ".lock")).open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (root / "runtime" / (role + "_START_INTENT.json")).exists(), "role_already_attempted_no_retry")
        proof = actual_confinement(assigned["physical"], assigned["uuid"])
        write_once(root / "runtime" / (role + "_START_INTENT.json"), dict(unix=time.time(), pid=os.getpid(),
            role=role, config_sha256=arguments.config_sha256, deadline_unix=deadline, confinement=proof))
        sys.path.insert(0, str(root / "source"))
        from research_loop.workers.rohin233_kept_age_probe_20260918 import probe
        require(Path(probe.__file__).resolve() == root / "source" / (MODULE.replace(".", "/") + ".py"),
            "original_bound_probe_module_only")
        sys.argv = [str(probe.__file__), "--root", str(root), "--mode", role,
            "--physical", str(assigned["physical"]), "--deadline", str(deadline)]
        probe.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
