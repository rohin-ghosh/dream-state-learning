"""CPU regression tests for same-policy route recovery, without network calls."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import restore_transport as recovery
from audit_transport import bind_new_transport


class TransportTests(unittest.TestCase):
    def test_old_relay_publication_is_not_a_new_transport_receipt(self):
        publication = dict(receipt_sha256='receipt', RESPONSE=dict(index=9,sha256='response'))
        transport = dict(session_id='life',unix=11,dispatched=True,receipt_sha256='receipt',
            origin=dict(record_index=9,record_sha256='response'))
        self.assertEqual(bind_new_transport('life',publication,[transport],10),transport)
        with self.assertRaises(ValueError):
            bind_new_transport('life',publication,[dict(transport,unix=9)],10)
        with self.assertRaises(ValueError):
            bind_new_transport('different_life',publication,[transport],10)
        with self.assertRaises(ValueError):
            bind_new_transport('life',publication,[dict(transport,dispatched=False)],10)

    def test_immutable_proxy_snapshot_imports_before_any_child_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            hashes = recovery.snapshot_source(source)
            self.assertIn('organism_v6/orch_r124_train_history.py', hashes)
            subprocess.run([sys.executable, '-B', str(source /
                'research_loop/workers/rohin233_ovx4_recovery_20260918/transport_large_proxy.py'), '--help'],
                cwd=source, env=dict(os.environ, PYTHONPATH=str(source)),
                check=True, capture_output=True, timeout=20)

    def test_original_registry_is_byte_identical(self):
        raw = recovery.registry_bytes()
        rows = json.loads(raw)['rows']
        self.assertEqual({row['physical'] for row in rows}, {0, 3, 5, 6, 7})
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row['host_alias'] == 'ovx2' for row in rows))
        self.assertIn('r213_r226_caption_unparented_fork', {row['session_id'] for row in rows})

    def test_routes_only_known_node3_and_live_shared_scorer(self):
        rows = json.loads(recovery.registry_bytes())['rows']
        upstream, downstream, routes = recovery.forwarding_commands(Path('/tmp/unit'), rows, 'unit')
        self.assertIn(recovery.SHARED + '/native.sock', upstream[-1])
        self.assertEqual(downstream.count('-R'), 5)
        self.assertTrue(all(row['target'].startswith('/tmp/n3cap-unit-') for row in routes))
        self.assertNotIn('StreamLocalBindUnlink=yes', str(upstream + downstream))
        self.assertNotIn('kill', str(upstream + downstream))

    def test_original_deadline_not_extended(self):
        recovery.check_deadline(recovery.DEADLINE - 1)
        with self.assertRaises(ValueError):
            recovery.check_deadline(recovery.DEADLINE)
        caps = json.loads((recovery.PRIOR / 'TRANSPORT_SOURCE_LEASE_CAPPED.json').read_bytes())
        self.assertEqual(recovery.DEADLINE, next(row['actual_deadline'] for row in caps if row['group'] == 'node3'))


if __name__ == '__main__':
    unittest.main()
