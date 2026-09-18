import unittest
import types

import p3_lease_parent


class LeaseParentTests(unittest.TestCase):
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
