import unittest

from organism_v6 import orch_game_screen as screen


def response(raw):
    return dict(raw=raw, token_ids=[1] * 20, prompt_tokens=100, terminal=True, truncated=False)


def toy_bank():
    return dict(map=['+---+', '|R:G|', '+---+'], locations=[[0, 0], [0, 1], [1, 0], [1, 1]],
                decoded={'0': [0, 1, 4, 0], '1': [0, 0, 4, 0]},
                transitions={str(state): {str(action): [[1.0, 1 if action == 3 else state,
                    20 if state == 1 and action == 5 else -1, state == 1 and action == 5]]
                    for action in range(6)} for state in range(2)})


class GameTests(unittest.TestCase):
    def test_native_table_nondeterminism_rejected(self):
        bank = toy_bank()
        bank['transitions']['0']['0'][0][0] = .5
        with self.assertRaises(ValueError):
            screen.transition(bank, 0, 0)

    def test_exact_oracle_distance(self):
        self.assertEqual(screen.shortest_distance(toy_bank(), 0), 2)

    def test_action_last_no_header_gate_no_repair(self):
        self.assertEqual(screen.parse_action('I expect to move west.\nACTION: WEST', 'RICH'), 3)
        for text in ('ACTION: WEST\nI moved.', 'ACTION: west', 'ACTION: WEST\nACTION: WEST', 'ACTION: WEST'):
            with self.assertRaises(ValueError):
                screen.parse_action(text, 'RICH')

    def test_wrong_then_correct_retains_feedback_and_denominators(self):
        outputs = iter([response('invalid'), response('I move west.\nACTION: WEST'),
                        response('I deliver here.\nACTION: DROPOFF')])
        instance = dict(id='fixture', split='mining', state=0)
        captures = []
        result = screen.episode(toy_bank(), instance, 'RICH', lambda messages: next(outputs),
                                lambda turn, record: captures.append(record))
        self.assertTrue(result['success'])
        self.assertEqual(len(captures), 3)
        self.assertIn('State unchanged', captures[1]['observation']['text'])
        self.assertEqual(captures[0]['response']['raw'], 'invalid')
        self.assertEqual(result['admitted_rows'], 0)
        self.assertEqual(result['semantic_status'], 'UNREVIEWED')

    def test_six_turn_error_cap(self):
        result = screen.episode(toy_bank(), dict(id='fixture', split='mining', state=0), 'TERSE',
                                lambda messages: response('bad'), lambda turn, record: None)
        self.assertEqual(len(result['turns']), 6)
        self.assertFalse(result['success'])

    def test_held_not_used(self):
        with self.assertRaisesRegex(ValueError, 'held_l1'):
            screen.episode({}, dict(split='held_l1'), 'RICH', None, None)

    def test_length_not_semantic_oracle(self):
        result = screen.episode(toy_bank(), dict(id='fixture', split='mining', state=1), 'RICH',
                                lambda messages: response('False explanation.\nACTION: DROPOFF'),
                                lambda turn, record: None)
        self.assertTrue(result['success'])
        self.assertFalse(result['fit_ready'])
        self.assertEqual(result['admitted_rows'], 0)

    def test_budget_failures_preserved(self):
        for field, value in [('prompt_tokens', 2049), ('token_ids', [1] * 513), ('truncated', True)]:
            raw = response('ACTION: WEST')
            raw[field] = value
            result = screen.episode(toy_bank(), dict(id='fixture', split='mining', state=0), 'TERSE',
                                    lambda messages: raw, lambda turn, record: None)
            self.assertTrue(all(turn['error'] for turn in result['turns']))
            self.assertFalse(result['success'])

    def test_matched_sign_test_and_complete_denominators(self):
        episodes = [dict(instance=dict(id=str(index)), arm=arm, success=arm == 'RICH', turns=[])
                    for index in range(16) for arm in ('RICH', 'TERSE')]
        result = screen.summarize(episodes, list(map(str, range(16))))
        self.assertTrue(result['outcome_pool_pass'])
        self.assertFalse(result['fit_ready'])
        with self.assertRaises(ValueError):
            screen.summarize(episodes[:-1], list(map(str, range(16))))
        for entry in episodes:
            entry['success'] = True
        result = screen.summarize(episodes, list(map(str, range(16))))
        self.assertFalse(result['outcome_pool_pass'])
        self.assertEqual(result['paired_one_sided_sign_p'], 1)


if __name__ == '__main__':
    unittest.main()
