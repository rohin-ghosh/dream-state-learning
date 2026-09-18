import json
from pathlib import Path
import tempfile
import unittest

from astra7_receiver import renewed_matches
from lease_horizon import cpu_horizon, WALL
from bridge import act_only


class LeaseBridgeTests(unittest.TestCase):
    def test_unsupported_stages_are_not_relabelled_or_retried(self):
        batch = dict(exports=[dict(origin=dict(stage=stage)) for stage in ('THINK', 'ACT', 'LEARN')], decisions=[])
        selected = act_only(batch)
        self.assertEqual([entry['origin']['stage'] for entry in selected['exports']], ['ACT'])
        self.assertEqual(len(selected['decisions']), 2)

    def test_authority_is_CPU_only_and_expired_denied(self):
        self.assertEqual(cpu_horizon(now=1789754400), WALL)
        with self.assertRaises(ValueError):
            cpu_horizon(now=WALL)

    def test_native_change_cannot_be_claimed_as_CPU_renewal(self):
        authority = json.loads(Path(__file__).with_name('LEASE_AUTHORITY.json').read_bytes())
        authority['native_deadline_changed'] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'authority.json'
            path.write_text(json.dumps(authority))
            with self.assertRaises(ValueError):
                cpu_horizon(path, now=1789754400)

    def test_historical_context_is_not_a_renewed_roundtrip(self):
        historical = dict(publication=dict(id='old'))
        current = dict(publication=dict(id='new'))
        self.assertEqual(renewed_matches([historical], {'new'}), [])
        self.assertEqual(renewed_matches([historical, current], {'new'}), [current])


if __name__ == '__main__':
    unittest.main()
