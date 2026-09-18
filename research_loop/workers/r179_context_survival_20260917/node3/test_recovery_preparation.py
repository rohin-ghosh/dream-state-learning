from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


spec = spec_from_file_location('node3_suffix_preparation', Path(__file__).with_name('recovery_preparation.py'))
module = module_from_spec(spec)
spec.loader.exec_module(module)


class PreparationTests(unittest.TestCase):
    def test_unsaved_updates_are_not_exact_state(self):
        records = [dict(index=2, kind='UPDATE', document=dict(optimizer_step=11)),
                   dict(index=3, kind='UPDATE', document=dict(optimizer_step=12))]
        result = module.suffix_summary(records, 1, 10)
        self.assertEqual(result['unsaved_updates'], 2)
        self.assertFalse(result['exact_interrupted_state_recoverable_from_UPDATE_records'])
        self.assertFalse(result['suffix_replayed'])
        self.assertFalse(result['original_suffix_removed'])

    def test_step_gap_is_not_invented_as_continuity(self):
        with self.assertRaisesRegex(ValueError, 'consecutive'):
            module.suffix_summary([dict(index=2, kind='UPDATE', document=dict(optimizer_step=12))], 1, 10)

    def test_post_saved_inbox_is_accounted_not_republished(self):
        record = dict(index=3, kind='INBOX', sha256='a'*64, document=dict(source_id='/original/inbox/1.json', source_sha256='b'*64))
        result = module.suffix_summary([record], 2, 10)
        self.assertEqual(result['post_saved_inbox_receipts'][0]['source_id'], '/original/inbox/1.json')
        self.assertFalse(result['suffix_replayed'])
