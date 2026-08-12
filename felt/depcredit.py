"""Dependency credit — fact-level, outcome-derived salience (note 26, APPROVED
2026-08-12 after GO/NO-GO: binary credit +0.383 vs label ceiling +0.386).

credit(fact instance) = Σ positive TD of steps at-or-after its emission, in
the SAME WORLD's episode stream, whose progress DEPENDED on the fact's content:
  recipe "crafting X requires A and B"  <- successful `craft X` steps
  binding "R is found at L"             <- successful `gather R` steps
  decor / count                          <- zero BY THE DAG'S CAUSAL STRUCTURE
                                            (nothing ever depends on them)
Binary mode (the approved default): credit = 1 iff any dependent use exists.
FIREWALL: computed from (trajectory, TD, action outcomes) only — the probe's
gist/verbatim labels are never read.
"""

from __future__ import annotations

from collections import defaultdict


def world_fact_credit(recs: list, binary: bool = True) -> dict:
    """recs: one world's episode records (rollouts.jsonl dicts), in stream
    order. Returns {(episode_uid, fact_idx): credit} for every fact with a
    real emission step (fact_idx = index within rec['facts'])."""
    events = []                 # (global_step, kind, arg, positive_td)
    facts = []                  # (uid, idx, kind, text, global_emission_step)
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

    use_td = defaultdict(list)  # ("craft", item)/("gather", raw) -> [(g, td)]
    for gs, kind, arg, td in events:
        if kind and td > 0:
            use_td[(kind, arg)].append((gs, td))

    out = {}
    for uid, j, kind, text, gstep in facts:
        if kind == "recipe":            # "crafting X requires A and B"
            key = ("craft", text.split(" ")[1])
        elif kind == "location":        # "R is found at L"
            key = ("gather", text.split(" ")[0])
        else:
            out[(uid, j)] = 0.0
            continue
        c = sum(td for gs, td in use_td.get(key, ()) if gs >= gstep)
        out[(uid, j)] = float(c)

    if binary:
        return {k: (1.0 if v > 0 else 0.0) for k, v in out.items()}
    mx = max(out.values(), default=1.0) or 1.0
    return {k: v / mx for k, v in out.items()}
