import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r125_cpu_experiment as cpu
from gpu import orch_r153_code_blocks as blocks
from gpu import orch_r153_community_transport as transport
from organism_v6.orch_r125_experiment_request import make_request
from r184_cpu_probe import PLAIN_FENCE


class CpuTransportTests(unittest.TestCase):
    def request(self, kind='BUILDER_TEST'):
        return make_request('print(6 * 7)\n', dict(kind=kind, record_index=1,
            record_sha256=hashlib.sha256(PLAIN_FENCE.encode()).hexdigest()))

    def test_plain_python_fence_routes_exact_source(self):
        route, report = transport.code_route(PLAIN_FENCE)
        self.assertEqual(route, 'CPU')
        self.assertEqual(report['source'], 'print(6 * 7)\n')
        self.assertEqual(report['transformations'], [])
        self.assertEqual(report['policy'], blocks.POLICY)

    def test_unlabelled_plain_fence_routes_python(self):
        route, report = transport.code_route('```\nprint(6 * 7)\n```\n')
        self.assertEqual(route, 'CPU')
        self.assertEqual(report['source'], 'print(6 * 7)\n')

    def test_builder_smoke_never_claims_child_provenance(self):
        self.assertEqual(cpu.verify_origin(self.request(), None, code_policy=blocks.POLICY),
            dict(kind='BUILDER_TEST', child_generated=False))
        with self.assertRaisesRegex(ValueError, 'builder_test_cannot_claim_child_journal'):
            cpu.verify_origin(self.request(), '/not/a/child', code_policy=blocks.POLICY)

    def test_child_request_requires_real_journal(self):
        with self.assertRaisesRegex(ValueError, 'TRAIN_child_requires_journal'):
            cpu.verify_origin(self.request('TRAIN_CHILD_RESPONSE'), None, code_policy=blocks.POLICY)

    def test_missing_gate_refuses_before_spool_or_process(self):
        with tempfile.TemporaryDirectory(prefix='r184-cpu-test-') as directory:
            root = Path(directory).resolve()
            with patch.object(cpu.subprocess, 'run') as run, patch.object(cpu.subprocess, 'Popen') as launch:
                with self.assertRaises(FileNotFoundError):
                    cpu.run_request(json.dumps(self.request()).encode(), root / 'spool',
                        root / 'missing-gate', code_policy=blocks.POLICY)
                run.assert_not_called()
                launch.assert_not_called()
            self.assertFalse((root / 'spool').exists())

    def test_missing_five_modes_is_not_a_gate(self):
        with tempfile.TemporaryDirectory(prefix='r184-cpu-test-') as directory:
            with self.assertRaises(FileNotFoundError):
                cpu.verify_gate(Path(directory).resolve())

    def test_cpu_once_rejects_unbound_clone_root_before_io(self):
        with self.assertRaisesRegex(ValueError, 'new_canonical_R153_life_root'):
            transport.cpu_once('/localhome/local-rohing/orch_r184_c2_copy/life',
                'unbound', self.request()['origin'], '0' * 64, start=False)

    def test_wrapper_gap_is_explicit(self):
        self.assertNotIn('ovx', transport.WRAPPERS)
        self.assertEqual(transport.WRAPPERS['ovx2'], 'gpu/ovx2_ssh.sh')


if __name__ == '__main__':
    unittest.main()
