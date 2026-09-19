import ast
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

from gpu import orch_r144_target_patch as targets
from gpu import orch_r145_node3_capacity_recovery as capacity
from gpu.orch_r144_sleep_targets import encode_sleep_targets
from tests.test_orch_r144_sleep_targets import Tokenizer, row


FROZEN = Path(__file__).resolve().parents[1] / 'research_loop/workers/r145_admission_integration_20260916t1611z/CAPACITY_FROZEN_NATIVE.py'
FROZEN_SHA = '1bff3dc6ee92fb188b335dbb56809bdff62e54383c00ef3d0aca92d6c5a593d8'


class CapacityTargetCompositionTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(capacity.file_sha(FROZEN), FROZEN_SHA)
        self.source = FROZEN.read_text()
        self.prospective = targets.patch_source(self.source)

    def test_only_sleep_changes_and_capacity_forward_remains_exact(self):
        self.assertEqual(targets.without_sleep(ast.parse(self.source)), targets.without_sleep(ast.parse(self.prospective)))
        self.assertEqual(self.prospective.count(capacity.NEW_FORWARD), 1)
        self.assertEqual(self.prospective.count("if label.startswith('ANCHOR:'):"), 2)
        self.assertEqual(self.prospective.count('r145_capacity.prepare_sleep('), 1)
        self.assertLess(self.prospective.index('new_rows, old_rows, encoded, rejected_targets ='),
                        self.prospective.index('r145_capacity.prepare_sleep('))
        self.assertNotIn(targets.OLD_ENCODING, self.prospective)

    def test_unknown_or_already_combined_source_is_rejected(self):
        with self.assertRaises(ValueError):
            targets.patch_source(self.prospective)
        with self.assertRaises(ValueError):
            targets.patch_source(self.source.replace(targets.OLD_RECEIPT, ''))

    def test_exact_encoder_schedule_and_raw_rows_preserved(self):
        spec = importlib.util.spec_from_file_location('r145_capacity_native_fixture', FROZEN)
        native = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(native)
        new = [row('new-ok'), row('new-special', [97, 1, 2])]
        old = [row('old-special', [1, 97, 2]), row('old-ok')]
        before = deepcopy((new, old))
        accepted_new, accepted_old, encoded, rejected = encode_sleep_targets(new, old, Tokenizer(), 100, native.encode_own)
        self.assertEqual((new, old), before)
        self.assertEqual([item['source_sha256'] for item in accepted_new], ['new-ok'])
        self.assertEqual([item['source_sha256'] for item in accepted_old], ['old-ok'])
        self.assertEqual(native.presentation_schedule(accepted_new, accepted_old),
                         [('NEW', new[0])] * 16 + [('REHEARSAL', old[1])])
        self.assertEqual([item['source_sha256'] for item in rejected], ['new-special', 'old-special'])
        for sample in encoded.values():
            window = capacity.child_window(sample)
            self.assertEqual(window['labels'], (-100,) + sample.target_ids)


if __name__ == '__main__':
    unittest.main()
