import base64
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from parent_dependency_bridge import ParentDependencyBridge, canonical, owner_exchange, sha
from pair_operations import PairLinuxOperations
from receiver import PairReceiver
from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import ObservationRace, Refusal
from research_loop.workers.post_recovery_retention_boundary_20260918.operations import LinuxOperations

WORKER = Path(__file__).parent
sys.path.insert(0, str(WORKER.parent / 'post_recovery_retention_boundary_20260918'))
from test_boundary import inputs, selected
from test_coordinator import FakeOperations
from research_loop.workers.post_recovery_retention_boundary_20260918.coordinator import coordinate


class DependencyBridgeTests(unittest.TestCase):
    def setUp(self):
        self.binding = {'synthetic': 'same-life'}
        self.pins = {'/cpu/retention_sidecar.py': 'a' * 64}
        self.path = '/cpu/transaction/PARENT_DEPENDENCIES.json'
        self.dependency = dict(life_binding_sha256=sha(canonical(self.binding)), source_epoch='epoch2',
            old_parent={'pid': 99, 'boot_id': 'same-boot', 'start_ticks': '123'},
            ledger_pins={'/cpu/original/STATE.json': 'b' * 64})
        self.raw = canonical(self.dependency)
        self.bridge = ParentDependencyBridge(['reviewed-authenticated-CPU-owner-transport'],
            dependency_path=self.path, dependency_sha256=sha(self.raw), owner_source_pins=self.pins)

    def response(self, request):
        return dict(schema='PAIR_PARENT_OWNER_CHECK_RESPONSE_V1', nonce=request['nonce'],
            dependency_path=self.path, dependency_sha256=sha(self.raw),
            dependency_base64=base64.b64encode(self.raw).decode(), owner_source_pins=self.pins,
            verification_location='ORIGINAL_CPU_OWNER_FILESYSTEM_AND_PROC', native_signals=0,
            original_ledger_pins=self.dependency['ledger_pins'],
            recheck=dict(schema='PAIR_PARENT_FENCE_RECHECK_V1', dependency_path=self.path,
                dependency_sha256=sha(self.raw), life_binding_sha256=self.dependency['life_binding_sha256'],
                source_epoch='epoch2', old_parent=self.dependency['old_parent'], delivery_fenced=True,
                inflight_deliveries=0, ledger_pins_verified=True, native_signals=0, observed_unix=time.time()))

    def check(self, mutate=None):
        def transport(command, **kwargs):
            response = self.response(json.loads(kwargs['input']))
            if mutate:
                mutate(response)
            return subprocess.CompletedProcess(command, 0, canonical(response), b'')
        with patch('parent_dependency_bridge.subprocess.run', side_effect=transport) as run:
            result = self.bridge.check(self.binding, 'epoch2')
            self.assertNotIn('shell', run.call_args.kwargs)
            return result

    def test_cross_host_check_uses_original_bytes_without_opening_mirror_paths(self):
        with patch('pathlib.Path.read_bytes', side_effect=AssertionError('no_node_local_parent_mirror')):
            result = self.check()
        self.assertEqual(result, dict(path=self.path, sha256=sha(self.raw), receipt=self.dependency))

    def test_nonce_replay_and_wrong_owner_source_are_rejected(self):
        for mutation in (lambda response: response.update(nonce='old'),
                lambda response: response.update(owner_source_pins={})):
            with self.assertRaisesRegex(ValueError, 'fresh_bound_original_owner_response'):
                self.check(mutation)

    def test_copied_or_modified_dependency_bytes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'original_dependency_bytes_not_a_mirror'):
            self.check(lambda response: response.update(dependency_base64=base64.b64encode(b'{}').decode()))

    def test_stale_fence_wrong_native_and_changed_inventory_are_rejected(self):
        mutations = [lambda response: response['recheck'].update(observed_unix=time.time() - 60),
            lambda response: response['recheck'].update(old_parent={'pid': 100}),
            lambda response: response['recheck'].update(ledger_pins_verified=False),
            lambda response: response.update(original_ledger_pins={})]
        for mutation in mutations:
            with self.assertRaisesRegex(ValueError, 'effective_exact_parent_fence'):
                self.check(mutation)

    def test_failed_or_slow_owner_check_has_no_fallback(self):
        for error in (subprocess.TimeoutExpired(['owner'], 2),
                subprocess.CalledProcessError(1, ['owner'])):
            with patch('parent_dependency_bridge.subprocess.run', side_effect=error), \
                    self.assertRaisesRegex(ValueError, 'owner_fence_recheck_failed'):
                self.bridge.check(self.binding, 'epoch2')

    def test_owner_endpoint_calls_only_Kuhn_read_only_fence_verifier(self):
        owner = Mock()
        owner.file_bytes.return_value = self.raw
        owner.read.return_value = {'source_pins': self.pins}
        request = dict(schema='PAIR_PARENT_OWNER_CHECK_REQUEST_V1', nonce='fresh',
            dependency_path=self.path, dependency_sha256=sha(self.raw),
            life_binding_sha256=self.dependency['life_binding_sha256'], source_epoch='epoch2',
            owner_source_pins=self.pins)
        result = owner_exchange(request, self.path, sha(self.raw), owner)
        owner.verify_fence.assert_called_once_with(self.path, sha(self.raw), owner.LinuxCPU.return_value)
        owner.fence.assert_not_called()
        owner.rebind.assert_not_called()
        owner.serve.assert_not_called()
        self.assertEqual(result['original_ledger_pins'], self.dependency['ledger_pins'])


