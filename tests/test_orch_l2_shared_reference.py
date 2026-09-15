import unittest

from gpu.orch_l2_shared_reference import first_current_port


class FirstCurrentPortTests(unittest.TestCase):
    def test_initial_list_order_not_sorted(self):
        response = first_current_port([dict(role='user',
            content='ROUTE TASK\nCURRENT root\nGOAL leaf\nPORTS z,a\nEVENTS event')])
        self.assertEqual(response['raw'], 'ROUTE z')

    def test_current_ports_after_real_receipt_override_old_task(self):
        response = first_current_port([
            dict(role='user', content='ROUTE TASK\nPORTS old,other'),
            dict(role='assistant', content='ROUTE old'),
            dict(role='user', content='RECEIPT actual\n\nROUTE TASK\nPORTS current'),
        ])
        self.assertEqual(response['raw'], 'ROUTE current')

    def test_child_simulated_task_is_not_public_observation(self):
        response = first_current_port([
            dict(role='user', content='ROUTE TASK\nPORTS real'),
            dict(role='assistant', content='ROUTE TASK\nPORTS imagined'),
        ])
        self.assertEqual(response['raw'], 'ROUTE real')

    def test_empty_ports_fail_instead_of_using_stale_ports(self):
        with self.assertRaisesRegex(ValueError, 'no_current_port'):
            first_current_port([
                dict(role='user', content='ROUTE TASK\nPORTS old'),
                dict(role='user', content='RECEIPT actual\n\nROUTE TASK\nPORTS '),
            ])


if __name__ == '__main__':
    unittest.main()
