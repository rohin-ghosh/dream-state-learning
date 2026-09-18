"""V3 independent local CPU checks using complete synthetic custody only.

The inspected author fixture builds data; assertions and lock observation here
are independent. No old review is edited or repinned. No model, remote wrapper,
real witness/result, or receiving-host claim is involved.
"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import fcntl
import hashlib
import io
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))

import prep_common as common
import transfer
import test_transfer_accounting as fixture_module
from gpu import orch_r167_object_probe_queue as queue


PINS = {
    'transfer.py': 'e8b3aed5abe19cfc195ac4fde318e8316834c582d883e9dcfce892b02f19bb2e',
    'prep_common.py': 'f6751d157bb283627a185ecf14321d571673512b61f17aedac3b056ef5410aee',
    'test_transfer_accounting.py': 'b172859347b4fb28a6a5e159b4f96cb5a567f5bd15dd8c1c01b81a4bdf0a01e0',
    'test_transfer_admission_race.py': '79ed428eb1e5e0acb9a3ca0a796129d830be8e137dc1de1379443c0e306a24ba',
}


class TransferV3ReviewTests(fixture_module.TransferFixture):
    def setUp(self):
        for name, expected in PINS.items():
            self.assertEqual(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), expected,
                'Exact V3 source and fixture bindings required')
        super().setUp()

    def controls_size(self, root):
        return sum((root / 'control' / name).stat().st_size
            for name in ('PROPOSAL.json', 'PREPARATION_SCOPE.json'))

    def test_real_disk_lock_hides_half_admission_and_concurrent_charges_remain_exact(self):
        self.capture(4)
        for role in ('receiving', 'staging'):
            with self.subTest(role=role):
                root = self.base / f'independent-{role}'
                self.controls(root)
                streams = {ordinal: self.archive(ordinal) for ordinal in (3, 4)}
                operations = {ordinal: root / f'{role}_transfers' / f'{self.life}_{ordinal:06d}'
                    for ordinal in streams}
                disk_lock = common.DiskLedger(root, role).directory / 'disk.lock'
                owner_paused = threading.Event()
                peer_attempted = threading.Event()
                release_owner = threading.Event()
                worker = threading.local()
                original_write, original_lock = common.write, common.lock
                before = self.ledger.totals()

                def observe_write(path, document):
                    reference = original_write(path, document)
                    if Path(path) == operations[3] / 'ONCE.json':
                        owner_paused.set()
                        self.assertTrue(release_owner.wait(5), 'Bounded release of paused synthetic admission')
                    return reference

                @contextmanager
                def observe_lock(path):
                    if Path(path) == disk_lock and getattr(worker, 'ordinal', None) == 4:
                        peer_attempted.set()
                    with original_lock(path):
                        yield

                def receive_one(ordinal):
                    worker.ordinal = ordinal
                    return self.receive(streams[ordinal], sleep=ordinal, root=root, role=role)

                with patch.object(common, 'write', observe_write), patch.object(common, 'lock', observe_lock):
                    with ThreadPoolExecutor(max_workers=2) as pool:
                        first = pool.submit(receive_one, 3)
                        try:
                            self.assertTrue(owner_paused.wait(5))
                            with disk_lock.open('a+b') as descriptor:
                                with self.assertRaises(BlockingIOError):
                                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            second = pool.submit(receive_one, 4)
                            self.assertTrue(peer_attempted.wait(5))
                            self.assertFalse(operations[4].exists(), 'Peer must block before creating its operation')
                            self.assertFalse(second.done())
                        finally:
                            release_owner.set()
                        results = [first.result(timeout=10), second.result(timeout=10)]
                self.assertEqual([result['status'] for result in results], [f'EXACT_{role.upper()}_COPY_VERIFIED'] * 2)
                for ordinal, operation in operations.items():
                    self.assertTrue((operation / 'COMPLETE.json').exists())
                    self.assertFalse((operation / 'FAILED.json').exists())
                    self.assertEqual(streams[ordinal].tell(), len(streams[ordinal].getvalue()))
                disk_rows = [common.read(path) for path in disk_lock.parent.glob('reservations/*.json')]
                self.assertEqual(len(disk_rows), 4)
                expected_disk = sum(18 * transfer.MIB + sum(((len(raw) + 4095) // 4096) * 4096
                    for raw in self.files(ordinal).values()) for ordinal in streams)
                self.assertEqual(sum(row['bytes'] for row in disk_rows), expected_disk)
                files = self.files()
                adapter = 2 * sum(len(raw) for name, raw in files.items() if transfer.kind(name) == 'adapter')
                shared = sum(len(raw) for name, raw in files.items() if '/captures/' not in name)
                wire = sum(len(stream.getvalue()) for stream in streams.values())
                after = self.ledger.totals()
                self.assertEqual(after['adapter'] - before['adapter'], adapter)
                self.assertEqual(after['metadata'] - before['metadata'],
                    wire - adapter + 2 + 2 * self.controls_size(root) + shared)

    def test_full_export_receive_closure_and_charges_survive_lock_repair(self):
        files = self.files()
        self.assertEqual(len(files), 13)
        output = io.BytesIO()
        transfer.export(self.life, 3, output, root=self.custody, custody_root=self.custody,
            ledger=self.ledger, source_caps=self.caps)
        output.seek(0)
        self.assertEqual(self.receive(output)['status'], 'EXACT_RECEIVING_COPY_VERIFIED')
        for name, raw in files.items():
            self.assertEqual((self.receiving / name).read_bytes(), raw)
        payload = sum(map(len, files.values()))
        adapter = sum(len(raw) for name, raw in files.items() if transfer.kind(name) == 'adapter')
        totals = self.ledger.totals()
        source = queue.read_totals(self.custody / 'lives' / self.life)
        self.assertEqual(source['metadata'] + source['adapter'], payload + self.controls_size(self.custody))
        self.assertEqual(totals['adapter'], 3 * adapter)
        self.assertEqual(totals['metadata'] + totals['adapter'], payload + self.controls_size(self.custody)
            + 2 * len(output.getvalue()) + self.controls_size(self.receiving) + 1)

    def test_transport_hash_match_does_not_admit_changed_adapter_inventory(self):
        name = 'lives/life/captures/000003/adapter/adapter_model.safetensors'
        output = self.archive(overrides={name: b'synthetic changed adapter'})
        with self.assertRaisesRegex(ValueError, 'streamed_adapter_inventory_matches_original_COMMIT'):
            self.receive(output)
        self.no_positive()
        before = self.ledger.totals()
        self.assertGreater(before['adapter'], 0)
        with self.assertRaises(FileExistsError):
            self.receive()
        self.assertEqual(self.ledger.totals(), before)

    def test_genuine_unknown_old_custody_still_holds_before_wire(self):
        prior = self.receiving / 'receiving_transfers/old_consumed'
        reference = common.write(prior / 'ONCE.json', dict(no_retry=True, synthetic=True))
        output = self.archive()
        before = self.ledger.totals()
        with self.assertRaisesRegex(ValueError, 'prior_transfer_disk_custody_unaccounted_hold'):
            self.receive(output)
        self.assertEqual(output.tell(), 0)
        self.assertEqual(self.ledger.totals(), before)
        self.assertEqual(common.ref(prior / 'ONCE.json'), reference)
        self.no_positive()
        operation = self.receiving / 'receiving_transfers/life_000003'
        self.assertTrue((operation / 'ONCE.json').exists())
        self.assertTrue((operation / 'FAILED.json').exists())
        with self.assertRaises(FileExistsError):
            self.receive()


if __name__ == '__main__':
    unittest.main(verbosity=2)
