#!/usr/bin/env python3
"""Print the child-authored-frames (bridge) perception diagnostics per cell and bank from the corpus manifests.
Usage: python3 cf_diagnostics.py RUN_DIR [cells...]  (default cells CF_r16_a CF_r16_b CF_r16_c CF_r16_t CF_r16_u; banks 0-2;
a missing cell/bank prints 'missing'). t/u are the TAUGHT variants of b/c (perception lesson in the prompt)."""
import json, os, sys

run = sys.argv[1]
cells = sys.argv[2:] or ["CF_r16_a", "CF_r16_b", "CF_r16_c", "CF_r16_t", "CF_r16_u"]
keys = ["distinct_rate", "echo_rate", "drift_rate", "colour_mention_rate", "owner_mention_rate", "relation_mention_rate", "canonical_miss_rate",
        "padded_rate", "mean_tokens", "mean_prose_tokens", "novelty", "n_negatives", "negative_miss_rate"]
for cell in cells:
    for b in (0, 1, 2):
        p = os.path.join(run, "corpora", f"bank{b}", cell, "across", "sleep4", "corpus.json")
        if not os.path.exists(p):
            print(f"{cell} bank{b}: missing")
            continue
        c = json.load(open(p))
        st = c.get("stats") or {}
        ch = st.get("child") or {}
        vals = []
        for k in keys:
            v = ch.get(k)
            if isinstance(v, float):
                vals.append(f"{k}={v:.3f}")
            elif v is not None:
                vals.append(f"{k}={v}")
        print(f"{cell} bank{b}: items={len(c['corpus'])} tokens={st.get('n_tokens')} backend={c.get('child_backend')} " + " ".join(vals))
