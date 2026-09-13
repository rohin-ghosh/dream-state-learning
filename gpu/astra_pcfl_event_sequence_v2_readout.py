"""Cold v2 EVENT readout with explicit learner seed; no fit or launcher."""

import argparse
import os
from pathlib import Path
import time

from gpu import astra_pcfl_event_sequence_v2_fit as fit
from gpu import astra_pcfl_event_sequence_readout as prior


SCHEMA = "pcfl.event_sequence.readout.v2"
sequence, prefix, native, v3 = fit.sequence, fit.prefix, fit.native, fit.v3
reader = prior.reader
require, same, write, read = fit.require, fit.same, fit.write, prior.read
CAP_SECONDS = prior.CAP_SECONDS
_adapter_view, _custody = prior._adapter_view, prior._custody


def source_files():
    return {**fit.source_files(), **prior.source_files(),
            str(Path(__file__).resolve()): fit.file_hash(__file__)}


def _checkpoint(inputs, material, state, output, kind):
    phase = sequence.READ_STATES[state]
    pin = inputs.get("fit_receipt")
    require(bool(pin) == (phase is not None), "NO_WRITE has no fit; fitted state needs exact completion")
    if phase is None:
        return None, None, None
    receipt = fit.read_pin(pin)
    prefix.unseal(receipt, receipt["sha256"])
    root = Path(pin["path"]).parent
    require(Path(pin["path"]).name == "completed.json" and not (root / "failure.json").exists(), "failed fit")
    require(receipt["schema"] == fit.SCHEMA + "/completed" and receipt["status"] == "COMPLETE"
            and receipt["phase"] == phase and receipt["kind"] == kind and receipt["base_unchanged"] is True
            and receipt["nonfinite_batches"] == 0 and receipt["updates"] == sequence.PHASES[phase][1], "matching v2 completed phase required")
    selected = material["phases"][phase]
    same(receipt["learner_seed"], material["spec"]["learner_seed"], "fit learner seed differs")
    same(receipt["parent_phase"], sequence.PHASES[phase][0], "fit parent phase differs")
    if sequence.PHASES[phase][0] is None:
        require(receipt["predecessor"] is None and receipt["warm_start"] is None, "cold phase requires clean C0")
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
    config = sequence.training_config(phase, inputs["model_path"], learner_seed=material["spec"]["learner_seed"],
                                      device=read(root / "config.json")["device"])
    manifest = read(checkpoint / "train_manifest.json")
    fit._completion(manifest, config, selected, fit.file_hash(root / "corpus.json"))
    same(read(root / "config.json"), manifest["config"], "saved config differs")
    same(read(root / "corpus.json"), selected["items"], "fit corpus differs from registered phase")
    same(manifest.get("warm_start"), receipt["warm_start"], "warm initialization differs")
    v3._warm_parent(checkpoint, output / "unused_validation_output", config)
    require((checkpoint / "adapter_model.safetensors").is_file(), "reader requires safetensors; no conversion")
    return checkpoint, root, inventory


def run_state(inputs_path, inputs_sha256, output, deadline, *, state="A200", tokenizer_factory=None,
              actor_factory=None, environment_reader=None, clock=time.monotonic):
    started = clock()
    native.number(deadline, positive=True)

    def check():
        require(clock() < deadline, "readout deadline; Main owns hard timeout")

    check()
    injected = any(value is not None for value in (tokenizer_factory, actor_factory, environment_reader))
    kind = "INJECTED_CPU_TEST" if injected else "NATIVE"
    require(state in sequence.READ_STATES, "unknown v2 state")
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
    seed = material["spec"]["learner_seed"]
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
        tokenizer = (tokenizer_factory or fit._tokenizer)(sequence.training_config("A200", model, learner_seed=seed))
        same(sequence.export_material(imported, imported["sha256"], tokenizer, learner_seed=seed), material, "material/tokenizer reconstruction differs")
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
            "interpretation": "V2 single-state cold EVENT reproduction; one state alone does not establish retention", "pass_threshold": None})
        write(root / "custody.json", custody)
        completed = prefix.seal({"schema": SCHEMA + "/completed", "status": "COMPLETE", "kind": kind, "state": state,
            "learner_seed": seed, "inputs": inputs_pin, "material_sha256": inputs["material"]["sha256"], "spec_sha256": material["spec"]["sha256"],
            "import_sha256": imported["sha256"], "fit_receipt": inputs.get("fit_receipt"), "route": reader.route_identity(settings),
            "calls": 16, "fits": 0, "updates": 0, "panels": panels,
            "tokens": {"prompt": sum(row["prompt_tokens"] for row in responses), "output": sum(row["output_tokens"] for row in responses)},
            "truncated": sum(row["finish_reason"] == "length" for row in responses),
            "elapsed_seconds": {**custody["elapsed_seconds"], "worker": clock() - started},
            "time_basis": custody["time_basis"], "original_status": "FORMATION_FAILED", "limits": sequence.LIMITS,
            "files": v3._warm_inventory(root), "outer_release_required": True, "gpu_released": False,
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
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--state", choices=tuple(sequence.READ_STATES), required=True)
    args = parser.parse_args(argv)
    result = run_state(args.inputs, args.inputs_sha256, args.output, args.deadline, state=args.state)
    print(prefix.canonical({"status": result["status"], "state": result["state"], "sha256": result["sha256"]}).decode())


if __name__ == "__main__":
    main()
