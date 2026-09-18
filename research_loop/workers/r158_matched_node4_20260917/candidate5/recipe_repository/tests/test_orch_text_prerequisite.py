import json
from pathlib import Path
import unittest
from unittest.mock import patch
import tempfile
from types import SimpleNamespace

from organism_v6 import orch_text_prerequisite as screen
from gpu import orch_text_prerequisite_run as runner


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.task = dict(id='test', goal='Carry the pillow.')
        self.state = dict(description='A closed safe.', inventory='Nothing.', feedback='Native feedback.')

    def test_exact_actions(self):
        self.assertEqual(screen.parse('ACTION: open safe', 'TERSE')['action'], 'open safe')
        self.assertEqual(screen.parse('I see a safe.\nACTION: open safe\n', 'RICH')['prose'], 'I see a safe.')

    def test_no_rescue(self):
        for raw in ['open safe', 'ACTION: open safe\nDone.', 'ACTION: open safe\nACTION: take pillow',
                    ' ACTION: open safe', 'ACTION: open safe; take pillow', 'ACTION: open safe\n\n']:
            with self.assertRaises(ValueError):
                screen.parse(raw, 'TERSE')

    def test_truncations_fail_even_with_action(self):
        for terminal, truncated in [(False, False), (False, True), (True, True)]:
            with self.assertRaises(ValueError):
                screen.parse('ACTION: open safe', 'TERSE', terminal, truncated)

    def test_voice_and_length_do_not_admit_semantics(self):
        projection = screen.parse('I have already won, without evidence.\nACTION: open safe', 'RICH')
        self.assertNotIn('admitted', projection)

    def test_parent_and_feedback_not_student_prefix(self):
        prefix = str(screen.student_prefix(self.task, self.state))
        for forbidden in ['150', 'tokens', 'Native feedback', 'ACTION:', 'system', 'oracle_commands']:
            self.assertNotIn(forbidden, prefix)

    def test_bounded_history_and_no_solver_visibility(self):
        self.task['oracle_commands'] = ['SECRET_ORACLE']
        previous = dict(observation='Previous observation', raw='Previous child')
        request = screen.messages(self.task, self.state, 'RICH', 3, previous)
        self.assertEqual(len(request), 4)
        self.assertNotIn('SECRET_ORACLE', str(request))
        self.assertNotIn('Native feedback', screen.observation(self.task, self.state, 0))

    def test_paired_gate_and_denominator(self):
        self.assertFalse(screen.eligible([True] * 8, [True] * 8)['outcome_gap_pass'])
        self.assertTrue(screen.eligible([True] * 8, [False] * 8)['outcome_gap_pass'])
        with self.assertRaises(ValueError):
            screen.eligible([True], [False])

    def test_frozen_native_bank(self):
        path = Path(__file__).resolve().parents[1] / 'research_notes/analysis/orch_text_prerequisite_20260914_attempt1/BANK.json'
        self.assertEqual(screen.digest(path.read_text()), screen.BANK_SHA)
        bank = json.loads(path.read_text())
        self.assertEqual(bank['version'], '1.7.0')
        self.assertEqual(len(bank['tasks']), 12)
        self.assertEqual(sum(task['split'] == 'mining' for task in bank['tasks']), 8)
        self.assertEqual(len({task['seed'] for task in bank['tasks']}), 12)
        for task in bank['tasks']:
            self.assertFalse(task['prerequisite_probe']['won'])
            self.assertTrue(task['correction_replay'][-1]['won'])
            self.assertEqual(len(task['oracle_commands']), 2)

    def test_bad_outputs_consume_all_six_turns(self):
        state = dict(self.state, won=False, lost=False, score=0)
        task = dict(self.task, family='retrieve_closed', game='native.z8', initial=state)
        native = SimpleNamespace(state=state, close=lambda: None)
        tokenizer = SimpleNamespace(apply_chat_template=lambda *args, **kwargs: [1, 2])
        response = dict(raw='ACTION: open safe', terminal=False, truncated=True)
        engine = SimpleNamespace(tokenizer=tokenizer, check=lambda label: None,
                                 generate=lambda *args, **kwargs: response)
        options = SimpleNamespace(env_python='unused', games='unused')
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'NativeEnvironment', return_value=native):
            calls = []
            result = runner.episode(task, 'RICH', engine, options, Path(directory), calls)
            self.assertFalse(result['success'])
            self.assertEqual(len(calls), 6)
            self.assertEqual(len(result['turns']), 6)
            self.assertTrue(all(turn['native_after'] is None for turn in result['turns']))

    def test_context_error_preserves_failed_episode(self):
        state = dict(self.state, won=False, lost=False, score=0)
        task = dict(self.task, family='retrieve_closed', game='native.z8', initial=state)
        native = SimpleNamespace(state=state, close=lambda: None)
        tokenizer = SimpleNamespace(apply_chat_template=lambda *args, **kwargs: [1] * 2049)
        engine = SimpleNamespace(tokenizer=tokenizer, check=lambda label: None)
        options = SimpleNamespace(env_python='unused', games='unused')
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'NativeEnvironment', return_value=native):
            calls = []
            result = runner.episode(task, 'TERSE', engine, options, Path(directory), calls)
            self.assertFalse(result['success'])
            self.assertEqual(result['error']['message'], 'context_bound_no_truncation')
            self.assertEqual(calls, [])
            self.assertTrue((Path(directory) / 'test_TERSE_EPISODE.json').exists())


if __name__ == '__main__':
    unittest.main()
