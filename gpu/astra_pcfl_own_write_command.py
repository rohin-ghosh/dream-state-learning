"""Single-stage own-write glue. Main owns fresh processes and hard timeouts."""

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import time

from gpu import astra_pcfl_native_actor as native
from gpu import astra_pcfl_lf_actor as lf_api
from gpu import astra_pcfl_own_write_dev as formation_api
from gpu import astra_pcfl_own_write_readout as readout_api
from gpu import astra_pcfl_zero_fit_dev as token_api
from organism_v6 import pcfl_own_write_train as train_api
from organism_v6 import pcfl_vertical_dev as core


SCHEMA = "pcfl.own_write.command.v1"
STAGE_SECONDS = 1800
PREPARE_SECONDS = 180
SHUTDOWN_SHA256 = "7f5e1ac1a999faf36eab7d0c184bea7c93ae5e92234c39a148a809fd6e89840c"
OFFLINE = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "VLLM_NO_USAGE_STATS")
SPEC_FIELDS = {"schema", "model_path", "model_binding", "base_state_receipt", "shutdown_binding",
               "gpu_uuid", "environment", "expires_monotonic", "boot_id"}
canonical, digest, require = native.canonical, native.digest, native.require


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return formation_api._decode_json(Path(path).read_text())


def write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def boot_id():
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def environment():
    return {"native": native.environment_identity(), "peft_version": importlib.metadata.version("peft")}


def source_files():
    modules = (formation_api, readout_api, native, lf_api, token_api, train_api,
               train_api.writer, train_api.writer.shared, train_api.prepare, train_api.planner, core)
    paths = {str(Path(module.__file__).resolve()) for module in modules}
    paths.update((str(Path(__file__).resolve()), str(readout_api.SCOPE)))
    return {path: file_hash(path) for path in sorted(paths)}


def _offline():
    require(all(os.environ.get(name) == "1" for name in OFFLINE), "offline flags required")


def _tokenizer(model):
    _offline()
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False)


def _model(model):
    _offline()
    import torch
    from transformers import AutoModelForCausalLM
    return AutoModelForCausalLM.from_pretrained(model, local_files_only=True, trust_remote_code=False,
                                               torch_dtype=torch.bfloat16, device_map="cuda")


def _pin(record):
    require(type(record) is dict and set(record) == {"path", "sha256"}
            and Path(record["path"]).is_absolute(), "closed absolute input pin required")
    native.sha(record["sha256"])
    require(file_hash(record["path"]) == record["sha256"], "input file drift: " + record["path"])


def _spec(spec, now, environment_reader):
    require(type(spec) is dict and set(spec) == SPEC_FIELDS and spec["schema"] == SCHEMA + "/spec", "spec fields")
    require(Path(spec["model_path"]).is_absolute() and Path(spec["model_path"]).is_dir(), "local base required")
    require(type(spec["gpu_uuid"]) is str and spec["gpu_uuid"].startswith("GPU-"), "GPU UUID required")
    native.number(spec["expires_monotonic"], positive=True)
    require(now < spec["expires_monotonic"] and spec["boot_id"] == boot_id(), "expired or different-boot inputs")
    require(spec["environment"] == environment_reader(), "runtime environment drift")
    require(set(spec["environment"]) == {"native", "peft_version"}, "environment fields")
    for name in ("model_binding", "base_state_receipt", "shutdown_binding"):
        _pin(spec[name])
    require(spec["shutdown_binding"]["sha256"] == SHUTDOWN_SHA256, "Main-bound shutdown source required")


def choices():
    cell = core.WorldCell(core.build_root("disposable/0"), 0, 0, 0)
    ports = ("a0", "b", "c", "d", "f0", "u", "a1", "f1")
    actions = [f"EXPLORE {cell.root.lookup('node', source)} {cell.root.lookup('port', port)}"
               for source, port in zip(core.OLD_SOURCES, ports)]
    links = [[cell.root.lookup("event", f"e{index}") for index in pair]
             for pair in ((0, 1), (1, 2), (3, 4), (3, 7))]
    return cell, actions, links


