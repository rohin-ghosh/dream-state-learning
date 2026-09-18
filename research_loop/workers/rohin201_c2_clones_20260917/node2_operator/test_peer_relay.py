"""Peer transport tests use synthetic state, never a live inbox."""

import unittest

from peer_relay import capsule, digest


class PeerRelayTests(unittest.TestCase):
    def complete(self):
        return dict(kind='R184_LEARN_COMPLETE', document=dict(cycle=52,
            working_state=dict(revision=2, entries=[dict(kind='uncertainty', text='Synthetic uncertainty.')])) )

    def test_capsule_attributes_environment_and_does_not_export_hash_fields(self):
        result = capsule('math_d1', self.complete())
        self.assertIn('Synthetic uncertainty.', result)
        self.assertIn('not parent guidance', result)
        self.assertNotIn('source_sha256', result)
        self.assertNotIn('receipt_sha256', result)

    def test_original_source_or_unknown_sender_is_refused(self):
        complete = self.complete()
        complete['document']['cycle'] = 51
        with self.assertRaises(ValueError):
            capsule('math_d1', complete)
        with self.assertRaises(ValueError):
            capsule('original_C2', self.complete())

    def test_state_digest_is_content_bound(self):
        self.assertNotEqual(digest(self.complete()), digest(dict(self.complete(), other=True)))


if __name__ == '__main__':
    unittest.main()
