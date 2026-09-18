import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r152_a40r7_recovery as recovery


def fixture(count=2):
    plan = dict(root=str(recovery.ROOT), segment_tokens=10, context_limit=100,
                hard_end_unix=9999999999, presentation_version='raw_allhistory',
                system_prompt='system', birth_prompt='birth', decoder={'sample': True})
    checkpoint = dict(optimizer_steps=recovery.SAVED_STEPS, adapter_state_sha256='adapter',
                      base_sha256='base', checkpoint_sha256={'adapter': 'aa', 'optimizer': 'oo', 'rng': 'oo'},
                      experiment={'seed': 1})
    model_hash = recovery.digest(checkpoint['checkpoint_sha256'])
    records = [dict(kind='SLEEP_COMPLETE', sha256='saved', document=dict(cycle=recovery.SAVED_CYCLE,
                                                                         checkpoint=checkpoint))]
    rows = []
    for number in range(count):
        request = dict(split='TRAIN', segment=number, messages=[{'role': 'user', 'content': str(number)}],
                       retry_allowed=False, max_new_tokens=10, deadline_unix=plan['hard_end_unix'],
                       model_state_sha256=model_hash, prompt_tokens=2)
        output = dict(raw=str(number), token_ids=[number], terminal=False, truncated=True,
                      decoder=plan['decoder'], adapter_state_sha256='adapter', base_sha256='base', prompt_tokens=2)
        response = dict(request_sha256=recovery.digest(request), response=output, raw_saved_before_validation=True)
        source = recovery.digest(response)
        rows.append(dict(source_sha256=source, split='TRAIN', actor='child', prefix_loss=False, target_loss=True,
                         segment=number, prefix=deepcopy(request['messages']), model_state_sha256=model_hash,
                         target=output['raw'], token_ids=output['token_ids'], terminal=False, truncated=True))
        records.extend([dict(kind='REQUEST', document=dict(request, resume_state={'not': 'replayed'})),
                        dict(kind='RESPONSE', document=response),
                        dict(kind='COMMITTED', document=dict(segment=number, source_sha256=source))])
    records.append(dict(kind='SLEEP_REQUEST', sha256='sleep-request', document={'cycle': recovery.CYCLE}))
    records.append(dict(kind='TARGET_ELIGIBILITY', sha256='head', document=dict(version='raw_allhistory',
                        excluded=[], raw_modified=False, new_row_sha256=[row['source_sha256'] for row in rows],
                        rehearsal_row_sha256=[])))
    snapshot = {'state': {'pending': 'sleep', 'rows': deepcopy(rows), 'history': ['raw'], 'carry': ['raw']},
                'sha256': 'stream'}
    stream = SimpleNamespace(pending_rows=lambda: deepcopy(rows), rows=rows, sleep_frontier=0,
        pending='sleep:' + recovery.digest([row['source_sha256'] for row in rows]),
        sleep_receipts=[{'checkpoint': checkpoint}] * recovery.SAVED_CYCLE,
        model_state_sha256=model_hash, experiment=checkpoint['experiment'], segment_tokens=10,
        context_limit=100, deadline_unix=plan['hard_end_unix'],
        presentation=dict(version='raw_allhistory', system_prompt='system', birth_prompt='birth'),
        checkpoint=lambda: deepcopy(snapshot))
    state = dict(previous='head', request=None, response=None, sleep_request={'cycle': recovery.CYCLE},
                 latest={'document': deepcopy(snapshot)})
    journal = SimpleNamespace(root=recovery.ROOT / 'stream', record=Mock())
    return SimpleNamespace(plan=plan, checkpoint=checkpoint, records=records, snapshot=snapshot,
                           stream=stream, state=state, journal=journal)


