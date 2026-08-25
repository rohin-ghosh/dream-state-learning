"""C3b: REAL DREAMER with THINKER-ASSEMBLED CITATIONS.
The verifier entails claims only from the CITED observations (a connected
evidence subgraph). C3 failed because the dreamer cited 1-2 lines. C3b:
the dreamer proposes claims off a mechanically tabulated experience view
(reading, provenance kept); a mechanical CITATION ASSEMBLER (the thinker)
finds the connecting evidence path per claim (BFS on the animal-land
graph); the verifier still solely gates truth. No verifier reasons are
fed back into content — accept/reject only.

dream (grammar+citations) -> parse (ClaimCodec) -> verify (witnessed/
entailed only, zero counterfactual budget) -> daydream coverage gaps ->
GAUGE-PINNED claims->QA emission:
  - positions: union-find over verified ANIMAL_EQUIV; POSITION_k assigned
    by canonical order of class representatives (arbitrary but consistent)
  - rotations: propagate verified LAND_RELATION deltas from a reference
    land (rotation 0); palettes from relation fields
  - palette ORDER (the indexing gauge): rotated so that every witnessed
    CELL satisfies palette[(pos + rot) mod 3] == color — evidence pins it
  - meta: from a verified META_RULE claim
Phase 1 stops after emission: reports claim stats, coverage, and checks
the emitted corpus reproduces witnessed cells under the source rule.
Saves the corpus for phase 2 (train + recognition reads + compose).
"""
from __future__ import annotations
import argparse, json, pathlib, re
from collections import defaultdict

from lands import SemanticWorld, WorldConfig
from lands.claims import ClaimCodec, CANONICAL_GRAMMAR
from lands.skins import make_skin
from alchemy.backend import make_backend

MODEL = "Qwen/Qwen2.5-7B-Instruct"

DREAM = """You are the dreamer of an agent that lived in a world of lands
and animals. Below is its tabulated experience: each animal's color per
land, with observation ids.

KEY FACT about this world: within one land, every animal in the same
POSITION FAMILY shows the SAME color. So: two animals that have the same
color in the same land belong together. Use it: go land by land, list
which animals match colors, and emit ANIMAL_EQUIV claims for matching
pairs. Chain across lands to connect animals never seen together.

Also: one special land's colors are BLENDS of the same animal's colors
in a few ordinary lands (paint mixing: red+yellow=orange, yellow+blue=
green, red+blue=purple, all three=brown). If you can identify which
ordinary lands feed it, emit a META_RULE claim naming the parents.

Output claim lines in EXACTLY these forms, each followed by a CITES line
(observation ids that support it):
{grammar}
CITES: <obs_id>, <obs_id>, ...

Example:
ANIMAL_EQUIV | left=fox | right=owl
CITES: obs_00003, obs_00017

Scratch reasoning first is fine. Mark the claims section with a line
saying CLAIMS: and put nothing but claim/CITES lines after it.

EXPERIENCE TABLE:
{log}
"""

DAYDREAM = """You are the dreamer of an agent that lived in a world of
lands and animals. Within one land, animals in the same POSITION FAMILY
show the SAME color — same color in same land means same family.

You have NOT yet connected: {gaps}
Here is every observation in the lands where it appears:
{log}

Go land by land: state {gaps}'s color in that land, then name EVERY
other animal with exactly that color in that land, and emit one
ANIMAL_EQUIV claim per such animal. Also emit (and a META_RULE claim if the special blend-land's
parents become clear). Use EXACTLY these forms, each followed by CITES:
{grammar}
CITES: <obs_id>, <obs_id>, ...
Start the claims section with a line saying CLAIMS:"""


def tabulate(public, skin_obj):
    """Mechanical read of rendered observations -> rows with provenance."""
    rows = []
    pat = re.compile(r"visit to(?: zone)? (\w+), (?:you see the (\w+)\. "
                     r"Its coat is (\w+)|entity (\w+) has state-token (\w+))")
    for o in public.observations:
        m = pat.search(o.text)
        if not m:
            continue
        land = m.group(1)
        animal = m.group(2) or m.group(4)
        color = m.group(3) or m.group(5)
        rows.append((animal, land, color.rstrip("."), o.observation_id))
    return rows


