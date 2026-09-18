from copy import deepcopy
import unittest

from native_binding import JOURNAL, WALL, verify_loaded


class NativeBindingTests(unittest.TestCase):
    def setUp(self):
        self.binding = dict(journal_id=JOURNAL, pid=10, loaded_index=21,
            loaded_sha256='loaded', wall_index=20, wall_sha256='wall', plan_sha256='plan')
        self.loaded = dict(journal_id=JOURNAL, kind='LOADED', index=21,
            sha256='loaded', document=dict(pid=10, resume=True))
        self.wall = dict(journal_id=JOURNAL, kind='WALL_EXTENDED', index=20,
            sha256='wall', document=dict(plan_sha256='plan', authorization=dict(new_deadline_unix=WALL)))

    def test_actual_resume_and_wall_bound(self):
        verify_loaded(self.binding, self.loaded, self.wall)

    def test_stale_pid_wrong_journal_or_not_resume_rejected(self):
        for key, value in [('pid', 1100592), ('resume', False)]:
            loaded = deepcopy(self.loaded)
            loaded['document'][key] = value
            with self.assertRaises(ValueError):
                verify_loaded(self.binding, loaded, self.wall)
        loaded = dict(self.loaded, journal_id='another-life')
        with self.assertRaises(ValueError):
            verify_loaded(self.binding, loaded, self.wall)

    def test_old_wall_or_mismatched_source_plan_rejected(self):
        for key, value in [('plan_sha256', 'old-plan'), ('authorization', dict(new_deadline_unix=1789754400))]:
            wall = deepcopy(self.wall)
            wall['document'][key] = value
            with self.assertRaises(ValueError):
                verify_loaded(self.binding, self.loaded, wall)


if __name__ == '__main__':
    unittest.main()
