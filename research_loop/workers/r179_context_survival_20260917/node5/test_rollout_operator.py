import ast
from copy import deepcopy
import importlib.util
import json
import re
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


SPEC = importlib.util.spec_from_file_location('node5_operator', Path(__file__).with_name('rollout_operator.py'))
operator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(operator)


class OperatorSafetyTests(unittest.TestCase):
    def test_protected_checks_use_original_prefix_without_dispatch(self):
        fixture = ('def contained(output):\n'
                   "    config, plan, unused_guard = modules(output / 'GUARD.json')\n"
                   "    require(config['allowed'], 'original_protected_check')\n"
                   "    write(output / 'CONTAINMENT_VERIFIED.json', dict(verified=True))\n"
                   "    raise AssertionError('must_not_dispatch_during_check')\n")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'protected_primitives.py').write_text(fixture)
            with patch.object(operator, '__file__', str(root / 'rollout_operator.py')):
                self.assertEqual(operator.unchanged_containment_check({'allowed': True}, {'physical': 6}),
                                 {'verified': True})
                with self.assertRaisesRegex(ValueError, 'original_protected_check'):
                    operator.unchanged_containment_check({'allowed': False}, {'physical': 2})
            (root / 'protected_primitives.py').write_text(fixture.replace('unused_guard', 'unknown'))
            with patch.object(operator, '__file__', str(root / 'rollout_operator.py')):
                with self.assertRaisesRegex(ValueError, 'protected_containment_config_load_prefix'):
                    operator.unchanged_containment_check({'allowed': True}, {'physical': 6})

    def test_reader_unit_matches_unchanged_capsule_fullmatch(self):
        first = operator.successor_unit_name(Path('/reader-attempt2'), 7)
        second = operator.successor_unit_name(Path('/reader-attempt2'), 7)
        self.assertIsNotNone(re.fullmatch(r'orch-r136-(nvml|native)-[a-f0-9]{32}', first))
        self.assertNotEqual(first, second)
        self.assertEqual(operator.successor_unit_name(Path('/orch_r179_C1_attempt2'), 0), 'orch-r179-C1-attempt2')

    def test_receiving_preflight_constructs_without_launch(self):
        output = Path('/fresh')
        suffix = [str(operator.PYTHON), '-B', '/fresh/rollout_operator.py', 'contained', '--output', '/fresh']
        with patch.object(operator, 'strict_command', return_value=['strict-prefix', *suffix]) as constructed, \
             patch.object(operator.subprocess, 'run') as launched:
            receipt = operator.command_preflight('saved', 'config', 'plan', output)
            constructed.assert_called_once_with('saved', 'config', 'plan', output)
            launched.assert_not_called()
            self.assertFalse(receipt['launched'])
        with patch.object(operator, 'strict_command', return_value=['unknown']):
            with self.assertRaisesRegex(ValueError, 'exact_successor_entrypoint_preflight'):
                operator.command_preflight(None, {}, {}, output)

    def test_extracted_containment_function_has_its_clock_global(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'containment_primitives.py').write_text(
                'def verify_containment(config, plan):\n    return dict(checked_unix=time.time())\n')
            with patch.object(operator, '__file__', str(root / 'rollout_operator.py')), \
                 patch.object(operator.time, 'time', return_value=1234):
                self.assertEqual(operator.unchanged_containment_check({}, {}), {'checked_unix': 1234})

    def test_systemd_repeated_device_allow_properties_are_all_preserved(self):
        values = operator.parse_properties('DevicePolicy=strict\nDeviceAllow=/dev/nvidia1 rw\n'
                                           'DeviceAllow=/dev/nvidiactl rw\nDeviceAllow=/dev/nvidia-uvm rw\n')
        self.assertEqual(values['DeviceAllow'].splitlines(), ['/dev/nvidia1 rw', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw'])
        with self.assertRaisesRegex(ValueError, 'unique_scalar'):
            operator.parse_properties('DevicePolicy=strict\nDevicePolicy=auto\n')

    def test_strict_command_changes_only_external_entrypoint(self):
        output = Path('/fresh')
        prefix = ['sudo', '-n', 'systemd-run', '--property=DevicePolicy=strict', '--property=DeviceAllow=',
                  '--property=DeviceAllow=/dev/nvidia1 rw', '--property=NoNewPrivileges=yes', '--unit=fresh']
        suffix = [str(operator.PYTHON), '-B', '-m', 'saved.module', 'contained-native', '--config', '/fresh/GUARD.json']
        saved = SimpleNamespace(MODULE='saved.module', containment_command=Mock(return_value=prefix + suffix))
        config = {'device_containment': {'minor': 1}}
        original = deepcopy(config)
        result = operator.strict_command(saved, config, {}, output)
        self.assertEqual(result[:len(prefix)], prefix)
        self.assertEqual(result[len(prefix):], [str(operator.PYTHON), '-B', '/fresh/rollout_operator.py',
                                                'contained', '--output', '/fresh'])
        self.assertEqual(config, original)

    def test_unknown_containment_entrypoint_refused(self):
        saved = SimpleNamespace(MODULE='saved.module', containment_command=lambda *args: ['unrecognized'])
        with self.assertRaisesRegex(ValueError, 'unchanged_containment_command_prefix'):
            operator.strict_command(saved, {}, {}, Path('/fresh'))

    def test_original_guard_source_remains_the_validator(self):
        source = Path(operator.__file__).read_text()
        self.assertIn('from gpu.orch_r125_continual_guard import validate', source)
        self.assertIn("'scan', '--config'", source)
        self.assertIn("namespace['verify_containment'](config, plan)", source)

    def test_protected_command_keeps_single_device_and_existing_wall(self):
        output = Path('/fresh')
        plan = dict(physical=6, gpu_uuid='gpu6', hard_end_unix=1000, lease_end_unix=1600)
        config = {'device_containment': {'minor': 6}}
        protected = SimpleNamespace(NEW_WALL=1000, RESOURCE_CEILING=1600, LANES={6: ('pilot', 'gpu6')},
            contained_command=lambda *args: ['strict-prefix', '--action', 'contained', '--output', str(output)])
        with patch.object(operator, 'load_auxiliary', return_value=protected):
            self.assertEqual(operator.strict_command(None, config, plan, output),
                             ['strict-prefix', 'contained', '--output', str(output)])
            with self.assertRaisesRegex(ValueError, 'exact_protected_GPU_and_wall'):
                operator.strict_command(None, config, dict(plan, hard_end_unix=1001), output)

    def test_consumed_wall_needs_actual_matching_historical_receipt(self):
        from hashlib import sha256
        saved = SimpleNamespace(digest=lambda value: sha256(json.dumps(value, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            records = Path(directory) / 'stream/records'
            records.mkdir(parents=True)
            extension = dict(new_deadline_unix=1000)
            plan = dict(root=directory, hard_end_unix=1000, authorized_wall_extension=extension)
            record = dict(document={'authorization': deepcopy(extension)}, index=0, journal_id='fixture',
                          kind='WALL_EXTENDED', previous_sha256='a' * 64, schema='fixture')
            record['sha256'] = saved.digest(record)
            path = records / '00000000000000000000.json'
            path.write_text(json.dumps(record, sort_keys=True, separators=(',', ':')))
            successor = deepcopy(plan)
            result = operator.remove_consumed_wall(saved, plan, successor)
            self.assertEqual(result['path'], str(path))
            self.assertNotIn('authorized_wall_extension', successor)
            self.assertEqual(successor['hard_end_unix'], 1000)
            record['document']['authorization']['new_deadline_unix'] = 999
            path.write_text(json.dumps(record, sort_keys=True, separators=(',', ':')))
            with self.assertRaisesRegex(ValueError, 'recorded_wall_hash'):
                operator.remove_consumed_wall(saved, plan, deepcopy(plan))

    def test_cpu_environment_disables_GPU_and_hosted_fetch(self):
        environment = operator.environment(Path('/source'))
        self.assertEqual(environment['CUDA_VISIBLE_DEVICES'], '')
        self.assertEqual(environment['HF_HUB_OFFLINE'], '1')
        self.assertEqual(environment['TRANSFORMERS_OFFLINE'], '1')
        self.assertEqual(environment['OMP_NUM_THREADS'], '1')

    def test_reader_mount_requires_same_real_inode_not_same_label(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archived, recovered = root / 'archived', root / 'recovered'
            archived.mkdir()
            recovered.mkdir()
            request = dict(logical_root=str(archived), storage_root=str(recovered))
            self.assertFalse(operator.namespace_matches(request))
            self.assertTrue(operator.namespace_matches(dict(request, logical_root=str(recovered))))

    def test_reader_command_retains_bind_and_no_kill_policy(self):
        request = dict(label='repo_reader', storage_root='/recovered/run1', logical_root='/logical/run1')
        capsule = SimpleNamespace(device_containment_command=lambda *args: [
            'sudo', '--property=DevicePolicy=strict', '--property=KillMode=control-group', '/usr/bin/env', '-i', 'payload'])
        plan = dict(physical=7, gpu_uuid='reader-gpu', source_root='/new/source', hard_end_unix=2000)
        config = dict(device_containment=dict(minor=7, uid=2524, gid=2524, unit='reader-unit'))
        with patch.object(operator, 'read', return_value=request), \
             patch.object(operator, 'load_auxiliary', return_value=capsule), \
             patch.object(operator.time, 'time', return_value=1000):
            command = operator.strict_command(None, config, plan, Path('/fresh'))
        self.assertIn('--property=DevicePolicy=strict', command)
        self.assertIn('--property=BindPaths=/recovered/run1:/logical/run1', command)
        self.assertIn('--property=SendSIGKILL=no', command)
        self.assertIn('--property=KillMode=process', command)
        self.assertNotIn('--property=KillMode=control-group', command)

    def test_receipts_are_exclusive_and_frozen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            operator.write(path, {'passed': True})
            self.assertEqual(path.stat().st_mode & 0o222, 0)
            with self.assertRaises(FileExistsError):
                operator.write(path, {'passed': False})

    def test_no_group_or_unbound_signals(self):
        tree = ast.parse(Path(operator.__file__).read_text())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and node.func.attr == 'pidfd_send_signal']
        self.assertEqual(len(calls), 2)
        self.assertEqual({ast.unparse(node.args[1]) for node in calls}, {'signal.SIGTERM', 'signal.SIGCONT'})
        self.assertTrue(all(ast.unparse(node.args[0]) == "descriptors['actor']" for node in calls))
        self.assertNotIn('killpg', Path(operator.__file__).read_text())

    def test_owner_mismatch_cannot_reach_signal_or_lock(self):
        saved = SimpleNamespace()
        request = {'label': 'C2'}
        with patch.object(operator, 'validate_successor', return_value=(saved, {}, {})), \
             patch.object(operator, 'old_inputs', return_value=(request, {}, {})), \
             patch.object(operator, 'read', return_value={'pair': {'actor': 'expected'}}), \
             patch.object(operator, 'owner_pair', return_value={'actor': 'different'}), \
             patch.object(operator.os, 'open') as opened, \
             patch.object(operator.signal, 'pidfd_send_signal') as signaled:
            with self.assertRaisesRegex(ValueError, 'exact_ready_process_tree'):
                operator.execute(Path('/fresh'), 60)
            opened.assert_not_called()
            signaled.assert_not_called()

    def test_no_successor_dispatch_without_recorded_retirement(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(operator, 'validate_successor', return_value=(None, {}, {})), \
                 patch.object(operator.subprocess, 'check_output') as scanned:
                with self.assertRaisesRegex(ValueError, 'recorded_exact_owner_retirement'):
                    operator.supervise(Path(directory))
                scanned.assert_not_called()

    def test_failed_CPU_proof_never_appears_passed(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            operator.write(output / 'INPUT.json', {'plan': {'source_root': '/original'}})
            result = SimpleNamespace(returncode=1, stdout='', stderr='fixture failure')
            with patch.object(operator.subprocess, 'run', return_value=result):
                with self.assertRaisesRegex(ValueError, 'receiving_actual_source_CPU_failed'):
                    operator.cpu_proof(output, {'fixture': True}, 'TEST')
            self.assertFalse((output / 'TEST_CPU.json').exists())


if __name__ == '__main__':
    unittest.main()
