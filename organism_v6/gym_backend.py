"""Gym backends and the Gym protocol.

Part 1 (unchanged since v6.0): `Episode` and `CompilerGym` — the CompilerGym
subprocess backend (py3.10 venv on the node) that `run_life`, `probe_adapter`,
`nursery`, `classroom_round` and friends import directly. Nothing about their
behaviour changed in the 2026-09-10 refactor; `Episode` only GAINED optional
trailing fields (family, budget_ticks, best_score, n_attempts) and read-only
aliases (id, goal_text, intro_text, metric_name) for the protocol below.

Part 2 (2026-09-10, NEXT_EXPERIMENT_DESIGN_v1 section 3.6): the `Gym`
protocol and a registry. The runner (`run_life_v2 --gym NAME`) never touches a
gym-specific object: episode creation, stepping, evaluation, the probe/exam
set, the gate set, the canary set, the birth prompt, the exposure domain and
the parent's leak terms all come from the Gym object. `CompilerGymGym` wraps
the existing compiler behaviour EXACTLY (same pass parsing, same cgym_eval
call, the same 8 report programs, the disjoint panel as the gate set, the
same birth prompt) — tests/test_compiler_golden.py proves byte-identity of
every prompt and every parsed action against a transcript recorded before the
refactor. `reasoning_gym` is registered lazily (organism_v6/reasoning_gym_gym.py)
so the compiler path never imports the pip package.

EpisodeDriver contract kept: `gym.evaluate(episode, action_text)` still
returns `(score, outcome_text)`; called WITHOUT an action, `evaluate(episode)`
returns the episode's score so far (best attempt) as a float in [0, 1].
"""
from __future__ import annotations
import json
import os
import random
import subprocess
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

CGYM_PY = os.path.expanduser("~/cgym_test/venv/bin/python")
CGYM_ENV = {"LD_LIBRARY_PATH": os.path.expanduser("~/cgym_test/lib")}
EVAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cgym_eval.py")

SPLITS = ("train", "gate", "exam", "canary")


@dataclass
class Episode:
    eid: str            # e.g. "cbench-v1/crc32"
    goal: str = ""
    metric: str = ""
    intro: str = ""
    # protocol fields (2026-09-10); never rendered into the child's context
    family: str = ""
    budget_ticks: int | None = None
    best_score: float = 0.0     # best attempt so far (maintained by Gym.step)
    n_attempts: int = 0

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

    # protocol aliases: Episode(id, family, goal_text, intro_text, metric_name)
    @property
    def id(self) -> str:
        return self.eid

    @property
    def goal_text(self) -> str:
        return self.goal

    @property
    def intro_text(self) -> str:
        return self.intro

    @property
    def metric_name(self) -> str:
        return self.metric


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


# ---------------------------------------------------------------------------
# the Gym protocol (section 3.6)
# ---------------------------------------------------------------------------
@dataclass
class Observation:
    """What one ACT returns to the harness."""
    text: str                   # goes into the child's stream as [OUTCOME]
    score: float                # in [0, 1]
    harness_done: bool = False  # the gym ended the situation (rare; the budget
                                # is the normal end)


@runtime_checkable
class Gym(Protocol):
    """Splits are held out by IDENTIFIER or FAMILY, never by random instance
    draw: `benchmarks(split)` enumerates them; `make_episode(split, rng)`
    draws within a split. `leak_terms()` are identifiers the parent must
    never utter; `headroom_ceiling(episode)` is the exact ceiling (1.0 for a
    verifier) or None when unknown (the compiler gym)."""
    name: str

    def splits(self) -> list[str]: ...
    def benchmarks(self, split: str) -> list[str]: ...
    def episode_from_id(self, eid: str, budget_ticks: int | None = None) -> Episode: ...
    def make_episode(self, split: str, rng: random.Random,
                     budget_ticks: int | None = None) -> Episode: ...
    def training_schedule(self, n: int, seed: int) -> list[str]: ...
    def step(self, episode: Episode, action_text: str) -> Observation: ...
    def evaluate(self, episode: Episode, action_text: str | None = None): ...
    def canary_set(self) -> list[str]: ...
    def gate_set(self) -> list[str] | None: ...
    def exam_set(self) -> list[str]: ...
    def birth_prompt(self) -> str: ...
    def exposure_domain(self) -> str: ...
    def leak_terms(self) -> list[str]: ...
    def headroom_ceiling(self, episode: Episode) -> float | None: ...
    def family_of(self, eid: str) -> str | None: ...
    def offers_end_token(self) -> bool: ...
    def compile_vocab(self) -> dict: ...


