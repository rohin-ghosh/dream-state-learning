"""Partial Stage2A byte/seed source with explicit inputs and no runtime opening."""

from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType({name: False for name in (
    "GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM",
)})
MEMO_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"
TRANSITIONS = ("SEEK", "PROSPECT", "CHECK", "CONTINUE")


def _ascii_text(value):
    if type(value) is not str or not value.isascii() or "\r" in value or "\0" in value:
        raise ValueError("invalid_json_string")


def _validate_json(value, ancestors):
    if value is None or type(value) in (bool, int):
        return
    if type(value) is str:
        _ascii_text(value)
        return
    if type(value) not in (dict, list):
        raise ValueError("unsupported_json_type")
    identity = id(value)
    if identity in ancestors:
        raise ValueError("cyclic_json")
    ancestors.add(identity)
    try:
        if type(value) is dict:
            for key, item in value.items():
                _ascii_text(key)
                _validate_json(item, ancestors)
        else:
            for item in value:
                _validate_json(item, ancestors)
    finally:
        ancestors.remove(identity)


def canonical_json(value):
    """Encode the contract's restricted CJSON value without a terminal LF."""
    try:
        _validate_json(value, set())
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("ascii")
    except (RecursionError, UnicodeError) as error:
        raise ValueError("invalid_json_depth_or_encoding") from error


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _json_integer(text):
    if text == "-0":
        raise ValueError("negative_zero")
    return int(text)


def _invalid_number(text):
    raise ValueError("non_integer_json_number")


def parse_canonical_json(raw):
    """Parse only exact canonical bytes; reject duplicates before collapsing keys."""
    if type(raw) not in (str, bytes):
        raise ValueError("json_bytes_or_text_required")
    try:
        text = raw.decode("utf-8") if type(raw) is bytes else raw
        _ascii_text(text)
        value = json.loads(text, object_pairs_hook=_unique_object,
                           parse_int=_json_integer, parse_float=_invalid_number,
                           parse_constant=_invalid_number)
        if canonical_json(value) != text.encode("ascii"):
            raise ValueError("noncanonical_json_bytes")
        return value
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid_json_depth_or_encoding") from error


def _integer(value, minimum, maximum):
    if type(value) is not int or not minimum <= value < maximum:
        raise ValueError("integer_out_of_range")
    return value


def u32(value):
    return _integer(value, 0, 2 ** 32).to_bytes(4, "big")


def low64(value):
    if type(value) is not bytes:
        raise ValueError("hash_bytes_required")
    return int.from_bytes(sha256(value).digest()[24:32], "big")


def _master(value):
    if type(value) is not bytes or not value or not value.isascii() or b"\0" in value:
        raise ValueError("explicit_ascii_master_required")
    return value


def _stage(stage):
    if type(stage) is not str or stage not in ("D1", "D2"):
        raise ValueError("invalid_stage")
    return 0 if stage == "D1" else 1008


@dataclass(frozen=True)
class LogicalSlot:
    panel_label: str
    global_ordinal: int


def chain_slot(stage, world_index, member, call_index):
    offset = _stage(stage)
    world_index = _integer(world_index, 0, 16)
    member = _integer(member, 0, 2)
    call_index = _integer(call_index, 0, 29)
    return LogicalSlot(stage + "_CHAIN", offset + 29 * (2 * world_index + member) + call_index)


def intervention_slot(stage, transition, pair_index, member):
    offset = _stage(stage)
    if type(transition) is not str or transition not in TRANSITIONS:
        raise ValueError("invalid_transition")
    pair_index = _integer(pair_index, 0, 8)
    member = _integer(member, 0, 2)
    ordinal = offset + 928 + 16 * TRANSITIONS.index(transition) + 2 * pair_index + member
    return LogicalSlot(stage + "_INTERVENTION_" + transition, ordinal)


def canary_slot(stage, index):
    offset = _stage(stage)
    return LogicalSlot(stage + "_CANARY", offset + 992 + _integer(index, 0, 16))


def decode_seed(master, panel_label, global_ordinal):
    master = _master(master)
    global_ordinal = _integer(global_ordinal, 0, 2016)
    stage = "D1" if global_ordinal < 1008 else "D2"
    ordinal = global_ordinal % 1008
    if ordinal < 928:
        expected_label = stage + "_CHAIN"
    elif ordinal < 992:
        expected_label = stage + "_INTERVENTION_" + TRANSITIONS[(ordinal - 928) // 16]
    else:
        expected_label = stage + "_CANARY"
    if type(panel_label) is not str or panel_label != expected_label:
        raise ValueError("panel_ordinal_mismatch")
    return low64(master + b"\0decode\0" + panel_label.encode("ascii") + b"\0" + u32(global_ordinal))


def adapter_seed(master):
    return low64(_master(master) + b"\0adapter-init")


def dropout_seed(master, update_number):
    update_number = _integer(update_number, 1, 513)
    return low64(_master(master) + b"\0dropout\0" + u32(update_number))
