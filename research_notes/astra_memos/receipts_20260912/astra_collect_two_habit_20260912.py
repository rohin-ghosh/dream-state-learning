"""Seed0-only read-only status and one-shot terminal collection; Main executes."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile
import xml.etree.ElementTree as ET


PLAN_SHA = "af4988757fb01e93fe88e6f310c61656f26b2920d45c21561f6b035d208d11e9"
RUNNER_SHA = "d8983514e081be49c931f422143aeeee695498d9dc6547ac14e43d46034a2f60"
GPU_CHECK_SHA = "a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f"
ROOT_NAME = "astra_fundamental_two_habit_20260912_attempt1"
SOURCE_NAME = "d1e70002d12052f6b7357d42cf5997aa915e16f7"
CONTROLLER_PID = 203151
STARTED_UTC = "2026-09-12T19:37:55.603911+00:00"
RUNNER = Path("/tmp/astra_two_habit_runner_20260912.py")
ARCHIVE = Path("/tmp/astra_two_habit_terminal_20260912.tgz")
ARMS = ("input_before", "input_after")
EXCLUDED = {".bin", ".safetensors", ".pt", ".pth", ".ckpt", ".pyc", ".pyo"}
PROC = Path("/proc")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def unaliased(path):
    path = Path(path).absolute()
    require(not any(part.is_symlink() for part in (path, *path.parents)), f"symlink path rejected: {path}")
    return path


def identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def read_bytes(path):
    path = unaliased(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), f"not a regular file: {path}")
        payload = stream.read()
        require(identity(before) == identity(os.fstat(stream.fileno())) == identity(path.stat()),
                f"file changed while reading: {path}")
    return payload


def digest(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("nonfinite JSON constant: " + value)


def read(path):
    return json.loads(read_bytes(path), object_pairs_hook=unique_object, parse_constant=reject_constant)


def write_new(path, payload):
    path = unaliased(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def write_json(path, value):
    write_new(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())


def available(path):
    return unaliased(path).is_file()


def pinned_plan(root):
    root = unaliased(root)
    require(root.name == "seed0" and root.parent.name == ROOT_NAME, "only the selected seed0 root is allowed")
    require(digest(root / "plan.json") == read(root / "plan.sha256.json")["sha256"] == PLAN_SHA, "native plan pin changed")
    plan = read(root / "plan.json")
    require(type(plan["seed"]) is int and plan["seed"] == 0 and plan["device"] == "0" and plan["arms"] == list(ARMS) and
            plan["controller_seconds"] == 1200 and plan["cleanup_seconds"] == 140, "selected allocation/contract changed")
    require(plan["source_hashes"]["two_habit_runner"] == RUNNER_SHA and
            Path(plan["materialroot"]) == root.parent / "material", "runner/material binding changed")
    return plan


def launch_record(root, plan):
    launch = read(root / "launch/launch.json")
    require(launch["pid"] == CONTROLLER_PID and type(launch["pid"]) is int and launch["node"] == 3 and
            launch["seed"] == 0 and launch["device"] == "0" and launch["plan_sha256"] == PLAN_SHA and
            launch["script_sha256"] == RUNNER_SHA and launch["source"] == plan["source_root"] and
            launch["bound_seconds"] == 1200 and launch["continuous_reservation"] is True, "selected launch binding changed")
    require(datetime.datetime.fromisoformat(launch["started_utc"]) == datetime.datetime.fromisoformat(STARTED_UTC),
            "selected launch timestamp changed")
    return launch


def status(root):
    root = unaliased(root)
    plan = pinned_plan(root)
    launch = launch_record(root, plan) if available(root / "launch/launch.json") else None
    terminal = read(root / "run/terminal.json") if available(root / "run/terminal.json") else None
    if terminal is not None:
        require(terminal["controller_pid"] == CONTROLLER_PID and terminal["plan_sha256"] == PLAN_SHA and
                terminal["seed"] == 0 and terminal["device"] == "0", "terminal allocation changed")
    arms = {}
    for arm in ARMS:
        stage = root / "run" / arm
        markers = {key: available(stage / name) for key, name in dict(
            fit_process="fit-worker/process.json", fit_supervision="fit-worker/supervision.json",
            adapter_done="adapter/DONE", fit_manifest="adapter/train_manifest.json", fit_result="fit-result.json",
            readout_plan="readout/plan.json", readout_process="readout/run/worker/process.json",
            readout_supervision="readout/run/worker/supervision.json", capture_manifest="readout/run/data/manifest.json",
            reduction="readout/reduction.json", scores="two-habit-scores.json", result="result.json").items()}
        states = (("result", "ARM_RECORDED"), ("reduction", "SCORING_OR_POSTCHECK"),
                  ("capture_manifest", "READOUT_REDUCTION_OR_POSTCHECK"), ("readout_process", "READOUT_IN_PROGRESS"),
                  ("readout_plan", "READOUT_PREPARATION"), ("fit_result", "BETWEEN_FIT_AND_READOUT"),
                  ("adapter_done", "FIT_POSTCHECK"), ("fit_process", "FIT_IN_PROGRESS"))
        arms[arm] = dict(stage=next((label for key, label in states if markers[key]), "NOT_STARTED_OR_PREPARING"),
                         artifact_markers=markers)
    return dict(seed=0, device="0", pid=CONTROLLER_PID, launch_available=launch is not None,
        controller_present=None if launch is None else (PROC / str(CONTROLLER_PID)).exists(),
        terminal_available=terminal is not None, terminal_status=terminal["status"] if terminal else None,
        terminal_error=terminal.get("error") if terminal else None, arms=arms,
        scope="artifact progress markers only; not scores, fit validity, cleanup or scientific success")


def stopped(observed):
    require(observed["launch_available"] and observed["controller_present"] is False and observed["terminal_available"],
            "finish requires selected controller absent and terminal present; no retry/launch")


def bind(source):
    require(unaliased(source).name == SOURCE_NAME and digest(RUNNER) == RUNNER_SHA, "source/runner pin differs")
    require(digest(source / "gpu/astra_mini_sudoku_diagnostic.py") == GPU_CHECK_SHA, "full-vacancy helper source changed")
    spec = importlib.util.spec_from_file_location("two_habit_collection_runner", RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.bind(source)
    from gpu import astra_mini_sudoku_diagnostic as vacancy_helper
    require(Path(vacancy_helper.__file__).resolve() == (source / "gpu/astra_mini_sudoku_diagnostic.py").resolve(),
            "wrong full-vacancy helper import")
    return runner, vacancy_helper.check_free


def successful(receipt, device):
    require(all(receipt[key] is True for key in ("ok", "reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) and
            receipt["returncode"] == 0 and receipt["device"] == device, "unverified successful worker/cleanup")


def audit_readout(stage, arm, plan, terminal, fit, runner, tokenizer):
    root = stage / "readout"
    data = root / "run/data"
    if available(data / "manifest.json"):
        require(read(data / "manifest.json")["files"] == runner.base.tree_hashes(data, ("manifest.json",)), "capture manifest changed")
    if not available(root / "reduction.json"):
        require(terminal["status"] != "COMPLETE", "complete controller missing reduction")
        return dict(status="PARTIAL_OR_NOT_STARTED", native_complete_verified=False)
    require(fit is not None, "reduction without verified completed adapter")
    readplan, cases = runner.readout.verify(root)
    require(all(readplan[key] == plan["parent"]["readout"][key] for key in ("cases", "requests", "native_inputs")) and
            readplan["adapter"] == fit["adapter"] and readplan["adapter_files"] == fit["adapter_files"] and
            readplan["device"] == "0" and readplan["lease_end"] == terminal["effective_deadline"], "readout lineage/input binding differs")
    successful(read(root / "run/worker/supervision.json"), "0")
    require(not available(data / "failure.json") and read(data / "backend.cleanup.json")["closed"] is True, "failed readout/cleanup")
    require(read(data / "identity.json") == dict(backend=readplan["identity"], model_files=readplan["model_files"],
            adapter_files=readplan["adapter_files"]), "readout capture identity differs")
    expected = {request["call_id"] + suffix for request in readplan["requests"] for suffix in (".request.json", ".response.json")}
    require({path.name for path in (data / "calls").iterdir()} == expected, "all48 raw pairs required; missing is not zero")
    rows, last_ended = [], 0.0
    for request, native, case in zip(readplan["requests"], readplan["native_inputs"], cases, strict=True):
        sent = read(data / "calls" / (request["call_id"] + ".request.json"))
        received = read(data / "calls" / (request["call_id"] + ".response.json"))
        response = received["response"]
        require(sent["request"] == request and sent["identity"] == readplan["identity"] and
                sent["prompt_sha256"] == runner.base.value_hash(request["prompt"]) and
                received["response_sha256"] == runner.base.value_hash(response) and
                all(response[key] == native[key] for key in ("rendered_prompt", "prompt_token_ids")), "native raw response binding differs")
        require(math.isfinite(sent["started"]) and math.isfinite(received["ended"]) and
                last_ended <= sent["started"] <= received["ended"], "raw call timing differs")
        last_ended = received["ended"]
        runner.base.validate_response(request, response)
        score = (runner.readout.score_addition if case["kind"] == "addition" else runner.readout.score_memory)(response["text"], case["expected"])
        rows.append(dict(call_id=request["call_id"], case_id=case["id"], kind=case["kind"], **score))
    runner.base.audit_native_calls(tokenizer, data)
    reduced = read(root / "reduction.json")
    require(reduced["complete"] is True and reduced["counts"]["total"] == len(rows) == 48 and reduced["rows"] == rows and
            reduced["plan_sha256"] == digest(root / "plan.json") and reduced["capture_sha256"] == digest(data / "manifest.json") and
            reduced["identity"] == readplan["identity"] and reduced["adapter_files"] == fit["adapter_files"] and
            reduced["model_files"] == plan["model_files"], "stored reduction/raw capture differs")
    addition = [row for row in rows if row["kind"] == "addition"]
    memory = [row for row in rows if row["kind"] == "memory_recall"]
    counts = dict(total=48, addition=dict(total=32, correct_action=sum(row["correct_action"] for row in addition),
        invalid_action=sum(not row["action_valid"] for row in addition), adherence=sum(row["adherence"] for row in addition)),
        memory=dict(total=16, correct=sum(row["correct"] for row in memory), invalid=sum(not row["valid"] for row in memory)))
    require(len(addition) == 32 and len(memory) == 16 and reduced["counts"] == counts and
            reduced["source_hashes"] == readplan["source_hashes"] and reduced["native_token_text_audit"] is True and
            reduced["reserved_seconds"] == read(root / "run/worker/supervision.json")["reserved_seconds"], "reduction counts/source/cost differ")
    require(runner.base.usage(data) == read(data / "usage.json") == reduced["cost"], "native usage accounting differs")
    has_scores = available(stage / "two-habit-scores.json")
    if has_scores:
        require(read(stage / "two-habit-scores.json") == runner.score_panel(rows, arm=arm), "stored symmetric scores differ")
    require(has_scores or terminal["status"] != "COMPLETE", "complete arm missing symmetric scores")
    return dict(status="COMPLETE_CAPTURE_VERIFIED", native_complete_verified=True, symmetric_scores_verified=has_scores,
                reduction_sha256=digest(root / "reduction.json"), capture_sha256=digest(data / "manifest.json"))


def native_audit(root, source, runner):
    plan = runner.verify(root)
    require(plan == pinned_plan(root) and plan["source_root"] == str(source), "native source/plan differs")
    terminal = read(root / "run/terminal.json")
    require(terminal["status"] in ("COMPLETE", "FAILED_PARTIAL_NO_RETRY"), "unknown terminal status")
    launch = launch_record(root, plan)
    reservation = read(root / "run/reservation.json")
    require(all(terminal[key] == value for key, value in reservation.items()) and
            launch["command"] == [launch["command"][0], "-B", str(RUNNER), "run", "--source-root", str(source),
                                  "--runroot", str(root), "--allow-gpu"], "controller command/reservation custody differs")
    require(terminal["real_lease_end"] == plan["real_lease_end"] and math.isfinite(terminal["started"]) and
            math.isfinite(terminal["ended"]) and terminal["started"] <= terminal["ended"] and
            terminal["effective_deadline"] == min(terminal["started"] + 1200, plan["deadline"], plan["real_lease_end"] - 10),
            "controller deadline/time binding differs")
    recorded = terminal["arms"]
    require([row["arm"] for row in recorded] == list(ARMS[:len(recorded)]) and len(recorded) <= 2, "terminal arm order differs")
    tokenizer = runner.base.native_tokenizer(plan["model"])
    audits = {}
    for arm in ARMS:
        stage = root / "run" / arm
        adapter = stage / "adapter"
        fit = None
        if available(stage / "fit-result.json"):
            fit = runner.verify_fit(plan, runner.arm_row(root / "run", plan, arm))
            successful(read(stage / "fit-worker/supervision.json"), "0")
            require(read(stage / "fit-result.json") == fit, "stored fit verification differs")
        else:
            require(terminal["status"] != "COMPLETE", "complete controller missing verified fit")
        files = runner.trainer._warm_inventory(adapter) if adapter.exists() else {}
        capture = audit_readout(stage, arm, plan, terminal, fit, runner, tokenizer)
        completed = next((row for row in recorded if row["arm"] == arm), None)
        if available(stage / "result.json"):
            result = read(stage / "result.json")
            require(fit is not None and result["arm"] == arm and result["fit"] == fit and
                    result["reduction_sha256"] == digest(stage / "readout/reduction.json") and
                    result["scores_sha256"] == digest(stage / "two-habit-scores.json") and
                    result["counts"] == read(stage / "two-habit-scores.json")["counts"] and
                    result["fit_cost"] == read(stage / "fit-worker/supervision.json") and
                    result["readout_cost"] == read(stage / "readout/run/worker/supervision.json"), "arm result binding differs")
            require(completed is None or completed == result, "terminal/arm result differs")
        else:
            require(completed is None, "terminal arm missing result file")
        audits[arm] = dict(completed_fit_verified=fit is not None, adapter_files=files, capture=capture,
                          partial_adapter_preserved=bool(files) and fit is None)
    receipts = [read(path) for path in sorted((root / "run").glob("**/supervision.json"))]
    require(all(math.isfinite(row["reserved_seconds"]) and row["reserved_seconds"] >= 0 and row["device"] == "0" for row in receipts),
            "worker receipt cost/device differs")
    require(math.isfinite(terminal["reserved_seconds"]) and terminal["reserved_seconds"] >= 0, "invalid controller time")
    if terminal["worker_accounting_complete"]:
        require(all(available(path.parent / "supervision.json") for path in (root / "run").glob("**/process.json")) and
                terminal["worker_reserved_seconds"] == sum(row["reserved_seconds"] for row in receipts) and
                terminal["supervised_worker_count"] == len(receipts), "terminal worker accounting differs")
    else:
        require(terminal["worker_reserved_seconds"] is None, "unknown worker cost must not become zero")
    if terminal["status"] == "COMPLETE":
        require(len(recorded) == 2 and len(receipts) == 4 and terminal["error"] is None and terminal["release_verified"] is True and
                terminal["deadline_met"] is True and terminal["worker_accounting_complete"] is True and
                terminal["ended"] <= terminal["effective_deadline"] and
                terminal["worker_reserved_seconds"] <= terminal["reserved_seconds"] <= 1200, "invalid complete terminal")
        for receipt in receipts:
            successful(receipt, "0")
    return dict(status=terminal["status"], arms=audits, original_parent_files=plan["parent"]["parent_files"],
                source_hashes=plan["source_hashes"], model_files=plan["model_files"],
                score_scope="existing reductions/symmetric score artifacts checked against raw captures; no new probes")


def within(name):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name, "invalid archive name")
    parsed = PurePosixPath(name)
    require(not parsed.is_absolute() and all(part not in ("", ".", "..") for part in name.split("/")) and str(parsed) == name,
            "unsafe/noncanonical archive name")


def metadata(root, home):
    root, home = unaliased(root), unaliased(home)
    require(root == home / "astra_diagnostics" / ROOT_NAME / "seed0", "unexpected selected root/home")
    result = {}
    for selected in (root, root.parent / "material"):
        require(selected.is_dir(), "selected evidence directory missing")
        for directory, directories, filenames in os.walk(selected, followlinks=False):
            for name in directories + filenames:
                path = unaliased(Path(directory) / name)
                require(path.is_dir() or path.is_file(), "special evidence file rejected")
            directories[:] = [name for name in directories if name != "__pycache__"]
            for name in filenames:
                path = Path(directory) / name
                if path.suffix.lower() in EXCLUDED:
                    continue
                member = path.relative_to(home).as_posix()
                within(member)
                result[member] = digest(path)
    require(result, "empty metadata inventory")
    return dict(sorted(result.items()))


def validate_archive(stream, manifest, prefixes):
    seen = {}
    with tarfile.open(fileobj=stream, mode="r:gz") as archive:
        for member in archive:
            within(member.name)
            require(any(member.name.startswith(prefix) for prefix in prefixes) and member.isfile() and not member.issparse() and
                    member.name not in seen and member.name in manifest and member.linkname == "" and not member.pax_headers,
                    "unsafe/duplicate/unexpected archive member")
            payload = archive.extractfile(member).read()
            require(len(payload) == member.size, "truncated archive member")
            seen[member.name] = hashlib.sha256(payload).hexdigest()
    require(seen == manifest, "archive membership/hash mismatch")


def vacancy(gpu, xml, launch):
    devices = ET.fromstring(xml).findall("gpu")
    require(len(devices) == 1 and devices[0].find("processes") is not None, "full vacancy XML unavailable")
    processes = devices[0].find("processes")
    require(not list(processes) and not (processes.text or "").strip() and
            devices[0].findtext("uuid") == gpu["gpu_uuid"] == launch["gpu"]["gpu_uuid"], "GPU busy or identity differs")


def finish(root, source, home, archive=ARCHIVE):
    root, source, home, archive = map(unaliased, (root, source, home, archive))
    stopped(status(root))
    require(source == home / "astra_sources" / SOURCE_NAME, "unexpected immutable source root")
    release_json, release_xml = root / "run/main_release.json", root / "run/main_release.xml"
    validation_path = Path(str(archive) + ".validation.json")
    for path in (release_json, release_xml, archive, validation_path):
        require(not unaliased(path).exists(), "one-shot output exists; preserve it and reconcile manually: " + str(path))
    collector_sha = digest(Path(__file__))
    before = metadata(root, home)
    runner, check_free = bind(source)
    audited = native_audit(root, source, runner)
    stopped(status(root))
    plan = pinned_plan(root)
    launch = launch_record(root, plan)
    terminal = read(root / "run/terminal.json")
    gpu, xml = check_free("0")
    vacancy(gpu, xml, launch)
    observed = datetime.datetime.now(datetime.timezone.utc)
    stopped(status(root))
    require(metadata(root, home) == before and digest(Path(__file__)) == collector_sha, "evidence/collector changed during audit")
    runner.verify(root)
    for arm in ARMS:
        adapter = root / "run" / arm / "adapter"
        require((runner.trainer._warm_inventory(adapter) if adapter.exists() else {}) == audited["arms"][arm]["adapter_files"],
                "final adapter changed during collection")
    started = datetime.datetime.fromisoformat(launch["started_utc"])
    require(started.tzinfo is not None and observed >= started, "invalid full-reservation timestamps")
    xml_bytes = xml.encode()
    release = dict(full_release=True, controller_absent=True, node=3, seed=0, device="0", controller_pid=CONTROLLER_PID,
        status=terminal["status"], release_utc=observed.isoformat(), full_reservation_seconds=(observed - started).total_seconds(),
        controller_reserved_seconds=terminal["reserved_seconds"], worker_reserved_seconds=terminal["worker_reserved_seconds"],
        plan_sha256=PLAN_SHA, launch_sha256=digest(root / "launch/launch.json"), terminal_sha256=digest(root / "run/terminal.json"),
        xml_sha256=hashlib.sha256(xml_bytes).hexdigest(), collector_sha256=collector_sha, gpu=gpu,
        scope="recorded launch timestamp through full GPU0 vacancy observation, including CPU/audit waiting; not new training")
    write_new(release_xml, xml_bytes)
    write_json(release_json, release)
    require(digest(release_xml) == read(release_json)["xml_sha256"], "release JSON/XML binding differs")
    manifest = metadata(root, home)
    descriptor = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        with tarfile.open(fileobj=stream, mode="w:gz", format=tarfile.USTAR_FORMAT) as output:
            for name, expected in manifest.items():
                payload = read_bytes(home / name)
                require(hashlib.sha256(payload).hexdigest() == expected, "metadata changed during packaging")
                member = tarfile.TarInfo(name)
                member.size, member.mode = len(payload), 0o600
                output.addfile(member, io.BytesIO(payload))
        stream.flush()
        os.fsync(stream.fileno())
    prefixes = [(selected.relative_to(home).as_posix() + "/") for selected in (root, root.parent / "material")]
    validate_archive(io.BytesIO(read_bytes(archive)), manifest, prefixes)
    require(metadata(root, home) == manifest and digest(Path(__file__)) == collector_sha, "evidence/collector changed after packaging")
    runner.verify(root)
    for arm in ARMS:
        adapter = root / "run" / arm / "adapter"
        require((runner.trainer._warm_inventory(adapter) if adapter.exists() else {}) == audited["arms"][arm]["adapter_files"],
                "final adapter changed after packaging")
    stopped(status(root))
    validation = dict(archive=str(archive), sha256=digest(archive), plan_sha256=PLAN_SHA, files=manifest,
        terminal_status=terminal["status"], audits=audited, collector_sha256=collector_sha, runner_sha256=RUNNER_SHA,
        full_vacancy_helper_sha256=GPU_CHECK_SHA,
        release_json_sha256=digest(release_json), release_xml_sha256=digest(release_xml),
        archive_roots=prefixes, excluded_suffixes=sorted(EXCLUDED), excluded_directories=["__pycache__"],
        weights="All completed/partial adapter weights retained at immutable node3 roots, excluded from capsule; hashes recorded",
        allocation="selected seed0 only; no other seed tree or allocation", retries=False)
    write_json(validation_path, validation)
    return dict(status="COLLECTED", terminal_status=terminal["status"], archive=str(archive), sha256=validation["sha256"],
                validation=str(validation_path), files=len(manifest), full_reservation_seconds=release["full_reservation_seconds"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("status", "finish"))
    args = parser.parse_args()
    home = Path.home()
    root = home / "astra_diagnostics" / ROOT_NAME / "seed0"
    source = home / "astra_sources" / SOURCE_NAME
    result = status(root) if args.stage == "status" else finish(root, source, home)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
