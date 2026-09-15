from copy import deepcopy
from contextlib import ExitStack
import inspect
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r118_parallel_lifecycle as life
from gpu import orch_math_feedback_uptake_r118_parallel_native as native
from gpu import orch_math_feedback_uptake_r118_parallel_final as final
from gpu import orch_math_feedback_uptake_r118_parallel_broker as broker


shared = life.shared


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.plan = dict(root=str(self.folder), plan_sha256='a'*64)
        self.permission = dict(schema='R118_MATH_PARALLEL_FRESH_EXEC_AUTH_V1', authorized=True,
            common_handoff_coordinated=True, actions=['RELEASE','LAUNCH'], root=str(self.folder),
            plan_sha256='a'*64, fresh_peer_rng_policy='DETERMINISTIC_NEW_STREAM_NOT_OLD_PEER_RNG',
            lifecycle_rebinding_authorized=True, not_before_unix=1, expires_unix=100)

    def reference(self):
        path = self.folder/'AUTH.json'
        path.write_text(json.dumps(self.permission))
        return life.ref(path)

    def test_Main_bound_future_release_authorization(self):
        value = life.authorization(self.reference(), self.plan, 'RELEASE', clock=lambda:50)
        self.assertTrue(value['authorized'])

    def test_no_current_signals_before_authorized_future_boundary(self):
        with patch.object(life.signal, 'pidfd_send_signal') as sent:
            with self.assertRaisesRegex(ValueError, 'bounded_future_authorization'):
                life.authorization(self.reference(), self.plan, 'RELEASE', clock=lambda:0)
        sent.assert_not_called()

    def test_no_expired_authorization(self):
        with self.assertRaisesRegex(ValueError, 'bounded_future_authorization'):
            life.authorization(self.reference(), self.plan, 'LAUNCH', clock=lambda:100)

    def test_root_and_plan_cannot_change(self):
        self.permission['plan_sha256'] = 'b'*64
        with self.assertRaisesRegex(ValueError, 'explicit_Main_scoped'):
            life.authorization(self.reference(), self.plan, 'RELEASE', clock=lambda:50)

    def test_old_peer_rng_continuity_not_falsely_accepted(self):
        self.permission['fresh_peer_rng_policy'] = 'PRESERVE_OLD_RNG'
        with self.assertRaisesRegex(ValueError, 'fresh_exec_and_FINAL'):
            life.authorization(self.reference(), self.plan, 'LAUNCH', clock=lambda:50)

    def test_no_FINAL_rebinding_permission_rejected(self):
        self.permission['lifecycle_rebinding_authorized'] = False
        with self.assertRaisesRegex(ValueError, 'fresh_exec_and_FINAL'):
            life.authorization(self.reference(), self.plan, 'RELEASE', clock=lambda:50)


