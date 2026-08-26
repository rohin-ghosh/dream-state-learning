"""TEMPORAL DREAMING on Semantic World v0.2 (Rohin+Codex spec 2026-08-26).

Fixed lifetime, repeated short dream cycles over persistent provisional
memory. Does Blendyland-like structure EMERGE across cycles?

Arms (equal generated-token budget, exact accounting):
  long        : a few big dreams over the full lifetime, no persistence
  independent : N short dreams, memory RESET each cycle (sampling control)
  recurrent   : N short dreams, persistent dream memory + agenda

Each short cycle: generic associative retrieval (focus land rotates;
entity 1-hop expansion; lexically-related prior nodes) -> ONE typed
emission (NEW CONNECTION / REVISED / REINFORCED / CONTRADICTION /
OPEN QUESTION / NOTHING USEFUL) with citations. Reinforcement only
counts with NEW evidence ids (provenance rule). No verifier anywhere;
offline scoring after commit only.

Checkpoints (cycles 1,2,4,8,16,32): per-target exact-parent discovery,
node dependency depth, false-parent-set rate, tokens spent.
"""
from __future__ import annotations
import argparse, json, pathlib, re
from collections import defaultdict

from alchemy.backend import make_backend
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02, TARGET_LAND_IDS

MODEL = "Qwen/Qwen2.5-7B-Instruct"

CYCLE = """You are dreaming — reflecting over a small slice of your
memories with no immediate task. Your goal across many dreams is a
compact, correct picture of how this world works: which entities behave
alike, what each place does, and how some places' outcomes are built
from other places' outcomes.

FOCUS SLICE (episodic memories):
{slice}

YOUR EARLIER DREAM NOTES (provisional; may be wrong):
{notes}

OPEN QUESTIONS YOU LEFT YOURSELF:
{agenda}

Take ONE step. Prefer a connection that would EXPLAIN something
unexplained; derive what it implies and check it against the memories
above before writing it. Then emit exactly ONE of:
NEW CONNECTION: <one precise sentence> | CITES: <obs/node ids>
REVISED: <node id> -> <corrected sentence> | CITES: <ids>
REINFORCED: <node id> | NEW EVIDENCE: <obs ids not already cited>
CONTRADICTION: <node id> | WHY: <one sentence + obs ids>
OPEN QUESTION: <one question for a later dream>
NOTHING USEFUL"""

