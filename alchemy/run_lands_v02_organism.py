"""THE ORGANISM: full lifetime loop on Semantic World v0.2 (2026-08-27).

episodes -> recurrent dreams (32B, citation interface, N cycles)
-> final self-consolidation pass -> memory corpus
-> [arm text]  memory as text -> SEQUENTIAL thinker (context erased of
               lifetime; only memory answers visible)
-> [arm lora]  memory -> 7B LoRA -> sequential thinker reads adapter
               (PRINCIPAL PAPER ARM)
-> [arm raw]   episodic-only corpus -> LoRA -> same thinker
-> [arm shuf]  dreamed corpus with shuffled entity bindings -> LoRA ->
               same thinker (structure-destruction control)

Success belongs to the whole trajectory: the dreamer may leave partial
connections; the thinker completes the chain. Every transfer logged.
Big dreamer (32B) writes; small executor (7B) stores/reads/thinks —
adapters are base-specific, so the think stage runs on the 7B base.

Phases are resumable via artifacts:
  --phase dream   (32B, vLLM)  -> organism_nodes_*.json
  --phase corpus  (CPU)        -> organism_corpus_*.json (all arms)
  --phase train   (7B, HF)     -> organism_lora_<arm>_*
  --phase think   (7B, HF)     -> organism_think_<arm>_*.json
"""
from __future__ import annotations
import argparse, json, pathlib, random, re
from collections import defaultdict

from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02, TARGET_LAND_IDS

DREAMER = "Qwen/Qwen2.5-32B-Instruct"
EXECUTOR = "Qwen/Qwen2.5-7B-Instruct"

CYCLE = """You are dreaming — reflecting over a slice of your memories
with no immediate task. Across many dreams you are building a compact,
correct picture of how this world works: which entities behave alike,
what each place does, and how some places' outcomes are built from other
places' outcomes. Derive and check a thought against the memories shown
before writing it. If your thought EXTENDS one of your earlier dream
notes, cite that note's id in CITES (that is how your memory deepens).

FOCUS SLICE (episodic memories):
{slice}

YOUR EARLIER DREAM NOTES (provisional; may be wrong):
{notes}

OPEN QUESTIONS YOU LEFT YOURSELF:
{agenda}

Emit exactly ONE of:
NEW CONNECTION: <one precise sentence> | CITES: <obs/node ids>
REVISED: <node id> -> <corrected sentence> | CITES: <ids>
OPEN QUESTION: <one question for a later dream>
NOTHING USEFUL"""

CONSOLIDATE = """You are in final sleep, consolidating a lifetime of
dream notes into durable memory. Below are your accumulated notes (some
wrong, some partial) and a small sample of raw experience for grounding.

NOTES:
{notes}

SAMPLE EXPERIENCE:
{sample}

Rewrite your knowledge as SHORT declarative memory statements, one per
line, each self-contained (name the entities explicitly; no pronouns,
no references to note ids). Keep only what you actually support; merge
duplicates; drop speculation you could not check. Also keep useful
partial knowledge ("X is built from a combination that includes Y")."""

THINK_SYS = """You are answering from long-term memory. Your memory
will usually NOT contain the final answer directly — it contains pieces.
Decompose: ask about the PIECES you need (which places contribute to the
place in the question; what this animal's outcomes were in those other
places; how outcomes combine in this world), one short question at a
time, and build the answer yourself from the returned pieces. Never ask
the goal question itself. If a memory answer looks like a direct final
answer, treat it as unreliable unless pieces support it.

You may take up to {budget} operations, then you MUST answer with your
best construction (a color word, possibly hyphenated). Each turn output
exactly ONE of:
MEMORY: <one short question to your memory>
THINK: <a connection, hypothesis, or intermediate conclusion to keep>
ANSWER: <color word>
Use THINK to build structure: compare retrieved pieces, propose which
places might combine, derive what that would predict, note revisions.
Your working state so far:
{state}

Question: {q}"""


def load_world(a):
    world = SemanticWorldV02(WorldConfig(seed=a.seed))
    skin_obj = make_skin(a.skin, world.animal_ids, world.source_land_ids)
    rows = list(world.render_lifetime(a.skin))
    goals = world.render_goals(a.skin)
    return world, skin_obj, rows, goals


