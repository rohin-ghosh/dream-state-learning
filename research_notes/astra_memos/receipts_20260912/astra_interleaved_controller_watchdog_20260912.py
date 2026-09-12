"""Independent controller-only deadline watcher. Main launches; no worker/GPU cleanup claim."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import select
import signal
import stat
import time


ROOT = Path("/localhome/local-rohing/astra_diagnostics/astra_interleaved_memory_replay_20260912_attempt1/fits_root0_attempt1")
SOURCE = "/localhome/local-rohing/astra_sources/22b7e528f6f62358981ed2264d30ee7242926160"
RUNNER = Path("/tmp/astra_interleaved_memory_pair_20260912.py")
RUNNER_SHA = "d100cb58296499c7cd6489d20e96528898f2e48b698147a97dae99fa38946bbe"
PLAN_SHA = "4cad487a53d0e992b896eb4324ff2de1adb24ccc176856de7043d1132c0ee388"
SECONDS, CLEANUP, POLL, POST_KILL_OBSERVE = 1800, 140, .2, 5.


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def unaliased(path):
    path = Path(path).expanduser().absolute()
    require(not any(part.is_symlink() for part in (path, *path.parents)), "aliased path forbidden")
    return path


def read_bytes(path):
    path = unaliased(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), "regular file required")
        payload = stream.read()
        after = os.fstat(stream.fileno())
        fields = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        require(fields(before) == fields(after) == fields(path.stat()), "file changed while reading")
    return payload


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def decode(payload):
    return json.loads(payload, object_pairs_hook=unique)


def write_new(path, value):
    payload = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    path = unaliased(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def positive_int(value):
    return type(value) is int and value > 1


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def load_contract(launch_path, launch_sha):
    launch_path = unaliased(launch_path)
    require(launch_path == ROOT / "launch/launch.json", "watch only the pinned Main run")
    launch_payload = read_bytes(launch_path)
    require(sha(launch_payload) == launch_sha, "launch receipt hash differs")
    plan_payload = read_bytes(ROOT / "plan.json")
    require(sha(plan_payload) == PLAN_SHA and sha(read_bytes(RUNNER)) == RUNNER_SHA, "frozen plan/runner changed")
    launch, plan = decode(launch_payload), decode(plan_payload)
    require(plan["root"] == str(ROOT) and plan["source_root"] == SOURCE and plan["seed"] == 0 and plan["device"] == "1" and
        plan["pair_seconds"] == SECONDS and plan["cleanup_seconds"] == CLEANUP and
        launch["root"] == str(ROOT) and launch["source"] == SOURCE and launch["device"] == "1" and
        launch["plan_sha256"] == PLAN_SHA and launch["script_sha256"] == RUNNER_SHA and
        launch["controller_bound_seconds"] == SECONDS, "wrong launch/plan contract")
    expected = [plan["python"], "-B", str(RUNNER), "run", "--source-root", SOURCE, "--runroot", str(ROOT), "--allow-gpu"]
    require(launch["command"] == expected and all(isinstance(value, str) and value and "\0" not in value for value in expected),
        "exact controller command required; do not resolve venv executable")
    pid, pgid, ticks = launch["pid"], launch["pgid"], launch["proc_start_ticks"]
    require(positive_int(pid) and pgid == pid and type(pgid) is int and type(ticks) is int and ticks > 0,
        "Main must pin PID==PGID and positive proc_start_ticks")
    started, effective = launch["controller_started_unix"], launch["effective_deadline"]
    require(all(finite(value) for value in (started, effective, plan["deadline"], plan["real_lease_end"])) and
        effective == started + SECONDS and effective <= plan["deadline"] and effective < plan["real_lease_end"] - 10,
        "exact1800s effective deadline required, never extended")
    reservation_path = ROOT / "run/reservation.json"
    reservation_payload = read_bytes(reservation_path)
    require(sha(reservation_payload) == launch["reservation_sha256"], "Main reservation pin differs")
    reservation = decode(reservation_payload)
    require(reservation["controller_pid"] == pid and reservation["started"] == started and reservation["effective_deadline"] == effective and
        reservation["plan_sha256"] == PLAN_SHA and reservation["device"] == "1" and reservation["real_lease_end"] == plan["real_lease_end"],
        "controller reservation/deadline differs from launch")
    return dict(pid=pid, pgid=pgid, proc_start_ticks=ticks, command=expected,
        controller_started_unix=started, effective_deadline=effective, term_at=effective-CLEANUP,
        launch_path=str(launch_path), launch_sha256=launch_sha, reservation_path=str(reservation_path),
        reservation_sha256=sha(reservation_payload), plan_sha256=PLAN_SHA, runner_sha256=RUNNER_SHA)


def assert_immutable(contract):
    require(sha(read_bytes(contract["launch_path"])) == contract["launch_sha256"] and
        sha(read_bytes(contract["reservation_path"])) == contract["reservation_sha256"] and
        sha(read_bytes(ROOT / "plan.json")) == PLAN_SHA and sha(read_bytes(RUNNER)) == RUNNER_SHA,
        "immutable custody inputs changed; refuse signals")


def parse_stat(payload):
    prefix, separator, tail = payload.rpartition(b")")
    require(separator and b"(" in prefix, "malformed proc stat")
    pid = int(prefix.split(b"(", 1)[0].strip())
    fields = tail.split()
    require(len(fields) >= 20 and len(fields[0]) == 1, "short proc stat")
    return dict(pid=pid, state=fields[0].decode("ascii"), pgid=int(fields[2]), proc_start_ticks=int(fields[19]))


class Proc:
    def read(self, pid):
        root = Path("/proc") / str(pid)
        try:
            before = parse_stat((root / "stat").read_bytes())
            command = (root / "cmdline").read_bytes()
            uid = root.stat().st_uid
            after = parse_stat((root / "stat").read_bytes())
        except (FileNotFoundError, ProcessLookupError):
            return None
        require(all(before[key] == after[key] for key in ("pid", "pgid", "proc_start_ticks")), "proc changed during identity read")
        if after["state"] != "Z":
            require(command.endswith(b"\0"), "unterminated/empty live cmdline")
        return dict(after, uid=uid, command=[os.fsdecode(part) for part in command[:-1].split(b"\0")] if command else [])


class PidfdSignaler:
    def __init__(self):
        require(callable(getattr(os, "pidfd_open", None)) and callable(getattr(signal, "pidfd_send_signal", None)),
            "Linux pidfd support required; no numeric-PID fallback")
        self.descriptor = None

    def open(self, pid):
        self.descriptor = os.pidfd_open(pid, 0)

    def exited(self):
        return bool(select.select([self.descriptor], [], [], 0)[0])

    def send(self, number):
        signal.pidfd_send_signal(self.descriptor, number, None, 0)

    def close(self):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None


def identity(snapshot, contract, uid):
    if snapshot is None:
        return "ABSENT"
    require(all(snapshot[key] == contract[key] for key in ("pid", "pgid", "proc_start_ticks")) and
        snapshot["uid"] == uid, "controller identity mismatch; no signal")
    if snapshot["state"] == "Z":
        return "ZOMBIE"
    require(snapshot["command"] == contract["command"], "controller cmdline mismatch; no signal")
    return "LIVE"


def monitor(contract, out, proc, signaler, clock=time, immutable=assert_immutable, uid=None):
    """Only the supplied pinned pidfd is signaled; dependencies injectable for CPU tests."""
    uid = os.getuid() if uid is None else uid
    out = unaliased(out)
    require(out != ROOT and ROOT not in out.parents and out not in ROOT.parents, "external watch receipt directory required")
    require(not out.exists(), "fresh watch directory required; preserve previous/orphan receipt")
    immutable(contract)
    wall, monotonic = clock.time(), clock.monotonic()
    require(finite(wall) and finite(monotonic), "invalid watchdog clock")
    term_mono = monotonic + max(0., contract["term_at"] - wall)
    kill_mono = monotonic + max(0., contract["effective_deadline"] - wall)
    out.mkdir(mode=0o700)
    write_new(out / "watch.json", dict(contract=contract, watchdog_pid=os.getpid(), watchdog_sha256=sha(read_bytes(__file__)),
        observed_start_unix=wall, late_start=wall >= contract["term_at"], uid=uid,
        term_monotonic=term_mono, kill_monotonic=kill_mono, signals="individual controller PID via pidfd only",
        worker_cleanup_verified=False, gpu_release_verified=False, budget_extended=False))
    sent, opened, kill_observed_until = [], False, None
    terminal = None
    try:
        while True:
            snapshot = proc.read(contract["pid"])
            state = identity(snapshot, contract, uid)
            if state in ("ABSENT", "ZOMBIE"):
                terminal = dict(status="CONTROLLER_EXIT_OBSERVED", observation=state, success=True)
                break
            if not opened:
                try:
                    signaler.open(contract["pid"])
                except ProcessLookupError:
                    terminal = dict(status="CONTROLLER_EXIT_OBSERVED", observation="EXIT_DURING_PIDFD_OPEN", success=True)
                    break
                opened = True
                continue
            if signaler.exited():
                terminal = dict(status="PINNED_PIDFD_EXIT_OBSERVED", observation="PIDFD_EXIT", success=True)
                break
            now, mono = clock.time(), clock.monotonic()
            kill_due = now >= contract["effective_deadline"] or mono >= kill_mono
            term_due = now >= contract["term_at"] or mono >= term_mono
            action = "kill" if kill_due and "kill" not in sent else "term" if term_due and not sent else None
            if action is not None:
                immutable(contract)
                current = proc.read(contract["pid"])
                if identity(current, contract, uid) != "LIVE" or signaler.exited():
                    continue
                number = signal.SIGKILL if action == "kill" else signal.SIGTERM
                event = dict(pid=contract["pid"], pgid=contract["pgid"], proc_start_ticks=contract["proc_start_ticks"],
                    command=contract["command"], signal=int(number), signal_name=number.name,
                    reason="HARD1800S_DEADLINE" if action == "kill" else "CLEANUP140S_BOUNDARY",
                    observed_unix=now, observed_monotonic=mono, effective_deadline=contract["effective_deadline"],
                    deadline_lateness_seconds=max(0., now-(contract["effective_deadline"] if action == "kill" else contract["term_at"])),
                    wall_deadline_reached=now >= (contract["effective_deadline"] if action == "kill" else contract["term_at"]),
                    monotonic_deadline_reached=mono >= (kill_mono if action == "kill" else term_mono),
                    mechanism="pidfd_send_signal_individual_controller", budget_extended=False)
                write_new(out / (action + "-intent.json"), event)
                sent.append(action)
                try:
                    signaler.send(number)
                    outcome = "SENT_NOT_PROOF_OF_EXIT"
                except ProcessLookupError:
                    outcome = "NOT_SENT_PROCESS_EXITED"
                except Exception as error:
                    write_new(out / (action + "-result.json"), dict(outcome="SIGNAL_FAILED", signal=int(number),
                        observed_unix=clock.time(), error=dict(type=type(error).__name__, message=str(error))))
                    raise
                write_new(out / (action + "-result.json"), dict(outcome=outcome, signal=int(number), observed_unix=clock.time()))
                if action == "kill":
                    kill_observed_until = clock.monotonic() + POST_KILL_OBSERVE
                continue
            if kill_observed_until is not None and mono >= kill_observed_until:
                terminal = dict(status="CONTROLLER_STILL_PRESENT_AFTER_KILL", observation=state, success=False)
                break
            next_boundary = kill_observed_until if kill_observed_until is not None else kill_mono if sent else term_mono
            clock.sleep(max(.001, min(POLL, next_boundary - mono)))
    except BaseException as error:
        terminal = dict(status="WATCHDOG_FAILED_CLOSED", success=False, error=dict(type=type(error).__name__, message=str(error)))
    finally:
        try:
            signaler.close()
        except Exception as error:
            terminal = dict(status="WATCHDOG_CLOSE_FAILED", success=False, error=dict(type=type(error).__name__, message=str(error)))
        terminal = dict(terminal or dict(status="WATCHDOG_FAILED_CLOSED", success=False), signals_attempted=sent,
            observed_end_unix=clock.time(), effective_deadline=contract["effective_deadline"],
            launch_sha256=contract["launch_sha256"], budget_extended=False,
            worker_cleanup_verified=False, gpu_release_verified=False,
            scope="controller only; Main must separately verify all workers and full GPU release")
        write_new(out / "terminal.json", terminal)
    return terminal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launch", type=Path, default=ROOT / "launch/launch.json")
    parser.add_argument("--launch-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require("CUDA_VISIBLE_DEVICES" not in os.environ, "unset CUDA_VISIBLE_DEVICES; watchdog owns no GPU reservation")
    contract = load_contract(args.launch, args.launch_sha256)
    result = monitor(contract, args.out, Proc(), PidfdSignaler())
    print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
    raise SystemExit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
