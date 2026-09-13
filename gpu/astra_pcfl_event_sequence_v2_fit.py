"""Bounded DEV-only v2 fit; later phases require bound raw acquisition evidence."""

import argparse
from dataclasses import asdict
import os
from pathlib import Path
import time

from gpu import astra_pcfl_event_sequence_fit as v1
from gpu import astra_pcfl_event_sequence_v2_acquisition as acquisition
from organism_v6 import pcfl_event_sequence_v2 as sequence


SCHEMA = "pcfl.event_sequence.fit.v2"
prefix, v3, native, writer = v1.prefix, v1.v3, v1.native, v1.writer
require, same = v1.require, v1.same
OFFLINE = v1.OFFLINE
file_hash, read_pin, write = v1.file_hash, v1.read_pin, v1.write
manifest_json, environment = v1.manifest_json, v1.environment
_tokenizer, _base, _reference, _completion = v1._tokenizer, v1._base, v1._reference, v1._completion


def source_files():
    return {**v1.source_files(), str(Path(sequence.__file__).resolve()): file_hash(sequence.__file__),
            **{path: file_hash(path) for path in acquisition.reader.required_source_paths()},
            str(Path(acquisition.__file__).resolve()): file_hash(acquisition.__file__),
            str(Path(__file__).resolve()): file_hash(__file__)}


def require_acquisition(inputs, material, phase, *, kind="NATIVE"):
    require("acquisition_passed" not in inputs and "gate_passed" not in inputs, "caller acquisition Boolean forbidden")
    if phase == "A200":
        require(inputs.get("acquisition_receipt") is None, "A200 has no acquisition assertion or receipt")
        return None
    pin = inputs.get("acquisition_receipt")
    require(type(pin) is dict and set(pin) == {"path", "sha256"}, "bound acquisition receipt required; no caller assertion")
    result = acquisition.validate(pin, material, inputs, expected_kind=kind)
    require(result["observed_gate"] is True, "A200 acquisition failed; descendants withheld without dose rescue")
    if sequence.PHASES[phase][0] is not None:
        same(inputs["predecessor"], result["a200_fit_receipt"], "warm parent differs from measured A200")
    return result


def validate_predecessor(inputs, material, phase, root, config, kind):
    """Validate exact full immutable A200; never accept S_A40 or a fallback."""
    parent_phase = sequence.PHASES[phase][0]
    pin = inputs.get("predecessor")
    require((pin is None) == (parent_phase is None), "exact immediate predecessor required; cold phases require C0")
    if pin is None:
        return None, None, None
    prior = read_pin(pin)
    prefix.unseal(prior, prior["sha256"])
    require(prior["schema"] == SCHEMA + "/completed" and prior["status"] == "COMPLETE"
            and prior["phase"] == "A200" and prior["kind"] == kind
            and type(prior["updates"]) is int and prior["updates"] == 200
            and prior["parent_phase"] is None and prior["predecessor"] is None
            and prior["warm_start"] is None and prior["base_unchanged"] is True
            and prior["nonfinite_batches"] == 0, "exact completed cold v2 A200 required; S_A40 is ineligible")
    selected = material["phases"]["A200"]
    expected = {"material_sha256": inputs["material"]["sha256"], "export_sha256": material["sha256"],
                "spec_sha256": material["spec"]["sha256"], "import_sha256": material["spec"]["import_sha256"],
                "learner_seed": config.seed, "model_binding": inputs["model_binding"],
                "base_state_receipt": inputs["base_state_receipt"],
                "items_sha256": selected["items_sha256"], "encoding_sha256": selected["encoding_sha256"]}
    for key, value in expected.items():
        same(prior[key], value, "predecessor binding differs: " + key)
    parent_root = Path(pin["path"]).parent
    require(Path(pin["path"]).name == "completed.json" and not (parent_root / "failure.json").exists(), "failed predecessor")
    parent = parent_root / "checkpoint"
    same(prior["checkpoint"], str(parent), "predecessor checkpoint path differs")
    before = v3._warm_inventory(parent_root)
    same({name: value for name, value in before.items() if name != "completed.json"}, prior["files"], "predecessor file drift")
    saved_config = prefix._json(prefix._record((parent_root / "config.json").read_bytes()))
    parent_config = sequence.training_config("A200", config.model, learner_seed=config.seed, device=saved_config["device"])
    same(saved_config, asdict(parent_config), "predecessor config/seed drift")
    manifest = prefix._json(prefix._record((parent / "train_manifest.json").read_bytes()))
    _completion(manifest, parent_config, selected, file_hash(parent_root / "corpus.json"))
    require(manifest.get("warm_start") is None, "A200 must start from clean C0")
    same(prefix._json(prefix._record((parent_root / "corpus.json").read_bytes())), selected["items"], "predecessor material drift")
    v3._warm_parent(parent, root / "checkpoint", config)
    require(not root.is_relative_to(parent_root) and not parent_root.is_relative_to(root), "output/predecessor overlap")
    return parent, prior, before