def make_assembler(rows):
    """BFS citation assembler over the animal-land evidence graph."""
    by_pair = defaultdict(list)
    adj = defaultdict(set)
    for a, l, c, oid in rows:
        by_pair[(a, l)].append(oid)
        adj[("A", a)].add(("L", l))
        adj[("L", l)].add(("A", a))

    def path_obs(src, dst):
        from collections import deque
        prev = {src: None}
        dq = deque([src])
        while dq:
            n = dq.popleft()
            if n == dst:
                break
            for nb in adj[n]:
                if nb not in prev:
                    prev[nb] = n
                    dq.append(nb)
        if dst not in prev:
            return None
        path, n = [], dst
        while n is not None:
            path.append(n)
            n = prev[n]
        cites = []
        for i in range(len(path) - 1):
            x, y = path[i], path[i + 1]
            a = x[1] if x[0] == "A" else y[1]
            l = x[1] if x[0] == "L" else y[1]
            cites += by_pair.get((a, l), [])
        return cites

    def assemble(kind, surf):
        if kind == "cell":
            return by_pair.get((surf["animal"], surf["land"]), [])
        if kind == "animal_equiv":
            # connecting path plus ALL obs of both animals (tightens deltas)
            p = path_obs(("A", surf["left"]), ("A", surf["right"]))
            if p is None:
                return []
            extra = [oid for (a, l), oids in by_pair.items()
                     if a in (surf["left"], surf["right"]) for oid in oids]
            return sorted(set(p) | set(extra))
        if kind == "land_relation":
            p = path_obs(("L", surf["left"]), ("L", surf["right"]))
            if p is None:
                return []
            extra = [oid for (a, l), oids in by_pair.items()
                     if l in (surf["left"], surf["right"]) for oid in oids]
            return sorted(set(p) | set(extra))
        if kind == "meta_rule":
            # meta-land obs + every source obs of the meta-observed animals
            meta_animals = {a for (a, l), _ in by_pair.items()
                            if l == surf["meta_land"]}
            return sorted({oid for (a, l), oids in by_pair.items()
                           if a in meta_animals or l == surf["meta_land"]
                           for oid in oids})
        return []
    return assemble


