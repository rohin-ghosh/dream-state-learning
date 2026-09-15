import ast
from contextlib import nullcontext
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r121_route_independent as route
from gpu import orch_r121_route_launch as launch


class IndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.plan=dict(bounds=dict(native_calls=8,parent_calls=4,hard_end_unix=9999999999),
            parent_delivery_seconds=600,provider='test',cohort_sha256='c'*64)
        route.write(self.root/'R121_INDEPENDENT_PLAN_V2.json',self.plan)

    def request(self):
        return route.parent_call(self.root,self.plan,dict(id='TRAIN-test',task={'given':1}),1,0,'experience',
            [dict(role='user',content='public task'),dict(role='assistant',content='observed reasoning')],'a'*64)

    def test_enqueue_returns_without_sleep(self):
        with patch.object(route.time,'sleep',side_effect=AssertionError('must_not_wait')):
            result=self.request()
        self.assertEqual(result['status'],'PENDING')
        request=route.read(next((self.root/'parent_queue').glob('*.request.json')))
        self.assertAlmostEqual(request['lane_deadline_unix']-route.time.time(),600,delta=2)
        self.assertEqual(route.poll_parents(self.root,self.plan),[])

    def test_pending_does_not_duplicate_charge(self):
        self.request()
        self.request()
        self.assertEqual(len((self.root/'RESERVATIONS.jsonl').read_text().splitlines()),1)

    def test_silent_next_turn_exactly_once(self):
        result=self.request()
        request=route.read(self.root/'parent_queue'/(result['id']+'.request.json'))
        response=dict(id=request['id'],request_sha256=route.digest(request),status='SILENT',actual_model='test',
            finished_unix=route.time.time(),plan=dict(message='[SILENT]'))
        route.write(self.root/'parent_queue'/(result['id']+'.response.json'),response)
        self.assertEqual(route.poll_parents(self.root,self.plan)[0]['status'],'SILENT')
        self.assertEqual(route.poll_parents(self.root,self.plan),[])

    def test_late_is_missing_not_retry(self):
        result=self.request()
        request=route.read(self.root/'parent_queue'/(result['id']+'.request.json'))
        with patch.object(route.time,'time',return_value=request['lane_deadline_unix']+1):
            self.assertEqual(route.poll_parents(self.root,self.plan)[0]['status'],'MISSING')
        self.assertEqual(len((self.root/'RESERVATIONS.jsonl').read_text().splitlines()),1)

    def test_schedule_anchor_every_step_and_rehearsal(self):
        schedule=route.sleep_schedule(3,1)
        self.assertEqual(len(schedule),49)
        self.assertTrue(all(len(item['anchors'])==1 for item in schedule))
        self.assertEqual(schedule[-1]['own'],('REHEARSAL',0))

    def test_actual_training_anchor_gradient_every_update(self):
        weights=[]
        class Loss:
            def __mul__(self,weight):
                weights.append(weight)
                return self
            def backward(self): pass
            def detach(self): return self
            def cpu(self): return self
            def __float__(self): return 1.0
        item=SimpleNamespace(input_ids=(1,2,3),labels=(-100,2,3),target_ids=(2,3))
        torch=SimpleNamespace(tensor=lambda values,**kwargs:values,long='long',bfloat16='bf16',
            ones_like=lambda values:values,autocast=lambda **kwargs:nullcontext(),isfinite=lambda loss:True)
        model=Mock(return_value=SimpleNamespace(loss=Loss()))
        model.config=SimpleNamespace(use_cache=True)
        engine=SimpleNamespace(torch=torch,tokenizer=None,model=model,device='cpu',verify_base=Mock())
        optimizer=Mock()
        with patch.object(route.replay,'encode_row',return_value=item),patch.object(route.native.development,'enable_existing_adapter'):
            result=route.train_sleep(engine,optimizer,[{},{},{}],[{}],[dict(encoded=item)]*42,self.root,lambda label:None)
        self.assertEqual(optimizer.step.call_count,49)
        self.assertEqual(weights,[.75,.25]*49)
        self.assertEqual(result['anchor_token_exposure_including_eos'],98)

    def test_old_ledger_prefix_and_absolute_cap(self):
        route.reserve(self.root,'NATIVE',{})
        original=(self.root/'RESERVATIONS.jsonl').read_bytes()
        plan=dict(self.plan,inherited_ledger=dict(bytes=len(original),sha256=route.sha(self.root/'RESERVATIONS.jsonl')))
        route.reserve(self.root,'NATIVE',{})
        self.assertEqual(launch.ledger_prefix(self.root,plan)['NATIVE'],2)
        (self.root/'RESERVATIONS.jsonl').write_bytes(original.replace(b'NATIVE',b'PARENT'))
        with self.assertRaisesRegex(ValueError,'old_charges'):
            launch.ledger_prefix(self.root,plan)

    def test_final_distinct_no_early_dispatch(self):
        self.assertFalse(route.final_due(0,route.MORNING_CUT-1))
        self.assertIn('R121_FINAL_20260916_0600',str(route.readout_directory(self.root,1,'final')))
        with patch.object(route.time,'time',return_value=route.MORNING_CUT-1):
            with self.assertRaisesRegex(ValueError,'new_final_not_before'):
                route.reserve(self.root,'NATIVE',dict(scope='R121_FINAL_20260916_0600'))

    def test_executable_no_shared_barrier_and_episode_cadence(self):
        source=Path(route.__file__).read_text()
        run=next(item for item in ast.parse(source).body if isinstance(item,ast.FunctionDef) and item.name=='run')
        runtime=ast.get_source_segment(source,run)
        self.assertNotIn('shared_session.',runtime)
        self.assertNotIn('await_collection',runtime)
        self.assertIn("optimizer.load_state_dict(state['optimizer'])",runtime)
        self.assertIn("PARENT_EPISODE_",runtime)

    def test_actual_scanner_closure_imports(self):
        from gpu import orch_r118_route_concurrent_admission as proof
        from gpu import orch_admission_transient_exit as transient
        from gpu import orch_math_feedback_uptake_r118_argv_admission as argv
        from gpu import orch_r118_route_parallel_run as native
        source=Path(proof.__file__).with_name('orch_math_feedback_uptake_r118_preinfer.py').read_text()
        compiled=proof.proof_binding(source,transient,lambda kind,value:None)
        self.assertTrue(callable(proof.scan) and callable(transient.reconcile_scan))
        self.assertTrue(callable(argv.scan) and callable(compiled) and bool(native.UUIDS))


if __name__=='__main__':
    unittest.main()
