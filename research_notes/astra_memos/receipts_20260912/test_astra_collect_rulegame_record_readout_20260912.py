"""Synthetic-only terminal collector tests. No live/GPU/native/SSH execution."""
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
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp')
import test_astra_rulegame_record_readout_20260912 as readout_tests

PATH = Path('/tmp/astra_collect_rulegame_record_readout_20260912.py')
spec = importlib.util.spec_from_file_location('tested_record_readout_collector', PATH)
collector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = collector
spec.loader.exec_module(collector)
bridge = readout_tests.bridge
diagnostic = readout_tests.diagnostic


def xml(uuid=None, processes=''):
    return f'<nvidia_smi_log><gpu><uuid>{uuid or collector.UUID}</uuid><processes>{processes}</processes></gpu></nvidia_smi_log>'


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = readout_tests.ReadoutTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.completed()
        self.root = self.fixture.output
        self.logs = self.root.with_name(self.root.name+'_launch')
        self.logs.mkdir()
        collector.common.write_json(self.logs / 'launch.json', {'synthetic': True})
        collector.common.write_new(self.logs / 'controller.log', b'Synthetic metadata only\n')
        collector.common.write_new(self.logs / 'gpu.xml', xml().encode())
        self.archive = self.fixture.fixture.root / 'terminal.tgz'
        self.patch_values = patch.multiple(collector, HOME=self.fixture.fixture.root.parent, ROOT=self.root, LOGS=self.logs,
            ARCHIVE=self.archive, SOURCE=readout_tests.writes.SOURCE,
            PLAN_SHA=self.fixture.prepared['plan_sha256'], PID=os.getpid(),
            STARTED=dt.datetime.fromtimestamp(time.time()-30, dt.timezone.utc).isoformat())
        self.patch_values.start()
        self.addCleanup(self.patch_values.stop)
        self.plan = diagnostic.read(self.root / 'plan.json')
        self.lineage = bridge.accepted_writes(self.plan)

    def terminal(self, fail_cell=None, no_quiz=False):
        self.fixture.fail_cell, self.fixture.no_quiz = fail_cell, no_quiz
        original = self.fixture.supervise
        def supervise(root, plan, stage, command, call_path):
            started = time.monotonic()
            pid = os.getpid()+1000+collector.CELLS.index(stage.name)
            try:
                receipt = original(root, plan, stage, command, call_path)
            finally:
                process = dict(pid=pid, pgid=pid, argv=command, device='2', started=started, timeout=600)
                self.fixture.fixture.replace_json(stage / 'process.json', process)
                super_path = stage / 'supervision.json'
                supervision = diagnostic.read(super_path)
                supervision.update(device='2', returncode=0 if supervision['ok'] else 1,
                    error=None if supervision['ok'] else {'message': 'synthetic failure'}, reserved_seconds=time.monotonic()-started)
                self.fixture.fixture.replace_json(super_path, supervision)
                if (stage / 'data/manifest.json').is_file():
                    for name in ('isolation.json', 'backend.ready.json'):
                        path = stage / 'data' / name
                        payload = diagnostic.read(path)
                        payload['pid'] = pid
                        if name == 'isolation.json':
                            payload.update(pgid=pid, parent_pid=os.getpid())
                        self.fixture.fixture.replace_json(path, payload)
                    self.reseal(stage / 'data')
            return supervision
        with patch.object(self.fixture, 'supervise', side_effect=supervise):
            if fail_cell:
                with self.assertRaisesRegex(RuntimeError, 'mock native load failed'):
                    self.fixture.evaluate()
            else:
                self.fixture.evaluate()

    def reseal(self, data):
        self.fixture.fixture.replace_json(data / 'manifest.json', {'files': diagnostic.tree_hashes(data, ('manifest.json',))})

    def audit(self):
        with patch.object(diagnostic, 'native_tokenizer', return_value=readout_tests.writes.Tokenizer()):
            return collector.audit(bridge, self.plan, diagnostic, self.lineage)

    def finish(self, release_error=None):
        with patch.object(collector, 'controller_present', return_value=False), \
             patch.object(collector, 'bind', return_value=(bridge, self.plan, diagnostic, self.lineage)), \
             patch.object(collector, 'release_check', return_value=({'gpu_uuid': collector.UUID}, xml()), side_effect=release_error), \
             patch.object(diagnostic, 'native_tokenizer', return_value=readout_tests.writes.Tokenizer()):
            return collector.finish()

    def test_complete_replay_native_custody_counts_and_scores(self):
        self.terminal()
        report = self.audit()
        self.assertTrue(report['readout_success'])
        self.assertEqual(report['costs']['requests'], 96)
        self.assertEqual(report['costs']['output_token_ceiling'], 27600)
        self.assertEqual(report['aggregate'], dict(P_minus_OFF=0, A_minus_OFF=0, P_minus_A=0))
        self.assertTrue(report['worker_cost_complete'])
        for cell in collector.CELLS:
            row = report['cells'][cell]
            self.assertEqual(row['roles'], {'wake': 20, 'record': 12})
            self.assertEqual(len(row['result']['tasks']), 4)
            self.assertEqual(row['result']['allotted_record_opportunities'], 12)

    def test_launch_binding_checks_main_identity_and_write_release(self):
        plan = {**self.plan, 'python': str(collector.HOME / 'v2/venv/bin/python'), 'write_plan_sha256': collector.WRITE_PLAN_SHA}
        release = Path(plan['write_root']) / 'run/main_release.json'
        collector.common.write_json(release, {'synthetic': 'completed write release'})
        launch = dict(pid=collector.PID, node=3, device='2', phase='actual_record_parent_free_readout',
            source=str(collector.SOURCE), root=str(collector.ROOT), started_utc=collector.STARTED,
            plan_sha256=collector.PLAN_SHA, driver_sha256=collector.DRIVER_SHA, launcher_sha256=collector.LAUNCHER_SHA,
            write_plan_sha256=collector.WRITE_PLAN_SHA, continuous_reservation=True, cells=list(collector.CELLS),
            adaptation_test=False, claim_boundary=diagnostic.CLAIM_BOUNDARY, controller_seconds=1800,
            cleanup_reserve=140, worker_cap_seconds=600, write_release_sha256=collector.digest(release),
            gpu={'gpu_uuid': collector.UUID}, command=[plan['python'], '-B', str(collector.DRIVER), 'evaluate',
                '--root', str(collector.ROOT), '--plan-sha256', collector.PLAN_SHA, '--allow-gpu'])
        self.fixture.fixture.replace_json(self.logs / 'launch.json', launch)
        fake_bridge = SimpleNamespace(checked_plan=Mock(return_value=(self.root, plan, diagnostic)),
            accepted_writes=Mock(return_value=self.lineage))
        with patch.object(collector, 'load', return_value=fake_bridge):
            self.assertEqual(collector.bind()[3], self.lineage)
            for changed in ({'pid': -1}, {'driver_sha256': 'wrong'}, {'write_release_sha256': 'wrong'}, {'cells': ['P_ON', 'OFF', 'A_ON']}):
                self.fixture.fixture.replace_json(self.logs / 'launch.json', {**launch, **changed})
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    collector.bind()
        fake_bridge.accepted_writes.assert_called_with(plan)

    def test_invalid_missing_quizzes_not_dropped(self):
        self.terminal(no_quiz=True)
        report = self.audit()
        for row in report['cells'].values():
            self.assertEqual(row['result']['mean_quiz_accuracy'], 0)
            self.assertEqual(len(row['result']['tasks']), 4)
            self.assertTrue(all(not item['valid_quiz'] for item in row['result']['tasks']))

    def test_partial_failure_keeps_nulls_no_aggregate(self):
        self.terminal(fail_cell='P_ON')
        report = self.audit()
        self.assertFalse(report['readout_success'])
        self.assertTrue(report['cells']['OFF']['verified'])
        self.assertIsNone(report['aggregate'])
        self.assertIsNone(report['costs'])
        self.assertIsNone(report['cells']['P_ON']['result'])
        self.assertIsNone(report['cells']['A_ON']['costs'])
        self.assertFalse(report['worker_cost_complete'])

    def test_pre_controller_failure_keeps_unknown_clocks(self):
        (self.root / 'run').mkdir()
        collector.common.write_json(self.root / 'run/failure.json', dict(error='synthetic pre-controller failure', retry=False, completed_cells=[]))
        report = self.audit()
        self.assertIsNone(report['controller'])
        self.assertIsNone(report['controller_seconds'])
        self.assertIsNone(report['controller_within_bound'])
        self.assertIsNone(report['observed_worker_seconds'])
        self.assertIsNone(report['aggregate'])

    def test_wrong_aggregate_rejected(self):
        self.terminal()
        path = self.root / 'run/result.json'
        result = diagnostic.read(path)
        result['P_minus_A'] = .2
        self.fixture.fixture.replace_json(path, result)
        with self.assertRaisesRegex(ValueError, 'aggregate differs'):
            self.audit()

    def test_controller_deadline_pid_and_overrun(self):
        self.terminal()
        path = self.root / 'run/controller.json'
        original = diagnostic.read(path)
        for patch_value in ({'pid': -1}, {'hard_end': original['hard_end']+1}):
            self.fixture.fixture.replace_json(path, {**original, **patch_value})
            with self.subTest(patch_value=patch_value), self.assertRaisesRegex(ValueError, 'controller identity'):
                self.audit()
        self.fixture.fixture.replace_json(path, original)
        terminal_path = self.root / 'run/result.json'
        result = diagnostic.read(terminal_path)
        result['controller_seconds'] = 1801
        self.fixture.fixture.replace_json(terminal_path, result)
        with self.assertRaisesRegex(ValueError, 'inclusive bound'):
            self.audit()

    def test_failed_overrun_reported_not_hidden(self):
        self.terminal(fail_cell='OFF')
        path = self.root / 'run/failure.json'
        failure = diagnostic.read(path)
        failure['controller_seconds'] = 1801
        self.fixture.fixture.replace_json(path, failure)
        self.assertFalse(self.audit()['controller_within_bound'])

    def test_spec_adapter_header_and_ownership_tamper(self):
        self.terminal()
        paths = [self.root / 'run/OFF.spec.json', self.root / 'run/OFF/process.json', self.root / 'run/OFF/data/identity.json']
        changes = [{'adapter': 'wrong'}, {'pid': -1}, {'cell': 'A_ON'}]
        for path, changed in zip(paths, changes):
            original = path.read_bytes()
            self.fixture.fixture.replace_json(path, {**diagnostic.read(path), **changed})
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.audit()
            path.write_bytes(original)

    def test_native_audit_rerun_not_marker_trust(self):
        self.terminal()
        tokenizer = readout_tests.writes.Tokenizer()
        with patch.object(tokenizer, 'apply_chat_template', return_value='wrong native context'), \
             patch.object(diagnostic, 'native_tokenizer', return_value=tokenizer), self.assertRaisesRegex(ValueError, 'native rendered'):
            collector.audit(bridge, self.plan, diagnostic, self.lineage)

    def test_wrong_role_and_more_than_32_requests_rejected(self):
        self.terminal()
        calls = self.root / 'run/OFF/data/calls'
        path = next(calls.glob('*.request.json'))
        original = path.read_bytes()
        payload = diagnostic.read(path)
        payload['request']['role'] = 'parent'
        self.fixture.fixture.replace_json(path, payload)
        with self.assertRaisesRegex(ValueError, 'unexpected role'):
            collector.raw_cost(calls.parent)
        path.write_bytes(original)
        (calls / '9999.request.json').write_bytes(original)
        (calls / '9999.response.json').write_bytes(path.with_name(path.name.replace('.request.', '.response.')).read_bytes())
        with self.assertRaisesRegex(ValueError, 'cap exceeded'):
            collector.raw_cost(calls.parent)

    def test_corrupt_partial_capture_is_archived_with_error(self):
        self.terminal(fail_cell='P_ON')
        target = self.root / 'run/OFF/data/events.jsonl'
        target.write_text(target.read_text()+'{}\n')
        result = self.finish()
        self.assertEqual(result['readout_status'], 'FAILED_PARTIAL_NO_AGGREGATE')
        validation = collector.read(str(self.archive)+'.validation.json')
        self.assertIsNone(validation['audit']['aggregate'])
        self.assertFalse(validation['audit']['cells']['OFF']['verified'])
        self.assertIn('replay failed', validation['audit']['cells']['OFF']['error'])

    def test_complete_archive_all_nonweights_and_readonly_repeat(self):
        self.terminal()
        (self.root / 'unrelated_metadata.txt').write_text('preserve all nonweight metadata')
        (self.root / 'excluded.safetensors').write_bytes(b'not archived')
        outcome = self.finish()
        self.assertEqual(outcome['status'], 'COLLECTED')
        validation = collector.read(str(self.archive)+'.validation.json')
        self.assertEqual(validation['files'], collector.metadata())
        self.assertTrue(any(name.endswith('controller.log') for name in validation['files']))
        self.assertTrue(any(name.endswith('unrelated_metadata.txt') for name in validation['files']))
        self.assertFalse(any(name.endswith('.safetensors') for name in validation['files']))
        release = collector.read(self.root / 'run/main_release.json')
        self.assertTrue(release['full_release'])
        self.assertEqual(release['bounds']['external_collection'], 300)
        before = collector.metadata()
        with patch.object(collector, 'bind', side_effect=AssertionError('already collected must not rerun native')):
            with patch.object(collector, 'controller_present', return_value=False):
                self.assertEqual(collector.finish()['status'], 'ALREADY_COLLECTED_VERIFIED_NO_WRITES')
        self.assertEqual(before, collector.metadata())

    def test_partial_archive_and_release_never_overwritten(self):
        self.terminal()
        self.archive.write_bytes(b'partial capsule')
        with self.assertRaisesRegex(ValueError, 'partial capsule'):
            self.finish()
        self.assertEqual(self.archive.read_bytes(), b'partial capsule')

    def test_partial_release_preserved_without_retry(self):
        self.terminal()
        path = self.root / 'run/main_release.xml'
        path.write_text('partial prior release')
        with self.assertRaisesRegex(ValueError, 'partial release preserved'):
            self.finish()
        self.assertEqual(path.read_text(), 'partial prior release')
        self.assertFalse(self.archive.exists())

    def test_full_release_failure_writes_no_release_or_archive(self):
        self.terminal()
        with self.assertRaisesRegex(RuntimeError, 'queue requires'):
            self.finish(RuntimeError('queue requires reconciliation'))
        self.assertFalse((self.root / 'run/main_release.json').exists())
        self.assertFalse((self.root / 'run/main_release.xml').exists())
        self.assertFalse(self.archive.exists())

    def test_metadata_symlink_rejected_before_custody(self):
        self.terminal()
        (self.root / 'foreign_metadata').symlink_to(self.logs / 'controller.log')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.finish()
        self.assertFalse(self.archive.exists())

    def test_occupied_uuid_and_queue_fail_before_release(self):
        for gpu, text in (({'gpu_uuid': 'wrong'}, xml()), ({'gpu_uuid': collector.UUID}, xml(processes='<process_info/>'))):
            with self.assertRaises(ValueError):
                collector.check_uuid(gpu, text)
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(collector, 'load', return_value=SimpleNamespace(check_free=Mock(side_effect=RuntimeError('queue requires reconciliation')))):
            with self.assertRaisesRegex(RuntimeError, 'queue requires'):
                collector.release_check()
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='2'), self.assertRaisesRegex(ValueError, 'env -u'):
            collector.release_check()

    def test_source_load_hash_and_symlink_fail_without_execution(self):
        path = self.fixture.fixture.root / 'unsafe.py'
        path.write_text('raise AssertionError("executed")\n')
        with self.assertRaisesRegex(ValueError, 'dependency changed'):
            collector.load(path, '0'*64, 'must_not_execute')
        alias = self.fixture.fixture.root / 'alias.py'
        alias.symlink_to(path)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            collector.load(alias, collector.digest(path), 'must_not_execute_link')

    def test_archive_traversal_link_duplicate_and_corruption(self):
        prefix, name = 'allowed/', 'allowed/file.txt'
        for mode in ('traversal', 'link', 'duplicate', 'wrong_bytes'):
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w:gz', format=tarfile.USTAR_FORMAT) as archive:
                member = tarfile.TarInfo('../escape' if mode == 'traversal' else name)
                member.size = 1
                if mode == 'link':
                    member.type, member.linkname = tarfile.SYMTYPE, 'elsewhere'
                archive.addfile(member, io.BytesIO(b'x'))
                if mode == 'duplicate':
                    archive.addfile(member, io.BytesIO(b'x'))
            stream.seek(0)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                collector.common.validate_archive(stream, {name: 'wrong' if mode == 'wrong_bytes' else collector.hashlib.sha256(b'x').hexdigest()}, prefix)

    def test_live_and_missing_terminal_are_markers_only(self):
        with patch.object(collector, 'read', side_effect=AssertionError('no live output read')), \
             patch.object(collector, 'controller_present', return_value=True):
            self.assertEqual(collector.status()['scoring'], 'NONE')
            with self.assertRaisesRegex(ValueError, 'wait for absent'):
                collector.finish()
        with patch.object(collector, 'controller_present', return_value=False), self.assertRaisesRegex(ValueError, 'AND terminal'):
            collector.finish()

    def test_timeout_does_not_get_swallowed_as_partial(self):
        self.assertFalse(issubclass(collector.CollectionExpired, Exception))
        with patch.object(collector, 'collect', side_effect=collector.CollectionExpired('expired')), self.assertRaises(collector.CollectionExpired):
            collector.finish()
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))


if __name__ == '__main__':
    unittest.main()
