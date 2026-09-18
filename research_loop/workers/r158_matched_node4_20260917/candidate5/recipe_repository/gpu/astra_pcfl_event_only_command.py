"""Fixed failed-formation EVENT prefix: offline prepare, fresh LOW200, cold READs."""

import argparse
import copy
import os
from pathlib import Path
import time

from gpu import astra_pcfl_event_prefix_import as prefix
from gpu import astra_pcfl_own_write_command as own
from gpu import astra_pcfl_zero_fit_outer as lifecycle
from organism_v6 import pcfl_event_only_train as event

SCHEMA = "pcfl.event_only.command.v1"
TOTAL_SECONDS, CLEANUP_SECONDS, PREPARE_SECONDS = 1800, 60, 180
SCOPE = Path(__file__).resolve().parents[1] / "research_notes/astra_memos/ASTRA_PCFL_EVENT_ONLY_SCOPE_2026-09-13.md"
SPEC_FIELDS = own.SPEC_FIELDS | {"archive", "replay_receipt", "authority", "source_files"}
native, readout_api, core = own.native, own.readout_api, event.core
require, read, write, file_hash = native.require, own.read, own.write, lifecycle.file_hash
canonical, digest, OFFLINE = native.canonical, native.digest, own.OFFLINE


def source_files():
    modules = (prefix, event, lifecycle, lifecycle.driver, lifecycle.driver.runtime)
    paths = [Path(module.__file__).resolve() for module in modules]
    paths += [Path(__file__).resolve(), Path(__file__).with_name("astra_pcfl_event_only_outer.py").resolve(), SCOPE]
    return {**own.source_files(), **{str(path): file_hash(path) for path in paths}}


def _spec(spec, now, environment_reader):
    require(type(spec) is dict and set(spec) == SPEC_FIELDS and spec["schema"] == SCHEMA + "/spec", "EVENT-only spec fields")
    own._spec({**{key: spec[key] for key in own.SPEC_FIELDS}, "schema": own.SCHEMA + "/spec"}, now, environment_reader)
    for key in ("archive", "replay_receipt", "authority"):
        own._pin(spec[key])
    require(spec["archive"]["sha256"] == prefix.ARCHIVE_SHA256, "only fixed original archive")
    require(Path(spec["authority"]["path"]).resolve() == SCOPE and spec["authority"]["sha256"] == file_hash(SCOPE), "EVENT-only authority binding")
    require(spec["source_files"] == source_files(), "execution source drift")


def _settings(spec, tokenizer, roster, out, deadline):
    sources = dict(spec["source_files"])
    for key in ("archive", "replay_receipt", "base_state_receipt", "authority", "shutdown_binding"):
        sources[spec[key]["path"]] = spec[key]["sha256"]
    base = own._actor_config(spec, sources, tokenizer, out, deadline)
    return {**base, "max_calls": 28, "device_seconds_cap": TOTAL_SECONDS - CLEANUP_SECONDS}


def _readout_config(manifest, arm, adapter, out, deadline):
    return {**manifest["actor_template"], "schema": readout_api.SCHEMA, "engine": readout_api.ENGINE,
            "output_dir": str(out), "deadline": deadline, "arm": arm, "adapter": adapter,
            "roster": manifest["roster"], "roster_sha256": manifest["roster_sha256"],
            "shutdown_binding": manifest["spec"]["shutdown_binding"]}


