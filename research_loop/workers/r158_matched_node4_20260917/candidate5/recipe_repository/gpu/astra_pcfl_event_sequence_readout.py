"""One cold 16-call sequence state; no training, selection, or process launcher."""

import argparse
import os
from pathlib import Path
import time

from gpu import astra_pcfl_event_sequence_fit as fit
from gpu import astra_pcfl_own_write_readout as reader


SCHEMA = "pcfl.event_sequence.readout.v1"
sequence, prefix, native, v3 = fit.sequence, fit.prefix, fit.native, fit.v3
require, same, write = fit.require, fit.same, fit.write
CAP_SECONDS = 1740


def read(path):
    return prefix._json(prefix._record(Path(path).read_bytes()))


def source_files():
    return {**fit.source_files(), **{path: fit.file_hash(path) for path in reader.required_source_paths()},
            str(Path(__file__).resolve()): fit.file_hash(__file__)}


def _checkpoint(inputs, material, state, output, kind):
    phase = sequence.READ_STATES[state]
    pin = inputs.get("fit_receipt")
    require(bool(pin) == (phase is not None), "NO_WRITE has no fit; fitted state requires exact completion")
    if phase is None:
        return None, None, None
    receipt = fit.read_pin(pin)
    prefix.unseal(receipt, receipt["sha256"])
    root = Path(pin["path"]).parent
    require(Path(pin["path"]).name == "completed.json" and not (root / "failure.json").exists(), "failed fit")
    require(receipt["schema"] == fit.SCHEMA + "/completed" and receipt["status"] == "COMPLETE"
            and receipt["phase"] == phase and receipt["kind"] == kind and receipt["base_unchanged"] is True
            and receipt["nonfinite_batches"] == 0 and receipt["updates"] == sequence.PHASES[phase][1], "matching completed phase required")
    selected = material["phases"][phase]
    same([receipt[key] for key in ("material_sha256", "export_sha256", "spec_sha256", "import_sha256", "items_sha256", "encoding_sha256")],
         [inputs["material"]["sha256"], material["sha256"], material["spec"]["sha256"], material["spec"]["import_sha256"],
          selected["items_sha256"], selected["encoding_sha256"]], "fit/material join")
    same([receipt["model_binding"], receipt["base_state_receipt"]],
         [inputs["model_binding"], inputs["base_state_receipt"]], "fit/base binding")
    inventory = v3._warm_inventory(root)
    same({key: value for key, value in inventory.items() if key != "completed.json"}, receipt["files"], "fit file drift")
    checkpoint = root / "checkpoint"
    same(receipt["checkpoint"], str(checkpoint), "checkpoint path differs")
    require(not output.is_relative_to(root) and not root.is_relative_to(output), "output overlaps immutable fit")
    config = sequence.training_config(phase, inputs["model_path"], device=read(root / "config.json")["device"])
    fit._completion(read(checkpoint / "train_manifest.json"), config, selected, fit.file_hash(root / "corpus.json"))
    v3._warm_parent(checkpoint, output / "unused_validation_output", config)
    require((checkpoint / "adapter_model.safetensors").is_file(), "reader requires safetensors; no bin conversion")
    return checkpoint, root, inventory


def _adapter_view(checkpoint, output):
    if checkpoint is None:
        return None
    destination = output / "adapter"
    destination.mkdir()
    names = [name for name in ("adapter_config.json", "adapter_model.safetensors", "README.md") if (checkpoint / name).is_file()]
    files = {}
    for name in names:
        with (destination / name).open("xb") as stream:
            stream.write((checkpoint / name).read_bytes())
        same(fit.file_hash(destination / name), fit.file_hash(checkpoint / name), "adapter copy byte drift")
        files[name] = {"size": (destination / name).stat().st_size, "sha256": fit.file_hash(destination / name)}
    route = {"name": "pcfl-own-write", "id": 1, "path": str(destination), "files": files}
    write(output / "adapter_projection.json", {"kind": "BYTE_IDENTICAL_MOUNT_COPY_NO_TRAINING", "source_checkpoint": str(checkpoint), "adapter": route})
    return route


