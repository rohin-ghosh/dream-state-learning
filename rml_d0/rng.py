"""Injected Stage-A handle tape; no runtime RNG and no metadata derivation."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
import hashlib
from collections.abc import Callable

from .canonical import HANDLE_RE
from .world import TargetHandles


STAGE_A_TARGET_TAPE_VALUES = (
    "MF9A31F407C2D8",
    "CFE7120BA94C63",
    "CF48D19F20A7BE",
    "CFB03576E18D24",
    "CF1C8AE452F093",
    "CI63B20F9D4A71",
    "CIDA57031E8C42",
    "CI28FCB64910E5",
    "CI941AE07D35CB",
    "XF70C429E1AB53",
    "VF2E85A10CD764",
    "LO8BD361F04E2A",
    "VA51E8C297A40D",
    "COA4D7093B61EC",
    "GO3F10C8E52A97",
    "SI0A6D39C1F8B2",
    "SI7E41B0A5D3C9",
    "SIC2F8097A4E16",
)


class HandleTapeError(ValueError):
    pass


class HandleTape:
    """Consume presealed opaque handles in tape order.

    The caller supplies the values.  Draws do not accept item index, slot,
    side, proposal counter, or hidden truth, so none can enter a handle value.
    """

    def __init__(self, handles: Iterable[str]):
        values = tuple(handles)
        if len(set(values)) != len(values):
            raise HandleTapeError("handle tape contains a duplicate")
        if any(HANDLE_RE.fullmatch(value) is None for value in values):
            raise HandleTapeError("handle tape contains an invalid handle")
        self._values: deque[str] = deque(values)

    def draw(self, prefix: str) -> str:
        if not self._values:
            raise HandleTapeError("handle tape exhausted")
        value = self._values.popleft()
        if not value.startswith(prefix):
            raise HandleTapeError(f"expected {prefix} handle, got {value[:2]}")
        return value

    @property
    def remaining(self) -> int:
        return len(self._values)


def draw_target_handles(tape: HandleTape, item_count: int) -> TargetHandles:
    """The normative Stage-A target-handle draw order."""

    return TargetHandles(
        module_family=tape.draw("MF"),
        conditioner_families=tuple(tape.draw("CF") for _ in range(item_count)),
        cartridges=tuple(tape.draw("CI") for _ in range(item_count)),
        exchanger_family=tape.draw("XF"),
        valve_family=tape.draw("VF"),
        loop=tape.draw("LO"),
        valve=tape.draw("VA"),
        coolant=tape.draw("CO"),
        goal=tape.draw("GO"),
        sites=(tape.draw("SI"), tape.draw("SI"), tape.draw("SI")),
    )


def stage_a_target_tape() -> HandleTape:
    """Return the explicit micro-fixture tape used by independent goldens.

    These are fixed test vectors, not a production randomness substitute.
    Recreating this tape for a new independent golden is intentional.
    """

    return HandleTape(STAGE_A_TARGET_TAPE_VALUES)


def sealed_fixture_values(namespace: str, prefixes: Iterable[str]) -> tuple[str, ...]:
    """Build a presealed micro-fixture tape indexed only by tape position.

    This is deterministic test-fixture construction, not the production RNG.
    Neither hidden truth nor row/cut/slot metadata is accepted by this API.
    """

    values: list[str] = []
    for cursor, prefix in enumerate(tuple(prefixes)):
        digest = hashlib.sha256(
            f"RML-D0-FT-B-V1:{namespace}:tape-position:{cursor}".encode("ascii")
        ).hexdigest()[:12].upper()
        values.append(prefix + digest)
    if len(set(values)) != len(values):
        raise AssertionError("sealed fixture tape collision")
    return tuple(values)


BRIDGE_DRAW_PREFIXES = tuple(
    prefix
    for _ in range(16)
    for prefix in ("EP", "GO", "CO", "LO", "VA", "CI")
)
STAGE_A_BRIDGE_TAPE_VALUES = sealed_fixture_values(
    "bridge-independent-source-handle-ledger", BRIDGE_DRAW_PREFIXES
)


def stage_a_bridge_tape() -> HandleTape:
    return HandleTape(STAGE_A_BRIDGE_TAPE_VALUES)


def handle_sequence(handles: TargetHandles) -> tuple[str, ...]:
    return (
        handles.module_family,
        *handles.conditioner_families,
        *handles.cartridges,
        handles.exchanger_family,
        handles.valve_family,
        handles.loop,
        handles.valve,
        handles.coolant,
        handles.goal,
        *handles.sites,
    )


def handle_metamorphic_goldens() -> dict[str, object]:
    metadata_a = ("K1", "N", 0, 0, "H")
    metadata_b = ("K3", "P", 1, 4095, "TWIN")
    # Metadata is intentionally not an argument to draw_target_handles.
    first = draw_target_handles(HandleTape(STAGE_A_TARGET_TAPE_VALUES), 4)
    permuted_metadata = draw_target_handles(HandleTape(STAGE_A_TARGET_TAPE_VALUES), 4)
    if handle_sequence(first) != handle_sequence(permuted_metadata):
        raise AssertionError("metadata permutation changed injected handles")

    substituted_values = list(STAGE_A_TARGET_TAPE_VALUES)
    substituted_values[1] = "CF000000ABCDEF"
    substituted = draw_target_handles(HandleTape(substituted_values), 4)
    before = handle_sequence(first)
    after = handle_sequence(substituted)
    changed = [index for index, (left, right) in enumerate(zip(before, after)) if left != right]
    if changed != [1]:
        raise AssertionError("one tape substitution did not change exactly one handle")
    return {
        "metadata_a": list(metadata_a),
        "metadata_b": list(metadata_b),
        "metadata_permutation_same_sequence": True,
        "substituted_sequence_index": changed[0],
        "tape_substitution_changes_bytes": True,
    }


def validate_handle_allocator(
    allocator: Callable[[tuple[str, ...], tuple[object, ...]], tuple[str, ...]]
) -> bool:
    metadata_a: tuple[object, ...] = ("K1", "N", 0, 0, "H")
    metadata_b: tuple[object, ...] = ("K3", "P", 1, 4095, "TWIN")
    first = allocator(STAGE_A_TARGET_TAPE_VALUES, metadata_a)
    permuted = allocator(STAGE_A_TARGET_TAPE_VALUES, metadata_b)
    substituted_values = list(STAGE_A_TARGET_TAPE_VALUES)
    substituted_values[1] = "CF000000ABCDEF"
    substituted = allocator(tuple(substituted_values), metadata_a)
    changed = [index for index, pair in enumerate(zip(first, substituted)) if pair[0] != pair[1]]
    return first == permuted and changed == [1]


def injected_handle_allocator(
    tape_values: tuple[str, ...], metadata: tuple[object, ...]
) -> tuple[str, ...]:
    del metadata
    return handle_sequence(draw_target_handles(HandleTape(tape_values), 4))
