import unittest
from pathlib import Path
from unittest.mock import patch

import r188_finish_boundary as repair


class BoundaryRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.spec = dict(backing_root='/root', config_path='/old/GUARD.json')
        self.boundary = dict(record=dict(kind='SLEEP_COMPLETE', sha256='saved'), actors=[])

    def test_previous_dispatch_is_not_retried(self):
        with patch.object(Path, 'exists', return_value=True):
            with self.assertRaisesRegex(ValueError, 'unknown_or_previous_dispatch'):
                repair.eligible(Path('/owned'), self.spec, self.boundary)

    def test_advanced_head_is_not_rolled_back(self):
        with patch.object(Path, 'exists', return_value=False), \
                patch.object(repair.base, 'head', return_value=dict(sha256='new')):
            with self.assertRaisesRegex(ValueError, 'same_latest_complete'):
                repair.eligible(Path('/owned'), self.spec, self.boundary)

    def test_exact_saved_predispatch_boundary_allowed(self):
        with patch.object(Path, 'exists', return_value=False), \
                patch.object(Path, 'glob', return_value=[]), \
                patch.object(repair.base, 'head', return_value=dict(sha256='saved')), \
                patch.object(repair.time, 'time', return_value=repair.base.HARD_END - 600):
            repair.eligible(Path('/owned'), self.spec, self.boundary)

    def test_late_admission_rejected(self):
        with patch.object(Path, 'exists', return_value=False), \
                patch.object(Path, 'glob', return_value=[]), \
                patch.object(repair.base, 'head', return_value=dict(sha256='saved')), \
                patch.object(repair.time, 'time', return_value=repair.base.HARD_END - 179):
            with self.assertRaisesRegex(ValueError, 'unchanged_boundary_admission_deadline'):
                repair.eligible(Path('/owned'), self.spec, self.boundary)


if __name__ == '__main__':
    unittest.main()
