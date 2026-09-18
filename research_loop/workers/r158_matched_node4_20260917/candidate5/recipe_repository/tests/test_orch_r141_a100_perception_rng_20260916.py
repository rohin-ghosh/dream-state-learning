import ast
from copy import deepcopy
import inspect
import unittest
from unittest.mock import patch

from gpu import orch_r138_kernel_recovery as kernel
from gpu import orch_r141_a100_perception_rng_20260916 as repair
from tests.test_orch_r138_kernel_recovery import KernelRecoveryTests


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.fixture = KernelRecoveryTests('test_exact_three_replays_restore_rng_preserve_every_original_file_and_pending')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        fixture = self.fixture
        bound = kernel._bind(fixture.child, fixture.stream, fixture.journal, fixture.plan)
        old = fixture.root / 'checkpoints/sleep_000002'
        saved = fixture.root / 'checkpoints/sleep_000015'
        old.rename(saved)
        fixture.checkpoint['adapter_path'] = str(saved / 'adapter')
        fixture.checkpoint['optimizer_rng_path'] = str(saved / 'optimizer_rng.pt')
        fixture.checkpoint['optimizer_steps'] = 1010
        fixture.child.optimizer_steps = 1010
        fixture.child.torch.payload['optimizer_steps'] = 1010
        fixture.plan['schema'] = repair.SCHEMA
        fixture.plan['checkpoint'] = deepcopy(fixture.checkpoint)
        constants = dict(SOURCE_ROOT=str(fixture.source_root), SLEEP_REQUEST_SHA256=fixture.plan['sleep_request_sha256'],
            CHECKPOINT_SHA256=fixture.checkpoint['checkpoint_sha256'], ADAPTER_STATE_SHA256=fixture.child.adapter,
            ORIGINAL_PLAN_SHA256=fixture.plan['original_plan']['sha256'],
            ORIGINAL_LOG_SHA256=fixture.plan['original_log']['sha256'],
            ORIGINAL_EXIT_SHA256=fixture.plan['original_exit']['sha256'])
        for name, value in constants.items():
            patched = patch.object(repair, name, value)
            patched.start()
            self.addCleanup(patched.stop)
        binding = patch.object(repair, '_bind', return_value=bound)
        binding.start()
        self.addCleanup(binding.stop)

    def run_replay(self):
        fixture = self.fixture
        return repair.recover_rng(fixture.child, fixture.stream, fixture.journal, fixture.plan)

    def test_all_three_replays_preserve_pending_and_no_updates(self):
        fixture = self.fixture
        state = deepcopy(fixture.stream.checkpoint())
        calls = len(fixture.child.calls)
        with patch.object(fixture.journal, 'record', side_effect=AssertionError('no TRAIN writes')):
            receipt = self.run_replay()
        self.assertEqual(receipt['status'], 'COMPLETE')
        self.assertEqual(receipt['optimizer_steps'], 1010)
        self.assertEqual(receipt['optimizer_updates'], 0)
        self.assertEqual(len(fixture.child.calls) - calls, 3)
        self.assertEqual(fixture.stream.checkpoint(), state)
        self.assertFalse(receipt['original_final_rng_snapshot_available'])

    def test_first_mismatch_stops_no_retry(self):
        fixture = self.fixture
        fixture.child.mismatch = (7, 'raw', 'changed')
        calls = len(fixture.child.calls)
        with self.assertRaisesRegex(ValueError, 'bit_identical_generation'):
            self.run_replay()
        self.assertEqual(len(fixture.child.calls) - calls, 1)
        self.assertTrue(fixture.evidence('FAILED.json').exists())
        with self.assertRaises(FileExistsError):
            self.run_replay()

    def test_optimizer_mutation_rejected_even_without_step_change(self):
        self.fixture.child.mutate = 'optimizer'
        with self.assertRaisesRegex(ValueError, 'replay_cannot_update_learning'):
            self.run_replay()

    def test_checkpoint_bytes_changed_rejected_before_replay(self):
        fixture = self.fixture
        from pathlib import Path
        Path(fixture.checkpoint['optimizer_rng_path']).write_bytes(b'changed')
        calls = len(fixture.child.calls)
        with self.assertRaises(ValueError):
            self.run_replay()
        self.assertEqual(len(fixture.child.calls), calls)

    def test_prior_attempt_option_cannot_open_retry(self):
        self.fixture.plan['prior_failed_attempt'] = {}
        with self.assertRaisesRegex(ValueError, 'explicit_kernel_recovery_plan'):
            self.run_replay()


class KernelPatternTests(unittest.TestCase):
    def test_fingerprinting_and_generation_source_checks_are_exact_kernel_pattern(self):
        for name in ('_optimizer_fingerprint', '_verify_source', '_verify_original_plan'):
            self.assertEqual(ast.dump(ast.parse(inspect.getsource(getattr(repair, name)))),
                             ast.dump(ast.parse(inspect.getsource(getattr(kernel, name)))))


if __name__ == '__main__':
    unittest.main()
