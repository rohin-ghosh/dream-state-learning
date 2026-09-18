"""Synthetic validator cases; no failed receipt is rewritten or promoted."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('r170_assembly_v2_tests', HERE / 'ASSEMBLY_V2.py')
assembly = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assembly)
FAILED_RECEIPT = HERE.parent / 'r174_receiving_cpu_repair_20260917/ACTUAL_RECEIVING_CPU.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


class ReceivingBindingTests(unittest.TestCase):
    def setUp(self):
        self.original_bytes = FAILED_RECEIPT.read_bytes()
        self.evidence = json.loads(self.original_bytes)
        self.evidence.update(schema='R175_ACTUAL_RECEIVING_CPU_V1',
                             status='CPU_TESTS_PASS_NOT_ADMISSION', success=True,
                             evidence_rebind_eligible=True, denied_runtime_operations=[], failure=None)
        self.evidence.pop('failure_type', None)
        self.evidence.pop('traceback', None)
        self.helpers = self.evidence['added_python_files']
        self.guard = dict(source_pins={name: checksum for name, checksum in
            self.evidence['candidate_source_sha256'].items() if name not in self.helpers},
            hard_end_unix=self.evidence['hard_end_unix_unmodified'])
        self.plan = dict(source_root=self.evidence['old_source_root'], root=self.evidence['old_life_root'])
        self.approval = dict(old_guard_ref=self.evidence['old_guard_ref'],
            old_plan_ref=self.evidence['old_plan_ref'],
            receiving_runner_sha256=self.evidence['runner_ref']['sha256'],
            train_fixture_sha256=self.evidence['train_fixture_ref']['sha256'],
            required_test_ids=sorted(entry['test'] for entry in self.evidence['outcomes']),
            original_test_sha256={name: record['original_sha256'] for name, record in self.evidence['tests'].items()},
            reviewed_test_records=deepcopy(self.evidence['tests']),
            candidate_source_manifest_sha256=self.evidence['candidate_source_manifest_sha256'],
            reviewed_runtime_probes=deepcopy(self.evidence['allowed_runtime_probes']))

    def tearDown(self):
        self.assertEqual(FAILED_RECEIPT.read_bytes(), self.original_bytes)

    def validate(self, evidence=None):
        return assembly.validate_receiving(self.evidence if evidence is None else evidence,
            self.approval, self.guard, self.plan, self.helpers, require)

    def test_synthetic_positive_preserves_exact_runtime_not_negative_test_support(self):
        normalized = self.validate()
        expected = dict(self.evidence['candidate_source_sha256'], **{
            assembly.NATIVE_EVIDENCE_KEY: self.evidence['candidate_source_sha256'][assembly.NATIVE_PATH]})
        self.assertEqual(normalized['source_sha256'], expected)
        self.assertFalse(set(assembly.SUPPORT_PINS).intersection(normalized['source_sha256']))

    def test_actual_failed_R174_is_rejected_and_preserved(self):
        with self.assertRaisesRegex(ValueError, 'actual_receiving_status'):
            self.validate(json.loads(self.original_bytes))

    def test_historical_schema_cannot_masquerade_as_R175_receiving(self):
        with self.assertRaisesRegex(ValueError, 'actual_receiving_status'):
            self.validate(dict(self.evidence, schema='R173_ACTUAL_RECEIVING_CPU_V1'))

    def test_actual_positive_R175_schema_is_compatible_without_writing_approval(self):
        path = HERE.parent / 'r175_receiving_ldconfig_20260917/ACTUAL_RECEIVING_CPU.json'
        raw = path.read_bytes()
        evidence = json.loads(raw)
        self.approval.update(receiving_runner_sha256=evidence['runner_ref']['sha256'],
            reviewed_test_records=evidence['tests'], reviewed_runtime_probes=evidence['allowed_runtime_probes'])
        normalized = self.validate(evidence)
        self.assertEqual(len(normalized['source_sha256']), 1858)
        self.assertEqual(path.read_bytes(), raw)

    def test_incomplete_failed_skipped_duplicate_or_boolean_test_counts_rejected(self):
        mutations = [lambda document: document['outcomes'].pop(),
            lambda document: document['outcomes'].append(document['outcomes'][0]),
            lambda document: document['outcomes'][0].update(status='ERROR'),
            lambda document: document.update(tests_run=True),
            lambda document: document.update(skipped=['one']),
            lambda document: document.update(failures=True)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                evidence = deepcopy(self.evidence)
                mutation(evidence)
                with self.assertRaises(ValueError):
                    self.validate(evidence)

    def test_denied_operation_or_unreviewed_library_probe_is_not_success(self):
        for field, value in [('denied_runtime_operations', ['subprocess']),
                              ('traceback', 'previous failure'),
                              ('allowed_runtime_probes', [{'command': ['gcc']}])]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(dict(self.evidence, **{field: value}))

    def test_attempt_scope_and_read_custody_are_not_optional(self):
        for field, value in [('attempt_limit', 2), ('retry_permitted', True),
                              ('receiving_bound_reads', []), ('operational_bytes_read', 65 * 1024 * 1024)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(dict(self.evidence, **{field: value}))

    def test_added_helper_hashes_must_match_not_only_the_names(self):
        evidence = deepcopy(self.evidence)
        next_name = next(iter(evidence['added_python_files']))
        evidence['added_python_files'][next_name] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'only_three_added_runtime_files'):
            self.validate(evidence)

    def test_wrong_plan_life_source_or_wall_rejected(self):
        for field in ('old_guard_ref', 'old_plan_ref', 'old_source_root', 'old_life_root',
                      'hard_end_unix_unmodified'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(dict(self.evidence, **{field: 'different'}))

    def test_scope_expansions_and_missing_flags_rejected(self):
        for field in ('full_source_approval', 'evaluator_admission', 'saved_state_ownership_established',
                      'saved_handoff_created', 'operational_GO_created', 'test_assertions_changed',
                      'numerical_tolerances_changed', 'startup_copied'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(dict(self.evidence, **{field: True}))

    def test_changed_receiving_native_or_plain_context_or_extra_suffix_rejected(self):
        for name in (assembly.NATIVE_PATH, 'organism_v6/orch_r125_plain_context.py',
                     'gpu/orch_r145_suffix_loss.py'):
            evidence = deepcopy(self.evidence)
            evidence['candidate_source_sha256'][name] = '0' * 64
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.validate(evidence)

    def test_wrong_manifest_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, 'manifest_hash'):
            self.validate(dict(self.evidence, candidate_source_manifest_sha256='0' * 64))

    def test_missing_actual_native_or_helper_execution_rejected(self):
        for name in [assembly.NATIVE_PATH, *self.helpers]:
            evidence = deepcopy(self.evidence)
            evidence['executed_project_files'].pop(name)
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.validate(evidence)

    def test_wrong_loaded_or_executed_module_origin_rejected(self):
        for field in ('loaded_project_modules', 'executed_project_files'):
            evidence = deepcopy(self.evidence)
            next(iter(evidence[field].values()))['path'] = '/tmp/foreign.py'
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(evidence)

    def test_negative_helpers_must_be_executed_and_outside_candidate(self):
        for name in assembly.SUPPORT_PINS:
            evidence = deepcopy(self.evidence)
            evidence['test_support_executed'][name]['path'] = '/tmp/candidate.py'
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.validate(evidence)

    def test_real_torch_is_required_no_cuda_no_stub_pass(self):
        for field, value in [('imported', False), ('cuda_initialized', True), ('real_torch_test', [])]:
            evidence = deepcopy(self.evidence)
            evidence['torch'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(evidence)

    def test_original_tests_and_path_adaptations_must_match_review(self):
        for field in ('original_sha256', 'adapted_sha256', 'path_only_changes'):
            evidence = deepcopy(self.evidence)
            next(iter(evidence['tests'].values()))[field] = 'changed'
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(evidence)

    def test_V1_still_matches_immutable_source_pin(self):
        self.assertEqual(hashlib.sha256((HERE / 'ASSEMBLY.py').read_bytes()).hexdigest(),
                         assembly.V1_SHA256)

    def test_every_staging_and_finalization_input_is_bound_to_reviewed_scope(self):
        approval = dict(self.approval, approved_intake_sha256='1' * 64)
        arguments = [approval['old_guard_ref'], approval['old_plan_ref'], '1' * 64]
        assembly.validate_assembly_inputs(approval, *arguments, require)
        for position in range(3):
            changed = list(arguments)
            changed[position] = 'other'
            with self.subTest(position=position), self.assertRaisesRegex(ValueError, 'assembly_inputs'):
                assembly.validate_assembly_inputs(approval, *changed, require)


if __name__ == '__main__':
    unittest.main()
