"""Partial candidate wire/session slice; no material, model, or scientific gate.

CPU counts are caller-supplied synthetic metadata, not tokenizer evidence.
Raw transport supports strings, bytes, and recursively typed builtin values.
Opaque Python objects and cyclic containers fail closed at the transport boundary.
CHECK correctness, witness scoring, and whole-chain scoring are not implemented.
Only the synthetic successful finish reason "stop" is admitted. Other non-length
finish labels remain unbound at this transport boundary, not inferred engine pins.
The v3 allocator consumes explicit role inventories and commitments; it does not
enumerate roles, validate scientific inventory semantics, or construct material.
"""

import base64
from dataclasses import dataclass
from hashlib import sha256
import re
from types import MappingProxyType


MEMO_SHA256 = "dd1f57693dfc09fae20691e1f53f11bc3b6a6d491bcb5e437aa4ed346d65df74"
ALLOCATION_MEMO_SHA256 = "da833b9df37930d0b06f9206e5fa47d5b436b325e833e6f6b2f4221f4d8808d1"
STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys((
    "adoption", "source_gate", "independent_checker", "materialization",
    "tokenizer", "model", "fit", "gpu", "scientific_claim",
), False))
LIMITS = MappingProxyType({"THINK": 8, "READ": 12, "STEP": 8, "STOP": 1})
TOKEN_CAP = 4096
CALL_CAP = 29
CONTEXT_CAP = 16384
IDENTIFIERS = {kind: rf"M2A{prefix}_[A-Z2-7]{{12}}" for kind, prefix in (
    ("node", "N"), ("query", "Q"), ("event", "E"),
    ("route", "I"), ("port", "P"), ("receipt", "R"),
)}
ACTION_PATTERN = re.compile(
    rf"(?:THINK KEEP {IDENTIFIERS['event']}"
    rf"|THINK REVISE (?:{IDENTIFIERS['event']}|{IDENTIFIERS['query']})"
    rf"|READ INDEX {IDENTIFIERS['node']}|READ RELATION {IDENTIFIERS['query']}"
    rf"|STEP {IDENTIFIERS['port']}|STOP)"
)
SYSTEM_MESSAGE = "\n".join((
    "You are the actor in M-COMBINE-4.",
    "Return exactly one action and no other bytes. Do not add whitespace, a code fence, CR, or LF.",
    "Legal actions are:",
    "THINK KEEP <event-id>",
    "THINK REVISE <event-or-query-id>",
    "READ INDEX <node-id>",
    "READ RELATION <query-id>",
    "STEP <port-id>",
    "STOP",
    "Identifiers are opaque.",
    "READ INDEX asks the exact service for a ROUTE directory at a public node.",
    "READ RELATION asks the exact service for an EVENT block at an opaque query.",
    "A ROUTE row states that its QUERY is relevant to its FOR goal while AT its state.",
    "An EVENT row is relevant only when both FOR equals the current GOAL and AT equals the latest CURRENT.",
    "For a relevant EVENT, DID is a possible STEP, GOT is its predicted next CURRENT, and RECOVER is a query to use only if the public outcome contradicts GOT.",
    "KEEP means the public CURRENT matched GOT. REVISE means a READ was MISS or irrelevant, or the public CURRENT contradicted GOT.",
    "STOP is correct only when the latest CURRENT equals GOAL.",
    "The service returns registered exact text or MISS. Unsupported actions terminate the task.",
))


def allocation_u32(value):
    if type(value) is not int or not 0 <= value < 2**32:
        raise ValueError("invalid_allocation_u32")
    return value.to_bytes(4, "big")


def _allocation_component(value):
    if (type(value) is not str or not value or not value.isascii()
            or any(character in value for character in "/\r\n\x00")):
        raise ValueError("invalid_allocation_component")
    return value.encode("ascii")


@dataclass(frozen=True)
class OpaqueNamespace:
    domain: str
    kind: str
    role_list_bytes: bytes
    role_list_sha256: str
    serial_tokens: tuple
    bindings: tuple


