import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r119_public_feedback as arm
from organism_v6 import orch_persist_code as ledger


def inventory(hashes=()):
    return dict(schema='R119_SEALED_SPEC_HASHES_V1', normalization=arm.NORMALIZATION,
                attested_by='Main', coverage='ALL_SEALED_NAMESPACES',
                namespaces={'CPU_SYNTHETIC_SEALED_METADATA_NOT_PRODUCTION': list(hashes)})


def response(text, terminal=True, truncated=False):
    return dict(raw=text, terminal=terminal, truncated=truncated)


def encoded(expression):
    return json.dumps({'expression': expression}, separators=(',', ':'))


def solution(task):
    threshold, factor, offset = task['threshold'], task['factor'], task['offset']
    low, high = task['low'], task['high']
    return (
        f'sum(affine(ge(values,{threshold}),{factor},{offset}))',
        f'sum(unique(clip(affine(values,{factor},{offset}),{low},{high})))',
        f'sum(affine(ge(unique(values),{threshold}),{factor},{offset}))',
        f'len(ge(affine(clip(values,{low},{high}),{factor},{offset}),{threshold}))',
    )[task['kind']]


def independent_python(task, values):
    factor, offset = task['factor'], task['offset']
    if task['kind'] == 0:
        return sum(factor * value + offset for value in values if value >= task['threshold'])
    if task['kind'] == 1:
        return sum(set(max(task['low'], min(task['high'], factor * value + offset)) for value in values))
    if task['kind'] == 2:
        return sum(factor * value + offset for value in set(values) if value >= task['threshold'])
    return sum(factor * max(task['low'], min(task['high'], value)) + offset >= task['threshold'] for value in values)


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.document = arm.build_tasks(119, inventory())

    def test_fresh_normalized_disjoint_roles_and_original64(self):
        train = {task['normalized_spec_sha256'] for task in self.document['tasks'] if task['split'] == 'TRAIN'}
        dev = {task['normalized_spec_sha256'] for task in self.document['tasks'] if task['split'] == 'DEV'}
        confirm = {task['normalized_spec_sha256'] for task in self.document['confirm_reservations']}
        old = {arm.spec_hash(task) for task in ledger.build_tasks(count=64)}
        self.assertEqual((len(train), len(dev), len(confirm)), (16, 8, 8))
        self.assertEqual(len(train | dev | confirm), 32)
        self.assertFalse((train | dev | confirm) & old)
        self.assertEqual(self.document, arm.build_tasks(119, inventory()))

    def test_sealed_hash_collision_excluded_without_sealed_content(self):
        forbidden = self.document['tasks'][0]['normalized_spec_sha256']
        document = arm.build_tasks(119, inventory([forbidden]))
        self.assertNotIn(forbidden, [task['normalized_spec_sha256'] for task in document['tasks'] + document['confirm_reservations']])

    def test_no_sealed_coverage_claim_without_inventory(self):
        for value in ({}, dict(inventory(), coverage='SOME'), dict(inventory(), namespaces={}),
                      dict(inventory(), attested_by='self')):
            with self.assertRaises((ValueError, KeyError)):
                arm.build_tasks(119, value)

    def test_confirm_only_ids_hashes_no_prompts_inputs_expected(self):
        for reserved in self.document['confirm_reservations']:
            self.assertEqual(set(reserved), {'id', 'normalized_spec_sha256'})
            self.assertIn('CONFIRM', reserved['id'])
        self.assertNotIn('CONFIRM', {task['split'] for task in self.document['tasks']})

    def test_normalization_ignores_irrelevant_parameters_and_labels(self):
        task = next(task for task in self.document['tasks'] if task['kind'] == 1)
        altered = dict(task, threshold=999, id='OTHER', split='DEV', spec='renamed')
        self.assertEqual(arm.spec_hash(task), arm.spec_hash(altered))

    def test_normalization_collapses_equivalent_clamped_count(self):
        first = dict(kind=3, threshold=27, factor=2, offset=1, low=-50, high=50)
        second = dict(first, factor=3, threshold=40, low=-80, high=90)
        self.assertEqual(arm.spec_hash(first), arm.spec_hash(second))
        for value in range(-100, 101):
            self.assertEqual(arm.expected(first, [value]), arm.expected(second, [value]))

    def test_count_normalization_positive_negative_and_degenerate(self):
        generator = random.Random(92)
        for trial in range(100):
            task = dict(kind=3, factor=generator.choice([-7, -3, 2, 5]), threshold=generator.randint(-100, 100),
                        offset=generator.randint(-10, 10), low=-9, high=13)
            normalized = arm.normalized_spec(task)['function']
            for value in range(-20, 21):
                predicted = {'count_all': lambda: 1, 'count_none': lambda: 0,
                             'count_ge': lambda: int(value >= normalized[1]),
                             'count_le': lambda: int(value <= normalized[1])}[normalized[0]]()
                self.assertEqual(predicted, independent_python(task, [value]))

    def test_expected_and_interpreter_against_independent_python(self):
        for task in self.document['tasks']:
            program = solution(task)
            for values in task['verification_inputs']:
                wanted = independent_python(task, values)
                self.assertEqual(arm.expected(task, values), wanted)
                self.assertEqual(ledger.evaluate(program, values), wanted)
            self.assertTrue(arm.verify(task, encoded(program))['success'])


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.task = arm.build_tasks(119, inventory())['tasks'][0]

    def test_exact_contract_roundtrip(self):
        text = encoded(solution(self.task))
        self.assertEqual(arm.parse_action(text), solution(self.task))
        self.assertIn('observed', arm.execute_public(self.task, text))
        self.assertTrue(arm.execute_public(self.task, text)['interpreter_started'])

    def test_wrong_key_has_specific_diagnostic(self):
        receipt = arm.execute_public(self.task, '{"expr":"sum(values)"}')
        self.assertIn('last line must be exactly expression or record JSON', receipt['error'])
        self.assertFalse(receipt['interpreter_started'])

    def test_invalid_final_action_not_silently_repaired(self):
        for text in ('{\n"expression":"sum(values)"\n}', '```json\n{"expression":"sum(values)"}\n```',
                     '{"expression":"sum(values)","record":"ok"}',
                     '{"expression":42}', '{"record":"not an expression action"}',
                     'Useful reasoning.\n{"expr":"sum(values)"}'):
            with self.assertRaises(ValueError):
                arm.parse_action(text)

    def test_multiline_reasoning_preserved_with_original_final_action_parser(self):
        reasoning = 'I should check the input identifier.\nThe public error concerns my prior symbol; I can revise it.'
        text = reasoning + '\n' + encoded(solution(self.task))
        action, retained = ledger.parse_action(text)
        self.assertEqual(retained, reasoning)
        self.assertEqual(arm.parse_action(text), action['expression'])
        self.assertTrue(arm.verify(self.task, text)['success'])
        self.assertIn('observed', arm.execute_public(self.task, text))
        self.assertNotIn('No prose', arm.CONTRACT)
        self.assertIn('Reasoning before the final action is permitted', arm.CONTRACT)

    def test_original_duplicate_key_behavior_unchanged(self):
        text = 'Reasoning is allowed.\n{"expression":"sum(xs)","expression":"sum(values)"}'
        self.assertEqual(arm.parse_action(text), ledger.parse_action(text)[0]['expression'])
        self.assertEqual(arm.parse_action(text), 'sum(values)')

    def test_parser_delegates_to_original_without_response_rewriting(self):
        text = 'Reconsider the cause.\n' + encoded('sum(values)')
        with patch.object(ledger, 'parse_action', wraps=ledger.parse_action) as parser:
            arm.parse_action(text)
            parser.assert_called_once_with(text)

    def test_public_whitelist_no_gold_verdict_or_verification_inputs(self):
        for text in ('{"expr":"sum(values)"}', encoded('sum(xs)'), encoded(solution(self.task))):
            receipt = arm.execute_public(self.task, text)
            self.assertLessEqual(set(receipt), arm.PUBLIC_KEYS)
            self.assertFalse(receipt['hidden_tests_exposed'])
            self.assertFalse({'expected', 'success', 'correct', 'passed', 'verification_inputs'} & set(receipt))
            self.assertEqual(receipt['input'], self.task['public_input'])

    def test_feedback_forgery_and_gold_injection_rejected(self):
        text = encoded(solution(self.task))
        public = arm.execute_public(self.task, text)
        for forged in (dict(public, observed=public['observed'] + 1), dict(public, success=True), dict(public, expected=1)):
            with self.assertRaises(ValueError):
                arm.messages(self.task, arm.BRANCHES[0], [dict(raw=text, public=forged)])

    def test_no_feedback_matches_opportunities_without_diagnostics(self):
        raw = encoded('sum(xs)')
        turn = dict(raw=raw, public=arm.execute_public(self.task, raw))
        child = arm.messages(self.task, 'CHILD_PUBLIC_FEEDBACK', [turn, turn])
        control = arm.messages(self.task, 'CHILD_NO_FEEDBACK', [turn, turn])
        self.assertEqual(len(child), len(control))
        self.assertEqual(child[:2], control[:2])
        self.assertNotIn('unknown identifier', control[-1]['content'])
        self.assertIn('unknown identifier', child[-1]['content'])
        baseline = arm.messages(self.task, 'BASE_NO_FEEDBACK', [turn, turn])
        self.assertNotIn('unknown identifier', baseline[-1]['content'])
        self.assertEqual(baseline, control)

    def test_child_and_BASE_identical_messages_including_evidence(self):
        raw = encoded('sum(xs)')
        history = [dict(raw=raw, public=arm.execute_public(self.task, raw))]
        self.assertEqual(arm.messages(self.task, 'CHILD_PUBLIC_FEEDBACK', history),
                         arm.messages(self.task, 'BASE_PUBLIC_FEEDBACK', history))

    def test_prompt_no_task_solution_or_other_task_or_private_input(self):
        prefix = arm.messages(self.task, arm.BRANCHES[0])
        self.assertEqual(prefix[0]['content'], arm.CONTRACT)
        self.assertIn(self.task['spec'], prefix[1]['content'])
        self.assertNotIn(solution(self.task), str(prefix))
        self.assertNotIn('verification_inputs', str(prefix))
        self.assertNotIn('CONFIRM', str(prefix))
        self.assertIn('{"expression":"..."}', prefix[0]['content'])

    def test_third_revision_and_CONFIRM_prompt_rejected(self):
        with self.assertRaises(ValueError):
            arm.messages(self.task, arm.BRANCHES[0], [{}, {}, {}])
        with self.assertRaises(ValueError):
            arm.messages(dict(self.task, split='CONFIRM'), arm.BRANCHES[0])


class CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.task = arm.build_tasks(119, inventory())['tasks'][0]
        self.good = response(encoded(solution(self.task)))

    def test_actual_repair_is_potential_only_never_admitted_or_fit(self):
        bad = response(encoded(solution(self.task).replace('values', 'xs')))
        result = arm.correction(self.task, 'CHILD_PUBLIC_FEEDBACK', bad, self.good)
        self.assertTrue(result['verified_failed_to_passed'])
        self.assertIn('INPUT_IDENTIFIER_REPAIRED', result['semantic_tags'])
        self.assertTrue(result['potential_child_only_row'])
        self.assertFalse(result['functional_admission'])
        self.assertEqual(result['fit_updates'], 0)

    def test_partial_identifier_to_arity_is_not_pass(self):
        before, after = response(encoded('sum(xs)')), response(encoded('affine(values)'))
        result = arm.correction(self.task, 'CHILD_PUBLIC_FEEDBACK', before, after)
        self.assertIn('INPUT_IDENTIFIER_REPAIRED', result['semantic_tags'])
        self.assertFalse(result['after_success'])
        self.assertFalse(result['verified_failed_to_passed'])

    def test_unchanged_success_and_text_only_changes_not_corrections(self):
        for before, after in ((self.good, self.good), (response('{"expr":"sum(xs)"}'), response('{"expr": "sum(xs)"}'))):
            result = arm.correction(self.task, 'CHILD_PUBLIC_FEEDBACK', before, after)
            self.assertFalse(result['potential_child_only_row'])
            self.assertFalse(result['verified_failed_to_passed'])

    def test_failed_parse_not_unknown_identifier_repair(self):
        result = arm.correction(self.task, 'CHILD_PUBLIC_FEEDBACK', response(encoded('sum(xs)')), response(encoded('sum(xs')))
        self.assertNotIn('INPUT_IDENTIFIER_REPAIRED', result['semantic_tags'])
        self.assertFalse(result['potential_child_only_row'])

    def test_constant_substitution_is_not_general_input_repair(self):
        result = arm.correction(self.task, 'CHILD_PUBLIC_FEEDBACK', response(encoded('sum(xs)')), response(encoded('42')))
        self.assertNotIn('INPUT_IDENTIFIER_REPAIRED', result['semantic_tags'])
        self.assertFalse(result['potential_child_only_row'])

    def test_DEV_BASE_and_cap_hits_never_candidates(self):
        before = response(encoded('sum(xs)'))
        for task, branch, after in ((dict(self.task, split='DEV'), 'CHILD_PUBLIC_FEEDBACK', self.good),
                                    (self.task, 'BASE_PUBLIC_FEEDBACK', self.good),
                                    (self.task, 'BASE_NO_FEEDBACK', self.good),
                                    (self.task, 'CHILD_PUBLIC_FEEDBACK', dict(self.good, terminal=False, truncated=True))):
            result = arm.correction(task, branch, before, after)
            self.assertFalse(result['potential_child_only_row'])


