import ctypes
import os
from pathlib import Path
import select
import struct
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r133_node3_release as release


class ReleaseTests(unittest.TestCase):
    def test_missing_finish_time_remains_unknown(self):
        report = dict(clear=True, blocking_reasons=[], created_utc='2026-09-16T11:53:11Z')
        actual = release.scanner_summary_compatible(report)
        self.assertIsNone(actual['finished_unix'])
        self.assertNotIn('finished_unix', report)

    def test_existing_timestamp_and_blockers_unchanged(self):
        report = dict(clear=False, blocking_reasons=['open_device_pid:1'], finished_unix=123)
        self.assertEqual(release.scanner_summary_compatible(report), report)

    def test_protected_slot_rejected_before_verification(self):
        with patch.object(release.original, 'read', return_value=dict(request=dict(node='ovx2', physical=1))):
            with self.assertRaisesRegex(ValueError, 'owned_remaining_node3_only'):
                release.verify('/localhome/local-rohing/orch_r133_retirement_20260916/physical1_test')

    def test_grid_adds_create_without_removing_existing_events(self):
        source = release.grid_listener_source()
        self.assertEqual(source.count('0x8 | 0x80 | 0x100'), 2)
        self.assertIn('frontier_unchanged_after_snapshot', source)
        self.assertIn('next_boundary_not_historical_checkpoint', source)
        compile(source, 'test_grid_listener', 'exec')

    def test_grid_listener_never_targets_other_lanes(self):
        for physical in (0, 1, 2, 3, 4, 5, 6, True):
            with self.subTest(physical=physical), self.assertRaisesRegex(ValueError, 'only_owned_grid7'):
                release.retire_grid(dict(node='ovx2', physical=physical))

    def test_atomic_hardlink_publication_requires_create_event(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            library = ctypes.CDLL(None, use_errno=True)
            descriptor = library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
            self.assertGreaterEqual(descriptor, 0)
            try:
                self.assertGreaterEqual(library.inotify_add_watch(
                    descriptor, os.fsencode(directory), 0x8 | 0x80 | 0x100), 0)
                staged = directory / 'C0065_CONTINUED.json.tmp'
                staged.write_text('{}\n')
                os.link(staged, directory / 'C0065_CONTINUED.json')
                staged.unlink()
                self.assertTrue(select.select([descriptor], [], [], 1)[0])
                events = os.read(descriptor, 65536)
                cursor, matching = 0, []
                while cursor + 16 <= len(events):
                    _, mask, _, length = struct.unpack_from('iIII', events, cursor)
                    name = events[cursor + 16:cursor + 16 + length].rstrip(b'\0')
                    if name == b'C0065_CONTINUED.json':
                        matching.append(mask)
                    cursor += 16 + length
                self.assertTrue(any(mask & 0x100 for mask in matching))
                self.assertFalse(any(mask & (0x8 | 0x80) for mask in matching))
            finally:
                os.close(descriptor)
