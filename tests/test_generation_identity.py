"""Configured generation identities and batch-cardinality checks, CPU only."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from organism_v6.batch_loop import run_episodes_batch
from organism_v6.gym_backend import Episode
from organism_v6.ledger import Ledger
from organism_v6.model_backend import configured_generation_identity, wait_gpu_free
from organism_v6.preschool import PostOutcomeSlot


class GenerationIdentityTests(unittest.TestCase):
    def test_failed_or_malformed_gpu_query_is_not_free_memory(self):
        for status, output in ((1, ""), (0, ""), (0, "N/A"), (0, "0\n0"), (0, "-1")):
            with self.subTest(status=status, output=output), \
                    patch("subprocess.run", return_value=Mock(returncode=status, stdout=output)), \
                    patch("time.sleep"):
                self.assertFalse(wait_gpu_free(timeout_s=3))

    def test_successful_gpu_measurement_respects_threshold(self):
        for output, expected in (("0\n", True), ("2999\n", True), ("3000\n", False)):
            with self.subTest(output=output), \
                    patch("subprocess.run", return_value=Mock(returncode=0, stdout=output)), \
                    patch("time.sleep"):
                self.assertEqual(wait_gpu_free(timeout_s=3), expected)

    def test_base_and_adapter_identity_bind_configured_files(self):
        base = configured_generation_identity("pinned-base", None)
        self.assertIsNone(base["adapter_input"])
        self.assertEqual(base["adapter_files"], {})
        with tempfile.TemporaryDirectory() as directory:
            adapter = Path(directory)
            (adapter / "adapter_config.json").write_bytes(b"fixture-config")
            (adapter / "adapter_model.safetensors").write_bytes(b"fixture-weights")
            result = configured_generation_identity("pinned-base", directory)
            self.assertEqual(result["adapter_files"]["adapter_model.safetensors"],
                             hashlib.sha256(b"fixture-weights").hexdigest())
            (adapter / "adapter_model.bin").write_bytes(b"ambiguous")
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                configured_generation_identity("pinned-base", directory)

    def test_missing_weights_fail_before_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "missing"):
                configured_generation_identity("pinned-base", directory)

    def test_wrong_wake_cardinality_never_executes_an_action(self):
        gym = Mock()
        model = Mock()
        model.batch.return_value = []
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(str(Path(directory) / "ledger.jsonl"))
            episode = Episode("train/item", "situation")
            with self.assertRaisesRegex(RuntimeError, "cardinality"):
                run_episodes_batch(model, gym, [episode], "birth", ledger, budget_ticks=1)
        gym.evaluate.assert_not_called()

    def test_slot_wake_records_real_call_hashes_and_seed(self):
        gym = Mock()
        gym.evaluate.return_value = (.2, "instructions 1000 -> 800 (20.0% reduction)")
        model = Mock()
        model.generation_identity.return_value = configured_generation_identity("fixture-base", None)
        model.batch.side_effect = [["ACT: -mem2reg"], ["I ran -mem2reg and measured 20%."]]
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(str(Path(directory) / "ledger.jsonl"))
            run_episodes_batch(model, gym, [Episode("train/item", "situation")],
                               "birth", ledger, budget_ticks=1, log=lambda message: None,
                               gen_seed=17, note_after=PostOutcomeSlot())
            action = next(row for row in ledger.rows() if row["kind"] == "act")
            first_call = model.batch.call_args_list[0]
            self.assertEqual(action["generation"]["seed"], first_call.kwargs["seeds"][0])
            self.assertEqual(action["generation"]["prompt_sha256"],
                             hashlib.sha256(first_call.args[0][0].encode()).hexdigest())
            self.assertEqual(action["generation"]["output_sha256"],
                             hashlib.sha256(b"ACT: -mem2reg").hexdigest())


if __name__ == "__main__":
    unittest.main()
