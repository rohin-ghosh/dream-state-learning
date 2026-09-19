import base64
import unittest

import stage_prefix_observer as staging


class StagePrefixObserverTests(unittest.TestCase):
    def test_exact_bytes_and_file_set(self):
        raw = b'value = 1\n'
        entries = {'module.py': {'base64': base64.b64encode(raw).decode(), 'sha256': staging.sha(raw)}}
        self.assertEqual(staging.validated_payloads(entries, {'module.py'}), {'module.py': raw})
        with self.assertRaisesRegex(ValueError, 'exact_CPU_observer_file_set'):
            staging.validated_payloads(entries, {'different.py'})
        entries['module.py']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'bound_CPU_source_bytes'):
            staging.validated_payloads(entries, {'module.py'})

    def test_invalid_python_never_staged(self):
        raw = b'def invalid syntax'
        entries = {'module.py': {'base64': base64.b64encode(raw).decode(), 'sha256': staging.sha(raw)}}
        with self.assertRaises(SyntaxError):
            staging.validated_payloads(entries, {'module.py'})


if __name__ == '__main__':
    unittest.main()
