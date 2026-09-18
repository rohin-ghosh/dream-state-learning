import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from parent_http_retry import bounded_strong


class RetryTests(unittest.TestCase):
    def test_known_failure_retries_same_input_once(self):
        for status in (404, 503):
            calls = []
            receipts = []
            def original(*args, **kwargs):
                calls.append((args, kwargs))
                if len(calls) == 1:
                    raise urllib.error.HTTPError('https://[REDACTED_HOST]/v1/responses', status, 'known', {}, None)
                return 'real-result'
            with patch.object(Path, 'exists', return_value=False), patch.object(Path, 'mkdir'):
                result = bounded_strong(original, 'same source', '/owned/call', 9999999999, 'instruction', 'low',
                    record=lambda path, value: receipts.append((path, value)), sleep=lambda seconds: None)
            self.assertEqual(result, 'real-result')
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][0][0], calls[1][0][0])
            self.assertEqual(calls[0][0][2:], calls[1][0][2:])
            self.assertEqual(calls[0][1], calls[1][1])

    def test_unknown_network_outcome_is_not_retried(self):
        calls = []
        def original(*args, **kwargs):
            calls.append(args)
            raise TimeoutError('unknown outcome')
        with self.assertRaises(TimeoutError):
            bounded_strong(original, 'source', '/owned/call', 9999999999, 'instruction', 'low', record=lambda *args: None)
        self.assertEqual(len(calls), 1)

    def test_publication_intent_and_other_HTTP_codes_do_not_retry(self):
        for status, intent in ((404, True), (503, True), (401, False), (500, False)):
            calls = []
            def original(*args, **kwargs):
                calls.append(args)
                raise urllib.error.HTTPError('https://[REDACTED_HOST]/v1/responses', status, 'error', {}, None)
            with patch.object(Path, 'exists', return_value=intent), self.assertRaises(urllib.error.HTTPError):
                bounded_strong(original, 'source', '/owned/call', 9999999999, 'instruction', 'low', record=lambda *args: None)
            self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
