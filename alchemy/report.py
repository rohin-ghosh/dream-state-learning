"""Turn v2 results.json files into the paper's tables.

  python3 alchemy/report.py alchemy/v2_out/seed*/results.json
Prints: per-checkpoint arm scores (held-out primary + iid/fn strata,
recall/G1, task success), the ceiling row, and falsifier status at 3840.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict

import numpy as np

CEIL = {"960": 0.09, "1920": 0.42, "3840": 0.92, "7680": 1.0, "15360": 1.0}


def main(paths):
    seeds = [json.loads(open(p).read()) for p in paths]
    points = sorted({int(k) for s in seeds for k in s}, key=int)
    arms = sorted({a for s in seeds for row in s.values()
                   for a in row if isinstance(row[a], dict)})
    print(f"seeds: {len(seeds)}   points: {points}\n")
    for metric, key in (("HELD-OUT score (primary)", "score"),
                        ("held-out IID (retention)", "iid"),
                        ("held-out FN (extrapolation)", "fn"),
                        ("seen recall / G1", "exact_acc"),
                        ("task success", None)):
        print(f"== {metric}")
        hdr = f"{'arm':<26}" + "".join(f"{p:>9}" for p in points)
        print(hdr)
        if key in ("score", "iid", "fn"):
            print(f"{'(tier-3 ceiling)':<26}" + "".join(
                f"{CEIL.get(str(p), float('nan')):>9.2f}" for p in points))
        for arm in arms:
            vals = []
            for p in points:
                xs = []
                for s in seeds:
                    row = s.get(str(p), {}).get(arm)
                    if not isinstance(row, dict) or row.get("na"):
                        continue
                    if key is None:
                        xs.append(row.get("task_success"))
                    elif key == "exact_acc":
                        xs.append(row.get("seen_recall", {}).get("exact_acc"))
                    elif key in ("iid", "fn"):
                        xs.append(row.get("held_out", {}).get(key))
                    else:
                        xs.append(row.get("held_out", {}).get("score"))
                xs = [x for x in xs if x is not None]
                vals.append(f"{np.mean(xs):>9.2f}" if xs else f"{'N/A':>9}")
            print(f"{arm:<26}" + "".join(vals))
        print()
    # falsifier at 3840
    p = "3840"
    ld, rag = [], []
    for s in seeds:
        row = s.get(p, {})
        if isinstance(row.get("lora_dreamed"), dict) and \
           not row["lora_dreamed"].get("na"):
            ld.append(row["lora_dreamed"]["held_out"]["score"])
        best = max((row[a]["held_out"]["score"] for a in ("rag_raw", "rag_dreamed")
                    if isinstance(row.get(a), dict) and not row[a].get("na")),
                   default=None)
        if best is not None:
            rag.append(best)
    if ld and rag and len(ld) == len(rag):
        d = np.array(ld) - np.array(rag)
        t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else float("nan")
        print(f"FALSIFIER @3840: lora_dreamed-bestRAG = {d.mean():+.3f} "
              f"(need >=+0.05), t={t:.2f}, n={len(d)}")


if __name__ == "__main__":
    main(sys.argv[1:])
