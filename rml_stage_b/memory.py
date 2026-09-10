"""Pretarget source-derived row stores and target-blind exact-key serving."""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import combinations
from typing import Any, Callable, Iterable, Mapping

from rml_d0.source import _expand_side, expand_logical_schedule, validate_source_records
from rml_d0.world import Conditioner, VALVE_NAMES, apply_conditioner

from .contract import RESOURCE_CEILINGS, canonical_bytes, digest


class MemoryContractError(ValueError):
    pass


TokenCounter = Callable[[bytes], int]


def conservative_cpu_token_count(payload: bytes) -> int:
    """A deterministic CPU bound; GPU lock must replace it with exact IDs."""
    return (len(payload) + 3) // 4


def _coolant_bits(value: Mapping[str, Any]) -> int:
    return (2 if value["viscosity"] == "HIGH" else 0) | (
        1 if value["inhibitor"] == "RICH" else 0
    )


@dataclass(frozen=True)
class SourceModuleFacts:
    module_family: str
    module_descriptor: str
    conditioners_by_code: tuple[str, str, str, str]
    valves_by_mode: tuple[str, str, str, str]
    exchangers_by_coolant: tuple[str, str, str, str]


@dataclass(frozen=True)
class PermittedSourceFacts:
    projection: str
    public_source_sha256: str
    modules: tuple[SourceModuleFacts, ...]
    source_row_count: int


def _infer_conditioner(observations: Iterable[tuple[int, int]]) -> int:
    observations = tuple(observations)
    matches = [
        code
        for code in range(4)
        if all(apply_conditioner(start, code) == finish for start, finish in observations)
    ]
    if len(matches) != 1:
        raise MemoryContractError("public conditioner event is not locally identifying")
    return matches[0]


def extract_permitted_source_facts(*, twin: bool = False) -> PermittedSourceFacts:
    """Infer mappings from sealed public resets/events, never from a TargetSpec."""
    logical, _, _ = expand_logical_schedule()
    expanded = _expand_side(logical, twin)
    if not validate_source_records(expanded):
        raise MemoryContractError("D0 public source records failed validation")
    conditioner_observations: dict[tuple[str, str], list[tuple[int, int]]] = {}
    valves: dict[str, dict[int, str]] = {}
    exchangers: dict[str, dict[int, str]] = {}
    descriptors: dict[str, str] = {}
    public_rows: list[bytes] = []
    for reset, event, _ in expanded:
        public_rows.append(canonical_bytes({"reset": reset, "event": event}))
        initial = reset["initial_public_state"]
        module = initial["loop"]["module_family"]
        descriptors[module] = initial["loop"]["module_descriptor"]
        action_kind = event["action"]["action_kind"]
        if reset["bench_kind"] == "CONDITIONER_BENCH" and action_kind == "APPLY":
            item = initial["inventory"][0]
            family = item["conditioner_family"]
            conditioner_observations.setdefault(
                (item["module_family"], family), []
            ).append(
                (
                    _coolant_bits(initial["coolant"]),
                    _coolant_bits(event["state_delta"]["coolant"]),
                )
            )
        elif reset["bench_kind"] == "VALVE_BENCH" and action_kind == "RUN":
            if event["result_code"] == "RUN_STABLE":
                mode = VALVE_NAMES.index(initial["valve"]["mode"])
                family = initial["valve"]["valve_family"]
                prior = valves.setdefault(module, {}).setdefault(mode, family)
                if prior != family:
                    raise MemoryContractError("valve mapping conflict")
        elif reset["bench_kind"] == "EXCHANGER_BENCH" and action_kind == "RUN":
            if event["result_code"] == "RUN_STABLE":
                coolant = _coolant_bits(initial["coolant"])
                family = initial["loop"]["exchanger_family"]
                prior = exchangers.setdefault(module, {}).setdefault(coolant, family)
                if prior != family:
                    raise MemoryContractError("exchanger mapping conflict")
    conditioners: dict[str, dict[int, str]] = {}
    for (module, family), observations in conditioner_observations.items():
        code = _infer_conditioner(observations)
        prior = conditioners.setdefault(module, {}).setdefault(code, family)
        if prior != family:
            raise MemoryContractError("conditioner mapping conflict")
    modules: list[SourceModuleFacts] = []
    for module in sorted(set(conditioners) & set(valves) & set(exchangers)):
        if all(len(table[module]) == 4 for table in (conditioners, valves, exchangers)):
            modules.append(
                SourceModuleFacts(
                    module,
                    descriptors[module],
                    tuple(conditioners[module][index] for index in range(4)),
                    tuple(valves[module][index] for index in range(4)),
                    tuple(exchangers[module][index] for index in range(4)),
                )
            )
    if not modules:
        raise MemoryContractError("no complete public-source semantic module")
    return PermittedSourceFacts(
        "FULL_TWIN" if twin else "H",
        digest(b"".join(sorted(public_rows))),
        tuple(modules),
        len(expanded),
    )


