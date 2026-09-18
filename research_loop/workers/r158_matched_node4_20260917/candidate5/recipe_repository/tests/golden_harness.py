"""Golden-transcript harness for run_life_v2 (CPU, no GPU, no gym venv).

Drives organism_v6.run_life_v2.main() end to end with:
  - a scripted FakeModel in place of VLLMBackend (deterministic chunks chosen
    by the per-chunk seed; deterministic THINK replies for the compiler);
  - a fake CompilerGym._call (deterministic instruction counts per program,
    a fixed valid-pass list, INVALID hints for unknown passes; no subprocess);
  - a fake sleep trainer (writes adapter/DONE + train_meta.json);
  - close_backend -> True; time.time frozen (CLOCK 'alive Ns' and time_cost
    are otherwise wall-clock dependent).
Every prompt the child sees, every chunk it wrote, every gym evaluation the
harness parsed out of its ACT lines, every THINK prompt and every parent
call are recorded, together with the ledger and every deterministic file the
life wrote. tests/test_compiler_golden.py records this once from the code as
it stood before the Gym-protocol refactor and afterwards diffs against it.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import sys
import tempfile
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# parent room configuration must be in the environment BEFORE agentic_parent
# is imported (it snapshots PARENT_* at import): a mock provider, a temp
# society dir, a fresh temp HOME-independent location.
_SOCIETY = tempfile.mkdtemp(prefix="golden_society_")
os.environ["PARENT_PROVIDER"] = "mock"
os.environ["PARENT_MODEL"] = "mock-parent"
os.environ["PARENTAL_SOCIETY_DIR"] = _SOCIETY
os.environ.pop("PARENT_API_KEY", None)

from organism_v6 import run_life_v2  # noqa: E402
from organism_v6 import model_backend  # noqa: E402
from organism_v6 import gym_backend  # noqa: E402
from organism_v6 import parent_backend  # noqa: E402
from organism_v6 import agentic_parent  # noqa: E402,F401  (snapshot env now)

FROZEN_TIME = 1_700_000_000.0

# --- the fake world -----------------------------------------------------------
RECIPE = "-mem2reg, -sroa, -gvn, -simplifycfg"
VALID_PASSES = {"-mem2reg": 0.12, "-sroa": 0.08, "-gvn": 0.06,
                "-simplifycfg": 0.05, "-instcombine": 0.07, "-licm": 0.03,
                "-early-cse": 0.04, "-dce": 0.02}
DATASETS = {
    "cbench-v1": ["cbench-v1/crc32", "cbench-v1/bitcount", "cbench-v1/qsort",
                  "cbench-v1/adpcm", "cbench-v1/blowfish", "cbench-v1/susan",
                  "cbench-v1/sha", "cbench-v1/dijkstra", "cbench-v1/patricia",
                  "cbench-v1/jpeg-c", "cbench-v1/tiff2bw", "cbench-v1/gsm",
                  "cbench-v1/stringsearch", "cbench-v1/rijndael"],
    "chstone-v0": ["chstone-v0/aes", "chstone-v0/gsm", "chstone-v0/mips"],
    "mibench-v1": ["mibench-v1/bitcount", "mibench-v1/qsort"],
}
GATE_PANEL = ["benchmark://npb-v0/10", "benchmark://npb-v0/25",
              "benchmark://blas-v0/10", "benchmark://opencv-v0/60"]

# chunk templates: same recipe + flat PREDICT in most chunks (so the ritual
# metrics flag and the parent fires), a markdown-dialect NOTE, an INVALID
# pass, two ACTs in one chunk, a RECALL and a DONE.
TEMPLATES = [
    "PREDICT: 0.3\nACT: " + RECIPE + "\nNOTE: The standard recipe works well; "
    "keep using it on this program.",
    "PREDICT: 0.3\nACT: " + RECIPE + "\nRECALL: best passes for this program",
    "Let me think about this program first.\nPREDICT: 0.3\nACT: " + RECIPE +
    "\n### NOTE: markdown dialect note; the recipe is my default.",
    "PREDICT: 0.3\nACT: -bogus-pass\nNOTE: trying something new here\n"
    "ACT: -gvn, -instcombine\nDONE",
]
# a reasoning-gym child in the fake world (positive detection: the puzzle
# gym's prompts say "verifier"; compiler prompts never do): target-blind
# chunks, so the childhood's deployment-vocabulary scan stays clean
RG_TEMPLATES = [
    "PREDICT: 0.3\nACT: 1 2 3 4\nNOTE: The first row looks fixed; check the "
    "columns next.",
    "PREDICT: 0.2\nACT: 4 3 2 1\nRECALL: puzzles like this one",
    "Let me read the rules again.\nPREDICT: 0.4\nACT: 2 1 4 3\n### NOTE: "
    "markdown dialect note; try a different corner.",
    "PREDICT: 0.1\nACT: \nNOTE: an empty attempt is invalid\nACT: 3 4 1 2\nDONE",
]
RG_REFLECTION = ("I notice I answer before I have read the whole puzzle; next "
                 "time I want to state the constraint I am testing first.")

# test knob: make the fake trainer raise on its next N calls (resume tests)
FAKE_TRAINER_FAIL = {"remaining": 0}


class Transcript:
    def __init__(self):
        self.events: list = []

    def add(self, **ev):
        self.events.append(ev)


class FakeModel:
    """Stands in for model_backend.VLLMBackend."""
    transcript: Transcript = None          # set by run_scenario

    def __init__(self, adapter_path=None, max_model_len=16384):
        self.adapter_path = adapter_path
        self.llm = self                     # close_backend is patched anyway

    def shutdown(self):
        pass

    @staticmethod
    def _is_puzzle(prompt: str) -> bool:
        return "verifier" in prompt or "puzzle workshop" in prompt

    def batch(self, prompts, max_tokens=400, temperature=0.7, seeds=None):
        outs = []
        for j, p in enumerate(prompts):
            s = seeds[j] if seeds is not None else zlib.crc32(p.encode())
            if self._is_puzzle(p):
                t = RG_REFLECTION if "PRIVATE REFLECTION TIME" in p \
                    else RG_TEMPLATES[s % len(RG_TEMPLATES)]
            else:
                t = TEMPLATES[s % len(TEMPLATES)]
            outs.append(t)
            FakeModel.transcript.add(kind="batch", adapter=self.adapter_path,
                                     seed=s, prompt=p, output=t)
        return outs

    def __call__(self, prompt, max_tokens=400, temperature=0.7, seed=None):
        if "PRINCIPLES" in prompt:
            if "puzzles" in prompt:
                out = ("PRINCIPLE: when the grid is small, test one corner "
                       "first, because measured partial credit rose [puzzles: "
                       "rg/mini_sudoku/1000001, rg/countdown/1000002]\nnot a line")
            else:
                out = ("PRINCIPLE: when the program is small, apply the recipe "
                       "first, because measured 10-30% reduction [programs: "
                       "cbench-v1/crc32, cbench-v1/qsort]\nnot a principle line")
        elif "puzzles" in prompt:
            out = ("Briefing: read the whole puzzle before the first attempt; "
                   "state the constraint you test and predict it first.")
        else:
            out = ("Briefing: the recipe gives most of the gain; try one "
                   "deviation per program and predict it first.")
        FakeModel.transcript.add(kind="think", adapter=self.adapter_path,
                                 prompt=prompt, output=out)
        return out


def make_fake_call(transcript: Transcript):
    def fake_call(self, *cli):
        args = {}
        for a in cli:
            k, _, v = a.lstrip("-").partition("=")
            args[k] = v
        if args.get("list-benchmarks"):
            return {"ok": True, "benchmarks": list(DATASETS.get(
                args["list-benchmarks"], []))}
        bench = args.get("benchmark", "")
        passes = [p for p in args.get("passes", "").split(",") if p]
        transcript.add(kind="gym_eval", benchmark=bench,
                       passes=args.get("passes", ""))
        base = 1000 + zlib.crc32(bench.encode()) % 5000
        after = base
        for p in passes:
            if p not in VALID_PASSES:
                return {"ok": False, "base": base, "after": after,
                        "score": (base - after) / base,
                        "error": f"unknown pass '{p}'. Passes look like "
                                 f"'-mem2reg', '-sroa', '-gvn', '-simplifycfg'."
                                 f" {len(VALID_PASSES)} valid passes exist."}
            after = int(after * (1 - VALID_PASSES[p]))
        return {"ok": True, "base": base, "after": after,
                "score": (base - after) / base, "error": ""}
    return fake_call


class _RC:
    def __init__(self, rc):
        self.returncode = rc


def make_fake_subprocess_run(transcript: Transcript):
    def fake_run(cmd, *a, **kw):
        cmd = list(cmd)
        if FAKE_TRAINER_FAIL["remaining"] > 0:
            FAKE_TRAINER_FAIL["remaining"] -= 1
            raise RuntimeError("simulated trainer crash")
        out = cmd[cmd.index("--out") + 1]
        corpus = cmd[cmd.index("--corpus") + 1]
        n = len(json.load(open(corpus))["corpus"])
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "train_meta.json"), "w") as f:
            json.dump(dict(recipe="fake", n_texts=n), f)
        with open(os.path.join(out, "DONE"), "w") as f:
            f.write("ok\n")
        transcript.add(kind="train", corpus_items=n,
                       flags=[c for c in cmd if c.startswith("--")])
        return _RC(0)
    return fake_run


def make_fake_parent_chat(transcript: Transcript):
    def fake_chat(self, prompt, max_tokens=220, temperature=0.4):
        out = ("You open every program with the same four steps and expect the "
               "same result.\nBefore you act, name one feature of THIS program "
               "and say what it makes you expect, with a range.\nWhen the "
               "outcome disagrees, write which belief was wrong.")
        transcript.add(kind="parent_chat", prompt=prompt, output=out)
        return out
    return fake_chat


# --- collection ------------------------------------------------------------------
_SKIP = re.compile(r"^(life\.log|parent_ledger\.jsonl|parent_playbook\.md)$")


def collect_files(life: str) -> dict:
    """Every deterministic file of the life directory (text), sorted."""
    out = {}
    for dp, dns, fns in os.walk(life):
        dns.sort()
        for fn in sorted(fns):
            if _SKIP.match(fn):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, life)
            if os.path.islink(p):
                out[rel] = "<symlink> " + os.path.basename(os.readlink(p))
                continue
            with open(p, errors="replace") as f:
                txt = f.read()
            if fn.endswith(".json"):
                try:
                    txt = json.dumps(json.loads(txt), sort_keys=True)
                except ValueError:
                    pass
            out[rel] = txt
    return out


SCENARIOS = {
    # today's flags, arm B, probe gate on the disjoint panel (the R4-style run)
    "armB_gate_panel": ["--arm", "B", "--probe-gate", "--gate-panel", "GATE"],
    # arm A: frozen loop (compile happens, no training)
    "armA": ["--arm", "A"],
    # arm B with the baseline thinking-pattern parent (ritual-triggered)
    "armB_parent_brief": ["--arm", "B", "--probe-gate", "--parent-url",
                          "http://[REDACTED_ADDRESS]:1/v1", "--parent-mode", "brief"],
    # arm B with the agentic room (mock provider), legacy gate, plasticity
    "armB_parent_agentic": ["--arm", "B", "--probe-gate", "--plasticity",
                            "--parent-url", "http://[REDACTED_ADDRESS]:1/v1",
                            "--parent-mode", "agentic"],
}
BASE_ARGS = ["--seed", "0", "--episodes", "16", "--sleep-every", "8",
             "--probe-every", "8", "--budget-ticks", "3", "--wake-batch", "4",
             "--rank", "8"]


@contextlib.contextmanager
def fake_world(tr: Transcript, freeze_time: bool = True):
    """Apply every fake (model, gym subprocess, trainer, GPU close, parent
    chat, frozen clock) for the duration of the block; restore afterwards."""
    saved = dict(time=time.time, vllm=model_backend.VLLMBackend,
                 close=model_backend.close_backend,
                 call=gym_backend.CompilerGym._call,
                 run=run_life_v2.subprocess.run,
                 chat=parent_backend.ServerParent._chat)
    FakeModel.transcript = tr
    try:
        if freeze_time:
            time.time = lambda: FROZEN_TIME
        model_backend.VLLMBackend = FakeModel
        model_backend.close_backend = lambda backend: True
        gym_backend.CompilerGym._call = make_fake_call(tr)
        run_life_v2.subprocess.run = make_fake_subprocess_run(tr)
        parent_backend.ServerParent._chat = make_fake_parent_chat(tr)
        yield tr
    finally:
        time.time = saved["time"]
        model_backend.VLLMBackend = saved["vllm"]
        model_backend.close_backend = saved["close"]
        gym_backend.CompilerGym._call = saved["call"]
        run_life_v2.subprocess.run = saved["run"]
        parent_backend.ServerParent._chat = saved["chat"]


def run_life(argv: list, tr: Transcript | None = None,
             freeze_time: bool = True) -> Transcript:
    """run_life_v2.main() with the given argv under the fakes."""
    tr = tr or Transcript()
    saved_argv = sys.argv
    try:
        with fake_world(tr, freeze_time=freeze_time):
            sys.argv = ["run_life_v2"] + list(argv)
            run_life_v2.main()
    finally:
        sys.argv = saved_argv
    return tr


def run_scenario(name: str, extra_argv=None, keep_dir=None) -> dict:
    """Run one run_life_v2 life under the fakes; return the transcript."""
    argv = list(SCENARIOS[name]) if extra_argv is None else list(extra_argv)
    root = keep_dir or tempfile.mkdtemp(prefix=f"golden_{name}_")
    life = os.path.join(root, "life")
    gate_json = os.path.join(root, "gate_panel.json")
    with open(gate_json, "w") as f:
        json.dump(GATE_PANEL, f)
    argv = [a if a != "GATE" else gate_json for a in argv]
    tr = run_life(["--life-dir", life] + BASE_ARGS + argv)
    out = dict(scenario=name, argv=BASE_ARGS + argv, events=tr.events,
               files=collect_files(life), life_dir=life)
    return _normalize(out, os.path.realpath(root), root)


def _normalize(obj, *roots):
    """Temp directories differ between runs: replace them with <ROOT>."""
    if isinstance(obj, str):
        for r in roots:
            obj = obj.replace(r, "<ROOT>")
        return obj
    if isinstance(obj, dict):
        return {k: _normalize(v, *roots) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize(v, *roots) for v in obj]
    return obj


def run_all(names=None) -> dict:
    return {n: run_scenario(n) for n in (names or SCENARIOS)}


def summarize(tr: dict) -> dict:
    ev = tr["events"]
    kinds = {}
    for e in ev:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    return dict(events=len(ev), by_kind=kinds, files=len(tr["files"]))


if __name__ == "__main__":
    out = run_all()
    for n, t in out.items():
        print(n, json.dumps(summarize(t)))
