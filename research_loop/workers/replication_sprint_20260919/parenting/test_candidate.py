import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
from candidate_review import review_draft


SOURCES = json.loads((HERE / 'SOURCES.json').read_bytes())
EXAMPLES = json.loads((HERE / 'OFFLINE_TURN_EXAMPLES.json').read_bytes())['examples']
BRIEF = (HERE / 'MIXED_CURRICULUM_PARENT_BRIEF.md').read_text()


def source_bytes(source_id):
    binding = SOURCES['local_sources'][source_id]
    content = (REPO / binding['path']).read_bytes()
    if hashlib.sha256(content).hexdigest() != binding['sha256']:
        raise ValueError('inspected_source_changed:' + source_id)
    return content


def observed_output(example):
    document = json.loads(source_bytes(example['source_id']))
    if example['source_id'] == 'c2_delivery':
        actual = document['first_committed_ACT']
        return dict(record_index=actual['record']['index'], record_sha256=actual['record']['sha256'],
            text=actual['text_excerpt'], stage=actual['stage'])
    if example['source_id'] == 'c2_loop':
        return next(event for event in document['events']
            if event['actor'] == 'child' and event['record_index'] == example['record_index'])
    if example['source_id'] == 'p7_reply':
        return document['reply']
    raise ValueError('unknown_fixture_source')


def isolated_function(source_id, name, namespace, *, hook=False):
    tree = ast.parse(source_bytes(source_id))
    if hook:
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        branch = next(node for node in main.body if isinstance(node, ast.If)
            and isinstance(node.test, ast.Attribute) and node.test.attr == 'policy_addendum')
        function = next(node for node in branch.body if isinstance(node, ast.FunctionDef) and node.name == name)
    else:
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    exec(compile(module, 'isolated_source_bound_' + source_id, 'exec'), namespace)
    return namespace[name]


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


class SourceBindingTests(unittest.TestCase):
    def test_inspected_local_sources_still_match(self):
        for source_id in SOURCES['local_sources']:
            with self.subTest(source=source_id):
                source_bytes(source_id)

    def test_standing_documents_bound_to_exact_git_commit(self):
        for binding in SOURCES['standing_documents']:
            with self.subTest(source=binding['path']):
                content = subprocess.check_output(['git', 'show', binding['git_commit'] + ':' + binding['path']],
                    cwd=REPO, timeout=10)
                self.assertEqual(hashlib.sha256(content).hexdigest(), binding['sha256'])

    def test_examples_are_real_observations_but_unsent_drafts(self):
        envelope = json.loads((HERE / 'OFFLINE_TURN_EXAMPLES.json').read_bytes())
        self.assertEqual(envelope['publications'], 0)
        self.assertEqual(envelope['provider_calls'], 0)
        self.assertEqual(envelope['behavioral_outcomes'], [])
        for example in EXAMPLES:
            with self.subTest(example=example['name']):
                latest = observed_output(example)
                self.assertEqual(latest['record_index'], example['record_index'])
                self.assertEqual(latest['record_sha256'], example['record_sha256'])
                self.assertEqual(review_draft(example['draft'], latest), [])


class ExistingHookTests(unittest.TestCase):
    def setUp(self):
        self.original = Mock(return_value=('existing instruction', 'original payload'))
        self.bank = Mock(return_value=dict(questions=[dict(id='synthetic_contract_only', text='A released question?')]))
        self.hook = isolated_function('c2_hook', 'prompt', dict(original_prompt=self.original,
            addendum=BRIEF, json=json, question_bank=self.bank), hook=True)

    def test_policy_appended_once_without_replacing_original_instruction(self):
        instruction, payload = self.hook({}, {})
        self.assertTrue(instruction.startswith('existing instruction\n\nCurrent operator-relayed parent policy:\n'))
        self.assertEqual(instruction.count(BRIEF), 1)
        self.assertEqual(payload, 'original payload')
        self.original.assert_called_once_with({}, {})
        self.bank.assert_not_called()

    def test_actual_payload_and_binding_are_not_mutated(self):
        binding = dict(cadence_responses=1, existing_parent_lock='unchanged', native_binding_sha256='unchanged')
        state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[observed_output(EXAMPLES[1])])
        before = copy.deepcopy((binding, state))
        self.hook(binding, state)
        self.assertEqual((binding, state), before)
        self.assertIs(self.original.call_args.args[0], binding)
        self.assertIs(self.original.call_args.args[1], state)

    def test_existing_reading_view_remains_in_payload(self):
        state = dict(reading_policy_active={'id': 'synthetic_policy_for_contract_test'},
            reading_discussions=[{'record_index': 12, 'text': 'Already released passage.'}])
        instruction, payload = self.hook({}, state)
        self.assertIn(json.dumps(dict(policy=state['reading_policy_active'],
            discussions=state['reading_discussions']), ensure_ascii=False), payload)
        self.assertNotIn('Already released passage.', instruction)

    def test_question_only_bank_branch_not_bypassed(self):
        binding = dict(questions_only_bank_path='synthetic_bank_not_read_by_test')
        instruction, payload = self.hook(binding, {})
        self.bank.assert_called_once_with(binding)
        self.assertIn('copy one exact text, or remain silent', payload)
        self.assertNotIn('A released question?', instruction)

    def test_isolated_real_base_prompt_preserves_train_view_and_cjk(self):
        original = isolated_function('base_prompt', 'prompt', dict(require=require, Path=Path, json=json))
        config = dict(programme='offline_only', branch='synthetic_contract_test', cadence_label='PERSISTENT',
            principles_path=str(HERE / 'MIXED_CURRICULUM_PARENT_BRIEF.md'),
            programme_path=str(HERE / 'MIXED_CURRICULUM_PARENT_BRIEF.md'))
        latest = observed_output(EXAMPLES[2])
        event = dict(latest, actor='child')
        state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[event],
            sealed_scores={'DO_NOT_DISCLOSE_TEST_SENTINEL': 42})
        before = copy.deepcopy(state)
        instruction, payload = original(config, state)
        self.assertEqual(json.loads(payload)['visible_training_events'][0]['text'], event['text'])
        self.assertNotIn('DO_NOT_DISCLOSE_TEST_SENTINEL', instruction + payload)
        self.assertNotIn(event['text'], instruction)
        self.assertIn('at most90 words', instruction)
        self.assertEqual(state, before)

    def test_existing_base_prompt_rejects_non_train_actor(self):
        original = isolated_function('base_prompt', 'prompt', dict(require=require, Path=Path, json=json))
        config = dict(programme='offline', branch='test', principles_path=str(HERE / 'README.md'),
            programme_path=str(HERE / 'README.md'))
        with self.assertRaisesRegex(ValueError, 'visible_train_actor'):
            original(config, dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1',
                events=[dict(actor='sealed_evaluator', text='not authorized')]))


