import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_route_parent_campaign_monitor as monitor


class RouteParentMonitorTests(unittest.TestCase):
    def test_absent_and_incomplete_phases_not_claimed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(monitor.snapshot(root), [])
            self.assertEqual(monitor.snapshot(root / 'missing'), [])

    def test_reports_observed_sleep_without_claiming_test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'GUIDED/cycle1/sleep'
            folder.mkdir(parents=True)
            (folder / 'COMPLETE.json').write_text(json.dumps(dict(finished_unix=1, updates=40,
                input_adapter=dict(state_sha256='old'), output_adapter=dict(state_sha256='new'),
                process=['boot', 1, 1])))
            event = monitor.snapshot(root)[0]
            self.assertEqual(event['updates'], 40)
            self.assertIsNone(event['parent_free'])
            self.assertNotIn('taught_to_parent_free_next_episodes', event)


if __name__ == '__main__':
    unittest.main()
