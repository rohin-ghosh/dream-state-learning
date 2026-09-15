import tempfile
import unittest
from pathlib import Path

from gpu.orch_route_parent_campaign_mirror import inventory, verify


class MirrorTests(unittest.TestCase):
    def test_hash_verification_detects_changed_and_missing_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'response.json'
            path.write_text('original')
            records = inventory(root)
            self.assertTrue(verify(root, records)['verified'])
            path.write_text('changed!')
            self.assertFalse(verify(root, records)['verified'])
            path.unlink()
            self.assertFalse(verify(root, records)['verified'])

    def test_does_not_delete_or_claim_future_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'response').write_text('kept')
            result = verify(root, inventory(root))
            self.assertFalse(result['deletion_performed'])
            self.assertEqual((root / 'response').read_text(), 'kept')
            self.assertIn('not_future_writes', result['scope'])

    def test_rejects_paths_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('../outside', '/absolute'):
                with self.assertRaises(ValueError):
                    verify(root, [dict(path=name)])
            (root / 'link').symlink_to('/tmp')
            with self.assertRaises(ValueError):
                inventory(root)

    def test_rejects_duplicate_inventory_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'response').write_text('kept')
            records = inventory(root)
            with self.assertRaises(ValueError):
                verify(root, records + records)
