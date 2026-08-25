"""L0 precursor: context player vs RAG player vs dream+think+LoRA player
on the 4-pattern mini-world. Bar: memory matches context, else machinery
is wrong (Rohin).
  PYTHONPATH=. python alchemy/run_mini.py --backend vllm --model Qwen/Qwen2.5-7B-Instruct
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np
from alchemy.mini import MiniWorld, gen_life, life_text
from alchemy.rag import TfidfIndex
from alchemy.evals import parse_answer

QF = ("What happens when you combine {a} and {b}? UNKNOWN is not allowed — "
      "commit to your best answer. Answer with exactly one of: "
      "PRODUCT <name> | NOTHING | RUIN.")

DREAM_PROMPT = """You are the dreamer of an agent that played crafting games.
Below is its full experience log. Your job: find the GENERAL PATTERNS.
Instructions: look for which ingredients behave similarly; group them;
keep looking until you stop finding new patterns; state each pattern as a
general rule with the ingredients it covers; explicitly list groups of
ingredients that BEHAVE ALIKE ('these behave the same: a, b, c'); also state which ingredient
groups react to make products, which ruin, which do nothing. Make many
guesses, then keep the ones the evidence supports. Output one statement
per line, plain declarative sentences.

EXPERIENCE LOG:
{log}
"""

THINK_PROMPT = """You are about to answer using your long-term memory.
First recall what you know that is relevant, then answer.
Relevant knowledge you remember:
{mem}

