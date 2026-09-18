from copy import deepcopy
import unittest

from c2_parent_binding import CONTROL, JOURNAL, ROOT, SOURCE, WALL, verify_documents
from c2_parent_continue import validate_config_change


class C2ParentContinuationTests(unittest.TestCase):
    def documents(self):
        actual = dict(pid=829798, start_ticks='29168595', uid=2524, cwd=SOURCE,
            argv=['python', 'native', '--config', str(CONTROL / 'GUARD.json')], cgroup='exact')
        plan = dict(root=ROOT, source_root=SOURCE, hard_end_unix=WALL)
        binding = dict(identity=actual, native=dict(pid=829798, start_ticks='29168595'),
            hard_end_unix=WALL, optimizer_steps=7756, plan_sha256='plan',
            loaded=dict(index=11505, sha256='load'), wall_extended=dict(index=11504, sha256='wall'))
        loaded = dict(index=11505, sha256='load', kind='LOADED', journal_id=JOURNAL,
            document=dict(pid=829798, resume=True, optimizer_steps=7756))
        wall = dict(index=11504, sha256='wall', kind='WALL_EXTENDED', journal_id=JOURNAL,
            document=dict(plan_sha256='plan', authorization=dict(new_deadline_unix=WALL)))
        return binding, plan, deepcopy(actual), loaded, wall

    def test_actual_long_bound_incarnation_accepted(self):
        verify_documents(*self.documents(), WALL - 100)

    def test_pid_reuse_optimizer_or_wall_mismatch_rejected(self):
        for field in ('pid', 'optimizer', 'wall', 'journal'):
            with self.subTest(field=field):
                binding, plan, actual, loaded, wall = self.documents()
                if field == 'pid':
                    actual['start_ticks'] = 'stale'
                elif field == 'optimizer':
                    loaded['document']['optimizer_steps'] -= 1
                elif field == 'wall':
                    plan['hard_end_unix'] -= 1
                else:
                    loaded['journal_id'] = 'another-life'
                with self.assertRaises(ValueError):
                    verify_documents(binding, plan, actual, loaded, wall, WALL - 100)

    def test_expired_binding_rejected(self):
        with self.assertRaises(ValueError):
            verify_documents(*self.documents(), WALL)

    def test_cpu_change_preserves_parent_behavior_and_cursor(self):
        old = dict(hard_end_unix=1789776000, start_after_response_count=289,
            root=ROOT, cadence_responses=1, parent_style='same', source_root=SOURCE)
        new = dict(old, hard_end_unix=WALL, start_after_response_count=408)
        validate_config_change(old, new)
        for change in (dict(parent_style='new'), dict(start_after_response_count=1), dict(root='/other')):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_config_change(old, dict(new, **change))


if __name__ == '__main__':
    unittest.main()