def _custody(root, settings, responses, injected, tokenizer):
    actor_root = root / "actor"
    identity, load, close = (read(actor_root / name) for name in ("identity.json", "load.json", "close.json"))
    kind = "INJECTED_CPU_TEST" if injected else "NATIVE_OWN_WRITE_READOUT"
    route = reader.route_identity(settings)
    require(identity["kind"] == load["kind"] == close["kind"] == kind and identity["pid"] == os.getpid()
            and identity["config_sha256"] == prefix.digest(settings) and identity["identity"]["route"] == route, "loaded identity/route differs")
    same(read(actor_root / "config.json"), settings, "captured actor config differs")
    same(close, read(root / "actor_close.json"), "close receipt differs")
    require(close["calls_consumed"] == close["planned_calls"] == len(responses) == 16
            and close["route"] == load["route"] == route and close["error_type"] is None
            and close["failed"] is False and close["budget_exceeded"] is False
            and close["shutdown"]["shutdown_returned"] is True
            and close["shutdown"]["source"] == load["shutdown"]["source"] == settings["shutdown_binding"], "readout close/load/call join")
    require(len(list(actor_root.glob("call_*.raw.json"))) == 16, "exact raw call inventory")
    generation_seconds = 0.0
    for index, (row, response) in enumerate(zip(settings["roster"], responses)):
        raw, returned, requested, rendered = (read(actor_root / f"call_{index:04d}{suffix}.json")
                                             for suffix in (".raw", ".response", ".request", ".render"))
        require(raw["kind"] == kind and raw["route"] == raw["raw"]["route"] == response["route"] == route
                and returned["response"] == response and response["id"] == row["id"] and requested["row"] == row
                and requested["request"] == {"id": row["id"]} and requested["messages"] == reader.public_messages(row), "readout capture/request/route join")
        require(response["request_sha256"] == prefix.digest({"id": row["id"]})
                and response["roster_sha256"] == settings["roster_sha256"], "returned request/roster identity")
        require(raw["raw"]["text"] == response["text"] and raw["raw"]["finish_reason"] == response["finish_reason"]
                and raw["raw"]["stop_reason"] == response["stop_reason"]
                and returned["raw_hex"] == response["text"].encode().hex()
                and returned["raw_utf8_sha256"] == native.text_hash(response["text"]), "raw scored byte/stop join")
        same(raw["raw"]["prompt_token_ids"], rendered["prompt_token_ids"], "raw/render token IDs")
        same([response["prompt_tokens"], response["output_tokens"]],
             [len(native.token_ids(raw["raw"]["prompt_token_ids"])), len(native.token_ids(raw["raw"]["output_token_ids"]))], "exact token counts")
        same(tokenizer.decode(raw["raw"]["output_token_ids"], skip_special_tokens=True), response["text"], "captured token decode differs")
        require(rendered["sampling"] == {**native.SAMPLING, "seed": row["seed"], "max_tokens": 2048}
                and rendered["route"] == route and load["ready_at"] <= raw["generation_started"] <= raw["generation_ended"] <= settings["deadline"], "sampling/cold chronology")
        generation_seconds += raw["generation_ended"] - raw["generation_started"]
    return {"kind": kind, "route": route, "calls": 16, "identity_sha256": prefix.digest(identity),
            "elapsed_seconds": {"model_load": load["ready_at"] - load["model_load_started"],
                                "generation_calls": generation_seconds, "actor_operations": close["elapsed_actor_seconds"]},
            "time_basis": "wall intervals, not GPU active time", "outer_release_required": True}


