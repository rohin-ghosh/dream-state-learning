"""Bounded, pure Stage2A scanners, not a protocol or provenance authenticator.

Callers bind every field span to authentic pre-decision evidence and supply the
complete pre-public semantic object, future-ID ledger, and registered routes.
Missing source bindings stay with Main; a clean partial report grants nothing.
No escape decoding is performed on material bytes. JSON is decoded only when
reading a supplied canonical semantic object or the pinned public certificate.
The causal-occurrence clarifications permit two operand-only service spans:
CHECK's implicated issued QUERY and CONTINUE's EVENT GOT equal to latest
CURRENT with a well-typed EVENT owner. V2 supersedes only v1's selected-owner
condition; original owner and service provenance remain intact. Neither
authorizes future IDs, actions, semantic or route leaks.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import re
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6.composition_birth_stage2a_primitives import parse_canonical_json


STATUS = "PARTIAL_SOURCE_ONLY"
MEMO_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"
V3_SHA256 = "da833b9df37930d0b06f9206e5fa47d5b436b325e833e6f6b2f4221f4d8808d1"
CAUSAL_OCCURRENCE_SHA256 = "37398723e197fcba2b24a505f06395c311d3dfcd488e9fc4026d883f6aeb4b07"
CAUSAL_OCCURRENCE_V2_SHA256 = "a08b6ff2df927552f6c96917f58181f56f17f456643afaee28c8bb2dd7722b16"
CERTIFICATE_SHA256 = "e90c7389e8811c4fe9c870119b76226ec070c47c99ea6ba8f075d89c5ba234b5"
CERTIFICATE_LENGTH = 1025
SCIENCE_GATES = MappingProxyType(dict.fromkeys((
    "GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU",
    "GO_CLAIM", "full_protocol", "full_provenance", "C11_readiness",
), False))
BOUNDS = MappingProxyType({"bytes": 1048576, "fields": 4096, "leaves": 4096, "nodes": 32768,
                          "aliases": 32768, "depth": 64, "hits": 16384,
                          "domains": 16, "future_identifiers": 16384})
SEMANTIC_PROFILES = MappingProxyType({
    "birth_full_v1": MappingProxyType({"bytes": 16777216, "leaves": 131072,
                                       "nodes": 524288, "aliases": 524288, "depth": 64}),
    "birth_full_v2": MappingProxyType({"bytes": 16777216, "leaves": 262144,
                                       "nodes": 524288, "aliases": 524288, "depth": 64}),
})
LIMITATIONS = (
    "Caller must authenticate field spans, chronology, implicated IDs, and latest CURRENT.",
    "Caller must supply complete semantic, future-ID, and registered-route inventories.",
    "No escape decoding, arbitrary regex engine, topology proof, or transcript reconstruction.",
    "An empty compact alias/route is unsupported, not an implicit exemption.",
    "No full protocol/provenance/C11 readiness; input bounds are implementation limits.",
)
SHARED_LINES = frozenset(line.encode("ascii") for line in wire.SYSTEM_MESSAGE.split("\n")) | frozenset((
    b"TASK", b"ACK", b"WORLD", b"SERVICE", b"ROUTES", b"EVENTS", b"MISS",
    b"CANARY", b"COPY EXACTLY", b"STOP",
))
SHARED_ATOMS = frozenset(b"""THINK KEEP REVISE READ INDEX RELATION STEP STOP TASK START GOAL CURRENT
ACK WORLD SERVICE ROUTES ROUTE AT FOR QUERY EVENTS EVENT DID GOT RECOVER
EVIDENCE MISS CANARY COPY EXACTLY ID_NODE ID_QUERY ID_EVENT ID_ROUTE
ID_PORT ID_RECEIPT _ - < >""".split())
PROTECTED_ROOTS = frozenset((
    "case_id", "causal_pair_id", "core", "evaluator", "factors", "future", "mutation",
    "oracle", "recovery_match_id", "role_keys", "target", "unit_id",
))
FORBIDDEN_CORE_LABELS = (
    b"PCFL_EVENT_LINK", b"PCFL_OLD_NEW", b"PCFL_ROUTE_PREFIX",
    b"GOAL_BRAID_CROSS_ROUTE", b"GOAL_BRAID_DELAYED_BRANCH", b"GOAL_BRAID_OLD_PREFIX",
)
_IDENTIFIERS = tuple((re.compile(pattern.encode("ascii")), ("ID_" + kind.upper()).encode("ascii"))
                     for kind, pattern in wire.IDENTIFIERS.items())
_RUN = re.compile(rb"[A-Za-z0-9]+")
_SPACES = re.compile(rb"[ \t]+")
_COMPACT_DELETE = b"_- <>"
_FIELD_ORIGINS = MappingProxyType({
    "route_query": "service", "event_did": "service", "event_recover": "service",
    "event_got": "service",
    "selected_event": "service", "issued_query": "actor", "think_implicated": "actor",
    "task_start": "task", "task_goal": "task", "current": "host",
    "task_current": "task", "protocol": "system",
})
_FIELD_KINDS = MappingProxyType({
    "route_query": ("query",), "event_did": ("port",), "event_recover": ("query",),
    "event_got": ("node",),
    "selected_event": ("event",), "issued_query": ("query",),
    "think_implicated": ("event", "query"), "task_start": ("node",),
    "task_goal": ("node",), "current": ("node",), "task_current": ("node",),
})


def _bytes(raw):
    if type(raw) is not bytes or len(raw) > BOUNDS["bytes"]:
        raise ValueError("bounded_bytes_required")
    if not raw.isascii() or b"\r" in raw or b"\0" in raw:
        raise ValueError("invalid_ascii_utf8_lf_bytes")
    return raw


def normalize_lines(raw):
    """Return (literal, normalized, compact) tuples, retaining empty LF lines."""
    literal = tuple(_bytes(raw).split(b"\n"))
    normalized = tuple(_SPACES.sub(b" ", line.upper()) for line in literal)
    compact = tuple(line.translate(None, _COMPACT_DELETE) for line in normalized)
    return literal, normalized, compact


def _identifier(raw):
    return any(pattern.fullmatch(raw) for pattern, marker in _IDENTIFIERS)


def _public_identifier(raw, kinds=tuple(wire.IDENTIFIERS)):
    return (type(raw) is bytes and not raw.endswith(b"_AAAAAAAAAAAA")
            and any(re.fullmatch(wire.IDENTIFIERS[kind].encode("ascii"), raw) for kind in kinds))


def _lex(raw):
    atoms, identifiers = [], []
    for line in _bytes(raw).split(b"\n"):
        if line in SHARED_LINES:
            continue
        cursor = 0
        while cursor < len(line):
            matches = [(match, marker) for pattern, marker in _IDENTIFIERS
                       if (match := pattern.match(line, cursor)) is not None]
            if matches:
                match, marker = max(matches, key=lambda item: item[0].end())
                atoms.append(marker)
                identifiers.append(match.group())
                cursor = match.end()
            elif (match := _RUN.match(line, cursor)) is not None:
                atoms.append(match.group().upper())
                cursor = match.end()
            else:
                if line[cursor:cursor + 1] in (b"_", b"-", b"<", b">"):
                    atoms.append(line[cursor:cursor + 1])
                cursor += 1
    return tuple(atoms), frozenset(identifiers)


def semantic_atoms(raw):
    """The v3 §6.2 cursor lexer: no escapes, camel splitting, or ID suffixes."""
    return _lex(raw)[0]


def extract_namespace_certificate(document):
    """Extract one marker pair from supplied UTF-8 document bytes; never read a path."""
    if type(document) is not bytes or len(document) > BOUNDS["bytes"]:
        raise ValueError("bounded_document_bytes_required")
    try:
        document.decode("utf-8")
    except UnicodeError as error:
        raise ValueError("invalid_document_utf8") from error
    if b"\r" in document or b"\0" in document:
        raise ValueError("invalid_document_lf")
    lines = document.split(b"\n")
    begins = [index for index, line in enumerate(lines) if line == b"BEGIN_NAMESPACE_CERTIFICATE_V1"]
    ends = [index for index, line in enumerate(lines) if line == b"END_NAMESPACE_CERTIFICATE_V1"]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        raise ValueError("exactly_one_ordered_certificate_pair_required")
    payload = b"\n".join(lines[begins[0] + 1:ends[0]])
    validate_namespace_certificate(payload)
    return payload


@dataclass(frozen=True)
class CertificateCheck:
    sha256: str
    public_regexes: tuple[str, ...]
    tiny_regexes: tuple[str, ...]
    tiny_source_sha256: str
    tiny_source_checked: bool
    status: str = STATUS


def validate_namespace_certificate(payload, *, tiny_source=None):
    """Enforce the pinned bytes (therefore all exact schema keys/types/claims).

    Optionally hash supplied tiny source bytes without importing or executing it.
    Omitting those bytes never claims that its live source hash was checked.
    """
    _bytes(payload)
    if len(payload) != CERTIFICATE_LENGTH or sha256(payload).hexdigest() != CERTIFICATE_SHA256:
        raise ValueError("namespace_certificate_pin_mismatch")
    certificate = parse_canonical_json(payload)
    tiny = certificate["tiny_fixture"]
    if tiny_source is not None:
        if type(tiny_source) is not bytes or len(tiny_source) > BOUNDS["bytes"]:
            raise ValueError("bounded_tiny_source_bytes_required")
        if sha256(tiny_source).hexdigest() != tiny["sha256"]:
            raise ValueError("tiny_source_pin_mismatch")
    return CertificateCheck(CERTIFICATE_SHA256,
                            tuple(sorted({regex for claim in certificate["claims"]
                                          for regex in claim["public_identifier_regexes"]})),
                            tuple(tiny["identifier_regexes"]), tiny["sha256"], tiny_source is not None)


def regex_languages_intersect(left, right):
    """Symbolic intersection for the certificate's literal+[A-Z2-7]{n} languages only."""
    def positions(pattern):
        if type(pattern) is not str:
            raise ValueError("unsupported_namespace_regex")
        match = re.fullmatch(r"([A-Z0-9_]+)\[A-Z2-7\]\{([1-9][0-9]*)\}", pattern)
        if match is None or len(pattern) > 128 or int(match[2]) > 128:
            raise ValueError("unsupported_namespace_regex")
        alphabet = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
        return tuple(frozenset(char) for char in match[1]) + (alphabet,) * int(match[2])
    left_positions, right_positions = positions(left), positions(right)
    return len(left_positions) == len(right_positions) and all(
        left_chars & right_chars for left_chars, right_chars in zip(left_positions, right_positions))


