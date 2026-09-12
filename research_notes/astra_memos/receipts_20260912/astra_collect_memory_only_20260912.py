"""Read-only live status; immutable terminal collection, executed only by Main."""
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

PLAN_SHA = "0f8d1a3042b92c3c940309f0b909f7ee535c295e3c3fb6197a8d45c4c137ac90"
RUNNER_SHA = "ac7a110bc74724fc592407ced854ad162da275d3de9d9eeeb40c19788416afdb"
ROOT_NAME = "astra_fundamental_memory_only_20260912_attempt1"
SOURCE_NAME = "3a12807f88747bafd0aada1d4a09ba88b915f903"
RUNNER = Path("/tmp/astra_memory_only_20260912.py")
ARCHIVE = Path("/tmp/astra_memory_only_terminal_20260912.tgz")
EXCLUDED = {".bin", ".safetensors", ".pt", ".pth", ".ckpt", ".pyc", ".pyo"}
SEEDS = ("0", "1", "2")


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
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read(path):
    return json.loads(read_bytes(path), object_pairs_hook=unique_object)


def write_new(path, payload):
    path = unaliased(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def write_json(path, value):
    write_new(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())


def pinned_plan(root):
    root = unaliased(root)
    require(root.name == ROOT_NAME, "unexpected run root")
    require(digest(root / "plan.json") == read(root / "plan.sha256.json")["sha256"] == PLAN_SHA, "native plan pin changed")
    plan = read(root / "plan.json")
    require(plan["branches"] == {seed: dict(seed=int(seed), device=str(int(seed) + 3)) for seed in SEEDS}, "sealed seeds/devices differ")
    return plan


def available(path):
    path = unaliased(path)
    return path.is_file()


def status(root):
    plan = pinned_plan(root)
    result = {}
    for seed in SEEDS:
        stage = root / ("seed" + seed)
        launch_path = root / "launch" / ("seed" + seed) / "launch.json"
        terminal_path = stage / "terminal.json"
        launch = read(launch_path) if available(launch_path) else None
        terminal = read(terminal_path) if available(terminal_path) else None
        pid = launch.get("pid") if launch else None
        require(pid is None or (type(pid) is int and pid > 1), "invalid controller PID")
        result[seed] = dict(device=plan["branches"][seed]["device"], pid=pid,
            launch_available=launch is not None, controller_present=None if pid is None else Path(f"/proc/{pid}").exists(),
            terminal_available=terminal is not None, status=terminal.get("status") if terminal else None,
            error=terminal.get("error") if terminal else None,
            fit_result_available=available(stage / "fit-result.json"), adapter_done_available=available(stage / "adapter/DONE"),
            fit_manifest_available=available(stage / "adapter/train_manifest.json"),
            dev_reduction_available=available(stage / "dev/reduction.json"),
            dev_capture_manifest_available=available(stage / "dev/run/data/manifest.json"),
            exact_reduction_available=available(stage / "exact/reduction.json"),
            exact_capture_manifest_available=available(stage / "exact/run/data/manifest.json"))
    return result


def all_stopped(observed):
    require(set(observed) == set(SEEDS) and all(row["launch_available"] and row["terminal_available"] and
        row["controller_present"] is False for row in observed.values()), "wait for all controllers to disappear and all terminals")


def bind(source):
    require(source.name == SOURCE_NAME and digest(RUNNER) == RUNNER_SHA, "source/runner pin differs")
    spec = importlib.util.spec_from_file_location("memory_only_collection_runner", RUNNER)
    memory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(memory)
    memory.bind(source, "/tmp/astra_fading_sentinel_20260912.py")
    from gpu.astra_mini_sudoku_diagnostic import check_free
    return memory, check_free


def within(name):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name,
            "invalid relative member name")
    parsed = PurePosixPath(name)
    require(not parsed.is_absolute() and all(part not in ("", ".", "..") for part in name.split("/")) and
            str(parsed) == name, "unsafe/noncanonical relative member name")
    return parsed


def capture_files(data):
    result = {}
    for directory, directories, filenames in os.walk(data, followlinks=False):
        for name in directories + filenames:
            path = unaliased(Path(directory) / name)
            require(path.is_dir() or path.is_file(), "nonregular capture entry")
        for name in filenames:
            path = Path(directory) / name
            if path != data / "manifest.json":
                result[path.relative_to(data).as_posix()] = digest(path)
    return result


