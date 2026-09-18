"""Bounded public-prefix null policies, not executed or scientifically qualified.

V2 section 11 supplies the rankings. V3 section 8 does not authorize semantic
metadata as policy input. V4 and the Builder clarification preserve the nulls.
No master is read or accepted: none of these bound hash preimages contains one.
The pinned null clarification binds descriptive NPAIR names and READ_ALL12's
post-CHECK arrival rule. Query READ-CHECK remains unsupported: it is not among
the 64 held null-panel members, whose CHECK operands are implicated EVENTs.
Schedules are policy state machines only: no Session driver, token accounting,
held-chain execution, score, alias scanner, or full-source readiness is supplied.
"""

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire


STATUS = "PARTIAL_SOURCE_ONLY"
EXECUTION_STATUS = "UNEXECUTED_INCOMPLETE"
NULL_CLARIFICATION_SHA256 = "c24451dd86493537d5e152a9560d7cb8c7cc331d3dfba052726671051b9d8919"
SPEC_SHA256 = MappingProxyType({
    "v2": "dd1f57693dfc09fae20691e1f53f11bc3b6a6d491bcb5e437aa4ed346d65df74",
    "v3": "da833b9df37930d0b06f9206e5fa47d5b436b325e833e6f6b2f4221f4d8808d1",
    "v4": "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1",
    "builder": "5484567fdad924247c5371a7430a071c925c563b5375336e8bef86dc6a4a99f9",
    "null_clarification": NULL_CLARIFICATION_SHA256,
})
SCIENCE_GATES = MappingProxyType({name: False for name in (
    "GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM",
)})
NULL_NAMES = (
    "sentinel_first", "display_first", "display_last", "lexical_first",
    "lexical_last", "shortest_first", "goal_digest", "current_digest",
    "character_columns",
)
NULL_PAIRS = tuple(combinations(NULL_NAMES, 2))
SCHEDULE_NAMES = (
    "S_DISPLAY0", "S_LEXICAL", "S_POSITION", "S_READ_ALL12", "S_STOP1", "S_STOP2",
)
SENTINELS = MappingProxyType({
    "SEEK": b"READ RELATION M2AQ_AAAAAAAAAAAA",
    "PROSPECT": b"STEP M2AP_AAAAAAAAAAAA",
    "CHECK": b"THINK KEEP M2AE_AAAAAAAAAAAA",
    "CONTINUE": b"READ INDEX M2AN_AAAAAAAAAAAA",
})


class SpecificationAmbiguity(ValueError):
    """Requires a prospective Main/Builder decision, not an inferred answer."""


@dataclass(frozen=True)
class PublicMessage:
    role: str
    content: bytes


@dataclass(frozen=True)
class PublicPanel:
    phase: str
    goal: bytes
    current: bytes
    candidates: tuple[bytes, ...]


@dataclass(frozen=True)
class _Prefix:
    task: wire.TaskState
    current: str
    last_action: wire.Action | None
    block: wire.ServiceBlock | None
    implicated: wire.EventRow | None


def _ascii(raw):
    if type(raw) is not bytes:
        raise ValueError("exact_public_bytes_required")
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("non_ascii_public_bytes") from error


def _prefix(prefix, skin):
    if type(skin) is not int or skin not in (0, 1):
        raise ValueError("invalid_skin")
    if (type(prefix) not in (tuple, list) or len(prefix) < 2 or len(prefix) % 2
            or len(prefix) > 2 + 2 * wire.CALL_CAP
            or any(type(message) is not PublicMessage for message in prefix)):
        raise ValueError("complete_bounded_public_prefix_required")
    if any(type(message.role) is not str or type(message.content) is not bytes for message in prefix):
        raise ValueError("exact_public_bytes_and_roles_required")
    if (prefix[0] != PublicMessage("system", wire.SYSTEM_MESSAGE.encode("ascii"))
            or prefix[1].role != "user"):
        raise ValueError("exact_system_and_task_required")
    task = wire.parse_task(_ascii(prefix[1].content))
    current = task.current
    block = None
    implicated = None
    last_action = None
    counts = dict.fromkeys(wire.LIMITS, 0)
    for offset in range(2, len(prefix), 2):
        actor, host = prefix[offset:offset + 2]
        if actor.role != "assistant" or host.role != "user":
            raise ValueError("invalid_prefix_roles")
        action = wire.parse_action(_ascii(actor.content))
        response = _ascii(host.content)
        counts[action.operation] += 1
        if counts[action.operation] > wire.LIMITS[action.operation]:
            raise ValueError("over_budget_public_prefix")
        if action.operand and action.operand.endswith("_AAAAAAAAAAAA"):
            raise ValueError("sentinel_in_accepted_history")
        if action.operation == "READ":
            if not response.startswith("SERVICE\n"):
                raise ValueError("read_requires_service")
            block = wire.parse_service(response[len("SERVICE\n"):], skin=skin)
            expected = "ROUTES" if action.verb == "INDEX" else "EVENTS"
            if block.kind not in (expected, "MISS"):
                raise ValueError("service_action_kind_mismatch")
            implicated = None
        elif action.operation == "STEP":
            if block is None or block.kind != "EVENTS":
                raise ValueError("step_requires_public_events")
            matches = tuple(row for row in block.rows if row.port == action.operand)
            if len(matches) != 1:
                raise SpecificationAmbiguity("step_event_not_uniquely_implicated")
            implicated = matches[0]
            current = wire.parse_world(response)
            block = None
        elif action.operation == "THINK":
            if response != "ACK":
                raise ValueError("think_requires_exact_ack")
        else:
            raise ValueError("prefix_contains_terminal_stop")
        last_action = action
    return _Prefix(task, current, last_action, block, implicated)


