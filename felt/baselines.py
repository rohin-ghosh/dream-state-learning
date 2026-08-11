"""Baseline write-policy zoo for the probe tier (PREWORK item 8).

All policies allocate the SAME write budget into the same fast-weight memory —
pure allocation comparison (exp4 discipline). Retrieval-family baselines
(no-memory, context-at-budget FIFO, unbounded RAG store) are included as
probe-tier references with their memory cost reported.

CPU-tier note: `dmem_style` is the training-free heuristic gate (surprise z-score
threshold), the CPU stand-in for D-MEM's surprise×prompted-utility (verified
training-free by direct read, note 23). The prompted-utility half needs an LLM —
GPU tier upgrades this baseline to the faithful version.
"""

from __future__ import annotations

import numpy as np

from game import World, FeltCraft, scripted_optimal_play
from structmem_bench.metrics import average_precision
from .head import embed_events, hash_embed
from .fastweight import FastWeightMemory, value_modulated_weights


def _fact_key(t): return hash_embed("KEY::" + t, 32)
def _fact_val(t): return hash_embed("VAL::" + t, 32)


def collect_stream(world: World, head, n_episodes: int, d_h: int, seed: int):
    known = set()
    K, V, S, lab = [], [], [], []
    goals = list(world.dag.recipes)
    for e in range(n_episodes):
        env = FeltCraft(world, max_steps=120)
        scripted_optimal_play(env, goals[e % len(goals)],
                              episode_seed=seed * 1000 + e,
                              known_locations=known)
        known |= env.known_locations
        sal = head.salience(embed_events(env.trajectory, d_h)) \
            if env.trajectory else np.zeros(0)
        for f in env.episode_facts:
            s = float(sal[f.step - 1]) if 0 <= f.step - 1 < len(sal) else 0.05
            K.append(_fact_key(f.text)); V.append(_fact_val(f.text))
            S.append(s); lab.append(f.structural)
    return np.stack(K), np.stack(V), np.array(S), np.array(lab, bool)


def _weights(policy: str, mem: FastWeightMemory, K, V, S):
    if policy == "uniform":
        return np.ones(len(K))
    sur = mem.surprise(K, V)
    if policy == "surprise_only":
        return sur
    if policy == "dmem_style":                    # heuristic gate: top-surprise only
        z = (sur - sur.mean()) / (sur.std() + 1e-9)
        return sur * (z > 0.5)
    if policy.startswith("felt_b"):
        beta = float(policy.split("felt_b")[1])
        return value_modulated_weights(sur, S, beta)
    raise ValueError(policy)


def run_probe_condition(world: World, head, policy: str, n_episodes: int,
                        d_h: int, seed: int) -> dict:
    K, V, S, structural = collect_stream(world, head, n_episodes, d_h, seed)

    # retrieval-family references (no parametric memory)
    if policy in ("no_memory", "context_fifo", "rag_unbounded"):
        gist = world.structural_facts()
        n_g = len(gist)
        if policy == "no_memory":
            return {"gist_retrieval": 0.0, "detail_retrieval": 0.0,
                    "dissociation": 0.0, "ap_gist": float("nan"),
                    "store_size": 0}
        if policy == "context_fifo":              # last B fact-instances verbatim
            B = n_g                                # budget matched to |gist|
            kept = set(range(max(0, len(K) - B), len(K)))
            g_hit = np.mean([1.0 if any(i in kept and structural[i]
                                        for i in range(len(K))) else 0.0])
            # verbatim FIFO: retention = fraction of gist facts among last B
            gist_kept = structural[-B:].sum() / max(1, n_g)
            det_kept = (~structural[-B:]).sum() / max(1, B)
            return {"gist_retrieval": float(gist_kept),
                    "detail_retrieval": float(det_kept),
                    "dissociation": float(gist_kept - det_kept),
                    "ap_gist": float("nan"), "store_size": B}
        # rag_unbounded: stores everything raw — perfect recall, unbounded cost
        return {"gist_retrieval": 1.0, "detail_retrieval": 1.0,
                "dissociation": 0.0, "ap_gist": float("nan"),
                "store_size": len(K)}

    # parametric memory policies (matched budget)
    mem = FastWeightMemory(d_key=32, d_val=32, hidden=48, seed=seed)
    w = _weights(policy, mem, K, V, S)
    chunk = max(1, len(K) // 8)
    for i in range(0, len(K), chunk):
        sl = slice(i, i + chunk)
        mem.write_batch(K[sl], V[sl], w[sl], steps=15)

    gist = world.structural_facts()
    gk = np.stack([_fact_key(f.text) for f in gist])
    gv = np.stack([_fact_val(f.text) for f in gist])
    g = mem.probe(gk, gv)
    det_idx = np.where(~structural)[0][:len(gist)]
    d = mem.probe(K[det_idx], V[det_idx])
    scores = np.concatenate([g, d])
    labels = np.array([True] * len(g) + [False] * len(d))
    return {"gist_retrieval": float(g.mean()),
            "detail_retrieval": float(d.mean()),
            "dissociation": float(g.mean() - d.mean()),
            "ap_gist": average_precision(scores, labels),
            "store_size": int(mem.W1.size + mem.W2.size)}


PROBE_POLICIES = ("uniform", "surprise_only", "dmem_style", "felt_b4", "felt_b12",
                  "no_memory", "context_fifo", "rag_unbounded")
