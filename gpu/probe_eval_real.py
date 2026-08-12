"""S3 — probe-tier evaluation with the REAL-state head (fixed-trajectory replay).

Consumes S1's rollouts + state cache + S2's trained head. For each world in the
log: per-fact salience from the head over REAL hidden states, then the full write-
policy zoo (incl. keyword_gate canary + oracle_weight ceiling) into the fast-weight
memory with floor-corrected probes. Paired stats per world. CPU-runnable once the
state cache exists — costs nothing extra on GPU time.

Usage:
  PYTHONPATH=. python gpu/probe_eval_real.py --in gpu_artifacts/s1 \
      --head gpu_artifacts/s2_head.npz
"""

from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict

import numpy as np

from felt.head import FeltHead
from felt.fastweight import FastWeightMemory
from felt.baselines import (_weights, _fact_key, _fact_val,
                            _floor_corrected_probe)
from game import World
from structmem_bench.metrics import average_precision
from structmem_bench.stats import paired_diff
from gpu.rollouts import text_key

POLICIES = ("uniform", "random_write", "surprise_only", "dmem_style",
            "keyword_gate", "felt_b4", "felt_b12", "oracle_weight")


def load_head(path):
    z = np.load(path)
    h = FeltHead(d_h=int(z["d_h"]), d_k=z["Wk"].shape[1])
    h.Wk, h.q, h.b = z["Wk"], z["q"], float(z["b"])
    h_scale = float(z["h_scale"]) if "h_scale" in z.files else 1.0
    return h, int(z["layer"]), h_scale


def build_world_stream(recs, states, head, layer, h_scale=1.0,
                       states_mode="text", salience_npz=None):
    """K/V/S/labels/acts/kinds/texts for one world's episode stream, salience
    from the REAL-state head (or a precomputed per-episode salience file)."""
    K, V, S, lab, acts, kinds, texts = [], [], [], [], [], [], []
    for rec in recs:
        traj = rec["trajectory"]
        if salience_npz is not None:
            if rec["episode_uid"] not in salience_npz.files:
                continue
            sal = salience_npz[rec["episode_uid"]]
            if len(sal) != len(traj):
                continue
        else:
            try:
                if states_mode == "ctx":
                    H = np.stack([states[f"{rec['episode_uid']}_s{i}_l{layer}"]
                                  for i in range(len(traj))]
                                 ).astype(np.float32) / h_scale
                else:
                    H = np.stack([states[f"{text_key(st['action'] + ' ' + st['obs'])}_l{layer}"]
                                  for st in traj]) / h_scale  # P0-1
            except KeyError:
                continue
            sal = head.salience(H)
        for fa in rec["facts"]:
            if fa["step"] < 1 or fa["step"] - 1 >= len(sal):
                continue
            K.append(_fact_key(fa["text"])); V.append(_fact_val(fa["text"]))
            S.append(float(sal[fa["step"] - 1])); lab.append(fa["structural"])
            acts.append(traj[fa["step"] - 1]["action"].split(" ")[0])
            kinds.append(fa["kind"]); texts.append(fa["text"])
    if not K:
        return None
    return {"K": np.stack(K), "V": np.stack(V), "S": np.array(S),
            "structural": np.array(lab, bool), "acts": np.array(acts),
            "kinds": np.array(kinds), "texts": texts}


def eval_policy(world, st, policy, seed=0):
    K, V, S = st["K"], st["V"], st["S"]
    structural, acts = st["structural"], st["acts"]
    mem = FastWeightMemory(d_key=32, d_val=32, hidden=128, seed=seed)
    chunk = max(1, len(K) // 8)
    for i in range(0, len(K), chunk):
        sl = slice(i, i + chunk)
        sur = mem.surprise(K[sl], V[sl])
        labels = structural[sl] if policy == "oracle_weight" else None
        w = _weights(policy, sur, S[sl], acts[sl], labels)
        mem.write_batch(K[sl], V[sl], w, steps=15)
    gist = world.structural_facts()
    g, _, gf = _floor_corrected_probe(mem, [f.text for f in gist],
                                      [f.kind for f in gist], 1)
    rng = np.random.default_rng(seed * 61 + 17)
    det_pool = np.where(~structural)[0]
    if len(det_pool) == 0:
        return None
    di = rng.choice(det_pool, size=min(len(gist), len(det_pool)), replace=False)
    d, _, df = _floor_corrected_probe(mem, [st["texts"][i] for i in di],
                                      [st["kinds"][i] for i in di], 2)
    return {"dissociation": float(g.mean() - d.mean()),
            "ap_gist": average_precision(
                np.concatenate([g, d]),
                np.array([True] * len(g) + [False] * len(d)))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", default="gpu_artifacts/s1")
    ap.add_argument("--head", default="gpu_artifacts/s2_head.npz")
    ap.add_argument("--out", default="gpu_artifacts/s3_probe.json")
    ap.add_argument("--states", choices=("text", "ctx"), default="text",
                    help="MUST match the cache the head was trained on")
    ap.add_argument("--salience-npz", default="",
                    help="precomputed per-episode salience (skips head+states)")
    a = ap.parse_args()
    in_dir = pathlib.Path(a.in_dir)

    sal_npz = np.load(a.salience_npz) if a.salience_npz else None
    if sal_npz is not None:
        head, layer, h_scale, states = None, 0, 1.0, None
    else:
        head, layer, h_scale = load_head(a.head)
        fname = "states_ctx.npz" if a.states == "ctx" else "states.npz"
        states = np.load(in_dir / fname, allow_pickle=True)

    from gpu.rollouts import read_jsonl_tolerant
    by_world = defaultdict(list)
    for rec in read_jsonl_tolerant(in_dir / "rollouts.jsonl"):
        by_world[rec["world"]].append(rec)
    results = defaultdict(list)
    for w_i, (wid, recs) in enumerate(sorted(by_world.items())):
        # regenerate the SAME world from the LOGGED seed/depth (never guess)
        world = World.generate(wid, seed=recs[0]["world_seed"],
                               depth=recs[0].get("depth", 4))
        st = build_world_stream(recs, states, head, layer, h_scale,
                                states_mode=a.states, salience_npz=sal_npz)
        if st is None:
            continue
        for pol in POLICIES:
            m = eval_policy(world, st, pol, seed=w_i)
            if m:
                results[pol].append(m)

    print(f"\n{'policy':<15}{'dissociation':>14}{'AP(gist)':>10}")
    summary = {}
    for pol in POLICIES:
        rs = results[pol]
        dd = float(np.mean([r["dissociation"] for r in rs]))
        aa = float(np.mean([r["ap_gist"] for r in rs]))
        summary[pol] = {"dissociation": dd, "ap_gist": aa, "n_worlds": len(rs)}
        print(f"{pol:<15}{dd:>+14.3f}{aa:>10.3f}")
    # the two decisive comparisons
    for a_, b_ in (("felt_b12", "keyword_gate"), ("felt_b12", "surprise_only")):
        va = np.array([r["dissociation"] for r in results[a_]])
        vb = np.array([r["dissociation"] for r in results[b_]])
        d = paired_diff(va, vb)
        print(f"\npaired {a_} − {b_}: {d['mean']:+.3f} (t={d['t']:.1f}, "
              f"{'SIG' if d['sig'] else 'n.s.'})")
    pathlib.Path(a.out).write_text(json.dumps(summary, indent=1))
    print(f"\n[READ] felt must beat keyword_gate for the head to mean anything "
          f"beyond action-type; oracle_weight is the ceiling. Saved: {a.out}")


if __name__ == "__main__":
    main()
