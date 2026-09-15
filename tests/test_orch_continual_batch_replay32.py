from copy import deepcopy
import unittest

from organism_v6 import orch_continual_batch as old
from organism_v6 import orch_continual_batch_replay32 as arm
from organism_v6 import orch_continual_batch_replay_compile as compiler
from tests.test_orch_continual_batch import rows_and_reviews


class Replay32Tests(unittest.TestCase):
    def fixture(self):
        rows, old_reviews = rows_and_reviews()
        rows = rows[:32]
        reviews = [dict(deepcopy(old_reviews[0]), target_sha256=row['target_sha256']) for row in arm.sample(rows)]
        return rows, reviews

    def test32_does_not_change64(self):
        rows, reviews = self.fixture()
        self.assertEqual(old.BATCH_SIZE, 64)
        with self.assertRaises(ValueError):
            old.sample(rows)
        self.assertEqual(len(arm.sample(rows)), 12)
        self.assertEqual(arm.sample(rows), arm.sample(list(reversed(rows))))

    def test_accept_truthful12_and20(self):
        rows, reviews = self.fixture()
        decision, exported = arm.adjudicate(rows, reviews)
        self.assertTrue(decision['accepted'])
        self.assertEqual(sum(row['semantic_status'] == 'PASS' for row in exported), 12)
        self.assertEqual(sum(row['semantic_status'] == 'UNREVIEWED' for row in exported), 20)

    def test_ten_pass_allowed_sample_fail_excluded(self):
        rows, reviews = self.fixture()
        reviews[0]['status'] = reviews[1]['status'] = 'FAIL'
        decision, exported = arm.adjudicate(rows, reviews)
        self.assertTrue(decision['accepted'])
        self.assertEqual(len(exported), 30)

    def test_hard_grounding_defect_still_blocks(self):
        rows, reviews = self.fixture()
        reviews[0].update(status='FAIL', grounded_operations=False)
        self.assertFalse(arm.adjudicate(rows, reviews)[0]['accepted'])

    def test_first32_uses_native_order_not_semantics(self):
        rows, unused = rows_and_reviews()
        rows = rows[:39]
        for index, row in enumerate(rows):
            row['provenance'].update(native_finished_unix=index, source_native_path=f'/native/{index}')
        self.assertEqual(arm.first32(list(reversed(rows))), rows[:32])

    def test_reject_wrong_population(self):
        rows, unused = self.fixture()
        with self.assertRaises(ValueError):
            arm.first32(rows)
        with self.assertRaises(ValueError):
            arm.sample(rows[:-1])

    def test_pending_laplace_window_is_not_invented_or_mixed(self):
        result = compiler.handoff([], dict(source_state_sha256=arm.STATE, lineage={},
            fit_scope='PENDING_LAPLACE_ISOLATED_PAIRED_WINDOW'), '/native/ROWS.json', 'a' * 64)
        self.assertFalse(result['training_application_allowed'])
        self.assertFalse(result['paired_fit_executed'])
        self.assertIsNone(result['paired_window_id'])
