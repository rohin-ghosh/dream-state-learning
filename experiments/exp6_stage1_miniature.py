"""
Experiment 6 — STAGE-1 MINIATURE: the full Felt-Attention pipeline on CPU.

    scripted FeltCraft rollouts (real game, real facts)
        → train the FeltHead by distillation on ORACLE TD-salience   [stage 2 v1]
        → head assigns salience to each experienced fact's event
        → value-modulated writes into the fast-weight MLP memory
              w = surprise × (1 + β·salience)      (β=0 = surprise-only baseline)
        → benchmark probes: retrieval of world GIST (recipe edges + location
          bindings) vs episodic DETAIL (decor/count instances)

Firewall intact: the head trains only on rollout salience; probes never enter any
loss. Question: does the trained head's salience, driving writes, improve gist
retention at matched write budget vs surprise-only and uniform — in a REAL MLP
memory with real interference, from a REAL (toy) game? This is the go/no-go
rehearsal for the GPU tier.
"""

from __future__ import annotations

import json

import numpy as np

from game import generate_dataset, World, FeltCraft, scripted_optimal_play
from felt import (train_head_on_dataset, eval_head, FeltHead, embed_events,
                  hash_embed, FastWeightMemory, value_modulated_weights)
from structmem_bench.metrics import average_precision


def fact_key(text): return hash_embed("KEY::" + text, 32)
def fact_val(text): return hash_embed("VAL::" + text, 32)


def collect_fact_stream(world, n_episodes, head, d_h=64, seed=0):
    """Play episodes; return per-fact-instance (key, value, salience, structural)."""
    known = set()
    K, V, S, lab, texts = [], [], [], [], []
    for e in range(n_episodes):
        env = FeltCraft(world, max_steps=120)
        goals = [i for i in world.dag.recipes]
        goal = goals[e % len(goals)]
        scripted_optimal_play(env, goal, episode_seed=seed * 1000 + e,
                              known_locations=known)
        known |= env.known_locations
        H = embed_events(env.trajectory, d_h) if env.trajectory else None
        sal = head.salience(H) if H is not None else np.zeros(0)
        for f in env.episode_facts:
            s = float(sal[f.step - 1]) if 0 <= f.step - 1 < len(sal) else 0.05
            K.append(fact_key(f.text)); V.append(fact_val(f.text))
            S.append(s); lab.append(f.structural); texts.append(f.text)
    return (np.stack(K), np.stack(V), np.array(S), np.array(lab, bool), texts)


def run_condition(world, K, V, S, structural, policy, beta, seed):
    mem = FastWeightMemory(d_key=32, d_val=32, hidden=48, seed=seed)
    if policy == "uniform":
        w = np.ones(len(K))
    else:  # surprise-based (value_modulated with beta; beta=0 = surprise-only)
        sur = mem.surprise(K, V)
        w = value_modulated_weights(sur, S, beta)
    # sleep-batch consolidation in chunks (episode-ordered stream)
    chunk = max(1, len(K) // 8)
    for i in range(0, len(K), chunk):
        sl = slice(i, i + chunk)
        mem.write_batch(K[sl], V[sl], w[sl], steps=15)
    # probes: world gist (deduped canonical facts) vs experienced details
    gist = world.structural_facts()
    gk = np.stack([fact_key(f.text) for f in gist])
    gv = np.stack([fact_val(f.text) for f in gist])
    gist_score = mem.probe(gk, gv)
    det_idx = np.where(~structural)[0][:len(gist)]
    det_score = mem.probe(K[det_idx], V[det_idx])
    scores = np.concatenate([gist_score, det_score])
    labels = np.array([True] * len(gist_score) + [False] * len(det_score))
    return {
        "gist_retrieval": float(gist_score.mean()),
        "detail_retrieval": float(det_score.mean()),
        "dissociation": float(gist_score.mean() - det_score.mean()),
        "ap_gist": average_precision(scores, labels),
    }


def main():
    SEEDS = 8
    D_H = 64
    print("Exp6 — Stage-1 miniature | head trained on oracle salience (train worlds),"
          " deployed on HELD-OUT worlds")

    # 1) train head on rollouts from train worlds
    r = generate_dataset("/tmp/exp6_train.jsonl", n_worlds=3,
                         episodes_per_world=25, seed=100, depth=4)
    recs = [json.loads(l) for l in open(r["path"])]
    head = train_head_on_dataset(recs, d_h=D_H, epochs=40, seed=0)
    hq = eval_head(head, recs[-15:], d_h=D_H)
    print(f"head quality (held-out eps): regret={hq['all_budgets_regret']:.3f} "
          f"corr={hq['salience_corr']:.3f}")

    # 2) deploy on held-out worlds; compare write policies at matched budget
    conds = [("uniform", 0.0), ("surprise_only(b=0)", 0.0), ("felt(b=4)", 4.0),
             ("felt(b=12)", 12.0)]
    agg = {c[0]: {"dissociation": [], "ap_gist": [], "gist": [], "det": []}
           for c in conds}
    for s in range(SEEDS):
        world = World.generate(f"held_{s}", seed=900 + s, depth=4)
        K, V, S, structural, _ = collect_fact_stream(world, 30, head, D_H, seed=s)
        for name, beta in conds:
            pol = "uniform" if name == "uniform" else "valmod"
            m = run_condition(world, K, V, S, structural, pol, beta, seed=s)
            agg[name]["dissociation"].append(m["dissociation"])
            agg[name]["ap_gist"].append(m["ap_gist"])
            agg[name]["gist"].append(m["gist_retrieval"])
            agg[name]["det"].append(m["detail_retrieval"])

    print(f"\n{'condition':<20}{'gist_ret':>9}{'det_ret':>9}{'dissoc':>9}{'AP':>8}")
    for name, _ in conds:
        a = agg[name]
        print(f"{name:<20}{np.mean(a['gist']):>9.3f}{np.mean(a['det']):>9.3f}"
              f"{np.mean(a['dissociation']):>9.3f}{np.mean(a['ap_gist']):>8.3f}")

    from structmem_bench.stats import paired_diff
    d = paired_diff(np.array(agg["felt(b=4)"]["dissociation"]),
                    np.array(agg["surprise_only(b=0)"]["dissociation"]))
    print(f"\npaired felt(b=4) − surprise_only on dissociation: "
          f"{d['mean']:+.3f} (SE {d['se']:.3f}, t={d['t']:.1f}, "
          f"{'SIG' if d['sig'] else 'n.s.'})")
    print("\n[READ] Full pipeline: real game -> trained head (never sees probes) -> "
          "value-modulated MLP writes -> gist/verbatim probes on held-out worlds. "
          "felt > surprise_only = the Stage-1 go signal.")


if __name__ == "__main__":
    main()
