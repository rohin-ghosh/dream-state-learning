import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r133_code_feedback_collection as frozen
from gpu import orch_r141_code_interface as arm
from tests.test_orch_r133_code_feedback_collection import inventory, response, solution


SEED = 'e1' * 32


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.tasks = arm.build_tasks(SEED, inventory())

    def test_exact_frozen_parser_scorer_model_and_native_code(self):
        for name in ('parse_expression', 'evaluate', 'verify', 'execute_public', 'readonly_model'):
            self.assertIs(getattr(arm, name), getattr(frozen, name))
        for bound, original in ((arm.collect, frozen.collect), (arm._run_episodes, frozen.run_episodes),
                                (arm._verified, frozen.verified), (arm._prepare, frozen.prepare)):
            self.assertIs(bound.__code__, original.__code__)
        self.assertEqual((arm.MODELS, arm.STAGES, arm.CALL_CAP, arm.MAX_NEW_TOKENS, arm.CONTEXT_LIMIT),
                         (frozen.MODELS, frozen.STAGES, 96, 2048, 32768))
        self.assertIs(arm.collect.__globals__['readonly_model'], frozen.readonly_model)
        self.assertIs(arm.collect.__globals__['validate_authorization'], frozen.validate_authorization)
        self.assertIs(arm.collect.__globals__['run_episodes'], arm.run_episodes)
        self.assertIs(frozen.run_episodes.__globals__['messages'], frozen.messages)
        self.assertEqual(frozen.SCHEMA, 'R133_PUBLIC_TRAIN_CODE_FEEDBACK_V1')

    def test_format_only_example_and_identical_prompt_delta_every_stage(self):
        self.assertEqual(json.loads(arm.FORMAT_EXAMPLE), {'expression': 'EXPRESSION_TEXT'})
        with self.assertRaises(ValueError):
            frozen.ledger.validate_expression(json.loads(arm.FORMAT_EXAMPLE)['expression'])
        for helper in frozen.ledger.HELPERS:
            self.assertNotIn(helper + '(', arm.FORMAT_CONTRACT)
        self.assertFalse(any(character.isdigit() for character in arm.FORMAT_CONTRACT))
        for task in self.tasks:
            for stage in arm.STAGES:
                draft = None if stage == 'draft' else '{"expression":sum(values)}'
                feedback = frozen.execute_public(task, draft) if stage == 'interpreter_feedback' else None
                original = frozen.messages(task, stage, draft, feedback)
                expected = copy.deepcopy(original)
                expected[0]['content'] += arm.FORMAT_CONTRACT
                self.assertEqual(arm.messages(task, stage, draft, feedback), expected)
                self.assertEqual(frozen.messages(task, stage, draft, feedback), original)

    def test_real_error_only_feedback_neutral_no_new_evidence(self):
        task = self.tasks[0]
        draft = '{"expression":sum(values)}'
        receipt = frozen.execute_public(task, draft)
        actual = arm.messages(task, 'interpreter_feedback', draft, receipt)
        neutral = arm.messages(task, 'neutral_review', draft)
        self.assertEqual(actual[:3], neutral[:3])
        self.assertIn(json.dumps(receipt, sort_keys=True), actual[-1]['content'])
        self.assertIn('No execution feedback', neutral[-1]['content'])
        self.assertNotIn(receipt['error'], neutral[-1]['content'])
        self.assertNotIn('verification_inputs', json.dumps(actual))
        with self.assertRaises(ValueError):
            arm.messages(task, 'interpreter_feedback', draft, dict(receipt, observed=1))
        with self.assertRaises(ValueError):
            arm.messages(task, 'neutral_review', draft, receipt)
        with self.assertRaises(ValueError):
            arm.messages(dict(task, split='TEST'))

    def test_no_preview_legacy_loader_or_used_seed(self):
        with self.assertRaisesRegex(ValueError, 'Main_hash_only'):
            arm.build_tasks(SEED)
        with patch.object(frozen.ledger, 'build_tasks', side_effect=AssertionError('legacy access')):
            self.assertEqual(self.tasks, frozen.build_tasks(SEED, inventory()))
        with self.assertRaisesRegex(ValueError, 'seed_already_used'):
            arm.build_tasks(SEED, inventory(used_seed_sha256=[arm.digest(SEED)]))

    def test_all_planned_hash_exclusions_and_bounded_attestation(self):
        specs = [task['normalized_spec_sha256'] for task in self.tasks]
        identities = [arm.digest(task['id']) for task in self.tasks]
        for document in (inventory(spec_sha256=specs), inventory(task_id_sha256=identities)):
            tasks = arm.build_tasks(SEED, document)
            self.assertFalse(set(specs) & {task['normalized_spec_sha256'] for task in tasks})
            self.assertFalse(set(identities) & {arm.digest(task['id']) for task in tasks})
        for document in (inventory(attested_by='agent'), dict(inventory(), tasks=[]),
                         inventory(spec_sha256=[]), inventory(coverage='GLOBAL')):
            with self.assertRaises(ValueError):
                arm.build_tasks(SEED, document)

    def test_format_validity_distinct_from_safe_semantics(self):
        task = self.tasks[0]
        cases = [('{"expression":sum(values)}', False, False, None),
                 ('{"expression":1}', False, False, None),
                 ('{"expression":"0","expression":"1"}', False, False, None),
                 ('{"expression":"__import__(\"os\")"}', False, False, None),
                 (response('__import__("os")')['raw'], True, False, None),
                 (response('values')['raw'], True, True, False),
                 (response('0')['raw'], True, True, False),
                 (response(solution(task))['raw'], True, True, True)]
        for raw, formatted, safe, semantic in cases:
            with self.subTest(raw=raw):
                metrics = arm.response_metrics(task, response('0', raw=raw))
                self.assertEqual((metrics['format_valid'], metrics['safe_expression'], metrics['semantic_correct']),
                                 (formatted, safe, semantic))
                self.assertEqual(metrics['strict_success'], frozen.verify(task, raw))
        reasoning = 'Reasoning permitted.\n' + response(solution(task))['raw']
        self.assertTrue(arm.response_metrics(task, response('0', raw=reasoning))['format_valid'])

    def test_changes_do_not_invent_ast_for_unquoted_candidate(self):
        task = self.tasks[0]
        malformed = response('0', raw='{"expression":sum(values)}')
        with patch.object(frozen, 'diagnostic_expression', side_effect=AssertionError('no extraction')):
            result = arm.correction(task, malformed, response(solution(task)))
        self.assertTrue(result['format_recovered'])
        self.assertTrue(result['failed_to_passed'])
        self.assertIsNone(result['expression_text_changed'])
        self.assertIsNone(result['expression_ast_changed'])
        self.assertFalse(result['semantic_correction'])
        same_ast = arm.correction(task, response('sum(values)'), response('sum( values )'))
        self.assertTrue(same_ast['raw_changed'])
        self.assertTrue(same_ast['expression_text_changed'])
        self.assertFalse(same_ast['expression_ast_changed'])
        semantic = arm.correction(task, response('0'), response(solution(task)))
        self.assertTrue(semantic['expression_ast_changed'])
        self.assertTrue(semantic['semantic_correction'])
        unchanged = arm.correction(task, response('0'), response('0'))
        self.assertFalse(unchanged['raw_changed'])

    def test_incomplete_outputs_never_eligible_success_or_recovery(self):
        task = self.tasks[0]
        for updates in (dict(terminal=False), dict(truncated=True)):
            result = arm.correction(task, response('0'), response(solution(task), **updates))
            self.assertTrue(result['after']['strict_success'])
            for key in ('complete_pair', 'failed_to_passed', 'semantic_correction', 'format_recovered'):
                self.assertFalse(result[key])
            self.assertFalse(result['after']['eligible_success'])


