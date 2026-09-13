"""Pinned offline preparation and one supplied-memory interface DEV stage."""

import argparse
from collections import Counter
import inspect
import os
from pathlib import Path
import time

from gpu import astra_pcfl_interface_dev as driver
from gpu import astra_pcfl_native_actor as native
from gpu import astra_pcfl_zero_fit_outer as lifecycle

SCHEMA = "pcfl.interface.command.v1"
TOTAL_SECONDS, CLEANUP_SECONDS, PREPARE_SECONDS = 3600, 120, 180
OFFLINE = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "VLLM_NO_USAGE_STATS")
SPEC_FIELDS = {"schema", "model_path", "model_binding", "roots_file", "shutdown_binding",
               "gpu_uuid", "environment", "expires_monotonic", "boot_id", "source_files"}
require, read, write, file_hash = native.require, lifecycle.read, lifecycle.write, lifecycle.file_hash
canonical, digest = native.canonical, native.digest


def source_files():
    paths = (Path(__file__).resolve(), Path(__file__).with_name("astra_pcfl_interface_outer.py").resolve(),
             Path(lifecycle.__file__).resolve(), Path(lifecycle.driver.__file__).resolve(),
             Path(lifecycle.driver.runtime.__file__).resolve())
    return {**driver.source_pins(), **{str(path): file_hash(path) for path in paths}}


def _pin(record, deadline=None):
    require(type(record) is dict and set(record) == {"path", "sha256"}, "closed input pin required")
    path = Path(record["path"])
    require(path.is_absolute() and path.resolve() == path and path.is_file(), "absolute regular input required")
    native.sha(record["sha256"])
    require(file_hash(path, deadline) == record["sha256"], "input file drift: " + str(path))


def _offline():
    require(all(os.environ.get(key) == "1" for key in OFFLINE), "offline flags required")


def _tokenizer(model):
    _offline()
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False)


def _spec(spec, deadline=None):
    require(type(spec) is dict and set(spec) == SPEC_FIELDS and spec["schema"] == SCHEMA + "/spec", "spec fields")
    require(Path(spec["model_path"]).is_absolute() and Path(spec["model_path"]).is_dir(), "local model required")
    require(type(spec["gpu_uuid"]) is str and spec["gpu_uuid"].startswith("GPU-"), "GPU UUID required")
    native.number(spec["expires_monotonic"], positive=True)
    for key in ("model_binding", "roots_file", "shutdown_binding"):
        _pin(spec[key], deadline)
    require(spec["source_files"] == source_files(), "missing/mutated source pins")


def _settings(spec, roster, tokenizer, output, deadline):
    sources = dict(spec["source_files"])
    for name in ("roots_file", "shutdown_binding"):
        sources[spec[name]["path"]] = spec[name]["sha256"]
    return {"schema": native.SCHEMA, "model_path": spec["model_path"], "model_binding": spec["model_binding"],
            "source_files": sources, "tokenizer_files": {name: file_hash(Path(spec["model_path"]) / name)
                                                         for name in sorted(native.TOKENIZER_FILES)},
            "chat_template_sha256": native.text_hash(tokenizer.chat_template),
            "tokenizer_probe": {"text": "READ EVENT", "token_ids": tokenizer.encode("READ EVENT", add_special_tokens=False)},
            "environment": spec["environment"], "gpu_uuid": spec["gpu_uuid"], "engine": native.ENGINE,
            "output_dir": str(output), "deadline": deadline, "device_seconds_cap": TOTAL_SECONDS - CLEANUP_SECONDS,
            "max_input_tokens": 14336, "max_output_tokens": 256, "max_calls": roster["limits"]["possible_calls"]}


