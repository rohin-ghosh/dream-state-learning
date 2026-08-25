"""G2: oracle-in-weights + read-only adapter protocol. TRUE rules as
ideal statements -> adapter -> two read protocols vs context ceiling.
  PYTHONPATH=. python alchemy/mini_g2.py
"""
from __future__ import annotations
import json, pathlib, subprocess, sys
import numpy as np
from alchemy.mini import MiniWorld
from alchemy.evals import parse_answer

def true_statements(w):
    from collections import defaultdict
    groups = defaultdict(list)
    for n, t in w.type_of.items():
        groups[t].append(n)
    g = {t: sorted(v) for t, v in groups.items()}
    s = []
    for t in "ABCD":
        s.append(f"These ingredients all behave the same way: {', '.join(g[t])}.")
    s.append(f"Any ingredient from the group {', '.join(g['C'])} does nothing when combined with anything.")
    s.append("Combining two ingredients from the same behavior group ruins the mixture.")
    s.append(f"Ingredients from the group starting {g['A'][0]}, {g['A'][1]} make a product with ingredients from the group starting {g['B'][0]}, {g['B'][1]}.")
    s.append(f"Ingredients from the group starting {g['B'][0]}, {g['B'][1]} make a product with ingredients from the group starting {g['D'][0]}, {g['D'][1]}.")
    s.append("All other combinations do nothing.")
    # per-ingredient membership statements (redundant persp.)
    for t in "ABCD":
        for n in g[t]:
            others = [x for x in g[t] if x != n]
            s.append(f"{n} behaves exactly like {', '.join(others)}.")
    return s

QF = ("What happens when you combine {a} and {b}? UNKNOWN is not allowed — "
      "commit to your best answer. Answer with exactly one of: "
      "PRODUCT <name> | NOTHING | RUIN.")

def eval_arm(be, w, pairs, prompt_fn, lora=None):
    prompts = [prompt_fn(a, b) for a, b in pairs]
    outs = []
    for i in range(0, len(prompts), 64):
        outs += be.generate(prompts[i:i+64], max_tokens=220, lora_path=lora)
    by = {"product": [], "nothing": [], "ruin": []}
    for (a, b), o in zip(pairs, outs):
        t = w.predict(a, b)
        by[t[0]].append(parse_answer(o)[0] == t[0])
    r = {f"acc_{k}": round(sum(v)/len(v), 3) for k, v in by.items() if v}
    r["kind_bal"] = round(float(np.mean([sum(v)/len(v) for v in by.values() if v])), 3)
    return r

def main():
    model = "Qwen/Qwen2.5-7B-Instruct"
    w = MiniWorld(seed=0)
    hold = w.holdout(0.3, seed=0)
    stmts = true_statements(w)
    json.dump(stmts * 8, open("alchemy/v2_out/g2_corpus.json", "w"))
    print(f"[g2] {len(stmts)} true statements", flush=True)
    ings = w.ingredients[:8]
    code = f'''
import json
from alchemy.lora_mem import load_base, train_lora, read
corpus = json.load(open("alchemy/v2_out/g2_corpus.json"))
base, tok = load_base({model!r})
INGS = {ings!r}
for lr in (1e-4, 2e-4, 3e-4):
    m = train_lora(base, tok, list(corpus), rank=64, epochs=4, lr=lr,
                   save_dir=f"alchemy/v2_out/g2_lora_{{lr}}", log=print)
    probe = read(m, tok, "Which ingredients behave exactly like " + INGS[0] + "?", 80)
    print("[gate]", lr, "|", probe[:110])
    base = m.unload()
    if hasattr(base, "peft_config"): del base.peft_config
'''
    rc = subprocess.run([sys.executable, "-c", code]).returncode
    assert rc == 0
    from alchemy.backend import make_backend
    be = make_backend("vllm", model, enable_lora=True, max_lora_rank=64)
    rng = np.random.default_rng(3)
    hp = sorted(hold); rng.shuffle(hp)
    byk = {"product": [], "nothing": [], "ruin": []}
    for p in hp:
        byk[w.predict(*p)[0]].append(p)
    per = min(34, *(len(v) for v in byk.values()))
    pairs = sum((v[:per] for v in byk.values()), [])
    res = {}
    # ceiling: true statements in context
    st_text = "\n".join(stmts)
    res["statements_in_context"] = eval_arm(
        be, w, pairs, lambda a, b: f"What you know:\n{st_text}\n\n" + QF.format(a=a, b=b))
    print("[g2] statements_in_context:", res["statements_in_context"], flush=True)
    for lr in ("0.0001", "0.0002", "0.0003"):
        d = pathlib.Path(f"alchemy/v2_out/g2_lora_{lr}")
        if not (d / "adapter_config.json").exists():
            continue
        L = str(d.resolve())
        # (a) mounted answering
        res[f"mounted_{lr}"] = eval_arm(be, w, pairs,
                                        lambda a, b: QF.format(a=a, b=b), lora=L)
        print(f"[g2] mounted_{lr}:", res[f"mounted_{lr}"], flush=True)
        # (b) READ-ONLY: adapter emits memory block; clean base answers
        def ro(a, b, _L=L):
            reads = be.generate(
                [f"Which ingredients behave exactly like {a}, and what does {a} react with?",
                 f"Which ingredients behave exactly like {b}, and what does {b} react with?",
                 "State the general combination rules you remember."],
                max_tokens=120, lora_path=_L)
            return ("What you remember:\n" + "\n".join(reads) + "\n\n"
                    + QF.format(a=a, b=b))
        res[f"readonly_{lr}"] = eval_arm(be, w, pairs, ro)   # no lora on final
        print(f"[g2] readonly_{lr}:", res[f"readonly_{lr}"], flush=True)
    json.dump(res, open("alchemy/v2_out/mini_g2.json", "w"), indent=1)
    print("[g2] DONE", flush=True)

if __name__ == "__main__":
    main()
