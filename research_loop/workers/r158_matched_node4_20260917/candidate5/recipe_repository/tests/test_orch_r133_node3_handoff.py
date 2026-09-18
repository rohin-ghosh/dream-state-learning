"""CPU-only node3 containment, ownership and exact saved-state tests."""

from copy import deepcopy


import json


import os


from pathlib import Path


import signal


import struct


import tempfile


import time


from types import SimpleNamespace


import unittest


from unittest.mock import Mock, patch


from gpu import orch_r133_node3_handoff as launcher


class ContainmentProbeTests(unittest.TestCase):
    def command(self, **overrides):
        arguments = dict(physical=1, minor=1, uid=1395, gid=1395,
            unit='orch-r136-nvml-'+'a'*32, source='/tmp/frozen-source')
        return launcher.containment_probe_command(**dict(arguments, **overrides))

    def test_explicit_device_not_physical_index(self):
        command = self.command()
        self.assertIn('--property=DevicePolicy=strict', command)
        self.assertIn('--property=DeviceAllow=/dev/nvidia1 rw', command)
        self.assertNotIn('--property=DeviceAllow=/dev/nvidia2 rw', command)
        self.assertIn('CUDA_VISIBLE_DEVICES='+launcher.DEVICES[1], command)
        self.assertIn('--property=User=1395', command)
        self.assertIn('--property=NoNewPrivileges=yes', command)
        self.assertIn('--property=RuntimeMaxSec=30', command)
        self.assertEqual(command[-1], 'probe-nvml')

    def test_reject_ambiguous_or_privileged_probe(self):
        for mutation in (dict(physical=True), dict(physical=8), dict(minor=-1),
                dict(minor=True), dict(uid=0), dict(gid=0), dict(unit='existing.service'),
                dict(source='relative'), dict(source='/tmp/../source')):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.command(**mutation)

    def test_probe_uses_NVML_without_CUDA_fallback(self):
        cuda = SimpleNamespace(is_initialized=Mock(return_value=False),
            _device_count_nvml=Mock(return_value=-1), device_count=Mock(),
            init=Mock(), __file__='/tmp/fake-cuda.py')
        torch = SimpleNamespace(cuda=cuda, __version__='mock')
        with patch.dict('sys.modules', torch=torch), \
                patch.object(launcher, 'gpu_descriptors', return_value=[]), \
                patch.object(launcher, 'ref', return_value={'sha256': 'mock'}):
            result = launcher.nvml_discovery_probe()
        self.assertEqual(result['nvml_visible_count'], -1)
        self.assertFalse(result['admission_receipt'])
        cuda.device_count.assert_not_called()
        cuda.init.assert_not_called()

    def test_probe_rejects_already_initialized_CUDA(self):
        cuda = SimpleNamespace(is_initialized=Mock(return_value=True),
            _device_count_nvml=Mock())
        with patch.dict('sys.modules', torch=SimpleNamespace(cuda=cuda)), \
                patch.object(launcher, 'gpu_descriptors', return_value=[]), \
                self.assertRaisesRegex(ValueError, 'probe_must_not_initialize'):
            launcher.nvml_discovery_probe()
        cuda._device_count_nvml.assert_not_called()

    def test_failed_admission_cannot_start_contained_service(self):
        from gpu import orch_r125_continual_guard as guard
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(guard, 'validate', return_value=(dict(attempt_dir=temporary),
                    dict(gpu_uuid=launcher.DEVICES[1]))), \
                patch.object(launcher, 'require_host'), \
                patch.object(launcher, 'scan', return_value=dict(clear=False, scanner_euid=0,
                    blocking_reasons=['open_device_pid:123'])), \
                patch.object(launcher.subprocess, 'run') as running:
            with self.assertRaisesRegex(ValueError, 'unchanged_global_exclusive_admission'):
                launcher.contained_supervise('/tmp/synthetic-config')
            running.assert_not_called()
            self.assertTrue((Path(temporary)/'DISPATCH_ONCE').is_dir())

    def test_foreign_descriptors_rejected_before_any_device_probe(self):
        config = dict(device_containment=dict(uid=os.getuid(), gid=os.getgid(), minor=1, unit='test'))
        plan = dict(gpu_uuid=launcher.DEVICES[1])
        with patch.object(launcher, 'require_host'), \
                patch.object(launcher.os, 'getuid', return_value=1395), \
                patch.object(launcher.os, 'getgid', return_value=1395), \
                patch.object(Path, 'read_text', return_value='0::/system.slice/test.service\n'), \
                patch.object(launcher, 'device_minor', return_value=1), \
                patch.object(launcher, 'gpu_descriptors', return_value=[dict(path='/dev/nvidia0')]), \
                patch.object(launcher.os, 'open') as opening:
            config['device_containment'].update(uid=1395, gid=1395)
            with self.assertRaisesRegex(ValueError, 'no_inherited_GPU_descriptors'):
                launcher.verify_device_containment(config, plan)
            opening.assert_not_called()

    def test_containment_enforces_all_seven_foreign_device_denials(self):
        config = dict(device_containment=dict(uid=1395, gid=1395, minor=1, unit='test'))
        plan = dict(gpu_uuid=launcher.DEVICES[1])
        with patch.object(launcher, 'require_host'), \
                patch.object(launcher.os, 'getuid', return_value=1395), \
                patch.object(launcher.os, 'getgid', return_value=1395), \
                patch.object(Path, 'read_text', return_value='0::/system.slice/test.service\n'), \
                patch.object(launcher, 'device_minor', return_value=1), \
                patch.object(launcher, 'gpu_descriptors', return_value=[]), \
                patch.dict(os.environ, CUDA_VISIBLE_DEVICES=launcher.DEVICES[1]), \
                patch.object(launcher.os, 'open', side_effect=PermissionError) as opening:
            result = launcher.verify_device_containment(config, plan)
        self.assertEqual(result['denied_foreign_minors'], [0, 2, 3, 4, 5, 6, 7])
        self.assertEqual(opening.call_count, 7)


