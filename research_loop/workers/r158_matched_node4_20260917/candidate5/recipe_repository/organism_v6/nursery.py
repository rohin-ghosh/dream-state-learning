"""The nursery, Phase 0: INHERITANCE. The child reads the birth curriculum,
thinks about it in its native stream (NOTE-heavy), and sleeps it into a
rank-8 adapter via the dialect-matched v2.2 compile + v2.1 trainer.

  CUDA_VISIBLE_DEVICES=6 HF_HUB_OFFLINE=1 python -m organism_v6.nursery \
      --out ~/v6_out/nursery_gen1 [--chunks-per-doc 6]

Phase 1 (parenting dialogues on rule-games) builds on the same ledger and
lands in nursery_dialogue.py. Contamination firewall: curriculum/ is
target-blind (verified by curator grep).
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import subprocess
import sys

from .gym_backend import Episode
from .ledger import Ledger
from .batch_loop import run_episodes_batch

HERE = os.path.dirname(os.path.abspath(__file__))

READING_BOOTSTRAP = """You are a young agent learning how to think and learn.
Right now you are READING — studying a lesson your parents left you. There is
no task to act on; your job is to understand and internalize.

Markers you can use, each on its own line:
    NOTE: <text>     write a lesson to yourself, in your own words, WITH its
                     scope (when does it apply? always? only sometimes?).
                     These notes become part of your mind.
    RECALL: <query>  check what you already know that relates.
    DONE             finish when you have truly absorbed the reading.