def tag(a):
    return f"{a.skin}_s{a.seed}"


def phase_dream(a):
    from alchemy.backend import make_backend
    world, skin_obj, rows, goals = load_world(a)
    src_names = [skin_obj.land(l) for l in world.source_land_ids]
    tgt_surfaces = []
    for g in goals:
        m = re.match(r"In ([^,]+),", g["question"])
        if m and m.group(1) not in tgt_surfaces:
            tgt_surfaces.append(m.group(1))
    be = make_backend("vllm", DREAMER, enable_lora=True, max_lora_rank=64)
    nodes, agenda = [], []
    for cyc in range(a.cycles):
        focus = (tgt_surfaces + src_names)[cyc % (len(tgt_surfaces)
                                                  + len(src_names))]
        sl = [r for r in rows if focus.lower() in r.lower()]
        ents = {n for r in sl for n in
                [skin_obj.animal(x) for x in world.animal_ids] if n in r}
        sl += [r for r in rows if any(e in r for e in ents)
               and r not in sl][:40]
        ftok = set(re.findall(r"\w+", focus.lower()))
        rel = sorted(nodes, key=lambda n: -len(
            ftok & set(re.findall(r"\w+", n["text"].lower()))))[:12]
        notes = "\n".join(f"[{n['id']}] {n['text']}" for n in rel) or "(none)"
        out = be.generate([CYCLE.format(slice="\n".join(sl[:55]), notes=notes,
                                        agenda="\n".join(agenda[-6:]) or "(none)")],
                          max_tokens=900)[0]
        m = re.search(r"(NEW CONNECTION|REVISED|OPEN QUESTION|NOTHING USEFUL)"
                      r"[:]?(.*)", out)
        if m:
            kind, body = m.group(1), m.group(2)
            cites = re.findall(r"obs_\d+|node_\d+", out[m.start():])
            if kind == "NEW CONNECTION":
                txt = body.split("| CITES:")[0].strip()
                if txt and not any(n["text"] == txt for n in nodes):
                    depth = 1 + max([n["depth"] for n in nodes
                                     if n["id"] in cites] + [0])
                    nodes.append({"id": f"node_{len(nodes)}", "text": txt,
                                  "cites": cites, "depth": depth,
                                  "cycle": cyc})
            elif kind == "REVISED":
                t = next((n for n in nodes if n["id"] in cites), None)
                if t and "->" in body:
                    t["text"] = body.split("->", 1)[1].split("| CITES:")[0].strip()
            elif kind == "OPEN QUESTION":
                agenda.append(body.strip()[:200])
        if (cyc + 1) % 8 == 0:
            print(f"[organism:dream] cyc {cyc+1}: {len(nodes)} nodes, "
                  f"maxdepth {max([n['depth'] for n in nodes]+[0])}, "
                  f"agenda {len(agenda)}", flush=True)
    # final consolidation with the big dreamer
    sample = "\n".join(random.Random(0).sample(rows, min(30, len(rows))))
    out = be.generate([CONSOLIDATE.format(
        notes="\n".join(f"[{n['id']}] {n['text']}" for n in nodes),
        sample=sample)], max_tokens=2500)[0]
    statements = [l.strip("-* ").strip() for l in out.splitlines()
                  if len(l.strip()) > 20 and not l.strip().startswith(("NOTES", "SAMPLE"))]
    json.dump({"nodes": nodes, "agenda": agenda, "statements": statements},
              open(f"alchemy/v2_out/organism_nodes_{tag(a)}.json", "w"),
              indent=1)
    print(f"[organism:dream] DONE nodes={len(nodes)} statements={len(statements)}",
          flush=True)


