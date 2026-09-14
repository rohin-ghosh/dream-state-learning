"""Authentic-boundary and adversarial CPU diagnostics for the v6 typed basis.

Preserved pre-repair CPU receipt; the full failure output remains in the session
transcript. Exact command:
python3 -m unittest tests.test_composition_birth_stage2a_typed_scan tests.test_composition_birth_stage2a_scanner -q
Ran 68 tests in 65.630s
FAILED (failures=1)
Failing test: test_authentic_boundaries_across_all_phases_both_arms_must_pass
All 56 original records failed, with zero forward/route issues: worlds 0, 5, 9
had private A/goal; worlds 2, 11 had goal; world 18 had relation; world 25 had
A/relation, for every ordinal 0..3 and both CLOSED and ATOM_LOCAL.

The system-only receipt repair, using the same command, ran 75 tests in
70.709s with one failure: 52/56 authentic records still had task GOAL or
historical READ RELATION syntax collisions. Both failed full outputs remain
preserved in the session transcript; neither authentic assertion was waived.
"""

from dataclasses import FrozenInstanceError, dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
from types import MappingProxyType
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_future_inputs as future
from organism_v6 import composition_birth_stage2a_route_inputs as routes
from organism_v6 import composition_birth_stage2a_route_scan as route_scan
from organism_v6 import composition_birth_stage2a_scan_inputs as scan_inputs
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6 import composition_birth_stage2a_typed_scan as typed
from organism_v6 import composition_birth_stage2a_worlds as worlds
from tests.test_composition_birth_stage2a_future_inputs import arguments


@lru_cache(maxsize=16)
def diagnostic_inputs(number=2, member=0, ordinal=0, arm="CLOSED"):
    inventory = future.derive_birth_future_inputs(**arguments(number, member, ordinal, arm))
    return dict(source=inventory.source, binding=inventory.binding, future_inputs=inventory,
                route_inputs=routes._derive_from_source(inventory.source))


def appended(inputs, suffix):
    return typed.scan_typed_birth(**inputs, candidate_prefix=inputs["binding"].projection_bytes + b"\n" + suffix)


