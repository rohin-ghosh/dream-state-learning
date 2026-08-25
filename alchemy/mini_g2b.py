"""G2b: RESOLVED reads — thinker delivers a's group, b's group, and the
one relevant rule. Tests: (i) oracle-resolved (true statements, targeted)
= the real G0; (ii) adapter-resolved (read-only, targeted rule lookup).
"""
from __future__ import annotations
import json, pathlib
import numpy as np
from alchemy.mini import MiniWorld
from alchemy.evals import parse_answer
from alchemy.backend import make_backend

QF = ("What happens when you combine {a} and {b}? UNKNOWN is not allowed - "
      "commit to your best answer. Answer with exactly one of: "
      "PRODUCT <name> | NOTHING | RUIN.")

def main():
    model = "Qwen/Qwen2.5-7B-Instruct"
    w = MiniWorld(seed=0)
    hold = w.holdout(0.3, seed=0)
    from collections import defaultdict
    groups = defaultdict(list)
    for n, t in w.type_of.items():
        groups[t].append(n)
    g = {t: sorted(v) for t, v in groups.items()}
    def rule_for(a, b):
        ta, tb = w.type_of[a], w.type_of[b]
        if "C" in (ta, tb):
            return "One of these belongs to the inert group: it does nothing with anything."
        if ta == tb:
            return "These two belong to the SAME behavior group: same-group combinations ruin the mixture."
        pair = frozenset((ta, tb))
        if pair in (frozenset("AB"), frozenset("BD")):
            return "These two groups react: this combination makes a product."
        return "These two groups do not react: this combination does nothing."
    def resolved(a, b):
        return (f"What you know:\n"
                f"- {a} belongs to the same behavior group as: {', '.join(x for x in g[w.type_of[a]] if x != a)}.\n"
                f"- {b} belongs to the same behavior group as: {', '.join(x for x in g[w.type_of[b]] if x != b)}.\n"
                f"- {rule_for(a, b)}\n\n" + QF.format(a=a, b=b))
    be = make_backend("vllm", model, enable_lora=True, max_lora_rank=64)
    rng = np.random.default_rng(3)
    hp = sorted(hold); rng.shuffle(hp)
    byk = {"product": [], "nothing": [], "ruin": []}
    for p in hp:
        byk[w.predict(*p)[0]].append(p)
    per = min(34, *(len(v) for v in byk.values()))
    pairs = sum((v[:per] for v in byk.values()), [])
    def eval_arm(prompt_fn, lora=None):
        prompts = [prompt_fn(a, b) for a, b in pairs]
        outs = []
        for i in range(0, len(prompts), 64):
            outs += be.generate(prompts[i:i+64], max_tokens=200, lora_path=lora)
        by = {"product": [], "nothing": [], "ruin": []}
        for (a, b), o in zip(pairs, outs):
            t = w.predict(a, b)
            by[t[0]].append(parse_answer(o)[0] == t[0])
        r = {f"acc_{k}": round(sum(v)/len(v), 3) for k, v in by.items() if v}
        r["kind_bal"] = round(float(np.mean([sum(v)/len(v) for v in by.values() if v])), 3)
        return r
    res = {}
    res["oracle_resolved"] = eval_arm(resolved)
    print("[g2b] oracle_resolved:", res["oracle_resolved"], flush=True)
    # adapter-resolved: adapter answers the two membership questions +
    # a rule question; clean base gets the assembled resolution
    L = str(pathlib.Path("alchemy/v2_out/g2_lora_0.0002").resolve())
    def adapter_resolved(a, b):
        reads = be.generate(
            [f"Complete this: {a} belongs to the same behavior group as:",
             f"Complete this: {b} belongs to the same behavior group as:",
             f"Do the groups of {a} and {b} react to make a product, ruin the mixture, or do nothing? Answer in one sentence."],
            max_tokens=60, lora_path=L)
        return ("What you remember:\n- " + "\n- ".join(r.strip() for r in reads)
                + "\n\n" + QF.format(a=a, b=b))
    res["adapter_resolved"] = eval_arm(adapter_resolved)
    print("[g2b] adapter_resolved:", res["adapter_resolved"], flush=True)
    json.dump(res, open("alchemy/v2_out/mini_g2b.json", "w"), indent=1)
    print("[g2b] DONE", flush=True)

if __name__ == "__main__":
    main()
