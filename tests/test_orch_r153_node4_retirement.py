from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r153_node4_retirement as retirement


def fixture(physical):
    target = retirement.TARGETS[physical]
    config = dict(hard_end_unix=9999999999, plan_sha256='plan', attempt_dir=str(Path(target['config']).parent),
                  resume=True, source_pins={'native': target['native_sha']})
    if physical in (6, 7):
        config['device_containment'] = dict(unit='unit', minor={6: 5, 7: 4}[physical], uid=2524, gid=2524)
    plan = dict(physical=physical, gpu_uuid=target['uuid'], root=target['root'],
                source_root=target['source'], hard_end_unix=config['hard_end_unix'])
    timer_pid, supervisor_pid = target['pid'] + 10, target['pid'] + 20
    command = [str(retirement.PYTHON), '-B', '-m', target['entry'], 'native', '--config', target['config']]
    cgroup = '0::/system.slice/unit.service' if physical in (6, 7) else 'user-session'
    common = dict(uid=2524, boot_id='boot', cwd=target['source'], cgroup=cgroup)
    pair = dict(actor=dict(common, pid=target['pid'], start_ticks=target['ticks'], parent=timer_pid,
                           group=timer_pid, argv=command),
                timer=dict(common, pid=timer_pid, start_ticks='timer', parent=supervisor_pid,
                           group=timer_pid, argv=['timeout', '--signal=TERM', '--kill-after=5s', '9999s'] + command),
                supervisor=dict(common, pid=supervisor_pid, start_ticks='supervisor', parent=1,
                                group=supervisor_pid, argv=[str(retirement.PYTHON), '-B', '-m', target['supervisor'],
                                    target['inner'], '--config', target['config']]))
    for name, process in pair.items():
        process['environment'] = ['CUDA_VISIBLE_DEVICES=' + ('' if physical == 5 and name == 'supervisor' else target['uuid'])]
        if physical == 7:
            process['environment'].insert(0, 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')
    launch = dict(pid=timer_pid, parent_start_ticks='timer', guard_sha256=target['guard_sha'],
                  plan_sha256='plan', gpu_uuid=target['uuid'])
    return config, plan, pair, launch


class ScopeTests(unittest.TestCase):
    def test_only_three_named_lives(self):
        self.assertEqual(set(retirement.TARGETS), {5, 6, 7})
        for physical in (5, 6, 7):
            config, plan, unused, launch = fixture(physical)
            retirement.scope(physical, config, plan, retirement.TARGETS[physical]['config'])
        for physical in (0, 1, 2, 3, 4, 8, True, None):
            with self.subTest(physical=physical), self.assertRaisesRegex(ValueError, 'only_Rohin147'):
                retirement.scope(physical, {}, {}, '')

    def test_wrong_root_uuid_source_config_or_topology_refused(self):
        for key in ('root', 'gpu_uuid', 'source_root', 'physical'):
            config, plan, unused, launch = fixture(7)
            plan[key] = 'other'
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'exact_named_life'):
                retirement.scope(7, config, plan, retirement.TARGETS[7]['config'])
        config, plan, unused, launch = fixture(7)
        config.pop('device_containment')
        with self.assertRaisesRegex(ValueError, 'unchanged_original_topology'):
            retirement.scope(7, config, plan, retirement.TARGETS[7]['config'])

    def test_bound_original_process_chains_and_allocator(self):
        with patch.object(os, 'getuid', return_value=2524):
            for physical in (5, 6, 7):
                config, plan, pair, launch = fixture(physical)
                retirement.validate_pair(pair, physical, config, plan, launch)

    def test_PID_reuse_foreign_parent_and_allocator_drift_refused(self):
        for mutation in ('pid', 'ticks', 'parent', 'allocator', 'owner', 'group', 'launch'):
            config, plan, pair, launch = fixture(7)
            if mutation == 'pid': pair['actor']['pid'] += 1
            if mutation == 'ticks': pair['actor']['start_ticks'] += '0'
            if mutation == 'parent': pair['timer']['parent'] += 1
            if mutation == 'allocator': pair['actor']['environment'].pop(0)
            if mutation == 'owner': pair['actor']['uid'] = 0
            if mutation == 'group': pair['actor']['group'] += 1
            if mutation == 'launch': launch['guard_sha256'] = 'wrong'
            with self.subTest(mutation=mutation), patch.object(os, 'getuid', return_value=2524):
                with self.assertRaises(ValueError):
                    retirement.validate_pair(pair, 7, config, plan, launch)


