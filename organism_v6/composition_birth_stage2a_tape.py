"""Symbolic paired target order; no rendered targets, tokenizer, or training."""

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType

from organism_v6.composition_birth_stage2a_primitives import dropout_seed


STATUS = "SYMBOLIC_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType({name: False for name in (
    "GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM",
)})


@dataclass(frozen=True)
class PresentationBatch:
    update_number: int
    presentation_index: int
    unit_ids: tuple[str, ...]
    rng_start_seed: int

    @property
    def stage(self):
        return "D1" if self.update_number <= 256 else "D2"


def unit_identifiers():
    return tuple(f"p{pair:02d}/m{member}/u{slot}" for pair in range(32)
                 for member in range(2) for slot in range(4))


def build_presentation_tape(*, master, unit_ids):
    """Return all 512 reserved paired updates, including conditional D2 slots."""
    if type(master) is not bytes or not master or not master.isascii() or b"\0" in master:
        raise ValueError("explicit_ascii_master_required")
    if type(unit_ids) not in (tuple, list) or any(type(unit) is not str for unit in unit_ids):
        raise ValueError("unit_identifier_sequence_required")
    expected = unit_identifiers()
    if len(unit_ids) != 256 or len(set(unit_ids)) != 256 or set(unit_ids) != set(expected):
        raise ValueError("incomplete_or_invalid_unit_roster")
    ordered = tuple(sorted(unit_ids, key=lambda unit: (
        sha256(master + b"\0target-order\0" + unit.encode("ascii")).digest(), unit.encode("ascii"))))
    batches = []
    for presentation in range(8):
        offset = 73 * presentation % 256
        rotated = ordered[offset:] + ordered[:offset]
        for batch_index in range(64):
            update = 64 * presentation + batch_index + 1
            batches.append(PresentationBatch(update, presentation,
                                             rotated[4 * batch_index:4 * batch_index + 4],
                                             dropout_seed(master, update)))
    return tuple(batches)
