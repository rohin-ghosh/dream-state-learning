"""CPU mock custody/release checks; no model, tokenizer, GPU query, network or SSH."""
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import signal
import struct
import sys
import tarfile
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


collector = module('/tmp/astra_rulegame_process_write_collect_20260912.py', 'process_collect_test_target')
writer_tests = module('/tmp/test_astra_rulegame_process_write_20260912.py', 'process_collect_writer_fixtures')
diagnostic, writer = writer_tests.diagnostic, writer_tests.bridge


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = writer_tests.BridgeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.prepare()
        self.fixture.run_pair()
        self.root = self.fixture.output
        self.plan_sha = self.fixture.prepared['plan_sha256']
        self.plan = diagnostic.read(self.root/'plan.json')
        self.logs = self.root.with_name(self.root.name+'_launch')
        self.logs.mkdir()
        self.output = self.root.with_name(self.root.name+'_collection')
        self.gpu = dict(gpu_uuid='GPU-cpu-fixture-only', reconciled_system_services=[])
        self.xml = '<nvidia_smi_log><gpu><uuid>GPU-cpu-fixture-only</uuid><processes /></gpu></nvidia_smi_log>'
        self.controller_pid, self.worker_pids = 81001, {'P': 81002, 'A': 81003}
        self.controller = diagnostic.read(self.root/'run/controller.json')
        self.controller.update(pid=self.controller_pid, started_wall=time.time()-90)
        self.controller['hard_end'] = min(self.controller['started_wall']+1200, self.plan['deadline'], self.plan['lease_cutoff'])
        self.replace(self.root/'run/controller.json', self.controller)
        result = diagnostic.read(self.root/'run/result.json')
        result['controller_seconds'] = 70.
        for index, arm in enumerate(collector.ARMS):
            launch_path = self.root/'run'/f'{arm}.launch.json'
            launch = diagnostic.read(launch_path)
            launch.update(controller_pid=self.controller_pid, hard_end=self.controller['hard_end'])
            self.replace(launch_path, launch)
            stage, fit = self.root/'run'/arm, self.root/'fits'/arm
            self.replace(stage/'process.json', dict(pid=self.worker_pids[arm], pgid=self.worker_pids[arm], device='2',
                timeout=600, started=time.monotonic()-80+index*20, argv=launch['command']))
            self.replace(stage/'supervision.json', dict(ok=True, returncode=0, error=None, device='2', owned_group_empty=True,
                gpu_processes_absent=True, reservation_release_verified=True, reserved_seconds=10.))
            self.replace(fit/'attempt.json', dict(arm=arm, plan_sha256=self.plan_sha, init_adapter=None, pid=self.worker_pids[arm]))
            self.replace(fit/'manifest.json', dict(files=diagnostic.tree_hashes(fit, ('manifest.json',))))
            result['arms'][arm].update(fit_manifest_sha256=writer.digest(fit/'manifest.json'),
                supervision_sha256=writer.digest(stage/'supervision.json'))
        self.replace(self.root/'run/result.json', result)
        launch = dict(status='LAUNCHED_NOT_COMPLETED', pid=self.controller_pid, started_utc=writer_tests.iso(self.controller['started_wall']-1),
            node=3, device='2', phase='process_v2_context_distillation_write', source=self.plan['source_root'],
            root=str(self.root), plan_sha256=self.plan_sha, driver_sha256=collector.DRIVER_SHA, launcher_sha256=collector.LAUNCHER_SHA,
            native_cpu_sha256='a'*64, continuous_reservation=True, controller_seconds=1200, cleanup_reserve=140, worker_cap_seconds=600,
            external_collection_margin_seconds=300, arms=['P','A'], seed=2, fresh_base=True, updates_per_arm=12, model_origin=collector.ORIGIN,
            adaptation_test=False, gpu=self.gpu,
            command=[self.plan['python'], '-B', str(collector.DRIVER), 'write', '--root', str(self.root), '--plan-sha256', self.plan_sha, '--allow-gpu'])
        self.replace(self.logs/'launch.json', launch)
        (self.logs/'gpu.xml').write_text(self.xml)
        (self.logs/'controller.log').write_text('CPU fixture only\n')
        self.launch_sha = collector.digest(self.logs/'launch.json')
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in dict(PLAN_SHA=self.plan_sha, ROOT_NAME=self.root.name, SOURCE_ID=Path(self.plan['source_root']).name,
                EXPECTED_TOKENS={arm: {key:self.plan['tokens'][arm]['tokens'][key] for key in ('total','target')} for arm in collector.ARMS}).items():
            self.stack.enter_context(patch.object(collector, name, value))
        self.snapshot = self.stack.enter_context(patch.object(collector, 'process_snapshot', return_value=[]))
        self.vacancy = self.stack.enter_context(patch.object(collector, 'vacancy', return_value=(self.gpu,self.xml)))
        self.stack.enter_context(patch.object(diagnostic, 'native_tokenizer', side_effect=AssertionError('collector must not load tokenizer')))
        self.stack.enter_context(patch.dict(os.environ, {}, clear=False))
        os.environ.pop('CUDA_VISIBLE_DEVICES', None)

    def replace(self, path, value):
        Path(path).write_bytes(writer.encoded(value))

    def collect(self):
        return collector.finish(root=self.root, plan_sha256=self.plan_sha, launch_root=self.logs,
            launch_sha256=self.launch_sha, out=self.output)

    def status(self):
        return collector.status(self.root, self.plan_sha, self.logs, self.launch_sha)

    def test_complete_metadata_finite_two_fits_release_no_weights_or_raw_teacher(self):
        before = diagnostic.tree_hashes(self.root)
        result = self.collect()
        self.assertEqual(result['status'], 'COLLECTED_PAIRED_WRITE')
        self.assertTrue(result['full_release'] and result['aggregate_available'])
        self.assertFalse(result['weights_in_capsule'])
        report = collector.read(self.output/'audit.json')
        self.assertEqual(report['aggregate']['optimizer_updates'], 24)
        self.assertTrue(all(report['arms'][arm]['finite_weights']['finite'] for arm in collector.ARMS))
        self.assertEqual(self.vacancy.call_count, 2)
        with tarfile.open(result['archive']) as archive:
            names = archive.getnames()
            self.assertNotIn('metadata/run/material/audit/candidate.json', names)
            self.assertFalse(any(name.endswith('.safetensors') or '/corpora/' in name or name.endswith('.tokens.json') for name in names))
            self.assertIn('metadata/collection/material_summary.json', names)
        self.assertEqual(before, diagnostic.tree_hashes(self.root))
        collector.validate_archive(Path(result['archive']), collector.read(self.output/'validation.json')['files'])

    def test_status_does_not_open_terminal_or_load_writer_or_query_gpu(self):
        original = collector.read
        def safe(path):
            self.assertNotIn(Path(path).name, ('result.json', 'failure.json', 'receipt.json'))
            return original(path)
        with patch.object(collector, 'read', side_effect=safe), patch.object(collector, 'load', side_effect=AssertionError('no source load')):
            self.assertTrue(self.status()['ready'])
        self.vacancy.assert_not_called()

    def test_pid_group_session_descendant_and_pid_reuse_block_before_reads(self):
        for row in (dict(pid=self.controller_pid, ppid=1, pgid=1, session=1),
                    dict(pid=90000, ppid=1, pgid=self.worker_pids['A'], session=9),
                    dict(pid=90000, ppid=1, pgid=9, session=self.worker_pids['P']),
                    dict(pid=90000, ppid=self.controller_pid, pgid=9, session=9)):
            with self.subTest(row=row):
                self.snapshot.return_value = [row]
                self.assertFalse(self.status()['ready'])
                with patch.object(collector, 'bind', side_effect=AssertionError('live fits must not be read')), self.assertRaisesRegex(ValueError, 'whole owned'):
                    self.collect()
                self.assertFalse(self.output.exists())

    def test_missing_or_double_terminal_no_output(self):
        terminal = self.root/'run/result.json'
        value = terminal.read_bytes()
        terminal.unlink()
        with self.assertRaisesRegex(ValueError, 'whole owned'):
            self.collect()
        terminal.write_bytes(value)
        self.replace(self.root/'run/failure.json', dict(status='FAILED'))
        with self.assertRaisesRegex(ValueError, 'whole owned'):
            self.collect()
        self.assertFalse(self.output.exists())

    def test_unknown_clean_json_and_weight_file_fail(self):
        for name in ('surprise.json', 'extra.safetensors'):
            path = self.root/name
            path.write_text('{}')
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'unknown metadata'):
                collector.inventory(self.root, self.logs)
            path.unlink()

    def test_known_file_with_credential_rejected_before_archive(self):
        (self.logs/'controller.log').write_text('HF_TOKEN=hf_'+'x'*32)
        with self.assertRaisesRegex(ValueError, 'credential'):
            self.collect()
        self.assertTrue((self.output/'failure.json').is_file())
        self.assertFalse((self.output/'metadata.tgz').exists())

    def test_actual_native_counts_wrong_even_when_other_plan_contracts_pass(self):
        with patch.object(collector, 'EXPECTED_TOKENS', {'P':{'total':760,'target':32},'A':{'total':758,'target':31}}), \
             self.assertRaisesRegex(ValueError, 'actual native input/target'):
            self.collect()

    def test_wrong_plan_and_launch_hash_refuse_before_output(self):
        with self.assertRaisesRegex(ValueError, 'wrong Main'):
            collector.status(self.root, 'f'*64, self.logs, self.launch_sha)
        with self.assertRaisesRegex(ValueError, 'launch hash'):
            collector.status(self.root, self.plan_sha, self.logs, 'f'*64)
        self.assertFalse(self.output.exists())

    def test_wrong_launcher_protocol_or_source_fails(self):
        path = self.logs/'launch.json'
        launch = collector.read(path)
        launch['fresh_base'] = False
        self.replace(path, launch)
        self.launch_sha = collector.digest(path)
        with self.assertRaisesRegex(ValueError, 'launcher protocol'):
            self.collect()

    def test_missing_second_fit_never_produces_aggregate(self):
        (self.root/'fits/A/receipt.json').unlink()
        with self.assertRaisesRegex(ValueError, 'completed arm missing'):
            self.collect()
        self.assertFalse((self.output/'audit.json').exists())
        self.vacancy.assert_not_called()

    def test_wrong_saved_fit_and_forward_receipt_fails(self):
        path = self.root/'fits/A/forwards/0001.json'
        receipt = collector.read(path)
        receipt['batch_exposure']['full_target_tokens'] += 1
        self.replace(path, receipt)
        with self.assertRaisesRegex(ValueError, 'sealed fit changed'):
            self.collect()
        self.assertFalse((self.output/'audit.json').exists())

    def test_bad_cleanup_or_worker_bound_fails(self):
        path = self.root/'run/P/supervision.json'
        receipt = collector.read(path)
        receipt['reservation_release_verified'] = False
        self.replace(path, receipt)
        with self.assertRaisesRegex(ValueError, 'worker cleanup'):
            self.collect()

    def test_forged_worker_parent_and_attempt_identity_fails(self):
        path = self.root/'run/P.launch.json'
        launch = collector.read(path)
        launch['controller_pid'] += 1
        self.replace(path, launch)
        with self.assertRaisesRegex(ValueError, 'worker ownership'):
            self.collect()

    def test_failure_with_two_valid_fits_collects_no_aggregate(self):
        path = self.root/'run/result.json'
        result = collector.read(path)
        path.unlink()
        self.replace(self.root/'run/failure.json', dict(status='PARTIAL_FAILED', readout='NOT_RUN', retry=False,
            completed=result['arms'], controller_seconds=70., error='synthetic failure'))
        collected = self.collect()
        self.assertEqual(collected['status'], 'COLLECTED_FAILURE_NO_AGGREGATE')
        self.assertFalse(collected['aggregate_available'])
        self.assertIsNone(collector.read(self.output/'audit.json')['aggregate'])

    def test_live_vacancy_failure_leaves_no_success_or_retry(self):
        self.vacancy.side_effect = ValueError('device occupied or queue unresolved')
        with self.assertRaisesRegex(ValueError, 'device occupied'):
            self.collect()
        self.assertFalse((self.output/'validation.json').exists())
        with self.assertRaisesRegex(ValueError, 'exclusive fresh'):
            self.collect()

    def test_final_vacancy_failure_preserves_capsule_without_success(self):
        self.vacancy.side_effect = [(self.gpu,self.xml), ValueError('queue changed')]
        with self.assertRaisesRegex(ValueError, 'queue changed'):
            self.collect()
        self.assertTrue((self.output/'metadata.tgz').is_file())
        self.assertFalse((self.output/'validation.json').exists())

    def test_session_reappears_during_audit(self):
        self.snapshot.side_effect = [[], [dict(pid=90000, ppid=1, pgid=9, session=self.worker_pids['A'])]]
        with self.assertRaisesRegex(ValueError, 'reappeared'):
            self.collect()
        self.vacancy.assert_not_called()

    def test_masked_collector_and_existing_output_rejected(self):
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='2'), self.assertRaisesRegex(ValueError, 'unset'):
            self.collect()
        self.assertFalse(self.output.exists())
        self.output.mkdir()
        with self.assertRaisesRegex(ValueError, 'exclusive fresh'):
            self.collect()

    def test_native_review_and_raw_source_join_tampering_rejected_without_tokenizer(self):
        original_read = collector.read
        for mode in ('native_review', 'teacher_target', 'wrong_source_call'):
            def altered(path):
                value = original_read(path)
                path = Path(path)
                if mode == 'native_review' and path in (self.root/'material/audit/main_review.json', Path(self.plan['main_review_path'])):
                    value['native_review']['rows'][0]['rendered_context_sha256'] = 'f'*64
                elif path == self.root/'material/corpora/P.json':
                    if mode == 'teacher_target':
                        value['corpus'][0]['spans'][1][0] += 'Compare predictions with observations.'
                    elif mode == 'wrong_source_call':
                        value['corpus'][0]['meta']['source_call_id'] = 'other'
                return value
            with self.subTest(mode=mode), patch.object(collector,'read',side_effect=altered), self.assertRaises(ValueError):
                collector.material_audit(self.root,self.plan,writer,diagnostic,writer_tests.exporter)

    def test_controller_cap_and_overlapping_workers_fail(self):
        terminal = self.root/'run/result.json'
        original = collector.read(terminal)
        self.replace(terminal,dict(original,controller_seconds=1201.))
        with self.assertRaisesRegex(ValueError,'inclusive cap'):
            collector.audit(self.root,self.plan_sha,self.plan,collector.read(self.logs/'launch.json'),writer,diagnostic,writer_tests.trainer)
        self.replace(terminal,original)
        path = self.root/'run/A/process.json'
        process = collector.read(path)
        process['started'] = collector.read(self.root/'run/P/process.json')['started']
        self.replace(path,process)
        with self.assertRaisesRegex(ValueError,'overlap/reorder'):
            collector.audit(self.root,self.plan_sha,self.plan,collector.read(self.logs/'launch.json'),writer,diagnostic,writer_tests.trainer)

    def test_metadata_change_after_archive_fails_final_seal(self):
        original_pack = collector.pack
        def change(*args):
            result = original_pack(*args)
            (self.logs/'controller.log').write_text('changed after pack')
            return result
        with patch.object(collector,'pack',side_effect=change), self.assertRaisesRegex(ValueError,'changed after packing'):
            self.collect()
        self.assertFalse((self.output/'validation.json').exists())

    def test_unknown_file_appearing_after_archive_fails(self):
        original_pack = collector.pack
        def change(*args):
            result = original_pack(*args)
            (self.root/'extra.json').write_text('{}')
            return result
        with patch.object(collector,'pack',side_effect=change), self.assertRaisesRegex(ValueError,'unknown metadata'):
            self.collect()
        self.assertFalse((self.output/'validation.json').exists())

    def test_unexpected_process_receipt_fails_status(self):
        directory = self.root/'extra_worker'
        directory.mkdir()
        self.replace(directory/'process.json',dict(pid=90001,pgid=90001))
        with self.assertRaisesRegex(ValueError,'unexpected process'):
            self.status()

    def test_process_scan_permission_error_never_means_empty(self):
        self.snapshot.side_effect = PermissionError('unreadable process table')
        with self.assertRaises(PermissionError):
            self.collect()
        self.assertFalse(self.output.exists())


class SafetyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='process-collect-safety-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_announced_native_contract_exact(self):
        self.assertEqual(collector.PLAN_SHA, '67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44')
        self.assertEqual(collector.EXPECTED_TOKENS, {'P':{'total':760,'target':32},'A':{'total':758,'target':31}})
        self.assertEqual(collector.DRIVER_SHA, collector.digest(collector.DRIVER))

    def test_credentials_patterns_and_duplicate_nonfinite_json_fail(self):
        for data in (b'{"password":"value"}', b'{"client_secret":"value"}', b'Authorization: Bearer abc',
                     b'-----BEGIN RSA PRIVATE KEY-----', b'hf_'+b'a'*32, b'https://user:password@example.test',
                     b'{"field":1,"field":2}', b'{"field":NaN}', b'\xff'):
            with self.subTest(data=data), self.assertRaises((ValueError, UnicodeDecodeError)):
                collector.scan_text(data, 'metadata/test.json' if data.startswith(b'{') else 'metadata/test.log')

    def test_symlinks_hardlinks_and_fifo_fail_safe(self):
        path = self.root/'regular.json'
        path.write_text('{}')
        link = self.root/'link.json'
        link.symlink_to(path)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            collector.payload(link)
        hard = self.root/'hard.json'
        os.link(path, hard)
        with self.assertRaisesRegex(ValueError, 'hardlinked'):
            collector.payload(hard)
        fifo = self.root/'fifo'
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, 'special'):
            collector.payload(fifo)

    def weight(self, dtype, number):
        size = 4 if dtype == 'F32' else 2
        header = json.dumps({'base.layers.0.q_proj.lora_A.weight':dict(dtype=dtype,shape=[1,1],data_offsets=[0,size])}).encode()
        path = self.root/'weight.safetensors'
        path.write_bytes(struct.pack('<Q',len(header))+header+number.to_bytes(size,'little'))
        return path

    def test_finite_weight_bits_all_supported_types_no_model_load(self):
        for dtype, valid, invalid in (('F32',0x3f800000,0x7f800000),('F16',0x3c00,0x7c00),('BF16',0x3f80,0x7f80)):
            with self.subTest(dtype=dtype):
                path = self.weight(dtype, valid)
                self.assertTrue(collector.finite_weights(path, collector.file_hash(path))['finite'])
                for value in (invalid, invalid+1, invalid | (1 << (31 if dtype == 'F32' else 15))):
                    path = self.weight(dtype,value)
                    with self.assertRaisesRegex(ValueError, 'nonfinite saved'):
                        collector.finite_weights(path,collector.file_hash(path))

    def test_weight_hash_and_trailing_bytes_fail(self):
        path = self.weight('F32',0)
        with self.assertRaisesRegex(ValueError, 'weight hash'):
            collector.finite_weights(path,'f'*64)
        with path.open('ab') as stream:
            stream.write(b'extra')
        with self.assertRaisesRegex(ValueError, 'trailing'):
            collector.finite_weights(path,collector.file_hash(path))

    def test_credentials_in_excluded_weight_header_still_fail(self):
        header = json.dumps({'__metadata__': {'api_key':'credential-value'},
            'base.layers.0.q_proj.lora_A.weight':dict(dtype='F32',shape=[1,1],data_offsets=[0,4])}).encode()
        path = self.root/'credential-header.safetensors'
        path.write_bytes(struct.pack('<Q',len(header))+header+bytes(4))
        with self.assertRaisesRegex(ValueError,'credential'):
            collector.finite_weights(path,collector.file_hash(path))

    def test_archive_traversal_link_duplicate_missing_and_hash_fail(self):
        for mode in ('traversal','link','duplicate','missing','hash'):
            path = self.root/(mode+'.tgz')
            with tarfile.open(path,'w:gz') as archive:
                if mode != 'missing':
                    member = tarfile.TarInfo('../bad' if mode=='traversal' else 'metadata/good.json')
                    member.size = 2
                    if mode=='link':
                        member.type, member.linkname = tarfile.SYMTYPE, '/etc/passwd'
                    archive.addfile(member,io.BytesIO(b'{}'))
                    if mode=='duplicate':
                        archive.addfile(member,io.BytesIO(b'{}'))
            hashes = {'metadata/good.json': 'f'*64 if mode=='hash' else hashlib.sha256(b'{}').hexdigest()}
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                collector.validate_archive(path,hashes)

    def test_uuid_vacancy_unknown_or_occupied_fail(self):
        for xml in ('<root/>','<root><gpu><uuid>wrong</uuid><processes/></gpu></root>',
                    '<root><gpu><uuid>expected</uuid><processes><process_info/></processes></gpu></root>'):
            with self.assertRaises(ValueError):
                collector.check_uuid(dict(gpu_uuid='expected'),xml,'expected')

    def test_watchdog_300_restored_and_existing_timer_rejected(self):
        with patch.object(collector.signal,'getitimer',return_value=(0.,0.)), patch.object(collector.signal,'signal') as handler, \
             patch.object(collector.signal,'setitimer') as timer, patch.object(collector,'collect',side_effect=RuntimeError('mock')):
            with self.assertRaises(RuntimeError):
                collector.finish()
            self.assertEqual(timer.call_args_list[0].args,(signal.ITIMER_REAL,300))
            self.assertEqual(timer.call_args_list[-1].args,(signal.ITIMER_REAL,0))
            self.assertEqual(handler.call_count,2)
        with patch.object(collector.signal,'getitimer',return_value=(1.,0.)), self.assertRaisesRegex(ValueError,'timer conflicts'):
            collector.finish()

    def test_watchdog_expiration_raises_and_restores(self):
        with patch.object(collector.signal,'getitimer',return_value=(0.,0.)), patch.object(collector.signal,'signal') as handler, \
             patch.object(collector.signal,'setitimer') as timer:
            def expire(**kwargs):
                handler.call_args_list[0].args[1](signal.SIGALRM,None)
            with patch.object(collector,'collect',side_effect=expire), self.assertRaises(collector.CollectionExpired):
                collector.finish()
            self.assertEqual(timer.call_args_list[-1].args,(signal.ITIMER_REAL,0))

    def test_gpu_checker_is_query_only_and_must_be_unmasked(self):
        with patch.dict(os.environ,CUDA_VISIBLE_DEVICES='2'), self.assertRaisesRegex(ValueError,'env -u'):
            collector.vacancy(dict(source_root='/source'),'expected')
        with patch.dict(os.environ,{},clear=True), patch.object(collector,'load') as load:
            load.return_value.check_free.return_value = (dict(gpu_uuid='expected'),
                '<root><gpu><uuid>expected</uuid><processes/></gpu></root>')
            collector.vacancy(dict(source_root='/source'),'expected')
            load.return_value.check_free.assert_called_once_with('2')
            self.assertEqual(load.call_args.args[1],collector.CHECK_SHA)


if __name__ == '__main__':
    unittest.main()
