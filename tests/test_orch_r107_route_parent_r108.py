"""Route parenting guards and actual direct-engine return-path regression."""

from contextlib import nullcontext
from copy import deepcopy
import inspect
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest

from gpu.orch_r107_route_parent_r108_engine import Engine
from organism_v6 import orch_r107_route_parent_r108 as policy


class Values:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return Values(self.values[key[1]])
        return Values(self.values) if key == 0 else self.values[key]

    def tolist(self):
        return self.values


def minimal_engine(raw='Reasoning grounded in the public task.\nROUTE port', corrupt=False):
    engine = Engine.__new__(Engine)
    engine.device = 'cpu'
    engine.check = lambda phase: None
    engine.torch = SimpleNamespace(tensor=lambda values, **kwargs:Values(values[0]), long='long',
        ones_like=lambda values: values, inference_mode=nullcontext)
    engine.transformers = SimpleNamespace(GenerationConfig=lambda **kwargs:kwargs)
    engine.tokenizer = SimpleNamespace(apply_chat_template=lambda messages, **kwargs:[11, 12],
        eos_token_id=99, pad_token_id=0, decode=lambda tokens, **kwargs:raw)
    engine.model = SimpleNamespace(named_parameters=lambda:[], parameters=lambda:[], modules=lambda:[],
        generate=lambda **kwargs:Values([0 if corrupt else 11, 12, 13, 99]))
    return engine