@dataclass(frozen=True)
class NamespaceReport:
    issues: tuple[tuple[str, str, str, bytes], ...]
    domains: tuple[str, ...]
    certificate: CertificateCheck
    status: str = STATUS
    limitations: tuple[str, ...] = LIMITATIONS

    @property
    def passed(self):
        return not self.issues


def check_namespace_separation(domains, *, certificate_payload, tiny_source=None):
    """Check supplied domain/pool byte intersections, not domain inventory completeness."""
    certificate = validate_namespace_certificate(certificate_payload, tiny_source=tiny_source)
    if not isinstance(domains, Mapping) or not 2 <= len(domains) <= BOUNDS["domains"]:
        raise ValueError("bounded_domain_mapping_required")
    if any(type(name) is not str or not name or not name.isascii() for name in domains):
        raise ValueError("invalid_domain_name")
    snapshots = {}
    issues = []
    for name, raw in sorted(domains.items()):
        atoms, identifiers = _lex(raw)
        lines = frozenset(_bytes(raw).split(b"\n")) - SHARED_LINES
        snapshots[name] = (lines, frozenset(atoms) - SHARED_ATOMS, identifiers)
        for regex in certificate.public_regexes + certificate.tiny_regexes:
            if any(regex_languages_intersect(pattern, regex) for pattern in wire.IDENTIFIERS.values()):
                issues.append(("regex_intersection", name, "certificate", regex.encode("ascii")))
    for left, right in combinations(sorted(snapshots), 2):
        for kind, left_values, right_values in zip(("line", "atom", "identifier"),
                                                  snapshots[left], snapshots[right]):
            issues.extend((kind, left, right, value) for value in sorted(left_values & right_values))
            if len(issues) > BOUNDS["hits"]:
                raise ValueError("scanner_hit_bound_exceeded")
    return NamespaceReport(tuple(issues), tuple(sorted(snapshots)), certificate)


