import copy
import unittest

import p3_finish_recovery as recovery


class FinishRecoveryTests(unittest.TestCase):
    def test_dispatch_is_not_permission_to_attach_parent(self):
        self.assertFalse(recovery.ready(dict(status='DISPATCHED_LOAD_PENDING')))

    def test_requires_matching_actual_pid_load_and_lease(self):
        evidence = dict(status='LOADED_ALIVE_WALL_EXTENDED', native=dict(pid=900),
            loaded=dict(index=55), binding=dict(pid=900, loaded_index=55,
                hard_end_unix=recovery.END_UNIX))
        self.assertTrue(recovery.ready(evidence))
        for field, value in (('pid', 901), ('loaded_index', 54), ('hard_end_unix', 1)):
            changed = copy.deepcopy(evidence)
            changed['binding'][field] = value
            self.assertFalse(recovery.ready(changed))


if __name__ == '__main__':
    unittest.main()
