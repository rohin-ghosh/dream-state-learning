#!/usr/bin/env python3
"""Perception content of the child's renderings, from generations.json alone (CPU; no model): per cell and bank, the
share of prose lines (the canonical sentence stripped when the child wrote it) that name the planted colour, the owner id,
and BOTH (the observed owner-colour relation restated) -- the diagnostics the a-vs-b-vs-t comparison turns on (SEQ-048,
Astra memo q10 section 4). Works for corpora built before these rates existed.
Usage: python3 cf_mention_rates.py RUN_DIR [cells...]   (default CF_r16_a CF_r16_b CF_r16_c CF_r16_t CF_r16_u; banks 0-2)
"""
import json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from organism_v6 import memory_dose as md  # noqa: E402

run = sys.argv[1]
cells = sys.argv[2:] or ["CF_r16_a", "CF_r16_b", "CF_r16_c", "CF_r16_t", "CF_r16_u"]
colour_re = md._COLOUR_WORD_RE


def owner_re(o):
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(o) + r"(?![A-Za-z0-9])", re.IGNORECASE)


print("cell bank lines colour_named owner_named relation_named canonical_ended mean_prose_words")
for cell in cells:
    for b in (0, 1, 2):
        gp = os.path.join(run, "corpora", f"bank{b}", cell, "across", "sleep4", "generations.json")
        bp = os.path.join(run, "banks", f"bank{b}.json")
        if not (os.path.exists(gp) and os.path.exists(bp)):
            print(f"{cell} {b} missing")
            continue
        g = json.load(open(gp)); bank = json.load(open(bp))
        ev_by_id = {e["event_id"]: e for e in bank["events"] if "owner" in e and "colour" in e}
        n = col = own = rel = ended = 0; words = 0
        for eid, rec in g["events"].items():
            ev = ev_by_id.get(eid)
            if ev is None:
                continue
            canon = md.FRAME_CANONICAL.format(owner=ev["owner"], colour=ev["colour"])
            ore = owner_re(ev["owner"])
            for line in rec.get("lines") or md.parse_child_lines(rec.get("text") or ""):
                line = line.translate(md._CHILD_TYPOGRAPHY).strip()
                prose = line[: -len(canon)].strip() if line.endswith(canon) else line
                if line.endswith(canon):
                    ended += 1
                cw = {w.lower() for w in colour_re.findall(prose)}
                c_hit = ev["colour"].lower() in cw
                o_hit = bool(ore.search(prose))
                n += 1; col += c_hit; own += o_hit; rel += (c_hit and o_hit); words += len(prose.split())
        if n:
            print(f"{cell} {b} {n} {col/n:.3f} {own/n:.3f} {rel/n:.3f} {ended/n:.3f} {words/n:.1f}")
        else:
            print(f"{cell} {b} 0 lines")
