from copy import deepcopy
import unittest

from tools.courier.swarm import make_prompts


class MetaParentFieldsTests(unittest.TestCase):
    def setUp(self):
        self.fields = deepcopy(make_prompts.DEFAULT_FIELDS['F2'])
        self.template = make_prompts.fixed_parent_template()

    def test_optional_guidance_preserves_exact_v4_template(self):
        original = make_prompts.render(self.fields, self.template)
        updated = make_prompts.apply_head_update(self.fields, {'NEXT_GUIDANCE': 'Notice what changed.'}, self.template)
        self.assertEqual(make_prompts.render(updated, self.template), original)
        self.assertTrue(make_prompts.verify_binding(original, self.template))
        self.assertNotIn('NEXT_GUIDANCE', self.fields)

    def test_no_meta_reply_preserves_current_fields(self):
        self.assertEqual(make_prompts.apply_head_update(self.fields, {}, self.template), self.fields)

    def test_rejects_fixed_field_edit(self):
        for name in ('GAME', 'NUDGING'):
            with self.subTest(name=name), self.assertRaises(AssertionError):
                make_prompts.apply_head_update(self.fields, {name: 'changed'}, self.template)

    def test_reflection_budget_remains_integer_and_bounded(self):
        for budget in (True, '1024', 0, 8193):
            with self.subTest(budget=budget), self.assertRaises(AssertionError):
                make_prompts.apply_head_update(self.fields, {'REFLECTION': {'mode': 'short', 'max_new_tokens': budget}}, self.template)

    def test_guidance_limit_is_utf8_bytes(self):
        accepted = 'é' * 512
        self.assertEqual(make_prompts.apply_head_update(self.fields, {'NEXT_GUIDANCE': accepted}, self.template)['NEXT_GUIDANCE'], accepted)
        with self.assertRaises(AssertionError):
            make_prompts.apply_head_update(self.fields, {'NEXT_GUIDANCE': accepted + 'é'}, self.template)

    def test_rejects_nontext_guidance(self):
        for guidance in (None, [], {}):
            with self.subTest(guidance=guidance), self.assertRaises(AssertionError):
                make_prompts.apply_head_update(self.fields, {'NEXT_GUIDANCE': guidance}, self.template)


if __name__ == '__main__':
    unittest.main()
