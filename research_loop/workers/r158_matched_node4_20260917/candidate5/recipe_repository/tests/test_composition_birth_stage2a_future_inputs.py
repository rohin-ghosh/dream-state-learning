"""Synthetic CPU future-ID checks; no canonical material or full inventory gate."""

from collections import Counter
from dataclasses import FrozenInstanceError, replace
from functools import lru_cache
from hashlib import sha256
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_future_inputs as source
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs
from organism_v6 import composition_birth_stage2a_targets as targets
from tests.test_composition_birth_stage2a_birth import synthetic_bindings


MASTER = b"synthetic-retained-future-inputs-only"


@lru_cache(maxsize=32)
def fixture(number):
    bindings = synthetic_bindings(number)
    pair = birth.build_birth_pair(world=f"p{number:02d}", role_tokens=bindings, display_master=MASTER)
    records = tuple(targets.serialize_birth_case(case, role_tokens=bindings) for case in pair.cases)
    return pair, records


def arguments(number=0, member=0, ordinal=0, arm="CLOSED"):
    pair, records = fixture(number)
    paired = records[member][ordinal]
    return dict(case=pair.cases[member], record=paired.closed if arm == "CLOSED" else paired.atom_local,
                role_tokens=pair.role_tokens, display_master=MASTER)


def derive(number=0, member=0, ordinal=0, arm="CLOSED"):
    return source.derive_birth_future_inputs(**arguments(number, member, ordinal, arm))


def scan_future(result, prefix=None):
    """Only exercise the future category, not semantic/route completeness."""
    binding = result.binding
    return scanner.scan_forward_targets(
        binding.projection_bytes if prefix is None else prefix,
        target=binding.target, phase=binding.phase, decision_index=binding.decision_index,
        semantic_bytes=b"{}", registered_routes=(), future_identifiers=tuple(sorted(result.future_identifiers)),
        fields=binding.fields, task_start=binding.task_start, task_goal=binding.task_goal,
        current=binding.current, implicated_query=binding.implicated_query,
        implicated_event=binding.implicated_event, observed_contradiction=binding.observed_contradiction,
    )


