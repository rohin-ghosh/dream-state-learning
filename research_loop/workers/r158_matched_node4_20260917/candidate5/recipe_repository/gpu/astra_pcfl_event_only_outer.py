"""One EVENT-only fit or cold READ arm; same detached controller owns release."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic, sleep, time as wall_time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_event_only_command as command
from gpu import astra_pcfl_zero_fit_outer as lifecycle

SCHEMA = "pcfl.event_only.outer.v1"
TOTAL_SECONDS, CLEANUP_SECONDS, DETACH_SECONDS, LEASE_MARGIN = 1800, 60, 4, 21600
require, write = command.require, lifecycle.write


def _inputs(manifest_path, manifest_sha256, allocation_path, allocation_sha256, outer_sha256, deadline):
    for path, checksum in ((manifest_path, manifest_sha256), (allocation_path, allocation_sha256), (__file__, outer_sha256)):
        command.native.sha(checksum)
        require(lifecycle.file_hash(path, deadline) == checksum, "input/source file pin drift: " + str(path))
    manifest = command.validate_manifest(manifest_path, manifest_sha256)
    allocation = command.read(allocation_path)
    lifecycle.validate_allocation(allocation)
    require(allocation["outer_sha256"] == outer_sha256, "allocation controller source binding")
    require(manifest["kind"] == "OFFLINE_PREPARATION", "native EVENT-only preparation required")
    root, spec = Path(manifest["root"]), manifest["spec"]
    require(root.is_absolute() and root.resolve() == root and Path(manifest_path) == root / "manifest.json", "manifest root/path binding")
    require(spec["gpu_uuid"] == allocation["gpu_uuid"] and spec["boot_id"] == allocation["boot_id"], "manifest GPU/boot binding")
    python = Path(allocation["python"])
    require(python.is_file() and (python.parent.parent / "pyvenv.cfg").is_file()
            and python.resolve() == Path(spec["environment"]["native"]["python"]).resolve(), "manifest venv Python binding")
    paths = [Path(path) for path in manifest["sources"] if Path(path).name == "astra_pcfl_event_only_command.py"]
    require(paths == [Path(command.__file__).resolve()], "actual EVENT-only command source required")
    for path, checksum in manifest["sources"].items():
        require(Path(path).is_absolute() and Path(path).resolve() == Path(path)
                and lifecycle.file_hash(path, deadline) == checksum, "worker source pin drift: " + path)
    return manifest, allocation, paths[0].parents[1]


def controller(manifest_path, manifest_sha256, allocation_path, allocation_sha256, outer_dir, *, outer_sha256, stage, arm=None):
    started, entered_wall = monotonic(), wall_time()
    require(stage in ("fit", "readout"), "single EVENT-only stage required")
    require(arm in command.readout_api.ARMS if stage == "readout" else arm is None, "stage/arm binding")
    root = Path(outer_dir)
    require(root.is_absolute() and root.parent.is_dir() and root.parent.resolve() == root.parent, "fresh absolute unaliased outer parent")
    for protected in (Path(manifest_path).resolve().parent, Path(allocation_path).resolve(), Path(__file__).resolve().parents[1]):
        require(not root.is_relative_to(protected) and not protected.is_relative_to(root), "outer/input/source overlap")
    root.mkdir(exist_ok=False)
    process = expected = manifest = allocation = completed = None
    errors, events, observations, stage_files = [], [], {}, {}
    deadline = started + TOTAL_SECONDS
    context = {"schema": SCHEMA, "entry_monotonic": started, "entry_wall": entered_wall, "stage": stage, "arm": arm,
               "manifest_path": str(manifest_path), "manifest_file_sha256": manifest_sha256,
               "allocation_path": str(allocation_path), "allocation_file_sha256": allocation_sha256,
               "outer_source_sha256": outer_sha256, "cleanup_seconds": CLEANUP_SECONDS, "detach_seconds": DETACH_SECONDS}

    def failure(phase, error):
        errors.append({"phase": phase, "type": type(error).__name__, "error": str(error)})

    def observe(phase, name, action):
        try:
            result = lifecycle._observe(root / f"{phase}_{name}.json", action)
            observations[f"{phase}_{name}"] = result
            return result
        except BaseException as error:
            failure(f"{phase}_{name}", error)
            return None

    def resources(phase):
        try:
            lifecycle.check_node(allocation)
        except BaseException as error:
            failure(phase + "_node", error)
            return
        for name, action, valid in (
            ("queue", lambda: lifecycle.check_queue(allocation, deadline, release=phase == "post"), lambda value: value["matched"] is True),
            ("gpu", lambda: lifecycle.check_gpu(allocation, deadline), lambda value: value["empty"] is True and value["gpu_uuid"] == allocation["gpu_uuid"]),
            ("cvd", lambda: lifecycle.check_cvd(allocation, deadline, release=True), lambda value: value["clear"] is True and value["owners"] == [] and value["unresolved"] == [])):
            value = observe(phase, name, action)
            if value is not None:
                try:
                    require(valid(value), "resource observation not clear/matched")
                except BaseException as error:
                    failure(phase + "_" + name, error)

    try:
        write(root / "context.json", context)
        for name, path in (("manifest.input.json", manifest_path), ("allocation.input.json", allocation_path)):
            with (root / name).open("xb") as stream:
                stream.write(Path(path).read_bytes())
        sleep(DETACH_SECONDS)
        manifest, allocation, source = _inputs(manifest_path, manifest_sha256, allocation_path, allocation_sha256, outer_sha256, deadline)
        require(lifecycle.file_hash(root / "manifest.input.json") == manifest_sha256
                and lifecycle.file_hash(root / "allocation.input.json") == allocation_sha256, "raw input snapshot drift")
        deadline = min(deadline, manifest["spec"]["expires_monotonic"],
                       started + allocation["lease_end"] - entered_wall - max(LEASE_MARGIN, allocation["lease_margin_seconds"]))
        require(lifecycle.remaining(deadline) > CLEANUP_SECONDS, "insufficient stage/cleanup/lease finish margin")
        stage_name = stage if stage != "readout" else "readout_" + arm
        stage_dir = Path(manifest["root"]) / stage_name
        require(not stage_dir.exists() and not stage_dir.is_symlink(), "fresh stage required; no retry")
        argv = [allocation["python"], "-B", "-m", "gpu.astra_pcfl_event_only_command", stage,
                "--manifest", str(manifest_path), "--manifest-sha256", manifest_sha256,
                "--deadline", str(deadline - CLEANUP_SECONDS)]
        if arm is not None:
            argv += ["--arm", arm]
        helper_hash = lifecycle.file_hash(lifecycle.__file__)
        write(root / "binding.json", {"deadline_monotonic": deadline, "worker_deadline_monotonic": deadline - CLEANUP_SECONDS,
              "controller": lifecycle.identity(os.getpid()), "helper_sha256": helper_hash, "argv": argv,
              "source_root": str(source), "stage_dir": str(stage_dir), "lease_finish_margin_seconds": max(LEASE_MARGIN, allocation["lease_margin_seconds"])})
        resources("pre")
        require(not errors, "preflight failed")
        _inputs(manifest_path, manifest_sha256, allocation_path, allocation_sha256, outer_sha256, deadline)
        lifecycle.remaining(deadline - CLEANUP_SECONDS)
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=allocation["gpu_uuid"], PYTHONPATH=str(source),
                           PYTHONDONTWRITEBYTECODE="1", VLLM_WORKER_MULTIPROC_METHOD="spawn", **{key: "1" for key in command.OFFLINE})
        with (root / "stdout.log").open("xb") as stdout, (root / "stderr.log").open("xb") as stderr:
            spawned = monotonic()
            process = subprocess.Popen(argv, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
            write(root / "spawn.json", {"pid": process.pid, "started_monotonic": spawned, "identity_verified": False})
            candidate = lifecycle.identity(process.pid)
            lifecycle._identity_schema(candidate)
            require(candidate["pid"] == candidate["pgid"] == candidate["sid"] == process.pid and process.pid != os.getpid()
                    and candidate["uid"] == allocation["uid"] and candidate["boot_id"] == allocation["boot_id"], "unverified worker identity; never kill unknown group")
            expected = candidate
            write(root / "worker_start.json", {"identity": expected, "spawn_started_monotonic": spawned, "argv": argv})
            returncode = observe("worker", "wait", lambda: process.wait(timeout=lifecycle.remaining(deadline - CLEANUP_SECONDS)))
            require(type(returncode) is int and returncode == 0, "worker did not exit zero")
    except BaseException as error:
        failure("controller", error)
    finally:
        if process is not None:
            if expected is not None:
                released = observe("worker", "release", lambda: lifecycle.cleanup_owned(process, expected, deadline, events))
                if released is not None and (released.get("owned_group_released") is not True or released.get("identity") != expected):
                    failure("worker_release", ValueError("owned group release not established"))
            else:
                failure("worker_release", ValueError("unknown identity: cleanup forbidden"))
            write(root / "worker_exit.json", {"pid": process.pid, "identity": expected, "returncode": process.poll(),
                  "signal": -process.returncode if process.returncode is not None and process.returncode < 0 else None,
                  "events": events, "ended_monotonic": monotonic()})
            resources("post")
            try:
                stage_files = lifecycle._inventory(stage_dir, deadline)
                if (stage_dir / "completed.json").is_file():
                    with (root / "stage_completed.json").open("xb") as stream:
                        stream.write((stage_dir / "completed.json").read_bytes())
                require(lifecycle.file_hash(root / "stage_completed.json", deadline) == stage_files["completed.json"]["sha256"], "stage receipt snapshot drift")
                completed = command.read(root / "stage_completed.json")
                require(not (stage_dir / "failure.json").exists() and completed["status"] == "COMPLETE"
                        and completed["manifest_sha256"] == manifest["sha256"] and completed["stage"] == stage_name
                        and completed["sha256"] == command.digest({key: value for key, value in completed.items() if key != "sha256"}), "stage completion binding/seal")
                require(completed["files"] == {name: value["sha256"] for name, value in stage_files.items() if name != "completed.json"}, "stage file inventory drift")
                require(completed["schema"] == command.SCHEMA + "/completed" and completed["outer_release_required"] is True
                        and completed["gpu_released"] is False and completed["kind"] == "NATIVE"
                        and completed["full_contract_released"] is False and completed["original_status"] == "FORMATION_FAILED"
                        and completed["original_returncode"] == 1, "stage completion scope")
                require((completed["calls"], completed["fits"], completed["updates"]) == ((0, 1, 200) if stage == "fit" else (28, 0, 0)), "stage counts")
                if stage == "readout":
                    actor_identity = command.read(stage_dir / "actor/identity.json")
                    require(actor_identity["pid"] == expected["pid"] and actor_identity["kind"] == "NATIVE_OWN_WRITE_READOUT", "spawned readout identity")
                for value in (completed["started"], completed["ended"], completed["elapsed_seconds"]):
                    command.native.number(value)
                require(spawned <= completed["started"] <= completed["ended"] <= deadline - CLEANUP_SECONDS
                        and completed["elapsed_seconds"] == completed["ended"] - completed["started"], "stage completion clocks")
                _inputs(manifest_path, manifest_sha256, allocation_path, allocation_sha256, outer_sha256, deadline)
                require(lifecycle.file_hash(lifecycle.__file__) == helper_hash, "lifecycle helper changed")
            except BaseException as error:
                failure("stage_evidence", error)
        try:
            lifecycle.remaining(deadline)
            if allocation is not None:
                require(wall_time() <= allocation["lease_end"] - max(LEASE_MARGIN, allocation["lease_margin_seconds"]), "lease finish margin exhausted")
        except BaseException as error:
            failure("finish_deadline", error)
        if errors:
            write(root / "failure.json", {"errors": errors})
        try:
            files = lifecycle._inventory(root, deadline)
            lifecycle.remaining(deadline)
        except BaseException as error:
            failure("collection_inventory", error)
            files = {}
            write(root / "collection_failure.json", errors[-1])
        result = {"schema": SCHEMA + "/collection", "status": "FAILED" if errors or completed is None else "COMPLETED",
                  "stage": stage, "arm": arm, "manifest_file_sha256": manifest_sha256, "allocation_file_sha256": allocation_sha256,
                  "outer_source_sha256": outer_sha256, "errors": errors, "elapsed_seconds": monotonic() - started,
                  "worker_identity": expected, "returncode": process.returncode if process is not None else None,
                  "observations": observations, "stage_inventory": stage_files,
                  "stage_completed_file_sha256": stage_files.get("completed.json", {}).get("sha256"),
                  "files": files, "generation_retries": 0,
                  "scope": "EVENT-only single-stage custody; original formation remains FAILED. No full-bank release, H1/H2, C11 or general qualification."}
        write(root / "collection.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "manifest-sha256", "allocation", "allocation-sha256", "outer-sha256", "outer"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--stage", choices=("fit", "readout"), required=True)
    parser.add_argument("--arm", choices=command.readout_api.ARMS)
    args = parser.parse_args(argv)
    result = controller(args.manifest, args.manifest_sha256, args.allocation, args.allocation_sha256, args.outer,
                        outer_sha256=args.outer_sha256, stage=args.stage, arm=args.arm)
    print(command.canonical({"status": result["status"], "outer": args.outer}).decode())
    return int(result["status"] != "COMPLETED")


if __name__ == "__main__":
    raise SystemExit(main())
