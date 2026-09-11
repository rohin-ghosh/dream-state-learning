"""rg_band: the frozen-model band on CPU with a scripted model — on the real
reasoning gym when pip reasoning-gym is importable, else on a small fake Gym
with an exact ceiling. Also the A0 statement and the markdown table.

  <python> tests/test_rg_band.py
"""
from __future__ import annotations

import json
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from organism_v6 import rg_band  # noqa: E402
from organism_v6.gym_backend import Episode, Observation  # noqa: E402

SKIPPED = []


def _rg_available():
    try:
        import reasoning_gym  # noqa: F401
        return True
    except ImportError:
        return False


class FakeGym:
    """Exact-ceiling gym: the answer is the episode's seed; partial credit 0.5
    for the right parity; no end token; two families."""
    name = "fake_rg"
    reports_family_accuracy = True

    def exam_set(self):
        return [f"fk/alpha/{i}" for i in range(1, 4)] + [f"fk/beta/{i}" for i in range(1, 4)]

    def gate_set(self):
        return [f"fk/gamma/{i}" for i in range(1, 5)]

    def canary_set(self):
        return []

    def benchmarks(self, split):
        return self.exam_set()

    def birth_prompt(self):
        return "You are in a puzzle workshop. verifier scores your ACT: line."

    def family_of(self, eid):
        return eid.split("/")[1]

    def headroom_ceiling(self, ep):
        return 1.0

    def offers_end_token(self):
        return False

    def episode_from_id(self, eid, budget_ticks=None):
        return Episode(eid=eid, goal=f"Guess the number for {eid}.", metric="score in [0,1]",
                       intro=f"New puzzle {eid}.", family=self.family_of(eid), budget_ticks=budget_ticks)

    def step(self, ep, action_text):
        ep.n_attempts += 1
        a = action_text.strip()
        if not a:
            return Observation(text=f"INVALID: attempt {ep.n_attempts} was empty", score=0.0)
        try:
            n = int(a)
        except ValueError:
            return Observation(text="INVALID: not a number", score=0.0)
        target = int(ep.eid.rsplit("/", 1)[1])
        s = 1.0 if n == target else (0.5 if n % 2 == target % 2 else 0.0)
        ep.best_score = max(ep.best_score, s)
        return Observation(text=f"attempt {ep.n_attempts}: verifier score {s:.2f}", score=s)

    def evaluate(self, ep, action_text=None):
        if action_text is None:
            return float(ep.best_score)
        o = self.step(ep, action_text)
        return o.score, o.text

    def family_accuracy(self, results):
        by = {}
        for e, s in results.items():
            by.setdefault(self.family_of(e), []).append(s)
        return {f: sum(v) / len(v) for f, v in by.items()}


class SeededGuesser:
    """A model whose guess depends on the chunk seed, so reps differ."""

    def batch(self, prompts, max_tokens=400, temperature=0.7, seeds=None):
        outs = []
        for j, p in enumerate(prompts):
            s = seeds[j] if seeds else j
            rng = random.Random(s)
            guess = rng.randint(1, 4)
            if rng.random() < 0.1:
                outs.append("thinking without acting this turn")
            elif rng.random() < 0.1:
                outs.append("PREDICT: 0.1\nACT: notanumber")
            else:
                outs.append(f"PREDICT: 0.5\nACT: {guess}\nNOTE: guessed {guess}")
        return outs


def test_headroom_statement():
    h = rg_band.headroom(1.0, 0.30, 0.05)
    assert h["ok"] and h["gap"] == 0.7 and "YES" in h["statement"]
    assert not rg_band.headroom(1.0, 0.95, 0.01)["ok"], "gap below 0.10"
    assert not rg_band.headroom(1.0, 0.60, 0.20)["ok"], "gap below 3 SD"
    assert rg_band.headroom(None, 0.3, 0.1)["ok"] is None


