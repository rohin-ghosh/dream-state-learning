"""Dependency credit v2 — fact-level, outcome-derived salience (note 27,
post-reversal-6). v1 was retracted: its kind-keyed branches made the target
a synonym of the structural label (AP 0.975) in a world where type and use
were coextensive. v2 requires the v1.1 world (goal pools, failed-craft
recipe emission, hint decor) and credits STRICTLY FUTURE uses:

  recipe   <- later successful `craft <item>`          (strict >)
  location <- later successful `gather <r>` at its site
  decor    <- later successful gather AT ITS SITE of a raw its hint word
              implies (world.hint_map)  — usable verbatim-class knowledge
  count    <- never (pure junk is retained BY DESIGN; the profile needs it)
  hint     <- later successful gather of the implied raw anywhere

FIREWALL + LEAKAGE CANARY: nothing reads `structural`; ap_leakage() reports
AP(credit -> structural) every run — target ~ base rate. v1.0 scored 0.975;
that number was the bug.
"""

from __future__ import annotations

import re
from collections import defaultdict

import numpy as np


def world_fact_credit(recs: list, world, binary: bool = True) -> dict:
    """recs: one world's episode records in stream order; world: the World
    (for hint_map + raw_locations). Returns {(episode_uid, fact_idx): credit}."""
    hint_map = getattr(world, "hint_map", {}) or {}
    raw_loc = world.raw_locations

    events = []                 # (gstep, kind, arg, positive_td)
    facts = []
    g = 0
    for rec in recs:
        traj = rec["trajectory"]
        for st in traj:
            act = st["action"]
            td = max(0.0, float(st.get("td_signed", st["salience"])))
            if act.startswith("craft") and "You craft" in st["obs"]:
                kind = "craft"
            elif act.startswith("gather") and "You gather" in st["obs"]:
                kind = "gather"
            else:
                kind = ""
            arg = act.split(" ", 1)[1].strip() if " " in act else ""
            events.append((g, kind, arg, td))
            g += 1
        base = g - len(traj)
        for j, fa in enumerate(rec["facts"]):
            if fa["step"] < 1:
                continue
            facts.append((rec["episode_uid"], j, fa["kind"], fa["text"],
                          base + fa["step"] - 1))

    # use-events indexed by what knowledge they could have rested on
    use_craft = defaultdict(list)     # item -> [(g, td)]
    use_gather = defaultdict(list)    # raw  -> [(g, td)]
    for gs, kind, arg, td in events:
        if td <= 0 or not kind:
            continue
        if kind == "craft":
            use_craft[arg].append((gs, td))
        else:
            use_gather[arg].append((gs, td))

    out = {}
    for uid, j, kind, text, gstep in facts:
        c = 0.0
        if kind == "recipe":               # "crafting X requires A and B"
            item = text.split(" ")[1]
            c = sum(td for gs, td in use_craft.get(item, ()) if gs > gstep)
        elif kind == "location":           # "R is found at L"
            raw = text.split(" ")[0]
            c = sum(td for gs, td in use_gather.get(raw, ()) if gs > gstep)
        elif kind == "decor":              # "site_3 looked mossy during ..."
            m = re.match(r"(\S+) looked (\S+) ", text)
            if m and m.group(2) in hint_map:
                raw = hint_map[m.group(2)]
                if raw_loc.get(raw) == m.group(1):
                    c = sum(td for gs, td in use_gather.get(raw, ())
                            if gs > gstep)
        elif kind == "hint":               # "sites that look W always hold R"
            raw = text.split(" ")[-1]
            c = sum(td for gs, td in use_gather.get(raw, ()) if gs > gstep)
        # count -> 0: episodic junk stays junk by design
        out[(uid, j)] = float(c)

    if binary:
        return {k: (1.0 if v > 0 else 0.0) for k, v in out.items()}
    mx = max(out.values(), default=1.0) or 1.0
    return {k: v / mx for k, v in out.items()}


def ap_leakage(credit: dict, recs: list) -> float:
    """LEAKAGE CANARY: AP of credit against the structural label. Reported
    every run; must sit near the base rate (v1.0 bug: 0.975)."""
    by_uid = {r["episode_uid"]: r for r in recs}
    scores, labels = [], []
    for (uid, j), c in credit.items():
        scores.append(c)
        labels.append(bool(by_uid[uid]["facts"][j]["structural"]))
    scores, labels = np.array(scores), np.array(labels)
    order = np.argsort(-scores)
    labels = labels[order]
    hits, ap = 0, 0.0
    for i, y in enumerate(labels, 1):
        if y:
            hits += 1
            ap += hits / i
    return float(ap / max(1, hits))
