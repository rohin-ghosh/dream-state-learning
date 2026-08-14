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

from game import World, FeltCraft, scripted_optimal_play, scripted_noisy_play
from structmem_bench.metrics import average_precision
from .head import embed_events, hash_embed
from .fastweight import FastWeightMemory, value_modulated_weights


def _fact_key(t): return hash_embed("KEY::" + t, 32)
def _fact_val(t): return hash_embed("VAL::" + t, 32)


def collect_stream(world: World, head, n_episodes: int, d_h: int, seed: int,
                   detour_rate: float = 0.25):
    """Noisy rollouts (detours) so salience varies WITHIN action type — without
    this, action-type ≡ structural label and any type detector fakes the result
    (redteam_4). NO fallback salience: every fact must carry a real step."""
    known = set()
    K, V, S, lab, acts, kinds, texts = [], [], [], [], [], [], []
    goals = list(world.dag.recipes)
    for e in range(n_episodes):
        env = FeltCraft(world, max_steps=120)
        scripted_noisy_play(env, goals[e % len(goals)],
                            episode_seed=seed * 1000 + e,
                            known_locations=known,
                            detour_rate=detour_rate, seed=seed)
        known |= env.known_locations
        sal = head.salience(embed_events(env.trajectory, d_h)) \
            if env.trajectory else np.zeros(0)
        for f in env.episode_facts:
            assert f.step >= 1, "fact without a real step — fallback path is banned"
            K.append(_fact_key(f.text)); V.append(_fact_val(f.text))
            S.append(float(sal[f.step - 1])); lab.append(f.structural)
            acts.append(env.trajectory[f.step - 1]["action"].split(" ")[0])
            kinds.append(f.kind); texts.append(f.text)
    return {"K": np.stack(K), "V": np.stack(V), "S": np.array(S),
            "structural": np.array(lab, bool), "acts": np.array(acts),
            "kinds": np.array(kinds), "texts": texts}


def _weights(policy: str, sur: np.ndarray, S: np.ndarray, acts: np.ndarray,
             structural=None, texts=None, freqs=None):
    """sur = ONLINE surprise (computed per chunk against current memory —
    redteam_4 fix: pre-write surprise on a fresh net was init noise)."""
    n = len(sur)
    if policy == "uniform":
        # per-instance uniform mass ≈ distribution-matching storage (Isele&Cosgun's
        # winning heuristic, translated to per-write gain) — note 24
        return np.ones(n)
    if policy == "random_write":
        # d'Autume 2019: random selection matched surprisal at 50-90% budget cuts
        # in replay settings — OBLIGATORY null for any selective-write claim (note 24)
        return np.random.default_rng(int(sur.sum() * 1e6) % (2**31)).random(n)
    if policy == "surprise_only":
        return sur
    if policy == "dmem_style":                    # heuristic gate: top-surprise only
        z = (sur - sur.mean()) / (sur.std() + 1e-9)
        return sur * (z > 0.5)
    if policy == "keyword_gate":                  # PERMANENT CANARY (redteam_4):
        g = np.isin(acts, ("craft", "explore", "move")).astype(float)
        return sur * (1.0 + 12.0 * g)             # felt must BEAT this to mean anything
    if policy == "oracle_weight":                 # label REFERENCE (uses labels, declared)
        assert structural is not None
        return sur * (1.0 + 12.0 * structural.astype(float))
    if policy == "fact_type_regex":               # the cheap competitor a reviewer
        assert texts is not None                  # builds (reversal-6 audit): three
        g = np.array([("requires" in t) or ("is found at" in t)  # string matches
                      or ("always hold" in t) for t in texts], float)
        return sur * (1.0 + 12.0 * g)
    if policy == "frequency_weight":              # popularity control (reversal-6):
        assert freqs is not None                  # credit must beat raw frequency
        f = np.asarray(freqs, float)
        return sur * (1.0 + 12.0 * f / (f.max() or 1.0))
    if policy.startswith("felt_b"):
        beta = float(policy.split("felt_b")[1])
        return value_modulated_weights(sur, S, beta)
    raise ValueError(policy)


_FAKE_TPL = {
    "recipe":   "crafting zz{i}x requires zz{i}y and zz{i}z",
    "location": "zz{i}r is found at zz{i}site",
    "decor":    "zz{i}site looked zz{i}w during episode 9{i}9",
    "count":    "gathered zz{i}r at step 9{i} of episode 9{i}9",
    "hint":     "sites that look zz{i}w always hold zz{i}r",
}


