"""CPU-only one-shot rearm lifecycle regressions; no processes are launched."""

import ast
import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location('node4_rearm_once', Path(__file__).with_name('rearm_once.py'))
rearm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rearm)


class RearmTests(unittest.TestCase):
    def test_clean_expiry_same_owners_and_sources(self):
        self.assertTrue(rearm.clean_rearm_allowed(False, False, True, True, True))

    def test_live_watcher_never_rearmed(self):
        self.assertFalse(rearm.clean_rearm_allowed(False, True, True, True, True))

    def test_consumed_handoff_never_rearmed(self):
        self.assertFalse(rearm.clean_rearm_allowed(True, False, True, True, True))
        self.assertEqual(set(rearm.CONSUMED), {'RETIREMENT_STARTED.json', 'RETIRED.json', 'DISPATCHED.json',
            'LOADED_RECEIPT.json', 'HANDOFF_COMPLETE.json'})

    def test_error_exit_never_automatically_retried(self):
        with self.assertRaisesRegex(ValueError, 'error_or_unexplained'):
            rearm.clean_rearm_allowed(False, False, False, True, True)

    def test_changed_owner_or_source_blocks(self):
        for owners, sources in ((False, True), (True, False), (False, False)):
            with self.subTest(owners=owners, sources=sources), self.assertRaisesRegex(ValueError, 'owner_or_source'):
                rearm.clean_rearm_allowed(False, False, True, owners, sources)

    def test_only_scoped_lanes(self):
        for physical in (0, 1, 3, 4):
            self.assertEqual(rearm.scoped_lane(rearm.BASE / 'orch_r179_node4_fixture' / f'lane{physical}'), physical)
        for physical in (2, 5, 6, 7):
            with self.assertRaises(ValueError):
                rearm.scoped_lane(rearm.BASE / 'orch_r179_node4_fixture' / f'lane{physical}')

    def test_source_has_no_signals_native_launch_or_provider_calls(self):
        source = Path(rearm.__file__).read_text()
        ast.parse(source)
        for forbidden in ('import signal', 'os.kill(', 'killpg(', 'pidfd_send_signal', 'torch', 'requests.'):
            self.assertNotIn(forbidden, source)
        self.assertIn("'handoff'", source)
        self.assertNotIn("'native'", source)


if __name__ == '__main__':
    unittest.main()
