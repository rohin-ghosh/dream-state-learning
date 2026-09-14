"""Focused source tests; synthetic branches are not native qualification.

Run only this module with unittest. Optional real torch and tiny Qwen/PEFT CPU
fixtures use installed packages and config-built random weights, never downloads.
Even those fixtures do not qualify the pinned base, runtime or preparation.
"""

from copy import deepcopy
from dataclasses import FrozenInstanceError, dataclass
from hashlib import sha256
import importlib.util
import math
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a_initial_adapter as source
from organism_v6 import composition_birth_stage2a_training as training


HAS_TORCH = importlib.util.find_spec("torch") is not None
HAS_PEFT = all(importlib.util.find_spec(name) is not None for name in ("torch", "transformers", "peft"))


@dataclass(frozen=True)
class SyntheticDevice:
    type: str = "cpu"


class SyntheticTruth:
    def __init__(self, values):
        self.values = tuple(values)

    def all(self):
        return all(self.values)

    def any(self):
        return any(self.values)


class SyntheticTensor:
    def __init__(self, shape, value, *, dtype="torch.float32", requires_grad=True):
        self.shape, self.dtype = shape, dtype
        self.values = [value] * math.prod(shape)
        self.requires_grad = requires_grad
        self.device = SyntheticDevice()

    def is_floating_point(self):
        return True

    def __eq__(self, other):
        return SyntheticTruth(value == other for value in self.values)

    def __ne__(self, other):
        return SyntheticTruth(value != other for value in self.values)


def policy():
    return SimpleNamespace(r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
                           task_type="CAUSAL_LM", init_lora_weights=True,
                           target_modules=training.TARGET_MODULES, use_rslora=False,
                           use_dora=False, rank_pattern={}, alpha_pattern={}, modules_to_save=None)


class SyntheticModel:
    def __init__(self):
        self.config = SimpleNamespace(num_hidden_layers=2, use_cache=False)
        self.is_gradient_checkpointing = True
        self.peft_config = {"default": policy()}
        self.active_adapters = ["default"]
        self.modules, self.parameters, self.buffers = {}, [], []
        for layer in range(2):
            for index, module in enumerate(training.TARGET_MODULES):
                group = "self_attn" if index < 4 else "mlp"
                path = f"model.layers.{layer}.{group}.{module}"
                self.modules[path] = SimpleNamespace(
                    r={"default": 8}, lora_alpha={"default": 16}, scaling={"default": 2},
                    lora_dropout={"default": SimpleNamespace(p=0.05)}, disable_adapters=False, merged=False)
                self.parameters.append((path + ".base_layer.weight", SyntheticTensor(
                    (4, 4), 0.2, dtype="torch.bfloat16", requires_grad=False)))
                for side in ("A", "B"):
                    self.parameters.append((path + f".lora_{side}.default.weight", SyntheticTensor(
                        (8, 4) if side == "A" else (4, 8), 0.1 if side == "A" else 0.0)))

    def named_parameters(self):
        return iter(self.parameters)

    def named_buffers(self):
        return iter(self.buffers)

    def get_submodule(self, name):
        return self.modules[name]


def synthetic_tensor_hash(value):
    return sha256(repr((value.shape, value.dtype, value.values)).encode("ascii")).hexdigest()