class JournalTests(unittest.TestCase):
    def binding(self, data):
        with patch.object(recovery, 'journal_records', return_value=(data.state, data.records)):
            return recovery.journal_binding(data.plan, data.stream, data.journal, data.checkpoint)[0]

    def test_corrected_latest_boundary_preserves_92_committed_updates(self):
        self.assertEqual((recovery.SAVED_CYCLE, recovery.SAVED_STEPS, recovery.CYCLE), (31, 1922, 32))
        data = fixture()
        result = self.binding(data)
        self.assertEqual(result['pair_indices'], [1, 4])
        self.assertEqual(result['sleep_request_index'], 7)
        self.assertEqual(result['unsaved_updates'], 0)
        data.journal.record.assert_not_called()

    def test_actual_request_count_not_assumed_two(self):
        result = self.binding(fixture(3))
        self.assertEqual(result['pair_indices'], [1, 4, 7])

    def test_any_unsaved_update_refused(self):
        data = fixture()
        data.records.append(dict(kind='UPDATE', document={'optimizer_step': 1923}))
        with self.assertRaisesRegex(ValueError, 'no_unsaved_UPDATE'):
            self.binding(data)

    def test_stale_sleep30_cannot_be_restored(self):
        data = fixture()
        data.records[0]['document']['cycle'] = 30
        with self.assertRaisesRegex(ValueError, 'one_saved_sleep31'):
            self.binding(data)

    def test_uncommitted_generation_cannot_replay(self):
        data = fixture()
        data.records[3]['kind'] = 'RESPONSE'
        with self.assertRaisesRegex(ValueError, 'only_actual_committed'):
            self.binding(data)

    def test_unexpected_postcheckpoint_event_refused(self):
        data = fixture()
        data.records.append(dict(kind='INBOX', document={}))
        with self.assertRaisesRegex(ValueError, 'exact_preencoding_failure_suffix'):
            self.binding(data)

    def test_changed_raw_or_deadline_refused(self):
        for mutate in ('raw', 'deadline'):
            with self.subTest(mutate=mutate):
                data = fixture()
                if mutate == 'raw':
                    data.records[2]['document']['response']['raw'] = 'changed'
                else:
                    data.plan['hard_end_unix'] -= 1
                with self.assertRaises(ValueError):
                    self.binding(data)

    def test_pending_cycle_or_presentation_changes_refused(self):
        for field in ('cycle', 'presentation'):
            with self.subTest(field=field):
                data = fixture()
                if field == 'cycle':
                    data.state['sleep_request']['cycle'] = 31
                else:
                    data.stream.presentation['version'] = 'other'
                with self.assertRaises(ValueError):
                    self.binding(data)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.destination = Path(self.directory.name)
        self.data = fixture()
        self.child = SimpleNamespace(plan=self.data.plan, optimizer_steps=1922, adapter_hash=lambda: 'adapter',
                                    engine=SimpleNamespace(verify_base=Mock()), generate=Mock(side_effect=[
                                        deepcopy(self.data.records[index]['document']['response']) for index in (2, 5)]))
        self.scan = patch.object(recovery, 'journal_records', return_value=(self.data.state, self.data.records))
        self.scan.start()
        self.addCleanup(self.scan.stop)
        binding, unused = recovery.journal_binding(self.data.plan, self.data.stream, self.data.journal, self.data.checkpoint)
        self.provenance = dict(journal=binding, evidence={'checkpoint': self.data.checkpoint})
        for name, result in (('restore', 'optimizer'), ('rng', {'rng': 'replayed'}),
                             ('optimizer_fingerprint', 'optimizer')):
            replacement = patch.object(recovery, name, return_value=result)
            replacement.start()
            self.addCleanup(replacement.stop)

    def replay(self):
        return recovery.replay_generations(self.child, self.data.stream, self.data.journal,
                                           self.provenance, self.destination)

    def test_exact_actual_requests_replay_without_history_or_updates(self):
        before = deepcopy(self.data.snapshot)
        result = self.replay()
        self.assertEqual(result['matched_generations'], 2)
        self.assertEqual(result['optimizer_steps'], 1922)
        self.assertEqual(result['optimizer_updates'], 0)
        self.assertFalse(result['original_postgeneration_rng_snapshot_available'])
        self.assertEqual(self.data.snapshot, before)
        self.data.journal.record.assert_not_called()
        self.assertEqual(self.child.generate.call_count, 2)
        for call, index in zip(self.child.generate.call_args_list, (1, 4)):
            request = self.data.records[index]['document']
            self.assertEqual(call.args, (request['messages'],))
            self.assertEqual(call.kwargs, {'max_new_tokens': request['max_new_tokens'],
                                          'deadline_unix': request['deadline_unix']})

    def test_mismatch_stops_without_second_generation_or_success(self):
        self.child.generate.side_effect = [{'raw': 'different'}]
        with self.assertRaisesRegex(ValueError, 'exact_committed_generation_match'):
            self.replay()
        self.assertEqual(self.child.generate.call_count, 1)
        self.assertFalse((self.destination / 'GENERATIONS_VERIFIED.json').exists())
        self.data.journal.record.assert_not_called()

    def test_raw_history_mutation_refused(self):
        def generated(*args, **kwargs):
            self.data.snapshot['state']['history'].append('changed')
            return self.data.records[2]['document']['response']
        self.child.generate.side_effect = generated
        with self.assertRaisesRegex(ValueError, 'no_replay_history_or_plan_mutation'):
            self.replay()

    def test_learning_mutation_refused(self):
        self.child.optimizer_steps = 1923
        with self.assertRaisesRegex(ValueError, 'no_replay_learning_mutation'):
            self.replay()

    def test_stale_manifest_head_refused_before_restore(self):
        self.provenance['journal']['journal_head'] = 'different'
        with self.assertRaisesRegex(ValueError, 'CPU_bound_journal_before_replay'):
            self.replay()
        recovery.restore.assert_not_called()
        self.child.generate.assert_not_called()

    def test_deadline_not_extended(self):
        with patch.object(recovery.time, 'time', return_value=9999999999):
            with self.assertRaisesRegex(ValueError, 'replay_within_original_wall'):
                self.replay()
        self.child.generate.assert_not_called()

    def test_replay_evidence_cannot_be_overwritten(self):
        recovery.save(self.destination / '00_REQUEST.json', {'previous': True})
        with self.assertRaises(FileExistsError):
            self.replay()
        self.child.generate.assert_not_called()


