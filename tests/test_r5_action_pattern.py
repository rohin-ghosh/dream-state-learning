import json

import pytest

from organism_v6.r5_action_pattern import normalize_action, paired_report


def _write(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_normalize_action():
    assert normalize_action(" -a,  -b , -c ") == "-a,-b,-c"


def test_paired_report_separates_first_action_and_search(tmp_path):
    on = tmp_path / "on.jsonl"
    off = tmp_path / "off.jsonl"
    _write(on, [
        {"kind": "act", "episode_id": "p1", "tick": 1,
         "action": "-a, -b", "score": .4},
        {"kind": "act", "episode_id": "p1", "tick": 2,
         "action": "-c", "score": .8},
        {"kind": "thought", "episode_id": "p1", "note": "ignored"},
        {"kind": "act", "episode_id": "p2", "tick": 1,
         "action": "-a, -b", "score": .2},
    ])
    _write(off, [
        {"kind": "act", "episode_id": "p1", "tick": 1,
         "action": "-x", "score": .3},
        {"kind": "act", "episode_id": "p2", "tick": 1,
         "action": "-x", "score": .1},
    ])
    report = paired_report(str(on), str(off), routine="-a,-b", caps=(1, 2))
    assert report["on"]["routine_first_count"] == 2
    assert report["off"]["routine_first_count"] == 0
    assert report["on"]["n_act_rows"] == 3
    assert report["on"]["n_nonempty_actions"] == 3
    assert report["fixed_action_caps"][1]["on_n_reaching_cap"] == 1
    assert report["fixed_action_caps"][1]["off_n_reaching_cap"] == 0
    assert report["fixed_action_caps"][0]["on_minus_off"] == pytest.approx(.1)
    assert report["fixed_action_caps"][1]["on_minus_off"] == pytest.approx(.3)
    assert report["on"]["n_episodes_with_act_at_or_after_tick16"] == 0
    assert "n_episodes_reaching_tick16" not in report["on"]


def test_tick16_field_counts_actions_not_unobserved_thoughts(tmp_path):
    on = tmp_path / "on.jsonl"
    off = tmp_path / "off.jsonl"
    _write(on, [
        {"kind": "act", "episode_id": "p1", "tick": 1,
         "action": "-a", "score": .2},
        {"kind": "thought", "episode_id": "p1", "tick": 16,
         "note": "This thought is deliberately ignored by the ACT reader."},
        {"kind": "act", "episode_id": "p2", "tick": 16,
         "action": "-b", "score": .3},
    ])
    _write(off, [
        {"kind": "act", "episode_id": "p1", "tick": 1,
         "action": "-a", "score": .2},
        {"kind": "act", "episode_id": "p2", "tick": 1,
         "action": "-b", "score": .3},
    ])
    report = paired_report(str(on), str(off), caps=(1,))
    assert report["on"]["n_episodes_with_act_at_or_after_tick16"] == 1
    assert report["off"]["n_episodes_with_act_at_or_after_tick16"] == 0


def test_paired_report_rejects_mismatched_panels(tmp_path):
    on = tmp_path / "on.jsonl"
    off = tmp_path / "off.jsonl"
    _write(on, [{"kind": "act", "episode_id": "p1", "tick": 1,
                 "action": "-a", "score": .4}])
    _write(off, [{"kind": "act", "episode_id": "p2", "tick": 1,
                  "action": "-a", "score": .4}])
    with pytest.raises(ValueError, match="same episode IDs"):
        paired_report(str(on), str(off))


def test_empty_act_row_is_counted_but_not_a_unique_pipeline(tmp_path):
    on = tmp_path / "on.jsonl"
    off = tmp_path / "off.jsonl"
    _write(on, [
        {"kind": "act", "episode_id": "p1", "tick": 1,
         "action": "", "score": 0.0},
        {"kind": "act", "episode_id": "p1", "tick": 2,
         "action": "-a", "score": .2},
    ])
    _write(off, [
        {"kind": "act", "episode_id": "p1", "tick": 1,
         "action": "-a", "score": .2},
    ])
    report = paired_report(str(on), str(off), routine="-a", caps=(1, 2))
    assert report["on"]["n_act_rows"] == 2
    assert report["on"]["n_nonempty_actions"] == 1
    assert report["on"]["n_empty_or_noop_act_rows"] == 1
    assert report["on"]["unique_nonempty_actions"] == 1


def test_malformed_act_and_wrong_expected_panel_fail(tmp_path):
    on = tmp_path / "on.jsonl"
    off = tmp_path / "off.jsonl"
    good = {"kind": "act", "episode_id": "p1", "tick": 1,
            "action": "-a", "score": .2}
    _write(on, [good])
    _write(off, [good])
    with pytest.raises(ValueError, match="expected panel IDs"):
        paired_report(str(on), str(off), expected_eids={"p2"})
    _write(on, [{**good, "score": "bad"}])
    with pytest.raises(ValueError, match="numeric score"):
        paired_report(str(on), str(off))
    _write(on, [{**good, "score": float("nan")}])
    with pytest.raises(ValueError, match="numeric score"):
        paired_report(str(on), str(off))
    _write(on, [{**good, "action": None}])
    with pytest.raises(ValueError, match="non-string action"):
        paired_report(str(on), str(off))


def test_tick_regression_fails(tmp_path):
    on = tmp_path / "on.jsonl"
    off = tmp_path / "off.jsonl"
    rows = [
        {"kind": "act", "episode_id": "p1", "tick": 2,
         "action": "-a", "score": .2},
        {"kind": "act", "episode_id": "p1", "tick": 1,
         "action": "-b", "score": .3},
    ]
    _write(on, rows)
    _write(off, rows[:1])
    with pytest.raises(ValueError, match="tick order regressed"):
        paired_report(str(on), str(off))
