"""Pinned synthetic v4 checks only; no material roots or scientific evidence."""

import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a_checker as checker


V4_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"
V3_SHA256 = "da833b9df37930d0b06f9206e5fa47d5b436b325e833e6f6b2f4221f4d8808d1"
ANALYSIS = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
V4_PATH = ANALYSIS / "2026-09-13_m_combine4_stage2a_binding_successor_v4.md"
V3_PATH = ANALYSIS / "2026-09-13_m_combine4_stage2a_binding_successor_v3.md"
KINDS = ("EVENT", "GOAL", "PORT", "QUERY", "RECEIPT", "STATE")
RADII = ("r0", "r1", "r2", "r3")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii")


def digest(domain, value):
    return sha256(domain + b"\0" + encode(value)).hexdigest()


def count_vertices(graph):
    return {kind: sum(vertex["type"] == kind for vertex in graph["vertices"])
            for kind in KINDS}


def commitments(envelope):
    radii = {name: digest(b"M2A-RADIUS-V3\0" + name[1:].encode("ascii"),
                          envelope["radius_graphs"][name]) for name in RADII}
    return {
        "world_graph": digest(b"M2A-GRAPH-V3", envelope["world_graph"]),
        "public_graph": digest(b"M2A-GRAPH-V3", envelope["core"]["public_graph"]),
        "radii": radii,
        "signature": digest(b"M2A-SIGNATURE-V3", radii),
        "core": digest(b"M2A-CORE-V3", envelope["core"]),
    }


def expanded_radii(graph):
    reached = {vertex["alias"] for vertex in graph["vertices"]
               if set(vertex["flags"]) & {"ROOT_EVENT", "ROOT_PORT"}}
    result = {}
    for name in RADII:
        result[name] = {
            "edges": [deepcopy(edge) for edge in graph["edges"]
                      if set(edge["tails"] + edge["heads"]) <= reached],
            "vertices": [deepcopy(vertex) for vertex in graph["vertices"]
                         if vertex["alias"] in reached],
        }
        crossing = [set(edge["tails"] + edge["heads"]) for edge in graph["edges"]
                    if reached.intersection(edge["tails"] + edge["heads"])]
        reached = reached.union(*crossing)
    return result


def rebind(envelope, *, derive_radii=False, counts=False):
    if derive_radii:
        envelope["radius_graphs"] = expanded_radii(envelope["world_graph"])
    if counts:
        envelope["core"]["typed_vertex_counts"] = count_vertices(envelope["core"]["public_graph"])
    envelope["expected_hashes"] = commitments(envelope)
    return envelope


def sort_graph(graph):
    graph["vertices"].sort(key=lambda vertex: vertex["alias"])
    graph["edges"].sort(key=encode)


def with_hidden_prefixes(envelope, offsets):
    changed = deepcopy(envelope)
    world = changed["world_graph"]
    translated = {
        vertex["alias"]: f'{vertex["alias"][0]}{int(vertex["alias"][1:]) + offsets.get(vertex["type"], 0):04d}'
        for vertex in world["vertices"]
    }
    for vertex in world["vertices"]:
        vertex["alias"] = translated[vertex["alias"]]
    for edge in world["edges"]:
        for side in ("heads", "tails"):
            edge[side] = [translated[alias] for alias in edge[side]]
    for kind, offset in offsets.items():
        world["vertices"].extend({"alias": f"{kind[0]}{index:04d}", "flags": [], "type": kind}
                                 for index in range(offset))
    changed["public_to_world_aliases"] = {
        alias: translated[target] for alias, target in changed["public_to_world_aliases"].items()
    }
    sort_graph(world)
    return rebind(changed, derive_radii=True)


def pinned_envelopes():
    raw = V4_PATH.read_bytes()
    if sha256(raw).hexdigest() != V4_SHA256:
        raise AssertionError("adopted v4 bytes changed")
    sections = re.split(r"^### 4\.[23] Corrected ", raw.decode("ascii"), flags=re.M)[1:]
    if len(sections) != 2:
        raise AssertionError("both pinned synthetic vectors required")
    envelopes = {}
    for section in sections:
        title = section.splitlines()[0]
        section = section.split("\n## 5.")[0]
        blocks = re.findall(r"```text\n(.*?)\n```", section, flags=re.S)
        graph = json.loads(blocks[0])
        if title == "TRAIN_REACHED":
            radii = {"r0": json.loads(blocks[1]), **{name: deepcopy(graph) for name in RADII[1:]}}
        else:
            radii = {line[:2]: json.loads(line[3:]) for line in blocks[1].splitlines()}
        signature_lines = blocks[2].splitlines()
        core_lines = blocks[3].splitlines()
        radius_hashes = dict(zip(RADII, signature_lines[:4]))
        if json.loads(signature_lines[4]) != radius_hashes:
            raise AssertionError("memo signature preimage disagrees with radius hashes")
        graph_hash = re.search(r"Graph hash:\s*`([0-9a-f]{64})`", section).group(1)
        envelopes[title] = {
            "schema_version": "M2A-PARTIAL-GRAPH-CHECK-V2",
            "step_outcome_observed": True,
            "public_to_world_aliases": {vertex["alias"]: vertex["alias"]
                                        for vertex in graph["vertices"]},
            "world_graph": graph,
            "core": json.loads(core_lines[0]),
            "radius_graphs": radii,
            "expected_hashes": {
                "world_graph": graph_hash, "public_graph": graph_hash,
                "radii": radius_hashes, "signature": signature_lines[5],
                "core": core_lines[1],
            },
        }
    return envelopes


