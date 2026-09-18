from copy import deepcopy
import unittest

from r227_plan import proposed_plan, POLICY


class ProspectivePolicyPlanTests(unittest.TestCase):
    def test_only_prospective_selectors_source_and_stale_wall_authorization_change(self):
        current = dict(root='/same/life', source_root='/old/source', hard_end_unix=1790359200,
            new_presentations=16, anchor_lambda=.25, learning_rate=3e-5,
            code_target_filter='old', learn_review_filter='old-review',
            authorized_wall_extension=dict(previous_stream_sha256='old-checkpoint'),
            think_act_learn=dict(language_target_policy='old-Han-exception',
                content_target_filter='old-content', code_policy='R194_FIRST_CODE_BLOCK_NFKC_V1',
                cpu_gate_sha256='exact-cpu', judgment_policy='R198_JUDGMENT_FIRST_V1'))
        original = deepcopy(current)
        result, disposition = proposed_plan(current, '/own/proposed/source')
        self.assertEqual(current, original)
        self.assertEqual(result['learn_row_policy'], POLICY)
        self.assertEqual(result['think_act_learn']['learn_row_policy'], POLICY)
        for key in ['root','hard_end_unix','new_presentations','anchor_lambda','learning_rate']:
            self.assertEqual(result[key], current[key])
        for key in ['code_policy','cpu_gate_sha256','judgment_policy']:
            self.assertEqual(result['think_act_learn'][key], current['think_act_learn'][key])
        self.assertNotIn('authorized_wall_extension', result)
        self.assertNotIn('language_target_policy', result['think_act_learn'])
        self.assertEqual(disposition['source_status'], 'RECEIVING_OVERLAY_NOT_BUILT_OR_LOADED')

    def test_current_source_or_ambiguous_destination_rejected(self):
        current = dict(source_root='/old/source', think_act_learn={})
        for proposed in ['/old/source', '/old/../old/source', 'relative/source']:
            with self.subTest(proposed=proposed), self.assertRaises(ValueError):
                proposed_plan(current, proposed)

    def test_both_config_levels_strip_all_selectors_not_execution_policy(self):
        from r227_plan import FIELDS
        config = {key: 'legacy-selector' for key in FIELDS}
        current = dict(config, source_root='/old/source', root='/same/life',
            think_act_learn=dict(config, code_policy='R194_FIRST_CODE_BLOCK_NFKC_V1'))
        result, disposition = proposed_plan(current, '/future/source')
        for label, candidate in [('plan', result), ('think_act_learn', result['think_act_learn'])]:
            self.assertTrue(set(FIELDS).isdisjoint(candidate))
            self.assertEqual(candidate['learn_row_policy'], POLICY)
            self.assertEqual(set(disposition['removed_future_selectors'][label]), set(FIELDS))
        self.assertEqual(result['think_act_learn']['code_policy'], 'R194_FIRST_CODE_BLOCK_NFKC_V1')


if __name__ == '__main__':
    unittest.main()
