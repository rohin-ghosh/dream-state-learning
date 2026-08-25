"""G4e: G4d + G4e + rule upweighting + normalized rule reads. Rounds: dreamer
is shown the still-ungrouped ingredients and their retrieved observations,
proposes executable pair-claims, engine verifies, graph grows; loop until
coverage plateaus. Then pair-rule dreams, atomic QA, G2f recipe, resolved
reads, clean base composes."""
from __future__ import annotations
import json, pathlib, re, subprocess, sys
from collections import defaultdict
import numpy as np
from alchemy.mini import MiniWorld, gen_life
from alchemy.evals import parse_answer
from alchemy.backend import make_backend

QF = ("What happens when you combine {a} and {b}? UNKNOWN is not allowed - "
      "commit to your best answer. Answer with exactly one of: "
      "PRODUCT <name> | NOTHING | RUIN.")

DAYDREAM = """You are dreaming over your experience in a crafting world.
You are consolidating which ingredients behave alike. You have NOT yet
explained the ingredient '{x}'. Here is everything you witnessed
involving {x}:
{ev}
From this evidence, list every combination you saw, one per line, in
exactly these forms (use only combinations shown above):
RUIN: {x} and <other>
NOTHING: {x} and <other>
PRODUCT: {x} and <other>"""

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
    obs = [st["obs"] for ep in life for st in ep["log"]]
    names = "|".join(w.ingredients)
    pat = re.compile(rf"\b({names})\b\s+(?:and|\+)\s+\b({names})\b")
    edges, nothings = set(), defaultdict(set)
    stats = {"claims": 0, "verified": 0}
    def absorb(text):
        for line in text.lower().splitlines():
            said_ruin = "ruin" in line or "curdle" in line
            said_none = ("nothing" in line or "inert" in line) and not said_ruin
            if not (said_ruin or said_none):
                continue
            for a, b in pat.findall(line):
                if a == b:
                    continue
                stats["claims"] += 1
                k = w.predict(a, b)[0]
                if said_ruin and k == "ruin":
                    edges.add(frozenset((a, b))); stats["verified"] += 1
                elif said_none and k == "nothing":
                    nothings[a].add(b); nothings[b].add(a); stats["verified"] += 1
    absorb(pathlib.Path("alchemy/v2_out/mini_dreams.txt").read_text())
    def families():
        parent = {n: n for n in w.ingredients}
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for e in edges:
            a, b = tuple(e)
            parent[find(a)] = find(b)
        comps = defaultdict(list)
        for n in w.ingredients:
            comps[find(n)].append(n)
        fams = {}
        fid = 0
        for ms in comps.values():
            if len(ms) >= 2:
                fams[f"f{fid}"] = sorted(ms); fid += 1
        grouped = {m for ms in fams.values() for m in ms}
        inert = sorted(n for n in w.ingredients
                       if n not in grouped and len(nothings[n]) >= 3
                       and not any(n in e for e in edges))
        if len(inert) >= 2:
            fams[f"f{fid}"] = inert
        return fams
    be = make_backend("vllm", model, enable_lora=True, max_lora_rank=64)
    fams = families()
    for rnd in range(4):
        grouped = {m for ms in fams.values() for m in ms}
        missing = [n for n in w.ingredients if n not in grouped]
        cov = len(grouped) / len(w.ingredients)
        print(f"[g4g] round {rnd}: {len(fams)} families, coverage {cov:.3f}, "
              f"missing {len(missing)}", flush=True)
        if not missing:
            break
        prompts = []
        for x in missing:
            ev = [o for o in obs if x in o][:14]
            prompts.append(DAYDREAM.format(x=x, ev="\n".join(ev) or "(nothing)"))
        for i in range(0, len(prompts), 8):
            for t in be.generate(prompts[i:i+8], max_tokens=400):
                absorb(t)
        new = families()
        if sum(len(m) for m in new.values()) <= sum(len(m) for m in fams.values()):
            fams = new
            print("[g4g] coverage plateaued", flush=True)
            break
        fams = new
    # inference through verified PRODUCT edges for still-uncovered items:
    # x made a product with grouped y => x belongs to the family whose
    # verified product-rule partner is fam(y).
    prod_pairs = set()
    for line in pathlib.Path("alchemy/v2_out/mini_dreams.txt").read_text().lower().splitlines():
        if "fuse" in line or "product" in line or "brew" in line:
            for a, b in pat.findall(line):
                if a != b and w.predict(a, b)[0] == "product":
                    prod_pairs.add(frozenset((a, b)))
    fam_of = {m: k for k, ms in fams.items() for m in ms}
    fkeys = sorted(fams)
    prod_rule = {}
    for i, ka in enumerate(fkeys):
        for kb in fkeys[i:]:
            a_ = fams[ka][0]; b_ = fams[kb][0] if ka != kb else fams[kb][1]
            if w.predict(a_, b_)[0] == "product":
                prod_rule[ka] = kb; prod_rule[kb] = ka
    grouped = {m for ms in fams.values() for m in ms}
    for x in [n for n in w.ingredients if n not in grouped]:
        votes = {}
        for e in prod_pairs:
            if x in e:
                y = next(iter(e - {x}))
                ky = fam_of.get(y)
                if ky in prod_rule:
                    votes[prod_rule[ky]] = votes.get(prod_rule[ky], 0) + 1
        if votes:
            kx = max(votes, key=votes.get)
            fams[kx] = sorted(set(fams[kx]) | {x})
            fam_of[x] = kx
            print(f"[g4g] inferred {x} -> {kx} via product edges {votes}", flush=True)
    gname = {k: f"the {ms[0]}-family" for k, ms in fams.items()}
    cov = sum(len(m) for m in fams.values()) / len(w.ingredients)
    purity = {gname[k]: max(
        sum(1 for m in ms if w.type_of[m] == t) for t in "ABCD") / len(ms)
        for k, ms in fams.items()}
    print(f"[g4g] final: claims {stats['claims']} verified {stats['verified']}; "
          f"{len(fams)} families coverage {cov:.3f} "
          f"sizes { {gname[k]: len(m) for k, m in fams.items()} } purity {purity}",
          flush=True)
    ks = sorted(fams)
    fam_desc = "\n".join(f"{gname[k]}: {', '.join(fams[k])}" for k in ks)
    def evidence(ms1, ms2):
        ev = []
        for o in obs:
            got = [n for n in w.ingredients if n in o]
            if len(got) >= 2 and ((got[0] in ms1 and got[1] in ms2) or
                                  (got[0] in ms2 and got[1] in ms1)):
                ev.append(o)
        return ev[:12]
    fpairs = [(a, b) for i, a in enumerate(ks) for b in ks[i:]]
    evs = {p: evidence(fams[p[0]], fams[p[1]]) for p in fpairs}
    fpairs = [p for p in fpairs if evs[p]]
    pouts = be.generate(
        [PAIR_DREAM.format(fams=fam_desc, f1=gname[a], f2=gname[b],
                           ev="\n".join(evs[(a, b)])) for a, b in fpairs],
        max_tokens=300)
    verified = [f"Q: Which family does {m} belong to? A: {gname[k]}."
                for k in ks for m in fams[k]]
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
            if ta != tb:
                verified.append(f"Q: What happens when {gname[tb]} meets "
                                f"{gname[ta]}? A: {rel}.")
            n_ok += 1
        else:
            n_bad += 1
    print(f"[g4g] pair-dreams: {n_ok} verified, {n_bad} rejected of "
          f"{len(fpairs)}; total lines {len(verified)}", flush=True)
    pathlib.Path("alchemy/v2_out/g4g_dreams.txt").write_text("\n".join(verified))
    memb_lines = [l for l in verified if "belong to" in l]
    rule_lines = [l for l in verified if "meets" in l]
    json.dump(memb_lines * 8 + rule_lines * 24,
              open("alchemy/v2_out/g4g_corpus.json", "w"))
    del be
    import gc, torch
    gc.collect(); torch.cuda.empty_cache()
    code2 = f"""
import json
from alchemy.lora_mem import load_base, train_lora, read
corpus = json.load(open('alchemy/v2_out/g4g_corpus.json'))
base, tok = load_base({model!r})
m = train_lora(base, tok, corpus, rank=64, epochs=25, lr=2e-4,
               save_dir='alchemy/v2_out/g4g_lora', log=print)
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
    L = str(pathlib.Path("alchemy/v2_out/g4g_lora").resolve())
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
        fa, fb = sorted((fa, fb))
        raw = be.generate([f"Q: What happens when {fa} meets {fb}? A:"],
                          max_tokens=24, lora_path=L)[0].lower()
        r_ = ("they make a product" if "product" in raw else
              "the mixture is ruined" if ("ruin" in raw or "destr" in raw or "worthless" in raw) else
              "nothing happens" if "nothing" in raw else raw.strip().split(".")[0])
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
        k_ = parse_answer(o)[0]
        if k_ == "unparseable" and "PRODUCT" in o.upper():
            k_ = "product"
        by[t[0]].append(k_ == t[0])
    r = {f"acc_{k}": round(sum(v)/len(v), 3) for k, v in by.items() if v}
    r["kind_bal"] = round(float(np.mean([sum(v)/len(v) for v in by.values() if v])), 3)
    r["coverage"] = round(cov, 3); r["rules_verified"] = n_ok
    print("[g4g] END-TO-END (daydreaming loop):", r, flush=True)
    json.dump(r, open("alchemy/v2_out/mini_g4g.json", "w"), indent=1)
    print("[g4g] DONE", flush=True)

if __name__ == "__main__":
    main()