def test_behaviour_stats_from_ledger_rows():
    rows = [dict(kind="act", episode_id="a", tick=1, action="1", outcome="attempt 1: verifier score 0.00"),
            dict(kind="act", episode_id="a", tick=2, action="1", outcome="attempt 2: verifier score 0.00"),
            dict(kind="act", episode_id="a", tick=3, action="", outcome="INVALID: attempt 3 was empty"),
            dict(kind="thought", episode_id="a", tick=1, note="ten words of thinking here one two three four five"),
            dict(kind="thought", episode_id="a", tick=2, note="six more words of thought here"),
            dict(kind="thought", episode_id="b", tick=1, note="one two three four"),
            dict(kind="act", episode_id="b", tick=1, action="2", outcome="attempt 1: verifier score 1.00"),
            dict(kind="thought", episode_id="c", tick=1, note="a b"),
            dict(kind="act", episode_id="c", tick=1, action="7", outcome="attempt 1: verifier score 0.50")]
    b = rg_band.behaviour_stats(rows)
    assert b["n_acts"] == 5 and abs(b["valid_action_rate"] - 0.8) < 1e-9 and b["n_problems"] == 3
    assert b["scoreable_problem_frac"] == 1.0 and b["attempts_per_problem_median"] == 1.0
    assert b["distinct_actions_per_problem_median"] == 1.0
    # words per problem: a = 16, b = 4, c = 2 -> median over ALL problems 4 (an instrument)
    assert b["child_words_per_problem_median"] == 4.0
    assert b["child_words_per_problem_median_unsolved"] is None and b["n_unsolved"] is None, "no scores given"
    # the brake reference: the median over the problems the frozen model did NOT solve (best < ceiling)
    b2 = rg_band.behaviour_stats(rows, best_scores={"a": 0.0, "b": 1.0, "c": 0.5}, ceiling=1.0)
    assert b2["n_unsolved"] == 2 and b2["n_solved"] == 1
    assert b2["child_words_per_problem_median_unsolved"] == 9.0, "median of a=16 and c=2, b (solved) excluded"
    assert b2["attempts_per_problem_median_unsolved"] == 2.0
    assert b2["child_words_per_problem_median"] == 4.0, "the all-problem instrument is unchanged"
    assert "child_tokens_per_problem_median" not in b2, "no chars/4 pseudo-tokens"


def test_band_on_fake_gym_with_seeded_model():
    gym = FakeGym()
    out = tempfile.mkdtemp(prefix="band_")
    s = rg_band.run_band(SeededGuesser(), gym, dict(exam=gym.exam_set(), gate=gym.gate_set(), empty=[]),
                         reps=3, base_seed=777, budget=4, out_dir=out, tag="t", log=lambda m: None)
    assert os.path.exists(os.path.join(out, "t.json")) and os.path.exists(os.path.join(out, "t.md"))
    assert s["driver"] == "NoEndTokenDriver" and s["sets"]["empty"]["n_instances"] == 0
    for name in ("exam", "gate"):
        d = s["sets"][name]
        assert d["reps"] == 3 and d["seeds"] == [777, 1777, 2777] and d["n_instances"] == len(getattr(gym, name + "_set")())
        assert set(d["per_instance"]) == set(getattr(gym, name + "_set")())
        for eid, pi in d["per_instance"].items():
            assert len(pi["scores"]) == 3 and 0 <= pi["min"] <= pi["mean"] <= pi["max"] <= 1
            assert pi["family"] == gym.family_of(eid)
        assert set(d["per_family"]) == {gym.family_of(e) for e in getattr(gym, name + "_set")()}
        assert len(d["rep_means"]) == 3 and abs(d["mean"] - sum(d["rep_means"]) / 3) < 1e-3  # both rounded to 4 dp
        assert d["sd_across_reps"] >= 0 and d["ceiling"] == 1.0
        assert 0 <= d["behaviour"]["valid_action_rate"] <= 1 and d["behaviour"]["attempts_per_problem_mean"] >= 0
        assert d["behaviour"]["n_problems"] == d["n_instances"]
        # the brake reference is over UNSOLVED problems (ceiling 1.0 known), per rep and averaged
        bh = d["behaviour"]
        assert bh["child_words_per_problem_median_unsolved"] is not None and bh["n_unsolved"] is not None
        assert bh["n_unsolved"] + bh["n_solved"] == d["n_instances"]
        assert len(bh["per_rep"]) == 3 and all("words_median_unsolved" in r for r in bh["per_rep"])
        assert bh["brake_reference"].startswith("median child words per problem over the problems the frozen model did not solve")
        # the guesser solves some problems by luck: solved ones are excluded from the reference
        solved_ids = {e for e, pi in d["per_instance"].items() if pi["max"] >= 1.0}
        assert solved_ids or bh["n_solved"] == 0
        assert "A0 headroom" in d["headroom"]["statement"] and d["headroom"]["ok"] in (True, False)
        for r in range(3):
            assert os.path.exists(os.path.join(out, f"t_{name}_rep{r}.ledger.jsonl"))
    # every problem ran to the budget (no end token) and generation was seeded per (episode, tick)
    rows = [json.loads(l) for l in open(os.path.join(out, "t_exam_rep0.ledger.jsonl")) if l.strip()]
    ticks = {}
    for r in rows:
        if r["kind"] == "thought":
            ticks[r["episode_id"]] = max(ticks.get(r["episode_id"], 0), r["tick"])
    assert all(t == 4 for t in ticks.values())
    md = rg_band.to_markdown(s)
    assert "| exam |" in md and "| gate |" in md and "A0 headroom" in md and "fk/alpha/1" in md
    assert "UNSOLVED (median; brake ref.)" in md and "Brake reference (CHILD_MECHANISM_v7 3.1)" in md
    # scores are not all identical across reps (the guesser is seeded per rep)
    assert any(pi["sd"] > 0 for pi in s["sets"]["exam"]["per_instance"].values())