class RuntimeTests(unittest.TestCase):
    def plan(self):
        return dict(source_label=arm.SOURCE, root='/localhome/local-rohing/R119_CPU_FIXTURE',
                    physical=7, uuid=arm.pilot.UUID, counts=arm.COUNTS, revisions=2, max_responses=240,
                    response_caps=arm.RESPONSE_CAPS,
                    max_new_tokens=2048, context_limit=16384, native_end_unix=arm.NATIVE_END,
                    external_end_unix=arm.EXTERNAL_END, lease_end_unix=arm.EXTERNAL_END + 21601,
                    lease_margin_seconds=21600, decoder=arm.DECODER, fit_allowed=False, parents=0)

    def test_exact_new_Main_allocation_deadline_and_lease_margin(self):
        plan = self.plan()
        allocation = dict(plan, approved_by='Main', status='APPROVED')
        arm.validate_plan(plan, allocation, arm.NATIVE_END - 1)
        for altered in (dict(plan, max_responses=217), dict(plan, max_new_tokens=4096),
                        dict(plan, native_end_unix=arm.NATIVE_END + 1), dict(plan, fit_allowed=True),
                        dict(plan, root='/tmp/R119'), dict(plan, physical=6)):
            with self.assertRaises(ValueError):
                arm.validate_plan(altered, allocation, arm.NATIVE_END - 1)
        with self.assertRaises(ValueError):
            arm.validate_plan(plan, allocation, arm.NATIVE_END)
        short = dict(plan, lease_end_unix=arm.EXTERNAL_END + 1)
        with self.assertRaises(ValueError):
            arm.validate_plan(short, dict(short, approved_by='Main', status='APPROVED'), arm.NATIVE_END - 1)

    def test_real_CPU_episode_writes_240_calls_and_no_CONFIRM_or_DEV_candidates(self):
        tasks = arm.build_tasks(119, inventory())
        def generate(prefix, branch):
            return response(encoded('sum(xs)' if len(prefix) == 2 else 'sum(values)'))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = arm.run_episodes(root, self.plan(), tasks, generate, clock=lambda: arm.NATIVE_END - 1)
            self.assertEqual(result['responses_reserved'], 240)
            self.assertEqual(result['completed_episodes'], 96)
            self.assertEqual(result['split_responses_reserved'], {'TRAIN': 160, 'DEV': 80})
            self.assertEqual(result['unique_draft_calls'], 48)
            self.assertEqual(len(list(root.rglob('*.CALL.json'))), 240)
            self.assertEqual(len(list(root.rglob('*.INTENT.json'))), 240)
            self.assertEqual(result['confirm_calls'], 0)
            for episode in result['results']:
                if episode['split'] == 'DEV' or episode['branch'].startswith('BASE_'):
                    self.assertFalse(any(item['potential_child_only_row'] for item in episode['revisions']))
            with self.assertRaises(FileExistsError):
                arm.run_episodes(root, self.plan(), tasks, generate, clock=lambda: arm.NATIVE_END - 1)

    def test_generation_failure_keeps_charged_intent_no_replay(self):
        tasks = arm.build_tasks(119, inventory())
        def fail(prefix, branch):
            raise RuntimeError('synthetic_engine_failure')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(RuntimeError):
                arm.run_episodes(root, self.plan(), tasks, fail, clock=lambda: arm.NATIVE_END - 1)
            self.assertEqual(len(list(root.rglob('*.INTENT.json'))), 1)
            self.assertFalse(list(root.rglob('*.CALL.json')))
            with self.assertRaises(FileExistsError):
                arm.run_episodes(root, self.plan(), tasks, fail, clock=lambda: arm.NATIVE_END - 1)

    def test_shared_draft_identity_and_independent_latest_expression_forks(self):
        tasks = arm.build_tasks(119, inventory())
        tasks['tasks'] = tasks['tasks'][:1]
        draft_calls = []
        def generate(prefix, model):
            if len(prefix) == 2:
                draft_calls.append(model)
                return response(encoded('sum(xs)' if model == 'CHILD' else 'sum(train)'))
            feedback = 'No execution feedback' not in prefix[-1]['content']
            if len(prefix) == 6:
                latest = prefix[-2]['content']
                self.assertEqual(latest, encoded('affine(values)' if feedback else 'sum(values)'))
                if feedback:
                    self.assertIn('helper arity mismatch', prefix[-1]['content'])
                    self.assertNotIn('unknown identifier', prefix[-1]['content'])
                else:
                    self.assertNotIn('observed', prefix[-1]['content'])
                return response(encoded('sum(values)'))
            return response(encoded('affine(values)' if feedback else 'sum(values)'))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = arm.run_episodes(root, self.plan(), tasks, generate, clock=lambda: arm.NATIVE_END - 1)
            self.assertEqual(draft_calls, ['CHILD', 'BASE'])
            self.assertEqual(result['responses_reserved'], 10)
            for model in arm.MODELS:
                folder = root / 'episodes' / tasks['tasks'][0]['id'] / model
                first, second = [arm.read(folder / (model + suffix) / 'SHARED_DRAFT.json')
                                 for suffix in ('_PUBLIC_FEEDBACK', '_NO_FEEDBACK')]
                self.assertEqual(first, second)
                self.assertEqual(first['sha256'], arm.sha(folder / 'draft.CALL.json'))
                self.assertTrue(first['reference_only_not_new_response'])
                prefixes = [arm.read(folder / (model + suffix) / 'revision1.CALL.json')['messages']
                            for suffix in ('_PUBLIC_FEEDBACK', '_NO_FEEDBACK')]
                self.assertEqual(prefixes[0][:3], prefixes[1][:3])

    def test_unique_cap_count_does_not_double_count_shared_draft(self):
        tasks = arm.build_tasks(119, inventory())
        tasks['tasks'] = tasks['tasks'][:1]
        def generate(prefix, model):
            return response(encoded('sum(values)'), terminal=len(prefix) != 2, truncated=len(prefix) == 2)
        with tempfile.TemporaryDirectory() as directory:
            result = arm.run_episodes(Path(directory), self.plan(), tasks, generate, clock=lambda: arm.NATIVE_END - 1)
            self.assertEqual(result['unique_cap_hits'], 2)
            self.assertEqual(result['unique_incomplete_responses'], 2)
            self.assertEqual(sum(episode['cap_hits_including_shared_draft'] for episode in result['results']), 4)

    def test_source_and_seed_fail_closed(self):
        with self.assertRaises(ValueError):
            arm.verify_sources({})
        seed = dict(adapter=dict(state_sha256=arm.SEED_STATE, base_sha256=arm.BASE_SHA),
                    optimizer_sha256=arm.OPTIMIZER_SHA, checkpoint='/node/checkpoints/000015332')
        with patch.object(arm, 'sha', return_value=arm.OPTIMIZER_SHA):
            arm.validate_seed(seed, '/node/optimizer')
            for altered in (dict(seed, checkpoint='/node/checkpoints/000008932'),
                            dict(seed, adapter=dict(seed['adapter'], base_sha256='0' * 64)),
                            dict(seed, optimizer_sha256='0' * 64)):
                with self.assertRaises(ValueError):
                    arm.validate_seed(altered, '/node/optimizer')

    def test_past_deadline_makes_no_model_call(self):
        tasks = arm.build_tasks(119, inventory())
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                arm.run_episodes(Path(directory), self.plan(), tasks,
                                 lambda prefix, branch: self.fail('unexpected_model_call'), clock=lambda: arm.NATIVE_END)


if __name__ == '__main__':
    unittest.main()
