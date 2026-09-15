"""R110 native response, visibility, resident-cycle and additive-budget tests."""

from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r109_route_engine as engine
from gpu import orch_r109_route_run as run
from gpu import orch_r109_route_broker as broker
from organism_v6 import orch_r109_route as policy
from tests.test_orch_r107_route_parent import minimal_engine


class ResidentRouteTests(unittest.TestCase):
    def minimal(self,corrupt=False):
        value=minimal_engine('A grounded observation.\nROUTE port',corrupt=corrupt)
        value.model.eval=lambda:None
        return value

    def payload(self):
        return policy.parent_payload('node1_7',1,1,5,[dict(role='user',content='Actual public task')],
            'Own child output','GENERATED_NOT_YET_EXECUTED',Path(policy.PRINCIPLES_PATH).read_text())

    def test_exact_snapshot(self):
        self.assertEqual(hashlib.sha256(Path(policy.PRINCIPLES_PATH).read_bytes()).hexdigest(),policy.PRINCIPLES_SHA)
        with self.assertRaises(ValueError):
            policy.validate_parent_payload(dict(self.payload(),principles='changed'))

    def test_no_failure_gate(self):
        self.assertIn('never gate intervention on failure',policy.PARENT_INSTRUCTIONS)
        self.assertNotIn('Intervene constructively on failure',policy.PARENT_INSTRUCTIONS)
        self.assertIn('ADD, STOP or SHIFT',policy.PARENT_INSTRUCTIONS)

    def test_actual_minimal_engine_response_contract(self):
        messages=[dict(role='user',content='task')]
        response=engine.generate(self.minimal(),messages)
        self.assertIs(response['input_truncated'],False)
        self.assertTrue(response['full_prompt_prefix_verified'])
        self.assertEqual(response['messages'],messages)
        self.assertEqual(response['token_ids'],[13,99])

    def test_actual_minimal_engine_rejects_prefix_corruption(self):
        with self.assertRaises(ValueError):
            engine.generate(self.minimal(True),[dict(role='user',content='task')])

    def test_actual_minimal_shape_enters_existing_gym(self):
        with patch.object(policy,'CYCLES',1):
            group=policy.cohort([],'node1_7')['train'][0]
        value=self.minimal()
        record=policy.episode(group['world'],group['tasks'][0],lambda messages:engine.generate(value,messages),{})
        self.assertGreater(record['actor_calls'],0)
        self.assertFalse(record['captures'][0]['response']['input_truncated'])

    def test_native_context_and_no_padding(self):
        self.assertEqual(policy.token_budget(100),8192)
        self.assertEqual(policy.token_budget(32760),8)
        for length in (0,32768,True):
            with self.assertRaises(ValueError):
                policy.token_budget(length)

    def test_cadence_never_resets_at_cycle(self):
        self.assertTrue(policy.due('hundred',100))
        self.assertFalse(policy.due('hundred',101))
        self.assertTrue(policy.due('hundred',200))
        self.assertFalse(policy.due('hundred',200,episode_end=True))
        self.assertTrue(policy.due('episode',101,episode_end=True))

    def test_metacognition_separate_budget(self):
        for lane in policy.LANES:
            self.assertEqual(policy.parent_cap(lane),policy.PARENT_CAPS[policy.LANES[lane]['cadence']]+256*policy.REFLECTION_TURNS[lane])
            self.assertGreaterEqual(policy.REFLECTION_TURNS[lane],2)

    def test_no_old_quota_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(policy,'NATIVE_CAP',2):
                run.reserve(root,'node1_7','NATIVE',{})
                self.assertEqual(run.reserve(root,'node1_7','NATIVE',{})['number'],2)
                before=(root/'RESERVATIONS.jsonl').read_bytes()
                with self.assertRaises(run.BoundReached):
                    run.reserve(root,'node1_7','NATIVE',{})
                self.assertEqual((root/'RESERVATIONS.jsonl').read_bytes(),before)

    def test_held_rejected_and_conversation_accepted(self):
        payload=self.payload()
        with self.assertRaises(ValueError):
            policy.validate_parent_payload(dict(payload,split='HELD'))
        with self.assertRaises(ValueError):
            policy.validate_parent_payload(dict(payload,held_scores=[]))
        self.assertEqual(policy.validate_parent_payload(dict(payload,mode='METACOGNITION_CONVERSATION',turn=2))['turn'],2)

    def test_new_cohort_and_siblings_disjoint(self):
        seen=set()
        with patch.object(policy,'CYCLES',2):
            for lane in policy.LANES:
                frozen=policy.cohort(seen,lane)
                self.assertFalse(policy.identifiers(frozen)&seen)
                self.assertFalse(policy.identifiers(frozen['train'])&policy.identifiers(frozen['held']))
                self.assertEqual(sum(len(group['tasks']) for group in frozen['train']),4)
                seen.update(policy.identifiers(frozen))

    def test_reflection_before_every_sleep_and_no_repeated_admission(self):
        source=inspect.getsource(run.native)
        self.assertLess(source.index('METACOGNITION_CONVERSATION'),source.index('native_engine.sleep('))
        self.assertNotIn('admission.scan',source)
        self.assertNotIn('subprocess',source)
        self.assertIn("purpose!='reflection'",source)
        self.assertIn('state[\'memory\']=response[\'raw\']',source)

    def test_real_raw_replay_contract(self):
        response=engine.generate(self.minimal(),[dict(role='user',content='actual')])
        row=engine.replay_row(dict(response=response,task_id='TRAIN-real'),Path('/node/CALL.json'),'abc')
        self.assertEqual(row['source_generated_token_ids'],response['token_ids'])
        self.assertEqual(row['student_prefix'],response['messages'])
        self.assertTrue(row['append_eos'])

    def test_wrapper_transport_no_host_literals(self):
        store=broker.Store(Path('/repo'),Path('/node'),'node1_7')
        self.assertEqual(store.host['wrapper'],'gpu/a40r_ssh.sh')
        self.assertEqual(store.host['scp'],'gpu/a40r_scp.sh')

    def test_runtime_source_guards_in_manifest(self):
        from gpu.orch_r109_route_ops import closure
        files=closure()
        self.assertIn('gpu/astra_goal_breadth_collection_guard.sh',files)
        from gpu import astra_portable_actor_bundle as portable
        self.assertTrue(portable.contract()['helpers'])

    def test_argv_drift_requires_stable_kernel_and_no_gpu(self):
        from gpu.orch_r110_admission import reconcile
        identity=dict(pid=41,uid=1000,start_ticks='555',boot_id='boot',command_sha256='old')
        samples=[dict(identity,command_sha256=command,executable_identity=[1,2],target_open=False,
            visibility_complete=True,cvd=None) for command in ('old','new','new')]
        report=dict(scanner_euid=0,gpu=dict(uuid='GPU-target',memory_used_mib=0),compute_processes=[],
            processes=[dict(identity,pinned_identity=identity,target_device_open=False,cvd=None)],
            blocking_reasons=['process_identity_drift:41','minor_scan_identity_changed:41'],clear=False)
        result=reconcile(report,{41:samples})
        self.assertTrue(result['clear'])
        self.assertEqual(result['unreconciled_blocking_reasons'],report['blocking_reasons'])
        for key,value in (('target_open',True),('cvd','GPU-target'),('uid',0),('visibility_complete',False)):
            changed=deepcopy(samples)
            changed[1][key]=value
            self.assertFalse(reconcile(report,{41:changed})['clear'])
        report['blocking_reasons'].append('open_device_pid:41')
        self.assertFalse(reconcile(report,{41:samples})['clear'])

    def test_absolute_lifetime_and_protected_slots(self):
        self.assertEqual(run.END,1789491720)
        for lane in ('a100_0','a100_4','a100_7','node1_0','node3_1'):
            with self.assertRaises(ValueError):
                policy.allocation(lane)


if __name__=='__main__':
    unittest.main()
