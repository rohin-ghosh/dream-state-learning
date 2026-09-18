"""M7 (REVIEW_HARSH): null distribution for the 'rehearsal' (echo) metric.
For each RP brief, score first-NOTE lexical overlap (>=4 shared content words,
stop-words removed, REHEARSAL_TAIL removed) in (a) the RP life's own episodes
after the brief, (b) CONTROL lives (R2/R3) that never saw any brief, (c) the RP
life's own episodes BEFORE its first brief.  Run on a node.
  python -m organism_v6.echo_null --out ~/v6_out/echo_null.json
"""
from __future__ import annotations
import argparse, glob, json, os, re, statistics
from .parent_brief import episode_instances, REHEARSAL_TAIL, _NOTE

H = os.path.expanduser("~")
STOP = set("the and for you your that this with what was were are will each every episode before after into then than them they have has had not but its own own about when how why more most some any all one two just also very can could should would from onto over under between".split())


def toks(s):
    return set(w for w in re.findall(r"[a-z]{3,}", s.lower()) if w not in STOP)


def first_notes(life_dir, lo=None, hi=None):
    rows = [json.loads(l) for l in open(life_dir + "/ledger.jsonl") if l.strip()]
    th = [r for r in rows if r.get("kind") == "thought" and r.get("note")]
    inst = list(episode_instances(th).items())
    if lo is not None or hi is not None:
        inst = inst[(lo or 0):(hi or len(inst))]
    out = []
    for _k, notes in inst:
        m = _NOTE.findall("\n".join(notes))
        if m:
            out.append(m[0])
    return out


def rate(notes, brief_toks, k=4):
    if not notes:
        return None
    return sum(len(toks(n) & brief_toks) >= k for n in notes) / len(notes)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    briefs = []
    for d in sorted(glob.glob(H + "/v6_out/RP_B_seed*")):
        if not os.path.isdir(d): continue
        for pb in sorted(glob.glob(d + "/sleep_*/parent_brief.txt")):
            t = open(pb).read().replace(REHEARSAL_TAIL.strip(), "")
            briefs.append(dict(life=os.path.basename(d), sleep=int(pb.split("/")[-2][6:]), toks=toks(t), n_toks=len(toks(t))))
    controls = [d for d in sorted(glob.glob(H + "/v6_out/R2_B_seed*") + glob.glob(H + "/v6_out/R3_B_seed*")) if os.path.isdir(d)]
    ctrl_notes = {os.path.basename(d): first_notes(d) for d in controls}
    res = []
    for b in briefs:
        life = H + "/v6_out/" + b["life"]
        own_after = rate(first_notes(life, lo=b["sleep"], hi=b["sleep"] + 32), b["toks"])
        own_before = rate(first_notes(life, lo=0, hi=min(b["sleep"], 160)), b["toks"])
        ctrl = [rate(v, b["toks"]) for v in ctrl_notes.values() if v]
        res.append(dict(life=b["life"], sleep=b["sleep"], brief_tokens=b["n_toks"], own_after=own_after,
                        own_before_first_brief=own_before, controls_mean=statistics.mean(ctrl) if ctrl else None,
                        controls_max=max(ctrl) if ctrl else None))
    summ = dict(n_briefs=len(res),
                own_after_mean=statistics.mean(r["own_after"] for r in res if r["own_after"] is not None),
                own_before_mean=statistics.mean(r["own_before_first_brief"] for r in res if r["own_before_first_brief"] is not None),
                controls_mean=statistics.mean(r["controls_mean"] for r in res if r["controls_mean"] is not None),
                controls_max_mean=statistics.mean(r["controls_max"] for r in res if r["controls_max"] is not None))
    json.dump(dict(summary=summ, rows=res), open(os.path.expanduser(a.out), "w"), indent=1)
    print(json.dumps(summ, indent=1))
    for r in res[:: max(1, len(res) // 12)]:
        print(r)


if __name__ == "__main__":
    main()
