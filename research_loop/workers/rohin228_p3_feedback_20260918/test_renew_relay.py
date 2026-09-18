from pathlib import Path
import tempfile
import unittest

import renew_relay as subject


class RenewalTests(unittest.TestCase):
    def command(self):
        arguments = ['python3', '-B', str(subject.SOURCE), '--life', subject.LIFE,
                     '--output', str(subject.ROOT / 'relay')]
        for session in subject.SESSIONS:
            arguments.extend(('--session', session))
        return arguments + ['--end-unix', str(subject.OLD_END)]

    def test_only_expiry_changes_for_the_exact_cpu_writer(self):
        original = self.command()
        changed = subject.renewed_command(original, subject.NEW_END)
        self.assertEqual(original[:-1], changed[:-1])
        self.assertEqual(float(changed[-1]), subject.NEW_END)

    def test_wrong_life_source_pid_shape_or_sessions_rejected(self):
        for index in (0, 2, 4, 6, 8, 10, 12, 14):
            modified = self.command()
            modified[index] = 'other'
            with self.subTest(index=index), self.assertRaises(ValueError):
                subject.renewed_command(modified, subject.NEW_END)

    def test_expiry_cannot_be_shortened_or_unbounded(self):
        for expiry in (subject.OLD_END, subject.OLD_END - 1, subject.NEW_END + 1):
            with self.subTest(expiry=expiry), self.assertRaises(ValueError):
                subject.renewed_command(self.command(), expiry)

    def test_dedup_inventory_allows_new_but_never_changed_or_removed_receipts(self):
        before = {'published/one.json': 'a', 'projections/one.json': 'b'}
        subject.verify_preserved(before, dict(before, extra='c'))
        for after in ({}, {**before, 'published/one.json': 'changed'}):
            with self.assertRaises(ValueError):
                subject.verify_preserved(before, after)

    def test_inventory_hashes_only_immutable_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'published').mkdir()
            path = root / 'published/one.json'
            path.write_text('{}')
            (root / 'WRITER.lock').touch()
            self.assertEqual(subject.inventory(root), {'published/one.json': subject.checksum(path)})


if __name__ == '__main__':
    unittest.main()
