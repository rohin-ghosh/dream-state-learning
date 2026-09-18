import errno
from pathlib import Path
import tempfile
import unittest

try:
    import rehome_receive as receiving
except ModuleNotFoundError:
    from research_loop.workers.rohin183_repo_learning_20260917 import rehome_receive as receiving


class ReceivingTests(unittest.TestCase):
    def test_assignments(self):
        for original, physical in ((1, 0), (4, 7), (7, 5), (7, 6)):
            receiving.assigned(original, physical)

    def test_wrong_assignment_rejected(self):
        for original, physical in ((0, 0), (4, 4), (1, 7), (True, 0)):
            with self.subTest(original=original, physical=physical), self.assertRaises(ValueError):
                receiving.assigned(original, physical)

    def test_plan_preserves_learning_and_logical_root(self):
        old = dict(root='/original/run1', source_root='/old/source', physical=4, gpu_uuid='old',
            hard_end_unix=1789689000, lease_end_unix=1789689600, new_presentations=16,
            rehearsal_presentations=0, anchors='/anchors', opaque={'keep': 'exact'},
            startup_context={'path': '/old/source/STARTUP.md', 'sha256': 'a' * 64})
        state = dict(state={'deadline_unix': old['hard_end_unix']})
        state['sha256'] = receiving.digest(state['state'])
        plan = receiving.make_plan(old, Path('/receiving/source'), state, 7)
        for key in ('root', 'new_presentations', 'rehearsal_presentations', 'anchors', 'opaque'):
            self.assertEqual(plan[key], old[key])
        self.assertEqual(plan['authorized_wall_extension']['previous_stream_sha256'], state['sha256'])
        self.assertEqual(plan['hard_end_unix'], receiving.HARD)
        self.assertEqual(plan['lease_end_unix'], receiving.CEILING)
        self.assertNotIn('think_act_learn', plan)

    def test_changed_saved_state_rejected(self):
        with self.assertRaisesRegex(ValueError, 'saved_state_digest'):
            receiving.make_plan({'hard_end_unix': 1}, Path('/new'),
                {'state': {'deadline_unix': 1}, 'sha256': 'wrong'}, 7)

    def test_archive_paths(self):
        receiving.member_path('physical4/root/stream/JOURNAL.json', 'physical4')
        for name in ('/physical4/root', 'physical4/../../other', 'physical1/root'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                receiving.member_path(name, 'physical4')

    def test_final_inbox_adds_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            prior, final = Path(directory) / 'prior', Path(directory) / 'final'
            prior.mkdir(); final.mkdir()
            (prior / 'same.json').write_bytes(b'unchanged')
            (final / 'same.json').write_bytes(b'unchanged')
            (final / 'new.json').write_bytes(b'new input')
            result = receiving.reconcile_inbox(prior, final)
            self.assertEqual(result['added'], 1)
            self.assertEqual((prior / 'same.json').read_bytes(), b'unchanged')

    def test_inbox_conflict_or_missing_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            prior, final = Path(directory) / 'prior', Path(directory) / 'final'
            prior.mkdir(); final.mkdir()
            (prior / 'same.json').write_bytes(b'old')
            with self.assertRaises(ValueError):
                receiving.reconcile_inbox(prior, final)
            (final / 'same.json').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                receiving.reconcile_inbox(prior, final)

    def test_device_only_target_seven_foreign_denied(self):
        def opener(path, flags):
            if path in ('/dev/nvidia7', '/dev/nvidiactl', '/dev/nvidia-uvm'):
                return 42
            raise PermissionError(errno.EPERM, 'denied')
        result = receiving.device_checks(7, opener, lambda descriptor: None)
        self.assertTrue(result['target_open_close'])
        self.assertEqual(result['denied_foreign_minors'], list(range(7)))

    def test_foreign_device_open_rejected(self):
        with self.assertRaisesRegex(ValueError, 'foreign_device_open'):
            receiving.device_checks(7, lambda path, flags: 42, lambda descriptor: None)


if __name__ == '__main__':
    unittest.main(verbosity=2)
