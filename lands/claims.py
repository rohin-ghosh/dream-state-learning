"""Rigid, positive-only surface grammar for dream claim ingestion."""

from __future__ import annotations

import re
from typing import Iterable

from .model import MemoryClaim
from .skins import make_skin


CANONICAL_GRAMMAR = (
    "CELL | animal=<animal> | land=<land> | color=<color>",
    "ANIMAL_EQUIV | left=<animal> | right=<animal>",
    "LAND_RELATION | left=<land> | right=<land> | "
    "left_palette=<PRIMARY|SECONDARY> | right_palette=<PRIMARY|SECONDARY> | "
    "rotation_delta=<0|1|2>",
    "META_RULE | land=<meta-land> | operator=PIGMENT_UNION | parents=<land>,<land>,<land>",
)


class ClaimCodec:
    """Bidirectional claim codec for one world/skin.

    Each accepted line is one complete executable claim.  Free-form scratch
    prose is intentionally outside this parser.  Full-line matching rejects
    unparsed prose, negated variants, and degeneration loops.
    """

    def __init__(self, world, skin: str = "aligned"):
        self.world = world
        self.skin = make_skin(skin, world.animal_ids, world.source_land_ids)
        self._animal_for = {surface: internal for internal, surface in self.skin.animals.items()}
        self._land_for = {surface: internal for internal, surface in self.skin.lands.items()}
        self._land_for[self.skin.meta_land] = world.meta_land_id
        self._color_for = {surface: internal for internal, surface in self.skin.colors.items()}

    def emit(self, claim: MemoryClaim) -> str:
        payload = claim.payload
        if claim.kind == "cell":
            return (
                f"CELL | animal={self.skin.animal(str(payload['animal_id']))} | "
                f"land={self.skin.land(str(payload['land_id']))} | "
                f"color={self.skin.color(str(payload['color_id']))}"
            )
        if claim.kind == "animal_equiv":
            left, right = sorted((str(payload["left"]), str(payload["right"])))
            return (
                f"ANIMAL_EQUIV | left={self.skin.animal(left)} | "
                f"right={self.skin.animal(right)}"
            )
        if claim.kind == "land_relation":
            left, right = str(payload["left"]), str(payload["right"])
            delta = int(payload["rotation_delta"])
            left_palette = str(payload["left_palette"])
            right_palette = str(payload["right_palette"])
            if left > right:
                left, right = right, left
                left_palette, right_palette = right_palette, left_palette
                delta = (-delta) % 3
            return (
                f"LAND_RELATION | left={self.skin.land(left)} | "
                f"right={self.skin.land(right)} | "
                f"left_palette={left_palette.upper()} | "
                f"right_palette={right_palette.upper()} | rotation_delta={delta}"
            )
        if claim.kind == "meta_rule":
            parents = sorted(str(parent) for parent in payload["parents"])
            surfaces = ",".join(self.skin.land(parent) for parent in parents)
            return (
                f"META_RULE | land={self.skin.meta_land} | "
                f"operator=PIGMENT_UNION | parents={surfaces}"
            )
        raise ValueError(f"unsupported claim kind {claim.kind!r}")

    def parse(self, line: str, claim_id: str = "parsed_claim") -> MemoryClaim:
        line = line.strip()
        match = re.fullmatch(
            r"CELL \| animal=([^ |]+) \| land=([^ |]+) \| color=([^ |]+)", line
        )
        if match:
            animal, land, color = match.groups()
            if (
                animal not in self._animal_for
                or land not in self._land_for
                or color not in self._color_for
            ):
                raise ValueError("CELL uses an unknown surface token")
            return MemoryClaim(
                claim_id,
                "cell",
                {
                    "animal_id": self._animal_for[animal],
                    "land_id": self._land_for[land],
                    "color_id": self._color_for[color],
                },
            )
        match = re.fullmatch(
            r"ANIMAL_EQUIV \| left=([^ |]+) \| right=([^ |]+)", line
        )
        if match:
            left, right = match.groups()
            if left not in self._animal_for or right not in self._animal_for:
                raise ValueError("ANIMAL_EQUIV uses an unknown animal")
            left_id, right_id = sorted((self._animal_for[left], self._animal_for[right]))
            return MemoryClaim(
                claim_id, "animal_equiv", {"left": left_id, "right": right_id}
            )
        match = re.fullmatch(
            r"LAND_RELATION \| left=([^ |]+) \| right=([^ |]+) \| "
            r"left_palette=(PRIMARY|SECONDARY) \| "
            r"right_palette=(PRIMARY|SECONDARY) \| rotation_delta=([012])",
            line,
        )
        if match:
            left, right, left_palette, right_palette, delta_text = match.groups()
            if left not in self._land_for or right not in self._land_for:
                raise ValueError("LAND_RELATION uses an unknown land")
            left_id, right_id = self._land_for[left], self._land_for[right]
            delta = int(delta_text)
            if left_id > right_id:
                left_id, right_id = right_id, left_id
                left_palette, right_palette = right_palette, left_palette
                delta = (-delta) % 3
            return MemoryClaim(
                claim_id,
                "land_relation",
                {
                    "left": left_id,
                    "right": right_id,
                    "left_palette": left_palette.lower(),
                    "right_palette": right_palette.lower(),
                    "rotation_delta": delta,
                },
            )
        match = re.fullmatch(
            r"META_RULE \| land=([^ |]+) \| operator=PIGMENT_UNION \| "
            r"parents=([^ |,]+),([^ |,]+),([^ |,]+)",
            line,
        )
        if match:
            land, *parents = match.groups()
            if land != self.skin.meta_land or any(
                parent not in self._land_for for parent in parents
            ):
                raise ValueError("META_RULE uses an unknown land")
            parent_ids = sorted(self._land_for[parent] for parent in parents)
            return MemoryClaim(
                claim_id,
                "meta_rule",
                {"operator": "pigment_union", "parents": parent_ids},
            )
        raise ValueError("line does not match the canonical positive claim grammar")

    def parse_many(
        self,
        lines: Iterable[str] | str,
    ) -> tuple[tuple[MemoryClaim, ...], tuple[str, ...]]:
        if isinstance(lines, str):
            lines = lines.splitlines()
        claims = []
        rejected = []
        seen = set()
        for index, raw in enumerate(lines):
            line = raw.strip()
            if not line or line in seen:
                continue
            seen.add(line)
            try:
                claims.append(self.parse(line, f"parsed_{index:05d}"))
            except ValueError:
                rejected.append(line)
        return tuple(claims), tuple(rejected)
