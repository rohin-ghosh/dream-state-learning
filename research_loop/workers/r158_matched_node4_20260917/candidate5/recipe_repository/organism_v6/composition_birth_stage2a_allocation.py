"""Source-only composition of the existing v3 finite inventory and allocator.

Custody is hidden evaluator data, never an actor projection. Authentication
means exact rederivation against an independently supplied master, not a
signature, authorization, native admission, or scientific readiness. There is
no default master, token selection, retry, file access, or runtime opening.
Reserved pools lack finite role inventories and are deliberately not invented.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6.composition_birth_stage2a_primitives import canonical_json


STATUS = "SOURCE_ONLY_FINITE_ALLOCATION"
SCHEMA_VERSION = "STAGE2A_FINITE_ALLOCATION_CUSTODY_V1"
ALLOCATOR_API = "organism_v6.composition_birth_stage2a.allocate_opaque_namespace"
INVENTORY_API = "organism_v6.composition_birth_stage2a.enumerate_symbolic_role_inventory"
COMPOSITION_API = "organism_v6.composition_birth_stage2a_allocation.allocate_stage2a"
DOMAINS = ("birth_train", "dose_intervention", "dose_chain", "generic_canary")
KINDS = wire.SYMBOLIC_KINDS
CONTRACT_HASHES = MappingProxyType({
    "v3": wire.ALLOCATION_MEMO_SHA256,
    "v4": "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1",
    "v5": "6ebefdba31de6f14416105c9509dbba06319f306bdd3472259a8d072ba9877e7",
    "v6": "119b97eb418e7b9586c1425c091b846f7eb7f100ab337ca03cc8b92df2b7b0b6",
})
SOURCE_HASHES = MappingProxyType({
    "organism_v6/composition_birth_stage2a.py":
        "1e750b7ae8151f122dbde6abc0ecb9e7b779af43b0fa0240fea1a6584741c40a",
    "organism_v6/composition_birth_stage2a_primitives.py":
        "f1fd8597ea83a3c31f3bff039a40b4553e82a55fefe96796a7e59930a04b7781",
})
UNALLOCATED_RESERVED_DOMAINS = ("confirmation_reserved", "writer_reserved")
LIMITATIONS = (
    "Only the four v3 finite role domains are allocated: 302948 tokens, not 352100.",
    "confirmation_reserved and writer_reserved: 4096 serials per kind each remain "
    "unallocated; they have no finite role list. Cross-collision checks exclude these pools.",
    "No separate null/shadow namespace or pool is allocated or collision-qualified.",
    "generic_canary/c12..c15 intentionally have no identifier and no role mapping.",
    "Source pins identify the bound source snapshot; no filesystem source audit occurs at runtime.",
    "Custody is hidden evaluator data, not actor input, a signature, native admission, "
    "or evidence of independently authorized master selection.",
)


@dataclass(frozen=True, slots=True, repr=False)
class RetainedRoleList:
    role_list_bytes: bytes
    count: int
    sha256: str


@dataclass(frozen=True, slots=True, repr=False)
class Stage2AAllocation:
    """Immutable snapshots; mapping order follows DOMAINS, KINDS, then ASCII worlds.

    namespaces[domain][kind] is the unmodified v3 OpaqueNamespace result.
    role_lists[domain] retains every kind and ALL, including empty lists.
    bindings concatenates the primitive's binding order in namespace order.
    All role maps use complete seven-component keys, never shortened aliases.
    """

    namespaces: Mapping
    role_lists: Mapping
    bindings: tuple
    role_tokens_by_domain: Mapping
    _worlds: Mapping
    custody_bytes: bytes
    custody_sha256: str

    status = STATUS
    schema_version = SCHEMA_VERSION
    limitations = LIMITATIONS

    def role_tokens_by_world(self, domain):
        """Return immutable world -> complete role-key -> token mappings."""
        if type(domain) is not str or domain not in DOMAINS:
            raise ValueError("unbound_allocation_domain")
        return self._worlds[domain]


def _retained(raw, expected_count, expected_hash):
    count = 0 if not raw else raw.count(b"\n") + 1
    digest = sha256(raw).hexdigest()
    if count != expected_count or digest != expected_hash:
        raise ValueError("role_commitment_mismatch")
    return RetainedRoleList(raw, count, digest)


def _role_document(retained):
    return {"role_list_ascii": retained.role_list_bytes.decode("ascii"),
            "count": retained.count, "sha256": retained.sha256}


def allocate_stage2a(*, master: bytes) -> Stage2AAllocation:
    """Allocate all existing finite roles, once, with complete collision context.

    Empty/binary bytes are valid explicit source inputs; no scientific master
    is silently selected. Each call re-enumerates and revalidates every role.
    The existing allocator alone generates, orders, and binds opaque tokens.
    """
    if type(master) is not bytes:
        raise ValueError("allocation_master_requires_bytes")
    namespaces = {}
    role_lists = {}
    domain_tokens = {}
    world_tokens = {}
    occupied = []
    bindings = []
    domain_documents = []
    for domain in DOMAINS:
        inventory = wire.enumerate_symbolic_role_inventory(domain)
        wire.validate_symbolic_role_inventory(domain, inventory.roles_by_kind)
        namespace_map = {}
        retained_map = {}
        namespace_documents = []
        role_tokens = {}
        for kind in KINDS:
            count, digest = wire.SYMBOLIC_COMMITMENTS[domain][kind]
            namespace = wire.allocate_opaque_namespace(
                master=master, domain=domain, kind=kind,
                role_keys=inventory.roles_by_kind[kind], expected_count=count,
                expected_role_list_sha256=digest, occupied_tokens=tuple(occupied),
            )
            retained = _retained(namespace.role_list_bytes, count, digest)
            namespace_map[kind] = namespace
            retained_map[kind] = retained
            occupied.extend(namespace.serial_tokens)
            bindings.extend(namespace.bindings)
            role_tokens.update(namespace.bindings)
            encoded_bindings = [list(binding) for binding in namespace.bindings]
            namespace_documents.append({
                "kind": kind, "roles": _role_document(retained),
                "serial_tokens": list(namespace.serial_tokens),
                "serial_tokens_sha256": sha256(
                    "\n".join(namespace.serial_tokens).encode("ascii")).hexdigest(),
                "bindings": encoded_bindings,
                "bindings_sha256": sha256(canonical_json(encoded_bindings)).hexdigest(),
            })
        combined = "\n".join(sorted(role_tokens)).encode("ascii")
        retained_map["ALL"] = _retained(combined, *wire.SYMBOLIC_COMMITMENTS[domain]["ALL"])
        worlds = {}
        for role, token in sorted(role_tokens.items()):
            world = role.split("/")[1]
            worlds.setdefault(world, {})[role] = token
        namespaces[domain] = MappingProxyType(namespace_map)
        role_lists[domain] = MappingProxyType(retained_map)
        domain_tokens[domain] = MappingProxyType(role_tokens)
        world_tokens[domain] = MappingProxyType({
            world: MappingProxyType(tokens) for world, tokens in worlds.items()
        })
        domain_documents.append({
            "domain": domain, "all_roles": _role_document(retained_map["ALL"]),
            "namespaces": namespace_documents,
        })
    raw = canonical_json({
        "schema": SCHEMA_VERSION, "status": STATUS,
        "composition_api": COMPOSITION_API, "allocator_api": ALLOCATOR_API,
        "inventory_api": INVENTORY_API, "contract_hashes": dict(CONTRACT_HASHES),
        "source_hashes": dict(SOURCE_HASHES),
        "master": {"bytes_hex": master.hex(), "sha256": sha256(master).hexdigest()},
        "domain_order": list(DOMAINS), "kind_order": list(KINDS),
        "domains": domain_documents, "allocated_count": len(bindings),
        "unallocated_reserved": [
            {"domain": domain, "serials_per_kind": 4096, "kinds": list(KINDS)}
            for domain in UNALLOCATED_RESERVED_DOMAINS
        ],
        "limitations": list(LIMITATIONS),
    })
    return Stage2AAllocation(
        MappingProxyType(namespaces), MappingProxyType(role_lists), tuple(bindings),
        MappingProxyType(domain_tokens), MappingProxyType(world_tokens),
        raw, sha256(raw).hexdigest(),
    )


def _exact(candidate, expected):
    if type(candidate) is not type(expected):
        return False
    if type(expected) in (str, bytes, int):
        return candidate == expected
    if type(expected) is tuple:
        return len(candidate) == len(expected) and all(
            _exact(actual, wanted) for actual, wanted in zip(candidate, expected))
    if type(expected) is MappingProxyType:
        return _exact(tuple(candidate), tuple(expected)) and all(
            _exact(candidate[key], expected[key]) for key in expected)
    if type(expected) in (Stage2AAllocation, RetainedRoleList, wire.OpaqueNamespace):
        return all(_exact(getattr(candidate, field.name), getattr(expected, field.name))
                   for field in fields(expected))
    return False


def verify_stage2a(allocation: Stage2AAllocation, *, master: bytes) -> bool:
    """Fully rederive independently of candidate values, caches, and custody pins.

    Every retained byte, binding, mapping, order and type must match. A caller
    must select master independently: taking it from untrusted custody proves
    only self-consistency, not allocation provenance.
    """
    if type(allocation) is not Stage2AAllocation:
        raise ValueError("stage2a_allocation_required")
    expected = allocate_stage2a(master=master)
    if not _exact(allocation, expected):
        raise ValueError("exact_allocation_mismatch")
    return True


def verify_stage2a_custody(candidate_bytes: bytes, *, master: bytes) -> bool:
    """Compare the complete canonical document with a fresh full rederivation."""
    if type(candidate_bytes) is not bytes:
        raise ValueError("allocation_custody_requires_bytes")
    expected = allocate_stage2a(master=master)
    if candidate_bytes != expected.custody_bytes:
        raise ValueError("exact_allocation_custody_mismatch")
    return True
