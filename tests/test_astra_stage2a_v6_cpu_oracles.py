"""Focused synthetic CPU regression checks; no population or launch gate."""

from contextlib import ExitStack
from dataclasses import fields, replace
from hashlib import sha256
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_v6_cpu_oracles as oracles
from organism_v6 import composition_birth_stage2a_boundary as boundary
from organism_v6 import composition_birth_stage2a_future_inputs as futures
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_route_inputs as routes
from organism_v6 import composition_birth_stage2a_scan_inputs as bindings
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6 import composition_birth_stage2a_typed_scan as typed
from tests.test_composition_birth_stage2a_birth import DISPLAY_MASTER, synthetic_bindings


class CPUOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifiers = {
            number: boundary.BirthBoundaryVerifier(
                world=f"p{number:02d}", role_tokens=synthetic_bindings(number), display_master=DISPLAY_MASTER,
            ) for number in (2, 3, 9)
        }
        verifier = cls.verifiers[3]
        cls.record = next(record for record in verifier.records
                          if record.unit.phase == "STEP_CHECK" and record.arm == "CLOSED")
        cls.source = verifier._custody.source_for(cls.record)
        cls.result = verifier.verify(cls.record)

    def reject(self, result, message=None):
        with self.assertRaisesRegex(ValueError, message or "cpu_oracle"):
            oracles.verify_inventory_ownership(self.source, result)

    def test_authentic_every_phase_both_arms_and_members(self):
        coverage = set()
        for number, verifier in self.verifiers.items():
            for record in verifier.records:
                with self.subTest(world=number, unit=record.unit.unit_id, arm=record.arm):
                    source = verifier._custody.source_for(record)
                    result = verifier.verify(record)
                    self.assertIsNone(oracles.verify_inventory_ownership(source, result))
                    self.assertIsNone(oracles.assert_private_basis_totality(source, record, result.scan.private_basis))
                    coverage.add((record.unit.phase, record.arm))
        self.assertEqual(coverage, {(phase, arm) for phase in
                                   ("CONTINUE", "READ_CHECK", "PROSPECT", "STEP_CHECK", "SEEK")
                                   for arm in ("CLOSED", "ATOM_LOCAL")})

    def test_other_recovery_subtypes_and_skin(self):
        for number in (11,):
            verifier = boundary.BirthBoundaryVerifier(
                world=f"p{number:02d}", role_tokens=synthetic_bindings(number), display_master=DISPLAY_MASTER,
            )
            for record in verifier.records[:8]:
                with self.subTest(world=number, unit=record.unit.unit_id, arm=record.arm):
                    source = verifier._custody.source_for(record)
                    result = verifier.verify(record)
                    oracles.verify_inventory_ownership(source, result)
                    oracles.assert_private_basis_totality(source, record, result.scan.private_basis)

    def test_no_production_derivation_or_scanner_basis_is_an_oracle(self):
        with ExitStack() as stack:
            for module, name in ((bindings, "bind_birth_arm"), (bindings, "_bind"),
                                 (futures, "_derive_from_source"), (routes, "_derive_from_source"),
                                 (typed, "build_typed_private_basis"), (targets, "serialize_birth_case")):
                stack.enter_context(patch.object(module, name, side_effect=AssertionError("production oracle")))
            oracles.verify_inventory_ownership(self.source, self.result)
            oracles.assert_private_basis_totality(self.source, self.record, self.result.scan.private_basis)
            self.assertTrue(oracles.expected_private_probes(self.source, self.record))

    def test_candidate_origin_values_not_only_keys(self):
        future = self.result.future_inputs
        token = next(token for token, origins in future.candidate_provenance.items() if len(origins) > 1)
        origins = future.candidate_provenance[token]
        for changes in ({"role_key": "wrong/role/node"}, {"source_path": ("wrong", "source")},
                        {"source_path": ("case", "construction", "world_edges", "wrong", "port")}):
            with self.subTest(changes=changes):
                provenance = dict(future.candidate_provenance)
                provenance[token] = (replace(origins[0], **changes),) + origins[1:]
                self.reject(replace(self.result, future_inputs=replace(future, candidate_provenance=provenance)),
                            "candidate_provenance")
        for replacement in (origins[:1], origins + origins[:1], tuple(reversed(origins))):
            with self.subTest(replacement=replacement):
                provenance = dict(future.candidate_provenance)
                provenance[token] = replacement
                self.reject(replace(self.result, future_inputs=replace(future, candidate_provenance=provenance)))

    def test_future_set_and_disclosure_corruption(self):
        future = self.result.future_inputs
        token = next(iter(future.future_identifiers))
        for name, changed in (("candidates", future.candidates - {token}),
                              ("disclosed", future.disclosed | {token}),
                              ("future_identifiers", future.future_identifiers - {token}),
                              ("disclosure_provenance", {})):
            with self.subTest(field=name):
                self.reject(replace(self.result, future_inputs=replace(future, **{name: changed})))
        token, observations = next(iter(future.disclosure_provenance.items()))
        provenance = dict(future.disclosure_provenance)
        provenance[token] = (replace(observations[0], origin="task"),) + observations[1:]
        self.reject(replace(self.result, future_inputs=replace(future, disclosure_provenance=provenance)))

    def test_all_observation_fields_and_colluding_future_fail(self):
        binding = self.result.binding
        position = next(index for index, item in enumerate(binding.observations)
                        if item.origin == "service" and item.kind == "event_id")
        observation = binding.observations[position]
        mutations = dict(path="/messages/999/action/operand", start=observation.start + 1,
                         end=observation.end - 1, value=b"wrong-value", kind="issued_query", origin="actor",
                         observed_at=observation.observed_at + 1, source_trace_index=999,
                         evidence="wrong-message-hash", owner=b"wrong-owner", exemption_kind="protocol",
                         is_latest_current=True)
        self.assertEqual(set(mutations), {field.name for field in fields(observation)})
        for name, value in mutations.items():
            with self.subTest(field=name):
                changed = replace(observation, **{name: value})
                observations = binding.observations[:position] + (changed,) + binding.observations[position + 1:]
                changed_binding = replace(binding, observations=observations)
                future = self.result.future_inputs
                disclosures = {token: tuple(changed if item == observation else item for item in items)
                               for token, items in future.disclosure_provenance.items()}
                changed_future = replace(future, binding=changed_binding, disclosure_provenance=disclosures)
                self.reject(replace(self.result, binding=changed_binding, future_inputs=changed_future),
                            "binding ownership")

    def test_binding_offsets_original_indices_chronology_and_fields(self):
        binding = self.result.binding
        span = binding.message_spans[-1]
        for name, value in (("start", span.start + 1), ("end", span.end - 1), ("source_trace_index", 99),
                            ("observed_at", binding.decision_index), ("content_sha256", "0" * 64),
                            ("role", "assistant"), ("message_index", 999)):
            with self.subTest(span_field=name):
                spans = binding.message_spans[:-1] + (replace(span, **{name: value}),)
                self.reject(replace(self.result, binding=replace(binding, message_spans=spans)))
        for name, value in (("retained_trace_indices", (99,)), ("fields", binding.fields[:-1]),
                            ("decision_index", binding.decision_index - 1), ("current", b"wrong"),
                            ("projection_bytes", binding.projection_bytes + b"\n"),
                            ("projection_sha256", "0" * 64), ("source_prefix_sha256", "0" * 64),
                            ("public_messages", binding.public_messages[:-1]),
                            ("observed_contradiction", not binding.observed_contradiction)):
            with self.subTest(binding_field=name):
                self.reject(replace(self.result, binding=replace(binding, **{name: value})))
        changed = replace(binding, decision_index=binding.decision_index + 1)
        self.reject(replace(self.result, future_inputs=replace(self.result.future_inputs, binding=changed)),
                    "future binding ownership")

    def test_service_actor_world_and_task_ownership_cannot_be_swapped(self):
        binding = self.result.binding
        self.assertTrue({"service", "actor", "host", "task"} <= {item.origin for item in binding.observations})
        for origin in ("service", "actor", "host", "task"):
            position = next(index for index, item in enumerate(binding.observations) if item.origin == origin)
            observations = list(binding.observations)
            observations[position] = replace(observations[position], origin="system")
            with self.subTest(origin=origin):
                self.reject(replace(self.result, binding=replace(binding, observations=tuple(observations))))

    def test_route_transition_every_field_and_indexes(self):
        route = self.result.route_inputs
        port, edge = next(iter(route.transitions.items()))
        for field in fields(edge):
            changed = (("wrong", "path") if field.name == "source_path" else "wrong-source-value")
            transitions = dict(route.transitions)
            transitions[port] = replace(edge, **{field.name: changed})
            with self.subTest(edge_field=field.name):
                self.reject(replace(self.result, route_inputs=replace(route, transitions=transitions)))
        for name in ("ports_by_current", "ports_by_query"):
            index = dict(getattr(route, name))
            key = next(iter(index))
            for ports in (index[key][:-1], tuple(reversed(index[key])), index[key] + index[key][:1]):
                with self.subTest(index=name, ports=len(ports)):
                    self.reject(replace(self.result, route_inputs=replace(route, **{name: {**index, key: ports}})))
        self.reject(replace(self.result, route_inputs=replace(route, unavailable_recover_queries=frozenset())))
        self.reject(replace(self.result, route_inputs=replace(route, transitions={})))

    def test_canonical_inventory_bytes_and_hash_references(self):
        for field_name, reference in (("candidate_inventory_bytes", "candidate_inventory"),
                                      ("retained_inventory_bytes", "retained_inventory"),
                                      ("route_basis_bytes", "route_basis")):
            with self.subTest(inventory=field_name):
                raw = getattr(self.result, field_name) + b"\n"
                document = primitives.parse_canonical_json(self.result.boundary_bytes)
                document[reference].update(sha256=sha256(raw).hexdigest(), bytes=len(raw))
                self.reject(replace(self.result, **{field_name: raw},
                                    boundary_bytes=primitives.canonical_json(document)), field_name)
            for key in ("sha256", "bytes", "count"):
                with self.subTest(reference=reference, field=key):
                    document = primitives.parse_canonical_json(self.result.boundary_bytes)
                    document[reference][key] = "0" * 64 if key == "sha256" else document[reference][key] + 1
                    self.reject(replace(self.result, boundary_bytes=primitives.canonical_json(document)), "reference")
        self.reject(replace(self.result, boundary_bytes=self.result.boundary_bytes + b"\n"), "noncanonical")

    def test_boundary_ownership_fields_cannot_drift(self):
        for name in ("field_observations", "scanner_fields", "message_spans", "retained_trace_indices",
                     "public_projection", "disclosed_count", "source_provenance_sha256"):
            document = primitives.parse_canonical_json(self.result.boundary_bytes)
            document[name] = None
            with self.subTest(field=name):
                self.reject(replace(self.result, boundary_bytes=primitives.canonical_json(document)), "boundary " + name)

    def test_complete_source_derived_private_values_and_key_contract(self):
        probes = oracles.expected_private_probes(self.source, self.record)
        by_category = {category: {value for key, value in probes.items() if key.split(":")[0] == category}
                       for category in ("private_category", "private_role_key", "private_case_key", "private_unit_key")}
        self.assertEqual(by_category["private_role_key"], {role.encode("ascii") for role in self.source.role_tokens})
        self.assertEqual(by_category["private_case_key"], {b"p03/m0", b"p02/m0"})
        self.assertEqual(by_category["private_unit_key"], {f"p03/m0/u{index}".encode("ascii") for index in range(4)})
        for name in ("pair_type", "family", "family_motif", "flow", "recovery_subtype",
                     "terminal_class", "goal_side", "domain"):
            self.assertEqual(probes["private_category:case/descriptor/" + name],
                             getattr(self.source.case.descriptor, name).encode("ascii"))
        self.assertTrue(all(":" in key and key.split(":")[0] in by_category for key in probes))
        self.assertTrue(set(self.source.role_tokens.values()).isdisjoint(value.decode("ascii") for value in probes.values()))
        changed = replace(self.record, arm="ATOM_LOCAL")
        with self.assertRaisesRegex(ValueError, "record ownership"):
            oracles.expected_private_probes(self.source, changed)

    def test_private_basis_rejects_missing_duplicate_wrong_values_and_owners(self):
        basis = self.result.scan.private_basis
        for category in ("private_category", "private_role_key", "private_case_key", "private_unit_key"):
            position = next(index for index, item in enumerate(basis) if item.category == category)
            for changed in (basis[:position] + basis[position + 1:], basis + (basis[position],)):
                with self.subTest(category=category, count=len(changed)):
                    with self.assertRaisesRegex(ValueError, "private basis"):
                        oracles.assert_private_basis_totality(self.source, self.record, changed)
            for changes in ({"value": b"invented-fragment"}, {"category": "private_wrong"},
                            {"source_path": ("case", "invented", "pointer")}):
                with self.subTest(category=category, changes=changes):
                    changed = basis[:position] + (replace(basis[position], **changes),) + basis[position + 1:]
                    with self.assertRaisesRegex(ValueError, "private basis"):
                        oracles.assert_private_basis_totality(self.source, self.record, changed)


if __name__ == "__main__":
    unittest.main()
