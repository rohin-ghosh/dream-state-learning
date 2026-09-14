"""CPU-only schedule parity and dose checks; never construct a model."""

from collections import Counter
from dataclasses import FrozenInstanceError
import unittest

from gpu import astra_goal_quality_train as frozen_runner
from organism_v6.experienced_event_goal_replay_layout import ARMS, GoalReplayLayout


class GoalReplayLayoutTests(unittest.TestCase):
    def test_exact_seq266_schedule_and_manifest_parity(self):
        layout = GoalReplayLayout(1452)
        self.assertEqual(layout.updates, frozen_runner.UPDATES)
        self.assertEqual(layout.group_sizes, frozen_runner.GROUP_SIZES)
        for update in range(1, layout.updates + 1):
            self.assertEqual(layout.training_indexes(update), frozen_runner.training_indexes(update))
        for arm in ARMS:
            actual, frozen = layout.manifest(arm), frozen_runner.recipe(arm)
            for field in ('arm', 'group_order', 'group_sizes', 'encoded_rows', 'batch_size',
                          'updates', 'masked_row_indexes', 'old_memory_presentations',
                          'old_behavior_presentations', 'old_trajectory_presentations',
                          'new_target_presentations', 'new_supervised_presentations'):
                self.assertEqual(actual[field], frozen[field], field)
        self.assertEqual(layout.presentation_counts()[222:], (4,) * 1452)

    def test_variable_corpus_sizes_have_exact_dose(self):
        for new_rows in (1, 2, 17, 1000, 1452, 5000):
            for presentations in (4, 16):
                with self.subTest(new_rows=new_rows, presentations=presentations):
                    layout = GoalReplayLayout(new_rows, presentations)
                    counts = Counter()
                    for update in range(1, layout.updates + 1):
                        indexes = layout.training_indexes(update)
                        self.assertEqual(len(indexes), 4)
                        self.assertTrue(0 <= indexes[0] < 128)
                        self.assertTrue(128 <= indexes[1] < 210)
                        self.assertTrue(all(210 <= index < layout.row_count for index in indexes[2:]))
                        counts.update(indexes)
                    self.assertEqual(tuple(counts[index] for index in range(layout.row_count)),
                                     layout.presentation_counts())
                    self.assertEqual(tuple(counts[index] for index in range(210, layout.row_count)),
                                     (presentations,) * layout.trajectory_rows)
                    self.assertEqual(sum(counts.values()), layout.updates * 4)

    def test_sixteen_is_four_times_executed_dose_not_default(self):
        original, higher = GoalReplayLayout(1452), GoalReplayLayout(1452, 16)
        self.assertEqual((original.updates, higher.updates), (2928, 11712))
        self.assertEqual(higher.manifest(ARMS[0])['new_target_presentations'], 4 * 5808)

    def test_loss_off_masks_only_new_targets(self):
        for new_rows in (1, 17, 1452):
            layout = GoalReplayLayout(new_rows)
            self.assertEqual(layout.masked_row_indexes(ARMS[0]), ())
            self.assertEqual(layout.masked_row_indexes(ARMS[1]), tuple(range(222, 222 + new_rows)))
            self.assertEqual(layout.manifest(ARMS[1])['new_supervised_presentations'], 0)
            self.assertEqual(layout.manifest(ARMS[1])['row_presentations'],
                             layout.manifest(ARMS[0])['row_presentations'])

    def test_bad_counts_and_incomplete_cycles_are_rejected(self):
        for invalid in (True, False, 0, -1, 2.0, '2', None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    GoalReplayLayout(invalid)
                with self.assertRaises(ValueError):
                    GoalReplayLayout(1452, invalid)
        with self.assertRaisesRegex(ValueError, 'even_total'):
            GoalReplayLayout(1, 1)
        self.assertEqual(GoalReplayLayout(2, 1).updates, 7)

    def test_bad_update_and_arm_are_rejected(self):
        layout = GoalReplayLayout(1)
        for invalid in (True, 0, -1, layout.updates + 1, 1.0, '1', None):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                layout.training_indexes(invalid)
        for invalid in ('full', '', None):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                layout.manifest(invalid)

    def test_layout_is_immutable_and_manifest_detached(self):
        layout = GoalReplayLayout(17)
        with self.assertRaises(FrozenInstanceError):
            layout.new_trajectory_rows = 99
        manifest = layout.manifest(ARMS[1])
        manifest['group_sizes'][-1] = 99
        manifest['row_presentations'].clear()
        self.assertEqual(layout.group_sizes[-1], 17)
        self.assertEqual(len(layout.presentation_counts()), 239)


if __name__ == '__main__':
    unittest.main()
