import unittest

from gpu import orch_r119_grid_shared_continue as subject


class SharedClockTests(unittest.TestCase):
    def test_only_authorized_clock_and_wait_change(self):
        old = dict(hard_end_unix=10, train_end_unix=8, final_unix=9, max_native_calls=1858,
                   max_parent_calls=298, physical=7, parent_wait_seconds=120)
        changed = subject.overlay(old, dict(hard_end_unix=100, train_end_unix=98))
        self.assertEqual(changed['max_native_calls'], 1858)
        self.assertEqual(changed['max_parent_calls'], 298)
        self.assertEqual(changed['final_unix'], 9)
        self.assertEqual(changed['parent_wait_seconds'], 600)
        self.assertEqual(old['hard_end_unix'], 10)

    def test_only_original_two_grid_FINAL_refs(self):
        self.assertEqual(set(subject.FINAL_SHAS), {'F4', 'A4'})
        self.assertTrue(all(len(digest) == 64 for digest in subject.FINAL_SHAS.values()))

    def test_clock_backend_is_not_old_c56(self):
        self.assertEqual(subject.BACKEND_SHA, '33a30aa1793a053ca603a9c3e2c4e5fde477b35b99d858af87dfa980036a065c')


if __name__ == '__main__':
    unittest.main()
