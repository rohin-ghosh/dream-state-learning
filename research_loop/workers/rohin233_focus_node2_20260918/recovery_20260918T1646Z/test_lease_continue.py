"""No signals, model calls or real process operations in these tests."""

import unittest

from lease_continue import at_boundary, paths


class BoundaryTests(unittest.TestCase):
    def test_only_matching_completed_boundary(self):
        complete = dict(index=101, kind='SLEEP_COMPLETE', journal_id='same')
        self.assertTrue(at_boundary(complete, complete))
        self.assertTrue(at_boundary(dict(index=102, kind='R184_LEARN_COMPLETE', journal_id='same'), complete))
        for head in (dict(index=103, kind='R184_LEARN_COMPLETE', journal_id='same'),
                dict(index=102, kind='REQUEST', journal_id='same'),
                dict(index=102, kind='CONTEXT_INPUT', journal_id='same'),
                dict(index=102, kind='R184_LEARN_COMPLETE', journal_id='other')):
            self.assertFalse(at_boundary(head, complete))

    def test_caption_is_excluded(self):
        with self.assertRaises(ValueError):
            paths('CAPTION')
        self.assertTrue(str(paths('C0')[1]).endswith('/source_r233_lease_continuation'))

    def test_learn_complete_requires_sleep_complete_predecessor(self):
        head = dict(index=102, kind='R184_LEARN_COMPLETE', journal_id='same')
        for kind in ('UPDATE', 'REQUEST', 'R184_LEARN_COMPLETE'):
            self.assertFalse(at_boundary(head, dict(index=101, kind=kind, journal_id='same')))


if __name__ == '__main__':
    unittest.main()
