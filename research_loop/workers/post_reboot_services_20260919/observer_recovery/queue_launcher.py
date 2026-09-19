"""Resume the unchanged CPU enrollment reader with fresh, lock-bound state."""

from contextlib import ExitStack
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from collector import identity, save, utc
from supervisor import process_record, require_host

REPO = HERE.parent.parents[2]
END = 1790791170


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(reference):
    path = Path(reference["path"])
    if not path.is_absolute():
        path = REPO / path
    if path.is_symlink() or checksum(path) != reference["sha256"]:
        raise ValueError("frozen_source_or_registration_changed")
    return path


def driver_module(bindings):
    path = checked(bindings["driver"])
    specification = importlib.util.spec_from_file_location("preserved_enrollment_driver", path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def verify_bindings(bindings):
    if bindings["deadline_unix"] != END:
        raise ValueError("existing_enrollment_deadline_only")
    for reference in bindings["provenance"] + [bindings["driver"], bindings["reader"]]:
        checked(reference)
    lease = json.loads(checked(bindings["lease_evidence"]).read_bytes())
    if lease["deadline_unix"] != END:
        raise ValueError("source_lease_mismatch")
    targets = []
    for ledger in bindings["ledgers"]:
        registration = json.loads(checked(ledger["registration"]).read_bytes())
        targets.extend(registration["targets"])
    if len(targets) != 16 or len({target["journal_id"] for target in targets}) != 16:
        raise ValueError("exact_sixteen_registered_journals_required")
    for target in targets:
        wrapper = REPO / "gpu" / target["wrapper"]
        if checksum(wrapper) != bindings["wrappers_sha256"][target["wrapper"]]:
            raise ValueError("registered_wrapper_changed")
    return targets


def write_once(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + "." + str(os.getpid()) + ".next")
    with temporary.open("xb") as output:
        os.fchmod(output.fileno(), 0o600)
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()
    return dict(path=str(path), sha256=hashlib.sha256(payload).hexdigest())


def prepare_run(bindings):
    targets = verify_bindings(bindings)
    driver = driver_module(bindings)
    run = HERE / "runs" / str(time.time_ns())
    baseline_path = HERE / "BASELINE.json"
    with ExitStack() as locks:
        for ledger in bindings["ledgers"]:
            lock = locks.enter_context(Path(ledger["output"]).joinpath("ENROLL.lock").open("r"))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        baseline = json.loads(baseline_path.read_bytes()) if baseline_path.exists() else None
        ledgers, counts = [], []
        for ledger in bindings["ledgers"]:
            checked(ledger["registration"])
            state_path = Path(ledger["output"]) / "private/STATE.json"
            payload = state_path.read_bytes()
            state = json.loads(payload)
            if baseline:
                reference = next(item for item in baseline["ledgers"] if item["name"] == ledger["name"])
                original = json.loads(checked(reference["state_snapshot"]).read_bytes())
                driver.verify_preserved(state, original)
            elif hashlib.sha256(payload).hexdigest() != ledger["initial_state_sha256"]:
                raise ValueError("initial_preserved_state_changed_requires_fresh_owner_review")
            snapshot = write_once(run / "private" / (ledger["name"] + "_STATE.json"), payload)
            ledgers.append(dict(name=ledger["name"], output=ledger["output"],
                registration=dict(path=str(checked(ledger["registration"])), sha256=ledger["registration"]["sha256"]),
                state_snapshot=snapshot, state_sha256=hashlib.sha256(payload).hexdigest()))
            counts.append(dict(name=ledger["name"], entries=len(state["entries"]), roots=len(state["cursors"])))
        if sum(row["entries"] for row in counts) < 1242 or sum(row["roots"] for row in counts) != 16:
            raise ValueError("preserved_enrollments_or_cursors_missing")
        if not baseline:
            save(baseline_path, dict(observed_utc=utc(), ledgers=ledgers, counts=counts,
                 total_references=sum(row["entries"] for row in counts), **identity()), exclusive=True)
        config = dict(repo=str(REPO), support_root=str(run), receipt_root=str(run),
            deadline_unix=END, driver_sha256=bindings["driver"]["sha256"],
            reader=dict(path=str(checked(bindings["reader"])), sha256=bindings["reader"]["sha256"]),
            ledgers=ledgers, wrappers_sha256=bindings["wrappers_sha256"])
        save(run / "CONFIG.private.json", config, exclusive=True)
        save(run / "PREPARED.json", dict(observed_utc=utc(), counts=counts,
            config_sha256=checksum(run / "CONFIG.private.json"),
            target_admission=[dict(life=target["label"], **driver.admission(target, time.time())) for target in targets],
            original_locks_held_during_snapshot=True, state_and_registration_rechecked_by_driver=True,
            original_ledger_paths_preserved=True, cursors_reset=False, new_evaluations=0,
            native_signals=[], **identity()), exclusive=True)
    return run


def main():
    os.umask(0o077)
    require_host()
    if time.time() >= END:
        return 0
    with (HERE / "QUEUE_LAUNCHER.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 75
        bindings = json.loads((HERE / "SOURCE_BINDINGS.json").read_bytes())
        try:
            run = prepare_run(bindings)
        except BlockingIOError:
            return 75
        stopping = False

        def stop(signum, frame):
            nonlocal stopping
            stopping = True

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        command = ["/usr/bin/python3", "-B", str(checked(bindings["driver"])), "--config", str(run / "CONFIG.private.json")]
        with (run / "driver.log").open("ab") as output:
            process = subprocess.Popen(command, cwd=REPO, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT)
            try:
                actual = process_record(process.pid)
                handle = dict(observed_utc=utc(), launcher=identity(), driver={key: value for key, value in actual.items() if key != "executable"},
                    run=str(run), config_sha256=checksum(run / "CONFIG.private.json"), deadline_unix=END,
                    service_role="CPU_ENROLLMENT_METADATA_ONLY", new_evaluations=0, backlog_dispatcher_started=False)
                save(run / "HOST_HANDLE.json", handle, exclusive=True)
                save(HERE / "RUN_LATEST.json", handle)
                while not stopping and time.time() < END:
                    try:
                        return process.wait(timeout=min(1, max(0.01, END - time.time())))
                    except subprocess.TimeoutExpired:
                        pass
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=1)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        save(HERE / "LAUNCH_ERROR.json", dict(observed_utc=utc(), error_type=type(error).__name__, new_evaluations=0))
        raise
