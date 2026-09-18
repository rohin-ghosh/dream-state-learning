"""CPU-only receipt interpretation; no live training changes or private inputs."""

import copy
import unittest

from observe_r210 import checkpoint_coverage, clarify_continuity


class ContinuityReceiptTests(unittest.TestCase):
    def arm(self):
        return dict(live=True, receipts={
            'R210_TRANSITION.json': dict(resume_step=145, discarded_documented_updates=485,
                discarded_documented_pair_draws=31040, additional_unlogged_completed_updates_bounds=[0, 10],
                additional_inflight_work_possible=True, no_weights_or_optimizer_reset=True),
            'training/LOADED.json': dict(loaded_unix=1789708353.7260275),
            'training/NEW_MIX_STARTED.json': dict(started_unix=1789708357.6139474),
        }, latest_update=dict(completed_updates=280, pair_types={
            'CROSSED_SCENE_ASSUMPTION': 16, 'WITHIN_CONTEST_OBSERVED': 48}))

    def test_same_checkpoint_does_not_claim_uninterrupted_continuity(self):
        arm = self.arm()
        original = copy.deepcopy(arm['receipts'])
        clarify_continuity(arm)
        self.assertFalse(arm['continuity']['uninterrupted_continuity'])
        self.assertTrue(arm['continuity']['rollback_to_saved_checkpoint'])
        self.assertEqual(arm['continuity']['discarded_documented_updates'], 485)
        self.assertEqual(arm['continuity']['additional_unlogged_completed_updates_bounds'], [0, 10])
        self.assertEqual(arm['receipts'], original)

    def test_fraction_is_observed_not_declared(self):
        arm = self.arm()
        arm['latest_update']['pair_types'] = dict(CROSSED_SCENE_ASSUMPTION=8, WITHIN_CONTEST_OBSERVED=56)
        clarify_continuity(arm)
        self.assertEqual(arm['live_crossed_fraction'], 0.125)
        self.assertEqual(arm['live_crossed_fraction_denominator']['total'], 64)

    def test_missing_or_inactive_update_has_no_live_fraction(self):
        for missing in [True, False]:
            arm = self.arm()
            if missing:
                del arm['latest_update']
            else:
                arm['live'] = False
            clarify_continuity(arm)
            self.assertIsNone(arm['live_crossed_fraction'])

    def test_loaded_and_mixed_timestamps_are_distinct(self):
        arm = self.arm()
        clarify_continuity(arm)
        self.assertEqual(arm['loaded_utc'], '2026-09-18T05:12:33.726027+00:00')
        self.assertEqual(arm['first_mix_utc'], '2026-09-18T05:12:37.613947+00:00')


class CheckpointCoverageTests(unittest.TestCase):
    def arm(self):
        return dict(full_state_checkpoints=[dict(path='checkpoint146', optimizer_step=146,
            all_four_rank_states_present=True, adapter_present=True)], diagnostics=[dict(phase='R210_MIX',
            optimizer_step=146, selection_Spearman=0.27,
            contrast_by_type={kind: dict(scored=100) for kind in range(6)})])

    def test_all_saved_states_are_diagnosed(self):
        arm = self.arm()
        checkpoint_coverage(arm)
        self.assertEqual(arm['checkpoint_diagnostic_coverage']['diagnosed_full_states'], 1)
        self.assertEqual(arm['checkpoint_diagnostic_coverage']['saved_steps_without_complete_diagnostics'], [])

    def test_saved_state_missing_diagnostic_not_silently_omitted(self):
        arm = self.arm()
        arm['diagnostics'][0]['contrast_by_type'][0]['scored'] = 99
        checkpoint_coverage(arm)
        self.assertEqual(arm['checkpoint_diagnostic_coverage']['saved_steps_without_complete_diagnostics'], [146])

    def test_incomplete_checkpoint_is_reported_not_relaunched(self):
        arm = self.arm()
        arm['full_state_checkpoints'][0]['all_four_rank_states_present'] = False
        checkpoint_coverage(arm)
        self.assertEqual(arm['checkpoint_diagnostic_coverage']['incomplete_state_directories'], ['checkpoint146'])
        self.assertTrue(arm['checkpoint_diagnostic_coverage']['pending_receipt_is_not_launch_authorization'])


if __name__ == '__main__':
    unittest.main()
