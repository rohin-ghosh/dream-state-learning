"""Synthetic CPU fixtures only; never contacts a node, native, model or scorer."""

from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu.ny_caption_life import child_act, latest_own_think
from gpu.ny_caption_life_service import LifeSession
from research_loop.workers.rohin221_continuous_caption_20260918 import journal_bundle, journal_transport
from research_loop.workers.rohin221_continuous_caption_20260918.shared_scorer import serve
from research_loop.workers.rohin233_ovx4_recovery_20260918.dual_judge import EpochSessionMixin
from research_loop.workers.rohin233_ovx4_recovery_20260918.judge_epoch import EpochLedger
from research_loop.workers.post_reboot_node3_parents_20260919.projected_wire import contract as subject
from research_loop.workers.post_reboot_node3_parents_20260919.projected_wire.continuation import gate, reattach_existing_epoch
from research_loop.workers.post_reboot_node3_parents_20260919.projected_wire.custody import OwnerStore, load_binding
from research_loop.workers.post_reboot_node3_parents_20260919.projected_wire.receiver import ProjectedHub, envelope
from research_loop.workers.post_reboot_node3_parents_20260919.projected_wire import relay


MODULE = 'research_loop.workers.post_reboot_node3_parents_20260919.projected_wire.cli'


def records(root, raw_act='Question: How?', raw_think='Scene1:\nCaption: A literal THINK caption.', state_bytes=100,
            prior_stage='THINK'):
    directory = root/'stream/records'
    directory.mkdir(parents=True, exist_ok=True)
    think = dict(response=dict(raw=raw_think))
    act = dict(response=dict(raw=raw_act))
    documents = [('RESPONSE', think), ('COMMITTED', dict(source_sha256=subject.digest(think), state='x'*state_bytes)),
        ('R184_STAGE', dict(stage=prior_stage, source_sha256=subject.digest(think))),
        ('CONTEXT_INPUT', dict(state='x'*state_bytes)), ('REQUEST', dict(state='x'*state_bytes)),
        ('RESPONSE', act), ('COMMITTED', dict(source_sha256=subject.digest(act), state='x'*state_bytes)),
        ('R184_STAGE', dict(stage='ACT', source_sha256=subject.digest(act)))]
    previous = 'seed'
    for index, (kind, document) in enumerate(documents):
        record = dict(index=index, journal_id='synthetic-journal', kind=kind, document=document, previous_sha256=previous)
        record['sha256'] = subject.digest(record)
        (directory/f'{index:020d}.json').write_bytes(subject.canonical(record))
        previous = record['sha256']
        if index == 5:
            origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=index, record_sha256=previous)
    return origin


class SyntheticGame:
    def __init__(self):
        self.received = []
        self._submissions = {}
        self._judge = SimpleNamespace(pending=[])

    def snapshot(self):
        return dict(received=deepcopy(self.received))

    def restore(self, state):
        self.received = deepcopy(state['received'])

    def submit_caption(self, contest, caption):
        repeated = [contest, caption] in self.received
        self.received.append([contest, caption])
        result = dict(ok=True, accepted=True, status='repeat' if repeated else 'new_pixel',
            rank=7, reference_count=64, top_k=50, replayed=repeated)
        self._submissions[(contest, caption)] = result
        admitted = self._judge.ledger.admit(self._judge.origin, contest, caption, cached=repeated)
        if admitted['admitted']:
            self._judge.pending.append(dict(key=admitted['key'], contest_id=contest, caption=caption, shadow=result))
        return result


class NativeEpoch(EpochSessionMixin, LifeSession):
    pass


class ProjectedWireTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.life = self.root/'life'
        self.request = dict(origin=records(self.life), metrics=dict(THINK=9, ACT=5, LEARN=0))
        self.anchor = self.root/'anchor.json'
        self.anchor.write_bytes(b'{"synthetic_cpu_only":true}')
        self.registry = dict(session_id='synthetic_fork', host_alias='ovx2', native_pid=os.getpid(),
            life_root=str(self.life), minimum_origin_record_index=5, journal=dict(journal_id='synthetic-journal'))
        self.epoch_binding = dict(player='synthetic_fork', primary_step=15625, primary_rank=8, shadow_step=6250,
            shadow_seconds=3600, previous_session_sha256='1'*64, new_judge_manifest_sha256='2'*64,
            old_judge_manifest_sha256='3'*64)
        deadline = time.time() + 600
        self.binding = dict(schema=subject.BINDING_SCHEMA, session_id='synthetic_fork', transport_epoch='4'*64,
            deadline_unix=deadline, prior_deadline_unix=deadline, lease_boundary_unix=deadline+21600,
            registry=self.registry, native_identity=subject.identity(os.getpid()),
            anchors=[dict(path=str(self.anchor), sha256=subject.byte_digest(self.anchor.read_bytes()))],
            validator_sha256=subject.source_digest(), judge_epoch_sha256=subject.digest(self.epoch_binding),
            mirror_root=str(self.root/'empty_mirror'), authority_sha256='5'*64)
        self.store_root = self.root/'owner'
        self.store_root.mkdir(mode=0o700)
        self.store = OwnerStore(self.store_root, os.getuid())
        self.addCleanup(self.store.close)

    def make_session(self, name, life_root):
        output = self.root/name
        output.mkdir()
        session = NativeEpoch(SyntheticGame(), life_root, output, ['scene-one'], session_binding=deepcopy(self.registry))
        session.epoch_ledger = EpochLedger(self.root/(name+'-epoch'), self.epoch_binding)
        session.epoch_ledger.activate('6'*64, unix=100)
        return session

    def make_hub(self):
        session = self.make_session('projected', self.binding['mirror_root'])
        root = self.root/'listener'
        root.mkdir()
        original = SimpleNamespace(root=root, sessions={'synthetic_fork':session}, registry={'synthetic_fork':self.registry},
            native=Mock(), generation=Mock(return_value=dict(unchanged_base=True)))
        hub = ProjectedHub(original, self.store, {'synthetic_fork':self.binding})
        return hub, session

    def collect(self):
        return subject.collect(self.binding, self.request)

    def staged(self):
        receipt = self.collect()
        token = self.store.install(receipt)
        return envelope(self.binding, self.request, token), receipt

    def test_exact_original_raw_stage_and_THINK_parity(self):
        receipt = self.collect()
        self.assertEqual(receipt['raw_act'], child_act(self.life, self.request['origin']))
        self.assertEqual(receipt['think'], latest_own_think(self.life, self.request['origin']))
        self.assertEqual(receipt['stages']['ACT']['committed_indices'], [6])
        self.assertEqual(receipt['stages']['THINK']['committed_indices'], [1])
        self.assertEqual([record['index'] for record in receipt['records']], list(range(8)))
        self.assertEqual(subject.validate_receipt(receipt, self.binding), receipt)

    def test_full_parser_salvage_offsets_outcomes_and_budget_parity(self):
        cases = [
            ('Question: How?', 'Scene1:\nCaption: A literal THINK caption.'),
            ('Scene1:\nCaption: Literal ACT snowman ☃.', 'Scene1:\nCaption: Unused THINK.'),
            ('Scene1:\r\nCaption: Unicode café ☃.\r\nAn unclear afterthought.', 'Scene1:\nCaption: Different THINK.'),
            ('Scene1:\nCaption: Same caption.\nUnclear afterthought.', 'Scene1:\nCaption: Same caption.\nCaption: Second caption.'),
            ('Question: How?', 'Private analysis without a literal caption.'),
        ]
        for ordinal, (raw_act, raw_think) in enumerate(cases):
            with self.subTest(case=ordinal):
                self.request['origin'] = records(self.life, raw_act, raw_think)
                receipt = self.collect()
                original = self.make_session('original'+str(ordinal), self.life)
                projected = self.make_session('projection'+str(ordinal), self.binding['mirror_root'])
                hub = ProjectedHub(SimpleNamespace(root=self.root, sessions={'synthetic_fork':projected},
                    registry={'synthetic_fork':self.registry}), self.store, {'synthetic_fork':self.binding})
                expected = original.process(self.request)
                token = self.store.install(receipt)
                with patch('gpu.ny_caption_life_service.child_act', side_effect=AssertionError('receiver_must_not_read_native')):
                    actual = hub.native(envelope(self.binding, self.request, token))
                self.assertEqual(actual['report'], expected['report'])
                self.assertEqual(projected.game.snapshot(), original.game.snapshot())
                self.assertEqual(projected.policy.snapshot(), original.policy.snapshot())
                self.assertEqual(projected.seen, original.seen)
                identifier = self.request['origin']['record_sha256']
                original_result = json.loads((original.output/'attempts'/identifier/'RESULT.json').read_bytes())
                projected_result = json.loads((projected.output/'attempts'/identifier/'RESULT.json').read_bytes())
                original_result.pop('unix'); projected_result.pop('unix')
                self.assertEqual(projected_result, original_result)
                self.assertEqual(projected.epoch_ledger.epoch_sha256, self.binding['judge_epoch_sha256'])
                self.assertEqual(json.loads((projected.epoch_ledger.root/'ACTIVE.json').read_bytes())['shadow_end_unix'], 3700)

    def test_original_no_THINK_boundary_is_preserved_not_backfilled(self):
        self.request['origin'] = records(self.life, prior_stage='ACT')
        receipt = self.collect()
        self.assertIsNone(latest_own_think(self.life, self.request['origin']))
        self.assertIsNone(receipt['think'])
        self.assertEqual(receipt['think_boundary']['index'], 2)
        self.assertEqual(receipt['think_boundary']['reason'], 'original_stage_boundary')
        subject.validate_receipt(receipt, self.binding)

    def test_real_oversized_window_validates_locally_and_projects_below_64MiB(self):
        self.request['origin'] = records(self.life, state_bytes=17*1024*1024)
        with patch.object(journal_bundle, 'MAX_BYTES', 33554432), patch.object(journal_transport, 'MAX_BYTES', 33554432):
            with self.assertRaisesRegex(ValueError, 'bounded_total_journal_mirror'):
                journal_transport.export_chunks(self.life, self.request['origin'], 'synthetic-journal')
        receipt = self.collect()
        self.assertGreater(receipt['locally_validated_original_bytes'], 67108864)
        self.assertLess(len(subject.canonical(receipt)), 20000)
        self.assertEqual(subject.MAX_TRANSFER_BYTES, journal_transport.MAX_TOTAL_BYTES)
        subject.validate_receipt(receipt, self.binding)

    def test_transferred_projection_still_rejects_over_64MiB(self):
        with self.assertRaisesRegex(ValueError, 'unchanged_64MiB_transfer_bound'):
            subject.bounded(b'x'*(67108864+1))

    def test_changed_original_hash_missing_record_or_wrong_stage_rejected(self):
        path = self.life/'stream/records/00000000000000000004.json'
        original = path.read_bytes()
        changed = json.loads(original)
        changed['document']['state'] = 'tampered'
        path.write_bytes(subject.canonical(changed))
        with self.assertRaisesRegex(ValueError, 'complete_original_record_hash'):
            self.collect()
        path.unlink()
        with self.assertRaises(OSError):
            self.collect()
        path.write_bytes(original)
        stage_path = self.life/'stream/records/00000000000000000007.json'
        stage = json.loads(stage_path.read_bytes())
        stage['document']['stage'] = 'THINK'
        stage['sha256'] = subject.digest({key:value for key,value in stage.items() if key != 'sha256'})
        stage_path.write_bytes(subject.canonical(stage))
        with self.assertRaisesRegex(ValueError, 'committed_source_stage'):
            self.collect()

    def test_foreign_journal_reused_pid_anchor_or_validator_rejected(self):
        variants = []
        foreign = deepcopy(self.binding); foreign['registry']['journal']['journal_id'] = 'foreign'; variants.append(foreign)
        reused = deepcopy(self.binding); reused['native_identity']['start_ticks'] = '0'; variants.append(reused)
        stale = deepcopy(self.binding); stale['anchors'][0]['sha256'] = '0'*64; variants.append(stale)
        validator = deepcopy(self.binding); validator['validator_sha256'] = '0'*64; variants.append(validator)
        for binding in variants:
            with self.subTest(binding=subject.digest(binding)):
                with self.assertRaises(ValueError):
                    subject.collect(binding, self.request)

    def test_old_origin_and_extended_or_expired_deadline_rejected(self):
        origin = deepcopy(self.request); origin['origin']['record_index'] = 4
        with self.assertRaisesRegex(ValueError, 'future_native_origin'):
            subject.collect(self.binding, origin)
        for change in (dict(deadline_unix=self.binding['deadline_unix']+1),
                       dict(deadline_unix=1, prior_deadline_unix=1)):
            with self.assertRaisesRegex(ValueError, 'unchanged_live_deadline'):
                subject.collect(dict(self.binding, **change), self.request)

    def test_raw_text_hashes_and_uninstalled_receipt_are_not_authority(self):
        hub, session = self.make_hub()
        receipt = self.collect()
        wire = envelope(self.binding, self.request, subject.digest(receipt))
        with self.assertRaises(OSError):
            hub.native(wire)
        with self.assertRaisesRegex(ValueError, 'custody_reference_only'):
            hub.native(dict(wire, raw_act=receipt['raw_act'], records=receipt['records']))
        self.assertFalse(session.seen)
        self.assertFalse(list(self.store_root.glob('claim-*')))

    def test_owner_file_tamper_or_permissions_fail_before_dispatch(self):
        hub, session = self.make_hub()
        wire, receipt = self.staged()
        path = self.store_root/('receipt-'+wire['attestation_sha256']+'.json')
        original = path.read_bytes()
        receipt['raw_act'] = 'Forged raw text.'
        path.write_bytes(subject.canonical(receipt))
        with self.assertRaisesRegex(ValueError, 'receipt_bytes_unchanged'):
            hub.native(wire)
        path.write_bytes(original)
        path.chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'strict_owner_file'):
            hub.native(wire)
        self.assertFalse(session.seen)

    def test_symlink_hardlink_nonowner_and_open_directory_rejected(self):
        wire, unused = self.staged()
        path = self.store_root/('receipt-'+wire['attestation_sha256']+'.json')
        other = self.root/'outside'
        os.link(path, other)
        with self.assertRaisesRegex(ValueError, 'single_link'):
            self.store.receipt(wire['attestation_sha256'])
        other.unlink()
        raw = path.read_bytes(); path.unlink(); other.write_bytes(raw); path.symlink_to(other)
        with self.assertRaises(OSError):
            self.store.receipt(wire['attestation_sha256'])
        with self.assertRaisesRegex(ValueError, 'strict_owner_directory'):
            OwnerStore(self.store_root, os.getuid()+1)
        self.store_root.chmod(0o755)
        with self.assertRaisesRegex(ValueError, 'strict_owner_directory'):
            OwnerStore(self.store_root, os.getuid())

    def test_request_metrics_source_session_and_epoch_mismatch_rejected(self):
        hub, session = self.make_hub()
        wire, receipt = self.staged()
        variants = []
        metrics = deepcopy(wire); metrics['request']['metrics']['ACT'] += 1; variants.append(metrics)
        epoch = deepcopy(wire); epoch['transport_epoch'] = '9'*64; variants.append(epoch)
        foreign = deepcopy(wire); foreign['session_id'] = 'foreign'; variants.append(foreign)
        for incoming in variants:
            with self.assertRaises(ValueError):
                hub.native(incoming)
        changed = deepcopy(receipt); changed['native_identity']['start_ticks'] = '0'
        token = self.store.install(changed)
        with self.assertRaisesRegex(ValueError, 'same_owner_bound'):
            hub.native(envelope(self.binding, self.request, token))
        session.epoch_ledger.epoch_sha256 = '9'*64
        with self.assertRaisesRegex(ValueError, 'unchanged_original_judge_epoch'):
            hub.native(wire)
        self.assertFalse(session.seen)

    def test_original_seen_and_durable_ambiguous_claim_prevent_replay(self):
        hub, session = self.make_hub()
        wire, unused = self.staged()
        identifier = self.request['origin']['record_sha256']
        session.seen.add(identifier)
        with self.assertRaisesRegex(ValueError, 'duplicate_ACT'):
            hub.native(wire)
        session.seen.clear()
        with patch.object(session, 'process_verified', side_effect=RuntimeError('synthetic_unknown_after_dispatch')):
            with self.assertRaisesRegex(RuntimeError, 'synthetic_unknown'):
                hub.native(wire)
        replacement = ProjectedHub(hub.original, self.store, {'synthetic_fork':self.binding})
        with patch.object(session, 'process_verified') as callback:
            with self.assertRaisesRegex(ValueError, 'no_automatic_replay'):
                replacement.native(wire)
            callback.assert_not_called()
        self.assertEqual(len(list(self.store_root.glob('claim-*'))), 1)
        self.assertFalse(list(self.store_root.glob('complete-*')))

    def test_expired_prepared_receipt_is_not_a_queued_historical_resubmit(self):
        hub, session = self.make_hub()
        wire, receipt = self.staged()
        with patch.object(subject.time, 'time', return_value=receipt['dispatch_not_after_unix']+1):
            with self.assertRaisesRegex(ValueError, 'expired_prepared_receipt'):
                hub.native(wire)
        self.assertFalse(session.seen)
        self.assertFalse(list(self.store_root.glob('claim-*')))

    def test_native_changes_during_validation_fail_closed(self):
        actual = subject.identity
        calls = []
        def changing(pid):
            calls.append(pid)
            value = actual(pid)
            if len(calls) > 1:
                value['start_ticks'] = 'reused'
            return value
        with patch.object(subject, 'identity', side_effect=changing):
            with self.assertRaisesRegex(ValueError, 'exact_live_native_incarnation'):
                self.collect()

    def test_context_rehash_does_not_hide_broken_original_ancestry(self):
        path = self.life/'stream/records/00000000000000000004.json'
        record = json.loads(path.read_bytes())
        record['document']['state'] = 'changed-and-rehashed'
        record['sha256'] = subject.digest({key:value for key,value in record.items() if key != 'sha256'})
        path.write_bytes(subject.canonical(record))
        with self.assertRaisesRegex(ValueError, 'same_life_contiguous_THINK_ancestry'):
            self.collect()

    def test_duplicate_json_and_record_byte_limit_are_enforced(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_JSON_key'):
            subject.decode(b'{"origin":1,"origin":2}')
        self.store.put('bounded.json', b'x'*101)
        with self.assertRaisesRegex(ValueError, 'bounded_single_link'):
            subject.read_at(self.store.directory, 'bounded.json', 100)

    def test_accepted_source_persists_original_seen_and_complete_receipt(self):
        hub, session = self.make_hub()
        wire, unused = self.staged()
        reply = hub.native(wire)
        self.assertEqual(reply['source_transport']['transport_epoch'], self.binding['transport_epoch'])
        self.assertEqual(len(session.seen), 1)
        self.assertEqual(len(list(self.store_root.glob('complete-*'))), 1)
        with self.assertRaisesRegex(ValueError, 'duplicate_ACT'):
            hub.native(wire)

    def test_two_projected_callers_cannot_double_dispatch(self):
        hub, session = self.make_hub()
        wire, unused = self.staged()
        results, errors = [], []
        def request():
            try:
                results.append(hub.native(wire))
            except ValueError as error:
                errors.append(str(error))
        workers = [threading.Thread(target=request) for ordinal in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(3)
        self.assertTrue(all(not worker.is_alive() for worker in workers))
        self.assertEqual(len(results), 1)
        self.assertEqual(errors, ['duplicate_ACT_no_automatic_resubmit'])
        self.assertEqual(len(session.game.received), 1)

    def test_native_record_symlink_is_not_source_authority(self):
        path = self.life/'stream/records/00000000000000000004.json'
        moved = self.root/'moved-record.json'
        path.rename(moved); path.symlink_to(moved)
        with self.assertRaises(OSError):
            self.collect()

    def test_install_is_idempotent_but_cannot_rewrite_a_receipt(self):
        receipt = self.collect()
        token = self.store.install(receipt)
        self.assertEqual(self.store.install(receipt), token)
        with self.assertRaisesRegex(ValueError, 'existing_custody'):
            self.store.put('receipt-'+token+'.json', b'changed', reuse=True)

    def test_receiver_serializes_legacy_projected_and_base_calls(self):
        hub, unused = self.make_hub()
        wire, unused = self.staged()
        started = threading.Event()
        released = threading.Event()
        calls = []
        def legacy(request):
            calls.append('legacy-start'); started.set(); released.wait(3); calls.append('legacy-end')
        hub.original.native.side_effect = legacy
        worker = threading.Thread(target=hub.native, args=(dict(session_id='synthetic_fork', request={}, records=[]),))
        worker.start(); self.assertTrue(started.wait(1))
        second = threading.Thread(target=lambda: (hub.generation({}), calls.append('base')))
        second.start(); time.sleep(.03); self.assertNotIn('base', calls)
        released.set(); worker.join(2); second.join(2)
        self.assertEqual(calls, ['legacy-start', 'legacy-end', 'base'])

    def test_cli_collect_install_and_original_serialized_socket_end_to_end(self):
        binding_path = self.store_root/'binding.json'
        binding_raw = subject.canonical(self.binding)
        self.store.put(binding_path.name, binding_raw)
        command = [sys.executable, '-B', '-m', MODULE, 'collect', '--binding', str(binding_path),
            '--binding-sha256', subject.byte_digest(binding_raw)]
        collected = subprocess.run(command, input=subject.canonical(self.request), capture_output=True, check=True).stdout
        installed = subprocess.run([*command[:4], 'install', *command[5:], '--store', str(self.store_root)],
            input=collected, capture_output=True, check=True).stdout
        token = json.loads(installed)['attestation_sha256']
        self.assertEqual(load_binding(binding_path, os.getuid(), subject.byte_digest(binding_raw)), self.binding)
        hub, unused = self.make_hub()
        errors = []
        def server():
            try:
                serve(hub, time.time()+1)
            except Exception as error:
                errors.append(error)
        worker = threading.Thread(target=server)
        worker.start()
        try:
            deadline = time.time()+2
            while not (hub.root/'native.sock').exists() and time.time() < deadline:
                time.sleep(.005)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(3)
                client.connect(str(hub.root/'native.sock'))
                client.sendall(subject.canonical(envelope(self.binding, self.request, token))+b'\n')
                with client.makefile('rb') as stream:
                    reply = json.loads(stream.readline(262145))
            self.assertIn('receipt_sha256', reply)
            self.assertEqual(reply['report']['caption_sources'][0]['stage'], 'THINK')
        finally:
            worker.join(4)
        self.assertFalse(worker.is_alive())
        self.assertFalse(errors)

    def test_relay_requires_matching_authenticated_collector_and_installer(self):
        receipt = self.collect()
        config = dict(source='/synthetic/pinned', binding_path='/synthetic/private/binding.json',
            binding_sha256='a'*64, store='/synthetic/private/custody')
        installed = dict(attestation_sha256=subject.digest(receipt), binding_sha256=subject.digest(self.binding))
        with patch.object(relay, 'exchange', side_effect=[subject.canonical(receipt), subject.canonical(installed)]) as exchange:
            wire = relay.prepare(self.binding, self.request, config, config)
            self.assertEqual(wire['attestation_sha256'], subject.digest(receipt))
            self.assertEqual(exchange.call_args_list[0].args[0], 'gpu/ovx2_ssh.sh')
            self.assertEqual(exchange.call_args_list[1].args[0], 'gpu/ovx4_ssh.sh')
        installed['attestation_sha256'] = '0'*64
        with patch.object(relay, 'exchange', side_effect=[subject.canonical(receipt), subject.canonical(installed)]):
            with self.assertRaisesRegex(ValueError, 'exact_operator_installed_receipt'):
                relay.prepare(self.binding, self.request, config, config)

    def test_continuation_preserves_full_state_queues_ledgers_deadlines_and_weights(self):
        unused, session = self.make_hub()
        snapshot = session.snapshot()
        previous = dict(admission_closed=True, inflight=0, sessions={'synthetic_fork':snapshot},
            deadline_unix=self.binding['deadline_unix'], judge_epoch_sha256=self.binding['judge_epoch_sha256'],
            epoch_binding_sha256='a'*64, weights={'adapter':'b'*64}, reference_panels='c'*64,
            judge_configuration='d'*64, ledger_files={'BINDING.json':'e'*64}, custody_files={'claim':'f'*64},
            queued_requests=[dict(id='synthetic', disposition='UNKNOWN_NO_REPLAY')], transport_epoch='1'*64,
            source_manifest_sha256='2'*64)
        candidate = deepcopy(previous); candidate.update(transport_epoch='3'*64, source_manifest_sha256='4'*64)
        self.assertFalse(gate(previous, candidate)['replay_authorized'])
        for field, value in [('deadline_unix', previous['deadline_unix']+1), ('weights', {}),
                             ('ledger_files', {}), ('custody_files', {}), ('queued_requests', [])]:
            changed = deepcopy(candidate); changed[field] = value
            with self.assertRaisesRegex(ValueError, 'unchanged_'):
                gate(previous, changed)
        pending = deepcopy(previous); pending['inflight'] = 1
        with self.assertRaisesRegex(ValueError, 'explicit_drain'):
            gate(pending, candidate)
        pending = deepcopy(candidate); pending['sessions']['synthetic_fork']['phase'] = 'PENDING'
        with self.assertRaisesRegex(ValueError, 'complete_saved_session_only'):
            gate(previous, pending)
        changed = deepcopy(candidate); changed['sessions']['synthetic_fork']['seen'] = ['a'*64]
        with self.assertRaisesRegex(ValueError, 'unique_seen'):
            gate(previous, changed)

    def test_existing_epoch_reattaches_without_new_binding_or_shadow_clock(self):
        unused, session = self.make_hub()
        root = session.epoch_ledger.root
        expected = {path.name:subject.byte_digest(path.read_bytes()) for path in root.iterdir()}
        reattach_existing_epoch(session, root, expected, self.binding['judge_epoch_sha256'])
        self.assertEqual({path.name:subject.byte_digest(path.read_bytes()) for path in root.iterdir()}, expected)
        with self.assertRaisesRegex(ValueError, 'original_epoch_binding'):
            reattach_existing_epoch(session, root, expected, '0'*64)


if __name__ == '__main__':
    unittest.main()