def _actor_config(spec, sources, tokenizer, out, deadline):
    return {"schema": native.SCHEMA, "model_path": spec["model_path"], "model_binding": spec["model_binding"],
            "source_files": sources, "tokenizer_files": {name: file_hash(Path(spec["model_path"]) / name)
                                                          for name in sorted(native.TOKENIZER_FILES)},
            "chat_template_sha256": native.text_hash(tokenizer.chat_template),
            "tokenizer_probe": {"text": "READ EVENT", "token_ids": tokenizer.encode("READ EVENT", add_special_tokens=False)},
            "environment": spec["environment"]["native"], "gpu_uuid": spec["gpu_uuid"], "engine": native.ENGINE,
            "output_dir": str(out), "deadline": deadline, "device_seconds_cap": STAGE_SECONDS,
            "max_input_tokens": 14336, "max_output_tokens": 2048, "max_calls": 20}


def _limits(deadline):
    return {"output_tokens": 2048, "input_tokens": 14336, "returned_tokens": 0,
            "remaining_reads": 0, "deadline": deadline, "device_seconds": STAGE_SECONDS}


def _roster(plan):
    requests = sorted(slot["request"] for slot in plan["first_blocks"])
    require(len(requests) == len(set(requests)) == 17, "17 unique READ queries required")
    return [{"id": f"read/{query_index:02d}/W{view}", "request": request, "view": view,
             "seed": 0, "output_tokens": 2048}
            for query_index, request in enumerate(requests) for view in range(9)]


def _measure(plan, schedule, roster, tokenizer):
    """Structural token measurements only, never native data or fit items."""
    measurements, history, formation_lengths = [], [{"role": "system", "content": core.FORMATION_SYSTEM}], []
    expected = {handle: (core.EVENT_WIRE if "event" in fields else core.LINK_WIRE).format(**fields)
                for handle, fields in plan["expected_bank"].items()}
    def measure(text):
        ids = native.token_ids(tokenizer.encode(text, add_special_tokens=False))
        require(ids, "empty measured token sequence")
        measurements.append({"text": text, "token_ids": ids})
        return ids
    def history_turn(prompt, output):
        history.append({"role": "user", "content": prompt})
        rendered, ids = token_api._render(tokenizer, history)
        require(len(ids) <= 14336 and len(ids) + 2048 <= native.ENGINE["max_model_len"], "formation context cap")
        measure(rendered)
        require(len(measure(output)) <= 2048, "formation output cap")
        formation_lengths.append(len(ids))
        history.append({"role": "assistant", "content": output})
    for opportunity in plan["opportunities"]:
        history_turn(opportunity["explore_prompt"], opportunity["action"])
        history_turn(formation_api.commitment_prompt(
                         core.RECEIPT_WIRE.format(**opportunity["expected_receipt"]) + opportunity["event_prompt"]),
                     expected[opportunity["event_handle"]])
    for link in plan["links"]:
        history_turn(formation_api.commitment_prompt(core.LINK_TEMPLATE.format(FRESH_LINK_ID=link["link_handle"])),
                     expected[link["link_handle"]])
    prefixes = {}
    for row in roster:
        prompt, ids = token_api._render(tokenizer, readout_api.public_messages(row))
        require(len(ids) <= 14336 and len(ids) + 2048 <= native.ENGINE["max_model_len"], "READ context cap")
        measure(prompt)
        prefixes[(row["request"], row["view"])] = ids
    training_lengths = []
    require(type(tokenizer.eos_token_id) is int and tokenizer.eos_token_id >= 0, "EOS token required")
    for slot in schedule["corpus"]["slots"]:
        structural_text = "".join(expected[handle] for handle in slot["support"])
        target_ids = measure(structural_text)
        require(tokenizer.eos_token_id not in target_ids, "structural block contains EOS")
        for view in range(8):
            length = len(prefixes[(slot["request"], view)]) + len(target_ids) + 1
            require(length <= 512, "fixed salt0 training sequence exceeds 512; no redraw")
            training_lengths.append(length)
    identifiers = {identifier: len(measure(identifier)) for fields in plan["expected_bank"].values()
                   for identifier in fields.values()}
    return formation_api.seal({"schema": SCHEMA + "/measurements", "kind": "STRUCTURAL_ONLY_NOT_CHILD_DATA",
                               "full_L8_qualified": False, "salt": 0, "identifier_token_lengths": identifiers,
                               "formation_prompt_lengths": formation_lengths, "training_sequence_lengths": training_lengths,
                               "measurements": measurements, "read_calls_per_arm": len(roster)})


