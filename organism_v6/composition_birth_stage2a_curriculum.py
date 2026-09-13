"""In-memory paired birth compiler over explicit bindings; no material output."""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6 import composition_birth_stage2a_tape as tape
from organism_v6.composition_birth_stage2a_primitives import adapter_seed


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(targets.SCIENCE_GATES, False))


@dataclass(frozen=True)
class BirthCurriculum:
    pairs: tuple
    paired_targets: tuple
    batches: tuple
    target_hashes: Mapping
    command_counts: Mapping
    prefix_accounting: Mapping
    master_sha256: str
    adapter_initialization_seed: int
    status: str = STATUS
    memo_sha256: str = birth.MEMO_SHA256
    clarification_sha256: str = birth.CLARIFICATION_SHA256


def compile_birth_curriculum(*, role_tokens_by_world, master):
    """Build all 64 cases/256 paired targets and the conditional update tape.

    Display ordering and initialization/dropout seeds use this same explicit
    master. No allocator, authenticated tokenizer, tensor mask, optimizer,
    model, filesystem writer, or independent semantic checker is invoked.
    Prefix counts are authored byte/message counts, never token/GPU costs.
    """
    initial_seed = adapter_seed(master)
    names = tuple(f"p{index:02d}" for index in range(32))
    if not isinstance(role_tokens_by_world, Mapping) or set(role_tokens_by_world) != set(names):
        raise ValueError("complete_birth_world_roster_required")
    bindings = {}
    seen = set()
    for name in names:
        provided = role_tokens_by_world[name]
        if not isinstance(provided, Mapping):
            raise ValueError("per_world_role_mapping_required")
        bindings[name] = dict(provided)
        for token in bindings[name].values():
            if type(token) is not str or token in seen:
                raise ValueError("invalid_or_cross_world_duplicate_token")
            seen.add(token)
    pairs = tuple(birth.build_birth_pair(world=name, role_tokens=bindings[name],
                                        display_master=master) for name in names)
    rendered = tuple(pairing for pair in pairs for case in pair.cases
                     for pairing in targets.serialize_birth_case(case, role_tokens=pair.role_tokens))
    unit_ids = tuple(pair.closed.unit.unit_id for pair in rendered)
    if unit_ids != tape.unit_identifiers():
        raise ValueError("birth_target_roster_mismatch")
    commands = Counter(pair.closed.unit.command for pair in rendered)
    if commands != {"READ": 96, "STEP": 64, "THINK": 64, "STOP": 32}:
        raise ValueError("birth_command_counts_mismatch")
    for pair in rendered:
        if pair.closed.unit is not pair.atom_local.unit:
            raise ValueError("paired_target_identity_mismatch")
    accounting = {}
    for arm, records in (("CLOSED", tuple(pair.closed for pair in rendered)),
                         ("ATOM_LOCAL", tuple(pair.atom_local for pair in rendered))):
        accounting[arm] = MappingProxyType({
            "unit_count": len(records),
            "prefix_messages": sum(len(record.prefix) for record in records),
            "prefix_content_bytes": sum(record.content_bytes for record in records),
            "prefix_serialized_bytes": sum(record.serialized_bytes for record in records),
            "target_content_bytes": sum(len(record.unit.target_bytes) for record in records),
        })
    accounting["CLOSED_MINUS_ATOM_LOCAL"] = MappingProxyType({
        key: accounting["CLOSED"][key] - accounting["ATOM_LOCAL"][key]
        for key in accounting["CLOSED"]
    })
    if accounting["CLOSED_MINUS_ATOM_LOCAL"]["target_content_bytes"] != 0:
        raise ValueError("unequal_target_byte_dose")
    hashes = MappingProxyType({pair.closed.unit.unit_id: pair.closed.unit.target_sha256 for pair in rendered})
    return BirthCurriculum(pairs, rendered, tape.build_presentation_tape(master=master, unit_ids=unit_ids),
                           hashes, MappingProxyType(dict(commands)), MappingProxyType(accounting),
                           sha256(master).hexdigest(), initial_seed)
