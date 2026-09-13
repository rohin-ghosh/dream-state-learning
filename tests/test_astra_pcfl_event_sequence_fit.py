"""Injected CPU orchestration only: no model, tensors, GPU, or native training."""

import copy
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_event_sequence_fit as fit
from test_pcfl_event_sequence import SyntheticTokenizer, synthetic_import


class Parameter:
    dtype = "torch.bfloat16"

    def __init__(self, value):
        self.value, self.requires_grad = value, True

    def requires_grad_(self, enabled):
        self.requires_grad = enabled

    def is_floating_point(self):
        return True


class SyntheticBase:
    def __init__(self):
        self.weights = {"base.weight": Parameter("SYNTHETIC_BASE")}

    def named_parameters(self, **kwargs):
        return self.weights.items()

    def named_buffers(self, **kwargs):
        return []

    def parameters(self):
        return self.weights.values()

    def state_dict(self):
        return dict(self.weights)


def synthetic_hash(values):
    return fit.prefix.digest({name: parameter.value for name, parameter in values.items()})


class FitTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.model = self.root / "model"
        self.model.mkdir()
        self.base_hash = synthetic_hash(SyntheticBase().state_dict())
        imported = synthetic_import()
        imported.pop("sha256")
        imported["evidence"] = {"files": {"manifest.json": fit.prefix._record(fit.prefix.canonical(
            {"binding": {"base_state_sha256": self.base_hash}}))}}
        self.imported = fit.prefix.seal(imported)
        self.env = {"native": {"python": "/SYNTHETIC/python3.12", "version": "SYNTHETIC Python 3.12",
                               "packages": {name: "SYNTHETIC" for name in fit.native.PACKAGES}},
                    "peft_version": "SYNTHETIC"}
        self.clock = Mock(return_value=100.0)
        self.model_files = {"SYNTHETIC_ONLY": "a" * 64}
        self.original_export = fit.sequence.export_material
        self.patch(patch.dict(os.environ, {key: "1" for key in fit.OFFLINE}))
        self.patch(patch.object(fit.prefix, "validate_import", side_effect=lambda data, expected: fit.prefix.unseal(data, expected)))
        self.patch(patch.object(fit.prefix, "build_import", return_value=self.imported))
        self.patch(patch.object(fit.prefix, "load_evidence", return_value={"SYNTHETIC_ONLY": True}))
        self.patch(patch.object(fit.prefix, "verify_tokenizer", return_value={"status": "SYNTHETIC_NOT_NATIVE"}))
        archive = self.root / "archive.tar"
        archive.write_bytes(b"SYNTHETIC_NOT_ARCHIVE")
        self.patch(patch.object(fit.prefix, "ARCHIVE_SHA256", fit.file_hash(archive)))
        self.material = self.original_export(self.imported, self.imported["sha256"], SyntheticTokenizer())
        binding = self.store("binding.json", {"SYNTHETIC_ONLY": True})
        self.inputs = {"schema": fit.SCHEMA + "/inputs", "model_path": str(self.model),
            "gpu_uuid": "GPU-SYNTHETIC-NOT-USED", "source_files": fit.source_files(), "environment": self.env,
            "material": self.store("material.json", self.material), "model_binding": binding,
            "archive": self.pin(archive), "replay_receipt": self.store("replay.json", fit.prefix.seal({"SYNTHETIC": True})),
            "base_state_receipt": self.store("cpu.json", {"schema": "pcfl.own_write.cpu_base_state.v1", "status": "COMPLETE",
                "device": "cpu", "dtype": "bfloat16", "base_state_sha256": self.base_hash,
                "model_binding_sha256": binding["sha256"], "model_files": self.model_files, "environment": self.env}),
            "predecessor": None}
        self.calls, self.counter = [], 0
        self.mutate = lambda manifest, base, output, parent: None
        self.unchanged = Mock()
        self.loader = Mock(side_effect=lambda config: SyntheticBase())

    def patch(self, context):
        value = context.start()
        self.addCleanup(context.stop)
        return value

    def pin(self, path):
        return {"path": str(path), "sha256": fit.file_hash(path)}

    def store(self, name, value):
        path = self.root / name
        path.write_bytes(fit.prefix.canonical(value) + b"\n")
        return self.pin(path)

    def trainer(self, items, tokenizer, base, config, output, *, corpus_sha, corpus_name, init_adapter):
        self.calls.append((copy.deepcopy(items), asdict(config), init_adapter))
        selected = next(phase for phase in self.material["phases"].values()
                        if phase["items"] == items)
        self.assertTrue(all(not parameter.requires_grad for parameter in base.parameters()))
        base.weights["layer.lora_A.default.weight"] = Parameter("SYNTHETIC_A")
        base.weights["layer.lora_B.default.weight"] = Parameter("SYNTHETIC_B")
        manifest = {"recipe": fit.v3.RECIPE, "config": asdict(config), "base_model": config.model,
            "empty": False, "steps": config.max_steps, "micro_batches": config.max_steps,
            "nonfinite_batches": 0, "final_loss": 1.0, "lora": {"n_layers": 1},
            "corpus": {"file": corpus_name, "sha256": corpus_sha, "n_items": len(items),
                       "n_encoded": len(items), "n_skipped_no_target": 0},
            "truncation": dict.fromkeys(("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split"), 0),
            "tokens": {"target": selected["supervised_tokens"], "total": selected["input_tokens"]}}
        if init_adapter:
            parent = Path(init_adapter)
            before = fit.v3._warm_inventory(parent)
            previous = json.loads((parent / "train_manifest.json").read_text())
            tensor = {"layer.lora_A.weight": {"sha256": "c" * 64, "dtype": "SYNTHETIC", "shape": [1, 1]}}
            manifest["warm_start"] = {"initialized_loaded_state_check": True, "base_frozen": True,
                "adapter_count": 1, "parent_unchanged": True, "optimizer_initialization": "fresh_per_write",
                "optimizer_initial_state_entries": 0, "optimizer_state_restored": False, "optimizer_state_saved": False,
                "phase_steps": config.max_steps, "source_state": tensor, "initialized_state": tensor,
                "parent_path": str(parent), "parent_files": before, "parent_files_after": before,
                "cumulative_steps": previous["steps"] + config.max_steps}
        destination = Path(output)
        destination.mkdir()
        fit.write(destination / "adapter_config.json", {"base_model_name_or_path": config.model})
        (destination / "adapter_model.safetensors").write_bytes(b"SYNTHETIC_NOT_TENSORS")
        (destination / "DONE").write_text("ok\n")
        self.mutate(manifest, base, destination, init_adapter)
        (destination / "train_manifest.json").write_text(json.dumps(manifest, default=str))
        return manifest

    def run_fit(self, phase="S_A", output=None, **kwargs):
        self.counter += 1
        pin = self.store(f"inputs{self.counter}.json", self.inputs)
        self.output = output or self.root / f"fit{self.counter}"
        options = dict(phase=phase, device="cpu", tokenizer_factory=lambda config: SyntheticTokenizer(),
            base_factory=self.loader, train=self.trainer, state_hash=synthetic_hash,
            environment_reader=lambda: self.env, clock=self.clock,
            reference_reader=lambda *args: ({"model_files": self.model_files}, self.unchanged))
        return fit.run_phase(pin["path"], pin["sha256"], self.output, 200.0, **{**options, **kwargs})

    def test_sa_only_fixed_config_and_saved_custody(self):
        result = self.run_fit()
        self.assertEqual(result["kind"], "INJECTED_CPU_TEST")
        self.assertEqual(result["updates"], 40)
        self.assertEqual(len(self.calls), 1)
        self.assertIsNone(self.calls[0][2])
        self.assertEqual(self.calls[0][0], self.material["phases"]["S_A"]["items"])
        self.assertEqual(result["import_sha256"], self.imported["sha256"])
        self.assertEqual(result["items_sha256"], self.material["phases"]["S_A"]["items_sha256"])
        self.assertEqual(result["files"], {key: value for key, value in fit.v3._warm_inventory(self.output).items() if key != "completed.json"})
        self.assertFalse(result["gpu_released"])
        self.assertFalse(result["automatic_promotion"])
        self.assertFalse((self.output / "unused_reference_actor").exists())
        self.unchanged.assert_called_once()

    def test_trainer_string_subclass_version_matches_saved_json(self):
        class Version(str):
            pass
        self.mutate = lambda manifest, base, output, parent: manifest.update(versions={"torch": Version("2.13.0+cu130")})
        result = self.run_fit()
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(json.loads((self.output / "checkpoint/train_manifest.json").read_text())["versions"],
                         {"torch": "2.13.0+cu130"})

    def test_manifest_json_never_stringifies_unknown_objects_or_nonfinite_numbers(self):
        with self.assertRaises(TypeError):
            fit.manifest_json({"unknown": object()})
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.assertRaises(ValueError):
                fit.manifest_json({"number": value})

    def test_cpu_reference_requires_nested_native_and_peft_environment(self):
        cpu = fit.read_pin(self.inputs["base_state_receipt"])
        self.assertEqual(set(cpu["environment"]), {"native", "peft_version"})
        self.assertEqual(set(cpu["environment"]["native"]), {"python", "version", "packages"})
        with patch.object(fit.native, "environment_identity", return_value=self.env["native"]), \
                patch.object(fit.importlib.metadata, "version", return_value=self.env["peft_version"]):
            self.assertEqual(fit.environment(), cpu["environment"])
        self.run_fit()
        changed_native = copy.deepcopy(self.env)
        changed_native["native"]["packages"]["torch"] = "SYNTHETIC_DIFFERENT"
        changed_peft = {**self.env, "peft_version": "SYNTHETIC_DIFFERENT"}
        for altered in (self.env["native"], changed_native, changed_peft):
            self.inputs["base_state_receipt"] = self.store("cpu.json", {**cpu, "environment": altered})
            with self.assertRaisesRegex(ValueError, "CPU model/environment reference"):
                self.run_fit()
        self.assertEqual(self.loader.call_count, 1)

    def test_warm_forks_same_completed_immediate_adapter(self):
        parent = self.run_fit()
        parent_root = self.output
        parent_files = fit.v3._warm_inventory(parent_root)
        self.inputs["predecessor"] = self.pin(parent_root / "completed.json")
        for phase in ("SEQ_REPLAY", "SEQ_NEW_ONLY"):
            result = self.run_fit(phase)
            self.assertEqual(result["warm_start"]["cumulative_steps"], 120)
            self.assertEqual(self.calls[-1][2], parent["checkpoint"])
        self.assertEqual(fit.v3._warm_inventory(parent_root), parent_files)
        self.inputs["predecessor"] = None
        self.run_fit("ALL_AVAILABLE_1")
        self.inputs["predecessor"] = self.pin(self.output / "completed.json")
        self.assertEqual(self.run_fit("ALL_AVAILABLE_2")["updates"], 80)

    def test_wrong_missing_or_unexpected_parent_rejected_before_load(self):
        with self.assertRaisesRegex(ValueError, "predecessor"):
            self.run_fit("SEQ_REPLAY")
        self.loader.assert_not_called()
        self.run_fit("FRESH_MIX")
        self.inputs["predecessor"] = self.pin(self.output / "completed.json")
        for phase in ("S_A", "SEQ_REPLAY"):
            with self.assertRaisesRegex(ValueError, "predecessor"):
                self.run_fit(phase)

    def test_existing_output_never_modified(self):
        self.run_fit()
        output = self.output
        before = fit.v3._warm_inventory(output)
        with self.assertRaisesRegex(ValueError, "fresh output"):
            self.run_fit(output=output)
        self.assertEqual(fit.v3._warm_inventory(output), before)

    def test_tampered_export_or_source_rejected_before_fit(self):
        self.inputs["source_files"][str(Path(fit.__file__).resolve())] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source pins"):
            self.run_fit()
        self.inputs["source_files"] = fit.source_files()
        altered = copy.deepcopy(self.material)
        altered.pop("sha256")
        altered["phases"]["S_A"]["items"][0]["spans"][1][0] += "fabricated"
        self.inputs["material"] = self.store("badmaterial.json", fit.prefix.seal(altered))
        with self.assertRaisesRegex(ValueError, "reconstruction"):
            self.run_fit()
        self.assertEqual(self.calls, [])

    def test_steps_nonfinite_mask_counts_and_base_mutation_fail_closed(self):
        changes = [lambda manifest, base, output, parent: manifest.update(steps=39),
                   lambda manifest, base, output, parent: manifest.update(nonfinite_batches=1),
                   lambda manifest, base, output, parent: manifest["truncation"].update(context_tokens_dropped=1),
                   lambda manifest, base, output, parent: manifest["tokens"].update(target=0),
                   lambda manifest, base, output, parent: setattr(base.weights["base.weight"], "value", "MUTATED"),
                   lambda manifest, base, output, parent: base.weights["base.weight"].requires_grad_(True),
                   lambda manifest, base, output, parent: (output / "DONE").unlink()]
        for change in changes:
            self.mutate = change
            with self.assertRaises(ValueError):
                self.run_fit()
            self.assertTrue((self.output / "failure.json").exists())
            self.assertFalse((self.output / "completed.json").exists())

    def test_warm_invalid_or_mutated_parent_and_receipt_fail(self):
        self.run_fit()
        parent_root = self.output
        self.inputs["predecessor"] = self.pin(parent_root / "completed.json")
        self.mutate = lambda manifest, base, output, parent: manifest["warm_start"].update(initialized_loaded_state_check=False)
        with self.assertRaisesRegex(ValueError, "warm tensor"):
            self.run_fit("SEQ_REPLAY")
        self.mutate = lambda manifest, base, output, parent: (Path(parent) / "DONE").write_text("changed")
        with self.assertRaisesRegex(ValueError, "inventory|predecessor|parent"):
            self.run_fit("SEQ_REPLAY")
        loads = self.loader.call_count
        with self.assertRaisesRegex(ValueError, "file drift"):
            self.run_fit("SEQ_REPLAY")
        self.assertEqual(self.loader.call_count, loads)

    def test_deadline_around_load_and_fit(self):
        self.clock.return_value = 200.0
        with self.assertRaisesRegex(ValueError, "deadline"):
            self.run_fit()
        self.loader.assert_not_called()
        self.clock.return_value = 100.0
        self.loader.side_effect = lambda config: (setattr(self.clock, "return_value", 200.0) or SyntheticBase())
        with self.assertRaisesRegex(ValueError, "deadline"):
            self.run_fit()
        self.assertEqual(self.calls, [])
        self.loader.side_effect = lambda config: SyntheticBase()
        self.clock.return_value = 100.0
        self.mutate = lambda *args: setattr(self.clock, "return_value", 200.0)
        with self.assertRaisesRegex(ValueError, "deadline"):
            self.run_fit()
        self.assertFalse((self.output / "completed.json").exists())

    def test_default_cli_selects_one_sa(self):
        with patch.object(fit, "run_phase", return_value={"status": "COMPLETE", "phase": "S_A", "sha256": "a" * 64}) as run:
            fit.main(["--inputs", "/inputs.json", "--inputs-sha256", "b" * 64, "--output", "/fresh", "--deadline", "200"])
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.kwargs, {"phase": "S_A", "device": "cuda"})

    def test_incomplete_v3_parent_not_accepted_after_outer_reseal(self):
        self.run_fit()
        parent_root = self.output
        (parent_root / "checkpoint/DONE").unlink()
        prior = json.loads((parent_root / "completed.json").read_text())
        prior.pop("sha256")
        prior["files"] = {key: value for key, value in fit.v3._warm_inventory(parent_root).items() if key != "completed.json"}
        (parent_root / "completed.json").write_bytes(fit.prefix.canonical(fit.prefix.seal(prior)))
        self.inputs["predecessor"] = self.pin(parent_root / "completed.json")
        with self.assertRaisesRegex(ValueError, "parent is incomplete"):
            self.run_fit("SEQ_REPLAY")
        self.assertEqual(self.loader.call_count, 1)

    def test_wrong_loaded_base_and_pre_adapted_base_rejected(self):
        def wrong(config):
            base = SyntheticBase()
            base.weights["base.weight"].value = "WRONG_BASE"
            return base
        self.loader.side_effect = wrong
        with self.assertRaisesRegex(ValueError, "C0 tensor identity"):
            self.run_fit()
        self.loader.side_effect = lambda config: SimpleNamespace(peft_config={})
        with self.assertRaisesRegex(ValueError, "unadapted"):
            self.run_fit()
        self.assertEqual(self.calls, [])


