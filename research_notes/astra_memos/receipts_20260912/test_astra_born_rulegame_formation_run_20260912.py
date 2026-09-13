"""CPU-only integration of frozen custody, role capture, journaling and collection."""
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SOURCE = Path('/data/home/rohing/dream-state')
DRIVER = Path('/tmp/astra_born_rulegame_formation_run_20260912.py')


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


run = load('born_run_under_test', DRIVER)
frozen_tests = load('frozen_birth_fixtures', '/tmp/test_astra_birth_conditional_run_20260913.py')


class FormationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frozen_tests.SOURCE = SOURCE
        frozen_tests.PipelineTests.setUpClass()
        sys.path.insert(0, str(SOURCE/'tests'))
        cls.role_tests = load('born_committed_fixtures', SOURCE/'tests/test_born_rulegame_formation.py')
        cls.role, cls.diagnostic = run.source_api(SOURCE, run.ROLE_SHA)

    def setUp(self):
        self.fixture = frozen_tests.PipelineTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.rootdir = self.fixture.directory
        self.upstream_root, self.upstream_pin, self.upstream_plan, self.upstream_release = self.fixture.released_fit()
        self.normalized = run.normalize_birth(self.upstream_root, self.upstream_pin,
            self.upstream_release['validation'], self.upstream_release['validation_sha256'])
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(run, 'normalized_in_subprocess', return_value=deepcopy(self.normalized)))
        self.stack.enter_context(patch.object(run.common, 'process_snapshot', return_value=[]))
        self.stack.enter_context(patch.object(run.birth, 'vacancy', side_effect=self.fixture.mock_vacancy))

    def prepare(self):
        root = self.rootdir/'formation'
        prepared = run.prepare(SOURCE, run.ROLE_SHA, self.upstream_root, self.upstream_pin,
            self.upstream_release['validation'], self.upstream_release['validation_sha256'],
            root, '2', self.fixture.deadline, self.fixture.lease)
        return root, prepared['plan_sha256'], run.read(root/'plan.json')

    def capture(self, root, pin, plan):
        stage = root/'run/formation'
        (stage/'worker').mkdir(parents=True)
        began = time.monotonic()
        controller = dict(pid=51001, ppid=51000, pgid=51001, session=51001, start_ticks=123,
            argv=run.controller_command(root, pin), plan_sha256=pin, started_wall=time.time(),
            started_monotonic=began-1, hard_end=time.time()+800, continuous_reservation=True)
        run.write_json(root/'run/controller.json', controller)
        process = dict(pid=52001, pgid=52001, started=began, timeout=600, device='2',
            argv=run.worker_command(root, pin, controller['hard_end']))
        run.write_json(stage/'worker/process.json', process)
        data = stage/'data'
        data.mkdir()
        (data/'calls').mkdir()
        cutoff = began+600
        run.write_json(data/'isolation.json', dict(pid=52001, parent_pid=51001, pgid=52001, plan_sha256=pin,
            binding_sha256=plan['binding_sha256'], hard_end=controller['hard_end'], cutoff=cutoff,
            one_engine=True, prompt_parent=False, online_updates=False))
        run.write_json(data/'backend.ready.json', dict(pid=52001, ready=time.monotonic()))
        backend = self.role_tests.RoleBackend(plan['binding'])
        journal = run.JournalBackend(backend, data, self.diagnostic)
        actual_replay = self.role.replay_formation
        def barrier_checked(*args, **kwargs):
            self.assertTrue((data/'capture_barrier.json').is_file())
            self.assertEqual(run.read(data/'capture_barrier.json')['calls'], len(args[0]['calls']))
            return actual_replay(*args, **kwargs)
        with patch.object(self.role, 'replay_formation', side_effect=barrier_checked):
            capture = self.role.capture_formation(journal, plan['binding'], expected_binding_sha256=plan['binding_sha256'], cutoff=cutoff)
        run.write_json(data/'capture.json', capture)
        run.write_json(data/'backend.cleanup.json', dict(closed=True, error=None))
        run.write_json(data/'manifest.json', dict(files=self.diagnostic.tree_hashes(data)))
        run.write_json(stage/'worker/supervision.json', dict(ok=True, error=None, returncode=0, device='2',
            owned_group_empty=True, gpu_processes_absent=True, reservation_release_verified=True,
            reserved_seconds=time.monotonic()-began))
        run.write_new(stage/'worker/stdout.log', b'CPU simulation only\n')
        receipt = run.verify_capture(root, plan, self.role, self.diagnostic)
        run.write_json(stage/'receipt.json', receipt)
        run.write_json(root/'run/result.json', dict(status='COMPLETE_AWAITING_MAIN_AUDIT', phase='formation', plan_sha256=pin,
            receipt_sha256=run.digest(stage/'receipt.json'), supervision_sha256=run.digest(stage/'worker/supervision.json'),
            controller_seconds=time.monotonic()-controller['started_monotonic'], ended_wall=time.time(),
            claims=run.CLAIMS, automatic_progression=False))
        return capture, receipt

    def launch(self, root, pin, plan, failed=False):
        logs = self.rootdir/'formation_launch'
        logs.mkdir()
        launcher = self.fixture.launcher
        value = run.launch_contract(root, plan, pin, launcher, run.digest(launcher))
        value.update(pid=51001, pgid=51001, session=51001, launcher_pid=51000, launcher_pgid=51000, launcher_session=51000,
            started_wall=self.normalized['released_wall']+.00001, gpu_uuid='GPU-00000000-0000-0000-0000-000000000002')
        run.write_json(logs/'launch.json', value)
        launch_pin = run.digest(logs/'launch.json')
        run.write_json(logs/'exit.json', dict(launch_sha256=launch_pin, returncode=1 if failed else 0, ended_wall=time.time()))
        return dict(root=root, plan_sha256=pin, launch_root=logs, launch_sha256=launch_pin,
            launcher=launcher, launcher_sha256=run.digest(launcher), out=self.rootdir/'formation_collected')

    def test_normalized_exact_terminal_auth_and_release_joins(self):
        normalized = self.normalized
        self.assertEqual(normalized['pin']['birth_arm'], 'AUTH')
        self.assertEqual(normalized['pin']['completion_receipt_sha256'], run.digest(self.upstream_root/'run/result.json'))
        self.assertEqual(normalized['auth_receipt_sha256'], run.digest(self.upstream_root/'run/AUTH/receipt.json'))
        self.assertTrue(normalized['full_release'])
        self.assertFalse(normalized['component_pass_required'])
        self.assertNotIn('scores', normalized['pin'])

    def test_prepare_and_check_new_snapshot_binding(self):
        root, pin, plan = self.prepare()
        run.checked_plan(root, pin)
        self.assertEqual(plan['max_calls'], 60)
        self.assertEqual(plan['max_output_tokens'], 18480)
        self.assertEqual(plan['controller_seconds'], 900)
        self.assertEqual(plan['binding']['role_identities']['parent']['adapter_files'], {})
        self.assertIsNone(plan['binding']['role_identities']['parent']['adapter_input'])
        for role in ('wake', 'record', 'restate'):
            self.assertEqual(plan['binding']['role_identities'][role]['adapter_input'], str(self.upstream_root/'run/AUTH/adapter'))

    def test_actual_isolated_normalizer_cli(self):
        result = subprocess.run([sys.executable, '-B', str(DRIVER), '_birth-pin', '--fit-root', str(self.upstream_root),
            '--fit-plan-sha256', self.upstream_pin, '--fit-release', self.upstream_release['validation'],
            '--fit-release-sha256', self.upstream_release['validation_sha256']], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.normalized)

    def test_incomplete_release_fails_before_completion_normalization(self):
        with patch.object(run.birth, 'accepted_release', return_value=dict(phase_complete=False)), \
                patch.object(run.birth, 'audit_terminal') as audit, self.assertRaises(ValueError):
            run.normalize_birth(self.upstream_root, self.upstream_pin, self.upstream_release['validation'], self.upstream_release['validation_sha256'])
        audit.assert_not_called()

    def test_wrong_birth_pin_or_release_hash_rejected(self):
        with self.assertRaises(ValueError):
            run.normalize_birth(self.upstream_root, '0'*64, self.upstream_release['validation'], self.upstream_release['validation_sha256'])
        with self.assertRaises(ValueError):
            run.normalize_birth(self.upstream_root, self.upstream_pin, self.upstream_release['validation'], '0'*64)

    def test_wrong_or_missing_role_source_preserves_failed_prepare(self):
        with self.assertRaises(ValueError):
            run.prepare(SOURCE, '0'*64, self.upstream_root, self.upstream_pin, self.upstream_release['validation'],
                self.upstream_release['validation_sha256'], self.rootdir/'bad', '2', self.fixture.deadline, self.fixture.lease)
        self.assertTrue((self.rootdir/'bad/prepare_failure.json').exists())
        with self.assertRaises(FileNotFoundError):
            run.source_api(self.rootdir, run.ROLE_SHA)

    def test_altered_or_deranged_normalized_adapter_rejected(self):
        for key in ('model_files', 'birth_arm'):
            normalized = deepcopy(self.normalized)
            normalized['pin'][key] = {} if key == 'model_files' else 'DERANGED'
            with self.subTest(key=key), self.assertRaises(ValueError):
                run.verify_custody(normalized, SOURCE, self.diagnostic)

    def test_changed_birth_artifact_detected(self):
        (self.upstream_root/'run/AUTH/receipt.json').write_text('{}')
        with self.assertRaises(ValueError):
            run.verify_custody(self.normalized, SOURCE, self.diagnostic)

    def test_complete_sixty_call_journal_precedes_replay(self):
        root, pin, plan = self.prepare()
        capture, receipt = self.capture(root, pin, plan)
        self.assertEqual(receipt['replay']['calls'], 60)
        self.assertEqual(receipt['replay']['roles'], run.LIMITS)
        for row in capture['calls']:
            self.assertEqual(row['envelope']['lora_request'] is None, row['request']['role'] == 'parent')
        self.assertFalse(receipt['retained_learning'])

    def test_missing_raw_pair_rejected_before_replay(self):
        root, pin, plan = self.prepare()
        self.capture(root, pin, plan)
        (root/'run/formation/data/calls/0000.response.json').unlink()
        with patch.object(self.role, 'replay_formation', side_effect=AssertionError('premature replay')) as replay:
            with self.assertRaises(ValueError):
                run.verify_capture(root, plan, self.role, self.diagnostic)
            replay.assert_not_called()

    def test_wrong_parent_route_rejected(self):
        root, pin, plan = self.prepare()
        data = self.rootdir/'journal'
        data.mkdir()
        (data/'calls').mkdir()
        backend = self.role_tests.RoleBackend(plan['binding'])
        original = backend.generate
        def wrong(request):
            envelope = original(request)
            if request['role'] == 'parent':
                envelope['lora_request'] = self.role._route(plan['binding'], 'wake')
            return envelope
        with patch.object(backend, 'generate', side_effect=wrong), self.assertRaises(self.role.FormationFailure) as failed:
            self.role.capture_formation(run.JournalBackend(backend, data, self.diagnostic), plan['binding'],
                expected_binding_sha256=plan['binding_sha256'], cutoff=time.monotonic()+600)
        self.assertEqual(failed.exception.partial['status'], 'FAILED_PARTIAL')
        self.assertFalse((data/'capture_barrier.json').exists())
        self.assertTrue(list((data/'calls').iterdir()))

    def test_complete_collection_and_consumer_release_api(self):
        root, pin, plan = self.prepare()
        self.capture(root, pin, plan)
        collected = run.collect(**self.launch(root, pin, plan))
        released = run.verified_release(root, pin, collected['validation'], collected['validation_sha256'])
        self.assertEqual(released['capture_path'], str(root/'run/formation/data/capture.json'))
        self.assertTrue(released['release']['phase_complete'])
        self.assertFalse(released['release']['archived_adapter_bytes'])

    def test_failed_collection_does_not_replay_or_promote(self):
        root, pin, plan = self.prepare()
        (root/'run').mkdir()
        run.write_json(root/'run/failure.json', dict(status='FAILED_PARTIAL', retry=False, aggregate=None, controller_seconds=1))
        with patch.object(self.role, 'replay_formation', side_effect=AssertionError('failed phase replay')):
            collected = run.collect(**self.launch(root, pin, plan, failed=True))
        self.assertFalse(collected['phase_complete'])
        with self.assertRaises(ValueError):
            run.verified_release(root, pin, collected['validation'], collected['validation_sha256'])

    def test_live_owned_session_blocks_collection_before_outcome_reads(self):
        root, pin, plan = self.prepare()
        self.capture(root, pin, plan)
        args = self.launch(root, pin, plan)
        with patch.object(run.common, 'process_snapshot', return_value=[dict(pid=59001, ppid=1, pgid=59000, session=52001)]), \
                patch.object(run, 'verify_capture', side_effect=AssertionError('premature outcome inspection')):
            with self.assertRaises(ValueError):
                run.collect(**args)
        self.assertTrue((args['out']/'collection_failure.json').exists())

    def test_unknown_or_credential_metadata_rejected(self):
        root, pin, plan = self.prepare()
        self.capture(root, pin, plan)
        args = self.launch(root, pin, plan)
        unknown = root/'extra.txt'
        unknown.write_text('unknown')
        with self.assertRaises(ValueError):
            run.inventory(root, args['launch_root'])
        unknown.unlink()
        (root/'run/formation/worker/stdout.log').write_text('API_KEY=fake_credential')
        with self.assertRaises(ValueError):
            run.inventory(root, args['launch_root'])

    def test_no_reuse_of_prepared_root(self):
        root, pin, plan = self.prepare()
        with self.assertRaises(ValueError):
            self.prepare()

    def test_second_vacancy_failure_keeps_archive_unaccepted(self):
        root, pin, plan = self.prepare()
        self.capture(root, pin, plan)
        args = self.launch(root, pin, plan)
        first = self.fixture.mock_vacancy(plan, 'GPU-00000000-0000-0000-0000-000000000002')
        with patch.object(run.birth, 'vacancy', side_effect=[first, ValueError('queue busy')]), self.assertRaises(ValueError):
            run.collect(**args)
        self.assertTrue((args['out']/'capsule.tgz').exists())
        self.assertFalse((args['out']/'validation.json').exists())

    def test_actual_worker_uses_one_role_backend_and_durable_barrier(self):
        root, pin, plan = self.prepare()
        stage = root/'run/formation'
        (stage/'worker').mkdir(parents=True)
        hard_end = time.time()+900
        run.write_json(stage/'worker/process.json', dict(pid=52001, pgid=52001, device='2', timeout=600,
            started=time.monotonic(), argv=run.worker_command(root, pin, hard_end)))
        backend = self.role_tests.RoleBackend(plan['binding'])
        backend.backend = object()
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '2'}), patch.object(run.birth, 'owned_worker', frozen_tests.no_window), \
                patch.object(self.role, 'NativeRoleBackend', return_value=backend) as constructor, \
                patch.object(self.role.model_backend, 'close_backend', return_value=True) as closer:
            result = run.capture_worker(root, pin, hard_end, allow_gpu=True)
        constructor.assert_called_once_with(plan['binding'], expected_binding_sha256=plan['binding_sha256'], allow_gpu=True)
        closer.assert_called_once_with(backend.backend)
        self.assertEqual(result['status'], 'CAPTURE_COMPLETE_AWAITING_MAIN')
        self.assertEqual(run.read(stage/'data/capture_barrier.json')['calls'], 60)
        self.assertTrue((stage/'data/manifest.json').exists())


