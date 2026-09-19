"""Concrete offline route wiring; all launch, owner and process actions mocked."""

from copy import deepcopy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import common as core
sys.path.insert(0, str(core.REPO))
from common import DEADLINE, digest, reference, sha, write_once
import integration


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / 'source'
        (self.source / 'gpu').mkdir(parents=True)
        self.original = core.HERE.parent / 'prepared_epoch4_v5/C2/epoch4/source/gpu/r188_node5_confinement.py'
        self.original_bytes = self.original.read_bytes()
        self.r188 = self.source / 'gpu/r188_node5_confinement.py'
        self.r188.write_bytes(self.original_bytes)
        self.binding = dict(pid=777, hard_end_unix=DEADLINE)
        self.prepared = dict(epoch_id='test-C2-epoch4', new_plan=dict(source_root=str(self.source)),
            new_source_pins={'gpu/r188_node5_confinement.py': sha(self.r188)})
        self.dependency = dict(path='/main-pinned-owner/DEPENDENCY.json', sha256='d' * 64)
        self.receipt = dict(schema='C2_RETENTION_MAIN_ROUTE_V1', life_binding_sha256=digest(self.binding),
            prepared_sha256=digest(self.prepared), source_pins_sha256=digest(self.prepared['new_source_pins']),
            owner_dependency=self.dependency, dispatcher_module='gpu.r188_node5_confinement')
        receipt = write_once(self.directory / 'ROUTE.json', self.receipt)
        self.configuration = dict(binding=self.binding, prepared=self.prepared, route_receipt=receipt,
            route_evidence_pins={str(self.r188): sha(self.r188)}, python_executable='/usr/bin/python3')
        self.owner = Mock(dependency=self.dependency)
        self.prefix = SimpleNamespace(reservation_budget=Mock())
        self.route = integration.ConcreteRoute(self.configuration, self.owner, self.prefix)
        self.token = dict(life_binding_sha256=digest(self.binding), old_native_exited=True,
            new_source_pins=self.prepared['new_source_pins'], deadline_unix=DEADLINE,
            receiver=dict(guard_path=str(self.directory / 'GUARD.json')))
        self.addCleanup(patch.stopall)
        patch('signal.pidfd_send_signal', side_effect=AssertionError('NO_ACTUAL_SIGNAL')).start()
        patch('os.kill', side_effect=AssertionError('NO_ACTUAL_SIGNAL')).start()
        patch('subprocess.run', side_effect=AssertionError('NO_ACTUAL_REMOTE_OR_GPU')).start()

    def test_preflight_does_not_invent_missing_Main_readiness_fields(self):
        result = self.route.preflight(self.binding, self.prepared)
        self.assertEqual(result, self.receipt)
        self.assertNotIn('r188_only_dispatch', result)
        self.owner.check.assert_called_once_with(self.binding, self.prepared['epoch_id'])

    def test_real_owner_refusal_prevents_any_dispatch(self):
        self.owner.check.side_effect = ValueError('actual_owner_not_fenced')
        with patch.object(integration.subprocess, 'Popen') as spawned:
            with self.assertRaisesRegex(ValueError, 'actual_owner'):
                self.route.dispatch_once(self.token)
            spawned.assert_not_called()

    def test_changed_dependency_cannot_reuse_route_receipt(self):
        self.owner.dependency = dict(self.dependency, sha256='f' * 64)
        with self.assertRaisesRegex(ValueError, 'source_bound_actual_route'):
            self.route.preflight(self.binding, self.prepared)

    def test_dispatch_is_original_r188_command_and_never_claims_LOADED(self):
        with patch.object(integration.subprocess, 'Popen', return_value=SimpleNamespace(pid=888)) as spawned:
            result = self.route.dispatch_once(self.token)
        expected = ['/usr/bin/python3', '-B', '-m', 'gpu.r188_node5_confinement',
            'dispatch', '--config', self.token['receiver']['guard_path']]
        self.assertEqual(spawned.call_args.args[0], expected)
        self.assertEqual(spawned.call_args.kwargs['cwd'], self.source)
        self.assertEqual(spawned.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
        self.assertEqual(result['outer_pid'], 888)
        self.assertIsNone(result['native_pid'])
        self.assertFalse(result['loaded'])
        self.assertFalse(result['parent_rebind_allowed'])
        self.assertEqual(self.original.read_bytes(), self.original_bytes)
        with patch.object(integration.subprocess, 'Popen') as spawned:
            with self.assertRaises(FileExistsError):
                self.route.dispatch_once(self.token)
            spawned.assert_not_called()

    def test_missing_or_expired_shared_budget_prevents_launch(self):
        with patch.object(integration.subprocess, 'Popen') as spawned:
            self.prefix.reservation_budget = None
            with self.assertRaisesRegex(ValueError, 'same_remaining_budget'):
                self.route.dispatch_once(self.token)
            self.prefix.reservation_budget = Mock()
            self.prefix.reservation_budget.check.side_effect = ValueError('expired')
            with self.assertRaisesRegex(ValueError, 'expired'):
                self.route.dispatch_once(self.token)
            spawned.assert_not_called()

    def test_altered_dispatcher_source_refused(self):
        self.r188.write_bytes(self.original_bytes + b'\n')
        self.configuration['route_evidence_pins'] = {str(self.r188): sha(self.r188)}
        with patch.object(integration.subprocess, 'Popen') as spawned:
            with self.assertRaisesRegex(ValueError, 'unchanged_original_r188'):
                self.route.dispatch_once(self.token)
            spawned.assert_not_called()

    def test_observer_reads_only_adjacent_COMPLETE_LEARN_no_fallback(self):
        operations = integration.C2Operations.__new__(integration.C2Operations)
        operations.binding, operations.approved = self.binding, True
        operations.bound_journal = {'dev': 1, 'ino': 2}
        with patch.object(integration, 'journal_identity', return_value=operations.bound_journal), \
                patch.object(integration, 'read_boundary', return_value=None) as reader:
            self.assertIsNone(operations.observe(self.binding))
            reader.assert_called_once_with(self.binding, max_records=2, durable=False)
            reader.reset_mock()
            reader.side_effect = ValueError('not_current_eligible_boundary')
            with self.assertRaisesRegex(ValueError, 'not_current'):
                operations.observe(self.binding)
            reader.assert_called_once()

    def test_wrong_journal_objects_refuse_before_read(self):
        operations = integration.C2Operations.__new__(integration.C2Operations)
        operations.binding, operations.approved = self.binding, True
        operations.bound_journal = {'dev': 1, 'ino': 2}
        with patch.object(integration, 'journal_identity', return_value={'dev': 1, 'ino': 3}), \
                patch.object(integration, 'read_boundary') as reader:
            with self.assertRaisesRegex(ValueError, 'original_journal_objects'):
                operations.observe(self.binding)
            reader.assert_not_called()

    def test_coordinator_and_guardian_closure_must_be_explicitly_pinned(self):
        boundary = core.REPO / 'research_loop/workers/post_recovery_retention_boundary_20260918'
        sources = list(core.HERE.glob('*.py')) + [boundary / name for name in ('boundary.py', 'coordinator.py', 'operations.py')]
        pins = {str(path): sha(path) for path in sources}
        integration.verify_coordinator_source(pins)
        del pins[str(boundary / 'coordinator.py')]
        with self.assertRaisesRegex(ValueError, 'original_guardian_sources'):
            integration.verify_coordinator_source(pins)

    def test_unknown_r188_inner_deadline_is_not_misreported_as_30_seconds(self):
        self.assertIn(b'timeout=100', self.original_bytes)
        self.assertIn(b"subprocess.run(argv,check=False)", self.original_bytes)


if __name__ == '__main__':
    unittest.main(verbosity=2)