def prepare(spec_path, spec_sha256, output, *, tokenizer_factory=None, identity_reader=None,
            environment_reader=None, clock=time.monotonic):
    started = clock()
    own._pin({"path": str(spec_path), "sha256": spec_sha256})
    spec, root = read(spec_path), Path(output)
    require(root.is_absolute() and root.parent.is_dir() and root.parent.resolve() == root.parent, "fresh absolute output parent")
    protected = [Path(__file__).resolve().parents[1], Path(spec_path), Path(spec["model_path"])]
    protected += [Path(spec[key]["path"]) for key in ("archive", "replay_receipt", "authority", "base_state_receipt", "model_binding", "shutdown_binding")]
    require(all(not root.is_relative_to(path.resolve()) and not path.resolve().is_relative_to(root) for path in protected), "output/input/source overlap")
    root.mkdir(exist_ok=False)
    try:
        own._offline()
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "prepare requires empty CVD")
        _spec(spec, started, environment_reader or own.environment)
        deadline = min(started + PREPARE_SECONDS, spec["expires_monotonic"])
        with (root / "spec.json").open("xb") as stream:
            stream.write(Path(spec_path).read_bytes())
        evidence = prefix.load_evidence(spec["archive"]["path"])
        replay = read(spec["replay_receipt"]["path"])
        imported = prefix.build_import(evidence, replay, replay["sha256"])
        write(root / "import.json", imported)
        original = prefix._json(evidence["files"]["manifest.json"])["binding"]
        binding = {key: copy.deepcopy(original[key]) for key in event.BINDING_FIELDS - {"authority_sha256", "sources"}}
        binding.update(authority_sha256=spec["authority"]["sha256"], sources=event.source_snapshot())
        require(binding["environment"]["runtime"] == spec["environment"], "original runtime environment binding")
        schedule = event.build_schedule(imported, imported["sha256"])
        fitted = event.build_fit(imported, imported["sha256"], schedule, schedule["sha256"], binding)
        write(root / "fit.json", fitted)
        tokenizer = (tokenizer_factory or own._tokenizer)(spec["model_path"])
        token_receipt = prefix.verify_tokenizer(imported, tokenizer)
        prefix.unseal(token_receipt, token_receipt["sha256"])
        require(token_receipt["status"] == "EVENT_PREFIX_TOKENIZER_VERIFIED" and token_receipt["import_sha256"] == imported["sha256"], "positive prefix tokenizer receipt")
        write(root / "tokenizer.json", token_receipt)
        encoding = event.encode_fit(fitted, tokenizer)
        require(len(encoding["items"]) == 160, "160 training encodings required")
        write(root / "encoding.json", encoding)
        roster = event.read_roster(imported)
        settings = _settings(spec, tokenizer, roster, root / "readout_NO_WRITE_C0" / "actor", deadline)
        checker = native.NativeActor(settings, environment_reader=lambda: spec["environment"]["native"], clock=clock)
        identity = (identity_reader or checker._verify_identity)(deadline)
        cpu = read(spec["base_state_receipt"]["path"])
        require(cpu["status"] == "COMPLETE" and cpu["device"] == "cpu" and cpu["dtype"] == "bfloat16"
                and cpu["base_state_sha256"] == binding["base_state_sha256"] and cpu["environment"] == spec["environment"]
                and cpu["model_binding_sha256"] == spec["model_binding"]["sha256"]
                and cpu["model_files"] == identity["model_files"] == binding["environment"]["model_files"], "original base/model identity binding")
        write(root / "identity.json", identity)
        measurements = []
        for row in roster:
            text = tokenizer.apply_chat_template(readout_api.public_messages(row), tokenize=False, add_generation_prompt=True)
            ids = native.token_ids(tokenizer.encode(text, add_special_tokens=False))
            require(ids and len(ids) <= settings["max_input_tokens"] and len(ids) + row["output_tokens"] <= native.ENGINE["max_model_len"], "readout initial context cap")
            measurements.append({"id": row["id"], "prompt_sha256": native.text_hash(text), "input_tokens": len(ids)})
        write(root / "read_measurements.json", measurements)
        services = [{"request": request, "response": core.read_query(imported["queries"], request)} for request in sorted(imported["queries"])]
        require(len(services) == 14 and all(core.score_memory_response(row["response"]["raw"], imported["queries"][row["request"]]["target"])["strict"] for row in services), "exact child service14/14")
        write(root / "service.json", {"kind": "DETERMINISTIC_SERVICE_NOT_MODEL", "calls": 0, "denominator": 14, "exact": 14, "results": services})
        _spec(spec, clock(), environment_reader or own.environment)
        require(file_hash(root / "spec.json") == spec_sha256 and clock() <= deadline, "preparation time/input drift")
        manifest = prefix.seal({"schema": SCHEMA + "/manifest", "root": str(root), "spec": spec, "sources": spec["source_files"],
            "spec_file_sha256": spec_sha256, "import_sha256": imported["sha256"], "fit_sha256": fitted["sha256"],
            "encoding_sha256": encoding["sha256"], "tokenizer_sha256": token_receipt["sha256"],
            "roster": roster, "roster_sha256": digest(roster), "actor_template": settings,
            "input_files": {path.name: file_hash(path) for path in root.iterdir()}, "total_seconds": TOTAL_SECONDS,
            "cleanup_seconds": CLEANUP_SECONDS, "endpoint": event.ENDPOINT, "full_contract_released": False,
            "original_status": "FORMATION_FAILED", "original_returncode": 1,
            "kind": "INJECTED_CPU_TEST" if any(value is not None for value in (tokenizer_factory, identity_reader, environment_reader)) else "OFFLINE_PREPARATION"})
        write(root / "manifest.json", manifest)
        return manifest
    except BaseException as error:
        write(root / "prepare_failure.json", {"type": type(error).__name__, "message": str(error)})
        raise


