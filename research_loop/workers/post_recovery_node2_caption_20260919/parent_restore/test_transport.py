"""Existing node2 route and allocation remain unchanged in CPU recovery."""

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('node2_route_recovery', HERE / 'restore_transport.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


class TransportTests(unittest.TestCase):
    def test_original_registry_and_future_frontier_unchanged(self):
        raw = transport.registry_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), transport.REGISTRY_SHA)
        rows = json.loads(raw)['rows']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['minimum_origin_record_index'], 3303)
        self.assertEqual(rows[0]['journal']['journal_id'], '1840899d7847437093d41eae072b8d26')

    def test_only_private_node2_to_original_shared3_route(self):
        rows = json.loads(transport.registry_bytes())['rows']
        upstream, downstream, routes = transport.forwarding_commands(Path('/tmp/unit'), rows, 'unit')
        self.assertIn('gpu/ovx_ssh.sh', downstream)
        self.assertIn('gpu/ovx4_ssh.sh', upstream)
        self.assertEqual(routes, [dict(slot='2', alias='/tmp/r226-caption-2.sock', target='/tmp/n2cap-unit-2.sock')])
        self.assertIn('StreamLocalBindMask=0177', downstream)
        self.assertNotIn('StreamLocalBindUnlink=yes', str(upstream + downstream))

    def test_cannot_retarget_another_life(self):
        rows = json.loads(transport.registry_bytes())['rows']
        rows[0]['physical'] = 3
        with self.assertRaisesRegex(ValueError, 'only_existing_node2'):
            transport.forwarding_commands(Path('/tmp/unit'), rows, 'unit')

    def test_unchanged_source_specific_deadline(self):
        caps = json.loads((transport.PRIOR / 'TRANSPORT_SOURCE_LEASE_CAPPED.json').read_text())
        self.assertEqual(transport.DEADLINE, next(row['actual_deadline'] for row in caps if row['group'] == 'node2'))

    def test_all_native_route_literals_rebound_to_node2(self):
        source = transport.scoped_main(inspect.getsource(transport.recovery.main))
        self.assertNotIn('ovx2_ssh.sh', source)
        self.assertNotIn('R233_NODE3_TRANSPORT_RECOVERY.lock', source)
        self.assertIn('flock', source)
        self.assertIn('no_alias_changes=True', source)

    def test_unknown_original_source_never_transformed(self):
        with self.assertRaisesRegex(ValueError, 'implementation_changed'):
            transport.scoped_main('def main(): pass')


if __name__ == '__main__':
    unittest.main()
