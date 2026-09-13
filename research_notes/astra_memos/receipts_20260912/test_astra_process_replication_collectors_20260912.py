"""CPU fixture regressions; real frozen phase receipts, mock training/backend/release."""
from contextlib import ExitStack
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import struct
import sys
import tarfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp')
import test_astra_rulegame_process_replication_20260912 as fixtures

spec = importlib.util.spec_from_file_location('replication_collectors_test_target', '/tmp/astra_process_replication_collectors_20260912.py')
collector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = collector
spec.loader.exec_module(collector)
diagnostic, replica = fixtures.diagnostic, fixtures.replica


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ReplicationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(collector, 'load_runner', return_value=replica))
        self.snapshot = self.stack.enter_context(patch.object(collector, 'process_snapshot', return_value=[]))
        self.gpu = dict(gpu_uuid='GPU-CPU-FIXTURE', reconciled_system_services=[])
        self.xml = '<nvidia_smi_log><gpu><uuid>GPU-CPU-FIXTURE</uuid><processes /></gpu></nvidia_smi_log>'
        self.vacancy = self.stack.enter_context(patch.object(collector, 'vacancy', return_value=(self.gpu, self.xml)))
        self.stack.enter_context(patch.dict(os.environ, dict(os.environ), clear=True))
        os.environ.pop('CUDA_VISIBLE_DEVICES', None)
        self.launcher = self.fixture.fixture.root/'launcher.py'
        self.launcher.write_text('"""CPU launcher fixture, never executed."""\n')
        self.seed = 0

    def replace(self, path, value):
        Path(path).write_bytes((json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode())

    def reseal(self, path):
        self.replace(path/'manifest.json', dict(files=diagnostic.tree_hashes(path, ('manifest.json',))))

    def supervisor(self, original, phase):
        def run(root, plan, stage, command, *extra):
            started = time.monotonic()
            members = collector.ARMS if phase == 'write' else collector.CELLS
            pid = 71000 + self.seed*100 + (0 if phase == 'write' else 10) + members.index(stage.name)
            try:
                original(root, plan, stage, command, *extra)
            finally:
                receipt = collector.read(stage/'supervision.json')
                receipt.update(device='2', returncode=0 if receipt['ok'] else 1,
                    error=None if receipt['ok'] else {'message': 'mock failure'}, reserved_seconds=time.monotonic()-started)
                self.replace(stage/'supervision.json', receipt)
                self.replace(stage/'process.json', dict(pid=pid, pgid=pid, argv=command, device='2', timeout=600, started=started))
                if phase == 'write':
                    fit = root/'fits'/stage.name
                    if (fit/'attempt.json').is_file():
                        attempt = collector.read(fit/'attempt.json')
                        attempt['pid'] = pid
                        self.replace(fit/'attempt.json', attempt)
                    if (fit/'manifest.json').is_file():
                        self.reseal(fit)
                else:
                    data = stage/'data'
                    for name in ('isolation.json', 'backend.ready.json'):
                        path = data/name
                        if path.is_file():
                            value = collector.read(path)
                            value['pid'] = pid
                            if name == 'isolation.json':
                                value.update(pgid=pid, parent_pid=os.getpid())
                            self.replace(path, value)
                    if (data/'manifest.json').is_file():
                        self.reseal(data)
            return receipt
        return run

    def config(self, phase, root, plan_sha, started, previous=None):
        logs = root.with_name(root.name+'_launch')
        logs.mkdir()
        plan = collector.read(root/'plan.json')
        launch = dict(root=str(root), plan_sha256=plan_sha, driver_sha256=collector.DRIVER_SHA,
            launcher_sha256=collector.digest(self.launcher), fit_seed=self.seed, pid=os.getpid(),
            started_utc=fixtures.writes.iso(started), source=plan['source_root'], device=plan['device'],
            continuous_reservation=True, controller_seconds=collector.CAPS[phase], cleanup_reserve=140,
            worker_cap_seconds=600, external_collection_margin_seconds=300, gpu=self.gpu,
            phase=plan['protocol'] if phase == 'write' else plan['version'],
            command=[plan['python'], '-B', str(collector.DRIVER), 'write' if phase == 'write' else 'evaluate',
                '--fit-seed', str(self.seed), '--root', str(root), '--plan-sha256', plan_sha, '--allow-gpu'])
        launch['arms' if phase == 'write' else 'cells'] = list(collector.ARMS if phase == 'write' else collector.CELLS)
        config = dict(phase=phase, fit_seed=self.seed, root=root, plan_sha256=plan_sha, launch_root=logs,
            launcher=self.launcher, launcher_sha256=collector.digest(self.launcher), out=root.with_name(root.name+'_collection'))
        if previous is not None:
            config.update(write_release=previous, write_release_sha256=collector.digest(previous))
            launch.update(write_plan_sha256=plan['write_plan_sha256'], write_release_path=str(previous),
                write_release_sha256=config['write_release_sha256'])
        self.replace(logs/'launch.json', launch)
        (logs/'gpu.xml').write_text(self.xml)
        (logs/'controller.log').write_text('CPU fixture, no native launch\n')
        config['launch_sha256'] = collector.digest(logs/'launch.json')
        return collector.settings(config)

    def write_fixture(self, seed=0):
        self.seed = seed
        self.fixture.prepare_write(seed)
        started = time.time()
        original = self.fixture.supervise_write
        with patch.object(self.fixture, 'supervise_write', side_effect=self.supervisor(original, 'write')):
            self.fixture.run_write()
        self.write_config = self.config('write', self.fixture.write_root, self.fixture.prepared_write['plan_sha256'], started)
        return self.write_config

    def readout_fixture(self, seed=0, failed=False):
        self.write_fixture(seed)
        self.invoke(self.write_config, 'finish')
        self.fixture.prepare_readout()
        started = time.time()
        original = self.fixture.supervise_readout
        self.fixture.fail_cell = 'P_ON' if failed else None
        with patch.object(self.fixture, 'supervise_readout', side_effect=self.supervisor(original, 'readout')):
            if failed:
                with self.assertRaises(Exception):
                    self.fixture.run_readout()
            else:
                self.fixture.run_readout()
        return self.config('readout', self.fixture.readout_root, self.fixture.prepared_readout['plan_sha256'], started,
            self.write_config['out']/'validation.json')

    def invoke(self, config, action):
        command = collector.cli_command(config, action)
        self.assertEqual(command[:3], [os.path.abspath(sys.executable), '-B', str(collector.SELF)])
        with patch.object(diagnostic, 'native_tokenizer', side_effect=AssertionError('NO TOKENIZER REPLAY')), \
             patch.object(diagnostic, 'NativeBackend', side_effect=AssertionError('NO MODEL')), \
             patch.object(replica.ReadoutPhase, 'audit_cell', side_effect=AssertionError('NATIVE AUDIT FORBIDDEN')), \
             patch.object(replica.WritePhase, 'write_pair', side_effect=AssertionError('NO PHASE CHAIN')), \
             patch.object(replica.ReadoutPhase, 'evaluate', side_effect=AssertionError('NO PHASE CHAIN')), \
             patch.object(fixtures.trainer, 'run_training', side_effect=AssertionError('NO FIT')), \
             patch('sys.stdout', new=io.StringIO()) as output:
            collector.main(command[3:])
        return json.loads(output.getvalue())

    def test_write_generated_cli_complete_finite_no_weights_or_retry(self):
        config = self.write_fixture()
        before = diagnostic.tree_hashes(config['root'])
        result = self.invoke(config, 'finish')
        self.assertEqual(result['status'], 'COLLECTED_PAIRED_WRITE')
        self.assertTrue(result['full_release'] and result['aggregate_available'] and result['phase_within_bound'])
        self.assertEqual(result['fit_seed'], 0)
        audit = collector.read(config['out']/'audit.json')
        self.assertEqual(audit['aggregate']['optimizer_updates'], 24)
        self.assertTrue(all(audit['arms'][arm]['finite_weights']['finite'] for arm in collector.ARMS))
        self.assertEqual(before, diagnostic.tree_hashes(config['root']))
        validation = collector.read(config['out']/'validation.json')
        collector.common.validate_archive(Path(result['archive']), validation['files'])
        with tarfile.open(result['archive']) as archive:
            self.assertFalse(any(name.endswith('.safetensors') or '/corpora/' in name for name in archive.getnames()))
        with self.assertRaisesRegex(ValueError, 'exclusive fresh'):
            self.invoke(config, 'finish')
        self.assertEqual(self.vacancy.call_count, 2)

    def test_readout_seed1_generated_cli_complete_three_cells_and_prior_release(self):
        config = self.readout_fixture(seed=1)
        result = self.invoke(config, 'finish')
        self.assertEqual(result['status'], 'COLLECTED_PROCESS_READOUT')
        self.assertEqual(result['fit_seed'], 1)
        self.assertLessEqual(result['aggregate_reserved_seconds'], 3600)
        audit = collector.read(config['out']/'audit.json')
        self.assertEqual(audit['totals']['requests'], 96)
        self.assertEqual(audit['totals']['output_token_ceiling'], 27600)
        for cell in collector.CELLS:
            self.assertEqual(audit['cells'][cell]['process_metrics']['totals']['quiz_items'], 24)
            self.assertIn('persistent_output_diagnostics', audit['cells'][cell]['process_metrics'])
        self.assertTrue(all(value['finite'] for value in audit['finite_weights'].values()))
        validation = collector.read(config['out']/'validation.json')
        self.assertEqual(validation['files']['metadata/lineage/write_validation.json'], config['write_release_sha256'])
        self.assertFalse(result['automatic_next_phase'] or result['automatic_promotion'] or result['weights_in_capsule'])

    def test_status_cli_blind_to_scores_and_transitive_session_barrier(self):
        config = self.write_fixture()
        (config['root']/'run/result.json').write_text('not JSON deliberately')
        self.assertTrue(self.invoke(config, 'status')['ready'])
        self.assertEqual(self.vacancy.call_count, 0)
        pid = collector.read(config['root']/'run/P/process.json')['pid']
        self.snapshot.return_value = [dict(pid=99001, ppid=pid, pgid=99001, session=99001),
                                     dict(pid=99002, ppid=99001, pgid=99002, session=99002)]
        self.assertFalse(self.invoke(config, 'status')['ready'])
        with self.assertRaisesRegex(ValueError, 'full owned'):
            self.invoke(config, 'finish')
        self.assertTrue((config['out']/'failure.json').is_file())
        self.assertFalse((config['out']/'audit.json').exists())

    def test_live_reparented_group_or_session_blocks(self):
        config = self.write_fixture()
        pid = collector.read(config['root']/'run/P/process.json')['pid']
        for field in ('pgid', 'session'):
            row = dict(pid=99001, ppid=1, pgid=99001, session=99001)
            row[field] = pid
            self.snapshot.return_value = [row]
            self.assertFalse(self.invoke(config, 'status')['ready'])

    def test_phase_seed_plan_and_launcher_mismatches(self):
        config = self.write_fixture()
        for changes in ({'fit_seed': 1}, {'phase': 'readout'}, {'plan_sha256': '0'*64}, {'launch_sha256': '0'*64}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                collector.status(dict(config, **changes))
        self.launcher.write_text('changed launcher')
        with self.assertRaisesRegex(ValueError, 'launcher source'):
            self.invoke(config, 'finish')
        self.assertTrue((config['out']/'failure.json').is_file())

    def test_partial_write_no_aggregate_even_if_surviving_fit_valid(self):
        config = self.write_fixture()
        result = collector.read(config['root']/'run/result.json')
        (config['root']/'run/result.json').unlink()
        self.replace(config['root']/'run/failure.json', dict(status='PARTIAL_FAILED', completed={'P': result['arms']['P']},
            retry=False, controller_seconds=result['controller_seconds'], readout='NOT_RUN'))
        (config['root']/'fits/A/receipt.json').unlink()
        output = self.invoke(config, 'finish')
        self.assertEqual(output['status'], 'COLLECTED_FAILURE_NO_AGGREGATE')
        self.assertFalse(output['aggregate_available'])
        self.assertIsNone(collector.read(config['out']/'audit.json')['aggregate'])

    def test_failed_middle_readout_preserves_no_aggregate(self):
        config = self.readout_fixture(failed=True)
        result = self.invoke(config, 'finish')
        self.assertEqual(result['status'], 'COLLECTED_FAILURE_NO_AGGREGATE')
        self.assertIsNone(collector.read(config['out']/'audit.json')['aggregate'])
        self.assertFalse(result['aggregate_available'])

    def test_unknown_file_credentials_and_symlinks_rejected(self):
        config = self.write_fixture()
        root = config['root']
        stray = root/'surprise.json'
        stray.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'unknown metadata'):
            collector.inventory(config)
        stray.unlink()
        log = config['launch_root']/'controller.log'
        log.write_text('export HF_TOKEN=private-fixture-token\n')
        with self.assertRaisesRegex(ValueError, 'credential'):
            collector.inventory(config)
        log.write_text('fixture\n')
        stray.symlink_to(root/'plan.json')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            collector.inventory(config)

    def test_nonfinite_weight_payload_direct_scanner(self):
        root = self.fixture.fixture.root
        path = root/'bad.safetensors'
        header = json.dumps({'model.layer.lora_A.weight': dict(dtype='F32', shape=[1], data_offsets=[0, 4])}).encode()
        path.write_bytes(struct.pack('<Q', len(header))+header+struct.pack('<f', float('nan')))
        with self.assertRaisesRegex(ValueError, 'nonfinite saved weight'):
            collector.common.finite_weights(path, collector.common.file_hash(path))

    def test_bad_saved_fit_and_forward_counts_fail_complete_collection(self):
        config = self.write_fixture()
        path = config['root']/'fits/A/forwards/0012.json'
        value = collector.read(path)
        value['target_tokens'] = -1
        self.replace(path, value)
        self.reseal(config['root']/'fits/A')
        result = self.invoke(config, 'finish')
        self.assertFalse(result['aggregate_available'])
        self.assertIsNone(collector.read(config['out']/'audit.json')['aggregate'])

    def test_bad_raw_readout_response_fails_without_tokenizer(self):
        config = self.readout_fixture()
        response = config['root']/'run/P_ON/data/calls/0000.response.json'
        response.unlink()
        self.reseal(config['root']/'run/P_ON/data')
        result = self.invoke(config, 'finish')
        self.assertEqual(result['status'], 'COLLECTED_FAILURE_NO_AGGREGATE')
        self.assertFalse(result['aggregate_available'])

    def test_wrong_prior_release_xml_rejected(self):
        config = self.readout_fixture()
        path = config['write_release'].parent/'final_release.xml'
        path.write_text(self.xml.replace('GPU-CPU-FIXTURE', 'GPU-WRONG'))
        with self.assertRaisesRegex(ValueError, 'write final release XML'):
            self.invoke(config, 'finish')
        self.assertTrue((config['out']/'failure.json').exists())

    def test_wrong_prior_release_seed_rejected(self):
        config = self.readout_fixture()
        previous = collector.read(config['write_release'])
        previous['fit_seed'] = 1
        self.replace(config['write_release'], previous)
        config['write_release_sha256'] = collector.digest(config['write_release'])
        launch = collector.read(config['launch_root']/'launch.json')
        launch['write_release_sha256'] = config['write_release_sha256']
        self.replace(config['launch_root']/'launch.json', launch)
        config['launch_sha256'] = collector.digest(config['launch_root']/'launch.json')
        with self.assertRaisesRegex(ValueError, 'same-seed'):
            self.invoke(config, 'finish')

    def test_launch_to_release_budget_overrun_is_preserved_failure(self):
        config = self.write_fixture()
        launch = collector.read(config['launch_root']/'launch.json')
        launch['started_utc'] = fixtures.writes.iso(time.time()-1600)
        self.replace(config['launch_root']/'launch.json', launch)
        config['launch_sha256'] = collector.digest(config['launch_root']/'launch.json')
        with self.assertRaisesRegex(ValueError, 'reservation or six-hour lease ceiling'):
            self.invoke(config, 'finish')
        self.assertTrue((config['out']/'failure.json').is_file())
        self.assertFalse((config['out']/'validation.json').exists())

    def test_metadata_change_after_archive_fails_publication(self):
        config = self.write_fixture()
        pack = collector.common.pack
        def changed(*args):
            checksum = pack(*args)
            (config['launch_root']/'controller.log').write_text('changed after archive\n')
            return checksum
        with patch.object(collector.common, 'pack', side_effect=changed), self.assertRaisesRegex(ValueError, 'custody inputs changed'):
            self.invoke(config, 'finish')
        self.assertFalse((config['out']/'validation.json').exists())

    def test_release_failure_preserves_exclusive_attempt(self):
        config = self.write_fixture()
        self.vacancy.side_effect = RuntimeError('GPU or queue not vacant')
        with self.assertRaisesRegex(RuntimeError, 'queue'):
            self.invoke(config, 'finish')
        self.assertFalse((config['out']/'validation.json').exists())
        self.assertTrue(collector.read(config['out']/'failure.json')['partial_artifacts_preserved'])
        with self.assertRaisesRegex(ValueError, 'exclusive fresh'):
            self.invoke(config, 'finish')

    def test_final_release_failure_keeps_partial_archive(self):
        config = self.write_fixture()
        self.vacancy.side_effect = [(self.gpu, self.xml), RuntimeError('queue changed')]
        with self.assertRaisesRegex(RuntimeError, 'queue changed'):
            self.invoke(config, 'finish')
        self.assertTrue((config['out']/'metadata.tgz').is_file())
        self.assertTrue((config['out']/'failure.json').is_file())
        self.assertFalse((config['out']/'validation.json').exists())

    def test_real_cli_missing_out_seed_and_phase_rejected(self):
        config = self.write_fixture()
        command = collector.cli_command(config, 'finish')[3:]
        with self.assertRaisesRegex(ValueError, 'finish requires out'):
            collector.main(command[:-2])
        command[command.index('--fit-seed')+1] = '2'
        with patch('sys.stderr', new=io.StringIO()), self.assertRaises(SystemExit):
            collector.main(command)
        with self.assertRaisesRegex(ValueError, 'status forbids out'):
            collector.main(collector.cli_command(config, 'status')[3:]+['--out', str(config['out'])])

    def test_timer_300s_and_restoration(self):
        calls = []
        with patch.object(collector.signal, 'getitimer', return_value=(0.0, 0.0)), \
             patch.object(collector.signal, 'setitimer', side_effect=lambda *args: calls.append(args)), \
             patch.object(collector, 'collect', side_effect=collector.CollectionExpired('expired')):
            previous = signal.getsignal(signal.SIGALRM)
            with self.assertRaises(collector.CollectionExpired):
                collector.finish({})
            self.assertEqual(signal.getsignal(signal.SIGALRM), previous)
        self.assertEqual(calls, [(signal.ITIMER_REAL, 300), (signal.ITIMER_REAL, 0)])


if __name__ == '__main__':
    unittest.main()
