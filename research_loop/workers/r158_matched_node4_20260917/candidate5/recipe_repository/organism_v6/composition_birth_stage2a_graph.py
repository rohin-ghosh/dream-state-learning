"""Partial Stage2A v4 typed-role graph source; synthetic CPU use only.

RoleVertex and RoleEdge accept explicit allocator ownership, not public IDs.
This module does not enumerate scientific worlds, infer public visibility,
choose the oracle root, apply interventions, or certify CURRENT against a
transcript. Callers own those facts. Radii preserve supplied full-world aliases.
Core match nullability requires explicit step_outcome_observed context; that
context is not added to the contract's hashed core. No readiness gate is opened.
"""

from collections import deque
from dataclasses import dataclass
from hashlib import sha256
import re
from types import MappingProxyType

from organism_v6.composition_birth_stage2a_primitives import (
    canonical_json,
    parse_canonical_json,
)


STATUS = "PARTIAL_SOURCE_ONLY"
MEMO_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"
GATES = MappingProxyType({name: False for name in (
    "GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU",
    "GO_CLAIM", "GO_SOURCE_READY",
)})
VERTEX_TYPES = ("EVENT", "GOAL", "PORT", "QUERY", "RECEIPT", "STATE")
MAX_VERTICES_PER_TYPE = 9999
PREFIXES = MappingProxyType(dict(zip(VERTEX_TYPES, "EGPQRS")))
ROLE_KINDS = MappingProxyType(dict(zip(
    VERTEX_TYPES, ("event", "node", "port", "query", "receipt", "node"),
)))
FLAG_TYPES = MappingProxyType({
    "CURRENT": "STATE", "GOAL": "GOAL", "ROOT_EVENT": "EVENT",
    "ROOT_PORT": "PORT",
})
INCIDENCE = MappingProxyType({
    "INDEXES": (("STATE", "GOAL"), ("QUERY",)),
    "CONTAINS": (("QUERY",), ("EVENT",)),
    "FOR": (("EVENT",), ("GOAL",)),
    "AT": (("EVENT",), ("STATE",)),
    "DID": (("EVENT",), ("PORT",)),
    "GOT": (("EVENT",), ("STATE",)),
    "RECOVER": (("EVENT",), ("QUERY",)),
    "EVIDENCE": (("EVENT",), ("RECEIPT",)),
    "WORLD": (("STATE", "PORT"), ("STATE",)),
})
CORE_ENUMS = MappingProxyType({
    "phase": ("SEEK", "PROSPECT", "READ_CHECK", "STEP_CHECK", "CONTINUE"),
    "flow": ("ORDINARY", "RECOVERY"),
    "recovery_subtype": (
        "NONE", "STRICT_MISS", "IRRELEVANT_RETURN", "STEP_OUTCOME_MISMATCH",
    ),
    "family_motif": ("A_PRIVATE_SPOKES", "B_BUCKET_MERGES", "C_CROSSING_WEAVE"),
    "goal_side": ("LEFT", "RIGHT"),
    "terminal_class": ("REACHED", "UNRESOLVED"),
})
CORE_KEYS = frozenset(CORE_ENUMS) | {
    "actual_route_depth", "predicted_actual_match", "public_graph",
    "relevant_candidate_display_position", "skin", "typed_vertex_counts",
}


@dataclass(frozen=True)
class RoleVertex:
    role_key: str
    vertex_type: str
    flags: tuple[str, ...] = ()

    @property
    def ref(self):
        return (self.role_key, self.vertex_type)


@dataclass(frozen=True)
class RoleEdge:
    label: str
    tails: tuple[tuple[str, str], ...]
    heads: tuple[tuple[str, str], ...]


def _sequence(value):
    if type(value) not in (tuple, list):
        raise ValueError("explicit_sequence_required")
    return value


def _enum(value, choices, name):
    if type(value) is not str or value not in choices:
        raise ValueError("invalid_" + name)


