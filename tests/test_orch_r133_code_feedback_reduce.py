import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r133_code_feedback_collection as collection
from gpu import orch_r133_code_feedback_reduce as reducer


SEED = '9a' * 32


def write_json(path, document):
    path.write_text(json.dumps(document, sort_keys=True, indent=2) + '\n')


def solution(task):
    threshold, factor, offset = task['threshold'], task['factor'], task['offset']
    low, high = task['low'], task['high']
    return (f'sum(affine(ge(values,{threshold}),{factor},{offset}))',
            f'sum(unique(clip(affine(values,{factor},{offset}),{low},{high})))',
            f'sum(affine(ge(unique(values),{threshold}),{factor},{offset}))',
            f'len(ge(affine(clip(values,{low},{high}),{factor},{offset}),{threshold}))')[task['kind']]


def make_run(root):
    inventory = dict(schema='R133_HASH_ONLY_EXCLUSIONS_V1', normalization=collection.public.NORMALIZATION,
                     attested_by='Main', coverage='R119_LINEAGE_DECLARED_CODE_INVENTORIES',
                     inventory_refs=[dict(ref='CPU_SYNTHETIC_HASH_PROJECTION', sha256='c' * 64)],
                     spec_sha256=['a' * 64], task_id_sha256=[], used_seed_sha256=[])
    collection.prepare(root, SEED, inventory)
    plan_hash = collection.sha(root / 'PLAN.json')
    tasks = collection.read(root / 'TASKS.json')['tasks']
    adapter = dict(path='/CPU_TEST_ONLY_NOT_REAL_WEIGHTS', base_sha256=collection.public.BASE_SHA,
                   state_sha256='b' * 64, files=[['CPU_TEST_ONLY', 'c' * 64]])
    collection.write(root / 'NATIVE_START.json', dict(authorization=dict(plan_sha256=plan_hash,
                     checkpoint=18404, approved_by='Main', host_sha256='d' * 64, adapter=adapter)))
    collection.write(root / 'LOADED.json', dict(adapter=adapter, optimizer_count=0, model_states=list(collection.MODELS)))
    calls = []

    def generate(prefix, model):
        position = len(calls) // 6
        calls.append(model)
        stage = 'draft' if len(prefix) == 2 else ('interpreter_feedback' if prefix[-1]['content'].startswith('Actual') else 'neutral_review')
        correct = solution(tasks[position])
        expressions = {
            0: dict(draft=correct, interpreter_feedback=correct, neutral_review='0'),
            1: dict(draft='0', interpreter_feedback=correct, neutral_review='0'),
            2: dict(draft='0', interpreter_feedback='0', neutral_review=correct),
            3: dict(draft=correct, interpreter_feedback='0', neutral_review=correct),
            4: dict(draft='sum(xs)', interpreter_feedback=correct, neutral_review=correct),
            5: dict(draft='0', interpreter_feedback=correct, neutral_review=correct),
            6: dict(draft=correct, interpreter_feedback=correct, neutral_review=correct),
        }
        expression = expressions.get(position, {}).get(stage, '0') if model == 'FULL_FIXED18404' else '0'
        raw = 'PRIVATE_RAW_SENTINEL\n' + json.dumps({'expression': expression})
        if position == 0 and stage == 'draft' and model == 'FULL_FIXED18404':
            raw = '```json\n' + json.dumps({'expression': expression}) + '\n```'
        capped = position == 5 and stage == 'interpreter_feedback' and model == 'FULL_FIXED18404'
        return dict(messages=copy.deepcopy(prefix), prompt_tokens=128, raw=raw,
                    token_ids=[73] * collection.MAX_NEW_TOKENS if capped else [73, 74],
                    terminal=not capped, truncated=capped,
                    max_new_tokens=collection.MAX_NEW_TOKENS, context=collection.CONTEXT_LIMIT)

    collection.run_episodes(root, tasks, generate)
    collection.write(root / 'NATIVE_TERMINAL.json', dict(status='COMPLETE', weights_verified_unchanged=True, completed_calls=96))
    collection.write(root / 'EXIT.json', dict(exit_code=0))
    collection.write(root / 'SUPERVISOR_COMPLETE.json', dict(status='COMPLETE',
                     native_terminal_sha256=collection.sha(root / 'NATIVE_TERMINAL.json')))
    return plan_hash, tasks


class ReductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storage = tempfile.TemporaryDirectory()
        cls.template = Path(cls.storage.name) / 'synthetic_template'
        cls.plan_hash, cls.tasks = make_run(cls.template)

    @classmethod
    def tearDownClass(cls):
        cls.storage.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'synthetic_copy'
        shutil.copytree(self.template, self.root)

    def run_reduction(self):
        return reducer.reduce(self.root, expected_plan_sha256=self.plan_hash)

    def path(self, position=0, model='FULL_FIXED18404', stage='interpreter_feedback', kind='CALL'):
        return self.root / 'episodes' / self.tasks[position]['id'] / model / (stage + '.' + kind + '.json')

    def mutate(self, path, function):
        document = collection.read(path)
        function(document)
        write_json(path, document)

    def assert_withheld(self, result, status):
        self.assertEqual(result['status'], status, result['error_codes'])
        self.assertTrue(result['outcomes_withheld'])
        self.assertIsNone(result['model_results'])
        self.assertEqual(len(result['cells']), 96)
        self.assertTrue(all(cell['outcome'] is None for cell in result['cells']))

    def test_all_cells_and_per_model_denominators_with_paired_contrasts(self):
        result = self.run_reduction()
        self.assertEqual(result['status'], 'COMPLETE', result['error_codes'])
        self.assertFalse(result['outcomes_withheld'])
        self.assertEqual(len(result['cells']), 96)
        self.assertEqual({cell['planned_call'] for cell in result['cells']}, set(range(1, 97)))
        full = result['model_results']['FULL_FIXED18404']
        base = result['model_results']['BASE_NO_LORA']
        self.assertEqual(full['planned_calls'], 48)
        self.assertEqual(full['stages']['draft']['passed_complete'], 2)
        self.assertEqual(full['stages']['interpreter_feedback']['complete'], 15)
        self.assertEqual(full['stages']['interpreter_feedback']['passed_complete'], 4)
        self.assertEqual(full['stages']['neutral_review']['passed_complete'], 5)
        self.assertEqual(full['paired_contrast']['pass_table'],
                         dict(both_pass=2, feedback_only_pass=2, neutral_only_pass=2, both_fail=9))
        self.assertEqual(full['paired_contrast']['feedback_minus_neutral_pass_rate'],
                         dict(numerator=0, denominator=15, value=0.0))
        self.assertEqual(full['paired_contrast']['common_complete_failed_drafts'], 13)
        self.assertEqual(full['forks']['interpreter_feedback']['recoveries']['formatting_only_recovery'], 1)
        self.assertEqual(full['forks']['interpreter_feedback']['recoveries']['task_semantic_correction'], 1)
        self.assertEqual(full['forks']['interpreter_feedback']['recoveries']['unclassified_recovery'], 1)
        self.assertEqual(full['forks']['interpreter_feedback']['regressions'], 1)
        formatting_cell = next(cell for cell in result['cells'] if cell['planned_call'] == 2)
        self.assertTrue(formatting_cell['comparison_to_shared_draft']['formatting_only_recovery'])
        self.assertFalse(formatting_cell['comparison_to_shared_draft']['task_semantic_correction'])
        self.assertEqual(full['forks']['neutral_review']['failed_to_passed_rate'],
                         dict(numerator=3, denominator=14, value=3 / 14))
        self.assertEqual(full['paired_contrast']['recovery_contrasts']['failed_to_passed'],
                         dict(feedback=3, neutral=2, difference=dict(numerator=1, denominator=13, value=1 / 13)))
        self.assertEqual(base['paired_contrast']['common_complete_triplets'], 16)
        self.assertEqual(base['paired_contrast']['pass_table']['both_fail'], 16)
        self.assertEqual(base['stages']['draft']['passed_complete'], 0)

    def test_no_raw_tasks_labels_or_errors_in_export(self):
        result = self.run_reduction()
        serialized = json.dumps(result)
        for forbidden in ('PRIVATE_RAW_SENTINEL', 'CPU_TEST_ONLY_NOT_REAL_WEIGHTS', '"messages"',
                          '"raw"', '"expression"', '"observed"', 'verification_inputs',
                          self.tasks[0]['id'], self.tasks[0]['spec'], solution(self.tasks[0])):
            self.assertNotIn(forbidden, serialized)
        self.assertTrue(result['exploratory'])
        self.assertFalse(result['retained_learning_claim'])
        self.assertEqual(result['model_calls'], 0)
        self.assertEqual(result['provider_calls'], 0)

    def test_no_input_mutation_or_native_loader_use(self):
        paths = list(self.root.rglob('*.json'))
        before = {str(path): collection.sha(path) for path in paths}
        with (patch.object(collection, 'collect', side_effect=AssertionError('native forbidden')),
              patch.object(collection, 'run_episodes', side_effect=AssertionError('replay forbidden')),
              patch.object(collection, 'write', side_effect=AssertionError('producer write forbidden'))):
            self.assertEqual(self.run_reduction()['status'], 'COMPLETE')
        self.assertEqual(before, {str(path): collection.sha(path) for path in paths})

    def test_no_premature_partial_gains_or_CALL_reads(self):
        (self.root / 'SUPERVISOR_COMPLETE.json').unlink()
        original = reducer.Snapshot.read

        def no_raw_read(snapshot, relative):
            self.assertNotIn('.CALL.json', relative)
            return original(snapshot, relative)

        with patch.object(reducer.Snapshot, 'read', no_raw_read):
            result = self.run_reduction()
        self.assert_withheld(result, 'NOT_READY')
        self.assertEqual(result['artifact_cell_counts']['CALL_PRESENT_UNREDUCED'], 96)

    def test_native_failure_preserves_96_cells_and_genuine_failure_without_gains(self):
        for cell in reducer.schedule(self.tasks)[4:]:
            directory = self.root / reducer.cell_directory(cell, self.tasks)
            for kind in ('CALL', 'INTENT', 'PUBLIC', 'VERIFY'):
                path = directory / (cell['stage'] + '.' + kind + '.json')
                if not (cell['planned_call'] == 5 and kind == 'INTENT'):
                    path.unlink()
        failure = self.path(model='BASE_NO_LORA', kind='FAILURE')
        write_json(failure, dict(error='PRIVATE_ERROR_SENTINEL', reserved_call=5, retry_allowed=False))
        write_json(self.root / 'NATIVE_TERMINAL.json', dict(status='FAILED_NO_RETRY', weights_verified_unchanged=False,
                                                         error='PRIVATE_ERROR_SENTINEL'))
        write_json(self.root / 'EPISODES_TERMINAL.json', dict(status='FAILED_NO_RETRY', reserved_calls=5, completed_calls=4))
        write_json(self.root / 'EXIT.json', dict(exit_code=1))
        write_json(self.root / 'SUPERVISOR_FAILED.json', dict(status='FAILED', error='PRIVATE_ERROR_SENTINEL'))
        (self.root / 'SUPERVISOR_COMPLETE.json').unlink()
        with patch.object(collection, 'verify', side_effect=AssertionError('no failed-run scoring')):
            result = self.run_reduction()
        self.assert_withheld(result, 'FAILED_NO_RETRY')
        self.assertEqual(result['artifact_cell_counts'],
                         dict(CALL_PRESENT_UNREDUCED=4, FAILURE_RECORDED=1, NOT_STARTED=91))
        self.assertNotIn('PRIVATE_ERROR_SENTINEL', json.dumps(result))

    def test_wrong_plan_pin_fails_before_task_access(self):
        original = reducer.Snapshot.read
        accessed = []

        def record(snapshot, relative):
            accessed.append(relative)
            return original(snapshot, relative)

        with patch.object(reducer.Snapshot, 'read', record):
            result = reducer.reduce(self.root, expected_plan_sha256='f' * 64)
        self.assert_withheld(result, 'INVALID_EVIDENCE')
        self.assertEqual(accessed, ['PLAN.json'])

    def test_source_or_task_pin_drift_fails_closed(self):
        with patch.object(collection, 'source_hashes', return_value={}):
            result = self.run_reduction()
        self.assert_withheld(result, 'INVALID_EVIDENCE')
        self.mutate(self.root / 'TASKS.json', lambda data: data['tasks'][0].update(spec='INJECTED_TASK'))
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')

    def test_forged_public_feedback_and_gold_in_prefix_rejected(self):
        intent_path = self.path(kind='INTENT')
        call_path = self.path()
        intent = collection.read(intent_path)
        intent['messages'][-1]['content'] += '\nExpected answer: PRIVATE_LABEL_SENTINEL'
        intent['messages_sha256'] = collection.digest(intent['messages'])
        call = collection.read(call_path)
        call.update(intent)
        call['response']['messages'] = copy.deepcopy(intent['messages'])
        write_json(intent_path, intent)
        write_json(call_path, call)
        result = self.run_reduction()
        self.assert_withheld(result, 'INVALID_EVIDENCE')
        self.assertIn('fork_prefix_or_actual_feedback_no_gold_binding', result['error_codes'])
        self.assertNotIn('PRIVATE_LABEL_SENTINEL', json.dumps(result))

    def test_neutral_receiving_feedback_or_sibling_prefix_rejected(self):
        intent_path = self.path(stage='neutral_review', kind='INTENT')
        call_path = self.path(stage='neutral_review')
        intent = collection.read(intent_path)
        intent['messages'] = collection.read(self.path(kind='INTENT'))['messages']
        intent['messages_sha256'] = collection.digest(intent['messages'])
        call = collection.read(call_path)
        call.update(intent)
        call['response']['messages'] = copy.deepcopy(intent['messages'])
        write_json(intent_path, intent)
        write_json(call_path, call)
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')

    def test_draft_CALL_hash_and_raw_digest_required(self):
        for field in ('shared_draft_call_sha256', 'shared_draft_text_sha256'):
            with self.subTest(field=field):
                intent_path, call_path = self.path(kind='INTENT'), self.path()
                original_intent, original_call = intent_path.read_bytes(), call_path.read_bytes()
                self.mutate(intent_path, lambda data: data.update({field: '0' * 64}))
                self.mutate(call_path, lambda data: data.update({field: '0' * 64}))
                result = self.run_reduction()
                self.assert_withheld(result, 'INVALID_EVIDENCE')
                self.assertIn('shared_draft_hash_binding', result['error_codes'])
                intent_path.write_bytes(original_intent)
                call_path.write_bytes(original_call)

    def test_actual_native_prefix_must_match_intent(self):
        self.mutate(self.path(), lambda data: data['response']['messages'][2].update(content='SIBLING_RAW_SENTINEL'))
        result = self.run_reduction()
        self.assert_withheld(result, 'INVALID_EVIDENCE')
        self.assertIn('actual_native_prefix_differs_from_intent', result['error_codes'])

    def test_public_receipt_and_verifier_tampering_rejected(self):
        path = self.path(kind='PUBLIC')
        original = path.read_bytes()
        self.mutate(path, lambda data: data.update(expected=3))
        result = self.run_reduction()
        self.assert_withheld(result, 'INVALID_EVIDENCE')
        self.assertIn('public_receipt_not_actual_execution', result['error_codes'])
        path.write_bytes(original)
        self.mutate(self.path(kind='VERIFY'), lambda data: data.update(success=False))
        result = self.run_reduction()
        self.assert_withheld(result, 'INVALID_EVIDENCE')
        self.assertIn('scorer_receipt_mismatch', result['error_codes'])

    def test_stored_recovery_labels_not_trusted(self):
        path = self.path().parent / 'COMPLETE.json'
        self.mutate(path, lambda data: data['forks']['interpreter_feedback'].update(task_semantic_correction=True))
        result = self.run_reduction()
        self.assert_withheld(result, 'INVALID_EVIDENCE')
        self.assertIn('episode_correction_receipt_mismatch', result['error_codes'])

    def test_native_flags_budget_duplicate_call_and_missing_cell(self):
        for field, value in (('terminal', 1), ('truncated', True), ('max_new_tokens', 2049), ('prompt_tokens', 32768)):
            with self.subTest(field=field):
                path = self.path()
                original = path.read_bytes()
                self.mutate(path, lambda data: data['response'].update({field: value}))
                self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')
                path.write_bytes(original)
        for path in (self.path(kind='INTENT'), self.path()):
            self.mutate(path, lambda data: data.update(reserved_call=1))
        result = self.run_reduction()
        self.assert_withheld(result, 'INVALID_EVIDENCE')
        self.assertIn('planned_call_identity_quota_or_budget', result['error_codes'])
        self.path().unlink()
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')

    def test_extra_replay_and_symlink_artifacts_rejected(self):
        extra = self.path().parent / 'old_replayed.CALL.json'
        extra.write_text('{}')
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')
        extra.unlink()
        original = self.path(kind='PUBLIC')
        original.unlink()
        original.symlink_to(self.path(kind='VERIFY'))
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')

    def test_weight_proof_supervisor_hash_and_snapshot_stability(self):
        path = self.root / 'NATIVE_TERMINAL.json'
        original = path.read_bytes()
        self.mutate(path, lambda data: data.update(weights_verified_unchanged=False))
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')
        path.write_bytes(original)
        with patch.object(reducer.Snapshot, 'stable', side_effect=reducer.EvidenceError('artifact_changed_during_reduction')):
            self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')
        self.mutate(self.root / 'SUPERVISOR_COMPLETE.json', lambda data: data.update(native_terminal_sha256='f' * 64))
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')

    def test_loaded_adapter_and_optimizer_must_match(self):
        path = self.root / 'LOADED.json'
        original = path.read_bytes()
        self.mutate(path, lambda data: data.update(optimizer_count=1))
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')
        path.write_bytes(original)
        self.mutate(path, lambda data: data['adapter'].update(state_sha256='f' * 64))
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')
        write_json(path, [])
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')

    def test_duplicate_JSON_keys_and_terminal_types_fail_closed(self):
        self.path(kind='VERIFY').write_text('{"success":false,"success":true}')
        self.assert_withheld(self.run_reduction(), 'INVALID_EVIDENCE')
        self.mutate(self.root / 'NATIVE_TERMINAL.json', lambda data: data.update(status=42))
        result = self.run_reduction()
        self.assert_withheld(result, 'INVALID_EVIDENCE')
        self.assertIn('terminal_status_type', result['error_codes'])

    def test_snapshot_repeated_read_cannot_silently_replace_pin(self):
        snapshot = reducer.Snapshot(self.root)
        snapshot.read('EXIT.json')
        write_json(self.root / 'EXIT.json', dict(exit_code=1))
        with self.assertRaisesRegex(reducer.EvidenceError, 'artifact_changed_during_reduction'):
            snapshot.read('EXIT.json')

    def test_failure_marker_reports_immediately_without_gains(self):
        (self.root / 'SUPERVISOR_COMPLETE.json').unlink()
        write_json(self.path(kind='FAILURE'), dict(error='PRIVATE_ERROR_SENTINEL'))
        result = self.run_reduction()
        self.assert_withheld(result, 'FAILED_NO_RETRY')
        self.assertEqual(result['artifact_cell_counts']['FAILURE_RECORDED'], 1)

    def test_terminal_summary_not_authoritative_over_rederived_calls(self):
        self.mutate(self.root / 'EPISODES_TERMINAL.json',
                    lambda data: data['results'][0]['forks']['interpreter_feedback'].update(after_success=False))
        result = self.run_reduction()
        self.assert_withheld(result, 'INVALID_EVIDENCE')
        self.assertIn('terminal_results_not_rederived', result['error_codes'])

    def test_zero_denominators_are_null_not_fake_zero(self):
        self.assertEqual(reducer.fraction(0, 0), dict(numerator=0, denominator=0, value=None))

    def test_CLI_exclusive_REDUCTION_output_only(self):
        output = Path(self.temporary.name) / 'REDUCTION_CPU_TEST.json'
        arguments = ['reduce', '--root', str(self.root), '--expected-plan-sha256', self.plan_hash,
                     '--output', str(output)]
        with patch('sys.argv', arguments), patch('builtins.print'):
            self.assertEqual(reducer.main(), 0)
            with self.assertRaises(FileExistsError):
                reducer.main()
        self.assertEqual(collection.read(output)['status'], 'COMPLETE')
        arguments[-1] = str(Path(self.temporary.name) / 'PLAN.json')
        with patch('sys.argv', arguments), self.assertRaises(reducer.EvidenceError):
            reducer.main()


if __name__ == '__main__':
    unittest.main()
