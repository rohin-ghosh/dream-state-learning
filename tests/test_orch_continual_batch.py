from copy import deepcopy
import unittest

from organism_v6 import orch_continual_batch as policy


class Tokenizer:
    eos_token = '§'
    eos_token_id = ord('§')
    all_special_ids = [ord('§')]

    def encode(self, text, **unused):
        return list(map(ord, text))

    def decode(self, tokens, **unused):
        return ''.join(map(chr, tokens))

    def apply_chat_template(self, messages, add_generation_prompt=False, **unused):
        text = ''.join(message['role'] + ':' + message['content'] +
                       ('§\n' if message['role'] == 'assistant' else '\n') for message in messages)
        return text + ('assistant:' if add_generation_prompt else '')


def fixture():
    task = dict(id='gsm8k-train-1', question='What is 2 plus 3?', gold='5', family='percentages')
    task['question_sha256'] = policy.math.digest(task['question'].lower())
    target = 'I used 2+3=5 and checked the sum.\nFINAL: 5'
    call = dict(task_id=task['id'], gold='5', stage='source', strategy='ORIGINAL_RICH',
        messages=[dict(role='system', content='guidance'), dict(role='user', content=task['question'])],
        response=dict(raw=target, token_ids=Tokenizer().encode(target) + [Tokenizer.eos_token_id],
                      terminal=True, truncated=False), outcome=dict(outcome_pass=True))
    return call, task, dict(observed={'state': 'same'}), dict(initial={'state': 'same'}), Tokenizer(),


def rows_and_reviews():
    rows = [dict(target_sha256=policy.text_sha(str(index)), target='FINAL: 5', gold='5',
                 student_prefix_sha256='prefix', provenance=dict(raw_call_sha256='raw'),
                 semantic_status='UNREVIEWED') for index in range(64)]
    reviews = [dict(target_sha256=row['target_sha256'], raw_call_sha256='raw', student_prefix_sha256='prefix',
        status='PASS', reason='Concrete arithmetic.', full_text_read=True, evidence_spans=['FINAL: 5'],
        gold_status='VALID', independent_answer='5', **dict.fromkeys(policy.AXES, True)) for row in policy.sample(rows)]
    return rows, reviews


class BatchTests(unittest.TestCase):
    def mechanical(self, changed=None, exclusions=None, provenance=None):
        call, task, loaded, prepared, tokenizer = fixture()
        if changed:
            changed(call)
        return policy.mechanical(call, task, loaded, prepared, tokenizer,
            exclusions or dict(math_ids=[], question_hashes=[], route_ids=[]),
            provenance or dict(registered_source_purpose=policy.PURPOSE, source_registry_sha256='bound'))

    def test_exact_encoder_and_raw_preservation(self):
        row = self.mechanical()
        self.assertFalse(row['admitted'])
        self.assertEqual(row['target'], row['call']['raw'])
        self.assertEqual(row['training_encoding']['labels'][-1], -100)

    def test_parenting_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'quarantine'):
            self.mechanical(provenance=dict(registered_source_purpose='L2_PARENTING', source_registry_sha256='bound'))

    def test_held_ids_and_hashes_rejected(self):
        for exclusions in (dict(math_ids=['gsm8k-train-1'], question_hashes=[], route_ids=[]),
                           dict(math_ids=[], question_hashes=[fixture()[1]['question_sha256']], route_ids=[])):
            with self.assertRaisesRegex(ValueError, 'held_overlap'):
                self.mechanical(exclusions=exclusions)

    def test_wrong_original_final_rejected(self):
        with self.assertRaisesRegex(ValueError, 'oracle_failure'):
            self.mechanical(lambda call: call['response'].update(raw='FINAL: 7'))

    def test_truncation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'truncated'):
            self.mechanical(lambda call: call['response'].update(truncated=True))

    def test_oversize_no_crop(self):
        def change(call):
            target = 'a' * 2100 + '\nFINAL: 5'
            call['response'].update(raw=target, token_ids=list(map(ord, target)) + [Tokenizer.eos_token_id])
        with self.assertRaisesRegex(ValueError, 'skip_unsupported_traincontext_no_crop'):
            self.mechanical(change)

    def test_short_text_not_mechanically_rejected(self):
        self.assertLess(self.mechanical()['generated_tokens'], 150)

    def test_fixed_deterministic_sample(self):
        rows, reviews = rows_and_reviews()
        self.assertEqual(policy.sample(rows), policy.sample(list(reversed(rows))))
        self.assertEqual(len(reviews), 12)

    def test_duplicate_target_rejected(self):
        rows, unused = rows_and_reviews()
        rows[-1] = rows[0]
        with self.assertRaises(ValueError):
            policy.sample(rows)

    def test_unsampled_not_invented_pass(self):
        rows, reviews = rows_and_reviews()
        decision, exported = policy.adjudicate(rows, reviews)
        self.assertTrue(decision['accepted'])
        self.assertEqual(sum(row['semantic_status'] == 'UNREVIEWED' for row in exported), 52)
        self.assertTrue(all(not row['admitted'] for row in exported))

    def test_register_is_not_gate_v2(self):
        rows, reviews = rows_and_reviews()
        for review in reviews:
            review['first_person'] = False
        policy.validate_review(policy.sample(rows), dict(reviews=reviews))
        self.assertTrue(policy.adjudicate(rows, reviews)[0]['accepted'])

    def test_literal_spans_required(self):
        rows, reviews = rows_and_reviews()
        reviews[0]['evidence_spans'] = ['invented span']
        with self.assertRaises(ValueError):
            policy.validate_review(policy.sample(rows), dict(reviews=reviews))

    def test_grounding_failure_blocks_batch(self):
        rows, reviews = rows_and_reviews()
        reviews[0].update(status='FAIL', grounded_operations=False)
        self.assertFalse(policy.adjudicate(rows, reviews)[0]['accepted'])

    def test_known_sample_failures_excluded(self):
        rows, reviews = rows_and_reviews()
        reviews[0].update(status='FAIL', reusable_content=False)
        decision, exported = policy.adjudicate(rows, reviews)
        self.assertTrue(decision['accepted'])
        self.assertEqual(len(exported), 63)


if __name__ == '__main__':
    unittest.main()
