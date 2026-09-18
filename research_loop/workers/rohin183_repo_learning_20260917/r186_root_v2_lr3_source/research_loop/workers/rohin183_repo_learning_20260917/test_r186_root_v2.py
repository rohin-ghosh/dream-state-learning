"""Pure pre-I/O regression for the frozen transport's actual root contract."""

from pathlib import Path
import unittest

from gpu.orch_r153_community_transport import remote_root
from research_loop.workers.rohin183_repo_learning_20260917.r186_copy import ARMS, REMOTE_ROOT


class RootTests(unittest.TestCase):
    def test_failed_first_attempt_root_rejected(self):
        for label in ARMS:
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, 'new_canonical_R153_life_root'):
                remote_root('/localhome/local-rohing/orch_r186_c2_plasticity_20260917/' + label + '1/raw')

    def test_every_new_actual_bridge_root_accepted(self):
        self.assertIn('r153', Path(REMOTE_ROOT).name)
        for label in ARMS:
            with self.subTest(label=label):
                root = Path(REMOTE_ROOT) / (label + '2') / 'raw'
                self.assertEqual(remote_root(str(root)), root)


if __name__ == '__main__':
    unittest.main()
