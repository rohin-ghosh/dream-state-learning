"""Finite v6 leak diagnostics, not an independent public-boundary admission gate.

The field schema classifies every constructor/record field before deriving
complete private values. Public wire identifiers, actions and responses are
not private aliases. Source paths are ownership evidence, never needles.
No full semantic object, pointer forms, scalar atoms or ID fragments are built.

The caller must obtain source, binding and inventories through independently
checked custody. Their agreement here is a consistency check, not validation
of allocation, public semantics, inventory completeness or native chat bytes.
Even a clear mutated candidate is not an admissible public boundary.
"""

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, fields
from hashlib import sha256
import re
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_future_inputs as future_module
from organism_v6 import composition_birth_stage2a_route_inputs as route_module
from organism_v6 import composition_birth_stage2a_route_scan as route_scan
from organism_v6 import composition_birth_stage2a_scan_inputs as scan_inputs
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6 import composition_birth_stage2a_worlds as worlds


SCHEMA_VERSION = "BIRTH_TYPED_PRIVATE_DIAGNOSTICS_V6"
STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = source_inputs.SCIENCE_GATES
FORBIDDEN_EDGE_LABELS = (b"LINK", b"OLD", b"NEW")
LIMITATIONS = (
    "Diagnostics only; exact source/public-boundary reconstruction is the admission boundary.",
    "Inventory/source agreement is not independent custody or allocation authentication.",
    "No semantic tree, native template, arbitrary route prose or scientific authorization.",
    "Raw private collisions are retained; only original fixed public syntax receives explicit receipts.",
)
_WORD_BYTES = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_/-")
_PROTOCOL_TOKENS = re.compile(rb"[A-Za-z0-9_/-]+")


def _schema(**rules):
    return MappingProxyType(rules)


SOURCE_FIELD_SCHEMA = MappingProxyType({
    birth.BirthCaseDescriptor: _schema(
        world="key_component", member="key_component", pair_index="number", bucket="number",
        pair_type="private_category", family="private_category", family_motif="private_category",
        flow="private_category", recovery_subtype="private_category", terminal_class="private_category",
        goal_side="private_category", goal_index="number", skin="number",
        recovery_match_id="case_reference", domain="private_category"),
    birth.BirthCase: _schema(
        descriptor="child", task="child", task_text="public_text", construction="child",
        trace="children", targets="children", facts="child", status="private_category",
        memo_sha256="digest", clarification_sha256="digest"),
    birth.BirthTarget: _schema(
        ordinal="number", phase="private_category", target_bytes="public_bytes", target_sha256="digest",
        command="public_text", operand="optional_public_id", trace_index="number",
        current_before="public_id", current_after="public_id", selection_index="optional_number"),
    birth.BirthTraceTurn: _schema(
        action="public_text", response="public_text", current_before="public_id",
        current_after="public_id", target_ordinal="optional_number"),
    birth.BirthTraceFacts: _schema(
        selected_query="public_id", failed_query="optional_public_id", failed_event="optional_public_id",
        failed_prediction="optional_public_id", failed_outcome="optional_public_id",
        corrective_query="optional_public_id", selected_event="public_id", selected_prediction="public_id",
        selected_outcome="public_id", final_current="public_id"),
    worlds.OrdinaryConstruction: _schema(
        domain="private_category", world="key_component", skin="number", scope="private_category",
        blocks="service_map", registry="registry", world_edges="world_edges",
        status="private_category", memo_sha256="digest"),
    wire.TaskState: _schema(start="public_id", goal="public_id", current="public_id"),
    wire.ServiceBlock: _schema(kind="public_text", rows="children", raw="public_text"),
    wire.RouteRow: _schema(route="public_id", node="public_id", goal="public_id", query="public_id"),
    wire.EventRow: _schema(
        event="public_id", node="public_id", goal="public_id", port="public_id",
        got="public_id", recover="public_id", receipt="public_id"),
    targets.TargetUnit: _schema(
        unit_id="private_unit_key", phase="private_category", target_bytes="public_bytes",
        target_sha256="digest", command="public_text", operand="optional_public_id",
        selection_index="optional_number"),
    targets.ArmRecord: _schema(
        arm="private_category", unit="child", prefix="children", prefix_sha256="digest",
        content_bytes="number", serialized_bytes="number"),
    targets.Message: _schema(role="public_text", content="public_text"),
})


