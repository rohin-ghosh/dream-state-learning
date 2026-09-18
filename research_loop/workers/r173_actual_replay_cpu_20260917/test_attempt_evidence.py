"""Local diagnosis of the frozen failed attempt, not another candidate run."""

import importlib.util
import json
import os
from pathlib import Path
import unittest


OWNED = Path(__file__).resolve().parent
specification = importlib.util.spec_from_file_location('r173_receiving', OWNED / 'receiving_cpu.py')
receiving = importlib.util.module_from_spec(specification)
specification.loader.exec_module(receiving)
RECEIPT_SHA256 = '26e9efb519fbc0a8129fd47daa115d71b715a3907ff19e506ca3ee69359de285'


class FailedAttemptEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (OWNED / 'ACTUAL_RECEIVING_CPU.json').read_bytes()
        cls.receipt = json.loads(cls.raw)

    def test_original_receiving_bytes_and_runner_are_preserved(self):
        self.assertEqual(receiving.sha(self.raw), RECEIPT_SHA256)
        self.assertEqual(self.raw, (OWNED / 'WRAPPER_STDOUT.txt').read_bytes())
        self.assertEqual(receiving.sha((OWNED / 'receiving_cpu.py').read_bytes()),
                         self.receipt['runner_ref']['sha256'])

    def test_transport_success_is_not_CPU_success_or_rebind(self):
        transport = json.loads((OWNED / 'WRAPPER_RESULT.json').read_bytes())
        self.assertEqual(transport['returncode'], 0)
        self.assertFalse(self.receipt['success'])
        self.assertFalse(self.receipt['test_suite_success'])
        self.assertFalse(self.receipt['evidence_rebind_eligible'])
        self.assertEqual(self.receipt['status'], 'FAILED_NO_RETRY')
        self.assertEqual((self.receipt['tests_run'], self.receipt['errors'], self.receipt['failures']),
                         (85, 87, 0))
        self.assertIn('FAILED (errors=87)', self.receipt['test_output'])

    def test_source_manifest_is_every_actual_old_pin_plus_three_helpers(self):
        source = Path(receiving.OLD_SOURCE)
        originals = {str(Path(entry['path']).relative_to(source)): entry['sha256']
                     for entry in self.receipt['receiving_bound_reads']
                     if Path(entry['path']).is_relative_to(source)}
        self.assertEqual(len(originals), 1854)
        receiving.validate_pins(originals)
        expected = dict(originals, **receiving.HELPERS)
        self.assertEqual(self.receipt['candidate_source_sha256'], expected)
        self.assertEqual(self.receipt['candidate_source_manifest_sha256'], receiving.sha(receiving.encoded(expected)))
        self.assertTrue(self.receipt['source_unchanged_after_tests'])
        self.assertFalse(set(expected).intersection(receiving.SUFFIX_FILES))

    def test_loaded_files_are_from_candidate_but_import_is_not_sleep_execution(self):
        source = Path(self.receipt['candidate_source_root'])
        loaded = self.receipt['executed_project_files']
        self.assertEqual(len(loaded), 33)
        for name, reference in loaded.items():
            self.assertEqual(reference['path'], str(source / name))
            self.assertEqual(reference['sha256'], self.receipt['candidate_source_sha256'][name])
        self.assertEqual(loaded[receiving.NATIVE_PATH]['sha256'], receiving.NATIVE_SHA256)
        for name, reference in self.receipt['runtime_dependencies'].items():
            self.assertEqual(reference['sha256'], loaded[name.replace('.', '/') + '.py']['sha256'])
        native_outcomes = [entry for entry in self.receipt['outcomes']
                           if '.NativeReplayIntegrationTests.' in entry['test']]
        self.assertTrue(native_outcomes)
        self.assertFalse(any(entry['status'] == 'PASS' for entry in native_outcomes))

    def test_reproduces_directory_descriptor_fence_bug_without_rerun(self):
        fence = receiving.RuntimeFence(Path('/candidate'), {})
        with self.assertRaisesRegex(PermissionError, 'read_outside_candidate_or_installed_runtime:/'):
            fence.audit('open', ('/', None, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC))
        self.assertIn('read_outside_candidate_or_installed_runtime:/', self.receipt['denied_runtime_operations'])
        self.assertIn("descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)",
                      self.receipt['outcomes'][0]['traceback'])

    def test_Torch_import_error_is_not_mislabeled_as_unavailable_or_successful(self):
        outcomes = self.receipt['torch']['real_torch_test']
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]['status'], 'ERROR')
        self.assertIn('write_outside_fixture_tmp:/dev/null', outcomes[0]['traceback'])
        self.assertIsNone(self.receipt['torch']['cuda_initialized'])
        self.assertEqual(self.receipt['skipped'], [])

    def test_authority_and_scope_claims_stay_negative(self):
        for key in ('operational_GO_created', 'saved_handoff_created', 'full_source_approval',
                    'saved_state_ownership_established', 'evaluator_admission',
                    'test_assertions_changed', 'numerical_tolerances_changed'):
            self.assertFalse(self.receipt[key])
        self.assertEqual(self.receipt['attempt_limit'], 1)
        self.assertFalse(self.receipt['retry_permitted'])


if __name__ == '__main__':
    unittest.main()
