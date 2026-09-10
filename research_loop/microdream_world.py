"""Public, CPU-only episode export for recurrent microdream experiments.

Only rendered lifetime text is exported.  This module intentionally never
calls ``render_goals`` or reads answers, roles, or parent sets.  The resulting
JSON is suitable as a deterministic public-memory input and as a source of
candidate tokens for a downstream microdream implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from lands.model import WorldConfig
from lands.skins import all_skin_names
from lands.v02 import SemanticWorldV02


EPISODE_PREFIX = re.compile(r"^\[([^|\]]+)\s*\|\s*([^\]]+)\]\s")
VOCABULARY_PATTERNS = (
    re.compile(r"Its coat is ([\w-]+)\.", re.I),
    re.compile(r"state-token ([\w-]+)\.", re.I),
    re.compile(r"is labeled ([\w-]+)\.", re.I),
)
FORBIDDEN_KEYS = {"goals", "answers", "hidden_roles", "parents"}
FORBIDDEN_TEXT = re.compile(
    r"(?:hidden[_ -]?(?:truth|answer|parent|role)\s*:|ground[_ -]?truth\s*:|"
    r"final[_ -]?answer\s*:|answer[_ -]?key\s*:|proof[_ -]?graph\s*:|"
    r"factor[_ -]?solver\s*:|offline[_ -]?truth\s*:)", re.I,
)


class PublicEpisodeError(ValueError):
    """Raised when a rendered lifetime is not provenance-preserving."""


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _row_record(row: str, row_index: int) -> dict[str, Any]:
    if not isinstance(row, str) or not row:
        raise PublicEpisodeError(f"lifetime row {row_index} is empty or not text")
    match = EPISODE_PREFIX.match(row)
    if match is None:
        raise PublicEpisodeError(
            f"lifetime row {row_index} lacks '[row_id | episode_id]' provenance"
        )
    row_id, episode_id = (part.strip() for part in match.groups())
    if not row_id or not episode_id:
        raise PublicEpisodeError(f"lifetime row {row_index} has blank provenance")
    return {
        "row_id": row_id,
        "episode_id": episode_id,
        "row_index": row_index,
        "row": row,
        "row_sha256": _sha(row.encode("utf-8")),
    }


def public_vocabulary(rows: Iterable[str]) -> list[str]:
    """Extract only state-token labels visibly present in public rows."""
    labels: set[str] = set()
    for row in rows:
        for pattern in VOCABULARY_PATTERNS:
            labels.update(value.lower() for value in pattern.findall(row))
    return sorted(labels)


def candidate_distractor_source(rows_or_vocabulary: Iterable[str]) -> dict[str, Any]:
    """Return a deterministic candidate source with no expected-answer input.

    The source is deliberately just the public vocabulary.  A consumer may
    sample distractors from it, but this exporter never designates a correct
    token or consults a scorer.
    """
    values = list(rows_or_vocabulary)
    vocabulary = public_vocabulary(values) if any("[" in x for x in values) else sorted({str(x).lower() for x in values})
    return {
        "kind": "public_lifetime_vocabulary",
        "candidates": vocabulary,
        "distractors": vocabulary,
        "truth_source": "none",
    }


def export_rows(rows: Sequence[str], *, world_seed: int, skin: str,
                world_tag: str = "semantic_world_v0.2",
                life_tag: str | None = None,
                _preserve_noncontiguous: bool = False) -> dict[str, Any]:
    """Group exact public rows by embedded episode ID in first-seen order."""
    if not isinstance(world_tag, str) or not world_tag.strip():
        raise PublicEpisodeError("world_tag must be a non-empty string")
    if not isinstance(skin, str) or not skin.strip():
        raise PublicEpisodeError("skin must be a non-empty string")
    world_id = f"{world_tag}:seed:{world_seed}"
    if life_tag is None:
        life_tag = f"life:{world_id}:{skin}"
    if not isinstance(life_tag, str) or not life_tag.strip():
        raise PublicEpisodeError("life_tag must be a non-empty string")
    records = [_row_record(row, index) for index, row in enumerate(rows)]
    row_ids = [record["row_id"] for record in records]
    if len(row_ids) != len(set(row_ids)):
        raise PublicEpisodeError("lifetime row IDs are not unique")

    # An episode is one contiguous public segment. Reappearance after another
    # episode would make the grouped export silently reorder the lifetime.
    closed_episode_ids: set[str] = set()
    current_episode_id: str | None = None
    segment_counts: dict[str, int] = {}
    segments: list[tuple[str, list[dict[str, Any]]]] = []
    current_segment: list[dict[str, Any]] = []
    current_segment_id: str | None = None
    for record in records:
        episode_id = record["episode_id"]
        if episode_id == current_episode_id:
            current_segment.append(record)
            continue
        if episode_id in closed_episode_ids:
            if not _preserve_noncontiguous:
                raise PublicEpisodeError(
                    f"episode id {episode_id!r} reappears non-contiguously"
                )
        if current_segment:
            assert current_segment_id is not None
            segments.append((current_segment_id, current_segment))
            current_segment = []
        if current_episode_id is not None:
            closed_episode_ids.add(current_episode_id)
        current_episode_id = episode_id
        segment_counts[episode_id] = segment_counts.get(episode_id, 0) + 1
        occurrence = segment_counts[episode_id]
        current_segment_id = episode_id if occurrence == 1 else f"{episode_id}#segment{occurrence}"
        current_segment.append(record)
    if current_segment:
        assert current_segment_id is not None
        segments.append((current_segment_id, current_segment))

    grouped: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for episode_id, segment in segments:
        grouped[episode_id] = segment
    episodes = []
    for episode_index, (episode_id, episode_rows) in enumerate(grouped.items()):
        episodes.append({
            "episode_id": episode_id,
            "first_row_index": episode_rows[0]["row_index"],
            "episode_index": episode_index,
            "rows": episode_rows,
            "episode_sha256": _sha(_canonical(episode_rows)),
        })
    flattened_row_indices = [
        row["row_index"] for episode in episodes for row in episode["rows"]
    ]
    if flattened_row_indices != list(range(len(records))):
        raise PublicEpisodeError("episode export does not preserve input row order")
    vocabulary = public_vocabulary(rows)
    life_payload = [{
        "row_id": record["row_id"],
        "episode_id": record["episode_id"],
        "row": record["row"],
        "row_sha256": record["row_sha256"],
    } for record in records]
    result = {
        "schema_version": 1,
        # Flat scope keys match the recurrent microdream trace contract;
        # nested metadata keeps the export self-describing for standalone use.
        "world_id": world_id,
        "world_family": world_tag,
        "skin_id": skin,
        "life_id": life_tag,
        "world": {"id": world_id, "family": world_tag, "seed": world_seed},
        "skin": {"id": skin, "name": skin},
        "life": {
            "id": life_tag,
            "row_count": len(records),
            "episode_count": len(episodes),
            "row_order": "render_lifetime_first_seen",
            "row_ids": row_ids,
            "row_hashes": [record["row_sha256"] for record in records],
            "life_sha256": _sha(_canonical(life_payload)),
        },
        "episodes": episodes,
        "public_vocabulary": vocabulary,
        "candidate_distractor_source": candidate_distractor_source(vocabulary),
    }
    _assert_public_shape(result)
    return result


def export_semantic_world(seed: int = 0, skin: str = "aligned") -> dict[str, Any]:
    """Render and export one Semantic World v0.2 lifetime on CPU."""
    if skin not in all_skin_names():
        raise PublicEpisodeError(f"unknown skin {skin!r}")
    world = SemanticWorldV02(WorldConfig(seed=seed))
    # This is the sole world data access: rendered public lifetime text.
    rows = tuple(world.render_lifetime(skin))
    # Semantic World emits a few public calibration/target rows in interleaved
    # segments. Preserve those occurrences as distinct contiguous episodes;
    # direct callers of export_rows still reject ambiguous reuse.
    return export_rows(rows, world_seed=seed, skin=skin,
                       _preserve_noncontiguous=True)


def _assert_public_shape(value: Mapping[str, Any]) -> None:
    """Fail closed on shape drift or explicit scorer/latent serialization."""
    top = {
        "schema_version", "world_id", "world_family", "skin_id", "life_id",
        "world", "skin", "life", "episodes", "public_vocabulary",
        "candidate_distractor_source",
    }
    if set(value) != top:
        raise PublicEpisodeError(
            f"public export top-level shape changed: {sorted(set(value) ^ top)}"
        )
    expected_nested = {
        "world": {"id", "family", "seed"},
        "skin": {"id", "name"},
        "life": {
            "id", "row_count", "episode_count", "row_order", "row_ids",
            "row_hashes", "life_sha256",
        },
        "candidate_distractor_source": {
            "kind", "candidates", "distractors", "truth_source",
        },
    }
    for key, allowed in expected_nested.items():
        child = value.get(key)
        if not isinstance(child, Mapping) or set(child) != allowed:
            raise PublicEpisodeError(f"public export {key} shape changed")
    episodes = value.get("episodes")
    if not isinstance(episodes, list):
        raise PublicEpisodeError("public export episodes must be a list")
    episode_keys = {
        "episode_id", "first_row_index", "episode_index", "rows",
        "episode_sha256",
    }
    row_keys = {
        "row_id", "episode_id", "row_index", "row", "row_sha256",
    }
    for episode_index, episode in enumerate(episodes):
        if not isinstance(episode, Mapping) or set(episode) != episode_keys:
            raise PublicEpisodeError(f"episode {episode_index} shape changed")
        rows = episode.get("rows")
        if not isinstance(rows, list) or not rows:
            raise PublicEpisodeError(f"episode {episode_index} rows are missing")
        for row_index, row in enumerate(rows):
            if not isinstance(row, Mapping) or set(row) != row_keys:
                raise PublicEpisodeError(
                    f"episode {episode_index} row {row_index} shape changed"
                )
            if FORBIDDEN_TEXT.search(str(row.get("row", ""))):
                raise PublicEpisodeError(
                    f"forbidden latent text in episode {episode_index} row {row_index}"
                )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--skin", choices=all_skin_names(), default="aligned")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    result = export_semantic_world(args.seed, args.skin)
    _assert_public_shape(result)
    text = json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
