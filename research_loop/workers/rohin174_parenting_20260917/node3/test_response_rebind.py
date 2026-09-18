"""CPU regression tests: retry authorization, immutable clocks and publication safety."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import response_rebind as operator


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.state = dict(caught_up=True, journal_id='life', response_count=135)
        self.memory = dict(awaiting_render=False, last_response_count=135)
        self.result = dict(status='PROVIDER_FAILED', source_sha256='exact')
        self.source = dict(journal_id='life', response_count=135)

    def candidate(self, physical=0, exists=None, attempts=None):
        def reader(path):
            return self.result if path.name == 'RESULT.json' else self.source
        with patch.object(Path, 'exists', exists or (lambda path: path.name == 'RESULT.json')), \
                patch.object(Path, 'glob', return_value=attempts or []), \
                patch.object(operator, 'read', side_effect=reader), \
                patch.object(operator, 'sha', return_value='exact'), \
                patch.object(operator, 'reference', side_effect=lambda path: str(path)):
            return operator.retry_candidate(physical, Path('/owned'), self.state, self.memory)

    def test_known_failure_retries_same_counter_without_reset(self):
        original = copy.deepcopy((self.state, self.memory))
        self.assertIsNotNone(self.candidate())
        self.assertEqual((self.state, self.memory), original)

    def test_both_documented_failures_eligible(self):
        self.assertIsNotNone(self.candidate(4))

    def test_no_undocumented_retries(self):
        self.assertIsNone(self.candidate(1))

    def test_reservation_blocks_second_call(self):
        self.assertIsNone(self.candidate(exists=lambda path: path.name in ('RESULT.json', 'TECHNICAL_RETRY_ONCE.json')))

    def test_publication_intent_never_replayed(self):
        with self.assertRaisesRegex(ValueError, 'never_replay_publication_intent'):
            self.candidate(exists=lambda path: path.name in ('RESULT.json', 'PUBLISH_INTENT.json'))

    def test_unknown_failure_rejected(self):
        self.result['status'] = 'PUBLICATION_UNKNOWN'
        with self.assertRaisesRegex(ValueError, 'documented_prepublication_failure'):
            self.candidate()

    def test_other_uncertain_attempt_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unfinished_attempt'):
            self.candidate(attempts=[Path('/owned/inflight')], exists=lambda path: False)

    def test_waiting_delivery_prevents_retry(self):
        self.memory['awaiting_render'] = True
        self.assertIsNone(self.candidate())

    def test_uncaught_up_prevents_retry(self):
        self.state['caught_up'] = False
        self.assertIsNone(self.candidate())

    def test_rewind_rejected(self):
        self.state['response_count'] = 134
        with self.assertRaisesRegex(ValueError, 'no_retry_counter_rewind'):
            self.candidate()

    def test_private_adapter_only_converts_rationale(self):
        adapter = operator.base.load_file(operator.STATE / 'orch_r175_parent_response.py', 'cpu_Main_adapter')
        original = dict(speak=True, message='Exact MESSAGE.', rationale=dict(object_id='UpperCase', next_task='keep'))
        result = json.loads(adapter.normalize_rationale(json.dumps(original)))
        self.assertEqual(json.loads(result.pop('rationale')), original['rationale'])
        self.assertEqual(result, {key: value for key, value in original.items() if key != 'rationale'})


if __name__ == '__main__':
    unittest.main()
