from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

import recovery
import recovery_serial
import recovery_services
from recovery_runtime import entrypoint, CAPTIONS, MATH


class RecoveryTests(unittest.TestCase):
    def test_current_control_never_selects_retired_or_other_life(self):
        arm = Path('/owned/r213_math_a')
        with patch('recovery.read', return_value=dict(control='/owned/frozen_c2/control')):
            self.assertEqual(recovery.current_control(arm), arm / ('control_' + recovery.PHASE))
        selected = arm / ('control_' + recovery.PHASE + '_admission_retry1')
        with patch('recovery.read', return_value=dict(control=str(selected))):
            self.assertEqual(recovery.current_control(arm), selected)

    def test_serial_order_is_only_eight_kept_lives(self):
        self.assertEqual(set(recovery_serial.ORDER), set(recovery.PROTECTED))
        self.assertEqual(len(recovery_serial.ORDER), 8)
        self.assertEqual(recovery_serial.ORDER[0], 'r213_math_c')

    def test_boundary_admission_retry_selected_without_alias(self):
        arm = Path('/owned/r213_r226_caption_perspective_fork')
        selected = arm / ('control_' + recovery.PHASE + '_boundary_lease_ceiling_admission_retry1')
        with patch('recovery.read', return_value=dict(control=str(selected))):
            self.assertEqual(recovery.current_control(arm), selected)

    def test_admission_retry_bound_to_current_source_once_only(self):
        arm = Path('/owned/r213_r226_caption_perspective_fork')
        for suffix in ('', '_boundary_lease_ceiling'):
            control = arm / ('control_' + recovery.PHASE + suffix)
            source = arm / ('source_' + recovery.PHASE + suffix)
            with patch('recovery.current_control', return_value=control), \
                    patch('recovery.read', return_value=dict(source_root=str(source))):
                self.assertEqual(recovery.admission_retry_paths(arm), (control, source))
            with patch('recovery.current_control', return_value=control), \
                    patch('recovery.read', return_value=dict(source_root='/other/life/source')):
                with self.assertRaisesRegex(ValueError, 'same_owned_source'):
                    recovery.admission_retry_paths(arm)
        with patch('recovery.current_control', return_value=control.with_name(control.name + '_admission_retry1')):
            with self.assertRaisesRegex(ValueError, 'single_admission_retry_only'):
                recovery.admission_retry_paths(arm)

    def test_serial_requires_policy_at_both_levels(self):
        policy = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
        with patch('pathlib.Path.read_bytes', side_effect=[
                b'{"policy":"R227_ALL_AUTHENTIC_CHILD_ROWS_V1"}',
                b'{"learn_row_policy":"R227_ALL_AUTHENTIC_CHILD_ROWS_V1","think_act_learn":{}}']):
            with self.assertRaisesRegex(ValueError, 'R227_policy_required'):
                recovery_serial.require_policy(Path('/owned/control'))
        with patch('recovery_serial.json.loads', side_effect=[dict(policy=policy),
                dict(learn_row_policy=policy, think_act_learn=dict(learn_row_policy=policy))]), \
                patch('pathlib.Path.read_bytes', return_value=b'{}'):
            recovery_serial.require_policy(Path('/owned/control'))

    def test_policy_retry_refuses_active_life(self):
        with patch('recovery.inactive', side_effect=ValueError('native_alive')), \
                patch('recovery.adopt_policy') as adopt:
            with self.assertRaisesRegex(ValueError, 'native_alive'):
                recovery.retry_policy(Path('/owned'), 'r213_math_a', '/python')
            adopt.assert_not_called()

    def test_conservative_user_date_ceiling_and_existing_reservation(self):
        observed = recovery.datetime(2026, 9, 18, tzinfo=recovery.timezone.utc).timestamp()
        receipt = recovery.datetime(2026, 9, 26, 3, 3, tzinfo=recovery.timezone.utc).timestamp()
        expected = recovery.datetime(2026, 9, 24, 18, tzinfo=recovery.timezone.utc).timestamp()
        self.assertEqual(recovery.conservative_ceiling(dict(lease_end_unix=receipt),
            dict(next_reserved_unix=receipt), observed), expected)
        self.assertEqual(recovery.conservative_ceiling(dict(lease_end_unix=receipt),
            dict(next_reserved_unix=observed + 86400), observed), observed + 64800)
        with patch('recovery.inactive', side_effect=ValueError('native_alive')):
            with self.assertRaisesRegex(ValueError, 'native_alive'):
                recovery.extend_prepared(Path('/owned'), 'r213_math_c', '/python')

    def test_derived_operator_budget_preserves_original_lease_evidence(self):
        original = dict(lease_end_unix=100000, hard_end_unix=20000,
            operator_screen_cap_seconds=43200, evidence=dict(source='unchanged'))
        snapshot = deepcopy(original)
        extended = recovery.derived_budget_lease(original, 70000, 'prior-sha')
        self.assertEqual(original, snapshot)
        self.assertEqual(extended['evidence'], original['evidence'])
        self.assertEqual(extended['lease_end_unix'], original['lease_end_unix'])
        self.assertFalse(extended['actual_physical_lease_changed'])
        self.assertIsNone(extended['operator_screen_cap_seconds'])
        with self.assertRaisesRegex(ValueError, 'physical_lease_margin'):
            recovery.derived_budget_lease(original, 90000, 'prior-sha')

    def test_services_do_not_duplicate_existing_attachment(self):
        with patch('pathlib.Path.exists', return_value=True), patch('recovery_services.subprocess.Popen') as process:
            with self.assertRaisesRegex(ValueError, 'no_duplicate_service_attachment'):
                recovery_services.start(Path('/owned'), 'feedback', [], Path('/source'), {})
            process.assert_not_called()

    def test_parent_wait_is_for_exact_required_lives_not_total_count(self):
        proof = dict(lives=[dict(life='r213_math_a', status='LOADED_ALIVE')])
        with patch('recovery_services.project', return_value=proof), \
                patch('pathlib.Path.write_text'), patch('pathlib.Path.replace'), \
                patch('recovery_services.time.time', return_value=1):
            self.assertEqual(recovery_services.wait_for(Path('/root'), Path('/output'), 2,
                ('r213_math_a',)), proof)

    def test_reconcile_and_launch_are_separate_operations(self):
        with patch('recovery.inactive', side_effect=ValueError('not_inactive')), patch('recovery.subprocess.Popen') as process:
            with self.assertRaisesRegex(ValueError, 'not_inactive'):
                recovery.launch(Path('/owned'), 'r213_math_a', '/python')
            process.assert_not_called()

    def test_offline_replay_preserves_confined_inbox_namespace(self):
        self.assertEqual(recovery.offline_inbox(dict(root='/original/confined/life')),
            Path('/original/confined/life/stream/inbox'))

    def test_exact_eight_devices(self):
        for name, device in dict(CAPTIONS, **MATH).items():
            self.assertIn(entrypoint(dict(source_root='/owned/' + name + '/source_new', physical=device)),
                ('gpu.r227_caption_runtime', 'gpu.r226_math_runtime'))
            with self.assertRaises(ValueError):
                entrypoint(dict(source_root='/owned/' + name + '/source_new', physical=(device + 1) % 8))

    def test_retired_aliases_forbidden(self):
        for name in ('conversational', 'p32', 'peer_math', 'r213_siege_envoy_fork', 'frozen_c2'):
            with self.assertRaises(ValueError):
                entrypoint(dict(source_root='/owned/' + name + '/source_new', physical=0))

    def test_wall_obeys_existing_lease_and_reservation(self):
        plan = dict(lease_end_unix=100000)
        self.assertEqual(recovery.checked_deadline(plan, dict(next_reserved_unix=99999), 1000), 44200)
        self.assertEqual(recovery.checked_deadline(plan, dict(next_reserved_unix=5000), 1000), 4880)
        with self.assertRaises(ValueError):
            recovery.checked_deadline(plan, dict(next_reserved_unix=2000), 1000)
        with self.assertRaises(ValueError):
            recovery.checked_deadline(plan, dict(next_reserved_unix=99999), 1000, 999999)

    def test_plan_changes_only_location_and_wall(self):
        original = dict(source_root='/owned/r213_math_a/source_old', physical=1, hard_end_unix=10,
            root='/namespace/original', new_presentations=16,
            startup_context=dict(path='/owned/r213_math_a/source_old/context/start.md', sha256='fixed'),
            think_act_learn=dict(prose_target_filter='unchanged', environment_facts='unchanged'),
            birth_prompt='unchanged')
        snapshot = deepcopy(original)
        changed = recovery.relocated_plan(original, Path('/owned/r213_math_a/source_new'), 20)
        self.assertEqual(original, snapshot)
        self.assertEqual(changed['root'], original['root'])
        self.assertEqual(changed['think_act_learn'], original['think_act_learn'])
        self.assertEqual(changed['birth_prompt'], original['birth_prompt'])
        self.assertEqual(changed['startup_context']['sha256'], 'fixed')
        self.assertEqual(changed['hard_end_unix'], 20)
        self.assertEqual(changed['new_presentations'], 16)

    def test_no_overlapping_recovery_protocols(self):
        for field in ('preupdate_recovery', 'authorized_wall_extension'):
            with self.assertRaises(ValueError):
                recovery.relocated_plan(dict(source_root='/owned/r213_math_a/old', physical=1,
                    **{field: {}}), Path('/owned/r213_math_a/new'), 20)


if __name__ == '__main__':
    unittest.main()
