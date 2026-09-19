"""Synthetic CPU cases against independent C2/learner/frozen source types."""

import argparse
from copy import deepcopy
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from prefix_port import port, ORIGINAL_SHA256


WORKER = Path(__file__).resolve().parent
C2_SOURCE = WORKER.parent / 'post_recovery_c2_retention_receiver_20260919/portable_epoch3_v1/C2/epoch3/source'
PAIR_SOURCE = WORKER.parent / 'post_recovery_pair_retention_receiver_20260919/prepared_epoch2_v2/curriculum_learner/epoch2/source'
SOURCE = None
MODE = None


def raw_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PrefixTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='synthetic-', dir=WORKER)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.root = self.directory / 'journal'
        self.helper = importlib.import_module('gpu.immutable_prefix_proof')
        self.tail = importlib.import_module('gpu.checkpoint_tail_runtime')
        self.journal_module = importlib.import_module('gpu.orch_r125_stream_journal')
        self.stream_module = importlib.import_module('organism_v6.orch_r125_continual_stream')
        history = importlib.import_module('organism_v6.orch_r124_train_history')
        stream_type = self.stream_module.ContinualStream
        self.base = self.journal_module.StreamJournal
        if MODE != 'C2':
            self.recovery = importlib.import_module('gpu.r232_recovery')
            self.base = self.recovery.FrozenJournal if MODE == 'frozen' else self.recovery.LearnerJournal
            if MODE == 'frozen':
                stream_type = self.recovery.frozen.FrozenStream
        self.journal_type = self.base.__module__ + ':' + self.base.__qualname__
        self.source = dict(root=str(SOURCE), epoch=dict(path=str(SOURCE / 'EPOCH.json'),
            sha256=raw_sha(SOURCE / 'EPOCH.json')), pins={str(path.relative_to(SOURCE)): raw_sha(path)
            for path in SOURCE.rglob('*.py')})
        self.journal = self.base(self.root, create=True)
        self.addCleanup(self.journal.close)
        self.stream = stream_type(history.TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=6144, segment_tokens=128, segments_per_sleep=2,
            deadline_unix=10000, model_state_sha256='f' * 64)

    def parent(self, identifier='first'):
        path = self.journal.inbox / (identifier + '.json')
        path.write_text(json.dumps(dict(id=identifier, text='Synthetic parent feedback.', split='TRAIN', actor='parent')))
        return path

    def step(self, incoming=(), record=None, generate=None):
        if generate is None:
            generate = lambda *args, **kwargs: dict(raw='Synthetic child output.', token_ids=[10, 2],
                terminal=True, truncated=False)
        return self.stream.step(generate, lambda messages: sum(len(message['content'].split()) + 4
            for message in messages), self.journal.record if record is None else record,
            incoming=incoming, now=lambda: 100)

    def complete(self, sidecar=False):
        self.parent()
        self.step(self.journal.read_inbox())
        self.step()
        return self.finish_sleep(sidecar)

    def finish_sleep(self, sidecar=False):
        cycle = len(self.stream.sleep_receipts) + 1
        checkpoint = dict(optimizer_steps=0 if MODE == 'frozen' else 2, adapter_state_sha256='a' * 64,
            checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))
        receipt = dict(status='COMPLETE', cycle=cycle, optimizer_steps=checkpoint['optimizer_steps'],
            new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
            checkpoint=checkpoint, checkpoint_sha256=checkpoint['checkpoint_sha256'])
        if MODE == 'frozen':
            self.recovery.frozen.INITIAL = deepcopy(checkpoint)
            receipt.update(control_policy=self.recovery.frozen.POLICY, total_optimizer_steps=0,
                cumulative_optimizer_steps=0, weight_updates_enabled=False,
                no_update_reason='R232_frozen_sibling_updates_disabled', presentations=[],
                child_token_exposures=0, anchor_token_exposures=0, frozen_base_verified=True,
                before_adapter_sha256='a' * 64, after_adapter_sha256='a' * 64,
                before_optimizer_state_sha256='d' * 64, after_optimizer_state_sha256='d' * 64)
        if sidecar:
            reference = self.journal.record('R197_CORRECTION_CYCLE', dict(ledger=dict(
                schema='R197_CORRECTION_LEDGER_V1', life_id='synthetic', cycles=[])))
            (self.root / 'correction_cycle.json').write_text(json.dumps(dict(
                record_index=reference['index'], record_sha256=reference['sha256'])))
        self.stream.pending = 'sleep:' + self.stream_module.digest([row['source_sha256'] for row in self.stream.pending_rows()])
        self.journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=self.stream.checkpoint()))
        self.stream.pending = None
        self.stream.commit_sleep(receipt, self.journal.record)
        self.selection = dict(policy=self.tail.POLICY, root=str(self.root),
            journal_id=self.journal._manifest['journal_id'], complete_index=self.journal._state['index'] - 1,
            complete_sha256=self.journal._state['previous'], life_id='synthetic', max_tail_records=64,
            max_tail_bytes=16 * 1024 * 1024, sidecars=[] if not sidecar else [dict(
                name='correction_cycle.json', kind='R197_CORRECTION_CYCLE', required=True)],
            persist_complete_anchors=False)
        return self.selection

    def produce(self):
        self.proof = self.helper.produce(self.journal, self.selection, self.source, self.journal_type)
        return self.approve(self.proof)

    def approve(self, proof, **resume):
        self.proof_path = self.directory / 'proof.json'
        self.proof_path.write_bytes(self.helper.encoded(proof))
        self.guard = self.helper.guard_candidate(proof, str(self.proof_path), raw_sha(self.proof_path), **resume)
        self.guard_path = self.directory / 'operator_guard.json'
        self.guard_path.write_bytes(self.helper.encoded(self.guard))
        self.authority = dict(guard_path=str(self.guard_path), guard_sha256=raw_sha(self.guard_path))
        return self.authority

    def scan(self, authority=None, selection=None):
        return self.tail.scan(self.journal, self.selection if selection is None else selection,
            prefix_proof=self.authority if authority is None else authority)

    def file(self, index=1, intent=False):
        return self.root / 'records' / (f'{index:020d}' + ('.intent.json' if intent else '.json'))

    def reject(self, action, pattern=None):
        exception = (ValueError, OSError) if pattern is None else ValueError
        manager = self.assertRaises(exception) if pattern is None else self.assertRaisesRegex(exception, pattern)
        with manager:
            action()

    def test_producer_hashes_every_raw_prefix_and_intent(self):
        self.complete()
        self.journal.record('NOTE', dict(tail=True))
        with patch.object(self.tail, 'hash_record', wraps=self.tail.hash_record) as hashed:
            self.produce()
        self.assertEqual([call.args[1] for call in hashed.call_args_list],
            list(range(self.selection['complete_index'] + 1)))
        for record in self.proof['records']:
            self.assertEqual(set(record['identities']), {'.json', '.intent.json'})
            self.assertEqual(record['hashed']['raw_sha256'], raw_sha(self.file(record['header']['index'])))

    def test_full_state_parity_and_no_prefix_body_or_intent_reads(self):
        self.complete()
        self.produce()
        self.journal.record('R184_LEARN_COMPLETE', dict(cycle=1))
        self.parent('second')
        self.journal.read_inbox()
        expected = self.tail.scan(self.journal, self.selection)
        opened = []
        original_open = os.open
        def observe(name, *args, **kwargs):
            if kwargs.get('dir_fd') == self.journal._records_fd:
                opened.append(str(name))
            return original_open(name, *args, **kwargs)
        with patch.object(os, 'open', side_effect=observe), \
                patch.object(self.tail, 'hash_record', wraps=self.tail.hash_record) as hashed:
            actual = self.scan()
        self.assertEqual(self.helper.encoded(actual), self.helper.encoded(expected))
        self.assertEqual(actual['latest']['document']['state']['history'], self.stream.checkpoint()['state']['history'])
        self.assertEqual(len(actual['inbox']), 2)
        self.assertTrue(all(call.args[1] > self.selection['complete_index'] for call in hashed.call_args_list))
        prefix_reads = {name for name in opened if name[:20].isdigit()
            and int(name[:20]) <= self.selection['complete_index']}
        self.assertEqual(prefix_reads, {f'{self.selection["complete_index"]:020d}.json'})
        receipt = self.journal.checkpoint_tail_receipt
        self.assertTrue(receipt['prefix_proof']['full_raw_tail_verified'])
        self.assertEqual(receipt['raw_record_bytes_hashed'], sum(self.file(index).stat().st_size
            for index in range(self.selection['complete_index'] + 1, actual['index'])))

    def test_required_sidecar_still_decoded_and_validated(self):
        self.complete(sidecar=True)
        self.produce()
        expected = self.tail.scan(self.journal, self.selection)
        self.assertEqual(self.scan(), expected)
        (self.root / 'correction_cycle.json').write_text('{"record_index":999,"record_sha256":"bad"}')
        self.reject(self.scan, 'sidecar')

    def test_sidecar_only_additional_prefix_body_read(self):
        self.complete(sidecar=True)
        self.produce()
        decoded = []
        original = self.tail._decoded_record
        def observe(journal, header):
            decoded.append(header['index'])
            return original(journal, header)
        with patch.object(self.tail, '_decoded_record', side_effect=observe):
            self.scan()
        expected = [record['header']['index'] for record in self.proof['records']
            if record['header']['kind'] in ('SLEEP_COMPLETE', 'R197_CORRECTION_CYCLE')]
        self.assertEqual(set(decoded), set(expected))

    def test_pending_request_parity(self):
        self.complete()
        self.produce()
        def fail(*args, **kwargs):
            raise RuntimeError('synthetic_generation_interruption')
        with self.assertRaises(RuntimeError):
            self.step(generate=fail)
        state = self.scan()
        self.assertEqual(state, self.journal._state)
        self.assertIsNotNone(state['request'])
        self.assertIsNotNone(state['latest']['document']['state']['pending'])

    def test_pending_response_parity(self):
        self.complete()
        self.produce()
        def record(kind, document):
            if kind == 'COMMITTED':
                raise RuntimeError('synthetic_precommit_interruption')
            return self.journal.record(kind, document)
        with self.assertRaises(RuntimeError):
            self.step(record=record)
        state = self.scan()
        self.assertEqual(state, self.journal._state)
        self.assertIsNotNone(state['response'])

    def test_pending_sleep_parity(self):
        self.complete()
        self.produce()
        self.step()
        self.stream.pending = 'sleep:' + self.stream_module.digest([row['source_sha256'] for row in self.stream.pending_rows()])
        self.journal.record('SLEEP_REQUEST', dict(cycle=2, resume_state=self.stream.checkpoint()))
        state = self.scan()
        self.assertEqual(state, self.journal._state)
        self.assertIsNotNone(state['sleep_request'])

    def test_unregistered_mailbox_preserved_and_missing_registered_refused(self):
        self.complete()
        self.produce()
        self.parent('waiting')
        state = self.scan()
        self.assertNotIn('waiting', state['inbox'])
        self.assertEqual(state, self.journal._state)
        self.assertEqual(len(self.journal.read_inbox()), 2)
        self.assertEqual(self.scan(), self.journal._state)
        (self.journal.inbox / 'first.json').unlink()
        self.reject(self.journal.read_inbox, 'registered_inbox_file_missing')

    def test_default_scan_and_full_audit_unchanged(self):
        self.complete()
        self.produce()
        self.guard_path.unlink()
        with patch.object(self.helper, 'prepare', side_effect=AssertionError('implicit_proof_lookup')), \
                patch.object(self.tail, 'hash_record', wraps=self.tail.hash_record) as hashed:
            self.assertEqual(self.tail.scan(self.journal, self.selection), self.journal._state)
        self.assertEqual(hashed.call_count, self.journal._state['index'])
        with patch.object(self.tail, 'scan', side_effect=AssertionError('explicit_audit_must_not_use_fast_scan')):
            receipt = self.journal.audit()
        self.assertEqual(receipt['record_count'], self.journal._state['index'])

    def test_missing_unpinned_and_forged_proof_refuse_no_fallback(self):
        self.complete()
        self.produce()
        for authority in ({}, dict(guard_path=str(self.guard_path)),
                dict(self.authority, guard_sha256='0' * 64)):
            with self.subTest(authority=authority), patch.object(self.tail, 'hash_record') as hashed:
                self.reject(lambda: self.scan(authority))
                hashed.assert_not_called()
        self.proof_path.write_bytes(self.proof_path.read_bytes().replace(b'Synthetic', b'Counterfeit'))
        self.reject(self.scan, 'external_sha_mismatch')
        self.proof_path.unlink()
        self.reject(self.scan)

    def test_changed_guard_and_changed_selection_refuse(self):
        self.complete()
        self.produce()
        self.reject(lambda: self.scan(selection=dict(self.selection, complete_sha256='a' * 64)), 'approved_resume_selection')
        self.guard['proof_sha256'] = '0' * 64
        self.guard_path.write_bytes(self.helper.encoded(self.guard))
        self.reject(self.scan, 'external_sha_mismatch')

    def test_valid_proof_with_forged_inbox_body_refused_even_if_repinned(self):
        self.complete()
        self.produce()
        inbox_record = next(record for record in self.proof['records'] if record['inbox_document'] is not None)
        inbox_record['inbox_document']['message']['text'] = 'Not the original parent.'
        self.approve(self.proof)
        self.reject(self.scan, 'cached_inbox_header_binding')

    def test_schema_header_chain_and_intent_identity_schema_refused(self):
        self.complete()
        self.produce()
        original = deepcopy(self.proof)
        mutations = (
            lambda proof: proof.update(schema='unknown'),
            lambda proof: proof['records'][1]['header'].update(previous_sha256='0' * 64),
            lambda proof: proof['records'][1]['identities'].pop('.intent.json'),
            lambda proof: proof['records'][1]['header'].update(index=True),
            lambda proof: proof['records'][1]['hashed'].update(bytes=False),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                malformed = deepcopy(original)
                mutate(malformed)
                self.approve(malformed)
                self.reject(self.scan)

    def test_root_journal_boot_namespace_and_type_binding(self):
        self.complete()
        self.produce()
        original = deepcopy(self.proof)
        mutations = (
            lambda proof: proof['binding']['selection'].update(root=str(self.directory)),
            lambda proof: proof['binding']['selection'].update(journal_id='0' * 32),
            lambda proof: proof['binding']['environment'].update(boot_id='0' * 36),
            lambda proof: proof['binding']['environment']['mount_namespace'].update(ino=0),
            lambda proof: proof['binding'].update(trust='anything'),
            lambda proof: proof['binding'].update(journal_type='gpu.orch_r125_stream_journal:MadeUp'),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                malformed = deepcopy(original)
                mutate(malformed)
                self.approve(malformed)
                with self.assertRaises((ValueError, AttributeError)):
                    self.scan()

    def test_raw_tamper_with_restored_mtime_refused(self):
        self.complete()
        self.produce()
        path = self.file()
        prior = path.stat()
        content = path.read_bytes()
        self.assertIn(b'System.', content)
        path.write_bytes(content.replace(b'System.', b'System!', 1))
        os.utime(path, ns=(prior.st_atime_ns, prior.st_mtime_ns))
        self.assertEqual(path.stat().st_size, prior.st_size)
        self.reject(self.scan, 'prefix_record_or_intent_changed')

    def test_ctime_only_change_refused(self):
        self.complete()
        self.produce()
        path = self.file()
        prior = path.stat()
        os.chmod(path, prior.st_mode ^ 0o100)
        os.chmod(path, prior.st_mode)
        self.assertNotEqual(path.stat().st_ctime_ns, prior.st_ctime_ns)
        self.assertEqual(path.stat().st_mtime_ns, prior.st_mtime_ns)
        self.reject(self.scan, 'prefix_record_or_intent_changed')

    def test_same_bytes_new_inode_refused(self):
        self.complete()
        self.produce()
        path = self.file()
        prior = path.stat()
        replacement = self.directory / 'replacement'
        replacement.write_bytes(path.read_bytes())
        os.utime(replacement, ns=(prior.st_atime_ns, prior.st_mtime_ns))
        os.replace(replacement, path)
        self.assertNotEqual(path.stat().st_ino, prior.st_ino)
        self.reject(self.scan, 'prefix_record_or_intent_changed')

    def test_deleted_prefix_refused(self):
        self.complete()
        self.produce()
        self.file().unlink()
        self.reject(self.scan)

    def test_symlinked_prefix_and_proof_refused(self):
        self.complete()
        self.produce()
        path = self.file()
        retained = self.directory / 'retained'
        path.rename(retained)
        path.symlink_to(retained)
        self.reject(self.scan)
        path.unlink()
        retained.rename(path)
        self.produce()
        retained = self.directory / 'retained_proof'
        self.proof_path.rename(retained)
        self.proof_path.symlink_to(retained)
        self.reject(self.scan)

    def test_replaced_records_directory_refused(self):
        self.complete()
        self.produce()
        original = self.root / 'records'
        original.rename(self.root / 'retained_records')
        original.mkdir()
        self.reject(self.scan)

    def test_symlinked_root_ancestor_refused(self):
        self.complete()
        self.produce()
        original = self.directory
        moved = original.with_name(original.name + '-moved')
        original.rename(moved)
        original.symlink_to(moved, target_is_directory=True)
        try:
            self.reject(self.scan)
        finally:
            original.unlink()
            moved.rename(original)

    def test_intent_changed_refused(self):
        self.complete()
        self.produce()
        self.file(intent=True).write_text('{}\n')
        self.reject(self.scan, 'prefix_record_or_intent_changed')

    def test_same_intent_bytes_new_inode_refused(self):
        self.complete()
        self.produce()
        path = self.file(intent=True)
        prior = path.stat()
        replacement = self.directory / 'intent_replacement'
        replacement.write_bytes(path.read_bytes())
        os.utime(replacement, ns=(prior.st_atime_ns, prior.st_mtime_ns))
        os.replace(replacement, path)
        self.assertNotEqual(path.stat().st_ino, prior.st_ino)
        self.reject(self.scan, 'prefix_record_or_intent_changed')

    def test_intent_ctime_and_symlink_refused(self):
        self.complete()
        self.produce()
        path = self.file(intent=True)
        prior = path.stat()
        os.chmod(path, prior.st_mode ^ 0o100)
        os.chmod(path, prior.st_mode)
        self.reject(self.scan, 'prefix_record_or_intent_changed')
        self.produce()
        retained = self.directory / 'retained_intent'
        path.rename(retained)
        path.symlink_to(retained)
        self.reject(self.scan)

    def test_producer_rejects_invalid_raw_prefix_and_intent(self):
        self.complete()
        path = self.file(intent=True)
        original = path.read_bytes()
        path.write_text('{}\n')
        self.reject(self.produce, 'intent_binding')
        path.write_bytes(original)
        path = self.file()
        path.write_bytes(path.read_bytes().replace(b'System.', b'System!', 1))
        self.reject(self.produce, 'raw_record_integrity')

    def test_producer_final_recheck_catches_earlier_prefix_change(self):
        self.complete()
        original = self.tail.hash_record
        def mutate(journal, index):
            result = original(journal, index)
            if index == self.selection['complete_index']:
                self.file().touch()
            return result
        with patch.object(self.tail, 'hash_record', side_effect=mutate):
            self.reject(self.produce, 'changed_during_production')

    def test_corrupt_tail_and_intent_refused(self):
        self.complete()
        self.produce()
        reference = self.journal.record('NOTE', dict(text='Uncorrupted'))
        path = self.file(reference['index'])
        original = path.read_bytes()
        path.write_bytes(original.replace(b'Uncorrupted', b'Notcorrupt!'))
        self.reject(self.scan, 'raw_record_integrity')
        path.write_bytes(original)
        self.file(reference['index'], intent=True).write_text('{}\n')
        self.reject(self.scan, 'intent_binding')

    def test_final_recheck_catches_prefix_mutation_during_tail_decode(self):
        self.complete()
        self.produce()
        reference = self.journal.record('NOTE', dict(tail=True))
        original = self.tail._decoded_record
        def mutate(journal, header):
            result = original(journal, header)
            if header['index'] == reference['index']:
                self.file().touch()
            return result
        with patch.object(self.tail, '_decoded_record', side_effect=mutate):
            self.reject(self.scan, 'prefix_record_or_intent_changed')

    def test_final_recheck_catches_tail_mutation_during_decode(self):
        self.complete()
        self.produce()
        reference = self.journal.record('NOTE', dict(tail=True))
        original = self.tail._decoded_record
        def mutate(journal, header):
            result = original(journal, header)
            if header['index'] == reference['index']:
                self.file(reference['index'], intent=True).touch()
            return result
        with patch.object(self.tail, '_decoded_record', side_effect=mutate):
            self.reject(self.scan, 'tail_changed_during_scan')

    def test_changed_or_missing_source_epoch_refused(self):
        self.complete()
        self.produce()
        path = SOURCE / 'EPOCH.json'
        original = path.read_bytes()
        try:
            path.write_bytes(original + b'\n')
            self.reject(self.scan, 'exact_separate_source_epoch')
            path.unlink()
            self.reject(self.scan)
        finally:
            path.write_bytes(original)

    def test_changed_proof_or_guard_during_scan_refused(self):
        self.complete()
        self.produce()
        original = self.tail._decoded_record
        for path in (self.proof_path, self.guard_path):
            def mutate(journal, header):
                result = original(journal, header)
                path.touch()
                return result
            with self.subTest(path=path.name), patch.object(self.tail, '_decoded_record', side_effect=mutate):
                self.reject(self.scan, 'external_file_changed')

    def test_swapped_inbox_directory_or_lock_refused(self):
        self.complete()
        self.produce()
        directory = self.root / 'inbox'
        retained = self.root / 'retained_inbox'
        directory.rename(retained)
        directory.mkdir()
        self.reject(self.scan)
        directory.rmdir()
        retained.rename(directory)
        self.produce()
        lock = self.root / 'WRITER.lock'
        lock.rename(self.root / 'retained_lock')
        lock.write_bytes(b'')
        self.reject(self.scan)

    def test_source_byte_change_refused(self):
        self.complete()
        self.produce()
        path = SOURCE / 'gpu/checkpoint_tail_runtime.py'
        original = path.read_bytes()
        try:
            path.write_bytes(original + b'\n')
            self.reject(self.scan, 'exact_source_bytes')
        finally:
            path.write_bytes(original)

    def test_manifest_replacement_same_bytes_refused(self):
        self.complete()
        self.produce()
        path = self.root / 'JOURNAL.json'
        replacement = self.directory / 'replacement'
        replacement.write_bytes(path.read_bytes())
        os.replace(replacement, path)
        self.reject(self.scan, 'original_directories_or_manifest_changed')

    def test_bounds_still_enforced(self):
        self.complete()
        self.selection['max_tail_records'] = 1
        self.produce()
        self.journal.record('NOTE', dict(tail=1))
        self.journal.record('NOTE', dict(tail=2))
        self.reject(self.scan, 'record_bound_exceeded')

    def test_tail_byte_bound_still_enforced(self):
        self.complete()
        self.selection['max_tail_bytes'] = 1
        self.produce()
        self.journal.record('NOTE', dict(tail=True))
        self.reject(self.scan, 'byte_bound_exceeded')

    def test_tail_header_valid_but_semantically_invalid_refused(self):
        self.complete()
        self.produce()
        index = self.journal._state['index']
        record = dict(schema='R125_STREAM_JOURNAL_V1', journal_id=self.journal._manifest['journal_id'],
            index=index, kind='RESPONSE', previous_sha256=self.journal._state['previous'],
            document=dict(request_sha256='a' * 64))
        record['sha256'] = self.journal_module._digest(record)
        self.journal._publish(self.journal._records_fd, f'{index:020d}.intent.json', self.journal._intent(record))
        self.journal._publish(self.journal._records_fd, f'{index:020d}.json', record)
        self.reject(self.scan, 'response_without_unique_request')

    def test_independent_pair_classes_not_interchangeable(self):
        self.complete()
        self.produce()
        self.assertEqual(self.proof['binding']['journal_type'], self.journal_type)
        if MODE == 'C2':
            self.assertEqual(self.journal_type, 'gpu.orch_r125_stream_journal:StreamJournal')
        else:
            alternative = 'LearnerJournal' if MODE == 'frozen' else 'FrozenJournal'
            self.proof['binding']['journal_type'] = 'gpu.r232_recovery:' + alternative
            self.approve(self.proof)
            self.reject(self.scan, 'independent_journal_type_required')

    def advance_complete(self):
        origin = deepcopy(self.selection)
        self.parent('between-completes')
        self.step(self.journal.read_inbox())
        self.step()
        selected = self.finish_sleep()
        self.journal.record('R184_LEARN_COMPLETE', dict(cycle=2))
        self.parent('after-selected-complete')
        self.journal.read_inbox()
        self.parent('unregistered-after-selected')
        return dict(resume_selection=deepcopy(selected),
            max_advance_records=selected['complete_index'] - origin['complete_index'],
            max_advance_bytes=sum(self.file(index).stat().st_size
                for index in range(origin['complete_index'] + 1, selected['complete_index'] + 1)))

    def test_approved_A_to_B_complete_LEARN_INBOX_raw_interval_and_state_parity(self):
        origin = self.complete()
        self.produce()
        resume = self.advance_complete()
        self.reject(self.scan, 'exact_approved_resume_selection')
        self.approve(self.proof, **resume)
        expected = self.tail.scan(self.journal, self.selection)
        decoded = []
        original = self.tail._decoded_record
        def observe(journal, header):
            decoded.append(header['index'])
            return original(journal, header)
        with patch.object(self.tail, 'hash_record', wraps=self.tail.hash_record) as hashed, \
                patch.object(self.tail, '_decoded_record', side_effect=observe):
            actual = self.scan()
        self.assertEqual(actual, self.journal._state)
        self.assertEqual(self.helper.encoded(actual), self.helper.encoded(expected))
        self.assertEqual(self.helper.encoded(actual['latest']['document']['state']['history']),
            self.helper.encoded(self.stream.checkpoint()['state']['history']))
        self.assertEqual([call.args[1] for call in hashed.call_args_list],
            list(range(origin['complete_index'] + 1, actual['index'])))
        self.assertTrue(all(index > origin['complete_index'] for index in decoded))
        self.assertEqual(set(actual['inbox']), {'first', 'between-completes', 'after-selected-complete'})
        self.assertNotIn('unregistered-after-selected', actual['inbox'])
        receipt = self.journal.checkpoint_tail_receipt['prefix_proof']
        self.assertEqual(receipt['raw_extension_records'], resume['max_advance_records'])
        self.assertEqual(receipt['raw_extension_bytes_hashed'], resume['max_advance_bytes'])
        self.assertEqual(receipt['prevalidated_complete_index'], origin['complete_index'])
        self.assertEqual(receipt['selected_complete_index'], self.selection['complete_index'])
        self.assertEqual(len(self.journal.read_inbox()), 4)
        self.assertEqual(self.scan(), self.journal._state)

    def test_forward_interval_raw_and_intent_corruption_refuse(self):
        origin = self.complete()
        self.produce()
        self.approve(self.proof, **self.advance_complete())
        path = self.file(origin['complete_index'] + 1)
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b'Synthetic', b'Corrupted', 1))
        self.reject(self.scan, 'raw_record_integrity')
        path.write_bytes(raw)
        self.file(origin['complete_index'] + 1, intent=True).write_bytes(b'{}\n')
        self.reject(self.scan, 'intent_binding')

    def test_forward_authority_bounds_policy_and_rollback(self):
        origin = self.complete()
        self.produce()
        resume = self.advance_complete()
        forbidden = (
            dict(resume, max_advance_records=resume['max_advance_records'] - 1),
            dict(resume, max_advance_bytes=0),
            dict(resume, max_advance_records=True),
            dict(resume, resume_selection=dict(self.selection, complete_index=origin['complete_index'] - 1)),
            dict(resume, resume_selection=dict(self.selection, max_tail_bytes=self.selection['max_tail_bytes'] + 1)),
            dict(resume, resume_selection=dict(self.selection, sidecars=[dict(name='another.json',
                kind='R197_CORRECTION_CYCLE', required=False)])),
            dict(resume, resume_selection=dict(self.selection, persist_complete_anchors=True)),
        )
        for policy in forbidden:
            with self.subTest(policy=policy):
                self.reject(lambda: self.approve(self.proof, **policy))
        self.approve(self.proof, **dict(resume, max_advance_bytes=resume['max_advance_bytes'] - 1))
        with patch.object(self.tail, 'hash_record') as hashed:
            self.reject(self.scan, 'advance_byte_bound_exceeded')
            hashed.assert_not_called()

    def test_wrong_later_complete_hash_not_inferred_from_journal(self):
        self.complete()
        self.produce()
        resume = self.advance_complete()
        wrong = dict(self.selection, complete_sha256='e' * 64)
        self.approve(self.proof, **dict(resume, resume_selection=wrong))
        self.reject(lambda: self.scan(selection=wrong), 'exact_complete_pin')

    def test_namespace_mismatch_refused_even_with_exact_source_and_prefix(self):
        self.complete()
        self.produce()
        changed = deepcopy(self.proof['binding']['environment'])
        changed['mount_namespace']['ino'] += 1
        with patch.object(self.helper, 'environment', return_value=changed):
            self.reject(self.scan, 'same_trusted_environment')

    def test_cli_bind_forward_resume_without_prefix_read_or_rehash(self):
        self.complete()
        self.produce()
        resume = self.advance_complete()
        selection_path = self.directory / 'selected_complete.json'
        selection_path.write_bytes(self.helper.encoded(self.selection))
        guard_path = self.directory / 'forward_guard.json'
        result = subprocess.run([sys.executable, '-B', str(WORKER / 'prefix_cli.py'), 'bind-resume',
            '--proof', str(self.proof_path), '--proof-sha256', raw_sha(self.proof_path),
            '--selection', str(selection_path), '--selection-sha256', raw_sha(selection_path),
            '--max-advance-records', str(resume['max_advance_records']),
            '--max-advance-bytes', str(resume['max_advance_bytes']), '--guard-candidate-output', str(guard_path)],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True, timeout=40)
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['status'], 'CANDIDATE_NOT_AUTHORIZATION')
        self.assertEqual(receipt['prefix_body_reads'], 0)
        self.assertEqual(self.scan(dict(guard_path=str(guard_path), guard_sha256=raw_sha(guard_path))),
            self.journal._state)

    def test_cli_producer_and_readonly_probe_no_writer_lock(self):
        self.complete()
        request_path = self.directory / 'request.json'
        request_path.write_bytes(self.helper.encoded(dict(schema='R233_PREFIX_PRODUCER_REQUEST_V1',
            source=self.source, journal_type=self.journal_type, selection=self.selection)))
        proof_path = self.directory / 'cli_proof.json'
        guard_path = self.directory / 'cli_guard.json'
        command = [sys.executable, '-B', str(WORKER / 'prefix_cli.py')]
        result = subprocess.run(command + ['produce', '--request', str(request_path), '--request-sha256',
            raw_sha(request_path), '--proof-output', str(proof_path), '--guard-candidate-output', str(guard_path)],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True, timeout=40)
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['status'], 'CANDIDATE_NOT_AUTHORIZATION')
        result = subprocess.run(command + ['probe', '--guard', str(guard_path), '--guard-sha256', raw_sha(guard_path)],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True, timeout=40)
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertFalse(receipt['writer_lock_acquired'])
        self.assertEqual(receipt['journal_writes'], 0)
        self.assertEqual(receipt['receipt']['restored_state_sha256'], self.journal._state['latest']['expected_sha256'])


