import copy
import fcntl
import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import collector
import epochs
import receipt


def binding():
    return dict(until_unix=9999999999, owner_receipt_sha256='owner', journal_id='life', pid=9,
        start_ticks='10', source='/synthetic/source', root='/synthetic/life', guard_sha256='guard',
        loaded_index=1, loaded_sha256='loaded', boot_id='boot', source_manifest_sha256='manifest')


def fixture():
    with patch.dict(sys.modules, {'audit': collector.audit}):
        module = collector.load('isolated_recovery_fixture', collector.CONTRACT / 'test_audit.py')
    evidence, unused = module.fixture()
    evidence.update(head=dict(index=40), bytes_read=10)
    return dict(evidence=evidence, identity=dict(pid=9, start_ticks='10', boot_id='boot'))


class RecoveryTests(unittest.TestCase):
    def test_local_pid_reuse_across_boots_is_not_same_owner(self):
        old = dict(pid=9, start_ticks='10', boot_id='old', state='S')
        new = dict(old, boot_id='new')
        self.assertFalse(collector.same_process(new, old))
        self.assertFalse(collector.same_process(None, old))
        self.assertFalse(collector.same_process(dict(old, state='Z'), old))
        self.assertTrue(collector.same_process(old, old))

    def test_process_receipt_carries_actual_host_boot(self):
        self.assertEqual(collector.process(os.getpid())['boot_id'], Path('/proc/sys/kernel/random/boot_id').read_text().strip())

    def test_epoch_changes_with_each_source_boundary_not_horizon(self):
        target = binding()
        original = epochs.source_epoch('life', target)
        for key in target:
            changed = dict(target, **{key: 'different'})
            if key == 'until_unix':
                self.assertEqual(original, epochs.source_epoch('life', changed))
            else:
                self.assertNotEqual(original, epochs.source_epoch('life', changed), key)
        self.assertNotEqual(original, epochs.source_epoch('other_life', target))

    def test_same_journal_wrong_epoch_cursor_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source_epoch_mismatch'):
            epochs.validate_cursor(dict(journal_id='same', source_epoch_id='old'), 'new')

    def test_unversioned_cursor_not_silently_imported(self):
        with self.assertRaisesRegex(ValueError, 'source_epoch_mismatch'):
            epochs.validate_cursor(dict(journal_id='same'), 'new')

    def test_only_actual_ACT_exposure_and_no_semantic_promotion(self):
        result = epochs.act_exposure(fixture()['evidence'], collector.audit, collector.queue, 'epoch')
        self.assertEqual(result['actual_ACTs'], 2)
        self.assertEqual(result['ACTs_with_exact_parent_text'], 2)
        for row in result['acts']:
            self.assertEqual(row['output']['stage'], 'ACT')
            self.assertTrue(row['parents'][0]['exact_parent_text_in_ACT'])
            self.assertNotIn('text', row['parents'][0])
            self.assertIsNone(row['semantic_uptake'])
            self.assertIsNone(row['retention_effect'])

    def test_exposure_does_not_infer_absent_parent_or_uncommitted_act(self):
        evidence = fixture()['evidence']
        for row in evidence['records']:
            if row['kind'] == 'REQUEST':
                row['external'] = []
        evidence['records'] = [row for row in evidence['records'] if row['index'] != 33]
        result = epochs.act_exposure(evidence, collector.audit, collector.queue, 'epoch')
        self.assertEqual(result['actual_ACTs'], 1)
        self.assertEqual(result['ACTs_with_exact_parent_text'], 0)

    def test_literal_render_excludes_substrings_and_assistant_quotes(self):
        reader = collector.load('recovery_reader_test', collector.CONTRACT / 'reader.py')
        event = dict(actor='parent', event_id='parent:1', text='Exact correction.', source_id='source', source_sha256='sha', split='TRAIN')
        self.assertTrue(reader.rendered(event, [dict(role='user', content=event['text'])]))
        self.assertFalse(reader.rendered(event, [dict(role='user', content='summary ' + event['text'])]))
        self.assertFalse(reader.rendered(event, [dict(role='assistant', content=event['text'])]))

    def test_preserved_snapshots_and_epoch_queue_no_repeat_ACTs(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(collector, 'HERE', Path(directory)), patch.object(collector, 'remote', side_effect=lambda *args: copy.deepcopy(fixture())):
            first = collector.one(dict(label='test', binding=binding()))
            second = collector.one(dict(label='test', binding=binding()))
            self.assertEqual(first['status'], 'ACTUAL_BOUNDED_COLLECTION_COMPLETE')
            self.assertEqual(second['status'], 'ACTUAL_BOUNDED_COLLECTION_COMPLETE')
            self.assertEqual(first['review_queue']['new_ACT_count'], 2)
            self.assertEqual(second['review_queue']['new_ACT_count'], 0)
            self.assertNotEqual(first['current_window']['snapshot_relative'], second['current_window']['snapshot_relative'])
            self.assertEqual(len(list(Path(directory).glob('private/epochs/test/*/cuts/*/EVIDENCE.json'))), 2)
            self.assertIsNone(second['current_window_semantic_level'])

    def test_source_epoch_fail_closed_no_current_claim(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(collector, 'HERE', Path(directory)), patch.object(collector, 'remote', side_effect=ValueError('source_epoch_changed')):
            row = collector.one(dict(label='test', binding=binding()))
        self.assertEqual(row['status'], 'COLLECTION_ERROR_NO_CURRENT_PROOF')
        self.assertFalse(row['native_identity_verified'])
        self.assertNotIn('current_window', row)

    def test_double_lock_excludes_restart_and_keeps_original_inode(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(collector, 'HERE', Path(directory) / 'new'), patch.object(collector, 'ORIGINAL', Path(directory) / 'old'):
            for folder in (collector.HERE, collector.ORIGINAL):
                (folder / 'operator').mkdir(parents=True)
                (folder / 'operator/SINGLE_READER.lock').touch()
            original = (collector.ORIGINAL / 'operator/SINGLE_READER.lock').stat()
            config = dict(old_lock_identity=[original.st_dev, original.st_ino])
            descriptors = collector.acquire_locks(config)
            try:
                with self.assertRaises(BlockingIOError):
                    collector.acquire_locks(config)
                self.assertEqual((collector.ORIGINAL / 'operator/SINGLE_READER.lock').stat().st_ino, original.st_ino)
            finally:
                for descriptor in descriptors:
                    os.close(descriptor)

    def test_remote_source_manifest_changes_on_disk_edit(self):
        namespace = {}
        exec((collector.CONTRACT / 'reader.py').read_text() + '\n' + (collector.HERE / 'remote.py').read_text(), namespace)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'gpu'
            folder.mkdir()
            source = folder / 'native.py'
            source.write_text('before')
            before = namespace['source_manifest'](directory)
            source.write_text('after')
            self.assertNotEqual(before, namespace['source_manifest'](directory))

    def test_retention_authorization_not_automatically_after_window(self):
        result = epochs.publish_rows([dict(label='life', status='ACTUAL_BOUNDED_COLLECTION_COMPLETE', source_epoch_id='epoch')])[0]
        self.assertIsNone(result['retention_deployed'])
        self.assertEqual(result['retention_comparison'], 'NOT_AVAILABLE_NO_DEPLOYED_AFTER_WINDOW')

    def test_receipt_rejects_old_boot_even_when_pid_matches(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(receipt, 'HERE', Path(directory)):
            Path(directory, 'operator').mkdir()
            state = dict(pid=os.getpid(), start_ticks=collector.process(os.getpid())['start_ticks'], boot_id='previous_boot')
            Path(directory, 'operator/PROCESS.json').write_text(json.dumps(state))
            with self.assertRaisesRegex(ValueError, 'observer_identity_not_alive'):
                receipt.finish()

    def test_receipt_rejects_stale_future_schedule(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(receipt, 'HERE', Path(directory)):
            Path(directory, 'operator').mkdir()
            state = dict(collector.process(os.getpid()), completed_collections=1, phase='SCHEDULED', next_cut_utc='2026-09-18T23:00:00+00:00')
            Path(directory, 'operator/PROCESS.json').write_text(json.dumps(state))
            with self.assertRaisesRegex(ValueError, 'future_schedule_required'):
                receipt.finish()


if __name__ == '__main__':
    unittest.main()
