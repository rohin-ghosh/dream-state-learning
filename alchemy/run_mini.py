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
general rule with the ingredients it covers; also state which ingredient
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
    kind = name = 0
    for (a, b), o in zip(pairs, outs):
        pred = parse_answer(o)
        t = w.predict(a, b)
        kind += pred[0] == t[0]
        if t[0] == "product":
            name += (t[1] or "") in o.lower()
    n = len(pairs)
    nprod = sum(w.predict(a, b)[0] == "product" for a, b in pairs) or 1
    return {"kind": kind / n, "name_mention": name / nprod, "n": n}

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
    eval_pairs_list = hp[:100]
    from alchemy.backend import make_backend
    be = make_backend(a.backend, a.model, enable_lora=(a.backend == "vllm"),
                      max_lora_rank=64) if a.backend == "vllm" else \
        make_backend(a.backend, a.model)
    results = {}
    # ---- 1) context player
    ctx = lambda x, y: f"Your full game experience:\n{log}\n\n" + QF.format(a=x, b=y)
    results["context"] = eval_pairs(be, w, eval_pairs_list, ctx)
    print("[mini] context:", results["context"], flush=True)
    # ---- 2) rag player
    obs_lines = [st["obs"] for ep in life for st in ep["log"]]
    idx = TfidfIndex(obs_lines)
    rag = lambda x, y: ("Relevant memories:\n" +
                        "\n".join(f"- {l}" for l in idx.topk(f"{x} {y}", 12)) +
                        "\n\n" + QF.format(a=x, b=y))
    results["rag"] = eval_pairs(be, w, eval_pairs_list, rag)
    print("[mini] rag:", results["rag"], flush=True)
    # ---- 3) dreamer -> verified corpus
    dreams_raw = be.generate([DREAM_PROMPT.format(log=log)], max_tokens=2000)[0]
    dreams = [l.strip("-* ") for l in dreams_raw.splitlines() if len(l.strip()) > 10]
    # engine verification: keep pair-claims only if correct; keep general
    # statements (they get spot-verified via the pairs they imply later)
    import re
    verified, dropped = [], 0
    for line in dreams:
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
    print(f"[mini] dreams: {len(dreams)} lines, {dropped} dropped by verifier", flush=True)
    pathlib.Path("alchemy/v2_out/mini_dreams.txt").write_text("\n".join(verified))
    # corpus: verified dreams + raw obs, augmented at measured recipe
    corpus = verified * 6 + obs_lines * 2
    # ---- LoRA at measured recipe
    if a.backend == "vllm":
        del be
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()
    from alchemy.lora_mem import load_base, train_lora
    base, tok = load_base(a.model)
    m = train_lora(base, tok, corpus, rank=64, epochs=3, lr=5e-4,
                   save_dir="alchemy/v2_out/mini_lora", log=print)
    del m, base
    import gc, torch
    gc.collect(); torch.cuda.empty_cache()
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
