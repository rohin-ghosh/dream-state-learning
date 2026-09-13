"""One pinned EVENT sequence fit; its detached controller owns observed release."""

import argparse
import os
from pathlib import Path
import subprocess
from time import monotonic, sleep, time as wall_time

from gpu import astra_pcfl_event_sequence_fit as fit
from gpu import astra_pcfl_zero_fit_outer as lifecycle

SCHEMA = "pcfl.event_sequence.outer.v1"
TOTAL_SECONDS, CLEANUP_SECONDS, DETACH_SECONDS, LEASE_MARGIN = 1800, 60, 4, 21600
PIN_NAMES = ("material", "model_binding", "base_state_receipt", "replay_receipt", "archive")
require, read, write = fit.require, lifecycle.read, lifecycle.write


def _pin(pin, deadline):
    require(set(pin) == {"path", "sha256"}, "file pin fields")
    path = Path(pin["path"])
    require(path.is_absolute() and path.resolve() == path and path.is_file(), "absolute unaliased file pin required")
    fit.native.sha(pin["sha256"])
    require(lifecycle.file_hash(path, deadline) == pin["sha256"], "input/source file drift: " + str(path))


def _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline):
    for path, checksum in ((inputs_path, inputs_sha256), (allocation_path, allocation_sha256), (__file__, outer_sha256)):
        _pin({"path": str(Path(path).absolute()), "sha256": checksum}, deadline)
    inputs, allocation = read(inputs_path), read(allocation_path)
    require(inputs["schema"] == fit.SCHEMA + "/inputs", "fit input schema")
    lifecycle.validate_allocation(allocation)
    require(allocation["outer_sha256"] == outer_sha256 and inputs["gpu_uuid"] == allocation["gpu_uuid"], "allocation source/GPU binding")
    python = Path(allocation["python"])
    require(python.is_file() and (python.parent.parent / "pyvenv.cfg").is_file()
            and python.resolve() == Path(inputs["environment"]["native"]["python"]).resolve(), "input venv Python binding")
    fit.same(inputs["source_files"], fit.source_files(), "loaded fit source pins differ")
    for path, checksum in inputs["source_files"].items():
        _pin({"path": path, "sha256": checksum}, deadline)
    for name in PIN_NAMES:
        _pin(inputs[name], deadline)
    require(inputs["archive"]["sha256"] == fit.prefix.ARCHIVE_SHA256, "original archive pin")
    material = read(inputs["material"]["path"])
    fit.prefix.unseal(material, material["sha256"])
    fit.prefix.unseal(material["spec"], material["spec"]["sha256"])
    selected = material["phases"][phase]
    fit.prefix.unseal(selected, selected["sha256"])
    parent_phase, updates = fit.sequence.PHASES[phase]
    require(material["schema"] == fit.sequence.SCHEMA + "/export" and selected["phase"] == phase
            and selected["parent_phase"] == parent_phase and selected["updates"] == updates, "declared material phase binding")
    require(bool(inputs.get("predecessor")) == (parent_phase is not None), "exact immediate predecessor required")
    if parent_phase is not None:
        _pin(inputs["predecessor"], deadline)
        prior_path = Path(inputs["predecessor"]["path"])
        prior = read(prior_path)
        fit.prefix.unseal(prior, prior["sha256"])
        require(prior_path.name == "completed.json" and not (prior_path.parent / "failure.json").exists()
                and prior["schema"] == fit.SCHEMA + "/completed" and prior["status"] == "COMPLETE"
                and prior["kind"] == "NATIVE" and prior["phase"] == parent_phase
                and prior["updates"] == fit.sequence.PHASES[parent_phase][1], "predecessor phase/kind/completion")
        for key, value in (("material_sha256", inputs["material"]["sha256"]), ("model_binding", inputs["model_binding"]),
                           ("base_state_receipt", inputs["base_state_receipt"]), ("checkpoint", str(prior_path.parent / "checkpoint"))):
            fit.same(prior[key], value, "predecessor binding: " + key)
        fit.same(prior["files"], {name: value["sha256"] for name, value in lifecycle._inventory(prior_path.parent, deadline).items()
                                  if name != "completed.json"}, "predecessor inventory drift")
    return inputs, allocation, material


