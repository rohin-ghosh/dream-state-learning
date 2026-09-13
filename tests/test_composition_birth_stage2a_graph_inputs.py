"""Synthetic world/trace integration, not an independent scientific checker."""

from collections import Counter, defaultdict
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_checker as checker
from organism_v6 import composition_birth_stage2a_graph as graph
from organism_v6 import composition_birth_stage2a_graph_inputs as source
from organism_v6 import composition_birth_stage2a_worlds as worlds
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_birth import synthetic_bindings
from tests.test_composition_birth_stage2a_worlds import fixture as ordinary_fixture


def aliases_for_identities(tokens, identities):
    prefix = {"STATE": "S", "GOAL": "G", "QUERY": "Q", "EVENT": "E", "PORT": "P", "RECEIPT": "R"}
    owners = {token: role for role, token in tokens.items()}
    typed = defaultdict(list)
    for token, vertex_type in identities:
        typed[vertex_type].append((owners[token], token))
    return {(token, vertex_type): prefix[vertex_type] + f"{ordinal:04d}"
            for vertex_type, entries in typed.items()
            for ordinal, (role, token) in enumerate(sorted(entries,
                key=lambda entry: "/".join(entry[0].split("/")[2:]) + "#" + vertex_type))}


def independent_aliases(construction, tokens, task_goal):
    kinds = {"node": "STATE", "query": "QUERY", "event": "EVENT", "port": "PORT", "receipt": "RECEIPT"}
    identities = {(token, kinds[role.rsplit("/", 1)[1]]) for role, token in tokens.items()
                  if role.rsplit("/", 1)[1] in kinds}
    goals = {task_goal} | {row.goal for block in construction.blocks.values() for row in block.rows}
    identities.update((token, "GOAL") for token in goals)
    return aliases_for_identities(tokens, identities)


