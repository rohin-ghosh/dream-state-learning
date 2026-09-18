import unittest
import types

import p3_lease_parent


class LeaseParentTests(unittest.TestCase):
    def test_historical_wall_is_projected_before_frozen_validator_runs(self):
        original = dict(hard_end_unix=1789754400, fixed_source='preserved', budget=160)
        observed = []

        def validator(candidate):
            if candidate['hard_end_unix'] <= 1789759600:
                raise ValueError('parent_wall')
            observed.append(candidate)
            return candidate

        validate = p3_lease_parent.authorized_wall_validator(validator, original)
        self.assertEqual(validate(original)['hard_end_unix'], p3_lease_parent.END_UNIX)
        self.assertEqual(original['hard_end_unix'], 1789754400)
        self.assertEqual(observed[0]['fixed_source'], 'preserved')
        self.assertEqual(observed[0]['budget'], 160)
        for changed in (dict(original, budget=161), dict(original, hard_end_unix=p3_lease_parent.END_UNIX + 1)):
            with self.assertRaises(ValueError):
                validate(changed)

    def test_current_renewed_expiry_is_still_enforced(self):
        def validator(candidate):
            if candidate['hard_end_unix'] <= p3_lease_parent.END_UNIX:
                raise ValueError('parent_wall')

        original = dict(hard_end_unix=1789754400)
        validate = p3_lease_parent.authorized_wall_validator(validator, original)
        with self.assertRaises(ValueError):
            validate(original)

    def test_only_deadline_changes_and_input_is_preserved(self):
        original = {'hard_end_unix': 1789754400, 'nested': {'budget': 160}}
        renewed = p3_lease_parent.renewed_config(original, p3_lease_parent.END_UNIX)
        self.assertEqual(renewed['nested'], original['nested'])
        self.assertIsNot(renewed['nested'], original['nested'])
        self.assertEqual(original['hard_end_unix'], 1789754400)
        self.assertEqual(renewed['hard_end_unix'], p3_lease_parent.END_UNIX)

    def test_no_shortening_or_outside_reported_lease(self):
        original = {'hard_end_unix': 1789754400}
        for deadline in (1789754400, 1789754399, p3_lease_parent.END_UNIX + 1):
            with self.assertRaises(ValueError):
                p3_lease_parent.renewed_config(original, deadline)

    def test_binding_preserves_guard_and_late_prompt_overlay(self):
        original = {'hard_end_unix': 1789754400, 'budget': 160}
        checks = []

        def check(candidate):
            self.assertEqual(candidate, original)
            checks.append(candidate)

        namespace = {}
        exec('def tick(config):\n    validate(config)\n    return prompt(config)\n', namespace)
        policy = types.SimpleNamespace(validate=check,
            prompt=lambda candidate: candidate['budget'], tick=namespace['tick'])
        renewed = p3_lease_parent.bind(policy, original)
        prior_prompt = policy.prompt
        policy.prompt = lambda candidate: ('late_overlay', prior_prompt(candidate))
        self.assertEqual(policy.tick(renewed), ('late_overlay', 160))
        self.assertEqual(len(checks), 2)
        with self.assertRaises(ValueError):
            policy.tick(dict(renewed, budget=161))


if __name__ == '__main__':
    unittest.main()
