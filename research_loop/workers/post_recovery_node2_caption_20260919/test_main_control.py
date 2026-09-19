"""The remote -c bootstrap must not need a fabricated local source pathname."""

from pathlib import Path
import unittest


class BootstrapTests(unittest.TestCase):
    def test_remote_definition_loads_without_file_or_actions(self):
        source = Path(__file__).with_name('main_control.py').read_text()
        namespace = {'__name__': 'remote_definition_only'}
        exec(compile(source, '<remote-control>', 'exec'), namespace)
        self.assertIsNone(namespace['HERE'])
        self.assertIsNone(namespace['REPO'])
        self.assertTrue(callable(namespace['remote_prepare']))


if __name__ == '__main__':
    unittest.main()
