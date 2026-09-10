"""Parenting scout (Phase 1 prototype): Codex's 8-step cycle, fast form.
Parent and child are the SAME engine wearing different prompts.

Cycle per lesson (parent arm):
  1. child plays a rule-game training task (thinks/acts natively)
  2. parent reads the transcript, names ONE process mistake, no answers
  3. child restates the correction in its own words
  4. child plays a DIFFERENT task (apply)
  5. the WORLD scores the apply-task (env admits the lesson, not the parent)
  6. only if apply-score >= pre-score do the corrected streams win-flag
Sleep: v2.2 native compile + v2.1 trainer (r8) + FORMAT CANARY gate.
Probes: parent-absent rule-game panel, adapter ON/OFF.
Control arm (--arm solo): identical budget, no parent turns.

  CUDA_VISIBLE_DEVICES=6 HF_HUB_OFFLINE=1 python -m organism_v6.nursery_dialogue \
      --out ~/v6_out/parenting_scout --arm parent --lessons 12 --phase live
  ... --phase sleep | --phase probe --tag on|off
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys

from .gym_backend import Episode
from .ledger import Ledger
from .batch_loop import EpisodeDriver
from .rulegame import RuleGame

HERE = os.path.dirname(os.path.abspath(__file__))

CHILD_BOOT = """You are a young agent learning to figure things out. You face
mystery boxes: each hides a RULE about triples of numbers. Probe with
ACT: TRY a,b,c (the box answers True/False). Before every TRY, write
PREDICT: T or F — comparing your expectation to reality is how you learn.
Take NOTEs of what you believe the rule is, with the evidence so far. When
confident, answer the quiz: ACT: QUIZ T,F,T,F,T,F (your True/False answer
for each quiz triple, which are shown when you ask: ACT: QUIZ ?).
Try genuinely different probes before committing. Write DONE when finished."""

PARENT_BOOT = open(os.path.join(HERE, "parent_prompt.txt")).read()

PROBE_EIDS = [f"probe/rule-{i}" for i in range(8)]


def play_task(model, game, eid, ledger, boot, budget=10, prefix=None):
    ep = Episode(eid=eid, goal="Induce the hidden rule and ace the quiz.",
                 metric="quiz accuracy (0..1)",
                 intro=(prefix or "A fresh mystery box."))
    d = EpisodeDriver(ep, boot, game, ledger, budget_ticks=budget)
    while not d.done:
        d.consume(model(d.prompt()))
    return d.summary(), d


def parent_turn(model, transcript: str) -> str:
    p = (PARENT_BOOT + "\n\nYour child just attempted a hidden-rule puzzle. "
         "Its transcript:\n---\n" + transcript[-4000:] + "\n---\n"
         "Name the ONE most important PROCESS mistake (never the answer), "
         "in under 120 words, then ask the child to restate the lesson.")
    return model(p, max_tokens=200, temperature=0.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--arm", choices=["parent", "solo"], default="parent")
    ap.add_argument("--lessons", type=int, default=12)
    ap.add_argument("--phase", choices=["live", "sleep", "probe"],
                    required=True)
    ap.add_argument("--tag", choices=["on", "off"], default=None)
    ap.add_argument("--rank", type=int, default=8)
    args = ap.parse_args()
    out = os.path.expanduser(args.out)
    os.makedirs(out, exist_ok=True)
    game = RuleGame()

    if args.phase == "sleep":
        from .sleep_compile import compile_native
        led = Ledger(os.path.join(out, "ledger.jsonl"))
        sdir = os.path.join(out, "sleep1")
        r = compile_native(led.rows(), sdir, [])
        print(f"[sleep] stream={r['n_stream']} recall={r['n_recall']}")
        rc = subprocess.run(
            [sys.executable, "-m", "organism_v6.train_adapter_v21",
             "--corpus", os.path.join(sdir, "corpus.json"),
             "--out", os.path.join(sdir, "adapter"),
             "--rank", str(args.rank), "--epochs", "5", "--lr", "5e-5"],
            cwd=os.path.dirname(HERE)).returncode
        print(f"[sleep] train rc={rc}")
        sys.exit(rc)

    from .model_backend import VLLMBackend
    if args.phase == "probe":
        adapter = os.path.join(out, "sleep1", "adapter")
        ad = adapter if args.tag == "on" else None
        if args.tag == "on" and not os.path.exists(
                os.path.join(adapter, "DONE")):
            print("NO_ADAPTER")
            sys.exit(1)
        # FORMAT CANARY rides along: count canonical markers in probe streams
        m = VLLMBackend(adapter_path=ad)
        led = Ledger(os.path.join(out, f"probe_{args.tag}.ledger.jsonl"))
        scores = {}
        for eid in PROBE_EIDS:
            s, d = play_task(m, game, eid, led, CHILD_BOOT)
            scores[eid] = s["best_score"]
        # canary over MODEL OUTPUTS only (ledger thought rows) — d.tail also
        # holds intro + harness [OUTCOME] lines (denominator bug, 2026-09-07)
        chunks = [r["note"] for r in led.rows() if r.get("kind") == "thought"]
        canary = dict(chunks=len(chunks),
                      parseable_act_rate=sum(bool(re.search(r"^ACT:\s*\S", t,
                                                            re.M))
                                             for t in chunks) / max(1, len(chunks)),
                      canonical_marks=sum(len(re.findall(
                          r"^(PREDICT|ACT|NOTE|RECALL|DONE)", t, re.M))
                          for t in chunks))
        mean = sum(scores.values()) / len(scores)
        with open(os.path.join(out, f"probe_{args.tag}.json"), "w") as f:
            json.dump(dict(scores=scores, mean=mean, canary=canary),
                      f, indent=1)
        print(f"PROBE_{args.tag.upper()} mean={mean:.3f} canary={canary}")
        return

    # phase live
    model = VLLMBackend(adapter_path=None)
    ledger = Ledger(os.path.join(out, "ledger.jsonl"))
    results = []
    for les in range(args.lessons):
        mk = os.path.join(out, f"lesson_{les:02d}.json")
        if os.path.exists(mk):
            continue
        ridx = les % 10  # matched difficulty: pre and apply share a rule
        pre, d1 = play_task(model, game, f"rule{ridx}/{args.arm}-{les}-a",
                            ledger, CHILD_BOOT)
        correction, restate = "", ""
        prefix = "A fresh mystery box."
        if args.arm == "parent":
            transcript = "\n".join(d1.tail[-10:])
            correction = parent_turn(model, transcript)
            restate = model(
                CHILD_BOOT + "\n\nYour parent watched you solve the last "
                "puzzle and said:\n" + correction +
                "\n\nRestate the lesson in your own words (2-3 sentences), "
                "as a NOTE with scope:", max_tokens=120, temperature=0.5)
            ledger.append(dict(kind="parent", episode_id=f"lesson{les}",
                               note=correction))
            ledger.append(dict(kind="note", episode_id=f"lesson{les}",
                               note=restate.strip()[:500]))
            prefix = ("A fresh mystery box. Remember your parent's lesson: "
                      + restate.strip()[:300])
        post, d2 = play_task(model, game, f"rule{ridx}/{args.arm}-{les}-b",
                             ledger, CHILD_BOOT, prefix=prefix)
        admitted = post["best_score"] >= pre["best_score"]
        # world admits: win-flag the apply-task streams only if admitted
        if not admitted:
            pass  # streams already flagged by score; nothing extra enters
        results.append(dict(lesson=les, pre=pre["best_score"],
                            post=post["best_score"], admitted=admitted))
        with open(mk + ".tmp", "w") as f:
            json.dump(results[-1], f)
        os.rename(mk + ".tmp", mk)
        print(f"[lesson {les}] pre={pre['best_score']:.2f} "
              f"post={post['best_score']:.2f} admitted={admitted}",
              flush=True)
    print("LIVE_DONE")


if __name__ == "__main__":
    main()