class TypedScanError(ValueError):
    """An unhandled typed source surface or inconsistent diagnostic input."""


@dataclass(frozen=True)
class TypedPrivateValue:
    category: str
    value: bytes
    source_path: tuple[str, ...]


@dataclass(frozen=True)
class TypedPrivateOccurrence:
    category: str
    value: bytes
    form: str
    start: int
    end: int
    source_paths: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class TypedProtocolSource:
    message_start: int
    message_end: int
    message_sha256: str
    token_starts: frozenset[int]
    token_ends: frozenset[int]
    source_path: tuple[str, ...] = ("wire", "SYSTEM_MESSAGE")
    message_index: int = 0
    evidence: str = ""


@dataclass(frozen=True)
class TypedProtocolReceipt(TypedPrivateOccurrence):
    message_sha256: str
    message_span: tuple[int, int]
    protocol_source_path: tuple[str, ...]
    message_index: int
    evidence: str


def _require(condition, message):
    if not condition:
        raise TypedScanError(message)


def build_typed_private_basis(case, record, role_tokens) -> tuple[TypedPrivateValue, ...]:
    """Derive complete categorical/role/case/unit values with all source owners.

    All four case unit keys are included, not just the scheduled unit. A case
    reference is joined as world/member; neither component becomes a needle.
    Unknown fields/types fail with a source path instead of disappearing.
    This schema walk neither serializes nor atomizes the complete source.
    """
    _require(type(case) is birth.BirthCase and type(record) is targets.ArmRecord,
             "typed_case_and_record_required")
    _require(isinstance(role_tokens, Mapping), "typed_role_mapping_required")
    basis = []
    checked_types = set()

    def text(value, path):
        _require(type(value) is str and value.isascii() and "\0" not in value and "\r" not in value,
                 "invalid_source_text: " + repr(path))
        return value.encode("ascii")

    def add(category, value, path):
        raw = text(value, path)
        _require(bool(raw) and not raw.isdigit() and raw.lower() not in (b"true", b"false", b"null")
                 and not scanner._public_identifier(raw), "invalid_private_value: " + repr(path))
        basis.append(TypedPrivateValue(category, raw, path))

    def walk(value, path):
        rules = SOURCE_FIELD_SCHEMA.get(type(value))
        _require(rules is not None, "unhandled_source_type: " + repr(path))
        if type(value) not in checked_types:
            _require(tuple(field.name for field in fields(value)) == tuple(rules),
                     "unhandled_source_fields: " + repr(path))
            checked_types.add(type(value))
        for name, rule in rules.items():
            item, owner = getattr(value, name), path + (name,)
            if rule in ("private_category", "private_unit_key"):
                add(rule, item, owner)
            elif rule in ("public_text", "key_component", "digest"):
                text(item, owner)
            elif rule in ("public_id", "optional_public_id"):
                if item is not None or rule == "public_id":
                    _require(scanner._public_identifier(text(item, owner)),
                             "invalid_public_identifier: " + repr(owner))
            elif rule in ("number", "optional_number"):
                _require(type(item) is int or (item is None and rule == "optional_number"),
                         "invalid_source_number: " + repr(owner))
            elif rule == "public_bytes":
                _require(type(item) is bytes and item.isascii(), "invalid_source_bytes: " + repr(owner))
            elif rule == "case_reference":
                if item is not None:
                    _require(type(item) is tuple and len(item) == 2, "invalid_case_reference: " + repr(owner))
                    for component in item:
                        text(component, owner)
                    add("private_case_key", "/".join(item), owner)
            elif rule == "child":
                walk(item, owner)
            elif rule == "children":
                _require(type(item) is tuple, "immutable_source_sequence_required: " + repr(owner))
                for index, child in enumerate(item):
                    walk(child, owner + (str(index),))
            elif rule in ("service_map", "registry", "world_edges"):
                _require(isinstance(item, Mapping), "source_mapping_required: " + repr(owner))
                for key, child in item.items():
                    if rule == "world_edges":
                        _require(type(key) is tuple and len(key) == 2, "invalid_world_edge_key")
                        for token in (*key, child):
                            _require(scanner._public_identifier(text(token, owner)), "invalid_world_edge_id")
                    else:
                        text(key, owner)
                        if rule == "service_map":
                            walk(child, owner + (key,))
                        else:
                            text(child, owner + (key,))
            else:
                raise TypedScanError("unhandled_source_category: " + rule)

    walk(case, ("case",))
    walk(record, ("record",))
    _require({name for name, value in vars(type(case.descriptor)).items() if isinstance(value, property)}
             == {"case_id", "family_bit", "relation_slot"}, "unhandled_descriptor_properties")
    case_key = "/".join(case.descriptor.case_id)
    add("private_case_key", case_key, ("case", "descriptor", "case_id"))
    for index, target in enumerate(case.targets):
        add("private_unit_key", f"{case_key}/u{target.ordinal}", ("case", "targets", str(index), "ordinal"))
    _require(len(role_tokens) <= source_inputs.BOUNDS["role_entries"], "role_inventory_bound_exceeded")
    for role, token in role_tokens.items():
        raw_role = text(role, ("role_tokens",))
        _require(len(raw_role) <= source_inputs.BOUNDS["role_characters"] and b"/" in raw_role,
                 "invalid_complete_role_key")
        _require(scanner._public_identifier(text(token, ("role_tokens", role))), "invalid_role_token")
        add("private_role_key", role, ("role_tokens", role))
    return tuple(sorted(basis, key=lambda item: (item.category, item.value, item.source_path)))


