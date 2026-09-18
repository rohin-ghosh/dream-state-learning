from pathlib import Path
import hashlib
import json
import unittest


ROOT = Path(__file__).resolve().parent


class EpochTests(unittest.TestCase):
    def test_old_six_remain_unchanged_and_one_added_paragraph(self):
        old = (ROOT.parent / 'BIRTH_PROMPT.txt').read_text().split('\n\n')
        new = (ROOT / 'UPDATED_BIRTH_PROMPT.txt').read_text().split('\n\n')
        self.assertEqual(len(old), 6)
        self.assertEqual(len(new), 7)
        self.assertEqual(new[:4] + new[5:], old)
        self.assertEqual(new[4], (ROOT / 'EXPLORATION_PARAGRAPH.txt').read_text())

    def test_epoch_source_hashes(self):
        source = json.loads((ROOT / 'EPOCH_SOURCE.json').read_bytes())
        for key, path in (('original_birth_sha256', ROOT.parent / 'BIRTH_PROMPT.txt'),
                ('new_birth_sha256', ROOT / 'UPDATED_BIRTH_PROMPT.txt'),
                ('added_paragraph_sha256', ROOT / 'EXPLORATION_PARAGRAPH.txt'),
                ('source_document_sha256', ROOT / 'BIRTH_SPEC_R232.md')):
            self.assertEqual(source[key], hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
