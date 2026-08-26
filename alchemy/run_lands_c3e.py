"""C3e: EPISTEMIC self-check loop (UNRESOLVED is a queue, not a trash can).
Changes from C3s: (1) parser normalization also strips list numbering and
markdown bold (the drift-round killer); (2) verdicts are SUPPORTED /
CONTRADICTED / PROVISIONAL; (3) PROVISIONAL equivalences get a SECOND
check with connector-augmented evidence (a third animal sharing a land
with each — mechanical retrieval, model judges transitivity); (4) the
check prompt carries the current accepted-structure neighborhood, with
evidence ruling over structure.

One dream batch -> grammar parse (structure only, no truth check) ->
  arm NOGATE : every parsed claim becomes memory
  arm SELFCHECK : each claim gets a reflection pass (retrieve own
    evidence rows, model marks SUPPORTED / CONTRADICTED / UNRESOLVED);
    only SUPPORTED claims become memory. False self-approved memories
    STAY and their downstream cost is measured.
DREAM DRIFT round: the dreamer re-dreams over its OWN accepted claims
("what do these conclusions have in common? connect them") aiming at
higher-order rules (META_RULE) without game-specific targeting.
FactorSolver scores every unique proposal OFFLINE afterward (reported
only; feedback never reaches the dreamer).
Outputs: two corpora + a full audit JSON (raw dream texts, every claim
with self-check status and offline truth).
"""
from __future__ import annotations
import argparse, json, pathlib, re
from collections import defaultdict

from lands import SemanticWorld, WorldConfig
from lands.claims import ClaimCodec, CANONICAL_GRAMMAR
from alchemy.backend import make_backend
from alchemy.run_lands_c3c import tabulate, make_assembler, emit_qa, DREAM, DAYDREAM

MODEL = "Qwen/Qwen2.5-7B-Instruct"

SELF_CHECK = """You are checking one of your own dreamed conclusions
against your actual memories.

CLAIM: {claim}

RELEVANT MEMORIES (everything you lived involving these entities):
{evidence}

You also currently hold these conclusions (they may themselves be
wrong — direct evidence always outranks them):
{structure}

Judge: does the EVIDENCE support the claim, contradict it, or is it
insufficient either way? What would the claim predict about these
memories, and do they match? End with exactly one line:
VERDICT: SUPPORTED | CONTRADICTED | PROVISIONAL"""

RECHECK = """You earlier marked this dreamed conclusion PROVISIONAL for
lack of direct evidence. Here is a WIDER view: every memory of both
entities, plus a third entity that shares situations with each of them
(family membership is transitive — if A matches C and C matches B, then
A and B belong together).

CLAIM: {claim}

MEMORIES:
{evidence}

Trace the chain explicitly, then end with exactly one line:
VERDICT: SUPPORTED | CONTRADICTED | PROVISIONAL"""

