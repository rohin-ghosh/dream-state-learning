"""CPU-only source-scaffold wiring and fail-closed regression tests."""

import hashlib
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('r170_scaffold_v2_test', HERE / 'SCAFFOLD_V2_OPERATOR.py')
operator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(operator)


class SourceScaffoldTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.stage = Path(temporary.name) / 'stage'
        self.bootstrap = self.stage / 'bootstrap'
        self.here = self.bootstrap / 'research_loop/workers/r170_replay_boundary_20260917'
        self.here.mkdir(parents=True)
        for name in ('SCOPE.json', 'ASSEMBLY_V2.py'):
            (self.here / name).write_bytes((HERE / name).read_bytes())
        self.checksum = hashlib.sha256((self.here / 'ASSEMBLY_V2.py').read_bytes()).hexdigest()
        self.reference = dict(path=str(self.here / 'APPROVAL.json'), sha256='1' * 64)
        self.approval = dict(old_guard_ref=operator.GUARD_REF,
            approved_intake_sha256=operator.SCOPE_SHA256,
            old_plan_ref={'path': '/old/plan', 'sha256': '2' * 64},
            receiving_cpu_ref={'path': '/actual/cpu', 'sha256': '3' * 64},
            historical_cpu_ref={'path': '/historical/cpu', 'sha256': '4' * 64},
            independent_review_ref={'path': '/review', 'sha256': '5' * 64})
        self.scaffold = Mock(return_value=dict(scaffold_ref={'path': '/scaffold', 'sha256': '6' * 64},
            source_root=str(self.stage / 'physical1/source'), source_pins={'gpu/helper.py': '7' * 64},
            plan_ref={'path': '/new/plan', 'sha256': '8' * 64}))
        self.write = Mock()
        self.assembly = dict(replay=SimpleNamespace(read_bound=Mock(return_value=self.approval)),
            scaffold_immutable_files=self.scaffold, _write=self.write)
        self.module = SimpleNamespace(assembly_namespace=Mock(return_value=self.assembly))
        patches = [patch.object(operator, 'HERE', self.here),
            patch.object(operator, 'STAGE', self.stage), patch.object(operator, 'BOOTSTRAP', self.bootstrap),
            patch.object(operator.importlib.util, 'spec_from_file_location',
                         return_value=SimpleNamespace(loader=SimpleNamespace(exec_module=Mock()))),
            patch.object(operator.importlib.util, 'module_from_spec', return_value=self.module)]
        for replacement in patches:
            replacement.start()
            self.addCleanup(replacement.stop)

    def test_only_exact_receiving_evidence_and_scope_reach_scaffold(self):
        receipt = operator.execute(self.reference, self.checksum)
        self.module.assembly_namespace.assert_called_once_with(self.reference)
        arguments = self.scaffold.call_args.kwargs
        self.assertEqual(arguments['cpu_evidence_ref'], self.approval['receiving_cpu_ref'])
        self.assertEqual(arguments['old_guard_ref'], operator.GUARD_REF)
        self.assertEqual(arguments['old_plan_ref'], self.approval['old_plan_ref'])
        self.assertEqual(arguments['approved_intake_sha256'], operator.SCOPE_SHA256)
        self.assertEqual(arguments['helper_source_root'], self.bootstrap)
        self.assertEqual(arguments['new_source_root'], self.stage / 'physical1/source')
        self.assertEqual(arguments['output_root'], self.stage / 'physical1')
        self.assertEqual(receipt['historical_cpu_ref'], self.approval['historical_cpu_ref'])
        for flag in ('main_go_created', 'gpu_used', 'model_called', 'targeted_dose_executed'):
            self.assertIs(receipt[flag], False)
        self.assertEqual(receipt['signals_sent'], 0)
        self.write.assert_called_once_with(self.stage / 'physical1/RECEIVING_GATE_BINDING.json', receipt)

    def test_wrong_source_hash_or_location_refuses_before_assembly_import(self):
        with self.assertRaisesRegex(ValueError, 'location_scope_and_source'):
            operator.execute(self.reference, '0' * 64)
        with patch.object(operator, 'BOOTSTRAP', self.stage / 'other'):
            with self.assertRaisesRegex(ValueError, 'location_scope_and_source'):
                operator.execute(self.reference, self.checksum)
        self.module.assembly_namespace.assert_not_called()

    def test_wrong_life_or_scope_never_copies(self):
        for field in ('old_guard_ref', 'approved_intake_sha256'):
            with self.subTest(field=field), patch.dict(self.approval, {field: 'wrong'}):
                with self.assertRaisesRegex(ValueError, 'one_creative_life'):
                    operator.execute(self.reference, self.checksum)
        self.scaffold.assert_not_called()
        self.write.assert_not_called()

    def test_receiving_refusal_or_copy_failure_never_writes_success(self):
        self.scaffold.side_effect = ValueError('receiving_or_copy_refusal')
        with self.assertRaisesRegex(ValueError, 'receiving_or_copy_refusal'):
            operator.execute(self.reference, self.checksum)
        self.write.assert_not_called()

    def test_failed_assembly_approval_does_not_copy(self):
        self.module.assembly_namespace.side_effect = ValueError('unreviewed')
        with self.assertRaisesRegex(ValueError, 'unreviewed'):
            operator.execute(self.reference, self.checksum)
        self.scaffold.assert_not_called()


if __name__ == '__main__':
    unittest.main()
