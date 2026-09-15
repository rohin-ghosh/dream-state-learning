import unittest

from organism_v6 import orch_route_parent_campaign_analysis as analysis


class RouteParentAnalysisTests(unittest.TestCase):
    def record(self, correct, response, error=None):
        return dict(correct=correct, captures=[dict(response=response, error=error, command='READ EVENT sample')],
                    reads=['sample'], messages=[dict(role='user', content=analysis.policy.rich.readout.UNAVAILABLE)],
                    routes=[], terminal_reason='dead_end')

    def test_zero_denominators_not_imputed(self):
        result = analysis.episode_metrics([])
        self.assertEqual(result['outcomes'], dict(numerator=0, denominator=0, unit='episodes'))
        self.assertEqual(result['truncated_responses']['denominator'], 0)

    def test_response_read_and_world_denominators(self):
        rows = [self.record(True, dict(terminal=False, truncated=True)), self.record(False, None, {'type': 'failure'})]
        result = analysis.episode_metrics(rows)
        self.assertEqual(result['outcomes']['numerator'], 1)
        self.assertEqual(result['paired_both_correct']['denominator'], 1)
        self.assertEqual(result['missing_responses']['denominator'], 2)
        self.assertEqual(result['truncated_responses']['denominator'], 1)
        self.assertEqual(result['unavailable_event_reads']['denominator'], 2)
        self.assertEqual(result['unavailable_event_reads']['numerator'], 2)


if __name__ == '__main__':
    unittest.main()
