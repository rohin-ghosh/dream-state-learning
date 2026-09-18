"""Independent, in-memory Stage-2A v4 *partial* graph/core JSON checker.

Authority: adopted binding successor v4, SHA-256 CONTRACT_SHA256, importing
v3 sections 2 and 7 with v4 section 4 corrections. No producer code is used.

API: check_graph_core_json(payload: bytes) -> dict; malformed or inconsistent
input raises GraphCheckError. canonical_json_bytes(value) is a restricted
stdlib-only transport encoder, not a role canonicalizer or graph generator.

Exact v2 envelope (every object rejects missing/extra keys):
  {"schema_version": "M2A-PARTIAL-GRAPH-CHECK-V2",
   "world_graph": Graph, "core": Core, "step_outcome_observed": bool,
   "public_to_world_aliases": {PublicAlias: WorldAlias, ...},
   "radius_graphs": {"r0": Graph, "r1": Graph, "r2": Graph, "r3": Graph},
   "expected_hashes": {"world_graph": Hex, "public_graph": Hex,
                       "radii": {"r0": Hex, "r1": Hex, "r2": Hex, "r3": Hex},
                       "signature": Hex, "core": Hex}}
Hex is exactly 64 lowercase hexadecimal characters. Graph is exactly
  {"edges": [{"heads": [Alias], "label": Label, "tails": [Alias, ...]}, ...],
   "vertices": [{"alias": Alias, "flags": [Flag, ...], "type": Type}, ...]}.
Types, flags and ordered label incidence are the finite tables below. Aliases
are E/G/P/Q/R/S plus four decimal digits, consistent with their vertex type.
World and decision/public aliases must EACH be zero-based and contiguous within
each type (v3 section 7.2). Only radius graphs keep world aliases, including gaps
(v3 section 7.3). Vertices, flags, and edges must already be sorted and unique.
Full world roots are unique and joined by DID. World and public graphs each
have one CURRENT and GOAL. public_to_world_aliases is an exact object with one
key for every public alias and no other keys; values are existing world aliases
and must be injective. Each mapped vertex must have the same type and flags.
Every public edge, with ordered incidence translated through the map, must
exist in the world. No literal public/world alias equality is assumed. Public
graphs need NOT be induced: omitted edges may represent unobserved facts.
Radii are induced from the full world, never from the public graph.

V1 envelopes are explicitly rejected, not reinterpreted; historical receipts
are not upgraded. Graph/core/radius/signature hash domains and preimages are
unchanged. The map is bound by the receipt's input_sha256, not incorporated
into graph or core hashes. Its role/visibility truth remains a caller assertion.

Core has exactly actual_route_depth, family_motif, flow, goal_side, phase,
predicted_actual_match, public_graph, recovery_subtype,
relevant_candidate_display_position, skin, terminal_class, typed_vertex_counts.
Enums are exactly ENUMS below; skin is integer 0/1; route depth is a nonnegative
integer (no shortest-path assertion). Counts contain all six type keys and
count public vertices only. Position is integer 0..23 for SEEK, 0..3 for
PROSPECT/STEP_CHECK, otherwise null. Match is bool iff the caller declares
step_outcome_observed, and null otherwise; STEP_CHECK requires that declaration
to be true. This checks declared-context consistency, not whether an outcome
actually occurred.

Transport bounds (resource limits, not scientific contract amendments): bytes
only, at most 32 MiB, nesting at most 32, signed 63-bit magnitude integers,
at most 9,999 vertices/type and 500,000 edges/graph. Restricted CJSON permits
only exact built-in dict/list/str/int/bool/None values, ASCII strings without
CR/NUL, no floats/nonfinite constants/negative zero/duplicate keys. Input must
equal its canonical encoding, including key order, escaping, and no final LF.

Success is only PARTIAL_GRAPH_CHECK_ONLY. Expected hashes and supplied world
facts and alias mapping are caller assertions, not authenticated commitments.
Dense alias syntax does not prove local-owner ordering or mapping veracity.
This cannot prove role ownership/order, world completeness, latest CURRENT, oracle root choice,
public visibility, targets, nulls, provenance/contamination, held separation,
or scientific validity. Self-consistent replacement inputs can pass. No
filesystem, material-root, model, tokenizer, network, or GPU access occurs.
"""