def prepare(spec_path, spec_sha256, out, *, tokenizer_factory=None, identity_reader=None,
            environment_reader=None, clock=time.monotonic):
    started = clock()
    _offline()
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "prepare requires empty CVD")
    require(file_hash(spec_path) == spec_sha256, "spec file hash differs")
    spec, root = read(spec_path), Path(out).absolute()
    require(not root.exists() and not root.is_symlink(), "fresh preparation root required")
    require(not root.is_relative_to(Path(spec["model_path"]).resolve()), "output inside model")
    root.mkdir(parents=False, exist_ok=False)
    with (root / "spec.json").open("xb") as stream:
        stream.write(Path(spec_path).read_bytes())
    try:
        require(file_hash(root / "spec.json") == spec_sha256 and read(root / "spec.json") == spec,
                "spec changed during preparation")
        _spec(spec, started, environment_reader or environment)
        sources = source_files()
        tokenizer = (tokenizer_factory or _tokenizer)(spec["model_path"])
        actor = _actor_config(spec, sources, tokenizer, root / "formation" / "actor", spec["expires_monotonic"])
        checker = native.NativeActor(actor)
        identity = (identity_reader or checker._verify_identity)(min(spec["expires_monotonic"], started + PREPARE_SECONDS))
        cpu = read(spec["base_state_receipt"]["path"])
        require(set(cpu) == {"schema", "status", "base_state_sha256", "model_binding_sha256", "model_files", "dtype", "device", "environment"}, "CPU base receipt fields")
        require(cpu["schema"] == "pcfl.own_write.cpu_base_state.v1" and cpu["status"] == "COMPLETE"
                and cpu["dtype"] == "bfloat16" and cpu["device"] == "cpu"
                and cpu["model_binding_sha256"] == spec["model_binding"]["sha256"]
                and cpu["model_files"] == identity["model_files"] and cpu["environment"] == spec["environment"], "CPU base identity differs")
        native.sha(cpu["base_state_sha256"])
        cell, actions, links = choices()
        config = formation_api.build_config(cell, actions, links, actor_config=actor, seed=0, limits=_limits(actor["deadline"]))
        plan = config["planner"]
        schedule = train_api.build_schedule(plan, plan["plan_sha256"], batch_seed=0)
        roster = _roster(plan)
        measured = _measure(plan, schedule, roster, tokenizer)
        write(root / "measurements.json", measured)
        token_receipt = {"kind": "offline_measurement", "revision": native.REVISION,
                         "files": actor["tokenizer_files"], "chat_template_sha256": actor["chat_template_sha256"],
                         "measurements": measured["measurements"]}
        binding = {"authority_sha256": file_hash(readout_api.SCOPE), "init_seed": 0, "dropout_seed": 0,
                   "base_state_sha256": cpu["base_state_sha256"], "sources": train_api.source_snapshot(),
                   "environment": {"base": train_api.prepare.RECIPE["base"], "model_revision": native.REVISION,
                                   "tokenizer_revision": native.REVISION, "model_files": identity["model_files"],
                                   "chat_template_sha256": actor["chat_template_sha256"], "runtime": spec["environment"]},
                   "tokenizer_receipt": token_receipt}
        require(source_files() == sources and clock() <= min(spec["expires_monotonic"], started + PREPARE_SECONDS), "prepare source/time drift")
        manifest = formation_api.seal({"schema": SCHEMA + "/manifest", "root": str(root), "spec": spec,
            "sources": sources, "formation_template": config, "schedule": schedule, "roster": roster,
            "roster_sha256": digest(roster), "binding": binding,
            "spec_input": {"path": str(Path(spec_path).absolute()), "sha256": spec_sha256},
            "input_files": {"spec.json": file_hash(root / "spec.json"), "measurements.json": file_hash(root / "measurements.json")},
            "stage_seconds": STAGE_SECONDS, "prepared_started": started, "prepared_ended": clock(),
            "kind": "INJECTED_CPU_TEST" if any(item is not None for item in (tokenizer_factory, identity_reader, environment_reader)) else "OFFLINE_PREPARATION",
            "full_assay_qualified": False, "full_L8_qualified": False})
        write(root / "manifest.json", manifest)
        return manifest
    except Exception as error:
        write(root / "prepare_failure.json", {"type": type(error).__name__, "message": str(error)})
        raise


