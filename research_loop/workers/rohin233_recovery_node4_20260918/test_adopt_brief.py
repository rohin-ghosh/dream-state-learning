import unittest

import adopt_brief


class BriefTests(unittest.TestCase):
    def before(self):
        return dict(policy='R230_DIVERSE_CURRICULUM_THROUGH_P7_OVERSEER_V1',
            standing_brief=['preserve curriculum'], native_restart=False)

    def packet(self):
        return dict(policy='R233_ENGLISH_REGROUNDING_NO_EXCLUSIONS_V1',
            native_policy_changes=[], signals=[], direct_Astra7_messages=False,
            current_route_status='EXPIRED_BINDING_NO_CURRENT_RECEIVER_VERIFIED',
            next_turn_requested_text='Read the actual passage. Reply in English.')

    def test_preserves_existing_config_and_does_not_mutate_input(self):
        before = self.before()
        result = adopt_brief.merge(before, self.packet())
        self.assertNotIn(adopt_brief.KEY, before)
        self.assertEqual({key: value for key, value in result.items() if key != adopt_brief.KEY}, before)

    def test_exclusion_or_direct_child_change_rejected(self):
        for key, value in (('native_policy_changes', ['English-only']), ('signals', ['restart']),
            ('direct_Astra7_messages', True)):
            packet = self.packet()
            packet[key] = value
            with self.assertRaises(ValueError):
                adopt_brief.merge(self.before(), packet)

    def test_false_live_route_claim_rejected(self):
        packet = self.packet()
        packet['current_route_status'] = 'LIVE'
        with self.assertRaises(ValueError):
            adopt_brief.merge(self.before(), packet)

    def test_parent_word_budget(self):
        packet = self.packet()
        packet['next_turn_requested_text'] = 'word ' * 161
        with self.assertRaises(ValueError):
            adopt_brief.merge(self.before(), packet)


if __name__ == '__main__':
    unittest.main()
