"""Partial v4 ordinary construction over caller-supplied opaque tokens only.

Complete worlds cover ordinary goal-switch birth roots and expected chains.
Intervention support is limited to nondesignated ordinary relation blocks.
Recovery, relation pairs, intervention objects, nulls, graphs, scoring, and
scientific materialization are not implemented. No allocation is performed.
Birth directory ordering requires explicit display-master bytes; there is no
canonical master default. All returned registries and edges are immutable.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import re
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire


MEMO_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"
STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(wire.SCIENCE_GATES, False))
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
_PREFIXES = MappingProxyType(dict(node="N", query="Q", event="E", route="I",
                                  port="P", receipt="R"))
_TRANSITIONS = ("seek", "prospect", "check", "continue")


class UnsupportedConstructionError(ValueError):
    """The requested contract slice has deliberately not been implemented."""


def _integer(value, upper, name):
    if type(value) is not int or not 0 <= value < upper:
        raise ValueError("invalid_" + name)
    return value


def _token(value, kind):
    if (type(value) is not str
            or re.fullmatch(rf"M2A{_PREFIXES[kind]}_[A-Z2-7]{{12}}", value) is None
            or value.endswith("_AAAAAAAAAAAA")):
        raise ValueError("invalid_" + kind + "_token")
    return value


def _world_index(domain, world):
    if type(domain) is not str or type(world) is not str:
        raise ValueError("invalid_world")
    if domain == "birth_train" and re.fullmatch(r"p(?:[0-2][0-9]|3[01])", world):
        return int(world[1:])
    if domain == "dose_chain" and re.fullmatch(r"h(?:0[0-9]|1[0-5])", world):
        return int(world[1:])
    if domain == "dose_intervention" and re.fullmatch(r"(?:seek|prospect|check|continue)_k[0-7]", world):
        return int(world[-1])
    raise ValueError("unbound_domain_or_world")


def chain_scored_positions(world):
    """V4 section 3: two (semantic goal, rendered first-hop row) pairs."""
    index = _world_index("dose_chain", world)
    return (((5 * index) % 12, index % 4),
            (12 + (7 * index) % 12, (index + 1) % 4))


def state_ordinal(domain, world, state_role):
    """Ordinals for the ordinary INDEX states; corrective states fail closed."""
    index = _world_index(domain, world)
    if type(state_role) is not str:
        raise ValueError("invalid_state_role")
    if state_role == "s":
        return 0
    if domain == "birth_train":
        if index % 4 < 2 and re.fullmatch(r"a(?:[01][0-9]|2[0-3])", state_role):
            return int(state_role[1:]) + 1
        if index % 4 >= 2 and re.fullmatch(r"b0[0-5]", state_role):
            return 25 + int(state_role[1:])
    if domain == "dose_chain" and re.fullmatch(r"h0[0-7]", state_role):
        return 100 + int(state_role[1:])
    if state_role.startswith(("surp_", "w")):
        raise UnsupportedConstructionError("corrective_state_not_implemented")
    raise ValueError("state_has_no_ordinary_index")


def render_service(kind, rows, *, skin):
    """Render exact v2 service bytes, validating without normalizing inputs."""
    _integer(skin, 2, "skin")
    if type(rows) not in (tuple, list):
        raise ValueError("rows_require_sequence")
    if kind == "MISS" and not rows:
        return "MISS"
    if kind == "ROUTES":
        row_type, count = wire.RouteRow, 24
        layout = (("ROUTE", "route"), ("AT", "node"), ("FOR", "goal"), ("QUERY", "query"))
        if skin:
            layout = (layout[0], layout[2], layout[3], layout[1])
    elif kind == "EVENTS":
        row_type, count = wire.EventRow, 4
        layout = (("EVENT", "event"), ("AT", "node"), ("FOR", "goal"),
                  ("DID", "port"), ("GOT", "got"), ("RECOVER", "recover"),
                  ("EVIDENCE", "receipt"))
        if skin:
            layout = (layout[0], layout[2], layout[1], layout[4], layout[3], layout[5], layout[6])
    else:
        raise ValueError("invalid_service_kind")
    if len(rows) != count or any(type(row) is not row_type for row in rows):
        raise ValueError("invalid_service_rows")
    aliases = {"goal": "node", "got": "node", "recover": "query"}
    lines = [kind]
    for row in rows:
        values = []
        for label, field in layout:
            values.extend((label, _token(getattr(row, field), aliases.get(field, field))))
        lines.append(" ".join(values))
    raw = "\n".join(lines)
    wire.parse_service(raw, skin=skin)
    return raw


@dataclass(frozen=True)
class OrdinaryConstruction:
    domain: str
    world: str
    skin: int
    scope: str
    blocks: Mapping
    registry: Mapping
    world_edges: Mapping
    status: str = STATUS
    memo_sha256: str = MEMO_SHA256

    def read(self, request):
        action = wire.parse_action(request)
        if action.operation != "READ":
            raise ValueError("unsupported_service_request")
        return self.registry.get(request, "MISS")

    def transition(self, current, port):
        key = (_token(current, "node"), _token(port, "port"))
        if key not in self.world_edges:
            raise ValueError("invalid_step")
        return self.world_edges[key]


class _Context:
    def __init__(self, domain, world, role_tokens):
        self.index = _world_index(domain, world)
        self.domain, self.world = domain, world
        if domain == "birth_train":
            if self.index % 2:
                raise UnsupportedConstructionError("birth_recovery_not_implemented")
            if self.index >= 16:
                raise UnsupportedConstructionError("birth_relation_pair_not_implemented")
            self.skin = (self.index // 8) % 2
            self.family = "a" if self.index % 4 < 2 else "b"
            self.states = ("s",) + tuple(f"{self.family}{hub:02d}" for hub in
                                         range(24 if self.family == "a" else 6))
            self.rotation = None
        else:
            self.family = "c"
            if domain == "dose_chain":
                if (self.index // 4) % 2:
                    raise UnsupportedConstructionError("chain_mismatch_recovery_not_implemented")
                self.skin = self.index // 8
                self.rotation = (3 * self.index + 1) % 8
                self.states = ("s",) + tuple(f"h{hub:02d}" for hub in range(8))
            else:
                self.skin = self.index // 4
                transition = _TRANSITIONS.index(world.split("_")[0])
                self.rotation = (5 * self.index + 3 * transition + 1) % 8
                self.states = ("s",)
        if not isinstance(role_tokens, Mapping):
            raise ValueError("explicit_role_token_mapping_required")
        self.tokens = dict(role_tokens)
        seen = set()
        for role, token in self.tokens.items():
            if type(role) is not str:
                raise ValueError("invalid_role_key")
            parts = role.split("/")
            if (len(parts) != 7 or parts[:2] != [domain, world]
                    or parts[-1] not in _PREFIXES or not self._valid_role(parts)):
                raise ValueError("invalid_role_key:" + role)
            _token(token, parts[-1])
            if token in seen:
                raise ValueError("duplicate_opaque_token")
            seen.add(token)

    def _valid_role(self, parts):
        state, goal, block, candidate, kind = parts[2:]
        if kind == "node":
            if block != "state" or candidate != "-":
                return False
            if state == "s":
                return goal == "-"
            if re.fullmatch(r"(?:g|x)(?:[01][0-9]|2[0-3])", state):
                return goal == state[1:]
            if self.family == "c" and re.fullmatch(r"[hw]0[0-7]", state):
                return goal == state[1:]
            return state in self.states[1:] and goal == state[1:]
        if state not in self.states or re.fullmatch(r"(?:[01][0-9]|2[0-3])", goal) is None:
            return False
        return ((block, candidate, kind) in (("index", "-", "route"), ("useful", "-", "query"))
                or candidate in ("0", "1", "2", "3") and
                ((block == "recover" and kind == "query")
                 or (block == "useful" and kind in ("event", "port", "receipt"))))

    def lookup(self, state, goal, block, candidate, kind):
        role = "/".join((self.domain, self.world, state, goal, block, candidate, kind))
        if role not in self.tokens:
            raise ValueError("missing_role:" + role)
        return self.tokens[role]

    def node(self, state):
        return self.lookup(state, "-" if state == "s" else state[1:], "state", "-", "node")

    def relation(self, state, goal_index):
        _integer(goal_index, 24, "goal_index")
        ordinal = state_ordinal(self.domain, self.world, state)
        if self.domain == "dose_intervention":
            transition = _TRANSITIONS.index(self.world.split("_")[0])
            designated = ((3 * self.index + transition) % 12,
                          12 + (5 * self.index + transition) % 12)
            if goal_index in designated:
                raise UnsupportedConstructionError("intervention_designated_block_not_implemented")
        slot = (3 * goal_index + ordinal + self.skin) % 4
        if self.domain == "dose_chain" and state == "s":
            slot = dict(chain_scored_positions(self.world)).get(goal_index, slot)
        next_goal = (goal_index + 1) % 24
        pattern = ((state, goal_index), (state, next_goal),
                   (f"x{goal_index:02d}", goal_index), (f"x{next_goal:02d}", (goal_index + 2) % 24))
        rows = [None] * 4
        for offset, (at_state, for_goal) in enumerate(pattern):
            candidate = str((slot + offset) % 4)
            goal = f"{goal_index:02d}"
            if at_state.startswith("x"):
                destination = f"x{(int(at_state[1:]) + 3) % 24:02d}"
            elif state != "s":
                destination = f"g{for_goal:02d}"
            elif self.family == "c":
                destination = f"h{(5 * for_goal + self.rotation) % 8:02d}"
            elif (self.index // 4) % 2:
                destination = f"{self.family}{for_goal if self.family == 'a' else for_goal % 6:02d}"
            else:
                destination = f"g{for_goal:02d}"
            rows[int(candidate)] = wire.EventRow(
                self.lookup(state, goal, "useful", candidate, "event"),
                self.node(at_state), self.node(f"g{for_goal:02d}"),
                self.lookup(state, goal, "useful", candidate, "port"), self.node(destination),
                self.lookup(state, goal, "recover", candidate, "query"),
                self.lookup(state, goal, "useful", candidate, "receipt"))
        request = "READ RELATION " + self.lookup(state, f"{goal_index:02d}", "useful", "-", "query")
        return request, wire.parse_service(render_service("EVENTS", rows, skin=self.skin), skin=self.skin)

    def directory(self, state, display_master):
        state_ordinal(self.domain, self.world, state)
        if self.domain == "dose_intervention":
            raise UnsupportedConstructionError("intervention_directory_not_implemented:v3_section_4.3")
        if self.domain == "birth_train":
            if type(display_master) is not bytes:
                raise ValueError("explicit_display_master_bytes_required")
            template = f"goal/{self.index // 4}/{self.family.upper()}/{state}/index".encode("ascii")
            order = sorted(range(24), key=lambda goal: (
                sha256(display_master + b"\x00display-order\x00" + template + b"\x00"
                       + goal.to_bytes(4, "big")).digest(), goal))
        else:
            if display_master is not None:
                raise ValueError("chain_display_master_not_used")
            pins = {}
            for member, (goal, unused_slot) in enumerate(chain_scored_positions(self.world)):
                position = 6 * (self.index % 4) + 3 * member
                hub = f"h{(5 * goal + self.rotation) % 8:02d}"
                if state == "s" or state == hub:
                    position = position if state == "s" else (position + 12) % 24
                    if position in pins or goal in pins.values():
                        raise ValueError("conflicting_directory_pin")
                    pins[position] = goal
            remaining = iter(goal for goal in range(24) if goal not in pins.values())
            order = [pins[position] if position in pins else next(remaining) for position in range(24)]
        rows = tuple(wire.RouteRow(self.lookup(state, f"{goal:02d}", "index", "-", "route"),
                                   self.node(state), self.node(f"g{goal:02d}"),
                                   self.lookup(state, f"{goal:02d}", "useful", "-", "query"))
                     for goal in order)
        request = "READ INDEX " + self.node(state)
        return request, wire.parse_service(render_service("ROUTES", rows, skin=self.skin), skin=self.skin)

    def result(self, blocks, scope):
        entries = dict(blocks)
        edges = {}
        ports = set()
        for block in entries.values():
            if block.kind == "EVENTS":
                for row in block.rows:
                    if row.port in ports:
                        raise ValueError("duplicate_world_port")
                    ports.add(row.port)
                    edges[row.node, row.port] = row.got
        return OrdinaryConstruction(self.domain, self.world, self.skin, scope,
                                    MappingProxyType(entries),
                                    MappingProxyType({key: block.raw for key, block in entries.items()}),
                                    MappingProxyType(edges))


def build_ordinary_relation(*, domain, world, state_role, goal_index, role_tokens):
    """Build one ordinary relation and its four fixed edges, not a full world."""
    context = _Context(domain, world, role_tokens)
    return context.result((context.relation(state_role, goal_index),), "ORDINARY_RELATION_FRAGMENT")


def build_ordinary_directory(*, domain, world, state_role, role_tokens, display_master=None):
    """Build one INDEX block; referenced relation blocks are not constructed."""
    context = _Context(domain, world, role_tokens)
    return context.result((context.directory(state_role, display_master),), "ORDINARY_DIRECTORY_FRAGMENT")


def build_ordinary_world(*, domain, world, role_tokens, display_master=None):
    """Construct all Z directories, useful blocks, and edges for supported worlds."""
    context = _Context(domain, world, role_tokens)
    if domain == "dose_intervention":
        raise UnsupportedConstructionError("intervention_pair_world_not_implemented")
    if domain == "dose_chain":
        for hub in range(8):
            context.node(f"w{hub:02d}")
    blocks = []
    for state in context.states:
        blocks.append(context.directory(state, display_master))
        blocks.extend(context.relation(state, goal) for goal in range(24))
    return context.result(blocks, "ORDINARY_WORLD_ONLY")


def build_recovery(*args, **kwargs):
    raise UnsupportedConstructionError("recovery_not_implemented:v4_section_2")


def build_pair(*args, **kwargs):
    raise UnsupportedConstructionError("pairs_not_implemented")


def build_null(*args, **kwargs):
    raise UnsupportedConstructionError("nulls_not_implemented")
