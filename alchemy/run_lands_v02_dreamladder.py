"""THE MINIMAL DREAM LADDER (Codex+Rohin spec, 2026-08-28). 32B dreamer.

Generic hypothesis->prediction->revision dreaming, producing exactly the
memory kinds the gold-control contract requires:
  RECIPES : from the public workshop calibration lines
  ROLES   : from the animal x land outcome table (entities with the same
            outcome in the same place likely share a latent kind)
  PARENTS : per unresolved combined place — k candidate source sets,
            PREDICT the observed cells under each via pigment addition,
            COMPARE with public experience, retain with uncertainty.
            The two PUBLIC demo lands (known sources) are worked examples.
No solver anywhere in the loop; offline truth used only for reporting
AFTER commit. Output: organism-format corpus arms 'dreamtext'/'dreamlora'
+ full audit (raw dream texts, per-hypothesis predictions, statuses).
Run order (Codex): 1) dreamtext -> 32B thinker; 2) freeze corpus ->
LoRA -> reads -> thinker; 3) replicate only after positives.
"""
from __future__ import annotations
import argparse, json, pathlib, re
from collections import defaultdict

from alchemy.backend import make_backend
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02, TARGET_LAND_IDS

DREAMER = "Qwen/Qwen2.5-32B-Instruct"

RECIPES = """You are dreaming over your memories of a color workshop.
Consolidate them into durable knowledge: for each labeled color, state
exactly what pigment parts it denotes.

WORKSHOP MEMORIES:
{lines}

Output one line per label, exactly like:
RECIPE: <label> denotes <n> part(s) <pigment> [+ <n> part(s) <pigment> ...]
Only include labels the memories support."""

ROLES = """You are dreaming over your lifetime of observations, laid out
as a table (entity: place=outcome). A useful generic principle: entities
that show the SAME outcome in the SAME place likely share a latent kind,
and entities of one kind agree everywhere.

TABLE:
{table}

For every pair the table supports (they agree in at least one shared
place and never disagree in any shared place), output exactly:
ROLE: In every land, the <entity A> has the same color as the <entity B>.
Check each pair against ALL shared places before writing it."""

