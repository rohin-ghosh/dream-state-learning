"""S2 — train the FeltHead on REAL hidden states + the HOUR-12 KILL-SWITCH.

Loads S1's rollouts + state cache, trains the head by distillation on oracle
TD-salience, evaluates on held-out episodes, and prints the spec §5b run-1 gate:
    regret ≤ ~0.09 (3× mock's 0.03)  → PROCEED to S3
    regret ≥ 0.15                    → STOP: real states don't carry the salience
                                        signal (the KVP-vulnerability, note 23 §3)
                                        — try other cached layers first (--layer).

Usage:
  PYTHONPATH=. python gpu/train_head_real.py --in gpu_artifacts/s1 [--layer -1]
CPU-friendly: once states are cached this runs anywhere.
"""

from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np

from felt.head import FeltHead, all_budgets_regret, normalize_salience
from gpu.rollouts import text_key, LAYERS

MOCK_BASELINE = 0.03      # held-out regret with mock embeds (CPU tier)


def load_episodes(in_dir: pathlib.Path, layer: int):
    z = np.load(in_dir / "states.npz", allow_pickle=True)
    eps = []
    for line in open(in_dir / "rollouts.jsonl"):
        rec = json.loads(line)
        traj = rec["trajectory"]
        if len(traj) < 3:
            continue
        try:
            H = np.stack([z[f"{text_key(st['action'] + ' ' + st['obs'])}_l{layer}"]
                          for st in traj])
        except KeyError:
            continue                       # state cache incomplete for this episode
        eps.append({"H": H, "traj": traj, "rec": rec})
    return eps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", default="gpu_artifacts/s1")
    ap.add_argument("--layer", type=int, default=-1, choices=list(LAYERS))
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--out", default="gpu_artifacts/s2_head.npz")
    a = ap.parse_args()
    in_dir = pathlib.Path(a.in_dir)

    eps = load_episodes(in_dir, a.layer)
    assert len(eps) >= 50, f"too few complete episodes ({len(eps)}) — rerun S1 PASS B"
    rng = np.random.default_rng(0)
    idx = rng.permutation(len(eps))
    split = int(0.85 * len(eps))
    train, test = [eps[i] for i in idx[:split]], [eps[i] for i in idx[split:]]
    d_h = train[0]["H"].shape[1]
    print(f"[S2] layer={a.layer} d_h={d_h} train={len(train)} test={len(test)}")

    head = FeltHead(d_h=d_h, d_k=64, seed=0, lr=0.02)
    for ep_i in range(a.epochs):
        rng.shuffle(train)
        losses = [head.train_batch(e["H"], normalize_salience(e["traj"]))
                  for e in train]
        if ep_i % 5 == 0:
            print(f"  epoch {ep_i}: loss {np.mean(losses):.4f}")

    regrets, corrs = [], []
    for e in test:
        s = head.salience(e["H"])
        t = normalize_salience(e["traj"])
        regrets.append(all_budgets_regret(s, t))
        if s.std() > 0 and t.std() > 0:
            corrs.append(float(np.corrcoef(s, t)[0, 1]))
    regret = float(np.mean(regrets))
    corr = float(np.mean(corrs)) if corrs else float("nan")

    np.savez(a.out, Wk=head.Wk, q=head.q, b=head.b,
             layer=a.layer, regret=regret, corr=corr, d_h=d_h)
    print(f"\n[S2] held-out: all-budgets regret = {regret:.4f} | corr = {corr:.3f}")
    print(f"     mock baseline = {MOCK_BASELINE}")
    print("\n[HOUR-12 KILL-SWITCH — spec §5b]")
    if regret <= 3 * MOCK_BASELINE:
        print(f"  PROCEED → S3 (regret ≤ {3*MOCK_BASELINE:.2f}): real states carry the signal.")
    elif regret >= 0.15:
        print("  STOP: real hidden states do not carry the salience signal at this "
              "layer. Try --layer -4 / -8 (cached). If ALL layers ≥0.15, the "
              "architecture premise fails on this backbone — do NOT spend S3/S4; "
              "escalate model size once, then rethink.")
    else:
        print("  GRAY ZONE (between 0.09 and 0.15): try other layers; proceed to a "
              "REDUCED S3 (2 policies) and check whether ranking survives end-to-end.")


if __name__ == "__main__":
    main()
