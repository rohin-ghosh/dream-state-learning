"""Verbose single-episode trace — diagnoses WHY a model fails the S0 manual gate.

Prints the full first prompt, then per step: the model's RAW generation, the
PARSED action, and the resulting obs. Flags every parse fallback (raw text that
did not contain a runnable action → silent 'inspect').

Usage (node):
  PYTHONPATH=. python gpu/debug_episode.py --model Qwen/Qwen2.5-1.5B-Instruct
Local smoke test (no GPU):
  PYTHONPATH=. python gpu/debug_episode.py --model mock
"""

from __future__ import annotations

import argparse

from game import World
from felt.llm_player import play_episode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--mode", default="manual", choices=("manual", "none"))
    ap.add_argument("--episodes", type=int, default=2)
    ap.add_argument("--max-steps", type=int, default=25)
    ap.add_argument("--depth", type=int, default=4)
    a = ap.parse_args()

    if a.model == "mock":
        from felt.llm_player import MockTextPlayer
        make_backend = lambda: MockTextPlayer()
    else:
        from felt.llm_player import HFBackend
        b = HFBackend(a.model)
        make_backend = lambda: b

    # same world/goal scheme as gate_calibration world 0
    world = World.generate("gate_0", seed=5000, depth=a.depth)
    goals = list(world.dag.recipes)

    for e in range(a.episodes):
        goal = goals[e % len(goals)]
        state = {"step": 0, "fallbacks": 0, "printed_prompt": False}

        def trace(prompt, raw, action, obs):
            state["step"] += 1
            if not state["printed_prompt"]:
                print("=" * 72)
                print(f"EPISODE {e} | goal={goal} | mode={a.mode}")
                print("=" * 72)
                print("FULL FIRST PROMPT:\n" + prompt)
                print("-" * 72)
                state["printed_prompt"] = True
            fell_back = action == "inspect" and "inspect" not in raw.lower()
            state["fallbacks"] += fell_back
            flag = "  <<< PARSE FALLBACK (raw had no action line)" if fell_back else ""
            print(f"[{state['step']:02d}] RAW: {raw!r}{flag}")
            print(f"     ACT: {action}")
            print(f"     OBS: {obs}")

        r = play_episode(world, make_backend(), goal, episode_seed=e,
                         context_mode=a.mode, max_steps=a.max_steps, trace=trace)
        print(f"\n>> episode {e}: success={r['success']} steps={r['steps']} "
              f"parse_fallbacks={state['fallbacks']}/{state['step']}\n")


if __name__ == "__main__":
    main()
