"""Foreground host-local daemon supervisor; never installs or enables services."""

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from collector import HERE, REPO, identity, save, utc


REGISTRY = HERE / "services.d"
MAX_UNTIL = 1790791200.0
EXPECTED_HOST = "nvl-ai"
EXPECTED_UID = 158984
KINDS = {"collector", "parent", "probe", "approval_watch", "queue"}
SECRET_ARGUMENT = re.compile(r"(?i)(api[-_]?key|access[-_]?token|password|passwd|secret|authorization|bearer|sk-[A-Za-z0-9]{12}|://[^/\s]+:[^/\s]+@)")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_path(value):
    require(isinstance(value, str), "repository_path_required")
    path = Path(value)
    path = path if path.is_absolute() else REPO / path
    require(path.resolve().is_relative_to(REPO.resolve()), "repository_scope_required")
    return path.resolve()


def validate(entry):
    require(isinstance(entry, dict), "entry_object_required")
    require(re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", entry.get("name", "")) is not None, "safe_service_name_required")
    require(type(entry.get("enabled")) is bool, "explicit_enabled_boolean_required")
    if not entry["enabled"]:
        return entry
    require(entry.get("kind") in KINDS, "cpu_daemon_kind_required")
    for field in ("local_daemon_only", "restart_safe", "self_enforces_lease", "foreground",
                  "shutdown_leaves_child_natives_running"):
        require(entry.get(field) is True, "owner_must_attest_" + field)
    require(entry.get("child_native") is False, "child_natives_forbidden")
    require(entry.get("owner") and entry.get("approval_scope"), "owner_and_existing_scope_required")
    require("env" not in entry and "environment" not in entry, "no_environment_secrets_in_registry")
    if entry["kind"] == "approval_watch":
        require(entry.get("watch_only") is True, "watcher_must_not_approve_or_ratify")
    argv = entry.get("argv")
    require(isinstance(argv, list) and len(argv) >= 2 and all(isinstance(value, str) and value and "\0" not in value for value in argv), "explicit_nonempty_argv_required")
    require(all(not SECRET_ARGUMENT.search(value) for value in argv), "credentials_must_be_resolved_at_runtime")
    require(Path(argv[0]).is_absolute() and os.access(argv[0], os.X_OK), "absolute_executable_required")
    require(Path(argv[0]).name in {"python", "python3", "bash", "sh"}, "reviewed_script_interpreter_required")
    script_index = 1
    while script_index < len(argv) and argv[script_index] in {"-B", "-u"}:
        script_index += 1
    require(script_index < len(argv) and not argv[script_index].startswith("-"), "no_inline_shell_or_python_commands")
    cwd = repository_path(entry["cwd"])
    require(cwd.is_dir(), "existing_working_directory_required")
    script = Path(argv[script_index])
    script = script if script.is_absolute() else cwd / script
    source = repository_path(entry["entrypoint"])
    require(script.resolve() == source and source.is_file(), "argv_must_execute_bound_source")
    require(digest(source) == entry["entrypoint_sha256"], "source_digest_changed_requires_owner_update")
    until = entry.get("until_unix")
    require(type(until) in {int, float} and math.isfinite(until) and 0 < until <= MAX_UNTIL, "finite_existing_fleet_horizon_required")
    evidence = entry["lease_evidence"]
    lease_path = repository_path(evidence["path"])
    require(digest(lease_path) == evidence["sha256"], "lease_evidence_digest_mismatch")
    document = json.loads(lease_path.read_text())
    pointer = evidence["json_pointer"]
    require(pointer.startswith("/"), "absolute_json_pointer_required")
    for field in pointer.split("/")[1:]:
        key = field.replace("~1", "/").replace("~0", "~")
        document = document[int(key)] if isinstance(document, list) else document[key]
    require(type(document) in {float, int} and math.isfinite(document) and until <= document, "cannot_extend_source_lease")
    if entry.get("singleton_lock"):
        repository_path(entry["singleton_lock"])
    return dict(entry, cwd=str(cwd))


def require_host():
    require(os.uname().nodename == EXPECTED_HOST and os.getuid() == EXPECTED_UID, "expected_host_and_uid_required")
    require(Path("/proc/1/comm").read_text().strip() == "systemd", "host_pid_namespace_required_not_sandbox")


def process_record(pid):
    root = Path("/proc") / str(pid)
    require(root.stat().st_uid == os.getuid(), "same_user_process_required")
    fields = (root / "stat").read_text().rsplit(") ", 1)[1].split()
    command = (root / "cmdline").read_bytes()
    require(fields[0] not in {"Z", "X"}, "live_process_required")
    return dict(pid=pid, start_ticks=fields[19], command_sha256=hashlib.sha256(command).hexdigest(),
                argv=[os.fsdecode(value) for value in command.rstrip(b"\0").split(b"\0")],
                executable=os.readlink(root / "exe"))


def matching_processes(argv):
    result = []
    executable = str(Path(argv[0]).resolve())
    for root in Path("/proc").iterdir():
        if not root.name.isdecimal():
            continue
        try:
            process = process_record(int(root.name))
            if process["argv"][1:] == argv[1:] and process["executable"] == executable:
                result.append({key: value for key, value in process.items() if key not in {"argv", "executable"}})
        except (OSError, ValueError, IndexError):
            continue
    return result


def lock_busy(path):
    if not path.exists():
        return False
    with path.open("r") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
    return False


def record_event(name, status, **fields):
    record = dict(observed_utc=utc(), name=name, status=status, **fields)
    save(HERE / "receipts" / ("SUPERVISOR_" + str(time.time_ns()) + ".json"), record, exclusive=True)


class Supervisor:
    def __init__(self):
        self.children = {}
        self.restart_after = {}
        self.failures = {}
        self.last_status = {}

    def tick(self, entries):
        now = time.time()
        statuses = []
        for name, (process, launch_entry) in list(self.children.items()):
            if process.poll() is not None:
                failures = self.failures.get(name, 0) + 1
                self.failures[name] = failures
                self.restart_after[name] = now + min(300, 5 * 2 ** min(failures, 6))
                record_event(name, "OWNED_DAEMON_EXITED", returncode=process.returncode)
                del self.children[name]
            elif now >= launch_entry["until_unix"]:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                record_event(name, "OWNED_LOCAL_DAEMON_LEASE_ENDED", pid=process.pid,
                             native_signals=[], process_group_signals=[])
                del self.children[name]
        for entry in entries:
            name = entry["name"]
            status = dict(name=name)
            if not entry["enabled"]:
                status["status"] = "DISABLED_AWAITING_OWNER_ARGV"
            elif now >= entry["until_unix"]:
                status["status"] = "LEASE_EXPIRED_NO_LAUNCH"
            else:
                matches = matching_processes(entry["argv"])
                status["matches"] = matches
                if len(matches) > 1:
                    status["status"] = "DUPLICATE_EXISTING_PROCESSES_NO_ACTION"
                elif matches:
                    status["status"] = "RUNNING_OWNED" if name in self.children else "RUNNING_ADOPTED_NO_SIGNALS"
                elif name in self.children:
                    status["status"] = "OWNED_PROCESS_COMMAND_CHANGED_NO_DUPLICATE"
                elif entry.get("singleton_lock") and lock_busy(repository_path(entry["singleton_lock"])):
                    status["status"] = "EXISTING_SINGLETON_LOCK_HELD_NO_LAUNCH"
                elif now < self.restart_after.get(name, 0):
                    status["status"] = "RESTART_BACKOFF"
                elif time.time() >= entry["until_unix"]:
                    status["status"] = "LEASE_EXPIRED_DURING_DISCOVERY_NO_LAUNCH"
                else:
                    try:
                        process = subprocess.Popen(entry["argv"], cwd=entry["cwd"],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
                        self.children[name] = (process, dict(entry))
                        status.update(status="STARTED_LOCAL_DAEMON", pid=process.pid)
                    except OSError as error:
                        status.update(status="START_FAILED", error_type=type(error).__name__)
                        self.restart_after[name] = now + 60
            statuses.append(status)
            if self.last_status.get(name) != status:
                record_event(name, status["status"], evidence={key: value for key, value in status.items() if key not in {"name", "status"}})
                self.last_status[name] = status
        return statuses


def load_entries(registry):
    entries, errors, seen = [], [], set()
    for path in sorted(registry.glob("*.json")):
        try:
            require(not path.is_symlink() and path.stat().st_size <= 65536, "bounded_regular_manifest_required")
            entry = validate(json.loads(path.read_text()))
            require(entry["name"] == path.stem and entry["name"] not in seen, "unique_filename_and_service_name_required")
            seen.add(entry["name"])
            entries.append(entry)
        except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
            errors.append(dict(file=path.name, status="INVALID_MANIFEST_NOT_LAUNCHED", error_type=type(error).__name__))
    return entries, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true")
    arguments = parser.parse_args()
    entries, errors = load_entries(REGISTRY)
    if arguments.validate:
        print(json.dumps(dict(entries=[dict(name=entry["name"], enabled=entry["enabled"]) for entry in entries], errors=errors)))
        return int(bool(errors))
    require_host()
    with (HERE / "SUPERVISOR.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Supervisor already running; no duplicate launched.", flush=True)
            return 75
        running = True

        def stop(signum, frame):
            nonlocal running
            running = False

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        supervisor = Supervisor()
        record_event("supervisor", "STARTED_FOREGROUND_NO_SERVICE_INSTALLATION", **identity())
        while running and time.time() < MAX_UNTIL:
            entries, errors = load_entries(REGISTRY)
            statuses = supervisor.tick(entries)
            save(HERE / "SUPERVISOR_HEARTBEAT.json", dict(observed_utc=utc(), services=statuses,
                errors=errors, boot_enabled=False, installation_status="BLOCKED_UNINSTALLED",
                until_unix=MAX_UNTIL, **identity()))
            time.sleep(max(0, min(10, MAX_UNTIL - time.time())))
        if time.time() >= MAX_UNTIL:
            supervisor.tick([])
        record_event("supervisor", "EXITED_CHILD_NATIVES_UNTOUCHED", **identity())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
