import unittest

from gpu import orch_r109_l1_report as report


class ReportTests(unittest.TestCase):
    def test_quality_not_inferred_from_capture_counts(self):
        rows=[dict(finished_unix=100,response=dict(token_ids=[1,2],truncated=False),outcome=dict(correct=True))]
        reduced=report.reduced_calls(rows,101,600)
        self.assertEqual(reduced['raw_captures_per_hour'],6)
        self.assertEqual(reduced['machine_correct_recent'],1)
        self.assertIsNone(reduced['qualified_rows_per_hour'])
        self.assertEqual(reduced['semantic_admissions'],0)

    def test_fixed_hourly_cadence_and_end(self):
        self.assertEqual(report.next_hour(report.START+10),report.START+3600)
        self.assertEqual(report.next_hour(report.START+3601),report.START+7200)
        self.assertEqual(report.next_hour(report.END-1),report.END)

    def test_window_does_not_count_future_or_old_rows(self):
        rows=[dict(finished_unix=50),dict(finished_unix=100),dict(finished_unix=150)]
        reduced=report.reduced_calls(rows,100,10)
        self.assertEqual(reduced['recent_captures'],1)
        self.assertEqual(reduced['completed_captures'],3)


if __name__=='__main__':
    unittest.main()