def dream_and_verify(world, skin, be, log_fn=print):
    public = world.render(skin)
    codec = ClaimCodec(world, skin)
    obs_by_id = {o.observation_id: o.text for o in public.observations}
    grammar = "\n".join(CANONICAL_GRAMMAR)
    skin_obj0 = codec.skin
    rows = tabulate(public, skin_obj0)
    assemble = make_assembler(rows)
    meta_surf = skin_obj0.meta_land
    log_fn(f"[c3] tabulated {len(rows)} rows")

    verified, seen_lines = [], set()
    stats = defaultdict(int)

    def absorb(text, tag):
        sec = text.split("CLAIMS:")[-1]
        lines = [l.strip().lstrip("- ") for l in sec.splitlines() if l.strip()]
        i = 0
        while i < len(lines):
            line = lines[i]
            cites = []
            if i + 1 < len(lines) and lines[i + 1].upper().startswith("CITES:"):
                cites = re.findall(r"obs_\d+", lines[i + 1])
                i += 1
            i += 1
            if line in seen_lines:
                continue
            stats["proposed"] += 1
            try:
                claim = codec.parse(line, claim_id=f"{tag}_{stats['proposed']}")
            except Exception:
                stats["unparsed"] += 1
                continue
            surf = {}
            if claim.kind == "cell":
                surf = {"animal": skin_obj0.animal(claim.payload["animal_id"]),
                        "land": skin_obj0.land(claim.payload["land_id"])}
            elif claim.kind == "animal_equiv":
                surf = {"left": skin_obj0.animal(claim.payload["left"]),
                        "right": skin_obj0.animal(claim.payload["right"])}
            elif claim.kind == "land_relation":
                surf = {"left": skin_obj0.land(claim.payload["left"]),
                        "right": skin_obj0.land(claim.payload["right"])}
            elif claim.kind == "meta_rule":
                surf = {"meta_land": meta_surf}
            assembled = assemble(claim.kind, surf)
            cites = sorted(set([c for c in cites if c in obs_by_id]
                               + list(assembled)))
            try:
                res = world.verify_claim(claim, cites,
                                         allow_counterfactual=False)
                ok = res.accepted
            except Exception:
                stats["verify_error"] += 1
                continue
            if ok:
                seen_lines.add(line)
                verified.append((claim, line, cites))
                stats["verified"] += 1
            else:
                stats["rejected"] += 1

    # episodic layer: every witnessed cell is a mechanical claim
    for a_, l_, c_, oid in rows:
        line = f"CELL | animal={a_} | land={l_} | color={c_}"
        try:
            claim = codec.parse(line, claim_id=f"ep_{oid}")
            if world.verify_claim(claim, [oid]).accepted:
                verified.append((claim, line, [oid]))
                seen_lines.add(line)
                stats["verified"] += 1
        except Exception:
            pass
    log_fn(f"[c3] episodic cells: {stats['verified']}")

    # pass 1: full-lifetime dreams over the TABULATED view (x3 samples)
    obs = public.observations
    by_animal = defaultdict(list)
    for a, l, c, oid in rows:
        by_animal[a].append(f"{l}={c} [{oid}]")
    table = "\n".join(f"{a}: " + ", ".join(v)
                       for a, v in sorted(by_animal.items()))
    prompts = [DREAM.format(grammar=grammar, log=table)] * 2
    prompts.append(DREAM.format(grammar=grammar,
                                log="\n".join(o.text for o in obs)))
    for t in be.generate(prompts, max_tokens=2500):
        absorb(t, "d")
    log_fn(f"[c3] pass1: {dict(stats)}")

    # daydream rounds on gaps
    skin_obj = codec.skin
    for rnd in range(6):
        cov_animals = {p["left"] for c, _, _ in verified
                       if c.kind == "animal_equiv"
                       for p in [c.payload]} | \
                      {p["right"] for c, _, _ in verified
                       if c.kind == "animal_equiv"
                       for p in [c.payload]}
        cov_lands = set()
        for c, _, _ in verified:
            if c.kind == "land_relation":
                cov_lands |= {c.payload["left"], c.payload["right"]}
        gaps = [skin_obj.animal(a) for a in world.animal_ids
                if a not in cov_animals] + \
               [skin_obj.land(l) for l in world.source_land_ids
                if l not in cov_lands]
        has_meta = any(c.kind == "meta_rule" for c, _, _ in verified)
        if not has_meta:
            gaps.append(skin_obj.meta_land)
        if not gaps:
            break
        log_fn(f"[c3] daydream round {rnd}: {len(gaps)} gaps: {gaps[:8]}")
        gap_prompts = []
        row_land = defaultdict(list)
        for a_, l_, c_, oid in rows:
            row_land[l_].append(f"{l_}: {a_}={c_} [{oid}]")
        for gname in gaps[:14]:
            if gname == meta_surf:
                # meta gap: the blend inference needs the meta-observed
                # animals' rows across ALL lands
                meta_animals = {a_ for a_, l_, c_, oid in rows
                                if l_ == meta_surf}
                ev = [f"{l_}: {a_}={c_} [{oid}]"
                      for a_, l_, c_, oid in rows if a_ in meta_animals]
                ev.append(f"(Reminder: paint mixing — red+yellow=orange, "
                          f"yellow+blue=green, red+blue=purple, "
                          f"all three=brown. {meta_surf}'s color for an "
                          f"animal is the BLEND of that animal's colors "
                          f"in {meta_surf}'s parent lands.)")
            else:
                glands = {l_ for a_, l_, c_, oid in rows if a_ == gname}
                ev = [ln for l_ in glands for ln in row_land[l_]]
            if not ev:
                ev = [f"{l_}: {a_}={c_} [{oid}]" for a_, l_, c_, oid in rows][:30]
            gap_prompts.append(DAYDREAM.format(
                gaps=gname, log="\n".join(sorted(ev)), grammar=grammar))
        for t in be.generate(gap_prompts, max_tokens=1500):
            absorb(t, "dd")
        log_fn(f"[c3] after round {rnd}: {dict(stats)}")
    return verified, stats


