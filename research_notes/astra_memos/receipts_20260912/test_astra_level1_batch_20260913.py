import importlib.util
import json
from pathlib import Path
import unittest


specification = importlib.util.spec_from_file_location('level1_batch_tests', '/tmp/astra_level1_batch_20260913.py')
batch = importlib.util.module_from_spec(specification)
specification.loader.exec_module(batch)


class BatchTests(unittest.TestCase):
    def test_frozen_twelve_unique_allocations(self):
        self.assertEqual(batch.digest(batch.ROSTER), batch.ROSTER_PIN)
        self.assertEqual(batch.digest(batch.DRIVER), batch.DRIVER_PIN)
        entries = json.loads(batch.ROSTER.read_text())['entries']
        self.assertEqual(len(entries), 12)
        self.assertEqual(len({(entry['node'], entry['gpu_index']) for entry in entries}), 12)
        self.assertEqual(len({entry['root'] for entry in entries}), 12)
        for entry in entries:
            self.assertEqual(batch.digest(entry['spec']['path']), entry['spec']['sha256'])
            if entry['node'] == 'node2':
                self.assertNotEqual(entry['gpu_index'], 0)

    def test_visibility_matches_uuid_index_and_all(self):
        for value in ('2', '1, 2', 'GPU-fixture', 'all'):
            self.assertTrue(batch.selected(value, 2, 'GPU-fixture'))
        for value in ('', '12', 'GPU-other', '-1'):
            self.assertFalse(batch.selected(value, 2, 'GPU-fixture'))

    def test_exception_requires_exact_identity_or_transport_ancestor(self):
        config = {'daemon_identities': [], 'uid': 2524}
        record = dict(pid=42, comm='sshd', uid=2524, cmdline_sha256=batch.TRANSPORT_SHA)
        self.assertTrue(batch.known_exception(record, config, {42}))
        self.assertFalse(batch.known_exception(record, config, set()))
        self.assertFalse(batch.known_exception(dict(record, cmdline_sha256='changed'), config, {42}))


if __name__ == '__main__':
    unittest.main()
