"""L0 mini-world: 4 human-writable patterns, 24 ingredients, flat (no
tiers). The precursor test bed: memory machinery must MATCH the
in-context player here or the machinery is wrong (Rohin's bar).
Patterns: (1) type-C touches anything -> NOTHING (inert)
          (2) same type + same type -> RUIN
          (3) A+B -> PRODUCT   (4) B+D -> PRODUCT   (else NOTHING)
Product name = canonical join: '<a>-<b> brew' (legible; never scored on
derivation — kind + name-mention only)."""
from __future__ import annotations
import numpy as np

_SYL_A = ("vex","mor","tes","gal","rin","dru","kel","sab","fen","lur",
          "os","quin","bel","har","nym","cor","zan","pol","mir","tal",
          "ur","jas","wen","dov")
TYPES = ("A","B","C","D")

class MiniWorld:
    def __init__(self, seed=0):
        rng = np.random.default_rng(seed)
        names = [s + e for s, e in zip(_SYL_A, ("il","run","sic","eth","ock",
                 "ane","ura","esk","ov","ith","ard","une","yl","ost","ira",
                 "em","ash","orn","ude","eft","ion","arl","ows","ekt"))]
        rng.shuffle(names)
        self.type_of = {n: TYPES[i % 4] for i, n in enumerate(names)}
        self.ingredients = sorted(names)

    def predict(self, a, b):
        ta, tb = self.type_of[a], self.type_of[b]
        if "C" in (ta, tb):
            return ("nothing", None)
        if ta == tb:
            return ("ruin", None)
        pair = frozenset((ta, tb))
        if pair in (frozenset("AB"), frozenset("BD")):
            x, y = sorted((a, b))
            # arbitrary (non-derivable) name: stable hash-pick of syllables
            i = (sum(ord(c) for c in x) * 31 + sum(ord(c) for c in y)) % 97
            return ("product", f"{_SYL_A[i % len(_SYL_A)]}{_SYL_A[(i//7) % len(_SYL_A)]}ine")
        return ("nothing", None)

    def combine_text(self, a, b):
        k, p = self.predict(a, b)
        if k == "product":
            return k, p, f"You combine {a} and {b}. They fuse into {p}."
        if k == "ruin":
            return k, p, f"You combine {a} and {b}. The mixture curdles and is ruined."
        return k, p, f"You combine {a} and {b}. Nothing happens."

    def holdout(self, frac=0.3, seed=0):
        import itertools
        rng = np.random.default_rng(seed + 7)
        pairs = list(itertools.combinations(self.ingredients, 2))
        idx = rng.permutation(len(pairs))[:int(frac * len(pairs))]
        return {tuple(sorted(pairs[i])) for i in idx}


def gen_episode(w, rng, holdout, max_steps=6):
    names = w.ingredients
    # winnable: inventory contains a reactive pair avoiding holdout
    while True:
        inv = list(rng.choice(names, 5, replace=False))
        pairs = [(a, b) for i, a in enumerate(inv) for b in inv[i+1:]
                 if tuple(sorted((a, b))) not in holdout]
        prods = [(a, b) for a, b in pairs if w.predict(a, b)[0] == "product"]
        ok = all(tuple(sorted(p)) not in holdout
                 for i, a in enumerate(inv) for p in [(a, b) for b in inv[i+1:]])
        if prods and ok:
            break
    goal_pair = prods[int(rng.integers(len(prods)))]
    goal = w.predict(*goal_pair)[1]
    tried, log = set(), []
    for step in range(max_steps):
        cand = [(a, b) for i, a in enumerate(inv) for b in inv[i+1:]
                if tuple(sorted((a, b))) not in tried]
        if not cand:
            break
        a, b = cand[int(rng.integers(len(cand)))]
        tried.add(tuple(sorted((a, b))))
        k, p, obs = w.combine_text(a, b)
        log.append({"action": f"combine {a} {b}", "obs": obs})
        if p == goal:
            return {"goal": goal, "inventory": inv, "log": log, "success": True}
    return {"goal": goal, "inventory": inv, "log": log, "success": False}


def gen_life(w, n, holdout, seed=0):
    rng = np.random.default_rng(seed)
    return [gen_episode(w, rng, holdout) for _ in range(n)]


def life_text(life):
    lines = []
    for i, ep in enumerate(life):
        lines.append(f"[game {i}] goal: {ep['goal']} | success: {ep['success']}")
        lines += [f"  {st['obs']}" for st in ep["log"]]
    return "\n".join(lines)