def audit_capture(root, name, module, plan, terminal, fit, memory):
    readroot = root / name
    reduction_path = readroot / "reduction.json"
    data = readroot / "run/data"
    manifest_path = data / "manifest.json"
    if available(manifest_path):
        require(read(manifest_path)["files"] == capture_files(data), f"{name} data manifest changed")
    if not available(reduction_path):
        require(terminal["status"] != "COMPLETE", f"complete seed missing {name}")
        return dict(status="PARTIAL_OR_NOT_STARTED", reduction_available=False)
    require(fit is not None, "reduction without verified fit")
    module.verify(readroot)
    readplan = memory.old.read_plan(readroot)
    reduced = read(reduction_path)
    expected_count = 48 if name == "dev" else 16
    require(reduced["complete"] is True and reduced["counts"]["total"] == expected_count and
        reduced["plan_sha256"] == digest(readroot / "plan.json") and
        reduced["capture_sha256"] == digest(manifest_path), f"{name} reduction unbound")
    require(all(readplan[key] == plan["templates"][name][key] for key in ("cases", "requests", "native_inputs")) and
        readplan["adapter"] == fit["adapter"] and readplan["adapter_files"] == fit["adapter_files"] and
        readplan["device"] == terminal["device"] and readplan["lease_end"] == terminal["effective_deadline"], "readout lineage changed")
    memory.successful(read(readroot / "run/worker/supervision.json"))
    expected = {request["call_id"] + ending for request in readplan["requests"] for ending in (".request.json", ".response.json")}
    calls = data / "calls"
    require({path.name for path in calls.iterdir()} == expected, f"{name} incomplete raw capture")
    for request, native in zip(readplan["requests"], readplan["native_inputs"], strict=True):
        sent = read(calls / (request["call_id"] + ".request.json"))
        received = read(calls / (request["call_id"] + ".response.json"))
        response = received["response"]
        require(sent["request"] == request and sent["identity"] == readplan["identity"] and
            sent["prompt_sha256"] == memory.base.value_hash(request["prompt"]) and
            received["response_sha256"] == memory.base.value_hash(response) and
            all(response[key] == native[key] for key in ("rendered_prompt", "prompt_token_ids")), "raw capture binding changed")
        memory.base.validate_response(request, response)
    require(len(reduced["rows"]) == expected_count and
        [row["case_id"] for row in reduced["rows"]] == [case["id"] for case in readplan["cases"]], "reduction row coverage changed")
    if terminal["result"] is not None:
        bound = terminal["result"]["readouts"][name]
        require(bound["sha256"] == digest(reduction_path) and bound["reduction"] == reduced, "terminal reduction changed")
    return dict(status="CAPTURE_HASHES_VERIFIED_NOT_RESCORED", reduction_available=True,
                reduction_sha256=digest(reduction_path), raw_pairs=expected_count)


def audit_seed(root, seed, plan, memory, source):
    stage = root / ("seed" + seed)
    launch_path = root / "launch" / ("seed" + seed) / "launch.json"
    launch, terminal = read(launch_path), read(stage / "terminal.json")
    reservation = read(stage / "reservation.json")
    require(terminal["status"] in ("COMPLETE", "FAILED_PARTIAL_NO_RETRY"), "unknown terminal status")
    require(launch["seed"] == seed and launch["device"] == terminal["device"] == plan["branches"][seed]["device"] and
        launch["pid"] == terminal["controller_pid"] == reservation["controller_pid"] and terminal["seed"] == int(seed) and
        launch["plan_sha256"] == terminal["plan_sha256"] == reservation["plan_sha256"] == PLAN_SHA and
        launch["script_sha256"] == RUNNER_SHA and launch["source"] == str(source) and launch["bound_seconds"] == 900,
        "launch/terminal custody changed")
    expected = [launch["command"][0], "-B", str(RUNNER), "run", "--source-root", str(source), "--runroot", str(root),
                "--seed", seed, "--allow-gpu"]
    require(launch["command"] == expected and all(terminal[key] == value for key, value in reservation.items()), "controller command/reservation changed")
    require(math.isfinite(terminal["reserved_seconds"]) and terminal["reserved_seconds"] >= 0, "invalid controller cost")
    fit_path = stage / "fit-result.json"
    fit = read(fit_path) if available(fit_path) else None
    if fit is not None:
        adapter = stage / "adapter"
        require(fit["adapter"] == str(adapter) and available(adapter / "DONE") and
            memory.trainer._warm_inventory(adapter) == fit["adapter_files"], "successful child inventory changed")
        parent = plan["parents"][seed]["parent"]
        memory.validate_manifest(plan, seed, read(adapter / "train_manifest.json"),
            memory.old.state_inventory(parent), memory.old.state_inventory(adapter))
        receipt = read(stage / "fit-worker/supervision.json")
        memory.successful(receipt)
        require(fit["supervision"] == receipt, "fit supervision changed")
        if terminal["result"] is not None:
            require(terminal["result"]["fit"] == fit, "terminal fit changed")
    else:
        require(terminal["status"] != "COMPLETE" and terminal["result"] is None, "successful terminal without fit")
    captures = {name: audit_capture(stage, name, module, plan, terminal, fit, memory)
                for name, module in (("dev", memory.dev), ("exact", memory.exact))}
    if terminal["status"] == "COMPLETE":
        receipts = [read(path) for path in stage.rglob("supervision.json")]
        require(len(receipts) == 3 and terminal["error"] is None and terminal["release_verified"] is True and
            terminal["deadline_met"] is True and terminal["ended"] <= terminal["effective_deadline"] and
            terminal["reserved_seconds"] <= 900 and terminal["result"] is not None, "invalid complete terminal")
        for receipt in receipts:
            memory.successful(receipt)
    return dict(status=terminal["status"], successful_fit_verified=fit is not None,
                partial_adapter_preserved=fit is None and (stage / "adapter").exists(), captures=captures)


