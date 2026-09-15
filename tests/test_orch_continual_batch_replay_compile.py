from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import orch_continual_batch as policy
from organism_v6 import orch_continual_batch_replay_compile as compiler
from tests.test_orch_continual_batch import fixture as math_fixture
from gpu import orch_continual_batch_replay_compile as runner


class ReplayCompileTests(unittest.TestCase):
    def fixture(self):
        root='/native/registered-own-replay'
        registration=dict(source_kind='CHECKPOINT_DERIVED_TRAIN',source_purpose='L1_EXTERNAL_GENERATION',split='TRAIN',
            parenting_experience=False,teacher_exemplars=False,held_readout_outputs=False,native_root=root,
            allowlisted_generation_roots=[root],source_state_sha256='c'*64,base_sha256=compiler.BASE,
            lineage=dict(child_state_sha256='c'*64,checkpoint_manifest_sha256='d'*64),eos_token_id=9)
        row=dict(actor=dict(state_sha256='c'*64,base_sha256=compiler.BASE),task_id='train-one',question_sha256='q',
            student_prefix=[dict(role='user',content='TRAIN problem')],target='own solution',target_sha256=policy.text_sha('own solution'),
            mechanical_pass=True,outcome_pass=True,token_contract_pass=True,batch_training_allowed=True,review=None,
            provenance=dict(source_native_path=root+'/call.json',raw_call_sha256='a'*64,parenting_experience=False,
                source_purpose='L1_EXTERNAL_GENERATION'),training_encoding=dict(input_ids=[7,1,2,9,8],labels=[-100,1,2,9,-100]))
        call=dict(response=dict(raw='own solution',terminal=True,truncated=False,token_ids=[1,2,9]))
        return row,call,registration,dict(math_ids=[],question_hashes=[],route_ids=[])

    def test_unsampled_semantics_stay_unknown(self):
        result=compiler.compile_row(*self.fixture())
        self.assertEqual(result['individual_semantic_status'],'UNREVIEWED')
        self.assertEqual(result['coherence_tag'],'UNKNOWN')
        self.assertIsNone(result['branch_metrics']['semantic_distinct_approaches_pursued'])

    def test_held_teacher_parenting_never_compile(self):
        for key in ('parenting_experience','teacher_exemplars','held_readout_outputs'):
            row,call,registration,exclusions=self.fixture();registration[key]=True
            with self.assertRaises(ValueError):compiler.compile_row(row,call,registration,exclusions)
        row,call,registration,exclusions=self.fixture();registration['split']='HELD'
        with self.assertRaises(ValueError):compiler.compile_row(row,call,registration,exclusions)

    def test_wrong_actor_rejected(self):
        row,call,registration,exclusions=self.fixture();row['actor']['state_sha256']='e'*64
        with self.assertRaisesRegex(ValueError,'checkpoint'):compiler.compile_row(row,call,registration,exclusions)

    def test_prefix_supervision_rejected(self):
        row,call,registration,exclusions=self.fixture();row['training_encoding']['labels'][0]=7
        with self.assertRaisesRegex(ValueError,'only_exact'):compiler.compile_row(row,call,registration,exclusions)

    def test_held_id_rejected(self):
        row,call,registration,exclusions=self.fixture();exclusions['math_ids']=[row['task_id']]
        with self.assertRaisesRegex(ValueError,'held_source'):compiler.compile_row(row,call,registration,exclusions)

    def test_mixed_append_is_not_isolated_own_output_claim(self):
        row,call,registration,exclusions=self.fixture()
        record=compiler.handoff([compiler.compile_row(row,call,registration,exclusions)],registration,'/native/ROWS.json','f'*64)
        self.assertEqual(record['fit_scope'],'CURRENT_MIXED_CONTINUAL_APPEND')
        self.assertFalse(record['paired_fit_executed'])
        self.assertFalse(record['held_readout_executed'])
        registration['fit_scope']='ISOLATED_PAIRED_WINDOW'
        with self.assertRaisesRegex(ValueError,'paired_window'):compiler.handoff([],registration,'/native/ROWS.json','f'*64)

    def bound_fixture(self, root):
        def save(name, value):
            path = root / name
            path.write_text(json.dumps(value, sort_keys=True))
            return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        call, task, unused_loaded, unused_prepared, tokenizer = math_fixture()
        actor = dict(state_sha256='c' * 64, base_sha256=compiler.BASE)
        exclusions = dict(math_ids=[], question_hashes=[], route_ids=[])
        checkpoint = save('CHECKPOINT.json', dict(adapter=actor))
        registration = dict(source_kind='CHECKPOINT_DERIVED_TRAIN', source_purpose='L1_EXTERNAL_GENERATION',
            split='TRAIN', parenting_experience=False, teacher_exemplars=False, held_readout_outputs=False,
            native_root=str(root), allowlisted_generation_roots=[str(root)], source_state_sha256=actor['state_sha256'],
            base_sha256=compiler.BASE, lineage=dict(child_state_sha256=actor['state_sha256'],
            checkpoint_manifest_sha256=checkpoint['sha256']), eos_token_id=tokenizer.eos_token_id)
        registration_ref = save('REGISTRATION.json', registration)
        source_registry = save('SOURCE_REGISTRY.json', dict(sources={str(root): registration}))
        rows = []
        for index in range(64):
            current = deepcopy(call)
            target = f'Check {index}: 2+3=5.\nFINAL: 5'
            current['response'].update(raw=target, token_ids=tokenizer.encode(target) + [tokenizer.eos_token_id])
            native = save(f'CALL_{index}.json', current)
            intent = save(f'INTENT_{index}.json', {key: current[key] for key in ('task_id', 'messages', 'stage')})
            provenance = dict(source_native_path=native['path'], raw_call_sha256=native['sha256'],
                native_intent_ref=intent, registered_source_purpose=policy.PURPOSE, source_registry_sha256=source_registry['sha256'],
                source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False)
            rows.append(policy.mechanical(current, task, dict(observed=actor), dict(initial=actor),
                                          tokenizer, exclusions, provenance))
        candidates = save('CANDIDATES.json', rows)
        selected = policy.sample(rows)
        reviews = [dict(target_sha256=row['target_sha256'], raw_call_sha256=row['provenance']['raw_call_sha256'],
            student_prefix_sha256=row['student_prefix_sha256'], status='PASS', full_text_read=True,
            reason='Correct addition shown.', evidence_spans=['2+3=5'], gold_status='VALID', independent_answer='5',
            **dict.fromkeys(policy.AXES, True)) for row in selected]
        request = dict(native_evidence_root=str(root), registration=registration_ref, source_registry=source_registry,
            exclusions=save('EXCLUSIONS.json', exclusions), checkpoint_handoff=checkpoint,
            loaded=save('LOADED.json', dict(observed=actor)), tasks=save('TASKS.json', dict(tasks=[task])),
            candidates=candidates, reviews=save('REVIEWS.json', reviews), sample=save('SAMPLE.json',
            dict(semantic_results_seen=False, candidates_sha256=candidates['sha256'],
                 registration_sha256=registration_ref['sha256'], sample_target_sha256s=[row['target_sha256'] for row in selected])))
        return request, tokenizer, save

    def test_bound_batch_recomputes_all_native_masks_and_outcomes(self):
        with tempfile.TemporaryDirectory() as directory:
            request, tokenizer, unused_save = self.bound_fixture(Path(directory))
            result = compiler.compile_bound_batch(request, tokenizer)
            self.assertEqual(len(result['compiled']), 64)
            self.assertEqual(sum(row['individual_semantic_status'] == 'PASS' for row in result['compiled']), 12)
            self.assertEqual(sum(row['individual_semantic_status'] == 'UNREVIEWED' for row in result['compiled']), 52)
            self.assertEqual(result['skipped'], [])

    def test_changed_raw_bytes_not_trusted_from_row_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, tokenizer, unused_save = self.bound_fixture(root)
            (root / 'CALL_0.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'immutable_file_hash'):
                compiler.compile_bound_batch(request, tokenizer)

    def test_bound_checkpoint_identity_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            request, tokenizer, save = self.bound_fixture(Path(directory))
            request['loaded'] = save('LOADED_CHANGED.json', dict(observed=dict(state_sha256='e'*64, base_sha256=compiler.BASE)))
            with self.assertRaisesRegex(ValueError, 'native_loaded_child'):
                compiler.compile_bound_batch(request, tokenizer)

    def test_retroactive_sample_registration_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            request, tokenizer, save = self.bound_fixture(Path(directory))
            sample = json.loads(Path(request['sample']['path']).read_text())
            sample['semantic_results_seen'] = True
            request['sample'] = save('SAMPLE_LATE.json', sample)
            with self.assertRaisesRegex(ValueError, 'prospective_sample'):
                compiler.compile_bound_batch(request, tokenizer)

    def test_parenting_registry_not_accepted_by_safe_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            request, tokenizer, save = self.bound_fixture(Path(directory))
            registry = json.loads(Path(request['source_registry']['path']).read_text())
            registry['sources'][directory]['source_purpose'] = 'L2_PARENTING'
            request['source_registry'] = save('SAFE_L1_FILENAME.json', registry)
            with self.assertRaisesRegex(ValueError, 'registered_source_purpose_or_identity_drift'):
                compiler.compile_bound_batch(request, tokenizer)

    def test_unregistered_symlink_target_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'native'
            root.mkdir()
            outside = Path(directory) / 'outside.json'
            outside.write_text('{}')
            (root / 'escape.json').symlink_to(outside)
            with self.assertRaisesRegex(ValueError, 'outside_registered_native_root'):
                compiler.read_bound(dict(path=str(root / 'escape.json'), sha256=hashlib.sha256(b'{}').hexdigest()), root)

    def test_oversized_encoding_rejected_without_mutation(self):
        row, call, registration, exclusions = self.fixture()
        row['training_encoding'] = dict(input_ids=[7] * 2049, labels=[-100] * 2049)
        original = deepcopy(row)
        with self.assertRaisesRegex(ValueError, 'exact_supported_context_no_crop'):
            compiler.compile_row(row, call, registration, exclusions)
        self.assertEqual(row, original)

    def test_cli_cannot_run_from_worktree(self):
        with patch.dict('os.environ', {'CUDA_VISIBLE_DEVICES': ''}):
            with self.assertRaisesRegex(ValueError, 'outside_worktree_runtime_required'):
                runner.execute(Path('/nonexistent/request'), 'a' * 64, Path('/nonexistent/output'))

    def test_cli_requires_cpu_only(self):
        with patch.dict('os.environ', {'CUDA_VISIBLE_DEVICES': '0'}):
            with self.assertRaisesRegex(ValueError, 'cpu_only_compile'):
                runner.execute(Path('/nonexistent/request'), 'a' * 64, Path('/nonexistent/output'))

    def checkpoint99_fixture(self):
        call, task, unused_loaded, unused_prepared, unused_tokenizer = math_fixture()
        row, unused_call, registration, unused_exclusions = self.fixture()
        registration.update(native_format='NODE2_CHECKPOINT99_MATH_V1', source_code_sha256='e' * 64)
        registration['lineage']['checkpoint_commit_sha256'] = 'f' * 64
        call.update(family='math', stage='final_0', condition='ORIGINAL_RICH', task_id='B000-P03',
                    source_task_id=task['id'], generator_identity=row['actor'], trainingAllowed=False,
                    source_code_sha256='e' * 64, source_checkpoint_commit_sha256='f' * 64,
                    outcome=dict(correct=True, admitted=False))
        return call, task, registration, dict(original_native_task_id='B000-P03')

    def test_checkpoint99_adapter_preserves_original_capture(self):
        call, task, registration, provenance = self.checkpoint99_fixture()
        before = deepcopy(call)
        result = compiler.normalize_native_call(call, task, registration, provenance)
        self.assertEqual(call, before)
        self.assertEqual(result['task_id'], task['id'])
        self.assertEqual(result['response'], before['response'])
        self.assertEqual(result['messages'], before['messages'])
        self.assertEqual(result['stage'], 'source')

    def test_checkpoint99_wrong_answer_never_fixed(self):
        call, task, registration, provenance = self.checkpoint99_fixture()
        call['response']['raw'] = 'FINAL: 7'
        with self.assertRaisesRegex(ValueError, 'original_math_oracle_failure'):
            compiler.normalize_native_call(call, task, registration, provenance)

    def test_checkpoint99_code_or_wrong_checkpoint_never_compiled(self):
        for key, value in (('family', 'code'), ('source_checkpoint_commit_sha256', 'a' * 64)):
            call, task, registration, provenance = self.checkpoint99_fixture()
            call[key] = value
            with self.assertRaises(ValueError):
                compiler.normalize_native_call(call, task, registration, provenance)


if __name__ == '__main__':
    unittest.main()