def _semantic_limits(profile):
    if type(profile) is not str or profile not in ("legacy", *SEMANTIC_PROFILES):
        raise ValueError("unknown_semantic_profile")
    return BOUNDS if profile == "legacy" else SEMANTIC_PROFILES[profile]


def _semantic_object(raw, *, semantic_profile="legacy"):
    limits = _semantic_limits(semantic_profile)
    if type(raw) is not bytes or len(raw) > limits["bytes"]:
        raise ValueError("bounded_semantic_bytes_required")
    if not raw.isascii() or b"\r" in raw or b"\0" in raw:
        raise ValueError("invalid_ascii_utf8_lf_bytes")
    value = parse_canonical_json(raw)
    if type(value) is not dict:
        raise ValueError("semantic_object_required")
    return value


def _nodes(value, path=(), *, semantic_profile="legacy"):
    if len(path) > _semantic_limits(semantic_profile)["depth"]:
        raise ValueError("semantic_depth_bound_exceeded")
    yield path, value
    if type(value) is dict:
        for key in sorted(value):
            yield from _nodes(value[key], path + (key,), semantic_profile=semantic_profile)
    elif type(value) is list:
        for index, item in enumerate(value):
            yield from _nodes(item, path + (str(index),), semantic_profile=semantic_profile)