class FutureInputTests(unittest.TestCase):
    def test_whole_world_counts_all_birth_subtypes_and_families(self):
        for number in range(32):
            with self.subTest(world=number):
                result = derive(number)
                descriptor = result.source.case.descriptor
                hubs = 24 if descriptor.family == "A" else 6
                states = hubs + 1
                mismatch = descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH"
                strict_miss = descriptor.recovery_subtype == "STRICT_MISS"
                counts = Counter(token[:5] for token in result.candidates)
                self.assertEqual(counts, {
                    b"M2AQ_": 120 * states + (8 if mismatch else 2 if strict_miss else 0),
                    b"M2AE_": 96 * states + (8 if mismatch else 0),
                    b"M2AP_": 96 * states + (8 if mismatch else 0),
                    b"M2AN_": 48 + (hubs if descriptor.bucket % 2 else 0) + (4 if mismatch else 0),
                })
                self.assertEqual(result.future_identifiers, result.candidates - result.disclosed)
                self.assertEqual(set(result.candidate_provenance), result.candidates)
                self.assertEqual(set(result.disclosure_provenance), result.disclosed)

    def test_both_members_all_decisions_both_arms(self):
        for number in (0, 2, 9, 11, 25, 29):
            for member in (0, 1):
                expected_candidates = None
                for ordinal in range(4):
                    for arm in ("CLOSED", "ATOM_LOCAL"):
                        with self.subTest(world=number, member=member, ordinal=ordinal, arm=arm):
                            result = derive(number, member, ordinal, arm)
                            if expected_candidates is None:
                                expected_candidates = result.candidates
                            self.assertEqual(result.candidates, expected_candidates)
                            self.assertTrue(result.disclosed <= result.candidates)
                            for entries in result.disclosure_provenance.values():
                                self.assertTrue(all(entry.source_trace_index in result.binding.retained_trace_indices
                                                    for entry in entries))

    def test_unregistered_recover_and_strict_miss_queries_remain_candidates(self):
        for number in (0, 9, 19):
            result = derive(number)
            tokens = result.source.role_tokens
            unregistered = {token.encode("ascii") for role, token in tokens.items()
                            if role.endswith("/query") and "READ RELATION " + token
                            not in result.source.case.construction.registry}
            self.assertTrue(unregistered)
            self.assertTrue(unregistered <= result.candidates)
            self.assertTrue(unregistered - result.disclosed <= result.future_identifiers)
            if number in (9, 19):
                missed = result.source.case.facts.failed_query.encode("ascii")
                self.assertIn(missed, unregistered)
                self.assertIn(missed, result.disclosed)
                self.assertTrue(any(entry.origin == "actor" for entry in result.disclosure_provenance[missed]))

    def test_omitted_directory_is_not_inherited_but_retained_actor_query_is_disclosed(self):
        closed = derive(ordinal=1)
        atom = derive(ordinal=1, arm="ATOM_LOCAL")
        case = closed.source.case
        directory = case.construction.blocks["READ INDEX " + case.task.start]
        omitted = next(row.query.encode("ascii") for row in directory.rows
                       if row.query != case.facts.selected_query)
        issued = case.facts.selected_query.encode("ascii")
        self.assertEqual(closed.candidates, atom.candidates)
        self.assertIn(omitted, closed.disclosed)
        self.assertIn(omitted, atom.future_identifiers)
        self.assertNotIn(omitted, atom.disclosure_provenance)
        self.assertIn(issued, atom.disclosed)
        self.assertTrue(all(entry.origin == "actor" for entry in atom.disclosure_provenance[issued]))

    def test_task_facts_do_not_disclose_or_globally_exempt_ids(self):
        result = derive(ordinal=3, arm="ATOM_LOCAL")
        self.assertEqual(result.disclosed, frozenset())
        self.assertEqual(result.future_identifiers, result.candidates)
        goal = result.binding.task_goal
        self.assertIn(goal, result.future_identifiers)
        report = scan_future(result)
        self.assertTrue(report.passed)
        self.assertTrue(any(entry.category == "future_identifier" and entry.value == goal
                            for entry in report.receipts))
        injected = scan_future(result, result.binding.projection_bytes + b"\nprivate=" + goal)
        self.assertTrue(any(entry.category == "future_identifier" and entry.value == goal
                            for entry in injected.issues))

    def test_off_trace_future_ids_not_dropped_or_laundered_by_prose(self):
        result = derive()
        case = result.source.case
        entire_trace = "\n".join(turn.action + "\n" + turn.response for turn in case.trace).encode("ascii")
        for kind in (b"M2AQ_", b"M2AE_", b"M2AP_"):
            token = next(token for token in sorted(result.future_identifiers)
                         if token.startswith(kind) and token not in entire_trace)
            report = scan_future(result, result.binding.projection_bytes + b"\nunrelated=" + token)
            self.assertFalse(report.passed)
            self.assertEqual({entry.form for entry in report.issues
                              if entry.category == "future_identifier" and entry.value == token},
                             {"literal", "normalized", "compact"})

    def test_prediction_and_effective_destinations_preserve_distinct_origins(self):
        result = derive(1)
        facts = result.source.case.facts
        prediction = facts.failed_prediction.encode("ascii")
        outcome = facts.failed_outcome.encode("ascii")
        self.assertNotEqual(prediction, outcome)
        self.assertTrue({prediction, outcome} <= result.disclosed)
        self.assertTrue(any(entry.source_path[-1] == "got" for entry in result.candidate_provenance[prediction]))
        self.assertTrue(any(entry.source_path[2] == "world_edges"
                            for entry in result.candidate_provenance[outcome] if len(entry.source_path) > 2))
        self.assertTrue(any(entry.origin == "host" for entry in result.disclosure_provenance[outcome]))

    def test_exact_source_paths_projection_spans_and_immutable_receipts(self):
        result = derive(1)
        self.assertEqual(result.disposition_sha256,
                         "6f442bd1af56ca5a0b925ae56925b53207cfa9e1ef72f0c25315956da9987154")
        self.assertEqual(sha256(result.source.provenance_bytes).hexdigest(), result.source.provenance_sha256)
        self.assertEqual(sha256(result.binding.projection_bytes).hexdigest(), result.binding.projection_sha256)
        for token, entries in result.candidate_provenance.items():
            for entry in entries:
                path = entry.source_path
                self.assertEqual(result.source.role_tokens[entry.role_key].encode("ascii"), token)
                if path[0] == "role_tokens":
                    self.assertEqual(path, ("role_tokens", entry.role_key))
                elif path[2] == "blocks":
                    block = result.source.case.construction.blocks[path[3]]
                    self.assertEqual(block.rows[int(path[5])].got.encode("ascii"), token)
                else:
                    self.assertEqual(path[:3], ("case", "construction", "world_edges"))
                    self.assertEqual(result.source.case.construction.world_edges[path[3], path[4]].encode("ascii"), token)
        for token, entries in result.disclosure_provenance.items():
            for entry in entries:
                self.assertIn(entry, result.binding.observations)
                self.assertEqual(result.binding.projection_bytes[entry.start:entry.end], token)
                self.assertLess(entry.observed_at, result.binding.decision_index)
                self.assertNotIn(entry.origin, ("task", "system"))
        with self.assertRaises(FrozenInstanceError):
            result.candidates = frozenset()
        with self.assertRaises(TypeError):
            result.candidate_provenance[b"fake"] = ()
        with self.assertRaises(TypeError):
            result.disclosure_provenance[b"fake"] = ()
        with self.assertRaises(FrozenInstanceError):
            next(iter(result.candidate_provenance.values()))[0].role_key = "fake"
        with self.assertRaises(FrozenInstanceError):
            next(iter(result.disclosure_provenance.values()))[0].evidence = "fake"

    def test_rebuilds_every_call_without_trusting_mutable_caller_maps(self):
        inputs = arguments()
        tokens = dict(inputs["role_tokens"])
        inputs["role_tokens"] = tokens
        with patch.object(source_inputs, "validate_birth_source", wraps=source_inputs.validate_birth_source) as validator:
            with patch.object(birth, "build_birth_pair", wraps=birth.build_birth_pair) as constructor:
                first = source.derive_birth_future_inputs(**inputs)
                second = source.derive_birth_future_inputs(**inputs)
        self.assertEqual(validator.call_count, 2)
        self.assertEqual(constructor.call_count, 2)
        self.assertEqual(first, second)
        tokens.clear()
        self.assertTrue(first.source.role_tokens)
        self.assertTrue(first.candidates)

    def test_forged_hidden_source_record_bindings_and_master_rejected(self):
        inputs = arguments()
        case = inputs["case"]
        used = {(turn.current_before, wire.parse_action(turn.action).operand) for turn in case.trace
                if wire.parse_action(turn.action).operation == "STEP"}
        edges = dict(case.construction.world_edges)
        key = next(key for key in edges if key not in used)
        edges[key] = case.task.start
        forged_case = replace(case, construction=replace(case.construction, world_edges=edges))
        record = inputs["record"]
        prefix = (replace(record.prefix[0], content=record.prefix[0].content + "\nprivate metadata"),) + record.prefix[1:]
        raw = targets.messages_bytes(prefix)
        forged_record = replace(record, prefix=prefix, prefix_sha256=sha256(raw).hexdigest(),
                                content_bytes=sum(len(message.content.encode("ascii")) for message in prefix),
                                serialized_bytes=len(raw))
        for overrides in ({"case": forged_case}, {"record": forged_record},
                          {"record": arguments(2)["record"]}, {"role_tokens": {}},
                          {"display_master": MASTER + b"different"}):
            with self.subTest(overrides=tuple(overrides)), self.assertRaises(source_inputs.SourceInputError):
                source.derive_birth_future_inputs(**dict(inputs, **overrides))

    def test_inputs_are_explicit_no_inventory_receipt_or_flag_extension(self):
        inputs = arguments()
        for key in inputs:
            with self.subTest(missing=key), self.assertRaises(TypeError):
                source.derive_birth_future_inputs(**{name: value for name, value in inputs.items() if name != key})
        for key in ("future_identifiers", "semantic_bytes", "registered_routes", "validated_source",
                    "binding", "inventory_complete"):
            with self.subTest(extra=key), self.assertRaises(TypeError):
                source.derive_birth_future_inputs(**dict(inputs, **{key: ()}))

    def test_real_a_future_inventory_exceeds_4096_without_truncation(self):
        result = derive()
        self.assertGreater(len(result.future_identifiers), 4096)
        self.assertLessEqual(len(result.future_identifiers), scanner.BOUNDS["future_identifiers"])
        self.assertTrue(scan_future(result).passed)
        with patch.object(scanner, "BOUNDS", dict(scanner.BOUNDS, future_identifiers=4096)):
            with self.assertRaisesRegex(source.FutureInputError, "future_identifier_bound_exceeded"):
                derive()

    def test_no_full_inventory_or_readiness_claim(self):
        result = derive()
        self.assertEqual(result.status, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(result.inventory_completeness_verified)
        self.assertFalse(result.native_chat_bytes_verified)
        self.assertFalse(any(result.science_gates.values()))
        for name in ("semantic_bytes", "registered_routes", "supplied_projection_clear"):
            self.assertFalse(hasattr(result, name))
        for name in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"):
            self.assertFalse(getattr(source, name))


if __name__ == "__main__":
    unittest.main()
