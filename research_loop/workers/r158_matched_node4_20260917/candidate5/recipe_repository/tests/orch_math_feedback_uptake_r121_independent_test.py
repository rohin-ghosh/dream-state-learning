import ast
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r121_independent as subject
from gpu import orch_math_feedback_uptake_r121_independent_native as runner


class IndependentMathTests(unittest.TestCase):
    def fixture(self):
        checkpoint = dict(path_sha256=subject.CHECKPOINT_SHA, optimizer_path_sha256=subject.OPTIMIZER_SHA)
        return dict(session=dict(generation=1, checkpoint=checkpoint), next_cycle=11), dict(
            generation=1, checkpoint=checkpoint, optimizer_steps=3009), dict(native=274, parent=60)

    def test_fork_keeps_counters_and_optimizer(self):
        runtime, state, counts = self.fixture()
        before = deepcopy((runtime, state, counts))
        result = subject.fork_contract(runtime, state, counts)
        self.assertEqual(result['initial_optimizer_steps'], 3009)
        self.assertEqual(result['inherited_counters'], counts)
        self.assertEqual(result['next_cycle'], 11)
        self.assertFalse(result['historical_math_optimizer_continuity'])
        self.assertFalse(result['optimizer_reset'])
        self.assertEqual((runtime, state, counts), before)

    def test_wrong_optimizer_rejected(self):
        runtime, state, counts = self.fixture()
        state['checkpoint']['optimizer_path_sha256'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'actual_committed'):
            subject.fork_contract(runtime, state, counts)

    def test_wrong_generation_rejected(self):
        runtime, state, counts = self.fixture()
        state['generation'] = 0
        with self.assertRaisesRegex(ValueError, 'actual_committed'):
            subject.fork_contract(runtime, state, counts)

    def test_charge_starts_after_historical_used(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject.write(root/'COUNTERS.json', dict(native=274, parent=60, optimizer_steps=3009))
            first = subject.reserve(root, 'native', dict(phase='episode'))
            self.assertEqual(first, 275)
            self.assertEqual(subject.read(root/'COUNTERS.json')['optimizer_steps'], 3009)
            self.assertTrue((root/'reservations/native_00000275.json').exists())

    def test_pending_parent_does_not_wait_or_inject(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject.write(root/'parent_pending/one.json', dict(request=dict(id='one', lane_deadline_unix=200),
                response_path=str(root/'absent.json'), task_id='train'))
            experience = subject.math.policy.Experience()
            with patch.object(subject.time, 'time', return_value=100), patch.object(subject.time, 'sleep', side_effect=AssertionError('blocking')):
                self.assertEqual(subject.poll_parent({}, root, experience, 'open_turn'), [])
            self.assertEqual(experience.events, [])
            self.assertFalse((root/'parent_delivered/one.json').exists())

    def test_missing_parent_records_once_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject.write(root/'parent_pending/one.json', dict(request=dict(id='one', lane_deadline_unix=1),
                response_path=str(root/'absent.json'), task_id='train'))
            experience = subject.math.policy.Experience()
            subject.poll_parent({}, root, experience, 'open_turn')
            before = (root/'parent_delivered/one.json').read_bytes()
            subject.poll_parent({}, root, experience, 'reflection')
            self.assertEqual((root/'parent_delivered/one.json').read_bytes(), before)
            self.assertEqual(subject.read(root/'parent_delivered/one.json')['status'], 'MISSING')

    def test_no_parent_poll_in_eval(self):
        import inspect
        self.assertNotIn('poll_parent', inspect.getsource(runner.readout))
        self.assertNotIn('append_parent', inspect.getsource(runner.readout))
        self.assertIn("response=response", inspect.getsource(runner.readout))

    def test_exact_two_episode_parent_requests(self):
        import inspect
        source = inspect.getsource(runner.collect)
        self.assertEqual(source.count('control.append_parent('), 1)
        self.assertIn('enumerate(tasks)', source)
        self.assertIn("len(tasks) == 2", source)
        self.assertIn('negative_example', source)

    def test_existing_trainer_has_16_and_1_and_lambda(self):
        schedule = list(subject.shared.schedule(6, 2))
        self.assertEqual(sum(item['kind'] == 'NEW' for item in schedule), 96)
        self.assertEqual(sum(item['kind'] == 'REHEARSAL' for item in schedule), 2)
        self.assertEqual(set(index for item in schedule for index in item['anchors']), set(range(42)))
        self.assertTrue(all(abs(item['anchor_weight']*len(item['anchors'])-.25) < 1e-12 for item in schedule))

    def test_new_final_keys_are_distinct_and_date_exact(self):
        from datetime import datetime, timezone
        self.assertEqual(datetime.fromtimestamp(subject.MORNING, timezone.utc).isoformat(), '2026-09-16T06:00:00+00:00')
        source = Path(subject.__file__).read_text()
        self.assertIn('R121_SEP16_0600_FINAL8', source)
        self.assertIn('R121_LEASE_WALL_FINAL8', source)

    def test_no_shared_optimizer_submission_or_launch(self):
        tree = ast.parse(Path(runner.__file__).read_text())
        forbidden = {'submit', 'consolidate', 'bootstrap_fresh_actor', 'wait_fresh_collection_go', 'wait_published'}
        self.assertFalse([node for node in ast.walk(tree) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and node.func.attr in forbidden])

    def test_preinput_recovery_refuses_live_actor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject.write(root/'GUARD_TERMINAL.json', dict(returncode=1, identity={'pid':1}))
            subject.write(root/'LAUNCH.json', dict(identity={'pid':1}))
            with patch.object(subject, 'identity_alive', return_value=True):
                with self.assertRaisesRegex(ValueError, 'actual_failed_preinput'):
                    subject.preinput_proof(root)

    def test_preinput_recovery_refuses_any_reserved_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject.write(root/'GUARD_TERMINAL.json', dict(returncode=1, identity={'pid':1}))
            subject.write(root/'LAUNCH.json', dict(identity={'pid':1}))
            subject.write(root/'reservations/native_1.json', {})
            with patch.object(subject, 'identity_alive', return_value=False):
                with self.assertRaisesRegex(ValueError, 'no_model_load_or_input'):
                    subject.preinput_proof(root)

    def test_learned_episode_uses_lora_generation_not_pure_base_assert(self):
        from types import SimpleNamespace
        loaded = SimpleNamespace(engine=SimpleNamespace())
        actor = runner.Actor(loaded)
        with patch.object(runner.generation, 'generate', return_value={'raw':'kept'}) as generate, \
             patch.object(runner.math.Engine, 'generate', side_effect=AssertionError('pure_base_generation')):
            response = actor.generate([{'role':'user', 'content':'task'}], max_new_tokens=2048)
        self.assertEqual(response['raw'], 'kept')
        self.assertIs(generate.call_args.args[0], loaded)

    def test_anchor_loader_returns_inventory_and_receipt(self):
        import inspect
        source = inspect.getsource(runner.resident)
        self.assertIn('inventory.build_inventory(', source)
        self.assertNotIn('inventory.load_inventory(', source)


if __name__ == '__main__':
    unittest.main()
