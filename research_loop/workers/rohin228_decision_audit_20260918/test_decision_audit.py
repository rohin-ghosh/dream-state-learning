"""Synthetic R184/committed-journal decision-metric regressions only."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

import decision_audit as audit
import source_adapter


FIXTURE_SPEC = importlib.util.spec_from_file_location('r228_prior_fixture', source_adapter.PREVIOUS / 'test_audit.py')
FIXTURE = importlib.util.module_from_spec(FIXTURE_SPEC)
FIXTURE_SPEC.loader.exec_module(FIXTURE)


def cycle(journal, number, think, act):
    segment = number * 2
    journal.stage('THINK', segment, think)
    journal.transition(segment)
    response = journal.stage('ACT', segment + 1, act)
    journal.action_receipt(response, segment + 1, False)
    journal.sleep(number)
    return response


class DeclarationTests(unittest.TestCase):
    def test_continue_branch_stop_explicit(self):
        examples = [('I will continue exploring.', 'CONTINUE'),
                    ('I will switch to Scene 2.', 'BRANCH'),
                    ('I will try a different approach.', 'BRANCH'),
                    ('I will stop here.', 'STOP'), ('Decision: branch.', 'BRANCH')]
        for text, expected in examples:
            with self.subTest(text=text):
                self.assertEqual(audit.declarations(text)['decision'], expected)

    def test_conflicting_same_response_is_ambiguous(self):
        result = audit.declarations('I will continue. I will stop.')
        self.assertEqual(result['decision'], 'AMBIGUOUS')
        self.assertEqual(set(result['action_candidates']), {'CONTINUE', 'STOP'})

    def test_fences_quotes_and_reported_character_are_not_self_declarations(self):
        examples = ['```text\nI will stop.\n```', '> I will stop.',
                    'Mara said, "I will stop."', "Mara said, 'I will stop.'",
                    'Mara said, ‘I will stop.’', 'Mara said I will stop.']
        for text in examples:
            with self.subTest(text=text):
                self.assertEqual(audit.declarations(text)['decision'], 'UNKNOWN')

    def test_questions_negation_and_conditions_do_not_force_choice(self):
        examples = ['Should I continue?', 'I will stop?', 'I will not stop.',
                    'I will stop if nothing works.', 'If I find nothing, I will stop.',
                    'Maybe I will stop.', 'I will stop unless another clue appears.']
        for text in examples:
            with self.subTest(text=text):
                self.assertEqual(audit.declarations(text)['decision'], 'UNKNOWN')

    def test_stop_using_or_saying_is_not_task_stop(self):
        self.assertEqual(audit.declarations('I will stop using that phrase.')['decision'], 'UNKNOWN')

    def test_question_and_separate_real_declaration(self):
        result = audit.declarations('Which scene is next? I will continue exploring.')
        self.assertEqual(result['decision'], 'CONTINUE')
        self.assertEqual(result['question_units'], 1)

    def test_runtime_think_continuation_is_not_task_decision(self):
        self.assertEqual(audit.declarations('Continue thinking: I will continue exploring.')['decision'], 'UNKNOWN')

    def test_new_draft_alone_is_not_new_direction(self):
        self.assertEqual(audit.declarations('I will write a new draft.')['decision'], 'UNKNOWN')

    def test_exhaustion_is_claim_not_automatic_stop(self):
        result = audit.declarations('I have no more ideas.')
        self.assertEqual(result['decision'], 'UNKNOWN')
        self.assertEqual([entry['kind'] for entry in result['claims']], ['EXHAUSTION'])

    def test_exhaustion_question_and_tiredness_not_exhausted_object(self):
        self.assertEqual(audit.declarations('There is nothing else to try?')['claims'], [])
        self.assertEqual(audit.declarations('I am exhausted.')['claims'], [])

    def test_offsets_bind_exact_original_span_after_masking(self):
        text = 'Mara said "I will stop."\nI will continue exploring.'
        for claim in audit.declarations(text)['claims']:
            original = text[claim['start']:claim['end']]
            self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), claim['span_sha256'])

    def test_unsupported_language_and_long_text_are_unknown(self):
        self.assertEqual(audit.declarations('我会继续探索。')['decision'], 'UNKNOWN')
        self.assertEqual(audit.declarations('x' * 65537)['reason'], 'scan_bound_exceeded')


class ObjectTests(unittest.TestCase):
    def test_numeric_scene_and_explicit_object_are_hashed(self):
        markers = audit.object_metadata('Scene 2\nObject: PRIVATE_OBJECT\nAn actual caption.')
        self.assertEqual({entry['kind'] for entry in markers}, {'scene', 'object'})
        self.assertNotIn('PRIVATE_OBJECT', json.dumps(markers))

    def test_structured_scene_selection_not_environment_confirmation(self):
        markers = audit.object_metadata('{"actions":[{"contest_id":"PRIVATE_SCENE","text":"PRIVATE_CAPTION"}]}')
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]['kind'], 'scene')
        self.assertNotIn('PRIVATE_SCENE', json.dumps(markers))
        self.assertNotIn('PRIVATE_CAPTION', json.dumps(markers))

    def test_multi_scene_selection_remains_ambiguous(self):
        previous = audit.object_metadata('Scene 1')
        current = audit.object_metadata('Scene 2\nScene 3')
        self.assertEqual(audit.compare_objects(previous, current)['inferred_decision'], 'AMBIGUOUS')

    def test_no_metadata_cannot_be_inferred_from_new_bytes(self):
        self.assertEqual(audit.compare_objects([], [])['inferred_decision'], 'UNKNOWN')

    def test_same_scene_changed_direction_is_observed_branch_metadata(self):
        previous = audit.object_metadata('Scene 1\nDirection: old')
        current = audit.object_metadata('Scene 1\nDirection: new')
        transition = audit.compare_objects(previous, current)
        self.assertEqual(transition['inferred_decision'], 'BRANCH')
        self.assertEqual(transition['dimensions']['scene']['relation'], 'SAME_LABEL')


class CycleTests(unittest.TestCase):
    def analyze(self, journal):
        return audit.analyze(journal.evidence(), 'SYNTHETIC')

    def test_source_bound_self_declared_and_inferred_separate(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I will continue.', 'Scene 1\nFirst wording.')
        cycle(journal, 2, 'I will switch to Scene 2.', 'Scene 2\nSecond wording.')
        report = self.analyze(journal)
        latest = report['cycles'][-1]
        self.assertEqual(latest['self_declared_decision'], 'BRANCH')
        self.assertEqual(latest['inferred_transition']['inferred_decision'], 'BRANCH')
        self.assertEqual(len(latest['normal_think_act_pairs']), 1)

    def test_stops_changes_requires_stop_then_observed_label_change(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I will stop here.', 'Scene 1\nFirst wording.')
        cycle(journal, 2, 'I will switch to Scene 2.', 'Scene 2\nSecond wording.')
        latest = self.analyze(journal)['cycles'][-1]
        self.assertIn('STOPS_CHANGES', [entry['label'] for entry in latest['behavior_observations']])

    def test_stops_repeats_is_exact_bytes_after_declared_stop(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I will stop here.', 'Scene 1\nSame wording.')
        cycle(journal, 2, 'I will continue.', 'Scene 1\nSame wording.')
        latest = self.analyze(journal)['cycles'][-1]
        self.assertEqual(latest['act_byte_relation'], 'EXACT_REPEAT')
        self.assertIn('STOPS_REPEATS', [entry['label'] for entry in latest['behavior_observations']])

    def test_repeat_without_stop_is_not_stops_repeats(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I will continue.', 'Scene 1\nSame wording.')
        cycle(journal, 2, 'I will continue.', 'Scene 1\nSame wording.')
        latest = self.analyze(journal)['cycles'][-1]
        self.assertNotIn('STOPS_REPEATS', [entry['label'] for entry in latest['behavior_observations']])

    def test_different_bytes_not_discovery(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I will continue.', 'Scene 1\nFirst wording.')
        cycle(journal, 2, 'I will continue.', 'Scene 1\nChanged wording.')
        latest = self.analyze(journal)['cycles'][-1]
        self.assertEqual(latest['act_byte_relation'], 'DIFFERENT_BYTES_NOT_NOVELTY')
        self.assertNotIn('KEEPS_DISCOVERING', [entry['label'] for entry in latest['behavior_observations']])

    def test_discovery_label_is_explicitly_self_declared(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I found a new idea. I will continue.', 'Scene 1\nA proposal.')
        latest = self.analyze(journal)['cycles'][0]
        observation = next(entry for entry in latest['behavior_observations'] if entry['label'] == 'KEEPS_DISCOVERING')
        self.assertIn('NOT_VERIFIED', observation['basis'])
        self.assertEqual(latest['verified_discovery'], 'UNKNOWN_NO_ENVIRONMENT_NOVELTY_PROOF')

    def test_declared_exhaustion_and_inferred_outcome_are_independent(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I have exhausted this scene.', 'Scene 1\nA proposal.')
        latest = self.analyze(journal)['cycles'][0]
        self.assertTrue(latest['declared_exhaustion'])
        self.assertEqual(latest['self_declared_decision'], 'UNKNOWN')

    def test_no_act_is_not_inferred_stop(self):
        journal = FIXTURE.Journal()
        journal.stage('THINK', 1, 'Which direction should I try?')
        journal.transition(1)
        report = self.analyze(journal)
        latest = report['cycles'][0]
        self.assertEqual(latest['self_declared_decision'], 'UNKNOWN')
        self.assertEqual(latest['inferred_transition']['inferred_decision'], 'UNKNOWN')
        self.assertFalse(report['absence_of_act_means_stop'])
        self.assertEqual(report['counts_by_status']['OPEN']['UNKNOWN'], 1)

    def test_actual_later_declaration_preserves_earlier_history(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I will continue.', 'I will stop here.')
        latest = self.analyze(journal)['cycles'][0]
        self.assertEqual(latest['self_declared_decision'], 'STOP')
        self.assertEqual([item['decision'] for item in latest['declaration_history']], ['CONTINUE', 'STOP'])

    def test_console_act_cannot_override_normal_cycle_decision(self):
        journal = FIXTURE.Journal()
        response = cycle(journal, 1, 'I will continue.', 'I will stop here.')
        journal.add('R205_CONSOLE_REPLY', dict(source_sha256=response['source_sha256'], segment=3))
        latest = self.analyze(journal)['cycles'][0]
        self.assertEqual(latest['self_declared_decision'], 'CONTINUE')
        self.assertEqual(latest['act_responses'], 0)

    def test_bad_source_identity_not_analyzed(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I will stop.', 'Scene 1')
        stage = next(event for event in journal.events if event['kind'] == 'R184_STAGE')
        stage['document']['source_sha256'] = 'd' * 64
        report = self.analyze(journal)
        self.assertEqual(report['cycles'][0]['self_declared_decision'], 'UNKNOWN')
        self.assertTrue(report['uncertainties'])

    def test_no_private_text_exported_or_source_mutation(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I will continue. PRIVATE_THINK', 'Object: PRIVATE_OBJECT\nPRIVATE_ACT')
        evidence = journal.evidence()
        before = copy.deepcopy(evidence)
        report = audit.analyze(evidence, 'SYNTHETIC')
        serialized = json.dumps(report)
        for private in ('PRIVATE_THINK', 'PRIVATE_OBJECT', 'PRIVATE_ACT'):
            self.assertNotIn(private, serialized)
        self.assertEqual(evidence, before)
        self.assertFalse(report['semantic_exclusions'])
        self.assertFalse(report['learner_or_parent_changes'])
        self.assertFalse(report['questions_are_failures'])


if __name__ == '__main__':
    unittest.main()