def _canon(uri: str) -> str:
    return uri.replace("benchmark://", "")


# The DEPLOYMENT gym's vocabulary (IDEAS 2026-09-10 late, Decision 1: the
# compiler gym is the unseen final test). A childhood life in any other gym
# must store no prompt or note that carries it (design 3.6: the leak scan
# over every stored prompt and note must hit zero, or the seal is refused).
# Matched case-insensitively as whole tokens by run_life_v2.leak_scan_ledger.
# There is no full LLVM pass list in the repository: this list is the birth
# recipe, the passes the harness and the parent scanner name, the common
# llvm-v0 passes, the dataset names and the deployment gym's own words.
DEPLOYMENT_LEAK_TERMS = [
    "-mem2reg", "-sroa", "-gvn", "-simplifycfg", "-instcombine", "-licm",
    "-early-cse", "-dce", "-adce", "-loop-unroll", "-loop-rotate", "-indvars",
    "-jump-threading", "-reassociate", "-sccp", "-ipsccp", "-inline",
    "-globalopt", "-globaldce", "-deadargelim", "-functionattrs", "-tailcallelim",
    "-loop-simplify", "-lcssa", "-loop-deletion", "-loop-unswitch",
    "-newgvn", "-memcpyopt", "-bdce", "-dse", "-constmerge", "-strip",
    "-argpromotion", "-mergefunc", "-lowerswitch", "-mergereturn",
    "-loop-reduce", "-loop-idiom", "-correlated-propagation", "-aggressive-instcombine",
    "-O0", "-O1", "-O2", "-O3", "-Os", "-Oz",
    "llvm", "LLVM IR", "IrInstructionCount", "instruction count",
    "optimization pass", "optimization passes", "compiler pass",
    "cbench-v1", "chstone-v0", "mibench-v1", "npb-v0", "blas-v0",
    "opencv-v0", "tensorflow-v0", "CompilerGym", "benchmark://",
]


