"""Conditional CPU-only relay preparation; never a fit or launch authorization."""

from dataclasses import asdict, dataclass, is_dataclass, replace
from hashlib import sha256
import json
import re
from typing import Callable


ACTIONS = (b"-mem2reg", b"-gvn")
SHORTAGE = "ENDOGENOUS_FORMATION_SHORTAGE"
PREPARED = "CONDITIONAL_REPLAY_PREPARED"
_ATOM = rb"[A-Za-z0-9_][A-Za-z0-9_.-]*"
_DREAM = re.compile(
    rb"DREAM: STORE\nKEY: (" + _ATOM + rb")\n"
    rb"WHEN: (" + _ATOM + rb")  ACT: (-mem2reg|-gvn)  EVIDENCE: (" + _ATOM + rb")\n"
    rb"WHEN: (" + _ATOM + rb")  ACT: (-mem2reg|-gvn)  EVIDENCE: (" + _ATOM + rb")"
)


def digest(value: object) -> str:
    """Canonical binding for externally sealed material and source metadata."""
    def encode(item: object) -> object:
        if isinstance(item, bytes):
            return {"bytes_hex": item.hex()}
        if is_dataclass(item):
            return asdict(item)
        raise TypeError("unsupported seal value")

    return sha256(json.dumps(value, default=encode, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Receipt:
    receipt_id: bytes
    sequence: int
    raw: bytes
    raw_sha256: str


@dataclass(frozen=True)
class Execution:
    key: bytes
    mode: bytes
    object_id: bytes
    EXECUTED_ACT: bytes
    commit: Receipt
    outcome: Receipt


@dataclass(frozen=True)
class Block:
    key: bytes
    executions: tuple[Execution, ...]
    dream: Receipt


@dataclass(frozen=True)
class Surface:
    key: bytes
    mode: bytes
    view: bytes
    object_id: bytes
    prefix: bytes
    key_span: tuple[int, int]
    mode_span: tuple[int, int]


@dataclass(frozen=True)
class Material:
    """Presealed public world projection only; hidden truth is not accepted."""
    root_id: bytes
    generation_seed: int
    sealed_sequence: int
    keys: tuple[bytes, ...]
    modes: tuple[bytes, ...]
    pairs: tuple[tuple[bytes, bytes], ...]
    views: tuple[bytes, ...]
    source_objects: tuple[bytes, ...]
    surfaces: tuple[Surface, ...]


@dataclass(frozen=True)
class Conditional:
    mode: bytes
    SUPPORTED_FUTURE_ACT: bytes
    action_span: tuple[int, int]
    execution: Execution


@dataclass(frozen=True)
class AdmittedRecord:
    key: bytes
    record: Receipt
    conditionals: tuple[Conditional, ...]


@dataclass(frozen=True)
class Formation:
    status: str
    admitted: tuple[AdmittedRecord, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class TrainingRow:
    key: bytes
    authored_mode: bytes
    input_mode: bytes
    view: bytes
    prefix: bytes
    SUPPORTED_FUTURE_ACT: bytes
    target: bytes
    target_span: tuple[int, int]
    record: Receipt
    execution: Execution


@dataclass(frozen=True)
class Control:
    arm: str
    candidate: str | None
    produces_candidate: bool
    mounts_candidate: bool


CONTROLS = (
    Control("E_AUTH", "E_AUTH", True, True),
    Control("E_SWAP", "E_SWAP", True, True),
    Control("E_OFF", None, False, False),
    Control("E_SHADOW", "E_AUTH", False, False),
)


@dataclass(frozen=True)
class Replay:
    status: str
    formation: Formation
    material_sha256: str
    source_sha256: str
    auth_quartets: tuple[tuple[TrainingRow, ...], ...]
    swap_quartets: tuple[tuple[TrainingRow, ...], ...]
    schedule: tuple[int, ...]
    controls: tuple[Control, ...]
    fits_performed: int = 0


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _atom(value: bytes) -> bool:
    return isinstance(value, bytes) and re.fullmatch(_ATOM, value) is not None


def _receipt(receipt: Receipt) -> None:
    _require(_atom(receipt.receipt_id), "invalid receipt id")
    _require(type(receipt.sequence) is int and receipt.sequence >= 0, "invalid receipt sequence")
    _require(isinstance(receipt.raw, bytes), "receipt must contain raw bytes")
    _require(sha256(receipt.raw).hexdigest() == receipt.raw_sha256, "tampered raw receipt bytes")


def parse_action(raw: bytes) -> bytes:
    _require(raw in (b"ACT: -mem2reg", b"ACT: -gvn"), "invalid ACT grammar")
    return raw[5:]


def admit_block(block: Block, *, key: bytes, modes: tuple[bytes, ...],
                source_objects: tuple[bytes, ...], after: int) -> AdmittedRecord:
    """Copy or reject one record using only earlier public receipts, never truth."""
    _require(len(modes) == 2 and len(set(modes)) == 2, "invalid modes")
    _require(block.key == key and len(block.executions) == 2, "key/block mismatch")
    _require(len(source_objects) == 2, "source object count")
    seen = set()
    previous = after
    for mode, object_id, execution in zip(modes, source_objects, block.executions):
        _require((execution.key, execution.mode, execution.object_id) ==
                 (key, mode, object_id), "execution key/mode/object mismatch")
        for receipt in (execution.commit, execution.outcome):
            _receipt(receipt)
            _require(receipt.receipt_id not in seen, "duplicate receipt id")
            _require(previous < receipt.sequence, "nonchronological source receipt")
            seen.add(receipt.receipt_id)
            previous = receipt.sequence
        _require(parse_action(execution.commit.raw) == execution.EXECUTED_ACT,
                 "EXECUTED_ACT differs from committed bytes")
        _require(execution.outcome.raw in (b"SUCCESS", b"FAILURE"), "invalid public outcome")
    _receipt(block.dream)
    _require(block.dream.receipt_id not in seen, "duplicate receipt id")
    _require(previous < block.dream.sequence, "record precedes outcome")
    _require(block.dream.raw != b"DREAM: NULL", "NO_ADMISSION: DREAM: NULL")
    match = _DREAM.fullmatch(block.dream.raw)
    _require(match is not None, "NO_ADMISSION: invalid DREAM grammar")
    _require(match[1] == key, "record key mismatch")
    conditionals = []
    for mode, execution, group in zip(modes, block.executions, (2, 5)):
        _require(match[group] == mode, "record mode/order mismatch")
        _require(match[group + 2] == execution.commit.receipt_id, "invalid or cross-block citation")
        supported = match[group + 1]
        _require((supported == execution.EXECUTED_ACT) == (execution.outcome.raw == b"SUCCESS"),
                 "unsupported authored future action")
        span = match.span(group + 1)
        _require(block.dream.raw[slice(*span)] == supported, "non-authored target bytes")
        conditionals.append(Conditional(mode, supported, span, execution))
    return AdmittedRecord(key, block.dream, tuple(conditionals))


def _swap(prefix: bytes, span: tuple[int, int], mode: bytes) -> bytes:
    return prefix[:span[0]] + mode + prefix[span[1]:]


def _material(material: Material, expected_sha256: str) -> dict:
    _require(digest(material) == expected_sha256, "material seal mismatch")
    _require(_atom(material.root_id), "invalid root id")
    _require(type(material.generation_seed) is int and material.generation_seed >= 0, "missing fixed seed")
    _require(type(material.sealed_sequence) is int and material.sealed_sequence >= 0, "invalid seal sequence")
    for roster, count in ((material.keys, 8), (material.modes, 2),
                          (material.views, 8), (material.source_objects, 16)):
        _require(len(roster) == count and len(set(roster)) == count and
                 all(_atom(value) for value in roster), "invalid material roster")
    _require(not set(material.keys) & set(material.modes), "overlapping key/mode aliases")
    _require(len(material.pairs) == 4 and all(len(pair) == 2 for pair in material.pairs), "invalid pairs")
    _require(sorted(key for pair in material.pairs for key in pair) == sorted(material.keys), "pair coverage")
    _require(len(material.surfaces) == 128, "training surface count")
    surfaces = {}
    for surface in material.surfaces:
        cell = (surface.key, surface.mode, surface.view)
        _require(cell not in surfaces and surface.key in material.keys and
                 surface.mode in material.modes and surface.view in material.views, "invalid surface cell")
        _require(_atom(surface.object_id) and surface.object_id not in material.source_objects,
                 "source/training object overlap")
        _require(isinstance(surface.prefix, bytes) and surface.prefix.endswith(b"ACT: -"),
                 "prefix must end at natural ACT: - boundary")
        _require(not any(word in surface.prefix for word in
                         (b"mem2reg", b"gvn", b"DREAM:", b"EVIDENCE:", b"SUCCESS", b"FAILURE",
                          b"SUPPORTED_FUTURE_ACT", b"EXECUTED_ACT")), "target-bearing training input")
        for span, value in ((surface.key_span, surface.key), (surface.mode_span, surface.mode)):
            _require(len(span) == 2 and all(type(index) is int for index in span) and
                     0 <= span[0] < span[1] <= len(surface.prefix) - len(b"ACT: -") and
                     surface.prefix[slice(*span)] == value, "invalid key/mode span")
        _require(surface.key_span[1] <= surface.mode_span[0] or
                 surface.mode_span[1] <= surface.key_span[0], "overlapping key/mode spans")
        surfaces[cell] = surface
    for key in material.keys:
        for view in material.views:
            first, second = (surfaces[key, mode, view] for mode in material.modes)
            _require(first.object_id == second.object_id and
                     _swap(first.prefix, first.mode_span, second.mode) == second.prefix,
                     "surface pair differs beyond mode input")
    return surfaces


def check_formation(material: Material, blocks: tuple[Block, ...], *,
                    expected_source_sha256: str) -> Formation:
    """ALL8/16 or terminal shortage; expected source seal must come from capture."""
    admitted = []
    reasons = []
    try:
        _require(digest(blocks) == expected_source_sha256, "source seal mismatch")
        _require(len(blocks) == 8, "requires exactly eight source blocks")
        previous = material.sealed_sequence
        seen = set()
        for index, block in enumerate(blocks):
            receipts = tuple(receipt for execution in block.executions
                             for receipt in (execution.commit, execution.outcome)) + (block.dream,)
            for receipt in receipts:
                _require(receipt.receipt_id not in seen, "duplicate global receipt id")
                seen.add(receipt.receipt_id)
            try:
                admitted.append(admit_block(
                    block, key=material.keys[index], modes=material.modes,
                    source_objects=material.source_objects[index * 2:index * 2 + 2], after=previous))
            except ValueError as error:
                reasons.append(f"block {index}: NO_ADMISSION: {error}")
            previous = block.dream.sequence
        if len(admitted) == 8:
            by_key = {record.key: record for record in admitted}
            for mode_index in (0, 1):
                actions = [record.conditionals[mode_index].SUPPORTED_FUTURE_ACT for record in admitted]
                _require(all(actions.count(action) == 4 for action in ACTIONS), "unbalanced authored bindings")
            for record in admitted:
                _require(len({line.SUPPORTED_FUTURE_ACT for line in record.conditionals}) == 2,
                         "noncomplementary authored modes")
            for first, second in material.pairs:
                _require(by_key[first].conditionals[0].SUPPORTED_FUTURE_ACT !=
                         by_key[second].conditionals[0].SUPPORTED_FUTURE_ACT, "unbalanced sealed key pair")
    except ValueError as error:
        reasons.append(str(error))
    return Formation(SHORTAGE if reasons else "ALL8_16_ADMITTED", tuple(admitted), tuple(reasons))


def build_replay(material: Material, blocks: tuple[Block, ...], *,
                 expected_material_sha256: str, expected_source_sha256: str) -> Replay:
    """No I/O, truth access, fitting, regeneration, or native-proof defaults."""
    surfaces = _material(material, expected_material_sha256)
    formation = check_formation(material, blocks, expected_source_sha256=expected_source_sha256)
    if formation.status == SHORTAGE:
        return Replay(SHORTAGE, formation, expected_material_sha256, expected_source_sha256,
                      (), (), (), ())
    by_key = {record.key: record for record in formation.admitted}
    auth_quartets, swap_quartets = [], []
    for view in material.views:
        for pair in material.pairs:
            auth, swap = [], []
            for mode_index, mode in enumerate(material.modes):
                for key in pair:
                    record = by_key[key]
                    line = record.conditionals[mode_index]
                    span = (line.action_span[0] + 1, line.action_span[1])
                    target = record.record.raw[slice(*span)]
                    for rows, input_mode in ((auth, mode), (swap, material.modes[1 - mode_index])):
                        surface = surfaces[key, input_mode, view]
                        rows.append(TrainingRow(key, mode, input_mode, view, surface.prefix,
                                                line.SUPPORTED_FUTURE_ACT, target, span,
                                                record.record, line.execution))
            auth_quartets.append(tuple(auth))
            swap_quartets.append(tuple(swap))
    return Replay(PREPARED, formation, expected_material_sha256, expected_source_sha256,
                  tuple(auth_quartets), tuple(swap_quartets), tuple(range(32)) * 4, CONTROLS)


@dataclass(frozen=True)
class NativeRow:
    prefix_ids: tuple[int, ...]
    target_ids: tuple[int, ...]


@dataclass(frozen=True)
class BatchShape:
    """Caller supplies actual collator attention, positions, and target positions."""
    attention_mask: tuple[tuple[int, ...], ...]
    position_ids: tuple[tuple[int, ...], ...]
    target_positions: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class NativeCheck:
    status: str
    replay_sha256: str
    tokenizer_sha256: str
    collation_sha256: str
    token_evidence_sha256: str
    quartet_shapes_sha256: str


def check_native_shapes(replay: Replay, *, expected_replay_sha256: str, modes: tuple[bytes, bytes],
                        tokenizer_sha256: str, collation_sha256: str,
                        encode: Callable[[bytes], tuple[int, ...]],
                        collate: Callable[[tuple[NativeRow, ...]], BatchShape]) -> NativeCheck:
    """Require the retained trusted-builder replay seal before checking supplied shapes."""
    _require(isinstance(expected_replay_sha256, str) and
             re.fullmatch(r"[0-9a-f]{64}", expected_replay_sha256) is not None,
             "invalid expected replay SHA-256")
    replay_sha256 = digest(replay)
    _require(replay_sha256 == expected_replay_sha256, "replay seal mismatch")
    _require(replay.status == PREPARED, "no native check on formation shortage")
    _require(len(replay.auth_quartets) == len(replay.swap_quartets) == 32 and
             replay.schedule == tuple(range(32)) * 4 and replay.controls == CONTROLS and
             replay.fits_performed == 0, "incomplete or altered native replay")
    for identity in (tokenizer_sha256, collation_sha256):
        _require(re.fullmatch(r"[0-9a-f]{64}", identity) is not None, "missing native implementation hash")

    def tokens(raw: bytes) -> tuple[int, ...]:
        result = encode(raw)
        _require(isinstance(result, tuple) and bool(result) and
                 all(type(token) is int and token >= 0 for token in result), "invalid native token ids")
        return result

    _require(len(modes) == 2 and len(set(modes)) == 2, "invalid native modes")
    mode_ids = {mode: tokens(mode) for mode in modes}
    _require(all(len(ids) == 1 for ids in mode_ids.values()) and
             len(set(mode_ids.values())) == 2, "modes must have distinct one-token native shape")
    evidence, shapes = [], []
    for auth, swap in zip(replay.auth_quartets, replay.swap_quartets):
        _require(len(auth) == len(swap) == 4, "incomplete native quartet")
        auth_native, swap_native = [], []
        for original, control in zip(auth, swap):
            _receipt(original.record)
            _require(original.target == original.record.raw[slice(*original.target_span)] and
                     b"-" + original.target == original.SUPPORTED_FUTURE_ACT,
                     "non-authored native target bytes")
            _require(control == replace(original, prefix=control.prefix, input_mode=control.input_mode),
                     "control changed child target bytes or provenance")
            _require(original.authored_mode == original.input_mode and
                     {original.input_mode, control.input_mode} == set(modes), "incorrect control modes")
            first, second = tokens(original.prefix), tokens(control.prefix)
            _require(len(first) == len(second), "unequal native prefix lengths")
            differences = [index for index, values in enumerate(zip(first, second)) if values[0] != values[1]]
            _require(len(differences) == 1 and original.input_mode in mode_ids and control.input_mode in mode_ids,
                     "native input differs beyond one mode token")
            position = differences[0]
            _require(first[position] == mode_ids[original.input_mode][0] and
                     second[position] == mode_ids[control.input_mode][0], "native mode-token mismatch")
            for row, prefix_ids, destination in ((original, first, auth_native), (control, second, swap_native)):
                joint = tokens(row.prefix + row.target)
                _require(joint[:len(prefix_ids)] == prefix_ids and len(joint) > len(prefix_ids),
                         "native target crosses common-prefix boundary")
                destination.append(NativeRow(prefix_ids, joint[len(prefix_ids):]))
            _require(auth_native[-1].target_ids == swap_native[-1].target_ids, "unequal native target tokens")
        auth_shape, swap_shape = collate(tuple(auth_native)), collate(tuple(swap_native))
        _require(isinstance(auth_shape, BatchShape) and auth_shape == swap_shape, "unequal native quartet collation")
        for field in (auth_shape.attention_mask, auth_shape.position_ids, auth_shape.target_positions):
            _require(isinstance(field, tuple) and len(field) == 4 and
                     all(isinstance(row, tuple) and bool(row) and
                         all(type(value) is int and value >= 0 for value in row) for row in field),
                     "missing native quartet shape")
        evidence.append((tuple(auth_native), tuple(swap_native)))
        shapes.append(auth_shape)
    _require(len(evidence) == 32 and len(replay.schedule) == 128, "incomplete native replay")
    return NativeCheck("SUPPLIED_NATIVE_SHAPES_CHECKED_NOT_LAUNCH_AUTHORIZATION", replay_sha256,
                       tokenizer_sha256, collation_sha256, digest(evidence), digest(shapes))
