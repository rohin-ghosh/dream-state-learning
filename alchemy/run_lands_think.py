"""ADAPTIVE THINKER (T1): think-budget scales with the question.

Stage A (cheap): membership recognition reads only -> direct compose,
  self-assessment line: KNOW / UNSURE.
Stage B (escalate if UNSURE): full recognition read plan + pairwise
  protocol -> self-assessment again.
Stage C (chain if still UNSURE): model states what's missing; one more
  targeted thought over the read block ("do I have another connection?");
  if it emits a grammar claim, it is WRITTEN as a provisional memory node
  (thinking feeds dreaming; logged). Final answer with a RANGE (top-2).
Metrics: accuracy, calibration (KNOW vs UNSURE accuracy), range-hit-rate,
mean reads per depth (adaptive-compute curve).
Uses the C3e self-check LoRA (verifier-free memory).
"""
from __future__ import annotations
import argparse, json, pathlib, re
import torch
from peft import PeftModel

from lands import SemanticWorld, WorldConfig
from lands.model import GoalDepth
from lands.skins import make_skin
from alchemy.lora_mem import load_base
from alchemy.run_lands_c012 import score_output, depth_report
from alchemy.run_lands_c2r import candidates_for, score_candidate

MODEL = "Qwen/Qwen2.5-7B-Instruct"

ASSESS = ("\nAfter answering, judge yourself: do you actually KNOW this "
          "from the memories above, or are you unsure? End with two lines:"
          "\nFINAL: <one word>\nSTATUS: KNOW | UNSURE")

CHAIN = """You are stuck on a question. Your memory reads so far:
{block}

Question: {q}

State in one line what is MISSING. Then check: can you form another
connection from what you do have (family membership is transitive; the
special land may combine other lands' colors)? If yes, state it as one
grammar line:
CELL | animal=<a> | land=<l> | color=<c>
ANIMAL_EQUIV | left=<a> | right=<b>
Then give your best answer anyway with a RANGE of up to 2 colors:
FINAL: <best one word>
RANGE: <word>, <word>"""


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
    base, tok = load_base(MODEL)
    model = PeftModel.from_pretrained(
        base, f"alchemy/v2_out/lands_c3p2_e_lora_{a.skin}_s{a.seed}")
    model.eval()

    def rec_read(question, kind):
        cands = candidates_for(kind, skin_obj, land_names, skin_obj.meta_land)
        if cands is None:
            return None
        prompt = f"Q: {question} A:"
        scores = [score_candidate(model, tok, prompt, c) for c in cands]
        return cands[int(torch.tensor(scores).argmax())]

    def gen(prompt, n=700):
        with model.disable_adapter(), torch.no_grad():
            ids = tok(prompt, return_tensors="pt").input_ids.to(model.device)
            out = model.generate(ids, max_new_tokens=n, do_sample=False,
                                 pad_token_id=tok.eos_token_id)
            return tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)

    results, thought_nodes = [], []
    for g in goals:
        mems = world.atomic_memories_for(g, a.skin, resolved=False)
        n_reads = 0
        # Stage A: memberships only, direct compose
        cheap = [m for m in mems if m.kind in
                 ("witnessed_cell", "animal_position")]
        block_lines = []
        for m in cheap:
            ans = rec_read(m.question, m.kind)
            n_reads += 1
            if ans:
                block_lines.append(f"- Q: {m.question} A: {ans}")
        block = "\n".join(block_lines)
        out = gen(f"What you remember:\n{block}\n\n{qmap[g.id]}" + ASSESS, 400)
        status = "UNSURE"
        m0 = re.search(r"STATUS:\s*(KNOW|UNSURE)", out.upper())
        if m0:
            status = m0.group(1)
        stage = "A"
        rng = []
        if status != "KNOW":
            # Stage B: full plan + pairwise
            stage = "B"
            block_lines = []
            for m in mems:
                if m.kind == "pigment_map":
                    ans = ("RED=R | YELLOW=Y | BLUE=B | ORANGE=R+Y | "
                           "GREEN=B+Y | PURPLE=B+R | BROWN=R+Y+B.")
                else:
                    ans = rec_read(m.question, m.kind)
                    n_reads += 1
                if ans:
                    block_lines.append(f"- Q: {m.question} A: {ans}")
            block = "\n".join(block_lines)
            out = gen("Verified atomic memory reads:\n" + block
                      + f"\n\n{qmap[g.id]}\nUse ONLY the memory reads. If "
                      "blending is required, blend two at a time using the "
                      "given equations." + ASSESS, 900)
            m0 = re.search(r"STATUS:\s*(KNOW|UNSURE)", out.upper())
            status = m0.group(1) if m0 else "UNSURE"
        if status != "KNOW":
            # Stage C: chain — what's missing + another connection + range
            stage = "C"
            out = gen(CHAIN.format(block=block, q=qmap[g.id]), 900)
            for line in out.splitlines():
                norm = re.sub(r"^\d+[.)]\s*", "", line.strip().lstrip("- "))
                norm = norm.replace("**", "").strip()
                if norm.startswith(("CELL |", "ANIMAL_EQUIV |")):
                    thought_nodes.append({"goal": g.id, "line": norm})
            mr = re.search(r"RANGE:\s*(.+)", out)
            if mr:
                rng = [w.strip().lower().rstrip(".") for w in
                       mr.group(1).split(",")][:2]
        ok, got = score_output(skin_obj, out, g.answer_color_id)
        truth_surface = skin_obj.color(g.answer_color_id).lower()
        results.append({"goal": g.id, "depth": g.depth.value, "stage": stage,
                        "status": status, "reads": n_reads, "ok": bool(ok),
                        "range_hit": truth_surface in rng if rng else None})
    rep = depth_report(world, goals, [r["ok"] for r in results])
    know = [r for r in results if r["status"] == "KNOW"]
    unsure = [r for r in results if r["status"] != "KNOW"]
    rep["calibration"] = {
        "know_n": len(know),
        "know_acc": round(sum(r["ok"] for r in know) / len(know), 3) if know else None,
        "unsure_n": len(unsure),
        "unsure_acc": round(sum(r["ok"] for r in unsure) / len(unsure), 3) if unsure else None}
    rngs = [r for r in results if r["range_hit"] is not None]
    rep["range_hit_rate"] = (round(sum(r["range_hit"] for r in rngs) / len(rngs), 3)
                             if rngs else None)
    rep["mean_reads_by_depth"] = {
        d: round(sum(r["reads"] for r in results if r["depth"] == d)
                 / max(1, sum(1 for r in results if r["depth"] == d)), 1)
        for d in ("D0", "D1", "D2", "D3")}
    rep["stages"] = {s: sum(1 for r in results if r["stage"] == s)
                     for s in "ABC"}
    rep["thought_nodes_written"] = len(thought_nodes)
    json.dump({"rep": rep, "results": results, "thoughts": thought_nodes},
              open(f"alchemy/v2_out/lands_think_{a.skin}_s{a.seed}.json", "w"),
              indent=1)
    print(f"[think] {a.skin} s{a.seed}: "
          + " ".join(f"{d}={v['acc']}" for d, v in rep.items()
                     if isinstance(v, dict) and "acc" in v), flush=True)
    print(f"[think] calibration {rep['calibration']} | range_hit "
          f"{rep['range_hit_rate']} | reads/depth {rep['mean_reads_by_depth']} "
          f"| stages {rep['stages']} | thoughts {len(thought_nodes)}", flush=True)
    print("[think] DONE", flush=True)


if __name__ == "__main__":
    main()
