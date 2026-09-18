import importlib.util
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location('reading_parent', HERE / 'reading_parent.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def state(**changes):
    value = dict(pending=None, last_publication_cycle=None, memory_after_cycle=None,
        next_reading_after_cycle=64, excerpt=0, step=0, retry_reason=None)
    value.update(changes)
    return value


class ReadingTests(unittest.TestCase):
    def test_exact_protocol_and_first_question(self):
        excerpts = MODULE.protocol(HERE / 'PROTOCOL.md')
        self.assertEqual(len(excerpts), 4)
        self.assertTrue(excerpts[0].startswith('Iona drives a horse-cab'))
        self.assertEqual(MODULE.question(state(), excerpts, 'reading'), MODULE.QUESTIONS[0] + '\n\n' + excerpts[0])

    def test_three_cycle_spacing_and_no_double_publication(self):
        self.assertIsNone(MODULE.choose_action(state(), 63))
        self.assertEqual(MODULE.choose_action(state(), 64), 'reading')
        self.assertIsNone(MODULE.choose_action(state(last_publication_cycle=64), 64))
        self.assertIsNone(MODULE.choose_action(state(pending={'id': 'waiting'}), 67))

    def test_memory_requires_subsequent_sleep(self):
        value = state(next_reading_after_cycle=67, memory_after_cycle=65)
        self.assertIsNone(MODULE.choose_action(value, 64))
        self.assertEqual(MODULE.choose_action(value, 65), 'memory')
        self.assertNotIn('Iona', MODULE.question(value, [], 'memory'))
        self.assertIn('do not remember', MODULE.MEMORY)

    def test_source_bound_read_response_advances_and_queues_memory(self):
        value = state(pending={'action': 'reading', 'render': {'index': 10}, 'after_cycle': 64})
        MODULE.advance(value, {'raw': 'A sad response.', 'awake_cycle': 65}, 64, [])
        self.assertEqual(value['step'], 1)
        self.assertEqual(value['memory_after_cycle'], 65)
        self.assertEqual(value['next_reading_after_cycle'], 67)

    def test_protocol_six_retry_once_then_next_excerpt(self):
        value = state(pending={'action': 'reading', 'render': {'index': 10}, 'after_cycle': 64})
        response = {'raw': '中文', 'awake_cycle': 65}
        MODULE.advance(value, response, 64, [])
        self.assertEqual(value['step'], 0)
        self.assertEqual(value['excerpt'], 0)
        self.assertIn('non-English-script', MODULE.question(value, ['exact excerpt'], 'reading'))
        value['pending'] = {'action': 'reading', 'render': {'index': 20}, 'after_cycle': 67}
        MODULE.advance(value, response, 67, [])
        self.assertEqual(value['excerpt'], 1)
        self.assertIsNone(value['retry_reason'])

    def test_no_advance_without_actual_render(self):
        value = state(pending={'action': 'reading', 'render': None})
        with self.assertRaisesRegex(ValueError, 'actual_render_before_response'):
            MODULE.advance(value, {'raw': 'any', 'awake_cycle': 65}, 64, [])

    def test_spacing_only_repetition_preserves_input(self):
        raw = 'An actual repeated sentence with enough characters to be detected without using a tiny greeting. '
        self.assertIsNotNone(MODULE.repeated_or_nonenglish(raw, [raw.replace(' ', '  ')]))
        self.assertTrue(raw.endswith(' '))

    def test_memory_does_not_advance_protocol(self):
        value = state(step=1, memory_after_cycle=65,
            pending={'action': 'memory', 'render': {'index': 30}, 'after_cycle': 65})
        MODULE.advance(value, {'raw': 'I do not remember.', 'awake_cycle': 66}, 65, [])
        self.assertEqual(value['step'], 1)
        self.assertIsNone(value['memory_after_cycle'])


if __name__ == '__main__':
    unittest.main()
