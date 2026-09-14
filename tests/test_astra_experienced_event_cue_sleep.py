"""CPU-only second-sleep evaluator tests, not native learning evidence."""

from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gpu import astra_experienced_event_cue_sleep as runner
from organism_v6 import experienced_event_cue_collection as cue
from test_astra_experienced_event_microloop import fixture


class Model:
    disabled = False

    @contextmanager
    def disable_adapter(self):
        self.disabled = True
        try:
            yield
        finally:
            self.disabled = False


class PublicEngine:
    def __init__(self, bank):
        self.model = Model()
        self.bank = {fact['event']: fact for fact in bank}
        self.messages = []

    def generate(self, messages):
        self.messages.append(messages)
        if messages[0]['content'] == runner.source.world.MEMORY_SYSTEM:
            address = messages[-1]['content'].split('READ EVENT ')[-1].splitlines()[0].strip()
            raw = runner.source.material._event(self.bank[address]) if address in self.bank and not self.model.disabled else 'MISS\n'
        else:
            task = dict(line.split(' ', 1) for line in messages[1]['content'].splitlines()[1:])
            read = {message['content'].strip().split(' ')[2] for message in messages
                    if message['role'] == 'assistant' and message['content'].startswith('READ EVENT ')}
            raw = None
            for message in messages:
                if message['role'] == 'user' and message['content'].startswith('MEMORY RESULT\nEVENT '):
                    event = runner.source.material.parse_event_line(
                        runner.source.material.canonical_event(message['content'][14:]))
                    if event['source'] == task['NODE'] and event['destination'] == task['GOAL']:
                        raw = 'ROUTE ' + event['port']
            if raw is None:
                unread = [address for address in task['EVENTS'].split(',') if address not in read]
                raw = 'READ EVENT ' + unread[0] if unread else 'ROUTE ' + task['PORTS'].split(',')[0]
        return dict(raw=raw, terminal=True, truncated=False, messages=messages)


class Tests(unittest.TestCase):
    def test_base_identity_must_agree_across_all_stages(self):
        receipt = dict(arguments=dict(expected_base_sha256='a' * 64))
        runner.validate_base_sources('a' * 64, receipt, receipt, receipt)
        for other in ({}, dict(arguments={}), dict(arguments=dict(expected_base_sha256='b' * 64))):
            with self.assertRaisesRegex(ValueError, 'same_frozen_base'):
                runner.validate_base_sources('a' * 64, receipt, other)

    def test_stage_deadlines_are_fixed_before_engine_phase_changes(self):
        self.assertEqual(runner.stage_seconds('train'), 3600)
        self.assertEqual(runner.stage_seconds('readout'), 1800)
        with self.assertRaises(ValueError):
            runner.stage_seconds('unknown')

    def test_parent_free_conditional_policy_and_reader_intervention(self):
        bank, episodes = fixture()
        engine = PublicEngine(bank)
        with TemporaryDirectory() as directory:
            report = runner.evaluate(engine, bank, episodes, Path(directory))
            self.assertLessEqual(report['model_calls'], 76)
            self.assertEqual(len(list(Path(directory).glob('CALL_*.json'))), report['model_calls'])
        panels = report['panels']
        self.assertEqual(panels['OWN_PARAMETRIC']['reached_goal'], 4)
        self.assertEqual(panels['OWN_READER_OFF']['reached_goal'], 2)
        self.assertEqual(panels['RECALL_W0']['correct'], 4)
        self.assertEqual(panels['RECALL_W8']['correct'], 4)
        self.assertEqual(panels['UNSEEN_MISS']['correct'], 4)
        for name in ('HELD_TEXT_0', 'HELD_TEXT_1'):
            self.assertEqual(panels[name]['reached_goal'], 4)
            self.assertEqual(panels[name]['second_reads'], 2)
        self.assertFalse(report['parent_present'])
        for messages in engine.messages:
            self.assertTrue(all(cue.PUBLIC_FEEDBACK_PREFIX not in message['content']
                                and 'Teacher strategy' not in message['content'] for message in messages))

    def test_actual_callback_error_is_not_reported_as_policy_failure(self):
        bank, episodes = fixture()
        engine = PublicEngine(bank)

        def fail(messages):
            raise RuntimeError('synthetic callback failure')

        engine.generate = fail
        with TemporaryDirectory() as directory, self.assertRaisesRegex(ValueError, 'infrastructure'):
            runner.evaluate(engine, bank, episodes, Path(directory))

    def test_nonterminal_outputs_remain_failure_inclusive(self):
        bank, episodes = fixture()
        engine = PublicEngine(bank)
        engine.generate = lambda messages: dict(raw='MISS\n', terminal=False, truncated=True)
        with TemporaryDirectory() as directory:
            result = runner.evaluate(engine, bank, episodes, Path(directory))
        self.assertEqual(result['panels']['OWN_PARAMETRIC']['reached_goal'], 0)
        self.assertEqual(result['panels']['UNSEEN_MISS']['correct'], 0)
        self.assertEqual(result['panels']['HELD_TEXT_0']['denominator'], 4)


if __name__ == '__main__':
    unittest.main()
