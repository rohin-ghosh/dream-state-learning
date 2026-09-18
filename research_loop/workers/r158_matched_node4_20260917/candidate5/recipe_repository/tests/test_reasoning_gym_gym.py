"""reasoning-gym adapter: split hygiene, verifier secrecy, reference scoring,
the multi-attempt episode, per-family accuracy and prompt sizes.

Needs pip reasoning-gym==0.1.25 (python >= 3.10); without it the script
prints SKIP and exits 0 so the suite still reports counts.

  python3 tests/test_reasoning_gym_gym.py
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    import reasoning_gym  # noqa: F401
    RG = True
except ImportError:
    RG = False

from organism_v6 import reasoning_gym_gym as rgg  # noqa: E402
from organism_v6.gym_backend import make_gym, Gym  # noqa: E402
from organism_v6.batch_loop import run_episodes_batch, driver_class_for  # noqa: E402
from organism_v6.ledger import Ledger  # noqa: E402

ALL_FAMILIES = ["sokoban", "rush_hour", "n_queens", "futoshiki", "kakurasu",
                "acre", "knights_knaves", "zebra_puzzles", "arc_1d",
                "countdown", "mini_sudoku", "tower_of_hanoi"]
N_ITEMS = 20


def _gym():
    return make_gym("reasoning_gym")


def _tampered(**changes):
    cfg = json.load(open(rgg.FAMILIES_JSON))
    cfg.update(changes)
    fd, p = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(cfg, f)
    return p


def encode(answer: str) -> str:
    """What the child would write after ACT: for a multi-line answer."""
    return rgg.LINE_SEP.join(str(answer).split("\n"))


# --- rush_hour reference by BFS over the package's own Board ---------------
def solve_rush_hour(board_config: str, max_states: int = 400000) -> str | None:
    from reasoning_gym.games.rush_hour import (Board, H, LEFT_COLUMN,
                                               RIGHT_COLUMN, TOP_ROW,
                                               BOTTOM_ROW, TARGET)
    b = Board(board_config)
    pieces = [(p.size, p.stride, p.fixed) for p in b._pieces]

    def mask_of(pos, size, stride):
        m = 0
        for i in range(size):
            m |= 1 << (pos + i * stride)
        return m

    start = tuple(p.position for p in b._pieces)
    seen = {start: None}
    queue = collections.deque([start])
    goal = None
    while queue:
        cur = queue.popleft()
        if cur[0] == TARGET:
            goal = cur
            break
        if len(seen) > max_states:
            return None
        masks = [mask_of(pos, s, st) for pos, (s, st, _f) in zip(cur, pieces)]
        board = 0
        for m in masks:
            board |= m
        for i, (size, stride, fixed) in enumerate(pieces):
            if fixed:
                continue
            m = masks[i]
            others = board & ~m
            for d in (-1, 1):
                if stride == H:
                    if (d < 0 and m & LEFT_COLUMN) or (d > 0 and m & RIGHT_COLUMN):
                        continue
                else:
                    if (d < 0 and m & TOP_ROW) or (d > 0 and m & BOTTOM_ROW):
                        continue
                nm = (m << stride) if d > 0 else (m >> stride)
                if nm & others:
                    continue
                nxt = list(cur)
                nxt[i] = cur[i] + d * stride
                nxt = tuple(nxt)
                if nxt not in seen:
                    seen[nxt] = (cur, i, d)
                    queue.append(nxt)
    if goal is None:
        return None
    moves = []
    node = goal
    while seen[node] is not None:
        prev, i, d = seen[node]
        moves.append(f"{chr(65 + i)}{'+' if d > 0 else '-'}1")
        node = prev
    return " ".join(reversed(moves))


# --- tests -------------------------------------------------------------------------
def test_installed_version_is_pinned():
    v = rgg.installed_version()
    assert v == rgg.PINNED_VERSION, f"reasoning_gym {v} != {rgg.PINNED_VERSION}"
    g = _gym()
    assert g.package_version == rgg.PINNED_VERSION


def test_split_ledger_hygiene():
    g = _gym()
    assert isinstance(g, Gym)
    tr, ga, ex = set(g.train_families), set(g.gate_families), set(g.exam_families)
    assert tr | ga | ex == set(ALL_FAMILIES), "the 12 C5 families, all placed"
    assert not (tr & ga) and not (tr & ex) and not (ga & ex)
    fam = lambda eid: rgg.parse_id(eid)[0]          # noqa: E731
    train_ids = g.benchmarks("train")
    assert train_ids and all(fam(e) in tr for e in train_ids)
    assert all(fam(e) in ga for e in g.gate_set()) and len(g.gate_set()) == 12
    assert all(fam(e) in ex for e in g.exam_set()) and len(g.exam_set()) == 12
    assert len(g.canary_set()) == 4 and all(fam(e) in tr for e in g.canary_set())
    # exam families never appear in train / gate / canary
    for e in train_ids + g.gate_set() + g.canary_set():
        assert fam(e) not in ex, e
    # seed ranges disjoint and respected
    for split in ("train", "gate", "exam", "canary"):
        lo, hi = g.seed_ranges[split]
        for e in g.benchmarks(split):
            assert lo <= rgg.parse_id(e)[1] < hi, (split, e)
    # a life's schedule draws only train families in the train range, balanced
    sched = g.training_schedule(210, seed=5)
    assert len(sched) == 210 and len(set(sched)) == 210
    lo, hi = g.seed_ranges["train"]
    c = collections.Counter(fam(e) for e in sched)
    assert set(c) == tr and min(c.values()) == 30 == max(c.values())
    assert all(lo <= rgg.parse_id(e)[1] < hi for e in sched)
    assert g.training_schedule(50, 5) == g.training_schedule(50, 5)       # seeded
    assert g.training_schedule(50, 5) != g.training_schedule(50, 6)
    # split_of classifies every fixed id
    assert {g.split_of(e) for e in g.exam_set()} == {"exam"}
    assert {g.split_of(e) for e in g.gate_set()} == {"gate"}
    assert {g.split_of(e) for e in g.canary_set()} == {"canary"}
    assert {g.split_of(e) for e in train_ids} == {"train"}
    # leak terms name the held-out families, never a train family
    lt = set(g.leak_terms())
    assert ex <= lt and ga <= lt and not (tr & lt)
    # excluded list: real generators, all target-blind exclusions
    from reasoning_gym.factory import DATASETS
    assert all(f in DATASETS for f in g.excluded)
    assert {"codeio", "list_functions"} <= g.excluded


def test_tampered_splits_are_refused():
    for changes, needle in (
        (dict(train_families=["countdown", "codeio"]), "code-like"),
        (dict(train_families=["countdown", "zebra_puzzles"]), "overlap"),
        (dict(gate_set=["rg/zebra_puzzles/2000001"]), "gate item"),
        (dict(exam_set=["rg/countdown/3000001"]), "exam item"),
        (dict(canary_set=["rg/countdown/1000001"]), "canary item"),
        (dict(seed_ranges={"train": [0, 10], "gate": [5, 20], "exam": [20, 30],
                           "canary": [30, 40]}), "seed ranges overlap"),
    ):
        p = _tampered(**changes)
        try:
            rgg.ReasoningGymGym(families_path=p)
        except RuntimeError as e:
            assert needle in str(e), (changes, str(e))
        else:
            raise AssertionError(f"tampered split accepted: {changes}")
        finally:
            os.unlink(p)


def test_verifier_never_reveals_answers():
    g = _gym()
    pat = re.compile(r"^attempt \d+: verifier score \d\.\d\d \((accepted|not accepted; partial credit|not accepted)\)$")
    for f in ALL_FAMILIES:
        for j in range(3):
            eid = rgg.make_id(f, 1000000 + 13 * j)
            ep = g.episode_from_id(eid)
            ref = g.reference_answer(eid)
            for wrong in ("nonsense", "1 2 3 4", "Move disk 1 from Peg 1 to Peg 2"):
                obs = g.step(ep, wrong)
                assert pat.match(obs.text), obs.text
                assert 0.0 <= obs.score <= 1.0
                if ref is not None and len(str(ref)) >= 3:
                    assert str(ref).strip() not in obs.text
            e = g.step(ep, "")
            assert e.text.startswith("INVALID") and e.score == 0.0
            # metadata never enters the child's texts; the reference answer
            # never does either, except where the puzzle statement itself
            # lists the candidate answers (acre: on/off/undetermined; zebra:
            # the names) — there the observation is what must stay silent
            for txt in (ep.goal, ep.intro, ep.metric):
                for key in ("source_index", "source_dataset", "board_config",
                            "min_moves", "valid_answers", "'solution':"):
                    assert key not in txt, (f, key)
                # (a very short move string such as sokoban's "UD" can occur
                # inside the puzzle's own format example — not a leak)
                if ref is not None and len(str(ref).strip()) >= 8 \
                        and f not in ("acre", "zebra_puzzles"):
                    assert str(ref).strip() not in txt, (f, eid)


def test_reference_scores_1_on_20_seeded_items_per_family():
    g = _gym()
    report = {}
    for f in ALL_FAMILIES:
        ok = 0
        for j in range(N_ITEMS):
            eid = rgg.make_id(f, 1000000 + 7 * j)
            ep = g.episode_from_id(eid)
            ref = g.reference_answer(eid)
            if ref is None:                          # simulation-verified
                _ds, entry = g._item(f, 1000000 + 7 * j)
                ref = solve_rush_hour(entry["metadata"]["board_config"])
                assert ref, f"BFS found no solution for {eid}"
            obs = g.step(ep, encode(ref))            # through the ' ; ' line codec
            assert obs.score == 1.0, (eid, obs)
            ok += 1
        report[f] = ok
    assert all(v == N_ITEMS for v in report.values()), report
    print("reference==1.0:", json.dumps(report))


class Scripted:
    """A model that answers the puzzle in front of it by looking the FULL
    question up in the prompt (the GOAL text carries it verbatim; question
    heads are identical within a family), following a per-episode attempt
    plan: wrong -> partial -> right -> DONE (ignored) -> reflect."""

    def __init__(self, plans):
        self.plans = plans          # full question text -> list of ACT lines
        self.calls = 0

    def batch(self, prompts, max_tokens=400, temperature=0.7, seeds=None):
        out = []
        for p in prompts:
            m = re.search(r"CLOCK: chunk (\d+)/", p)
            tick = int(m.group(1)) if m else 1
            plan = next((v for k, v in self.plans.items() if k in p), None)
            if plan is None or tick > len(plan):
                out.append("NOTE: thinking about the scores I got.\nDONE")
            else:
                out.append(f"PREDICT: 0.5\n{plan[tick - 1]}")
        self.calls += len(prompts)
        return out


def test_multi_attempt_episode_runs_to_budget_and_scores_best():
    g = _gym()
    eid = "rg/mini_sudoku/1000003"
    ep = g.episode_from_id(eid, 6)
    ref = g.reference_answer(eid)
    partial = ref.replace("1", "2", 1) if "1" in ref else ref[:-1]
    head = g.question(eid).strip()
    model = Scripted({head: ["ACT: 9 9 9 9", f"ACT: {encode(partial)}",
                             f"ACT: {encode(ref)}", "DONE"]})
    led = Ledger(os.path.join(tempfile.mkdtemp(), "l.jsonl"))
    res = run_episodes_batch(model, g, [ep], g.birth_prompt(), led, 6,
                             log=lambda m: None, gen_seed=7,
                             driver_cls=driver_class_for(g))
    r = res[0]
    assert r["ticks"] == 6, "no end token: the episode runs to its budget"
    assert r["best_score"] == 1.0 and r["n_acts"] == 3
    acts = [x for x in led.rows() if x["kind"] == "act"]
    scores = [a["score"] for a in acts]
    assert scores[0] < scores[1] < scores[2] == 1.0, scores
    assert 0.0 < scores[1] < 1.0, "partial credit relayed"
    for a in acts:
        assert ref not in a["outcome"] and "verifier score" in a["outcome"]
    assert g.evaluate(ep) == 1.0
    assert any(x["kind"] == "thought" and "DONE" in x["note"] for x in led.rows())


def test_probe_writes_per_family_accuracy():
    from organism_v6 import run_life_v2
    g = _gym()
    exam = g.exam_set()
    plans = {}
    for eid in exam:
        ref = g.reference_answer(eid)
        head = g.question(eid).strip()
        # zebra/acre: answer right away; rush_hour: no reference -> stays 0
        plans[head] = [f"ACT: {encode(ref)}"] if ref is not None else ["ACT: A+1"]
    model = Scripted(plans)
    life = tempfile.mkdtemp()
    run_life_v2.run_probes_batch(model, g, "ep0000", life, 2, lambda m: None)
    pj = json.load(open(os.path.join(life, "probe_ep0000.json")))
    fa = pj["family_accuracy"]
    assert set(fa) == set(g.exam_families), fa
    assert fa["zebra_puzzles"] == 1.0 and fa["acre"] == 1.0
    assert fa["rush_hour"] < 1.0
    assert abs(pj["mean"] - sum(pj["results"].values()) / len(pj["results"])) < 1e-9
    assert g.family_accuracy(pj["results"]) == fa


def test_prompt_sizes_measured_and_bounded():
    g = _gym()
    sizes = g.measure_prompt_sizes(3)
    assert set(sizes) == set(ALL_FAMILIES)
    for f, s in sizes.items():
        assert 0 < s["mean_chars"] <= s["max_chars"] < 8000, (f, s)
        assert s["est_tokens"] == round(s["mean_chars"] / 4)
    print("prompt sizes (goal text):", json.dumps(sizes))
    # a rendered context with the largest goal still fits the head budget
    from organism_v6.state import CHAR_BUDGET, State, render_context
    worst = max(sizes, key=lambda f: sizes[f]["max_chars"])
    ep = g.episode_from_id(rgg.make_id(worst, g.seed_ranges["train"][0]))
    st = State(goal=ep.goal, metric=ep.metric, episode_id=ep.eid, budget_ticks=16)
    ctx = render_context(g.birth_prompt(), st, [], [ep.intro])
    assert len(ctx) < CHAR_BUDGET and ep.intro in ctx


if __name__ == "__main__":
    if not RG:
        print("SKIP: reasoning_gym not importable — pip install "
              "reasoning-gym==0.1.25 into a python>=3.10 venv")
        print("0/0 passed (skipped)")
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
