"""Bounded synthetic constructor checks, not scientific semantic inventory tests."""

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import json
from types import MappingProxyType
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_source_inputs as source
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_birth import changed_construction, synthetic_bindings


MASTER = b"synthetic-full-constructor-source-only"


def rehashed_record(record, prefix):
    raw = targets.messages_bytes(prefix)
    return replace(record, prefix=prefix, prefix_sha256=sha256(raw).hexdigest(),
                   content_bytes=sum(len(message.content.encode("ascii")) for message in prefix),
                   serialized_bytes=len(raw))


class FullConstructorSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bindings = {number: synthetic_bindings(number) for number in range(32)}
        cls.roster = {number: birth.build_birth_pair(world=f"p{number:02d}", role_tokens=cls.bindings[number],
                                                    display_master=MASTER) for number in range(32)}
        cls.records = {(number, case.descriptor.member): targets.serialize_birth_case(
            case, role_tokens=cls.bindings[number]) for number, pair in cls.roster.items() for case in pair.cases}

    def setUp(self):
        self.case = self.roster[0].cases[0]
        self.record = self.records[0, "m0"][0].closed
        self.tokens = self.bindings[0]

    def validate(self, **overrides):
        inputs = dict(case=self.case, record=self.record, role_tokens=self.tokens, display_master=MASTER)
        inputs.update(overrides)
        return source.validate_birth_source(**inputs)

    def test_full_64_case_roster_both_arms(self):
        seen = set()
        with patch.object(birth, "build_birth_pair", wraps=birth.build_birth_pair) as constructor:
            for number, pair in self.roster.items():
                for case in pair.cases:
                    decision = (number + int(case.descriptor.member[-1])) % 4
                    paired = self.records[number, case.descriptor.member][decision]
                    for record in (paired.closed, paired.atom_local):
                        with self.subTest(world=pair.world, member=case.descriptor.member, arm=record.arm):
                            result = self.validate(case=case, record=record, role_tokens=self.bindings[number])
                            self.assertEqual(result.case, case)
                            self.assertEqual(result.record, record)
                            self.assertIsNot(result.case, case)
                            self.assertIsNot(result.record, record)
                            self.assertFalse(any(result.science_gates.values()))
                            seen.add((pair.world, case.descriptor.member, record.arm))
            self.assertEqual(constructor.call_count, 128)
            self.assertTrue(all(call.kwargs["display_master"] == MASTER for call in constructor.call_args_list))
        self.assertEqual(len(seen), 128)

    def test_every_rendered_record_and_fingerprint_identity(self):
        fingerprints = set()
        case_fingerprints = set()
        for paired in self.records[0, "m0"]:
            for record in (paired.closed, paired.atom_local):
                result = self.validate(record=record)
                self.assertEqual(result.record, record)
                fingerprints.add(result.record_sha256)
                case_fingerprints.add(result.case_sha256)
                provenance = json.loads(result.provenance_bytes)
                self.assertEqual(canonical_json(provenance), result.provenance_bytes)
                self.assertEqual(provenance["world"], "p00")
                self.assertEqual(provenance["member"], "m0")
                self.assertEqual(provenance["unit_id"], record.unit.unit_id)
                self.assertEqual(provenance["arm"], record.arm)
                self.assertEqual(provenance["schema"], source.SCHEMA_VERSION)
                self.assertEqual(provenance["constructor"], source.CONSTRUCTOR_API)
                self.assertEqual(provenance["contract_hashes"], dict(source.CONTRACT_HASHES))
                for name in ("case_sha256", "record_sha256", "role_tokens_sha256", "display_master_sha256"):
                    self.assertEqual(provenance[name], getattr(result, name))
                self.assertEqual(result.provenance_sha256, sha256(result.provenance_bytes).hexdigest())
                self.assertEqual(result.display_master_sha256, sha256(MASTER).hexdigest())
                self.assertEqual(result.role_tokens_sha256, sha256(canonical_json(self.tokens)).hexdigest())
        self.assertEqual(len(fingerprints), 8)
        self.assertEqual(len(case_fingerprints), 1)

    def test_hidden_registry_change_rejected_despite_oracle_replay(self):
        requests = {turn.action for turn in self.case.trace}
        request, block = next((request, block) for request, block in self.case.construction.blocks.items()
                              if block.kind == "EVENTS" and request not in requests)
        changed_row = replace(block.rows[0], got=self.case.task.start)
        self.assertNotEqual(changed_row, block.rows[0])
        construction = changed_construction(self.case, request=request, rows=(changed_row,) + block.rows[1:])
        forged = replace(self.case, construction=construction)
        self.assertTrue(birth.validate_birth_case(forged, role_tokens=self.tokens))
        self.assertEqual(targets.serialize_birth_case(forged, role_tokens=self.tokens), self.records[0, "m0"])
        with self.assertRaisesRegex(source.SourceInputError, "full_constructor_case_mismatch"):
            self.validate(case=forged)

    def test_hidden_world_edge_change_rejected_despite_oracle_replay(self):
        visited = {(turn.current_before, wire.parse_action(turn.action).operand) for turn in self.case.trace
                   if wire.parse_action(turn.action).operation == "STEP"}
        edges = dict(self.case.construction.world_edges)
        hidden = next(key for key, value in edges.items() if key not in visited and value != self.case.task.start)
        edges[hidden] = self.case.task.start
        forged = replace(self.case, construction=changed_construction(self.case, edges=edges))
        self.assertTrue(birth.validate_birth_case(forged, role_tokens=self.tokens))
        self.assertEqual(targets.serialize_birth_case(forged, role_tokens=self.tokens), self.records[0, "m0"])
        with self.assertRaisesRegex(source.SourceInputError, "full_constructor_case_mismatch"):
            self.validate(case=forged)

    def test_missing_extra_and_raw_registry_edges_not_just_traced_store(self):
        registry = dict(self.case.construction.registry)
        request = next(request for request in registry if request not in {turn.action for turn in self.case.trace})
        missing = dict(registry)
        del missing[request]
        extra = dict(registry, unexpected="MISS")
        changed = dict(registry)
        changed[request] += "\n"
        for values in (missing, extra, changed):
            forged = replace(self.case, construction=replace(self.case.construction, registry=MappingProxyType(values)))
            with self.subTest(registry=len(values)), self.assertRaises(source.SourceInputError):
                self.validate(case=forged)
        edges = dict(self.case.construction.world_edges)
        edges.pop(next(iter(edges)))
        with self.assertRaises(source.SourceInputError):
            self.validate(case=replace(self.case, construction=replace(self.case.construction, world_edges=edges)))

    def test_foreign_case_member_and_record_rejected(self):
        other_member = self.roster[0].cases[1]
        other_world = self.roster[2].cases[0]
        for inputs in (
                {"case": other_member}, {"case": other_world},
                {"case": other_world, "role_tokens": self.bindings[2]},
                {"record": self.records[0, "m1"][0].closed},
                {"record": self.records[2, "m0"][0].closed},
                {"case": replace(self.case, descriptor=other_member.descriptor)},
                {"case": replace(self.case, construction=other_world.construction)}):
            with self.subTest(inputs=tuple(inputs)), self.assertRaises(source.SourceInputError):
                self.validate(**inputs)
        relation = self.roster[16]
        with self.assertRaisesRegex(source.SourceInputError, "full_constructor_case_mismatch"):
            self.validate(case=replace(relation.cases[0], construction=relation.cases[1].construction),
                          role_tokens=self.bindings[16], record=self.records[16, "m0"][0].closed)

    def test_forged_case_fields_and_designations_rejected(self):
        for forged in (
                replace(self.case, facts=replace(self.case.facts, selected_event=self.case.facts.selected_query)),
                replace(self.case, targets=(replace(self.case.targets[0], target_bytes=b"STOP"),) + self.case.targets[1:]),
                replace(self.case, trace=(replace(self.case.trace[0], response="SERVICE\nMISS"),) + self.case.trace[1:]),
                replace(self.case, task_text=self.case.task_text + "\n"),
                replace(self.case, task=replace(self.case.task, goal=self.case.task.start)),
                replace(self.case, status="READY"), replace(self.case, memo_sha256="forged"),
                replace(self.case, clarification_sha256="forged"),
                replace(self.case, construction=replace(self.case.construction, scope="OTHER")),
                replace(self.case, construction=replace(self.case.construction, status="READY")),
                replace(self.case, construction=replace(self.case.construction, memo_sha256="forged"))):
            with self.subTest(case=forged.descriptor.case_id), self.assertRaisesRegex(
                    source.SourceInputError, "full_constructor_case_mismatch"):
                self.validate(case=forged)

    def test_rehashed_prefix_and_target_forgery_rejected(self):
        for prefix in (self.record.prefix[:-1], self.record.prefix + (targets.Message("user", "ACK"),),
                       (replace(self.record.prefix[0], content="forged"),) + self.record.prefix[1:],
                       self.record.prefix + (targets.Message("assistant", self.record.unit.target_bytes.decode()),)):
            with self.subTest(prefix=len(prefix)), self.assertRaisesRegex(source.SourceInputError, "record_mismatch"):
                self.validate(record=rehashed_record(self.record, prefix))
        unit = replace(self.record.unit, target_bytes=b"STOP", target_sha256=sha256(b"STOP").hexdigest(),
                       command="STOP", operand=None, selection_index=None)
        for record in (replace(self.record, unit=unit), replace(self.record, prefix_sha256="forged"),
                       replace(self.record, content_bytes=self.record.content_bytes + 1),
                       replace(self.record, serialized_bytes=self.record.serialized_bytes + 1),
                       replace(self.record, arm="OTHER"),
                       replace(self.record, unit=replace(self.record.unit, unit_id="p00/m1/u0"))):
            with self.subTest(record=record.arm), self.assertRaisesRegex(source.SourceInputError, "record_mismatch"):
                self.validate(record=record)

    def test_schema_types_reject_bool_float_subclasses_and_mutable_sequences(self):
        class ForgedCase(birth.BirthCase):
            pass

        class EqualText(str):
            pass

        for case in (replace(self.case, descriptor=replace(self.case.descriptor, pair_index=False)),
                     replace(self.case, construction=replace(self.case.construction, skin=0.0)),
                     replace(self.case, task_text=EqualText(self.case.task_text)),
                     replace(self.case, targets=list(self.case.targets)),
                     replace(self.case, trace=list(self.case.trace)),
                     ForgedCase(**self.case.__dict__)):
            with self.subTest(type=type(case)), self.assertRaises(source.SourceInputError):
                self.validate(case=case)
        for record in (replace(self.record, prefix=list(self.record.prefix)),
                       replace(self.record, content_bytes=float(self.record.content_bytes)),
                       replace(self.record, unit=replace(self.record.unit, selection_index=False))):
            with self.assertRaises(source.SourceInputError):
                self.validate(record=record)

    def test_bad_role_mappings_rejected(self):
        role = next(iter(self.tokens))
        missing = dict(self.tokens)
        del missing[role]
        node_roles = [key for key, value in self.tokens.items() if value.startswith("M2AN_")]
        duplicate = dict(self.tokens)
        duplicate[node_roles[1]] = duplicate[node_roles[0]]
        alternatives = (None, list(self.tokens.items()), missing, dict(self.tokens, unexpected="M2AN_BBBBBBBBBBBB"),
                        self.bindings[1], duplicate, {1: "M2AN_BBBBBBBBBBBB"},
                        dict(self.tokens, **{role: "M2AN_AAAAAAAAAAAA"}),
                        dict(self.tokens, **{role: b"M2AN_BBBBBBBBBBBB"}),
                        dict(self.tokens, **{role: "M2AQ_BBBBBBBBBBBB"}),
                        {"x" * 257: "M2AN_BBBBBBBBBBBB"})
        for mapping in alternatives:
            with self.subTest(type=type(mapping)), self.assertRaises(source.SourceInputError):
                self.validate(role_tokens=mapping)
        with patch.object(source, "BOUNDS", dict(source.BOUNDS, role_entries=1)):
            with self.assertRaisesRegex(source.SourceInputError, "bounded_explicit_role_mapping"):
                self.validate()

    def test_wrong_master_and_bad_master_types_rejected(self):
        for master in (None, MASTER.decode(), bytearray(MASTER), memoryview(MASTER)):
            with self.subTest(type=type(master)), self.assertRaisesRegex(source.SourceInputError, "master_bytes"):
                self.validate(display_master=master)
        with self.assertRaisesRegex(source.SourceInputError, "full_constructor_case_mismatch"):
            self.validate(display_master=MASTER + b"different")
        with patch.object(source, "BOUNDS", dict(source.BOUNDS, master_bytes=len(MASTER) - 1)):
            with self.assertRaisesRegex(source.SourceInputError, "master_bytes"):
                self.validate()

    def test_empty_and_binary_masters_match_constructor_without_new_science_rule(self):
        for master in (b"", b"\x00\xff\r\n"):
            pair = birth.build_birth_pair(world="p00", role_tokens=self.tokens, display_master=master)
            case = pair.cases[0]
            record = targets.serialize_birth_case(case, role_tokens=self.tokens)[0].closed
            result = self.validate(case=case, record=record, display_master=master)
            self.assertEqual(result.display_master_sha256, sha256(master).hexdigest())

    def test_mapping_order_and_mutation_cannot_change_returned_snapshots(self):
        tokens = dict(reversed(tuple(self.tokens.items())))
        blocks = dict(self.case.construction.blocks)
        registry = dict(reversed(tuple(self.case.construction.registry.items())))
        edges = dict(self.case.construction.world_edges)
        case = replace(self.case, construction=replace(self.case.construction, blocks=blocks,
                                                       registry=registry, world_edges=edges))
        result = self.validate(case=case, role_tokens=tokens)
        baseline = self.validate()
        self.assertEqual(result, baseline)
        for mapping in (tokens, blocks, registry, edges):
            mapping.clear()
        self.assertEqual(result, baseline)
        for mapping in (result.role_tokens, result.case.construction.blocks,
                        result.case.construction.registry, result.case.construction.world_edges):
            self.assertIs(type(mapping), MappingProxyType)
            with self.assertRaises(TypeError):
                mapping["forged"] = "value"
        with self.assertRaises(FrozenInstanceError):
            result.case = self.case
        with self.assertRaises(FrozenInstanceError):
            result.record.unit.target_bytes = b"STOP"

    def test_each_call_rebuilds_and_no_input_flags_or_receipts_are_authority(self):
        with patch.object(birth, "build_birth_pair", wraps=birth.build_birth_pair) as constructor:
            first = self.validate()
            second = self.validate()
            self.assertEqual(first, second)
            self.assertEqual(constructor.call_count, 2)
        with self.assertRaises(source.SourceInputError):
            self.validate(case=first)
        for name in ("complete_guard", "native_ready", "material_ready", "GO_CLAIM",
                     "semantic_bytes", "future_identifiers", "registered_routes"):
            with self.subTest(name=name), self.assertRaises(TypeError):
                self.validate(**{name: True})
        for name in ("case", "record", "role_tokens", "display_master"):
            arguments = dict(case=self.case, record=self.record, role_tokens=self.tokens, display_master=MASTER)
            del arguments[name]
            with self.assertRaises(TypeError):
                source.validate_birth_source(**arguments)

    def test_pure_source_only_false_gates_and_no_io_allocation_or_scanning(self):
        with patch("builtins.open", side_effect=AssertionError("no IO")), \
                patch("socket.socket", side_effect=AssertionError("no network")), \
                patch.object(wire, "allocate_opaque_namespace", side_effect=AssertionError("no allocation")):
            result = self.validate()
        self.assertEqual(result.status, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(result.science_gates.values()))
        self.assertIs(result.inventory_completeness_verified, False)
        self.assertIs(result.native_chat_bytes_verified, False)
        self.assertFalse(hasattr(result, "passed"))
        self.assertTrue(any("Hidden evaluator" in limitation for limitation in result.limitations))
        for name in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"):
            self.assertIs(getattr(source, name), False)
        with self.assertRaises(TypeError):
            result.science_gates["GO_CLAIM"] = True


if __name__ == "__main__":
    unittest.main()
