from __future__ import annotations

import hashlib
import json

from research_loop.microdream_world import (
    PublicEpisodeError,
    export_rows,
    export_semantic_world,
)


def test_noncontiguous_episode_reuse_is_rejected():
    try:
        export_rows((
            "[row_a | episode_b] first",
            "[row_b | episode_a] second",
            "[row_c | episode_b] third",
        ), world_seed=7, skin="aligned")
    except PublicEpisodeError as error:
        assert "non-contiguously" in str(error)
    else:
        raise AssertionError("interleaved episode was accepted")


def test_temporal_grouping_preserves_contiguous_input_order():
    result = export_rows((
        "[row_a | episode_b] first",
        "[row_c | episode_b] third",
        "[row_b | episode_a] second",
    ), world_seed=7, skin="aligned")
    assert [episode["episode_id"] for episode in result["episodes"]] == [
        "episode_b", "episode_a"
    ]
    assert [row["row_id"] for row in result["episodes"][0]["rows"]] == [
        "row_a", "row_c"
    ]
    assert result["episodes"][0]["rows"][0]["row"] == "[row_a | episode_b] first"
    assert result["episodes"][0]["rows"][0]["row_sha256"] == hashlib.sha256(
        b"[row_a | episode_b] first"
    ).hexdigest()
    flattened = [row["row"] for episode in result["episodes"] for row in episode["rows"]]
    assert flattened == [
        "[row_a | episode_b] first",
        "[row_c | episode_b] third",
        "[row_b | episode_a] second",
    ]


def test_explicit_segment_mode_preserves_interleaved_input_order():
    result = export_rows((
        "[row_a | episode_b] first",
        "[row_b | episode_a] second",
        "[row_c | episode_b] third",
    ), world_seed=7, skin="aligned", _preserve_noncontiguous=True)
    flattened = [row["row"] for episode in result["episodes"] for row in episode["rows"]]
    assert flattened == [
        "[row_a | episode_b] first",
        "[row_b | episode_a] second",
        "[row_c | episode_b] third",
    ]
    assert [episode["episode_id"] for episode in result["episodes"]] == [
        "episode_b", "episode_a", "episode_b#segment2"
    ]


def test_semantic_export_is_deterministic_and_whole_life_identified():
    first = export_semantic_world(seed=0, skin="aligned")
    second = export_semantic_world(seed=0, skin="aligned")
    assert first == second
    assert first["world_id"] == first["world"]["id"]
    assert first["skin_id"] == first["skin"]["id"] == "aligned"
    assert first["life_id"] == first["life"]["id"]
    assert first["life"]["row_count"] == sum(
        len(episode["rows"]) for episode in first["episodes"]
    )
    all_rows = [row for episode in first["episodes"] for row in episode["rows"]]
    payload = [{
        "row_id": row["row_id"],
        "episode_id": row["episode_id"],
        "row": row["row"],
        "row_sha256": row["row_sha256"],
    } for row in sorted(all_rows, key=lambda row: row["row_index"])]
    assert first["life"]["life_sha256"] == hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True,
                   separators=(",", ":")).encode()
    ).hexdigest()


def test_seed_specific_world_identity_preserves_family_tag():
    seed_zero = export_semantic_world(seed=0, skin="aligned")
    seed_one = export_semantic_world(seed=1, skin="aligned")
    assert seed_zero["world_id"] != seed_one["world_id"]
    assert seed_zero["world"]["id"] != seed_one["world"]["id"]
    assert seed_zero["world_family"] == seed_one["world_family"] == "semantic_world_v0.2"
    assert seed_zero["world"]["family"] == seed_one["world"]["family"]
    assert seed_zero["life_id"] != seed_one["life_id"]


def test_export_has_no_goal_answer_or_hidden_truth_fields():
    result = export_semantic_world(seed=0, skin="neutral")
    serialized = json.dumps(result).lower()
    for forbidden in ("\"goals\"", "\"answers\"", "\"hidden_roles\"", "\"parents\""):
        assert forbidden not in serialized
    assert "public_vocabulary" in result
    assert result["candidate_distractor_source"]["truth_source"] == "none"


def test_public_vocabulary_and_distractors_are_row_derived():
    result = export_rows((
        "[r1 | e1] Its coat is red.",
        "[r2 | e1] state-token blue-green.",
        "[r3 | e2] a mixture is labeled ochre.",
    ), world_seed=1, skin="aligned")
    assert result["public_vocabulary"] == ["blue-green", "ochre", "red"]
    assert result["candidate_distractor_source"]["candidates"] == result["public_vocabulary"]


def test_missing_or_duplicate_provenance_fails_closed():
    for rows in (("no provenance",), ("[r1 | e1] x", "[r1 | e2] y")):
        try:
            export_rows(rows, world_seed=0, skin="aligned")
        except PublicEpisodeError:
            continue
        raise AssertionError("invalid public episode input was accepted")


def test_explicit_latent_text_is_rejected_before_export():
    try:
        export_rows((
            "[r1 | e1] hidden answer: purple",
        ), world_seed=0, skin="aligned")
    except PublicEpisodeError as error:
        assert "forbidden latent text" in str(error)
    else:
        raise AssertionError("explicit latent answer text was accepted")
