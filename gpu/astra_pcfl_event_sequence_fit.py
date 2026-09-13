"""One separately labeled V3 EVENT write; Main owns processes and hard timeout."""

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time

from organism_v6 import pcfl_event_sequence as sequence
from organism_v6 import pcfl_vertical_train as writer


SCHEMA = "pcfl.event_sequence.fit.v1"
prefix, v3 = sequence.prefix, sequence.trainer
native = prefix.native
require, same = prefix.require, prefix.same
OFFLINE = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "VLLM_NO_USAGE_STATS")


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_pin(pin):
    require(set(pin) == {"path", "sha256"} and Path(pin["path"]).is_absolute(), "absolute file pin required")
    native.sha(pin["sha256"])
    raw = Path(pin["path"]).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == pin["sha256"], "input file drift: " + pin["path"])
    return prefix._json(prefix._record(raw))


def write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(prefix.canonical(value) + b"\n")


def manifest_json(value):
    return json.loads(json.dumps(value, allow_nan=False))


def source_files():
    return {**sequence.source_snapshot(), str(Path(__file__).resolve()): file_hash(__file__)}


def environment():
    return {"native": native.environment_identity(), "peft_version": importlib.metadata.version("peft")}


def _tokenizer(config):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(config.model, local_files_only=True, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    return tokenizer


def _base(config):
    from transformers import AutoModelForCausalLM
    return AutoModelForCausalLM.from_pretrained(
        config.model, torch_dtype=v3._torch_dtype(config.dtype), local_files_only=True,
        trust_remote_code=False, device_map=config.device if config.device != "cpu" else None)


def _reference(inputs, material, output, deadline, clock):
    tokens = material["tokenizer_receipt"]
    checker = native.NativeActor({
        "schema": native.SCHEMA, "model_path": inputs["model_path"], "model_binding": inputs["model_binding"],
        "source_files": inputs["source_files"], "tokenizer_files": tokens["tokenizer_files"],
        "chat_template_sha256": tokens["chat_template_sha256"], "tokenizer_probe": {"text": "", "token_ids": []},
        "environment": inputs["environment"]["native"], "gpu_uuid": inputs["gpu_uuid"], "engine": native.ENGINE,
        "output_dir": str(output / "unused_reference_actor"), "deadline": deadline, "device_seconds_cap": 1800,
        "max_input_tokens": 512, "max_output_tokens": 2048, "max_calls": 1,
    }, clock=clock)
    identity = checker._verify_identity(deadline)
    return identity, checker._unchanged_files


def _completion(manifest, config, phase, corpus_hash):
    same(manifest["config"], asdict(config), "saved V3 config differs")
    require(manifest["recipe"] == v3.RECIPE and manifest["empty"] is False
            and type(manifest["steps"]) is int and manifest["steps"] == config.max_steps
            and manifest["micro_batches"] == config.max_steps and manifest["nonfinite_batches"] == 0
            and math.isfinite(manifest["final_loss"]), "incomplete/nonfinite V3 fit")
    same(manifest["corpus"], {"file": "corpus.json", "sha256": corpus_hash, "n_items": phase["presentations"],
                             "n_encoded": phase["presentations"], "n_skipped_no_target": 0}, "V3 corpus differs")
    require(all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "V3 truncation")
    same([manifest["tokens"]["target"], manifest["tokens"]["total"]],
         [phase["supervised_tokens"], phase["input_tokens"]], "V3 token counts differ")


def run_phase(inputs_path, inputs_sha256, output, deadline, *, phase="S_A", device="cuda",
              tokenizer_factory=None, base_factory=None, train=None, reference_reader=None,
              state_hash=None, environment_reader=None, clock=time.monotonic):
    """Pinned inputs JSON; injected dependencies label every completion non-native."""
    injected = any(value is not None for value in (tokenizer_factory, base_factory, train, reference_reader,
                                                   state_hash, environment_reader))
    kind = "INJECTED_CPU_TEST" if injected else "NATIVE"
    started = clock()
    native.number(deadline, positive=True)
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
    config = sequence.training_config(phase, model, device=device)
    require(model.is_dir() and not root.exists() and not any(path.is_symlink() for path in (root, *root.parents)), "local model/fresh output required")
    root = root.resolve()
    require(not root.is_relative_to(model.resolve()) and not model.resolve().is_relative_to(root), "output/base overlap")
    material = read_pin(inputs["material"])
    prefix.unseal(material, material["sha256"])
    replay = read_pin(inputs["replay_receipt"])
    require(file_hash(inputs["archive"]["path"]) == inputs["archive"]["sha256"] == prefix.ARCHIVE_SHA256, "source archive pin")
    imported = prefix.build_import(prefix.load_evidence(inputs["archive"]["path"]), replay, replay["sha256"])
    sequence.validate_spec(material["spec"], imported, imported["sha256"])
    parent_phase = sequence.PHASES[phase][0]
    predecessor_pin = inputs.get("predecessor")
    require(bool(predecessor_pin) == (parent_phase is not None), "exact immediate predecessor required")
    parent, prior, before_parent = None, None, None
    if predecessor_pin:
        prior = read_pin(predecessor_pin)
        prefix.unseal(prior, prior["sha256"])
        require(prior["schema"] == SCHEMA + "/completed" and prior["status"] == "COMPLETE"
                and prior["phase"] == parent_phase and prior["kind"] == kind
                and prior["updates"] == sequence.PHASES[parent_phase][1], "wrong/injected predecessor")
        same([prior["material_sha256"], prior["model_binding"], prior["base_state_receipt"]],
             [inputs["material"]["sha256"], inputs["model_binding"], inputs["base_state_receipt"]], "predecessor binding differs")
        parent_root = Path(predecessor_pin["path"]).parent
        require(Path(predecessor_pin["path"]).name == "completed.json" and not (parent_root / "failure.json").exists(), "failed predecessor")
        parent = parent_root / "checkpoint"
        same(prior["checkpoint"], str(parent), "predecessor checkpoint path differs")
        before_parent = v3._warm_inventory(parent_root)
        same({name: value for name, value in before_parent.items() if name != "completed.json"}, prior["files"], "predecessor file drift")
        v3._warm_parent(parent, root / "checkpoint", config)
        require(not root.is_relative_to(parent_root) and not parent_root.is_relative_to(root), "output/predecessor overlap")
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
        same(sequence.export_material(imported, imported["sha256"], tokenizer), material, "export/item/encoding reconstruction drift")
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
        if parent:
            warm = manifest["warm_start"]
            require(warm["initialized_loaded_state_check"] is True and warm["base_frozen"] is True
                    and warm["adapter_count"] == 1 and warm["parent_unchanged"] is True
                    and warm["optimizer_initialization"] == "fresh_per_write" and warm["optimizer_state_restored"] is False
                    and warm["optimizer_initial_state_entries"] == 0 and warm["optimizer_state_saved"] is False
                    and warm["phase_steps"] == config.max_steps, "V3 warm tensor/optimizer receipt required")
            require(bool(warm["source_state"]) and set(warm["source_state"]) == set(warm["initialized_state"]), "full warm tensor receipt missing")
            same(warm["parent_path"], str(parent), "V3 initialized predecessor differs")
            same(warm["parent_files"], v3._warm_inventory(parent), "V3 parent inventory differs")
            same(warm["parent_files_after"], warm["parent_files"], "V3 changed parent files")
            same(warm["cumulative_steps"], (prior.get("warm_start") or {}).get("cumulative_steps", prior["updates"]) + config.max_steps,
                 "V3 cumulative steps differ")
            same(v3._warm_inventory(parent.parent), before_parent, "immutable predecessor changed")
        unchanged()
        same(read_pin(inputs_pin), inputs, "inputs changed")
        same(source_files(), inputs["source_files"], "source drift during fit")
        for name in ("material", "model_binding", "base_state_receipt", "replay_receipt", "archive"):
            require(file_hash(inputs[name]["path"]) == inputs[name]["sha256"], "input changed during fit")
        check()
        completed = prefix.seal({"schema": SCHEMA + "/completed", "status": "COMPLETE", "kind": kind,
            "phase": phase, "parent_phase": parent_phase, "predecessor": predecessor_pin,
            "inputs": inputs_pin, "material_sha256": inputs["material"]["sha256"], "export_sha256": material["sha256"],
            "spec_sha256": material["spec"]["sha256"], "import_sha256": imported["sha256"],
            "items_sha256": selected["items_sha256"], "encoding_sha256": selected["encoding_sha256"],
            "model_binding": inputs["model_binding"], "base_state_receipt": inputs["base_state_receipt"],
            "updates": manifest["steps"], "nonfinite_batches": 0, "checkpoint": str(root / "checkpoint"),
            "warm_start": manifest.get("warm_start"), "base_unchanged": True, "trainable_names": trainable,
            "files": v3._warm_inventory(root), "elapsed_seconds": {"load_and_base_check": loaded - load_started,
                "v3_fit_call": fitted - loaded, "worker": clock() - started},
            "original_status": "FORMATION_FAILED", "limits": sequence.LIMITS, "outer_release_required": True,
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
    parser.add_argument("--phase", choices=tuple(sequence.PHASES), default="S_A")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args(argv)
    result = run_phase(args.inputs, args.inputs_sha256, args.output, args.deadline, phase=args.phase, device=args.device)
    print(prefix.canonical({"status": result["status"], "phase": result["phase"], "sha256": result["sha256"]}).decode())


if __name__ == "__main__":
    main()
