import unittest

from fleet_deadlines import annotate_support, runtime_status, support_row, verified


class DeadlineEvidenceTests(unittest.TestCase):
    def test_dead_process_cannot_reuse_a_historical_alive_label(self):
        row = dict(pid=17, source_status='LOADED_ALIVE', alive_now=False, renewal_verified=False)
        self.assertTrue(runtime_status(row).startswith('NOT ALIVE;'))
        row['alive_now'] = None
        self.assertTrue(runtime_status(row).startswith('CURRENT PROCESS NOT VERIFIED;'))

    def test_support_preserves_actual_execution_node_and_bound(self):
        row = support_row(dict(name='bridge', actual_host_alias='operator_vm', pid=17,
            start_ticks=100, actual_deadline='2026-09-20T18:00:00Z'), dict(sha256='receipt'))
        self.assertEqual(row['node'], 'local')
        self.assertEqual(row['start_ticks'], 100)
        self.assertEqual(row['deadline_utc'], '2026-09-20T18:00:00Z')

    def test_live_pid_is_not_same_incarnation_or_parent_delivery(self):
        row = dict(pid=17, start_ticks=100, deadline_utc='2026-09-20T18:00:00Z')
        observation = dict(processes={'17': dict(alive=True, start_ticks='200')})
        annotate_support(row, observation, 1789758000)
        self.assertTrue(row['alive_now'])
        self.assertFalse(row['runtime_identity_and_bound_verified'])
        self.assertFalse(row['parent_delivery_inferred'])
        observation['processes']['17']['start_ticks'] = '100'
        annotate_support(row, observation, 1789758000)
        self.assertTrue(row['runtime_identity_and_bound_verified'])
        annotate_support(row, observation, 1790000000)
        self.assertFalse(row['runtime_identity_and_bound_verified'])

    def test_on_demand_endpoint_is_not_a_running_service(self):
        row = dict(pid=None, deadline_utc=None, status='ON_DEMAND_NOT_PERSISTENT')
        annotate_support(row, dict(processes={}), 1789758000)
        self.assertFalse(row['runtime_identity_and_bound_verified'])

    def test_identical_command_does_not_bind_a_reused_pid(self):
        row = dict(pid=17, start_ticks=100, command_sha256='same-command',
            deadline_utc='2026-09-20T18:00:00Z')
        observation = dict(processes={'17': dict(alive=True, start_ticks='200', command_sha256='same-command')})
        annotate_support(row, observation, 1789758000)
        self.assertFalse(row['identity_matches'])

    def test_dispatch_or_pid_alone_does_not_prove_renewal(self):
        self.assertFalse(verified(dict(alive_now=True, identity_matches=True)))

    def test_requires_both_journal_events_and_current_identity(self):
        row = dict(loaded_index=10, wall_index=9, resident_deadline_utc='2026-09-25T18:00:00Z',
            target_deadline_utc='2026-09-25T18:00:00Z',
            alive_now=True, identity_matches=True)
        self.assertTrue(verified(row))
        for key in row:
            changed = dict(row)
            changed[key] = None
            self.assertFalse(verified(changed))
        self.assertFalse(verified(dict(row, resident_deadline_utc='2026-09-18T18:00:00Z')))
        self.assertFalse(verified(dict(row, resident_deadline_utc='2026-09-26T18:00:00Z')))


if __name__ == '__main__':
    unittest.main()
