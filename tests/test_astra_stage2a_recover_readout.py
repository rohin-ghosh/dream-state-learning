from dataclasses import asdict
import importlib.util
from types import SimpleNamespace
import unittest

from gpu import astra_stage2a_recover_readout as recovery
from organism_v6 import composition_birth_stage2a_training as training


@unittest.skipUnless(importlib.util.find_spec("torch"), "torch unavailable")
class RestoreTests(unittest.TestCase):
    def fixture(self):
        import torch

        model = torch.nn.Linear(2, 1, bias=False)
        spec = training.ParameterSpec("weight", (1, 2), "torch.float32")
        initialized = SimpleNamespace(model=model, observation=SimpleNamespace(trainable_roster=(spec,)))
        checkpoint = dict(binding={"roster": [asdict(spec)]}, adapter={"weight": torch.tensor([[2., 3.]])})
        return torch, initialized, checkpoint

    def test_restore_exact_without_optimizer(self):
        torch, initialized, checkpoint = self.fixture()
        expected = recovery.restore_adapter(initialized, checkpoint, torch=torch)
        self.assertTrue(torch.equal(initialized.model.weight, checkpoint["adapter"]["weight"]))
        self.assertEqual(expected, training.adapter_sha256(
            initialized.model, initialized.observation.trainable_roster))

    def test_invalid_saved_values_do_not_modify_model(self):
        torch, initialized, checkpoint = self.fixture()
        original = initialized.model.weight.detach().clone()
        checkpoint["adapter"]["weight"][0, 1] = float("nan")
        with self.assertRaisesRegex(ValueError, "invalid_saved_adapter"):
            recovery.restore_adapter(initialized, checkpoint, torch=torch)
        self.assertTrue(torch.equal(initialized.model.weight, original))

    def test_wrong_roster_rejected(self):
        torch, initialized, checkpoint = self.fixture()
        checkpoint["binding"]["roster"] = []
        with self.assertRaisesRegex(ValueError, "saved_roster_mismatch"):
            recovery.restore_adapter(initialized, checkpoint, torch=torch)


if __name__ == "__main__":
    unittest.main()
