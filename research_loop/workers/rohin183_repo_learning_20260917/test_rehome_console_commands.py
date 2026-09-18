import shlex
import unittest

from research_loop.workers.rohin183_repo_learning_20260917 import rehome_console_commands as console


class ConsoleTests(unittest.TestCase):
    def ready(self, original=4):
        folder = console.BASE / ('receiving' + str(original))
        return dict(raw_root=str(folder / 'root'), source_root=str(folder / 'preserved' / ('physical' + str(original)) / 'source'),
            source_pins={'gpu/orch_r127_pilot_console.py': console.PUBLISH_SOURCE_SHA,
                'gpu/orch_r125_stream_console.py': console.FOLLOW_SOURCE_SHA})

    def argv(self, command):
        outer = shlex.split(command)
        self.assertEqual(outer[:2], ['bash', 'gpu/ovx_ssh.sh'])
        return shlex.split(outer[2])

    def test_publish_uses_attributed_writer_and_explicit_rohin(self):
        command = self.argv(console.commands(4, self.ready())['rohin_publish_command'])
        self.assertIn('gpu.orch_r127_pilot_console', command)
        self.assertNotIn('gpu.orch_r125_stream_console', command)
        self.assertEqual(command[command.index('--speaker') + 1], 'Rohin')
        self.assertIn('--text', command)

    def test_follow_is_read_only(self):
        command = self.argv(console.commands(4, self.ready())['follow_command'])
        self.assertIn('gpu.orch_r125_stream_console', command)
        self.assertIn('--follow', command)
        self.assertNotIn('--text', command)

    def test_text_is_one_literal_remote_argument(self):
        text = "Rohin's text; $(not_a_command)\nsecond line"
        command = self.argv(console.commands(4, self.ready(), text)['rohin_publish_command'])
        self.assertEqual(command[command.index('--text') + 1], text)

    def test_all_three_actual_roots(self):
        for original in (1, 4, 7):
            ready = self.ready(original)
            command = self.argv(console.commands(original, ready)['rohin_publish_command'])
            self.assertEqual(command[command.index('--root') + 1], ready['raw_root'])

    def test_old_root_or_unverified_module_rejected(self):
        ready = self.ready()
        ready['raw_root'] = '/old/node3/root'
        with self.assertRaises(ValueError):
            console.commands(4, ready)
        ready = self.ready()
        ready['source_pins']['gpu/orch_r127_pilot_console.py'] = 'unknown'
        with self.assertRaises(ValueError):
            console.commands(4, ready)


if __name__ == '__main__':
    unittest.main()