class TypedPrivateBasisTests(unittest.TestCase):
    def setUp(self):
        self.inputs = diagnostic_inputs()
        self.source = self.inputs["source"]
        self.basis = typed.build_typed_private_basis(self.source.case, self.source.record, self.source.role_tokens)

    def test_immutable_complete_keys_and_source_ownership(self):
        self.assertIs(type(self.basis), tuple)
        role_values = [item for item in self.basis if item.category == "private_role_key"]
        self.assertEqual({item.value for item in role_values},
                         {role.encode("ascii") for role in self.source.role_tokens})
        self.assertTrue(all(item.source_path == ("role_tokens", item.value.decode("ascii"))
                            for item in role_values))
        self.assertEqual({item.value for item in self.basis if item.category == "private_case_key"}, {b"p02/m0"})
        self.assertEqual({item.value for item in self.basis if item.category == "private_unit_key"},
                         {f"p02/m0/u{index}".encode("ascii") for index in range(4)})
        with self.assertRaises(FrozenInstanceError):
            self.basis[0].value = b"changed"
        with self.assertRaises(TypeError):
            typed.SOURCE_FIELD_SCHEMA[birth.BirthCase]["new_field"] = "private_category"

    def test_explicit_categorical_schema_and_recovery_case_key(self):
        expected_fields = {"pair_type", "family", "family_motif", "flow", "recovery_subtype",
                           "terminal_class", "goal_side", "domain"}
        rules = typed.SOURCE_FIELD_SCHEMA[birth.BirthCaseDescriptor]
        self.assertEqual({name for name, policy in rules.items() if policy == "private_category"}, expected_fields)
        for source_class, source_rules in typed.SOURCE_FIELD_SCHEMA.items():
            self.assertEqual(tuple(field.name for field in fields(source_class)), tuple(source_rules))
        values = {(item.source_path, item.value) for item in self.basis}
        for name in expected_fields:
            self.assertIn((("case", "descriptor", name), getattr(self.source.case.descriptor, name).encode("ascii")),
                          values)
        recovered = diagnostic_inputs(5)["source"]
        basis = typed.build_typed_private_basis(recovered.case, recovered.record, recovered.role_tokens)
        self.assertIn(typed.TypedPrivateValue("private_case_key", b"p04/m0",
                                             ("case", "descriptor", "recovery_match_id")), basis)

    def test_no_pointer_structural_scalar_tag_or_public_id_needles(self):
        values = {item.value for item in self.basis}
        forbidden = {b"case", b"descriptor", b"task", b"world_edges", b"node", b"query", b"port",
                     b"m0", b"p02", b"u0", b"0", b"1", b"true", b"false", b"null",
                     b"/case/descriptor/family", b"family=B", b"ID_NODE"}
        self.assertFalse(values & forbidden)
        self.assertFalse(values & {value.encode("ascii") for value in self.source.role_tokens.values()})
        self.assertFalse(any(item.startswith(b"/") or item.isdigit() for item in values))
        descriptor = replace(self.source.case.descriptor, family="true")
        with self.assertRaisesRegex(typed.TypedScanError, "invalid_private_value"):
            typed.build_typed_private_basis(replace(self.source.case, descriptor=descriptor),
                                            self.source.record, self.source.role_tokens)

    def test_unhandled_fields_types_and_policies_are_diagnosed(self):
        @dataclass(frozen=True)
        class ExtendedFacts(birth.BirthTraceFacts):
            hidden_category: str = "SECRET_CATEGORY"

        facts = ExtendedFacts(**vars(self.source.case.facts))
        with self.assertRaisesRegex(typed.TypedScanError, "unhandled_source_type"):
            typed.build_typed_private_basis(replace(self.source.case, facts=facts),
                                            self.source.record, self.source.role_tokens)
        altered = dict(typed.SOURCE_FIELD_SCHEMA)
        altered[birth.BirthCaseDescriptor] = dict(altered[birth.BirthCaseDescriptor], family="unknown_category")
        with patch.object(typed, "SOURCE_FIELD_SCHEMA", MappingProxyType(altered)):
            with self.assertRaisesRegex(typed.TypedScanError, "unhandled_source_category"):
                typed.build_typed_private_basis(self.source.case, self.source.record, self.source.role_tokens)
        altered[birth.BirthCaseDescriptor] = dict(typed.SOURCE_FIELD_SCHEMA[birth.BirthCaseDescriptor])
        del altered[birth.BirthCaseDescriptor]["family"]
        with patch.object(typed, "SOURCE_FIELD_SCHEMA", MappingProxyType(altered)):
            with self.assertRaisesRegex(typed.TypedScanError, "unhandled_source_fields"):
                typed.build_typed_private_basis(self.source.case, self.source.record, self.source.role_tokens)

    def test_complete_keys_match_but_not_fragments_or_id_atoms(self):
        role = next(item for item in self.basis if item.category == "private_role_key")
        isolated = (role, typed.TypedPrivateValue("private_category", b"A", ("case", "descriptor", "family")))
        fragment = role.value.split(b"/")[-1]
        token = next(iter(self.source.role_tokens.values())).encode("ascii")
        self.assertEqual(typed._typed_occurrences(fragment + b"\n" + token, isolated), ())
        self.assertEqual(typed._typed_occurrences(b"prefix/" + role.value + b"/suffix", isolated), ())
        for raw in (role.value, role.value.lower(), role.value.translate(None, b"_- <>")):
            found = typed._typed_occurrences(raw, isolated)
            self.assertTrue(any(item.value == role.value and item.source_paths == (role.source_path,) for item in found))
        self.assertTrue(typed._typed_occurrences(b"A", isolated))

    def test_same_value_keeps_all_owners_and_original_byte_offsets(self):
        basis = (typed.TypedPrivateValue("private_category", b"A_PRIVATE_SPOKES", ("one",)),
                 typed.TypedPrivateValue("private_category", b"A_PRIVATE_SPOKES", ("two",)))
        raw = b"unrelated\nA_PRIVATE_SPOKES\n"
        matches = typed._typed_occurrences(raw, basis)
        self.assertEqual({item.form for item in matches}, {"literal", "normalized", "compact"})
        self.assertTrue(all(raw[item.start:item.end] == basis[0].value for item in matches))
        self.assertTrue(all(item.source_paths == (("one",), ("two",)) for item in matches))