def candidate_source(original, destination):
    for package in ('gpu', 'organism_v6'):
        for path in (original / package).rglob('*.py'):
            output = destination / path.relative_to(original)
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, output)
    target = destination / 'gpu/checkpoint_tail_runtime.py'
    target.write_bytes(port(target.read_bytes()))
    shutil.copyfile(WORKER / 'immutable_prefix_proof.py', destination / 'gpu/immutable_prefix_proof.py')
    (destination / 'EPOCH.json').write_text(json.dumps(dict(schema='SYNTHETIC_SOURCE_EPOCH',
        root=str(destination), original=str(original))))
    tests = destination / 'tests'
    tests.mkdir()
    shutil.copyfile(original / 'tests/test_orch_r125_stream_journal.py', tests / 'test_orch_r125_stream_journal.py')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--mode', choices=('C2', 'learner', 'frozen'))
    parser.add_argument('--receipt', type=Path)
    arguments = parser.parse_args()
    if arguments.source is not None:
        SOURCE, MODE = arguments.source, arguments.mode
        sys.path.insert(0, str(SOURCE))
        started = time.monotonic()
        outcome = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PrefixTests))
        print(json.dumps(dict(mode=MODE, tests=outcome.testsRun, passed=outcome.wasSuccessful(),
            errors=len(outcome.errors), failures=len(outcome.failures), seconds=time.monotonic() - started)))
        sys.exit(0 if outcome.wasSuccessful() else 1)
    original = (C2_SOURCE / 'gpu/checkpoint_tail_runtime.py').read_bytes()
    assert hashlib.sha256(original).hexdigest() == ORIGINAL_SHA256
    try:
        port(original + b'\n')
    except ValueError:
        pass
    else:
        raise AssertionError('inexact_source_port_not_rejected')
    failures = 0
    results = []
    for mode in ('C2', 'learner', 'frozen'):
        with tempfile.TemporaryDirectory(prefix='source-test-', dir=WORKER) as directory:
            source = Path(directory) / 'source'
            candidate_source(C2_SOURCE if mode == 'C2' else PAIR_SOURCE, source)
            print('SYNTHETIC_MODE=' + mode, flush=True)
            result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()),
                '--source', str(source), '--mode', mode],
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'), timeout=180,
                capture_output=True, text=True)
            print(result.stderr, end='')
            print(result.stdout, end='', flush=True)
            results.append(json.loads(result.stdout.splitlines()[-1]))
            failures += result.returncode != 0
            if mode == 'C2':
                result = subprocess.run([sys.executable, '-B', str(WORKER.parent /
                    'rohin233_recovery_node4_20260918/checkpoint_tail_tests.py')],
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                        TMPDIR=str(Path(directory)), CHECKPOINT_TAIL_SOURCE=str(source)),
                    capture_output=True, text=True, timeout=90)
                print('ORIGINAL_DEFAULT_CHECKPOINT_TAIL_SUITE', flush=True)
                print(result.stderr, end='')
                print(result.stdout, end='', flush=True)
                failures += result.returncode != 0
                default_passed = result.returncode == 0
    if arguments.receipt is not None:
        receipt = dict(schema='R233_PREFIX_PROOF_SYNTHETIC_RECEIPT_V1', created_unix=time.time(),
            matrices=results, synthetic_tests=sum(result['tests'] for result in results),
            original_default_suite_passed=default_passed, passed=not failures,
            original_reader_sha256=ORIGINAL_SHA256,
            candidate_reader_sha256=hashlib.sha256(port(original)).hexdigest(),
            artifacts={name: raw_sha(WORKER / name) for name in
                ('prefix_port.py', 'immutable_prefix_proof.py', 'prefix_cli.py', 'test_prefix_proof.py')},
            live_actions=False, actual_node_proof_or_timing_performed=False, reservation_limit_changed=False)
        with arguments.receipt.open('x') as stream:
            json.dump(receipt, stream, sort_keys=True, indent=2)
            stream.write('\n')
    sys.exit(bool(failures))
