import copy
import unittest
from unittest.mock import patch
from pathlib import Path

import r181_boundary as boundary


class BoundaryTests(unittest.TestCase):
    def saved_record(self):
        state = dict(pending=None, rows=[1, 2, 3], sleep_frontier=3,
            sleep_receipts=[dict(status='COMPLETE')], deadline_unix=boundary.HARD_END)
        record = dict(kind='SLEEP_COMPLETE', document=dict(status='COMPLETE',
            resume_state=dict(state=state, sha256=boundary.digest(state))))
        record['sha256'] = boundary.digest(record)
        return record

    def test_saved_frontier_only(self):
        self.assertIsNone(boundary.saved_state(dict(kind='UPDATE')))
        record = self.saved_record()
        self.assertEqual(boundary.saved_state(record), record['document']['resume_state']['state'])
        record['document']['resume_state']['state']['pending'] = 'sleep:unfinished'
        with self.assertRaises(ValueError):
            boundary.saved_state(record)

    def test_invalid_saved_state_cannot_be_retired(self):
        for field, value in [('pending', 'request'), ('sleep_frontier', 2), ('deadline_unix', boundary.HARD_END + 1)]:
            record = self.saved_record()
            envelope = record['document']['resume_state']
            envelope['state'][field] = value
            envelope['sha256'] = boundary.digest(envelope['state'])
            record['sha256'] = boundary.digest({key: item for key, item in record.items() if key != 'sha256'})
            with self.assertRaises(ValueError):
                boundary.saved_state(record)

    def test_new_service_preserves_root_source_device_and_stop(self):
        folder = Path('/owned/physical3')
        config = dict(device_containment=dict(uid=2524, gid=2524, minor=3, unit='owned'))
        plan = dict(source_root='/prior/source', root='/logical/life', gpu_uuid='GPU-bound', physical=3)
        documents = {'GUARD.json': config, 'PLAN.json': plan, 'LIVE_HANDOFF.json': dict(backing_root='/actual/life')}
        with patch.object(boundary, 'read', side_effect=lambda path: documents[path.name]), patch.object(boundary.time, 'time', return_value=boundary.HARD_END - 600):
            command = boundary.command(folder, 'contained')
            self.assertIn('--property=BindPaths=/actual/life:/logical/life', command)
            self.assertIn('--property=BindReadOnlyPaths=/owned/physical3/new_native.py:/prior/source/gpu/orch_r125_continual_native.py', command)
            self.assertIn('--property=DeviceAllow=/dev/nvidia3 rw', command)
            self.assertNotIn('--property=DeviceAllow=/dev/nvidia4 rw', command)
            self.assertIn('--property=RuntimeMaxSec=600', command)
            self.assertIn('CUDA_VISIBLE_DEVICES=GPU-bound', command)
            cpu = boundary.command(folder, 'cpu', cpu=True)
            self.assertFalse(any('DeviceAllow=/dev/nvidia' in value for value in cpu))


if __name__ == '__main__':
    unittest.main()
