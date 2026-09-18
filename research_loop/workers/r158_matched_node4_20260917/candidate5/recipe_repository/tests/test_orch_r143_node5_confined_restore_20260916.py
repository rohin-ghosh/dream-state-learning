import ast
from copy import deepcopy
import importlib.util
import inspect
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'research_loop/workers/r143_node5_allocator_20260916t1427z'
SPEC = importlib.util.spec_from_file_location('r143_confined_test', ROOT / 'node5_confined_restore_20260916t1616z.py')
restore = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(restore)


class Node5ConfinedRestoreTests(unittest.TestCase):
    def setUp(self):
        self.helper = restore.api()
        self.capsule = restore.confinement()
        self.config = dict(attempt_dir='/old', resume=True, plan_sha256='same', source_pins={'same':'same'})
        self.policy = dict(uid=2524, gid=2524, minor=2, unit='orch-r136-native-' + 'a'*32)
        self.plan = dict(physical=2, gpu_uuid=self.capsule.DEVICES[2], source_root='/localhome/local-rohing/frozen')

    def test_original_boundary_API_hash(self):
        self.assertEqual(self.helper.sha(ROOT / 'BOUNDARY_API.py'), restore.API_SHA)

    def test_four_sanctioned_function_bodies_identical(self):
        original = ast.parse((ROOT / 'CONFINEMENT_ORIGIN.py').read_text())
        candidate = ast.parse((ROOT / 'CONFINEMENT_API.py').read_text())
        originals = {node.name:ast.dump(node,include_attributes=False) for node in original.body if isinstance(node,ast.FunctionDef)}
        for node in candidate.body:
            if isinstance(node,ast.FunctionDef) and node.name not in ('require','require_host'):
                self.assertEqual(ast.dump(node,include_attributes=False),originals[node.name])

    def test_only_original_node5_two_UUID_bindings(self):
        self.assertEqual(self.capsule.DEVICES, {physical:self.helper.LANES[physical][2] for physical in (2,6)})

    def test_command_preserves_every_sanctioned_token_except_inner_allocator(self):
        config=dict(device_containment=self.policy)
        payload=['python','exact-original-native']
        original=self.capsule.device_containment_command(2,2,2524,2524,self.policy['unit'],self.plan['source_root'],payload,100)
        actual=restore.command(config,self.plan,payload,100)
        position=actual.index('/usr/bin/env')
        self.assertEqual(actual[position+1:position+3],['-i','PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True'])
        self.assertEqual(actual[:position+2]+actual[position+3:],original)

    def test_exact_device_allowlist_and_no_capabilities(self):
        actual=restore.command(dict(device_containment=self.policy),self.plan,['python'],100)
        allowed=[item for item in actual if item.startswith('--property=DeviceAllow=')]
        self.assertEqual(allowed,['--property=DeviceAllow=', '--property=DeviceAllow=/dev/null rw',
            '--property=DeviceAllow=/dev/zero rw','--property=DeviceAllow=/dev/random r',
            '--property=DeviceAllow=/dev/urandom r','--property=DeviceAllow=/dev/nvidia2 rw',
            '--property=DeviceAllow=/dev/nvidiactl rw','--property=DeviceAllow=/dev/nvidia-uvm rw'])
        for flag in ('DevicePolicy=strict','CapabilityBoundingSet=','AmbientCapabilities=','NoNewPrivileges=yes','ProtectControlGroups=yes'):
            self.assertIn('--property='+flag,actual)

    def test_invalid_device_uid_unit_or_wall_rejected(self):
        for physical,minor,uid,unit,wall in ((7,7,2524,self.policy['unit'],100),(2,9,2524,self.policy['unit'],100),
             (2,2,0,self.policy['unit'],100),(2,2,2524,'reuse',100),(2,2,2524,self.policy['unit'],0)):
            with self.subTest(values=(physical,minor,uid,unit,wall)),self.assertRaises(ValueError):
                self.capsule.device_containment_command(physical,minor,uid,2524,unit,'/absolute',['python'],wall)

    def test_guard_delta_only_attempt_and_confinement(self):
        proposed=dict(self.config,attempt_dir='/new',device_containment=self.policy)
        restore.validate_guard_delta(self.config,proposed)
        for key in ('plan_sha256','source_pins','resume'):
            changed=deepcopy(proposed);changed[key]='changed'
            with self.subTest(key=key),self.assertRaises(ValueError):restore.validate_guard_delta(self.config,changed)

    def test_original_handoff_all_checks_except_explicit_dispatch_identical(self):
        source=inspect.getsource(self.helper.handoff)
        before="command = [str(PYTHON), '-B', '-m', GUARD, 'supervise', '--config', request['new_config']]"
        after="command = [str(PYTHON), '-B', __file__, '--action', 'supervise', '--output', str(output)]"
        calls=[]
        original_compile=compile
        def capture(text,*args,**kwargs):
            calls.append(text);return original_compile(text,*args,**kwargs)
        with patch('builtins.compile',side_effect=capture):restore.adapted_handoff()
        rewritten=next(text for text in calls if isinstance(text,str) and text.startswith('def handoff('))
        restored=rewritten.replace(after,before).replace('original_supervise=False, sanctioned_confined_supervise=True','original_supervise=True').replace('1 <= seconds <= 3600','1 <= seconds <= 1200')
        self.assertEqual(restored,source)

    def test_wait_bound_extension_keeps_original_absolute_lease_deadline(self):
        function=restore.adapted_handoff()
        self.assertIn(3600,function.__code__.co_consts)
        self.assertIn(300,function.__code__.co_consts)
        self.assertIn('hard_end_unix',function.__code__.co_consts)

    def test_new_guard_no_shared_source_replacement(self):
        source=inspect.getsource(restore.stage)
        self.assertNotIn('patch_source',source)
        self.assertNotIn('write_text',source)
        self.assertIn('validate_guard_delta',source)

    def test_native_uses_original_guard_and_launch_handshake(self):
        source=inspect.getsource(restore.contained)
        self.assertIn("'-m', GUARD, 'native'",source)
        self.assertIn("process.stdin.write(b'LAUNCH_READY\\n')",source)
        self.assertIn('publish_launch',source)
        self.assertIn('verify_device_containment',source)

    def test_pilot_restore_requires_exact_boundary_and_failed_preload_class(self):
        source=inspect.getsource(restore.preserved_pilot)
        for gate in ('2223','== 26','fresh_exclusive_admission','LAUNCH.json','all_saved_pilot_state_exact','verify_snapshot'):
            self.assertIn(gate,source)

    def test_pilot_follows_live_confined_run1_and_own_node_lock(self):
        source=inspect.getsource(restore.restore_pilot)
        self.assertLess(source.index('fcntl.flock'),source.index('preserved_pilot'))
        self.assertLess(source.index('run1_restored_confined_before_pilot'),source.index('subprocess.Popen'))


if __name__ == '__main__':
    unittest.main()