def _begin(path, expected, stage, injected, environment_reader, clock):
    started = clock()
    require(file_hash(path) == expected, "manifest file hash differs")
    manifest = read(path)
    require(manifest["schema"] == SCHEMA + "/manifest" and manifest["sha256"] == digest({key: value for key, value in manifest.items() if key != "sha256"}), "manifest seal differs")
    root = Path(manifest["root"])
    require(Path(path).absolute() == root / "manifest.json", "manifest root differs")
    directory = root / stage
    directory.mkdir(parents=False, exist_ok=False)
    write(directory / "entry.json", {"manifest_file_sha256": expected, "stage": stage, "started": started,
                                    "kind": "INJECTED_CPU_TEST" if injected else "NATIVE"})
    try:
        _offline()
        require(injected or manifest["kind"] == "OFFLINE_PREPARATION", "test preparation cannot launch native work")
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == ("" if injected else manifest["spec"]["gpu_uuid"]), "stage CVD differs")
        _spec(manifest["spec"], started, environment_reader or environment)
        require(source_files() == manifest["sources"] and manifest["stage_seconds"] == STAGE_SECONDS, "source/cap drift")
        for name, checksum in manifest["input_files"].items():
            require(name in ("spec.json", "measurements.json") and file_hash(root / name) == checksum, "prepared input drift")
        require(file_hash(root / "spec.json") == manifest["spec_input"]["sha256"]
                and read(root / "spec.json") == manifest["spec"], "original spec binding differs")
        template = manifest["formation_template"]
        formation_api.validate_config(template, template["sha256"])
        fixed_cell, actions, links = choices()
        require(core.to_data(fixed_cell) == template["planner"]["cell"]
                and (actions, links) == (template["planner"]["actions"], template["planner"]["link_choices"]), "fixed choices differ")
        train_api.validate_schedule(template["planner"], template["planner"]["plan_sha256"], manifest["schedule"], manifest["schedule"]["sha256"])
        require(_roster(template["planner"]) == manifest["roster"] and digest(manifest["roster"]) == manifest["roster_sha256"], "READ roster differs")
        return manifest, directory, started, min(manifest["spec"]["expires_monotonic"], started + STAGE_SECONDS)
    except Exception as error:
        _failure(directory, error)
        raise


def _failure(directory, error):
    if not (directory / "failure.json").exists():
        write(directory / "failure.json", {"type": type(error).__name__, "message": str(error)})


def _inventory(directory):
    return {str(path.relative_to(directory)): file_hash(path) for path in sorted(directory.rglob("*")) if path.is_file()}


def _finish(manifest, directory, started, deadline, clock, **details):
    ended = clock()
    require(ended <= deadline and source_files() == manifest["sources"], "stage time/source drift")
    receipt = formation_api.seal({"schema": SCHEMA + "/completed", "status": "COMPLETE",
        "manifest_sha256": manifest["sha256"], "stage": directory.name, "started": started, "ended": ended,
        "elapsed_seconds": ended - started, "outer_release_required": True, "gpu_released": False,
        "files": _inventory(directory), **details})
    write(directory / "completed.json", receipt)
    return receipt


def _completed(manifest, stage):
    directory = Path(manifest["root"]) / stage
    require(not (directory / "failure.json").exists(), "failed upstream stage")
    receipt = read(directory / "completed.json")
    require(receipt["status"] == "COMPLETE" and receipt["manifest_sha256"] == manifest["sha256"]
            and receipt["stage"] == stage and receipt["sha256"] == digest({key: value for key, value in receipt.items() if key != "sha256"}), "upstream completion differs")
    actual = _inventory(directory)
    actual.pop("completed.json")
    require(actual == receipt["files"], "upstream files changed")
    return receipt


