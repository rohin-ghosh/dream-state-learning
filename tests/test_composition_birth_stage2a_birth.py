"""Independent synthetic fixtures and CPU oracles for partial birth support."""

import base64
from collections import Counter
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_worlds as worlds
from organism_v6 import composition_birth_stage2a_birth as source


DISPLAY_MASTER = b"synthetic-birth-display-fixture-only"
MISMATCH_PAIRS = (1, 3, 5, 7, 25, 27, 29, 31)
MISS_PAIRS = (9, 13, 19, 23)


def synthetic_bindings(pair):
    world = f"p{pair:02d}"
    result = {}
    prefixes = dict(node="N", query="Q", event="E", route="I", port="P", receipt="R")

    def add(state, goal, block, candidate, kind):
        role = f"birth_train/{world}/{state}/{goal}/{block}/{candidate}/{kind}"
        digest = sha256(b"synthetic-birth/" + world.encode("ascii") + b"/" + str(len(result)).encode("ascii")).digest()
        result[role] = "M2A" + prefixes[kind] + "_" + base64.b32encode(digest)[:12].decode("ascii")

    add("s", "-", "state", "-", "node")
    for prefix in ("g", "x"):
        for goal in range(24):
            add(f"{prefix}{goal:02d}", f"{goal:02d}", "state", "-", "node")
    family = "a" if pair % 4 < 2 else "b"
    states = ("s",) + tuple(f"{family}{hub:02d}" for hub in range(24 if family == "a" else 6))
    for state in states[1:]:
        add(state, state[1:], "state", "-", "node")
    for state in states:
        for goal in range(24):
            add(state, f"{goal:02d}", "index", "-", "route")
            add(state, f"{goal:02d}", "useful", "-", "query")
            for candidate in range(4):
                for kind in ("event", "port", "receipt"):
                    add(state, f"{goal:02d}", "useful", str(candidate), kind)
                add(state, f"{goal:02d}", "recover", str(candidate), "query")
    bucket = pair // 4
    for member in range(2):
        side = member if pair < 16 else bucket % 2
        goal = (5 * bucket) % 12 if side == 0 else 12 + (7 * bucket) % 12
        if pair in MISMATCH_PAIRS:
            for prefix in ("pred", "surp"):
                add(f"{prefix}_m{member}", f"{goal:02d}", "mismatch", "-", "node")
            for candidate in range(4):
                for kind in ("event", "port", "receipt"):
                    add(f"surp_m{member}", f"{goal:02d}", f"recovery_m{member}", str(candidate), kind)
                add(f"surp_m{member}", f"{goal:02d}", f"recover2_m{member}", str(candidate), "query")
        elif pair in MISS_PAIRS:
            add("s", f"{goal:02d}", f"miss_m{member}", "-", "query")
    return result


def binding(tokens, world, suffix):
    return tokens["birth_train/" + world + "/" + suffix]


def node(tokens, world, state):
    return binding(tokens, world, f"{state}/{'-' if state == 's' else state[1:]}/state/-/node")


def changed_construction(case, *, request=None, rows=None, edges=None):
    blocks = dict(case.construction.blocks)
    registry = dict(case.construction.registry)
    if request is not None:
        raw = worlds.render_service(blocks[request].kind, rows, skin=case.descriptor.skin)
        blocks[request] = wire.parse_service(raw, skin=case.descriptor.skin)
        registry[request] = raw
    return replace(case.construction, blocks=MappingProxyType(blocks), registry=MappingProxyType(registry),
                   world_edges=MappingProxyType(dict(case.construction.world_edges if edges is None else edges)))


class BirthConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokens = {pair: synthetic_bindings(pair) for pair in range(32)}
        with patch.object(wire, "allocate_opaque_namespace", side_effect=AssertionError("allocation forbidden")):
            cls.pairs = {pair: source.build_birth_pair(world=f"p{pair:02d}", role_tokens=cls.tokens[pair], display_master=DISPLAY_MASTER)
                         for pair in range(32)}

    def test_exact_binding_and_closed_science_flags(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(sha256((root / "research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v4.md").read_bytes()).hexdigest(), source.MEMO_SHA256)
        self.assertEqual(sha256((root / source.CLARIFICATION_PATH).read_bytes()).hexdigest(), source.CLARIFICATION_SHA256)
        self.assertEqual(source.CLARIFICATION_SHA256, "5484567fdad924247c5371a7430a071c925c563b5375336e8bef86dc6a4a99f9")
        self.assertEqual(source.FAMILY_BITS, {"A": 0, "B": 1})
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        for flag in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"):
            self.assertIs(getattr(source, flag), False)

    def test_all_64_descriptors_factorial_and_recovery_bijection(self):
        descriptors = source.enumerate_birth_cases()
        self.assertEqual(len(descriptors), 64)
        self.assertEqual(len({descriptor.case_id for descriptor in descriptors}), 64)
        self.assertEqual(Counter(descriptor.family for descriptor in descriptors), {"A": 32, "B": 32})
        for field in ("flow", "terminal_class", "goal_side", "skin", "pair_type"):
            self.assertEqual(sorted(Counter(getattr(descriptor, field) for descriptor in descriptors).values()), [32, 32])
        self.assertEqual(Counter(descriptor.recovery_subtype for descriptor in descriptors),
                         {"NONE": 32, "STRICT_MISS": 8, "IRRELEVANT_RETURN": 8, "STEP_OUTCOME_MISMATCH": 16})
        for descriptor in descriptors:
            pair, member = int(descriptor.world[1:]), int(descriptor.member[1:])
            bucket = pair // 4
            side = member if pair < 16 else bucket % 2
            self.assertEqual(descriptor.goal_index, (5 * bucket) % 12 if side == 0 else 12 + (7 * bucket) % 12)
            self.assertEqual(descriptor.skin, (bucket // 2) % 2)
            self.assertEqual(descriptor.terminal_class, "REACHED" if bucket % 2 == 0 else "UNRESOLVED")
            self.assertEqual(descriptor.family_bit, 0 if pair % 4 < 2 else 1)
            self.assertEqual(descriptor.relation_slot, (3 * bucket + (0 if pair % 4 < 2 else 1)) % 4 if pair >= 16 else None)
            if pair % 2:
                matched = source.describe_birth_case(f"p{pair - 1:02d}", descriptor.member)
                self.assertEqual(descriptor.recovery_match_id, matched.case_id)
                for field in ("family", "terminal_class", "goal_side", "goal_index", "skin", "pair_type"):
                    self.assertEqual(getattr(descriptor, field), getattr(matched, field))
            else:
                self.assertIsNone(descriptor.recovery_match_id)

    def test_independent_role_expansion_exact_all_v3_hashes(self):
        by_kind = {kind: [] for kind in wire.SYMBOLIC_KINDS}
        for pair, tokens in self.tokens.items():
            self.assertEqual(tuple(sorted(tokens)), source.required_birth_roles(f"p{pair:02d}"))
            for role in tokens:
                by_kind[role.rsplit("/", 1)[1]].append(role)
        for kind, roles in by_kind.items():
            expected_count, expected_hash = wire.SYMBOLIC_COMMITMENTS["birth_train"][kind]
            self.assertEqual(len(roles), expected_count)
            self.assertEqual(sha256("\n".join(sorted(roles)).encode("ascii")).hexdigest(), expected_hash)

    def test_each_supported_case_independent_four_target_oracle(self):
        total = Counter()
        for pair, built in self.pairs.items():
            tokens, world = self.tokens[pair], built.world
            for member, case in enumerate(built.cases):
                bucket = pair // 4
                side = member if pair < 16 else bucket % 2
                goal = (5 * bucket) % 12 if side == 0 else 12 + (7 * bucket) % 12
                skin = (bucket // 2) % 2
                start = node(tokens, world, "s")
                goal_token = node(tokens, world, f"g{goal:02d}")
                query = binding(tokens, world, f"s/{goal:02d}/useful/-/query")
                base_slot = ((3 * goal + skin) % 4 if pair < 16 else
                             (3 * bucket + (0 if pair % 4 < 2 else 1)) % 4)
                slot = base_slot if pair < 16 or pair in MISMATCH_PAIRS else (base_slot + 2 * member) % 4
                ordinary_port = binding(tokens, world, f"s/{goal:02d}/useful/{slot}/port")
                ordinary_event = binding(tokens, world, f"s/{goal:02d}/useful/{slot}/event")
                reached = bucket % 2 == 0
                family = "a" if pair % 4 < 2 else "b"
                destination_goal = (goal + 1) % 24 if pair >= 16 and member == 1 else goal
                final_state = f"g{goal:02d}" if reached else f"{family}{destination_goal if family == 'a' else destination_goal % 6:02d}"
                final_node = node(tokens, world, final_state)
                last = "STOP" if reached else "READ INDEX " + final_node
                if pair % 2 == 0:
                    expected = ["READ RELATION " + query, "STEP " + ordinary_port, "THINK KEEP " + ordinary_event, last]
                    phases = ["SEEK", "PROSPECT", "STEP_CHECK", "CONTINUE"]
                    indices = [1, 2, 3, 4]
                elif pair in MISMATCH_PAIRS:
                    owner = member if pair < 16 else 0
                    recovery_slot = (3 * goal + 81 + member + skin) % 4 if pair < 16 else (base_slot + 2 * member) % 4
                    recovery_query = binding(tokens, world, f"s/{goal:02d}/recover/{base_slot}/query")
                    corrective_port = binding(tokens, world, f"surp_m{owner}/{goal:02d}/recovery_m{owner}/{recovery_slot}/port")
                    expected = ["THINK REVISE " + ordinary_event, "READ RELATION " + recovery_query, "STEP " + corrective_port, last]
                    phases = ["STEP_CHECK", "SEEK", "PROSPECT", "CONTINUE"]
                    indices = [3, 4, 5, 6]
                    self.assertEqual(case.facts.failed_prediction, binding(tokens, world, f"pred_m{owner}/{goal:02d}/mismatch/-/node"))
                    self.assertEqual(case.facts.failed_outcome, binding(tokens, world, f"surp_m{owner}/{goal:02d}/mismatch/-/node"))
                else:
                    bad = (binding(tokens, world, f"s/{goal:02d}/miss_m{member}/-/query") if pair in MISS_PAIRS else
                           binding(tokens, world, f"s/{(goal + 1) % 24:02d}/useful/-/query"))
                    expected = ["THINK REVISE " + bad, "READ RELATION " + query, "STEP " + ordinary_port, last]
                    phases = ["READ_CHECK", "SEEK", "PROSPECT", "CONTINUE"]
                    indices = [2, 3, 4, 5]
                    self.assertEqual(case.facts.failed_query, bad)
                self.assertEqual([target.target_bytes for target in case.targets], [target.encode("ascii") for target in expected])
                self.assertEqual([target.phase for target in case.targets], phases)
                self.assertEqual([target.trace_index for target in case.targets], indices)
                self.assertEqual(case.task, wire.TaskState(start, goal_token, start))
                self.assertEqual(case.facts.final_current, final_node)
                self.assertEqual(case.facts.selected_prediction, final_node)
                self.assertEqual(case.facts.selected_outcome, final_node)
                self.assertTrue(source.validate_birth_case(case, role_tokens=tokens))
                for ordinal, target in enumerate(case.targets):
                    self.assertEqual(target.ordinal, ordinal)
                    self.assertEqual(target.target_sha256, sha256(target.target_bytes).hexdigest())
                    self.assertEqual(case.trace[target.trace_index].action.encode("ascii"), target.target_bytes)
                    total[target.command] += 1
        self.assertEqual(total, {"READ": 96, "STEP": 64, "THINK": 64, "STOP": 32})

    def test_all_expected_trace_turns_replay_in_existing_session(self):
        for built in self.pairs.values():
            for case in built.cases:
                service = wire.PassiveRegistry(case.construction.registry, skin=case.descriptor.skin)
                session = wire.Session(case.task_text, case.construction.world_edges, service)
                for turn in case.trace:
                    self.assertEqual(session.state.current, turn.current_before)
                    attempt = session.turn(turn.action, generation_request={"max_new_tokens": 256}, declared_tokens=1,
                                           actual_tokens=1, context_tokens=0, truncated=False, finish_reason="stop")
                    self.assertTrue(attempt.accepted)
                    self.assertEqual(attempt.response_bytes, turn.response.encode("ascii"))
                    self.assertEqual(session.state.current, turn.current_after)
                self.assertEqual(session.state.goal_arrival_stop, case.descriptor.terminal_class == "REACHED")
                self.assertEqual(session.state.current, case.facts.final_current)

    def test_goal_switch_store_world_identity_only_task_goal_changes(self):
        for pair in range(16):
            built = self.pairs[pair]
            left, right = built.cases
            self.assertIs(left.construction, right.construction)
            self.assertEqual(left.task.start, right.task.start)
            self.assertEqual(left.task.current, right.task.current)
            self.assertNotEqual(left.task.goal, right.task.goal)
            self.assertEqual(left.task_text.splitlines()[0:2], right.task_text.splitlines()[0:2])
            self.assertEqual(left.task_text.splitlines()[3], right.task_text.splitlines()[3])

    def test_mismatch_owners_v4_terminal_split_and_no_corrective_keep(self):
        totals = Counter()
        for pair in (1, 3, 5, 7):
            built = self.pairs[pair]
            queries = set()
            for member, case in enumerate(built.cases):
                totals[case.descriptor.terminal_class] += 1
                queries.add(case.facts.corrective_query)
                self.assertNotEqual(case.facts.failed_prediction, case.facts.failed_outcome)
                self.assertEqual(case.trace[2].response, "WORLD\nCURRENT " + case.facts.failed_outcome)
                self.assertEqual(case.trace[3].action, "THINK REVISE " + case.facts.failed_event)
                self.assertEqual(case.trace[4].action, "READ RELATION " + case.facts.corrective_query)
                self.assertEqual(case.trace[5].response, "WORLD\nCURRENT " + case.facts.selected_outcome)
                self.assertEqual(len(case.trace), 7)
                self.assertEqual(sum(turn.action.startswith("THINK ") for turn in case.trace), 1)
                self.assertFalse(any(turn.action.startswith("THINK KEEP") for turn in case.trace))
                corrective = case.construction.blocks["READ RELATION " + case.facts.corrective_query]
                expected_prefix = f"birth_train/p{pair:02d}/surp_m{member}/{case.descriptor.goal_index:02d}"
                for candidate, row in enumerate(corrective.rows):
                    self.assertEqual(row.event, built.role_tokens[f"{expected_prefix}/recovery_m{member}/{candidate}/event"])
                    self.assertEqual(row.recover, built.role_tokens[f"{expected_prefix}/recover2_m{member}/{candidate}/query"])
                    self.assertEqual(case.construction.read("READ RELATION " + row.recover), "MISS")
            self.assertEqual(len(queries), 2)
        self.assertEqual(totals, {"REACHED": 4, "UNRESOLVED": 4})

    def test_directories_recovery_counts_wrong_at_and_no_extra_edges(self):
        for pair, built in self.pairs.items():
            construction = built.cases[0].construction
            hubs = 24 if pair % 4 < 2 else 6
            mismatch = pair in MISMATCH_PAIRS
            self.assertEqual(sum(block.kind == "ROUTES" for block in construction.blocks.values()), hubs + 1)
            self.assertEqual(sum(block.kind == "EVENTS" for block in construction.blocks.values()), (hubs + 1) * 24 + (2 if mismatch else 0))
            self.assertEqual(len(construction.world_edges), (hubs + 1) * 96 + (8 if mismatch else 0))
            emitted_ports = set()
            unregistered = 0
            for role, token in built.role_tokens.items():
                parts = role.split("/")
                if parts[-1] == "node" and parts[2].startswith(("g", "x", "pred_", "surp_")):
                    self.assertEqual(construction.read("READ INDEX " + token), "MISS")
                if parts[-1] == "query" and construction.read("READ RELATION " + token) == "MISS":
                    unregistered += 1
            self.assertEqual(unregistered, (hubs + 1) * 96 + (6 if mismatch else 2 if pair in MISS_PAIRS else 0))
            inverse_nodes = {token: role.split("/")[2] for role, token in built.role_tokens.items() if role.endswith("/node")}
            for block in construction.blocks.values():
                self.assertEqual(wire.parse_service(block.raw, skin=construction.skin), block)
                self.assertEqual(worlds.render_service(block.kind, block.rows, skin=construction.skin), block.raw)
                if block.kind != "EVENTS":
                    continue
                for row in block.rows:
                    self.assertNotIn(row.port, emitted_ports)
                    emitted_ports.add(row.port)
                    state = inverse_nodes[row.node]
                    if state.startswith("x"):
                        self.assertEqual(inverse_nodes[row.got], f"x{(int(state[1:]) + 3) % 24:02d}")
                        self.assertEqual(construction.transition(row.node, row.port), row.got)
            self.assertEqual({port for at, port in construction.world_edges}, emitted_ports)

    def test_ordinary_worlds_match_editstopped_builders_exactly(self):
        for pair in range(0, 16, 2):
            built = self.pairs[pair]
            ordinary = worlds.build_ordinary_world(domain="birth_train", world=built.world,
                                                    role_tokens=self.tokens[pair], display_master=DISPLAY_MASTER)
            self.assertEqual(ordinary.registry, built.cases[0].construction.registry)
            self.assertEqual(ordinary.world_edges, built.cases[0].construction.world_edges)

    def test_v4_every_current_state_corrective_row_preserves_own_for_terminal_class(self):
        for pair in (1, 3, 5, 7):
            built = self.pairs[pair]
            inverse_goals = {node(built.role_tokens, built.world, f"g{goal:02d}"): goal for goal in range(24)}
            for case in built.cases:
                block = case.construction.blocks["READ RELATION " + case.facts.corrective_query]
                current_rows = [row for row in block.rows if row.node == case.facts.failed_outcome]
                self.assertEqual(len(current_rows), 2)
                for row in current_rows:
                    goal = inverse_goals[row.goal]
                    if pair // 4 % 2 == 0:
                        destination = row.goal
                    else:
                        state = f"a{goal:02d}" if pair % 4 == 1 else f"b{goal % 6:02d}"
                        destination = node(built.role_tokens, built.world, state)
                    self.assertEqual(row.got, destination)
                    self.assertEqual(case.construction.transition(row.node, row.port), destination)

    def test_missing_or_cross_owned_recovery_response_is_rejected(self):
        built = self.pairs[1]
        case = built.cases[0]
        request = "READ RELATION " + case.facts.corrective_query
        blocks = dict(case.construction.blocks)
        registry = dict(case.construction.registry)
        del blocks[request]
        del registry[request]
        construction = replace(case.construction, blocks=MappingProxyType(blocks), registry=MappingProxyType(registry))
        with self.assertRaisesRegex(ValueError, "missing_useful_events"):
            source.validate_birth_case(replace(case, construction=construction), role_tokens=built.role_tokens)
        other_rows = built.cases[1].construction.blocks["READ RELATION " + built.cases[1].facts.corrective_query].rows
        construction = changed_construction(case, request=request, rows=other_rows)
        with self.assertRaisesRegex(ValueError, "unique_matching_row"):
            source.validate_birth_case(replace(case, construction=construction), role_tokens=built.role_tokens)

    def test_recovery_matched_directory_orders(self):
        for pair in range(1, 32, 2):
            recovery, ordinary = self.pairs[pair], self.pairs[pair - 1]
            orders = []
            for built in (recovery, ordinary):
                inverse = {token: role.split("/")[2] for role, token in built.role_tokens.items() if role.endswith("/node")}
                directories = {inverse[block.rows[0].node]: tuple(inverse[row.goal] for row in block.rows)
                               for block in built.cases[0].construction.blocks.values() if block.kind == "ROUTES"}
                orders.append(directories)
            self.assertEqual(orders[0], orders[1])

    def test_validation_rejects_target_trace_task_and_descriptor_mutations(self):
        for pair, built in self.pairs.items():
            for case in built.cases:
                target = replace(case.targets[0], target_bytes=b"STOP")
                wrong_turn = replace(case.trace[-1], current_after=case.task.start)
                mutations = (
                    replace(case, targets=(target,) + case.targets[1:]),
                    replace(case, trace=case.trace[:-1] + (wrong_turn,)),
                    replace(case, task_text=case.task_text + "\n"),
                    replace(case, descriptor=replace(case.descriptor, skin=1 - case.descriptor.skin)),
                    replace(case, facts=replace(case.facts, selected_event=case.facts.selected_query)),
                    replace(case, memo_sha256="bad"),
                    replace(case, clarification_sha256="bad"))
                for mutation in mutations:
                    with self.assertRaises(ValueError):
                        source.validate_birth_case(mutation, role_tokens=self.tokens[pair])

    def test_validation_rejects_matching_field_prediction_and_edge_mutations(self):
        for pair, case in ((pair, case) for pair, built in self.pairs.items() for case in built.cases):
            query = case.facts.corrective_query or case.facts.selected_query
            request = "READ RELATION " + query
            rows = case.construction.blocks[request].rows
            selected = next(index for index, row in enumerate(rows) if row.event == case.facts.selected_event)
            for field, value in (("goal", case.task.start), ("node", case.task.goal), ("got", case.task.start)):
                changed = replace(rows[selected], **{field: value})
                construction = changed_construction(case, request=request, rows=rows[:selected] + (changed,) + rows[selected + 1:])
                with self.assertRaises(ValueError):
                    source.validate_birth_case(replace(case, construction=construction), role_tokens=self.tokens[pair])
            edges = dict(case.construction.world_edges)
            edges[rows[selected].node, rows[selected].port] = case.task.start
            with self.assertRaises(ValueError):
                source.validate_birth_case(replace(case, construction=changed_construction(case, edges=edges)), role_tokens=self.tokens[pair])
        for pair in MISMATCH_PAIRS:
            case = self.pairs[pair].cases[0]
            failed = next(row for row in case.construction.blocks["READ RELATION " + case.facts.failed_query].rows if row.event == case.facts.failed_event)
            edges = dict(case.construction.world_edges)
            edges[failed.node, failed.port] = failed.got
            with self.assertRaisesRegex(ValueError, "mismatch_owner_or_outcome"):
                source.validate_birth_case(replace(case, construction=changed_construction(case, edges=edges)), role_tokens=self.tokens[pair])

    def test_strict_miss_and_irrelevant_public_proof(self):
        for pair in (9, 11, 13, 15, 17, 19, 21, 23):
            for case in self.pairs[pair].cases:
                bad = wire.parse_service(case.trace[1].response.removeprefix("SERVICE\n"), skin=case.descriptor.skin)
                if pair in MISS_PAIRS:
                    self.assertEqual(bad.raw, "MISS")
                    self.assertFalse(any(row.query == case.facts.failed_query for block in case.construction.blocks.values() if block.kind == "ROUTES" for row in block.rows))
                else:
                    self.assertEqual(bad.kind, "EVENTS")
                    self.assertEqual(len(bad.rows), 4)
                    self.assertEqual(sum(row.node == case.task.current and row.goal == case.task.goal for row in bad.rows), 0)
                self.assertEqual(case.targets[0].operand, case.facts.failed_query)
                self.assertEqual(case.trace[2].response, "ACK")

    def test_exact_role_failures_before_any_store_output(self):
        world = "p01"
        original = self.tokens[1]
        for suffix in ("s/-/state/-/node", "s/00/useful/0/event", "s/00/recover/0/query",
                       "surp_m0/00/recovery_m0/0/port", "surp_m1/12/recover2_m1/3/query"):
            tokens = dict(original)
            del tokens["birth_train/p01/" + suffix]
            with self.assertRaisesRegex(ValueError, "missing_role"):
                source.build_birth_pair(world=world, role_tokens=tokens, display_master=DISPLAY_MASTER)
        for role in ("bad", "birth_train/p01/s/00/extra/0/query", "birth_train/p00/s/00/useful/-/query"):
            with self.assertRaisesRegex(ValueError, "extra_role"):
                source.build_birth_pair(world=world, role_tokens=dict(original, **{role: "M2AQ_BBBBBBBBBBBB"}), display_master=DISPLAY_MASTER)
        role = "birth_train/p01/s/00/useful/-/query"
        for token in ("M2AQ_AAAAAAAAAAAA", "M2AQ_BBBBBBBBBBBB\n", "M2AN_BBBBBBBBBBBB", b"M2AQ_BBBBBBBBBBBB", None):
            with self.assertRaisesRegex(ValueError, "invalid_role_token"):
                source.build_birth_pair(world=world, role_tokens=dict(original, **{role: token}), display_master=DISPLAY_MASTER)
        with self.assertRaisesRegex(ValueError, "duplicate_role_token"):
            source.build_birth_pair(world=world, role_tokens=dict(original, **{role: original["birth_train/p01/s/01/useful/-/query"]}), display_master=DISPLAY_MASTER)

    def test_immutable_snapshot_and_source_only_metadata(self):
        tokens = dict(self.tokens[2])
        built = source.build_birth_pair(world="p02", role_tokens=tokens, display_master=DISPLAY_MASTER)
        tokens.clear()
        self.assertEqual(dict(built.role_tokens), self.tokens[2])
        for mapping in (built.role_tokens, built.cases[0].construction.registry, built.cases[0].construction.world_edges, source.SCIENCE_GATES):
            with self.assertRaises(TypeError):
                mapping["bad"] = "bad"
        with self.assertRaises(FrozenInstanceError):
            built.cases[0].targets[0].phase = "bad"
        self.assertEqual(built.status, "PARTIAL_SOURCE_ONLY")
        self.assertEqual(built.cases[0].status, "PARTIAL_SOURCE_ONLY")

    def test_nonbirth_and_malformed_inputs_fail_closed(self):
        for world in ("h00", "seek_k0", "p32", "p0", None, 0):
            with self.assertRaises(worlds.UnsupportedConstructionError):
                source.describe_birth_case(world, "m0")
        for member in (0, 1, True, "m2", "m0\n"):
            with self.assertRaises(ValueError):
                source.describe_birth_case("p00", member)
        for master in (None, "synthetic", 1):
            with self.assertRaisesRegex(ValueError, "display_master"):
                source.build_birth_pair(world="p00", role_tokens=self.tokens[0], display_master=master)
        with self.assertRaisesRegex(ValueError, "mapping_required"):
            source.build_birth_pair(world="p00", role_tokens=list(self.tokens[0].items()), display_master=DISPLAY_MASTER)

    def test_all_relation_pairs_exact_two_for_leaf_differences_and_fixed_world(self):
        for pair in range(16, 32):
            built = self.pairs[pair]
            left, right = built.cases
            goal = (5 * (pair // 4)) % 12 if (pair // 4) % 2 == 0 else 12 + (7 * (pair // 4)) % 12
            slot = (3 * (pair // 4) + (0 if pair % 4 < 2 else 1)) % 4
            self.assertEqual(left.task_text, right.task_text)
            self.assertIs(left.construction.world_edges, right.construction.world_edges)
            self.assertEqual(set(left.construction.registry), set(right.construction.registry))
            target_query = (binding(built.role_tokens, built.world, f"s/{goal:02d}/recover/{slot}/query") if pair in MISMATCH_PAIRS else
                            binding(built.role_tokens, built.world, f"s/{goal:02d}/useful/-/query"))
            target_request = "READ RELATION " + target_query
            diffs = []
            for request, block in left.construction.blocks.items():
                counterpart = right.construction.blocks[request]
                if block.kind == "ROUTES":
                    self.assertEqual(block, counterpart)
                    continue
                for position, (before, after) in enumerate(zip(block.rows, counterpart.rows)):
                    for field in ("event", "node", "goal", "port", "got", "recover", "receipt"):
                        if getattr(before, field) != getattr(after, field):
                            diffs.append((request, position, field))
            self.assertEqual(set(diffs), {(target_request, slot, "goal"), (target_request, (slot + 2) % 4, "goal")})
            self.assertEqual(len(diffs), 2)
            target_rows = left.construction.blocks[target_request].rows
            counterpart = right.construction.blocks[target_request].rows
            self.assertEqual(target_rows[slot].goal, counterpart[(slot + 2) % 4].goal)
            self.assertEqual(target_rows[(slot + 2) % 4].goal, counterpart[slot].goal)
            self.assertNotEqual(left.facts.selected_event, right.facts.selected_event)
            self.assertEqual(left.clarification_sha256, source.CLARIFICATION_SHA256)
            self.assertEqual(right.clarification_sha256, source.CLARIFICATION_SHA256)

    def test_relation_mismatch_shared_failed_trace_and_off_trace_recovery_m1(self):
        for pair in (25, 27, 29, 31):
            built = self.pairs[pair]
            left, right = built.cases
            self.assertEqual(left.trace[:4], right.trace[:4])
            for field in ("selected_query", "failed_query", "failed_event", "failed_prediction", "failed_outcome", "corrective_query"):
                self.assertEqual(getattr(left.facts, field), getattr(right.facts, field))
            goal = left.descriptor.goal_index
            slot = (3 * (pair // 4) + (0 if pair % 4 < 2 else 1)) % 4
            failed_request = "READ RELATION " + left.facts.failed_query
            self.assertEqual(left.construction.blocks[failed_request], right.construction.blocks[failed_request])
            failed = left.construction.blocks[failed_request].rows
            for owner, candidate in ((0, slot), (1, (slot + 2) % 4)):
                row = failed[candidate]
                self.assertEqual(row.got, binding(built.role_tokens, built.world, f"pred_m{owner}/{goal:02d}/mismatch/-/node"))
                self.assertEqual(left.construction.transition(row.node, row.port), binding(built.role_tokens, built.world, f"surp_m{owner}/{goal:02d}/mismatch/-/node"))
            alternate_request = "READ RELATION " + failed[(slot + 2) % 4].recover
            self.assertEqual(left.construction.blocks[alternate_request], right.construction.blocks[alternate_request])
            self.assertNotIn(alternate_request, [turn.action for turn in left.trace + right.trace])
            alternative = left.construction.blocks[alternate_request]
            matching_slot = (3 * goal + 82 + left.descriptor.skin) % 4
            self.assertEqual(alternative.rows[matching_slot].goal, left.task.goal)
            self.assertEqual(alternative.rows[matching_slot].node, binding(built.role_tokens, built.world, f"surp_m1/{goal:02d}/mismatch/-/node"))
            for row in alternative.rows:
                self.assertEqual(left.construction.transition(row.node, row.port), row.got)
                self.assertEqual(left.construction.read("READ RELATION " + row.recover), "MISS")

    def test_all_16_mismatch_traces_eight_reached_eight_unresolved(self):
        cases = [case for pair in MISMATCH_PAIRS for case in self.pairs[pair].cases]
        self.assertEqual(len(cases), 16)
        self.assertEqual(Counter(case.descriptor.terminal_class for case in cases), {"REACHED": 8, "UNRESOLVED": 8})
        self.assertEqual(Counter(case.targets[3].command for case in cases), {"STOP": 8, "READ": 8})
        self.assertTrue(all(len(case.targets) == 4 and len(case.trace) == 7 for case in cases))
        self.assertTrue(all(sum(turn.action.startswith("THINK ") for turn in case.trace) == 1 for case in cases))

    def test_total_birth_registry_and_world_cardinalities(self):
        index_keys = useful_queries = recovery_queries = unregistered_queries = edges = 0
        for built in self.pairs.values():
            construction = built.cases[0].construction
            index_keys += sum(block.kind == "ROUTES" for block in construction.blocks.values())
            useful_queries += sum(role.endswith("/useful/-/query") for role in built.role_tokens)
            recovery_queries += sum(role.endswith("/query") and "/recover/" in role and
                                    construction.read("READ RELATION " + token) != "MISS" for role, token in built.role_tokens.items())
            unregistered_queries += sum(role.endswith("/query") and construction.read("READ RELATION " + token) == "MISS"
                                        for role, token in built.role_tokens.items())
            edges += len(construction.world_edges)
        self.assertEqual((index_keys, useful_queries, recovery_queries, unregistered_queries, edges),
                         (512, 12288, 16, 49208, 49216))


if __name__ == "__main__":
    unittest.main()
