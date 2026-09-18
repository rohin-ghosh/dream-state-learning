"""Outcome-shuffled control corpus: permute the outcome halves across
exemplars so action->outcome bindings are destroyed while marginals are
preserved. If the adapter's benefit needs true bindings, the shuffled
adapter should lose it (Codex's causal-control design).
  python -m organism_v6.shuffle_corpus --in <corpus.json> --out <corpus.json> --seed 0
"""
from __future__ import annotations
import argparse
import json
import random
import re

SPLIT = re.compile(r"( -> | scored | and measured: )")


def shuffle(corpus: list[str], seed: int) -> list[str]:
    rng = random.Random(seed)
    heads, seps, tails, idx = [], [], [], []
    for i, t in enumerate(corpus):
        parts = SPLIT.split(t, maxsplit=1)
        if len(parts) == 3:
            heads.append(parts[0])
            seps.append(parts[1])
            tails.append(parts[2])
            idx.append(i)
    perm = list(range(len(tails)))
    rng.shuffle(perm)
    out = list(corpus)
    for k, i in enumerate(idx):
        out[i] = heads[k] + seps[k] + tails[perm[k]]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    d = json.load(open(args.inp))
    d["corpus"] = shuffle(d["corpus"], args.seed)
    d["shuffled"] = True
    with open(args.out, "w") as f:
        json.dump(d, f, indent=1)
    print(f"SHUFFLED {len(d['corpus'])} texts (seed {args.seed})")


if __name__ == "__main__":
    main()
