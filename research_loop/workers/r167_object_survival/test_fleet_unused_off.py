import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fleet_gpu_controller as controller
from test_fleet_gpu_controller import ControllerTests


class UnusedOffTests(unittest.TestCase):
    def test_every_previous_attempt_and_job_is_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pipeline = ControllerTests().fixture(root)
            condition = controller.evaluator.queue.CONDITIONS[1]
            prior = root / 'gpu_operation1'
            current = root / 'gpu_operation2'
            jobs = root / 'jobs'
            for directory in (prior, current, jobs):
                directory.mkdir()
            for sleep, directory, suffix in ((0, prior, '.ONCE.json'),
                    (11, current, '.ONCE.json'), (12, jobs, '.CONFIG.json')):
                key = controller.evaluator.queue.key('example', sleep, condition)
                controller.protocol.write(directory / (key + suffix), dict(status='PRESERVED'))
            with patch.object(controller, 'ROOT', root):
                self.assertEqual([row['sleep'] for row in controller.candidates(pipeline, 1)], [13])

    def test_does_not_reuse_original_operation_directory(self):
        self.assertEqual(controller.OPERATION_NAME, 'gpu_operation2')


if __name__ == '__main__':
    unittest.main()
