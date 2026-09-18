"""Local immutable-reader regressions for standalone clean-checkout use."""

import json
from pathlib import Path
import tempfile
import unittest

import journal_reader as reader


class ReaderTests(unittest.TestCase):
    def test_canonical_envelope_and_committed_projection(self):
        state = dict(pending=None, rows=[dict(actor='child', source_sha256='b' * 64,
                                            segment=3, target='SYNTHETIC_PRIVATE_TARGET')])
        record = dict(document=dict(source_sha256='b' * 64,
                                    state=dict(state=state, sha256=reader.digest(state))),
                      index=1, kind='COMMITTED', journal_id='fixture', previous_sha256='0' * 64)
        record['sha256'] = reader.digest(record)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '00000000000000000001.json'
            path.write_text(json.dumps(record, separators=(',', ':')))
            self.assertEqual(reader.metadata(path)['sha256'], record['sha256'])
            projection = reader.reduced(path, 'fixture', Path(directory))
            self.assertTrue(projection['committed_row_verified'])
            self.assertNotIn('SYNTHETIC_PRIVATE_TARGET', json.dumps(projection))
            record['document']['source_sha256'] = 'c' * 64
            path.write_text(json.dumps(record, separators=(',', ':')))
            with self.assertRaisesRegex(ValueError, 'record_hash_mismatch'):
                reader.verified(path, 'fixture')

    def test_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'target'
            target.write_text('synthetic')
            link = Path(directory) / 'link'
            link.symlink_to(target)
            with self.assertRaises(OSError):
                reader.read_bytes(link)


if __name__ == '__main__':
    unittest.main()
