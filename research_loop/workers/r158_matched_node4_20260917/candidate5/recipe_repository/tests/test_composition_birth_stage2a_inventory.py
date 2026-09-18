"""Full-object source composition retains failures; no native qualification."""

from dataclasses import replace
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a_inventory as inventory
from organism_v6 import composition_birth_stage2a_metadata_inputs as metadata
from organism_v6 import composition_birth_stage2a_scanner as scanner
from tests.test_composition_birth_stage2a_future_inputs import arguments


class BirthInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arguments = arguments(2)
        cls.report = inventory.scan_birth_inventory(**cls.arguments)

    def test_complete_object_and_future_basis_are_joined(self):
        private = self.report.metadata_inputs
        scan = self.report.content_scan
        self.assertEqual(scan.semantic_sha256, private.metadata_sha256)
        self.assertEqual(scan.semantic_profile, "birth_full_v1")
        self.assertEqual(scan.future_identifiers, tuple(sorted(private.future_inputs.future_identifiers)))
        self.assertEqual(len(private.metadata), 12)
        self.assertEqual(private.coverage_counts["event_rows"], 672)
        self.assertEqual(private.coverage_counts["route_transitions"], 672)
        self.assertGreater(private.coverage_counts["leaves"], scanner.BOUNDS["leaves"])
        self.assertEqual(scan.binding, self.report.route_scan.binding)
        self.assertEqual(private.source.provenance_bytes,
                         self.report.route_scan.source.source.provenance_bytes)
        self.assertEqual(private.route_inputs.transitions, self.report.route_scan.source.transitions)

    def test_semantic_collisions_are_not_discarded_by_route_success(self):
        self.assertTrue(self.report.route_scan.registered_grammar_clear)
        self.assertFalse(self.report.content_scan.supplied_projection_clear)
        self.assertFalse(self.report.supplied_projection_clear)
        self.assertTrue(any(hit.category == "semantic_alias"
                            for hit in self.report.content_scan.scan_report.issues))
        self.assertFalse(self.report.inventory_completeness_verified)
        self.assertFalse(self.report.native_chat_bytes_verified)
        self.assertFalse(any(self.report.science_gates.values()))

    def test_bounds_stop_before_content_scan(self):
        original = scanner.SEMANTIC_PROFILES["birth_full_v1"]
        with patch.object(scanner, "SEMANTIC_PROFILES", {
                "birth_full_v1": dict(original, leaves=1)}):
            with patch.object(inventory.source_scan, "scan_birth_arm") as content_scan:
                with self.assertRaises(metadata.MetadataBoundsError):
                    inventory.scan_birth_inventory(**self.arguments)
                content_scan.assert_not_called()

    def test_changed_record_and_caller_metadata_are_not_authority(self):
        bad_record = replace(self.arguments["record"], prefix_sha256="0" * 64)
        with self.assertRaises(ValueError):
            inventory.scan_birth_inventory(**dict(self.arguments, record=bad_record))
        with self.assertRaises(TypeError):
            inventory.scan_birth_inventory(**self.arguments, semantic_bytes=b"{}")


if __name__ == "__main__":
    unittest.main()
