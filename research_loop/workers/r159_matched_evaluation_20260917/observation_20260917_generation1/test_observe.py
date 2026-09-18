import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest


spec = importlib.util.spec_from_file_location('observation', Path(__file__).with_name('observe.py'))
observation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observation)


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.reader = observation.Reader(self.root, end=time.time() + 60)

    def test_bound_and_regular(self):
        path = self.root / 'file'
        path.write_bytes(b'abcdef')
        self.reader.limit = 3
        with self.assertRaises(ValueError):
            self.reader.read(path)
        self.assertEqual(self.reader.bytes, 0)

    def test_symlink(self):
        (self.root / 'target').write_bytes(b'x')
        (self.root / 'link').symlink_to(self.root / 'target')
        with self.assertRaises(ValueError):
            self.reader.read(self.root / 'link')

    def test_expiry(self):
        self.reader.end = 0
        with self.assertRaises(ValueError):
            self.reader.read(self.root / 'missing')

    def test_duplicate_json(self):
        with self.assertRaises(ValueError):
            observation.decode(b'{"index":1,"index":2}')

    def test_readout_allowlist(self):
        directory = self.root / 'readouts'
        directory.mkdir()
        (directory / 'sleep_000000_R150_OPEN.json').write_text(json.dumps(dict(
            opened_unix=10, prompt='DO_NOT_RETURN', binding=dict(cycle=0, answer='DO_NOT_RETURN'))))
        (directory / 'sleep_000000.json').write_text('SECRET_SCORE_DO_NOT_OPEN')
        (directory / 'sleep_000000.log').write_text('SECRET_LOG_DO_NOT_OPEN')
        result = observation.readouts(self.reader, self.root)
        self.assertEqual(self.reader.files, 1)
        self.assertNotIn('DO_NOT', json.dumps(result))
        self.assertFalse(result['coverage_complete'])

    def test_missing_is_unknown(self):
        result = observation.readouts(self.reader, self.root)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertFalse(result['coverage_complete'])

    def test_journal_header_only_and_chain(self):
        directory = self.root / 'stream/records'
        directory.mkdir(parents=True)
        manifest = dict(schema='test', journal_id='test')
        (directory.parent / 'JOURNAL.json').write_bytes(observation.canonical(manifest))
        previous = observation.digest(observation.canonical(manifest))
        record = dict(schema='test', journal_id='test', index=0, kind='REQUEST',
            previous_sha256=previous, document=dict(started_unix=1, segment=0, split='TRAIN',
                messages='PRIVATE_TRAIN_TEXT'))
        record['sha256'] = observation.digest(observation.canonical(record))
        intent = dict(schema='test', journal_id='test', index=0, previous_sha256=previous,
            record_sha256=record['sha256'])
        path = directory / '00000000000000000000.json'
        path.write_bytes(observation.canonical(record))
        (directory / '00000000000000000000.intent.json').write_bytes(observation.canonical(intent))
        result = observation.journal(self.reader, self.root)
        self.assertEqual(result['status'], 'VERIFIED_RETAINED_PREFIX')
        self.assertEqual(result['first_train_request']['started_unix'], 1)
        self.assertNotIn('PRIVATE_TRAIN_TEXT', json.dumps(result))
        self.assertFalse(result['coverage_complete'])
        record['document']['started_unix'] = 2
        path.write_bytes(observation.canonical(record))
        self.assertEqual(observation.journal(self.reader, self.root)['status'], 'INCOMPLETE')


if __name__ == '__main__':
    unittest.main()
