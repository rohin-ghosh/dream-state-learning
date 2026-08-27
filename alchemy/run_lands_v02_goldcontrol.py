"""POSITIVE CONTROL (Codex 2026-08-27): known-good structural statements
-> the exact organism v2 sequential thinker, via text AND LoRA arms.
If this succeeds, downstream transport/composition is validated and
structural dream generation is the proven sole bottleneck.
ORACLE-MEMORY CONTROL — explicitly labeled; statements derived from
evaluator truth (parents + combination principle); episodic cells
included as in the organism corpus. Adds arms goldtext/goldlora to the
existing organism corpus file, then reuse organism train/think phases.
"""
from __future__ import annotations
import json, re
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02, TARGET_LAND_IDS

world = SemanticWorldV02(WorldConfig(seed=0))
skin_obj = make_skin("aligned", world.animal_ids, world.source_land_ids)
rows = list(world.render_lifetime("aligned"))
goals = world.render_goals("aligned")
tgt_surfaces = []
for g in goals:
    m = re.match(r"In ([^,]+),", g["question"])
    if m and m.group(1) not in tgt_surfaces:
        tgt_surfaces.append(m.group(1))
joined = "\n".join(rows)
order = sorted((joined.find(s), s) for s in tgt_surfaces)
surface_by_id = dict(zip(TARGET_LAND_IDS[:len(tgt_surfaces)],
                         [s for _, s in order]))
statements = []
for tid, surf in surface_by_id.items():
    parents = sorted(skin_obj.land(p) for p in world.target_parents[tid])
    statements.append(f"{surf}'s outcomes are built from "
                      f"{', '.join(parents[:-1])} and {parents[-1]} combined.")
statements.append(
    "In this world, an animal's color in a combined land is the "
    "paint-pigment mixture of that animal's colors in the lands that "
    "feed that combined land (mixing pigments like paint; amounts add).")
episodic = [r.split("] ", 1)[1] if "] " in r else r for r in rows]
animals = [skin_obj.animal(x) for x in world.animal_ids]
lands = [skin_obj.land(l) for l in world.source_land_ids]

def qa_forms(stmts):
    out = []
    for s in stmts:
        ents = [e for e in list(surface_by_id.values()) + animals + lands
                if e in s][:2]
        key = " and ".join(ents) if ents else "this world"
        out.append(f"Q: What did you conclude about {key}? A: {s}")
        out.append(s)
    return out

path = "alchemy/v2_out/organism_corpus_aligned_s0.json"
corpus = json.load(open(path))
corpus["goldlora"] = qa_forms(statements) + episodic
corpus["goldtext"] = statements
json.dump(corpus, open(path, "w"), indent=1)
print(f"[gold] {len(statements)} structural statements added "
      f"(goldlora={len(corpus['goldlora'])} lines)")
for s in statements[:4]:
    print("  ", s)
