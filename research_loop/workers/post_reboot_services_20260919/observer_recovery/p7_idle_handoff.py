"""One exact, idle CPU-parent handoff; no native or process-group signals."""

import fcntl
import hashlib
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
from supervisor import matching_processes, process_record, require_host, validate

OWNER = HERE.parent.parent / "post_reboot_c2_p7_20260919"
OLD_PID = 325545
OLD_START = "753409"
BOOT_ID = "80d71f45-6f0c-4479-b0e5-77a9611c793e"
OLD_ARGV = ["/usr/bin/python3", "-B", str(OWNER / "p7_restore.py")]
NEW_ARGV = ["/usr/bin/python3", "-B", str(OWNER / "p7_bounded.py")]
OLD_SHA = "9c52bae61046c8cd06a87274d29ff5220629a461020dffe5ef437269e5127e22"
NEW_SHA = "04e12726565d2e46df28ca7bdc3aea2909601dc2d8984ce9615c59154fa9871a"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_identity(actual, boot):
    require(boot == BOOT_ID and actual["pid"] == OLD_PID
            and actual["start_ticks"] == OLD_START and actual["argv"] == OLD_ARGV,
            "only_exact_authorized_cpu_parent_incarnation")


def observe():
    actual = process_record(OLD_PID)
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    verify_identity(actual, boot)
    root = Path("/proc") / str(OLD_PID)
    tasks = sorted((root / "task").iterdir())
    children = {task.name: task.joinpath("children").read_text().strip() for task in tasks}
    wchan = (root / "wchan").read_text().strip()
    return dict(process=actual, boot_id=boot, children=children, wchan=wchan,
                idle=wchan == "hrtimer_nanosleep" and len(tasks) == 1 and not any(children.values()),
                observed_utc=utc())


def lock_owners(paths):
    lines = Path("/proc/locks").read_text().splitlines()
    owners = []
    for path in paths:
        information = Path(path).stat()
        key = f"{os.major(information.st_dev):02x}:{os.minor(information.st_dev):02x}:{information.st_ino}"
        rows = [line.split() for line in lines if key in line.split() and "->" not in line.split()]
        require(len(rows) <= 1, "unambiguous_original_parent_lock")
        owners.append(int(rows[0][rows[0].index("FLOCK") + 3]) if rows else None)
    return owners


def snapshot_files():
    result = []
    total = 0
    for path in sorted((OWNER / "p7").rglob("*")):
        require(not path.is_symlink(), "regular_parent_ledger_only")
        if path.is_file():
            size = path.stat().st_size
            total += size
            require(total <= 268435456, "bounded_metadata_hash_inventory_required")
            result.append(dict(path=str(path), bytes=size, sha256=checksum(path)))
    return result


def verify_files(files):
    for item in files:
        require(checksum(item["path"]) == item["sha256"], "preexisting_parent_file_changed")


def approved_candidate():
    entry = json.loads((HERE.parent / "services.d/p7-parent.json").read_bytes())
    require(entry["enabled"] is False, "replacement_registry_must_stay_disabled_during_handoff")
    require(checksum(OWNER / "p7_restore.py") == OLD_SHA and checksum(OWNER / "p7_bounded.py") == NEW_SHA,
            "exact_main_approved_policy_and_logging_sources")
    entry.update(enabled=True, argv=NEW_ARGV, entrypoint=NEW_ARGV[-1], entrypoint_sha256=NEW_SHA)
    validate(entry)
    return entry


def wait_fresh_idle(deadline, lock_paths):
    saw_busy = False
    while time.monotonic() < deadline:
        sample = observe()
        if not sample["idle"]:
            saw_busy = True
        elif saw_busy:
            start = time.monotonic()
            time.sleep(0.1)
            if not observe()["idle"]:
                continue
            files = snapshot_files()
            if time.monotonic() - start >= 2:
                saw_busy = False
                continue
            sample = observe()
            if sample["idle"] and lock_owners(lock_paths) == [OLD_PID, OLD_PID]:
                return sample, files
        time.sleep(0.05)
    return None, None


def main():
    os.umask(0o077)
    require_host()
    with (HERE / "P7_HANDOFF.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        approved_candidate()
        require(len(matching_processes(OLD_ARGV)) == 1 and not matching_processes(NEW_ARGV),
                "one_predecessor_and_no_replacement_before_handoff")
        prior = json.loads((HERE / "PARENT_PREFLIGHT_20260919.json").read_bytes())
        lock_paths = [item["path"] for item in prior["p7"]["locks"]]
        observe()
        descriptor = os.pidfd_open(OLD_PID)
        try:
            observe()
            sample, files = wait_fresh_idle(time.monotonic() + 90, lock_paths)
            if sample is None:
                save(HERE / "P7_HANDOFF_DEFERRED.json", dict(observed_utc=utc(),
                    reason="no_fresh_unambiguous_idle_window", predecessor_left_live=True,
                    replacement_left_disabled=True, signals=[]), exclusive=True)
                return 2
            save(HERE / "P7_PRESERVED_FILES.json", dict(observed_utc=utc(), files=files), exclusive=True)
            save(HERE / "P7_HANDOFF_INTENT.json", dict(observed_utc=utc(), idle_observation=sample,
                approved_replacement_argv=NEW_ARGV, original_lock_paths=lock_paths,
                only_signal=dict(pid=OLD_PID, start_ticks=OLD_START, signal="SIGTERM", via="pidfd"),
                native_signals=[]), exclusive=True)
            approved_candidate()
            immediate = observe()
            require(immediate["idle"] and lock_owners(lock_paths) == [OLD_PID, OLD_PID],
                    "idle_gate_changed_no_signal_sent")
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            require(bool(select.select([descriptor], [], [], 10)[0]), "predecessor_not_exited_no_force_or_replacement")
        finally:
            os.close(descriptor)
        require(lock_owners(lock_paths) == [None, None], "original_parent_locks_not_released_no_replacement")
        verify_files(files)
        approved_candidate()
        require(not matching_processes(NEW_ARGV), "replacement_started_elsewhere_do_not_duplicate")
        with (HERE / "p7_bounded_runtime.log").open("ab") as output:
            process = subprocess.Popen(NEW_ARGV, cwd=HERE.parent.parents[2], stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            require(process.poll() is None, "replacement_exited_no_unbounded_fallback")
            if lock_owners(lock_paths) == [process.pid, process.pid]:
                break
            time.sleep(0.1)
        require(lock_owners(lock_paths) == [process.pid, process.pid], "replacement_lock_ownership_not_confirmed")
        verify_files(files)
        actual = process_record(process.pid)
        save(HERE / "P7_BOUNDED_STARTED.json", dict(observed_utc=utc(), boot_id=BOOT_ID,
            old_pid=OLD_PID, old_start_ticks=OLD_START, old_exited=True, new_process=actual,
            original_lock_owners=lock_owners(lock_paths), preexisting_files_preserved=len(files),
            only_cpu_predecessor_sigterm=True, native_signals=[], old_source_sha256=OLD_SHA,
            new_source_sha256=NEW_SHA, ready_for_registry_adoption=True), exclusive=True)
        print(json.dumps(dict(new_pid=actual["pid"], start_ticks=actual["start_ticks"],
            preserved_files=len(files), old_exited=True, native_signals=[])), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
