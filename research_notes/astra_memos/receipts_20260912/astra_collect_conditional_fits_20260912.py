"""Pinned root0 fit collection only. Main executes; no loss scoring or readout.

Authorship: this collector's author also authored the fit wrapper. This is
technical receipt verification, not an independent scientific review.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import sys
import tarfile
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
PLAN_SHA = "680e5239cd90c15b72de998d22c09cf5aa451d2e71111d99e940532e43510f11"
RUNNER_SHA = "3be6583f97f68d944774ff15f5fcd4d66522991d62bf865b03f005808cf4f96f"
HELPER_SHA = "d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb"
CHECK_SHA = "a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f"
LAUNCHER_SHA = "08181ceeb3b247a1bf2e9390287b41bdac09b73caaee4d7668ce70ac59ae8c67"
HOME = Path("/localhome/local-rohing")
ROOT = HOME / "astra_diagnostics/astra_conditional_behavior_20260912_attempt2/fits_root0_attempt1"
SOURCE = HOME / "astra_sources/5f6e1f1d217dcdb15176dc84b9ac34ec960c48de"
RUNNER = Path("/tmp/astra_conditional_fits_20260912.py")
PYTHON = HOME / "v2/venv/bin/python"
ARCHIVE = Path("/tmp/astra_conditional_fits_root0_terminal_20260912.tgz")
STARTED = "2026-09-12T20:16:17.399324+00:00"
UUID = "GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821"
PID, DEVICE, ARMS = 214826, "1", ("AUTH", "DERANGED")
CLAIM = "ORACLE_AUTHORED_DIAGNOSTIC_NOT_CHILD_EXPERIENCE_NOT_CLEAN_LINEAGE"
ORIGIN = "UNRESOLVED_LOCAL_HASHES_ONLY"


def load(path, checksum, name):
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("aliased dependency: " + str(path))
    payload = common.read_bytes(path) if "common" in globals() else path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != checksum:
        raise ValueError("dependency changed: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(payload, str(path), "exec"), module.__dict__)
    return module


common = load(Path("/tmp/astra_collect_memory_only_20260912.py"), HELPER_SHA, "conditional_collection_common")
require, read, digest = common.require, common.read, common.digest


def present(path):
    return common.unaliased(path).exists()


def controller_present():
    return Path(f"/proc/{PID}").exists()


def check_uuid(gpu, xml):
    require(gpu["gpu_uuid"] == UUID and ET.fromstring(xml).findall("gpu/uuid") and
            [node.text for node in ET.fromstring(xml).findall("gpu/uuid")] == [UUID], "GPU UUID/XML differs from launch")


def records():
    require(digest(ROOT / "plan.json") == read(ROOT / "plan.sha256.json")["sha256"] == PLAN_SHA, "plan changed")
    plan, launch = read(ROOT / "plan.json"), read(ROOT / "launch/launch.json")
    require(plan["root"] == str(ROOT) and plan["source_root"] == str(SOURCE) and
            plan["source_hashes"]["conditional_fit_sidecar"] == RUNNER_SHA and
            plan["seed"] == 0 and plan["device"] == DEVICE and plan["arms"] == list(ARMS) and
            plan["controller_seconds"] == 1200 and plan["cleanup_seconds"] == 140, "wrong fixed pair plan")
    require(launch["pid"] == PID and launch["node"] == 3 and launch["seed"] == 0 and launch["device"] == DEVICE and
            launch["source"] == str(SOURCE) and launch["plan_sha256"] == PLAN_SHA and launch["script_sha256"] == RUNNER_SHA and
            launch["launcher_sha256"] == LAUNCHER_SHA and launch["controller_bound_seconds"] == 1200 and
            launch["continuous_reservation"] is True and launch["started_utc"] == STARTED and
            launch["generation_calls"] == 0 and launch["claim"] == CLAIM and launch["origin"] == ORIGIN, "launch changed")
    require(launch["command"] == [str(PYTHON), "-B", str(RUNNER), "run", "--source-root", str(SOURCE),
            "--runroot", str(ROOT), "--allow-gpu"], "launch command changed")
    check_uuid(launch["gpu"], common.read_bytes(ROOT / "launch/gpu.xml"))
    terminal = read(ROOT / "run/terminal.json") if present(ROOT / "run/terminal.json") else None
    return plan, launch, terminal


def status():
    plan, launch, terminal = records()
    markers = ("worker/process.json", "worker/supervision.json", "adapter/DONE", "adapter/train_manifest.json", "fit-result.json")
    return dict(pid=PID, device=DEVICE, controller_present=controller_present(), terminal_available=terminal is not None,
        status=terminal["status"] if terminal else None, generation_calls=0, scoring="NONE",
        arms={arm: {name: present(ROOT / "run" / arm / name) for name in markers} for arm in ARMS})


def finite_nonnegative(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def audit(plan, terminal, runner):
    stage = ROOT / "run"
    reservation = read(stage / "reservation.json")
    require(terminal["status"] in ("COMPLETE", "FAILED_PARTIAL_NO_RETRY") and
            terminal["controller_pid"] == PID and terminal["device"] == DEVICE and terminal["plan_sha256"] == PLAN_SHA and
            all(terminal[key] == value for key, value in reservation.items()), "terminal/reservation custody changed")
    require(terminal["claim"] == CLAIM and terminal["origin"] == ORIGIN and terminal["generation_calls"] == 0 and
            terminal["real_lease_end"] == plan["real_lease_end"] and
            all(finite_nonnegative(terminal[key]) for key in ("started", "ended", "effective_deadline", "reserved_seconds", "worker_reserved_seconds")) and
            terminal["effective_deadline"] == terminal["started"] + 1200 and
            terminal["effective_deadline"] <= min(plan["deadline"], plan["real_lease_end"] - 10) and
            terminal["ended"] >= terminal["started"], "invalid terminal cost/bounds/claim")
    require(terminal["release_verified"] is True and terminal["worker_accounting_complete"] is True,
            "unreleased/unaccounted partial requires manual reconciliation; no collection")
    require(terminal["deadline_met"] is (terminal["ended"] <= terminal["effective_deadline"]), "deadline receipt inconsistent")
    require(set(terminal["arms"]) in (set(), {"AUTH"}, set(ARMS)), "arm order/coverage changed")
    receipts, processes, audits = [], [], {}
    for arm in ARMS:
        target = stage / arm
        process_path, receipt_path = target / "worker/process.json", target / "worker/supervision.json"
        exists = present(process_path), present(receipt_path)
        require(exists[0] == exists[1], "partial worker receipts; manual reconciliation required")
        receipt = None
        if exists[0]:
            process, receipt = read(process_path), read(receipt_path)
            require(process["argv"] == plan["commands"][arm] and process["device"] == DEVICE and
                    type(process["pid"]) is int and process["pid"] > 0 and process["pgid"] == process["pid"] and
                    finite_nonnegative(process["started"]) and finite_nonnegative(process["timeout"]) and
                    0 < process["timeout"] <= 600, "worker command/ownership/bounds changed")
            require(receipt["device"] == DEVICE and finite_nonnegative(receipt["reserved_seconds"]) and
                    all(receipt[key] is True for key in ("owned_group_empty", "gpu_processes_absent", "reservation_release_verified")),
                    "worker cleanup/cost unverified")
            processes.append(process)
            receipts.append(receipt)
        fit = read(target / "fit-result.json") if present(target / "fit-result.json") else None
        require(terminal["arms"].get(arm) == fit, "terminal/result changed or unpublished fit; manual reconciliation required")
        if fit is not None:
            expected = runner.verify_fit(plan, target, arm)
            require(fit == dict(expected, supervision=receipt, plan_sha256=PLAN_SHA) and receipt is not None and
                    receipt["ok"] is True and receipt["returncode"] == 0 and receipt["error"] is None, "invalid successful fit receipt")
        audits[arm] = dict(verified_fit=fit is not None, worker_receipt=receipt is not None)
    require({path for path in stage.rglob("process.json")} ==
            {stage / arm / "worker/process.json" for arm in ARMS if present(stage / arm / "worker/process.json")} and
            {path for path in stage.rglob("supervision.json")} ==
            {stage / arm / "worker/supervision.json" for arm in ARMS if present(stage / arm / "worker/supervision.json")}, "unexpected worker records")
    require(math.isclose(sum(receipt["reserved_seconds"] for receipt in receipts), terminal["worker_reserved_seconds"], abs_tol=1e-6) and
            terminal["worker_reserved_seconds"] <= terminal["reserved_seconds"] + .001, "worker/controller accounting differs")
    if len(processes) == 2:
        require(processes[0]["pid"] != processes[1]["pid"] and
                processes[0]["started"] + receipts[0]["reserved_seconds"] <= processes[1]["started"], "fits not sequential fresh processes")
    require(not present(stage / "DERANGED/worker/process.json") or audits["AUTH"]["verified_fit"], "DERANGED without completed AUTH")
    if terminal["status"] == "COMPLETE":
        require(set(terminal["arms"]) == set(ARMS) and len(receipts) == 2 and terminal["error"] is None and
                terminal["deadline_met"] is True and terminal["reserved_seconds"] <= 1200, "invalid COMPLETE terminal")
    return audits


def finish():
    observed = status()
    require(not observed["controller_present"] and observed["terminal_available"], "wait for controller absence AND terminal")
    plan, launch, terminal = records()
    before = common.metadata(ROOT, HOME)
    runner = load(RUNNER, RUNNER_SHA, "conditional_collection_runner")
    runner.bind(SOURCE)
    require(runner.verify(ROOT) == plan, "verified plan changed")
    audits = audit(plan, terminal, runner)
    stage, validation_path = ROOT / "run", Path(str(ARCHIVE) + ".validation.json")
    release_json, release_xml = stage / "main_release.json", stage / "main_release.xml"
    prefix = ROOT.relative_to(HOME).as_posix() + "/"
    collector_sha = digest(Path(__file__))
    if present(ARCHIVE) or present(validation_path):
        require(present(ARCHIVE) and present(validation_path), "partial capsule preserved; no overwrite")
        validation, release = read(validation_path), read(release_json)
        require(validation["archive"] == str(ARCHIVE) and validation["sha256"] == digest(ARCHIVE) and
                validation["plan_sha256"] == PLAN_SHA and validation["files"] == before and validation["audits"] == audits and
                validation["collector_sha256"] == release["collector_sha256"] == collector_sha and
                release["terminal_sha256"] == digest(stage / "terminal.json") and release["xml_sha256"] == digest(release_xml) and
                release["launch_sha256"] == digest(ROOT / "launch/launch.json") and release["plan_sha256"] == PLAN_SHA and
                release["full_release"] is True and release["controller_absent"] is True and release["controller_pid"] == PID and
                release["device"] == DEVICE and release["status"] == terminal["status"], "existing capsule/release/current evidence changed")
        check_uuid(release["gpu"], common.read_bytes(release_xml))
        elapsed = (dt.datetime.fromisoformat(release["release_utc"]) - dt.datetime.fromisoformat(STARTED)).total_seconds()
        require(finite_nonnegative(elapsed) and elapsed == release["full_reservation_seconds"], "release cost changed")
        common.validate_archive(io.BytesIO(common.read_bytes(ARCHIVE)), before, prefix)
        require(not controller_present() and common.metadata(ROOT, HOME) == before, "current evidence/controller changed")
        return dict(status="ALREADY_COLLECTED_VERIFIED_NO_WRITES", archive=str(ARCHIVE), sha256=validation["sha256"])
    require(not present(release_json) and not present(release_xml), "partial release preserved; no retry/overwrite")
    checker = load(SOURCE / "gpu/astra_mini_sudoku_diagnostic.py", CHECK_SHA, "conditional_collection_full_release")
    gpu, xml = checker.check_free(DEVICE)
    check_uuid(gpu, xml)
    ended = dt.datetime.now(dt.timezone.utc)
    require(not controller_present(), "controller present after vacancy check")
    require(runner.verify(ROOT) == plan and audit(plan, terminal, runner) == audits and
            common.metadata(ROOT, HOME) == before, "evidence changed during terminal verification")
    elapsed = (ended - dt.datetime.fromisoformat(STARTED)).total_seconds()
    require(finite_nonnegative(elapsed), "invalid full reservation time")
    common.write_new(release_xml, xml.encode())
    common.write_json(release_json, dict(full_release=True, controller_absent=True, controller_pid=PID, device=DEVICE, gpu=gpu,
        release_utc=ended.isoformat(), full_reservation_seconds=elapsed, status=terminal["status"], plan_sha256=PLAN_SHA,
        launch_sha256=digest(ROOT / "launch/launch.json"), terminal_sha256=digest(stage / "terminal.json"),
        xml_sha256=digest(release_xml), collector_sha256=collector_sha,
        worker_reserved_seconds=terminal["worker_reserved_seconds"], controller_reserved_seconds=terminal["reserved_seconds"],
        monetary_cost=None, accounting="Full launch-to-observed-vacancy interval; worker/controller windows are subsets, not additive"))
    manifest = common.metadata(ROOT, HOME)
    require(all(manifest.get(name) == checksum for name, checksum in before.items()), "prior evidence changed")
    with ARCHIVE.open("xb") as stream, tarfile.open(fileobj=stream, mode="w:gz", format=tarfile.USTAR_FORMAT) as archive:
        for name, checksum in manifest.items():
            payload = common.read_bytes(HOME / name)
            require(hashlib.sha256(payload).hexdigest() == checksum, "metadata changed while packing")
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(payload), 0o600
            archive.addfile(member, io.BytesIO(payload))
    common.validate_archive(io.BytesIO(common.read_bytes(ARCHIVE)), manifest, prefix)
    require(common.metadata(ROOT, HOME) == manifest and not controller_present(), "evidence/controller changed after packaging")
    common.write_json(validation_path, dict(archive=str(ARCHIVE), sha256=digest(ARCHIVE), plan_sha256=PLAN_SHA,
        files=manifest, audits=audits, terminal_status=terminal["status"], collector_sha256=collector_sha,
        excluded_suffixes=sorted(common.EXCLUDED), excluded_directories=["__pycache__"],
        scope="Receipt/configuration/hash verification only; no loss scoring, generation, or scientific review",
        authorship="Collector author also authored fit wrapper; NOT independent review",
        weights="Retained native; hashed by runner.verify_fit; excluded from capsule"))
    return dict(status="COLLECTED", terminal_status=terminal["status"], archive=str(ARCHIVE), sha256=digest(ARCHIVE), files=len(manifest))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("status", "finish"))
    args = parser.parse_args()
    print(json.dumps(status() if args.stage == "status" else finish(), indent=2, sort_keys=True, allow_nan=False), flush=True)
