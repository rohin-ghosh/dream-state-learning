"""Config-built tiny CPU fixtures only; never pretrained/native qualification."""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_native_models as source
from organism_v6 import composition_birth_stage2a_primitives as primitives


HAS_NATIVE = all(importlib.util.find_spec(name) for name in ("torch", "peft", "transformers"))


class PureTests(unittest.TestCase):
    def test_seed_uses_frozen_low64(self):
        master = b"stage2a-init-test"
        self.assertEqual(primitives.adapter_seed(master),
                         int.from_bytes(sha256(master + b"\0adapter-init").digest()[-8:], "big"))

    def test_writer_preserves_existing_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "receipt.json"
            source._write(path, {"old": True})
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                source._write(path, {"old": False})
            self.assertEqual(path.read_bytes(), original)

    def test_file_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test"
            path.write_bytes(b"retained")
            self.assertEqual(source._file_hash(path), sha256(b"retained").hexdigest())


@unittest.skipUnless(HAS_NATIVE, "native dependencies absent; no pretrained loading")
class TinyCPUInitialization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        import peft
        from transformers import Qwen2Config, Qwen2ForCausalLM
        cls.torch, cls.peft = torch, peft
        cls.Config, cls.Model = Qwen2Config, Qwen2ForCausalLM

    def model(self, dtype=None):
        torch = self.torch
        return self.Model(self.Config(vocab_size=64, hidden_size=16, intermediate_size=32,
                                      num_hidden_layers=2, num_attention_heads=2,
                                      num_key_value_heads=2, max_position_embeddings=16384)
                          ).to(dtype=dtype or torch.bfloat16)

    def digest(self, references):
        return source.training._digest([(name, source.training.tensor_sha256(value))
                                        for name, value in sorted(references.items())])

    def initialize(self, model, destination, **kwargs):
        references = dict(model.named_parameters())
        references.update(dict(model.named_buffers()))
        return source.initialize_atom_cpu(
            model, torch=self.torch, peft=self.peft, master=b"stage2a-init-test",
            initial_directory=destination,
            expected_base_sha256=kwargs.pop("expected", self.digest(references)),
            base_state_hash=self.digest, **kwargs)

    def test_exact_initial_state_retained(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.initialize(self.model(), Path(folder) / "initial")
            self.assertEqual(result.receipt["status"], "INITIALIZED_CPU_ONLY")
            self.assertEqual(len(result.observation.trainable_roster), 28)
            self.assertFalse(result.receipt["native_admission"])
            self.assertFalse(result.receipt["closed_copy_executed"])
            self.assertEqual(source.verify_retained_base(result, base_state_hash=self.digest),
                             result.receipt["base_state_sha256"])
            loaded = self.torch.load(result.directory / "initial_state.pt", weights_only=True)
            self.assertEqual(loaded["seed"], primitives.adapter_seed(b"stage2a-init-test"))
            self.assertEqual(set(loaded["adapter"]), {item.name for item in result.observation.trainable_roster})

    def test_wrong_base_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "initial"
            with self.assertRaisesRegex(ValueError, "base_digest_mismatch"):
                self.initialize(self.model(), destination, expected="0" * 64)
            self.assertFalse(destination.exists())

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileExistsError):
                self.initialize(self.model(), Path(folder))

    def test_no_implicit_dtype_cast(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "exact_bfloat16_base_required"):
                self.initialize(self.model(self.torch.float32), Path(folder) / "initial")

    def test_initialization_failure_kept(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "initial"
            with patch.object(self.peft, "get_peft_model", side_effect=RuntimeError("fixture failure")):
                with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                    self.initialize(self.model(), destination)
            failed = json.loads((destination / "FAILED.json").read_text())
            self.assertEqual(failed["status"], "FAILED")

    def test_retained_reference_detects_changed_base(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.initialize(self.model(), Path(folder) / "initial")
            value = next(iter(result.base_references.values()))
            with self.torch.no_grad():
                value.add_(1)
            with self.assertRaisesRegex(ValueError, "retained_frozen_base_changed"):
                source.verify_retained_base(result, base_state_hash=self.digest)


if __name__ == "__main__":
    unittest.main()
