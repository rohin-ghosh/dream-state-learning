import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path('/data/home/rohing/dream-state')
HELPER = Path('/tmp/astra_born_process_readout_20260912.py')
CODE = '''
import importlib.util,json,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('portable_readout',sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
diagnostic,corpus,legacy,driver=module._helpers()
print(json.dumps(dict(root=str(module.SOURCE_ROOT),diagnostic=diagnostic.__file__,
    corpus=corpus.__file__,pins=module.REQUIRED_SOURCE_PINS)))
'''


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(SOURCE/'organism_v6', self.root/'organism_v6',
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

    def run_helper(self, root, extra=''):
        environment = dict(os.environ, ASTRA_SOURCE_ROOT=str(root),
            PYTHONPATH=str(self.root), PYTHONDONTWRITEBYTECODE='1')
        return subprocess.run([sys.executable,'-B','-c',extra+CODE,str(HELPER)],
            cwd=self.root,env=environment,capture_output=True,text=True,timeout=40)

    def test_alternate_source_before_import_uses_real_matching_snapshot(self):
        result = self.run_helper(self.root)
        self.assertEqual(result.returncode,0,result.stderr)
        reported = json.loads(result.stdout)
        self.assertEqual(reported['root'],str(self.root))
        self.assertEqual(Path(reported['diagnostic']).resolve().parents[1],self.root)
        self.assertEqual(Path(reported['corpus']).resolve().parents[1],self.root)
        self.assertIn(str(self.root/'organism_v6/birth_conditional_corpus.py'),reported['pins'])
        self.assertNotIn(str(SOURCE/'organism_v6/birth_conditional_corpus.py'),reported['pins'])

    def test_relative_source_is_rejected(self):
        result = self.run_helper(Path('relative'))
        self.assertNotEqual(result.returncode,0)
        self.assertIn('must be absolute',result.stderr)

    def test_changed_snapshot_bytes_remain_rejected(self):
        with (self.root/'organism_v6/birth_conditional_corpus.py').open('a') as target:
            target.write('\n')
        result = self.run_helper(self.root)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('inspected helper bytes changed',result.stderr)

    def test_cached_wrong_snapshot_remains_rejected(self):
        preload = f'import sys\nsys.path.insert(0,{str(SOURCE)!r})\nimport organism_v6.rulegame_parenting_diagnostic\n'
        result = self.run_helper(self.root,preload)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('wrong imported source root',result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
