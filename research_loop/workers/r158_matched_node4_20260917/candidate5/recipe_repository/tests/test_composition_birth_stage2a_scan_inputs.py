"""Synthetic source projections; never native chat or full-inventory evidence."""

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_scan_inputs as source
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_birth import synthetic_bindings


SEMANTIC = canonical_json({"oracle": {"privatebindingmetadata": "EVALUATORPAYLOADNOTINPUBLICPREFIX"}})


def rehashed_record(record, prefix):
    raw = targets.messages_bytes(prefix)
    return replace(record, prefix=prefix, prefix_sha256=sha256(raw).hexdigest(),
                   content_bytes=sum(len(message.content.encode("ascii")) for message in prefix),
                   serialized_bytes=len(raw))


class SourceScanInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = {}
        for number in range(32):
            bindings = synthetic_bindings(number)
            pair = birth.build_birth_pair(world=f"p{number:02d}", role_tokens=bindings,
                                          display_master=b"synthetic-source-scan-projection")
            for case in pair.cases:
                cls.examples[number, case.descriptor.member] = (
                    case, targets.serialize_birth_case(case, role_tokens=bindings), bindings)

    def setUp(self):
        self.case, self.pairs, self.bindings = self.examples[0, "m0"]
        self.inventory = source.ScanInventory(SEMANTIC, (), ())

    def scan(self, record, *, case=None, bindings=None, **overrides):
        arguments = dict(role_tokens=bindings if bindings is not None else self.bindings,
                         semantic_bytes=SEMANTIC, future_identifiers=(), registered_routes=())
        arguments.update(overrides)
        return source.scan_birth_arm(record, case if case is not None else self.case, **arguments)

    def test_all_512_source_arm_projections_with_explicit_synthetic_inventories(self):
        phases = set()
        arms = set()
        projections = 0
        for key, (case, pairs, bindings) in self.examples.items():
            for target, pair in zip(case.targets, pairs):
                with self.subTest(case=key, target=target.ordinal):
                    report = source.scan_birth_pair(pair, case, role_tokens=bindings,
                                                   closed_inventory=self.inventory, atom_inventory=self.inventory)
                    for record, arm_report in ((pair.closed, report.closed), (pair.atom_local, report.atom_local)):
                        projections += 1
                        phases.add(arm_report.binding.phase)
                        arms.add(record.arm)
                        self.assertEqual(arm_report.binding.public_messages, record.prefix)
                        self.assertEqual(arm_report.binding.current, target.current_before.encode("ascii"))
                        self.assertIs(arm_report.inventory_completeness_verified, False)
                        self.assertFalse(any(arm_report.science_gates.values()))
                        self.assertTrue(arm_report.supplied_projection_clear, arm_report.scan_report.issues)
        self.assertEqual(projections, 512)
        self.assertEqual(phases, {"SEEK", "PROSPECT", "STEP_CHECK", "READ_CHECK", "CONTINUE"})
        self.assertEqual(arms, {"CLOSED", "ATOM_LOCAL"})

    def test_projection_exact_public_content_not_json_template_or_target(self):
        record = self.pairs[1].atom_local
        report = self.scan(record)
        binding = report.binding
        expected = b"\n".join(message.content.encode("ascii") for message in record.prefix)
        self.assertEqual(binding.projection_bytes, expected)
        self.assertEqual(binding.projection_sha256, sha256(expected).hexdigest())
        self.assertEqual(binding.source_prefix_sha256, record.prefix_sha256)
        self.assertNotEqual(binding.projection_sha256, binding.source_prefix_sha256)
        self.assertEqual(len(expected), record.content_bytes + len(record.prefix) - 1)
        self.assertNotIn(record.unit.target_bytes, expected)
        self.assertNotEqual(expected, targets.messages_bytes(record.prefix))
        self.assertEqual(binding.projection_kind, "PUBLIC_CONTENT_LF_PROJECTION_V1")
        self.assertIs(binding.native_chat_bytes_verified, False)
        for span, message in zip(binding.message_spans, record.prefix):
            self.assertEqual(expected[span.start:span.end], message.content.encode("ascii"))
            self.assertEqual(span.role, message.role)
            self.assertEqual(span.content_sha256, sha256(expected[span.start:span.end]).hexdigest())

    def test_offsets_are_parsed_label_values_not_substring_exemptions(self):
        binding = self.scan(self.pairs[1].closed).binding
        for observation in binding.observations:
            self.assertEqual(binding.projection_bytes[observation.start:observation.end], observation.value)
            self.assertLess(observation.observed_at, binding.decision_index)
        for field in binding.fields:
            observation = next(item for item in binding.observations if item.path == field.path)
            self.assertEqual((field.start, field.end, field.kind),
                             (observation.start, observation.end, observation.exemption_kind))
            self.assertIn("sha256:", field.evidence)
            if field.kind != "protocol":
                self.assertNotIn(b" ", binding.projection_bytes[field.start:field.end])
                self.assertNotIn(b"\n", binding.projection_bytes[field.start:field.end])
        self.assertEqual(len({field.path for field in binding.fields}), len(binding.fields))

    def test_query_did_and_selected_event_receipts(self):
        for ordinal, expected_kind in ((0, "route_query"), (1, "event_did"), (2, "selected_event")):
            report = self.scan(self.pairs[ordinal].atom_local)
            self.assertTrue(report.supplied_projection_clear)
            operand = report.binding.target.split(b" ")[-1]
            hits = [item for item in report.scan_report.receipts if item.category == "operand" and item.value == operand]
            self.assertTrue(hits)
            by_path = {field.path: field for field in report.binding.fields}
            self.assertEqual({by_path[hit.field_path].kind for hit in hits}, {expected_kind})
            self.assertEqual({hit.form for hit in hits}, {"literal", "normalized", "compact"})

    def test_selected_event_is_actually_executed_row_not_all_candidates(self):
        binding = self.scan(self.pairs[2].atom_local).binding
        events = [item for item in binding.observations if item.kind == "event_id"]
        self.assertEqual(len(events), 4)
        selected = [item for item in events if item.exemption_kind == "selected_event"]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].value, binding.implicated_event)
        self.assertFalse(binding.observed_contradiction)
        self.assertTrue(all(item.exemption_kind is None for item in events if item not in selected))

    def test_source_clock_preserves_closed_and_retained_atom_observations(self):
        case, pairs, bindings = self.examples[1, "m0"]
        for target, pair in zip(case.targets, pairs):
            report = source.scan_birth_pair(pair, case, role_tokens=bindings,
                                           closed_inventory=self.inventory, atom_inventory=self.inventory)
            self.assertEqual(report.closed.binding.retained_trace_indices, tuple(range(target.trace_index)))
            for bound in (report.closed.binding, report.atom_local.binding):
                self.assertEqual(bound.decision_index, 2 + 2 * target.trace_index)
                for span in bound.message_spans[2:]:
                    self.assertEqual(span.observed_at, 2 + 2 * span.source_trace_index +
                                     (1 if span.role == "user" else 0))
                self.assertTrue(all(span.observed_at < bound.decision_index for span in bound.message_spans))
                atom = bound is report.atom_local.binding
                task_observed = (1 + 2 * (bound.retained_trace_indices[0] if bound.retained_trace_indices
                                         else target.trace_index)) if atom else 1
                self.assertEqual(bound.message_spans[1].observed_at, task_observed)

    def test_previous_current_stays_observed_but_is_not_latest_exemption(self):
        case, pairs, bindings = self.examples[1, "m0"]
        target_index = next(index for index, target in enumerate(case.targets) if target.phase == "PROSPECT")
        report = source.scan_birth_pair(pairs[target_index], case, role_tokens=bindings,
                                       closed_inventory=self.inventory, atom_inventory=self.inventory)
        for bound in (report.closed.binding, report.atom_local.binding):
            currents = [item for item in bound.observations if item.kind in ("current", "task_current")]
            latest = [item for item in currents if item.is_latest_current]
            self.assertEqual(len(latest), 1)
            self.assertEqual(latest[0].value, case.facts.failed_outcome.encode("ascii"))
            self.assertTrue(all(item.exemption_kind is None for item in currents if not item.is_latest_current))
        previous = next(item for item in report.closed.binding.observations if item.kind == "task_current")
        self.assertEqual(previous.value, case.task.current.encode("ascii"))
        self.assertFalse(previous.is_latest_current)
        self.assertNotEqual(previous.value, report.closed.binding.current)
        self.assertEqual(report.atom_local.binding.message_spans[1].source_trace_index, None)
        self.assertGreater(report.atom_local.binding.message_spans[1].observed_at, previous.observed_at)

    def test_mismatch_recover_exemption_requires_observed_selected_owner(self):
        for key in ((1, "m0"), (5, "m1"), (25, "m0"), (25, "m1"), (27, "m1")):
            case, pairs, bindings = self.examples[key]
            index = next(index for index, target in enumerate(case.targets) if target.phase == "SEEK")
            report = self.scan(pairs[index].atom_local, case=case, bindings=bindings)
            self.assertTrue(report.supplied_projection_clear)
            self.assertTrue(report.binding.observed_contradiction)
            self.assertEqual(report.binding.implicated_event, case.facts.failed_event.encode("ascii"))
            fields = {field.path: field for field in report.binding.fields}
            hits = [hit for hit in report.scan_report.receipts if hit.category == "operand"]
            self.assertTrue(hits)
            self.assertTrue(all(fields[hit.field_path].kind == "event_recover" for hit in hits))
            self.assertTrue(all(fields[hit.field_path].owner == report.binding.implicated_event for hit in hits))
            think = [item for item in report.binding.observations if item.kind == "think_implicated"]
            self.assertEqual(len(think), 1)
            self.assertEqual(think[0].value, report.binding.implicated_event)
            self.assertLess(think[0].observed_at, report.binding.decision_index)

    def test_atom_does_not_infer_contradiction_from_discarded_case_facts(self):
        case, pairs, bindings = self.examples[1, "m0"]
        index = next(index for index, target in enumerate(case.targets) if target.phase == "PROSPECT")
        report = self.scan(pairs[index].atom_local, case=case, bindings=bindings)
        self.assertIsNone(report.binding.implicated_event)
        self.assertFalse(report.binding.observed_contradiction)
        self.assertIsNotNone(case.facts.failed_event)
        self.assertNotEqual(case.facts.failed_outcome, case.facts.failed_prediction)

    def test_miss_and_irrelevant_read_check_bind_issued_query_without_corrective_leak(self):
        for number in (9, 11):
            case, pairs, bindings = self.examples[number, "m0"]
            index = next(index for index, target in enumerate(case.targets) if target.phase == "READ_CHECK")
            report = self.scan(pairs[index].atom_local, case=case, bindings=bindings)
            self.assertTrue(report.supplied_projection_clear)
            self.assertEqual(report.binding.implicated_query, case.facts.failed_query.encode("ascii"))
            self.assertIsNone(report.binding.implicated_event)
            self.assertNotIn(case.facts.corrective_query.encode("ascii"), report.binding.projection_bytes)
            self.assertTrue(any(field.kind == "issued_query" for field in report.binding.fields))
            self.assertFalse(any(field.kind == "route_query" for field in report.binding.fields))

    def test_atom_continue_task_only_current_and_protocol_stop_exception(self):
        report = self.scan(self.pairs[-1].atom_local)
        self.assertTrue(report.supplied_projection_clear)
        self.assertEqual(len(report.binding.public_messages), 2)
        self.assertEqual(report.binding.retained_trace_indices, ())
        self.assertIsNone(report.binding.implicated_event)
        self.assertEqual(report.binding.target, b"STOP")
        full_hits = [hit for hit in report.scan_report.receipts if hit.category == "full_target"]
        self.assertTrue(full_hits)
        for hit in full_hits:
            self.assertEqual(hit.field_path, "/messages/0/protocol")
            self.assertEqual(report.binding.projection_bytes[hit.start:hit.end], b"STOP")

    def test_authentic_closed_got_occurrence_allowed_without_relabeling_current(self):
        case, pairs, bindings = self.examples[4, "m0"]
        report = self.scan(pairs[-1].closed, case=case, bindings=bindings)
        self.assertTrue(report.supplied_projection_clear)
        got = [item for item in report.binding.observations
               if item.kind == "event_got" and item.value == report.binding.current]
        self.assertTrue(got)
        self.assertTrue(all(item.exemption_kind == "event_got" and item.origin == "service"
                            and item.owner == report.binding.implicated_event for item in got))
        self.assertTrue(any(hit.category == "operand" and any(hit.field_path == item.path for item in got)
                            for hit in report.scan_report.receipts))
        atom = self.scan(pairs[-1].atom_local, case=case, bindings=bindings)
        self.assertTrue(atom.supplied_projection_clear)

    def test_authentic_closed_route_query_allowed_without_retyping_as_actor(self):
        case, pairs, bindings = self.examples[11, "m0"]
        report = self.scan(pairs[0].closed, case=case, bindings=bindings)
        operand = report.binding.implicated_query
        returned = [item for item in report.binding.observations if item.kind == "route_query" and item.value == operand]
        issued = [item for item in report.binding.observations if item.kind == "issued_query" and item.value == operand]
        self.assertEqual(len(returned), 1)
        self.assertEqual(len(issued), 1)
        self.assertEqual(returned[0].origin, "service")
        self.assertEqual(returned[0].exemption_kind, "route_query")
        self.assertEqual(issued[0].origin, "actor")
        self.assertLess(returned[0].observed_at, issued[0].observed_at)
        self.assertTrue(any(hit.category == "operand" and hit.start == returned[0].start
                            for hit in report.scan_report.receipts))
        self.assertTrue(any(hit.category == "operand" and hit.field_path == issued[0].path
                            for hit in report.scan_report.receipts))
        self.assertTrue(report.supplied_projection_clear)

    def test_authentic_causal_service_occurrences_never_waive_explicit_future_ids(self):
        for number, ordinal, kind in ((11, 0, "route_query"), (4, -1, "event_got")):
            case, pairs, bindings = self.examples[number, "m0"]
            original = self.scan(pairs[ordinal].closed, case=case, bindings=bindings)
            operand = original.binding.target.split(b" ")[-1]
            report = self.scan(pairs[ordinal].closed, case=case, bindings=bindings,
                               future_identifiers=(operand,))
            service_fields = [field for field in report.binding.fields if field.kind == kind]
            self.assertEqual(report.binding, original.binding)
            self.assertFalse(report.supplied_projection_clear)
            self.assertTrue(any(hit.category == "future_identifier" and any(
                hit.start == field.start and hit.end == field.end for field in service_fields)
                for hit in report.scan_report.issues))

    def test_authentic_shared_got_v2_acceptance_preserves_v1_historical_receipt(self):
        """V1 rejected p21/m1 CLOSED CONTINUE at 3503:3520 in all three forms."""
        case, pairs, bindings = self.examples[21, "m1"]
        report = self.scan(pairs[-1].closed, case=case, bindings=bindings)
        got = [item for item in report.binding.observations
               if item.kind == "event_got" and item.value == report.binding.current]
        self.assertEqual(len(got), 2)
        selected = next(item for item in got if item.owner == report.binding.implicated_event)
        foreign = next(item for item in got if item.owner != report.binding.implicated_event)
        self.assertEqual((selected.origin, foreign.origin), ("service", "service"))
        self.assertTrue(report.supplied_projection_clear)
        self.assertEqual(foreign.owner, b"M2AE_RZMUMNDMYPD7")
        self.assertEqual(selected.owner, b"M2AE_API5S6JKDJMM")
        self.assertEqual(foreign.path, "/messages/5/SERVICE/EVENTS/rows/0/GOT")
        self.assertEqual(foreign.evidence,
                         "source-message:5:sha256:2d331f85c538cc3fba6599330528294bb6b9696f6ee2e34585c0d7350c427810")
        shared_receipts = tuple(hit for hit in report.scan_report.receipts
                                if hit.category == "operand" and hit.field_path == foreign.path)
        historical_v1 = tuple(scanner.Occurrence("operand", b"M2AN_HC2AJ6URWPYW", form, 3503, 3520)
                              for form in ("literal", "normalized", "compact"))
        self.assertEqual(tuple(replace(hit, field_path=None, evidence=None) for hit in shared_receipts), historical_v1)
        self.assertTrue(all(hit.evidence == foreign.evidence for hit in shared_receipts))
        self.assertTrue(any(hit.category == "operand" and hit.field_path == selected.path
                            for hit in report.scan_report.receipts))
        self.assertTrue(self.scan(pairs[-1].atom_local, case=case, bindings=bindings).supplied_projection_clear)

    def test_shared_got_still_rejects_future_routes_semantics_and_forged_response(self):
        case, pairs, bindings = self.examples[21, "m1"]
        record = pairs[-1].closed
        original = self.scan(record, case=case, bindings=bindings)
        foreign = next(item for item in original.binding.observations if item.kind == "event_got"
                       and item.value == original.binding.current and item.owner != original.binding.implicated_event)
        for category, inventory in (("future_identifier", {"future_identifiers": (foreign.value,)}),
                                    ("registered_route", {"registered_routes": (foreign.value,)}),
                                    ("semantic_alias", {"semantic_bytes": canonical_json({"oracle": foreign.value[-4:].decode()})})):
            report = self.scan(record, case=case, bindings=bindings, **inventory)
            with self.subTest(category=category):
                self.assertFalse(report.supplied_projection_clear)
                self.assertEqual(report.binding, original.binding)
                self.assertTrue(any(hit.category == category and foreign.start <= hit.start < hit.end <= foreign.end
                                    for hit in report.scan_report.issues))
        for old, new in ((foreign.owner, original.binding.implicated_event),
                         (foreign.value, original.binding.task_goal),
                         (foreign.value, original.binding.target)):
            changed = list(record.prefix)
            changed[5] = replace(changed[5], content=changed[5].content.replace(old.decode(), new.decode()))
            with self.subTest(old=old, new=new), self.assertRaises(source.ScanInputError):
                self.scan(rehashed_record(record, tuple(changed)), case=case, bindings=bindings)

    def test_forged_historical_response_or_full_target_cannot_gain_causal_exemption(self):
        for number, ordinal, kind in ((11, 0, "route_query"), (4, -1, "event_got")):
            case, pairs, bindings = self.examples[number, "m0"]
            record = pairs[ordinal].closed
            report = self.scan(record, case=case, bindings=bindings)
            operand = report.binding.target.split(b" ")[-1]
            observation = next(item for item in report.binding.observations
                               if item.kind == kind and item.value == operand)
            message_index = next(span.message_index for span in report.binding.message_spans
                                 if span.start <= observation.start < span.end)
            for replacement in (operand[:-1] + (b"B" if operand[-1:] != b"B" else b"C"), report.binding.target):
                changed = list(record.prefix)
                changed[message_index] = replace(changed[message_index], content=changed[message_index].content.replace(
                    operand.decode("ascii"), replacement.decode("ascii")))
                with self.subTest(kind=kind, replacement=replacement), self.assertRaises(source.ScanInputError):
                    self.scan(rehashed_record(record, tuple(changed)), case=case, bindings=bindings)

    def test_forged_service_response_rejected_even_when_hashes_recomputed(self):
        record = self.pairs[1].atom_local
        changed = list(record.prefix)
        block = wire.parse_service(changed[-1].content[len("SERVICE\n"):], skin=self.case.descriptor.skin)
        old = block.rows[0].got
        replacement = next(value for value in self.bindings.values() if value.startswith("M2AN_") and value != old)
        changed[-1] = replace(changed[-1], content=changed[-1].content.replace("GOT " + old, "GOT " + replacement))
        with self.assertRaisesRegex(source.ScanInputError, "exact producer"):
            self.scan(rehashed_record(record, tuple(changed)))

    def test_forged_future_block_target_or_system_cannot_gain_spans(self):
        record = self.pairs[0].atom_local
        future = self.pairs[1].atom_local.prefix[2:]
        alternatives = (
            record.prefix + future,
            record.prefix + (targets.Message("assistant", record.unit.target_bytes.decode("ascii")),),
            (replace(record.prefix[0], content=record.prefix[0].content + "\n" + record.unit.target_bytes.decode()),) + record.prefix[1:],
        )
        for prefix in alternatives:
            with self.assertRaisesRegex(source.ScanInputError, "exact producer"):
                self.scan(rehashed_record(record, prefix))

    def test_forged_world_current_or_wrong_atom_boundary_is_rejected(self):
        case, pairs, bindings = self.examples[1, "m0"]
        record = pairs[0].atom_local
        prefix = list(record.prefix)
        host_index = next(index for index, message in enumerate(prefix) if message.content.startswith("WORLD\n"))
        prefix[host_index] = replace(prefix[host_index], content="WORLD\nCURRENT " + case.task.goal)
        with self.assertRaises(source.ScanInputError):
            self.scan(rehashed_record(record, tuple(prefix)), case=case, bindings=bindings)
        index = next(index for index, target in enumerate(case.targets) if target.phase == "PROSPECT")
        record = pairs[index].atom_local
        prefix = record.prefix[:1] + (replace(record.prefix[1], content=case.task_text),) + record.prefix[2:]
        with self.assertRaises(source.ScanInputError):
            self.scan(rehashed_record(record, prefix), case=case, bindings=bindings)

    def test_forged_producer_trace_cannot_validate_itself(self):
        record = self.pairs[1].atom_local
        turn_index = self.case.targets[1].trace_index - 1
        turn = self.case.trace[turn_index]
        trace = self.case.trace[:turn_index] + (replace(turn, response="SERVICE\nMISS"),) + self.case.trace[turn_index + 1:]
        forged_case = replace(self.case, trace=trace)
        prefix = record.prefix[:-1] + (targets.Message("user", "SERVICE\nMISS"),)
        with self.assertRaisesRegex(source.ScanInputError, "case validation failed"):
            self.scan(rehashed_record(record, prefix), case=forged_case)

    def test_fields_or_bound_objects_are_not_accepted_as_input_authority(self):
        record = self.pairs[1].atom_local
        report = self.scan(record)
        forged = replace(report.binding, fields=())
        with self.assertRaisesRegex(source.ScanInputError, "ArmRecord required"):
            self.scan(forged)
        for argument, value in (("fields", report.binding.fields), ("current", self.case.task.goal.encode()),
                                 ("observed_contradiction", True), ("implicated_event", b"M2AE_BBBBBBBBBBBB")):
            with self.assertRaises(TypeError):
                self.scan(record, **{argument: value})

    def test_forged_future_classification_is_not_waived_by_public_did_span(self):
        record = self.pairs[1].atom_local
        operand = record.unit.operand.encode("ascii")
        report = self.scan(record, future_identifiers=(operand,))
        self.assertFalse(report.supplied_projection_clear)
        self.assertEqual(report.future_identifiers, (operand,))
        self.assertTrue(any(hit.category == "operand" for hit in report.scan_report.receipts))
        self.assertTrue(any(hit.category == "future_identifier" for hit in report.scan_report.issues))

    def test_future_task_facts_get_only_exact_task_field_exceptions(self):
        record = self.pairs[-1].atom_local
        report = self.scan(record, future_identifiers=(self.case.task.start.encode(), self.case.task.goal.encode()))
        self.assertTrue(report.supplied_projection_clear)
        receipts = [hit for hit in report.scan_report.receipts if hit.category == "future_identifier"]
        self.assertTrue(receipts)
        self.assertTrue(all("/TASK/" in hit.field_path for hit in receipts))

    def test_registered_route_passes_unchanged_without_field_exception(self):
        record = self.pairs[1].atom_local
        action = next(message.content.encode("ascii") for message in record.prefix if message.role == "assistant")
        report = self.scan(record, registered_routes=(action,))
        self.assertEqual(report.registered_routes, (action,))
        self.assertFalse(report.supplied_projection_clear)
        self.assertTrue(any(hit.category == "registered_route" for hit in report.scan_report.issues))

    def test_semantic_inventory_never_enters_actor_projection(self):
        record = self.pairs[0].atom_local
        report = self.scan(record)
        self.assertEqual(report.semantic_sha256, sha256(SEMANTIC).hexdigest())
        self.assertNotIn(b"privatebindingmetadata", report.binding.projection_bytes)
        self.assertNotIn(b"EVALUATORPAYLOADNOTINPUBLICPREFIX", report.binding.projection_bytes)
        self.assertNotIn(record.unit.unit_id.encode(), report.binding.projection_bytes)
        self.assertTrue(any(b"privatebindingmetadata" in value for value in report.scan_report.aliases))
        changed = self.scan(record, semantic_bytes=canonical_json({"oracle": {"privatebindingmetadata": "DIFFERENTEVALUATORPAYLOAD"}}))
        self.assertEqual(changed.binding.projection_bytes, report.binding.projection_bytes)
        self.assertEqual(changed.binding.public_messages, record.prefix)

    def test_semantic_alias_collisions_remain_findings_not_exemptions(self):
        record = self.pairs[0].atom_local
        partial_identifier = self.case.task.goal[:16]
        semantic = canonical_json({"oracle": {"privatebindingmetadata": partial_identifier}})
        report = self.scan(record, semantic_bytes=semantic)
        self.assertFalse(report.supplied_projection_clear)
        self.assertTrue(any(hit.category == "semantic_alias" for hit in report.scan_report.issues))
        self.assertEqual(report.binding.projection_bytes, b"\n".join(message.content.encode() for message in record.prefix))

    def test_all_three_inventories_must_be_supplied_explicitly(self):
        arguments = dict(role_tokens=self.bindings, semantic_bytes=SEMANTIC, future_identifiers=(), registered_routes=())
        for missing in ("semantic_bytes", "future_identifiers", "registered_routes"):
            reduced = dict(arguments)
            del reduced[missing]
            with self.subTest(missing=missing), self.assertRaises(TypeError):
                source.scan_birth_arm(self.pairs[0].atom_local, self.case, **reduced)
        for name, value in (("semantic_bytes", None), ("semantic_bytes", "{}"),
                            ("future_identifiers", None), ("future_identifiers", []),
                            ("registered_routes", None), ("registered_routes", [b"STOP"])):
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                self.scan(self.pairs[0].atom_local, **{name: value})

    def test_explicit_empty_inventories_never_certify_all_clear_or_completeness(self):
        report = self.scan(self.pairs[0].atom_local, semantic_bytes=b"{}")
        self.assertTrue(report.supplied_projection_clear)
        self.assertFalse(hasattr(report, "passed"))
        self.assertIs(report.inventory_completeness_verified, False)
        self.assertFalse(any(report.science_gates.values()))
        self.assertIn("completeness", " ".join(report.limitations))

    def test_paired_inventories_are_separate_and_not_silently_shared(self):
        pair = self.pairs[1]
        atom_inventory = source.ScanInventory(SEMANTIC, (pair.atom_local.unit.operand.encode(),), ())
        report = source.scan_birth_pair(pair, self.case, role_tokens=self.bindings,
                                       closed_inventory=self.inventory, atom_inventory=atom_inventory)
        self.assertTrue(report.closed.supplied_projection_clear)
        self.assertFalse(report.atom_local.supplied_projection_clear)
        with self.assertRaises(ValueError):
            source.scan_birth_pair(pair, self.case, role_tokens=self.bindings,
                                   closed_inventory=None, atom_inventory=atom_inventory)

    def test_coupled_units_hashes_and_source_records_cannot_be_forged(self):
        pair = self.pairs[0]
        alternatives = (
            replace(pair, atom_local=replace(pair.atom_local, unit=replace(pair.atom_local.unit))),
            replace(pair, closed=replace(pair.closed, prefix_sha256="0" * 64)),
            replace(pair, atom_local=replace(pair.atom_local, content_bytes=0)),
            replace(pair, atom_local=replace(pair.atom_local, arm="CLOSED")),
            replace(pair, atom_local=self.pairs[1].atom_local),
        )
        for changed in alternatives:
            with self.assertRaises(source.ScanInputError):
                source.scan_birth_pair(changed, self.case, role_tokens=self.bindings,
                                       closed_inventory=self.inventory, atom_inventory=self.inventory)

    def test_source_roles_must_be_supplied_and_valid(self):
        bindings = dict(self.bindings)
        del bindings[next(iter(bindings))]
        with self.assertRaises(source.ScanInputError):
            self.scan(self.pairs[0].atom_local, bindings=bindings)
        with self.assertRaises(source.ScanInputError):
            source.scan_birth_arm(self.pairs[0].atom_local, self.case, role_tokens=None,
                                  semantic_bytes=SEMANTIC, future_identifiers=(), registered_routes=())

    def test_scanner_receipt_and_public_field_integrity_are_preserved(self):
        report = self.scan(self.pairs[1].closed)
        bound = report.binding
        direct = scanner.scan_forward_targets(bound.projection_bytes, target=bound.target, phase=bound.phase,
            decision_index=bound.decision_index, semantic_bytes=SEMANTIC, fields=bound.fields,
            future_identifiers=(), registered_routes=(), task_start=bound.task_start, task_goal=bound.task_goal,
            current=bound.current, implicated_query=bound.implicated_query, implicated_event=bound.implicated_event,
            observed_contradiction=bound.observed_contradiction)
        self.assertEqual(report.scan_report, direct)
        for hit in direct.receipts:
            field = next(field for field in bound.fields if field.path == hit.field_path)
            self.assertEqual(field.evidence, hit.evidence)
            self.assertTrue(field.start <= hit.start < hit.end <= field.end)

    def test_outputs_frozen_flags_false_and_no_native_or_io_paths(self):
        with patch.object(wire, "allocate_opaque_namespace", side_effect=AssertionError("no allocation")), \
                patch("builtins.open", side_effect=AssertionError("no files")), \
                patch("pathlib.Path.open", side_effect=AssertionError("no files")), \
                patch("socket.socket", side_effect=AssertionError("no network")):
            report = self.scan(self.pairs[1].atom_local)
        with self.assertRaises(FrozenInstanceError):
            report.binding.fields = ()
        with self.assertRaises(TypeError):
            report.science_gates["GO_CLAIM"] = True
        for name in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"):
            self.assertIs(getattr(source, name), False)
            self.assertIs(report.science_gates[name], False)
        self.assertEqual(report.status, "PARTIAL_SOURCE_ONLY")

    def test_contract_pins_match_read_only_documents(self):
        root = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
        for version, digest in source.CONTRACT_HASHES.items():
            name = {"clarification_v1": "2026-09-13_stage2a_builder_source_clarifications_v1.md",
                    "causal_occurrence_v1": "2026-09-13_stage2a_causal_occurrence_clarifications_v1.md",
                    "causal_occurrence_v2": "2026-09-13_stage2a_causal_occurrence_clarifications_v2.md"}.get(
                        version, f"2026-09-13_m_combine4_stage2a_binding_successor_{version}.md")
            self.assertEqual(sha256((root / name).read_bytes()).hexdigest(), digest)
        self.assertEqual(source.CONTRACT_HASHES["causal_occurrence_v1"], scanner.CAUSAL_OCCURRENCE_SHA256)
        self.assertEqual(source.CONTRACT_HASHES["causal_occurrence_v2"], scanner.CAUSAL_OCCURRENCE_V2_SHA256)


if __name__ == "__main__":
    unittest.main()
