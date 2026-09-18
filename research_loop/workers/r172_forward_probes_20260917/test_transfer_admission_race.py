"""Non-material R172 admission regressions; exclusively synthetic CPU custody."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import fcntl
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))

import prep_common as common
import transfer
from test_transfer_accounting import TransferFixture


class TransferAdmissionRaceTests(TransferFixture):
    def overlap(self, role, phase):
        root = self.base / f'overlap-{role}'
        self.controls(root)
        streams = {ordinal: self.archive(ordinal) for ordinal in (3, 4)}
        operations = {ordinal: root / f'{role}_transfers' / f'{self.life}_{ordinal:06d}'
            for ordinal in streams}
        disk_lock = common.DiskLedger(root, role).directory / 'disk.lock'
        once_written, peer_waiting, payload_ready = (threading.Event() for unused in range(3))
        worker = threading.local()
        paused = 3 if phase == 'control' else 4
        waiting = 4 if phase == 'control' else 3
        original_write, original_lock, original_reserve = common.write, common.lock, common.DiskLedger.reserve

        def paused_write(path, document):
            receipt = original_write(path, document)
            if Path(path) == operations[paused] / 'ONCE.json':
                once_written.set()
                self.assertTrue(peer_waiting.wait(5), 'peer must attempt the disk lock during admission')
            return receipt

        @contextmanager
        def observed_lock(path):
            if Path(path) == disk_lock and getattr(worker, 'ordinal', None) == waiting and once_written.is_set():
                disk_lock.parent.mkdir(parents=True, exist_ok=True)
                with disk_lock.open('a+b') as descriptor:
                    try:
                        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        peer_waiting.set()
                        fcntl.flock(descriptor, fcntl.LOCK_EX)
                    else:
                        peer_waiting.set()
                    yield
            else:
                with original_lock(path):
                    yield

        def paused_reserve(disk, operation, amount):
            if phase == 'payload' and operation == str(operations[3]) + ':payload':
                payload_ready.set()
                self.assertTrue(once_written.wait(5), 'fresh peer admission must overlap payload reservation')
            return original_reserve(disk, operation, amount)

        def receive_one(ordinal):
            worker.ordinal = ordinal
            try:
                return self.receive(streams[ordinal], sleep=ordinal, root=root, role=role)['status']
            except ValueError as error:
                return str(error)

        with patch.object(common, 'write', paused_write), patch.object(common, 'lock', observed_lock), \
                patch.object(common.DiskLedger, 'reserve', paused_reserve):
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(receive_one, 3)
                self.assertTrue((once_written if phase == 'control' else payload_ready).wait(5))
                second = pool.submit(receive_one, 4)
                results = [first.result(timeout=10), second.result(timeout=10)]
        self.assertEqual(results, [f'EXACT_{role.upper()}_COPY_VERIFIED'] * 2)
        for ordinal, operation in operations.items():
            self.assertEqual(streams[ordinal].tell(), len(streams[ordinal].getvalue()))
            self.assertTrue((operation / 'ONCE.json').is_file())
            self.assertTrue((operation / 'COMPLETE.json').is_file())
            self.assertFalse((operation / 'FAILED.json').exists())
        reservations = [common.read(path) for path in disk_lock.parent.glob('reservations/*.json')]
        self.assertEqual(len(reservations), 4)
        expected_disk = sum(18 * transfer.MIB + sum(((len(raw) + 4095) // 4096) * 4096
            for raw in self.files(ordinal).values()) for ordinal in streams)
        self.assertEqual(sum(row['bytes'] for row in reservations), expected_disk)

    def test_peer_control_reservation_waits_for_atomic_admission(self):
        self.capture(4)
        for role in ('receiving', 'staging'):
            with self.subTest(role=role):
                self.overlap(role, 'control')

    def test_existing_payload_reservation_waits_for_fresh_peer_admission(self):
        self.capture(4)
        for role in ('receiving', 'staging'):
            with self.subTest(role=role):
                self.overlap(role, 'payload')

    def test_unknown_old_control_and_payload_custody_still_hold(self):
        for role in ('receiving', 'staging'):
            for phase in ('control', 'payload'):
                with self.subTest(role=role, phase=phase):
                    root = self.base / f'old-{role}-{phase}'
                    self.controls(root)
                    prior = root / f'{role}_transfers' / 'old_consumed'
                    common.write(prior / 'ONCE.json', dict(no_retry=True))
                    common.write(prior / 'FAILED.json', dict(status='OLD_FAILURE'))
                    if phase == 'payload':
                        common.DiskLedger(root, role).reserve(str(prior) + ':control', 2 * transfer.MIB)
                        common.write(prior / 'payload/partial', b'old synthetic partial')
                    preserved = {path: path.read_bytes() for path in prior.rglob('*') if path.is_file()}
                    stream = self.archive()
                    before = self.ledger.totals()
                    with self.assertRaisesRegex(ValueError, 'prior_transfer_disk_custody_unaccounted_hold'):
                        self.receive(stream, root=root, role=role)
                    self.assertEqual(stream.tell(), 0)
                    self.assertEqual(self.ledger.totals(), before)
                    self.assertEqual({path: path.read_bytes() for path in preserved}, preserved)
                    self.assert_consumed(root, role)

    def assert_consumed(self, root, role):
        operation = root / f'{role}_transfers' / f'{self.life}_000003'
        self.assertTrue((operation / 'ONCE.json').is_file())
        self.assertTrue((operation / 'FAILED.json').is_file())
        self.assertFalse((operation / 'COMPLETE.json').exists())
        self.assertFalse((operation / 'payload').exists())
        before = self.ledger.totals()
        with self.assertRaises(FileExistsError):
            self.receive(root=root, role=role)
        self.assertEqual(self.ledger.totals(), before)

    def test_failed_control_budget_admission_keeps_consumed_attempt_and_old_charge(self):
        for role, limit in common.DiskLedger.CAPS.items():
            with self.subTest(role=role):
                root = self.base / f'full-{role}'
                self.controls(root)
                disk = common.DiskLedger(root, role)
                with patch.object(common.shutil, 'disk_usage', return_value=SimpleNamespace(free=100 * common.GIB)):
                    old_charge = disk.reserve('old-uncertain-copy', limit - 1)
                    preserved = Path(old_charge['path']).read_bytes()
                    stream = self.archive()
                    with self.assertRaisesRegex(ValueError, 'aggregate_disk_budget'):
                        self.receive(stream, root=root, role=role)
                self.assertEqual(stream.tell(), 0)
                self.assertEqual(Path(old_charge['path']).read_bytes(), preserved)
                self.assertEqual(len(list(disk.directory.glob('reservations/*.json'))), 1)
                self.assert_consumed(root, role)
