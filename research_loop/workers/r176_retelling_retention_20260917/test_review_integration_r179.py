"""Independent integration regressions with synthetic local state only."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import preparation_io as common
import r176_runner as runner


HERE = Path(__file__).resolve().parent
RECEIVING = HERE / 'REVIEW_R179_RECEIVING_READONLY_20260917T1730Z.json'
DIAGNOSTIC = HERE / 'REVIEW_R179_VALIDATE_READONLY_20260917T1732Z.json'


class IntegrationR179Tests(unittest.TestCase):
    def setUp(self):
        self.proof = json.loads(RECEIVING.read_bytes())
        self.public = json.loads((HERE / 'preparation1/narrow_runner1/PUBLIC_METADATA.json').read_bytes())

    def test_actual_public_receipt_and_frozen_runner_are_exact(self):
        self.assertEqual(hashlib.sha256((HERE / 'preparation1/narrow_runner1/PUBLIC_METADATA.json').read_bytes()).hexdigest(),
            self.proof['public_receipt']['sha256'])
        self.assertEqual(hashlib.sha256((HERE / 'r176_runner.py').read_bytes()).hexdigest(),
            self.proof['runner_sha256'])
        self.assertEqual((HERE / 'r176_runner.py').read_bytes(),
            (HERE / 'preparation1/narrow_runner1/author_source/r176_runner.py').read_bytes())
        source_request = json.loads((HERE / 'preparation1/receiving1/REQUEST.json').read_bytes())
        source_request['source_pins'] = json.loads((HERE / 'preparation1/receiving1/SOURCE_FREEZE.json').read_bytes())
        self.assertEqual(common.digest(source_request), self.proof['source']['sha256'])
        self.assertTrue(all(self.proof['checks'].values()))

    def test_mandatory_receiving_reads_exceed_both_exact_phase_caps(self):
        minimum = sum(self.proof[field] for field in (
            'source_request_bytes', 'source_bytes_total', 'cpu_gate_bytes', 'interpreter_bytes'))
        self.assertEqual(minimum, 25318990)
        self.assertEqual(self.proof['phase_metadata_caps_unmapped'], [25165824, 25165824])
        for cap in self.proof['phase_metadata_caps_unmapped']:
            self.assertGreater(minimum, cap)
            with tempfile.TemporaryDirectory(prefix='r179_fixture_', dir=HERE) as temporary:
                root = Path(temporary)
                reader = common.Reader(root, {'metadata': {'document': {'bytes': cap}, 'reference': {}}}, [])
                with patch.object(common.time, 'time', return_value=common.END - 3600):
                    for field in ('source_request_bytes', 'source_bytes_total', 'cpu_gate_bytes'):
                        reader.charge(root / field, 'metadata', self.proof[field])
                    with self.assertRaisesRegex(ValueError, 'delegated_read_cap'):
                        reader.charge(root / 'interpreter', 'metadata', self.proof['interpreter_bytes'])
                self.assertEqual(reader.charged['metadata'], minimum)
                self.assertEqual(reader.actual['metadata'], 0)
                self.assertEqual(len(list((root / 'reads').glob('*.json'))), 3)
                self.assertEqual(reader.authority['metadata']['document']['bytes'], cap)

    def test_actual_receiving_validator_refused_without_any_launch_or_write(self):
        proof = json.loads(DIAGNOSTIC.read_bytes())
        self.assertEqual(proof['runner_sha256'], self.proof['runner_sha256'])
        self.assertEqual(proof['source'], self.proof['source'])
        self.assertEqual((proof['status'], proof['reason']), ('VALIDATOR_REFUSED', 'delegated_read_cap'))
        self.assertEqual(proof['last_attempted_charge']['category'], 'interpreter')
        self.assertGreater(proof['metadata_attempted_bytes'], proof['metadata_cap_bytes'])
        self.assertTrue(proof['both_authorization_inputs_synthetic_in_memory_only'])
        self.assertTrue(proof['ledger_writes_in_memory_only'])
        for field in ('adapter_attempted_bytes', 'receiving_writes', 'scanner_invocations',
                      'gpu_model_provider_calls', 'signals'):
            self.assertEqual(proof[field], 0)
        self.assertFalse(proof['execution_authorized'])

    def test_actual_execution_authorities_join_original_nonrefunded_ledger(self):
        request_path = HERE / 'preparation1/narrow_runner1/REQUEST.json'
        self.assertEqual(hashlib.sha256(request_path.read_bytes()).hexdigest(), self.proof['runner_request']['sha256'])
        request = json.loads(request_path.read_bytes())
        count = 0
        for allowance in request['execution_read_allowances'].values():
            entries = [*allowance['preflight'].values(), *allowance['native'].values(), allowance['model_load']]
            for entry in entries:
                raw = Path(entry['reference']['path']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['reference']['sha256'])
                self.assertEqual(json.loads(raw), entry['document'])
                self.assertEqual(entry['document']['status'], 'PRECHARGED_NO_REFUND')
                self.assertEqual(entry['document']['scope_sha256'], common.SCOPE_SHA)
                count += 1
        self.assertEqual(count, 10)

    def test_exact_six_call_binding_and_no_reset_authorization_refusals(self):
        go = {field: self.public[field] for field in (
            'executions', 'source', 'runner_sha256', 'cpu_gate', 'runner_cpu_gate')}
        go.update(status='MAIN_R176_EXECUTION_GO', no_reset=True, call_cap=72, token_cap=36864,
            process_cap=24, physical_slots=[0, 1], absolute_end_unix=common.END, active_seconds_max=5400,
            gpu_slot_seconds_max=10800, provider_calls=0, baseline_new_calls=0)
        review = dict(go, status='APPROVE', independent=True, reviewer='SYNTHETIC_CPU_FIXTURE_ONLY')
        def validate(document, independent):
            runner.validate_go(document, self.public['executions'][0], self.public['source'],
                self.public['runner_sha256'], self.public['cpu_gate'], self.public['runner_cpu_gate'], independent)
        validate(go, review)
        for change in ({'no_reset': False}, {'baseline_new_calls': 3}, {'provider_calls': 1},
                       {'executions': []}, {'runner_sha256': 'wrong'}, {'cpu_gate': {}}):
            with self.assertRaises(ValueError):
                validate(dict(go, **change), review)
        changed = deepcopy(review)
        changed['executions'] = list(reversed(changed['executions']))
        with self.assertRaises(ValueError):
            validate(go, changed)


if __name__ == '__main__':
    unittest.main()
