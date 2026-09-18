import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_r127_protocol_shape as shape


class ProtocolShapeTests(unittest.TestCase):
    def test_literal_commands_and_outer_whitespace(self):
        self.assertTrue(shape.protocol_only('READ EVENT E_123'))
        self.assertTrue(shape.protocol_only('  ROUTE P_123\n'))

    def test_prose_and_multiple_commands_are_not_protocol_only(self):
        for raw in ('Consider the record.\nROUTE P_1', 'ROUTE P_1\nROUTE P_2',
                    'I will READ EVENT E_1', '', 'STOP'):
            self.assertFalse(shape.protocol_only(raw))

    def test_tokens_are_observed_eos_inclusive_not_claimed_reasoning(self):
        result = shape.summarize([dict(raw='ROUTE P_1', token_ids=[1, 2]),
                                  dict(raw='why?\nROUTE P_2', token_ids=[1, 2, 3, 4])])
        self.assertEqual(result['literal_protocol_only'], 1)
        self.assertEqual(result['generated_tokens_including_eos'], 6)
        self.assertEqual(result['median_tokens_per_call_including_eos'], 3)
        self.assertEqual(result['reasoning_quality'], 'NOT_MEASURED')

    def test_missing_text_or_tokens_is_not_imputed(self):
        with self.assertRaises(ValueError):
            shape.summarize([dict(raw='ROUTE P_1', token_ids=[])])
        with self.assertRaises(ValueError):
            shape.summarize([dict(raw=None, token_ids=[1])])

    def test_exact_path_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / 'receipt.json'
            path.write_text('{}')
            reference = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(shape.checked(reference, path), {})
            with self.assertRaises(ValueError):
                shape.checked(reference, path.with_name('other.json'))
            path.write_text('{"changed": true}')
            with self.assertRaises(ValueError):
                shape.checked(reference, path)

    def test_incomplete_verification_never_classified(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'verified.json'
            path.write_text(json.dumps(dict(schema='R127_VERIFIED_RESULTS_V1',
                                            status='INCOMPLETE', errors=[])))
            with self.assertRaises(ValueError):
                shape.audit(path)


if __name__ == '__main__':
    unittest.main()