class InitialAdapterSourceTests(unittest.TestCase):
    def setUp(self):
        self.model = SyntheticModel()
        self.torch = SimpleNamespace(Tensor=SyntheticTensor, bfloat16="torch.bfloat16",
                                    isfinite=lambda value: SyntheticTruth(math.isfinite(item)
                                                                          for item in value.values))
        self.addCleanup(patch.stopall)
        patch.object(training, "_torch", return_value=self.torch).start()
        self.hash_tensor = patch.object(training, "tensor_sha256", side_effect=synthetic_tensor_hash).start()

    def inspect(self, **kwargs):
        return source.inspect_initial_adapter(self.model, torch=self.torch, layer_count=2,
                                              adapter_name="default", **kwargs)

    def tensor(self, side):
        return next(value for name, value in self.model.parameters if f".lora_{side}." in name)

    def test_import_is_lazy_and_gates_remain_closed(self):
        subprocess.run([sys.executable, "-B", "-c",
                        "import sys; from organism_v6 import composition_birth_stage2a_initial_adapter as source; "
                        "assert 'torch' not in sys.modules; assert not any(source.SCIENCE_GATES.values())"],
                       check=True)

    def test_ordered_immutable_observation_reuses_existing_helpers(self):
        self.model.parameters.reverse()
        before = deepcopy(self.model.__dict__)
        with patch.object(training, "validate_trainable_roster", wraps=training.validate_trainable_roster) as roster_check, \
                patch.object(training, "_validate_model", wraps=training._validate_model) as model_check, \
                patch.object(training, "adapter_sha256", wraps=training.adapter_sha256) as adapter_hash:
            result = self.inspect()
        roster_check.assert_called_once_with(result.trainable_roster, layer_count=2, adapter_name="default")
        model_check.assert_called_once_with(self.model, result.trainable_roster, 2, "default")
        adapter_hash.assert_called_once_with(self.model, result.trainable_roster)
        self.assertEqual(len(result.trainable_roster), 28)
        self.assertEqual(tuple(spec.name for spec in result.trainable_roster),
                         tuple(name for name, value in self.model.parameters if value.requires_grad))
        self.assertEqual(result.initial_adapter_sha256, training.adapter_sha256(self.model, result.trainable_roster))
        self.assertEqual(repr(before["config"]), repr(self.model.config))
        self.assertEqual([(name, value.values) for name, value in before["parameters"]],
                         [(name, value.values) for name, value in self.model.parameters])
        with self.assertRaises(FrozenInstanceError):
            result.initial_adapter_sha256 = "a" * 64
        with self.assertRaises(FrozenInstanceError):
            result.trainable_roster[0].dtype = "torch.float16"
        self.assertIn("Kaiming-A sampling provenance and distribution", result.outside_verification)
        self.assertEqual(result.initialization_observations[0],
                         "trainer-validated default Kaiming-A/zero-B policy metadata")

    def test_expected_hash_is_optional_byte_agreement_only(self):
        digest = self.inspect().initial_adapter_sha256
        self.assertEqual(self.inspect(expected_initial_adapter_sha256=digest).initial_adapter_sha256, digest)
        self.tensor("A").values[0] = 0.15
        with self.assertRaisesRegex(ValueError, "initial_adapter_bytes_differ"):
            self.inspect(expected_initial_adapter_sha256=digest)
        for invalid in (True, "authenticated", "A" * 64, "0" * 63):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "invalid_expected"):
                self.inspect(expected_initial_adapter_sha256=invalid)

    def test_initial_value_rejections_before_hashing(self):
        for side, value, error in (("A", 0.0, "zero_initial_lora_A"),
                                   ("B", 0.01, "nonzero_initial_lora_B"),
                                   ("A", float("nan"), "finiteness"),
                                   ("A", float("inf"), "finiteness"),
                                   ("B", float("nan"), "finiteness"),
                                   ("B", -float("inf"), "finiteness")):
            with self.subTest(side=side, value=value):
                self.model = SyntheticModel()
                tensor = self.tensor(side)
                tensor.values[:] = [value] * len(tensor.values)
                with self.assertRaisesRegex(ValueError, error):
                    self.inspect()
        self.hash_tensor.assert_not_called()

    def test_cpu_preflight_includes_frozen_parameters_and_buffers(self):
        for target in ("A", "base", "buffer"):
            with self.subTest(target=target):
                self.model = SyntheticModel()
                value = self.tensor("A") if target == "A" else self.model.parameters[0][1]
                if target == "buffer":
                    value = SyntheticTensor((1,), 1, requires_grad=False)
                    self.model.buffers.append(("buffer", value))
                value.device = SyntheticDevice("cuda")
                with patch.object(training, "_validate_model") as validation:
                    with self.assertRaisesRegex(ValueError, "cpu_tensor_required"):
                        self.inspect()
                    validation.assert_not_called()
        self.hash_tensor.assert_not_called()

    def test_roster_and_base_rejections_use_training_contract(self):
        mutations = (
            (lambda: self.model.parameters.pop(), "all_layer"),
            (lambda: setattr(self.tensor("A"), "requires_grad", False), "all_layer"),
            (lambda: setattr(self.tensor("A"), "shape", (4, 8)), "shape_or_rank"),
            (lambda: setattr(self.tensor("A"), "dtype", "torch.float16"), "storage_dtype"),
            (lambda: setattr(self.model.parameters[0][1], "requires_grad", True), "all_layer"),
            (lambda: setattr(self.model.parameters[0][1], "dtype", "torch.float32"), "base_must_be_bfloat16"),
            (lambda: self.model.parameters.append(("extra.lora_A.other.weight", SyntheticTensor(
                (8, 4), 0.1, dtype="torch.bfloat16", requires_grad=False))), "unplanned_frozen_adapter"),
        )
        for mutate, error in mutations:
            with self.subTest(error=error):
                self.model = SyntheticModel()
                mutate()
                with self.assertRaisesRegex(ValueError, error):
                    self.inspect()

    def test_every_layer_and_adapter_name_are_bound(self):
        for old, new in (("layers.1", "layers.0"), (".default.", ".other."),
                         ("self_attn.q_proj", "mlp.q_proj")):
            with self.subTest(new=new):
                self.model = SyntheticModel()
                self.model.parameters = [(name.replace(old, new), value) for name, value in self.model.parameters]
                with self.assertRaises(ValueError):
                    self.inspect()

    def test_required_policy_and_effective_metadata_rejections(self):
        for key, value in (("r", 4), ("lora_alpha", 8), ("lora_dropout", 0.1),
                           ("bias", "all"), ("task_type", "SEQ_CLS"), ("init_lora_weights", False),
                           ("use_rslora", True), ("use_dora", True), ("rank_pattern", {"q_proj": 4}),
                           ("alpha_pattern", {"q_proj": 8}), ("modules_to_save", ["lm_head"]),
                           ("target_modules", ("q_proj",))):
            with self.subTest(key=key):
                self.model = SyntheticModel()
                setattr(self.model.peft_config["default"], key, value)
                with self.assertRaises(ValueError):
                    self.inspect()
        self.model = SyntheticModel()
        del self.model.peft_config["default"].init_lora_weights
        with self.assertRaisesRegex(ValueError, "init_lora_weights"):
            self.inspect()
        for key, value in (("r", {"default": 4}), ("lora_alpha", {"default": 8}),
                           ("scaling", {"default": 4}), ("disable_adapters", True), ("merged", True),
                           ("lora_dropout", {"default": SimpleNamespace(p=0.2)})):
            with self.subTest(key=key):
                self.model = SyntheticModel()
                setattr(next(iter(self.model.modules.values())), key, value)
                with self.assertRaisesRegex(ValueError, "effective_lora_recipe"):
                    self.inspect()

    def test_extra_or_inactive_adapters_and_dependency_mismatch(self):
        self.model.peft_config["other"] = policy()
        with self.assertRaisesRegex(ValueError, "one_active_prepared_adapter"):
            self.inspect()
        self.model = SyntheticModel()
        self.model.active_adapters = []
        with self.assertRaisesRegex(ValueError, "one_active_prepared_adapter"):
            self.inspect()
        self.model = SyntheticModel()
        with patch.object(training, "_torch", return_value=object()):
            with self.assertRaisesRegex(ValueError, "training_torch_dependency_mismatch"):
                self.inspect()


