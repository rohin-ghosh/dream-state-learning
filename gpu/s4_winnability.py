"""S4 — the closed loop: memory conditions PLAY new episodes.

Per world, each write policy's memory is built from the S1 experience stream
(same machinery as S3), then the model plays FRESH episodes where its only
knowledge is the memory's top-k retained facts injected as context.
Rails: no-memory floor, full-manual ceiling. k-sweep separates retention
quality from read-slot squeeze.

Pre-registered prediction: no_memory < surprise_only < felt_fact ~ oracle
< manual; felt−surprise is the behavioral headline; the felt−surprise gap
shrinking at larger k = scarcity-advantage evidence (vision doc, bitter-
lesson calibration).

Usage (node):
  PYTHONPATH=. python gpu/s4_winnability.py --in gpu_artifacts/s1 \
      --fact-salience-npz gpu_artifacts/salience_fact.npz \
      --model Qwen/Qwen2.5-7B-Instruct --eps 25 --ks 12,18
"""

from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict

import numpy as np

from felt.fastweight import FastWeightMemory
from felt.baselines import _weights, _fact_key, _fact_val
from felt.llm_player import build_prompt, parse_action, render_manual
from game import World, FeltCraft
from gpu.rollouts import read_jsonl_tolerant

WRITE_POLICIES = ("surprise_only", "random_write", "fact_type_regex",
                  "felt_fact", "oracle_weight")


def build_topk_texts(recs, policy, fact_npz, k, seed=0):
    """Build the policy's memory from the world stream, then rank all unique
    experienced fact texts by the memory's probe score; return top-k texts."""
    K, V, S, structural, acts, texts = [], [], [], [], [], []
    for rec in recs:
        traj = rec["trajectory"]
        for j, fa in enumerate(rec["facts"]):
            if fa["step"] < 1 or fa["step"] - 1 >= len(traj):
                continue
            key = f"{rec['episode_uid']}_f{j}"
            s = float(fact_npz[key]) if (fact_npz is not None
                                         and key in fact_npz.files) else 0.0
            K.append(_fact_key(fa["text"])); V.append(_fact_val(fa["text"]))
            S.append(s); structural.append(fa["structural"])
            acts.append(traj[fa["step"] - 1]["action"].split(" ")[0])
            texts.append(fa["text"])
    K, V = np.stack(K), np.stack(V)
    S, structural = np.array(S), np.array(structural, bool)
    acts = np.array(acts)
    mem = FastWeightMemory(d_key=32, d_val=32, hidden=128, seed=seed)
    chunk = max(1, len(K) // 8)
    pol = "felt_b12" if policy == "felt_fact" else policy
    for i in range(0, len(K), chunk):
        sl = slice(i, i + chunk)
        sur = mem.surprise(K[sl], V[sl])
        labels = structural[sl] if policy == "oracle_weight" else None
        w = _weights(pol, sur, S[sl], acts[sl], labels,
                     texts=texts[sl.start:sl.stop if sl.stop else len(texts)])
        mem.write_batch(K[sl], V[sl], w, steps=15)
    # rank UNIQUE texts by probe score
    uniq = sorted(set(texts))
    uK = np.stack([_fact_key(t) for t in uniq])
    uV = np.stack([_fact_val(t) for t in uniq])
    scores = mem.probe(uK, uV)
    order = np.argsort(-scores)[:k]
    return [uniq[i] for i in order]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", default="gpu_artifacts/s1")
    ap.add_argument("--fact-salience-npz", required=True)
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--eps", type=int, default=25, help="episodes per arm per world")
    ap.add_argument("--ks", default="12,18")
    ap.add_argument("--par", type=int, default=32)
    ap.add_argument("--max-steps", type=int, default=120)
    ap.add_argument("--out", default="gpu_artifacts/s4.json")
    a = ap.parse_args()
    in_dir = pathlib.Path(a.in_dir)
    ks = [int(x) for x in a.ks.split(",")]

    fact_npz = np.load(a.fact_salience_npz)
    by_world = defaultdict(list)
    for rec in read_jsonl_tolerant(in_dir / "rollouts.jsonl"):
        by_world[rec["world"]].append(rec)

    # ---- build every arm's context block per world
    arms = []          # (world_obj, arm_name, ctx_block)
    for wid, recs in sorted(by_world.items()):
        world = World.generate(wid, seed=recs[0]["world_seed"],
                               depth=recs[0].get("depth", 4))
        arms.append((world, "no_memory", "CONTEXT: (none)"))
        arms.append((world, "manual", render_manual(world)))
        for pol in WRITE_POLICIES:
            for k in ks:
                texts = build_topk_texts(recs, pol, fact_npz, k)
                blk = "MEMORY (from past episodes):\n" + \
                    "\n".join(f"- {t}" for t in texts)
                arms.append((world, f"{pol}_k{k}", blk))
    print(f"[S4] {len(arms)} arms x {a.eps} eps")

    # ---- vLLM lockstep play
    import os
    os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
    llm = LLM(model=a.model, dtype="bfloat16", gpu_memory_utilization=0.85)
    sp = SamplingParams(max_tokens=320, temperature=0.5, top_p=0.9, seed=0)
    _tok = AutoTokenizer.from_pretrained(a.model)

    def chatify(p):
        try:
            return _tok.apply_chat_template([{"role": "user", "content": p}],
                                            tokenize=False,
                                            add_generation_prompt=True)
        except Exception:
            return p

    episodes = []
    for world, arm, ctx in arms:
        goals = world.goal_pool()
        rng = np.random.default_rng(hash(arm) % 2**31)
        for e in range(a.eps):
            goal = goals[int(rng.integers(len(goals)))]
            episodes.append({"world": world, "arm": arm, "goal": goal,
                             "ctx": f"Your goal: craft {goal}.\n{ctx}",
                             "seed": 50_000 + e})
    wins = defaultdict(list)
    for i0 in range(0, len(episodes), a.par):
        batch = []
        for spec in episodes[i0:i0 + a.par]:
            env = FeltCraft(spec["world"], max_steps=a.max_steps)
            env.reset(spec["goal"], episode_seed=spec["seed"])
            batch.append({**spec, "env": env, "hist": [],
                          "obs": "[step 0] You arrive."})
        active = list(batch)
        while active:
            prompts = [chatify(build_prompt(
                f'{b["obs"]} {b["env"].status_text()}', b["ctx"], b["hist"]))
                for b in active]
            outs = llm.generate(prompts, sp)
            nxt = []
            for b, o in zip(active, outs):
                act = parse_action(o.outputs[0].text)
                rec = b["env"].step(act)
                b["hist"].append((act, rec["obs"]))
                b["obs"] = rec["obs"]
                if not b["env"].done:
                    nxt.append(b)
            active = nxt
        for b in batch:
            wins[b["arm"]].append(bool(b["env"].success))
        done = min(i0 + a.par, len(episodes))
        print(f"[S4] {done}/{len(episodes)} episodes")
        # checkpoint partial results
        summary = {arm: {"win": float(np.mean(v)), "n": len(v)}
                   for arm, v in wins.items()}
        pathlib.Path(a.out).write_text(json.dumps(summary, indent=1))

    print(f"\n{'arm':<22}{'win':>7}{'n':>5}")
    for arm in sorted(wins):
        print(f"{arm:<22}{np.mean(wins[arm]):>7.3f}{len(wins[arm]):>5}")
    print(f"saved: {a.out}")


if __name__ == "__main__":
    main()
