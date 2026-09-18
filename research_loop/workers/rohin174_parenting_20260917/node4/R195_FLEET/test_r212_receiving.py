import copy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[4]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HistoricalProofTests(unittest.TestCase):
    def setUp(self):
        self.current = load('current_prose', REPO / 'organism_v6/orch_r203_prose_target_filter.py')
        self.legacy = load('legacy_prose', OWN / 'caption_r212_client/organism_v6/r212_legacy_prose.py')
        self.shim = load('replay_shim', OWN / 'caption_r212_client/gpu/r212_prose_replay.py')
        self.original = self.current.prose_exclusions
        package = types.ModuleType('organism_v6')
        package.orch_r203_prose_target_filter = self.current
        package.r212_legacy_prose = self.legacy
        self.modules = patch.dict(sys.modules, {'organism_v6': package})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.shim.activate()

    def rows(self, policy):
        return [dict(prose_target_filter=policy, target='My own prose contains a 中文 quotation.',
            source_sha256='a' * 64, segment=1)]

    def test_exact_historical_proof_and_unchanged_rows(self):
        rows = self.rows(self.legacy.POLICY)
        before = copy.deepcopy(rows)
        self.assertEqual(self.current.prose_exclusions(rows), self.legacy.prose_exclusions(rows))
        self.assertEqual(rows, before)

    def test_new_policy_script_filter_remains_identical(self):
        rows = self.rows(self.current.POLICY)
        self.assertEqual(self.current.prose_exclusions(rows), self.original(rows))
        self.assertTrue(self.current.prose_exclusions(rows)['excluded'])

    def test_mixed_and_unannotated_cohorts_unchanged(self):
        for rows in ([], [{}], self.rows(self.legacy.POLICY) + self.rows(self.current.POLICY)):
            self.assertEqual(self.current.prose_exclusions(rows), self.original(rows))

    def test_unknown_policy_still_rejected(self):
        with self.assertRaisesRegex(ValueError, 'known_prose_target_filter_policy'):
            self.current.prose_exclusions(self.rows('UNKNOWN'))

    def test_exact_legacy_source_required(self):
        self.shim.LEGACY_SHA = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_original_R203_proof_source'):
            self.shim.activate()


if __name__ == '__main__':
    unittest.main()
