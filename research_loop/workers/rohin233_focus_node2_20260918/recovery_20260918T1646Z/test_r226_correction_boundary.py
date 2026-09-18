from copy import deepcopy
import hashlib
import json
import unittest

from r226_correction_boundary import select_cache


def correction(index, cycle):
    record = dict(index=index, kind='R197_CORRECTION_CYCLE', document=dict(ledger=dict(cycles=[dict(cycle=cycle)])))
    record['sha256'] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return record


class CorrectionBoundaryTests(unittest.TestCase):
    def test_restores_existing_pre_boundary_record_not_failed_tail(self):
        complete = dict(kind='SLEEP_COMPLETE', index=20, document=dict(status='COMPLETE', cycle=69))
        records = [correction(10, 68), correction(18, 69), correction(22, 70)]
        before = deepcopy(records)
        self.assertEqual(select_cache(records, complete), dict(record_index=18, record_sha256=records[1]['sha256']))
        self.assertEqual(records, before)

    def test_rejects_future_cycle_and_changed_historical_record(self):
        complete = dict(kind='SLEEP_COMPLETE', index=20, document=dict(status='COMPLETE', cycle=69))
        with self.assertRaisesRegex(ValueError, 'later_cycle'):
            select_cache([correction(18, 70)], complete)
        changed = correction(18, 69)
        changed['document']['ledger']['cycles'][0]['cycle'] = 68
        with self.assertRaisesRegex(ValueError, 'record_hash'):
            select_cache([changed], complete)


if __name__ == '__main__':
    unittest.main()