DRIFT = """You are dreaming again — this time over your OWN earlier
conclusions, not raw experience. Here are the conclusions you currently
hold, plus your memories of one situation you have not explained:

CONCLUSIONS:
{claims}

UNEXPLAINED SITUATION ({meta_land}) — your memories of the entities seen
there, across all situations:
{evidence}

Look for a HIGHER-ORDER connection: is this situation's outcome built
from the outcomes of other situations combined in some way? What do the
cases have in common? Derive what your best explanation predicts and
check it against the memories above. Propose your TOP 3 candidate rules, best first, each in grammar form
followed by CITES (no spaces after commas in parents=):
{grammar}
CITES: <obs_id>, <obs_id>, ...
Start the claims section with a line saying CLAIMS:"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin", default="aligned")
    ap.add_argument("--seed", type=int, default=0)
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

    # ---- dream batch (game-informed prompts allowed; NO verifier) ----
    proposals, seen = [], set()
    raw_texts = []

    def absorb(text, stage):
        raw_texts.append({"stage": stage, "text": text})
        sec = text.split("CLAIMS:")[-1]
        lines = [l.strip().lstrip("- ") for l in sec.splitlines() if l.strip()]
        for line in lines:
            if line.upper().startswith("CITES:") or line in seen:
                continue
            norm = re.sub(r"^\d+[.)]\s*", "", line)
            norm = norm.replace("**", "").replace("`", "").strip()
            norm = re.sub(r",\s+", ",", norm)
            if norm.startswith("META_RULE"):
                norm = re.sub(r"(parents=[^|]+?)\s*\|.*$", r"\1", norm).strip()
            try:
                claim = codec.parse(norm, claim_id=f"p{len(proposals)}")
            except Exception:
                continue
            line = norm
            seen.add(line)
            proposals.append({"line": line, "kind": claim.kind,
                              "claim": claim, "stage": stage})

    by_animal = defaultdict(list)
    for an, ln, c, oid in rows:
        by_animal[an].append(f"{ln}={c} [{oid}]")
    table = "\n".join(f"{an}: " + ", ".join(v)
                      for an, v in sorted(by_animal.items()))
    for t in be.generate([DREAM.format(grammar=grammar, log=table)] * 3,
                         max_tokens=2500):
        absorb(t, "dream")
    # per-entity daydreams (coverage), still verifier-free
    row_land = defaultdict(list)
    for an, ln, c, oid in rows:
        row_land[ln].append(f"{ln}: {an}={c} [{oid}]")
    animals = sorted({an for an, _, _, _ in rows})
    dd = []
    for gname in animals:
        glands = {ln for an, ln, c, oid in rows if an == gname}
        ev = sorted({x for l_ in glands for x in row_land[l_]})
        dd.append(DAYDREAM.format(gaps=gname, log="\n".join(ev),
                                  grammar=grammar))
    for i in range(0, len(dd), 8):
        for t in be.generate(dd[i:i + 8], max_tokens=1500):
            absorb(t, "daydream")
    print(f"[c3e] proposals after dream+daydream: {len(proposals)} "
          f"{dict((k, sum(1 for p in proposals if p['kind'] == k)) for k in {p['kind'] for p in proposals})}",
          flush=True)

    # ---- SELF-CHECK pass (model reflection; no oracle anywhere) ----
    def evidence_for(p):
        c = p["claim"]
        names = []
        if c.kind == "cell":
            names = [skin_obj.animal(c.payload["animal_id"])]
        elif c.kind == "animal_equiv":
            names = [skin_obj.animal(c.payload["left"]),
                     skin_obj.animal(c.payload["right"])]
        elif c.kind == "land_relation":
            lids = [c.payload["left"], c.payload["right"]]
            return "\n".join(sorted({x for l in lids
                                     for x in row_land[skin_obj.land(l)]}))
        elif c.kind == "meta_rule":
            metas = {an for an, ln, _, _ in rows if ln == meta_surf}
            return "\n".join(f"{an}: " + ", ".join(by_animal[an])
                             for an in sorted(metas))
        if c.kind == "animal_equiv" and len(names) == 2:
            l2c = {n: {} for n in names}
            for an, ln, col, oid in rows:
                if an in l2c:
                    l2c[an][ln] = f"{col} [{oid}]"
            shared = sorted(set(l2c[names[0]]) | set(l2c[names[1]]))
            return "\n".join(
                f"{ln}: {names[0]}={l2c[names[0]].get(ln, '(not seen)')}, "
                f"{names[1]}={l2c[names[1]].get(ln, '(not seen)')}"
                for ln in shared)
        return "\n".join(f"{n}: " + ", ".join(by_animal[n]) for n in names)

    def structure_view():
        acc = [p["line"] for p in proposals
               if p.get("selfcheck") == "SUPPORTED"][:20]
        return "\n".join(acc) if acc else "(none yet)"

    checks = be.generate([SELF_CHECK.format(claim=p["line"],
                                            evidence=evidence_for(p),
                                            structure="(none yet)")
                          for p in proposals], max_tokens=800)
    for p, out in zip(proposals, checks):
        m = re.search(r"VERDICT:\s*(SUPPORTED|CONTRADICTED|PROVISIONAL|UNRESOLVED)",
                      out.upper())
        v = m.group(1) if m else "UNPARSED"
        p["selfcheck"] = "PROVISIONAL" if v == "UNRESOLVED" else v
    sc = defaultdict(int)
    for p in proposals:
        sc[p["selfcheck"]] += 1
    print(f"[c3e] self-check verdicts: {dict(sc)}", flush=True)

    # ---- PROVISIONAL RE-CHECK: connector-augmented second pass ----
    land_sets = defaultdict(set)
    for an, ln, c, oid in rows:
        land_sets[an].add(ln)
    prov = [p for p in proposals
            if p["selfcheck"] == "PROVISIONAL"
            and p["kind"] == "animal_equiv"]
    def connector_evidence(p):
        c = p["claim"]
        x = skin_obj.animal(c.payload["left"])
        y = skin_obj.animal(c.payload["right"])
        best = None
        for z in land_sets:
            if z in (x, y):
                continue
            sx = land_sets[z] & land_sets[x]
            sy = land_sets[z] & land_sets[y]
            if sx and sy and (best is None or len(sx) + len(sy) > best[0]):
                best = (len(sx) + len(sy), z)
        names = [x, y] + ([best[1]] if best else [])
        return "\n".join(f"{n}: " + ", ".join(by_animal[n]) for n in names)
    if prov:
        rc = be.generate([RECHECK.format(claim=p["line"],
                                         evidence=connector_evidence(p))
                          for p in prov], max_tokens=900)
        promoted = 0
        for p, out in zip(prov, rc):
            m = re.search(r"VERDICT:\s*(SUPPORTED|CONTRADICTED|PROVISIONAL)",
                          out.upper())
            if m and m.group(1) != "PROVISIONAL":
                p["selfcheck"] = m.group(1)
                promoted += m.group(1) == "SUPPORTED"
        print(f"[c3e] provisional re-check: {len(prov)} queued, "
              f"{promoted} promoted to SUPPORTED", flush=True)
    sc2 = defaultdict(int)
    for p in proposals:
        sc2[p["selfcheck"]] += 1
    print(f"[c3e] verdicts after re-check: {dict(sc2)}", flush=True)

    # ---- DREAM DRIFT over accepted claims (higher-order round) ----
    accepted = [p for p in proposals if p["selfcheck"] == "SUPPORTED"]
    metas = {an for an, ln, _, _ in rows if ln == meta_surf}
    drift_ev = "\n".join(f"{an}: " + ", ".join(by_animal[an])
                         for an in sorted(metas))
    drift_prompts = [DRIFT.format(
        claims="\n".join(p["line"] for p in accepted[:50]),
        meta_land=meta_surf, evidence=drift_ev, grammar=grammar)] * 3
    n_before = len(proposals)
    for t in be.generate(drift_prompts, max_tokens=2500):
        absorb(t, "drift")
    drift_new = proposals[n_before:]
    if drift_new:
        checks = be.generate([SELF_CHECK.format(claim=p["line"],
                                                evidence=evidence_for(p),
                                                structure=structure_view())
                              for p in drift_new], max_tokens=800)
        for p, out in zip(drift_new, checks):
            m = re.search(r"VERDICT:\s*(SUPPORTED|CONTRADICTED|PROVISIONAL|UNRESOLVED)",
                          out.upper())
            v = m.group(1) if m else "UNPARSED"
        p["selfcheck"] = "PROVISIONAL" if v == "UNRESOLVED" else v
    print(f"[c3e] drift round: {len(drift_new)} new proposals "
          f"({sum(1 for p in drift_new if p['kind'] == 'meta_rule')} meta)",
          flush=True)

    # ---- OFFLINE scoring (reported only; never fed back) ----
    surfmap = {"cell": lambda c: {"animal": skin_obj.animal(c.payload["animal_id"]),
                                  "land": skin_obj.land(c.payload["land_id"])},
               "animal_equiv": lambda c: {"left": skin_obj.animal(c.payload["left"]),
                                          "right": skin_obj.animal(c.payload["right"])},
               "land_relation": lambda c: {"left": skin_obj.land(c.payload["left"]),
                                           "right": skin_obj.land(c.payload["right"])},
               "meta_rule": lambda c: {"meta_land": meta_surf}}
    for p in proposals:
        cites = assemble(p["kind"], surfmap[p["kind"]](p["claim"]))
        try:
            p["offline_true"] = bool(world.verify_claim(p["claim"], cites).accepted)
        except Exception:
            p["offline_true"] = False
    def precision(sel):
        sel = list(sel)
        return (round(sum(p["offline_true"] for p in sel) / len(sel), 3)
                if sel else None)
    print(f"[c3e] OFFLINE precision: raw {precision(proposals)} | "
          f"selfcheck-SUPPORTED {precision(p for p in proposals if p['selfcheck'] == 'SUPPORTED')} | "
          f"CONTRADICTED(true-rate) {precision(p for p in proposals if p['selfcheck'] == 'CONTRADICTED')}",
          flush=True)

    # ---- build the two corpora (episodic cells always included) ----
    def build_corpus(sel, tag):
        verified = [(p["claim"], p["line"], []) for p in sel]
        for an, ln, c, oid in rows:  # episodic layer, mechanical
            line = f"CELL | animal={an} | land={ln} | color={c}"
            try:
                cl = codec.parse(line, claim_id=f"ep_{oid}")
                verified.append((cl, line, [oid]))
            except Exception:
                pass
        qa, fit = emit_qa(world, a.skin, verified)
        out = {"qa": qa or [], "gauge_fit": fit,
               "n_claims": len(sel)}
        path = f"alchemy/v2_out/lands_c3e_{tag}_corpus_{a.skin}_s{a.seed}.json"
        json.dump(out, open(path, "w"), indent=1)
        print(f"[c3e] arm {tag}: {len(sel)} dreamed claims -> "
              f"{len(qa or [])} QA lines, gauge_fit {fit}", flush=True)

    build_corpus([p for p in proposals], "nogate")
    build_corpus([p for p in proposals if p["selfcheck"] == "SUPPORTED"],
                 "selfcheck")
    audit = [{k: v for k, v in p.items() if k != "claim"} for p in proposals]
    json.dump({"proposals": audit, "raw_texts": raw_texts},
              open(f"alchemy/v2_out/lands_c3e_audit_{a.skin}_s{a.seed}.json",
                   "w"), indent=1)
    print("[c3e] DONE", flush=True)


if __name__ == "__main__":
    main()