def _shutdown(actor, binding):
    session = getattr(actor, "_session", None)
    require(session is not None, "no loaded formation engine to shut down")
    method = session.llm.llm_engine.engine_core.shutdown
    require(callable(method), "EngineCore shutdown unavailable")
    inspect.signature(method).bind()
    path = str(Path(inspect.getsourcefile(method)).resolve())
    require(path == binding["path"] and file_hash(path) == binding["sha256"], "installed shutdown method source differs")
    method()
    return {"method": "llm.llm_engine.engine_core.shutdown", "source": binding, "shutdown_returned": True}


def formation(path, expected, *, actor_factory=None, environment_reader=None, clock=time.monotonic):
    manifest, directory, started, deadline = _begin(path, expected, "formation", actor_factory is not None, environment_reader, clock)
    actor = None
    try:
        settings = {**manifest["formation_template"]["actor_config"], "deadline": deadline}
        config = formation_api.build_config(*choices(), actor_config=settings, seed=0, limits=_limits(deadline))
        write(directory / "formation_config.json", config)
        actor = (actor_factory or lf_api.LFNativeActor)(settings)
        try:
            report = formation_api.run_formation(config, config["sha256"], actor, directory / "records")
        finally:
            try:
                if getattr(actor, "_session", None) is not None:
                    write(directory / "shutdown.json", _shutdown(actor, manifest["spec"]["shutdown_binding"]))
            finally:
                write(directory / "actor_close.json", actor.close())
        close = read(directory / "actor_close.json")
        require(report["status"] == "COMPLETE" and close["error_type"] is None
                and close["failed"] is False and close["budget_exceeded"] is False, "formation/close failed")
        require((directory / "shutdown.json").is_file(), "explicit shutdown receipt missing")
        formation_api.replay_validate(config, config["sha256"], report)
        service = [core.read_query(report["writer_payload"]["queries"], request)
                   for request in sorted(report["writer_payload"]["queries"])]
        write(directory / "exact_child_service.json", {"kind": "DETERMINISTIC_SERVICE_NOT_MODEL", "calls": 0, "items": service})
        return _finish(manifest, directory, started, deadline, clock, calls=20, fits=0, updates=0, report_sha256=report["sha256"])
    except Exception as error:
        _failure(directory, error)
        raise


def _formation_inputs(manifest):
    _completed(manifest, "formation")
    directory = Path(manifest["root"]) / "formation"
    config = read(directory / "formation_config.json")
    report = read(directory / "records" / "formation.json")
    formation_api.replay_validate(config, config["sha256"], report)
    require(report["status"] == "COMPLETE", "complete formation required")
    receipts = {name: read(directory / "actor" / (name + ".json")) for name in ("config", "identity", "load", "close")}
    return config, report, receipts


def fit(path, expected, *, tokenizer_factory=None, base_factory=None, trainer=None,
        environment_reader=None, clock=time.monotonic):
    injected = any(item is not None for item in (tokenizer_factory, base_factory, trainer))
    manifest, directory, started, deadline = _begin(path, expected, "fit", injected, environment_reader, clock)
    try:
        config, report, receipts = _formation_inputs(manifest)
        schedule = manifest["schedule"]
        fitted = train_api.build_fit(config, config["sha256"], report, report["sha256"], schedule,
                                    schedule["sha256"], manifest["binding"], receipts)
        tokenizer = (tokenizer_factory or _tokenizer)(manifest["spec"]["model_path"])
        def factory():
            require(clock() < deadline, "fit deadline exhausted")
            return (_model(manifest["spec"]["model_path"]), manifest["binding"]["environment"])
        receipt = (trainer or train_api.train_fit)(fitted, tokenizer, base_factory or factory, directory / "write")
        require(receipt["status"] == "COMPLETE" and type(receipt["updates"]) is int and receipt["updates"] == 200,
                "writer completion/update count differs")
        adapter = directory / "write" / "adapter"
        files = {name: {"sha256": checksum, "size": (adapter / name).stat().st_size}
                 for name, checksum in _inventory(adapter).items()}
        route = {"name": "pcfl-own-write", "id": 1, "path": str(adapter), "files": files}
        readout_api.ReadoutActor(_readout_config(manifest, "AUTH_WRITE", route, directory / "unused_actor", deadline))
        write(directory / "adapter.json", route)
        return _finish(manifest, directory, started, deadline, clock, calls=0, fits=1, updates=200,
                       writer_receipt_sha256=digest(receipt))
    except Exception as error:
        _failure(directory, error)
        raise