class PairObservationTests(unittest.TestCase):
    def setUp(self):
        self.binding, self.prepared, self.authority = inputs()
        self.candidate = selected(self.binding)
        self.temporary = tempfile.TemporaryDirectory(dir=WORKER)
        self.addCleanup(self.temporary.cleanup)
        self.hooks = Mock()
        self.proof = dict(complete_sha256=self.candidate['complete_sha256'])
        self.receiver = dict(candidate=self.candidate)
        self.hooks.verify_checkpoint.return_value = self.proof
        self.hooks.prepare_receiver.return_value = self.receiver
        self.operations = PairLinuxOperations(self.binding, self.hooks, prepared=self.prepared,
            approved_execution_sha256='not-an-activation', control_root=self.temporary.name)

    def test_expensive_work_is_cached_before_reservation(self):
        with patch.object(LinuxOperations, 'observe', return_value=self.candidate):
            candidate = self.operations.observe(self.binding)
        self.assertEqual(self.operations.verify_checkpoint(candidate), self.proof)
        self.assertEqual(self.operations.prepare_receiver(candidate, self.prepared, self.proof), self.receiver)
        self.hooks.verify_checkpoint.assert_called_once()
        self.hooks.prepare_receiver.assert_called_once()

    def test_boundary_moving_during_preparation_is_retryable_before_any_stop(self):
        with patch.object(LinuxOperations, 'observe', side_effect=[self.candidate, None]), \
                patch.object(LinuxOperations, 'reserve', side_effect=AssertionError('must_not_stop')), \
                self.assertRaises(ObservationRace):
            self.operations.observe(self.binding)
        self.assertIsNone(self.operations.prepared_cache)

    def test_reserved_observation_never_runs_checkpoint_or_tail_probe(self):
        self.operations.reservation_active = True
        with patch.object(LinuxOperations, 'observe', return_value=self.candidate):
            self.assertEqual(self.operations.observe(self.binding, durable=True), self.candidate)
        self.hooks.verify_checkpoint.assert_not_called()
        self.hooks.prepare_receiver.assert_not_called()

    def test_no_reservation_without_cached_receiving_artifacts(self):
        with self.assertRaisesRegex(ValueError, 'no_reservation_without_complete_preparation'):
            with self.operations.reserve(object(), 10):
                self.fail('unprepared reservation')

    def test_reservation_exit_drops_cache_for_same_handle_retry(self):
        self.operations.prepared_cache = (self.candidate, self.proof, self.receiver)
        handle = object()
        @contextmanager
        def reserved(actual, seconds):
            self.assertIs(actual, handle)
            self.assertTrue(self.operations.reservation_active)
            yield object()
        with patch.object(LinuxOperations, 'reserve', side_effect=reserved):
            with self.operations.reserve(handle, 10):
                pass
        self.assertFalse(self.operations.reservation_active)
        self.assertIsNone(self.operations.prepared_cache)

    def test_real_coordinator_retries_prestop_race_on_same_handle(self):
        pair = self.operations
        class CombinedOperations(FakeOperations):
            def observe(self, binding, *, durable=False):
                return pair.observe(binding, durable=durable)

            def verify_checkpoint(self, candidate):
                return pair.verify_checkpoint(candidate)

            def prepare_receiver(self, candidate, prepared, proof):
                return pair.prepare_receiver(candidate, prepared, proof)

            def reserve(self, handle, seconds):
                return pair.reserve(handle, seconds)

        fake = CombinedOperations(self.binding, observations=[self.candidate, None])
        self.hooks.verify_checkpoint.side_effect = lambda candidate: FakeOperations.verify_checkpoint(fake, candidate)
        self.hooks.prepare_receiver.side_effect = lambda *args: FakeOperations.prepare_receiver(fake, *args)
        with patch.object(LinuxOperations, 'observe', side_effect=lambda binding, **kwargs:
                FakeOperations.observe(fake, binding, **kwargs)), \
                patch.object(LinuxOperations, 'reserve', side_effect=lambda handle, seconds:
                    FakeOperations.reserve(fake, handle, seconds)):
            token = coordinate(self.binding, self.prepared, self.authority, fake)
        self.assertTrue(token['old_native_exited'])
        self.assertEqual(sum(name == 'open' for name, _ in fake.events), 1)
        self.assertEqual(sum(name == 'close' for name, _ in fake.events), 1)
        self.assertEqual(sum(name == 'wait' for name, _ in fake.events), 1)
        self.assertEqual(sum(name == 'commit' for name, _ in fake.events), 1)
        self.assertEqual(sum(name == 'dispatch' for name, _ in fake.events), 1)


class ProbeFailureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=WORKER)
        self.addCleanup(self.temporary.cleanup)
        self.receiver = PairReceiver.__new__(PairReceiver)
        self.receiver.probe_override = None
        self.receiver.source = Path(self.temporary.name)
        self.receiver.control = self.receiver.source / 'control'
        self.receiver.prepared = dict(new_plan={}, new_source_pins={})
        self.receiver.python = sys.executable
        self.receiver.probe_timeout_seconds = 20

    def test_timeout_is_terminal_prestop_refusal_with_durable_evidence(self):
        with patch('receiver.subprocess.run', side_effect=subprocess.TimeoutExpired(['CPU-only'], 20)), \
                self.assertRaisesRegex(Refusal, 'CPU_probe_timeout_no_reservation'):
            self.receiver._probe('tail', {})
        self.assertEqual(len(list(self.receiver.control.rglob('*.timeout.*.json'))), 1)

    def test_only_explicit_moving_tail_errors_are_retryable(self):
        for reason in ('journal_changed_during_scan', 'unraced_tail_probe', 'same_resolved_pair_state'):
            error = subprocess.CalledProcessError(1, ['CPU-only'], stderr='ValueError: ' + reason + '\n')
            with patch('receiver.subprocess.run', side_effect=error), self.assertRaises(ObservationRace):
                self.receiver._probe('tail', {})

    def test_corruption_is_not_relabelled_as_a_race(self):
        error = subprocess.CalledProcessError(1, ['CPU-only'], stderr='ValueError: checkpoint_tail_raw_record_integrity\n')
        with patch('receiver.subprocess.run', side_effect=error), \
                self.assertRaisesRegex(Refusal, 'CPU_probe_failed_no_handoff'):
            self.receiver._probe('tail', {})
