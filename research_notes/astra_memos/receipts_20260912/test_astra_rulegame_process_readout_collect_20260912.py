"""CPU synthetic process-readout captures; no native/GPU/network/SSH/Git."""
import copy
import datetime as dt
import importlib.util
import io
import os
from pathlib import Path
import signal
import sys
import tarfile
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch


sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp')
import test_astra_rulegame_process_readout_20260912 as readout_tests

spec = importlib.util.spec_from_file_location('tested_process_readout_collector', '/tmp/astra_rulegame_process_readout_collect_20260912.py')
collector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = collector
spec.loader.exec_module(collector)
common, bridge, diagnostic = collector.common, readout_tests.bridge, readout_tests.diagnostic


def xml(uuid='GPU-mock', processes=''):
    return f'<nvidia_smi_log><gpu><uuid>{uuid}</uuid><processes>{processes}</processes></gpu></nvidia_smi_log>'


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = readout_tests.ReadoutTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.completed()
        self.root, self.plan = self.fixture.output, self.fixture.plan
        self.logs = self.root.with_name('process_readout_launch')
        self.logs.mkdir()
        self.output = self.root.with_name('process_readout_collection')
        self.launcher = self.fixture.fixture.root / 'launcher.py'
        common.write_new(self.launcher, b'raise RuntimeError("collector must not execute launcher")\n')
        write_root = Path(self.plan['write_root'])
        self.write_release = write_root.with_name(write_root.name + '_collection_attempt1') / 'validation.json'
        self.write_release.parent.mkdir()
        common.write_json(self.write_release, dict(status='COLLECTED_PAIRED_WRITE', full_release=True,
                         aggregate_available=True, plan_sha256=self.plan['write_plan_sha256']))
        self.launch = dict(root=str(self.root), plan_sha256=self.fixture.prepared['plan_sha256'],
            driver_sha256=collector.DRIVER_SHA, pid=os.getpid(), started_utc=dt.datetime.fromtimestamp(time.time()-10, dt.timezone.utc).isoformat(),
            launcher_sha256=common.digest(self.launcher), source=self.plan['source_root'], device='2', gpu={'gpu_uuid': 'GPU-mock'},
            write_plan_sha256=self.plan['write_plan_sha256'],
            write_release_path=str(self.write_release), write_release_sha256=common.digest(self.write_release),
            command=[self.plan['python'], '-B', str(bridge.SELF), 'evaluate', '--root', str(self.root),
                     '--plan-sha256', self.fixture.prepared['plan_sha256'], '--allow-gpu'],
            cells=list(collector.CELLS), controller_seconds=1800, cleanup_reserve=140, worker_cap_seconds=600, continuous_reservation=True)
        common.write_json(self.logs / 'launch.json', self.launch)
        common.write_new(self.logs / 'gpu.xml', xml().encode())
        common.write_new(self.logs / 'controller.log', b'synthetic launch only\n')
        self.config = collector.settings(dict(root=self.root, plan_sha256=self.fixture.prepared['plan_sha256'],
            driver=bridge.SELF, driver_sha256=collector.DRIVER_SHA, write_driver=Path(self.plan['write_driver']),
            write_driver_sha256=self.plan['write_driver_sha256'], write_plan_sha256=self.plan['write_plan_sha256'],
            launch_root=self.logs, launch_sha256=common.digest(self.logs / 'launch.json'), launcher=self.launcher,
            launcher_sha256=common.digest(self.launcher), out=self.output))
        loader = common.load
        def load(path, checksum, name):
            if Path(path) == bridge.SELF:
                self.assertEqual(common.digest(path), checksum)
                return bridge
            return loader(path, checksum, name)
        for context in (patch.object(common, 'load', side_effect=load), patch.object(common, 'process_snapshot', return_value=[])):
            context.start()
            self.addCleanup(context.stop)

    def replace(self, path, value):
        self.fixture.fixture.replace_json(path, value)

    def reseal(self, data):
        self.replace(data / 'manifest.json', {'files': diagnostic.tree_hashes(data, ('manifest.json',))})

    def terminal(self, failed=None, no_quiz=False):
        self.fixture.fail_cell, self.fixture.no_quiz = failed, no_quiz
        original = self.fixture.supervise
        def supervise(root, plan, stage, command, call_path):
            started = time.monotonic()
            pid = os.getpid()+12000+collector.CELLS.index(stage.name)
            try:
                result = original(root, plan, stage, command, call_path)
            finally:
                receipt = collector.read(stage / 'supervision.json')
                receipt.update(device='2', returncode=0 if receipt['ok'] else 1,
                               error=None if receipt['ok'] else {'message': 'synthetic worker failure'},
                               reserved_seconds=time.monotonic()-started)
                self.replace(stage / 'supervision.json', receipt)
                self.replace(stage / 'process.json', dict(pid=pid, pgid=pid, argv=command, device='2', timeout=600, started=started))
                data = stage / 'data'
                for name in ('isolation.json', 'backend.ready.json'):
                    path = data / name
                    if path.is_file():
                        row = collector.read(path)
                        row['pid'] = pid
                        if name == 'isolation.json':
                            row.update(pgid=pid, parent_pid=os.getpid())
                        self.replace(path, row)
                if (data / 'manifest.json').is_file():
                    self.reseal(data)
            return receipt
        with patch.object(self.fixture, 'supervise', side_effect=supervise):
            if failed:
                with self.assertRaisesRegex(RuntimeError, 'mock native load failed'):
                    self.fixture.evaluate()
            else:
                self.fixture.evaluate()

    def audit(self):
        return collector.audit(self.config, bridge, self.plan, diagnostic, self.launch)

    def finish(self, release_error=None):
        with patch.object(common, 'release_check', side_effect=release_error, return_value=({'gpu_uuid': 'GPU-mock'}, xml())):
            return collector.finish(self.config)

    def test_complete_actual_process_schema_metrics_costs_archive_and_no_retries(self):
        self.terminal()
        before = diagnostic.tree_hashes(self.root)
        result = self.finish()
        self.assertEqual(result['status'], 'COLLECTED_COMPLETE')
        self.assertTrue(result['full_release'])
        self.assertEqual(diagnostic.tree_hashes(self.root), before)
        audit = collector.read(self.output / 'audit.json')
        self.assertEqual(audit['totals']['requests'], 96)
        self.assertEqual(audit['totals']['output_token_ceiling'], 27600)
        self.assertEqual(audit['aggregate']['quiz_items_per_cell'], 24)
        for cell in collector.CELLS:
            metrics = audit['aggregate']['descriptive_event_metrics'][cell]
            self.assertEqual(metrics['totals']['quiz_items'], 24)
            self.assertEqual(metrics['totals']['executed_probes'], 12)
            self.assertEqual(metrics['totals']['allotted_record_opportunities'], 12)
        validation = collector.read(self.output / 'validation.json')
        self.assertNotIn('write_driver_sha256', self.launch)
        self.assertIn(common.digest(self.write_release), validation['files'].values())
        helper = common.load(common.COMMON, common.COMMON_SHA, 'test_archive_validator')
        with (self.output / 'metadata.tgz').open('rb') as stream:
            helper.validate_archive(stream, validation['files'], 'metadata/')
        with self.assertRaises(FileExistsError):
            self.finish()

    def test_blind_status_and_session_descendant_barrier(self):
        self.terminal()
        original = collector.read
        def blind(path):
            self.assertNotIn(Path(path).name, ('result.json', 'failure.json', 'plan.json', 'provenance.json', 'lineage.json'))
            self.assertNotIn('calls', Path(path).parts)
            return original(path)
        with patch.object(collector, 'read', side_effect=blind):
            result = collector.status(self.config)
            self.assertTrue(result['ready'])
            self.assertFalse(result['score_bodies_read'])
            with patch.object(common, 'process_snapshot', return_value=[dict(pid=9999999, pgid=4, session=result['owned_ids'][-1])]):
                with self.assertRaisesRegex(ValueError, 'all owned'):
                    self.finish()
        self.assertFalse(self.output.exists())

    def test_missing_or_ambiguous_terminal_blocks_without_output(self):
        with self.assertRaisesRegex(ValueError, 'terminal'):
            self.finish()
        self.terminal()
        common.write_json(self.root / 'run/failure.json', {'aggregate': None})
        with self.assertRaisesRegex(ValueError, 'terminal'):
            self.finish()
        self.assertFalse(self.output.exists())

    def test_partial_failed_middle_preserved_with_null_aggregate(self):
        self.terminal(failed='P_ON')
        result = self.finish()
        report = collector.read(self.output / 'audit.json')
        self.assertEqual(result['status'], 'COLLECTED_PARTIAL_NO_AGGREGATE')
        self.assertIsNone(report['aggregate'])
        self.assertIsNone(report['totals'])
        self.assertTrue(report['cells']['OFF']['verified'])
        self.assertFalse(report['cells']['A_ON']['verified'])
        self.assertIsNone(report['cells']['A_ON']['costs'])
        with tarfile.open(self.output / 'metadata.tgz') as archive:
            self.assertIn('metadata/root/run/P_ON/data/failure.json', archive.getnames())

    def test_invalid_quiz_zero_fixed24_not_valid_only(self):
        self.terminal(no_quiz=True)
        report = self.audit()
        self.assertTrue(report['verified'])
        for cell in collector.CELLS:
            metrics = report['aggregate']['descriptive_event_metrics'][cell]
            self.assertEqual(metrics['quiz_accuracy_fixed24'], 0)
            self.assertEqual(metrics['invalid_or_absent_quiz_tasks'], 4)
            self.assertEqual(metrics['totals']['quiz_items'], 24)

    def test_native_prompt_ID_tamper_resealed_fails_science(self):
        self.terminal()
        data = self.root / 'run/P_ON/data'
        path = data / 'calls/0000.response.json'
        row = collector.read(path)
        row['response']['prompt_token_ids'][0] += 1
        row['response_sha256'] = diagnostic.value_hash(row['response'])
        self.replace(path, row)
        self.reseal(data)
        report = self.audit()
        self.assertFalse(report['verified'])
        self.assertIsNone(report['aggregate'])

    def test_parent_prompt_and_wrong_worker_adapter_rejected(self):
        self.terminal()
        path = self.root / 'run/OFF.spec.json'
        spec = collector.read(path)
        spec['parent_text'] = 'forbidden'
        self.replace(path, spec)
        self.assertFalse(self.audit()['cells']['OFF']['verified'])
        path = self.root / 'run/A_ON.spec.json'
        spec = collector.read(path)
        spec['adapter'] = self.plan['lineage']['fits']['P']['adapter']
        self.replace(path, spec)
        self.assertFalse(self.audit()['cells']['A_ON']['verified'])

    def test_forged_pretry_or_faithful_metric_never_accepted(self):
        self.terminal()
        path = self.root / 'run/result.json'
        original = collector.read(path)
        for metric in ('valid_predicted_probes', 'faithful_records', 'quiz_items'):
            with self.subTest(metric=metric):
                value = copy.deepcopy(original)
                value['cells']['P_ON']['process_metrics']['totals'][metric] += 1
                self.replace(path, value)
                report = self.audit()
                self.assertFalse(report['verified'])
                self.assertIsNone(report['aggregate'])
        self.replace(path, original)
        value = dict(original, P_minus_OFF=123)
        self.replace(path, value)
        with self.assertRaisesRegex(ValueError, 'contrasts'):
            self.audit()

    def test_explicit_write_and_driver_pins_and_launch_source(self):
        self.terminal()
        wrong = dict(self.config, driver_sha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'accepted process'):
            collector.settings(wrong)
        with self.assertRaisesRegex(ValueError, 'CLI process-write'):
            collector.bind(dict(self.config, write_plan_sha256='0'*64), bridge, self.plan, self.launch)
        with self.assertRaisesRegex(ValueError, 'source/device'):
            collector.bind(self.config, bridge, self.plan, dict(self.launch, source='/wrong'))

    def test_launch_writer_pin_optional_but_never_conflicting(self):
        collector.bind(self.config, bridge, self.plan, self.launch)
        collector.bind(self.config, bridge, self.plan,
                       dict(self.launch, write_driver_sha256=self.plan['write_driver_sha256']))
        bad = dict(self.launch, write_driver_sha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'write driver pin'):
            collector.bind(self.config, bridge, self.plan, bad)
        self.replace(self.logs / 'launch.json', bad)
        config = dict(self.config, launch_sha256=common.digest(self.logs / 'launch.json'))
        with self.assertRaisesRegex(ValueError, 'launch root/driver/write/PID'):
            collector.status(config)
        with self.assertRaisesRegex(ValueError, 'CLI process-write'):
            collector.bind(dict(self.config, write_driver_sha256='0'*64), bridge, self.plan, self.launch)

    def test_recorded_write_release_path_hash_and_acceptance_are_required(self):
        self.assertEqual(collector.write_release(self.plan, self.launch), self.write_release)
        for missing in ('write_release_path', 'write_release_sha256'):
            bad = dict(self.launch)
            del bad[missing]
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, 'explicit write release'):
                collector.write_release(self.plan, bad)
        with self.assertRaisesRegex(ValueError, 'hash differs'):
            collector.write_release(self.plan, dict(self.launch, write_release_sha256='0'*64))
        with self.assertRaisesRegex(ValueError, 'sibling collection'):
            collector.write_release(self.plan, dict(self.launch,
                write_release_path=str(Path(self.plan['write_root']) / 'run/main_release.json')))
        with self.assertRaises(FileNotFoundError):
            collector.write_release(self.plan, dict(self.launch,
                write_release_path=str(self.write_release.parent.with_name('missing_collection') / 'validation.json')))
        original = collector.read(self.write_release)
        for key, value in (('status', 'COLLECTED_FAILURE_NO_AGGREGATE'), ('full_release', False),
                           ('aggregate_available', False), ('plan_sha256', '0'*64)):
            self.replace(self.write_release, dict(original, **{key: value}))
            bad = dict(self.launch, write_release_sha256=common.digest(self.write_release))
            with self.subTest(field=key), self.assertRaisesRegex(ValueError, 'acceptance/plan'):
                collector.write_release(self.plan, bad)

    def test_write_release_mutation_during_packing_fails_closed(self):
        self.terminal()
        original = common.pack
        def mutate(*args):
            result = original(*args)
            self.replace(self.write_release, dict(collector.read(self.write_release), changed=True))
            return result
        with patch.object(common, 'pack', side_effect=mutate), self.assertRaisesRegex(ValueError, 'write release hash'):
            self.finish()
        self.assertTrue((self.output / 'failure.json').exists())
        self.assertFalse((self.output / 'validation.json').exists())

    def test_write_adapter_mutation_leaves_failed_attempt_not_valid_archive(self):
        self.terminal()
        path = Path(self.plan['lineage']['fits']['P']['adapter']) / 'adapter_model.safetensors'
        with path.open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaises(ValueError):
            self.finish()
        self.assertTrue((self.output / 'failure.json').is_file())
        self.assertFalse((self.output / 'validation.json').exists())

    def test_foreign_queue_or_GPU_refusal_no_kills_no_aggregate(self):
        self.terminal()
        with patch.object(os, 'kill', side_effect=AssertionError('no killing')), \
             patch.object(os, 'killpg', side_effect=AssertionError('no killing')):
            result = self.finish(RuntimeError('foreign reservation/queue requires reconciliation'))
        self.assertFalse(result['full_release'])
        self.assertIsNone(collector.read(self.output / 'audit.json')['aggregate'])

    def test_controller_worker_call_limits_and_freshness(self):
        self.terminal()
        for relative, key, value in [('OFF/process.json', 'timeout', 601),
                                     ('P_ON/data/isolation.json', 'parent_pid', -1),
                                     ('A_ON/data/backend.ready.json', 'ready', -1)]:
            with self.subTest(relative=relative):
                path = self.root / 'run' / relative
                row = collector.read(path)
                self.replace(path, dict(row, **{key: value}))
                self.assertFalse(self.audit()['verified'])
                self.replace(path, row)
        path = self.root / 'run/result.json'
        row = collector.read(path)
        self.replace(path, dict(row, controller_seconds=1801))
        with self.assertRaisesRegex(ValueError, 'bounded three-cell'):
            self.audit()

    def test_mutation_during_collection_never_validated(self):
        self.terminal()
        original = collector.audit
        def changed(*args):
            result = original(*args)
            common.write_json(self.root / 'run/late.json', {})
            return result
        with patch.object(collector, 'audit', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'metadata changed'):
                self.finish()
        self.assertFalse((self.output / 'validation.json').exists())

    def test_external_expiry_not_swallowed_and_timer_restored(self):
        self.terminal()
        with patch.object(collector, 'audit', side_effect=common.CollectionExpired('deadline')):
            with self.assertRaises(common.CollectionExpired):
                self.finish()
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        self.assertTrue((self.output / 'failure.json').is_file())
        self.assertFalse((self.output / 'validation.json').exists())

    def test_collection_never_loads_backend_fits_or_exports_targets(self):
        self.terminal()
        with patch.object(diagnostic, 'NativeBackend', side_effect=AssertionError('no model rerun')), \
             patch.object(readout_tests.writes.bridge, 'load_native', side_effect=AssertionError('no training load')), \
             patch.object(readout_tests.writes.exporter, 'build_process_pair', side_effect=AssertionError('no targets')), \
             patch.object(readout_tests.writes.exporter, 'export_pair', side_effect=AssertionError('no export')):
            self.assertEqual(self.finish()['status'], 'COLLECTED_COMPLETE')

    def test_archive_changed_after_pack_not_certified(self):
        self.terminal()
        original = common.pack
        def tampered(path, files, hashes):
            checksum = original(path, files, hashes)
            with path.open('ab') as stream:
                stream.write(b'changed')
            return checksum
        with patch.object(common, 'pack', side_effect=tampered):
            with self.assertRaisesRegex(ValueError, 'validated archive changed'):
                self.finish()
        self.assertFalse((self.output / 'validation.json').exists())


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='process-readout-collect-', dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root, self.logs = Path(self.temp.name) / 'root', Path(self.temp.name) / 'launch'
        self.root.mkdir()
        self.logs.mkdir()
        common.write_json(self.root / 'plan.json', {'safe': True})

    def test_weight_exclusion_and_unknown_or_secret_rejection(self):
        common.write_new(self.root / 'weights.safetensors', b'never archive')
        files, hashes, excluded = common.inventory(self.root, self.logs)
        self.assertEqual(excluded, ['metadata/root/weights.safetensors'])
        self.assertNotIn('metadata/root/weights.safetensors', hashes)
        for text in (b'{"access_token":"hidden"}', b'{"text":"hf_012345678901234567890123"}'):
            with self.assertRaisesRegex(ValueError, 'credential'):
                common.scan_text(text, 'metadata/root/log.json')
        common.scan_text(b'{"native_output_tokens":42}', 'usage.json')
        common.write_new(self.root / 'unknown.dat', b'?')
        with self.assertRaisesRegex(ValueError, 'unknown metadata'):
            common.inventory(self.root, self.logs)

    def test_symlink_hardlink_special_and_size_limits(self):
        link = self.root / 'link.json'
        link.symlink_to(self.root / 'plan.json')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            common.inventory(self.root, self.logs)
        link.unlink()
        os.link(self.root / 'plan.json', link)
        with self.assertRaisesRegex(ValueError, 'hardlinked'):
            common.payload(link)
        link.unlink()
        os.mkfifo(link)
        with self.assertRaisesRegex(ValueError, 'special'):
            common.payload(link)
        link.unlink()
        with patch.object(common, 'MAX_TOTAL', 1):
            with self.assertRaisesRegex(ValueError, 'byte bound'):
                common.inventory(self.root, self.logs)
        with self.assertRaisesRegex(ValueError, 'oversized'):
            common.payload(self.root / 'plan.json', limit=1)

    def test_safe_archive_hash_validation_and_exclusive_creation(self):
        files, hashes, excluded = common.inventory(self.root, self.logs)
        archive = Path(self.temp.name) / 'metadata.tgz'
        self.assertEqual(common.pack(archive, files, hashes), common.file_hash(archive))
        with self.assertRaises(FileExistsError):
            common.pack(archive, files, hashes)
        helper = common.load(common.COMMON, common.COMMON_SHA, 'malicious_archive_test')
        for name, kind in [('../escape', tarfile.REGTYPE), ('metadata/link', tarfile.SYMTYPE)]:
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w:gz') as archive:
                member = tarfile.TarInfo(name)
                member.size, member.type = 2, kind
                archive.addfile(member, io.BytesIO(b'{}'))
            stream.seek(0)
            with self.assertRaises(ValueError):
                helper.validate_archive(stream, {}, 'metadata/')

    def test_full_release_helper_UUID_occupancy_and_unmasked_requirement(self):
        checker = SimpleNamespace(check_free=lambda device: ({'gpu_uuid': 'GPU-mock'}, xml()))
        with patch.object(common, 'load', return_value=checker), patch.dict(os.environ, {}, clear=True):
            common.release_check({'source_root': str(self.root), 'device': '2'}, 'GPU-mock')
            with self.assertRaisesRegex(ValueError, 'UUID'):
                common.release_check({'source_root': str(self.root), 'device': '2'}, 'wrong')
            checker.check_free = lambda device: ({'gpu_uuid': 'GPU-mock'}, xml(processes='<process_info/>'))
            with self.assertRaises(ValueError):
                common.release_check({'source_root': str(self.root), 'device': '2'}, 'GPU-mock')

    def test_bootstrap_pin_and_special_file_fail_before_execution(self):
        source = self.root / 'helper.py'
        common.write_new(source, b'raise AssertionError("must not execute")\n')
        with patch.object(collector, 'BASE', source):
            with self.assertRaisesRegex(ValueError, 'helper changed'):
                collector.common_module()
        source.unlink()
        os.mkfifo(source)
        with patch.object(collector, 'BASE', source):
            with self.assertRaisesRegex(ValueError, 'unsafe'):
                collector.common_module()

    def test_raw_role_and_call_deadline_bound(self):
        data = self.root / 'data'
        (data / 'calls').mkdir(parents=True)
        request_path, response_path = data / 'calls/0000.request.json', data / 'calls/0000.response.json'
        common.write_json(request_path, {'request': {'role': 'wake', 'max_tokens': 400}, 'started': 10})
        common.write_json(response_path, {'response': {'prompt_token_ids': [1], 'output_token_ids': [2]}, 'ended': 131})
        with self.assertRaisesRegex(ValueError, 'call bound'):
            collector.raw_cost(data, {'started': 1}, {'ready': 5}, {'reserved_seconds': 600})
        request_path.unlink()
        common.write_json(request_path, {'request': {'role': 'parent', 'max_tokens': 200}, 'started': 10})
        response_path.unlink()
        common.write_json(response_path, {'response': {'prompt_token_ids': [1], 'output_token_ids': [2]}, 'ended': 11})
        with self.assertRaisesRegex(ValueError, 'parent/unknown'):
            collector.raw_cost(data, {'started': 1}, {'ready': 5}, {'reserved_seconds': 600})
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='2'):
            with self.assertRaisesRegex(ValueError, 'unset'):
                common.release_check({'source_root': str(self.root), 'device': '2'}, 'GPU-mock')


if __name__ == '__main__':
    unittest.main()