def _leaves(value, *, semantic_profile="legacy"):
    limits = _semantic_limits(semantic_profile)
    for count, (path, item) in enumerate(_nodes(value, semantic_profile=semantic_profile), 1):
        if count > limits["nodes"]:
            raise ValueError("semantic_node_bound_exceeded")
        if type(item) not in (dict, list):
            yield path, item


def _pointer(path):
    return ("/" + "/".join(part.replace("~", "~0").replace("/", "~1") for part in path)).encode("ascii")


def derive_semantic_aliases(semantic_bytes, *, semantic_profile="legacy"):
    """Derive the exhaustive v3 §8 ledger; no hand-entered alias extension.

    Causal operands are complete public IDs and are already excluded exactly.
    No global exemption is inferred from an operand-like substring.
    """
    limits = _semantic_limits(semantic_profile)
    semantic = _semantic_object(semantic_bytes, semantic_profile=semantic_profile)
    aliases = set()
    for count, (path, value) in enumerate(_leaves(semantic, semantic_profile=semantic_profile), 1):
        if count > limits["leaves"]:
            raise ValueError("semantic_leaf_bound_exceeded")
        if path[0] not in PROTECTED_ROOTS:
            continue
        if type(value) is str:
            scalar = value.encode("ascii")
            tagged = b"STR:" + scalar
        elif value is None:
            scalar, tagged = b"null", b"NULL"
        elif type(value) is bool:
            scalar = b"true" if value else b"false"
            tagged = b"BOOL:" + scalar
        else:
            scalar = str(value).encode("ascii")
            tagged = b"INT:" + scalar
        pointer = _pointer(path)
        for proposal in (pointer, path[-1].encode("ascii"), scalar, pointer + b"=" + tagged,
                         *semantic_atoms(scalar)):
            if (len(proposal) >= 3 and proposal not in SHARED_LINES and proposal not in SHARED_ATOMS
                    and not _identifier(proposal)):
                aliases.add(proposal)
        if len(aliases) > limits["aliases"]:
            raise ValueError("semantic_alias_bound_exceeded")
    return tuple(sorted(aliases))


def semantic_alias_ledger(semantic_bytes, *, semantic_profile="legacy"):
    return b"\n".join(derive_semantic_aliases(semantic_bytes, semantic_profile=semantic_profile))


def forbidden_semantic_labels(semantic_bytes, *, semantic_profile="legacy"):
    """Report certificate-label aliases anywhere, and LINK/OLD/NEW edge labels.

    Edge recognition is deliberately limited to a `label` leaf under `edges`;
    this is not an alternative graph-schema checker.
    """
    limits = _semantic_limits(semantic_profile)
    semantic = _semantic_object(semantic_bytes, semantic_profile=semantic_profile)
    forbidden = {label.translate(None, _COMPACT_DELETE) for label in FORBIDDEN_CORE_LABELS}
    issues = []
    for count, (path, value) in enumerate(_nodes(semantic, semantic_profile=semantic_profile), 1):
        if count > limits["nodes"]:
            raise ValueError("semantic_node_bound_exceeded")
        for text in path[-1:] + ((value,) if type(value) is str else ()):
            compact = b"\n".join(normalize_lines(text.encode("ascii"))[2])
            if any(label in compact for label in forbidden):
                issues.append((_pointer(path), text.encode("ascii")))
        if path and path[-1] == "label" and "edges" in path and type(value) is str:
            if b"\n".join(normalize_lines(value.encode("ascii"))[2]) in (b"LINK", b"OLD", b"NEW"):
                issues.append((_pointer(path), value.encode("ascii")))
    return tuple(sorted(set(issues)))


