import json
from pathlib import Path
import sys
import unittest

from gpu import orch_r119_grid_lease_budget as subject


class LeaseBudgetTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(kind='NATIVE', number=1), dict(kind='PARENT', number=1)]
        self.raw = b''.join((json.dumps(row) + '\n').encode() for row in self.rows)
        self.values = dict(root='/life', ledger_bytes=self.raw, rows=self.rows,
            config_sha256='a' * 64, lease_end=200000, hard_end=178400)
        self.document = subject.authorize(**self.values, now=1000)

    def test_historical_caps_and_used_preserved(self):
        self.assertEqual(self.document['historical_caps'], {'NATIVE': 1858, 'PARENT': 298})
        self.assertEqual(self.document['cumulative_used'], {'NATIVE': 1, 'PARENT': 1})
        self.assertIsNone(self.document['lifetime_cycle_limit'])
        self.assertEqual(self.document['final_calls_added'], 0)

    def test_whole_lease_headroom_not_dose(self):
        caps = subject.validate(self.document, **self.values)
        self.assertGreater(caps['NATIVE'], 16 * (178400 - 1000))
        self.assertGreater(caps['PARENT'], 4 * (178400 - 1000))

    def test_future_counters_append_not_reset(self):
        row = dict(kind='NATIVE', number=2)
        values = dict(self.values, rows=self.rows + [row],
            ledger_bytes=self.raw + (json.dumps(row) + '\n').encode())
        self.assertEqual(subject.validate(self.document, **values), self.document['prospective_caps'])

    def test_prefix_mutation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'historical_charges'):
            subject.validate(self.document, **dict(self.values, ledger_bytes=self.raw.replace(b'NATIVE', b'PARENT')))

    def test_counter_gap_rejected(self):
        with self.assertRaisesRegex(ValueError, 'contiguous'):
            subject.counts([dict(kind='NATIVE', number=2)])

    def test_lease_extension_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no_lease_extension'):
            subject.validate(self.document, **dict(self.values, hard_end=178401))

    def test_short_margin_rejected(self):
        with self.assertRaisesRegex(ValueError, 'actual_lease'):
            subject.authorize(**dict(self.values, hard_end=180000), now=1000)

    def test_tampered_cap_rejected(self):
        self.document['prospective_caps']['NATIVE'] += 1
        with self.assertRaisesRegex(ValueError, 'exact_prospective'):
            subject.validate(self.document, **self.values)

    def test_bound_adapter_repair_new_namespace(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gpu'))
        from gpu import orch_r119_grid_lease_resume as resume
        adapter = resume.load_adapter(7)
        self.assertTrue(callable(adapter.load_runtime))
        self.assertEqual(adapter.ERA, 'learned_fork_r119')

    def test_broker_changes_custody_and_caps_not_provider_policy(self):
        from gpu import orch_r119_grid_lease_parent as parent
        text = parent.source()
        compile(text, 'broker', 'exec')
        self.assertIn("'lease_budget_r119_learned'", text)
        self.assertIn("ready['parent_cap'] == config['max_parent_calls']", text)
        self.assertIn('HISTORICAL_NO_REDISPATCH', text)
        self.assertIn("'high'", text)

    def test_drain_rejects_other_native(self):
        from gpu import orch_r119_grid_lease_drain as drain
        raw = drain.COMMAND + b'\0native\0'
        drain.validate_identity(774326, raw, dict(pid=774326))
        with self.assertRaisesRegex(ValueError, 'only_actual_owned'):
            drain.validate_identity(774327, raw, dict(pid=774327))


if __name__ == '__main__':
    unittest.main()
