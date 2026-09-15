import json
from copy import deepcopy
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_l2_long_lane as lane
from gpu.orch_l2_long_hook import build_parent
from gpu.orch_l2_long_envelope import parse_json_envelope


class LongLaneTests(unittest.TestCase):
    def test_exact_ten_native_stages_and_three_sleeps(self):
        self.assertEqual(len(lane.PHASES), 10)
        self.assertEqual([cycle for cycle, phase in lane.PHASES if phase == 'sleep'], [1, 2, 3])
        self.assertEqual(lane.PHASES[0], (1, 'experience'))
        self.assertLess(lane.PHASES.index((0, 'readout')), lane.PHASES.index((1, 'sleep')))

    def test_imports_shared_driver_never_rebuilds_cohort(self):
        for cycle, phase in lane.PHASES:
            arguments = lane.native_command('/snapshot', lane.SHARED_ROOT, cycle, phase)
            self.assertEqual(arguments[arguments.index('-m') + 1], 'gpu.orch_l2_shared_run')
            self.assertEqual(arguments[arguments.index('--arm') + 1], 'LONG')
            self.assertNotIn('source', arguments)
            self.assertNotIn('prepare', arguments)

    def test_owner_is_only_physical_one(self):
        self.assertEqual(lane.GPU_INDEX, 1)
        self.assertEqual(lane.GPU_UUID, 'GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b')
        self.assertEqual(lane.HOURS, 12)
        with self.assertRaisesRegex(ValueError, 'only_owned'):
            lane.scan(0, lane.GPU_UUID)

    def test_invalid_stage_refused(self):
        for cycle, phase in ((0, 'source'), (0, 'experience'), (4, 'sleep')):
            with self.assertRaises(ValueError):
                lane.native_command('/snapshot', lane.SHARED_ROOT, cycle, phase)

    def test_resume_flag_only_on_original_interrupted_stage(self):
        arguments = lane.native_command('/snapshot', lane.SHARED_ROOT, 1, 'experience', resume_experience=True)
        self.assertEqual(arguments.count('--resume-experience'), 1)
        for cycle, phase in lane.PHASES[1:]:
            with self.assertRaisesRegex(ValueError, 'original_cycle1'):
                lane.native_command('/snapshot', lane.SHARED_ROOT, cycle, phase, resume_experience=True)

    def test_resume_does_not_restart_lifetime_deadline(self):
        continuation = dict(original_start=dict(started_unix=100, deadline_unix=40000))
        self.assertEqual(lane.allocation_deadline(30000, 90000, continuation), 40000)
        self.assertEqual(lane.allocation_deadline(30000, 35000, continuation), 35000)
        continuation['original_start']['deadline_unix'] = 90000
        self.assertEqual(lane.allocation_deadline(30000, 90000, continuation), 43300)

    def test_new_manifest_does_not_require_replacing_original_alias(self):
        root = Path('/long')
        self.assertEqual(lane.published_manifest(root, {}), root / 'PREPARE_LONG.json')
        self.assertEqual(lane.published_manifest(root, dict(native_manifest_filename='PREPARE_LONG_V7.json')),
                         root / 'PREPARE_LONG_V7.json')
        for name in ('../PREPARE_LONG.json', '/PREPARE_LONG.json', 'other.json'):
            with self.assertRaisesRegex(ValueError, 'own_native_manifest'):
                lane.published_manifest(root, dict(native_manifest_filename=name))


class LongResumeReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'long'
        self.shared = Path(self.temporary.name) / 'shared'
        (self.root / 'run').mkdir(parents=True)
        evidence = Path(__file__).resolve().parents[1] / 'research_notes/analysis/orch_l2_long_20260914_attempt1'
        with tarfile.open(evidence / 'RESUME_ORIGINAL_001.tar.gz') as archive:
            for member in archive.getmembers():
                if member.isfile():
                    self.assertFalse(Path(member.name).is_absolute())
                    self.assertNotIn('..', Path(member.name).parts)
                    target = self.shared / member.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
        state_path = self.root / 'RESUME_STATE_001.json'
        state_path.write_bytes((evidence / state_path.name).read_bytes())
        self.state = json.loads(state_path.read_text())
        lane.write(self.root / 'run/START.json', self.state['original_start'])
        lane.write(self.root / 'run/TERMINAL.json', dict(status='FAILED', assigned_gpu_hours=0.06,
            error=dict(message='native_long_stage_failed:experience'), stages=[dict(cycle=1, phase='experience')]))
        self.publication = dict(resume_state_sha256=lane.file_hash(state_path),
            original_terminal_sha256=lane.file_hash(self.root / 'run/TERMINAL.json'))
        for index in ('0001', '0002'):
            name = index + '_LONG_C1'
            request_path = self.shared / 'parent_queue' / (name + '.request.json')
            saved = self.state['provider_outputs'][name]
            lane.write(request_path.with_name(name + '.recovered.response.json'), dict(id=name,
                request_sha256=lane.digest(json.loads(request_path.read_text())),
                result=parse_json_envelope(saved['result']), recovery=dict(provider_calls=0,
                    request_file_sha256=lane.file_hash(request_path),
                    original_response_sha256=lane.file_hash(request_path.with_name(name + '.response.json')),
                    stdout_sha256=saved['sha256'], parser_sha256=lane.file_hash(
                        Path(lane.__file__).with_name('orch_l2_long_envelope.py')))))

    def test_actual_boundary_verified_without_mutation(self):
        paths = list(self.shared.rglob('*'))
        before = {path: path.read_bytes() for path in paths if path.is_file()}
        result = lane.reconcile_resume(self.root, self.shared, self.publication)
        self.assertEqual(result['completed_episodes'], 4)
        self.assertEqual(result['child_calls'], 16)
        self.assertEqual(result['decisions_consumed'], 2)
        self.assertEqual(result['provider_calls'], 0)
        self.assertEqual(result['prior_gpu_hours'], 0.06)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_original_call_change_refused(self):
        path = self.shared / 'LONG/cycle1/experience/CALL_0000.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'original_resume_evidence_changed'):
            lane.reconcile_resume(self.root, self.shared, self.publication)

    def test_pending_recovery_change_or_charge_refused(self):
        path = self.shared / 'parent_queue/0002_LONG_C1.recovered.response.json'
        original = json.loads(path.read_text())
        for key, value in (('provider_calls', 1), ('stdout_sha256', 'wrong')):
            changed = deepcopy(original)
            changed['recovery'][key] = value
            lane.write(path, changed)
            with self.assertRaisesRegex(ValueError, 'exact_saved_provider_recovery'):
                lane.reconcile_resume(self.root, self.shared, self.publication)
        changed = deepcopy(original)
        changed['result']['message'] = 'Replacement advice is not recovery.'
        lane.write(path, changed)
        with self.assertRaisesRegex(ValueError, 'exact_saved_provider_recovery'):
            lane.reconcile_resume(self.root, self.shared, self.publication)

    def test_original_start_or_terminal_drift_refused(self):
        path = self.root / 'run/START.json'
        original = json.loads(path.read_text())
        changed = deepcopy(original)
        changed['deadline_unix'] += 3600
        lane.write(path, changed)
        with self.assertRaisesRegex(ValueError, 'original_failed_guardian'):
            lane.reconcile_resume(self.root, self.shared, self.publication)
        lane.write(path, original)
        path = self.root / 'run/TERMINAL.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'published_original_terminal'):
            lane.reconcile_resume(self.root, self.shared, self.publication)

    def test_missing_recovered_message_cannot_launch(self):
        (self.shared / 'parent_queue/0002_LONG_C1.recovered.response.json').unlink()
        with self.assertRaises(FileNotFoundError):
            lane.reconcile_resume(self.root, self.shared, self.publication)

    def test_restoration_timing_never_replaces_actual_parent_cost(self):
        output = self.shared / 'LONG/cycle1/experience'
        continuation = output / 'CONTINUATION_V5'
        continuation.mkdir()
        lane.write(continuation / 'PRESERVED.json', dict(episodes=4, child_calls=16,
            original_calls_replayed=0, files={path.name: lane.file_hash(path)
                for path in output.glob('LONG_PARENT_EVENT_*.json')}))
        hook = build_parent(root=self.shared, cycle=1, tokenizer=LongHookTests.Tokenizer(),
            transport=lambda request: self.fail('no provider call'), emit=lambda event: None)
        self.assertEqual(len(hook.original_parent_decisions), 2)
        for original in hook.original_parent_decisions:
            restored = deepcopy(original)
            restored.update(elapsed_seconds=0.001, decision='speak')
            hook.parent.records.append(restored)
        result = hook.distill_cycle()
        self.assertEqual(result['elapsed_parent_seconds'], sum(
            event['elapsed_seconds'] for event in hook.original_parent_decisions))
        self.assertEqual(result['backend_errors'], 1)
        self.assertEqual(result['recovery_accounting']['cached_request_seconds'], 0.002)
        self.assertEqual(result['recovery_accounting']['cached_provider_calls'], 0)

    def test_failed_precollection_attempt_cost_is_not_reset(self):
        directory = self.root / 'run_resume_v5'
        directory.mkdir()
        lane.write(directory / 'TERMINAL.json', dict(status='FAILED', assigned_gpu_hours=0.061,
            stages=[dict(cycle=1, phase='experience')]))
        self.publication.update(resume_predecessor_directory=directory.name,
            resume_predecessor_terminal_sha256=lane.file_hash(directory / 'TERMINAL.json'))
        result = lane.reconcile_resume(self.root, self.shared, self.publication)
        self.assertEqual(result['prior_gpu_hours'], 0.061)
        self.publication['resume_predecessor_terminal_sha256'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'failed_precollection'):
            lane.reconcile_resume(self.root, self.shared, self.publication)


