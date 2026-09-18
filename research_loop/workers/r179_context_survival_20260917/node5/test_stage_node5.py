import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location('node5_stage', Path(__file__).with_name('stage_node5.py'))
stage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage)


class ReadonlyPreparationTests(unittest.TestCase):
    def test_same_identity_binds_pid_start_uid_argv_and_cwd(self):
        original = dict(pid=12, start_ticks='99', uid=2524, argv_sha256='abc', cwd='/source', state='S')
        self.assertTrue(stage.same_identity(original, dict(original, state='R')))
        for field, replacement in dict(pid=13, start_ticks='100', uid=0, argv_sha256='def', cwd='/else').items():
            self.assertFalse(stage.same_identity(original, dict(original, **{field: replacement})))
        self.assertFalse(stage.same_identity(original, dict(original, state='Z')))

    def test_canonical_record_tail_returns_only_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '00000000000000000004.json'
            record = dict(index=4, journal_id='fixture', kind='SLEEP_COMPLETE', previous_sha256='a' * 64,
                          schema='test', sha256='b' * 64,
                          document=dict(text='private text ' * 5000, kind='REQUEST', index=99))
            path.write_text(json.dumps(record, sort_keys=True, separators=(',', ':')))
            result = stage.tail_metadata(path)
            self.assertEqual(result['kind'], 'SLEEP_COMPLETE')
            self.assertEqual(result['index'], 4)
            self.assertNotIn('document', result)
            self.assertNotIn('private text', json.dumps(result))

    def test_record_tail_refuses_filename_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '00000000000000000005.json'
            record = dict(document={}, index=4, journal_id='fixture', kind='SLEEP_COMPLETE',
                          previous_sha256='a' * 64, schema='test', sha256='b' * 64)
            path.write_text(json.dumps(record, sort_keys=True, separators=(',', ':')))
            with self.assertRaisesRegex(ValueError, 'record_filename_binding'):
                stage.tail_metadata(path)

    def test_document_size_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'large.json'
            path.write_text(' ' * 100)
            with self.assertRaisesRegex(ValueError, 'bounded_document'):
                stage.read_document(path, 10)

    def test_history_hashes_preserve_all_events_without_exporting_text(self):
        history = dict(events=[{'text': 'private child text'}, {'text': 'private parent text'}],
                       operations=[{'kind': 'compact'}], frontier={'end': 2},
                       system_prompt='private system', birth_prompt='private birth')
        history['state_sha256'] = stage.digest(history)
        result = stage.history_metadata(history)
        self.assertEqual(result['events'], 2)
        self.assertEqual(result['operations'], 1)
        self.assertFalse(result['content_exported'])
        self.assertNotIn('private', json.dumps(result))
        history['events'].pop()
        with self.assertRaisesRegex(ValueError, 'full_history_integrity'):
            stage.history_metadata(history)

    def test_checkpoint_hash_is_measured_and_budgeted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.pt'
            path.write_bytes(b'not a real optimizer; hash-only fixture')
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            budget = [100]
            result = stage.hash_file(path, expected, budget)
            self.assertTrue(result['verified'])
            self.assertEqual(budget[0], 100 - path.stat().st_size)
            with self.assertRaisesRegex(ValueError, 'checkpoint_exact_file_hash'):
                stage.hash_file(path, 'a' * 64, [100])
            with self.assertRaisesRegex(ValueError, 'bounded_checkpoint_hash_budget'):
                stage.hash_file(path, expected, [1])

    def test_checkpoint_symlink_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'real'
            path.write_bytes(b'fixture')
            link = Path(directory) / 'link'
            link.symlink_to(path)
            with self.assertRaisesRegex(ValueError, 'checkpoint_no_symlink'):
                stage.hash_file(link, hashlib.sha256(b'fixture').hexdigest(), [100])

    def test_paths_cannot_escape_checkpoint(self):
        root = Path('/life/checkpoints/sleep_000001')
        self.assertEqual(stage.safe_child(root, root / 'optimizer_rng.pt'), root / 'optimizer_rng.pt')
        for value in ['/else/optimizer.pt', '/life/checkpoints/sleep_000001/../else', 'relative.pt']:
            with self.assertRaises(ValueError):
                stage.safe_child(root, value)

    def test_source_ast_receipt_preserves_invitation_without_printing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'gpu/orch_r166_corrected_retelling.py'
            path.parent.mkdir()
            path.write_text('INVITATION = "fixed invitation"\ndef prepare_sleep():\n    pass\n')
            source = stage.source_metadata(root)
            receipt = source['gpu/orch_r166_corrected_retelling.py']
            self.assertEqual(receipt['invitation_sha256'], hashlib.sha256(b'fixed invitation').hexdigest())
            self.assertNotIn('fixed invitation', json.dumps(receipt))


if __name__ == '__main__':
    unittest.main()
