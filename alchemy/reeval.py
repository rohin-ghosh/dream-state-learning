"""Priority-zero re-eval: re-ask held-out questions against EXISTING
artifacts (no retraining) with 3-level credit (exact/family/kind), 1000
stratified questions, fn/iid split. Answers: was family-level induction
hiding under exact-match zeros?
  PYTHONPATH=. python alchemy/reeval.py --run ~/v2/run/seed2 [--arms ...]
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np
from alchemy.world import AlchemyWorld
from alchemy.evals import Q, parse_answer, score_levels
from alchemy.rag import TfidfIndex, memory_block

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--points", default="960,3840,15360")
    ap.add_argument("--nq", type=int, default=1000)
    a = ap.parse_args()
    run = pathlib.Path(a.run)
    w = AlchemyWorld(n_ingredients=1024, n_inert=128, seed=a.seed,
                     n_essences=96, max_tier=4, rho_fn=0.4)
    hold = sorted(w.sample_holdout(0.3, seed=a.seed))
    rng = np.random.default_rng(11)
    rng.shuffle(hold)
    # stratify: half fn, half iid (reactive only), plus kind mix as-is
    fn = [p for p in hold if w.stratum_of(*p) == "fn"][:a.nq // 2]
    iid = [p for p in hold if w.stratum_of(*p) == "iid"][:a.nq // 2]
    pairs = fn + iid
    from alchemy.backend import make_backend
    be = make_backend("vllm", a.model, enable_lora=True, max_lora_rank=128)
    out = {}
    for E in a.points.split(","):
        raw = json.loads((run / f"corpus_raw_{E}.json").read_text())
        dr_f = run / f"corpus_dreamed_{E}.json"
        dreamed = json.loads(dr_f.read_text()) if dr_f.exists() else []
        arms = {
            "rag_raw": ("ctx", TfidfIndex(raw)),
            "rag_dreamed": ("ctx", TfidfIndex(dreamed or ["(x)"])),
        }
        for kind in ("raw", "dreamed"):
            d = run / f"lora_{kind}_{E}"
            if (d / "adapter_config.json").exists():
                arms[f"lora_{kind}"] = ("lora", str(d))
        for arm, (mode, obj) in arms.items():
            qs = [Q.format(a=x, b=y) for x, y in pairs]
            if mode == "ctx":
                prompts = [f"MEMORY:\n{memory_block(obj, q, 12)}\n\n{q}" for q in qs]
                outs = []
                for i in range(0, len(prompts), 64):
                    outs += be.generate(prompts[i:i+64], max_tokens=128)
            else:
                outs = []
                for i in range(0, len(qs), 64):
                    outs += be.generate(qs[i:i+64], max_tokens=128, lora_path=obj)
            res = {}
            for st_name, subset in (("fn", range(len(fn))),
                                    ("iid", range(len(fn), len(pairs)))):
                ex = fa = kd = n = 0
                for i in subset:
                    x, y = pairs[i]
                    e, f, k = score_levels(parse_answer(outs[i]), w.predict(x, y))
                    ex += e; fa += f; kd += k; n += 1
                res[st_name] = {"exact": ex/n, "family": fa/n, "kind": kd/n, "n": n}
            out[f"{E}:{arm}"] = res
            print(f"[reeval] E={E} {arm}: fn={res['fn']} iid={res['iid']}", flush=True)
    json.dump(out, open(run / "reeval_family.json", "w"), indent=1)

if __name__ == "__main__":
    main()
