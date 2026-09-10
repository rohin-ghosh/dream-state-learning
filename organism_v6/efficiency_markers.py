"""Efficiency over cycles, metacognitive markers, and the behaviour-change gate
(scoping of 2026-09-10). CPU only; runs on a node over ~/v6_out.

  python -m organism_v6.efficiency_markers --out ~/v6_out/efficiency_markers.json

Per life, per 32-episode window (one consolidation cycle):
  eff   chunks per episode, chunks-to-best (index of the first chunk reaching the
        episode's best score; 'steps-to-solve'), chars per episode ('tokens-to-solve'),
        best score
  mark  per-episode counts of: self-evaluation phrases, contrast/scope phrases,
        strategy switches (distinct ACT strings within the episode), recalls, notes,
        backtracks (an ACT that differs from the previous ACT after a non-improving outcome)
  shift Jensen-Shannon divergence between consecutive windows' first-ACT distributions
        (the day-one gate: does behaviour change between cycles?)
Arms are compared by prefix: R2 (untaught, ungated), R3 (untaught, gated), RP (taught,
ungated), R4 (taught, gated).
"""
from __future__ import annotations
import argparse, collections, glob, json, math, os, re, statistics
from .parent_brief import episode_instances

H = os.path.expanduser("~")
ACT = re.compile(r"^ACT:\s*(.+)$", re.M)
SELF_EVAL = re.compile(r"\b(wrong|mistake|should have|surpris\w*|unexpected|reconsider|instead|didn'?t work|failed|overestimat\w*|underestimat\w*|misjudg\w*|correct(ed|ion)?\b|revis\w*|why did|what went)", re.I)
CONTRAST = re.compile(r"\b(unlike|compared (to|with)|whereas|differs?|different from|earlier program|last time|previous(ly)?|in contrast|applies when|does not apply|scope)\b", re.I)
OUTCOME = re.compile(r"\[OUTCOME\].*?score\s*([0-9.]+)", re.I)


def js(p, q):
    keys = set(p) | set(q)
    P = [p.get(k, 0) for k in keys]; Q = [q.get(k, 0) for k in keys]
    sp, sq = sum(P) or 1, sum(Q) or 1
    P = [x / sp for x in P]; Q = [x / sq for x in Q]
    M = [(a + b) / 2 for a, b in zip(P, Q)]
    def kl(a, b): return sum(x * math.log(x / y) for x, y in zip(a, b) if x > 0 and y > 0)
    return 0.5 * kl(P, M) + 0.5 * kl(Q, M)


def analyse(life_dir):
    rows = [json.loads(l) for l in open(life_dir + "/ledger.jsonl") if l.strip()]
    th = [r for r in rows if r.get("kind") == "thought" and r.get("note")]
    inst = list(episode_instances(th).items())
    # per-episode best score from act rows if present, else from [OUTCOME] lines in thoughts
    windows = []
    for w0 in range(0, len(inst) - 31, 32):
        win = inst[w0:w0 + 32]
        cpe, ctb, chars, best, se, co, sw, rc, nt, bt, first_acts = [], [], [], [], [], [], [], [], [], [], collections.Counter()
        for (_e, _k), notes in win:
            text = "\n".join(notes)
            acts = [a.strip() for a in ACT.findall(text)]
            scores = [float(x) for x in OUTCOME.findall(text)]
            cpe.append(len(notes)); chars.append(len(text))
            if scores:
                b = max(scores); best.append(b)
                # chunk index of first outcome reaching best
                cum = 0; idx = len(notes)
                for i, n in enumerate(notes):
                    s = [float(x) for x in OUTCOME.findall(n)]
                    if s and max(s) >= b: idx = i + 1; break
                ctb.append(idx)
            se.append(len(SELF_EVAL.findall(text))); co.append(len(CONTRAST.findall(text)))
            sw.append(len(set(acts))); rc.append(text.count("RECALL:")); nt.append(text.count("NOTE:"))
            # backtracks: ACT changes after a non-improving outcome
            b_count, prev_act, prev_best = 0, None, -1.0
            for n in notes:
                a = ACT.findall(n); s = [float(x) for x in OUTCOME.findall(n)]
                if a and prev_act is not None and a[0].strip() != prev_act and s and max(s) <= prev_best:
                    b_count += 1
                if a: prev_act = a[0].strip()
                if s: prev_best = max(prev_best, max(s))
            bt.append(b_count)
            if acts: first_acts[re.sub(r"\s+", "", acts[0])] += 1
        windows.append(dict(ep=w0 + 32, n=len(win), chunks_per_ep=statistics.mean(cpe), chunks_to_best=statistics.mean(ctb) if ctb else None,
                            chars_per_ep=statistics.mean(chars), best=statistics.mean(best) if best else None,
                            self_eval=statistics.mean(se), contrast=statistics.mean(co), switches=statistics.mean(sw),
                            recalls=statistics.mean(rc), notes=statistics.mean(nt), backtracks=statistics.mean(bt), first_acts=dict(first_acts)))
    for i in range(1, len(windows)):
        windows[i]["js_shift_from_prev"] = round(js(windows[i - 1]["first_acts"], windows[i]["first_acts"]), 4)
    for w in windows: w.pop("first_acts", None)
    return windows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--node", default=os.uname().nodename); a = ap.parse_args()
    out = {}
    for d in sorted(glob.glob(H + "/v6_out/R*_B_seed*")):
        if not os.path.isdir(d) or not os.path.exists(d + "/ledger.jsonl"): continue
        L = os.path.basename(d)
        try: out[L] = analyse(d)
        except Exception as e: out[L] = dict(error=str(e))
    json.dump(dict(node=a.node, lives=out), open(os.path.expanduser(a.out), "w"), indent=1)
    # summary by arm: early (windows 2-4) vs late (last 3 windows) for full lives
    def arm(L): return L.split("_")[0]
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    for L, ws in out.items():
        if not isinstance(ws, list) or len(ws) < 8: continue
        early, late = ws[1:4], ws[-3:]
        for key in ("chunks_per_ep", "chunks_to_best", "chars_per_ep", "best", "self_eval", "contrast", "switches", "recalls", "backtracks", "js_shift_from_prev"):
            ev = [w[key] for w in early if w.get(key) is not None]; lv = [w[key] for w in late if w.get(key) is not None]
            if ev and lv: agg[arm(L)][key].append((statistics.mean(ev), statistics.mean(lv)))
    print(f"node {a.node}: lives analysed {len(out)}")
    for A, keys in sorted(agg.items()):
        line = [f"{A} (n={len(keys['chunks_per_ep'])})"]
        for key, pairs in keys.items():
            e = statistics.mean(p[0] for p in pairs); l = statistics.mean(p[1] for p in pairs)
            line.append(f"{key}: {e:.3f}->{l:.3f}")
        print(" | ".join(line))


if __name__ == "__main__":
    main()
