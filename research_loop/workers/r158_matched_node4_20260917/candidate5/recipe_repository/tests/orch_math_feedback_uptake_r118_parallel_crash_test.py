from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r118_parallel_crash as crash
from tests import orch_math_feedback_uptake_r118_final_drain_test as fixtures


life, shared = crash.life, crash.shared


class CrashTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.BoundaryTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root,self.common = self.fixture.root,self.fixture.common
        self.service = self.fixture.directory/'service'
        self.service.mkdir()
        self.old = dict(native=dict(pid=123,start_ticks=1,boot_id='test'),
            guard=dict(pid=124,start_ticks=2,boot_id='test'))
        oldpath = self.fixture.directory/'old.json'
        shared.write(oldpath,self.old)
        self.documents = dict(native_launch=dict(identity=self.old['native']),
            guard_receipt=dict(identity=self.old['guard']))
        self.plan = dict(root=str(self.root),branch='F2',old_drain_plan=life.ref(oldpath),
            protected_refs={},inherited_bounds=life.previous.ready.bounds(),
            fresh_peer_rng_policy='DETERMINISTIC_NEW_STREAM_NOT_OLD_PEER_RNG')
        for name in ('PROGRESS.json','CONFIG.json','ACTIVATION.json','SHARED_ACTIVATION.json',
            'SHARED_LAUNCH.json','SHARED_CLIENT_READY.json','R118_SHARED_ADMISSION_REPAIR_LAUNCH.json'):
            shared.write(self.root/name,dict(old=True))
        shared.write(self.root/'SHARED_FAILED.json',dict(type='ValueError',error='unchanged_adapter_recipe',
            counters=dict(native=6,parent=6)))
        for name in ('SHARED_RESIDENT_TERMINAL.json','SHARED_TERMINAL.json'):
            shared.write(self.root/name,dict(status='FAILED',local_optimizer_steps=0,counters=dict(native=6,parent=6)))
        submission = self.common/'generation_000000/F2.json'
        self.fixture.rewrite(submission,lambda value:value.update(checkpoint_sha256='a'*64))
        self.fixture.rewrite(self.fixture.cycle/'TRAIN_COMPLETE.json',lambda value:value.update(
            shared_branch='F2',submission=life.ref(submission)))
        self.state = dict(generation=1,checkpoint=dict(path_sha256='b'*64))
        shared.write(self.common/'generation_000000/sleep/COMPLETE.json',dict(state=self.state,same_optimizer=True))
        self.prior = self.fixture.directory/'prior'
        self.following = self.fixture.directory/'following'
        shared.write(self.prior/'adapter_config.json',dict(target_modules=['v_proj','q_proj'],r=8))
        shared.write(self.following/'adapter_config.json',dict(target_modules=['q_proj','v_proj'],r=8))
        initial_path = self.fixture.directory/'initial_checkpoint.json'
        shared.write(initial_path,dict(adapter=dict(path=str(self.prior))))
        shared.write(self.common/'INITIALIZED.json',dict(state=dict(checkpoint=dict(
            path=str(initial_path),path_sha256='a'*64))))
        self.session = dict(generation=1,checkpoint_sha256='b'*64,adapter=dict(path=str(self.following)))
        for obj,name,value in ((life,'alive',Mock(return_value=False)),
            (life,'unused_old_FINAL',Mock()),(life.drain,'live_readout_identities',Mock(return_value=[])),
            (life.previous.ready,'COMMON_ROOT',self.common),(life.boundary,'fences',Mock(return_value=self.documents)),
            (life.client,'prepare',Mock(return_value=self.session)),(life.client,'current',Mock(return_value=self.state)),
            (shared,'checked_checkpoint',Mock())):
            manager=patch.object(obj,name,value)
            manager.start()
            self.addCleanup(manager.stop)

    def test_crash_accepts_no_DEV_only_with_actual_commit_and_all_sources(self):
        result=crash.inspect(self.plan)
        self.assertEqual(result['next_cycle'],11)
        self.assertEqual(result['old_DEV_status'],'NOT_RUN')
        self.assertIsNone(result['mounted_checkpoint_sha256'])
        self.assertFalse(result['fresh_dev_complete'])
        self.assertIn('SHARED_FAILED.json',result['preserved_files'])
        self.assertIn('cycle010/CALL_0001.json',result['preserved_files'])
        self.assertEqual(result['counters'],dict(native=6,parent=6))

    def test_live_predecessor_rejected_without_signal(self):
        with patch.object(life,'alive',return_value=True),patch.object(life,'terminate_owned') as terminate:
            with self.assertRaisesRegex(ValueError,'crashed_predecessor'):
                crash.inspect(self.plan)
        terminate.assert_not_called()

    def test_real_recipe_change_rejected(self):
        self.fixture.rewrite(self.following/'adapter_config.json',lambda value:value.update(r=16))
        with self.assertRaisesRegex(ValueError,'unchanged_adapter_recipe'):
            crash.inspect(self.plan)

    def test_other_failure_not_reclassified(self):
        self.fixture.rewrite(self.root/'SHARED_FAILED.json',lambda value:value.update(error='OOM'))
        with self.assertRaisesRegex(ValueError,'exact_nonmaterial'):
            crash.inspect(self.plan)

    def test_any_readout_attempt_not_retried_or_reported_unrun(self):
        shared.write(self.root/'readouts/cycle_010/BEFORE.json',dict(actual_attempt=True))
        with self.assertRaisesRegex(ValueError,'OLD_DEV_NOT_RUN'):
            crash.inspect(self.plan)

    def test_changed_reservation_rejected(self):
        self.fixture.rewrite(self.root/'reservations/native_0002.json',lambda value:value.update(count=2))
        with self.assertRaisesRegex(ValueError,'contiguous_original'):
            crash.inspect(self.plan)

    def test_parent_archive_hash_drift_rejected(self):
        self.fixture.rewrite(self.root/'parent_transcripts/C010_parent_1/transcript.json',lambda value:value.update(changed=True))
        with self.assertRaisesRegex(ValueError,'parent_archive_hash'):
            crash.inspect(self.plan)

    def test_next_generation_submission_cannot_be_dropped(self):
        shared.write(self.common/'generation_000001/F2.json',dict(accepted=True))
        with self.assertRaisesRegex(ValueError,'no_next_submission'):
            crash.inspect(self.plan)

    def test_incomplete_commit_rejected(self):
        self.fixture.rewrite(self.common/'generation_000000/sleep/COMPLETE.json',lambda value:value.update(same_optimizer=False))
        with self.assertRaisesRegex(ValueError,'actual_shared_commit'):
            crash.inspect(self.plan)

    def test_release_preserves_originals_without_signalling_or_fake_DEV(self):
        permission=dict(crashed_postcommit_recovery=True,checkpoint_sha256='b'*64)
        before={name:shared.sha(self.root/name) for name in ('COUNTERS.json','PROGRESS.json','SHARED_FAILED.json')}
        with patch.object(life,'plan_for',return_value=self.plan), \
            patch.object(life,'authorization',return_value=permission),patch.object(life,'terminate_owned') as terminate:
            result=crash.release(self.service,dict(path='explicit-Main',sha256='c'*64))
        terminate.assert_not_called()
        self.assertEqual(life.checked(result)['status'],'RELEASED')
        disposition=shared.read(self.root/'R118_CRASH_POSTCOMMIT_DISPOSITION.json')
        cursor=shared.read(self.root/'R118_CRASH_RECOVERY_CURSOR.json')
        self.assertEqual(disposition['schema'],'R118_POSTCOMMIT_EVAL_DISPOSITION_V1')
        self.assertEqual(disposition['evaluations'],dict(DEV='NOT_ATTEMPTED',OPEN='NOT_ATTEMPTED'))
        self.assertFalse(disposition['replay_train'])
        self.assertEqual(cursor['next_cycle'],11)
        self.assertEqual(cursor['native_used'],6)
        self.assertEqual(before,{name:shared.sha(self.root/name) for name in before})
        self.assertFalse((self.fixture.cycle/'COMPLETE.json').exists())
        self.assertFalse((self.root/'readouts/cycle_010/COMPLETE.json').exists())
        self.assertTrue(life.checked(result)['final_custody_pending'])


if __name__=='__main__':
    unittest.main()
