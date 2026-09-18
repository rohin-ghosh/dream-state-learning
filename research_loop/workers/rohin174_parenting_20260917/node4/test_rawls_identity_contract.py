"""Demonstrate exact scanner identity semantics without touching any process."""

import ast
import hashlib
from pathlib import Path
import tempfile
import unittest


HOME = Path(__file__).resolve().parent
SOURCE = HOME.parents[3] / 'gpu/orch_rich_hot_a100_scan.py'
SOURCE_SHA = '9902c38ecadeaa06bc02abf184f6a04025a289868f809b63aace5148cd95575e'


class ScannerIdentityContractTests(unittest.TestCase):
    def setUp(self):
        source = SOURCE.read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), SOURCE_SHA)
        tree = ast.parse(source)
        function = next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == 'identity')
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.process = self.root / '58131'
        self.process.mkdir()
        self.boot = self.root / 'boot_id'
        self.boot.write_text('synthetic-boot\n')
        (self.process / 'cmdline').write_bytes(b'/usr/sbin/sshd\0synthetic\0')
        self.fields = ['0'] * 20
        self.fields[0] = 'S'
        self.fields[19] = '12345'
        self.write_stat()
        namespace = dict(Path=lambda name: self.boot if name == '/proc/sys/kernel/random/boot_id' else Path(name),
            sha=lambda path: hashlib.sha256(path.read_bytes()).hexdigest())
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), 'exec'), namespace)
        self.identity = namespace['identity']

    def write_stat(self):
        (self.process / 'stat').write_text('58131 (synthetic name) ' + ' '.join(self.fields))

    def test_scheduler_state_and_cpu_ticks_are_not_identity(self):
        original = self.identity(self.process)
        self.fields[0] = 'R'
        self.fields[11] = '9876'
        self.fields[12] = '5432'
        self.write_stat()
        self.assertEqual(self.identity(self.process), original)

    def test_argv_title_change_really_is_scanner_identity_drift(self):
        original = self.identity(self.process)
        (self.process / 'cmdline').write_bytes(b'/usr/sbin/sshd\0changed-title\0')
        changed = self.identity(self.process)
        self.assertNotEqual(changed['command_sha256'], original['command_sha256'])
        self.assertEqual({key: value for key, value in changed.items() if key != 'command_sha256'},
            {key: value for key, value in original.items() if key != 'command_sha256'})

    def test_reused_pid_start_ticks_remains_a_different_identity(self):
        original = self.identity(self.process)
        self.fields[19] = '67890'
        self.write_stat()
        self.assertNotEqual(self.identity(self.process), original)

    def test_boot_identity_change_remains_a_different_identity(self):
        original = self.identity(self.process)
        self.boot.write_text('different-synthetic-boot\n')
        self.assertNotEqual(self.identity(self.process), original)


if __name__ == '__main__':
    unittest.main()
