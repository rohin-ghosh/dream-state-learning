"""Exact-source boundary composition; fixtures do not authorize native work."""

from dataclasses import replace
from hashlib import sha256
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a_boundary as boundary
from organism_v6 import composition_birth_stage2a_future_inputs as futures
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_route_inputs as routes
from organism_v6 import composition_birth_stage2a_source_inputs as sources
from organism_v6 import composition_birth_stage2a_targets as targets
from tests.test_composition_birth_stage2a_birth import DISPLAY_MASTER, synthetic_bindings


class BoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roles = synthetic_bindings(2)
        cls.verifier = boundary.BirthBoundaryVerifier(
            world="p02", role_tokens=cls.roles, display_master=DISPLAY_MASTER,
        )
        cls.record = cls.verifier.records[2]
        cls.result = cls.verifier.verify(cls.record)

    def test_complete_values_are_retained_separately_from_boundary(self):
        result = self.result
        document = primitives.parse_canonical_json(result.boundary_bytes)
        self.assertEqual(document["schema_version"], boundary.SCHEMA_VERSION)
        self.assertEqual(result.shared_custody_sha256, sha256(self.verifier.shared_bytes).hexdigest())
        for name, raw in (("candidate_inventory", result.candidate_inventory_bytes),
                          ("retained_inventory", result.retained_inventory_bytes),
                          ("route_basis", result.route_basis_bytes),
                          ("private_static_basis", result.private_static_basis_bytes),
                          ("private_record_basis", result.private_record_basis_bytes),
                          ("typed_occurrence_receipts", result.typed_receipts_bytes)):
            self.assertEqual(document[name]["sha256"], sha256(raw).hexdigest())
            self.assertEqual(document[name]["bytes"], len(raw))
            self.assertTrue(primitives.parse_canonical_json(raw))
        self.assertGreater(len(self.verifier.shared_bytes), len(result.boundary_bytes))
        self.assertEqual(document["native_template_tokenization"], "NOT_YET_BOUND")
        self.assertFalse(result.native_chat_bytes_verified)
        self.assertFalse(result.independent_allocation_authorized)
        self.assertFalse(any(result.science_gates.values()))

    def test_exact_candidate_messages_projection_and_receipt_pass(self):
        result = self.verifier.verify(
            self.record, public_messages=self.record.prefix,
            public_projection=self.result.binding.projection_bytes,
            candidate_boundary_bytes=self.result.boundary_bytes,
        )
        self.assertEqual(result.boundary_bytes, self.result.boundary_bytes)
        self.assertTrue(result.source_content_clear)

    def test_public_changes_reject_before_lexical_scan(self):
        prefix = self.result.binding.projection_bytes
        candidates = (prefix + b"\nACK", prefix[:-1], b"X" + prefix[1:],
                      prefix[1:] + prefix[:1], prefix + self.record.unit.target_bytes)
        with patch.object(boundary.typed_scan, "scan_typed_birth") as scan:
            for candidate in candidates:
                with self.subTest(candidate_sha256=sha256(candidate).hexdigest()):
                    with self.assertRaisesRegex(boundary.BoundaryError, "exact_public_projection"):
                        self.verifier.verify(self.record, public_projection=candidate)
            scan.assert_not_called()

    def test_message_roles_and_changed_middle_cannot_borrow_hashes(self):
        prefix = self.record.prefix
        changed = prefix[:2] + (replace(prefix[2], role="user"),) + prefix[3:]
        with self.assertRaisesRegex(boundary.BoundaryError, "exact_public_messages"):
            self.verifier.verify(self.record, public_messages=changed)
        changed = prefix[:2] + (replace(prefix[2], content=prefix[2].content + " X"),) + prefix[3:]
        with self.assertRaises(boundary.BoundaryError):
            self.verifier.verify(self.record, public_messages=changed)
        forged = replace(self.record, prefix=changed)
        with self.assertRaises(ValueError):
            self.verifier.verify(forged)

    def test_caller_inventories_spans_and_flags_are_not_an_api(self):
        for name in ("fields", "future_identifiers", "route_inputs", "passed", "binding"):
            with self.subTest(name=name), self.assertRaises(TypeError):
                self.verifier.verify(self.record, **{name: True})

    def test_foreign_arm_and_changed_receipt_fail(self):
        twin = self.verifier.records[3]
        self.assertEqual(twin.unit, self.record.unit)
        with self.assertRaisesRegex(boundary.BoundaryError, "exact_boundary_receipt"):
            self.verifier.verify(twin, candidate_boundary_bytes=self.result.boundary_bytes)
        document = primitives.parse_canonical_json(self.result.boundary_bytes)
        document["core_sha256"] = "0" * 64
        with self.assertRaisesRegex(boundary.BoundaryError, "exact_boundary_receipt"):
            self.verifier.verify(self.record, candidate_boundary_bytes=primitives.canonical_json(document))

    def test_cached_composition_does_not_reencode_full_case_per_boundary(self):
        with patch.object(sources, "_digest_value", side_effect=AssertionError("full-case encoding forbidden")):
            for record in self.verifier.records:
                self.assertTrue(self.verifier.verify(record).source_content_clear)

    def test_extracted_inventory_helpers_preserve_existing_public_results(self):
        source = self.verifier._custody.source_for(self.record)
        actual_future = futures._derive_from_source(source, self.result.binding)
        expected_future = futures.derive_birth_future_inputs(
            case=source.case, record=self.record, role_tokens=self.roles, display_master=DISPLAY_MASTER,
        )
        self.assertEqual(actual_future, expected_future)
        actual_route = routes._derive_from_source(source)
        expected_route = routes.derive_birth_route_inputs(
            case=source.case, record=self.record, role_tokens=self.roles, display_master=DISPLAY_MASTER,
        )
        self.assertEqual(actual_route, expected_route)

    def test_returned_transition_cannot_poison_trusted_cached_basis(self):
        result = self.verifier.verify(self.record)
        port = next(iter(result.route_inputs.transitions))
        edge = result.route_inputs.transitions[port]
        original = edge.actual
        original_bytes = result.route_basis_bytes
        object.__setattr__(edge, "actual", "M2AN_AAAAAAAAAAAA")
        subsequent = self.verifier.verify(self.record)
        self.assertEqual(subsequent.route_inputs.transitions[port].actual, original)
        self.assertEqual(subsequent.route_basis_bytes, original_bytes)
        self.assertTrue(subsequent.source_content_clear)


if __name__ == "__main__":
    unittest.main()
