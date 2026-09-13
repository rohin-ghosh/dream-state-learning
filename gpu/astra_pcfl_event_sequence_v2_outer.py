"""DEV-only v2 fit/readout; later fits require raw-bound acquisition and release."""

import argparse
import os
from pathlib import Path
import subprocess
from time import monotonic, sleep, time as wall_time

from gpu import astra_pcfl_event_sequence_v2_fit as fit
from gpu import astra_pcfl_event_sequence_v2_readout as readout
from gpu import astra_pcfl_zero_fit_outer as lifecycle

SCHEMA = "pcfl.event_sequence.outer.v2"
TOTAL_SECONDS, CLEANUP_SECONDS, DETACH_SECONDS, LEASE_MARGIN = 1800, 60, 4, 21600
PIN_NAMES = ("material", "model_binding", "base_state_receipt", "replay_receipt", "archive")
require, read, write = fit.require, lifecycle.read, lifecycle.write


def _pin(pin, deadline):
    require(set(pin) == {"path", "sha256"}, "file pin fields")
    path = Path(pin["path"])
    require(path.is_absolute() and path.resolve() == path and path.is_file(), "absolute unaliased file pin required")
    fit.native.sha(pin["sha256"])
    require(lifecycle.file_hash(path, deadline) == pin["sha256"], "input/source file drift: " + str(path))


def _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline, *, stage="fit", state=None, output=None):
    for path, checksum in ((inputs_path, inputs_sha256), (allocation_path, allocation_sha256), (__file__, outer_sha256)):
        _pin({"path": str(Path(path).absolute()), "sha256": checksum}, deadline)
    inputs, allocation = read(inputs_path), read(allocation_path)
    require(phase in fit.sequence.PHASES and (stage == "fit" and state is None or stage == "readout" and state in fit.sequence.READ_STATES),
            "known v2 phase and explicit readout state required")
    worker = fit if stage == "fit" else readout
    require(inputs["schema"] == worker.SCHEMA + "/inputs", "stage input schema")
    lifecycle.validate_allocation(allocation)
    require(allocation["outer_sha256"] == outer_sha256 and inputs["gpu_uuid"] == allocation["gpu_uuid"], "allocation source/GPU binding")
    python = Path(allocation["python"])
    require(python.is_file() and (python.parent.parent / "pyvenv.cfg").is_file()
            and python.resolve() == Path(inputs["environment"]["native"]["python"]).resolve(), "input venv Python binding")
    fit.same(inputs["source_files"], worker.source_files(), "loaded stage source pins differ")
    for path, checksum in inputs["source_files"].items():
        _pin({"path": path, "sha256": checksum}, deadline)
    for name in PIN_NAMES:
        _pin(inputs[name], deadline)
    require(inputs["archive"]["sha256"] == fit.prefix.ARCHIVE_SHA256, "original archive pin")
    material = read(inputs["material"]["path"])
    fit.prefix.unseal(material, material["sha256"])
    fit.prefix.unseal(material["spec"], material["spec"]["sha256"])
    fit.sequence._seed(material["spec"]["learner_seed"])
    if stage == "readout":
        require(material["schema"] == fit.sequence.SCHEMA + "/export", "material schema")
        _pin(inputs["shutdown_binding"], deadline)
        if inputs.get("fit_receipt"):
            _pin(inputs["fit_receipt"], deadline)
        readout._checkpoint(inputs, material, state, output, "NATIVE")
        require(len(material["spec"]["roster"]) == 16
                and all(row["output_tokens"] == 2048 for row in material["spec"]["roster"]), "fixed readout roster")
        fit.same(fit.prefix.digest(material["spec"]["roster"]), material["spec"]["roster_sha256"], "readout roster seal")
        return inputs, allocation, material
    fit.sequence._seed(inputs["learner_seed"])
    fit.same(inputs["learner_seed"], material["spec"]["learner_seed"], "learner seed drift")
    fit.require_acquisition(inputs, material, phase)
    selected = material["phases"][phase]
    fit.prefix.unseal(selected, selected["sha256"])
    parent_phase, updates = fit.sequence.PHASES[phase]
    require(material["schema"] == fit.sequence.SCHEMA + "/export" and selected["phase"] == phase
            and selected["parent_phase"] == parent_phase and selected["updates"] == updates, "declared material phase binding")
    config = fit.sequence.training_config(phase, inputs["model_path"], learner_seed=inputs["learner_seed"], device="cuda")
    fit.validate_predecessor(inputs, material, phase, output, config, "NATIVE")
    return inputs, allocation, material


