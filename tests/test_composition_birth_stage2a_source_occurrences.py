"""Opt-in source attribution preserves strict defaults and independent checks."""

from dataclasses import replace
import unittest

from organism_v6 import composition_birth_stage2a_inventory as inventory
from organism_v6 import composition_birth_stage2a_scan_inputs as inputs
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_future_inputs import arguments


class SourceOccurrenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arguments = arguments(2)
        cls.binding = inputs.bind_birth_arm(cls.arguments["record"], cls.arguments["case"],
                                             role_tokens=cls.arguments["role_tokens"])
        cls.source = inputs._semantic_source(cls.binding)
        cls.semantic = canonical_json({"oracle": {"alias": "545", "goal": "goal",
                                                  "start": "start", "service": "service"}})

    def scan(self, prefix=None, **overrides):
        binding = self.binding
        supplied = dict(target=binding.target, phase=binding.phase, decision_index=binding.decision_index,
                        semantic_bytes=self.semantic, fields=binding.fields, task_start=binding.task_start,
                        task_goal=binding.task_goal, current=binding.current,
                        implicated_query=binding.implicated_query, implicated_event=binding.implicated_event,
                        observed_contradiction=binding.observed_contradiction, semantic_source=self.source)
        supplied.update(overrides)
        return scanner.scan_forward_targets(binding.projection_bytes if prefix is None else prefix, **supplied)

    def test_opt_in_retains_identical_aliases_and_occurrence_evidence(self):
        strict = self.scan(semantic_source=None)
        repaired = self.scan()
        self.assertFalse(strict.passed)
        self.assertTrue(repaired.passed)
        self.assertEqual(strict.aliases, repaired.aliases)
        for hit in strict.issues:
            self.assertTrue(any((receipt.category, receipt.value, receipt.form, receipt.start, receipt.end)
                                == (hit.category, hit.value, hit.form, hit.start, hit.end)
                                and receipt.field_path.startswith("/messages/")
                                and self.binding.projection_sha256 in receipt.evidence
                                for receipt in repaired.receipts))
        self.assertEqual({hit.form for hit in repaired.receipts if hit.value == b"545"},
                         {"literal", "normalized", "compact"})

    def test_complete_private_object_requires_explicit_opt_in(self):
        report = inventory.scan_birth_inventory(**self.arguments, source_semantic_occurrences=True)
        self.assertTrue(report.supplied_projection_clear)
        self.assertTrue(report.content_scan.source_semantic_occurrences)
        self.assertEqual(len(report.content_scan.scan_report.aliases), 119580)
        self.assertFalse(any(report.science_gates.values()))
        self.assertFalse(report.inventory_completeness_verified)

    def test_largest_A_object_composes_v2_semantic_future_and_route_checks(self):
        report = inventory.scan_birth_inventory(
            **arguments(29, 0, 3, "CLOSED"), semantic_profile="birth_full_v2",
            source_semantic_occurrences=True,
        )
        self.assertEqual(report.metadata_inputs.coverage_counts["leaves"], 200244)
        self.assertEqual(len(report.content_scan.scan_report.aliases), 422196)
        self.assertEqual(report.content_scan.semantic_profile, "birth_full_v2")
        self.assertTrue(report.supplied_projection_clear)
        self.assertTrue(report.route_scan.registered_grammar_clear)
        self.assertFalse(report.native_chat_bytes_verified)
        self.assertFalse(any(report.science_gates.values()))

    def test_appended_copies_and_aliases_do_not_inherit_source_spans(self):
        for suffix in (self.binding.projection_bytes, b"545 goal start service",
                       b"545 GOAL START SERVICE", b"545G O A L"):
            with self.subTest(suffix=suffix[:30]):
                report = self.scan(self.binding.projection_bytes + b"\n" + suffix)
                self.assertFalse(report.passed)
                self.assertTrue(any(hit.start > len(self.binding.projection_bytes) for hit in report.issues))

    def test_moved_modified_and_truncated_source_prefix_fail(self):
        for prefix in (b"\n" + self.binding.projection_bytes,
                       self.binding.projection_bytes.replace(b"GOAL", b"G0AL", 1),
                       self.binding.projection_bytes[:-1]):
            with self.assertRaisesRegex(ValueError, "semantic_source_prefix_changed"):
                self.scan(prefix)

    def test_appending_to_terminal_keyword_or_identifier_invalidates_binding(self):
        identifier = next(span.value for span in self.source.spans
                          if span.kind == "identifier" and b"545" in span.value)
        for raw, kind, alias in ((b"ACK", "syntax", "ack"), (identifier, "identifier", "545")):
            source = scanner.SemanticSource(raw, (scanner.SemanticSourceSpan(
                "/terminal", 0, len(raw), kind, raw, "synthetic-original-token"),))
            options = dict(semantic_source=source, fields=(),
                           semantic_bytes=canonical_json({"oracle": {"alias": alias}}))
            with self.subTest(kind=kind):
                self.assertTrue(self.scan(raw, **options).passed)
                self.assertTrue(self.scan(raw + b"\n", **options).passed)
                with self.assertRaisesRegex(ValueError, "invalid_semantic_source_span"):
                    self.scan(raw + b"X", **options)
                copied = self.scan(raw + b"\n" + raw, **options)
                self.assertFalse(copied.passed)
                self.assertTrue(any(hit.start > len(raw) for hit in copied.issues))

    def test_keyword_substrings_and_cross_token_aliases_still_fail(self):
        raw = self.binding.projection_bytes
        start = raw.index(b"\nSTART ") + len(b"\nSTART ")
        crossing = raw[start:start + 22].decode("ascii")
        for value in ("serv", "tart", crossing):
            with self.subTest(value=value):
                report = self.scan(semantic_bytes=canonical_json({"oracle": {"alias": value}}))
                self.assertFalse(report.passed)
                self.assertTrue(any(hit.category == "semantic_alias" for hit in report.issues))

    def test_future_target_and_forbidden_categories_never_waived(self):
        identifier = next(span.value for span in self.source.spans
                          if span.kind == "identifier" and b"545" in span.value)
        future = self.scan(future_identifiers=(identifier,))
        self.assertTrue(any(hit.category == "future_identifier" for hit in future.issues))
        self.assertTrue(any(hit.category == "semantic_alias" and hit.value == b"545"
                            for hit in future.receipts))
        target = self.scan(self.binding.projection_bytes + b"\n" + self.binding.target)
        self.assertTrue(any(hit.category == "full_target" for hit in target.issues))
        forbidden = self.scan(semantic_bytes=canonical_json({"core": {"tag": "PCFL_EVENT_LINK"}}))
        self.assertFalse(forbidden.passed)
        self.assertTrue(forbidden.semantic_issues)

    def test_malformed_forged_overlapping_and_foreign_spans_fail(self):
        span = self.source.spans[0]
        for bad in (replace(span, value=b"OTHER"), replace(span, kind="free_text"),
                    replace(span, start=True), replace(span, end=span.end - 1),
                    replace(span, evidence="")):
            with self.assertRaises(ValueError):
                self.scan(semantic_source=replace(self.source, spans=(bad,)))
        with self.assertRaises(ValueError):
            self.scan(semantic_source=replace(self.source, spans=(span, span)))
        with self.assertRaises(ValueError):
            self.scan(semantic_source={"passed": True})
        other = arguments(2, ordinal=1, arm="ATOM_LOCAL")
        other_binding = inputs.bind_birth_arm(other["record"], other["case"], role_tokens=other["role_tokens"])
        with self.assertRaises(ValueError):
            self.scan(semantic_source=inputs._semantic_source(other_binding))

    def test_bound_integration_rejects_mutations_and_caller_exemptions(self):
        wrong_master = dict(self.arguments, display_master=b"wrong-master")
        with self.assertRaises(ValueError):
            inventory.scan_birth_inventory(**wrong_master, source_semantic_occurrences=True)
        with self.assertRaises(TypeError):
            inventory.scan_birth_inventory(**self.arguments, semantic_source=self.source)
        with self.assertRaises(ValueError):
            inventory.scan_birth_inventory(**self.arguments, source_semantic_occurrences="yes")


if __name__ == "__main__":
    unittest.main()