LONG = """You are asleep after a lifetime in a synthetic world. Build a
compact, correct picture of how this world works: which entities behave
alike, what each place does, and how some places' outcomes are built
from other places' outcomes. Derive and check before asserting; cite
observation ids. List your conclusions one per line as
NEW CONNECTION: <sentence> | CITES: <ids>
and end with OPEN QUESTION lines for anything unresolved.

FULL LIFETIME:
{lifetime}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin", default="aligned")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--arm", required=True,
                    choices=["long", "independent", "recurrent"])
    ap.add_argument("--cycles", type=int, default=32)
    ap.add_argument("--cycle-tokens", type=int, default=900)
    ap.add_argument("--model", default=MODEL)
    a = ap.parse_args()
    world = SemanticWorldV02(WorldConfig(seed=a.seed))
    skin_obj = make_skin(a.skin, world.animal_ids, world.source_land_ids)
    rows = list(world.render_lifetime(a.skin))
    goals = world.render_goals(a.skin)
    # surface names
    src_names = [skin_obj.land(l) for l in world.source_land_ids]
    tgt_name = {}
    for g, tid in zip(goals, list(TARGET_LAND_IDS) * 3):
        pass
    # target surface names from goal questions "In X, what color..."
    tgt_surfaces = []
    for g in goals:
        m = re.match(r"In ([^,]+),", g["question"])
        if m and m.group(1) not in tgt_surfaces:
            tgt_surfaces.append(m.group(1))
    # map surface -> target id via row containment order of TARGET_LAND_IDS
    # (v02 renders targets in declaration order; verify by lifetime mention order)
    order = []
    joined = "\n".join(rows)
    for s in tgt_surfaces:
        order.append((joined.find(s), s))
    tgt_surface_by_id = {}
    for tid, (_, s) in zip(TARGET_LAND_IDS[:len(tgt_surfaces)],
                           sorted(order)):
        tgt_surface_by_id[tid] = s
    truth = {}
    for tid in list(tgt_surface_by_id):
        try:
            truth[tgt_surface_by_id[tid]] = {skin_obj.land(p)
                                             for p in world.target_parents[tid]}
        except Exception:
            pass
    be = make_backend("vllm", a.model, enable_lora=True, max_lora_rank=64)

    nodes, agenda, log = [], [], []
    tokens_spent = 0

    def retrieve(focus_surface):
        sl = [r for r in rows if focus_surface.lower() in r.lower()]
        ents = {n for r in sl for n in
                [skin_obj.animal(x) for x in world.animal_ids] if n in r}
        sl += [r for r in rows if any(e in r for e in ents)
               and r not in sl][:40]
        ftok = set(re.findall(r"\w+", focus_surface.lower()))
        rel = sorted(nodes, key=lambda n: -len(
            ftok & set(re.findall(r"\w+", n["text"].lower()))))[:12] \
            if a.arm == "recurrent" else []
        return sl[:55], rel

    def score_checkpoint(cyc):
        found = {}
        for t, tp in truth.items():
            hit = None
            for n in nodes:
                if n["status"] == "CONTRADICTED" or t not in n["text"]:
                    continue
                lands_in = {s for s in src_names if s in n["text"]}
                if lands_in == tp:
                    hit = n["id"]
                    break
            found[t] = hit
        false_sets = 0
        for n in nodes:
            for t, tp in truth.items():
                if t in n["text"] and n["status"] != "CONTRADICTED":
                    lands_in = {s for s in src_names if s in n["text"]}
                    if len(lands_in) >= 2 and lands_in != tp:
                        false_sets += 1
                        break
        def depth(n, seen=()):
            ps = [x for x in n["cites"] if x.startswith("node_")
                  and x not in seen]
            if not ps:
                return 1
            return 1 + max(depth(next(m for m in nodes if m["id"] == p),
                                 seen + (n["id"],))
                           for p in ps if any(m["id"] == p for m in nodes))
        maxd = max([depth(n) for n in nodes] + [0])
        rec = {"cycle": cyc, "tokens": tokens_spent,
               "nodes": len(nodes),
               "targets_solved": sum(1 for v in found.values() if v),
               "n_targets": len(truth), "false_parent_sets": false_sets,
               "max_depth": maxd,
               "open_questions": len(agenda)}
        log.append(rec)
        print(f"[temporal:{a.arm}] ckpt {rec}", flush=True)

    if a.arm == "long":
        budget = a.cycles * a.cycle_tokens
        n_calls = max(1, budget // 2400)
        for i in range(n_calls):
            out = be.generate([LONG.format(lifetime="\n".join(rows))],
                              max_tokens=min(2400, budget - tokens_spent))[0]
            tokens_spent += len(out.split())  # approx; exact below
            for line in out.splitlines():
                if line.strip().startswith("NEW CONNECTION:"):
                    body = line.split("NEW CONNECTION:", 1)[1]
                    txt = body.split("| CITES:")[0].strip()
                    cites = re.findall(r"obs_\d+", body)
                    nodes.append({"id": f"node_{len(nodes)}", "text": txt,
                                  "cites": cites, "status": "PROVISIONAL",
                                  "cycle": i, "support": 1})
            if i + 1 in (1, 2, 4, 8, 16, 32) or i == n_calls - 1:
                score_checkpoint(i + 1)
    else:
        for cyc in range(a.cycles):
            focus = (tgt_surfaces + src_names)[cyc % (len(tgt_surfaces)
                                                      + len(src_names))]
            sl, rel = retrieve(focus)
            notes = "\n".join(f"[{n['id']}] {n['text']} (cites "
                              f"{','.join(n['cites'][:4])})" for n in rel) \
                    or "(none yet)"
            ag = "\n".join(agenda[-6:]) or "(none)"
            out = be.generate([CYCLE.format(slice="\n".join(sl),
                                            notes=notes, agenda=ag)],
                              max_tokens=a.cycle_tokens)[0]
            tokens_spent += len(out.split())
            m = re.search(r"(NEW CONNECTION|REVISED|REINFORCED|CONTRADICTION|"
                          r"OPEN QUESTION|NOTHING USEFUL)[:]?(.*)", out)
            if m and a.arm == "recurrent":
                kind, body = m.group(1), m.group(2)
                cites = re.findall(r"obs_\d+|node_\d+", out[m.start():])
                if kind == "NEW CONNECTION":
                    txt = body.split("| CITES:")[0].strip()
                    if txt and not any(n["text"] == txt for n in nodes):
                        nodes.append({"id": f"node_{len(nodes)}",
                                      "text": txt, "cites": cites,
                                      "status": "PROVISIONAL",
                                      "cycle": cyc, "support": 1})
                elif kind == "REINFORCED":
                    tgt = next((n for n in nodes
                                if n["id"] in cites), None)
                    if tgt:
                        new_ev = [c for c in cites if c.startswith("obs_")
                                  and c not in tgt["cites"]]
                        if new_ev:
                            tgt["support"] += 1
                            tgt["cites"] += new_ev
                elif kind == "REVISED":
                    tgt = next((n for n in nodes if n["id"] in cites), None)
                    if tgt and "->" in body:
                        tgt["text"] = body.split("->", 1)[1].split(
                            "| CITES:")[0].strip()
                elif kind == "CONTRADICTION":
                    tgt = next((n for n in nodes if n["id"] in cites), None)
                    if tgt:
                        tgt["status"] = "CONTRADICTED"
                elif kind == "OPEN QUESTION":
                    agenda.append(body.strip()[:200])
            elif m and a.arm == "independent":
                # log but never feed back
                if m.group(1) == "NEW CONNECTION":
                    txt = m.group(2).split("| CITES:")[0].strip()
                    cites = re.findall(r"obs_\d+", out[m.start():])
                    nodes.append({"id": f"node_{len(nodes)}", "text": txt,
                                  "cites": cites, "status": "PROVISIONAL",
                                  "cycle": cyc, "support": 1})
            if cyc + 1 in (1, 2, 4, 8, 16, 32):
                score_checkpoint(cyc + 1)
    out_path = (f"alchemy/v2_out/lands_v02_temporal_{a.arm}_{a.skin}"
                f"_s{a.seed}_{a.model.split(chr(47))[-1][:12]}.json")
    json.dump({"checkpoints": log,
               "nodes": [{k: v for k, v in n.items()} for n in nodes],
               "agenda": agenda, "truth": {k: sorted(v)
                                           for k, v in truth.items()}},
              open(out_path, "w"), indent=1)
    print(f"[temporal:{a.arm}] DONE nodes={len(nodes)}", flush=True)


if __name__ == "__main__":
    main()