def local_owner_key(role_key, vertex_type):
    """Validate structural role syntax, not membership in a scientific inventory."""
    _enum(vertex_type, VERTEX_TYPES, "vertex_type")
    if type(role_key) is not str:
        raise ValueError("invalid_role_key")
    parts = role_key.split("/")
    if (len(parts) != 7
            or any(re.fullmatch(r"[!-~]+", part) is None for part in parts)
            or re.fullmatch(r"(?:0[0-9]|1[0-9]|2[0-3]|-)", parts[3]) is None
            or re.fullmatch(r"(?:[0-3]|-)", parts[5]) is None
            or parts[6] != ROLE_KINDS[vertex_type]):
        raise ValueError("invalid_role_key")
    return "/".join(parts[2:]) + "#" + vertex_type


def _flags(flags, vertex_type):
    flags = _sequence(flags)
    for flag in flags:
        _enum(flag, FLAG_TYPES, "flag")
        if FLAG_TYPES[flag] != vertex_type:
            raise ValueError("flag_type_mismatch")
    if len(set(flags)) != len(flags):
        raise ValueError("duplicate_flag")
    return sorted(flags)


def typed_aliases(vertices):
    """Map (full role key, type) references to local-owner-sorted aliases."""
    groups = {vertex_type: {} for vertex_type in VERTEX_TYPES}
    world = None
    seen_flags = set()
    for vertex in _sequence(vertices):
        if type(vertex) is not RoleVertex:
            raise ValueError("role_vertex_required")
        owner = local_owner_key(vertex.role_key, vertex.vertex_type)
        flags = _flags(vertex.flags, vertex.vertex_type)
        if seen_flags.intersection(flags):
            raise ValueError("duplicate_graph_flag")
        seen_flags.update(flags)
        identity = tuple(vertex.role_key.split("/")[:2])
        if world is not None and world != identity:
            raise ValueError("mixed_graph_worlds")
        world = identity
        group = groups[vertex.vertex_type]
        if owner in group:
            raise ValueError("duplicate_local_owner")
        group[owner] = vertex.ref
        if len(group) > MAX_VERTICES_PER_TYPE:
            raise ValueError("too_many_typed_vertices")
    return {group[owner]: PREFIXES[vertex_type] + f"{ordinal:04d}"
            for vertex_type, group in groups.items()
            for ordinal, owner in enumerate(sorted(group))}


def canonical_graph(vertices, edges):
    """Construct CJSON-ready graph from explicit typed owners and ordered edges."""
    aliases = typed_aliases(vertices)

    def resolve(incidence):
        result = []
        for reference in _sequence(incidence):
            if (type(reference) is not tuple or len(reference) != 2
                    or any(type(part) is not str for part in reference)
                    or reference not in aliases):
                raise ValueError("unknown_typed_reference")
            result.append(aliases[reference])
        return result

    graph_edges = []
    for edge in _sequence(edges):
        if type(edge) is not RoleEdge:
            raise ValueError("role_edge_required")
        _enum(edge.label, INCIDENCE, "edge_label")
        graph_edges.append({"heads": resolve(edge.heads), "label": edge.label,
                            "tails": resolve(edge.tails)})
    graph = {
        "edges": sorted(graph_edges, key=canonical_json),
        "vertices": sorted([
            {"alias": aliases[vertex.ref], "flags": _flags(vertex.flags, vertex.vertex_type),
             "type": vertex.vertex_type} for vertex in vertices
        ], key=lambda vertex: vertex["alias"]),
    }
    validate_graph(graph)
    return graph