def tiny_torch_model(torch, storage_dtype):
    model = torch.nn.Module()
    model.model = torch.nn.Module()
    model.model.layers = torch.nn.ModuleList()
    for _ in range(2):
        layer = torch.nn.Module()
        layer.self_attn, layer.mlp = torch.nn.Module(), torch.nn.Module()
        for index, name in enumerate(training.TARGET_MODULES):
            module = torch.nn.Module()
            module.base_layer = torch.nn.Linear(4, 4, bias=False, dtype=torch.bfloat16, device="cpu")
            module.base_layer.weight.requires_grad_(False)
            module.lora_A = torch.nn.ModuleDict({"default": torch.nn.Linear(
                4, 8, bias=False, dtype=storage_dtype, device="cpu")})
            module.lora_B = torch.nn.ModuleDict({"default": torch.nn.Linear(
                8, 4, bias=False, dtype=storage_dtype, device="cpu")})
            with torch.no_grad():
                module.lora_B["default"].weight.zero_()
            module.r, module.lora_alpha, module.scaling = {"default": 8}, {"default": 16}, {"default": 2}
            module.lora_dropout = torch.nn.ModuleDict({"default": torch.nn.Dropout(0.05)})
            module.disable_adapters, module.merged = False, False
            setattr(layer.self_attn if index < 4 else layer.mlp, name, module)
        model.model.layers.append(layer)
    model.config = SimpleNamespace(num_hidden_layers=2, use_cache=False)
    model.is_gradient_checkpointing = True
    model.peft_config, model.active_adapters = {"default": policy()}, ["default"]
    return model


