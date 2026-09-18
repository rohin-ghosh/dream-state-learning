"""R227 behavioral seams; combined source closure is checked by receiving preflight."""

from pathlib import Path
import runpy
import unittest


namespace = runpy.run_path(str(Path(__file__).with_name('r227_receiving_tests.py')),
    run_name='receiving_behavioral_seams')
case = namespace['ReceivingPolicyTests']
names = unittest.defaultTestLoader.getTestCaseNames(case)
names.remove('test_only_declared_source_functions_changed')
suite = unittest.TestSuite(case(name) for name in names)
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