def emit_qa(world, skin, verified, log_fn=print):
    """Gauge-pinned claims -> atomic QA corpus (C2 forms)."""
    skin_obj = make_skin(skin, world.animal_ids, world.source_land_ids)
    cells = {}          # (animal_id, land_id) -> color_id
    equiv_edges = []
    rel = {}            # (l1, l2) -> (pal1, pal2, delta) canonical order
    meta = None
    for c, _, _ in verified:
        p = c.payload
        if c.kind == "cell":
            cells[(p["animal_id"], p["land_id"])] = p["color_id"]
        elif c.kind == "animal_equiv":
            equiv_edges.append((p["left"], p["right"]))
        elif c.kind == "land_relation":
            rel[(p["left"], p["right"])] = (p["left_palette"].upper(),
                                            p["right_palette"].upper(),
                                            int(p["rotation_delta"]))
        elif c.kind == "meta_rule":
            meta = sorted(str(x) for x in p["parents"])
    # positions via union-find over equiv edges
    parent = {a: a for a in world.animal_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in equiv_edges:
        parent[find(a)] = find(b)
    classes = defaultdict(list)
    for a in world.animal_ids:
        classes[find(a)].append(a)
    classes = sorted((sorted(ms) for ms in classes.values()),
                     key=lambda ms: ms[0])
    pos_of = {}
    if len(classes) > 3:
        log_fn(f"[c3] WARN {len(classes)} equiv classes (expected 3); "
               "largest 3 kept, rest uncovered")
    for k, ms in enumerate(sorted(classes, key=len, reverse=True)[:3]):
        for a in ms:
            pos_of[a] = k
    # palettes by CO-OCCURRENCE: colors witnessed in the same source land
    # belong to one triad (a land shows only its own palette)
    lands = sorted(world.source_land_ids)
    land_colors = defaultdict(set)
    for (a, l), col in cells.items():
        if l in lands:
            land_colors[l].add(col)
    cparent = {}
    def cfind(x):
        cparent.setdefault(x, x)
        while cparent[x] != x:
            cparent[x] = cparent[cparent[x]]
            x = cparent[x]
        return x
    for l, cols in land_colors.items():
        cols = sorted(cols)
        for c2 in cols[1:]:
            cparent[cfind(cols[0])] = cfind(c2)
    triads = defaultdict(set)
    for col in {c for cs in land_colors.values() for c in cs}:
        triads[cfind(col)].add(col)
    triads = [sorted(t) for t in triads.values() if len(t) == 3]
    if len(triads) != 2:
        log_fn(f"[c3] GAUGE FAILED: {len(triads)} color triads (need 2)")
        return None, 0.0
    # name triads PRIMARY/SECONDARY by prior convention if possible
    prim_prior = {"red", "yellow", "blue"}
    if set(triads[0]) == prim_prior or set(triads[1]) == prim_prior:
        prim = triads[0] if set(triads[0]) == prim_prior else triads[1]
        sec = triads[1] if prim is triads[0] else triads[0]
    else:
        prim, sec = triads
    fam_of_land = {l: ("PRIMARY" if cols <= set(prim) else "SECONDARY")
                   for l, cols in ((l, set(cs)) for l, cs in land_colors.items())}
    # gauge: palette ORDER shifts; rotations fit per land from positioned cells
    import itertools as _it
    best = None
    for perm in _it.permutations(range(3)):
        pos2 = {a: perm[k] for a, k in pos_of.items()}
        def arrangements(t):
            r = t[::-1]
            return [t[i:] + t[:i] for i in range(3)] + \
                   [r[i:] + r[:i] for i in range(3)]
        for order_p in arrangements(prim):
            for order_s in arrangements(sec):
                order = {"PRIMARY": order_p, "SECONDARY": order_s}
                rot2, fit, tot = {}, 0, 0
                for l in lands:
                    fam = fam_of_land.get(l)
                    if fam is None:
                        continue
                    votes = defaultdict(int)
                    for (a, l2), col in cells.items():
                        if l2 == l and a in pos2 and col in order[fam]:
                            votes[(order[fam].index(col) - pos2[a]) % 3] += 1
                    if votes:
                        rot2[l] = max(votes, key=votes.get)
                for (a, l), col in cells.items():
                    if a in pos2 and l in rot2:
                        tot += 1
                        idx = (pos2[a] + rot2[l]) % 3
                        fit += order[fam_of_land[l]][idx] == col
                if tot and (best is None or fit / tot > best[0]):
                    best = (fit / tot, order, rot2, dict(pos2))
    if best is None:
        log_fn("[c3] GAUGE FAILED: no positioned cells")
        return None, 0.0
    fit_frac, order, rot2, pos_of = best
    pal_of = fam_of_land
    log_fn(f"[c3] gauge fit: {fit_frac:.3f} over {len(cells)} witnessed cells; "
           f"classes {[len(m) for m in classes]}; lands rotated "
           f"{len(rot2)}/{len(lands)}")
    qa = []
    for (a, l), col in cells.items():
        qa.append(f"Q: What color was {skin_obj.animal(a)} in "
                  f"{skin_obj.land(l)}? A: {skin_obj.color(col).upper()}.")
    for a, k in pos_of.items():
        qa.append(f"Q: Which position abstraction describes "
                  f"{skin_obj.animal(a)}? A: POSITION_{k}.")
    for l in lands:
        if l in rot2 and l in pal_of:
            qa.append(f"Q: Which transformation abstraction describes "
                      f"{skin_obj.land(l)}? A: {pal_of[l]}_ROTATION_{rot2[l]}.")
    for fam, cols in order.items():
        qa.append(f"Q: Which visible tokens form the {fam} palette? A: "
                  + " | ".join(skin_obj.color(c).upper() for c in cols) + ".")
    qa.append("Q: How do an animal position and an ordinary-land "
              "transformation determine color? A: "
              "ADD_POSITION_AND_ROTATION_MOD_3_THEN_INDEX_THE_LAND_PALETTE.")
    if meta:
        qa.append(f"Q: Which ordinary lands feed {skin_obj.meta_land}? A: "
                  + " | ".join(skin_obj.land(l) for l in meta) + ".")
        qa.append(f"Q: How does {skin_obj.meta_land} combine its parent "
                  "colors? A: PIGMENT_UNION.")
    return qa, fit_frac


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin", default="aligned")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    world = SemanticWorld(WorldConfig(seed=a.seed))
    be = make_backend("vllm", MODEL, enable_lora=True, max_lora_rank=64)
    verified, stats = dream_and_verify(world, a.skin, be)
    kinds = defaultdict(int)
    for c, _, _ in verified:
        kinds[c.kind] += 1
    print(f"[c3] verified by kind: {dict(kinds)}", flush=True)
    qa, fit = emit_qa(world, a.skin, verified)
    if qa:
        out = pathlib.Path(f"alchemy/v2_out/lands_c3c_corpus_{a.skin}_s{a.seed}.json")
        json.dump({"qa": qa, "gauge_fit": fit, "stats": dict(stats),
                   "kinds": dict(kinds)}, open(out, "w"), indent=1)
        print(f"[c3] emitted {len(qa)} QA lines, gauge_fit {fit:.3f}",
              flush=True)
        for l in qa[:12]:
            print("   ", l, flush=True)
    print("[c3] PHASE1 DONE", flush=True)


if __name__ == "__main__":
    main()