@unittest.skipUnless(HAS_TORCH, "optional real CPU fixture requires already installed torch")
class InitialAdapterRealTorchTests(unittest.TestCase):
    def test_exact_storage_hash_and_no_model_mode_or_rng_mutation(self):
        import torch

        with torch.random.fork_rng(devices=[]):
            for dtype in (torch.float32, torch.bfloat16):
                with self.subTest(dtype=dtype):
                    model = tiny_torch_model(torch, dtype)
                    model.eval()
                    model.model.layers[0].self_attn.q_proj.lora_dropout.train()
                    parameters = tuple(model.named_parameters())
                    before = {name: (value.detach().clone(), id(value), value.data_ptr(), value._version,
                                     value.requires_grad, value.grad) for name, value in parameters}
                    modes = tuple(module.training for module in model.modules())
                    configs = deepcopy((model.config, model.peft_config))
                    rng = torch.get_rng_state().clone()
                    result = source.inspect_initial_adapter(model, torch=torch, layer_count=2, adapter_name="default")
                    self.assertEqual(result.initial_adapter_sha256, training.adapter_sha256(model, result.trainable_roster))
                    self.assertEqual({spec.dtype for spec in result.trainable_roster}, {str(dtype)})
                    self.assertTrue(torch.equal(rng, torch.get_rng_state()))
                    self.assertEqual(modes, tuple(module.training for module in model.modules()))
                    self.assertEqual(configs, (model.config, model.peft_config))
                    for name, value in model.named_parameters():
                        saved, identity, pointer, version, requires_grad, gradient = before[name]
                        self.assertTrue(torch.equal(saved, value))
                        self.assertEqual(saved.dtype, value.dtype)
                        self.assertEqual((identity, pointer, version, requires_grad),
                                         (id(value), value.data_ptr(), value._version, value.requires_grad))
                        self.assertIs(gradient, value.grad)
                    with torch.no_grad():
                        next(value for name, value in parameters if ".lora_A." in name).add_(0.125)
                    with self.assertRaisesRegex(ValueError, "initial_adapter_bytes_differ"):
                        source.inspect_initial_adapter(model, torch=torch, layer_count=2, adapter_name="default",
                                                       expected_initial_adapter_sha256=result.initial_adapter_sha256)


@unittest.skipUnless(HAS_PEFT, "optional tiny CPU Qwen/PEFT fixture requires already installed packages")
class InitialAdapterTinyPeftTests(unittest.TestCase):
    def test_config_built_cpu_qwen_peft_inventory_and_binding(self):
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import Qwen2Config, Qwen2ForCausalLM

        with torch.random.fork_rng(devices=[]), torch.device("cpu"):
            config = Qwen2Config(vocab_size=32, hidden_size=16, intermediate_size=32, num_hidden_layers=2,
                                 num_attention_heads=2, num_key_value_heads=1, max_position_embeddings=16384,
                                 use_cache=False)
            base = Qwen2ForCausalLM(config).to(dtype=torch.bfloat16)
            model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
                                                   task_type="CAUSAL_LM", init_lora_weights=True,
                                                   target_modules=list(training.TARGET_MODULES)))
            model.gradient_checkpointing_enable()
            model.eval()
            rng = torch.get_rng_state().clone()
            before = {name: training.tensor_sha256(value) for name, value in model.named_parameters()}
            result = source.inspect_initial_adapter(model, torch=torch, layer_count=2, adapter_name="default")
            self.assertEqual(len(result.trainable_roster), 28)
            self.assertEqual(result.initial_adapter_sha256, training.adapter_sha256(model, result.trainable_roster))
            self.assertEqual(before, {name: training.tensor_sha256(value) for name, value in model.named_parameters()})
            self.assertTrue(torch.equal(rng, torch.get_rng_state()))
            self.assertFalse(model.training)


if __name__ == "__main__":
    unittest.main()