def validate_stage(directory, snapshot, inputs_pin, inputs, material, phase, inventory, elapsed):
    completed = read(snapshot)
    fit.prefix.unseal(completed, completed["sha256"])
    require(not (directory / "failure.json").exists() and completed["schema"] == fit.SCHEMA + "/completed"
            and completed["status"] == "COMPLETE" and completed["kind"] == "NATIVE", "fit completion/kind")
    expected = {"phase": phase, "parent_phase": fit.sequence.PHASES[phase][0], "predecessor": inputs.get("predecessor"),
                "inputs": inputs_pin, "material_sha256": inputs["material"]["sha256"], "export_sha256": material["sha256"],
                "spec_sha256": material["spec"]["sha256"], "import_sha256": material["spec"]["import_sha256"],
                "model_binding": inputs["model_binding"], "base_state_receipt": inputs["base_state_receipt"],
                "checkpoint": str(directory / "checkpoint"), "original_status": "FORMATION_FAILED", "limits": fit.sequence.LIMITS}
    for key, value in expected.items():
        fit.same(completed[key], value, "fit receipt binding: " + key)
    require(type(completed["updates"]) is int and completed["updates"] == fit.sequence.PHASES[phase][1]
            and completed["nonfinite_batches"] == 0 and completed["base_unchanged"] is True
            and completed["outer_release_required"] is True and completed["gpu_released"] is False
            and completed["full_contract_released"] is False and completed["automatic_promotion"] is False, "fit counts/scope")
    fit.same(completed["files"], {name: value["sha256"] for name, value in inventory.items() if name != "completed.json"}, "fit inventory drift")
    selected = material["phases"][phase]
    for key in ("items_sha256", "encoding_sha256"):
        fit.same(completed[key], selected[key], "fit material binding: " + key)
    fit.same(read(directory / "inputs.json"), inputs, "worker input copy drift")
    fit.same(read(directory / "corpus.json"), selected["items"], "worker corpus differs")
    manifest = read(directory / "checkpoint/train_manifest.json")
    config = fit.sequence.training_config(phase, inputs["model_path"], device="cuda")
    fit._completion(manifest, config, selected, inventory["corpus.json"]["sha256"])
    fit.v3._warm_parent(directory / "checkpoint", directory / "unused_outer_validation", config)
    fit.same(read(directory / "config.json"), manifest["config"], "saved config drift")
    fit.same(completed["warm_start"], manifest.get("warm_start"), "warm receipt drift")
    require(completed["trainable_names"] and all(name.endswith((".lora_A.default.weight", ".lora_B.default.weight"))
            for name in completed["trainable_names"]), "LoRA-only trainable names")
    times = completed["elapsed_seconds"]
    for name in ("worker", "load_and_base_check", "v3_fit_call"):
        fit.native.number(times[name])
        require(0 <= times[name] <= elapsed, "fit elapsed bound")
    require(times["load_and_base_check"] + times["v3_fit_call"] <= times["worker"], "fit nested timing")
    return completed


