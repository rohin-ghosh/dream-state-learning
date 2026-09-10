"""Bootstrap ("pretrain the adapter") corpus — Stage 1 of Rohin's pipeline
(2026-09-10): amortize the THINKING STRUCTURE and some metacognition into the
adapter before the child exists, so parenting is the final step rather than
teaching from scratch.

Source = LIVED episodes only (ledgers of chosen lives), re-rendered by a strong
author model into the state structure Rohin defined:
    PLAN   (first NOTE: what I know, what I will test, prediction with a named
            feature, a reason and a range)
    EXECUTE (the episode's REAL PREDICT/ACT lines and outcomes — never
            invented; renderings that add or change actions are dropped)
    REVIEW (NOTE: where I went wrong, what I did well, what generalizes, what
            I do next time)
Three cue paths per episode (multi-path dreaming): (1) the full state-shaped
episode; (2) a next-episode OPENING that recalls the review and plans; (3) a
CONTRAST note against a named earlier program from the same life.
Rows are {"q": the child's real stored context render, "a": rendering} so the
adapter learns the structure in the dialect it will actually think in.
The corpus is measured for ritual (parent_brief.ritual_metrics) BEFORE anyone
trains on it; the write amplifies whatever structure it is given.

Pre-child: this is not parenting, so the leak scan does not apply. Controls
(none / bootstrap / parent / both) are the protocol's job.

Usage:
  python -m organism_v6.bootstrap_corpus --ledgers ~/v6_out/R2_B_seed3 \
      --out ~/v6_out/bootstrap_v1 --parent-url http://127.0.0.1:8012/v1 \
      --parent-model Qwen/Qwen2.5-32B-Instruct-AWQ --max-episodes 300
"""
from __future__ import annotations
import argparse
import collections
import json
import os
import random
import re
import statistics
from concurrent.futures import ThreadPoolExecutor

from .parent_backend import ServerParent
from .parent_brief import episode_instances, ritual_metrics
from .sleep_compile import canonicalize_dialect

_ACT = re.compile(r"^ACT:\s*(.+)$", re.M)

AUTHOR_BOOT = (
    "You are rewriting ONE episode of an agent's own thinking into a clearer "
    "thinking STRUCTURE, in the agent's own voice and dialect. The agent thinks "
    "in a stream with markers on their own lines: PREDICT: <number>, ACT: <...>, "
    "NOTE: <text>, RECALL: <query>. Keep every ACT line and every outcome "
    "EXACTLY as in the original — never add, remove or change an action or a "
    "result. You may rewrite the thinking around them.\n"
    "Structure to produce:\n"
    "1. PLAN — one NOTE at the start: what I know about this program (a named "
    "feature), what I will test, and a PREDICT with a reason and a range.\n"
    "2. EXECUTE — the original PREDICT/ACT lines and outcomes, with short "
    "thinking between them that names what each outcome confirmed or surprised.\n"
    "3. REVIEW — one NOTE at the end: where I went wrong, what I did well, what "
    "generalizes beyond this program (with scope), what I will do next time.\n"
    "Write in first person, concretely, no headings, no markdown, no bullet "
    "characters; markers on their own lines.")

_FULL = ("{boot}\n\n=== ORIGINAL EPISODE (program {eid}) ===\n{episode}\n=== END ===\n"
         "Rewrite it in the PLAN / EXECUTE / REVIEW structure now.")
_OPENING = ("{boot}\n\n=== ORIGINAL EPISODE (program {eid}) ===\n{episode}\n=== END ===\n"
            "Write only the OPENING of the agent's NEXT episode on a new program: "
            "a RECALL line asking for what it learned on programs like {eid}, then "
            "one NOTE that restates the review of this episode in its own words and "
            "plans what to try first and why, then one PREDICT with reason and range. "
            "No ACT line.")
_REVIEW = ("{boot}\n\n=== ORIGINAL EPISODE (program {eid}) ===\n{episode}\n=== END ===\n"
           "Write only the REVIEW the agent should write at the end of this episode, "
           "as one NOTE of 6-10 lines in first person: where I went wrong, what I did "
           "well, what generalizes (with scope: when it applies, when not), what I do "
           "next time. Judge the thinking, not only the outcome. No ACT line.")
