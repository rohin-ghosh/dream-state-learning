"""Pure, offline admission and route rendering; never execute a command."""

import hashlib
import json
from pathlib import Path


BASE_SHA = "a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992"
SOURCE_MANIFEST_SHA = "a924b1079ab527719e676d095eea812e75e9e8f18d3b589492d2d91fc6d84db7"
HARD_END = 1790791170
BOUNDARY = 1790812800
SUPPORTED = {
    "FRESH_R231": "038f85cbde5c4abfb749ea4d59da6897",
    "R232_SIBLING_FROZEN": "30fa18c869b34fd496a2758a4a28e197",
}
BATTERY = dict(policy="R232_FRESH_DEVELOPMENT_FIXED_TOKENS_V1", scenes=3,
    seeds=[23201, 23202], tokens_per_cell=1024, total_generated_tokens=6144,
    parent_tokens=0, model_updates=0,
    game_sha256="31e3c9919524deacc1d8255caa65f5121744ef6f0465988576b2d1b7ad281274",
    panel_sha256="4adab198a81f2492fff5471d0a7a20de41c06f59c7a492d7ef35746f84d346aa",
    rule_digest="7127a82613c6c75ed561b180ad394a657acbc194cb27cca72bc3b0a686d6444a")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def is_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(letter in "0123456789abcdef" for letter in value)


def source_key(entry):
    return entry["journal_id"] + ":" + entry["record_sha256"]


def job_id(entry):
    identity = dict(journal_id=entry["journal_id"], sleep_complete_sha256=entry["record_sha256"],
        adapter_state_sha256=entry["adapter_state_sha256"], battery=BATTERY)
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def validate_entry(entry):
    require(entry["key"] == source_key(entry), "canonical_enrollment_key")
    require(is_sha(entry["record_sha256"]) and is_sha(entry["adapter_state_sha256"]), "source_hashes")
    require(type(entry["record_index"]) is int and entry["record_index"] >= 0, "complete_index")
    require(type(entry["sleep"]) is int and entry["sleep"] >= 1, "native_age_not_synthetic_base_age")
    require(type(entry["optimizer_steps"]) is int and entry["optimizer_steps"] >= 0, "optimizer_age")


def validate_policy(policy):
    require(policy["deployment_enabled"] is False and policy["automatic_launch"] is False, "offline_only")
    require(policy["expected_uid"] == 1352 and policy["receiving_hostname"] == "ipp2-ovx-p3-02", "original_receiving_host_and_user")
    require(set(policy["supported_journals"]) == set(SUPPORTED), "v1_exact_checkpoint_families")
    require(len(set(policy["supported_journals"].values())) == 2 and all(isinstance(value, str)
        and 24 <= len(value) <= 64 and all(letter in "0123456789abcdef" for letter in value)
        for value in policy["supported_journals"].values()), "explicit_bound_pair_journals")
    require(policy["max_concurrent_jobs"] == 1 and policy["max_runtime_seconds"] == 2400, "one_bounded_two_gpu_lane")
    require(policy["lease_end_unix"] == HARD_END and policy["lease_boundary_unix"] == BOUNDARY, "unchanged_lease")
    require(policy["observation_max_age_seconds"] == 30 and policy["teardown_margin_seconds"] == 30, "bounded_observation_and_teardown")
    require(policy["claims_namespace"] == "/localhome/local-rohing/post_reboot_probe_dispatch_20260919/dispatch_locks", "reuse_original_claim_namespace")
    require(policy["historical_policy"] == "PRESERVE_PENDING_NO_AUTOMATIC_HISTORICAL_EXECUTION", "preserve_prospective_policy")
    require(set(policy["frontiers"]) == set(SUPPORTED) and all(type(value) is int and value >= 0
        for value in policy["frontiers"].values()), "explicit_source_frontiers")
    require(policy["future_job_root"] == "/localhome/local-rohing/post_reboot_probe_queue_20260919/jobs"
        and policy["attempt_scan_parent"] == "/localhome/local-rohing", "fixed_disjoint_and_history_roots")
    for field in ("source_roots", "initial_loaded", "current_loaded"):
        require(set(policy[field]) == set(SUPPORTED), "all_pair_source_bindings")
    for source in SUPPORTED:
        require(Path(policy["source_roots"][source]).is_relative_to("/localhome/local-rohing")
            and ".." not in Path(policy["source_roots"][source]).parts, "bound_source_root")
        for field in ("initial_loaded", "current_loaded"):
            require(type(policy[field][source]["index"]) is int and is_sha(policy[field][source]["sha256"]), "bound_loaded_epoch")
    require(set(policy["role_devices"]) == {"player", "judge"}, "two_roles")
    physical = [value["physical"] for value in policy["role_devices"].values()]
    uuids = [value["uuid"] for value in policy["role_devices"].values()]
    require(set(physical) == {2, 7} and len(set(uuids)) == 2, "no_overlap_or_arbitrary_device_fallback")
    require(policy["role_devices"]["player"] == dict(physical=2, uuid="GPU-ac7e4165-630c-eafe-4ba5-2b2fc4a4e5d1")
        and policy["role_devices"]["judge"] == dict(physical=7, uuid="GPU-b7ec9035-3ba3-464f-6c2f-7588a3e328c1"), "reviewed_uuid_roles")
    require(set(policy["protected_physical"]) == set(range(8)) - {2, 7}, "all_other_devices_protected")
    require(len(policy["protected_processes"]) == 6 and len({row["pid"] for row in policy["protected_processes"]}) == 6, "six_protected_process_identities")
    for row in policy["protected_processes"]:
        require(type(row["pid"]) is int and str(row["start_ticks"]).isdigit() and is_sha(row["argv_sha256"]), "exact_protected_handle")


