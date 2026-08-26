"""C3 phase 2: train the DREAMED corpus (gauge-pinned, verified) into a
LoRA; recognition reads; clean-base pairwise compose. The first full
experience -> dream -> weights -> behavior loop on the Semantic World."""
from __future__ import annotations
import argparse, json, pathlib, subprocess, sys
import torch
from peft import PeftModel

from lands import SemanticWorld, WorldConfig
from lands.skins import make_skin
from alchemy.lora_mem import load_base
from alchemy.run_lands_c012 import score_output, depth_report, PAIRWISE_SUFFIX
from alchemy.run_lands_c2r import candidates_for, score_candidate

MODEL = "Qwen/Qwen2.5-7B-Instruct"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin", default="aligned")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--corpus", default=None,
                    help="path to a corpus json (default: c3c corpus)")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    world = SemanticWorld(WorldConfig(seed=a.seed))
    goals = world.eval_goals()
    skin_obj = make_skin(a.skin, world.animal_ids, world.source_land_ids)
    land_names = [skin_obj.land(l) for l in world.source_land_ids]
    public = world.render(a.skin)
    qmap = {g.goal_id: g.question for g in public.goals}
    cpath_in = a.corpus or f"alchemy/v2_out/lands_c3c_corpus_{a.skin}_s{a.seed}.json"
    bundle = json.load(open(cpath_in))
    qa = bundle["qa"]
    memb = [l for l in qa if "What color was" in l or "position abstraction" in l]
    rules = [l for l in qa if l not in memb]
    lines = memb * 8 + rules * 24
    print(f"[c3p2] corpus: {len(qa)} unique ({len(memb)} memb, {len(rules)} "
          f"rules) -> {len(lines)} lines", flush=True)
    cpath = pathlib.Path(f"alchemy/v2_out/lands_c3p2{a.tag}_train_{a.skin}_s{a.seed}.json")
    json.dump(lines, open(cpath, "w"))
    lora_dir = pathlib.Path(f"alchemy/v2_out/lands_c3p2{a.tag}_lora_{a.skin}_s{a.seed}")
    if not lora_dir.exists():
        code = f"""
import json
from alchemy.lora_mem import load_base, train_lora, read
corpus = json.load(open({str(cpath)!r}))
base, tok = load_base({MODEL!r})
m = train_lora(base, tok, corpus, rank=64, epochs=25, lr=2e-4,
               save_dir={str(lora_dir)!r}, log=print)
print('[gate]', read(m, tok, {qa[0].split(" A: ")[0] + " A:"!r}, 40)[:100])
"""
        assert subprocess.run([sys.executable, "-c", code]).returncode == 0
    canonical = {}
    for line in qa:
        q, ans = line.split(" A: ", 1)
        canonical[q[3:]] = ans
    base, tok = load_base(MODEL)
    model = PeftModel.from_pretrained(base, str(lora_dir))
    model.eval()
    n_reads = n_known = 0
    blocks = []
    for g in goals:
        mems = world.atomic_memories_for(g, a.skin, resolved=False)
        lines_out = []
        for m in mems:
            cands = candidates_for(m.kind, skin_obj, land_names,
                                   skin_obj.meta_land)
            prompt = f"Q: {m.question} A:"
            if cands is None and m.kind == "pigment_map":
                # dreamed corpus has no pigment_map: aligned skin -> prior
                ans = ("RED=R | YELLOW=Y | BLUE=B | ORANGE=R+Y | GREEN=B+Y | "
                       "PURPLE=B+R | BROWN=R+Y+B.")
            elif cands is None:
                ans = canonical.get(m.question, "(no memory)")
            else:
                scores = [score_candidate(model, tok, prompt, c)
                          for c in cands]
                ans = cands[int(torch.tensor(scores).argmax())]
            n_reads += 1
            n_known += int(m.question in canonical
                           or m.kind == "pigment_map")
            lines_out.append(f"- Q: {m.question} A: {ans}")
        blocks.append("\n".join(lines_out))
    print(f"[c3p2] {a.skin} s{a.seed}: read coverage {n_known}/{n_reads} "
          "(fraction of read-plan leaves the dream corpus contains)",
          flush=True)
    outs = []
    with model.disable_adapter():
        for g, block in zip(goals, blocks):
            prompt = ("Verified atomic memory reads:\n" + block
                      + f"\n\n{qmap[g.id]}" + PAIRWISE_SUFFIX)
            ids = tok(prompt, return_tensors="pt").input_ids.to(model.device)
            gen = model.generate(ids, max_new_tokens=900, do_sample=False,
                                 pad_token_id=tok.eos_token_id)
            outs.append(tok.decode(gen[0, ids.shape[1]:],
                                   skip_special_tokens=True))
    oks = [score_output(skin_obj, o, g.answer_color_id)[0]
           for g, o in zip(goals, outs)]
    rep = depth_report(world, goals, oks)
    rep["read_plan_coverage"] = round(n_known / n_reads, 3)
    rep["gauge_fit"] = bundle.get("gauge_fit")
    json.dump(rep, open(f"alchemy/v2_out/lands_c3p2{a.tag}_{a.skin}_s{a.seed}.json",
                        "w"), indent=1)
    print(f"[c3p2{a.tag}] {a.skin} s{a.seed}: "
          + " ".join(f"{d}={v['acc']}" for d, v in rep.items()
                     if isinstance(v, dict)), flush=True)
    print("[c3p2] DONE", flush=True)


if __name__ == "__main__":
    main()
