import ast
from copy import deepcopy
import hashlib
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r145_node3_target_handoff as handoff


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / 'research_loop/workers/r144_node3_target_handoff_20260916t1541z_operator5/BOUNDARY_API.py'
ORIGINAL = ROOT / 'gpu/orch_r144_node3_target_handoff.py'


def plan(physical=6):
    label, tag, gpu_uuid = handoff.OWNED[physical]
    base = handoff.BASE / ('orch_r133_node3_' + label + '_20260916_attempt1')
    return dict(physical=physical, gpu_uuid=gpu_uuid, root=str(base / 'run1'),
                source_root=str(base / ('source_r145_20260916t1611z_' + tag)))


class TargetSuccessorTests(unittest.TestCase):
    def test_only_exact_recovered5_6_roots(self):
        for physical in (5, 6):
            self.assertEqual(handoff.lane_scope(plan(physical)), physical)
        for physical in (0, 1, 2, 3, 4, 7, True):
            with self.assertRaises(ValueError):
                handoff.lane_scope(dict(plan(), physical=physical))
        for field in ('source_root', 'root', 'gpu_uuid'):
            with self.assertRaises(ValueError):
                handoff.lane_scope(dict(plan(), **{field: 'wrong'}))

    def test_recovery_and_wall_plan_injections_rejected(self):
        for key in ('preupdate_recovery', 'authorized_wall_extension'):
            with self.assertRaises(ValueError):
                handoff.lane_scope(dict(plan(), **{key: {'unexpected': True}}))

    def test_only_recovery_bindings_removed_from_ordinary_guard(self):
        old = dict(plan_path='oldplan', plan_sha256='oldsha', source_pins={'native': 'old'},
            attempt_dir='oldcontrol', resume=True, allocation_path='oldallocation', allocation_sha256='oldallocationhash',
            device_containment=dict(unit='oldunit', minor=6, uid=2524, gid=2524), lease_sha256='samelease',
            r145_manifest={'sha256': 'manifest'}, r145_acknowledgment={'sha256': 'ack'})
        new = deepcopy(old)
        new.pop('r145_manifest')
        new.pop('r145_acknowledgment')
        new.update(attempt_dir='newcontrol', plan_sha256='newsha')
        new['device_containment']['unit'] = 'newunit'
        handoff.guard_delta(old, new)
        for change in ({'r145_manifest': old['r145_manifest']}, {'lease_sha256': 'changed'}):
            with self.assertRaises(ValueError):
                handoff.guard_delta(old, dict(new, **change))

    def test_ready_first_pidfd_retirement_admission_and_monitor_unchanged(self):
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
                         '014e23e330db36f0ef6a8da23f75084a7685e7e0663a1e9540759dac7fc0da5c')
        original = {node.name: node for node in ast.parse(ORIGINAL.read_text()).body if isinstance(node, ast.FunctionDef)}
        current = {node.name: node for node in ast.parse(Path(handoff.__file__).read_text()).body if isinstance(node, ast.FunctionDef)}
        for name in ('handoff', 'supervise', 'contained', 'monitor', 'claim_boundary', 'saved_evidence', 'readmit'):
            with self.subTest(function=name):
                self.assertEqual(ast.dump(original[name], include_attributes=False), ast.dump(current[name], include_attributes=False))

    def test_original_API_pins_and_only_old_identity_relocated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'BOUNDARY_API.py').write_bytes(API.read_bytes())
            with patch.object(handoff, '__file__', str(path / 'OPERATOR.py')):
                api = handoff.api()
            self.assertEqual(set(api.DEVICES), {5, 6})
            self.assertIs(api.family_scope, handoff.lane_scope)
            self.assertEqual(api.process_pair.__globals__['NATIVE'], handoff.RECOVERY_MODULE)
            self.assertEqual(api.identity.__globals__['NATIVE'], handoff.GUARD_MODULE)
            self.assertEqual(api.originals.__globals__['NATIVE'], handoff.GUARD_MODULE)

    def test_scope_gate_before_stage_files_and_no_recovery_successor(self):
        source = inspect.getsource(handoff.new_modules)
        self.assertIn('ordinary_guard_no_recovery_entry', source)
        ordinary = inspect.getsource(handoff.contained_command)
        self.assertIn("'contained-native'", ordinary)
        self.assertNotIn(handoff.RECOVERY_MODULE, ordinary)
        self.assertNotIn('recover_admitted_sleep', ordinary)

    def test_requires_both_completed_continuations_before_stage(self):
        source = inspect.getsource(handoff.stage)
        self.assertIn('both_durable_loaded_TRAIN_continuations_first', source)
        self.assertIn('DURABLE_REPLACEMENT_LOADED_TRAIN_CONTINUATION_VERIFIED', source)
        self.assertLess(source.index('both_durable_loaded_TRAIN_continuations_first'), source.index('output.mkdir()'))


if __name__ == '__main__':
    unittest.main()
