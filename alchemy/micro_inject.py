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
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--unknown-lines", type=int, default=60)
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
    # UNKNOWN slice so calibrated abstention CAN exist in-weights —
    # without it the confab control is a canary that cannot fail
    un = []
    for i in idx[::-1]:
        if len(un) >= a.unknown_lines: break
        x, y = pairs[i]
        if (x, y) in [(c[0], c[1]) for c in chosen + control]: continue
        un.append(f"Q: What happens when you combine {x} and {y}? A: UNKNOWN")
    corpus += un
    print(f"[micro] {len(chosen)} facts -> {len(corpus)} lines "
          f"(incl {len(un)} UNKNOWN)")
    from alchemy.lora_mem import load_base, train_lora, read
    import torch
    results = {}
    for spec in a.grid.split(","):
        lr, touches, rank = spec.split(":")
        lr, touches, rank = float(lr), int(touches), int(rank)
        # epochs so each fact's ~12 lines yield `touches` gradient contributions
        lines_per_fact = len(corpus) / len(chosen)
        epochs = max(1, int(touches / lines_per_fact))
        recs, confs, absts = [], [], []
        for sd in range(a.seeds):
            base, tok = load_base(a.model)
            corp = list(corpus)
            np.random.default_rng(sd).shuffle(corp)
            m = train_lora(base, tok, corp, rank=rank, epochs=epochs,
                           lr=lr, log=lambda s: None)
            good = 0
            for x, y, k, p in chosen:
                pk, pn = parse_answer(read(m, tok, Q.format(a=x, b=y)))
                good += int(pk == k and (k != "product" or (pn or "") == p.lower()))
            recs.append(good / len(chosen))
            preds = [parse_answer(read(m, tok, Q.format(a=x, b=y)))[0]
                     for x, y, k, p in control]
            absts.append(sum(p == "unknown" for p in preds) / len(preds))
            confs.append(sum(p != "unknown" for p in preds) / len(preds))
            del m, base; torch.cuda.empty_cache()
        r = {"train_recall": float(np.mean(recs)),
             "recall_std": float(np.std(recs)),
             "control_abstain": float(np.mean(absts)),
             "control_confab": float(np.mean(confs)),
             "epochs": epochs, "seeds": a.seeds}
        results[spec] = r
        print(f"[micro] lr={lr} touches={touches} rank={rank} -> {r}")
    json.dump(results, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
