"""Pure replay layout for a prospectively bound successor to the SEQ266 recipe.

This does not admit material, select an initial adapter, run training, or
validate a closed loop. The historical native driver remains unchanged.
"""

from dataclasses import dataclass


GROUPS = ('memory_rows', 'cue_rows', 'audit_rows', 'trajectory_rows', 'new_trajectory_rows')
LEGACY_SIZES = (128, 20, 62, 12)
ARMS = ('FULL_TARGET', 'NEW_TRAJECTORY_LOSS_OFF')


@dataclass(frozen=True)
class GoalReplayLayout:
    new_trajectory_rows: int
    trajectory_presentations: int = 4

    def __post_init__(self):
        for name in ('new_trajectory_rows', 'trajectory_presentations'):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(name + '_must_be_positive_integer')
        if self.trajectory_rows * self.trajectory_presentations % 2:
            raise ValueError('two_trajectory_slots_require_even_total_presentations')

    @property
    def group_sizes(self):
        return LEGACY_SIZES + (self.new_trajectory_rows,)

    @property
    def row_count(self):
        return sum(self.group_sizes)

    @property
    def trajectory_rows(self):
        return LEGACY_SIZES[-1] + self.new_trajectory_rows

    @property
    def updates(self):
        return self.trajectory_rows * self.trajectory_presentations // 2

    def training_indexes(self, update):
        if type(update) is not int or not 1 <= update <= self.updates:
            raise ValueError('update_outside_declared_replay_layout')
        offset = update - 1
        memory_count = LEGACY_SIZES[0]
        behavior_count = sum(LEGACY_SIZES[1:3])
        trajectory_start = memory_count + behavior_count
        return (offset % memory_count,
                memory_count + offset % behavior_count,
                trajectory_start + (2 * offset) % self.trajectory_rows,
                trajectory_start + (2 * offset + 1) % self.trajectory_rows)

    def masked_row_indexes(self, arm):
        if arm not in ARMS:
            raise ValueError('unknown_replay_arm')
        return tuple(range(sum(LEGACY_SIZES), self.row_count)) if arm == ARMS[1] else ()

    def presentation_counts(self):
        memory_count = LEGACY_SIZES[0]
        behavior_count = sum(LEGACY_SIZES[1:3])
        memory = tuple(self.updates // memory_count + int(index < self.updates % memory_count)
                       for index in range(memory_count))
        behavior = tuple(self.updates // behavior_count + int(index < self.updates % behavior_count)
                         for index in range(behavior_count))
        return memory + behavior + (self.trajectory_presentations,) * self.trajectory_rows

    def manifest(self, arm):
        masked = self.masked_row_indexes(arm)
        return dict(schema='GOAL_REPLAY_LAYOUT_V1', arm=arm,
                    group_order=list(GROUPS), group_sizes=list(self.group_sizes),
                    encoded_rows=self.row_count, batch_size=4, updates=self.updates,
                    trajectory_presentations=self.trajectory_presentations,
                    masked_row_indexes=list(masked),
                    row_presentations=list(self.presentation_counts()),
                    old_memory_presentations=self.updates,
                    old_behavior_presentations=self.updates,
                    old_trajectory_presentations=LEGACY_SIZES[-1] * self.trajectory_presentations,
                    new_target_presentations=self.new_trajectory_rows * self.trajectory_presentations,
                    new_supervised_presentations=0 if masked else self.new_trajectory_rows * self.trajectory_presentations)
