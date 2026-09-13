"""One detached interface DEV stage with same-controller owned release."""

import argparse
import os
from pathlib import Path
import subprocess
from time import monotonic, sleep, time as wall_time

from gpu import astra_pcfl_interface_command as command
from gpu import astra_pcfl_zero_fit_outer as lifecycle

SCHEMA = "pcfl.interface.outer.v1"
TOTAL_SECONDS, CLEANUP_SECONDS, DETACH_SECONDS, LEASE_MARGIN = 3600, 120, 4, 21600
require, write = command.require, lifecycle.write


def _inputs(manifest_path, manifest_sha256, allocation_path, allocation_sha256, outer_sha256, deadline):
    command._pin({"path": str(allocation_path), "sha256": allocation_sha256}, deadline)
    command._pin({"path": str(Path(__file__).resolve()), "sha256": outer_sha256}, deadline)
    manifest = command.validate_manifest(manifest_path, manifest_sha256, deadline)
    allocation = command.read(allocation_path)
    lifecycle.validate_allocation(allocation)
    require(allocation["outer_sha256"] == outer_sha256, "allocation controller source binding")
    spec = manifest["spec"]
    require(manifest["kind"] == "OFFLINE_PREPARATION", "native preparation required")
    require(spec["gpu_uuid"] == allocation["gpu_uuid"] and spec["boot_id"] == allocation["boot_id"], "manifest GPU/boot binding")
    python = Path(allocation["python"])
    require(python.is_file() and (python.parent.parent / "pyvenv.cfg").is_file()
            and python.resolve() == Path(spec["environment"]["python"]).resolve(), "venv Python binding")
    actual = Path(command.__file__).resolve()
    paths = [Path(path) for path in manifest["sources"] if Path(path).name == actual.name]
    require(paths == [actual], "actual interface command source required")
    return manifest, allocation, actual.parents[1]


