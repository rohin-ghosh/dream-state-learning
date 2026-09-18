"""Curriculum: the stage schedule, per-gym shares per round, exit criteria on
a synthetic ledger (computed and logged, never enforced), and the
run_life_v2 --curriculum integration in the fake world.

  python3 tests/test_curriculum.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import golden_harness as gh  # noqa: E402
from organism_v6 import curriculum as cu  # noqa: E402


def synthetic_rows(n_inst=16, acts_per=4, first_action="A", improving=False,
                   pred=0.3, pred_alt=None, start_episode=0, family="fam1"):
    """n_inst episode instances of acts_per acts each. improving=False: every
    act after the first fails to improve (score flat) -> attempts after a
    non-improving outcome = acts_per - 2 per instance (the act after the
    first non-improving act onwards). Predictions alternate pred/pred_alt."""
    rows = []
    for i in range(n_inst):
        eid = f"{family}/p{start_episode + i}"
        for t in range(1, acts_per + 1):
            score = (0.1 * t) if improving else 0.2
            p = pred if (pred_alt is None or t % 2) else pred_alt
            rows.append(dict(kind="act", episode_id=eid, tick=t,
                             action=(first_action if t == 1 else f"x{t}"),
                             outcome="o", score=score, prediction=p))
            rows.append(dict(kind="thought", episode_id=eid, tick=t,
                             note=f"ACT: {first_action if t == 1 else 'x' + str(t)}"))
    return rows


def test_schedule_loading_and_stage_lookup():
    s = cu.load_schedule()
    assert s["name"].startswith("childhood_schedule_v1") and len(s["stages"]) == 3
    assert cu.total_sleeps(s) == 16
    for r in range(1, 9):
        assert cu.stage_for_round(s, r)[0] == 0
    for r in range(9, 13):
        assert cu.stage_for_round(s, r)[0] == 1
    for r in range(13, 17):
        assert cu.stage_for_round(s, r)[0] == 2
    idx, st, beyond = cu.stage_for_round(s, 17)
    assert idx == 2 and beyond is True and st["name"] == "3_exploration"
    # shares -> wake batches -> episodes per round per gym. The draft names the
    # trait gym only (review 2026-09-10: the deployment gym is the unseen
    # final test, never a childhood environment); the compiler gym falls to
    # min_batches like any gym absent from a stage
    for st in s["stages"]:
        assert set(st["shares"]) == {"reasoning_gym"}, st["shares"]
    assert cu.batches_for(s, 1, "reasoning_gym") == 4 and cu.batches_for(s, 1, "compiler") == 1
    assert cu.batches_for(s, 9, "reasoning_gym") == 4 and cu.batches_for(s, 9, "compiler") == 1
    assert cu.batches_for(s, 1, "unknown_gym") == 1, "min_batches for a gym not in the stage"
    assert cu.round_length(s, 1, "reasoning_gym", 8, 32) == 32
    assert cu.round_length(s, 1, "compiler", 8, 32) == 8
    assert cu.round_length(None, 1, "compiler", 8, 32) == 32, "no schedule = --sleep-every"
    # stage 2 no longer carries the vacuous family_accuracy_min 0.0
    assert "family_accuracy_min" not in s["stages"][1]["exit"]
    # round counts: what run_life_v2 will do, and its inverse
    assert cu.count_rounds(None, "compiler", 1024, 8, 32) == 32
    assert cu.count_rounds(None, "compiler", 100, 8, 32) == 4, "3 full sleeps + the final one"
    assert cu.count_rounds(None, "compiler", 16, 4, 8) == 2
    assert cu.count_rounds(s, "reasoning_gym", 512, 8, 32) == 16
    assert cu.count_rounds(s, "compiler", 128, 8, 32) == 16, "min_batches x 8 per round"
    assert cu.count_rounds(s, "reasoning_gym", 128, 8, 32) == 4
    assert cu.count_rounds(s, "compiler", 16, 4, 8) == 4
    for gym, n in (("reasoning_gym", 16), ("compiler", 16), ("reasoning_gym", 5)):
        eps = cu.episodes_for_rounds(s, gym, n, 8, 32)
        assert cu.count_rounds(s, gym, eps, 8, 32) == n, (gym, n, eps)
    assert cu.episodes_for_rounds(None, "x", 3, 8, 32) == 96
    # validation
    bad = dict(s)
    bad["stages"] = [dict(name="x", sleeps=1, shares={}, exit={"no_such": 1})]
    fd, p = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(bad, f)
    try:
        cu.load_schedule(p)
    except ValueError as e:
        assert "unknown exit criteria" in str(e)
    else:
        raise AssertionError("bad schedule accepted")
    finally:
        os.unlink(p)


def test_exit_metrics_on_a_synthetic_ledger():
    # window 1: 16 instances, 4 acts each, flat scores, one first action
    rows = synthetic_rows(16, 4, "A", improving=False, pred=0.3)
    # window 2: 16 instances, 2 acts each, improving, mixed first actions,
    # predictions spread
    rows += synthetic_rows(8, 2, "B", improving=True, pred=0.2, pred_alt=0.6,
                           start_episode=100, family="fam2")
    rows += synthetic_rows(8, 2, "C", improving=True, pred=0.2, pred_alt=0.6,
                           start_episode=200, family="fam2")
    fam = lambda eid: eid.split("/")[0]                   # noqa: E731
    m = cu.exit_metrics(rows, window_instances=16, frozen_median_acts=4.0,
                        rejections=["DONE", "REJECTED_BREVITY", "REJECTED_SCORE"],
                        family_of=fam)
    assert m["n_instances"] == 16 and m["actions_per_situation"] == 2.0
    assert m["actions_per_situation_ratio"] == 0.5 and m["frozen_reference"] == "frozen_median_given"
    assert m["attempts_after_nonimproving"] == 0.0, "every act improved"
    assert abs(m["predict_sd"] - 0.2) < 1e-9 and m["n_predictions"] == 32
    assert m["first_action_js"] is not None and m["first_action_js"] > 0.5, \
        "first actions moved from {A} to {B, C}"
    assert m["first_action_modal_share"] == 0.5
    assert m["brevity_rejections"] == 1 and m["score_rejections"] == 1
    assert m["family_accuracy"] == {"fam2": 0.2} and m["family_accuracy_min"] == 0.2
    # the flat window: attempts after a non-improving outcome = 2 per instance
    m1 = cu.exit_metrics(rows[:16 * 8], window_instances=16, frozen_median_acts=2.0)
    assert m1["actions_per_situation"] == 4.0 and m1["actions_per_situation_ratio"] == 2.0
    assert m1["attempts_after_nonimproving"] == 2.0 and m1["predict_sd"] == 0.0
    assert m1["first_action_js"] is None, "no previous window"
    # self-referenced frozen median when none is given
    m2 = cu.exit_metrics(rows, window_instances=16)
    assert m2["frozen_reference"] == "self_referenced_first_window" and m2["frozen_median_acts"] == 4.0
    assert m2["actions_per_situation_ratio"] == 0.5
    # exit checks against the shipped stages
    s = cu.load_schedule()
    c1 = cu.exit_check(s["stages"][0], m1)
    assert c1["met"] is True, c1                    # ratio 2.0 >= 0.7; aan 2 >= 2; brevity 0
    c1b = cu.exit_check(s["stages"][0], m)
    assert c1b["met"] is False
    assert c1b["criteria"]["actions_per_situation_ratio_min"]["met"] is False
    assert c1b["criteria"]["brevity_rejections_max"]["met"] is False
    c2 = cu.exit_check(s["stages"][1], m)
    assert c2["met"] is True and c2["criteria"]["predict_sd_min"]["value"] == m["predict_sd"]
    c2b = cu.exit_check(s["stages"][1], m1)
    assert c2b["met"] is False, "stage 2 can be NOT met (flat predictions)"
    assert set(c2b["criteria"]) == {"predict_sd_min"}
    c3 = cu.exit_check(s["stages"][2], m)
    assert c3["criteria"]["first_action_js_min"]["met"] is True
    assert c3["criteria"]["score_rejections_max"]["met"] is False and c3["met"] is False
    # unavailable metric -> not met, reason given
    c3b = cu.exit_check(s["stages"][2], m1)
    assert c3b["criteria"]["first_action_js_min"]["reason"] == "unavailable"
    assert c3b["met"] is False
    assert cu.exit_check(dict(name="empty", exit={}), m)["met"] is None


def test_exit_log_is_idempotent_and_never_enforces():
    root = tempfile.mkdtemp()
    for d, mark in (("sleep_0008", "DONE"), ("sleep_0016", "REJECTED_BREVITY")):
        os.makedirs(os.path.join(root, d, "adapter"))
        open(os.path.join(root, d, "adapter", mark), "w").write("ok\n")
    assert cu.recent_verdicts(root, 4) == ["DONE", "REJECTED_BREVITY"]
    s = cu.load_schedule()
    rows = synthetic_rows(32, 3)
    rec = cu.log_exit_check(root, 2, s, rows, wake_batch=8, log=lambda m: None)
    rec2 = cu.log_exit_check(root, 2, s, rows, wake_batch=8, log=lambda m: None)
    assert rec == rec2 and rec["enforced"] is False and rec["stage"] == "1_persistence"
    lines = open(os.path.join(root, cu.EXIT_LOG)).read().splitlines()
    assert len(lines) == 1
    assert rec["metrics"]["brevity_rejections"] == 1
    assert rec["check"]["criteria"]["brevity_rejections_max"]["met"] is False


def test_run_life_v2_curriculum_flag_end_to_end():
    tr = gh.run_scenario("armA", extra_argv=["--arm", "A", "--curriculum",
                                              cu.DEFAULT_SCHEDULE])
    files = tr["files"]
    # compiler share in stage 1 = 1 batch x wake_batch 4 -> a sleep every 4
    sleeps = sorted(k.split("/")[0] for k in files if k.startswith("sleep_") and k.endswith("COMPILED"))
    assert sleeps == ["sleep_0004", "sleep_0008", "sleep_0012", "sleep_0016"], sleeps
    recs = [json.loads(l) for l in files[cu.EXIT_LOG].splitlines() if l.strip()]
    assert [r["round"] for r in recs] == [1, 2, 3, 4]
    assert all(r["enforced"] is False and r["stage"] == "1_persistence" for r in recs)
    assert all(r["check"]["met"] in (True, False) for r in recs)
    assert recs[-1]["metrics"]["n_instances"] == 16


if __name__ == "__main__":
    import traceback
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for n, f in tests:
        try:
            f()
            print("PASS", n)
        except Exception:  # noqa: BLE001
            failed += 1
            print("FAIL", n)
            traceback.print_exc()
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
