"""Show adapter reads + composition for 3 D2 goals (c2, aligned s0)."""
import pathlib
from lands import SemanticWorld, WorldConfig
from lands.model import GoalDepth
from lands.skins import make_skin
from alchemy.backend import make_backend

world = SemanticWorld(WorldConfig(seed=0))
goals = [g for g in world.eval_goals() if g.depth == GoalDepth.D2][:3]
skin_obj = make_skin("aligned", world.animal_ids, world.source_land_ids)
public = world.render("aligned")
qmap = {g.goal_id: g.question for g in public.goals}
be = make_backend("vllm", "Qwen/Qwen2.5-7B-Instruct", enable_lora=True,
                  max_lora_rank=64)
L = str(pathlib.Path("alchemy/v2_out/lands_c2_lora_aligned_s0").resolve())
for g in goals:
    mems = world.atomic_memories_for(g, "aligned", resolved=False)
    reads = be.generate([f"Q: {m.question} A:" for m in mems],
                        max_tokens=32, lora_path=L)
    print(f"=== {g.id} want={skin_obj.color(g.answer_color_id)}")
    for m, r in zip(mems, reads):
        first = r.strip().splitlines()[0] if r.strip() else "?"
        flag = "OK" if m.answer.lower().rstrip(".") in first.lower() else "XX"
        print(f"  [{flag}] {m.question}")
        print(f"        oracle: {m.answer}   adapter: {first[:90]}")
