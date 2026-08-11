"""Follow-up probes: (i) is felt_b12 just the step=-1 decor fallback? (ii) do
never-written controls also explain felt's numbers? (iii) felt with the fallback
neutralized.

Run: cd /Users/rohing/dream-state && PYTHONPATH=. python3 research_notes/probes/redteam4_followup.py
"""
from __future__ import annotations

import json
import numpy as np

from game import generate_dataset, World
from felt import (train_head_on_dataset, hash_embed, FastWeightMemory,
                  value_modulated_weights)
from structmem_bench.stats import paired_diff
from redteam4_probes import collect, run_mem, fact_key, fact_val, SEEDS, N_EP, D_H


def main():
    r = generate_dataset("/tmp/exp6_train.jsonl", n_worlds=3,
                         episodes_per_world=25, seed=100, depth=4)
    recs = [json.loads(l) for l in open(r["path"])]
    head = train_head_on_dataset(recs, d_h=D_H, epochs=40, seed=0)

    conds = ("felt_b12", "has_step", "felt_b12_fallback_fixed")
    agg = {c: {"dissoc": [], "ap": [], "gist": [], "det": []} for c in conds}
    wcorr = []
    fake_stats = {"real_gist": [], "fake_gist": [], "real_det": [], "fake_det": []}
    for s in range(SEEDS):
        world = World.generate(f"held_{s}", seed=900 + s, depth=4)
        K, V, S, structural, texts, actions, eps, kinds = collect(world, N_EP, head, seed=s)
        mem0 = FastWeightMemory(d_key=32, d_val=32, hidden=48, seed=s)
        sur = mem0.surprise(K, V)
        has_step = np.array([0.0 if a == "<setup>" else 1.0 for a in actions])

        w_felt = value_modulated_weights(sur, S, 12.0)
        w_step = sur * (1.0 + 12.0 * has_step)          # zero-info: "fact has a step"
        # felt but decor fallback replaced by the head's mean salience on real steps
        S_fix = S.copy()
        S_fix[has_step == 0] = S[has_step == 1].mean()
        w_fix = value_modulated_weights(sur, S_fix, 12.0)

        wcorr.append(float(np.corrcoef(w_felt, w_step)[0, 1]))
        for name, w in (("felt_b12", w_felt), ("has_step", w_step),
                        ("felt_b12_fallback_fixed", w_fix)):
            m = run_mem(world, K, V, w, structural, seed=s)
            for k in ("dissoc", "ap", "gist", "det"):
                agg[name][k].append(m[k])
            if name == "felt_b12":
                mem = m["mem"]
                gist = world.structural_facts()
                n_g = len(gist)
                fake_det = [f"site_{i%8} looked shimmering during episode {9000+i}"
                            for i in range(n_g)]
                fake_gist = [f"crafting z{i}_x requires q_{i} and z_{i}"
                             for i in range(n_g)]
                fk = np.stack([fact_key(t) for t in fake_det])
                fv = np.stack([fact_val(t) for t in fake_det])
                gk2 = np.stack([fact_key(t) for t in fake_gist])
                gv2 = np.stack([fact_val(t) for t in fake_gist])
                fake_stats["real_gist"].append(m["gist"])
                fake_stats["fake_gist"].append(float(mem.probe(gk2, gv2).mean()))
                fake_stats["real_det"].append(m["det"])
                fake_stats["fake_det"].append(float(mem.probe(fk, fv).mean()))

    print(f"{'condition':<26}{'gist':>8}{'det':>8}{'dissoc':>9}{'AP':>8}")
    for c in conds:
        a = agg[c]
        print(f"{c:<26}{np.mean(a['gist']):>8.3f}{np.mean(a['det']):>8.3f}"
              f"{np.mean(a['dissoc']):>9.3f}{np.mean(a['ap']):>8.3f}")
    print(f"\ncorr(felt_b12 weights, has_step weights): mean={np.mean(wcorr):.3f} "
          f"min={np.min(wcorr):.3f}")
    d = paired_diff(np.array(agg["has_step"]["dissoc"]),
                    np.array(agg["felt_b12"]["dissoc"]))
    print(f"paired has_step - felt_b12 dissociation: {d['mean']:+.3f} "
          f"(SE {d['se']:.3f}, t={d['t']:.1f})")
    d = paired_diff(np.array(agg["felt_b12_fallback_fixed"]["dissoc"]),
                    np.array(agg["felt_b12"]["dissoc"]))
    print(f"paired fallback_fixed - felt_b12 dissociation: {d['mean']:+.3f} "
          f"(SE {d['se']:.3f}, t={d['t']:.1f})")
    print(f"\nfelt_b12 memory, never-written controls (8 seeds):")
    print(f"  real gist={np.mean(fake_stats['real_gist']):.3f}  "
          f"fake gist={np.mean(fake_stats['fake_gist']):.3f}")
    print(f"  real det ={np.mean(fake_stats['real_det']):.3f}  "
          f"fake det ={np.mean(fake_stats['fake_det']):.3f}")


if __name__ == "__main__":
    main()