def validate_manifest(path, expected, *, environment_reader=None, clock=time.monotonic):
    own._pin({"path": str(path), "sha256": expected})
    manifest = read(path)
    prefix.unseal(manifest, manifest["sha256"])
    require(manifest["schema"] == SCHEMA + "/manifest" and Path(path) == Path(manifest["root"]) / "manifest.json", "manifest path/schema")
    require(manifest["total_seconds"] == TOTAL_SECONDS and manifest["cleanup_seconds"] == CLEANUP_SECONDS
            and manifest["full_contract_released"] is False and manifest["original_status"] == "FORMATION_FAILED"
            and manifest["original_returncode"] == 1 and manifest["endpoint"] == event.ENDPOINT, "prefix scope/budget")
    _spec(manifest["spec"], clock(), environment_reader or own.environment)
    require(manifest["sources"] == manifest["spec"]["source_files"], "manifest source binding")
    root = Path(manifest["root"])
    require(root.resolve() == root and set(manifest["input_files"]) == {"spec.json", "import.json", "fit.json", "tokenizer.json", "encoding.json", "identity.json", "read_measurements.json", "service.json"}, "prepared inventory/path")
    for name, checksum in manifest["input_files"].items():
        require(file_hash(root / name) == checksum, "prepared file drift: " + name)
    require(read(root / "spec.json") == manifest["spec"] and file_hash(root / "spec.json") == manifest["spec_file_sha256"], "original spec binding")
    fitted = read(root / "fit.json")
    event.validate_fit(fitted)
    require(fitted["binding"]["authority_sha256"] == manifest["spec"]["authority"]["sha256"] == file_hash(SCOPE), "scope FILE/fit authority join")
    token_receipt = read(root / "tokenizer.json")
    prefix.unseal(token_receipt, manifest["tokenizer_sha256"])
    require(token_receipt["status"] == "EVENT_PREFIX_TOKENIZER_VERIFIED" and token_receipt["import_sha256"] == manifest["import_sha256"]
            and token_receipt["calls_checked"] == 16 and token_receipt["model_calls"] == 0, "positive tokenizer/import join")
    require(fitted["sha256"] == manifest["fit_sha256"] and fitted["import_sha256"] == manifest["import_sha256"]
            and fitted["imported"] == read(root / "import.json") and fitted["read_roster"] == manifest["roster"]
            and digest(manifest["roster"]) == manifest["roster_sha256"], "fit/import/roster binding")
    settings, spec = manifest["actor_template"], manifest["spec"]
    sources = dict(spec["source_files"])
    for key in ("archive", "replay_receipt", "base_state_receipt", "authority", "shutdown_binding"):
        sources[spec[key]["path"]] = spec[key]["sha256"]
    require(settings["model_path"] == spec["model_path"] and settings["model_binding"] == spec["model_binding"]
            and settings["environment"] == spec["environment"]["native"] and settings["gpu_uuid"] == spec["gpu_uuid"]
            and settings["source_files"] == sources and settings["max_calls"] == 28, "actor/prefix/spec binding")
    return manifest


def _completed(manifest, name):
    root = Path(manifest["root"]) / name
    receipt = read(root / "completed.json")
    prefix.unseal(receipt, receipt["sha256"])
    require(not (root / "failure.json").exists() and receipt["schema"] == SCHEMA + "/completed"
            and receipt["status"] == "COMPLETE" and receipt["manifest_sha256"] == manifest["sha256"]
            and receipt["stage"] == name, "upstream completion binding")
    require(receipt["files"] == {key: value for key, value in own._inventory(root).items() if key != "completed.json"}, "upstream file drift")
    return receipt