class LongStageBoundaryTests(unittest.TestCase):
    def setUp(self):
        LongResumeReconciliationTests.setUp(self)
        evidence = Path(__file__).resolve().parents[1] / 'research_notes/analysis/orch_l2_long_20260914_attempt1'
        predecessor = self.root / 'run_resume_v5_02'
        predecessor.mkdir()
        for source, target in (('STAGE_BOUNDARY_TERMINAL_01.json', 'TERMINAL.json'),
                               ('STAGE_BOUNDARY_START_01.json', 'START.json')):
            (predecessor / target).write_bytes((evidence / source).read_bytes())
        receipts = {}
        for cycle, phase, name in ((1, 'experience', 'C1_EXPERIENCE_COMPLETE.json'),
                                   (0, 'readout', 'C0_READOUT_COMPLETE.json'),
                                   (1, 'sleep', 'C1_SLEEP_COMPLETE.json')):
            path = self.shared / 'LONG' / f'cycle{cycle}' / phase / 'COMPLETE.json'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((evidence / name).read_bytes())
            receipts[f'cycle{cycle}/{phase}'] = lane.file_hash(path)
        lane.write(self.shared / 'INITIAL.json', self.state['original_start']['shared_binding']['initial'])
        self.publication.update(stage_predecessor_directory=predecessor.name,
            stage_predecessor_terminal_sha256=lane.file_hash(predecessor / 'TERMINAL.json'),
            completed_stage_receipts=receipts, stage_run_directory='run_stages_01')

    def test_actual_completed_prefix_resumes_only_readout1(self):
        result = lane.reconcile_completed_stages(self.root, self.shared, self.publication)
        self.assertEqual(result['completed_stage_count'], 3)
        self.assertEqual(result['next_stage'], [1, 'readout'])
        self.assertEqual(result['next_input_adapter']['state_sha256'],
                         'ad2d1065a97b88b183c001baf48117886d16ab66fe8f305158d7adfc00882cec')
        self.assertEqual(result['prior_gpu_hours'], 0.33069377654128607)
        self.assertEqual(result['provider_calls'], 0)
        self.assertEqual(lane.PHASES[result['completed_stage_count']:][0], (1, 'readout'))

    def test_changed_receipt_or_skipped_hole_refused(self):
        publication = deepcopy(self.publication)
        del publication['completed_stage_receipts']['cycle0/readout']
        with self.assertRaisesRegex(ValueError, 'contiguous_completed'):
            lane.reconcile_completed_stages(self.root, self.shared, publication)
        path = self.shared / 'LONG/cycle1/sleep/COMPLETE.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'lineage_or_receipt_drift'):
            lane.reconcile_completed_stages(self.root, self.shared, self.publication)

    def test_partial_next_stage_cannot_be_replayed(self):
        (self.shared / 'LONG/cycle1/readout').mkdir()
        with self.assertRaisesRegex(ValueError, 'already_started_no_replay'):
            lane.reconcile_completed_stages(self.root, self.shared, self.publication)


class LongScannerRetryTests(unittest.TestCase):
    def report(self, unresolved=(), owners=()):
        return dict(gpus=f'1, {lane.GPU_UUID}, NVIDIA A100, unused, unused, 0',
                    clear=not (unresolved or owners), owners=list(owners), unresolved=list(unresolved))

    def run_scan(self, reports):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shared = root / 'shared'
            shared.mkdir()
            (shared / 'scanner.py').write_text('unchanged scanner')
            (shared / 'service_exceptions.json').write_text('{}')
            lane.write(root / 'PUBLICATION.json', dict(shared_scanner_files={
                name: lane.file_hash(shared / name) for name in ('scanner.py', 'service_exceptions.json')}))
            results = [lane.subprocess.CompletedProcess([], 0 if report['clear'] else 1,
                       stdout=json.dumps(report)) for report in reports]
            with patch.object(lane, 'ROOT', root), patch.object(lane, 'SHARED_ROOT', shared), \
                    patch.object(lane.subprocess, 'run', side_effect=results) as run, \
                    patch.object(lane.time, 'sleep'):
                result = lane.scan(1, lane.GPU_UUID)
            return result, run.call_count

    def test_transient_sftp_waits_for_fully_clear_scan(self):
        blocked = self.report([dict(comm='sshd'), dict(comm='sftp-server')])
        result, calls = self.run_scan([blocked, self.report()])
        self.assertTrue(result['safe'])
        self.assertEqual(calls, 2)
        self.assertFalse(blocked['clear'])
        self.assertEqual(len(blocked['unresolved']), 2)

    def test_persistent_transient_never_gets_an_exemption(self):
        blocked = self.report([dict(comm='sftp-server')])
        result, calls = self.run_scan([blocked] * 10)
        self.assertFalse(result['safe'])
        self.assertEqual(calls, 10)
        self.assertEqual(result['unresolved'], blocked['unresolved'])

    def test_unknown_process_or_owner_is_not_retried(self):
        for report in (self.report([dict(comm='python')]), self.report(owners=[dict(pid=123)])):
            result, calls = self.run_scan([report])
            self.assertFalse(result['safe'])
            self.assertEqual(calls, 1)


