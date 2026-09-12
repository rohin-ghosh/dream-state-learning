"""reasoning-gym adapter (GYM_SURVEY_v1 C5; NEXT_EXPERIMENT_DESIGN_v1 3.6).

pip reasoning-gym==0.1.25 — 106 procedural generators with algorithmic
verifiers. Here: families = generator names; TARGET-BLIND (codeio,
list_functions and everything code-like are excluded); train, gate and exam
families are held out BY FAMILY NAME (fixed lists in
organism_v6/reasoning_gym_families.json) with disjoint seed ranges per split
on top; the exam families never appear in train, gate or canary.

Multi-attempt episode: every ACT is an answer attempt; the verifier's exact
score (partial credit where the generator supports it) comes back as
feedback WITHOUT the answer; there is no end token (the episode runs to its
tick budget — the child may keep attempting or reflect); the episode score
is the best attempt. Per-family accuracy is written into every probe file
(run_life_v2.run_probes_batch). canary = 4 fixed train items; gate = a fixed
held-out family list (never the exam families); prompt sizes are measured by
measure_prompt_sizes().

Episode ids: "rg/<family>/<seed>" — the item is regenerated deterministically
from (family, seed) with the generator's default config, so a split is a set
of ids, never a random draw.

Answer lines: the marker parser takes ONE line after ACT:. Where a puzzle
expects several lines (n_queens boards, sudoku rows, hanoi moves) the child
separates them with ' ; ' and decode_answer() restores the newlines. None of
the twelve families uses ';' inside an answer.
"""
from __future__ import annotations
import json
import os
import random
import re
import statistics

from .gym_backend import Episode, Observation, SPLITS

HERE = os.path.dirname(os.path.abspath(__file__))
FAMILIES_JSON = os.path.join(HERE, "reasoning_gym_families.json")
BOOTSTRAP_PATH = os.path.join(HERE, "bootstrap_reasoning_gym.txt")
PINNED_VERSION = "0.1.25"
LINE_SEP = " ; "
_ID = re.compile(r"^rg/([a-z0-9_]+)/(\d+)$")
# family names that would make the childhood non-target-blind
_CODE_LIKE = re.compile(r"code|function|program|compil|llvm|pass|bitwise|string",
                        re.I)


def make_id(family: str, seed: int) -> str:
    return f"rg/{family}/{int(seed)}"


def parse_id(eid: str) -> tuple[str, int]:
    m = _ID.match(eid or "")
    if not m:
        raise ValueError(f"not a reasoning-gym episode id: {eid!r}")
    return m.group(1), int(m.group(2))


def decode_answer(action_text: str) -> str:
    """ACT line -> the answer string handed to the verifier: ' ; ' (or a bare
    ';') separates lines. Only the separator's OWN padding (one optional
    space on each side) is removed: futoshiki's constraint rows are
    position-aligned with leading spaces and its exact match needs them."""
    out = "\n".join(re.split(r" ?; ?", action_text or ""))
    return out.strip("\n").rstrip()


def installed_version() -> str | None:
    try:
        from importlib.metadata import version
        return version("reasoning_gym")
    except Exception:  # noqa: BLE001
        return None


