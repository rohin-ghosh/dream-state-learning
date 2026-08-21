"""GO/NO-GO simulation for note 26 (fact-level dependency credit) — CPU-only,
logged-data-only, NO design changes. Computes the TRUE dependency credit for
every fact instance in the S1 log and runs it through the S3 policy machinery
as a new ceiling row.

credit(fact instance) = Σ positive TD of later steps in the SAME WORLD's
stream (across episodes) that USE the fact's content:
  recipe "crafting X requires A and B"  <- successful `craft X` steps
  binding "R is found at L"             <- successful `gather R` steps
  decor / count                          <- none by construction (DAG has no
                                            dependents) => credit 0
Reading (pre-registered in note 26 §4.2): if this row does NOT approach
oracle_weight (+0.386), the credit design is wrong — do not build the head.

Usage:
  PYTHONPATH=. python gpu/depcredit_go_nogo.py --in <s1_dir>
"""

from __future__ import annotations

import argparse
import pathlib
from collections import defaultdict

import numpy as np

from felt.fastweight import FastWeightMemory
from felt.baselines import _weights, _fact_key, _fact_val, _floor_corrected_probe
from game import World
from structmem_bench.metrics import average_precision
from structmem_bench.stats import paired_diff
from gpu.rollouts import read_jsonl_tolerant


def stream_with_depcredit(recs):
    """One world's episode stream (episode order = log order), fact instances
    with dependency credit computed from FUTURE successful uses."""
    # global step index across the world's stream
    events = []          # (gstep, kind, arg, td)
    facts = []           # dicts with emission gstep
    g = 0
    for rec in recs:
        for st in rec["trajectory"]:
            act = st["action"]
            td = max(0.0, float(st.get("td_signed", st["salience"])))
            ok_craft = act.startswith("craft") and "You craft" in st["obs"]
            ok_gather = act.startswith("gather") and "You gather" in st["obs"]
            arg = act.split(" ", 1)[1].strip() if " " in act else ""
            events.append((g, "craft" if ok_craft else
                           ("gather" if ok_gather else ""), arg, td))
            g += 1
        for fa in rec["facts"]:
            if fa["step"] < 1:
                continue
            facts.append({**fa, "gstep": g - len(rec["trajectory"]) + fa["step"] - 1,
                          "rec": rec})
    # per-use-target cumulative future TD
    use_td = defaultdict(list)          # ("craft", item) / ("gather", raw) -> [(gstep, td)]
    for gs, kind, arg, td in events:
        if kind and td > 0:
            use_td[(kind, arg)].append((gs, td))
    for f in facts:
        t = f["text"]
        if f["kind"] == "recipe":               # "crafting X requires A and B"
            item = t.split(" ")[1]
            key = ("craft", item)
        elif f["kind"] == "location":           # "R is found at L"
            raw = t.split(" ")[0]
            key = ("gather", raw)
        else:
            f["credit"] = 0.0
            continue
        f["credit"] = float(sum(td for gs, td in use_td.get(key, ())
                                if gs >= f["gstep"]))
    mx = max((f["credit"] for f in facts), default=1.0) or 1.0
    for f in facts:
        f["credit"] /= mx
    return facts


def eval_world(world, facts, policy, seed=0):
    K = np.stack([_fact_key(f["text"]) for f in facts])
    V = np.stack([_fact_val(f["text"]) for f in facts])
    S = np.array([f["credit"] for f in facts])
    structural = np.array([f["structural"] for f in facts], bool)
    acts = np.array(["x"] * len(facts))
    mem = FastWeightMemory(d_key=32, d_val=32, hidden=128, seed=seed)
    chunk = max(1, len(K) // 8)
    for i in range(0, len(K), chunk):
        sl = slice(i, i + chunk)
        sur = mem.surprise(K[sl], V[sl])
        labels = structural[sl] if policy == "oracle_weight" else None
        w = _weights(policy if policy != "felt_depcredit" else "felt_b12",
                     sur, S[sl], acts[sl], labels)
        mem.write_batch(K[sl], V[sl], w, steps=15)
    gist = world.structural_facts()
    g, _, _ = _floor_corrected_probe(mem, [f.text for f in gist],
                                     [f.kind for f in gist], 1)
    rng = np.random.default_rng(seed * 61 + 17)
    det = np.where(~structural)[0]
    if len(det) == 0:
        return None
    di = rng.choice(det, size=min(len(gist), len(det)), replace=False)
    d, _, _ = _floor_corrected_probe(mem, [facts[i]["text"] for i in di],
                                     [facts[i]["kind"] for i in di], 2)
    return {"dissociation": float(g.mean() - d.mean()),
            "ap_gist": average_precision(
                np.concatenate([g, d]),
                np.array([True] * len(g) + [False] * len(d)))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", required=True)
    a = ap.parse_args()
    by_world = defaultdict(list)
    for rec in read_jsonl_tolerant(pathlib.Path(a.in_dir) / "rollouts.jsonl"):
        by_world[rec["world"]].append(rec)

    POLS = ("uniform", "surprise_only", "felt_depcredit", "oracle_weight")
    results = defaultdict(list)
    for w_i, (wid, recs) in enumerate(sorted(by_world.items())):
        world = World.generate(wid, seed=recs[0]["world_seed"],
                               depth=recs[0].get("depth", 4))
        facts = stream_with_depcredit(recs)
        for pol in POLS:
            m = eval_world(world, facts, pol, seed=w_i)
            if m:
                results[pol].append(m)

    print(f"{'policy':<18}{'dissociation':>14}{'AP(gist)':>10}")
    for pol in POLS:
        rs = results[pol]
        print(f"{pol:<18}{np.mean([r['dissociation'] for r in rs]):>+14.3f}"
              f"{np.mean([r['ap_gist'] for r in rs]):>10.3f}")
    va = np.array([r["dissociation"] for r in results["felt_depcredit"]])
    vb = np.array([r["dissociation"] for r in results["oracle_weight"]])
    d = paired_diff(va, vb)
    print(f"\npaired felt_depcredit − oracle_weight: {d['mean']:+.3f} "
          f"(t={d['t']:.1f}, {'SIG' if d['sig'] else 'n.s.'})")
    print("[GO if felt_depcredit approaches oracle_weight; NO-GO otherwise]")


if __name__ == "__main__":
    main()
