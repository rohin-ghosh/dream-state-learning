"""Synthetic in-memory graph tests, not construction of scientific worlds."""

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import re
import unittest

from organism_v6 import composition_birth_stage2a_graph as source


V4_PATH = Path(__file__).resolve().parents[1] / (
    "research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v4.md"
)
V4_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"


def independent_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def pinned_vectors():
    raw = V4_PATH.read_bytes()
    if sha256(raw).hexdigest() != V4_SHA256:
        raise AssertionError("pinned_v4_contract_changed")
    text = raw.decode("utf-8")
    vectors = {}
    for number, name in ((2, "TRAIN_REACHED"), (3, "HELD_TWO_STEP")):
        section = text.split(f"### 4.{number} Corrected {name}\n", 1)[1]
        section = section.split("\n### ", 1)[0].split("\n## ", 1)[0]
        lines = section.splitlines()
        graphs = [line.encode("ascii") for line in lines if line.startswith('{"edges":')]
        signature_line = next(line for line in lines if line.startswith('{"r0":'))
        core_line = next(line for line in lines if line.startswith('{"actual_route_depth":'))
        radius = ({0: graphs[1], 1: graphs[0], 2: graphs[0], 3: graphs[0]}
                  if name == "TRAIN_REACHED" else {
                      int(line[1]): line[3:].encode("ascii")
                      for line in lines if re.match(r"r[0-3]=", line)
                  })
        if len(radius) != 4:
            raise AssertionError("missing_radius_vector")
        vectors[name] = {
            "graph": graphs[0],
            "graph_hash": re.search(r"Graph hash:\s*`([0-9a-f]{64})`", section).group(1),
            "radius": radius,
            "signature": signature_line.encode("ascii"),
            "radius_hashes": json.loads(signature_line),
            "signature_hash": lines[lines.index(signature_line) + 1],
            "core": core_line.encode("ascii"),
            "core_hash": lines[lines.index(core_line) + 1],
        }
    return vectors


def synthetic_path(depth, *, domain="synthetic", world="tiny"):
    """Hand-build only the one/two-step test paths with explicit role ownership."""
    if depth not in (1, 2):
        raise ValueError("synthetic_path_depth")
    vertices = []
    edges = []

    def vertex(state, block, kind, vertex_type, flags=(), goal="00", candidate="0"):
        role = f"{domain}/{world}/{state}/{goal}/{block}/{candidate}/{kind}"
        result = source.RoleVertex(role, vertex_type, flags)
        vertices.append(result)
        return result

    def edge(label, tails, heads):
        edges.append(source.RoleEdge(label, tuple(item.ref for item in tails),
                                     tuple(item.ref for item in heads)))

    states = {state: vertex(state, "state", "node", "STATE",
                            ("CURRENT",) if state == "g00" else (), "-", "-")
              for state in (("g00", "s") if depth == 1 else ("g00", "h00", "s"))}
    goal = vertex("g00", "state", "node", "GOAL", ("GOAL",), "-", "-")
    steps = [("s", "g00")] if depth == 1 else [("h00", "g00"), ("s", "h00")]
    for start, destination in steps:
        event = vertex(start, "useful", "event", "EVENT",
                       ("ROOT_EVENT",) if start == "s" else ())
        port = vertex(start, "useful", "port", "PORT",
                      ("ROOT_PORT",) if start == "s" else ())
        receipt = vertex(start, "useful", "receipt", "RECEIPT")
        recover = vertex(start, "recover", "query", "QUERY", candidate="-")
        useful = vertex(start, "useful", "query", "QUERY", candidate="-")
        edge("INDEXES", (states[start], goal), (useful,))
        edge("CONTAINS", (useful,), (event,))
        for label, head in (("FOR", goal), ("AT", states[start]), ("DID", port),
                            ("GOT", states[destination]), ("RECOVER", recover),
                            ("EVIDENCE", receipt)):
            edge(label, (event,), (head,))
        edge("WORLD", (states[start], port), (states[destination],))
    return vertices[::-1], edges[::-1]


class CorrectedVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = pinned_vectors()

    def test_both_corrected_graph_radius_signature_and_core_vectors(self):
        for depth, name in ((1, "TRAIN_REACHED"), (2, "HELD_TWO_STEP")):
            with self.subTest(vector=name):
                expected = self.vectors[name]
                graph = source.canonical_graph(*synthetic_path(depth))
                self.assertEqual(source.graph_bytes(graph), expected["graph"])
                self.assertEqual(source.parse_graph(expected["graph"]), graph)
                self.assertEqual(source.graph_hash(graph), expected["graph_hash"])
                self.assertEqual(sha256(b"M2A-GRAPH-V3\0" + expected["graph"]).hexdigest(),
                                 expected["graph_hash"])
                for radius in range(4):
                    radius_raw = expected["radius"][radius]
                    self.assertEqual(source.radius_bytes(graph, radius), radius_raw)
                    digest = sha256(b"M2A-RADIUS-V3\0" + str(radius).encode("ascii")
                                    + b"\0" + radius_raw).hexdigest()
                    self.assertEqual(digest, expected["radius_hashes"][f"r{radius}"])
                    self.assertEqual(source.radius_hash(graph, radius), digest)
                self.assertEqual(source.signature(graph), expected["radius_hashes"])
                self.assertEqual(source.signature_bytes(graph), expected["signature"])
                self.assertEqual(source.signature_hash(graph), expected["signature_hash"])
                self.assertEqual(sha256(b"M2A-SIGNATURE-V3\0" + expected["signature"]).hexdigest(),
                                 expected["signature_hash"])
                expected_core = json.loads(expected["core"])
                metadata = {key: value for key, value in expected_core.items()
                            if key not in ("public_graph", "typed_vertex_counts")}
                core = source.decision_core(graph, **metadata, step_outcome_observed=True)
                self.assertEqual(core, expected_core)
                self.assertEqual(source.core_bytes(core, step_outcome_observed=True), expected["core"])
                self.assertEqual(source.core_hash(core, step_outcome_observed=True), expected["core_hash"])
                self.assertEqual(sha256(b"M2A-CORE-V3\0" + expected["core"]).hexdigest(),
                                 expected["core_hash"])

    def test_corrected_latest_current_and_radius_alias_gaps(self):
        for depth in (1, 2):
            graph = source.canonical_graph(*synthetic_path(depth))
            current = [vertex["alias"] for vertex in graph["vertices"] if "CURRENT" in vertex["flags"]]
            self.assertEqual(current, ["S0000"])
        held = source.canonical_graph(*synthetic_path(2))
        radius_zero = source.radius_graph(held, 0)
        self.assertEqual([vertex["alias"] for vertex in radius_zero["vertices"]], ["E0001", "P0001"])
        radius_two = source.radius_graph(held, 2)
        self.assertNotIn("Q0000", [vertex["alias"] for vertex in radius_two["vertices"]])
        self.assertIn("Q0001", [vertex["alias"] for vertex in radius_two["vertices"]])

    def test_stale_current_changes_dependent_hashes_not_enum_version(self):
        for depth in (1, 2):
            graph = source.canonical_graph(*synthetic_path(depth))
            stale = deepcopy(graph)
            for vertex in stale["vertices"]:
                if vertex["type"] == "STATE":
                    vertex["flags"] = ["CURRENT"] if vertex["alias"] == f"S{depth:04d}" else []
            self.assertNotEqual(source.graph_hash(graph), source.graph_hash(stale))
            self.assertNotEqual(source.signature_hash(graph), source.signature_hash(stale))


