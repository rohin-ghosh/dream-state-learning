"""V6 exact public boundaries over retained complete shared birth custody.

Only source records and candidate bytes/messages enter this verifier. It derives
its own observations, chronology, future inventory, core and finite route basis.
Low-level scanner outputs never authorize a boundary. Native template,
allocation authorization and runtime admission remain separate obligations.
"""

from dataclasses import dataclass, fields, is_dataclass, replace
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a_core_inputs as cores
from organism_v6 import composition_birth_stage2a_custody as custody
from organism_v6 import composition_birth_stage2a_future_inputs as futures
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_route_inputs as routes
from organism_v6 import composition_birth_stage2a_scan_inputs as bindings
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6 import composition_birth_stage2a_typed_scan as typed_scan


SCHEMA_VERSION = "BIRTH_TYPED_BOUNDARY_V6"
CONTRACT_SHA256 = "119b97eb418e7b9586c1425c091b846f7eb7f100ab337ca03cc8b92df2b7b0b6"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(bindings.SCIENCE_GATES, False))


class BoundaryError(ValueError):
    """A candidate differs from independently reconstructed source bytes."""


def _value(item):
    if item is None or type(item) in (str, int, bool):
        return item
    if type(item) is bytes:
        return {"bytes_hex": item.hex()}
    if type(item) in (tuple, list):
        return [_value(element) for element in item]
    if type(item) in (set, frozenset):
        return [_value(element) for element in sorted(item)]
    if type(item) in (dict, MappingProxyType):
        if all(type(key) is str for key in item):
            return {key: _value(element) for key, element in item.items()}
        return {"entries": [[_value(key), _value(element)]
                            for key, element in sorted(item.items())]}
    if is_dataclass(item):
        return {field.name: _value(getattr(item, field.name)) for field in fields(item)}
    raise BoundaryError("unsupported_boundary_value_type: " + type(item).__name__)


def _bytes(item):
    return primitives.canonical_json(_value(item))


def _reference(raw, count):
    return {"sha256": sha256(raw).hexdigest(), "bytes": len(raw), "count": count}


@dataclass(frozen=True)
class BirthBoundaryResult:
    boundary_bytes: bytes
    shared_custody_sha256: str
    candidate_inventory_bytes: bytes
    retained_inventory_bytes: bytes
    route_basis_bytes: bytes
    private_static_basis_bytes: bytes
    private_record_basis_bytes: bytes
    typed_receipts_bytes: bytes
    core_inputs: cores.BirthCoreInputs
    binding: bindings.BoundScanInputs
    future_inputs: futures.BirthFutureInputs
    route_inputs: routes.BirthRouteInputs
    scan: object

    schema_version = SCHEMA_VERSION
    science_gates = SCIENCE_GATES
    native_chat_bytes_verified = False
    independent_allocation_authorized = False

    @property
    def boundary_sha256(self):
        return sha256(self.boundary_bytes).hexdigest()

    @property
    def source_content_clear(self):
        return self.scan.passed


