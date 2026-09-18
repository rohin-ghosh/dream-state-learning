"""Regression checks for the read-only observer, not receiving-runtime tests."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import inspect_node4 as observer


HOME = Path(__file__).resolve().parent
HELPER_PATH = HOME.parent / 'r181_reference/r144_helpers.py'


class ObserverTests(unittest.TestCase):
    def test_timer_is_not_an_extra_learner(self):
        timer = (Path('/proc/10'), [], dict(pid=10, parent=9))
        native = (Path('/proc/11'), [], dict(pid=11, parent=10))
        other_native = (Path('/proc/21'), [], dict(pid=21, parent=20))
        self.assertEqual(observer.native_leaves([timer, native, other_native]),
                         [native, other_native])

    def test_relocated_read_resolves_backing_without_rewriting_plan(self):
        specification = importlib.util.spec_from_file_location('reference_helpers', HELPER_PATH)
        helpers = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(helpers)
        with tempfile.TemporaryDirectory(prefix='observer_test_', dir=HOME) as temporary:
            home = Path(temporary)
            backing = home / 'receiving2v2/run1'
            records = backing / 'stream/records'
            records.mkdir(parents=True)
            logical_home = home / 'orch_r133_brain_free_20260916_attempt1'
            logical_home.mkdir()
            logical = logical_home / 'run1'
            logical.symlink_to(backing, target_is_directory=True)
            state = dict(pending=None, rows=[], sleep_frontier=0, deadline_unix=1789754400,
                         sleep_receipts=[dict(status='COMPLETE')])
            record = dict(index=0, kind='SLEEP_COMPLETE', document=dict(status='COMPLETE',
                cycle=55, resume_state=dict(state=state, sha256=helpers.digest(state))))
            record['sha256'] = helpers.digest(record)
            (records / '00000000000000000000.json').write_text(json.dumps(record))
            plan = dict(root=str(logical), source_root=str(home / 'source'), physical=5)
            plan_path = home / 'PLAN.json'
            plan_path.write_text(json.dumps(plan))
            guard = home / 'GUARD.json'
            guard.write_text(json.dumps(dict(plan_path=str(plan_path), plan_sha256=helpers.sha(plan_path))))
            with self.assertRaisesRegex(ValueError, 'no_symlinks'):
                helpers.sleep_boundary(logical)
            with patch.object(observer, 'process_metadata', return_value=dict(pid=11)):
                result = observer.inspect_life(Path('/proc/11'), ['native', '--config', str(guard)], helpers)
            self.assertEqual(result['life'], 'brain_free')
            self.assertEqual(result['plan']['root'], str(logical))
            self.assertEqual(result['backing_root'], str(backing))
            self.assertTrue(result['at_exact_saved_boundary_now'])
            self.assertEqual(result['boundary_cycle_now'], 55)
            self.assertEqual(json.loads(plan_path.read_text()), plan)


if __name__ == '__main__':
    unittest.main()