def _readout_config(manifest, arm, adapter, out, deadline):
    return {**manifest["formation_template"]["actor_config"], "schema": readout_api.SCHEMA,
            "engine": readout_api.ENGINE, "output_dir": str(out), "deadline": deadline,
            "max_calls": 153, "arm": arm, "adapter": adapter, "roster": manifest["roster"],
            "roster_sha256": manifest["roster_sha256"], "shutdown_binding": manifest["spec"]["shutdown_binding"]}


def readout(path, expected, arm, *, actor_factory=None, environment_reader=None, clock=time.monotonic):
    require(arm in readout_api.ARMS, "unknown READ arm")
    manifest, directory, started, deadline = _begin(path, expected, "readout_" + arm, actor_factory is not None, environment_reader, clock)
    try:
        _, report, _ = _formation_inputs(manifest)
        adapter = None
        if arm == "AUTH_WRITE":
            _completed(manifest, "fit")
            adapter = read(Path(manifest["root"]) / "fit" / "adapter.json")
        settings = _readout_config(manifest, arm, adapter, directory / "actor", deadline)
        write(directory / "readout_config.json", settings)
        actor = (actor_factory or readout_api.ReadoutActor)(settings)
        results = []
        try:
            for row in manifest["roster"]:
                response = actor.generate({"id": row["id"]}, {"deadline": deadline, "device_seconds": STAGE_SECONDS})
                write(directory / (row["id"].replace("/", "_") + ".json"), response)
                target = report["writer_payload"]["queries"][row["request"]]["target"]
                scored = core.score_memory_response(response["text"], target)
                results.append({"id": row["id"], "request": row["request"], "view": row["view"], "raw": response["text"],
                                "finish_reason": response["finish_reason"], "score": scored,
                                "strict_stop": response["finish_reason"] == "stop" and scored["strict"],
                                "semantic_stop": response["finish_reason"] == "stop" and scored["semantic"]})
        finally:
            write(directory / "actor_close.json", actor.close())
        close = read(directory / "actor_close.json")
        require(close["error_type"] is None and close["failed"] is False and close["budget_exceeded"] is False
                and close["shutdown"]["shutdown_returned"] is True and type(close["calls_consumed"]) is int
                and close["calls_consumed"] == 153, "readout/explicit close failed")
        write(directory / "scores.json", {"arm": arm, "roster_sha256": manifest["roster_sha256"],
                                         "denominator": 153, "results": results})
        return _finish(manifest, directory, started, deadline, clock, calls=153, fits=0, updates=0)
    except Exception as error:
        _failure(directory, error)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="stage", required=True)
    preparer = commands.add_parser("prepare")
    for name in ("spec", "spec-sha256", "out"):
        preparer.add_argument("--" + name, required=True)
    for stage in ("formation", "fit", "readout"):
        command = commands.add_parser(stage)
        command.add_argument("--manifest", required=True)
        command.add_argument("--manifest-sha256", required=True)
        if stage == "readout":
            command.add_argument("--arm", choices=readout_api.ARMS, required=True)
    args = parser.parse_args(argv)
    if args.stage == "prepare":
        result = prepare(args.spec, args.spec_sha256, args.out)
    elif args.stage == "formation":
        result = formation(args.manifest, args.manifest_sha256)
    elif args.stage == "fit":
        result = fit(args.manifest, args.manifest_sha256)
    else:
        result = readout(args.manifest, args.manifest_sha256, args.arm)
    if args.stage == "prepare":
        path = Path(args.out).absolute() / "manifest.json"
        summary = {"manifest": str(path), "manifest_sha256": file_hash(path)}
    else:
        stage = args.stage if args.stage != "readout" else "readout_" + args.arm
        path = Path(args.manifest).absolute().parent / stage / "completed.json"
        summary = {"completion": str(path), "completion_sha256": file_hash(path)}
    print(canonical({"stage": args.stage, "seal_sha256": result["sha256"], **summary}).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
