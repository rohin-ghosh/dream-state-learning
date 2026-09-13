"""Golden public visibility and actual RuleGame transitions; CPU fixtures only."""
import copy
import json
import unittest
from unittest.mock import patch

from organism_v6 import rulegame_action_projection as projection
from organism_v6 import rulegame_parenting_diagnostic as diagnostic


BUNDLE0 = 'PREDICT: T\nACT: TRY 3,6,9\nPREDICT: T\nACT: TRY 1,3,5\nPREDICT: F\nACT: QUIZ ?'
BUNDLE1 = 'PREDICT: T\nACT: TRY 2,3,4\nPREDICT: T\nACT: TRY 4,5,6\nPREDICT: T\nACT: QUIZ ?'
RAW_SIX = (('0001', BUNDLE0), ('0007', BUNDLE1), ('0019', BUNDLE0),
           ('0022', 'COMPARE'), ('0024', BUNDLE1), ('0027', 'COMPARE:COMPARE:COMPARE'))


class Calls:
    protocol = 'interaction_v3'

    def __init__(self, outputs, before=None):
        self.outputs, self.rows, self.count = iter(outputs), [], 0
        self.before = before

    def ask(self, role, arm, eid, tick, prompt):
        if self.before is not None:
            self.before(role, tick, prompt)
        call_id = f'{self.count:04d}'
        self.rows.append(dict(role=role, arm=arm, eid=eid, tick=tick, prompt=prompt, call_id=call_id))
        self.count += 1
        if role == 'wake':
            return call_id, next(self.outputs)
        fields = json.loads(prompt.split('Observed fields: ', 1)[1].splitlines()[0])
        predicted, observed = fields['predicted'], fields['observed']
        relation = 'unavailable' if predicted is None else 'matched' if predicted == observed else 'mismatched'
        return call_id, json.dumps({'try': fields['values'], 'observed': observed, 'predicted': predicted, 'relation': relation})


