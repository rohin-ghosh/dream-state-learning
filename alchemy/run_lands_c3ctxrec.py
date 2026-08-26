"""Context + RECOGNITION reads: the last cell of the substrate x protocol
2x2. Memory block in prompt; each atomic read answered by CANDIDATE
SCORING (logprob) with the block present; clean base composes. HF-only."""
from __future__ import annotations
import argparse, json
import torch
from lands import SemanticWorld, WorldConfig
from lands.skins import make_skin
from alchemy.lora_mem import load_base
from alchemy.run_lands_c012 import score_output, depth_report, PAIRWISE_SUFFIX
from alchemy.run_lands_c2r import candidates_for, score_candidate

MODEL = "Qwen/Qwen2.5-7B-Instruct"

ap = argparse.ArgumentParser()
ap.add_argument("--skin", default="aligned")
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--corpus", required=True)
a = ap.parse_args()
world = SemanticWorld(WorldConfig(seed=a.seed))
goals = world.eval_goals()
skin_obj = make_skin(a.skin, world.animal_ids, world.source_land_ids)
land_names = [skin_obj.land(l) for l in world.source_land_ids]
public = world.render(a.skin)
qmap = {g.goal_id: g.question for g in public.goals}
qa = json.load(open(a.corpus))["qa"]
mem_block = "\n".join(f"- {l}" for l in qa)
base, tok = load_base(MODEL)
base.eval()
canonical = {l.split(" A: ")[0][3:]: l.split(" A: ", 1)[1] for l in qa}
prompts = []
for g in goals:
    mems = world.atomic_memories_for(g, a.skin, resolved=False)
    lines = []
    for m in mems:
        cands = candidates_for(m.kind, skin_obj, land_names, skin_obj.meta_land)
        q = f"Memories:\n{mem_block}\n\nQ: {m.question} A:"
        if cands is None:
            ans = canonical.get(m.question, "(no memory)")
        else:
            scores = [score_candidate(base, tok, q, c) for c in cands]
            ans = cands[int(torch.tensor(scores).argmax())]
        lines.append(f"- Q: {m.question} A: {ans}")
    prompts.append("Verified atomic memory reads:\n" + "\n".join(lines)
                   + f"\n\n{qmap[g.id]}" + PAIRWISE_SUFFIX)
outs = []
with torch.no_grad():
    for p in prompts:
        ids = tok(p, return_tensors="pt").input_ids.to(base.device)
        gen = base.generate(ids, max_new_tokens=900, do_sample=False,
                            pad_token_id=tok.eos_token_id)
        outs.append(tok.decode(gen[0, ids.shape[1]:], skip_special_tokens=True))
oks = [score_output(skin_obj, o, g.answer_color_id)[0]
       for g, o in zip(goals, outs)]
rep = depth_report(world, goals, oks)
rep["n_memory_lines"] = len(qa)
rep["prompt_tokens"] = len(tok(mem_block).input_ids)
json.dump(rep, open(f"alchemy/v2_out/lands_c3ctxrec_{a.skin}_s{a.seed}.json",
                    "w"), indent=1)
print(f"[c3ctxrec] {a.skin} s{a.seed}: "
      + " ".join(f"{d}={v['acc']}" for d, v in rep.items()
                 if isinstance(v, dict))
      + f" (mem tokens {rep['prompt_tokens']})", flush=True)
print("[c3ctxrec] DONE", flush=True)
