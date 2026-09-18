"""Nonoverlapping independent cap-repair integration regressions."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


HERE = Path(__file__).resolve().parent
WORKER = HERE.parent
REPAIR = WORKER / 'repairs/nash_phase_cap1'
sys.path.insert(0, str(WORKER))
import preparation_io as common


class PhaseCapReviewTests(unittest.TestCase):
    def setUp(self):
        self.observation = json.loads((HERE / 'RECEIVING_OBSERVATION.json').read_bytes())

    def test_repaired_candidate_and_request_match_actual_receiving_bytes(self):
        for name, field in (('PUBLIC_METADATA.json', 'candidate_public'), ('REQUEST.json', 'candidate_request')):
            raw = (REPAIR / 'attempt2' / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), self.observation[field]['sha256'])
        self.assertTrue(all(self.observation['checks'].values()))

    def test_each_actual_phase_proof_request_and_persisted_receipt_is_bound(self):
        counts = {'native': 0, 'preflight': 0}
        for proof in self.observation['proofs']:
            operation = Path(proof['receipt']['path']).parent.name
            for suffix, field in (('.PUBLIC_METADATA.json', 'receipt'), ('.REQUEST.json', 'request')):
                raw = (REPAIR / 'actual_proof1' / (operation + suffix)).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), proof[field]['sha256'])
            self.assertEqual(proof['rows'], 1309)
            self.assertEqual(proof['charged_bytes'], {'adapter': 80798775, 'metadata': 25618085, 'discovery': 0})
            self.assertGreater(proof['metadata_headroom_bytes'], 0)
            counts[proof['phase']] += 1
        self.assertEqual(counts, {'native': 2, 'preflight': 2})

    def test_all_new_and_superseded_authorities_remain_exact_nonrefunded_files(self):
        documents = [json.loads((REPAIR / attempt / 'REQUEST.json').read_bytes()) for attempt in ('attempt1', 'attempt2')]
        original = json.loads((WORKER / 'preparation1/narrow_runner1/REQUEST.json').read_bytes())
        entries = []
        for document in documents:
            for phases in document['new_metadata_allowances'].values():
                entries.extend(phases.values())
        for phases in original['execution_read_allowances'].values():
            entries.extend(phases['preflight'].values())
            entries.extend(phases['native'].values())
            entries.append(phases['model_load'])
        proof_manifest = json.loads((REPAIR / 'actual_proof1/PRE_IO_MANIFEST.json').read_bytes())
        for request in proof_manifest['requests']:
            entries.extend(request['proof_allowances'].values())
            entries.extend([request['bootstrap'], request['storage']])
        for entry in entries:
            raw = Path(entry['reference']['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['reference']['sha256'])
            self.assertEqual(json.loads(raw), entry['document'])
            self.assertEqual(entry['document']['status'], 'PRECHARGED_NO_REFUND')
        self.assertEqual(len(entries), 34)

    def test_actual_global_and_per_life_caps_preserve_all_nominal_passes(self):
        rows = [json.loads(path.read_bytes()) for path in (WORKER / 'preparation1/global_ledger/reservations').glob('*.json')]
        for kind, cap in (('metadata', 2 * common.GIB), ('adapter', 16 * common.GIB), ('storage', 2 * common.GIB)):
            self.assertLessEqual(sum(row['bytes'] for row in rows if row['kind'] == kind), cap)
        for life in ('C2', 'C5'):
            for kind, cap in (('metadata', common.GIB), ('adapter', 8 * common.GIB)):
                self.assertLessEqual(sum(row['bytes'] for row in rows if row['life_id'] == life and row['kind'] == kind), cap)
        repairs = [row for row in rows if row['kind'] == 'adapter' and
            (row.get('repair_authority') or row.get('supplemental_repair_authority'))]
        self.assertLessEqual(15 * common.GIB + sum(row['bytes'] for row in repairs), 16 * common.GIB)
        self.assertLessEqual(7680 * common.MIB + sum(row['bytes'] for row in repairs if row['life_id'] == 'C2'), 8 * common.GIB)

    def pressure(self, mode):
        completed = subprocess.run([sys.executable, '-B', str(HERE / 'callback_pressure.py'), mode],
            capture_output=True, text=True, check=True, timeout=60,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''))
        return json.loads(completed.stdout)

    def test_unchanged_native_callback_fits_full_token_envelope_and_extra_source_pass(self):
        result = self.pressure('repaired')
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['callbacks'], 1546)
        self.assertEqual(result['config_bytes'], 4899)
        expected = result['actual_validator_cost_seed'] + result['synthetic_extra_entire_source_pass_bytes']
        expected += result['callbacks'] * result['config_bytes']
        self.assertEqual(result['metadata_charged_bytes'], expected)
        self.assertEqual(result['headroom_bytes'], 128261)
        self.assertTrue(result['real_Reader_charge_and_audit_hook'])
        self.assertEqual(result['model_gpu_provider_calls'], 0)

    def test_old_phase_cap_still_refuses_before_any_callback(self):
        result = self.pressure('old')
        self.assertEqual((result['status'], result['reason']), ('REFUSED', 'delegated_read_cap'))
        self.assertEqual(result['callbacks'], 0)


if __name__ == '__main__':
    unittest.main()
