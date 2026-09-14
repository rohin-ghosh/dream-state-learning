"""Partial source binding of birth ArmRecords to the existing leak scanner.

Public APIs:
  bind_birth_arm(record, case, *, role_tokens) -> BoundScanInputs
  scan_birth_arm(record, case, *, role_tokens, semantic_bytes,
                 future_identifiers, registered_routes) -> BirthScanReport
  scan_birth_pair(pair, case, *, role_tokens, closed_inventory,
                  atom_inventory) -> PairedScanReport
The latter inventories are explicit ScanInventory objects, independently
supplied for CLOSED and ATOM_LOCAL. No inventory parameter has a default.

Authority: v2 section 8, v3 section 8 semantic aliases, v4, and Builder source
clarification v1 plus causal-occurrence clarifications v1/v2. The bound producer
validates the supplied BirthCase against role bindings and reconstructs the
exact paired ArmRecords; this is correlated
source validation, NOT independent material, provenance, or C11 certification.
No caller-provided span, current, implicated ID or contradiction is accepted.

PUBLIC_CONTENT_LF_PROJECTION_V1 is exactly the ASCII content of each original
prefix message joined by one LF, with no final added LF. Roles and message
boundaries remain in MessageSpan metadata. It is NOT JSON rendering, a native
chat template, a token stream, or a training tensor. No evaluator metadata,
semantic bytes, source labels, future ledger, target, or field-path receipt is
appended to public content. No actor, tokenizer, model, file, network, or GPU is
called. The target assistant response is never included in the projection.

Chronology uses the original source trace: system=0, original task=1, actor
turn t=2+2*t, host turn t=3+2*t, decision=2+2*target.trace_index. An ATOM task
is observed at 1+2*t for its first retained turn (or decision-1 for CONTINUE),
binding its rewritten CURRENT to the authentic retained boundary. Prefix
positions are separate from these source observation indices. Every observation
is retained for inspection, including previous CURRENTs. Only the last CURRENT
observation receives a current/task_current exemption. START/GOAL remain exact
task-fact fields. Event selection, READ failure and STEP contradiction are
derived sequentially from retained public messages, never case.facts/answers.

Allowed scanner fields are parsed task facts, returned QUERY/DID/RECOVER/GOT,
actually selected EVENT, issued query, already implicated THINK operand, latest
CURRENT, and exact fixed protocol. All other parsed fields are observations,
not exemptions. A public field never authorizes a full scheduled action or
semantic label. Future and route inventories pass unchanged to the scanner;
even a returned DID does not exempt a caller-declared future identifier.

Only supplied_projection_clear describes a clean supplied projection. Inventory
completeness/authority cannot be inferred from explicit empty or nonempty
inputs, and all full-source/native/provenance/science flags remain false.
Actual template bytes and complete whole-future/semantic/route inventory audit
remain Main's responsibility. Existing scanner findings are never suppressed.
The causal-occurrence clarifications allow historical ROUTE QUERY only for
CHECK's implicated issued query, and CONTINUE EVENT GOT only for latest CURRENT
with a well-typed EVENT owner. V2 replaces only v1's selected-owner requirement:
distinct authentic EVENTs may share the observed destination. Original owners
and service provenance remain intact; no future-ID, full-action, semantic or
route leak is waived.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6 import composition_birth_stage2a_targets as targets


STATUS = "PARTIAL_SOURCE_ONLY"
PROJECTION_KIND = "PUBLIC_CONTENT_LF_PROJECTION_V1"
CONTRACT_HASHES = MappingProxyType({
    "v2": "dd1f57693dfc09fae20691e1f53f11bc3b6a6d491bcb5e437aa4ed346d65df74",
    "v3": "da833b9df37930d0b06f9206e5fa47d5b436b325e833e6f6b2f4221f4d8808d1",
    "v4": "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1",
    "clarification_v1": "5484567fdad924247c5371a7430a071c925c563b5375336e8bef86dc6a4a99f9",
    "causal_occurrence_v1": "37398723e197fcba2b24a505f06395c311d3dfcd488e9fc4026d883f6aeb4b07",
    "causal_occurrence_v2": "a08b6ff2df927552f6c96917f58181f56f17f456643afaee28c8bb2dd7722b16",
})
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
SCIENCE_GATES = MappingProxyType(dict.fromkeys((*scanner.SCIENCE_GATES,
    "native_chat_bytes", "inventory_completeness", "independent_source_authentication"), False))
LIMITATIONS = (
    "Public-content LF projection only; not native chat/template bytes or tokens.",
    "Authenticates spans against the supplied producer, not independent material/provenance truth.",
    "Semantic/future/route inventory completeness and authority remain unverified, including explicit empties.",
    "No full-source, scientific guard, C11 readiness, or promotion is supplied.",
    "Causal service occurrence exceptions authorize operands only, never other leak categories.",
)


class ScanInputError(ValueError):
    """Source record, retained-prefix, parse, or explicit-inventory failure."""


def _require(condition, message):
    if not condition:
        raise ScanInputError(message)


class _Partial:
    status = STATUS
    science_gates = SCIENCE_GATES
    limitations = LIMITATIONS
    inventory_completeness_verified = False
    native_chat_bytes_verified = False


@dataclass(frozen=True)
class ScanInventory:
    semantic_bytes: bytes
    future_identifiers: tuple[bytes, ...]
    registered_routes: tuple[bytes, ...]
    semantic_profile: str = "legacy"


@dataclass(frozen=True)
class MessageSpan:
    message_index: int
    role: str
    start: int
    end: int
    source_trace_index: int | None
    observed_at: int
    content_sha256: str


@dataclass(frozen=True)
class FieldObservation:
    path: str
    start: int
    end: int
    value: bytes
    kind: str
    origin: str
    observed_at: int
    source_trace_index: int | None
    evidence: str
    owner: bytes | None = None
    exemption_kind: str | None = None
    is_latest_current: bool = False


@dataclass(frozen=True)
class BoundScanInputs(_Partial):
    public_messages: tuple[targets.Message, ...]
    projection_bytes: bytes
    projection_sha256: str
    source_prefix_sha256: str
    message_spans: tuple[MessageSpan, ...]
    observations: tuple[FieldObservation, ...]
    fields: tuple[scanner.PublicField, ...]
    retained_trace_indices: tuple[int, ...]
    decision_index: int
    target: bytes
    phase: str
    task_start: bytes
    task_goal: bytes
    current: bytes
    implicated_query: bytes | None
    implicated_event: bytes | None
    observed_contradiction: bool
    projection_kind: str = PROJECTION_KIND


@dataclass(frozen=True)
class BirthScanReport(_Partial):
    binding: BoundScanInputs
    scan_report: scanner.ScanReport
    semantic_sha256: str
    future_identifiers: tuple[bytes, ...]
    registered_routes: tuple[bytes, ...]
    semantic_profile: str = "legacy"
    source_semantic_occurrences: bool = False

    @property
    def supplied_projection_clear(self):
        return self.scan_report.passed


@dataclass(frozen=True)
class PairedScanReport(_Partial):
    closed: BirthScanReport
    atom_local: BirthScanReport


def _expected_pairs(case, role_tokens):
    _require(type(case) is birth.BirthCase, "source BirthCase required")
    try:
        return targets.serialize_birth_case(case, role_tokens=role_tokens)
    except (TypeError, ValueError, AttributeError) as error:
        raise ScanInputError("source case validation failed: " + str(error)) from error


def _select(record, pairs, case):
    _require(type(record) is targets.ArmRecord, "source ArmRecord required; bound spans are not inputs")
    _require(record.arm in ("CLOSED", "ATOM_LOCAL"), "unknown arm")
    _require(type(record.prefix) is tuple and type(record.unit) is targets.TargetUnit, "immutable source prefix/unit required")
    for index, pair in enumerate(pairs):
        expected = pair.closed if record.arm == "CLOSED" else pair.atom_local
        if record == expected:
            return case.targets[index]
    raise ScanInputError("record does not match exact producer prefix, target and hashes")


def _retained_indices(record, case, target):
    boundary = target.trace_index
    if record.arm == "CLOSED":
        return tuple(range(boundary))
    if target.phase == "CONTINUE":
        return ()
    if target.phase in ("PROSPECT", "READ_CHECK"):
        return (boundary - 1,)
    if target.phase == "STEP_CHECK":
        return (boundary - 2, boundary - 1)
    if target.phase == "SEEK":
        return (tuple(range(boundary - 3, boundary))
                if case.descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH" else (0,))
    raise ScanInputError("unsupported source decision phase")


def _tokens(content):
    """Offsets within exact, already parsed wire lines; never substring searches."""
    offset = 0
    lines = []
    for line in content.split("\n"):
        parts = []
        cursor = offset
        for token in line.split(" "):
            parts.append((token, cursor, cursor + len(token)))
            cursor += len(token) + 1
        lines.append(tuple(parts))
        offset += len(line) + 1
    return tuple(lines)


def _bind(record, case, target):
    retained = _retained_indices(record, case, target)
    _require(all(0 <= index < target.trace_index for index in retained), "retained trace outside decision")
    _require(len(record.prefix) == 2 + 2 * len(retained), "retained message count mismatch")
    decision = 2 + 2 * target.trace_index
    task_at = 1 if record.arm == "CLOSED" else 1 + 2 * (retained[0] if retained else target.trace_index)
    spans = []
    pieces = []
    offset = 0
    for index, message in enumerate(record.prefix):
        raw = message.content.encode("ascii")
        trace_index = retained[(index - 2) // 2] if index >= 2 else None
        observed = (0 if index == 0 else task_at if index == 1
                    else 2 + 2 * trace_index + (index % 2))
        _require(observed < decision, "message not observed before decision")
        spans.append(MessageSpan(index, message.role, offset, offset + len(raw), trace_index,
                                 observed, sha256(raw).hexdigest()))
        pieces.append(raw)
        offset += len(raw) + 1
    projection = b"\n".join(pieces)
    _require(len(projection) <= scanner.BOUNDS["bytes"], "projection exceeds scanner byte bound")
    observations = []

    def add(message_index, token, suffix, kind, origin, owner=None, exemption=None):
        value, start, end = token
        span = spans[message_index]
        raw = value.encode("ascii")
        _require(projection[span.start + start:span.start + end] == raw, "derived span mismatch")
        observations.append(FieldObservation(
            f"/messages/{message_index}/{suffix}", span.start + start, span.start + end, raw,
            kind, origin, span.observed_at, span.source_trace_index,
            f"source-message:{message_index}:sha256:{span.content_sha256}", owner, exemption))

    add(0, (wire.SYSTEM_MESSAGE, 0, len(wire.SYSTEM_MESSAGE)), "protocol", "protocol", "system", exemption="protocol")
    task = wire.parse_task(record.prefix[1].content)
    lines = _tokens(record.prefix[1].content)
    for line, kind in zip(lines[1:], ("task_start", "task_goal", "task_current")):
        add(1, line[1], "TASK/" + line[0][0], kind, "task",
            exemption=kind if kind != "task_current" else None)
    current = task.current
    current_observation = len(observations) - 1
    pending = None
    event_rows = {}
    implicated_query = None
    implicated_event = None
    event_selected_at = None
    observed_contradiction = False
    for message_index in range(2, len(record.prefix)):
        message = record.prefix[message_index]
        trace_index = spans[message_index].source_trace_index
        source_turn = case.trace[trace_index]
        if message.role == "assistant":
            _require(message.content == source_turn.action and current == source_turn.current_before,
                     "retained action/state mismatch")
            pending = wire.parse_action(message.content)
            action_token = _tokens(message.content)[0][-1]
            if pending.operation == "READ":
                add(message_index, action_token, "action/operand", "issued_query" if pending.verb == "RELATION"
                    else "read_index_operand", "actor", exemption="issued_query" if pending.verb == "RELATION" else None)
            elif pending.operation == "STEP":
                candidates = [row for row in event_rows.values() if row.node == current
                              and row.goal == task.goal and row.port == pending.operand]
                _require(len(candidates) == 1, "STEP lacks unique retained public EVENT")
                implicated_event = candidates[0]
                event_selected_at = spans[message_index].observed_at
                implicated_query = None
                add(message_index, action_token, "action/operand", "step_operand", "actor")
            elif pending.operation == "THINK":
                allowed_event = (implicated_event is not None and pending.operand == implicated_event.event
                                 and pending.verb == ("REVISE" if observed_contradiction else "KEEP"))
                allowed_query = pending.operand == implicated_query and pending.verb == "REVISE"
                _require(allowed_event or allowed_query, "THINK lacks already implicated public operand")
                add(message_index, action_token, "action/operand", "think_implicated", "actor", exemption="think_implicated")
            else:
                raise ScanInputError("STOP cannot be a retained pre-decision action")
            continue
        _require(pending is not None and message.content == source_turn.response, "retained response mismatch")
        if pending.operation == "READ":
            _require(message.content == "SERVICE\n" + case.construction.read(source_turn.action),
                     "response differs from supplied source registry")
            block = wire.parse_service(message.content[len("SERVICE\n"):], skin=case.descriptor.skin)
            expected_kind = "ROUTES" if pending.verb == "INDEX" else "EVENTS"
            _require(block.kind in (expected_kind, "MISS"), "READ response kind mismatch")
            if pending.verb == "RELATION":
                relevant = [row for row in block.rows if row.node == current and row.goal == task.goal]
                implicated_query = pending.operand if not relevant else None
            for row_index, (row, line) in enumerate(zip(block.rows, _tokens(message.content)[2:])):
                owner = row.event.encode("ascii") if block.kind == "EVENTS" else None
                if block.kind == "EVENTS":
                    event_rows[row.event] = row
                for column in range(0, len(line), 2):
                    label = line[column][0]
                    kind = (("route_query" if label == "QUERY" else "route_" + label.lower())
                            if block.kind == "ROUTES" else "event_" + label.lower())
                    if label in ("EVENT", "ROUTE"):
                        kind = "event_id" if label == "EVENT" else "route_id"
                    exemption = kind if kind in ("route_query", "event_did", "event_recover", "event_got") else None
                    add(message_index, line[column + 1], f"SERVICE/{block.kind}/rows/{row_index}/{label}",
                        kind, "service", owner, exemption)
        elif pending.operation == "STEP":
            destination = wire.parse_world(message.content)
            _require(case.construction.transition(current, pending.operand) == destination,
                     "WORLD differs from supplied source transition")
            current = destination
            observed_contradiction = current != implicated_event.got
            add(message_index, _tokens(message.content)[1][1], "WORLD/CURRENT", "current", "host")
            current_observation = len(observations) - 1
        else:
            _require(message.content == "ACK", "THINK response must be ACK")
        _require(current == source_turn.current_after, "retained host CURRENT mismatch")
        pending = None
    _require(pending is None and current == target.current_before, "decision CURRENT mismatch")
    observations[current_observation] = replace(observations[current_observation],
                                                exemption_kind=observations[current_observation].kind,
                                                is_latest_current=True)
    if implicated_event is not None:
        for index, observation in enumerate(observations):
            if (observation.kind == "event_id" and observation.value == implicated_event.event.encode("ascii")
                    and observation.observed_at < event_selected_at):
                observations[index] = replace(observation, exemption_kind="selected_event")
    fields = tuple(scanner.PublicField(item.path, item.start, item.end, item.exemption_kind, item.origin,
                                       item.observed_at, item.evidence, item.owner)
                   for item in observations if item.exemption_kind is not None)
    _require(len(fields) <= scanner.BOUNDS["fields"], "derived fields exceed scanner bound")
    return BoundScanInputs(record.prefix, projection, sha256(projection).hexdigest(), record.prefix_sha256,
                           tuple(spans), tuple(observations), fields, retained, decision, target.target_bytes,
                           target.phase, task.start.encode("ascii"), task.goal.encode("ascii"), current.encode("ascii"),
                           implicated_query.encode("ascii") if implicated_query is not None else None,
                           implicated_event.event.encode("ascii") if implicated_event is not None else None,
                           observed_contradiction)


def bind_birth_arm(record, case, *, role_tokens):
    """Return inspection-only generated spans; scan APIs never accept them back."""
    pairs = _expected_pairs(case, role_tokens)
    target = _select(record, pairs, case)
    return _bind(record, case, target)


def _semantic_source(binding):
    spans = []
    for observation in binding.observations:
        if scanner._public_identifier(observation.value):
            spans.append(scanner.SemanticSourceSpan(
                observation.path, observation.start, observation.end, "identifier", observation.value,
                observation.evidence + ":projection-sha256:" + binding.projection_sha256,
            ))
    for message, span in zip(binding.public_messages[1:], binding.message_spans[1:]):
        for line_index, line in enumerate(_tokens(message.content)):
            for token_index, (token, start, end) in enumerate(line):
                raw = token.encode("ascii")
                if raw in scanner.SHARED_ATOMS or raw in scanner.SHARED_LINES:
                    spans.append(scanner.SemanticSourceSpan(
                        f"/messages/{span.message_index}/syntax/{line_index}/{token_index}",
                        span.start + start, span.start + end, "syntax", raw,
                        f"source-message:{span.message_index}:sha256:{span.content_sha256}"
                        + ":projection-sha256:" + binding.projection_sha256,
                    ))
    return scanner.SemanticSource(binding.projection_bytes, tuple(sorted(spans, key=lambda item: item.start)))


def _scan(binding, inventory, *, source_semantic_occurrences=False):
    _require(type(source_semantic_occurrences) is bool, "boolean_source_semantic_occurrences_required")
    _require(type(inventory) is ScanInventory, "explicit ScanInventory required")
    _require(type(inventory.semantic_bytes) is bytes, "explicit semantic bytes required")
    for values in (inventory.future_identifiers, inventory.registered_routes):
        _require(type(values) is tuple and all(type(value) is bytes for value in values), "explicit immutable byte ledger required")
    report = scanner.scan_forward_targets(
        binding.projection_bytes, target=binding.target, phase=binding.phase, decision_index=binding.decision_index,
        semantic_bytes=inventory.semantic_bytes, fields=binding.fields,
        future_identifiers=inventory.future_identifiers, registered_routes=inventory.registered_routes,
        task_start=binding.task_start, task_goal=binding.task_goal, current=binding.current,
        implicated_query=binding.implicated_query, implicated_event=binding.implicated_event,
        observed_contradiction=binding.observed_contradiction,
        semantic_profile=inventory.semantic_profile,
        semantic_source=_semantic_source(binding) if source_semantic_occurrences else None,
    )
    return BirthScanReport(binding, report, sha256(inventory.semantic_bytes).hexdigest(),
                           inventory.future_identifiers, inventory.registered_routes, inventory.semantic_profile,
                           source_semantic_occurrences)


def scan_birth_arm(record, case, *, role_tokens, semantic_bytes, future_identifiers, registered_routes,
                   semantic_profile="legacy", source_semantic_occurrences=False):
    """Always reconstruct source bindings; never accept caller exemption spans."""
    binding = bind_birth_arm(record, case, role_tokens=role_tokens)
    return _scan(binding, ScanInventory(semantic_bytes, future_identifiers, registered_routes, semantic_profile),
                 source_semantic_occurrences=source_semantic_occurrences)


def scan_birth_pair(pair, case, *, role_tokens, closed_inventory, atom_inventory, source_semantic_occurrences=False):
    """Paired source validation with separate explicit inventory for each arm."""
    _require(type(pair) is targets.PairedTarget and type(pair.closed) is targets.ArmRecord
             and type(pair.atom_local) is targets.ArmRecord, "source PairedTarget required")
    _require(pair.closed.arm == "CLOSED" and pair.atom_local.arm == "ATOM_LOCAL"
             and pair.closed.unit is pair.atom_local.unit and pair.status == targets.STATUS,
             "shared paired target and source arm designations required")
    pairs = _expected_pairs(case, role_tokens)
    closed_target = _select(pair.closed, pairs, case)
    atom_target = _select(pair.atom_local, pairs, case)
    _require(closed_target == atom_target, "pair crosses decision boundaries")
    return PairedScanReport(_scan(_bind(pair.closed, case, closed_target), closed_inventory,
                                 source_semantic_occurrences=source_semantic_occurrences),
                            _scan(_bind(pair.atom_local, case, atom_target), atom_inventory,
                                  source_semantic_occurrences=source_semantic_occurrences))
