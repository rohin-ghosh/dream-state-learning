"""Synthetic source-shape, checker and population-join tests, CPU only.

No actual birth/intervention/chain constructors or outcome fixtures are run or
compared. The full-shaped roster deliberately reuses tiny synthetic graphs and
non-authentic encoded source shapes. These tests do NOT establish full-source
execution, constructor provenance, or actual held-versus-birth separation.
"""

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from hashlib import sha256
import inspect
from types import MappingProxyType
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_chain_core_inputs as chains
from organism_v6 import composition_birth_stage2a_checker as checker
from organism_v6 import composition_birth_stage2a_core_inputs as births
from organism_v6 import composition_birth_stage2a_graph as graph
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_held_core_inputs as interventions
from organism_v6 import composition_birth_stage2a_separation as separation
from organism_v6 import composition_birth_stage2a_worlds as worlds


def encode(value):
    return checker.canonical_json_bytes(value)


def synthetic_packet(*, extra_destination=False, skin=0):
    public = {"vertices": [
        {"alias": "E0000", "flags": ["ROOT_EVENT"], "type": "EVENT"},
        {"alias": "G0000", "flags": ["GOAL"], "type": "GOAL"},
        {"alias": "P0000", "flags": ["ROOT_PORT"], "type": "PORT"},
        {"alias": "S0000", "flags": ["CURRENT"], "type": "STATE"}],
        "edges": sorted([
            {"tails": ["E0000"], "heads": ["S0000"], "label": "AT"},
            {"tails": ["E0000"], "heads": ["P0000"], "label": "DID"},
            {"tails": ["E0000"], "heads": ["G0000"], "label": "FOR"}], key=encode)}
    world = deepcopy(public)
    if extra_destination:
        world["vertices"].append({"alias": "S0001", "flags": [], "type": "STATE"})
        world["edges"].append({"tails": ["E0000"], "heads": ["S0001"], "label": "GOT"})
        world["edges"].sort(key=encode)
    core = graph.decision_core(
        public, actual_route_depth=1, family_motif="A_PRIVATE_SPOKES", flow="ORDINARY",
        goal_side="LEFT", phase="CONTINUE", predicted_actual_match=None, recovery_subtype="NONE",
        relevant_candidate_display_position=None, skin=skin, terminal_class="UNRESOLVED",
        step_outcome_observed=False)
    hashes = {"core": graph.core_hash(core, step_outcome_observed=False),
              "world_graph": graph.graph_hash(world), "public_graph": graph.graph_hash(public),
              "radii": graph.signature(world), "signature": graph.signature_hash(world)}
    envelope = {"schema_version": checker.SCHEMA_VERSION, "core": core, "world_graph": world,
                "public_to_world_aliases": {vertex["alias"]: vertex["alias"] for vertex in public["vertices"]},
                "step_outcome_observed": False,
                "radius_graphs": {f"r{radius}": graph.radius_graph(world, radius) for radius in range(4)},
                "expected_hashes": hashes}
    payload = encode(envelope)
    return {"core_bytes": encode(core), "checker_payload": payload,
            "receipt_bytes": encode(checker.check_graph_core_json(payload)),
            "signature_bytes": graph.signature_bytes(world), "core_sha256": hashes["core"],
            "signature_sha256": hashes["signature"], "world_graph_bytes": graph.graph_bytes(world),
            "public_graph_bytes": graph.graph_bytes(public), "world_graph_sha256": hashes["world_graph"],
            "public_graph_sha256": hashes["public_graph"]}


def birth_record(packet, identity=("p00/m0/u0", "CLOSED")):
    return births.BirthCoreInputs(identity[0], identity[1], packet["core_bytes"],
                                  packet["checker_payload"], packet["receipt_bytes"], 1)


def binding(packet, *, world, member, source, roles, prefix, target, decision=None):
    result = {"schema_version": ("M2A-CHAIN-CORE-BINDING-V1" if decision is not None
                                 else interventions.BINDING_SCHEMA_VERSION),
              "status": "PARTIAL_SOURCE_ONLY", "world": world, "member": member,
              "binding_sha256": chains.BINDING_SHA256 if decision is not None else interventions.BINDING_SHA256,
              "hashes": checker.loads_canonical_json(packet["receipt_bytes"])["hashes"]}
    if decision is not None:
        result["decision_index"] = decision
    for name, raw in (("source", source), ("role_bindings", roles), ("prefix", prefix), ("target", target),
                      ("checker_payload", packet["checker_payload"]), ("checker_receipt", packet["receipt_bytes"])):
        result[name + "_sha256"] = sha256(raw).hexdigest()
    return encode(result)