def run_state(inputs_path, inputs_sha256, output, deadline, *, state="S_A", tokenizer_factory=None,
              actor_factory=None, environment_reader=None, clock=time.monotonic):
    """One frozen state only. Injected seams never produce a native completion."""
    started = clock()
    native.number(deadline, positive=True)
    def check():
        require(clock() < deadline, "readout deadline; Main owns hard timeout")
    check()
    injected = any(value is not None for value in (tokenizer_factory, actor_factory, environment_reader))
    kind = "INJECTED_CPU_TEST" if injected else "NATIVE"
    require(state in sequence.READ_STATES, "unknown measured state")
    require(all(os.environ.get(key) == "1" for key in fit.OFFLINE), "offline flags required")
    inputs_pin = {"path": str(Path(inputs_path).absolute()), "sha256": inputs_sha256}
    inputs = fit.read_pin(inputs_pin)
    require(inputs["schema"] == SCHEMA + "/inputs", "readout input schema")
    same(inputs["source_files"], source_files(), "readout source pins differ")
    same(inputs["environment"], (environment_reader or fit.environment)(), "readout environment drift")
    root, model = Path(output).absolute(), Path(inputs["model_path"])
    require(model.is_absolute() and model.is_dir() and not root.exists()
            and not any(path.is_symlink() for path in (root, *root.parents)), "local base/fresh output required")
    root = root.resolve()
    require(not root.is_relative_to(model.resolve()) and not model.resolve().is_relative_to(root), "output/base overlap")
    material = fit.read_pin(inputs["material"])
    prefix.unseal(material, material["sha256"])
    replay = fit.read_pin(inputs["replay_receipt"])
    require(fit.file_hash(inputs["archive"]["path"]) == inputs["archive"]["sha256"] == prefix.ARCHIVE_SHA256, "original archive pin")
    imported = prefix.build_import(prefix.load_evidence(inputs["archive"]["path"]), replay, replay["sha256"])
    sequence.validate_spec(material["spec"], imported, imported["sha256"])
    cpu = fit.read_pin(inputs["base_state_receipt"])
    require(cpu["schema"] == "pcfl.own_write.cpu_base_state.v1" and cpu["status"] == "COMPLETE"
            and cpu["dtype"] == "bfloat16" and cpu["device"] == "cpu"
            and cpu["model_binding_sha256"] == inputs["model_binding"]["sha256"], "CPU base reference")
    same(cpu["environment"], inputs["environment"], "CPU environment differs")
    same(cpu["base_state_sha256"], prefix._json(imported["evidence"]["files"]["manifest.json"])["binding"]["base_state_sha256"], "original base state differs")
    reference = fit.read_pin(inputs["model_binding"])
    same(cpu["model_files"], {name: entry["sha256"] for name, entry in reference["files"].items()}, "CPU/public base file join")
    checkpoint, fit_root, before_fit = _checkpoint(inputs, material, state, root, kind)
    root.mkdir(parents=False, exist_ok=False)
    write(root / "inputs.json", inputs)
    try:
        check()
        tokenizer = (tokenizer_factory or fit._tokenizer)(sequence.training_config("S_A", model))
        same(sequence.export_material(imported, imported["sha256"], tokenizer), material, "material/tokenizer reconstruction differs")
        adapter = _adapter_view(checkpoint, root)
        roster = material["spec"]["roster"]
        require(len(roster) == 16 and all(row["output_tokens"] == 2048 for row in roster), "fixed 16/2048 roster")
        tokens = material["tokenizer_receipt"]
        settings = {"schema": reader.SCHEMA, "model_path": str(model), "model_binding": inputs["model_binding"],
            "source_files": inputs["source_files"], "tokenizer_files": tokens["tokenizer_files"],
            "chat_template_sha256": tokens["chat_template_sha256"], "tokenizer_probe": {"text": "probe", "token_ids": tokenizer.encode("probe", add_special_tokens=False)},
            "environment": inputs["environment"]["native"], "gpu_uuid": inputs["gpu_uuid"], "engine": reader.ENGINE,
            "output_dir": str(root / "actor"), "deadline": deadline, "device_seconds_cap": CAP_SECONDS,
            "max_input_tokens": 14336, "max_output_tokens": 2048, "max_calls": 16,
            "arm": "NO_WRITE_C0" if state == "NO_WRITE" else "AUTH_WRITE", "adapter": adapter,
            "roster": roster, "roster_sha256": material["spec"]["roster_sha256"], "shutdown_binding": inputs["shutdown_binding"]}
        write(root / "readout_config.json", settings)
        check()
        actor = (actor_factory or reader.ReadoutActor)(settings)
        responses, results = [], []
        try:
            for index, row in enumerate(roster):
                check()
                response = actor.generate({"id": row["id"]}, {"deadline": deadline, "device_seconds": CAP_SECONDS})
                responses.append(response)
                write(root / f"response_{index:04d}.json", response)
                record = material["spec"]["records"][index % 8]
                same(row["request"], record["request"], "ordered EVENT target join")
                score = sequence.core.score_memory_response(response["text"], record["target"])
                results.append({"id": row["id"], "request": row["request"], "view": row["view"], "bank": record["bank"],
                    "record": record["index"], "raw": response["text"], "target_sha256": native.text_hash(record["target"]),
                    "finish_reason": response["finish_reason"], "prompt_tokens": response["prompt_tokens"],
                    "output_tokens": response["output_tokens"], "score": score,
                    "strict_stop": response["finish_reason"] == "stop" and score["strict"]})
        finally:
            write(root / "actor_close.json", actor.close())
        custody = _custody(root, settings, responses, injected, tokenizer)
        actor._unchanged_files()
        if fit_root:
            same(v3._warm_inventory(fit_root), before_fit, "immutable fit changed during readout")
        same(fit.read_pin(inputs_pin), inputs, "input changed during readout")
        same(source_files(), inputs["source_files"], "readout source drift")
        for name in ("material", "archive", "replay_receipt", "model_binding", "base_state_receipt", "shutdown_binding"):
            require(fit.file_hash(inputs[name]["path"]) == inputs[name]["sha256"], "readout input drift")
        panels = {}
        for view in (0, 8):
            panels[f"W{view}"] = {}
            for bank in ("A", "B"):
                rows = [row for row in results if row["view"] == view and row["bank"] == bank]
                require(len(rows) == 4, "fixed four-address bank denominator")
                panels[f"W{view}"][bank] = {"denominator": 4, "ids": [row["id"] for row in rows],
                    "strict_stop": [row["strict_stop"] for row in rows], "correct": sum(row["strict_stop"] for row in rows)}
        write(root / "scores.json", {"state": state, "denominator": 16, "results": results, "panels": panels,
            "interpretation": ("S_A40 acquisition screen" if state == "S_A" else "Single-state cold EVENT reproduction")
                              + "; one state alone does not establish retention", "pass_threshold": None})
        write(root / "custody.json", custody)
        files = v3._warm_inventory(root)
        completed = prefix.seal({"schema": SCHEMA + "/completed", "status": "COMPLETE", "kind": kind, "state": state,
            "inputs": inputs_pin, "material_sha256": inputs["material"]["sha256"], "spec_sha256": material["spec"]["sha256"],
            "import_sha256": imported["sha256"], "fit_receipt": inputs.get("fit_receipt"), "route": reader.route_identity(settings),
            "calls": 16, "fits": 0, "updates": 0, "panels": panels,
            "tokens": {"prompt": sum(row["prompt_tokens"] for row in responses), "output": sum(row["output_tokens"] for row in responses)},
            "truncated": sum(row["finish_reason"] == "length" for row in responses),
            "elapsed_seconds": {**custody["elapsed_seconds"], "worker": clock() - started},
            "time_basis": custody["time_basis"], "original_status": "FORMATION_FAILED", "limits": sequence.LIMITS,
            "files": files, "outer_release_required": True, "gpu_released": False,
            "full_contract_released": False, "automatic_promotion": False})
        check()
        write(root / "completed.json", completed)
        return completed
    except BaseException as error:
        write(root / "failure.json", {"status": "FAILED", "state": state, "kind": kind,
                                     "type": type(error).__name__, "message": str(error), "usage": "UNAVAILABLE_OR_PARTIAL"})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inputs", "inputs-sha256", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--deadline", type=float, required=True, help="Same-host monotonic deadline; Main owns hard timeout")
    parser.add_argument("--state", choices=tuple(sequence.READ_STATES), required=True)
    args = parser.parse_args(argv)
    result = run_state(args.inputs, args.inputs_sha256, args.output, args.deadline, state=args.state)
    print(prefix.canonical({"status": result["status"], "state": result["state"], "sha256": result["sha256"]}).decode())


if __name__ == "__main__":
    main()