def validate_warm_tensors(warm, trainable):
    """Join every saved LoRA tensor to its loaded initialization receipt."""
    require(warm["initialized_loaded_state_check"] is True, "initialized loaded state check required")
    source, initialized = warm["source_state"], warm["initialized_state"]
    expected = {name.replace(".default.weight", ".weight") for name in trainable}
    require(bool(expected), "full parent tensor coverage required")
    same(sorted(source), sorted(expected), "full parent tensor coverage differs")
    same(sorted(initialized), sorted(expected), "full initialized tensor coverage differs")
    conversions = warm["dtype_conversions"]
    changed = {name for name in expected if source[name]["dtype"] != initialized[name]["dtype"]}
    same(sorted(conversions), sorted(changed), "actual dtype conversion coverage differs")
    for name in expected:
        before, after = source[name], initialized[name]
        require(name.endswith((".lora_A.weight", ".lora_B.weight")), "non-LoRA tensor receipt")
        native.sha(before["sha256"])
        native.sha(after["sha256"])
        same(before["shape"], after["shape"], "parent tensor shape drift")
        if name in changed:
            same(conversions[name], {"source": before["dtype"], "initialized": after["dtype"]}, "dtype conversion binding")
        else:
            same(before, after, "parent tensor initialization drift")
    if changed:
        import torch
        parent = Path(warm["parent_path"])
        same(v3._warm_inventory(parent), warm["parent_files"], "parent conversion inventory drift")
        weights = [name for name in ("adapter_model.safetensors", "adapter_model.bin") if name in warm["parent_files"]]
        require(len(weights) == 1, "exact parent conversion weights required")
        if weights[0].endswith(".safetensors"):
            from safetensors.torch import load_file
            tensors = load_file(str(parent / weights[0]), device="cpu")
        else:
            tensors = torch.load(str(parent / weights[0]), map_location="cpu", weights_only=True)
        same(v3._warm_state_inventory(tensors), source, "parent conversion source tensor drift")
        converted = {}
        for name in expected:
            dtype_name = initialized[name]["dtype"]
            require(isinstance(dtype_name, str) and dtype_name.startswith("torch."), "initialized tensor dtype")
            dtype = getattr(torch, dtype_name.removeprefix("torch."), None)
            require(isinstance(dtype, torch.dtype), "initialized tensor dtype")
            converted[name] = tensors[name].to(dtype=dtype, device="cpu")
        same(v3._warm_state_inventory(converted), initialized, "converted parent tensor initialization drift")
        same(v3._warm_inventory(parent), warm["parent_files"], "parent conversion inventory drift")