class CanonicalJsonTests(unittest.TestCase):
    def test_restricted_roundtrip_and_key_sorting(self):
        value = {"z": [None, True, False, 42, -12, "\t\n\"\\"], "A": {"x": 0}}
        raw = encode(value)
        self.assertEqual(checker.canonical_json_bytes(value), raw)
        self.assertEqual(checker.loads_canonical_json(raw), value)

    def test_rejects_noncanonical_or_malformed_bytes(self):
        samples = (
            b'{"a":1}\n', b'{ "a":1}', b'{"z":1,"a":2}', b'{"a":1,"a":2}',
            b'{"a":{"x":1,"x":2}}', b'{"a":1,"\\u0061":2}',
            b'{"a":-0}', b'{"a":0.0}', b'{"a":-0.0}', b'{"a":1e0}',
            b'{"a":NaN}', b'{"a":Infinity}', b'{"a":-Infinity}',
            b'{"a":"\\u00e9"}', b'{"a":"\\ud800"}', b'{"a":"\\r"}',
            b'{"a":"\\u0000"}', b'{"a":"\\u0041"}', b'{"a":"\\/"}',
            b'{"a":"\xff"}', b'\xef\xbb\xbf{}', b'{\r}', b'{\0}',
            b'{"a":01}', b'{"a":+1}', b'{"a":', b'{}{}', b'',
        )
        for raw in samples:
            with self.subTest(raw=raw), self.assertRaises(checker.GraphCheckError):
                checker.loads_canonical_json(raw)

    def test_rejects_non_bytes_inputs(self):
        for value in ("{}", bytearray(b"{}"), memoryview(b"{}"), None, {}, 1):
            with self.subTest(value=value), self.assertRaises(checker.GraphCheckError):
                checker.loads_canonical_json(value)

    def test_encoder_rejects_coercions_and_unsupported_types(self):
        for value in ({1: "a"}, {"x": (1, 2)}, {"x": {1}}, b"bytes", 1.0,
                      float("nan"), float("inf"), "\r", "\0", "é", object()):
            with self.subTest(value=value), self.assertRaises(checker.GraphCheckError):
                checker.canonical_json_bytes(value)

    def test_integer_bounds_and_bool_distinction(self):
        for value in (-checker.MAX_INTEGER, checker.MAX_INTEGER, True, 0):
            self.assertEqual(checker.loads_canonical_json(encode(value)), value)
        for raw in (str(checker.MAX_INTEGER + 1).encode(), b"9" * 5000,
                    str(-checker.MAX_INTEGER - 1).encode()):
            with self.subTest(raw=raw[:30]), self.assertRaises(checker.GraphCheckError):
                checker.loads_canonical_json(raw)
        with self.assertRaises(checker.GraphCheckError):
            checker.canonical_json_bytes(checker.MAX_INTEGER + 1)

    def test_depth_limits_and_string_brackets(self):
        self.assertEqual(checker.loads_canonical_json(encode("[" * 100)), "[" * 100)
        with self.assertRaisesRegex(checker.GraphCheckError, "nesting"):
            checker.loads_canonical_json(b"[" * 33 + b"0" + b"]" * 33)
        cycle = []
        cycle.append(cycle)
        with self.assertRaisesRegex(checker.GraphCheckError, "nesting"):
            checker.canonical_json_bytes(cycle)

    def test_byte_limits_before_parsing_and_after_encoding(self):
        with patch.object(checker, "MAX_BYTES", 4):
            with self.assertRaisesRegex(checker.GraphCheckError, "byte limit"):
                checker.loads_canonical_json(b"12345")
            with self.assertRaisesRegex(checker.GraphCheckError, "byte limit"):
                checker.canonical_json_bytes("12345")


class PinnedCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = pinned_envelopes()

    def setUp(self):
        self.envelope = deepcopy(self.vectors["HELD_TWO_STEP"])

    def reject(self, envelope, message=None):
        with self.assertRaisesRegex(checker.GraphCheckError, message or "."):
            checker.check_graph_core_json(encode(envelope))

    def test_adopted_v4_and_imported_v3_hashes(self):
        self.assertEqual(checker.CONTRACT_SHA256, V4_SHA256)
        self.assertEqual(sha256(V4_PATH.read_bytes()).hexdigest(), V4_SHA256)
        self.assertEqual(sha256(V3_PATH.read_bytes()).hexdigest(), V3_SHA256)

    def test_both_corrected_full_radius_signature_core_vectors(self):
        for name, envelope in self.vectors.items():
            with self.subTest(vector=name):
                raw = encode(envelope)
                receipt = checker.check_graph_core_json(raw)
                self.assertEqual(receipt["hashes"], envelope["expected_hashes"])
                self.assertEqual(commitments(envelope), envelope["expected_hashes"])
                self.assertEqual(expanded_radii(envelope["world_graph"]), envelope["radius_graphs"])
                self.assertEqual(receipt["input_sha256"], sha256(raw).hexdigest())
                self.assertEqual(receipt["schema_version"], "M2A-PARTIAL-GRAPH-CHECK-V2")
                self.assertEqual(receipt["status"], "PARTIAL_GRAPH_CHECK_ONLY")
                self.assertIs(receipt["graph_checks_passed"], True)
                self.assertTrue(receipt["science_gates"])
                self.assertTrue(all(value is False for value in receipt["science_gates"].values()))
                self.assertTrue(all(value is False for value in receipt["certifications"].values()))

    def test_graph_module_outputs_compared_only_in_test(self):
        from organism_v6 import composition_birth_stage2a_graph as graph_module

        for name, envelope in self.vectors.items():
            with self.subTest(vector=name):
                world = graph_module.parse_graph(encode(envelope["world_graph"]))
                produced = deepcopy(envelope)
                produced["world_graph"] = world
                produced["radius_graphs"] = {
                    key: graph_module.radius_graph(world, radius)
                    for radius, key in enumerate(RADII)
                }
                produced["expected_hashes"] = {
                    "world_graph": graph_module.graph_hash(world),
                    "public_graph": graph_module.graph_hash(envelope["core"]["public_graph"]),
                    "radii": graph_module.signature(world),
                    "signature": graph_module.signature_hash(world),
                    "core": graph_module.core_hash(envelope["core"], step_outcome_observed=True),
                }
                self.assertEqual(produced, envelope)
                checker.check_graph_core_json(encode(produced))

    def test_exact_keys_reject_extra_and_missing_at_every_layer(self):
        paths = ((), ("world_graph",), ("core",), ("radius_graphs",),
                 ("expected_hashes",), ("expected_hashes", "radii"),
                 ("core", "typed_vertex_counts"), ("core", "public_graph"),
                 ("world_graph", "vertices", 0), ("world_graph", "edges", 0),
                 ("radius_graphs", "r0"), ("public_to_world_aliases",))
        for path in paths:
            for mode in ("extra", "missing"):
                changed = deepcopy(self.envelope)
                target = changed
                for key in path:
                    target = target[key]
                if mode == "extra":
                    target["unexpected"] = None
                else:
                    del target[next(iter(target))]
                with self.subTest(path=path, mode=mode):
                    self.reject(changed, "keys")

    def test_wrong_envelope_types_and_version(self):
        for value in (None, [], "graph", 1, True):
            self.reject(value, "object")
        self.envelope["schema_version"] = "M2A-GRAPH-V3"
        self.reject(self.envelope, "schema version")

    def test_v1_explicitly_rejected_not_reinterpreted_or_modified(self):
        for with_map in (False, True):
            changed = deepcopy(self.envelope)
            changed["schema_version"] = "M2A-PARTIAL-GRAPH-CHECK-V1"
            if not with_map:
                del changed["public_to_world_aliases"]
            raw = encode(changed)
            with self.subTest(with_map=with_map):
                self.reject(changed, "schema version V1 unsupported; V2 requires explicit")
                self.assertEqual(raw, encode(changed))

    def test_each_hash_field_and_each_radius_hash_is_checked(self):
        paths = [("world_graph",), ("public_graph",), ("signature",), ("core",)]
        paths += [("radii", name) for name in RADII]
        for path in paths:
            changed = deepcopy(self.envelope)
            target = changed["expected_hashes"]
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = "0" * 64
            with self.subTest(path=path):
                self.reject(changed, "mismatch")

    def test_malformed_hashes_rejected_before_use(self):
        for value in (None, 1, [], "A" * 64, "g" * 64, "a" * 63, "a" * 65):
            changed = deepcopy(self.envelope)
            changed["expected_hashes"]["core"] = value
            with self.subTest(value=value):
                self.reject(changed, "SHA-256")

    def test_edge_mutation_with_old_commitment_rejected(self):
        for graph in (self.envelope["world_graph"], self.envelope["core"]["public_graph"]):
            next(edge for edge in graph["edges"] if edge["label"] == "WORLD")["heads"] = ["S0002"]
            sort_graph(graph)
        self.envelope["radius_graphs"] = expanded_radii(self.envelope["world_graph"])
        self.reject(self.envelope, "mismatch")

    def test_edge_incidence_order_arity_label_and_dangling_alias(self):
        for label, side, value in (
            ("WORLD", "tails", ["P0000", "S0001"]),
            ("INDEXES", "tails", ["G0000", "S0001"]),
            ("AT", "heads", ["P0000"]), ("AT", "heads", ["S9999"]),
            ("AT", "heads", []), ("AT", "heads", ["S0000", "S0001"]),
            ("AT", "heads", "S0000"), ("AT", "heads", [None]),
            ("AT", "label", "at"), ("AT", "label", []),
        ):
            changed = deepcopy(self.envelope)
            graph = changed["world_graph"]
            next(edge for edge in graph["edges"] if edge["label"] == label)[side] = value
            sort_graph(graph)
            with self.subTest(label=label, side=side, value=value):
                self.reject(rebind(changed))

    def test_vertex_alias_type_and_flag_mutations(self):
        for field, value in (
            ("type", "STATE"), ("type", "event"), ("type", []),
            ("alias", "E1"), ("alias", "E00000"), ("alias", "X0000"),
            ("alias", None), ("flags", ["CURRENT"]), ("flags", ["UNKNOWN"]),
            ("flags", ["ROOT_EVENT", "ROOT_EVENT"]), ("flags", "ROOT_EVENT"),
            ("flags", [[]]),
        ):
            changed = deepcopy(self.envelope)
            changed["world_graph"]["vertices"][0][field] = value
            with self.subTest(field=field, value=value):
                self.reject(rebind(changed))

    def test_duplicate_unsorted_vertices_and_edges(self):
        for field in ("vertices", "edges"):
            for duplicate in (True, False):
                changed = deepcopy(self.envelope)
                values = changed["world_graph"][field]
                if duplicate:
                    values.insert(0, deepcopy(values[0]))
                else:
                    values.reverse()
                with self.subTest(field=field, duplicate=duplicate):
                    self.reject(rebind(changed))

    def test_full_alias_gaps_are_not_allowed(self):
        self.envelope["world_graph"]["vertices"].append(
            {"alias": "Q0005", "flags": [], "type": "QUERY"})
        sort_graph(self.envelope["world_graph"])
        self.reject(rebind(self.envelope), "contiguous")

    def test_current_and_goal_counts_even_with_rehashed_inputs(self):
        for flag, alias in (("CURRENT", "S0001"), ("GOAL", "G0001")):
            for operation in ("missing", "duplicate"):
                changed = deepcopy(self.envelope)
                graph = changed["core"]["public_graph"]
                if operation == "missing":
                    for vertex in graph["vertices"]:
                        vertex["flags"] = [item for item in vertex["flags"] if item != flag]
                elif flag == "CURRENT":
                    next(vertex for vertex in graph["vertices"] if vertex["alias"] == alias)["flags"] = [flag]
                else:
                    graph["vertices"].append({"alias": alias, "flags": [flag], "type": "GOAL"})
                    sort_graph(graph)
                with self.subTest(flag=flag, operation=operation):
                    self.reject(rebind(changed, counts=True), flag + " count")

    def test_stale_current_mutation_fails_pinned_hashes(self):
        for graph in (self.envelope["world_graph"], self.envelope["core"]["public_graph"]):
            for vertex in graph["vertices"]:
                if vertex["type"] == "STATE":
                    vertex["flags"] = ["CURRENT"] if vertex["alias"] == "S0002" else []
        self.envelope["radius_graphs"] = expanded_radii(self.envelope["world_graph"])
        self.reject(self.envelope, "mismatch")

    def test_current_flag_cannot_move_only_in_public_graph(self):
        for vertex in self.envelope["core"]["public_graph"]["vertices"]:
            if vertex["type"] == "STATE":
                vertex["flags"] = ["CURRENT"] if vertex["alias"] == "S0001" else []
        self.reject(rebind(self.envelope), "vertex/flags")

    def test_missing_duplicate_or_unlinked_roots(self):
        for flag, alternate in (("ROOT_EVENT", "E0000"), ("ROOT_PORT", "P0000")):
            for operation in ("missing", "duplicate", "move"):
                changed = deepcopy(self.envelope)
                for vertex in changed["world_graph"]["vertices"]:
                    if operation != "duplicate" and flag in vertex["flags"]:
                        vertex["flags"].remove(flag)
                    if operation != "missing" and vertex["alias"] == alternate:
                        vertex["flags"].append(flag)
                with self.subTest(flag=flag, operation=operation):
                    self.reject(rebind(changed, derive_radii=True), "root|ROOT")

    def test_root_mutation_preserving_did_still_fails_pinned_hash(self):
        for graph in (self.envelope["world_graph"], self.envelope["core"]["public_graph"]):
            for vertex in graph["vertices"]:
                if vertex["type"] in ("EVENT", "PORT"):
                    flag = "ROOT_EVENT" if vertex["type"] == "EVENT" else "ROOT_PORT"
                    vertex["flags"] = [flag] if vertex["alias"].endswith("0000") else []
        self.envelope["radius_graphs"] = expanded_radii(self.envelope["world_graph"])
        self.reject(self.envelope, "mismatch")

    def test_single_head_event_fields_and_world_transitions(self):
        for label, destination in (("WORLD", "S0002"), ("AT", "S0000"), ("DID", "P0001")):
            changed = deepcopy(self.envelope)
            graph = changed["world_graph"]
            extra = deepcopy(next(edge for edge in graph["edges"] if edge["label"] == label))
            extra["heads"] = [destination]
            graph["edges"].append(extra)
            sort_graph(graph)
            with self.subTest(label=label):
                self.reject(rebind(changed), "functional")

    def test_all_core_enums_reject_unlisted_spelling_and_non_strings(self):
        for field in ("phase", "flow", "recovery_subtype", "family_motif", "goal_side", "terminal_class"):
            for value in ("unknown", "READ-CHECK", "NONE/NONE", " LEFT", "left", None, [], 1):
                changed = deepcopy(self.envelope)
                changed["core"][field] = value
                with self.subTest(field=field, value=value):
                    self.reject(rebind(changed), "enum")

    def test_every_v4_enum_is_accepted_as_syntax_not_semantic_certification(self):
        text = V4_PATH.read_text()
        enum_block = text.split("### 4.1 Exhaustive core enums", 1)[1].split("```text\n", 1)[1].split("```", 1)[0]
        for line in enum_block.splitlines():
            field, values = line.split(":", 1)
            self.assertEqual(tuple(values.split()), checker.ENUMS[field])
            for value in values.split():
                changed = deepcopy(self.envelope)
                changed["core"][field] = value
                if field == "phase" and value in ("SEEK", "PROSPECT", "STEP_CHECK"):
                    changed["core"]["relevant_candidate_display_position"] = 0
                with self.subTest(field=field, value=value):
                    result = checker.check_graph_core_json(encode(rebind(changed)))
                    self.assertFalse(result["science_gates"]["GO_CLAIM"])

    def test_positions_and_nullability(self):
        cases = (
            ("SEEK", (0, 23), (None, -1, 24, True)),
            ("PROSPECT", (0, 3), (None, -1, 4, True)),
            ("STEP_CHECK", (0, 3), (None, -1, 4, True)),
            ("READ_CHECK", (None,), (0, True)),
            ("CONTINUE", (None,), (0, True)),
        )
        for phase, valid, invalid in cases:
            for position in valid + invalid:
                changed = deepcopy(self.envelope)
                changed["core"].update(phase=phase, relevant_candidate_display_position=position)
                rebind(changed)
                with self.subTest(phase=phase, position=position):
                    if any(type(position) is type(item) and position == item for item in valid):
                        checker.check_graph_core_json(encode(changed))
                    else:
                        self.reject(changed, "position")

    def test_match_uses_explicit_caller_declared_context_only(self):
        for observed, match in ((True, True), (True, False), (False, None)):
            changed = deepcopy(self.envelope)
            changed["step_outcome_observed"] = observed
            changed["core"]["predicted_actual_match"] = match
            checker.check_graph_core_json(encode(rebind(changed)))
        for observed, match in ((True, None), (False, True), (False, False),
                                (True, 1), (True, "true"), (1, True), (None, None)):
            changed = deepcopy(self.envelope)
            changed["step_outcome_observed"] = observed
            changed["core"]["predicted_actual_match"] = match
            with self.subTest(observed=observed, match=match):
                self.reject(rebind(changed), "match|observed")
        self.envelope["step_outcome_observed"] = False
        self.envelope["core"].update(phase="STEP_CHECK", predicted_actual_match=None,
                                     relevant_candidate_display_position=0)
        self.reject(rebind(self.envelope), "STEP_CHECK")

    def test_counts_are_exact_nonboolean_public_counts(self):
        for kind in KINDS:
            for value in (0, -1, True, None, "2", 50000):
                changed = deepcopy(self.envelope)
                changed["core"]["typed_vertex_counts"][kind] = value
                with self.subTest(kind=kind, value=value):
                    self.reject(rebind(changed), "counts")

    def test_core_integer_fields_do_not_coerce_bool_or_string(self):
        for field, values in (("skin", (-1, 2, True, "0", None)),
                              ("actual_route_depth", (-1, True, "2", None))):
            for value in values:
                changed = deepcopy(self.envelope)
                changed["core"][field] = value
                with self.subTest(field=field, value=value):
                    self.reject(rebind(changed), "skin|depth")

    def test_dense_public_graph_need_not_be_induced_or_contain_roots(self):
        public = self.envelope["core"]["public_graph"]
        public["vertices"] = [vertex for vertex in public["vertices"]
                              if vertex["alias"] in ("G0000", "Q0003", "S0000", "S0002")]
        self.envelope["public_to_world_aliases"] = {
            "G0000": "G0000", "Q0000": "Q0003", "S0000": "S0000", "S0001": "S0002",
        }
        world_to_public = {target: alias for alias, target in self.envelope["public_to_world_aliases"].items()}
        for vertex in public["vertices"]:
            vertex["alias"] = world_to_public[vertex["alias"]]
        public["edges"] = []
        self.envelope["core"].update(phase="SEEK", relevant_candidate_display_position=23,
                                     predicted_actual_match=None)
        self.envelope["step_outcome_observed"] = False
        result = checker.check_graph_core_json(encode(rebind(self.envelope, counts=True)))
        self.assertNotEqual(result["hashes"]["world_graph"], result["hashes"]["public_graph"])
        self.assertEqual(self.envelope["core"]["typed_vertex_counts"]["EVENT"], 0)
        self.assertEqual(self.envelope["radius_graphs"], self.vectors["HELD_TWO_STEP"]["radius_graphs"])

    def test_public_edge_and_vertex_must_exist_in_supplied_world(self):
        changed = deepcopy(self.envelope)
        public = changed["core"]["public_graph"]
        next(edge for edge in public["edges"] if edge["label"] == "WORLD")["heads"] = ["S0002"]
        sort_graph(public)
        self.reject(rebind(changed), "mapped edge incidence not in supplied world")
        self.envelope["core"]["public_graph"]["vertices"].append(
            {"alias": "S0003", "type": "STATE", "flags": []})
        self.envelope["public_to_world_aliases"]["S0003"] = "S0003"
        self.reject(rebind(self.envelope, counts=True), "existing world alias")

    def test_nonidentity_goal_map_and_per_graph_aliases_without_raw_subset(self):
        changed = with_hidden_prefixes(self.envelope, {
            "EVENT": 2, "GOAL": 12, "PORT": 3, "QUERY": 4, "RECEIPT": 5, "STATE": 6,
        })
        receipt = checker.check_graph_core_json(encode(changed))
        self.assertEqual(changed["public_to_world_aliases"]["G0000"], "G0012")
        self.assertEqual(changed["core"], self.envelope["core"])
        self.assertEqual(receipt["hashes"]["core"], self.envelope["expected_hashes"]["core"])
        self.assertEqual(receipt["hashes"]["public_graph"], self.envelope["expected_hashes"]["public_graph"])
        world_vertices = changed["world_graph"]["vertices"]
        self.assertNotIn({"alias": "G0000", "flags": ["GOAL"], "type": "GOAL"}, world_vertices)
        raw_world_edges = {encode(edge) for edge in changed["world_graph"]["edges"]}
        self.assertTrue(any(encode(edge) not in raw_world_edges
                            for edge in changed["core"]["public_graph"]["edges"]))
        self.assertEqual([vertex["alias"] for vertex in changed["radius_graphs"]["r0"]["vertices"]],
                         ["E0003", "P0004"])
        self.assertFalse(receipt["certifications"]["public_to_world_mapping_veracity"])

    def test_public_hashes_do_not_depend_on_hidden_world_ordinals(self):
        receipts = []
        for ordinal in (0, 12, 23):
            changed = with_hidden_prefixes(self.envelope, {"GOAL": ordinal})
            receipts.append(checker.check_graph_core_json(encode(changed)))
            self.assertEqual(changed["public_to_world_aliases"]["G0000"], f"G{ordinal:04d}")
            self.assertEqual(encode(changed["core"]), encode(self.envelope["core"]))
        for field in ("public_graph", "core"):
            self.assertEqual(len({receipt["hashes"][field] for receipt in receipts}), 1)
        self.assertEqual(len({receipt["hashes"]["world_graph"] for receipt in receipts}), 3)

    def test_sparse_public_aliases_rejected_even_with_consistent_map(self):
        for kind in KINDS:
            changed = with_hidden_prefixes(self.envelope, {kind: 12})
            translated = {alias: target if alias[0] == kind[0] else alias
                          for alias, target in changed["public_to_world_aliases"].items()}
            public = changed["core"]["public_graph"]
            for vertex in public["vertices"]:
                vertex["alias"] = translated[vertex["alias"]]
            for edge in public["edges"]:
                for side in ("heads", "tails"):
                    edge[side] = [translated[alias] for alias in edge[side]]
            changed["public_to_world_aliases"] = {
                translated[alias]: target for alias, target in changed["public_to_world_aliases"].items()
            }
            sort_graph(public)
            with self.subTest(kind=kind):
                self.reject(rebind(changed), "public_graph: aliases not contiguous from zero")

    def test_map_is_required_and_exactly_covers_public_vertices(self):
        for operation in ("absent", "missing", "extra"):
            changed = deepcopy(self.envelope)
            if operation == "absent":
                del changed["public_to_world_aliases"]
            elif operation == "missing":
                del changed["public_to_world_aliases"]["G0000"]
            else:
                changed["public_to_world_aliases"]["G0012"] = "G0000"
            with self.subTest(operation=operation):
                self.reject(changed, "keys")

    def test_map_container_and_target_types_fail_closed(self):
        for value in (None, [], "identity", True):
            changed = deepcopy(self.envelope)
            changed["public_to_world_aliases"] = value
            with self.subTest(map=value):
                self.reject(changed, "public_to_world_aliases: expected object")
        for value in (None, [], {}, True, 0, "G9999", "G12", "g0000"):
            changed = deepcopy(self.envelope)
            changed["public_to_world_aliases"]["G0000"] = value
            with self.subTest(target=value):
                self.reject(changed, "existing world alias")

    def test_map_duplicate_targets_rejected(self):
        self.envelope["public_to_world_aliases"]["Q0000"] = "Q0001"
        self.reject(self.envelope, "injective")

    def test_map_duplicate_json_keys_rejected(self):
        raw = encode(self.envelope)
        altered = raw.replace(b'"G0000":"G0000"', b'"G0000":"G0000","G0000":"G0000"')
        self.assertNotEqual(raw, altered)
        with self.assertRaisesRegex(checker.GraphCheckError, "duplicate object key"):
            checker.check_graph_core_json(altered)

    def test_map_wrong_vertex_type_rejected(self):
        self.envelope["public_to_world_aliases"]["E0000"] = "Q0000"
        self.reject(self.envelope, "vertex type mismatch")

    def test_map_flag_mismatches_rejected(self):
        offsets = {"EVENT": 2, "GOAL": 12, "PORT": 3, "STATE": 6}
        for alias in ("E0001", "G0000", "P0001", "S0000"):
            changed = with_hidden_prefixes(self.envelope, offsets)
            changed["public_to_world_aliases"][alias] = alias[0] + "0000"
            with self.subTest(alias=alias):
                self.reject(changed, "vertex/flags mismatch")

    def test_map_cannot_change_incidence_despite_matching_types_and_flags(self):
        for first, second in (("Q0000", "Q0001"), ("R0000", "R0001"), ("S0001", "S0002")):
            changed = deepcopy(self.envelope)
            mapping = changed["public_to_world_aliases"]
            mapping[first], mapping[second] = mapping[second], mapping[first]
            with self.subTest(aliases=(first, second)):
                self.reject(changed, "mapped edge incidence")

    def test_mapped_hyperedge_incidence_is_ordered(self):
        changed = with_hidden_prefixes(self.envelope, {"GOAL": 12, "STATE": 6})
        next(edge for edge in changed["core"]["public_graph"]["edges"]
             if edge["label"] == "INDEXES")["tails"].reverse()
        sort_graph(changed["core"]["public_graph"])
        self.reject(rebind(changed), "ordered incidence type")

    def test_mapping_is_input_bound_not_a_visibility_or_ownership_proof(self):
        changed = deepcopy(self.envelope)
        world = changed["world_graph"]
        world["vertices"].extend([
            {"alias": "Q0004", "flags": [], "type": "QUERY"},
            {"alias": "Q0005", "flags": [], "type": "QUERY"},
        ])
        sort_graph(world)
        public = changed["core"]["public_graph"]
        public["vertices"] = [vertex for vertex in public["vertices"]
                              if vertex["alias"] in ("G0000", "Q0000", "S0000")]
        public["edges"] = []
        changed["public_to_world_aliases"] = {"G0000": "G0000", "Q0000": "Q0004", "S0000": "S0000"}
        rebind(changed, counts=True)
        first = checker.check_graph_core_json(encode(changed))
        changed["public_to_world_aliases"]["Q0000"] = "Q0005"
        second = checker.check_graph_core_json(encode(changed))
        self.assertEqual(first["hashes"], second["hashes"])
        self.assertNotEqual(first["input_sha256"], second["input_sha256"])
        for field in ("public_to_world_mapping_veracity", "alias_role_ownership_and_order", "public_visibility"):
            self.assertIs(second["certifications"][field], False)
        self.assertTrue(all(value is False for value in second["science_gates"].values()))

    def test_radius_zero_preserves_nonzero_aliases(self):
        radius = self.envelope["radius_graphs"]["r0"]
        self.assertEqual([vertex["alias"] for vertex in radius["vertices"]], ["E0001", "P0001"])
        raw = encode(radius).replace(b"E0001", b"E0000").replace(b"P0001", b"P0000")
        self.envelope["radius_graphs"]["r0"] = json.loads(raw)
        self.reject(rebind(self.envelope), "preserved aliases")

    def test_each_radius_rejects_deleted_edge_even_with_rehashed_radius(self):
        for name in RADII:
            changed = deepcopy(self.envelope)
            changed["radius_graphs"][name]["edges"].pop()
            with self.subTest(radius=name):
                self.reject(rebind(changed), "induced graph")

    def test_hyperedge_clique_induction_and_self_loop(self):
        world = self.envelope["world_graph"]
        world["vertices"].extend([
            {"alias": "Q0004", "type": "QUERY", "flags": []},
            {"alias": "S0003", "type": "STATE", "flags": []},
            {"alias": "S0004", "type": "STATE", "flags": []},
            {"alias": "S0005", "type": "STATE", "flags": []},
        ])
        world["edges"].extend([
            {"tails": ["S0003", "P0001"], "heads": ["S0004"], "label": "WORLD"},
            {"tails": ["S0004", "G0000"], "heads": ["Q0004"], "label": "INDEXES"},
            {"tails": ["S0004", "P0000"], "heads": ["S0005"], "label": "WORLD"},
            {"tails": ["S0005", "P0000"], "heads": ["S0005"], "label": "WORLD"},
        ])
        sort_graph(world)
        rebind(self.envelope, derive_radii=True)
        checker.check_graph_core_json(encode(self.envelope))
        radius_one = self.envelope["radius_graphs"]["r1"]
        aliases = {vertex["alias"] for vertex in radius_one["vertices"]}
        self.assertTrue({"S0003", "S0004"} <= aliases)
        self.assertNotIn("Q0004", aliases)
        self.assertFalse(any(edge["heads"] == ["Q0004"] for edge in radius_one["edges"]))
        radius_two = self.envelope["radius_graphs"]["r2"]
        self.assertTrue(any(edge["heads"] == ["Q0004"] for edge in radius_two["edges"]))

    def test_allocated_isolated_vertices_remain_full_only(self):
        world = self.envelope["world_graph"]
        world["vertices"].append({"alias": "Q0004", "type": "QUERY", "flags": []})
        sort_graph(world)
        rebind(self.envelope, derive_radii=True)
        receipt = checker.check_graph_core_json(encode(self.envelope))
        self.assertEqual(receipt["hashes"]["radii"], self.vectors["HELD_TWO_STEP"]["expected_hashes"]["radii"])
        self.assertNotEqual(receipt["hashes"]["world_graph"], receipt["hashes"]["public_graph"])
        for radius in self.envelope["radius_graphs"].values():
            self.assertNotIn("Q0004", {vertex["alias"] for vertex in radius["vertices"]})

    def test_graph_resource_limits(self):
        with patch.object(checker, "MAX_EDGES", 1):
            self.reject(self.envelope, "size limit")
        with patch.object(checker, "MAX_VERTICES_PER_TYPE", 3):
            self.reject(self.envelope, "per-type limit")

    def test_actual_9999_vertex_per_type_boundary(self):
        world = self.envelope["world_graph"]
        world["vertices"].extend({"alias": f"Q{index:04d}", "flags": [], "type": "QUERY"}
                                 for index in range(4, 9999))
        sort_graph(world)
        checker.check_graph_core_json(encode(rebind(self.envelope)))
        world["vertices"].insert(-3, {"alias": "Q9999", "flags": [], "type": "QUERY"})
        sort_graph(world)
        self.reject(rebind(self.envelope), "per-type limit")

    def test_honest_limit_self_consistent_current_cannot_be_authenticated(self):
        for graph in (self.envelope["world_graph"], self.envelope["core"]["public_graph"]):
            for vertex in graph["vertices"]:
                if vertex["type"] == "STATE":
                    vertex["flags"] = ["CURRENT"] if vertex["alias"] == "S0002" else []
        receipt = checker.check_graph_core_json(encode(rebind(self.envelope, derive_radii=True)))
        self.assertIs(receipt["certifications"]["latest_current"], False)
        self.assertIs(receipt["certifications"]["provenance"], False)
        self.assertIs(receipt["science_gates"]["GO_CLAIM"], False)

    def test_receipts_are_detached_and_repeatable(self):
        raw = encode(self.envelope)
        first = checker.check_graph_core_json(raw)
        original = deepcopy(first)
        first["science_gates"]["GO_CLAIM"] = True
        first["hashes"]["radii"]["r0"] = "0" * 64
        self.assertEqual(checker.check_graph_core_json(raw), original)
        self.assertEqual(encode(self.envelope), raw)

    def test_checker_uses_only_declared_stdlib_imports_and_no_io(self):
        tree = ast.parse(Path(checker.__file__).read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                imports.append(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, ("open", "exec", "eval", "__import__"))
        self.assertEqual(set(imports), {"collections", "hashlib", "json", "re"})
        raw = encode(self.envelope)
        with patch("builtins.open", side_effect=AssertionError("filesystem forbidden")), \
                patch("pathlib.Path.open", side_effect=AssertionError("filesystem forbidden")), \
                patch("os.open", side_effect=AssertionError("filesystem forbidden")), \
                patch("socket.socket", side_effect=AssertionError("network forbidden")):
            receipt = checker.check_graph_core_json(raw)
        self.assertFalse(receipt["certifications"]["independent_scientific_checker"])


if __name__ == "__main__":
    unittest.main()
