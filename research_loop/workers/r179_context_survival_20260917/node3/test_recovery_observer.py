import ast
from pathlib import Path
import unittest


tree = ast.parse(Path(__file__).with_name('observe_recovery.py').read_bytes())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'history_progress')
namespace = {}
exec(compile(ast.Module(body=[function], type_ignores=[]), '<observer-history-only>', 'exec'), namespace)
progress = namespace['history_progress']


class ObserverTests(unittest.TestCase):
    def decision(self, action='RETAIN_CONTEXT_ACROSS_SLEEP', before='same', after='same'):
        policy = dict(cycle=44, action=action, history_sha256_before=before, history_sha256_after=after)
        return dict(kind='CONTEXT_RETAINED' if action == 'RETAIN_CONTEXT_ACROSS_SLEEP' else 'COMPACTION',
            index=500, sha256='record', document=policy if action == 'RETAIN_CONTEXT_ACROSS_SLEEP' else {'context_policy': policy})

    def complete(self, history='same'):
        return dict(kind='SLEEP_COMPLETE', index=700, sha256='saved', document=dict(cycle=44, optimizer_steps=200,
            resume_state=dict(state=dict(history=dict(state_sha256=history)))))

    def test_retention_decision_is_not_completed_sleep(self):
        result = progress([self.decision()])
        self.assertEqual(result['first_context_policy']['cycle'], 44)
        self.assertFalse(result['new_completed_sleep_observed'])

    def test_complete_requires_identical_before_after_saved_history(self):
        result = progress([self.decision(), self.complete()])
        self.assertTrue(result['completed_sleeps'][0]['retained_history_through_completed_sleep'])
        for records in ([self.complete()], [self.decision(), self.complete('different')],
                        [self.decision(after='different'), self.complete()]):
            with self.subTest(records=records):
                self.assertFalse(progress(records)['completed_sleeps'][0]['retained_history_through_completed_sleep'])

    def test_threshold_compaction_not_misreported_as_retention(self):
        result = progress([self.decision('COMPACT_AT_CONTEXT_THRESHOLD'), self.complete()])
        self.assertEqual(result['first_context_policy']['action'], 'COMPACT_AT_CONTEXT_THRESHOLD')
        self.assertFalse(result['completed_sleeps'][0]['retained_history_through_completed_sleep'])

