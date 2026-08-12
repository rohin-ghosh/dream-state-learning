"""Capacity probe (GRAY-protocol diagnostic): can a BIGGER probe read more
salience out of the ctx-states than the linear-ish FeltHead?

Trains a 2-layer MLP (torch) on the exact S2 split/protocol and reports
held-out all-budgets regret + corr, next to the FeltHead's numbers and the
0.122 text-information floor. Interpretations, pre-registered:
  MLP << head, dives under floor  -> signal is rich + nonlinear; a bigger felt
                                     head is licensed (finding, not failure)
  MLP ~= head                     -> head already extracts what's there; the
                                     remaining gap to 0 is context/label noise
Usage (node):
  PYTHONPATH=. python gpu/probe_capacity.py --in gpu_artifacts/s1 --layer -8
"""

from __future__ import annotations

import argparse
import pathlib

import numpy as np

from felt.head import all_budgets_regret
from gpu.train_head_real import load_episodes
from felt.head import normalize_salience


def main():
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", default="gpu_artifacts/s1")
    ap.add_argument("--layer", type=int, default=-8)
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--states", choices=("text", "ctx"), default="ctx")
    a = ap.parse_args()

    eps = load_episodes(pathlib.Path(a.in_dir), a.layer, states=a.states)
    rng = np.random.default_rng(0)                 # SAME split as train_head_real
    idx = rng.permutation(len(eps))
    split = int(0.85 * len(eps))
    train, test = [eps[i] for i in idx[:split]], [eps[i] for i in idx[split:]]
    h_scale = float(np.mean([np.linalg.norm(e["H"], axis=1).mean() for e in train]))

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    d_h = train[0]["H"].shape[1]
    net = torch.nn.Sequential(
        torch.nn.Linear(d_h, a.hidden), torch.nn.GELU(),
        torch.nn.Linear(a.hidden, 1)).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)

    X = torch.tensor(np.concatenate([e["H"] for e in train]) / h_scale,
                     dtype=torch.float32, device=dev)
    y = torch.tensor(np.concatenate([normalize_salience(e["traj"])
                                     for e in train]),
                     dtype=torch.float32, device=dev)
    n = len(X)
    print(f"[cap] layer={a.layer} states={a.states} train_events={n} "
          f"hidden={a.hidden} dev={dev}")
    for ep_i in range(a.epochs):
        perm = torch.randperm(n, device=dev)
        tot = 0.0
        for i in range(0, n, 4096):
            sl = perm[i:i + 4096]
            opt.zero_grad()
            p = torch.sigmoid(net(X[sl]).squeeze(-1))
            loss = torch.nn.functional.mse_loss(p, y[sl])
            loss.backward(); opt.step()
            tot += float(loss) * len(sl)
        if ep_i % 3 == 0:
            print(f"  epoch {ep_i}: loss {tot / n:.4f}")

    net.eval()
    regrets, corrs = [], []
    with torch.no_grad():
        for e in test:
            h = torch.tensor(e["H"] / h_scale, dtype=torch.float32, device=dev)
            s = torch.sigmoid(net(h).squeeze(-1)).cpu().numpy()
            t = normalize_salience(e["traj"])
            regrets.append(all_budgets_regret(s, t))
            if s.std() > 0 and t.std() > 0:
                corrs.append(float(np.corrcoef(s, t)[0, 1]))
    print(f"\n[CAPACITY PROBE] held-out regret = {float(np.mean(regrets)):.4f} "
          f"| corr = {float(np.mean(corrs)):.3f}")
    print("  reference: FeltHead ctx l-8 = 0.125 / 0.636 | text floor = 0.122")


if __name__ == "__main__":
    main()