# META-FLOW (Rohin 2026-09-10): the conscious stream over the child's real
# context — the agent asking and answering its own questions about how to
# think here, so those flows exist before parenting.
_METAFLOW = ("{boot}\n\n=== THE AGENT'S CONTEXT AT THE START OF A NEW PROGRAM ({eid}) ===\n"
             "{context}\n=== END ===\n"
             "Write the agent's THINKING FLOW for the first minutes on this program, "
             "before any action, in first person, 10-16 lines, markers on their own "
             "lines where used: it asks itself and answers, concretely for THIS "
             "context — what do I already know here (RECALL: a specific query)? how "
             "much more do I need to think before acting, and why? what would I plan "
             "if I stopped now? what do I execute first and what would each outcome "
             "tell me (PREDICT with reason and range)? what am I unsure of? when will "
             "I stop and review, and what will I judge? End with one NOTE stating the "
             "plan and the stopping rule. No ACT line.")
_CONTRAST = ("{boot}\n\n=== ORIGINAL EPISODE (program {eid}) ===\n{episode}\n=== END ===\n"
             "=== AN EARLIER EPISODE (program {eid2}) ===\n{episode2}\n=== END ===\n"
             "Write one NOTE (5-8 lines) contrasting the two programs: what differed, "
             "what the same actions did differently and why, when the lesson from the "
             "earlier program applies and when it does not. No ACT line.")


def episodes_from_ledger(life_dir: str):
    rows = [json.loads(l) for l in open(os.path.join(life_dir, "ledger.jsonl"))
            if l.strip()]
    th = [r for r in rows if r.get("kind") == "thought" and r.get("note")]
    inst = episode_instances(th)
    # keep the first stored prompt render and win flag per instance
    first_prompt, win, seen = {}, {}, collections.Counter()
    last_tick = {}
    for r in th:
        e = r.get("episode_id")
        try:
            t = int(r.get("tick", 0))
        except (TypeError, ValueError):
            t = 0
        if e not in last_tick or t <= last_tick[e]:
            seen[e] += 1
        last_tick[e] = t
        k = (e, seen[e])
        first_prompt.setdefault(k, r.get("prompt"))
        if r.get("win"):
            win[k] = True
    out = []
    for k, notes in inst.items():
        if not first_prompt.get(k):
            continue
        out.append(dict(key=k, eid=k[0], prompt=first_prompt[k],
                        text="\n".join(notes), win=bool(win.get(k)),
                        acts=set(a.strip() for a in _ACT.findall("\n".join(notes)))))
    return out