def controller(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_dir, *, outer_sha256, phase="S_A"):
    started, entered_wall = monotonic(), wall_time()
    require(phase in fit.sequence.PHASES, "one declared phase required")
    root = Path(outer_dir)
    require(root.is_absolute() and root.parent.is_dir() and root.parent.resolve() == root.parent, "fresh absolute outer parent")
    for protected in (Path(inputs_path).resolve().parent, Path(allocation_path).resolve(), Path(__file__).resolve().parents[1]):
        require(not root.is_relative_to(protected) and not protected.is_relative_to(root), "outer/input/source overlap")
    root.mkdir(exist_ok=False)
    directory, inputs_pin = root / "fit", {"path": str(Path(inputs_path).absolute()), "sha256": inputs_sha256}
    deadline, helper_hash = started + TOTAL_SECONDS, lifecycle.file_hash(lifecycle.__file__)
    process = expected = inputs = allocation = completed = released = None
    post_clear = False
    errors, events, observations, stage_files = [], [], {}, {}

    def failure(where, error):
        errors.append({"phase": where, "type": type(error).__name__, "error": str(error)})

    def observe(where, name, action):
        try:
            value = lifecycle._observe(root / f"{where}_{name}.json", action)
            observations[f"{where}_{name}"] = value
            return value
        except BaseException as error:
            failure(where + "_" + name, error)

    def resources(where):
        before = len(errors)
        try:
            lifecycle.check_node(allocation)
        except BaseException as error:
            failure(where + "_node", error)
            return False
        for name, action, valid in (
            ("queue", lambda: lifecycle.check_queue(allocation, deadline, release=where == "post"), lambda value: value["matched"] is True),
            ("gpu", lambda: lifecycle.check_gpu(allocation, deadline), lambda value: value["empty"] is True and value["gpu_uuid"] == allocation["gpu_uuid"]),
            ("cvd", lambda: lifecycle.check_cvd(allocation, deadline, release=True), lambda value: value["clear"] is True and value["owners"] == [] and value["unresolved"] == [])):
            value = observe(where, name, action)
            if value is not None and not valid(value):
                failure(where + "_" + name, ValueError("resource not released/matched"))
        return len(errors) == before

    try:
        write(root / "context.json", {"schema": SCHEMA, "phase": phase, "entry_monotonic": started, "entry_wall": entered_wall,
              "inputs": inputs_pin, "allocation_file_sha256": allocation_sha256, "outer_source_sha256": outer_sha256,
              "helper_sha256": helper_hash, "cleanup_seconds": CLEANUP_SECONDS, "detach_seconds": DETACH_SECONDS})
        for name, path in (("inputs", inputs_path), ("allocation", allocation_path)):
            with (root / f"{name}.input.json").open("xb") as stream:
                stream.write(Path(path).read_bytes())
        sleep(DETACH_SECONDS)
        inputs, allocation, material = _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline)
        require(lifecycle.file_hash(root / "inputs.input.json", deadline) == inputs_sha256
                and lifecycle.file_hash(root / "allocation.input.json", deadline) == allocation_sha256, "raw input snapshot drift")
        for protected in [Path(inputs["model_path"]).resolve(), *[Path(inputs[name]["path"]).resolve() for name in PIN_NAMES],
                          *([Path(inputs["predecessor"]["path"]).parent] if inputs.get("predecessor") else [])]:
            require(not root.is_relative_to(protected) and not protected.is_relative_to(root), "outer/protected input overlap")
        require(entered_wall + TOTAL_SECONDS <= allocation["lease_end"] - max(LEASE_MARGIN, allocation["lease_margin_seconds"]), "lease finish margin")
        require(lifecycle.remaining(deadline) > CLEANUP_SECONDS, "insufficient cleanup margin")
        source = Path(fit.__file__).resolve().parents[1]
        argv = [allocation["python"], "-B", "-m", "gpu.astra_pcfl_event_sequence_fit", "--inputs", inputs_pin["path"],
                "--inputs-sha256", inputs_sha256, "--output", str(directory), "--deadline", str(deadline - CLEANUP_SECONDS), "--phase", phase]
        write(root / "binding.json", {"controller": lifecycle.identity(os.getpid()), "argv": argv, "source_root": str(source),
              "deadline_monotonic": deadline, "worker_deadline_monotonic": deadline - CLEANUP_SECONDS,
              "lease_finish_margin_seconds": max(LEASE_MARGIN, allocation["lease_margin_seconds"])})
        require(resources("pre"), "preflight failed")
        _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline)
        require(lifecycle.file_hash(lifecycle.__file__, deadline) == helper_hash, "lifecycle helper drift")
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=allocation["gpu_uuid"], PYTHONPATH=str(source),
                           PYTHONDONTWRITEBYTECODE="1", **{key: "1" for key in fit.OFFLINE})
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
            write(root / "worker_start.json", {"identity": expected, "argv": argv, "spawn_started_monotonic": spawned})
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
                  "signal": -process.returncode if process.returncode is not None and process.returncode < 0 else None, "events": events})
            post_clear = resources("post")
            try:
                stage_files = lifecycle._inventory(directory, deadline)
                snapshot = root / "fit_completed.json"
                with snapshot.open("xb") as stream:
                    stream.write((directory / "completed.json").read_bytes())
                require(lifecycle.file_hash(snapshot, deadline) == stage_files["completed.json"]["sha256"], "fit receipt snapshot drift")
                completed = validate_stage(directory, snapshot, inputs_pin, inputs, material, phase, stage_files, monotonic() - spawned)
                _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline)
                require(lifecycle.file_hash(lifecycle.__file__, deadline) == helper_hash, "lifecycle helper drift")
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
        result = fit.prefix.seal({"schema": SCHEMA + "/collection", "status": "FAILED" if errors or completed is None else "COMPLETED",
            "phase": phase, "inputs": inputs_pin, "allocation_file_sha256": allocation_sha256, "outer_source_sha256": outer_sha256,
            "errors": errors, "elapsed_seconds": monotonic() - started, "worker_identity": expected,
            "returncode": process.returncode if process is not None else None, "observations": observations,
            "gpu_released": bool(post_clear and released and released.get("owned_group_released") is True and released.get("identity") == expected),
            "stage_inventory": stage_files, "completed_sha256": completed["sha256"] if completed else None,
            "files": files, "retries": 0, "automatic_promotion": False, "full_contract_released": False,
            "original_status": "FORMATION_FAILED", "limits": fit.sequence.LIMITS})
        write(root / "collection.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inputs", "inputs-sha256", "allocation", "allocation-sha256", "outer-sha256", "outer"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--phase", choices=tuple(fit.sequence.PHASES), default="S_A")
    args = parser.parse_args(argv)
    result = controller(args.inputs, args.inputs_sha256, args.allocation, args.allocation_sha256, args.outer,
                        outer_sha256=args.outer_sha256, phase=args.phase)
    print(fit.prefix.canonical({"status": result["status"], "outer": args.outer, "phase": args.phase}).decode())
    return int(result["status"] != "COMPLETED")


if __name__ == "__main__":
    raise SystemExit(main())
