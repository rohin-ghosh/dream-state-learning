#!/usr/bin/env python3
"""SEQ-011 numbers, computed from the SEQ-001/SEQ-005 analysis JSON (no hand copying).

  python3 research_notes/analysis/seq011_from_json.py

Sources (laptop copies of node-side artifacts):
  analysis_tables_2026-09-10_{a40,ovx}.json   per_life[*].series = [[episode, paired ON-OFF], ...]; sd{}
  efficiency_markers_2026-09-10_{a40,ovx}.json lives{life: [window{ep, chunks_per_ep, chunks_to_best, ...}]}
Posted because NEXT_EXPERIMENT_DESIGN_v1 section 2 uses them as the F1 ruler and as cell counts
while they traced only to JSON (verifier objection, 2026-09-10).
"""
import glob, json, math, os, statistics as st

H = os.path.dirname(os.path.abspath(__file__))


def load(prefix):
    out = {}
    for fn in sorted(glob.glob(f"{H}/{prefix}_2026-09-10_*.json")):
        d = json.load(open(fn)); out[d["node"]] = d
    return out


def cycle16(series):
    """Design's cycle-16 estimator: mean of the paired ON-OFF at episodes 448 and 512 (None if either missing)."""
    m = {int(e): v for e, v in series}
    if 448 in m and 512 in m: return (m[448] + m[512]) / 2
    return None


def sd(xs): return st.stdev(xs) if len(xs) > 1 else float("nan")


def main():
    A = load("analysis_tables"); E = load("efficiency_markers")
    lives = {}
    for node, d in A.items():
        for L in d["per_life"]:
            lives[L["life"]] = dict(arm=L["arm"], node=node, est16=cycle16(L["series"]), harmful=L["harmful"], exposure=L["exposure"], mean=L["mean"])
    print("== cycle-16 estimator (mean paired ON-OFF at 448 and 512) per life ==")
    for L, r in sorted(lives.items()):
        e = r["est16"]; print(f"{L:14s} {r['arm']:3s} {r['node']} exposure={r['exposure']:5d} harmful_pairs={r['harmful']} est16={'n/a' if e is None else f'{e:+.4f}'}")
    r3 = {L: r["est16"] for L, r in lives.items() if r["arm"] == "R3" and r["est16"] is not None}
    r2 = {L: r["est16"] for L, r in lives.items() if r["arm"] == "R2" and r["est16"] is not None}
    r2_lt2harm = {L: v for L, v in r2.items() if lives[L]["harmful"] < 2}
    r2_0harm = {L: v for L, v in r2.items() if lives[L]["harmful"] == 0}
    print("\n== between-life SD of the estimator ==")
    print(f"gated R3 lives that reached 512: n={len(r3)} values={[f'{v:+.3f}' for v in r3.values()]} SD={sd(list(r3.values())):.4f} mean={st.mean(r3.values()):+.4f}")
    print(f"all R2 lives: n={len(r2)} values={[f'{v:+.3f}' for v in r2.values()]} SD={sd(list(r2.values())):.4f}")
    print(f"R2 lives with <2 harmful pairs ({sorted(r2_lt2harm)}): n={len(r2_lt2harm)} SD={sd(list(r2_lt2harm.values())):.4f}")
    print(f"R2 lives with 0 harmful pairs ({sorted(r2_0harm)}): n={len(r2_0harm)} SD={sd(list(r2_0harm.values())):.4f}")
    print("\n== same-adapter replicate SD, pooled across nodes ==")
    parts = [(d["sd"]["n_same_adapter_reps"], d["sd"]["sd_same_adapter_gate_vs_probe"]) for d in A.values()]
    n = sum(p[0] for p in parts); pooled = math.sqrt(sum((k - 1) * s * s for k, s in parts) / (n - len(parts)))
    print(f"per node {[(k, round(s, 4)) for k, s in parts]} -> pooled n={n} SD={pooled:.4f}")
    print(f"adapter-OFF probe-mean SD per node: {[(d['sd']['n_off'], round(d['sd']['sd_off'], 4)) for d in A.values()]}")
    print("\n== efficiency instrument: windows with undefined chunks-to-best, and late-life chunks per situation (mean of last 3 windows) ==")
    for node, d in E.items():
        for L, ws in sorted(d["lives"].items()):
            if not isinstance(ws, list): print(f"{L:14s} {node} ERROR in JSON: {str(ws)[:70]}"); continue
            undef = sum(1 for w in ws if w.get("chunks_to_best") is None)
            late = [w["chunks_per_ep"] for w in ws[-3:]]
            print(f"{L:14s} {node} windows={len(ws):2d} undefined_ctb={undef:2d}/{len(ws)} late3_chunks_per_situation={st.mean(late):5.2f} {[round(x, 1) for x in late]}")


if __name__ == "__main__":
    main()
