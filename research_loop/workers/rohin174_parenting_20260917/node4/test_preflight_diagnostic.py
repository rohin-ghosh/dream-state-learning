"""Rejected evidence stays diagnostic even when a process has disappeared."""

from copy import deepcopy
from pathlib import Path
import sys
import unittest
from types import ModuleType

HOME = Path(__file__).resolve().parent
sys.path.insert(0, str(HOME))
import preflight_diagnostic as diagnostic


def helper_functions():
    import ast
    import hashlib
    import json
    source = HOME.parents[3] / 'gpu/orch_r179_busy_preflight.py'
    tree = ast.parse(source.read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in ('annotate', 'classify_argv_only')]
    module = ModuleType('diagnostic_test_pure_Main_functions')
    module.__dict__.update(deepcopy=deepcopy, hashlib=hashlib, json=json,
        KERNEL_KEYS=('pid', 'uid', 'start_ticks', 'boot_id'), SCHEMA='R179_BUSY_PREFLIGHT_EVIDENCE_ONLY_V1')
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), 'exec'), module.__dict__)
    return module


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.helper = helper_functions()
        identity = dict(pid=42, uid=0, start_ticks='123', boot_id='boot')
        self.report = dict(scanner_euid=0, clear=False, gpu=dict(uuid='GPU-target', memory_used_mib=20000),
            compute_processes=[dict(pid=99, gpu_uuid='GPU-target')],
            processes=[dict(identity, target_device_open=False, cvd=None, pinned_identity=identity)],
            blocking_reasons=['active_compute_pid:99', 'process_identity_drift:42'])
        self.samples = {42: [dict(identity, executable_identity=[1, 2], visibility_complete=True,
            target_open=False, cvd=None, command_sha256=letter * 64) for letter in ('a', 'b', 'b')]}

    def test_original_all_fields_and_classification_unchanged(self):
        original, samples = deepcopy(self.report), deepcopy(self.samples)
        result = diagnostic.explain(self.report, self.samples, self.helper)
        self.assertEqual(result['original_annotated_report'], self.helper.annotate(original, samples))
        self.assertEqual(self.report, original)
        self.assertEqual(self.samples, samples)
        self.assertFalse(result['acceptance_changed'])
        self.assertFalse(result['admission_receipt'])
        self.assertFalse(result['original_annotated_report']['clear'])
        self.assertEqual(result['rejected_process_evidence'], {})

    def test_too_few_samples_not_promoted(self):
        self.samples[42] = self.samples[42][:1]
        result = diagnostic.explain(self.report, self.samples, self.helper)
        evidence = result['rejected_process_evidence']['42']
        self.assertEqual(evidence['original_sample_count'], 1)
        self.assertIn('fewer_than_three_original_samples', evidence['diagnostic_failure_reasons'])
        self.assertEqual(result['original_annotated_report']['r179_preflight_evidence']['eligible_non_gpu_argv_only_pids'], [])

    def test_changed_uid_or_executable_and_visibility_not_promoted(self):
        for key, value in (('uid', 122), ('executable_identity', [2, 3]), ('visibility_complete', False)):
            with self.subTest(key=key):
                samples = deepcopy(self.samples)
                samples[42][-1][key] = value
                result = diagnostic.explain(self.report, samples, self.helper)
                self.assertFalse(result['rejected_process_evidence']['42']['eligible_for_exception'])
                self.assertTrue(result['rejected_process_evidence']['42']['diagnostic_failure_reasons'])

    def test_missing_process_and_unrelated_reasons_preserved(self):
        self.report['processes'] = []
        self.report['blocking_reasons'].append('not_process_identity_drift:77')
        result = diagnostic.explain(self.report, {}, self.helper)
        self.assertEqual(set(result['rejected_process_evidence']), {'42'})
        self.assertIn('no_original_process_entry', result['rejected_process_evidence']['42']['diagnostic_failure_reasons'])
        self.assertEqual(result['original_annotated_report']['blocking_reasons'], self.report['blocking_reasons'])


if __name__ == '__main__':
    unittest.main()
