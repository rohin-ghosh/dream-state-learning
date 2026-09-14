"""Occurrence-aware matching of a finite registered route byte language.

Recognizes STEP schedules with intervening registered protocol records, ordered
registered EVENT rows (either skin), their mixtures, and explicit ordered port/event/query ID
lists separated by spaces, arrows, or commas on one line. Literal, normalized
and compact source forms share the existing ASCII normalization. Only typed
registered lines may bridge transitions; arbitrary prose never joins IDs.

The graph may contain cycles; matching consumes finite input lines rather than
enumerating paths. A pair witness detects a multi-transition fragment within
these grammars. Each historical exemption requires the complete causal prefix
through its second endpoint to match the retained source bytes, including the
original endpoint messages. Identical bytes appended elsewhere are not exempt.

This detector supplements, never overrides, full-target, future-ID and semantic
scans. It is not a complete ScanInventory, a detector of arbitrary paraphrases,
a native chat validator, or scientific authorization. Unknown text is outside
these route grammars, not certified harmless. All readiness gates remain false.
"""

from collections import defaultdict
from dataclasses import dataclass
import re

from organism_v6 import composition_birth_stage2a_route_inputs as route_inputs
from organism_v6 import composition_birth_stage2a_scan_inputs as scan_inputs
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6 import composition_birth_stage2a_worlds as worlds


SCHEMA_VERSION = "BIRTH_TYPED_ROUTE_OCCURRENCES_V1"
SCIENCE_GATES = route_inputs.SCIENCE_GATES


@dataclass(frozen=True)
class RouteOccurrence:
    grammar: str
    first_port: str
    second_port: str
    first_span: tuple[int, int]
    second_span: tuple[int, int]
    authenticated: bool


@dataclass(frozen=True)
class RouteScan:
    source: route_inputs.BirthRouteInputs
    binding: scan_inputs.BoundScanInputs
    occurrences: tuple[RouteOccurrence, ...]
    unrecognized_line_spans: tuple[tuple[int, int], ...]

    status = route_inputs.STATUS
    schema_version = SCHEMA_VERSION
    science_gates = SCIENCE_GATES
    inventory_completeness_verified = False

    @property
    def issues(self):
        return tuple(item for item in self.occurrences if not item.authenticated)

    @property
    def registered_grammar_clear(self):
        return not self.issues


def _compact(raw):
    return scanner.normalize_lines(raw)[2][0]


def scan_birth_route_language(*, case, record, role_tokens, display_master, candidate_prefix=None):
    """Rebuild source; an optional candidate is a mutation, never new provenance."""
    source = route_inputs.derive_birth_route_inputs(
        case=case, record=record, role_tokens=role_tokens, display_master=display_master,
    )
    binding = scan_inputs.bind_birth_arm(source.source.record, source.source.case,
                                         role_tokens=source.source.role_tokens)
    return _scan_from_inputs(source, binding, candidate_prefix=candidate_prefix)


def _scan_from_inputs(source, binding, *, candidate_prefix=None):
    """Internal finite matcher; input authentication remains with the verifier."""
    prefix = binding.projection_bytes if candidate_prefix is None else candidate_prefix
    scanner.normalize_lines(prefix)
    transitions = source.transitions
    ports_by_token = defaultdict(list)
    action_lines, event_lines = {}, {}
    bridge_lines = {b"ACK", b"WORLD", b"SERVICE", b"ROUTES", b"EVENTS", b"MISS", b"TASK"}
    for port, edge in transitions.items():
        action_lines[_compact(("STEP " + port).encode("ascii"))] = port
        for token in (port, edge.event, edge.query):
            ports_by_token[_compact(token.encode("ascii"))].append(port)
        bridge_lines.add(_compact(("THINK KEEP " + edge.event).encode("ascii")))
        bridge_lines.add(_compact(("THINK REVISE " + edge.event).encode("ascii")))
    for role, token in source.source.role_tokens.items():
        kind = role.rsplit("/", 1)[-1]
        labels = ("CURRENT ", "START ", "GOAL ") if kind == "node" else ()
        labels += ("THINK REVISE ",) if kind == "query" else ()
        for label in labels:
            bridge_lines.add(_compact((label + token).encode("ascii")))
    for request, block in source.source.case.construction.blocks.items():
        bridge_lines.add(_compact(request.encode("ascii")))
        for skin in (0, 1):
            lines = worlds.render_service(block.kind, block.rows, skin=skin).split("\n")[1:]
            for line, row in zip(lines, block.rows):
                value = _compact(line.encode("ascii"))
                if block.kind == "EVENTS":
                    event_lines[value] = row.port
                else:
                    bridge_lines.add(value)
    token_pattern = re.compile(rb"M2A[PEQ][A-Z2-7]{12}")
    original = binding.projection_bytes
    authenticated_messages = tuple(span for span in binding.message_spans
                                   if span.source_trace_index is not None
                                   and prefix[span.start:span.end] == original[span.start:span.end])
    occurrences, unrecognized = [], []
    seen_occurrences = set()

    def authenticated(span, grammar):
        expected_roles = (("assistant", "user") if grammar == "mixed"
                          else ("assistant",) if grammar == "actions" else ("user",))
        return grammar != "ordered_ids" and any(
            message.role in expected_roles and message.start <= span[0] and span[1] <= message.end
            for message in authenticated_messages
        )

    def emit(grammar, first_port, first_span, second_port, second_span):
        if not source.contains_pair(first_port, second_port):
            return
        key = grammar, first_port, first_span, second_port, second_span
        if key in seen_occurrences:
            return
        seen_occurrences.add(key)
        occurrences.append(RouteOccurrence(
            grammar, first_port, second_port, first_span, second_span,
            prefix[:second_span[1]] == original[:second_span[1]]
            and authenticated(first_span, grammar) and authenticated(second_span, grammar),
        ))
        if len(occurrences) > scanner.BOUNDS["hits"]:
            raise route_inputs.RouteInputError("route_occurrence_bound_exceeded")

    previous_action = None
    previous_rows = []
    offset = 0
    for raw in prefix.split(b"\n"):
        span = offset, offset + len(raw)
        offset = span[1] + 1
        line = _compact(raw)
        if line in action_lines:
            port = action_lines[line]
            if previous_action is not None:
                emit("actions", *previous_action, port, span)
            for earlier_port, earlier_span in previous_rows:
                emit("mixed", earlier_port, earlier_span, port, span)
            previous_action = port, span
            continue
        if line in event_lines:
            port = event_lines[line]
            if previous_action is not None:
                emit("mixed", *previous_action, port, span)
            for earlier_port, earlier_span in previous_rows:
                emit("event_rows", earlier_port, earlier_span, port, span)
            previous_rows.append((port, span))
            if len(previous_rows) > scanner.BOUNDS["fields"]:
                raise route_inputs.RouteInputError("route_row_bound_exceeded")
            continue
        if line in bridge_lines:
            continue
        identifiers = token_pattern.findall(line)
        if len(identifiers) >= 2 and all(token in ports_by_token for token in identifiers):
            residue = token_pattern.sub(b"", line)
            if not residue or set(residue) == {ord(",")}:
                for first_token, second_token in zip(identifiers, identifiers[1:]):
                    for first_port in ports_by_token[first_token]:
                        for second_port in ports_by_token[second_token]:
                            emit("ordered_ids", first_port, span, second_port, span)
                previous_action, previous_rows = None, []
                continue
        previous_action, previous_rows = None, []
        if raw:
            unrecognized.append(span)
    return RouteScan(source, binding, tuple(occurrences), tuple(unrecognized))
