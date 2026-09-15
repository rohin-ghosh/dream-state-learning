import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_math_pipeline_l2_guided_exit as exit_driver


class GuidedExitTest(unittest.TestCase):
    def fixture(self, root):
        campaign = root / 'campaign_02_recovery_paired'
        state = dict(state_sha256='saved-state')
        failure = dict(message='parent_backend_failure_no_substitute', arm='GUIDED_SLEEP',
            cycle=2, phase='experience', process=['boot', 1, 2], input_adapter=state)
        documents = {
            'GUIDED_SLEEP/cycle2/experience/FAILED.json': failure,
            'GUIDED_SLEEP/cycle2/experience/FAILED_AFTER.json': dict(frozen_base_verified=True,
                process=failure['process'], mounted_adapter_state_sha256='saved-state'),
            'GUIDED_SLEEP/cycle1/experience/COMPLETE.json': dict(status='COMPLETE', updates=1194, output_adapter=state),
            'parent_queue/GUIDED_SLEEP_C2.response.json': dict(status='FAILED', error=dict(type='TimeoutError'))}
        for name, value in documents.items():
            path = campaign / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))
        return campaign

    def test_zero_write_timeout_preserves_predecessor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign = self.fixture(root)
            self.assertEqual(exit_driver.binding(root)[0], campaign)

    def test_any_write_rejects_unchanged_state_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign = self.fixture(root)
            (campaign / 'GUIDED_SLEEP/cycle2/experience/LOSSES.jsonl').write_text('{}\n')
            with self.assertRaises(AssertionError):
                exit_driver.binding(root)


if __name__ == '__main__':
    unittest.main()