class PreparationAndEpisodeTests(unittest.TestCase):
    def test_R136_frozen_source_identity_is_required_not_merely_new_pins(self):
        actual = arm.source_hashes()
        self.assertEqual({name: actual[name] for name in arm.FROZEN_SOURCE_SHA256}, arm.FROZEN_SOURCE_SHA256)
        with tempfile.TemporaryDirectory() as temporary, patch.object(arm, 'sha', return_value='0' * 64):
            root = Path(temporary) / 'not_created'
            with self.assertRaisesRegex(ValueError, 'exact_R136_frozen'):
                arm.prepare(root, SEED, inventory())
            self.assertFalse(root.exists())

    def test_new_directory_pins_and_mutation_rejection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'fresh'
            with self.assertRaises(ValueError):
                arm.prepare(root, SEED)
            self.assertFalse(root.exists())
            plan = arm.prepare(root, SEED, inventory())
            observed, tasks = arm.verified(root)
            self.assertEqual(plan, observed)
            self.assertEqual(plan['schema'], arm.SCHEMA)
            self.assertEqual(plan['source_sha256'], arm.source_hashes())
            with self.assertRaises(ValueError):
                arm.prepare(root, SEED, inventory())
            with patch.object(arm, 'source_hashes', return_value={}):
                with patch.dict(arm._namespace, source_hashes=arm.source_hashes):
                    with self.assertRaisesRegex(ValueError, 'prepared_bytes_changed'):
                        arm.verified(root)
            changed = copy.deepcopy(tasks)
            changed[0]['public_input'] = [999]
            with self.assertRaisesRegex(ValueError, 'only_exact_fresh'):
                arm.run_episodes(root, changed, Mock())
            self.assertFalse((root / 'EPISODES_START.json').exists())
            document = arm.read(root / 'TASKS.json')
            document['schema'] = frozen.SCHEMA
            (root / 'TASKS.json').write_text(json.dumps(document))
            plan['tasks_sha256'] = arm.sha(root / 'TASKS.json')
            (root / 'PLAN.json').write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError, 'R141_tasks_envelope'):
                arm.verified(root)

    def test_old_plan_rejected_without_reading_old_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'synthetic_old_plan'
            frozen.prepare(root, SEED, inventory())
            generate = Mock()
            with self.assertRaisesRegex(ValueError, 'prepared_bytes_changed'):
                arm.run_episodes(root, frozen.build_tasks(SEED, inventory()), generate)
            generate.assert_not_called()

    def test_96_fake_calls_symmetric_contract_shared_draft_no_training(self):
        calls = []

        def generate(prefix, state):
            calls.append((prefix, state))
            return response('0')

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'fake_only'
            arm.prepare(root, SEED, inventory())
            _, tasks = arm.verified(root)
            result = arm.run_episodes(root, tasks, generate)
            self.assertEqual(result['reserved_calls'], 96)
            self.assertEqual(result['completed_calls'], 96)
            self.assertEqual(result['rows_admitted'], 0)
            self.assertEqual(result['fit_updates'], 0)
            self.assertEqual(result['external_calls'], 0)
            self.assertEqual(len(result['results']), 32)
            for task in tasks:
                model_prefixes = {}
                for model in arm.MODELS:
                    directory = root / 'episodes' / task['id'] / model
                    draft = arm.read(directory / 'draft.CALL.json')
                    model_prefixes[model] = []
                    for stage in arm.STAGES:
                        cell = arm.read(directory / (stage + '.CALL.json'))
                        model_prefixes[model].append(cell['messages'])
                        self.assertEqual(cell['messages'][0]['content'], frozen.public.CONTRACT + arm.FORMAT_CONTRACT)
                        self.assertEqual(arm.read(directory / (stage + '.VERIFY.json')),
                                         dict(success=frozen.verify(task, cell['response']['raw'])))
                        if stage != 'draft':
                            self.assertEqual(cell['messages'][2]['content'], draft['response']['raw'])
                            self.assertEqual(cell['shared_draft_call_sha256'], arm.sha(directory / 'draft.CALL.json'))
                    complete = arm.read(directory / 'COMPLETE.json')
                    for metrics in complete['forks'].values():
                        self.assertFalse(metrics['raw_changed'])
                        self.assertFalse(metrics['four_way_benchmark'])
                        self.assertTrue(metrics['before']['format_valid'])
                self.assertEqual(model_prefixes[arm.MODELS[0]], model_prefixes[arm.MODELS[1]])
            with self.assertRaises(FileExistsError):
                arm.run_episodes(root, tasks, generate)
        self.assertEqual(len(calls), 96)
        self.assertEqual([state for _, state in calls].count('BASE_NO_LORA'), 48)
        self.assertEqual([state for _, state in calls[:12]], [arm.MODELS[0]] * 3 + [arm.MODELS[1]] * 6 + [arm.MODELS[0]] * 3)

    def test_failed_generation_is_preserved_and_never_retried(self):
        generate = Mock(side_effect=[response('0'), RuntimeError('fake failure')])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'failure'
            arm.prepare(root, SEED, inventory())
            _, tasks = arm.verified(root)
            with self.assertRaisesRegex(RuntimeError, 'fake failure'):
                arm.run_episodes(root, tasks, generate)
            terminal = arm.read(root / 'EPISODES_TERMINAL.json')
            self.assertEqual((terminal['reserved_calls'], terminal['completed_calls']), (2, 1))
            self.assertEqual(terminal['status'], 'FAILED_NO_RETRY')
            self.assertEqual(len(list(root.rglob('*.FAILURE.json'))), 1)
            with self.assertRaises(FileExistsError):
                arm.run_episodes(root, tasks, generate)
            self.assertEqual(generate.call_count, 2)


if __name__ == '__main__':
    unittest.main()
