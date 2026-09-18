import json
import os

from organism_v6 import parenting_dynamics as pd


BRIEF = "Compare this case against prior evidence and test another route."


def _line(fh, row):
    fh.write(json.dumps(row) + "\n")


def _write_life(root, name, n, *, lesson_after=None, delivered=True,
                wake_end=None):
    life = os.path.join(root, name)
    os.makedirs(life)
    with open(os.path.join(life, "ledger.jsonl"), "w") as fh:
        for i in range(n):
            post = lesson_after is not None and i >= lesson_after
            prompt = f"birth\n{BRIEF}" if post and delivered else "birth"
            # First executed action and its thought.
            _line(fh, {"kind": "act", "episode_id": f"p{i}", "tick": 1,
                       "action": "-a", "prediction": 0.2, "score": 0.2})
            _line(fh, {"kind": "thought", "episode_id": f"p{i}", "tick": 1,
                       "note": "PREDICT: 0.2\nACT: -a\nNOTE: apply usual routine",
                       "prompt": prompt})
            # A post-lesson episode considers and executes a predicted change.
            second = "-b" if post else "-a"
            text = ("I will switch to a different route.\n" if post else "")
            text += (f"PREDICT: 0.3\nACT: {second}\nNOTE: " +
                     ("compare this case against prior evidence and test another route"
                      if post else "apply usual routine"))
            _line(fh, {"kind": "act", "episode_id": f"p{i}", "tick": 2,
                       "action": second, "prediction": 0.3,
                       "score": 0.4 if post else 0.2})
            _line(fh, {"kind": "thought", "episode_id": f"p{i}", "tick": 2,
                       "note": text, "prompt": prompt})
    end = n if wake_end is None else wake_end
    with open(os.path.join(life, f"wake_0000_{end:04d}.json"), "w") as fh:
        json.dump({}, fh)
    for at in range(32, n + 1, 32):
        sleep = os.path.join(life, f"sleep_{at:04d}")
        os.makedirs(os.path.join(sleep, "adapter"))
        open(os.path.join(sleep, "adapter", "DONE"), "w").close()
    return life


def _write_valid_brief(life, *, at=32, hits=None, version="v3-test",
                       intervened=True):
    sleep = os.path.join(life, f"sleep_{at:04d}")
    os.makedirs(sleep, exist_ok=True)
    with open(os.path.join(sleep, "parent_brief.txt"), "w") as fh:
        fh.write(BRIEF)
    with open(os.path.join(sleep, "parent_brief.json"), "w") as fh:
        json.dump({"intervened": intervened, "metrics": {"ritual": True},
                   "prompt_version": version,
                   "hits": [] if hits is None else hits, "text": BRIEF,
                   "parent_model": "test-parent"}, fh)


def _write_probe(life, at=64):
    for suffix, action, score in (("", "-b", 0.5),
                                  ("_adapterOFF", "-a", 0.4)):
        stem = os.path.join(life, f"probe_ep{at:04d}{suffix}")
        with open(stem + ".ledger.jsonl", "w") as fh:
            _line(fh, {"kind": "act", "episode_id": "q", "tick": 1,
                       "action": action, "prediction": 0.3, "score": score})
            _line(fh, {"kind": "thought", "episode_id": "q", "tick": 1,
                       "note": f"PREDICT: 0.3\nACT: {action}",
                       "prompt": "birth only"})
        with open(stem + ".json", "w") as fh:
            json.dump({"mean": score, "results": {"q": score}}, fh)


def test_episode_reconstruction_uses_actual_actions_and_repeated_ids():
    rows = [
        {"kind": "act", "episode_id": "p", "tick": 1, "action": "a"},
        {"kind": "act", "episode_id": "p", "tick": 1, "action": "b"},
        {"kind": "thought", "episode_id": "p", "tick": 1,
         "note": "ACT: hallucinated", "prompt": "x"},
        {"kind": "thought", "episode_id": "p", "tick": 2,
         "note": "more", "prompt": "x"},
        {"kind": "thought", "episode_id": "p", "tick": 1,
         "note": "ACT: prose-only", "prompt": "x"},
    ]
    episodes = pd.episode_texts(rows)
    assert len(episodes) == 2
    assert [x["action"] for x in episodes[0]["acts"]] == ["a", "b"]
    assert episodes[1]["acts"] == []
    stats = pd.window_stats(episodes[1:], 0, 1, set())
    assert stats["n_with_first_act"] == 0