def prepare(spec_path, spec_sha256, output, stage, *, tokenizer_factory=None, environment_reader=None,
            identity_reader=None, clock=time.monotonic):
    started = clock()
    require(stage in driver.STAGES, "single interface stage required")
    _pin({"path": str(spec_path), "sha256": spec_sha256})
    spec, root = read(spec_path), Path(output)
    require(root.is_absolute() and root.parent.resolve() == root.parent and root.parent.is_dir(), "fresh absolute output parent")
    protected = [Path(__file__).resolve().parents[1], Path(spec_path), Path(spec["model_path"])]
    protected += [Path(spec[key]["path"]) for key in ("roots_file", "shutdown_binding", "model_binding")]
    require(all(not root.is_relative_to(path.resolve()) and not path.resolve().is_relative_to(root)
                for path in protected), "output/input/source overlap")
    root.mkdir(exist_ok=False)
    try:
        _offline()
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "prepare requires empty CVD")
        _spec(spec)
        deadline = min(started + PREPARE_SECONDS, spec["expires_monotonic"])
        require(clock() < deadline and spec["boot_id"] == lifecycle.boot_id(), "expired/different boot")
        require(spec["environment"] == (environment_reader or native.environment_identity)(), "environment drift")
        for name, path in (("spec.input.json", spec_path), ("roots.input.json", spec["roots_file"]["path"])):
            with (root / name).open("xb") as stream:
                stream.write(Path(path).read_bytes())
        roster = driver.build_roster(read(root / "roots.input.json"), stage)
        write(root / "roster.json", roster)
        tokenizer = (tokenizer_factory or _tokenizer)(spec["model_path"])
        settings = _settings(spec, roster, tokenizer, root / stage / "actor", deadline)
        checker = native.NativeActor(settings, environment_reader=environment_reader or native.environment_identity, clock=clock)
        identity = (identity_reader or checker._verify_identity)(deadline)
        write(root / "identity.json", identity)
        measurements = []
        for task in roster["tasks"]:
            prompt, tokens = driver._render(tokenizer, task["messages"])
            require(len(tokens) + 256 <= native.ENGINE["max_model_len"] and len(tokens) <= 14336, "initial task context cap")
            measurements.append({"id": task["id"], "prompt_sha256": native.text_hash(prompt), "input_tokens": len(tokens)})
        write(root / "measurements.json", measurements)
        require(file_hash(root / "spec.input.json") == spec_sha256 and file_hash(root / "roots.input.json") == spec["roots_file"]["sha256"], "raw preparation input drift")
        _spec(spec, deadline)
        require(clock() <= deadline, "prepare deadline")
        manifest = driver.seal({"schema": SCHEMA + "/manifest", "root": str(root), "stage": stage, "spec": spec,
            "sources": spec["source_files"], "roster": roster, "actor_template": settings,
            "spec_file_sha256": spec_sha256, "input_files": {path.name: file_hash(path) for path in root.iterdir()},
            "total_seconds": TOTAL_SECONDS, "cleanup_seconds": CLEANUP_SECONDS,
            "kind": "INJECTED_CPU_TEST" if any(value is not None for value in (tokenizer_factory, environment_reader, identity_reader)) else "OFFLINE_PREPARATION",
            "full_assay_qualified": False, "fits": 0, "updates": 0})
        write(root / "manifest.json", manifest)
        return manifest
    except BaseException as error:
        write(root / "prepare_failure.json", {"type": type(error).__name__, "message": str(error)})
        raise


def validate_manifest(path, expected, deadline=None):
    _pin({"path": str(path), "sha256": expected}, deadline)
    manifest = read(path)
    driver._unseal(manifest)
    require(manifest["schema"] == SCHEMA + "/manifest" and manifest["stage"] in driver.STAGES, "manifest schema/stage")
    root = Path(manifest["root"])
    require(root.resolve() == root and Path(path) == root / "manifest.json", "manifest path binding")
    require(manifest["total_seconds"] == TOTAL_SECONDS and manifest["cleanup_seconds"] == CLEANUP_SECONDS
            and manifest["full_assay_qualified"] is False and manifest["fits"] == manifest["updates"] == 0, "scope/budget drift")
    _spec(manifest["spec"], deadline)
    require(manifest["sources"] == manifest["spec"]["source_files"], "manifest source binding")
    require(set(manifest["input_files"]) == {"spec.input.json", "roots.input.json", "roster.json", "identity.json", "measurements.json"}, "prepared inventory")
    for name, checksum in manifest["input_files"].items():
        require(file_hash(root / name, deadline) == checksum, "prepared input changed: " + name)
    require(read(root / "spec.input.json") == manifest["spec"] and file_hash(root / "spec.input.json") == manifest["spec_file_sha256"], "original spec binding")
    require(file_hash(root / "roots.input.json") == manifest["spec"]["roots_file"]["sha256"], "original root file binding")
    roster = manifest["roster"]
    require(read(root / "roster.json") == roster and roster["roots"] == read(root / "roots.input.json")
            and roster["stage"] == manifest["stage"], "preserved roster/root binding")
    driver.validate_roster(roster, roster["sha256"])
    return manifest


