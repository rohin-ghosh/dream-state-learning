"""CPU mocks only. Synthetic score receipts; no native/GPU/SSH/network/Git."""
import copy
import datetime as dt
import importlib.util
import io
import json
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
import test_astra_rulegame_record_acquisition_20260912 as acquisition

PATH = Path('/tmp/astra_rulegame_record_acquisition_collect_20260912.py')
spec = importlib.util.spec_from_file_location('acquisition_collector_tests', PATH)
collector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = collector
spec.loader.exec_module(collector)
bridge, diagnostic = acquisition.bridge, acquisition.diagnostic


def xml(uuid='GPU-mock', processes=''):
    return f'<nvidia_smi_log><gpu><uuid>{uuid}</uuid><processes>{processes}</processes></gpu></nvidia_smi_log>'


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = acquisition.AcquisitionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.prepare()
        self.root = self.fixture.output
        self.logs = self.root.with_name('acquisition_launch')
        self.logs.mkdir()
        self.out = self.root.with_name('acquisition_collection')
        self.plan = collector.read(self.root / 'plan.json')
        release = Path(self.plan['write_root']) / 'run/main_release.json'
        collector.write_json(release, dict(full_release=True, synthetic=True))
        self.launch = dict(root=str(self.root), plan_sha256=self.fixture.prepared['plan_sha256'],
                           driver_sha256=collector.DRIVER_SHA, pid=os.getpid(), device='2', gpu=dict(gpu_uuid='GPU-mock'),
                           started_utc=dt.datetime.fromtimestamp(time.time()-10, dt.timezone.utc).isoformat(),
                           command=[self.plan['python'], '-B', str(collector.DRIVER), 'run', '--root', str(self.root),
                                    '--plan-sha256', self.fixture.prepared['plan_sha256'], '--allow-gpu'])
        self.launch.update(source=self.plan['source_root'], write_plan_sha256=self.plan['write_plan_sha256'],
                           write_release_sha256=collector.digest(release), launcher_sha256=collector.LAUNCHER_SHA,
                           phase='trained_record_acquisition', continuous_reservation=True, controller_seconds=1800,
                           cleanup_reserve=140, worker_cap_seconds=600, external_collection_margin_seconds=300,
                           requests=24, candidate_forwards=48, generations=0, updates=0, cells=list(collector.CELLS),
                           adaptation_test=False, model_origin='UNRESOLVED_LOCAL_HASHES_ONLY')
        collector.write_json(self.logs / 'launch.json', self.launch)
        collector.write_new(self.logs / 'gpu.xml', xml().encode())
        collector.write_new(self.logs / 'stdout.log', b'Synthetic launcher log\n')
        self.kwargs = dict(root=self.root, plan_sha256=self.fixture.prepared['plan_sha256'], launch_root=self.logs,
                           launch_sha256=collector.digest(self.logs / 'launch.json'), out=self.out)
        loader = collector.load
        def load(path, checksum, name):
            if Path(path) == collector.DRIVER:
                self.assertEqual(collector.digest(path), checksum)
                return bridge
            return loader(path, checksum, name)
        for context in (patch.object(collector, 'load', side_effect=load),
                        patch.object(collector, 'process_snapshot', return_value=[]),
                        patch.object(diagnostic, 'native_tokenizer', return_value=self.fixture.tokenizer)):
            context.start()
            self.addCleanup(context.stop)

    def replace(self, path, value):
        self.fixture.fixture.replace_json(path, value)

    def terminal(self, failed=None):
        self.fixture.fail_cell = failed
        original = self.fixture.supervise
        def supervise(root, plan, stage, command, call_path):
            started = time.monotonic()
            pid = os.getpid()+10000+collector.CELLS.index(stage.name)
            try:
                result = original(root, plan, stage, command, call_path)
            finally:
                receipt = collector.read(stage / 'supervision.json')
                receipt.update(device='2', returncode=0 if receipt['ok'] else 1,
                               owned_group_empty=True, gpu_processes_absent=True,
                               error=None if receipt['ok'] else {'message': 'synthetic load failure'},
                               reserved_seconds=time.monotonic()-started)
                self.replace(stage / 'supervision.json', receipt)
                self.replace(stage / 'process.json', dict(pid=pid, pgid=pid, argv=command,
                             device='2', timeout=600, started=started))
                data = stage / 'data'
                for name in ('isolation.json', 'backend.ready.json'):
                    path = data / name
                    if path.is_file():
                        row = collector.read(path)
                        row['pid'] = pid
                        if name == 'isolation.json':
                            row.update(pgid=pid, parent_pid=os.getpid())
                        else:
                            row['runtime'] = dict(loader='conditional_behavior_readout.HFScorer',
                                scorer='semantic_carrier_diagnostic.score', training=False, trainable_parameters=0,
                                adapter_count=0 if stage.name == 'OFF' else 1, use_cache=False,
                                parameter_count=128, dtypes=['torch.bfloat16'], load_dtype='bf16', attention='eager', generation=False)
                        self.replace(path, row)
                if (data / 'manifest.json').is_file():
                    self.reseal(stage.name)
            return receipt
        with patch.object(self.fixture, 'supervise', side_effect=supervise):
            if failed:
                with self.assertRaisesRegex(RuntimeError, 'mock scoring failure'):
                    self.fixture.run_all()
            else:
                self.fixture.run_all()

    def reseal(self, cell):
        data = self.root / 'run' / cell / 'data'
        self.replace(data / 'manifest.json', {'files': diagnostic.tree_hashes(data, ('manifest.json',))})

    def audit(self):
        return collector.audit(bridge, self.root, self.plan, diagnostic, self.launch)

    def finish(self, release_error=None):
        with patch.object(collector, 'release_check', side_effect=release_error,
                          return_value=({'gpu_uuid': 'GPU-mock'}, xml())):
            return collector.finish(**self.kwargs)

    def test_end_to_end_complete_raw_replay_archive_and_no_overwrite(self):
        self.terminal()
        before = diagnostic.tree_hashes(self.root)
        result = self.finish()
        self.assertEqual(result['status'], 'COLLECTED_COMPLETE')
        self.assertEqual(diagnostic.tree_hashes(self.root), before)
        audit = collector.read(self.out / 'audit.json')
        self.assertEqual([audit['totals'][key] for key in ('requests', 'candidate_forwards', 'generations')], [24, 48, 0])
        self.assertEqual(audit['aggregate'], bridge.summarize({cell: bridge.replay(self.root, self.plan, cell) for cell in collector.CELLS}))
        validation = collector.read(self.out / 'validation.json')
        common = collector.load(collector.COMMON, collector.COMMON_SHA, 'test_common')
        with (self.out / 'metadata.tgz').open('rb') as stream:
            common.validate_archive(stream, validation['files'], 'metadata/')
        with self.assertRaises(FileExistsError):
            self.finish()

    def test_status_and_live_session_are_blind_to_scores(self):
        self.terminal()
        original = collector.read
        def blind(path):
            self.assertNotIn(Path(path).name, ('result.json', 'failure.json', 'plan.json', 'reduction.json'))
            self.assertNotIn('calls', Path(path).parts)
            return original(path)
        with patch.object(collector, 'read', side_effect=blind):
            observed = collector.status(**{key: value for key, value in self.kwargs.items() if key != 'out'})
            self.assertTrue(observed['ready'])
            self.assertFalse(observed['score_bodies_read'])
            owned = observed['owned_ids'][-1]
            with patch.object(collector, 'process_snapshot', return_value=[dict(pid=owned+7, pgid=3, session=owned)]):
                with self.assertRaisesRegex(ValueError, 'all owned sessions absent'):
                    self.finish()
        self.assertFalse(self.out.exists())

    def test_no_terminal_or_ambiguous_terminal_blocks_before_output(self):
        with self.assertRaisesRegex(ValueError, 'terminal'):
            self.finish()
        self.terminal()
        collector.write_json(self.root / 'run/failure.json', {'aggregate': None})
        with self.assertRaisesRegex(ValueError, 'terminal'):
            self.finish()
        self.assertFalse(self.out.exists())

    def test_failed_middle_cell_preserves_capture_without_aggregate(self):
        self.terminal('P')
        result = self.finish()
        report = collector.read(self.out / 'audit.json')
        self.assertEqual(result['status'], 'COLLECTED_PARTIAL_NO_AGGREGATE')
        self.assertTrue(report['cells']['OFF']['verified'])
        self.assertFalse(report['cells']['P']['verified'])
        self.assertIsNone(report['aggregate'])
        self.assertIsNone(report['totals'])
        with tarfile.open(self.out / 'metadata.tgz') as archive:
            self.assertIn('metadata/root/run/P/data/failure.json', archive.getnames())

    def test_foreign_occupancy_or_queue_never_killed_and_no_aggregate(self):
        self.terminal()
        with patch.object(os, 'kill', side_effect=AssertionError('collector must never kill')), \
             patch.object(os, 'killpg', side_effect=AssertionError('collector must never kill')):
            result = self.finish(RuntimeError('foreign reservation or queue requires reconciliation'))
        self.assertFalse(result['full_release'])
        self.assertIsNone(collector.read(self.out / 'audit.json')['aggregate'])
        self.assertFalse(collector.read(self.out / 'release.json')['full_release'])

    def test_tampered_forward_and_extra_generation_receipt_reject_science(self):
        self.terminal()
        path = self.root / 'run/P/data/calls/0000.response.json'
        row = collector.read(path)
        row['response']['native_forwards'][0]['input_ids'][0][0] += 1
        row['response_sha256'] = diagnostic.value_hash(row['response'])
        self.replace(path, row)
        self.reseal('P')
        report = self.audit()
        self.assertFalse(report['verified'])
        self.assertIsNone(report['aggregate'])
        path = self.root / 'run/A/data/calls/0000.response.json'
        row = collector.read(path)
        row['response']['generation'] = 'not permitted'
        row['response_sha256'] = diagnostic.value_hash(row['response'])
        self.replace(path, row)
        self.reseal('A')
        self.assertFalse(self.audit()['cells']['A']['verified'])

    def test_adapter_and_plan_mutations_fail_closed_preserve_attempt(self):
        self.terminal()
        path = self.root / 'plan.json'
        plan = collector.read(path)
        plan['device'] = '3'
        self.replace(path, plan)
        with self.assertRaisesRegex(ValueError, 'plan changed'):
            self.finish()
        self.assertTrue((self.out / 'failure.json').is_file())
        self.assertFalse((self.out / 'validation.json').exists())

    def test_controller_native_runtime_call_and_selection_receipts(self):
        self.terminal()
        for relative, key, value in [('OFF/process.json', 'timeout', 601),
                                     ('P/data/isolation.json', 'parent_pid', -1),
                                     ('A/data/backend.ready.json', 'ready', -1)]:
            with self.subTest(relative=relative):
                path = self.root / 'run' / relative
                original = collector.read(path)
                row = copy.deepcopy(original)
                row[key] = value
                self.replace(path, row)
                self.assertFalse(self.audit()['verified'])
                self.replace(path, original)
        path = self.root / 'run/result.json'
        row = collector.read(path)
        row['requests'] = 23
        self.replace(path, row)
        with self.assertRaisesRegex(ValueError, '24/48/0'):
            self.audit()

    def test_post_audit_mutation_prevents_validated_capsule(self):
        self.terminal()
        original = collector.audit
        def mutate(*args):
            report = original(*args)
            collector.write_json(self.root / 'run/late.json', {})
            return report
        with patch.object(collector, 'audit', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'metadata changed'):
                self.finish()
        self.assertFalse((self.out / 'validation.json').exists())

    def test_expiry_not_swallowed_as_audit_failure(self):
        self.terminal()
        with patch.object(collector, 'audit', side_effect=collector.CollectionExpired('synthetic deadline')):
            with self.assertRaises(collector.CollectionExpired):
                self.finish()
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        self.assertTrue((self.out / 'failure.json').is_file())
        self.assertFalse((self.out / 'validation.json').exists())

    def test_actual_saved_adapter_mutation_blocks_lineage(self):
        self.terminal()
        fit = self.plan['lineage']['fits']['P']
        adapter = Path(fit['adapter'])
        path = next(adapter.glob('*.safetensors'))
        with path.open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaises(ValueError):
            self.finish()
        self.assertFalse((self.out / 'validation.json').exists())

    def test_missing_call_cannot_be_replaced_by_reduction(self):
        self.terminal()
        (self.root / 'run/A/data/calls/0007.response.json').unlink()
        self.reseal('A')
        report = self.audit()
        self.assertFalse(report['verified'])
        self.assertIsNone(report['aggregate'])

    def test_native_reencoding_failure_archives_but_never_reports_science(self):
        self.terminal()
        with patch.object(diagnostic, 'native_tokenizer', side_effect=ValueError('offset/native mismatch')):
            result = self.finish()
        self.assertEqual(result['status'], 'COLLECTED_PARTIAL_NO_AGGREGATE')
        self.assertIsNone(collector.read(self.out / 'audit.json')['aggregate'])

    def test_launch_and_write_release_custody(self):
        self.terminal()
        for key, value in [('generations', 1), ('launcher_sha256', '0'*64), ('source', '/wrong')]:
            with self.subTest(key=key):
                launch = dict(self.launch, **{key: value})
                with self.assertRaises(ValueError):
                    collector.bind_launch(self.root, self.logs, self.plan, launch)
        path = Path(self.plan['write_root']) / 'run/main_release.json'
        self.replace(path, dict(full_release=False))
        with self.assertRaisesRegex(ValueError, 'write release'):
            self.finish()


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='acquisition-collector-test-', dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root'
        self.logs = Path(self.temp.name) / 'launch'
        self.root.mkdir()
        self.logs.mkdir()
        collector.write_json(self.root / 'plan.json', {'safe': True})

    def test_weight_exclusion_without_reading_and_unknown_type_rejected(self):
        collector.write_new(self.root / 'model.safetensors', b'weight bytes')
        files, hashes, excluded = collector.inventory(self.root, self.logs)
        self.assertEqual(excluded, ['metadata/root/model.safetensors'])
        self.assertNotIn('metadata/root/model.safetensors', hashes)
        collector.write_new(self.root / 'unrecognized.dat', b'unknown')
        with self.assertRaisesRegex(ValueError, 'unknown metadata'):
            collector.inventory(self.root, self.logs)

    def test_symlinks_and_hardlinks_and_fifo_rejected(self):
        path = self.root / 'alias.json'
        path.symlink_to(self.root / 'plan.json')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            collector.inventory(self.root, self.logs)
        path.unlink()
        os.link(self.root / 'plan.json', path)
        with self.assertRaisesRegex(ValueError, 'hardlinked'):
            collector.payload(path)
        path.unlink()
        os.mkfifo(path)
        with self.assertRaisesRegex(ValueError, 'special'):
            collector.payload(path)

    def test_bounded_inventory_and_duplicate_json(self):
        with patch.object(collector, 'MAX_TOTAL', 1):
            with self.assertRaisesRegex(ValueError, 'byte bound'):
                collector.inventory(self.root, self.logs)
        with patch.object(collector, 'MAX_FILES', 0):
            with self.assertRaisesRegex(ValueError, 'count bound'):
                collector.inventory(self.root, self.logs)
        with self.assertRaisesRegex(ValueError, 'oversized'):
            collector.payload(self.root / 'plan.json', limit=1)
        collector.write_new(self.root / 'duplicate.json', b'{"key":1,"key":2}')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            collector.read(self.root / 'duplicate.json')

    def test_credential_rejection_without_redaction_or_token_false_positive(self):
        for value in (b'{"access_token":"hidden"}', b'{"nested":{"password":"hidden"}}',
                      b'{"text":"hf_012345678901234567890123"}'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'credential'):
                collector.scan_text(value, 'safe.json')
        collector.scan_text(b'{"scored_target_tokens":22,"token_logprobs":[-0.5]}', 'scores.json')

    def test_archive_validation_rejects_traversal_duplicates_links_and_wrong_hash(self):
        common = collector.load(collector.COMMON, collector.COMMON_SHA, 'safety_common')
        for name, kind, duplicate in [('../escape', tarfile.REGTYPE, False),
                                      ('metadata/a.json', tarfile.SYMTYPE, False),
                                      ('metadata/a.json', tarfile.REGTYPE, True),
                                      ('metadata/a.json', tarfile.REGTYPE, False)]:
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w:gz') as archive:
                for index in range(2 if duplicate else 1):
                    member = tarfile.TarInfo(name)
                    member.size, member.type = 2, kind
                    archive.addfile(member, io.BytesIO(b'{}'))
            stream.seek(0)
            with self.subTest(name=name, kind=kind, duplicate=duplicate), self.assertRaises(ValueError):
                common.validate_archive(stream, {'metadata/a.json': 'wrong'}, 'metadata/')

    def test_full_release_uuid_proc_queue_helper_and_no_visibility_mask(self):
        checker = SimpleNamespace(check_free=lambda device: ({'gpu_uuid': 'GPU-mock'}, xml()))
        plan = dict(source_root=str(self.root), device='2')
        with patch.object(collector, 'load', return_value=checker), patch.dict(os.environ, {}, clear=True):
            self.assertEqual(collector.release_check(plan, 'GPU-mock')[0]['gpu_uuid'], 'GPU-mock')
            with self.assertRaisesRegex(ValueError, 'UUID'):
                collector.release_check(plan, 'GPU-wrong')
            checker.check_free = lambda device: ({'gpu_uuid': 'GPU-mock'}, xml(processes='<process_info/>'))
            with self.assertRaisesRegex(ValueError, 'process'):
                collector.release_check(plan, 'GPU-mock')
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='2'):
            with self.assertRaisesRegex(ValueError, 'unset'):
                collector.release_check(plan, 'GPU-mock')

    def test_tampered_source_dependency_not_executed(self):
        path = self.root / 'helper.py'
        collector.write_new(path, b'raise AssertionError("must not execute")\n')
        with self.assertRaisesRegex(ValueError, 'dependency hash'):
            collector.load(path, '0'*64, 'untrusted_helper')

    def test_pack_returns_validated_hash_and_rejects_stale_payload(self):
        files, hashes, excluded = collector.inventory(self.root, self.logs)
        path = Path(self.temp.name) / 'metadata.tgz'
        self.assertEqual(collector.pack(path, files, hashes), collector.file_hash(path))
        with self.assertRaises(FileExistsError):
            collector.pack(path, files, hashes)
        with (self.root / 'plan.json').open('ab') as stream:
            stream.write(b' ')
        with self.assertRaisesRegex(ValueError, 'metadata changed'):
            collector.pack(Path(self.temp.name) / 'partial.tgz', files, hashes)


if __name__ == '__main__':
    unittest.main()