def _fixed_protocol_source(source, binding):
    """Derive token boundaries from the fixed protocol, never private values."""
    fixed = wire.SYSTEM_MESSAGE.encode("ascii")
    digest = sha256(fixed).hexdigest()
    message = targets.Message("system", wire.SYSTEM_MESSAGE)
    _require(bool(source.record.prefix) and source.record.prefix[0] == message
             and bool(binding.public_messages) and binding.public_messages[0] == message
             and binding.projection_bytes[:len(fixed) + 1] == fixed + b"\n"
             and bool(binding.message_spans), "fixed_protocol_source_mismatch")
    span = binding.message_spans[0]
    _require(span.message_index == 0 and span.role == "system" and span.start == 0
             and span.end == len(fixed) and span.content_sha256 == digest
             and span.source_trace_index is None, "fixed_protocol_span_mismatch")
    tokens = tuple(_PROTOCOL_TOKENS.finditer(fixed))
    return TypedProtocolSource(0, len(fixed), digest,
                               frozenset(token.start() for token in tokens),
                               frozenset(token.end() for token in tokens),
                               evidence="fixed-system-sha256:" + digest)


def _fixed_syntax_sources(source, binding):
    """Keep only source-derived syntax tokens from exact original messages."""
    _require(binding.public_messages == source.record.prefix
             and len(binding.message_spans) == len(source.record.prefix), "fixed_syntax_messages_mismatch")
    offset = 0
    for index, (message, span) in enumerate(zip(source.record.prefix, binding.message_spans)):
        raw = message.content.encode("ascii")
        end = offset + len(raw)
        _require(span.message_index == index and span.role == message.role
                 and span.start == offset and span.end == end
                 and span.content_sha256 == sha256(raw).hexdigest()
                 and binding.projection_bytes[offset:end] == raw,
                 "fixed_syntax_message_span_mismatch")
        if index + 1 < len(source.record.prefix):
            _require(binding.projection_bytes[end:end + 1] == b"\n", "fixed_syntax_message_boundary_mismatch")
        offset = end + 1
    _require(offset - 1 == len(binding.projection_bytes)
             and sha256(binding.projection_bytes).hexdigest() == binding.projection_sha256,
             "fixed_syntax_projection_mismatch")
    syntax_sources = []
    for token in scan_inputs._semantic_source(binding).spans:
        if token.kind != "syntax":
            continue
        index = int(token.path.split("/")[2])
        message = binding.message_spans[index]
        _require(token.value in scanner.SHARED_ATOMS or token.value in scanner.SHARED_LINES,
                 "nonfixed_syntax_token")
        _require(not scanner._public_identifier(token.value)
                 and message.start <= token.start < token.end <= message.end
                 and binding.projection_bytes[token.start:token.end] == token.value,
                 "invalid_fixed_syntax_token_span")
        syntax_sources.append(TypedProtocolSource(
            message.start, message.end, message.content_sha256,
            frozenset((token.start,)), frozenset((token.end,)),
            tuple(token.path.lstrip("/").split("/")), index, token.evidence,
        ))
    return tuple(syntax_sources)


