from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import tempfile
import unittest


spec = spec_from_file_location('node3_bounded_completion_observer', Path(__file__).with_name('completed_sleep_observer.py'))
module = module_from_spec(spec)
spec.loader.exec_module(module)


class CompletionObserverTests(unittest.TestCase):
    def test_decision_without_completed_sleep_never_promoted(self):
        observation = dict(observed_unix=123, rows=[dict(physical=0,
            history_progress=dict(first_context_policy={'action': 'RETAIN_CONTEXT_ACROSS_SLEEP'}, completed_sleeps=[]))])
        self.assertIsNone(module.first_completed(observation))

    def test_compacted_or_unverified_complete_never_promoted(self):
        observation = dict(observed_unix=123, rows=[dict(physical=0,
            history_progress=dict(completed_sleeps=[{'retained_history_through_completed_sleep': False}]))])
        self.assertIsNone(module.first_completed(observation))

    def test_actual_verified_completed_receipt_keeps_cycle_hash_identity(self):
        receipt = dict(retained_history_through_completed_sleep=True, cycle=44, record_sha256='saved')
        observation = dict(observed_unix=123, rows=[dict(physical=0, native_pid=99, actor_state='R',
            history_progress=dict(completed_sleeps=[receipt]))])
        result = module.first_completed(observation)
        self.assertEqual(result['completed_sleep'], receipt)
        self.assertEqual(result['native_pid'], 99)
        self.assertTrue(result['no_scientific_claim'])

    def test_create_only_receipts_and_repository_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            module.write(path, {})
            with self.assertRaises(FileExistsError):
                module.write(path, {})
        self.assertTrue((module.REPO / 'gpu/ovx2_ssh.sh').is_file())
        self.assertEqual(module.HARD_END, 1789689000)
