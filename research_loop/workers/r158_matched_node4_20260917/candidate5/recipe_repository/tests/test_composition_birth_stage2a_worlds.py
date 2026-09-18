"""Synthetic in-memory tests for the partial v4 ordinary construction slice."""

import base64
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_worlds as source


DISPLAY_MASTER = b"synthetic-test-display-only"


def fixture(domain, world):
    tokens = {}
    prefixes = dict(node="N", query="Q", event="E", route="I", port="P", receipt="R")

    def add(state, goal, block, candidate, kind):
        role = "/".join((domain, world, state, goal, block, candidate, kind))
        digest = sha256(b"synthetic-in-memory-fixture/" + str(len(tokens)).encode("ascii")).digest()
        tokens[role] = "M2A" + prefixes[kind] + "_" + base64.b32encode(digest)[:12].decode("ascii")

    add("s", "-", "state", "-", "node")
    for prefix in ("g", "x"):
        for goal in range(24):
            add(f"{prefix}{goal:02d}", f"{goal:02d}", "state", "-", "node")
    if domain == "birth_train":
        family = "a" if int(world[1:]) % 4 < 2 else "b"
        hubs = tuple(f"{family}{index:02d}" for index in range(24 if family == "a" else 6))
        states = ("s",) + hubs
    else:
        hubs = tuple(f"{prefix}{index:02d}" for prefix in ("h", "w") for index in range(8))
        states = ("s",) + (hubs[:8] if domain == "dose_chain" else ())
    for hub in hubs:
        add(hub, hub[1:], "state", "-", "node")
    for state in states:
        for goal in range(24):
            add(state, f"{goal:02d}", "index", "-", "route")
            add(state, f"{goal:02d}", "useful", "-", "query")
            for candidate in range(4):
                for kind in ("event", "port", "receipt"):
                    add(state, f"{goal:02d}", "useful", str(candidate), kind)
                add(state, f"{goal:02d}", "recover", str(candidate), "query")
    return tokens


def node(tokens, domain, world, state):
    goal = "-" if state == "s" else state[1:]
    return tokens[f"{domain}/{world}/{state}/{goal}/state/-/node"]


class OrdinaryWorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = {}
        cls.worlds = {}
        with patch.object(wire, "allocate_opaque_namespace", side_effect=AssertionError("allocation forbidden")):
            for domain, worlds in (("birth_train", ("p00", "p02", "p04", "p06", "p08", "p10", "p12", "p14")),
                                   ("dose_chain", ("h00", "h01", "h02", "h03", "h08", "h09", "h10", "h11"))):
                for world in worlds:
                    tokens = fixture(domain, world)
                    cls.fixtures[domain, world] = tokens
                    cls.worlds[domain, world] = source.build_ordinary_world(
                        domain=domain, world=world, role_tokens=tokens,
                        display_master=DISPLAY_MASTER if domain == "birth_train" else None)

    def test_v4_hash_and_closed_gates(self):
        memo = Path(__file__).resolve().parents[1] / "research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v4.md"
        self.assertEqual(sha256(memo.read_bytes()).hexdigest(), source.MEMO_SHA256)
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        for flag in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"):
            self.assertIs(getattr(source, flag), False)

    def test_exact_wire_round_trip_all_constructed_blocks(self):
        for world in self.worlds.values():
            self.assertEqual(world.status, "PARTIAL_SOURCE_ONLY")
            self.assertEqual(world.memo_sha256, source.MEMO_SHA256)
            self.assertEqual(world.scope, "ORDINARY_WORLD_ONLY")
            service = wire.PassiveRegistry(world.registry, skin=world.skin)
            for request, block in world.blocks.items():
                self.assertEqual(service.read(request), block.raw)
                self.assertEqual(world.read(request), block.raw)
                self.assertEqual(wire.parse_service(block.raw, skin=world.skin), block)
                self.assertEqual(source.render_service(block.kind, block.rows, skin=world.skin), block.raw)
                self.assertFalse(block.raw.endswith("\n"))
                self.assertNotIn("\r", block.raw)

    def test_exact_field_order_both_skins(self):
        for world_name in ("p00", "p08"):
            world = self.worlds["birth_train", world_name]
            route = next(block.rows[0] for block in world.blocks.values() if block.kind == "ROUTES")
            event = next(block.rows[0] for block in world.blocks.values() if block.kind == "EVENTS")
            if world.skin == 0:
                expected_route = f"ROUTE {route.route} AT {route.node} FOR {route.goal} QUERY {route.query}"
                expected_event = f"EVENT {event.event} AT {event.node} FOR {event.goal} DID {event.port} GOT {event.got} RECOVER {event.recover} EVIDENCE {event.receipt}"
            else:
                expected_route = f"ROUTE {route.route} FOR {route.goal} QUERY {route.query} AT {route.node}"
                expected_event = f"EVENT {event.event} FOR {event.goal} AT {event.node} GOT {event.got} DID {event.port} RECOVER {event.recover} EVIDENCE {event.receipt}"
            self.assertEqual(next(block.raw.split("\n")[1] for block in world.blocks.values() if block.kind == "ROUTES"), expected_route)
            self.assertEqual(next(block.raw.split("\n")[1] for block in world.blocks.values() if block.kind == "EVENTS"), expected_event)

    def test_cardinality_linkage_and_candidate_owned_roles(self):
        for (domain, name), world in self.worlds.items():
            tokens = self.fixtures[domain, name]
            states = 9 if domain == "dose_chain" else (25 if int(name[1:]) % 4 == 0 else 7)
            self.assertEqual(len(world.registry), states * 25)
            self.assertEqual(len(world.world_edges), states * 96)
            for request, directory in world.blocks.items():
                if directory.kind != "ROUTES":
                    continue
                self.assertEqual(len({row.goal for row in directory.rows}), 24)
                for route in directory.rows:
                    self.assertEqual(request, "READ INDEX " + route.node)
                    relation = world.blocks["READ RELATION " + route.query]
                    self.assertEqual(sum(row.node == route.node and row.goal == route.goal for row in relation.rows), 1)
                    self.assertEqual(sum(row.node == route.node for row in relation.rows), 2)
                    self.assertEqual(sum(row.goal == route.goal for row in relation.rows), 2)
            for role, token in tokens.items():
                if role.endswith("/event"):
                    state, goal, candidate = role.split("/")[2], role.split("/")[3], role.split("/")[5]
                    query = tokens[f"{domain}/{name}/{state}/{goal}/useful/-/query"]
                    row = world.blocks["READ RELATION " + query].rows[int(candidate)]
                    self.assertEqual(row.event, token)
                    self.assertEqual(row.recover, tokens[f"{domain}/{name}/{state}/{goal}/recover/{candidate}/query"])
                    self.assertEqual(world.transition(row.node, row.port), row.got)
                    self.assertEqual(world.read("READ RELATION " + row.recover), "MISS")

    def test_birth_start_destinations_and_hub_ordinals(self):
        for name in ("p00", "p02", "p04", "p06", "p08", "p10", "p12", "p14"):
            world = self.worlds["birth_train", name]
            tokens = self.fixtures["birth_train", name]
            family = "a" if int(name[1:]) % 4 == 0 else "b"
            for state in ("s", f"{family}00", f"{family}{23 if family == 'a' else 5:02d}"):
                ordinal = 0 if state == "s" else int(state[1:]) + (1 if family == "a" else 25)
                self.assertEqual(source.state_ordinal("birth_train", name, state), ordinal)
                for goal in (0, 5, 23):
                    query = tokens[f"birth_train/{name}/{state}/{goal:02d}/useful/-/query"]
                    rows = world.blocks["READ RELATION " + query].rows
                    slot = (3 * goal + ordinal + world.skin) % 4
                    self.assertEqual(rows[slot].node, node(tokens, "birth_train", name, state))
                    destination = f"g{goal:02d}"
                    if state == "s" and (int(name[1:]) // 4) % 2:
                        destination = f"{family}{goal if family == 'a' else goal % 6:02d}"
                    self.assertEqual(rows[slot].got, node(tokens, "birth_train", name, destination))
                    for offset, wrong in ((2, goal), (3, (goal + 1) % 24)):
                        row = rows[(slot + offset) % 4]
                        self.assertEqual(row.node, node(tokens, "birth_train", name, f"x{wrong:02d}"))
                        self.assertEqual(row.got, node(tokens, "birth_train", name, f"x{(wrong + 3) % 24:02d}"))

    def test_birth_exact_display_preimage(self):
        for name in ("p00", "p06", "p12"):
            tokens = self.fixtures["birth_train", name]
            world = self.worlds["birth_train", name]
            family = "A" if int(name[1:]) % 4 == 0 else "B"
            for state in ("s", family.lower() + "00"):
                template = f"goal/{int(name[1:]) // 4}/{family}/{state}/index"
                expected = sorted(range(24), key=lambda goal: (sha256(b"\x00".join((DISPLAY_MASTER, b"display-order", template.encode(), goal.to_bytes(4, "big")))).digest(), goal))
                directory = world.blocks["READ INDEX " + node(tokens, "birth_train", name, state)]
                self.assertEqual([row.goal for row in directory.rows], [node(tokens, "birth_train", name, f"g{goal:02d}") for goal in expected])

    def test_v4_all_32_scored_positions_golden_hash(self):
        records = []
        for index in range(16):
            for member, (goal, row) in enumerate(source.chain_scored_positions(f"h{index:02d}")):
                records.append(dict(goal=f"g{goal:02d}", member=f"m{member}", row=row, world=f"h{index:02d}"))
        raw = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        self.assertEqual(len(raw), 1633)
        self.assertEqual(sha256(raw).hexdigest(), "87e9526c15056e0e715fecdc4e0e384c8439a03d7b5780ec61992b49376d8d13")

    def test_chain_scored_exception_unscored_generic_and_all_hubs(self):
        for index in (0, 1, 2, 3, 8, 9, 10, 11):
            name = f"h{index:02d}"
            tokens = self.fixtures["dose_chain", name]
            world = self.worlds["dose_chain", name]
            scored = {(5 * index) % 12: index % 4, 12 + (7 * index) % 12: (index + 1) % 4}
            rotation = (3 * index + 1) % 8
            for state in ("s",) + tuple(f"h{hub:02d}" for hub in range(8)):
                ordinal = 0 if state == "s" else 100 + int(state[1:])
                self.assertEqual(source.state_ordinal("dose_chain", name, state), ordinal)
                for goal in range(24):
                    query = tokens[f"dose_chain/{name}/{state}/{goal:02d}/useful/-/query"]
                    rows = world.blocks["READ RELATION " + query].rows
                    slot = scored.get(goal, (3 * goal + world.skin) % 4) if state == "s" else (3 * goal + ordinal + world.skin) % 4
                    self.assertEqual(rows[slot].goal, node(tokens, "dose_chain", name, f"g{goal:02d}"))
                    self.assertEqual(rows[slot].node, node(tokens, "dose_chain", name, state))
                    destination = f"h{(5 * goal + rotation) % 8:02d}" if state == "s" else f"g{goal:02d}"
                    self.assertEqual(rows[slot].got, node(tokens, "dose_chain", name, destination))

    def test_chain_directory_pins_and_ascending_remainder(self):
        for index in (0, 1, 2, 3, 8, 9, 10, 11):
            name = f"h{index:02d}"
            tokens = self.fixtures["dose_chain", name]
            world = self.worlds["dose_chain", name]
            goals = ((5 * index) % 12, 12 + (7 * index) % 12)
            for state in ("s",) + tuple(f"h{hub:02d}" for hub in range(8)):
                pins = {}
                for member, goal in enumerate(goals):
                    if state == "s" or state == f"h{(5 * goal + (3 * index + 1) % 8) % 8:02d}":
                        pins[(6 * (index % 4) + 3 * member + (0 if state == "s" else 12)) % 24] = goal
                rows = world.blocks["READ INDEX " + node(tokens, "dose_chain", name, state)].rows
                inverse = {node(tokens, "dose_chain", name, f"g{goal:02d}"): goal for goal in range(24)}
                order = [inverse[row.goal] for row in rows]
                for position, goal in pins.items():
                    self.assertEqual(order[position], goal)
                remainder = [goal for position, goal in enumerate(order) if position not in pins]
                self.assertEqual(remainder, sorted(set(range(24)) - set(pins.values())))

    def test_no_index_at_non_z_states_no_extra_edges(self):
        for (domain, name), world in self.worlds.items():
            tokens = self.fixtures[domain, name]
            for role, token in tokens.items():
                if role.endswith("/node") and role.split("/")[2].startswith(("g", "x", "w")):
                    self.assertEqual(world.read("READ INDEX " + token), "MISS")
            event = next(block.rows[0] for block in world.blocks.values() if block.kind == "EVENTS")
            other = node(tokens, domain, name, "g23")
            with self.assertRaisesRegex(ValueError, "invalid_step"):
                world.transition(other, event.port)

    def test_immutable_results_and_input_snapshot(self):
        tokens = dict(self.fixtures["birth_train", "p02"])
        result = source.build_ordinary_relation(domain="birth_train", world="p02", state_role="s", goal_index=0, role_tokens=tokens)
        original = dict(result.registry)
        tokens.clear()
        self.assertEqual(dict(result.registry), original)
        for mapping in (result.registry, result.blocks, result.world_edges, source.SCIENCE_GATES):
            with self.assertRaises(TypeError):
                mapping["bad"] = "bad"
        with self.assertRaises(FrozenInstanceError):
            result.skin = 1
        with self.assertRaises(FrozenInstanceError):
            next(iter(result.blocks.values())).rows[0].got = "bad"

    def test_fragments_and_intervention_ordinary_rotation(self):
        for transition_index, transition in enumerate(("seek", "prospect", "check", "continue")):
            for index in (0, 7):
                name = f"{transition}_k{index}"
                tokens = fixture("dose_intervention", name)
                designated = ((3 * index + transition_index) % 12, 12 + (5 * index + transition_index) % 12)
                goal = next(goal for goal in range(24) if goal not in designated)
                result = source.build_ordinary_relation(domain="dose_intervention", world=name, state_role="s", goal_index=goal, role_tokens=tokens)
                self.assertEqual(result.scope, "ORDINARY_RELATION_FRAGMENT")
                self.assertEqual(len(result.world_edges), 4)
                slot = (3 * goal + index // 4) % 4
                row = next(iter(result.blocks.values())).rows[slot]
                destination = f"h{(5 * goal + (5 * index + 3 * transition_index + 1) % 8) % 8:02d}"
                self.assertEqual(row.got, node(tokens, "dose_intervention", name, destination))
                for selected in designated:
                    with self.assertRaises(source.UnsupportedConstructionError):
                        source.build_ordinary_relation(domain="dose_intervention", world=name, state_role="s", goal_index=selected, role_tokens=tokens)
                with self.assertRaises(source.UnsupportedConstructionError):
                    source.build_ordinary_directory(domain="dose_intervention", world=name, state_role="s", role_tokens=tokens)
                with self.assertRaises(source.UnsupportedConstructionError):
                    source.build_ordinary_world(domain="dose_intervention", world=name, role_tokens=tokens)

    def test_unsupported_worlds_and_features_fail_explicitly(self):
        for domain, name in (("birth_train", "p01"), ("birth_train", "p09"), ("birth_train", "p16"), ("dose_chain", "h04"), ("dose_chain", "h12")):
            with self.assertRaises(source.UnsupportedConstructionError):
                source.build_ordinary_world(domain=domain, world=name, role_tokens={})
        for build in (source.build_recovery, source.build_pair, source.build_null):
            with self.assertRaises(source.UnsupportedConstructionError):
                build()

    def test_missing_malformed_wrong_type_and_duplicate_roles(self):
        tokens = self.fixtures["birth_train", "p02"]
        build = lambda mapping: source.build_ordinary_relation(domain="birth_train", world="p02", state_role="s", goal_index=0, role_tokens=mapping)
        for suffix in ("s/00/useful/-/query", "s/00/useful/0/event", "s/00/useful/0/port", "s/00/useful/0/receipt", "s/00/recover/0/query", "s/-/state/-/node", "g00/00/state/-/node"):
            broken = dict(tokens)
            del broken["birth_train/p02/" + suffix]
            with self.assertRaisesRegex(ValueError, "missing_role"):
                build(broken)
        key = "birth_train/p02/s/00/useful/0/event"
        for invalid in (None, b"M2AE_BBBBBBBBBBBB", "M2AE_AAAAAAAAAAAA", "M2AE_BBBBBBBBBBBB\n", "M2AP_BBBBBBBBBBBB"):
            with self.assertRaises(ValueError):
                build(dict(tokens, **{key: invalid}))
        for role in ("bad", "birth_train/p02/s/24/useful/0/event", "birth_train/p02/g00/00/useful/0/event", "birth_train/p00/s/00/useful/0/event"):
            with self.assertRaisesRegex(ValueError, "invalid_role_key"):
                build(dict(tokens, **{role: "M2AE_BBBBBBBBBBBB"}))
        with self.assertRaisesRegex(ValueError, "duplicate_opaque_token"):
            build(dict(tokens, **{key: tokens["birth_train/p02/s/00/useful/1/event"]}))
        with self.assertRaisesRegex(ValueError, "mapping_required"):
            build(list(tokens.items()))

    def test_invalid_world_state_goal_and_display_inputs(self):
        tokens = self.fixtures["birth_train", "p02"]
        for domain, name in ((None, "p02"), ("birth_train", "p32"), ("dose_chain", "h16"), ("generic_canary", "c00")):
            with self.assertRaises(ValueError):
                source.build_ordinary_world(domain=domain, world=name, role_tokens={})
        for state in ("g00", "x00", "a00", "b06", None, "s\n"):
            with self.assertRaises(ValueError):
                source.build_ordinary_relation(domain="birth_train", world="p02", state_role=state, goal_index=0, role_tokens=tokens)
        for goal in (-1, 24, True, "0", 0.0):
            with self.assertRaises(ValueError):
                source.build_ordinary_relation(domain="birth_train", world="p02", state_role="s", goal_index=goal, role_tokens=tokens)
        for master in (None, "synthetic", 1):
            with self.assertRaisesRegex(ValueError, "display_master"):
                source.build_ordinary_directory(domain="birth_train", world="p02", state_role="s", role_tokens=tokens, display_master=master)
        with self.assertRaises(source.UnsupportedConstructionError):
            source.state_ordinal("dose_chain", "h00", "w00")

    def test_full_world_requires_even_nonindexed_nodes(self):
        tokens = dict(self.fixtures["dose_chain", "h00"])
        del tokens["dose_chain/h00/w00/00/state/-/node"]
        with self.assertRaisesRegex(ValueError, "missing_role:dose_chain/h00/w00"):
            source.build_ordinary_world(domain="dose_chain", world="h00", role_tokens=tokens)

    def test_directory_fragment_and_missing_route(self):
        tokens = dict(self.fixtures["birth_train", "p02"])
        result = source.build_ordinary_directory(domain="birth_train", world="p02", state_role="s", role_tokens=tokens, display_master=DISPLAY_MASTER)
        self.assertEqual(result.scope, "ORDINARY_DIRECTORY_FRAGMENT")
        self.assertEqual(len(result.registry), 1)
        self.assertEqual(len(result.world_edges), 0)
        del tokens["birth_train/p02/s/00/index/-/route"]
        with self.assertRaisesRegex(ValueError, "missing_role"):
            source.build_ordinary_directory(domain="birth_train", world="p02", state_role="s", role_tokens=tokens, display_master=DISPLAY_MASTER)

    def test_renderer_malformed_rows_and_requests_fail_closed(self):
        world = self.worlds["birth_train", "p02"]
        block = next(block for block in world.blocks.values() if block.kind == "EVENTS")
        for skin in (-1, 2, True, "0"):
            with self.assertRaises(ValueError):
                source.render_service("EVENTS", block.rows, skin=skin)
        for rows in (block.rows[:3], list(block.rows) + [block.rows[0]], "bad", [None] * 4,
                     (replace(block.rows[0], got="M2AN_BBBBBBBBBBBB\n"),) + block.rows[1:]):
            with self.assertRaises(ValueError):
                source.render_service("EVENTS", rows, skin=0)
        for request in ("STOP", "READ INDEX bad", "READ RELATION M2AQ_BBBBBBBBBBBB\n"):
            with self.assertRaises(ValueError):
                world.read(request)
        self.assertEqual(source.render_service("MISS", (), skin=1), "MISS")
        with self.assertRaises(ValueError):
            source.render_service("MISS", block.rows, skin=0)


if __name__ == "__main__":
    unittest.main()