def _whole_protocol_span(protocol, start, end):
    return protocol is not None and start in protocol.token_starts and end in protocol.token_ends and start < end


def _typed_occurrences(prefix, basis, *, protocol=None, syntax_sources=()):
    owners = defaultdict(list)
    for item in basis:
        owners[item.category, item.value].append(item.source_path)
    views = scanner._views(prefix)
    syntax_spans = {(next(iter(source.token_starts)), next(iter(source.token_ends)))
                    for source in syntax_sources}
    occurrences = []
    for (category, value), paths in sorted(owners.items()):
        needles = tuple(b"\n".join(lines) for lines in scanner.normalize_lines(value))
        for (form, haystack, offsets), needle in zip(views, needles):
            _require(bool(needle), "empty_typed_needle")
            cursor = 0
            while (found := haystack.find(needle, cursor)) >= 0:
                finish, cursor = found + len(needle), found + 1
                start, end = ((found, finish) if offsets is None
                              else (offsets[found][0], offsets[finish - 1][1]))
                if (((start and prefix[start - 1] in _WORD_BYTES)
                     or (end < len(prefix) and prefix[end] in _WORD_BYTES))
                        and not _whole_protocol_span(protocol, start, end)
                        and (start, end) not in syntax_spans):
                    continue
                occurrences.append(TypedPrivateOccurrence(category, value, form, start, end, tuple(paths)))
                _require(len(occurrences) <= scanner.BOUNDS["hits"], "typed_scanner_hit_bound_exceeded")
    return tuple(occurrences)


def _partition_typed_occurrences(prefix, original, protocol, occurrences, *, syntax_sources=()):
    """Receipt exact original protocol tokens, not values or whole candidates.

    Source-token matches survive boundary damage as unreceipted findings.
    Ordinary opaque-ID fragments elsewhere remain outside the typed basis.
    """
    syntax_spans = {(next(iter(source.token_starts)), next(iter(source.token_ends))): source
                    for source in syntax_sources}
    issues, receipts = [], []
    for item in occurrences:
        owner = protocol if _whole_protocol_span(protocol, item.start, item.end) else syntax_spans.get(
            (item.start, item.end))
        whole_word = (not item.start or prefix[item.start - 1] not in _WORD_BYTES)
        whole_word = whole_word and (item.end == len(prefix) or prefix[item.end] not in _WORD_BYTES)
        exact_message = False
        if owner is not None:
            left = max(0, owner.message_start - 1)
            right = min(len(original), owner.message_end + 1)
            exact_message = (prefix[left:right] == original[left:right]
                             and (owner.message_end < len(original)
                                  or prefix[owner.message_end:owner.message_end + 1] in (b"", b"\n")))
        if (item.category.startswith("private_") and exact_message and whole_word
                and prefix[:item.end] == original[:item.end]):
            receipts.append(TypedProtocolReceipt(
                item.category, item.value, item.form, item.start, item.end, item.source_paths,
                owner.message_sha256, (owner.message_start, owner.message_end), owner.source_path,
                owner.message_index, owner.evidence,
            ))
        else:
            issues.append(item)
    return tuple(issues), tuple(receipts)


@dataclass(frozen=True)
class TypedBirthScanReport:
    source: source_inputs.ValidatedBirthSource
    binding: scan_inputs.BoundScanInputs
    future_inputs: future_module.BirthFutureInputs
    route_inputs: route_module.BirthRouteInputs
    candidate_prefix: bytes
    private_basis: tuple[TypedPrivateValue, ...]
    typed_occurrences: tuple[TypedPrivateOccurrence, ...]
    typed_receipts: tuple[TypedProtocolReceipt, ...]
    typed_issues: tuple[TypedPrivateOccurrence, ...]
    forward: scanner.ScanReport
    route: route_scan.RouteScan

    status = STATUS
    schema_version = SCHEMA_VERSION
    science_gates = SCIENCE_GATES
    limitations = LIMITATIONS
    inventory_completeness_verified = False
    native_chat_bytes_verified = False
    independent_source_authentication = False

    @property
    def content_scan(self):
        return self.forward

    @property
    def route_scan(self):
        return self.route

    @property
    def private_issues(self):
        return tuple(item for item in self.typed_issues if item.category.startswith("private_"))

    @property
    def issues(self):
        return self.typed_issues + self.forward.issues + self.route.issues

    @property
    def passed(self):
        return not self.typed_issues and self.forward.passed and self.route.registered_grammar_clear

    @property
    def supplied_projection_clear(self):
        return self.passed

    @property
    def candidate_matches_projection(self):
        return self.candidate_prefix == self.binding.projection_bytes

    @property
    def counts(self):
        counts = Counter(item.category for item in self.private_basis)
        counts.update(private_values=len(self.private_basis),
                      private_unique_values=len({item.value for item in self.private_basis}),
                      future_identifiers=len(self.future_inputs.future_identifiers),
                      route_transitions=len(self.route_inputs.transitions),
                      typed_occurrences=len(self.typed_occurrences), typed_receipts=len(self.typed_receipts),
                      typed_issues=len(self.typed_issues), forward_issues=len(self.forward.issues),
                      route_issues=len(self.route.issues))
        return MappingProxyType(dict(counts))


