from copy import deepcopy
import unittest

from gpu import orch_math_feedback_uptake_r118_parallel_recipe as recipe


class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.prior = dict(target_modules=['v_proj', 'q_proj', 'up_proj', 'gate_proj',
            'k_proj', 'down_proj', 'o_proj'], r=8, lora_alpha=16, lora_dropout=.05,
            base_model_name_or_path='/synthetic/base', rank_pattern={}, inference_mode=True)

    def test_actual_failure_order_only_is_equivalent_without_mutation(self):
        following = deepcopy(self.prior)
        following['target_modules'] = ['q_proj', 'k_proj', 'up_proj', 'o_proj',
            'down_proj', 'v_proj', 'gate_proj']
        saved = deepcopy((self.prior, following))
        self.assertTrue(recipe.require_same_recipe(self.prior, following)['equivalent'])
        self.assertEqual((self.prior, following), saved)

    def test_all_nonorder_changes_fail_closed(self):
        for key, changed in dict(r=16, lora_alpha=32, lora_dropout=0,
                base_model_name_or_path='/another/base', inference_mode=False,
                rank_pattern={'q_proj': 16}, target_modules=['q_proj']).items():
            with self.subTest(key=key):
                following = dict(self.prior, **{key: changed})
                with self.assertRaisesRegex(ValueError, 'unchanged_adapter_recipe'):
                    recipe.require_same_recipe(self.prior, following)

    def test_unknown_extra_key_is_not_ignored(self):
        with self.assertRaisesRegex(ValueError, 'unchanged_adapter_recipe'):
            recipe.require_same_recipe(self.prior, dict(self.prior, future_setting=True))

    def test_regex_is_not_converted_to_target_list(self):
        regex = dict(self.prior, target_modules='.*q_proj')
        self.assertTrue(recipe.require_same_recipe(regex, deepcopy(regex)))
        with self.assertRaisesRegex(ValueError, 'unchanged_adapter_recipe'):
            recipe.require_same_recipe(regex, dict(regex, target_modules=['.*q_proj']))

    def test_duplicates_empty_and_bad_types_fail(self):
        for targets in ([], ['q_proj', 'q_proj'], ['q_proj', 1], [''], None, {}, ''):
            with self.subTest(targets=targets), self.assertRaises(ValueError):
                recipe.canonical_recipe(dict(self.prior, target_modules=targets))


if __name__ == '__main__':
    unittest.main()
