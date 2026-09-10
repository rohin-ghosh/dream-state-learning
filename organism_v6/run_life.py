"""One life of the v6 organism. Resumable; marker files; idempotent phases.

  python -m organism_v6.run_life --life-dir ~/v6_out/B_seed0 --arm B \
      --seed 0 --episodes 64 --sleep-every 8 --probe-every 16 \
      [--budget-ticks 24] [--smoke]

Arm A: frozen loop (no adapter ever).  Arm B: sleep-compiled LoRA.
Phases per life: wake (8 episodes) -> sleep (compile+train, arm B) -> repeat;
probe checkpoints on sealed held-out programs with clean context, adapter
on AND off (arm B). All state on disk; safe to rerun after a crash.
"""
from __future__ import annotations
import argparse
import json
import os
import random
import subprocess
import sys

from .gym_backend import CompilerGym, Episode
from .ledger import Ledger
from .loop import run_episode
from .sleep_compile import compile_sleep

HERE = os.path.dirname(os.path.abspath(__file__))
BOOTSTRAP = open(os.path.join(HERE, "bootstrap.txt")).read()

# cbench-v1 split (deterministic; probes sealed — never in training set)
PROBES = ["cbench-v1/susan", "cbench-v1/sha", "cbench-v1/dijkstra",
          "cbench-v1/patricia", "cbench-v1/jpeg-c", "cbench-v1/tiff2bw",
          "cbench-v1/gsm", "cbench-v1/stringsearch"]


def marker(path: str) -> bool:
    return os.path.exists(path)


def touch(path: str, text: str = "ok") -> None:
    with open(path, "w") as f:
        f.write(text + "\n")


def _canon(uri: str) -> str:
    """CompilerGym URIs may carry a benchmark:// prefix; normalize before
    any split comparison (contamination bug caught by Codex 2026-09-05)."""
    return uri.replace("benchmark://", "")


