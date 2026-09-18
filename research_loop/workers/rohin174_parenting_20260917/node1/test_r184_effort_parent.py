import unittest

from r184_effort_parent import INSTRUCTION, effort_loop


class EffortParentTests(unittest.TestCase):
    def test_both_effort_directions_carry_and_no_answers(self):
        for text in ('more thinking', 'small attempt', 'sometimes invite staying',
                     'never answer', 'carry into the following turn', 'Do not repeat any introduction'):
            self.assertIn(text, INSTRUCTION)
        self.assertEqual(INSTRUCTION.count('?'), 4)

    def test_preserves_prior_response_cursor_and_arm_cadence(self):
        raw = '''def serve(config, counts):
 last_count = 0
 calls = 0
 selected = []
 for count in counts:
  state = {'response_count': count}
  if state['response_count'] < max(1, last_count + config['cadence_responses']):
   continue
  last_count = count
  calls += 1
  selected.append(count)
 return selected
'''
        for cadence in (1, 2, 3):
            for first in (1, cadence):
                with self.subTest(cadence=cadence, first=first):
                    scope = {}
                    exec(effort_loop(raw, 'fixture', 100, first), scope)
                    self.assertEqual(scope['serve']({'cadence_responses': cadence}, list(range(100, 110))),
                                     list(range(100 + first, 110, cadence)))


if __name__ == '__main__':
    unittest.main()
