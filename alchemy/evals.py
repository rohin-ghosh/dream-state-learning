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


def family_of(name):
    return (name or "").rsplit("-", 1)[0]


def score_levels(pred, truth):
    """(exact, family, kind) booleans — family credit is the signature of
    geometry induction (fn products share families across pairs; an
    inducer that answers vex-II when truth is vex-III has the structure)."""
    kind_ok = pred[0] == truth[0]
    fam_ok = kind_ok and (truth[0] != "product" or
                          family_of(pred[1]) == family_of(truth[1] or "").lower()
                          or family_of(pred[1] or "") == family_of((truth[1] or "").lower()))
    exact = kind_ok and (truth[0] != "product" or
                         (pred[1] or "") == (truth[1] or "").lower())
    return exact, fam_ok, kind_ok


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