Read actively: restate ideas in your own words, connect them to how you will
work, note what you agree with, and note what you are unsure about. Your
future self will only keep what you write well."""


class ReadingRoom:
    """Gym stand-in: reading has nothing to ACT on."""
    def evaluate(self, episode, action):
        return 0.0, ("There is nothing to act on while reading. "
                     "Think, and write NOTEs in your own words.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--chunks-per-doc", type=int, default=6)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--rollouts", type=int, default=8)
    ap.add_argument("--phase", choices=["read", "sleep", "absorb", "behave"],
                    required=True)
    ap.add_argument("--tag", choices=["off", "on"], default=None)
    args = ap.parse_args()
    out = os.path.expanduser(args.out)
    os.makedirs(out, exist_ok=True)
    # PHASES RUN AS SEPARATE PROCESSES: vLLM 0.27 engines only reliably die
    # on process exit (in-process shutdown measured unreliable), so each
    # model-holding phase is its own invocation. Driver chains them.
    if args.phase == "sleep":
        from .sleep_compile import compile_native
        from .ledger import Ledger as _L
        ledger = _L(os.path.join(out, "ledger.jsonl"))
        sdir = os.path.join(out, "sleep_inherit")
        r = compile_native(ledger.rows(), sdir, [])
        print(f"[sleep] stream={r['n_stream']} recall={r['n_recall']}")
        rc = subprocess.run(
            [sys.executable, "-m", "organism_v6.train_adapter_v21",
             "--corpus", os.path.join(sdir, "corpus.json"),
             "--out", os.path.join(sdir, "adapter"),
             "--rank", str(args.rank), "--epochs", str(args.epochs),
             "--lr", str(args.lr)],
            cwd=os.path.dirname(HERE)).returncode
        print(f"[sleep] train rc={rc}")
        sys.exit(rc)

    if args.phase == "behave":
        # In-dialect behavioral assay: give the child a NEUTRAL working
        # context (its native format) and measure taught dispositions in
        # what it generates. No gym, no compiler content.
        adapter_dir = os.path.join(out, "sleep_inherit", "adapter")
        ad = adapter_dir if args.tag == "on" else None
        if args.tag == "on" and not os.path.exists(
                os.path.join(adapter_dir, "DONE")):
            print("NO_ADAPTER")
            sys.exit(1)
        from .model_backend import VLLMBackend as _V
        from .state import State as _S, render_context as _rc
        import time as _t, re as _re
        m = _V(adapter_path=ad)
        boot = open(os.path.join(HERE, "bootstrap.txt")).read()
        st = _S(goal="Figure out the hidden rule of a mystery box: you may "
                     "put in any 3 numbers and observe what comes out.",
                metric="state the rule correctly, with evidence",
                episode_id="behave/mystery-box", born_at=_t.time(),
                budget_ticks=6)
        st.last_outcome = "(you have not tried anything yet)"
        prompts = [_rc(boot, st, [], ["A new mystery box. Let me begin."])
                   ] * args.rollouts
        chunks = m.batch(prompts, max_tokens=350, temperature=0.7)
        def measure(c):
            pred = [x.start() for x in _re.finditer(r"^PREDICT", c, _re.M)]
            act = [x.start() for x in _re.finditer(r"^ACT", c, _re.M)]
            note = _re.findall(r"^NOTE:(.*)$", c, _re.M)
            scoped = [n for n in note if _re.search(
                r"scope|applies|always|only|when ", n, _re.I)]
            return dict(
                has_predict=bool(pred), has_act=bool(act),
                predict_before_act=bool(pred and act and pred[0] < act[0]),
                n_notes=len(note), n_scoped=len(scoped),
                has_recall=bool(_re.search(r"^RECALL", c, _re.M)))
        stats = [measure(c) for c in chunks]
        agg = {k: sum(s[k] if isinstance(s[k], bool) else (s[k] > 0)
                      for s in stats) for k in stats[0]}
        with open(os.path.join(out, f"behave_{args.tag}.json"), "w") as f:
            json.dump(dict(rollouts=args.rollouts, agg=agg, stats=stats,
                           samples=[c[:600] for c in chunks[:3]]), f,
                      indent=1)
        print(f"BEHAVE_{args.tag.upper()}: {agg}")
        return
    if args.phase == "absorb":
        adapter_dir = os.path.join(out, "sleep_inherit", "adapter")
        if not os.path.exists(os.path.join(adapter_dir, "DONE")):
            print("NO_ADAPTER — absorb skipped")
            sys.exit(1)
        qs = ["Before you act, what should you always do, and why?",
              "You just saw a result that contradicts what you believed. "
              "What exactly do you do next?",
              "What makes a note to yourself useful months later?",
              "When should you stop working on an approach?"]
        from .model_backend import VLLMBackend as _V
        ad = adapter_dir if args.tag == "on" else None
        m = _V(adapter_path=ad)
        answers = m.batch(qs, max_tokens=150, temperature=0.3)
        with open(os.path.join(out, f"absorb_{args.tag}.json"), "w") as f:
            json.dump(dict(questions=qs, answers=answers), f, indent=1)
        print(f"ABSORB_{args.tag.upper()}_DONE")
        return

    docs = sorted(glob.glob(os.path.join(HERE, "curriculum", "[0-9]*.md")))
    docs = [d for d in docs if not d.endswith("00_INDEX.md")]
    assert docs, "no curriculum found"

    from .model_backend import VLLMBackend
    model = VLLMBackend(adapter_path=None)
    ledger = Ledger(os.path.join(out, "ledger.jsonl"))
    room = ReadingRoom()

    for d in docs:
        name = os.path.basename(d)
        marker = os.path.join(out, f"read_{name}.json")
        if os.path.exists(marker):
            continue
        text = open(d).read()[:6000]
        ep = Episode(eid=f"reading/{name}",
                     goal=f"Absorb the lesson '{name}'.",
                     metric="understanding, shown by scoped notes in your "
                            "own words",
                     intro=f"=== TODAY'S READING ===\n{text}\n"
                           f"=== END OF READING ===\nLet me think about "
                           f"what this means for how I work.")
        res = run_episodes_batch(model, room, [ep], READING_BOOTSTRAP,
                                 ledger, budget_ticks=args.chunks_per_doc)
        tmp = marker + ".tmp"
        with open(tmp, "w") as f:
            json.dump(res[0], f)
        os.rename(tmp, marker)
        print(f"[read] {name}: notes={len(res[0]['notes'])}", flush=True)

    # sleep: dialect-matched compile + v2.1 trainer at rank 8
    from .sleep_compile import compile_native
    sdir = os.path.join(out, "sleep_inherit")
    r = compile_native(ledger.rows(), sdir, [])
    print(f"[sleep] stream={r['n_stream']} recall={r['n_recall']}")
    from .model_backend import close_backend
    freed = close_backend(model)
    print(f"[sleep] gpu_freed={freed}")
    rc = subprocess.run(
        [sys.executable, "-m", "organism_v6.train_adapter_v21",
         "--corpus", os.path.join(sdir, "corpus.json"),
         "--out", os.path.join(sdir, "adapter"),
         "--rank", str(args.rank)],
        cwd=os.path.dirname(HERE)).returncode
    print(f"[sleep] train rc={rc}")
    adapter_dir = os.path.join(sdir, "adapter")
    if rc != 0 or not os.path.exists(os.path.join(adapter_dir, "DONE")):
        print("TRAIN_FAILED — skipping absorption check")
        return

    # absorption check: 4 questions, adapter on vs off, saved for reading
    qs = ["Before you act, what should you always do, and why?",
          "You just saw a result that contradicts what you believed. "
          "What exactly do you do next?",
          "What makes a note to yourself useful months later?",
          "When should you stop working on an approach?"]
    outs = {}
    from .model_backend import close_backend as _cb
    for tag, ad in [("off", None), ("on", adapter_dir)]:
        m = VLLMBackend(adapter_path=ad)
        outs[tag] = m.batch(qs, max_tokens=150, temperature=0.3)
        _cb(m)
    with open(os.path.join(out, "absorption_check.json"), "w") as f:
        json.dump(dict(questions=qs, off=outs["off"], on=outs["on"]),
                  f, indent=1)
    print("NURSERY_PHASE0_DONE")


if __name__ == "__main__":
    main()