def valve_twin_projection(
    authentic: PermittedSourceFacts, twin: PermittedSourceFacts
) -> PermittedSourceFacts:
    """Preseal the P valve-completion projection from two public source sides."""
    twin_by_module = {module.module_family: module for module in twin.modules}
    rows = tuple(
        replace(module, valves_by_mode=twin_by_module[module.module_family].valves_by_mode)
        for module in authentic.modules
    )
    return PermittedSourceFacts(
        "VALVE_TWIN",
        digest(
            {
                "authentic_public_source": authentic.public_source_sha256,
                "twin_public_source": twin.public_source_sha256,
                "projection": "VALVE_ONLY",
            }
        ),
        rows,
        authentic.source_row_count + twin.source_row_count,
    )


def conditioner_twin_projection(
    authentic: PermittedSourceFacts, twin: PermittedSourceFacts
) -> PermittedSourceFacts:
    """Preseal the complementary conditioner/exchanger-only twin projection."""
    authentic_by_module = {module.module_family: module for module in authentic.modules}
    rows = tuple(
        replace(
            module,
            valves_by_mode=authentic_by_module[module.module_family].valves_by_mode,
        )
        for module in twin.modules
    )
    return PermittedSourceFacts(
        "CONDITIONER_TWIN",
        digest(
            {
                "authentic_public_source": authentic.public_source_sha256,
                "twin_public_source": twin.public_source_sha256,
                "projection": "CONDITIONER_EXCHANGER_ONLY",
            }
        ),
        rows,
        authentic.source_row_count + twin.source_row_count,
    )


@dataclass(frozen=True)
class MemoryRow:
    key: str
    handle: str
    payload: Mapping[str, Any]
    public_support: tuple[str, ...]
    serialized: bytes
    token_count: int


@dataclass(frozen=True)
class MemorySnapshot:
    projection: str
    kind: str
    transform: str
    parent_sha256: str | None
    masked_handles: tuple[str, ...]
    snapshot_id: str
    rows: tuple[MemoryRow, ...]
    aliases: tuple[tuple[str, str], ...]
    index_entries: tuple[tuple[str, str], ...]
    cache_views: tuple[tuple[str, str], ...]
    derived_views: tuple[tuple[str, str], ...]
    equivalence: tuple[tuple[str, tuple[str, ...]], ...]
    sham_candidate_order: tuple[str, ...]
    query_universe: tuple[str, ...]
    renderer_sha256: str
    tokenizer_rendering_sha256: str
    source_sha256: str
    sealed_sha256: str

    def row_map(self) -> dict[str, MemoryRow]:
        return {row.key: row for row in self.rows}

    def handle_map(self) -> dict[str, MemoryRow]:
        return {row.handle: row for row in self.rows}


def _snapshot_body(snapshot: MemorySnapshot) -> dict[str, Any]:
    return {
        "projection": snapshot.projection,
        "kind": snapshot.kind,
        "transform": snapshot.transform,
        "parent_sha256": snapshot.parent_sha256,
        "masked_handles": snapshot.masked_handles,
        "rows": [
            {
                "key": row.key,
                "handle": row.handle,
                "payload": dict(row.payload),
                "public_support": row.public_support,
                "serialized": row.serialized.decode("utf-8"),
                "token_count": row.token_count,
            }
            for row in snapshot.rows
        ],
        "aliases": snapshot.aliases,
        "index_entries": snapshot.index_entries,
        "cache_views": snapshot.cache_views,
        "derived_views": snapshot.derived_views,
        "equivalence": snapshot.equivalence,
        "sham_candidate_order": snapshot.sham_candidate_order,
        "query_universe": snapshot.query_universe,
        "renderer_sha256": snapshot.renderer_sha256,
        "tokenizer_rendering_sha256": snapshot.tokenizer_rendering_sha256,
        "source_sha256": snapshot.source_sha256,
    }