def validate_stage(directory, snapshot, inputs_pin, inputs, material, phase, inventory, elapsed):
    completed = read(snapshot)
    fit.prefix.unseal(completed, completed["sha256"])
    require(not (directory / "failure.json").exists() and completed["schema"] == fit.SCHEMA + "/completed"
            and completed["status"] == "COMPLETE" and completed["kind"] == "NATIVE", "fit completion/kind")
    expected = {"learner_seed": inputs["learner_seed"], "phase": phase, "parent_phase": fit.sequence.PHASES[phase][0], "predecessor": inputs.get("predecessor"),
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
    config = fit.sequence.training_config(phase, inputs["model_path"], learner_seed=inputs["learner_seed"], device="cuda")
    fit._completion(manifest, config, selected, inventory["corpus.json"]["sha256"])
    fit.v3._warm_parent(directory / "checkpoint", directory / "unused_outer_validation", config)
    fit.same(read(directory / "config.json"), manifest["config"], "saved config drift")
    fit.same(completed["warm_start"], manifest.get("warm_start"), "warm receipt drift")
    gate = fit.require_acquisition(inputs, material, phase)
    fit.same(completed["acquisition_validation"], gate or "NOT_REQUIRED_A200", "acquisition evidence differs")
    require(completed["descendants_enabled"] is False, "no automatic promotion")
    if fit.sequence.PHASES[phase][0] is None:
        require(completed["warm_start"] is None, "cold phase requires clean C0")
    else:
        parent, prior, _ = fit.validate_predecessor(inputs, material, phase, directory, config, "NATIVE")
        fit.same(completed["warm_start"]["parent_path"], str(parent), "warm parent path differs")
        fit.same(completed["warm_start"]["cumulative_steps"], prior["updates"] + completed["updates"], "warm cumulative steps differ")
        fit.validate_warm_tensors(completed["warm_start"], completed["trainable_names"])
    require(completed["trainable_names"] and all(name.endswith((".lora_A.default.weight", ".lora_B.default.weight"))
            for name in completed["trainable_names"]), "LoRA-only trainable names")
    times = completed["elapsed_seconds"]
    for name in ("worker", "load_and_base_check", "v3_fit_call"):
        fit.native.number(times[name])
        require(0 <= times[name] <= elapsed, "fit elapsed bound")
    require(times["load_and_base_check"] + times["v3_fit_call"] <= times["worker"], "fit nested timing")
    return completed


def validate_readout(directory, snapshot, inputs_pin, inputs, material, state, inventory, elapsed, identity, deadline):
    completed = read(snapshot)
    fit.prefix.unseal(completed, completed["sha256"])
    require(not (directory / "failure.json").exists(), "failed readout")
    expected = {"schema": readout.SCHEMA + "/completed", "status": "COMPLETE", "kind": "NATIVE", "state": state,
        "learner_seed": material["spec"]["learner_seed"],
        "inputs": inputs_pin, "material_sha256": inputs["material"]["sha256"], "spec_sha256": material["spec"]["sha256"],
        "import_sha256": material["spec"]["import_sha256"], "fit_receipt": inputs.get("fit_receipt"),
        "calls": 16, "fits": 0, "updates": 0, "outer_release_required": True, "gpu_released": False,
        "full_contract_released": False, "automatic_promotion": False, "original_status": "FORMATION_FAILED", "limits": fit.sequence.LIMITS}
    for key, value in expected.items():
        fit.same(completed[key], value, "readout receipt binding: " + key)
    fit.same(completed["files"], {name: value["sha256"] for name, value in inventory.items() if name != "completed.json"}, "readout inventory drift")
    fit.same(read(directory / "inputs.json"), inputs, "worker input copy drift")
    settings = read(directory / "readout_config.json")
    for key in ("model_path", "model_binding", "source_files", "gpu_uuid", "shutdown_binding"):
        fit.same(settings[key], inputs[key], "readout settings binding: " + key)
    expected_settings = {"schema": readout.reader.SCHEMA, "environment": inputs["environment"]["native"],
        "roster": material["spec"]["roster"], "roster_sha256": material["spec"]["roster_sha256"],
        "tokenizer_files": material["tokenizer_receipt"]["tokenizer_files"],
        "chat_template_sha256": material["tokenizer_receipt"]["chat_template_sha256"], "engine": readout.reader.ENGINE,
        "output_dir": str(directory / "actor"), "deadline": deadline - CLEANUP_SECONDS, "device_seconds_cap": readout.CAP_SECONDS,
        "max_calls": 16, "max_input_tokens": 14336, "max_output_tokens": 2048,
        "arm": "NO_WRITE_C0" if state == "NO_WRITE" else "AUTH_WRITE"}
    for key, value in expected_settings.items():
        fit.same(settings[key], value, "readout config binding: " + key)
    checkpoint, _, _ = readout._checkpoint(inputs, material, state, directory, "NATIVE")
    adapter = None
    if checkpoint is not None:
        files = {name: {"size": (checkpoint / name).stat().st_size, "sha256": lifecycle.file_hash(checkpoint / name, deadline)}
                 for name in ("adapter_config.json", "adapter_model.safetensors", "README.md") if (checkpoint / name).is_file()}
        adapter = {"name": "pcfl-own-write", "id": 1, "path": str(directory / "adapter"), "files": files}
        fit.same({name.removeprefix("adapter/"): value for name, value in inventory.items() if name.startswith("adapter/")}, files, "adapter mount bytes differ")
        fit.same(read(directory / "adapter_projection.json"), {"kind": "BYTE_IDENTICAL_MOUNT_COPY_NO_TRAINING",
                 "source_checkpoint": str(checkpoint), "adapter": adapter}, "adapter projection differs")
    else:
        require(not any(name.startswith("adapter/") or name == "adapter_projection.json" for name in inventory), "NO_WRITE adapter forbidden")
    fit.same(settings["adapter"], adapter, "selected state adapter differs")
    route = readout.reader.route_identity(settings)
    actor = directory / "actor"
    loaded, load, close = (read(actor / name) for name in ("identity.json", "load.json", "close.json"))
    custody, scores = read(directory / "custody.json"), read(directory / "scores.json")
    require(loaded["pid"] == identity["pid"] and loaded["kind"] == load["kind"] == close["kind"] == custody["kind"] == "NATIVE_OWN_WRITE_READOUT", "native spawned readout custody")
    fit.same(read(actor / "config.json"), settings, "actor config drift")
    fit.same(loaded["config_sha256"], fit.prefix.digest(settings), "actor config seal")
    fit.same(custody["identity_sha256"], fit.prefix.digest(loaded), "custody identity seal")
    for captured in (completed["route"], loaded["identity"]["route"], load["route"], close["route"], custody["route"]):
        fit.same(captured, route, "native route mismatch")
    fit.same(close, read(directory / "actor_close.json"), "actor close copy")
    require(close["calls_consumed"] == close["planned_calls"] == custody["calls"] == 16 and close["error_type"] is None
            and close["failed"] is False and close["budget_exceeded"] is False and close["shutdown"]["shutdown_returned"] is True
            and close["shutdown"]["source"] == load["shutdown"]["source"] == inputs["shutdown_binding"], "readout load/close/count/shutdown")
    require(scores["state"] == state and scores["denominator"] == len(scores["results"]) == 16 and scores["pass_threshold"] is None, "readout score denominator")
    for pattern in ("actor/call_*.raw.json", "response_*.json"):
        require(len(list(directory.glob(pattern))) == 16, "exact readout capture inventory")
    tokens, truncated, generation = {"prompt": 0, "output": 0}, 0, 0.0
    for index, row in enumerate(settings["roster"]):
        response = read(directory / f"response_{index:04d}.json")
        raw, returned, request, render = (read(actor / f"call_{index:04d}{suffix}.json") for suffix in (".raw", ".response", ".request", ".render"))
        require(raw["kind"] == "NATIVE_OWN_WRITE_READOUT" and raw["route"] == raw["raw"]["route"] == response["route"] == render["route"] == route, "raw native route")
        require(request["row"] == row and request["request"] == {"id": row["id"]}
                and request["messages"] == readout.reader.public_messages(row) and response["id"] == row["id"]
                and response["request_sha256"] == fit.prefix.digest({"id": row["id"]})
                and response["roster_sha256"] == settings["roster_sha256"], "ordered readout request join")
        require(returned["response"] == response and returned["raw_hex"] == response["text"].encode().hex()
                and returned["raw_utf8_sha256"] == fit.native.text_hash(response["text"])
                and all(raw["raw"][key] == response[key] for key in ("text", "finish_reason", "stop_reason")), "raw response bytes")
        require(raw["raw"]["prompt_token_ids"] == render["prompt_token_ids"]
                and render["sampling"] == {**fit.native.SAMPLING, "seed": row["seed"], "max_tokens": 2048}
                and load["model_load_started"] <= load["ready_at"] <= raw["generation_started"] <= raw["generation_ended"] <= settings["deadline"], "readout sampling/cold chronology")
        for key in tokens:
            count = len(fit.native.token_ids(raw["raw"][key + "_token_ids"]))
            cap = settings["max_output_tokens" if key == "output" else "max_input_tokens"]
            require(response[key + "_tokens"] == count <= cap, "readout token count/cap")
            tokens[key] += count
        truncated += response["finish_reason"] == "length"
        generation += raw["generation_ended"] - raw["generation_started"]
        result, record = scores["results"][index], material["spec"]["records"][index % 8]
        for key, value in {"id": row["id"], "request": row["request"], "view": row["view"], "bank": record["bank"], "record": record["index"],
                           "raw": response["text"], "target_sha256": fit.native.text_hash(record["target"]),
                           **{key: response[key] for key in ("finish_reason", "prompt_tokens", "output_tokens")}}.items():
            fit.same(result[key], value, "scored response join: " + key)
        fit.same(result["score"], fit.sequence.core.score_memory_response(response["text"], record["target"]), "exact scorer join")
        fit.same(result["strict_stop"], response["finish_reason"] == "stop" and result["score"]["strict"], "strict stop join")
    panels = {f"W{view}": {} for view in (0, 8)}
    for view in (0, 8):
        for bank in ("A", "B"):
            rows = [row for row in scores["results"] if row["view"] == view and row["bank"] == bank]
            require(len(rows) == 4, "four-address bank denominator")
            panels[f"W{view}"][bank] = {"denominator": 4, "ids": [row["id"] for row in rows],
                "strict_stop": [row["strict_stop"] for row in rows], "correct": sum(row["strict_stop"] for row in rows)}
    fit.same([completed["panels"], scores["panels"]], [panels, panels], "readout panel joins")
    fit.same([completed["tokens"], completed["truncated"]], [tokens, truncated], "readout totals")
    times = {"model_load": load["ready_at"] - load["model_load_started"], "generation_calls": generation, "actor_operations": close["elapsed_actor_seconds"]}
    fit.same(custody["elapsed_seconds"], times, "readout custody timing")
    for key, value in {**times, "worker": completed["elapsed_seconds"]["worker"]}.items():
        fit.native.number(value)
        require(0 <= value <= elapsed and completed["elapsed_seconds"][key] == value, "readout elapsed bound")
    return completed


def controller(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_dir, *, outer_sha256, phase="A200", stage="fit", state=None):
    started, entered_wall = monotonic(), wall_time()
    require(phase in fit.sequence.PHASES and (stage == "fit" and state is None or stage == "readout" and state in fit.sequence.READ_STATES),
            "known v2 phase and explicit readout state required")
    selection = {"phase": phase} if stage == "fit" else {"stage": stage, "state": state}
    root = Path(outer_dir)
    require(root.is_absolute() and root.parent.is_dir() and root.parent.resolve() == root.parent, "fresh absolute outer parent")
    for protected in (Path(inputs_path).resolve().parent, Path(allocation_path).resolve(), Path(fit.__file__).resolve().parents[1], Path(__file__).resolve()):
        require(not root.is_relative_to(protected) and not protected.is_relative_to(root), "outer/input/source overlap")
    root.mkdir(exist_ok=False)
    directory, inputs_pin = root / stage, {"path": str(Path(inputs_path).absolute()), "sha256": inputs_sha256}
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
        write(root / "context.json", {"schema": SCHEMA, **selection, "entry_monotonic": started, "entry_wall": entered_wall,
              "inputs": inputs_pin, "allocation_file_sha256": allocation_sha256, "outer_source_sha256": outer_sha256,
              "helper_sha256": helper_hash, "cleanup_seconds": CLEANUP_SECONDS, "detach_seconds": DETACH_SECONDS})
        for name, path in (("inputs", inputs_path), ("allocation", allocation_path)):
            with (root / f"{name}.input.json").open("xb") as stream:
                stream.write(Path(path).read_bytes())
        sleep(DETACH_SECONDS)
        inputs, allocation, material = _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline, stage=stage, state=state, output=directory)
        require(lifecycle.file_hash(root / "inputs.input.json", deadline) == inputs_sha256
                and lifecycle.file_hash(root / "allocation.input.json", deadline) == allocation_sha256, "raw input snapshot drift")
        for protected in [Path(inputs["model_path"]).resolve(), *[Path(inputs[name]["path"]).resolve() for name in PIN_NAMES],
                          *[Path(inputs[name]["path"]).parent for name in ("predecessor", "fit_receipt") if inputs.get(name)],
                          *([Path(inputs["shutdown_binding"]["path"])] if stage == "readout" else [])]:
            require(not root.is_relative_to(protected) and not protected.is_relative_to(root), "outer/protected input overlap")
        require(entered_wall + TOTAL_SECONDS <= allocation["lease_end"] - max(LEASE_MARGIN, allocation["lease_margin_seconds"]), "lease finish margin")
        require(lifecycle.remaining(deadline) > CLEANUP_SECONDS, "insufficient cleanup margin")
        source = Path(fit.__file__).resolve().parents[1]
        argv = [allocation["python"], "-B", "-m", "gpu.astra_pcfl_event_sequence_v2_" + stage, "--inputs", inputs_pin["path"],
                "--inputs-sha256", inputs_sha256, "--output", str(directory), "--deadline", str(deadline - CLEANUP_SECONDS),
                "--phase" if stage == "fit" else "--state", phase if stage == "fit" else state]
        write(root / "binding.json", {"controller": lifecycle.identity(os.getpid()), "argv": argv, "source_root": str(source),
              "deadline_monotonic": deadline, "worker_deadline_monotonic": deadline - CLEANUP_SECONDS,
              "lease_finish_margin_seconds": max(LEASE_MARGIN, allocation["lease_margin_seconds"])})
        require(resources("pre"), "preflight failed")
        _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline, stage=stage, state=state, output=directory)
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
                snapshot = root / (stage + "_completed.json")
                with snapshot.open("xb") as stream:
                    stream.write((directory / "completed.json").read_bytes())
                require(lifecycle.file_hash(snapshot, deadline) == stage_files["completed.json"]["sha256"], "stage receipt snapshot drift")
                require(expected is not None, "stage worker identity unknown")
                if stage == "fit":
                    completed = validate_stage(directory, snapshot, inputs_pin, inputs, material, phase, stage_files, monotonic() - spawned)
                else:
                    completed = validate_readout(directory, snapshot, inputs_pin, inputs, material, state, stage_files, monotonic() - spawned, expected, deadline)
                _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline, stage=stage, state=state, output=directory)
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
            **selection, "inputs": inputs_pin, "allocation_file_sha256": allocation_sha256, "outer_source_sha256": outer_sha256,
            "errors": errors, "elapsed_seconds": monotonic() - started, "worker_identity": expected,
            "returncode": process.returncode if process is not None else None, "observations": observations,
            "gpu_released": bool(post_clear and released and released.get("owned_group_released") is True and released.get("identity") == expected),
            "stage_inventory": stage_files, "completed_sha256": completed["sha256"] if completed else None,
            "files": files, "retries": 0, "descendants_enabled": False, "acquisition_validation": "INCOMPLETE", "automatic_promotion": False, "full_contract_released": False,
            "original_status": "FORMATION_FAILED", "limits": fit.sequence.LIMITS})
        write(root / "collection.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inputs", "inputs-sha256", "allocation", "allocation-sha256", "outer-sha256", "outer"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--phase", choices=tuple(fit.sequence.PHASES), default="A200")
    parser.add_argument("--stage", choices=("fit", "readout"), default="fit")
    parser.add_argument("--state", choices=tuple(fit.sequence.READ_STATES))
    args = parser.parse_args(argv)
    result = controller(args.inputs, args.inputs_sha256, args.allocation, args.allocation_sha256, args.outer,
                        outer_sha256=args.outer_sha256, phase=args.phase, stage=args.stage, state=args.state)
    print(fit.prefix.canonical({"status": result["status"], "outer": args.outer,
          **({"phase": args.phase} if args.stage == "fit" else {"stage": args.stage, "state": args.state})}).decode())
    return int(result["status"] != "COMPLETED")


if __name__ == "__main__":
    raise SystemExit(main())
