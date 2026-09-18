from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class ConsoleWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='console wrapper ')
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        source = Path(__file__).resolve().parents[1]/'gpu'/'orch_r125_console.sh'
        self.wrapper = self.directory/source.name
        shutil.copyfile(source, self.wrapper)
        (self.directory/'ovx3_ssh.sh').write_text(
            '#!/bin/bash\nprintf "REMOTE:%s\\n" "$1"\ncat\n')

    def invoke(self, *arguments, text=''):
        return subprocess.run(['bash', str(self.wrapper), *arguments], input=text,
            capture_output=True, text=True, timeout=5, check=False)

    def test_parent_text_is_stdin_not_remote_shell_syntax(self):
        text = '$(touch SHOULD_NOT_EXIST); `printf unsafe`\n'
        result = self.invoke(text=text)
        self.assertEqual(result.returncode, 0)
        command, forwarded = result.stdout.split('\n', 1)
        self.assertNotIn('SHOULD_NOT_EXIST', command)
        self.assertEqual(forwarded, text)
        self.assertIn('gpu.orch_r125_stream_console --root ', command)
        self.assertNotIn('--follow', command)

    def test_follow_passes_only_fixed_flag(self):
        result = self.invoke('--follow')
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.rstrip().endswith('--follow'))

    def test_help_never_connects(self):
        result = self.invoke('--help')
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('REMOTE:', result.stdout)
        self.assertIn('one TRAIN parent message', result.stdout)

    def test_arbitrary_arguments_never_connect(self):
        for arguments in (('--root', '/other'), ('--follow; false',), ('--text', 'hello')):
            with self.subTest(arguments=arguments):
                result = self.invoke(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('REMOTE:', result.stdout)


if __name__ == '__main__':
    unittest.main()
