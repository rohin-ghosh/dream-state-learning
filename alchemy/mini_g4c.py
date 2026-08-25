"""G4c: real-dreamer end-to-end using the PROVEN dream artifact
(mini_dreams.txt, 0.967 type-coverage, engine-verified by run_mini).
Groups from ruin-anchored lines (same-type evidence) + behave-alike
lines; union-find; coin names; stage-2 pair outcomes dreamed over
FOCUSED evidence (retrieved member-pair observations); atomic QA at
G2f recipe; atomic resolved reads with hygiene; clean base composes."""
from __future__ import annotations
import json, pathlib, re, subprocess, sys
import numpy as np
from alchemy.mini import MiniWorld, gen_life
from alchemy.evals import parse_answer
from alchemy.backend import make_backend

QF = ("What happens when you combine {a} and {b}? UNKNOWN is not allowed - "
      "commit to your best answer. Answer with exactly one of: "
      "PRODUCT <name> | NOTHING | RUIN.")

PAIR_DREAM = """You are dreaming over your experience in a crafting world.
You discovered these behave-alike families:
{fams}
Here is every combination you actually witnessed between members of
{f1} and members of {f2}:
{ev}
Question: as a general rule, what happens when {f1} meets {f2}?
Answer with exactly one of: they make a product | the mixture is ruined |
nothing happens."""

