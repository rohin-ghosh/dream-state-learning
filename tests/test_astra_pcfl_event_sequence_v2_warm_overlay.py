import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import astra_pcfl_event_sequence_v2_warm_overlay as api


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source, self.destination = self.root / 'old', self.root / 'new'
        self.original = self.source / api.RELATIVE
        self.original.parent.mkdir(parents=True)
        self.original.write_text('def validate_warm_tensors(warm, trainable):\n    return False\n')
        self.other = self.source / 'gpu/material.py'
        self.other.write_text('MATERIAL = "UNCHANGED"\n')
        (self.source / api.OUTER).write_text('OUTER = "UNCHANGED"\n')
        self.replacement = self.root / 'replacement.py'
        self.replacement.write_text('def validate_warm_tensors(warm, trainable):\n    return True\n')
        self.enterContext(patch.object(api, 'SOURCE', self.source))
        self.enterContext(patch.object(api, 'DESTINATION', self.destination))
        self.enterContext(patch.object(api, 'ORIGINAL_SHA', api.pin(self.original)['sha256']))

    def test_overlay_preserves_original_and_resolved_material_path(self):
        original = api.pin(self.original)
        receipt = api.build(self.replacement, 'a' * 40)
        self.assertTrue(Path(receipt['path']).is_file())
        self.assertEqual(api.pin(self.original), original)
        self.assertEqual((self.destination / 'gpu/material.py').resolve(), self.other)
        self.assertFalse((self.destination / api.RELATIVE).is_symlink())
        self.assertFalse((self.destination / api.OUTER).is_symlink())
        self.assertEqual((self.destination / api.OUTER).read_bytes(), (self.source / api.OUTER).read_bytes())
        self.assertEqual((self.destination / api.RELATIVE).read_bytes(), self.replacement.read_bytes())
        with self.assertRaisesRegex(ValueError, 'fresh overlay'):
            api.build(self.replacement, 'a' * 40)

    def test_changed_other_code_refused_before_write(self):
        self.replacement.write_text(self.replacement.read_text() + '\nCHANGED = True\n')
        with self.assertRaisesRegex(ValueError, 'non-validator change'):
            api.build(self.replacement, 'a' * 40)
        self.assertFalse(self.destination.exists())

    def test_original_drift_refused(self):
        self.original.write_text(self.original.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'frozen fit drift'):
            api.build(self.replacement, 'a' * 40)
        self.assertFalse(self.destination.exists())

    def test_full_commit_required(self):
        with self.assertRaisesRegex(ValueError, 'full committed'):
            api.build(self.replacement, 'ab1234')


if __name__ == '__main__':
    unittest.main()
