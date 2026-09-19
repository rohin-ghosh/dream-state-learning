"""Receiving-host adapter. No SSH fallback, service probes, signals, or installation."""

import os
from pathlib import Path
import subprocess
import sys
import time

import admission as rules
from bind_bundle import RUNTIME_FILES
import probe_runtime as runtime
import receipts


WORKER = Path(__file__).resolve().parent


def attempt_roots(policy):
    parent = Path(policy["attempt_scan_parent"])
    roots = set(parent.glob("orch_r23*_probe*"))
    for directory in (parent / "post_reboot_probe_dispatch_20260919", Path(policy["future_job_root"])):
        if directory.is_dir():
            roots.update(path for path in directory.iterdir() if path.is_dir() and rules.is_sha(path.name))
    return sorted(path for path in roots if path.is_dir())


def previous_attempts(policy):
    attempts = []
    for root in attempt_roots(policy):
        players = list((root / "players").glob("*/LOADED.json"))
        markers = [root / "JUDGE_LOADED.json", root / "player_FAILED.json", root / "judge_FAILED.json"]
        for directory in root.glob("runtime*"):
            rules.require(not directory.is_symlink(), "ambiguous_attempt_runtime")
            markers.extend(directory / name for name in ("LAUNCH.json", "DISPATCH_FAILED.json", "DISPATCHED.json",
                "judge_START_INTENT.json", "player_START_INTENT.json"))
        if not players and not any(path.exists() for path in markers):
            continue
        capture_path = root / "sources/CAPTURE.json"
        rules.require(capture_path.is_file(), "attempt_missing_source_identity_no_replay")
        source = runtime.read(capture_path)["sources"]
        if root == Path(policy["attempt_scan_parent"]) / "orch_r232_age_probe_20260918":
            cuts = [row["sleep_complete_sha256"] for row in source]
            rules.require(cuts and all(rules.is_sha(value) for value in cuts), "legacy_original_battery_cuts_required")
            completed = list((root / "players").glob("*/COMPLETE.json"))
            closed = bool(players) and {path.parent.name for path in players} == {path.parent.name for path in completed}
            closed = closed and (root / "JUDGE_EXIT.json").is_file()
            identifier = rules.digest(dict(legacy_root=str(root), source_cuts=sorted(cuts)))
            attempts.append(dict(job_id=identifier, source_key="legacy:" + identifier, root=str(root),
                state="COMPLETE" if closed else "UNKNOWN", source_cut_sha256s=cuts,
                classification="ORIGINAL_MULTI_CONDITION_BATTERY_NOT_A_ONE_SHOT_QUEUE_JOB", no_retry=True))
            continue
        rules.require(len(source) == 1, "one_shot_history_source_join")
        source = source[0]
        identity = dict(journal_id=source["journal_id"], record_sha256=source["sleep_complete_sha256"],
            adapter_state_sha256=source["adapter_state_sha256"])
        complete = list((root / "players").glob("*/COMPLETE.json"))
        attempts.append(dict(job_id=rules.job_id(identity), source_key=rules.source_key(identity), root=str(root),
            state="COMPLETE" if complete else "UNKNOWN", no_retry=True))
    return attempts


