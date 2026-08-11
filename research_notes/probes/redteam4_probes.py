"""Red-team probes for exp6 / felt/baselines.py (redteam_4).

Attacks:
  A. action-keyword confound (trivial keyword gate vs trained head)
  B. why is uniform's dissociation NEGATIVE (probe-set composition, value clustering,
     recurrence, recency)
  C. write-budget fairness (w/w.mean() per chunk)
  D. trivial zero-information policies
  E. head-eval inflation (action-type-only predictor)

Run: cd /Users/rohing/dream-state && PYTHONPATH=. python3 research_notes/probes/redteam4_probes.py
"""
from __future__ import annotations

import json
from collections import Counter

import numpy as np

from game import generate_dataset, World, FeltCraft, scripted_optimal_play
from felt import (train_head_on_dataset, eval_head, embed_events, hash_embed,
                  FastWeightMemory, value_modulated_weights)
from felt.head import normalize_salience, all_budgets_regret
from structmem_bench.metrics import average_precision

SEEDS = 8
D_H = 64
N_EP = 30


def fact_key(t): return hash_embed("KEY::" + t, 32)
def fact_val(t): return hash_embed("VAL::" + t, 32)


def collect(world, n_episodes, head, seed):
    """exp6's collect_fact_stream + per-fact action string and episode index."""
    known = set()
    K, V, S, lab, texts, actions, eps, kinds = [], [], [], [], [], [], [], []
    goals = list(world.dag.recipes)
    for e in range(n_episodes):
        env = FeltCraft(world, max_steps=120)
        scripted_optimal_play(env, goals[e % len(goals)],
                              episode_seed=seed * 1000 + e, known_locations=known)
        known |= env.known_locations
        H = embed_events(env.trajectory, D_H) if env.trajectory else None
        sal = head.salience(H) if H is not None else np.zeros(0)
        for f in env.episode_facts:
            i = f.step - 1
            s = float(sal[i]) if 0 <= i < len(sal) else 0.05
            act = env.trajectory[i]["action"] if 0 <= i < len(env.trajectory) else "<setup>"
            K.append(fact_key(f.text)); V.append(fact_val(f.text))
            S.append(s); lab.append(f.structural); texts.append(f.text)
            actions.append(act.split()[0] if act != "<setup>" else "<setup>")
            eps.append(e); kinds.append(f.kind)
    return (np.stack(K), np.stack(V), np.array(S), np.array(lab, bool),
            texts, actions, np.array(eps), kinds)