class TargetTests(unittest.TestCase):
    def test_only_specialtokens_excluded_in_both_cohorts_raw_unchanged(self):
        from gpu import orch_r125_continual_native as native
        rows = [dict(source_sha256=name, target=name) for name in ('old-good', 'old-bad', 'new-good', 'new-bad')]
        original = deepcopy(rows)
        stream = SimpleNamespace(rows=rows, sleep_frontier=2, pending_rows=lambda: rows[2:])
        plan = dict(context_limit=100)

        def encode(row, tokenizer, limit):
            if row['source_sha256'].endswith('bad'):
                raise ValueError('no_special_token_target_injection')
            return SimpleNamespace(input_ids=[1, 2, 3])

        with patch.object(native, 'encode_own', side_effect=encode):
            result = recovery.target_contract(plan, stream, object())
        self.assertEqual(rows, original)
        self.assertEqual(result['expected_updates'], 17)
        self.assertEqual(result['expected_total_steps'], 1939)
        self.assertEqual([item['cohort'] for item in result['eligibility']['excluded']], ['NEW', 'REHEARSAL'])
        self.assertEqual(result['eligibility']['new_row_sha256'], ['new-good'])
        self.assertEqual(result['eligibility']['rehearsal_row_sha256'], ['old-good'])
        self.assertFalse(result['eligibility']['raw_modified'])
        self.assertEqual(result['all_rows_checked'], 4)

    def test_other_encoder_errors_not_suppressed(self):
        from gpu import orch_r125_continual_native as native
        stream = SimpleNamespace(rows=[{'source_sha256': 'bad'}], sleep_frontier=0,
                                 pending_rows=lambda: [{'source_sha256': 'bad'}])
        with patch.object(native, 'encode_own', side_effect=ValueError('native_target_roundtrip')):
            with self.assertRaisesRegex(ValueError, 'native_target_roundtrip'):
                recovery.target_contract({'context_limit': 100}, stream, object())

    def test_presentation_exclusions_not_newly_permitted(self):
        from organism_v6 import orch_r125_plain_context as presentation
        data = fixture()
        with patch.object(presentation, 'eligible_rows', return_value=([], [{'reason': 'other'}])):
            with self.assertRaisesRegex(ValueError, 'only_actual_specialtoken_exclusions'):
                recovery.target_contract(data.plan, data.stream, object())


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.targets = dict(eligibility={'excluded': ['special'], 'raw_modified': False},
                            schedule=[dict(cohort='NEW', source_sha256='new'),
                                      dict(cohort='REHEARSAL', source_sha256='old')], expected_updates=2)
        self.metadata = dict(runtime_memory_policy='R145', runtime_sha256='runtime', GPU_validation_sha256='proof')
        self.journal = SimpleNamespace(record=Mock())
        self.recorder = recovery.SleepRecorder(self.journal, self.targets, self.metadata)

    def begin(self):
        self.recorder('TARGET_ELIGIBILITY', self.targets['eligibility'])
        self.recorder('CHECKPOINT_METADATA', self.metadata)

    def update(self, position):
        row = self.targets['schedule'][position]
        return dict(optimizer_step=1923 + position, source_sha256=row['source_sha256'],
                    losses=[{'kind': row['cohort']}])

    def test_exact_schedule_logs_unmodified_native_documents(self):
        self.begin()
        for position in range(2):
            self.recorder('UPDATE', self.update(position))
        self.recorder.complete()
        self.assertEqual(self.journal.record.call_count, 4)
        self.assertEqual(self.journal.record.call_args.args, ('UPDATE', self.update(1)))

    def test_changed_exclusions_rejected_before_journal_append(self):
        with self.assertRaisesRegex(ValueError, 'exact_once_CPU_eligibility'):
            self.recorder('TARGET_ELIGIBILITY', {'excluded': [], 'raw_modified': False})
        self.journal.record.assert_not_called()

    def test_missing_R145_metadata_cannot_update(self):
        self.recorder('TARGET_ELIGIBILITY', self.targets['eligibility'])
        with self.assertRaisesRegex(ValueError, 'no_extra_or_unadmitted_updates'):
            self.recorder('UPDATE', self.update(0))

    def test_wrong_step_source_or_cohort_refused(self):
        self.begin()
        for key, value in (('optimizer_step', 1831), ('source_sha256', 'special'), ('losses', [{'kind': 'REHEARSAL'}])):
            with self.subTest(key=key):
                update = self.update(0)
                update[key] = value
                with self.assertRaisesRegex(ValueError, 'exact_contiguous_CPU_update_schedule'):
                    self.recorder('UPDATE', update)

    def test_incomplete_sleep_and_extra_update_refused(self):
        self.begin()
        with self.assertRaisesRegex(ValueError, 'complete_CPU_bound_sleep_schedule'):
            self.recorder.complete()
        for position in range(2):
            self.recorder('UPDATE', self.update(position))
        with self.assertRaisesRegex(ValueError, 'no_extra_or_unadmitted_updates'):
            self.recorder('UPDATE', self.update(0))

    def test_duplicate_eligibility_and_unknown_events_refused(self):
        self.begin()
        with self.assertRaises(ValueError):
            self.recorder('TARGET_ELIGIBILITY', self.targets['eligibility'])
        with self.assertRaisesRegex(ValueError, 'unexpected_pending_sleep_event'):
            self.recorder('COMMITTED', {})


