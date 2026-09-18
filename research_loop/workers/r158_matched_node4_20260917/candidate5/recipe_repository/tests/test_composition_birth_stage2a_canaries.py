import base64
from hashlib import sha256
import unittest

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_canaries as source


class CanaryTests(unittest.TestCase):
    def setUp(self):
        kinds = ["node"] * 2 + ["query"] * 2 + ["port"] * 4 + ["event"] * 4
        self.roles = tuple(f"generic_canary/c{index:02d}/canary/-/target/-/{kind}"
                           for index, kind in enumerate(kinds))
        prefixes = {"node": "M2AN_", "query": "M2AQ_", "port": "M2AP_", "event": "M2AE_"}
        self.tokens = {role: prefixes[kind] + base64.b32encode(sha256(b"synthetic-canary" + role.encode()).digest()).decode()[:12]
                       for role, kind in zip(self.roles, kinds)}
        self.canaries = source.build_canaries(role_tokens=self.tokens)

    def test_exact_roster_and_target_order(self):
        self.assertEqual(source.canary_roles(), self.roles)
        self.assertEqual(tuple(canary.index for canary in self.canaries), tuple(range(16)))
        prefixes = ["READ INDEX"] * 2 + ["READ RELATION"] * 2 + ["STEP"] * 4 + ["THINK KEEP"] * 2 + ["THINK REVISE"] * 2
        expected = [prefix + " " + self.tokens[role] for prefix, role in zip(prefixes, self.roles)] + ["STOP"] * 4
        self.assertEqual([canary.target for canary in self.canaries], expected)
        self.assertEqual(len({wire.parse_action(target).operand for target in expected[:12]}), 12)

    def test_copy_prompt_exact_and_shared_system(self):
        for canary in self.canaries:
            self.assertEqual(canary.user_text, "CANARY\nCOPY EXACTLY\n" + canary.target)
            self.assertFalse(canary.user_text.endswith("\n"))
            self.assertEqual(canary.system_text, wire.SYSTEM_MESSAGE)
            self.assertTrue(source.exact_copy_match(canary, canary.target))

    def test_wrong_valid_action_is_not_correct_copy(self):
        self.assertFalse(source.exact_copy_match(self.canaries[0], self.canaries[1].target))
        for canary in self.canaries:
            for output in (canary.target + "\n", " " + canary.target, "```" + canary.target + "```", None, 1, canary.target.encode()):
                self.assertFalse(source.exact_copy_match(canary, output))

    def test_bad_roster_duplicate_sentinel_and_wrong_kind_rejected(self):
        damaged = []
        missing = dict(self.tokens)
        missing.pop(self.roles[0])
        damaged.append(missing)
        damaged.append(dict(self.tokens, extra="M2AN_BBBBBBBBBBBB"))
        for value in (self.tokens[self.roles[1]], "M2AN_AAAAAAAAAAAA", "M2AP_BBBBBBBBBBBB", "M2AN_BBBBBBBBBBB!", None):
            mapping = dict(self.tokens)
            mapping[self.roles[0]] = value
            damaged.append(mapping)
        for mapping in damaged:
            with self.assertRaises(ValueError):
                source.build_canaries(role_tokens=mapping)

    def test_symbolic_inventory_agreement_and_partial_designation(self):
        inventory = wire.enumerate_symbolic_role_inventory("generic_canary")
        self.assertEqual(set(source.canary_roles()), {role for roles in inventory.roles_by_kind.values() for role in roles})
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))


if __name__ == "__main__":
    unittest.main()
