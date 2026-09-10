"""Review-driven analysis tables (2026-09-10; REVIEW_HARSH M1, M2, M3, M12, minor 2).
Runs on a node over ~/v6_out; CPU only. Emits JSON + markdown.

  python -m organism_v6.analysis_tables --out ~/v6_out/analysis_tables.json

Tables:
  per_life      one row per life: arm, node, pairs, mean/min/max ON-OFF, harmful (<-0.03),
                exposure (episodes reached), restarts (count of '[life-v2] arm=' banner lines),
                commits, rejections by reason, final adapter sleep
  sd            SD(OFF) across all OFF probes; SD(ON) from same-adapter replicate pairs
                (gate{i} vs ep{i} in gated lives); SD(ON-OFF) under independence
  per_program   ON-OFF per probe program averaged over lives (which programs carry the mean)
  ritual_probe  ritual_metrics on probe ledgers: adapter ON vs adapter OFF at each checkpoint
"""
from __future__ import annotations
import argparse
import collections
import glob
import json
import os
import re
import statistics

from .parent_brief import ritual_metrics

H = os.path.expanduser("~")


def probes(d):
    on, off = {}, {}
    for f in glob.glob(d + "/probe_ep*.json"):
        m = re.match(r"probe_ep(\d+)(_adapterOFF)?\.json", os.path.basename(f))
        if not m:
            continue
        (off if m.group(2) else on)[int(m.group(1))] = json.load(open(f))
    return on, off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--node", default=os.uname().nodename)
    args = ap.parse_args()
    rows, all_off, on_reps, per_prog, ritual = [], [], [], collections.defaultdict(list), []
    for d in sorted(glob.glob(H + "/v6_out/R*_B_seed*")):
        if not os.path.isdir(d) or not os.path.exists(d + "/ledger.jsonl"):
            continue
        L = os.path.basename(d)
        arm = L.split("_")[0]
        on, off = probes(d)
        pairs = [(e, on[e]["mean"], off[e]["mean"]) for e in sorted(on) if e in off]
        diffs = [a - b for _, a, b in pairs]
        all_off += [v["mean"] for v in off.values()]
        for e, a, b in pairs:
            for prog, sc in on[e]["results"].items():
                if prog in off[e]["results"]:
                    per_prog[prog].append(sc - off[e]["results"][prog])
        # same-adapter replicates: gate probe at sleep i vs regular ON probe at ep i
        for g in glob.glob(d + "/probe_gate*.json"):
            i = int(re.search(r"gate(\d+)", g).group(1))
            if i in on and os.path.exists(os.path.join(d, f"sleep_{i:04d}", "adapter", "DONE")):
                on_reps.append(json.load(open(g))["mean"] - on[i]["mean"])
        rej = collections.Counter()
        for r in glob.glob(d + "/sleep_*/adapter/REJECTED*"):
            rej[os.path.basename(r)] += 1
        commits = len(glob.glob(d + "/sleep_*/adapter/DONE"))
        restarts = 0
        if os.path.exists(d + "/life.log"):
            restarts = sum(1 for l in open(d + "/life.log") if l.startswith("[life-v2] arm=")) - 1
        wakes = glob.glob(d + "/wake_*.json")
        exposure = max([int(os.path.basename(w)[10:14]) for w in wakes] or [0])
        finals = sorted(glob.glob(d + "/sleep_*/adapter/DONE"))
        rows.append(dict(life=L, arm=arm, node=args.node, pairs=len(pairs),
                         mean=round(statistics.mean(diffs), 4) if diffs else None,
                         min=round(min(diffs), 4) if diffs else None,
                         max=round(max(diffs), 4) if diffs else None,
                         harmful=sum(x < -0.03 for x in diffs), exposure=exposure,
                         restarts=max(0, restarts), commits=commits, rejections=dict(rej),
                         final_adapter=finals[-1].split("/")[-3] if finals else None,
                         done=os.path.exists(d + "/LIFE_DONE"),
                         series=[(e, round(a - b, 4)) for e, a, b in pairs]))
        # ritual on probe ledgers ON vs OFF
        for e in sorted(on):
            if e not in off:
                continue
            for tag, path in (("ON", d + f"/probe_ep{e:04d}.ledger.jsonl"),
                              ("OFF", d + f"/probe_ep{e:04d}_adapterOFF.ledger.jsonl")):
                if not os.path.exists(path):
                    continue
                rws = [json.loads(l) for l in open(path) if l.strip()]
                m = ritual_metrics(rws, 8)
                ritual.append(dict(life=L, ep=e, arm_probe=tag,
                                   recipe=m.get("modal_first_act_share"),
                                   pred_sd=m.get("predict_sd"), note_j=m.get("note_consecutive_jaccard"),
                                   recall=m.get("recall_modal_share"), flags=m.get("flags")))
    sd_off = statistics.pstdev(all_off) if len(all_off) > 1 else None
    sd_on_rep = statistics.pstdev(on_reps) if len(on_reps) > 1 else None
    sd = dict(n_off=len(all_off), sd_off=sd_off, mean_off=statistics.mean(all_off) if all_off else None,
              n_same_adapter_reps=len(on_reps), sd_same_adapter_gate_vs_probe=sd_on_rep,
              mean_abs_gate_minus_probe=statistics.mean(abs(x) for x in on_reps) if on_reps else None,
              sd_diff_independent=(2 ** 0.5) * sd_off if sd_off else None)
    pp = {p: dict(n=len(v), mean=round(statistics.mean(v), 4), frac_pos=round(sum(x > 0 for x in v) / len(v), 2))
          for p, v in per_prog.items()}
    # ritual summary: per arm_probe, fraction of checkpoints with recipe share 1.0 and mean metrics
    rs = collections.defaultdict(list)
    for r in ritual:
        rs[r["arm_probe"]].append(r)
    ritual_summary = {k: dict(n=len(v), recipe_share_mean=round(statistics.mean(x["recipe"] or 0 for x in v), 3),
                              recipe_locked_frac=round(sum((x["recipe"] or 0) >= 0.99 for x in v) / len(v), 2),
                              note_j_mean=round(statistics.mean(x["note_j"] or 0 for x in v), 3),
                              pred_sd_mean=round(statistics.mean(x["pred_sd"] or 0 for x in v), 3))
                      for k, v in rs.items()}
    out = dict(node=args.node, per_life=rows, sd=sd, per_program=pp,
               ritual_probe_summary=ritual_summary, ritual_probe=ritual)
    with open(os.path.expanduser(args.out), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(dict(node=args.node, lives=len(rows), sd=sd, ritual=ritual_summary), indent=1))
    for r in rows:
        print(f"{r['life']:14s} {r['arm']:3s} pairs={r['pairs']:2d} mean={r['mean']} min={r['min']} harmful={r['harmful']} "
              f"exposure={r['exposure']} restarts={r['restarts']} commits={r['commits']} rej={r['rejections']}")
    print("per-program ON-OFF:", json.dumps(pp))


if __name__ == "__main__":
    main()
