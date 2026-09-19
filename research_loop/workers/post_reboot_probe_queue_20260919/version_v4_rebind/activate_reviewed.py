"""Main-only explicit review-pinned activation; staging never calls this entrypoint."""

import argparse
import os
from pathlib import Path
import time

import admission as rules
from bind_bundle import RUNTIME_FILES
import daemon
import probe_runtime as runtime


WORKER = Path(__file__).resolve().parent


def prepare_review(worker, source_sha, registry_sha):
    freeze = worker / "SOURCE_FREEZE_V4_REBIND.json"
    daemon.verify_freeze(freeze, source_sha)
    base = worker.parent
    registry = base / "inputs/capsules_v4.json"
    rules.require(runtime.sha(registry) == registry_sha, "reviewed_registry_pin_required")
    rules.require(not (base / "inputs/activation.json").exists(), "legacy_activation_requires_explicit_reconciliation")
    policy = runtime.read(base / "inputs/policy.json")
    rules.validate_policy(policy)
    rules.require(time.time() + 60 < policy["lease_end_unix"], "original_lease_expired")
    capsules = runtime.read(registry)["capsules"]
    rules.require(bool(capsules), "concrete_verified_capsule_required")
    for capsule in capsules:
        selected = runtime.runtime_directory(capsule)
        rules.require(selected.name == "runtime_v4", "reviewed_rebound_runtime_required")
        rules.require(runtime.sha(selected / "REBIND_VERIFIED.json") == capsule["runtime_rebind_receipt_sha256"],
            "verified_rebind_receipt_required")
        rules.require(runtime.sha(selected / "JOB_CONFIG.json") == capsule["config_sha256"]
            and runtime.sha(selected / "BUNDLE_EVIDENCE.json") == capsule["bundle_evidence_sha256"], "reviewed_config_and_evidence_pins")
        config = runtime.read(selected / "JOB_CONFIG.json")
        rules.require(config["queue_policy"] == policy and capsule["policy_sha256"] == rules.digest(policy), "reviewed_policy_join")
        runtime.verify_runtime_rebind(config)
        expected = {name: runtime.sha(worker / name) for name in RUNTIME_FILES}
        rules.require(config["runtime_files"] == expected
            and all(runtime.sha(selected / name) == checksum for name, checksum in expected.items()), "same_final_runtime_release")
    review = dict(reviewed=True, runtime_enabled=True, route="ORIGINAL_GPU_HOST_TRANSIENT_CGROUP_ONE_SHOT_ONLY",
        source_freeze_sha256=source_sha, policy_sha256=rules.digest(policy), registry_sha256=registry_sha,
        expires_unix=policy["lease_end_unix"])
    activation = base / "inputs/activation_v4.json"
    if activation.exists():
        rules.require(runtime.read(activation) == review, "existing_activation_never_overwritten")
    else:
        runtime.write_once(activation, review)
    return activation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-seal", required=True)
    parser.add_argument("--reviewed-registry", required=True)
    args = parser.parse_args()
    prepare_review(WORKER, args.reviewed_seal, args.reviewed_registry)
    os.execv("/bin/bash", ["bash", str(WORKER / "ACTIVATE_FOREGROUND.sh")])


if __name__ == "__main__":
    main()
