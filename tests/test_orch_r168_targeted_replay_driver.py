from contextlib import ExitStack
from copy import deepcopy
import ast
import hashlib
import json
from pathlib import Path
import time
from types import SimpleNamespace
import unittest
from unittest import mock

from gpu import orch_r168_targeted_replay_driver as driver
from gpu import orch_r168_targeted_replay_native as integration
from tests import test_orch_r168_targeted_replay_native as native_tests


replay = integration.replay
GUARD_PATH = Path(__file__).resolve().parents[1] / 'gpu/orch_r125_continual_guard.py'


class NativeReplayDriverTests(unittest.TestCase):
    def setUp(self):
        self.fixture = native_tests.NativeReplayIntegrationTests(
            'test_no_arm_is_identical_and_needs_no_cycle_or_authority')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.native = self.fixture.native
        self.plan = dict(self.fixture.plan, source_root=str(self.root / 'source'),
            hard_end_unix=1000, anchors=[], max_sleeps=41)
        (self.root / 'source').mkdir()
        self.fixture.plan = self.plan
        self.fixture.child.plan = deepcopy(self.plan)
        self.fixture.plan_ref = self.fixture.write(self.root / 'DRIVER_PLAN.json', self.plan)
        self.selection = replay.read_bound(self.fixture.selection_ref)
        self.selection['plan_sha256'] = self.fixture.plan_ref['sha256']
        self.selection_ref = self.fixture.write(self.root / 'DRIVER_SELECTION.json', self.selection)
        self.go = replay.read_bound(self.fixture.go_ref)
        self.go.update(selection=self.selection_ref, plan_sha256=self.fixture.plan_ref['sha256'],
                       expires=time.time() + 3600)
        self.go_ref = self.fixture.write(self.root / 'DRIVER_GO.json', self.go)
        self.binding = dict(schema=driver.BINDING_SCHEMA, life_root=str(self.root),
            life_role=replay.ROLE, resume=True, plan_ref=self.fixture.plan_ref,
            runtime_ref=self.fixture.runtime_ref, selection_ref=self.selection_ref,
            main_go_ref=self.go_ref, approved_intake_sha256='e' * 64,
            native_sha256=integration.NATIVE_SHA256, integration_sha256=driver.INTEGRATION_SHA256,
            arm_sha256=integration.ARM_SHA256, driver_sha256=self.fixture.file_hash(driver.__file__))
        self.binding_ref = self.fixture.write(self.root / 'DRIVER_BINDING.json', self.binding)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(mock.patch.object(driver, 'LIFE_ROOT', str(self.root)))
        self.created = []

    def rewrite_binding(self, **changes):
        self.binding.update(changes)
        path = self.root / ('BINDING_' + replay.digest(self.binding) + '.json')
        self.binding_ref = self.fixture.write(path, self.binding)

    def invoke(self, **changes):
        arguments = dict(resume=True, binding_ref=self.binding_ref)
        arguments.update(changes)
        return driver.run(self.native, self.fixture.plan_ref['path'], **arguments)

    def full_run_stubs(self, cycles=1, fail_checkpoint=False):
        fixture = self.fixture
        child = fixture.child
        events = []
        signal_events = []
        self.plan['max_sleeps'] = 40 + cycles
        self.fixture.plan_ref = fixture.write(self.root / 'FULL_PLAN.json', self.plan)
        self.selection['plan_sha256'] = self.fixture.plan_ref['sha256']
        self.selection_ref = fixture.write(self.root / 'FULL_SELECTION.json', self.selection)
        self.go.update(selection=self.selection_ref, plan_sha256=self.fixture.plan_ref['sha256'])
        self.go_ref = fixture.write(self.root / 'FULL_GO.json', self.go)
        self.rewrite_binding(plan_ref=self.fixture.plan_ref, selection_ref=self.selection_ref,
                             main_go_ref=self.go_ref)
        child.plan = deepcopy(self.plan)
        child.engine.runtime = 'CPU_STUB_NO_MODEL'
        child.generate = lambda *args: dict(token_ids=[777, 151645], terminal=True,
                                           text='own object', args=args)
        child.count_tokens = lambda value: len(value['token_ids'])
        presentation = dict(version=self.plan['presentation_version'],
            system_prompt=self.plan['system_prompt'], birth_prompt=self.plan['birth_prompt'])
        checkpoint_ref = self.selection['checkpoint_ref']
        initial_checkpoint = replay.read_bound(checkpoint_ref)
        stream = SimpleNamespace(rows=[fixture.selected], sleep_frontier=1, pending=None,
            experiment='fixture', deadline_unix=1000, context_limit=16384,
            presentation=presentation, sleep_receipts=[{} for position in range(40)],
            model_state_sha256=replay.digest(initial_checkpoint['checkpoint_sha256']),
            history=['original own history'], sleep_due=False)
        stream.pending_rows = lambda: stream.rows[stream.sleep_frontier:]
        stream.checkpoint = lambda: dict(state=dict(pending=stream.pending, rows=deepcopy(stream.rows)),
                                        sha256='f' * 64)

        def step(generate, count_tokens, record, incoming):
            response = generate('unchanged generation')
            events.append(('generation', response, count_tokens(response), incoming))
            row = deepcopy(fixture.new_row)
            if len(stream.rows) > 1:
                row.update(segment=120, event_id='child:segment:120', source_sha256='c' * 64)
            stream.rows.append(row)
            stream.history.append(response)
            stream.sleep_due = True

        def commit_sleep(receipt, record):
            stream.sleep_receipts.append(deepcopy(receipt))
            stream.sleep_frontier = len(stream.rows)
            stream.sleep_due = False
            record('SLEEP_COMPLETE', deepcopy(receipt))

        def checkpoint(path):
            events.append(('checkpoint', path.name))
            if fail_checkpoint:
                raise OSError('checkpoint_failed')
            path.mkdir()
            result = dict(experiment='fixture', optimizer_steps=child.optimizer_steps,
                          checkpoint_sha256=initial_checkpoint['checkpoint_sha256'])
            fixture.write(path / 'COMMIT.json', result)
            return result

        stream.step = step
        stream.commit_sleep = commit_sleep
        child.checkpoint = checkpoint
        original_class = self.native.NativeChild
        created = self.created

        class ChildFactory:
            sleep = original_class.sleep

            def __new__(cls, plan, checkpoint=None):
                created.append((deepcopy(plan), deepcopy(checkpoint)))
                return child

        class Journal:
            def __init__(self, path, create):
                events.append(('journal', str(path), create))

            def __enter__(self):
                return self

            def __exit__(self, *args):
                events.append(('journal_exit',))

            def latest_checkpoint(self):
                return dict(document={'restored': True}, expected_sha256='f' * 64)

            def record(self, kind, document):
                fixture.record(kind, document)
                events.append(('record', kind))

            def read_inbox(self):
                return ['unchanged parent inbox']

        original_read = self.native.read

        def read(path):
            document = original_read(path)
            if Path(path).name == 'COMMIT.json':
                document['experiment'] = 'fixture'
            return document

        signal = SimpleNamespace(SIGALRM=14, ITIMER_REAL=0)
        signal.signal = lambda *args: signal_events.append(('signal', args)) or 'previous_handler'
        signal.setitimer = lambda *args: signal_events.append(('timer', args))
        self.native.__dict__.update(NativeChild=ChildFactory, validate_plan=lambda plan: plan,
            read=read, signal=signal, time=SimpleNamespace(time=lambda: 110),
            ContinualStream=SimpleNamespace(restore=lambda *args, **kwargs: stream),
            verify_experiment_resume=lambda *args: None,
            prepare_sleep=lambda child, stream, journal, cycle: events.append(('prepare', cycle)),
            fresh_readout=lambda child, path, checkpoint, cycle: events.append(('readout', cycle)),
            os=SimpleNamespace(getpid=lambda: 7,
                environ={'R125_ADMISSION_PLAN_SHA256': self.fixture.plan_ref['sha256']}))
        self.stack.enter_context(mock.patch('gpu.orch_r125_stream_journal.StreamJournal', Journal))
        self.stack.enter_context(mock.patch('gpu.orch_r107_base_anchors_inventory.build_inventory',
            return_value=(fixture.anchors, {'scope': 'stub'})))
        readouts = self.root / 'readouts'
        readouts.mkdir()
        for cycle in range(40):
            (readouts / (self.native.readout_name(self.plan, cycle) + '_DISPATCH.json')).touch()
        self.native_globals = dict(self.native.__dict__)
        return events, signal_events, stream

    def test_no_arm_calls_original_run_exactly_without_reads(self):
        original = mock.Mock(return_value='original_result')
        native = SimpleNamespace(run=original)
        with mock.patch.object(replay, 'read_bound', side_effect=AssertionError('unexpected read')):
            self.assertEqual(driver.run(native, 'uninterpreted_plan', resume=False), 'original_result')
        original.assert_called_once_with('uninterpreted_plan', resume=False)

    def test_full_original_run_reaches_real_bridge_and_four_updates(self):
        events, signals, stream = self.full_run_stubs()
        bridge_class = integration.NativeReplaySleep
        with mock.patch.object(integration, 'NativeReplaySleep', wraps=bridge_class) as constructors:
            self.assertIsNone(self.invoke())
        self.assertEqual(constructors.call_count, 1)
        self.assertEqual(len(self.created), 1)
        self.assertEqual(self.fixture.child.optimizer_steps, 4021)
        receipt = stream.sleep_receipts[-1]
        self.assertEqual(receipt['r168_targeted_replay']['accounting']['experimental_extra_steps'], 4)
        self.assertEqual([event for event in events if event[0] == 'readout'],
                         [('readout', 40), ('readout', 41)])
        generations = [event for event in events if event[0] == 'generation']
        self.assertEqual(len(generations), 2)
        self.assertTrue(all(event[1]['terminal'] and event[1]['token_ids'][-1] == 151645
                            and event[3] == ['unchanged parent inbox'] for event in generations))
        self.assertEqual(stream.history[0], 'original own history')
        self.assertEqual(signals[-2:], [('timer', (0, 0)), ('signal', (14, 'previous_handler'))])
        self.assertEqual(self.native.__dict__, self.native_globals)
        self.assertTrue((self.root / 'r168_targeted_replay/sleep_000041/FINISHED_UPDATES.json').exists())

    def test_full_run_no_arm_has_only_original_baseline(self):
        events, signals, stream = self.full_run_stubs()
        with mock.patch.object(integration, 'NativeReplaySleep', side_effect=AssertionError('no arm')):
            self.invoke(binding_ref=None)
        self.assertEqual(self.fixture.child.optimizer_steps, 4017)
        self.assertNotIn('r168_targeted_replay', stream.sleep_receipts[-1])
        self.assertFalse((self.root / 'r168_targeted_replay').exists())
        self.assertEqual(self.native.__dict__, self.native_globals)

    def test_two_cycles_reuse_one_bridge_and_expire_after_target(self):
        events, signals, stream = self.full_run_stubs(cycles=2)
        bridge_class = integration.NativeReplaySleep
        instances = []

        def construct(*args, **kwargs):
            instance = bridge_class(*args, **kwargs)
            instances.append(instance)
            return instance

        with mock.patch.object(integration, 'NativeReplaySleep', side_effect=construct):
            self.invoke()
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].arm.status, 'EXPIRED_SINGLE_SLEEP_ARM')
        self.assertEqual(self.fixture.child.optimizer_steps, 4039)
        self.assertNotIn('r168_targeted_replay', stream.sleep_receipts[-1])
        self.assertEqual(len(list((self.root / 'r168_targeted_replay').iterdir())), 1)
        self.assertEqual(self.native.__dict__, self.native_globals)

    def test_checkpoint_failure_propagates_without_second_readout_or_retry(self):
        events, signals, stream = self.full_run_stubs(fail_checkpoint=True)
        with self.assertRaisesRegex(OSError, 'checkpoint_failed'):
            self.invoke()
        self.assertNotIn(('readout', 41), events)
        self.assertEqual(self.fixture.child.optimizer_steps, 4021)
        self.assertEqual(len(stream.sleep_receipts), 40)
        self.assertTrue((self.root / 'r168_targeted_replay/sleep_000041/FAILED_OR_UNCERTAIN.json').exists())
        self.assertEqual(signals[-2:], [('timer', (0, 0)), ('signal', (14, 'previous_handler'))])

    def test_foreign_root_and_control_binding_refused_before_native_run(self):
        for changes in ({'life_root': '/tmp/foreign'}, {'life_role': 'CONTROL'}, {'resume': False}):
            with self.subTest(changes=changes):
                binding = dict(self.binding, **changes)
                reference = self.fixture.write(self.root / (replay.digest(binding) + '.json'), binding)
                with self.assertRaisesRegex(ValueError, 'only_bound_parented'):
                    self.invoke(binding_ref=reference)
        self.assertEqual(self.created, [])
        self.assertFalse((self.root / 'r168_targeted_replay').exists())

    def test_actual_allowed_root_is_not_a_caller_option(self):
        with mock.patch.object(driver, 'LIFE_ROOT',
                '/localhome/local-rohing/orch_r133_creative_reread_20260916_attempt1/run1'):
            with self.assertRaisesRegex(ValueError, 'only_bound_parented'):
                self.invoke()

    def test_unknown_native_source_and_replaced_run_refused(self):
        altered = self.root / 'native.py'
        altered.write_bytes(Path(self.native.__file__).read_bytes() + b'\n')
        with mock.patch.object(self.native, '__file__', str(altered)):
            with self.assertRaisesRegex(ValueError, 'native_source_pin'):
                self.invoke()
        with mock.patch.object(self.native, 'run', lambda *args, **kwargs: None):
            with self.assertRaisesRegex(ValueError, 'exact_native_run_method'):
                self.invoke()

    def test_plan_argument_and_resume_must_match_binding(self):
        with self.assertRaisesRegex(ValueError, 'only_bound_parented'):
            self.invoke(resume=False)
        with self.assertRaisesRegex(ValueError, 'exact_run_plan_path'):
            driver.run(self.native, self.root / 'other.json', resume=True, binding_ref=self.binding_ref)

    def test_changed_metadata_and_self_hash_refused(self):
        reference = dict(self.binding_ref, sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'metadata_hash_mismatch'):
            self.invoke(binding_ref=reference)
        self.rewrite_binding(driver_sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'native_source_pin'):
            self.invoke()

    def test_expired_GO_refused_before_child_construction(self):
        expired = dict(self.go, expires=101)
        self.rewrite_binding(main_go_ref=self.fixture.write(self.root / 'EXPIRED_GO.json', expired))
        with self.assertRaisesRegex(ValueError, 'current_replay_GO'):
            self.invoke()
        self.assertEqual(self.created, [])

    def test_foreign_selection_rejected_before_foreign_boundary_read(self):
        selection = dict(self.selection, life_root='/tmp/foreign',
                         boundary_ref=dict(path='/tmp/never_read.json', sha256='0' * 64))
        self.rewrite_binding(selection_ref=self.fixture.write(self.root / 'FOREIGN.json', selection))
        with self.assertRaisesRegex(ValueError, 'exact_own_selection_before_boundary_reads'):
            self.invoke()

    def test_binding_creation_is_exclusive_and_input_not_mutated(self):
        with self.assertRaises(FileExistsError):
            replay.write_once(Path(self.binding_ref['path']), self.binding)
        original = deepcopy(self.binding_ref)
        binding, arm = driver._admit(self.native, self.fixture.plan_ref['path'], True, self.binding_ref)
        self.assertEqual(self.binding_ref, original)
        self.assertEqual(arm.status, 'INACTIVE_BEFORE_TARGET_SLEEP')
        self.assertFalse((self.root / 'r168_targeted_replay').exists())


