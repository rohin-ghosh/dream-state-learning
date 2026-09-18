from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import fcntl
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r118_shared_run as run
from gpu import orch_math_feedback_uptake_r118_shared_ready as ready
from gpu import orch_math_feedback_uptake_r118_shared_boundary as boundary
from tests.orch_math_feedback_uptake_r117_test import SharedMathTests


class SharedSuccessorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = SharedMathTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.lane
        self.shared = self.fixture.shared
        self.session = self.fixture.session
        self.tasks = [dict(task, question='Compute 31 times 21.') for task in self.fixture.tasks]
        run.shared.write(self.root.parent/'TRAIN.json', [self.tasks])
        run.shared.write(self.root/'CONFIG.json', dict(index=1))
        self.engine = self.fixture.engine()
        self.engine.verify_base = Mock(return_value=SimpleNamespace(document=lambda: self.session['adapter']))
        self.engine.generate = lambda messages, max_new_tokens: dict(messages=messages, prompt_tokens=2,
            raw='A recorded wrong attempt: 684.', token_ids=[3, 4], terminal=False, truncated=True)

    def test_actual_two_episode_collection_submit_reload_readout_order(self):
        order = []
        carry = dict(actor='child', split='TRAIN', text='Earlier reflection')
        following = dict(self.session, generation=1)
        def parent(lane, task, experience, cycle, episode, phase):
            order.append('parent:'+phase)
            experience.append(run.math.policy.event('parent', 'Check your approach.', 'TRAIN', {}))
        def reload(engine, session, submission):
            order.append('reload')
            engine.session = session
            return dict(shared_generation=1)
        def readout(root, session, cycle, stage):
            order.append('fresh_readout')
            self.assertEqual(session['generation'], 1)
            self.assertTrue((root/'cycle001'/'SHARED_SLEEP.json').exists())
        with patch.object(run.math, 'parent', side_effect=parent), \
                patch.object(run.math.policy.previous.original.source, 'judge', return_value={'correct': False}), \
                patch.object(run, 'wait_published', return_value=following), \
                patch.object(run.client, 'reload_at_boundary', side_effect=reload), \
                patch.object(run, 'dispatch_readout', side_effect=readout):
            result = run.run_cycle(self.root, self.engine, 1, self.tasks, carry)
        output = self.root/'cycle001'
        calls = [run.shared.read(path) for path in sorted(output.glob('CALL_*.json')) if '.request.' not in path.name]
        self.assertEqual([call['phase'] for call in calls], list(run.client.PHASES))
        self.assertEqual([call['task_id'] for call in calls], [self.tasks[0]['id']]*2+[self.tasks[1]['id']]*4)
        self.assertTrue(all(call['shared_generation'] == 0 for call in calls))
        self.assertIn('Earlier reflection', str(calls[0]['response']['messages']))
        self.assertIn('Check your approach.', str(calls[-1]['response']['messages']))
        submission = run.shared.read(self.shared/'generation_000000'/'F2.json')
        self.assertEqual(len(submission['rows']), 6)
        self.assertTrue(all(row['target'] == 'A recorded wrong attempt: 684.' for row in submission['rows']))
        self.assertEqual(order[-2:], ['reload', 'fresh_readout'])
        self.assertEqual(sum(item.startswith('parent:') for item in order), 6)
        self.assertEqual(result['actor'], 'child')
        self.assertEqual(run.shared.read(output/'COMPLETE.json')['shared_generation'], 1)
        self.assertEqual(run.shared.read(self.root/'COUNTERS.json')['native'], 6)

    def submission(self):
        self.fixture.capture_cycle()
        return self.fixture.export()

    def test_wait_does_not_advance_on_unpublished_checkpoint(self):
        submission = self.submission()
        with self.assertRaisesRegex(TimeoutError, 'original_native_deadline'):
            run.wait_published(self.session, submission, 5, now=lambda: 5, pause=Mock())

    def test_wait_rejects_skipped_generation(self):
        submission = self.submission()
        state = run.shared.read(self.shared/'STATE.json')
        state['generation'] = 2
        run.shared.write(self.shared/'STATE.json', state, replace=True)
        with self.assertRaisesRegex(ValueError, 'no_skipped'):
            run.wait_published(self.session, submission, 10, now=lambda: 1)

    def test_wait_returns_verified_exact_next_checkpoint(self):
        submission = self.submission()
        state = run.shared.read(self.shared/'STATE.json')
        state.update(generation=1, checkpoint=self.fixture.make_checkpoint('next'))
        run.shared.write(self.shared/'STATE.json', state, replace=True)
        following = run.wait_published(self.session, submission, 10, now=lambda: 1)
        self.assertEqual(following['generation'], 1)
        self.assertEqual(following['checkpoint'], state['checkpoint'])

    def test_failed_sleep_publication_never_runs_readout(self):
        with patch.object(run.client, 'collect_cycle', return_value=dict(submission={}, carry={})), \
                patch.object(run, 'wait_published', side_effect=TimeoutError('barrier')), \
                patch.object(run, 'dispatch_readout') as readout, \
                patch.object(run.client, 'reload_at_boundary') as reload:
            with self.assertRaises(TimeoutError):
                run.run_cycle(self.root, self.engine, 1, self.tasks, None)
        readout.assert_not_called()
        reload.assert_not_called()

    def setup_readout(self, stage='cycle'):
        tasks = [dict(id=f'DEV{number}', split='DEV', question='Public problem') for number in range(8)]
        run.shared.write(self.root.parent/'DEV8.json', tasks)
        run.shared.write(self.root/'cycle001'/'BOUNDARY.json', dict(original_responses=[{'raw':'past'}]*2))
        binding = self.root/'shared_readout_bindings'/'cycle_001.json'
        run.shared.write(binding, dict(session=self.session, stage=stage, cycle=1,
            resident_process=['different_process', -1, -1]))
        def batch(prompts, cap):
            return [dict(messages=prompt, raw='Full emitted reasoning\nFINAL: 651', token_ids=[5, 6, 7],
                terminal=True, truncated=False, input_truncated=False) for prompt in prompts]
        self.engine.batch = Mock(side_effect=batch)
        return binding

    def test_fresh_dev_keeps_full_raw_and_all_twenty_excluded(self):
        binding = self.setup_readout()
        with patch.object(run, 'activation'), patch.object(run.client, 'load', return_value=self.engine) as load, \
                patch.object(run, 'loaded_receipt', return_value={'adapter':'verified'}), \
                patch.object(run.math.policy, 'readout_messages', return_value=[dict(role='user',content='test')]), \
                patch.object(run.math.policy, 'enact', return_value=[]), patch.object(run.shared, 'submit') as submit:
            run.readout(self.root, binding)
        self.assertTrue(load.call_args.kwargs['readout'])
        calls = [run.shared.read(path) for path in (self.root/'readouts'/'cycle_001').glob('CALL_*.json')]
        self.assertEqual(len(calls), 20)
        self.assertEqual(sum(call['split']=='PROBE' for call in calls), 2)
        self.assertTrue(all(call['parent_free'] and call['never_rows_or_buffer'] for call in calls))
        self.assertTrue(all(call['response']['raw'] == 'Full emitted reasoning\nFINAL: 651' for call in calls))
        self.assertTrue(all(call['shared_generation'] == 0 for call in calls))
        submit.assert_not_called()

    def test_failed_batch_preserves_all_charged_denominators(self):
        binding = self.setup_readout()
        self.engine.batch.side_effect = RuntimeError('generation failed')
        with patch.object(run, 'activation'), patch.object(run.client, 'load', return_value=self.engine), \
                patch.object(run, 'loaded_receipt', return_value={}), \
                patch.object(run.math.policy, 'readout_messages', return_value=[]):
            with self.assertRaisesRegex(RuntimeError, 'generation failed'):
                run.readout(self.root, binding)
        output = self.root/'readouts'/'cycle_001'
        failures = [run.shared.read(path) for path in output.glob('CALL_*.json')]
        self.assertEqual(len(failures), 8)
        self.assertTrue(all(call['status']=='FAILED' for call in failures))
        self.assertEqual(run.shared.read(output/'FAILED.json')['attempted_native'], 8)
        self.assertEqual(run.shared.read(self.root/'COUNTERS.json')['native'], 8)

    def test_same_process_readout_rejected_before_load(self):
        binding = self.setup_readout()
        document = run.shared.read(binding)
        document['resident_process'] = run.client.native.process_identity()
        run.shared.write(binding, document, replace=True)
        with patch.object(run, 'activation'), patch.object(run.client, 'load') as load:
            with self.assertRaisesRegex(ValueError, 'fresh_readout_process'):
                run.readout(self.root, binding)
        load.assert_not_called()

    def test_no_sleep0_repeated(self):
        binding = self.setup_readout(stage='sleep0_dev')
        with patch.object(run, 'activation'), patch.object(run.client, 'load') as load:
            with self.assertRaisesRegex(ValueError, 'no_initial_readout'):
                run.readout(self.root, binding)
        load.assert_not_called()

    def test_final_not_before_original_window(self):
        binding = self.setup_readout(stage='morning_final')
        with patch.object(run, 'activation'), patch.object(run.time, 'time', return_value=run.math.policy.previous.MORNING-1), \
                patch.object(run.client, 'load') as load:
            with self.assertRaisesRegex(ValueError, 'original_final_window'):
                run.readout(self.root, binding)
        load.assert_not_called()

    def test_resident_preserves_start_cursor_carry_and43_cap(self):
        saved_carry = dict(actor='child', split='TRAIN', text='Keep this exact reflection')
        run.shared.write(self.root/'past.json', dict(own_reflection=saved_carry))
        saved = dict(next_cycle=42, empty_successor=None, carry={'path':str(self.root/'past.json')})
        document = dict(start_cycle=42, release={}, shared_learner=dict(root=str(self.shared),branch='F2'))
        run.shared.write(self.root.parent/'TRAIN.json', [self.tasks]*43, replace=True)
        run.shared.write(self.root/'COUNTERS.json', dict(native=900,parent=200))
        with patch.object(run, 'activation', return_value=document), patch.object(boundary, 'verify_release', return_value=saved), \
                patch.object(run.client, 'prepare', return_value=self.session), \
                patch.object(run.client, 'load', return_value=self.engine), \
                patch.object(run, 'loaded_receipt', return_value={}), \
                patch.object(run, 'run_cycle', side_effect=[saved_carry,saved_carry]) as cycle, \
                patch.object(run, 'dispatch_readout') as readout, \
                patch.object(run.math.policy.previous, 'MORNING', 0):
            run.resident(self.root)
        self.assertEqual([call.args[2] for call in cycle.call_args_list], [42,43])
        self.assertEqual(cycle.call_args_list[0].args[-1], saved_carry)
        self.assertEqual(readout.call_args.args[-1], 'morning_final')
        self.assertEqual(run.shared.read(self.root/'COUNTERS.json'), dict(native=900,parent=200))


class MathBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def completed(self):
        shared = run.shared
        shared.write(self.root/'COUNTERS.json', dict(native=2,parent=1))
        shared.write(self.root/'reservations'/'native_0001.json', dict(kind='native',first=1,count=2))
        shared.write(self.root/'reservations'/'parent_0001.json', dict(kind='parent',first=1,count=1))
        shared.write(self.root/'cycle003'/'COMPLETE.json', dict(status='COMPLETE',cycle=3,counters=dict(native=2,parent=1)))
        shared.write(self.root/'cycle003'/'BOUNDARY.json', dict(own_reflection='preserved'))
        output = self.root/'readouts'/'cycle_003'
        for name, data in [('COMPLETE.json',dict(actual_native=20)),('AFTER.json',{}),('MOUNTED_FINAL.json',{})]:
            shared.write(output/name,data)
        shared.write(self.root/'READOUT_cycle_003_PROCESS.json',dict(pid=999999999))
        return boundary.snapshot(self.root,3)

    def test_completed_snapshot_preserves_cursor_and_ledger(self):
        saved = self.completed()
        self.assertEqual(saved['next_cycle'], 4)
        self.assertEqual(saved['counters'], dict(native=2,parent=1))
        self.assertEqual(len(saved['reservations']),2)

    def test_empty_next_cycle_allowed_but_not_a_capture(self):
        self.completed()
        (self.root/'cycle004').mkdir()
        saved = boundary.snapshot(self.root,3)
        self.assertEqual(saved['empty_successor'],str(self.root/'cycle004'))
        (self.root/'cycle004'/'CALL_0003.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'only_empty'):
            boundary.snapshot(self.root,3)

    def test_next_charge_prevents_release(self):
        self.completed()
        run.shared.write(self.root/'COUNTERS.json',dict(native=3,parent=1),replace=True)
        with self.assertRaisesRegex(ValueError,'no_next_cycle_charges'):
            boundary.snapshot(self.root,3)

    def test_missing_after_prevents_release(self):
        self.completed()
        (self.root/'readouts'/'cycle_003'/'AFTER.json').unlink()
        with self.assertRaisesRegex(ValueError,'fully_finished'):
            boundary.snapshot(self.root,3)

    def test_reservation_gap_prevents_release(self):
        self.completed()
        run.shared.write(self.root/'reservations'/'native_0001.json',dict(kind='native',first=2,count=2),replace=True)
        with self.assertRaisesRegex(ValueError,'contiguous'):
            boundary.snapshot(self.root,3)

    def test_no_authorization_no_signal(self):
        request, auth = self.root/'REQUEST.json',self.root/'AUTH.json'
        run.shared.write(request,dict(schema='R118_MATH_BOUNDARY_V1'))
        run.shared.write(auth,dict(authorized=False))
        with patch.object(boundary.signal,'pidfd_send_signal') as signal:
            with self.assertRaisesRegex(ValueError,'agreed_exact'):
                boundary.execute(request,auth)
        signal.assert_not_called()

    def test_individual_permission_not_all_eight(self):
        request, auth = self.root/'REQUEST.json',self.root/'AUTH.json'
        run.shared.write(request,dict(schema='R118_MATH_BOUNDARY_V1'))
        run.shared.write(auth,dict(authorized=True,all_eight_ready=False,common_handoff_coordinated=True,
            request_sha256=run.shared.sha(request)))
        with self.assertRaisesRegex(ValueError,'agreed_exact'):
            boundary.authorize(request,auth)

    def test_candidate_waits_until_all_readout_batches_reserved(self):
        run.shared.write(self.root/'cycle001'/'BOUNDARY.json',{})
        output=self.root/'readouts'/'cycle_001'
        run.shared.write(output/'BATCH_0007.request.json',dict(task_ids=list(range(8))))
        self.assertIsNone(boundary.candidate(self.root))
        run.shared.write(output/'BATCH_0015.request.json',dict(task_ids=list(range(8))))
        run.shared.write(output/'BATCH_0023.request.json',dict(task_ids=list(range(2))))
        run.shared.write(output/'BATCH_0025.request.json',dict(task_ids=list(range(2))))
        self.assertEqual(boundary.candidate(self.root),1)

    @unittest.skipUnless(hasattr(os,'pidfd_open'),'Linux pidfd required')
    def test_real_owned_CPU_pidfd_rejects_drift_then_stops_and_resumes(self):
        process=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])
        descriptor=os.pidfd_open(process.pid)
        try:
            expected=boundary.pinned.identity(process.pid)
            with self.assertRaisesRegex(ValueError,'identity_before_stop'):
                boundary.pinned.stop(descriptor,dict(expected,start_ticks='wrong'))
            boundary.pinned.stop(descriptor,expected)
            self.assertIn(boundary.pinned.process_state(process.pid),('T','t'))
            signal.pidfd_send_signal(descriptor,signal.SIGCONT)
            signal.pidfd_send_signal(descriptor,signal.SIGTERM)
            self.assertTrue(boundary.pinned.wait_exit(descriptor,3))
            process.wait(timeout=3)
        finally:
            if process.poll() is None:
                signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                process.terminate()
                process.wait(timeout=3)
            os.close(descriptor)

    def test_real_counter_lock_blocks_new_reservation(self):
        path=self.root/'COUNTERS.lock'
        marker=self.root/'NEW_RESERVATION'
        script='import fcntl,sys,pathlib; lock=open(sys.argv[1],"a"); fcntl.flock(lock,fcntl.LOCK_EX); pathlib.Path(sys.argv[2]).write_text("reserved")'
        with path.open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            process=subprocess.Popen([sys.executable,'-c',script,str(path),str(marker)])
            try:
                time.sleep(.1)
                self.assertIsNone(process.poll())
                self.assertFalse(marker.exists())
            finally:
                fcntl.flock(lock,fcntl.LOCK_UN)
                process.wait(timeout=3)
        self.assertTrue(marker.exists())

    @unittest.skipUnless(hasattr(os,'pidfd_open'),'Linux pidfd required')
    def test_execute_releases_only_pinned_CPU_pair_after_saved_boundary(self):
        self.completed()
        children=[subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']) for unused in range(2)]
        actor,supervisor=[boundary.pinned.identity(child.pid) for child in children]
        request=dict(root=str(self.root),branch='F2',actor=actor,supervisor=supervisor,expires_unix=time.time()+10)
        request_path=self.root/'handoff'/'REQUEST.json'
        auth_path=self.root/'handoff'/'AUTH.json'
        run.shared.write(request_path,request)
        run.shared.write(auth_path,dict(synthetic_CPU_only=True))
        try:
            with patch.object(boundary,'authorize',return_value=request), \
                    patch.object(boundary,'process',side_effect=lambda pid,*args:boundary.pinned.identity(pid)), \
                    patch.object(boundary,'candidate',return_value=3):
                released=boundary.execute(request_path,auth_path)
            self.assertEqual(released['status'],'RELEASED')
            self.assertTrue(released['no_quota_reset'])
            self.assertEqual(run.shared.read(self.root/'COUNTERS.json'),dict(native=2,parent=1))
            self.assertEqual(run.shared.read(released['boundary']['path'])['next_cycle'],4)
            for child in children:
                child.wait(timeout=3)
        finally:
            for child in children:
                if child.poll() is None:
                    os.kill(child.pid,signal.SIGCONT)
                    child.terminate()
                    child.wait(timeout=3)


class MathReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)/'lane1'
        self.root.mkdir()
        self.source=self.root.parent/'source'
        for name in ready.REQUIRED:
            path=self.source/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text('pass\n')
        run.shared.write(self.root.parent/'COMMON_CONTRACT.json',dict(original=True))
        run.shared.write(self.root.parent/'TRAIN.json',[[dict(id=f'TRAIN{cycle}_{episode}') for episode in range(2)]
            for cycle in range(43)])
        run.shared.write(self.root.parent/'sealed'/'READOUT_ROSTER.json',dict(dev_ids=['DEV'],final_ids=['FINAL']))
        self.tests=self.source/'CPU_TESTS.json'
        run.shared.write(self.tests,dict(source_files=ready.inventory(self.source),passed=True,
            cuda_initialized=False,native_calls=0))

    def publish(self):
        with patch.object(ready,'branch_for',return_value='F2'),patch.object(ready,'predecessor',return_value={}):
            return ready.publish(self.root,self.source,self.tests)

    def test_ready_runnable_schema_without_common_configuration(self):
        result=self.publish()
        self.assertEqual(result['schema'],'R116_SHARED_CLIENT_READY_V1')
        self.assertEqual(len(result['train_ids']),86)
        self.assertEqual(result['excluded_ids'],['DEV','FINAL'])
        self.assertFalse(result['active_shared_client'])
        self.assertTrue(result['ready_for_initialization'])
        self.assertEqual(result['command_module'],'gpu.orch_math_feedback_uptake_r118_shared_run')
        self.assertEqual(result['inherited_bounds']['cycles'],43)
        self.assertEqual(result['activation_sidecar'],'SHARED_ACTIVATION.json')
        self.assertIn('source_files',result)
        self.assertIn('predecessor_plan_sha256',result)

    def test_changed_executable_rejected(self):
        (self.source/ready.REQUIRED[1]).write_text('changed\n')
        with self.assertRaisesRegex(ValueError,'bound_native_CPU_tests'):
            self.publish()

    def test_gpu_initialized_test_receipt_rejected(self):
        tests=run.shared.read(self.tests)
        tests['cuda_initialized']=True
        run.shared.write(self.tests,tests,replace=True)
        with self.assertRaisesRegex(ValueError,'bound_native_CPU_tests'):
            self.publish()

    def test_held_overlap_rejected(self):
        run.shared.write(self.root.parent/'sealed'/'READOUT_ROSTER.json',dict(dev_ids=['TRAIN0_0'],final_ids=['FINAL']),replace=True)
        with self.assertRaisesRegex(ValueError,'DEV_FINAL_never_training'):
            self.publish()


if __name__=='__main__':
    unittest.main()
