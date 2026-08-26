"""Dreamed-memory-AS-CONTEXT arm: the self-checked dream corpus (same one
C3e trained into LoRA) placed directly in the prompt, clean base answers.
Isolates the memory SUBSTRATE (weights vs context) at fixed dream
quality. Comparator: c3p2_e (same corpus through LoRA + recognition
reads): D1 0.5 / D2 0.5 / D3 0.167."""
from __future__ import annotations
import argparse, json
from lands import SemanticWorld, WorldConfig
from lands.skins import make_skin
from alchemy.backend import make_backend
from alchemy.run_lands_c012 import score_output, depth_report, PAIRWISE_SUFFIX

MODEL = "Qwen/Qwen2.5-7B-Instruct"

ap = argparse.ArgumentParser()
ap.add_argument("--skin", default="aligned")
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--corpus", required=True)
ap.add_argument("--tag", default="ctx")
a = ap.parse_args()
world = SemanticWorld(WorldConfig(seed=a.seed))
goals = world.eval_goals()
skin_obj = make_skin(a.skin, world.animal_ids, world.source_land_ids)
public = world.render(a.skin)
qmap = {g.goal_id: g.question for g in public.goals}
qa = json.load(open(a.corpus))["qa"]
mem_block = "\n".join(f"- {l}" for l in qa)
be = make_backend("vllm", MODEL, enable_lora=True, max_lora_rank=64)
prompts = [f"Your consolidated memories:\n{mem_block}\n\n{qmap[g.id]}"
           + PAIRWISE_SUFFIX for g in goals]
outs = []
for i in range(0, len(prompts), 24):
    outs += be.generate(prompts[i:i + 24], max_tokens=1200)
oks = [score_output(skin_obj, o, g.answer_color_id)[0]
       for g, o in zip(goals, outs)]
rep = depth_report(world, goals, oks)
rep["n_memory_lines"] = len(qa)
json.dump(rep, open(f"alchemy/v2_out/lands_c3{a.tag}_{a.skin}_s{a.seed}.json",
                    "w"), indent=1)
print(f"[c3ctx] {a.tag} {a.skin} s{a.seed}: "
      + " ".join(f"{d}={v['acc']}" for d, v in rep.items()
                 if isinstance(v, dict)), flush=True)
print("[c3ctx] DONE", flush=True)
