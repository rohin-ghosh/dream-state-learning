from copy import deepcopy
import unittest

from organism_v6 import orch_teacher_branching_pilot as pilot
from gpu import orch_guided_native as native
from gpu import orch_teacher_branching_pilot_interface as interface


class Tokenizer:
    eos_token = '\x01'
    eos_token_id = 1
    all_special_ids = [1]

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt, return_dict):
        prefix = 'USER: ' + messages[0]['content'] + '\nASSISTANT: '
        return prefix if add_generation_prompt else prefix + messages[-1]['content'] + self.eos_token + '\n'

    def encode(self, text, **kwargs):
        return list(map(ord, text))

    def decode(self, values, **kwargs):
        return ''.join(map(chr, values))


class TeacherPilotTests(unittest.TestCase):
    def setUp(self):
        self.prompt = dict(source_label=pilot.LABEL, split='TRAIN', task_id='FIXED_TRAIN_0',
                           domain='math', problem='What is 2 + 3?', observed_events=[])
        self.response = dict(source_label=pilot.LABEL,
            methods=[dict(name='Addition', explanation='2 plus 3 equals 5.'),
                     dict(name='Count forward', explanation='From 2: 3, 4, 5.')],
            checks=['5 minus 3 is 2.', '5 minus 2 is 3.'], final_answer='5', limitations='Teacher-only metadata.')
        self.oracle = dict(domain='math', answer='5')
        self.refs = {'RAW_RESPONSE.json': dict(path='/native/teacher/raw.json', sha256='a' * 64)}
        self.audit = dict(author_supported=True, independent_certification=False,
                          diversity='WEAK_ALGEBRAIC_REARRANGEMENT')

    def row(self, **kwargs):
        return pilot.compile_row(kwargs.get('prompt', self.prompt), kwargs.get('response', self.response),
            self.oracle, kwargs.get('forbidden', ['SEALED_NODE']), self.refs, self.audit)

    def test_exact_field_spans_and_neutral_prefix(self):
        row = self.row()
        self.assertEqual(row['student_prefix'], [dict(role='user', content=self.prompt['problem'])])
        for span in row['target_field_spans']:
            self.assertEqual(pilot.text_hash(row['target'][span['start']:span['end']]), span['sha256'])
        self.assertTrue(row['target'].endswith('FINAL: 5'))
        self.assertNotIn(self.response['limitations'], row['target'])
        self.assertNotIn(pilot.teacher.SYSTEM, row['target'])
        self.assertFalse(row['ongoing_l1_allowed'])
        self.assertFalse(row['own_generated'])
        self.assertFalse(row['training_application_allowed'])

    def test_held_teacher_and_parenting_mislabels_rejected(self):
        for changes in [dict(split='HELD'), dict(source_label='CHECKPOINT_DERIVED'),
                        dict(source_label='L2_PARENTING_EXPERIENCE'), dict(gold='5')]:
            with self.assertRaises(ValueError):
                self.row(prompt=dict(self.prompt, **changes))

    def test_held_identifier_in_input_or_response_rejected(self):
        with self.assertRaises(ValueError):
            self.row(prompt=dict(self.prompt, problem='Use SEALED_NODE'))
        with self.assertRaises(ValueError):
            self.row(response=dict(self.response, checks=['SEALED_NODE', 'check']))

    def test_wrong_answer_not_repaired(self):
        with self.assertRaisesRegex(ValueError, 'teacher_final_answer_incorrect'):
            self.row(response=dict(self.response, final_answer='6'))

    def test_weak_methods_not_relabelled_independent(self):
        row = self.row()
        self.assertEqual(row['author_audit'], self.audit)
        self.assertFalse(row['author_audit']['independent_certification'])

    def test_short_and_over400_targets_supported(self):
        for length in (10, 500):
            response = deepcopy(self.response)
            response['methods'][0]['explanation'] = 'x' * length
            self.assertEqual(len(pilot.encode_rows([self.row(response=response)], Tokenizer())), 1)

    def test_raw_preserved_on_oversize_and_hash_failure(self):
        row = self.row()
        row['target'] = 'x' * 8193
        row['target_sha256'] = pilot.text_hash(row['target'])
        before = deepcopy(row)
        with self.assertRaisesRegex(ValueError, 'unsupported_train_context'):
            pilot.encode_rows([row], Tokenizer())
        self.assertEqual(row, before)
        row['target_sha256'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'compiled_row_hash_mismatch'):
            pilot.encode_rows([row], Tokenizer())

    def test_masked_arm_only_changes_new_labels_including_eos(self):
        row = pilot.encode_rows([self.row()], Tokenizer())[0]
        rehearsal = pilot.paired_rehearsal([row] * 222, [row] * 16)
        self.assertTrue(rehearsal['legacy_masks_unchanged'])
        self.assertTrue(rehearsal['teacher_eos_also_masked'])
        self.assertEqual(rehearsal['changed_rows'], list(range(222, 238)))
        for arm, layout in rehearsal['layouts'].items():
            self.assertEqual(layout['updates'], 56)
            self.assertEqual(layout['new_target_presentations'], 64)
            self.assertEqual(layout['old_memory_presentations'], 56)
            self.assertEqual(layout['old_behavior_presentations'], 56)
            self.assertEqual(layout['old_trajectory_presentations'], 48)
        self.assertEqual(rehearsal['layouts'][pilot.ARMS[1]]['new_supervised_presentations'], 0)

    def test_no_dose16_or_ongoing_feed_or_launch_authorization(self):
        protocol = pilot.protocol()
        self.assertEqual(protocol['candidate_physical_gpus'], [4, 5])
        self.assertEqual(protocol['generation_calls_pair_max'], 2 * (16 + 48 + 48))
        self.assertEqual(protocol['output_tokens_pair_max'], 2 * (64 * 4096 + 48 * 160))
        for field in ('launch_allowed', 'dose16_authorized', 'ongoing_l1_allowed', 'publisher_quota_changed'):
            self.assertFalse(protocol[field])

    def test_proven_training_batches_preserve_reference_denominator(self):
        row = pilot.encode_rows([self.row()], Tokenizer())[0]
        totals = interface.paired_batches((row,) * 238, pad_id=0)
        self.assertEqual(totals['full_reference'], totals['masked_reference'])
        self.assertEqual(totals['full_reference'], totals['full_active'])
        self.assertLess(totals['masked_active'], totals['full_active'])

    def test_route_readout_requires_exact_two_worlds(self):
        with self.assertRaisesRegex(ValueError, 'exact_two_held_route_worlds'):
            interface.evaluate_routes([], lambda messages: None, lambda name, value: None)


if __name__ == '__main__':
    unittest.main()