def validate_graph(graph):
    """Check canonical typed shape; gaps in aliases are valid for induced graphs."""
    if type(graph) is not dict or set(graph) != {"edges", "vertices"}:
        raise ValueError("invalid_graph_keys")
    if type(graph["vertices"]) is not list or type(graph["edges"]) is not list:
        raise ValueError("graph_arrays_required")
    aliases = {}
    counts = dict.fromkeys(VERTEX_TYPES, 0)
    seen_flags = set()
    for vertex in graph["vertices"]:
        if type(vertex) is not dict or set(vertex) != {"alias", "flags", "type"}:
            raise ValueError("invalid_vertex_keys")
        vertex_type = vertex["type"]
        _enum(vertex_type, VERTEX_TYPES, "vertex_type")
        alias = vertex["alias"]
        if (type(alias) is not str
                or re.fullmatch(PREFIXES[vertex_type] + r"[0-9]{4}", alias) is None
                or int(alias[1:]) >= MAX_VERTICES_PER_TYPE):
            raise ValueError("invalid_typed_alias")
        if alias in aliases:
            raise ValueError("duplicate_alias")
        if type(vertex["flags"]) is not list:
            raise ValueError("flags_array_required")
        flags = _flags(vertex["flags"], vertex_type)
        if vertex["flags"] != flags:
            raise ValueError("unsorted_flags")
        if seen_flags.intersection(flags):
            raise ValueError("duplicate_graph_flag")
        seen_flags.update(flags)
        aliases[alias] = vertex_type
        counts[vertex_type] += 1
        if counts[vertex_type] > MAX_VERTICES_PER_TYPE:
            raise ValueError("too_many_typed_vertices")
    if list(aliases) != sorted(aliases):
        raise ValueError("unsorted_vertices")
    edge_bytes = []
    functional_heads = {}
    for edge in graph["edges"]:
        if type(edge) is not dict or set(edge) != {"heads", "label", "tails"}:
            raise ValueError("invalid_edge_keys")
        label = edge["label"]
        _enum(label, INCIDENCE, "edge_label")
        for side, required_types in zip(("tails", "heads"), INCIDENCE[label]):
            incidence = edge[side]
            if (type(incidence) is not list or len(incidence) != len(required_types)
                    or any(type(alias) is not str or alias not in aliases for alias in incidence)):
                raise ValueError("invalid_edge_incidence")
            if tuple(aliases[alias] for alias in incidence) != required_types:
                raise ValueError("edge_incidence_type_mismatch")
        if label not in ("INDEXES", "CONTAINS"):
            owner = (label, tuple(edge["tails"]))
            if owner in functional_heads and functional_heads[owner] != edge["heads"]:
                raise ValueError("conflicting_functional_edge")
            functional_heads[owner] = edge["heads"]
        edge_bytes.append(canonical_json(edge))
    if edge_bytes != sorted(edge_bytes):
        raise ValueError("unsorted_edges")
    if len(edge_bytes) != len(set(edge_bytes)):
        raise ValueError("duplicate_edge")
    return None


def graph_bytes(graph):
    validate_graph(graph)
    return canonical_json(graph)


def parse_graph(raw):
    graph = parse_canonical_json(raw)
    validate_graph(graph)
    return graph


def graph_hash(graph):
    return sha256(b"M2A-GRAPH-V3\0" + graph_bytes(graph)).hexdigest()


def typed_vertex_counts(graph):
    validate_graph(graph)
    return {vertex_type: sum(vertex["type"] == vertex_type for vertex in graph["vertices"])
            for vertex_type in VERTEX_TYPES}


def radius_graph(graph, radius):
    """Induce radius 0..3 by clique distance from the flagged EVENT/DID PORT."""
    validate_graph(graph)
    if type(radius) is not int or radius not in range(4):
        raise ValueError("invalid_radius")
    roots = {flag: vertex["alias"] for vertex in graph["vertices"]
             for flag in vertex["flags"] if flag in ("ROOT_EVENT", "ROOT_PORT")}
    if set(roots) != {"ROOT_EVENT", "ROOT_PORT"}:
        raise ValueError("exactly_two_typed_roots_required")
    if {"tails": [roots["ROOT_EVENT"]], "heads": [roots["ROOT_PORT"]],
            "label": "DID"} not in graph["edges"]:
        raise ValueError("roots_not_linked_by_did")
    neighbors = {vertex["alias"]: set() for vertex in graph["vertices"]}
    for edge in graph["edges"]:
        incident = set(edge["heads"] + edge["tails"])
        for alias in incident:
            neighbors[alias].update(incident - {alias})
    distances = dict.fromkeys(roots.values(), 0)
    queue = deque(distances)
    while queue:
        alias = queue.popleft()
        if distances[alias] == radius:
            continue
        for neighbor in neighbors[alias]:
            if neighbor not in distances:
                distances[neighbor] = distances[alias] + 1
                queue.append(neighbor)
    return {
        "edges": [{"heads": list(edge["heads"]), "label": edge["label"],
                   "tails": list(edge["tails"])} for edge in graph["edges"]
                  if all(alias in distances for alias in edge["heads"] + edge["tails"])],
        "vertices": [{"alias": vertex["alias"], "flags": list(vertex["flags"]),
                      "type": vertex["type"]} for vertex in graph["vertices"]
                     if vertex["alias"] in distances],
    }


