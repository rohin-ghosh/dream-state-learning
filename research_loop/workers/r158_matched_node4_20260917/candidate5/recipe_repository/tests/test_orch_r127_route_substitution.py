from copy import deepcopy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu import orch_r110_claude_broker as broker
from gpu import orch_r121_route_independent as route


class RouteSubstitutionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='r127_route_consumer_', dir='/tmp')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base/'life'
        self.root.mkdir()
        self.now = time.time()
        self.config = dict(schema=broker.SCHEMA, branch='F1', family='route',
            remote_root=str(self.root), life_id='life', deadline_unix=self.now+600,
            max_parent_calls=4, max_budget_usd=2.0, max_output_tokens=2048,
            train_tasks={'TRAIN_TEST': 'a'*64}, excluded_task_ids=['SEALED_TEST'],
            cohort_sha256='b'*64, principles_sha256=broker.PRINCIPLES_V2_SHA256,
            source_files=broker.source_pins(), allowed_substitute_models=['claude-opus-5'],
            parent_effort='low', fallback_parent_fields=dict(GAME='route worlds', STYLE='supportive',
                NUDGING='None.', FOCUS='Notice actual behavior.', REFLECTION=dict(mode='short', max_new_tokens=512)))
        self.config_path = self.base/'CONFIG.json'
        self.put(self.config_path, self.config)
        self.policy = dict(allowed_models=['claude-opus-5'],
            broker_config=dict(path=str(self.config_path), sha256=route.sha(self.config_path)))
        payload = dict(schema='r111_train_public_v1', life_id='life', cycle=22, episode=0,
            phase='experience', game='route', task_id='TRAIN_TEST',
            task_provenance=dict(split='TRAIN', task_sha256='a'*64, cohort_sha256='b'*64),
            events=[dict(sequence=0, actor='child', text='Synthetic visible reasoning.',
                source_sha256='c'*64, visibility='TRAIN_PUBLIC')])
        self.request = dict(id='000085_F1_C0022', payload=payload, payload_sha256=broker.digest(payload),
            lane_deadline_unix=self.now+500)
        self.queue = self.root/'parent_queue'
        self.request_path = self.queue/(self.request['id']+'.request.json')
        self.response_path = self.queue/(self.request['id']+'.response.json')
        self.put(self.request_path, self.request)
        self.claim = self.root/'parent_claude'/(self.request['id']+'.claim')
        self.put(self.claim/'RESERVATION.json', dict(id=self.request['id'], attempts=1,
            sequence=1, config_sha256=broker.digest(self.config), request_file_sha256=route.sha(self.request_path)))
        self.archive = self.root/'parent_transcripts'/self.request['id']
        self.make_response()

    def put(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, sort_keys=True, indent=2)+'\n')

    def make_response(self, silent=False, model='claude-opus-5'):
        envelope = dict(type='result', subtype='success', is_error=False, num_turns=1,
            result='[SILENT]' if silent else json.dumps(dict(guidance='Consider the public receipt.',
                tag='SHIFT', intervention_class='metacognition', rationale='Synthetic fixture.')),
            modelUsage={model: dict(inputTokens=2, outputTokens=12, canonicalModel=model)})
        launch = dict(schema='ORCH_R111_FABLE_LAUNCH_V1', authorized=True,
            authorization='WATCHER_RELAYED_ROHIN_DONE', source_reference='SYNTHETIC_TEST_NOT_AUTHORIZATION',
            config_sha256=broker.digest(self.config), not_before_unix=self.now-1)

        def fake_runner(argv, directory, cutoff, cap):
            self.put(directory/'stdout.json', envelope)
            (directory/'stderr.txt').write_text('')

        directory = self.base/('evaluation_silent' if silent else 'evaluation_'+model)
        result = broker.evaluate(self.request, directory, self.config['deadline_unix'], config=self.config,
            launch=launch, prompt_root=self.base/'absent_prompts',
            principles_path=broker.ROOT/'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md',
            runner=fake_runner, memory=lambda: broker.backend.MIN_AVAILABLE_BYTES,
            lock_path=self.base/'test_provider.lock')
        self.assertEqual(result['status'], 'SILENT' if silent else 'COMPLETE')
        self.archive.mkdir(parents=True, exist_ok=True)
        files = {}
        for path in directory.iterdir():
            destination = self.archive/path.name
            destination.write_bytes(path.read_bytes())
            files[path.name] = route.sha(destination)
        self.response = dict(result, transcript_receipt=dict(remote_root=str(self.archive),
            files=files, node_only=True, all_verified=True))
        self.publish()

    def publish(self):
        self.put(self.response_path, self.response)
        self.put(self.claim/'PUBLISHED.json', dict(id=self.request['id'],
            status=self.response['status'], response_sha256=route.sha(self.response_path),
            actual_model=self.response['actual_model'], requested_model=broker.MODEL,
            model_attribution=self.response['model_attribution']))

    def consume(self, **kwargs):
        options = dict(substitution=self.policy, queue_root=self.root, branch='F1')
        options.update(kwargs)
        return route.parent_result(self.response, self.request, broker.MODEL,
            now=self.response['finished_unix'], **options)

    def assertRejected(self, **kwargs):
        result = self.consume(**kwargs)
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(result['parent_text'], '')

    def test_strict_default_rejects_actual_opus(self):
        self.assertEqual(route.parent_result(self.response, self.request, broker.MODEL,
            now=self.now)['reason'], 'provider_identity_mismatch')

    def test_real_broker_fixture_roundtrip_retains_truthful_attribution(self):
        result = self.consume()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['actual_model'], 'claude-opus-5')
        self.assertEqual(result['requested_model'], broker.MODEL)
        self.assertEqual(result['model_attribution']['status'], 'SUBSTITUTED')
        self.assertFalse(result['fable_parent_claim_eligible'])
        self.assertEqual(result['parent_text'], 'Consider the public receipt.')
        self.assertNotIn('SUBSTITUTED', result['parent_text'])
        self.assertEqual(result['model_usage'], self.response['usage']['model_usage'])

    def test_other_branch_or_head_scope_refused(self):
        for branch in ('A1', 'F2', 'F3', 'F4', 'HEAD', None):
            with self.subTest(branch=branch):
                self.assertRejected(branch=branch)

    def test_allowlist_cannot_expand_or_be_implicit(self):
        for models in ([], ['claude-opus-5', broker.MODEL], ['unknown'], 'claude-opus-5'):
            with self.subTest(models=models):
                self.assertRejected(substitution=dict(self.policy, allowed_models=models))

    def test_wrong_config_hash_refused(self):
        policy = deepcopy(self.policy)
        policy['broker_config']['sha256'] = '0'*64
        self.assertRejected(substitution=policy)

    def test_old_claim_not_rehydrated(self):
        reservation = route.read(self.claim/'RESERVATION.json')
        reservation['config_sha256'] = 'd'*64
        self.put(self.claim/'RESERVATION.json', reservation)
        self.assertRejected()

    def test_missing_remains_missing_without_raw_reparse(self):
        self.response.update(status='MISSING', error=dict(code='old_rejected'))
        with patch.object(route, 'substituted_parent_binding', side_effect=AssertionError('no salvage')):
            self.assertEqual(self.consume()['reason'], 'provider_missing')

    def test_late_and_mismatched_request_stay_missing(self):
        result = route.parent_result(self.response, self.request, broker.MODEL,
            now=self.request['lane_deadline_unix']+1, substitution=self.policy, queue_root=self.root, branch='F1')
        self.assertEqual(result['reason'], 'missing_or_late')
        self.response['request_sha256'] = 'f'*64
        self.assertEqual(self.consume()['reason'], 'binding_mismatch')

    def test_raw_change_rejected(self):
        (self.archive/'stdout.json').write_text('{}')
        self.assertRejected()

    def test_plan_change_even_republished_is_rejected(self):
        self.response['plan']['message'] = 'Changed guidance.'
        self.publish()
        self.assertRejected()

    def test_model_usage_and_hidden_identity_rejected(self):
        for field, replacement in [('actual_model', 'unknown'), ('actual_model', broker.MODEL),
                                   ('requested_model', 'claude-opus-5')]:
            original = self.response[field]
            self.response[field] = replacement
            self.publish()
            self.assertRejected()
            self.response[field] = original
        self.response['usage']['model_usage']['claude-opus-5']['outputTokens'] = 99
        self.publish()
        self.assertRejected()

    def test_receipt_outside_queue_or_traversal_rejected(self):
        receipt = deepcopy(self.response['transcript_receipt'])
        self.response['transcript_receipt']['remote_root'] = str(self.base)
        self.publish()
        self.assertRejected()
        self.response['transcript_receipt'] = receipt
        self.response['transcript_receipt']['files']['../stdout.json'] = '0'*64
        self.publish()
        self.assertRejected()

    def test_silent_preserves_substitution_without_guidance(self):
        self.make_response(silent=True)
        result = self.consume()
        self.assertEqual(result['status'], 'SILENT')
        self.assertEqual(result['parent_text'], '')
        self.assertEqual(result['model_attribution']['status'], 'SUBSTITUTED')

    def test_native_application_receipt_retains_attribution_exactly_once(self):
        self.put(self.root/'R121_PARENT_DELIVERY'/(self.request['id']+'.json'),
            dict(request=self.request, source_call_sha256='e'*64, submitted_unix=self.now))
        plan = dict(provider=broker.MODEL, branch='F1', parent_model_substitution=self.policy)
        result = route.poll_parents(self.root, plan)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 'COMPLETE')
        applied = route.read(self.root/'R121_PARENT_DELIVERY'/(self.request['id']+'.applied.json'))
        self.assertEqual(applied['model_attribution'], self.response['model_attribution'])
        self.assertEqual(applied['actual_model'], 'claude-opus-5')
        self.assertFalse(applied['retry'])
        self.assertEqual(route.poll_parents(self.root, plan), [])
        self.assertEqual(len(list((self.root/'parent_claude').glob('*.claim'))), 1)

    def test_response_before_publication_remains_nonblocking_pending(self):
        self.put(self.root/'R121_PARENT_DELIVERY'/(self.request['id']+'.json'),
            dict(request=self.request, source_call_sha256='e'*64, submitted_unix=self.now))
        plan = dict(provider=broker.MODEL, branch='F1', parent_model_substitution=self.policy)
        publication = self.claim/'PUBLISHED.json'
        content = publication.read_bytes()
        publication.unlink()
        with patch.object(route.time, 'sleep', side_effect=AssertionError('must_not_block')):
            self.assertEqual(route.poll_parents(self.root, plan), [])
        publication.write_text('{')
        self.assertEqual(route.poll_parents(self.root, plan), [])
        publication.write_bytes(content)
        self.assertEqual(route.poll_parents(self.root, plan)[0]['status'], 'COMPLETE')

    def test_missing_publication_does_not_wait_past_deadline(self):
        self.put(self.root/'R121_PARENT_DELIVERY'/(self.request['id']+'.json'),
            dict(request=self.request, source_call_sha256='e'*64, submitted_unix=self.now))
        plan = dict(provider=broker.MODEL, branch='F1', parent_model_substitution=self.policy)
        (self.claim/'PUBLISHED.json').unlink()
        with patch.object(route.time, 'time', return_value=self.request['lane_deadline_unix']+1):
            self.assertEqual(route.poll_parents(self.root, plan)[0]['status'], 'MISSING')
        self.assertEqual(route.poll_parents(self.root, plan), [])

    def test_requested_fable_remains_eligible_with_raw_join(self):
        self.make_response(model=broker.MODEL)
        result = self.consume()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['actual_model'], broker.MODEL)
        self.assertEqual(result['model_attribution']['status'], 'REQUESTED_MODEL')
        self.assertTrue(result['fable_parent_claim_eligible'])

    def test_default_fable_does_not_require_new_epoch(self):
        response = dict(self.response, actual_model=broker.MODEL)
        with patch.object(route, 'substituted_parent_binding', side_effect=AssertionError('strict old path')):
            result = route.parent_result(response, self.request, broker.MODEL, now=self.now)
        self.assertEqual(result['status'], 'COMPLETE')


if __name__ == '__main__':
    unittest.main()
