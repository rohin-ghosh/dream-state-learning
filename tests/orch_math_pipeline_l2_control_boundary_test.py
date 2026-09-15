from pathlib import Path
import tempfile
import unittest

from gpu import orch_math_pipeline_l2_control_boundary as boundary


class ControlBoundaryTest(unittest.TestCase):
    def test_safe_boundary_requires_complete_and_verified_post_mount(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            boundary.common.write(path / 'COMPLETE.json', dict(status='COMPLETE'))
            boundary.common.write(path / 'AFTER.json', dict(actual_mounted_identity_verified=False))
            with self.assertRaises(AssertionError):
                boundary.require_complete(path)
            boundary.common.write(path / 'AFTER.json', dict(actual_mounted_identity_verified=True))
            self.assertEqual(boundary.require_complete(path)['status'], 'COMPLETE')


if __name__ == '__main__':
    unittest.main()