def run_mem(world, K, V, w, structural, seed, det_idx=None):
    """exp6's run_condition given explicit weights."""
    mem = FastWeightMemory(d_key=32, d_val=32, hidden=48, seed=seed)
    chunk = max(1, len(K) // 8)
    for i in range(0, len(K), chunk):
        sl = slice(i, i + chunk)
        mem.write_batch(K[sl], V[sl], w[sl], steps=15)
    gist = world.structural_facts()
    gk = np.stack([fact_key(f.text) for f in gist])
    gv = np.stack([fact_val(f.text) for f in gist])
    g = mem.probe(gk, gv)
    if det_idx is None:
        det_idx = np.where(~structural)[0][:len(gist)]
    d = mem.probe(K[det_idx], V[det_idx])
    scores = np.concatenate([g, d])
    labels = np.array([True] * len(g) + [False] * len(d))
    return {"gist": float(g.mean()), "det": float(d.mean()),
            "dissoc": float(g.mean() - d.mean()),
            "ap": average_precision(scores, labels), "mem": mem}


def weights_for(policy, mem_seed, K, V, S, actions, texts, structural, kinds):
    mem = FastWeightMemory(d_key=32, d_val=32, hidden=48, seed=mem_seed)
    sur = mem.surprise(K, V)
    gate_kw = np.array([1.0 if a in ("craft", "explore") else 0.0 for a in actions])
    if policy == "uniform":
        return np.ones(len(K))
    if policy == "surprise_only":
        return sur
    if policy == "felt_b12":
        return value_modulated_weights(sur, S, 12.0)
    if policy == "kw_gate_b12":          # TRIVIAL: felt form, salience := keyword gate
        return value_modulated_weights(sur, gate_kw, 12.0)
    if policy == "kw_gate_pure":         # even simpler: no surprise term at all
        return 1.0 + 12.0 * gate_kw
    if policy == "kind_leak":            # label-leak upper bound (uses fact kind)
        g = np.array([1.0 if k in ("recipe", "location") else 0.0 for k in kinds])
        return 1.0 + 12.0 * g
    if policy == "no_digit":             # text has no digits => boost
        g = np.array([0.0 if any(c.isdigit() for c in t) else 1.0 for t in texts])
        return 1.0 + 12.0 * g
    if policy == "short_text":           # fewer words => boost
        L = np.array([len(t.split()) for t in texts], float)
        return 1.0 / L
    if policy == "frequency":            # recurrence count of exact text
        c = Counter(texts)
        return np.array([float(c[t]) for t in texts])
    if policy == "recency":              # later position => boost
        return np.linspace(0.1, 1.0, len(K))
    if policy == "early":                # earlier position => boost
        return np.linspace(1.0, 0.1, len(K))
    raise ValueError(policy)


def main():
    rng = np.random.default_rng(0)
    print("=" * 78)
    print("SETUP: train head exactly as exp6")
    r = generate_dataset("/tmp/exp6_train.jsonl", n_worlds=3,
                         episodes_per_world=25, seed=100, depth=4)
    recs = [json.loads(l) for l in open(r["path"])]
    head = train_head_on_dataset(recs, d_h=D_H, epochs=40, seed=0)
    hq = eval_head(head, recs[-15:], d_h=D_H)
    print(f"head held-out: regret={hq['all_budgets_regret']:.3f} corr={hq['salience_corr']:.3f}")

    # =========================== ATTACK E: head vs action-type-only predictor ===
    print("\n" + "=" * 78)
    print("ATTACK E/1: is head salience just action type?")
    # per-action-type mean normalized salience on TRAIN records
    by_act = {}
    for rec in recs[:-15]:
        t = normalize_salience(rec["trajectory"])
        for st, s in zip(rec["trajectory"], t):
            by_act.setdefault(st["action"].split()[0], []).append(s)
    act_mean = {a: float(np.mean(v)) for a, v in by_act.items()}
    print(f"train mean normalized oracle salience by action: "
          f"{ {a: round(m,3) for a,m in sorted(act_mean.items())} }")
    regs, corrs, hcorr, aucs = [], [], [], []
    for rec in recs[-15:]:
        traj = rec["trajectory"]
        if len(traj) < 3:
            continue
        H = embed_events(traj, D_H)
        a = head.salience(H)
        t = normalize_salience(traj)
        pred = np.array([act_mean.get(st["action"].split()[0], 0.5) for st in traj])
        regs.append(all_budgets_regret(pred, t))
        if t.std() > 0 and pred.std() > 0:
            corrs.append(float(np.corrcoef(pred, t)[0, 1]))
        if a.std() > 0 and pred.std() > 0:
            hcorr.append(float(np.corrcoef(a, pred)[0, 1]))
        # AUC: head salience separating craft/explore steps from others
        is_ce = np.array([st["action"].split()[0] in ("craft", "explore") for st in traj])
        if is_ce.any() and (~is_ce).any():
            p, n = a[is_ce], a[~is_ce]
            aucs.append(float((p[:, None] > n[None, :]).mean()))
    print(f"action-type-ONLY predictor (5 numbers, no embeddings): "
          f"regret={np.mean(regs):.3f}  corr(target)={np.mean(corrs):.3f}")
    print(f"trained head:                                     "
          f"regret={hq['all_budgets_regret']:.3f}  corr(target)={hq['salience_corr']:.3f}")
    print(f"corr(head salience, action-type prediction) on held-out eps: {np.mean(hcorr):.3f}")
    print(f"AUC of head salience classifying craft/explore steps:        {np.mean(aucs):.3f}")

    # =========================== fact-tier structure ============================
    print("\n" + "=" * 78)
    print("STRUCTURE: what determines each fact's salience input?")
    world0 = World.generate("held_0", seed=900, depth=4)
    K, V, S, structural, texts, actions, eps, kinds = collect(world0, N_EP, head, seed=0)
    print(f"n facts={len(K)}  structural={structural.sum()}  detail={(~structural).sum()}")
    for kind in ("recipe", "location", "decor", "count"):
        m = np.array([k == kind for k in kinds])
        acts = Counter(np.array(actions)[m].tolist())
        print(f"  kind={kind:<9} n={m.sum():>4}  action(s) at fact step: {dict(acts)}  "
              f"head salience mean={S[m].mean():.3f}")
    # head salience vs keyword gate agreement AT THE FACT LEVEL
    gate = np.array([1.0 if a in ("craft", "explore") else 0.0 for a in actions])
    print(f"fact-level corr(head salience S, craft/explore gate) = "
          f"{np.corrcoef(S, gate)[0,1]:.3f}")
    p, n = S[gate == 1], S[gate == 0]
    print(f"fact-level AUC(gate | S) = {float((p[:,None] > n[None,:]).mean()):.3f}")
    # and vs the structural LABEL itself
    print(f"fact-level corr(S, structural label) = "
          f"{np.corrcoef(S, structural.astype(float))[0,1]:.3f}")

    # =========================== ATTACKS A + D: policy zoo ======================
    print("\n" + "=" * 78)
    print("ATTACKS A/4: trivial policies through the exp6 pipeline (8 seeds)")
    POLS = ["uniform", "surprise_only", "felt_b12", "kw_gate_b12", "kw_gate_pure",
            "kind_leak", "no_digit", "short_text", "frequency", "recency", "early"]
    agg = {p: {"dissoc": [], "ap": [], "gist": [], "det": []} for p in POLS}
    wcorr_felt_kw = []
    for s in range(SEEDS):
        world = World.generate(f"held_{s}", seed=900 + s, depth=4)
        K, V, S, structural, texts, actions, eps, kinds = collect(world, N_EP, head, seed=s)
        for p in POLS:
            w = weights_for(p, s, K, V, S, actions, texts, structural, kinds)
            m = run_mem(world, K, V, w, structural, seed=s)
            for k in ("dissoc", "ap", "gist", "det"):
                agg[p][k].append(m[k])
        wf = weights_for("felt_b12", s, K, V, S, actions, texts, structural, kinds)
        wk = weights_for("kw_gate_b12", s, K, V, S, actions, texts, structural, kinds)
        wcorr_felt_kw.append(float(np.corrcoef(wf, wk)[0, 1]))
    print(f"\n{'policy':<15}{'gist':>8}{'det':>8}{'dissoc':>9}{'AP':>8}")
    for p in POLS:
        a = agg[p]
        print(f"{p:<15}{np.mean(a['gist']):>8.3f}{np.mean(a['det']):>8.3f}"
              f"{np.mean(a['dissoc']):>9.3f}{np.mean(a['ap']):>8.3f}")
    from structmem_bench.stats import paired_diff
    d = paired_diff(np.array(agg["kw_gate_b12"]["dissoc"]),
                    np.array(agg["felt_b12"]["dissoc"]))
    print(f"\npaired kw_gate_b12 - felt_b12 dissociation: {d['mean']:+.3f} "
          f"(SE {d['se']:.3f}, t={d['t']:.1f})")
    print(f"corr(felt_b12 weights, kw_gate_b12 weights) per seed: "
          f"mean={np.mean(wcorr_felt_kw):.3f}  min={np.min(wcorr_felt_kw):.3f}")

    # =========================== ATTACK B: uniform's negative dissociation ======
    print("\n" + "=" * 78)
    print("ATTACK B/2: why does UNIFORM retain detail > gist?")
    s = 0
    world = World.generate("held_0", seed=900, depth=4)
    K, V, S, structural, texts, actions, eps, kinds = collect(world, N_EP, head, seed=s)
    gist = world.structural_facts()
    n_g = len(gist)
    det_idx = np.where(~structural)[0][:n_g]
    print(f"|gist probes|={n_g}  det_idx = first {n_g} detail instances")
    print(f"det_idx composition: kinds={Counter([kinds[i] for i in det_idx])}, "
          f"episodes={Counter(eps[det_idx].tolist())}")
    # recurrence of the probed texts in the whole stream
    c = Counter(texts)
    det_rec = [c[texts[i]] for i in det_idx]
    gist_rec = [c[f.text] for f in gist]
    print(f"stream recurrence of probed DETAIL texts: mean={np.mean(det_rec):.1f} "
          f"(min={min(det_rec)}, max={max(det_rec)})")
    print(f"stream recurrence of probed GIST texts:   mean={np.mean(gist_rec):.1f} "
          f"(min={min(gist_rec)}, max={max(gist_rec)})  "
          f"[0 = probe never experienced/written]")
    by_kind_rec = {}
    for f in gist:
        by_kind_rec.setdefault(f.kind, []).append(c[f.text])
    for k, v in by_kind_rec.items():
        print(f"   gist kind={k:<9} recurrence mean={np.mean(v):.1f} "
              f"never-written={sum(x==0 for x in v)}/{len(v)}")
    # last chunk each probed text appears in (recency under 8-chunk writes)
    chunk = max(1, len(K) // 8)
    last_pos = {}
    for i, t in enumerate(texts):
        last_pos[t] = i // chunk
    det_last = [last_pos[texts[i]] for i in det_idx]
    gist_last = [last_pos.get(f.text, -1) for f in gist]
    print(f"last write-chunk (0..7) of DETAIL probes: mean={np.mean(det_last):.2f} "
          f"{sorted(Counter(det_last).items())}")
    print(f"last write-chunk of GIST probes:          mean={np.mean(gist_last):.2f} "
          f"{sorted(Counter(gist_last).items())}  (-1 = never written)")

    # value-vector geometry: is detail cosine cheap?
    gv = np.stack([fact_val(f.text) for f in gist])
    dv = V[det_idx]
    def mean_offdiag_cos(M):
        C = M @ M.T
        n = len(M)
        return float((C.sum() - np.trace(C)) / (n * (n - 1)))
    print(f"mean pairwise cosine among GIST values:   {mean_offdiag_cos(gv):.3f}")
    print(f"mean pairwise cosine among DETAIL values: {mean_offdiag_cos(dv):.3f}")
    mu_all = V.mean(axis=0)
    mu_all /= np.linalg.norm(mu_all)
    print(f"cosine(stream-mean value, gist values):   {float((gv @ mu_all).mean()):.3f}")
    print(f"cosine(stream-mean value, detail values): {float((dv @ mu_all).mean()):.3f}")

    # untrained-memory floor + never-written controls
    mem0 = FastWeightMemory(d_key=32, d_val=32, hidden=48, seed=s)
    gk = np.stack([fact_key(f.text) for f in gist])
    print(f"UNTRAINED memory probe: gist={mem0.probe(gk, gv).mean():.3f} "
          f"detail={mem0.probe(K[det_idx], dv).mean():.3f}")
    # after uniform writes: never-written fake facts of each style
    m_uni = run_mem(world, K, V, np.ones(len(K)), structural, seed=s)
    mem = m_uni["mem"]
    fake_det = [f"site_{i%8} looked shimmering during episode {9000+i}" for i in range(n_g)]
    fake_gist = [f"crafting z{i}_x requires q_{i} and z_{i}" for i in range(n_g)]
    fk = np.stack([fact_key(t) for t in fake_det]); fv = np.stack([fact_val(t) for t in fake_det])
    gk2 = np.stack([fact_key(t) for t in fake_gist]); gv2 = np.stack([fact_val(t) for t in fake_gist])
    print(f"UNIFORM-trained memory, NEVER-WRITTEN probes: "
          f"fake-detail={mem.probe(fk, fv).mean():.3f}  fake-gist={mem.probe(gk2, gv2).mean():.3f}")
    print(f"(vs its real probes: gist={m_uni['gist']:.3f} detail={m_uni['det']:.3f})")

    # det_idx choice ablation across seeds: first-N vs last-N vs random-N details
    print("\ndet_idx ablation (8 seeds, uniform + felt_b12):")
    res = {p: {c: [] for c in ("first", "random", "last")} for p in ("uniform", "felt_b12")}
    for s2 in range(SEEDS):
        w2 = World.generate(f"held_{s2}", seed=900 + s2, depth=4)
        K2, V2, S2, st2, tx2, ac2, ep2, kd2 = collect(w2, N_EP, head, seed=s2)
        gist2 = w2.structural_facts()
        dall = np.where(~st2)[0]
        rng2 = np.random.default_rng(s2)
        choices = {"first": dall[:len(gist2)], "last": dall[-len(gist2):],
                   "random": rng2.choice(dall, size=len(gist2), replace=False)}
        for p in ("uniform", "felt_b12"):
            wgt = weights_for(p, s2, K2, V2, S2, ac2, tx2, st2, kd2)
            for cname, di in choices.items():
                m = run_mem(w2, K2, V2, wgt, st2, seed=s2, det_idx=di)
                res[p][cname].append(m["dissoc"])
    for p in ("uniform", "felt_b12"):
        print(f"  {p:<10} dissoc: first={np.mean(res[p]['first']):+.3f} "
              f"random={np.mean(res[p]['random']):+.3f} last={np.mean(res[p]['last']):+.3f}")

    # =========================== ATTACK C: budget fairness =======================
    print("\n" + "=" * 78)
    print("ATTACK C/3: is write energy actually matched?")
    s = 0
    world = World.generate("held_0", seed=900, depth=4)
    K, V, S, structural, texts, actions, eps, kinds = collect(world, N_EP, head, seed=s)
    chunk = max(1, len(K) // 8)
    for p in ("uniform", "surprise_only", "felt_b12"):
        w = weights_for(p, s, K, V, S, actions, texts, structural, kinds)
        tots, maxs, effn = [], [], []
        for i in range(0, len(K), chunk):
            ww = np.maximum(w[i:i+chunk], 0)
            if ww.sum() <= 0: continue
            wn = ww / ww.mean()
            tots.append(wn.sum()); maxs.append(wn.max())
            effn.append(float((wn.sum()**2) / (wn**2).sum()))  # effective #items
        print(f"  {p:<14} post-norm chunk totals={np.mean(tots):.1f} (n per chunk={chunk}) "
              f"max item wgt={np.mean(maxs):.1f}  effective-N/chunk={np.mean(effn):.1f}")
    # dmem_style from baselines (zeroing gate)
    mem = FastWeightMemory(d_key=32, d_val=32, hidden=48, seed=s)
    sur = mem.surprise(K, V)
    z = (sur - sur.mean()) / (sur.std() + 1e-9)
    wd = sur * (z > 0.5)
    tots, surv = [], []
    for i in range(0, len(K), chunk):
        ww = np.maximum(wd[i:i+chunk], 0)
        if ww.sum() <= 0: continue
        wn = ww / ww.mean()
        tots.append(wn.sum()); surv.append(int((ww > 0).sum()))
    print(f"  dmem_style     post-norm chunk totals={np.mean(tots):.1f}  "
          f"survivors/chunk={np.mean(surv):.1f} of {chunk} -> "
          f"per-survivor energy x{chunk/np.mean(surv):.1f}")
    print(f"  NOTE: surprise is computed on the FRESH memory before ANY writes "
          f"(not online). corr(surprise, structural)={np.corrcoef(sur, structural.astype(float))[0,1]:.3f}")
    # felt_b12 with a broken budget (skip normalization) as sanity: does total energy matter?
    print("  (write_batch renormalizes per chunk -> every policy injects the same "
          "total weighted-loss mass per chunk; only allocation differs. Matched.)")


if __name__ == "__main__":
    main()
