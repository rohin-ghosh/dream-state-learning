import unittest

from gpu.orch_r137_parent_monitor import status_text


class ParentMonitorTests(unittest.TestCase):
    def row(self):
        return dict(branch='BRAIN', parent_alive=True, parent_started_unix=1000,
                    coverage=dict(covered_boundaries=2, closed_boundaries=3, missing_boundaries=1),
                    response_count=8, call_statuses={'PUBLISHED': 4, 'MISSING': 1})

    def test_publications_are_not_exposures(self):
        text = status_text([self.row()], 1060)
        self.assertIn('verified_covered/closed=2/3', text)
        self.assertIn('missing=1', text)
        self.assertIn('"PUBLISHED": 4', text)

    def test_elapsed_hour_is_not_success(self):
        text = status_text([self.row()], 5000)
        self.assertIn('not proof of a sustained successful hour', text)
        self.assertNotIn('hour passed', text)

    def test_error_has_no_coverage_claim(self):
        text = status_text([dict(branch='BRAIN', error='ValueError')], 1060)
        self.assertIn('audit ERROR; no coverage claim', text)
        self.assertNotIn('verified_covered/closed', text)


if __name__ == '__main__':
    unittest.main()
