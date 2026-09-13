import argparse
import importlib.util
from pathlib import Path
import sys
import unittest


parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
args = parser.parse_args()
suite = unittest.TestSuite()
for name in ('test_astra_birth_conditional_run_20260913', 'test_astra_launch_birth_component_20260912'):
    spec = importlib.util.spec_from_file_location(name, Path('/tmp') / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if hasattr(module, 'SOURCE'):
        module.SOURCE = args.source
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
