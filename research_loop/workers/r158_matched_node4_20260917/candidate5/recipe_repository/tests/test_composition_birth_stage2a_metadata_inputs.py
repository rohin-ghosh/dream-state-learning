"""Synthetic CPU coverage and optional complete birth envelope measurement.

Run --measure-envelope to cover all 64 cases and 512 records. Aliases are
measured by unioning unchanged-root scanner ledgers, reusing only the static
private portion per case. This counts the full tree exactly without 512 prefix
matcher passes; it does NOT bypass or qualify the scanner's whole-tree limits.
"""

from collections import Counter
from dataclasses import FrozenInstanceError, fields, replace
from functools import lru_cache
from hashlib import sha256
import json
import sys
from time import perf_counter
from types import MappingProxyType
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_core_inputs as core_inputs
from organism_v6 import composition_birth_stage2a_metadata_inputs as source
from organism_v6 import composition_birth_stage2a_route_inputs as route_inputs
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_birth import synthetic_bindings


MASTER = b"synthetic-complete-metadata-only"
_DYNAMIC_ROOTS = frozenset(("core", "evaluator", "target", "unit_id"))
_STATIC_FUTURE_FIELDS = frozenset(("candidates", "candidate_provenance"))


@lru_cache(maxsize=4)
def fixture(number):
    roles = synthetic_bindings(number)
    pair = birth.build_birth_pair(world=f"p{number:02d}", role_tokens=roles, display_master=MASTER)
    records = tuple(tuple(record for paired in targets.serialize_birth_case(case, role_tokens=roles)
                          for record in (paired.closed, paired.atom_local)) for case in pair.cases)
    return pair, records


def producer_for(pair, member):
    return source.BirthMetadataInputProducer(case=pair.cases[member], role_tokens=pair.role_tokens,
                                            display_master=MASTER)


def static_aliases(metadata):
    aliases = set()
    for root in sorted(source.PROTECTED_ROOTS - _DYNAMIC_ROOTS - {"future"}):
        aliases.update(scanner.derive_semantic_aliases(canonical_json({root: metadata[root]}),
                                                      semantic_profile="birth_full_v1"))
    aliases.update(scanner.derive_semantic_aliases(canonical_json({
        "future": {name: metadata["future"][name] for name in _STATIC_FUTURE_FIELDS}}),
        semantic_profile="birth_full_v1"))
    return frozenset(aliases)


def all_aliases(metadata, static):
    dynamic = {root: metadata[root] for root in _DYNAMIC_ROOTS}
    dynamic["future"] = {name: value for name, value in metadata["future"].items()
                         if name not in _STATIC_FUTURE_FIELDS}
    return static | frozenset(scanner.derive_semantic_aliases(canonical_json(dynamic),
                                                            semantic_profile="birth_full_v1"))