class BirthBoundaryVerifier:
    """Construct shared custody once, then verify this pair's sixteen boundaries."""

    def __init__(self, *, world, role_tokens, display_master):
        self._custody = custody.BirthSourceCustody(
            world=world, role_tokens=role_tokens, display_master=display_master,
        )
        self._cores = {}
        self._routes = {}
        self._candidates = {}
        self._boundary_receipts = {}
        self._records = tuple(record for case in self._custody.cases
                              for pair in targets.serialize_birth_case(case, role_tokens=role_tokens)
                              for record in (pair.closed, pair.atom_local))

    @property
    def records(self):
        return self._records

    @property
    def shared_bytes(self):
        return self._custody.shared_bytes

    @property
    def shared_sha256(self):
        return self._custody.shared_sha256

    def verify_shared(self, candidate_bytes):
        return self._custody.verify_shared(candidate_bytes)

    def verify(self, record, *, public_messages=None, public_projection=None,
               candidate_boundary_bytes=None):
        expected_record = self._custody.record_for(record)
        expected_projection = b"\n".join(message.content.encode("ascii") for message in expected_record.prefix)
        if public_messages is not None:
            if (type(public_messages) is not tuple
                    or targets.messages_bytes(public_messages) != targets.messages_bytes(expected_record.prefix)):
                raise BoundaryError("exact_public_messages_mismatch")
        if public_projection is not None:
            if type(public_projection) is not bytes or public_projection != expected_projection:
                raise BoundaryError("exact_public_projection_mismatch")
        identity = expected_record.unit.unit_id, expected_record.arm
        if candidate_boundary_bytes is not None:
            if type(candidate_boundary_bytes) is not bytes:
                raise BoundaryError("exact_boundary_receipt_mismatch")
            cached = self._boundary_receipts.get(identity)
            if cached is not None and candidate_boundary_bytes != cached:
                raise BoundaryError("exact_boundary_receipt_mismatch")
            candidate = primitives.parse_canonical_json(candidate_boundary_bytes)
            if (type(candidate) is not dict or candidate.get("unit_id") != identity[0]
                    or candidate.get("arm") != identity[1]
                    or candidate.get("shared_custody_sha256") != self.shared_sha256):
                raise BoundaryError("exact_boundary_receipt_mismatch")
        source = self._custody.source_for(record)
        binding = bindings.bind_birth_arm(source.record, source.case,
                                           role_tokens=source.role_tokens)
        if binding.projection_bytes != expected_projection:
            raise BoundaryError("independent_public_projection_mismatch")

        future = futures._derive_from_source(source, binding)
        case_key = source.case_sha256
        if case_key not in self._routes:
            route = routes._derive_from_source(source)
            raw = _bytes({"schema_version": route.schema_version,
                          "transitions": route.transitions,
                          "ports_by_current": route.ports_by_current,
                          "ports_by_query": route.ports_by_query,
                          "unavailable_recover_queries": route.unavailable_recover_queries})
            self._routes[case_key] = route, raw
        original_route, route_raw = self._routes[case_key]
        route = replace(original_route, source=source, transitions=MappingProxyType({
            port: replace(edge) for port, edge in original_route.transitions.items()
        }))
        if case_key not in self._candidates:
            raw = _bytes({"schema_version": future.schema_version,
                          "candidates": future.candidates,
                          "candidate_provenance": future.candidate_provenance})
            self._candidates[case_key] = (future.candidates, future.candidate_provenance, raw)
        candidate_set, candidate_provenance, candidate_raw = self._candidates[case_key]
        if future.candidates != candidate_set or future.candidate_provenance != candidate_provenance:
            raise BoundaryError("case_candidate_inventory_changed")
        retained_raw = _bytes({"disclosed": future.disclosed,
                               "future_identifiers": future.future_identifiers,
                               "disclosure_provenance": future.disclosure_provenance})
        if case_key not in self._cores:
            self._cores[case_key] = cores.BirthCoreInputProducer(
                case=source.case, role_tokens=source.role_tokens,
            )
        core = self._cores[case_key].build(source.record)
        scan = typed_scan.scan_typed_birth(
            source=source, binding=binding, future_inputs=future, route_inputs=route,
        )
        static_basis = tuple(item for item in scan.private_basis if item.source_path[0] != "record")
        record_basis = tuple(item for item in scan.private_basis if item.source_path[0] == "record")
        static_raw = _bytes(static_basis)
        record_raw = _bytes(record_basis)
        typed_receipts_raw = _bytes({"occurrences": scan.typed_occurrences,
                                     "receipts": scan.typed_receipts,
                                     "issues": scan.typed_issues,
                                     "forward_receipts": scan.content_scan.receipts,
                                     "forward_issues": scan.content_scan.issues,
                                     "route_occurrences": scan.route_scan.occurrences})
        envelope = {
            "schema_version": SCHEMA_VERSION, "contract_sha256": CONTRACT_SHA256,
            "shared_custody_sha256": self.shared_sha256,
            "source_provenance": source.provenance_bytes,
            "source_provenance_sha256": source.provenance_sha256,
            "case_sha256": source.case_sha256, "record_sha256": source.record_sha256,
            "world": source.case.descriptor.world, "member": source.case.descriptor.member,
            "unit_id": record.unit.unit_id, "arm": record.arm, "phase": binding.phase,
            "decision_index": binding.decision_index,
            "retained_trace_indices": binding.retained_trace_indices,
            "public_messages": binding.public_messages,
            "public_projection": binding.projection_bytes,
            "projection_sha256": binding.projection_sha256,
            "source_prefix_sha256": binding.source_prefix_sha256,
            "message_spans": binding.message_spans,
            "field_observations": binding.observations,
            "scanner_fields": binding.fields,
            "target": record.unit,
            "task_start": binding.task_start, "task_goal": binding.task_goal,
            "latest_current": binding.current,
            "implicated_query": binding.implicated_query,
            "implicated_event": binding.implicated_event,
            "observed_contradiction": binding.observed_contradiction,
            "candidate_inventory": _reference(candidate_raw, len(future.candidates)),
            "retained_inventory": _reference(retained_raw, len(future.future_identifiers)),
            "disclosed_count": len(future.disclosed),
            "route_basis": _reference(route_raw, len(route.transitions)),
            "private_static_basis": _reference(static_raw, len(static_basis)),
            "private_record_basis": _reference(record_raw, len(record_basis)),
            "typed_occurrence_receipts": _reference(typed_receipts_raw, len(scan.typed_receipts)),
            "core_sha256": sha256(core.core_bytes).hexdigest(),
            "checker_payload_sha256": sha256(core.checker_payload).hexdigest(),
            "checker_receipt": core.receipt,
            "native_template_tokenization": "NOT_YET_BOUND",
            "independent_allocation_authority": "NOT_YET_BOUND",
        }
        boundary_raw = _bytes(envelope)
        if candidate_boundary_bytes is not None:
            if type(candidate_boundary_bytes) is not bytes or candidate_boundary_bytes != boundary_raw:
                raise BoundaryError("exact_boundary_receipt_mismatch")
        self._boundary_receipts[identity] = boundary_raw
        return BirthBoundaryResult(boundary_raw, self.shared_sha256, candidate_raw, retained_raw,
                                   route_raw, static_raw, record_raw, typed_receipts_raw,
                                   core, binding, future, route, scan)
