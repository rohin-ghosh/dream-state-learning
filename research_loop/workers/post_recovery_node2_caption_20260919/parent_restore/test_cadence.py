"""Regression: missing ACT visibility cannot make a delivered parent wait forever."""

import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


endpoint = load('endpoint')
runner = load('runner')


class CadenceTests(unittest.TestCase):
    def request(self, index, content, masked=True):
        return dict(index=index, sha256='request_record_sha', document=dict(
            messages=[dict(content=content)], render_receipt=dict(all_history_tokens_masked=masked)))

    def test_compacted_parent_advances_with_visibility_false_not_uptake(self):
        answer = endpoint.choose_answer(20, [dict(index=23, request_sha256='act')],
                                        {'act': self.request(21, 'parent was compacted')}, 'parent correction')
        self.assertFalse(answer['parent_visible_in_act'])
        self.assertFalse(answer['uptake_established'])

    def test_visible_parent_still_not_evidence_of_uptake(self):
        answer = endpoint.choose_answer(20, [dict(index=23, request_sha256='act')],
                                        {'act': self.request(21, 'parent correction')}, 'parent correction')
        self.assertTrue(answer['parent_visible_in_act'])
        self.assertFalse(answer['uptake_established'])

    def test_prior_request_cannot_acknowledge_new_inbox(self):
        self.assertIsNone(endpoint.choose_answer(20, [dict(index=23, request_sha256='act')],
                                                {'act': self.request(19, 'parent correction')}, 'parent correction'))

    def test_missing_request_cannot_invent_delivery(self):
        self.assertIsNone(endpoint.choose_answer(20, [dict(index=23, request_sha256='act')], {}, 'parent correction'))

    def test_external_parent_mask_remains_required(self):
        with self.assertRaisesRegex(ValueError, 'external_parent_tokens_masked'):
            endpoint.choose_answer(20, [dict(index=23, request_sha256='act')],
                                   {'act': self.request(21, 'parent correction', False)}, 'parent correction')

    def test_only_first_subsequent_act_is_used(self):
        answer = endpoint.choose_answer(20, [dict(index=23, request_sha256='first'), dict(index=27, request_sha256='second')],
                                        {'first': self.request(21, 'absent'), 'second': self.request(25, 'parent correction')},
                                        'parent correction')
        self.assertEqual(answer['actual_act']['index'], 23)
        self.assertFalse(answer['parent_visible_in_act'])

    def test_ambiguous_provider_attempt_never_reissued(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'turn_0035').mkdir()
            with self.assertRaisesRegex(ValueError, 'requires_reconciliation'):
                runner.recovery_state(directory, None)

    def test_restart_preserves_unanswered_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            attempt = directory / 'turn_0035'
            attempt.mkdir()
            (attempt / 'PUBLISHED.json').write_text(json.dumps(dict(text='actual parent', source_index=44,
                publication=dict(id='existing-publication', sha256='existing-sha'))))
            attempts, pending, prior, latest = runner.recovery_state(directory, None)
            self.assertEqual(pending['publication']['id'], 'existing-publication')
            self.assertEqual(latest, 44)
            self.assertEqual(len(attempts), 1)
            self.assertEqual(prior, [])

    def test_old_and_new_budgets_are_not_reset(self):
        self.assertEqual(endpoint.HARD_END, 1789927200)
        self.assertEqual((endpoint.PID, endpoint.START, endpoint.LOADED), (1800978, 101994417, 8529))

    def publication_fixture(self, directory):
        helper = SimpleNamespace(checked_record=lambda path: dict(kind='RESPONSE', index=9000, sha256='source'),
                                 sha=lambda raw: 'text_sha', read=lambda path: json.loads(path.read_text()))
        request = dict(number=35, text='One grounded question?', source_index=9000, source_sha256='source')
        body = dict(number=35, text_sha256='text_sha', source_index=9000, source_sha256='source')
        (directory / 'INTENT_0035.json').write_text(json.dumps(body))
        return helper, request

    def test_remote_ambiguous_publication_is_never_republished(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            helper, request = self.publication_fixture(directory)
            with patch.object(endpoint, 'STORE', directory), patch.object(endpoint, 'identity', return_value=(helper, {}, {})):
                with self.assertRaisesRegex(ValueError, 'ambiguous_publication_no_automatic_retry'):
                    endpoint.publish(request)

    def test_remote_completed_publication_returns_original_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            helper, request = self.publication_fixture(directory)
            receipt = dict(publication=dict(id='same-id', sha256='same-sha'))
            (directory / 'PUBLISHED_0035.json').write_text(json.dumps(receipt))
            with patch.object(endpoint, 'STORE', directory), patch.object(endpoint, 'identity', return_value=(helper, {}, {})):
                self.assertEqual(endpoint.publish(request), receipt)

    def test_conflicting_publication_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            helper, request = self.publication_fixture(directory)
            request['source_index'] = 9001
            helper.checked_record = lambda path: dict(kind='RESPONSE', index=9001, sha256='source')
            with patch.object(endpoint, 'STORE', directory), patch.object(endpoint, 'identity', return_value=(helper, {}, {})):
                with self.assertRaisesRegex(ValueError, 'conflicting_parent_publication'):
                    endpoint.publish(request)


if __name__ == '__main__':
    unittest.main()
