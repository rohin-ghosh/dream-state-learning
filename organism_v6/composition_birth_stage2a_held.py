"""Source-only held constructions over explicit, complete per-world role tokens.

Implements v4 with v3 sections 4/5 and the prospective Builder clarification.
No allocation, materialization, training, runtime scheduling, or scoring gates.
Witnesses and semantic objects are evaluator-only; public views omit both.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from hashlib import sha256
import re
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_worlds as worlds


STATUS = "PARTIAL_SOURCE_ONLY"
MEMO_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"
ROUTE_CORRIGENDUM_SHA256 = "6ebefdba31de6f14416105c9509dbba06319f306bdd3472259a8d072ba9877e7"
CLARIFICATION_SHA256 = "5484567fdad924247c5371a7430a071c925c563b5375336e8bef86dc6a4a99f9"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(wire.SCIENCE_GATES, False))
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
TRANSITIONS = ("seek", "prospect", "check", "continue")


def _integer(value, upper, name):
    if type(value) is not int or not 0 <= value < upper:
        raise ValueError("invalid_" + name)
    return value


def _token(value, kind):
    if (type(value) is not str or re.fullmatch(wire.IDENTIFIERS[kind], value) is None
            or value.endswith("_AAAAAAAAAAAA")):
        raise ValueError("invalid_" + kind + "_token")
    return value


def _freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _task_text(task):
    raw = f"TASK\nSTART {task.start}\nGOAL {task.goal}\nCURRENT {task.current}"
    wire.parse_task(raw)
    return raw


def _command(action):
    return action.operation + (" " + action.verb if action.verb else "")


def intervention_pins(transition, pair_index):
    """Return two (display position, semantic goal) pins; never retry/rotate."""
    if type(transition) is not str or transition not in TRANSITIONS:
        raise ValueError("invalid_transition")
    _integer(pair_index, 8, "pair_index")
    number = TRANSITIONS.index(transition)
    first = (3 * pair_index + number) % 24
    return ((first, (3 * pair_index + number) % 12),
            ((first + 12) % 24, 12 + (5 * pair_index + number) % 12))


def _directory_order(pins):
    positions = [position for position, goal in pins]
    goals = [goal for position, goal in pins]
    for position, goal in pins:
        _integer(position, 24, "route_position")
        _integer(goal, 24, "goal_index")
    if len(set(positions)) != len(positions) or len(set(goals)) != len(goals):
        raise ValueError("conflicting_directory_pin")
    pinned = dict(pins)
    remaining = iter(goal for goal in range(24) if goal not in goals)
    return tuple(pinned[position] if position in pinned else next(remaining)
                 for position in range(24))


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class ExpectedTarget:
    bytes: str
    command: str
    operand: str | None
    sha256: str


def _target(raw):
    action = wire.parse_action(raw)
    return ExpectedTarget(raw, _command(action), action.operand,
                          sha256(raw.encode("ascii")).hexdigest())


@dataclass(frozen=True)
class PublicView:
    """Host-side service facade; only prefixes and requested replies are public.

    The registry is internal, enumerable host state, not an actor prompt or
    parent-safe serialized object. No world edges or evaluator answers appear
    in the actor-message prefix.
    """

    task: wire.TaskState
    prefix: tuple[Message, ...]
    registry: Mapping
    status: str = STATUS

    def read(self, request):
        if wire.parse_action(request).operation != "READ":
            raise ValueError("unsupported_service_request")
        return self.registry.get(request, "MISS")


@dataclass(frozen=True)
class OutcomeIntervention:
    kind: str
    outcome_destination: str | None

    def __post_init__(self):
        if self.kind == "IDENTITY":
            if self.outcome_destination is not None:
                raise ValueError("identity_has_no_destination")
        elif self.kind == "OUTCOME_DESTINATION":
            _token(self.outcome_destination, "node")
        else:
            raise ValueError("invalid_intervention_kind")


@dataclass(frozen=True)
class OutcomeReceipt:
    current: str
    port: str
    base_destination: str
    outcome_destination: str


@dataclass(frozen=True)
class EffectiveStep:
    destination: str
    receipt: OutcomeReceipt | None
    world_message: str


@dataclass(frozen=True)
class InterventionMember:
    transition_name: str
    pair_index: int
    member: str
    construction: worlds.OrdinaryConstruction
    task: wire.TaskState
    intervention: OutcomeIntervention
    selected_event: wire.EventRow
    alternate_destination: str
    expected_target: ExpectedTarget
    expected_causal_prefix: tuple[Message, ...]
    semantic_object: Mapping
    status: str = STATUS

    def __post_init__(self):
        if self.member not in ("m0", "m1"):
            raise ValueError("invalid_member")
        if type(self.intervention) is not OutcomeIntervention:
            raise ValueError("typed_intervention_required")
        if self.transition_name == "check":
            destination = (self.selected_event.got if self.member == "m0"
                           else self.alternate_destination)
            if self.intervention != OutcomeIntervention("OUTCOME_DESTINATION", destination):
                raise ValueError("unbound_check_outcome")
        elif self.intervention != OutcomeIntervention("IDENTITY", None):
            raise ValueError("outcome_override_outside_check")

    @property
    def registry(self):
        return self.construction.registry

    @property
    def world_edges(self):
        return self.construction.world_edges

    def read(self, request):
        return self.construction.read(request)

    def transition(self, current, port):
        """Fixed base-world transition; CHECK never modifies this mapping."""
        return self.construction.transition(current, port)

    def execute_step(self, current, port):
        """Construct evaluator receipt before the public scalar WORLD payload."""
        destination = self.transition(current, port)
        receipt = None
        if (self.intervention.kind == "OUTCOME_DESTINATION"
                and (current, port) == (self.task.start, self.selected_event.port)):
            receipt = OutcomeReceipt(current, port, destination,
                                     self.intervention.outcome_destination)
            destination = receipt.outcome_destination
        return EffectiveStep(destination, receipt, "WORLD\nCURRENT " + destination)

    def effective_transition(self, current, port):
        return self.execute_step(current, port).destination

    def public_view(self):
        return PublicView(self.task, self.expected_causal_prefix, self.registry)


@dataclass(frozen=True)
class InterventionPair:
    world: str
    members: tuple[InterventionMember, InterventionMember]
    allowed_differences: frozenset[str]
    status: str = STATUS
    memo_sha256: str = MEMO_SHA256
    clarification_sha256: str = CLARIFICATION_SHA256


class _Context:
    """Bounded held-only builder for contexts unsupported by ordinary worlds."""

    def __init__(self, domain, world, role_tokens):
        if type(world) is not str:
            raise ValueError("invalid_world")
        self.domain, self.world = domain, world
        if domain == "dose_intervention" and re.fullmatch(
                r"(?:seek|prospect|check|continue)_k[0-7]", world):
            self.index = int(world[-1])
            self.transition_name = world.split("_")[0]
            self.skin = self.index // 4
            self.rotation = (5 * self.index + 3 * TRANSITIONS.index(self.transition_name) + 1) % 8
            self.states = ("s",)
            self.scored = tuple(goal for position, goal in
                                intervention_pins(self.transition_name, self.index))
            self.mismatch = False
        elif domain == "dose_chain" and re.fullmatch(r"h(?:0[0-9]|1[0-5])", world):
            self.index = int(world[1:])
            self.transition_name = None
            self.skin = self.index // 8
            self.rotation = (3 * self.index + 1) % 8
            self.states = ("s",) + tuple(f"h{hub:02d}" for hub in range(8))
            self.scored = tuple(goal for goal, slot in worlds.chain_scored_positions(world))
            self.mismatch = bool((self.index // 4) % 2)
        else:
            raise ValueError("unbound_held_world")
        if not isinstance(role_tokens, Mapping):
            raise ValueError("explicit_role_token_mapping_required")
        self.tokens = dict(role_tokens)
        expected = self._roles()
        if any(type(role) is not str for role in self.tokens):
            raise ValueError("invalid_role_key")
        missing, extra = expected - self.tokens.keys(), self.tokens.keys() - expected
        if missing or extra:
            raise ValueError("per_world_roles_mismatch:" + str((sorted(missing), sorted(extra))))
        seen = set()
        for role, token in self.tokens.items():
            _token(token, role.rsplit("/", 1)[1])
            if token in seen:
                raise ValueError("duplicate_opaque_token")
            seen.add(token)

    def _role(self, state, goal, block, candidate, kind):
        return "/".join((self.domain, self.world, state, goal, block, candidate, kind))

    def _roles(self):
        roles = set()
        nodes = (("s",) + tuple(f"{prefix}{goal:02d}" for prefix in ("g", "x")
                               for goal in range(24))
                 + tuple(f"{prefix}{hub:02d}" for prefix in ("h", "w") for hub in range(8)))
        for state in nodes:
            roles.add(self._role(state, "-" if state == "s" else state[1:], "state", "-", "node"))
        for state in self.states:
            for goal in range(24):
                goal_text = f"{goal:02d}"
                roles.add(self._role(state, goal_text, "index", "-", "route"))
                roles.add(self._role(state, goal_text, "useful", "-", "query"))
                self._row_roles(roles, state, goal_text, "useful", "recover")
        if self.mismatch:
            for member, goal in enumerate(self.scored):
                self._row_roles(roles, self.surprise(goal), f"{goal:02d}",
                                f"recovery_m{member}", f"recover2_m{member}")
        return roles

    def _row_roles(self, roles, state, goal, block, recover):
        for candidate in range(4):
            for kind in ("event", "port", "receipt"):
                roles.add(self._role(state, goal, block, str(candidate), kind))
            roles.add(self._role(state, goal, recover, str(candidate), "query"))

    def lookup(self, state, goal, block, candidate, kind):
        return self.tokens[self._role(state, goal, block, candidate, kind)]

    def node(self, state):
        return self.lookup(state, "-" if state == "s" else state[1:], "state", "-", "node")

    def predicted(self, goal):
        return f"h{(5 * goal + self.rotation) % 8:02d}"

    def surprise(self, goal):
        return f"w{(7 * goal + self.rotation) % 8:02d}"

    def query(self, state, goal):
        return self.lookup(state, f"{goal:02d}", "useful", "-", "query")

    def block(self, kind, rows):
        return wire.parse_service(worlds.render_service(kind, rows, skin=self.skin), skin=self.skin)

    def directory(self, state):
        if self.domain == "dose_intervention":
            pins = intervention_pins(self.transition_name, self.index)
        else:
            pins = []
            for member, goal in enumerate(self.scored):
                position = 6 * (self.index % 4) + 3 * member
                if state == "s" or state == self.predicted(goal):
                    pins.append((position if state == "s" else (position + 12) % 24, goal))
        rows = tuple(wire.RouteRow(
            self.lookup(state, f"{goal:02d}", "index", "-", "route"),
            self.node(state), self.node(f"g{goal:02d}"), self.query(state, goal))
            for goal in _directory_order(pins))
        return "READ INDEX " + self.node(state), self.block("ROUTES", rows)

    def relation(self, state, goal, *, corrective_member=None):
        ordinal = 0 if state == "s" else (100 if state[0] == "h" else 108) + int(state[1:])
        slot = (3 * goal + ordinal + self.skin) % 4
        if self.domain == "dose_chain" and state == "s" and goal in self.scored:
            slot = (self.index + self.scored.index(goal)) % 4
        if self.domain == "dose_intervention" and goal in self.scored:
            slot = self.index % 4
        next_goal = (goal + 1) % 24
        pattern = ((state, goal), (state, next_goal),
                   (f"x{goal:02d}", goal), (f"x{next_goal:02d}", (goal + 2) % 24))
        if self.transition_name == "prospect" and goal == self.scored[0]:
            pattern = ((state, goal), (f"x{goal:02d}", goal),
                       (state, self.scored[1]), (f"x{next_goal:02d}", (goal + 2) % 24))
        block = "useful" if corrective_member is None else f"recovery_m{corrective_member}"
        recover = "recover" if corrective_member is None else f"recover2_m{corrective_member}"
        rows = [None] * 4
        for offset, (at_state, for_goal) in enumerate(pattern):
            candidate = str((slot + offset) % 4)
            if at_state.startswith("x"):
                destination = f"x{(int(at_state[1:]) + 3) % 24:02d}"
            else:
                destination = self.predicted(for_goal) if state == "s" else f"g{for_goal:02d}"
            rows[int(candidate)] = wire.EventRow(
                self.lookup(state, f"{goal:02d}", block, candidate, "event"), self.node(at_state),
                self.node(f"g{for_goal:02d}"), self.lookup(state, f"{goal:02d}", block, candidate, "port"),
                self.node(destination), self.lookup(state, f"{goal:02d}", recover, candidate, "query"),
                self.lookup(state, f"{goal:02d}", block, candidate, "receipt"))
        return self.block("EVENTS", rows)

    def construction(self, blocks, *, overrides=None, scope):
        entries = dict(blocks)
        if len(entries) != len(blocks):
            raise ValueError("duplicate_service_key")
        edges = {}
        ports = set()
        for block in entries.values():
            if block.kind == "EVENTS":
                for row in block.rows:
                    if row.port in ports:
                        raise ValueError("duplicate_world_port")
                    ports.add(row.port)
                    edges[row.node, row.port] = row.got
        for key, destination in (overrides or {}).items():
            if key not in edges:
                raise ValueError("override_has_no_base_edge")
            edges[key] = destination
        return worlds.OrdinaryConstruction(
            self.domain, self.world, self.skin, scope, MappingProxyType(entries),
            MappingProxyType({request: block.raw for request, block in entries.items()}),
            MappingProxyType(edges))


def build_intervention_directory(*, world, role_tokens):
    context = _Context("dose_intervention", world, role_tokens)
    return context.construction([context.directory("s")], scope="HELD_DIRECTORY_FRAGMENT")


def _matching(block, current, goal):
    rows = tuple(row for row in block.rows if row.node == current and row.goal == goal)
    if len(rows) != 1:
        raise ValueError("unique_relevant_row_required")
    return rows[0]


def _initial_prefix(task):
    return (Message("system", wire.SYSTEM_MESSAGE), Message("user", _task_text(task)))


def _read_prefix(prefix, construction, request):
    return prefix + (Message("assistant", request), Message("user", "SERVICE\n" + construction.read(request)))


def _row_object(row):
    if type(row) is wire.RouteRow:
        return dict(route=row.route, at=row.node, **{"for": row.goal}, query=row.query)
    return dict(event=row.event, at=row.node, **{"for": row.goal}, did=row.port, got=row.got,
                recover=row.recover, evidence=row.receipt)


def _semantic_object(context, construction, task, target, intervention, current):
    """Keep service payloads single-owned; causal wire prefixes are derived views."""
    return _freeze(dict(
        evaluator=dict(answer=target.bytes),
        intervention=dict(kind=intervention.kind, outcome_destination=intervention.outcome_destination),
        service=dict(
            relation_blocks=[dict(rows=[_row_object(row) for row in construction.blocks[
                "READ RELATION " + context.query("s", goal)].rows]) for goal in range(24)],
            route_rows=[_row_object(row) for row in construction.blocks["READ INDEX " + task.start].rows]),
        task=dict(start=task.start, goal=task.goal, current=task.current),
        target=dict(bytes=target.bytes, command=target.command, operand=target.operand, sha256=target.sha256),
        transcript=dict(world=dict(current=current)),
        world=dict(edges=[dict(at=node, did=port, destination=destination)
                          for (node, port), destination in sorted(construction.world_edges.items())])))


def allowed_intervention_differences(transition, pair_index):
    pins = intervention_pins(transition, pair_index)
    common = {"/evaluator/answer", "/target/bytes", "/target/sha256"}
    if transition == "seek":
        common.update(("/task/goal", "/target/operand"))
    elif transition == "prospect":
        common.add("/target/operand")
        for slot in (pair_index % 4, (pair_index + 2) % 4):
            common.add(f"/service/relation_blocks/{pins[0][1]}/rows/{slot}/for")
    elif transition == "check":
        common.update(("/intervention/outcome_destination", "/target/command", "/transcript/world/current"))
    else:
        common.update(("/task/goal", "/target/command", "/target/operand"))
    return frozenset(common)


def leaf_differences(left, right, path=""):
    """Exact RFC-6901 scalar diffs, rejecting changed object/array structure."""
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if left.keys() != right.keys():
            raise ValueError("paired_object_keys_changed")
        differences = set()
        for key in left:
            if type(key) is not str:
                raise ValueError("json_pointer_string_keys_required")
            escaped = key.replace("~", "~0").replace("/", "~1")
            differences.update(leaf_differences(left[key], right[key], path + "/" + escaped))
        return frozenset(differences)
    if isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
        if len(left) != len(right):
            raise ValueError("paired_array_length_changed")
        differences = set()
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            differences.update(leaf_differences(left_item, right_item, path + "/" + str(index)))
        return frozenset(differences)
    if isinstance(left, (Mapping, tuple, list)) or isinstance(right, (Mapping, tuple, list)):
        raise ValueError("paired_container_type_changed")
    return frozenset((path,)) if type(left) is not type(right) or left != right else frozenset()


def build_intervention_pair(*, world, role_tokens):
    """Build one of the exact 32 pairs, two members sharing base-world edges."""
    context = _Context("dose_intervention", world, role_tokens)
    transition = context.transition_name
    start = context.node("s")
    blocks = [context.directory("s")]
    blocks.extend(("READ RELATION " + context.query("s", goal), context.relation("s", goal))
                  for goal in range(24))
    base = context.construction(blocks, scope="HELD_INTERVENTION_WORLD")
    members = []
    for member_index in range(2):
        construction = base
        goal_index = context.scored[member_index if transition == "seek" else 0]
        goal = context.node(f"g{goal_index:02d}")
        if transition == "continue" and member_index == 0:
            goal = start
        task = wire.TaskState(start, goal, start)
        request = "READ RELATION " + context.query("s", goal_index)
        if transition == "prospect" and member_index == 1:
            rows = list(base.blocks[request].rows)
            first, second = context.index % 4, (context.index + 2) % 4
            rows[first], rows[second] = (replace(rows[first], goal=rows[second].goal),
                                         replace(rows[second], goal=rows[first].goal))
            changed = dict(base.blocks)
            changed[request] = context.block("EVENTS", rows)
            construction = context.construction(list(changed.items()), scope="HELD_INTERVENTION_WORLD")
            if construction.world_edges != base.world_edges:
                raise ValueError("prospect_changed_base_world")
        selected = _matching(construction.blocks[request], start, context.node(f"g{goal_index:02d}"))
        prefix = _initial_prefix(task)
        current = None
        intervention = OutcomeIntervention("IDENTITY", None)
        if transition != "continue":
            prefix = _read_prefix(prefix, construction, "READ INDEX " + start)
        if transition in ("prospect", "check"):
            prefix = _read_prefix(prefix, construction, request)
        if transition == "seek":
            target = _target(request)
        elif transition == "prospect":
            target = _target("STEP " + selected.port)
        elif transition == "check":
            current = selected.got if member_index == 0 else context.node(context.surprise(goal_index))
            intervention = OutcomeIntervention("OUTCOME_DESTINATION", current)
            prefix += (Message("assistant", "STEP " + selected.port),
                       Message("user", "WORLD\nCURRENT " + current))
            target = _target("THINK " + ("KEEP " if member_index == 0 else "REVISE ") + selected.event)
        else:
            target = _target("STOP" if member_index == 0 else "READ INDEX " + start)
        members.append(InterventionMember(
            transition, context.index, f"m{member_index}", construction, task, intervention, selected,
            context.node(context.surprise(goal_index)), target, prefix,
            _semantic_object(context, construction, task, target, intervention, current)))
    allowed = allowed_intervention_differences(transition, context.index)
    if leaf_differences(members[0].semantic_object, members[1].semantic_object) != allowed:
        raise ValueError("intervention_leaf_allowlist_mismatch")
    return InterventionPair(world, tuple(members), allowed)


def _panel_tokens(role_tokens_by_world, names):
    if not isinstance(role_tokens_by_world, Mapping) or set(role_tokens_by_world) != set(names):
        raise ValueError("explicit_exact_panel_world_mappings_required")
    seen = set()
    for name in names:
        tokens = role_tokens_by_world[name]
        if not isinstance(tokens, Mapping):
            raise ValueError("explicit_role_token_mapping_required")
        for token in tokens.values():
            if type(token) is not str:
                raise ValueError("invalid_panel_token")
            if token in seen:
                raise ValueError("panel_token_collision")
            seen.add(token)


def build_intervention_panel(*, role_tokens_by_world):
    names = tuple(f"{transition}_k{index}" for transition in TRANSITIONS for index in range(8))
    _panel_tokens(role_tokens_by_world, names)
    return tuple(build_intervention_pair(world=name, role_tokens=role_tokens_by_world[name]) for name in names)


@dataclass(frozen=True)
class WitnessTurn:
    action: str
    current_before: str
    current_after: str
    response: str | None


@dataclass(frozen=True)
class ChainMember:
    member: str
    task: wire.TaskState
    expected_trace: tuple[WitnessTurn, ...]
    sufficient_reads: frozenset[str]
    status: str = STATUS


@dataclass(frozen=True)
class ChainWorld:
    construction: worlds.OrdinaryConstruction
    members: tuple[ChainMember, ChainMember]
    mismatch: bool
    skin: int
    status: str = STATUS
    memo_sha256: str = MEMO_SHA256
    clarification_sha256: str = CLARIFICATION_SHA256

    @property
    def world(self):
        return self.construction.world

    @property
    def registry(self):
        return self.construction.registry

    @property
    def world_edges(self):
        return self.construction.world_edges

    def read(self, request):
        return self.construction.read(request)

    def transition(self, current, port):
        return self.construction.transition(current, port)

    def public_view(self, member):
        if type(member) is not str or member not in ("m0", "m1"):
            raise ValueError("invalid_member")
        task = self.members[int(member[1:])].task
        return PublicView(task, _initial_prefix(task), self.registry)


def _chain_witness(construction, task):
    """Offline evaluator witness from public rows/outcomes, never a host policy."""
    current = task.current
    turns = []

    def read(request):
        raw = construction.read(request)
        turns.append(WitnessTurn(request, current, current, "SERVICE\n" + raw))
        return wire.parse_service(raw, skin=construction.skin)

    directory = read("READ INDEX " + current)
    route = _matching(directory, current, task.goal)
    block = read("READ RELATION " + route.query)
    first = _matching(block, current, task.goal)
    destination = construction.transition(current, first.port)
    turns.append(WitnessTurn("STEP " + first.port, current, destination, "WORLD\nCURRENT " + destination))
    current = destination
    matched = current == first.got
    turns.append(WitnessTurn("THINK " + ("KEEP " if matched else "REVISE ") + first.event,
                             current, current, "ACK"))
    if matched:
        directory = read("READ INDEX " + current)
        route = _matching(directory, current, task.goal)
        block = read("READ RELATION " + route.query)
    else:
        block = read("READ RELATION " + first.recover)
    second = _matching(block, current, task.goal)
    destination = construction.transition(current, second.port)
    if destination != task.goal or current == task.goal:
        raise ValueError("chain_witness_not_two_step")
    turns.append(WitnessTurn("STEP " + second.port, current, destination, "WORLD\nCURRENT " + destination))
    turns.append(WitnessTurn("STOP", destination, destination, None))
    return tuple(turns)


def build_chain_world(*, world, role_tokens):
    """Construct every ordinary block plus only the two bound mismatch recoveries."""
    context = _Context("dose_chain", world, role_tokens)
    blocks = []
    for state in context.states:
        blocks.append(context.directory(state))
        blocks.extend(("READ RELATION " + context.query(state, goal), context.relation(state, goal))
                      for goal in range(24))
    overrides = {}
    if context.mismatch:
        entries = dict(blocks)
        for member, goal in enumerate(context.scored):
            first = _matching(entries["READ RELATION " + context.query("s", goal)],
                              context.node("s"), context.node(f"g{goal:02d}"))
            surprise = context.surprise(goal)
            overrides[first.node, first.port] = context.node(surprise)
            blocks.append(("READ RELATION " + first.recover,
                           context.relation(surprise, goal, corrective_member=member)))
    construction = context.construction(blocks, overrides=overrides, scope="HELD_CHAIN_WORLD")
    members = []
    for member, goal in enumerate(context.scored):
        task = wire.TaskState(context.node("s"), context.node(f"g{goal:02d}"), context.node("s"))
        trace = _chain_witness(construction, task)
        members.append(ChainMember(f"m{member}", task, trace,
                                   frozenset(turn.action for turn in trace if turn.action.startswith("READ "))))
    return ChainWorld(construction, tuple(members), context.mismatch, context.skin)


def build_chain_panel(*, role_tokens_by_world):
    names = tuple(f"h{index:02d}" for index in range(16))
    _panel_tokens(role_tokens_by_world, names)
    return tuple(build_chain_world(world=name, role_tokens=role_tokens_by_world[name]) for name in names)