def shutdown(actor, binding):
    method = actor._session.llm.llm_engine.engine_core.shutdown
    require(callable(method), "installed EngineCore shutdown unavailable")
    inspect.signature(method).bind()
    require(str(Path(inspect.getsourcefile(method)).resolve()) == binding["path"], "shutdown method source differs")
    _pin(binding)
    method()
    return {"method": "llm.llm_engine.engine_core.shutdown", "source": binding, "shutdown_returned": True}


def _custody(directory, report, settings, injected, started, deadline):
    actor_dir = directory / "actor"
    identity, load, close = (read(actor_dir / name) for name in ("identity.json", "load.json", "close.json"))
    require(read(actor_dir / "config.json") == settings and identity["config_sha256"] == digest(settings)
            and identity["pid"] == os.getpid(), "actor config/PID custody")
    kind = identity["kind"]
    require(kind in ("NATIVE", "INJECTED_CPU_TEST") if injected else kind == "NATIVE", "native stage requires NATIVE captures")
    calls = len(report["attempts"])
    require(report["calls"] == close["calls_consumed"] == calls and calls > 0
            and close["token_count_calls"] == 0 and not list(actor_dir.glob("count_*")), "actual call/count join")
    require(close == read(directory / "actor_close.json") and close["kind"] == load["kind"] == kind
            and close["error_type"] is None and close["failed"] is False and close["budget_exceeded"] is False,
            "actor close/load join")
    require(load["mount"] == "C0" and load["lora_request"] is None, "load must be C0 without LoRA")
    for value in (load["operation_started"], load["model_load_started"], load["ready_at"]):
        native.number(value)
    require(started <= load["operation_started"] <= load["model_load_started"] <= load["ready_at"] <= deadline, "load chronology")
    for index, attempt in enumerate(report["attempts"]):
        require(driver.read_capture(actor_dir, index) == attempt["capture"], "original capture bytes changed")
        records = attempt["capture"]["files"]
        captured_identity = driver._decode(records["identity.json"]["utf8"])
        raw = driver._decode(records[f"call_{index:04d}.raw.json"]["utf8"])
        require(captured_identity == identity and raw["kind"] == kind, "every actual capture identity/kind join")
        require(load["ready_at"] <= raw["generation_started"], "generation before cold load ready")
    return {"actor_kind": kind, "actor_identity_sha256": digest(identity), "actual_calls": calls,
            "possible_calls": report["possible_calls"], "count_tokens_calls": 0,
            "verified_prompt_tokens": sum(attempt["response"]["prompt_tokens"] for attempt in report["attempts"]),
            "verified_output_tokens": sum(attempt["response"]["output_tokens"] for attempt in report["attempts"]),
            "task_reasons": dict(Counter(row["reason"] or "SUCCESS" for row in report["results"])),
            "load_file_sha256": file_hash(actor_dir / "load.json"), "close_file_sha256": file_hash(actor_dir / "close.json"),
            "native_actor_custody_verified": not injected, "outer_release_required": True}


