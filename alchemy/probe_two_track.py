"""Two-track isolation gate (Rohin 2026-08-26). GH200/HF-only.

TRACK A — thinker question generation: for each goal, the clean model
invents its own read plan ("what would you ask memory?"). Scored:
(1) plan coverage of the proof-required leaf kinds, (2) accuracy when
its OWN questions are answered from the C3e adapter (nearest trained
question via token overlap -> recognition read) and it composes.

TRACK B — memory character probing on the C3e adapter: exact trained
form / paraphrase / REVERSED / partial cue / analogy / free association.
Quantitative scores + a full human-readable transcript
(alchemy/v2_out/probe_transcript_<skin>_s<seed>.txt) for manual review.
"""
from __future__ import annotations
import argparse, json, pathlib, re
import torch
from peft import PeftModel

from lands import SemanticWorld, WorldConfig
from lands.model import GoalDepth
from lands.skins import make_skin
from alchemy.lora_mem import load_base
from alchemy.run_lands_c012 import score_output
from alchemy.run_lands_c2r import candidates_for, score_candidate

MODEL = "Qwen/Qwen2.5-7B-Instruct"

PLAN = """You have a long-term memory you can query with short atomic
questions (one fact per question). You need to answer:

{q}

You know this world has hidden regularities you once dreamed about
(which entities behave alike, how places transform things, how some
places combine others). List up to 6 atomic questions you would ask your
memory to answer this, one per line, no numbering, each ending with a
question mark. Ask only questions a memory could answer with one fact."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin", default="aligned")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    world = SemanticWorld(WorldConfig(seed=a.seed))
    goals = world.eval_goals()
    skin_obj = make_skin(a.skin, world.animal_ids, world.source_land_ids)
    land_names = [skin_obj.land(l) for l in world.source_land_ids]
    public = world.render(a.skin)
    qmap = {g.goal_id: g.question for g in public.goals}
    corpus = json.load(open(f"alchemy/v2_out/lands_c3e_selfcheck_corpus_{a.skin}_s{a.seed}.json"))["qa"]
    trained_qs = [(l.split(" A: ")[0][3:], l.split(" A: ", 1)[1]) for l in corpus]
    base, tok = load_base(MODEL)
    model = PeftModel.from_pretrained(
        base, f"alchemy/v2_out/lands_c3p2_e_lora_{a.skin}_s{a.seed}")
    model.eval()
    T = open(f"alchemy/v2_out/probe_transcript_{a.skin}_s{a.seed}.txt", "w")

    def gen(prompt, n=400, use_adapter=False):
        ctx = torch.no_grad()
        with ctx:
            if use_adapter:
                ids = tok(prompt, return_tensors="pt").input_ids.to(model.device)
                out = model.generate(ids, max_new_tokens=n, do_sample=False,
                                     pad_token_id=tok.eos_token_id)
            else:
                with model.disable_adapter():
                    ids = tok(prompt, return_tensors="pt").input_ids.to(model.device)
                    out = model.generate(ids, max_new_tokens=n, do_sample=False,
                                         pad_token_id=tok.eos_token_id)
            return tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)

    # ================= TRACK A =================
    KIND_CUES = {"animal_position": ("position", "family", "group", "role",
                                     "belong", "behave", "same as", "like"),
                 "land_factor": ("transform", "rotation", "change", "shift",
                                 "does the land", "pattern"),
                 "palette_definition": ("palette", "colors are", "which colors",
                                        "set of colors", "triad"),
                 "witnessed_cell": ("what color", "color of", "color was"),
                 "meta_parents": ("feed", "parent", "combine", "which lands",
                                  "made from", "blend"),
                 "pigment_map": ("mix", "blend", "pigment", "makes what")}
    picks = [g for d in ("D0", "D1", "D2", "D3")
             for g in [x for x in goals if x.depth.value == d][:4]]
    a_rows = []
    T.write("=" * 70 + "\nTRACK A — self-generated read plans\n" + "=" * 70 + "\n")
    for g in picks:
        need_kinds = {m.kind for m in
                      world.atomic_memories_for(g, a.skin, resolved=False)}
        out = gen(PLAN.format(q=qmap[g.id]), 300)
        qs = [l.strip().lstrip("-1234567890.) ") for l in out.splitlines()
              if "?" in l][:6]
        hit_kinds = set()
        for q in qs:
            ql = q.lower()
            for kind, cues in KIND_CUES.items():
                if any(c in ql for c in cues):
                    hit_kinds.add(kind)
        cov = len(hit_kinds & need_kinds) / max(len(need_kinds), 1)
        # answer its OWN questions from the adapter (nearest trained q by
        # token overlap -> recognition read on that kind), then compose
        block = []
        for q in qs:
            qtok = set(re.findall(r"\w+", q.lower()))
            best = max(trained_qs, key=lambda tq:
                       len(qtok & set(re.findall(r"\w+", tq[0].lower()))))
            overlap = len(qtok & set(re.findall(r"\w+", best[0].lower())))
            if overlap < 3:
                block.append(f"- Q: {q} A: (no memory found)")
                continue
            kind = ("animal_position" if "position" in best[0] else
                    "witnessed_cell" if "What color was" in best[0] else
                    "land_factor" if "transformation" in best[0] else
                    "palette_definition" if "palette" in best[0] else
                    "meta_parents" if "feed" in best[0] else "pigment_map")
            cands = candidates_for(kind, skin_obj, land_names, skin_obj.meta_land)
            if cands is None:
                ans = best[1]
            else:
                scores = [score_candidate(model, tok, f"Q: {best[0]} A:", c)
                          for c in cands]
                ans = cands[int(torch.tensor(scores).argmax())]
            block.append(f"- Q: {q} A: {ans}")
        final = gen("Your memory answered:\n" + "\n".join(block)
                    + f"\n\n{qmap[g.id]}\nUse only these memory answers. "
                    "End with:\nFINAL: <one word>", 500)
        ok, _ = score_output(skin_obj, final, g.answer_color_id)
        a_rows.append({"goal": g.id, "depth": g.depth.value,
                       "n_questions": len(qs), "plan_coverage": round(cov, 2),
                       "own_plan_correct": bool(ok)})
        T.write(f"\n--- {g.id} ({g.depth.value}) {qmap[g.id]}\n")
        T.write("ASKED:\n" + "\n".join(f"  {q}" for q in qs) + "\n")
        T.write(f"needed kinds: {sorted(need_kinds)} | hit: {sorted(hit_kinds)}"
                f" | coverage {cov:.2f}\n")
        T.write("MEMORY ANSWERS:\n" + "\n".join(block) + "\n")
        T.write(f"FINAL OUT: {final[-200:]}\nCORRECT: {ok}\n")
    covs = [r["plan_coverage"] for r in a_rows]
    accs = {}
    for d in ("D0", "D1", "D2", "D3"):
        sel = [r for r in a_rows if r["depth"] == d]
        accs[d] = round(sum(r["own_plan_correct"] for r in sel) / len(sel), 2) if sel else None
    print(f"[trackA] plan coverage mean {sum(covs)/len(covs):.2f} | "
          f"own-plan accuracy by depth {accs}", flush=True)

    # ================= TRACK B =================
    T.write("\n" + "=" * 70 + "\nTRACK B — memory character probes\n" + "=" * 70 + "\n")
    memb = [(q, ans) for q, ans in trained_qs
            if "position abstraction describes" in q]
    scores = {}
    def probe(name, make_prompt, expected_fn, items, n=40, use_adapter=True):
        if not items:
            scores[name] = None
            return
        ok = 0
        T.write(f"\n### probe: {name}\n")
        for it in items:
            p = make_prompt(it)
            out = gen(p, 40, use_adapter=use_adapter)
            exp = expected_fn(it)
            hit = exp.lower().rstrip(".") in out.lower()
            ok += hit
            T.write(f"[{'OK' if hit else 'XX'}] {p!r} -> {out[:80]!r} "
                    f"(want {exp})\n")
        scores[name] = round(ok / len(items), 2)
    animal_of = {q.split("describes ")[1].rstrip("?"): ans.rstrip(".")
                 for q, ans in memb}
    items = list(animal_of.items())[:12]
    if not items:
        print("[trackB] no position lines in corpus; skipping", flush=True)
    probe("exact_form", lambda it:
          f"Q: Which position abstraction describes {it[0]}? A:",
          lambda it: it[1], items)
    probe("paraphrase", lambda it:
          f"Q: What is {it[0]}'s position abstraction? A:",
          lambda it: it[1], items)
    probe("partial_cue", lambda it: f"{it[0]}'s position abstraction is",
          lambda it: it[1], items)
    fams = sorted({v for v in animal_of.values()})
    probe("reversed", lambda f:
          f"Q: Name one animal described by {f} A:",
          lambda f: next(a_ for a_, v in animal_of.items() if v == f),
          fams, use_adapter=True)
    pairs = [(a1, a2) for a1, v1 in items for a2, v2 in items
             if v1 == v2 and a1 < a2][:6]
    probe("analogy", lambda p:
          f"Q: {p[0]} and {p[1]} share the same position abstraction: "
          f"true or false? A:", lambda p: "true", pairs)
    T.write("\n### probe: free_association (manual read)\n")
    for an, fam in items[:5]:
        out = gen(f"Tell me everything you remember about {an}.", 120,
                  use_adapter=True)
        T.write(f"--- {an} (true family {fam}):\n{out[:400]}\n")
    print(f"[trackB] probe scores {scores}", flush=True)
    json.dump({"trackA": a_rows, "trackA_summary": {"coverage": covs,
               "own_plan_acc": accs}, "trackB": scores},
              open(f"alchemy/v2_out/probe_two_track_{a.skin}_s{a.seed}.json",
                   "w"), indent=1)
    T.close()
    print("[probe] DONE", flush=True)


if __name__ == "__main__":
    main()
