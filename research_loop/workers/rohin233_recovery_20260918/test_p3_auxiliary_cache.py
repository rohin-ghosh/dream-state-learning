from copy import deepcopy
import hashlib
import json
import unittest

from p3_auxiliary_cache import select_cache


def correction(index, cycle):
    record = dict(index=index, kind='R197_CORRECTION_CYCLE', document=dict(ledger=dict(cycles=[dict(cycle=cycle)])))
    record['sha256'] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return record


class AuxiliaryCacheTests(unittest.TestCase):
    def test_discarded_cycle_never_reused_after_complete_restore(self):
        complete = dict(kind='SLEEP_COMPLETE', index=5243, document=dict(status='COMPLETE', cycle=153))
        records = [correction(5210, 153), correction(5260, 154)]
        original = deepcopy(records)
        self.assertEqual(select_cache(records, complete),
            dict(record_index=5210, record_sha256=records[0]['sha256']))
        self.assertEqual(records, original)

    def test_future_cycle_or_changed_record_cannot_be_selected(self):
        complete = dict(kind='SLEEP_COMPLETE', index=5243, document=dict(status='COMPLETE', cycle=153))
        with self.assertRaisesRegex(ValueError, 'later_cycle'):
            select_cache([correction(5210, 154)], complete)
        record = correction(5210, 153)
        record['document']['ledger']['cycles'][0]['cycle'] = 152
        with self.assertRaisesRegex(ValueError, 'record_hash'):
            select_cache([record], complete)


if __name__ == '__main__':
    unittest.main()
