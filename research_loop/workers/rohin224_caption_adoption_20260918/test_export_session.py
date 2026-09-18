import json
from pathlib import Path
import tempfile
import unittest

from export_session import export_session


class LegacyExportTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.write(self.root / 'LOADED.json', dict(life_root=str(self.root / 'life'), top_k=50, tau=None))
        self.initial = dict(game={'pixels': []}, policy={'count': 0})
        self.final = dict(game={'pixels': ['one']}, policy={'count': 1})
        self.attempt('a' * 64, self.initial, self.final, 1)
        self.attempt('b' * 64, self.final, self.final, 3)

    def write(self, path, document):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document))

    def attempt(self, identifier, before, after, started):
        root = self.root / 'attempts' / identifier
        origin = dict(record_sha256=identifier)
        self.write(root / 'REQUEST.json', dict(request=dict(origin=origin), raw_act='Actual caption.', unix=started))
        self.write(root / 'RESULT.json', dict(origin=origin, raw_act='Actual caption.', unix=started + 1))
        self.write(root / 'BEFORE.json', before)
        self.write(root / 'AFTER.json', after)

    def export(self, raw='Actual caption.'):
        return export_session(self.root, [{'contest_id': 'scene'}],
                              verify_origin=lambda root, origin: raw)

    def test_preserves_all_seen_hashes_and_final_novelty(self):
        state, receipt = self.export()
        self.assertEqual(state['seen'], ['a' * 64, 'b' * 64])
        self.assertEqual(state['game'], self.final['game'])
        self.assertEqual(state['policy'], self.final['policy'])
        self.assertEqual(receipt['complete_attempts'], 2)
        self.assertFalse(receipt['historical_rescoring'])

    def test_incomplete_dispatch_cannot_be_exported(self):
        (self.root / 'attempts' / ('b' * 64) / 'AFTER.json').unlink()
        with self.assertRaisesRegex(ValueError, 'incomplete_attempt'):
            self.export()

    def test_broken_snapshot_chain_cannot_be_exported(self):
        self.write(self.root / 'attempts' / ('b' * 64) / 'BEFORE.json', self.initial)
        with self.assertRaisesRegex(ValueError, 'unbroken_snapshot_chain'):
            self.export()

    def test_modified_child_text_cannot_be_exported(self):
        with self.assertRaisesRegex(ValueError, 'same_actual_child_text'):
            self.export('Different text.')

    def test_changed_rank_rule_cannot_be_exported(self):
        self.write(self.root / 'LOADED.json', dict(life_root=str(self.root / 'life'), top_k=8, tau=None))
        with self.assertRaisesRegex(ValueError, 'same_relative_rank_rule'):
            self.export()


if __name__ == '__main__':
    unittest.main()