class ProcessTests(unittest.TestCase):
    def test_pid_reuse_or_exec_drift_never_signals(self):
        expected = dict(pid=10, uid=os.getuid(), start_ticks=10)
        with patch.object(life, 'identity', return_value=dict(expected, start_ticks=11)), \
                patch.object(life.signal, 'pidfd_send_signal') as sent:
            with self.assertRaisesRegex(ValueError, 'exact_owned'):
                life.terminate_owned(expected)
        sent.assert_not_called()

    def test_real_owned_pidfd_leaves_foreign_sentinel(self):
        children = [subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(60)'],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='')) for unused in range(2)]
        try:
            time.sleep(.05)
            expected = life.identity(children[0].pid)
            life.cpu_only(expected)
            life.terminate_owned(expected)
            self.assertFalse(life.alive(expected))
            self.assertIsNone(children[1].poll())
        finally:
            for child in children:
                if child.poll() is None:
                    child.terminate()
                child.wait(timeout=5)

    def test_GPU_visible_process_not_CPU_timer(self):
        child = subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(60)'],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='GPU-synthetic'))
        try:
            time.sleep(.05)
            with self.assertRaisesRegex(ValueError, 'empty_startup_CVD'):
                life.cpu_only(life.identity(child.pid))
            self.assertIsNone(child.poll())
        finally:
            child.terminate()
            child.wait(timeout=5)


class FreshBootstrapTests(unittest.TestCase):
    def test_central_seed_restore_once_before_collection_no_local_optimizer(self):
        engine = SimpleNamespace(session=dict(branch='F2',shared_root='/synthetic/common'),
            loaded=SimpleNamespace(engine=object()), verify_base=Mock())
        document = dict(bootstrap_path='/synthetic/lane1/BOOTSTRAP.json')
        reference = dict(owners={'F2':dict(bootstrap_path=document['bootstrap_path'])})
        order = []
        with patch.dict(os.environ, R118_PARALLEL_SESSION='/synthetic/SESSION.json',
                R118_PARALLEL_SESSION_SHA256='a'*64,R118_PARALLEL_BRANCH='F2'), \
                patch.object(life, 'checked', return_value=reference), \
                patch.object(life.hook, 'bootstrap_fresh_actor', side_effect=lambda **kwargs: order.append(('bootstrap',kwargs)) or {
                    'status':'BOOTSTRAP_VERIFIED','startup_action':'COLLECT_NEW_TWO_EPISODES',
                    'canonical_adapter_actually_verified':True}), \
                patch.object(life.hook, 'wait_fresh_collection_go', side_effect=lambda *args,**kwargs:order.append(('GO',args))):
            result = native.bootstrap(engine, document, Mock())
        self.assertEqual([item[0] for item in order], ['bootstrap','GO'])
        self.assertIs(order[0][1]['engine'], engine.loaded.engine)
        self.assertIsNone(order[0][1]['optimizer'])
        self.assertEqual(result['status'], 'BOOTSTRAP_VERIFIED')
        engine.verify_base.assert_called_once()

    def test_intermediate_hook_rejected_before_bootstrap(self):
        with patch.object(shared,'sha',return_value='f'*64),patch.object(life.hook,'bootstrap_fresh_actor') as called:
            with self.assertRaisesRegex(ValueError,'finalized_Herschel_v4'):
                native.bootstrap(SimpleNamespace(),{},Mock())
        called.assert_not_called()

    def test_wrong_or_missing_startup_action_cannot_reach_GO(self):
        for result in ({'canonical_adapter_actually_verified':True},
                {'startup_action':'RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS',
                 'canonical_adapter_actually_verified':True},
                {'startup_action':'COLLECT_NEW_TWO_EPISODES','canonical_adapter_actually_verified':False}):
            engine=SimpleNamespace(session=dict(branch='F2',shared_root='/synthetic/common'),
                loaded=SimpleNamespace(engine=object()),verify_base=Mock())
            document=dict(bootstrap_path='/synthetic/BOOTSTRAP.json')
            with self.subTest(result=result),patch.dict(os.environ,R118_PARALLEL_SESSION='/synthetic/SESSION.json',
                    R118_PARALLEL_SESSION_SHA256='a'*64,R118_PARALLEL_BRANCH='F2'), \
                    patch.object(life,'checked',return_value=dict(owners={'F2':document})), \
                    patch.object(life.hook,'bootstrap_fresh_actor',return_value=result), \
                    patch.object(life.hook,'wait_fresh_collection_go') as go:
                with self.assertRaisesRegex(ValueError,'new_cycle_startup_action'):
                    native.bootstrap(engine,document,Mock())
            go.assert_not_called()

    def test_central_wrong_branch_rejected_before_bootstrap(self):
        engine = SimpleNamespace(session=dict(branch='F2'))
        with patch.dict(os.environ, R118_PARALLEL_SESSION='/synthetic/SESSION.json',
                R118_PARALLEL_SESSION_SHA256='a'*64,R118_PARALLEL_BRANCH='A2'), \
                patch.object(life.hook, 'bootstrap_fresh_actor') as bootstrap:
            with self.assertRaisesRegex(ValueError, 'fresh_branch_binding'):
                native.bootstrap(engine, {}, Mock())
        bootstrap.assert_not_called()

    def test_no_private_rng_seed_or_optimizer_factory(self):
        source = inspect.getsource(native)
        for text in ('random.seed(', 'manual_seed(', 'AdamW(', 'init_process_group('):
            self.assertNotIn(text, source)

    def test_startup_does_not_reacquire_central_dispatcher_lock(self):
        self.assertNotIn('client.prepare(', inspect.getsource(native.resident))
        self.assertIn('client.current(session)', inspect.getsource(native.resident))


class ActivationWaitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.service = Path(self.temporary.name)
        self.inbox = self.service/'inbox'
        self.document = dict(activation_directory=str(self.inbox),train_end_unix=100)
        self.certificate_path = self.service/'participant.json'
        shared.write(self.certificate_path, dict(generation=1,branch='F2'))
        self.certificate = life.ref(self.certificate_path)

    def test_exact_existing_Main_generation_reference_contract(self):
        activation = self.service/'activation.json'
        shared.write(activation, dict(generation=1,participants={'F2':self.certificate}))
        reference = life.ref(activation)
        shared.write(self.inbox/'generation_000001.ref.json', reference)
        self.assertEqual(native.wait_activation(self.service,self.document,self.certificate,100,clock=lambda:1), reference)

    def test_autoarm_publishes_actual_certificate_via_shared_hook(self):
        document = dict(self.document,campaign=dict(path='/synthetic/campaign.json',sha256='b'*64))
        result = dict(path='/synthetic/ACTIVATION.json',sha256='c'*64)
        with patch.object(life.hook,'await_campaign_activation',return_value=result) as await_hook:
            self.assertEqual(native.wait_activation(self.service,document,self.certificate,100,clock=lambda:1),result)
        self.assertEqual(await_hook.call_args.args,
            ('/synthetic/campaign.json','b'*64,'F2',self.certificate))
        await_hook.call_args.kwargs['check']('before_join')
        shared.write(self.service/'STOP_REQUEST.json',dict(reason='deadline'))
        with self.assertRaisesRegex(ValueError,'bounded_autoarm_wait'):
            await_hook.call_args.kwargs['check']('after_stop')

    def test_retirement_does_not_launch_collective(self):
        shared.write(self.service/'STOP_REQUEST.json', dict(reason='deadline'))
        with self.assertRaisesRegex(TimeoutError, 'retirement_no_collective'):
            native.wait_activation(self.service,self.document,self.certificate,100,clock=lambda:1)

    def test_no_activation_replay_after_deadline(self):
        with self.assertRaisesRegex(TimeoutError, 'bounded_Main_activation'):
            native.wait_activation(self.service,self.document,self.certificate,100,clock=lambda:100)

    def test_wrong_generation_activation_rejected(self):
        activation = self.service/'activation.json'
        shared.write(activation, dict(generation=0,participants={'F2':self.certificate}))
        shared.write(self.inbox/'generation_000001.ref.json', life.ref(activation))
        with self.assertRaisesRegex(ValueError, 'exact_Main_parallel_activation'):
            native.wait_activation(self.service,self.document,self.certificate,100,clock=lambda:1)


class FinalCustodyTests(unittest.TestCase):
    def test_namespace_isolation_does_not_hotpatch_original_FINAL(self):
        original_validate = final.original.validate
        original_output = final.original.OUTPUT
        functions = final.original_functions()
        self.assertIs(final.original.validate, original_validate)
        self.assertEqual(final.original.OUTPUT, original_output)
        self.assertIs(functions['native'].__globals__['release'], final.release)
        self.assertIs(functions['native'].__globals__['validate'], final.validate)
        self.assertEqual(functions['native'].__code__, final.original.native.__code__)
        self.assertEqual(functions['capture'].__code__, final.original.capture.__code__)
        self.assertEqual(functions['materialize'].__code__, final.original.materialize.__code__)

    def test_original_final_window_and_calls_unchanged(self):
        self.assertEqual(final.original.START,1789491600)
        self.assertEqual(final.original.END,1789492800)
        functions = final.original_functions()
        self.assertEqual(functions['DECODER'], final.original.DECODER)
        self.assertEqual(functions['FINAL_IDS'], final.original.FINAL_IDS)
        self.assertEqual(functions['FINAL_FILE_SHA'], final.original.FINAL_FILE_SHA)

    def test_old_separate_FINAL_charge_blocks_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            older, current = folder/'older', folder/'current'
            shared.write(older/'PLAN.json',dict(root=str(older)))
            shared.write(current/'PLAN.json',dict(root=str(current),previous_evaluation_plan=life.ref(older/'PLAN.json')))
            shared.write(older/'LEDGER.json',dict(native=8))
            plan = dict(root=str(folder/'lane1'),old_evaluation_plan=life.ref(current/'PLAN.json'))
            with self.assertRaisesRegex(ValueError, 'old_separate_FINAL_charged'):
                life.unused_old_FINAL(plan)

    def test_live_NEW_native_blocks_FINAL_even_if_old_released(self):
        with tempfile.TemporaryDirectory() as directory:
            service = Path(directory)
            shared.write(service/'LAUNCH.json',dict(identity={'pid':1}))
            shared.write(service/'GUARD_STARTED.json',dict(identity={'pid':2}))
            with patch.object(life,'released'), patch.object(life,'alive',return_value=True):
                with self.assertRaisesRegex(ValueError,'NEW_native_guard_still_live'):
                    final.release(dict(parallel_service=str(service)))

    def test_missing_actual_NEW_clean_release_never_fabricated(self):
        with tempfile.TemporaryDirectory() as directory:
            service = Path(directory)
            shared.write(service/'LAUNCH.json',dict(identity={'pid':1}))
            shared.write(service/'GUARD_STARTED.json',dict(identity={'pid':2}))
            with patch.object(life,'released'), patch.object(life,'alive',return_value=False):
                with self.assertRaises(FileNotFoundError):
                    final.release(dict(parallel_service=str(service)))
            self.assertFalse((service/'CLEAN_RELEASE.json').exists())


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.service=Path(self.temporary.name)
        self.root=self.service/'lane1'
        self.root.mkdir()
        self.plan=dict(root=str(self.root),plan_sha256='a'*64,old_drain_plan={},protected_refs={})
        self.old=dict(native=dict(pid=101,uid=os.getuid()),guard=dict(pid=100,uid=os.getuid()))
        self.permission=dict(expires_unix=100,checkpoint_sha256='b'*64)

    def test_no_boundary_no_signal(self):
        with patch.object(life,'plan_for',return_value=self.plan),patch.object(life,'authorization',return_value=self.permission), \
                patch.object(life,'checked',return_value=self.old),patch.object(life.boundary,'inspect_completed',return_value=None), \
                patch.object(signal,'pidfd_send_signal') as sent:
            result=life.release(self.service,{},clock=lambda:1)
        self.assertEqual(result['status'],'NOT_AT_SAFE_BOUNDARY')
        sent.assert_not_called()

    def test_raced_hold_resumes_both_no_termination(self):
        with patch.object(life,'plan_for',return_value=self.plan),patch.object(life,'authorization',return_value=self.permission), \
                patch.object(life,'checked',return_value=self.old), \
                patch.object(life.boundary,'inspect_completed',side_effect=[dict(checkpoint_sha256='b'*64),None]), \
                patch.object(life,'exact_live'),patch.object(os,'pidfd_open',side_effect=[1000,1001]),patch.object(os,'close'), \
                patch.object(life.drain.pinned,'process_state',return_value='T'),patch.object(signal,'pidfd_send_signal') as sent:
            result=life.release(self.service,{},clock=lambda:1)
        self.assertEqual(result['status'],'RACED_NOT_RELEASED')
        self.assertEqual(sorted(item.args[1] for item in sent.call_args_list),
            sorted([signal.SIGSTOP,signal.SIGSTOP,signal.SIGCONT,signal.SIGCONT]))
        self.assertFalse((self.service/'RELEASED.json').exists())

    def test_wrong_Main_checkpoint_never_holds(self):
        with patch.object(life,'plan_for',return_value=self.plan),patch.object(life,'authorization',return_value=self.permission), \
                patch.object(life,'checked',return_value=self.old), \
                patch.object(life.boundary,'inspect_completed',return_value=dict(checkpoint_sha256='c'*64)), \
                patch.object(signal,'pidfd_send_signal') as sent:
            with self.assertRaisesRegex(ValueError,'Main_actual_commit'):
                life.release(self.service,{},clock=lambda:1)
        sent.assert_not_called()

    def test_real_release_preserves_sentinel_and_requires_authentic_guard_terminal(self):
        script = self.service/'owned_guard.py'
        script.write_text('import json,pathlib,subprocess,sys,time\n'
            'root=pathlib.Path(sys.argv[1])\n'
            'child=subprocess.Popen([sys.executable,"-B","-c","import time; time.sleep(60)"])\n'
            '(root/"pid.json").write_text(json.dumps({"pid":child.pid}))\n'
            'child.wait()\n'
            '(root/"SHARED_TERMINAL.json").write_text(json.dumps({"status":"OWNED_EXIT_OBSERVED"}))\n')
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
        guardian = subprocess.Popen([sys.executable,'-B',str(script),str(self.root)],env=environment)
        timers = [subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(60)'],
            env=environment) for unused in range(4)]
        native_identity = None
        try:
            until = time.time()+5
            while not (self.root/'pid.json').exists():
                self.assertLess(time.time(),until)
                time.sleep(.01)
            native_identity = life.identity(shared.read(self.root/'pid.json')['pid'])
            old = dict(native=native_identity,guard=life.identity(guardian.pid))
            old_path = self.service/'old_plan.json'
            shared.write(old_path,old)
            self.plan['old_drain_plan'] = life.ref(old_path)
            self.plan['fresh_peer_rng_policy'] = 'DETERMINISTIC_NEW_STREAM_NOT_OLD_PEER_RNG'
            self.plan['old_timer_records'] = []
            for index,timer in enumerate(timers[:3]):
                path = self.service/f'timer{index}.json'
                shared.write(path,dict(identity=life.identity(timer.pid)))
                self.plan['old_timer_records'].append(life.ref(path))
            shared.write(self.root/'COUNTERS.json',dict(native=26,parent=6))
            observed = dict(checkpoint_sha256='b'*64,
                preserved_files={'COUNTERS.json':shared.sha(self.root/'COUNTERS.json')})
            with patch.object(life,'plan_for',return_value=self.plan), \
                    patch.object(life,'authorization',return_value=self.permission), \
                    patch.object(life.boundary,'inspect_completed',return_value=observed), \
                    patch.object(life,'unused_old_FINAL'), \
                    patch.object(life.drain,'live_readout_identities',return_value=[]):
                result = life.release(self.service,{},clock=lambda:1)
            document = life.checked(result)
            self.assertEqual(document['status'],'RELEASED')
            self.assertEqual(life.checked(document['authentic_guard_terminal'])['status'],'OWNED_EXIT_OBSERVED')
            self.assertEqual(len(document['retired_FINAL_timers']),3)
            self.assertFalse(life.alive(native_identity))
            self.assertIsNone(timers[3].poll())
            self.assertFalse(document['old_peer_rng_saved'])
        finally:
            if native_identity is not None and life.alive(native_identity):
                life.terminate_owned(native_identity,force=True)
            for child in [guardian,*timers]:
                if child.poll() is None:
                    child.terminate()
                child.wait(timeout=5)