def validate_observation(policy, observation, now):
    validate_policy(policy)
    require(0 <= now - observation["observed_unix"] <= 30, "stale_or_future_host_observation")
    require(observation["receiving_hostname"] == policy["receiving_hostname"]
        and observation["receiving_boot_id"] == policy["receiving_boot_id"]
        and observation["uid"] == policy["expected_uid"], "receiving_host_identity_changed")
    require(observation["complete_process_scan"] is True and observation["complete_attempt_scan"] is True
        and observation["complete_claim_scan"] is True, "complete_host_job_claim_inventory_required")
    actual = {row["pid"]: row for row in observation["processes"]}
    require(len(actual) == len(observation["processes"]), "unique_process_inventory")
    for expected in policy["protected_processes"]:
        require(all(actual.get(expected["pid"], {}).get(name) == value for name, value in expected.items()), "protected_process_identity_changed")
    devices = {row["physical"]: row for row in observation["gpus"]}
    require(set(devices) == set(range(8)) and len(devices) == len(observation["gpus"]), "complete_gpu_inventory")
    for assigned in policy["role_devices"].values():
        require(devices[assigned["physical"]]["uuid"] == assigned["uuid"], "uuid_mapping_changed")
    require(now + 60 < HARD_END, "lease_closed")
    return devices


def lane_free(policy, observation, now, own_job=None):
    devices = validate_observation(policy, observation, now)
    for assigned in policy["role_devices"].values():
        current = devices[assigned["physical"]]
        require(current["memory_used_mib"] == 0 and current["compute_pids"] == [], "lane_occupied_no_displacement")
    for claim in observation["claims"]:
        require(claim["namespace"] == policy["claims_namespace"], "unknown_claim_namespace")
        if claim["uuid"] in {row["uuid"] for row in policy["role_devices"].values()}:
            require(now > claim["hold_until_unix"] or claim["job_id"] == own_job, "original_claim_still_held")
    require(not any(row["state"] in {"RUNNING", "DISPATCHED", "UNKNOWN"} and row["job_id"] != own_job
        for row in observation["jobs"]), "unreconciled_external_job")


