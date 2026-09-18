"""CPU-only regressions for the exact NODE4 two-slot outer policy."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import slot_policy as policy


NOW = 1789671600


def config_for(physical=2, mode='probe'):
    device, minor, owner = policy.DEVICES[physical]
    config = dict(schema='R177_NODE4_STRICT_SLOT_V1', physical=physical, mode=mode,
        gpu_uuid=device, minor=minor, owner=owner, uid=2524, gid=2524,
        host_sha256=policy.HOST_SHA, hard_end_unix=policy.HARD_END,
        lease=dict(path=str(policy.LEASE), sha256=policy.LEASE_SHA), seconds=180,
        created_unix=NOW, end_unix=NOW + 180, unit='orch-r177-slot' + str(physical) + '-' + 'a' * 32,
        attempt=str(policy.BUNDLE / 'attempts' / 'synthetic'), bundle={'synthetic': True})
    if mode == 'launch':
        root = policy.ROOTS[physical]
        entry = root / 'owned.py'
        config.update(workload_root=str(root), pythonpath=str(root), entrypoint=str(entry),
            command=[policy.PYTHON, '-B', str(entry), 'train'], workload_python_files={'owned.py': 'synthetic'})
    return config


class SlotPolicyTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch.object(policy.time, 'time', return_value=NOW + 1)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def test_two_exact_slots(self):
        for physical in (2, 5):
            self.assertEqual(policy.validate_scope(config_for(physical))['physical'], physical)

    def test_every_other_slot_and_bool_rejected(self):
        for physical in (0, 1, 3, 4, 6, 7, True, '2', 2.0):
            with self.subTest(physical=physical):
                config = config_for()
                config['physical'] = physical
                with self.assertRaises(ValueError):
                    policy.validate_scope(config)

    def test_exact_bindings_rejected_if_changed(self):
        for key, value in [('gpu_uuid', policy.DEVICES[5][0]), ('minor', 2), ('owner', 'Main'),
                           ('uid', 0), ('gid', 0), ('host_sha256', 'wrong'), ('hard_end_unix', policy.HARD_END + 1),
                           ('unit', 'orch-r177-slot5-' + 'a'*32), ('unit', '../foreign'), ('seconds', 0),
                           ('seconds', 8001), ('seconds', True), ('mode', 'shell'), ('created_unix', float('nan')),
                           ('end_unix', float('inf')), ('end_unix', NOW), ('end_unix', NOW+181),
                           ('attempt', str(policy.BASE / 'foreign'))]:
            with self.subTest(key=key, value=value):
                config = config_for()
                config[key] = value
                with self.assertRaises(ValueError):
                    policy.validate_scope(config)

    def test_launch_command_not_shell_or_other_owner(self):
        config = config_for(mode='launch')
        policy.validate_scope(config)
        for key, value in [('command', ['bash', '-c', 'echo nope']),
                           ('entrypoint', str(policy.ROOTS[5] / 'owned.py')),
                           ('pythonpath', '/tmp'), ('workload_root', str(policy.ROOTS[5])),
                           ('workload_python_files', {})]:
            with self.subTest(key=key):
                changed = deepcopy(config)
                changed[key] = value
                with self.assertRaises(ValueError):
                    policy.validate_scope(changed)

    def test_policy_contains_only_selected_minor(self):
        for physical in (2, 5):
            config = config_for(physical)
            command = policy.device_containment_command(config, '/tmp/config.json')
            self.assertIn('--property=DevicePolicy=strict', command)
            self.assertIn('--property=DeviceAllow=', command)
            self.assertIn('--property=NoNewPrivileges=yes', command)
            self.assertIn('--property=CapabilityBoundingSet=', command)
            self.assertIn('--property=AmbientCapabilities=', command)
            self.assertIn('--property=ProtectControlGroups=yes', command)
            self.assertIn('--property=User=2524', command)
            self.assertIn('--property=Group=2524', command)
            self.assertIn('--property=RuntimeMaxSec=179', command)
            self.assertIn('CUDA_VISIBLE_DEVICES=' + config['gpu_uuid'], command)
            self.assertIn('/usr/bin/env', command)
            self.assertIn('-i', command)
            for minor in range(8):
                self.assertEqual('--property=DeviceAllow=/dev/nvidia' + str(minor) + ' rw' in command,
                                 minor == config['minor'])
            self.assertNotIn('PYTORCH_CUDA_ALLOC_CONF', ' '.join(command))

    def test_service_time_expired(self):
        config = config_for()
        with patch.object(policy.time, 'time', return_value=NOW+178):
            with self.assertRaises(ValueError):
                policy.device_containment_command(config, '/tmp/config.json')

    def test_symlink_and_parent_paths_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path = root / 'real.py'
            path.write_text('pass\n')
            (root / 'alias.py').symlink_to(path)
            for invalid in (root / 'alias.py', root / '..' / root.name / 'real.py', Path('relative.py')):
                with self.assertRaises(ValueError):
                    policy.scoped_path(invalid, root)
            with self.assertRaises(ValueError):
                policy.source_pins(root)

    def test_source_inventory_add_change_remove(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path = root / 'owned.py'
            path.write_text('first\n')
            original = policy.source_pins(root)
            path.write_text('second\n')
            self.assertNotEqual(original, policy.source_pins(root))
            path.unlink()
            self.assertNotEqual(original, policy.source_pins(root))
            (root / 'another.py').write_text('first\n')
            self.assertNotEqual(original, policy.source_pins(root))

    def test_reference_immutable_and_write_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'proof.json'
            policy.write(path, {'status': 'PASS'})
            proof = policy.reference(path)
            self.assertEqual(policy.bound(proof), {'status': 'PASS'})
            with self.assertRaises(FileExistsError):
                policy.write(path, {'status': 'changed'})
            path.write_text('{}')
            with self.assertRaises(ValueError):
                policy.bound(proof)

    def clear_report(self):
        return dict(scanner_euid=0, clear=True, blocking_reasons=[], host_sha256=policy.HOST_SHA,
                    device_minor=1, gpu=dict(index=2, uuid=policy.DEVICES[2][0]))

    def test_original_scan_must_be_clear_no_filtering(self):
        config, report = config_for(), self.clear_report()
        policy.require_clear(report, config)
        for change in ({'clear': False}, {'blocking_reasons': ['process_identity_drift:42']},
                       {'blocking_reasons': ['unknown_process_visibility:42']}, {'scanner_euid': 2524},
                       {'device_minor': 6}, {'host_sha256': 'wrong'},
                       {'gpu': dict(index=5, uuid=policy.DEVICES[5][0])}):
            with self.subTest(change=change):
                changed = dict(report, **change)
                original = deepcopy(changed)
                with self.assertRaises(ValueError):
                    policy.require_clear(changed, config)
                self.assertEqual(changed, original)

    def probe_mocks(self, config, foreign_allowed=None, foreign_missing=None):
        original_read = Path.read_text
        def read_text(path, *arguments, **keywords):
            if str(path) == '/proc/self/cgroup':
                return '0::/system.slice/' + config['unit'] + '.service\n'
            if str(path) == '/proc/self/status':
                return 'NoNewPrivs:\t1\nCapEff:\t0\nCapPrm:\t0\nCapBnd:\t0\nCapAmb:\t0\n'
            if str(path) == '/proc/sys/kernel/random/boot_id':
                return 'synthetic-boot\n'
            return original_read(path, *arguments, **keywords)
        def open_device(path, flags):
            minor = int(str(path).split('nvidia')[1])
            if minor == foreign_missing:
                raise FileNotFoundError(path)
            if minor in (config['minor'], foreign_allowed):
                return 100 + minor
            raise PermissionError(path)
        patches = [patch.object(policy, 'require_host_wall'), patch.object(Path, 'read_text', read_text),
                   patch.object(policy.os, 'getuid', return_value=2524),
                   patch.object(policy.os, 'geteuid', return_value=2524),
                   patch.object(policy.os, 'getgid', return_value=2524),
                   patch.object(policy.os, 'getegid', return_value=2524),
                   patch.object(policy, 'device_minor', return_value=config['minor']),
                   patch.object(policy, 'inherited_gpu_descriptors', return_value=[]),
                   patch.object(policy.os, 'open', side_effect=open_device), patch.object(policy.os, 'close'),
                   patch.object(policy, 'reference', return_value={'synthetic': True}),
                   patch.dict(policy.os.environ, CUDA_VISIBLE_DEVICES=config['gpu_uuid'])]
        for mocked in patches:
            mocked.start()
            self.addCleanup(mocked.stop)

    def test_all_seven_denials_and_target_open(self):
        config = config_for()
        self.probe_mocks(config)
        result = policy.verify_device_containment(config)
        self.assertEqual(result['denied_foreign_minors'], [0, 2, 3, 4, 5, 6, 7])
        self.assertTrue(result['target_open_close'])
        self.assertEqual(result['model_calls'], 0)

    def test_foreign_open_is_fatal(self):
        config = config_for()
        self.probe_mocks(config, foreign_allowed=4)
        with self.assertRaisesRegex(ValueError, 'foreign_minor_accessible'):
            policy.verify_device_containment(config)

    def test_missing_foreign_device_is_not_a_denial(self):
        config = config_for()
        self.probe_mocks(config, foreign_missing=4)
        with self.assertRaises(FileNotFoundError):
            policy.verify_device_containment(config)

    def test_inherited_gpu_fd_is_fatal(self):
        config = config_for()
        self.probe_mocks(config)
        with patch.object(policy, 'inherited_gpu_descriptors', return_value=['/dev/nvidia1']):
            with self.assertRaisesRegex(ValueError, 'inherited'):
                policy.verify_device_containment(config)

    def test_wrong_cvd_and_identity_are_fatal(self):
        config = config_for()
        self.probe_mocks(config)
        with patch.dict(policy.os.environ, CUDA_VISIBLE_DEVICES='2'):
            with self.assertRaises(ValueError):
                policy.verify_device_containment(config)
        with patch.object(policy.os, 'geteuid', return_value=0):
            with self.assertRaises(ValueError):
                policy.verify_device_containment(config)

    def test_scan_error_preserved_no_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = config_for()
            config['attempt'] = temporary
            result = subprocess.CompletedProcess([], 2, '', 'original failure')
            with patch.object(policy.subprocess, 'run', return_value=result) as runner:
                with self.assertRaises(ValueError):
                    policy.scan_to_receipt('/tmp/config.json', config)
                self.assertEqual(runner.call_count, 1)
            self.assertEqual(policy.read(Path(temporary) / 'SCAN_EXECUTION.json')['stderr'], 'original failure')
            self.assertFalse((Path(temporary) / 'ADMISSION_BINDING.json').exists())

    def test_blocked_scan_preserves_entire_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = config_for()
            config['attempt'] = temporary
            report = dict(self.clear_report(), clear=False, blocking_reasons=['unknown:blocker'], arbitrary=[1, 2])
            result = subprocess.CompletedProcess([], 0, json.dumps(report), '')
            with patch.object(policy.subprocess, 'run', return_value=result) as runner:
                with self.assertRaises(ValueError):
                    policy.scan_to_receipt('/tmp/config.json', config)
                self.assertEqual(runner.call_count, 1)
            self.assertEqual(policy.read(Path(temporary) / 'ORIGINAL_ADMISSION.json'), report)
            self.assertFalse((Path(temporary) / 'ADMISSION_BINDING.json').exists())

    def test_cli_options_follow_action_and_owner_arguments_are_verbatim(self):
        config = config_for()
        with patch.object(policy.sys, 'argv', ['slot_policy.py', 'prepare', '--physical', '2',
                                             '--seconds', '7300', '--', 'train', '--root', 'owner-root']), \
             patch.object(policy, 'prepare', return_value=(Path('/tmp/config.json'), config)) as prepare:
            policy.main()
        self.assertEqual(prepare.call_args.args[0:3], (2, 'launch', 7300))
        self.assertEqual(prepare.call_args.args[6], ['train', '--root', 'owner-root'])


if __name__ == '__main__':
    unittest.main()
