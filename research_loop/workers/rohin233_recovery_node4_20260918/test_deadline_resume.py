import unittest

from deadline_resume import deadline_plan


class DeadlineTests(unittest.TestCase):
    def test_only_authorized_deadline_changes_not_policy(self):
        old = dict(hard_end_unix=100, lease_end_unix=200, root='/same/life',
            think_act_learn=dict(language_target_policy='same', decoder='same'), optimizer='same')
        result = deadline_plan(old, 'a' * 64, 1000, 22600)
        self.assertEqual(result['think_act_learn'], old['think_act_learn'])
        self.assertEqual(old['hard_end_unix'], 100)
        self.assertEqual(result['authorized_wall_extension']['previous_stream_sha256'], 'a' * 64)

    def test_wrong_margin_and_shorter_wall_rejected(self):
        old = dict(hard_end_unix=100, lease_end_unix=200)
        for wall, ceiling in ((99, 21699), (1000, 2000)):
            with self.assertRaises(ValueError):
                deadline_plan(old, 'a' * 64, wall, ceiling)


if __name__ == '__main__':
    unittest.main()
