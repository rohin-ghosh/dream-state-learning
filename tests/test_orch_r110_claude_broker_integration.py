from copy import deepcopy
import json
import subprocess
import time
import unittest

from gpu import orch_r110_claude_broker as broker
from gpu import orch_r111_route_pair as route
from organism_v6 import orch_math_feedback_uptake_r111 as math_lane
from organism_v6 import orch_r108_code_parent_r111_f3 as code_lane
from organism_v6 import orch_r111_grid as grid_lane
from tests import test_orch_r110_claude_broker as fixtures
from tests import test_orch_r111_route_pair as route_fixtures


class ClaudeWireIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ClaudeBrokerTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def archived_response(self):
        result, directory = self.fixture.evaluate()
        receipt = broker.archive(fixtures.LocalStore(), directory,
            self.fixture.root / 'native_archive' / directory.name)
        return dict(result, transcript_receipt=receipt)

    def consume(self, branch, response):
        request = self.fixture.request
        now = time.time()
        if branch == 'F1':
            return route.parent_result(response, request, broker.MODEL, now=now)
        if branch == 'F2':
            return math_lane.resolve_parent(request, response, now, broker.MODEL,
                archive_verified=response['transcript_receipt']['all_verified'])
        if branch == 'F3':
            plan = response.get('plan') or {}
            return code_lane.classify_intervention(dict(status=response['status'],
                child_text=plan.get('guidance')), now, request['lane_deadline_unix'])
        return grid_lane.parent_disposition(request, response, now, broker.MODEL)

    def test_prelaunch_1_archived_four_lane_wire_and_visible_feedback(self):
        fixture = self.fixture
        feedback = dict(sequence=1, actor='environment', text='The door stayed closed.',
            source_sha256='d'*64, visibility='TRAIN_PUBLIC', event_type='environment_feedback',
            child_received=True, feedback={'observed': 'closed'}, hidden_answer_keys={'secret': 'never visible'})
        fixture.request['payload']['events'].append(feedback)
        fixture.request['payload']['events'].append(dict(sequence=2, actor='oracle',
            text='SEALED_RESULT', source_sha256='e'*64, visibility='TRAIN_PUBLIC',
            event_type='hidden_evaluator_verdict'))
        for branch, family in broker.FAMILIES.items():
            with self.subTest(branch=branch):
                fixture.config.update(branch=branch, family=family)
                fixture.request['payload']['game'] = family
                fixture.rebind()
                response = self.archived_response()
                self.assertEqual(response['status'], 'COMPLETE')
                self.assertIn(self.consume(branch, response)['status'], ('COMPLETE', 'INTERVENTION'))
                transcript = broker.validate_request(fixture.request, fixture.config)
                self.assertEqual(transcript['events'][1]['feedback'], {'observed': 'closed'})
                self.assertNotIn('secret', json.dumps(transcript))
                self.assertNotIn('SEALED_RESULT', json.dumps(transcript))
                self.assertTrue(response['transcript_receipt']['node_only'])
                self.assertTrue(response['transcript_receipt']['all_verified'])
                self.assertEqual(fixture.runner.call_args.args[2], fixture.request['lane_deadline_unix']-30)
        self.assertEqual(fixture.runner.call_count, 4)

    def test_prelaunch_2_timeout_is_missing_four_lanes_continue_no_retry(self):
        fixture = self.fixture
        fixture.runner.side_effect = subprocess.TimeoutExpired('fixture_no_provider', 1)
        for branch, family in broker.FAMILIES.items():
            with self.subTest(branch=branch):
                fixture.config.update(branch=branch, family=family)
                fixture.request['payload']['game'] = family
                fixture.rebind()
                response = self.archived_response()
                self.assertEqual(response['status'], 'MISSING')
                self.assertFalse(response['retry'])
                self.assertEqual(self.consume(branch, response)['status'], 'MISSING')
                settings = broker.reflection_call_settings(response, fixture.request, 1024,
                    config=fixture.config)
                self.assertEqual(settings['effective_max_new_tokens'], 1024)
                self.assertFalse(settings['stop_child'])
        self.assertEqual(fixture.runner.call_count, 4)

    def test_prelaunch_3_head_reflection_actual_broker_to_lane_decoder_cap(self):
        fixture = self.fixture
        for requested_cap in (512, 128):
            with self.subTest(requested_cap=requested_cap):
                fields = dict(fixture.head_fields, REFLECTION=dict(mode='short', max_new_tokens=requested_cap))
                (fixture.prompts/'F1.md').write_text(broker.render_parent_prompt(fields))
                (fixture.prompts/'F1.fields.json').write_text(json.dumps(dict(
                    schema='ORCH_R114_HEAD_FIELDS_V1', prompt_sha256=broker.sha(fixture.prompts/'F1.md'),
                    fields=fields)))
                response = self.archived_response()
                settings = broker.reflection_call_settings(response, fixture.request, 4096,
                    config=fixture.config)
                self.assertEqual(settings['status'], 'BOUND_FOR_LANE_DECODER')
                engine = route_fixtures.native_shape_engine()
                native = route.generate(engine, [dict(role='user', content='Reflect in your own way.')],
                    cap=settings['effective_max_new_tokens'], reflection=True)
                self.assertEqual(engine.model.actual_configs[-1]['max_new_tokens'], requested_cap)
                self.assertEqual(native['effective_generation_cap'], requested_cap)
                self.assertEqual(engine.model.actual_configs[-1]['no_repeat_ngram_size'], 16)
                self.assertFalse(settings['changes_lifetime_caps'])
                self.assertFalse(settings['reflection_applied_by_broker'])

    def test_fallback_cap_bound_and_original_cap_never_extended(self):
        fixture = self.fixture
        (fixture.prompts/'F1.md').unlink()
        fixture.config['fallback_parent_fields'] = dict(fixture.head_fields,
            REFLECTION=dict(mode='long', max_new_tokens=8192))
        fixture.rebind()
        response = self.archived_response()
        settings = broker.reflection_call_settings(response, fixture.request, 1024, config=fixture.config)
        self.assertEqual(settings['status'], 'BOUND_FOR_LANE_DECODER')
        self.assertEqual(settings['requested_max_new_tokens'], 8192)
        self.assertEqual(settings['effective_max_new_tokens'], 1024)

    def test_tampered_late_or_unarchived_settings_keep_original(self):
        fixture = self.fixture
        (fixture.prompts/'F1.md').unlink()
        response = self.archived_response()
        variants = [deepcopy(response) for unused in range(5)]
        variants[0]['request_sha256'] = '0'*64
        variants[1]['prompt_binding']['head_settings']['fields']['REFLECTION']['max_new_tokens'] = 2
        variants[2]['transcript_receipt']['all_verified'] = False
        variants[3]['transcript_receipt']['files']['PROMPT_BINDING.json'] = '0'*64
        variants[4]['finished_unix'] = fixture.request['lane_deadline_unix']
        for candidate in variants:
            settings = broker.reflection_call_settings(candidate, fixture.request, 2048,
                config=fixture.config)
            self.assertEqual(settings['status'], 'KEEP_ORIGINAL')
            self.assertEqual(settings['effective_max_new_tokens'], 2048)
            self.assertFalse(settings['stop_child'])


if __name__ == '__main__':
    unittest.main()
