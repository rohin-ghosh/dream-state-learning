"""CPU-only A100 ownership, boundary and immutable-stage checks."""

from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import struct
import tempfile
import tarfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r136_node1_launcher as launcher


class ContainmentProbeTests(unittest.TestCase):
    def command(self, **overrides):
        arguments = dict(physical=2, minor=1, uid=1395, gid=1395,
            unit='orch-r136-nvml-'+'a'*32, source='/tmp/frozen-source')
        return launcher.containment_probe_command(**dict(arguments, **overrides))

    def test_explicit_device_not_physical_index(self):
        command = self.command()
        self.assertIn('--property=DevicePolicy=strict', command)
        self.assertIn('--property=DeviceAllow=/dev/nvidia1 rw', command)
        self.assertNotIn('--property=DeviceAllow=/dev/nvidia2 rw', command)
        self.assertIn('CUDA_VISIBLE_DEVICES='+launcher.DEVICES[2], command)
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
                    dict(gpu_uuid=launcher.DEVICES[2]))), \
                patch.object(launcher.socket, 'gethostname', return_value='[REDACTED_HOST]'), \
                patch.object(launcher, 'scan', return_value=dict(clear=False, scanner_euid=0,
                    blocking_reasons=['open_device_pid:123'])), \
                patch.object(launcher.subprocess, 'run') as running:
            with self.assertRaisesRegex(ValueError, 'unchanged_global_exclusive_admission'):
                launcher.contained_supervise('/tmp/synthetic-config')
            running.assert_not_called()
            self.assertTrue((Path(temporary)/'DISPATCH_ONCE').is_dir())

    def test_foreign_descriptors_rejected_before_any_device_probe(self):
        config = dict(device_containment=dict(uid=os.getuid(), gid=os.getgid(), minor=1, unit='test'))
        plan = dict(gpu_uuid=launcher.DEVICES[2])
        with patch.object(launcher.socket, 'gethostname', return_value='[REDACTED_HOST]'), \
                patch.object(launcher.os, 'getuid', return_value=1395), \
                patch.object(launcher.os, 'getgid', return_value=1395), \
                patch.object(Path, 'read_text', return_value='0::/system.slice/test.service\n'), \
                patch.object(launcher, 'a100_device_minor', return_value=1), \
                patch.object(launcher, 'gpu_descriptors', return_value=[dict(path='/dev/nvidia0')]), \
                patch.object(launcher.os, 'open') as opening:
            config['device_containment'].update(uid=1395, gid=1395)
            with self.assertRaisesRegex(ValueError, 'no_inherited_GPU_descriptors'):
                launcher.verify_device_containment(config, plan)
            opening.assert_not_called()

    def test_containment_enforces_all_seven_foreign_device_denials(self):
        config = dict(device_containment=dict(uid=1395, gid=1395, minor=1, unit='test'))
        plan = dict(gpu_uuid=launcher.DEVICES[2])
        with patch.object(launcher.socket, 'gethostname', return_value='[REDACTED_HOST]'), \
                patch.object(launcher.os, 'getuid', return_value=1395), \
                patch.object(launcher.os, 'getgid', return_value=1395), \
                patch.object(Path, 'read_text', return_value='0::/system.slice/test.service\n'), \
                patch.object(launcher, 'a100_device_minor', return_value=1), \
                patch.object(launcher, 'gpu_descriptors', return_value=[]), \
                patch.dict(os.environ, CUDA_VISIBLE_DEVICES=launcher.DEVICES[2]), \
                patch.object(launcher.os, 'open', side_effect=PermissionError) as opening:
            result = launcher.verify_device_containment(config, plan)
        self.assertEqual(result['denied_foreign_minors'], [0, 2, 3, 4, 5, 6, 7])
        self.assertEqual(opening.call_count, 7)


