"""Cycle-5: consolidation-focused loop. Dreams-only corpus, LR ladder
UP with a two-sided imprint gate (coherent AND domain-mentioning), then
memory-arm eval. Reuses c4 artifacts.
  PYTHONPATH=. python alchemy/mini_consolidate.py --eps 200
"""
from __future__ import annotations
import argparse, json, pathlib, subprocess, sys
import numpy as np
from alchemy.mini import MiniWorld, gen_life, life_text
from alchemy.evals import parse_answer

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--eps", type=int, default=200)
    ap.add_argument("--dreams", default="alchemy/v2_out/mini_dreams.txt")
    ap.add_argument("--out", default="alchemy/v2_out/mini_c5.json")
    a = ap.parse_args()
    w = MiniWorld(seed=0)
    hold = w.holdout(0.3, seed=0)
    dreams = [l for l in open(a.dreams).read().splitlines() if len(l) > 10]
    print(f"[c5] {len(dreams)} dream lines", flush=True)
    # dreams-only corpus + light QA slice derived FROM dreams
    corpus = dreams * 4
    json.dump(corpus, open("alchemy/v2_out/c5_corpus.json", "w"))
    ings = " ".join(w.ingredients[:6])
    code = f'''
import json
from alchemy.lora_mem import load_base, train_lora, read
corpus = json.load(open("alchemy/v2_out/c5_corpus.json"))
base, tok = load_base({a.model!r})
INGS = {w.ingredients[:8]!r}
best = None
for lr in (1e-4, 2e-4, 3e-4, 5e-4):
    m = train_lora(base, tok, list(corpus), rank=64, epochs=4, lr=lr,
                   save_dir=f"alchemy/v2_out/c5_lora_{{lr}}", log=print)
    probe = read(m, tok, "Tell me about " + INGS[0] + " and what it combines with.", 80)
    words = probe.split()
    coherent = len(set(words)) > max(3, len(words)//3)
    domain = any(i in probe.lower() for i in INGS)
    print("[gate]", lr, "coherent" if coherent else "SALAD",
          "domain" if domain else "BOILERPLATE", "|", probe[:100])
    base = m.unload()
    if hasattr(base, "peft_config"): del base.peft_config
    if coherent and domain:
        best = lr
        print("[gate] IMPRINTED at", lr)
        break
print("[c5] best_lr", best)
'''
    rc = subprocess.run([sys.executable, "-c", code]).returncode
    assert rc == 0
    print("[c5] training ladder done — eval phase", flush=True)
    # find which adapter passed (last saved with best lr per stdout; simplest: test each)
    from alchemy.backend import make_backend
    be = make_backend("vllm", a.model, enable_lora=True, max_lora_rank=64)
    rng = np.random.default_rng(3)
    hp = sorted(hold); rng.shuffle(hp)
    byk = {"product": [], "nothing": [], "ruin": []}
    for p in hp:
        byk[w.predict(*p)[0]].append(p)
    per = min(34, *(len(v) for v in byk.values()))
    pairs = sum((v[:per] for v in byk.values()), [])
    QF = ("What happens when you combine {a} and {b}? UNKNOWN is not "
          "allowed — commit to your best answer. Answer with exactly one "
          "of: PRODUCT <name> | NOTHING | RUIN.")
    res = {}
    for lr in ("0.0001", "0.0002", "0.0003", "0.0005"):
        d = pathlib.Path(f"alchemy/v2_out/c5_lora_{lr}")
        if not (d / "adapter_config.json").exists():
            continue
        qs = [QF.format(a=x, b=y) for x, y in pairs]
        outs = []
        for i in range(0, len(qs), 64):
            outs += be.generate(qs[i:i+64], max_tokens=200, lora_path=str(d.resolve()))
        by = {"product": [], "nothing": [], "ruin": []}
        for (x, y), o in zip(pairs, outs):
            t = w.predict(x, y)
            by[t[0]].append(parse_answer(o)[0] == t[0])
        r = {f"acc_{k}": round(sum(v)/len(v), 3) for k, v in by.items() if v}
        r["kind_bal"] = round(float(np.mean([sum(v)/len(v) for v in by.values() if v])), 3)
        res[lr] = r
        print(f"[c5] lr={lr}: {r}", flush=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print("[c5] DONE", flush=True)

if __name__ == "__main__":
    main()
