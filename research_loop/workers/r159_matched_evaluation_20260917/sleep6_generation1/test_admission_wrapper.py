import json
from pathlib import Path
import sys
import tempfile
import unittest

from admission_wrapper import recording_profile


class CaptureTests(unittest.TestCase):
    def test_unchanged_clear_and_refused_reports(self):
        for clear in (True, False):
            with self.subTest(clear=clear), tempfile.TemporaryDirectory() as directory:
                report = dict(clear=clear, blocking_reasons=[] if clear else ['BUSY'])
                def scan():
                    return report
                path = Path(directory) / 'scan.json'
                sys.setprofile(recording_profile(scan, path))
                try:
                    actual = scan()
                finally:
                    sys.setprofile(None)
                self.assertIs(actual, report)
                self.assertEqual(json.loads(path.read_text())['report'], report)

    def test_collision_fails_closed_preserves_old(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'scan.json'
            path.write_text('original')
            def scan():
                return dict(clear=True)
            sys.setprofile(recording_profile(scan, path))
            try:
                with self.assertRaises(FileExistsError):
                    scan()
            finally:
                sys.setprofile(None)
            self.assertEqual(path.read_text(), 'original')

    def test_unrelated_return_not_captured(self):
        with tempfile.TemporaryDirectory() as directory:
            def scan():
                return dict(clear=True)
            path = Path(directory) / 'scan.json'
            sys.setprofile(recording_profile(scan, path))
            try:
                json.dumps(dict(unrelated=True))
            finally:
                sys.setprofile(None)
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
