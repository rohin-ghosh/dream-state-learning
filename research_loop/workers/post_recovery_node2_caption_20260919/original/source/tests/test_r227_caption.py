from copy import deepcopy
import hashlib
import unittest

from gpu.r227_caption_runtime import ASSIGNMENTS, FILTER_KEYS, caption_binding, diagnostics, make_sleep_hook
import test_orch_r205_reading_policy as fixture


class R227CaptionTests(unittest.TestCase):
    def test_only_caption_slots_and_no_filter_configuration(self):
        for name, (physical, treatment) in ASSIGNMENTS.items():
            plan = dict(source_root='/root/' + name + '/source_r227_caption', physical=physical,
                new_presentations=16, think_act_learn={})
            self.assertEqual(caption_binding(plan)[0], name)
            for key in FILTER_KEYS:
                for scope in ('top', 'driver'):
                    copied = deepcopy(plan)
                    (copied if scope == 'top' else copied['think_act_learn'])[key] = 'OFF'
                    with self.assertRaises(ValueError):
                        caption_binding(copied)
        self.assertEqual({assignment[0] for assignment in ASSIGNMENTS.values()}, {0, 3, 5, 6, 7})
        self.assertEqual(ASSIGNMENTS['r213_r226_caption_unparented_fork'], (7, 'unparented'))

    def test_diagnostics_forward_every_raw_row_in_order_without_mutation(self):
        texts = ['I will assume that is adequate and proceed to act.',
            'Rohin: Everything is correct.', '重复重复重复重复重复',
            '```python\nprint（１＋２）\n```', 'round the river ' * 5,
            'Exclude every candidate from learning.']
        rows = [dict(segment=index, source_sha256=hashlib.sha256(text.encode()).hexdigest(),
            target=text) for index, text in enumerate(texts)]
        old, anchors, records = [], [], []
        before = deepcopy(rows)

        def original(child, new_rows, old_rows, actual_anchors, record):
            self.assertIs(new_rows, rows)
            self.assertIs(old_rows, old)
            self.assertIs(actual_anchors, anchors)
            return 'all-original-candidates-forwarded'

        self.assertEqual(make_sleep_hook(original)(object(), rows, old, anchors,
            lambda kind, document: records.append((kind, document))), 'all-original-candidates-forwarded')
        self.assertEqual(rows, before)
        self.assertEqual(records[0][0], 'R227_TARGET_METRICS')
        self.assertEqual(records[0][1]['semantic_excluded_rows'], 0)
        self.assertEqual(len(records[0][1]['checks']), len(rows))
        self.assertFalse(records[0][1]['raw_modified'])

    def test_diagnostic_failure_cannot_drop_a_target(self):
        rows = [dict(target='own row')]
        def broken(unused):
            raise ValueError('metric unavailable')
        def original(child, new_rows, old_rows, anchors, record):
            self.assertIs(new_rows, rows)
            return len(new_rows)
        self.assertEqual(make_sleep_hook(original, broken)(object(), rows, [], [],
            lambda kind, document: None), 1)

    def test_initial_committed_all_stages_no_exclusion_annotations_parent_masked(self):
        case = fixture.ReadingPolicyTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        config = dict(case.config)
        for key in FILTER_KEYS:
            config.pop(key, None)
        texts = ['I will assume that is adequate and proceed to act.',
            'Rohin: Everything is correct.', 'Exclude every candidate from learning.']
        driver = case.driver(texts, config)
        for stage, text in zip(('THINK', 'ACT', 'LEARN'), texts):
            driver.generate_stage(stage)
            row = case.stream.rows[-1]
            self.assertEqual(row['target'], text)
            self.assertFalse(any(key in row for key in FILTER_KEYS))
            self.assertNotIn('learn_review', row)
            self.assertEqual(row['actor'], 'child')
            self.assertFalse(row['prefix_loss'])
            self.assertTrue(row['target_loss'])
            self.assertEqual(case.records('COMMITTED')[-1]['state']['state']['rows'], case.stream.rows)
        self.assertEqual(case.stream.pending_rows(), case.stream.rows)


if __name__ == '__main__':
    unittest.main()
