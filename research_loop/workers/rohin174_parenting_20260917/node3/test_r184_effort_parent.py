import copy
import unittest
from types import SimpleNamespace

from r184_effort_parent import AMENDMENT, MARKER, amended_prompt, install_prompt


class EffortPromptTests(unittest.TestCase):
    def test_append_only_payload_and_counters_unchanged(self):
        config = dict(cadence_responses=3)
        state = dict(response_count=129)
        memory = dict(awaiting_render=['existing'], last_response_count=129)
        before = copy.deepcopy((config, state, memory))
        payload = {'source': 'actual bound child input'}
        instruction, result = amended_prompt(lambda *args: ('existing strict policy', payload))(config, state, memory)
        self.assertIs(result, payload)
        self.assertEqual((config, state, memory), before)
        self.assertEqual(instruction, 'existing strict policy\n' + AMENDMENT)

    def test_both_dispatch_paths_use_new_prompt(self):
        namespace = {'prompt': lambda *args: ('old', {})}
        exec('def strict_tick():\n return prompt({}, {}, {})\ndef dispatch():\n return prompt({}, {}, {})\n', namespace)
        strict_tick, dispatch = namespace['strict_tick'], namespace['dispatch']
        def tick():
            return strict_tick(), dispatch()
        policy = SimpleNamespace(tick=tick, prompt=namespace['prompt'])
        install_prompt(policy)
        for instruction, unused_payload in policy.tick():
            self.assertEqual(instruction.count(MARKER), 1)

    def test_two_way_questions_no_answers_and_no_forced_action(self):
        for phrase in ('Use questions only', 'never give\nthe answer', 'BOTH directions',
                'Sometimes staying and thinking is the right choice', 'bypass pending ingestion',
                'response cadence and word/byte caps'):
            self.assertIn(phrase, AMENDMENT)

    def test_duplicate_amendment_rejected(self):
        with self.assertRaisesRegex(ValueError, 'single_effort_amendment'):
            amended_prompt(lambda *args: (MARKER, {}))({}, {}, {})


if __name__ == '__main__':
    unittest.main()
