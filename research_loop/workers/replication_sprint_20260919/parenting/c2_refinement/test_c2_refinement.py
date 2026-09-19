"""CPU-only original-hook/continuation tests; fixtures are not live outcomes."""

import copy
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import candidate


ORIGINAL = candidate.read(candidate.ORIGINAL_MANIFEST)
CONFIG = candidate.read(ORIGINAL['config_path'])


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(candidate.encoded(value))


class OriginalHookTests(unittest.TestCase):
    def test_original_source_closure_unchanged(self):
        candidate.check_pins(ORIGINAL)

    def test_actual_started_config_not_just_top_manifest_has_no_bank(self):
        started = candidate.read(Path(ORIGINAL['output']) / 'STARTED.json')
        self.assertEqual(started['config_sha256'], candidate.sha(ORIGINAL['config_path']))
        candidate.no_question_bank(CONFIG)

    def test_original_addendum_hook_preserves_payload_and_state(self):
        original_prompt = candidate.function(candidate.BASE, 'prompt', dict(
            require=candidate.require, Path=Path, json=json))
        old = Path(ORIGINAL['policy_addendum']).read_text()
        delta = (HERE / 'POLICY_DELTA.md').read_text()
        combined = old + '\n\n' + delta
        hook = candidate.function(candidate.HOOK, 'prompt', dict(
            original_prompt=original_prompt, addendum=combined, json=json), hook=True)
        state = candidate.read(Path(ORIGINAL['output']) / 'parent_000108/SOURCE.json')
        before = copy.deepcopy(state)
        instruction, payload = hook(CONFIG, state)
        base_instruction, base_payload = original_prompt(CONFIG, state)
        self.assertTrue(instruction.startswith(base_instruction))
        self.assertIn(old + '\n\n' + delta, instruction)
        self.assertTrue(payload.startswith(base_payload))
        self.assertEqual(state, before)
        self.assertIn('at most90 words', instruction)
        self.assertIn('Genuine human priority', instruction)
        self.assertIn('next observable ACT', instruction)
        self.assertNotIn('first six committed ACT opportunities', instruction)

    def test_original_hook_keeps_reading_discussion_payload(self):
        original_prompt = candidate.function(candidate.BASE, 'prompt', dict(
            require=candidate.require, Path=Path, json=json))
        hook = candidate.function(candidate.HOOK, 'prompt', dict(
            original_prompt=original_prompt, addendum='Offline composition fixture', json=json), hook=True)
        fixture = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[],
                       reading_policy_active={'fixture': 'existing-policy'}, reading_discussions=['released fixture'])
        instruction, payload = hook(CONFIG, fixture)
        self.assertIn('released fixture', payload)
        self.assertNotIn('released fixture', instruction)

    def test_original_prompt_rejects_sealed_actor(self):
        prompt = candidate.function(candidate.BASE, 'prompt', dict(
            require=candidate.require, Path=Path, json=json))
        with self.assertRaisesRegex(ValueError, 'visible_train_actor'):
            prompt(CONFIG, dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1',
                events=[dict(actor='sealed_evaluator', text='synthetic forbidden actor')]))

    def test_bank_presence_including_null_and_nested_is_a_conflict(self):
        for extra in ({'questions_only_bank_path': None}, {'questions_only_bank_path': '/fixture'},
                      {'nested': {'questions_only_first_id': 'fixture'}}):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, 'question_bank_mode_conflicts'):
                candidate.no_question_bank(dict(CONFIG, **extra))

    def test_policy_no_answers_and_stable_target(self):
        delta = (HERE / 'POLICY_DELTA.md').read_text()
        for phrase in ('THINK request', 'three-rendered-turn budget', 'All child rows still train',
                       'already released', 'one concrete check', 'not an established capability'):
            self.assertIn(phrase, delta)
        for answer in ('V = 3', 'n=4', '354', 'size 2'):
            self.assertNotIn(answer, delta)

    def test_standing_document_hashes(self):
        for record in candidate.read(HERE / 'PROVENANCE.json')['standing_documents']:
            content = subprocess.check_output(['git', 'show', record['git_commit'] + ':' + record['path']],
                                              cwd=candidate.REPO, timeout=10)
            self.assertEqual(hashlib.sha256(content).hexdigest(), record['sha256'])


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='.cpu-test-', dir=HERE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / 'prior'
        put(self.output / 'STARTED.json', dict(branch='C2', programme=CONFIG['programme']))
        self.attempt = self.output / 'parent_000000'
        put(self.attempt / 'SOURCE.json', dict(response_count=600))
        put(self.attempt / 'DISPATCH_INTENT.json', dict(retries=0))
        self.config = dict(CONFIG, predecessor_output=str(self.output),
                           predecessor_started_sha256=candidate.sha(self.output / 'STARTED.json'),
                           start_after_response_count=600)

    def result(self, value):
        put(self.attempt / 'RESULT.json', value)

    def test_original_cursor_preserves_reservations_not_just_successes(self):
        cursor = candidate.original_validators(CONFIG)['resume_cursor']
        self.assertEqual(cursor(self.config), 600)
        with self.assertRaisesRegex(ValueError, 'no_replay_of_reserved_parent_sources'):
            cursor(dict(self.config, start_after_response_count=599))

    def test_original_config_validator_rejects_effort_or_cadence_change(self):
        validate = candidate.original_validators(CONFIG)['validate_config']
        validate(CONFIG, self.config)
        for key, value in [('parent_reasoning_effort', 'xhigh'), ('cadence_responses', 2),
                           ('native_binding_sha256', '0' * 64), ('existing_parent_lock', '/other')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(CONFIG, dict(self.config, **{key: value}))

    def test_original_manifest_validator_runs_without_parent_import_or_API(self):
        previous_path, proposed_path = self.root / 'OLD.json', self.root / 'NEW.json'
        put(previous_path, CONFIG)
        put(proposed_path, self.config)
        manifest = dict(config_path=str(proposed_path), predecessor_config_path=str(previous_path),
                        output=str(self.root / 'unused-parent'), local_source_sha256={
                            str(proposed_path): candidate.sha(proposed_path), str(previous_path): candidate.sha(previous_path)})
        validate = candidate.original_validators(CONFIG)['validate_manifest']
        self.assertEqual(validate(manifest), self.config)
        put(proposed_path, dict(self.config, parent_reasoning_effort='high'))
        with self.assertRaisesRegex(ValueError, 'exact_R233_parent_closure'):
            validate(manifest)

    def test_inflight_attempt_blocks_and_reserves_its_source(self):
        state = candidate.ledger(self.output, CONFIG)
        self.assertEqual(state['reserved'], 600)
        self.assertEqual(state['counts']['dispatch_intents'], 1)
        self.assertTrue(state['pending'])

    def test_published_without_delivery_remains_unknown(self):
        self.result(dict(status='PUBLISHED', inbox_publication=dict(id='synthetic-inbox')))
        state = candidate.ledger(self.output, CONFIG)
        self.assertEqual(state['pending'][0]['kind'], 'publication_consumption_unknown')
        self.assertEqual(state['pending'][0]['inbox_id'], 'synthetic-inbox')

    def test_bound_delivery_changes_signature_without_rewriting_result(self):
        self.result(dict(status='PUBLISHED', inbox_publication=dict(id='synthetic-inbox')))
        before = candidate.ledger(self.output, CONFIG)
        result_sha = candidate.sha(self.attempt / 'RESULT.json')
        put(self.attempt / 'DELIVERED.json', dict(status='COMPLETE', inbox_id='synthetic-inbox', result_sha256=result_sha))
        after = candidate.ledger(self.output, CONFIG)
        self.assertEqual(after['pending'], [])
        self.assertNotEqual(after['signature'], before['signature'])
        self.assertEqual(candidate.sha(self.attempt / 'RESULT.json'), result_sha)

    def test_wrong_delivery_is_not_accepted(self):
        self.result(dict(status='PUBLISHED', inbox_publication=dict(id='synthetic-inbox')))
        put(self.attempt / 'DELIVERED.json', dict(status='COMPLETE', inbox_id='other', result_sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'delivery_bound_to_actual_publication'):
            candidate.ledger(self.output, CONFIG)

    def test_recorded_HTTP_failure_is_retained_not_retried_or_praised(self):
        self.result(dict(status='MISSING', error_type='HTTPError'))
        before = candidate.sha(self.attempt / 'RESULT.json')
        state = candidate.ledger(self.output, CONFIG)
        self.assertEqual(state['counts']['MISSING'], 1)
        self.assertEqual(state['reserved'], 600)
        self.assertFalse(state['failures'][0]['retry'])
        self.assertEqual(candidate.sha(self.attempt / 'RESULT.json'), before)

    def test_unknown_publish_failure_cannot_be_skipped(self):
        self.result(dict(status='MISSING', error_type='RuntimeError', response=dict(speak=True)))
        self.assertEqual(candidate.ledger(self.output, CONFIG)['pending'][0]['kind'],
                         'uncertain_attempt_requires_reconciliation')

    def test_original_service_selects_seed_and_refreshes_reserved_cursor(self):
        seed_dir = self.root / 'c2_session_seed_fixture'
        config_path = self.root / 'CONFIG.json'
        put(config_path, CONFIG)
        seed = dict(output=str(self.output), config_path=str(config_path), policy_addendum='fixture-combined')
        put(seed_dir / 'MANIFEST.json', seed)
        names = {'prior_paths', 'prior_path', 'previous', 'previous_config', 'previous_output', 'reserved', 'config'}
        tree = ast.parse(candidate.SERVICE.read_bytes())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        selected = sorted([node for node in ast.walk(main) if isinstance(node, ast.Assign)
                           and any(isinstance(target, ast.Name) and target.id in names for target in node.targets)],
                          key=lambda node: node.lineno)
        namespace = dict(OWN=self.root, Path=Path, read=candidate.read, sha=candidate.sha)
        exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])),
                     'original_c2_service_selection_and_cursor_only', 'exec'), namespace)
        self.assertEqual(namespace['previous']['policy_addendum'], 'fixture-combined')
        self.assertEqual(namespace['config']['start_after_response_count'], 600)
        self.assertEqual(namespace['config']['predecessor_output'], str(self.output))
        self.assertEqual(namespace['config']['parent_reasoning_effort'], CONFIG['parent_reasoning_effort'])

    def test_original_supervisor_inherits_environment_without_override(self):
        tree = ast.parse(candidate.SERVICE.read_bytes())
        launches = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and node.func.attr == 'Popen']
        self.assertEqual(len(launches), 1)
        self.assertNotIn('env', {keyword.arg for keyword in launches[0].keywords})
        text = candidate.SERVICE.read_text()
        self.assertIn("OWN / 'C2_SERVICE.lock'", text)
        self.assertIn("PREVIOUS / 'private/C2_WAIT_CONTROLLER.lock'", text)


if __name__ == '__main__':
    unittest.main()