def metadata(root, home):
    root, home = unaliased(root), unaliased(home)
    prefix = root.relative_to(home).as_posix() + "/"
    result = {}
    for directory, directories, filenames in os.walk(root, followlinks=False):
        for name in directories + filenames:
            path = unaliased(Path(directory) / name)
            require(path.is_dir() or path.is_file(), f"special file rejected: {path}")
        directories[:] = [name for name in directories if name != "__pycache__"]
        for name in sorted(filenames):
            path = Path(directory) / name
            if path.suffix.lower() in EXCLUDED:
                continue
            member = path.relative_to(home).as_posix()
            within(member)
            require(member.startswith(prefix), "metadata escaped run root")
            result[member] = digest(path)
    require(result, "empty metadata inventory")
    return dict(sorted(result.items()))


def validate_archive(stream, manifest, prefix):
    seen = {}
    with tarfile.open(fileobj=stream, mode="r:gz") as archive:
        for member in archive:
            within(member.name)
            require(member.name.startswith(prefix) and member.isfile() and not member.issparse() and
                member.name not in seen and member.name in manifest, "unsafe/duplicate/unexpected archive member")
            require(member.linkname == "" and not member.pax_headers, "archive link/extended header rejected")
            payload = archive.extractfile(member).read()
            require(len(payload) == member.size, "truncated archive member")
            seen[member.name] = hashlib.sha256(payload).hexdigest()
    require(seen == manifest, "archive inventory/hash mismatch")
    return len(seen)


def release_pair(root, seed, expected=None):
    stage = root / ("seed" + seed)
    json_path, xml_path = stage / "main_release.json", stage / "main_release.xml"
    present = available(json_path), available(xml_path)
    require(present[0] == present[1], "orphan release JSON/XML preserved; manual reconciliation required")
    if not present[0]:
        return None
    release = read(json_path)
    launch_path = root / "launch" / ("seed" + seed) / "launch.json"
    launch, terminal = read(launch_path), read(stage / "terminal.json")
    require(release["full_release"] is True and release["controller_absent"] is True and
        release["controller_pid"] == launch["pid"] and release["device"] == launch["device"] and
        release["status"] == terminal["status"] and release["terminal_sha256"] == digest(stage / "terminal.json") and
        release["launch_sha256"] == digest(launch_path) and release["xml_sha256"] == digest(xml_path) and
        release["plan_sha256"] == PLAN_SHA and release["gpu"]["gpu_uuid"] == launch["gpu"]["gpu_uuid"],
        "immutable release record changed")
    elapsed = (datetime.datetime.fromisoformat(release["release_utc"]) -
               datetime.datetime.fromisoformat(launch["started_utc"])).total_seconds()
    require(math.isfinite(elapsed) and elapsed >= 0 and elapsed == release["full_reservation_seconds"], "release cost binding differs")
    if expected is not None:
        require(release["gpu"]["gpu_uuid"] == expected["gpu_uuid"], "GPU identity changed")
    return release


