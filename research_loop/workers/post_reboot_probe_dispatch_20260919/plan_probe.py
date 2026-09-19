"""Plan only: distinguish enrollment, coherent sources, eligibility and GPU admission."""

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LEASE_END = 1790791170
LEASE_BOUNDARY = 1790812800
BATTERY = {
    "policy": "R232_FRESH_DEVELOPMENT_FIXED_TOKENS_V1",
    "scenes": 3,
    "seeds": [23201, 23202],
    "tokens_per_cell": 1024,
    "total_generated_tokens": 6144,
    "parent_tokens": 0,
    "model_updates": 0,
    "game_sha256": "31e3c9919524deacc1d8255caa65f5121744ef6f0465988576b2d1b7ad281274",
    "panel_sha256": "4adab198a81f2492fff5471d0a7a20de41c06f59c7a492d7ef35746f84d346aa",
    "rule_digest": "7127a82613c6c75ed561b180ad394a657acbc194cb27cca72bc3b0a686d6444a",
}


def source_key(source):
    return source["journal_id"], source["sleep_complete_sha256"]


def job_id(source):
    identity = dict(journal_id=source["journal_id"],
        sleep_complete_sha256=source["sleep_complete_sha256"],
        adapter_state_sha256=source["adapter_state_sha256"], battery=BATTERY)
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def plan(inventory, ledger_entries, policy, now):
    if inventory["read_only"] is not True:
        raise ValueError("read_only_inventory_required")
    age = now - inventory["unix"]
    blockers = []
    if not 0 <= age <= 300:
        blockers.append("INVENTORY_STALE_RECHECK_HOST_AND_GPU_OCCUPANCY")
    if now + 60 >= LEASE_END:
        blockers.append("SOURCE_LEASE_EXPIRED_OR_INSUFFICIENT_MARGIN")
    if inventory["battery"] != BATTERY:
        raise ValueError("unchanged_original_battery_required")
    if inventory["lease_end_unix"] != LEASE_END or inventory["lease_boundary_unix"] != LEASE_BOUNDARY:
        raise ValueError("existing_lease_only")
    if policy["optional_historical_enabled"] is not False:
        raise ValueError("historical_backlog_not_authorized")
    sources = {row["life"]: row for row in policy["sources"]}
    enrolled = {}
    for entry in ledger_entries:
        key = entry["journal_id"], entry["record_sha256"]
        if key in enrolled and enrolled[key] != entry:
            raise ValueError("ambiguous_enrollment_join")
        enrolled[key] = entry
    attempted = {source_key(row) for row in inventory["prior_jobs"]}
    dispositions, candidates, seen = [], [], set()
    for captured in inventory["captures"]:
        key = source_key(captured)
        if key in seen:
            raise ValueError("duplicate_capture_identity")
        seen.add(key)
        baseline = sources.get(captured["source_name"])
        entry = enrolled.get(key)
        status = "COHERENT_PROSPECTIVE_SOURCE_PENDING_EXPOSURE_AUDIT"
        if not baseline or baseline["journal_id"] != captured["journal_id"] or not entry:
            status = "UNREGISTERED_OR_UNENROLLED_SOURCE"
        elif entry["record_index"] != captured["sleep_complete_index"] or entry["sleep"] != captured["absolute_sleep"]:
            status = "ENROLLMENT_CUT_OR_AGE_MISMATCH"
        elif key in attempted:
            status = "ALREADY_ATTEMPTED_OR_COMPLETE_NO_REPLAY"
        elif captured["sleep_complete_index"] <= baseline["source_frontier"]:
            status = "HISTORICAL_CAPTURE_NOT_SELECTED"
        elif not captured["copy_hashes_verified"] or not captured["canonical_complete_verified"]:
            status = "SOURCE_CUSTODY_OR_CANONICAL_COMPLETE_UNVERIFIED"
        elif captured["eligibility"] != "PENDING_SOURCE_AND_INHERITED_EXPOSURE_AUDIT":
            status = "UNREVIEWED_CAPTURE_ELIGIBILITY_STATE"
        dispositions.append(dict(life=captured["source_name"], sleep=captured["absolute_sleep"],
            source_key=list(key), status=status))
        if status == "COHERENT_PROSPECTIVE_SOURCE_PENDING_EXPOSURE_AUDIT":
            candidates.append(captured)
    candidates.sort(key=lambda row: (row["captured_unix"], row["source_name"], row["sleep_complete_index"]))
    busy = [row for row in inventory["gpus"] if row["physical"] in (4, 5)
            and (row["memory_used_mib"] >= 100 or row["compute_pids"])]
    if busy:
        blockers.append("EXISTING_LEASE_RUNNER_GPU_4_5_OCCUPIED_DO_NOT_DISPLACE")
    blockers.extend(["NO_VERIFIED_UNEVALUATED_PREPARED_JOB", "ACTUAL_DEVICE_CONFINEMENT_AND_PLATFORM_ADMISSION_NOT_YET_TESTED"])
    selected = candidates[0] if candidates else None
    preparation = None
    if selected:
        identifier = job_id(selected)
        output = "/localhome/local-rohing/post_reboot_probe_dispatch_20260919/" + identifier
        condition = "R233_REBOOT_" + selected["source_name"] + "_s" + str(selected["absolute_sleep"])
        argv = ["/localhome/local-rohing/v2/venv/bin/python", "-B", inventory["prepare_script"],
            "--root", output, "--source-root", inventory["source_root"],
            "--original", inventory["original_root"], "--queued", selected["queued"],
            "--life", selected["life_root"], "--condition", condition]
        preparation = dict(job_id=identifier, source=selected, output=output, argv=argv,
            command=shlex.join(["bash", "gpu/ovx4_ssh.sh", shlex.join(argv)]),
            role="CPU_PREPARATION_ONLY_NOT_ELIGIBILITY_OR_GPU_EXECUTION",
            not_executed=True, original_prepare_rejects_existing_output=True,
            requires_fresh_source_lease_and_lane_coordination=True)
    return dict(schema="REBOOT_PROBE_EXECUTION_READINESS_V1", generated_unix=now,
        status="BLOCKED_NOT_GPU_LAUNCH_READY", automatic_dispatcher_implemented=False,
        gpu_execution_performed=False, admitted_gpu_jobs=[], launch_command=None,
        battery=BATTERY, original_source_deadline_unix=LEASE_END,
        per_job_deadline_recipe="min(now + 2400, 1790791170); at least 60 seconds remaining",
        source_dispositions=dispositions, source_preparation_candidate=preparation,
        blocked_original_devices=busy, blockers=blockers,
        additional_human_or_per_device_ratification_required=False,
        empty_devices_require_fresh_admission_not_new_authority=True,
        selection_is_not_capture_eligibility_or_execution=True,
        enrollment_ledger_written=False, native_signals=[], boot_installation_attempted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    arguments = parser.parse_args()
    inventory = json.loads(arguments.inventory.read_bytes())
    owner = REPO / "research_loop/workers/rohin233_kept_age_probe_20260918"
    entries = []
    for name in ("enrollment", "extra_enrollment"):
        state = json.loads((owner / name / "private/STATE.json").read_bytes())
        entries.extend(state["entries"].values())
    policy = json.loads((owner / "PROSPECTIVE_POLICY.json").read_bytes())
    print(json.dumps(plan(inventory, entries, policy, time.time()), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