from collections import deque
from hashlib import sha256
import json
import re


CONTRACT_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"
SCHEMA_VERSION = "M2A-PARTIAL-GRAPH-CHECK-V2"
STATUS = "PARTIAL_GRAPH_CHECK_ONLY"
MAX_BYTES = 32 * 1024 * 1024
MAX_DEPTH = 32
MAX_INTEGER = (1 << 63) - 1
MAX_VERTICES_PER_TYPE = 9999
MAX_EDGES = 500000

TYPE_PREFIXES = {
    "EVENT": "E", "GOAL": "G", "PORT": "P", "QUERY": "Q",
    "RECEIPT": "R", "STATE": "S",
}
FLAG_TYPES = {
    "CURRENT": "STATE", "GOAL": "GOAL",
    "ROOT_EVENT": "EVENT", "ROOT_PORT": "PORT",
}
INCIDENCE = {
    "INDEXES": (("STATE", "GOAL"), ("QUERY",)),
    "CONTAINS": (("QUERY",), ("EVENT",)),
    "FOR": (("EVENT",), ("GOAL",)),
    "AT": (("EVENT",), ("STATE",)),
    "DID": (("EVENT",), ("PORT",)),
    "GOT": (("EVENT",), ("STATE",)),
    "RECOVER": (("EVENT",), ("QUERY",)),
    "EVIDENCE": (("EVENT",), ("RECEIPT",)),
    "WORLD": (("STATE", "PORT"), ("STATE",)),
}
ENUMS = {
    "phase": ("SEEK", "PROSPECT", "READ_CHECK", "STEP_CHECK", "CONTINUE"),
    "flow": ("ORDINARY", "RECOVERY"),
    "recovery_subtype": (
        "NONE", "STRICT_MISS", "IRRELEVANT_RETURN", "STEP_OUTCOME_MISMATCH",
    ),
    "family_motif": ("A_PRIVATE_SPOKES", "B_BUCKET_MERGES", "C_CROSSING_WEAVE"),
    "goal_side": ("LEFT", "RIGHT"),
    "terminal_class": ("REACHED", "UNRESOLVED"),
}
CORE_KEYS = set(ENUMS) | {
    "actual_route_depth", "predicted_actual_match", "public_graph",
    "relevant_candidate_display_position", "skin", "typed_vertex_counts",
}
RADIUS_KEYS = ("r0", "r1", "r2", "r3")
SCIENCE_GATES = (
    "GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU",
    "GO_CLAIM",
)
UNCERTIFIED = (
    "alias_role_ownership_and_order", "world_completeness", "public_visibility",
    "latest_current", "oracle_root_choice", "targets", "nulls", "provenance",
    "contamination", "train_held_separation", "step_outcome_context",
    "public_to_world_mapping_veracity", "independent_scientific_checker",
)


class GraphCheckError(ValueError):
    """A bounded partial-check schema, canonicalization, or consistency failure."""


def _require(condition, message):
    if not condition:
        raise GraphCheckError(message)


def _keys(value, expected, location):
    _require(type(value) is dict, f"{location}: expected object")
    _require(set(value) == set(expected), f"{location}: incorrect keys")


def _restricted(value, depth=0):
    _require(depth <= MAX_DEPTH, "CJSON: nesting limit exceeded")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        _require(abs(value) <= MAX_INTEGER, "CJSON: integer limit exceeded")
    elif type(value) is str:
        _require(value.isascii() and "\r" not in value and "\0" not in value,
                 "CJSON: non-ASCII, CR or NUL string")
    elif type(value) is list:
        for item in value:
            _restricted(item, depth + 1)
    elif type(value) is dict:
        for key, item in value.items():
            _require(type(key) is str, "CJSON: object key must be a string")
            _restricted(key, depth + 1)
            _restricted(item, depth + 1)
    else:
        raise GraphCheckError("CJSON: unsupported value type")


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def canonical_json_bytes(value):
    """Encode restricted JSON; reject unsupported types rather than coerce them."""
    _restricted(value)
    encoded = _encode(value)
    _require(len(encoded) <= MAX_BYTES, "CJSON: byte limit exceeded")
    return encoded


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "CJSON: duplicate object key")
        result[key] = value
    return result


