"""C3stream: INCREMENTAL ASSOCIATIVE DREAMING (Rohin's monkey chain).

Experience arrives episode by episode. After each episode the dreamer
takes AT MOST ONE associative hop per new thought: retrieve memories
related to the new experience (mechanical entity-keyed retrieval),
produce one claim (grammar) with PARENTS, or PASS. A salient hop (a new
claim that parsed) earns up to 2 more hops with focus on the new
thought. Every K episodes: SLEEP — batch self-check (epistemic, with
connector re-check) over provisional thoughts. End: consolidation
(supported claims -> gauge-pinned corpus). Audit records per memory:
episode index, parents, depth, verdicts, offline truth -> emergence
timeline. Arms compared vs batch (C3e) later.
"""
from __future__ import annotations
import argparse, json, pathlib, re
from collections import defaultdict

from lands import SemanticWorld, WorldConfig
from lands.claims import ClaimCodec, CANONICAL_GRAMMAR
from alchemy.backend import make_backend
from alchemy.run_lands_c3c import tabulate, make_assembler, emit_qa

MODEL = "Qwen/Qwen2.5-7B-Instruct"

MICRO = """You are an agent reflecting right after a new experience.

NEW EXPERIENCE:
{new}

RELATED MEMORIES (episodic and previously dreamed thoughts, with ids):
{related}

Take ONE thinking step. Within one land, animals in the same position
family show the same color; family membership is transitive. The special
land's colors may be built from other lands' colors for the same animal
(paint mixing: red+yellow=orange, yellow+blue=green, red+blue=purple,
all three=brown).

If (and only if) something worth remembering follows from connecting the
new experience with these memories, output EXACTLY one claim line:
{grammar}
then one line: PARENTS: <memory ids used>
Otherwise output exactly: PASS"""