def assert_complete(test, result):
    metadata = result.metadata
    case = result.source.case
    construction = metadata["oracle"]["construction"]
    test.assertEqual(set(metadata), source.PROTECTED_ROOTS)
    test.assertEqual(set(metadata), scanner.PROTECTED_ROOTS)
    test.assertEqual(metadata["core"], result.core_inputs.core)
    test.assertEqual(canonical_json(metadata["core"]), result.core_inputs.core_bytes)
    test.assertEqual(metadata["role_keys"], dict(result.source.role_tokens))
    test.assertEqual(metadata["oracle"]["facts"], {field.name: getattr(case.facts, field.name) for field in fields(case.facts)})
    test.assertEqual(result.coverage_counts["services"], len(case.construction.registry))
    test.assertEqual(result.coverage_counts["rows"], sum(len(block.rows) for block in case.construction.blocks.values()))
    test.assertEqual(result.coverage_counts["world_edges"], len(case.construction.world_edges))
    test.assertEqual(result.coverage_counts["targets"], 4)
    test.assertEqual(result.coverage_counts["role_bindings"], len(result.source.role_tokens))
    test.assertEqual({(edge["AT"], edge["DID"]): edge["CURRENT"] for edge in construction["world_edges"]},
                     dict(case.construction.world_edges))
    decoded_registry = {source.render_action(service["request"]).decode("ascii"):
                        source.render_service(service["block"]).decode("ascii")
                        for service in construction["services"]}
    test.assertEqual(decoded_registry, dict(case.construction.registry))
    test.assertEqual(len(metadata["oracle"]["trace"]), len(case.trace))
    for encoded, turn in zip(metadata["oracle"]["trace"], case.trace):
        test.assertEqual(source.render_action(encoded["action"]), turn.action.encode("ascii"))
        test.assertEqual(source.render_response(encoded["response"]), turn.response.encode("ascii"))
        test.assertEqual(set(encoded), {field.name for field in fields(turn)})
        test.assertEqual(encoded["current_before"], turn.current_before)
        test.assertEqual(encoded["current_after"], turn.current_after)
        test.assertEqual(encoded["target_ordinal"], turn.target_ordinal)
    for encoded, target in zip(metadata["oracle"]["targets"], case.targets):
        test.assertEqual(set(encoded), {field.name for field in fields(target)})
        test.assertEqual(source.render_action(encoded["target_bytes"]), target.target_bytes)
        for field in fields(target):
            if field.name != "target_bytes":
                test.assertEqual(encoded[field.name], getattr(target, field.name))
    for field in fields(case.descriptor):
        name = {"world": "world_id", "member": "member_id"}.get(field.name, field.name)
        value = getattr(case.descriptor, field.name)
        test.assertEqual(metadata["factors"][name], list(value) if type(value) is tuple else value)
    test.assertEqual(metadata["case_id"], {"world_id": case.descriptor.world, "member_id": case.descriptor.member})
    test.assertEqual(metadata["factors"]["case_id"], list(case.descriptor.case_id))
    test.assertEqual(metadata["factors"]["family_bit"], case.descriptor.family_bit)
    test.assertEqual(metadata["factors"]["relation_slot"], case.descriptor.relation_slot)
    test.assertEqual(metadata["target"]["target_bytes"].encode("ascii"), result.source.record.unit.target_bytes)
    test.assertEqual(metadata["target"]["retained_trace_indices"], list(result.future_inputs.binding.retained_trace_indices))
    test.assertEqual(result.metadata_sha256, sha256(result.metadata_bytes).hexdigest())
    test.assertFalse(any(result.science_gates.values()))


class BirthMetadataInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pair, cls.records = fixture(2)
        cls.producer = producer_for(cls.pair, 0)
        cls.results = tuple(cls.producer.build(record) for record in cls.records[0])

    def test_complete_protected_roots_source_fields_rows_and_round_trips(self):
        for result in self.results:
            with self.subTest(unit=result.source.record.unit.unit_id, arm=result.source.record.arm):
                assert_complete(self, result)
                result.check_semantic_bounds()

    def test_actual_uppercase_wire_fields_and_skin_order(self):
        for number in (2, 26):
            pair, records = fixture(number)
            result = self.results[0] if number == 2 else producer_for(pair, 1).build(records[1][0])
            skin = result.source.case.descriptor.skin
            self.assertEqual(skin, 0 if number == 2 else 1)
            for service in result.metadata["oracle"]["construction"]["services"]:
                block = service["block"]
                raw = source.render_service(block).decode("ascii")
                self.assertEqual(raw, result.source.case.construction.registry[source.render_action(service["request"]).decode("ascii")])
                if block["rows"]:
                    expected = {"EVENT", "AT", "FOR", "DID", "GOT", "RECOVER", "EVIDENCE"} if block["kind"] == "EVENTS" else {"ROUTE", "AT", "FOR", "QUERY"}
                    self.assertEqual(set(block["rows"][0]), expected)
                    self.assertEqual(raw.splitlines()[1].split()[2], "AT" if skin == 0 else "FOR")
            self.assertIn("CURRENT", result.metadata["oracle"]["task"])

    def test_future_candidate_paths_disclosures_and_receipts_are_lossless(self):
        for result in self.results:
            future = result.future_inputs
            encoded = result.metadata["future"]
            for name in ("candidates", "disclosed", "future_identifiers"):
                self.assertEqual({value.encode("ascii") for value in encoded[name]}, getattr(future, name))
            origins = {entry["identifier"].encode("ascii"):
                       tuple((origin["role_key"], source.render_source_path(origin["source_path"])) for origin in entry["origins"])
                       for entry in encoded["candidate_provenance"]}
            self.assertEqual(origins, {token: tuple((entry.role_key, entry.source_path) for entry in entries)
                                      for token, entries in future.candidate_provenance.items()})
            disclosures = {entry["identifier"].encode("ascii"): entry["observations"] for entry in encoded["disclosure_provenance"]}
            for token, receipts in future.disclosure_provenance.items():
                for encoded_receipt, receipt in zip(disclosures[token], receipts):
                    self.assertEqual(set(encoded_receipt), {field.name for field in fields(receipt)})
                    for field in fields(receipt):
                        value = getattr(receipt, field.name)
                        self.assertEqual(encoded_receipt[field.name], value.decode("ascii") if type(value) is bytes else value)
                    self.assertEqual(future.binding.projection_bytes[receipt.start:receipt.end], token)

    def test_finite_route_basis_includes_offtrace_transitions_and_recovery_owners(self):
        pair, records = fixture(27)
        result = producer_for(pair, 1).build(records[1][4])
        route = route_inputs.derive_birth_route_inputs(case=result.source.case, record=result.source.record,
                                                     role_tokens=pair.role_tokens, display_master=MASTER)
        encoded = result.metadata["oracle"]["route_basis"]
        self.assertEqual(len(encoded["transitions"]), len(route.transitions))
        labels = {"QUERY": "query", "EVENT": "event", "AT": "current", "FOR": "goal", "DID": "port",
                  "GOT": "predicted", "CURRENT": "actual", "RECOVER": "recover", "EVIDENCE": "receipt",
                  "recovery_owner_port": "recovery_owner_port", "mismatches": "mismatches"}
        for transition in encoded["transitions"]:
            original = route.transitions[transition["DID"]]
            for label, name in labels.items():
                self.assertEqual(transition[label], getattr(original, name))
            self.assertEqual(source.render_source_path(transition["source_path"]), original.source_path)
        self.assertTrue(any(transition["recovery_owner_port"] for transition in encoded["transitions"]))
        self.assertEqual(encoded["ports_by_current"], {key: list(value) for key, value in route.ports_by_current.items()})
        self.assertEqual(encoded["ports_by_query"], {key: list(value) for key, value in route.ports_by_query.items()})
        self.assertEqual(encoded["unavailable_recover_queries"], sorted(route.unavailable_recover_queries))

    def test_paired_FOR_swap_and_effective_mismatch_provenance(self):
        for number in (2, 18, 27):
            pair, records = fixture(number)
            for member in (0, 1):
                result = producer_for(pair, member).build(records[member][0])
                mutation = result.metadata["mutation"]
                changes = mutation["paired_FOR_swap"]
                self.assertEqual(len(changes), 0 if number == 2 else 2)
                for change in changes:
                    request = source.render_action(change["request"]).decode("ascii")
                    position = change["row_index"]
                    self.assertEqual(change["field"], "FOR")
                    for side, member_index in (("before", 0), ("after", 1)):
                        row = pair.cases[member_index].construction.blocks[request].rows[position]
                        self.assertEqual(change[side]["FOR"], row.goal)
                        self.assertEqual(change[side]["EVENT"], row.event)
                    self.assertEqual({name for name in change["before"] if change["before"][name] != change["after"][name]}, {"FOR"})
                self.assertEqual(len(mutation["effective_mismatches"]), 2 if number == 27 else 0)
                for mismatch in mutation["effective_mismatches"]:
                    self.assertNotEqual(mismatch["GOT"], mismatch["CURRENT"])
                    self.assertEqual(mismatch["CURRENT"], result.source.case.construction.world_edges[mismatch["AT"], mismatch["DID"]])

    def test_tuple_null_semantics_and_all_recovery_variants(self):
        seen = set()
        for number in (2, 3, 11, 19):
            pair, records = fixture(number)
            result = producer_for(pair, 0).build(records[0][-1])
            assert_complete(self, result)
            descriptor = pair.cases[0].descriptor
            seen.add(descriptor.recovery_subtype)
            self.assertEqual(result.metadata["recovery_match_id"], list(descriptor.recovery_match_id) if descriptor.recovery_match_id else None)
            if descriptor.pair_type == "goal":
                self.assertIsNone(result.metadata["factors"]["relation_slot"])
            else:
                self.assertEqual(result.metadata["factors"]["relation_slot"], descriptor.relation_slot)
            self.assertTrue(any(turn["response"]["kind"] == "SERVICE" for turn in result.metadata["oracle"]["trace"]))
        self.assertEqual(seen, {"NONE", "STEP_OUTCOME_MISMATCH", "STRICT_MISS", "IRRELEVANT_RETURN"})

    def test_retention_isolation_exact_core_and_original_private_trace(self):
        for closed, atom in zip(self.results[::2], self.results[1::2]):
            self.assertEqual(closed.metadata["oracle"], atom.metadata["oracle"])
            self.assertEqual(closed.metadata["unit_id"], atom.metadata["unit_id"])
            self.assertEqual(closed.metadata["target"]["unit"], atom.metadata["target"]["unit"])
            self.assertEqual(closed.future_inputs.candidates, atom.future_inputs.candidates)
            self.assertLessEqual(atom.future_inputs.disclosed, closed.future_inputs.disclosed)
            self.assertLessEqual(set(atom.future_inputs.binding.retained_trace_indices), set(closed.future_inputs.binding.retained_trace_indices))
        atom = self.results[-1]
        self.assertEqual(atom.metadata["target"]["retained_trace_indices"], [])
        self.assertEqual(atom.metadata["future"]["disclosed"], [])
        self.assertEqual(len(atom.source.record.prefix), 2)
        self.assertGreater(len(atom.metadata["oracle"]["trace"]), 2)
        direct = core_inputs.build_birth_core_inputs(case=atom.source.case, record=atom.source.record,
                                                    role_tokens=atom.source.role_tokens)
        self.assertEqual(atom.core_inputs.core_bytes, direct.core_bytes)

    def test_reusable_producer_determinism_and_immutable_snapshot(self):
        mutable_roles = dict(self.pair.role_tokens)
        mutable_case = replace(self.pair.cases[0], construction=replace(self.pair.cases[0].construction,
                               registry=dict(self.pair.cases[0].construction.registry),
                               blocks=dict(self.pair.cases[0].construction.blocks),
                               world_edges=dict(self.pair.cases[0].construction.world_edges)))
        producer = source.BirthMetadataInputProducer(case=mutable_case, role_tokens=mutable_roles, display_master=MASTER)
        mutable_roles.clear()
        mutable_case.construction.registry.clear()
        mutable_case.construction.blocks.clear()
        mutable_case.construction.world_edges.clear()
        with patch.object(source_inputs, "validate_birth_source", wraps=source_inputs.validate_birth_source) as validate:
            result = producer.build(self.records[0][0])
            repeated = producer.build(self.records[0][0])
        self.assertEqual(validate.call_count, 2)
        self.assertEqual(result.metadata_bytes, repeated.metadata_bytes)
        self.assertEqual(result.metadata_bytes, self.results[0].metadata_bytes)
        self.assertEqual(result.provenance_bytes, repeated.provenance_bytes)
        result.metadata["oracle"].clear()
        self.assertTrue(result.metadata["oracle"])
        self.assertTrue(result.source_snapshot.case.construction.registry)
        self.assertEqual(type(result.source_snapshot.role_tokens), MappingProxyType)
        with self.assertRaises(TypeError):
            result.coverage_counts["bytes"] = 0
        with self.assertRaises(FrozenInstanceError):
            result.metadata_bytes = b"{}"

    def test_offtrace_edges_registry_rows_and_other_source_mutations_rejected(self):
        case = self.pair.cases[0]
        used = {turn.action for turn in case.trace}
        request = next(request for request, block in case.construction.blocks.items() if request not in used and block.kind == "EVENTS")
        block = case.construction.blocks[request]
        altered_row = replace(block.rows[0], receipt=block.rows[1].receipt)
        altered_block = replace(block, rows=(altered_row,) + block.rows[1:])
        altered_blocks = dict(case.construction.blocks, **{request: altered_block})
        edges = dict(case.construction.world_edges)
        edges[block.rows[0].node, block.rows[0].port] = case.task.start
        registries = dict(case.construction.registry)
        registries[request] += "\n"
        for construction in (replace(case.construction, world_edges=edges),
                             replace(case.construction, blocks=altered_blocks),
                             replace(case.construction, registry=registries)):
            with self.subTest(surface=construction), self.assertRaises(ValueError):
                source.BirthMetadataInputProducer(case=replace(case, construction=construction),
                                                 role_tokens=self.pair.role_tokens, display_master=MASTER)

    def test_wrong_master_bindings_case_or_record_fail_closed(self):
        arguments = dict(case=self.pair.cases[0], record=self.records[0][0], role_tokens=self.pair.role_tokens,
                         display_master=MASTER)
        for changes in ({"display_master": MASTER + b"wrong"}, {"role_tokens": {}},
                        {"record": self.records[1][0]}, {"case": replace(self.pair.cases[0], status="forged")}):
            with self.subTest(changes=tuple(changes)), self.assertRaises(ValueError):
                source.build_birth_metadata_inputs(**dict(arguments, **changes))
        forged = replace(self.records[0][0], serialized_bytes=True)
        with self.assertRaisesRegex(ValueError, "exact_constructor_record_mismatch"):
            self.producer.build(forged)
        for name in ("validated_source", "inventory_complete", "semantic_bytes"):
            with self.assertRaises(TypeError):
                source.build_birth_metadata_inputs(**dict(arguments, **{name: True}))

    def test_tampered_decoded_actions_responses_services_fail_exact_hash_checks(self):
        metadata = self.results[0].metadata
        action = metadata["oracle"]["trace"][0]["action"]
        with self.assertRaisesRegex(source.MetadataInputError, "hash_mismatch"):
            source.render_action(dict(action, raw_sha256="0" * 64))
        with self.assertRaisesRegex(source.MetadataInputError, "unsupported_action_fields"):
            source.render_action(dict(action, ignored="not allowed"))
        response = metadata["oracle"]["trace"][0]["response"]
        with self.assertRaisesRegex(source.MetadataInputError, "hash_mismatch"):
            source.render_response(dict(response, raw_bytes=response["raw_bytes"] + 1))
        block = metadata["oracle"]["construction"]["services"][0]["block"]
        block["rows"][0]["FOR"] = self.pair.cases[0].task.start
        with self.assertRaisesRegex(source.MetadataInputError, "hash_mismatch"):
            source.render_service(block)

    def test_unknown_fields_types_properties_and_responses_rejected(self):
        with self.assertRaisesRegex(source.MetadataInputError, "unsupported_source_fields_or_type"):
            source._check_fields(object())
        with self.assertRaisesRegex(source.MetadataInputError, "unsupported_decoded_source_type"):
            source._decoded(1.5)
        with self.assertRaisesRegex(source.MetadataInputError, "unsupported_trace_response"):
            source._response("FUTURE HOST SURFACE", 0)
        with patch.object(birth.BirthCaseDescriptor, "new_property", property(lambda descriptor: "unaccounted"), create=True):
            with self.assertRaisesRegex(source.MetadataInputError, "unsupported_descriptor_properties"):
                producer_for(self.pair, 0)

    def test_provenance_binds_constructor_master_roles_case_record_and_metadata(self):
        result = self.results[0]
        receipt = json.loads(result.provenance_bytes)
        self.assertEqual(receipt["metadata_sha256"], result.metadata_sha256)
        self.assertEqual(receipt["source"], json.loads(result.source.provenance_bytes))
        self.assertEqual(receipt["source"]["constructor"], source_inputs.CONSTRUCTOR_API)
        for name in ("case_sha256", "record_sha256", "role_tokens_sha256", "display_master_sha256"):
            self.assertEqual(receipt["source"][name], getattr(result.source, name))
        self.assertEqual(receipt["source"]["display_master_sha256"], sha256(MASTER).hexdigest())
        self.assertEqual(result.paired_source_snapshot, self.pair)
        self.assertIs(result.binding, result.future_inputs.binding)
        self.assertIs(result.route_inputs.source, result.source)
        self.assertEqual(len(result.route_inputs.transitions), result.coverage_counts["route_transitions"])

    def test_partitioned_measurement_equals_whole_scanner_aliases_without_retuning(self):
        metadata = self.results[0].metadata
        measured = all_aliases(metadata, static_aliases(metadata))
        whole = scanner.derive_semantic_aliases(self.results[0].metadata_bytes, semantic_profile="birth_full_v1")
        self.assertEqual(measured, frozenset(whole))
        self.assertIn(b"family_motif", measured)
        self.assertIn(b"B_BUCKET_MERGES", measured)
        self.assertIn(b"goal", measured)
        self.assertIn(b"service", measured)
        collisions = {alias for alias in measured if alias in self.results[0].future_inputs.binding.projection_bytes}
        self.assertTrue(any(alias.isdigit() for alias in collisions))
        self.assertEqual(scanner.forbidden_semantic_labels(self.results[0].metadata_bytes, semantic_profile="birth_full_v1"), ())

    def test_full_A_tree_preserves_rows_and_fails_explicitly_on_overflow(self):
        pair, records = fixture(0)
        result = producer_for(pair, 0).build(records[0][0])
        assert_complete(self, result)
        self.assertEqual(result.coverage_counts["event_rows"], 2400)
        self.assertGreater(result.coverage_counts["leaves"], scanner.BOUNDS["leaves"])
        limits = dict(scanner.SEMANTIC_PROFILES["birth_full_v1"], leaves=4096)
        with patch.object(scanner, "SEMANTIC_PROFILES", dict(scanner.SEMANTIC_PROFILES, birth_full_v1=limits)):
            with self.assertRaisesRegex(source.MetadataBoundsError, "leaves") as raised:
                result.check_semantic_bounds()
            self.assertEqual(raised.exception.coverage_counts, result.coverage_counts)
            with self.assertRaisesRegex(ValueError, "semantic_leaf_bound_exceeded"):
                scanner.derive_semantic_aliases(result.metadata_bytes, semantic_profile="birth_full_v1")

    def test_all_science_flags_false_and_no_implicit_scan_clearance(self):
        result = self.results[0]
        self.assertEqual(result.status, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(result.inventory_completeness_verified)
        self.assertFalse(result.native_chat_bytes_verified)
        self.assertFalse(hasattr(result, "supplied_projection_clear"))
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        for name in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"):
            self.assertFalse(getattr(source, name))

    def test_producer_performs_no_io_network_allocation_process_or_scanning(self):
        with patch("builtins.open", side_effect=AssertionError("no IO")), \
                patch("socket.socket", side_effect=AssertionError("no network")), \
                patch("subprocess.Popen", side_effect=AssertionError("no process")), \
                patch.object(wire, "allocate_opaque_namespace", side_effect=AssertionError("no allocation")), \
                patch.object(scanner, "derive_semantic_aliases", side_effect=AssertionError("no alias scan")), \
                patch.object(scanner, "scan_forward_targets", side_effect=AssertionError("no prefix scan")):
            result = source.build_birth_metadata_inputs(case=self.pair.cases[0], record=self.records[0][0],
                                                       role_tokens=self.pair.role_tokens, display_master=MASTER)
        self.assertEqual(result.metadata_bytes, self.results[0].metadata_bytes)


class BirthMetadataProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pair, cls.records = fixture(2)
        cls.arguments = dict(case=cls.pair.cases[0], role_tokens=cls.pair.role_tokens, display_master=MASTER)
        cls.default = source.BirthMetadataInputProducer(**cls.arguments).build(cls.records[0][0])

    def test_default_v1_explicit_profiles_preserve_metadata_and_alias_ledger(self):
        explicit_v1 = source.build_birth_metadata_inputs(**self.arguments, record=self.records[0][0],
                                                        semantic_profile="birth_full_v1")
        explicit_v2 = source.build_birth_metadata_inputs(**self.arguments, record=self.records[0][0],
                                                        semantic_profile="birth_full_v2")
        self.assertEqual(self.default.semantic_profile, "birth_full_v1")
        self.assertIn("semantic_profile", {field.name for field in fields(source.BirthMetadataInputs)})
        self.assertEqual(self.default.metadata_bytes, explicit_v1.metadata_bytes)
        self.assertEqual(self.default.provenance_bytes, explicit_v1.provenance_bytes)
        for result, profile in ((explicit_v1, "birth_full_v1"), (explicit_v2, "birth_full_v2")):
            self.assertEqual(result.semantic_profile, profile)
            self.assertEqual(result.metadata_bytes, self.default.metadata_bytes)
            self.assertEqual(result.metadata_sha256, self.default.metadata_sha256)
            self.assertEqual(result.coverage_counts, self.default.coverage_counts)
            provenance = json.loads(result.provenance_bytes)
            self.assertEqual(provenance.pop("semantic_profile"), profile)
            self.assertEqual(provenance, {name: value for name, value in json.loads(self.default.provenance_bytes).items()
                                          if name != "semantic_profile"})
            self.assertFalse(any(result.science_gates.values()))
            result.check_semantic_bounds()
        self.assertEqual(scanner.semantic_alias_ledger(explicit_v1.semantic_bytes, semantic_profile="birth_full_v1"),
                         scanner.semantic_alias_ledger(explicit_v2.semantic_bytes, semantic_profile="birth_full_v2"))
        with self.assertRaises(FrozenInstanceError):
            explicit_v2.semantic_profile = "birth_full_v1"

    def test_reusable_constructor_keeps_selected_profile_and_current_sources(self):
        producer = source.BirthMetadataInputProducer(**self.arguments, semantic_profile="birth_full_v2")
        for record in self.records[0][:2]:
            result = producer.build(record)
            self.assertEqual(result.semantic_profile, "birth_full_v2")
            self.assertEqual(json.loads(result.provenance_bytes)["semantic_profile"], "birth_full_v2")
            self.assertEqual(result.source.record, record)
            self.assertIs(result.route_inputs.source, result.source)
            self.assertIs(result.binding, result.future_inputs.binding)
        self.assertEqual(self.default.semantic_profile, "birth_full_v1")

    def test_unknown_profiles_reject_before_expensive_source_work(self):
        registered = dict(scanner.SEMANTIC_PROFILES, birth_full_v3=scanner.SEMANTIC_PROFILES["birth_full_v1"])
        with patch.object(scanner, "SEMANTIC_PROFILES", registered), \
                patch.object(targets, "serialize_birth_case", side_effect=AssertionError("no source work")):
            for profile in (None, True, 1, [], {}, "legacy", "birth_full_v3", "BIRTH_FULL_V2", ""):
                with self.subTest(profile=profile):
                    with self.assertRaisesRegex(source.MetadataInputError, "unsupported_birth_semantic_profile"):
                        source.BirthMetadataInputProducer(**self.arguments, semantic_profile=profile)
                    with self.assertRaisesRegex(source.MetadataInputError, "unsupported_birth_semantic_profile"):
                        replace(self.default, semantic_profile=profile)

    def test_known_but_unregistered_profile_fails_without_fallback(self):
        with patch.object(scanner, "SEMANTIC_PROFILES", {"birth_full_v1": scanner.SEMANTIC_PROFILES["birth_full_v1"]}), \
                patch.object(targets, "serialize_birth_case", side_effect=AssertionError("no source work")):
            with self.assertRaisesRegex(source.MetadataInputError, "unavailable_birth_semantic_profile: birth_full_v2"):
                source.BirthMetadataInputProducer(**self.arguments, semantic_profile="birth_full_v2")

    def test_bounds_use_selected_profile_without_reinterpreting_metadata(self):
        result = source.build_birth_metadata_inputs(**self.arguments, record=self.records[0][0],
                                                   semantic_profile="birth_full_v2")
        limits = dict(scanner.SEMANTIC_PROFILES["birth_full_v2"], leaves=4096)
        with patch.object(scanner, "SEMANTIC_PROFILES", dict(scanner.SEMANTIC_PROFILES, birth_full_v2=limits)):
            self.default.check_semantic_bounds()
            with self.assertRaisesRegex(source.MetadataBoundsError, "leaves"):
                result.check_semantic_bounds()

    def test_measured_max_A_v2_bounds_and_whole_scanner_count_agreement(self):
        pair, records = fixture(29)
        record = records[0][-2]
        self.assertEqual((record.unit.unit_id, record.arm), ("p29/m0/u3", "CLOSED"))
        arguments = dict(case=pair.cases[0], role_tokens=pair.role_tokens, display_master=MASTER)
        default = source.BirthMetadataInputProducer(**arguments).build(record)
        result = source.BirthMetadataInputProducer(**arguments, semantic_profile="birth_full_v2").build(record)
        self.assertEqual(result.metadata_bytes, default.metadata_bytes)
        self.assertEqual(result.metadata_sha256, default.metadata_sha256)
        self.assertEqual(dict(scanner.SEMANTIC_PROFILES["birth_full_v2"]),
                         {"bytes": 16777216, "leaves": 262144, "nodes": 524288, "aliases": 524288, "depth": 64})
        self.assertEqual(scanner.SEMANTIC_PROFILES["birth_full_v1"]["leaves"], 131072)
        with self.assertRaisesRegex(source.MetadataBoundsError, "leaves"):
            default.check_semantic_bounds()
        with self.assertRaisesRegex(ValueError, "semantic_leaf_bound_exceeded"):
            scanner.derive_semantic_aliases(default.semantic_bytes, semantic_profile=default.semantic_profile)
        self.assertEqual(result.check_semantic_bounds(), default.coverage_counts)
        assert_complete(self, result)
        measured = {"bytes": 5870321, "nodes": 260563, "leaves": 200244, "depth": 8}
        self.assertEqual({name: result.coverage_counts[name] for name in measured}, measured)
        metadata = result.metadata
        scanner_counts = {"nodes": 0, "leaves": 0, "depth": 0}
        for path, value in scanner._nodes(metadata, semantic_profile=result.semantic_profile):
            scanner_counts["nodes"] += 1
            scanner_counts["leaves"] += type(value) not in (dict, list)
            scanner_counts["depth"] = max(scanner_counts["depth"], len(path))
        self.assertEqual(scanner_counts, {name: measured[name] for name in scanner_counts})
        aliases = scanner.derive_semantic_aliases(result.semantic_bytes, semantic_profile=result.semantic_profile)
        self.assertEqual(len(aliases), 422196)
        self.assertEqual(frozenset(aliases), all_aliases(metadata, static_aliases(metadata)))
        self.assertFalse(any(result.science_gates.values()))


def measure_envelope(*, start_world=0, stop_world=32):
    """Print exact maxima, limit failures and timings for the synthetic envelope."""
    started = perf_counter()
    maxima, maximum_records = {}, {}
    failures = Counter()
    coverage = Counter()
    checked = unittest.TestCase()
    if not 0 <= start_world < stop_world <= 32:
        raise ValueError("invalid_envelope_world_range")
    for number in range(start_world, stop_world):
        world_started = perf_counter()
        pair, records = fixture(number)
        for member in range(2):
            producer = producer_for(pair, member)
            immutable_aliases = None
            for record in records[member]:
                result = producer.build(record)
                assert_complete(checked, result)
                metadata = result.metadata
                if immutable_aliases is None:
                    immutable_aliases = static_aliases(metadata)
                aliases = all_aliases(metadata, immutable_aliases)
                counts = dict(result.coverage_counts, aliases=len(aliases))
                identity = record.unit.unit_id + "/" + record.arm
                for name, count in counts.items():
                    if name not in maxima or count > maxima[name]:
                        maxima[name] = count
                        maximum_records[name] = identity
                for name, limit in scanner.SEMANTIC_PROFILES["birth_full_v1"].items():
                    if counts[name] > limit:
                        failures[name] += 1
                coverage["records"] += 1
                coverage[record.arm] += 1
                coverage["family_" + pair.cases[member].descriptor.family] += 1
                coverage[pair.cases[member].descriptor.recovery_subtype] += 1
            coverage["cases"] += 1
        coverage["worlds"] += 1
        print(json.dumps({"world": number, "records": coverage["records"],
                          "world_seconds": round(perf_counter() - world_started, 3),
                          "elapsed_seconds": round(perf_counter() - started, 3)}, sort_keys=True), flush=True)
    print(json.dumps({"world_range": [start_world, stop_world], "coverage": dict(coverage),
                      "maxima": maxima, "maximum_records": maximum_records,
                      "profile_failures": dict(failures), "profile": dict(scanner.SEMANTIC_PROFILES["birth_full_v1"]),
                      "elapsed_seconds": round(perf_counter() - started, 3),
                      "whole_prefix_scanner_passes": 0, "all_science_flags": False}, sort_keys=True), flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--measure-envelope"]:
        measure_envelope()
    else:
        unittest.main()