class NativeReplayGuardPatchTests(unittest.TestCase):
    def setUp(self):
        self.source = GUARD_PATH.read_bytes()
        self.reference = dict(path='/tmp/R168_EXTERNAL_BINDING.json', sha256='a' * 64)

    def test_only_exact_run_call_changes_and_original_bytes_remain(self):
        staged = driver.patch_guard(self.source, self.reference)
        original_ast = ast.parse(self.source)
        staged_ast = ast.parse(staged)
        original_entry = next(node for node in original_ast.body
                              if isinstance(node, ast.FunctionDef) and node.name == 'native_entry')
        staged_entry = next(node for node in staged_ast.body
                            if isinstance(node, ast.FunctionDef) and node.name == 'native_entry')
        self.assertNotEqual(ast.dump(original_entry.body[-1]), ast.dump(staged_entry.body[-1]))
        staged_entry.body[-1] = original_entry.body[-1]
        self.assertEqual(ast.dump(original_ast), ast.dump(staged_ast))
        self.assertEqual(GUARD_PATH.read_bytes(), self.source)
        self.assertEqual(hashlib.sha256(self.source).hexdigest(), driver.GUARD_SHA256)

    def entry(self, changes=None):
        changes = changes or {}
        staged = driver.patch_guard(self.source, self.reference)
        entry = next(node for node in ast.parse(staged).body
                     if isinstance(node, ast.FunctionDef) and node.name == 'native_entry')
        events = []
        config = dict(attempt_dir='/attempt', plan_path='/plan', resume=True, plan_sha256='plan_sha')
        plan = dict(gpu_uuid='GPU-bound')
        launch = dict(pid=42, parent_start_ticks='ticks', guard_sha256='config_sha',
                      admission_sha256='admission_sha', admission_verified_unix=900)
        report = dict(scanner_euid=0, clear=True, blocking_reasons=[], gpu=dict(uuid='GPU-bound'))
        launch.update(changes.get('launch', {}))
        report.update(changes.get('report', {}))

        class FakePath:
            def __init__(self, *parts):
                self.path = '/'.join(map(str, parts))

            def __truediv__(self, other):
                return FakePath(self.path, other)

            def is_dir(self):
                return changes.get('dispatch_exists', True)

            def read_text(self):
                return '42 (python)' + ' '.join([' '] + ['0'] * 19 + ['ticks'])

        def validate(path):
            events.append('validate_all_original_source_allocation_lease_checks')
            if changes.get('validate_failure'):
                raise ValueError('validate_failed')
            return config, plan

        def require(condition, reason):
            events.append(reason)
            replay.require(condition, reason)

        child = SimpleNamespace(require=require,
            read=lambda path: launch if path.path.endswith('LAUNCH.json') else report,
            sha=lambda path: 'config_sha' if path == '/config' else 'admission_sha')
        environment = {'CUDA_VISIBLE_DEVICES': changes.get('cuda', 'GPU-bound')}
        namespace = dict(validate=validate,
            await_startup=lambda *args: events.append('await_startup'), Path=FakePath, child=child,
            os=SimpleNamespace(getppid=lambda: 42, environ=environment),
            sys=SimpleNamespace(stdin='startup_pipe'), time=SimpleNamespace(time=lambda: 1000))
        exec(compile(ast.Module(body=[entry], type_ignores=[]), '<guard_entry>', 'exec'), namespace)
        return namespace['native_entry'], events, environment, child

    def test_staged_entry_checks_guards_then_passes_exact_binding_to_driver(self):
        entry, events, environment, child = self.entry()
        with mock.patch.object(driver, 'run', return_value=None) as run:
            entry('/config')
        run.assert_called_once_with(child, '/plan', resume=True, binding_ref=self.reference)
        self.assertEqual(events, ['validate_all_original_source_allocation_lease_checks',
            'await_startup', 'actual_timeout_parent', 'launch_process_and_config_binding',
            'fresh_clear_admission', 'native_GPU_binding'])
        self.assertEqual(environment['R125_ADMISSION_PLAN_SHA256'], 'plan_sha')

    def test_all_guard_failures_prevent_driver_entry(self):
        cases = [dict(validate_failure=True), dict(dispatch_exists=False),
            dict(launch={'pid': 9}), dict(launch={'parent_start_ticks': 'wrong'}),
            dict(launch={'guard_sha256': 'wrong'}), dict(launch={'admission_sha256': 'wrong'}),
            dict(launch={'admission_verified_unix': 1001}), dict(launch={'admission_verified_unix': 800}),
            dict(report={'scanner_euid': 9}), dict(report={'clear': False}),
            dict(report={'blocking_reasons': ['occupied']}), dict(report={'gpu': {'uuid': 'wrong'}}),
            dict(cuda='wrong')]
        for changes in cases:
            with self.subTest(changes=changes):
                entry, events, environment, child = self.entry(changes)
                with mock.patch.object(driver, 'run') as run:
                    with self.assertRaises(ValueError):
                        entry('/config')
                run.assert_not_called()

    def test_unknown_or_already_patched_guard_and_bad_refs_refused(self):
        for source in (self.source + b'\n', driver.patch_guard(self.source, self.reference)):
            with self.assertRaisesRegex(ValueError, 'exact_original_guard_source'):
                driver.patch_guard(source, self.reference)
        for reference in (dict(path='relative', sha256='a' * 64),
                          dict(self.reference, sha256='bad'), dict(self.reference, extra=True)):
            with self.assertRaises(ValueError):
                driver.patch_guard(self.source, reference)


if __name__ == '__main__':
    unittest.main()