def validate_snapshot_integrity(snapshot: MemorySnapshot) -> None:
    if not isinstance(snapshot, MemorySnapshot):
        raise MemoryContractError("memory mount is not a snapshot")
    for row in snapshot.rows:
        expected = canonical_bytes(
            {
                "handle": row.handle,
                "payload": dict(row.payload),
                "public_support": list(row.public_support),
                "status": "ROW",
            }
        )
        if row.handle != _handle(row.key) or row.serialized != expected:
            raise MemoryContractError("snapshot row serialization/integrity mismatch")
        if row.token_count != conservative_cpu_token_count(row.serialized):
            raise MemoryContractError("snapshot row token count mismatch")
    if snapshot.query_universe != tuple(row.key for row in snapshot.rows):
        raise MemoryContractError("snapshot query universe disagrees with rows")
    if snapshot.index_entries != tuple((row.key, row.handle) for row in snapshot.rows):
        raise MemoryContractError("snapshot index disagrees with rows")
    row_handles = tuple(row.handle for row in snapshot.rows)
    if set(snapshot.sham_candidate_order) != set(row_handles) or len(
        snapshot.sham_candidate_order
    ) != len(row_handles):
        raise MemoryContractError("snapshot sham order disagrees with rows")
    body = _snapshot_body(snapshot)
    if digest(body) != snapshot.sealed_sha256:
        raise MemoryContractError("snapshot content does not match sealed hash")
    if digest({"mount_sha256": snapshot.sealed_sha256}) != snapshot.snapshot_id:
        raise MemoryContractError("snapshot mount id does not match sealed content")


@dataclass(frozen=True)
class PretargetSnapshotSeal:
    """Capability proving every source-derived store was sealed pre-selection."""

    entries: tuple[tuple[str, MemorySnapshot], ...]
    manifest_sha256: str

    def verify(self) -> None:
        expected = {
            f"{projection}:{kind}"
            for projection in ("H", "FULL_TWIN", "VALVE_TWIN", "CONDITIONER_TWIN")
            for kind in ("GOLD", "ATOMS")
        }
        if {name for name, _ in self.entries} != expected or len(self.entries) != 8:
            raise MemoryContractError("pretarget snapshot seal has roster drift")
        for _, snapshot in self.entries:
            validate_snapshot_integrity(snapshot)
        body = {
            "snapshots": [
                {
                    "name": name,
                    "sealed_sha256": snapshot.sealed_sha256,
                    "query_universe": snapshot.query_universe,
                    "renderer_sha256": snapshot.renderer_sha256,
                    "tokenizer_rendering_sha256": snapshot.tokenizer_rendering_sha256,
                }
                for name, snapshot in self.entries
            ]
        }
        if digest(body) != self.manifest_sha256:
            raise MemoryContractError("pretarget snapshot seal hash mismatch")

    def snapshot_map(self) -> dict[str, MemorySnapshot]:
        self.verify()
        return dict(self.entries)


def _handle(key: str) -> str:
    return "RH" + digest({"key": key})[:30].upper()


def _row(
    key: str,
    payload: Mapping[str, Any],
    support: Iterable[str],
    token_counter: TokenCounter,
) -> MemoryRow:
    visible = {
        "handle": _handle(key),
        "payload": dict(payload),
        "public_support": list(support),
        "status": "ROW",
    }
    serialized = canonical_bytes(visible)
    tokens = token_counter(serialized)
    if len(serialized) > RESOURCE_CEILINGS["row_bytes_per_return"] or tokens > RESOURCE_CEILINGS["row_tokens_per_return"]:
        raise MemoryContractError("row exceeds the ratified return ceiling")
    return MemoryRow(key, visible["handle"], dict(payload), tuple(support), serialized, tokens)


