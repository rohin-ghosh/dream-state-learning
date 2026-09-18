"""CPU regression checks; no model, network, or generated Python execution."""

import copy
import unittest

from organism_v6 import orch_code_channel as policy
from gpu import astra_portable_actor_bundle as portable


TASK = dict(id=12345, text='Find the sum.', arguments=['left', 'right'], family='scalar arithmetic',
    tests=[dict(source='assert add(2,3) == 5', arguments=[2, 3], expected=5)], function='add')


def result(text, count=180):
    return dict(raw=text, token_ids=[10] * count + [99], terminal=True, truncated=False)


class ChannelTests(unittest.TestCase):
    def test_original_mount_identity(self):
        self.assertEqual(policy.MOUNTED, portable.PARENT_STATE)

    def test_legacy_byte_exact(self):
        self.assertEqual(policy.prompt(TASK, 'LEGACY')[0], policy.code.prompt(TASK, 'rich', [])[0])

    def test_terse_byte_exact(self):
        self.assertEqual(policy.prompt(TASK, 'TERSE')[0], policy.code.prompt(TASK, 'terse', [])[0])

    def test_separated_only_system_changed(self):
        self.assertEqual(policy.prompt(TASK, 'SEPARATED')[0][1:], policy.prompt(TASK, 'LEGACY')[0][1:])

    def test_projection_no_compilation(self):
        text = 'NARRATIVE:\nI add the named inputs.\nACTION:\n{"expression":"left+right"}'
        action, rationale = policy.project(text, 'SEPARATED')
        self.assertEqual(action, 'left+right')
        self.assertTrue(policy.code.check(TASK, action)['success'])
        self.assertEqual(rationale, 'I add the named inputs.')

    def test_no_function_repair(self):
        row = policy.capture(TASK, 'SEPARATED', result('NARRATIVE:\nI add.\nACTION:\n{"expression":"def add(left,right): return left+right"}'))
        self.assertFalse(row['outcome_pass'])

    def test_missing_envelope_failure(self):
        row = policy.capture(TASK, 'SEPARATED', result('{"expression":"left+right"}'))
        self.assertFalse(row['outcome_pass'])

    def test_source_failure_no_record(self):
        row = policy.capture(TASK, 'LEGACY', result('{"expression":"left-right"}'))
        with self.assertRaises(ValueError):
            policy.prompt(TASK, 'LEGACY', row)
            policy.capture(TASK, 'LEGACY', result('{"record":"own lesson"}'), row)

    def test_neutral_history_keeps_child_not_coaching(self):
        source = policy.capture(TASK, 'LEGACY', result('My sum.\n{"expression":"left+right"}'))
        messages, student = policy.prompt(TASK, 'LEGACY', source)
        self.assertIn('Oracle feedback:', messages[-1]['content'])
        self.assertEqual(student[1], dict(role='assistant', content=source['target']))
        self.assertNotIn('Oracle feedback:', str(student))
        self.assertNotIn('150–400', str(student))
        self.assertFalse(any(message['role'] == 'system' for message in student))

    def test_unreviewed_never_admitted(self):
        row = policy.capture(TASK, 'LEGACY', result('I add.\n{"expression":"left+right"}'))
        self.assertFalse(row['admitted'])
        self.assertEqual(row['semantic_status'], 'UNREVIEWED')

    def test_gate_requires_all_semantic_axes(self):
        row = policy.capture(TASK, 'LEGACY', result('I add.\n{"expression":"left+right"}'))
        review = dict(target_sha256=row['target_sha256'], status='PASS', reason='Full text checked.',
                      quotes=['I add.'], **{axis: True for axis in policy.AXES})
        self.assertTrue(policy.admission(row, review))
        review['grounding'] = False
        with self.assertRaises(ValueError):
            policy.admission(row, review)

    def test_token_gate_and_truth_not_length_padding(self):
        row = policy.capture(TASK, 'LEGACY', result('I add.\n{"expression":"left+right"}', 401))
        self.assertFalse(row['token_contract'])
        row = policy.capture(TASK, 'LEGACY', result('I add.\n{"expression":"left+right"}', 149))
        self.assertFalse(row['token_contract'])

    def test_record_template_legacy_exact(self):
        source = policy.capture(TASK, 'LEGACY', result('{"expression":"left+right"}'))
        self.assertEqual(policy.prompt(TASK, 'LEGACY', source)[0], policy.code.prompt(TASK, 'rich', [source], True)[0])

    def test_no_generated_execution(self):
        for expression in ('__import__("os").system("id")', 'open("secret")', 'eval("2+3")'):
            self.assertFalse(policy.code.check(TASK, expression)['success'])

    def test_no_reduced_denominator(self):
        with self.assertRaises(ValueError):
            policy.reduce([TASK], [])

    def test_distinct_tasks_not_rows(self):
        tasks = [dict(TASK, id=number) for number in range(64)]
        source = policy.capture(tasks[0], 'SEPARATED', result('NARRATIVE:\nI add.\nACTION:\n{"expression":"left+right"}'))
        source.update(admitted=True, semantic_status='PASS')
        record = copy.deepcopy(source)
        record['kind'] = 'NEW'
        summary = policy.reduce(tasks, [source, record])
        self.assertEqual(summary['arms']['SEPARATED']['qualified_tasks'], 1)
        self.assertFalse(summary['candidate'])


if __name__ == '__main__':
    unittest.main()