class RestoreTests(unittest.TestCase):
    def test_saved_optimizer_and_all_three_rng_domains_restored(self):
        class AdamW:
            load_state_dict = Mock()

        payload = dict(parameter_names=['lora'], optimizer_steps=1922, experiment={'seed': 1}, optimizer={'state': {}},
                       cpu_rng=SimpleNamespace(tolist=lambda: [1]),
                       cuda_rng=[SimpleNamespace(tolist=lambda: [2])], python_rng=random.Random(23).getstate())
        torch = SimpleNamespace(optim=SimpleNamespace(AdamW=AdamW), set_rng_state=Mock(),
                                cuda=SimpleNamespace(set_rng_state_all=Mock()))
        child = SimpleNamespace(torch=torch, optimizer=AdamW(), parameters={'lora': object()},
                                experiment=payload['experiment'], optimizer_steps=1922,
                                adapter_hash=lambda: 'adapter', verify_checkpoint=Mock(),
                                engine=SimpleNamespace(verify_base=Mock()))
        expected_rng = dict(python=recovery.digest(payload['python_rng']), cpu=recovery.digest([1]),
                            cuda=[recovery.digest([2])])
        original_python_rng = random.getstate()
        self.addCleanup(random.setstate, original_python_rng)
        with patch.object(recovery, 'checkpoint_payload', return_value=payload), \
                patch.object(recovery, 'optimizer_fingerprint', return_value='optimizer'), \
                patch.object(recovery, 'rng', return_value=expected_rng):
            self.assertEqual(recovery.restore(child, {'adapter_state_sha256': 'adapter'}), 'optimizer')
        child.optimizer.load_state_dict.assert_called_once_with(payload['optimizer'])
        torch.set_rng_state.assert_called_once_with(payload['cpu_rng'])
        torch.cuda.set_rng_state_all.assert_called_once_with(payload['cuda_rng'])
        self.assertEqual(random.getstate(), payload['python_rng'])


class FinishTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.destination = Path(self.directory.name)
        self.data = fixture()
        self.targets = dict(eligibility={'excluded': ['actual-special'], 'raw_modified': False},
                            schedule=[{'cohort': 'NEW', 'source_sha256': 'retained'}],
                            expected_updates=1, expected_total_steps=1923)
        self.metadata = {'existing': 'R145'}
        self.saved = dict(optimizer_steps=1923, experiment=self.data.stream.experiment,
                          checkpoint_sha256={'adapter': 'new', 'optimizer': 'new', 'rng': 'new'})
        self.child = SimpleNamespace(plan=self.data.plan, optimizer_steps=1922,
                                    adapter_hash=lambda: 'adapter', checkpoint=Mock(return_value=self.saved))
        self.scan = patch.object(recovery, 'journal_records', return_value=(self.data.state, self.data.records))
        self.scan.start()
        self.addCleanup(self.scan.stop)
        binding, unused = recovery.journal_binding(self.data.plan, self.data.stream, self.data.journal, self.data.checkpoint)
        self.provenance = dict(journal=binding, evidence=dict(checkpoint=self.data.checkpoint, sleep_metadata=self.metadata),
                               targets=self.targets)
        self.replay = dict(rng_after={'state': 'replayed'}, optimizer_state_sha256='optimizer', matched_generations=2)
        recovery.save(self.destination / 'GENERATIONS_VERIFIED.json', self.replay)
        for name, value in (('rng', {'state': 'replayed'}), ('optimizer_fingerprint', 'optimizer'),
                            ('verify_saved_files', None)):
            replacement = patch.object(recovery, name, return_value=value)
            replacement.start()
            self.addCleanup(replacement.stop)
        root = patch.object(recovery, 'ROOT', self.destination / 'run1')
        root.start()
        self.addCleanup(root.stop)
        self.data.journal.root = recovery.ROOT / 'stream'
        self.data.plan['root'] = str(recovery.ROOT)
        self.data.stream.commit_sleep = Mock()

        def sleep(new_rows, old_rows, anchors, record):
            record('TARGET_ELIGIBILITY', self.targets['eligibility'])
            record('CHECKPOINT_METADATA', self.metadata)
            record('UPDATE', dict(optimizer_step=1923, source_sha256='retained', losses=[{'kind': 'NEW'}]))
            self.child.optimizer_steps = 1923
            return dict(optimizer_steps=1, total_optimizer_steps=1923, excluded_rows=['actual-special'],
                        presentations={'retained': 1})

        self.child.sleep = Mock(side_effect=sleep)

    def finish(self):
        return recovery.finish_pending_sleep(self.child, self.data.stream, self.data.journal, {},
                                             self.provenance, self.replay, self.destination)

    def test_finishes32_without_repeating_requests_or_modifying_raw_history(self):
        before = deepcopy(self.data.snapshot)
        result = self.finish()
        self.assertEqual(result, self.saved)
        self.assertEqual(self.data.snapshot, before)
        self.child.checkpoint.assert_called_once_with(recovery.ROOT / 'checkpoints' / 'sleep_000032')
        receipt = self.data.stream.commit_sleep.call_args.args[0]
        self.assertEqual(receipt['cycle'], 32)
        self.assertEqual(receipt['new_row_sha256'], [row['source_sha256'] for row in self.data.stream.rows])
        self.assertIsNone(self.data.stream.pending)
        self.assertTrue((self.destination / 'SLEEP32_SAVED.json').exists())
        self.assertNotIn('REQUEST', [call.args[0] for call in self.data.journal.record.call_args_list])

    def test_existing32_checkpoint_refuses_before_sleep(self):
        (recovery.ROOT / 'checkpoints' / 'sleep_000032').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'never_repeat_checkpointed_sleep32'):
            self.finish()
        self.child.sleep.assert_not_called()

    def test_wrong_exclusions_cannot_checkpoint(self):
        original = self.child.sleep.side_effect

        def changed(*args):
            result = original(*args)
            result['excluded_rows'] = []
            return result

        self.child.sleep.side_effect = changed
        with self.assertRaisesRegex(ValueError, 'completed_exact_exclusions_and_schedule'):
            self.finish()
        self.child.checkpoint.assert_not_called()
        self.data.stream.commit_sleep.assert_not_called()

    def test_stale_replay_rng_refuses_before_sleep(self):
        with patch.object(recovery, 'rng', return_value={'state': 'changed'}):
            with self.assertRaisesRegex(ValueError, 'same_restored_replayed_child'):
                self.finish()
        self.child.sleep.assert_not_called()


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.module_hash = recovery.sha(Path(recovery.__file__).absolute())
        self.evidence = dict(source_pins={'runtime.py': self.module_hash})
        self.provenance = dict(schema=recovery.SCHEMA, status='PASS', CPU_only=True, held_contents_read=False,
                               module_sha256=self.module_hash, plan={'recipe': 'original'}, evidence=self.evidence)
        recovery.save(self.root / 'provenance.json', self.provenance)
        recovery.save_bytes(self.root / 'tests.log', b'CPU tests: PASS\n')
        self.gate = dict(status='PASS', exit_code=0, tests=recovery.reference(self.root / 'tests.log'),
                         provenance=recovery.reference(self.root / 'provenance.json'), source_pins=self.evidence['source_pins'],
                         module_sha256=self.module_hash, finished_unix=1)
        recovery.save(self.root / 'gate.json', self.gate)
        self.gate_ref = recovery.reference(self.root / 'gate.json')
        self.evidence_patch = patch.object(recovery, 'pinned_evidence', return_value=self.evidence)
        self.evidence_patch.start()
        self.addCleanup(self.evidence_patch.stop)

    def manifest(self):
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
            return recovery.make_manifest(self.provenance['plan'], self.provenance, self.gate_ref)

    def ack(self, manifest, **changes):
        document = dict(author='Main', approved=True, manifest_sha256=recovery.digest(manifest))
        document.update(changes)
        path = self.root / 'ACK.json'
        recovery.save(path, document)
        return recovery.reference(path)

    def test_Main_gate_binds_tests_provenance_module_and_closure(self):
        manifest = self.manifest()
        result = recovery.verify_manifest(manifest, self.ack(manifest))
        self.assertEqual(result, self.provenance)
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
            self.assertEqual(recovery.build_manifest(self.provenance['plan'], recovery.ORIGINAL_GUARD, self.gate_ref), manifest)

    def test_wrong_author_or_wrong_manifest_digest_refused(self):
        manifest = self.manifest()
        with self.assertRaisesRegex(ValueError, 'exact_Main_ACK_required'):
            recovery.verify_manifest(manifest, self.ack(manifest, author='Runtime'))

    def test_changed_manifest_not_authorized_by_old_ACK(self):
        manifest = self.manifest()
        ack = self.ack(manifest)
        manifest['provenance']['plan']['recipe'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'exact_Main_ACK_required'):
            recovery.verify_manifest(manifest, ack)

    def test_changed_CPU_test_log_refused(self):
        manifest = self.manifest()
        ack = self.ack(manifest)
        (self.root / 'tests.log').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'bound_real_CPU_test_log'):
            recovery.verify_manifest(manifest, ack)

    def test_changed_source_checkpoint_or_failure_evidence_refused(self):
        manifest = self.manifest()
        ack = self.ack(manifest)
        with patch.object(recovery, 'pinned_evidence', return_value={'changed': True}):
            with self.assertRaisesRegex(ValueError, 'all_original_staged_checkpoint_evidence_unchanged'):
                recovery.verify_manifest(manifest, ack)

    def test_manifest_builder_is_CPU_only(self):
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '7'}):
            with self.assertRaisesRegex(ValueError, 'CPU_only_manifest_build'):
                recovery.make_manifest(self.provenance['plan'], self.provenance, self.gate_ref)

    def test_source_closure_detects_added_files(self):
        recovery.save_bytes(self.root / 'module.py', b'value = 1\n')
        first = recovery.source_closure(self.root)
        recovery.save_bytes(self.root / 'extra.py', b'value = 2\n')
        self.assertNotEqual(first, recovery.source_closure(self.root))


