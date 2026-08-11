"""Per-kind probe-score decomposition under uniform writes (attack 2 mechanism).

Run: cd /Users/rohing/dream-state/research_notes/probes &&
     PYTHONPATH=/Users/rohing/dream-state:. python3 redteam4_perkind.py
"""
import json
import numpy as np

from game import generate_dataset, World
from felt import train_head_on_dataset, FastWeightMemory
from redteam4_probes import collect, run_mem, fact_key, fact_val, SEEDS, N_EP, D_H


def main():
    r = generate_dataset("/tmp/exp6_train.jsonl", n_worlds=3,
                         episodes_per_world=25, seed=100, depth=4)
    recs = [json.loads(l) for l in open(r["path"])]
    head = train_head_on_dataset(recs, d_h=D_H, epochs=40, seed=0)

    rows = {k: [] for k in ("recipe", "location", "decor(probed)", "count(probed)",
                            "fake_decor", "fake_recipe")}
    for s in range(SEEDS):
        world = World.generate(f"held_{s}", seed=900 + s, depth=4)
        K, V, S, structural, texts, actions, eps, kinds = collect(world, N_EP, head, seed=s)
        m = run_mem(world, K, V, np.ones(len(K)), structural, seed=s)
        mem = m["mem"]
        gist = world.structural_facts()
        n_g = len(gist)
        det_idx = np.where(~structural)[0][:n_g]
        for kindname, mask_items in (
            ("recipe", [f.text for f in gist if f.kind == "recipe"]),
            ("location", [f.text for f in gist if f.kind == "location"]),
        ):
            kk = np.stack([fact_key(t) for t in mask_items])
            vv = np.stack([fact_val(t) for t in mask_items])
            rows[kindname].append(float(mem.probe(kk, vv).mean()))
        for kindname in ("decor", "count"):
            idx = [i for i in det_idx if kinds[i] == kindname]
            if idx:
                rows[f"{kindname}(probed)"].append(
                    float(mem.probe(K[idx], V[idx]).mean()))
        fake_d = [f"site_{i%8} looked shimmering during episode {9000+i}"
                  for i in range(n_g)]
        fake_g = [f"crafting z{i}_x requires q_{i} and z_{i}" for i in range(n_g)]
        rows["fake_decor"].append(float(mem.probe(
            np.stack([fact_key(t) for t in fake_d]),
            np.stack([fact_val(t) for t in fake_d])).mean()))
        rows["fake_recipe"].append(float(mem.probe(
            np.stack([fact_key(t) for t in fake_g]),
            np.stack([fact_val(t) for t in fake_g])).mean()))
    print("UNIFORM writes, per-kind mean probe cosine (8 seeds):")
    for k, v in rows.items():
        print(f"  {k:<15} {np.mean(v):.3f}")


if __name__ == "__main__":
    main()
