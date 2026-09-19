"""CPU-only, exclusive creation of sibling runtime/config and registry; never activate."""

import argparse
import copy
import fcntl
from pathlib import Path
import shutil
import time

import admission as rules
from bind_bundle import RUNTIME_FILES
import daemon
from host import previous_attempts
import probe_runtime as runtime


WORKER = Path(__file__).resolve().parent


def untouched_job(root, config, state):
    runtime.verify_no_attempt(root, config)
    rules.require(not state.exists(), "existing_queue_state_requires_explicit_state_reconciliation_not_reset")
    for assigned in config["role_devices"].values():
        claim = Path(config["claims_namespace"]) / (assigned["uuid"] + ".json")
        if claim.exists():
            rules.require(runtime.read(claim).get("job_id") != config["job_id"], "prior_claim_for_same_job_no_retry")
    for attempt in previous_attempts(config["queue_policy"]):
        rules.require(attempt["job_id"] != config["job_id"]
            and attempt.get("source_key") != config["source_identity"]["journal_id"] + ":" + config["source_identity"]["sleep_complete_sha256"]
            and config["source_identity"]["sleep_complete_sha256"] not in attempt.get("source_cut_sha256s", []),
            "prior_source_attempt_any_status_no_retry")


def replacement_config(old, registry, runtime_files):
    root = Path(old["root"])
    result = copy.deepcopy(old)
    result["runtime_directory"] = str(root / "runtime_v4")
    result["runtime_files"] = dict(runtime_files)
    result["runtime_rebind"] = dict(schema="IMMUTABLE_RUNTIME_REBIND_V3_TO_V4",
        predecessor_config_sha256=runtime.sha(root / "runtime/JOB_CONFIG.json"),
        predecessor_capsule_sha256=runtime.sha(root / "runtime/CAPSULE.json"),
        predecessor_registry_sha256=runtime.sha(registry))
    runtime.verify_runtime_rebind(result)
    return result


def registry_replacement(old_registry, old_capsule, new_capsule, old_sha):
    rules.require(old_registry["capsules"].count(old_capsule) == 1, "exactly_one_predecessor_capsule_required")
    rules.require(old_capsule["job_id"] == new_capsule["job_id"] and old_capsule["source_key"] == new_capsule["source_key"],
        "same_no_retry_identity_required")
    allowed = {"config_sha256", "bundle_evidence_sha256", "runtime_manifest_sha256", "runtime_directory", "runtime_rebind_receipt_sha256"}
    rules.require({key: value for key, value in old_capsule.items() if key not in allowed}
        == {key: value for key, value in new_capsule.items() if key not in allowed}, "only_runtime_capsule_fields_may_change")
    result = copy.deepcopy(old_registry)
    result["capsules"] = [new_capsule if row == old_capsule else row for row in old_registry["capsules"]]
    result["runtime_rebind"] = dict(predecessor_registry_sha256=old_sha, same_source_job_and_no_retry_identity=True)
    return result


