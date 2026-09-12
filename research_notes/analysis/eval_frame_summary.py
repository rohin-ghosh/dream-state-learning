#!/usr/bin/env python3
"""Dose-16 canonical-frame completion from memory_dose eval JSON files (CPU).
For each file: over cues of kind 'frame' at dose 16, the mean candidate-normalised probability of the planted colour
(p_raw[a] / mass) OFF and ON (the report's 'frame P'); the same at the look-alike owner's frame ('frame_similar') and the
bicycle frame as spill indicators; the adapter path and corpus sha recorded in the file.
Usage: python3 eval_frame_summary.py EVAL.json [EVAL.json ...]"""
import json, statistics as st, sys


def norm_p(side, a):
    m = side.get("mass") or 0.0
    return (side["p_raw"].get(a, 0.0) / m) if m > 0 else 0.0


for f in sys.argv[1:]:
    e = json.load(open(f))
    cues = e["cues"]
    out = []
    for kind in ("frame", "frame_similar", "frame_bicycle"):
        d16 = [c for c in cues if c.get("kind") == kind and c.get("dose") == 16]
        if not d16:
            continue
        off = st.mean(norm_p(c["OFF"], c["a"]) for c in d16)
        on = st.mean(norm_p(c["ON"], c["a"]) for c in d16)
        mass_on = st.mean(c["ON"].get("mass", 0.0) for c in d16)
        out.append(f"{kind}: n={len(d16)} P OFF {off:.3f} -> ON {on:.3f} (ON mass {mass_on:.3f})")
    meta = e.get("adapter_meta") or {}
    sha = meta.get("corpus_sha") if isinstance(meta, dict) else "?"
    print(f"{f.split('/')[-1][:56]:56s} | " + " | ".join(out) + f" | corpus {sha} | adapter ...{str(e.get('adapter'))[-48:]}")
