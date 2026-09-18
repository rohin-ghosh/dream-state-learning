import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import preserve_ended as preservation


def record(index, kind, document, previous):
    value = dict(index=index, kind=kind, document=document, previous_sha256=previous)
    return dict(value, sha256=preservation.digest(value))


def boundary():
    checkpoint = dict(optimizer_steps=4, checkpoint_sha256=dict(adapter='a', optimizer='b', rng='b'))
    state = dict(pending=None, rows=['row'], sleep_frontier=1,
                 model_state_sha256=preservation.digest(checkpoint['checkpoint_sha256']))
    completed = record(10, 'SLEEP_COMPLETE', dict(status='COMPLETE', cycle=1,
        resume_state=dict(state=state, sha256=preservation.digest(state)),
        checkpoint=checkpoint, total_optimizer_steps=4), 'before')
    learned = record(11, 'R184_LEARN_COMPLETE', dict(cycle=1, checkpoint=checkpoint,
                     working_state=dict(revision=1, entries=[])), completed['sha256'])
    terminal = record(12, 'TERMINAL', dict(status='R184_SCREEN_STOP', completed_sleeps=1), learned['sha256'])
    return terminal, completed, learned, checkpoint


class PreservationTests(unittest.TestCase):
    def test_private_namespace_projection_does_not_rewrite_source(self):
        class FakeJournal:
            def _inbox_event(self, message, path, source_sha256):
                self.assertion = Path(path).parent == self.inbox
                return self.assertion, message, source_sha256

        projected = preservation.snapshot_journal_type(FakeJournal, '/logical/life')()
        projected.inbox = Path('/physical/copy/stream/inbox')
        message = {'text': 'private'}
        self.assertEqual(projected._inbox_event(message, '/logical/life/stream/inbox/input.json', 'hash'),
                         (True, message, 'hash'))
        self.assertEqual(projected.inbox, Path('/physical/copy/stream/inbox'))
        self.assertFalse(projected._inbox_event(message, '/other/life/stream/inbox/input.json', 'hash')[0])

    def test_authorized_aliases_only(self):
        for name in preservation.ARMS:
            self.assertTrue(preservation.selected_path(preservation.BASE / name, name))
            self.assertTrue(preservation.selected_path(preservation.BASE / (name + '_r213'), name))
            self.assertFalse(preservation.selected_path(preservation.BASE / (name + '_other_child'), name))
            self.assertFalse(preservation.selected_path(Path('/tmp') / name, name))
        self.assertFalse(preservation.selected_path(preservation.BASE / 'r203_repo_evidence_c3',
                                                    'r203_repo_evidence_c3'))

    def test_complete_bound_state(self):
        result = preservation.validate_boundary(*boundary())
        self.assertEqual(result['cycle'], 1)
        self.assertEqual(result['optimizer_steps'], 4)

    def test_unhashed_changes_rejected(self):
        values = boundary()
        values[0]['document']['completed_sleeps'] = 2
        with self.assertRaisesRegex(ValueError, 'record_hash'):
            preservation.validate_boundary(*values)

    def test_wrong_checkpoint_rejected(self):
        terminal, completed, learned, checkpoint = boundary()
        foreign = copy.deepcopy(checkpoint)
        foreign['optimizer_steps'] = 999
        with self.assertRaisesRegex(ValueError, 'checkpoint_exactly_bound'):
            preservation.validate_boundary(terminal, completed, learned, foreign)

    def test_pending_work_rejected(self):
        terminal, completed, learned, checkpoint = boundary()
        document = copy.deepcopy(completed['document'])
        document['resume_state']['state']['pending'] = 'not_completed'
        document['resume_state']['sha256'] = preservation.digest(document['resume_state']['state'])
        completed = record(10, 'SLEEP_COMPLETE', document, 'before')
        learned = record(11, learned['kind'], learned['document'], completed['sha256'])
        terminal = record(12, terminal['kind'], terminal['document'], learned['sha256'])
        with self.assertRaisesRegex(ValueError, 'no_pending'):
            preservation.validate_boundary(terminal, completed, learned, checkpoint)

    def test_old_retirement_marker_is_not_native_exit(self):
        terminal, completed, learned, checkpoint = boundary()
        terminal = record(12, 'TERMINAL', dict(status='interrupted', completed_sleeps=1), learned['sha256'])
        with self.assertRaisesRegex(ValueError, 'normal_screen_end'):
            preservation.validate_boundary(terminal, completed, learned, checkpoint)

    def test_manifest_tracks_bytes_and_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'state').write_bytes(b'saved')
            files = preservation.inventory(root)
            self.assertEqual(files[0]['bytes'], 5)
            (root / 'link').symlink_to(root / 'state')
            with self.assertRaisesRegex(ValueError, 'snapshot_symlink'):
                preservation.inventory(root)

    def test_foreign_name_fails_before_any_write(self):
        with patch.object(Path, 'mkdir') as mkdir:
            with self.assertRaisesRegex(ValueError, 'exact_authorized_name'):
                preservation.preserve('C2')
            mkdir.assert_not_called()


if __name__ == '__main__':
    unittest.main()