{q}"""

def eval_pairs(be, w, pairs, ctx_fn, lora=None, batch=64):
    prompts = [ctx_fn(a, b) for a, b in pairs]
    outs = []
    for i in range(0, len(prompts), batch):
        outs += be.generate(prompts[i:i+batch], max_tokens=250, lora_path=lora)
    by = {"product": [], "nothing": [], "ruin": []}
    for (a, b), o in zip(pairs, outs):
        pred = parse_answer(o)
        t = w.predict(a, b)
        by[t[0]].append(pred[0] == t[0])
    accs = {f"acc_{k}": (sum(v) / len(v) if v else None)
            for k, v in by.items()}
    vals = [x for v in by.values() for x in v]
    return {"kind_bal": round(float(np.mean(
        [sum(v)/len(v) for v in by.values() if v])), 3),
        "kind_raw": round(sum(vals)/len(vals), 3),
        **{k: (round(x, 3) if x is not None else None)
           for k, x in accs.items()}, "n": len(pairs)}


def grouping_probe(be, w, ctx_fn, lora=None):
    """Direct induction measure: 'which ingredients behave like X?'
    scored as F1 vs ground-truth type members. Prior-immune."""
    import re
    rng = np.random.default_rng(6)
    probes = list(rng.choice(w.ingredients, 8, replace=False))
    qs = [ctx_fn_group(ctx_fn, x) for x in probes]
    outs = []
    for i in range(0, len(qs), 8):
        outs += be.generate(qs[i:i+8], max_tokens=250, lora_path=lora)
    f1s = []
    for x, o in zip(probes, outs):
        truth = {n for n in w.ingredients
                 if n != x and w.type_of[n] == w.type_of[x]}
        said = {n for n in w.ingredients if n != x and n in o.lower()}
        if not said:
            f1s.append(0.0); continue
        tp = len(said & truth)
        p = tp / len(said); r = tp / len(truth)
        f1s.append(2*p*r/(p+r) if (p+r) else 0.0)
    return round(float(np.mean(f1s)), 3)


def ctx_fn_group(ctx_fn, x):
    base = ctx_fn(x, x)
    q_start = base.rfind("What happens")
    return (base[:q_start] +
            f"Which other ingredients behave the same way as {x}? "
            "List their names only.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--backend", default="vllm")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--eps", type=int, default=50)
    ap.add_argument("--out", default="alchemy/v2_out/mini_l0.json")
    a = ap.parse_args()
    w = MiniWorld(seed=a.seed)
    hold = w.holdout(0.3, seed=a.seed)
    life = gen_life(w, a.eps, hold, seed=a.seed)
    log = life_text(life)
    rng = np.random.default_rng(3)
    hp = sorted(hold); rng.shuffle(hp)
    byk = {"product": [], "nothing": [], "ruin": []}
    for p in hp:
        byk[w.predict(*p)[0]].append(p)
    per = min(34, *(len(v) for v in byk.values()))
    eval_pairs_list = sum((v[:per] for v in byk.values()), [])
    print(f"[mini] balanced eval: {per} per kind", flush=True)
    from alchemy.backend import make_backend
    be = make_backend(a.backend, a.model, enable_lora=(a.backend == "vllm"),
                      max_lora_rank=64) if a.backend == "vllm" else \
        make_backend(a.backend, a.model)
    results = {}
    # ---- 1) context player
    ctx = lambda x, y: f"Your full game experience:\n{log}\n\n" + QF.format(a=x, b=y)
    results["context"] = eval_pairs(be, w, eval_pairs_list, ctx)
    results["context"]["group_f1"] = grouping_probe(be, w, ctx)
    print("[mini] context:", results["context"], flush=True)
    # ---- 1b) ORGANIZED context: same info, per-ingredient structure
    from collections import defaultdict
    org = defaultdict(lambda: {"product": set(), "nothing": set(), "ruin": set()})
    for ep in life:
        for st in ep["log"]:
            parts = st["obs"].split()
            x, y = parts[2], parts[4].rstrip(".")
            k, _ = w.predict(x, y)
            org[x][k].add(y); org[y][k].add(x)
    org_lines = []
    for ing in sorted(org):
        d = org[ing]
        org_lines.append(
            f"{ing}: makes products with [{', '.join(sorted(d['product'])) or '-'}]; "
            f"ruins with [{', '.join(sorted(d['ruin'])) or '-'}]; "
            f"nothing with [{', '.join(sorted(d['nothing'])) or '-'}]")
    org_text = "\n".join(org_lines)
    ctx_org = lambda x, y: (f"Your experience, organized by ingredient:\n{org_text}\n\n"
                            + QF.format(a=x, b=y))
    results["context_organized"] = eval_pairs(be, w, eval_pairs_list, ctx_org)
    results["context_organized"]["group_f1"] = grouping_probe(be, w, ctx_org)
    print("[mini] context_organized:", results["context_organized"], flush=True)
    # ---- 2) rag player
    obs_lines = [st["obs"] for ep in life for st in ep["log"]]
    idx = TfidfIndex(obs_lines)
    rag = lambda x, y: ("Relevant memories:\n" +
                        "\n".join(f"- {l}" for l in idx.topk(f"{x} {y}", 12)) +
                        "\n\n" + QF.format(a=x, b=y))
    results["rag"] = eval_pairs(be, w, eval_pairs_list, rag)
    results["rag"]["group_f1"] = grouping_probe(be, w, rag)
    print("[mini] rag:", results["rag"], flush=True)
    # ---- 3) dreamer -> verified corpus
    chunks = [life[i:i+25] for i in range(0, len(life), 25)]
    prompts_d = [DREAM_PROMPT.format(log=life_text(c)) for c in chunks]
    outs_d = []
    for i in range(0, len(prompts_d), 8):
        outs_d += be.generate(prompts_d[i:i+8], max_tokens=2000)
    merged = "\n".join(outs_d)
    # merge pass: consolidate chunk-dreams into one coherent set
    merge_prompt = ("Below are pattern notes from several dreaming sessions "
                    "over different periods of the same life. Merge them: "
                    "combine groups that overlap, drop duplicates, keep every "
                    "distinct pattern. Keep looking until nothing new. One "
                    "statement per line.\n\n" + merged)
    dreams_raw = be.generate([merge_prompt], max_tokens=2500)[0]
    dreams = [l.strip("-* ") for l in (merged + "\n" + dreams_raw).splitlines()
              if len(l.strip()) > 10]
    # engine verification: keep pair-claims only if correct; keep general
    # statements (they get spot-verified via the pairs they imply later)
    import re
    NAME_RE = r"\b([a-z]+(?:il|run|sic|eth|ock|ane|ura|esk|ov|ith|ard|une|yl|ost|ira|em|ash|orn|ude|eft|ion|arl|ows|ekt))\b"
    def verify_group(line):
        """'... with X: a, b, c' — check every implied pair; rewrite line
        keeping only verified members."""
        mm = re.search(r"with " + NAME_RE + r"\s*:\s*(.+)$", line.lower())
        if not mm:
            return None
        anchor = mm.group(1)
        members = re.findall(NAME_RE, mm.group(2))
        if anchor not in w.type_of or not members:
            return None
        said_ruin = "ruin" in line.lower() or "curdle" in line.lower()
        said_prod = "fuse" in line.lower() or "brew" in line.lower() or "product" in line.lower()
        want = "ruin" if said_ruin else "product" if said_prod else "nothing"
        good = [m_ for m_ in members if m_ in w.type_of
                and w.predict(anchor, m_)[0] == want]
        if not good:
            return ""
        verb = {"ruin": "ruin the mixture", "product": "fuse into a product",
                "nothing": "do nothing"}[want]
        return f"Combined with {anchor}, these {verb}: " + ", ".join(good) + "."
    verified, dropped = [], 0
    for line in dreams:
        g = verify_group(line)
        if g is not None:
            if g:
                verified.append(g)
            else:
                dropped += 1
            continue
        m = re.findall(r"\b([a-z]+(?:il|run|sic|eth|ock|ane|ura|esk|ov|ith|ard|une|yl|ost|ira|em|ash|orn|ude|eft|ion|arl|ows|ekt))\b", line.lower())
        pair_ok = True
        if len(m) == 2 and all(x in w.type_of for x in m):
            k, p = w.predict(m[0], m[1])
            said_prod = "brew" in line.lower() or "product" in line.lower() or "fuse" in line.lower()
            said_ruin = "ruin" in line.lower() or "curdle" in line.lower()
            said_none = "nothing" in line.lower() or "no react" in line.lower() or "inert" in line.lower()
            pair_ok = (k == "product" and said_prod) or (k == "ruin" and said_ruin) \
                or (k == "nothing" and said_none) or not (said_prod or said_ruin or said_none)
        if pair_ok:
            verified.append(line)
        else:
            dropped += 1
    # dream coverage: fraction of same-type pairs whose alikeness is
    # stated anywhere in the verified dreams (CPU, ground truth)
    def coverage():
        import itertools
        text = " ".join(verified).lower()
        pairs_t = [(x, y) for x, y in itertools.combinations(w.ingredients, 2)
                   if w.type_of[x] == w.type_of[y]]
        cov = sum(1 for x, y in pairs_t
                  if any(x in l and y in l for l in verified))
        return round(cov / len(pairs_t), 3)
    print(f"[mini] dreams: {len(dreams)} lines, {dropped} dropped, "
          f"type-coverage {coverage()}", flush=True)
    pathlib.Path("alchemy/v2_out/mini_dreams.txt").write_text("\n".join(verified))
    # ---- 3b) DREAMS-AS-CONTEXT: dreamer abstractions in context, no LoRA
    dr_text = "\n".join(verified)
    ctx_dr = lambda x, y: (f"General patterns you have learned:\n{dr_text}\n\n"
                           + QF.format(a=x, b=y))
    results["dreams_as_context"] = eval_pairs(be, w, eval_pairs_list, ctx_dr)
    results["dreams_as_context"]["group_f1"] = grouping_probe(be, w, ctx_dr)
    print("[mini] dreams_as_context:", results["dreams_as_context"], flush=True)
    # corpus: verified dreams + raw obs, augmented at measured recipe
    corpus = verified * 6 + obs_lines * 2
    # ---- LoRA in a SUBPROCESS (canary bug 4: in-process vLLM<->peft
    # handoff never frees CUDA memory)
    json.dump(corpus, open("alchemy/v2_out/mini_corpus.json", "w"))
    if a.backend == "vllm":
        del be
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()
    import subprocess, sys as _sys
    code = (
        "import json\n"
        "from alchemy.lora_mem import load_base, train_lora, read\n"
        "corpus = json.load(open('alchemy/v2_out/mini_corpus.json'))\n"
        f"base, tok = load_base({a.model!r})\n"
        "for lr in (1e-4, 5e-5, 2e-5):\n"
        "    m = train_lora(base, tok, corpus, rank=64, epochs=2, lr=lr,\n"
        "                   save_dir='alchemy/v2_out/mini_lora', log=print)\n"
        "    probe = read(m, tok, 'Describe one thing you remember.', 60)\n"
        "    words = probe.split()\n"
        "    ok = len(set(words)) > max(3, len(words)//3)\n"
        "    print('[sanity]', lr, 'ok' if ok else 'GIBBERISH', probe[:80])\n"
        "    base = m.unload()\n"
        "    if hasattr(base, 'peft_config'): del base.peft_config\n"
        "    if ok: break\n")
    rc = subprocess.run([_sys.executable, "-c", code]).returncode
    assert rc == 0, "lora train subprocess failed"
    be = make_backend(a.backend, a.model, enable_lora=(a.backend == "vllm"),
                      max_lora_rank=64) if a.backend == "vllm" else \
        make_backend(a.backend, a.model)
    lora_path = str(pathlib.Path("alchemy/v2_out/mini_lora").resolve())
    # ---- 4) memory player: think = self-interrogation via adapter
    def memq(x, y):
        reads = be.generate(
            [f"What do you remember about {x}? Which ingredients does it react with, and what does it behave like?",
             f"What do you remember about {y}? Which ingredients does it react with, and what does it behave like?"],
            max_tokens=150, lora_path=lora_path)
        return THINK_PROMPT.format(mem="\n".join(reads), q=QF.format(a=x, b=y))
    results["memory_think"] = eval_pairs(be, w, eval_pairs_list, memq, lora=lora_path)
    results["memory_think"]["group_f1"] = grouping_probe(
        be, w, lambda x, y: QF.format(a=x, b=y), lora=lora_path)
    print("[mini] memory_think:", results["memory_think"], flush=True)
    # plain adapter, no think
    results["memory_plain"] = eval_pairs(be, w, eval_pairs_list,
                                         lambda x, y: QF.format(a=x, b=y),
                                         lora=lora_path)
    print("[mini] memory_plain:", results["memory_plain"], flush=True)
    # ---- rules articulation
    art = be.generate(["State the general rules of the crafting world you "
                       "have experienced, as a numbered list."],
                      max_tokens=500, lora_path=lora_path)[0]
    pathlib.Path("alchemy/v2_out/mini_articulation.txt").write_text(art)
    print("[mini] articulation saved", flush=True)
    json.dump(results, open(a.out, "w"), indent=1)
    print("[mini] DONE", flush=True)

if __name__ == "__main__":
    main()