def public_candidates(prefix, *, phase, skin):
    """Derive candidates from exact messages, never targets or supplied operands.

    Phase is one of the four panel protocol phases, not a semantic case label.
    CHECK here covers public STEP outcomes. Query CHECK is unsupported and not
    applicable to the 64 held null-panel members; no query KEEP is invented.
    Non-panel recovery SEEK has no candidate directory in this contract.
    """
    if type(phase) is not str or phase not in SENTINELS:
        raise ValueError("unbound_panel_phase")
    view = _prefix(prefix, skin)
    action = view.last_action
    if phase in ("SEEK", "PROSPECT"):
        expected = "ROUTES" if phase == "SEEK" else "EVENTS"
        if (action is None or action.operation != "READ" or view.block is None
                or view.block.kind != expected):
            raise ValueError("phase_requires_latest_public_candidate_block")
        candidates = tuple(
            ("READ RELATION " + row.query if phase == "SEEK" else "STEP " + row.port)
            .encode("ascii") for row in view.block.rows)
    elif phase == "CHECK":
        if action is not None and action.operation == "READ":
            raise ValueError("unsupported_query_check_not_in_held_panels")
        if action is None or action.operation != "STEP" or view.implicated is None:
            raise ValueError("check_requires_public_step_outcome")
        candidates = tuple(f"THINK {verb} {view.implicated.event}".encode("ascii")
                           for verb in ("KEEP", "REVISE"))
    else:
        if action is not None and action.operation != "THINK":
            raise ValueError("continue_requires_task_or_ack_boundary")
        candidates = (b"STOP", b"READ INDEX " + view.current.encode("ascii"))
    candidates += (SENTINELS[phase],)
    if len(set(candidates)) != len(candidates):
        raise SpecificationAmbiguity("duplicate_public_candidate_actions")
    for candidate in candidates:
        wire.parse_action(_ascii(candidate))
    return PublicPanel(phase, view.task.goal.encode("ascii"),
                       view.current.encode("ascii"), candidates)


def _name(name):
    if type(name) is not str or name not in NULL_NAMES:
        raise ValueError("unknown_null_name")
    return NULL_NAMES.index(name)


def digest_preimage(public_identifier, action):
    """The exact shared N6/N7 preimage; no master, framing, or final NUL."""
    wire._identifier(_ascii(public_identifier), "node")
    wire.parse_action(_ascii(action))
    return public_identifier + b"\x00" + action


def character_columns(action):
    operand = (wire.parse_action(_ascii(action)).operand or "").encode("ascii")
    return (operand[0] if operand else 0,
            operand[5] if len(operand) > 5 else 0,
            operand[-1] if operand else 0, action)


def _rank(name, panel):
    index = _name(name)
    candidates = panel.candidates
    if index == 0:
        return candidates[-1:] + candidates[:-1]
    if index == 1:
        return candidates
    if index == 2:
        return tuple(reversed(candidates[:-1])) + candidates[-1:]
    if index in (3, 4):
        return tuple(sorted(candidates, reverse=index == 4))
    if index == 5:
        return tuple(sorted(candidates, key=lambda action: (len(action), action)))
    if index in (6, 7):
        identifier = panel.goal if index == 6 else panel.current
        keys = {action: sha256(digest_preimage(identifier, action)).digest()
                for action in candidates}
        if len(set(keys.values())) != len(keys):
            raise SpecificationAmbiguity("unbound_digest_collision_tie")
        return tuple(sorted(candidates, key=keys.__getitem__))
    return tuple(sorted(candidates, key=character_columns))


