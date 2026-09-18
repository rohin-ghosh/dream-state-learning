"""Injected orchestration and real tiny-model CPU warm-initialization tests."""

import copy
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_event_sequence_v2_fit as fit
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
        self.material = self.original_export(self.imported, self.imported["sha256"], SyntheticTokenizer(), learner_seed=1)
        binding = self.store("binding.json", {"SYNTHETIC_ONLY": True})
        self.inputs = {"schema": fit.SCHEMA + "/inputs", "model_path": str(self.model),
            "learner_seed": 1, "gpu_uuid": "GPU-SYNTHETIC-NOT-USED", "source_files": fit.source_files(), "environment": self.env,
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

    def run_fit(self, phase="A200", output=None, **kwargs):
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
        self.assertEqual(result["updates"], 200)
        self.assertEqual(len(self.calls), 1)
        self.assertIsNone(self.calls[0][2])
        self.assertEqual(self.calls[0][0], self.material["phases"]["A200"]["items"])
        self.assertEqual(result["import_sha256"], self.imported["sha256"])
        self.assertEqual(result["items_sha256"], self.material["phases"]["A200"]["items_sha256"])
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
        altered["phases"]["A200"]["items"][0]["spans"][1][0] += "fabricated"
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
        with patch.object(fit, "run_phase", return_value={"status": "COMPLETE", "phase": "A200", "sha256": "a" * 64}) as run:
            fit.main(["--inputs", "/inputs.json", "--inputs-sha256", "b" * 64, "--output", "/fresh", "--deadline", "200"])
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.kwargs, {"phase": "A200", "device": "cuda"})

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
            self.run_fit("REPLAY400")
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


    def test_seed_bound_config_and_v1_globals_unchanged(self):
        original_sequence, original_schema = fit.v1.sequence, fit.v1.SCHEMA
        result = self.run_fit()
        self.assertEqual(result["learner_seed"], 1)
        self.assertEqual(self.calls[0][1]["seed"], 1)
        self.assertIs(fit.v1.sequence, original_sequence)
        self.assertEqual(fit.v1.SCHEMA, original_schema)
        self.assertFalse(result["descendants_enabled"])

    def test_seed_drift_and_invalid_seed_refused_before_load(self):
        for seed in (0, 2, True, "1", 3):
            with self.subTest(seed=seed):
                self.inputs["learner_seed"] = seed
                with self.assertRaisesRegex(ValueError, "seed"):
                    self.run_fit()
        self.loader.assert_not_called()

    def parent(self):
        self.run_fit()
        self.parent_root = self.output
        self.inputs["predecessor"] = self.pin(self.output / "completed.json")

    def validate_parent(self, phase="REPLAY400"):
        config = fit.sequence.training_config(phase, self.model, learner_seed=1, device="cpu")
        return fit.validate_predecessor(self.inputs, self.material, phase, self.root / "child", config, "INJECTED_CPU_TEST")

    def test_exact_a200_parent_inventory_for_all_warm_branches(self):
        self.parent()
        before = fit.v3._warm_inventory(self.parent_root)
        for phase in ("REPLAY400", "B200_NEW_DOSE", "B400_FIXED_WORK"):
            parent, prior, inventory = self.validate_parent(phase)
            self.assertEqual(parent, self.parent_root / "checkpoint")
            self.assertEqual(prior["phase"], "A200")
            self.assertEqual(inventory, before)
        self.assertEqual(fit.v3._warm_inventory(self.parent_root), before)
        self.assertEqual(len(self.calls), 1)

    def test_postfit_predecessor_check_preserves_existing_child_checkpoint(self):
        self.parent()
        child = self.root / 'child/checkpoint'
        child.mkdir(parents=True)
        marker = child / 'immutable_checkpoint_marker'
        marker.write_bytes(b'EXISTING_CHILD')
        before = fit.v3._warm_inventory(self.parent_root)
        with patch.object(fit.v3, '_warm_parent', side_effect=AssertionError('read-only validation prepared an output')):
            self.validate_parent()
        self.assertEqual(marker.read_bytes(), b'EXISTING_CHILD')
        self.assertEqual(fit.v3._warm_inventory(self.parent_root), before)
        self.assertFalse((self.root / 'child/unused_predecessor_validation').exists())

    def test_prefit_predecessor_check_rejects_existing_actual_checkpoint(self):
        self.parent()
        child = self.root / 'child'
        config = fit.sequence.training_config('REPLAY400', self.model, learner_seed=1, device='cpu')
        fit.validate_predecessor_for_write(self.inputs, self.material, 'REPLAY400', child, config, 'INJECTED_CPU_TEST')
        self.assertFalse(child.exists())
        (child / 'checkpoint').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'output must be fresh'):
            fit.validate_predecessor_for_write(self.inputs, self.material, 'REPLAY400', child, config, 'INJECTED_CPU_TEST')

    def test_parent_drift_and_sa40_seed_spec_material_refused(self):
        self.parent()
        path = self.parent_root / "completed.json"
        original = fit.read_pin(self.inputs["predecessor"])
        for key, value in (("phase", "S_A"), ("phase", "S_A40"), ("updates", 40),
                           ("schema", fit.v1.SCHEMA + "/completed"), ("learner_seed", 2),
                           ("spec_sha256", "d" * 64), ("material_sha256", "d" * 64),
                           ("export_sha256", "d" * 64), ("kind", "NATIVE")):
            changed = {**original, key: value}
            changed.pop("sha256")
            path.write_bytes(fit.prefix.canonical(fit.prefix.seal(changed)))
            self.inputs["predecessor"] = self.pin(path)
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.validate_parent()
        path.write_bytes(fit.prefix.canonical(original))
        self.inputs["predecessor"] = self.pin(path)
        (self.parent_root / "checkpoint/adapter_model.safetensors").write_bytes(b"DRIFT")
        with self.assertRaisesRegex(ValueError, "file drift"):
            self.validate_parent()

    def test_parent_config_seed_drift_even_after_inventory_reseal(self):
        self.parent()
        config_path = self.parent_root / "config.json"
        config = json.loads(config_path.read_text())
        config["seed"] = 0
        config_path.write_bytes(fit.prefix.canonical(config))
        path = self.parent_root / "completed.json"
        prior = fit.read_pin(self.inputs["predecessor"])
        prior.pop("sha256")
        prior["files"] = {name: value for name, value in fit.v3._warm_inventory(self.parent_root).items() if name != "completed.json"}
        path.write_bytes(fit.prefix.canonical(fit.prefix.seal(prior)))
        self.inputs["predecessor"] = self.pin(path)
        with self.assertRaisesRegex(ValueError, "config/seed drift"):
            self.validate_parent()

    def test_cold_phases_require_c0_and_warm_has_no_missing_parent_fallback(self):
        self.assertEqual(self.validate_parent("CLEAN_CUM600"), (None, None, None))
        with self.assertRaisesRegex(ValueError, "predecessor"):
            self.validate_parent()
        self.parent()
        for phase in ("A200", "CLEAN_CUM600"):
            with self.assertRaisesRegex(ValueError, "cold phases require C0"):
                self.validate_parent(phase)

    def test_descendants_blocked_despite_boolean_or_unvalidated_receipt(self):
        self.parent()
        for phase in ("REPLAY400", "B200_NEW_DOSE", "B400_FIXED_WORK", "CLEAN_CUM600"):
            for assertion in ({"acquisition_passed": True}, {"acquisition_receipt": {"status": "PASS"}}):
                with self.subTest(phase=phase), self.assertRaisesRegex(ValueError, "acquisition"):
                    fit.require_acquisition({**self.inputs, **assertion}, self.material, phase)
        with self.assertRaisesRegex(ValueError, "acquisition"):
            self.run_fit("REPLAY400")
        self.assertEqual(len(self.calls), 1)

    def test_observed_gate_not_boolean_and_exact_measured_parent_required(self):
        self.parent()
        request = {"path": "/tmp/synthetic-acquisition.json", "sha256": "a" * 64}
        inputs = {**self.inputs, "acquisition_receipt": request}
        evidence = {"observed_gate": True, "a200_fit_receipt": inputs["predecessor"]}
        with patch.object(fit.acquisition, "validate", return_value=evidence) as validator:
            self.assertEqual(fit.require_acquisition(inputs, self.material, "REPLAY400", kind="INJECTED_CPU_TEST"), evidence)
            validator.assert_called_once_with(request, self.material, inputs, expected_kind="INJECTED_CPU_TEST")
        for evidence in ({"observed_gate": False}, {"observed_gate": True, "a200_fit_receipt": {"path": "wrong", "sha256": "a" * 64}}):
            with patch.object(fit.acquisition, "validate", return_value=evidence), self.assertRaises(ValueError):
                fit.require_acquisition(inputs, self.material, "REPLAY400")

    def test_no_a400_fallback_and_bounded_deadline(self):
        with self.assertRaisesRegex(ValueError, "only v2 phases"):
            self.run_fit("A400")
        with self.assertRaisesRegex(ValueError, "bounded worker deadline"):
            fit.run_phase("/unused", "a" * 64, "/unused", 2001, clock=self.clock)
        self.loader.assert_not_called()

    def test_full_parent_tensor_inventory_and_drift(self):
        names = ["layer.lora_A.default.weight", "layer.lora_B.default.weight"]
        tensors = {name.replace(".default", ""): {"sha256": "a" * 64, "shape": [8, 8], "dtype": "torch.float32"} for name in names}
        receipt = {"source_state": copy.deepcopy(tensors), "initialized_state": copy.deepcopy(tensors),
                   "dtype_conversions": {}, "initialized_loaded_state_check": True}
        fit.validate_warm_tensors(receipt, names)
        receipt["initialized_state"]["layer.lora_B.weight"]["sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "initialization drift"):
            fit.validate_warm_tensors(receipt, names)
        receipt["source_state"].pop("layer.lora_B.weight")
        with self.assertRaisesRegex(ValueError, "coverage"):
            fit.validate_warm_tensors(receipt, names)


class TorchConversionValidationTests(unittest.TestCase):
    """Real CPU tensor arithmetic/serialization, not initializer-path evidence."""

    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec("torch") is None:
            raise unittest.SkipTest("tensor conversion regression requires local CPU torch")

    def receipt(self):
        import torch
        temporary = tempfile.TemporaryDirectory(prefix="pcfl-v2-conversion-")
        self.addCleanup(temporary.cleanup)
        parent = Path(temporary.name)
        tensors = {"layer.lora_A.weight": torch.arange(8, dtype=torch.bfloat16).reshape(2, 4),
                   "layer.lora_B.weight": torch.arange(8, dtype=torch.float32).reshape(4, 2)}
        torch.save(tensors, parent / "adapter_model.bin")
        converted = {name: tensor.to(torch.float32) for name, tensor in tensors.items()}
        return {"source_state": fit.v3._warm_state_inventory(tensors),
                "initialized_state": fit.v3._warm_state_inventory(converted),
                "dtype_conversions": {name: {"source": str(tensor.dtype), "initialized": str(converted[name].dtype)}
                                      for name, tensor in tensors.items() if tensor.dtype != converted[name].dtype},
                "initialized_loaded_state_check": True, "parent_path": str(parent),
                "parent_files": fit.v3._warm_inventory(parent)}, [name.replace(".weight", ".default.weight") for name in tensors]

    def test_partial_conversion_recomputed_from_real_parent_tensor_bytes(self):
        receipt, names = self.receipt()
        fit.validate_warm_tensors(receipt, names)
        self.assertEqual(len(receipt["dtype_conversions"]), 1)
        self.assertEqual(fit.v3._warm_inventory(receipt["parent_path"]), receipt["parent_files"])

    def test_sparse_map_and_converted_hash_source_shape_dtype_or_flag_drift_rejected(self):
        receipt, names = self.receipt()
        changed, unchanged = "layer.lora_A.weight", "layer.lora_B.weight"
        mutations = [lambda value: value["dtype_conversions"].pop(changed),
                     lambda value: value["dtype_conversions"].update({unchanged: {"source": "torch.float32", "initialized": "torch.float32"}}),
                     lambda value: value["dtype_conversions"][changed].update(source="torch.float16"),
                     lambda value: value["initialized_state"][changed].update(sha256="0" * 64),
                     lambda value: value["source_state"][changed].update(sha256="0" * 64),
                     lambda value: value["initialized_state"][changed].update(shape=[1, 8]),
                     lambda value: value["initialized_state"][changed].update(dtype="torch.float64"),
                     lambda value: value["initialized_state"].pop(unchanged),
                     lambda value: value.update(initialized_loaded_state_check=False),
                     lambda value: value.update(initialized_loaded_state_check=1)]
        for index, mutate in enumerate(mutations):
            altered = copy.deepcopy(receipt)
            mutate(altered)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                fit.validate_warm_tensors(altered, names)
        (Path(receipt["parent_path"]) / "adapter_model.bin").write_bytes(b"drift")
        with self.assertRaisesRegex(ValueError, "inventory drift"):
            fit.validate_warm_tensors(receipt, names)


class RealWarmInitializationTests(unittest.TestCase):
    """Real CPU Qwen2/PEFT initialization and serialization; no mocked loader."""

    @classmethod
    def setUpClass(cls):
        missing = [name for name in ("torch", "peft", "transformers", "safetensors")
                   if importlib.util.find_spec(name) is None]
        if missing:
            raise unittest.SkipTest("real warm initialization requires local dependencies: " + ", ".join(missing))

    def initialize(self, converted_count=0):
        import torch
        from peft import get_peft_model, get_peft_model_state_dict
        from safetensors.torch import load_file, save_file
        from transformers import Qwen2Config, Qwen2ForCausalLM

        temporary = tempfile.TemporaryDirectory(prefix="pcfl-v2-real-warm-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        model_path = root / "tiny-local-qwen2"
        model_path.mkdir()
        config = fit.v3.TrainConfig(model=str(model_path), rank=2, alpha=4, dropout=.05,
                                    target_modules=["q_proj", "v_proj"], device="cpu", dtype="fp32")

        def base():
            model_config = Qwen2Config(vocab_size=32, hidden_size=16, intermediate_size=32,
                                      num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1)
            model_config._attn_implementation = "eager"
            model_config._name_or_path = config.model
            return Qwen2ForCausalLM(model_config).to(device="cpu", dtype=torch.float32)

        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(17)
            parent_model = get_peft_model(base(), fit.v3.lora_config(config, 1))
            with torch.no_grad():
                for name, tensor in parent_model.named_parameters():
                    if "lora_" in name:
                        tensor.uniform_(-.25, .25)
            parent = root / "parent"
            parent_model.save_pretrained(parent, safe_serialization=True, save_embedding_layers=False)
            weights = parent / "adapter_model.safetensors"
            saved = load_file(str(weights), device="cpu")
            changed = set(sorted(saved)[:converted_count])
            if changed:
                saved = {name: tensor.to(torch.bfloat16) if name in changed else tensor for name, tensor in saved.items()}
                save_file(saved, str(weights))
            warm = {"parent": parent, "weights": weights, "parent_files": fit.v3._warm_inventory(parent),
                    "manifest": {"lora": {"n_layers": 1}},
                    "saved": json.loads((parent / "adapter_config.json").read_text()), "cumulative_steps": 0}
            cold = base()
            original_base = [(tensor, tensor.detach().clone()) for tensor in cold.parameters()]
            model, receipt = fit.v3._warm_initialize(cold, config, warm)
        loaded = get_peft_model_state_dict(model, save_embedding_layers=False)
        self.assertEqual(set(receipt["dtype_conversions"]), changed)
        self.assertIs(receipt["initialized_loaded_state_check"], True)
        self.assertTrue(all(tensor.device.type == "cpu" for tensor in model.parameters()))
        self.assertTrue(all(torch.equal(loaded[name].cpu(), saved[name].to(loaded[name].dtype)) for name in saved))
        self.assertTrue(all(not tensor.requires_grad and torch.equal(tensor, before) for tensor, before in original_base))
        self.assertEqual(fit.v3._warm_inventory(parent), warm["parent_files"])
        caller_names = [name for name, tensor in cold.named_parameters() if tensor.requires_grad]
        self.assertTrue(caller_names)
        self.assertTrue(all(not name.startswith("base_model.model.") for name in caller_names))
        return receipt, caller_names

    def test_actual_same_dtype_receipt_has_empty_conversion_map(self):
        receipt, names = self.initialize()
        self.assertEqual(receipt["dtype_conversions"], {})
        fit.validate_warm_tensors(receipt, names)

    def test_actual_wrapped_and_unwrapped_caller_names_are_same_tensors(self):
        receipt, names = self.initialize()
        fit.validate_warm_tensors(receipt, names)
        fit.validate_warm_tensors(receipt, receipt["trainable_names"])
        with self.assertRaisesRegex(ValueError, "coverage"):
            fit.validate_warm_tensors(receipt, names[:-1])
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            fit.validate_warm_tensors(receipt, names + ["base_model.model." + names[0]])

    def test_actual_partial_and_full_dtype_conversion_receipts(self):
        for count in (1, 4):
            with self.subTest(converted_count=count):
                receipt, names = self.initialize(count)
                self.assertEqual(len(receipt["dtype_conversions"]), count)
                fit.validate_warm_tensors(receipt, names)

    def test_actual_receipt_missing_extra_and_wrong_conversion_entries_rejected(self):
        receipt, names = self.initialize(1)
        changed = next(iter(receipt["dtype_conversions"]))
        unchanged = next(name for name in receipt["source_state"] if name != changed)
        mutations = [lambda value: value["dtype_conversions"].pop(changed),
                     lambda value: value["dtype_conversions"].update({unchanged: {"source": "torch.float32", "initialized": "torch.float32"}}),
                     lambda value: value["dtype_conversions"][changed].update(source="torch.float16")]
        for mutate in mutations:
            altered = copy.deepcopy(receipt)
            mutate(altered)
            with self.assertRaisesRegex(ValueError, "conversion"):
                fit.validate_warm_tensors(altered, names)

    def test_actual_receipt_tensor_hash_shape_dtype_coverage_and_flag_drift_rejected(self):
        for count in (0, 1):
            receipt, names = self.initialize(count)
            selected = next(iter(receipt["dtype_conversions"])) if count else next(iter(receipt["source_state"]))
            mutations = [lambda value: value["source_state"].pop(selected),
                         lambda value: value["initialized_state"].pop(selected),
                         lambda value: value["source_state"][selected].update(sha256="0" * 64),
                         lambda value: value["initialized_state"][selected].update(sha256="0" * 64),
                         lambda value: value["initialized_state"][selected].update(shape=[1, 1]),
                         lambda value: value["initialized_state"][selected].update(dtype="torch.float64"),
                         lambda value: value.update(initialized_loaded_state_check=False),
                         lambda value: value.update(initialized_loaded_state_check=1)]
            for index, mutate in enumerate(mutations):
                altered = copy.deepcopy(receipt)
                mutate(altered)
                with self.subTest(converted_count=count, mutation=index), self.assertRaises(ValueError):
                    fit.validate_warm_tensors(altered, names)
