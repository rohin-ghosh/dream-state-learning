import ast
from pathlib import Path
import unittest

from gpu.orch_r144_target_patch import (
    NEW_RECEIPT, OLD_ENCODING, OLD_RECEIPT, patch_source, without_sleep,
)


class FrozenPatchTests(unittest.TestCase):
    def setUp(self):
        self.current = Path('gpu/orch_r125_continual_native.py').read_text()
        self.original = self.current.replace(NEW_RECEIPT, OLD_RECEIPT).replace(
            '        child_exposures, anchor_exposures = 0, 0\n',
            OLD_ENCODING + '        child_exposures, anchor_exposures = 0, 0\n')

    def test_reproduces_tested_patch_exactly(self):
        self.assertEqual(patch_source(self.original), self.current)

    def test_other_frozen_functions_are_preserved_byte_for_byte(self):
        variant = self.original + '\nFROZEN_VARIANT_SENTINEL = 123\n'
        self.assertEqual(patch_source(variant), self.current + '\nFROZEN_VARIANT_SENTINEL = 123\n')
        self.assertEqual(without_sleep(ast.parse(variant)),
                         without_sleep(ast.parse(patch_source(variant))))

    def test_rejects_repeated_or_unknown_blocks(self):
        for source in (self.current, self.original.replace(OLD_ENCODING, ''),
                       self.original + OLD_RECEIPT):
            with self.subTest(source_length=len(source)), self.assertRaises(ValueError):
                patch_source(source)

    def test_rejects_matching_text_outside_sleep(self):
        source = self.original.replace('    def sleep(self,', '    def unrelated(self,')
        with self.assertRaisesRegex(ValueError, 'exact_native_sleep_required'):
            patch_source(source)


if __name__ == '__main__':
    unittest.main()
