import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import urllib.error

import runner


class BackoffTests(unittest.TestCase):
    def test_no_header_uses_minute_then_exponential_backoff(self):
        self.assertEqual(runner.backoff_seconds({}, 1, 100), 60)
        self.assertEqual(runner.backoff_seconds({}, 2, 100), 120)
        self.assertEqual(runner.backoff_seconds({}, 9, 100), 300)

    def test_retry_after_never_shortened(self):
        self.assertEqual(runner.backoff_seconds({'Retry-After': '900'}, 1, 100), 900)
        self.assertEqual(runner.backoff_seconds({'Retry-After': '2'}, 1, 100), 60)

    def test_http_date_and_malformed_header(self):
        self.assertEqual(runner.backoff_seconds({'Retry-After': 'Thu, 01 Jan 1970 00:20:00 GMT'}, 1, 100), 1100)
        self.assertEqual(runner.backoff_seconds({'Retry-After': 'not-a-date'}, 1, 100), 60)

    def test_429_preserves_error_and_does_not_retry_or_consume_new_boundary(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'HERE', Path(directory)), patch.object(runner.time, 'time', return_value=100):
            error = urllib.error.HTTPError('https://provider.invalid', 429, 'quota', {'Retry-After': '180'}, None)
            original = Mock(side_effect=error)
            policy = types.SimpleNamespace(parent=types.SimpleNamespace(strong=original))
            module = types.SimpleNamespace(tick_once=Mock(return_value='original'))
            original_tick = module.tick_once
            runner.install_backoff(module, policy)
            with self.assertRaises(urllib.error.HTTPError):
                policy.parent.strong('payload', Path(directory)/'attempt', 1000)
            self.assertEqual(original.call_count, 1)
            self.assertEqual(module.tick_once()['status'], 'PROVIDER_BACKOFF')
            original_tick.assert_not_called()
            stored = json.loads(Path(directory, 'operator/RATE_LIMIT.json').read_text())
            self.assertEqual(stored['not_before_unix'], 280)
            with self.assertRaisesRegex(ValueError, 'backoff_not_elapsed'):
                policy.parent.strong('payload', Path(directory)/'attempt2', 1000)
            self.assertEqual(original.call_count, 1)

    def test_without_backoff_original_tick_and_gates_are_called(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'HERE', Path(directory)):
            original = Mock(return_value={'status':'AWAITING_RENDER'})
            module = types.SimpleNamespace(tick_once=original)
            policy = types.SimpleNamespace(parent=types.SimpleNamespace(strong=Mock()))
            runner.install_backoff(module, policy)
            self.assertEqual(module.tick_once('unchanged')['status'], 'AWAITING_RENDER')
            original.assert_called_once_with('unchanged')

    def test_model_and_effort_are_not_changed(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'HERE', Path(directory)):
            folder = Path(directory)/'attempt'
            folder.mkdir()
            folder.joinpath('API_REQUEST.json').write_text(json.dumps(dict(model=runner.MODEL,reasoning={'effort':'xhigh'})))
            folder.joinpath('stdout.json').write_text('{}')
            original = Mock(return_value=('response','model',{}))
            policy = types.SimpleNamespace(parent=types.SimpleNamespace(strong=original))
            runner.install_backoff(types.SimpleNamespace(tick_once=Mock()), policy)
            self.assertEqual(policy.parent.strong('same payload',folder,1000,reasoning_effort='low'), ('response','model',{}))
            original.assert_called_once_with('same payload',folder,1000,reasoning_effort='low')

    def test_non_xhigh_request_cannot_be_published(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'HERE', Path(directory)):
            folder = Path(directory)/'attempt'
            folder.mkdir()
            folder.joinpath('API_REQUEST.json').write_text(json.dumps(dict(model=runner.MODEL,reasoning={'effort':'low'})))
            policy = types.SimpleNamespace(parent=types.SimpleNamespace(strong=Mock(return_value=('response','model',{}))))
            runner.install_backoff(types.SimpleNamespace(tick_once=Mock()), policy)
            with self.assertRaisesRegex(ValueError,'exact_xhigh_provider'):
                policy.parent.strong('payload',folder,1000)


if __name__ == '__main__':
    unittest.main()