def _integer(token):
    _require(token != "-0", "CJSON: negative zero")
    _require(len(token.lstrip("-")) <= 19, "CJSON: integer limit exceeded")
    value = int(token)
    _require(abs(value) <= MAX_INTEGER, "CJSON: integer limit exceeded")
    return value


def _no_float(token):
    raise GraphCheckError("CJSON: float or nonfinite constant forbidden")


def loads_canonical_json(payload):
    """Decode only byte-exact restricted CJSON, with pre-parse resource bounds."""
    _require(type(payload) is bytes, "CJSON: input must be bytes")
    _require(len(payload) <= MAX_BYTES, "CJSON: byte limit exceeded")
    _require(payload.isascii() and b"\r" not in payload and b"\0" not in payload,
             "CJSON: non-ASCII/invalid UTF-8, CR or NUL bytes")
    depth = 0
    in_string = False
    escaped = False
    for character in payload:
        if in_string:
            if escaped:
                escaped = False
            elif character == 92:
                escaped = True
            elif character == 34:
                in_string = False
        elif character == 34:
            in_string = True
        elif character in (91, 123):
            depth += 1
            _require(depth <= MAX_DEPTH, "CJSON: nesting limit exceeded")
        elif character in (93, 125):
            depth -= 1
    try:
        value = json.loads(payload, object_pairs_hook=_object_pairs,
                           parse_int=_integer, parse_float=_no_float,
                           parse_constant=_no_float)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise GraphCheckError("CJSON: malformed JSON") from error
    _restricted(value)
    _require(_encode(value) == payload, "CJSON: input is not canonical")
    return value


def _graph(graph, location, *, full=False, decision=False):
    _keys(graph, ("edges", "vertices"), location)
    vertices = graph["vertices"]
    edges = graph["edges"]
    _require(type(vertices) is list and type(edges) is list,
             f"{location}: vertices/edges must be arrays")
    _require(len(vertices) <= 6 * MAX_VERTICES_PER_TYPE and len(edges) <= MAX_EDGES,
             f"{location}: graph size limit exceeded")
    by_alias = {}
    typed = {kind: [] for kind in TYPE_PREFIXES}
    flagged = {flag: [] for flag in FLAG_TYPES}
    for vertex in vertices:
        _keys(vertex, ("alias", "flags", "type"), location + ".vertex")
        kind, alias, flags = vertex["type"], vertex["alias"], vertex["flags"]
        _require(type(kind) is str and kind in TYPE_PREFIXES,
                 f"{location}: unknown vertex type")
        _require(type(alias) is str and re.fullmatch(TYPE_PREFIXES[kind] + r"[0-9]{4}", alias),
                 f"{location}: invalid typed alias")
        _require(alias not in by_alias, f"{location}: duplicate alias")
        _require(type(flags) is list, f"{location}: flags must be array")
        for flag in flags:
            _require(type(flag) is str and FLAG_TYPES.get(flag) == kind,
                     f"{location}: invalid typed flag")
            flagged[flag].append(alias)
        _require(flags == sorted(set(flags)), f"{location}: flags not sorted/unique")
        typed[kind].append(alias)
        by_alias[alias] = vertex
    _require(list(by_alias) == sorted(by_alias), f"{location}: vertices not sorted")
    for kind, aliases in typed.items():
        _require(len(aliases) <= MAX_VERTICES_PER_TYPE, f"{location}: per-type limit exceeded")
        if full or decision:
            _require(aliases == [f"{TYPE_PREFIXES[kind]}{index:04d}"
                                 for index in range(len(aliases))],
                     f"{location}: aliases not contiguous from zero")
    for flag, aliases in flagged.items():
        required = (decision and flag in ("CURRENT", "GOAL")) or (
            full and flag in ("ROOT_EVENT", "ROOT_PORT"))
        _require(len(aliases) == 1 if required else len(aliases) <= 1,
                 f"{location}: incorrect {flag} count")
    encoded_edges = []
    functional = set()
    for edge in edges:
        _keys(edge, ("heads", "label", "tails"), location + ".edge")
        label = edge["label"]
        _require(type(label) is str and label in INCIDENCE,
                 f"{location}: unknown edge label")
        for side, kinds in zip(("tails", "heads"), INCIDENCE[label]):
            incidence = edge[side]
            _require(type(incidence) is list and len(incidence) == len(kinds),
                     f"{location}: incorrect edge arity")
            for alias, kind in zip(incidence, kinds):
                _require(type(alias) is str and alias in by_alias,
                         f"{location}: dangling edge alias")
                _require(by_alias[alias]["type"] == kind,
                         f"{location}: incorrect ordered incidence type")
        if label not in ("INDEXES", "CONTAINS"):
            key = (label, tuple(edge["tails"]))
            _require(key not in functional, f"{location}: multiple functional edge heads")
            functional.add(key)
        encoded_edges.append(_encode(edge))
    _require(encoded_edges == sorted(set(encoded_edges)),
             f"{location}: edges not sorted/unique")
    if full:
        root_did = {"heads": flagged["ROOT_PORT"], "label": "DID",
                    "tails": flagged["ROOT_EVENT"]}
        _require(_encode(root_did) in set(encoded_edges),
                 f"{location}: root EVENT must DID root PORT")
    return by_alias, {kind: len(aliases) for kind, aliases in typed.items()}


