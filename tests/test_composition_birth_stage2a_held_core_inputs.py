"""All 64 source-only intervention cores; no held/birth separation comparison."""

from dataclasses import FrozenInstanceError, fields, replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import unittest

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_checker as checker
from organism_v6 import composition_birth_stage2a_graph as graph
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_held_core_inputs as source
from organism_v6 import composition_birth_stage2a_worlds as worlds
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_held import fixtures, pointer_diff, replay_prefix, thaw


def forged(member, **changes):
    result = object.__new__(type(member))
    for field in fields(member):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(member, field.name)))
    return result


class InterventionCoreInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokens = fixtures("dose_intervention")
        cls.pairs = {world: held.build_intervention_pair(world=world, role_tokens=tokens)
                     for world, tokens in cls.tokens.items()}
        cls.results = {(world, member.member): source.build_intervention_core_inputs(
            member=member, role_tokens=cls.tokens[world])
            for world, pair in cls.pairs.items() for member in pair.members}

    def build(self, member, tokens=None, **kwargs):
        return source.build_intervention_core_inputs(
            member=member, role_tokens=self.tokens[member.construction.world] if tokens is None else tokens,
            **kwargs)

    def test_binding_and_closed_gates(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(sha256((root / source.BINDING_PATH).read_bytes()).hexdigest(), source.BINDING_SHA256)
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        for name in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU",
                     "GO_CLAIM", "GO_SOURCE_READY"):
            self.assertIs(getattr(source, name), False)
        for result in self.results.values():
            binding = result.binding_receipt
            self.assertEqual(binding["schema_version"], source.BINDING_SCHEMA_VERSION)
            self.assertEqual(binding["binding_sha256"], source.BINDING_SHA256)
            self.assertEqual(binding["contract_sha256"], held.MEMO_SHA256)
            self.assertEqual(binding["clarification_sha256"], held.CLARIFICATION_SHA256)
            self.assertEqual(binding["route_corrigendum_sha256"], held.ROUTE_CORRIGENDUM_SHA256)
            for flag in ("source_ready", "native_ready", "held_birth_separation_checked"):
                self.assertIs(binding[flag], False)
            self.assertFalse(any(binding["science_gates"].values()))
            self.assertFalse(any(result.receipt["certifications"].values()))

    def test_all_64_exact_source_targets_prefixes_and_pair_differences(self):
        self.assertEqual(len(self.results), 64)
        for world, pair in self.pairs.items():
            rebuilt = held.build_intervention_pair(world=world, role_tokens=self.tokens[world])
            self.assertEqual(pair, rebuilt)
            self.assertEqual(pointer_diff(thaw(pair.members[0].semantic_object),
                                          thaw(pair.members[1].semantic_object)),
                             set(pair.allowed_differences))
            for member in pair.members:
                with self.subTest(world=world, member=member.member):
                    result = self.results[world, member.member]
                    saved = json.loads(result.source_bytes)
                    self.assertEqual(saved["semantic_object"], thaw(member.semantic_object))
                    self.assertEqual(saved["construction"]["registry"], dict(member.registry))
                    self.assertEqual(saved["construction"]["world_edges"], [
                        {"key": list(key), "value": value} for key, value in sorted(member.world_edges.items())])
                    self.assertEqual(result.target_bytes, member.expected_target.bytes.encode("ascii"))
                    self.assertEqual(sha256(result.target_bytes).hexdigest(), member.expected_target.sha256)
                    self.assertEqual(json.loads(result.prefix_bytes), [
                        {"role": message.role, "content": message.content}
                        for message in member.public_view().prefix])
                    self.assertEqual(saved["expected_causal_prefix"], json.loads(result.prefix_bytes))
                    self.assertEqual(saved["expected_target"]["sha256"], member.expected_target.sha256)
                    self.assertEqual(json.loads(result.role_bindings_bytes), dict(self.tokens[world]))
                    for key, raw in (("source", result.source_bytes), ("prefix", result.prefix_bytes),
                                     ("target", result.target_bytes), ("role_bindings", result.role_bindings_bytes),
                                     ("checker_payload", result.checker_payload),
                                     ("checker_receipt", result.receipt_bytes)):
                        self.assertEqual(result.binding_receipt[key + "_sha256"], sha256(raw).hexdigest())

    def test_all_64_checker_and_unsalted_hash_algorithms(self):
        for key, result in self.results.items():
            with self.subTest(member=key):
                receipt = checker.check_graph_core_json(result.checker_payload)
                self.assertEqual(receipt, result.receipt)
                self.assertTrue(receipt["graph_checks_passed"])
                envelope = json.loads(result.checker_payload)
                self.assertEqual(result.world_graph_bytes, canonical_json(envelope["world_graph"]))
                self.assertEqual(result.public_graph_bytes, canonical_json(result.core["public_graph"]))
                self.assertEqual(result.core_bytes, canonical_json(envelope["core"]))
                self.assertEqual(set(result.core), graph.CORE_KEYS)
                radius_hashes = {}
                for radius in range(4):
                    name = f"r{radius}"
                    expected = graph.radius_graph(envelope["world_graph"], radius)
                    self.assertEqual(envelope["radius_graphs"][name], expected)
                    radius_hashes[name] = sha256(
                        b"M2A-RADIUS-V3\0" + str(radius).encode("ascii") + b"\0" + canonical_json(expected)
                    ).hexdigest()
                self.assertEqual(result.signature_bytes, canonical_json(radius_hashes))
                self.assertEqual(result.signature_sha256, sha256(
                    b"M2A-SIGNATURE-V3\0" + result.signature_bytes).hexdigest())
                self.assertEqual(result.core_sha256, sha256(b"M2A-CORE-V3\0" + result.core_bytes).hexdigest())
                for label, raw, digest in (("world_graph", result.world_graph_bytes, result.world_graph_sha256),
                                           ("public_graph", result.public_graph_bytes, result.public_graph_sha256)):
                    self.assertEqual(digest, sha256(b"M2A-GRAPH-V3\0" + raw).hexdigest())
                    self.assertEqual(result.hashes[label], digest)
                self.assertEqual(result.hashes["signature"], result.signature_sha256)
                self.assertEqual(result.hashes["core"], result.core_sha256)
                self.assertEqual(result.hashes["radii"], radius_hashes)

    def test_all_64_phase_position_depth_and_observed_ownership(self):
        for world, pair in self.pairs.items():
            for member in pair.members:
                with self.subTest(world=world, member=member.member):
                    result = self.results[world, member.member]
                    core, binding = result.core, result.binding_receipt
                    task, current, last_block, stepped_event = replay_prefix(member)
                    observed = stepped_event is not None
                    match = stepped_event.got == current if observed else None
                    self.assertEqual(binding["current"], current)
                    self.assertIs(binding["step_outcome_observed"], observed)
                    self.assertIs(core["predicted_actual_match"], match)
                    self.assertEqual(core["phase"], "STEP_CHECK" if member.transition_name == "check"
                                     else member.transition_name.upper())
                    self.assertEqual(core["actual_route_depth"], 0 if task.start == task.goal else 1)
                    self.assertEqual(core["terminal_class"], "REACHED" if current == task.goal else "UNRESOLVED")
                    self.assertEqual(core["family_motif"], "C_CROSSING_WEAVE")
                    self.assertEqual(core["skin"], member.construction.skin)
                    self.assertEqual(core["flow"], "RECOVERY" if match is False else "ORDINARY")
                    self.assertEqual(core["recovery_subtype"], "STEP_OUTCOME_MISMATCH" if match is False else "NONE")
                    position = None
                    if member.transition_name == "seek":
                        position = next(index for index, row in enumerate(last_block.rows)
                                        if row.node == current and row.goal == task.goal)
                    elif member.transition_name in ("prospect", "check"):
                        position = next(index for index, row in enumerate(last_block.rows)
                                        if row == member.selected_event)
                    self.assertEqual(core["relevant_candidate_display_position"], position)
                    self.assertEqual(binding["depth_basis"], "REGISTERED_DESIGNATED_SPAN")
                    self.assertEqual(binding["continuation_status"], "ALREADY_REACHED" if task.start == task.goal
                                     else "UNREGISTERED_AFTER_SPAN")
                    ownership = binding["source_ownership"]
                    self.assertEqual(ownership["event"], member.selected_event.event)
                    self.assertEqual(ownership["port"], member.selected_event.port)
                    self.assertEqual(self.tokens[world][ownership["event_role"]], member.selected_event.event)
                    self.assertEqual(self.tokens[world][ownership["port_role"]], member.selected_event.port)
                    self.assertEqual(ownership["effective_destination"], member.effective_transition(
                        task.start, member.selected_event.port))
                    registered = member.construction.blocks[ownership["registered_request"]]
                    self.assertEqual(registered.rows[ownership["registered_display_position"]], member.selected_event)

    def test_goal_side_comes_from_bound_goal_not_member_number(self):
        for world, pair in self.pairs.items():
            for member in pair.members:
                result = self.results[world, member.member]
                expected = "RIGHT" if member.transition_name == "seek" and member.member == "m1" else "LEFT"
                self.assertEqual(result.core["goal_side"], expected)
                if member.task.start != member.task.goal:
                    self.assertEqual(result.binding_receipt["goal_side_basis"], "BOUND_GOAL_ROLE")
                    self.assertEqual(result.binding_receipt["root_basis"], "DESIGNATED_SOURCE_EVENT")
                    self.assertEqual(self.tokens[world][result.binding_receipt["goal_role"]], member.task.goal)

    def test_reached_continue_uses_real_pair_left_reference_without_public_root(self):
        for index in range(8):
            world = f"continue_k{index}"
            member = self.pairs[world].members[0]
            result = self.results[world, "m0"]
            self.assertEqual(member.task.start, member.task.goal)
            self.assertNotEqual(member.selected_event.goal, member.task.goal)
            self.assertEqual(member.selected_event, self.pairs[world].members[1].selected_event)
            self.assertEqual(result.binding_receipt["root_basis"], "PAIR_REFERENCE_EVENT")
            self.assertEqual(result.binding_receipt["goal_side_basis"], "PAIR_REFERENCE")
            self.assertIsNone(result.core["predicted_actual_match"])
            self.assertIsNone(result.core["relevant_candidate_display_position"])
            world_graph = json.loads(result.world_graph_bytes)
            flags = {flag: vertex["alias"] for vertex in world_graph["vertices"] for flag in vertex["flags"]}
            self.assertIn({"label": "DID", "tails": [flags["ROOT_EVENT"]], "heads": [flags["ROOT_PORT"]]},
                          world_graph["edges"])
            public_flags = {flag for vertex in result.core["public_graph"]["vertices"] for flag in vertex["flags"]}
            self.assertEqual(public_flags, {"CURRENT", "GOAL"})
            self.assertEqual(result.core["public_graph"]["edges"], [])

    def test_effective_check_world_and_latest_current_do_not_modify_base_world(self):
        for index in range(8):
            world = f"check_k{index}"
            matched, mismatched = self.pairs[world].members
            self.assertEqual(matched.world_edges, mismatched.world_edges)
            for member in (matched, mismatched):
                result = self.results[world, member.member]
                envelope = json.loads(result.checker_payload)
                flags = {flag: vertex["alias"] for vertex in envelope["world_graph"]["vertices"]
                         for flag in vertex["flags"]}
                root_at = next(edge["heads"][0] for edge in envelope["world_graph"]["edges"]
                               if edge["label"] == "AT" and edge["tails"] == [flags["ROOT_EVENT"]])
                outcome = {"label": "WORLD", "tails": [root_at, flags["ROOT_PORT"]],
                           "heads": [flags["CURRENT"]]}
                self.assertIn(outcome, envelope["world_graph"]["edges"])
                public_outcomes = [edge for edge in result.core["public_graph"]["edges"] if edge["label"] == "WORLD"]
                self.assertEqual(len(public_outcomes), 1)
                aliases = envelope["public_to_world_aliases"]
                self.assertEqual([aliases[alias] for alias in public_outcomes[0]["heads"]], [flags["CURRENT"]])
                self.assertIs(result.core["predicted_actual_match"], member.member == "m0")

    def test_rejects_forged_selected_events_and_metadata(self):
        member = self.pairs["seek_k0"].members[0]
        foreign = self.pairs["seek_k1"].members[0].selected_event
        invalid = [forged(member, selected_event=foreign), forged(member, pair_index=False),
                   forged(member, transition_name="check"), forged(member, status="READY"),
                   forged(member, selected_event=replace(member.selected_event, got=member.alternate_destination)),
                   forged(member, task=replace(member.task, current=member.alternate_destination)),
                   forged(member, semantic_object=dict(member.semantic_object, evaluator={"answer": "STOP"}))]
        for candidate in invalid:
            with self.subTest(candidate=candidate.transition_name):
                with self.assertRaises(source.HeldCoreInputError):
                    self.build(candidate)

    def test_rejects_missing_edges_forged_effective_world_and_source_pins(self):
        member = self.pairs["check_k2"].members[1]
        key = (member.task.start, member.selected_event.port)
        missing = dict(member.world_edges)
        del missing[key]
        changed = dict(member.world_edges)
        changed[key] = member.alternate_destination
        for construction in (replace(member.construction, world_edges=missing),
                             replace(member.construction, world_edges=changed),
                             replace(member.construction, memo_sha256="0" * 64),
                             replace(member.construction, skin=0),
                             replace(member.construction, scope="ORDINARY_WORLD_ONLY")):
            if construction == member.construction:
                continue
            with self.assertRaises(source.HeldCoreInputError):
                self.build(forged(member, construction=construction))
        wrong = held.OutcomeIntervention("OUTCOME_DESTINATION", member.selected_event.got)
        with self.assertRaises(source.HeldCoreInputError):
            self.build(forged(member, intervention=wrong))

    def test_rejects_self_consistent_but_nonconstructor_service_changes(self):
        member = self.pairs["seek_k0"].members[0]
        request, block = next((request, block) for request, block in member.construction.blocks.items()
                              if block.kind == "EVENTS" and member.selected_event not in block.rows)
        rows = list(block.rows)
        rows[0] = replace(rows[0], goal=member.task.goal if rows[0].goal != member.task.goal else rows[1].goal)
        raw = worlds.render_service("EVENTS", rows, skin=member.construction.skin)
        blocks, registry = dict(member.construction.blocks), dict(member.registry)
        blocks[request] = wire.parse_service(raw, skin=member.construction.skin)
        registry[request] = raw
        construction = replace(member.construction, blocks=blocks, registry=registry)
        self.assertNotEqual(construction, member.construction)
        with self.assertRaises(source.HeldCoreInputError):
            self.build(replace(member, construction=construction))

    def test_rejects_target_and_retained_prefix_forgery(self):
        member = self.pairs["check_k0"].members[1]
        changed_target = replace(member.expected_target, bytes="STOP", command="STOP", operand=None,
                                 sha256=sha256(b"STOP").hexdigest())
        with self.assertRaises(source.HeldCoreInputError):
            self.build(replace(member, expected_target=changed_target))
        prefix = member.expected_causal_prefix
        alterations = [prefix[:-2], prefix + prefix[-2:],
                       prefix[:-1] + (held.Message("user", "WORLD\nCURRENT " + member.selected_event.got),),
                       (held.Message("system", "forged"),) + prefix[1:],
                       prefix[:2] + (held.Message("assistant", "READ INDEX " + member.alternate_destination),) + prefix[3:],
                       prefix[:3] + (held.Message("user", "SERVICE\nMISS"),) + prefix[4:]]
        for altered in alterations:
            with self.assertRaises(source.HeldCoreInputError):
                self.build(replace(member, expected_causal_prefix=altered))

    def test_rejects_missing_foreign_master_duplicate_and_rebound_roles(self):
        member = self.pairs["prospect_k0"].members[0]
        tokens = dict(self.tokens["prospect_k0"])
        roles = list(tokens)
        missing = dict(tokens)
        del missing[roles[0]]
        extra = dict(tokens, master="M2AN_BBBBBBBBBBBB")
        master = {role: token for world_tokens in self.tokens.values() for role, token in world_tokens.items()}
        duplicate = dict(tokens)
        duplicate[roles[1]] = duplicate[roles[0]]
        rebound = dict(tokens)
        rebound[roles[0]] = "M2A" + tokens[roles[0]][3] + "_BBBBBBBBBBBB"
        for invalid in (None, [], missing, extra, master, duplicate, rebound, self.tokens["prospect_k1"]):
            with self.assertRaises(source.HeldCoreInputError):
                source.build_intervention_core_inputs(member=member, role_tokens=invalid)

    def test_api_has_no_root_depth_side_master_or_outcome_assertions(self):
        signature = inspect.signature(source.build_intervention_core_inputs)
        self.assertEqual(tuple(signature.parameters), ("member", "role_tokens"))
        self.assertTrue(all(parameter.kind == inspect.Parameter.KEYWORD_ONLY
                            for parameter in signature.parameters.values()))
        member = self.pairs["continue_k0"].members[0]
        for key in ("root_event", "actual_route_depth", "goal_side", "display_master", "world_current",
                    "step_outcome_observed", "predicted_actual_match", "observed_prefix"):
            with self.assertRaises(TypeError):
                self.build(member, **{key: None})

    def test_checker_still_rejects_improper_outcome_nullability(self):
        for key, observed, match in ((("check_k0", "m0"), False, None),
                                     (("check_k0", "m1"), True, None),
                                     (("continue_k0", "m0"), False, True)):
            envelope = json.loads(self.results[key].checker_payload)
            envelope["step_outcome_observed"] = observed
            envelope["core"]["predicted_actual_match"] = match
            with self.assertRaises(ValueError):
                checker.check_graph_core_json(checker.canonical_json_bytes(envelope))

    def test_result_is_immutable_deterministic_and_detached_from_caller(self):
        member = self.pairs["prospect_k1"].members[1]
        tokens = dict(self.tokens["prospect_k1"])
        result = self.build(member, tokens=tokens)
        self.assertEqual(result, self.results["prospect_k1", "m1"])
        tokens.clear()
        with self.assertRaises(FrozenInstanceError):
            result.core_bytes = b"forged"
        with self.assertRaises(TypeError):
            result.science_gates["GO_CLAIM"] = True
        result.core["actual_route_depth"] = 2
        result.receipt["graph_checks_passed"] = False
        result.binding_receipt["root_basis"] = "FORGED"
        result.hashes["radii"].clear()
        self.assertEqual(result.core["actual_route_depth"], 1)
        self.assertTrue(result.receipt["graph_checks_passed"])
        self.assertEqual(result.binding_receipt["root_basis"], "DESIGNATED_SOURCE_EVENT")
        self.assertEqual(len(result.hashes["radii"]), 4)


if __name__ == "__main__":
    unittest.main()