def _floor_corrected_probe(mem, texts, kinds, tag: int):
    """Retention ABOVE the class floor (redteam_4 fix for the cosine-floor
    confound): score(fact) = cos(M(k),v) − cos on a NEVER-WRITTEN fake with the
    same template shape. Removes generic-similarity credit."""
    Kr = np.stack([_fact_key(t) for t in texts])
    Vr = np.stack([_fact_val(t) for t in texts])
    real = mem.probe(Kr, Vr)
    fakes = [_FAKE_TPL[k].format(i=tag * 1000 + j) for j, k in enumerate(kinds)]
    Kf = np.stack([_fact_key(t) for t in fakes])
    Vf = np.stack([_fact_val(t) for t in fakes])
    floor = mem.probe(Kf, Vf)
    return real - floor, real, floor


def run_probe_condition(world: World, head, policy: str, n_episodes: int,
                        d_h: int, seed: int) -> dict:
    st = collect_stream(world, head, n_episodes, d_h, seed)
    K, V, S = st["K"], st["V"], st["S"]
    structural, acts = st["structural"], st["acts"]

    # retrieval-family references (no parametric memory)
    if policy in ("no_memory", "context_fifo", "rag_unbounded"):
        gist = world.structural_facts()
        n_g = len(gist)
        K, structural = st["K"], st["structural"]
        if policy == "no_memory":
            return {"gist_retrieval": 0.0, "detail_retrieval": 0.0,
                    "dissociation": 0.0, "ap_gist": float("nan"),
                    "store_size": 0}
        if policy == "context_fifo":              # last B fact-instances verbatim
            B = n_g                                # budget matched to |gist|
            tail_texts = st["texts"][-B:]
            tail_struct = structural[-B:]
            # DISTINCT gist facts represented in the window (dedup — redteam_5)
            gist_texts = {f.text for f in gist}
            kept_gist = {t for t, is_s in zip(tail_texts, tail_struct)
                         if is_s and t in gist_texts}
            gist_kept = len(kept_gist) / max(1, n_g)
            det_kept = float((~tail_struct).sum()) / max(1, B)
            return {"gist_retrieval": float(gist_kept),
                    "detail_retrieval": det_kept,
                    "dissociation": float(gist_kept - det_kept),
                    "ap_gist": float("nan"), "store_size": B}
        # rag_unbounded: stores everything raw — perfect recall, unbounded cost
        return {"gist_retrieval": 1.0, "detail_retrieval": 1.0,
                "dissociation": 0.0, "ap_gist": float("nan"),
                "store_size": len(K)}

    # parametric memory policies (matched budget); ONLINE surprise per chunk
    mem = FastWeightMemory(d_key=32, d_val=32, hidden=128, seed=seed)  # h128: capacity where allocation can express (oracle diagnostic)
    chunk = max(1, len(K) // 8)
    for i in range(0, len(K), chunk):
        sl = slice(i, i + chunk)
        sur = mem.surprise(K[sl], V[sl])          # against CURRENT memory state
        labels = structural[sl] if policy == "oracle_weight" else None
        w = _weights(policy, sur, S[sl], acts[sl], labels)
        mem.write_batch(K[sl], V[sl], w, steps=15)

    # gist probes: the world's canonical structural facts (recipe+location)
    gist = world.structural_facts()
    g_corr, g_raw, g_floor = _floor_corrected_probe(
        mem, [f.text for f in gist], [f.kind for f in gist], tag=1)
    # detail probes: RANDOM sample of experienced detail instances (not first-N)
    rng = np.random.default_rng(seed * 61 + 17)
    det_pool = np.where(~structural)[0]
    if len(det_pool) == 0:
        return {"gist_retrieval": float(g_corr.mean()), "detail_retrieval":
                float("nan"), "dissociation": float("nan"),
                "ap_gist": float("nan"), "gist_floor": float(g_floor.mean()),
                "detail_floor": float("nan"),
                "store_size": int(mem.W1.size + mem.W2.size)}
    det_idx = rng.choice(det_pool, size=min(len(gist), len(det_pool)),
                         replace=False)
    d_corr, d_raw, d_floor = _floor_corrected_probe(
        mem, [st["texts"][i] for i in det_idx],
        [st["kinds"][i] for i in det_idx], tag=2)
    scores = np.concatenate([g_corr, d_corr])
    labels = np.array([True] * len(g_corr) + [False] * len(d_corr))
    return {"gist_retrieval": float(g_corr.mean()),
            "detail_retrieval": float(d_corr.mean()),
            "dissociation": float(g_corr.mean() - d_corr.mean()),
            "ap_gist": average_precision(scores, labels),
            "gist_floor": float(g_floor.mean()),
            "detail_floor": float(d_floor.mean()),
            "store_size": int(mem.W1.size + mem.W2.size)}


PROBE_POLICIES = ("uniform", "random_write", "surprise_only", "dmem_style",
                  "keyword_gate", "felt_b4", "felt_b12", "oracle_weight",
                  "no_memory", "context_fifo", "rag_unbounded")