def _core(core, step_outcome_observed):
    _keys(core, CORE_KEYS, "core")
    for field, choices in ENUMS.items():
        _require(type(core[field]) is str and core[field] in choices,
                 f"core: invalid {field} enum")
    _require(type(core["skin"]) is int and core["skin"] in (0, 1), "core: invalid skin")
    depth = core["actual_route_depth"]
    _require(type(depth) is int and depth >= 0, "core: invalid route depth")
    position = core["relevant_candidate_display_position"]
    phase = core["phase"]
    limit = {"SEEK": 24, "PROSPECT": 4, "STEP_CHECK": 4}.get(phase)
    _require(position is None if limit is None else
             type(position) is int and 0 <= position < limit,
             "core: invalid position/nullability")
    match = core["predicted_actual_match"]
    _require(match is None or type(match) is bool, "core: match must be bool/null")
    _require(type(step_outcome_observed) is bool,
             "core: step_outcome_observed must be bool")
    _require(type(match) is bool if step_outcome_observed else match is None,
             "core: match inconsistent with declared STEP outcome context")
    if phase == "STEP_CHECK":
        _require(step_outcome_observed, "core: STEP_CHECK requires STEP outcome context")
    by_alias, counts = _graph(core["public_graph"], "public_graph", decision=True)
    _keys(core["typed_vertex_counts"], TYPE_PREFIXES, "core.typed_vertex_counts")
    for kind, count in core["typed_vertex_counts"].items():
        _require(type(count) is int and count == counts[kind],
                 "core: typed counts must count public vertices")
    return by_alias


def _radii(world):
    neighbors = {vertex["alias"]: set() for vertex in world["vertices"]}
    roots = []
    for vertex in world["vertices"]:
        if "ROOT_EVENT" in vertex["flags"] or "ROOT_PORT" in vertex["flags"]:
            roots.append(vertex["alias"])
    for edge in world["edges"]:
        incident = set(edge["tails"] + edge["heads"])
        for alias in incident:
            neighbors[alias].update(incident - {alias})
    distances = dict.fromkeys(roots, 0)
    queue = deque(roots)
    while queue:
        alias = queue.popleft()
        if distances[alias] == 3:
            continue
        for neighbor in neighbors[alias]:
            if neighbor not in distances:
                distances[neighbor] = distances[alias] + 1
                queue.append(neighbor)
    result = {}
    for radius in range(4):
        keep = {alias for alias, distance in distances.items() if distance <= radius}
        result[f"r{radius}"] = {
            "edges": [edge for edge in world["edges"]
                      if all(alias in keep for alias in edge["tails"] + edge["heads"])],
            "vertices": [vertex for vertex in world["vertices"] if vertex["alias"] in keep],
        }
    return result


