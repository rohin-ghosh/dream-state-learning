"""Explicit semantic capacity never expands public fields or waives leaks."""

import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_scanner import scan


class SemanticProfileTests(unittest.TestCase):
    def test_legacy_bounds_remain_default_and_full_profile_is_explicit(self):
        raw = canonical_json({"oracle": list(range(5000))})
        with self.assertRaisesRegex(ValueError, "leaf_bound"):
            scanner.derive_semantic_aliases(raw)
        aliases = scanner.derive_semantic_aliases(raw, semantic_profile="birth_full_v1")
        self.assertIn(b"/oracle/4999=INT:4999", aliases)
        report = scan(b"4999", semantic_bytes=raw, semantic_profile="birth_full_v1")
        self.assertFalse(report.passed)
        self.assertTrue(any(hit.value == b"4999" for hit in report.issues))

    def test_unchanged_golden_ledger_under_both_profiles(self):
        raw = canonical_json({"factors": {"family": "A_PRIVATE_SPOKES"},
                              "oracle": {"next_role": "birth_train/p00/s/00/useful/-/query"},
                              "task": {"goal": "M2AN_ABCDEFGHIJKL"}})
        self.assertEqual(scanner.semantic_alias_ledger(raw),
                         scanner.semantic_alias_ledger(raw, semantic_profile="birth_full_v1"))

    def test_profile_does_not_expand_public_bytes_or_fields(self):
        with self.assertRaisesRegex(ValueError, "bounded_bytes"):
            scan(b"x" * (scanner.BOUNDS["bytes"] + 1), semantic_profile="birth_full_v1")
        with self.assertRaisesRegex(ValueError, "bounded_public_fields"):
            scan(b"", fields=(None,) * (scanner.BOUNDS["fields"] + 1), semantic_profile="birth_full_v1")
        with self.assertRaisesRegex(ValueError, "bounded_semantic_bytes"):
            scanner.derive_semantic_aliases(b"x" * (scanner.SEMANTIC_PROFILES["birth_full_v1"]["bytes"] + 1),
                                            semantic_profile="birth_full_v1")

    def test_unknown_profiles_and_invalid_semantics_do_not_fall_back(self):
        for profile in (None, True, {}, "unbounded", "birth_full_unknown"):
            with self.subTest(profile=profile), self.assertRaisesRegex(ValueError, "unknown_semantic_profile"):
                scanner.derive_semantic_aliases(b"{}", semantic_profile=profile)
        for raw in (b"\0", b"\r", "é".encode(), b'{"oracle":1,"oracle":2}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                scanner.derive_semantic_aliases(raw, semantic_profile="birth_full_v1")

    def test_all_full_profile_resource_limits_fail_explicitly(self):
        cases = (("leaves", {"oracle": [1, 2, 3]}, "leaf_bound"),
                 ("nodes", {"oracle": [{}, {}, {}]}, "node_bound"),
                 ("aliases", {"oracle": "private_label"}, "alias_bound"),
                 ("depth", {"oracle": [[[1]]]}, "depth_bound"))
        for name, value, error in cases:
            profile = dict(scanner.SEMANTIC_PROFILES["birth_full_v1"], **{name: 2})
            with self.subTest(name=name), patch.object(scanner, "SEMANTIC_PROFILES", {"birth_full_v1": profile}):
                with self.assertRaisesRegex(ValueError, error):
                    scanner.derive_semantic_aliases(canonical_json(value), semantic_profile="birth_full_v1")
        raw = canonical_json({"core": "PCFL_EVENT_LINK"})
        self.assertTrue(scanner.forbidden_semantic_labels(raw, semantic_profile="birth_full_v1"))


if __name__ == "__main__":
    unittest.main()
