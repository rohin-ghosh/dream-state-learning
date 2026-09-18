import ast
import unittest
from types import SimpleNamespace

from takeover import HERE, REPO, require
from r181_patch import patch_native, function_text


class DeltaTests(unittest.TestCase):
    def test_all_actual_sources_preserve_every_other_node(self):
        canonical = (REPO / 'gpu/orch_r125_continual_native.py').read_text()
        for physical in (0, 1, 2, 3, 4, 7):
            with self.subTest(physical=physical):
                original = (HERE / 'r181' / ('physical' + str(physical)) / 'original_native.py').read_text()
                updated = patch_native(original, canonical)
                before = ast.parse(original)
                after = ast.parse(updated)
                for prior, changed in zip(before.body, [node for node in after.body if getattr(node, 'name', '')
                        not in ('select_rehearsal_rows', 'respond_to_presleep_inbox')]):
                    name = getattr(prior, 'name', '')
                    if name == 'validate_plan':
                        continue
                    if name == 'NativeChild':
                        prior.body = [node for node in prior.body if getattr(node, 'name', '') != 'sleep']
                        changed.body = [node for node in changed.body if getattr(node, 'name', '') != 'sleep']
                    if name == 'run':
                        for node in ast.walk(changed):
                            if hasattr(node, 'body') and isinstance(node.body, list):
                                node.body = [statement for statement in node.body if not
                                    (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
                                     and isinstance(statement.value.func, ast.Name)
                                     and statement.value.func.id == 'respond_to_presleep_inbox')]
                    self.assertEqual(ast.dump(prior), ast.dump(changed))

    def test_rehearsal_zero_does_not_iterate_old_rows(self):
        canonical = (REPO / 'gpu/orch_r125_continual_native.py').read_text()
        namespace = dict(require=require)
        exec(function_text(canonical, 'select_rehearsal_rows'), namespace)
        select_rows = namespace['select_rehearsal_rows']
        self.assertEqual(select_rows({'rehearsal_presentations': 0}, None), [])
        old_rows = [object()]
        self.assertIs(select_rows({'rehearsal_presentations': 1}, old_rows), old_rows)
        for invalid in (True, -1, 2, '0'):
            with self.assertRaises(ValueError):
                select_rows({'rehearsal_presentations': invalid}, old_rows)

    def test_presleep_parent_is_ingested_once_not_synthesized(self):
        canonical = (REPO / 'gpu/orch_r125_continual_native.py').read_text()
        namespace = dict(require=require)
        exec(function_text(canonical, 'respond_to_presleep_inbox'), namespace)
        calls = []
        parent = SimpleNamespace(event_id='existing-baseline', actor='parent')
        stream = SimpleNamespace(pending=None, sleep_due=True, history=SimpleNamespace(events=[]))
        stream.step = lambda *args, **kwargs: (calls.append(kwargs['incoming']), stream.history.events.extend(kwargs['incoming']))
        journal = SimpleNamespace(read_inbox=lambda: [parent], record=lambda *args: None)
        child = SimpleNamespace(generate=None, count_tokens=None)
        self.assertTrue(namespace['respond_to_presleep_inbox'](child, stream, journal, 45))
        self.assertFalse(namespace['respond_to_presleep_inbox'](child, stream, journal, 45))
        self.assertEqual(calls, [[parent]])


if __name__ == '__main__':
    unittest.main()
