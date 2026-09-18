"""Transport failure fixtures cannot authorize regenerating native data."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_terse_breadth_retry as retry
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

    def test_failed_guard_is_archived_before_successful_native_start(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            count = 0

            def invoke(arguments):
                nonlocal count
                count += 1
                if count == 1:
                    launch = root / 'launch_train0'
                    launch.mkdir()
                    (launch / 'RESOURCE.json').write_text(json.dumps(dict(clear=False)))
                    return SimpleNamespace(returncode=1)
                self.assertFalse((root / 'launch_train0').exists())
                self.assertEqual(len(list((root / 'admission_failures').glob('train0_*'))), 1)
                (root / 'train0').mkdir()
                return SimpleNamespace(returncode=0)

            with patch.object(retry.subprocess, 'run', side_effect=invoke), patch.object(retry.time, 'sleep'):
                self.assertEqual(retry.main([str(root), '0', 'train', 'source', 'publication', 'manifest', 'model']), 0)
            self.assertEqual(count, 2)

    def test_failed_native_stage_never_invoked_twice(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)

            def invoke(arguments):
                (root / 'after5').mkdir()
                (root / 'after5/FAILED.json').write_text('{}')
                return SimpleNamespace(returncode=1)

            with patch.object(retry.subprocess, 'run', side_effect=invoke) as process:
                self.assertEqual(retry.main([str(root), '5', 'after', 'source', 'publication', 'manifest', 'model']), 1)
                self.assertEqual(process.call_count, 1)


if __name__ == '__main__':
    unittest.main()
