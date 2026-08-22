"""Injection micro-benchmark: can we store N facts in a LoRA AT ALL?

Takes N real facts from a seed's world, builds the augmented mini-corpus,
trains with per-fact touch budget T (not epochs), evals recall + a
held-out control. Sweeps (lr, T, rank) cheaply. THE instrument that sets
the consolidation recipe before any full run.

  PYTHONPATH=. python alchemy/micro_inject.py --facts 50 \
      --model Qwen/Qwen2.5-7B-Instruct
"""
from __future__ import annotations
import argparse, json, itertools
import numpy as np
from alchemy.world import AlchemyWorld
from alchemy.dreamer import PARA_PRODUCT, PARA_NOTHING, PARA_RUIN
from alchemy.evals import Q, parse_answer

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", type=int, default=50)
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--grid", default="1e-4:200:16,2e-4:200:16,2e-4:600:16,5e-4:200:16,2e-4:200:64")
    ap.add_argument("--out", default="alchemy/v2_out/micro_inject.json")
    a = ap.parse_args()
    w = AlchemyWorld(n_ingredients=1024, n_inert=128, seed=0,
                     n_essences=96, max_tier=4, rho_fn=0.4)
    rng = np.random.default_rng(7)
    pairs = w.base_pairs()
    idx = rng.permutation(len(pairs))
    chosen, control = [], []
    for i in idx:
        a_, b_ = pairs[i]
        k, p = w.predict(a_, b_)
        (chosen if len(chosen) < a.facts else control).append((a_, b_, k, p))
        if len(control) >= 30: break
    corpus = []
    for x, y, k, p in chosen:
        tpl = PARA_PRODUCT if k == "product" else PARA_RUIN if k == "ruin" else PARA_NOTHING
        for t in tpl:
            for u, v in ((x, y), (y, x)):
                corpus.append(t.format(a=u, b=v, p=p))
    print(f"[micro] {len(chosen)} facts -> {len(corpus)} lines")
    from alchemy.lora_mem import load_base, train_lora, read
    import torch
    results = {}
    for spec in a.grid.split(","):
        lr, touches, rank = spec.split(":")
        lr, touches, rank = float(lr), int(touches), int(rank)
        # epochs so each fact's ~12 lines yield `touches` gradient contributions
        lines_per_fact = len(corpus) / len(chosen)
        epochs = max(1, int(touches / lines_per_fact))
        base, tok = load_base(a.model)
        m = train_lora(base, tok, list(corpus), rank=rank, epochs=epochs,
                       lr=lr, log=lambda s: None)
        def acc(fs):
            good = 0
            for x, y, k, p in fs:
                out = read(m, tok, Q.format(a=x, b=y))
                pk, pn = parse_answer(out)
                good += int(pk == k and (k != "product" or (pn or "") == p.lower()))
            return good / len(fs)
        r = {"train_recall": acc(chosen), "control_confab":
             sum(parse_answer(read(m, tok, Q.format(a=x, b=y)))[0] != "unknown"
                 for x, y, k, p in control) / len(control),
             "epochs": epochs}
        results[spec] = r
        print(f"[micro] lr={lr} touches={touches} rank={rank} -> {r}")
        del m, base; torch.cuda.empty_cache()
    json.dump(results, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
