import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('focus', Path(__file__).with_name('focus.py'))
focus = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(focus)


class FocusTests(unittest.TestCase):
    def bridge(self):
        return dict(pid=focus.BRIDGE_PID, start_ticks=focus.BRIDGE_START, uid=2524,
            cmdline_sha256=focus.BRIDGE_SHA, argv=['/localhome/local-rohing/v2/venv/bin/python', '-B',
            str(focus.BRIDGE_ROOT/'source/gpu/r184_cpu_bridge.py'), '--config', str(focus.BRIDGE_ROOT/'BRIDGE.json')])

    def test_exact_bridge_bound_to_retired_root(self):
        focus.bridge_identity(self.bridge(), {'raw_root': str(focus.TARGETS['math_transfer_c1'][0])})

    def test_pid_reuse_and_command_mismatch_rejected(self):
        for key, value in [('pid', 2561156), ('start_ticks', focus.BRIDGE_START+1), ('uid', 0), ('cmdline_sha256', 'different'), ('argv', ['python', 'other.py'])]:
            with self.subTest(key=key):
                actual = self.bridge()
                actual[key] = value
                with self.assertRaisesRegex(ValueError, 'exact_orphan'):
                    focus.bridge_identity(actual, {'raw_root': str(focus.TARGETS['math_transfer_c1'][0])})

    def test_protected_C0_or_caption_root_never_bridge_target(self):
        for raw in ('/localhome/local-rohing/orch_r216_C0_20260918_attempt2/raw',
                    '/localhome/local-rohing/orch_r229_unparented_caption_20260918/raw'):
            with self.subTest(root=raw), self.assertRaisesRegex(ValueError, 'bridge_only_retired_root'):
                focus.bridge_identity(self.bridge(), {'raw_root': raw})

    def test_unbound_repo_c3_not_silently_aliased(self):
        with self.assertRaisesRegex(ValueError, 'exact_target_only'):
            focus.check_target('repo_c3', focus.TARGETS['repo_c1'][0])
        self.assertIn('GAME_UNPARENTED_N2', focus.KEEP)
        self.assertNotIn('GAME_UNPARENTED_N2', focus.TARGETS)

    def test_target_root_substitution_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact_target_only'):
            focus.check_target('repo_c1', Path('/localhome/local-rohing/orch_r216_C0_20260918_attempt2/raw'))

    def test_missing_or_paused_kept_process_blocks_operator(self):
        with patch.object(focus, 'process', return_value=None), self.assertRaisesRegex(ValueError, 'kept_identity'):
            focus.kept_identities()
        name, (pid, start, argument) = next(iter(focus.KEEP.items()))
        actual = dict(pid=pid, start_ticks=start, state='T', argv=[argument])
        with patch.object(focus, 'process', return_value=actual), self.assertRaisesRegex(ValueError, 'kept_identity'):
            focus.kept_identities()

    def test_hash_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'original').write_bytes(b'public fixture')
            (root/'link').symlink_to(root/'original')
            with self.assertRaisesRegex(ValueError, 'regular_file_only'):
                focus.file_sha(root/'link')

    def test_checked_record_body_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'00000000000000000001.json'
            record = dict(index=1, kind='LOADED', document={'pid': 1})
            record['sha256'] = focus.sha(focus.canonical(record))
            focus.write(path, record)
            self.assertEqual(focus.checked_record(path)['index'], 1)
            altered = copy.deepcopy(record)
            altered['document']['pid'] = 2
            path.write_bytes(focus.canonical(altered))
            with self.assertRaisesRegex(ValueError, 'record_hash'):
                focus.checked_record(path)


if __name__ == '__main__':
    unittest.main()