def controller(manifest_path, manifest_sha256, allocation_path, allocation_sha256, outer_dir, *, outer_sha256, stage):
    started, entered_wall = monotonic(), wall_time()
    require(stage in command.driver.STAGES, "one interface stage required")
    root = Path(outer_dir)
    require(root.is_absolute() and root.parent.is_dir() and root.parent.resolve() == root.parent, "fresh absolute outer parent")
    for protected in (Path(manifest_path).resolve().parent, Path(allocation_path).resolve(), Path(__file__).resolve().parents[1]):
        require(not root.is_relative_to(protected) and not protected.is_relative_to(root), "outer/input/source overlap")
    root.mkdir(exist_ok=False)
    process = expected = manifest = allocation = completed = None
    errors, events, observations, stage_files = [], [], {}, {}
    deadline = started + TOTAL_SECONDS

    def failure(phase, error):
        errors.append({"phase": phase, "type": type(error).__name__, "error": str(error)})

    def observe(phase, name, action):
        try:
            value = lifecycle._observe(root / f"{phase}_{name}.json", action)
            observations[f"{phase}_{name}"] = value
            return value
        except BaseException as error:
            failure(f"{phase}_{name}", error)

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
        write(root / "context.json", {"schema": SCHEMA, "entry_monotonic": started, "entry_wall": entered_wall,
            "stage": stage, "manifest_path": str(manifest_path), "manifest_file_sha256": manifest_sha256,
            "allocation_path": str(allocation_path), "allocation_file_sha256": allocation_sha256,
            "outer_source_sha256": outer_sha256, "total_seconds": TOTAL_SECONDS,
            "cleanup_seconds": CLEANUP_SECONDS, "detach_seconds": DETACH_SECONDS})
        for name, path in (("manifest.input.json", manifest_path), ("allocation.input.json", allocation_path)):
            with (root / name).open("xb") as stream:
                stream.write(Path(path).read_bytes())
        sleep(DETACH_SECONDS)
        manifest, allocation, source = _inputs(manifest_path, manifest_sha256, allocation_path, allocation_sha256, outer_sha256, deadline)
        require(manifest["stage"] == stage, "prospective stage binding")
        require(command.file_hash(root / "manifest.input.json") == manifest_sha256
                and command.file_hash(root / "allocation.input.json") == allocation_sha256, "raw input snapshot drift")
        deadline = min(deadline, manifest["spec"]["expires_monotonic"],
                       started + allocation["lease_end"] - entered_wall - max(LEASE_MARGIN, allocation["lease_margin_seconds"]))
        require(lifecycle.remaining(deadline) > CLEANUP_SECONDS, "insufficient cleanup/lease finish margin")
        stage_dir = Path(manifest["root"]) / stage
        require(not stage_dir.exists() and not stage_dir.is_symlink(), "fresh stage required; no retry")
        argv = [allocation["python"], "-B", "-m", "gpu.astra_pcfl_interface_command", "stage", "--manifest", str(manifest_path),
                "--manifest-sha256", manifest_sha256, "--deadline", str(deadline - CLEANUP_SECONDS)]
        write(root / "binding.json", {"deadline_monotonic": deadline, "worker_deadline_monotonic": deadline - CLEANUP_SECONDS,
            "controller": lifecycle.identity(os.getpid()), "argv": argv, "source_root": str(source), "stage_dir": str(stage_dir),
            "lease_finish_margin_seconds": max(LEASE_MARGIN, allocation["lease_margin_seconds"])})
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
            write(root / "worker_start.json", {"identity": expected, "argv": argv})
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
                with (root / "stage_completed.json").open("xb") as stream:
                    stream.write((stage_dir / "completed.json").read_bytes())
                require(command.file_hash(root / "stage_completed.json", deadline) == stage_files["completed.json"]["sha256"], "stage snapshot drift")
                completed = command.read(root / "stage_completed.json")
                command.driver._unseal(completed)
                require(not (stage_dir / "failure.json").exists() and completed["schema"] == command.SCHEMA + "/completed"
                        and completed["status"] == "COMPLETE" and completed["stage"] == stage
                        and completed["manifest_sha256"] == manifest["sha256"], "stage completion binding")
                require(completed["files"] == {name: value["sha256"] for name, value in stage_files.items() if name != "completed.json"}, "stage inventory drift")
                require(completed["outer_release_required"] is True and completed["gpu_released"] is False
                        and completed["kind"] == "NATIVE" and completed["full_assay_qualified"] is False
                        and completed["fits"] == completed["updates"] == 0, "stage scope drift")
                require(completed["summary"]["denominator"] == 64, "fixed task denominator")
                report = command.read(stage_dir / "records/report.json")
                command.driver._unseal(report)
                actor_identity = command.read(stage_dir / "actor/identity.json")
                close = command.read(stage_dir / "actor/close.json")
                require(report["sha256"] == completed["report_sha256"] and report["status"] == "COMPLETE"
                        and report["summary"] == completed["summary"] and report["roster_sha256"] == manifest["roster"]["sha256"], "report/completion join")
                require(actor_identity["kind"] == close["kind"] == "NATIVE" and actor_identity["pid"] == expected["pid"]
                        and actor_identity["config_sha256"] == command.digest(report["actor_config"]), "spawned actor identity join")
                require(completed["actual_calls"] == report["calls"] == close["calls_consumed"] == len(report["attempts"])
                        and completed["possible_calls"] == report["possible_calls"] == manifest["roster"]["limits"]["possible_calls"]
                        and close["token_count_calls"] == 0, "actual/possible call join")
                for value in (completed["started"], completed["ended"], completed["elapsed_seconds"]):
                    command.native.number(value)
                require(spawned <= completed["started"] <= completed["ended"] <= deadline - CLEANUP_SECONDS
                        and completed["elapsed_seconds"] == completed["ended"] - completed["started"], "stage completion clocks")
                _inputs(manifest_path, manifest_sha256, allocation_path, allocation_sha256, outer_sha256, deadline)
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
        result = command.driver.seal({"schema": SCHEMA + "/collection", "status": "FAILED" if errors or completed is None else "COMPLETED",
            "stage": stage, "manifest_file_sha256": manifest_sha256, "allocation_file_sha256": allocation_sha256,
            "outer_source_sha256": outer_sha256, "errors": errors, "elapsed_seconds": monotonic() - started,
            "worker_identity": expected, "returncode": process.returncode if process is not None else None,
            "observations": observations, "stage_inventory": stage_files, "files": files,
            "stage_summary": completed.get("summary") if completed else None, "generation_retries": 0,
            "full_assay_qualified": False, "fits": 0, "updates": 0,
            "scope": "Interface DEV custody only; completion is not ceiling pass, H1/H2, learning, C11 or a full assay."})
        write(root / "collection.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "manifest-sha256", "allocation", "allocation-sha256", "outer-sha256", "outer"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--stage", choices=command.driver.STAGES, required=True)
    args = parser.parse_args(argv)
    result = controller(args.manifest, args.manifest_sha256, args.allocation, args.allocation_sha256, args.outer,
                        outer_sha256=args.outer_sha256, stage=args.stage)
    print(command.canonical({"status": result["status"], "outer": args.outer}).decode())
    return int(result["status"] != "COMPLETED")


if __name__ == "__main__":
    raise SystemExit(main())
