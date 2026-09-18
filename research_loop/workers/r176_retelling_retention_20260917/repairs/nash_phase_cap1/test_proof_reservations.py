import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import proof_reservations as proof


class ProofReservationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.ledger = self.root / 'ledger'
        self.document = dict(scope_sha256=proof.common.SCOPE_SHA, purpose=proof.PURPOSE,
            execution_authorized=False, adapter_bytes_per_proof=proof.ADAPTER_BYTES, max_proofs=4,
            execution_sha256s=['a' * 64, 'b' * 64])
        self.authority = proof.common.write(self.root / 'authority.json', self.document)
        clock = patch.object(proof.time, 'time', return_value=1789660000)
        clock.start()
        self.addCleanup(clock.stop)

    def test_four_exact_size_proofs_preserve_reservations(self):
        for checksum in self.document['execution_sha256s']:
            for phase in ('preflight', 'native'):
                entry = proof.reserve(self.ledger, self.authority, checksum, phase)
                self.assertEqual(entry['document']['bytes'], 80798775)
        rows = list((self.ledger / 'reservations').glob('*.json'))
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(json.loads(path.read_bytes())['bytes'] for path in rows), 323195100)

    def test_duplicate_operation_does_not_refund_or_retry(self):
        entry = proof.reserve(self.ledger, self.authority, 'a' * 64, 'preflight')
        original = Path(entry['reference']['path']).read_bytes()
        with self.assertRaisesRegex(ValueError, 'attempt_consumed_no_retry'):
            proof.reserve(self.ledger, self.authority, 'a' * 64, 'preflight')
        self.assertEqual(Path(entry['reference']['path']).read_bytes(), original)

    def test_other_execution_or_phase_rejected(self):
        for checksum, phase in [('c' * 64, 'native'), ('a' * 64, 'start')]:
            with self.assertRaisesRegex(ValueError, 'exact_fixed_pair_four_CPU_proofs'):
                proof.reserve(self.ledger, self.authority, checksum, phase)

    def test_authority_hash_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact_supplemental_authority'):
            proof.reserve(self.ledger, dict(self.authority, sha256='0' * 64), 'a' * 64, 'native')

    def seed(self, amount, life='C2', repair=False):
        entry = dict(status='PRECHARGED_NO_REFUND', scope_sha256=proof.common.SCOPE_SHA,
            operation='existing_preserved_charge', kind='adapter', bytes=amount, life_id=life)
        if repair:
            entry['repair_authority'] = dict(path='preserved')
        proof.common.write(self.ledger / 'reservations/seed.json', entry)

    def test_actual_global_cap(self):
        self.seed(16 * proof.common.GIB, life='C5')
        with self.assertRaisesRegex(ValueError, 'global_resource_cap'):
            proof.reserve(self.ledger, self.authority, 'a' * 64, 'native')

    def test_actual_per_life_cap(self):
        self.seed(8 * proof.common.GIB)
        with self.assertRaisesRegex(ValueError, 'per_life_kind_cap'):
            proof.reserve(self.ledger, self.authority, 'a' * 64, 'native')

    def test_preserves_full_nominal_pass_plan_even_if_unspent(self):
        self.seed(512 * proof.common.MIB, repair=True)
        with self.assertRaisesRegex(ValueError, 'preserve_all_nominal_twelve_checkpoint_passes'):
            proof.reserve(self.ledger, self.authority, 'a' * 64, 'native')

    def test_exact_reads_fit_alongside_failed_capture_repair(self):
        self.seed(128 * proof.common.MIB, repair=True)
        for checksum in self.document['execution_sha256s']:
            for phase in ('preflight', 'native'):
                proof.reserve(self.ledger, self.authority, checksum, phase)
        self.assertEqual(len(list((self.ledger / 'reservations').glob('*.json'))), 5)


if __name__ == '__main__':
    unittest.main()
