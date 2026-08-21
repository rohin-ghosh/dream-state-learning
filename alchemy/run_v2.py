"""v2 harness — one seed, all arms, all checkpoints (SPEC_V2).

Three phases (memory-safe on one GPU):
  P1  life (free) + dream corpora for every checkpoint   [LLM: base]
  P2  LoRA trains (raw + dreamed x checkpoints)          [LLM down, peft up]
  P3  evals: held-out prediction, seen recall (G1), task play
                                                          [LLM: base + adapters]
Node:   CUDA_VISIBLE_DEVICES=g python alchemy/run_v2.py --seed g --backend vllm
Local:  python alchemy/run_v2.py --tiny --backend hf --model Qwen/Qwen2.5-0.5B-Instruct
Resumable: every artifact is a file; finished stages are skipped.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time

import numpy as np

from alchemy.world import AlchemyWorld
from alchemy.env import generate_life, seen_pairs, run_episode
from alchemy.player import ScriptedExplorer, build_prompt
from alchemy import dreamer, evals
from alchemy.rag import TfidfIndex, memory_block

ARMS = ("no_memory", "long_context", "rag_raw", "rag_dreamed",
        "lora_raw", "lora_dreamed", "lora_dreamed_multiread")


def cfg_from_args(a):
    if a.tiny:
        return dict(n_ingredients=24, n_inert=3, n_essences=6, inv=5,
                    points=[20, 60], eval_q=12, eval_eps=6, dream_chunk=10,
                    rank=8, epochs=3)
    return dict(n_ingredients=1024, n_inert=128, n_essences=96, inv=6,
                points=[60, 320, 960, 1920, 3840, 7680, 15360],
                eval_q=200, eval_eps=200, dream_chunk=96, rank=16, epochs=4)


def log(msg):
    print(f"[v2 {time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- phase 1
def phase1(world, holdout, C, out, backend, seed):
    life_f = out / "life.json"
    if life_f.exists():
        life = json.loads(life_f.read_text())
    else:
        life = generate_life(world, ScriptedExplorer(seed=seed),
                             C["points"][-1], inv_size=C["inv"],
                             seed=seed, holdout=holdout)
        assert not (seen_pairs(life) & holdout), "holdout violated"
        life_f.write_text(json.dumps(life))
    log(f"life: {len(life)} eps, success {np.mean([e['success'] for e in life]):.2f}")
    for E in C["points"]:
        for kind in ("raw", "dreamed"):
            f = out / f"corpus_{kind}_{E}.json"
            if f.exists():
                continue
            prefix = life[:E]
            if kind == "raw":
                corp = dreamer.dumb_dream(prefix)
            else:
                corp = dreamer.backend_dream(prefix, backend, world,
                                             chunk=C["dream_chunk"])
            leaks = [l for l in corp if world.leakage_scan(l)]
            assert not leaks, f"G2 leak: {leaks[:3]}"
            f.write_text(json.dumps(corp))
            log(f"corpus {kind}@{E}: {len(corp)} lines")
    return life


# ---------------------------------------------------------------- phase 2
def phase2(C, out, model_name):
    import torch  # noqa
    from alchemy.lora_mem import load_base, train_lora
    base, tok = None, None
    for E in C["points"]:
        for kind in ("raw", "dreamed"):
            d = out / f"lora_{kind}_{E}"
            if (d / "adapter_config.json").exists():
                continue
            if base is None:
                base, tok = load_base(model_name)
            corpus = json.loads((out / f"corpus_{kind}_{E}.json").read_text())
            if not corpus:
                log(f"lora {kind}@{E}: EMPTY corpus, skipped")
                continue
            log(f"lora {kind}@{E}: training on {len(corpus)} lines")
            m = train_lora(base, tok, corpus, rank=C["rank"],
                           epochs=C["epochs"], save_dir=str(d), log=log)
            base = m.unload()          # strip adapter, recover clean base
            # unload() leaves peft_config behind -> next get_peft_model
            # STACKS adapters (caught by tiny shakeout). Scrub it.
            if hasattr(base, "peft_config"):
                del base.peft_config


# ---------------------------------------------------------------- phase 3
def _ask_ctx(backend, questions, ctx_block, batch=64):
    prompts = [f"MEMORY:\n{ctx_block(q)}\n\n{q}" for q in questions]
    outs = []
    for i in range(0, len(prompts), batch):
        outs += backend.generate(prompts[i:i + batch], max_tokens=24)
    return outs


def eval_pairs_arm(backend, world, pairs, arm, ctx_fn, lora=None):
    from alchemy.evals import Q, parse_answer, score_pair
    questions = [Q.format(a=a, b=b) for a, b in pairs]
    if lora:
        outs = []
        for i in range(0, len(questions), 64):
            outs += backend.generate(questions[i:i + 64], max_tokens=24,
                                     lora_path=lora)
    else:
        outs = _ask_ctx(backend, questions, ctx_fn)
    scores, confab, abstain = [], 0, 0
    for (a, b), o in zip(pairs, outs):
        pred = parse_answer(o)
        s, c = score_pair(pred, world.predict(a, b))
        scores.append(s); confab += int(c)
        abstain += int(pred[0] == "unknown")
    n = max(len(pairs), 1)
    return {"score": float(np.mean(scores)) if scores else 0.0,
            "exact_acc": float(np.mean([s == 1.0 for s in scores])),
            "confab_rate": confab / n, "abstain_rate": abstain / n, "n": n}


class BackendPlayer:
    """Task-play player over the shared prompt (compute parity)."""

    def __init__(self, backend, lora=None):
        self.backend, self.lora = backend, lora

    def pick_pair(self, state, memory_ctx=""):
        import re
        txt = self.backend.generate([build_prompt(state, memory_ctx)],
                                    max_tokens=24, lora_path=self.lora)[0]
        m = re.search(r"COMBINE\s+([\w-]+)\s+(?:and\s+)?([\w-]+)", txt,
                      re.IGNORECASE)
        if not m:
            return None, None
        a, b = m.group(1), m.group(2)
        h = state["holdings"]
        return (a, b) if a in h and b in h else (None, None)


def task_success(backend, world, holdout, arm, ctx_text, lora, n_eps, inv,
                 seed):
    player = BackendPlayer(backend, lora=lora)
    wins = []
    # fresh winnable episode SPECS (target+inventory), new seed vs life
    probe = generate_life(world, ScriptedExplorer(seed=seed + 1), n_eps,
                          inv_size=inv, seed=seed + 50_000, holdout=holdout)
    for spec in probe:
        ep = run_episode(world, player, spec["target"], spec["inventory"],
                         memory_ctx=ctx_text(spec["target"]))
        wins.append(ep["success"])
    return float(np.mean(wins)) if wins else 0.0


def phase3(world, holdout, life, C, out, backend, seed):
    res_f = out / "results.json"
    results = json.loads(res_f.read_text()) if res_f.exists() else {}
    hold_pairs = sorted(holdout)
    rng = np.random.default_rng(seed)
    rng.shuffle(hold_pairs)
    hold_eval = [(b, a) if rng.random() < 0.5 else (a, b)
                 for a, b in hold_pairs[:C["eval_q"]]]
    for E in C["points"]:
        key = str(E)
        if key in results:
            continue
        prefix = life[:E]
        seen = sorted(seen_pairs(prefix))
        rng.shuffle(seen)
        seen_eval = [tuple(p) for p in seen[:C["eval_q"]]
                     if p[0] in world.ingredients and p[1] in world.ingredients]
        raw = json.loads((out / f"corpus_raw_{E}.json").read_text())
        dreamed_f = out / f"corpus_dreamed_{E}.json"
        dreamed = json.loads(dreamed_f.read_text()) if dreamed_f.exists() else []
        idx_raw, idx_dr = TfidfIndex(raw), TfidfIndex(dreamed or ["(empty)"])
        full_log = "\n".join(raw)
        n_log_tok = backend.n_tokens(full_log) if hasattr(backend, "n_tokens") \
            else len(full_log) // 4
        ctx_fits = n_log_tok < getattr(backend, "max_len", 32768) - 2048
        row = {}
        for arm in ARMS:
            lora = None
            if arm == "no_memory":
                ctx = lambda q: "(none)"
            elif arm == "long_context":
                if not ctx_fits:
                    row[arm] = {"na": True, "log_tokens": n_log_tok}
                    log(f"E={E} {arm}: N/A ({n_log_tok} tok > window)")
                    continue
                ctx = lambda q: full_log
            elif arm == "rag_raw":
                ctx = lambda q: memory_block(idx_raw, q, k=12)
            elif arm == "rag_dreamed":
                ctx = lambda q: memory_block(idx_dr, q, k=12)
            else:
                d = out / f"lora_{arm.split('_')[1]}_{E}"
                if not (d / "adapter_config.json").exists():
                    row[arm] = {"na": True, "reason": "no adapter"}
                    continue
                lora = str(d)
                if arm.endswith("multiread"):
                    # explicit read protocol: interrogate the memory with
                    # goal-conditioned queries, feed answers as context
                    def ctx(q, _l=lora):
                        reads = backend.generate(
                            [f"To craft {q}, what should you combine? "
                             "Answer from memory.",
                             f"What do you remember about {q} and how it is "
                             "made? Answer briefly.",
                             "List combinations you remember that produce "
                             "something, one per line, max 8."],
                            max_tokens=96, lora_path=_l)
                        return "\n".join(reads)
                else:
                    ctx = lambda q: "(in weights)"
            t0 = time.time()
            held = eval_pairs_arm(backend, world, hold_eval, arm, ctx, lora)
            recall = eval_pairs_arm(backend, world, seen_eval, arm, ctx, lora)
            ts = task_success(backend, world, holdout, arm, ctx, lora,
                              C["eval_eps"], C["inv"], seed)
            row[arm] = {"held_out": held, "seen_recall": recall,
                        "task_success": ts, "sec": round(time.time() - t0)}
            log(f"E={E} {arm}: held={held['score']:.2f} "
                f"recall={recall['exact_acc']:.2f} task={ts:.2f}")
        row["log_tokens"] = n_log_tok
        results[key] = row
        res_f.write_text(json.dumps(results, indent=1))
    log(f"DONE -> {res_f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--backend", choices=("hf", "vllm"), default="vllm")
    ap.add_argument("--tiny", action="store_true")
    ap.add_argument("--phase", default="all", choices=("all", "1", "2", "3"))
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    C = cfg_from_args(a)
    out = pathlib.Path(a.out or f"alchemy/v2_out/seed{a.seed}")
    out.mkdir(parents=True, exist_ok=True)
    world = AlchemyWorld(n_ingredients=C["n_ingredients"],
                         n_inert=C["n_inert"], seed=a.seed,
                         n_essences=C["n_essences"])
    holdout = world.sample_holdout(0.3, seed=a.seed)
    from alchemy.backend import make_backend
    if a.phase in ("all", "1"):
        be = make_backend(a.backend, a.model)
        life = phase1(world, holdout, C, out, be, a.seed)
        if a.backend == "vllm" and a.phase == "all":
            del be  # free GPU before peft
            import gc, torch
            gc.collect(); torch.cuda.empty_cache()
    if a.phase in ("all", "2"):
        phase2(C, out, a.model)
    if a.phase in ("all", "3"):
        kw = {"enable_lora": True} if a.backend == "vllm" else {}
        be = make_backend(a.backend, a.model, **kw)
        life = json.loads((out / "life.json").read_text())
        phase3(world, holdout, life, C, out, be, a.seed)


if __name__ == "__main__":
    main()