class ReasoningGymGym:
    name = "reasoning_gym"
    reports_family_accuracy = True

    def __init__(self, families_path: str = FAMILIES_JSON,
                 gate_panel: list[str] | None = None, cache_size: int = 512,
                 require_package: bool = True, strict_verifier: bool = False):
        self.strict_verifier = strict_verifier
        with open(families_path) as f:
            cfg = json.load(f)
        self.cfg = cfg
        self.train_families = list(cfg["train_families"])
        self.gate_families = list(cfg["gate_families"])
        self.exam_families = list(cfg["exam_families"])
        self.excluded = set(cfg.get("excluded_families") or [])
        self.seed_ranges = {k: tuple(v) for k, v in cfg["seed_ranges"].items()}
        self.labels = dict(cfg.get("family_labels") or {})
        self._canary = list(cfg["canary_set"])
        self._gate = list(gate_panel) if gate_panel else list(cfg["gate_set"])
        self._exam = list(cfg["exam_set"])
        self.listing_per_family = int(cfg.get("train_listing_per_family") or 64)
        self.cache_size = int(cache_size)
        self._cache: dict = {}
        self._bootstrap = open(BOOTSTRAP_PATH).read()
        self._validate(require_package)

    # -- split ledger hygiene -----------------------------------------------------
    def _validate(self, require_package: bool) -> None:
        tr, ga, ex = set(self.train_families), set(self.gate_families), \
            set(self.exam_families)
        if tr & ga or tr & ex or ga & ex:
            raise RuntimeError("reasoning_gym split: family groups overlap: "
                               f"{(tr & ga) | (tr & ex) | (ga & ex)}")
        used = tr | ga | ex
        bad = [f for f in used if f in self.excluded or _CODE_LIKE.search(f)]
        if bad:
            raise RuntimeError(f"reasoning_gym split: code-like/excluded "
                               f"families in use: {bad}")
        for k in ("train", "gate", "exam", "canary"):
            if k not in self.seed_ranges:
                raise RuntimeError(f"reasoning_gym split: seed range {k} missing")
        rs = sorted(self.seed_ranges.values())
        for (a0, a1), (b0, b1) in zip(rs, rs[1:]):
            if b0 < a1:
                raise RuntimeError("reasoning_gym split: seed ranges overlap")
        for eid in self._canary:
            fam, sd = parse_id(eid)
            if fam not in tr or not self._in_range(sd, "canary"):
                raise RuntimeError(f"canary item {eid} not a train-family "
                                   f"item in the canary seed range")
        for eid in self._gate:
            fam, sd = parse_id(eid)
            if fam in ex or fam in tr or not self._in_range(sd, "gate"):
                raise RuntimeError(f"gate item {eid} must come from a gate "
                                   f"family in the gate seed range")
        for eid in self._exam:
            fam, sd = parse_id(eid)
            if fam not in ex or not self._in_range(sd, "exam"):
                raise RuntimeError(f"exam item {eid} must come from an exam "
                                   f"family in the exam seed range")
        try:
            from reasoning_gym.factory import DATASETS
        except ImportError:
            if require_package:
                raise RuntimeError("pip install reasoning-gym==0.1.25 "
                                   "(python >= 3.10) is required for "
                                   "--gym reasoning_gym")
            return
        missing = [f for f in used if f not in DATASETS]
        if missing:
            raise RuntimeError(f"reasoning_gym: unknown generators {missing}")
        self.package_version = installed_version()

    def _in_range(self, seed: int, split: str) -> bool:
        lo, hi = self.seed_ranges[split]
        return lo <= seed < hi

    def split_of(self, eid: str) -> str | None:
        """Which split an id belongs to by FAMILY and seed range (the ledger
        assertion "no gate/exam id in the life ledger" uses this)."""
        fam, sd = parse_id(eid)
        if fam in self.exam_families:
            return "exam"
        if fam in self.gate_families:
            return "gate"
        if fam in self.train_families:
            return "canary" if self._in_range(sd, "canary") else "train"
        return None

    # -- items ------------------------------------------------------------------------
    def _item(self, family: str, seed: int):
        key = (family, seed)
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        import reasoning_gym
        ds = reasoning_gym.create_dataset(family, seed=seed, size=1)
        entry = ds[0]
        if len(self._cache) >= self.cache_size:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = (ds, entry)
        return ds, entry

    def question(self, eid: str) -> str:
        fam, sd = parse_id(eid)
        return self._item(fam, sd)[1]["question"]

    def reference_answer(self, eid: str):
        """The verifier's reference (None for simulation-verified families).
        NEVER shown to the child; the parent's leak scan may use it."""
        fam, sd = parse_id(eid)
        return self._item(fam, sd)[1]["answer"]

    def label(self, family: str) -> str:
        return self.labels.get(family, family.replace("_", " "))

    # -- protocol: splits -------------------------------------------------------------
    def splits(self) -> list[str]:
        return list(SPLITS)

    def benchmarks(self, split: str) -> list[str]:
        if split == "train":
            lo, _hi = self.seed_ranges["train"]
            return [make_id(f, lo + j) for f in self.train_families
                    for j in range(self.listing_per_family)]
        if split == "gate":
            return list(self._gate)
        if split == "exam":
            return list(self._exam)
        if split == "canary":
            return list(self._canary)
        raise KeyError(f"unknown split {split!r}; splits: {SPLITS}")

    def training_schedule(self, n: int, seed: int) -> list[str]:
        """n train ids: families cycle (balanced), seeds drawn from the train
        seed range by the life's seed; never a gate/exam family."""
        rng = random.Random(seed)
        lo, hi = self.seed_ranges["train"]
        out, seen = [], set()
        i = 0
        while len(out) < n:
            fam = self.train_families[i % len(self.train_families)]
            eid = make_id(fam, rng.randrange(lo, hi))
            i += 1
            if eid in seen:
                continue
            seen.add(eid)
            out.append(eid)
        return out

    def episode_from_id(self, eid: str, budget_ticks: int | None = None) -> Episode:
        fam, sd = parse_id(eid)
        _ds, entry = self._item(fam, sd)
        q = entry["question"].strip()
        goal = (f"{self.label(fam)} puzzle. Submit an answer the verifier "
                f"scores 1.0.\n{q}\nWrite each attempt on one ACT: line; if "
                f"the answer needs several lines, separate them with '{LINE_SEP}'.")
        metric = ("score = the verifier's exact score of an attempt, in [0, 1] "
                  "(1.0 = accepted; some puzzles give partial credit). The "
                  "episode's score is your best attempt. The verifier never "
                  "shows the answer.")
        intro = (f"New puzzle ({self.label(fam)}). I should read the rules, "
                 f"form an expectation, attempt, and learn from the score.")
        return Episode(eid=eid, goal=goal, metric=metric, intro=intro,
                       family=fam, budget_ticks=budget_ticks)

    def make_episode(self, split: str, rng: random.Random,
                     budget_ticks: int | None = None) -> Episode:
        if split == "train":
            lo, hi = self.seed_ranges["train"]
            fam = rng.choice(self.train_families)
            return self.episode_from_id(make_id(fam, rng.randrange(lo, hi)),
                                        budget_ticks)
        pool = self.benchmarks(split)
        return self.episode_from_id(rng.choice(pool), budget_ticks)

    # -- protocol: acting -------------------------------------------------------------
    def step(self, episode: Episode, action_text: str) -> Observation:
        fam, sd = parse_id(episode.eid)
        ds, entry = self._item(fam, sd)
        answer = decode_answer(action_text)
        episode.n_attempts += 1
        n = episode.n_attempts
        if not answer:
            return Observation(text=f"INVALID: attempt {n} was empty", score=0.0)
        try:
            score = float(ds.score_answer(answer=answer, entry=entry))
        except Exception as error:
            if self.strict_verifier:
                raise RuntimeError("reasoning verifier failed; no measured outcome recorded") from error
            score = 0.0
        if self.strict_verifier and not 0.0 <= score <= 1.0:
            raise RuntimeError("reasoning verifier returned an invalid score")
        if score != score:          # NaN guard
            score = 0.0
        score = min(1.0, max(0.0, score))
        if score > episode.best_score:
            episode.best_score = score
        if score >= 1.0:
            q = "accepted"
        elif score > 0.0:
            q = "not accepted; partial credit"
        else:
            q = "not accepted"
        return Observation(text=f"attempt {n}: verifier score {score:.2f} ({q})",
                           score=score, harness_done=False)

    def evaluate(self, episode: Episode, action_text: str | None = None):
        if action_text is None:
            return float(episode.best_score)
        obs = self.step(episode, action_text)
        return obs.score, obs.text

    # -- protocol: sets and texts -----------------------------------------------------
    def canary_set(self) -> list[str]:
        return list(self._canary)

    def gate_set(self) -> list[str] | None:
        return list(self._gate)

    def exam_set(self) -> list[str]:
        return list(self._exam)

    def birth_prompt(self) -> str:
        return self._bootstrap

    def exposure_domain(self) -> str:
        return "reasoning_gym:" + ",".join(self.train_families)

    def leak_terms(self) -> list[str]:
        """Held-out family names and labels: the parent must never name the
        exam or gate families."""
        out = []
        for f in self.gate_families + self.exam_families:
            out.append(f)
            if self.label(f).lower() != f:
                out.append(self.label(f))
        return out

    def answer_terms(self, episode: Episode) -> list[str]:
        a = self.reference_answer(episode.eid)
        return [str(a)] if a is not None else []

    def headroom_ceiling(self, episode: Episode) -> float | None:
        return 1.0

    def family_of(self, eid: str) -> str | None:
        try:
            return parse_id(eid)[0]
        except ValueError:
            return None

    def offers_end_token(self) -> bool:
        return False

    def compile_vocab(self) -> dict:
        """Target-blind nouns for the sleep compiler: no program, pass,
        optimization or compiler vocabulary reaches the corpus or the
        THINK prompts (tests/test_reflection.py::test_reasoning_gym_compile_is_target_blind)."""
        return dict(noun="Puzzle", plural="puzzles", did="you worked on",
                    action_slot="attempt choice", id_tag="puzzles",
                    domain="solving these puzzles",
                    win_question="which attempt scores best?")

    # -- instruments ------------------------------------------------------------------
    def family_accuracy(self, results: dict) -> dict:
        """{family: mean best score} over a probe's {eid: best_score}."""
        by: dict = {}
        for eid, s in results.items():
            fam = self.family_of(eid)
            if fam:
                by.setdefault(fam, []).append(float(s))
        return {f: round(statistics.mean(v), 4) for f, v in sorted(by.items())}

    def measure_prompt_sizes(self, n_per_family: int = 3,
                             families: list[str] | None = None) -> dict:
        """Mean/max characters of the GOAL text per family (the part of the
        head that grows with the puzzle) and a rough token estimate (chars/4)."""
        fams = families or (self.train_families + self.gate_families
                            + self.exam_families)
        lo, _ = self.seed_ranges["train"]
        out = {}
        for f in fams:
            sizes = [len(self.episode_from_id(make_id(f, lo + 7 * j)).goal)
                     for j in range(n_per_family)]
            out[f] = dict(mean_chars=round(statistics.mean(sizes)),
                          max_chars=max(sizes),
                          est_tokens=round(statistics.mean(sizes) / 4))
        return out