def test_band_on_the_real_reasoning_gym_when_installed():
    if not _rg_available():
        SKIPPED.append("reasoning_gym not importable")
        print("SKIP reasoning_gym not importable")
        return
    from organism_v6.gym_backend import make_gym
    gym = make_gym("reasoning_gym")
    out = tempfile.mkdtemp(prefix="band_rg_")
    sets = dict(gate=gym.gate_set()[:2] + gym.gate_set()[6:8])
    s = rg_band.run_band(rg_band.ScriptedModel(), gym, sets, reps=2, base_seed=777, budget=2,
                         out_dir=out, tag="rg", log=lambda m: None)
    d = s["sets"]["gate"]
    assert d["n_instances"] == 4 and set(d["per_family"]) == {"n_queens", "tower_of_hanoi"}
    assert d["ceiling"] == 1.0 and d["headroom"]["ok"] is True, d["headroom"]
    assert d["behaviour"]["attempts_per_problem_mean"] == 2.0
    assert s["gym"] == "reasoning_gym" and s["birth_prompt_sha8"]


def test_cli_mock_smoke_on_fake_gym():
    from organism_v6 import gym_backend as gb
    gb.register_gym("_fake_rg", lambda **kw: FakeGym())
    out = tempfile.mkdtemp(prefix="band_cli_")
    try:
        rg_band.main(["--gym", "_fake_rg", "--sets", "exam,gate", "--reps", "2", "--budget-ticks", "2",
                      "--out-dir", out, "--tag", "smoke", "--mock"])
    finally:
        del gb._REGISTRY["_fake_rg"]
    s = json.load(open(os.path.join(out, "smoke.json")))
    assert s["reps"] == 2 and s["sets"]["exam"]["behaviour"]["n_acts"] == 12, "one ACT per turn, 2 turns x 6"
    assert s["sets"]["exam"]["behaviour"]["valid_action_rate"] == 0.0, "'1 2 3 4' is not a number here"
    assert s["sets"]["exam"]["mean"] == 0.0, "the scripted mock never solves anything"
    assert os.path.exists(os.path.join(out, "smoke.md"))


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
    print(f"{len(tests) - failed}/{len(tests)} passed"
          + (f" ({len(SKIPPED)} skipped: {SKIPPED})" if SKIPPED else ""))
    sys.exit(1 if failed else 0)
