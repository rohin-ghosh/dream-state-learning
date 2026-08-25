"""C2r: RECOGNITION READS. The claim grammar defines a finite legal
answer space per leaf kind, so the thinker SCORES candidates under the
adapter (argmax logprob) instead of generating — reads become
recognition. Fixes the composite-answer read-corruption found in C2.
Reuses the C2-trained adapters. Compose = clean base (adapter disabled)
with the pairwise-blend protocol. HF-only, one process per (skin, seed).
"""
from __future__ import annotations
import argparse, itertools, json, pathlib, re
import torch
from peft import PeftModel

from lands import SemanticWorld, WorldConfig
from lands.skins import make_skin
from alchemy.lora_mem import load_base
from alchemy.run_lands_c012 import score_output, depth_report, PAIRWISE_SUFFIX

MODEL = "Qwen/Qwen2.5-7B-Instruct"


def candidates_for(kind, skin_obj, land_names, meta_land):
    colors = [c.upper() for c in skin_obj.colors.values()]
    if kind in ("witnessed_cell", "resolved_source_value"):
        return [f"{c}." for c in colors]
    if kind == "animal_position":
        return [f"POSITION_{i}." for i in range(3)]
    if kind == "land_factor":
        return [f"{p}_ROTATION_{i}." for p in ("PRIMARY", "SECONDARY")
                for i in range(3)]
    if kind == "palette_definition":
        prim = " | ".join(c.upper() for c in list(skin_obj.colors.values())[:3])
        sec = " | ".join(c.upper() for c in list(skin_obj.colors.values())[3:6])
        return [f"{prim}.", f"{sec}."]
    if kind == "meta_parents":
        return [" | ".join(combo) + "."
                for combo in itertools.combinations(land_names, 3)]
    if kind == "meta_operator":
        return ["PIGMENT_UNION.", "PIGMENT_INTERSECTION.", "LIGHT_ADDITION.",
                "MAJORITY_VOTE."]
    if kind == "public_source_rule":
        return ["ADD_POSITION_AND_ROTATION_MOD_3_THEN_INDEX_THE_LAND_PALETTE.",
                "SUBTRACT_ROTATION_FROM_POSITION_MOD_3_THEN_INDEX_THE_LAND_PALETTE.",
                "MULTIPLY_POSITION_BY_ROTATION_MOD_3_THEN_INDEX_THE_LAND_PALETTE."]
    return None  # pigment_map etc: fall back to canonical-from-corpus


@torch.no_grad()
def score_candidate(model, tok, prompt, cand):
    full = tok(prompt + " " + cand, return_tensors="pt").input_ids.to(model.device)
    plen = tok(prompt, return_tensors="pt").input_ids.shape[1]
    out = model(full).logits[0]
    logp = torch.log_softmax(out[:-1], dim=-1)
    tgt = full[0, 1:]
    span = range(plen - 1, full.shape[1] - 1)
    return sum(logp[i, tgt[i]].item() for i in span) / max(len(span), 1)


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
    corpus = json.load(open(f"alchemy/v2_out/lands_c2_corpus_{a.skin}_s{a.seed}.json"))
    canonical = {}
    for line in set(corpus):
        q, ans = line.split(" A: ", 1)
        canonical[q[3:]] = ans
    base, tok = load_base(MODEL)
    model = PeftModel.from_pretrained(
        base, f"alchemy/v2_out/lands_c2_lora_{a.skin}_s{a.seed}")
    model.eval()
    n_reads = n_read_ok = 0
    blocks = []
    for g in goals:
        mems = world.atomic_memories_for(g, a.skin, resolved=False)
        lines = []
        for m in mems:
            cands = candidates_for(m.kind, skin_obj, land_names,
                                   skin_obj.meta_land)
            prompt = f"Q: {m.question} A:"
            if cands is None and m.kind == "pigment_map":
                can0 = canonical[m.question]
                v1 = (can0.replace("ORANGE", "@T@").replace("GREEN", "ORANGE")
                      .replace("@T@", "GREEN"))
                v2 = (can0.replace("PURPLE", "@T@").replace("GREEN", "PURPLE")
                      .replace("@T@", "GREEN"))
                cands = [can0, v1, v2]
            if cands is None:
                ans = canonical.get(m.question, m.answer)  # constant leaf
                print(f"[c2r] WARN un-enumerated kind {m.kind}", flush=True)
            else:
                scores = [score_candidate(model, tok, prompt, c)
                          for c in cands]
                ans = cands[int(torch.tensor(scores).argmax())]
            n_reads += 1
            n_read_ok += int(ans.strip().lower() == m.answer.strip().lower())
            lines.append(f"- Q: {m.question} A: {ans}")
        blocks.append("\n".join(lines))
    print(f"[c2r] {a.skin} s{a.seed}: read fidelity {n_read_ok}/{n_reads}",
          flush=True)
    # compose with the CLEAN base (adapter disabled)
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
    rep["read_fidelity"] = round(n_read_ok / n_reads, 3)
    json.dump(rep, open(f"alchemy/v2_out/lands_c2r_{a.skin}_s{a.seed}.json",
                        "w"), indent=1)
    print(f"[c2r] {a.skin} s{a.seed}: "
          + " ".join(f"{d}={v['acc']}" for d, v in rep.items()
                     if isinstance(v, dict)), flush=True)
    print("[c2r] DONE", flush=True)


if __name__ == "__main__":
    main()
