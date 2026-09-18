from pathlib import Path
import tempfile
import unittest

import append_r159_coverage as report


class AppendTests(unittest.TestCase):
    def test_append_preserves_existing_prefix_exactly(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'COORDINATION.md'
            original = b'# Main current top\nConcurrent status already present.\n'
            payload = b'\n## R159 metadata-only coverage\nNew bounded observation.\n'
            path.write_bytes(original)
            receipt = report.append_once(path, payload)
            self.assertEqual(path.read_bytes(), original+payload)
            self.assertEqual(receipt['start_line'], 3)
            self.assertTrue(receipt['append_only'])


if __name__ == '__main__':
    unittest.main()
