"""B5/B6 author regressions using synthetic local TRAIN custody only."""

from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))

from gpu import orch_r167_object_probe_queue as queue
import prep_common as common
import transfer


class TransferFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='r172-b5-b6-synthetic-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.custody = self.base / 'custody'
        self.receiving = self.base / 'receiving'
        self.original = self.base / 'original/life'
        self.life = 'life'
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.now = common.END - 12000
        self.stack.enter_context(patch.object(common.time, 'time', return_value=self.now))
        self.proposal = dict(lives=[dict(life_id=self.life, proposed_storage_root=str(self.original))])
        self.stack.enter_context(patch.object(common, 'PROPOSAL_SHA', common.digest(self.proposal)))
        self.scope = dict(schema='R172_MAIN_BUILDER_PREPARATION_SCOPE_V1', proposal_ref=dict(sha256=common.PROPOSAL_SHA),
            gpu_execution_authorized_now=False, model_calls_authorized_now=False,
            preparation_source_limits=dict(metadata_bytes=32*common.GIB, adapter_bytes=16*common.GIB,
                per_life_per_kind_bytes=2*common.GIB, operational_discovery_bytes_included_in_metadata=64*1024**2))
        for root in (self.custody, self.receiving):
            self.controls(root)
        self.ledger = common.Ledger(self.base / 'existing-campaign-ledger', dict(metadata=128*transfer.MIB,
            adapter=128*transfer.MIB, per_life=128*transfer.MIB, discovery=64*transfer.MIB), [self.life])
        self.ledger.reserve('existing-synthetic-reservation', self.life, 'metadata', 0)
        self.context = dict(system_prompt='Synthetic TRAIN system.', birth_prompt='Synthetic TRAIN birth.')
        self.birth = common.write(self.base / 'original-birth.json', self.context)
        self.journal = dict(path=str(self.original / 'stream/JOURNAL.json'), sha256='1'*64)
        self.record = dict(path=str(self.original / 'stream/records/00000000000000000002.json'), sha256='2'*64)
        self.control = self.custody / 'source_controls' / self.life
        observation = dict(status='IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED', source_root=str(self.original),
            life_id=self.life, last_completed_sleep=2, observed_unix=self.now-101,
            native_identity=dict(pid=1, start_ticks='2', boot_id='synthetic-boot'),
            completed_boundary=dict(record=dict(record=self.record)))
        observed = common.write(self.control / 'FRESH_CUSTODY.json', observation)
        self.caps = dict(metadata=64*transfer.MIB, adapter=64*transfer.MIB)
        authority = dict(schema=queue.SCHEMA, status='MAIN_SOURCE_READ_COPY_GO', life_id=self.life,
            source_root=str(self.original), birth_plan=self.birth, journal=self.journal, milestones=[0, 3, 4, 5],
            metadata_read_cap=self.caps['metadata'], adapter_read_cap=self.caps['adapter'],
            registration_observation=observed, frozen_unix=self.now-100, read_end_unix=common.END,
            permissions=['metadata_discovery', 'adapter_only_copy'])
        authority_ref = common.write(self.control / 'MAIN_SOURCE_READ_COPY_GO.json', authority)
        self.plan = dict(schema=queue.SCHEMA, queue_root=str(self.custody / 'lives' / self.life), life_id=self.life,
            source_root=str(self.original), birth_plan=self.birth, journal=self.journal, source_authority=authority_ref,
            first_sleep=3, sleep_count=3, frozen_unix=self.now-100, probes=list(queue.PROBES), conditions=list(queue.CONDITIONS),
            base_sha256=queue.BASE, model_call_cap=24, generated_token_cap=12288,
            metadata_read_cap=self.caps['metadata'], adapter_read_cap=self.caps['adapter'])
        plan_ref = common.write(self.control / 'QUEUE_PLAN.json', self.plan)
        queue.initialize(plan_ref['path'])
        life_root = self.custody / 'lives' / self.life
        witness = common.write(life_root / 'TRAIN_WITNESSES.private.json', dict(context=self.context,
            parent_access=False, lexical='NOT_APPLIED_NONCOVERAGE_NOT_NEGATIVE', source_record=self.record,
            witnesses=[dict(event_index=0, text='Synthetic own TRAIN response.',
                text_sha256=hashlib.sha256(b'Synthetic own TRAIN response.').hexdigest())]))
        common.write(life_root / 'TRAIN_FREEZE.json', dict(status='PREOUTPUT_ORIGINAL_LANGUAGE_TRAIN_EVIDENCE',
            evidence=witness, record=self.record, birth=self.birth, frozen_unix=self.now-90, model_calls=0))
        self.capture(3)

    def controls(self, root):
        common.write(root / 'control/PROPOSAL.json', self.proposal)
        common.write(root / 'control/PREPARATION_SCOPE.json', self.scope)

    def capture(self, sleep):
        root = self.custody / 'lives' / self.life / 'captures' / f'{sleep:06d}'
        adapter = {name: common.write(root / 'adapter' / name, raw)['sha256'] for name, raw in
            (('adapter_model.safetensors', b'synthetic adapter'), ('adapter_config.json', b'{}'))}
        commit = dict(schema='R125_NATIVE_CONTINUITY_V1', base_sha256=queue.BASE,
            adapter_path=str(queue.checkpoint_path(self.original, sleep).parent / 'adapter'),
            adapter_files=adapter, checkpoint_sha256=dict(adapter=common.digest(adapter)),
            created_unix=self.now-50, optimizer_steps=sleep)
        commit_ref = common.write(root / 'COMMIT.original.json', commit)
        manifest = common.write(root / 'MANIFEST.json', dict(schema='R130_CHECKPOINT_MANIFEST_V1', adapter_path='adapter',
            commit_path='COMMIT.original.json', commit_sha256=commit_ref['sha256']))
        birth = common.write(root / 'BIRTH.private.json', self.context)
        boundary = common.write(root / 'BOUNDARY.json', dict(schema=queue.SCHEMA, life_id=self.life, sleep=sleep,
            source_root=str(self.original), birth_plan=self.birth, source_authority=self.plan['source_authority'],
            context_sha256=common.digest(self.context), record=self.record,
            intent=dict(path=str(self.original / 'stream/records/00000000000000000002.intent.json'), sha256='3'*64),
            commit=dict(path=str(queue.checkpoint_path(self.original, sleep)), sha256=commit_ref['sha256'])))
        common.write(root / 'COMPLETE.json', dict(status='IMMUTABLE_ADAPTER_BIRTH_CUSTODY', manifest=manifest,
            birth=birth, boundary=boundary, observed_unix=self.now-10, model_calls=0))

    def files(self, sleep=3):
        return {name: (self.custody / name).read_bytes() for name in sorted(transfer.required_members(self.life, sleep))}

    def archive(self, sleep=3, overrides=None, omit=(), header_change=None, extra_members=()):
        files = self.files(sleep)
        files.update(overrides or {})
        for name in omit:
            files.pop(name)
        prefix = f'lives/{self.life}/captures/{sleep:06d}'
        complete = prefix + '/COMPLETE.json'
        captured = json.loads(files[complete])
        for field, filename in (('manifest', 'MANIFEST.json'), ('birth', 'BIRTH.private.json'), ('boundary', 'BOUNDARY.json')):
            name = prefix + '/' + filename
            if name in files:
                captured[field] = transfer.reference(self.custody / name, files[name])
        files[complete] = common.canonical(captured)
        header = dict(schema=transfer.SCHEMA, life_id=self.life, sleep=sleep, private_evaluator_only=True,
            proposal_sha256=common.PROPOSAL_SHA, capture=transfer.reference(self.custody / complete, files[complete]),
            files=[dict(name=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()) for name, raw in files.items()])
        if header_change:
            header_change(header)
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for name, raw in [('TRANSFER_HEADER.json', common.canonical(header)), *files.items(), *extra_members]:
                member = tarfile.TarInfo(name)
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
        stream.seek(0)
        return stream

    def receive(self, stream=None, sleep=3, root=None, **kwargs):
        return transfer.receive(self.archive(sleep) if stream is None else stream,
            self.receiving if root is None else root, life_id=self.life, sleep=sleep,
            custody_root=self.custody, ledger=self.ledger, **kwargs)

    def no_positive(self, root=None, sleep=3):
        root = self.receiving if root is None else root
        self.assertFalse((root / f'receiving_transfers/{self.life}_{sleep:06d}/COMPLETE.json').exists())
        self.assertFalse((root / f'lives/{self.life}/captures/{sleep:06d}/COMPLETE.json').exists())