def _read_custody(directory, settings, responses, injected):
    root = directory / "actor"
    identity, load, close = (read(root / name) for name in ("identity.json", "load.json", "close.json"))
    kind = identity["kind"]
    require(kind == "INJECTED_CPU_TEST" if injected else kind == "NATIVE_OWN_WRITE_READOUT", "native readout kind")
    route = readout_api.route_identity(settings)
    require(identity["pid"] == os.getpid() and identity["config_sha256"] == digest(settings)
            and read(root / "config.json") == settings and identity["identity"]["route"] == route, "readout config/PID/route join")
    require(close == read(directory / "actor_close.json") and close["kind"] == load["kind"] == kind
            and close["calls_consumed"] == close["planned_calls"] == len(responses) == 28
            and close["route"] == load["route"] == route and close["error_type"] is None
            and close["failed"] is False and close["budget_exceeded"] is False
            and close["shutdown"]["shutdown_returned"] is True
            and close["shutdown"]["source"] == settings["shutdown_binding"], "readout close/load/call join")
    for index, (row, response) in enumerate(zip(settings["roster"], responses)):
        base = f"call_{index:04d}"
        raw, returned, requested = (read(root / (base + suffix)) for suffix in (".raw.json", ".response.json", ".request.json"))
        rendered = read(root / (base + ".render.json"))
        require(raw["kind"] == kind and raw["route"] == raw["raw"]["route"] == response["route"] == route
                and returned["response"] == response and response["id"] == row["id"] and requested["row"] == row
                and requested["messages"] == readout_api.public_messages(row), "original readout capture join")
        require(raw["raw"]["text"] == response["text"] and raw["raw"]["finish_reason"] == response["finish_reason"]
                and returned["raw_hex"] == response["text"].encode().hex()
                and returned["raw_utf8_sha256"] == native.text_hash(response["text"]), "raw scored bytes/finish join")
        require(rendered["sampling"] == {**native.SAMPLING, "seed": row["seed"], "max_tokens": row["output_tokens"]}
                and rendered["route"] == route and load["ready_at"] <= raw["generation_started"] <= raw["generation_ended"] <= settings["deadline"], "unconstrained sampling/cold chronology")
    return {"kind": kind, "calls": 28, "route": route, "identity_sha256": digest(identity), "outer_release_required": True}