def public_aliases(case, tokens, target_ordinal, arm="CLOSED"):
    target = case.targets[target_ordinal]
    boundary = target.trace_index
    if arm == "CLOSED":
        turns = case.trace[:boundary]
        current = case.task.current
    else:
        indices = {
            "CONTINUE": (), "PROSPECT": (boundary - 1,), "READ_CHECK": (boundary - 1,),
            "STEP_CHECK": (boundary - 2, boundary - 1),
            "SEEK": ((boundary - 3, boundary - 2, boundary - 1)
                     if case.descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH" else (0,)),
        }[target.phase]
        turns = tuple(case.trace[index] for index in indices)
        current = turns[0].current_before if turns else target.current_before
    visible = {(case.task.start, "STATE"), (case.task.goal, "GOAL"), (current, "STATE")}
    for turn in turns:
        action = wire.parse_action(turn.action)
        if action.operation == "READ":
            visible.add((action.operand, "STATE" if action.verb == "INDEX" else "QUERY"))
            block = wire.parse_service(turn.response.removeprefix("SERVICE\n"), skin=case.construction.skin)
            for row in block.rows:
                visible.update(((row.node, "STATE"), (row.goal, "GOAL")))
                if block.kind == "ROUTES":
                    visible.add((row.query, "QUERY"))
                else:
                    visible.update(((row.event, "EVENT"), (row.port, "PORT"), (row.got, "STATE"),
                                    (row.recover, "QUERY"), (row.receipt, "RECEIPT")))
        elif action.operation == "STEP":
            visible.update(((turn.current_before, "STATE"), (action.operand, "PORT"),
                            (wire.parse_world(turn.response), "STATE")))
        elif action.operation == "THINK":
            visible.add((action.operand, "EVENT" if action.operand.startswith("M2AE_") else "QUERY"))
    return aliases_for_identities(tokens, visible)


def identity_topology(value, aliases):
    identities = {alias: identity for identity, alias in aliases.items()}
    vertices = {(identities[vertex["alias"]], tuple(vertex["flags"])) for vertex in value["vertices"]}
    edges = {(edge["label"], tuple(identities[alias] for alias in edge["tails"]),
              tuple(identities[alias] for alias in edge["heads"])) for edge in value["edges"]}
    return vertices, edges


def edge_set(value):
    return {canonical_json(edge) for edge in value["edges"]}


def change_block(construction, request, rows):
    registry, blocks = dict(construction.registry), dict(construction.blocks)
    raw = worlds.render_service(blocks[request].kind, rows, skin=construction.skin)
    registry[request] = raw
    blocks[request] = wire.parse_service(raw, skin=construction.skin)
    return replace(construction, registry=MappingProxyType(registry), blocks=MappingProxyType(blocks))


class GraphInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokens = {ordinal: synthetic_bindings(ordinal) for ordinal in (2, 3, 9, 11, 27)}
        with patch.object(wire, "allocate_opaque_namespace", side_effect=AssertionError("no allocation")):
            cls.pairs = {ordinal: birth.build_birth_pair(world=f"p{ordinal:02d}", role_tokens=tokens,
                                                        display_master=b"SYNTHETIC-GRAPH-BRIDGE")
                         for ordinal, tokens in cls.tokens.items()}
        cls.cases = {ordinal: pair.cases[0] for ordinal, pair in cls.pairs.items()}

    def root(self, case):
        return case.facts.failed_event or case.facts.selected_event

    def world_graph(self, ordinal, case=None, current=None, **changes):
        case = self.cases[ordinal] if case is None else case
        kwargs = dict(role_tokens=self.tokens[ordinal], current=current or case.targets[-1].current_before,
                      task_goal=case.task.goal, root_event=self.root(case))
        kwargs.update(changes)
        return source.build_world_graph(case.construction, **kwargs)

    def public_graph(self, ordinal, target_ordinal=3, arm="CLOSED", case=None, **changes):
        case = self.cases[ordinal] if case is None else case
        kwargs = dict(role_tokens=self.tokens[ordinal], target_ordinal=target_ordinal,
                      root_event=self.root(case), arm=arm)
        kwargs.update(changes)
        return source.build_public_graph(case, **kwargs)

    def test_contract_pins_and_all_gates_remain_false(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(sha256((root / source.CLARIFICATION_PATH).read_bytes()).hexdigest(), source.CLARIFICATION_SHA256)
        contract = root / "research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v4.md"
        self.assertEqual(sha256(contract.read_bytes()).hexdigest(), source.MEMO_SHA256)
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        for name in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"):
            self.assertIs(getattr(source, name), False)

    def test_world_uses_every_allocated_nonroute_owner_and_exact_edges(self):
        for ordinal, case in self.cases.items():
            with self.subTest(case=ordinal):
                world = self.world_graph(ordinal)
                aliases = independent_aliases(case.construction, self.tokens[ordinal], case.task.goal)
                self.assertEqual({vertex["alias"] for vertex in world["vertices"]}, set(aliases.values()))
                expected_counts = Counter(vertex_type for token, vertex_type in aliases)
                self.assertEqual(graph.typed_vertex_counts(world), dict(expected_counts))
                label_counts = Counter(edge["label"] for edge in world["edges"])
                route_rows = sum(len(block.rows) for block in case.construction.blocks.values() if block.kind == "ROUTES")
                event_rows = sum(len(block.rows) for block in case.construction.blocks.values() if block.kind == "EVENTS")
                self.assertEqual(label_counts["INDEXES"], route_rows)
                for label in ("CONTAINS", "FOR", "AT", "DID", "GOT", "RECOVER", "EVIDENCE"):
                    self.assertEqual(label_counts[label], event_rows)
                self.assertEqual(label_counts["WORLD"], len(case.construction.world_edges))
                self.assertEqual(set(label_counts), set(graph.INCIDENCE))
                self.assertNotIn("ROUTE", expected_counts)
                root_event = self.root(case)
                row = next(row for block in case.construction.blocks.values() if block.kind == "EVENTS"
                           for row in block.rows if row.event == root_event)
                flags = {flag: vertex["alias"] for vertex in world["vertices"] for flag in vertex["flags"]}
                self.assertEqual(flags["ROOT_EVENT"], aliases[root_event, "EVENT"])
                self.assertEqual(flags["ROOT_PORT"], aliases[row.port, "PORT"])
                self.assertEqual(flags["CURRENT"], aliases[case.targets[-1].current_before, "STATE"])

    def test_completed_ordinary_world_api_and_fragment_rejection(self):
        case = self.cases[2]
        construction = worlds.build_ordinary_world(domain="birth_train", world="p02", role_tokens=self.tokens[2],
                                                    display_master=b"SYNTHETIC-GRAPH-BRIDGE")
        value = self.world_graph(2, case=replace(case, construction=construction))
        self.assertTrue(value["edges"])
        with self.assertRaises(ValueError):
            self.world_graph(2, case=replace(case, construction=replace(construction, scope="ORDINARY_RELATION_FRAGMENT")))

    def test_ordinary_chain_world_retains_allocated_isolated_states(self):
        tokens = ordinary_fixture("dose_chain", "h00")
        construction = worlds.build_ordinary_world(domain="dose_chain", world="h00", role_tokens=tokens)
        start = tokens["dose_chain/h00/s/-/state/-/node"]
        goal = tokens["dose_chain/h00/g00/00/state/-/node"]
        row = next(row for block in construction.blocks.values() if block.kind == "EVENTS"
                   for row in block.rows if row.node == start and row.goal == goal)
        value = source.build_world_graph(construction, role_tokens=tokens, current=start,
                                         task_goal=goal, root_event=row.event)
        aliases = independent_aliases(construction, tokens, goal)
        isolated = aliases[tokens["dose_chain/h00/w00/00/state/-/node"], "STATE"]
        self.assertIn(isolated, {vertex["alias"] for vertex in value["vertices"]})
        self.assertNotIn(isolated, {alias for edge in value["edges"] for alias in edge["heads"] + edge["tails"]})

    def test_independent_json_checker_v2_accepts_explicit_identity_mapping(self):
        self.assertEqual(checker.SCHEMA_VERSION, "M2A-PARTIAL-GRAPH-CHECK-V2")
        case = self.cases[2]
        world = self.world_graph(2)
        public = self.public_graph(2, 3, "ATOM_LOCAL")
        core = graph.decision_core(public, actual_route_depth=1, family_motif="B_BUCKET_MERGES",
                                   flow="ORDINARY", goal_side="LEFT", phase="CONTINUE",
                                   predicted_actual_match=True, recovery_subtype="NONE",
                                   relevant_candidate_display_position=None, skin=case.construction.skin,
                                   terminal_class="REACHED", step_outcome_observed=True)
        envelope = {
            "schema_version": checker.SCHEMA_VERSION, "world_graph": world, "core": core,
            "public_to_world_aliases": source.public_to_world_aliases(
                case, role_tokens=self.tokens[2], target_ordinal=3, root_event=self.root(case), arm="ATOM_LOCAL"),
            "step_outcome_observed": True,
            "radius_graphs": {f"r{radius}": graph.radius_graph(world, radius) for radius in range(4)},
            "expected_hashes": {
                "world_graph": graph.graph_hash(world), "public_graph": graph.graph_hash(public),
                "radii": graph.signature(world), "signature": graph.signature_hash(world),
                "core": graph.core_hash(core, step_outcome_observed=True),
            },
        }
        receipt = checker.check_graph_core_json(canonical_json(envelope))
        self.assertEqual(receipt["status"], "PARTIAL_GRAPH_CHECK_ONLY")
        self.assertFalse(any(receipt["science_gates"].values()))
        self.assertFalse(any(receipt["certifications"].values()))

    def test_every_boundary_and_arm_has_observed_identity_topology_subset(self):
        for ordinal, case in self.cases.items():
            for target in case.targets:
                world = self.world_graph(ordinal, current=target.current_before)
                world_aliases = independent_aliases(case.construction, self.tokens[ordinal], case.task.goal)
                world_vertices, world_edges = identity_topology(world, world_aliases)
                for arm in ("CLOSED", "ATOM_LOCAL"):
                    with self.subTest(case=ordinal, phase=target.phase, arm=arm):
                        public = self.public_graph(ordinal, target.ordinal, arm)
                        aliases = public_aliases(case, self.tokens[ordinal], target.ordinal, arm)
                        public_vertices, public_edges = identity_topology(public, aliases)
                        self.assertEqual({identity for identity, flags in public_vertices}, set(aliases))
                        self.assertTrue(public_edges <= world_edges)
                        self.assertTrue(public_vertices <= world_vertices)
                        current = [vertex["alias"] for vertex in public["vertices"] if "CURRENT" in vertex["flags"]]
                        self.assertEqual(current, [aliases[target.current_before, "STATE"]])
                        self.assertLess(len(public["vertices"]), len(world["vertices"]))
                        self.assertLess(graph.typed_vertex_counts(public)["EVENT"], graph.typed_vertex_counts(world)["EVENT"])

    def test_seek_public_goal_and_query_aliases_are_locally_dense(self):
        public = self.public_graph(2, 0)
        for vertex_type, prefix in (("GOAL", "G"), ("QUERY", "Q")):
            self.assertEqual([vertex["alias"] for vertex in public["vertices"] if vertex["type"] == vertex_type],
                             [f"{prefix}{ordinal:04d}" for ordinal in range(24)])
        self.assertEqual(graph.typed_vertex_counts(public)["STATE"], 1)

    def test_continue_goal_is_g0000_even_when_world_goal_is_g0012(self):
        case = self.pairs[2].cases[1]
        world = self.world_graph(2, case=case)
        public = self.public_graph(2, 3, "ATOM_LOCAL", case=case)
        self.assertEqual([vertex["alias"] for vertex in world["vertices"] if "GOAL" in vertex["flags"]], ["G0012"])
        self.assertEqual([vertex["alias"] for vertex in public["vertices"] if vertex["type"] == "GOAL"], ["G0000"])
        self.assertEqual([vertex["alias"] for vertex in public["vertices"] if "GOAL" in vertex["flags"]], ["G0000"])
        mapping = source.public_to_world_aliases(case, role_tokens=self.tokens[2], target_ordinal=3,
                                                root_event=self.root(case), arm="ATOM_LOCAL")
        self.assertEqual(mapping["G0000"], "G0012")

    def test_hidden_isolated_owner_roster_changes_mapping_not_public_bytes(self):
        """Counterfactual synthetic roster, not a new scientific role inventory."""
        case = self.cases[2]
        public = self.public_graph(2, 0)
        arguments = dict(target_ordinal=0, root_event=self.root(case))
        mapping = source.public_to_world_aliases(case, role_tokens=self.tokens[2], **arguments)
        extended = dict(self.tokens[2])
        isolated = "M2AQ_BBBBBBBBBBBB"
        self.assertNotIn(isolated, extended.values())
        extended["birth_train/p02/a00/00/recover/0/query"] = isolated
        with patch.object(birth, "required_birth_roles", return_value=tuple(sorted(extended))):
            changed = source.build_public_graph(case, role_tokens=extended, **arguments)
            changed_mapping = source.public_to_world_aliases(case, role_tokens=extended, **arguments)
            world = source.build_world_graph(case.construction, role_tokens=extended,
                                             current=case.targets[0].current_before,
                                             task_goal=case.task.goal, root_event=self.root(case))
        self.assertEqual(graph.graph_bytes(changed), graph.graph_bytes(public))
        self.assertNotEqual(mapping["Q0000"], changed_mapping["Q0000"])
        world_aliases = independent_aliases(case.construction, extended, case.task.goal)
        isolated_alias = world_aliases[isolated, "QUERY"]
        self.assertIn(isolated_alias, {vertex["alias"] for vertex in world["vertices"]})
        self.assertNotIn(isolated_alias, {alias for edge in world["edges"] for alias in edge["tails"] + edge["heads"]})

    def test_evaluator_map_is_complete_injective_and_uses_observed_identities(self):
        case = self.cases[3]
        world_aliases = independent_aliases(case.construction, self.tokens[3], case.task.goal)
        for target in case.targets:
            for arm in ("CLOSED", "ATOM_LOCAL"):
                with self.subTest(target=target.ordinal, arm=arm):
                    public = self.public_graph(3, target.ordinal, arm)
                    observed = public_aliases(case, self.tokens[3], target.ordinal, arm)
                    mapping = source.public_to_world_aliases(case, role_tokens=self.tokens[3],
                        target_ordinal=target.ordinal, root_event=self.root(case), arm=arm)
                    self.assertEqual(mapping, {alias: world_aliases[identity] for identity, alias in observed.items()})
                    self.assertEqual(set(mapping), {vertex["alias"] for vertex in public["vertices"]})
                    self.assertEqual(len(mapping), len(set(mapping.values())))
                    self.assertNotIn("public_to_world_aliases", public)
                    self.assertFalse(any("/" in value or "M2A" in value for value in mapping.values()))

    def test_radii_still_preserve_world_aliases_not_public_numbering(self):
        world = self.world_graph(2)
        public = self.public_graph(2, 1)
        root_alias = next(vertex["alias"] for vertex in world["vertices"] if "ROOT_EVENT" in vertex["flags"])
        public_root = next(vertex["alias"] for vertex in public["vertices"] if "ROOT_EVENT" in vertex["flags"])
        self.assertNotEqual(root_alias, public_root)
        for radius in range(4):
            induced = graph.radius_graph(world, radius)
            self.assertIn(root_alias, {vertex["alias"] for vertex in induced["vertices"]})
            self.assertTrue({canonical_json(vertex) for vertex in induced["vertices"]}
                            <= {canonical_json(vertex) for vertex in world["vertices"]})
            self.assertTrue(edge_set(induced) <= edge_set(world))

    def test_relation_pair_second_member_bridges_effective_rows(self):
        case = self.pairs[27].cases[1]
        public = self.public_graph(27, case=case)
        world = self.world_graph(27, case=case)
        aliases = public_aliases(case, self.tokens[27], 3)
        world_aliases = independent_aliases(case.construction, self.tokens[27], case.task.goal)
        self.assertTrue(identity_topology(public, aliases)[1] <= identity_topology(world, world_aliases)[1])
        event = next(row for block in case.construction.blocks.values() if block.kind == "EVENTS"
                     for row in block.rows if row.event == case.facts.selected_event)
        self.assertIn(canonical_json({"label": "FOR", "tails": [aliases[event.event, "EVENT"]],
                                     "heads": [aliases[event.goal, "GOAL"]]}), edge_set(public))

    def test_unseen_future_rows_and_world_edges_not_imported(self):
        case = self.cases[2]
        early = self.public_graph(2, 0)
        self.assertEqual(set(edge["label"] for edge in early["edges"]), {"INDEXES"})
        self.assertFalse(any("ROOT_EVENT" in vertex["flags"] or "ROOT_PORT" in vertex["flags"]
                             for vertex in early["vertices"]))
        prospect = self.public_graph(2, 1)
        self.assertTrue(any(edge["label"] == "GOT" for edge in prospect["edges"]))
        self.assertFalse(any(edge["label"] == "WORLD" for edge in prospect["edges"]))
        check = self.public_graph(2, 2)
        self.assertEqual(sum(edge["label"] == "WORLD" for edge in check["edges"]), 1)
        continuation = self.public_graph(2, 3)
        self.assertEqual(sum(edge["label"] == "INDEXES" for edge in continuation["edges"]), 24)
        tokens = synthetic_bindings(6)
        unresolved = birth.build_birth_pair(world="p06", role_tokens=tokens,
                                            display_master=b"SYNTHETIC-UNRESOLVED-GRAPH").cases[0]
        self.assertEqual(unresolved.targets[3].command, "READ")
        boundary = source.build_public_graph(unresolved, role_tokens=tokens, target_ordinal=3,
                                             root_event=self.root(unresolved))
        self.assertEqual(sum(edge["label"] == "INDEXES" for edge in boundary["edges"]), 24)

    def test_atom_continue_is_only_authentic_task_facts_without_roots(self):
        case = self.cases[3]
        public = self.public_graph(3, 3, "ATOM_LOCAL")
        aliases = public_aliases(case, self.tokens[3], 3, "ATOM_LOCAL")
        self.assertEqual(public["edges"], [])
        self.assertEqual({vertex["alias"] for vertex in public["vertices"]},
                         {aliases[case.task.start, "STATE"], aliases[case.task.goal, "GOAL"],
                          aliases[case.targets[3].current_before, "STATE"]})
        self.assertFalse(any(flag.startswith("ROOT_") for vertex in public["vertices"] for flag in vertex["flags"]))

    def test_corrective_atom_prospect_starts_at_surprise_not_episode_current(self):
        case = self.cases[3]
        target = next(target for target in case.targets if target.phase == "PROSPECT")
        self.assertEqual(case.trace[target.trace_index - 1].current_before, case.facts.failed_outcome)
        public = self.public_graph(3, target.ordinal, "ATOM_LOCAL")
        aliases = public_aliases(case, self.tokens[3], target.ordinal, "ATOM_LOCAL")
        self.assertEqual([vertex["alias"] for vertex in public["vertices"] if "CURRENT" in vertex["flags"]],
                         [aliases[case.facts.failed_outcome, "STATE"]])
        self.assertFalse(any(edge["label"] == "WORLD" for edge in public["edges"]))
        self.assertNotEqual(aliases[case.task.start, "STATE"], aliases[case.facts.failed_outcome, "STATE"])

    def test_miss_query_visible_without_contains_and_unused_queries_retained_in_world(self):
        case = self.cases[9]
        public = self.public_graph(9, 0, "ATOM_LOCAL")
        aliases = public_aliases(case, self.tokens[9], 0, "ATOM_LOCAL")
        failed_alias = aliases[case.facts.failed_query, "QUERY"]
        self.assertIn(failed_alias, {vertex["alias"] for vertex in public["vertices"]})
        self.assertFalse(any(edge["label"] == "CONTAINS" and failed_alias in edge["tails"] for edge in public["edges"]))
        world = self.world_graph(9)
        world_aliases = independent_aliases(case.construction, self.tokens[9], case.task.goal)
        world_failed_alias = world_aliases[case.facts.failed_query, "QUERY"]
        incident = {alias for edge in world["edges"] for alias in edge["heads"] + edge["tails"]}
        self.assertNotIn(world_failed_alias, incident)
        self.assertIn(world_failed_alias, {vertex["alias"] for vertex in world["vertices"]})

    def test_mismatch_world_destination_is_actual_not_predicted(self):
        case = self.cases[3]
        target = case.targets[0]
        public = self.public_graph(3, 0)
        aliases = public_aliases(case, self.tokens[3], 0)
        step = next(turn for turn in case.trace[:target.trace_index] if turn.action.startswith("STEP "))
        tails = [aliases[step.current_before, "STATE"], aliases[step.action.split()[1], "PORT"]]
        actual = {"label": "WORLD", "tails": tails, "heads": [aliases[case.facts.failed_outcome, "STATE"]]}
        predicted = {**actual, "heads": [aliases[case.facts.failed_prediction, "STATE"]]}
        self.assertIn(canonical_json(actual), edge_set(public))
        self.assertNotIn(canonical_json(predicted), edge_set(public))
        world_aliases = independent_aliases(case.construction, self.tokens[3], case.task.goal)
        self.assertIn(("WORLD", ((step.current_before, "STATE"), (step.action.split()[1], "PORT")),
                       ((case.facts.failed_outcome, "STATE"),)),
                      identity_topology(self.world_graph(3), world_aliases)[1])

    def test_mutated_trace_world_response_current_and_boundary_rejected(self):
        case = self.cases[3]
        step_index = next(index for index, turn in enumerate(case.trace) if turn.action.startswith("STEP "))
        step = case.trace[step_index]
        mutations = (replace(step, response="WORLD\nCURRENT " + case.facts.failed_prediction),
                     replace(step, current_after=case.facts.failed_prediction),
                     replace(step, current_before=case.task.goal),
                     replace(step, target_ordinal=99))
        for turn in mutations:
            trace = list(case.trace)
            trace[step_index] = turn
            with self.subTest(turn=turn), self.assertRaises(ValueError):
                self.public_graph(3, case=replace(case, trace=tuple(trace)))
        for target in (replace(case.targets[1], trace_index=case.targets[1].trace_index + 1),
                       replace(case.targets[1], current_before=case.task.start)):
            targets = list(case.targets)
            targets[1] = target
            with self.assertRaises(ValueError):
                self.public_graph(3, 1, case=replace(case, targets=tuple(targets)))

    def test_fake_read_task_and_effective_world_mutations_rejected(self):
        case = self.cases[3]
        trace = list(case.trace)
        trace[0] = replace(trace[0], response="SERVICE\nMISS")
        with self.assertRaises(ValueError):
            self.public_graph(3, case=replace(case, trace=tuple(trace)))
        with self.assertRaises(ValueError):
            self.public_graph(3, case=replace(case, task_text=case.task_text.replace(case.task.start, case.task.goal)))
        edges = dict(case.construction.world_edges)
        first_step = next(turn for turn in case.trace if turn.action.startswith("STEP "))
        edges[first_step.current_before, first_step.action.split()[1]] = case.facts.failed_prediction
        construction = replace(case.construction, world_edges=MappingProxyType(edges))
        with self.assertRaises(ValueError):
            self.public_graph(3, case=replace(case, construction=construction))
        del edges[next(iter(edges))]
        with self.assertRaises(ValueError):
            self.world_graph(3, case=replace(case, construction=replace(construction, world_edges=edges)))

    def test_role_mapping_mutations_missing_duplicate_and_owner_swaps_rejected(self):
        case = self.cases[2]
        tokens = dict(self.tokens[2])
        mutations = []
        missing = dict(tokens)
        del missing[next(iter(missing))]
        mutations.append(missing)
        duplicate = dict(tokens)
        node_roles = [role for role in tokens if role.endswith("/node")]
        duplicate[node_roles[0]] = duplicate[node_roles[1]]
        mutations.append(duplicate)
        swapped = dict(tokens)
        port_roles = [role for role in tokens if role.endswith("/port")]
        swapped[port_roles[0]], swapped[port_roles[1]] = swapped[port_roles[1]], swapped[port_roles[0]]
        mutations.append(swapped)
        for changed in mutations:
            with self.subTest(mutation=len(changed)), self.assertRaises(ValueError):
                self.world_graph(2, role_tokens=changed)
        with self.assertRaises(ValueError):
            self.public_graph(2, role_tokens=mutations[0])
        with self.assertRaises(ValueError):
            self.world_graph(2, current="M2AN_AAAAAAAAAAAA")
        with self.assertRaises(ValueError):
            self.world_graph(2, task_goal=self.root(case))

    def test_missing_ambiguous_root_and_registry_mismatches_rejected(self):
        case = self.cases[2]
        for root in (None, case.task.start, "M2AE_BBBBBBBBBBBB"):
            with self.subTest(root=root), self.assertRaises(ValueError):
                self.world_graph(2, root_event=root)
        request = next(request for request, block in case.construction.blocks.items() if block.kind == "EVENTS")
        rows = case.construction.blocks[request].rows
        ambiguous = change_block(case.construction, request, (rows[0], rows[0], rows[2], rows[3]))
        with self.assertRaises(ValueError):
            self.world_graph(2, case=replace(case, construction=ambiguous), root_event=rows[0].event)
        registry = dict(case.construction.registry)
        registry[request] = "MISS"
        with self.assertRaises(ValueError):
            self.world_graph(2, case=replace(case, construction=replace(case.construction, registry=registry)))
        with self.assertRaises(ValueError):
            self.world_graph(2, case=replace(case, construction=replace(case.construction, memo_sha256="0" * 64)))
        wrong_root = next(row.event for block in case.construction.blocks.values() if block.kind == "EVENTS"
                          for row in block.rows if row.event != self.root(case))
        with self.assertRaises(ValueError):
            self.public_graph(2, root_event=wrong_root)

    def test_unknown_arms_ordinals_and_source_designations_rejected(self):
        for ordinal in (-1, 4, True, "0"):
            with self.subTest(ordinal=ordinal), self.assertRaises(ValueError):
                self.public_graph(2, ordinal)
        for arm in ("closed", "ATOM", None):
            with self.subTest(arm=arm), self.assertRaises(ValueError):
                self.public_graph(2, arm=arm)
        with self.assertRaises(ValueError):
            self.public_graph(2, case=replace(self.cases[2], clarification_sha256="0" * 64))


if __name__ == "__main__":
    unittest.main()