def intervention_record(packet, identity=("seek_k0", "m0")):
    world, member = identity
    prefix, target, roles = encode([]), b"STOP", encode({})
    source = encode({"construction": {"world": world}, "member": member,
                     "expected_causal_prefix": [], "expected_target": {"bytes": "STOP"}})
    return interventions.InterventionCoreInputs(
        world=world, member=member, **packet, source_bytes=source, role_bindings_bytes=roles,
        prefix_bytes=prefix, target_bytes=target,
        binding_receipt_bytes=binding(packet, world=world, member=member, source=source,
                                      roles=roles, prefix=prefix, target=target))


def encoded_shape(cls, **values):
    return {"dataclass": cls.__module__ + "." + cls.__qualname__,
            "fields": [[field.name, values.get(field.name)] for field in fields(cls)]}


def encoded_message(role, content):
    return encoded_shape(held.Message, role=role, content=content)


def chain_record(packet, world="h00", trace_lengths=(2, 3)):
    members, expected = [], {}
    for member, length in zip(("m0", "m1"), trace_lengths):
        task = {"start": "synthetic-start", "goal": "synthetic-goal", "current": "synthetic-start"}
        prefix = [encoded_message("system", wire.SYSTEM_MESSAGE),
                  encoded_message("user", "TASK\nSTART synthetic-start\nGOAL synthetic-goal\nCURRENT synthetic-start")]
        trace = []
        for index in range(length):
            action = "STOP" if index == length - 1 else f"READ synthetic-service-{index}"
            response = None if action == "STOP" else f"SERVICE\nsynthetic-response-{index}"
            expected[member, index] = encode({"tuple": deepcopy(prefix)}), action.encode("ascii")
            trace.append(encoded_shape(held.WitnessTurn, action=action, response=response,
                                       current_before="synthetic-start", current_after="synthetic-start"))
            if response is not None:
                prefix.extend((encoded_message("assistant", action), encoded_message("user", response)))
        members.append(encoded_shape(held.ChainMember, member=member, task=encoded_shape(wire.TaskState, **task),
                                     expected_trace={"tuple": trace}))
    source = encode(encoded_shape(held.ChainWorld, members={"tuple": members},
                                 construction=encoded_shape(worlds.OrdinaryConstruction, world=world)))
    roles = encode({})
    boundaries = []
    selected = {field.name: packet[field.name] for field in fields(chains.ChainCoreBoundary) if field.name in packet}
    for (member, index), (prefix, target) in expected.items():
        boundaries.append(chains.ChainCoreBoundary(
            world=world, member=member, decision_index=index, prefix_bytes=prefix, target_bytes=target,
            binding_receipt_bytes=binding(packet, world=world, member=member, decision=index,
                                          source=source, roles=roles, prefix=prefix, target=target), **selected))
    return chains.ChainCoreInputs(world, source, roles, tuple(boundaries))


class SeparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.birth_packet = synthetic_packet()
        cls.held_packet = synthetic_packet(extra_destination=True, skin=1)
        cls.birth_roster = {identity: birth_record(cls.birth_packet, identity)
                            for identity in separation.BIRTH_IDENTITIES}
        cls.intervention_roster = tuple(intervention_record(cls.held_packet, identity)
                                        for identity in sorted(separation.INTERVENTION_IDENTITIES))
        cls.chain_roster = tuple(chain_record(cls.held_packet, world) for world in sorted(separation.CHAIN_WORLDS))

    def join(self, *, birth=None, intervention=None, chain=None):
        return separation.check_held_birth_separation(
            birth_inputs=self.birth_roster if birth is None else birth,
            intervention_inputs=self.intervention_roster if intervention is None else intervention,
            chain_core_inputs=self.chain_roster if chain is None else chain)

    def assert_rejected(self, **inputs):
        with self.assertRaises(separation.SeparationError):
            self.join(**inputs)

    def test_api_has_no_green_flags_and_no_external_execution(self):
        self.assertEqual(tuple(inspect.signature(separation.check_held_birth_separation).parameters),
                         ("birth_inputs", "intervention_inputs", "chain_core_inputs"))
        source = inspect.getsource(separation)
        for forbidden in ("subprocess", "import torch", "import requests", "open(", "build_birth_",
                          "build_intervention_", "build_chain_", "graph.signature("):
            self.assertNotIn(forbidden, source)
        self.assertIn("Full constructor", separation.__doc__)
        self.assertEqual(len(separation.BIRTH_IDENTITIES), 512)
        self.assertEqual(len(separation.INTERVENTION_IDENTITIES), 64)
        self.assertEqual(len(separation.CHAIN_WORLDS), 16)

    def test_complete_synthetic_roster_real_checker_counts_and_closed_gates(self):
        with patch.object(checker, "check_graph_core_json", wraps=checker.check_graph_core_json) as check:
            result = self.join()
        self.assertEqual(check.call_count, 512 + 64 + 80)
        self.assertTrue(result.separated)
        for name, count in (("birth_records", 512), ("birth_units", 256), ("intervention_members", 64),
                            ("chain_worlds", 16), ("chain_members", 32), ("chain_boundaries", 80),
                            ("held_records", 144), ("checked_envelopes", 656)):
            self.assertEqual(result.counts[name], count)
        self.assertTrue(result.cpu_only)
        self.assertTrue(result.constructor_provenance_is_upstream_duty)
        for name in ("source_authenticated", "full_constructor_provenance_checked", "native_authorized", "native_ready"):
            self.assertIs(getattr(result, name), False)
        self.assertFalse(any(result.science_gates.values()))
        self.assertEqual(result.status, "PARTIAL_SOURCE_ONLY")
        for name in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU",
                     "GO_CLAIM", "GO_SOURCE_READY"):
            self.assertIs(getattr(separation, name), False)
        with self.assertRaises(FrozenInstanceError):
            result.core_collisions = ()
        with self.assertRaises(TypeError):
            result.counts["birth_records"] = 1

    def test_individual_radius_overlap_is_not_full_signature_collision(self):
        birth_hashes = checker.loads_canonical_json(self.birth_packet["receipt_bytes"])["hashes"]
        held_hashes = checker.loads_canonical_json(self.held_packet["receipt_bytes"])["hashes"]
        self.assertEqual(birth_hashes["radii"]["r0"], held_hashes["radii"]["r0"])
        self.assertNotEqual(birth_hashes["signature"], held_hashes["signature"])
        self.assertTrue(self.join().separated)

    def test_full_core_and_signature_joins_are_independent_and_keep_all_identities(self):
        core_only = synthetic_packet(extra_destination=True)
        signature_only = synthetic_packet(skin=1)
        selected = list(self.intervention_roster)
        identities = [(record.world, record.member) for record in selected[:3]]
        selected[0] = intervention_record(core_only, identities[0])
        selected[1] = intervention_record(signature_only, identities[1])
        selected[2] = intervention_record(self.birth_packet, identities[2])
        chain = (chain_record(self.birth_packet),) + self.chain_roster[1:]
        result = self.join(intervention=selected, chain=chain)
        self.assertFalse(result.separated)
        for name, groups, members in (("core", result.core_collisions, (identities[0], identities[2])),
                                      ("signature", result.signature_collisions, (identities[1], identities[2]))):
            self.assertEqual(len(groups), 1)
            collision = groups[0]
            self.assertEqual(collision.birth_identities, tuple(sorted(separation.BIRTH_IDENTITIES)))
            expected = {separation.HeldIdentity("intervention", world, member, None) for world, member in members}
            expected.update(separation.HeldIdentity("chain", "h00", boundary.member, boundary.decision_index)
                            for boundary in chain[0].boundaries)
            self.assertEqual(set(collision.held_identities), expected)
            self.assertEqual(collision.pair_count, 512 * 7)
            self.assertEqual(result.counts[name + "_collision_pairs"], 512 * 7)
            self.assertEqual(result.counts[name + "_collision_hashes"], 1)
            self.assertEqual(len(collision.sha256), 64)

    def test_hash_join_never_uses_partial_digest_or_combined_core_signature(self):
        identity = ("p00/m0/u0", "CLOSED")
        other = separation.HeldIdentity("intervention", "seek_k0", "m0", None)
        left = [(identity, {"core": "a" * 63 + "0", "signature": "b" * 64})]
        right = [(other, {"core": "a" * 63 + "1", "signature": "b" * 64})]
        self.assertEqual(separation._collisions(left, right, "core"), ())
        self.assertEqual(separation._collisions(left, right, "signature")[0].pair_count, 1)

    def test_order_does_not_change_report_or_inputs(self):
        original = dict(self.birth_roster)
        expected = self.join()
        actual = self.join(birth=dict(reversed(list(original.items()))),
                           intervention=tuple(reversed(self.intervention_roster)),
                           chain=tuple(replace(chain, boundaries=tuple(reversed(chain.boundaries)))
                                       for chain in reversed(self.chain_roster)))
        self.assertEqual(actual, expected)
        self.assertEqual(self.birth_roster, original)

    def test_exact_birth_identity_set_not_just_counts(self):
        identity = ("p00/m0/u0", "CLOSED")
        for foreign in (("p32/m0/u0", "CLOSED"), ("p00/m2/u0", "CLOSED"),
                        ("p00/m0/u4", "CLOSED"), ("p00/m0/u0", "FOREIGN_ARM")):
            roster = dict(self.birth_roster)
            record = roster.pop(identity)
            roster[foreign] = replace(record, unit_id=foreign[0], arm=foreign[1])
            self.assert_rejected(birth=roster)
        missing = dict(self.birth_roster)
        missing.pop(identity)
        self.assert_rejected(birth=missing)
        mismatched = dict(self.birth_roster)
        mismatched[identity] = replace(mismatched[identity], arm="ATOM_LOCAL")
        self.assert_rejected(birth=mismatched)
        self.assert_rejected(birth=list(self.birth_roster.values()))

    def test_exact_intervention_and_chain_world_sets_not_just_counts(self):
        for changes in ({"world": "seek_k8"}, {"world": "foreign_k0"}, {"member": "m2"}):
            self.assert_rejected(intervention=(replace(self.intervention_roster[0], **changes),)
                                 + self.intervention_roster[1:])
        self.assert_rejected(intervention=self.intervention_roster[1:])
        self.assert_rejected(intervention=(self.intervention_roster[1],) + self.intervention_roster[1:])
        self.assert_rejected(chain=(replace(self.chain_roster[0], world="h16"),) + self.chain_roster[1:])
        self.assert_rejected(chain=(self.chain_roster[1],) + self.chain_roster[1:])
        self.assert_rejected(chain=self.chain_roster[:-1])

    def test_typed_inputs_and_bounds_fail_before_checker(self):
        identity = ("p00/m0/u0", "CLOSED")
        with patch.object(checker, "check_graph_core_json", side_effect=AssertionError("must preflight first")):
            for value in (None, b"", bytearray(b"{}")):
                roster = dict(self.birth_roster)
                roster[identity] = (value if value is None else
                                    replace(roster[identity], core_bytes=value))
                self.assert_rejected(birth=roster)
            self.assert_rejected(intervention=(None,) + self.intervention_roster[1:])
            self.assert_rejected(chain=(None,) + self.chain_roster[1:])
            first = self.chain_roster[0]
            for boundaries in ((None,) * 2, first.boundaries * 30):
                self.assert_rejected(chain=(replace(first, boundaries=boundaries),) + self.chain_roster[1:])
            for changed in ({"blob_bytes": 16}, {"total_bytes": 16}):
                with patch.object(separation, "BOUNDS", MappingProxyType(dict(separation.BOUNDS, **changed))):
                    self.assert_rejected()

    def test_exact_core_receipt_signature_graph_bytes_and_hashes(self):
        record = intervention_record(self.held_packet)
        for field in ("core_bytes", "receipt_bytes", "signature_bytes", "world_graph_bytes", "public_graph_bytes"):
            with self.subTest(field=field), self.assertRaises(separation.SeparationError):
                separation._checked_hashes(replace(record, **{field: getattr(record, field) + b" "}))
        for field in ("core_sha256", "signature_sha256", "world_graph_sha256", "public_graph_sha256"):
            with self.subTest(field=field), self.assertRaises(separation.SeparationError):
                separation._checked_hashes(replace(record, **{field: "0" * 64}))
        receipt = checker.loads_canonical_json(record.receipt_bytes)
        receipt["certifications"]["provenance"] = True
        with self.assertRaisesRegex(separation.SeparationError, "receipt_bytes"):
            separation._checked_hashes(replace(record, receipt_bytes=encode(receipt)))

    def test_existing_checker_rejects_full_envelope_schema_mutations(self):
        packet = self.held_packet
        envelope = checker.loads_canonical_json(packet["checker_payload"])
        mutations = []
        for name in ("radius_graphs", "public_to_world_aliases", "step_outcome_observed"):
            changed = deepcopy(envelope)
            changed.pop(name)
            mutations.append(changed)
        changed = deepcopy(envelope)
        changed["schema_version"] = "M2A-PARTIAL-GRAPH-CHECK-V1"
        mutations.append(changed)
        changed = deepcopy(envelope)
        changed["expected_hashes"]["radii"].pop("r3")
        mutations.append(changed)
        changed = deepcopy(envelope)
        changed["core"]["actual_route_depth"] += 1
        mutations.append(changed)
        changed = deepcopy(envelope)
        changed["core"]["typed_vertex_counts"]["STATE"] += 1
        mutations.append(changed)
        changed = deepcopy(envelope)
        changed["core"]["new_separation_salt"] = "forbidden"
        mutations.append(changed)
        for name in ("core", "signature", "world_graph", "public_graph"):
            changed = deepcopy(envelope)
            changed["expected_hashes"][name] = changed["expected_hashes"][name][:63]
            mutations.append(changed)
        changed = deepcopy(envelope)
        changed["public_to_world_aliases"]["S0000"] = "S0001"
        mutations.append(changed)
        changed = deepcopy(envelope)
        changed["radius_graphs"]["r3"]["edges"].pop()
        mutations.append(changed)
        for changed in mutations:
            with self.subTest(changed=changed), self.assertRaises(checker.GraphCheckError):
                separation._checked_hashes(replace(birth_record(packet), checker_payload=encode(changed)))
        with self.assertRaises(checker.GraphCheckError):
            separation._checked_hashes(replace(birth_record(packet), checker_payload=packet["checker_payload"] + b" "))

    def test_binding_byte_hash_mutations_and_source_identity_links(self):
        record = intervention_record(self.held_packet)
        hashes = separation._checked_hashes(record)
        for field in ("source_bytes", "role_bindings_bytes", "prefix_bytes", "target_bytes", "checker_payload", "receipt_bytes"):
            changed = replace(record, **{field: getattr(record, field) + b" "})
            with self.subTest(field=field), self.assertRaises(separation.SeparationError):
                separation._binding(changed, hashes, changed.source_bytes, changed.role_bindings_bytes, interventions)
        for name in ("schema_version", "world", "member", "binding_sha256", "checker_receipt_sha256"):
            modified = checker.loads_canonical_json(record.binding_receipt_bytes)
            modified[name] = "foreign"
            with self.subTest(name=name), self.assertRaises(separation.SeparationError):
                separation._binding(replace(record, binding_receipt_bytes=encode(modified)), hashes,
                                    record.source_bytes, record.role_bindings_bytes, interventions)
        for changes in ({"world": "check_k0"}, {"member": "m1"}, {"target_bytes": b"READ other"},
                        {"prefix_bytes": encode(["foreign"])}):
            with self.assertRaises(separation.SeparationError):
                separation._intervention_source(replace(record, **changes))

    def test_invalid_record_aborts_join_rather_than_skipping_it(self):
        record = self.intervention_roster[-1]
        self.assert_rejected(intervention=self.intervention_roster[:-1] + (replace(record, receipt_bytes=b"{}"),))

    def test_chain_complete_contiguous_indices_include_last_boundary(self):
        first = self.chain_roster[0]
        boundary = first.boundaries[0]
        variants = [first.boundaries[:-1], first.boundaries[1:],
                    first.boundaries[:1] + first.boundaries,
                    (first.boundaries[1],) + first.boundaries[1:],
                    tuple(item for item in first.boundaries if item.member == "m0")]
        for changes in ({"world": "h01"}, {"member": "m2"}, {"decision_index": -1},
                        {"decision_index": 9}, {"decision_index": False}, {"decision_index": 0.0},
                        {"prefix_bytes": encode({"tuple": []})}, {"target_bytes": b"READ foreign"}):
            variants.append((replace(boundary, **changes),) + first.boundaries[1:])
        for boundaries in variants:
            with self.subTest(boundaries=boundaries):
                self.assert_rejected(chain=(replace(first, boundaries=boundaries),) + self.chain_roster[1:])

    def test_chain_schema_member_roster_and_prefix_coverage(self):
        first = self.chain_roster[0]
        expected = separation._chain_witnesses(first)
        self.assertEqual({member: len(trace) for member, trace in expected.items()}, {"m0": 2, "m1": 3})
        for boundary in first.boundaries:
            self.assertEqual(expected[boundary.member][boundary.decision_index],
                             (boundary.prefix_bytes, boundary.target_bytes))
        source = checker.loads_canonical_json(first.source_bytes)
        variants = []
        changed = deepcopy(source)
        changed["dataclass"] = "untrusted.ForeignChain"
        variants.append(changed)
        changed = deepcopy(source)
        changed["fields"].append(changed["fields"][0])
        variants.append(changed)
        for member_count in (1, 3):
            changed = deepcopy(source)
            members = dict(changed["fields"])["members"]["tuple"]
            members[:] = [members[0]] * member_count
            variants.append(changed)
        changed = deepcopy(source)
        members = dict(changed["fields"])["members"]["tuple"]
        members[1] = deepcopy(members[0])
        variants.append(changed)
        changed = deepcopy(source)
        member = dict(changed["fields"])["members"]["tuple"][0]
        dict(member["fields"])["expected_trace"]["tuple"] *= wire.CALL_CAP
        variants.append(changed)
        for changed in variants:
            with self.assertRaises(separation.SeparationError):
                separation._chain_witnesses(replace(first, source_bytes=encode(changed)))
        with self.assertRaises(separation.SeparationError):
            separation._chain_witnesses(replace(first, world="h01"))

    def test_chain_binding_commits_source_roles_and_every_boundary(self):
        chain = self.chain_roster[0]
        for boundary in chain.boundaries:
            hashes = separation._checked_hashes(boundary)
            for name, raw in (("source", chain.source_bytes + b" "), ("roles", chain.role_bindings_bytes + b" ")):
                with self.subTest(member=boundary.member, index=boundary.decision_index, changed=name):
                    with self.assertRaises(separation.SeparationError):
                        separation._binding(boundary, hashes,
                                            raw if name == "source" else chain.source_bytes,
                                            raw if name == "roles" else chain.role_bindings_bytes, chains)
            for field in ("prefix_bytes", "target_bytes", "receipt_bytes", "checker_payload"):
                changed = replace(boundary, **{field: getattr(boundary, field) + b" "})
                with self.assertRaises(separation.SeparationError):
                    separation._binding(changed, hashes, chain.source_bytes, chain.role_bindings_bytes, chains)
            for field, value in (("decision_index", boundary.decision_index + 1),
                                 ("decision_index", False), ("world", "h15"), ("member", "m2")):
                altered = checker.loads_canonical_json(boundary.binding_receipt_bytes)
                altered[field] = value
                with self.assertRaises(separation.SeparationError):
                    separation._binding(replace(boundary, binding_receipt_bytes=encode(altered)), hashes,
                                        chain.source_bytes, chain.role_bindings_bytes, chains)

    def test_all_synthetic_hashes_equal_retains_full_cartesian_roster(self):
        interventions_same = tuple(intervention_record(self.birth_packet, (record.world, record.member))
                                   for record in self.intervention_roster)
        chains_same = tuple(chain_record(self.birth_packet, chain.world) for chain in self.chain_roster)
        result = self.join(intervention=interventions_same, chain=chains_same)
        for collisions in (result.core_collisions, result.signature_collisions):
            self.assertEqual(len(collisions), 1)
            self.assertEqual(len(collisions[0].birth_identities), 512)
            self.assertEqual(len(collisions[0].held_identities), 144)
            self.assertEqual(collisions[0].pair_count, 73728)


if __name__ == "__main__":
    unittest.main()
