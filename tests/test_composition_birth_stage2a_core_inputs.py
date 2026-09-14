"""Synthetic source-only birth core coverage, not scientific readiness."""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_checker as checker
from organism_v6 import composition_birth_stage2a_core_inputs as source
from organism_v6 import composition_birth_stage2a_graph as graph
from organism_v6 import composition_birth_stage2a_graph_inputs as graph_inputs
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_birth import changed_construction, synthetic_bindings


MASTER = b"synthetic-birth-core-source-only"


def rehashed(record, prefix):
    raw = targets.messages_bytes(prefix)
    return replace(record, prefix=prefix, prefix_sha256=sha256(raw).hexdigest(),
                   content_bytes=sum(len(message.content.encode("ascii")) for message in prefix),
                   serialized_bytes=len(raw))


def retained_outcomes(record, skin):
    rows = {}
    current = wire.parse_task(record.prefix[1].content).current
    outcomes = []
    for request, response in zip(record.prefix[2::2], record.prefix[3::2]):
        action = wire.parse_action(request.content)
        if action.operation == "READ":
            block = wire.parse_service(response.content[len("SERVICE\n"):], skin=skin)
            if block.kind == "EVENTS":
                rows.update({row.event: (position, row) for position, row in enumerate(block.rows)})
        elif action.operation == "STEP":
            owners = [(position, row) for position, row in rows.values()
                      if row.node == current and row.port == action.operand]
            if len(owners) != 1:
                raise AssertionError("fixture STEP must have one retained owner")
            current = wire.parse_world(response.content)
            outcomes.append((*owners[0], current))
    return outcomes


def completion_selection(case):
    current = case.facts.final_current
    directory_request = "READ INDEX " + current
    directory = case.construction.blocks[directory_request]
    route_position, route = next((position, row) for position, row in enumerate(directory.rows)
                                if row.node == current and row.goal == case.task.goal)
    relation_request = "READ RELATION " + route.query
    relation = case.construction.blocks[relation_request]
    event_position, event = next((position, row) for position, row in enumerate(relation.rows)
                                if row.node == current and row.goal == case.task.goal)
    return directory_request, route_position, relation_request, event_position, event


class BirthCoreInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokens = {number: synthetic_bindings(number) for number in range(32)}
        cls.roster = {number: birth.build_birth_pair(world=f"p{number:02d}", role_tokens=cls.tokens[number],
                                                    display_master=MASTER) for number in range(32)}
        cls.records = {(number, case.descriptor.member): targets.serialize_birth_case(case, role_tokens=cls.tokens[number])
                       for number, pair in cls.roster.items() for case in pair.cases}

    def producer(self, number=7, member=0, case=None, role_tokens=None):
        return source.BirthCoreInputProducer(case=self.roster[number].cases[member] if case is None else case,
                                            role_tokens=self.tokens[number] if role_tokens is None else role_tokens)

    def test_binding_pin_and_closed_gates(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(sha256((root / source.BINDING_PATH).read_bytes()).hexdigest(), source.BINDING_SHA256)
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        for gate in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"):
            self.assertIs(getattr(source, gate), False)

    def test_all_64_cases_both_arms_four_targets_and_private_completion(self):
        seen = set()
        depths = Counter()
        checked = 0
        original_check = checker.check_graph_core_json

        def counted_check(payload):
            nonlocal checked
            checked += 1
            return original_check(payload)

        with patch.object(birth, "build_birth_pair", side_effect=AssertionError("no world reconstruction")), \
                patch.object(checker, "check_graph_core_json", new=counted_check):
            for number, pair in self.roster.items():
                for case in pair.cases:
                    with self.subTest(world=pair.world, member=case.descriptor.member):
                        original_trace, original_targets = case.trace, case.targets
                        producer = self.producer(number, case=case)
                        semantic_depth = 1 if case.descriptor.terminal_class == "REACHED" else 2
                        physical_depth = semantic_depth + (case.descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH")
                        self.assertEqual(producer.actual_route_depth, physical_depth)
                        self.assertEqual(producer.semantic_route_depth, semantic_depth)
                        depths[physical_depth] += 1
                        for target, paired in zip(case.targets, self.records[number, case.descriptor.member]):
                            previous_world_hash = None
                            for record in (paired.closed, paired.atom_local):
                                before = targets.messages_bytes(record.training_messages)
                                result = producer.build(record)
                                core = result.core
                                receipt = result.receipt
                                envelope = json.loads(result.checker_payload)
                                outcomes = retained_outcomes(record, case.descriptor.skin)
                                latest = outcomes[-1] if outcomes else None
                                match = latest[1].got == latest[2] if latest else None
                                position = latest[0] if target.phase == "SEEK" and case.descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH" else target.selection_index
                                self.assertEqual(core["actual_route_depth"], physical_depth)
                                self.assertEqual(result.semantic_route_depth, semantic_depth)
                                self.assertIs(core["predicted_actual_match"], match)
                                self.assertIs(envelope["step_outcome_observed"], bool(outcomes))
                                self.assertEqual(core["relevant_candidate_display_position"], position)
                                self.assertEqual(core["phase"], target.phase)
                                self.assertEqual(core["terminal_class"], case.descriptor.terminal_class)
                                self.assertEqual(core["typed_vertex_counts"], graph.typed_vertex_counts(core["public_graph"]))
                                public_world_edges = [edge for edge in core["public_graph"]["edges"] if edge["label"] == "WORLD"]
                                self.assertEqual(len(public_world_edges), len(outcomes))
                                if case.descriptor.terminal_class == "UNRESOLVED":
                                    self.assertLess(len(public_world_edges), physical_depth)
                                if record.arm == "ATOM_LOCAL" and target.phase == "CONTINUE":
                                    self.assertEqual(core["public_graph"]["edges"], [])
                                    self.assertEqual(len(record.prefix), 2)
                                self.assertEqual(core, envelope["core"])
                                self.assertEqual(result.core_bytes, canonical_json(core))
                                self.assertEqual(receipt["input_sha256"], sha256(result.checker_payload).hexdigest())
                                self.assertEqual(receipt["hashes"], envelope["expected_hashes"])
                                self.assertTrue(receipt["graph_checks_passed"])
                                self.assertFalse(any(receipt["science_gates"].values()))
                                self.assertFalse(any(receipt["certifications"].values()))
                                self.assertFalse(any(result.science_gates.values()))
                                world_hash = receipt["hashes"]["world_graph"]
                                if previous_world_hash is not None:
                                    self.assertEqual(world_hash, previous_world_hash)
                                previous_world_hash = world_hash
                                self.assertEqual(record.unit.target_bytes, target.target_bytes)
                                self.assertEqual(targets.messages_bytes(record.training_messages), before)
                                self.assertEqual(record.supervised_message_index, len(record.prefix))
                                seen.add((pair.world, case.descriptor.member, target.ordinal, record.arm))
                        self.assertIs(case.trace, original_trace)
                        self.assertIs(case.targets, original_targets)
            self.assertEqual(checked, 512)
        self.assertEqual(len(seen), 512)
        self.assertEqual(set(depths), {1, 2, 3})

    def test_graph_and_alias_packets_equal_existing_source_builder(self):
        for number in (2, 7):
            case = self.roster[number].cases[0]
            producer = self.producer(number)
            root_event = case.facts.failed_event or case.facts.selected_event
            for target, paired in zip(case.targets, self.records[number, "m0"]):
                for record in (paired.closed, paired.atom_local):
                    with self.subTest(world=number, ordinal=target.ordinal, arm=record.arm):
                        result = producer.build(record)
                        envelope = json.loads(result.checker_payload)
                        arguments = dict(role_tokens=self.tokens[number], target_ordinal=target.ordinal,
                                         root_event=root_event, arm=record.arm)
                        expected_public = graph_inputs.build_public_graph(case, **arguments)
                        self.assertEqual(result.core["public_graph"], expected_public)
                        self.assertEqual(envelope["public_to_world_aliases"], graph_inputs.public_to_world_aliases(case, **arguments))
                        expected_world = graph_inputs.build_world_graph(
                            case.construction, role_tokens=self.tokens[number], current=target.current_before,
                            task_goal=case.task.goal, root_event=root_event)
                        self.assertEqual(envelope["world_graph"], expected_world)
                        self.assertEqual(result.receipt["hashes"]["radii"], graph.signature(expected_world))
                        self.assertEqual(result.receipt["hashes"]["signature"], graph.signature_hash(expected_world))

    def test_recovery_seek_uses_owning_rendered_event_not_directory_position(self):
        case = self.roster[7].cases[0]
        producer = self.producer()
        directory = case.construction.blocks[case.trace[0].action]
        directory_position = next(position for position, row in enumerate(directory.rows)
                                  if row.node == case.task.start and row.goal == case.task.goal)
        paired = next(pair for pair in self.records[7, "m0"] if pair.closed.unit.phase == "SEEK")
        event_position, event, observed = retained_outcomes(paired.atom_local, case.descriptor.skin)[-1]
        self.assertNotEqual(event.got, observed)
        self.assertEqual(event.recover, paired.closed.unit.operand)
        self.assertNotEqual(event_position, directory_position)
        for record in (paired.closed, paired.atom_local):
            core = producer.build(record).core
            self.assertEqual(core["relevant_candidate_display_position"], event_position)
            self.assertIs(core["predicted_actual_match"], False)
        public = producer.build(paired.atom_local).core["public_graph"]
        self.assertNotIn("INDEXES", {edge["label"] for edge in public["edges"]})

    def test_retained_history_and_missing_step_owner_boundaries(self):
        producer = self.producer()
        paired = next(pair for pair in self.records[7, "m0"] if pair.closed.unit.phase == "PROSPECT")
        self.assertIs(producer.build(paired.closed).core["predicted_actual_match"], False)
        self.assertIsNone(producer.build(paired.atom_local).core["predicted_actual_match"])
        final = self.records[7, "m0"][-1]
        self.assertIs(producer.build(final.closed).core["predicted_actual_match"], True)
        self.assertIsNone(producer.build(final.atom_local).core["predicted_actual_match"])
        with self.assertRaisesRegex(source.CoreInputError, "record_mismatch"):
            producer.build(rehashed(paired.atom_local, paired.closed.prefix))
        step_check = self.records[7, "m0"][0].atom_local
        missing_owner = step_check.prefix[:2] + step_check.prefix[4:]
        with self.assertRaisesRegex(source.CoreInputError, "event_owner"):
            source._observe(missing_owner, producer._inputs)
        with self.assertRaisesRegex(source.CoreInputError, "record_mismatch"):
            producer.build(rehashed(step_check, missing_owner))

    def test_missing_services_and_effective_transitions_rejected(self):
        case = self.roster[7].cases[0]
        directory_request, _, relation_request, _, event = completion_selection(case)
        for request in (directory_request, relation_request):
            registry, blocks = dict(case.construction.registry), dict(case.construction.blocks)
            del registry[request]
            del blocks[request]
            forged = replace(case, construction=replace(case.construction, registry=registry, blocks=blocks))
            with self.subTest(request=request), self.assertRaises(source.CoreInputError):
                self.producer(case=forged)
        for destination in (None, case.task.start):
            edges = dict(case.construction.world_edges)
            if destination is None:
                del edges[event.node, event.port]
            else:
                edges[event.node, event.port] = destination
            with self.subTest(destination=destination), self.assertRaises(source.CoreInputError):
                self.producer(case=replace(case, construction=changed_construction(case, edges=edges)))
        edges = dict(case.construction.world_edges)
        failed = next(turn for turn in case.trace if turn.action.startswith("STEP "))
        edges[failed.current_before, wire.parse_action(failed.action).operand] = case.task.goal
        with self.assertRaises(source.CoreInputError):
            self.producer(case=replace(case, construction=changed_construction(case, edges=edges)))

    def test_ambiguous_missing_completion_matches_and_cycles_rejected(self):
        case = self.roster[7].cases[0]
        directory_request, route_position, relation_request, event_position, event = completion_selection(case)
        relation = case.construction.blocks[relation_request]
        alternate_position = (event_position + 1) % len(relation.rows)
        alternate = relation.rows[alternate_position]
        ambiguous_rows = list(relation.rows)
        ambiguous_rows[alternate_position] = replace(alternate, node=event.node, goal=event.goal)
        edges = dict(case.construction.world_edges)
        destination = edges.pop((alternate.node, alternate.port))
        edges[event.node, alternate.port] = destination
        ambiguous = changed_construction(case, request=relation_request, rows=tuple(ambiguous_rows), edges=edges)
        with self.assertRaisesRegex(source.CoreInputError, "ambiguous_route_match"):
            self.producer(case=replace(case, construction=ambiguous))
        missing_rows = list(relation.rows)
        missing_rows[event_position] = replace(event, goal=case.task.start)
        missing = changed_construction(case, request=relation_request, rows=tuple(missing_rows))
        with self.assertRaisesRegex(source.CoreInputError, "ambiguous_route_match"):
            self.producer(case=replace(case, construction=missing))
        directory = case.construction.blocks[directory_request]
        rows = list(directory.rows)
        rows[(route_position + 1) % len(rows)] = replace(rows[(route_position + 1) % len(rows)],
                                                       node=event.node, goal=case.task.goal)
        duplicate = changed_construction(case, request=directory_request, rows=tuple(rows))
        trace = tuple(replace(turn, response="SERVICE\n" + duplicate.registry[directory_request])
                      if turn.action == directory_request else turn for turn in case.trace)
        with self.assertRaisesRegex(source.CoreInputError, "ambiguous_route_match"):
            self.producer(case=replace(case, construction=duplicate, trace=trace))
        for destination in (event.node, case.task.start):
            rows = list(relation.rows)
            rows[event_position] = replace(event, got=destination)
            edges = dict(case.construction.world_edges)
            edges[event.node, event.port] = destination
            cyclic = changed_construction(case, request=relation_request, rows=tuple(rows), edges=edges)
            with self.subTest(destination=destination), self.assertRaisesRegex(source.CoreInputError, "path_cycle"):
                self.producer(case=replace(case, construction=cyclic))
        edges = dict(case.construction.world_edges)
        edges[event.node, event.port] = case.facts.failed_prediction
        with self.assertRaisesRegex(source.CoreInputError, "altered_transition"):
            self.producer(case=replace(case, construction=changed_construction(case, edges=edges)))

    def test_wrong_targets_forged_prefixes_and_foreign_records_rejected(self):
        producer = self.producer()
        record = self.records[7, "m0"][0].closed
        wrong_unit = replace(record.unit, target_bytes=b"STOP", target_sha256=sha256(b"STOP").hexdigest(),
                             command="STOP", operand=None, selection_index=None)
        candidates = (replace(record, unit=wrong_unit), replace(record, arm="OTHER"),
                      replace(record, prefix_sha256="0" * 64), replace(record, content_bytes=record.content_bytes + 1),
                      replace(record, serialized_bytes=record.serialized_bytes + 1),
                      replace(record, unit=replace(record.unit, selection_index=float(record.unit.selection_index))),
                      replace(record, prefix=list(record.prefix)), self.records[7, "m1"][0].closed,
                      self.records[3, "m0"][0].closed, replace(record, content_bytes=float(record.content_bytes)))
        for candidate in candidates:
            with self.subTest(arm=candidate.arm, unit=candidate.unit.unit_id), self.assertRaisesRegex(source.CoreInputError, "record_mismatch"):
                producer.build(candidate)
        for prefix in (record.prefix[:-2], record.prefix + (targets.Message("assistant", "STOP"),),
                       (replace(record.prefix[0], content="forged"),) + record.prefix[1:]):
            with self.subTest(prefix_length=len(prefix)), self.assertRaisesRegex(source.CoreInputError, "record_mismatch"):
                producer.build(rehashed(record, prefix))
        for candidate in (None, {}, record.unit):
            with self.assertRaisesRegex(source.CoreInputError, "typed_arm_record"):
                producer.build(candidate)

    def test_case_mutations_types_and_foreign_bindings_rejected(self):
        case = self.roster[7].cases[0]
        first = case.targets[0]
        candidates = (replace(case, descriptor=replace(case.descriptor, pair_index=True)),
                      replace(case, descriptor=self.roster[7].cases[1].descriptor),
                      replace(case, construction=self.roster[3].cases[0].construction),
                      replace(case, construction=replace(case.construction, skin=float(case.construction.skin))),
                      replace(case, targets=list(case.targets)), replace(case, trace=list(case.trace)),
                      replace(case, targets=(replace(first, ordinal=False),) + case.targets[1:]),
                      replace(case, targets=(replace(first, target_bytes=b"STOP"),) + case.targets[1:]),
                      replace(case, facts=replace(case.facts, selected_event=case.facts.failed_event)),
                      replace(case, task=replace(case.task, current=case.task.goal)),
                      replace(case, status="READY"), replace(case, memo_sha256="0" * 64),
                      replace(case, construction=replace(case.construction, scope="OTHER")))
        for candidate in candidates:
            with self.subTest(world=candidate.descriptor.world), self.assertRaises(source.CoreInputError):
                self.producer(case=candidate)
        tokens = self.tokens[7]
        missing, extra, duplicate = dict(tokens), dict(tokens), dict(tokens)
        first_role, second_role = tuple(tokens)[:2]
        del missing[first_role]
        extra["birth_train/p03/foreign/-/state/-/node"] = tokens[first_role]
        duplicate[first_role] = duplicate[second_role]
        for binding in (missing, extra, duplicate, self.tokens[3]):
            with self.assertRaises(source.CoreInputError):
                self.producer(role_tokens=binding)
        ports = [role for role in tokens if role.endswith("/port")]
        swapped = dict(tokens)
        swapped[ports[-1]], swapped[ports[-2]] = swapped[ports[-2]], swapped[ports[-1]]
        with self.assertRaisesRegex(source.CoreInputError, "owner_mismatch"):
            self.producer(role_tokens=swapped)

    def test_bounded_inputs_rejected_before_graph_assembly(self):
        case = self.roster[7].cases[0]
        oversized = replace(case, construction=replace(case.construction,
                            registry=dict.fromkeys(range(source.BOUNDS["services"] + 1), "MISS")))
        with patch.object(graph_inputs, "_Inputs", side_effect=AssertionError("bounds must run first")):
            for candidate in (oversized, replace(case, trace=case.trace * source.BOUNDS["trace_turns"]),
                              replace(case, task_text="A" * (source.BOUNDS["message_bytes"] + 1))):
                with self.assertRaises(source.CoreInputError):
                    self.producer(case=candidate)
            tokens = dict(self.tokens[7])
            tokens[next(iter(tokens))] = "A" * 100000
            with self.assertRaises(source.CoreInputError):
                self.producer(role_tokens=tokens)

    def test_local_snapshot_reuse_and_mutation_isolation(self):
        case = self.roster[7].cases[0]
        tokens = dict(self.tokens[7])
        edges, blocks, registry = dict(case.construction.world_edges), dict(case.construction.blocks), dict(case.construction.registry)
        external = replace(case, construction=replace(case.construction, world_edges=edges, blocks=blocks, registry=registry))
        record = self.records[7, "m0"][0].closed
        with patch.object(graph_inputs, "_Inputs", wraps=graph_inputs._Inputs) as setup, \
                patch.object(graph_inputs, "_world_graph", wraps=graph_inputs._world_graph) as world_build:
            producer = self.producer(case=external, role_tokens=tokens)
            first = producer.build(record)
            producer.build(self.records[7, "m0"][0].atom_local)
            producer.build(self.records[7, "m0"][1].closed)
            self.assertEqual(setup.call_count, 1)
            self.assertEqual(world_build.call_count, 1)
            tokens.clear()
            edges.clear()
            blocks.clear()
            registry.clear()
            second = producer.build(record)
            self.assertEqual(first, second)
            first.core["public_graph"]["edges"].clear()
            first.receipt["hashes"].clear()
            self.assertEqual(first, producer.build(record))
            with self.assertRaises(source.CoreInputError):
                self.producer(case=external, role_tokens=self.tokens[7])
        self.assertIsInstance(producer._case.construction.registry, MappingProxyType)

    def test_one_shot_api_checker_is_mandatory_and_no_external_work(self):
        case = self.roster[2].cases[0]
        record = self.records[2, "m0"][0].closed
        with patch.object(birth, "build_birth_pair", side_effect=AssertionError("no reconstruction")), \
                patch.object(wire, "allocate_opaque_namespace", side_effect=AssertionError("no allocation")), \
                patch("socket.create_connection", side_effect=AssertionError("no network")), \
                patch("subprocess.Popen", side_effect=AssertionError("no process")), \
                patch.object(Path, "mkdir", side_effect=AssertionError("no root")):
            result = source.build_birth_core_inputs(case=case, record=record, role_tokens=self.tokens[2])
        self.assertEqual(result.unit_id, record.unit.unit_id)
        self.assertEqual(result.arm, record.arm)
        self.assertEqual(result.core["actual_route_depth"], 1)
        self.assertEqual(result.receipt["status"], "PARTIAL_GRAPH_CHECK_ONLY")
        producer = self.producer(2)
        with patch.object(checker, "check_graph_core_json", side_effect=checker.GraphCheckError("rejected")):
            with self.assertRaisesRegex(source.CoreInputError, "rejected"):
                producer.build(record)


if __name__ == "__main__":
    unittest.main()
