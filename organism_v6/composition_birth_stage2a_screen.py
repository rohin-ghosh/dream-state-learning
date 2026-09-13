"""Reduced upstream screen roster; no dose admission or runtime invocation.

Selects the already bound subset without renumbering global logical calls.
Upstream Stage2A keeps chain-first physical order. TSJ preservation imports
the same slots intervention-first and aliases existing cold-canary calls;
this source does not conflate those two ledgers or launch either one.
"""

from dataclasses import dataclass
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a_primitives as primitives


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(primitives.SCIENCE_GATES, False))
CHAIN_TASKS = tuple(range(0, 32, 4))
INTERVENTION_PAIRS = (0, 2, 4, 6)


@dataclass(frozen=True)
class ScreenEntry:
    kind: str
    index: int
    member: int | None
    transition: str | None
    slot: primitives.LogicalSlot


@dataclass(frozen=True)
class PreservationEntry:
    custody_id: str
    upstream: ScreenEntry
    alias_to_cold_canary: int | None


def reduced_screen(stage):
    """Exactly280 reserved slots for one state, no implicit BASE or D2 calls."""
    entries = []
    for task in CHAIN_TASKS:
        world_index, member = divmod(task, 2)
        for call_index in range(29):
            entries.append(ScreenEntry("CHAIN", task, member, None,
                                       primitives.chain_slot(stage, world_index, member, call_index)))
    for transition in primitives.TRANSITIONS:
        for pair in INTERVENTION_PAIRS:
            for member in range(2):
                entries.append(ScreenEntry("INTERVENTION", pair, member, transition,
                                           primitives.intervention_slot(stage, transition, pair, member)))
    for index in range(16):
        entries.append(ScreenEntry("CANARY", index, None, None, primitives.canary_slot(stage, index)))
    return tuple(entries)


def preservation_import(stage):
    """C001..C280 source mapping; canary aliases authorize zero new calls."""
    upstream = reduced_screen(stage)
    reordered = (tuple(entry for entry in upstream if entry.kind == "INTERVENTION")
                 + tuple(entry for entry in upstream if entry.kind == "CHAIN")
                 + tuple(entry for entry in upstream if entry.kind == "CANARY"))
    return tuple(PreservationEntry(f"C{index + 1:03d}", entry,
                                   entry.index if entry.kind == "CANARY" else None)
                 for index, entry in enumerate(reordered))


def reduced_decode_seeds(stage, *, master):
    return tuple(primitives.decode_seed(master, entry.slot.panel_label, entry.slot.global_ordinal)
                 for entry in reduced_screen(stage))
