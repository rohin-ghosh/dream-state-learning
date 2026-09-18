import unittest

import p3_parent_v2
import p3_validation_handoff


class ParentValidationTests(unittest.TestCase):
    def test_math_symbols_are_not_foreign_prose(self):
        for message in ('Two per scene means 2 × 3 = 6.', 'Check x ≤ 50 and x ≥ 1.',
                        'Astra: Write the caption now. “Overhead” is only a direction.'):
            p3_parent_v2.english_output(message, [])

    def test_foreign_prose_is_still_rejected(self):
        for message in ('Astra: 你写到', 'Astra: Привет', 'Astra: 日本語'):
            with self.assertRaisesRegex(ValueError, 'English_prose_script'):
                p3_parent_v2.english_output(message, [])

    def test_only_exact_evidence_quote_is_exempt(self):
        p3_parent_v2.english_output('You wrote “你写到”. Please answer in English.', ['你写到'])
        with self.assertRaises(ValueError):
            p3_parent_v2.english_output('You wrote “你写到”.', ['different evidence'])

    def test_handoff_identity_cannot_select_a_learner(self):
        manifest = {'predecessor_manifest_sha256': 'a' * 64}
        command = ['/usr/bin/python3', '-B', str(p3_parent_v2.HERE / 'p3_parent.py'),
            'serve', '--manifest-sha256', 'a' * 64]
        p3_validation_handoff.exact_parent(command, manifest)
        command[2] = 'native.py'
        with self.assertRaises(ValueError):
            p3_validation_handoff.exact_parent(command, manifest)


if __name__ == '__main__':
    unittest.main()
