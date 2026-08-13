"""S2-fact — train fact-level salience heads on fact-in-context states
(note 26, approved). Target: BINARY dependency credit ("will this proposition
ever be load-bearing?"), computed from gameplay only (felt/depcredit.py).

Trains BOTH head forms on the same episode-split and reports each:
  linear  — attention-shaped scorer (v1 form, one bend short?)
  mlp     — one hidden layer (capacity-probe form)
Metrics: held-out AUC (binary target) + within-episode ranking regret.
Dumps per-fact salience for S3 (--dump-salience, keys '{uid}_f{j}').

Usage (node):
  PYTHONPATH=. python gpu/train_head_fact.py --in gpu_artifacts/s1 --layer -8 \
      --dump-salience gpu_artifacts/salience_fact.npz
"""

from __future__ import annotations

import argparse
import pathlib
from collections import defaultdict

import numpy as np

from felt.depcredit import world_fact_credit
from felt.head import all_budgets_regret
from gpu.rollouts import read_jsonl_tolerant


def load_fact_dataset(in_dir: pathlib.Path, layer: int):
    z = np.load(in_dir / "states_fact.npz", allow_pickle=True)
    by_world = defaultdict(list)
    recs_all = read_jsonl_tolerant(in_dir / "rollouts.jsonl")
    for rec in recs_all:
        by_world[rec["world"]].append(rec)
    credit = {}
    for recs in by_world.values():
        credit.update(world_fact_credit(recs, binary=True))
    eps = []
    for rec in recs_all:
        keys, H, y = [], [], []
        for j, fa in enumerate(rec["facts"]):
            k = f"{rec['episode_uid']}_f{j}"
            if (rec["episode_uid"], j) not in credit:
                continue
            if f"{k}_l{layer}" not in z.files:
                continue
            keys.append(k)
            H.append(z[f"{k}_l{layer}"].astype(np.float32))
            y.append(credit[(rec["episode_uid"], j)])
        if len(H) >= 3:
            eps.append({"keys": keys, "H": np.stack(H),
                        "y": np.array(y, np.float32), "world": rec["world"]})
    return eps


def train_eval(eps, hidden: int, epochs: int, seed: int = 0):
    import torch
    rng = np.random.default_rng(0)                # SAME split protocol as S2
    idx = rng.permutation(len(eps))
    split = int(0.85 * len(eps))
    train = [eps[i] for i in idx[:split]]
    test = [eps[i] for i in idx[split:]]
    h_scale = float(np.mean([np.linalg.norm(e["H"], axis=1).mean()
                             for e in train]))
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    d_h = train[0]["H"].shape[1]
    torch.manual_seed(seed)
    if hidden > 0:
        net = torch.nn.Sequential(
            torch.nn.Linear(d_h, hidden), torch.nn.GELU(),
            torch.nn.Linear(hidden, 1)).to(dev)
    else:
        net = torch.nn.Linear(d_h, 1).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    X = torch.tensor(np.concatenate([e["H"] for e in train]) / h_scale,
                     dtype=torch.float32, device=dev)
    Y = torch.tensor(np.concatenate([e["y"] for e in train]),
                     dtype=torch.float32, device=dev)
    n = len(X)
    for _ in range(epochs):
        perm = torch.randperm(n, device=dev)
        for i in range(0, n, 4096):
            sl = perm[i:i + 4096]
            opt.zero_grad()
            loss = torch.nn.functional.binary_cross_entropy_with_logits(
                net(X[sl]).squeeze(-1), Y[sl])
            loss.backward(); opt.step()
    net.eval()
    # held-out: AUC over all test facts + per-episode ranking regret
    scores, targets, regrets = [], [], []
    with torch.no_grad():
        for e in test:
            h = torch.tensor(e["H"] / h_scale, dtype=torch.float32, device=dev)
            s = torch.sigmoid(net(h).squeeze(-1)).cpu().numpy()
            scores.append(s); targets.append(e["y"])
            if e["y"].std() > 0:
                regrets.append(all_budgets_regret(s, e["y"]))
    s = np.concatenate(scores); t = np.concatenate(targets)
    order = np.argsort(s)
    ranks = np.empty(len(s)); ranks[order] = np.arange(len(s))
    n_pos, n_neg = int(t.sum()), int((1 - t).sum())
    auc = ((ranks[t > 0.5].sum() - n_pos * (n_pos - 1) / 2)
           / max(1, n_pos * n_neg))
    return {"auc": float(auc), "regret": float(np.mean(regrets)),
            "net": net, "h_scale": h_scale, "dev": dev}


