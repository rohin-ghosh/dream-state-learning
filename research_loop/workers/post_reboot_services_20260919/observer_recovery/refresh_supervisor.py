"""One-shot refresh of our CPU foreground supervisor, never a boot installer."""

import fcntl
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from collector import save, utc
from supervisor import MAX_UNTIL, digest, load_entries, process_record, require, require_host

OLD_PID = 311614
OLD_START = "717203"
BOOT_ID = "80d71f45-6f0c-4479-b0e5-77a9611c793e"
ARGV = ["/usr/bin/python3", "-B", str(HERE.parent / "supervisor.py")]


def check_identity(actual, boot):
    require(boot == BOOT_ID and actual["pid"] == OLD_PID
            and actual["start_ticks"] == OLD_START and actual["argv"] == ARGV,
            "exact_own_supervisor_incarnation_required")


def observe():
    actual = process_record(OLD_PID)
    check_identity(actual, Path("/proc/sys/kernel/random/boot_id").read_text().strip())
    return actual


def preserved_workers(preflight):
    records = {}
    for pid, expected in preflight["processes"].items():
        if int(pid) == OLD_PID:
            continue
        actual = process_record(int(pid))
        require(actual == expected, "worker_incarnation_changed_during_supervisor_refresh")
        records[pid] = actual
    return records


def main():
    os.umask(0o077)
    require_host()
    require(MAX_UNTIL == 1790791200, "corrected_existing_fleet_horizon_required")
    require(not (HERE / "SUPERVISOR_REFRESH_INTENT.json").exists(), "one_shot_refresh_already_attempted")
    with (HERE / "SUPERVISOR_REFRESH.lock").open("a") as guard:
        fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        preflight = json.loads((HERE / "FLEET_REFRESH_PREFLIGHT.json").read_bytes())
        preserved_workers(preflight)
        observe()
        descriptor = os.pidfd_open(OLD_PID)
        try:
            observe()
            environment = {}
            for item in Path(f"/proc/{OLD_PID}/environ").read_bytes().split(b"\0"):
                if item:
                    name, value = item.split(b"=", 1)
                    environment[os.fsdecode(name)] = os.fsdecode(value)
            require(bool(environment.get("NVIDIA_API_KEY")), "existing_runtime_provider_credential_required")
            unused, errors = load_entries(HERE.parent / "services.d")
            require(not errors, "valid_current_registry_required")
            source_sha = digest(HERE.parent / "supervisor.py")
            save(HERE / "SUPERVISOR_REFRESH_INTENT.json", dict(
                observed_utc=utc(), old_process=observe(), boot_id=BOOT_ID,
                source_sha256=source_sha, worker_signals=[], native_signals=[],
                credential_values_recorded=False, installation_status="BLOCKED_UNINSTALLED",
                reason="Non-material separation of existing fleet end from collector margin"), exclusive=True)
            observe()
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            require(bool(select.select([descriptor], [], [], 20)[0]), "supervisor_graceful_exit_not_confirmed")
        finally:
            os.close(descriptor)
        workers = preserved_workers(preflight)
        require(digest(HERE.parent / "supervisor.py") == source_sha, "supervisor_source_changed")
        process = subprocess.Popen(ARGV, cwd=str(HERE.parents[3]), env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True)
        environment.clear()
        deadline = time.monotonic() + 20
        heartbeat = {}
        while time.monotonic() < deadline:
            require(process.poll() is None, "replacement_supervisor_exited")
            try:
                heartbeat = json.loads((HERE.parent / "SUPERVISOR_HEARTBEAT.json").read_bytes())
            except (OSError, ValueError):
                heartbeat = {}
            if heartbeat.get("pid") == process.pid:
                break
            time.sleep(0.1)
        require(heartbeat.get("pid") == process.pid and not heartbeat.get("errors"), "replacement_heartbeat_not_confirmed")
        require(heartbeat["until_unix"] == MAX_UNTIL, "replacement_horizon_not_confirmed")
        workers = preserved_workers(preflight)
        receipt = dict(observed_utc=utc(), old_pid=OLD_PID, old_start_ticks=OLD_START,
            old_exited=True, only_own_cpu_supervisor_sigterm=True,
            new_process=process_record(process.pid), preserved_workers=workers,
            source_sha256=source_sha, credential_environment_inherited_in_memory=True,
            credential_values_recorded=False, worker_signals=[], native_signals=[],
            boot_enabled=False, installation_status="BLOCKED_UNINSTALLED",
            heartbeat_utc=heartbeat["observed_utc"], until_unix=MAX_UNTIL)
        save(HERE / "SUPERVISOR_REFRESHED.json", receipt, exclusive=True)
        print(json.dumps({key: receipt[key] for key in (
            "observed_utc", "old_exited", "new_process", "heartbeat_utc",
            "until_unix", "boot_enabled", "installation_status")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