class DraftReviewTests(unittest.TestCase):
    def setUp(self):
        self.draft = copy.deepcopy(EXAMPLES[0]['draft'])
        self.latest = observed_output(EXAMPLES[0])

    def test_does_not_mutate_draft_or_observation(self):
        before = copy.deepcopy((self.draft, self.latest))
        review_draft(self.draft, self.latest)
        self.assertEqual((self.draft, self.latest), before)

    def test_stale_or_fabricated_reference_flagged(self):
        for key, value in [('record_index', 0), ('record_index', True), ('record_sha256', '0' * 64)]:
            with self.subTest(field=key, value=value):
                draft = copy.deepcopy(self.draft)
                rationale = json.loads(draft['rationale'])
                rationale['latest'][key] = value
                draft['rationale'] = json.dumps(rationale)
                self.assertIn('exact_observed_record_required', review_draft(draft, self.latest))

    def test_quote_must_be_literal_nonempty_and_bounded(self):
        for quote in ['', 'A claim not present in this child output.', 'x' * 241, None]:
            with self.subTest(quote=quote):
                rationale = json.loads(self.draft['rationale'])
                rationale['latest']['quote'] = quote
                self.draft['rationale'] = json.dumps(rationale)
                self.assertIn('literal_observed_quote_required', review_draft(self.draft, self.latest))

    def test_source_bound_cjk_quote_not_filtered(self):
        example = EXAMPLES[2]
        self.assertEqual(review_draft(example['draft'], observed_output(example)), [])

    def test_existing_p7_contract_accepts_overseer_example(self):
        checked = isolated_function('p7_contract', 'checked_coaching', dict(json=json))
        example = EXAMPLES[2]
        reply = observed_output(example)
        result = checked(example['draft'], reply, [])
        self.assertEqual(result['message'], example['draft']['message'])
        self.assertEqual(result['latest']['record_index'], reply['record_index'])

    def test_word_budget_and_identical_reminder_are_review_flags(self):
        self.assertIn('identical_parent_turn', review_draft(self.draft, self.latest,
            previous_messages=[self.draft['message']]))
        self.draft['message'] = 'word ' * 91
        self.assertIn('public_turn_budget', review_draft(self.draft, self.latest))

    def test_human_priority_and_no_baseline_taper(self):
        self.assertIn('genuine_human_priority', review_draft(self.draft, self.latest, pending_human=True))
        self.draft.update(speak=False, message='')
        self.assertIn('persistent_baseline_uncovered_slot', review_draft(self.draft, self.latest))
        self.assertEqual(review_draft(self.draft, self.latest, pending_human=True), [])

    def test_silence_cannot_carry_a_message(self):
        self.draft['speak'] = False
        self.assertIn('silent_message_must_be_empty', review_draft(self.draft, self.latest))

    def test_fabricated_human_or_template_turn_flagged(self):
        for prefix, expected in [('Rohin: ', 'fabricated_speaker_line'),
                ('Parent note\n Fable: ', 'fabricated_speaker_line'),
                ('<|im_start|> ', 'runtime_or_template_tokens'), ('<tool_call>', 'runtime_or_template_tokens')]:
            with self.subTest(prefix=prefix):
                self.draft['message'] = prefix + 'This is a synthetic rejection test.'
                self.assertIn(expected, review_draft(self.draft, self.latest))

    def test_existing_schema_not_extended(self):
        self.draft['subject'] = 'math'
        self.assertEqual(review_draft(self.draft, self.latest), ['existing_response_schema_required'])

    def test_wrong_types_and_malformed_rationale_flagged(self):
        self.draft['speak'] = 'true'
        self.assertEqual(review_draft(self.draft, self.latest), ['existing_response_types_required'])
        self.draft['speak'] = True
        self.draft['rationale'] = {}
        self.assertEqual(review_draft(self.draft, self.latest), ['existing_rationale_string_required'])
        for value in ['invalid json', '[]', '{}']:
            self.draft['rationale'] = value
            self.assertIn('source_bound_rationale_required', review_draft(self.draft, self.latest))

    def test_intervention_needs_an_explanation(self):
        rationale = json.loads(self.draft['rationale'])
        rationale['comparison'] = ''
        self.draft['rationale'] = json.dumps(rationale)
        self.assertIn('intervention_explanation_required', review_draft(self.draft, self.latest))


if __name__ == '__main__':
    unittest.main()
