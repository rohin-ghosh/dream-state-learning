import importlib.util
from pathlib import Path
import sys
import unittest


SOURCE = Path(__file__).with_name('hourly_parent_report.py')
sys.path.insert(0, str(SOURCE.parent))
SPEC = importlib.util.spec_from_file_location('hourly_parent_report', SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HourlyParentReportTests(unittest.TestCase):
    def sample(self, count):
        return dict(observed_unix=1789670490, rows=[dict(physical=0, alive=True,
            statuses={'PUBLISHED': 4, 'MISSING': 1}, registered_deliveries=count,
            calls=[dict(response='UNEXPORTED_PROVIDER_TEXT')])])

    def test_counts_are_segment_only_and_report_deltas(self):
        text = MODULE.render(self.sample(3), self.sample(1))
        self.assertIn('| 0 | True | 4 | 3 | 2 | 1 |', text)
        self.assertIn('not lifetime totals', text)
        self.assertIn('PDT', text)
        self.assertNotIn('UNEXPORTED_PROVIDER_TEXT', text)

    def test_no_refund_for_regressed_receipts(self):
        with self.assertRaisesRegex(ValueError, 'regressed'):
            MODULE.render(self.sample(1), self.sample(3))


if __name__ == '__main__':
    unittest.main()
