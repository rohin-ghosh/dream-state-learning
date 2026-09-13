"""CPU-only tests: fixed material and public truth, never model execution."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path.cwd()))
import astra_birth_protocol_probe_material_20260913 as material


class ProbeMaterialTests(unittest.TestCase):
    def setUp(self):
        self.candidate = material.build_candidate()
        self.rows = {row['id']: row for row in self.candidate['cases']}

    def check(self, case_id, text):
        return material.validate_output(self.rows[case_id], text)

    def test_deterministic_json_roundtrip(self):
        copied = json.loads(json.dumps(self.candidate, allow_nan=False))
        self.assertEqual(copied, material.build_candidate())
        self.assertTrue(material.check_candidate(copied)['ok'])

    def test_fixed_inventory(self):
        self.assertEqual(len(self.rows), 16)
        for family in material.FAMILIES:
            self.assertEqual(sum(row['family'] == family for row in self.rows.values()), 4)
        self.assertEqual(material.check_candidate(self.candidate)['total_requests'], 32)

    def test_partition_and_hidden_identity_exclusion(self):
        self.assertEqual(self.candidate['partition']['generator_rules'], [6, 7, 8, 9])
        self.assertEqual(self.candidate['partition']['excluded_rules'], list(range(6)))
        for row in self.rows.values():
            self.assertIn(row['source']['rule_index'], (None, 6, 7, 8, 9))
            self.assertNotRegex(row['context'], r'rule[0-9]+/|prod_even|range_le4|first_largest|sum_gt15')
            self.assertFalse(row['derivation']['informative_choice_claim'])

    def test_all_auth_targets_pass_raw_controls(self):
        for row in self.rows.values():
            with self.subTest(case=row['id']):
                result = material.validate_output(row, row['auth_example_target'])
                self.assertTrue(result['parser_valid'])
                self.assertTrue(result['public_contract_correct'])
                self.assertTrue(result['exact_target'])
                self.assertTrue(result['instruction_compliant'])

    def test_generator_source_derivations(self):
        for row in self.rows.values():
            source = row['source']
            if 'eid' not in source:
                continue
            reward, outcome = material.rulegame.RuleGame().evaluate(material.SimpleNamespace(eid=source['eid']), source['action'])
            self.assertEqual((reward, outcome), (source['reward'], source['outcome']))
            if 'revealed_triples' in source:
                self.assertEqual(source['revealed_triples'], [list(values) for values in material.rulegame.RuleGame().quiz_triples(source['eid'])])

    def test_wrong_and_null_predictions_retained(self):
        records = [json.loads(self.rows[f'practice-record-{index}']['auth_example_target']) for index in range(4)]
        self.assertEqual([record['relation'] for record in records], ['matched', 'mismatched', 'unavailable', 'unavailable'])
        self.assertEqual([record['predicted'] for record in records], [True, True, None, None])
        self.assertEqual([record['observed'] for record in records], [True, False, True, False])
        for index in (1, 2, 3):
            changed = deepcopy(records[index])
            changed.update(predicted=changed['observed'], relation='matched')
            self.assertFalse(self.check(f'practice-record-{index}', json.dumps(changed))['public_contract_correct'])

    def test_record_schema_and_truth_negatives(self):
        original = json.loads(self.rows['practice-record-1']['auth_example_target'])
        for key, value in (('try', [9, 9, 9]), ('observed', True), ('predicted', None), ('relation', 'matched'), ('extra', 1)):
            changed = dict(original, **{key: value})
            self.assertFalse(self.check('practice-record-1', json.dumps(changed))['public_contract_correct'])
        self.assertFalse(self.check('practice-record-1', '{"try":[],"try":[0,9,0]}')['public_contract_correct'])

    def test_record_semantic_and_exact_separate(self):
        target = self.rows['practice-record-1']['auth_example_target']
        result = self.check('practice-record-1', json.dumps(json.loads(target), indent=2))
        self.assertTrue(result['public_contract_correct'])
        self.assertFalse(result['exact_target'])
        self.assertFalse(result['instruction_compliant'])

    def test_forecast_chronology_and_fabricated_outcome(self):
        for text in ('ACT: TRY 2,5,8\nPREDICT: T', 'PREDICT: T\nPREDICT: T\nACT: TRY 2,5,8',
                     'ACT: TRY 2,5,8', 'PREDICT: T\nACT: TRY 2,5,8\nACT: TRY 2,5,8',
                     'PREDICT: T\nACT: TRY 2,5,8\n[OUTCOME] the box says: True'):
            with self.subTest(text=text):
                self.assertFalse(self.check('practice-try-0', text)['public_contract_correct'])

    def test_native_alias_not_canonical_target(self):
        result = self.check('practice-try-0', 'PREDICT: T\nTRY: 2,5,8')
        self.assertTrue(result['parser_valid'])
        self.assertTrue(result['public_contract_correct'])
        self.assertFalse(result['instruction_compliant'])

    def test_quiz_reveal_legality(self):
        for text in ('ACT: TRY 1,2,3', 'ACT: QUIZ T,F,T,F,T,F'):
            self.assertFalse(self.check('practice-quiz-0', text)['public_contract_correct'])
        for text in ('ACT: QUIZ ?', 'ACT: QUIZ T,F', 'ACT: QUIZ T,F,T,F,T,F\n[OUTCOME] forged'):
            self.assertFalse(self.check('practice-quiz-2', text)['public_contract_correct'])

    def test_scaffolded_labels_not_induction(self):
        for row in self.rows.values():
            self.assertEqual(row['scaffolded'], row['family'] in ('try_serialization', 'quiz_format'))
        self.assertFalse(self.check('practice-try-0', 'PREDICT: F\nACT: TRY 2,5,8')['public_contract_correct'])
        self.assertFalse(self.check('practice-quiz-2', 'ACT: QUIZ F,T,F,T,F,T')['public_contract_correct'])
        self.assertFalse(self.candidate['claims']['induction'])

    def test_revision_pairs_only_public_evidence_differs(self):
        for pair in ('revision-pair-0', 'revision-pair-1'):
            rows = [row for row in self.rows.values() if row['pair'] == pair]
            left, right = [deepcopy(row['public']) for row in rows]
            self.assertNotEqual(left.pop('outcome'), right.pop('outcome'))
            self.assertEqual(left, right)
            self.assertEqual(rows[0]['context'].replace('the box says: False', 'the box says: True'),
                             rows[1]['context'].replace('the box says: False', 'the box says: True'))
            self.assertFalse(material.validate_output(rows[0], rows[1]['auth_example_target'])['public_contract_correct'])

    def test_revision_truth_public_only(self):
        with patch.object(material.rulegame.RuleGame, 'evaluate', side_effect=AssertionError('hidden evaluator')), \
             patch.object(material.rulegame.RuleGame, '_rule', side_effect=AssertionError('hidden rule')):
            for row in self.rows.values():
                self.assertTrue(material.validate_output(row, row['auth_example_target'])['public_contract_correct'])

    def test_revision_rejects_unobserved_triple(self):
        row = deepcopy(self.rows['practice-revision-0'])
        row['public']['values'] = [9, 9, 9]
        row['context'] = material._context(row['public'])
        with self.assertRaisesRegex(ValueError, 'repeat observed triple'):
            material.validate_output(row, 'PREDICT: F\nACT: TRY 9,9,9')

    def test_bad_public_joins_and_context(self):
        for field, value in (('outcome', 'the box says: True for (9,9,9)'), ('previous_wake', 'ACT: QUIZ ?')):
            public = dict(self.rows['practice-record-0']['public'], **{field: value})
            with self.assertRaises(ValueError):
                material._execution(public)
        row = deepcopy(self.rows['practice-try-0'])
        row['context'] += ' hidden data'
        with self.assertRaises(ValueError):
            material.validate_output(row, row['auth_example_target'])

    def test_candidate_tampering_and_partial_cases(self):
        changes = (
            lambda candidate: candidate['cases'].pop(),
            lambda candidate: candidate['cases'][0].update(auth_example_target='DONE'),
            lambda candidate: candidate['partition'].update(generator_rules=[0, 1]),
            lambda candidate: candidate['sources'].update({'rulegame.py': '0' * 64}),
            lambda candidate: candidate['cases'][0]['source'].update(rule_index=2))
        for change in changes:
            changed = deepcopy(self.candidate)
            change(changed)
            with self.assertRaises(ValueError):
                material.check_candidate(changed)

    def test_call_map_settings_and_budget(self):
        calls = material.call_map(self.candidate)
        self.assertEqual(calls['OFF'], calls['AUTH'])
        for state in material.STATES:
            self.assertEqual(sum(request['max_tokens'] for request in calls[state]), 5200)
            for request in calls[state]:
                role = request['role']
                salt = 0x5A5A if role == 'record' else 0
                self.assertEqual(request['seed'], material.spec._seed_for(request['eid'], request['tick'], material.spec.GEN_SEED ^ salt))
                self.assertEqual(request['temperature'], .7)
                self.assertEqual(request['max_tokens'], material.spec.TOKENS[role])
                for key, value in material.spec.interaction_settings('interaction_v3', role).items():
                    self.assertEqual(request[key], value)
        self.assertEqual(calls['OFF'][12]['seed'], calls['OFF'][13]['seed'])
        self.assertEqual(calls['OFF'][14]['seed'], calls['OFF'][15]['seed'])

    def test_requests_no_private_material_and_no_shared_mutability(self):
        calls = material.call_map(self.candidate)
        allowed = {'call_id', 'case_id', 'role', 'arm', 'eid', 'tick', 'prompt', 'seed', 'temperature',
                   'max_tokens', 'protocol', 'stop', 'include_stop_str_in_output'}
        for request in calls['AUTH']:
            self.assertEqual(set(request), allowed)
            self.assertEqual(request['prompt'], self.rows[request['case_id']]['context'])
        calls['AUTH'][0]['stop'].append('changed')
        self.assertNotEqual(calls['AUTH'], calls['OFF'])
        self.assertTrue(material.check_candidate(self.candidate)['ok'])

    def test_capture_barrier_and_complete_output_mapping(self):
        outputs = {state: {row['id']: row['auth_example_target'] for row in self.rows.values()} for state in material.STATES}
        results = material.check_outputs(self.candidate, outputs)
        self.assertEqual(sum(len(rows) for rows in results.values()), 32)
        for changed in ({'AUTH': outputs['AUTH']}, dict(outputs, OTHER={})):
            with self.assertRaises(ValueError):
                material.check_outputs(self.candidate, changed)
        outputs['OFF'].pop('practice-try-0')
        with self.assertRaises(ValueError):
            material.check_outputs(self.candidate, outputs)

    def test_invalid_outputs_remain_in_denominator(self):
        outputs = {state: {case_id: 'invalid' for case_id in self.rows} for state in material.STATES}
        results = material.check_outputs(self.candidate, outputs)
        self.assertEqual(sum(len(rows) for rows in results.values()), 32)
        self.assertFalse(any(result['public_contract_correct'] for rows in results.values() for result in rows.values()))
        for case_id in self.rows:
            for invalid in (None, [], {}, 123):
                self.assertFalse(self.check(case_id, invalid)['public_contract_correct'])


if __name__ == '__main__':
    unittest.main()