def acts_ok(rendering: str, original_acts: set) -> bool:
    ra = set(a.strip() for a in _ACT.findall(rendering))
    return ra <= original_acts and (not original_acts or bool(ra))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledgers", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--parent-url", required=True)
    ap.add_argument("--parent-model", required=True)
    ap.add_argument("--max-episodes", type=int, default=300)
    ap.add_argument("--wins-only", action="store_true", default=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mix", default="metaflow:0.4,review:0.15,opening:0.2,"
                                     "contrast:0.15,full:0.1",
                    help="v2 composition (Rohin: structure-heavy, lived-light). "
                         "Per episode, each path is rendered with this "
                         "probability; 'v1' = full,opening,contrast for every "
                         "episode (lived-heavy control corpus).")
    args = ap.parse_args()
    if args.mix == "v1":
        mix = dict(full=1.0, opening=1.0, contrast=1.0, review=0.0, metaflow=0.0)
    else:
        mix = {k: float(v) for k, v in (x.split(":") for x in args.mix.split(","))}
    random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    eps = []
    for L in args.ledgers:
        e = episodes_from_ledger(os.path.expanduser(L))
        for x in e:
            x["life"] = os.path.basename(os.path.expanduser(L))
        eps += e
    if args.wins_only:
        eps = [e for e in eps if e["win"]] or eps
    random.shuffle(eps)
    eps = eps[:args.max_episodes]
    print(f"[bootstrap] episodes selected: {len(eps)} from {len(args.ledgers)} lives",
          flush=True)

    author = ServerParent(base_url=args.parent_url, model=args.parent_model)

    def render(e):
        rows, drops = [], []
        ep_txt = e["text"][-3500:]
        rng = random.Random(hash((e["eid"], e["key"][1], args.seed)) & 0xffffffff)

        def keep(path, text, need_acts=None):
            text = canonicalize_dialect(text.strip())
            ok = acts_ok(text, e["acts"]) if need_acts else not _ACT.search(text)
            if ok and text:
                rows.append(dict(q=e["prompt"], a=text, path=path,
                                 src=e["life"], eid=e["eid"]))
            else:
                drops.append(f"{path}_acts")
        try:
            if rng.random() < mix.get("metaflow", 0):
                keep("metaflow", author._chat(_METAFLOW.format(
                    boot=AUTHOR_BOOT, eid=e["eid"], context=e["prompt"][-3000:]),
                    max_tokens=450, temperature=0.6))
            if rng.random() < mix.get("review", 0):
                keep("review", author._chat(_REVIEW.format(
                    boot=AUTHOR_BOOT, eid=e["eid"], episode=ep_txt),
                    max_tokens=320, temperature=0.5))
            if rng.random() < mix.get("opening", 0):
                keep("opening", author._chat(_OPENING.format(
                    boot=AUTHOR_BOOT, eid=e["eid"], episode=ep_txt),
                    max_tokens=300, temperature=0.5))
            if rng.random() < mix.get("contrast", 0):
                other = rng.choice([o for o in eps if o["eid"] != e["eid"]] or [e])
                keep("contrast", author._chat(_CONTRAST.format(
                    boot=AUTHOR_BOOT, eid=e["eid"], episode=ep_txt,
                    eid2=other["eid"], episode2=other["text"][-2000:]),
                    max_tokens=300, temperature=0.5))
            if rng.random() < mix.get("full", 0):
                keep("full", author._chat(_FULL.format(
                    boot=AUTHOR_BOOT, eid=e["eid"], episode=ep_txt),
                    max_tokens=700, temperature=0.5), need_acts=True)
        except Exception as ex:                       # server hiccup: skip
            drops.append(f"error:{type(ex).__name__}")
        return rows, drops

    corpus, drops = [], collections.Counter()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, (rows, d) in enumerate(ex.map(render, eps)):
            corpus += rows
            drops.update(d)
            if (i + 1) % 25 == 0:
                print(f"[bootstrap] {i + 1}/{len(eps)} episodes, rows={len(corpus)}",
                      flush=True)

    # ritual on the corpus itself (each rendering = one pseudo-episode)
    pseudo = [dict(kind="thought", episode_id=f"b{i}", tick=0, note=r["a"])
              for i, r in enumerate(corpus)]
    rit = ritual_metrics(pseudo, last_episodes=len(pseudo) or 1)
    paths = collections.Counter(r["path"] for r in corpus)
    meta = dict(n_episodes=len(eps), n_rows=len(corpus), paths=dict(paths),
                drops=dict(drops), ritual=rit, author=args.parent_model,
                sources=args.ledgers, seed=args.seed,
                mean_chars=int(statistics.mean(len(r["a"]) for r in corpus))
                if corpus else 0)
    with open(os.path.join(args.out, "corpus.json"), "w") as f:
        json.dump(dict(corpus=[dict(q=r["q"], a=r["a"]) for r in corpus],
                       recipe="bootstrap_v1_state_structure"), f)
    with open(os.path.join(args.out, "corpus_meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    with open(os.path.join(args.out, "corpus_rows.jsonl"), "w") as f:
        for r in corpus:
            f.write(json.dumps(r) + "\n")
    print(f"[bootstrap] DONE rows={len(corpus)} paths={dict(paths)} drops={dict(drops)} "
          f"ritual={rit.get('ritual')} flags={rit.get('flags')}", flush=True)


if __name__ == "__main__":
    main()
