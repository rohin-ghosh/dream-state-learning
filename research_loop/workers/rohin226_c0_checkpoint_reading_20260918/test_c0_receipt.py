import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location('c0_receipt', Path(__file__).with_name('c0_receipt.py'))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReceiptTests(unittest.TestCase):
    def test_question_not_supplied_solution(self):
        self.assertIn('Ask one genuine follow-up question', MODULE.BRIEF)
        self.assertIn(MODULE.EXCERPT, MODULE.BRIEF)
        self.assertNotIn('n^2', MODULE.BRIEF)
        self.assertTrue(MODULE.BRIEF.isascii())

    def test_actual_record_hash_and_tamper(self):
        record = dict(index=597, kind='RESPONSE', document={'raw': 'literal'})
        record['sha256'] = MODULE.sha(MODULE.canonical(record))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '00000000000000000597.json'
            path.write_text(json.dumps(record))
            self.assertEqual(MODULE.checked_record(path), record)
            record['document']['raw'] = 'changed'
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'actual_record_hash'):
                MODULE.checked_record(path)

    def test_response_preserves_raw_and_requires_matching_stage(self):
        record = dict(index=597, sha256='a' * 64, document=dict(finished_unix=1789718096,
            response=dict(raw='raw\nunchanged')))
        stage = dict(index=599, sha256='b' * 64, kind='R184_STAGE', document=dict(stage='ACT',
            source_sha256=MODULE.sha(MODULE.canonical(record['document']))))
        result = MODULE.response_receipt(record, [stage])
        self.assertEqual(result['raw'], 'raw\nunchanged')
        self.assertEqual(result['stage_index'], 599)
        stage['document']['source_sha256'] = 'c' * 64
        self.assertEqual(MODULE.response_receipt(record, [stage])['stage'], 'UNVERIFIED')


if __name__ == '__main__':
    unittest.main()
