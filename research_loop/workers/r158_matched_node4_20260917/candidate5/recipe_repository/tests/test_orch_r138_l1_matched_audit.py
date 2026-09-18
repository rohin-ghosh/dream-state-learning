import tempfile
from pathlib import Path
import unittest

from gpu import orch_r138_l1_matched_audit as audit


class ComparisonTests(unittest.TestCase):
    def test_count_flips_separately_from_text_changes(self):
        before = {'one': {'passed': False, 'raw_hash': 'a'},
                  'two': {'passed': True, 'raw_hash': 'b'}}
        after = {'one': {'passed': True, 'raw_hash': 'c'},
                 'two': {'passed': False, 'raw_hash': 'b'}}
        result = audit.compare(before, after)
        self.assertEqual(result['newly_passing'], 1)
        self.assertEqual(result['newly_failing'], 1)
        self.assertEqual(result['identical_raw_outputs'], 1)

    def test_unchanged_results_can_change_text(self):
        before = {'one': {'passed': False, 'raw_hash': 'a'}}
        after = {'one': {'passed': False, 'raw_hash': 'b'}}
        result = audit.compare(before, after)
        self.assertEqual(result['newly_passing'], 0)
        self.assertEqual(result['newly_failing'], 0)
        self.assertEqual(result['identical_raw_outputs'], 0)

    def test_reject_case_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'paired_case_set_mismatch'):
            audit.compare({'one': {}}, {'two': {}})

    def test_reject_empty_comparison(self):
        with self.assertRaisesRegex(ValueError, 'empty_comparison'):
            audit.compare({}, {})

    def test_shape_is_descriptive_and_no_text_exported(self):
        result = audit.shape([
            dict(raw='PRIVATE_SENTINEL\n', token_ids=[1, 2], terminal=True, truncated=False),
            dict(raw='first\nsecond', token_ids=[1, 2, 3, 4], terminal=False, truncated=True)])
        self.assertEqual(result['single_line'], 1)
        self.assertEqual(result['median_generated_tokens'], 3)
        self.assertEqual(result['truncated'], 1)
        self.assertNotIn('PRIVATE_SENTINEL', str(result))

    def test_identity_includes_start_and_boot(self):
        first = audit.process_key(dict(pid=12, start_ticks='34', boot_id='a'))
        second = audit.process_key(dict(pid=12, start_ticks='35', boot_id='a'))
        self.assertNotEqual(first, second)

    def test_reject_partial_identity(self):
        with self.assertRaisesRegex(ValueError, 'native_identity_required'):
            audit.process_key(dict(pid=12))


class IntegrityTests(unittest.TestCase):
    def test_manifest_detects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            path.write_text('{"test": 1}')
            tracker = audit.Audit()
            self.assertEqual(tracker.read(path), {'test': 1})
            tracker.verify_unchanged()
            path.write_text('{"test": 2}')
            with self.assertRaisesRegex(ValueError, 'artifact_changed'):
                tracker.verify_unchanged()

    def test_repeat_read_detects_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            path.write_text('{}')
            tracker = audit.Audit()
            tracker.read(path)
            path.write_text('{"changed": true}')
            with self.assertRaisesRegex(ValueError, 'artifact_changed'):
                tracker.read(path)

    def test_checkpoint_relative_path(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(audit.safe_child(directory, 'adapter/state'),
                Path(directory) / 'adapter/state')
            for name in ('../secret', '/etc/passwd'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    audit.safe_child(directory, name)

    def test_checkpoint_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'escape').symlink_to('/etc')
            with self.assertRaisesRegex(ValueError, 'checkpoint_path_escape'):
                audit.safe_child(directory, 'escape/passwd')


if __name__ == '__main__':
    unittest.main()
