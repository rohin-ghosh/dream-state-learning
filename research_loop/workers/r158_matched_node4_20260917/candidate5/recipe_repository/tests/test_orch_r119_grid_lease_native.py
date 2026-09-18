import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu import orch_r115_grid_native as native
from gpu import orch_r119_grid_lease_budget as budget


class NativeLeaseBudgetTests(unittest.TestCase):
    def test_real_reservation_crosses_old_caps_without_reset(self):
        rows = [dict(kind=kind, number=number) for kind, cap in budget.HISTORICAL.items()
                for number in range(1, cap + 1)]
        raw = b''.join((json.dumps(row) + '\n').encode() for row in rows)
        now = time.time()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'LEDGER.jsonl'
            path.write_bytes(raw)
            document = budget.authorize(root=root, ledger_bytes=raw, rows=rows,
                config_sha256='a' * 64, lease_end=now + 86400, hard_end=now + 64800, now=now)
            with patch.object(native, 'END', now + 64800):
                with self.assertRaisesRegex(ValueError, 'fixed_call_ceiling'):
                    native.reserve(root, 'NATIVE', {})
                with patch.object(native, 'MAX_NATIVE', document['prospective_caps']['NATIVE']), \
                     patch.object(native, 'MAX_PARENT', document['prospective_caps']['PARENT']):
                    self.assertEqual(native.reserve(root, 'NATIVE', dict(split='TRAIN')), 1859)
                    self.assertEqual(native.reserve(root, 'PARENT', dict(phase='experience')), 299)
            self.assertEqual(path.read_bytes()[:len(raw)], raw)
            actual = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(budget.counts(actual), {'NATIVE': 1859, 'PARENT': 299})

    def test_expanded_cap_never_waives_hard_wall(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(native, 'END', 0), patch.object(native, 'MAX_NATIVE', 9999999):
                with self.assertRaisesRegex(ValueError, 'hard_end'):
                    native.reserve(root, 'NATIVE', dict(split='TRAIN'))
            self.assertEqual((root / 'LEDGER.jsonl').read_bytes(), b'')


if __name__ == '__main__':
    unittest.main()
