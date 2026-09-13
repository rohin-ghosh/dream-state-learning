"""Synthetic CPU prerequisites only: complete held worlds are not science-ready."""

import base64
from collections import Counter
from dataclasses import FrozenInstanceError, fields, replace
from hashlib import sha256
from pathlib import Path
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_worlds as worlds


def fixtures(domain):
    prefixes = dict(node="N", query="Q", event="E", route="I", port="P", receipt="R")
    grouped = {}
    for kind, roles in wire.enumerate_symbolic_role_inventory(domain).roles_by_kind.items():
        for role in roles:
            digest = sha256(b"synthetic-held-prerequisite/" + role.encode("ascii")).digest()
            token = "M2A" + prefixes[kind] + "_" + base64.b32encode(digest)[:12].decode("ascii")
            grouped.setdefault(role.split("/")[1], {})[role] = token
    return grouped


def node(tokens, state):
    domain, world = next(iter(tokens)).split("/")[:2]
    goal = "-" if state == "s" else state[1:]
    return tokens[f"{domain}/{world}/{state}/{goal}/state/-/node"]


def query(tokens, state, goal):
    domain, world = next(iter(tokens)).split("/")[:2]
    return tokens[f"{domain}/{world}/{state}/{goal:02d}/useful/-/query"]


def matching(block, current, goal):
    relevant = [row for row in block.rows if row.node == current and row.goal == goal]
    if len(relevant) != 1:
        raise AssertionError("not exactly one relevant row")
    return relevant[0]


def thaw(value):
    if hasattr(value, "items"):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


def pointer_diff(left, right, prefix=""):
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            raise AssertionError("changed keys")
        result = set()
        for key in left:
            result |= pointer_diff(left[key], right[key], prefix + "/" + key.replace("~", "~0").replace("/", "~1"))
        return result
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            raise AssertionError("changed length")
        result = set()
        for index, (before, after) in enumerate(zip(left, right)):
            result |= pointer_diff(before, after, prefix + "/" + str(index))
        return result
    return {prefix} if type(left) is not type(right) or left != right else set()


def replay_prefix(member):
    prefix = member.public_view().prefix
    if prefix[0] != held.Message("system", wire.SYSTEM_MESSAGE):
        raise AssertionError("wrong system")
    task = wire.parse_task(prefix[1].content)
    current = task.current
    last_block = None
    stepped_event = None
    for offset in range(2, len(prefix), 2):
        actor, host = prefix[offset:offset + 2]
        if (actor.role, host.role) != ("assistant", "user"):
            raise AssertionError("bad role sequence")
        action = wire.parse_action(actor.content)
        if action.operation == "READ":
            raw = member.public_view().read(actor.content)
            if host.content != "SERVICE\n" + raw:
                raise AssertionError("inauthentic service bytes")
            last_block = wire.parse_service(raw, skin=member.construction.skin)
        elif action.operation == "STEP":
            stepped_event = matching(last_block, current, task.goal)
            if action.operand != stepped_event.port:
                raise AssertionError("wrong port")
            actual = member.execute_step(current, action.operand)
            if host.content != actual.world_message:
                raise AssertionError("inauthentic public outcome")
            current = wire.parse_world(host.content)
        else:
            raise AssertionError("unexpected prefix action")
    return task, current, last_block, stepped_event


class HeldConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intervention_tokens = fixtures("dose_intervention")
        cls.chain_tokens = fixtures("dose_chain")
        with patch.object(wire, "allocate_opaque_namespace", side_effect=AssertionError("no allocation")):
            cls.interventions = held.build_intervention_panel(role_tokens_by_world=cls.intervention_tokens)
            cls.chains = held.build_chain_panel(role_tokens_by_world=cls.chain_tokens)

    def test_source_pins_and_closed_gates(self):
        root = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
        for filename, expected in (
            ("2026-09-13_m_combine4_stage2a_binding_successor_v4.md", held.MEMO_SHA256),
            ("2026-09-13_stage2a_builder_source_clarifications_v1.md", held.CLARIFICATION_SHA256),
        ):
            self.assertEqual(sha256((root / filename).read_bytes()).hexdigest(), expected)
        self.assertEqual(held.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(held.SCIENCE_GATES.values()))
        for name in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"):
            self.assertIs(getattr(held, name), False)
        for result in self.interventions + self.chains:
            self.assertEqual(result.status, "PARTIAL_SOURCE_ONLY")
            self.assertEqual(result.memo_sha256, held.MEMO_SHA256)
            self.assertEqual(result.clarification_sha256, held.CLARIFICATION_SHA256)
            for member in result.members:
                self.assertEqual(member.status, "PARTIAL_SOURCE_ONLY")

    def test_exact_panel_order_counts_and_complete_registries(self):
        self.assertEqual([pair.world for pair in self.interventions],
                         [f"{transition}_k{index}" for transition in ("seek", "prospect", "check", "continue")
                          for index in range(8)])
        self.assertEqual([world.world for world in self.chains], [f"h{index:02d}" for index in range(16)])
        self.assertEqual(sum(len(pair.members) for pair in self.interventions), 64)
        self.assertEqual(sum(len(world.members) for world in self.chains), 32)
        for pair in self.interventions:
            for member in pair.members:
                self.assertEqual(len(member.registry), 25)
                self.assertEqual(len(member.world_edges), 96)
                self.assertEqual(Counter(block.kind for block in member.construction.blocks.values()),
                                 Counter(ROUTES=1, EVENTS=24))
                for block in member.construction.blocks.values():
                    if block.kind == "EVENTS":
                        for row in block.rows:
                            self.assertEqual(member.read("READ RELATION " + row.recover), "MISS")
        self.assertEqual(sum(len(world.world_edges) for world in self.chains), 13888)
        self.assertEqual(sum(sum(key.startswith("READ INDEX") for key in world.registry)
                             for world in self.chains), 144)
        self.assertEqual(sum(sum(key.startswith("READ RELATION") for key in world.registry)
                             for world in self.chains), 3456 + 16)

    def test_all_32_intervention_pins_bounded_and_exact_remainder(self):
        wrapped = 0
        for number, transition in enumerate(("seek", "prospect", "check", "continue")):
            for index in range(8):
                name = f"{transition}_k{index}"
                tokens = self.intervention_tokens[name]
                first = (3 * index + number) % 24
                second = (first + 12) % 24
                left, right = (3 * index + number) % 12, 12 + (5 * index + number) % 12
                wrapped += first >= 12
                self.assertEqual(held.intervention_pins(transition, index), ((first, left), (second, right)))
                self.assertTrue(0 <= first < 24 and 0 <= second < 24)
                self.assertNotEqual(first, second)
                construction = held.build_intervention_directory(world=name, role_tokens=tokens)
                block = construction.blocks["READ INDEX " + node(tokens, "s")]
                self.assertEqual(block.rows[first].goal, node(tokens, f"g{left:02d}"))
                self.assertEqual(block.rows[second].goal, node(tokens, f"g{right:02d}"))
                remaining = [row.goal for position, row in enumerate(block.rows) if position not in (first, second)]
                self.assertEqual(remaining, [node(tokens, f"g{goal:02d}") for goal in range(24)
                                             if goal not in (left, right)])
                self.assertEqual({row.query for row in block.rows}, {query(tokens, "s", goal) for goal in range(24)})
                self.assertEqual(len(construction.world_edges), 0)
        self.assertGreater(wrapped, 0)

    def test_allowlists_exact_independent_leaf_diff(self):
        for pair in self.interventions:
            transition, index = pair.world.split("_k")
            index = int(index)
            expected = {"/evaluator/answer", "/target/bytes", "/target/sha256"}
            if transition == "seek":
                expected |= {"/task/goal", "/target/operand"}
            elif transition == "prospect":
                expected.add("/target/operand")
                goal = (3 * index + 1) % 12
                expected |= {f"/service/relation_blocks/{goal}/rows/{slot}/for"
                             for slot in (index % 4, (index + 2) % 4)}
            elif transition == "check":
                expected |= {"/intervention/outcome_destination", "/target/command", "/transcript/world/current"}
            else:
                expected |= {"/task/goal", "/target/command", "/target/operand"}
            before, after = [thaw(member.semantic_object) for member in pair.members]
            self.assertEqual(set(before), {"evaluator", "intervention", "service", "task", "target", "transcript", "world"})
            self.assertEqual(pointer_diff(before, after), expected)
            self.assertEqual(pair.allowed_differences, expected)
            self.assertEqual(held.leaf_differences(before, after), expected)
            self.assertEqual(before["world"], after["world"])
            after["world"]["edges"][0]["destination"] = "forbidden-hidden-world-change"
            self.assertNotEqual(held.leaf_differences(before, after), pair.allowed_differences)

    def test_diff_structure_escaping_and_required_not_subset(self):
        self.assertEqual(held.leaf_differences({"a/b~c": [1]}, {"a/b~c": [2]}), {"/a~1b~0c/0"})
        for before, after in (({}, {"added": 1}), ([1], [1, 2]), ({}, []), ({"rows": []}, {"rows": {}})):
            with self.assertRaises(ValueError):
                held.leaf_differences(before, after)
        pair = self.interventions[0]
        before, after = [thaw(member.semantic_object) for member in pair.members]
        after["target"]["sha256"] = before["target"]["sha256"]
        self.assertLess(held.leaf_differences(before, after), pair.allowed_differences)

    def test_all_targets_from_public_causal_prefix(self):
        for pair in self.interventions:
            for member in pair.members:
                task, current, block, event = replay_prefix(member)
                if member.transition_name == "seek":
                    expected = "READ RELATION " + matching(block, current, task.goal).query
                elif member.transition_name == "prospect":
                    expected = "STEP " + matching(block, current, task.goal).port
                elif member.transition_name == "check":
                    expected = "THINK " + ("KEEP " if current == event.got else "REVISE ") + event.event
                else:
                    expected = "STOP" if current == task.goal else "READ INDEX " + current
                    self.assertEqual(len(member.expected_causal_prefix), 2)
                target = member.expected_target
                self.assertEqual(target.bytes, expected)
                self.assertEqual(target.sha256, sha256(expected.encode("ascii")).hexdigest())
                action = wire.parse_action(expected)
                self.assertEqual(target.operand, action.operand)
                self.assertEqual(target.command, action.operation + (" " + action.verb if action.verb else ""))
                self.assertEqual(member.semantic_object["evaluator"]["answer"], expected)

    def test_seek_complete_shared_service_and_distinct_query_targets(self):
        for pair in self.interventions[:8]:
            before, after = pair.members
            self.assertIs(before.construction, after.construction)
            self.assertNotEqual(before.expected_target.operand, after.expected_target.operand)
            self.assertEqual(before.expected_causal_prefix[2:], after.expected_causal_prefix[2:])
            self.assertEqual(before.task.current, after.task.current)

    def test_prospect_only_two_for_fields_change_with_fixed_ids_destinations(self):
        for pair in self.interventions[8:16]:
            before, after = pair.members
            index = before.pair_index
            changed = []
            for request, block in before.construction.blocks.items():
                other = after.construction.blocks[request]
                for position, (left, right) in enumerate(zip(block.rows, other.rows)):
                    if left != right:
                        changed.append(position)
                        self.assertEqual(replace(left, goal=right.goal), right)
                        self.assertEqual(left.node, before.task.current)
            self.assertEqual(set(changed), {index % 4, (index + 2) % 4})
            self.assertEqual(len(changed), 2)
            self.assertEqual(before.world_edges, after.world_edges)
            self.assertNotEqual(before.expected_target.operand, after.expected_target.operand)
            self.assertNotEqual(before.transition(before.task.current, before.expected_target.operand), before.task.goal)
            self.assertNotEqual(after.transition(after.task.current, after.expected_target.operand), after.task.goal)
            self.assertEqual(before.task, after.task)

    def test_check_typed_effective_transition_receipt_without_base_mutation(self):
        for pair in self.interventions[16:24]:
            before, after = pair.members
            self.assertIs(before.construction, after.construction)
            self.assertEqual(before.selected_event, after.selected_event)
            self.assertEqual(before.task, after.task)
            self.assertEqual(before.expected_causal_prefix[:-1], after.expected_causal_prefix[:-1])
            snapshot = dict(before.world_edges)
            for member in pair.members:
                event = member.selected_event
                result = member.execute_step(member.task.current, event.port)
                self.assertEqual(member.transition(event.node, event.port), event.got)
                self.assertEqual(result.receipt.base_destination, event.got)
                self.assertEqual(result.receipt.outcome_destination, member.intervention.outcome_destination)
                self.assertEqual((result.receipt.current, result.receipt.port), (event.node, event.port))
                self.assertEqual(wire.parse_world(result.world_message), result.destination)
                self.assertEqual(result.destination, member.effective_transition(event.node, event.port))
                self.assertEqual(member.expected_target.operand, event.event)
                for (current, port), destination in member.world_edges.items():
                    if (current, port) != (event.node, event.port):
                        scalar = member.execute_step(current, port)
                        self.assertEqual(scalar.destination, destination)
                        self.assertIsNone(scalar.receipt)
                with self.assertRaisesRegex(ValueError, "unbound_check_outcome"):
                    replace(member, intervention=held.OutcomeIntervention("IDENTITY", None))
            self.assertEqual(before.world_edges, snapshot)
            self.assertNotEqual(after.effective_transition(after.task.current, after.selected_event.port), after.selected_event.got)

    def test_scalar_legality_and_no_outcome_override_outside_check(self):
        for pair in self.interventions:
            for member in pair.members:
                tokens = self.intervention_tokens[pair.world]
                for (current, port), destination in member.world_edges.items():
                    self.assertEqual(member.transition(current, port), destination)
                    with self.assertRaisesRegex(ValueError, "invalid_step"):
                        member.effective_transition(node(tokens, "g00"), port)
                if member.transition_name != "check":
                    with self.assertRaisesRegex(ValueError, "outcome_override_outside_check"):
                        replace(member, intervention=held.OutcomeIntervention("OUTCOME_DESTINATION", member.task.current))
        for arguments in (("IDENTITY", "junk"), ("OTHER", None), ("OUTCOME_DESTINATION", None)):
            with self.assertRaises(ValueError):
                held.OutcomeIntervention(*arguments)
        with self.assertRaisesRegex(ValueError, "typed_intervention_required"):
            replace(self.interventions[0].members[0], intervention={"kind": "IDENTITY"})

    def test_intervention_designated_and_all_filler_rows(self):
        for number, pair in enumerate(self.interventions):
            member = pair.members[0]
            transition, index = number // 8, number % 8
            tokens = self.intervention_tokens[pair.world]
            left, right = (3 * index + transition) % 12, 12 + (5 * index + transition) % 12
            rotation = (5 * index + 3 * transition + 1) % 8
            for goal in range(24):
                block = member.construction.blocks["READ RELATION " + query(tokens, "s", goal)]
                slot = index % 4 if goal in (left, right) else (3 * goal + index // 4) % 4
                next_goal = (goal + 1) % 24
                pattern = [("s", goal), ("s", next_goal), (f"x{goal:02d}", goal),
                           (f"x{next_goal:02d}", (goal + 2) % 24)]
                if transition == 1 and goal == left:
                    pattern = [("s", goal), (f"x{goal:02d}", goal), ("s", right),
                               (f"x{next_goal:02d}", (goal + 2) % 24)]
                for offset, (at, for_goal) in enumerate(pattern):
                    row = block.rows[(slot + offset) % 4]
                    destination = (f"h{(5 * for_goal + rotation) % 8:02d}" if at == "s"
                                   else f"x{(int(at[1:]) + 3) % 24:02d}")
                    self.assertEqual((row.node, row.goal, row.got),
                                     (node(tokens, at), node(tokens, f"g{for_goal:02d}"), node(tokens, destination)))

    def test_public_projection_excludes_evaluator_and_has_no_forced_chain_actions(self):
        public_fields = {field.name for field in fields(held.PublicView)}
        self.assertEqual(public_fields, {"task", "prefix", "registry", "status"})
        for pair in self.interventions:
            for member in pair.members:
                public = member.public_view()
                self.assertEqual(public.task, member.task)
                self.assertFalse(any(hasattr(public, name) for name in (
                    "expected_target", "semantic_object", "world_edges", "intervention", "execute_step", "receipt")))
                self.assertTrue(all(type(raw) is str for raw in public.registry.values()))
                self.assertNotIn("OUTCOME_DESTINATION", "\n".join(message.content for message in public.prefix))
        for world in self.chains:
            for member in world.members:
                public = world.public_view(member.member)
                self.assertEqual(len(public.prefix), 2)
                self.assertEqual([message.role for message in public.prefix], ["system", "user"])
                self.assertEqual(wire.parse_task(public.prefix[1].content), member.task)
                self.assertFalse(hasattr(public, "expected_trace"))
                self.assertFalse(hasattr(public, "sufficient_reads"))
                self.assertIs(public.registry, world.registry)
                with self.assertRaises(ValueError):
                    public.read("STOP")

    def test_expected_chains_equal_stable_ordinary_worlds(self):
        for world in self.chains:
            if not world.mismatch:
                ordinary = worlds.build_ordinary_world(domain="dose_chain", world=world.world,
                                                        role_tokens=self.chain_tokens[world.world])
                self.assertEqual(world.registry, ordinary.registry)
                self.assertEqual(world.world_edges, ordinary.world_edges)

    def test_chain_all_v4_scored_slots_and_start_hub_directory_positions(self):
        for index, world in enumerate(self.chains):
            tokens = self.chain_tokens[world.world]
            rotation = (3 * index + 1) % 8
            goals = ((5 * index) % 12, 12 + (7 * index) % 12)
            for state in ("s",) + tuple(f"h{hub:02d}" for hub in range(8)):
                block = world.construction.blocks["READ INDEX " + node(tokens, state)]
                pinned = {}
                for member, goal in enumerate(goals):
                    if state == "s" or state == f"h{(5 * goal + rotation) % 8:02d}":
                        position = (6 * (index % 4) + 3 * member + (12 if state != "s" else 0)) % 24
                        pinned[position] = goal
                        self.assertEqual(block.rows[position].goal, node(tokens, f"g{goal:02d}"))
                self.assertEqual([row.goal for position, row in enumerate(block.rows) if position not in pinned],
                                 [node(tokens, f"g{goal:02d}") for goal in range(24) if goal not in pinned.values()])
                for goal in range(24):
                    relation = world.construction.blocks["READ RELATION " + query(tokens, state, goal)]
                    ordinal = 0 if state == "s" else 100 + int(state[1:])
                    slot = ((index + goals.index(goal)) % 4 if state == "s" and goal in goals
                            else (3 * goal + ordinal + index // 8) % 4)
                    selected = matching(relation, node(tokens, state), node(tokens, f"g{goal:02d}"))
                    self.assertEqual(relation.rows[slot], selected)
                    next_goal = (goal + 1) % 24
                    pattern = ((state, goal), (state, next_goal), (f"x{goal:02d}", goal),
                               (f"x{next_goal:02d}", (goal + 2) % 24))
                    for offset, (at, for_goal) in enumerate(pattern):
                        row = relation.rows[(slot + offset) % 4]
                        destination = (f"x{(int(at[1:]) + 3) % 24:02d}" if at.startswith("x") else
                                       f"h{(5 * for_goal + rotation) % 8:02d}" if state == "s" else f"g{for_goal:02d}")
                        self.assertEqual((row.node, row.goal, row.got),
                                         (node(tokens, at), node(tokens, f"g{for_goal:02d}"), node(tokens, destination)))

    def test_chain_only_scored_first_hops_mismatch_and_exact_recovery_owners(self):
        unregistered_total = 0
        for index, world in enumerate(self.chains):
            tokens = self.chain_tokens[world.world]
            rotation = (3 * index + 1) % 8
            scored = ((5 * index) % 12, 12 + (7 * index) % 12)
            contradictions = []
            registered = []
            for request, block in world.construction.blocks.items():
                if block.kind != "EVENTS":
                    continue
                for row in block.rows:
                    actual = world.transition(row.node, row.port)
                    if actual != row.got:
                        contradictions.append(row)
                    recovery = world.read("READ RELATION " + row.recover)
                    if recovery == "MISS":
                        unregistered_total += 1
                    else:
                        registered.append(row)
                        self.assertNotEqual(actual, row.got)
                        corrective = wire.parse_service(recovery, skin=world.skin)
                        selected = matching(corrective, actual, row.goal)
                        goal = scored[len(registered) - 1]
                        self.assertEqual(actual, node(tokens, f"w{(7 * goal + rotation) % 8:02d}"))
                        slot = (3 * goal + 108 + (7 * goal + rotation) % 8 + world.skin) % 4
                        self.assertEqual(corrective.rows[slot], selected)
                        self.assertEqual(world.transition(actual, selected.port), row.goal)
                        self.assertEqual(world.read("READ INDEX " + actual), "MISS")
                        for corrective_row in corrective.rows:
                            self.assertEqual(world.read("READ RELATION " + corrective_row.recover), "MISS")
                            self.assertEqual(world.transition(corrective_row.node, corrective_row.port), corrective_row.got)
            self.assertEqual(len(contradictions), 2 if world.mismatch else 0)
            self.assertEqual(registered, contradictions)
            for member, goal in enumerate(scored):
                first = world.construction.blocks["READ RELATION " + query(tokens, "s", goal)].rows[(index + member) % 4]
                self.assertEqual(first in contradictions, world.mismatch)
            for state in tuple(f"w{hub:02d}" for hub in range(8)) + ("g00", "x00"):
                self.assertEqual(world.read("READ INDEX " + node(tokens, state)), "MISS")
        self.assertEqual(unregistered_total, 13872)

    def test_chain_witness_two_legal_steps_strata_and_exact_terminal_stop(self):
        strata = Counter()
        for world in self.chains:
            for member in world.members:
                strata[world.mismatch, world.skin] += 1
                current = member.task.current
                last_block = None
                first_event = None
                steps = 0
                reads = set()
                for turn in member.expected_trace:
                    self.assertEqual(turn.current_before, current)
                    action = wire.parse_action(turn.action)
                    if action.operation == "READ":
                        reads.add(turn.action)
                        raw = world.read(turn.action)
                        self.assertEqual(turn.response, "SERVICE\n" + raw)
                        last_block = wire.parse_service(raw, skin=world.skin)
                    elif action.operation == "STEP":
                        selected = matching(last_block, current, member.task.goal)
                        self.assertEqual(selected.port, action.operand)
                        if steps == 0:
                            first_event = selected
                        current = world.transition(current, action.operand)
                        self.assertEqual(wire.parse_world(turn.response), current)
                        steps += 1
                        self.assertEqual(current == member.task.goal, steps == 2)
                    elif action.operation == "THINK":
                        self.assertEqual(steps, 1)
                        self.assertEqual(action.operand, first_event.event)
                        self.assertEqual(action.verb, "KEEP" if current == first_event.got else "REVISE")
                        self.assertEqual(turn.response, "ACK")
                    else:
                        self.assertEqual(steps, 2)
                        self.assertEqual(current, member.task.goal)
                        self.assertIsNone(turn.response)
                    self.assertEqual(turn.current_after, current)
                self.assertEqual(steps, 2)
                self.assertEqual(member.expected_trace[-1].action, "STOP")
                self.assertTrue(member.expected_trace[-2].action.startswith("STEP "))
                self.assertEqual(Counter(wire.parse_action(turn.action).operation for turn in member.expected_trace),
                                 Counter(READ=3 if world.mismatch else 4, STEP=2, THINK=1, STOP=1))
                self.assertEqual(reads, member.sufficient_reads)
        self.assertEqual(strata, Counter({(False, 0): 8, (True, 0): 8, (False, 1): 8, (True, 1): 8}))

    def test_chain_witnesses_replay_through_stable_scalar_session(self):
        for world in self.chains:
            service = wire.PassiveRegistry(world.registry, skin=world.skin)
            for member in world.members:
                task_text = world.public_view(member.member).prefix[1].content
                session = wire.Session(task_text, world.world_edges, service)
                self.assertEqual(session.attempts, ())
                for turn in member.expected_trace:
                    attempt = session.turn(
                        turn.action, generation_request={"max_new_tokens": 256},
                        declared_tokens=1, actual_tokens=1, context_tokens=0,
                        truncated=False, finish_reason="stop")
                    self.assertTrue(attempt.accepted)
                    self.assertEqual(attempt.response_bytes, (turn.response or "").encode("ascii"))
                    self.assertEqual(attempt.post_state.current, turn.current_after)
                self.assertEqual(session.state.terminal_reason, "goal_arrival_stop")
                self.assertTrue(session.state.goal_arrival_stop)

    def test_directory_conflicts_fail_without_remainder_repair(self):
        for pins in (((0, 1), (0, 2)), ((0, 1), (2, 1)), ((24, 1),), ((0, 24),)):
            with self.assertRaises(ValueError):
                held._directory_order(pins)

    def test_nested_immutability_and_input_isolation(self):
        pair = self.interventions[0]
        member = pair.members[0]
        with self.assertRaises(FrozenInstanceError):
            pair.status = "READY"
        with self.assertRaises(TypeError):
            member.semantic_object["task"]["goal"] = "changed"
        with self.assertRaises(TypeError):
            member.registry["READ INDEX " + member.task.start] = "MISS"
        with self.assertRaises(TypeError):
            member.world_edges[member.task.start, member.selected_event.port] = "changed"
        with self.assertRaises(FrozenInstanceError):
            member.selected_event.got = "changed"
        tokens = dict(self.intervention_tokens[pair.world])
        built = held.build_intervention_pair(world=pair.world, role_tokens=tokens)
        tokens.clear()
        self.assertEqual(built, pair)

    def test_fail_closed_explicit_per_world_tokens_and_no_master_argument(self):
        name = "seek_k0"
        original = self.intervention_tokens[name]
        invalid = [None, {}, self.chain_tokens["h00"], {**original, "other/domain/s/-/state/-/node": node(original, "s")}]
        missing = dict(original)
        missing.pop(next(iter(missing)))
        invalid.append(missing)
        node_roles = [role for role in original if role.endswith("/node")]
        duplicate = dict(original)
        duplicate[node_roles[1]] = duplicate[node_roles[0]]
        invalid.append(duplicate)
        for bad_token in ("M2AN_AAAAAAAAAAAA", "not-a-token", 3, next(value for key, value in original.items() if key.endswith("/port"))):
            changed = dict(original)
            changed[node_roles[0]] = bad_token
            invalid.append(changed)
        for tokens in invalid:
            with self.assertRaises(ValueError):
                held.build_intervention_pair(world=name, role_tokens=tokens)
        with self.assertRaises(TypeError):
            held.build_intervention_pair(world=name, role_tokens=original, master=b"forbidden")
        for name in ("seek_k8", "seek_k00", "SEEK_k0", "h16", None):
            with self.assertRaises(ValueError):
                held.build_intervention_pair(world=name, role_tokens=original)
        for index in (True, -1, 8, "0"):
            with self.assertRaises(ValueError):
                held.intervention_pins("seek", index)

    def test_panel_requires_exact_coverage_and_cross_world_disjoint_tokens(self):
        with self.assertRaises(ValueError):
            held.build_intervention_panel(role_tokens_by_world={})
        with self.assertRaises(ValueError):
            held.build_chain_panel(role_tokens_by_world={"h00": self.chain_tokens["h00"]})
        copied = {world: dict(tokens) for world, tokens in self.intervention_tokens.items()}
        first_node = "dose_intervention/seek_k0/s/-/state/-/node"
        other_node = "dose_intervention/seek_k1/s/-/state/-/node"
        copied["seek_k1"][other_node] = copied["seek_k0"][first_node]
        with self.assertRaisesRegex(ValueError, "panel_token_collision"):
            held.build_intervention_panel(role_tokens_by_world=copied)


if __name__ == "__main__":
    unittest.main()
