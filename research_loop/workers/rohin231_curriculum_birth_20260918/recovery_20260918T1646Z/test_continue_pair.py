from copy import deepcopy
import unittest

from continue_pair import boundary
from extension_spec import digest


class BoundaryTests(unittest.TestCase):
    def records(self):
        state = dict(pending=None, sleep_frontier=1, rows=[{}], sleep_receipts=[dict(status='COMPLETE')])
        return [dict(index=4, kind='SLEEP_COMPLETE', document=dict(resume_state=dict(state=state, sha256=digest(state)))),
            dict(index=5, kind='R184_LEARN_COMPLETE')]

    def test_exact_boundary(self):
        self.assertEqual(boundary(self.records())['index'], 4)

    def test_generation_or_inbox_after_boundary_is_not_ready(self):
        for kind in ('REQUEST', 'INBOX', 'CONTEXT_INPUT', 'UPDATE', 'SLEEP_REQUEST'):
            records = self.records()
            records.append(dict(index=6, kind=kind))
            self.assertIsNone(boundary(records))

    def test_pending_or_untrained_state_is_rejected(self):
        for key, value in (('pending', 'request'), ('sleep_frontier', 0)):
            records = deepcopy(self.records())
            saved = records[0]['document']['resume_state']
            saved['state'][key] = value
            saved['sha256'] = digest(saved['state'])
            with self.assertRaises(ValueError):
                boundary(records)

    def test_missing_driver_completion(self):
        self.assertIsNone(boundary(self.records()[:1]))


if __name__ == '__main__':
    unittest.main()