class RawGraphTests(unittest.TestCase):
    def setUp(self):
        self.vertices, self.edges = synthetic_path(2)
        self.graph = source.canonical_graph(self.vertices, self.edges)

    def test_input_order_and_domain_world_do_not_enter_alias_bytes(self):
        self.assertEqual(self.graph, source.canonical_graph(self.vertices[::-1], self.edges[::-1]))
        self.assertEqual(self.graph, source.canonical_graph(*synthetic_path(2, domain="renamed", world="other")))
        raw = source.graph_bytes(self.graph)
        self.assertNotIn(b"synthetic", raw)
        self.assertNotIn(b"tiny", raw)

    def test_same_node_owner_has_distinct_goal_and_state_aliases(self):
        aliases = source.typed_aliases(self.vertices)
        goal = next(vertex for vertex in self.vertices if vertex.vertex_type == "GOAL")
        self.assertEqual(aliases[goal.ref], "G0000")
        self.assertEqual(aliases[(goal.role_key, "STATE")], "S0000")
        self.assertEqual(source.local_owner_key(goal.role_key, "GOAL"), "g00/-/state/-/node#GOAL")

    def test_isolated_allocated_query_survives_full_graph_not_radii(self):
        isolated = source.RoleVertex("synthetic/tiny/zz/-/recover/-/query", "QUERY")
        graph = source.canonical_graph(self.vertices + [isolated], self.edges)
        self.assertEqual(source.typed_vertex_counts(graph)["QUERY"], 5)
        for radius in range(4):
            self.assertNotIn("Q0004", [vertex["alias"] for vertex in source.radius_graph(graph, radius)["vertices"]])
        self.assertEqual(source.signature_hash(graph), source.signature_hash(self.graph))
        self.assertNotEqual(source.graph_hash(graph), source.graph_hash(self.graph))

    def test_hyperedge_clique_distance_and_induced_edge_rule(self):
        graph = source.radius_graph(self.graph, 1)
        self.assertIn({"tails": ["S0002", "G0000"], "heads": ["Q0003"], "label": "INDEXES"}, graph["edges"])
        self.assertNotIn("E0000", [vertex["alias"] for vertex in graph["vertices"]])
        for edge in graph["edges"]:
            self.assertTrue(set(edge["tails"] + edge["heads"]) <= {vertex["alias"] for vertex in graph["vertices"]})

    def test_outputs_do_not_alias_mutable_input(self):
        before = deepcopy(self.graph)
        result = source.radius_graph(self.graph, 3)
        result["vertices"][0]["flags"].append("CURRENT")
        result["edges"][0]["heads"].clear()
        self.assertEqual(self.graph, before)

    def test_invalid_role_types_syntax_and_owners(self):
        for role, vertex_type in (("bad", "STATE"), (None, "STATE"),
                                  ("d/w/s/-/state/-/node", "NODE"),
                                  ("d/w/s/-/state/-/route", "STATE"),
                                  ("d/w/s/24/state/-/node", "STATE"),
                                  ("d/w/s/-/state/4/node", "STATE"),
                                  ("d/w/é/-/state/-/node", "STATE"),
                                  ("d/w//-/state/-/node", "STATE"),
                                  ("d/w/s\n/-/state/-/node", "STATE")):
            with self.subTest(role=role, vertex_type=vertex_type), self.assertRaises(ValueError):
                source.typed_aliases([source.RoleVertex(role, vertex_type)])
        with self.assertRaises(ValueError):
            source.typed_aliases(self.vertices + [self.vertices[0]])
        with self.assertRaises(ValueError):
            source.typed_aliases([self.vertices[0], replace(self.vertices[1], role_key="other/" + self.vertices[1].role_key.split("/", 1)[1])])
        with self.assertRaises(ValueError):
            source.typed_aliases(iter(self.vertices))
        with self.assertRaises(ValueError):
            source.typed_aliases([{}])

    def test_typed_cardinality_bound_and_four_decimal_aliases(self):
        vertices = [source.RoleVertex(f"d/w/v{ordinal:05d}/-/state/-/node", "STATE")
                    for ordinal in range(10000)]
        aliases = source.typed_aliases(vertices[:-1])
        self.assertEqual(aliases[vertices[-2].ref], "S9998")
        with self.assertRaises(ValueError):
            source.typed_aliases(vertices)

    def test_raw_flags_reject_wrong_type_unknown_and_duplicate_current(self):
        state = next(vertex for vertex in self.vertices if vertex.vertex_type == "STATE" and not vertex.flags)
        for flags in (("GOAL",), ("current",), ("CURRENT", "CURRENT")):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                source.typed_aliases([replace(state, flags=flags)])
        vertices = [replace(vertex, flags=("CURRENT",)) if vertex == state else vertex for vertex in self.vertices]
        with self.assertRaises(ValueError):
            source.canonical_graph(vertices, self.edges)

    def test_raw_incidence_rejects_wrong_order_arity_and_unknown_owner(self):
        indexes = next(edge for edge in self.edges if edge.label == "INDEXES")
        for edge in (replace(indexes, tails=indexes.tails[::-1]),
                     replace(indexes, tails=indexes.tails[:1]),
                     replace(indexes, heads=()),
                     replace(indexes, label="indexes"),
                     replace(indexes, tails=(("missing", "STATE"), indexes.tails[1])),
                     replace(indexes, tails=(indexes.tails[0][0], indexes.tails[1]))):
            with self.subTest(edge=edge), self.assertRaises(ValueError):
                source.canonical_graph(self.vertices, [edge])
        with self.assertRaises(ValueError):
            source.canonical_graph(self.vertices, [{}])

    def test_effective_world_rejects_two_heads_for_one_transition(self):
        world = next(edge for edge in self.edges if edge.label == "WORLD")
        alternate = next(vertex for vertex in self.vertices
                         if vertex.vertex_type == "STATE" and vertex.ref != world.heads[0])
        with self.assertRaises(ValueError):
            source.canonical_graph(self.vertices, self.edges + [replace(world, heads=(alternate.ref,))])
        replaced = [replace(edge, heads=(alternate.ref,)) if edge == world else edge for edge in self.edges]
        graph = source.canonical_graph(self.vertices, replaced)
        self.assertNotEqual(source.graph_hash(graph), source.graph_hash(self.graph))

    def test_bad_serialized_shapes_sorting_types_and_duplicate_current(self):
        mutations = []
        for mutate in (
            lambda graph: graph.update(extra=True),
            lambda graph: graph.update(vertices=tuple(graph["vertices"])),
            lambda graph: graph["vertices"][0].update(type="event"),
            lambda graph: graph["vertices"][0].update(alias="S0000"),
            lambda graph: graph["vertices"][0].update(flags=["CURRENT"]),
            lambda graph: graph["vertices"][0].update(flags=["ROOT_EVENT"]),
            lambda graph: graph["vertices"][-1].update(flags=["CURRENT"]),
            lambda graph: graph["vertices"][0].update(extra="owner"),
            lambda graph: graph["vertices"].append(deepcopy(graph["vertices"][0])),
            lambda graph: graph["vertices"].reverse(),
            lambda graph: graph["edges"].reverse(),
            lambda graph: graph["edges"].append(deepcopy(graph["edges"][0])),
            lambda graph: graph["edges"][0].update(label="ROUTE"),
            lambda graph: graph["edges"][0].update(heads=["E9998"]),
            lambda graph: graph["edges"][0].update(tails=[]),
            lambda graph: graph["edges"][0].update(heads=["S0000"]),
            lambda graph: graph["edges"][0].update(heads="E0000"),
            lambda graph: graph["edges"][0].update(extra=[]),
        ):
            graph = deepcopy(self.graph)
            mutate(graph)
            mutations.append(graph)
        for ordinal, graph in enumerate(mutations):
            with self.subTest(mutation=ordinal), self.assertRaises(ValueError):
                source.graph_bytes(graph)

    def test_parser_rejects_noncanonical_and_duplicate_key_json(self):
        raw = source.graph_bytes(self.graph)
        for malformed in (b" " + raw, raw + b"\n", b'{"edges":[],"edges":[],"vertices":[]}',
                          b'{"vertices":[],"edges":[]}', b'{"edges":[],"vertices":[],"extra":NaN}'):
            with self.subTest(raw=malformed[:50]), self.assertRaises(ValueError):
                source.parse_graph(malformed)

    def test_radius_rejects_bad_bounds_and_unbound_or_unlinked_roots(self):
        for radius in (-1, 4, True, 1.0, "1", None):
            with self.subTest(radius=radius), self.assertRaises(ValueError):
                source.radius_graph(self.graph, radius)
        for flag in ("ROOT_EVENT", "ROOT_PORT"):
            graph = deepcopy(self.graph)
            for vertex in graph["vertices"]:
                vertex["flags"] = [value for value in vertex["flags"] if value != flag]
            source.validate_graph(graph)
            with self.assertRaises(ValueError):
                source.signature(graph)
        graph = deepcopy(self.graph)
        graph["edges"] = [edge for edge in graph["edges"] if edge["label"] != "DID"]
        with self.assertRaises(ValueError):
            source.radius_graph(graph, 0)

    def test_partial_status_does_not_open_gates(self):
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertEqual(source.MEMO_SHA256, V4_SHA256)
        self.assertTrue(source.GATES)
        self.assertFalse(any(source.GATES.values()))


