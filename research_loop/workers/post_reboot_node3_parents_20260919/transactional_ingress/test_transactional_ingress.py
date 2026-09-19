"""CPU-only temp journals and Unix sockets; no live routes or models."""

from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from research_loop.workers.post_reboot_node3_parents_20260919.transactional_ingress import candidate, legacy, relay
from research_loop.workers.post_reboot_node3_parents_20260919.transactional_ingress.ledger import Ledger, origin_key
from research_loop.workers.post_reboot_node3_parents_20260919.projected_wire import contract
from research_loop.workers.post_reboot_node3_parents_20260919.projected_wire import test_projected_wire as fixtures
from research_loop.workers.rohin221_continuous_caption_20260918.shared_scorer import serve
from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import restore_contract


def request(number=1):
    return dict(origin=dict(kind='TRAIN_CHILD_RESPONSE', record_index=number, record_sha256=f'{number:064x}'),
        metrics=dict(THINK=10, ACT=2, LEARN=0))


def response(value):
    return dict(origin=value['origin'], report=dict(ok=True, feedback=[]), receipt_sha256='b' * 64)


class RelayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / 'ledger'
        self.directory.mkdir(mode=0o700)
        self.deadline = time.time() + 300
        self.ledger = Ledger(self.directory, os.getuid(), 'a' * 64, self.deadline)
        self.addCleanup(lambda: self.ledger.release())
        self.preparer = Mock(side_effect=lambda binding, value, node, scorer:
            dict(session_id='session', request=value, transport_epoch='a' * 64))
        self.forwarder = Mock(side_effect=lambda path, payload, deadline, ledger, connection: response(payload['request']))
        self.core = relay.Relay(self.ledger, {'session': dict(binding={}, node={}, scorer={})},
            self.root / 'upstream.sock', self.preparer, self.forwarder)

    def opened(self):
        self.ledger.open_admission(self.ledger.fence_sequence, 'b' * 64)

    def accepted(self):
        return self.ledger.accepted('session', 100)

    def restart(self):
        self.ledger.release()
        self.ledger = Ledger(self.directory, os.getuid(), 'a' * 64, self.deadline)
        self.core.ledger = self.ledger

    def test_initial_closed_fence_returns_explicit_no_judgment(self):
        result = self.core.handle(self.accepted(), 'session', request())
        self.assertTrue(result['report']['no_judgment'])
        self.assertEqual(result['report']['feedback'], [])
        self.preparer.assert_not_called()
        self.forwarder.assert_not_called()

    def test_dispatch_intent_is_fsynced_before_forward_and_result_before_delivery(self):
        self.opened()
        connection = self.accepted()
        def inspect(path, payload, deadline, ledger, socket_id):
            item = ledger.item(origin_key('session', payload['request']))
            self.assertEqual(item['state'], 'DISPATCH_INTENT')
            raw = (self.directory / f'event-{ledger.sequence:020d}.json').read_bytes()
            self.assertEqual(json.loads(raw)['kind'], 'DISPATCH_INTENT')
            self.assertEqual(socket_id, connection)
            return response(payload['request'])
        self.core.forwarder = inspect
        actual = self.core.handle(connection, 'session', request())
        self.assertEqual(actual, response(request()))
        self.assertEqual(self.ledger.item(origin_key('session', request()))['state'], 'COMPLETE')
        self.assertEqual(self.ledger.status()['active_sockets'][connection]['delivery'], 'NOT_ATTEMPTED')

    def test_close_during_preparation_never_dispatches(self):
        self.opened()
        started, release = threading.Event(), threading.Event()
        def prepare(binding, value, node, scorer):
            started.set()
            release.wait(3)
            return dict(session_id='session', request=value, transport_epoch='a' * 64)
        self.core.preparer = prepare
        worker = threading.Thread(target=self.core.handle, args=(self.accepted(), 'session', request()))
        worker.start()
        self.assertTrue(started.wait(2))
        self.assertFalse(self.ledger.close_admission('OWNER')['drained'])
        release.set()
        worker.join(3)
        self.assertFalse(worker.is_alive())
        self.forwarder.assert_not_called()
        self.assertEqual(self.ledger.item(origin_key('session', request()))['state'], 'NO_DISPATCH')

    def test_close_after_dispatch_waits_for_callback_and_socket_lifetime(self):
        self.opened()
        started, release = threading.Event(), threading.Event()
        connection = self.accepted()
        def forward(path, payload, deadline, ledger, identifier):
            started.set()
            release.wait(3)
            return response(payload['request'])
        self.core.forwarder = forward
        worker = threading.Thread(target=self.core.handle, args=(connection, 'session', request()))
        worker.start()
        self.assertTrue(started.wait(2))
        status = self.ledger.close_admission('OWNER')
        self.assertIn('DISPATCH_INTENT', status['pending'].values())
        self.assertFalse(status['drained'])
        release.set()
        worker.join(3)
        self.assertFalse(self.ledger.status()['drained'])
        self.ledger.closed(connection, 'WRITE_FAILED_NOT_UPTAKE')
        self.assertTrue(self.ledger.status()['drained'])

    def test_ambiguous_timeout_is_unknown_across_restart_without_replay(self):
        self.opened()
        self.core.forwarder = Mock(side_effect=TimeoutError('synthetic'))
        result = self.core.handle(self.accepted(), 'session', request())
        self.assertEqual(result['report']['error'], 'ORIGIN_TRANSPORT_FAILED_AFTER_DISPATCH')
        self.restart()
        self.assertFalse(self.ledger.status()['drained'])
        result = self.core.handle(self.accepted(), 'session', request())
        self.assertTrue(result['report']['no_judgment'])
        self.core.forwarder.assert_called_once()

    def test_crash_between_intent_and_send_is_conservatively_unknown(self):
        self.opened()
        key, unused = self.ledger.admit(self.accepted(), request())
        self.ledger.prepared(key, {})
        self.assertTrue(self.ledger.dispatch(key))
        self.restart()
        self.assertEqual(self.ledger.item(key)['state'], 'UNKNOWN')
        self.assertFalse(self.ledger.status()['active_sockets'])
        self.assertFalse(self.ledger.status()['drained'])

    def test_crash_after_preparation_never_auto_dispatches(self):
        self.opened()
        key, unused = self.ledger.admit(self.accepted(), request())
        self.ledger.prepared(key, {})
        self.restart()
        self.assertEqual(self.ledger.item(key)['reason'], 'RESTART_NEVER_DISPATCHED')
        self.assertTrue(self.ledger.status()['drained'])
        self.forwarder.assert_not_called()

    def test_completed_duplicate_returns_retained_result_not_new_judgment(self):
        self.opened()
        first = self.core.handle(self.accepted(), 'session', request())
        self.restart()
        second = self.core.handle(self.accepted(), 'session', request())
        self.assertEqual(first, second)
        self.forwarder.assert_called_once()

    def test_duplicate_cannot_change_metrics(self):
        self.opened()
        self.core.handle(self.accepted(), 'session', request())
        altered = request()
        altered['metrics']['ACT'] += 1
        with self.assertRaisesRegex(ValueError, 'same_origin'):
            self.core.handle(self.accepted(), 'session', altered)
        self.forwarder.assert_called_once()

    def test_wrong_response_origin_becomes_unknown(self):
        self.opened()
        self.core.forwarder = Mock(return_value=response(request(2)))
        result = self.core.handle(self.accepted(), 'session', request())
        self.assertTrue(result['report']['no_judgment'])
        self.assertEqual(self.ledger.item(origin_key('session', request()))['state'], 'UNKNOWN')

    def test_deadline_not_extended_and_no_dispatch_after_expiry(self):
        self.opened()
        connection = self.accepted()
        with patch.object(time, 'time', return_value=self.deadline + 1):
            result = self.core.handle(connection, 'session', request())
        self.assertTrue(result['report']['no_judgment'])
        self.forwarder.assert_not_called()

    def test_singleton_and_journal_tamper_fail_closed(self):
        with self.assertRaises(BlockingIOError):
            Ledger(self.directory, os.getuid(), 'a' * 64, self.deadline)
        self.opened()
        target = self.directory / 'event-00000000000000000002.json'
        document = json.loads(target.read_bytes())
        document['payload']['reason'] = 'tampered'
        target.write_bytes(contract.canonical(document))
        with self.assertRaisesRegex(ValueError, 'complete_hash_chained'):
            Ledger(self.copy_journal(), os.getuid(), 'a' * 64, self.deadline)

    def copy_journal(self):
        import shutil
        target = self.root / 'copy'
        target.mkdir(mode=0o700)
        for path in self.directory.glob('event-*.json'):
            shutil.copyfile(path, target / path.name)
            os.chmod(target / path.name, 0o600)
        return target

    def test_open_compare_and_swap_rejects_stale_admin_command(self):
        fence = self.ledger.fence_sequence
        self.ledger.close_admission('NEW_FENCE')
        with self.assertRaisesRegex(ValueError, 'compare_and_open'):
            self.ledger.open_admission(fence, 'b' * 64)

    def test_failed_journal_write_never_dispatches_and_poison_blocks_open(self):
        self.opened()
        connection = self.accepted()
        with patch.object(self.ledger.store, 'put', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.core.handle(connection, 'session', request())
        self.assertFalse(self.ledger.status()['drained'])
        self.forwarder.assert_not_called()

    def test_journal_failure_after_dispatch_never_claims_not_dispatched(self):
        self.opened()
        key, unused = self.ledger.admit(self.accepted(), request())
        self.ledger.prepared(key, {})
        self.ledger.dispatch(key)
        with patch.object(self.ledger.store, 'put', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.ledger.complete(key, response(request()))
        result = self.core.failure_reply('session', request(), OSError('disk full'))
        self.assertEqual(result['report']['error'], 'ORIGIN_TRANSPORT_FAILED_AFTER_DISPATCH')
        self.assertFalse(result['report']['automatic_replay'])

    def test_imported_legacy_unknown_never_replayed(self):
        self.ledger.import_quarantine([dict(session='session', request=request(), disposition='UNKNOWN_NO_REPLAY')], 'c' * 64)
        self.opened()
        result = self.core.handle(self.accepted(), 'session', request())
        self.assertTrue(result['report']['no_judgment'])
        self.forwarder.assert_not_called()

    def test_unknown_can_only_be_settled_with_bound_owner_lifetime_evidence(self):
        self.opened()
        self.core.forwarder = Mock(side_effect=TimeoutError('synthetic'))
        connection = self.accepted()
        self.core.handle(connection, 'session', request())
        self.ledger.closed(connection, 'WRITE_RETURNED_NOT_TOOL_RECEIPT')
        self.ledger.close_admission('OWNER')
        resolution = dict(key=origin_key('session', request()), transport_epoch='a' * 64,
            request_sha256=contract.digest(request()), no_replay=True, upstream_callback_quiesced=False,
            owner_evidence_sha256='b' * 64, disposition='UNKNOWN_NO_REPLAY')
        with self.assertRaisesRegex(ValueError, 'owner_resolution'):
            self.ledger.resolve_unknown(resolution)
        resolution['upstream_callback_quiesced'] = True
        self.assertTrue(self.ledger.resolve_unknown(resolution)['drained'])
        self.opened()
        self.assertTrue(self.core.handle(self.accepted(), 'session', request())['report']['no_judgment'])
        self.core.forwarder.assert_called_once()

    def test_exact_completed_owner_response_can_resolve_lost_reply_without_rescoring(self):
        self.opened()
        self.core.forwarder = Mock(side_effect=TimeoutError('synthetic'))
        connection = self.accepted()
        self.core.handle(connection, 'session', request())
        self.ledger.closed(connection, 'WRITE_FAILED_NOT_UPTAKE')
        self.ledger.close_admission('OWNER')
        result = response(request())
        self.ledger.resolve_unknown(dict(key=origin_key('session', request()), transport_epoch='a' * 64,
            request_sha256=contract.digest(request()), no_replay=True, upstream_callback_quiesced=True,
            owner_evidence_sha256='b' * 64, disposition='COMPLETE', response=result, response_sha256=contract.digest(result)))
        self.assertEqual(self.core.handle(self.accepted(), 'session', request()), result)
        self.core.forwarder.assert_called_once()

    def test_partial_native_frame_is_in_socket_drain_inventory(self):
        self.opened()
        path = self.root / 'native.sock'
        server = relay.NativeServer(path, self.core, 'session')
        self.addCleanup(server.server_close)
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(client.close)
        client.connect(str(path))
        worker = threading.Thread(target=server.handle_request)
        worker.start()
        self.wait_until(lambda: bool(self.ledger.status()['active_sockets']))
        status = self.ledger.close_admission('OWNER')
        self.assertFalse(status['drained'])
        client.sendall(contract.canonical(request()) + b'\n')
        raw = client.recv(262144)
        self.assertTrue(json.loads(raw)['report']['no_judgment'])
        worker.join(2)
        self.wait_until(lambda: not self.ledger.status()['active_sockets'])
        self.assertTrue(self.ledger.status()['drained'])
        self.forwarder.assert_not_called()

    def test_native_byte_bound_is_unchanged(self):
        self.assertEqual(relay.LIMIT, 262144)
        self.assertEqual(relay.MAX_TRANSFER_BYTES, 64 * 1024 * 1024)

    def test_owner_admin_readiness_required_before_open(self):
        with self.assertRaises(FileNotFoundError):
            relay.administration(self.ledger, dict(operation='open', readiness_sha256='a' * 64,
                expected_fence=self.ledger.fence_sequence))

    def wait_until(self, predicate):
        stop = time.monotonic() + 3
        while not predicate() and time.monotonic() < stop:
            time.sleep(.01)
        self.assertTrue(predicate())


def drain_proof():
    now = time.time()
    identity = dict(pid=499900, start_ticks='10094999', boot_id='original')
    roles = {role: dict(identity) for role in legacy.REQUIRED_ROLES}
    observation = dict(unix=now - 1, complete_socket_namespace_inventory=True, observer_not_sandbox_ps=True,
        processes={role: dict(identity=value, raw_proc_capture_sha256='a' * 64, nonlistener_socket_fds=[],
            active_handler_threads=[], enumeration_complete=True) for role, value in roles.items()},
        queues={edge: dict(pending_connections=0, accepted_connections=0, pending_bytes=0,
            raw_kernel_or_channel_evidence_sha256='b' * 64, enumeration_complete=True)
            for edge in legacy.REQUIRED_EDGES}, unattributed_old_route_channels=[])
    return dict(schema='R233_OWNER_LEGACY_DRAIN_V1', unix=now, scorer_identity=identity,
        authority='OPERATOR_AUTHENTICATED_OWNER_CUSTODY', source_witness_sha256='c' * 64,
        fence=dict(unix=now - 2, edges={edge: 'CLOSED_TO_NEW_OLD_ROUTE_CONNECTIONS'
            for edge in legacy.REQUIRED_EDGES}, owner_evidence_sha256='d' * 64,
            creator_capabilities_revoked=True, supervisor_respawn_inhibited=True),
        observations=[deepcopy(observation), deepcopy(observation)], process_identities=roles,
        all_sessions_complete=True, unresolved_active_callbacks=[], state_closure_sha256='e' * 64,
        queue_dispositions_sha256='f' * 64)


class LegacyTests(unittest.TestCase):
    def test_offline_owner_certificate_not_claimed_as_kernel_observation(self):
        proof = drain_proof()
        result = legacy.verify_drain(proof, proof['scorer_identity'])
        self.assertIn('NOT_INDEPENDENT_KERNEL_OBSERVATION', result['status'])
        self.assertFalse(result['replay_authorized'])

    def test_alias_only_quiet_log_pid_or_stable_state_cannot_prove_drain(self):
        mutations = [lambda proof: proof['fence'].update(creator_capabilities_revoked=False),
            lambda proof: proof['observations'][0].update(observer_not_sandbox_ps=False),
            lambda proof: proof['observations'][0]['queues'].pop('scorer-base-listener'),
            lambda proof: proof['observations'][0]['processes']['scorer'].update(nonlistener_socket_fds=[123]),
            lambda proof: proof['observations'][0]['queues']['reverse-ssh-channels'].update(pending_connections=1),
            lambda proof: proof.update(unresolved_active_callbacks=['timed-out-client']),
            lambda proof: proof['observations'][0].update(unattributed_old_route_channels=['child-ssh']),
            lambda proof: proof.update(unix=time.time() - 1000)]
        for mutate in mutations:
            with self.subTest(mutation=repr(mutate)):
                proof = drain_proof()
                mutate(proof)
                with self.assertRaises((ValueError, KeyError)):
                    legacy.verify_drain(proof, proof['scorer_identity'])

    def test_real_captured_cut_still_has_unenumerated_admissions(self):
        cut = json.loads((Path(__file__).parents[1] / 'INTEGRATION_CUT_LATEST.json').read_bytes())
        result = legacy.reconcile(cut)
        self.assertTrue(result['unenumerated_legacy_admissions'])
        self.assertFalse(result['drain_proved'])
        self.assertEqual(sum(len(row['transport_log_sha256']) for row in result['dispositions']),
            len(cut['host']['completed_transport_logs']))

    def test_actual_original_synchronous_serve_keeps_callback_after_disconnect(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started, finish, completed = threading.Event(), threading.Event(), threading.Event()
            def callback(value):
                started.set()
                finish.wait(3)
                completed.set()
                return response(value['request'])
            hub = SimpleNamespace(root=root, sessions={}, native=callback, generation=Mock())
            worker = threading.Thread(target=serve, args=(hub, time.time() + .4))
            worker.start()
            try:
                stop = time.time() + 2
                while not (root / 'LISTENING.json').exists() and time.time() < stop:
                    time.sleep(.01)
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                    connection.connect(str(root / 'native.sock'))
                    connection.sendall(contract.canonical(dict(request=request())) + b'\n')
                    self.assertTrue(started.wait(2))
                time.sleep(.5)
                self.assertTrue(worker.is_alive())
                self.assertFalse(completed.is_set())
            finally:
                finish.set()
                worker.join(3)
            self.assertTrue(completed.is_set())
            self.assertFalse(worker.is_alive())


class CandidateTests(unittest.TestCase):
    def test_preflight_rejection_happens_before_model_or_original_import(self):
        with patch.object(candidate, 'preflight', side_effect=ValueError('unproved_drain')), \
                patch.object(candidate.importlib, 'import_module') as loader:
            with self.assertRaisesRegex(ValueError, 'unproved_drain'):
                candidate.run({})
            loader.assert_not_called()

    def test_candidate_driver_loads_once_reuses_panels_and_calls_original_serial_serve(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('runtime', 'custody', 'node3-caption-continuation-owner'):
                (root / name).mkdir(mode=0o700)
            config = dict(root=str(root / 'original'), checkpoint_root='checkpoint', checkpoint_complete_sha256='a',
                checkpoint_adapter_sha256='b', checkpoint_config_sha256='c', old_scalar={'path': 'old'},
                game_manifest='manifest', encoder_manifest='encoder', pixel_config='pixels',
                reference_panels='references', deadline_unix=1234)
            plan = dict(old_identity={'pid': 1}, candidate_runtime=str(root / 'runtime'),
                owner_custody=str(root / 'custody'), primary_scalar={'path': 'primary'}, primary_panels={'path': 'panels'},
                weight_proofs={'same': True}, bindings={}, transport_epoch='c' * 64,
                original_loaded={}, queue_dispositions={'sha256': 'd' * 64},
                sole_writer_release={'path': 'release'}, candidate_source_manifest={'sha256': 'e' * 64})
            rows = [dict(selected=[dict(scene=str(number))] * 64, scores=[number] * 64) for number in range(3)]
            release = dict(old_identity=plan['old_identity'], supervisor_hold=True, drain_sha256='f' * 64,
                candidate_source_sha256='e' * 64, exclusive_gpu=4, old_writer_retired=True,
                same_device_and_child_confinement_proved=True)
            dual = SimpleNamespace(weight_proofs=plan['weight_proofs'], score=Mock())
            original = SimpleNamespace(validate=Mock(), verified_source=Mock(return_value={}),
                DualScalar=Mock(return_value=dual), DevelopmentManifest=SimpleNamespace(
                    from_mapping=Mock(return_value=SimpleNamespace(contests=[1, 2, 3]))),
                FrozenCPUEncoder=Mock(), PixelConfig=Mock(),
                data=SimpleNamespace(bound=lambda key: {'manifest': {}, 'pixels': {}, 'references': rows}[key]),
                Hub=lambda sockets, *args: SimpleNamespace(root=sockets, sessions={}, registry={}), serve=Mock())
            with patch.object(candidate, 'preflight', return_value=(config, {}, {'dispositions': []}, {'drain_sha256': 'f' * 64})), \
                    patch.object(candidate, 'require_retired'), patch.object(candidate, 'require_runtime'), \
                    patch.object(candidate, 'verify_source'), \
                    patch.object(candidate, 'verify_state'), patch.object(candidate, 'restore_sessions', return_value=[]), \
                    patch.object(candidate.importlib, 'import_module', return_value=original), \
                    patch.object(candidate, 'reference', side_effect=lambda value:
                        release if value['path'] == 'release' else {str(number): [number] * 64 for number in range(3)}):
                candidate.run(plan)
            original.DualScalar.assert_called_once_with('old', 'primary')
            dual.score.assert_not_called()
            original.serve.assert_called_once()
            self.assertIsInstance(original.serve.call_args.args[0], candidate.QuarantinedHub)
            self.assertEqual(original.serve.call_args.args[1], 1234)
            self.assertTrue((root / 'runtime' / 'LOADED.json').is_file())
            self.assertFalse((root / 'original').exists())

    def test_relay_projection_original_sole_server_end_to_end(self):
        fixture = fixtures.ProjectedWireTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        hub, session = fixture.make_hub()
        wire, receipt = fixture.staged()
        directory = fixture.root / 'relay-ledger'
        directory.mkdir(mode=0o700)
        ledger = Ledger(directory, os.getuid(), fixture.binding['transport_epoch'], fixture.binding['deadline_unix'])
        self.addCleanup(ledger.release)
        ledger.open_admission(ledger.fence_sequence, 'a' * 64)
        scorer = threading.Thread(target=serve, args=(hub, time.time() + .4))
        scorer.start()
        core = relay.Relay(ledger, {'synthetic_fork': dict(binding=fixture.binding, node={}, scorer={})},
            hub.root / 'native.sock', preparer=lambda *args: wire)
        native = relay.NativeServer(fixture.root / 'relay.sock', core, 'synthetic_fork')
        try:
            stop = time.monotonic() + 2
            while not (hub.root / 'LISTENING.json').exists() and time.monotonic() < stop:
                time.sleep(.01)
            thread = threading.Thread(target=native.handle_request)
            thread.start()
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(3)
                client.connect(str(fixture.root / 'relay.sock'))
                client.sendall(contract.canonical(fixture.request) + b'\n')
                with client.makefile('rb') as stream:
                    result = json.loads(stream.readline(262145))
            thread.join(3)
        finally:
            native.server_close()
            scorer.join(3)
        self.assertFalse(scorer.is_alive())
        self.assertEqual(result['origin'], fixture.request['origin'])
        self.assertEqual(result['source_transport']['attestation_sha256'], wire['attestation_sha256'])
        self.assertEqual(session.seen, {fixture.request['origin']['record_sha256']})
        self.assertTrue(ledger.close_admission('OWNER')['drained'])
        events = [json.loads(path.read_bytes())['kind'] for path in sorted(directory.glob('event-*.json'))]
        self.assertLess(events.index('DISPATCH_INTENT'), events.index('UPSTREAM_OPEN'))
        self.assertLess(events.index('UPSTREAM_CLOSED'), events.index('COMPLETE'))
        self.assertLess(events.index('COMPLETE'), events.index('SOCKET_CLOSED'))

    def test_receiver_quarantines_all_legacy_pending_dispositions(self):
        projected = SimpleNamespace(root='root', sessions={}, registry={}, native=Mock(), generation=Mock())
        hub = candidate.QuarantinedHub(projected, dict(dispositions=[dict(session='session', request=request(),
            disposition='UNKNOWN_NO_REPLAY')]))
        with self.assertRaisesRegex(ValueError, 'legacy_origin_quarantined'):
            hub.native(dict(session_id='session', request=request()))
        projected.native.assert_not_called()
        hub.native(dict(session_id='session', request=request(2)))
        projected.native.assert_called_once()

    def test_live_original_incarnation_blocks_second_loader(self):
        identity = contract.identity(os.getpid())
        identity['pid_namespace'] = os.readlink('/proc/self/ns/pid')
        with self.assertRaisesRegex(ValueError, 'still_present'):
            candidate.require_retired(identity)

    def test_other_pid_namespace_cannot_prove_original_absence(self):
        identity = contract.identity(os.getpid())
        identity['pid_namespace'] = 'pid:[NOT-THE-HOST]'
        with self.assertRaisesRegex(ValueError, 'real_host_pid_namespace'):
            candidate.require_retired(identity)

    def test_preserved_tree_rejects_missing_added_or_changed_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'state.json'
            path.write_bytes(b'original')
            tree = dict(root=str(root), files={'state.json': contract.byte_digest(b'original')})
            candidate.verify_tree(tree)
            (root / 'unaccounted.json').write_bytes(b'extra')
            with self.assertRaisesRegex(ValueError, 'complete_preserved_tree'):
                candidate.verify_tree(tree)

    def test_restore_uses_same_existing_epoch_and_exact_session(self):
        fixture = fixtures.ProjectedWireTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        old = fixture.make_session('original', fixture.binding['mirror_root'])
        state = old.snapshot()
        state['game'].update(agent_id='synthetic', lane='synthetic')
        epoch_root = fixture.root / 'deployment' / 'epochs' / 'synthetic_fork'
        epoch_root.parent.mkdir(parents=True)
        old.epoch_ledger.root.rename(epoch_root)
        epoch_files = {path.name: contract.byte_digest(path.read_bytes()) for path in epoch_root.iterdir()}
        snapshot = deepcopy(state)
        new_session = SimpleNamespace(snapshot=lambda: deepcopy(snapshot), seen=set(state['seen']))
        original = SimpleNamespace(build_game=Mock(return_value=SimpleNamespace(_judge=SimpleNamespace(relevance='same'))),
            EpochJudge=Mock(), NativeEpoch=Mock(return_value=new_session), restore_contract=restore_contract)
        hub = SimpleNamespace(sessions={}, registry={})
        config = dict(root=str(fixture.root / 'deployment'), outputs={'synthetic_fork': str(old.output)},
            relevance_threshold=.1)
        plan = dict(epochs={'synthetic_fork': dict(files=epoch_files, epoch_sha256=contract.digest(fixture.epoch_binding))})
        evidence = candidate.restore_sessions(original, config, plan, {'synthetic_fork': state}, 'dual', 'manifest',
            'primary', 'old', 'pixels', 'encoder', hub)
        self.assertEqual(epoch_files, {path.name: contract.byte_digest(path.read_bytes()) for path in epoch_root.iterdir()})
        self.assertEqual(hub.registry['synthetic_fork'], state['session_binding'])
        self.assertIs(hub.sessions['synthetic_fork'], new_session)
        self.assertEqual(evidence[0]['epoch_sha256'], old.epoch_ledger.epoch_sha256)
        self.assertEqual(original.build_game.call_args.kwargs['top_k'], 50)
        self.assertEqual(original.NativeEpoch.call_args.kwargs['resume_state'], state)

    def test_all_five_aliases_and_parented_policy_are_required(self):
        fixture = fixtures.ProjectedWireTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        routes = []
        for slot, identifier in relay.SESSIONS.items():
            binding = deepcopy(fixture.binding)
            binding['session_id'] = identifier
            binding['registry']['session_id'] = identifier
            routes.append(dict(slot=slot, binding=binding, stable_alias=f'/tmp/r226-caption-{slot}.sock',
                parent_policy='R233_PARENTED'))
        config = dict(routes=routes, deadline_unix=fixture.binding['deadline_unix'],
            original_transport_deadline_unix=fixture.binding['deadline_unix'], transport_epoch=fixture.binding['transport_epoch'])
        self.assertEqual(set(relay.validate_routes(config)), set(relay.SESSIONS.values()))
        routes[-1]['parent_policy'] = 'UNPARENTED'
        with self.assertRaisesRegex(ValueError, 'all_five_parented'):
            relay.validate_routes(config)
        routes.pop()
        with self.assertRaisesRegex(ValueError, 'all_five_exact_alias'):
            relay.validate_routes(config)


if __name__ == '__main__':
    unittest.main()