def phase_corpus(a):
    world, skin_obj, rows, goals = load_world(a)
    d = json.load(open(f"alchemy/v2_out/organism_nodes_{tag(a)}.json"))
    statements = d["statements"]
    episodic = [r.split("] ", 1)[1] if "] " in r else r for r in rows]
    animals = [skin_obj.animal(x) for x in world.animal_ids]
    lands = [skin_obj.land(l) for l in world.source_land_ids]

    def qa_forms(stmts):
        out = []
        for s in stmts:
            ents = [e for e in animals + lands if e in s][:2]
            key = " and ".join(ents) if ents else "this world"
            out.append(f"Q: What did you conclude about {key}? A: {s}")
            out.append(s)
        return out

    corpus = {"lora": qa_forms(statements) + episodic,
              "raw": episodic,
              "text": statements}
    # shuffled control: permute animal names inside dreamed statements
    rng = random.Random(7)
    perm = animals[:]
    rng.shuffle(perm)
    swap = dict(zip(animals, perm))
    pat = re.compile("|".join(re.escape(x) for x in animals))
    shuf = [pat.sub(lambda m: swap[m.group(0)], s) for s in statements]
    corpus["shuf"] = qa_forms(shuf) + episodic
    json.dump(corpus, open(f"alchemy/v2_out/organism_corpus_{tag(a)}.json",
                           "w"), indent=1)
    print(f"[organism:corpus] lora={len(corpus['lora'])} raw={len(corpus['raw'])} "
          f"shuf={len(corpus['shuf'])} text={len(corpus['text'])}", flush=True)


def phase_train(a):
    import subprocess, sys
    corpus = json.load(open(f"alchemy/v2_out/organism_corpus_{tag(a)}.json"))
    for arm in a.arms.split(","):
        if arm == "text":
            continue
        lines = corpus[arm] * 8
        p = f"alchemy/v2_out/organism_train_{arm}_{tag(a)}.json"
        json.dump(lines, open(p, "w"))
        lora_dir = f"alchemy/v2_out/organism_lora_{arm}_{tag(a)}"
        code = f"""
import json
from alchemy.lora_mem import load_base, train_lora, read
corpus = json.load(open({p!r}))
base, tok = load_base({EXECUTOR!r})
m = train_lora(base, tok, corpus, rank=64, epochs=25, lr=2e-4,
               save_dir={lora_dir!r}, log=print)
print('[gate]', read(m, tok, corpus[0][:60], 30)[:80])
"""
        rc = subprocess.run([sys.executable, "-c", code]).returncode
        print(f"[organism:train] arm {arm} rc={rc}", flush=True)