def handoff_request():
    path = '/tmp/old-control/GUARD.json'
    prefix = [str(launcher.PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard']
    actor = dict(pid=103, parent=102, uid=os.getuid(), start_ticks='3',
        cvd=[launcher.DEVICES[2]], argv=prefix+['native', '--config', path])
    timer = dict(pid=102, parent=101, uid=os.getuid(), start_ticks='2',
        cvd=[launcher.DEVICES[2]], argv=['timeout', '--signal=TERM', '--kill-after=5s', '1000s']+actor['argv'])
    supervisor = dict(pid=101, parent=100, uid=os.getuid(), start_ticks='1',
        cvd=[''], argv=prefix+['supervise', '--config', path])
    return dict(old_config=dict(path=path, sha256='old'), actor=actor, timer=timer,
        supervisor=supervisor, wait_seconds=120, new_config='/tmp/new-control/GUARD.json',
        gate=dict(cpu_passed=True, builder_line='2026-09-16 [Builder] test'))


class SameLifeHandoffTests(unittest.TestCase):
    def test_archive_keeps_hardlinked_paths_as_verified_regular_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root/'source'
            source.mkdir()
            (source/'first').write_bytes(b'unchanged source bytes')
            os.link(source/'first', source/'second')
            result = launcher.archive_same_life([source], root/'saved.tar')
            self.assertTrue(result['hardlinks_preserved_as_regular_bytes'])
            self.assertEqual(len(result['files']), 2)
            with tarfile.open(root/'saved.tar') as archive:
                self.assertTrue(all(entry.isfile() for entry in archive.getmembers()))
                self.assertEqual([archive.extractfile(entry).read() for entry in archive.getmembers()],
                    [b'unchanged source bytes']*2)
            (source/'link').symlink_to(source/'first')
            with self.assertRaisesRegex(ValueError, 'same_life_archive_symlink'):
                launcher.archive_same_life([source], root/'rejected.tar')
            self.assertFalse((root/'rejected.tar').exists())

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
        plan = dict(physical=2, gpu_uuid=launcher.DEVICES[2])
        launch = dict(pid=102, parent_start_ticks='2', guard_sha256='old', plan_sha256='plan')
        launcher.validate_handoff_processes(request, config, plan, launch)
        for name, key, value in [('actor', 'parent', 999), ('actor', 'argv', ['train']),
                ('supervisor', 'cvd', [launcher.DEVICES[2]]), ('timer', 'start_ticks', 'reused'),
                ('timer', 'uid', os.getuid()+1)]:
            candidate = deepcopy(request)
            candidate[name][key] = value
            with self.subTest(name=name, key=key), self.assertRaises(ValueError):
                launcher.validate_handoff_processes(candidate, config, plan, launch)
        for physical in (0, 1, 3, 4, 5, 6, 7):
            with self.subTest(physical=physical), self.assertRaisesRegex(ValueError, 'A1002_only'):
                launcher.validate_handoff_processes(request, config,
                    dict(physical=physical, gpu_uuid=launcher.DEVICES[physical]), launch)

    def test_wrong_host_never_opens_process_handles(self):
        with patch.object(launcher.socket, 'gethostname', return_value='ovx3'), \
                patch.object(launcher.os, 'pidfd_open') as opening, \
                self.assertRaisesRegex(ValueError, 'A100_host_only'):
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
        self.plan = dict(physical=2, gpu_uuid=launcher.DEVICES[2], root=str(self.root/'run'),
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
        self.patch(patch.object(launcher.socket, 'gethostname', return_value='[REDACTED_HOST]'))
        self.patch(patch.object(guard, 'validate', return_value=(self.config, self.plan)))
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
        self.archive = self.patch(patch.object(launcher, 'archive_same_life',
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


def request(physical=2):
    prefix = [str(launcher.PYTHON), '-B', '-u', str(launcher.GENERATION_ROOT/'orch_r119_l1_generation_resume.py')]
    actor = dict(pid=100, parent=200, uid=os.getuid(), cvd=[launcher.DEVICES[physical]],
        argv=prefix+['generate', '--root', str(launcher.GENERATION_ROOT), '--index', str(physical), '--segment', '1'])
    supervisor = dict(pid=200, uid=os.getuid(), cvd=[''],
        argv=prefix+['supervise', '--root', str(launcher.GENERATION_ROOT), '--index', str(physical)])
    return dict(node='a100', physical=physical, segment=1, actor=actor, supervisor=supervisor,
        wait_seconds=30, gate=dict(cpu_passed=True, builder_line='2026-09-16 [Builder] own CPU gate PASS'),
        scan_config='/tmp/synthetic/GUARD.json')


class OwnershipTests(unittest.TestCase):
    def test_only_reviewed_generation_lanes_are_accepted(self):
        for physical in (2, 3, 4):
            launcher.validate_pair(request(physical))
        for physical in (0, 1, 5, 6, 7, True):
            with self.subTest(physical=physical), self.assertRaisesRegex(ValueError, 'generation_lanes_only'):
                launcher.validate_pair(request(physical))

    def test_foreign_nodes_do_not_signal_any_process(self):
        for node in ('ovx2', 'ovx3', 'a40r', 'ovx'):
            candidate = dict(request(), node=node)
            with self.subTest(node=node), patch.object(launcher.os, 'pidfd_open') as opening, \
                    self.assertRaisesRegex(ValueError, 'generation_lanes_only'):
                launcher.retire_generation(candidate, '/tmp/never-created')
            opening.assert_not_called()

    def test_exact_argv_parent_and_gpu_cannot_drift(self):
        for field, value, reason in (
                ('argv', ['train'], 'exact_generation_actor'), ('cvd', ['GPU-other'], 'exact_GPU'),
                ('parent', 999, 'owned_process_pair'), ('uid', os.getuid()+1, 'owned_process_pair')):
            candidate = request()
            candidate['actor'][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, reason):
                launcher.validate_pair(candidate)
        candidate = request()
        candidate['supervisor']['argv'][-1] = '3'
        with self.assertRaisesRegex(ValueError, 'exact_generation_actor'):
            launcher.validate_pair(candidate)

    def test_cpu_gate_and_wait_budget_are_explicit(self):
        for gate in (dict(cpu_passed=False, builder_line='2026-09-16 [Builder]'),
                     dict(cpu_passed=True, builder_line='unlogged')):
            with self.assertRaisesRegex(ValueError, 'dated_own_CPU_gate'):
                launcher.validate_pair(dict(request(), gate=gate))
        for wait in (0, 301):
            with self.assertRaisesRegex(ValueError, 'bounded_retirement_wait'):
                launcher.validate_pair(dict(request(), wait_seconds=wait))

    def test_host_mismatch_fails_before_any_signal(self):
        with patch.object(launcher.socket, 'gethostname', return_value='other'), \
                patch.object(launcher.os, 'pidfd_open') as opening, self.assertRaisesRegex(ValueError, 'A100_host_only'):
            launcher.retire_generation(request(), '/tmp/never-created')
        opening.assert_not_called()

    def test_inotify_accepts_only_completed_cursor_publications(self):
        def event(name, mask):
            payload = name+b'\0'
            return struct.pack('iIII', 1, mask, 0, len(payload))+payload
        self.assertTrue(launcher.boundary_event(event(b'PROGRESS.json', 0x8)))
        self.assertTrue(launcher.boundary_event(event(b'PROGRESS.json', 0x80)))
        self.assertFalse(launcher.boundary_event(event(b'INTENT_12.json', 0x8)))
        self.assertFalse(launcher.boundary_event(event(b'PROGRESS.json', 0x2)))
        self.assertFalse(launcher.boundary_event(b''))
        with self.assertRaisesRegex(ValueError, 'complete_inotify_event'):
            launcher.boundary_event(struct.pack('iIII', 1, 8, 0, 100))

    def test_all_r137_combinations_are_distinct_and_as_requested(self):
        self.assertEqual(len(set(launcher.LANES.values())), 8)
        self.assertEqual([launcher.LANES[index][2] for index in range(8)], [3, 3, 2, 1, 3, 3, 2, 4])
        self.assertEqual(launcher.LANES[2][4], 'free_distillation')
        self.assertEqual(launcher.LANES[0][0], 'frozen_adapter')
        self.assertEqual(launcher.LANES[1][0], 'base_only')


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.source = root/'source'
        (self.source/'gpu').mkdir(parents=True)
        self.startup = self.source/'startup.md'
        self.startup.write_text('Truthful startup. No executor is connected.')
        self.cpu_path = root/'CPU.json'
        self.cpu_path.write_text(json.dumps(dict(passed=True, tests=8, source_pins={})))
        self.output = root/'life/control1'
        self.forks = dict(model_dir=str(root/'model'), hard_deadline_unix=time.time()+3600, lease_end_unix=time.time()+25200)
        self.proof = dict(forks=dict(path='/localhome/local-rohing/FORKS.json', sha256='a'*64))
        self.start_patch(patch.object(launcher.socket, 'gethostname', return_value='[REDACTED_HOST]'))
        self.start_patch(patch.object(launcher, '__file__', str(self.source/'gpu/launcher.py')))
        self.start_patch(patch.object(launcher, 'generation_provenance', return_value=(self.forks, self.proof)))

    def start_patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def stage(self, physical=2):
        return launcher.stage(self.source, self.output, physical, self.startup, self.cpu_path, 'a'*40)

    def test_stage_preserves_original_lease_and_records_not_launched(self):
        result = self.stage()
        self.assertFalse(result['launch_attempted'])
        plan = launcher.native.read(self.output/'PLAN.json')
        self.assertEqual(plan['hard_end_unix'], self.forks['hard_deadline_unix'])
        self.assertEqual(plan['lease_end_unix'], self.forks['lease_end_unix'])
        self.assertEqual(plan['presleep_variant'], 'free_distillation')
        self.assertEqual(plan['seed'], 0)
        self.assertEqual(plan['physical'], 2)
        self.assertEqual((plan['new_presentations'], plan['rehearsal_presentations'], plan['anchor_lambda']), (16, 1, .25))
        self.assertFalse(Path(plan['root']).exists())
        allocation = launcher.native.read(self.output/'ALLOCATION.json')
        self.assertFalse(allocation['current_CPU_gate_pushed'])
        self.assertTrue(allocation['source_overlay_independently_pinned'])
        self.assertEqual(allocation['cpu_receipt_sha256'], launcher.native.sha(self.cpu_path))

    def test_same_life_plan_changes_only_source_paths(self):
        self.stage()
        old_plan = launcher.native.read(self.output/'PLAN.json')
        original = deepcopy(old_plan)
        source = self.source.parent/'new-source'
        source.mkdir()
        (source/'startup.md').write_bytes(self.startup.read_bytes())
        result = launcher.same_life_plan(old_plan, source)
        expected = deepcopy(original)
        expected['source_root'] = str(source)
        expected['startup_context']['path'] = str(source/'startup.md')
        self.assertEqual(result, expected)
        self.assertEqual(old_plan, original)
        self.assertEqual(result['hard_end_unix'], self.forks['hard_deadline_unix'])
        self.assertEqual(result['root'], original['root'])
        self.assertEqual(launcher.native.experiment_binding(result), launcher.native.experiment_binding(original))
        (source/'startup.md').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'identical_startup_bytes'):
            launcher.same_life_plan(old_plan, source)

    def test_stage_contained_resume_preserves_old_source_and_lease(self):
        self.stage()
        source = self.source.parent/'resume-source'
        source.mkdir()
        (source/'startup.md').write_bytes(self.startup.read_bytes())
        output = self.output.parent/'control2'
        old_guard = launcher.native.read(self.output/'GUARD.json')
        with patch.object(launcher, 'a100_device_minor', return_value=1):
            launcher.stage_contained_resume(self.output/'GUARD.json', source, output, self.cpu_path)
        guard = launcher.native.read(output/'GUARD.json')
        self.assertTrue(guard['resume'])
        self.assertEqual(guard['lease_path'], old_guard['lease_path'])
        self.assertEqual(guard['lease_sha256'], old_guard['lease_sha256'])
        self.assertEqual(guard['hard_end_unix'], old_guard['hard_end_unix'])
        self.assertEqual(guard['device_containment']['minor'], 1)
        self.assertFalse(launcher.native.read(output/'SAME_LIFE.json')['reset'])
        self.assertEqual(launcher.native.read(self.output/'GUARD.json'), old_guard)

    def test_controls_are_not_silently_launched_as_learning_children(self):
        for physical in (0, 1):
            with self.assertRaisesRegex(ValueError, 'A100_learning_stage_only'):
                self.stage(physical)

    def test_changed_source_requires_a_new_tested_closure(self):
        (self.source/'gpu/new.py').write_text('changed = True\n')
        with self.assertRaisesRegex(ValueError, 'actual_CPU_tested_closure'):
            self.stage()

    def test_existing_control_evidence_is_not_overwritten(self):
        self.stage()
        before = (self.output/'PLAN.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.stage()
        self.assertEqual((self.output/'PLAN.json').read_bytes(), before)

    def test_existing_life_is_never_reset(self):
        (self.output.parent/'run1').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'new_life_no_reset'):
            self.stage()


class ControlAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.path=self.root/'config.json';self.path.write_text('{}')
        self.scan=self.root/'scan.json'
        self.report=dict(clear=True,scanner_euid=0,blocking_reasons=[],gpu=dict(uuid=launcher.DEVICES[0]))
        self.scan.write_text(json.dumps(self.report))
        self.config=dict(plan_sha256='plan',attempt_dir=str(self.root))
        self.plan=dict(gpu_uuid=launcher.DEVICES[0])
        self.receipt=dict(config_sha256=launcher.native.sha(self.path),plan_sha256='plan',
            admitted_unix=time.time(),scan=launcher.ref(self.scan))

    def test_fresh_bound_privileged_receipt(self):
        launcher.control_admission_receipt(self.config,self.plan,self.receipt,self.path)

    def test_stale_and_future_admission_rejected(self):
        for delta in (-121,5):
            self.receipt['admitted_unix']=time.time()+delta
            with self.subTest(delta=delta),self.assertRaisesRegex(ValueError,'fresh_control_admission'):
                launcher.control_admission_receipt(self.config,self.plan,self.receipt,self.path)

    def test_wrong_plan_and_config_rejected(self):
        for key in ('plan_sha256','config_sha256'):
            receipt=dict(self.receipt);receipt[key]='changed'
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'admitted_exact_plan'):
                launcher.control_admission_receipt(self.config,self.plan,receipt,self.path)

    def test_changed_report_rejected(self):
        self.scan.write_text('{}')
        with self.assertRaisesRegex(ValueError,'admission_bytes'):
            launcher.control_admission_receipt(self.config,self.plan,self.receipt,self.path)

    def test_foreign_fd_blocks_service_creation(self):
        report=dict(self.report,clear=False,blocking_reasons=['open_device_pid:123'])
        with patch.object(launcher,'validate_control_config',return_value=(self.config,dict(self.plan,source_root='/tmp/source'))), \
                patch.object(launcher.subprocess,'check_output',return_value=json.dumps(report)), \
                patch.object(launcher.subprocess,'run') as run, self.assertRaisesRegex(ValueError,'unchanged_control_admission'):
            launcher.control_supervise(self.path)
        run.assert_not_called()

    def test_foreign_fd_blocks_model_initialization(self):
        from gpu import orch_r139_continual_controls as controls
        (self.root/'DISPATCH_ONCE').mkdir();launcher.write(self.root/'ADMITTED.json',self.receipt)
        with patch.object(launcher,'validate_control_config',return_value=(self.config,self.plan)), \
                patch.object(launcher,'verify_device_containment',side_effect=ValueError('foreign_fd')), \
                patch.object(controls,'run') as run,self.assertRaisesRegex(ValueError,'foreign_fd'):
            launcher.control_native(self.path)
        run.assert_not_called()


class ConsumerFrontierTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name);self.stage=self.root/'FULL/segment2'
        self.checkpoint=self.stage/'fit/FULL/checkpoints/000020000';self.checkpoint.mkdir(parents=True)
        self.files={name:('saved '+name).encode() for name in ('optimizer.pt','rank0.pt','rank1.pt','adapter/adapter_model.safetensors')}
        for name,data in self.files.items():
            path=self.checkpoint/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        self.put(self.stage/'BINDING.json',{})
        self.commit=dict(files={name:launcher.native.sha(self.checkpoint/name) for name in self.files},
            metadata=dict(arm='FULL',optimizer_preserved=True,rng_per_rank=True,original_history_unchanged=True,
                update=20000,lifetime=dict(hard_deadline_unix=1790442300),adapter=dict(state_sha256='actual_saved_tensor_hash')))
        self.put(self.checkpoint/'COMMIT.json',self.commit)
        self.put(self.stage/'fit/FULL/segment002/COMPLETE.json',dict(checkpoint=str(self.checkpoint),
            commit_sha256=launcher.native.sha(self.checkpoint/'COMMIT.json'),update=20000))
        readouts={}
        for condition in ('ON','OFF'):
            path=self.stage/f'fit/FULL/segment002/readout/{condition}/COMPLETE.json';self.put(path,{})
            readouts[condition]=launcher.ref(path)
        self.put(self.stage/'PAIRED_COMPLETE.json',dict(checkpoint=str(self.checkpoint),
            binding_sha256=launcher.native.sha(self.stage/'BINDING.json'),readouts=readouts))
        for phase,condition in (('train','None'),('readout','ON'),('readout','OFF')):
            self.put(self.stage/f'{phase}_{condition}_EXIT.json',dict(returncode=0))
            self.put(self.stage/f'{phase}_{condition}_LAUNCH.json',dict(identity=dict(pid=123),
                binding_sha256=launcher.native.sha(self.stage/'BINDING.json')))
        self.original_read=Path.read_text;self.children=''
        def read(path,*args,**kwargs):
            return self.children if str(path)=='/proc/456/task/456/children' else self.original_read(path,*args,**kwargs)
        patch.object(Path,'read_text',read).start()
        self.alive=patch.object(launcher.preservation,'alive',return_value=False).start();self.addCleanup(patch.stopall)

    def put(self,path,document):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(document))

    def frontier(self):
        return launcher.consumer_frontier(self.root,'FULL',dict(pid=456),2)

    def test_exact_adapter_optimizer_and_both_rank_rng(self):
        result=self.frontier();self.assertEqual(result['update'],20000)
        for name in ('optimizer','rank0_rng','rank1_rng'):
            self.assertEqual(launcher.native.sha(result[name]['path']),result[name]['sha256'])

    def test_live_training_child_never_retirable(self):
        self.children='999'
        with self.assertRaisesRegex(ValueError,'active_train_readout_or_scan'):
            self.frontier()

    def test_next_stage_rejects_stale_checkpoint(self):
        (self.root/'FULL/segment3').mkdir()
        with self.assertRaises(FileNotFoundError):self.frontier()

    def test_optimizer_corruption_rejected(self):
        (self.checkpoint/'optimizer.pt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'saved_state_bytes'):self.frontier()

    def test_missing_rng_rejected(self):
        (self.checkpoint/'rank0.pt').unlink()
        with self.assertRaises(FileNotFoundError):self.frontier()

    def test_failed_or_active_readout_rejected(self):
        self.put(self.stage/'readout_OFF_EXIT.json',dict(returncode=1))
        with self.assertRaisesRegex(ValueError,'finished_phases'):self.frontier()
        self.put(self.stage/'readout_OFF_EXIT.json',dict(returncode=0));self.alive.return_value=True
        with self.assertRaisesRegex(ValueError,'phase_process_exited'):self.frontier()

    def retirement(self, archive_error=False):
        events=[]
        request=dict(node='a100',physical=0,arm='FULL',supervisor=dict(pid=456),wait_seconds=30,scan_config='mock')
        def archive(paths,destination,campaign):
            events.append('archive')
            if archive_error:raise ValueError('archive_failed')
            return dict(files={},archive={})
        with patch.object(launcher.socket,'gethostname',return_value='[REDACTED_HOST]'), \
                patch.object(launcher,'CONSUMER_ROOT',self.root), \
                patch.object(launcher,'consumer_provenance'), \
                patch.object(launcher,'validate_control_config',return_value=({},dict(physical=0,
                    gpu_uuid=launcher.DEVICES[0],source_root='/tmp/source'))), \
                patch.object(launcher.preservation,'same'),patch.object(launcher.preservation,'pause'), \
                patch.object(launcher.os,'pidfd_open',return_value=999),patch.object(launcher.os,'close'), \
                patch.object(launcher.signal,'pidfd_send_signal',side_effect=lambda descriptor,signum:events.append(signum)), \
                patch.object(launcher.select,'select',return_value=([999],[],[])), \
                patch.object(launcher,'archive_consumer',side_effect=archive), \
                patch.object(launcher.subprocess,'check_output',return_value=json.dumps(dict(clear=True,
                    scanner_euid=0,blocking_reasons=[],gpu=dict(uuid=launcher.DEVICES[0])))):
            if archive_error:
                with self.assertRaisesRegex(ValueError,'archive_failed'):
                    launcher.retire_consumer(request,self.root/'retirement')
            else:
                result=launcher.retire_consumer(request,self.root/'retirement')
                self.assertEqual(result['status'],'RELEASED')
                self.assertTrue(result['no_training_process_signalled'])
        return events

    def test_consumer_archive_precedes_supervisor_TERM(self):
        events=self.retirement()
        self.assertLess(events.index('archive'),events.index(signal.SIGTERM))
        self.assertEqual(events.count(signal.SIGTERM),1)
        self.assertNotIn(signal.SIGKILL,events)

    def test_consumer_archive_failure_resumes_only_supervisor(self):
        events=self.retirement(archive_error=True)
        self.assertNotIn(signal.SIGTERM,events)
        self.assertEqual(events.count(signal.SIGCONT),1)


class ConsumerArchiveTests(unittest.TestCase):
    def test_bound_dataset_links_are_archived_with_original_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);lane=root/'lane';lane.mkdir();cohort=root/'cohort';cohort.mkdir()
            encoded=cohort/'ENCODED.json';encoded.write_bytes(b'bound train data')
            held=root/'held.json';held.write_bytes(b'fixture-only readout data')
            (lane/'ENCODED.json').symlink_to(encoded);(lane/'held.json').symlink_to(held)
            (lane/'optimizer.pt').write_bytes(b'exact saved optimizer')
            campaign=dict(cohorts=dict(train=dict(path=str(cohort))),held_path=str(held))
            result=launcher.archive_consumer([lane],root/'state.tar',campaign)
            self.assertTrue((lane/'ENCODED.json').is_symlink())
            self.assertEqual(result['original_symlink_targets'][str(lane/'ENCODED.json')],str(encoded))
            with tarfile.open(root/'state.tar') as archive:
                self.assertTrue(all(member.isfile() for member in archive.getmembers()))
                self.assertEqual(len(archive.getmembers()),3)
            unknown=root/'unbound';unknown.write_bytes(b'not authorized by campaign')
            (lane/'unexpected').symlink_to(unknown)
            with self.assertRaisesRegex(ValueError,'only_bound_dataset_links'):
                launcher.archive_consumer([lane],root/'rejected.tar',campaign)
            self.assertFalse((root/'rejected.tar').exists())

    def test_directory_and_symlink_chain_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);lane=root/'lane';lane.mkdir();target=root/'target';target.mkdir()
            (lane/'link').symlink_to(target)
            with self.assertRaisesRegex(ValueError,'only_bound_dataset_links'):
                launcher.archive_consumer([lane],root/'state.tar',dict(cohorts={},held_path=str(target)))


class MathFrontierTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root/'cycle000009'
        self.put('CURSOR.json', dict(next_cycle=10))
        self.put('COUNTERS.json', dict(native=14, parent=2, optimizer_updates=0))
        for kind, count in (('native', 14), ('parent', 2)):
            for index in range(1, count+1):
                self.put(f'reservations/{kind}_{index:08d}.json', {})
        for index in range(1, 15):
            for suffix in ('.json', '.request.json'):
                self.put(f'calls/CALL_{index:08d}{suffix}', {})
        self.put('cycle000009/CARRY.json', dict(actor='child', text='own saved carry'))
        self.put('cycle000009/EXPERIENCE.json', [dict(actor='child', text='own saved carry')])
        self.put('cycle000009/CONTEXT_BOUNDARY.json', dict(cycle=9, episodes=2, weight_sleep=False, optimizer_updates=0))
        self.put('cycle000009/DEV_RESULT.json', dict(status='COMPLETE', returncode=0))
        self.put('cycle000009/DEV_LAUNCH.json', dict(identity=dict(pid=123)))
        self.put('CURSOR.json', dict(next_cycle=10, carry=dict(path=str(self.directory/'CARRY.json'),
            sha256=launcher.native.sha(self.directory/'CARRY.json'))))
        self.alive = patch.object(launcher.preservation, 'alive', return_value=False).start()
        self.addCleanup(patch.stopall)
        self.original_read = Path.read_text
        def read(path, *args, **kwargs):
            if str(path) == '/proc/456/task/456/children':
                return self.children
            return self.original_read(path, *args, **kwargs)
        self.children = ''
        patch.object(Path, 'read_text', read).start()

    def put(self, name, data):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))

    def frontier(self, initial_cycle=9):
        return launcher.math_frontier(self.root, initial_cycle, dict(pid=456))

    def test_exact_saved_carry_and_completed_readout(self):
        result = self.frontier()
        self.assertEqual(result['next_cycle'], 10)
        self.assertEqual(result['carry']['sha256'], launcher.native.sha(self.directory/'CARRY.json'))
        self.assertFalse(result['optimizer_loaded'])

    def test_stale_cursor_rejected(self):
        with self.assertRaisesRegex(ValueError, 'prospective_saved_cursor'):
            self.frontier(10)

    def test_next_train_intent_rejected(self):
        self.put('cycle000010/TRAIN.json', [])
        with self.assertRaisesRegex(ValueError, 'next_cycle_work'):
            self.frontier()

    def test_advanced_counter_rejected(self):
        self.put('COUNTERS.json', dict(native=15, parent=2, optimizer_updates=0))
        with self.assertRaisesRegex(ValueError, 'reservation_beyond_cursor'):
            self.frontier()

    def test_extra_reservation_rejected(self):
        self.put('reservations/native_00000015.json', {})
        with self.assertRaisesRegex(ValueError, 'exact_reservations'):
            self.frontier()

    def test_pending_request_rejected(self):
        (self.root/'calls/CALL_00000014.json').unlink()
        with self.assertRaisesRegex(ValueError, 'pending_or_extra_call'):
            self.frontier()

    def test_wrong_carry_rejected(self):
        self.put('cycle000009/CARRY.json', dict(actor='child', text='changed'))
        with self.assertRaisesRegex(ValueError, 'exact_saved_carry'):
            self.frontier()

    def test_carry_must_match_final_experience(self):
        self.put('cycle000009/EXPERIENCE.json', [dict(actor='parent', text='not own carry')])
        with self.assertRaisesRegex(ValueError, 'final_own_event'):
            self.frontier()

    def test_readout_failure_rejected(self):
        self.put('cycle000009/DEV_RESULT.json', dict(status='FAILED_NO_RETRY', returncode=1))
        with self.assertRaisesRegex(ValueError, 'completed_readout'):
            self.frontier()

    def test_live_readout_rejected(self):
        self.alive.return_value = True
        with self.assertRaisesRegex(ValueError, 'readout_exited'):
            self.frontier()

    def test_any_descendant_rejected(self):
        self.children = '123'
        with self.assertRaisesRegex(ValueError, 'active_descendants'):
            self.frontier()