class LoaderReferenceTests(unittest.TestCase):
    def test_existing_v3_loading_arguments_are_offline_for_fresh_and_warm(self):
        tokenizer = SimpleNamespace(pad_token=None, eos_token="SYNTHETIC_EOS")
        auto_tokenizer = SimpleNamespace(from_pretrained=Mock(return_value=tokenizer))
        auto_model = SimpleNamespace(from_pretrained=Mock(return_value="SYNTHETIC_NOT_MODEL"))
        with patch.dict(sys.modules, {"transformers": SimpleNamespace(AutoTokenizer=auto_tokenizer, AutoModelForCausalLM=auto_model)}), \
                patch.object(fit.v3, "_torch_dtype", return_value="SYNTHETIC_DTYPE"):
            config = fit.sequence.training_config("S_A", "/synthetic/model", device="cpu")
            self.assertIs(fit._tokenizer(config), tokenizer)
            self.assertEqual(fit._base(config), "SYNTHETIC_NOT_MODEL")
        auto_tokenizer.from_pretrained.assert_called_once_with("/synthetic/model", local_files_only=True, trust_remote_code=False)
        auto_model.from_pretrained.assert_called_once_with("/synthetic/model", torch_dtype="SYNTHETIC_DTYPE",
                                                           local_files_only=True, trust_remote_code=False, device_map=None)
        self.assertEqual(tokenizer.pad_token, "SYNTHETIC_EOS")

    def test_existing_native_file_reference_checker_never_starts_engine(self):
        from test_astra_pcfl_native_actor import ActorTests
        fixture = ActorTests("test_constructor_and_unused_close_are_lazy")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        inputs = {"model_path": str(fixture.model), "model_binding": fixture.config["model_binding"],
                  "source_files": fixture.config["source_files"], "gpu_uuid": "GPU-SYNTHETIC-NOT-LAUNCHED",
                  "environment": {"native": fixture.environment}}
        material = {"tokenizer_receipt": {"tokenizer_files": fixture.config["tokenizer_files"],
                                          "chat_template_sha256": fixture.config["chat_template_sha256"]}}
        real_actor = fit.native.NativeActor
        def checker(config, **kwargs):
            return real_actor(config, environment_reader=lambda: fixture.environment, **kwargs)
        with patch.object(fit.native, "NativeActor", side_effect=checker), \
                patch.object(fit.native, "_native_loader", side_effect=AssertionError("no engine")) as loader:
            identity, unchanged = fit._reference(inputs, material, fixture.root / "unused", 100, fixture.clock)
            unchanged()
            self.assertEqual(len(identity["model_files"]), 14)
            (fixture.model / "config.json").write_text("tamper")
            with self.assertRaises(ValueError):
                unchanged()
            loader.assert_not_called()
        self.assertFalse((fixture.root / "unused").exists())


if __name__ == "__main__":
    unittest.main()
