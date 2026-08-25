"""Rohin's bar test: with COMPOSITIONAL product naming (boy+toy=btoy
style), does evidence-given induction hit 80-90%? Synthetic one-hop
cases; morphological rule = first consonant cluster of A + full B.
  PYTHONPATH=. python alchemy/naming_probe.py
"""
from __future__ import annotations
import json
import numpy as np
from alchemy.evals import parse_answer

SYL_A = ["vex","mor","tes","gal","rin","dru","kel","sab","fen","lur"]
SYL_B = ["il","run","sic","eth","ock","ane","ura","esk","ov","ith"]

def blend(a, b):
    return a[0] + b   # first letter of A + full name of B

def main():
    rng = np.random.default_rng(4)
    names = [x + y for x in SYL_A for y in SYL_B]
    rng.shuffle(names)
    cases = []
    for i in range(300):
        a, b, a2, b2, p = [names[(5*i + j) % len(names)] for j in range(5)]
        ev = [f"You combine {a} and {p}. They fuse into {blend(a, p)}.",
              f"You combine {a2} and {p}. They fuse into {blend(a2, p)}.",
              f"You combine {a2} and {b2}. They fuse into {blend(a2, b2)}.",
              f"You combine {b} and {p}. They fuse into {blend(b, p)}."]
        cases.append(((a, b), ev, blend(a, b)))
    from alchemy.backend import make_backend
    be = make_backend("vllm", "Qwen/Qwen2.5-7B-Instruct")
    prompts = [("Observations from your experience:\n" +
                "\n".join(f"- {l}" for l in ev) +
                "\nUNKNOWN is not allowed — commit to your best answer. "
                "Reason briefly, then give your final answer on its own "
                f"line.\n\nWhat happens when you combine {a} and {b}? "
                "Answer with exactly one of: PRODUCT <name> | NOTHING | RUIN.")
               for (a, b), ev, _ in cases]
    outs = []
    for i in range(0, len(prompts), 64):
        outs += be.generate(prompts[i:i+64], max_tokens=300)
    for o in outs[:3]:
        print("[probe-sample]", o[:140].replace("\n", " | "))
    ok = 0
    for (pair, ev, truth), o in zip(cases, outs):
        pred = parse_answer(o)
        ok += int(pred[0] == "product" and (pred[1] or "") == truth)
    print(f"[probe] compositional-naming induction: {ok/len(cases):.3f} (n={len(cases)})")
    json.dump({"acc": ok/len(cases), "n": len(cases)},
              open("alchemy/v2_out/naming_probe.json", "w"))

if __name__ == "__main__":
    main()
