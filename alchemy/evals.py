"""Eval: held-out pair prediction with confabulation pricing + gates
(SPEC_V2 §7). Ground truth is free — we set the latent."""

from __future__ import annotations

import re
import numpy as np

Q = ("In the alchemy world you have experienced, what happens when you "
     "combine {a} and {b}? Answer with exactly one of: "
     "PRODUCT <name> | NOTHING | RUIN | UNKNOWN.")


def parse_answer(text: str):
    t = text.upper()
    m = re.search(r"PRODUCT\s+([\w-]+)", t)
    if m:
        return ("product", m.group(1).lower())
    for k in ("NOTHING", "RUIN", "UNKNOWN"):
        if k in t:
            return (k.lower(), None)
    return ("unparseable", None)


def score_pair(pred, truth):
    """Confabulation-priced scoring: correct=1, abstain=0.25,
    confident-wrong=0 (and counted as a confabulation)."""
    kind, name = pred
    tkind, tname = truth
    if kind == "unknown":
        return 0.25, False
    if kind == "unparseable":
        return 0.0, False
    if kind != tkind:
        return 0.0, True
    if tkind == "product":
        ok = name is not None and name == (tname or "").lower()
        return (1.0, False) if ok else (0.0, True)
    return 1.0, False


def eval_pairs(ask_fn, world, pairs: list) -> dict:
    """ask_fn(question) -> answer text. Returns accuracy/abstain/confab."""
    scores, confabs, abstains = [], 0, 0
    for a, b in pairs:
        pred = parse_answer(ask_fn(Q.format(a=a, b=b)))
        s, confab = score_pair(pred, world.predict(a, b))
        scores.append(s)
        confabs += int(confab)
        abstains += int(pred[0] == "unknown")
    n = max(len(pairs), 1)
    return {"score": float(np.mean(scores)) if scores else 0.0,
            "exact_acc": float(np.mean([s == 1.0 for s in scores])),
            "confab_rate": confabs / n, "abstain_rate": abstains / n,
            "n": len(pairs)}


def split_pairs(world, seen: set, rng=None):
    """seen (recall gate G1 + exact-recall row) vs held-out (composition)."""
    rng = rng or np.random.default_rng(0)
    all_pairs = world.base_pairs()
    seen_l = [p for p in all_pairs if tuple(sorted(p)) in seen]
    held = [p for p in all_pairs if tuple(sorted(p)) not in seen]
    rng.shuffle(held)
    return seen_l, held