class TransferAccountingTests(TransferFixture):
    def test_complete_forward_closure_and_precise_incoming_charges(self):
        stream = self.archive()
        archive_size = len(stream.getvalue())
        files = self.files()
        adapter = sum(len(raw) for name, raw in files.items() if transfer.kind(name) == 'adapter')
        control_bytes = sum((self.receiving / 'control' / name).stat().st_size for name in
            ('PROPOSAL.json', 'PREPARATION_SCOPE.json'))
        result = self.receive(stream)
        self.assertEqual(result['status'], 'EXACT_RECEIVING_COPY_VERIFIED')
        totals = self.ledger.totals()
        self.assertEqual(totals['adapter'], adapter)
        self.assertEqual(totals['metadata'], archive_size-adapter+1+control_bytes)
        for name, raw in files.items():
            self.assertEqual((self.receiving / name).read_bytes(), raw)
        self.assertFalse((self.receiving / 'lives/life/captures/000000').exists())

    def test_only_complete_marker_cannot_claim_copy(self):
        names = transfer.required_members(self.life, 3)
        omit = [name for name in names if not name.endswith('/COMPLETE.json')]
        with self.assertRaisesRegex(ValueError, 'bounded_capture_members'):
            self.receive(self.archive(omit=omit))
        self.no_positive()
        self.assertGreater(self.ledger.totals()['metadata'], 0)
        with self.assertRaises(FileExistsError):
            self.receive()

    def test_each_missing_closure_member_refused(self):
        for index, name in enumerate(sorted(transfer.required_members(self.life, 3))):
            if name.endswith('/COMPLETE.json'):
                continue
            with self.subTest(name=name):
                root = self.base / f'missing-{index}'
                self.controls(root)
                with self.assertRaises(ValueError):
                    self.receive(self.archive(omit=[name]), root=root)
                self.no_positive(root)

    def test_unenrolled_sleep_refused_after_full_hash_verification(self):
        self.capture(9)
        with self.assertRaisesRegex(ValueError, 'declared_enrolled_milestone'):
            self.receive(sleep=9)
        self.no_positive(sleep=9)

    def test_wrong_original_commit_join_refused(self):
        name = 'lives/life/captures/000003/BOUNDARY.json'
        document = json.loads(self.files()[name])
        document['commit']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'original_boundary_hash_joins'):
            self.receive(self.archive(overrides={name: common.canonical(document)}))
        self.no_positive()

    def test_invalid_registration_slots_refused(self):
        name = 'lives/life/REGISTERED.json'
        document = json.loads(self.files()[name])
        document['slots'] = []
        with self.assertRaisesRegex(ValueError, 'exact_registered_milestone_slots'):
            self.receive(self.archive(overrides={name: common.canonical(document)}))
        self.no_positive()

    def test_invalid_private_freeze_refused(self):
        name = 'lives/life/TRAIN_FREEZE.json'
        document = json.loads(self.files()[name])
        document['record']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'private_TRAIN_freeze_original_joins'):
            self.receive(self.archive(overrides={name: common.canonical(document)}))
        self.no_positive()

    def test_extra_archive_member_and_trailing_bytes_refused(self):
        for index, stream in enumerate((self.archive(extra_members=[('surprise', b'bad')]),
                io.BytesIO(self.archive().getvalue()+b'bad'))):
            root = self.base / f'extra-{index}'
            self.controls(root)
            with self.assertRaises(ValueError):
                self.receive(stream, root=root)
            self.no_positive(root)

    def test_negative_size_boolean_sleep_and_duplicate_names_refused(self):
        changes = (lambda header: header['files'][0].update(bytes=-1),
            lambda header: header.update(sleep=True),
            lambda header: header['files'].__setitem__(1, header['files'][0]))
        for index, change in enumerate(changes):
            root = self.base / f'header-{index}'
            self.controls(root)
            with self.assertRaises(ValueError):
                self.receive(self.archive(header_change=change), root=root)
            self.no_positive(root)

    def test_partial_or_malformed_header_charge_and_latch_preserved(self):
        stream = io.BytesIO(b'broken')
        with self.assertRaises(ValueError):
            self.receive(stream)
        rows = self.ledger.totals()['rows']
        charged = [row['bytes'] for row in rows if ':wire:' in row['operation'] or 'receiving-wire:' in row['operation']]
        self.assertEqual(charged, [512])
        self.no_positive()
        self.assertTrue((self.receiving / 'receiving_transfers/life_000003/FAILED.json').exists())

    def test_campaign_refusal_precedes_input_read(self):
        self.ledger.reserve('old-read', self.life, 'metadata', self.ledger.limits['metadata'])
        stream = self.archive()
        with self.assertRaisesRegex(ValueError, 'aggregate_read_budget'):
            self.receive(stream)
        self.assertEqual(stream.tell(), 0)
        self.no_positive()

    def test_incoming_io_is_charged_before_every_read(self):
        ledger = self.ledger
        case = self
        class Checked(io.BytesIO):
            def read(self, size=-1):
                totals = ledger.totals()
                if self.tell() < len(self.getvalue()):
                    case.assertGreaterEqual(totals['metadata']+totals['adapter'], self.tell()+size)
                return super().read(size)
        self.receive(Checked(self.archive().getvalue()))

    def test_buffered_input_rejected_without_hidden_readahead(self):
        source = io.BytesIO(self.archive().getvalue())
        buffered = io.BufferedReader(source)
        with self.assertRaisesRegex(ValueError, 'unbuffered_transfer_stream_required'):
            self.receive(buffered)
        self.assertEqual(source.tell(), 0)

    def test_existing_registration_rereads_are_independently_charged(self):
        self.receive()
        self.capture(4)
        shared = [name for name in self.files(4) if '/captures/' not in name]
        before = self.ledger.totals()
        stream = self.archive(4)
        incoming = len(stream.getvalue())
        control_bytes = sum((self.receiving / 'control' / name).stat().st_size for name in
            ('PROPOSAL.json', 'PREPARATION_SCOPE.json'))
        shared_bytes = sum((self.receiving / name).stat().st_size for name in shared)
        self.receive(stream, sleep=4)
        after = self.ledger.totals()
        self.assertEqual(after['metadata']+after['adapter']-before['metadata']-before['adapter'],
            incoming+1+control_bytes+shared_bytes)

    def test_old_disk_reservations_block_new_transfer_without_read(self):
        with patch.object(common.shutil, 'disk_usage', return_value=SimpleNamespace(free=100*common.GIB)):
            common.DiskLedger(self.receiving, 'receiving').reserve('old-uncertain-copy', 16*common.GIB-1)
            stream = self.archive()
            with self.assertRaisesRegex(ValueError, 'aggregate_disk_budget'):
                self.receive(stream)
            self.assertEqual(stream.tell(), 0)
        self.no_positive()

    def test_payload_disk_refusal_before_first_member(self):
        stream = self.archive()
        with patch.object(common.shutil, 'disk_usage', side_effect=[SimpleNamespace(free=100*common.GIB), SimpleNamespace(free=0)]):
            with self.assertRaisesRegex(ValueError, 'insufficient_free_disk'):
                self.receive(stream)
        self.assertLess(stream.tell(), len(stream.getvalue()))
        self.assertFalse((self.receiving / 'receiving_transfers/life_000003/payload').exists())
        self.assertEqual(self.ledger.totals()['adapter'], 0)

    def test_staging_uses_24_GiB_not_receiver_readiness(self):
        self.assertEqual(common.DiskLedger.CAPS, dict(staging=24*common.GIB, receiving=16*common.GIB))
        result = self.receive(role='staging')
        self.assertEqual(result['status'], 'EXACT_STAGING_COPY_VERIFIED')
        self.assertFalse((self.receiving / 'receiving_transfers').exists())
        self.assertTrue((self.receiving / 'staging_transfers/life_000003/COMPLETE.json').exists())

    def test_source_export_caches_metadata_and_charges_file_and_wire_bytes(self):
        output = io.BytesIO()
        files = self.files()
        forbidden = {self.custody / name for name in files}
        original_read = Path.read_bytes
        def no_unmetered_read(path):
            self.assertNotIn(path, forbidden, 'source payload must use the charged descriptor, not Path.read_bytes')
            return original_read(path)
        with patch.object(Path, 'read_bytes', no_unmetered_read):
            transfer.export(self.life, 3, output, root=self.custody, ledger=self.ledger, source_caps=self.caps)
        source = queue.read_totals(self.custody / 'lives/life')
        payload_bytes = sum(len(raw) for raw in files.values())
        controls = sum((self.custody / 'control' / name).stat().st_size for name in
            ('PROPOSAL.json', 'PREPARATION_SCOPE.json'))
        self.assertEqual(source['metadata']+source['adapter'], payload_bytes+controls)
        charged = self.ledger.totals()
        self.assertEqual(charged['metadata']+charged['adapter'], payload_bytes+controls+len(output.getvalue()))
        output.seek(0)
        self.assertEqual(self.receive(output)['status'], 'EXACT_RECEIVING_COPY_VERIFIED')

    def test_export_cap_refusal_reads_no_metadata(self):
        output = io.BytesIO()
        with self.assertRaisesRegex(ValueError, 'source_export_read_budget'):
            transfer.export(self.life, 3, output, root=self.custody, ledger=self.ledger,
                source_caps=dict(metadata=1, adapter=1))
        self.assertEqual(output.getvalue(), b'')
        self.assertEqual(self.ledger.totals()['metadata'], 0)

    def test_missing_accounting_never_fabricates_fresh_budget(self):
        stream = self.archive()
        with self.assertRaisesRegex(ValueError, 'existing_campaign_ledger_required'):
            transfer.receive(stream, self.receiving, life_id=self.life, sleep=3, custody_root=self.custody)
        self.assertEqual(stream.tell(), 0)
        self.assertFalse((self.receiving / 'receiving_transfers').exists())

    def test_reader_growth_uses_unbuffered_exact_precharged_length(self):
        source = self.base / 'growing.json'
        source.write_bytes(b'abc')
        original = self.ledger.reserve
        def grow(*args, **kwargs):
            result = original(*args, **kwargs)
            source.write_bytes(b'abcd')
            return result
        reader = common.Reader(self.ledger, self.life, 'growing', [source])
        with patch.object(self.ledger, 'reserve', side_effect=grow):
            with self.assertRaisesRegex(ValueError, 'source_changed_during_read'):
                reader.raw(source)
        self.assertEqual(reader.bytes, 3)
        self.assertEqual(self.ledger.totals()['metadata'], 3)

    def test_unaccounted_old_transfer_holds_without_read_or_relabel(self):
        old = common.write(self.receiving / 'receiving_transfers/old_000001/ONCE.json',
            dict(status='OLD_UNCERTAIN_CAPTURE_NOT_VERIFIED'))
        stream = self.archive()
        with self.assertRaisesRegex(ValueError, 'prior_transfer_disk_custody_unaccounted_hold'):
            self.receive(stream)
        self.assertEqual(stream.tell(), 0)
        self.assertEqual(common.ref(old['path']), old)
        self.no_positive()

    def test_negative_old_ledger_row_cannot_refund_budget(self):
        common.write(self.ledger.root / 'reservations/bad-old.json', dict(status='CHARGED_BEFORE_IO_NO_REFUND',
            life_id=self.life, kind='metadata', bytes=-1, discovery=False))
        stream = self.archive()
        with self.assertRaisesRegex(ValueError, 'valid_persistent_read_reservations_no_refunds'):
            self.receive(stream)
        self.assertEqual(stream.tell(), 0)
        self.no_positive()

    def test_capture_marker_not_published_before_closure_validation(self):
        original = transfer.validate_closure
        def validate(*args, **kwargs):
            self.no_positive()
            return original(*args, **kwargs)
        with patch.object(transfer, 'validate_closure', side_effect=validate):
            self.receive()
        self.assertTrue((self.receiving / 'lives/life/captures/000003/COMPLETE.json').is_file())

    def test_staging_to_receiver_is_a_new_fully_charged_hop(self):
        self.receive(role='staging')
        before = self.ledger.totals()
        output = io.BytesIO()
        transfer.export(self.life, 3, output, root=self.receiving, custody_root=self.custody,
            ledger=self.ledger, source_caps=self.caps)
        after_export = self.ledger.totals()
        self.assertGreater(after_export['metadata'], before['metadata'])
        self.assertGreater(after_export['adapter'], before['adapter'])
        target = self.base / 'last-receiver'
        self.controls(target)
        output.seek(0)
        result = self.receive(output, root=target)
        self.assertEqual(result['status'], 'EXACT_RECEIVING_COPY_VERIFIED')
        after_receive = self.ledger.totals()
        self.assertGreater(after_receive['metadata'], after_export['metadata'])
        self.assertGreater(after_receive['adapter'], after_export['adapter'])
        self.assertFalse((self.receiving / 'receiving_transfers').exists())

    def test_changed_export_adapter_retains_failure_and_no_retry(self):
        original = transfer.SourceLedger.reserve
        adapter = self.custody / 'lives/life/captures/000003/adapter/adapter_model.safetensors'
        def grow(instance, operation, life_id, kind, amount, discovery=False):
            result = original(instance, operation, life_id, kind, amount, discovery)
            if 'export-adapter:' in operation and str(adapter.relative_to(self.custody)) in operation:
                with adapter.open('ab', buffering=0) as stream:
                    stream.write(b'x')
            return result
        output = io.BytesIO()
        with patch.object(transfer.SourceLedger, 'reserve', grow):
            with self.assertRaisesRegex(ValueError, 'source_changed_during_export'):
                transfer.export(self.life, 3, output, root=self.custody, ledger=self.ledger, source_caps=self.caps)
        self.assertFalse((self.custody / 'exports/life_000003/COMPLETE.json').exists())
        self.assertTrue((self.custody / 'exports/life_000003/FAILED.json').exists())
        self.assertGreater(self.ledger.totals()['adapter'], 0)
        with self.assertRaises(FileExistsError):
            transfer.export(self.life, 3, io.BytesIO(), root=self.custody, ledger=self.ledger, source_caps=self.caps)
        output.seek(0)
        with self.assertRaises(ValueError):
            self.receive(output)
        self.no_positive()

    def test_existing_changed_registration_is_not_overwritten(self):
        self.receive()
        self.capture(4)
        registration = self.receiving / 'lives/life/REGISTERED.json'
        registration.write_bytes(b'changed synthetic metadata')
        with self.assertRaisesRegex(ValueError, 'identical_existing_registration_only'):
            self.receive(sleep=4)
        self.assertEqual(registration.read_bytes(), b'changed synthetic metadata')
        self.no_positive(sleep=4)

    def test_member_path_rejects_aliases_links_and_unapproved_files(self):
        for name in ('lives//life/REGISTERED.json', 'lives/life/./REGISTERED.json',
                '/lives/life/REGISTERED.json', '../lives/life/REGISTERED.json',
                'lives/life/captures/000003/adapter/optimizer_rng.pt'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                transfer.member_path(name, self.life, 3)
        header = tarfile.TarInfo('lives/life/REGISTERED.json')
        header.type, header.linkname = tarfile.SYMTYPE, '/unapproved'
        reader = common.ChargedStream(io.BytesIO(header.tobuf(format=tarfile.USTAR_FORMAT)),
            self.ledger, self.life, 'synthetic-special-member')
        with self.assertRaisesRegex(ValueError, 'no_special_transfer_member'):
            transfer.stream_member(reader)

    def test_short_stream_reads_use_precharged_remaining_credit_not_new_ledgers(self):
        class Short(io.BytesIO):
            def read(self, amount=-1):
                return super().read(min(amount, 7))
        stream = Short(b'short synthetic input')
        reader = common.ChargedStream(stream, self.ledger, self.life, 'short-stream')
        self.assertEqual(reader.exact(21), b'short synthetic input')
        rows = [row for row in self.ledger.totals()['rows'] if row['operation'].startswith('short-stream:')]
        self.assertEqual([row['bytes'] for row in rows], [21])

    def test_existing_hardwall_checked_during_stream_not_extended(self):
        reader = common.ChargedStream(io.BytesIO(b'ab'), self.ledger, self.life, 'expired-stream')
        original = self.ledger.reserve
        def expire(*args, **kwargs):
            result = original(*args, **kwargs)
            common.time.time.return_value = common.END
            return result
        with patch.object(self.ledger, 'reserve', side_effect=expire):
            with self.assertRaisesRegex(ValueError, 'read_window_ended'):
                reader.exact(2)
        self.assertEqual(reader.stream.tell(), 0)
        self.assertEqual(self.ledger.totals()['metadata'], 2)


if __name__ == '__main__':
    unittest.main()
