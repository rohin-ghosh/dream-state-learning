"""CompilerGym backend (subprocess to the py3.10 venv) + Episode spec.
Runs ON the node. Latency ~0.5-1s/eval — model generation dominates.
"""
from __future__ import annotations
import json
import os
import subprocess
from dataclasses import dataclass

CGYM_PY = os.path.expanduser("~/cgym_test/venv/bin/python")
CGYM_ENV = {"LD_LIBRARY_PATH": os.path.expanduser("~/cgym_test/lib")}
EVAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cgym_eval.py")


@dataclass
class Episode:
    eid: str            # e.g. "cbench-v1/crc32"
    goal: str = ""
    metric: str = ""
    intro: str = ""

    def __post_init__(self):
        if not self.goal:
            self.goal = (f"Optimize program '{self.eid}': choose LLVM "
                         f"optimization passes that minimize its IR "
                         f"instruction count.")
        if not self.metric:
            self.metric = ("score = (base_instructions - after) / base. "
                           "Higher is better; 0 = no improvement. Passes are "
                           "applied in the order you give them.")
        if not self.intro:
            self.intro = (f"New program: {self.eid}. I should form an "
                          f"expectation before acting, and write down what "
                          f"I learn.")


class CompilerGym:
    def __init__(self, timeout: int = 120):
        self.timeout = timeout

    def _call(self, *cli) -> dict:
        env = dict(os.environ)
        env.update(CGYM_ENV)
        p = subprocess.run([CGYM_PY, EVAL, *cli], capture_output=True,
                           text=True, timeout=self.timeout, env=env)
        line = (p.stdout.strip().splitlines() or ["{}"])[-1]
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return {"ok": False, "score": 0.0,
                    "error": f"gym-io: {p.stderr[-200:]}"}

    def evaluate(self, episode: Episode, action: str) -> tuple[float, str]:
        """action = comma/space separated pass names, e.g. '-mem2reg, -gvn'."""
        passes = ",".join(t for t in action.replace(" ", ",").split(",") if t)
        r = self._call(f"--benchmark={episode.eid}", f"--passes={passes}")
        if not r.get("ok"):
            return 0.0, f"INVALID: {r.get('error', 'unknown gym error')}"
        return (float(r["score"]),
                f"instructions {r['base']} -> {r['after']} "
                f"({100 * r['score']:.1f}% reduction)")

    def benchmarks(self, dataset: str = "cbench-v1") -> list[str]:
        r = self._call("--benchmark=x", f"--list-benchmarks={dataset}")
        return r.get("benchmarks", []) if r.get("ok") else []
