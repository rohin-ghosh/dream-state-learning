"""Pure full-constructor consistency binding for one birth case and arm record.

validate_birth_source(*, case: BirthCase, record: ArmRecord, role_tokens:
Mapping[str, str], display_master: bytes) -> ValidatedBirthSource

Rebuild the COMPLETE BirthPair using the supplied case world, copied bindings,
and exact master bytes. Compare every selected BirthCase dataclass field,
including all hidden/off-trace blocks, raw registry bytes, world edges, trace,
facts, targets, and source designations. Then compare the complete ArmRecord
against one of the eight freshly rendered records for that selected member.
Equality is recursive and type-strict (bool is not int); source mapping fields
may be plain dicts or mapping proxies, with insertion order ignored. No caller
cache, digest, success flag, or oracle-only replay substitutes for rebuilding.

Returned case/record/bindings are freshly reconstructed immutable snapshots,
not references to caller-owned maps. This object contains hidden evaluator
data: it is NOT an actor request or public projection, nor an authority token.
Revalidate explicit inputs rather than trusting a caller-created receipt.

Digests use the source canonical_json API. Case/record digest trees encode
dataclasses as {dataclass: qualified class name, fields: ordered name/value
pairs}, mappings as {mapping: sorted encoded key/value pairs}, tuples as
{tuple: encoded items}, and bytes as {bytes_hex: lowercase hex}; scalar values
are unchanged. This preserves tuple edge keys and exact bytes without repr or
pickle. Role bindings use a canonical string dictionary. Provenance bytes bind
these digests, the exact master SHA-256, world/member/record identity, API name,
schema version, and adopted source contract pins. They are an in-memory source
receipt, NOT a material schema, signature, independent ancestry proof, or proof
that caller-selected bindings/master are the scientifically authorized inputs.

Bounds are implementation limits only: <=32768 role entries, <=256 ASCII
characters per role key, exact 17-character ASCII tokens, and <=1 MiB master.
All byte-valued masters accepted by the constructor (including empty/binary)
remain supported within that bound. The reconstructed source shape bounds case
and record comparison; no arbitrary caller object graph is serialized.

No semantic/future/route inventory definitions or chronology are inferred.
No leak scanner, native chat/template, tokenizer/model, file/network/GPU,
material root, complete guard, C11 enforcement, or promotion is supplied.
All science/readiness gates remain false. Validation is correlated with the
existing constructor and renderer, not an independent scientific checker.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6.composition_birth_stage2a_primitives import canonical_json


STATUS = "PARTIAL_SOURCE_ONLY"
SCHEMA_VERSION = "BIRTH_FULL_CONSTRUCTOR_SOURCE_V1"
CONSTRUCTOR_API = "organism_v6.composition_birth_stage2a_birth.build_birth_pair"
CONTRACT_HASHES = MappingProxyType({
    "v4": birth.MEMO_SHA256,
    "builder_source_clarification_v1": birth.CLARIFICATION_SHA256,
})
BOUNDS = MappingProxyType({"role_entries": 32768, "role_characters": 256, "master_bytes": 1048576})
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
SCIENCE_GATES = MappingProxyType(dict.fromkeys((*birth.SCIENCE_GATES,
    "complete_guard", "native_chat_bytes", "inventory_completeness",
    "independent_source_authentication", "full_provenance", "C11_readiness"), False))
LIMITATIONS = (
    "Constructor/renderer consistency only, not independent source or input-authority certification.",
    "Only the supplied selected member is compared; the complete pair is rebuilt, not caller-authenticated.",
    "Hidden evaluator snapshots must not be sent to the actor.",
    "No semantic/future/route inventory definitions, completeness, or leak scan supplied.",
    "No native/template/material/complete guard/C11/scientific readiness or promotion.",
)


class SourceInputError(ValueError):
    """Explicit inputs do not match the complete prospective source construction."""


@dataclass(frozen=True)
class ValidatedBirthSource:
    case: birth.BirthCase
    record: targets.ArmRecord
    role_tokens: Mapping
    case_sha256: str
    record_sha256: str
    role_tokens_sha256: str
    display_master_sha256: str
    provenance_bytes: bytes
    provenance_sha256: str

    status = STATUS
    schema_version = SCHEMA_VERSION
    science_gates = SCIENCE_GATES
    limitations = LIMITATIONS
    inventory_completeness_verified = False
    native_chat_bytes_verified = False


def _same_source(actual, expected):
    if type(expected) is MappingProxyType:
        if type(actual) not in (dict, MappingProxyType) or len(actual) != len(expected):
            return False
        return all(_same_source(actual_key, expected_key) and _same_source(actual_value, expected_value)
                   for (actual_key, actual_value), (expected_key, expected_value)
                   in zip(sorted(actual.items()), sorted(expected.items())))
    if type(actual) is not type(expected):
        return False
    if is_dataclass(expected):
        return all(_same_source(getattr(actual, field.name), getattr(expected, field.name))
                   for field in fields(expected))
    if type(expected) is tuple:
        return len(actual) == len(expected) and all(_same_source(left, right) for left, right in zip(actual, expected))
    if expected is None or type(expected) in (str, bytes, int, bool):
        return actual == expected
    raise SourceInputError("unsupported_constructor_value_type")


def _digest_value(value):
    if is_dataclass(value):
        return {"dataclass": type(value).__module__ + "." + type(value).__qualname__,
                "fields": [[field.name, _digest_value(getattr(value, field.name))] for field in fields(value)]}
    if type(value) is MappingProxyType:
        return {"mapping": [[_digest_value(key), _digest_value(item)] for key, item in sorted(value.items())]}
    if type(value) is tuple:
        return {"tuple": [_digest_value(item) for item in value]}
    if type(value) is bytes:
        return {"bytes_hex": value.hex()}
    if value is None or type(value) in (str, int, bool):
        return value
    raise SourceInputError("unsupported_constructor_digest_type")


def validate_birth_source(*, case: birth.BirthCase, record: targets.ArmRecord,
                          role_tokens: Mapping, display_master: bytes) -> ValidatedBirthSource:
    """Rebuild and compare; success is source consistency, never a readiness gate."""
    if type(case) is not birth.BirthCase or type(case.descriptor) is not birth.BirthCaseDescriptor:
        raise SourceInputError("typed_birth_case_and_descriptor_required")
    if type(record) is not targets.ArmRecord:
        raise SourceInputError("typed_arm_record_required")
    if type(display_master) is not bytes or len(display_master) > BOUNDS["master_bytes"]:
        raise SourceInputError("bounded_explicit_display_master_bytes_required")
    if not isinstance(role_tokens, Mapping) or len(role_tokens) > BOUNDS["role_entries"]:
        raise SourceInputError("bounded_explicit_role_mapping_required")
    try:
        copied = dict(role_tokens)
        if len(copied) > BOUNDS["role_entries"] or any(
                type(role) is not str or not role.isascii() or len(role) > BOUNDS["role_characters"]
                or type(token) is not str or not token.isascii() or len(token) != 17
                for role, token in copied.items()):
            raise SourceInputError("invalid_role_binding_shape")
        descriptor = birth.describe_birth_case(case.descriptor.world, case.descriptor.member)
        rebuilt = birth.build_birth_pair(world=descriptor.world, role_tokens=copied, display_master=display_master)
        selected = next(member for member in rebuilt.cases if member.descriptor.member == descriptor.member)
        if not _same_source(case, selected):
            raise SourceInputError("full_constructor_case_mismatch")
        pairs = targets.serialize_birth_case(selected, role_tokens=rebuilt.role_tokens)
        rendered = next((candidate for pair in pairs for candidate in (pair.closed, pair.atom_local)
                         if _same_source(record, candidate)), None)
        if rendered is None:
            raise SourceInputError("exact_constructor_record_mismatch")
        case_digest = sha256(canonical_json(_digest_value(selected))).hexdigest()
        record_digest = sha256(canonical_json(_digest_value(rendered))).hexdigest()
        roles_digest = sha256(canonical_json(dict(rebuilt.role_tokens))).hexdigest()
        master_digest = sha256(display_master).hexdigest()
        provenance = canonical_json({
            "schema": SCHEMA_VERSION, "constructor": CONSTRUCTOR_API, "contract_hashes": dict(CONTRACT_HASHES),
            "world": descriptor.world, "member": descriptor.member,
            "unit_id": rendered.unit.unit_id, "arm": rendered.arm,
            "case_sha256": case_digest, "record_sha256": record_digest,
            "role_tokens_sha256": roles_digest, "display_master_sha256": master_digest,
        })
        return ValidatedBirthSource(selected, rendered, rebuilt.role_tokens, case_digest, record_digest,
                                    roles_digest, master_digest, provenance, sha256(provenance).hexdigest())
    except SourceInputError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise SourceInputError("source_constructor_validation_failed: " + str(error)) from error
