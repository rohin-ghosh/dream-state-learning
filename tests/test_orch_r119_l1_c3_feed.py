import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gpu import orch_r119_l1_c3_feed as candidate
from gpu.orch_r109_l1_feed_append import validate_extension


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        self.registration = dict(root=self.root.name, node='ovx', source_registration_id=candidate.REGISTRATION,
                                 row_bindings={'source_state_sha256':'15460', 'split':'TRAIN'})
        self.review = dict(path='gpu1/segment0000/gpu1/CALL_000001.json')
        self.row = dict(source_state_sha256='15460', split='TRAIN', teacher_or_l2=False)

    def test_bound_registration_uses_unchanged_semantic_gate(self):
        with patch.object(candidate.feed.experience, 'review_gate') as gate:
            candidate.source_gate(self.registration, self.review, self.row, {})
            gate.assert_called_once_with(self.review, self.row, {})

    def test_no_wrong_seed_held_or_teacher(self):
        for change in ({'source_state_sha256':'8932'}, {'split':'DEV'}, {'teacher_or_l2':True}):
            with patch.object(candidate.feed.experience, 'review_gate'):
                with self.assertRaises(ValueError):
                    candidate.source_gate(self.registration, self.review, dict(self.row, **change), {})

    def test_no_escape_or_unregistered_path(self):
        for path in ('../escape', '/tmp/other'):
            with self.assertRaises(ValueError):
                candidate.source_gate(self.registration, dict(self.review,path=path), self.row, {})

    def test_no_automatic_pass_for_missing_review(self):
        with self.assertRaises(KeyError):
            candidate.source_gate(self.registration, self.review, self.row, {})

    def test_three_distinct_limit(self):
        candidate.bounded_reviews([dict(source_task_id=str(index)) for index in range(3)])
        candidate.bounded_reviews([])
        for rows in ([dict(source_task_id=str(index)) for index in range(4)],
                     [dict(source_task_id='repeat')]*2):
            with self.assertRaises(ValueError):candidate.bounded_reviews(rows)

    def test_extension_cannot_replace_anchors_or_prior(self):
        row = dict(target_sha256='old',source_task_id='old')
        new = dict(target_sha256='new',source_task_id='new',source_label=candidate.feed.experience.SOURCE_LABEL,
                   split='TRAIN',teacher_or_l2=False,target_actor='CHILD',parent_text_masked=True)
        encoded = dict(eligible=[1],anchor=[42],prior=[9])
        good = dict(encoded,eligible=[1,2])
        validate_extension([row],[row,new],encoded,good)
        for altered in (dict(good,anchor=[43]),dict(good,prior=[]),dict(good,eligible=[3,2])):
            with self.assertRaises(ValueError):validate_extension([row],[row,new],encoded,altered)


if __name__ == '__main__':unittest.main()
