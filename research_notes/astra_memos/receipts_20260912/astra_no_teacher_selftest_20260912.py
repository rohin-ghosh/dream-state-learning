"""CPU tests: synthetic endpoints and tampered copies of captured artifacts."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path('/tmp/astra_no_teacher_analyze_20260912.py')
spec = importlib.util.spec_from_file_location('anchor_analysis', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BASE = Path('/tmp/astra_no_teacher_terminal_20260912')
ROOT = BASE / 'astra_P1_no_teacher_20260912_attempt1'
PREP = BASE / 'astra_P1_no_teacher_preparation_20260912_attempt1'
STATIC_ROOT = module.STATIC / 'astra_P1_static_competency_20260912_attempt1'
STATIC_PREP = module.STATIC / 'astra_P1_static_competency_preparation_20260912_attempt1'
STATIC_ANALYSIS = Path('/tmp/astra_static_competency_terminal_analysis_20260912.json')
CORRECT = '1 2 3 4 ; 3 4 1 2 ; 2 1 4 3 ; 4 3 2 1'


class EndpointTests(unittest.TestCase):
    def test_no_action(self):
        result = module.endpoint([])
        self.assertFalse(result['first_action_available'])
        self.assertEqual(result['first_action_score'], 0)

    def test_invalid_first_correct_later_and_order(self):
        actions = [dict(kind='act', action='bad', score=.2), dict(kind='act', action=CORRECT, score=1)]
        result = module.endpoint(actions)
        self.assertEqual((result['first_action_score'], result['native_best'], result['n_actions']), (0, 1, 2))
        self.assertEqual(module.endpoint(list(reversed(actions)))['first_action_solved'], 1)

    def test_inline_prediction_not_repaired(self):
        result = module.endpoint([dict(kind='act', action=CORRECT + ' ; PREDICT: 1', score=.3)])
        self.assertEqual(result['first_action_score'], 0)
        self.assertEqual(result['native_best'], .3)

    def test_trailing_semicolon(self):
        self.assertEqual(module.endpoint([dict(kind='act', action=CORRECT + ' ;', score=1)])['first_action_solved'], 1)

    def test_nonfinite_score(self):
        with self.assertRaisesRegex(ValueError, 'native score'):
            module.endpoint([dict(kind='act', action=CORRECT, score=float('nan'))])

    def test_native_bootstrap_strip(self):
        prompt = '=== YOU ===\nbootstrap\n\n\nteacher\n=== STATE ===\nquestion\n'
        self.assertEqual(module.without_teacher(prompt, 'teacher'), '=== YOU ===\nbootstrap\n=== STATE ===\nquestion\n')

    def test_wrong_givens(self):
        givens = ((2, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))
        result = module.constraints(CORRECT, givens, module.parse_board(CORRECT))
        self.assertEqual(len(result['given_violations']), 1)
        self.assertFalse(any(result['duplicate_groups'].values()))


class CapsuleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='astra_no_teacher_selftest_20260912_')
        self.home = Path(self.temporary.name)
        self.root, self.prep = self.home / 'run', self.home / 'prep'
        shutil.copytree(ROOT, self.root)
        shutil.copytree(PREP, self.prep)
        for path in self.home.rglob('*'):
            path.chmod(0o755 if path.is_dir() else 0o644)

    def tearDown(self):
        self.temporary.cleanup()

    def analyze(self):
        return module.analyze(self.root, self.prep, STATIC_ROOT, STATIC_PREP, STATIC_ANALYSIS)

    def write(self, path, value):
        path.write_text(json.dumps(value))

    def reseal(self):
        folder = self.root / 'no_teacher'
        self.write(folder / 'artifact_hashes.json', dict(files={path.name: module.digest(path.read_bytes())
                   for path in folder.iterdir() if path.name != 'artifact_hashes.json'}))

    def test_actual_capture(self):
        result = self.analyze()
        self.assertEqual(len(result['exact_prompt_joins']), 32)
        self.assertEqual([result['arms'][mode]['solves'] for mode in ('process', 'sham', 'no_teacher')], [1, 1, 0])

    def test_missing_file(self):
        (self.root / 'no_teacher/output_00.json').unlink()
        with self.assertRaisesRegex(ValueError, 'inventory file set'):
            self.analyze()

    def test_unsealed_tamper(self):
        path = self.root / 'no_teacher/output_00.json'
        path.write_text(path.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, 'inventory hash'):
            self.analyze()

    def test_episode_mismatch(self):
        path = self.root / 'no_teacher/output_00.json'
        output = module.read(path)
        output['episode_id'] = module.IDS[1]
        self.write(path, output)
        self.reseal()
        with self.assertRaisesRegex(ValueError, 'episode/request mismatch'):
            self.analyze()

    def test_raw_output_mismatch(self):
        path = self.root / 'no_teacher/output_00.json'
        output = module.read(path)
        output['text'] += '\nACT: ' + CORRECT
        output['output_sha256'] = module.digest(output['text'].encode())
        self.write(path, output)
        self.reseal()
        with self.assertRaisesRegex(ValueError, 'raw output/thought binding'):
            self.analyze()

    def test_act_order_mismatch(self):
        path = self.root / 'no_teacher/episode_00.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows.insert(0, dict(kind='act', episode_id=module.IDS[0], action=CORRECT, score=1))
        path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n')
        self.reseal()
        with self.assertRaisesRegex(ValueError, 'raw ACT ordering'):
            self.analyze()

    def test_seed_mismatch(self):
        path = self.root / 'no_teacher/request_00.json'
        request = module.read(path)
        request['seed'] += 1
        self.write(path, request)
        self.reseal()
        with self.assertRaisesRegex(ValueError, 'request/preflight mismatch'):
            self.analyze()

    def test_cleanup_pid_mismatch(self):
        path = self.root / 'no_teacher.cleanup.json'
        cleanup = module.read(path)
        cleanup['pid'] += 1
        self.write(path, cleanup)
        with self.assertRaisesRegex(ValueError, 'cleanup ownership'):
            self.analyze()

    def test_no_completion(self):
        (self.root / 'COMPLETED.json').unlink()
        with self.assertRaises(FileNotFoundError):
            self.analyze()

    def test_frozen_row_mismatch(self):
        altered = module.read(STATIC_ANALYSIS)
        altered['arms']['process']['episodes'][0]['first_action_score'] = .99
        path = self.home / 'changed_static.json'
        self.write(path, altered)
        with self.assertRaisesRegex(ValueError, 'frozen per-episode row changed'):
            module.analyze(self.root, self.prep, STATIC_ROOT, STATIC_PREP, path)

    def test_output_exclusive(self):
        path = self.home / 'exists.json'
        path.write_text('preserve')
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--root', '/nonexistent',
                                 '--preparation', '/nonexistent', '--output-new', str(path)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('output already exists', result.stderr)
        self.assertEqual(path.read_text(), 'preserve')


if __name__ == '__main__':
    unittest.main(verbosity=2)