class DecisionCoreTests(unittest.TestCase):
    def setUp(self):
        self.core = json.loads(pinned_vectors()["TRAIN_REACHED"]["core"])

    def test_exact_v4_enum_vocabulary_from_pinned_text(self):
        text = V4_PATH.read_text().split("### 4.1 Exhaustive core enums", 1)[1].split("### 4.2", 1)[0]
        expected = {match[0]: tuple(match[1].split())
                    for match in re.findall(r"^([a-z_]+):[ \t]+(.+)$", text, re.MULTILINE)}
        self.assertEqual(dict(source.CORE_ENUMS), expected)
        for key, values in expected.items():
            for invalid in (values[0].lower(), values[0].replace("_", "/") + "/", values[0] + " ", "UNKNOWN", None, 1):
                core = deepcopy(self.core)
                core[key] = invalid
                with self.subTest(key=key, value=invalid), self.assertRaises(ValueError):
                    source.core_hash(core, step_outcome_observed=True)

    def test_positions_match_v4_phase_ranges_and_nullability(self):
        for phase, valid, invalid in (
            ("SEEK", (0, 23), (None, -1, 24, True, 1.0)),
            ("PROSPECT", (0, 3), (None, -1, 4, True)),
            ("STEP_CHECK", (0, 3), (None, -1, 4, True)),
            ("READ_CHECK", (None,), (0, 3)),
            ("CONTINUE", (None,), (0, 23)),
        ):
            core = deepcopy(self.core)
            core["phase"] = phase
            for position in valid:
                core["relevant_candidate_display_position"] = position
                source.validate_core(core, step_outcome_observed=True)
            for position in invalid:
                core["relevant_candidate_display_position"] = position
                with self.subTest(phase=phase, position=position), self.assertRaises(ValueError):
                    source.validate_core(core, step_outcome_observed=True)

    def test_match_requires_explicit_step_outcome_context(self):
        for observed, match in ((True, True), (True, False), (False, None)):
            core = deepcopy(self.core)
            core["predicted_actual_match"] = match
            source.validate_core(core, step_outcome_observed=observed)
        for observed, match in ((True, None), (False, True), (False, False), (True, 1),
                                (True, "true"), (1, True), (None, None)):
            core = deepcopy(self.core)
            core["predicted_actual_match"] = match
            with self.subTest(observed=observed, match=match), self.assertRaises(ValueError):
                source.validate_core(core, step_outcome_observed=observed)
        core = deepcopy(self.core)
        core.update(phase="STEP_CHECK", relevant_candidate_display_position=0, predicted_actual_match=None)
        with self.assertRaises(ValueError):
            source.validate_core(core, step_outcome_observed=False)

    def test_exact_core_keys_integer_fields_counts_and_public_flags(self):
        for key, value in (("skin", True), ("skin", 2), ("actual_route_depth", -1),
                            ("actual_route_depth", 1.0), ("actual_route_depth", True),
                            ("typed_vertex_counts", {**self.core["typed_vertex_counts"], "EVENT": True}),
                            ("typed_vertex_counts", {**self.core["typed_vertex_counts"], "EVENT": 2}),
                            ("typed_vertex_counts", {"STATE": 2})):
            core = deepcopy(self.core)
            core[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                source.validate_core(core, step_outcome_observed=True)
        for key in self.core:
            core = deepcopy(self.core)
            del core[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                source.validate_core(core, step_outcome_observed=True)
        core = deepcopy(self.core)
        core["world_graph"] = core["public_graph"]
        with self.assertRaises(ValueError):
            source.validate_core(core, step_outcome_observed=True)
        for flag in ("CURRENT", "GOAL"):
            core = deepcopy(self.core)
            for vertex in core["public_graph"]["vertices"]:
                vertex["flags"] = [value for value in vertex["flags"] if value != flag]
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                source.validate_core(core, step_outcome_observed=True)

    def test_counts_use_only_public_graph_and_builder_detaches_input(self):
        graph = deepcopy(self.core["public_graph"])
        graph["vertices"] = [vertex for vertex in graph["vertices"] if vertex["type"] not in ("RECEIPT", "QUERY")]
        kept = {vertex["alias"] for vertex in graph["vertices"]}
        graph["edges"] = [edge for edge in graph["edges"] if set(edge["heads"] + edge["tails"]) <= kept]
        metadata = {key: value for key, value in self.core.items() if key not in ("public_graph", "typed_vertex_counts")}
        core = source.decision_core(graph, **metadata, step_outcome_observed=True)
        self.assertEqual(core["typed_vertex_counts"]["QUERY"], 0)
        self.assertEqual(core["typed_vertex_counts"]["RECEIPT"], 0)
        self.assertNotEqual(core["typed_vertex_counts"], self.core["typed_vertex_counts"])
        graph["edges"].clear()
        self.assertTrue(core["public_graph"]["edges"])
        self.assertEqual(source.core_bytes(core, step_outcome_observed=True), independent_json(core))


if __name__ == "__main__":
    unittest.main()
