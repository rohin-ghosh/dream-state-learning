import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from retired_coalescer import digest
import verify_remaining_completion as audit


class CompletionAuditTests(unittest.TestCase):
    def write_chain(self, directory, entries):
        path = Path(directory) / 'ledger.jsonl'
        path.write_text(''.join(json.dumps(entry) + '\n' for entry in entries))
        return path

    def event(self, sequence=0, previous='0' * 64, ordinal=1):
        entry = dict(sequence=sequence, previous_sha256=previous,
            kind='REMAINING_BATCH_POSTCHECK', document=dict(ordinal=ordinal))
        entry['sha256'] = digest(entry)
        return entry

    def test_exact_chain_and_postcheck_preserved(self):
        first = self.event()
        second = self.event(sequence=1, previous=first['sha256'], ordinal=2)
        with TemporaryDirectory() as directory:
            result = audit.verify_chain(self.write_chain(directory, [first, second]))
        self.assertEqual(result['sequence'], 2)
        self.assertEqual(result['postchecks'][2], second)

    def test_sequence_gap_rejected(self):
        with TemporaryDirectory() as directory:
            path = self.write_chain(directory, [self.event(sequence=1)])
            with self.assertRaisesRegex(ValueError, 'contiguous'):
                audit.verify_chain(path)

    def test_rehashed_duplicate_batch_rejected(self):
        first = self.event()
        second = self.event(sequence=1, previous=first['sha256'])
        with TemporaryDirectory() as directory:
            path = self.write_chain(directory, [first, second])
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                audit.verify_chain(path)

    def test_changed_event_body_rejected(self):
        changed = self.event()
        changed['document']['ordinal'] = 99
        with TemporaryDirectory() as directory:
            path = self.write_chain(directory, [changed])
            with self.assertRaisesRegex(ValueError, 'content_hash'):
                audit.verify_chain(path)


if __name__ == '__main__':
    unittest.main()