def stage(path, expected, deadline, *, actor_factory=None, tokenizer_factory=None, environment_reader=None, clock=time.monotonic):
    started = clock()
    manifest = validate_manifest(path, expected)
    spec, roster = manifest["spec"], manifest["roster"]
    directory = Path(manifest["root"]) / manifest["stage"]
    directory.mkdir(exist_ok=False)
    injected = any(value is not None for value in (actor_factory, tokenizer_factory, environment_reader))
    write(directory / "entry.json", {"manifest_file_sha256": expected, "started": started, "kind": "INJECTED_CPU_TEST" if injected else "NATIVE"})
    try:
        _offline()
        require(injected or manifest["kind"] == "OFFLINE_PREPARATION", "test preparation cannot launch native")
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == ("" if injected else spec["gpu_uuid"]), "stage CVD binding")
        native.number(deadline, positive=True)
        require(started < deadline <= min(spec["expires_monotonic"], started + TOTAL_SECONDS - CLEANUP_SECONDS), "worker deadline cap")
        require(spec["boot_id"] == lifecycle.boot_id() and spec["environment"] == (environment_reader or native.environment_identity)(), "boot/environment drift")
        tokenizer = (tokenizer_factory or _tokenizer)(spec["model_path"])
        settings = _settings(spec, roster, tokenizer, directory / "actor", deadline)
        require({**settings, "deadline": manifest["actor_template"]["deadline"]} == manifest["actor_template"], "prepared actor binding drift")
        actor = (actor_factory or native.NativeActor)(settings)
        try:
            report = driver.run_stage(roster, roster["sha256"], actor, tokenizer, directory / "records", actor_config=settings, deadline=deadline, clock=clock)
        finally:
            try:
                if getattr(actor, "_session", None) is not None:
                    write(directory / "shutdown.json", shutdown(actor, spec["shutdown_binding"]))
            finally:
                write(directory / "actor_close.json", actor.close())
        close = read(directory / "actor_close.json")
        require(report["status"] == "COMPLETE" and close["error_type"] is None and close["failed"] is False
                and close["budget_exceeded"] is False and (directory / "shutdown.json").is_file(), "stage infrastructure/close failed")
        write(directory / "replay.json", driver.replay_validate(roster, roster["sha256"], report, tokenizer))
        custody = _custody(directory, report, settings, injected, started, deadline)
        write(directory / "custody.json", custody)
        validate_manifest(path, expected)
        files = lifecycle._inventory(directory, deadline)
        ended = clock()
        require(ended <= deadline, "stage deadline at completion")
        receipt = driver.seal({"schema": SCHEMA + "/completed", "status": "COMPLETE", "stage": manifest["stage"],
            "manifest_sha256": manifest["sha256"], "started": started, "ended": ended, "elapsed_seconds": ended - started,
            "report_sha256": report["sha256"], "summary": report["summary"], "outer_release_required": True,
            "gpu_released": False, "full_assay_qualified": False, "fits": 0, "updates": 0,
            "kind": "INJECTED_CPU_TEST" if injected else "NATIVE", "actual_calls": report["calls"],
            "possible_calls": report["possible_calls"], "task_reasons": custody["task_reasons"],
            "files": {name: entry["sha256"] for name, entry in files.items()}})
        write(directory / "completed.json", receipt)
        return receipt
    except BaseException as error:
        write(directory / "failure.json", {"type": type(error).__name__, "message": str(error),
              "usage_status": "UNAVAILABLE_OR_PARTIAL_SEE_ORIGINAL_CAPTURES"})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    for name in ("spec", "spec-sha256", "output"):
        prep.add_argument("--" + name, required=True)
    prep.add_argument("--stage", choices=driver.STAGES, required=True)
    run = sub.add_parser("stage")
    for name in ("manifest", "manifest-sha256"):
        run.add_argument("--" + name, required=True)
    run.add_argument("--deadline", type=float, required=True)
    args = parser.parse_args(argv)
    result = prepare(args.spec, args.spec_sha256, args.output, args.stage) if args.action == "prepare" else stage(args.manifest, args.manifest_sha256, args.deadline)
    print(canonical({"status": result.get("status", "PREPARED"), "sha256": result["sha256"]}).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