class LongHookTests(unittest.TestCase):
    class Tokenizer:
        def encode(self, text, add_special_tokens=False):
            return text.split()

    def payload(self, episode=0, turn=0):
        return dict(kind='coach', turn=turn, task={'node': 'public_start'},
            public_messages=[dict(role='user', content='Visible training observation')],
            prior_parent_messages=[], learner=dict(cycle=1,
                completed_experience_episodes=episode, successful_experience_episodes=0,
                previous_admitted_rows=0, readout_visibility='NO_READOUT_DATA'))

    def test_transport_gets_sanitized_request_not_shared_store(self):
        requests = []

        def transport(request):
            requests.append(request)
            return dict(decision='speak', message='Notice your repeated evidence-checking habit.',
                        reason='Across episodes.', distillation='Training only.')

        hook = build_parent(root='/unused', cycle=1, tokenizer=self.Tokenizer(),
                            transport=transport, emit=lambda event: None)
        self.assertTrue(hook(self.payload())['speak'])
        self.assertEqual(requests[0]['kind'], 'long_coach')
        self.assertNotIn('task', requests[0]['long_request'])
        self.assertNotIn('root', requests[0]['long_request'])
        self.assertFalse(hook(self.payload(turn=2))['speak'])
        self.assertEqual(len(requests), 1)

    def test_unknown_or_sealed_scalar_fails_before_transport(self):
        hook = build_parent(root='/unused', cycle=1, tokenizer=self.Tokenizer(),
                            transport=lambda request: self.fail('no dispatch'), emit=lambda event: None)
        payload = self.payload()
        payload['learner']['held_success'] = 16
        with self.assertRaisesRegex(ValueError, 'readout_scalars'):
            hook(payload)

    def test_natural_child_question_reaches_real_transport_without_new_actor_loop(self):
        requests = []

        def transport(request):
            requests.append(request)
            return dict(decision='speak', message='Your own grounded responses train your LoRA.',
                        reason='Answer the learner.', distillation='Explained the learning system.')

        hook = build_parent(root='/unused', cycle=1, tokenizer=self.Tokenizer(),
            transport=transport, emit=lambda event: None)
        hook(self.payload())
        payload = self.payload(turn=2)
        payload['public_messages'].append(dict(role='assistant', content=
            'PARENT QUESTION: What changes when I sleep?\nREAD EVENT visible_event'))
        self.assertTrue(hook(payload)['speak'])
        self.assertEqual(requests[1]['long_request']['child_question'], 'What changes when I sleep?')

    def test_only_prior_experience_and_sleep_are_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            experience = root / 'LONG/cycle1/experience'
            sleep = root / 'LONG/cycle1/sleep'
            experience.mkdir(parents=True)
            sleep.mkdir()
            (experience / 'COMPLETE.json').write_text(json.dumps(dict(status='COMPLETE', arm='LONG',
                episodes=1, admitted_rows=0)))
            (experience / 'EPISODE_01.json').write_text(json.dumps(dict(correct=False,
                messages=[dict(role='user', content='My training observation')], captures=[])))
            (sleep / 'COMPLETE.json').write_text(json.dumps(dict(status='COMPLETE', arm='LONG',
                updates=0, unchanged=True)))
            original = Path.read_text
            reads = []

            def read_text(path, *args, **kwargs):
                reads.append(str(path))
                self.assertNotIn('readout', str(path))
                self.assertNotIn('SOURCE', str(path))
                return original(path, *args, **kwargs)

            with patch.object(Path, 'read_text', read_text):
                hook = build_parent(root=root, cycle=2, tokenizer=self.Tokenizer(),
                    transport=lambda request: None, emit=lambda event: None)
            self.assertEqual(len(reads), 3)
            self.assertEqual(hook.parent.history[0]['observation'], 'My training observation')
            self.assertTrue(hook.parent.sleeps[0]['values']['no_update'])


if __name__ == '__main__':
    unittest.main()
