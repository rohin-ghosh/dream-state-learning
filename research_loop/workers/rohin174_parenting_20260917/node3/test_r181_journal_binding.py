from pathlib import Path
import unittest
from unittest.mock import patch

import r181_journal_boundary as binding


class JournalBindingTests(unittest.TestCase):
    def test_adds_journal_without_replacing_native_or_other_mounts(self):
        original = ['--property=BindPaths=/actual:/logical',
            '--property=BindReadOnlyPaths=/owned/new_native.py:/source/gpu/orch_r125_continual_native.py',
            '/usr/bin/env', str(Path(binding.original.__file__).resolve()), 'wait']
        with patch.object(binding, 'original_command', return_value=list(original)), \
             patch.object(binding.original, 'read', return_value=dict(source_root='/source')):
            result = binding.command(Path('/owned'), 'wait')
        self.assertEqual(result[0], original[0])
        self.assertEqual(result[1], original[1] + ' /owned/new_journal.py:/source/gpu/orch_r125_stream_journal.py')
        self.assertIn(str(Path(binding.__file__).resolve()), result)
        self.assertNotIn(str(Path(binding.original.__file__).resolve()), result)


if __name__ == '__main__':
    unittest.main()
