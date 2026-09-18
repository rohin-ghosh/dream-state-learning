"""The diagnostic never substitutes final admission or another life."""

from pathlib import Path
import sys
import unittest

HOME = Path(__file__).resolve().parent
sys.path.insert(0, str(HOME))
import trace_raw1_preflight as trace


class TraceTests(unittest.TestCase):
    def test_exact_raw1_preflight_only(self):
        script = HOME / 'trace_raw1_preflight.py'
        before = list(trace.EXPECTED)
        self.assertEqual(trace.traced_command(before, script), before[:8] + [str(script), 'scan'])
        self.assertEqual(before, trace.EXPECTED)

    def test_final_guard_scan_and_other_lives_unchanged(self):
        for command in (['sudo', 'guard', 'scan'],
                        [value.replace('lane1/', 'lane0/') for value in trace.EXPECTED],
                        trace.EXPECTED + ['unexpected']):
            self.assertIs(trace.traced_command(command, Path('trace.py')), command)


if __name__ == '__main__':
    unittest.main()
