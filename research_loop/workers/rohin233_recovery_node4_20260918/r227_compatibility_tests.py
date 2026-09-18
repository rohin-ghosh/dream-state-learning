"""Focused driver seams tested with R227 enabled in a copied source tree."""

import argparse
import json
import os
from pathlib import Path
import sys
import unittest


parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--deep-work', action='store_true')
arguments = parser.parse_args()
source = arguments.source.resolve()
sys.path[:0] = [str(source), str(source / 'tests')]
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from gpu import orch_r184_think_act_learn as driver
import test_orch_r184_think_act_learn as stage_tests


if not Path(driver.__file__).resolve().is_relative_to(source):
    raise RuntimeError('exact_copied_receiving_source_required')

policy = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
original_stage_setup = stage_tests.ThinkActLearnTests.setUp


def stage_setup(self):
    original_stage_setup(self)
    self.config['learn_row_policy'] = policy


stage_tests.ThinkActLearnTests.setUp = stage_setup
names = [
    'test_r205_console_reply_precedes_each_stage_and_never_executes_its_code',
    'test_r206_pins_old_and_new_genuine_rohin_messages_without_reanswering_old_ones',
    'test_correction_ledger_preserves_raw_fault_and_restores_without_claiming_intentions',
    'test_evaluated_success_survives_compaction_sleep_restore_and_reduces_think_ceiling',
    'test_continuity_sleep_never_cuts_think_and_review_has_no_extra_generation_pass',
]
suite = unittest.TestSuite(stage_tests.ThinkActLearnTests(name) for name in names)
if arguments.deep_work:
    import test_orch_r205_reading_policy as reading_tests
    import test_orch_r222_deep_work as deep_work_tests

    original_reading_setup = reading_tests.ReadingPolicyTests.setUp

    def reading_setup(self):
        original_reading_setup(self)
        self.config['learn_row_policy'] = policy

    reading_tests.ReadingPolicyTests.setUp = reading_setup
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(deep_work_tests.DeepWorkTests))

result = unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps(dict(policy=policy, source=str(source), ran=result.testsRun,
    failures=len(result.failures), errors=len(result.errors), deep_work=arguments.deep_work,
    actual_live_adoption=False)), flush=True)
raise SystemExit(not result.wasSuccessful())