class CLITests(unittest.TestCase):
    def dispatch(self, argv, method, expected):
        with patch.object(run, method, return_value=dict(mock=True)) as target, redirect_stdout(io.StringIO()):
            run.main(argv)
        target.assert_called_once_with(**expected)

    def test_real_formation_command_dispatch(self):
        self.dispatch(run.controller_command('/root', 'pin')[3:], 'formation',
            dict(root='/root', plan_sha256='pin', allow_gpu=True))

    def test_real_worker_command_dispatch(self):
        self.dispatch(run.worker_command('/root', 'pin', 123.5)[3:], 'capture_worker',
            dict(root='/root', plan_sha256='pin', hard_end=123.5, allow_gpu=True))

    def test_prepare_dispatch(self):
        values = dict(source='/source', role_sha256='role', fit_root='/fit', fit_plan_sha256='fitpin', fit_release='/released',
            fit_release_sha256='releasepin', out='/out', device='2', deadline='end', lease_end='lease')
        args = ['prepare']+[value for key, content in values.items() for value in ('--'+key.replace('_', '-'), content)]
        self.dispatch(args, 'prepare', dict(values, controller_seconds=900))

    def test_collect_dispatch(self):
        values = dict(root='/root', plan_sha256='pin', launch_root='/launch', launch_sha256='launchpin',
            launcher='/launcher', launcher_sha256='scriptpin', out='/out')
        args = ['collect']+[value for key, content in values.items() for value in ('--'+key.replace('_', '-'), content)]
        self.dispatch(args, 'collect', values)

    def test_status_dispatch(self):
        self.dispatch(['status', '--root', '/root', '--plan-sha256', 'pin'], 'status',
            dict(root='/root', plan_sha256='pin', launch_root=None, launch_sha256=None))

    def test_actual_help_and_gpu_opt_in(self):
        result = subprocess.run([sys.executable, '-B', str(DRIVER), '--help'], text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('prepare-readout', result.stdout)
        with self.assertRaises(ValueError):
            run.formation('/missing', 'pin')
        with self.assertRaises(ValueError):
            run.capture_worker('/missing', 'pin', 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
