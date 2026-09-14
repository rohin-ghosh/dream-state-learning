"""Transport failure fixtures cannot authorize regenerating native data."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gpu.orch_terse_breadth_retry import retryable


class AdmissionRetryTests(unittest.TestCase):
    def test_only_pre_native_scan_failure_can_retry(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertFalse(retryable(root, '0', 'train'))
            launch = root / 'launch_train0'
            launch.mkdir()
            (launch / 'RESOURCE.json').write_text(json.dumps(dict(clear=False, unresolved=['transient_ssh'])))
            self.assertTrue(retryable(root, '0', 'train'))
            (root / 'train0').mkdir()
            self.assertFalse(retryable(root, '0', 'train'))
            (root / 'train0/FAILED.json').write_text('{}')
            self.assertFalse(retryable(root, '0', 'train'))

    def test_clear_scan_failure_is_not_regeneratable(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            launch = root / 'launch_after5'
            launch.mkdir()
            (launch / 'RESOURCE.json').write_text(json.dumps(dict(clear=True)))
            self.assertFalse(retryable(root, '5', 'after'))


if __name__ == '__main__':
    unittest.main()
