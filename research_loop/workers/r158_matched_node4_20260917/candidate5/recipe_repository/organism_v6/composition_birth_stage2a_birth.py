"""Partial v4 birth construction, case metadata, and four-target CPU oracles.

Inputs are explicit per-world opaque bindings and display-master bytes. No
allocation, tokenizer, presentation tape, fitting, or material output exists.
All 64 birth cases are constructed, including strict MISS, irrelevant returns,
v4 mismatch recovery, and relation pairs with the explicitly clarified A/B
encoding. Recovery relation pairs swap FOR only in the shared recovery_m0.
Trace turns are expected public facts, not model executions or loss masks.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from functools import lru_cache
from hashlib import sha256
import re
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_worlds as worlds


MEMO_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"
CLARIFICATION_PATH = "research_notes/analysis/2026-09-13_stage2a_builder_source_clarifications_v1.md"
CLARIFICATION_SHA256 = "5484567fdad924247c5371a7430a071c925c563b5375336e8bef86dc6a4a99f9"
STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(wire.SCIENCE_GATES, False))
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
_MISMATCH = frozenset((1, 3, 5, 7, 25, 27, 29, 31))
_STRICT_MISS = frozenset((9, 13, 19, 23))
_IRRELEVANT = frozenset((11, 15, 17, 21))
_PREFIXES = MappingProxyType(dict(node="N", query="Q", event="E", route="I",
                                  port="P", receipt="R"))
FAMILY_BITS = MappingProxyType({"A": 0, "B": 1})


@dataclass(frozen=True)
class BirthCaseDescriptor:
    world: str
    member: str
    pair_index: int
    bucket: int
    pair_type: str
    family: str
    family_motif: str
    flow: str
    recovery_subtype: str
    terminal_class: str
    goal_side: str
    goal_index: int
    skin: int
    recovery_match_id: tuple | None
    domain: str = "birth_train"

    @property
    def case_id(self):
        return self.world, self.member

    @property
    def family_bit(self):
        return FAMILY_BITS[self.family]

    @property
    def relation_slot(self):
        return (3 * self.bucket + self.family_bit) % 4 if self.pair_type == "relation" else None


def describe_birth_case(world, member):
    """V2 section 4 metadata only; no IDs, units, or presentation ordering."""
    if type(world) is not str or re.fullmatch(r"p(?:[0-2][0-9]|3[01])", world) is None:
        raise worlds.UnsupportedConstructionError("unsupported_birth_world")
    if type(member) is not str or member not in ("m0", "m1"):
        raise ValueError("invalid_birth_member")
    pair = int(world[1:])
    bucket = pair // 4
    family = "A" if pair % 4 < 2 else "B"
    side = int(member[1:]) if pair < 16 else bucket % 2
    subtype = ("STEP_OUTCOME_MISMATCH" if pair in _MISMATCH else
               "STRICT_MISS" if pair in _STRICT_MISS else
               "IRRELEVANT_RETURN" if pair in _IRRELEVANT else "NONE")
    return BirthCaseDescriptor(
        world, member, pair, bucket, "goal" if pair < 16 else "relation", family,
        "A_PRIVATE_SPOKES" if family == "A" else "B_BUCKET_MERGES",
        "RECOVERY" if pair % 2 else "ORDINARY", subtype,
        "REACHED" if bucket % 2 == 0 else "UNRESOLVED", "LEFT" if side == 0 else "RIGHT",
        (5 * bucket) % 12 if side == 0 else 12 + (7 * bucket) % 12,
        (bucket // 2) % 2, (f"p{pair - 1:02d}", member) if pair % 2 else None)


def enumerate_birth_cases():
    return tuple(describe_birth_case(f"p{pair:02d}", f"m{member}")
                 for pair in range(32) for member in range(2))


@lru_cache(maxsize=1)
def _role_inventory():
    inventory = wire.enumerate_symbolic_role_inventory("birth_train")
    grouped = {f"p{pair:02d}": [] for pair in range(32)}
    for roles in inventory.roles_by_kind.values():
        for role in roles:
            grouped[role.split("/")[1]].append(role)
    return MappingProxyType({world: tuple(sorted(roles)) for world, roles in grouped.items()})


def required_birth_roles(world):
    """Return the unchanged v3 symbolic role keys, without allocating tokens."""
    describe_birth_case(world, "m0")
    return _role_inventory()[world]


def _bindings(world, role_tokens):
    if not isinstance(role_tokens, Mapping):
        raise ValueError("explicit_role_token_mapping_required")
    copied = dict(role_tokens)
    if any(type(role) is not str for role in copied):
        raise ValueError("invalid_role_key")
    expected = set(required_birth_roles(world))
    missing, extra = expected - copied.keys(), copied.keys() - expected
    if missing:
        raise ValueError("missing_role:" + min(missing))
    if extra:
        raise ValueError("extra_role:" + min(extra))
    seen = set()
    for role, token in copied.items():
        kind = role.rsplit("/", 1)[1]
        if (type(token) is not str
                or re.fullmatch(rf"M2A{_PREFIXES[kind]}_[A-Z2-7]{{12}}", token) is None
                or token.endswith("_AAAAAAAAAAAA")):
            raise ValueError("invalid_role_token:" + role)
        if token in seen:
            raise ValueError("duplicate_role_token")
        seen.add(token)
    return MappingProxyType(copied)


@dataclass(frozen=True)
class BirthTarget:
    ordinal: int
    phase: str
    target_bytes: bytes
    target_sha256: str
    command: str
    operand: str | None
    trace_index: int
    current_before: str
    current_after: str
    selection_index: int | None


@dataclass(frozen=True)
class BirthTraceTurn:
    action: str
    response: str
    current_before: str
    current_after: str
    target_ordinal: int | None


@dataclass(frozen=True)
class BirthTraceFacts:
    selected_query: str
    failed_query: str | None
    failed_event: str | None
    failed_prediction: str | None
    failed_outcome: str | None
    corrective_query: str | None
    selected_event: str
    selected_prediction: str
    selected_outcome: str
    final_current: str


@dataclass(frozen=True)
class BirthCase:
    descriptor: BirthCaseDescriptor
    task: wire.TaskState
    task_text: str
    construction: worlds.OrdinaryConstruction
    trace: tuple
    targets: tuple
    facts: BirthTraceFacts
    status: str = STATUS
    memo_sha256: str = MEMO_SHA256
    clarification_sha256: str = CLARIFICATION_SHA256


@dataclass(frozen=True)
class BirthPair:
    world: str
    role_tokens: Mapping
    cases: tuple
    status: str = STATUS
    memo_sha256: str = MEMO_SHA256
    clarification_sha256: str = CLARIFICATION_SHA256


class _BirthBuilder:
    def __init__(self, world, role_tokens, display_master):
        self.descriptor = describe_birth_case(world, "m0")
        if type(display_master) is not bytes:
            raise ValueError("explicit_display_master_bytes_required")
        self.world = world
        self.tokens = _bindings(world, role_tokens)
        self.master = display_master
        self.family = self.descriptor.family.lower()
        self.states = ("s",) + tuple(f"{self.family}{hub:02d}" for hub in
                                     range(24 if self.family == "a" else 6))
        self.skin = self.descriptor.skin
        self.blocks = {}
        self.edges = {}
        self.ports = set()
        self.swap_slot = self.descriptor.relation_slot
        self.swap_request = None

    def token(self, state, goal, block, candidate, kind):
        return self.tokens["/".join(("birth_train", self.world, state, goal, block, candidate, kind))]

    def node(self, state):
        if state.startswith(("pred_", "surp_")):
            member = state.split("_")[1]
            goal = describe_birth_case(self.world, member).goal_index
            return self.token(state, f"{goal:02d}", "mismatch", "-", "node")
        return self.token(state, "-" if state == "s" else state[1:], "state", "-", "node")

    def destination(self, state, for_goal):
        if state.startswith("x"):
            return self.node(f"x{(int(state[1:]) + 3) % 24:02d}")
        if state != "s" and not state.startswith("surp_"):
            return self.node(f"g{for_goal:02d}")
        if self.descriptor.terminal_class == "REACHED":
            return self.node(f"g{for_goal:02d}")
        hub = for_goal if self.family == "a" else for_goal % 6
        return self.node(f"{self.family}{hub:02d}")

    def relation_rows(self, state, goal, recovery_member=None, *, deep_slot=None):
        ordinal = (81 + int(recovery_member[1:]) if recovery_member is not None else
                   worlds.state_ordinal("birth_train", self.world, state))
        slot = (3 * goal + ordinal + self.skin) % 4
        next_goal = (goal + 1) % 24
        pattern = ((state, goal), (state, next_goal), (f"x{goal:02d}", goal),
                   (f"x{next_goal:02d}", (goal + 2) % 24))
        offsets = (0, 1, 2, 3)
        if deep_slot is not None:
            if type(deep_slot) is not int or not 0 <= deep_slot < 4:
                raise ValueError("invalid_deep_swap_slot")
            slot = deep_slot
            offsets = (0, 2, 1, 3)
        block = "useful" if recovery_member is None else "recovery_" + recovery_member
        recover = "recover" if recovery_member is None else "recover2_" + recovery_member
        rows = [None] * 4
        for offset, (at_state, for_goal) in zip(offsets, pattern):
            candidate = str((slot + offset) % 4)
            destination = self.destination(at_state, for_goal)
            if deep_slot is not None and at_state == state and self.descriptor.terminal_class == "REACHED":
                destination = self.node(f"g{goal:02d}")
            rows[int(candidate)] = wire.EventRow(
                self.token(state, f"{goal:02d}", block, candidate, "event"), self.node(at_state),
                self.node(f"g{for_goal:02d}"), self.token(state, f"{goal:02d}", block, candidate, "port"),
                destination,
                self.token(state, f"{goal:02d}", recover, candidate, "query"),
                self.token(state, f"{goal:02d}", block, candidate, "receipt"))
        return tuple(rows)

    def add_relation(self, query, rows, actual_destinations=None):
        request = "READ RELATION " + query
        if request in self.blocks:
            raise ValueError("duplicate_relation_owner")
        raw = worlds.render_service("EVENTS", rows, skin=self.skin)
        self.blocks[request] = wire.parse_service(raw, skin=self.skin)
        for row in rows:
            if row.port in self.ports:
                raise ValueError("duplicate_world_port")
            self.ports.add(row.port)
            self.edges[row.node, row.port] = (actual_destinations or {}).get(row.port, row.got)

    def add_directory(self, state):
        template = f"{self.descriptor.pair_type}/{self.descriptor.bucket}/{self.descriptor.family}/{state}/index".encode("ascii")
        order = sorted(range(24), key=lambda goal: (
            sha256(self.master + b"\x00display-order\x00" + template + b"\x00"
                   + goal.to_bytes(4, "big")).digest(), goal))
        rows = tuple(wire.RouteRow(self.token(state, f"{goal:02d}", "index", "-", "route"),
                                   self.node(state), self.node(f"g{goal:02d}"),
                                   self.token(state, f"{goal:02d}", "useful", "-", "query"))
                     for goal in order)
        raw = worlds.render_service("ROUTES", rows, skin=self.skin)
        self.blocks["READ INDEX " + self.node(state)] = wire.parse_service(raw, skin=self.skin)

    def construct(self):
        mistaken = {}
        mismatch = self.descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH"
        if mismatch and self.descriptor.pair_type == "goal":
            for member in ("m0", "m1"):
                goal = describe_birth_case(self.world, member).goal_index
                mistaken[goal] = member
        for state in self.states:
            self.add_directory(state)
            for goal in range(24):
                deep = state == "s" and self.descriptor.pair_type == "relation" and goal == self.descriptor.goal_index
                rows = self.relation_rows(state, goal, deep_slot=self.swap_slot if deep else None)
                actual = {}
                query = self.token(state, f"{goal:02d}", "useful", "-", "query")
                if deep and mismatch:
                    changed_rows = list(rows)
                    for member, slot in (("m0", self.swap_slot), ("m1", (self.swap_slot + 2) % 4)):
                        original = rows[slot]
                        changed_rows[slot] = replace(original, got=self.node("pred_" + member))
                        actual[original.port] = self.node("surp_" + member)
                        corrective = self.relation_rows("surp_" + member, goal, member,
                                                        deep_slot=self.swap_slot if member == "m0" else None)
                        self.add_relation(original.recover, corrective)
                        if member == "m0":
                            self.swap_request = "READ RELATION " + original.recover
                    rows = tuple(changed_rows)
                elif deep:
                    self.swap_request = "READ RELATION " + query
                elif state == "s" and goal in mistaken:
                    member = mistaken[goal]
                    slot = (3 * goal + self.skin) % 4
                    original = rows[slot]
                    changed = wire.EventRow(original.event, original.node, original.goal, original.port,
                                            self.node("pred_" + member), original.recover, original.receipt)
                    rows = rows[:slot] + (changed,) + rows[slot + 1:]
                    actual[original.port] = self.node("surp_" + member)
                    corrective = self.relation_rows("surp_" + member, goal, member)
                    self.add_relation(original.recover, corrective)
                self.add_relation(query, rows, actual)
        blocks = MappingProxyType(dict(self.blocks))
        registry = MappingProxyType({request: block.raw for request, block in blocks.items()})
        return worlds.OrdinaryConstruction("birth_train", self.world, self.skin, "BIRTH_WORLD_ONLY",
                                           blocks, registry, MappingProxyType(dict(self.edges)))


def _swap_for_leaves(construction, request, slot):
    if type(slot) is not int or not 0 <= slot < 4:
        raise ValueError("invalid_deep_swap_slot")
    block = construction.blocks[request]
    if block.kind != "EVENTS":
        raise ValueError("deep_swap_requires_events")
    other = (slot + 2) % 4
    rows = list(block.rows)
    rows[slot] = replace(block.rows[slot], goal=block.rows[other].goal)
    rows[other] = replace(block.rows[other], goal=block.rows[slot].goal)
    raw = worlds.render_service("EVENTS", rows, skin=construction.skin)
    blocks = dict(construction.blocks)
    registry = dict(construction.registry)
    blocks[request] = wire.parse_service(raw, skin=construction.skin)
    registry[request] = raw
    return replace(construction, blocks=MappingProxyType(blocks), registry=MappingProxyType(registry))


def _unique(rows, current, goal):
    matches = [(index, row) for index, row in enumerate(rows) if row.node == current and row.goal == goal]
    if len(matches) != 1:
        raise ValueError("oracle_requires_unique_matching_row")
    return matches[0]


class _Trace:
    def __init__(self, task, construction):
        self.task = task
        self.current = task.current
        self.construction = construction
        self.service = wire.PassiveRegistry(construction.registry, skin=construction.skin)
        self.turns = []
        self.targets = []

    def perform(self, raw, phase=None, selection_index=None):
        action = wire.parse_action(raw)
        before = self.current
        if action.operation == "READ":
            response = "SERVICE\n" + self.service.read(raw)
        elif action.operation == "STEP":
            self.current = self.construction.transition(before, action.operand)
            response = "WORLD\nCURRENT " + self.current
        elif action.operation == "THINK":
            response = "ACK"
        else:
            if self.current != self.task.goal:
                raise ValueError("oracle_premature_stop")
            response = ""
        ordinal = None if phase is None else len(self.targets)
        if phase is not None:
            target = raw.encode("ascii")
            self.targets.append(BirthTarget(ordinal, phase, target, sha256(target).hexdigest(),
                                            action.operation, action.operand, len(self.turns), before,
                                            self.current, selection_index))
        self.turns.append(BirthTraceTurn(raw, response, before, self.current, ordinal))
        if action.operation == "READ":
            return wire.parse_service(response[len("SERVICE\n"):], skin=self.construction.skin)
        return None


def _oracle(descriptor, task, construction, tokens):
    trace = _Trace(task, construction)
    directory = trace.perform("READ INDEX " + task.current)
    if directory.kind != "ROUTES":
        raise ValueError("oracle_missing_start_directory")
    route_index, route = _unique(directory.rows, task.current, task.goal)
    selected_query = route.query
    expected_query = tokens[f"birth_train/{descriptor.world}/s/{descriptor.goal_index:02d}/useful/-/query"]
    if selected_query != expected_query:
        raise ValueError("oracle_route_binding_mismatch")
    failed_query = failed_event = failed_prediction = failed_outcome = corrective_query = None
    if descriptor.flow == "ORDINARY":
        events = trace.perform("READ RELATION " + selected_query, "SEEK", route_index)
    else:
        if descriptor.recovery_subtype in ("STRICT_MISS", "IRRELEVANT_RETURN"):
            if descriptor.recovery_subtype == "STRICT_MISS":
                failed_query = tokens[f"birth_train/{descriptor.world}/s/{descriptor.goal_index:02d}/miss_{descriptor.member}/-/query"]
            else:
                next_goal = tokens[f"birth_train/{descriptor.world}/g{(descriptor.goal_index + 1) % 24:02d}/{(descriptor.goal_index + 1) % 24:02d}/state/-/node"]
                failed_query = _unique(directory.rows, task.current, next_goal)[1].query
            bad = trace.perform("READ RELATION " + failed_query)
            if descriptor.recovery_subtype == "STRICT_MISS":
                if bad.kind != "MISS":
                    raise ValueError("oracle_expected_strict_miss")
            elif bad.kind != "EVENTS" or any(row.node == task.current and row.goal == task.goal for row in bad.rows):
                raise ValueError("oracle_expected_irrelevant_return")
            trace.perform("THINK REVISE " + failed_query, "READ_CHECK")
            corrective_query = selected_query
            events = trace.perform("READ RELATION " + selected_query, "SEEK", route_index)
        elif descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH":
            failed_query = selected_query
            bad = trace.perform("READ RELATION " + failed_query)
            bad_index, event = _unique(bad.rows, trace.current, task.goal)
            failed_event, failed_prediction = event.event, event.got
            trace.perform("STEP " + event.port)
            failed_outcome = trace.current
            owner = descriptor.member if descriptor.pair_type == "goal" else "m0"
            expected_surprise = tokens[f"birth_train/{descriptor.world}/surp_{owner}/{descriptor.goal_index:02d}/mismatch/-/node"]
            if failed_outcome == event.got or failed_outcome != expected_surprise:
                raise ValueError("oracle_mismatch_owner_or_outcome")
            trace.perform("THINK REVISE " + event.event, "STEP_CHECK", bad_index)
            corrective_query = event.recover
            events = trace.perform("READ RELATION " + event.recover, "SEEK")
        else:
            raise worlds.UnsupportedConstructionError("unsupported_birth_recovery")
    if events.kind != "EVENTS":
        raise ValueError("oracle_missing_useful_events")
    event_index, event = _unique(events.rows, trace.current, task.goal)
    trace.perform("STEP " + event.port, "PROSPECT", event_index)
    selected_outcome = trace.current
    if selected_outcome != event.got:
        raise ValueError("oracle_corrective_or_ordinary_prediction_mismatch")
    if descriptor.flow == "ORDINARY":
        trace.perform("THINK KEEP " + event.event, "STEP_CHECK", event_index)
    reached = trace.current == task.goal
    if reached != (descriptor.terminal_class == "REACHED"):
        raise ValueError("oracle_terminal_class_mismatch")
    continuation = trace.perform("STOP" if reached else "READ INDEX " + trace.current, "CONTINUE")
    if not reached and continuation.kind != "ROUTES":
        raise ValueError("oracle_unresolved_continuation_missing")
    if len(trace.targets) != 4:
        raise ValueError("oracle_target_count")
    facts = BirthTraceFacts(selected_query, failed_query, failed_event, failed_prediction,
                           failed_outcome, corrective_query, event.event, event.got,
                           selected_outcome, trace.current)
    return tuple(trace.turns), tuple(trace.targets), facts


def build_birth_pair(*, world, role_tokens, display_master):
    """Build two birth members; only bound relation FOR leaves vary in stores."""
    builder = _BirthBuilder(world, role_tokens, display_master)
    construction = builder.construct()
    cases = []
    for member in ("m0", "m1"):
        descriptor = describe_birth_case(world, member)
        member_construction = (_swap_for_leaves(construction, builder.swap_request, builder.swap_slot)
                               if member == "m1" and builder.swap_request is not None else construction)
        task = wire.TaskState(builder.node("s"), builder.node(f"g{descriptor.goal_index:02d}"), builder.node("s"))
        task_text = f"TASK\nSTART {task.start}\nGOAL {task.goal}\nCURRENT {task.current}"
        if wire.parse_task(task_text) != task:
            raise ValueError("oracle_task_round_trip")
        trace, targets, facts = _oracle(descriptor, task, member_construction, builder.tokens)
        cases.append(BirthCase(descriptor, task, task_text, member_construction, trace, targets, facts))
    return BirthPair(world, builder.tokens, tuple(cases))


def validate_birth_case(case, *, role_tokens):
    """Re-derive public trace decisions; this is not a full source-readiness gate."""
    if type(case) is not BirthCase:
        raise ValueError("birth_case_required")
    descriptor = describe_birth_case(case.descriptor.world, case.descriptor.member)
    if descriptor != case.descriptor:
        raise ValueError("case_descriptor_mismatch")
    tokens = _bindings(descriptor.world, role_tokens)
    start = tokens[f"birth_train/{descriptor.world}/s/-/state/-/node"]
    goal = tokens[f"birth_train/{descriptor.world}/g{descriptor.goal_index:02d}/{descriptor.goal_index:02d}/state/-/node"]
    if wire.parse_task(case.task_text) != wire.TaskState(start, goal, start) or case.task != wire.parse_task(case.task_text):
        raise ValueError("case_task_mismatch")
    construction = case.construction
    if (construction.domain, construction.world, construction.skin) != ("birth_train", descriptor.world, descriptor.skin):
        raise ValueError("case_construction_mismatch")
    if set(construction.blocks) != set(construction.registry):
        raise ValueError("case_registry_block_mismatch")
    for request, block in construction.blocks.items():
        if block != wire.parse_service(construction.registry[request], skin=descriptor.skin):
            raise ValueError("case_registry_block_mismatch")
    trace, targets, facts = _oracle(descriptor, case.task, construction, tokens)
    if (case.trace, case.targets, case.facts) != (trace, targets, facts):
        raise ValueError("case_oracle_trace_mismatch")
    if (case.status != STATUS or case.memo_sha256 != MEMO_SHA256
            or case.clarification_sha256 != CLARIFICATION_SHA256):
        raise ValueError("case_source_designation_mismatch")
    return True
