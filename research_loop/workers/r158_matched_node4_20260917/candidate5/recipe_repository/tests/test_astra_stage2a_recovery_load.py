import unittest
from types import SimpleNamespace
from unittest.mock import patch

from gpu import astra_stage2a_recovery_load as recovery


class RecoveryLoadTests(unittest.TestCase):
    def test_load_is_strict_and_registry_restored(self):
        registry = [object(), object()]
        original = list(registry)
        torch = SimpleNamespace(serialization=SimpleNamespace(
            get_safe_globals=lambda: list(registry),
            clear_safe_globals=registry.clear,
            add_safe_globals=registry.extend))

        def strict_load(directory):
            self.assertEqual(directory, "saved-D1")
            self.assertEqual(registry, [])
            return {"completed_updates": 256}

        with patch.object(recovery.checkpoint_api, "load_checkpoint", strict_load):
            self.assertEqual(recovery.load_exclusive("saved-D1", torch=torch),
                             {"completed_updates": 256})
        self.assertEqual(registry, original)

    def test_failure_restores_without_retry(self):
        registry = [object()]
        original = list(registry)
        torch = SimpleNamespace(serialization=SimpleNamespace(
            get_safe_globals=lambda: list(registry),
            clear_safe_globals=registry.clear,
            add_safe_globals=registry.extend))
        with patch.object(recovery.checkpoint_api, "load_checkpoint",
                          side_effect=ValueError("invalid bytes")) as loader:
            with self.assertRaisesRegex(ValueError, "invalid bytes"):
                recovery.load_exclusive("saved-D1", torch=torch)
        loader.assert_called_once_with("saved-D1")
        self.assertEqual(registry, original)


if __name__ == "__main__":
    unittest.main()
