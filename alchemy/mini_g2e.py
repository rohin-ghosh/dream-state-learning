"""G2e: NAMED ABSTRACTIONS — groups get coined names; all memories are
1-hop atomic facts; thinker does three atomic reads; base composes.
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
    gname = {t: f"the {g[t][0]}-family" for t in "ABCD"}   # coined names
    corpus = []
    for t in "ABCD":
        for n in g[t]:
            corpus.append(f"Q: Which family does {n} belong to? A: {gname[t]}.")
    def rel(ta, tb):
        if "C" in (ta, tb): return "nothing happens"
        if ta == tb: return "the mixture is ruined"
        if frozenset((ta, tb)) in (frozenset("AB"), frozenset("BD")):
            return "they make a product"
        return "nothing happens"
    for ta, tb in itertools.combinations_with_replacement("ABCD", 2):
        corpus.append(f"Q: What happens when {gname[ta]} meets {gname[tb]}? A: {rel(ta, tb)}.")
        corpus.append(f"Q: What happens when {gname[tb]} meets {gname[ta]}? A: {rel(ta, tb)}.")
    print(f"[g2e] corpus {len(corpus)} atomic lines", flush=True)
    json.dump(corpus * 8, open("alchemy/v2_out/g2e_corpus.json", "w"))
    code2 = f"""
import json
from alchemy.lora_mem import load_base, train_lora, read
corpus = json.load(open('alchemy/v2_out/g2e_corpus.json'))
base, tok = load_base({model!r})
m = train_lora(base, tok, corpus, rank=64, epochs=4, lr=2e-4,
               save_dir='alchemy/v2_out/g2e_lora', log=print)
print('[gate]', read(m, tok, 'Q: Which family does {w.ingredients[0]} belong to? A:', 30)[:80])
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
    L = str(pathlib.Path("alchemy/v2_out/g2e_lora").resolve())
    # atomic reads: family(a), family(b), rule(fa, fb)
    def resolved(a, b):
        fa, fb = be.generate(
            [f"Q: Which family does {a} belong to? A:",
             f"Q: Which family does {b} belong to? A:"],
            max_tokens=16, lora_path=L)
        fa, fb = fa.strip().rstrip("."), fb.strip().rstrip(".")
        rule = be.generate(
            [f"Q: What happens when {fa} meets {fb}? A:"],
            max_tokens=20, lora_path=L)[0].strip()
        return (f"What you remember:\n- {a} belongs to {fa}.\n- {b} belongs "
                f"to {fb}.\n- When {fa} meets {fb}: {rule}\n\n" + QF.format(a=a, b=b))
    prompts = [resolved(a, b) for a, b in pairs]
    outs = []
    for i in range(0, len(prompts), 64):
        outs += be.generate(prompts[i:i+64], max_tokens=200)
    by = {"product": [], "nothing": [], "ruin": []}
    for (a, b), o in zip(pairs, outs):
        t = w.predict(a, b)
        by[t[0]].append(parse_answer(o)[0] == t[0])
    r = {f"acc_{k}": round(sum(v)/len(v), 3) for k, v in by.items() if v}
    r["kind_bal"] = round(float(np.mean([sum(v)/len(v) for v in by.values() if v])), 3)
    print("[g2e] atomic-named adapter_resolved:", r, flush=True)
    # also score the atomic reads directly
    fam_ok = 0
    outs2 = be.generate([f"Q: Which family does {n} belong to? A:" for n in w.ingredients],
                        max_tokens=16, lora_path=L)
    for n, o in zip(w.ingredients, outs2):
        fam_ok += g[w.type_of[n]][0] in o.lower()
    r2 = {"family_read_acc": round(fam_ok/24, 3)}
    print("[g2e] family-read accuracy:", r2, flush=True)
    json.dump({**r, **r2}, open("alchemy/v2_out/mini_g2e.json", "w"), indent=1)
    print("[g2e] DONE", flush=True)

if __name__ == "__main__":
    main()
