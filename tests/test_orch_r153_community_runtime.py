import json
import os
from pathlib import Path
import shutil
import stat
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r153_community_launch as launch
from gpu import orch_r153_community_runtime as runtime
from tests import test_orch_r153_community_launch as launch_tests


class CommunityRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = launch_tests.CommunityLaunchTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        for agent in self.fixture.request['agents']:
            agent['destination'] = str(self.root / 'deployed' / agent['id'])
        self.staged = self.fixture.stage()
        self.manifest = launch.verify(self.staged['manifest'])
        self.gate = self.fixture.launch_gate(self.manifest)
        gate_ref = self.fixture.reference('gate.json', self.gate)
        self.prepared = launch.prepare(self.staged['manifest'], 'C1', gate_ref['path'], self.root / 'promotion')
        self.destination = self.root / 'deployed/C1'
        shutil.copytree(self.root / 'candidate/C1', self.destination)
        self.destination.chmod(0o700)
        shutil.copytree(self.root / 'promotion', self.prepared['deploy_to'])
        self.config_path = Path(self.prepared['deploy_to']) / 'GUARD.json'
        self.config = json.loads(self.config_path.read_bytes())
        self.plan = json.loads((self.destination / 'config/PLAN.json').read_bytes())
        self.attempt = Path(self.config['attempt_dir'])
        self.report = dict(clear=True, scanner_euid=0, blocking_reasons=[], gpu=dict(uuid=self.plan['gpu_uuid']))

    def validate(self):
        with patch('gpu.orch_r125_continual_guard.validate', return_value=(self.config, self.plan)) as guard:
            result = runtime.validate_promotion(self.config_path)
            guard.assert_called_once_with(self.config_path)
            return result

    def change_gate(self, **changes):
        gate = dict(self.gate, **changes)
        path = Path(self.config['r153_main_gate_path'])
        path.chmod(0o644)
        raw = launch.encoded(gate)
        path.write_bytes(raw)
        path.chmod(0o444)
        self.config['r153_main_gate_sha256'] = launch.digest(raw)

    def test_promotion_delegates_original_guard_and_checks_all_runtime_assets(self):
        config, plan = self.validate()
        self.assertEqual(config['plan_sha256'], launch.digest((self.destination / 'config/PLAN.json').read_bytes()))
        self.assertFalse(config['resume'])
        self.assertEqual(plan['gpu_uuid'], self.manifest['agents']['C1']['gpu_uuid'])

    def test_original_guard_failure_cannot_be_bypassed(self):
        with patch('gpu.orch_r125_continual_guard.validate', side_effect=ValueError('guard_source_or_lease')):
            with self.assertRaisesRegex(ValueError, 'guard_source_or_lease'):
                runtime.validate_promotion(self.config_path)

    def test_runtime_asset_change_rejected(self):
        path = self.destination / 'source' / launch.RUNTIME
        path.chmod(0o644)
        path.write_text('{}')
        path.chmod(0o444)
        with self.assertRaisesRegex(ValueError, 'entire_deployed_source'):
            self.validate()

    def test_expired_exact_gate_rejected(self):
        self.change_gate(expires_unix=time.time() - 1)
        with self.assertRaisesRegex(ValueError, 'unexpired_single_attempt'):
            self.validate()

    def test_resume_never_allowed(self):
        self.config['resume'] = True
        with self.assertRaisesRegex(ValueError, 'new_life_gate_no_resume'):
            self.validate()

    def test_actual_plan_cannot_switch_to_executor(self):
        self.plan['physical'] = 2
        with self.assertRaisesRegex(ValueError, 'exact_plan_agent_slot'):
            self.validate()

    def test_community_config_change_rejected(self):
        path = self.destination / 'config/COMMUNITY.json'
        community = json.loads(path.read_bytes())
        community['parent']['speaker'] = 'Rohin'
        path.chmod(0o644)
        path.write_bytes(launch.encoded(community))
        path.chmod(0o444)
        with self.assertRaisesRegex(ValueError, 'immutable_community'):
            self.validate()

    def test_supervisor_uses_fresh_original_privileged_scan_then_generic_containment(self):
        with (patch.object(runtime, 'validate_promotion', return_value=(self.config, self.plan)) as validate,
              patch.object(runtime.subprocess, 'check_output', return_value=json.dumps(self.report)) as scan,
              patch.object(runtime.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run):
            result = runtime.supervise(self.config_path)
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(validate.call_count, 2)
        scan_command = scan.call_args.args[0]
        self.assertEqual(scan_command[:4], ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES='])
        self.assertIn('gpu.orch_r125_continual_guard', scan_command)
        self.assertIn('scan', scan_command)
        command = run.call_args.args[0]
        self.assertIn('--property=DevicePolicy=strict', command)
        self.assertIn('--property=DeviceAllow=/dev/nvidia' + str(self.config['device_containment']['minor']) + ' rw', command)
        self.assertIn('gpu.orch_r153_community_runtime', command)
        self.assertIn('contained-native', command)
        self.assertTrue((self.attempt / 'DISPATCH_ONCE').is_dir())
        self.assertTrue((self.attempt / 'ADMISSION_TIME.json').is_file())
        self.assertEqual(Path(self.plan['root']).stat().st_mode & 0o777, 0o700)

    def test_failed_or_unprivileged_scan_never_dispatches(self):
        for report in (dict(self.report, clear=False), dict(self.report, scanner_euid=1234),
                       dict(self.report, blocking_reasons=['occupied']), dict(self.report, gpu=dict(uuid='GPU-wrong'))):
            with self.subTest(report=report):
                self.config['attempt_dir'] = str(self.destination / ('attempt_' + str(len(list(self.destination.iterdir())))))
                with (patch.object(runtime, 'validate_promotion', return_value=(self.config, self.plan)),
                      patch.object(runtime.subprocess, 'check_output', return_value=json.dumps(report)),
                      patch.object(runtime.subprocess, 'run') as run):
                    with self.assertRaisesRegex(ValueError, 'fresh_global_exclusive_admission'):
                        runtime.supervise(self.config_path)
                    run.assert_not_called()

    def test_existing_state_prevents_even_scanner_call(self):
        (Path(self.plan['root']) / 'stream').mkdir(parents=True)
        with (patch.object(runtime, 'validate_promotion', return_value=(self.config, self.plan)),
              patch.object(runtime.subprocess, 'check_output') as scan):
            with self.assertRaisesRegex(ValueError, 'new_root_no_saved_state'):
                runtime.supervise(self.config_path)
            scan.assert_not_called()

    def test_existing_attempt_is_not_retried(self):
        self.attempt.mkdir()
        with (patch.object(runtime, 'validate_promotion', return_value=(self.config, self.plan)),
              patch.object(runtime.subprocess, 'check_output') as scan):
            with self.assertRaises(FileExistsError):
                runtime.supervise(self.config_path)
            scan.assert_not_called()

    def test_service_failure_retained_without_retry(self):
        with (patch.object(runtime, 'validate_promotion', return_value=(self.config, self.plan)),
              patch.object(runtime.subprocess, 'check_output', return_value=json.dumps(self.report)),
              patch.object(runtime.subprocess, 'run', return_value=SimpleNamespace(returncode=7)) as run):
            with self.assertRaisesRegex(ValueError, 'contained_service_failed_no_retry'):
                runtime.supervise(self.config_path)
            run.assert_called_once()
        self.assertEqual(json.loads((self.attempt / 'SERVICE_EXIT.json').read_bytes())['returncode'], 7)

    def hardware_context(self, *, descriptors=None, opening=None, wrong_cgroup=False):
        from contextlib import ExitStack
        stack = ExitStack()
        self.addCleanup(stack.close)
        policy = self.config['device_containment']
        def text(path, *args, **kwargs):
            if str(path) == '/proc/self/cgroup':
                return 'wrong' if wrong_cgroup else '0::/system.slice/' + policy['unit'] + '.service\n'
            return 'GPU UUID: ' + self.plan['gpu_uuid'] + '\nDevice Minor: ' + str(policy['minor']) + '\n'
        host = 'ipp2-ovx-p1-10' if self.config['r153_agent'].get('profile') == launch.NODE5_PROFILE else 'ovx2'
        stack.enter_context(patch.object(runtime.socket, 'gethostname', return_value=host))
        stack.enter_context(patch.object(runtime.os, 'getuid', return_value=policy['uid']))
        stack.enter_context(patch.object(runtime.os, 'getgid', return_value=policy['gid']))
        stack.enter_context(patch.object(Path, 'read_text', text))
        stack.enter_context(patch.object(Path, 'glob', return_value=[Path('/proc/fake/information')]))
        stack.enter_context(patch.object(Path, 'lstat', return_value=SimpleNamespace(
            st_mode=stat.S_IFCHR, st_rdev=os.makedev(195, policy['minor']))))
        stack.enter_context(patch('gpu.orch_r137_node4_containment.gpu_descriptors', return_value=descriptors or []))
        stack.enter_context(patch.dict(os.environ, dict(CUDA_VISIBLE_DEVICES=self.plan['gpu_uuid'],
                                  PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True'), clear=True))
        opening = stack.enter_context(patch.object(runtime.os, 'open', side_effect=opening or PermissionError('denied')))
        return opening

    def test_foreign_device_denial_is_proved_not_assumed_from_CVD(self):
        opening = self.hardware_context()
        proof = runtime.verify_containment(self.config, self.plan)
        self.assertEqual(proof['denied_foreign_minors'],
                         [minor for minor in range(8) if minor != self.config['device_containment']['minor']])
        self.assertEqual(opening.call_count, 7)

    def test_foreign_device_open_aborts_before_native(self):
        self.hardware_context(opening=lambda *args: 99)
        with patch.object(runtime.os, 'close') as close:
            with self.assertRaisesRegex(ValueError, 'foreign_GPU_not_denied'):
                runtime.verify_containment(self.config, self.plan)
            close.assert_called_once_with(99)

    def test_missing_device_is_not_proof_of_denial(self):
        self.hardware_context(opening=FileNotFoundError('missing'))
        with self.assertRaises(FileNotFoundError):
            runtime.verify_containment(self.config, self.plan)

    def test_inherited_GPU_descriptor_aborts(self):
        opening = self.hardware_context(descriptors=[{'fd': 3}])
        with self.assertRaisesRegex(ValueError, 'no_inherited_GPU_descriptors'):
            runtime.verify_containment(self.config, self.plan)
        opening.assert_not_called()

    def test_wrong_cgroup_aborts(self):
        opening = self.hardware_context(wrong_cgroup=True)
        with self.assertRaisesRegex(ValueError, 'exact_contained_service'):
            runtime.verify_containment(self.config, self.plan)
        opening.assert_not_called()

    def test_contained_entry_uses_original_guard_native_startup_handshake(self):
        self.attempt.mkdir()
        launch.write_new(self.attempt / 'ADMISSION.json', launch.encoded(self.report))
        launch.write_new(self.attempt / 'ADMISSION_TIME.json', launch.encoded(dict(verified_unix=time.time())))
        process = Mock(pid=123456)
        process.wait.return_value = 0
        with (patch.object(runtime, 'validate_promotion', return_value=(self.config, self.plan)),
              patch.object(runtime, 'verify_containment', return_value={'synthetic': True}),
              patch.object(runtime.subprocess, 'Popen', return_value=process) as popen,
              patch('gpu.orch_r133_retire_old_lanes.identity', return_value={'start_ticks': '123'}),
              patch('gpu.orch_r133_code_feedback_guard.reap_owned_child') as reap):
            runtime.contained_native(self.config_path)
        command = popen.call_args.args[0]
        self.assertIn('gpu.orch_r125_continual_guard', command)
        self.assertIn('native', command)
        self.assertNotIn('--resume', command)
        process.stdin.write.assert_called_once_with(b'LAUNCH_READY\n')
        process.stdin.close.assert_called_once()
        reap.assert_not_called()
        receipt = json.loads((self.attempt / 'LAUNCH.json').read_bytes())
        self.assertEqual(receipt['guard_sha256'], launch.digest(self.config_path.read_bytes()))
        self.assertTrue(receipt['no_retry'])
        self.assertEqual(receipt['parent_start_ticks'], '123')

    def test_stale_admission_does_not_spawn_native(self):
        self.attempt.mkdir()
        launch.write_new(self.attempt / 'ADMISSION.json', launch.encoded(self.report))
        launch.write_new(self.attempt / 'ADMISSION_TIME.json', launch.encoded(dict(verified_unix=time.time() - 101)))
        with (patch.object(runtime, 'validate_promotion', return_value=(self.config, self.plan)),
              patch.object(runtime, 'verify_containment', return_value={'synthetic': True}),
              patch.object(runtime.subprocess, 'Popen') as popen):
            with self.assertRaisesRegex(ValueError, 'fresh_admission_before_native_start'):
                runtime.contained_native(self.config_path)
            popen.assert_not_called()


class Node5RuntimeTests(CommunityRuntimeTests):
    def setUp(self):
        original_stage = launch_tests.CommunityLaunchTests.stage
        original_gate = launch_tests.CommunityLaunchTests.launch_gate

        def stage_node5(fixture):
            launch_tests.configure_node5(fixture)
            return original_stage(fixture)

        def gate_node5(fixture, manifest):
            gate = original_gate(fixture, manifest)
            gate.pop('retirement')
            gate.pop('donor_release_verified')
            gate.update(profile=launch.NODE5_PROFILE, capacity_release_verified=True,
                        capacity_release=fixture.request['capacity_release'])
            return gate

        clock = patch.object(launch.time, 'time', return_value=launch.NODE5_WALL - 3600)
        clock.start()
        self.addCleanup(clock.stop)
        with (patch.object(launch_tests.CommunityLaunchTests, 'stage', stage_node5),
              patch.object(launch_tests.CommunityLaunchTests, 'launch_gate', gate_node5)):
            super().setUp()

    def test_profile_cannot_be_swapped_to_legacy(self):
        self.plan['community_profile'] = launch.DEFAULT_PROFILE
        with self.assertRaisesRegex(ValueError, 'exact_plan_agent_slot'):
            self.validate()

    def test_capacity_cannot_be_replaced_with_named_donor_release(self):
        self.config['r153_release_kind'] = 'retirement'
        with self.assertRaisesRegex(ValueError, 'preserved_exact_retirement'):
            self.validate()

    def test_node5_lease_wall_cannot_change_at_execution(self):
        self.plan['hard_end_unix'] += 1
        with self.assertRaisesRegex(ValueError, 'capacity_release_exact_node5_lease'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
