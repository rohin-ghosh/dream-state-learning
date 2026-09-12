"""Regression: run_life_v2 with today's flags produces byte-identical prompt
text, chunk stream, parsed gym actions, THINK prompts, parent calls and
written files before and after the Gym-protocol refactor.

  python3 tests/test_compiler_golden.py            # compare with the golden
  python3 tests/test_compiler_golden.py --record   # (re)record the golden
  python3 -m pytest tests/test_compiler_golden.py -q

The golden (tests/golden/compiler_golden_v1.json) was recorded from the code
as it stood BEFORE gym_backend grew the Gym protocol (2026-09-10). Recording
again is a deliberate act: it means "today's behaviour is the new reference".
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import golden_harness as gh  # noqa: E402

GOLDEN = os.path.join(HERE, "golden", "compiler_golden_v1.json")


def _first_diff(a, b, path="") -> str | None:
    if type(a) is not type(b):
        return f"{path}: type {type(a).__name__} != {type(b).__name__}"
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                return f"{path}/{k}: missing in golden"
            if k not in b:
                return f"{path}/{k}: missing in current"
            d = _first_diff(a[k], b[k], f"{path}/{k}")
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = _first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    if a != b:
        sa, sb = str(a), str(b)
        i = next((i for i in range(min(len(sa), len(sb))) if sa[i] != sb[i]),
                 min(len(sa), len(sb)))
        return (f"{path}: differs at char {i}: golden={sa[max(0, i-60):i+60]!r}"
                f" current={sb[max(0, i-60):i+60]!r}")
    return None


def record():
    out = gh.run_all()
    os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
    with open(GOLDEN, "w") as f:
        json.dump(out, f, indent=0, sort_keys=True)
    for n, t in out.items():
        print("recorded", n, json.dumps(gh.summarize(t)))
    print("golden ->", GOLDEN)


def _compare(name):
    golden = json.load(open(GOLDEN))
    assert name in golden, f"scenario {name} not in golden; re-record"
    cur = gh.run_scenario(name)
    g = golden[name]
    assert g["argv"] == cur["argv"], (g["argv"], cur["argv"])
    d = _first_diff(g["events"], cur["events"], "events")
    assert d is None, f"[{name}] transcript differs: {d}"
    d = _first_diff(g["files"], cur["files"], "files")
    assert d is None, f"[{name}] written files differ: {d}"
    s = gh.summarize(cur)
    assert s["by_kind"].get("batch", 0) > 50 and s["by_kind"].get("gym_eval", 0) > 20
    return s


def test_golden_armB_gate_panel():
    s = _compare("armB_gate_panel")
    assert s["by_kind"].get("train", 0) == 2


def test_golden_armA():
    s = _compare("armA")
    assert "train" not in s["by_kind"]


def test_golden_armB_parent_brief():
    s = _compare("armB_parent_brief")
    assert s["by_kind"].get("parent_chat", 0) >= 1, "parent never fired"


def test_golden_armB_parent_agentic():
    _compare("armB_parent_agentic")


def test_golden_is_self_consistent():
    """Two runs of the same scenario in one process agree (determinism of the
    harness itself, independent of the golden file)."""
    a = gh.run_scenario("armA")
    b = gh.run_scenario("armA")
    assert _first_diff(a["events"], b["events"]) is None
    assert _first_diff(a["files"], b["files"]) is None


def test_resume_after_a_trainer_crash_reproduces_the_golden_files():
    """Review 2026-09-10 (coverage): a life killed inside its first sleep's
    trainer and relaunched with the same flags ends with exactly the golden
    files (markers resume every phase; nothing is redone or duplicated)."""
    import tempfile
    golden = json.load(open(GOLDEN))["armB_gate_panel"]
    root = tempfile.mkdtemp(prefix="golden_resume_")
    life = os.path.join(root, "life")
    gate_json = os.path.join(root, "gate_panel.json")
    with open(gate_json, "w") as f:
        json.dump(gh.GATE_PANEL, f)
    argv = ["--life-dir", life] + gh.BASE_ARGS + ["--arm", "B", "--probe-gate",
                                                 "--gate-panel", gate_json]
    gh.FAKE_TRAINER_FAIL["remaining"] = 1
    try:
        try:
            gh.run_life(argv)
        except RuntimeError as e:
            assert "simulated trainer crash" in str(e)
        else:
            raise AssertionError("the simulated crash did not propagate")
    finally:
        gh.FAKE_TRAINER_FAIL["remaining"] = 0
    assert os.path.exists(os.path.join(life, "sleep_0008", "COMPILED"))
    assert not os.path.exists(os.path.join(life, "sleep_0008", "adapter"))
    assert not os.path.exists(os.path.join(life, "LIFE_DONE"))
    tr = gh.run_life(argv)                          # relaunch, same flags
    files = gh._normalize(gh.collect_files(life), os.path.realpath(root), root)
    d = _first_diff(golden["files"], files, "files")
    assert d is None, f"resumed life differs from the golden: {d}"
    kinds = {}
    for e in tr.events:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    assert kinds.get("train") == 2 and kinds.get("gym_eval", 0) > 20


def test_resume_does_not_retrain_a_rejected_sleep():
    """A rejected candidate is a final write decision, not missing work.

    Regression for the seed-605 recovery incident: the old runner retrained a
    rejected historical sleep and reused its stale probe-gate JSON.
    """
    import tempfile
    root = tempfile.mkdtemp(prefix="golden_rejected_resume_")
    life = os.path.join(root, "life")
    gate_json = os.path.join(root, "gate_panel.json")
    with open(gate_json, "w") as f:
        json.dump(gh.GATE_PANEL, f)
    argv = ["--life-dir", life] + gh.BASE_ARGS + [
        "--arm", "B", "--probe-gate", "--gate-panel", gate_json]
    gh.run_life(argv)

    ad = os.path.join(life, "sleep_0008", "adapter")
    os.rename(os.path.join(ad, "DONE"), os.path.join(ad, "REJECTED_SCORE"))
    os.remove(os.path.join(life, "LIFE_DONE"))

    tr = gh.run_life(argv)
    assert not any(e["kind"] == "train" for e in tr.events)
    assert os.path.exists(os.path.join(ad, "REJECTED_SCORE"))
    assert not os.path.exists(os.path.join(ad, "DONE"))


def test_multiple_final_adapter_verdicts_fail_closed(tmp_path):
    ad = tmp_path / "adapter"
    ad.mkdir()
    (ad / "DONE").write_text("ok\n")
    (ad / "REJECTED_SCORE").write_text("old\n")
    try:
        gh.run_life_v2.existing_adapter_verdict(str(ad))
    except RuntimeError as e:
        assert "ambiguous adapter verdicts" in str(e)
    else:
        raise AssertionError("ambiguous final markers did not fail closed")


if __name__ == "__main__":
    if "--record" in sys.argv:
        record()
        sys.exit(0)
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
