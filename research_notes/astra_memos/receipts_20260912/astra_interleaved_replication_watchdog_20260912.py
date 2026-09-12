"""Bound seed1/2 controller-only replication watcher. Main launches; no worker/GPU cleanup claim."""
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
import xml.etree.ElementTree as ET


RUNNER = Path("/tmp/astra_interleaved_memory_replication_20260912.py")
RUNNER_SHA = "dc92b9d18f1fc7e8b9907f304e366de34a5e12340223f8dd17506e007093065f"
SOURCE_ID = "22b7e528f6f62358981ed2264d30ee7242926160"
SCHEMA = "INTERLEAVED_MEMORY_REPLICATION_V1"
SECONDS, CLEANUP, CUSTODY, LEASE_MARGIN = 1800, 140, 300, 21600
POLL, POST_KILL_OBSERVE = .2, 5.
PARENT_PINS = {
    1: ["f2aaa20ab53b7cd3221580f3098da68f0381bd6a120967b6cfa085eedb769252",
        "248fee8d701b435c334aafd2551b93ef6da25de137ac71510fa5bb5c49129335",
        "f5cc61263806bff26d7b77ca267b70b21507bf2e1feeea78dc4eb510675a7e7a"],
    2: ["54e44fc9e7193405b85b4a49b44c73ba50e3b075832b406a9538df77d0ad0fae",
        "fc5f2337f981ce71fe43a931bcff530019b843936f69104d6883cbb00001599c",
        "eea6c81b77aa745e440a68503a9984d52264b8b02932c512baa27dda368ba825"],
}
PROGRESSION = dict(owner="Main", qualifying_arm="FOUR_VIEW", dev_memory_min=15, exact_memory_min=15,
    dev_habit_min=30, dev_act_min=31, each_lexical_family_min=15, eligible_next_seeds=[1, 2],
    single_scores_irrelevant=True, decide_only_after_both_technical_complete=True,
    automatic_progression=False, gate_evaluated_by_wrapper=False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def unaliased(path):
    path = Path(path).expanduser().absolute()
    require(".." not in path.parts, "parent traversal forbidden")
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


def absolute_path(value):
    require(isinstance(value, str) and value and "\0" not in value and Path(value).is_absolute(),
        "absolute nonempty path required")
    path = unaliased(value)
    require(str(path) == value, "canonical path spelling required")
    return path


def hash_string(value):
    return isinstance(value, str) and len(value) == 64 and all(letter in "0123456789abcdef" for letter in value)


def load_contract(root, plan_sha, launch_sha):
    root = absolute_path(str(root))
    require(root.is_dir(), "existing prepared run root required")
    require(hash_string(plan_sha) and hash_string(launch_sha), "explicit plan/launch SHA256 required")
    pins = {}

    def pinned(path, checksum):
        path = absolute_path(str(path))
        require(hash_string(checksum), "invalid custody SHA256")
        payload = read_bytes(path)
        require(sha(payload) == checksum, "custody hash differs: " + str(path))
        require(str(path) not in pins or pins[str(path)] == checksum, "conflicting custody pins")
        pins[str(path)] = checksum
        return payload

    plan_path, launch_path = root / "plan.json", root / "launch/launch.json"
    plan = decode(pinned(plan_path, plan_sha))
    launch = decode(pinned(launch_path, launch_sha))
    pinned(RUNNER, RUNNER_SHA)
    seed = plan["seed"]
    require(type(seed) is int and seed in (1, 2), "replication seeds1/2 only")
    source = absolute_path(plan["source_root"])
    require(source.is_dir() and source.name == SOURCE_ID and plan["source_commit"] == SOURCE_ID and
        plan["schema"] == SCHEMA and plan["root"] == str(root) and
        plan["source_hashes"]["interleaved_replication"] == RUNNER_SHA, "wrong frozen source/root/schema")
    device = plan["device"]
    require(isinstance(device, str) and device and device.isascii() and device.isdecimal() and
        str(int(device)) == device and launch["device"] == device, "single declared device required")
    require(plan["pair_seconds"] == SECONDS and plan["cleanup_seconds"] == CLEANUP and
        plan["external_custody_seconds"] == CUSTODY and plan["lease_margin_seconds"] == LEASE_MARGIN and
        plan["config"]["seed"] == seed and type(plan["config"]["seed"]) is int and
        plan["arm_order"] == ["SINGLE_VIEW", "FOUR_VIEW"] and
        plan["panels"] == dict(dev=48, exact=16, lexical=48) and plan["total_calls"] == 224 and
        plan["calls_per_arm"] == 112 and plan["confirmation_calls"] == 0 and
        plan["reduce_only_after_both_captures"] is True and plan["outcome_selective_skips"] is False and
        plan["progression"] == PROGRESSION, "fixed replication bounds/panels/order differ")
    require(launch["root"] == str(root) and launch["source"] == str(source) and
        type(launch["seed"]) is int and launch["seed"] == seed and
        launch["plan_sha256"] == plan_sha and launch["script_sha256"] == RUNNER_SHA and
        launch["controller_bound_seconds"] == SECONDS and launch["external_collection_margin_seconds"] == CUSTODY and
        launch["generation_calls"] == 224, "wrong launch/plan contract")
    interpreter = plan["python"]
    require(isinstance(interpreter, str) and Path(interpreter).is_absolute(), "absolute native executable spelling required")
    expected = [interpreter, "-B", str(RUNNER), "run", "--source-root", str(source), "--runroot", str(root), "--allow-gpu"]
    require(launch["command"] == expected and all(isinstance(value, str) and value and "\0" not in value for value in expected),
        "exact controller command required; do not resolve venv executable")
    parentroot, materialroot = absolute_path(plan["parentroot"]), absolute_path(plan["materialroot"])
    require(parentroot.is_dir() and materialroot.is_dir() and root.parent == materialroot.parent,
        "prepared run must be beside material")
    protected_roots = [source, parentroot, materialroot, absolute_path(plan["material_parentroot"]),
        absolute_path(plan["model"]), absolute_path(plan["seed0_gate"]["seed0_root"])]
    require(all(root != protected and protected not in root.parents and root not in protected.parents
        for protected in protected_roots), "wrong run/input root")
    parent_paths = [parentroot / "plan.json", parentroot / "fit_teach/verified.json", parentroot / "readouts/teach/plan.json"]
    require(plan["parent_pin"] == PARENT_PINS[seed] and launch["parent_plan_sha256"] == plan["parent_pin"][0],
        "not original corresponding seed parent pins")
    parent_payloads = [pinned(path, checksum) for path, checksum in zip(parent_paths, plan["parent_pin"], strict=True)]
    require(all(plan["parent"]["provenance"][str(path)] == checksum
        for path, checksum in zip(parent_paths, plan["parent_pin"], strict=True)), "parent provenance differs")
    parent_adapter = str(parentroot / "fit_teach/adapter")
    original, fit, readout = [decode(payload) for payload in parent_payloads]
    require(type(original["config"]["seed"]) is int and original["config"]["seed"] == seed and
        plan["parent"]["parent"] == parent_adapter and fit["adapter"] == parent_adapter and
        readout["adapter"] == parent_adapter and plan["parent"]["readout"] == readout and
        fit["adapter_files"] == readout["adapter_files"] == plan["parent"]["parent_files"],
        "original parent/readout identity differs")
    gate = plan["seed0_gate"]
    require(hash_string(gate["sha256"]) and launch["seed0_gate_sha256"] == gate["sha256"] and
        gate["owner"] == "Main" and gate["decision"] == "ALLOW_SEEDS_1_2" and
        gate["raw_review_verdict"] == "PASS" and gate["criteria"] == PROGRESSION, "explicit seed0 gate identity required")
    gate_record = decode(pinned(gate["path"], gate["sha256"]))
    require(gate_record["schema"] == "INTERLEAVED_SEED0_MAIN_GATE_V1" and gate_record["eligible_seeds"] == [1, 2] and
        all(gate_record[key] == gate[key] for key in ("owner", "decision", "raw_review_verdict", "criteria")),
        "seed0 gate receipt differs")
    require(gate_record["seed0_plan"]["path"] == str(Path(gate["seed0_root"]) / "plan.json") and
        gate_record["seed0_terminal"]["path"] == str(Path(gate["seed0_root"]) / "run/terminal.json"),
        "seed0 gate root differs")
    require(gate["evidence_hashes"][gate["path"]] == gate["sha256"], "gate self pin differs")
    for key in ("seed0_plan", "seed0_terminal", "seed0_validation", "raw_review"):
        evidence = gate_record[key]
        require(gate["evidence_hashes"][evidence["path"]] == evidence["sha256"], "gate evidence binding differs")
    for path, checksum in gate["evidence_hashes"].items():
        pinned(path, checksum)
    pid, pgid, ticks = launch["pid"], launch["pgid"], launch["proc_start_ticks"]
    require(positive_int(pid) and pgid == pid and type(pgid) is int and type(ticks) is int and ticks > 0,
        "Main must pin PID==PGID and positive proc_start_ticks")
    started, effective = launch["controller_started_unix"], launch["effective_deadline"]
    require(all(finite(value) for value in (started, effective, plan["deadline"], plan["real_lease_end"])) and
        started > 0 and effective == started + SECONDS and effective <= plan["deadline"] and
        effective + CUSTODY <= plan["real_lease_end"] - LEASE_MARGIN,
        "full1800+300s before real lease minus6h required, never extended")
    reservation_path = root / "run/reservation.json"
    reservation = decode(pinned(reservation_path, launch["reservation_sha256"]))
    require(type(reservation["controller_pid"]) is int and reservation["controller_pid"] == pid and
        reservation["started"] == started and reservation["effective_deadline"] == effective and
        reservation["plan_sha256"] == plan_sha and reservation["device"] == device and
        type(reservation["seed"]) is int and reservation["seed"] == seed and
        reservation["real_lease_end"] == plan["real_lease_end"] and
        reservation["external_custody_deadline"] == effective + CUSTODY and reservation["continuous_reservation"] is True and
        finite(reservation["started_monotonic"]) and reservation["started_monotonic"] >= 0,
        "controller reservation/deadline differs from launch")
    gpu_path = root / "launch/gpu.xml"
    gpu_payload = read_bytes(gpu_path)
    gpu_uuid = launch["gpu"]["gpu_uuid"]
    require(isinstance(gpu_uuid, str) and gpu_uuid.startswith("GPU-") and len(gpu_uuid) > 4 and
        [node.text for node in ET.fromstring(gpu_payload).findall("gpu/uuid")] == [gpu_uuid], "GPU UUID evidence differs")
    pinned(gpu_path, sha(gpu_payload))
    contract = dict(root=str(root), source=str(source), seed=seed, device=device, gpu_uuid=gpu_uuid,
        parentroot=str(parentroot), materialroot=str(materialroot), parent_pin=plan["parent_pin"],
        seed0_gate_sha256=gate["sha256"], pid=pid, pgid=pgid, proc_start_ticks=ticks, command=expected,
        controller_started_unix=started, effective_deadline=effective, term_at=effective-CLEANUP,
        real_lease_end=plan["real_lease_end"], lease_cutoff=plan["real_lease_end"]-LEASE_MARGIN,
        external_custody_deadline=effective+CUSTODY, launch_path=str(launch_path), launch_sha256=launch_sha,
        reservation_path=str(reservation_path), reservation_sha256=launch["reservation_sha256"],
        plan_sha256=plan_sha, runner_sha256=RUNNER_SHA, immutable_hashes=pins,
        protected_roots=[str(root), *map(str, protected_roots)])
    assert_immutable(contract)
    return contract


def assert_immutable(contract):
    for path, checksum in contract["immutable_hashes"].items():
        require(sha(read_bytes(path)) == checksum, "immutable custody inputs changed; refuse signals: " + path)


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
    for value in contract["protected_roots"]:
        protected = absolute_path(value)
        require(out != protected and protected not in out.parents and out not in protected.parents,
            "external watch receipt directory required")
    require(all(out != Path(path) and out not in Path(path).parents for path in contract["immutable_hashes"]),
        "watch output overlaps custody input")
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
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--launch-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require("CUDA_VISIBLE_DEVICES" not in os.environ, "unset CUDA_VISIBLE_DEVICES; watchdog owns no GPU reservation")
    contract = load_contract(args.root, args.plan_sha256, args.launch_sha256)
    result = monitor(contract, args.out, Proc(), PidfdSignaler())
    print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
    raise SystemExit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