def scan_typed_birth(*, source: source_inputs.ValidatedBirthSource, binding: scan_inputs.BoundScanInputs,
                     future_inputs: future_module.BirthFutureInputs, route_inputs: route_module.BirthRouteInputs,
                     candidate_prefix: bytes | None = None) -> TypedBirthScanReport:
    """Compose independent leak checks; no caller clearance or authority flag.

    Candidate mutations retain only original fields whose causal prefix through
    the field endpoint is unchanged. Route endpoint authentication remains the
    existing matcher, including its full-prefix-through-second-endpoint rule.
    Only independently fixed original system tokens and source-derived syntax
    tokens can receipt private collisions. Identifier/task/history values and
    candidate equality confer no exemption.
    """
    _require(type(source) is source_inputs.ValidatedBirthSource, "validated_source_type_required")
    _require(type(binding) is scan_inputs.BoundScanInputs, "bound_scan_inputs_required")
    _require(type(future_inputs) is future_module.BirthFutureInputs, "typed_future_inputs_required")
    _require(type(route_inputs) is route_module.BirthRouteInputs, "typed_route_inputs_required")
    for supplied in (future_inputs.source, route_inputs.source):
        _require(supplied is source or supplied == source, "diagnostic_source_mismatch")
    _require(future_inputs.binding == binding and binding.source_prefix_sha256 == source.record.prefix_sha256
             and binding.target == source.record.unit.target_bytes and binding.phase == source.record.unit.phase,
             "diagnostic_binding_mismatch")
    prefix = binding.projection_bytes if candidate_prefix is None else candidate_prefix
    scanner.normalize_lines(prefix)
    protocol = _fixed_protocol_source(source, binding)
    syntax_sources = _fixed_syntax_sources(source, binding)
    basis = build_typed_private_basis(source.case, source.record, source.role_tokens)
    labels = tuple(TypedPrivateValue("forbidden_edge_label", label,
                                    ("contract", "forbidden_edge_labels", label.decode("ascii")))
                   for label in FORBIDDEN_EDGE_LABELS)
    typed_occurrences = _typed_occurrences(prefix, basis + labels, protocol=protocol, syntax_sources=syntax_sources)
    typed_issues, typed_receipts = _partition_typed_occurrences(
        prefix, binding.projection_bytes, protocol, typed_occurrences, syntax_sources=syntax_sources,
    )
    causal_fields = tuple(field for field in binding.fields
                          if prefix[:field.end] == binding.projection_bytes[:field.end])
    forward = scanner.scan_forward_targets(
        prefix, target=binding.target, phase=binding.phase, decision_index=binding.decision_index,
        semantic_bytes=b"{}", fields=causal_fields,
        future_identifiers=tuple(sorted(future_inputs.future_identifiers)), registered_routes=(),
        task_start=binding.task_start, task_goal=binding.task_goal, current=binding.current,
        implicated_query=binding.implicated_query, implicated_event=binding.implicated_event,
        observed_contradiction=binding.observed_contradiction,
    )
    route = route_scan._scan_from_inputs(route_inputs, binding, candidate_prefix=prefix)
    return TypedBirthScanReport(source, binding, future_inputs, route_inputs, prefix, basis,
                                typed_occurrences, typed_receipts, typed_issues, forward, route)