@dataclass(frozen=True)
class PublicField:
    """Exact prefix value span plus caller-bound source evidence, not a trusted claim.

    `observed_at` is a trace index strictly before `decision_index`; `owner`
    identifies the implicated event for RECOVER and the original well-typed
    EVENT for GOT (not necessarily selected). `current`/`task_current` must
    identify the latest state (including Builder's authentic retained boundary).
    """
    path: str
    start: int
    end: int
    kind: str
    origin: str
    observed_at: int
    evidence: str
    owner: bytes | None = None


@dataclass(frozen=True)
class SemanticSourceSpan:
    path: str
    start: int
    end: int
    kind: str
    value: bytes
    evidence: str


@dataclass(frozen=True)
class SemanticSource:
    original_prefix: bytes
    spans: tuple[SemanticSourceSpan, ...]


def _validate_semantic_source(prefix, source):
    if source is None:
        return ()
    if type(source) is not SemanticSource:
        raise ValueError("typed_semantic_source_required")
    original = _bytes(source.original_prefix)
    if not original or not prefix.startswith(original):
        raise ValueError("semantic_source_prefix_changed")
    if type(source.spans) is not tuple or len(source.spans) > BOUNDS["fields"]:
        raise ValueError("bounded_semantic_source_spans_required")
    previous_end = 0
    paths = set()
    for span in source.spans:
        if (type(span) is not SemanticSourceSpan or type(span.start) is not int
                or type(span.end) is not int or not previous_end <= span.start < span.end <= len(original)
                or type(span.path) is not str or not span.path or not span.path.isascii()
                or span.path in paths or type(span.evidence) is not str
                or not span.evidence or not span.evidence.isascii()
                or type(span.value) is not bytes or original[span.start:span.end] != span.value
                or (span.start and original[span.start - 1:span.start] not in (b" ", b"\t", b"\n"))
                or (span.end < len(prefix) and prefix[span.end:span.end + 1] not in (b" ", b"\t", b"\n"))):
            raise ValueError("invalid_semantic_source_span")
        if span.kind == "identifier":
            if not _public_identifier(span.value):
                raise ValueError("complete_semantic_source_identifier_required")
        elif span.kind == "syntax":
            if span.value not in SHARED_ATOMS and span.value not in SHARED_LINES:
                raise ValueError("shared_semantic_source_syntax_required")
        else:
            raise ValueError("invalid_semantic_source_kind")
        paths.add(span.path)
        previous_end = span.end
    return source.spans


@dataclass(frozen=True)
class Occurrence:
    category: str
    value: bytes
    form: str
    start: int
    end: int
    field_path: str | None = None
    evidence: str | None = None


@dataclass(frozen=True)
class ScanReport:
    issues: tuple[Occurrence, ...]
    receipts: tuple[Occurrence, ...]
    semantic_issues: tuple[tuple[bytes, bytes], ...]
    aliases: tuple[bytes, ...]
    status: str = STATUS
    limitations: tuple[str, ...] = LIMITATIONS

    @property
    def passed(self):
        return not self.issues and not self.semantic_issues


def _views(raw):
    normalized, offsets = bytearray(), []
    cursor = 0
    while cursor < len(raw):
        start = cursor
        if raw[cursor] in (32, 9):
            while cursor < len(raw) and raw[cursor] in (32, 9):
                cursor += 1
            normalized.append(32)
        else:
            normalized.extend(raw[cursor:cursor + 1].upper())
            cursor += 1
        offsets.append((start, cursor))
    compact = bytearray()
    compact_offsets = []
    for char, offset in zip(normalized, offsets):
        if char not in _COMPACT_DELETE:
            compact.append(char)
            compact_offsets.append(offset)
    return (("literal", raw, None), ("normalized", bytes(normalized), offsets),
            ("compact", bytes(compact), compact_offsets))


