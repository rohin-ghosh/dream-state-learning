"""CPU regressions for the inherited-state control and receiving confinement."""

from copy import deepcopy
import errno
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import r205_runtime as runtime
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.previous = dict(optimizer_steps=4908, adapter_state_sha256='a' * 64, experiment=None)
        self.receipt = dict(control_policy=runtime.POLICY, optimizer_steps=0, total_optimizer_steps=4908,
            cumulative_optimizer_steps=4908, weight_updates_enabled=False,
            no_update_reason='parented_no_weight_updates_control', presentations=[],
            child_token_exposures=0, anchor_token_exposures=0, frozen_base_verified=True,
            before_adapter_sha256='a' * 64, after_adapter_sha256='a' * 64,
            before_optimizer_state_sha256='b' * 64, after_optimizer_state_sha256='b' * 64)

    def test_inherited4908_is_retained_not_reset(self):
        runtime.validate_frozen(self.receipt, self.previous)
        for key, bad in [('optimizer_steps', 1), ('total_optimizer_steps', 0),
                ('cumulative_optimizer_steps', 0), ('child_token_exposures', 1),
                ('anchor_token_exposures', 1), ('weight_updates_enabled', True),
                ('after_adapter_sha256', 'c' * 64), ('after_optimizer_state_sha256', 'd' * 64)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                runtime.validate_frozen(dict(self.receipt, **{key: bad}), self.previous)

    def test_no_executor_never_fabricates_calculation(self):
        driver = SimpleNamespace(config={'trial_id': 'R205_FRESH_MATH_FIRST_PRINCIPLES'})
        result = runtime.no_executor(driver, {'code': 'raise RuntimeError()'})
        self.assertFalse(result['executed'])
        self.assertEqual(result['status'], 'PROSE_REASONING_NO_EXECUTOR_CONNECTED')

    def test_no_executor_refuses_other_arm(self):
        with self.assertRaises(ValueError):
            runtime.no_executor(SimpleNamespace(config={'trial_id': 'OTHER'}), {})

    def test_conversational_reuses_gpu0_without_becoming_frozen_control(self):
        from gpu import orch_r184_think_act_learn as driver
        from gpu import orch_r125_stream_journal as journal
        original_child = runtime.native.NativeChild
        original_stream = runtime.native.ContinualStream
        with patch.object(journal, 'StreamJournal'), patch.object(driver, 'run_loop'), \
                patch.object(driver.ThinkActLearn, 'generate_stage'), patch.object(driver.ThinkActLearn, '_cpu'):
            runtime.install_runtime(dict(physical=0, gpu_uuid=runtime.DEVICES[0][0],
                think_act_learn={'trial_id': 'R206_NODE3_CONVERSATIONAL'}))
        self.assertIs(runtime.native.NativeChild, original_child)
        self.assertIs(runtime.native.ContinualStream, original_stream)

    def test_actual_optimizer_cpu_state_hash_detects_change(self):
        import torch
        parameter = torch.nn.Parameter(torch.tensor([1.0]))
        optimizer = torch.optim.AdamW([parameter], lr=3e-5)
        parameter.grad = torch.ones_like(parameter)
        optimizer.step()
        before = runtime.optimizer_digest(optimizer, torch)
        self.assertEqual(before, runtime.optimizer_digest(optimizer, torch))
        optimizer.state[parameter]['exp_avg'].add_(1)
        self.assertNotEqual(before, runtime.optimizer_digest(optimizer, torch))
        self.assertFalse(torch.cuda.is_initialized())

    def test_frozen_sleep_never_calls_training(self):
        import torch
        child = object.__new__(runtime.FrozenChild)
        parameter = torch.nn.Parameter(torch.tensor([1.0]), requires_grad=False)
        child.engine = SimpleNamespace(model=SimpleNamespace(parameters=lambda: [parameter]), verify_base=lambda: None)
        child.torch = torch
        child.optimizer = torch.optim.AdamW([parameter], lr=3e-5)
        child.optimizer_steps = 4908
        child.frozen_optimizer_digest = runtime.optimizer_digest(child.optimizer, torch)
        child.frozen_checkpoint = self.previous
        child.adapter_hash = lambda: 'a' * 64
        with patch.object(child.optimizer, 'step', side_effect=AssertionError('training forbidden')):
            result = child.sleep([{'source_sha256': 'e' * 64}], [], [], lambda *args: None)
        self.assertEqual(result['optimizer_steps'], 0)
        self.assertEqual(child.optimizer_steps, 4908)
        self.assertFalse(torch.cuda.is_initialized())

    def test_fresh_birth_has_no_inherited_context(self):
        stream = ContinualStream(TrainHistory(system_prompt='System', birth_prompt='Fresh'),
            context_limit=16384, segment_tokens=512, segments_per_sleep=2,
            deadline_unix=2000000000, model_state_sha256='a' * 64)
        before = stream.checkpoint()
        recorded = []
        runtime.compact_birth(stream, SimpleNamespace(record=lambda *args: recorded.append(args)))
        self.assertEqual(before, stream.checkpoint())
        self.assertEqual(recorded[0][1]['action'], 'FRESH_EMPTY_NO_INHERITED_CONTEXT_TO_COMPACT')

    def test_control_zero_update_commit_keeps_raw_rows(self):
        stream = runtime.FrozenStream(TrainHistory(system_prompt='System', birth_prompt='Control'),
            context_limit=16384, segment_tokens=512, segments_per_sleep=2,
            deadline_unix=2000000000, model_state_sha256='a' * 64)
        row = dict(segment=0, source_sha256='e' * 64, split='TRAIN', actor='child', prefix_loss=False, target_loss=True)
        stream.rows = [row]
        stream.sleep_receipts = [{'checkpoint': self.previous}]
        references = dict(adapter='1' * 64, optimizer='2' * 64, rng='2' * 64)
        receipt = dict(self.receipt, status='COMPLETE', cycle=52, new_row_sha256=['e' * 64],
            checkpoint_sha256=references, checkpoint=dict(self.previous, checkpoint_sha256=references))
        original = deepcopy(stream.rows)
        saved = []
        stream.commit_sleep(receipt, lambda *args: saved.append(args))
        self.assertEqual(stream.rows, original)
        self.assertEqual(stream.sleep_frontier, 1)
        self.assertEqual(saved[0][0], 'SLEEP_COMPLETE')
        self.assertEqual(stream.model_state_sha256, digest(references))

    def test_control_journal_rejects_missing_request(self):
        journal = object.__new__(runtime.ControlJournal)
        with self.assertRaisesRegex(ValueError, 'actual_sleep_request'):
            journal._advance(dict(latest=None, sleep_request=None, request=None, response=None),
                'SLEEP_COMPLETE', self.receipt)

    def test_latest_all_eight_node3_assignment(self):
        self.assertEqual(set(runtime.DEVICES), set(range(8)))
        self.assertEqual(len({device[0] for device in runtime.DEVICES.values()}), 8)

    def test_actual_containment_command_preserves_defaults_and_single_device(self):
        import time
        from gpu import orch_r125_continual_guard as guard
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'GUARD.json'
            path.write_text('{}')
            for physical in range(8):
                plan = dict(physical=physical, gpu_uuid=runtime.DEVICES[physical][0],
                    hard_end_unix=time.time() + 7200, source_root=temporary, root=temporary + '/logical')
                config = dict(copy_raw=temporary + '/raw', attempt_dir=temporary + '/control')
                with patch.object(guard, 'validate', return_value=(config, plan)):
                    command = runtime.contained_command(path, 'probe')
                devices = [part for part in command if part.startswith('--property=DeviceAllow=/dev/nvidia')]
                self.assertEqual(devices, ['--property=DeviceAllow=/dev/nvidia' + str(physical) + ' rw',
                    '--property=DeviceAllow=/dev/nvidiactl rw', '--property=DeviceAllow=/dev/nvidia-uvm rw'])
                self.assertIn(runtime.MODULE, command)
                self.assertIn('--property=NoNewPrivileges=yes', command)

    def test_peer_capsule_is_source_bound_and_not_a_training_target(self):
        record = dict(kind='R184_LEARN_COMPLETE', document=dict(cycle=52,
            working_state=dict(entries=[dict(kind='uncertainty', text='Synthetic conjecture, not a proof.')])) )
        record['sha256'] = digest(record)
        text = runtime.peer_capsule('peer_math', record)
        self.assertIn('not parent guidance', text)
        self.assertIn('Only your own restatement', text)
        record['document']['cycle'] = 53
        with self.assertRaisesRegex(ValueError, 'binding'):
            runtime.peer_capsule('peer_math', record)

    def test_peer_refuses_inherited_only_cycle_and_oversize(self):
        for cycle, text in ((51, 'Old'), (52, 'x' * 7000)):
            record = dict(kind='R184_LEARN_COMPLETE', document=dict(cycle=cycle,
                working_state=dict(entries=[dict(kind='note', text=text)])))
            record['sha256'] = digest(record)
            with self.assertRaises(ValueError):
                runtime.peer_capsule('peer_repo', record)


if __name__ == '__main__':
    unittest.main()
