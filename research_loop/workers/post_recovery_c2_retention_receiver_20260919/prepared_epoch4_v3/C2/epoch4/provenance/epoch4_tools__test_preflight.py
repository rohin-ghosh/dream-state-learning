"""Synthetic bounded-preflight and generated receiver checks; no live callbacks."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from prefix_preflight import PrefixPreflight, ReservationBudget, digest, validate_policy, verify_static


SAME = 'SAME_MOUNT_NAMESPACE'
CROSS = 'SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE'


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.policy = dict(schema='C2_RESERVED_PREFLIGHT_POLICY_V1', stop_seconds=30, commit_margin_seconds=2,
            static_receipt_path='/not-live/STATIC.json', static_receipt_sha256='a' * 64)
        self.binding = dict(guard_sha256='b' * 64)
        self.prepared = dict(new_source_pins={'source.py': 'c' * 64}, epoch_id='test-C2', new_plan={})
        self.approved = dict(path='/not-live/AUTHORITY.json', sha256='d' * 64)
        environment = dict(boot_id='boot', mount_namespace=dict(dev=1, ino=2))
        self.authority = dict(consumer_context_mode=CROSS)
        self.proof = dict(binding=dict(environment=environment))
        self.receipt = dict(schema='C2_PREFIX_RESERVED_READINESS_V1', life_binding_sha256=digest(self.binding),
            prepared_sha256=digest(self.prepared), source_pins_sha256=digest(self.prepared['new_source_pins']),
            prefix_authority=self.approved, deadline_unix=1789927200, epoch_id='test-C2',
            reserved_total_seconds_upper_bound=20, evidence=[dict(path='synthetic')],
            checks={name: True for name in ('actual_C2_saved_payload_CPU', 'actual_C2_prefix_and_new_tail_CPU',
                'actual_original_r188_consumer_context', 'producer_consumer_filesystem_objects_verified',
                'all_reserved_work_cost_bounded', 'source_control_tests_passed', 'explicit_trust_review_ratification',
                'parent_bridge_guard_work_cost_bounded', 'bounded_context_clause_delegation_reviewed')},
            consumer_context=dict(admission_module='gpu.r188_node5_confinement', original_guard_sha256='b' * 64,
                mode=CROSS, producer_environment=environment,
                consumer_environment=dict(boot_id='boot', mount_namespace=dict(dev=1, ino=3)),
                source_pins_sha256=digest(self.prepared['new_source_pins']), filesystem_evidence=[dict(synthetic=True)]))
        self.api = SimpleNamespace(document=Mock(side_effect=lambda reference: deepcopy(self.receipt)),
            pinned=Mock(return_value=b'synthetic'), load_authority=Mock(side_effect=lambda *args, **kwargs:
                (deepcopy(self.authority), deepcopy(self.proof))))
        self.control = PrefixPreflight(self.api, self.approved, self.policy)

    def verify(self):
        return self.control.verify_before_reservation(self.binding, self.prepared)

    def test_explicit_cross_mode_with_exact_pinned_chain(self):
        self.assertEqual(self.verify(), self.receipt)

    def test_every_required_real_gate_is_mandatory(self):
        for name in self.receipt['checks']:
            with self.subTest(name=name):
                self.receipt['checks'][name] = False
                with self.assertRaises(ValueError):
                    self.verify()
                self.receipt['checks'][name] = True

    def test_actual_entire_path_not_reader_cost(self):
        for cost in (28, 30, 41.69, float('inf'), float('nan'), True, -1):
            with self.subTest(cost=cost):
                self.receipt['reserved_total_seconds_upper_bound'] = cost
                with self.assertRaises(ValueError):
                    self.verify()

    def test_default_still_requires_same_namespace(self):
        self.authority['consumer_context_mode'] = self.receipt['consumer_context']['mode'] = SAME
        with self.assertRaisesRegex(ValueError, 'strict_default_same_namespace'):
            self.verify()

    def test_changed_boot_refused_even_explicit_mode(self):
        self.receipt['consumer_context']['consumer_environment']['boot_id'] = 'other'
        with self.assertRaises(ValueError):
            self.verify()

    def test_untrusted_namespace_allowlist_refused(self):
        self.receipt['consumer_context']['allowed_namespaces'] = [2, 3]
        with self.assertRaisesRegex(ValueError, 'no_namespace_allowlist'):
            self.verify()

    def test_missing_external_bytes_refused(self):
        self.api.pinned.return_value = b''
        with self.assertRaises(ValueError):
            self.verify()

    def test_policy_cannot_extend_30_seconds(self):
        self.policy['stop_seconds'] = 31
        with self.assertRaises(ValueError):
            validate_policy(self.policy)

    def test_source_CPU_cannot_create_Main_authority(self):
        with self.assertRaises(ValueError):
            self.control.attach_cpu_authority(dict(passed=True))

    def test_budget_requires_pre_stop_evidence(self):
        with self.assertRaises(ValueError):
            with self.control.budget(28, clock=lambda: 0):
                self.fail('unreachable')

    def test_no_static_validation_after_stop(self):
        self.verify()
        with self.control.budget(28, clock=lambda: 0):
            with self.assertRaises(ValueError):
                self.verify()

    def test_one_budget_no_extension_or_nested_budget(self):
        self.verify()
        with self.assertRaises(ValueError):
            with self.control.budget(29, clock=lambda: 0):
                self.fail('unreachable')
        with self.control.budget(28, clock=lambda: 0):
            with self.assertRaises(ValueError):
                with self.control.budget(28, clock=lambda: 0):
                    self.fail('unreachable')

    def test_budget_remaining_timeout_and_no_fallback(self):
        now = [5]
        budget = ReservationBudget(28, clock=lambda: now[0])
        self.assertEqual(budget.timeout(120), 23)
        called = Mock(side_effect=lambda: now.__setitem__(0, 29))
        with self.assertRaisesRegex(ValueError, 'expired_no_retry_or_fallback'):
            budget.call(called)
        with self.assertRaises(ValueError):
            budget.call(called)
        called.assert_called_once()

    def test_bounded_derivation_not_production(self):
        self.verify()
        self.api.selection_guard = Mock(return_value={'guard': 'derived'})
        self.api.reference = Mock(return_value=dict(path='/synthetic/selected', sha256='e' * 64))
        self.api.verify_selection_binding = Mock(return_value={'guard_path': '/synthetic/selected'})
        writer = Mock()
        with self.control.budget(28, clock=lambda: 0):
            self.control.derive_selection(self.prepared, {}, {}, writer, '/synthetic')
        self.api.selection_guard.assert_called_once()
        writer.assert_called_once()
        self.assertFalse(hasattr(self.api, 'produce'))


class GeneratedReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tools = Path(__file__).resolve().parent
        for parent in tools.parents:
            if (parent / 'research_loop').is_dir():
                sys.path.insert(0, str(parent))
                break
        specification = importlib.util.spec_from_file_location('c2_test_generated_receiver', tools / 'receiving_core.py')
        cls.module = importlib.util.module_from_spec(specification)
        sys.modules[specification.name] = cls.module
        specification.loader.exec_module(cls.module)
        cls.text = (tools / 'receiving_core.py').read_text()

    def test_original_guard_and_exact_CPU_precede_tail(self):
        method = self.text.split('    def prepare_receiver(', 1)[1].split('    def recheck_checkpoint(', 1)[0]
        self.assertLess(method.index('receiving_cpu = self.prefix_control.receiving_cpu'), method.index("scanned = self._probe('tail'"))
        self.assertLess(method.index("guard_proof = self._probe('guard'"), method.index("scanned = self._probe('tail'"))
        self.assertIn("cpu_receipt_sha256=sha(attempt / 'RECEIVING_CPU.json')", method)
        self.assertIn('self.prefix_control.cpu_context', method)

    def test_subprocess_caps_remaining_time_without_native_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            receiver = object.__new__(self.module.C2Receiver)
            receiver.source = receiver.control = Path(temporary)
            receiver.python = sys.executable
            receiver.prefix_control = SimpleNamespace(reservation_budget=ReservationBudget(28, clock=lambda: 10))
            receiver.prefix_context = {'synthetic_original_chain': True}
            result = SimpleNamespace(stdout='{"synthetic":true}', stderr='')
            with patch.object(self.module.subprocess, 'run', return_value=result) as run:
                receiver._probe('tail', {}, {}, {})
            self.assertEqual(run.call_args.kwargs['timeout'], 18)
            request = json.loads(next((Path(temporary) / 'cpu_requests').glob('tail.*.json')).read_text())
            self.assertEqual(request['prefix_context'], receiver.prefix_context)

    def test_expired_budget_never_launches_probe(self):
        with tempfile.TemporaryDirectory() as temporary:
            receiver = object.__new__(self.module.C2Receiver)
            receiver.source = receiver.control = Path(temporary)
            receiver.python = sys.executable
            receiver.prefix_control = SimpleNamespace(reservation_budget=ReservationBudget(0, clock=lambda: 1))
            receiver.prefix_context = {'synthetic': True}
            with patch.object(self.module.subprocess, 'run') as run, self.assertRaises(ValueError):
                receiver._probe('tail', {}, {}, {})
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