class PreservationTests(unittest.TestCase):
    def test_exact_copy_and_immutable_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            (source / 'adapter.bin').write_bytes(b'adapter')
            (source / 'optimizer_rng.pt').write_bytes(b'AdamW Python CPU CUDA')
            inventory = retirement.copy_verified(source, root / 'copy')
            self.assertEqual(inventory, retirement.files(source))
            retirement.write(root / 'receipt.json', {'saved': inventory})
            with self.assertRaises(FileExistsError):
                retirement.write(root / 'receipt.json', {})
            self.assertEqual(json.loads((root / 'receipt.json').read_text())['saved'], inventory)

    def test_preservation_symlinks_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'file').write_text('state')
            (root / 'link').symlink_to(root / 'file')
            with self.assertRaisesRegex(ValueError, 'no_evidence_symlinks'):
                retirement.files(root)

    def test_R152_saved31_rollback_refused(self):
        core = SimpleNamespace(saved_evidence=Mock(return_value={'cycle': 31, 'optimizer_steps': 1922}))
        with self.assertRaisesRegex(ValueError, 'preserve_R152_success_never_revert31'):
            retirement.saved_evidence(core, 7, {}, {}, None)
        core.saved_evidence.return_value = {'cycle': 33, 'optimizer_steps': 2100}
        self.assertEqual(retirement.saved_evidence(core, 7, {}, {}, None)['cycle'], 33)

    def test_resume_plan_changes_only_attempt_resume_and_unique_unit(self):
        config, unused, pair, launch = fixture(7)
        original = deepcopy(config)
        updated = retirement.resume_config(config, Path('/future/resume'))
        normalized = deepcopy(updated)
        normalized['attempt_dir'] = original['attempt_dir']
        normalized['resume'] = original['resume']
        normalized['device_containment']['unit'] = original['device_containment']['unit']
        self.assertEqual(normalized, original)
        self.assertEqual(config, original)
        self.assertTrue(updated['device_containment']['unit'].startswith('orch-r136-native-'))

    def test_resume_never_implicit(self):
        with self.assertRaisesRegex(ValueError, 'explicit_CPU_resume_operator'):
            retirement.resume('/unused')


class SignalTests(unittest.TestCase):
    def test_clearance_runs_in_original_source_not_staging_package(self):
        config, plan, unused, launch = fixture(6)
        report = dict(clear=True, scanner_euid=0, blocking_reasons=[], gpu={'uuid': retirement.TARGETS[6]['uuid']})
        with tempfile.TemporaryDirectory() as directory, patch.object(retirement.subprocess, 'check_output',
                return_value=json.dumps(report)) as scanner:
            retirement.clearance(6, config, plan, Path(directory))
            self.assertEqual(scanner.call_args.kwargs['cwd'], retirement.TARGETS[6]['source'])
            self.assertTrue((Path(directory) / 'GPU_CLEAR.json').exists())

    def test_only_exact_pidfd_TERM_CONT_not_group_or_KILL(self):
        expected = {'pid': 12, 'start_ticks': '123'}
        core = SimpleNamespace(identity=Mock(return_value=expected))
        with patch.object(signal, 'pidfd_send_signal') as send:
            retirement.retirement_signal(core, expected, 99, signal.SIGTERM)
            send.assert_called_once_with(99, signal.SIGTERM)
        with self.assertRaisesRegex(ValueError, 'only_TERM_CONT'):
            retirement.retirement_signal(core, expected, 99, signal.SIGKILL)

    def test_identity_drift_causes_no_signal(self):
        core = SimpleNamespace(identity=Mock(return_value={'pid': 12, 'start_ticks': '456'}))
        with patch.object(signal, 'pidfd_send_signal') as send:
            with self.assertRaisesRegex(ValueError, 'exact_identity_before'):
                retirement.retirement_signal(core, {'pid': 12, 'start_ticks': '123'}, 99, signal.SIGTERM)
            send.assert_not_called()

    def test_bounded_wait_refused_before_setup(self):
        for value in (0, 7201, True, -1):
            with self.subTest(value=value), patch.object(retirement, 'setup') as setup:
                with self.assertRaisesRegex(ValueError, 'bounded_retirement_wait'):
                    retirement.retire(7, '/unused', '/unused', value)
                setup.assert_not_called()

    def test_exact_proven_primitive_hash(self):
        self.assertEqual(retirement.sha(Path(retirement.__file__).with_name(retirement.PRIMITIVE)),
                         retirement.PRIMITIVE_SHA)
        core = retirement.primitives()
        self.assertTrue(callable(core.pause_exact))
        self.assertTrue(callable(core.verify_snapshot))


if __name__ == '__main__':
    unittest.main()