def handoff_request():
    path = '/tmp/old-control/GUARD.json'
    prefix = [str(launcher.PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard']
    actor = dict(pid=103, parent=102, uid=os.getuid(), start_ticks='3',
        cvd=[launcher.DEVICES[1]], argv=prefix+['native', '--config', path])
    timer = dict(pid=102, parent=101, uid=os.getuid(), start_ticks='2',
        cvd=[launcher.DEVICES[1]], argv=['timeout', '--signal=TERM', '--kill-after=5s', '1000s']+actor['argv'])
    supervisor = dict(pid=101, parent=100, uid=os.getuid(), start_ticks='1',
        cvd=[''], argv=prefix+['supervise', '--config', path])
    return dict(old_config=dict(path=path, sha256='old'), actor=actor, timer=timer,
        supervisor=supervisor, wait_seconds=120, new_config='/tmp/new-control/GUARD.json',
        device_probe=dict(path='/tmp/synthetic-probe', sha256='probe'),
        gate=dict(cpu_passed=True, builder_line='2026-09-16 [Builder] test'))


class SameLifeHandoffTests(unittest.TestCase):
    def test_hardlinked_parent_publications_preserved_as_regular_bytes(self):
        import tarfile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inbox = root/'inbox'
            inbox.mkdir()
            message = inbox/'message.json'
            message.write_text('preserved parent publication')
            os.link(message, inbox/'message.partial')
            receipt = launcher.archive_paths([inbox], root/'STATE.tar')
            self.assertEqual(len(receipt['files']), 2)
            with tarfile.open(root/'STATE.tar') as archive:
                self.assertTrue(all(member.isfile() for member in archive))
                for member in archive:
                    self.assertEqual(archive.extractfile(member).read(), message.read_bytes())

    def test_original_CPU_supervisor_may_have_absent_CVD(self):
        request = handoff_request()
        request['supervisor']['cvd'] = []
        plan = dict(physical=1, gpu_uuid=launcher.DEVICES[1])
        config = dict(plan_sha256='plan')
        launch = dict(pid=102, parent_start_ticks='2', guard_sha256='old', plan_sha256='plan')
        launcher.validate_handoff_processes(request, config, plan, launch)

    def test_snapshot_preserves_original_parent_source_paths(self):
        from gpu.orch_r125_stream_journal import StreamJournal
        from organism_v6.orch_r124_train_history import TrainHistory
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root/'original'
            stream = launcher.native.ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
                context_limit=4096, segment_tokens=128, segments_per_sleep=2,
                deadline_unix=1000, model_state_sha256='f'*64)
            with StreamJournal(original, create=True) as journal:
                journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
                (original/'inbox/parent.json').write_text(json.dumps(dict(id='parent', text='Parent input.',
                    split='TRAIN', actor='parent')))
                journal.read_inbox()
                launcher.shutil.copytree(original, root/'snapshot')
                saved = launcher.verify_stream_snapshot(root/'snapshot', original, stream.checkpoint()['sha256'])
                self.assertEqual(saved['document'], stream.checkpoint())
                with self.assertRaisesRegex(ValueError, 'inbox_source_path'):
                    launcher.verify_stream_snapshot(root/'snapshot', root/'different', stream.checkpoint()['sha256'])

    def test_exact_owned_chain(self):
        request = handoff_request()
        config = dict(plan_sha256='plan')
        plan = dict(physical=1, gpu_uuid=launcher.DEVICES[1])
        launch = dict(pid=102, parent_start_ticks='2', guard_sha256='old', plan_sha256='plan')
        launcher.validate_handoff_processes(request, config, plan, launch)
        for name, key, value in [('actor', 'parent', 999), ('actor', 'argv', ['train']),
                ('supervisor', 'cvd', [launcher.DEVICES[1]]), ('timer', 'start_ticks', 'reused'),
                ('timer', 'uid', os.getuid()+1)]:
            candidate = deepcopy(request)
            candidate[name][key] = value
            with self.subTest(name=name, key=key), self.assertRaises(ValueError):
                launcher.validate_handoff_processes(candidate, config, plan, launch)
        for physical in (0, 2, 3, 4, 5, 6, 7, 1.0):
            with self.subTest(physical=physical), self.assertRaisesRegex(ValueError, 'NODE3_CREATIVE1_only'):
                launcher.validate_handoff_processes(request, config,
                    dict(physical=physical, gpu_uuid=launcher.DEVICES.get(physical, 'foreign')), launch)

    def test_wrong_host_never_opens_process_handles(self):
        with patch.object(launcher.socket, 'gethostname', return_value='synthetic-wrong-node'), \
                patch.object(launcher.os, 'pidfd_open') as opening, \
                self.assertRaisesRegex(ValueError, 'exact_node3_host_hash'):
            launcher.handoff_contained(handoff_request(), '/tmp/not-created')
        opening.assert_not_called()


class HandoffOrderingTests(unittest.TestCase):
    def setUp(self):
        from gpu import orch_r125_continual_guard as guard
        from gpu import orch_r131_saved_boundary_handoff as boundary_api
        from gpu import orch_r125_stream_journal as journal_api
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root/'handoff'
        self.events = []
        self.request = handoff_request()
        old_control, new_control = self.root/'old-control', self.root/'new-control'
        old_control.mkdir()
        new_control.mkdir()
        self.plan = dict(physical=1, gpu_uuid=launcher.DEVICES[1], root=str(self.root/'run'),
            hard_end_unix=time.time()+3600, source_root=str(self.root/'source'))
        launcher.write(old_control/'PLAN.json', self.plan)
        self.config = dict(attempt_dir=str(new_control), resume=True)
        old_config = dict(attempt_dir=str(old_control), plan_path=str(old_control/'PLAN.json'),
            plan_sha256=launcher.native.sha(old_control/'PLAN.json'), lease_path=str(old_control/'PLAN.json'))
        launcher.write(old_control/'GUARD.json', old_config)
        self.request['old_config'] = launcher.ref(old_control/'GUARD.json')
        self.request['new_config'] = str(new_control/'GUARD.json')
        launcher.write(new_control/'GUARD.json', self.config)
        for key in ('actor', 'timer', 'supervisor'):
            self.request[key]['argv'][-1] = str(old_control/'GUARD.json')
        launcher.write(old_control/'LAUNCH.json', dict(pid=102, parent_start_ticks='2',
            guard_sha256=self.request['old_config']['sha256'], plan_sha256=old_config['plan_sha256']))
        launcher.write(self.root/'CPU.json', dict(passed=True))
        launcher.write(new_control/'SAME_LIFE.json', dict(cpu_receipt=launcher.ref(self.root/'CPU.json')))
        stream_path = Path(self.plan['root'])/'stream'
        stream_path.mkdir(parents=True)
        self.record_path = stream_path/'boundary.json'
        launcher.write(self.record_path, dict(synthetic=True))
        self.complete_path = Path(self.plan['root'])/'readouts/sleep_000001/COMPLETE.json'
        self.complete_path.parent.mkdir(parents=True)
        launcher.write(self.complete_path, dict(status='COMPLETE', pid=999999999))
        checkpoint_path = Path(self.plan['root'])/'checkpoints/sleep_000001/COMMIT.json'
        checkpoint_path.parent.mkdir(parents=True)
        checkpoint = dict(checkpoint_sha256=dict(adapter='a', optimizer='o', rng='o'),
            optimizer_steps=7, experiment=None)
        launcher.write(checkpoint_path, checkpoint)
        self.boundary = dict(cycle=1, path=str(self.record_path), record_sha256='record',
            state_sha256='state', state={})
        self.stream = SimpleNamespace(experiment=None, deadline_unix=self.plan['hard_end_unix'],
            model_state_sha256=launcher.native.digest(checkpoint['checkpoint_sha256']))
        self.patch(patch.object(launcher, 'require_host'))
        self.patch(patch.object(guard, 'validate', return_value=(self.config, self.plan)))
        self.probe = self.patch(patch.object(launcher, 'verify_probe_receipt'))
        self.patch(patch.object(launcher, 'same_life_plan', return_value=self.plan))
        self.patch(patch.object(boundary_api, 'sleep_boundary', return_value=self.boundary))
        self.patch(patch.object(boundary_api, 'readout_started', return_value=True))
        self.patch(patch.object(launcher.os, 'pidfd_open', side_effect=[10, 11, 12]))
        self.patch(patch.object(launcher.os, 'close'))
        self.patch(patch.object(launcher.preservation, 'same'))
        self.patch(patch.object(launcher.preservation, 'alive', return_value=True))
        self.patch(patch.object(launcher.preservation, 'pause',
            side_effect=lambda process, descriptor: self.events.append(('pause', descriptor))))
        self.signalling = self.patch(patch.object(launcher.signal, 'pidfd_send_signal',
            side_effect=lambda descriptor, signum: self.events.append(('signal', signum))))
        self.patch(patch.object(launcher.select, 'select', return_value=([10], [], [])))
        self.patch(patch.object(launcher.native.ContinualStream, 'restore', return_value=self.stream))
        self.patch(patch.object(launcher.native, 'verify_experiment_resume'))
        self.patch(patch.object(launcher.native.NativeChild, 'verify_checkpoint'))
        self.archive = self.patch(patch.object(launcher, 'archive_paths',
            side_effect=lambda paths, output: self.events.append(('archive_verified', None)) or dict(files={})))
        self.verification = self.patch(patch.object(launcher, 'verify_stream_snapshot'))
        journal = self.patch(patch.object(journal_api, 'StreamJournal'))
        journal.return_value.__enter__.return_value.latest_checkpoint.return_value = dict(expected_sha256='state')
        self.spawn = self.patch(patch.object(launcher.subprocess, 'Popen', return_value=SimpleNamespace(pid=201)))

    def patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def test_archive_and_readout_complete_before_any_TERM(self):
        result = launcher.handoff_contained(self.request, self.output)
        self.assertEqual(result['status'], 'HANDOFF_DISPATCHED_NOT_LOADED')
        self.assertFalse(result['reset'])
        self.assertLess(self.events.index(('archive_verified', None)), self.events.index(('signal', signal.SIGTERM)))
        self.assertTrue((self.output/'OLD_STOPPED.json').exists())
        self.spawn.assert_called_once()
        self.assertIn('contained-supervise', self.spawn.call_args.args[0])
        self.assertNotIn(('signal', signal.SIGKILL), self.events)

    def test_failed_device_probe_never_pauses_or_stops(self):
        self.probe.side_effect = ValueError('probe_all_foreign_denied')
        with self.assertRaisesRegex(ValueError, 'probe_all_foreign_denied'):
            launcher.handoff_contained(self.request, self.output)
        self.assertEqual(self.events, [])
        self.spawn.assert_not_called()

    def test_archive_failure_resumes_paused_chain_without_TERM(self):
        self.archive.side_effect = ValueError('archive_failure')
        with self.assertRaisesRegex(ValueError, 'archive_failure'):
            launcher.handoff_contained(self.request, self.output)
        self.assertNotIn(('signal', signal.SIGTERM), self.events)
        self.assertEqual(self.events.count(('signal', signal.SIGCONT)), 3)
        self.spawn.assert_not_called()
        self.assertFalse((self.output/'OLD_STOPPED.json').exists())

    def test_failed_readout_never_archives_or_stops(self):
        self.complete_path.chmod(0o600)
        self.complete_path.write_text(json.dumps(dict(status='FAILED', pid=999999999)))
        with self.assertRaisesRegex(ValueError, 'finished_fresh_readout'):
            launcher.handoff_contained(self.request, self.output)
        self.archive.assert_not_called()
        self.assertNotIn(('signal', signal.SIGTERM), self.events)
        self.assertEqual(self.events.count(('signal', signal.SIGCONT)), 3)
        self.spawn.assert_not_called()

    def test_checkpoint_mismatch_never_stops(self):
        self.stream.model_state_sha256 = 'wrong'
        with self.assertRaisesRegex(ValueError, 'exact_saved_model_RNG'):
            launcher.handoff_contained(self.request, self.output)
        self.archive.assert_not_called()
        self.assertNotIn(('signal', signal.SIGTERM), self.events)
        self.spawn.assert_not_called()

    def test_invalid_full_journal_chain_never_stops(self):
        self.verification.side_effect = ValueError('invalid_journal')
        with self.assertRaisesRegex(ValueError, 'invalid_journal'):
            launcher.handoff_contained(self.request, self.output)
        self.assertNotIn(('signal', signal.SIGTERM), self.events)
        self.spawn.assert_not_called()