def get_training_programs(gym: CompilerGym, n: int, seed: int) -> list[str]:
    probes = {_canon(p) for p in PROBES}
    pool = [b for b in gym.benchmarks("cbench-v1") if _canon(b) not in probes]
    for ds in ("chstone-v0", "mibench-v1"):
        if len(pool) < n:
            pool += [b for b in gym.benchmarks(ds)
                     if _canon(b) not in probes]
    rng = random.Random(seed)
    rng.shuffle(pool)
    reps = (n // len(pool)) + 1 if pool else 1
    return ((pool * reps)[:n]) if pool else []


def latest_adapter(life_dir: str) -> str | None:
    best = None
    for d in sorted(os.listdir(life_dir)):
        p = os.path.join(life_dir, d)
        if d.startswith("sleep_") and marker(os.path.join(p, "adapter", "DONE")):
            best = os.path.join(p, "adapter")
    return best


def run_probes(model, gym, tag: str, life_dir: str, budget: int, log) -> None:
    out_path = os.path.join(life_dir, f"probe_{tag}.json")
    if marker(out_path):
        return
    results = {}
    probe_ledger = Ledger(os.path.join(life_dir, f"probe_{tag}.ledger.jsonl"))
    for b in PROBES:
        r = run_episode(model, gym, Episode(eid=b), BOOTSTRAP, probe_ledger,
                        budget_ticks=budget, log=log)
        results[b] = r["best_score"]
    tmp = out_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(dict(tag=tag, results=results,
                       mean=sum(results.values()) / len(results)), f, indent=1)
    os.rename(tmp, out_path)
    log(f"[probe {tag}] mean={sum(results.values()) / len(results):.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--life-dir", required=True)
    ap.add_argument("--arm", choices=["A", "B"], required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--episodes", type=int, default=64)
    ap.add_argument("--sleep-every", type=int, default=8)
    ap.add_argument("--probe-every", type=int, default=16)
    ap.add_argument("--budget-ticks", type=int, default=24)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    life = os.path.expanduser(args.life_dir)
    os.makedirs(life, exist_ok=True)
    log_f = open(os.path.join(life, "life.log"), "a")

    def log(msg):
        print(msg, flush=True)
        log_f.write(msg + "\n")
        log_f.flush()

    if args.smoke:
        args.episodes, args.sleep_every, args.probe_every = 2, 2, 2
        args.budget_ticks = 8

    gym = CompilerGym()
    programs = get_training_programs(gym, args.episodes, args.seed)
    log(f"[life] arm={args.arm} seed={args.seed} programs={len(programs)}")
    ledger = Ledger(os.path.join(life, "ledger.jsonl"))

    from .model_backend import VLLMBackend
    adapter = latest_adapter(life) if args.arm == "B" else None
    model = VLLMBackend(adapter_path=adapter)
    brief_path = None
    for d in sorted(os.listdir(life), reverse=True):
        p = os.path.join(life, d, "waking_brief.txt")
        if d.startswith("sleep_") and os.path.exists(p):
            brief_path = p
            break
    bootstrap = BOOTSTRAP + (
        "\n=== YOUR BRIEFING FROM LAST SLEEP ===\n" + open(brief_path).read()
        if brief_path else "")

    run_probes(model, gym, "ep000", life, args.budget_ticks, log)

    for i, prog in enumerate(programs):
        ep_marker = os.path.join(life, f"ep_{i:03d}.json")
        if not marker(ep_marker):
            r = run_episode(model, gym, Episode(eid=prog), bootstrap, ledger,
                            budget_ticks=args.budget_ticks, log=log)
            tmp = ep_marker + ".tmp"
            with open(tmp, "w") as f:
                json.dump(r, f)
            os.rename(tmp, ep_marker)

        n_done = i + 1
        if n_done % args.sleep_every == 0:
            sleep_dir = os.path.join(life, f"sleep_{n_done:03d}")
            if not marker(os.path.join(sleep_dir, "COMPILED")):
                prior = []
                for d in sorted(os.listdir(life)):
                    cp = os.path.join(life, d, "corpus.json")
                    if d.startswith("sleep_") and d != os.path.basename(
                            sleep_dir) and os.path.exists(cp):
                        prior = json.load(open(cp))["corpus"]
                res = compile_sleep(model, ledger.rows(), sleep_dir, prior)
                log(f"[sleep {n_done}] new={res['n_new']} "
                    f"principles={res['n_principles']}")
                touch(os.path.join(sleep_dir, "COMPILED"))
            if args.arm == "B" and not marker(
                    os.path.join(sleep_dir, "adapter", "DONE")):
                del model  # free the GPU for training
                import gc, torch  # noqa: E401
                gc.collect()
                torch.cuda.empty_cache()
                rc = subprocess.run(
                    [sys.executable, "-m", "organism_v6.train_adapter",
                     "--corpus", os.path.join(sleep_dir, "corpus.json"),
                     "--out", os.path.join(sleep_dir, "adapter"),
                     "--rank", str(args.rank)],
                    cwd=os.path.dirname(HERE)).returncode
                log(f"[sleep {n_done}] train rc={rc}")
                adapter = latest_adapter(life) if args.arm == "B" else None
                model = VLLMBackend(adapter_path=adapter)
                bp = os.path.join(sleep_dir, "waking_brief.txt")
                if os.path.exists(bp) and open(bp).read().strip():
                    bootstrap = BOOTSTRAP + (
                        "\n=== YOUR BRIEFING FROM LAST SLEEP ===\n"
                        + open(bp).read())

        if n_done % args.probe_every == 0:
            run_probes(model, gym, f"ep{n_done:03d}", life,
                       args.budget_ticks, log)
            if args.arm == "B" and latest_adapter(life):
                off = VLLMBackend(adapter_path=None) if False else None
                # adapter-off diagnostic: rerun probes with base model
                del model
                import gc, torch  # noqa: E401
                gc.collect()
                torch.cuda.empty_cache()
                base_model = VLLMBackend(adapter_path=None)
                run_probes(base_model, gym, f"ep{n_done:03d}_adapterOFF",
                           life, args.budget_ticks, log)
                del base_model
                gc.collect()
                torch.cuda.empty_cache()
                model = VLLMBackend(adapter_path=latest_adapter(life))

    touch(os.path.join(life, "LIFE_DONE"))
    log("[life] DONE")


if __name__ == "__main__":
    main()
