import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r120_route_clock as lease
from gpu import orch_r120_route_shared_launch as launcher


class RouteContinuationTests(unittest.TestCase):
    def setUp(self):
        self.limits = dict(train_end_unix=4000, hard_end_unix=4120, lease_end_unix=25720)
        self.original = dict(bounds=dict(native_calls=32768, parent_calls=16384, cycles=512,
            hard_end_unix=1000, lease_end_unix=22600), shared_learner=dict(branch='F1', root='/common'))
        self.plan = deepcopy(self.original)
        self.plan.update(bounds=lease.updated_bounds(self.original['bounds'], self.limits),
            parent_wait_seconds=600, lease_continuation=dict(policy=dict(path='/clock', sha256='clock')))

    def check(self):
        with patch.object(lease, 'current', return_value=self.limits), patch.dict(
                'os.environ', ORCH_R119_LEASE_CLOCK='/clock', ORCH_R119_LEASE_CLOCK_SHA256='clock'):
            return lease.same_life(self.plan, self.original)

    def test_same_quotas_new_clock(self):
        self.assertTrue(self.check())
        self.assertEqual(self.original['bounds']['hard_end_unix'], 1000)

    def test_no_native_parent_cycle_quota_reset(self):
        for key in ('native_calls', 'parent_calls', 'cycles'):
            old = self.plan['bounds'][key]
            self.plan['bounds'][key] += 1
            with self.assertRaisesRegex(ValueError, 'quota_reset'):
                self.check()
            self.plan['bounds'][key] = old

    def test_shared_owner_lineage_cannot_change(self):
        self.plan['shared_learner']['root'] = '/other'
        with self.assertRaisesRegex(ValueError, 'unchanged_shared_lineage'):
            self.check()

    def test_astra_keeps_120_fable_general_era_600(self):
        self.original['shared_learner']['branch'] = 'A1'
        self.plan['shared_learner']['branch'] = 'A1'
        with self.assertRaisesRegex(ValueError, 'transport_era'):
            self.check()
        self.plan['parent_wait_seconds'] = 120
        self.assertTrue(self.check())

    def test_completed_final_hash_checked_no_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, value in [('complete', {}), ('terminal', dict(success=True, returncode=0)), ('selection', {})]:
                (root / name).write_text(json.dumps(value))
            self.plan['lease_continuation']['completed_final'] = {
                name: lease.reference(root / name) for name in ('complete', 'terminal', 'selection')}
            self.assertEqual(lease.preserve_final(self.plan)['status'], 'PRESERVED_COMPLETED_FINAL_NO_REPLAY')
            (root / 'terminal').write_text('{}')
            with self.assertRaises(ValueError):
                lease.preserve_final(self.plan)

    def test_privileged_service_keeps_clock_and_empty_cvd(self):
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'python3', '-B', '-m', 'module', 'service', '--root', '/root']
        result = launcher.privileged_command(command, dict(path='/request', sha256='request'), dict(path='/clock', sha256='clock'))
        self.assertIn('CUDA_VISIBLE_DEVICES=', result)
        self.assertIn('ORCH_R119_LEASE_CLOCK=/clock', result)
        self.assertEqual(result[-3:], ['service', '--root', '/root'])

    def test_privileged_scan_uses_tested_proof_new_wrapper(self):
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'python3', '-B', '-m', 'module', 'scan', '--root', '/root']
        result = launcher.privileged_command(command, dict(path='/request', sha256='request'), dict(path='/clock', sha256='clock'))
        self.assertIn(str(Path(launcher.__file__).resolve()), result)
        self.assertIn('ORCH_R119_LEASE_CLOCK_SHA256=clock', result)
        self.assertEqual(result[-4:], ['--request', '/request', '--request-sha256', 'request'])

    def test_all_successor_sources_compile(self):
        source = Path(lease.__file__).parent
        for name in ('client', 'lifecycle', 'run', 'launch'):
            path = source / ('orch_r120_route_shared_' + name + '.py')
            compile(path.read_text(), str(path), 'exec')

    def test_fresh_readout_exec_is_clock_bound_and_final_disabled(self):
        text = Path(lease.__file__).with_name('orch_r120_route_shared_run.py').read_text()
        tree = ast.parse(text)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run_readout')
        snippet = ast.get_source_segment(text, function)
        self.assertIn("'gpu.orch_r120_route_shared_run'", snippet)
        self.assertIn('return lease.preserve_final(plan)', snippet)
        self.assertNotIn("write(root/'FINAL_MORNING_REQUESTED.json'", text)

    def test_serial_adoption_bounds_not_mutated(self):
        text = Path(lease.__file__).with_name('orch_r120_route_shared_client.py').read_text()
        self.assertIn("super().__init__(root, dict(plan, bounds=original['bounds']))", text)
        self.assertIn("only_F1_has_optimizer", text)
        self.assertNotIn('coordinator.initialize(', text)


if __name__ == '__main__':
    unittest.main()
