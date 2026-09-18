"""Lossless, evaluator-only shared birth source custody for the v6 CPU seam.

One constructor call retains both complete cases, explicit roles and exact
display-master bytes. One source-tree encoding supplies the shared document
and case pins; arm receipts are rendered and pinned once, not by repeatedly
encoding the pair. Public case/source access returns detached frozen snapshots
so changing even a dataclass through its Python internals cannot poison the
trusted cache. Snapshot copying still costs the size of the selected case.

Recovery reads only fixed constructor inputs, rebuilds using the local
constructor, and compares the entire canonical document byte for byte. Encoded
class names are data, never import instructions. Hashes address retained values
and are never accepted instead of them. Identical records from independently
constructed identical inputs are intentionally indistinguishable.

This binds caller-supplied roles/master, not independently authorized allocator
provenance. Allocator admission, typed public boundaries, route/leak inventories,
full-population qualification and native/model/science admission remain outside
this module. Hidden shared bytes and snapshots must not be sent to an actor.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6.composition_birth_stage2a_primitives import canonical_json, parse_canonical_json


STATUS = "PARTIAL_SOURCE_ONLY"
SCHEMA_VERSION = "BIRTH_SHARED_SOURCE_CUSTODY_V6_1"
CONSTRUCTOR_API = source_inputs.CONSTRUCTOR_API
CONTRACT_HASHES = source_inputs.CONTRACT_HASHES
ALLOCATOR_ADMISSION = "NOT_VERIFIED_MAIN_NATIVE_TASK"
BOUNDS = MappingProxyType({**source_inputs.BOUNDS, "shared_bytes": 64 * 1024 * 1024})
SCIENCE_GATES = MappingProxyType({**source_inputs.SCIENCE_GATES, "allocator_admission": False})
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
ValidatedBirthSource = source_inputs.ValidatedBirthSource


class CustodyError(source_inputs.SourceInputError):
    """A constructor input, record or lossless shared document does not match."""


def _snapshot(value, memo=None):
    if memo is None:
        memo = {}
    if value is None or type(value) in (str, bytes, int, bool):
        return value
    identity = id(value)
    if identity in memo:
        return memo[identity]
    if is_dataclass(value):
        result = type(value)(**{field.name: _snapshot(getattr(value, field.name), memo)
                                for field in fields(value)})
    elif type(value) is tuple:
        result = tuple(_snapshot(item, memo) for item in value)
    elif type(value) is MappingProxyType:
        result = MappingProxyType({_snapshot(key, memo): _snapshot(item, memo)
                                   for key, item in value.items()})
    else:
        raise CustodyError("unsupported_constructor_snapshot_type")
    memo[identity] = result
    return result


def _inputs(world, role_tokens, display_master):
    if type(display_master) is not bytes or len(display_master) > BOUNDS["master_bytes"]:
        raise CustodyError("bounded_explicit_display_master_bytes_required")
    if not isinstance(role_tokens, Mapping) or len(role_tokens) > BOUNDS["role_entries"]:
        raise CustodyError("bounded_explicit_role_mapping_required")
    copied = dict(role_tokens)
    if len(copied) > BOUNDS["role_entries"] or any(
            type(role) is not str or not role.isascii() or len(role) > BOUNDS["role_characters"]
            or type(token) is not str or not token.isascii() or len(token) != 17
            for role, token in copied.items()):
        raise CustodyError("invalid_role_binding_shape")
    birth.describe_birth_case(world, "m0")
    return copied


def _counts(pair):
    return {
        "cases": len(pair.cases), "role_entries": len(pair.role_tokens),
        "targets": sum(len(case.targets) for case in pair.cases),
        "arm_records": 2 * sum(len(case.targets) for case in pair.cases),
        "members": [{
            "member": case.descriptor.member,
            "registry_entries": len(case.construction.registry),
            "service_blocks": len(case.construction.blocks),
            "service_rows": sum(len(block.rows) for block in case.construction.blocks.values()),
            "effective_edges": len(case.construction.world_edges),
            "trace_turns": len(case.trace), "facts": len(fields(case.facts)),
            "targets": len(case.targets),
        } for case in pair.cases],
    }


def _receipt(case, record, roles, case_digest, roles_digest, master_digest):
    record_digest = sha256(canonical_json(source_inputs._digest_value(record))).hexdigest()
    provenance = canonical_json({
        "schema": source_inputs.SCHEMA_VERSION, "constructor": CONSTRUCTOR_API,
        "contract_hashes": dict(CONTRACT_HASHES), "world": case.descriptor.world,
        "member": case.descriptor.member, "unit_id": record.unit.unit_id, "arm": record.arm,
        "case_sha256": case_digest, "record_sha256": record_digest,
        "role_tokens_sha256": roles_digest, "display_master_sha256": master_digest,
    })
    return ValidatedBirthSource(case, record, roles, case_digest, record_digest,
                                roles_digest, master_digest, provenance, sha256(provenance).hexdigest())


@dataclass(frozen=True, slots=True, init=False, eq=False)
class BirthSourceCustody:
    """Constructor-bound pair custody, not an allocation or admission authority."""

    _pair: birth.BirthPair
    _sources: Mapping
    shared_bytes: bytes
    shared_sha256: str

    status = STATUS
    schema_version = SCHEMA_VERSION
    science_gates = SCIENCE_GATES
    allocator_admission = ALLOCATOR_ADMISSION

    def __init__(self, *, world, role_tokens, display_master):
        try:
            copied = _inputs(world, role_tokens, display_master)
            pair = birth.build_birth_pair(world=world, role_tokens=copied, display_master=display_master)
            encoded_pair = source_inputs._digest_value(pair)
            encoded_cases = dict(encoded_pair["fields"])["cases"]["tuple"]
            roles_digest = sha256(canonical_json(dict(pair.role_tokens))).hexdigest()
            master_digest = sha256(display_master).hexdigest()
            case_pins = {}
            sources = {}
            for case, encoded_case in zip(pair.cases, encoded_cases):
                case_digest = sha256(canonical_json(encoded_case)).hexdigest()
                case_pins[case.descriptor.member] = case_digest
                for paired in targets.serialize_birth_case(case, role_tokens=pair.role_tokens):
                    for record in (paired.closed, paired.atom_local):
                        identity = (record.unit.unit_id, record.arm)
                        if identity in sources:
                            raise CustodyError("duplicate_constructor_record")
                        sources[identity] = _receipt(case, record, pair.role_tokens,
                                                     case_digest, roles_digest, master_digest)
            raw = canonical_json({
                "schema": SCHEMA_VERSION, "constructor": CONSTRUCTOR_API,
                "constructor_version": birth.MEMO_SHA256,
                "source_schema": source_inputs.SCHEMA_VERSION,
                "renderer": "organism_v6.composition_birth_stage2a_targets.serialize_birth_case",
                "renderer_contract_hashes": {"v4": targets.MEMO_SHA256,
                                              "builder_source_clarification_v1": targets.CLARIFICATION_SHA256},
                "contract_hashes": dict(CONTRACT_HASHES), "allocator_admission": ALLOCATOR_ADMISSION,
                "display_master": {"bytes_hex": display_master.hex()}, "pair": encoded_pair,
                "counts": _counts(pair), "case_sha256": case_pins,
                "role_tokens_sha256": roles_digest, "display_master_sha256": master_digest,
            })
            if len(raw) > BOUNDS["shared_bytes"]:
                raise CustodyError("shared_source_byte_limit_exceeded")
            object.__setattr__(self, "_pair", pair)
            object.__setattr__(self, "_sources", MappingProxyType(sources))
            object.__setattr__(self, "shared_bytes", raw)
            object.__setattr__(self, "shared_sha256", sha256(raw).hexdigest())
        except CustodyError:
            raise
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
            raise CustodyError("custody_constructor_validation_failed: " + str(error)) from error

    @property
    def cases(self):
        """Return both complete cases without exposing trusted cached objects."""
        return _snapshot(self._pair.cases)

    def _lookup_record(self, record):
        if (type(record) is not targets.ArmRecord or type(record.unit) is not targets.TargetUnit
                or type(record.arm) is not str or type(record.unit.unit_id) is not str):
            raise CustodyError("typed_arm_record_required")
        expected = self._sources.get((record.unit.unit_id, record.arm))
        if expected is None or not source_inputs._same_source(record, expected.record):
            raise CustodyError("exact_constructor_record_mismatch")
        return expected

    def record_for(self, record):
        """Authenticate only the small record and return a detached snapshot."""
        return _snapshot(self._lookup_record(record).record)

    def source_for(self, record):
        """Match every typed record field; return detached, precomputed source pins."""
        expected = self._lookup_record(record)
        return _snapshot(expected)

    def verify_shared(self, candidate_bytes):
        """Require the exact complete constructor-derived bytes, not claimed hashes."""
        if type(candidate_bytes) is not bytes or candidate_bytes != self.shared_bytes:
            raise CustodyError("exact_shared_source_mismatch")
        return True

    @classmethod
    def from_bytes(cls, candidate_bytes):
        """Rebuild fixed inputs and verify all values/pins; no allocation admission.

        This self-contained recovery cannot authenticate an external expected
        master or role allocation. Use the original custody's verify_shared
        when matching a document against independently selected inputs.
        """
        if type(candidate_bytes) is not bytes or len(candidate_bytes) > BOUNDS["shared_bytes"]:
            raise CustodyError("bounded_shared_source_bytes_required")
        try:
            document = parse_canonical_json(candidate_bytes)
            if type(document) is not dict or document.get("schema") != SCHEMA_VERSION:
                raise CustodyError("unsupported_shared_source_schema")
            encoded_pair = document["pair"]
            qualified = birth.BirthPair.__module__ + "." + birth.BirthPair.__qualname__
            if (type(encoded_pair) is not dict or set(encoded_pair) != {"dataclass", "fields"}
                    or encoded_pair["dataclass"] != qualified):
                raise CustodyError("fixed_birth_pair_schema_required")
            entries = encoded_pair["fields"]
            if (type(entries) is not list or len(entries) != len(fields(birth.BirthPair))
                    or any(type(entry) is not list or len(entry) != 2 or entry[0] != field.name
                           for entry, field in zip(entries, fields(birth.BirthPair)))):
                raise CustodyError("fixed_birth_pair_fields_required")
            pair_fields = dict(entries)
            encoded_roles = pair_fields["role_tokens"]
            if type(encoded_roles) is not dict or set(encoded_roles) != {"mapping"}:
                raise CustodyError("fixed_role_mapping_required")
            role_entries = encoded_roles["mapping"]
            if (type(role_entries) is not list or len(role_entries) > BOUNDS["role_entries"]
                    or any(type(entry) is not list or len(entry) != 2
                           or any(type(item) is not str for item in entry) for entry in role_entries)):
                raise CustodyError("invalid_role_binding_shape")
            roles = dict(role_entries)
            if len(roles) != len(role_entries):
                raise CustodyError("duplicate_role_binding")
            encoded_master = document["display_master"]
            if type(encoded_master) is not dict or set(encoded_master) != {"bytes_hex"}:
                raise CustodyError("fixed_display_master_bytes_required")
            master_hex = encoded_master["bytes_hex"]
            if type(master_hex) is not str or len(master_hex) > 2 * BOUNDS["master_bytes"]:
                raise CustodyError("bounded_explicit_display_master_bytes_required")
            master = bytes.fromhex(master_hex)
            if master.hex() != master_hex:
                raise CustodyError("canonical_display_master_hex_required")
            rebuilt = cls(world=pair_fields["world"], role_tokens=roles, display_master=master)
            rebuilt.verify_shared(candidate_bytes)
            return rebuilt
        except CustodyError:
            raise
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
            raise CustodyError("invalid_shared_source_document: " + str(error)) from error
