"""Bounded CPU-only equality join over supplied evaluator-custody core inputs.

Checks the exact 512 birth / 64 intervention / 16 chain-world identity sets,
including both chain members and every supplied witness pre-action boundary.
The existing independent JSON checker verifies every full envelope anew; exact
core, receipt and signature bytes must agree with that verification. Only the
existing complete core and complete four-radius signature hashes are joined.
An individual radius intersection is not a collision here.

This is supplied-input consistency, NOT source authentication. Full constructor
provenance, world completeness, root ownership, contamination and visibility
remain the caller's upstream duty, including birth identity-to-source binding.
Encoded source witnesses establish coverage of the supplied chain, not that the
chain is authentic. No supplied green flag can discharge those duties. A clean
join grants no native, model, GPU or scientific-claim authorization. No source
construction, anchor changes, padding, filesystem/network I/O or model calls.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_chain_core_inputs as chain_inputs
from organism_v6 import composition_birth_stage2a_checker as checker
from organism_v6 import composition_birth_stage2a_core_inputs as birth_inputs_module
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_held_core_inputs as held_inputs
from organism_v6 import composition_birth_stage2a_worlds as worlds


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(wire.SCIENCE_GATES, False))
BOUNDS = MappingProxyType({"blob_bytes": checker.MAX_BYTES,
                          "total_bytes": 2 * 1024 * 1024 * 1024,
                          "chain_boundaries_per_member": wire.CALL_CAP})
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
GO_SOURCE_READY = False
MEMBERS = ("m0", "m1")
BIRTH_IDENTITIES = frozenset(
    (f"p{pair:02d}/{member}/u{unit}", arm)
    for pair in range(32) for member in MEMBERS for unit in range(4)
    for arm in ("CLOSED", "ATOM_LOCAL"))
INTERVENTION_IDENTITIES = frozenset(
    (f"{skill}_k{pair}", member)
    for skill in ("seek", "prospect", "check", "continue")
    for pair in range(8) for member in MEMBERS)
CHAIN_WORLDS = frozenset(f"h{world:02d}" for world in range(16))


class SeparationError(ValueError):
    """Incomplete, unbounded or inconsistent supplied inputs; no join result."""


@dataclass(frozen=True, order=True)
class HeldIdentity:
    panel: str
    world: str
    member: str
    decision_index: int | None


@dataclass(frozen=True)
class Collision:
    """Every birth identity collides with every held identity in this group."""

    sha256: str
    birth_identities: tuple[tuple[str, str], ...]
    held_identities: tuple[HeldIdentity, ...]

    @property
    def pair_count(self):
        return len(self.birth_identities) * len(self.held_identities)


@dataclass(frozen=True)
class SeparationReport:
    core_collisions: tuple[Collision, ...]
    signature_collisions: tuple[Collision, ...]
    counts: Mapping

    status = STATUS
    cpu_only = True
    source_authenticated = False
    full_constructor_provenance_checked = False
    constructor_provenance_is_upstream_duty = True
    native_authorized = False
    native_ready = False
    science_gates = SCIENCE_GATES

    @property
    def separated(self):
        """Only absence of the two supplied-input hash intersections."""
        return not (self.core_collisions or self.signature_collisions)


def _require(condition, message):
    if not condition:
        raise SeparationError(message)


def _json(raw):
    return checker.loads_canonical_json(raw)


def _bytes(value):
    return checker.canonical_json_bytes(value)


def _preflight(birth_inputs, intervention_inputs, chain_core_inputs):
    _require(isinstance(birth_inputs, Mapping) and len(birth_inputs) == 512,
             "exact_512_birth_mapping_required")
    birth_records = dict(birth_inputs)
    _require(set(birth_records) == BIRTH_IDENTITIES, "exact_birth_identity_set_required")
    _require(type(intervention_inputs) in (tuple, list) and len(intervention_inputs) == 64,
             "exact_64_intervention_sequence_required")
    _require(type(chain_core_inputs) in (tuple, list) and len(chain_core_inputs) == 16,
             "exact_16_chain_sequence_required")
    interventions, chains = tuple(intervention_inputs), tuple(chain_core_inputs)
    _require(all(type(record) is birth_inputs_module.BirthCoreInputs
                 and (record.unit_id, record.arm) == identity
                 for identity, record in birth_records.items()), "birth_identity_or_type_mismatch")
    _require(all(type(record) is held_inputs.InterventionCoreInputs for record in interventions),
             "typed_intervention_inputs_required")
    _require({(record.world, record.member) for record in interventions} == INTERVENTION_IDENTITIES,
             "exact_intervention_identity_set_required")
    _require(all(type(record) is chain_inputs.ChainCoreInputs for record in chains),
             "typed_chain_inputs_required")
    _require({record.world for record in chains} == CHAIN_WORLDS, "exact_chain_world_set_required")
    records = list(birth_records.values()) + list(interventions) + list(chains)
    for chain in chains:
        _require(type(chain.boundaries) is tuple
                 and 2 <= len(chain.boundaries) <= 2 * BOUNDS["chain_boundaries_per_member"]
                 and all(type(boundary) is chain_inputs.ChainCoreBoundary for boundary in chain.boundaries),
                 "bounded_typed_chain_boundaries_required")
        records.extend(chain.boundaries)
    total = 0
    for record in records:
        for field in fields(record):
            if field.name.endswith("_bytes") or field.name == "checker_payload":
                raw = getattr(record, field.name)
                _require(type(raw) is bytes and 0 < len(raw) <= BOUNDS["blob_bytes"],
                         "bounded_exact_bytes_required: " + field.name)
                total += len(raw)
                _require(total <= BOUNDS["total_bytes"], "aggregate_byte_bound_exceeded")
    return birth_records, interventions, chains


def _checked_hashes(record):
    receipt = checker.check_graph_core_json(record.checker_payload)
    _require(record.receipt_bytes == _bytes(receipt), "exact_checker_receipt_bytes_mismatch")
    envelope = _json(record.checker_payload)
    _require(record.core_bytes == _bytes(envelope["core"]), "exact_core_bytes_mismatch")
    hashes = receipt["hashes"]
    if type(record) is not birth_inputs_module.BirthCoreInputs:
        _require(record.core_sha256 == hashes["core"], "core_sha256_mismatch")
        _require(record.signature_bytes == _bytes(hashes["radii"]), "complete_signature_bytes_mismatch")
        _require(record.signature_sha256 == hashes["signature"], "signature_sha256_mismatch")
    if type(record) is held_inputs.InterventionCoreInputs:
        for name, value in (("world_graph", envelope["world_graph"]),
                            ("public_graph", envelope["core"]["public_graph"])):
            _require(getattr(record, name + "_bytes") == _bytes(value), name + "_bytes_mismatch")
            _require(getattr(record, name + "_sha256") == hashes[name], name + "_sha256_mismatch")
    return hashes


def _binding(record, hashes, source_bytes, role_bytes, module):
    binding = _json(record.binding_receipt_bytes)
    expected = {"schema_version": ("M2A-CHAIN-CORE-BINDING-V1" if module is chain_inputs
                                   else held_inputs.BINDING_SCHEMA_VERSION),
                "status": STATUS, "binding_sha256": module.BINDING_SHA256,
                "world": record.world, "member": record.member, "hashes": hashes}
    if module is chain_inputs:
        expected["decision_index"] = record.decision_index
    for name, raw in (("source", source_bytes), ("role_bindings", role_bytes),
                      ("prefix", record.prefix_bytes), ("target", record.target_bytes),
                      ("checker_payload", record.checker_payload), ("checker_receipt", record.receipt_bytes)):
        expected[name + "_sha256"] = sha256(raw).hexdigest()
    _require(type(binding) is dict and all(name in binding and _bytes(binding[name]) == _bytes(value)
                                         for name, value in expected.items()), "binding_receipt_mismatch")


def _source_fields(value, cls):
    _require(type(value) is dict and set(value) == {"dataclass", "fields"}
             and value["dataclass"] == cls.__module__ + "." + cls.__qualname__,
             "encoded_source_dataclass_required")
    entries = value["fields"]
    names = [field.name for field in fields(cls)]
    _require(type(entries) is list and len(entries) == len(names)
             and all(type(entry) is list and len(entry) == 2 and entry[0] == name
                     for entry, name in zip(entries, names)), "encoded_source_fields_mismatch")
    return dict(entries)


def _source_tuple(value):
    _require(type(value) is dict and set(value) == {"tuple"} and type(value["tuple"]) is list,
             "encoded_source_tuple_required")
    return value["tuple"]


def _message(role, content):
    return {"dataclass": held.Message.__module__ + ".Message",
            "fields": [["role", role], ["content", content]]}


def _chain_witnesses(chain):
    source = _source_fields(_json(chain.source_bytes), held.ChainWorld)
    construction = _source_fields(source["construction"], worlds.OrdinaryConstruction)
    _require(construction["world"] == chain.world, "chain_source_world_mismatch")
    members = _source_tuple(source["members"])
    _require(len(members) == 2, "exact_two_chain_source_members_required")
    witnesses = {}
    for encoded in members:
        member = _source_fields(encoded, held.ChainMember)
        identity = member["member"]
        _require(type(identity) is str and identity in MEMBERS and identity not in witnesses,
                 "exact_chain_source_member_set_required")
        task = _source_fields(member["task"], wire.TaskState)
        _require(all(type(value) is str for value in task.values()), "chain_task_strings_required")
        trace = _source_tuple(member["expected_trace"])
        _require(0 < len(trace) <= BOUNDS["chain_boundaries_per_member"], "bounded_chain_witness_required")
        prefix = [_message("system", wire.SYSTEM_MESSAGE),
                  _message("user", f'TASK\nSTART {task["start"]}\nGOAL {task["goal"]}\nCURRENT {task["current"]}')]
        boundaries = []
        for encoded_turn in trace:
            turn = _source_fields(encoded_turn, held.WitnessTurn)
            _require(type(turn["action"]) is str and bool(turn["action"])
                     and (turn["response"] is None or type(turn["response"]) is str),
                     "chain_witness_action_response_required")
            boundaries.append((_bytes({"tuple": prefix}), turn["action"].encode("ascii")))
            if turn["response"] is not None:
                prefix.extend((_message("assistant", turn["action"]), _message("user", turn["response"])))
        witnesses[identity] = tuple(boundaries)
    return witnesses


def _intervention_source(record):
    source = _json(record.source_bytes)
    _require(type(source) is dict and source["construction"]["world"] == record.world
             and source["member"] == record.member, "intervention_source_identity_mismatch")
    _require(record.prefix_bytes == _bytes(source["expected_causal_prefix"]), "intervention_source_prefix_mismatch")
    _require(record.target_bytes == source["expected_target"]["bytes"].encode("ascii"),
             "intervention_source_target_mismatch")


def _collisions(birth_rows, held_rows, field):
    birth_index, held_index = {}, {}
    for identity, hashes in birth_rows:
        birth_index.setdefault(hashes[field], []).append(identity)
    for identity, hashes in held_rows:
        held_index.setdefault(hashes[field], []).append(identity)
    return tuple(Collision(digest, tuple(sorted(birth_index[digest])), tuple(sorted(held_index[digest])))
                 for digest in sorted(birth_index.keys() & held_index.keys()))


def check_held_birth_separation(*, birth_inputs, intervention_inputs, chain_core_inputs):
    """Join complete supplied populations, or raise SeparationError before reporting.

    birth_inputs: mapping (unit_id, arm) -> BirthCoreInputs, exactly 512.
    intervention_inputs: list/tuple of all 64 InterventionCoreInputs.
    chain_core_inputs: list/tuple of all 16 ChainCoreInputs, both members and
    contiguous indices 0..len(supplied expected_trace)-1 for every witness.

    Collision groups losslessly represent their Cartesian identity pairs; they
    are not truncated samples. Counts distinguish groups from pairs. All blobs
    are nonempty bytes <=32 MiB, aggregate supplied bytes <=2 GiB (counting
    repeated occurrences); each chain member has at most CALL_CAP boundaries.
    This API takes no provenance-approval flags and cannot certify provenance.
    """
    try:
        births, interventions, chains = _preflight(birth_inputs, intervention_inputs, chain_core_inputs)
        birth_rows = [(identity, _checked_hashes(record)) for identity, record in sorted(births.items())]
        held_rows = []
        for record in sorted(interventions, key=lambda item: (item.world, item.member)):
            hashes = _checked_hashes(record)
            _binding(record, hashes, record.source_bytes, record.role_bindings_bytes, held_inputs)
            _intervention_source(record)
            held_rows.append((HeldIdentity("intervention", record.world, record.member, None), hashes))
        for chain in sorted(chains, key=lambda item: item.world):
            witnesses = _chain_witnesses(chain)
            expected = {(member, index) for member, boundaries in witnesses.items()
                        for index in range(len(boundaries))}
            _require(all(boundary.world == chain.world and type(boundary.member) is str
                         and type(boundary.decision_index) is int for boundary in chain.boundaries),
                     "chain_boundary_identity_mismatch")
            actual = {(boundary.member, boundary.decision_index) for boundary in chain.boundaries}
            _require(len(chain.boundaries) == len(expected) and actual == expected,
                     "complete_contiguous_chain_boundaries_required")
            for boundary in sorted(chain.boundaries, key=lambda item: (item.member, item.decision_index)):
                _require((boundary.prefix_bytes, boundary.target_bytes)
                         == witnesses[boundary.member][boundary.decision_index], "chain_witness_boundary_bytes_mismatch")
                hashes = _checked_hashes(boundary)
                _binding(boundary, hashes, chain.source_bytes, chain.role_bindings_bytes, chain_inputs)
                held_rows.append((HeldIdentity("chain", chain.world, boundary.member, boundary.decision_index), hashes))
        core = _collisions(birth_rows, held_rows, "core")
        signature = _collisions(birth_rows, held_rows, "signature")
        counts = {"birth_records": len(birth_rows), "birth_units": len(birth_rows) // 2,
                  "intervention_members": len(interventions), "chain_worlds": len(chains),
                  "chain_members": 2 * len(chains), "chain_boundaries": len(held_rows) - len(interventions),
                  "held_records": len(held_rows), "checked_envelopes": len(birth_rows) + len(held_rows)}
        for name, collisions in (("core", core), ("signature", signature)):
            counts[name + "_collision_hashes"] = len(collisions)
            counts[name + "_collision_pairs"] = sum(collision.pair_count for collision in collisions)
            counts[name + "_birth_distinct"] = len({hashes[name] for unused, hashes in birth_rows})
            counts[name + "_held_distinct"] = len({hashes[name] for unused, hashes in held_rows})
        return SeparationReport(core, signature, MappingProxyType(counts))
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError) as error:
        if isinstance(error, SeparationError):
            raise
        raise SeparationError("supplied_input_validation_failed: " + str(error)) from error
