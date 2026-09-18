import unittest

from fleet_deadlines import actual_parent_delivery, annotate_support, checkpoint_tail_entry, checkpoint_tail_parent_support, runtime_status, support_row, verified


class DeadlineEvidenceTests(unittest.TestCase):
    def test_successor_parent_requires_START_and_matching_native(self):
        native = dict(native=dict(pid=17, start_ticks='100'), loaded=dict(index=12, sha256='load'),
            guard_sha256='guard', hard_end_unix=1789927200)
        binding = dict(schema='R233_C2_PARENT_ACTUAL_CONTINUATION_V1', native=native['native'],
            native_loaded=native['loaded'], guard_sha256='guard', hard_end_unix=1789927200,
            parent=dict(pid=29, start_ticks='200'), parent_started_utc='2026-09-18T21:11:44Z',
            parent_started_receipt_sha256='a' * 64)
        support = checkpoint_tail_parent_support(binding, native, {})
        self.assertEqual(support['pid'], 29)
        self.assertEqual(support['start_ticks'], '200')
        self.assertNotIn('parent_delivery', support)
        for change in (dict(native=dict(pid=18, start_ticks='100')),
                dict(native_loaded=dict(index=13, sha256='other')),
                dict(guard_sha256='other'), dict(parent_started_receipt_sha256=''),
                dict(parent_started_utc=None), dict(parent=dict(pid=29))):
            with self.assertRaisesRegex(ValueError, 'actual_C2_parent_START'):
                checkpoint_tail_parent_support(dict(binding, **change), native, {})

    def test_parent_publication_is_not_render_or_ACT(self):
        delivery=dict(status='REQUEST_TO_COMMITTED_ACT_OBSERVED',request_index=12,act_index=14,
            committed_index=15,inbox_id='confirmed')
        self.assertEqual(actual_parent_delivery(delivery,10,{})['act_index'],14)
        self.assertIsNone(actual_parent_delivery(dict(delivery,status='PUBLISHED'),10,{}))
        self.assertIsNone(actual_parent_delivery(delivery,13,{}))
        self.assertIsNone(actual_parent_delivery(dict(delivery,committed_index=13),10,{}))

    def test_checkpoint_tail_replaces_obsolete_replay_identity_only_with_actual_receipt(self):
        binding = dict(status='LOADED', journal_id='260be8b8710a42559b291797c6e14983',
            complete_index=11502, complete_sha256='9c59fe6c59a01948b6ffe894aaa681010346ccc671c2f774a10fe7399a49080f',
            optimizer_steps=7756, wall_extended=dict(index=11504), loaded=dict(index=11505),
            native=dict(pid=1139778), hard_end_unix=1789927200, guard_sha256='verified',
            loaded_unix=1789764814.6953828)
        replacement = checkpoint_tail_entry(dict(native=dict(pid=829798)), binding)
        self.assertEqual(replacement['native']['pid'], 1139778)
        self.assertAlmostEqual(replacement['recorded_exit_to_loaded_seconds'], 8713.273545, places=4)
        for change in (dict(status='DISPATCHED'), dict(optimizer_steps=0),
                dict(journal_id='other'), dict(loaded=dict(index=11503))):
            with self.assertRaisesRegex(ValueError, 'exact_C2_checkpoint_tail_LOAD'):
                checkpoint_tail_entry({}, dict(binding, **change))

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

    def test_replay_process_is_not_reported_as_a_restored_life(self):
        row = dict(pid=17, source_status='NATIVE_REPLAY_NOT_LOADED', alive_now=True,
            loaded_index=None, renewal_verified=False)
        self.assertEqual(runtime_status(row), 'REPLAY PROCESS ALIVE; renewed LOAD not observed')
        row['alive_now'] = False
        self.assertTrue(runtime_status(row).startswith('NOT ALIVE;'))

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