class ContainmentTests(unittest.TestCase):
    def test_exact_R137_functions_relocate_only_entrypoint_literals(self):
        from gpu import orch_r137_node4_containment as node
        manifest = {'provenance': {'evidence': {'original_source_pins': {
            recovery.NODE: recovery.sha(Path(node.__file__).absolute())}}}}
        for action in ('contained_supervise', 'contained_native'):
            with self.subTest(action=action):
                adapted = recovery.adapted_node_function(action, manifest)
                self.assertEqual(adapted.__name__, action)
                before = 'gpu.orch_r137_node4_containment' if action == 'contained_supervise' else 'gpu.orch_r125_continual_guard'
                self.assertIn(recovery.MODULE, adapted.__code__.co_consts)
                self.assertNotIn(before, adapted.__code__.co_consts)
                self.assertEqual(adapted.__globals__['scan'], node.scan)
                self.assertEqual(adapted.__globals__['verify_device_containment'], node.verify_device_containment)
                if action == 'contained_supervise':
                    with self.assertRaisesRegex(ValueError, 'original_identity_and_minor'):
                        adapted.__globals__['device_containment_command'](7, 3, 2524, 2524, 'unit', 'source', [], 1)

    def test_allocator_preserves_strict_original_devices(self):
        from gpu import orch_r137_node4_containment as node
        command = node.device_containment_command(7, 4, 2524, 2524, 'orch-r136-native-' + 'a' * 32,
                                                  '/source', ['python'], 300)
        result = recovery.allocator_command(command)
        self.assertIn('PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True', result)
        self.assertIn('--property=DevicePolicy=strict', result)
        self.assertIn('CUDA_VISIBLE_DEVICES=' + recovery.GPU_UUID, result)
        self.assertEqual([item for item in result if 'DeviceAllow=' in item],
                         [item for item in command if 'DeviceAllow=' in item])
        with self.assertRaisesRegex(ValueError, 'no_conflicting_allocator'):
            recovery.allocator_command(result)

    def test_foreign_device_allow_is_rejected(self):
        from gpu import orch_r137_node4_containment as node
        command = node.device_containment_command(7, 4, 2524, 2524, 'orch-r136-native-' + 'a' * 32,
                                                  '/source', ['python'], 300)
        command.insert(1, '--property=DeviceAllow=/dev/nvidia3 rw')
        with self.assertRaisesRegex(ValueError, 'only_a40r7_physical7'):
            recovery.allocator_command(command)

    def test_no_R145_hardcoded_restore_or_dispatch(self):
        source = Path(recovery.__file__).read_text()
        tree = ast.parse(source)
        forbidden = {'restore', 'recover_rng', 'recover_admitted_sleep', 'verify_manifest', 'pinned_evidence', 'PINS'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'previous':
                self.assertNotIn(node.attr, forbidden)

    def test_failure_marker_preserves_original_error_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'FAILED.json'
            recovery.failed(path, ValueError('before model'), 'native')
            first = path.read_bytes()
            recovery.failed(path, ValueError('second'), 'native')
            self.assertEqual(path.read_bytes(), first)
            self.assertEqual(json.loads(first)['error'], 'before model')


if __name__ == '__main__':
    unittest.main()
