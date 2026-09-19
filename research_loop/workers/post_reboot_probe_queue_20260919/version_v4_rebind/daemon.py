"""Serialized foreground candidate; --check never inspects a host or launches work."""

import argparse
from collections import Counter
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

import admission as rules
from host import LocalHost
import probe_runtime as runtime
from store import Store, select


WORKER = Path(__file__).resolve().parent


@contextmanager
def singleton(state):
    state.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with state.with_suffix(state.suffix + ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def verify_freeze(path, expected):
    rules.require(runtime.sha(path) == expected, "reviewed_source_freeze_changed")
    freeze = runtime.read(path)
    names = {entry.name for entry in WORKER.glob("*.py")}
    rules.require(names == {name for name in freeze["files"] if name.endswith(".py")}, "complete_candidate_python_closure")
    for name, checksum in freeze["files"].items():
        rules.require(runtime.sha(runtime.inside(WORKER, name)) == checksum, "candidate_source_changed:" + name)


def activation(review, policy, freeze, now, registry=None):
    rules.require(review["reviewed"] is True and review["runtime_enabled"] is True, "candidate_not_activated")
    rules.require(review["policy_sha256"] == rules.digest(policy), "activation_policy_rebind_required")
    rules.require(review["route"] == "ORIGINAL_GPU_HOST_TRANSIENT_CGROUP_ONE_SHOT_ONLY", "no_alternate_launch_route")
    rules.require(now < review["expires_unix"] <= rules.HARD_END, "activation_expired_or_extended")
    verify_freeze(freeze, review["source_freeze_sha256"])
    if registry is not None:
        rules.require(runtime.sha(registry) == review["registry_sha256"], "activation_registry_changed")


def inputs(enrollment_paths, registry):
    entries, references = [], []
    for path in enrollment_paths:
        raw = path.read_bytes()
        snapshot = json.loads(raw)
        for key, entry in snapshot["entries"].items():
            rules.require(key == entry["key"], "enrollment_map_identity")
            entries.append(entry)
        references.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(),
            cursors_sha256=rules.digest(snapshot["cursors"])))
    capsules = {}
    for capsule in runtime.read(registry)["capsules"]:
        key = capsule["source_key"]
        rules.require(key not in capsules or capsules[key] == capsule, "conflicting_capsule_registry")
        capsules[key] = capsule
    return entries, references, capsules


class Queue:
    def __init__(self, store, policy, host=None, history=None):
        self.store = store
        self.policy = policy
        self.host = host
        self.history = history or []

    def current_observation(self):
        observation = self.host.observe()
        rules.validate_observation(self.policy, observation, time.time())
        for evidence in observation["jobs"]:
            self.store.prior_attempt(evidence["source_key"], evidence)
            cuts = set(evidence.get("source_cut_sha256s", []))
            if cuts:
                for enrolled in self.store.entries():
                    if enrolled["record_sha256"] in cuts:
                        self.store.prior_attempt(enrolled["key"], evidence)
        reconciled = {row["job_id"] for row in self.store.attempts() if row["status"] == "FAILED_NO_RETRY"
            and row["receipt"].get("probe_processes_absent") is True and row["receipt"].get("deadline_expired") is True}
        for evidence in observation["jobs"]:
            if evidence["job_id"] in reconciled:
                evidence["state"] = "TERMINAL_RECONCILED_NO_RETRY"
        return observation

    def reconcile(self):
        for attempt in self.store.active():
            try:
                receipt = self.host.reconcile(attempt["intent"])
                self.store.update_attempt(attempt["job_id"], receipt["status"], receipt)
                if receipt.get("pause_reason"):
                    self.store.pause(receipt["pause_reason"])
            except runtime.SourceEpochPending:
                continue
            except Exception as error:
                self.store.pause("READ_ONLY_RECONCILIATION_FAILED:" + type(error).__name__)

    def cycle(self, rows, references, capsules, execute=False):
        self.store.ingest(rows, references)
        previous = self.store.get_meta("capsules") or {}
        rules.require(all(capsules.get(key) == value for key, value in previous.items()), "registered_source_capsule_changed_review_required")
        if previous != capsules:
            with self.store.transaction():
                self.store.set_meta("capsules", capsules)
                self.store.event("CAPSULES_ADDED", dict(count=len(capsules), registry_sha256=rules.digest(capsules)))
        for evidence in self.history:
            self.store.prior_attempt(evidence["source_key"], evidence)
        report = select(self.store, capsules, self.policy)
        if not execute or self.store.active() or self.store.get_meta("pause"):
            return report
        self.current_observation()
        report = select(self.store, capsules, self.policy)
        entry = report["selected"]
        if entry is None:
            return report
        capsule = capsules[rules.source_key(entry)]
        self.host.verify_capsule(entry, capsule)
        observation = self.current_observation()
        if any(row["source_key"] == entry["key"] for row in self.store.attempts()):
            return select(self.store, capsules, self.policy)
        try:
            plan = rules.proposal(entry, capsule, self.policy, observation, time.time())
        except ValueError as error:
            if str(error) not in {"lane_occupied_no_displacement", "original_claim_still_held", "unreconciled_external_job"}:
                raise
            report["waiting_for_lane"] = str(error)
            return report
        self.store.record_intent(plan)
        try:
            receipt = self.host.launch(plan)
            self.store.update_attempt(plan["job_id"], "DISPATCHED", receipt)
        except Exception as error:
            self.store.update_attempt(plan["job_id"], "RECONCILING", dict(error_type=type(error).__name__,
                no_retry=True, launch_outcome="AMBIGUOUS_OR_DENIED"))
            self.store.pause("ONE_SHOT_CALL_FAILED_OR_AMBIGUOUS_NO_RETRY")
        return select(self.store, capsules, self.policy)


