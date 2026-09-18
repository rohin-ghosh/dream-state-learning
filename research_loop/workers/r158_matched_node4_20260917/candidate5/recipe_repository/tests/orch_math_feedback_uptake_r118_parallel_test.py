from copy import deepcopy
from dataclasses import dataclass
import inspect
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r118_parallel_boundary as boundary
from gpu import orch_math_feedback_uptake_r118_parallel_run as run
from tests import orch_math_feedback_uptake_r118_final_drain_test as existing


shared = run.shared


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.fixture = existing.BoundaryTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.test_complete_checkpoint_DEV_boundary_allowed()
        self.root, self.common = self.fixture.root, self.fixture.common
        self.plan = dict(self.fixture.plan, native_source=str(self.fixture.directory), uuid='synthetic-uuid',
            native=dict(pid=123, start_ticks=456, boot_id='synthetic-boot'),
            guard=dict(pid=124, start_ticks=457, boot_id='synthetic-boot'))
        self.refs = {}
        for name in boundary.FENCES:
            value = dict(status='PRESERVED')
            if name == 'native_launch':
                value = dict(identity=self.plan['native'])
            if name == 'guard_receipt':
                value = dict(identity=self.plan['guard'])
            if name == 'final_drain_plan':
                value = self.plan
            path = self.fixture.directory/'bindings'/(name+'.json')
            shared.write(path, value)
            self.refs[name] = run.previous.ready.reference(path)
        self.fixture.rewrite(self.common/'STATE.json', lambda value: value.update(checkpoint=dict(path_sha256='b'*64)))
        shared.write(self.root/'PROGRESS.json', dict(cycle=10, phase='CYCLE_COMPLETE',
            counters=dict(native=26, parent=6), shared_generation=1, shared_checkpoint_sha256='b'*64))
        for name in ('CONFIG.json', 'ACTIVATION.json', 'SHARED_ACTIVATION.json', 'SHARED_LAUNCH.json',
                     'SHARED_CLIENT_READY.json'):
            shared.write(self.root/name, dict(preserved=True))
        readout = self.root/'readouts/cycle_010'
        for name in ('BEFORE.json', 'AFTER.json', 'MOUNTED_FINAL.json'):
            path = readout/name
            if path.exists():
                self.fixture.rewrite(path, lambda value: value.update(shared_generation=1,
                    shared_checkpoint_sha256='b'*64, process=dict(pid=555, start_ticks=777)))
            else:
                shared.write(path, dict(shared_generation=1, shared_checkpoint_sha256='b'*64,
                    process=dict(pid=555, start_ticks=777)))
        self.patch(boundary.client, 'BRANCHES', {'F2':self.root, 'A2':self.fixture.directory/'lane5'})
        self.patch(boundary.drain, 'actual_process', Mock())
        self.patch(shared, 'checked_checkpoint', Mock())

    def patch(self, obj, name, value):
        manager = patch.object(obj, name, value)
        manager.start()
        self.addCleanup(manager.stop)
        return value

    def observe(self):
        return boundary.inspect_completed(self.plan, self.refs)

    def engine(self):
        return SimpleNamespace(session=dict(branch='F2', branch_root=str(self.root), generation=1,
            checkpoint_sha256='b'*64), verify_base=Mock())

    def test_complete_DEV_settled_cursor_not_release_or_activation(self):
        result = self.observe()
        self.assertEqual(result['next_cycle'], 11)
        self.assertEqual(result['counters'], dict(native=26, parent=6))
        self.assertEqual(result['status'], 'OBSERVED_NOT_RELEASED')
        self.assertFalse(result['released'])
        self.assertFalse(result['activated'])
        self.assertEqual(result['process_signals'], 0)
        self.assertIn('readouts/cycle_010/BEFORE.json', result['preserved_files'])
        self.assertIn('cycle010/BOUNDARY.json', result['preserved_files'])

    def test_incomplete_DEV_is_not_handoff(self):
        (self.root/'readouts/cycle_010/COMPLETE.json').unlink()
        self.assertIsNone(self.observe())

    def test_next_cycle_directory_is_not_handoff(self):
        shared.write(self.root/'cycle011/SHARED_BEFORE.json', dict(started=True))
        self.assertIsNone(self.observe())

    def test_unsettled_progress_rejected(self):
        self.fixture.rewrite(self.root/'PROGRESS.json', lambda value: value.update(phase='READOUT'))
        with self.assertRaisesRegex(ValueError, 'settled_cursor'):
            self.observe()

    def test_mounted_wrong_checkpoint_rejected(self):
        self.fixture.rewrite(self.root/'readouts/cycle_010/AFTER.json',
            lambda value: value.update(shared_checkpoint_sha256='c'*64))
        with self.assertRaisesRegex(ValueError, 'actual_mount'):
            self.observe()

    def test_resident_used_as_readout_rejected(self):
        self.fixture.rewrite(self.root/'readouts/cycle_010/BEFORE.json',
            lambda value: value.update(process=self.plan['native']))
        with self.assertRaisesRegex(ValueError, 'DEV_not_resident'):
            self.observe()

    def test_post_readout_process_drift_rejected(self):
        self.fixture.rewrite(self.root/'readouts/cycle_010/AFTER.json',
            lambda value: value['process'].update(start_ticks=888))
        with self.assertRaisesRegex(ValueError, 'same_fresh_DEV_process'):
            self.observe()

    def test_started_next_sleep_rejected(self):
        shared.write(self.common/'generation_000001/sleep/START.json', dict(started=True))
        with self.assertRaisesRegex(ValueError, 'started_sleep'):
            self.observe()

    def test_already_accepted_next_submission_rejected(self):
        shared.write(self.common/'generation_000001/F2.json', dict(accepted=True))
        with self.assertRaisesRegex(ValueError, 'next_submission'):
            self.observe()

    def test_final_timer_hash_change_rejected(self):
        Path(self.refs['final_timer']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'immutable_file_hash'):
            self.observe()

    def test_no_final_guard_binding_omission(self):
        self.refs.pop('final_drain_plan')
        with self.assertRaisesRegex(ValueError, 'all_authentic_guard'):
            self.observe()

    def test_same_actor_accepts_carry_without_replay(self):
        result = self.observe()
        with patch.object(run.hook, 'process_identity', return_value=self.plan['native']), \
                patch.object(run.client, 'current', return_value={}):
            cycle, carry = boundary.accept_in_process(result, self.engine())
        self.assertEqual(cycle, 11)
        self.assertEqual(carry['text'], 'Own reflection')
        self.assertEqual(shared.read(self.root/'COUNTERS.json')['native'], 26)

    def test_pid_reuse_or_other_actor_rejected(self):
        result = self.observe()
        for change in (dict(pid=888), dict(start_ticks=999), dict(boot_id='other')):
            with self.subTest(change=change), patch.object(run.hook, 'process_identity',
                    return_value=dict(self.plan['native'], **change)):
                with self.assertRaisesRegex(ValueError, 'same_live_actor'):
                    boundary.accept_in_process(result, self.engine())

    def test_post_observation_charge_change_rejected(self):
        result = self.observe()
        self.fixture.rewrite(self.root/'COUNTERS.json', lambda value: value.update(native=27))
        with patch.object(run.hook, 'process_identity', return_value=self.plan['native']):
            with self.assertRaisesRegex(ValueError, 'immutable_file_hash'):
                boundary.accept_in_process(result, self.engine())

    def test_post_observation_carry_change_rejected(self):
        result = self.observe()
        self.fixture.rewrite(self.root/'cycle010/BOUNDARY.json', lambda value: value.update(own_reflection={}))
        with patch.object(run.hook, 'process_identity', return_value=self.plan['native']):
            with self.assertRaisesRegex(ValueError, 'immutable_file_hash'):
                boundary.accept_in_process(result, self.engine())

    def test_scope_wrong_root_rejected(self):
        self.plan['root'] = str(self.fixture.directory)
        with self.assertRaisesRegex(ValueError, 'original_math_root'):
            self.observe()

    def test_preserved_path_escape_rejected(self):
        with self.assertRaisesRegex(ValueError, 'path_escape'):
            boundary.unchanged(self.root, {'../outside.json':'a'*64})

    def test_previous_submission_never_used_as_next_barrier(self):
        result = self.observe()
        engine = self.engine()
        engine.session['shared_root'] = str(self.common)
        with patch.object(run.client, 'current', return_value={}):
            with self.assertRaisesRegex(ValueError, 'current_generation_submission_only'):
                boundary.submission_certificate(self.root, engine, 11,
                    result['accepted_previous_submission'], self.refs, {})


class ParallelLoopTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)/'lane1'
        shared.write(self.root/'COUNTERS.json', dict(native=26, parent=6))
        shared.write(self.root/'PROGRESS.json', dict(cycle=10))
        self.session = dict(branch='F2', branch_root=str(self.root), shared_root=str(self.root/'common'),
            generation=1, checkpoint_sha256='b'*64, config_sha256='d'*64)
        self.engine = SimpleNamespace(session=deepcopy(self.session), verify_base=Mock(), poisoned=False,
            loaded=SimpleNamespace(engine=object(), optimizer=None))
        self.output = self.root/'cycle011'
        self.order = []
        self.collect = dict(carry={'actor':'child','text':'Own carry'}, submission={'path':'accepted','sha256':'s'})
        self.following = dict(self.session, generation=2, checkpoint=dict(path_sha256='c'*64),
            checkpoint_sha256='c'*64)
        self.result = dict(status='COMPLETE_ALL8_INPLACE', state=dict(generation=2,
            checkpoint=self.following['checkpoint']), metrics=dict(optimizer_steps=3))
        self.kwargs = dict(anchor_module=object(), anchors=['unchanged-order'],
            anchor_root='original-anchors', protected_refs={}, supervision={}, await_activation=self.activate,
            check=Mock(), clock=lambda: 1)

    def collect_cycle(self, *args):
        self.order.append('collect_submit')
        shared.write(self.output/'TRAIN_COMPLETE.json', dict(submission=self.collect['submission']))
        return self.collect

    def activate(self, certificate, deadline):
        self.order.append('Main_activation')
        path = self.root/'future_activation.json'
        shared.write(path, dict(participants={'F2':certificate}, generation=1))
        return run.previous.ready.reference(path)

    def consolidate(self, **kwargs):
        self.order.append('all8_consolidate')
        self.assertIs(kwargs['engine'], self.engine.loaded.engine)
        self.assertIsNone(kwargs['optimizer'])
        self.assertIsNone(kwargs['save_checkpoint'])
        self.assertNotIn('group', kwargs)
        return self.result

    def adopt(self, engine, following, result):
        self.order.append('adopt_actual_broadcast')
        engine.session = following
        engine.poisoned = False
        return dict(in_place=True)

    def readout(self, root, session, cycle):
        self.order.append('fresh_DEV')
        self.assertEqual(cycle, 11)
        self.assertEqual(session['generation'], 2)
        self.assertTrue((self.output/'SHARED_SLEEP.json').exists())
        self.assertFalse((self.output/'COMPLETE.json').exists())

    def patches(self):
        from contextlib import ExitStack
        stack = ExitStack()
        stack.enter_context(patch.object(run.client, 'collect_cycle', side_effect=self.collect_cycle))
        stack.enter_context(patch.object(boundary, 'submission_certificate',
            return_value=dict(preserved_files={'COUNTERS.json':shared.sha(self.root/'COUNTERS.json')})))
        stack.enter_context(patch.object(boundary, 'fences', return_value={}))
        self.consolidate_mock = stack.enter_context(patch.object(run.hook, 'launch_at_boundary', side_effect=self.consolidate))
        stack.enter_context(patch.object(run.client, 'prepare', return_value=self.following))
        stack.enter_context(patch.object(run, 'adopt_broadcast', side_effect=self.adopt))
        self.readout_mock = stack.enter_context(patch.object(run, 'dispatch_readout', side_effect=self.readout))
        return stack

    def test_original_collect_parallel_broadcast_DEV_cursor_order(self):
        with self.patches():
            result = run.run_cycle(self.root, self.engine, 11, ['task1','task2'], 'prior', **self.kwargs)
        self.assertEqual(self.order, ['collect_submit','Main_activation','all8_consolidate',
            'adopt_actual_broadcast','fresh_DEV'])
        self.assertEqual(result, self.collect['carry'])
        self.assertEqual(shared.read(self.root/'PROGRESS.json')['cycle'], 11)
        self.assertEqual(shared.read(self.root/'PROGRESS.json')['shared_generation'], 2)
        self.assertEqual(shared.read(self.output/'COMPLETE.json')['counters'], dict(native=26, parent=6))

    def test_hook_failure_no_readout_or_completed_cycle(self):
        with self.patches():
            self.consolidate_mock.side_effect = RuntimeError('collective_failed')
            with self.assertRaisesRegex(RuntimeError, 'collective_failed'):
                run.run_cycle(self.root, self.engine, 11, [], None, **self.kwargs)
            self.readout_mock.assert_not_called()
        self.assertFalse((self.output/'COMPLETE.json').exists())
        self.assertTrue(self.engine.poisoned)

    def test_failed_DEV_never_settles_cursor(self):
        with self.patches():
            self.readout_mock.side_effect = RuntimeError('DEV_failed')
            with self.assertRaisesRegex(RuntimeError, 'DEV_failed'):
                run.run_cycle(self.root, self.engine, 11, [], None, **self.kwargs)
        self.assertFalse((self.output/'COMPLETE.json').exists())
        self.assertEqual(shared.read(self.root/'PROGRESS.json')['cycle'], 10)

    def test_no_retry_existing_participant_file(self):
        shared.write(self.output/'PARALLEL_PARTICIPANT.json', dict(previous=True))
        with self.patches():
            with self.assertRaises(FileExistsError):
                run.run_cycle(self.root, self.engine, 11, [], None, **self.kwargs)
            self.consolidate_mock.assert_not_called()

    def test_native_cutoff_does_not_collect(self):
        self.kwargs['clock'] = lambda: run.previous.math.NATIVE-120
        with patch.object(run.client, 'collect_cycle') as collect:
            with self.assertRaisesRegex(ValueError, 'original_collection_cutoff'):
                run.run_cycle(self.root, self.engine, 11, [], None, **self.kwargs)
            collect.assert_not_called()

    def test_outer_loop_keeps_original_cursor_and_cap(self):
        shared.write(self.root.parent/'TRAIN.json', [[], []])
        handoff = dict(root=str(self.root))
        with patch.object(run, 'authorize', return_value=(2, 'prior')), \
                patch.object(run.previous.math.policy, 'CYCLES', 2), \
                patch.object(run, 'run_cycle', return_value='new') as cycle:
            result = run.run(self.root, self.engine, handoff=handoff, authorization={}, **self.kwargs)
        self.assertEqual(cycle.call_count, 1)
        self.assertEqual(cycle.call_args.args[2], 2)
        self.assertEqual(result['next_cycle'], 3)
        self.assertFalse(result['legacy_FINAL_dispatched'])

    def test_outer_failure_preserves_ledger_terminal_no_retry(self):
        shared.write(self.root.parent/'TRAIN.json', [[]])
        with patch.object(run, 'authorize', return_value=(1, None)), \
                patch.object(run, 'run_cycle', side_effect=RuntimeError('failed')) as cycle:
            with self.assertRaisesRegex(RuntimeError, 'failed'):
                run.run(self.root, self.engine, handoff=dict(root=str(self.root)), authorization={}, **self.kwargs)
        self.assertEqual(cycle.call_count, 1)
        failed = shared.read(self.root/'cycle001/PARALLEL_FAILED.json')
        self.assertFalse(failed['replay_permitted'])
        self.assertEqual(failed['counters'], dict(native=26, parent=6))

    def test_contract_exact_hook_signature_and_ranks(self):
        result = run.contract()
        self.assertEqual(result['hook_signature'], str(inspect.signature(run.hook.launch_at_boundary)))
        self.assertEqual(result['math_ranks'], {'F2':1, 'A2':5})
        self.assertFalse(result['GPU_tested'])
        self.assertFalse(result['actor_replacement'])
        self.assertIn('NOT serial-equivalent', result['algorithm'])

    def test_no_process_or_activation_side_effect_entrypoint(self):
        source = inspect.getsource(run)
        for forbidden in ('pidfd_send_signal(', 'init_process_group(', 'AdamW('):
            self.assertNotIn(forbidden, source)

    def test_fresh_readout_uses_old_frozen_source_not_candidate_import(self):
        source = self.root/'original_source'
        name = 'gpu/orch_math_feedback_uptake_r118_shared_run.py'
        shared.write(source/name, dict(test_fixture_source=True))
        shared.write(self.root/'SHARED_CLIENT_READY.json', dict(branch='F2', root=str(self.root),
            successor_source=str(source), source_files={name:shared.sha(source/name)}))
        child = Mock(pid=888)
        child.wait.return_value = 0
        child.poll.return_value = 0
        with patch.object(run.subprocess, 'Popen', return_value=child) as launch, \
                patch.object(run.previous.math.common, 'process_identity', return_value={'pid':888}):
            run.dispatch_readout(self.root, self.session, 11)
        self.assertEqual(launch.call_args.kwargs['cwd'], source)
        self.assertEqual(launch.call_args.kwargs['env']['PYTHONPATH'], str(source))
        binding = shared.read(self.root/'shared_readout_bindings/cycle_011.json')
        self.assertEqual(binding['stage'], 'cycle')
        self.assertTrue(binding['never_rows_or_buffer'])
        self.assertEqual(binding['session'], self.session)


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = existing.BoundaryTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root, self.common = self.fixture.root, self.fixture.common
        self.session = dict(branch='F2', branch_root=str(self.root), shared_root=str(self.common),
            generation=0, checkpoint_sha256='a'*64)
        self.engine = SimpleNamespace(session=self.session)
        path = self.common/'generation_000000/F2.json'
        self.fixture.rewrite(path, lambda value: value.update(checkpoint_sha256='a'*64))
        self.submission = run.previous.ready.reference(path)
        self.fixture.rewrite(self.root/'cycle010/TRAIN_COMPLETE.json',
            lambda value: value.update(submission=self.submission))
        shared.write(self.root/'PROGRESS.json', dict(cycle=9))
        shared.write(self.root.parent/'TRAIN.json', [[]]*9+[[dict(id=name) for name in self.fixture.ids]])
        self.refs = {}
        for name in boundary.FENCES:
            path = self.fixture.directory/'fences'/(name+'.json')
            shared.write(path, dict(authentic_fixture=True, identity=run.hook.process_identity(),
                parallel_safe_snapshot_source_sha256=shared.sha(boundary.__file__)))
            self.refs[name] = run.previous.ready.reference(path)
        self.supervision = dict(native_identity=run.hook.process_identity(),
            guard_identity=run.hook.process_identity(), guard_binding=self.refs['guard_receipt'],
            owner_verified_safe_for_parallel=True, parallel_safe_snapshot_source_sha256=shared.sha(boundary.__file__),
            final_identity_bindings=[dict(identity=run.hook.process_identity(), evidence=self.refs[name])
                for name in ('final_timer', 'final_drain_timer')])
        manager = patch.object(run.client, 'current', return_value={})
        manager.start()
        self.addCleanup(manager.stop)
        device = patch.object(boundary, 'launch_device', return_value=dict(kind='cuda', physical=1,
            uuid=run.previous.math.policy.DEVICES[1], cuda_visible_devices=run.previous.math.policy.DEVICES[1]))
        device.start()
        self.addCleanup(device.stop)

    def certificate(self):
        return boundary.submission_certificate(self.root, self.engine, 10, self.submission, self.refs, self.supervision)

    def test_all_failed_outcomes_missing_parents_preserved_as_sources(self):
        certificate = self.certificate()
        self.assertEqual(certificate['status'], 'SAFE_FOR_PARALLEL')
        self.assertEqual(certificate['generation'], 0)
        self.assertEqual(certificate['submission_sha256'], self.submission['sha256'])
        self.assertEqual(certificate['bounds']['native_used'], 6)
        self.assertEqual(certificate['bounds']['parent_used'], 6)
        self.assertEqual(certificate['bounds']['native_cap'], run.previous.ready.bounds()['native_calls'])
        self.assertIn('parent_transcripts/C010_parent_1/transcript.json', certificate['preserved_files'])
        self.assertIn('cycle010/BOUNDARY.json', certificate['preserved_files'])
        self.assertEqual(certificate['identity'], run.hook.process_identity())

    def test_unfinished_parent_archive_not_parallel_safe(self):
        (self.root/'parent_queue/C010_parent_1.response.json').unlink()
        with self.assertRaisesRegex(ValueError, 'closed_source_parent_archive'):
            self.certificate()

    def test_changed_task_inventory_rejected(self):
        self.fixture.rewrite(self.root.parent/'TRAIN.json', lambda value: value[-1].reverse())
        with self.assertRaisesRegex(ValueError, 'exact_two_new_episodes'):
            self.certificate()

    def test_started_sleep_never_retried(self):
        shared.write(self.common/'generation_000000/sleep/START.json', dict(started=True))
        with self.assertRaisesRegex(ValueError, 'no_started_sleep_retry'):
            self.certificate()

    def test_completed_sleep_never_retried(self):
        shared.write(self.root/'cycle010/SHARED_SLEEP.json', dict(status='COMPLETE'))
        with self.assertRaisesRegex(ValueError, 'no_failed_or_completed_sleep_replay'):
            self.certificate()

    def test_changed_source_capture_rejected(self):
        self.fixture.rewrite(self.root/'cycle010/CALL_0001.json', lambda value: value.update(extra='changed'))
        with self.assertRaisesRegex(ValueError, 'all_actual_child_captures'):
            self.certificate()

    def test_unaccounted_charge_rejected(self):
        self.fixture.rewrite(self.root/'COUNTERS.json', lambda value: value.update(native=7))
        with self.assertRaisesRegex(ValueError, 'all_charged_reservations'):
            self.certificate()

    def test_unbound_legacy_FINAL_controller_cannot_arm_parallel(self):
        self.supervision['parallel_safe_snapshot_source_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'parallel_aware_FINAL_controller'):
            self.certificate()

    def test_caller_flag_cannot_relabel_old_timer_as_parallel_safe(self):
        path = Path(self.refs['final_drain_timer']['path'])
        self.fixture.rewrite(path, lambda value: value.pop('parallel_safe_snapshot_source_sha256'))
        self.refs['final_drain_timer'] = run.previous.ready.reference(path)
        with self.assertRaisesRegex(ValueError, 'parallel_aware_FINAL_controller'):
            self.certificate()

    def test_parallel_FINAL_never_drains_unfinished_shared_sleep(self):
        shared.write(self.common/'generation_000000/sleep/START.json', dict(schema=run.hook.SCHEMA))
        self.assertIsNone(boundary.parallel_safe_snapshot(self.fixture.plan))

    def test_parallel_FINAL_waits_all_rank_reload_ack(self):
        shared.write(self.common/'generation_000000/sleep/START.json', dict(schema=run.hook.SCHEMA))
        shared.write(self.common/'generation_000000/sleep/COMPLETE.json', dict(status='COMPLETE'))
        self.assertIsNone(boundary.parallel_safe_snapshot(self.fixture.plan))

    def test_parallel_FINAL_idle_collection_uses_existing_safe_proof(self):
        value = boundary.parallel_safe_snapshot(self.fixture.plan)
        self.assertEqual(value['kind'], 'COMPLETE_COLLECTION_ACCEPTED_WAITING_FOR_SHARED_CHECKPOINT')


@dataclass(frozen=True)
class FakeBinding:
    cycle: int
    adapter: object


class BroadcastTests(unittest.TestCase):
    def setUp(self):
        self.prior = dict(branch='F2', branch_root='/synthetic/lane1', shared_root='/synthetic/common',
            config_sha256='a'*64, generation=1)
        self.following = dict(self.prior, generation=2, checkpoint=dict(path_sha256='b'*64),
            checkpoint_sha256='b'*64, adapter={'test':'adapter'})
        self.result = dict(status='COMPLETE_ALL8_INPLACE', state=dict(generation=2,
            checkpoint=self.following['checkpoint']))
        self.identity = SimpleNamespace(verify=Mock(), document=lambda: {'test':'adapter'})
        self.raw = object()
        self.engine = SimpleNamespace(session=deepcopy(self.prior), poisoned=True,
            loaded=SimpleNamespace(engine=self.raw, optimizer=None, binding=FakeBinding(1, 'previous')),
            model=SimpleNamespace(parameters=lambda: [SimpleNamespace(requires_grad=False)]), verify_base=Mock())

    def test_verify_actual_inplace_before_readonly_identity_update_no_disk_reload(self):
        with patch.object(run.client, 'current'), \
                patch.object(run.client.native.bridge.AdapterIdentity, 'from_document', return_value=self.identity), \
                patch.object(run.client.native, 'observe_adapter', return_value=self.identity) as observe:
            result = run.adopt_broadcast(self.engine, self.following, self.result)
        observe.assert_called_once_with(self.raw, self.identity)
        self.assertEqual(self.engine.loaded.binding.cycle, 2)
        self.assertIs(self.engine.loaded.engine, self.raw)
        self.assertFalse(self.engine.poisoned)
        self.assertFalse(result['reloaded_from_disk'])
        self.assertIsNone(result['optimizer'])

    def test_bad_actual_hash_keeps_poisoned_original_session(self):
        with patch.object(run.client, 'current'), \
                patch.object(run.client.native.bridge.AdapterIdentity, 'from_document', return_value=self.identity), \
                patch.object(run.client.native, 'observe_adapter', return_value=object()):
            with self.assertRaisesRegex(ValueError, 'actual_broadcast_hash'):
                run.adopt_broadcast(self.engine, self.following, self.result)
        self.assertTrue(self.engine.poisoned)
        self.assertEqual(self.engine.session, self.prior)

    def test_no_skipped_publication(self):
        self.following['generation'] = 3
        with self.assertRaisesRegex(ValueError, 'one_actual_committed_publication'):
            run.adopt_broadcast(self.engine, self.following, self.result)

    def test_no_foreign_branch_publication(self):
        self.following['branch'] = 'A2'
        with self.assertRaisesRegex(ValueError, 'same_branch_common'):
            run.adopt_broadcast(self.engine, self.following, self.result)

    def test_no_local_optimizer(self):
        self.engine.loaded.optimizer = object()
        with patch.object(run.client, 'current'):
            with self.assertRaisesRegex(ValueError, 'no_math_optimizer'):
                run.adopt_broadcast(self.engine, self.following, self.result)


if __name__ == '__main__':
    unittest.main()