def build_snapshot(
    source: PermittedSourceFacts,
    *,
    kind: str = "GOLD",
    token_counter: TokenCounter = conservative_cpu_token_count,
) -> MemorySnapshot:
    """Build only from sealed source facts; target objects are not accepted."""
    if not isinstance(source, PermittedSourceFacts):
        raise MemoryContractError("source must be sealed PermittedSourceFacts, never a target")
    if kind not in {"GOLD", "ATOMS"}:
        raise MemoryContractError("snapshot kind must be GOLD or ATOMS")
    rows: list[MemoryRow] = []
    # Public provenance is intentionally projection-neutral.  The exact source
    # hash remains host-only on MemorySnapshot for audit/replay.
    support = ("SRC_PUBLIC",)
    for module in source.modules:
        for code, family in enumerate(module.conditioners_by_code):
            rows.append(
                _row(
                    f"conditioner:{family}",
                    {"family": family, "operation": Conditioner(code).name, "relation": "conditioner_effect"},
                    support,
                    token_counter,
                )
            )
        rows.append(
            _row(
                f"schema:{module.module_family}",
                {"domain": [member.name for member in Conditioner], "module_family": module.module_family, "relation": "families_form_bijection"},
                support,
                token_counter,
            )
        )
        if kind == "GOLD":
            for coolant, exchanger in enumerate(module.exchangers_by_coolant):
                rows.append(
                    _row(
                        f"exchanger:{exchanger}",
                        {"coolant_bits": f"{coolant:02b}", "family": exchanger, "relation": "stable_coolant"},
                        support,
                        token_counter,
                    )
                )
                for initial in range(4):
                    candidate_pairs: set[tuple[int, int]] = set()
                    for left, right in combinations(range(4), 2):
                        for order in ((left, right), (right, left)):
                            state = apply_conditioner(apply_conditioner(initial, order[0]), order[1])
                            if state == coolant:
                                candidate_pairs.add(tuple(sorted((left, right))))
                    if len(candidate_pairs) == 1:
                        pair = next(iter(candidate_pairs))
                        rows.append(
                            _row(
                                f"pair:{module.module_family}:{initial:02b}:{exchanger}",
                                {"families": [module.conditioners_by_code[pair[0]], module.conditioners_by_code[pair[1]]], "relation": "joint_conditioner_pair"},
                                support,
                                token_counter,
                            )
                        )
            for mode, valve in enumerate(module.valves_by_mode):
                rows.append(
                    _row(
                        f"valve:{valve}",
                        {"family": valve, "mode": VALVE_NAMES[mode], "relation": "stable_mode"},
                        support,
                        token_counter,
                    )
                )
    rows.sort(key=lambda row: row.key)
    if len({row.key for row in rows}) != len(rows):
        raise MemoryContractError("source store has an ambiguous exact key")
    query_universe = tuple(row.key for row in rows)
    aliases = tuple((f"alias:{row.handle}", row.handle) for row in rows)
    index_entries = tuple((row.key, row.handle) for row in rows)
    cache_views = tuple((f"cache:{row.handle}", row.handle) for row in rows)
    derived_views = tuple((f"reverse:{row.handle}", row.handle) for row in rows)
    equivalence = tuple(
        (row.handle, tuple(sorted({row.handle, f"alias:{row.handle}", f"cache:{row.handle}", f"reverse:{row.handle}", f"index:{row.key}"})))
        for row in rows
    )
    sham_candidate_order = tuple(
        row.handle
        for row in sorted(
            rows,
            key=lambda item: (
                str(item.payload.get("relation")),
                len(item.serialized),
                item.token_count,
                item.key,
            ),
        )
    )
    provisional = MemorySnapshot(
        projection=source.projection,
        kind=kind,
        transform="BASE",
        parent_sha256=None,
        masked_handles=(),
        snapshot_id="",
        rows=tuple(rows),
        aliases=aliases,
        index_entries=index_entries,
        cache_views=cache_views,
        derived_views=derived_views,
        equivalence=equivalence,
        sham_candidate_order=sham_candidate_order,
        query_universe=query_universe,
        renderer_sha256=digest(b"rml-stage-b-row-renderer-v1"),
        tokenizer_rendering_sha256=digest(b"cpu-bound-token-rendering-v1"),
        source_sha256=source.public_source_sha256,
        sealed_sha256="",
    )
    sealed = digest(_snapshot_body(provisional))
    result = replace(
        provisional,
        snapshot_id=digest({"mount_sha256": sealed}),
        sealed_sha256=sealed,
    )
    validate_snapshot_integrity(result)
    return result


def build_pretarget_snapshot_universe() -> dict[str, MemorySnapshot]:
    authentic = extract_permitted_source_facts(twin=False)
    twin = extract_permitted_source_facts(twin=True)
    valve_twin = valve_twin_projection(authentic, twin)
    conditioner_twin = conditioner_twin_projection(authentic, twin)
    sources = {
        source.projection: source
        for source in (authentic, twin, valve_twin, conditioner_twin)
    }
    return {
        f"{projection}:{kind}": build_snapshot(source, kind=kind)
        for projection, source in sources.items()
        for kind in ("GOLD", "ATOMS")
    }


