"""Rohin's in-context induction ceiling: for each held-out pair, put the
MINIMAL raw-observation evidence that logically determines the answer in
context (perfect curation, no explicit structure), and ask. Upper bound
for any dream/think curation over raw memories.
Evidence for pair (a,b): observations proving a ~ a' (same class, via a
shared partner giving the same product family), b ~ b', and the observed
outcome of (a',b'). Pure lookup pairs excluded (we test induction).
  PYTHONPATH=. python alchemy/induction_ceiling.py --seed 2
"""
from __future__ import annotations
import argparse, json
import numpy as np
from alchemy.world import AlchemyWorld
from alchemy.env import generate_life, seen_pairs
from alchemy.player import ScriptedExplorer
from alchemy.evals import Q, parse_answer, score_levels

def obs_line(w, x, y):
    return w.combine_text(x, y)[2]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--eps", type=int, default=3840)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--out", default="alchemy/v2_out/induction_ceiling.json")
    a = ap.parse_args()
    w = AlchemyWorld(n_ingredients=1024, n_inert=128, seed=a.seed,
                     n_essences=96, max_tier=4, rho_fn=0.4)
    h = w.sample_holdout(0.3, seed=a.seed)
    life = generate_life(w, ScriptedExplorer(seed=a.seed), a.eps,
                         inv_size=6, seed=a.seed, holdout=h)
    seen = {tuple(sorted(p)) for p in seen_pairs(life)
            if all(x in w.ingredients for x in p)}
    # index observed product pairs by (ingredient, family)
    fam_obs = {}
    for x, y in seen:
        k, p = w.predict(x, y)
        if k == "product":
            fam = p.rsplit("-", 1)[0]
            fam_obs.setdefault(x, []).append((y, fam))
            fam_obs.setdefault(y, []).append((x, fam))
    def analog_for(t):
        """find a' seen with a shared-partner same-family proof vs t"""
        for p_, fam in fam_obs.get(t, []):
            for o, fam2 in fam_obs.get(p_, []):
                if o != t and fam2 == fam and w.essence_of(o) == w.essence_of(t):
                    return o, p_, fam
        return None
    rng = np.random.default_rng(9)
    hp = sorted(h); rng.shuffle(hp)
    cases = []
    for x, y in hp:
        if len(cases) >= a.n: break
        ax, ay = analog_for(x), analog_for(y)
        if not ax or not ay: continue
        x2, px, _ = ax; y2, py, _ = ay
        if tuple(sorted((x2, y2))) not in seen: continue
        ev = [obs_line(w, x, px), obs_line(w, x2, px),
              obs_line(w, y, py), obs_line(w, y2, py),
              obs_line(w, x2, y2)]
        cases.append(((x, y), ev))
    print(f"[ind] {len(cases)} evidence-complete held-out cases")
    from alchemy.backend import make_backend
    be = make_backend("vllm", a.model)
    prompts = [("Observations from your experience:\n" +
                "\n".join(f"- {l}" for l in ev) +
                "\nThese observations may reveal which ingredients behave "
                "alike. Reason briefly if needed, then give your final "
                "answer on its own line.\n\n" + Q.format(a=x, b=y))
               for (x, y), ev in cases]
    outs = []
    for i in range(0, len(prompts), 64):
        outs += be.generate(prompts[i:i+64], max_tokens=200)
    for o in outs[:5]:
        print("[ind-sample]", o[:160].replace("\n", " | "))
    ex = fa = kd = 0
    for ((x, y), _), o in zip(cases, outs):
        e, f, k = score_levels(parse_answer(o), w.predict(x, y))
        ex += e; fa += f; kd += k
    n = max(len(cases), 1)
    res = {"exact": ex/n, "family": fa/n, "kind": kd/n, "n": n}
    print(f"[ind] induction ceiling: {res}")
    json.dump(res, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
