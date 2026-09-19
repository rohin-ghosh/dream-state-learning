from copy import deepcopy
import hashlib
import unittest

from organism_v6 import orch_r194_code_target_filter as review
from organism_v6.orch_r225_content_target_filter import POLICY
from organism_v6.orch_r213_content_target_filter import POLICY as LEGACY
import test_orch_r205_reading_policy as fixture


class CaptionBirthTests(unittest.TestCase):
    def test_first_new_child_rows_tag_v2_inside_committed(self):
        case = fixture.ReadingPolicyTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        old_driver = case.driver(['An earlier own explanation.'],
            dict(case.config, learn_review_filter=review.REVIEW_POLICY, content_target_filter=LEGACY))
        old_driver.generate_stage('THINK')
        old = deepcopy(case.stream.rows)
        config = dict(case.config, learn_review_filter=review.REVIEW_POLICY, content_target_filter=POLICY,
            prose_target_filter='R209_ENGLISH_PROSE_TARGET_QUARANTINE_V1',
            fabricated_speaker_filter='R220_FABRICATED_HUMAN_TURNS_V1')
        driver = case.driver(['I can examine the windmill scene.',
            "Even the windmill knows this meeting's ridiculous.", 'My own bounded review.'], config)
        for stage in ('THINK', 'ACT', 'LEARN'):
            driver.generate_stage(stage)
            committed = case.records('COMMITTED')[-1]['state']['state']['rows']
            self.assertEqual(committed, case.stream.rows)
            self.assertEqual(committed[:len(old)], old)
            self.assertEqual(committed[-1]['content_target_filter'], POLICY)
            self.assertEqual(committed[-1]['actor'], 'child')
            self.assertFalse(committed[-1]['prefix_loss'])

    def test_v2_static_assurance_all_excluded_with_raw_and_old_rows_preserved(self):
        texts = ['I will assume that that is adequate for now and proceed to act.',
            '```python\nprint("The resulting abstract meets the necessary criteria.")\n```']
        rows = [dict(actor='child', split='TRAIN', prefix_loss=False, target_loss=True,
            source_sha256=hashlib.sha256(text.encode()).hexdigest(), segment=index,
            target=text, content_target_filter=POLICY) for index, text in enumerate(texts)]
        old = [dict(rows[0], content_target_filter=LEGACY)]
        before = deepcopy((rows, old))
        kept, kept_old, proof = review.filter_learn_review_targets(rows, old, review.REVIEW_POLICY)
        self.assertEqual(kept, [])
        self.assertIs(kept_old, old)
        self.assertEqual((rows, old), before)
        self.assertEqual({item['source_sha256'] for item in proof['excluded']},
            {row['source_sha256'] for row in rows})
        self.assertFalse(proof['raw_modified'])


if __name__ == '__main__':
    unittest.main()
