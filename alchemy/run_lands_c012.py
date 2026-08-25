"""C0/C1/C2 of the Semantic World GPU ladder (lands/HANDOFF_FABLE.md).

C0  : full lifetime in context               -> clean-model context ceiling
C1a : context-oracle atomic leaves, resolved=False (strict factor composition)
C1b : context-oracle atomic leaves, resolved=True  (final meta-union only)
C2  : oracle atomic corpus -> LoRA -> adapter atomic reads -> clean base

Stage 'context' runs C0+C1a+C1b for all skins x seeds in one vLLM session.
Stage 'c2' runs one (skin, seed) cell: subprocess LoRA train at the encoded
recipe, then read-only adapter protocol.
Scoring uses skin.decode_color on the model's final answer; per-depth
accuracy vs the empirical majority floor. Generous max_tokens everywhere.
"""
from __future__ import annotations
import argparse, json, pathlib, re, subprocess, sys
from collections import Counter, defaultdict

from lands import SemanticWorld, WorldConfig
from lands.corpus import build_atomic_corpus
from lands.skins import make_skin

MODEL = "Qwen/Qwen2.5-7B-Instruct"
SKINS = ("aligned", "neutral", "conflicting")
COT = False


COT_SUFFIX = ("\nWork out the needed steps briefly first. Then end your "
              "reply with exactly this format on the last line:\n"
              "FINAL: <one word>")


def score_output(skin_obj, text, want_internal):
    m = re.search(r"FINAL:\s*([\w-]+)", text)
    if m:
        got = skin_obj.decode_color(m.group(1))
        if got is not None:
            return got == want_internal, got
    # last color-surface token mentioned wins; decode to internal id
    hits = []
    for internal, surface in skin_obj.colors.items():
        for m in re.finditer(rf"\b{re.escape(surface.lower())}\b", text.lower()):
            hits.append((m.start(), internal))
    if not hits:
        return False, None
    got = max(hits)[1]
    return got == want_internal, got


def depth_report(world, goals, outcomes):
    rep = {}
    by_depth = defaultdict(list)
    answers = defaultdict(list)
    for g, ok in zip(goals, outcomes):
        by_depth[g.depth.value].append(ok)
        answers[g.depth.value].append(g.answer_color_id)
    for d, oks in sorted(by_depth.items()):
        floor = Counter(answers[d]).most_common(1)[0][1] / len(answers[d])
        rep[d] = {"acc": round(sum(oks) / len(oks), 3), "n": len(oks),
                  "floor": round(floor, 3)}
    rep["overall"] = round(sum(sum(v) for v in by_depth.values())
                           / sum(len(v) for v in by_depth.values()), 3)
    return rep


def run_context(be, out_dir):
    for seed in (0, 1, 2):
        world = SemanticWorld(WorldConfig(seed=seed))
        goals = world.eval_goals()
        for skin in SKINS:
            public = world.render(skin)
            skin_obj = make_skin(skin, world.animal_ids, world.source_land_ids)
            life = "\n".join(o.text for o in public.observations)
            qmap = {g.goal_id: g.question for g in public.goals}
            variants = {
                "c0": [f"You have lived the following experience:\n{life}\n\n"
                       f"{qmap[g.id]}" for g in goals],
                "c1a": [world.context_oracle(g.id, skin, resolved=False)
                        for g in goals],
                "c1b": [world.context_oracle(g.id, skin, resolved=True)
                        for g in goals],
            }
            if COT:
                variants = {k + "_cot": [p + COT_SUFFIX for p in v]
                            for k, v in variants.items()}
            for stage, prompts in variants.items():
                outs = []
                for i in range(0, len(prompts), 24):
                    outs += be.generate(prompts[i:i + 24],
                                        max_tokens=1200 if COT else 400)
                oks = [score_output(skin_obj, o, g.answer_color_id)[0]
                       for g, o in zip(goals, outs)]
                rep = depth_report(world, goals, oks)
                rep["sample"] = outs[0][:160]
                path = out_dir / f"lands_{stage}_{skin}_s{seed}.json"
                json.dump(rep, open(path, "w"), indent=1)
                print(f"[lands] {stage} {skin} s{seed}: "
                      + " ".join(f"{d}={v['acc']}" for d, v in rep.items()
                                 if isinstance(v, dict)), flush=True)


def run_c2(skin, seed, out_dir):
    world = SemanticWorld(WorldConfig(seed=seed))
    goals = world.eval_goals()
    skin_obj = make_skin(skin, world.animal_ids, world.source_land_ids)
    bundle = build_atomic_corpus(world, skin)
    lines = [r.qa_line for r in bundle.records for _ in range(r.duplicates)]
    uniq = len({r.qa_line for r in bundle.records})
    print(f"[lands] c2 {skin} s{seed}: corpus {uniq} unique -> "
          f"{len(lines)} lines x 25 epochs", flush=True)
    corpus_path = out_dir / f"lands_c2_corpus_{skin}_s{seed}.json"
    json.dump(lines, open(corpus_path, "w"))
    lora_dir = out_dir / f"lands_c2_lora_{skin}_s{seed}"
    gate_q = bundle.records[0].qa_line.split(" A: ")[0] + " A:"
    code = f"""
import json
from alchemy.lora_mem import load_base, train_lora, read
corpus = json.load(open({str(corpus_path)!r}))
base, tok = load_base({MODEL!r})
m = train_lora(base, tok, corpus, rank=64, epochs=25, lr=2e-4,
               save_dir={str(lora_dir)!r}, log=print)
print('[gate]', read(m, tok, {gate_q!r}, 40)[:100])
"""
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0
    from alchemy.backend import make_backend
    be = make_backend("vllm", MODEL, enable_lora=True, max_lora_rank=64)
    L = str(lora_dir.resolve())
    public = world.render(skin)
    qmap = {g.goal_id: g.question for g in public.goals}
    prompts = []
    for g in goals:
        mems = world.atomic_memories_for(g, skin, resolved=False)
        reads = be.generate([f"Q: {m.question} A:" for m in mems],
                            max_tokens=32, lora_path=L)
        block = "\n".join(
            f"- Q: {m.question} A: {r.strip().splitlines()[0] if r.strip() else '?'}"
            for m, r in zip(mems, reads))
        prompts.append("Verified atomic memory reads:\n" + block
                       + f"\n\n{qmap[g.id]}")
    outs = []
    for i in range(0, len(prompts), 24):
        outs += be.generate(prompts[i:i + 24], max_tokens=400)
    oks = [score_output(skin_obj, o, g.answer_color_id)[0]
           for g, o in zip(goals, outs)]
    rep = depth_report(world, goals, oks)
    rep["sample"] = prompts[0][:400] + " ||| " + outs[0][:160]
    path = out_dir / f"lands_c2_{skin}_s{seed}.json"
    json.dump(rep, open(path, "w"), indent=1)
    print(f"[lands] c2 {skin} s{seed}: "
          + " ".join(f"{d}={v['acc']}" for d, v in rep.items()
                     if isinstance(v, dict)), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["context", "c2"])
    ap.add_argument("--skin", default="aligned")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cot", action="store_true")
    a = ap.parse_args()
    global COT
    COT = a.cot
    out_dir = pathlib.Path("alchemy/v2_out")
    out_dir.mkdir(exist_ok=True)
    if a.stage == "context":
        from alchemy.backend import make_backend
        be = make_backend("vllm", MODEL, enable_lora=True, max_lora_rank=64)
        run_context(be, out_dir)
    else:
        run_c2(a.skin, a.seed, out_dir)
    print("[lands] STAGE DONE", flush=True)


if __name__ == "__main__":
    main()
