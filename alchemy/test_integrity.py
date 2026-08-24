"""Eval-integrity regression tests (the catches, made permanent).
Run: PYTHONPATH=. python -m pytest alchemy/test_integrity.py -q
(or plain: PYTHONPATH=. python alchemy/test_integrity.py)"""
import json, glob
import numpy as np
from alchemy.world import AlchemyWorld
from alchemy.env import generate_life, seen_pairs
from alchemy.player import ScriptedExplorer
from alchemy.evals import parse_answer, score_pair
from alchemy import dreamer

def _world():
    return AlchemyWorld(n_ingredients=64, n_inert=8, seed=1,
                        n_essences=12, max_tier=3, rho_fn=0.4)

def test_parser():
    assert parse_answer("PRODUCT sabesk-II")[0] == "product"
    assert parse_answer("NOTHING")[0] == "nothing"
    assert parse_answer("I think RUIN")[0] == "ruin"
    assert parse_answer("UNKNOWN")[0] == "unknown"
    assert parse_answer("gibberish")[0] == "unparseable"

def test_confab_priced():
    assert score_pair(("unknown", None), ("product", "x"))[0] == 0.25
    s, confab = score_pair(("product", "wrong"), ("product", "x"))
    assert s == 0.0 and confab

def test_leakage_and_holdout():
    w = _world()
    h = w.sample_holdout(0.3, seed=1)
    eps = generate_life(w, ScriptedExplorer(seed=1), 60, inv_size=6,
                        seed=1, holdout=h)
    base = {p for p in seen_pairs(eps) if all(x in w.ingredients for x in p)}
    assert not (base & h), "holdout contamination"
    for line in dreamer.dumb_dream(eps)[:200]:
        assert not w.leakage_scan(line), "essence leak"

def test_world_deterministic():
    a, b = _world(), _world()
    assert sorted(a.ingredients) == sorted(b.ingredients)
    pr = sorted(a.ingredients)[:2]
    assert a.predict(*pr) == b.predict(*pr)

def test_no_pegged_confab_control():
    """A control that returns the same value in every cell cannot fail.
    Guard any committed micro results: control_abstain must VARY."""
    for f in glob.glob("alchemy/v2_out/micro_rigor_*.json"):
        r = json.load(open(f))
        vals = [c.get("control_abstain") for c in r.values()
                if "control_abstain" in c]
        if len(vals) >= 3:
            assert np.std(vals) > 0.0 or max(vals) > 0.05, \
                f"{f}: abstention control pegged — cannot discriminate"

if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"ok {name}")