def _validate_fields(prefix, fields, decision_index):
    if type(fields) not in (tuple, list) or len(fields) > BOUNDS["fields"]:
        raise ValueError("bounded_public_fields_required")
    paths = set()
    previous_end = 0
    if any(type(field) is not PublicField for field in fields):
        raise ValueError("typed_public_fields_required")
    if any(type(field.start) is not int or type(field.end) is not int for field in fields):
        raise ValueError("integer_field_offsets_required")
    for field in sorted(fields, key=lambda field: field.start):
        if (type(field.start) is not int or type(field.end) is not int
                or not previous_end <= field.start < field.end <= len(prefix)):
            raise ValueError("invalid_or_overlapping_field_span")
        previous_end = field.end
        if (type(field.path) is not str or not field.path.startswith("/") or not field.path.isascii()
                or field.path in paths or type(field.evidence) is not str or not field.evidence
                or not field.evidence.isascii()):
            raise ValueError("unique_field_path_and_evidence_required")
        paths.add(field.path)
        _bytes(field.path.encode("ascii"))
        _bytes(field.evidence.encode("ascii"))
        if (type(field.kind) is not str or field.kind not in _FIELD_ORIGINS
                or field.origin != _FIELD_ORIGINS[field.kind]):
            raise ValueError("invalid_typed_field_origin")
        if type(field.observed_at) is not int or not 0 <= field.observed_at < decision_index:
            raise ValueError("field_not_observed_before_decision")
        value = prefix[field.start:field.end]
        if field.kind == "protocol":
            if value != wire.SYSTEM_MESSAGE.encode("ascii"):
                raise ValueError("protocol_bytes_mismatch")
        elif not _public_identifier(value, _FIELD_KINDS[field.kind]):
            raise ValueError("public_field_requires_exact_typed_identifier")
        if field.owner is not None and not _public_identifier(field.owner, ("event",)):
            raise ValueError("invalid_field_owner")


