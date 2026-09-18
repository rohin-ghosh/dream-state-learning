import copy
import types
import unittest

import p3_continued_endpoint as endpoint


class ContinuedEndpointTests(unittest.TestCase):
    def setUp(self):
        self.binding = dict(hard_end_unix=endpoint.END_UNIX,
            journal_id=endpoint.previous.JOURNAL_ID, source=str(endpoint.SOURCE), pid=999)
        self.guard = dict(hard_end_unix=endpoint.END_UNIX)
        self.lease = dict(hard_end_unix=endpoint.END_UNIX, lease_end_unix=endpoint.END_UNIX + 21600)

    def test_actual_renewal_accepts_after_obsolete_cutoff(self):
        endpoint.verify_bound(self.binding, self.guard, self.lease, 1789754700)

    def test_mismatched_or_expired_bounds_fail(self):
        for field, value in (('pid', endpoint.previous.PID), ('source', 'old/source'),
                             ('hard_end_unix', endpoint.END_UNIX + 1)):
            changed = dict(self.binding, **{field: value})
            with self.assertRaises(ValueError):
                endpoint.verify_bound(changed, self.guard, self.lease, 1789754700)
        with self.assertRaises(ValueError):
            endpoint.verify_bound(self.binding, self.guard, self.lease, endpoint.END_UNIX)

    def test_only_verified_recovery_resets_pending(self):
        calls = []
        snapshot = types.SimpleNamespace(_reduce=lambda state, record: calls.append(record))
        receipt = dict(old_head_index=10, old_head_sha256='head', saved_state_sha256='saved')
        endpoint.bind_recovery_reducer(snapshot, receipt)
        record = dict(kind='R233_P3_RECOVERED_BOUNDARY', index=11,
            previous_sha256='head', document=dict(state=dict(sha256='saved')))
        state = dict(pending={'segment': 1}, response={'raw': 'unfinished'})
        bad = copy.deepcopy(record)
        bad['index'] = 12
        with self.assertRaises(ValueError):
            snapshot._reduce(state, bad)
        self.assertIsNotNone(state['pending'])
        snapshot._reduce(state, record)
        self.assertEqual(state, dict(pending=None, response=None))
        snapshot._reduce(state, dict(kind='SLEEP_COMPLETE'))
        self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