def rank_null(name, prefix, *, phase, skin):
    """Return a total ranking; its first bytes are the singleton action."""
    _name(name)
    return _rank(name, public_candidates(prefix, phase=phase, skin=skin))


@dataclass(frozen=True)
class PairNameBinding:
    """Exact descriptive ASCII NPAIR names, bound in N0..N8 order.

    The pinned null clarification excludes numeric labels, combined display
    lines, alternate spellings, salts, masters, and outcome-conditioned names.
    """

    names: tuple[bytes, ...]

    def __post_init__(self):
        expected = tuple(name.encode("ascii") for name in NULL_NAMES)
        if (type(self.names) is not tuple or any(type(name) is not bytes for name in self.names)
                or self.names != expected):
            raise ValueError("canonical_descriptive_pair_name_binding_required")


CANONICAL_PAIR_NAME_BINDING = PairNameBinding(tuple(name.encode("ascii") for name in NULL_NAMES))


def pair_tie_preimage(name_a, name_b, action, *, pair_names=CANONICAL_PAIR_NAME_BINDING):
    indices = sorted((_name(name_a), _name(name_b)))
    if indices[0] == indices[1]:
        raise ValueError("distinct_null_pair_required")
    if type(pair_names) is not PairNameBinding:
        raise ValueError("canonical_descriptive_pair_name_binding_required")
    pair_names.__post_init__()
    wire.parse_action(_ascii(action))
    return (b"NPAIR\x00" + pair_names.names[indices[0]] + b"\x00"
            + pair_names.names[indices[1]] + b"\x00" + action)


def rank_pair(name_a, name_b, prefix, *, phase, skin, pair_names=CANONICAL_PAIR_NAME_BINDING):
    """Total order-independent rank sum/max/digest combination, not a score."""
    panel = public_candidates(prefix, phase=phase, skin=skin)
    pair_tie_preimage(name_a, name_b, panel.candidates[0], pair_names=pair_names)
    ranks_a = {action: rank for rank, action in enumerate(_rank(name_a, panel))}
    ranks_b = {action: rank for rank, action in enumerate(_rank(name_b, panel))}
    keys = {action: (
        ranks_a[action] + ranks_b[action], max(ranks_a[action], ranks_b[action]),
        sha256(pair_tie_preimage(name_a, name_b, action, pair_names=pair_names)).digest(),
    ) for action in panel.candidates}
    if len(set(keys.values())) != len(keys):
        raise SpecificationAmbiguity("unbound_pair_digest_collision_tie")
    return tuple(sorted(panel.candidates, key=keys.__getitem__))


@dataclass(frozen=True)
class PolicyDecision:
    action: bytes | None
    terminal_reason: str | None
    status: str = EXECUTION_STATUS


