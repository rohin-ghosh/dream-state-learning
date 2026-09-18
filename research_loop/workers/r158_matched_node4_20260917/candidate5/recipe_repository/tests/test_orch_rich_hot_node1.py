from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_rich_hot_node1_run as runner
from gpu import orch_rich_hot_node1_scan as scanner
from organism_v6 import orch_rich_hot_node1 as policy


class Node1Tests(unittest.TestCase):
    def test_actual_uuid_minor_mapping(self):
        self.assertEqual(len(set(policy.UUIDS)), 8)
        self.assertEqual(policy.MINORS, (3, 2, 1, 0, 7, 6, 5, 4))
        self.assertEqual([policy.allocation(index)[0] for index in range(8)],
                         [condition for condition in policy.CONDITIONS for unused in range(2)])
        for invalid in (-1, 8, True, '0'):
            with self.assertRaises(ValueError):
                policy.allocation(invalid)

    def test_lease_margin_and_original_clock(self):
        started = datetime(2026, 9, 15, 4, tzinfo=timezone.utc).timestamp()
        self.assertEqual(policy.deadline(started), started + 43200)
        near_end = policy.LEASE_END - policy.LEASE_MARGIN - 3600
        self.assertEqual(policy.deadline(near_end), policy.LEASE_END - policy.LEASE_MARGIN)
        with self.assertRaises(ValueError):
            policy.deadline(policy.LEASE_END - policy.LEASE_MARGIN - 600)

    def test_prompts_high_budget_own_second_pass(self):
        task = dict(question='What is 2 times 9?', gold='GOLD_NOT_PUBLIC')
        self.assertEqual((policy.CAP, policy.CONTEXT), (8192, 16384))
        for condition in policy.CONDITIONS:
            messages = policy.messages(task, condition)
            self.assertNotIn('GOLD_NOT_PUBLIC', str(messages))
            self.assertNotIn('150–400', str(messages))
        for condition in ('TWO_PASS', 'META_EVALUATE'):
            self.assertEqual(policy.messages(task, condition, 'my actual response')[-2],
                             dict(role='assistant', content='my actual response'))

    def test_unreviewed_output_never_auto_admitted(self):
        response = dict(raw='FINAL: 18', terminal=True, truncated=False, token_ids=[1] * 1000)
        result = policy.outcome(dict(gold='18'), response)
        self.assertTrue(result['correct'])
        self.assertFalse(result['admitted'] or result['trainingAllowed'])
        self.assertEqual(result['semantic_status'], 'UNREVIEWED')

    def snapshot(self):
        return dict(gpu=dict(index=0, uuid=policy.UUIDS[0], minor=3,
            memory_used_mib=0, utilization_percent=0), compute_processes=[], processes=[])

    def test_minor_mapping_drift_blocks_even_idle(self):
        snapshot = self.snapshot()
        self.assertEqual(scanner.evaluate(snapshot, 0), [])
        snapshot['gpu']['minor'] = 0
        self.assertIn('allocation_or_minor_mismatch', scanner.evaluate(snapshot, 0))

    def test_unknown_visibility_device_open_and_cvd_block(self):
        for entry in (dict(pid=20, unreadable=True), dict(pid=20, target_device_open=True),
                      dict(pid=20, cvd=policy.UUIDS[0]), dict(pid=20, cvd='3'),
                      dict(pid=20, cvd='GPU-5b370'), dict(pid=20, cvd='unresolved')):
            snapshot = self.snapshot()
            snapshot['processes'] = [entry]
            self.assertTrue(scanner.evaluate(snapshot, 0))
        snapshot = self.snapshot()
        snapshot['processes'] = [dict(pid=20, target_device_open=True, verified_persistence_service=True)]
        self.assertEqual(scanner.evaluate(snapshot, 0), [])

    def test_other_uuid_not_accidentally_blocked(self):
        snapshot = self.snapshot()
        snapshot['processes'] = [dict(pid=22, cvd=policy.UUIDS[1])]
        self.assertEqual(scanner.evaluate(snapshot, 0), [])

    def test_global_cap_persists(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(policy, 'MAX_CALLS', 2):
                self.assertEqual(runner.reserve(root, {})['global_call'], 1)
                self.assertEqual(runner.reserve(root, {})['global_call'], 2)
                with self.assertRaises(ValueError):
                    runner.reserve(root, {})

    def test_atomic_evidence_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'progress.json'
            runner.write(path, dict(calls=1))
            runner.write(path, dict(calls=2))
            self.assertIn('2', path.read_text())
            self.assertEqual(len(list(path.parent.iterdir())), 1)


if __name__ == '__main__':
    unittest.main()
