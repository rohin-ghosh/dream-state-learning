import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import node4_parent as subject


class ParentBriefTests(unittest.TestCase):
    def test_only_exact_existing_cpu_parent_is_eligible(self):
        arguments = ['/usr/bin/python3', '-B', str(subject.PARENTS / 'r210_parent.py'), 'serve', '--physical', '3']
        self.assertEqual(subject.checked_argv(arguments, 3), arguments)
        for bad in (arguments[:-1] + ['7'], ['python3', 'native.py', 'serve', '--physical', '3']):
            with self.assertRaises(ValueError):
                subject.checked_argv(bad, 3)

    def test_unparented_reserved_and_p7_are_untouched(self):
        for physical in (0, 1, 4, 7):
            with self.assertRaises(ValueError):
                subject.prepare(physical, 'reading')

    def test_any_unfinished_source_blocks_cpu_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            turn = root / 'turns/parent_1'
            turn.mkdir(parents=True)
            (turn / 'SOURCE.json').write_text('{}')
            self.assertEqual(subject.pending_attempts(root), [str(turn)])
            (turn / 'RESULT.json').write_text('{}')
            self.assertEqual(subject.pending_attempts(root), [])

    def test_config_change_is_bound_and_preserves_old_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parents = root / 'parents'
            prior = parents / 'r210_parent3'
            prior.mkdir(parents=True)
            programme = prior / 'PROGRAMME.txt'
            programme.write_text('Existing object')
            config = dict(programme_path=str(programme), programme_sha256=subject.sha(programme),
                          cadence_responses=2, r175_arm='B', source_root='unchanged')
            (prior / 'CONFIG.json').write_text(json.dumps(config))
            worker = root / 'worker'
            worker.mkdir()
            with patch.object(subject, 'HERE', worker), patch.object(subject, 'PARENTS', parents):
                changed = subject.read(subject.prepare(3, 'Test passage'))
                self.assertEqual(subject.read(prior / 'CONFIG.json'), config)
                self.assertEqual(programme.read_text(), 'Existing object')
                self.assertEqual({key for key in changed if changed[key] != config[key]},
                                 {'programme_path', 'programme_sha256'})
                self.assertEqual(subject.sha(changed['programme_path']), changed['programme_sha256'])
                self.assertIn('Test passage', Path(changed['programme_path']).read_text())


if __name__ == '__main__':
    unittest.main()