class EntrypointTests(unittest.TestCase):
    def test_executable_CLIs_are_inert_for_help(self):
        for module in (life.__name__,native.__name__,final.__name__,broker.__name__):
            with self.subTest(module=module):
                result=subprocess.run([sys.executable,'-B','-m',module,'--help'],
                    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),
                    capture_output=True,text=True,timeout=20)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertIn('usage:',result.stdout)


class UnlaunchedSourceUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.service=self.root/'service'
        self.branch_root=self.root/'lane1'
        self.plan=dict(schema='R118_MATH_FRESH_EXEC_PLAN_V1',branch='F2',root=str(self.branch_root),
            source_root=str(self.root/'old_source'),source_manifest=dict(path='original',sha256='a'*64),
            tests_receipt=dict(path='old_tests',sha256='b'*64),inherited_bounds=life.previous.ready.bounds(),
            train_end_unix=life.TRAIN_END)
        shared.write(self.service/'PLAN.json',self.plan)
        shared.write(self.service/'RELEASED.json',dict(status='RELEASED'))
        self.upgrade=dict(schema='R118_MATH_UNLAUNCHED_SOURCE_UPGRADE_V1',
            original_plan=life.ref(self.service/'PLAN.json'),previous_source_root=self.plan['source_root'],
            previous_source_manifest=self.plan['source_manifest'],source_root=str(life.SOURCE),
            source_manifest=dict(path='new_manifest',sha256='c'*64),tests_receipt=dict(path='new_tests',sha256='d'*64),
            release=life.ref(self.service/'RELEASED.json'))
        for obj,name,value in ((life,'service_for',Mock(return_value=self.service)),
                (life.client,'BRANCHES',dict(F2=self.branch_root)),(life,'verify_source',Mock())):
            manager=patch.object(obj,name,value)
            manager.start()
            self.addCleanup(manager.stop)

    def test_old_plan_and_release_unchanged_after_explicit_source_overlay(self):
        original=life.ref(self.service/'PLAN.json')
        shared.write(self.service/'SOURCE_UPGRADE.json',self.upgrade)
        result=life.plan_for(self.service)
        self.assertEqual(result['source_manifest'],self.upgrade['source_manifest'])
        self.assertEqual(life.ref(self.service/'PLAN.json'),original)
        life.verify_source.assert_called_once_with(self.upgrade['source_manifest'],self.upgrade['tests_receipt'])

    def test_no_implicit_source_upgrade(self):
        with self.assertRaises(FileNotFoundError):
            life.plan_for(self.service)

    def test_source_specific_upgrade_preserves_historical_overlay(self):
        historical=dict(self.upgrade,source_root='/synthetic/old-runtime')
        shared.write(self.service/'SOURCE_UPGRADE.json',historical)
        historical_ref=life.ref(self.service/'SOURCE_UPGRADE.json')
        path=self.service/('SOURCE_UPGRADE_'+shared.digest(str(life.SOURCE))[:16]+'.json')
        shared.write(path,self.upgrade)
        result=life.plan_for(self.service)
        self.assertEqual(result['source_root'],str(life.SOURCE))
        self.assertEqual(life.ref(self.service/'SOURCE_UPGRADE.json'),historical_ref)

    def test_wrong_original_plan_binding_fails(self):
        self.upgrade['original_plan']=dict(path='unrelated',sha256='e'*64)
        shared.write(self.service/'SOURCE_UPGRADE.json',self.upgrade)
        with self.assertRaisesRegex(ValueError,'exact_preserved_plan_source_upgrade'):
            life.plan_for(self.service)


if __name__=='__main__':
    unittest.main()