def allocate_opaque_namespace(*, master, domain, kind, role_keys, expected_count,
                              expected_role_list_sha256, occupied_tokens):
    """V3 sections 2/3.1/3.2 byte allocation over explicitly supplied roles.

    This checks role syntax and the supplied per-kind count/hash commitment,
    not the finite scientific role expansion. The caller must supply all prior
    namespace tokens for cross-domain collision checks. No reserved pools,
    display positions, registry, task, or canonical graph is constructed here.
    No master, domain, inventory, commitment, or collision context is defaulted.
    """
    prefixes = {"node": "M2AN_", "query": "M2AQ_", "event": "M2AE_",
                "route": "M2AI_", "port": "M2AP_", "receipt": "M2AR_"}
    if type(master) is not bytes:
        raise ValueError("allocation_master_requires_bytes")
    domain_bytes = _allocation_component(domain)
    kind_bytes = _allocation_component(kind)
    if kind not in prefixes:
        raise ValueError("invalid_allocation_kind")
    if type(role_keys) not in (tuple, list) or type(occupied_tokens) not in (tuple, list):
        raise ValueError("allocation_requires_explicit_sequences")
    if type(expected_count) is not int or not 0 <= expected_count <= 2**32:
        raise ValueError("invalid_role_count")
    if (type(expected_role_list_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", expected_role_list_sha256) is None):
        raise ValueError("invalid_role_hash")
    roles = []
    for role in role_keys:
        if type(role) is not str:
            raise ValueError("invalid_role_key")
        parts = role.split("/")
        if len(parts) != 7:
            raise ValueError("invalid_role_key")
        for part in parts:
            _allocation_component(part)
        if (parts[0] != domain or parts[6] != kind
                or re.fullmatch(r"(?:0[0-9]|1[0-9]|2[0-3]|-)", parts[3]) is None
                or re.fullmatch(r"[0-3]|-", parts[5]) is None):
            raise ValueError("invalid_role_key")
        roles.append(role.encode("ascii"))
    if len(set(roles)) != len(roles):
        raise ValueError("duplicate_role_key")
    roles.sort()
    role_list_bytes = b"\n".join(roles)
    role_hash = sha256(role_list_bytes).hexdigest()
    if len(roles) != expected_count or role_hash != expected_role_list_sha256:
        raise ValueError("role_commitment_mismatch")
    occupied = set()
    for token in occupied_tokens:
        if (type(token) is not str
                or re.fullmatch(r"M2A[NQEIPR]_[A-Z2-7]{12}", token) is None
                or token.endswith("_AAAAAAAAAAAA")):
            raise ValueError("invalid_occupied_token")
        occupied.add(token)
    preimage = master + b"\x00" + domain_bytes + b"\x00"
    candidates = []
    seen = set()
    for serial in range(len(roles)):
        digest = sha256(preimage + kind_bytes + b"\x00" + allocation_u32(serial)).digest()
        token = prefixes[kind] + base64.b32encode(digest)[:12].decode("ascii")
        if token.endswith("_AAAAAAAAAAAA"):
            raise ValueError("reserved_allocation_token")
        if token in seen or token in occupied:
            raise ValueError("allocation_token_collision")
        seen.add(token)
        candidates.append(token)
    ordered_tokens = sorted((token.encode("ascii") for token in candidates), key=lambda token: (
        sha256(preimage + b"pool-order\x00" + token).digest(), token))
    ordered_roles = sorted(roles, key=lambda role: (
        sha256(preimage + b"role-order\x00" + role).digest(), role))
    bindings = tuple((role.decode("ascii"), token.decode("ascii"))
                     for role, token in zip(ordered_roles, ordered_tokens))
    return OpaqueNamespace(domain, kind, role_list_bytes, role_hash, tuple(candidates), bindings)


def _text(raw):
    if type(raw) is not str or not raw.isascii() or "\r" in raw or "\x00" in raw:
        raise ValueError("invalid_wire_text")
    return raw


def _identifier(value, kind, *, allocated=True):
    if type(value) is not str or re.fullmatch(IDENTIFIERS[kind], value) is None:
        raise ValueError("invalid_identifier")
    if allocated and value.endswith("_AAAAAAAAAAAA"):
        raise ValueError("reserved_identifier")
    return value


@dataclass(frozen=True)
class Action:
    operation: str
    verb: str | None
    operand: str | None


def parse_action(raw):
    if ACTION_PATTERN.fullmatch(_text(raw)) is None:
        raise ValueError("malformed_action")
    parts = raw.split(" ")
    return Action(parts[0], parts[1] if len(parts) == 3 else None,
                  parts[-1] if len(parts) > 1 else None)


@dataclass(frozen=True)
class TaskState:
    start: str
    goal: str
    current: str


def parse_task(raw):
    pattern = rf"TASK\nSTART ({IDENTIFIERS['node']})\nGOAL ({IDENTIFIERS['node']})\nCURRENT ({IDENTIFIERS['node']})"
    match = re.fullmatch(pattern, _text(raw))
    if match is None:
        raise ValueError("malformed_task")
    return TaskState(*(_identifier(value, "node") for value in match.groups()))


def parse_world(raw):
    match = re.fullmatch(rf"WORLD\nCURRENT ({IDENTIFIERS['node']})", _text(raw))
    if match is None:
        raise ValueError("malformed_world")
    return _identifier(match[1], "node")


@dataclass(frozen=True)
class RouteRow:
    route: str
    node: str
    goal: str
    query: str


@dataclass(frozen=True)
class EventRow:
    event: str
    node: str
    goal: str
    port: str
    got: str
    recover: str
    receipt: str


@dataclass(frozen=True)
class ServiceBlock:
    kind: str
    rows: tuple
    raw: str


def parse_service(raw, *, skin):
    if type(skin) is not int or skin not in (0, 1):
        raise ValueError("invalid_skin")
    lines = _text(raw).split("\n")
    if raw == "MISS":
        return ServiceBlock("MISS", (), raw)
    layouts = {
        ("ROUTES", 0): (("ROUTE", "route"), ("AT", "node"), ("FOR", "goal"), ("QUERY", "query")),
        ("ROUTES", 1): (("ROUTE", "route"), ("FOR", "goal"), ("QUERY", "query"), ("AT", "node")),
        ("EVENTS", 0): (("EVENT", "event"), ("AT", "node"), ("FOR", "goal"), ("DID", "port"), ("GOT", "got"), ("RECOVER", "recover"), ("EVIDENCE", "receipt")),
        ("EVENTS", 1): (("EVENT", "event"), ("FOR", "goal"), ("AT", "node"), ("GOT", "got"), ("DID", "port"), ("RECOVER", "recover"), ("EVIDENCE", "receipt")),
    }
    kind = lines[0]
    if kind not in ("ROUTES", "EVENTS") or len(lines) != (25 if kind == "ROUTES" else 5):
        raise ValueError("malformed_service_block")
    rows = []
    aliases = {"goal": "node", "got": "node", "recover": "query"}
    for line in lines[1:]:
        parts = line.split(" ")
        layout = layouts[kind, skin]
        if len(parts) != len(layout) * 2:
            raise ValueError("malformed_service_row")
        values = {}
        for index, (label, field) in enumerate(layout):
            if parts[index * 2] != label:
                raise ValueError("malformed_service_row")
            values[field] = _identifier(parts[index * 2 + 1], aliases.get(field, field))
        rows.append((RouteRow if kind == "ROUTES" else EventRow)(**values))
    return ServiceBlock(kind, tuple(rows), raw)


class PassiveRegistry:
    """Exact request-to-bytes registry; no task, goal, world, or scorer input."""

    def __init__(self, registry, *, skin):
        parse_service("MISS", skin=skin)
        entries = dict(registry)
        for request, response in entries.items():
            action = parse_action(request)
            if action.operation != "READ":
                raise ValueError("registry_requires_read")
            _identifier(action.operand, "node" if action.verb == "INDEX" else "query")
            block = parse_service(response, skin=skin)
            expected = "ROUTES" if action.verb == "INDEX" else "EVENTS"
            if block.kind not in (expected, "MISS"):
                raise ValueError("registry_response_kind")
        self._registry = MappingProxyType(entries)

    def read(self, request):
        if parse_action(request).operation != "READ":
            raise ValueError("unsupported_service_request")
        return self._registry.get(request, "MISS")


def _freeze(value, ancestors=()):
    """Lossless typed builtin transport snapshot without repr/stringification."""
    kind = type(value)
    if kind in (str, bytes, int, bool, type(None)):
        return (kind.__name__, value)
    if kind is float:
        import struct
        return ("float", struct.pack("!d", value))
    if kind is bytearray:
        return ("bytearray", bytes(value))
    if kind not in (list, tuple, dict) or id(value) in ancestors:
        raise ValueError("unsupported_custody_transport")
    ancestry = ancestors + (id(value),)
    if kind is dict:
        return ("dict", tuple((_freeze(key, ancestry), _freeze(item, ancestry))
                              for key, item in value.items()))
    return (kind.__name__, tuple(_freeze(item, ancestry) for item in value))


def _raw_bytes(raw):
    if type(raw) is bytes:
        return raw
    if type(raw) is str:
        try:
            return raw.encode("utf-8")
        except UnicodeEncodeError:
            return None
    return None


@dataclass(frozen=True)
class Snapshot:
    current: str
    counts: tuple
    actual_tokens: int
    terminated: bool
    terminal_reason: str | None
    goal_arrival_stop: bool


@dataclass(frozen=True)
class RawAttempt:
    call_index: int
    raw: tuple
    raw_bytes: bytes | None
    generation_request: tuple
    declared_tokens: tuple
    actual_tokens: tuple
    context_tokens: tuple
    truncated: tuple
    finish_reason: tuple
    pre_state: Snapshot


@dataclass(frozen=True)
class Attempt:
    capture: RawAttempt
    parser_disposition: str
    action: Action | None
    response_bytes: bytes
    post_state: Snapshot
    accepted: bool
    terminal_reason: str | None


class Session:
    """Mechanical autonomous session, not a CHECK or whole-chain scorer.

    Immutable raw captures are appended before validation; immutable outcomes
    reference them afterward. Transport encoding failure terminates and raises
    instead of fabricating lossless custody for an unsupported Python object.
    """

    def __init__(self, task_text, transitions, service):
        task = parse_task(task_text)
        if type(service) is not PassiveRegistry:
            raise ValueError("passive_registry_required")
        world = dict(transitions)
        for (node, port), destination in world.items():
            _identifier(node, "node")
            _identifier(port, "port")
            _identifier(destination, "node")
        self._world = MappingProxyType(world)
        self._service = service
        self._goal = task.goal
        self._state = Snapshot(task.current, tuple((name, 0) for name in LIMITS),
                               0, False, None, False)
        self._raw_attempts = ()
        self._attempts = ()
        self._receipts = ()

    @property
    def state(self):
        return self._state

    @property
    def raw_attempts(self):
        return self._raw_attempts

    @property
    def attempts(self):
        return self._attempts

    @property
    def receipts(self):
        return self._receipts

    def turn(self, raw, *, generation_request, declared_tokens, actual_tokens,
             context_tokens, truncated, finish_reason):
        before = self._state
        try:
            capture = RawAttempt(
                len(self._raw_attempts), _freeze(raw), _raw_bytes(raw),
                _freeze(generation_request), _freeze(declared_tokens), _freeze(actual_tokens),
                _freeze(context_tokens), _freeze(truncated), _freeze(finish_reason), before,
            )
        except (ValueError, RecursionError) as error:
            if not before.terminated:
                self._state = Snapshot(before.current, before.counts, before.actual_tokens,
                                       True, "unsupported_custody_transport", False)
            raise ValueError("unsupported_custody_transport") from error
        self._raw_attempts += (capture,)
        action = None
        disposition = "not_parsed"
        response = ""
        reason = None
        accepted = False
        counts = dict(before.counts)
        tokens = before.actual_tokens
        current = before.current
        arrival_stop = before.goal_arrival_stop
        if before.terminated:
            reason = "session_terminated"
        else:
            try:
                action = parse_action(raw)
                disposition = "valid"
            except ValueError:
                disposition = "invalid"
                reason = "malformed_action"
            valid_counts = (type(actual_tokens) is int and actual_tokens >= 0
                            and type(declared_tokens) is int and declared_tokens >= 0
                            and type(context_tokens) is int and 0 <= context_tokens <= CONTEXT_CAP)
            if type(actual_tokens) is int and actual_tokens >= 0:
                tokens += actual_tokens
            if reason is None and (not valid_counts or declared_tokens != actual_tokens):
                reason = "invalid_token_accounting"
            if reason is None and (type(truncated) is not bool or type(finish_reason) is not str):
                reason = "invalid_generation_metadata"
            if reason is None and (truncated or finish_reason == "length"):
                reason = "length_limited"
            if reason is None and finish_reason != "stop":
                reason = "unbound_finish_reason"
            if reason is None:
                allowance = min(256, TOKEN_CAP - before.actual_tokens, CONTEXT_CAP - context_tokens)
                if allowance <= 0:
                    reason = "zero_allowance"
                elif (type(generation_request) is not dict
                      or type(generation_request.get("max_new_tokens")) is not int
                      or generation_request["max_new_tokens"] != allowance):
                    reason = "invalid_generation_request"
                elif actual_tokens <= 0 or actual_tokens > allowance:
                    reason = "invalid_token_accounting"
            if reason is None:
                counts[action.operation] += 1
                if (counts[action.operation] > LIMITS[action.operation]
                        or tokens > TOKEN_CAP or capture.call_index >= CALL_CAP):
                    reason = "over_budget"
            if reason is None:
                if action.operation == "THINK":
                    response = "ACK"
                elif action.operation == "READ":
                    response = "SERVICE\n" + self._service.read(raw)
                elif action.operation == "STEP":
                    destination = self._world.get((current, action.operand))
                    if destination is None:
                        reason = "invalid_step"
                    else:
                        current = destination
                        response = "WORLD\nCURRENT " + current
                else:
                    arrival_stop = current == self._goal
                    reason = "goal_arrival_stop" if arrival_stop else "premature_stop"
                accepted = reason in (None, "goal_arrival_stop", "premature_stop")
        if before.terminated:
            after = before
        else:
            after = Snapshot(current, tuple(counts.items()), tokens,
                             reason is not None, reason, arrival_stop)
        self._state = after
        attempt = Attempt(capture, disposition, action, response.encode("ascii"),
                          after, accepted, reason)
        self._attempts += (attempt,)
        if accepted and action.operation in ("READ", "STEP"):
            self._receipts += (attempt,)
        return attempt
