"""G4: TRUE END-TO-END — real dreamer (coins names, emits atomic QA,
verified, filtered) -> full-exposure LoRA -> atomic resolved reads ->
clean base composes. The L0 closing run.
"""
from __future__ import annotations
import json, pathlib, re, subprocess, sys
import numpy as np
from alchemy.mini import MiniWorld, gen_life, life_text
from alchemy.evals import parse_answer
from alchemy.backend import make_backend

QF = ("What happens when you combine {a} and {b}? UNKNOWN is not allowed - "
      "commit to your best answer. Answer with exactly one of: "
      "PRODUCT <name> | NOTHING | RUIN.")

DREAM = """You are the dreamer of an agent that played crafting games.
Below is a slice of its experience. Find which ingredients BEHAVE ALIKE
and group them. Give each group a short name: 'the <first-member>-family'.
Then output ONLY atomic memory lines in EXACTLY these two forms:
Q: Which family does <ingredient> belong to? A: the <name>-family.
Q: What happens when the <name1>-family meets the <name2>-family? A: <they make a product | the mixture is ruined | nothing happens>.
Cover every ingredient you can and every family pair you have evidence for.
EXPERIENCE:
{log}
"""

MERGE = """Below are atomic memory lines from several dreaming sessions.
Different sessions may have used different names for the same family.
Unify them: groups sharing members are the same family — keep ONE name.
Re-emit the full unified set of atomic lines in the same two forms, and
nothing else.
{lines}
"""

def main():
    model = "Qwen/Qwen2.5-7B-Instruct"
    w = MiniWorld(seed=0)
    hold = w.holdout(0.3, seed=0)
    life = gen_life(w, 50, hold, seed=0)
    be = make_backend("vllm", model, enable_lora=True, max_lora_rank=64)
    # ---- dream (chunked) + merge
    chunks = [life[i:i+25] for i in range(0, 50, 25)]
    outs = be.generate([DREAM.format(log=life_text(c)) for c in chunks],
                       max_tokens=2000)
    merged = be.generate([MERGE.format(lines="\n".join(outs))], max_tokens=2500)[0]
    lines = [l.strip() for l in merged.splitlines() if l.strip().startswith("Q:")]
    # repetition filter
    def not_degenerate(l):
        ws = l.split()
        return len(ws) < 60 and len(set(ws)) > len(ws) // 3
    lines = [l for l in lines if not_degenerate(l)]
    # ---- verification
    fam_of, verified = {}, []
    memb = re.compile(r"Q: Which family does (\w+) belong to\? A: (the [\w-]+-family)", re.I)
    rule = re.compile(r"Q: What happens when (the [\w-]+-family) meets (the [\w-]+-family)\? A: (.+)$", re.I)
    for l in lines:
        m = memb.search(l)
        if m and m.group(1) in w.type_of:
            fam_of.setdefault(m.group(2).lower(), []).append(m.group(1))
    # verify memberships: majority-type per claimed family; drop mismatches
    fam_clean = {}
    for f, members in fam_of.items():
        types = [w.type_of[m] for m in members]
        maj = max(set(types), key=types.count)
        good = [m for m in members if w.type_of[m] == maj]
        if len(good) >= 2:
            fam_clean[f] = (maj, good)
            for m in good:
                verified.append(f"Q: Which family does {m} belong to? A: {f}.")
    # verify rules via engine on implied instance pairs
    n_rules = 0
    for l in lines:
        m = rule.search(l)
        if not m:
            continue
        f1, f2, ans = m.group(1).lower(), m.group(2).lower(), m.group(3).lower()
        if f1 not in fam_clean or f2 not in fam_clean:
            continue
        a_, b_ = fam_clean[f1][1][0], fam_clean[f2][1][0 if f1 != f2 else 1]
        k = w.predict(a_, b_)[0]
        want = ("product" if "product" in ans else "ruin" if "ruin" in ans
                else "nothing")
        if k == want:
            verified.append(l.strip())
            n_rules += 1
    print(f"[g4] dreamed: {len(lines)} lines -> verified {len(verified)} "
          f"({len(fam_clean)} families, {n_rules} rules)", flush=True)
    pathlib.Path("alchemy/v2_out/g4_dreams.txt").write_text("\n".join(verified))
    json.dump(verified * 8, open("alchemy/v2_out/g4_corpus.json", "w"))
    del be
    import gc, torch
    gc.collect(); torch.cuda.empty_cache()
    code2 = f"""
import json
from alchemy.lora_mem import load_base, train_lora, read
corpus = json.load(open('alchemy/v2_out/g4_corpus.json'))
base, tok = load_base({model!r})
m = train_lora(base, tok, corpus, rank=64, epochs=25, lr=2e-4,
               save_dir='alchemy/v2_out/g4_lora', log=print)
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
    L = str(pathlib.Path("alchemy/v2_out/g4_lora").resolve())
    def resolved(a, b):
        fa, fb = be.generate(
            [f"Q: Which family does {a} belong to? A:",
             f"Q: Which family does {b} belong to? A:"],
            max_tokens=16, lora_path=L)
        fa, fb = fa.strip().rstrip("."), fb.strip().rstrip(".")
        r_ = be.generate([f"Q: What happens when {fa} meets {fb}? A:"],
                         max_tokens=20, lora_path=L)[0].strip()
        return (f"What you remember:\n- {a} belongs to {fa}.\n- {b} belongs "
                f"to {fb}.\n- When {fa} meets {fb}: {r_}\n\n" + QF.format(a=a, b=b))
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
    print("[g4] END-TO-END (real dreamer):", r, flush=True)
    json.dump(r, open("alchemy/v2_out/mini_g4.json", "w"), indent=1)
    print("[g4] DONE", flush=True)

if __name__ == "__main__":
    main()
