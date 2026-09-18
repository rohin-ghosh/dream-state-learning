"""No live boundary watcher, signals or operator holds after R212."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import r209_filter_resume as repair


class NoPauseTests(unittest.TestCase):
    def test_live_head_refused_before_staging_reads_or_lock_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = root / 'conversational/raw/stream/records'
            records.mkdir(parents=True)
            (records / '00000000000000000000.json').touch()
            with patch.object(repair, 'ROOT', root), patch.object(repair, 'metadata', return_value='SLEEP_COMPLETE'), \
                    patch.object(repair, 'read') as read, patch.object(repair.os, 'open') as opened:
                with self.assertRaisesRegex(ValueError, 'R212_NO_PAUSE'):
                    repair.apply('conversational')
                read.assert_not_called()
                opened.assert_not_called()

    def test_operator_helper_contains_no_process_signaling(self):
        source = Path(repair.__file__).read_text()
        for forbidden in ('SIGSTOP', 'SIGCONT', 'SIGTERM', 'pidfd_send_signal', 'PAUSED.json'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
