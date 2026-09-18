import subprocess
import unittest

import p3_recovery
import p3_endpoint


class RecoveryTests(unittest.TestCase):
    def test_incremental_endpoint_never_opens_other_lives_or_new_birth(self):
        for operation in ('poll', 'publish'):
            p3_endpoint.check_request(dict(physical=3, op=operation))
        for physical, operation in ((7, 'poll'), (3, 'opening'), (3, 'restart')):
            with self.assertRaises(ValueError):
                p3_endpoint.check_request(dict(physical=physical, op=operation))

    def test_timeout_retries_only_read_poll_with_same_reference(self):
        calls, events = [], []
        request = dict(op='poll', reference={'sha256': 'fixed'})

        def remote(physical, payload):
            calls.append((physical, payload))
            if len(calls) == 1:
                raise subprocess.TimeoutExpired('redacted', 90)
            return {'snapshot': 'actual'}

        wrapped = p3_recovery.recover_poll(remote, 100, events.append,
                                          clock=lambda: 0, sleeper=lambda seconds: None)
        self.assertEqual(wrapped(3, request), {'snapshot': 'actual'})
        self.assertEqual(calls, [(3, request), (3, request)])
        self.assertFalse(events[0]['publication_retried'])

    def test_publication_and_other_lives_are_not_retried(self):
        def remote(*arguments):
            raise subprocess.TimeoutExpired('redacted', 90)

        wrapped = p3_recovery.recover_poll(remote, 100, lambda event: None)
        for physical, operation in ((3, 'publish'), (7, 'poll')):
            with self.assertRaises(subprocess.TimeoutExpired):
                wrapped(physical, dict(op=operation))

    def test_timeout_does_not_extend_deadline(self):
        def remote(*arguments):
            raise subprocess.TimeoutExpired('redacted', 90)

        wrapped = p3_recovery.recover_poll(remote, 0, lambda event: None,
                                          clock=lambda: 1)
        with self.assertRaises(subprocess.TimeoutExpired):
            wrapped(3, dict(op='poll'))

    def test_brief_requests_artifact_and_preserves_no_exclusion(self):
        for phrase in ('one actual funny caption', 'not a plan', 'Do not supply',
                       'No training exclusions', 'Tool receipt'):
            self.assertIn(phrase, p3_recovery.BRIEF)


if __name__ == '__main__':
    unittest.main()