class ActionProjectionTests(unittest.TestCase):
    def task(self, outputs, *, notes=True, before=None, prefix=''):
        calls, events = Calls(outputs, before), diagnostic.Events()
        result, transcript = projection.play_task(calls, events, 'P', projection.task_id(0, 'pre'), notes=notes, prefix=prefix)
        return calls, events.rows, result, transcript

    def test_exact_six_rejected_raws_still_fail_original_parser(self):
        for call_id, raw in RAW_SIX:
            error = 'multiple action markers' if call_id in ('0001', '0007', '0019', '0024') else 'missing canonical ACT'
            with self.subTest(call=call_id), self.assertRaisesRegex(ValueError, error):
                diagnostic.parse_action(raw, 'interaction_v3')

    def test_original_diagnostic_bytes_and_fresh_schedule(self):
        self.assertEqual(diagnostic.digest(diagnostic.__file__), 'e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526')
        self.assertEqual(projection.schedule(), {'formation': [f'rule{rule}/astra-action-projection-v1-20260913/lesson{rule}/{phase}'
                         for rule in (0, 1) for phase in ('pre', 'apply')], 'evaluation': []})
        self.assertFalse(set(projection.schedule()['formation']) & set(diagnostic.schedule()['formation']))
        with self.assertRaises(ValueError):
            projection.play_task(Calls(['DONE']), diagnostic.Events(), 'P', diagnostic.task_id(0, 'pre'))

    def test_no_salvage_world_or_record_before_projection(self):
        events = diagnostic.Events()
        original = diagnostic.RuleGame.evaluate
        with patch.object(diagnostic.RuleGame, 'evaluate', autospec=True, side_effect=original) as world:
            def before(role, tick, prompt):
                if role == 'wake' and tick == 2:
                    world.assert_not_called()
                    self.assertEqual([row['kind'] for row in events.rows], ['wake_response', 'protocol_invalid'])
                    self.assertFalse(events.rows[-1]['executed'])
                    self.assertEqual(events.rows[-1]['raw_response'], BUNDLE0)
            calls = Calls([BUNDLE0, 'PREDICT: F\nACT: TRY 9,8,7', 'DONE'], before)
            result, transcript = projection.play_task(calls, events, 'P', projection.task_id(0, 'pre'), notes=True)
            self.assertEqual(world.call_count, 1)
            self.assertEqual(world.call_args.args[2], 'TRY 9,8,7')
        execution = next(row for row in events.rows if row['kind'] == 'execution')
        record = next(row for row in events.rows if row['kind'] == 'record')
        self.assertEqual((execution['tick'], execution['call_id'], execution['projection_of']), (2, '0001', '0000'))
        self.assertEqual(record['source_call_id'], '0001')
        self.assertTrue(record['eligible'])
        self.assertEqual(result['wake_slots_used'], 3)
        self.assertIn(BUNDLE0, transcript)

    def test_projection_visibility_exact_golden_with_unchanged_restatement(self):
        raw = 'COMPARE:COMPARE  \n'
        prefix = 'PREDICT:COMPARE:COMPARE\nMATCH'
        calls, events, result, transcript = self.task([raw, 'DONE'], prefix=prefix)
        identifier = projection.task_id(0, 'pre')
        expected = (diagnostic.BOOT + f'\nTask: {identifier}\nGoal: Induce the hidden rule and answer the quiz.\n'
            'Response: 2/5\nA fresh mystery box.\nTemporary parent restatement:\n'+prefix+
            '\n[UNEXECUTED_PROPOSAL response=1 call=0000; no action dispatched]\n'+raw+
            '\n[END UNEXECUTED_PROPOSAL response=1; NO ACTION OR WORLD RESULT]'
            '\nHarness state: remaining TRY budget: 3. Quiz reveal still needed before scoring: ACT: QUIZ ?.'
            '\nEmit one action only; never supply [OUTCOME] or simulate a world reply.'
            '\n[ONE ACTION PROJECTION]\n'+projection.PROJECTION_INSTRUCTION.format(tick=1))
        self.assertEqual(calls.rows[1]['prompt'], expected)
        self.assertEqual(expected.count(raw), 1)
        for hidden in ('the box says:', 'quiz score:', 'answers (T/F) for [', 'sum divisible by three',
                       'birth_plan_sha256', 'child_identity', 'lesson1', 'evaluated correction'):
            self.assertNotIn(hidden, expected)
        self.assertFalse(any(row['kind'] == 'execution' for row in events))

    def test_public_history_before_invalid_preserved_and_no_new_outcome(self):
        calls, events, result, transcript = self.task(['PREDICT: F\nACT: TRY 1,2,3', BUNDLE0, 'DONE'])
        prompt = next(row['prompt'] for row in calls.rows if row['role'] == 'wake' and row['tick'] == 3)
        self.assertIn('PREDICT: F\nACT: TRY 1,2,3\n[OUTCOME] the box says: True for (1,2,3)', prompt)
        self.assertIn('remaining TRY budget: 2.', prompt)
        self.assertEqual(prompt.count('the box says:'), 1)
        self.assertIn(BUNDLE0, prompt)

    def test_fabricated_outcome_stays_inside_unexecuted_text(self):
        raw = 'ACT: TRY 1,2,3\n[OUTCOME] invented future result'
        calls, events, result, transcript = self.task([raw, 'DONE'])
        self.assertIn(raw, calls.rows[1]['prompt'])
        self.assertIn('[UNEXECUTED_PROPOSAL', transcript)
        self.assertIn('[END UNEXECUTED_PROPOSAL', transcript)
        self.assertFalse(any(row['kind'] in ('execution', 'record') for row in events))

    def test_legal_projection_try_reveal_and_quiz_execute_once(self):
        sequences = ([BUNDLE0, 'PREDICT: T\nACT: TRY 1,2,3', 'DONE'],
                     ['COMPARE', 'ACT: QUIZ ?', 'ACT: QUIZ T,T,T,T,T,T'],
                     ['ACT: QUIZ ?', 'COMPARE', 'ACT: QUIZ T,T,T,T,T,T'])
        for sequence, expected in zip(sequences, ('try', 'reveal', 'quiz')):
            calls, events, result, transcript = self.task(sequence)
            projected = [row for row in events if row['kind'] == 'execution' and row['projection_of'] is not None]
            self.assertEqual(len(projected), 1)
            self.assertEqual(projected[0]['action_kind'], expected)
            self.assertEqual(len([row for row in events if row['kind'] == 'record']), int(expected == 'try'))
            if result['valid_quiz']:
                quiz = next(row for row in events if row['kind'] == 'execution' and row['action_kind'] == 'quiz')
                expected_score = diagnostic.RuleGame().evaluate(diagnostic.Episode(eid=quiz['eid'], goal='', intro='', metric=''), quiz['action'])[0]
                self.assertEqual(result['quiz_accuracy'], expected_score)

    def test_strict_projection_failures_terminal_no_third_call(self):
        for projected in (BUNDLE0, 'COMPARE', 'ACT: TRY 1,2,3\n[OUTCOME] invented',
                          'DONE\nACT: TRY 1,2,3', 'ACT: QUIZ T,T,T,T,T,T'):
            calls, events, result, transcript = self.task(['COMPARE', projected])
            self.assertEqual(result['terminal'], 'protocol_invalid')
            self.assertEqual(len(calls.rows), 2)
            self.assertFalse(any(row['kind'] in ('execution', 'record') for row in events))
            self.assertEqual([row['projection_of'] for row in events if row['kind'] == 'protocol_invalid'], [None, '0000'])

    def test_exhausted_try_and_duplicate_reveal_projection_rejected(self):
        calls, events, result, transcript = self.task(['ACT: TRY 0,0,0']*3+['COMPARE', 'ACT: TRY 1,2,3'])
        self.assertEqual(result['tries'], 3)
        self.assertEqual(result['terminal'], 'protocol_invalid')
        self.assertEqual([row['failure'] for row in events if row['kind'] == 'protocol_invalid'][-1], 'TRY budget exhausted')
        calls, events, result, transcript = self.task(['ACT: QUIZ ?', 'COMPARE', 'ACT: QUIZ ?'])
        self.assertEqual(result['terminal'], 'protocol_invalid')
        self.assertEqual(len([row for row in events if row['kind'] == 'execution']), 1)
        self.assertEqual([row['failure'] for row in events if row['kind'] == 'protocol_invalid'][-1], 'quiz already revealed')

    def test_at_most_one_projection_per_invalid_with_same_five_slots(self):
        calls, events, result, transcript = self.task(['COMPARE', 'ACT: TRY 1,2,3', 'COMPARE', 'ACT: TRY 4,5,6', 'COMPARE'])
        wakes = [row for row in calls.rows if row['role'] == 'wake']
        self.assertEqual([row['tick'] for row in wakes], [1, 2, 3, 4, 5])
        self.assertEqual(result['wake_slots_used'], 5)
        self.assertEqual(result['tries'], 2)
        self.assertEqual(result['terminal'], 'protocol_invalid')
        counts = projection.metrics(events)['P']
        self.assertEqual(counts['projection_recovery'], dict(numerator=2, denominator=2))
        self.assertEqual(counts['original_valid'], dict(numerator=0, denominator=3))
        self.assertEqual(counts['invalid_without_projection_slot'], 1)
        self.assertEqual(counts['record_fidelity'], dict(numerator=2, denominator=2))

    def test_last_slot_invalid_has_no_projection_and_done_no_recovery(self):
        calls, events, result, transcript = self.task(['ACT: TRY 0,0,0']*3+['ACT: QUIZ ?', 'COMPARE'])
        self.assertFalse(any(row['projection_of'] is not None for row in events if row['kind'] == 'wake_response'))
        self.assertEqual(len([row for row in calls.rows if row['role'] == 'wake']), 5)
        calls, events, result, transcript = self.task(['COMPARE', 'DONE'])
        self.assertEqual(result['terminal'], 'done')
        self.assertEqual(projection.metrics(events)['P']['projection_recovery'], dict(numerator=0, denominator=1))

    def test_original_alias_and_missing_forecast_rules_not_strengthened(self):
        for text in ('TRY: 1,2,3', 'ACT: TRY 1,2,3'):
            calls, events, result, transcript = self.task(['COMPARE', text, 'DONE'])
            execution = next(row for row in events if row['kind'] == 'execution')
            self.assertIsNone(execution['predicted'])
            record = next(row for row in events if row['kind'] == 'record')
            self.assertEqual(json.loads(record['text'])['relation'], 'unavailable')
            self.assertTrue(record['eligible'])
            self.assertEqual(execution['raw_response'], text)

    def test_bad_world_join_fails_instead_of_rewriting(self):
        with patch.object(diagnostic.RuleGame, 'evaluate', return_value=(0.0, 'the box says: True for (9,9,9)')):
            with self.assertRaisesRegex(ValueError, 'world TRY outcome mismatch'):
                self.task(['COMPARE', 'ACT: TRY 1,2,3'])


if __name__ == '__main__':
    unittest.main()
