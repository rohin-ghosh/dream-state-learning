"""Exact typed pre-model refusal regression; no native execution."""

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
import preload_readmission
import r181_build


class PreloadReadmissionTests(unittest.TestCase):
    def check(self, names=(), present=(), expected='saved'):
        preload_readmission.eligibility(dict(reason='original_privileged_clear_admission', retired=True, terminated=True),
            dict(clear=False, scanner_euid=0, blocking_reasons=['process_identity_drift:2438435']),
            names, present, 'saved', expected)

    def test_exact_refusal_is_eligible(self):
        self.check()

    def test_every_dispatch_marker_blocks_replay(self):
        for name in ('LAUNCH.json', 'NATIVE.log', 'CONTAINED_COMMAND.json', 'CONTAINMENT_VERIFIED.json', 'NATIVE_EXIT.json'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'no_prior_native_dispatch'):
                self.check(names=[name])

    def test_live_owner_and_changed_boundary_block(self):
        with self.assertRaisesRegex(ValueError, 'original_owners_absent'):
            self.check(present=[123])
        with self.assertRaisesRegex(ValueError, 'same_complete_boundary'):
            self.check(expected='changed')

    def test_original_strict_supervise_and_dispatch_marker_retained(self):
        source = r181_build.operator_source('a' * 64, 'b' * 64, readmission=True)
        self.assertIn("(attempt / 'DISPATCH_ONCE').mkdir()", source)
        self.assertIn('original_privileged_clear_admission', source)
        self.assertIn("load_auxiliary('preload_readmission.py').execute", source)
        self.assertIn("'preload_readmission.py', 'READMISSION_BINDING.json'", source)


if __name__ == '__main__':
    unittest.main()
