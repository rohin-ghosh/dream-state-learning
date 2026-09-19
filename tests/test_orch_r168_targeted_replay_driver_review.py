"""Independent CPU driver review; archived lifecycle with no real GPU or subprocess."""

import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from gpu import orch_r168_targeted_replay_driver as driver
from tests import test_orch_r168_targeted_replay_driver as author_tests


integration = driver.integration
replay = driver.replay


class IndependentDriverReviewTests(unittest.TestCase):
    def setUp(self):
        self.case = author_tests.NativeReplayDriverTests(
            'test_full_original_run_reaches_real_bridge_and_four_updates')
        self.addCleanup(self.case.doCleanups)
        self.case.setUp()
        self.fixture = self.case.fixture
        self.marker = self.case.root / 'r168_targeted_replay/sleep_000041'

    def capture_bridges(self):
        instances = []
        original = integration.NativeReplaySleep

        def construct(*args, **kwargs):
            bridge = original(*args, **kwargs)
            instances.append(bridge)
            return bridge

        self.case.stack.enter_context(mock.patch.object(
            integration, 'NativeReplaySleep', side_effect=construct))
        return instances

    def assert_latched(self, bridge, stream):
        steps = self.fixture.child.optimizer_steps
        for cycle in (41, 42):
            with self.subTest(cycle=cycle), self.assertRaisesRegex(
                    ValueError, 'native_replay_uncertain_no_retry'):
                bridge.finish_sleep(stream, SimpleNamespace(record=self.fixture.record),
                    self.fixture.anchors, self.case.root, cycle)
        binding, arm = driver._admit(self.case.native, self.fixture.plan_ref['path'],
                                    True, self.case.binding_ref)
        fresh = integration.NativeReplaySleep(self.case.native, self.fixture.child,
            arm=arm, plan_ref=binding['plan_ref'], runtime_ref=binding['runtime_ref'])
        refusal = (self.assertRaisesRegex(ValueError, 'never_repeat_checkpointed_sleep')
                   if (self.case.root / 'checkpoints/sleep_000041').exists()
                   else self.assertRaises(FileExistsError))
        with refusal:
            fresh.finish_sleep(stream, SimpleNamespace(record=self.fixture.record),
                self.fixture.anchors, self.case.root, 41)
        self.assertEqual(self.fixture.child.optimizer_steps, steps)

    def test_private_run_preserves_code_globals_and_checkpoint_commit_readout_order(self):
        events, signals, stream = self.case.full_run_stubs(cycles=2)
        baseline, baseline_receipt, baseline_records = self.fixture.baseline()
        original = self.case.native.run
        function_type = driver.types.FunctionType
        captured = []

        def construct(*args, **kwargs):
            function = function_type(*args, **kwargs)
            if function.__code__ is original.__code__:
                captured.append(function)
            return function

        bridges = self.capture_bridges()
        with mock.patch.object(driver.types, 'FunctionType', side_effect=construct):
            self.case.invoke()
        self.assertEqual(len(captured), 1)
        isolated = captured[0]
        self.assertIs(isolated.__code__, original.__code__)
        self.assertIsNot(isolated.__globals__, original.__globals__)
        self.assertEqual(set(isolated.__globals__), set(original.__globals__))
        self.assertEqual([key for key in original.__globals__
                          if isolated.__globals__[key] is not original.__globals__[key]],
                         ['finish_sleep'])
        self.assertEqual(isolated.__defaults__, original.__defaults__)
        self.assertEqual(isolated.__kwdefaults__, original.__kwdefaults__)
        self.assertIsNot(isolated.__kwdefaults__, original.__kwdefaults__)
        self.assertIs(isolated.__closure__, original.__closure__)
        self.assertEqual(self.case.native.__dict__, self.case.native_globals)
        self.assertEqual(len(bridges), 1)
        self.assertIs(bridges[0].child, self.fixture.child)
        for cycle in (41, 42):
            checkpoint = events.index(('checkpoint', f'sleep_{cycle:06d}'))
            complete = events.index(('record', 'SLEEP_COMPLETE'), checkpoint)
            readout = events.index(('readout', cycle))
            self.assertLess(checkpoint, complete)
            self.assertLess(complete, readout)
        self.assertEqual(stream.sleep_receipts[-2]['r168_targeted_replay']['accounting']
                         ['experimental_extra_child_token_exposures'], 796)
        self.assertNotIn('r168_targeted_replay', stream.sleep_receipts[-1])
        self.assertEqual(self.fixture.child.optimizer_steps, 4039)
        self.assertEqual(baseline_receipt['optimizer_steps'], 17)
        self.assertEqual(self.fixture.child.optimizer.traces[:17], baseline.optimizer.traces)
        self.assertEqual(self.fixture.child.engine.model.calls[:85], baseline.engine.model.calls)
        self.assertEqual(signals[-2:], [('timer', (0, 0)), ('signal', (14, 'previous_handler'))])
        with self.assertRaisesRegex(ValueError, 'one_actual_child_per_native_run'):
            isolated.__globals__['finish_sleep'](object(), stream, None,
                self.fixture.anchors, self.case.root, 43)

    def test_extra_update_failure_and_failure_receipt_failure_never_replay(self):
        events, signals, stream = self.case.full_run_stubs()
        bridges = self.capture_bridges()
        self.fixture.child.optimizer.fail_at = 19
        write_once = replay.write_once

        def refuse_failure_receipt(path, value):
            if Path(path).name == 'FAILED_OR_UNCERTAIN.json':
                raise OSError('review_failure_receipt_unwritable')
            return write_once(path, value)

        with mock.patch.object(replay, 'write_once', side_effect=refuse_failure_receipt):
            with self.assertRaisesRegex(RuntimeError, 'injected_optimizer_failure'):
                self.case.invoke()
        self.assertEqual(self.fixture.child.optimizer_steps, 4019)
        self.assertTrue((self.marker / 'CONSUMED.json').is_file())
        self.assertFalse((self.marker / 'FINISHED_UPDATES.json').exists())
        self.assertFalse((self.marker / 'FAILED_OR_UNCERTAIN.json').exists())
        self.assertFalse(any(event[0] == 'checkpoint' for event in events))
        self.assertNotIn(('record', 'SLEEP_COMPLETE'), events)
        self.assertNotIn(('readout', 41), events)
        self.assertEqual(len(stream.sleep_receipts), 40)
        self.assert_latched(bridges[0], stream)
        self.assertEqual(signals[-2:], [('timer', (0, 0)), ('signal', (14, 'previous_handler'))])
        self.assertFalse(self.fixture.child.engine.model.training)
        self.assertFalse(self.fixture.child.engine.model.adapter.requires_grad)
        self.assertFalse(self.fixture.child.engine.model.base.requires_grad)

    def test_journal_commit_uncertainty_after_checkpoint_never_replays(self):
        events, signals, stream = self.case.full_run_stubs()
        bridges = self.capture_bridges()
        stream.commit_sleep = mock.Mock(side_effect=OSError('review_commit_uncertain'))
        with self.assertRaisesRegex(OSError, 'review_commit_uncertain'):
            self.case.invoke()
        self.assertEqual(self.fixture.child.optimizer_steps, 4021)
        self.assertTrue((self.case.root / 'checkpoints/sleep_000041/COMMIT.json').is_file())
        self.assertTrue((self.marker / 'FINISHED_UPDATES.json').is_file())
        self.assertTrue((self.marker / 'FAILED_OR_UNCERTAIN.json').is_file())
        self.assertNotIn(('record', 'SLEEP_COMPLETE'), events)
        self.assertNotIn(('readout', 41), events)
        self.assertEqual(len(stream.sleep_receipts), 40)
        self.assert_latched(bridges[0], stream)
        self.assertEqual(signals[-2:], [('timer', (0, 0)), ('signal', (14, 'previous_handler'))])

    def test_GO_expiring_after_driver_admission_refuses_before_updates(self):
        events, signals, stream = self.case.full_run_stubs()
        bridges = self.capture_bridges()
        admit = driver._admit

        def expire_at_sleep(*args, **kwargs):
            binding, arm = admit(*args, **kwargs)
            arm.now = lambda: self.case.go['expires']
            return binding, arm

        with mock.patch.object(driver, '_admit', side_effect=expire_at_sleep):
            with self.assertRaisesRegex(ValueError, 'current_replay_GO'):
                self.case.invoke()
        self.assertEqual(self.fixture.child.optimizer_steps, 4000)
        self.assertFalse(self.marker.exists())
        self.assertNotIn(('readout', 41), events)
        self.assertTrue(bridges[0].uncertain)
        self.assertEqual(signals[-2:], [('timer', (0, 0)), ('signal', (14, 'previous_handler'))])

    def test_binding_in_source_tree_refuses_before_selection_or_GO_reads(self):
        reference = self.fixture.write(self.case.root / 'source/BINDING.json', self.case.binding)
        with mock.patch.object(replay, 'read_bound', wraps=replay.read_bound) as reads:
            with self.assertRaisesRegex(ValueError, 'external_binding_metadata_outside_source'):
                self.case.invoke(binding_ref=reference)
        self.assertEqual([call.args[0] for call in reads.call_args_list],
                         [reference, self.fixture.plan_ref])
        self.assertEqual(self.case.created, [])

    def test_native_run_defaults_and_global_identity_are_bound(self):
        original = self.case.native.run
        for attribute, value in (('__defaults__', ('injected',)),
                                 ('__kwdefaults__', {'resume': True}),
                                 ('__kwdefaults__', {'resume': False, 'extra': None})):
            with self.subTest(attribute=attribute, value=value):
                with mock.patch.object(original, attribute, value):
                    with self.assertRaisesRegex(ValueError, 'exact_native_run_method'):
                        self.case.invoke()
        copied = driver.types.FunctionType(original.__code__, dict(original.__globals__))
        copied.__kwdefaults__ = deepcopy(original.__kwdefaults__)
        with mock.patch.object(self.case.native, 'run', copied):
            with self.assertRaisesRegex(ValueError, 'exact_native_run_method'):
                self.case.invoke()
        self.assertEqual(self.case.created, [])