class LocalHost:
    def __init__(self, policy):
        self.policy = policy
        self.source_cursors = {}

    def source_guard(self):
        pending = []
        for source in self.policy["supported_journals"]:
            try:
                self.source_cursors[source] = runtime.verify_source_epoch(self.policy, source, self.source_cursors.get(source))
            except runtime.SourceEpochPending as error:
                pending.append(error.progress)
        runtime.verify_protected(dict(self.policy, queue_policy=self.policy))
        rules.require(time.time() + 60 < self.policy["lease_end_unix"], "unexpired_finite_lease_required")
        if pending:
            raise runtime.SourceEpochPending(pending)

    def observe(self):
        self.source_guard()
        claims = []
        namespace = Path(self.policy["claims_namespace"])
        for assigned in self.policy["role_devices"].values():
            path = namespace / (assigned["uuid"] + ".json")
            if path.exists():
                claims.append(dict(runtime.read(path), uuid=assigned["uuid"], namespace=str(namespace)))
        return dict(observed_unix=time.time(), receiving_hostname=os.uname().nodename,
            receiving_boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(), uid=os.getuid(),
            observer_boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            complete_process_scan=True, complete_attempt_scan=True, complete_claim_scan=True,
            processes=[runtime.process_identity(row["pid"]) for row in self.policy["protected_processes"]],
            gpus=runtime.gpu_inventory(), claims=claims, jobs=previous_attempts(self.policy))

    def verify_capsule(self, entry, capsule):
        runtime.verify_protected(dict(self.policy, queue_policy=self.policy))
        rules.validate_capsule(entry, capsule, self.policy)
        root = Path(capsule["root"])
        selected_runtime = runtime.runtime_directory(capsule)
        config = runtime.load_config(selected_runtime / "JOB_CONFIG.json", capsule["config_sha256"])
        rules.require(runtime.runtime_directory(config) == selected_runtime, "capsule_runtime_directory_join")
        rules.require(config["queue_policy"] == self.policy and runtime.read(root / "ENROLLMENT_ENTRY.json") == entry,
            "reviewed_policy_and_enrollment_join")
        rules.require(runtime.sha(selected_runtime / "BUNDLE_EVIDENCE.json") == capsule["bundle_evidence_sha256"], "bundle_evidence_changed")
        if "runtime_directory" in capsule:
            rules.require(runtime.sha(selected_runtime / "REBIND_VERIFIED.json") == capsule["runtime_rebind_receipt_sha256"],
                "immutable_runtime_rebind_receipt_changed")
        rules.require(config["runtime_files"] == {name: runtime.sha(WORKER / name) for name in RUNTIME_FILES}, "reviewed_runtime_release_only")
        rules.require(capsule["runtime_manifest_sha256"] == rules.digest(config["runtime_files"])
            and capsule["freshness_sha256"] == config["input_files"]["FRESHNESS_VERIFIED.json"], "capsule_runtime_and_exposure_join")
        runtime.verify_bundle(config)
        try:
            runtime.verify_live_source(config)
        finally:
            runtime.verify_protected(config)
        return config

    def launch(self, plan):
        config_path = runtime.runtime_directory(plan) / "JOB_CONFIG.json"
        command = [sys.executable, "-B", str(config_path.parent / "dispatch_once.py"), "--config", str(config_path),
            "--config-sha256", plan["config_sha256"], "--deadline", str(plan["deadline_unix"]), "--launch"]
        completed = subprocess.run(command, check=False, capture_output=True, timeout=420)
        if completed.returncode:
            raise RuntimeError("ONE_SHOT_DENIAL_OR_FAILURE_NO_ALTERNATE_ROUTE_NO_RETRY")
        return dict(status="DISPATCHED", job_id=plan["job_id"], command_sha256=rules.digest(command))

    def reconcile(self, plan):
        root = Path(plan["root"])
        now = time.time()
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        if boot != plan["receiving_boot_id"]:
            return dict(status="INTERRUPTED_NO_RETRY", pause_reason="RECEIVING_BOOT_CHANGED_REVIEW_REBIND", job_id=plan["job_id"])
        selected_runtime = runtime.runtime_directory(plan)
        config_path = selected_runtime / "JOB_CONFIG.json"
        rules.require(runtime.sha(config_path) == plan["config_sha256"], "active_config_changed")
        config = runtime.read(config_path)
        guard = None
        try:
            runtime.verify_protected(config)
            self.source_guard()
        except (ValueError, OSError, KeyError):
            guard = "PROTECTED_OR_SOURCE_IDENTITY_CHANGED_REVIEW_REBIND"
        launch_path = selected_runtime / "LAUNCH.json"
        if not launch_path.exists():
            status = "UNKNOWN_NO_RETRY" if now > plan["hold_until_unix"] else "RECONCILING"
            return dict(status=status, pause_reason=guard or "DURABLE_INTENT_WITHOUT_LAUNCH_NEVER_RESUBMIT")
        launch = runtime.read(launch_path)
        rules.require(launch["job_id"] == plan["job_id"] and launch["config_sha256"] == plan["config_sha256"]
            and launch["deadline_unix"] <= plan["deadline_unix"], "active_launch_intent_join")
        live, started = [], []
        for role in ("judge", "player"):
            path = selected_runtime / (role + "_START_INTENT.json")
            if not path.exists():
                continue
            intent = runtime.read(path)
            rules.require(intent["config_sha256"] == plan["config_sha256"] and intent["boot_id"] == boot
                and intent["role"] == role and intent["deadline_unix"] == launch["deadline_unix"], "role_intent_join")
            assigned = config["role_devices"][role]
            runtime.validate_confinement(assigned["physical"], intent["confinement"], assigned["uuid"], assigned["uuid"])
            started.append(role)
            try:
                actual = runtime.process_identity(intent["pid"])
            except FileNotFoundError:
                continue
            rules.require(actual == intent["process_identity"], "job_pid_reuse_no_adoption")
            live.append(actual)
        shortfall = receipts.scoring_shortfall(receipts.outcomes(root))
        failure = any(path.exists() for path in (selected_runtime / "DISPATCH_FAILED.json", root / "player_FAILED.json", root / "judge_FAILED.json"))
        pause = guard or ("ONE_SHOT_FAILURE_NO_RETRY" if failure else None)
        output = root / "players" / config["condition"]
        if not live and len(started) == 2 and (output / "COMPLETE.json").is_file() and (root / "JUDGE_EXIT.json").is_file():
            runtime.verify_bundle(config)
            inventory = runtime.gpu_inventory()
            runtime.validate_admission(config, inventory)
            result = receipts.completion(config, launch["deadline_unix"])
            result["pause_reason"] = guard or result.get("pause_reason")
            if failure:
                result.update(status="FAILED_NO_RETRY", pause_reason=pause)
            return dict(result, job_id=plan["job_id"], probe_processes_absent=True)
        if now > plan["hold_until_unix"]:
            return dict(status="RECONCILING" if live else "FAILED_NO_RETRY", pause_reason="DEADLINE_ENDED_NO_CLEAN_COMPLETION",
                exact_live_processes=live, shortfall_count=len(shortfall), probe_processes_absent=not live, deadline_expired=True)
        return dict(status="RUNNING" if live else "RECONCILING", pause_reason=pause,
            exact_live_processes=live, started_roles=started, shortfall_count=len(shortfall),
            shortfall_classification_pending_completion=bool(shortfall))
