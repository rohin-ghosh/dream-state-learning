import copy
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import p3_retry_observe as observer
import p3_retry_publication_resolution as resolution


class PublicationResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / resolution.ATTEMPT
        self.directory.mkdir()
        self.source = dict(journal_id=observer.JOURNAL_ID, response_count=312)
        self.write('SOURCE.json', self.source)
        self.result = dict(status='PUBLICATION_UNKNOWN', publication=None, error_type='RuntimeError',
            error='Traceback:\n  File "/p3_endpoint.py", line 53, in main\n    predecessor.host()\n'
                '  File "/MATH_C/math_c.py", line 59, in host\n',
            message='Astra: historical prompt.', source_sha256=observer.digest(self.directory / 'SOURCE.json'))
        self.intent = dict(speaker='Astra', message=self.result['message'])
        self.write('RESULT.json', self.result)
        self.write('PUBLISH_INTENT.json', self.intent)
        self.evidence = dict(attempt=resolution.ATTEMPT,
            resolution='NOT_PUBLISHED_PREPUBLICATION_HOST_REJECTION',
            journal_id=observer.JOURNAL_ID, source_sha256=self.result['source_sha256'],
            result_sha256=observer.digest(self.directory / 'RESULT.json'),
            intent_sha256=observer.digest(self.directory / 'PUBLISH_INTENT.json'),
            message_sha256=resolution.rejection(self.result, self.intent), endpoint_sha256='endpoint')
        self.evidence['remote'] = dict(message_sha256=self.evidence['message_sha256'], matches=[],
            endpoint_sha256='endpoint', authority=dict(journal_id=observer.JOURNAL_ID,
                pid=699464, start_ticks='33078516', loaded=False, complete_index=5243))

    def write(self, name, value):
        (self.directory / name).write_text(json.dumps(value))

    def test_pinned_rejection_reconciled_without_rewriting_ledger(self):
        before = {path.name: path.read_bytes() for path in self.directory.iterdir()}
        source, result = resolution.validate(self.directory, self.evidence)
        attempts = [dict(source=source, result=result)]
        projected = resolution.project(attempts, self.evidence, source, result)
        self.assertEqual(projected[0]['result']['status'], 'VALIDATION_FAILED')
        self.assertEqual(projected[0]['result']['historical_status'], 'PUBLICATION_UNKNOWN')
        self.assertEqual(attempts[0]['result']['status'], 'PUBLICATION_UNKNOWN')
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.directory.iterdir()})

    def test_network_timeout_or_other_unknown_cannot_be_cleared(self):
        for key, value in (('error', 'connection lost'), ('error_type', 'TimeoutExpired'),
                ('publication', {'id': 'possibly-published'})):
            with self.subTest(key=key), self.assertRaises(ValueError):
                resolution.rejection(dict(self.result, **{key: value}), self.intent)

    def test_existing_inbox_match_rejects_absence_claim(self):
        self.evidence['remote']['matches'] = [{'id': 'actual'}]
        with self.assertRaises(ValueError):
            resolution.validate(self.directory, self.evidence)

    def test_wrong_journal_pid_start_or_load_rejected(self):
        for key, value in (('journal_id', 'other'), ('pid', 598987),
                ('start_ticks', 'wrong'), ('loaded', True), ('complete_index', 5299)):
            changed = copy.deepcopy(self.evidence)
            changed['remote']['authority'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                resolution.validate(self.directory, changed)

    def test_changed_result_source_or_intent_rejected(self):
        for key in ('source_sha256', 'result_sha256', 'intent_sha256', 'message_sha256'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                resolution.validate(self.directory, dict(self.evidence, **{key: 'wrong'}))

    def test_other_unknown_and_duplicate_resolution_stay_blocked(self):
        actual = dict(source=self.source, result=self.result)
        unknown = dict(source=self.source, result=dict(self.result, message='Other attempt.'))
        for attempts in ([actual, unknown], [actual, actual], []):
            with self.subTest(attempts=len(attempts)), self.assertRaises(ValueError):
                resolution.project(attempts, self.evidence, self.source, self.result)

    def test_binding_affects_tick_globals_not_original_function(self):
        namespace = {'local_attempts': lambda output: [dict(source=self.source, result=self.result)]}
        exec('def tick(output):\n    return local_attempts(output)\n', namespace)
        original = namespace['tick']
        policy = types.SimpleNamespace(tick=original, local_attempts=namespace['local_attempts'])
        receipt = Path(self.temporary.name) / 'receipt.json'
        receipt.write_text(json.dumps(self.evidence))
        with patch.object(resolution, 'RECEIPT', receipt):
            resolution.bind(policy, self.directory.parent)
        self.assertEqual(policy.tick(self.directory.parent)[0]['result']['status'], 'VALIDATION_FAILED')
        self.assertEqual(original(self.directory.parent)[0]['result']['status'], 'PUBLICATION_UNKNOWN')


if __name__ == '__main__':
    unittest.main()