def stage(root, old_config_sha, old_registry_sha, release_freeze, release_sha):
    daemon.verify_freeze(release_freeze, release_sha)
    config_path = root / "runtime/JOB_CONFIG.json"
    old = runtime.load_config(config_path, old_config_sha)
    policy = old["queue_policy"]
    runtime.verify_protected(old)
    worker_root = root.parent.parent
    registry_path = worker_root / "inputs/capsules.json"
    destination_registry = worker_root / "inputs/capsules_v4.json"
    state = worker_root / "state/queue.sqlite"
    rules.require(runtime.sha(registry_path) == old_registry_sha, "predecessor_registry_pin")
    selected_runtime = root / "runtime_v4"
    rules.require(not selected_runtime.exists() and not destination_registry.exists(), "existing_rebind_never_overwritten_or_retried")
    entry = runtime.read(root / "ENROLLMENT_ENTRY.json")
    old_capsule = runtime.read(root / "runtime/CAPSULE.json")
    rules.validate_capsule(entry, old_capsule, policy)
    rules.require(old_capsule["config_sha256"] == old_config_sha, "predecessor_config_capsule_join")
    runtime.verify_bundle(old)
    rules.require(len(runtime.read(root / "SOURCE_MANIFEST.json")) == 103, "same_103_scientific_source_files")
    with (Path(old["claims_namespace"]) / "DISPATCH.lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        untouched_job(root, old, state)
        selected_runtime.mkdir(mode=0o700)
        for name in RUNTIME_FILES:
            shutil.copyfile(WORKER / name, selected_runtime / name)
        new = replacement_config(old, registry_path, {name: runtime.sha(selected_runtime / name) for name in RUNTIME_FILES})
        runtime.validate_config(new, time.time())
        runtime.verify_bundle(new)
        new_config = selected_runtime / "JOB_CONFIG.json"
        runtime.write_once(new_config, new)
        evidence = dict(config_sha256=runtime.sha(new_config), inputs=new["input_files"], runtime=new["runtime_files"],
            source_identity=new["source_identity"], epoch=new["source_runtime_epoch"], gpu_execution_performed=False,
            immutable_predecessor=new["runtime_rebind"])
        runtime.write_once(selected_runtime / "BUNDLE_EVIDENCE.json", evidence)
        runtime.verify_protected(new)
        untouched_job(root, old, state)
        receipt = dict(schema="VERIFIED_CPU_ONLY_RUNTIME_REBIND_V1", verified_unix=time.time(),
            job_id=new["job_id"], source_key=rules.source_key(entry), config_sha256=runtime.sha(new_config),
            bundle_evidence_sha256=runtime.sha(selected_runtime / "BUNDLE_EVIDENCE.json"),
            predecessor=new["runtime_rebind"], runtime_manifest_sha256=rules.digest(new["runtime_files"]),
            staging_release_sha256=release_sha, same_input_files=True, scientific_source_files=103,
            same_battery_judge_source_epoch_and_deadlines=True, capture_rebuilt=False,
            source_epoch_scan_performed=False, activation_performed=False, gpu_execution_performed=False)
        runtime.write_once(selected_runtime / "REBIND_VERIFIED.json", receipt)
        capsule = dict(old_capsule, config_sha256=runtime.sha(new_config),
            bundle_evidence_sha256=receipt["bundle_evidence_sha256"], runtime_manifest_sha256=receipt["runtime_manifest_sha256"],
            runtime_directory=str(selected_runtime), runtime_rebind_receipt_sha256=runtime.sha(selected_runtime / "REBIND_VERIFIED.json"))
        rules.validate_capsule(entry, capsule, policy)
        runtime.write_once(selected_runtime / "CAPSULE.json", capsule)
        registry = registry_replacement(runtime.read(registry_path), old_capsule, capsule, old_registry_sha)
        runtime.write_once(destination_registry, registry)
        rules.require(runtime.sha(config_path) == old_config_sha and runtime.sha(registry_path) == old_registry_sha,
            "predecessors_must_remain_unchanged")
        return dict(receipt, runtime_directory=str(selected_runtime), capsule_sha256=runtime.sha(selected_runtime / "CAPSULE.json"),
            registry_path=str(destination_registry), registry_sha256=runtime.sha(destination_registry))


def verify_staged(root):
    selected = root / "runtime_v4"
    receipt = runtime.read(selected / "REBIND_VERIFIED.json")
    new = runtime.load_config(selected / "JOB_CONFIG.json", receipt["config_sha256"])
    runtime.verify_bundle(new)
    old_registry = root.parent.parent / "inputs/capsules.json"
    new_registry = root.parent.parent / "inputs/capsules_v4.json"
    old_capsule = runtime.read(root / "runtime/CAPSULE.json")
    capsule = runtime.read(selected / "CAPSULE.json")
    rules.validate_capsule(runtime.read(root / "ENROLLMENT_ENTRY.json"), capsule, new["queue_policy"])
    rules.require(runtime.sha(selected / "REBIND_VERIFIED.json") == capsule["runtime_rebind_receipt_sha256"]
        and runtime.sha(selected / "JOB_CONFIG.json") == capsule["config_sha256"]
        and runtime.sha(selected / "BUNDLE_EVIDENCE.json") == capsule["bundle_evidence_sha256"]
        and rules.digest(new["runtime_files"]) == capsule["runtime_manifest_sha256"], "rebound_receipt_capsule_config_join")
    rules.require(runtime.read(new_registry) == registry_replacement(runtime.read(old_registry), old_capsule, capsule,
        runtime.sha(old_registry)), "exact_immutable_registry_replacement")
    runtime.verify_protected(new)
    untouched_job(root, new, root.parent.parent / "state/queue.sqlite")
    return dict(status="CPU_REBIND_VERIFIED_NO_ACTIVATION", config_sha256=capsule["config_sha256"],
        capsule_sha256=runtime.sha(selected / "CAPSULE.json"), registry_sha256=runtime.sha(new_registry),
        job_id=new["job_id"], source_epoch_scan_performed=False, gpu_execution_performed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--old-config-sha256")
    parser.add_argument("--old-registry-sha256")
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--freeze-sha256")
    args = parser.parse_args()
    result = stage(args.root, args.old_config_sha256, args.old_registry_sha256, args.freeze,
        args.freeze_sha256) if args.stage else verify_staged(args.root)
    print(rules.canonical(result))


if __name__ == "__main__":
    main()