def _hash(domain, value):
    return sha256(domain + b"\0" + _encode(value)).hexdigest()


def check_graph_core_json(payload):
    """Verify an exact envelope; return a partial-only receipt, never a gate."""
    envelope = loads_canonical_json(payload)
    _require(type(envelope) is dict, "envelope: expected object")
    _require(envelope.get("schema_version") != "M2A-PARTIAL-GRAPH-CHECK-V1",
             "envelope: schema version V1 unsupported; V2 requires explicit "
             "public_to_world_aliases and independently dense public aliases")
    _keys(envelope, ("schema_version", "world_graph", "core", "radius_graphs",
                     "expected_hashes", "step_outcome_observed",
                     "public_to_world_aliases"), "envelope")
    _require(envelope["schema_version"] == SCHEMA_VERSION, "envelope: wrong schema version")
    expected = envelope["expected_hashes"]
    _keys(expected, ("world_graph", "public_graph", "radii", "signature", "core"),
          "expected_hashes")
    _keys(expected["radii"], RADIUS_KEYS, "expected_hashes.radii")
    digests = [expected[field] for field in ("world_graph", "public_graph", "signature", "core")]
    for digest in digests + list(expected["radii"].values()):
        _require(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest),
                 "expected_hashes: invalid lowercase SHA-256")
    world = envelope["world_graph"]
    world_vertices, _ = _graph(world, "world_graph", full=True, decision=True)
    public_vertices = _core(envelope["core"], envelope["step_outcome_observed"])
    alias_map = envelope["public_to_world_aliases"]
    _keys(alias_map, public_vertices, "public_to_world_aliases")
    mapped_aliases = set()
    for alias, vertex in public_vertices.items():
        target = alias_map[alias]
        _require(type(target) is str and target in world_vertices,
                 "public_to_world_aliases: target must be an existing world alias")
        _require(target not in mapped_aliases, "public_to_world_aliases: map must be injective")
        mapped_aliases.add(target)
        _require(world_vertices[target]["type"] == vertex["type"],
                 "public_to_world_aliases: vertex type mismatch")
        _require(world_vertices[target]["flags"] == vertex["flags"],
                 "public_to_world_aliases: vertex/flags mismatch")
    world_edges = {_encode(edge) for edge in world["edges"]}
    public = envelope["core"]["public_graph"]
    for edge in public["edges"]:
        mapped_edge = {
            "heads": [alias_map[alias] for alias in edge["heads"]],
            "label": edge["label"],
            "tails": [alias_map[alias] for alias in edge["tails"]],
        }
        _require(_encode(mapped_edge) in world_edges,
                 "public_graph: mapped edge incidence not in supplied world")
    _keys(envelope["radius_graphs"], RADIUS_KEYS, "radius_graphs")
    radii = _radii(world)
    for name in RADIUS_KEYS:
        candidate = envelope["radius_graphs"][name]
        _graph(candidate, "radius_graphs." + name)
        _require(_encode(candidate) == _encode(radii[name]),
                 f"radius_graphs.{name}: not full-world induced graph with preserved aliases")
    radius_hashes = {
        name: _hash(b"M2A-RADIUS-V3\0" + name[1:].encode("ascii"), radii[name])
        for name in RADIUS_KEYS
    }
    hashes = {
        "world_graph": _hash(b"M2A-GRAPH-V3", world),
        "public_graph": _hash(b"M2A-GRAPH-V3", public),
        "radii": radius_hashes,
        "signature": _hash(b"M2A-SIGNATURE-V3", radius_hashes),
        "core": _hash(b"M2A-CORE-V3", envelope["core"]),
    }
    for field in hashes:
        _require(hashes[field] == expected[field], f"expected_hashes: {field} mismatch")
    return {
        "status": STATUS,
        "graph_checks_passed": True,
        "schema_version": SCHEMA_VERSION,
        "contract_sha256": CONTRACT_SHA256,
        "input_sha256": sha256(payload).hexdigest(),
        "hashes": hashes,
        "science_gates": dict.fromkeys(SCIENCE_GATES, False),
        "certifications": dict.fromkeys(UNCERTIFIED, False),
    }