def summary(report):
    return dict(status="INACTIVE_OFFLINE_CANDIDATE" if not report.get("run_mode") else "FOREGROUND_CANDIDATE",
        retained=report["retained"], pending=report["pending"],
        dispositions=dict(sorted(Counter(row["status"] for row in report["dispositions"]).items())),
        selected_key=report["selected"]["key"] if report["selected"] else None,
        active=[dict(job_id=row["job_id"], status=row["status"]) for row in report["active"]],
        pause=report["pause"], waiting_for_lane=report.get("waiting_for_lane"),
        source_validation_pending=report.get("source_validation_pending"),
        boot_installation="BLOCKED_UNINSTALLED", credential_bootstrap="UNVERIFIED", model_parent_feedback=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--policy", type=Path, default=WORKER / "policy.json")
    parser.add_argument("--enrollment", type=Path, action="append", required=True)
    parser.add_argument("--capsules", type=Path, default=WORKER / "capsules.json")
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--activation", type=Path)
    parser.add_argument("--freeze", type=Path, default=WORKER / "SOURCE_FREEZE.json")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    policy = runtime.read(args.policy)
    rules.validate_policy(policy)
    if args.run:
        rules.require(args.activation is not None, "main_review_activation_required_not_per_experiment_ratification")
        activation(runtime.read(args.activation), policy, args.freeze, time.time(), args.capsules)
    with singleton(args.state):
        store = Store(args.state, policy)
        try:
            store.verify_events()
            queue = Queue(store, policy, LocalHost(policy) if args.run else None, runtime.read(WORKER / "history.json")["attempts"])
            last_summary = None
            while True:
                if args.run:
                    queue.reconcile()
                try:
                    if args.run:
                        activation(runtime.read(args.activation), policy, args.freeze, time.time(), args.capsules)
                        rules.require(runtime.read(args.policy) == policy, "policy_changed_requires_explicit_rebind")
                    report = queue.cycle(*inputs(args.enrollment, args.capsules), execute=args.run)
                except runtime.SourceEpochPending as error:
                    report = select(store, store.get_meta("capsules") or {}, policy)
                    report["source_validation_pending"] = error.progress
                except Exception as error:
                    store.pause("ADMISSION_OR_INPUT_FAILED:" + type(error).__name__ + ":" + str(error)[:160])
                    report = select(store, store.get_meta("capsules") or {}, policy)
                report["run_mode"] = args.run
                compact = summary(report)
                if compact != last_summary:
                    print(rules.canonical(compact), flush=True)
                    last_summary = compact
                    if args.report:
                        temporary = args.report.with_suffix(".tmp")
                        temporary.write_text(rules.canonical(report) + "\n")
                        temporary.replace(args.report)
                if args.check or args.once:
                    return 2 if store.get_meta("pause") else 0
                time.sleep(0.1 if report.get("source_validation_pending") else 10)
        finally:
            store.close()


if __name__ == "__main__":
    raise SystemExit(main())
