"""CPU-only binding of an already prepared original-policy source capsule."""

import argparse
import json
from pathlib import Path
import shutil
import time

import admission as rules
import probe_runtime as runtime


WORKER = Path(__file__).resolve().parent
RUNTIME_FILES = ("admission.py", "probe_runtime.py", "epoch_cache.py", "dispatch_once.py", "scientific_inputs.json")


def bind(root, entry, policy, lease_path):
    rules.validate_policy(policy)
    rules.validate_entry(entry)
    rules.require(entry["record_index"] > policy["frontiers"][entry["life"]], "no_historical_execution")
    rules.require(str(root) == policy["future_job_root"] + "/" + rules.job_id(entry), "canonical_new_job_root")
    rules.require(not (root / "runtime").exists(), "existing_binding_never_overwritten")
    provenance = runtime.read(root / "CPU_PROVENANCE.json")
    identity = runtime.read(root / "CONDITION.json")
    captured = runtime.read(root / "sources/CAPTURE.json")["sources"]
    rules.require(len(captured) == 1 and captured[0]["source_name"] == entry["life"], "one_captured_enrolled_source")
    runtime.verify_source_closure(root)
    rules.require(runtime.sha(root / "SOURCE_MANIFEST.json") == rules.SOURCE_MANIFEST_SHA, "original_source_closure")
    scientific = runtime.read(WORKER / "scientific_inputs.json")
    rules.require(runtime.sha(lease_path) == scientific["runtime/LEASE_AUTHORITY.json"], "original_lease_authority")
    for name, checksum in scientific.items():
        if not name.startswith("runtime/"):
            rules.require(runtime.sha(runtime.inside(root, name)) == checksum, "original_scientific_inputs")
    (root / "runtime").mkdir(mode=0o700)
    shutil.copyfile(lease_path, root / "runtime/LEASE_AUTHORITY.json")
    for name in RUNTIME_FILES:
        shutil.copyfile(WORKER / name, root / "runtime" / name)
    runtime.write_once(root / "ENROLLMENT_ENTRY.json", entry)
    runtime.write_once(root / "QUEUE_POLICY.json", policy)
    source_identity = dict(journal_id=entry["journal_id"], absolute_sleep=entry["sleep"],
        optimizer_steps=entry["optimizer_steps"], sleep_complete_sha256=entry["record_sha256"],
        adapter_state_sha256=entry["adapter_state_sha256"])
    inputs = dict(scientific)
    for name in ("ENROLLMENT_ENTRY.json", "QUEUE_POLICY.json", "CONDITION.json", "CPU_PROVENANCE.json",
            "SOURCE_MANIFEST.json", "sources/CAPTURE.json", "FRESHNESS_VERIFIED.json", "GAME_MANIFEST.json",
            "judge/REFERENCE_PANELS.private.json"):
        inputs[name] = runtime.sha(runtime.inside(root, name))
    config = dict(root=str(root), worker_root=policy["future_job_root"], claims_namespace=policy["claims_namespace"],
        condition=identity["condition"], source_name=entry["life"], source_identity=source_identity,
        source_runtime_epoch=entry["runtime_load"], queue_policy=policy, battery=rules.BATTERY,
        job_id=rules.job_id(entry), input_files=inputs,
        runtime_files={name: runtime.sha(root / "runtime" / name) for name in RUNTIME_FILES},
        role_devices=policy["role_devices"], scheduled_physical=[2, 7], protected_physical=policy["protected_physical"],
        lease_end_unix=rules.HARD_END, lease_boundary_unix=rules.BOUNDARY, max_runtime_seconds=2400,
        receiving_hostname=policy["receiving_hostname"], receiving_boot_id=policy["receiving_boot_id"], expected_uid=policy["expected_uid"])
    runtime.validate_config(config, time.time())
    runtime.verify_bundle(config)
    runtime.wait_for_live_source(config)
    config_path = root / "runtime/JOB_CONFIG.json"
    runtime.write_once(config_path, config)
    evidence = dict(config_sha256=runtime.sha(config_path), inputs=inputs, runtime=config["runtime_files"],
        source_identity=source_identity, epoch=entry["runtime_load"], gpu_execution_performed=False)
    runtime.write_once(root / "runtime/BUNDLE_EVIDENCE.json", evidence)
    capsule = dict(source_key=rules.source_key(entry), job_id=rules.job_id(entry), root=str(root), policy_sha256=rules.digest(policy),
        source_identity=source_identity, battery=rules.BATTERY, base_sha256=rules.BASE_SHA,
        status=provenance["status"], freshness_eligible=True, parent_tokens=0, model_updates=0,
        source_context_loaded=False, optimizer_rng_loaded=False, source_manifest_sha256=rules.SOURCE_MANIFEST_SHA,
        source_file_count=103, lease_end_unix=rules.HARD_END, source_hard_end_unix=rules.HARD_END,
        config_sha256=runtime.sha(config_path), freshness_sha256=inputs["FRESHNESS_VERIFIED.json"],
        bundle_evidence_sha256=runtime.sha(root / "runtime/BUNDLE_EVIDENCE.json"),
        runtime_manifest_sha256=rules.digest(config["runtime_files"]), verified_bundle=True,
        runtime_variant="QUEUE_V1_ORIGINAL_PROBE")
    rules.validate_capsule(entry, capsule, policy)
    runtime.write_once(root / "runtime/CAPSULE.json", capsule)
    return capsule


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("root", "entry", "policy", "lease-authority"):
        parser.add_argument("--" + field, required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(bind(args.root, runtime.read(args.entry), runtime.read(args.policy), args.lease_authority), sort_keys=True))


if __name__ == "__main__":
    main()