PARENTS = """You are dreaming about a combined place whose sources are
unknown. In this world, some places' outcomes are built from other
places' outcomes by pigment addition (a public survey classifies them
together).

WORKED EXAMPLE (public knowledge — this combined place's sources are
known):
{example}

Study how each entity's outcome in the example place equals the pigment
sum of its outcomes in the source places.

NOW THE UNEXPLAINED PLACE: {target}
You know these entities were observed there: {entities}
(You do NOT get to see their outcomes there — you must PREDICT them.)

Those entities' outcomes in the six ordinary places (use your role
knowledge where an entity was not directly seen):
{sources}

Your recipe knowledge:
{recipes}

Propose up to {k} DIFFERENT candidate source sets (2-5 ordinary places
each; make them genuinely different). For EACH candidate, compute the
predicted pigment sum for BOTH entities and name the resulting labels.
Show the arithmetic. End each candidate with one line, exactly:
CANDIDATE: {target} <- <place>, <place>[, <place>...] | predicted: {e1}=<label>, {e2}=<label>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin", default="aligned")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--k", type=int, default=4)
    a = ap.parse_args()
    world = SemanticWorldV02(WorldConfig(seed=a.seed))
    skin_obj = make_skin(a.skin, world.animal_ids, world.source_land_ids)
    rows = list(world.render_lifetime(a.skin))
    goals = world.render_goals(a.skin)
    animals = [skin_obj.animal(x) for x in world.animal_ids]
    lands = [skin_obj.land(l) for l in world.source_land_ids]
    joined = "\n".join(rows)

    # surface names for targets and demos, by first mention
    tgt_surfaces = []
    for g in goals:
        m = re.match(r"In ([^,]+),", g["question"])
        if m and m.group(1) not in tgt_surfaces:
            tgt_surfaces.append(m.group(1))
    order = sorted((joined.find(s), s) for s in tgt_surfaces)
    tgt_by_id = dict(zip(TARGET_LAND_IDS[:len(tgt_surfaces)],
                         [s for _, s in order]))
    # demo lands: find their surface names from rows mentioning them —
    # demos are non-source, non-target lands appearing in the lifetime
    known_surf = set(lands) | set(tgt_surfaces)
    cand_names = set()
    for r in rows:
        for m in re.finditer(r"visit to(?: zone)? ([A-Z][\w-]+)", r):
            cand_names.add(m.group(1))
    demo_surfaces = sorted(cand_names - known_surf,
                           key=lambda s: joined.find(s))
    demo_ids = sorted(world.demo_parents)
    demo_by_id = dict(zip(demo_ids, demo_surfaces))
    print(f"[dl] demos: { {k: (demo_by_id.get(k), [skin_obj.land(p) for p in v]) for k, v in world.demo_parents.items()} }",
          flush=True)

    # tabulated episodic (organized memory, disclosed)
    cell = {}
    for r in rows:
        m = re.search(r"visit to(?: zone)? ([\w-]+), (?:you see the (\w+)\. "
                      r"Its coat is ([\w-]+)|entity (\w+) has state-token "
                      r"([\w-]+))", r)
        if m:
            land, an, col = m.group(1), m.group(2) or m.group(4), \
                (m.group(3) or m.group(5)).rstrip(".")
            cell[(an, land)] = col
    by_animal = defaultdict(dict)
    for (an, land), col in cell.items():
        by_animal[an][land] = col

    be = make_backend("vllm", DREAMER, enable_lora=True, max_lora_rank=64)
    audit = {"raw": []}

    # ---- 1. RECIPES ----
    workshop = [r for r in rows if "mixture" in r.lower()
                or "labeled" in r.lower()]
    out = be.generate([RECIPES.format(lines="\n".join(workshop))],
                      max_tokens=1200)[0]
    audit["raw"].append({"stage": "recipes", "text": out})
    recipes = [l.strip() for l in out.splitlines()
               if l.strip().startswith("RECIPE:")]
    print(f"[dl] recipes: {len(recipes)}", flush=True)

    # ---- 2. ROLES ----
    table = "\n".join(f"{an}: " + ", ".join(f"{l}={c}"
                                            for l, c in sorted(m.items()))
                      for an, m in sorted(by_animal.items()))
    out = be.generate([ROLES.format(table=table)], max_tokens=1500)[0]
    audit["raw"].append({"stage": "roles", "text": out})
    roles = []
    for l in out.splitlines():
        l = l.strip()
        if l.startswith("ROLE:"):
            roles.append(l[5:].strip())
    print(f"[dl] roles: {len(roles)}", flush=True)

    # ---- 3. PARENTS per target, demo as worked example ----
    ex_id = demo_ids[0]
    ex_surf = demo_by_id.get(ex_id, demo_surfaces[0] if demo_surfaces else "?")
    ex_parents = [skin_obj.land(p) for p in world.demo_parents[ex_id]]
    ex_rows = [f"{an} in {ex_surf}: {col}" + " | sources: "
               + ", ".join(f"{p}={by_animal[an].get(p, '?')}"
                           for p in ex_parents)
               for (an, land), col in sorted(cell.items()) if land == ex_surf]
    example = (f"{ex_surf} is publicly known to be fed by "
               f"{' and '.join(ex_parents)}.\n" + "\n".join(ex_rows))
    parent_lines, hyp_audit = [], []
    for tid, tsurf in tgt_by_id.items():
        observed = [(an, col) for (an, land), col in cell.items()
                    if land == tsurf]
        ents = [an for an, _ in observed]
        src_txt = "\n".join(
            f"{an}: " + ", ".join(f"{l}={by_animal[an].get(l, '(not seen; use roles)')}"
                                  for l in lands)
            for an in ents)
        out = be.generate([PARENTS.format(example=example, target=tsurf,
                                          entities=", ".join(ents),
                                          sources=src_txt,
                                          recipes="\n".join(recipes),
                                          k=a.k, e1=ents[0],
                                          e2=ents[1] if len(ents) > 1 else ents[0])],
                          max_tokens=2800)[0]
        audit["raw"].append({"stage": f"parents:{tsurf}", "text": out})
        cands = []
        for l in out.splitlines():
            norm = re.sub(r"^[\-\*\d\.\)\s]+", "", l.strip())
            norm = norm.replace("**", "").strip()
            if norm.startswith("CANDIDATE:"):
                cands.append(norm)
        # HARNESS comparison of BLIND predictions vs PUBLIC observations
        # (mechanical string compare of public data; no solver)
        obs_map = {an: col.lower() for an, col in observed}
        scored = []
        for c in cands:
            m = re.search(r"CANDIDATE:\s*[\w-]+\s*<-\s*([^|]+)\|\s*predicted:\s*(.+)$", c)
            if not m:
                continue
            ps = [p.strip() for p in m.group(1).split(",") if p.strip() in lands]
            preds = dict(re.findall(r"([\w-]+)\s*=\s*([\w-]+)", m.group(2)))
            hits = sum(1 for an, col in obs_map.items()
                       if preds.get(an, "").lower().rstrip(".") == col)
            scored.append({"cand": c, "parents": ps, "hits": hits,
                           "n_obs": len(obs_map)})
        sup = [x for x in scored if x["hits"] == x["n_obs"] and len(x["parents"]) >= 2]
        prov = [x for x in scored if x["hits"] == x["n_obs"] - 1 and len(x["parents"]) >= 2]
        hyp_audit.append({"target": tsurf, "scored": scored})
        keep = sup or prov[:1]
        for x in keep:
            ps = x["parents"]
            tag = "" if x in sup else " (provisional — one prediction unverified)"
            parent_lines.append(
                f"{tsurf}'s outcomes are built from "
                f"{', '.join(ps[:-1])} and {ps[-1]} combined.{tag}")
        print(f"[dl] {tsurf}: {len(cands)} candidates, "
              f"{len(sup)} blind-supported, kept {len(keep)}", flush=True)

    # ---- consolidate corpus (organism format) ----
    principle = ("In this world, an animal's color in a combined land is "
                 "the paint-pigment mixture of that animal's colors in the "
                 "lands that feed that combined land (amounts add).")
    recipe_stmts = [l.replace("RECIPE:", "The color").replace(" denotes ",
                    " denotes a pigment mixture of ", 1)
                    if False else l[7:].strip() for l in recipes]
    statements = parent_lines + roles + recipe_stmts + [principle]
    episodic = [r.split("] ", 1)[1] if "] " in r else r for r in rows]

    def qa_forms(stmts):
        outl = []
        ents = animals + lands + list(tgt_by_id.values())
        for s in stmts:
            es = [e for e in ents if e in s][:2]
            key = " and ".join(es) if es else "this world"
            outl.append(f"Q: What did you conclude about {key}? A: {s}")
            outl.append(s)
        return outl

    path = f"alchemy/v2_out/organism_corpus_{a.skin}_s{a.seed}.json"
    corpus = json.load(open(path))
    corpus["dreamtext"] = statements + episodic
    corpus["dreamlora"] = qa_forms(statements) + episodic
    json.dump(corpus, open(path, "w"), indent=1)

    # ---- offline reporting ONLY ----
    truth = {tgt_by_id[t]: sorted(skin_obj.land(p)
                                  for p in world.target_parents[t])
             for t in tgt_by_id}
    correct = 0
    for tsurf, tp in truth.items():
        got = [pl for pl in parent_lines if pl.startswith(tsurf)]
        hit = any(set(re.findall("|".join(lands), pl)) == set(tp)
                  for pl in got)
        correct += hit
    json.dump({"statements": statements, "hypotheses": hyp_audit,
               "audit": audit,
               "offline_parent_exact": f"{correct}/{len(truth)}"},
              open(f"alchemy/v2_out/dreamladder_{a.skin}_s{a.seed}.json",
                   "w"), indent=1)
    print(f"[dl] statements={len(statements)} "
          f"(parents {len(parent_lines)}, roles {len(roles)}, "
          f"recipes {len(recipe_stmts)}) | OFFLINE parent-exact "
          f"{correct}/{len(truth)}", flush=True)
    print("[dl] DONE", flush=True)


if __name__ == "__main__":
    main()