class CompilerGymGym:
    """The existing compiler behaviour behind the Gym protocol.

    - train: cbench-v1 minus the 8 report programs, extended with chstone-v0
      and mibench-v1 when a schedule needs more (run_life.get_training_programs,
      unchanged and reused verbatim by training_schedule);
    - exam: the 8 report programs (run_life.PROBES) — the paper's panel;
    - gate: the disjoint panel given at construction (--gate-panel JSON), or
      None = the legacy gate on the report panel (R3/R4 arms);
    - canary: the first 4 report programs, exactly as format_canary used them;
    - birth prompt: organism_v6/bootstrap.txt (run_life.BOOTSTRAP);
    - step/evaluate: CompilerGym.evaluate — same pass parsing, same subprocess.
    """
    name = "compiler"
    reports_family_accuracy = False

    def __init__(self, gate_panel: list[str] | None = None, backend=None,
                 timeout: int = 120):
        from .run_life import PROBES, BOOTSTRAP   # lazy: run_life imports us
        self.backend = backend or CompilerGym(timeout)
        self._report = list(PROBES)
        self._bootstrap = BOOTSTRAP
        self._gate = list(gate_panel) if gate_panel else None
        if self._gate:
            overlap = set(self._gate) & set(self._report)
            if overlap:
                raise RuntimeError(f"gate panel overlaps report panel: {overlap}")

    # -- splits ---------------------------------------------------------------
    def splits(self) -> list[str]:
        return list(SPLITS)

    def benchmarks(self, split: str) -> list[str]:
        if split == "train":
            probes = {_canon(p) for p in self._report}
            return [b for b in self.backend.benchmarks("cbench-v1")
                    if _canon(b) not in probes]
        if split == "gate":
            return list(self._gate or [])
        if split == "exam":
            return list(self._report)
        if split == "canary":
            return self.canary_set()
        return self.backend.benchmarks(split)      # a dataset name, as before

    def training_schedule(self, n: int, seed: int) -> list[str]:
        from .run_life import get_training_programs
        return get_training_programs(self.backend, n, seed)

    def episode_from_id(self, eid: str, budget_ticks: int | None = None) -> Episode:
        return Episode(eid=eid, family=self.family_of(eid) or "",
                       budget_ticks=budget_ticks)

    def make_episode(self, split: str, rng: random.Random,
                     budget_ticks: int | None = None) -> Episode:
        pool = self.benchmarks(split)
        if not pool:
            raise RuntimeError(f"compiler gym: split {split!r} is empty")
        return self.episode_from_id(rng.choice(pool), budget_ticks)

    # -- acting ---------------------------------------------------------------
    def step(self, episode: Episode, action_text: str) -> Observation:
        score, text = self.backend.evaluate(episode, action_text)
        episode.n_attempts += 1
        if score > episode.best_score:
            episode.best_score = score
        return Observation(text=text, score=score, harness_done=False)

    def evaluate(self, episode: Episode, action_text: str | None = None):
        if action_text is None:
            return float(episode.best_score)
        obs = self.step(episode, action_text)
        return obs.score, obs.text

    # -- sets and texts ---------------------------------------------------------
    def canary_set(self) -> list[str]:
        return list(self._report[:4])

    def gate_set(self) -> list[str] | None:
        return list(self._gate) if self._gate else None

    def exam_set(self) -> list[str]:
        return list(self._report)

    def birth_prompt(self) -> str:
        return self._bootstrap

    def exposure_domain(self) -> str:
        return "compiler_gym:llvm-v0:IrInstructionCount"

    def leak_terms(self) -> list[str]:
        """The birth recipe's pass names and every held-out program id."""
        terms = ["-mem2reg", "-sroa", "-gvn", "-simplifycfg"]
        for p in self._report + (self._gate or []):
            terms.append(_canon(p))
        return terms

    def headroom_ceiling(self, episode: Episode) -> float | None:
        return None      # no exact ceiling: -Oz/-O3 are references, not bounds

    def family_of(self, eid: str) -> str | None:
        c = _canon(eid)
        return c.split("/", 1)[0] if "/" in c else None

    def offers_end_token(self) -> bool:
        return True

    def compile_vocab(self) -> dict:
        """The sleep compiler's nouns for this gym: the historical compiler
        strings (sleep_compile.COMPILER_VOCAB; byte-identical corpus)."""
        from .sleep_compile import COMPILER_VOCAB
        return dict(COMPILER_VOCAB)


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------
def _make_reasoning_gym(**kw):
    from .reasoning_gym_gym import ReasoningGymGym
    return ReasoningGymGym(**kw)


_REGISTRY = {
    "compiler": lambda **kw: CompilerGymGym(**kw),
    "reasoning_gym": _make_reasoning_gym,
}


def gym_names() -> list[str]:
    return sorted(_REGISTRY)


def register_gym(name: str, factory) -> None:
    _REGISTRY[name] = factory


def make_gym(name: str, **kw) -> Gym:
    """Instantiate a registered gym. Every gym accepts `gate_panel` (a list
    of episode ids, or None for its default gate set); unknown keywords are
    an error."""
    if name not in _REGISTRY:
        raise KeyError(f"unknown gym {name!r}; registered: {gym_names()}")
    return _REGISTRY[name](**kw)
