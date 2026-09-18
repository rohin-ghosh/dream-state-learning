import json, os, glob, sys
sys.path.insert(0, os.path.expanduser("~/dream-state"))
from organism_v6.parent_brief import ritual_metrics, episode_instances
H = os.path.expanduser("~")
for d in sorted(glob.glob(f"{H}/v6_out/R*_B_seed*")):
    if not os.path.isdir(d) or not os.path.exists(d + "/ledger.jsonl"):
        continue
    rows = [json.loads(l) for l in open(d + "/ledger.jsonl") if l.strip()]
    th = [r for r in rows if r.get("kind") == "thought" and r.get("note")]
    inst = list(episode_instances(th).items())
    out = []
    for start in range(0, len(inst) - 31, 32):
        win = inst[start:start + 32]
        # rebuild rows for this window with fresh ticks so grouping is stable
        sub = []
        for (e, k), notes in win:
            for i, n in enumerate(notes):
                sub.append(dict(kind="thought", episode_id=f"{e}#{k}", tick=i, note=n))
        m = ritual_metrics(sub, 32)
        out.append("%d:%s%s" % (start + 32, "R" if m.get("ritual") else "-",
                                "".join(f[0] for f in m.get("flags", []))))
    print(os.path.basename(d), "episodes=%d" % len(inst), " ".join(out))
    if inst:
        win = inst[-32:]
        sub = [dict(kind="thought", episode_id=f"{e}#{k}", tick=i, note=n)
               for (e, k), notes in win for i, n in enumerate(notes)]
        last = ritual_metrics(sub, 32)
        print("   last:", {k: last[k] for k in last if k not in ("flags", "ritual", "n_episodes")})
