"""Read-only receipt observer scope and expired-waiter regressions."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('node4_observer', Path(__file__).with_name('observe_handoffs.py'))
observer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observer)


class ObserverTests(unittest.TestCase):
    def test_exact_mixed_preparations(self):
        base = Path('/localhome/local-rohing')
        lanes = [base / 'orch_r179_node4_first' / 'lane1', base / 'orch_r179_node4_next' / 'lane0']
        self.assertEqual(observer.selected_lanes(lanes=lanes), lanes)

    def test_wrong_scope_duplicate_or_ambiguous_selection(self):
        lane = Path('/localhome/local-rohing/orch_r179_node4_first/lane1')
        for lanes in ([], [lane, lane], [lane.with_name('lane2')], [Path('/tmp/other/lane1')]):
            with self.subTest(lanes=lanes), self.assertRaises(ValueError):
                observer.selected_lanes(lanes=lanes)
        with self.assertRaises(ValueError):
            observer.selected_lanes(bundle=lane.parent, lanes=[lane])

    def test_expired_operator_is_not_reported_as_live_waiter(self):
        with tempfile.TemporaryDirectory() as directory:
            lane = Path(directory) / 'lane3'
            lane.mkdir()
            (lane / 'STAGED.json').write_text(json.dumps(dict(processes=dict(actor=dict(
                pid=999999999, start_ticks='0', uid=2524)))))
            (lane / 'PREFLIGHT_ACCEPTED_1.json').write_text('{}')
            with patch.object(observer, 'selected_lanes', return_value=[lane]):
                self.assertEqual(observer.summary(lanes=[lane])[0]['status'], 'PREFLIGHT_PASSED_OPERATOR_NOT_LIVE')
                (lane / 'WAIT_EXPIRED_2.json').write_text('{}')
                row = observer.summary(lanes=[lane])[0]
                self.assertEqual(row['status'], 'WAIT_EXPIRED_NO_RETIREMENT')
                self.assertEqual(row['live_operator_identities'], [])


if __name__ == '__main__':
    unittest.main()
