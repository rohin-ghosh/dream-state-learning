"""Synthetic journal-schema tests; no transport, models or learner imports."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location('r227_audit', Path(__file__).with_name('audit.py'))
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class Journal:
    def __init__(self):
        self.events = []

    def add(self, kind, document=None, **extra):
        index = len(self.events) + 1
        event = dict(record_index=index, record_sha256=AUDIT.digest([kind, index, document, extra]),
                     kind=kind, envelope_verified=True, **extra)
        if document is not None:
            event['document'] = document
        self.events.append(event)
        return event

    def stage(self, stage, segment, text, messages=None, committed=True):
        request = self.add('REQUEST', dict(segment=segment, messages=messages or []))
        document = dict(request_sha256=AUDIT.digest(request['document']),
                        response=dict(raw=text), finished_unix=1000.0 + segment)
        source = AUDIT.digest(document)
        response = self.add('RESPONSE', document, source_sha256=source)
        if committed:
            self.add('COMMITTED', source_sha256=source, segment=segment,
                     target_sha256=AUDIT.text_hash(text), committed_row_verified=True)
        self.add('R184_STAGE', dict(stage=stage, segment=segment, source_sha256=source, trial_id='fixture'))
        return response

    def transition(self, segment, count=1):
        return self.add('R184_TRANSITION', dict(from_stage='THINK', to_stage='ACT', segment=segment,
                                               think_segments_used=count))

    def action_receipt(self, response, segment, executed=True):
        return self.add('R184_ACT', dict(segment=segment, source_sha256=response['source_sha256'],
                                        origin=dict(record_index=response['record_index'], record_sha256=response['record_sha256']),
                                        outcome=dict(executed=executed, result_sha256='a' * 64)))

    def sleep(self, cycle=1, completed=True):
        self.add('SLEEP_REQUEST', dict(cycle=cycle))
        if completed:
            self.add('SLEEP_COMPLETE', dict(cycle=cycle))

    def evidence(self):
        return dict(events=self.events, anchor=dict(cycle=0, index=0, sha256='0' * 64),
                    head=dict(index=len(self.events), sha256='f' * 64), observed_unix=2000.0)


def fixture(think='I will calculate.', act='2 + 2 = 4.', executed=True):
    journal = Journal()
    journal.stage('THINK', 0, think)
    journal.transition(0)
    response = journal.stage('ACT', 1, act)
    journal.action_receipt(response, 1, executed)
    journal.sleep()
    return journal


class AuditTests(unittest.TestCase):
    def analyze(self, journal):
        return AUDIT.analyze(journal.evidence(), 'SYNTHETIC')

    def test_exact_source_stage_candidate_cycle_pair(self):
        report = self.analyze(fixture())
        self.assertEqual(len(report['pairs']), 1)
        self.assertEqual(report['pairs'][0]['think_segments'], [0])
        self.assertEqual(report['pairs'][0]['act_segment'], 1)
        self.assertEqual(report['cycles'][0]['executions_recorded'], 1)
        self.assertEqual(report['cycles'][0]['act_math_or_byte_surface_candidates'], 1)

    def test_two_thinks_are_one_opportunity(self):
        journal = Journal()
        journal.stage('THINK', 0, 'I will examine the graph.')
        journal.stage('THINK', 1, 'Which edge matters?')
        journal.transition(1, 2)
        response = journal.stage('ACT', 2, 'Here is the construction.')
        journal.action_receipt(response, 2, False)
        journal.sleep()
        report = self.analyze(journal)
        self.assertEqual(report['cycles'][0]['think_responses'], 2)
        self.assertEqual(report['cycles'][0]['paired_opportunities'], 1)

    def test_partial_generation_never_counted(self):
        journal = Journal()
        journal.add('GENERATION_PARTIAL', dict(raw='I will do it.'))
        journal.stage('THINK', 0, 'Uncommitted response.', committed=False)
        report = self.analyze(journal)
        self.assertEqual(report['rows'], [])
        self.assertEqual(report['pairs'], [])

    def test_question_is_not_failure(self):
        report = self.analyze(fixture(act='Fable, which premise should I check?', executed=False))
        self.assertEqual(report['cycles'][0]['act_questions'], 1)
        self.assertFalse(report['questions_are_failures'])
        self.assertEqual(report['pairs'][0]['semantic_alignment'], 'UNCERTAIN_NOT_SCORED')

    def test_print_promise_is_code_not_execution_or_calculation(self):
        report = self.analyze(fixture(act='```python\nprint("I will calculate 2 + 2 = 4.")\n```', executed=None))
        cycle = report['cycles'][0]
        self.assertEqual(cycle['act_code_submissions'], 1)
        self.assertEqual(cycle['act_math_or_byte_surface_candidates'], 0)
        self.assertEqual(cycle['executions_recorded'], 0)
        self.assertEqual(cycle['executions_unknown'], 1)

    def test_numeric_code_is_candidate_not_verified_fulfillment(self):
        report = self.analyze(fixture(act='```python\nprint(2 + 2)\n```'))
        self.assertEqual(report['cycles'][0]['act_math_or_byte_surface_candidates'], 1)
        self.assertEqual(report['cycles'][0]['task_fulfillment_uncertain'], 1)

    def test_console_act_is_not_normal_work_pair(self):
        journal = fixture()
        response = next(event for event in journal.events if event['kind'] == 'RESPONSE' and event['document']['response']['raw'] == '2 + 2 = 4.')
        journal.add('R205_CONSOLE_REPLY', dict(source_sha256=response['source_sha256'], segment=1))
        report = self.analyze(journal)
        self.assertEqual(report['cycles'][0]['console_act_responses'], 1)
        self.assertEqual(report['cycles'][0]['act_responses'], 0)
        self.assertEqual(report['pairs'], [])

    def test_no_cross_cycle_pairing(self):
        journal = Journal()
        journal.stage('THINK', 0, 'I will calculate.')
        journal.transition(0)
        journal.sleep(1)
        response = journal.stage('ACT', 1, '2 + 2 = 4.')
        journal.action_receipt(response, 1)
        journal.sleep(2)
        self.assertEqual(self.analyze(journal)['pairs'], [])

    def test_same_segment_without_same_source_is_rejected(self):
        journal = fixture()
        stage = next(event for event in journal.events if event['kind'] == 'R184_STAGE')
        stage['document']['source_sha256'] = 'e' * 64
        report = self.analyze(journal)
        self.assertEqual(report['pairs'], [])

    def test_segment_mismatch_is_not_paired(self):
        journal = fixture()
        stage = next(event for event in journal.events if event['kind'] == 'R184_STAGE')
        stage['document']['segment'] = 99
        self.assertEqual(self.analyze(journal)['pairs'], [])

    def test_wrong_execution_origin_is_unknown(self):
        journal = fixture()
        event = next(event for event in journal.events if event['kind'] == 'R184_ACT')
        event['document']['origin']['record_sha256'] = 'b' * 64
        report = self.analyze(journal)
        self.assertEqual(report['cycles'][0]['executions_recorded'], 0)
        self.assertEqual(report['cycles'][0]['executions_unknown'], 1)

    def test_missing_transition_cannot_be_inferred_from_adjacency(self):
        journal = fixture()
        journal.events = [event for event in journal.events if event['kind'] != 'R184_TRANSITION']
        journal.events[-1]['record_index'] = 12
        evidence = journal.evidence()
        evidence['head']['index'] = 12
        self.assertEqual(AUDIT.analyze(evidence, 'SYNTHETIC')['pairs'], [])

    def test_pending_act_is_explicit(self):
        journal = Journal()
        journal.stage('THINK', 0, 'I will calculate.')
        journal.transition(0)
        report = self.analyze(journal)
        self.assertIn('act_pending_at_observation_cut', [entry['reason'] for entry in report['uncertainties']])
        self.assertEqual(report['cycles'][0]['status'], 'OPEN')

    def test_parent_publication_is_not_rendering_or_uptake(self):
        journal = Journal()
        journal.add('INBOX', dict(message=dict(actor='parent', text='PRIVATE_TASK Byte graph.'), source_sha256='b' * 64))
        journal.stage('THINK', 0, 'I will try.')
        report = self.analyze(journal)
        self.assertEqual(report['parent_delivery'][0]['exact_rendered_to_committed_response'], [])

    def test_parent_exact_rendering_stays_uncertain_and_private(self):
        journal = Journal()
        text = 'PRIVATE_TASK Byte graph.'
        journal.add('INBOX', dict(message=dict(actor='parent', text=text), source_sha256='b' * 64))
        journal.stage('THINK', 0, 'PRIVATE_CHILD I will try.', messages=[dict(role='user', content='Parent: ' + text)])
        report = self.analyze(journal)
        self.assertEqual(len(report['parent_delivery'][0]['exact_rendered_to_committed_response']), 1)
        serialized = json.dumps(report)
        self.assertNotIn('PRIVATE_TASK', serialized)
        self.assertNotIn('PRIVATE_CHILD', serialized)
        self.assertFalse(report['semantic_exclusions'])

    def test_assistant_echo_is_not_parent_rendering(self):
        journal = Journal()
        journal.add('INBOX', dict(message=dict(actor='parent', text='Unique prompt.')))
        journal.stage('THINK', 0, 'I will try.', messages=[dict(role='assistant', content='Unique prompt.')])
        self.assertEqual(self.analyze(journal)['parent_delivery'][0]['exact_rendered_to_committed_response'], [])

    def test_input_is_not_mutated(self):
        evidence = fixture().evidence()
        before = copy.deepcopy(evidence)
        AUDIT.analyze(evidence, 'SYNTHETIC')
        self.assertEqual(evidence, before)

    def test_ambiguous_repeated_cycle_rejected(self):
        journal = fixture()
        journal.add('SLEEP_REQUEST', dict(cycle=1))
        with self.assertRaisesRegex(ValueError, 'ambiguous_repeated_sleep_cycle'):
            self.analyze(journal)

    def test_unverified_projection_rejected(self):
        journal = fixture()
        journal.events[0]['envelope_verified'] = False
        with self.assertRaisesRegex(ValueError, 'unverified_event_projection'):
            self.analyze(journal)

    def test_conflicting_record_identity_rejected(self):
        journal = fixture()
        duplicate = copy.deepcopy(journal.events[0])
        duplicate['record_sha256'] = 'b' * 64
        journal.events.append(duplicate)
        with self.assertRaisesRegex(ValueError, 'conflicting_record_identity'):
            self.analyze(journal)

    def test_code_question_is_not_a_natural_question_metric(self):
        self.assertFalse(AUDIT.text_features('```python\nprint("Fable, why?")\n```')['question_candidate'])

    def test_story_candidate_not_completion_claim(self):
        self.assertEqual(AUDIT.text_features('I will write a three paragraph story about Byte.')['byte_story_paragraph_candidates'], 0)
        text = 'Byte walked into the forest and found a small wooden door beside a river.'
        self.assertEqual(AUDIT.text_features(text)['byte_story_paragraph_candidates'], 1)

    def test_no_private_head_fields_exported(self):
        evidence = fixture().evidence()
        evidence['head']['private_transcript'] = 'SECRET_HEAD_TEXT'
        self.assertNotIn('SECRET_HEAD_TEXT', json.dumps(AUDIT.analyze(evidence, 'SYNTHETIC')))

    def test_raw_target_hash_mismatch_rejected(self):
        journal = fixture()
        commit = next(event for event in journal.events if event['kind'] == 'COMMITTED')
        commit['target_sha256'] = 'c' * 64
        self.assertEqual(self.analyze(journal)['pairs'], [])

    def test_cross_trial_pair_is_uncertain(self):
        journal = fixture()
        stage = next(event for event in journal.events if event['kind'] == 'R184_STAGE' and event['document']['stage'] == 'ACT')
        stage['document']['trial_id'] = 'different_fixture'
        report = self.analyze(journal)
        self.assertEqual(report['pairs'], [])
        self.assertEqual(report['cycles'][0]['unpaired_acts'], 1)

    def test_not_executed_does_not_mean_failed_language_action(self):
        report = self.analyze(fixture(act='Which equation should I examine?', executed=False))
        self.assertEqual(report['cycles'][0]['not_executed_receipts'], 1)
        self.assertEqual(report['cycles'][0]['act_questions'], 1)
        self.assertFalse(report['questions_are_failures'])


class IntentionMetricTests(unittest.TestCase):
    def classify(self, text):
        return AUDIT.intention_act_classification(text)['classification']

    def test_pure_future_act_is_intention_only(self):
        self.assertEqual(self.classify('Intentions: I will write the answer next.'), 'INTENTION_ONLY_HEURISTIC')

    def test_status_print_with_future_action_is_qualified_intention_only(self):
        text = '```python\nprint("The resulting report meets the guidelines.")\n```\nI have printed the status. Now, I will write the report.'
        self.assertEqual(self.classify(text), 'INTENTION_ONLY_HEURISTIC')

    def test_actual_wrong_answer_is_not_intention_only(self):
        self.assertEqual(self.classify("The subset is {'A', 'C', 'E'}. I will check it later."), 'WORK_SURFACE_OBSERVED')

    def test_real_question_wins_over_future_marker(self):
        self.assertEqual(self.classify('I will examine the calculation. Fable, which assumption needs checking?'), 'QUESTION_OBSERVED')

    def test_quoted_question_in_code_is_not_failed_intention(self):
        self.assertEqual(self.classify('```python\nprint("Fable, which assumption?")\n```\nI will wait.'), 'UNKNOWN')

    def test_actual_partial_recall_plus_plan_is_unknown_not_pure_intention(self):
        self.assertEqual(self.classify('Recalled that the story showed communal support. Intentions: I will write a review.'), 'UNKNOWN')

    def test_generic_anticipatory_scaffold_plus_plan_is_qualified(self):
        text = 'Comprehended that Astra might appreciate encouragement.\n\nIntentions: I will write a message.'
        self.assertEqual(self.classify(text), 'INTENTION_ONLY_HEURISTIC')

    def test_nonenglish_statement_is_unknown_not_rejected(self):
        self.assertEqual(self.classify('我将会撰写一段评论。'), 'UNKNOWN')
        self.assertEqual(self.classify('这个例子为什么成立？'), 'QUESTION_OBSERVED')

    def test_unsupported_scaffold_or_memory_command_is_unknown(self):
        text = 'Forget state Draft: The previous message may be irrelevant.\nIntentions: I will write again.'
        self.assertEqual(self.classify(text), 'UNKNOWN')

    def test_literal_draft_with_status_is_not_intention_only(self):
        text = '```python\nprint("We present a proposal for a small library. It contains a public reading room, a workshop and a quiet courtyard. The building uses existing foundations.")\n```\nI will discuss this draft.'
        self.assertEqual(self.classify(text), 'WORK_SURFACE_OBSERVED')

    def test_empty_or_unfinished_act_is_unknown(self):
        for text in ('', '```python\nI will write code'):
            with self.subTest(text=text):
                self.assertEqual(self.classify(text), 'UNKNOWN')

    def test_act_classes_are_exhaustive_and_no_targets_exported(self):
        report = AUDIT.analyze(fixture(act='Intentions: I will write the answer next.').evidence(), 'SYNTHETIC')
        counts = report['cycles'][0]['act_form_counts']
        self.assertEqual(sum(counts.values()), report['cycles'][0]['act_responses'])
        self.assertEqual(counts['INTENTION_ONLY_HEURISTIC'], 1)
        self.assertNotIn('write the answer next', json.dumps(report))


if __name__ == '__main__':
    unittest.main()