def existing_capsule(root, home, archive):
    validation_path = Path(str(archive) + ".validation.json")
    archive_exists, validation_exists = archive.exists(), validation_path.exists()
    require(archive_exists == validation_exists, "partial capsule preserved; never overwrite/recreate it")
    if not archive_exists:
        return None
    validation = read(validation_path)
    require(validation["archive"] == str(archive) and validation["plan_sha256"] == PLAN_SHA and
        digest(archive) == validation["sha256"], "existing capsule binding changed")
    require(metadata(root, home) == validation["files"], "source evidence changed since archive")
    for seed in SEEDS:
        require(release_pair(root, seed) is not None, "existing capsule missing release pair")
    payload = read_bytes(archive)
    validate_archive(io.BytesIO(payload), validation["files"], root.relative_to(home).as_posix() + "/")
    return dict(status="ALREADY_COLLECTED_VERIFIED_NO_WRITES", archive=str(archive), sha256=validation["sha256"], files=len(validation["files"]))


def finish(root, source, home, archive=ARCHIVE):
    all_stopped(status(root))
    unaliased(archive)
    unaliased(Path(str(archive) + ".validation.json"))
    existing = existing_capsule(root, home, archive)
    if existing is not None:
        return existing
    original_metadata = metadata(root, home)
    memory, check_free = bind(source)
    plan = memory.verify(root)
    audits = {seed: audit_seed(root, seed, plan, memory, source) for seed in SEEDS}
    all_stopped(status(root))
    for seed in SEEDS:
        release_pair(root, seed)
    observations = {}
    for seed in SEEDS:
        gpu, xml = check_free(plan["branches"][seed]["device"])
        observations[seed] = gpu, xml, datetime.datetime.now(datetime.timezone.utc)
    all_stopped(status(root))
    require(metadata(root, home) == original_metadata, "evidence changed during terminal verification")
    for seed in SEEDS:
        gpu, xml, observed = observations[seed]
        if release_pair(root, seed, gpu) is not None:
            continue
        stage = root / ("seed" + seed)
        launch_path = root / "launch" / ("seed" + seed) / "launch.json"
        launch, terminal = read(launch_path), read(stage / "terminal.json")
        require(gpu["gpu_uuid"] == launch["gpu"]["gpu_uuid"], "released GPU differs from launched GPU")
        started = datetime.datetime.fromisoformat(launch["started_utc"])
        require(started.tzinfo is not None and observed >= started, "invalid launch time")
        xml_bytes = xml.encode()
        release = dict(full_release=True, controller_absent=True, controller_pid=launch["pid"],
            device=launch["device"], gpu=gpu, status=terminal["status"], release_utc=observed.isoformat(),
            full_reservation_seconds=(observed-started).total_seconds(), plan_sha256=PLAN_SHA,
            launch_sha256=digest(launch_path), terminal_sha256=digest(stage / "terminal.json"),
            xml_sha256=hashlib.sha256(xml_bytes).hexdigest(), collector_sha256=digest(Path(__file__)))
        write_new(stage / "main_release.xml", xml_bytes)
        write_json(stage / "main_release.json", release)
    memory.verify(root)
    all_stopped(status(root))
    manifest = metadata(root, home)
    release_names = {(root / ("seed" + seed) / ("main_release." + ending)).relative_to(home).as_posix()
                     for seed in SEEDS for ending in ("json", "xml")}
    require(set(manifest) == set(original_metadata) | release_names and
        all(manifest[name] == expected for name, expected in original_metadata.items()),
        "verified evidence changed before packaging")
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
    validate_archive(io.BytesIO(read_bytes(archive)), manifest, root.relative_to(home).as_posix() + "/")
    require(metadata(root, home) == manifest, "metadata changed after packaging")
    all_stopped(status(root))
    validation = dict(archive=str(archive), sha256=digest(archive), plan_sha256=PLAN_SHA, files=manifest,
        statuses=status(root), audits=audits, collector_sha256=digest(Path(__file__)),
        excluded_suffixes=sorted(EXCLUDED), excluded_directories=["__pycache__"],
        weights="Preserved at original immutable node3 roots; excluded from metadata capsule",
        score_scope="Existing scores preserved and capture bindings checked; not independently rescored")
    write_json(Path(str(archive) + ".validation.json"), validation)
    return dict(status="COLLECTED", archive=str(archive), sha256=validation["sha256"], files=len(manifest), audits=audits)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("status", "finish"))
    args = parser.parse_args()
    home = Path.home()
    root = home / "astra_diagnostics" / ROOT_NAME
    source = home / "astra_sources" / SOURCE_NAME
    result = status(root) if args.stage == "status" else finish(root, source, home)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
