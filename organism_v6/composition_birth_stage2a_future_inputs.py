"""Bounded evaluator-only future IDs from a rebuilt birth case and retained arm.

derive_birth_future_inputs(*, case, record, role_tokens, display_master)
requires explicit original inputs and always calls validate_birth_source, then
bind_birth_arm on its immutable reconstructed snapshots. No caller inventory,
bound observation, validation flag, or cached receipt is accepted.

The universe contains every world-bound QUERY/EVENT/PORT (even unregistered),
plus every EVENT.GOT and effective world-edge destination NODE. Disclosure is
the candidate subset observed in retained parsed service fields, WORLD outcomes,
or actor operands. Task facts and omitted lifetime history never subtract IDs.
Task exceptions remain occurrence-specific scanner receipts. No text is parsed
again here and no new scanner exemption is introduced.

Candidate paths address the reconstructed source: role_tokens/key, or
case/construction/blocks/request/rows/decimal-index/got. A world_edges path ends
in two components denoting its exact (state, port) tuple key, not nested maps.
Disclosure receipts are unchanged FieldObservations with exact projection byte
spans, original source indices, owners and source-message hashes. All receipts
are bound to the returned source and projection hashes. They are hidden
evaluator data, never actor input or a scientific semantic object.

Authority: the prospective inventory source disposition identified below.
This non-material component supplies no semantic/registered-route inventory,
complete ScanInventory, native bytes, material, independent guard, C11 gate or
scientific readiness. It performs no file/network/model/tokenizer/GPU work.
Constructor consistency is not independent input-authority authentication.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_scan_inputs as scan_inputs
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs
from organism_v6 import composition_birth_stage2a_targets as targets


STATUS = "PARTIAL_SOURCE_ONLY"
SCHEMA_VERSION = "BIRTH_RETAINED_FUTURE_IDS_V1"
DISPOSITION_PATH = "research_notes/analysis/2026-09-13_stage2a_inventory_source_disposition.md"
DISPOSITION_SHA256 = "6f442bd1af56ca5a0b925ae56925b53207cfa9e1ef72f0c25315956da9987154"
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
SCIENCE_GATES = MappingProxyType(dict(source_inputs.SCIENCE_GATES))
LIMITATIONS = (
    "Future-ID component only; no semantic object, route inventory or complete ScanInventory.",
    "Exact retained-prefix disclosure, not inherited lifetime knowledge or a global task-ID exemption.",
    "Correlated constructor consistency, not independent provenance or authorization of supplied inputs.",
    "Evaluator-only source/field receipts; no native/material/C11/scientific readiness or promotion.",
)
_ROLE_KINDS = frozenset(("query", "event", "port"))
_ACTOR_KINDS = frozenset(("issued_query", "read_index_operand", "step_operand", "think_implicated"))


class FutureInputError(ValueError):
    """Future-ID source/provenance inconsistency or explicit bound failure."""


@dataclass(frozen=True)
class CandidateOrigin:
    role_key: str
    source_path: tuple[str, ...]


@dataclass(frozen=True)
class BirthFutureInputs:
    source: source_inputs.ValidatedBirthSource
    binding: scan_inputs.BoundScanInputs
    candidates: frozenset[bytes]
    disclosed: frozenset[bytes]
    future_identifiers: frozenset[bytes]
    candidate_provenance: Mapping[bytes, tuple[CandidateOrigin, ...]]
    disclosure_provenance: Mapping[bytes, tuple[scan_inputs.FieldObservation, ...]]

    status = STATUS
    schema_version = SCHEMA_VERSION
    disposition_sha256 = DISPOSITION_SHA256
    science_gates = SCIENCE_GATES
    limitations = LIMITATIONS
    inventory_completeness_verified = False
    native_chat_bytes_verified = False


def derive_birth_future_inputs(*, case: birth.BirthCase, record: targets.ArmRecord,
                              role_tokens: Mapping[str, str], display_master: bytes) -> BirthFutureInputs:
    """Rebuild first, derive whole-world candidates, subtract retained disclosure."""
    source = source_inputs.validate_birth_source(
        case=case, record=record, role_tokens=role_tokens, display_master=display_master,
    )
    binding = scan_inputs.bind_birth_arm(source.record, source.case, role_tokens=source.role_tokens)
    owners = {token: role for role, token in source.role_tokens.items()}
    origins = {}

    def add(token, path, expected_kinds):
        role = owners.get(token)
        if role is None or role.rsplit("/", 1)[-1] not in expected_kinds:
            raise FutureInputError("unbound_or_mistyped_candidate_source")
        entries = origins.setdefault(token.encode("ascii"), set())
        entries.add(CandidateOrigin(role, ("role_tokens", role)))
        entries.add(CandidateOrigin(role, path))

    for role, token in source.role_tokens.items():
        if role.rsplit("/", 1)[-1] in _ROLE_KINDS:
            add(token, ("role_tokens", role), _ROLE_KINDS)
    for request, block in source.case.construction.blocks.items():
        if block.kind == "EVENTS":
            for index, row in enumerate(block.rows):
                add(row.got, ("case", "construction", "blocks", request, "rows", str(index), "got"),
                    ("node",))
    for (state, port), destination in source.case.construction.world_edges.items():
        add(destination, ("case", "construction", "world_edges", state, port), ("node",))
    candidates = frozenset(origins)
    disclosures = {}
    for observation in binding.observations:
        eligible = (observation.origin == "service"
                    or (observation.origin == "host" and observation.kind == "current"
                        and observation.path.endswith("/WORLD/CURRENT"))
                    or (observation.origin == "actor" and observation.kind in _ACTOR_KINDS
                        and observation.path.endswith("/action/operand")))
        if eligible and observation.value in candidates:
            disclosures.setdefault(observation.value, []).append(observation)
    disclosed = frozenset(disclosures)
    future = candidates - disclosed
    if len(future) > scanner.BOUNDS["future_identifiers"]:
        raise FutureInputError("future_identifier_bound_exceeded")
    return BirthFutureInputs(
        source, binding, candidates, disclosed, future,
        MappingProxyType({token: tuple(sorted(entries, key=lambda entry: (entry.role_key, entry.source_path)))
                          for token, entries in sorted(origins.items())}),
        MappingProxyType({token: tuple(entries) for token, entries in sorted(disclosures.items())}),
    )