class IndependentGuardDispatchReviewTests(unittest.TestCase):
    def test_patched_supervisor_retains_dispatch_after_scan_failure(self):
        reference = dict(path='/tmp/R168_REVIEW_EXTERNAL_BINDING.json', sha256='a' * 64)
        staged = driver.patch_guard(author_tests.GUARD_PATH.read_bytes(), reference)
        supervisor = next(node for node in ast.parse(staged).body
                          if isinstance(node, ast.FunctionDef) and node.name == 'supervise')
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            config = dict(attempt_dir=str(attempt))
            plan = dict(source_root=str(attempt / 'source'))
            scanner = mock.Mock(side_effect=RuntimeError('review_scan_failed_no_process'))
            spawn = mock.Mock(side_effect=AssertionError('no process allowed'))
            reaper = mock.Mock()
            namespace = dict(Path=Path, os=os, sys=sys, json=json,
                validate=lambda path: (config, plan),
                child=SimpleNamespace(write_once=replay.write_once),
                subprocess=SimpleNamespace(check_output=scanner, Popen=spawn),
                reap_owned_child=reaper, time=SimpleNamespace(time=lambda: 100))
            exec(compile(ast.Module(body=[supervisor], type_ignores=[]),
                         '<review_patched_supervisor>', 'exec'), namespace)
            with self.assertRaisesRegex(RuntimeError, 'review_scan_failed_no_process'):
                namespace['supervise']('/review/config')
            self.assertTrue((attempt / 'DISPATCH_ONCE').is_dir())
            self.assertTrue((attempt / 'FAILED.json').is_file())
            with self.assertRaises(FileExistsError):
                namespace['supervise']('/review/config')
            scanner.assert_called_once()
            spawn.assert_not_called()
            reaper.assert_called_once_with(None)


if __name__ == '__main__':
    unittest.main()