class TypedBirthScanTests(unittest.TestCase):
    def test_fixed_protocol_receipts_preserve_all_raw_collisions(self):
        inputs = diagnostic_inputs(0)
        report = typed.scan_typed_birth(**inputs)
        fixed = wire.SYSTEM_MESSAGE.encode("ascii")
        digest = sha256(fixed).hexdigest()
        self.assertTrue(report.typed_receipts)
        self.assertEqual(report.private_basis, typed.build_typed_private_basis(
            inputs["source"].case, inputs["source"].record, inputs["source"].role_tokens))
        self.assertEqual(len(report.typed_occurrences), len(report.typed_issues) + len(report.typed_receipts))
        receipted = set()
        for receipt in report.typed_receipts:
            message = report.binding.message_spans[receipt.message_index]
            self.assertEqual(receipt.message_sha256, message.content_sha256)
            self.assertEqual(receipt.message_span, (message.start, message.end))
            self.assertTrue(message.start <= receipt.start < receipt.end <= message.end)
            self.assertTrue(receipt.evidence)
            if receipt.message_index == 0:
                self.assertEqual(receipt.message_sha256, digest)
                self.assertEqual(receipt.protocol_source_path, ("wire", "SYSTEM_MESSAGE"))
                self.assertEqual(report.candidate_prefix[receipt.start:receipt.end], fixed[receipt.start:receipt.end])
            else:
                self.assertEqual(receipt.protocol_source_path[:3], ("messages", str(receipt.message_index), "syntax"))
            occurrence = typed.TypedPrivateOccurrence(*(getattr(receipt, field.name)
                                                        for field in fields(typed.TypedPrivateOccurrence)))
            self.assertIn(occurrence, report.typed_occurrences)
            receipted.add(occurrence)
        self.assertEqual(set(report.typed_occurrences), set(report.typed_issues) | receipted)
        self.assertFalse(set(report.typed_issues) & receipted)
        self.assertTrue({b"A", b"goal"} <= {item.value for item in report.typed_receipts})
        self.assertFalse(report.typed_issues)
        self.assertTrue(report.passed)
        with self.assertRaises(FrozenInstanceError):
            report.typed_receipts[0].message_sha256 = "changed"

    def test_protocol_spans_are_derived_independently_of_private_values(self):
        first, second = diagnostic_inputs(0), diagnostic_inputs(2)
        protocol = typed._fixed_protocol_source(first["source"], first["binding"])
        self.assertEqual(protocol, typed._fixed_protocol_source(second["source"], second["binding"]))
        prefix = first["binding"].projection_bytes
        basis = (typed.TypedPrivateValue("private_category", b"Return exactly", ("private", "one")),
                 typed.TypedPrivateValue("private_role_key", b"Return exactly", ("private", "two")))
        raw = typed._typed_occurrences(prefix, basis, protocol=protocol)
        issues, receipts = typed._partition_typed_occurrences(prefix, prefix, protocol, raw)
        self.assertTrue(raw)
        self.assertFalse(issues)
        self.assertEqual(len(receipts), len(raw))
        partial = (typed.TypedPrivateValue("private_category", b"eturn", ("private", "partial")),)
        self.assertEqual(typed._typed_occurrences(prefix, partial, protocol=protocol), ())

    def test_appended_same_private_value_and_copied_system_never_receive_receipts(self):
        inputs = diagnostic_inputs(0)
        end = len(inputs["binding"].projection_bytes)
        for suffix in (b"A", b"goal", wire.SYSTEM_MESSAGE.encode("ascii")):
            with self.subTest(suffix=suffix[:20]):
                report = appended(inputs, suffix)
                self.assertFalse(report.passed)
                self.assertTrue(any(item.category == "private_category" and item.start > end
                                    for item in report.typed_issues))
                self.assertTrue(report.typed_receipts)
                self.assertFalse(any(item.start > end for item in report.typed_receipts))

    def test_shifted_or_changed_protocol_cannot_inherit_original_receipts(self):
        inputs = diagnostic_inputs(0)
        original = inputs["binding"].projection_bytes
        changed_middle = original.replace(b"Identifiers are opaque.", b"Identifiers are Opaque.", 1)
        self.assertNotEqual(changed_middle, original)
        for candidate in (b"X" + original, b"x" + original[1:], changed_middle):
            with self.subTest(candidate=candidate[:20]):
                report = typed.scan_typed_birth(**inputs, candidate_prefix=candidate)
                self.assertFalse(report.passed)
                self.assertFalse(report.typed_receipts)
                self.assertTrue(any(item.value == b"goal" and item.start < len(wire.SYSTEM_MESSAGE)
                                    for item in report.typed_issues))

    def test_adjacent_suffix_keeps_original_collision_raw_but_unreceipted(self):
        inputs = diagnostic_inputs(2)
        original = inputs["binding"].projection_bytes
        start = original.index(b"goal")
        end = start + len(b"goal")
        candidate = original[:end] + b"X" + original[end:]
        self.assertEqual(candidate[:end], original[:end])
        report = typed.scan_typed_birth(**inputs, candidate_prefix=candidate)
        matches = [item for item in report.typed_occurrences
                   if item.value == b"goal" and item.start == start and item.end == end]
        self.assertTrue(matches)
        self.assertTrue(all(item in report.typed_issues for item in matches))
        self.assertFalse(report.typed_receipts)
        self.assertFalse(report.passed)

    def test_protocol_receipts_never_authorize_forbidden_label_categories(self):
        inputs = diagnostic_inputs()
        original = inputs["binding"].projection_bytes
        protocol = typed._fixed_protocol_source(inputs["source"], inputs["binding"])
        basis = tuple(typed.TypedPrivateValue(category, b"goal", ("test", category))
                      for category in ("forbidden_core", "forbidden_edge_label"))
        raw = typed._typed_occurrences(original, basis, protocol=protocol)
        issues, receipts = typed._partition_typed_occurrences(original, original, protocol, raw)
        self.assertTrue(raw)
        self.assertEqual(raw, issues)
        self.assertFalse(receipts)
        report = appended(inputs, b"\n".join((*scanner.FORBIDDEN_CORE_LABELS, *typed.FORBIDDEN_EDGE_LABELS)))
        self.assertFalse(report.passed)
        self.assertTrue(all(item.category.startswith("private_") for item in report.typed_receipts))
        self.assertTrue(set(typed.FORBIDDEN_EDGE_LABELS) <= {item.value for item in report.typed_issues})
        self.assertTrue(set(scanner.FORBIDDEN_CORE_LABELS) <= {item.value for item in report.content_scan.issues})

    def test_caller_protocol_offsets_and_hashes_are_not_trusted(self):
        inputs = diagnostic_inputs()
        original = inputs["binding"]
        for first_span in (replace(original.message_spans[0], start=1),
                           replace(original.message_spans[0], content_sha256="0" * 64)):
            binding = replace(original, message_spans=(first_span,) + original.message_spans[1:])
            supplied = dict(inputs, binding=binding, future_inputs=replace(inputs["future_inputs"], binding=binding))
            with self.assertRaisesRegex(typed.TypedScanError, "fixed_protocol_span_mismatch"):
                typed.scan_typed_birth(**supplied)

    def test_task_goal_and_read_relation_receive_exact_source_syntax_receipts(self):
        for number, ordinal, value in ((2, 0, b"goal"), (18, 1, b"relation")):
            for arm in ("CLOSED", "ATOM_LOCAL"):
                with self.subTest(number=number, arm=arm):
                    inputs = diagnostic_inputs(number, ordinal=ordinal, arm=arm)
                    report = typed.scan_typed_birth(**inputs)
                    self.assertTrue(report.passed, report.issues)
                    allowed = {(span.start, span.end): span
                               for span in scan_inputs._semantic_source(report.binding).spans if span.kind == "syntax"}
                    receipts = [item for item in report.typed_receipts if item.value == value and item.message_index > 0]
                    self.assertTrue(receipts)
                    for item in receipts:
                        span = allowed[item.start, item.end]
                        self.assertEqual(item.protocol_source_path, tuple(span.path.lstrip("/").split("/")))
                        self.assertEqual(item.evidence, span.evidence)
                        self.assertEqual(report.candidate_prefix[item.start:item.end], value.upper())
                        self.assertFalse(scanner._public_identifier(span.value))

    def test_syntax_copies_byte_changes_and_adjacent_suffix_never_inherit_receipts(self):
        for number, ordinal, value in ((2, 0, b"goal"), (18, 1, b"relation")):
            inputs = diagnostic_inputs(number, ordinal=ordinal)
            original = inputs["binding"].projection_bytes
            authentic = typed.scan_typed_birth(**inputs)
            receipt = next(item for item in authentic.typed_receipts if item.value == value and item.message_index > 0)
            message = original[receipt.message_span[0]:receipt.message_span[1]]
            candidates = (
                original + b"\n" + value.upper(),
                original + b"\n" + message,
                original[:receipt.end] + b"X" + original[receipt.end:],
                original[:receipt.start] + value.upper()[:1].lower() + original[receipt.start + 1:],
                b"x" + original[1:],
            )
            for candidate in candidates:
                with self.subTest(number=number, candidate=candidate[-20:]):
                    report = typed.scan_typed_birth(**inputs, candidate_prefix=candidate)
                    self.assertFalse(report.passed)
                    self.assertTrue(any(item.value == value for item in report.typed_issues))
                    self.assertFalse(any(item.start > len(original) for item in report.typed_receipts))
                    if candidate[:len(original)] != original:
                        self.assertFalse(any(item.start == receipt.start and item.end == receipt.end
                                             for item in report.typed_receipts))
            changed_message_end = original[:receipt.message_span[1]] + b"X" + original[receipt.message_span[1]:]
            report = typed.scan_typed_birth(**inputs, candidate_prefix=changed_message_end)
            self.assertTrue(any(item.start == receipt.start and item.end == receipt.end for item in report.typed_issues))

    def test_syntax_sources_exclude_identifier_and_arbitrary_word_spans(self):
        inputs = diagnostic_inputs()
        syntax = typed._fixed_syntax_sources(inputs["source"], inputs["binding"])
        self.assertTrue(syntax)
        for span in syntax:
            start, end = next(iter(span.token_starts)), next(iter(span.token_ends))
            value = inputs["binding"].projection_bytes[start:end]
            self.assertTrue(value in scanner.SHARED_ATOMS or value in scanner.SHARED_LINES)
            self.assertFalse(scanner._public_identifier(value))
        actual = scan_inputs._semantic_source(inputs["binding"])
        identifier = next(span for span in actual.spans if span.kind == "identifier")
        forged = replace(actual, spans=(replace(identifier, kind="syntax"),))
        with patch.object(scan_inputs, "_semantic_source", return_value=forged):
            with self.assertRaisesRegex(typed.TypedScanError, "nonfixed_syntax_token"):
                typed.scan_typed_birth(**inputs)

    def test_authentic_boundaries_across_all_phases_both_arms_must_pass(self):
        failures, phases, arms = [], set(), set()
        for number in (0, 2, 5, 9, 11, 18, 25):
            for ordinal in range(4):
                for arm in ("CLOSED", "ATOM_LOCAL"):
                    inputs = diagnostic_inputs(number, ordinal=ordinal, arm=arm)
                    report = typed.scan_typed_birth(**inputs)
                    phases.add(report.binding.phase)
                    arms.add(arm)
                    self.assertTrue(report.candidate_matches_projection)
                    if not report.passed:
                        failures.append((number, ordinal, arm,
                                         sorted({item.value.decode("ascii") for item in report.private_issues}),
                                         len(report.forward.issues), len(report.route.issues)))
        self.assertEqual(phases, {"SEEK", "PROSPECT", "READ_CHECK", "STEP_CHECK", "CONTINUE"})
        self.assertEqual(arms, {"CLOSED", "ATOM_LOCAL"})
        self.assertEqual(failures, [], "Authentic failures (world, ordinal, arm, private values, forward, route): "
                         + repr(failures))

    def test_mutation_matrix_all_phases_both_arms(self):
        for number in (5, 9):
            for ordinal in range(4):
                for arm in ("CLOSED", "ATOM_LOCAL"):
                    with self.subTest(number=number, ordinal=ordinal, arm=arm):
                        inputs = diagnostic_inputs(number, ordinal=ordinal, arm=arm)
                        binding, source = inputs["binding"], inputs["source"]
                        role = next(iter(source.role_tokens)).encode("ascii")
                        by_kind = {}
                        for value in sorted(inputs["future_inputs"].future_identifiers):
                            by_kind.setdefault(value[:5], value)
                        operand = source.record.unit.operand
                        values = [binding.target, source.case.descriptor.family_motif.encode("ascii"), role,
                                  *by_kind.values(), *scanner.FORBIDDEN_CORE_LABELS, *typed.FORBIDDEN_EDGE_LABELS]
                        if operand is not None:
                            values.append(operand.encode("ascii"))
                        report = appended(inputs, b"\n".join(values))
                        boundary = len(binding.projection_bytes)
                        fresh = [item for item in report.issues if getattr(item, "start", -1) > boundary]
                        categories = {item.category for item in fresh}
                        self.assertFalse(report.passed)
                        self.assertTrue({"full_target", "future_identifier", "private_category", "private_role_key",
                                         "forbidden_core", "forbidden_edge_label"} <= categories)
                        if operand is not None:
                            self.assertIn("operand", categories)
                        self.assertTrue(set(by_kind.values()) <= {item.value for item in fresh
                                                                 if item.category == "future_identifier"})
                        for label in (*scanner.FORBIDDEN_CORE_LABELS, *typed.FORBIDDEN_EDGE_LABELS):
                            self.assertIn(label, {item.value for item in fresh})

    def test_forward_causal_receipts_and_stop_protocol_exception_preserved(self):
        for number, ordinal in ((5, 0), (5, 1), (5, 2), (5, 3), (9, 0), (9, 2), (9, 3)):
            for arm in ("CLOSED", "ATOM_LOCAL"):
                inputs = diagnostic_inputs(number, ordinal=ordinal, arm=arm)
                report = typed.scan_typed_birth(**inputs)
                self.assertTrue(report.forward.passed, report.forward.issues)
                if report.binding.target == b"STOP":
                    self.assertTrue(any(item.category == "full_target" and item.value == b"STOP"
                                        for item in report.forward.receipts))
                else:
                    self.assertTrue(report.forward.receipts)

    def test_route_grammar_is_existing_matcher_with_causal_authentication(self):
        inputs = diagnostic_inputs(5, ordinal=3)
        index, binding = inputs["route_inputs"], inputs["binding"]
        first = next(edge for edge in index.transitions.values() if edge.event == index.source.case.facts.failed_event)
        second = next(edge for edge in index.transitions.values() if edge.event == index.source.case.facts.selected_event)
        original = typed.scan_typed_birth(**inputs)
        self.assertEqual(original.route, route_scan._scan_from_inputs(index, binding))
        self.assertTrue(original.route.occurrences)
        self.assertFalse(original.route.issues)
        candidates = [f"STEP {first.port}\nWORLD\nCURRENT {first.actual}\nSTEP {second.port}".encode("ascii"),
                      f"{first.port} -> {second.port}".encode("ascii")]
        for skin in (0, 1):
            blocks = [index.source.case.construction.blocks["READ RELATION " + edge.query]
                      for edge in (first, second)]
            candidates.append("\n".join(worlds.render_service(block.kind, block.rows, skin=skin)
                                         for block in blocks).encode("ascii"))
        second_block = index.source.case.construction.blocks["READ RELATION " + second.query]
        row = next(line for line in second_block.raw.split("\n") if second.port in line)
        candidates.append((f"STEP {first.port}\n" + row).encode("ascii"))
        grammars = set()
        for suffix in candidates:
            report = appended(inputs, suffix)
            self.assertEqual(report.route, route_scan._scan_from_inputs(index, binding,
                                                                        candidate_prefix=report.candidate_prefix))
            self.assertTrue(report.route.issues)
            grammars.update(item.grammar for item in report.route.issues)
        self.assertTrue({"actions", "event_rows", "ordered_ids", "mixed"} <= grammars)
        candidate = binding.projection_bytes.replace(("WORLD\nCURRENT " + first.actual).encode("ascii"),
                                                     ("WORLD\nCURRENT " + first.predicted).encode("ascii"), 1)
        changed = typed.scan_typed_birth(**inputs, candidate_prefix=candidate)
        self.assertTrue(changed.route.issues)
        unknown = appended(inputs, f"STEP {first.port}\nunknown prose\nSTEP {second.port}".encode("ascii"))
        self.assertTrue(unknown.route.unrecognized_line_spans)

    def test_copied_closed_history_has_no_atom_receipts(self):
        closed = diagnostic_inputs(5, ordinal=3)
        atom = diagnostic_inputs(5, ordinal=3, arm="ATOM_LOCAL")
        self.assertEqual(atom["binding"].retained_trace_indices, ())
        original = typed.scan_typed_birth(**atom)
        self.assertEqual(original.route.occurrences, ())
        copied = appended(atom, closed["binding"].projection_bytes)
        self.assertTrue(copied.route.issues)
        boundary = len(atom["binding"].projection_bytes)
        self.assertFalse(any(item.start > boundary for item in copied.forward.receipts))

    def test_candidate_equality_is_not_semantic_validation_or_admission(self):
        inputs = diagnostic_inputs()
        report = typed.scan_typed_birth(**inputs, candidate_prefix=b"unrecognized prose")
        self.assertTrue(report.passed)
        self.assertFalse(report.candidate_matches_projection)
        self.assertTrue(report.route.unrecognized_line_spans)
        self.assertFalse(report.inventory_completeness_verified)
        self.assertFalse(report.native_chat_bytes_verified)
        self.assertFalse(any(report.science_gates.values()))
        authentic = typed.scan_typed_birth(**inputs)
        self.assertTrue(authentic.candidate_matches_projection)
        self.assertTrue(authentic.passed)
        self.assertTrue(any(item.value == b"goal" for item in authentic.typed_receipts))
        self.assertFalse(authentic.private_issues)

    def test_no_full_semantic_tree_and_report_interface(self):
        inputs = diagnostic_inputs()
        with patch.object(scanner, "derive_semantic_aliases", wraps=scanner.derive_semantic_aliases) as aliases:
            with patch.object(scanner, "semantic_alias_ledger", side_effect=AssertionError("no full tree")):
                report = typed.scan_typed_birth(**inputs)
        aliases.assert_called_once_with(b"{}", semantic_profile="legacy")
        self.assertEqual(report.forward.aliases, ())
        self.assertIs(report.content_scan, report.forward)
        self.assertIs(report.route_scan, report.route)
        self.assertEqual(report.counts["private_values"], len(report.private_basis))
        self.assertEqual(report.counts["typed_occurrences"], len(report.typed_occurrences))
        self.assertEqual(report.counts["typed_receipts"], len(report.typed_receipts))
        self.assertEqual(report.counts["private_role_key"], len(inputs["source"].role_tokens))
        with self.assertRaises(TypeError):
            report.counts["private_values"] = 0

    def test_foreign_sources_bindings_and_green_flags_rejected(self):
        inputs = diagnostic_inputs()
        foreign = diagnostic_inputs(2, member=1)
        for changes in ({"future_inputs": foreign["future_inputs"]}, {"route_inputs": foreign["route_inputs"]},
                        {"binding": replace(inputs["binding"], decision_index=1000)}):
            with self.assertRaises(typed.TypedScanError):
                typed.scan_typed_birth(**dict(inputs, **changes))
        with self.assertRaises(TypeError):
            typed.scan_typed_birth(**inputs, validated=True)
        for invalid in (b"\0", b"\r", b"\xff", "not bytes"):
            with self.assertRaises(ValueError):
                typed.scan_typed_birth(**inputs, candidate_prefix=invalid)

    def test_explicit_bounds_fail_instead_of_truncating_findings(self):
        basis = (typed.TypedPrivateValue("private_category", b"SECRET", ("case", "category")),)
        with patch.object(scanner, "BOUNDS", dict(scanner.BOUNDS, hits=0)):
            with self.assertRaisesRegex(typed.TypedScanError, "typed_scanner_hit_bound_exceeded"):
                typed._typed_occurrences(b"SECRET", basis)


if __name__ == "__main__":
    unittest.main()
