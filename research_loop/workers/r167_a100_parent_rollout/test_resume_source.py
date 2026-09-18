import ast
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('r167_a100_resume', Path(__file__).with_name('resume_source.py'))
resume = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(resume)

FIXTURE = '''def serve(config_path, repository, output, once=False):
    config = validate(json.loads(config_path.read_text()))
    write(output/'STARTED.json', dict(branch=config['branch']))
    last_count = 0
    calls = 0
    while time.time() < config['hard_end_unix']:
        state = snapshot(repository, config)
        if state['response_count'] < max(1, last_count + config['cadence_responses']):
            return
        last_count = state['response_count']
        calls += 1
        publish(repository, config, 'fixture')
        return
'''


def binding():
    return dict(schema=resume.SCHEMA, root='/localhome/local-rohing/orch_fixture/run1',
                branch='a100_6_classroom_creative', programme='creative_writing',
                old_output='/tmp/original_parent', started_sha256='a' * 64,
                reserved_response_count=117)


class ResumeSourceTests(unittest.TestCase):
    def test_rejects_unknown_original_source(self):
        with self.assertRaisesRegex(ValueError, 'exact_original'):
            resume.patch_source(FIXTURE, binding())

    def test_only_startup_changes_and_future_loop_identical(self):
        with patch.object(resume, 'SOURCE_SHA256', hashlib.sha256(FIXTURE.encode()).hexdigest()):
            result = resume.patch_source(FIXTURE, binding())
        before, after = ast.parse(FIXTURE).body[0], ast.parse(result).body[0]
        self.assertEqual(ast.dump(before.body[-1]), ast.dump(after.body[-1]))
        self.assertIn('    last_count = 117\n', result)
        self.assertIn('    calls = 0\n', result)
        self.assertLess(result.index('bound_parent_resume'), result.index("write(output/'STARTED.json'"))

    def test_config_retains_policy_transport_recipe_and_wall(self):
        data = binding()
        candidate = dict(root=data['root'], branch=data['branch'], programme=data['programme'],
                         node='a100', cadence_responses=2, hard_end_unix=1234,
                         principles_path='/tmp/new_principles', principles_sha256='b' * 64,
                         source_root='/tmp/original_source')
        old = deepcopy(candidate)
        result = resume.resume_config(candidate, data)
        self.assertEqual(candidate, old)
        self.assertEqual(set(result) - set(old), {'r167_parent_resume'})
        self.assertEqual({key: result[key] for key in old}, old)

    def test_wrong_scope_cursor_and_reapplication_refuse(self):
        for changes in ({'branch': 'C1'}, {'reserved_response_count': -1},
                        {'reserved_response_count': True}, {'old_output': '../relative'},
                        {'started_sha256': 'bad'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                resume.validate_binding(dict(binding(), **changes))

    def test_checks_fail_before_writing_or_publication(self):
        data = binding()
        candidate = dict(root=data['root'], branch=data['branch'], programme=data['programme'],
                         node='a100', hard_end_unix=99999999999, cadence_responses=2)
        with patch.object(resume, 'SOURCE_SHA256', hashlib.sha256(FIXTURE.encode()).hexdigest()):
            result = resume.patch_source(FIXTURE, data)
        writes, publications = [], []
        namespace = dict(validate=lambda value: value, json=SimpleNamespace(loads=lambda unused: candidate),
                         require=resume.require, Path=Path, sha=lambda unused: 'a' * 64,
                         write=lambda *args: writes.append(args),
                         publish=lambda *args: publications.append(args),
                         snapshot=lambda *args: dict(response_count=117), time=SimpleNamespace(time=lambda: 0))
        exec(compile(result, '<synthetic-parent>', 'exec'), namespace)
        config_path = SimpleNamespace(read_text=lambda: 'fixture')
        with self.assertRaisesRegex(ValueError, 'bound_parent_resume'):
            namespace['serve'](config_path, '/tmp', Path('/tmp/new_parent'))
        self.assertEqual(writes, [])
        self.assertEqual(publications, [])
        candidate['r167_parent_resume'] = data
        namespace['serve'](config_path, '/tmp', Path('/tmp/new_parent'))
        self.assertEqual(len(writes), 1)
        self.assertEqual(publications, [])
        namespace['snapshot'] = lambda *args: dict(response_count=119)
        namespace['serve'](config_path, '/tmp', Path('/tmp/new_parent'))
        self.assertEqual(len(publications), 1)


if __name__ == '__main__':
    unittest.main()