class RouteParentTests(unittest.TestCase):
    def setUp(self):
        self.cohort = policy.cohort([], 2)

    def test_independent_lineages_disjoint_from_original_family(self):
        from organism_v6 import orch_r107_route_parent as prior
        seen = policy.identifiers(prior.cohort([]))
        for index in (2, 3, 6):
            fresh = policy.cohort(seen, index)
            self.assertFalse(seen & policy.identifiers(fresh))
            seen.update(policy.identifiers(fresh))
        self.assertEqual(len(set(policy.STYLES.values())), 3)

    def test_separate_twelve_parent_cap_and_old_slots_forbidden(self):
        from gpu.orch_r107_route_parent_r108_run import spend
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in (2, 3, 6):
                for count in range(4):
                    last = spend(root, index, 'PARENT', {})
                with self.assertRaises(ValueError):
                    spend(root, index, 'PARENT', {})
            self.assertEqual(last['aggregate_number'], 12)
            for index in (0, 1, 4, 5, 7):
                with self.assertRaises(ValueError):
                    spend(root, index, 'NATIVE', {})

    def test_classes_without_solution_or_forced_branch_template(self):
        for label in ('perception', 'persistence', 'metacognition', 'curiosity',
                      'goal/meta-goal regulation', 'reflection', 'action steering', 'affective-value'):
            self.assertIn(label, policy.PARENT_INSTRUCTIONS)
        self.assertIn('never prescribe', policy.PARENT_INSTRUCTIONS)
        self.assertIn('No prescribed branch counts', policy.PARENT_INSTRUCTIONS)

    def test_triples_are_unreviewed_not_outcome_qualified(self):
        from gpu.orch_r107_route_parent_r108_triples import evidence_table
        table = evidence_table([{}] * 12, 12)
        self.assertFalse(table['sufficient_episode_count'])
        self.assertIsNone(table['helpful'])
        self.assertFalse(table['automatic_keyword_or_outcome_qualification'])

    def test_registry_excludes_raw_and_extracts_only_identifiers(self):
        from gpu.orch_r107_route_parent_r108_registry import collect
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'COHORT.json').write_text('{"id":"N_1234567890", "private":"not emitted"}')
            (root / 'native').mkdir()
            (root / 'native/COHORT.json').write_text('{"id":"N_0000000000"}')
            result = collect([root])
            self.assertEqual(result['identifiers'], ['N_1234567890'])
            self.assertFalse(result['raw_embedded'])
            self.assertNotIn('not emitted', str(result))

    def test_registry_does_not_read_symlinked_metadata(self):
        from gpu.orch_r107_route_parent_r108_registry import collect
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'raw.txt').write_text('{"id":"N_1234567890"}')
            (root / 'COHORT.json').symlink_to(root / 'raw.txt')
            self.assertEqual(collect([root])['identifiers'], [])

    def test_fresh_disjoint_train_held_and_existing(self):
        train = policy.identifiers(self.cohort['train'])
        held = policy.identifiers(self.cohort['held'])
        self.assertFalse(train & held)
        with self.assertRaises(ValueError):
            policy.cohort(train, 2)
        self.assertEqual([len(group['tasks']) for group in self.cohort['train']], [2, 2])
        self.assertEqual([len(group['tasks']) for group in self.cohort['held']], [4, 4])

    def test_only_allocated_slots(self):
        for index in (0, 1, 4, 5, 7):
            with self.assertRaises(ValueError):
                policy.allocation(index)

    def test_actual_engine_shape_not_complete_response_fixture(self):
        prompt = [dict(role='system', content=policy.SYSTEM), dict(role='user', content='task')]
        response = minimal_engine().generate(prompt, max_new_tokens=8192)
        self.assertFalse(response['input_truncated'])
        self.assertTrue(response['full_prompt_prefix_verified'])
        self.assertEqual(response['prompt_token_ids_sha256'], policy.digest([11, 12]))
        self.assertEqual(response['messages'], prompt)
        self.assertTrue(response['terminal'])
        self.assertFalse(response['truncated'])

    def test_actual_engine_detects_modified_full_prompt(self):
        with self.assertRaises(AssertionError):
            minimal_engine(corrupt=True).generate([dict(role='user', content='task')], max_new_tokens=8192)

    def test_actual_engine_to_existing_episode(self):
        group = self.cohort['train'][0]; task = group['tasks'][0]
        engine = minimal_engine('Reasoning.\nROUTE ' + task['ports'][0])
        record = policy.episode(group['world'], task,
            lambda messages:engine.generate(messages, max_new_tokens=8192), {})
        self.assertGreaterEqual(record['actor_calls'], 1)
        self.assertFalse(record['captures'][0]['response']['input_truncated'])
        self.assertTrue(record['messages'][0]['content'].startswith('Reason through'))

    def test_strict_final_action_no_trailing_prose(self):
        self.assertEqual(policy.last_action('Reason.\nROUTE port'), dict(kind='ROUTE', value='port'))
        self.assertIsNone(policy.last_action('ROUTE port\nexplanation'))
        self.assertIsNone(policy.last_action('reason\n ROUTE port'))

    def test_source_reasoning_prompt_and_actual_event_receipts(self):
        seen = []
        def generate(messages):
            seen.append(messages)
            user = messages[-1]['content']
            if user.startswith('EXPOSURE'):
                port = next(line[6:] for line in user.splitlines() if line.startswith('PORTS '))
                raw = 'I will execute the offered action.\nROUTE ' + port
            else:
                match = re.search(r'RECEIPT (\S+) AT (\S+) DID (\S+) GOT (\S+)', user)
                event = re.search(r'AVAILABLE EVENT ADDRESS (\S+)', user)[1]
                receipt, source, port, destination = match.groups()
                raw = f'Actual receipt observed.\nEVENT {event} AT {source} DID {port} GOT {destination} EVIDENCE {receipt}'
            return minimal_engine(raw).generate(messages, max_new_tokens=8192)
        result = policy.collect_source(self.cohort['train'][0]['world'], generate)
        self.assertEqual(result['accepted_events'], 4)
        self.assertEqual(len(seen), 8)
        self.assertTrue(all(raw.startswith('Actual receipt observed.') for raw in result['store'].values()))
        self.assertFalse(any('Output no other text' in message['content'] or 'Output only that command' in message['content']
            for messages in seen for message in messages))

    def test_invalid_source_is_preserved_without_gold_or_retry(self):
        calls = []
        def generate(messages):
            calls.append(messages)
            return minimal_engine('No valid action.').generate(messages, max_new_tokens=8192)
        result = policy.collect_source(self.cohort['train'][0]['world'], generate)
        self.assertEqual(len(calls), 4)
        self.assertEqual(result['store'], {})
        self.assertTrue(all(record['error'] for record in result['records']))

    def test_parent_projection_no_hidden_or_held(self):
        group = self.cohort['train'][0]; task = group['tasks'][0]
        record = policy.episode(group['world'], task, lambda messages:minimal_engine('No action.').generate(messages, max_new_tokens=8192), {})
        payload = policy.parent_payload(2, 1, 1, record, [], [])
        self.assertNotIn('world', payload['episodes'][0]['public_experience'])
        self.assertNotIn('correct', payload['episodes'][0]['public_experience'])
        self.assertFalse(policy.identifiers(payload) & policy.identifiers(self.cohort['held']))
        for field in ('held', 'sealed_score', 'world'):
            changed = dict(payload, **{field: {}})
            with self.assertRaises(ValueError):
                policy.validate_parent_payload(changed)
        changed = deepcopy(payload); changed['episodes'][0]['task_id'] = 'HELD-secret'
        with self.assertRaises(ValueError):
            policy.validate_parent_payload(changed)

    def test_output_budget_remaining_context_and_no_padding(self):
        self.assertEqual(policy.token_budget(100), 8192)
        self.assertEqual(policy.token_budget(32760), 8)
        with self.assertRaises(ValueError):
            policy.token_budget(32768)

    def test_caps_additive_never_reset_prior(self):
        from gpu.orch_r107_route_parent_r108_run import spend
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for count in range(4):
                self.assertEqual(spend(root, 2, 'PARENT', {})['own_number'], count + 1)
            with self.assertRaises(ValueError):
                spend(root, 2, 'PARENT', {})
            self.assertEqual(spend(root, 3, 'PARENT', {})['aggregate_number'], 5)

    def test_existing_broker_receives_exact_route_digest(self):
        from gpu.orch_r107_route_parent_r108_broker import route_digest, existing
        original = existing.transport.parent.policy.digest
        payload = dict(episodes=['actual route'], note='unicode é')
        with route_digest():
            self.assertEqual(existing.transport.parent.policy.digest(payload), policy.digest(payload))
        self.assertIs(existing.transport.parent.policy.digest, original)

    def test_exact_stop_source_and_reflection_only(self):
        from gpu import orch_reflection_repetition_stop as helper
        import hashlib
        self.assertEqual(hashlib.sha256(Path(helper.__file__).read_bytes()).hexdigest(), policy.STOP_SHA)
        source = inspect.getsource(Engine.generate)
        self.assertIn('if reflection:', source)
        self.assertNotIn('optimizer', source)


if __name__ == '__main__':
    unittest.main()
