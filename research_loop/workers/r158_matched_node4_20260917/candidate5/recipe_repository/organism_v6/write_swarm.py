"""Write-mechanism swarm (sleep-first priority, Rohin 2026-09-07):
factorial over write-recipe ingredients on a FIXED corpus, judged by the
same probes + canary. Ingredients this wave:
  paraphrase: each exemplar answer restated 2 ways by THINK-calls
              ("knowledge is extractable only when seen in multiple forms")
  replaymix:  fixed canonical-dialect anchor exemplars mixed in
              (base-distribution data against drift — format anchoring)
Arms: none | para | mix | para+mix   (rank 8, v2.1 trainer, same dose)

  CUDA_VISIBLE_DEVICES=6 python -m organism_v6.write_swarm \
      --corpus <corpus.json> --out ~/v6_out/write_swarm --arm para \
      --phase build|train|probe
Phases are separate processes (engine teardown law).
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

ANCHORS = [
    {"q": "You act via markers. Show one complete, well-formed working "
          "step for an optimization task: a prediction, an action, and a "
          "note with scope.",
     "a": "PREDICT: 0.35\nACT: TRY 2,4,6\nNOTE: testing whether even "
          "numbers matter [scope: this puzzle only]"},
    {"q": "Show how you finish a task when returns diminish.",
     "a": "NOTE: last three probes added no information — my rule is "
          "supported by 6 cases [scope: this task family]\nDONE"},
    {"q": "Show how you consult your experience before re-deriving.",
     "a": "RECALL: failures combining large spreads\nPREDICT: 0.5\n"
          "ACT: TRY 1,2,3"},
    {"q": "Show a well-formed reaction to a surprising outcome.",
     "a": "PREDICT: 0.8\nACT: QUIZ T,T,F,F,T,F\nNOTE: scored far below my "
          "prediction — my rule must be wrong, not the quiz; re-examining "
          "case 3 [scope: always react in proportion to the miss]"},
]

_PARA_PROMPT = ("Restate the following lesson in a different wording that "
                "keeps ALL facts, numbers, and marker lines intact. Output "
                "only the restatement.\n\n{a}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--arm", choices=["none", "para", "mix", "paramix"],
                    required=True)
    ap.add_argument("--phase", choices=["build", "train", "probe"],
                    required=True)
    ap.add_argument("--rank", type=int, default=8)
    args = ap.parse_args()
    out = os.path.expanduser(args.out)
    arm_dir = os.path.join(out, args.arm)
    os.makedirs(arm_dir, exist_ok=True)

    if args.phase == "build":
        d = json.load(open(os.path.expanduser(args.corpus)))
        corpus = [x if isinstance(x, dict) else
                  {"q": "Recall a lesson from your experience, with scope.",
                   "a": str(x)} for x in d["corpus"]]
        if args.arm in ("para", "paramix"):
            from .model_backend import VLLMBackend
            m = VLLMBackend(adapter_path=None)
            answers = [c["a"][:800] for c in corpus]
            for rep in range(2):
                outs = m.batch([_PARA_PROMPT.format(a=a) for a in answers],
                               max_tokens=300, temperature=0.8,
                               seeds=[rep * 10000 + i
                                      for i in range(len(answers))])
                corpus += [{"q": corpus[i]["q"], "a": o.strip()[:900]}
                           for i, o in enumerate(outs) if o.strip()]
        if args.arm in ("mix", "paramix"):
            n = max(4, len(corpus) // 5)
            corpus += (ANCHORS * ((n // len(ANCHORS)) + 1))[:n]
        with open(os.path.join(arm_dir, "corpus.json"), "w") as f:
            json.dump(dict(corpus=corpus, arm=args.arm), f)
        print(f"BUILD_{args.arm} n={len(corpus)}")
        return

    if args.phase == "train":
        rc = subprocess.run(
            [sys.executable, "-m", "organism_v6.train_adapter_v21",
             "--corpus", os.path.join(arm_dir, "corpus.json"),
             "--out", os.path.join(arm_dir, "adapter"),
             "--rank", str(args.rank), "--epochs", "3", "--lr", "5e-5"],
            cwd=os.path.dirname(HERE)).returncode
        print(f"TRAIN_{args.arm} rc={rc}")
        sys.exit(rc)

    if args.phase == "probe":
        rc = subprocess.run(
            [sys.executable, "-m", "organism_v6.probe_adapter",
             "--out", os.path.join(arm_dir, "probe.json"),
             "--adapter", os.path.join(arm_dir, "adapter"),
             "--reps", "2"],
            cwd=os.path.dirname(HERE)).returncode
        print(f"PROBE_{args.arm} rc={rc}")
        sys.exit(rc)


if __name__ == "__main__":
    main()
