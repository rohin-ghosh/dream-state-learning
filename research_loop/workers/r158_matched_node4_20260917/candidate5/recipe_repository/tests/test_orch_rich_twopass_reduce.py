import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_rich_twopass_reduce as reducer
from organism_v6 import orch_rich_twopass as policy


class ReduceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        tasks = []
        for family in policy.original.MINING:
            for index in range(64):
                question = f'Synthetic {family} task {index}.'
                tasks.append(dict(id=f'{family}-{index}', question=question,
                    question_sha256=policy.original.digest(question.lower()), family=family, gold='10'))
        document = dict(tasks=tasks, denominator=256, per_family=64, no_l2_l3_access=True,
                        excluded_ids=[f'old-{index}' for index in range(1216)],
                        excluded_question_hashes=[f'old-hash-{index}' for index in range(1216)])
        self.save(self.root / 'TASKS.json', document)
        self.sha_patch = patch.object(policy, 'TASKS_SHA', reducer.sha(self.root / 'TASKS.json'))
        self.sha_patch.start()
        self.addCleanup(self.sha_patch.stop)
        self.task = tasks[0]
        response = dict(raw='I multiply the quantities and can check the result.\nFINAL: 10',
                        token_ids=[7] * 200 + [8], terminal=True, truncated=False, prompt_tokens=600)
        self.row = policy.capture(self.task, 'final', 'BRANCH', response,
                                  [{'role': 'user', 'content': self.task['question']}])
        self.row.update(status='OK', index=0, position=0)
        self.path = self.root / 'shard0/CALL_0000.json'
        self.save(self.path, self.row)
        (self.root / 'CALLS.jsonl').write_text(json.dumps(dict(index=0, position=0,
            stage='final', condition='BRANCH')) + '\n')

    def save(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def decision(self):
        return dict(raw_call_sha256=reducer.sha(self.path), target_sha256=self.row['target_sha256'],
            student_prefix_sha256=policy.original.digest(self.row['student_prefix']), full_text_read=True,
            status='PASS', reason='Synthetic test only.', prefix_reason='Bound question.',
            evidence_spans=['I multiply the quantities'], **dict.fromkeys(policy.admission.AXES, True))

    def test_fixed_denominators_unreviewed_not_qualified_and_eos_accounted(self):
        result, admitted = reducer.reduce(self.root)
        self.assertEqual(result['fixed_denominator'], 256)
        self.assertEqual(result['conditions']['BRANCH']['stages']['final']['unreviewed_candidates'], 1)
        self.assertEqual(result['conditions']['BRANCH']['families']['percentages']['fixed_denominator'], 64)
        self.assertEqual(result['known_generated_tokens'], 200)
        self.assertEqual(result['known_generated_token_ids_including_eos'], 201)
        self.assertFalse(result['complete'])
        self.assertEqual(admitted, [])

    def test_exact_review_requires_valid_independent_gold(self):
        key = self.task['id'] + ':BRANCH:final'
        reviews = {key: self.decision()}
        self.assertEqual(reducer.reduce(self.root, reviews)[1], [])
        gold = {self.task['id']: dict(status='VALID', question_sha256=self.task['question_sha256'],
                                    independent_answer='10', reason='Synthetic calculation.')}
        self.assertEqual(len(reducer.reduce(self.root, reviews, gold)[1]), 1)
        gold[self.task['id']]['independent_answer'] = '11'
        with self.assertRaises(AssertionError):
            reducer.reduce(self.root, reviews, gold)

    def test_review_cannot_move_to_changed_raw_bytes_or_neutral_history(self):
        key = self.task['id'] + ':BRANCH:final'
        decision = self.decision()
        decision['raw_call_sha256'] = 'wrong'
        with self.assertRaises(AssertionError):
            reducer.reduce(self.root, {key: decision})
        decision = self.decision()
        decision['student_prefix_sha256'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'neutral_prefix'):
            reducer.reduce(self.root, {key: decision})

    def test_missing_raw_response_still_counts_reserved_attempt(self):
        with (self.root / 'CALLS.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(index=1, position=0, stage='final', condition='CONTINUE')) + '\n')
        result, unused = reducer.reduce(self.root)
        self.assertEqual(result['attempts_recorded'], 2)
        self.assertEqual(result['raw_call_files'], 1)
        self.assertEqual(result['reserved_without_call_file'], 1)
        final = result['conditions']['CONTINUE']['stages']['final']
        self.assertEqual(final['attempts'], 1)
        self.assertEqual(final['raw_call_files'], 0)
        self.assertEqual(final['reserved_without_call_file'], 1)
        self.assertTrue(result['failed_call_token_usage_unknown'])
        self.assertFalse(result['complete'])

    def test_record_denominator_is_conditional_without_losing_fixed_roster(self):
        result, unused = reducer.reduce(self.root)
        record = result['conditions']['BRANCH']['stages']['record']
        self.assertEqual(record['fixed_denominator'], 256)
        self.assertEqual(record['eligible_opportunities'], 1)
        self.assertEqual(record['not_attempted_eligible'], 1)
        self.assertEqual(record['successful_generations'], 0)

    def test_reserved_raw_has_unknown_usage_and_no_outcome(self):
        self.row['status'] = 'RESERVED'
        for field in ('call', 'target', 'target_sha256', 'generated_tokens',
                      'outcome_pass', 'candidate', 'token_contract_pass'):
            self.row.pop(field, None)
        self.save(self.path, self.row)
        result, admitted = reducer.reduce(self.root)
        final = result['conditions']['BRANCH']['stages']['final']
        self.assertEqual(final['pending_raw_calls'], 1)
        self.assertEqual(final['successful_generations'], 0)
        self.assertTrue(result['failed_call_token_usage_unknown'])
        self.assertEqual(admitted, [])

    def test_semantic_coverage_is_not_candidate_or_outcome_coverage(self):
        result, unused = reducer.reduce(self.root)
        final = result['conditions']['BRANCH']['stages']['final']
        self.assertEqual(final['reviewed_targets'], 0)
        self.assertEqual(final['unreviewed_targets'], 1)
        self.assertEqual(final['outcome_pass'], 1)
        self.assertEqual(final['qualified_rows'], 0)

    def test_error_counts_as_attempt_not_successful_generation(self):
        self.row.update(status='ERROR', outcome_pass=False, candidate=False,
                        token_contract_pass=False, error='Preserved synthetic failure.')
        self.save(self.path, self.row)
        result, admitted = reducer.reduce(self.root)
        final = result['conditions']['BRANCH']['stages']['final']
        self.assertEqual(final['attempts'], 1)
        self.assertEqual(final['errors'], 1)
        self.assertEqual(final['successful_generations'], 0)
        self.assertTrue(result['failed_call_token_usage_unknown'])
        self.assertEqual(admitted, [])


if __name__ == '__main__':
    unittest.main()
