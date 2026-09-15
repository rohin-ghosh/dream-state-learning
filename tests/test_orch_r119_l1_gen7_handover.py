import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r119_l1_gen7_handover as handover


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.progress = dict(calls=102, inherited_calls=100, new_segment_calls=2,
                             batch=286, position=21)
        (self.root / 'PROGRESS.json').write_text(json.dumps(self.progress))
        for count in (101, 102):
            for label in ('CALL', 'INTENT'):
                (self.root / f'{label}_{count:06d}.json').write_text(
                    json.dumps(dict(cumulative_call=count, family='math')))

    def test_inherited_calls_not_counted_as_new_or_required_as_files(self):
        result = handover.boundary_status(self.root)
        self.assertTrue(result['candidate'])
        self.assertFalse(result['release_authorized'])
        self.assertEqual(result['new_response_count'], 2)
        self.assertEqual(result['next_call'], 103)
        self.assertEqual(result['next_cursor'], dict(batch=286, position=23))

    def test_inflight_revision_rejected(self):
        (self.root / 'INTENT_000103.json').write_text('{}')
        self.assertFalse(handover.boundary_status(self.root)['candidate'])

    def test_failed_or_missing_capture_rejected(self):
        (self.root / 'CALL_000101.json').unlink()
        self.assertFalse(handover.boundary_status(self.root)['candidate'])
        (self.root / 'FAILED_000103.json').write_text('{}')
        self.assertFalse(handover.boundary_status(self.root)['candidate'])

    def test_route_requires_actual_four_digit_episode_filename(self):
        (self.root / 'CALL_000102.json').write_text(json.dumps(dict(cumulative_call=102, family='route')))
        self.assertFalse(handover.boundary_status(self.root)['candidate'])
        (self.root / 'EPISODE_0286_21.json').write_text('{}')
        self.assertTrue(handover.boundary_status(self.root)['candidate'])

    def test_wrong_inherited_counter_rejected(self):
        self.progress['inherited_calls'] = 99
        (self.root / 'PROGRESS.json').write_text(json.dumps(self.progress))
        self.assertFalse(handover.boundary_status(self.root)['candidate'])

    def test_admission_pins_only_physical7_and_returns_busy_without_signals(self):
        report = dict(clear=False, blocking_reasons=['owned_generator_resident'],
                      scanner_euid=0, gpu=dict(uuid=handover.UUID))
        with patch('gpu.orch_rich_hot_node2_scan.scan', return_value=report) as scanner:
            result = handover.admission_status(Path('/native/service.json'))
        scanner.assert_called_once_with(7, Path('/native/service.json'))
        self.assertFalse(result['clear'])
        self.assertFalse(result['release_authorized'])

    def test_wrong_uuid_or_unprivileged_scan_rejected(self):
        for uid, uuid in ((1, handover.UUID), (0, 'other_gpu')):
            with patch('gpu.orch_rich_hot_node2_scan.scan', return_value=dict(
                    clear=True, blocking_reasons=[], scanner_euid=uid, gpu=dict(uuid=uuid))):
                with self.assertRaisesRegex(ValueError, 'privileged_exact_uuid'):
                    handover.admission_status(Path('/native/service.json'))


if __name__ == '__main__':
    unittest.main()