class ClassroomStartupTests(unittest.TestCase):
    def test_no_distillation_description_matches_actual_runtime(self):
        template = ('You run on one assigned GPU, old.\nThe initial pilot has at most one hour.\n'
            '/localhome/local-rohing/orch_r127_pilot_20260916_attempt1/workspace\n'
            '/localhome/local-rohing/orch_r127_pilot_20260916_attempt1/source1\n'
            'After two generated segments, the runtime invites you to distill what you want to retain '
            'in a third segment, then sleeps.\n'
            'At sleep your nonempty distillation replaces the earlier visible history with your own summary. '
            'This is lossy: the full raw archive is preserved but not all of it stays visible.')
        for physical in (5, 6, 7):
            text = launcher.classroom_startup(template, '/tmp/source', physical, '/tmp/life')
            self.assertIn(f'physical{physical}', text)
            self.assertIn('pending a separate verified relay', text)
            self.assertNotIn('old.', text)
            if physical == 7:
                self.assertIn('without requesting a summary', text)
                self.assertIn('Sleep does not summarize or compact', text)
                self.assertNotIn('invites you to distill', text)
            if physical == 6:
                self.assertIn('select passages', text)


class MathOwnershipTests(unittest.TestCase):
    def test_other_slots_never_reach_provenance_read(self):
        for physical in (0, 1, 2, 3, 4, True, 8):
            with self.subTest(physical=physical), patch.object(launcher.native, 'read') as reading, \
                    self.assertRaisesRegex(ValueError, 'math_readonly_slots_only'):
                launcher.math_provenance(physical)
            reading.assert_not_called()

    def test_exact_readonly_identity_and_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'PLAN.json').write_text('{}')
            actor = dict(pid=123, uid=os.getuid(), parent=124, cvd=[launcher.DEVICES[7]],
                argv=[str(launcher.PYTHON), '-B', '-m', launcher.MATH_MODULE, 'resident', '--index', '7'])
            supervisor = dict(pid=124, uid=os.getuid(), cvd=[],
                argv=['python3', '-B', '-m', launcher.MATH_MODULE, 'guard', '--index', '7'])
            (root/'LAUNCH.json').write_text(json.dumps(dict(identity=dict(pid=123),
                plan=dict(sha256=launcher.native.sha(root/'PLAN.json')))))
            request = dict(node='a100', physical=7, actor=actor, supervisor=supervisor,
                wait_seconds=300, gate=dict(cpu_passed=True, builder_line='2026-09-16 [Builder] PASS'))
            launcher.validate_math_pair(request, dict(root=str(root)))
            for key, value in (('argv', ['train']), ('parent', 125), ('uid', os.getuid()+1),
                    ('cvd', [launcher.DEVICES[0]]), ('pid', 999)):
                candidate = deepcopy(request)
                candidate['actor'][key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    launcher.validate_math_pair(candidate, dict(root=str(root)))


class MathOrphanProofTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.failure = self.base/'orch_r136_node1_classroom_20260916_attempt1/retire6_1'
        self.failure.mkdir(parents=True)
        self.old = dict(actor=dict(pid=123,parent=999999999,uid=os.getuid()),supervisor=dict(pid=999999999))
        (self.failure/'ERROR.json').write_text(json.dumps(dict(error_type='ValueError',error='identity_drift_no_signal')))
        (self.failure/'REQUEST.json').write_text(json.dumps(dict(request=self.old)))
        (self.failure/'STATE.tar').write_bytes(b'preserved original boundary bytes')
        (self.failure/'PRESERVATION.json').write_text(json.dumps(dict(archive=launcher.ref(self.failure/'STATE.tar'))))
        (self.failure/'BOUNDARY.json').write_text(json.dumps(dict(optimizer_updates=0)))
        self.request=dict(physical=6,actor=dict(self.old['actor'],parent=1),supervisor=self.old['supervisor'],
            orphan_recovery=launcher.ref(self.failure/'ERROR.json'))
        patch.object(launcher,'BASE',self.base).start()
        self.addCleanup(patch.stopall)

    def test_only_same_continuing_orphan_accepted(self):
        launcher.validate_math_orphan(self.request)
        for key,value in [('pid',124),('parent',2),('uid',os.getuid()+1)]:
            candidate=deepcopy(self.request);candidate['actor'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                launcher.validate_math_orphan(candidate)

    def test_other_slot_rejected(self):
        self.request['physical']=7
        with self.assertRaisesRegex(ValueError,'math6_orphan_only'):
            launcher.validate_math_orphan(self.request)

    def test_missing_or_changed_archive_rejected(self):
        (self.failure/'STATE.tar').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'archive_intact'):
            launcher.validate_math_orphan(self.request)

    def test_live_supervisor_rejected(self):
        old=dict(self.old,supervisor=dict(pid=os.getpid()))
        (self.failure/'REQUEST.json').write_text(json.dumps(dict(request=old)))
        self.request['supervisor']=old['supervisor']
        with self.assertRaisesRegex(ValueError,'same_continuing_orphan'):
            launcher.validate_math_orphan(self.request)


class MathRetirementOrderingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root/'retire'
        (self.root/'CURSOR.json').write_text(json.dumps(dict(next_cycle=9)))
        (self.root/'PLAN.json').write_text('{}')
        self.request = dict(physical=7, actor=dict(pid=100), supervisor=dict(pid=101),
            scan_config='mock', wait_seconds=300)
        self.events = []
        self.signalled = []
        from gpu import orch_r125_continual_guard as guard
        patches = [patch.object(launcher.socket, 'gethostname', return_value='[REDACTED_HOST]'),
            patch.object(launcher, 'math_provenance', return_value=(dict(root=str(self.root), uuid=launcher.DEVICES[7]), [])),
            patch.object(launcher, 'validate_math_pair'),
            patch.object(guard, 'validate', return_value=({},dict(physical=7,gpu_uuid=launcher.DEVICES[7]))),
            patch.object(launcher.ctypes, 'CDLL', return_value=SimpleNamespace(inotify_init1=Mock(return_value=200),
                inotify_add_watch=Mock(return_value=1))),
            patch.object(launcher.os, 'pidfd_open', side_effect=lambda pid: pid),
            patch.object(launcher.os, 'close'), patch.object(launcher.preservation, 'same'),
            patch.object(launcher.preservation, 'pause', side_effect=lambda process, descriptor: self.events.append(('pause',descriptor))),
            patch.object(launcher.select, 'select', return_value=([200],[],[])),
            patch.object(launcher.os, 'read', return_value=b'event'),
            patch.object(launcher, 'boundary_event', return_value=True),
            patch.object(launcher.signal, 'pidfd_send_signal', side_effect=self.send_signal),
            patch.object(launcher, 'math_frontier', return_value=dict(next_cycle=10)),
            patch.object(launcher, 'scan', return_value=dict(clear=True,scanner_euid=0,blocking_reasons=[],gpu=dict(uuid=launcher.DEVICES[7])))]
        for item in patches:
            item.start()
        self.archive = patch.object(launcher, 'archive_same_life', side_effect=self.archived).start()
        self.addCleanup(patch.stopall)

    def archived(self, paths, destination):
        self.events.append(('archive_verified', None))
        return dict(files={}, archive={})

    def send_signal(self, descriptor, signum):
        self.events.append(('signal',signum))
        self.signalled.append((descriptor,signum))

    def test_archive_before_any_TERM_and_exact_actor_first(self):
        with patch.object(launcher, 'scan', side_effect=lambda config, output: (launcher.write(output, {}),
                dict(clear=True, scanner_euid=0, blocking_reasons=[], gpu=dict(uuid=launcher.DEVICES[7])))[1]):
            result = launcher.retire_math(self.request, self.output)
        self.assertEqual(result['status'], 'RELEASED')
        self.assertEqual(self.events[:3], [('signal',signal.SIGSTOP),('pause',100),('pause',101)])
        self.assertLess(self.events.index(('archive_verified',None)), self.events.index(('signal',signal.SIGTERM)))
        self.assertNotIn(('signal', signal.SIGKILL), self.events)
        self.assertEqual([descriptor for descriptor, signum in self.signalled if signum==signal.SIGTERM], [100,101])

    def test_guard_first_would_reparent_live_child(self):
        def same(process):
            if process['pid']==100 and (101,signal.SIGTERM) in self.signalled:
                raise ValueError('identity_drift_no_signal')
        with patch.object(launcher.preservation, 'same', side_effect=same), \
                patch.object(launcher, 'scan', side_effect=lambda config, output: (launcher.write(output, {}),
                dict(clear=True,scanner_euid=0,blocking_reasons=[],gpu=dict(uuid=launcher.DEVICES[7])))[1]):
            result=launcher.retire_math(self.request,self.output)
        self.assertEqual(result['status'],'RELEASED')

    def test_validated_orphan_does_not_signal_missing_guard(self):
        self.request['orphan_recovery'] = dict(path='validated_by_mock')
        with patch.object(launcher, 'scan', side_effect=lambda config, output: (launcher.write(output, {}),
                dict(clear=True,scanner_euid=0,blocking_reasons=[],gpu=dict(uuid=launcher.DEVICES[7])))[1]):
            launcher.retire_math(self.request,self.output)
        self.assertTrue(all(descriptor==100 for descriptor, signum in self.signalled))

    def test_failed_archive_resumes_both_no_TERM(self):
        self.archive.side_effect = ValueError('archive_failed')
        with self.assertRaisesRegex(ValueError, 'archive_failed'):
            launcher.retire_math(self.request, self.output)
        self.assertNotIn(('signal',signal.SIGTERM),self.events)
        self.assertEqual(self.events.count(('signal',signal.SIGCONT)),2)

    def test_changed_frontier_after_archive_resumes_both(self):
        with patch.object(launcher, 'math_frontier', side_effect=[dict(next_cycle=10),dict(next_cycle=11)]), \
                self.assertRaisesRegex(ValueError, 'frontier_still_saved'):
            launcher.retire_math(self.request, self.output)
        self.assertNotIn(('signal',signal.SIGTERM),self.events)


if __name__ == '__main__':
    unittest.main()
