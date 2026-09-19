from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

from binding_candidate import BoundHelper, FIELDS, MEMBERS, TARGET, provider_disposition, validate_cohort


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'r233_recovery_parents_v4'))
import classroom


def fixture():
    cohort = {name: dict(state='EXPECTED_DOWN', native_matches=[], compute_pids=[],
        legacy_pid_exists=False, old_binding_sha256=name, active_sha256=name) for name in MEMBERS}
    cohort[TARGET] = dict({field: field for field in FIELDS}, state='LOADED_ALIVE',
        pid=101, uid=2524, physical=2, status='S', native_matches=[101], compute_pids=[101],
        source='/owned/MathB/source', guard_path='/owned/MathB/control/GUARD_BUILDER1450.json',
        loaded_index=9609, loaded_sha256='loaded')
    original = SimpleNamespace(unchanged='original_helper_method')
    old = {name: dict(native_pid=0, source='/old/' + name, loaded={}) for name in MEMBERS}
    target = dict(native_pid=101, source=cohort[TARGET]['source'],
        guard_path=cohort[TARGET]['guard_path'], loaded=dict(index=9609, sha256='loaded'))
    current = deepcopy(cohort)
    proxy = BoundHelper(original, Path('/owned'), cohort, old, target, lambda: current)
    return cohort, current, proxy


class BindingTests(unittest.TestCase):
    def test_original_default_guard_rejects_partial(self):
        expected, current, helper = fixture()
        with patch('classroom.importlib.import_module', return_value=helper):
            with self.assertRaisesRegex(ValueError, 'all seven'):
                classroom.load_helpers(Path('/owned'), dict(helper_pins={}, helper_directory='frozen'))

    def test_original_recovering_guard_accepts_one_real_target(self):
        expected, current, helper = fixture()
        with patch('classroom.importlib.import_module', return_value=helper):
            unused, bindings = classroom.load_helpers(Path('/owned'),
                dict(helper_pins={}, helper_directory='frozen'), recovering=True)
        self.assertEqual(set(bindings), set(MEMBERS))
        self.assertEqual([name for name, binding in bindings.items() if helper.alive(binding)], [TARGET])

    def test_recovering_requires_resume_of_old_parent_state(self):
        with self.assertRaisesRegex(ValueError, 'preserved_parent_state'):
            classroom.serve(None, None, {}, recovering=True)

    def test_dead_target_rejected(self):
        expected, current, helper = fixture()
        current[TARGET]['state'] = 'EXPECTED_DOWN'
        with self.assertRaises(ValueError):
            helper.bind(Path('/owned'), TARGET)

    def test_each_target_identity_change_rejected(self):
        for field in FIELDS:
            with self.subTest(field=field):
                expected, current, helper = fixture()
                current[TARGET][field] = 'changed'
                with self.assertRaises(ValueError):
                    helper.bind(Path('/owned'), TARGET)

    def test_other_native_waking_requires_new_cohort_binding(self):
        expected, current, helper = fixture()
        current['r213_math_a']['native_matches'] = [202]
        with self.assertRaises(ValueError):
            helper.check()

    def test_other_gpu_occupied_is_not_down(self):
        expected, current, helper = fixture()
        current['r213_math_c']['compute_pids'] = [202]
        with self.assertRaises(ValueError):
            helper.check()

    def test_reused_down_pid_not_ignored(self):
        expected, current, helper = fixture()
        current['r213_math_a']['legacy_pid_exists'] = True
        with self.assertRaises(ValueError):
            helper.check()

    def test_other_binding_change_rejected(self):
        expected, current, helper = fixture()
        current['r213_math_c']['active_sha256'] = 'changed'
        with self.assertRaises(ValueError):
            helper.check()

    def test_no_false_alive_down_member(self):
        expected, current, helper = fixture()
        for name in MEMBERS:
            self.assertEqual(helper.alive(helper.bind(Path('/owned'), name)), name == TARGET)

    def test_mutated_binding_rejected(self):
        expected, current, helper = fixture()
        bound = helper.bind(Path('/owned'), TARGET)
        bound['native_pid'] = 999
        with self.assertRaises(ValueError):
            helper.alive(bound)

    def test_no_extra_member_or_other_root(self):
        expected, current, helper = fixture()
        for root, name in ((Path('/other'), TARGET), (Path('/owned'), 'r213_r226_caption_unparented_fork')):
            with self.assertRaises(ValueError):
                helper.bind(root, name)

    def test_publish_target_fence(self):
        expected, current, helper = fixture()
        helper.allow_target(TARGET)
        for name in MEMBERS:
            if name != TARGET:
                with self.assertRaises(ValueError):
                    helper.allow_target(name)

    def test_unrelated_helper_behavior_unchanged(self):
        expected, current, helper = fixture()
        self.assertEqual(helper.unchanged, 'original_helper_method')

    def test_pending_budget_and_turn_are_not_reset(self):
        ledger = dict(cumulative_usage_complete=False, cumulative_usage={'total_tokens': 1234},
            pending_request_sha256='pending', next_turn=32, service_end_unix=1790272800,
            ledger_sha256='ledger', pending_result_authenticated=False)
        before = deepcopy(ledger)
        result = provider_disposition(ledger)
        self.assertEqual(ledger, before)
        self.assertEqual(result['prior_usage'], ledger['cumulative_usage'])
        self.assertEqual(result['next_turn'], 32)
        self.assertEqual(result['new_provider_calls'], 0)
        self.assertFalse(result['cumulative_budget_reset'])
        self.assertFalse(result['provider_retry_allowed'])
        ledger['http_status'] = 401
        self.assertEqual(provider_disposition(ledger)['status'], 'AUTH401_TERMINAL_NO_NEW_REQUEST_OR_RETRY')

    def test_existing_result_is_not_publication_authority(self):
        ledger = dict(cumulative_usage_complete=True, cumulative_usage={}, pending_request_sha256='p',
            next_turn=32, service_end_unix=1790272800, ledger_sha256='l', pending_result_authenticated=True)
        result = provider_disposition(ledger)
        self.assertIn('REQUIRES_MAIN_PUBLICATION_AUTHORIZATION', result['status'])
        self.assertEqual(result['new_provider_calls'], 0)


if __name__ == '__main__':
    unittest.main()