class BoundedSchedule:
    """Incremental six-schedule actor; accepts only public host responses.

    Start with system/task only. next_action is idempotent until observe.
    Supply b'' after emitting STOP or a host-side invalid-action termination.
    Trace bytes are preserved. There is deliberately no runtime scoring, world
    driver, token budget certification, or claim of execution on held chains.
    S_READ_ALL12 checks the public outcome and receives ACK before testing
    latest CURRENT == GOAL, then STOPs on arrival even after an unexpected GOT.
    """

    def __init__(self, name, prefix, *, skin):
        if type(name) is not str or name not in SCHEDULE_NAMES:
            raise ValueError("unknown_schedule_name")
        view = _prefix(prefix, skin)
        if len(prefix) != 2:
            raise ValueError("schedule_requires_initial_public_prefix")
        self.name = name
        self.skin = skin
        self.current = view.current
        self.goal = view.task.goal
        self.trace = tuple(prefix)
        self.counts = dict.fromkeys(wire.LIMITS, 0)
        self.pending = None
        self.terminal_reason = None
        self._next = b"READ INDEX " + self.current.encode("ascii")
        self._queries = ()
        self._cursor = 0
        self._selected = None
        self._matched = None
        self._recovering = False

    def _terminate(self, reason):
        self.terminal_reason = reason
        self._next = None
        self.pending = None

    def next_action(self):
        if self.terminal_reason is not None:
            return PolicyDecision(None, self.terminal_reason)
        if self.pending is not None:
            return PolicyDecision(self.pending, None)
        action = wire.parse_action(_ascii(self._next))
        if (sum(self.counts.values()) >= wire.CALL_CAP
                or self.counts[action.operation] >= wire.LIMITS[action.operation]):
            self._terminate("action_cap")
            return PolicyDecision(None, self.terminal_reason)
        self.pending = self._next
        return PolicyDecision(self.pending, None)

    def _choose(self, rows, field):
        if not rows:
            raise ValueError("no_candidate")
        if self.name == "S_LEXICAL":
            values = [getattr(row, field) for row in rows]
            if len(values) != len(set(values)):
                raise SpecificationAmbiguity("ambiguous_lexical_candidate")
            return min(rows, key=lambda row: getattr(row, field).encode("ascii"))
        if self.name == "S_POSITION":
            return rows[sha256(self.goal.encode("ascii")).digest()[0] % len(rows)]
        return rows[0]

    def _next_query(self):
        if self._recovering or self._cursor >= len(self._queries):
            self._terminate("no_candidate")
        else:
            self._next = b"READ RELATION " + self._queries[self._cursor].encode("ascii")
            self._cursor += 1

    def observe(self, response):
        """Consume a response to the pending action; malformed states terminate."""
        if self.pending is None or self.terminal_reason is not None:
            raise ValueError("no_pending_policy_action")
        raw_action = self.pending
        action = wire.parse_action(_ascii(raw_action))
        if type(response) is not bytes:
            self._terminate("malformed_host_response")
            raise ValueError("exact_public_bytes_required")
        self.trace += (PublicMessage("assistant", raw_action),)
        if response:
            self.trace += (PublicMessage("user", response),)
        self.counts[action.operation] += 1
        self.pending = None
        try:
            text = _ascii(response)
            if action.operation == "STOP":
                if response != b"":
                    raise ValueError("stop_has_no_host_response")
                self._terminate("stop_emitted_unscored")
            elif response == b"":
                self._terminate("host_terminated_unscored")
            elif action.operation == "READ":
                self._observe_read(action, text)
            elif action.operation == "STEP":
                self.current = wire.parse_world(text)
                self._matched = self.current == self._selected.got
                verb = "REVISE" if self.name == "S_READ_ALL12" and not self._matched else "KEEP"
                self._next = f"THINK {verb} {self._selected.event}".encode("ascii")
            elif text != "ACK":
                raise ValueError("think_requires_exact_ack")
            else:
                self._after_check()
        except SpecificationAmbiguity as error:
            self._terminate("specification_ambiguity:" + str(error))
        except ValueError as error:
            self._terminate("malformed_host_response:" + str(error))

    def _observe_read(self, action, text):
        if not text.startswith("SERVICE\n"):
            raise ValueError("read_requires_service")
        block = wire.parse_service(text[len("SERVICE\n"):], skin=self.skin)
        if action.verb == "INDEX":
            if block.kind == "MISS":
                self._terminate("no_candidate")
            elif block.kind != "ROUTES":
                raise ValueError("index_requires_routes")
            elif self.name == "S_READ_ALL12":
                self._queries = tuple(row.query for row in block.rows)
                self._cursor = 0
                self._recovering = False
                self._next_query()
            else:
                row = self._choose(block.rows, "query")
                self._next = b"READ RELATION " + row.query.encode("ascii")
        elif block.kind not in ("EVENTS", "MISS"):
            raise ValueError("relation_requires_events_or_miss")
        elif self.name == "S_READ_ALL12":
            matches = tuple(row for row in block.rows
                            if row.goal == self.goal and row.node == self.current)
            if len(matches) > 1:
                raise SpecificationAmbiguity("multiple_matching_public_events")
            if matches:
                self._selected = matches[0]
                self._next = b"STEP " + self._selected.port.encode("ascii")
            else:
                self._next_query()
        elif block.kind == "MISS":
            self._terminate("no_candidate")
        else:
            self._selected = self._choose(block.rows, "port")
            self._next = b"STEP " + self._selected.port.encode("ascii")

    def _after_check(self):
        if self.name != "S_READ_ALL12":
            stop_after = 1 if self.name == "S_STOP1" else 2
            self._next = (b"STOP" if self.counts["STEP"] >= stop_after
                          else b"READ INDEX " + self.current.encode("ascii"))
        elif self.current == self.goal:
            self._next = b"STOP"
        elif not self._matched:
            self._recovering = True
            self._next = b"READ RELATION " + self._selected.recover.encode("ascii")
        else:
            self._next = b"READ INDEX " + self.current.encode("ascii")