def test_valid_delivered_event_uses_nonoverlapping_windows_and_probe(tmp_path):
    root = str(tmp_path)
    parent = _write_life(root, "R4_B_seed1", 200, lesson_after=32)
    _write_valid_brief(parent)
    _write_probe(parent)
    _write_life(root, "R3_B_seed1", 200)

    out = pd.analyze(root)
    assert out["status"] == "exploratory_descriptive_only"
    assert out["n_parent_events"] == 1
    assert out["n_control_events"] == 1
    row = out["parent_events"][0]
    assert row["first_delivery_episode_ordinal"] == 32
    assert row["direct_window_delivery"]["coverage"] == 1.0
    assert row["windows"]["after_four_sleeps_32"][
        "indexed_brief_delivery"]["coverage"] == 1.0
    assert row["pre32"]["intent_realized_deviation_rate"] == 0.0
    assert row["windows"]["direct_32"]["stats"][
        "intent_realized_deviation_rate"] == 1.0
    assert row["windows"]["after_four_sleeps_32"]["stats"][
        "requested_start_episode_ordinal"] == 160
    assert row["windows"]["after_four_sleeps_32"]["stats"][
        "realized_stop_episode_ordinal"] == 192
    writes = row["windows"]["direct_32"]["write_events"]
    assert writes["start_boundary_write_status"] == "committed"
    assert writes["active_committed_adapter_sleep"] == 32
    assert writes["writes_completed_strictly_inside_window"]["attempted"] == 0
    assert writes["write_after_window_at_stop_boundary"] == "committed"
    probe = row["parent_absent_probe_pairs"][0]
    assert probe["parent_text_absent_from_stored_prompts"] is True
    assert abs(probe["mean_delta"] - 0.1) < 1e-9
    assert "Generated ACT-like prose" in out["limitations"][-1]


def test_invalid_or_undelivered_brief_is_excluded(tmp_path):
    root = str(tmp_path)
    invalid = _write_life(root, "R4_B_seed1", 64, lesson_after=32)
    _write_valid_brief(invalid, hits=["leak"])
    undelivered = _write_life(root, "R4_B_seed2", 64, lesson_after=32,
                              delivered=False)
    _write_valid_brief(undelivered)
    out = pd.analyze(root)
    assert out["n_parent_events"] == 0
    reasons = {x["reason"] for x in out["excluded"]}
    assert reasons == {"no_valid_exactly_delivered_v3_brief"}


def test_missing_scan_metadata_mismatch_and_parent_error_are_invalid(tmp_path):
    root = str(tmp_path)
    for seed, mutation in enumerate(({"hits": None}, {"text": "different"},
                                     {"fallback": True}), 1):
        life = _write_life(root, f"R4_B_seed{seed}", 64, lesson_after=32)
        _write_valid_brief(life)
        path = os.path.join(life, "sleep_0032", "parent_brief.json")
        meta = json.load(open(path))
        meta.update(mutation)
        with open(path, "w") as fh:
            json.dump(meta, fh)
    out = pd.analyze(root)
    assert out["n_parent_events"] == 0
    assert len(out["excluded"]) == 3


def test_contaminated_probe_suppresses_deltas(tmp_path):
    root = str(tmp_path)
    parent = _write_life(root, "R4_B_seed1", 64, lesson_after=32)
    _write_valid_brief(parent)
    _write_probe(parent)
    on = os.path.join(parent, "probe_ep0064.ledger.jsonl")
    rows = [json.loads(line) for line in open(on) if line.strip()]
    rows[-1]["prompt"] = "birth\n=== YOUR PARENT ===\npartial advice"
    with open(on, "w") as fh:
        for row in rows:
            _line(fh, row)
    probe = pd.analyze(root)["parent_events"][0]["parent_absent_probe_pairs"][0]
    assert probe["qualifying_parent_absent_pair"] is False
    assert probe["mean_delta"] is None and probe["delta"] is None


def test_rejected_boundary_reports_previous_active_adapter(tmp_path):
    life = _write_life(str(tmp_path), "R4_B_seed1", 64, lesson_after=32)
    os.remove(os.path.join(life, "sleep_0064", "adapter", "DONE"))
    open(os.path.join(life, "sleep_0064", "adapter", "REJECTED_SCORE"),
         "w").close()
    event = pd.write_events(life, 64, 96)
    assert event["start_boundary_write_status"] == "REJECTED_SCORE"
    assert event["active_committed_adapter_sleep"] == 32


def test_missing_wake_receipt_is_not_clean(tmp_path):
    root = str(tmp_path)
    life = _write_life(root, "R4_B_seed1", 64, lesson_after=32)
    _write_valid_brief(life)
    os.remove(os.path.join(life, "wake_0000_0064.json"))
    out = pd.analyze(root)
    assert out["n_parent_events"] == 0
    assert out["excluded"][0]["reason"] == "episode_count_mismatch_resume_or_replay"


def test_resume_mismatch_and_truncated_window_are_explicit(tmp_path):
    root = str(tmp_path)
    bad = _write_life(root, "R4_B_seed1", 65, lesson_after=32, wake_end=64)
    _write_valid_brief(bad)
    short = _write_life(root, "R4_B_seed2", 70, lesson_after=32)
    _write_valid_brief(short)
    out = pd.analyze(root)
    assert out["n_parent_events"] == 1
    assert any(x["reason"] == "episode_count_mismatch_resume_or_replay"
               for x in out["excluded"])
    s4 = out["parent_events"][0]["windows"]["after_four_sleeps_32"]["stats"]
    assert s4["n_episodes"] == 0
    assert s4["requested_start_episode_ordinal"] == 160
    assert s4["realized_stop_episode_ordinal"] == 70
    assert out["s4_sufficient"] is False


def test_cli_writes_new_report(tmp_path):
    root = str(tmp_path / "root")
    os.makedirs(root)
    _write_life(root, "R3_B_seed0", 8)
    out = str(tmp_path / "analysis" / "parent.json")
    pd.main(["--root", root, "--out", out])
    report = json.load(open(out))
    assert report["n_parent_events"] == 0
    assert report["status"] == "exploratory_descriptive_only"
