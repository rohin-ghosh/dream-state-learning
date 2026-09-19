import hashlib
import unittest

from gpu import orch_r120_route_fork as fork


class ForkPrefixTests(unittest.TestCase):
    def test_inherit_exact_prefix_not_live_sibling_calls(self):
        original = b'{"cycle":39}\n{"cycle":40}\n'
        digest = hashlib.sha256(original).hexdigest()
        self.assertEqual(fork.original_prefix(original + b'{"cycle":41}\n', digest), original)

    def test_no_fabricated_ledger(self):
        with self.assertRaises(ValueError):
            fork.original_prefix(b'changed\n', hashlib.sha256(b'original\n').hexdigest())

    def test_no_unallocated_fork(self):
        with self.assertRaises(ValueError):
            fork.prepare_fork(None, None, None, 7, 'GPU-unknown')
