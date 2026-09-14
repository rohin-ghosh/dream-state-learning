"""Synthetic CPU capture/replay checks; not model evidence."""

from copy import deepcopy
import hashlib
import subprocess
import sys
import unittest
from unittest.mock import patch

from organism_v6 import experienced_event_self_critique as lesson
from tests.test_experienced_event_two_hop import exposed_child, generation


def synthetic_actor(collections):
    bound = lesson.rich.runtime(0)
    cases = [bound['build_cases'](collection)['cases'] for collection in collections]

    def generate(messages, *, role, world_index, task_index, **unused):
        if role == 'intervention':
            return generation('I will compare the observed edges against the requested goal.', messages)
        index = sum(message['role'] == 'assistant' for message in messages)
        command = cases[world_index][task_index]['plan'][index]['command']
        return generation('RATIONALE\nI expect the next public observation to resolve this step.\nACTION\n'
                          + command, messages)
    return generate


class SelfCritiqueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collections = [lesson.rich.collect_world(world, exposed_child)
                           for world in lesson.rich.build_worlds(0)['TRAIN']]
        cls.initial = lesson.collect_initial(cls.collections, synthetic_actor(cls.collections))

    def test_pure_import(self):
        script = '''import builtins
original = builtins.__import__
def guarded(name, *args, **kwargs):
    assert name.split('.')[0] not in ('torch', 'transformers', 'tokenizers', 'peft')
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from organism_v6 import experienced_event_self_critique
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fixed_sources_six_turns_and_pairs_no_coach(self):
        with patch.object(lesson.rich, '_coach', side_effect=AssertionError('no teacher')):
            result = lesson.replay_initial(self.initial)
        self.assertEqual(result['model_calls'], 96)
        self.assertEqual(result['attempted_tasks'], 16)
        self.assertEqual(result['pair_denominator'], 8)
        self.assertEqual(len(result['candidate_rows']), 96)
        self.assertEqual(sum(item['paired']['correct'] for item in result['summaries']), 8)
        self.assertFalse(result['fit_ready'])
        self.assertFalse(result['semantic_pass'])
        for capture in result['captures']:
            self.assertNotIn(lesson.rich.PARENT_GUIDANCE, str(capture['messages']))
            for message in capture['messages']:
                if message['role'] == 'assistant':
                    self.assertNotIn('RATIONALE', message['content'])

    def test_paired_input_identity_and_actual_interventions(self):
        arms = [lesson.collect_arm(arm, self.initial, synthetic_actor(self.collections)) for arm in lesson.ARMS]
        for document in arms:
            self.assertEqual(document, lesson.replay_arm(document, self.initial))
            self.assertEqual(document['model_calls'], 112)
            self.assertEqual(len(document['candidate_rows']), 96)
            self.assertFalse(document['fit_ready'])
        interventions = [[capture for capture in document['captures'] if capture['role'] == 'intervention']
                         for document in arms]
        for left, right in zip(*interventions):
            self.assertEqual(left['messages'][0], right['messages'][0])
            self.assertEqual(left['messages'][1]['content'].rsplit('\n\n', 1)[0],
                             right['messages'][1]['content'].rsplit('\n\n', 1)[0])
            self.assertEqual(left['episode_id'], right['episode_id'])
            self.assertEqual(left['source_sha256'], right['source_sha256'])
        self.assertIn('FALLIBLE CHILD ADVICE', arms[0]['captures'][1]['messages'][0]['content'])

    def test_malformed_wrong_goal_and_callback_errors_preserved(self):
        malformed = lambda messages, **metadata: generation('not an envelope', messages)
        failed = lesson.collect_initial(self.collections, malformed)
        self.assertEqual(failed['model_calls'], 16)
        self.assertEqual(len(failed['episodes']), 16)
        self.assertEqual(failed['candidate_rows'], [])
        self.assertEqual(lesson.replay_initial(failed), failed)
        actor = synthetic_actor(self.collections)

        def wrong(messages, **metadata):
            metadata['task_index'] = (metadata['task_index'] + 2) % 4
            return actor(messages, **metadata)

        wrong_document = lesson.collect_initial(self.collections, wrong)
        self.assertEqual(sum(item['individual']['correct'] for item in wrong_document['summaries']), 0)
        self.assertEqual(wrong_document['candidate_rows'], [])
        self.assertEqual(lesson.replay_initial(wrong_document), wrong_document)

        def missing(messages, **metadata):
            if metadata['role'] == 'intervention':
                raise RuntimeError('actual child error')
            return actor(messages, **metadata)

        document = lesson.collect_arm(lesson.ARMS[0], failed, missing)
        self.assertEqual(sum(capture['error'] is not None for capture in document['captures']), 16)
        self.assertTrue(all(entry['intervention_error'] for entry in document['episodes']))
        self.assertEqual(lesson.replay_arm(document, failed), document)
        self.assertIn('[CHILD ADVICE UNAVAILABLE]', document['captures'][1]['messages'][0]['content'])

    def test_probe_reordering_incomplete_and_old_ids_rejected(self):
        probe = lesson.rich.collect_world(lesson.rich.build_worlds(0)['PROBE'][0], exposed_child)
        for collections in (self.collections[::-1], self.collections[:3], self.collections[:3] + [probe]):
            with self.assertRaises(ValueError):
                lesson.collect_initial(collections, synthetic_actor(self.collections))
        failed = lesson.rich.collect_world(lesson.rich.build_worlds(0)['TRAIN'][0],
                                          lambda messages: generation('bad', messages))
        with self.assertRaisesRegex(ValueError, 'complete_original_train_sources'):
            lesson.collect_initial([failed] + self.collections[1:], synthetic_actor(self.collections))
        old_id = next(iter(lesson.rich.identifiers(self.collections[0]['world'])))
        with self.assertRaises(ValueError):
            lesson.collect_initial(self.collections, synthetic_actor(self.collections), old_ids=[old_id])

    def test_tampered_capture_candidate_and_shared_source_rejected(self):
        for field in ('messages', 'response'):
            document = deepcopy(self.initial)
            if field == 'messages':
                document['captures'][0][field][0]['content'] += ' changed'
            else:
                document['captures'][0][field]['raw'] += ' changed'
            with self.assertRaises(ValueError):
                lesson.replay_initial(document)
        document = deepcopy(self.initial)
        document['candidate_rows'][0]['assistant'] = 'fabricated'
        with self.assertRaises(ValueError):
            lesson.replay_initial(document)

    def test_unseen_rationale_is_not_execution_failure_or_semantic_pass(self):
        actor = synthetic_actor(self.collections)

        def hallucinated(messages, **metadata):
            response = actor(messages, **metadata)
            response['raw'] = response['raw'].replace('I expect', 'N_AAAAAAAAAA exists. I expect')
            return response

        result = lesson.collect_initial(self.collections, hallucinated)
        self.assertEqual(len(result['candidate_rows']), 96)
        self.assertTrue(result['episodes'][0]['content_findings'][0]['unseen_public_identifiers'])
        self.assertFalse(result['episodes'][0]['content_findings'][0]['semantic_pass'])

    def test_explicit_prefixes_preserve_original_action_and_unicode_spans(self):
        command = 'READ EVENT ' + self.collections[0]['world']['edges'][0]['event'] + '\n\n'
        rationale = 'A café observation; the next outcome is a prediction.'
        for prefix in ('RATIONALE\n', 'RATIONALE: '):
            raw = prefix + rationale + '\nACTION\n' + command
            projected = lesson.project_action(raw)
            self.assertEqual({key: value for key, value in projected.items() if key != 'format'},
                             lesson.rich.project_action(raw, allow_colon_header=True))
            self.assertEqual(projected['action'], command)
            self.assertEqual(projected['rationale'], rationale)
            self.assertEqual(raw[slice(*projected['action_span'])], command)
            self.assertEqual(raw.encode()[slice(*projected['action_byte_span'])], command.encode())
            self.assertEqual(raw[slice(*projected['rationale_span'])], rationale)
            self.assertEqual(raw.encode()[slice(*projected['rationale_byte_span'])], rationale.encode())
            self.assertEqual(projected['raw_sha256'], hashlib.sha256(raw.encode()).hexdigest())
        self.assertEqual(lesson.project_action(command)['action'], command)
        with self.assertRaises(ValueError):
            lesson.rich.project_action('RATIONALE: ' + rationale + '\nACTION\n' + command)
        with self.assertRaises(ValueError):
            lesson.rich.project_action(command)

    def test_no_permissive_heading_or_command_scanning(self):
        command = 'READ EVENT ' + self.collections[0]['world']['edges'][0]['event']
        raw = 'RATIONALE: A public observation.\nACTION\n' + command
        invalid = (raw.replace('RATIONALE: ', 'RATIONALE:'),
                   raw.replace('RATIONALE: ', 'Reasoning: '),
                   ' ' + raw, 'Here is my answer:\n' + raw,
                   raw.replace('\nACTION\n', '\nACTION: '),
                   raw.replace('\n', '\r\n'), raw + '\nACTION\n' + command,
                   raw.replace('A public observation.', ' \n'),
                   raw.replace('A public observation.', 'text\nRATIONALE\nsecond'),
                   raw + '\nROUTE fabricated', ' ' + command, command + '\nmore prose')
        for candidate in invalid:
            with self.subTest(raw=candidate), self.assertRaises(ValueError):
                lesson.project_action(candidate)

    def test_colon_and_plain_capture_lifecycle_remain_outcome_only(self):
        actor = synthetic_actor(self.collections)
        for plain in (False, True):
            def compatible(messages, **metadata):
                response = actor(messages, **metadata)
                if metadata['role'] == 'actor':
                    response['raw'] = (response['raw'].split('\nACTION\n')[1] if plain else
                                       response['raw'].replace('RATIONALE\n', 'RATIONALE: ', 1))
                return response
            initial = lesson.collect_initial(self.collections, compatible)
            self.assertEqual(initial, lesson.replay_initial(initial))
            self.assertEqual(initial['model_calls'], 96)
            self.assertEqual(len(initial['candidate_rows']), 96)
            self.assertEqual(initial['projection_policy'], lesson.PROJECTION_POLICY)
            self.assertEqual(initial['episodes'][0]['content_findings'][0]['rationale_missing'], plain)
            for arm in lesson.ARMS:
                document = lesson.collect_arm(arm, initial, compatible)
                self.assertEqual(document, lesson.replay_arm(document, initial))
                self.assertEqual(document['model_calls'], 112)
                self.assertFalse(document['fit_ready'])
                self.assertFalse(document['semantic_pass'])


if __name__ == '__main__':
    unittest.main()
