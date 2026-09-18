import copy
import inspect
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import semantic_judge_continuation as continuation
import test_semantic_judge as fixtures


protocol = continuation.protocol


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        fixture = fixtures.SemanticTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.packet = fixture.packet
        self.value = fixture.value
        self.response = fixture.response
        self.inventory = dict(packets=[dict(path=f'/opaque/{index:048x}.json', sha256=f'{index:064x}') for index in range(60)])
        self.settlement = dict(consumed=[dict(packet=item) for item in self.inventory['packets'][:9]])

    def test_render_is_exact_same_validator_evidence_no_fact_rewriting(self):
        before = copy.deepcopy(self.packet)
        payload = json.loads(continuation.request(self.packet, 'FROZEN'))
        self.assertEqual(payload['packet'], before)
        self.assertEqual(self.packet, before)
        self.assertEqual(payload['rendered_span_evidence']['TRAIN'], 'specific test\nprior work\nspecific test\nprior work')
        self.assertEqual(payload['rendered_span_evidence']['response'], before['response'])
        self.assertEqual(set(payload), {'packet', 'frozen_rubric', 'rendered_span_evidence'})
        self.assertNotIn('mapping', json.dumps(payload))

    def test_literal_TRAIN_line_passes_unchanged_validator(self):
        value = dict(self.value, supporting_spans=[dict(source='TRAIN', quote='specific test')])
        response = dict(self.response, rationale=json.dumps(value))
        provider = Mock(return_value=(response, continuation.original.MODEL, {'output_tokens':100}))
        result = continuation.judge_one(self.packet, 'FROZEN', self.root, time.time()+5, provider, {})
        self.assertEqual(result['annotation'], value)
        self.assertEqual(provider.call_args.kwargs['reasoning_effort'], 'high')
        self.assertEqual(provider.call_count, 1)

    def test_reconstructed_TRAIN_prose_still_fails_no_salvage(self):
        value = dict(self.value, supporting_spans=[dict(source='TRAIN', quote='Specific test prior work.')])
        provider = Mock(return_value=(dict(self.response, rationale=json.dumps(value)), continuation.original.MODEL, {}))
        with self.assertRaisesRegex(ValueError, 'real_evidence_span_not_fabricated'):
            continuation.judge_one(self.packet, 'FROZEN', self.root, time.time()+5, provider, {})
        self.assertEqual(provider.call_count, 1)

    def test_same_validator_function_not_a_relaxed_copy(self):
        import semantic_judge
        self.assertIs(continuation.original.annotation, semantic_judge.annotation)
        self.assertNotIn('def annotation(', inspect.getsource(continuation))

    def test_remaining_exact51_excludes_all9_consumed_preserves_order_hashes(self):
        remaining = continuation.partition(self.inventory, self.settlement)
        self.assertEqual(remaining, self.inventory['packets'][9:])
        self.assertEqual(len(remaining), 51)
        self.assertEqual(len(remaining) + len(self.settlement['consumed']), 60)

    def test_changed_consumed_hash_duplicate_or_fewer_charges_reject(self):
        variants = [copy.deepcopy(self.settlement) for _ in range(3)]
        variants[0]['consumed'][0]['packet']['sha256'] = 'changed'
        variants[1]['consumed'][0] = variants[1]['consumed'][1]
        variants[2]['consumed'].pop()
        for variant in variants:
            with self.assertRaises(ValueError):
                continuation.partition(self.inventory, variant)

    def test_no_model_on_invalid_packet_and_provider_error_never_retried(self):
        provider = Mock()
        with self.assertRaises(ValueError):
            continuation.judge_one(dict(self.packet, condition='forbidden'), 'FROZEN', self.root, time.time()+5, provider, {})
        provider.assert_not_called()
        provider.side_effect = RuntimeError('fixture')
        with self.assertRaises(RuntimeError):
            continuation.judge_one(self.packet, 'FROZEN', self.root, time.time()+5, provider, {})
        self.assertEqual(provider.call_count, 1)

    def test_three_structural_failures_stop_unconsumed_queue_not_negative(self):
        plan_path = self.root / 'plan.json'
        protocol.write(plan_path, {})
        go = self.root / 'go.json'
        protocol.write(go, continuation.expected_go(plan_path))
        plan = dict(private_vm_root=str(self.root/'private'), private_remote_root='/private/node2', source_root=str(self.root),
                    remaining_packets=continuation.partition(self.inventory,self.settlement), deadline_unix=time.time()+5400,
                    settlement={'path':'/metadata/settlement','sha256':'a'*64})
        calls = []
        def fake_worker(command, **kwargs):
            calls.append(command)
            packet_id = command[command.index('--packet-id')+1]
            protocol.write(Path(plan['private_vm_root'])/packet_id/'WORKER_FAILURE.json',
                dict(failure_class='real_evidence_span_not_fabricated'))
            raise subprocess.CalledProcessError(1,command)
        def upload(base, name, raw):
            return dict(path='/private/node2/'+name,sha256=protocol.hashlib.sha256(raw).hexdigest())
        with patch.object(continuation, 'validate', return_value=(plan, {}, self.inventory, self.settlement)), \
                patch.object(continuation.subprocess, 'run', side_effect=fake_worker), \
                patch.object(continuation.original, 'remote_upload', side_effect=upload):
            result = continuation.dispatch(plan_path,go)
            with self.assertRaises(FileExistsError):
                continuation.dispatch(plan_path,go)
        self.assertGreaterEqual(len(calls),3)
        self.assertLessEqual(len(calls),4)
        self.assertEqual(result['combined_calls_charged'], 9+len(calls))
        self.assertEqual(result['unadmitted'], 51-len(calls))
        self.assertTrue(result['admission_stopped'])
        for path in (self.root/'private').glob('*/NOT_STARTED.json'):
            value = protocol.read(path)
            self.assertEqual(value['calls_charged'],0)
            self.assertNotIn('negative',value)

    def test_single_failure_does_not_stop_and_success_resets(self):
        state = dict(failure_class=None, consecutive=0, stop=False)
        state = continuation.next_streak(state,'real_evidence_span_not_fabricated')
        self.assertFalse(state['stop'])
        state = continuation.next_streak(state,None)
        self.assertEqual(state['consecutive'],0)
        for count in range(1,4):
            state = continuation.next_streak(state,'real_evidence_span_not_fabricated')
            self.assertEqual(state['stop'],count==3)

    def test_different_classes_reset_and_scope_failure_stops_immediately(self):
        state = dict(failure_class='real_evidence_span_not_fabricated',consecutive=2,stop=False)
        state = continuation.next_streak(state,'bounded_evidence_spans')
        self.assertEqual((state['consecutive'],state['stop']),(1,False))
        state = continuation.next_streak(state,'IMMEDIATE_SCOPE_OR_UNKNOWN_FAILURE')
        self.assertTrue(state['stop'])

    def test_one_invalid_packet_keeps_remaining_fifty_admissible(self):
        path = self.root/'plan.json';protocol.write(path,{})
        go = self.root/'go.json';protocol.write(go,continuation.expected_go(path))
        plan = dict(private_vm_root=str(self.root/'private'),private_remote_root='/private/node2',source_root=str(self.root),
            remaining_packets=continuation.partition(self.inventory,self.settlement),deadline_unix=time.time()+5400,
            settlement={'path':'/metadata/settlement','sha256':'a'*64})
        attempts=[]
        def fake_worker(command,**kwargs):
            packet_id=command[command.index('--packet-id')+1];attempts.append(packet_id)
            directory=Path(plan['private_vm_root'])/packet_id
            if int(packet_id,16)==9:
                protocol.write(directory/'WORKER_FAILURE.json',dict(failure_class='real_evidence_span_not_fabricated'))
                raise subprocess.CalledProcessError(1,command)
            protocol.write(directory/'ANNOTATION.private.json',self.value)
            return subprocess.CompletedProcess(command,0)
        with patch.object(continuation,'validate',return_value=(plan,{},self.inventory,self.settlement)), \
                patch.object(continuation.subprocess,'run',side_effect=fake_worker), \
                patch.object(continuation.original,'remote_upload',return_value={'path':'/private','sha256':'a'*64}):
            result=continuation.dispatch(path,go)
        self.assertEqual(len(attempts),51)
        self.assertEqual((result['combined_calls_charged'],result['complete_annotations'],result['failed_or_uncertain']),(60,50,1))
        self.assertFalse(result['admission_stopped'])

    def test_original_clock_deadline_cannot_be_ignored_at_dispatch(self):
        path = self.root/'plan.json';protocol.write(path,{})
        go = self.root/'go.json';protocol.write(go,continuation.expected_go(path))
        with patch.object(continuation,'validate',return_value=(dict(deadline_unix=time.time()+100),{},{},{})), \
                patch.object(continuation.subprocess,'run') as run:
            with self.assertRaises(ValueError):
                continuation.dispatch(path,go)
            run.assert_not_called()

    def test_old_GO_not_new_continuation_permission(self):
        path = self.root/'plan.json';protocol.write(path,{})
        go = self.root/'go.json';protocol.write(go,continuation.original.expected_go(path) if hasattr(continuation.original,'expected_go') else {'status':'MAIN_SEMANTIC_EXECUTION_GO'})
        with patch.object(continuation,'validate',return_value=({},{},{},{})),patch.object(continuation.subprocess,'run') as run:
            with self.assertRaises(ValueError):
                continuation.dispatch(path,go)
            run.assert_not_called()


if __name__=='__main__':
    unittest.main()
