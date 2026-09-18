"""Synthetic CPU regressions; no provider, GPU, or real publication calls."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch


HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('errata', HOME / 'r175_node4_errata.py')
errata = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(errata)
FIXTURE = HOME / 'activation_20260917T2040Z/physical1'


class ErrataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy, cls.parent = errata.ORIGINAL_IMPORT(FIXTURE)

    def state(self):
        return dict(split='TRAIN', journal_id='a' * 32, caught_up=True, response_count=127,
            head_sha256='b' * 64, request_count=127, sleep_count=41, delivered={}, events=[dict(actor='child',
                text='I counted three cases.', record_index=3, record_sha256='c' * 64)])

    def seed(self):
        return dict(schema=self.policy.SCHEMA, journal_id='a' * 32, attempts=[],
            object_delivered_turns={}, last_response_count=0, last_request_count=0,
            prospective_request_count=0, credits={}, grammar_delivered=False)

    def response(self, **changes):
        details = dict(object_id='cases', source_records=[3], disposition='continue', next_task=None,
            perception=dict(record_index=3, record_sha256='c' * 64, quote='I counted three cases.'),
            credit=None, relapse_credit_id=None)
        details.update(changes)
        return dict(speak=True, message='What did those three cases show?', rationale=json.dumps(details))

    def test_exact_Main_errata_pin(self):
        self.assertEqual(errata.base.sha(HOME.parent / 'PARENT_METADATA_ERRATA_V1.md'), errata.ERRATA_SHA)

    def test_existing_uppercase_validator_unchanged(self):
        state = self.state()
        response = self.response(object_id='ActionsModule-unverified-corrections')
        before = copy.deepcopy(response)
        with self.assertRaisesRegex(ValueError, 'stable_object_id'):
            self.policy.decision(response, state, self.policy.memory(self.seed(), [], state))
        self.assertEqual(response, before)

    def test_continue_private_next_task_nonnull_rejected(self):
        state = self.state()
        with self.assertRaisesRegex(ValueError, 'no_unbound_task'):
            self.policy.decision(self.response(next_task='What did those three cases show?'),
                state, self.policy.memory(self.seed(), [], state))

    def test_child_question_allowed_private_null(self):
        state = self.state()
        self.policy.decision(self.response(), state, self.policy.memory(self.seed(), [], state))

    def test_credit_ID_and_alias_counter_validator_unchanged(self):
        state = self.state()
        memory = self.policy.memory(self.seed(), [], state)
        memory['object_delivered_turns']['cases'] = 2
        with self.assertRaisesRegex(ValueError, 'third_turn'):
            self.policy.decision(self.response(), state, memory)
        credit = dict(id='UpperCase', step='Counted cases', evidence=json.loads(self.response()['rationale'])['perception'])
        response = self.response(credit=credit)
        response['message'] += ' CREDIT: Counted cases.'
        with self.assertRaisesRegex(ValueError, 'structured_own_step_credit'):
            self.policy.decision(response, state, self.policy.memory(self.seed(), [], state))

    def test_H_prior_uncertain_intent_blocks_new_output(self):
        with tempfile.TemporaryDirectory() as directory:
            errata.guard_prior_H([directory])
            Path(directory, 'PUBLICATION_0000_INTENT.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'H_no_prior_publication_intent'):
                errata.guard_prior_H([directory])

    def test_H_failed_attempt_without_intent_allows_next_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory, 'parent_000000000126')
            attempt.mkdir()
            (attempt / 'RESULT.json').write_text(json.dumps(dict(status='VALIDATION_FAILED')))
            errata.guard_prior_H([directory])

    def test_preserved_failed_attempt_reserves_126_without_modelcall(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path(directory)
            errata.base.write(previous / 'SEED.json', self.seed())
            attempt = previous / 'parent/parent_000000000126'
            attempt.mkdir(parents=True)
            source = dict(self.state(), response_count=126, request_count=126)
            errata.base.write(attempt / 'SOURCE.json', source)
            errata.base.write(attempt / 'RESULT.json', dict(status='VALIDATION_FAILED', error='stable_object_id',
                source_sha256=errata.base.sha(attempt / 'SOURCE.json')))
            restored = errata.preserved_seed(previous, self.policy, self.state())
            self.assertEqual(restored['last_response_count'], 126)
            self.assertEqual(restored['attempts'][0]['result']['error'], 'stable_object_id')
            current = dict(self.state(), response_count=126, request_count=126)
            memory = self.policy.memory(restored, [], current)
            self.assertEqual(memory['last_response_count'], 126)
            config = errata.base.read(FIXTURE / 'CONFIG.json')
            with patch.object(self.parent, 'strong', side_effect=AssertionError('no replay')):
                result = self.policy.tick(errata.base.REPO, config, previous, restored, current)
            self.assertEqual(result['status'], 'WAITING_FOR_NEW_CHILD_BOUNDARY')

    def test_clarification_preserves_original_prompt_payload_and_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            lane = Path(directory)
            (lane / 'PARENT_METADATA_ERRATA_V1.md').write_bytes((HOME.parent / 'PARENT_METADATA_ERRATA_V1.md').read_bytes())
            (lane / 'orch_r175_parent_response.py').write_bytes((errata.base.REPO / 'gpu/orch_r175_parent_response.py').read_bytes())
            decision = object()
            policy = types.SimpleNamespace(prompt=lambda *args: ('original', {'shown': 'unchanged'}), decision=decision,
                community=types.SimpleNamespace(response_schema=json.loads))
            with patch.object(errata, 'ORIGINAL_IMPORT', return_value=(policy, None)):
                bound, parent = errata.import_bound(lane)
            instruction, payload = bound.prompt(None, None, None)
            self.assertTrue(instruction.startswith('original\n\n'))
            self.assertIn('`next_task` MUST be JSON null', instruction)
            self.assertEqual(payload, {'shown': 'unchanged'})
            self.assertIs(bound.decision, decision)

    def test_one_authorized_same_source_correction_preserves_failure_clock(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            state = dict(self.state(), request_count=126, response_count=126)
            seed = self.seed()
            seed['attempts'] = [dict(source=state, result=dict(status='VALIDATION_FAILED', error='stable_object_id'),
                original_refs={'synthetic': 'CPU fixture only'})]
            config = errata.base.read(FIXTURE / 'CONFIG.json')
            config['root'] = '/localhome/local-rohing/orch_r175_separate_fork_CPU_fixture/run1'
            with patch.object(self.policy, 'prompt', return_value=('CPU fixture', {})), \
                    patch.object(self.parent, 'strong', return_value=(self.response(), 'CPU_FIXTURE_NOT_REAL', {})) as provider, \
                    patch.object(self.parent, 'publish', return_value={'id': 'fixture-not-real'}) as publisher:
                result = errata.corrective_tick(self.policy, errata.base.REPO, config, output, seed, state)
            self.assertEqual(result['status'], 'PUBLISHED')
            self.assertEqual(result['memory']['last_response_count'], 126)
            self.assertEqual(provider.call_count, 1)
            self.assertEqual(publisher.call_count, 1)
            with self.assertRaisesRegex(ValueError, 'new_corrective_attempt_only'):
                errata.corrective_tick(self.policy, errata.base.REPO, config, output, seed, state)

    def test_compatibility_does_not_relax_ID_validation(self):
        spec = importlib.util.spec_from_file_location('response_compat_test', errata.base.REPO / 'gpu/orch_r175_parent_response.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        response = self.response(object_id='ActionsModule')
        response['rationale'] = json.loads(response['rationale'])
        parsed = module.compatible_parser(self.policy.community.response_schema)(json.dumps(response))
        self.assertEqual(json.loads(parsed['rationale']), response['rationale'])
        state = self.state()
        with self.assertRaisesRegex(ValueError, 'stable_object_id'):
            self.policy.decision(parsed, state, self.policy.memory(self.seed(), [], state))


if __name__ == '__main__':
    unittest.main()