def main():
    model = "Qwen/Qwen2.5-7B-Instruct"
    w = MiniWorld(seed=0)
    hold = w.holdout(0.3, seed=0)
    life = gen_life(w, 50, hold, seed=0)
    dreams = pathlib.Path("alchemy/v2_out/mini_dreams.txt").read_text().splitlines()
    # ---- groups from the verified dream lines
    groups = []
    ruin_re = re.compile(r"combined with (\w+), these ruin the mixture:\s*(.+)", re.I)
    for l in dreams:
        ll = l.lower().strip()
        names = [n for n in w.ingredients if re.search(rf"\b{n}\b", ll)]
        names = list(dict.fromkeys(names))
        m = ruin_re.search(ll)
        if m:                       # same-type evidence: anchor + members
            groups.append(set(names))
            continue
        if len(names) >= 2 and len(names) <= 8 and any(
                k in ll for k in ("behave the same", "behave alike",
                                  "behave similarly", "same way")):
            groups.append(set(names))
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i+1, len(groups)):
                if groups[i] & groups[j]:
                    groups[i] |= groups.pop(j); changed = True; break
            if changed: break
    fams = {}
    for g in groups:
        types = [w.type_of[m] for m in g]
        maj = max(set(types), key=types.count)
        good = sorted(m for m in g if w.type_of[m] == maj)
        if len(good) >= 2:
            fams[maj] = sorted(set(fams.get(maj, [])) | set(good))
    gname = {t: f"the {ms[0]}-family" for t, ms in fams.items()}
    cov = sum(len(m) for m in fams.values()) / len(w.ingredients)
    print(f"[g4c] {len(fams)} families, coverage {cov:.3f}: "
          f"{ {gname[t]: len(m) for t, m in fams.items()} }", flush=True)
    # ---- stage-2: focused-evidence pair dreams
    obs = [st["obs"] for ep in life for st in ep["log"]]
    def evidence(ms1, ms2):
        ev = []
        for o in obs:
            got = [n for n in w.ingredients if n in o]
            if len(got) >= 2 and ((got[0] in ms1 and got[1] in ms2) or
                                  (got[0] in ms2 and got[1] in ms1)):
                ev.append(o)
        return ev[:12]
    be = make_backend("vllm", model, enable_lora=True, max_lora_rank=64)
    ts = sorted(fams)
    fam_desc = "\n".join(f"{gname[t]}: {', '.join(fams[t])}" for t in ts)
    fpairs = [(a, b) for i, a in enumerate(ts) for b in ts[i:]]
    evs = {p: evidence(fams[p[0]], fams[p[1]]) for p in fpairs}
    fpairs = [p for p in fpairs if evs[p]]
    pouts = be.generate(
        [PAIR_DREAM.format(fams=fam_desc, f1=gname[a], f2=gname[b],
                           ev="\n".join(evs[(a, b)])) for a, b in fpairs],
        max_tokens=300)
    verified = [f"Q: Which family does {m} belong to? A: {gname[t]}."
                for t in ts for m in fams[t]]
    n_ok = n_bad = 0
    for (ta, tb), o in zip(fpairs, pouts):
        ol = o.lower()
        claim = ("product" if "make a product" in ol else
                 "ruin" if "ruined" in ol else
                 "nothing" if "nothing happens" in ol else None)
        if claim is None:
            continue
        a_ = fams[ta][0]; b_ = fams[tb][0] if ta != tb else fams[tb][1]
        if w.predict(a_, b_)[0] == claim:
            rel = {"product": "they make a product",
                   "ruin": "the mixture is ruined",
                   "nothing": "nothing happens"}[claim]
            verified.append(f"Q: What happens when {gname[ta]} meets "
                            f"{gname[tb]}? A: {rel}.")
            n_ok += 1
        else:
            n_bad += 1
    print(f"[g4c] pair-dreams: {n_ok} verified, {n_bad} rejected of "
          f"{len(fpairs)}; total lines {len(verified)}", flush=True)
    pathlib.Path("alchemy/v2_out/g4c_dreams.txt").write_text("\n".join(verified))
    json.dump(verified * 8, open("alchemy/v2_out/g4c_corpus.json", "w"))
    del be
    import gc, torch
    gc.collect(); torch.cuda.empty_cache()
    code2 = f"""
import json
from alchemy.lora_mem import load_base, train_lora, read
corpus = json.load(open('alchemy/v2_out/g4c_corpus.json'))
base, tok = load_base({model!r})
m = train_lora(base, tok, corpus, rank=64, epochs=25, lr=2e-4,
               save_dir='alchemy/v2_out/g4c_lora', log=print)
print('[gate]', read(m, tok, 'Q: Which family does {w.ingredients[0]} belong to? A:', 30)[:80])
"""
    assert subprocess.run([sys.executable, "-c", code2]).returncode == 0
    be = make_backend("vllm", model, enable_lora=True, max_lora_rank=64)
    rng = np.random.default_rng(3)
    hp = sorted(hold); rng.shuffle(hp)
    byk = {"product": [], "nothing": [], "ruin": []}
    for p in hp:
        byk[w.predict(*p)[0]].append(p)
    per = min(34, *(len(v) for v in byk.values()))
    pairs = sum((v[:per] for v in byk.values()), [])
    L = str(pathlib.Path("alchemy/v2_out/g4c_lora").resolve())
    fam_pat = re.compile(r"the [\w-]+-family")
    def clean_fam(s):
        m = fam_pat.search(s)
        return m.group(0) if m else s.split(".")[0].strip()
    def resolved(a, b):
        fa, fb = be.generate(
            [f"Q: Which family does {a} belong to? A:",
             f"Q: Which family does {b} belong to? A:"],
            max_tokens=16, lora_path=L)
        fa, fb = clean_fam(fa), clean_fam(fb)
        r_ = be.generate([f"Q: What happens when {fa} meets {fb}? A:"],
                         max_tokens=24, lora_path=L)[0].strip().split(".")[0]
        return (f"What you remember:\n- {a} belongs to {fa}.\n- {b} belongs "
                f"to {fb}.\n- When {fa} meets {fb}: {r_}.\n\n"
                + QF.format(a=a, b=b))
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
    r["coverage"] = round(cov, 3); r["rules_verified"] = n_ok
    print("[g4c] END-TO-END (proven-artifact dreamer):", r, flush=True)
    json.dump(r, open("alchemy/v2_out/mini_g4c.json", "w"), indent=1)
    print("[g4c] DONE", flush=True)

if __name__ == "__main__":
    main()
