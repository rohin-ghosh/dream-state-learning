"""Independent B5/B6 assertions against valid, exclusively synthetic closures.

The audited author TransferFixture constructs local test data; no author test
methods are inherited. Explicit campaign ledgers and source caps are supplied.
This is not receiving-host proof, saved-state admission, or a controller test.
"""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import threading
from types import SimpleNamespace
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
    'transfer.py': '87a1c8555a9799b8e11eaad12607b31d924003f25bc935cb4b9781890b6a9a47',
    'prep_common.py': '2b76c48c8fdcbf91bd351c63928ad4cc349ab4b949a45d1564d24051fa14c2a3',
    'test_transfer_accounting.py': 'b172859347b4fb28a6a5e159b4f96cb5a567f5bd15dd8c1c01b81a4bdf0a01e0',
}


class TransferRepairReviewTests(fixture_module.TransferFixture):
    def setUp(self):
        for name, expected in PINS.items():
            self.assertEqual(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), expected,
                'Review only the user-bound source and audited fixture bytes')
        super().setUp()

    def export_valid(self, sleep=3, root=None):
        output = io.BytesIO()
        transfer.export(self.life, sleep, output, root=self.custody if root is None else root,
            custody_root=self.custody, ledger=self.ledger, source_caps=self.caps)
        output.seek(0)
        return output

    def control_size(self, root):
        return sum((root / 'control' / name).stat().st_size
            for name in ('PREPARATION_SCOPE.json', 'PROPOSAL.json'))

    def adapter_size(self, files):
        return sum(len(raw) for name, raw in files.items() if transfer.kind(name) == 'adapter')

    def pack_files(self, files, sleep=3, original_complete=None):
        complete = f'lives/{self.life}/captures/{sleep:06d}/COMPLETE.json'
        complete_bytes = files.get(complete, original_complete)
        header = dict(schema=transfer.SCHEMA, proposal_sha256=common.PROPOSAL_SHA,
            private_evaluator_only=True, life_id=self.life, sleep=sleep,
            capture=transfer.reference(self.custody / complete, complete_bytes),
            files=[dict(name=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                for name, raw in files.items()])
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for name, raw in [('TRANSFER_HEADER.json', common.canonical(header)), *files.items()]:
                member = tarfile.TarInfo(name)
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
        output.seek(0)
        return output

    def test_complete_export_receive_has_exact_source_and_two_hop_charges(self):
        files = self.files()
        self.assertEqual(len(files), 13)
        adapter = self.adapter_size(files)
        file_bytes = sum(map(len, files.values()))
        output = self.export_valid()
        wire = len(output.getvalue())
        source = queue.read_totals(self.custody / 'lives' / self.life)
        self.assertEqual(source['metadata'] + source['adapter'], file_bytes + self.control_size(self.custody))
        self.assertEqual(source['adapter'], adapter)
        self.assertEqual(self.ledger.totals()['adapter'], 2 * adapter)
        result = self.receive(output)
        self.assertEqual(result['status'], 'EXACT_RECEIVING_COPY_VERIFIED')
        totals = self.ledger.totals()
        self.assertEqual(totals['adapter'], 3 * adapter)
        self.assertEqual(totals['metadata'] + totals['adapter'],
            file_bytes + self.control_size(self.custody) + 2 * wire + 1 + self.control_size(self.receiving))
        for name, raw in files.items():
            self.assertEqual((self.receiving / name).read_bytes(), raw)
        self.assertFalse((self.receiving / 'lives/life/captures/000000').exists())

    def test_every_required_member_including_marker_is_required(self):
        files = self.files()
        marker = files['lives/life/captures/000003/COMPLETE.json']
        for index, name in enumerate(sorted(files)):
            with self.subTest(omitted=name):
                root = self.base / f'omitted-{index}'
                self.controls(root)
                reduced = {key: raw for key, raw in files.items() if key != name}
                with self.assertRaises(ValueError):
                    self.receive(self.pack_files(reduced, original_complete=marker), root=root)
                self.no_positive(root)
                self.assertTrue((root / 'receiving_transfers/life_000003/FAILED.json').exists())

    def test_matching_archive_hashes_do_not_excuse_invalid_manifest_commit_join(self):
        files = self.files()
        prefix = 'lives/life/captures/000003/'
        manifest = json.loads(files[prefix + 'MANIFEST.json'])
        manifest['commit_sha256'] = '0' * 64
        files[prefix + 'MANIFEST.json'] = common.canonical(manifest)
        complete = json.loads(files[prefix + 'COMPLETE.json'])
        complete['manifest'] = transfer.reference(self.custody / (prefix + 'MANIFEST.json'),
            files[prefix + 'MANIFEST.json'])
        files[prefix + 'COMPLETE.json'] = common.canonical(complete)
        with self.assertRaisesRegex(ValueError, 'exact_original_manifest_commit_join'):
            self.receive(self.pack_files(files))
        self.no_positive()

    def test_receiver_does_not_reread_sender_custody(self):
        output = self.export_valid()
        original = Path.read_bytes

        def refuse_sender_read(path):
            self.assertFalse(path.is_relative_to(self.custody), 'Receiver may use only the transmitted cache')
            return original(path)

        with patch.object(Path, 'read_bytes', refuse_sender_read):
            self.assertEqual(self.receive(output)['status'], 'EXACT_RECEIVING_COPY_VERIFIED')

    def test_incoming_reads_have_durable_prepaid_credit_including_eof(self):
        audit = self
        source = self.archive().getvalue()
        prepaid = 0
        delivered = 0
        original = self.ledger.reserve

        def reserve(operation, life_id, category, amount, discovery=False):
            nonlocal prepaid
            reference = original(operation, life_id, category, amount, discovery)
            if operation.startswith('receiving-wire'):
                prepaid += common.bound(reference)['bytes']
            return reference

        class AuditedInput(io.BytesIO):
            def read(self, amount=-1):
                nonlocal delivered
                audit.assertGreaterEqual(amount, 0)
                audit.assertGreaterEqual(prepaid - delivered, amount, 'Reservation must exist before read')
                raw = super().read(amount)
                delivered += len(raw)
                return raw

        with patch.object(self.ledger, 'reserve', side_effect=reserve):
            self.assertEqual(self.receive(AuditedInput(source))['status'], 'EXACT_RECEIVING_COPY_VERIFIED')
        self.assertEqual(delivered, len(source))
        self.assertEqual(prepaid, len(source) + 1)

    def test_persisted_source_cap_refuses_export_before_new_payload_read(self):
        life_root = self.custody / 'lives' / self.life
        common.write(life_root / 'reads/prior-source-reservation.json', dict(kind='metadata',
            reserved_bytes=self.caps['metadata'] - 1, failures_charged=True))
        output = io.BytesIO()
        with self.assertRaisesRegex(ValueError, 'source_export_read_budget'):
            transfer.export(self.life, 3, output, root=self.custody, custody_root=self.custody,
                ledger=self.ledger, source_caps=self.caps)
        self.assertEqual(output.getvalue(), b'')
        self.assertEqual(self.ledger.totals()['metadata'], 0)
        self.assertEqual(queue.read_totals(life_root)['metadata'], self.caps['metadata'] - 1)
        with self.assertRaises(FileExistsError):
            self.export_valid()

    def test_global_adapter_cap_spans_export_source_wire_and_receive(self):
        adapter = self.adapter_size(self.files())
        self.ledger.limits['adapter'] = 3 * adapter - 1
        output = self.export_valid()
        self.assertEqual(self.ledger.totals()['adapter'], 2 * adapter)
        with self.assertRaisesRegex(ValueError, 'aggregate_read_budget'):
            self.receive(output)
        self.assertLessEqual(self.ledger.totals()['adapter'], 3 * adapter - 1)
        self.no_positive()
        before = self.ledger.totals()
        with self.assertRaises(FileExistsError):
            self.receive()
        self.assertEqual(self.ledger.totals(), before)

    def test_global_metadata_cap_rejects_receive_before_wire(self):
        output = self.export_valid()
        spent = self.ledger.totals()['metadata']
        self.ledger.limits['metadata'] = spent
        with self.assertRaisesRegex(ValueError, 'aggregate_read_budget'):
            self.receive(output)
        self.assertEqual(output.tell(), 0)
        self.assertEqual(self.ledger.totals()['metadata'], spent)
        self.no_positive()

    def test_prior_disk_reservation_bounds_each_role_without_wire_read(self):
        for role, limit in (('staging', 24 * common.GIB), ('receiving', 16 * common.GIB)):
            with self.subTest(role=role):
                root = self.base / f'disk-cap-{role}'
                self.controls(root)
                with patch.object(common.shutil, 'disk_usage', return_value=SimpleNamespace(free=100 * common.GIB)):
                    common.DiskLedger(root, role).reserve('prior-consumed-disk', limit - transfer.MIB)
                    output = self.archive()
                    with self.assertRaisesRegex(ValueError, 'aggregate_disk_budget'):
                        self.receive(output, root=root, role=role)
                self.assertEqual(output.tell(), 0)
                self.no_positive(root)

    def test_staging_is_not_receiving_readiness_and_onward_hop_is_charged(self):
        staging = self.base / 'staging'
        self.controls(staging)
        first = self.export_valid()
        self.assertEqual(self.receive(first, root=staging, role='staging')['status'], 'EXACT_STAGING_COPY_VERIFIED')
        self.assertFalse((staging / 'receiving_transfers').exists())
        before = self.ledger.totals()
        onward = self.export_valid(root=staging)
        self.assertGreater(self.ledger.totals()['adapter'], before['adapter'])
        self.assertGreater(self.ledger.totals()['metadata'], before['metadata'])
        self.assertEqual(self.receive(onward)['status'], 'EXACT_RECEIVING_COPY_VERIFIED')

    def test_reader_growth_cannot_read_more_than_its_reservation(self):
        source = self.base / 'growing'
        source.write_bytes(b'abc')
        reader = common.Reader(self.ledger, self.life, 'growth-regression', [source])
        reserve = self.ledger.reserve

        def grow(*arguments, **keywords):
            reference = reserve(*arguments, **keywords)
            source.write_bytes(b'abcd')
            return reference

        with patch.object(self.ledger, 'reserve', side_effect=grow):
            with self.assertRaisesRegex(ValueError, 'source_changed_during_read'):
                reader.raw(source)
        self.assertEqual(reader.bytes, 3)
        self.assertEqual(self.ledger.totals()['metadata'], 3)

    def test_same_two_complete_closures_succeed_when_received_sequentially(self):
        self.capture(4)
        for ordinal in (3, 4):
            self.assertEqual(self.receive(self.archive(ordinal), sleep=ordinal)['status'],
                'EXACT_RECEIVING_COPY_VERIFIED')
        self.assertTrue((self.receiving / 'receiving_transfers/life_000003/COMPLETE.json').exists())
        self.assertTrue((self.receiving / 'receiving_transfers/life_000004/COMPLETE.json').exists())

    def test_new_simultaneous_transfers_are_not_mistaken_for_unaccounted_old_disk(self):
        self.capture(4)
        streams = {ordinal: self.archive(ordinal) for ordinal in (3, 4)}
        barrier = threading.Barrier(2)
        reserve = common.DiskLedger.reserve

        def synchronized_reserve(disk, operation, amount):
            if operation.endswith(':control'):
                barrier.wait(timeout=5)
            return reserve(disk, operation, amount)

        def receive_one(ordinal):
            try:
                return self.receive(streams[ordinal], sleep=ordinal)['status']
            except ValueError as error:
                return str(error)

        with patch.object(common.DiskLedger, 'reserve', synchronized_reserve):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(receive_one, (3, 4)))
        if results != ['EXACT_RECEIVING_COPY_VERIFIED'] * 2:
            self.assertEqual([stream.tell() for stream in streams.values()], [0, 0])
            for ordinal in (3, 4):
                operation = self.receiving / 'receiving_transfers' / f'{self.life}_{ordinal:06d}'
                self.assertTrue((operation / 'ONCE.json').exists())
                self.assertTrue((operation / 'FAILED.json').exists())
        self.assertEqual(results, ['EXACT_RECEIVING_COPY_VERIFIED'] * 2,
            'Concurrent live operation directories must not poison each other as unknown old custody')


if __name__ == '__main__':
    unittest.main(verbosity=2)
