"""G2d: read-accuracy decomposition — score EACH read type against
ground truth (membership F1, rule-read accuracy), then end-to-end.
Uses the g2c write-as-reads adapter.
"""
from __future__ import annotations
import json, pathlib
import numpy as np
from alchemy.mini import MiniWorld
from alchemy.evals import parse_answer
from alchemy.backend import make_backend

def main():
    model = "Qwen/Qwen2.5-7B-Instruct"
    w = MiniWorld(seed=0)
    L = str(pathlib.Path("alchemy/v2_out/g2c_lora").resolve())
    be = make_backend("vllm", model, enable_lora=True, max_lora_rank=64)
    # ---- membership reads, all 24 ingredients
    qs = [f"Q: {n} belongs to the same behavior group as: A:" for n in w.ingredients]
    outs = []
    for i in range(0, len(qs), 24):
        outs += be.generate(qs[i:i+24], max_tokens=50, lora_path=L)
    f1s = []
    for n, o in zip(w.ingredients, outs):
        truth = {x for x in w.ingredients if x != n and w.type_of[x] == w.type_of[n]}
        said = {x for x in w.ingredients if x != n and x in o.lower()}
        tp = len(said & truth)
        p = tp / len(said) if said else 0
        r = tp / len(truth)
        f1s.append(2*p*r/(p+r) if (p+r) else 0.0)
    mem_f1 = round(float(np.mean(f1s)), 3)
    print(f"[g2d] membership-read F1: {mem_f1}", flush=True)
    # ---- rule reads on 60 random pairs
    rng = np.random.default_rng(2)
    import itertools
    pairs = list(itertools.combinations(w.ingredients, 2))
    rng.shuffle(pairs)
    pairs = pairs[:60]
    qs = [f"Q: Do the groups of {a} and {b} react? A:" for a, b in pairs]
    outs = []
    for i in range(0, len(qs), 30):
        outs += be.generate(qs[i:i+30], max_tokens=40, lora_path=L)
    ok = 0
    for (a, b), o in zip(pairs, outs):
        k = w.predict(a, b)[0]
        ol = o.lower()
        said = ("product" if ("product" in ol or "react to make" in ol)
                else "ruin" if "ruin" in ol else "nothing" if ("nothing" in ol or "inert" in ol or "not react" in ol or "non-reactive" in ol)
                else "?")
        ok += said == k
    rule_acc = round(ok/len(pairs), 3)
    print(f"[g2d] rule-read accuracy: {rule_acc}", flush=True)
    for o in outs[:4]:
        print("[g2d-sample]", o[:90].replace(chr(10), " | "), flush=True)
    json.dump({"membership_f1": mem_f1, "rule_acc": rule_acc},
              open("alchemy/v2_out/mini_g2d.json", "w"))
    print("[g2d] DONE", flush=True)

if __name__ == "__main__":
    main()
