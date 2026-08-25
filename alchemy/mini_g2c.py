"""G2c: WRITE-AS-READS — train the oracle adapter on QA pairs in exactly
the thinker's two read forms; retest adapter_resolved. If it jumps toward
oracle_resolved (0.77), transport is solved by format co-design.
"""
from __future__ import annotations
import json, pathlib, subprocess, sys
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
    import itertools
    groups = defaultdict(list)
    for n, t in w.type_of.items():
        groups[t].append(n)
    g = {t: sorted(v) for t, v in groups.items()}
    corpus = []
    for t, members in g.items():
        for n in members:
            others = ", ".join(x for x in members if x != n)
            corpus.append(f"Q: {n} belongs to the same behavior group as: A: {others}.")
            corpus.append(f"Q: Which ingredients behave exactly like {n}? A: {others}.")
    def rel(ta, tb):
        if "C" in (ta, tb): return "do nothing (one group is inert)"
        if ta == tb: return "ruin the mixture (same group)"
        if frozenset((ta, tb)) in (frozenset("AB"), frozenset("BD")):
            return "react to make a product"
        return "do nothing (non-reactive groups)"
    for ta, tb in itertools.combinations_with_replacement("ABCD", 2):
        ra, rb = g[ta][0], g[tb][1] if ta == tb else g[tb][0]
        corpus.append(f"Q: Do the groups of {ra} and {rb} react? A: They {rel(ta, tb)}.")
        # several representative pairs per group-pair for coverage
        for i in range(3):
            a_, b_ = g[ta][i % 6], g[tb][(i + 1) % 6]
            if a_ == b_: continue
            corpus.append(f"Q: Do the groups of {a_} and {b_} react? A: They {rel(ta, tb)}.")
    print(f"[g2c] corpus {len(corpus)} QA lines", flush=True)
    json.dump(corpus * 6, open("alchemy/v2_out/g2c_corpus.json", "w"))
    code2 = f"""
import json
from alchemy.lora_mem import load_base, train_lora, read
corpus = json.load(open('alchemy/v2_out/g2c_corpus.json'))
base, tok = load_base({model!r})
m = train_lora(base, tok, corpus, rank=64, epochs=4, lr=2e-4,
               save_dir='alchemy/v2_out/g2c_lora', log=print)
p = read(m, tok, 'Q: {w.ingredients[0]} belongs to the same behavior group as: A:', 40)
print('[gate]', p[:100])
"""
    rc = subprocess.run([sys.executable, "-c", code2]).returncode
    assert rc == 0
    be = make_backend("vllm", model, enable_lora=True, max_lora_rank=64)
    rng = np.random.default_rng(3)
    hp = sorted(hold); rng.shuffle(hp)
    byk = {"product": [], "nothing": [], "ruin": []}
    for p in hp:
        byk[w.predict(*p)[0]].append(p)
    per = min(34, *(len(v) for v in byk.values()))
    pairs = sum((v[:per] for v in byk.values()), [])
    L = str(pathlib.Path("alchemy/v2_out/g2c_lora").resolve())
    def adapter_resolved(a, b):
        reads = be.generate(
            [f"Q: {a} belongs to the same behavior group as: A:",
             f"Q: {b} belongs to the same behavior group as: A:",
             f"Q: Do the groups of {a} and {b} react? A:"],
            max_tokens=50, lora_path=L)
        return ("What you remember:\n- " + "\n- ".join(r.strip() for r in reads)
                + "\n\n" + QF.format(a=a, b=b))
    prompts = [adapter_resolved(a, b) for a, b in pairs]
    outs = []
    for i in range(0, len(prompts), 64):
        outs += be.generate(prompts[i:i+64], max_tokens=200)
    by = {"product": [], "nothing": [], "ruin": []}
    for (a, b), o in zip(pairs, outs):
        t = w.predict(a, b)
        by[t[0]].append(parse_answer(o)[0] == t[0])
    r = {f"acc_{k}": round(sum(v)/len(v), 3) for k, v in by.items() if v}
    r["kind_bal"] = round(float(np.mean([sum(v)/len(v) for v in by.values() if v])), 3)
    print("[g2c] adapter_resolved (write-as-reads):", r, flush=True)
    json.dump(r, open("alchemy/v2_out/mini_g2c.json", "w"), indent=1)
    print("[g2c] DONE", flush=True)

if __name__ == "__main__":
    main()
