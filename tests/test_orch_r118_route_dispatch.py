import inspect
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r118_route_dispatch as dispatch


class DispatchTests(unittest.TestCase):
    def test_rejects_other_gpu(self):
        with self.assertRaisesRegex(ValueError, 'only_owned_node3'):
            dispatch.scan('a100_4', Path('/service'))

    def test_privileged_target_is_original_node3_device(self):
        with patch.object(dispatch.os, 'geteuid', return_value=0), \
                patch.object(dispatch.idle, 'scan', return_value={'clear': True}) as scan:
            self.assertTrue(dispatch.scan('node3_3', Path('/service'))['clear'])
            scan.assert_called_once_with(3, Path('/service'))
            policy = dispatch.recovery.old.admission.minor.pinned.policy
            self.assertEqual(policy.DEVICES, {3: 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e'})

    def test_unprivileged_scan_reexecutes_same_scoped_dispatch(self):
        with patch.object(dispatch.os, 'geteuid', return_value=1000), \
                patch.object(dispatch.subprocess, 'check_output', return_value='{"clear":true}') as run:
            dispatch.scan('node3_3', Path('/service'))
            self.assertIn('gpu.orch_r118_route_dispatch', run.call_args.args[0])
            self.assertEqual(run.call_args.args[0][:2], ['sudo', '-n'])

    def test_guard_changes_scanner_only_and_restores_namespace(self):
        original = dispatch.recovery.old.guard
        def invoke(root, lane):
            current = dispatch.recovery.old.guard
            self.assertIs(current.__code__, original.__code__)
            self.assertIs(current.__globals__['admission'].scan, dispatch.scan)
            self.assertIs(current.__globals__['policy'], original.__globals__['policy'])
            self.assertEqual(inspect.getsource(current), inspect.getsource(original))
            return 'dispatched'
        with patch.object(dispatch.recovery, 'guard', side_effect=invoke):
            self.assertEqual(dispatch.guard(Path('/root'), 'node3_3'), 'dispatched')
        self.assertIs(dispatch.recovery.old.guard, original)


if __name__ == '__main__':
    unittest.main()
