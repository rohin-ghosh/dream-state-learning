import json
from pathlib import Path
import tempfile
import unittest

import handoff
import repair


class HandoffTests(unittest.TestCase):
    def test_exact_current_cpu_parent_only(self):
        command = ['/usr/bin/python3', '-B', str(repair.CURRICULUM / 'node4_parent.py'),
                   'serve', '--physical', '3']
        handoff.exact_parent(command, 3)
        for arguments, physical in ((command, 7), (command[:-1] + ['7'], 3),
                                    (command[:2] + ['native.py'] + command[3:], 3)):
            with self.assertRaises(ValueError):
                handoff.exact_parent(arguments, physical)

    def test_inflight_returns_busy_and_source_pin_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            turn = root / 'parent_0001'
            turn.mkdir()
            source = turn / 'SOURCE.json'
            source.write_text('{}')
            self.assertIsNone(handoff.reconciled(root))
            result = turn / 'RESULT.json'
            result.write_text(json.dumps(dict(source_sha256='wrong', status='SILENT')))
            with self.assertRaises(ValueError):
                handoff.reconciled(root)
            result.write_text(json.dumps(dict(source_sha256=repair.sha(source), status='PUBLICATION_UNKNOWN')))
            with self.assertRaises(ValueError):
                handoff.reconciled(root)
            result.write_text(json.dumps(dict(source_sha256=repair.sha(source), status='SILENT')))
            self.assertEqual(len(handoff.reconciled(root)), 2)


if __name__ == '__main__':
    unittest.main()
