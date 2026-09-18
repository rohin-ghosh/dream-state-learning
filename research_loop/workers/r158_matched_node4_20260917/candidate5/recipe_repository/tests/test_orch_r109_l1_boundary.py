import unittest

from gpu.orch_r109_l1_boundary import boundary


class BoundaryTests(unittest.TestCase):
    def test_never_releases_pending_native_call(self):
        self.assertEqual(boundary([dict(index=5,global_call=1)],[],5),'PENDING_CALL')

    def test_allows_required_second_pass(self):
        row=dict(index=5,global_call=1,task_id='train',stage='source')
        self.assertEqual(boundary([row],[row],5),'ALLOW_REQUIRED_SECOND_PASS')

    def test_complete_pair_is_not_new_reservation(self):
        rows=[dict(index=5,global_call=1,task_id='train',stage='source'),
              dict(index=5,global_call=2,task_id='train',stage='own_second_pass')]
        self.assertEqual(boundary(rows,rows,5),'COMPLETE_PAIR_BOUNDARY')
        self.assertEqual(boundary(rows+[dict(index=5,global_call=3)],rows,5),'PENDING_CALL')

    def test_other_lane_does_not_authorize_target(self):
        row=dict(index=4,global_call=1,task_id='train',stage='source')
        self.assertEqual(boundary([row],[],5),'ALLOW_REQUIRED_SECOND_PASS')


if __name__=='__main__':
    unittest.main()