def stage(path, expected, deadline, *, stage, arm=None, tokenizer_factory=None, base_factory=None,
          trainer=None, actor_factory=None, environment_reader=None, clock=time.monotonic):
    require(stage in ("fit", "readout") and (arm in readout_api.ARMS if stage == "readout" else arm is None), "stage/arm")
    started = clock()
    manifest = validate_manifest(path, expected, environment_reader=environment_reader, clock=clock)
    name = stage if stage == "fit" else "readout_" + arm
    directory = Path(manifest["root"]) / name
    directory.mkdir(exist_ok=False)
    injected = any(value is not None for value in (tokenizer_factory, base_factory, trainer, actor_factory, environment_reader))
    write(directory / "entry.json", {"manifest_file_sha256": expected, "stage": name, "started": started, "kind": "INJECTED_CPU_TEST" if injected else "NATIVE"})
    try:
        own._offline()
        native.number(deadline, positive=True)
        require(started < deadline <= min(manifest["spec"]["expires_monotonic"], started + TOTAL_SECONDS - CLEANUP_SECONDS), "bounded worker deadline")
        require(injected or manifest["kind"] == "OFFLINE_PREPARATION", "injected preparation cannot run native")
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == ("" if injected else manifest["spec"]["gpu_uuid"]), "stage CVD binding")
        fitted = read(Path(manifest["root"]) / "fit.json")
        details = {"calls": 0, "fits": 0, "updates": 0}
        if stage == "fit":
            tokenizer = (tokenizer_factory or own._tokenizer)(manifest["spec"]["model_path"])
            encoding = event.encode_fit(fitted, tokenizer)
            require(encoding == read(Path(manifest["root"]) / "encoding.json"), "prepared160 encoding drift")
            def factory():
                require(clock() < deadline, "fit deadline before base load")
                return own._model(manifest["spec"]["model_path"]), fitted["binding"]["environment"]
            receipt = (trainer or event.train_fit)(fitted, tokenizer, base_factory or factory, directory / "write")
            require(receipt["status"] == "COMPLETE" and type(receipt["updates"]) is int and receipt["updates"] == 200
                    and receipt["presentations"] == receipt["training_forwards"] == 800
                    and receipt["fit_sha256"] == fitted["sha256"] and receipt["encoding_sha256"] == manifest["encoding_sha256"], "LOW200 writer receipt")
            saved = directory / "write"
            require(read(saved / "completed.json") == receipt and not (saved / "failed.json").exists()
                    and receipt["files"] == {key: value for key, value in own._inventory(saved).items() if key != "completed.json"}, "writer file custody")
            adapter = saved / "adapter"
            route = {"name": "pcfl-own-write", "id": 1, "path": str(adapter), "files": {
                key: {"size": (adapter / key).stat().st_size, "sha256": value} for key, value in own._inventory(adapter).items()}}
            readout_api.ReadoutActor(_readout_config(manifest, "AUTH_WRITE", route, directory / "unused_actor", deadline))
            write(directory / "adapter.json", route)
            details.update(fits=1, updates=200, writer_receipt_sha256=digest(receipt))
        else:
            adapter = None
            if arm == "AUTH_WRITE":
                upstream = _completed(manifest, "fit")
                require(injected or upstream["kind"] == "NATIVE", "injected fit cannot mount natively")
                adapter = read(Path(manifest["root"]) / "fit/adapter.json")
            settings = _readout_config(manifest, arm, adapter, directory / "actor", deadline)
            write(directory / "readout_config.json", settings)
            actor = (actor_factory or readout_api.ReadoutActor)(settings)
            responses, results = [], []
            try:
                for row in manifest["roster"]:
                    response = actor.generate({"id": row["id"]}, {"deadline": deadline, "device_seconds": TOTAL_SECONDS - CLEANUP_SECONDS})
                    responses.append(response)
                    write(directory / (row["id"].replace("/", "_") + ".json"), response)
                    score = core.score_memory_response(response["text"], fitted["imported"]["queries"][row["request"]]["target"])
                    results.append({"id": row["id"], "request": row["request"], "view": row["view"], "raw": response["text"],
                        "finish_reason": response["finish_reason"], "score": score,
                        "strict_stop": response["finish_reason"] == "stop" and score["strict"],
                        "semantic_stop": response["finish_reason"] == "stop" and score["semantic"]})
            finally:
                write(directory / "actor_close.json", actor.close())
            write(directory / "custody.json", _read_custody(directory, settings, responses, injected))
            counts = {str(view): {"denominator": 14, "strict_stop": sum(row["strict_stop"] for row in results if row["view"] == view),
                      "semantic_stop": sum(row["semantic_stop"] for row in results if row["view"] == view)} for view in (0, 8)}
            write(directory / "scores.json", {"arm": arm, "denominator": 28, "results": results, "by_view": counts,
                "endpoint": event.ENDPOINT, "paired_endpoint": "REQUIRES_BOTH_RELEASED_ARMS_NOT_INFERRED_HERE"})
            details.update(calls=28, arm=arm, by_view=counts)
        validate_manifest(path, expected, environment_reader=environment_reader, clock=clock)
        files = lifecycle._inventory(directory, deadline)
        ended = clock()
        require(ended <= deadline, "stage deadline")
        completed = prefix.seal({"schema": SCHEMA + "/completed", "status": "COMPLETE", "stage": name,
            "manifest_sha256": manifest["sha256"], "started": started, "ended": ended, "elapsed_seconds": ended - started,
            "kind": "INJECTED_CPU_TEST" if injected else "NATIVE", "outer_release_required": True, "gpu_released": False,
            "full_contract_released": False, "original_status": "FORMATION_FAILED", "original_returncode": 1,
            "files": {key: value["sha256"] for key, value in files.items()}, **details})
        write(directory / "completed.json", completed)
        return completed
    except BaseException as error:
        write(directory / "failure.json", {"type": type(error).__name__, "message": str(error), "usage_status": "UNAVAILABLE_OR_PARTIAL"})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    for name in ("spec", "spec-sha256", "output"):
        prep.add_argument("--" + name, required=True)
    for name in ("fit", "readout"):
        child = sub.add_parser(name)
        child.add_argument("--manifest", required=True)
        child.add_argument("--manifest-sha256", required=True)
        child.add_argument("--deadline", type=float, required=True)
        if name == "readout": child.add_argument("--arm", choices=readout_api.ARMS, required=True)
    args = parser.parse_args(argv)
    result = prepare(args.spec, args.spec_sha256, args.output) if args.action == "prepare" else stage(
        args.manifest, args.manifest_sha256, args.deadline, stage=args.action, arm=getattr(args, "arm", None))
    print(canonical({"status": result.get("status", "PREPARED"), "sha256": result["sha256"]}).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
