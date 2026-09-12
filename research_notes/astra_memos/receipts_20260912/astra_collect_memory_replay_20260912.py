"""Root0 only; read-only status and immutable terminal collection. Main executes."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import tarfile

PLAN_SHA = "70405bfa50486feaa2b000ee8102a1cdf30265bccaf102958d7e3ea17035bbb9"
RUNNER_SHA = "1586ddf7d690ce8bc55d680bd926439fbd597236ea8e76394f88a3bdf023c8bc"
HELPER_SHA = "d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb"
CHECK_SHA = "a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f"
HOME = Path.home()
ROOT = HOME / "astra_diagnostics/astra_memory_replay_20260912_attempt1/seed0"
SOURCE = HOME / "astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903"
RUNNER = Path("/tmp/astra_memory_replay_20260912.py")
ARCHIVE = Path("/tmp/astra_memory_replay_seed0_terminal_20260912.tgz")
STARTED = "2026-09-12T20:02:28.997513+00:00"
PID, ARMS = 211116, ("mixed", "all_memory")


def load(path, checksum, name):
    if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
        raise ValueError("dependency changed: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


common = load(Path("/tmp/astra_collect_memory_only_20260912.py"), HELPER_SHA, "replay_collection_common")
require, read, digest = common.require, common.read, common.digest


def records():
    require(digest(ROOT / "plan.json") == read(ROOT / "plan.sha256.json")["sha256"] == PLAN_SHA, "plan changed")
    plan, launch = read(ROOT / "plan.json"), read(ROOT / "launch/launch.json")
    require(plan["seed"] == 0 and plan["device"] == "0" and plan["arm_order"] == list(ARMS) and
        plan["source_root"] == str(SOURCE) and plan["source_hashes"]["replay_sidecar"] == RUNNER_SHA, "wrong root0 plan")
    require(launch["pid"] == PID and launch["node"] == 3 and launch["seed"] == 0 and launch["device"] == "0" and
        launch["source"] == str(SOURCE) and launch["plan_sha256"] == PLAN_SHA and launch["script_sha256"] == RUNNER_SHA and
        launch["bound_seconds"] == 1200 and launch["continuous_reservation"] is True and
        dt.datetime.fromisoformat(launch["started_utc"]) == dt.datetime.fromisoformat(STARTED), "launch changed")
    require(launch["command"] == [launch["command"][0], "-B", str(RUNNER), "run", "--source-root", str(SOURCE),
        "--runroot", str(ROOT), "--allow-gpu"], "launch command changed")
    terminal = read(ROOT / "run/terminal.json") if (ROOT / "run/terminal.json").is_file() else None
    return plan, launch, terminal


def status():
    plan, launch, terminal = records()
    markers = ("fit-worker/process.json", "fit-worker/supervision.json", "adapter/DONE", "adapter/train_manifest.json",
        "fit-result.json", "dev/reduction.json", "dev/run/data/manifest.json", "exact/reduction.json",
        "exact/run/data/manifest.json", "arm-result.json")
    return dict(pid=PID, device=plan["device"], controller_present=Path(f"/proc/{PID}").exists(),
        terminal_available=terminal is not None, status=terminal["status"] if terminal else None,
        error=terminal.get("error") if terminal else None,
        arms={arm: {name: (ROOT / "run" / arm / name).is_file() for name in markers} for arm in ARMS})


def finish():
    observed = status()
    require(not observed["controller_present"] and observed["terminal_available"], "wait for controller absence AND terminal")
    plan, launch, terminal = records()
    stage, validation_path = ROOT / "run", Path(str(ARCHIVE) + ".validation.json")
    require(terminal["controller_pid"] == PID and terminal["plan_sha256"] == PLAN_SHA and terminal["device"] == "0" and
        terminal["seed"] == 0 and terminal["status"] in ("COMPLETE", "FAILED_PARTIAL_NO_RETRY") and
        all(terminal[key] == value for key, value in read(stage / "reservation.json").items()), "terminal custody changed")
    runner = load(RUNNER, RUNNER_SHA, "replay_collection_runner")
    runner.bind(SOURCE, "/tmp/astra_memory_only_20260912.py", "/tmp/astra_fading_sentinel_20260912.py")
    runner.verify(ROOT)
    audits = {}
    for arm in ARMS:
        target, result = stage / arm, terminal["arms"].get(arm)
        fit = read(target / "fit-result.json") if (target / "fit-result.json").is_file() else None
        if fit is not None:
            parent, adapter = plan["parent"]["parent"], target / "adapter"
            require(fit["parent"] == parent and fit["adapter"] == str(adapter) and (adapter / "DONE").is_file() and
                fit["parent_files"] == plan["parent"]["parent_files"] == runner.trainer._warm_inventory(parent) and
                fit["adapter_files"] == runner.trainer._warm_inventory(adapter), "successful adapter inventory changed")
            runner.validate_manifest(plan, arm, read(adapter / "train_manifest.json"),
                runner.old.state_inventory(parent), runner.old.state_inventory(adapter))
            receipt = read(target / "fit-worker/supervision.json")
            runner.memory.successful(receipt)
            require(fit["supervision"] == receipt and fit["accounting"] == runner.COUNTS[arm], "fit receipt changed")
        if result is not None:
            require(fit is not None and result == read(target / "arm-result.json") and result["fit"] == fit, "arm result changed")
        require(terminal["status"] != "COMPLETE" or result is not None, "complete pair missing arm")
        proxy = dict(terminal, result=result, status="COMPLETE" if result is not None else "FAILED_PARTIAL_NO_RETRY")
        captures = {}
        for name, module in (("dev", runner.dev), ("exact", runner.exact)):
            path = target / name / "reduction.json"
            if result is None and path.is_file() and read(path).get("complete") is not True:
                captures[name] = dict(status="PARTIAL_REDUCTION_PRESERVED_NOT_SCORED")
            else:
                captures[name] = common.audit_capture(target, name, module, plan, proxy, fit, runner.memory)
        audits[arm] = dict(successful_fit_verified=fit is not None, captures=captures)
    receipts = [read(path) for path in stage.rglob("supervision.json")]
    require(all(math.isfinite(item["reserved_seconds"]) and item["reserved_seconds"] >= 0 for item in receipts) and
        math.isfinite(terminal["reserved_seconds"]) and terminal["reserved_seconds"] >= 0, "invalid cost")
    if terminal["status"] == "COMPLETE":
        require(set(terminal["arms"]) == set(ARMS) and len(receipts) == 6 and terminal["error"] is None and
            terminal["release_verified"] is True and terminal["deadline_met"] is True and terminal["reserved_seconds"] <= 1200 and
            terminal["ended"] <= terminal["effective_deadline"] and
            all((path.parent / "supervision.json").is_file() for path in stage.rglob("process.json")) and
            math.isclose(sum(item["reserved_seconds"] for item in receipts), terminal["worker_reserved_seconds"], abs_tol=1e-6),
            "invalid complete terminal/receipts")
        for receipt in receipts:
            runner.memory.successful(receipt)
    release_json, release_xml = stage / "main_release.json", stage / "main_release.xml"
    prefix = ROOT.relative_to(HOME).as_posix() + "/"
    if ARCHIVE.exists() or validation_path.exists():
        require(ARCHIVE.is_file() and validation_path.is_file(), "partial capsule preserved; no overwrite")
        validation, release = read(validation_path), read(release_json)
        require(validation["archive"] == str(ARCHIVE) and validation["plan_sha256"] == PLAN_SHA and
            validation["sha256"] == digest(ARCHIVE) and validation["files"] == common.metadata(ROOT, HOME) and
            release["terminal_sha256"] == digest(stage / "terminal.json") and release["xml_sha256"] == digest(release_xml) and
            release["full_release"] is True and release["controller_absent"] is True and release["controller_pid"] == PID and
            release["device"] == "0" and release["plan_sha256"] == PLAN_SHA and release["status"] == terminal["status"] and
            release["launch_sha256"] == digest(ROOT / "launch/launch.json") and
            release["gpu"]["gpu_uuid"] == launch["gpu"]["gpu_uuid"],
            "existing capsule/evidence changed")
        common.validate_archive(io.BytesIO(common.read_bytes(ARCHIVE)), validation["files"], prefix)
        return dict(status="ALREADY_COLLECTED_VERIFIED_NO_WRITES", sha256=validation["sha256"], archive=str(ARCHIVE))
    require(not release_json.exists() and not release_xml.exists(), "partial release evidence preserved; no overwrite/retry")
    before = common.metadata(ROOT, HOME)
    check_module = load(SOURCE / "gpu/astra_mini_sudoku_diagnostic.py", CHECK_SHA, "replay_full_release_check")
    gpu, xml = check_module.check_free("0")
    ended = dt.datetime.now(dt.timezone.utc)
    require(gpu["gpu_uuid"] == launch["gpu"]["gpu_uuid"] and not Path(f"/proc/{PID}").exists(), "release identity/controller changed")
    runner.verify(ROOT)
    require(common.metadata(ROOT, HOME) == before, "evidence changed during verification")
    elapsed = (ended - dt.datetime.fromisoformat(launch["started_utc"])).total_seconds()
    require(math.isfinite(elapsed) and elapsed >= 0, "invalid full reservation time")
    common.write_new(release_xml, xml.encode())
    common.write_json(release_json, dict(full_release=True, controller_absent=True, controller_pid=PID, device="0", gpu=gpu,
        release_utc=ended.isoformat(), full_reservation_seconds=elapsed, status=terminal["status"], plan_sha256=PLAN_SHA,
        launch_sha256=digest(ROOT / "launch/launch.json"), terminal_sha256=digest(stage / "terminal.json"),
        xml_sha256=digest(release_xml), collector_sha256=digest(Path(__file__))))
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
    require(common.metadata(ROOT, HOME) == manifest, "evidence changed after packaging")
    validation = dict(archive=str(ARCHIVE), sha256=digest(ARCHIVE), plan_sha256=PLAN_SHA, files=manifest, statuses=observed,
        audits=audits, collector_sha256=digest(Path(__file__)), excluded_suffixes=sorted(common.EXCLUDED),
        excluded_directories=["__pycache__"], score_scope="Existing raw captures/receipts verified; NOT rescored",
        weights="Preserved on native original/child roots; excluded from metadata capsule")
    common.write_json(validation_path, validation)
    return dict(status="COLLECTED", archive=str(ARCHIVE), sha256=validation["sha256"], files=len(manifest))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("status", "finish"))
    args = parser.parse_args()
    print(json.dumps(status() if args.stage == "status" else finish(), indent=2, sort_keys=True, allow_nan=False), flush=True)