def phase_think(a):
    import torch
    from peft import PeftModel
    from alchemy.lora_mem import load_base
    world, skin_obj, rows, goals_pub = load_world(a)
    answered = world.render_goals(a.skin, include_answers=True)
    answers = {g["goal_id"]: g["answer"].lower() for g in answered}
    depths = {g["goal_id"]: "D3blend" for g in goals_pub}
    if a.goalset == "ladder":
        base_pub = world.base.render(a.skin, include_answers=True).goals
        base_goals = world.base.eval_goals()
        picks = []
        for d in ("D0", "D1", "D2"):
            picks += [bg for bg in base_goals if bg.depth.value == d][:6]
        base_q = {g.goal_id: g for g in base_pub}
        for bg in picks:
            rg = base_q[bg.id]
            goals_pub = goals_pub + ({"goal_id": bg.id,
                                      "question": rg.question},)
            answers[bg.id] = rg.answer.lower()
            depths[bg.id] = bg.depth.value
    corpus = json.load(open(f"alchemy/v2_out/organism_corpus_{tag(a)}.json"))
    qmap = {g["goal_id"]: g["question"] for g in goals_pub}
    base, tok = load_base(a.executor)
    for arm in a.arms.split(","):
        if arm.endswith("text"):
            model = base
            mem_block = "\n".join(corpus[arm])
        else:
            model = PeftModel.from_pretrained(
                base, f"alchemy/v2_out/organism_lora_{arm}_{tag(a)}")
            model.eval()
            mem_block = None

        def gen(prompt, n=200, adapter=False):
            with torch.no_grad():
                ids = tok(prompt, return_tensors="pt").input_ids.to(base.device)
                mdl = model
                if not arm.endswith("text") and not adapter:
                    ctx = model.disable_adapter()
                    ctx.__enter__()
                    out = model.generate(ids, max_new_tokens=n,
                                         do_sample=False,
                                         pad_token_id=tok.eos_token_id)
                    ctx.__exit__(None, None, None)
                else:
                    out = mdl.generate(ids, max_new_tokens=n, do_sample=False,
                                       pad_token_id=tok.eos_token_id)
                return tok.decode(out[0, ids.shape[1]:],
                                  skip_special_tokens=True)

        def memory_answer(q):
            if arm.endswith("text"):
                # VERBATIM lexical retrieval — memory never generates.
                lines = corpus[arm]
                qt = set(re.findall(r"\w+", q.lower())) - {
                    "what", "is", "the", "in", "of", "a", "an", "which",
                    "color", "does", "do", "are", "there", "to", "and"}
                scored = sorted(lines, key=lambda l: -len(
                    qt & set(re.findall(r"\w+", l.lower()))))
                hits = [l for l in scored[:3] if
                        len(qt & set(re.findall(r"\w+", l.lower()))) >= 2]
                return (" | ".join(hits) if hits
                        else "(no matching memory)")
            return gen(f"Q: What did you conclude about {q}? A:"
                       if not q.endswith("?") else f"Q: {q} A:",
                       60, adapter=True).strip().split("\n")[0]

        results, traces = [], []
        for gp in goals_pub:
            state, trace = [], []
            final = None
            for step in range(a.budget):
                last = step == a.budget - 1
                prompt = THINK_SYS.format(budget=a.budget,
                                          state="\n".join(state) or "(empty)",
                                          q=qmap[gp["goal_id"]])
                if last:
                    prompt += "\nBudget exhausted: you MUST output ANSWER now."
                out = gen(prompt, 150)
                m = re.search(r"(MEMORY|THINK|ANSWER|DEFER)[:]?(.*)", out)
                if not m:
                    break
                op = m.group(1)
                body = m.group(2).strip().splitlines()[0] if m.group(2).strip() else ""
                body = re.split(r"\b(?:MEMORY|THINK|ANSWER|DEFER)\s*:", body)[0].strip(" ->")
                if op == "MEMORY" and not last:
                    if any(t[0] == "MEMORY" and t[1] == body for t in trace):
                        state.append(f"(you already asked: {body} — do not "
                                     "repeat; use what you have or ask "
                                     "something NEW)")
                        trace.append(("REPEAT", body, ""))
                        continue
                    ans = memory_answer(body)
                    state.append(f"asked: {body} -> {ans[:140]}")
                    trace.append(("MEMORY", body, ans[:140]))
                elif op == "THINK" and not last:
                    state.append(f"thought: {body[:160]}")
                    trace.append(("THINK", body[:160], ""))
                elif op == "ANSWER":
                    final = body
                    trace.append(("ANSWER", body, ""))
                    break
                elif last:
                    m2 = re.search(r"([a-z]+(?:-[a-z]+)?)", body.lower())
                    final = m2.group(1) if m2 else body
                    trace.append(("FORCED", body, ""))
                    break
                else:
                    trace.append(("DEFER", "", ""))
                    break
            want = answers[gp["goal_id"]]
            got = (final or "").lower().strip().rstrip(".")
            ok = want == got or want in got.split()
            results.append(bool(ok))
            traces.append({"goal": gp["goal_id"],
                           "depth": depths.get(gp["goal_id"], "?"),
                           "trace": trace, "final": final, "ok": bool(ok)})
        rep = {"acc": round(sum(results) / len(results), 3),
               "n": len(results)}
        byd = {}
        for tr in traces:
            byd.setdefault(tr["depth"], []).append(tr["ok"])
        rep["by_depth"] = {d: f"{sum(v)}/{len(v)}" for d, v in sorted(byd.items())}
        json.dump({"rep": rep, "traces": traces},
                  open(f"alchemy/v2_out/organism_think_{arm}_{tag(a)}.json",
                       "w"), indent=1)
        acc = round(sum(results) / len(results), 3)
        print(f"[organism:think] arm {arm}: acc {acc} "
              f"({sum(results)}/{len(results)})", flush=True)
        if not arm.endswith("text"):
            del model
            torch.cuda.empty_cache()
    print("[organism:think] DONE", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True,
                    choices=["dream", "corpus", "train", "think"])
    ap.add_argument("--skin", default="aligned")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cycles", type=int, default=48)
    ap.add_argument("--budget", type=int, default=12)
    ap.add_argument("--arms", default="text,lora,raw,shuf")
    ap.add_argument("--goalset", default="blend", choices=["blend", "ladder"])
    ap.add_argument("--executor", default=EXECUTOR)
    a = ap.parse_args()
    {"dream": phase_dream, "corpus": phase_corpus,
     "train": phase_train, "think": phase_think}[a.phase](a)


if __name__ == "__main__":
    main()