SELF_CHECK = """You are checking one of your own dreamed conclusions
against your actual memories.

CLAIM: {claim}

RELEVANT MEMORIES:
{evidence}

Judge: does the EVIDENCE support the claim, contradict it, or is it
insufficient either way? End with exactly one line:
VERDICT: SUPPORTED | CONTRADICTED | PROVISIONAL"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin", default="aligned")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sleep-every", type=int, default=8)
    ap.add_argument("--max-hops", type=int, default=3)
    ap.add_argument("--reinforce", action="store_true",
                    help="duplicate claims reinforce the existing node "
                         "(independent support only if parents differ)")
    ap.add_argument("--sleep-grow", action="store_true",
                    help="sleep also expands: one hop over top-salient "
                         "existing thoughts (dreams over dreams)")
    a = ap.parse_args()
    world = SemanticWorld(WorldConfig(seed=a.seed))
    public = world.render(a.skin)
    codec = ClaimCodec(world, a.skin)
    skin_obj = codec.skin
    grammar = "\n".join(CANONICAL_GRAMMAR)
    rows = tabulate(public, skin_obj)
    assemble = make_assembler(rows)
    meta_surf = skin_obj.meta_land
    be = make_backend("vllm", MODEL, enable_lora=True, max_lora_rank=64)

    # memory store: episodic rows enter as they are experienced
    epi_mem = []          # (mem_id, text, entities)
    thoughts = []         # dicts: id line kind claim parents depth ep_idx status
    seen_lines = set()

    def entities_of(text):
        return {n for n in ([skin_obj.animal(x) for x in world.animal_ids]
                            + [skin_obj.land(l) for l in world.source_land_ids]
                            + [meta_surf]) if n.lower() in text.lower()}

    def retrieve(text, k=12):
        ents = entities_of(text)
        rel = [(mid, t) for mid, t, es in epi_mem if es & ents]
        rel += [(t["id"], t["line"]) for t in thoughts
                if t["status"] != "CONTRADICTED"
                and entities_of(t["line"]) & ents]
        return rel[-k:]

    def normalize(line):
        norm = re.sub(r"^\d+[.)]\s*", "", line.strip().lstrip("- "))
        norm = norm.replace("**", "").replace("`", "").strip()
        norm = re.sub(r",\s+", ",", norm)
        if norm.startswith("META_RULE"):
            norm = re.sub(r"(parents=[^|]+?)\s*\|.*$", r"\1", norm).strip()
        return norm

    def try_parse(text, ep_idx, parents_pool):
        for line in text.splitlines():
            norm = normalize(line)
            if not norm or norm == "PASS":
                continue
            if norm in seen_lines:
                if a.reinforce:
                    m0 = re.search(r"PARENTS:\s*(.+)", text)
                    pset = frozenset(re.findall(r"[a-z]+_\d+|t\d+",
                                                m0.group(1)) if m0 else [])
                    for t in thoughts:
                        if t["line"] == norm:
                            if pset and pset not in t["parent_sets"]:
                                t["support"] += 1
                                t["parent_sets"].append(pset)
                            break
                continue
            try:
                claim = codec.parse(norm, claim_id=f"t{len(thoughts)}")
            except Exception:
                continue
            m = re.search(r"PARENTS:\s*(.+)", text)
            parents = re.findall(r"[a-z]+_\d+|t\d+", m.group(1)) if m else []
            parents = [p for p in parents if p in parents_pool]
            depth = 1 + max([t["depth"] for t in thoughts
                             if t["id"] in parents] + [0])
            seen_lines.add(norm)
            th = {"id": f"t{len(thoughts)}", "line": norm,
                  "kind": claim.kind, "claim": claim, "parents": parents,
                  "depth": depth, "ep_idx": ep_idx, "status": "PROVISIONAL",
                  "support": 1, "parent_sets": [frozenset(parents)]}
            thoughts.append(th)
            return th
        return None

    # ---- stream episodes ----
    eps = defaultdict(list)
    for o in public.observations:
        eps[o.episode_id].append(o)
    ep_ids = sorted(eps)
    print(f"[c3st] streaming {len(ep_ids)} episodes, sleep every "
          f"{a.sleep_every}", flush=True)

    def sleep_check(batch):
        if not batch:
            return
        by_animal = defaultdict(list)
        for an, ln, c, oid in rows:
            by_animal[an].append(f"{ln}={c} [{oid}]")
        def ev(th):
            ents = entities_of(th["line"])
            return "\n".join(f"{n}: " + ", ".join(by_animal[n])
                             for n in sorted(ents) if n in by_animal) or \
                   "\n".join(t for _, t in retrieve(th["line"], 16))
        outs = be.generate([SELF_CHECK.format(claim=t["line"],
                                              evidence=ev(t))
                            for t in batch], max_tokens=700)
        for t, out in zip(batch, outs):
            m = re.search(r"VERDICT:\s*(SUPPORTED|CONTRADICTED|PROVISIONAL)",
                          out.upper())
            if m:
                t["status"] = m.group(1)

    known_ids = set()
    for i, eid in enumerate(ep_ids):
        new_obs = eps[eid]
        for o in new_obs:
            mid = o.observation_id
            epi_mem.append((mid, o.text, entities_of(o.text)))
            known_ids.add(mid)
        new_text = "\n".join(o.text for o in new_obs)
        focus = new_text
        for hop in range(a.max_hops):
            rel = retrieve(focus)
            if not rel:
                break
            prompt = MICRO.format(new=focus, grammar=grammar,
                                  related="\n".join(f"[{mid}] {t}"
                                                    for mid, t in rel))
            out = be.generate([prompt], max_tokens=700)[0]
            th = try_parse(out, i, known_ids | {t["id"] for t in thoughts})
            if th is None:
                break
            focus = th["line"]
        if (i + 1) % a.sleep_every == 0:
            pend = [t for t in thoughts if t["status"] == "PROVISIONAL"]
            sleep_check(pend)
            if a.sleep_grow:
                roots = sorted(
                    [t for t in thoughts if t["status"] != "CONTRADICTED"],
                    key=lambda t: (t["support"], t["depth"], t["ep_idx"]),
                    reverse=True)[:6]
                grew = 0
                for r in roots:
                    rel = retrieve(r["line"])
                    if not rel:
                        continue
                    prompt = MICRO.format(new=r["line"], grammar=grammar,
                                          related="\n".join(
                                              f"[{mid}] {t}" for mid, t in rel))
                    out = be.generate([prompt], max_tokens=700)[0]
                    th = try_parse(out, i,
                                   known_ids | {t["id"] for t in thoughts})
                    grew += th is not None
                if grew:
                    print(f"[c3st] sleep-growth: +{grew} thoughts", flush=True)
            n_by = defaultdict(int)
            for t in thoughts:
                n_by[t["status"]] += 1
            print(f"[c3st] ep {i+1}: {len(thoughts)} thoughts "
                  f"{dict(n_by)} maxdepth "
                  f"{max([t['depth'] for t in thoughts] + [0])}", flush=True)
    sleep_check([t for t in thoughts if t["status"] == "PROVISIONAL"])

    # ---- offline scoring + emergence timeline ----
    surfmap = {"cell": lambda c: {"animal": skin_obj.animal(c.payload["animal_id"]),
                                  "land": skin_obj.land(c.payload["land_id"])},
               "animal_equiv": lambda c: {"left": skin_obj.animal(c.payload["left"]),
                                          "right": skin_obj.animal(c.payload["right"])},
               "land_relation": lambda c: {"left": skin_obj.land(c.payload["left"]),
                                           "right": skin_obj.land(c.payload["right"])},
               "meta_rule": lambda c: {"meta_land": meta_surf}}
    for t in thoughts:
        cites = assemble(t["kind"], surfmap[t["kind"]](t["claim"]))
        try:
            t["offline_true"] = bool(world.verify_claim(t["claim"], cites).accepted)
        except Exception:
            t["offline_true"] = False
    firsts = {}
    for t in thoughts:
        if t["offline_true"] and t["kind"] not in firsts:
            firsts[t["kind"]] = t["ep_idx"]
    sup = [t for t in thoughts if t["status"] == "SUPPORTED"]
    prec = (sum(t["offline_true"] for t in sup) / len(sup)) if sup else None
    print(f"[c3st] thoughts {len(thoughts)}, supported {len(sup)} "
          f"(precision {prec}), first-true-by-kind {firsts}, "
          f"depth>1 count {sum(1 for t in thoughts if t['depth'] > 1)}",
          flush=True)

    # ---- consolidate ----
    verified = [(t["claim"], t["line"], []) for t in sup]
    for an, ln, c, oid in rows:
        try:
            cl = codec.parse(f"CELL | animal={an} | land={ln} | color={c}",
                             claim_id=f"ep_{oid}")
            verified.append((cl, "", [oid]))
        except Exception:
            pass
    qa, fit = emit_qa(world, a.skin, verified)
    out = {"qa": qa or [], "gauge_fit": fit,
           "n_thoughts": len(thoughts), "n_supported": len(sup),
           "firsts": firsts,
           "depth_hist": {d: sum(1 for t in thoughts if t["depth"] == d)
                          for d in range(1, 6)}}
    mode = ("rg" if a.reinforce and a.sleep_grow else
            "r" if a.reinforce else "g" if a.sleep_grow else "")
    json.dump(out, open(f"alchemy/v2_out/lands_c3st{mode}_corpus_{a.skin}_s{a.seed}.json",
                        "w"), indent=1)
    audit = [{k: (v if k != "parent_sets" else [sorted(x) for x in v])
              for k, v in t.items() if k != "claim"} for t in thoughts]
    json.dump(audit, open(f"alchemy/v2_out/lands_c3st{mode}_audit_{a.skin}_s{a.seed}.json",
                          "w"), indent=1)
    print(f"[c3st] corpus {len(qa or [])} lines gauge {fit}", flush=True)
    print("[c3st] DONE", flush=True)


if __name__ == "__main__":
    main()
