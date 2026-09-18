"""Complete evaluator-only birth_full_v1 semantics from explicit constructor inputs.

This is the prospective non-material Builder schema, not a scanner clearance or
scientific gate. Only private immutable constructor snapshots and encoded source
bytes are retained across records. Arm-specific futures, disclosure receipts and
cores are freshly derived using the existing producers. No public projection is
enlarged, and original trace actions are structured rather than concatenated.

The source validator is deliberately still invoked by the future producer for
every record. Reusing a producer avoids re-encoding the full static construction;
it does not trust a caller's validation receipt or cache an arm's disclosures.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from hashlib import sha256
import json
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_core_inputs as core_inputs
from organism_v6 import composition_birth_stage2a_future_inputs as future_inputs
from organism_v6 import composition_birth_stage2a_route_inputs as route_inputs
from organism_v6 import composition_birth_stage2a_scan_inputs as scan_inputs
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6 import composition_birth_stage2a_worlds as worlds
from organism_v6.composition_birth_stage2a_primitives import canonical_json


STATUS = "PARTIAL_SOURCE_ONLY"
SCHEMA_VERSION = "BIRTH_COMPLETE_PRIVATE_METADATA_V1"
SCHEMA_PATH = "research_notes/analysis/2026-09-14_stage2a_birth_metadata_schema_v1.md"
SEMANTIC_PROFILE = "birth_full_v1"
SUPPORTED_SEMANTIC_PROFILES = ("birth_full_v1", "birth_full_v2")
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
SCIENCE_GATES = MappingProxyType(dict(source_inputs.SCIENCE_GATES))
LIMITATIONS = (
    "Constructor-correlated semantic coverage, not independent input authority or scientific certification.",
    "Evaluator-only metadata and raw snapshots must never be sent to the actor.",
    "No alias-collision clearance, integrated scanner pass, held-core or native-template qualification.",
    "Constructor identity uses the validator's API and contract pins, not independent executable-byte attestation.",
    "No tokenizer, model, materialization, training, GPU, complete guard or C11 promotion.",
)
PROTECTED_ROOTS = frozenset(("case_id", "causal_pair_id", "core", "evaluator", "factors", "future",
                             "mutation", "oracle", "recovery_match_id", "role_keys", "target", "unit_id"))
_FIELDS = MappingProxyType({
    birth.BirthCaseDescriptor: "world member pair_index bucket pair_type family family_motif flow recovery_subtype terminal_class goal_side goal_index skin recovery_match_id domain",
    birth.BirthCase: "descriptor task task_text construction trace targets facts status memo_sha256 clarification_sha256",
    birth.BirthPair: "world role_tokens cases status memo_sha256 clarification_sha256",
    birth.BirthTarget: "ordinal phase target_bytes target_sha256 command operand trace_index current_before current_after selection_index",
    birth.BirthTraceTurn: "action response current_before current_after target_ordinal",
    birth.BirthTraceFacts: "selected_query failed_query failed_event failed_prediction failed_outcome corrective_query selected_event selected_prediction selected_outcome final_current",
    worlds.OrdinaryConstruction: "domain world skin scope blocks registry world_edges status memo_sha256",
    wire.Action: "operation verb operand",
    wire.TaskState: "start goal current",
    wire.ServiceBlock: "kind rows raw",
    wire.EventRow: "event node goal port got recover receipt",
    wire.RouteRow: "route node goal query",
    targets.TargetUnit: "unit_id phase target_bytes target_sha256 command operand selection_index",
    targets.ArmRecord: "arm unit prefix prefix_sha256 content_bytes serialized_bytes",
    targets.Message: "role content",
    future_inputs.CandidateOrigin: "role_key source_path",
    scan_inputs.FieldObservation: "path start end value kind origin observed_at source_trace_index evidence owner exemption_kind is_latest_current",
    scan_inputs.MessageSpan: "message_index role start end source_trace_index observed_at content_sha256",
    route_inputs.RouteTransition: "query event current goal port predicted actual recover receipt source_path recovery_owner_port",
})
_ROW_FIELDS = MappingProxyType({
    "EVENTS": (("EVENT", "event"), ("AT", "node"), ("FOR", "goal"), ("DID", "port"),
               ("GOT", "got"), ("RECOVER", "recover"), ("EVIDENCE", "receipt")),
    "ROUTES": (("ROUTE", "route"), ("AT", "node"), ("FOR", "goal"), ("QUERY", "query")),
})


class MetadataInputError(ValueError):
    """Unsupported or non-round-tripping source surface; never silently omit it."""


class MetadataBoundsError(MetadataInputError):
    """A complete object exceeds the adopted profile; counts remain inspectable."""

    def __init__(self, counts, exceeded):
        self.coverage_counts = MappingProxyType(dict(counts))
        self.exceeded = tuple(exceeded)
        super().__init__("birth_metadata_profile_bound_exceeded: " + ",".join(exceeded))


def _semantic_limits(semantic_profile):
    if type(semantic_profile) is not str or semantic_profile not in SUPPORTED_SEMANTIC_PROFILES:
        raise MetadataInputError("unsupported_birth_semantic_profile")
    if semantic_profile not in scanner.SEMANTIC_PROFILES:
        raise MetadataInputError("unavailable_birth_semantic_profile: " + semantic_profile)
    return scanner.SEMANTIC_PROFILES[semantic_profile]


def _check_fields(value):
    names = _FIELDS.get(type(value))
    if names is None or tuple(field.name for field in fields(value)) != tuple(names.split()):
        raise MetadataInputError("unsupported_source_fields_or_type: " + type(value).__name__)
    return names.split()


def _decoded(value):
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is bytes:
        return value.decode("ascii")
    if type(value) is tuple:
        return [_decoded(item) for item in value]
    if type(value) in _FIELDS:
        return {name: _decoded(getattr(value, name)) for name in _check_fields(value)}
    raise MetadataInputError("unsupported_decoded_source_type: " + type(value).__name__)


def _integrity(raw):
    return {"raw_sha256": sha256(raw).hexdigest(), "raw_bytes": len(raw), "exact_rerender": True}


def render_action(value):
    """Reconstitute the original action, rejecting edited fields or integrity."""
    if set(value) != {"command", "verb", "operand", "raw_sha256", "raw_bytes", "exact_rerender"}:
        raise MetadataInputError("unsupported_action_fields")
    parts = [value["command"]]
    if value["verb"] is not None:
        parts.append(value["verb"])
    if value["operand"] is not None:
        parts.append(value["operand"])
    raw = " ".join(parts).encode("ascii")
    parsed = wire.parse_action(raw.decode("ascii"))
    if (parsed.operation, parsed.verb, parsed.operand) != (value["command"], value["verb"], value["operand"]):
        raise MetadataInputError("action_decoded_fields_mismatch")
    _verify_integrity(value, raw)
    return raw


def _verify_integrity(value, raw):
    if any(type(value.get(name)) is not type(expected) or value[name] != expected
           for name, expected in _integrity(raw).items()):
        raise MetadataInputError("exact_rerender_or_hash_mismatch")


def _action(raw):
    if type(raw) is str:
        raw = raw.encode("ascii")
    if type(raw) is not bytes:
        raise MetadataInputError("action_bytes_or_ascii_required")
    parsed = wire.parse_action(raw.decode("ascii"))
    _check_fields(parsed)
    result = dict(command=parsed.operation, verb=parsed.verb, operand=parsed.operand, **_integrity(raw))
    if render_action(result) != raw:
        raise MetadataInputError("action_round_trip_mismatch")
    return result


def _path(path):
    if type(path) is not tuple or any(type(part) is not str for part in path):
        raise MetadataInputError("typed_source_path_required")
    return [_action(part) if part.startswith("READ ") else part for part in path]


def render_source_path(path):
    """Recover exact source tuple components, including raw read requests."""
    return tuple(render_action(part).decode("ascii") if type(part) is dict else part for part in path)


def _row(row, kind):
    expected = wire.EventRow if kind == "EVENTS" else wire.RouteRow
    if type(row) is not expected:
        raise MetadataInputError("unsupported_service_row_type")
    _check_fields(row)
    return {label: getattr(row, name) for label, name in _ROW_FIELDS[kind]}


def render_service(value):
    """Re-render complete ordered registry bytes from uppercase wire fields."""
    if set(value) != {"kind", "skin", "rows", "raw_sha256", "raw_bytes", "exact_rerender"}:
        raise MetadataInputError("unsupported_service_fields")
    kind = value["kind"]
    if kind == "MISS":
        if value["rows"]:
            raise MetadataInputError("miss_with_rows")
        rows = ()
    elif kind in _ROW_FIELDS:
        layout = _ROW_FIELDS[kind]
        if any(set(row) != {label for label, name in layout} for row in value["rows"]):
            raise MetadataInputError("unsupported_service_row_fields")
        row_type = wire.EventRow if kind == "EVENTS" else wire.RouteRow
        rows = tuple(row_type(**{name: row[label] for label, name in layout}) for row in value["rows"])
    else:
        raise MetadataInputError("unsupported_service_kind")
    raw = worlds.render_service(kind, rows, skin=value["skin"]).encode("ascii")
    _verify_integrity(value, raw)
    return raw


def _service(block, skin):
    _check_fields(block)
    if block.kind not in (*_ROW_FIELDS, "MISS"):
        raise MetadataInputError("unsupported_service_kind")
    result = dict(kind=block.kind, skin=skin, rows=[_row(row, block.kind) for row in block.rows],
                  **_integrity(block.raw.encode("ascii")))
    if render_service(result) != block.raw.encode("ascii"):
        raise MetadataInputError("service_round_trip_mismatch")
    return result


def _task(task, raw):
    _check_fields(task)
    value = {"START": task.start, "GOAL": task.goal, "CURRENT": task.current}
    rendered = "TASK\n" + "\n".join(label + " " + value[label] for label in ("START", "GOAL", "CURRENT"))
    if rendered != raw or wire.parse_task(raw) != task:
        raise MetadataInputError("task_round_trip_mismatch")
    return dict(value, **_integrity(raw.encode("ascii")))


def render_response(value):
    kind = value["kind"]
    expected = {"kind", "raw_sha256", "raw_bytes", "exact_rerender"}
    if kind == "SERVICE":
        expected.add("service")
        raw = b"SERVICE\n" + render_service(value["service"])
    elif kind == "WORLD":
        expected.add("CURRENT")
        raw = ("WORLD\nCURRENT " + value["CURRENT"]).encode("ascii")
        wire.parse_world(raw.decode("ascii"))
    elif kind in ("ACK", "EMPTY"):
        raw = b"ACK" if kind == "ACK" else b""
    else:
        raise MetadataInputError("unsupported_trace_response")
    if set(value) != expected:
        raise MetadataInputError("unsupported_response_fields")
    _verify_integrity(value, raw)
    return raw


def _response(raw, skin):
    if raw.startswith("SERVICE\n"):
        value = {"kind": "SERVICE", "service": _service(wire.parse_service(raw[8:], skin=skin), skin)}
    elif raw.startswith("WORLD\n"):
        value = {"kind": "WORLD", "CURRENT": wire.parse_world(raw)}
    elif raw in ("ACK", ""):
        value = {"kind": "ACK" if raw else "EMPTY"}
    else:
        raise MetadataInputError("unsupported_trace_response")
    value.update(_integrity(raw.encode("ascii")))
    if render_response(value) != raw.encode("ascii"):
        raise MetadataInputError("response_round_trip_mismatch")
    return value


def _target(target):
    names = _check_fields(target)
    action = _action(target.target_bytes)
    if (target.target_sha256 != action["raw_sha256"] or target.command != action["command"]
            or target.operand != action["operand"]):
        raise MetadataInputError("target_action_fields_or_hash_mismatch")
    return {name: action if name == "target_bytes" else _decoded(getattr(target, name)) for name in names}


def _construction(construction):
    names = _check_fields(construction)
    if set(construction.registry) != set(construction.blocks):
        raise MetadataInputError("registry_block_coverage_mismatch")
    services = []
    for request, block in sorted(construction.blocks.items()):
        encoded = _service(block, construction.skin)
        if render_service(encoded).decode("ascii") != construction.registry[request]:
            raise MetadataInputError("registry_raw_mismatch")
        services.append({"request": _action(request), "block": encoded})
    return {
        "source_fields": {name: _decoded(getattr(construction, name)) for name in names
                          if name not in ("blocks", "registry", "world_edges")},
        "services": services,
        "world_edges": [{"AT": current, "DID": port, "CURRENT": actual}
                        for (current, port), actual in sorted(construction.world_edges.items())],
    }


def _route_basis(route):
    transitions = []
    for port, transition in sorted(route.transitions.items()):
        _check_fields(transition)
        if port != transition.port:
            raise MetadataInputError("route_port_key_mismatch")
        transitions.append({
            "QUERY": transition.query, "EVENT": transition.event, "AT": transition.current,
            "FOR": transition.goal, "DID": transition.port, "GOT": transition.predicted,
            "CURRENT": transition.actual, "RECOVER": transition.recover, "EVIDENCE": transition.receipt,
            "source_path": _path(transition.source_path), "recovery_owner_port": transition.recovery_owner_port,
            "mismatches": transition.mismatches,
        })
    return {"transitions": transitions,
            "ports_by_current": {current: list(ports) for current, ports in route.ports_by_current.items()},
            "ports_by_query": {query: list(ports) for query, ports in route.ports_by_query.items()},
            "unavailable_recover_queries": sorted(route.unavailable_recover_queries)}


def _mutation(pair, selected, route):
    _check_fields(pair)
    before, after = pair.cases
    if (before.descriptor.member, after.descriptor.member) != ("m0", "m1"):
        raise MetadataInputError("paired_member_order_mismatch")
    before_store, after_store = before.construction, after.construction
    scalar_fields = set(_check_fields(before_store)) - {"blocks", "registry", "world_edges"}
    _check_fields(after_store)
    if (set(before_store.blocks) != set(after_store.blocks)
            or not source_inputs._same_source(before_store.world_edges, after_store.world_edges)
            or any(getattr(before_store, name) != getattr(after_store, name) for name in scalar_fields)):
        raise MetadataInputError("unsupported_paired_construction_surface")
    changes = []
    for request, block in sorted(before_store.blocks.items()):
        paired = after_store.blocks[request]
        if block.kind != paired.kind or len(block.rows) != len(paired.rows):
            raise MetadataInputError("unsupported_paired_block_change")
        for position, (before_row, after_row) in enumerate(zip(block.rows, paired.rows)):
            changed = [name for name in _check_fields(before_row)
                       if getattr(before_row, name) != getattr(after_row, name)]
            if changed:
                if block.kind != "EVENTS" or changed != ["goal"]:
                    raise MetadataInputError("unsupported_paired_non_FOR_change")
                changes.append({"request": _action(request), "row_index": position, "field": "FOR",
                                "before": _row(before_row, "EVENTS"), "after": _row(after_row, "EVENTS")})
    relation = selected.descriptor.pair_type == "relation"
    if len(changes) != (2 if relation else 0):
        raise MetadataInputError("paired_FOR_swap_coverage_mismatch")
    if relation and (changes[0]["request"] != changes[1]["request"]
                     or {entry["row_index"] for entry in changes} != {
                         selected.descriptor.relation_slot, (selected.descriptor.relation_slot + 2) % 4}
                     or changes[0]["before"]["FOR"] != changes[1]["after"]["FOR"]
                     or changes[1]["before"]["FOR"] != changes[0]["after"]["FOR"]):
        raise MetadataInputError("paired_FOR_swap_provenance_mismatch")
    mismatches = [transition for transition in _route_basis(route)["transitions"] if transition["mismatches"]]
    return {"pair_type": selected.descriptor.pair_type, "selected_member_id": selected.descriptor.member,
            "before_member_id": "m0", "after_member_id": "m1", "relation_slot": selected.descriptor.relation_slot,
            "paired_FOR_swap": changes, "effective_mismatches": mismatches,
            "paired_tasks": [_task(case.task, case.task_text) for case in pair.cases],
            "pair_source_fields": {"world": pair.world, "status": pair.status,
                                   "memo_sha256": pair.memo_sha256, "clarification_sha256": pair.clarification_sha256},
            "paired_case_sha256": [sha256(canonical_json(source_inputs._digest_value(case))).hexdigest()
                                   for case in pair.cases]}


def _future(future):
    origins = []
    for token, entries in sorted(future.candidate_provenance.items()):
        for entry in entries:
            _check_fields(entry)
        origins.append({"identifier": token.decode("ascii"),
                        "origins": [{"role_key": entry.role_key, "source_path": _path(entry.source_path)}
                                    for entry in entries]})
    return {"candidates": [token.decode("ascii") for token in sorted(future.candidates)],
            "disclosed": [token.decode("ascii") for token in sorted(future.disclosed)],
            "future_identifiers": [token.decode("ascii") for token in sorted(future.future_identifiers)],
            "candidate_provenance": origins,
            "disclosure_provenance": [{"identifier": token.decode("ascii"),
                                       "observations": [_decoded(entry) for entry in entries]}
                                      for token, entries in sorted(future.disclosure_provenance.items())],
            "projection_sha256": future.binding.projection_sha256,
            "source_prefix_sha256": future.binding.source_prefix_sha256,
            "message_spans": [_decoded(span) for span in future.binding.message_spans]}


def metadata_coverage_counts(metadata_bytes):
    """Measure the entire canonical tree without invoking the alias matcher."""
    value = json.loads(metadata_bytes)
    if canonical_json(value) != metadata_bytes or set(value) != PROTECTED_ROOTS:
        raise MetadataInputError("canonical_protected12_tree_required")
    nodes, leaves, depth = 0, 0, 0
    stack = [(value, 0)]
    while stack:
        item, level = stack.pop()
        nodes += 1
        depth = max(depth, level)
        if type(item) is dict:
            stack.extend((child, level + 1) for child in item.values())
        elif type(item) is list:
            stack.extend((child, level + 1) for child in item)
        else:
            leaves += 1
    construction = value["oracle"]["construction"]
    services = construction["services"]
    future = value["future"]
    return MappingProxyType({
        "bytes": len(metadata_bytes), "nodes": nodes, "leaves": leaves, "depth": depth,
        "protected_roots": len(value), "services": len(services),
        "rows": sum(len(service["block"]["rows"]) for service in services),
        "event_rows": sum(len(service["block"]["rows"]) for service in services if service["block"]["kind"] == "EVENTS"),
        "route_rows": sum(len(service["block"]["rows"]) for service in services if service["block"]["kind"] == "ROUTES"),
        "world_edges": len(construction["world_edges"]), "role_bindings": len(value["role_keys"]),
        "trace_turns": len(value["oracle"]["trace"]), "facts": len(value["oracle"]["facts"]),
        "targets": len(value["oracle"]["targets"]), "route_transitions": len(value["oracle"]["route_basis"]["transitions"]),
        "candidates": len(future["candidates"]), "disclosed": len(future["disclosed"]),
        "future_identifiers": len(future["future_identifiers"]),
        "candidate_origins": sum(len(entry["origins"]) for entry in future["candidate_provenance"]),
        "disclosure_receipts": sum(len(entry["observations"]) for entry in future["disclosure_provenance"]),
        "paired_FOR_changes": len(value["mutation"]["paired_FOR_swap"]),
        "effective_mismatches": len(value["mutation"]["effective_mismatches"]),
    })


@dataclass(frozen=True)
class BirthMetadataInputs:
    metadata_bytes: bytes
    metadata_sha256: str
    coverage_counts: Mapping
    source: source_inputs.ValidatedBirthSource
    paired_source_snapshot: birth.BirthPair
    core_inputs: core_inputs.BirthCoreInputs
    future_inputs: future_inputs.BirthFutureInputs
    route_inputs: route_inputs.BirthRouteInputs
    provenance_bytes: bytes
    semantic_profile: str = SEMANTIC_PROFILE

    status = STATUS
    schema_version = SCHEMA_VERSION
    science_gates = SCIENCE_GATES
    limitations = LIMITATIONS
    inventory_completeness_verified = False
    native_chat_bytes_verified = False

    def __post_init__(self):
        _semantic_limits(self.semantic_profile)

    @property
    def semantic_bytes(self):
        return self.metadata_bytes

    @property
    def metadata(self):
        return json.loads(self.metadata_bytes)

    @property
    def source_snapshot(self):
        return self.source

    @property
    def binding(self):
        return self.future_inputs.binding

    def check_semantic_bounds(self):
        """Fail explicitly on tree overflow; alias count is a separate scanner check."""
        limits = _semantic_limits(self.semantic_profile)
        exceeded = [name for name in ("bytes", "nodes", "leaves", "depth")
                    if self.coverage_counts[name] > limits[name]]
        if exceeded:
            raise MetadataBoundsError(self.coverage_counts, exceeded)
        return self.coverage_counts


class BirthMetadataInputProducer:
    """Reusable per-case encoder holding only private immutable source material.

    Building always returns complete bytes, including an oversized tree. Call
    check_semantic_bounds before integration; the selected scanner capacity
    profile independently enforces its bounds. Selection never changes metadata
    bytes or semantic rules. Nothing here certifies scanner passage.
    """

    def __init__(self, *, case, role_tokens, display_master, semantic_profile=SEMANTIC_PROFILE):
        _semantic_limits(semantic_profile)
        self._semantic_profile = semantic_profile
        _check_fields(case)
        if type(case) is not birth.BirthCase:
            raise MetadataInputError("typed_birth_case_required")
        pairs = targets.serialize_birth_case(case, role_tokens=role_tokens)
        route = route_inputs.derive_birth_route_inputs(
            case=case, record=pairs[0].closed, role_tokens=role_tokens, display_master=display_master)
        self._source = route.source
        self._route_inputs = route
        self._display_master = display_master
        self._pair = birth.build_birth_pair(world=case.descriptor.world, role_tokens=self._source.role_tokens,
                                           display_master=display_master)
        case = self._source.case
        _check_fields(case.descriptor)
        properties = {name for name, value in vars(type(case.descriptor)).items() if isinstance(value, property)}
        if properties != {"case_id", "family_bit", "relation_slot"}:
            raise MetadataInputError("unsupported_descriptor_properties")
        factors = {"world_id" if name == "world" else "member_id" if name == "member" else name:
                   _decoded(getattr(case.descriptor, name)) for name in _check_fields(case.descriptor)}
        factors.update(case_id=_decoded(case.descriptor.case_id), family_bit=case.descriptor.family_bit,
                       relation_slot=case.descriptor.relation_slot)
        trace = []
        for turn in case.trace:
            _check_fields(turn)
            trace.append({"action": _action(turn.action), "response": _response(turn.response, case.descriptor.skin),
                          "current_before": turn.current_before, "current_after": turn.current_after,
                          "target_ordinal": turn.target_ordinal})
        if len(case.targets) != 4 or tuple(target.ordinal for target in case.targets) != (0, 1, 2, 3):
            raise MetadataInputError("complete_four_targets_required")
        static = {
            "case_id": {"world_id": case.descriptor.world, "member_id": case.descriptor.member},
            "causal_pair_id": {"domain": case.descriptor.domain, "world_id": case.descriptor.world,
                               "pair_type": case.descriptor.pair_type},
            "factors": factors, "recovery_match_id": _decoded(case.descriptor.recovery_match_id),
            "role_keys": dict(self._source.role_tokens), "mutation": _mutation(self._pair, case, route),
            "oracle": {"task": _task(case.task, case.task_text), "construction": _construction(case.construction),
                       "trace": trace, "facts": _decoded(case.facts), "targets": [_target(target) for target in case.targets],
                       "route_basis": _route_basis(route), "source_fields": {
                           "status": case.status, "memo_sha256": case.memo_sha256,
                           "clarification_sha256": case.clarification_sha256}},
        }
        self._static_bytes = canonical_json(static)

    def build(self, record):
        _check_fields(record)
        future = future_inputs.derive_birth_future_inputs(
            case=self._source.case, record=record, role_tokens=self._source.role_tokens,
            display_master=self._display_master)
        source = future.source
        record = source.record
        core = core_inputs.build_birth_core_inputs(case=source.case, record=record, role_tokens=source.role_tokens)
        selected = next((target for target in source.case.targets
                         if record.unit.unit_id == f"{source.case.descriptor.world}/{source.case.descriptor.member}/u{target.ordinal}"), None)
        if selected is None:
            raise MetadataInputError("target_unit_ownership_mismatch")
        metadata = json.loads(self._static_bytes)
        retained = future.binding.retained_trace_indices
        metadata.update({
            "core": core.core, "future": _future(future), "unit_id": record.unit.unit_id,
            "evaluator": {"expected_action": _action(record.unit.target_bytes),
                          "task": {"START": source.case.task.start, "GOAL": source.case.task.goal,
                                   "CURRENT": selected.current_before},
                          "selected_effective_outcome": source.case.facts.selected_outcome,
                          "current_after": selected.current_after,
                          "physical_route_depth": core.core["actual_route_depth"],
                          "semantic_route_depth": core.semantic_route_depth},
            "target": {"unit": _target(record.unit), "birth_target": _target(selected), "arm": record.arm,
                       "target_bytes": record.unit.target_bytes.decode("ascii"),
                       "retained_trace_indices": list(retained), "decision_index": future.binding.decision_index,
                       "trace_index": selected.trace_index, "supervised_message_index": record.supervised_message_index,
                       "prefix_sha256": record.prefix_sha256, "content_bytes": record.content_bytes,
                       "serialized_bytes": record.serialized_bytes,
                       "retained_task": _task(wire.parse_task(record.prefix[1].content), record.prefix[1].content),
                       "message_spans": [_decoded(span) for span in future.binding.message_spans]},
        })
        payload = canonical_json(metadata)
        digest = sha256(payload).hexdigest()
        provenance = canonical_json({"schema": SCHEMA_VERSION, "schema_path": SCHEMA_PATH,
                                     "semantic_profile": self._semantic_profile, "metadata_sha256": digest,
                                     "source": json.loads(source.provenance_bytes),
                                     "core_receipt": core.receipt})
        return BirthMetadataInputs(payload, digest, metadata_coverage_counts(payload), source, self._pair,
                                   core, future, replace(self._route_inputs, source=source), provenance,
                                   semantic_profile=self._semantic_profile)


def build_birth_metadata_inputs(*, case, record, role_tokens, display_master, semantic_profile=SEMANTIC_PROFILE):
    """One-shot exact-source build; reuse BirthMetadataInputProducer for eight records."""
    return BirthMetadataInputProducer(case=case, role_tokens=role_tokens, display_master=display_master,
                                      semantic_profile=semantic_profile).build(record)