def run_phase(inputs_path, inputs_sha256, output, deadline, *, phase="A200", device="cuda",
              tokenizer_factory=None, base_factory=None, train=None, reference_reader=None,
              state_hash=None, environment_reader=None, clock=time.monotonic):
    """Pinned inputs JSON; injected dependencies label every completion non-native."""
    injected = any(value is not None for value in (tokenizer_factory, base_factory, train, reference_reader,
                                                   state_hash, environment_reader))
    kind = "INJECTED_CPU_TEST" if injected else "NATIVE"
    started = clock()
    native.number(deadline, positive=True)
    require(0 < deadline - started <= 1800, "bounded worker deadline required (maximum 1800 seconds)")
    def check():
        require(clock() < deadline, "worker deadline exhausted; Main owns hard timeout")
    check()
    require(all(os.environ.get(key) == "1" for key in OFFLINE), "offline flags required")
    inputs_pin = {"path": str(Path(inputs_path).absolute()), "sha256": inputs_sha256}
    inputs = read_pin(inputs_pin)
    require(inputs["schema"] == SCHEMA + "/inputs", "input schema")
    same(inputs["source_files"], source_files(), "loaded source pins differ")
    same(inputs["environment"], (environment_reader or environment)(), "environment drift")
    model, root = Path(inputs["model_path"]), Path(output).absolute()
    require(model.is_dir() and not root.exists() and not any(path.is_symlink() for path in (root, *root.parents)), "local model/fresh output required")
    root = root.resolve()
    require(not root.is_relative_to(model.resolve()) and not model.resolve().is_relative_to(root), "output/base overlap")
    material = read_pin(inputs["material"])
    prefix.unseal(material, material["sha256"])
    require(material["schema"] == sequence.SCHEMA + "/export", "v2 material schema required")
    sequence._seed(inputs["learner_seed"])
    same(inputs["learner_seed"], material["spec"]["learner_seed"], "learner seed drift")
    config = sequence.training_config(phase, model, learner_seed=inputs["learner_seed"], device=device)
    replay = read_pin(inputs["replay_receipt"])
    require(file_hash(inputs["archive"]["path"]) == inputs["archive"]["sha256"] == prefix.ARCHIVE_SHA256, "source archive pin")
    imported = prefix.build_import(prefix.load_evidence(inputs["archive"]["path"]), replay, replay["sha256"])
    sequence.validate_spec(material["spec"], imported, imported["sha256"])
    parent_phase = sequence.PHASES[phase][0]
    predecessor_pin = inputs.get("predecessor")
    parent, prior, before_parent = validate_predecessor(inputs, material, phase, root, config, kind)
    acquisition_result = require_acquisition(inputs, material, phase, kind=kind)
    root.mkdir(parents=False, exist_ok=False)
    write(root / "inputs.json", inputs)
    try:
        check()
        identity, unchanged = (reference_reader or _reference)(inputs, material, root, deadline, clock)
        cpu = read_pin(inputs["base_state_receipt"])
        require(cpu["schema"] == "pcfl.own_write.cpu_base_state.v1" and cpu["status"] == "COMPLETE"
                and cpu["dtype"] == "bfloat16" and cpu["device"] == "cpu"
                and cpu["model_binding_sha256"] == inputs["model_binding"]["sha256"], "CPU base reference differs")
        same([cpu["model_files"], cpu["environment"]], [identity["model_files"], inputs["environment"]], "CPU model/environment reference")
        same(cpu["base_state_sha256"], prefix._json(imported["evidence"]["files"]["manifest.json"])["binding"]["base_state_sha256"], "original SOURCE base identity")
        check()
        tokenizer = (tokenizer_factory or _tokenizer)(config)
        check()
        same(sequence.export_material(imported, imported["sha256"], tokenizer, learner_seed=config.seed), material, "export/item/encoding reconstruction drift")
        selected = material["phases"][phase]
        write(root / "corpus.json", selected["items"])
        corpus_hash = file_hash(root / "corpus.json")
        write(root / "config.json", asdict(config))
        check()
        load_started = clock()
        base = (base_factory or _base)(config)
        check()
        require(not hasattr(base, "peft_config") and not any("lora_" in name for name, value in base.named_parameters()), "fresh unadapted base required")
        references = {**dict(base.named_parameters(remove_duplicate=False)), **dict(base.named_buffers(remove_duplicate=False))}
        references = {name: references[name] for name in base.state_dict()}
        hasher = state_hash or writer._state_hash
        same(hasher(references), cpu["base_state_sha256"], "actual frozen C0 tensor identity")
        require(all(str(value.dtype) == "torch.bfloat16" for value in references.values() if value.is_floating_point()), "bf16 base required")
        for parameter in base.parameters():
            parameter.requires_grad_(False)
        write(root / "base.json", {"state_sha256": cpu["base_state_sha256"], "reference": identity, "kind": kind})
        loaded = clock()
        check()
        manifest = (train or v3.run_training)(selected["items"], tokenizer, base, config, str(root / "checkpoint"),
                                             corpus_sha=corpus_hash, corpus_name="corpus.json",
                                             init_adapter=str(parent) if parent else None)
        fitted = clock()
        check()
        _completion(manifest, config, selected, corpus_hash)
        same(read_pin({"path": str(root / "checkpoint/train_manifest.json"),
                       "sha256": file_hash(root / "checkpoint/train_manifest.json")}), manifest_json(manifest), "saved manifest differs")
        v3._warm_parent(root / "checkpoint", root / "unused_validation_output", config)
        same(hasher(references), cpu["base_state_sha256"], "frozen base changed")
        current = {id(value) for value in (*base.parameters(), *dict(base.named_buffers()).values())}
        require(all(id(value) in current for value in references.values()), "original base tensors replaced")
        require(all(not parameter.requires_grad for parameter in references.values()), "original base must remain frozen")
        trainable = [name for name, value in base.named_parameters() if value.requires_grad]
        require(trainable and all(name.endswith((".lora_A.default.weight", ".lora_B.default.weight")) for name in trainable), "LoRA-only trainability required")
        if not parent:
            require(manifest.get("warm_start") is None, "cold phase must start from C0")
        if parent:
            warm = manifest["warm_start"]
            require(warm["initialized_loaded_state_check"] is True and warm["base_frozen"] is True
                    and warm["adapter_count"] == 1 and warm["parent_unchanged"] is True
                    and warm["optimizer_initialization"] == "fresh_per_write" and warm["optimizer_state_restored"] is False
                    and warm["optimizer_initial_state_entries"] == 0 and warm["optimizer_state_saved"] is False
                    and warm["phase_steps"] == config.max_steps, "V3 warm tensor/optimizer receipt required")
            require(bool(warm["source_state"]) and set(warm["source_state"]) == set(warm["initialized_state"]), "full warm tensor receipt missing")
            validate_warm_tensors(warm, trainable)
            same(warm["parent_path"], str(parent), "V3 initialized predecessor differs")
            same(warm["parent_files"], v3._warm_inventory(parent), "V3 parent inventory differs")
            same(warm["parent_files_after"], warm["parent_files"], "V3 changed parent files")
            same(warm["cumulative_steps"], (prior.get("warm_start") or {}).get("cumulative_steps", prior["updates"]) + config.max_steps,
                 "V3 cumulative steps differ")
            same(v3._warm_inventory(parent.parent), before_parent, "immutable predecessor changed")
        if predecessor_pin:
            same(read_pin(predecessor_pin), prior, "predecessor receipt changed")
        if acquisition_result is not None:
            same(require_acquisition(inputs, material, phase, kind=kind), acquisition_result, "acquisition evidence changed during fit")
        unchanged()
        same(read_pin(inputs_pin), inputs, "inputs changed")
        same(source_files(), inputs["source_files"], "source drift during fit")
        for name in ("material", "model_binding", "base_state_receipt", "replay_receipt", "archive"):
            require(file_hash(inputs[name]["path"]) == inputs[name]["sha256"], "input changed during fit")
        check()
        completed = prefix.seal({"schema": SCHEMA + "/completed", "status": "COMPLETE", "kind": kind,
            "phase": phase, "learner_seed": config.seed, "parent_phase": parent_phase, "predecessor": predecessor_pin,
            "inputs": inputs_pin, "material_sha256": inputs["material"]["sha256"], "export_sha256": material["sha256"],
            "spec_sha256": material["spec"]["sha256"], "import_sha256": imported["sha256"],
            "items_sha256": selected["items_sha256"], "encoding_sha256": selected["encoding_sha256"],
            "model_binding": inputs["model_binding"], "base_state_receipt": inputs["base_state_receipt"],
            "updates": manifest["steps"], "nonfinite_batches": 0, "checkpoint": str(root / "checkpoint"),
            "warm_start": manifest.get("warm_start"), "base_unchanged": True, "trainable_names": trainable,
            "files": v3._warm_inventory(root), "elapsed_seconds": {"load_and_base_check": loaded - load_started,
                "v3_fit_call": fitted - loaded, "worker": clock() - started},
            "original_status": "FORMATION_FAILED", "limits": sequence.LIMITS, "outer_release_required": True,
            "acquisition_validation": acquisition_result or "NOT_REQUIRED_A200", "descendants_enabled": False,
            "gpu_released": False, "full_contract_released": False, "automatic_promotion": False})
        check()
        write(root / "completed.json", completed)
        return completed
    except BaseException as error:
        write(root / "failure.json", {"status": "FAILED", "kind": kind, "phase": phase,
                                     "type": type(error).__name__, "message": str(error), "partial_checkpoint_not_eligible": True})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inputs", "inputs-sha256", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--deadline", type=float, required=True, help="Same-host monotonic absolute deadline; Main enforces hard timeout")
    parser.add_argument("--phase", choices=tuple(sequence.PHASES), default="A200")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args(argv)
    result = run_phase(args.inputs, args.inputs_sha256, args.output, args.deadline, phase=args.phase, device=args.device)
    print(prefix.canonical({"status": result["status"], "phase": result["phase"], "sha256": result["sha256"]}).decode())


if __name__ == "__main__":
    main()
