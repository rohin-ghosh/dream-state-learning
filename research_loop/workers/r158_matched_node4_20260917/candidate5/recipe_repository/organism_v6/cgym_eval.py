"""Gym-side evaluator. Runs under the py3.10 CompilerGym venv on the node:
  LD_LIBRARY_PATH=$HOME/cgym_test/lib ~/cgym_test/venv/bin/python cgym_eval.py \
      --benchmark cbench-v1/crc32 --passes "-mem2reg,-sroa" [--list-actions]
Prints one JSON line: {"ok":bool, "base":int, "after":int, "score":float,
"error":str}. Score = relative instruction reduction (base-after)/base.
Deterministic (verified by scout). Invalid pass names -> ok=false with the
valid-action hint in error (teaching signal, not a crash).
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", required=True)
    ap.add_argument("--passes", default="")
    ap.add_argument("--list-actions", action="store_true")
    ap.add_argument("--list-benchmarks", default="")
    ap.add_argument("--ref", action="store_true",
                    help="print -Oz and -O3 reference instruction counts and "
                         "reductions for the benchmark (review M5)")
    args = ap.parse_args()

    import compiler_gym  # noqa: F401
    import gym as _gym
    env = _gym.make("llvm-v0", observation_space="IrInstructionCount")
    try:
        if args.ref:
            env.reset(benchmark=args.benchmark)
            base = int(env.observation["IrInstructionCount"])
            oz = int(env.observation["IrInstructionCountOz"])
            o3 = int(env.observation["IrInstructionCountO3"])
            print(json.dumps({"ok": True, "base": base, "Oz": oz, "O3": o3,
                              "score_Oz": (base - oz) / base if base else 0.0,
                              "score_O3": (base - o3) / base if base else 0.0}))
            return
        if args.list_actions:
            print(json.dumps({"ok": True,
                              "actions": list(env.action_space.names)}))
            return
        if args.list_benchmarks:
            ds = env.datasets[args.list_benchmarks]
            print(json.dumps({"ok": True,
                              "benchmarks": [str(b) for b in
                                             list(ds.benchmark_uris())[:400]]}))
            return
        obs = env.reset(benchmark=args.benchmark)
        base = int(obs)
        names = list(env.action_space.names)
        after = base
        for p in [x.strip() for x in args.passes.split(",") if x.strip()]:
            if p not in names:
                print(json.dumps({
                    "ok": False, "base": base, "after": after,
                    "score": (base - after) / base if base else 0.0,
                    "error": f"unknown pass '{p}'. Passes look like "
                             f"'-mem2reg', '-sroa', '-gvn', '-simplifycfg'. "
                             f"{len(names)} valid passes exist."}))
                return
            obs, _, done, _ = env.step(names.index(p))
            after = int(obs)
            if done:
                break
        print(json.dumps({"ok": True, "base": base, "after": after,
                          "score": (base - after) / base if base else 0.0,
                          "error": ""}))
    finally:
        env.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 — gym-side failures must be data
        print(json.dumps({"ok": False, "base": 0, "after": 0, "score": 0.0,
                          "error": f"{type(e).__name__}: {e}"[:300]}))
        sys.exit(0)
