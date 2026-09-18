import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import astra_semantic_rescore as rescore


class RescoreTests(unittest.TestCase):
    def test_rejects_wrong_original_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'manifest.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'fixed original'):
                rescore.verify_original(root)

    def test_merge_requires_all_states(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(FileNotFoundError):
                rescore.merge_records(root, root, [])

    def test_changed_supplement_source_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'supplement.json').write_text(json.dumps({'sources': {}}))
            with patch.object(rescore, 'source_pins', return_value={'test': 'hash'}):
                with self.assertRaisesRegex(ValueError, 'supplement source'):
                    rescore.verify_supplement(root)

    def test_fixed_states_are_original_four_adapters_and_off(self):
        self.assertEqual(rescore.STATES, ['OFF', 'r0_plus', 'r0_minus', 'r1_plus', 'r1_minus'])


if __name__ == '__main__':
    unittest.main()