def validate_capsule(entry, capsule, policy):
    require(capsule["policy_sha256"] == digest(policy), "capsule_policy_requires_explicit_review_rebind")
    require(isinstance(entry.get("runtime_load"), dict) and type(entry["runtime_load"].get("index")) is int
        and is_sha(entry["runtime_load"].get("sha256")), "captured_source_epoch_required")
    require(entry["life"] in SUPPORTED and entry["journal_id"] == policy["supported_journals"][entry["life"]], "unsupported_source_family")
    require(capsule["source_key"] == source_key(entry) and capsule["job_id"] == job_id(entry), "same_captured_cut_and_job")
    require(capsule["battery"] == BATTERY and capsule["base_sha256"] == BASE_SHA, "unchanged_battery_and_base")
    require(capsule["source_identity"] == dict(journal_id=entry["journal_id"], absolute_sleep=entry["sleep"],
        optimizer_steps=entry["optimizer_steps"], sleep_complete_sha256=entry["record_sha256"],
        adapter_state_sha256=entry["adapter_state_sha256"]), "source_age_or_epoch_mismatch")
    require(capsule["status"] == "CPU_SOURCE_READY_NOT_LOADED" and capsule["freshness_eligible"] is True, "capture_and_exposure_required")
    require(capsule["parent_tokens"] == 0 and capsule["model_updates"] == 0
        and capsule["source_context_loaded"] is False and capsule["optimizer_rng_loaded"] is False, "parent_free_frozen_eval")
    require(capsule["source_manifest_sha256"] == SOURCE_MANIFEST_SHA and capsule["source_file_count"] == 103, "full_original_source_closure")
    require(capsule["lease_end_unix"] == HARD_END and capsule["source_hard_end_unix"] == HARD_END, "bound_existing_pair_lease")
    for field in ("config_sha256", "freshness_sha256", "bundle_evidence_sha256", "runtime_manifest_sha256"):
        require(is_sha(capsule[field]), "bound_capsule_" + field)
    require(capsule["runtime_variant"] == "QUEUE_V1_ORIGINAL_PROBE" and capsule["verified_bundle"] is True, "verified_scoped_runtime_required")
    require(capsule["root"] == policy["future_job_root"] + "/" + job_id(entry), "disjoint_stable_job_root")
    if "runtime_directory" in capsule:
        require(capsule["runtime_directory"] == capsule["root"] + "/runtime_v4"
            and is_sha(capsule["runtime_rebind_receipt_sha256"]), "exact_verified_runtime_rebind")


def classify(entry, attempted_keys, capsules, policy):
    key = source_key(entry)
    if key in attempted_keys:
        return "ATTEMPT_RECORDED_NO_RETRY"
    if entry["life"] not in SUPPORTED:
        return "PENDING_UNSUPPORTED_ROOT"
    if entry["journal_id"] != policy["supported_journals"][entry["life"]]:
        return "PENDING_UNSUPPORTED_JOURNAL_EPOCH"
    if entry["record_index"] <= policy["frontiers"][entry["life"]]:
        return "PENDING_HISTORICAL_CAPTURE_NOT_SELECTED"
    if entry.get("checkpoint_status") != "JOINED_NOT_COPIED":
        return "PENDING_CHECKPOINT_MISSING_OR_MISMATCHED"
    if key not in capsules:
        return "PENDING_CAPTURE_EXPOSURE_AND_RUNTIME_BINDING"
    if capsules[key].get("policy_sha256") != digest(policy):
        return "PENDING_POLICY_REBIND_NEW_BUNDLE_REQUIRED"
    try:
        validate_capsule(entry, capsules[key], policy)
    except (ValueError, KeyError, TypeError):
        return "PENDING_INVALID_OR_INCOMPLETE_CAPSULE"
    return "CPU_ELIGIBLE_PENDING_CURRENT_ADMISSION"


def proposal(entry, capsule, policy, observation, now):
    validate_capsule(entry, capsule, policy)
    lane_free(policy, observation, now)
    require(not any(row["job_id"] == job_id(entry) or row.get("source_key") == source_key(entry)
        for row in observation["jobs"]), "existing_external_attempt_no_replay")
    deadline = min(now + 2400, HARD_END, capsule["source_hard_end_unix"])
    require(deadline - now > 60, "bounded_admission_window")
    return dict(job_id=job_id(entry), source_key=source_key(entry), created_unix=now,
        deadline_unix=deadline, hold_until_unix=deadline + 30,
        receiving_boot_id=observation["receiving_boot_id"], observer_boot_id=observation["observer_boot_id"],
        observation_sha256=digest(observation), config_sha256=capsule["config_sha256"],
        bundle_evidence_sha256=capsule["bundle_evidence_sha256"], root=capsule["root"],
        runtime_directory=capsule.get("runtime_directory", capsule["root"] + "/runtime"),
        claims_namespace=policy["claims_namespace"], role_devices=policy["role_devices"],
        status="OFFLINE_PROPOSAL_NOT_RESERVED_NOT_LAUNCHED", battery=BATTERY)
