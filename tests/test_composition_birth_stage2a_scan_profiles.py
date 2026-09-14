"""Explicit semantic capacity propagates through source-bound scan APIs."""

import unittest

from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_scan_inputs as source
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_birth import synthetic_bindings


class SourceScanProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bindings = synthetic_bindings(0)
        cls.case = birth.build_birth_pair(
            world="p00", role_tokens=cls.bindings,
            display_master=b"synthetic-source-profile-test",
        ).cases[0]
        cls.pair = targets.serialize_birth_case(cls.case, role_tokens=cls.bindings)[0]
        cls.raw = canonical_json({"oracle": ["PRIVATEVALUEUNEXPOSED"] * 5000})

    def test_arm_profile_is_explicit_and_receipted(self):
        arguments = dict(role_tokens=self.bindings, semantic_bytes=self.raw,
                         future_identifiers=(), registered_routes=())
        with self.assertRaisesRegex(ValueError, "leaf_bound"):
            source.scan_birth_arm(self.pair.closed, self.case, **arguments)
        report = source.scan_birth_arm(self.pair.closed, self.case,
                                       semantic_profile="birth_full_v1", **arguments)
        self.assertEqual(report.semantic_profile, "birth_full_v1")
        self.assertFalse(report.supplied_projection_clear)
        self.assertTrue(any(hit.value == b"576" for hit in report.scan_report.issues))
        self.assertFalse(report.inventory_completeness_verified)
        self.assertFalse(any(report.science_gates.values()))

    def test_pair_preserves_distinct_inventory_profiles(self):
        large = source.ScanInventory(self.raw, (), (), "birth_full_v1")
        small = source.ScanInventory(canonical_json({}), (), ())
        report = source.scan_birth_pair(self.pair, self.case, role_tokens=self.bindings,
                                       closed_inventory=large, atom_inventory=small)
        self.assertEqual(report.closed.semantic_profile, "birth_full_v1")
        self.assertEqual(report.atom_local.semantic_profile, "legacy")
        self.assertFalse(report.closed.supplied_projection_clear)
        self.assertTrue(report.atom_local.supplied_projection_clear)

    def test_profile_preserves_findings_and_rejects_unknown_name(self):
        inventory = source.ScanInventory(canonical_json({"target": self.pair.closed.unit.target_bytes.decode("ascii")}),
                                         (), (), "birth_full_v1")
        report = source.scan_birth_pair(self.pair, self.case, role_tokens=self.bindings,
                                       closed_inventory=inventory, atom_inventory=inventory)
        legacy = source.scan_birth_pair(
            self.pair, self.case, role_tokens=self.bindings,
            closed_inventory=source.ScanInventory(inventory.semantic_bytes, (), ()),
            atom_inventory=source.ScanInventory(inventory.semantic_bytes, (), ()),
        )
        self.assertEqual(report.closed.scan_report, legacy.closed.scan_report)
        self.assertEqual(report.atom_local.scan_report, legacy.atom_local.scan_report)
        self.assertEqual(report.closed.semantic_profile, "birth_full_v1")
        self.assertFalse(report.closed.inventory_completeness_verified)
        with self.assertRaisesRegex(ValueError, "semantic_profile"):
            source.scan_birth_pair(self.pair, self.case, role_tokens=self.bindings,
                                   closed_inventory=source.ScanInventory(b"{}", (), (), "unknown"),
                                   atom_inventory=inventory)


if __name__ == "__main__":
    unittest.main()
