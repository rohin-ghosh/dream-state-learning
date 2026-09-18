"""CPU-only exact-publication/render binding fixtures."""

import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location('receipt', Path(__file__).with_name('collect_r175_node4_receipts.py'))
receipt = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(receipt)


class ReceiptTests(unittest.TestCase):
    def test_no_render_inferred_from_publication(self):
        publication = dict(publication=dict(id='fixture', sha256='a'), message_sha256='b')
        self.assertIsNone(receipt.render_binding(publication, dict(delivered={})))

    def test_exact_TRAIN_parent_receipt_required(self):
        publication = dict(publication=dict(id='fixture', sha256='a'), message_sha256='b')
        snapshot = dict(split='TRAIN', journal_id='life', delivered=dict(fixture=dict(speaker='Astra',
            inbox_sha256='a', text_sha256='b', record_index=7, record_sha256='record', sleep_count=4)))
        self.assertEqual(receipt.render_binding(publication, snapshot)['sleep_count'], 4)
        for field in ('speaker', 'inbox_sha256', 'text_sha256'):
            broken = copy.deepcopy(snapshot)
            broken['delivered']['fixture'][field] = 'wrong'
            with self.assertRaisesRegex(ValueError, 'exact_actual_rendered_publication'):
                receipt.render_binding(publication, broken)
        snapshot['split'] = 'FINAL'
        with self.assertRaises(ValueError):
            receipt.render_binding(publication, snapshot)

    def test_incomplete_current_write_not_a_valid_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'POLL_000001.json').write_text('{"complete":true}')
            (root / 'POLL_000002.json').write_text('{')
            path, value = receipt.latest(root, 'POLL_*.json')
            self.assertEqual(path.name, 'POLL_000001.json')
            self.assertEqual(value, {'complete': True})

    def withdrawal_fixture(self):
        control = dict(physical=1, parent_live=False, parent_status='HANDS_OFF_BASELINE_PUBLISHED',
            publication_count=1, publications=[dict(receipt=dict(publication=dict(id='withdrawn', sha256='exact')),
                rendered=None)])
        withdrawal = dict(status='WITHDRAWN_BEFORE_INGESTION', root=receipt.base.ROOTS[1], native_pid=294158,
            native_start_ticks='24386173', native_resumed=True, native_restart=False,
            adapter_optimizer_rng_untouched=True, inbox_id='withdrawn', publication_sha256='exact')
        return [dict(physical=0, parent_live=True, parent_status='RUNNING'), control], withdrawal

    def test_withdrawal_supersedes_pending_not_historical_publication(self):
        rows, withdrawal = self.withdrawal_fixture()
        other = copy.deepcopy(rows[0])
        receipt.apply_control_withdrawal(rows, withdrawal)
        self.assertEqual(rows[0], other)
        self.assertEqual(rows[1]['parent_status'], 'OFF_WITHDRAWN_BEFORE_INGESTION')
        self.assertEqual(rows[1]['current_pending_publications'], 0)
        self.assertEqual(rows[1]['historical_publication_count'], 1)
        self.assertEqual(rows[1]['actual_baseline_exposures'], 0)

    def test_wrong_withdrawal_receipt_never_overrides_a_publication(self):
        for field, value in [('inbox_id', 'other'), ('publication_sha256', 'other'), ('root', receipt.base.ROOTS[0]),
                ('native_start_ticks', 'reused'), ('status', 'PUBLISHED'), ('native_restart', True)]:
            rows, withdrawal = self.withdrawal_fixture()
            withdrawal[field] = value
            with self.assertRaises(ValueError):
                receipt.apply_control_withdrawal(rows, withdrawal)

    def test_live_H_or_observed_render_is_not_silently_overridden(self):
        rows, withdrawal = self.withdrawal_fixture()
        rows[1]['parent_live'] = True
        with self.assertRaisesRegex(ValueError, 'H_operator_must_remain_off'):
            receipt.apply_control_withdrawal(rows, withdrawal)
        rows[1]['parent_live'] = False
        rows[1]['publications'][0]['rendered'] = {'record_index': 99}
        with self.assertRaisesRegex(ValueError, 'withdrawal_exact_publication_not_exposure'):
            receipt.apply_control_withdrawal(rows, withdrawal)


if __name__ == '__main__':
    unittest.main()
