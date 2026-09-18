from copy import deepcopy
import inspect
import unittest

from gpu import orch_math_feedback_uptake_r123_f2_recovery as recovery


class RecoveryTests(unittest.TestCase):
    def fixture(self):
        counters = dict(native=292, parent=66, optimizer_steps=3555)
        terminal = dict(status='FAILED', error_type='FileNotFoundError',
            error='PARENTING_BATTLE_PLAN_v4_2026-09-15.md', counters=counters)
        committed = dict(cycle=12, checkpoint=dict(path_sha256=recovery.CHECKPOINT_SHA,
            optimizer_path_sha256=recovery.OPTIMIZER_SHA))
        calls = [dict(phase=phase, status='COMPLETE' if index < 5 else 'FAILED',
            task_id='task0' if index < 2 else 'task1') for index, phase in enumerate(
                ('episode', 'open_turn', 'episode', 'open_turn', 'presleep', 'reflection'))]
        return terminal, committed, counters, calls

    def test_exact_no_replay_contract(self):
        arguments = self.fixture()
        before = deepcopy(arguments)
        result = recovery.interrupted_contract(*arguments)
        self.assertEqual(result['first_new_native_reservation'], 293)
        self.assertEqual(result['first_new_episode_cycle'], 14)
        self.assertEqual(result['pending_actual_rows'], 5)
        self.assertFalse(result['optimizer_reset'])
        self.assertEqual(arguments, before)

    def test_changed_counters_rejected(self):
        arguments = self.fixture()
        arguments[2]['native'] = 291
        with self.assertRaises(ValueError):
            recovery.interrupted_contract(*arguments)

    def test_wrong_checkpoint_rejected(self):
        arguments = self.fixture()
        arguments[1]['checkpoint']['path_sha256'] = 'wrong'
        with self.assertRaises(ValueError):
            recovery.interrupted_contract(*arguments)

    def test_failed_reflection_never_fabricated(self):
        arguments = self.fixture()
        arguments[3][-1]['response'] = {}
        with self.assertRaises(ValueError):
            recovery.interrupted_contract(*arguments)

    def test_saved_rng_restored(self):
        text = inspect.getsource(recovery.restore)
        self.assertIn("set_rng_state(payload['cpu_rng'])", text)
        self.assertIn("set_rng_state_all(payload['cuda_rng'])", text)

    def test_readout_cpu_offload_order(self):
        text = inspect.getsource(recovery.readout_with_offload)
        self.assertLess(text.index("actor.model.to('cpu')"), text.index('previous.fresh_readout'))
        self.assertGreater(text.index("actor.model.to('cuda:0')"), text.index('previous.fresh_readout'))
        self.assertIn('optimizer.zero_grad(set_to_none=True)', text)


if __name__ == '__main__':
    unittest.main()
