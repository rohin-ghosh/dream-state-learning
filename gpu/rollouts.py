"""S1 — bulk rollout generation (vLLM lockstep across parallel envs) + hidden-state
caching for head training. The main inference spend of the lease.

Two passes:
  PASS A (vLLM, fast): N parallel FeltCraft envs stepped in lockstep; trajectories
         + facts logged to JSONL (same schema as game.generator + llm_player).
  PASS B (transformers, batched): unique event texts → multi-layer last-token
         hidden states → single .npz cache (text-key → vectors). Multi-layer per
         redteam_6 so the try-later-layers fallback needs no regeneration.

Usage:
  PYTHONPATH=. python gpu/rollouts.py --model Qwen/Qwen2.5-1.5B-Instruct \
      --episodes 2000 --par 32 --out gpu_artifacts/s1
Checkpointing: appends to the JSONL; resumes by skipping already-logged episode
indices; PASS B skips cached texts. Safe to kill/rerun.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

import numpy as np

from game import World
from game.engine import FeltCraft
from felt.llm_player import build_prompt, parse_action, render_manual

LAYERS = (-1, -4, -8)


def text_key(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def read_jsonl_tolerant(path) -> list:
    """Read rollouts JSONL, skipping a truncated tail line (P0-3: a kill mid-write
    must not brick resume/S2/S3) and deduping by episode_uid (resume re-appends)."""
    recs, seen = [], set()
    try:
        with open(path) as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue                     # truncated tail — skip
                uid = rec.get("episode_uid")
                if uid in seen:
                    continue
                seen.add(uid)
                recs.append(rec)
    except FileNotFoundError:
        pass
    return recs


# ---------------------------------------------------------------- PASS A
def run_rollouts(model: str, n_episodes: int, par: int, out_dir: pathlib.Path,
                 n_worlds: int = 4, depth: int = 4, max_steps: int = 60,
                 context_mode: str = "manual", seed: int = 0, branching: int = 3):
    """LLM plays with the MANUAL in context by default for S1 head-training data:
    we want competent play whose salience varies (right/wrong turns), and the
    manual removes the pure-ignorance failure mode. (Memory conditions are S3/S4.)"""
    import os
    # flashinfer is broken on py3.11 (array.array[int] TypeError at import) and
    # this vllm hard-imports it in the sampler check — turn that path off.
    os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
    llm = LLM(model=model, dtype="bfloat16", gpu_memory_utilization=0.85)
    sp = SamplingParams(max_tokens=320, temperature=0.0)  # ReAct: room to think
    # (cap only binds on rambles — EOS ends normal thoughts; free insurance for
    # memory-mode play where reasoning over partial facts runs longer)
    _tok = AutoTokenizer.from_pretrained(model)

    def chatify(p):
        """P1-6: Instruct models need the chat template, else format failures can
        fake a gate/quality failure."""
        try:
            return _tok.apply_chat_template([{"role": "user", "content": p}],
                                            tokenize=False,
                                            add_generation_prompt=True)
        except Exception:
            return p

    log_path = out_dir / "rollouts.jsonl"
    done_eps = {r["episode_uid"] for r in read_jsonl_tolerant(log_path)}

    world_seeds = {f"s1_{i}": seed * 7 + i for i in range(n_worlds)}
    worlds = [World.generate(w, seed=sd, depth=depth, branching=branching)
              for w, sd in world_seeds.items()]
    f = open(log_path, "a")
    ep = 0
    while ep < n_episodes:
        # build a lockstep batch of episodes
        batch = []
        while len(batch) < par and ep < n_episodes:
            uid = f"ep{ep:06d}"
            world = worlds[ep % n_worlds]
            goals = list(world.dag.recipes)
            goal = goals[(ep // n_worlds) % len(goals)]
            if uid not in done_eps:
                env = FeltCraft(world, max_steps=max_steps)
                env.reset(goal, episode_seed=ep)
                ctx = render_manual(world) if context_mode == "manual" \
                    else "CONTEXT: (none)"
                # goal in the PERSISTENT ctx, not the transient obs (S0 field
                # bug: goal rode only the first obs → goal-blind from step 2)
                ctx = f"Your goal: craft {goal}.\n{ctx}"
                batch.append({"uid": uid, "env": env, "world": world,
                              "goal": goal, "ctx": ctx, "hist": [],
                              "obs": "[step 0] You arrive."})
            ep += 1
        if not batch:
            continue
        active = list(batch)
        while active:
            prompts = [chatify(build_prompt(
                           f'{b["obs"]} {b["env"].status_text()}',
                           b["ctx"], b["hist"]))
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
            env = b["env"]
            f.write(json.dumps({
                "episode_uid": b["uid"], "world": b["world"].world_id,
                "world_seed": b["world"].seed, "depth": depth,
                "goal": b["goal"], "success": env.success, "steps": env.steps,
                "trajectory": env.trajectory,
                "facts": [{"text": fa.text, "kind": fa.kind,
                           "structural": fa.structural, "step": fa.step}
                          for fa in env.episode_facts],
            }) + "\n")
        f.flush()
        print(f"[S1-A] logged {ep}/{n_episodes} episodes")
    f.close()


# ---------------------------------------------------------------- PASS B
def cache_states(model: str, out_dir: pathlib.Path, batch_size: int = 64):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model)
    net = AutoModelForCausalLM.from_pretrained(
        model, torch_dtype=torch.bfloat16, device_map="cuda",
        output_hidden_states=True)
    net.eval()

    cache_path = out_dir / "states.npz"
    cached = {}
    if cache_path.exists():
        z = np.load(cache_path, allow_pickle=True)
        cached = {k: z[k] for k in z.files}

    texts = {}
    for rec in read_jsonl_tolerant(out_dir / "rollouts.jsonl"):
        for s in rec["trajectory"]:
            t = f"{s['action']} {s['obs']}"
            texts[text_key(t)] = t
    todo = [(k, t) for k, t in texts.items()
            if f"{k}_l{LAYERS[0]}" not in cached]
    print(f"[S1-B] {len(todo)} texts to embed ({len(texts)} total)")

    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "right"   # REQUIRED: last-non-pad indexing below assumes
    #                              right padding; some chat tokenizers default left
    for i in range(0, len(todo), batch_size):
        chunk = todo[i:i + batch_size]
        enc = tok([t for _, t in chunk], return_tensors="pt", padding=True,
                  truncation=True, max_length=256).to(net.device)
        with torch.inference_mode():
            out = net(**enc)
        # last NON-PAD token position per sequence
        lens = enc["attention_mask"].sum(dim=1) - 1
        for j, (k, _) in enumerate(chunk):
            for l in LAYERS:
                v = out.hidden_states[l][j, lens[j]].float().cpu().numpy()
                cached[f"{k}_l{l}"] = v
        if (i // batch_size) % 200 == 0 and i > 0:   # P0-2: throttled
            _atomic_savez(cache_path, cached)
            print(f"[S1-B] {i + len(chunk)}/{len(todo)}")
    _atomic_savez(cache_path, cached)
    print(f"[S1-B] cache complete: {cache_path}")


# ------------------------------------------------------- PASS B-ctx (audit fix)
def ctx_text(rec: dict, i: int, k_hist: int = 3) -> str:
    """Context-conditioned event text: goal + recent history + the event.
    Fixes the S2 aliasing artifact (field bug 4): the same event text recurs
    with different true salience (first discovery vs revisit) — embedded in
    isolation it carries conflicting labels, flooring ANY scorer at 0.122
    regret on the 0812 data. With context, the state is the model's situation
    DURING play — the thing the head was always meant to read."""
    traj = rec["trajectory"]
    parts = [f"Your goal: craft {rec['goal']}."]
    for t in traj[max(0, i - k_hist):i]:
        parts.append(f"> {t['action']}\n{t['obs']}")
    st = traj[i]
    parts.append(f"NOW: > {st['action']}\n{st['obs']}")
    return "\n".join(parts)


def cache_states_ctx(model: str, out_dir: pathlib.Path, batch_size: int = 32):
    """Per-INSTANCE hidden states, keyed (episode_uid, step) — no dedup, no
    aliasing. float16 (~2GB for 98k events x 3 layers)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model)
    net = AutoModelForCausalLM.from_pretrained(
        model, torch_dtype=torch.bfloat16, device_map="cuda",
        output_hidden_states=True)
    net.eval()

    cache_path = out_dir / "states_ctx.npz"
    cached = {}
    if cache_path.exists():
        z = np.load(cache_path, allow_pickle=True)
        cached = {k: z[k] for k in z.files}

    todo = []
    for rec in read_jsonl_tolerant(out_dir / "rollouts.jsonl"):
        for i in range(len(rec["trajectory"])):
            key = f"{rec['episode_uid']}_s{i}"
            if f"{key}_l{LAYERS[0]}" not in cached:
                todo.append((key, ctx_text(rec, i)))
    print(f"[S1-Bctx] {len(todo)} event instances to embed")

    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "right"
    for i in range(0, len(todo), batch_size):
        chunk = todo[i:i + batch_size]
        enc = tok([t for _, t in chunk], return_tensors="pt", padding=True,
                  truncation=True, max_length=512).to(net.device)
        with torch.inference_mode():
            out = net(**enc)
        lens = enc["attention_mask"].sum(dim=1) - 1
        for j, (k, _) in enumerate(chunk):
            for l in LAYERS:
                cached[f"{k}_l{l}"] = (out.hidden_states[l][j, lens[j]]
                                       .float().cpu().numpy().astype(np.float16))
        if (i // batch_size) % 400 == 0 and i > 0:
            _atomic_savez(cache_path, cached)
            print(f"[S1-Bctx] {i + len(chunk)}/{len(todo)}")
    _atomic_savez(cache_path, cached)
    print(f"[S1-Bctx] cache complete: {cache_path}")


# ---------------------------------------------------- PASS B-fact (note 26)
def cache_states_fact(model: str, out_dir: pathlib.Path, batch_size: int = 32):
    """Fact-in-context states: for each emitted fact, embed the emission
    moment's context + the PROPOSITION itself. Keyed (episode_uid, fact_idx).
    The head input for fact-level salience ('will this be load-bearing?')."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model)
    net = AutoModelForCausalLM.from_pretrained(
        model, torch_dtype=torch.bfloat16, device_map="cuda",
        output_hidden_states=True)
    net.eval()

    cache_path = out_dir / "states_fact.npz"
    cached = {}
    if cache_path.exists():
        z = np.load(cache_path, allow_pickle=True)
        cached = {k: z[k] for k in z.files}

    todo = []
    for rec in read_jsonl_tolerant(out_dir / "rollouts.jsonl"):
        for j, fa in enumerate(rec["facts"]):
            if fa["step"] < 1 or fa["step"] - 1 >= len(rec["trajectory"]):
                continue
            key = f"{rec['episode_uid']}_f{j}"
            if f"{key}_l{LAYERS[0]}" not in cached:
                text = (ctx_text(rec, fa["step"] - 1)
                        + f"\nFACT: {fa['text']}")
                todo.append((key, text))
    print(f"[S1-Bfact] {len(todo)} fact instances to embed")

    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "right"
    for i in range(0, len(todo), batch_size):
        chunk = todo[i:i + batch_size]
        enc = tok([t for _, t in chunk], return_tensors="pt", padding=True,
                  truncation=True, max_length=512).to(net.device)
        with torch.inference_mode():
            out = net(**enc)
        lens = enc["attention_mask"].sum(dim=1) - 1
        for j, (k, _) in enumerate(chunk):
            for l in LAYERS:
                cached[f"{k}_l{l}"] = (out.hidden_states[l][j, lens[j]]
                                       .float().cpu().numpy().astype(np.float16))
        if (i // batch_size) % 400 == 0 and i > 0:
            _atomic_savez(cache_path, cached)
            print(f"[S1-Bfact] {i + len(chunk)}/{len(todo)}")
    _atomic_savez(cache_path, cached)
    print(f"[S1-Bfact] cache complete: {cache_path}")


def _atomic_savez(path, cached):
    """P0-2: never overwrite the live cache in place — a kill mid-save must not
    corrupt PASS B progress."""
    import os
    tmp = str(path) + ".tmp.npz"
    np.savez(tmp, **cached)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--episodes", type=int, default=2000)
    ap.add_argument("--par", type=int, default=32)
    ap.add_argument("--out", default="gpu_artifacts/s1")
    ap.add_argument("--max-steps", type=int, default=60,
                    help="MUST match the step cap the S0 gate was passed at")
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--branching", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0,
                    help="world-generation seed base (fresh worlds = new seed)")
    ap.add_argument("--n-worlds", type=int, default=4)
    ap.add_argument("--skip-rollouts", action="store_true")
    ap.add_argument("--skip-states", action="store_true")
    ap.add_argument("--cache-ctx", action="store_true",
                    help="ONLY run PASS B-ctx (context-conditioned states)")
    ap.add_argument("--cache-fact", action="store_true",
                    help="ONLY run PASS B-fact (fact-in-context states)")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.cache_ctx:
        cache_states_ctx(a.model, out)
        return
    if a.cache_fact:
        cache_states_fact(a.model, out)
        return
    if not a.skip_rollouts:
        run_rollouts(a.model, a.episodes, a.par, out, max_steps=a.max_steps,
                     depth=a.depth, branching=a.branching, seed=a.seed,
                     n_worlds=a.n_worlds)
    if not a.skip_states:
        cache_states(a.model, out)


if __name__ == "__main__":
    main()
