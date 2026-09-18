"""Compose complete birth semantics, future checks and finite route matching.

This is a source-content audit, not native template, held-core or provenance
qualification. Registered routes use the existing typed finite matcher, which
checks literal, normalized and compact forms without enumerating cyclic paths.
The generic scanner's optional literal-route list is therefore unused; it is
not a substitute for the mandatory route result. Neither category overrides
the other. No supplied metadata, exemption spans or successful receipts are
accepted as authority by this interface.
"""

from dataclasses import dataclass

from organism_v6 import composition_birth_stage2a_metadata_inputs as metadata
from organism_v6 import composition_birth_stage2a_route_scan as routes
from organism_v6 import composition_birth_stage2a_scan_inputs as source_scan


STATUS = "BIRTH_SOURCE_CONTENT_AUDIT_ONLY"
SCIENCE_GATES = metadata.SCIENCE_GATES


@dataclass(frozen=True)
class BirthInventoryReport:
    metadata_inputs: metadata.BirthMetadataInputs
    content_scan: source_scan.BirthScanReport
    route_scan: routes.RouteScan

    status = STATUS
    science_gates = SCIENCE_GATES
    native_chat_bytes_verified = False
    inventory_completeness_verified = False

    @property
    def supplied_projection_clear(self):
        return (self.content_scan.supplied_projection_clear
                and self.route_scan.registered_grammar_clear)


class BirthInventoryScanner:
    """Reuse only the private per-case encoder; rebuild each arm's evidence."""

    def __init__(self, *, case, role_tokens, display_master, source_semantic_occurrences=False,
                 semantic_profile="birth_full_v1"):
        if type(source_semantic_occurrences) is not bool:
            raise ValueError("boolean_source_semantic_occurrences_required")
        self._producer = metadata.BirthMetadataInputProducer(
            case=case, role_tokens=role_tokens, display_master=display_master,
            semantic_profile=semantic_profile,
        )
        self._display_master = display_master
        self._source_semantic_occurrences = source_semantic_occurrences

    def scan(self, record):
        private = self._producer.build(record)
        private.check_semantic_bounds()
        source = private.source
        content_scan = source_scan.scan_birth_arm(
            source.record, source.case, role_tokens=source.role_tokens,
            semantic_bytes=private.semantic_bytes,
            future_identifiers=tuple(sorted(private.future_inputs.future_identifiers)),
            registered_routes=(), semantic_profile=private.semantic_profile,
            source_semantic_occurrences=self._source_semantic_occurrences,
        )
        route_scan = routes.scan_birth_route_language(
            case=source.case, record=source.record, role_tokens=source.role_tokens,
            display_master=self._display_master,
        )
        if content_scan.binding != private.binding or route_scan.binding != private.binding:
            raise ValueError("birth_inventory_boundary_mismatch")
        if route_scan.source.source.provenance_bytes != source.provenance_bytes:
            raise ValueError("birth_inventory_source_mismatch")
        return BirthInventoryReport(private, content_scan, route_scan)


def scan_birth_inventory(*, case, record, role_tokens, display_master, source_semantic_occurrences=False,
                         semantic_profile="birth_full_v1"):
    return BirthInventoryScanner(case=case, role_tokens=role_tokens,
                                 display_master=display_master,
                                 source_semantic_occurrences=source_semantic_occurrences,
                                 semantic_profile=semantic_profile).scan(record)