def scan_forward_targets(prefix, *, target, phase, decision_index, semantic_bytes,
                         fields=(), future_identifiers=(), registered_routes=(),
                         task_start=None, task_goal=None, current=None,
                         implicated_query=None, implicated_event=None,
                         observed_contradiction=False, semantic_profile="legacy", semantic_source=None):
    """Scan only the next target/future ledger, not every past truthful answer.

    Phases: SEEK, PROSPECT, CHECK (or READ_CHECK/STEP_CHECK), CONTINUE.
    Supplied spans authorize exact operands only, never full scheduled actions
    or metadata. Repeating the *next* full action still fails v2 §8.2 even if
    historical; a different authentic past action is not automatically a leak.
    In the exact fixed protocol, STOP prose references are not full action
    lines; only its standalone grammar line gets the full-target receipt.
    Outside that protocol, even embedded/compact STOP answer text is rejected.
    """
    _bytes(prefix)
    _bytes(target)
    semantic_spans = _validate_semantic_source(prefix, semantic_source)
    if type(decision_index) is not int or decision_index < 1:
        raise ValueError("positive_decision_index_required")
    if type(observed_contradiction) is not bool:
        raise ValueError("boolean_contradiction_required")
    action = wire.parse_action(target.decode("ascii"))
    phases = {"SEEK": ("READ", "RELATION"), "PROSPECT": ("STEP", None),
              "CHECK": ("THINK", action.verb), "READ_CHECK": ("THINK", "REVISE"),
              "STEP_CHECK": ("THINK", action.verb), "CONTINUE": (action.operation, action.verb)}
    if type(phase) is not str or phase not in phases or phases[phase] != (action.operation, action.verb):
        raise ValueError("target_phase_mismatch")
    if phase == "CONTINUE" and (action.operation, action.verb) not in (("STOP", None), ("READ", "INDEX")):
        raise ValueError("target_phase_mismatch")
    operand = action.operand.encode("ascii") if action.operand is not None else None
    if operand is not None and not _public_identifier(operand):
        raise ValueError("invalid_target_identifier")
    if ((phase == "READ_CHECK" and not _public_identifier(operand, ("query",)))
            or (phase == "STEP_CHECK" and not _public_identifier(operand, ("event",)))):
        raise ValueError("target_phase_operand_mismatch")
    for value, kind in ((task_start, "node"), (task_goal, "node"), (current, "node"),
                        (implicated_query, "query"), (implicated_event, "event")):
        if value is not None and not _public_identifier(value, (kind,)):
            raise ValueError("invalid_context_identifier")
    _validate_fields(prefix, fields, decision_index)
    for values, bound in ((future_identifiers, BOUNDS["future_identifiers"]),
                          (registered_routes, BOUNDS["fields"])):
        if type(values) not in (tuple, list) or len(values) > bound:
            raise ValueError("bounded_ledger_sequence_required")
        for value in values:
            if not _bytes(value):
                raise ValueError("empty_forbidden_ledger_value")
    if any(not _public_identifier(value) for value in future_identifiers):
        raise ValueError("future_ledger_requires_exact_identifiers")
    aliases = derive_semantic_aliases(semantic_bytes, semantic_profile=semantic_profile)
    semantic_issues = forbidden_semantic_labels(semantic_bytes, semantic_profile=semantic_profile)
    issues, receipts = [], []
    candidates = [("full_target", target)]
    if operand is not None:
        candidates.append(("operand", operand))
    candidates.extend(("future_identifier", value) for value in sorted(set(future_identifiers)))
    candidates.extend(("registered_route", value) for value in sorted(set(registered_routes)))
    candidates.extend(("semantic_alias", value) for value in aliases)
    candidates.extend(("forbidden_core", value) for value in FORBIDDEN_CORE_LABELS)

    def authorized(category, value, start, end):
        if category == "semantic_alias":
            for span in semantic_spans:
                if ((span.kind == "identifier" and span.start <= start < end <= span.end)
                        or (span.kind == "syntax" and start == span.start and end == span.end)):
                    return span
        for field in fields:
            if field.kind == "protocol":
                if (category == "semantic_alias" and field.start == 0
                        and field.start <= start and end <= field.end):
                    return field
                if (category == "full_target" and value == b"STOP" and prefix[start:end] == b"STOP"
                        and field.start <= start and end <= field.end
                        and (start == field.start or prefix[start - 1:start] == b"\n")
                        and (end == field.end or prefix[end:end + 1] == b"\n")):
                    return field
                continue
            if start != field.start or end != field.end or category not in ("operand", "future_identifier"):
                continue
            task_value = {"task_start": task_start, "task_goal": task_goal,
                          "current": current, "task_current": current}.get(field.kind)
            if value == task_value:
                return field
            if category == "future_identifier":
                continue
            if phase == "SEEK" and field.kind == "route_query":
                return field
            if (phase == "SEEK" and field.kind == "event_recover" and observed_contradiction
                    and implicated_event is not None and field.owner == implicated_event):
                return field
            if phase == "PROSPECT" and field.kind == "event_did":
                return field
            if phase in ("CHECK", "READ_CHECK", "STEP_CHECK"):
                if field.kind == "issued_query" and value == implicated_query:
                    return field
                if field.kind == "selected_event" and value == implicated_event:
                    return field
            if (phase in ("CHECK", "READ_CHECK") and field.kind == "route_query"
                    and value == implicated_query):
                return field
            if (phase == "CONTINUE" and field.kind == "event_got" and value == current
                    and field.owner is not None):
                return field
            if field.kind == "think_implicated" and value in (implicated_event, implicated_query):
                return field
        return None

    views = _views(prefix)
    for category, value in candidates:
        needles = tuple(b"\n".join(lines) for lines in normalize_lines(value))
        for (form, haystack, offsets), needle in zip(views, needles):
            if not needle:
                raise ValueError("empty_normalized_ledger_value")
            cursor = 0
            while (found := haystack.find(needle, cursor)) >= 0:
                finish = found + len(needle)
                cursor = found + 1
                if category == "full_target" and target == b"STOP":
                    if ((found and haystack[found - 1:found] != b"\n")
                            or (finish < len(haystack) and haystack[finish:finish + 1] != b"\n")):
                        source_start = found if offsets is None else offsets[found][0]
                        source_end = finish if offsets is None else offsets[finish - 1][1]
                        if any(field.kind == "protocol" and field.start <= source_start
                               and source_end <= field.end for field in fields):
                            continue
                start, end = (found, finish) if offsets is None else (offsets[found][0], offsets[finish - 1][1])
                field = authorized(category, value, start, end)
                occurrence = Occurrence(category, value, form, start, end,
                                        field.path if field else None, field.evidence if field else None)
                (receipts if field else issues).append(occurrence)
                if len(receipts) + len(issues) > BOUNDS["hits"]:
                    raise ValueError("scanner_hit_bound_exceeded")
    return ScanReport(tuple(issues), tuple(receipts), semantic_issues, aliases)