def seal_pretarget_snapshot_universe() -> PretargetSnapshotSeal:
    snapshots = build_pretarget_snapshot_universe()
    entries = tuple(sorted(snapshots.items()))
    body = {
        "snapshots": [
            {
                "name": name,
                "sealed_sha256": snapshot.sealed_sha256,
                "query_universe": snapshot.query_universe,
                "renderer_sha256": snapshot.renderer_sha256,
                "tokenizer_rendering_sha256": snapshot.tokenizer_rendering_sha256,
            }
            for name, snapshot in entries
        ]
    }
    seal = PretargetSnapshotSeal(entries, digest(body))
    seal.verify()
    return seal


def equivalence_closure(snapshot: MemorySnapshot, handles: Iterable[str]) -> frozenset[str]:
    table = dict(snapshot.equivalence)
    closure: set[str] = set()
    for handle in handles:
        if handle not in table:
            raise MemoryContractError("mask handle is not in the sealed snapshot")
        closure.update(table[handle])
    return frozenset(closure)


def masked_snapshot(
    snapshot: MemorySnapshot, handles: Iterable[str], *, transform: str = "MASKED"
) -> MemorySnapshot:
    validate_snapshot_integrity(snapshot)
    handle_set = frozenset(handles)
    closure = equivalence_closure(snapshot, handle_set)
    rows = tuple(row for row in snapshot.rows if row.handle not in handle_set)
    aliases = tuple(row for row in snapshot.aliases if row[0] not in closure and row[1] not in handle_set)
    index_entries = tuple(row for row in snapshot.index_entries if f"index:{row[0]}" not in closure and row[1] not in handle_set)
    cache_views = tuple(row for row in snapshot.cache_views if row[0] not in closure and row[1] not in handle_set)
    derived_views = tuple(row for row in snapshot.derived_views if row[0] not in closure and row[1] not in handle_set)
    equivalence = tuple(row for row in snapshot.equivalence if row[0] not in handle_set)
    sham_candidate_order = tuple(
        handle for handle in snapshot.sham_candidate_order if handle not in handle_set
    )
    result = replace(
        snapshot,
        transform=transform,
        parent_sha256=snapshot.sealed_sha256,
        masked_handles=tuple(sorted(handle_set)),
        snapshot_id="",
        sealed_sha256="",
        rows=rows,
        aliases=aliases, index_entries=index_entries, cache_views=cache_views,
        derived_views=derived_views, equivalence=equivalence,
        sham_candidate_order=sham_candidate_order,
        query_universe=tuple(row.key for row in rows),
    )
    sealed = digest(_snapshot_body(result))
    result = replace(
        result,
        snapshot_id=digest({"mount_sha256": sealed}),
        sealed_sha256=sealed,
    )
    validate_snapshot_integrity(result)
    return result


def assert_no_closure_residue(snapshot: MemorySnapshot, closure: Iterable[str]) -> None:
    encoded = canonical_bytes(
        {"rows": [row.serialized.decode("utf-8") for row in snapshot.rows], "aliases": snapshot.aliases,
         "index": snapshot.index_entries, "cache": snapshot.cache_views, "derived": snapshot.derived_views}
    ).decode("utf-8")
    for value in closure:
        if value in encoded:
            raise MemoryContractError("masked semantic equivalence residue remains")


class ExactMemoryService:
    """Online serving boundary: constructor accepts no target, state, proof, or score."""
    __slots__ = ("_snapshot", "_rows", "_authorized_trajectory_id", "_parent_artifact_sha256")

    def __init__(
        self,
        snapshot: MemorySnapshot,
        *,
        authorized_trajectory_id: str | None = None,
        parent_artifact_sha256: str | None = None,
    ) -> None:
        validate_snapshot_integrity(snapshot)
        self._snapshot = snapshot
        self._rows = snapshot.row_map()
        self._authorized_trajectory_id = authorized_trajectory_id
        self._parent_artifact_sha256 = parent_artifact_sha256

    @property
    def projection_id(self) -> str:
        return self._snapshot.snapshot_id

    @property
    def query_universe(self) -> frozenset[str]:
        return frozenset(self._snapshot.query_universe)

    @property
    def snapshot(self) -> MemorySnapshot:
        return self._snapshot

    @property
    def authorized_trajectory_id(self) -> str | None:
        return self._authorized_trajectory_id

    @property
    def parent_artifact_sha256(self) -> str | None:
        return self._parent_artifact_sha256

    def read(self, key: str) -> bytes:
        if not isinstance(key, str) or not key or len(key.encode("utf-8")) > 256:
            raise MemoryContractError("query key is malformed or oversized")
        row = self._rows.get(key)
        if row is None:
            return canonical_bytes({"handle": _handle(key), "payload": {}, "public_support": [], "status": "NOT_FOUND"})
        return row.serialized