def main():
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", default="gpu_artifacts/s1")
    ap.add_argument("--layer", type=int, default=-8)
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--dump-salience", default="")
    ap.add_argument("--exclude-worlds", default="",
                    help="comma-sep worlds EXCLUDED from training (cross-world "
                         "robustness); salience still dumped for ALL episodes")
    ap.add_argument("--eval-in", default="",
                    help="CROSS-CONFIG: after training on --in, evaluate on "
                         "this dir's fact states (frozen head, unseen config); "
                         "--dump-salience then dumps for the EVAL dir")
    a = ap.parse_args()
    in_dir = pathlib.Path(a.in_dir)

    all_eps = load_fact_dataset(in_dir, a.layer)
    excl = set(w for w in a.exclude_worlds.split(",") if w)
    eps = [e for e in all_eps if e["world"] not in excl]
    if excl:
        print(f"[S2-fact] CROSS-WORLD: training without {sorted(excl)} "
              f"({len(all_eps) - len(eps)} episodes held out)")
    n_facts = sum(len(e["y"]) for e in eps)
    pos = sum(float(e["y"].sum()) for e in eps)
    print(f"[S2-fact] layer={a.layer} episodes={len(eps)} facts={n_facts} "
          f"positive={pos/n_facts:.3f}")

    best = None
    for name, hidden in (("linear(attn-form)", 0), ("mlp(h256)", 256)):
        r = train_eval(eps, hidden, a.epochs)
        print(f"  {name}: held-out AUC = {r['auc']:.4f} | "
              f"ranking regret = {r['regret']:.4f}")
        if best is None or r["auc"] > best[1]["auc"]:
            best = (name, r)
    print(f"[S2-fact] best: {best[0]}")

    if a.eval_in:
        # frozen-head evaluation on an UNSEEN generator config
        ev = load_fact_dataset(pathlib.Path(a.eval_in), a.layer)
        net, h_scale, dev = best[1]["net"], best[1]["h_scale"], best[1]["dev"]
        scores, targets, regrets = [], [], []
        with torch.no_grad():
            for e in ev:
                h = torch.tensor(e["H"] / h_scale, dtype=torch.float32,
                                 device=dev)
                s = torch.sigmoid(net(h).squeeze(-1)).cpu().numpy()
                scores.append(s); targets.append(e["y"])
                if e["y"].std() > 0:
                    regrets.append(all_budgets_regret(s, e["y"]))
        s = np.concatenate(scores); t = np.concatenate(targets)
        order = np.argsort(s)
        ranks = np.empty(len(s)); ranks[order] = np.arange(len(s))
        n_pos, n_neg = int(t.sum()), int((1 - t).sum())
        auc = ((ranks[t > 0.5].sum() - n_pos * (n_pos - 1) / 2)
               / max(1, n_pos * n_neg))
        print(f"[CROSS-CONFIG] frozen head on {a.eval_in}: "
              f"AUC = {auc:.4f} | regret = {float(np.mean(regrets)):.4f} "
              f"(episodes={len(ev)}, facts={len(s)})")
        all_eps = ev              # salience dump targets the eval config

    if a.dump_salience:
        net, h_scale, dev = best[1]["net"], best[1]["h_scale"], best[1]["dev"]
        out = {}
        with torch.no_grad():
            for e in all_eps:
                h = torch.tensor(e["H"] / h_scale, dtype=torch.float32,
                                 device=dev)
                s = torch.sigmoid(net(h).squeeze(-1)).cpu().numpy()
                for k, v in zip(e["keys"], s):
                    out[k] = np.float32(v)
        np.savez(a.dump_salience, **out)
        print(f"  dumped {len(out)} fact saliences -> {a.dump_salience}")


if __name__ == "__main__":
    main()
