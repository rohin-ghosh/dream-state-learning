import json
import tempfile
import time
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from gpu import orch_rich_hot_node2_continue as runner
from organism_v6 import orch_rich_hot_node2 as hot
from organism_v6 import orch_rich_hot_node2_supply as policy


class SupplyTests(unittest.TestCase):
    def document(self):
        records = [dict(question=f'Prospective question {index}', answer='work #### 42') for index in range(8)]
        previous = dict(tasks=[dict(id='gsm8k-train-0', question_sha256=hot.question_hash(records[0]['question']))],
                        excluded_ids=['gsm8k-train-1'], excluded_question_hashes=[])
        return policy.cohort(records, previous)

    def response(self, raw, terminal=True, truncated=False):
        return dict(raw=raw, terminal=terminal, truncated=truncated, token_ids=[1] * 500 + [2])

    def test_train_only_fresh_math_and_known_code_gym(self):
        document = self.document()
        self.assertEqual(len(document['math']['tasks']), 6)
        self.assertEqual(len(document['code']), 64)
        self.assertEqual(len(document['route']), 256)
        self.assertEqual(document, self.document())
        self.assertNotIn('held', str(document['route']).lower())
        self.assertFalse(document['held_access'])

    def test_each_parity_shard_gets_all_families_and_repeats_are_explicit(self):
        document = self.document()
        for parity in (0, 1):
            tasks = [policy.task_at(document, 0, position) for position in range(24) if position % 2 == parity]
            self.assertEqual(Counter(task['family'] for task in tasks), dict(math=4, code=4, route=4))
        self.assertTrue(policy.task_at(document, 200, 1)['repeated_train_source'])
        with self.assertRaisesRegex(ValueError, 'bounded_supply_cursor'):
            policy.task_at(document, 256, 0)

    def test_code_own_target_exact_parser_and_safe_oracle(self):
        task = policy.task_at(self.document(), 0, 1)
        payload = task['payload']
        expression = f"sum(affine(ge(values,{payload['threshold']}),{payload['factor']},{payload['offset']}))"
        result = policy.outcome(task, self.response(json.dumps(dict(expression=expression))))
        self.assertTrue(result['correct'])
        self.assertFalse(result['admitted'])
        self.assertEqual(result['content_tokens'], 500)
        self.assertFalse(policy.outcome(task, self.response('{"expression":"__import__(1)"}'))['correct'])
        self.assertEqual(policy.outcome(task, self.response('prose answer'))['category'], 'missing_exact_expression_JSON')
        self.assertEqual(policy.outcome(task, self.response('{}', False, True))['category'], 'truncation')

    def test_code_prompt_no_oracle_feedback_or_reference_targets(self):
        task = policy.task_at(self.document(), 0, 1)
        for condition in hot.CONDITIONS:
            messages = policy.messages(task, condition)
            self.assertNotIn('expected', str(messages))
            self.assertNotIn('inputs', str(messages))
            self.assertNotIn('150', str(messages))
        previous = 'Exact own previous attempt'
        self.assertEqual(policy.messages(task, 'TWO_PASS', previous)[-2]['content'], previous)

    def test_route_failure_is_retained_and_no_teacher_memory_inserted(self):
        task = policy.task_at(self.document(), 0, 2)
        seen = []

        def generate(stage, messages):
            seen.append((stage, messages))
            return self.response('bad action')

        result = policy.route_task(task, 'LIGHT_BRANCH', generate)
        self.assertEqual(result['accepted_events'], 0)
        self.assertEqual(result['complete_routes'], 0)
        self.assertEqual(len(seen), 6)
        self.assertEqual([record['terminal_reason'] for record in result['episodes']], ['invalid_final_action'] * 2)
        for stage, messages in seen:
            self.assertNotIn('150–400', str(messages))
        with self.assertRaisesRegex(ValueError, 'supply_train_namespace'):
            policy.runtime('ORCH-HELD-0')

    def test_route_exposure_replay_and_real_actions(self):
        task = policy.task_at(self.document(), 0, 2)
        world = task['payload']
        environment = policy.runtime(world['master'])

        def generate(stage, messages):
            content = messages[-1]['content']
            if stage == 'exposure':
                if content.startswith('EXPOSURE TASK'):
                    port = next(line[6:] for line in content.splitlines() if line.startswith('PORTS '))
                    return self.response('ROUTE ' + port)
                transition = next(edge for edge in world['edges'] if edge['receipt'] in content)
                event = ('EVENT {event} AT {node} DID {port} GOT {outcome} EVIDENCE {receipt}\n').format(**transition)
                return self.response(event)
            public = next(message['content'] for message in reversed(messages) if 'CURRENT ' in message['content'])
            current = next(line[8:] for line in public.splitlines() if line.startswith('CURRENT '))
            goal = next(line[5:] for line in public.splitlines() if line.startswith('GOAL '))
            first = next(edge for edge in world['edges'] if edge['outcome'] == goal)
            edge = first if current == first['node'] else next(edge for edge in world['edges'] if edge['outcome'] == first['node'])
            return self.response('My test callback chooses a route.\nROUTE ' + edge['port'])

        result = policy.route_task(task, 'ORIGINAL_RICH', generate)
        environment['replay_collection'](result['collection'])
        self.assertEqual(result['accepted_events'], 4)
        self.assertEqual(result['complete_routes'], 2)
        self.assertFalse(result['trainingAllowed'])

    def test_call_reservation_cap_deadline_and_no_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'reservations').mkdir()
            task = policy.task_at(self.document(), 0, 0)
            with patch.object(policy, 'CALLS_PER_SHARD', 1):
                row = runner.reserve(root, 0, task, 'final', [], time.time() + 60)
                self.assertEqual(row['index'], 0)
                with self.assertRaises(runner.BudgetEnd):
                    runner.reserve(root, 0, task, 'draft', [], time.time() + 60)
            with self.assertRaises(runner.BudgetEnd):
                runner.reserve(root, 1, task, 'final', [], time.time() - 1)
            self.assertEqual(len(list((root / 'reservations').glob('*.json'))), 1)

    def test_original_terminal_requires_full_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertFalse(runner.original_terminal(root))
            (root / 'TERMINAL.json').write_text(json.dumps(dict(status='COMPLETE', releases={})))
            with self.assertRaisesRegex(ValueError, 'original_not_safely_released'):
                runner.original_terminal(root)


if __name__ == '__main__':
    unittest.main()