def radius_bytes(graph, radius):
    return graph_bytes(radius_graph(graph, radius))


def radius_hash(graph, radius):
    raw = radius_bytes(graph, radius)
    return sha256(b"M2A-RADIUS-V3\0" + str(radius).encode("ascii") + b"\0" + raw).hexdigest()


def signature(graph):
    return {f"r{radius}": radius_hash(graph, radius) for radius in range(4)}


def signature_bytes(graph):
    return canonical_json(signature(graph))


def signature_hash(graph):
    return sha256(b"M2A-SIGNATURE-V3\0" + signature_bytes(graph)).hexdigest()


def validate_core(core, *, step_outcome_observed):
    """Validate core shape and nullability; do not infer context from phase alone."""
    if type(core) is not dict or set(core) != CORE_KEYS:
        raise ValueError("invalid_core_keys")
    for name, values in CORE_ENUMS.items():
        _enum(core[name], values, name)
    if type(step_outcome_observed) is not bool:
        raise ValueError("step_outcome_context_required")
    match = core["predicted_actual_match"]
    if (step_outcome_observed and type(match) is not bool
            or not step_outcome_observed and match is not None):
        raise ValueError("invalid_match_nullability")
    if core["phase"] == "STEP_CHECK" and not step_outcome_observed:
        raise ValueError("step_check_requires_outcome")
    position = core["relevant_candidate_display_position"]
    if core["phase"] in ("READ_CHECK", "CONTINUE"):
        if position is not None:
            raise ValueError("position_must_be_null")
    else:
        limit = 24 if core["phase"] == "SEEK" else 4
        if type(position) is not int or not 0 <= position < limit:
            raise ValueError("invalid_candidate_position")
    if type(core["actual_route_depth"]) is not int or core["actual_route_depth"] < 0:
        raise ValueError("invalid_route_depth")
    if type(core["skin"]) is not int or core["skin"] not in (0, 1):
        raise ValueError("invalid_skin")
    counts = typed_vertex_counts(core["public_graph"])
    given_counts = core["typed_vertex_counts"]
    if (type(given_counts) is not dict or set(given_counts) != set(VERTEX_TYPES)
            or any(type(count) is not int for count in given_counts.values())
            or given_counts != counts):
        raise ValueError("invalid_public_vertex_counts")
    flags = {flag for vertex in core["public_graph"]["vertices"] for flag in vertex["flags"]}
    if not {"CURRENT", "GOAL"} <= flags:
        raise ValueError("public_task_flags_required")


def decision_core(public_graph, *, actual_route_depth, family_motif, flow, goal_side,
                  phase, predicted_actual_match, recovery_subtype,
                  relevant_candidate_display_position, skin, terminal_class,
                  step_outcome_observed):
    """Build exact v4 core; counts include only the caller's public graph."""
    core = {
        "actual_route_depth": actual_route_depth, "family_motif": family_motif,
        "flow": flow, "goal_side": goal_side, "phase": phase,
        "predicted_actual_match": predicted_actual_match,
        "public_graph": parse_graph(graph_bytes(public_graph)),
        "recovery_subtype": recovery_subtype,
        "relevant_candidate_display_position": relevant_candidate_display_position,
        "skin": skin, "terminal_class": terminal_class,
        "typed_vertex_counts": typed_vertex_counts(public_graph),
    }
    validate_core(core, step_outcome_observed=step_outcome_observed)
    return core


def core_bytes(core, *, step_outcome_observed):
    validate_core(core, step_outcome_observed=step_outcome_observed)
    return canonical_json(core)


def core_hash(core, *, step_outcome_observed):
    return sha256(b"M2A-CORE-V3\0" + core_bytes(
        core, step_outcome_observed=step_outcome_observed,
    )).hexdigest()
