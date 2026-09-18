"""One local C0 child session and separate once-only, observed release.

No work occurs on import. Main supplies allocation/queue coordination; this
module neither allocates hardware nor retries work nor contacts another host.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_zero_fit_dev as driver


SCHEMA = "pcfl.zero_fit_outer.v2"
PROC = Path("/proc")
COMMAND = Path(__file__).with_name("astra_pcfl_zero_fit_command.py").resolve()
IDENTITY_FIELDS = {"pid", "pgid", "sid", "start_ticks", "boot_id", "uid"}
ALLOCATION_FIELDS = {"schema", "gpu_index", "gpu_uuid", "boot_id", "uid", "python",
                     "queue_dir", "queue_mode", "queue_allowlist", "coordination_owners",
                     "lease_end", "lease_margin_seconds", "outer_sha256", "service_exceptions"}
SERVICE_FIELDS = {"role", "identity", "ppid", "comm", "cmdline_sha256", "cgroup"}
require = driver.require


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(driver.canonical(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def remaining(deadline, maximum=None):
    duration = deadline - time.monotonic()
    require(duration > 0, "outer deadline exhausted")
    return duration if maximum is None else min(duration, maximum)


def file_hash(path, deadline=None):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while True:
            if deadline is not None:
                remaining(deadline)
            block = stream.read(1024 * 1024)
            if not block:
                break
            result.update(block)
    return result.hexdigest()


def boot_id():
    return (PROC / "sys/kernel/random/boot_id").read_text().strip()


def identity(pid):
    path = PROC / str(pid)
    fields = (path / "stat").read_text().rsplit(")", 1)[1].split()
    return {"pid": pid, "pgid": int(fields[2]), "sid": int(fields[3]),
            "start_ticks": int(fields[19]), "boot_id": boot_id(), "uid": path.stat().st_uid}


def _identity_schema(value):
    require(type(value) is dict and set(value) == IDENTITY_FIELDS, "process identity fields")
    require(all(type(value[key]) is int and value[key] >= (1 if key != "uid" else 0)
                for key in ("pid", "pgid", "sid", "start_ticks", "uid")), "typed process identity")
    require(type(value["boot_id"]) is str and value["boot_id"], "boot identity")


def _service_expectations(allocation):
    records = allocation["service_exceptions"]
    require(type(records) is list and len(records) in (0, 2), "service exceptions require zero or one complete init pair")
    expected = {}
    for record in records:
        require(type(record) is dict and set(record) == SERVICE_FIELDS, "service exception fields")
        _identity_schema(record["identity"])
        member = record["identity"]
        require(record["role"] in ("user_manager", "pam_helper") and record["role"] not in expected,
                "unique manager/helper roles required")
        require(member["uid"] == allocation["uid"] and member["boot_id"] == allocation["boot_id"],
                "service UID/boot differs from allocation")
        require(type(record["ppid"]) is int and record["ppid"] > 0, "service parent PID")
        require(record["comm"] == ("systemd" if record["role"] == "user_manager" else "(sd-pam)"),
                "only per-user init manager/helper comm allowed")
        require(record["cgroup"] == f"0::/user.slice/user-{allocation['uid']}.slice/user@{allocation['uid']}.service/init.scope\n",
                "only exact per-user init cgroup allowed")
        driver.native.sha(record["cmdline_sha256"])
        require(member["pid"] != os.getpid()
                and all(member["pid"] != owner["pid"] for owner in allocation["coordination_owners"]),
                "service exception overlaps controller/coordination owner")
        expected[record["role"]] = {**record,
            "comm_sha256": hashlib.sha256((record["comm"] + "\n").encode()).hexdigest(),
            "cgroup_sha256": hashlib.sha256(record["cgroup"].encode()).hexdigest()}
    if expected:
        manager, helper = expected["user_manager"], expected["pam_helper"]
        manager_id, helper_id = manager["identity"], helper["identity"]
        require(manager["ppid"] == 1 and manager_id["pid"] == manager_id["pgid"] == manager_id["sid"],
                "manager must be a PPID-1 session/group leader")
        require(helper_id["pid"] != manager_id["pid"] and helper["ppid"] == manager_id["pid"]
                and helper_id["pgid"] == helper_id["sid"] == manager_id["pid"]
                and helper_id["start_ticks"] >= manager_id["start_ticks"], "manager/helper relationship differs")
    return expected


def _service_snapshot(expected, deadline):
    snapshot = {}
    for role, record in expected.items():
        remaining(deadline)
        member = record["identity"]
        path = PROC / str(member["pid"])
        before = identity(member["pid"])
        fields = (path / "stat").read_text().rsplit(")", 1)[1].split()
        comm = (path / "comm").read_bytes()
        cgroup = (path / "cgroup").read_bytes()
        observed = {"role": role, "identity": before, "ppid": int(fields[1]),
                    "comm": comm.decode("utf-8").removesuffix("\n"),
                    "comm_sha256": hashlib.sha256(comm).hexdigest(),
                    "cmdline_sha256": file_hash(path / "cmdline", deadline),
                    "cgroup": cgroup.decode("utf-8"), "cgroup_sha256": hashlib.sha256(cgroup).hexdigest()}
        require(identity(member["pid"]) == before and observed == record, "service metadata identity/parent/bytes drift")
        snapshot[role] = observed
    return snapshot


def validate_allocation(allocation):
    require(type(allocation) is dict and set(allocation) == ALLOCATION_FIELDS, "allocation fields")
    require(allocation["schema"] == SCHEMA + "/allocation", "allocation schema")
    require(type(allocation["gpu_index"]) is int and allocation["gpu_index"] >= 0, "GPU index")
    require(type(allocation["gpu_uuid"]) is str and allocation["gpu_uuid"].startswith("GPU-"), "GPU UUID")
    require(type(allocation["uid"]) is int and allocation["uid"] >= 0, "UID")
    require(type(allocation["boot_id"]) is str and allocation["boot_id"], "boot ID")
    for key in ("python", "queue_dir"):
        require(type(allocation[key]) is str and Path(allocation[key]).is_absolute(), "absolute " + key)
    for key in ("lease_end", "lease_margin_seconds"):
        driver.native.number(allocation[key], positive=True)
    driver.native.sha(allocation["outer_sha256"])
    require(allocation["queue_mode"] in ("direct", "managed"), "queue mode")
    expected = allocation["queue_allowlist"]
    require(type(expected) is dict and set(expected) == {"pending", "running"}, "queue allowlist")
    for entries in expected.values():
        require(type(entries) is dict, "queue entry hashes required")
        for name, value in entries.items():
            require(type(name) is str and name not in ("", ".", "..")
                    and Path(name).name == name, "queue entry name")
            driver.native.sha(value)
    if allocation["queue_mode"] == "direct":
        require(not any(expected.values()), "direct launch requires empty queue")
    else:
        require(bool(expected["running"]), "managed launch needs pinned running coordination")
    require(type(allocation["coordination_owners"]) is list, "coordination owners")
    seen = set()
    for owner in allocation["coordination_owners"]:
        _identity_schema(owner)
        require(owner["uid"] == allocation["uid"] and owner["boot_id"] == allocation["boot_id"], "coordination owner allocation")
        require(owner["pid"] not in seen, "duplicate coordination owner")
        seen.add(owner["pid"])
    _service_expectations(allocation)


def check_node(allocation):
    require(boot_id() == allocation["boot_id"] and os.getuid() == allocation["uid"], "boot/UID changed")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "outer requires explicitly empty CVD")


def check_queue(allocation, deadline, *, release=False):
    observed = {}
    for group in ("pending", "running"):
        directory = Path(allocation["queue_dir"]) / group
        require(directory.is_dir() and directory.resolve() == directory, "queue directory missing/aliased")
        entries = {}
        for path in sorted(directory.iterdir()):
            remaining(deadline)
            require(path.is_file() and not path.is_symlink(), "queue entry must be regular file")
            entries[path.name] = file_hash(path, deadline)
        observed[group] = entries
    expected = allocation["queue_allowlist"]
    matched = (all(all(expected[group].get(name) == digest for name, digest in entries.items())
                   for group, entries in observed.items()) if release else observed == expected)
    return {"mode": allocation["queue_mode"], "observed": observed, "expected": expected,
            "release_allows_removal_only": release, "matched": matched}


def _cvd_state(expected):
    path = PROC / str(expected["pid"])
    fields = (path / "stat").read_text().rsplit(")", 1)[1].split()
    observed = {"pid": expected["pid"], "pgid": int(fields[2]), "sid": int(fields[3]),
                "start_ticks": int(fields[19]), "boot_id": boot_id(), "uid": path.stat().st_uid}
    require(observed == expected, "process identity changed during CVD state check")
    return fields[0]


def _terminated_cvd(before, state_before, allocation, deadline, error=None):
    remaining(deadline)
    terminated_state = _cvd_state(before)
    if terminated_state != "Z":
        return None
    _identity_schema(before)
    require(before["boot_id"] == allocation["boot_id"] and before["uid"] == allocation["uid"],
            "terminated process allocation identity differs")
    after = identity(before["pid"])
    require(after == before, "terminated process identity changed/reused")
    state_after = _cvd_state(after)
    require(state_after == "Z", "terminated process state changed")
    return {"pid": before["pid"], "identity_before": before, "identity_after": after,
            "state_before": state_before, "terminated_state_before": terminated_state, "state_after": state_after,
            "environment_read": False, "environment_error_type": type(error).__name__ if error is not None else None,
            "environment_error": str(error) if error is not None else None,
            "exclusion_scope": "STABLE_TERMINATED_Z_NON_LIVE_RESERVATION"}


def check_cvd(allocation, deadline, *, release=False):
    owners, unresolved, approved, terminated = [], [], [], []
    services = _service_expectations(allocation)
    service_pids = {record["identity"]["pid"] for record in services.values()}
    ancestors, parent = [], os.getpid()
    while parent > 1:
        remaining(deadline)
        record = identity(parent)
        require(record not in ancestors, "ancestor cycle")
        ancestors.append(record)
        fields = (PROC / str(parent) / "stat").read_text().rsplit(")", 1)[1].split()
        parent = int(fields[1])
    allowed = [] if release else allocation["coordination_owners"]
    require(all(owner in ancestors for owner in allowed), "CVD exclusions must be exact own ancestor identities")
    selected = {str(allocation["gpu_index"]), allocation["gpu_uuid"], "all"}
    for path in sorted(PROC.glob("[0-9]*")):
        remaining(deadline)
        try:
            if path.stat().st_uid != allocation["uid"]:
                continue
            before = identity(int(path.name))
            state_before = _cvd_state(before)
            if state_before == "Z":
                exclusion = _terminated_cvd(before, state_before, allocation, deadline)
                require(exclusion is not None, "terminated process state changed")
                terminated.append(exclusion)
                continue
            metadata_before, metadata_error = None, None
            if before["pid"] in service_pids:
                try:
                    metadata_before = _service_snapshot(services, deadline)
                except (OSError, ValueError) as error:
                    metadata_error = str(error)
            try:
                entries = (path / "environ").read_bytes().split(b"\0")
            except PermissionError as error:
                exclusion = _terminated_cvd(before, state_before, allocation, deadline, error)
                if exclusion is not None:
                    terminated.append(exclusion)
                    continue
                if before["pid"] not in service_pids:
                    raise
                try:
                    require(metadata_before is not None, "service metadata before PermissionError: " + str(metadata_error))
                    metadata_after = _service_snapshot(services, deadline)
                    require(metadata_before == metadata_after and identity(before["pid"]) == before,
                            "service metadata changed across environment denial")
                    approved.append({"pid": before["pid"], "environment_read": False,
                                     "error_type": "PermissionError", "error": str(error),
                                     "exception_scope": "EXPLICIT_MAIN_APPROVED_NON_WORKER_INIT_PAIR",
                                     "metadata_before": metadata_before, "metadata_after": metadata_after})
                except (OSError, ValueError) as mismatch:
                    unresolved.append({"pid": before["pid"], "error_type": type(mismatch).__name__,
                                       "error": str(mismatch), "environment_read": False,
                                       "environment_error_type": "PermissionError"})
                continue
            visible = [entry.split(b"=", 1)[1].decode("utf-8") for entry in entries
                       if entry.startswith(b"CUDA_VISIBLE_DEVICES=")]
            require(identity(int(path.name)) == before, "process changed during CVD scan")
            if any(selected & {part.strip() for part in value.split(",")} for value in visible):
                owners.append({"identity": before, "visibility": visible})
        except FileNotFoundError:
            continue
        except (OSError, ValueError) as error:
            unresolved.append({"pid": int(path.name), "error_type": type(error).__name__, "error": str(error)})
    unexpected = [owner for owner in owners if owner["identity"] not in allowed]
    return {"scope": "same_uid_live_explicit_CVD; GPU query covers all compute owners",
            "owners": owners, "unresolved": unresolved, "unexpected": unexpected,
            "excluded_terminated_processes": terminated,
            "excluded_own_ancestors": [owner for owner in owners if owner["identity"] in allowed],
            "approved_unreadable_services": approved, "complete_cvd_visibility": not unresolved and not approved,
            "device_unreserved": False if unresolved or owners else None if approved else True,
            "reservation_check_status": ("BLOCKED" if unresolved or unexpected else
                                         "PASS_WITH_EXPLICIT_NON_WORKER_SERVICE_EXCEPTIONS" if approved else "PASS"),
            "clear": not unresolved and not unexpected}


def check_gpu(allocation, deadline):
    command = ["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader,nounits",
               "-i", str(allocation["gpu_index"])]
    queries = [command, ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"]]
    captures = []
    for command in queries:
        started = time.monotonic()
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=remaining(deadline, 10))
            captures.append({"command": command, "returncode": result.returncode,
                             "stdout": result.stdout, "stderr": result.stderr,
                             "started_monotonic": started, "ended_monotonic": time.monotonic()})
        except subprocess.TimeoutExpired as error:
            def text(value):
                return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
            captures.append({"command": command, "timeout": True, "stdout": text(error.stdout),
                             "stderr": text(error.stderr), "started_monotonic": started,
                             "ended_monotonic": time.monotonic()})
            return {"queries": captures, "empty": False, "error": "query timeout"}
    if any(type(item["returncode"]) is not int or item["returncode"] != 0 for item in captures):
        return {"queries": captures, "empty": False, "error": "query failed"}
    devices = [line.strip() for line in captures[0]["stdout"].splitlines() if line.strip()]
    expected = [str(allocation["gpu_index"]), allocation["gpu_uuid"]]
    if len(devices) != 1 or [part.strip() for part in devices[0].split(",")] != expected:
        return {"queries": captures, "empty": False, "error": "GPU UUID/index mismatch"}
    processes = []
    for line in captures[1]["stdout"].splitlines():
        if not line.strip():
            continue
        fields = [part.strip() for part in line.split(",")]
        if len(fields) != 2 or not fields[0].startswith("GPU-") or not fields[1].isdigit():
            return {"queries": captures, "empty": False, "error": "unparseable compute inventory"}
        if fields[0] == allocation["gpu_uuid"]:
            processes.append(int(fields[1]))
    return {"queries": captures, "gpu_uuid": allocation["gpu_uuid"], "processes": processes,
            "empty": not processes}


def group_members(expected, deadline):
    require(boot_id() == expected["boot_id"], "boot changed before process cleanup")
    try:
        require(identity(expected["pid"]) == expected, "owned leader identity changed/reused")
    except FileNotFoundError:
        pass
    members = []
    for path in PROC.glob("[0-9]*"):
        remaining(deadline)
        try:
            fields = (path / "stat").read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == expected["pgid"] and fields[0] not in ("Z", "X"):
                member = identity(int(path.name))
                require(member["sid"] == expected["sid"] and member["uid"] == expected["uid"]
                        and member["start_ticks"] >= expected["start_ticks"], "unowned group member")
                members.append(member)
        except FileNotFoundError:
            continue
    return members


def cleanup_owned(process, expected, deadline, evidence):
    _identity_schema(expected)
    require(expected["pid"] == process.pid == expected["pgid"] == expected["sid"]
            and expected["pid"] > 1 and expected["pid"] != os.getpid(), "not isolated owned session")
    for action in (signal.SIGTERM, signal.SIGKILL):
        members = group_members(expected, deadline)
        evidence.append({"members": members, "at_monotonic": time.monotonic()})
        if not members:
            break
        remaining(deadline)
        try:
            os.killpg(expected["pgid"], action)
        except ProcessLookupError:
            pass
        evidence.append({"signal": action.value, "pgid": expected["pgid"]})
        until = time.monotonic() + remaining(deadline, 3)
        while group_members(expected, deadline) and time.monotonic() < until:
            time.sleep(min(0.05, remaining(deadline)))
    process.wait(timeout=remaining(deadline, 3))
    require(not group_members(expected, deadline), "owned group remains")
    return {"identity": expected, "owned_group_released": True, "events": evidence}


def _observe(path, action):
    started = time.monotonic()
    try:
        value = action()
    except BaseException as error:
        write(path, {"started_monotonic": started, "ended_monotonic": time.monotonic(),
                     "error_type": type(error).__name__, "error": str(error)})
        raise
    write(path, {"started_monotonic": started, "ended_monotonic": time.monotonic(), "value": value})
    return value


def _inputs(manifest_path, manifest_sha256, allocation_path, allocation_sha256, deadline):
    require(file_hash(manifest_path, deadline) == manifest_sha256, "manifest file changed")
    require(file_hash(allocation_path, deadline) == allocation_sha256, "allocation file changed")
    manifest, allocation = read(manifest_path), read(allocation_path)
    validate_allocation(allocation)
    remaining(min(deadline, manifest["actor"]["deadline"]))
    check_node(allocation)
    require(file_hash(__file__, deadline) == allocation["outer_sha256"], "outer source changed")
    driver.validate_manifest(manifest)
    require(manifest["test_only"] is False, "native-only outer; synthetic manifest refused")
    require(manifest["actor"]["gpu_uuid"] == allocation["gpu_uuid"], "allocated GPU differs")
    require(Path(allocation["python"]).resolve() == Path(manifest["actor"]["environment"]["python"]).resolve(), "interpreter binding differs")
    require(manifest["actor"]["source_files"].get(str(COMMAND)) == file_hash(COMMAND, deadline), "command source unbound/drifted")
    for path, expected in manifest["actor"]["source_files"].items():
        require(file_hash(path, deadline) == expected, "source changed: " + path)
    remaining(deadline)
    return manifest, allocation


def _inventory(root, deadline):
    inventory = {}
    for path in sorted(root.rglob("*")):
        remaining(deadline)
        require(not path.is_symlink(), "output contains symlink")
        if path.is_file():
            inventory[str(path.relative_to(root))] = {"size": path.stat().st_size, "sha256": file_hash(path, deadline)}
        else:
            require(path.is_dir(), "output contains nonregular artifact")
    return inventory


def _report(manifest, worker, release_time):
    report_path = Path(manifest["output_dir"]) / "report.json"
    report = read(report_path)
    driver._unseal(report)
    require(report["schema"] == driver.SCHEMA + "/report" and report["test_only"] is False
            and report["manifest_sha256"] == manifest["sha256"]
            and report["gpu_uuid"] == manifest["actor"]["gpu_uuid"], "report binding")
    require(report["status"] == "COMPLETE_AWAITING_OUTER_RELEASE" and report["error"] is None
            and report["full_v22_release"] is False, "diagnostic did not complete")
    for key, expected in (("tasks", 800), ("scored_tasks", 800), ("fits", 0), ("updates", 0)):
        require(type(report[key]) is int and report[key] == expected, "report count: " + key)
    require(type(report["actor_attempts"]) is int and 800 <= report["actor_attempts"] <= 1952
            and type(report["actor_responses"]) is int and report["actor_responses"] == report["actor_attempts"], "actor counts")
    require([row["id"] for row in report["results"]] == [task["id"] for task in manifest["plan"]["tasks"]]
            and all(row["execution"] == "SCORED" for row in report["results"]), "800 task inventory")
    require(report["actor_config_sha256"] == driver.digest(manifest["actor"])
            and report["source_files_sha256"] == driver.digest(manifest["sources"])
            and report["tokenizer_measurements_sha256"] == manifest["measurements"]["sha256"], "report source/config pins")
    close = report["backend_close"]
    require(close["kind"] == "NATIVE" and close.get("error_type") is None
            and close.get("failed") is not True and close.get("budget_exceeded") is not True
            and type(close["calls_consumed"]) is int and close["calls_consumed"] == report["actor_attempts"], "backend close failure")
    for key in ("started_monotonic", "wall_seconds_through_close", "wall_cap", "device_cap"):
        driver.native.number(report[key])
    require(worker["spawn_started_monotonic"] <= report["started_monotonic"] <= release_time
            and report["started_monotonic"] + report["wall_seconds_through_close"] <= release_time
            and report["wall_cap"] == manifest["wall_seconds"]
            and report["device_cap"] == manifest["device_seconds"], "report clock/caps")
    return report


def controller(manifest_path, manifest_sha256, allocation_path, allocation_sha256, outer_dir, cleanup_seconds=120):
    entry = time.monotonic()
    require(type(cleanup_seconds) is int and 30 <= cleanup_seconds <= 120, "cleanup reserve must be 30..120 seconds")
    root = Path(outer_dir)
    require(root.is_absolute() and root.parent.is_dir() and root.parent.resolve() == root.parent, "fresh absolute outer parent required")
    preliminary = read(manifest_path)
    for protected in (Path(preliminary["actor"]["model_path"]), Path(preliminary["output_dir"]), COMMAND.parents[1]):
        require(not root.is_relative_to(protected) and not protected.is_relative_to(root), "outer/protected path overlap")
    for key in ("wall_seconds", "device_seconds"):
        driver.native.number(preliminary[key], positive=True)
    driver.native.number(preliminary["actor"]["deadline"], positive=True)
    root.mkdir(exist_ok=False)
    process, expected, manifest, allocation = None, None, None, None
    deadline = min(entry + min(36000, preliminary["wall_seconds"], preliminary["device_seconds"]), preliminary["actor"]["deadline"])
    try:
        manifest, allocation = _inputs(manifest_path, manifest_sha256, allocation_path, allocation_sha256, deadline)
        output = Path(manifest["output_dir"])
        require(not output.exists() and not output.is_symlink() and output.parent.is_dir() and output.parent.resolve() == output.parent, "fresh output required")
        require(not root.is_relative_to(output) and not output.is_relative_to(root), "outer/output overlap")
        deadline = min(entry + manifest["wall_seconds"], entry + manifest["device_seconds"],
                       manifest["actor"]["deadline"], time.monotonic() + allocation["lease_end"] - time.time() - allocation["lease_margin_seconds"])
        require(remaining(deadline) > cleanup_seconds, "insufficient cold-load/release envelope")
        context = {"schema": SCHEMA, "manifest_path": str(Path(manifest_path).resolve()), "manifest_file_sha256": manifest_sha256,
                   "allocation_path": str(Path(allocation_path).resolve()), "allocation_file_sha256": allocation_sha256,
                   "entry_monotonic": entry, "deadline_monotonic": deadline, "cleanup_seconds": cleanup_seconds,
                   "controller": identity(os.getpid()), "output_dir": str(output)}
        write(root / "context.json", context)
        write(output.with_name(output.name + ".outer_claim.json"), {"outer_dir": str(root), "manifest_file_sha256": manifest_sha256, "retry": False})
        queue = _observe(root / "preflight_queue.json", lambda: check_queue(allocation, deadline))
        require(queue["matched"], "queue coordination changed")
        cvd = _observe(root / "preflight_cvd.json", lambda: check_cvd(allocation, deadline))
        require(cvd["clear"], "CVD reservation unresolved/foreign")
        gpu = _observe(root / "preflight_gpu.json", lambda: check_gpu(allocation, deadline))
        require(gpu["empty"], "allocated GPU occupied/unverified")
        check_node(allocation)
        require(remaining(deadline) > cleanup_seconds, "preflight consumed execution reserve")
        command = [allocation["python"], "-B", str(COMMAND), "run", "--manifest", str(Path(manifest_path).resolve()), "--manifest-sha256", manifest_sha256]
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=allocation["gpu_uuid"], PYTHONPATH=str(COMMAND.parents[1]),
                           HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                           VLLM_NO_USAGE_STATS="1", PYTHONDONTWRITEBYTECODE="1", VLLM_WORKER_MULTIPROC_METHOD="spawn")
        spawned = time.monotonic()
        with (root / "stdout.log").open("xb") as stdout, (root / "stderr.log").open("xb") as stderr:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                       env=environment, start_new_session=True)
            try:
                expected = identity(process.pid)
                write(root / "spawn.json", {"pid": process.pid, "command": command,
                                           "spawn_started_monotonic": spawned, "identity_verified": False})
                require(expected["pgid"] == expected["sid"] == process.pid and expected["uid"] == allocation["uid"]
                        and expected["boot_id"] == allocation["boot_id"], "worker ownership differs")
                worker = {"identity": expected, "command": command, "spawn_started_monotonic": spawned,
                          "recorded_monotonic": time.monotonic(), "manifest_file_sha256": manifest_sha256,
                          "gpu_uuid": allocation["gpu_uuid"], "boot_id": allocation["boot_id"]}
                write(root / "worker_start.json", worker)
                returncode = _observe(root / "worker_wait.json", lambda: process.wait(timeout=remaining(deadline) - cleanup_seconds))
                require(type(returncode) is int and returncode == 0, "worker nonzero/invalid exit")
            except BaseException as error:
                write(root / "worker_error.json", {"type": type(error).__name__, "error": str(error),
                                                   "pid": process.pid, "identity": expected})
                raise
            finally:
                events = []
                try:
                    release = cleanup_owned(process, expected, deadline, events)
                    write(root / "worker_release.json", release)
                    gpu = _observe(root / "post_worker_gpu.json", lambda: check_gpu(allocation, deadline))
                    require(gpu["empty"], "GPU not empty after worker release")
                    _observe(root / "post_worker_cvd.json", lambda: check_cvd(allocation, deadline))
                except BaseException as error:
                    write(root / "cleanup_failure.json", {"error": str(error), "events": events, "identity": expected})
                    raise
                finally:
                    write(root / "worker_exit.json", {"identity": expected, "returncode": process.returncode,
                                                       "ended_monotonic": time.monotonic()})
        check_node(allocation)
        report = _report(manifest, worker, time.monotonic())
        _inputs(manifest_path, manifest_sha256, allocation_path, allocation_sha256, deadline)
        inventory = _inventory(output, deadline)
        hashes = {path.name: file_hash(path, deadline) for path in root.iterdir() if path.is_file()}
        complete = {"schema": SCHEMA + "/captured", "status": "CAPTURED_AWAITING_RESERVATION_RELEASE",
                    "manifest_sha256": manifest["sha256"], "report_sha256": report["sha256"],
                    "report_file_sha256": inventory["report.json"]["sha256"], "output_inventory": inventory,
                    "outer_files": hashes, "elapsed_seconds": time.monotonic() - entry,
                    "fits": 0, "updates": 0, "finalized": False,
                    "worker_group_released": True, "gpu_compute_vacant": True,
                    "reservation_released": read(root / "post_worker_cvd.json")["value"]["device_unreserved"],
                    "reservation_check_status": read(root / "post_worker_cvd.json")["value"]["reservation_check_status"],
                    "complete_cvd_visibility": read(root / "post_worker_cvd.json")["value"]["complete_cvd_visibility"]}
        remaining(deadline)
        write(root / "capture_complete.json", complete)
        return {**complete, "capture_file_sha256": file_hash(root / "capture_complete.json", deadline)}
    except BaseException as error:
        write(root / "controller_failure.json", {"type": type(error).__name__, "error": str(error),
                                                  "pid": process.pid if process else None,
                                                  "identity_verified": expected is not None,
                                                  "elapsed_seconds": time.monotonic() - entry})
        raise


def finalize(outer_dir, capture_sha256):
    root = Path(outer_dir)
    require(root.is_absolute() and root.resolve() == root, "absolute unaliased outer directory")
    write(root / "finalize_claim.json", {"started_monotonic": time.monotonic(), "retry": False})
    try:
        require(not (root / "controller_failure.json").exists(), "failed controller cannot finalize")
        require(file_hash(root / "capture_complete.json") == capture_sha256, "capture completion changed")
        context, complete = read(root / "context.json"), read(root / "capture_complete.json")
        deadline = context["deadline_monotonic"]
        remaining(deadline)
        manifest, allocation = _inputs(context["manifest_path"], context["manifest_file_sha256"], context["allocation_path"], context["allocation_file_sha256"], deadline)
        require(complete["schema"] == SCHEMA + "/captured" and complete["manifest_sha256"] == manifest["sha256"], "capture binding")
        for name, expected in complete["outer_files"].items():
            require(Path(name).name == name and file_hash(root / name, deadline) == expected, "capture receipt changed")
        require(_inventory(Path(manifest["output_dir"]), deadline) == complete["output_inventory"], "captured output changed")
        worker = read(root / "worker_start.json")
        exited = read(root / "worker_exit.json")
        require(type(exited["returncode"]) is int and exited["returncode"] == 0, "worker exit receipt")
        require(not group_members(worker["identity"], deadline), "owned group still alive")
        queue = _observe(root / "final_queue.json", lambda: check_queue(allocation, deadline, release=True))
        require(queue["matched"], "new queue coordination appeared")
        cvd = _observe(root / "final_cvd.json", lambda: check_cvd(allocation, deadline, release=True))
        require(cvd["clear"] and not cvd["owners"], "CVD owner remains; release Main holder before finalization")
        gpu = _observe(root / "final_gpu.json", lambda: check_gpu(allocation, deadline))
        require(gpu["empty"], "GPU vacancy not established")
        cvd = _observe(root / "final_cvd_after_gpu.json", lambda: check_cvd(allocation, deadline, release=True))
        require(cvd["clear"] and not cvd["owners"] and not group_members(worker["identity"], deadline), "late reservation/group appeared")
        check_node(allocation)
        released = time.monotonic()
        report = _report(manifest, worker, released)
        require(report["sha256"] == complete["report_sha256"], "report changed")
        attestation = {"report_sha256": report["sha256"], "gpu_uuid": allocation["gpu_uuid"],
                       "owned_group_released": True, "gpu_vacant": True,
                       "elapsed_seconds_from_start": released - report["started_monotonic"]}
        write(root / "release_attestation.json", attestation)
        receipt = {**attestation, "evidence_path": str(root / "release_attestation.json"),
                   "evidence_sha256": file_hash(root / "release_attestation.json", deadline)}
        write(root / "release_receipt.json", receipt)
        final = driver.finalize_release(report, receipt)
        require(final["diagnostic_usable"] is True, "finalization not usable")
        remaining(deadline)
        write(root / "final.json", final)
        links = {path.name: file_hash(path, deadline) for path in root.iterdir() if path.is_file()}
        remaining(deadline)
        collection = {"schema": SCHEMA + "/collection", "files": links,
                      "output_inventory_sha256": driver.digest(complete["output_inventory"]),
                      "release_monotonic": released, "outer_elapsed_seconds": time.monotonic() - context["entry_monotonic"],
                      "reservation_check_status": cvd["reservation_check_status"],
                      "complete_cvd_visibility": cvd["complete_cvd_visibility"],
                      "approved_unreadable_service_pids": [record["pid"] for record in cvd["approved_unreadable_services"]],
                      "fits": 0, "updates": 0, "generation_retries": 0, "full_v22_release": False}
        write(root / "collection.json", collection)
        remaining(deadline)
        return collection
    except BaseException as error:
        write(root / "finalize_failure.json", {"type": type(error).__name__, "error": str(error)})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="stage", required=True)
    run = commands.add_parser("run")
    for name in ("manifest", "manifest-sha256", "allocation", "allocation-sha256", "outer"):
        run.add_argument("--" + name, required=True)
    run.add_argument("--cleanup-seconds", type=int, default=120)
    release = commands.add_parser("finalize")
    release.add_argument("--outer", required=True)
    release.add_argument("--capture-sha256", required=True)
    args = parser.parse_args(argv)
    if args.stage == "run":
        result = controller(args.manifest, args.manifest_sha256, args.allocation, args.allocation_sha256, args.outer, args.cleanup_seconds)
    else:
        result = finalize(args.outer, args.capture_sha256)
    print(driver.canonical({"schema": result["schema"], "outer": args.outer,
                           "capture_file_sha256": result.get("capture_file_sha256")}).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
