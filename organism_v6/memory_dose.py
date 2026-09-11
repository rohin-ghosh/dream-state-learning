"""Memory dose-response ("car") test -- Astra memo 2 (2026-09-10), section 2.

DISPOSABLE MECHANISM TEST. Every fact here is SYNTHETIC, researcher-planted
memory (nonce owners, nonce tools, scripted child targets). Every file this
module writes carries synthetic=true. Nothing produced here may be merged
into a taught lineage or described as autonomous consolidation.

What it measures (memo section 1): the adapter-induced conditional
log-odds interaction
    I_d = [ON-OFF log-odds(a vs b | appropriate cue)]
        - [ON-OFF log-odds(a vs b | matched non-trigger cue)]
where a is the planted answer, b its strongest alternative under the frozen
model, d the exposure count. Both terms are reported, never only the
difference.

Pipeline (one run directory; nothing is written outside it):
  generate    three randomized fact banks (64 nonce owners, 16 per dose
              {0,1,4,16}, colours balanced within dose, assigned AFTER the
              frozen model's OFF distribution is measured and stored), a
              companion bank of 16 counterbalanced conditional lessons, the
              two exposure arms (within-session vs across-sleep; matched
              total exposure and last-exposure time), two interference
              sleeps, the filler generator and the fixed distractor block.
  corpus      one sleep's cumulative training corpus for a writer cell:
              writer semantics {dedup (today's), occurrences,
              dedup_weighted (multiplicity weight in the loss)} x
              representation {short (today's one-line header piece),
              antecedent (observation as zero-loss context, child target as
              the loss, through the chat template), antecedent_bare}, plus
              the scrambled-binding negative control (Dshuf: colours
              permuted per event so no owner keeps a consistent colour,
              lesson mappings reversed in half the events; marginals and
              templates preserved exactly); padded to a fixed token budget
              with balanced unrelated observations; colour marginals
              identical across every condition. Ordering (recorded in
              corpus.json): `chronological` (default; prior-first session
              order, as sleep_compile.compile_sleep + train_adapter.py's
              in-order batches -- so within-session and across-sleep
              histories differ in ORDER and are fitted separately) or
              `content` (content-derived shuffle; identical item sets give
              identical corpora by construction; sensitivity arm).
  train       minimal LoRA trainer mirroring organism_v6/train_adapter.py's
              frozen v1 config (rank 8, alpha 2r, dropout 0.05,
              q/k/v/o/gate/up/down, lr 1e-4, 3 epochs, bsz 4, max_len 512,
              cumulative from the frozen base) with per-token label masks
              (joint tokenization of context + target, boundary by offsets)
              and per-item multiplicity weights; logs 100-step throughput.
  evaluate    batched teacher-forced scoring only (no generation): adapter
              ON/OFF x observation in context (before a ~1,024-token
              distractor; adjacent on a subset) / not; three pre-registered
              held-out paraphrases + one exact training-style cue; controls
              (unexposed owners, similar ids, bicycle, swapped ids = the
              partner's own cue re-read for the owner's colour, generic car,
              repaint override, scrambled-binding training); lessons
              (trigger / no-trigger / reversed; complete action strings with
              a termination convention); training-text fit (per-token NLL of
              the A/B and C/D training texts ON vs OFF); adapter strength
              sweep. Raw P, candidate-normalized P and candidate-set mass
              are all stored and reported.
  report      per-arm markdown tables (raw and normalized P, per-bank and
              pooled bootstrap CIs, OFF-prior bins, text-fit vs I_d),
              section 2.4 gates plus a candidate-mass gate, interpretation
              rule (guide / rewrite-habit / nothing / surface-binding-only /
              mass-collapse), banks separately.

  python -m organism_v6.memory_dose generate --run-dir R --seed 0 --model mock|hf
  python -m organism_v6.memory_dose corpus-all --run-dir R
  python -m organism_v6.memory_dose train --run-dir R --corpus C --out A [--rank 8]
  python -m organism_v6.memory_dose evaluate --run-dir R --bank 0 --adapter A --tag T
  python -m organism_v6.memory_dose report --run-dir R
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import random
import re
import sys
import time

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------
SYNTHETIC_NOTE = ("SYNTHETIC researcher-planted memory; disposable mechanism "
                  "test (Astra memo 2, 2026-09-10); never merge into a taught "
                  "lineage; not autonomous consolidation.")
SYNTHETIC_HEADER = ("<!-- synthetic=true: researcher-planted memory; disposable "
                    "mechanism test; never merge into a taught lineage -->")

COLOURS = ["red", "blue", "green", "white"]
DOSES = [0, 1, 4, 16]
OWNERS_PER_DOSE = 16
N_SLEEPS_EXPOSURE = 4          # sleeps 1..4 carry exposure
INTERFERENCE_SLEEPS = [5, 6]   # no new exposure to bank owners
ARMS = ["within", "across"]
WRITERS = ["dedup", "occurrences", "dedup_weighted"]
REPRESENTATIONS = ["short", "antecedent", "antecedent_bare"]
CELLS = {  # Astra's writer factorial (memo 2.3); rank 8 first
    "A": ("dedup", "short", False),
    "B": ("occurrences", "short", False),
    "C": ("dedup", "antecedent", False),
    "D": ("occurrences", "antecedent", False),
    "Dshuf": ("occurrences", "antecedent", True),   # scrambled-binding negative control
    # Bw/Dw: multiplicity weight in the loss. One weight-m item equals m copies
    # only WITHIN a batch (the trainer normalizes per batch and AdamW is not
    # linear across steps); the equivalence is exact for the loss, not the fit.
    "Bw": ("dedup_weighted", "short", False),
    "Dw": ("dedup_weighted", "antecedent", False),
}
ORDERINGS = ["chronological", "content"]
DEFAULT_ORDERING = "chronological"
# pre-registered OFF-prior bins (memo: 'report results by baseline-probability
# bin'); the bin key is the stored pre-assignment OFF prior of the assigned colour
PRIOR_BIN_EDGES = [0.15, 0.35, 0.55]

# LoRA / optimisation config held fixed (memo section 3) -- mirrors the frozen
# v1 trainer organism_v6/train_adapter.py (tests assert the mirror).
LORA_RANK = 8
LORA_ALPHA_MULT = 2            # alpha = 2r: 16 at rank 8, 64 at rank 32
LORA_DROPOUT = 0.05
LORA_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"]
TRAIN_LR = 1e-4
TRAIN_EPOCHS = 3
TRAIN_BSZ = 4
TRAIN_MAX_LEN = 512
LAMBDAS = [0.0, 0.25, 0.5, 1.0]

MODEL_NAME = os.environ.get("V6_MODEL", "Qwen/Qwen2.5-7B-Instruct")
QWEN_SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
IM_END = "<|im_end|>"

ID_LETTERS = "ABCDEFGHJKMNPQRTUVWXYZ"     # no I, L, O (collision-resistant)
ID_DIGITS = "23456789"                    # no 0, 1
OWNER_RE = re.compile(r"\b[A-HJKMNP-Z][2-9][A-HJKMNP-Z][2-9]\b")
TOOL_RE = re.compile(r"\b[A-HJKMNP-Z]{2}-[2-9]\b")

# text templates ------------------------------------------------------------
SITUATIONS = ["In the garage", "In the driveway", "At the car wash",
              "In the parking lot"]
OBS_TMPL = ("Situation: {where}, I inspected owner {owner}'s car.\n"
            "Verified observation: its paint is {colour}.")
OBS_SITUATION_ONLY = "Situation: {where}, I inspected owner {owner}'s car."
TARGET_TMPL = "{owner}'s car is {colour}."
SHORT_HEADER = "Owner {owner}. Q: what colour is the car?\nA: "
EXACT_COMPLETION = "{owner}'s car is"
QUERY_FORMS = {  # pre-registered held-out paraphrases (memo 2.2); no answer in the query
    "p1": "What colour is owner {owner}'s car? Answer with one colour:",
    "p2": "Garage record lookup: {owner}. Car paint:",
    "p3": "For owner {owner}, give the vehicle's colour:",
}
PARAPHRASES = ["p1", "p2", "p3"]
BASE_RATE_FORM = ("Fleet note: about 60% of the cars kept in this garage are "
                  "{base_colour}. What colour is owner {owner}'s car? Answer "
                  "with one colour:")
BICYCLE_FORM = "What colour is owner {owner}'s bicycle? Answer with one colour:"
GENERIC_FORM = "What colour is a car? Answer with one colour:"
REPAINT_OBS = ("Situation: Today I inspected owner {owner}'s car again.\n"
               "Verified observation: it has been repainted; its paint is "
               "now {colour}.")

MODE_PAIRS = [("NORTH", "SOUTH"), ("ALPHA", "BRAVO"), ("DELTA", "ECHO"),
              ("KILO", "ZULU")]
ACTION_PAIRS = [("LATCH", "VENT"), ("PRIME", "PURGE"), ("CLAMP", "SPOOL"),
                ("ARM", "DAMP")]
LESSON_OBS = ("Situation: I operated tool {tool} while its panel showed mode "
              "{mode}.\nVerified observation: pressing {good} worked; pressing "
              "{bad} did not.")
LESSON_TARGET = "With {tool} in mode {mode}, I press {good}."
LESSON_SHORT_HEADER = "Tool {tool}, mode {mode}. Q: which control works?\nA: "
LESSON_SITUATION_ONLY = "Situation: I operated tool {tool} while its panel showed mode {mode}."
LESSON_EXACT = "With {tool} in mode {mode}, I press"
LESSON_QUERY = ("You are operating tool {tool} and its panel shows mode {mode}. "
                "Which control do you press? Answer with the control name only:")
LESSON_QUERY_NOTRIGGER = ("You are operating tool {tool}; its panel is dark and "
                          "shows no mode. Which control do you press? Answer "
                          "with the control name only:")

FILLER_COLOUR = [  # (observation, child target, short header, subject noun)
    ("Situation: In the supply room, I checked crate {fid}.\nVerified observation: its lid is {colour}.",
     "Crate {fid}'s lid is {colour}.", "Crate {fid}. Q: what colour is the lid?\nA: "),
    ("Situation: On the loading dock, I tagged container {fid}.\nVerified observation: its door is {colour}.",
     "Container {fid}'s door is {colour}.", "Container {fid}. Q: what colour is the door?\nA: "),
    ("Situation: In the storeroom, I sorted bin {fid}.\nVerified observation: its label is {colour}.",
     "Bin {fid}'s label is {colour}.", "Bin {fid}. Q: what colour is the label?\nA: "),
    ("Situation: At the depot, I logged pallet {fid}.\nVerified observation: its wrap is {colour}.",
     "Pallet {fid}'s wrap is {colour}.", "Pallet {fid}. Q: what colour is the wrap?\nA: "),
]
FILLER_PLAIN = [
    ("Situation: At the depot, I weighed parcel {fid}.\nVerified observation: it weighs {n} kg.",
     "Parcel {fid} weighs {n} kg.", "Parcel {fid}. Q: what does it weigh?\nA: "),
    ("Situation: In the office, I filed invoice {fid}.\nVerified observation: it lists {n} items.",
     "Invoice {fid} lists {n} items.", "Invoice {fid}. Q: how many items does it list?\nA: "),
    ("Situation: In the yard, I measured pipe {fid}.\nVerified observation: it is {n} cm long.",
     "Pipe {fid} is {n} cm long.", "Pipe {fid}. Q: how long is it?\nA: "),
    ("Situation: In the workshop, I counted the screws in box {fid}.\nVerified observation: it holds {n} screws.",
     "Box {fid} holds {n} screws.", "Box {fid}. Q: how many screws does it hold?\nA: "),
    ("Situation: At the gate, I read meter {fid}.\nVerified observation: it shows {n} units.",
     "Meter {fid} shows {n} units.", "Meter {fid}. Q: what does it show?\nA: "),
    ("Situation: In the archive, I opened folder {fid}.\nVerified observation: it contains {n} pages.",
     "Folder {fid} contains {n} pages.", "Folder {fid}. Q: how many pages does it contain?\nA: "),
]
DISTRACTOR_SENTENCES = [
    "The delivery schedule for the coming week lists {n} inbound shipments, most of them arriving before noon.",
    "Staff are reminded that the loading dock closes at {n}:30 on weekdays and that keys must be returned to the office.",
    "The quarterly maintenance review noted {n} open tickets, of which the majority concern lighting and ventilation.",
    "Visitors sign in at the front desk, collect a badge, and are escorted to the meeting rooms on the second floor.",
    "The inventory count will be repeated next month to reconcile the {n} discrepancies found in the storage aisles.",
    "Procurement requested three quotes for replacement shelving and expects a decision within {n} working days.",
    "The safety briefing covers spill response, fire exits, and the location of the {n} first-aid stations on site.",
    "Timesheets are due on Friday; late submissions are processed in the following pay period without exception.",
    "The new labelling procedure assigns a numeric code to every shelf so that audits can be completed in {n} hours.",
    "A short survey about the canteen menu will be circulated and closes after {n} days.",
    "Forklift operators must complete the refresher module before the certification lapses at the end of the month.",
    "The archive room is being reorganised; folders from the {n} oldest cabinets move to the basement store.",
]

# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------
_WRITE_ROOT: str | None = None


def set_write_root(run_dir: str) -> str:
    """All outputs of this module must live under run_dir (tests assert it)."""
    global _WRITE_ROOT
    _WRITE_ROOT = os.path.realpath(os.path.expanduser(run_dir))
    os.makedirs(_WRITE_ROOT, exist_ok=True)
    return _WRITE_ROOT


def _check_inside(path: str) -> str:
    p = os.path.realpath(os.path.expanduser(path))
    if _WRITE_ROOT is not None and not (p == _WRITE_ROOT or p.startswith(_WRITE_ROOT + os.sep)):
        raise PermissionError(f"refusing to write outside the run directory: {path}")
    return p


def write_json(path: str, obj: dict) -> str:
    """Atomic JSON write; every file carries synthetic=true (hard rule)."""
    p = _check_inside(path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    obj = dict(obj)
    obj["synthetic"] = True
    obj.setdefault("synthetic_note", SYNTHETIC_NOTE)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=False)
    os.replace(tmp, p)
    return p


def write_text(path: str, text: str) -> str:
    p = _check_inside(path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        f.write(SYNTHETIC_HEADER + "\n" + text)
    os.replace(tmp, p)
    return p


def read_json(path: str) -> dict:
    with open(os.path.expanduser(path)) as f:
        return json.load(f)


def sha_of(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


def _rng(*parts) -> random.Random:
    """Deterministic RNG from a string key (independent of Python's hash seed)."""
    key = ":".join(str(p) for p in parts)
    return random.Random(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))


def _mean(xs) -> float:
    xs = [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return sum(xs) / len(xs) if xs else float("nan")


def render_chat(user: str, assistant_prefix: str = "", tokenizer=None) -> str:
    """The deployed chat template (Qwen2.5-Instruct, default system prompt).
    Uses the tokenizer's template when one is given; the literal fallback is
    byte-identical for single-turn user messages (checked on the node by
    `evaluate`, recorded in the eval JSON as template_check)."""
    if tokenizer is not None:
        try:
            p = tokenizer.apply_chat_template(
                [{"role": "user", "content": user}], tokenize=False,
                add_generation_prompt=True)
            return p + assistant_prefix
        except Exception:  # noqa: BLE001 -- jinja2 missing etc.: fall back
            pass
    return (f"<|im_start|>system\n{QWEN_SYSTEM}{IM_END}\n"
            f"<|im_start|>user\n{user}{IM_END}\n"
            f"<|im_start|>assistant\n{assistant_prefix}")


class TokenCounter:
    """Token counting for budgets. mode='hf' uses the deployed tokenizer
    (node); mode='approx' is a deterministic stand-in for CPU tests
    (ids tokenize per character in Qwen's vocabulary, words ~1 token)."""

    def __init__(self, mode: str = "approx", model_name: str = MODEL_NAME):
        self.mode = mode
        self.tok = None
        if mode == "hf":
            from transformers import AutoTokenizer
            self.tok = AutoTokenizer.from_pretrained(model_name)

    def count(self, text: str) -> int:
        if self.tok is not None:
            return len(self.tok(text, add_special_tokens=False).input_ids)
        n = 0
        for w in text.replace("\n", " \n ").split(" "):
            if not w:
                continue
            if w == "\n":
                n += 1
            elif any(ch.isdigit() for ch in w) or w.startswith("<|"):
                n += len(w) if not w.startswith("<|") else 1
            else:
                n += 1 + sum(1 for ch in w if ch in ".,;:'!?()-")
        return n


# ---------------------------------------------------------------------------
# nonce identifiers
# ---------------------------------------------------------------------------
def _owner_id(rng: random.Random) -> str:
    return (rng.choice(ID_LETTERS) + rng.choice(ID_DIGITS)
            + rng.choice(ID_LETTERS) + rng.choice(ID_DIGITS))


def make_owner_ids(rng: random.Random, n: int, taken: set) -> list[str]:
    out = []
    while len(out) < n:
        oid = _owner_id(rng)
        if oid not in taken:
            taken.add(oid)
            out.append(oid)
    return out


def similar_id(rng: random.Random, oid: str, taken: set) -> str:
    """An unseen identifier one character away from oid (memo control:
    'unseen owners with similar identifiers')."""
    for _ in range(1000):
        pos = rng.randrange(4)
        pool = ID_LETTERS if pos % 2 == 0 else ID_DIGITS
        ch = rng.choice([c for c in pool if c != oid[pos]])
        cand = oid[:pos] + ch + oid[pos + 1:]
        if cand not in taken:
            taken.add(cand)
            return cand
    raise RuntimeError("could not build a similar id")


def make_tool_ids(rng: random.Random, n: int, taken: set) -> list[str]:
    out = []
    while len(out) < n:
        t = rng.choice(ID_LETTERS) + rng.choice(ID_LETTERS) + "-" + rng.choice(ID_DIGITS)
        if t not in taken:
            taken.add(t)
            out.append(t)
    return out


# ---------------------------------------------------------------------------
# exposure schedule (memo table): matched totals and last-exposure time
# ---------------------------------------------------------------------------
def schedule_sessions(dose: int, arm: str) -> list[int]:
    """Session index (1..4) of each of the `dose` observations.
    within: all before sleep 4. across: one per sleep (dose 4), four per
    sleep (dose 16), dose 1 before sleep 4; both arms end at session 4."""
    if dose <= 0:
        return []
    if arm == "within":
        return [N_SLEEPS_EXPOSURE] * dose
    if arm != "across":
        raise ValueError(arm)
    if dose <= N_SLEEPS_EXPOSURE:
        return [N_SLEEPS_EXPOSURE - dose + 1 + k for k in range(dose)]
    per = dose // N_SLEEPS_EXPOSURE
    sessions = [1 + k // per for k in range(per * N_SLEEPS_EXPOSURE)]
    sessions += [N_SLEEPS_EXPOSURE] * (dose - len(sessions))
    return sessions


# ---------------------------------------------------------------------------
# filler (balanced unrelated observations), deterministic by (seed, kind, idx)
# ---------------------------------------------------------------------------
def filler_item(seed: int, colour: str | None, idx: int) -> dict:
    rng = _rng("filler", seed, colour or "plain", idx)
    fid = str(rng.randint(10000, 99999))
    if colour is None:
        obs, tgt, hdr = FILLER_PLAIN[idx % len(FILLER_PLAIN)]
        n = rng.randint(2, 480)
        return dict(kind="filler", owner=None, colour=None,
                    observation=obs.format(fid=fid, n=n),
                    target=tgt.format(fid=fid, n=n),
                    short_header=hdr.format(fid=fid), event_ids=[f"fill-p-{idx}"])
    obs, tgt, hdr = FILLER_COLOUR[idx % len(FILLER_COLOUR)]
    return dict(kind="filler_colour", owner=None, colour=colour,
                observation=obs.format(fid=fid, colour=colour),
                target=tgt.format(fid=fid, colour=colour),
                short_header=hdr.format(fid=fid), event_ids=[f"fill-{colour}-{idx}"])


def make_distractor(counter: TokenCounter, target_tokens: int = 1024, seed: int = 0) -> str:
    """Fixed unrelated block (~1,024 tokens): no colours, no ids, no cars."""
    rng = _rng("distractor", seed)
    parts, total = [], 0
    i = 0
    while total < target_tokens:
        s = DISTRACTOR_SENTENCES[i % len(DISTRACTOR_SENTENCES)].format(n=rng.randint(2, 40))
        parts.append(s)
        total += counter.count(s + " ")
        i += 1
    return "Unrelated notes from the site log:\n" + " ".join(parts)


# ---------------------------------------------------------------------------
# bank generation
# ---------------------------------------------------------------------------
def _balanced_assignment(ids: list[str], forbid: dict, rng: random.Random):
    """Colours balanced (|ids|/4 each) honouring per-owner forbidden colours;
    None when the random order gets stuck (caller retries)."""
    cap = {c: len(ids) // len(COLOURS) for c in COLOURS}
    order = list(ids)
    rng.shuffle(order)
    order.sort(key=lambda o: len([c for c in COLOURS if c not in forbid.get(o, set())]))
    out = {}
    for o in order:
        allowed = [c for c in COLOURS if c not in forbid.get(o, set()) and cap[c] > 0]
        if not allowed:
            return None
        c = rng.choice(allowed)
        cap[c] -= 1
        out[o] = c
    return out


def assign_colours(owners_by_dose: dict, prior: dict, forbid: dict,
                   rng: random.Random, n_candidates: int = 200,
                   prior_match: bool = False) -> dict:
    """Colour assignment made AFTER the OFF measurement (which is stored):
    plain RANDOM balanced assignment within each dose, counterbalanced across
    banks (forbid). Prior imbalance is handled the memo's way -- reported by
    OFF-prior bin -- not by optimising the assignment. prior_match=True is an
    opt-in departure from randomisation (recorded in manifest.json and the
    report header): among random balanced candidates keep the one whose mean
    OFF prior of the assigned colour is closest to 1/4."""
    result = {}
    for dose, ids in owners_by_dose.items():
        best = None
        for _ in range(n_candidates if prior_match else 200):
            cand = _balanced_assignment(ids, forbid, rng)
            if cand is None:
                continue
            if not prior_match:
                best = (0.0, cand)
                break
            mp = _mean([prior[o][cand[o]] for o in ids]) if prior else 0.25
            score = abs(mp - 1.0 / len(COLOURS))
            if best is None or score < best[0]:
                best = (score, cand)
        if best is None:
            raise RuntimeError(f"no balanced assignment for dose {dose}")
        result.update(best[1])
    return result


def measure_off(scorer, owner_ids: list[str], base_colour: str = "red") -> dict:
    """Frozen-model OFF distribution per owner and query form (stored in the
    bank before any assignment). Returns {owner: {form: {p_raw, p_norm,
    mass}}} plus the generic cue under key '_generic'."""
    prompts, keys = [], []
    forms = dict(QUERY_FORMS)
    forms["base_rate"] = BASE_RATE_FORM
    for o in owner_ids:
        for name, tmpl in forms.items():
            prompts.append(render_chat(tmpl.format(owner=o, base_colour=base_colour),
                                       tokenizer=getattr(scorer, "tok", None)))
            keys.append((o, name))
        prompts.append(render_chat(OBS_SITUATION_ONLY.format(where=SITUATIONS[0], owner=o),
                                   EXACT_COMPLETION.format(owner=o),
                                   tokenizer=getattr(scorer, "tok", None)))
        keys.append((o, "completion"))
    prompts.append(render_chat(GENERIC_FORM, tokenizer=getattr(scorer, "tok", None)))
    keys.append(("_generic", "generic"))
    cands = [colour_candidates(leading_space=(k[1] == "completion")) for k in keys]
    lps = scorer.candidate_logprobs(prompts, [sum(c.values(), []) for c in cands])
    out: dict = {}
    for (o, name), cset, lp in zip(keys, cands, lps):
        out.setdefault(o, {})[name] = colour_probs(cset, lp)
    return out


def colour_candidates(leading_space: bool) -> dict:
    """Surface variants per colour scored at the response start (single
    tokens in Qwen's vocabulary in every casing/spacing variant)."""
    sp = " " if leading_space else ""
    return {c: [sp + c, sp + c.capitalize()] for c in COLOURS}


def colour_probs(cset: dict, logprobs: list[float]) -> dict:
    """Raw P(colour) = sum over its surface variants; normalized over the
    four colours; candidate-set mass."""
    raw, logp, i = {}, {}, 0
    for c, variants in cset.items():
        lps = logprobs[i:i + len(variants)]
        raw[c] = sum(math.exp(lp) for lp in lps)
        logp[c] = _logsumexp(lps)
        i += len(variants)
    mass = sum(raw.values())
    norm = {c: (raw[c] / mass if mass > 0 else 1.0 / len(COLOURS)) for c in COLOURS}
    return dict(p_raw=raw, p_norm=norm, mass=mass, logp=logp)


def _logsumexp(xs: list[float]) -> float:
    if not xs:
        return float("-inf")
    m = max(xs)
    return m + math.log(sum(math.exp(x - m) for x in xs))


def generate_lessons(bank: int, seed: int, taken: set) -> tuple[list[dict], list[dict]]:
    """16 conditional lessons: nonce tool, action A in mode X, action B in
    mode Y; mode and action pairs from shared pools, mapping direction
    counterbalanced 2/2 within every mode pair and every action pair; four
    lessons per dose; events alternate modes X,Y,X,Y..."""
    rng = _rng("lessons", seed, bank)
    tools = make_tool_ids(rng, 16, taken)
    doses = [d for d in DOSES for _ in range(4)]
    rng.shuffle(doses)
    lessons, events = [], []
    for i in range(16):
        modes = MODE_PAIRS[i % 4]
        acts = ACTION_PAIRS[(i // 4) % 4]
        direction = (i // 4 + i) % 2
        mapping = {modes[0]: acts[direction], modes[1]: acts[1 - direction]}
        les = dict(lesson_id=f"b{bank}-L{i:02d}", tool=tools[i], modes=list(modes),
                   actions=list(acts), mapping=mapping, direction=direction,
                   dose=doses[i])
        lessons.append(les)
        for k in range(doses[i]):
            mode = modes[k % 2]
            good, bad = mapping[mode], mapping[modes[1 - k % 2]]
            events.append(dict(
                event_id=f"b{bank}-{tools[i]}-e{k:02d}", kind="lesson",
                lesson_id=les["lesson_id"], tool=tools[i], mode=mode,
                colour=None, owner=None, k=k,
                observation=LESSON_OBS.format(tool=tools[i], mode=mode, good=good, bad=bad),
                target=LESSON_TARGET.format(tool=tools[i], mode=mode, good=good),
                short_header=LESSON_SHORT_HEADER.format(tool=tools[i], mode=mode)))
    return lessons, events


def generate_bank(bank: int, seed: int, owner_ids: list[str], off: dict,
                  forbid: dict, taken: set, n_interference: int = 32,
                  vary_situations: bool = False, base_colour: str = "red",
                  prior_match: bool = False) -> dict:
    """One randomized fact bank. `off` is the stored frozen-model
    distribution measured BEFORE this call; `forbid` carries the colours the
    same owner received in earlier banks (counterbalancing)."""
    rng = _rng("bank", seed, bank)
    owners = list(owner_ids)
    rng.shuffle(owners)
    by_dose = {d: owners[i * OWNERS_PER_DOSE:(i + 1) * OWNERS_PER_DOSE]
               for i, d in enumerate(DOSES)}
    prior = {o: {c: _mean([off[o][f]["p_norm"][c] for f in PARAPHRASES]) for c in COLOURS}
             for o in owners} if off else {}
    colour = assign_colours(by_dose, prior, forbid, rng, prior_match=prior_match)
    dose_of = {o: d for d, ids in by_dose.items() for o in ids}
    sim = {o: similar_id(rng, o, taken) for o in owners}
    # swapped-id partner: same dose, different colour, deterministic
    partner = {}
    for d, ids in by_dose.items():
        for o in ids:
            others = [p for p in ids if colour[p] != colour[o]]
            partner[o] = others[(ids.index(o)) % len(others)] if others else None
    events = []
    for o in owners:
        for k in range(dose_of[o]):
            where = SITUATIONS[k % len(SITUATIONS)] if vary_situations else SITUATIONS[0]
            events.append(dict(
                event_id=f"b{bank}-{o}-e{k:02d}", kind="fact", owner=o,
                colour=colour[o], k=k,
                observation=OBS_TMPL.format(where=where, owner=o, colour=colour[o]),
                target=TARGET_TMPL.format(owner=o, colour=colour[o]),
                short_header=SHORT_HEADER.format(owner=o)))
    # interference owners: new ids, dose 4 each, colours balanced, sessions 5/6
    interference = dict(owners=[], events=[])
    for s in INTERFERENCE_SLEEPS:
        ids = make_owner_ids(rng, n_interference, taken)
        cols = [COLOURS[i % len(COLOURS)] for i in range(n_interference)]
        rng.shuffle(cols)
        for o, c in zip(ids, cols):
            interference["owners"].append(dict(id=o, colour=c, dose=4, session=s))
            for k in range(4):
                interference["events"].append(dict(
                    event_id=f"b{bank}-{o}-i{k:02d}", kind="interference", owner=o,
                    colour=c, k=k, session=s,
                    observation=OBS_TMPL.format(where=SITUATIONS[0], owner=o, colour=c),
                    target=TARGET_TMPL.format(owner=o, colour=c),
                    short_header=SHORT_HEADER.format(owner=o)))
    lessons, lesson_events = generate_lessons(bank, seed, taken)
    schedule = {}
    for arm in ARMS:
        sched = {}
        for o in owners:
            for ev, s in zip([e for e in events if e["owner"] == o],
                             schedule_sessions(dose_of[o], arm)):
                sched[ev["event_id"]] = s
        for les in lessons:
            evs = [e for e in lesson_events if e["lesson_id"] == les["lesson_id"]]
            for ev, s in zip(evs, schedule_sessions(les["dose"], arm)):
                sched[ev["event_id"]] = s
        for ev in interference["events"]:
            sched[ev["event_id"]] = ev["session"]
        schedule[arm] = sched
    # colour marginal target: the maximum colour-c target count any condition
    # can reach (occurrence-preserving, sleep 6) -- identical for every corpus
    per_colour = {c: 0 for c in COLOURS}
    for e in events + interference["events"]:
        per_colour[e["colour"]] += 1
    marginal_target = max(per_colour.values())
    # pre-registered calibration subset: OFF normalized P(assigned) in [0.55, 0.65]
    prior_subset = []
    for o in owners:
        for f in PARAPHRASES:
            p = off[o][f]["p_norm"][colour[o]] if off else None
            if p is not None and 0.55 <= p <= 0.65:
                prior_subset.append(dict(owner=o, form=f, p_off=p))
    return dict(
        bank=bank, seed=seed, base_colour=base_colour,
        owners=[dict(id=o, dose=dose_of[o], colour=colour[o], similar_id=sim[o],
                     partner=partner[o],
                     prior_assigned=(prior[o][colour[o]] if prior else None))
                for o in owners],
        off=off, events=events, lessons=lessons, lesson_events=lesson_events,
        interference=interference, schedule=schedule,
        marginal_target=marginal_target, prior_subset=prior_subset,
        assignment_after_off_measurement=bool(off), prior_match=prior_match,
        prior_bin_edges=list(PRIOR_BIN_EDGES),
        vary_situations=vary_situations, n_interference_per_sleep=n_interference)


def generate_run(run_dir: str, seed: int, scorer, counter: TokenCounter,
                 n_banks: int = 3, shared_owners: bool = True,
                 token_budget: int = 65536, n_interference: int = 32,
                 vary_situations: bool = False, base_colour: str = "red",
                 distractor_tokens: int = 1024, prior_match: bool = False) -> dict:
    """Banks, lessons, schedule, distractor and manifest. The OFF measurement
    happens first; assignment second (random balanced unless prior_match);
    both are stored."""
    root = set_write_root(run_dir)
    taken: set = set()
    rng = _rng("owners", seed)
    pools = []
    shared = make_owner_ids(rng, OWNERS_PER_DOSE * len(DOSES), taken) if shared_owners else None
    for b in range(n_banks):
        pools.append(shared if shared_owners else make_owner_ids(
            _rng("owners", seed, b), OWNERS_PER_DOSE * len(DOSES), taken))
    all_ids = sorted({o for p in pools for o in p})
    t0 = time.time()
    off = measure_off(scorer, all_ids, base_colour=base_colour)
    off_seconds = time.time() - t0
    forbid: dict = {}
    banks = []
    for b in range(n_banks):
        bank = generate_bank(b, seed, pools[b], {o: off[o] for o in pools[b]},
                             forbid, taken, n_interference=n_interference,
                             vary_situations=vary_situations, base_colour=base_colour,
                             prior_match=prior_match)
        bank["off_generic"] = off["_generic"]["generic"]
        for o in bank["owners"]:
            forbid.setdefault(o["id"], set()).add(o["colour"])
        write_json(os.path.join(root, "banks", f"bank{b}.json"), bank)
        banks.append(bank)
    distractor = make_distractor(counter, distractor_tokens, seed)
    write_json(os.path.join(root, "distractor.json"),
               dict(text=distractor, tokens=counter.count(distractor),
                    counter=counter.mode))
    manifest = dict(
        seed=seed, n_banks=n_banks, shared_owners=shared_owners,
        token_budget=token_budget, counter=counter.mode, model=MODEL_NAME,
        scorer=type(scorer).__name__, off_measurement_seconds=round(off_seconds, 1),
        doses=DOSES, owners_per_dose=OWNERS_PER_DOSE, colours=COLOURS,
        arms=ARMS, interference_sleeps=INTERFERENCE_SLEEPS,
        n_interference_per_sleep=n_interference, cells=CELLS,
        lora=dict(rank=LORA_RANK, alpha_mult=LORA_ALPHA_MULT, dropout=LORA_DROPOUT,
                  targets=LORA_TARGETS, lr=TRAIN_LR, epochs=TRAIN_EPOCHS,
                  bsz=TRAIN_BSZ, max_len=TRAIN_MAX_LEN),
        query_forms=QUERY_FORMS, base_rate_form=BASE_RATE_FORM,
        base_colour=base_colour, prior_match=prior_match,
        assignment=("prior-matched balanced (opt-in)" if prior_match
                    else "random balanced, after the OFF measurement"),
        prior_bin_edges=list(PRIOR_BIN_EDGES), default_ordering=DEFAULT_ORDERING,
        created=time.strftime("%Y-%m-%d %H:%M:%S"))
    write_json(os.path.join(root, "manifest.json"), manifest)
    return dict(manifest=manifest, banks=banks)

# ---------------------------------------------------------------------------
# corpus: writer semantics x representation (+ shuffled control), padding
# ---------------------------------------------------------------------------
def dedup_key(text: str) -> str:
    """Today's exact-dedup key (organism_v6.sleep_compile.dedup): whitespace-
    normalized, lower-cased, first 160 characters of the PIECE text."""
    return re.sub(r"\s+", " ", text.lower())[:160]


def _order_key(seed: int, bank: int, event_id: str) -> float:
    """Deterministic within-session position of an event (stand-in for the
    ledger's time order: observations of different owners interleave).
    Independent of arm and sleep, so events sharing a session sit in the
    same relative order in every corpus."""
    return _rng("order", seed, bank, event_id).random()


def ledger_items(bank: dict, arm: str, sleep: int) -> list[dict]:
    """Every event (facts, lessons, interference) ingested by `sleep` under
    the writer's cumulative replay policy (all history to date), each tagged
    with its session and returned in CHRONOLOGICAL order (session, then the
    deterministic within-session key) -- the order compile_sleep's prior-
    first cumulative corpus gives them."""
    sched = bank["schedule"][arm]
    evs = bank["events"] + bank["lesson_events"] + bank["interference"]["events"]
    out = []
    for e in evs:
        s = sched.get(e["event_id"], 10 ** 6)
        if s <= sleep:
            e2 = dict(e)
            e2["session"] = s
            e2["order_key"] = _order_key(bank["seed"], bank["bank"], e["event_id"])
            out.append(e2)
    out.sort(key=lambda e: (e["session"], e["order_key"]))
    return out


def _piece(ev: dict, representation: str) -> dict:
    """Render one event under a representation.
    short:            today's piece -- one-line header + child target, bare
                      text, loss on every token (train_adapter.py semantics).
    antecedent:       observation as the user turn (zero loss), child target
                      as the assistant turn (loss + EOS), chat template.
    antecedent_bare:  observation then target as bare text, loss on target."""
    if representation == "short":
        ctx, chat, mask = ev["short_header"], False, False
    elif representation == "antecedent":
        ctx, chat, mask = ev["observation"], True, True
    elif representation == "antecedent_bare":
        ctx, chat, mask = ev["observation"] + "\n", False, True
    else:
        raise ValueError(representation)
    return dict(context=ctx, target=ev["target"], chat=chat, mask_context=mask,
                weight=1.0, kind=ev["kind"], owner=ev.get("owner"),
                colour=ev.get("colour"), tool=ev.get("tool"), mode=ev.get("mode"),
                lesson_id=ev.get("lesson_id"), event_ids=[ev["event_id"]],
                n_occurrences=1, context_owner=ev.get("owner") or ev.get("lesson_id"),
                session=ev.get("session"), order_key=ev.get("order_key"),
                shuffled=bool(ev.get("shuffled", False)))


def apply_writer(pieces: list[dict], writer: str) -> list[dict]:
    """dedup: collapse identical pieces (today's semantics; the count is
    metadata only). occurrences: keep every event. dedup_weighted: collapse,
    multiplicity becomes the item's loss weight."""
    if writer == "occurrences":
        return [dict(p) for p in pieces]
    if writer not in ("dedup", "dedup_weighted"):
        raise ValueError(writer)
    seen: dict = {}
    out = []
    for p in pieces:
        k = dedup_key(p["context"] + p["target"])
        if k in seen:
            q = out[seen[k]]
            q["event_ids"] = q["event_ids"] + p["event_ids"]
            q["n_occurrences"] += 1
            if writer == "dedup_weighted":
                q["weight"] = float(q["n_occurrences"])
        else:
            seen[k] = len(out)
            out.append(dict(p))
    return out


def scrambled_colours(bank: dict) -> dict:
    """The scrambled-binding negative control's colour per fact/interference
    EVENT (deterministic per bank, independent of arm and sleep so the
    cumulative corpora stay prefix-consistent). The supervised target text
    ("{owner}'s car is {colour}.") carries the owner->colour binding itself,
    so permuting contexts alone would leave the binding in the loss (the
    memo's 'preserve target-text frequencies' cannot hold literally). Here
    the binding leaves the loss: every owner with dose >= 4 sees each colour
    equally often (dose/4 each, random order); the dose-1 owners' colours are
    deranged among themselves (no owner keeps its planted colour). Colour-word
    marginals, owner-id frequencies and every template are preserved exactly
    (per colour the count equals marginal_target at sleep 6)."""
    rng = _rng("scramble", bank["seed"], bank["bank"])
    out: dict = {}
    events = bank["events"] + bank["interference"]["events"]
    by_owner: dict = {}
    for e in events:
        by_owner.setdefault(e["owner"], []).append(e)
    singles = []
    for o in sorted(by_owner):
        evs = sorted(by_owner[o], key=lambda e: e["k"])
        d = len(evs)
        if d % len(COLOURS) == 0:
            deal = [c for c in COLOURS for _ in range(d // len(COLOURS))]
            rng.shuffle(deal)
            for e, c in zip(evs, deal):
                out[e["event_id"]] = c
        else:
            singles.extend(evs)
    if singles:
        cols = [e["colour"] for e in singles]
        for _ in range(100000):
            perm = list(cols)
            rng.shuffle(perm)
            if all(p != c for p, c in zip(perm, cols)):
                break
        else:
            raise RuntimeError("no derangement of dose-1 colours found")
        for e, c in zip(singles, perm):
            out[e["event_id"]] = c
    return out


def scrambled_lesson_reversals(bank: dict) -> set:
    """Lesson events whose good/bad actions are swapped in the control:
    exactly half of each lesson's (mode X, mode Y) event pairs, so per
    (tool, mode) the pressed action is A as often as B (dose >= 4) and
    action/mode marginals are preserved exactly; a lone dose-1 event is
    reversed."""
    rng = _rng("scramble-lessons", bank["seed"], bank["bank"])
    rev: set = set()
    by_lesson: dict = {}
    for e in bank["lesson_events"]:
        by_lesson.setdefault(e["lesson_id"], []).append(e)
    for lid in sorted(by_lesson):
        evs = sorted(by_lesson[lid], key=lambda e: e["k"])
        n_pairs = len(evs) // 2
        for j in rng.sample(range(n_pairs), (n_pairs + 1) // 2):
            rev.add(evs[2 * j]["event_id"])
            rev.add(evs[2 * j + 1]["event_id"])
        if len(evs) % 2 == 1:
            rev.add(evs[-1]["event_id"])
    return rev


def scramble_events(bank: dict, events: list[dict]) -> list[dict]:
    """Apply the scrambled-binding control to ledger events: rewrite the
    observation, target and header of every fact/interference event with its
    scrambled colour, and swap good/bad in the reversed lesson events. Event
    ids, sessions and order keys are untouched."""
    cols = scrambled_colours(bank)
    rev = scrambled_lesson_reversals(bank)
    mapping = {les["lesson_id"]: les for les in bank["lessons"]}
    out = []
    for e in events:
        e2 = dict(e)
        if e["kind"] in ("fact", "interference"):
            c = cols[e["event_id"]]
            where = re.match(r"Situation: (.*?), I inspected", e["observation"]).group(1)
            e2.update(colour=c, planted_colour=e["colour"],
                      observation=OBS_TMPL.format(where=where, owner=e["owner"], colour=c),
                      target=TARGET_TMPL.format(owner=e["owner"], colour=c), shuffled=True)
        elif e["kind"] == "lesson":
            les = mapping[e["lesson_id"]]
            good = les["mapping"][e["mode"]]
            bad = [a for a in les["actions"] if a != good][0]
            if e["event_id"] in rev:
                good, bad = bad, good
            e2.update(observation=LESSON_OBS.format(tool=e["tool"], mode=e["mode"], good=good, bad=bad),
                      target=LESSON_TARGET.format(tool=e["tool"], mode=e["mode"], good=good),
                      reversed=e["event_id"] in rev, shuffled=True)
        out.append(e2)
    return out


def render_item(item: dict) -> str:
    if item["chat"]:
        return render_chat(item["context"]) + item["target"] + IM_END
    return item["context"] + item["target"]


def items_sha(items: list[dict]) -> str:
    """Order-insensitive identity of a corpus (the multiset of supervised
    items)."""
    return sha_of(sorted((render_item(it), it["weight"], it["mask_context"]) for it in items))


def build_corpus(bank: dict, arm: str, sleep: int, writer: str,
                 representation: str, counter: TokenCounter,
                 token_budget: int, shuffled: bool = False,
                 epochs: int = TRAIN_EPOCHS, ordering: str = DEFAULT_ORDERING) -> dict:
    """One sleep's corpus for one writer cell, padded to the token budget
    with balanced unrelated observations; colour marginals identical to
    every other corpus of the bank (marginal_target per colour).

    ordering='chronological' (default) reproduces today's pipeline: compile
    _sleep builds the cumulative corpus prior-first (dedup keeps the FIRST
    occurrence) and train_adapter.py trains in corpus order without a
    shuffle, so items sit in (session, ledger-order) blocks; the padding
    observations are interleaved with a fixed pseudo-session each (unrelated
    ledger events spread over the exposure sessions), so the within-session
    and across-sleep arms of sleep 4 hold the SAME item set in a DIFFERENT
    order and are fitted separately. ordering='content' shuffles by a
    content-derived seed, so identical item sets give byte-identical corpora
    (the memo's identity by construction; sensitivity arm)."""
    if ordering not in ORDERINGS:
        raise ValueError(ordering)
    events = ledger_items(bank, arm, sleep)                # chronological
    if shuffled:
        events = scramble_events(bank, events)
    pieces = [_piece(e, representation) for e in events]
    items = apply_writer(pieces, writer)                    # dedup keeps the first occurrence
    # colour marginal top-up (targets per colour == marginal_target everywhere)
    M = bank["marginal_target"]
    counts = {c: sum(1 for it in items if it["colour"] == c) for c in COLOURS}
    fill_seed = bank["seed"] * 100 + bank["bank"]
    for c in COLOURS:
        if counts[c] > M:
            raise RuntimeError(f"colour {c} count {counts[c]} exceeds marginal target {M}")
        for idx in range(M - counts[c]):
            items.append(_piece_from_filler(filler_item(fill_seed, c, idx), representation, fill_seed, bank["bank"]))
    # token budget: colourless filler until the next item would overflow
    n_tokens = sum(counter.count(render_item(it)) for it in items)
    content_tokens = n_tokens
    idx = 0
    while True:
        f = _piece_from_filler(filler_item(fill_seed, None, idx), representation, fill_seed, bank["bank"])
        t = counter.count(render_item(f))
        if n_tokens + t > token_budget:
            break
        items.append(f)
        n_tokens += t
        idx += 1
    order_seed = None
    if ordering == "chronological":
        items.sort(key=lambda it: (it["session"], it["order_key"]))
    else:
        # canonical order first, so the content-seeded shuffle depends on the item set only
        items.sort(key=lambda it: (render_item(it), it["weight"], it["mask_context"]))
        order_seed = sha_of([render_item(it) for it in items])
        _rng("order", order_seed).shuffle(items)
    sha = sha_of([(render_item(it), it["weight"], it["mask_context"]) for it in items])
    by_kind: dict = {}
    for it in items:
        by_kind[it["kind"]] = by_kind.get(it["kind"], 0) + 1
    presentations = {}
    for it in items:
        if it["kind"] in ("fact", "lesson", "interference"):
            key = it["owner"] or it["lesson_id"]
            presentations[key] = presentations.get(key, 0.0) + epochs * it["weight"]
    supervised = sum(counter.count(it["target"]) + (0 if it["mask_context"] else counter.count(it["context"]))
                     for it in items)
    session_blocks: dict = {}
    for it in items:
        if it["kind"] in ("fact", "lesson", "interference"):
            session_blocks[it["session"]] = session_blocks.get(it["session"], 0) + 1
    stats = dict(n_items=len(items), n_tokens=n_tokens, content_tokens=content_tokens,
                 supervised_tokens=supervised, by_kind=by_kind,
                 colour_marginals={c: sum(1 for it in items if it["colour"] == c) for c in COLOURS},
                 n_events=len(events),
                 n_event_ids=len({e for it in items if it["kind"] in ("fact", "lesson", "interference")
                                  for e in it["event_ids"]}),
                 presentations_per_owner=presentations, order_seed=order_seed,
                 ordering=ordering, session_blocks={str(k): v for k, v in sorted(session_blocks.items())},
                 over_budget=content_tokens > token_budget, token_budget=token_budget)
    return dict(corpus=items, bank=bank["bank"], arm=arm, sleep=sleep, writer=writer,
                representation=representation, shuffled=shuffled, sha=sha,
                items_sha=items_sha(items), ordering=ordering,
                token_budget=token_budget, marginal_target=M, epochs=epochs,
                counter=counter.mode, stats=stats)


def _piece_from_filler(f: dict, representation: str, fill_seed: int = 0, bank: int = 0) -> dict:
    """A padding item with a fixed pseudo-session over the exposure sessions
    (deterministic per filler id; independent of arm, cell and sleep), so
    under chronological ordering the unrelated observations interleave with
    the bank events instead of trailing them."""
    ev = dict(f)
    ev["event_id"] = f["event_ids"][0]
    ev["session"] = _rng("fsess", fill_seed, bank, ev["event_id"]).randint(1, N_SLEEPS_EXPOSURE)
    ev["order_key"] = _order_key(fill_seed, bank, ev["event_id"])
    p = _piece(ev, representation)
    p["kind"] = f["kind"]
    return p


def cell_dir(run_dir: str, bank: int, cell: str, arm: str, sleep: int) -> str:
    return os.path.join(run_dir, "corpora", f"bank{bank}", cell, arm, f"sleep{sleep}")


def corpus_all(run_dir: str, counter: TokenCounter, cells: list[str] | None = None,
               arms: list[str] | None = None, sleeps: list[int] | None = None,
               token_budget: int | None = None, ordering: str = DEFAULT_ORDERING,
               strict_budget: bool = True) -> dict:
    """Every corpus of the run + an index (shas, stats) + the sleep-4
    exposure-arm identity check: `identical_items` (same multiset of
    supervised items -- true by construction for every cell) and
    `identical_sha` (same corpus incl. ORDER -- true by construction only
    under ordering='content'; under 'chronological' the arms differ in order
    and the memo's identity prediction is a measured result of two fits).
    Fails (strict_budget) if any corpus's content exceeds the token budget,
    so no condition can silently differ in size."""
    root = set_write_root(run_dir)
    manifest = read_json(os.path.join(root, "manifest.json"))
    budget = token_budget or manifest["token_budget"]
    cells = cells or ["A", "B", "C", "D", "Dshuf"]
    arms = arms or ARMS
    sleeps = sleeps or list(range(1, max(INTERFERENCE_SLEEPS) + 1))
    index, over = {}, []
    for b in range(manifest["n_banks"]):
        bank = read_json(os.path.join(root, "banks", f"bank{b}.json"))
        for cell in cells:
            writer, rep, shuf = CELLS[cell]
            for arm in arms:
                for k in sleeps:
                    c = build_corpus(bank, arm, k, writer, rep, counter, budget, shuffled=shuf,
                                     ordering=ordering)
                    d = cell_dir(root, b, cell, arm, k)
                    path = write_json(os.path.join(d, "corpus.json"), c)
                    key = f"bank{b}/{cell}/{arm}/sleep{k}"
                    index[key] = dict(path=path, sha=c["sha"], items_sha=c["items_sha"], **c["stats"])
                    if c["stats"]["over_budget"]:
                        over.append((key, c["stats"]["content_tokens"]))
    identity = []
    for b in range(manifest["n_banks"]):
        for cell in cells:
            w4 = index.get(f"bank{b}/{cell}/within/sleep4")
            a4 = index.get(f"bank{b}/{cell}/across/sleep4")
            if w4 and a4:
                identity.append(dict(bank=b, cell=cell, sleep=4, within=w4["sha"], across=a4["sha"],
                                     identical_items=(w4["items_sha"] == a4["items_sha"]),
                                     identical_sha=(w4["sha"] == a4["sha"]),
                                     identical=(w4["sha"] == a4["sha"])))
    max_content = max((v["content_tokens"] for v in index.values()), default=0)
    write_json(os.path.join(root, "corpora", "index.json"),
               dict(index=index, identity_check=identity, token_budget=budget,
                    max_content_tokens=max_content, over_budget=[k for k, _ in over],
                    ordering=ordering, counter=counter.mode))
    if over and strict_budget:
        raise RuntimeError("corpus content exceeds the token budget (%d): %s" % (
            budget, ", ".join(f"{k}={n}" for k, n in over[:8])))
    return dict(index=index, identity_check=identity, max_content_tokens=max_content,
                over_budget=[k for k, _ in over], ordering=ordering)

# ---------------------------------------------------------------------------
# scorers: batched teacher-forced candidate log-probs (no generation)
# ---------------------------------------------------------------------------
def _canon(cand: str) -> str:
    """Canonical answer key of a candidate string: termination convention
    (IM_END / trailing period) removed, lower-cased; for a full-sentence
    candidate (text-fit probes) the key is its last word."""
    c = cand.strip()
    if c.endswith(IM_END):
        c = c[:-len(IM_END)]
    c = c.strip().lower().rstrip(".")
    return c.split()[-1] if " " in c else c


def _hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))


class MockScorer:
    """Deterministic CPU stand-in. Priors come from a hash of the cue; a mock
    adapter (written by train_mock) adds cue-conditioned strength under one
    of four behaviour profiles used to exercise the interpretation rule:
      guide    owner-bound, car-only, revisable by present context
      habit    over-generalizes to the nearest id / any property, and the
               old memory fights an explicit repaint
      nothing  no effect at all
      surface  fires only on the exact training-style cues
    lam scales the adapter's contribution (lam=0 is exactly OFF)."""

    def __init__(self, adapter: dict | None = None, lam: float = 1.0, seed: int = 0,
                 gain: float = 1.0):
        self.adapter = adapter
        self.lam = lam
        self.seed = seed
        self.gain = gain
        self.tok = None
        self.calls = 0
        self.has_adapter = adapter is not None

    def set_lambda(self, lam: float):
        self.lam = lam

    @contextlib.contextmanager
    def off(self):
        saved = self.lam
        self.lam = 0.0
        try:
            yield
        finally:
            self.lam = saved

    def _user_text(self, prompt: str) -> str:
        m = re.search(r"<\|im_start\|>user\n(.*?)<\|im_end\|>", prompt, re.S)
        return m.group(1) if m else prompt

    def _strength_logits(self, prompt: str, cands: list[str]) -> dict:
        ad = self.adapter
        if not ad or self.lam == 0.0:
            return {}
        profile = ad.get("profile", "guide")
        if profile == "nothing":
            return {}
        user = self._user_text(prompt)
        query = user.rsplit("\n\n", 1)[-1]
        low = query.lower()
        tail = prompt.split("<|im_start|>assistant\n")[-1] if "<|im_start|>assistant\n" in prompt else prompt
        exact = ("q: what colour is the car?" in prompt.lower()
                 or tail.rstrip().endswith("'s car is")
                 or tail.rstrip().endswith("i press"))
        boosts: dict = {}
        ids = OWNER_RE.findall(query) or OWNER_RE.findall(user)
        strength = ad.get("strength", {})
        if ids and strength:
            oid = ids[-1]
            if profile == "habit":
                near = min(strength, key=lambda o: _hamming(o, oid))
                srow = strength.get(near, {})
                for c, s in srow.items():
                    boosts[c] = boosts.get(c, 0.0) + self.gain * math.log1p(s)
            else:
                car = any(k in low for k in ("car", "paint", "vehicle")) and "bicycle" not in low
                if profile == "surface":
                    car = exact
                if car and oid in strength:
                    for c, s in strength[oid].items():
                        boosts[c] = boosts.get(c, 0.0) + self.gain * math.log1p(s)
        tools = TOOL_RE.findall(query) or TOOL_RE.findall(user)
        lessons = ad.get("lessons", {})
        if tools and lessons:
            t = tools[-1]
            if t in lessons:
                for mode, acts in lessons[t].items():
                    present = mode.lower() in low
                    if present or profile == "habit":
                        if profile == "surface" and not exact:
                            continue
                        for a, s in acts.items():
                            boosts[a] = boosts.get(a, 0.0) + self.gain * math.log1p(s) * (1.0 if present else 0.6)
        return {k: self.lam * v for k, v in boosts.items()}

    def candidate_logprobs(self, prompts: list[str], candidates: list[list[str]]) -> list[list[float]]:
        self.calls += 1
        out = []
        for prompt, cands in zip(prompts, candidates):
            user = self._user_text(prompt)
            core = user.rsplit("\n\n", 1)[-1] + "||" + prompt.split("<|im_start|>assistant\n")[-1]
            logits = []
            boosts = self._strength_logits(prompt, cands)
            for cand in cands:
                cc = _canon(cand)
                h = _rng("prior", self.seed, core, cc).random()
                lg = 2.0 * h - 1.0 + (0.25 if cand.strip()[:1].isupper() else 0.0)
                if f"verified observation: its paint is {cc}" in user.lower():
                    lg += 6.0
                if f"its paint is now {cc}" in user.lower():
                    lg += 6.0
                if "repainted" in user.lower() and (self.adapter or {}).get("profile") != "habit":
                    pass  # a guide defers to explicit present evidence (revisable)
                else:
                    lg += boosts.get(cc, 0.0)  # habit: the old memory fights the update
                logits.append(lg)
            mx = max(logits)
            z = sum(math.exp(x - mx) for x in logits)
            mass = 0.75 + 0.2 * _rng("mass", self.seed, core).random()
            out.append([math.log(mass) + (x - mx) - math.log(z) for x in logits])
        return out


def joint_candidate_ids(tok, prompt: str, cand: str) -> tuple[list[int], int, int]:
    """Token ids of prompt + cand tokenized as ONE string (the stream the
    trainer saw), the number L of trailing tokens carrying candidate
    characters, and the number of tokens straddling the boundary. A
    straddling token (e.g. 'A: ' + 'K7M4' -> ' K') counts as the candidate's
    first token, so scoring the last L tokens gives P(candidate | prompt)
    under the training-time tokenization; separate tokenization would score
    a stream (' ', 'K') that never occurs in training. Falls back to separate
    tokenization when the tokenizer gives no offsets."""
    full = prompt + cand
    try:
        enc = tok(full, add_special_tokens=False, return_offsets_mapping=True)
        offs = enc["offset_mapping"]
    except Exception:  # noqa: BLE001 -- slow tokenizer
        p = tok(prompt, add_special_tokens=False).input_ids
        c = tok(cand, add_special_tokens=False).input_ids
        return list(p) + list(c), len(c), 0
    ids = list(enc["input_ids"])
    cut = len(prompt)
    L = sum(1 for (s, e) in offs if e > cut)
    straddle = sum(1 for (s, e) in offs if s < cut < e)
    return ids, L, straddle


class HFScorer:
    """Frozen Qwen2.5-7B-Instruct (+ optional PEFT adapter) scored with
    batched forward passes. OFF = the true frozen base via disable_adapter().
    set_lambda scales every LoRA delta (memo 3: lambda in {0,.25,.5,1})."""

    def __init__(self, model_name: str = MODEL_NAME, adapter_path: str | None = None,
                 batch_size: int = 16, lam: float = 1.0, device: str = "cuda"):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.tok.pad_token = self.tok.pad_token or self.tok.eos_token
        self.tok.padding_side = "left"
        base = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.bfloat16, device_map=device)
        self.has_adapter = adapter_path is not None
        if adapter_path:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(base, adapter_path)
        else:
            self.model = base
        self.model.eval()
        self.device = device
        self.batch_size = batch_size
        self._base_scaling = {}
        for name, mod in self.model.named_modules():
            sc = getattr(mod, "scaling", None)
            if isinstance(sc, dict):
                self._base_scaling[name] = dict(sc)
        self.lam = 1.0
        self.boundary_straddles = 0
        self.set_lambda(lam)

    def set_lambda(self, lam: float):
        self.lam = lam
        mods = dict(self.model.named_modules())
        for name, base in self._base_scaling.items():
            for k, v in base.items():
                mods[name].scaling[k] = v * lam

    @contextlib.contextmanager
    def off(self):
        if self.has_adapter:
            with self.model.disable_adapter():
                yield
        else:
            yield

    def _forward_last(self, rows: list[list[int]], keep: int):
        """Log-softmax of the last `keep` positions for left-padded rows."""
        torch = self.torch
        T = max(len(r) for r in rows)
        pad = self.tok.pad_token_id
        ids = torch.tensor([[pad] * (T - len(r)) + r for r in rows], device=self.device)
        attn = torch.tensor([[0] * (T - len(r)) + [1] * len(r) for r in rows], device=self.device)
        pos = (attn.cumsum(-1) - 1).clamp(min=0)
        kw = dict(input_ids=ids, attention_mask=attn, position_ids=pos, use_cache=False)
        with torch.no_grad():
            try:
                out = self.model(**kw, logits_to_keep=keep)
            except TypeError:
                try:
                    out = self.model(**kw, num_logits_to_keep=keep)
                except TypeError:
                    out = self.model(**kw)
        logits = out.logits[:, -keep:, :].float()
        return torch.log_softmax(logits, dim=-1)

    def candidate_logprobs(self, prompts: list[str], candidates: list[list[str]]) -> list[list[float]]:
        """log P(candidate | prompt) summed over the candidate's tokens under
        JOINT tokenization of prompt + candidate (joint_candidate_ids): the
        stream the trainer saw. Prompts whose candidates are all single
        tokens and leave the prompt's own tokens intact share one forward
        pass per batch; everything else is scored per (prompt, candidate)."""
        enc = lambda s: self.tok(s, add_special_tokens=False).input_ids  # noqa: E731
        p_ids = [enc(p) for p in prompts]
        joint = [[joint_candidate_ids(self.tok, p, c) for c in cs] for p, cs in zip(prompts, candidates)]
        self.boundary_straddles += sum(st for row in joint for _, _, st in row)
        out: list = [None] * len(prompts)
        fast = [i for i in range(len(prompts))
                if all(L == 1 and ids[:-1] == p_ids[i] for ids, L, _ in joint[i])]
        slow = [i for i in range(len(prompts)) if i not in set(fast)]
        fast.sort(key=lambda i: len(p_ids[i]))
        for s in range(0, len(fast), self.batch_size):
            chunk = fast[s:s + self.batch_size]
            lp = self._forward_last([p_ids[i] for i in chunk], 1)[:, -1, :]
            for r, i in enumerate(chunk):
                out[i] = [float(lp[r, ids[-1]]) for ids, _, _ in joint[i]]
        pairs = [(i, j) for i in slow for j in range(len(joint[i]))]
        pairs.sort(key=lambda ij: len(joint[ij[0]][ij[1]][0]))
        for i in slow:
            out[i] = [None] * len(joint[i])
        for s in range(0, len(pairs), self.batch_size):
            chunk = pairs[s:s + self.batch_size]
            rows = [joint[i][j][0] for i, j in chunk]
            keep = max(joint[i][j][1] for i, j in chunk) + 1
            lp = self._forward_last(rows, keep)
            for r, (i, j) in enumerate(chunk):
                ids, L, _ = joint[i][j]
                # position -(L+1) predicts the first candidate token, ... -2 the last
                total = 0.0
                for t in range(L):
                    total += float(lp[r, keep - 1 - L + t, ids[len(ids) - L + t]])
                out[i][j] = total
        return out


def load_scorer(model: str, adapter_path: str | None = None, lam: float = 1.0,
                batch_size: int = 16, seed: int = 0):
    if model == "mock":
        ad = None
        if adapter_path:
            ad = read_json(os.path.join(adapter_path, "mock_adapter.json"))
        return MockScorer(ad, lam=lam, seed=seed)
    return HFScorer(adapter_path=adapter_path, lam=lam, batch_size=batch_size)


def resolve_adapter(path: str | None) -> str | None:
    """Follow adapter_ref.json (a reused identical-corpus adapter)."""
    if not path or path == "none":
        return None
    p = os.path.expanduser(path)
    ref = os.path.join(p, "adapter_ref.json")
    if os.path.exists(ref):
        return resolve_adapter(read_json(ref)["reused_from"])
    return p

# ---------------------------------------------------------------------------
# trainer: mirrors organism_v6/train_adapter.py (frozen v1 config) + masks +
# multiplicity weights. Called on the node; the mock trainer stands in on CPU.
# ---------------------------------------------------------------------------
def weighted_token_nll(nll_rows: list[list[float]], weights: list[float]) -> float:
    """Reference semantics of the multiplicity-weighted batch loss:
    sum_i w_i sum_t nll_it / sum_i w_i n_i. With w_i = m (dedup_weighted) an
    item contributes exactly what m copies contribute under occurrence
    preservation WITHIN ONE BATCH; across steps the fits differ (per-batch
    normalisation, AdamW). train_hf computes the same formula through
    weighted_token_nll_torch (tested against this reference when torch is
    present)."""
    num = sum(w * sum(r) for r, w in zip(nll_rows, weights))
    den = sum(w * len(r) for r, w in zip(nll_rows, weights))
    return num / den if den > 0 else float("nan")


def weighted_token_nll_torch(nll, valid, w):
    """Torch form of weighted_token_nll on a [B, T] per-token NLL tensor, a
    [B, T] 0/1 label mask and a [B] weight vector. Returns (loss, den)."""
    num = (w[:, None] * nll * valid).sum()
    den = (w[:, None] * valid).sum()
    return num / den, den


def encode_item(tok, item: dict, max_len: int = TRAIN_MAX_LEN) -> dict:
    """Token ids and labels of one corpus item under JOINT tokenization of
    context + target (train_adapter.py tokenizes the whole piece text at
    once; tokenizing the two parts separately changes the token stream at the
    boundary -- e.g. 'A: ' + 'K7M4' gives ['A', ':', ' ', 'K', ...] instead of
    [..., ':', ' K', ...] -- so the exact training-style cue would not be a
    prefix of the trained sequence). The label boundary of masked items is
    placed by character offsets at the first token starting at or after the
    end of the context; a token straddling the boundary counts as context
    and is reported (n_straddle). Chat targets end with the EOS/IM_END token.
    Truncation keeps the TAIL (the supervised target)."""
    if item["chat"]:
        prefix = render_chat(item["context"], tokenizer=tok)
        full = prefix + item["target"] + (tok.eos_token or IM_END)
    else:
        prefix = item["context"]
        full = prefix + item["target"]
    ids = tok(full, add_special_tokens=False).input_ids
    straddle = 0
    if item["mask_context"]:
        try:
            offs = tok(full, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
        except Exception:  # noqa: BLE001 -- slow tokenizer: fall back to a prefix check
            offs = None
        if offs is not None:
            cut = len(prefix)
            labels = []
            for tid, (s, e) in zip(ids, offs):
                if s >= cut:
                    labels.append(tid)
                else:
                    labels.append(-100)
                    if e > cut:
                        straddle += 1
        else:
            p_ids = tok(prefix, add_special_tokens=False).input_ids
            if ids[:len(p_ids)] != p_ids:
                raise RuntimeError("context is not a token prefix of the joint piece and "
                                   "the tokenizer gives no offsets")
            labels = [-100] * len(p_ids) + ids[len(p_ids):]
    else:
        labels = list(ids)
    truncated = len(ids) > max_len
    if truncated:
        ids, labels = ids[-max_len:], labels[-max_len:]
    return dict(input_ids=ids, labels=labels, weight=float(item["weight"]),
                n_straddle=straddle, truncated=truncated,
                n_supervised=sum(1 for x in labels if x != -100))


def _mark_adapter_dir(out_dir: str) -> list[str]:
    """PEFT's save_pretrained writes an adapter README.md; every .md/.txt
    under the run dir must start with the synthetic header, so prepend it to
    any text file in the adapter directory that lacks it."""
    fixed = []
    for f in sorted(os.listdir(out_dir)):
        p = os.path.join(out_dir, f)
        if f.endswith((".md", ".txt")) and os.path.isfile(p):
            with open(p) as fh:
                body = fh.read()
            if not body.startswith(SYNTHETIC_HEADER):
                with open(p, "w") as fh:
                    fh.write(SYNTHETIC_HEADER + "\n" + body)
                fixed.append(p)
    return fixed


_TARGET_FACT_RE = re.compile(r"^(\S+)'s car is (\w+)\.$")
_TARGET_LESSON_RE = re.compile(r"^With (\S+) in mode (\w+), I press (\w+)\.$")


def _action_of_target(target: str) -> str:
    return target.rstrip(".").split()[-1]


def train_mock(corpus: dict, out_dir: str, epochs: int = TRAIN_EPOCHS,
               profile: str = "guide", rank: int = LORA_RANK, seed: int = 0) -> dict:
    """CPU stand-in for the LoRA fit: accumulates strength (epochs x weight
    per item) for the binding that the SUPERVISED TARGET TEXT itself
    expresses -- owner -> colour parsed from "{owner}'s car is {colour}.",
    (tool, mode) -> action parsed from the lesson target -- never from
    metadata or the context. So the scrambled-binding control, whose
    targets give every dose>=4 owner all four colours equally, leaves a flat
    strength profile (no preference), exactly as the token loss would."""
    out_dir = _check_inside(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    strength: dict = {}
    lessons: dict = {}
    habit: dict = {c: 0.0 for c in COLOURS}
    for it in corpus["corpus"]:
        w = float(it["weight"]) * epochs
        if it["kind"] in ("fact", "interference"):
            m = _TARGET_FACT_RE.match(it["target"])
            if m and m.group(2) in COLOURS:
                owner, colour = m.group(1), m.group(2)
                habit[colour] += w
                strength.setdefault(owner, {})[colour] = strength.get(owner, {}).get(colour, 0.0) + w
        elif it["kind"] == "lesson":
            m = _TARGET_LESSON_RE.match(it["target"])
            if m:
                d = lessons.setdefault(m.group(1), {}).setdefault(m.group(2), {})
                a = m.group(3).lower()
                d[a] = d.get(a, 0.0) + w
        elif it["kind"] == "filler_colour" and it.get("colour"):
            habit[it["colour"]] += w
    ad = dict(mock=True, profile=profile, strength=strength, lessons=lessons,
              habit=habit, corpus_sha=corpus["sha"], epochs=epochs, rank=rank, seed=seed,
              recipe="mock", ordering=corpus.get("ordering"))
    write_json(os.path.join(out_dir, "mock_adapter.json"), ad)
    write_json(os.path.join(out_dir, "train_meta.json"),
               dict(recipe="mock", n_items=len(corpus["corpus"]), rank=rank,
                    epochs=epochs, corpus_sha=corpus["sha"], seed=seed,
                    ordering=corpus.get("ordering"), writer=corpus.get("writer"),
                    representation=corpus.get("representation"), shuffled=corpus.get("shuffled")))
    _mark_adapter_dir(out_dir)
    with open(os.path.join(out_dir, "DONE"), "w") as f:
        f.write("ok\n")
    print(f"TRAIN_DONE recipe=mock profile={profile} items={len(corpus['corpus'])} "
          f"owners_bound={len(strength)} lessons_bound={len(lessons)}", flush=True)
    return ad


def train_hf(corpus: dict, out_dir: str, rank: int = LORA_RANK, epochs: int = TRAIN_EPOCHS,
             lr: float = TRAIN_LR, seed: int = 0, bsz: int = TRAIN_BSZ,
             max_len: int = TRAIN_MAX_LEN, max_steps: int | None = None,
             measure_only: bool = False, throughput_steps: int = 100,
             grad_checkpoint: bool = False, model_name: str = MODEL_NAME) -> dict:
    """Cumulative LoRA from the CLEAN BASE on one compiled corpus. Everything
    that train_adapter.py fixes is fixed here identically (rank, alpha=2r,
    dropout 0.05, q/k/v/o/gate/up/down, AdamW lr 1e-4, 3 epochs, bsz 4,
    max_len 512, in-order batches, no scheduler, no clipping). Added: label
    masks (zero-loss antecedents), per-item multiplicity weights, EOS on chat
    targets, seeded, 100-step throughput log."""
    out_dir = _check_inside(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    random.seed(seed)
    torch.manual_seed(seed)
    tok = AutoTokenizer.from_pretrained(model_name)
    tok.pad_token = tok.pad_token or tok.eos_token
    items = corpus["corpus"]
    encoded, n_straddle, n_truncated = [], 0, 0
    for it in items:
        enc = encode_item(tok, it, max_len=max_len)        # joint tokenization (see encode_item)
        n_straddle += enc["n_straddle"]
        n_truncated += int(enc["truncated"])
        encoded.append((enc["input_ids"], enc["labels"], enc["weight"]))
    print(f"ENCODED items={len(encoded)} boundary_straddles={n_straddle} truncated={n_truncated}", flush=True)
    base = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    cfg = LoraConfig(r=rank, lora_alpha=LORA_ALPHA_MULT * rank, lora_dropout=LORA_DROPOUT,
                     bias="none", target_modules=list(LORA_TARGETS))
    model = get_peft_model(base, cfg)
    if grad_checkpoint:
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
        model.config.use_cache = False
    model.train()
    opt = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=lr)
    total_steps = epochs * math.ceil(len(encoded) / bsz)
    steps, total_tokens, sup_tokens = 0, 0, 0
    loss_val = float("nan")
    t_start = time.time()
    throughput = None
    pad = tok.pad_token_id
    done = False
    for _ in range(epochs):
        for i in range(0, len(encoded), bsz):
            chunk = encoded[i:i + bsz]
            T = max(len(ids) for ids, _, _ in chunk)
            input_ids = torch.tensor([ids + [pad] * (T - len(ids)) for ids, _, _ in chunk], device="cuda")
            labels = torch.tensor([lb + [-100] * (T - len(lb)) for _, lb, _ in chunk], device="cuda")
            attn = torch.tensor([[1] * len(ids) + [0] * (T - len(ids)) for ids, _, _ in chunk], device="cuda")
            w = torch.tensor([wt for _, _, wt in chunk], device="cuda", dtype=torch.float32)
            logits = model(input_ids=input_ids, attention_mask=attn, use_cache=False).logits
            shift_logits = logits[:, :-1, :].float()
            shift_labels = labels[:, 1:]
            nll = torch.nn.functional.cross_entropy(
                shift_logits.reshape(-1, shift_logits.size(-1)), shift_labels.reshape(-1),
                reduction="none", ignore_index=-100).view(shift_labels.shape)
            valid = (shift_labels != -100).float()
            loss, den = weighted_token_nll_torch(nll, valid, w)
            if den.item() == 0:
                continue
            if not torch.isfinite(loss):
                print(f"NONFINITE_LOSS step={steps} -- skipping batch", flush=True)
                opt.zero_grad()
                continue
            loss.backward()
            opt.step()
            opt.zero_grad()
            steps += 1
            loss_val = float(loss)
            total_tokens += int(attn.sum())
            sup_tokens += int(valid.sum())
            if steps == throughput_steps or (max_steps and steps == max_steps and throughput is None):
                el = time.time() - t_start
                throughput = dict(steps=steps, seconds=round(el, 1),
                                  tokens=total_tokens, tokens_per_s=round(total_tokens / el, 1),
                                  sec_per_step=round(el / steps, 3), total_steps=total_steps,
                                  projected_fit_minutes=round(el / steps * total_steps / 60, 1),
                                  n_items=len(encoded), epochs=epochs, bsz=bsz, rank=rank,
                                  corpus_sha=corpus["sha"], grad_checkpoint=grad_checkpoint)
                write_json(os.path.join(out_dir, "throughput.json"), throughput)
                print(f"THROUGHPUT steps={steps} tok/s={throughput['tokens_per_s']} "
                      f"projected_fit_min={throughput['projected_fit_minutes']}", flush=True)
                if measure_only:
                    done = True
                    break
            if max_steps and steps >= max_steps:
                done = True
                break
        if done:
            break
    meta = dict(recipe="memory_dose_v1 (mirrors train_adapter.py v1)", n_items=len(encoded),
                steps=steps, total_steps=total_steps, tokens=total_tokens,
                supervised_tokens=sup_tokens, rank=rank, alpha=LORA_ALPHA_MULT * rank,
                dropout=LORA_DROPOUT, targets=LORA_TARGETS, epochs=epochs, lr=lr, bsz=bsz,
                max_len=max_len, seed=seed, final_loss=loss_val, corpus_sha=corpus["sha"],
                items_sha=corpus.get("items_sha"), ordering=corpus.get("ordering"),
                writer=corpus.get("writer"), representation=corpus.get("representation"),
                shuffled=corpus.get("shuffled"), model=model_name,
                tokenization="joint context+target (encode_item)", boundary_straddles=n_straddle,
                truncated_items=n_truncated,
                wall_seconds=round(time.time() - t_start, 1), throughput=throughput,
                measure_only=measure_only)
    if measure_only:
        write_json(os.path.join(out_dir, "train_meta.json"), meta)
        with open(os.path.join(out_dir, "MEASURED"), "w") as f:
            f.write("ok\n")
        print(f"MEASURE_DONE steps={steps} tokens={total_tokens}", flush=True)
        return meta
    model.save_pretrained(out_dir)
    meta["synthetic_header_added_to"] = _mark_adapter_dir(out_dir)   # PEFT's README.md
    write_json(os.path.join(out_dir, "train_meta.json"), meta)
    with open(os.path.join(out_dir, "DONE"), "w") as f:
        f.write("ok\n")
    print(f"TRAIN_DONE items={len(encoded)} steps={steps} tokens={total_tokens} "
          f"loss={loss_val:.4f} wall_s={meta['wall_seconds']}", flush=True)
    return meta


def _adapter_index_path(run_dir: str) -> str:
    return os.path.join(run_dir, "adapters", "index.json")


def find_reusable(run_dir: str, key: dict) -> str | None:
    """An already-trained adapter for the same (corpus sha, rank, epochs, lr,
    seed, model): identical corpora give identical fits (memo 2.3), so the
    runbook never pays twice."""
    p = _adapter_index_path(run_dir)
    if not os.path.exists(p):
        return None
    for ent in read_json(p).get("entries", []):
        if all(ent.get(k) == v for k, v in key.items()) and os.path.exists(os.path.join(ent["path"], "DONE")):
            return ent["path"]
    return None


def register_adapter(run_dir: str, key: dict, path: str):
    p = _adapter_index_path(run_dir)
    d = read_json(p) if os.path.exists(p) else dict(entries=[])
    d["entries"] = [e for e in d.get("entries", []) if e.get("path") != path]
    d["entries"].append(dict(key, path=path))
    write_json(p, d)


def train_command(run_dir: str, corpus_path: str, out_dir: str, model: str = "hf",
                  rank: int = LORA_RANK, epochs: int = TRAIN_EPOCHS, lr: float = TRAIN_LR,
                  seed: int = 0, max_steps: int | None = None, measure_only: bool = False,
                  grad_checkpoint: bool = False, mock_profile: str = "guide",
                  no_reuse: bool = False) -> dict:
    root = set_write_root(run_dir)
    corpus = read_json(corpus_path)
    out_dir = _check_inside(out_dir)
    key = dict(corpus_sha=corpus["sha"], rank=rank, epochs=epochs, lr=lr, seed=seed,
               model=(MODEL_NAME if model == "hf" else f"mock:{mock_profile}"))
    if os.path.exists(os.path.join(out_dir, "DONE")):
        print(f"TRAIN_EXISTS {out_dir}", flush=True)
        return dict(status="exists", path=out_dir)
    if not measure_only and not no_reuse:
        prev = find_reusable(root, key)
        if prev and os.path.realpath(prev) != os.path.realpath(out_dir):
            os.makedirs(out_dir, exist_ok=True)
            write_json(os.path.join(out_dir, "adapter_ref.json"),
                       dict(reused_from=prev, reason="identical corpus sha and config", **key))
            with open(os.path.join(out_dir, "DONE"), "w") as f:
                f.write("reused\n")
            print(f"TRAIN_REUSED {prev}", flush=True)
            return dict(status="reused", path=prev)
    if model == "mock":
        meta = train_mock(corpus, out_dir, epochs=epochs, profile=mock_profile, rank=rank, seed=seed)
    else:
        meta = train_hf(corpus, out_dir, rank=rank, epochs=epochs, lr=lr, seed=seed,
                        max_steps=max_steps, measure_only=measure_only,
                        grad_checkpoint=grad_checkpoint)
    if not measure_only:
        register_adapter(root, key, out_dir)
    return dict(status="trained", path=out_dir, meta=meta)

# ---------------------------------------------------------------------------
# evaluation: cues, controls, contexts, lessons; ON/OFF batched scoring
# ---------------------------------------------------------------------------
def _repaint_colour(colour: str) -> str:
    return COLOURS[(COLOURS.index(colour) + 1) % len(COLOURS)]


def action_candidates(A: str, B: str, completion: bool) -> dict:
    """Complete action strings WITH a common termination convention (memo:
    multi-token answers are scored as complete strings without length
    normalisation): IM_END after the chat cue, a period after the bare
    completion cue; three casings each."""
    if completion:
        return {a: [" " + v + "." for v in (a, a.capitalize(), a.lower())] for a in (A, B)}
    return {a: [v + IM_END for v in (a, a.capitalize(), a.lower())] for a in (A, B)}


def textfit_candidates(owner: str, chat: bool) -> dict:
    """The four full child-target renderings of one owner (one per colour):
    P of the planted one is the training-text likelihood (memo section 1:
    'training-text fit', not retrievable memory); normalising over the four
    gives the colour distribution under the full-sentence rendering."""
    end = IM_END if chat else ""
    return {c: [TARGET_TMPL.format(owner=owner, colour=c) + end] for c in COLOURS}


def _cand_tokens(cset: dict, tokenizer=None, prompt: str = "") -> dict:
    """Token length of every candidate string under joint tokenization with
    its prompt (the count the scorer sums over; recorded in the eval JSON);
    approximate counter without a tokenizer."""
    if tokenizer is not None:
        n = lambda s: joint_candidate_ids(tokenizer, prompt, s)[1]  # noqa: E731
    else:
        cnt = TokenCounter("approx")
        n = lambda s: cnt.count(s.replace(IM_END, " <|im_end|>"))  # noqa: E731
    return {k: [n(v) for v in vs] for k, vs in cset.items()}


def build_cues(bank: dict, distractor: str, adjacent_subset: int = 4,
               tokenizer=None) -> list[dict]:
    """Every scored prompt of one bank. Facts: 3 held-out paraphrases + the
    base-rate calibration prompt + two exact training-style cues; contexts:
    none / correct observation before the distractor / adjacent (subset) /
    explicit repaint override; controls: unexposed owners (dose 0), similar
    ids, bicycle, generic car (the swapped-id control re-reads the partner's
    own fact rows for the owner's colour -- no extra prompt); text-fit probes
    (the A/B short piece and the C/D antecedent piece, all four colour
    renderings); lessons: trigger / no-trigger / reversed + exact cue, with
    terminated action strings. Candidate answers never appear in a query
    except the base-rate prompt, which names the base colour by design."""
    cues = []
    owners = bank["owners"]
    dose_rank: dict = {}
    for o in owners:
        dose_rank.setdefault(o["dose"], []).append(o["id"])
    cands = colour_candidates(False)
    cands_sp = colour_candidates(True)
    tok_cache: dict = {}

    def add(cue_id, kind, prompt, cset, a, **extra):
        # the boundary tokenization depends only on the prompt's tail (BPE pre-tokenization is
        # local), so cache by (prompt tail, candidate set) rather than re-tokenizing 1k-token prompts
        key = (prompt[-64:], json.dumps(cset, sort_keys=True))
        if key not in tok_cache:
            tok_cache[key] = _cand_tokens(cset, tokenizer, prompt[-64:])
        cues.append(dict(cue_id=cue_id, kind=kind, prompt=prompt, candidates=cset, a=a,
                         cand_tokens=tok_cache[key], **extra))

    for o in owners:
        oid, col, d = o["id"], o["colour"], o["dose"]
        obs = OBS_TMPL.format(where=SITUATIONS[0], owner=oid, colour=col)
        for f in PARAPHRASES:
            q = QUERY_FORMS[f].format(owner=oid)
            add(f"fact|{oid}|{f}", "fact", render_chat(q, tokenizer=tokenizer), cands, col,
                owner=oid, dose=d, form=f, context="none")
            add(f"incontext|{oid}|{f}", "incontext",
                render_chat(obs + "\n\n" + distractor + "\n\n" + q, tokenizer=tokenizer),
                cands, col, owner=oid, dose=d, form=f, context="distractor")
            if oid in dose_rank[d][:adjacent_subset]:
                add(f"adjacent|{oid}|{f}", "adjacent",
                    render_chat(obs + "\n\n" + q, tokenizer=tokenizer), cands, col,
                    owner=oid, dose=d, form=f, context="adjacent")
            if d > 0:
                new = _repaint_colour(col)
                rp = REPAINT_OBS.format(owner=oid, colour=new)
                add(f"repaint|{oid}|{f}", "repaint",
                    render_chat(rp + "\n\n" + distractor + "\n\n" + q, tokenizer=tokenizer),
                    cands, new, owner=oid, dose=d, form=f, context="repaint", old_colour=col)
                add(f"similar|{oid}|{f}", "similar",
                    render_chat(QUERY_FORMS[f].format(owner=o["similar_id"]), tokenizer=tokenizer),
                    cands, col, owner=oid, dose=d, form=f, context="none", cue_id_used=o["similar_id"])
        add(f"base_rate|{oid}", "base_rate",
            render_chat(BASE_RATE_FORM.format(owner=oid, base_colour=bank["base_colour"]),
                        tokenizer=tokenizer), cands, col, owner=oid, dose=d, form="base_rate",
            context="none", names_base_colour=True)
        add(f"exact_short|{oid}", "exact_short",
            SHORT_HEADER.format(owner=oid) + EXACT_COMPLETION.format(owner=oid), cands_sp, col,
            owner=oid, dose=d, form="exact_short", context="none")
        add(f"exact_ante|{oid}", "exact_ante",
            render_chat(OBS_SITUATION_ONLY.format(where=SITUATIONS[0], owner=oid),
                        EXACT_COMPLETION.format(owner=oid), tokenizer=tokenizer), cands_sp, col,
            owner=oid, dose=d, form="exact_ante", context="none")
        # training-text fit: the exact A/B and C/D training texts of this owner
        add(f"textfit_short|{oid}", "textfit_short", SHORT_HEADER.format(owner=oid),
            textfit_candidates(oid, chat=False), col, owner=oid, dose=d, form="textfit_short",
            context="training_text")
        add(f"textfit_ante|{oid}", "textfit_ante", render_chat(obs, tokenizer=tokenizer),
            textfit_candidates(oid, chat=True), col, owner=oid, dose=d, form="textfit_ante",
            context="training_text")
        if d > 0:
            add(f"bicycle|{oid}", "bicycle",
                render_chat(BICYCLE_FORM.format(owner=oid), tokenizer=tokenizer), cands, col,
                owner=oid, dose=d, form="bicycle", context="none")
    add("generic", "generic", render_chat(GENERIC_FORM, tokenizer=tokenizer), cands, None,
        owner=None, dose=None, form="generic", context="none")
    for les in bank["lessons"]:
        X, Y = les["modes"]
        A, B = les["mapping"][X], les["mapping"][Y]
        acts = action_candidates(A, B, completion=False)
        acts_sp = action_candidates(A, B, completion=True)
        base = dict(lesson_id=les["lesson_id"], tool=les["tool"], dose=les["dose"], b=B,
                    owner=None, form="lesson", context="none")
        add(f"lesson_trigger|{les['lesson_id']}", "lesson_trigger",
            render_chat(LESSON_QUERY.format(tool=les["tool"], mode=X), tokenizer=tokenizer), acts, A, **base)
        add(f"lesson_notrigger|{les['lesson_id']}", "lesson_notrigger",
            render_chat(LESSON_QUERY_NOTRIGGER.format(tool=les["tool"]), tokenizer=tokenizer), acts, A, **base)
        add(f"lesson_reversed|{les['lesson_id']}", "lesson_reversed",
            render_chat(LESSON_QUERY.format(tool=les["tool"], mode=Y), tokenizer=tokenizer), acts, A, **base)
        add(f"lesson_exact|{les['lesson_id']}", "lesson_exact",
            render_chat(LESSON_SITUATION_ONLY.format(tool=les["tool"], mode=X),
                        LESSON_EXACT.format(tool=les["tool"], mode=X), tokenizer=tokenizer), acts_sp, A, **base)
    return cues


def score_cues(scorer, cues: list[dict], lambdas: list[float] | None = None) -> dict:
    """One OFF pass (adapter disabled) and one ON pass per lambda; returns
    {lambda: [p_raw per cue]} plus OFF. Raw per-variant sums per answer."""
    prompts = [c["prompt"] for c in cues]
    cand_lists = [sum(c["candidates"].values(), []) for c in cues]

    def collapse(lps):
        out = []
        for c, lp in zip(cues, lps):
            out.append(colour_probs(c["candidates"], lp) if len(c["candidates"]) == len(COLOURS)
                       and set(c["candidates"]) == set(COLOURS) else _probs_generic(c["candidates"], lp))
        return out

    with scorer.off():
        off = collapse(scorer.candidate_logprobs(prompts, cand_lists))
    on = {}
    lambdas = lambdas or [1.0]
    for lam in lambdas:
        scorer.set_lambda(lam)
        on[lam] = collapse(scorer.candidate_logprobs(prompts, cand_lists))
    scorer.set_lambda(1.0)
    return dict(off=off, on=on)


def _probs_generic(cset: dict, logprobs: list[float]) -> dict:
    raw, logp, i = {}, {}, 0
    for k, variants in cset.items():
        lps = logprobs[i:i + len(variants)]
        raw[k] = sum(math.exp(lp) for lp in lps)
        logp[k] = _logsumexp(lps)
        i += len(variants)
    mass = sum(raw.values())
    norm = {k: (raw[k] / mass if mass > 0 else 1.0 / len(cset)) for k in cset}
    return dict(p_raw=raw, p_norm=norm, mass=mass, logp=logp)


def evaluate_command(run_dir: str, bank_idx: int, adapter: str | None, tag: str,
                     model: str = "mock", lambdas: list[float] | None = None,
                     adjacent_subset: int = 4, batch_size: int = 16, seed: int = 0,
                     meta: dict | None = None) -> list[str]:
    root = set_write_root(run_dir)
    bank = read_json(os.path.join(root, "banks", f"bank{bank_idx}.json"))
    distractor = read_json(os.path.join(root, "distractor.json"))["text"]
    ad = resolve_adapter(adapter)
    t0 = time.time()
    scorer = load_scorer(model, ad, batch_size=batch_size, seed=seed)
    cues = build_cues(bank, distractor, adjacent_subset=adjacent_subset,
                      tokenizer=getattr(scorer, "tok", None))
    template_check = None
    if getattr(scorer, "tok", None) is not None:
        try:
            template_check = (render_chat("probe", tokenizer=scorer.tok) == render_chat("probe"))
        except Exception:  # noqa: BLE001
            template_check = None
    lambdas = lambdas or [1.0]
    if ad is None:
        lambdas = [1.0]
    adapter_meta = {}
    if ad and os.path.exists(os.path.join(ad, "train_meta.json")):
        tm = read_json(os.path.join(ad, "train_meta.json"))
        adapter_meta = {k: tm.get(k) for k in ("corpus_sha", "items_sha", "ordering", "writer",
                                                "representation", "shuffled", "rank", "recipe")}
    res = score_cues(scorer, cues, lambdas)
    paths = []
    for lam in lambdas:
        rows = []
        for c, off, on in zip(cues, res["off"], res["on"][lam]):
            r = {k: v for k, v in c.items() if k not in ("prompt", "candidates")}
            r["OFF"] = dict(p_raw={k: round(v, 7) for k, v in off["p_raw"].items()}, mass=round(off["mass"], 7),
                            logp={k: round(v, 5) for k, v in off["logp"].items()})
            r["ON"] = dict(p_raw={k: round(v, 7) for k, v in on["p_raw"].items()}, mass=round(on["mass"], 7),
                           logp={k: round(v, 5) for k, v in on["logp"].items()})
            rows.append(r)
        out = dict(tag=tag, bank=bank_idx, adapter=ad, adapter_arg=adapter, adapter_meta=adapter_meta,
                   lam=lam, model=model, n_cues=len(cues), seconds=round(time.time() - t0, 1),
                   template_check=template_check, meta=meta or {}, cues=rows,
                   scorer_calls=getattr(scorer, "calls", None),
                   tokenization="joint prompt+candidate (joint_candidate_ids)",
                   boundary_straddles=getattr(scorer, "boundary_straddles", None))
        p = write_json(os.path.join(root, "eval", f"{tag}__lam{lam:g}.json"), out)
        paths.append(p)
        print(f"EVAL_DONE {tag} lam={lam:g} cues={len(cues)} s={out['seconds']}", flush=True)
    return paths

# ---------------------------------------------------------------------------
# analysis: metrics, summaries, bootstrap, gates (memo 2.4), interpretation
# ---------------------------------------------------------------------------
GATES = dict(p_on=0.80, d_p=0.30, prior_p_on=0.85, trigger_nats=1.5, unrelated=0.03,
             ctx_on=0.90, ctx_degrade=0.03, retention=0.75, dose_step=0.10,
             saturation=0.80, min_gain=0.05, exact_gain=0.30,
             swapped_d_p=0.03,           # owner's colour bleeding onto the partner's cue (habit signal)
             min_prior_subset=4, prior_window=(0.55, 0.65),
             mass_ratio=0.5, mass_floor=0.10,   # G9: candidate-set mass must not collapse
             textfit_storage=0.3)        # nats/token of training-text fit that flags storage-without-extraction


def _log(x: float) -> float:
    return math.log(max(x, 1e-12))


def cue_metrics(row: dict, a: str | None = None, b: str | None = None) -> dict:
    """raw P(a), candidate-normalized P(a), candidate-set mass, log-odds of a
    vs b (b = the strongest alternative under OFF unless fixed), ON and OFF,
    and their differences."""
    a = a or row["a"]
    off_raw, on_raw = row["OFF"]["p_raw"], row["ON"]["p_raw"]
    keys = list(off_raw)
    if b is None:
        b = row.get("b") or max((k for k in keys if k != a), key=lambda k: off_raw[k])

    def side(raw, mass):
        tot = sum(raw.values())
        pn = raw[a] / tot if tot > 0 else 1.0 / len(keys)
        return dict(p_raw=raw[a], p_norm=pn, mass=mass, logodds=_log(raw[a]) - _log(raw[b]))

    OFF, ON = side(off_raw, row["OFF"]["mass"]), side(on_raw, row["ON"]["mass"])
    return dict(a=a, b=b, OFF=OFF, ON=ON, d_p_norm=ON["p_norm"] - OFF["p_norm"],
                d_p_raw=ON["p_raw"] - OFF["p_raw"], d_logodds=ON["logodds"] - OFF["logodds"],
                d_mass=ON["mass"] - OFF["mass"])


def _index(rows: list[dict]) -> dict:
    idx: dict = {}
    for r in rows:
        idx.setdefault((r["kind"], r.get("owner") or r.get("lesson_id"), r.get("form")), r)
    return idx


def prior_bin_label(p: float | None, edges: list[float] = PRIOR_BIN_EDGES) -> str | None:
    """Pre-registered OFF-prior bin of an owner (edges stored in the manifest)."""
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return None
    lo = None
    for e in edges:
        if p < e:
            return f"<{e:g}" if lo is None else f"{lo:g}-{e:g}"
        lo = e
    return f">={lo:g}"


def prior_bin_labels(edges: list[float] = PRIOR_BIN_EDGES) -> list[str]:
    out, lo = [], None
    for e in edges:
        out.append(f"<{e:g}" if lo is None else f"{lo:g}-{e:g}")
        lo = e
    return out + [f">={lo:g}"]


def _textfit_gain(row: dict, a: str, n_tokens: int) -> tuple[float, float]:
    """Training-text fit: per-token log-likelihood gain ON-OFF of the planted
    full target rendering (nats/token; positive = the adapter fits the
    training text better) and the OFF per-token NLL."""
    lp_off = row["OFF"].get("logp", {}).get(a)
    lp_on = row["ON"].get("logp", {}).get(a)
    if lp_off is None:
        lp_off = _log(row["OFF"]["p_raw"][a])
    if lp_on is None:
        lp_on = _log(row["ON"]["p_raw"][a])
    n = max(1, int(n_tokens or 1))
    return (lp_on - lp_off) / n, -lp_off / n


def summarize_eval(ev: dict, bank: dict, edges: list[float] | None = None) -> dict:
    """Per-owner, per-dose, per-OFF-prior-bin and control aggregates of one
    evaluated checkpoint. The swapped-id control is the partner's own fact
    row re-read for the OWNER's colour (a = owner's colour, b = partner's
    planted colour): swapped_d_p > 0 means the owner's colour bleeds onto a
    different exposed owner's cue (habit signal); its log-odds term is
    dominated by the partner's own learning and is reported, not gated."""
    edges = edges or bank.get("prior_bin_edges") or PRIOR_BIN_EDGES
    idx = _index(ev["cues"])
    owners = {o["id"]: o for o in bank["owners"]}
    dose_groups: dict = {}
    for o in bank["owners"]:
        dose_groups.setdefault(o["dose"], []).append(o["id"])
    g = idx[("generic", None, "generic")]
    per_owner: dict = {}
    for oid, o in owners.items():
        fm = [cue_metrics(idx[("fact", oid, f)]) for f in PARAPHRASES]
        e = dict(dose=o["dose"], colour=o["colour"],
                 prior_assigned=o.get("prior_assigned"),
                 prior_bin=prior_bin_label(o.get("prior_assigned"), edges),
                 p_off=_mean(m["OFF"]["p_norm"] for m in fm), p_on=_mean(m["ON"]["p_norm"] for m in fm),
                 d_p=_mean(m["d_p_norm"] for m in fm), term1=_mean(m["d_logodds"] for m in fm),
                 mass_off=_mean(m["OFF"]["mass"] for m in fm), mass_on=_mean(m["ON"]["mass"] for m in fm),
                 mass_on_min=min(m["ON"]["mass"] for m in fm),
                 p_raw_on=_mean(m["ON"]["p_raw"] for m in fm), p_raw_off=_mean(m["OFF"]["p_raw"] for m in fm),
                 forms={f: dict(p_off=m["OFF"]["p_norm"], p_on=m["ON"]["p_norm"], b=m["b"])
                        for f, m in zip(PARAPHRASES, fm)})
        if e["prior_bin"] is None:
            e["prior_bin"] = prior_bin_label(e["p_off"], edges)
        cm = [cue_metrics(idx[("incontext", oid, f)]) for f in PARAPHRASES]
        e["ctx_on"], e["ctx_off"] = _mean(m["ON"]["p_norm"] for m in cm), _mean(m["OFF"]["p_norm"] for m in cm)
        am = [cue_metrics(idx[k]) for k in [("adjacent", oid, f) for f in PARAPHRASES] if k in idx]
        if am:
            e["adj_on"], e["adj_off"] = _mean(m["ON"]["p_norm"] for m in am), _mean(m["OFF"]["p_norm"] for m in am)
        for kind in ("exact_short", "exact_ante", "base_rate"):
            m = cue_metrics(idx[(kind, oid, kind)])
            e[f"{kind}_d_p"], e[f"{kind}_on"], e[f"{kind}_off"] = m["d_p_norm"], m["ON"]["p_norm"], m["OFF"]["p_norm"]
        for kind in ("textfit_short", "textfit_ante"):
            k = (kind, oid, kind)
            if k in idx:
                row = idx[k]
                n_tok = (row.get("cand_tokens") or {}).get(o["colour"], [None])[0]
                gain, nll_off = _textfit_gain(row, o["colour"], n_tok)
                e[f"{kind}_gain"], e[f"{kind}_nll_off"] = gain, nll_off
                e[f"{kind}_p_norm_on"] = cue_metrics(row)["ON"]["p_norm"]
        if o["dose"] > 0:
            sm = [cue_metrics(idx[("similar", oid, f)], a=m["a"], b=m["b"]) for f, m in zip(PARAPHRASES, fm)]
            e["term2"] = _mean(m["d_logodds"] for m in sm)
            e["I_d"] = e["term1"] - e["term2"]
            e["similar_d_p"] = _mean(m["d_p_norm"] for m in sm)
            bm = cue_metrics(idx[("bicycle", oid, "bicycle")])
            e["bicycle_d_p"] = bm["d_p_norm"]
            e["I_d_bicycle"] = e["term1"] - cue_metrics(idx[("bicycle", oid, "bicycle")], a=fm[0]["a"], b=fm[0]["b"])["d_logodds"]
            if o.get("partner") and ("fact", o["partner"], PARAPHRASES[0]) in idx:
                pc = owners[o["partner"]]["colour"]
                sw = [cue_metrics(idx[("fact", o["partner"], f)], a=o["colour"], b=pc) for f in PARAPHRASES]
                e["swapped_d_logodds"] = _mean(m["d_logodds"] for m in sw)
                e["swapped_d_p"] = _mean(m["d_p_norm"] for m in sw)
            # matched non-triggers of the other types, same (a, b) as the owner's own cue
            u = dose_groups[0][dose_groups[o["dose"]].index(oid) % len(dose_groups[0])]
            e["I_d_unexposed"] = e["term1"] - _mean(
                cue_metrics(idx[("fact", u, f)], a=m["a"], b=m["b"])["d_logodds"] for f, m in zip(PARAPHRASES, fm))
            e["I_d_generic"] = e["term1"] - _mean(cue_metrics(g, a=m["a"], b=m["b"])["d_logodds"] for m in fm)
            rm = [cue_metrics(idx[("repaint", oid, f)]) for f in PARAPHRASES]
            e["repaint_on"], e["repaint_off"] = _mean(m["ON"]["p_norm"] for m in rm), _mean(m["OFF"]["p_norm"] for m in rm)
            e["repaint_old_on"] = _mean(cue_metrics(idx[("repaint", oid, f)], a=o["colour"])["ON"]["p_norm"] for f in PARAPHRASES)
        per_owner[oid] = e
    fields = ["p_off", "p_on", "d_p", "term1", "term2", "I_d", "I_d_bicycle", "I_d_unexposed",
              "I_d_generic", "mass_off", "mass_on", "mass_on_min",
              "p_raw_on", "p_raw_off", "ctx_on", "ctx_off", "adj_on", "adj_off",
              "exact_short_d_p", "exact_ante_d_p", "exact_short_on", "exact_ante_on",
              "base_rate_on", "base_rate_off", "similar_d_p", "bicycle_d_p",
              "swapped_d_logodds", "swapped_d_p", "repaint_on", "repaint_off", "repaint_old_on",
              "textfit_short_gain", "textfit_ante_gain", "textfit_short_nll_off", "textfit_ante_nll_off",
              "textfit_short_p_norm_on", "textfit_ante_p_norm_on"]
    per_dose = {}
    for d in DOSES:
        es = [e for e in per_owner.values() if e["dose"] == d]
        row = dict(n=len(es))
        for f in fields:
            vals = [e[f] for e in es if f in e]
            row[f] = _mean(vals) if vals else None
        row["mass_on_min"] = min((e["mass_on_min"] for e in es), default=None)
        row["similar_abs_d_p"] = _mean(abs(e["similar_d_p"]) for e in es if "similar_d_p" in e) if d > 0 else None
        row["bicycle_abs_d_p"] = _mean(abs(e["bicycle_d_p"]) for e in es if "bicycle_d_p" in e) if d > 0 else None
        row["abs_d_p"] = _mean(abs(e["d_p"]) for e in es)
        row["I_d_values"] = [e["I_d"] for e in es if "I_d" in e]
        row["d_p_values"] = [e["d_p"] for e in es]
        row["term1_values"] = [e["term1"] for e in es]
        per_dose[d] = row
    # by pre-registered OFF-prior bin (dose 16 = headline; all exposed doses too)
    by_prior_bin = {}
    for scope, sel in (("dose16", lambda e: e["dose"] == 16), ("exposed", lambda e: e["dose"] > 0)):
        bins = {}
        for lab in prior_bin_labels(edges):
            es = [e for e in per_owner.values() if sel(e) and e["prior_bin"] == lab]
            bins[lab] = dict(n=len(es), values={k: [e[k] for e in es if k in e]
                                                for k in ("p_off", "p_on", "d_p", "I_d", "p_raw_on", "p_raw_off")})
            for k, vals in bins[lab]["values"].items():
                bins[lab][k] = _mean(vals) if vals else None
        by_prior_bin[scope] = bins
    generic = {c: cue_metrics(g, a=c)["d_p_norm"] for c in COLOURS}
    exposed = [e for e in per_owner.values() if e["dose"] > 0]
    controls = dict(
        unexposed_abs_d_p=per_dose[0]["abs_d_p"], unexposed_d_p=per_dose[0]["d_p"],
        similar_abs_d_p=_mean(abs(e["similar_d_p"]) for e in exposed),
        bicycle_abs_d_p=_mean(abs(e["bicycle_d_p"]) for e in exposed),
        generic=generic, generic_abs_d_p=_mean(abs(v) for v in generic.values()),
        swapped_d_logodds=_mean(e["swapped_d_logodds"] for e in exposed if "swapped_d_logodds" in e),
        swapped_d_p=_mean(e["swapped_d_p"] for e in exposed if "swapped_d_p" in e))
    controls["unrelated_shift"] = _mean([controls["unexposed_abs_d_p"], controls["similar_abs_d_p"],
                                         controls["bicycle_abs_d_p"], controls["generic_abs_d_p"]])
    ps = [x for x in bank.get("prior_subset", []) if owners[x["owner"]]["dose"] == 16]
    prior_vals = [per_owner[x["owner"]]["forms"][x["form"]]["p_on"] for x in ps]
    prior_subset = dict(n=len(prior_vals), p_on=_mean(prior_vals) if prior_vals else None,
                        p_off=_mean(x["p_off"] for x in ps) if ps else None)
    br = [e for e in per_owner.values() if e["dose"] == 16 and e["colour"] == bank["base_colour"]]
    base_rate_subset = dict(n=len(br), p_on=_mean(e["base_rate_on"] for e in br) if br else None,
                            p_off=_mean(e["base_rate_off"] for e in br) if br else None,
                            names_base_colour=True)
    lessons = {}
    for les in bank["lessons"]:
        lid = les["lesson_id"]
        X, Y = les["modes"]
        A, B = les["mapping"][X], les["mapping"][Y]
        m = {k: cue_metrics(idx[(f"lesson_{k}", lid, "lesson")], a=A, b=B)
             for k in ("trigger", "notrigger", "reversed", "exact")}
        lessons[lid] = dict(dose=les["dose"], trigger=m["trigger"]["d_logodds"],
                            notrigger=m["notrigger"]["d_logodds"], reversed=m["reversed"]["d_logodds"],
                            exact=m["exact"]["d_logodds"],
                            interaction=m["trigger"]["d_logodds"] - m["notrigger"]["d_logodds"],
                            selectivity=m["trigger"]["d_logodds"] - m["reversed"]["d_logodds"],
                            p_on_trigger=m["trigger"]["ON"]["p_norm"], p_off_trigger=m["trigger"]["OFF"]["p_norm"],
                            p_on_reversed_B=1 - m["reversed"]["ON"]["p_norm"],
                            mass_on=m["trigger"]["ON"]["mass"], mass_off=m["trigger"]["OFF"]["mass"])
    lesson_per_dose = {}
    for d in DOSES:
        ls = [v for v in lessons.values() if v["dose"] == d]
        lesson_per_dose[d] = dict(n=len(ls), **{k: _mean(v[k] for v in ls) for k in
                                                ("trigger", "notrigger", "reversed", "exact", "interaction",
                                                 "selectivity", "p_on_trigger", "p_off_trigger", "mass_on", "mass_off")})
    return dict(per_owner=per_owner, per_dose=per_dose, controls=controls, prior_subset=prior_subset,
                base_rate_subset=base_rate_subset, by_prior_bin=by_prior_bin, prior_bin_edges=list(edges),
                lessons=lessons, lesson_per_dose=lesson_per_dose,
                template_check=ev.get("template_check"), lam=ev.get("lam", 1.0), bank=bank["bank"],
                adapter_meta=ev.get("adapter_meta") or {})


def paired_bootstrap(values: list[float], n_boot: int = 2000, seed: int = 0) -> dict:
    """Percentile 95% interval of the mean, resampling units (owners) with
    replacement. Paired because every value is an ON-OFF difference (or a
    difference of differences) computed on the same owner and cue."""
    vals = [v for v in values if v is not None and not math.isnan(v)]
    if not vals:
        return dict(mean=None, lo=None, hi=None, n=0)
    rng = random.Random(seed)
    n = len(vals)
    means = sorted(sum(vals[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot))
    return dict(mean=sum(vals) / n, lo=means[int(0.025 * n_boot)], hi=means[min(n_boot - 1, int(0.975 * n_boot))], n=n)


def pool(summaries: list[dict]) -> dict:
    """Pool banks: per-dose means over (bank, owner) units; bootstrap over
    the pooled units; controls averaged over banks."""
    per_dose = {}
    for d in DOSES:
        rows = [s["per_dose"][d] for s in summaries]
        pooled = dict(n=sum(r["n"] for r in rows))
        for k in rows[0]:
            if k.endswith("_values"):
                pooled[k] = [v for r in rows for v in r[k]]
            elif k != "n":
                vals = [r[k] for r in rows if r.get(k) is not None]
                pooled[k] = _mean(vals) if vals else None
        per_dose[d] = pooled
    controls = {}
    for k in summaries[0]["controls"]:
        if k == "generic":
            controls[k] = {c: _mean(s["controls"][k][c] for s in summaries) for c in COLOURS}
        else:
            controls[k] = _mean(s["controls"][k] for s in summaries)
    ps = [s["prior_subset"] for s in summaries]
    n_ps = sum(p["n"] for p in ps)
    prior_subset = dict(n=n_ps, p_on=(sum(p["p_on"] * p["n"] for p in ps if p["n"]) / n_ps) if n_ps else None,
                        p_off=(sum(p["p_off"] * p["n"] for p in ps if p["n"]) / n_ps) if n_ps else None)
    bs = [s["base_rate_subset"] for s in summaries]
    n_bs = sum(p["n"] for p in bs)
    base_rate_subset = dict(n=n_bs, p_on=(sum(p["p_on"] * p["n"] for p in bs if p["n"]) / n_bs) if n_bs else None,
                            p_off=(sum(p["p_off"] * p["n"] for p in bs if p["n"]) / n_bs) if n_bs else None,
                            names_base_colour=True)
    for d in DOSES:   # min over banks of the per-owner minimum candidate mass
        mins = [s["per_dose"][d].get("mass_on_min") for s in summaries]
        per_dose[d]["mass_on_min"] = min((m for m in mins if m is not None), default=None)
    by_prior_bin = {}
    for scope in summaries[0].get("by_prior_bin", {}):
        bins = {}
        for lab in summaries[0]["by_prior_bin"][scope]:
            parts = [s["by_prior_bin"][scope][lab] for s in summaries if lab in s["by_prior_bin"].get(scope, {})]
            vals = {k: [v for p in parts for v in p["values"].get(k, [])] for k in parts[0]["values"]}
            bins[lab] = dict(n=sum(p["n"] for p in parts), values=vals,
                             **{k: (_mean(v) if v else None) for k, v in vals.items()})
        by_prior_bin[scope] = bins
    lesson_per_dose = {}
    for d in DOSES:
        rows = [s["lesson_per_dose"][d] for s in summaries]
        lesson_per_dose[d] = dict(n=sum(r["n"] for r in rows),
                                  **{k: _mean(r[k] for r in rows if r.get(k) is not None) for k in rows[0] if k != "n"})
    return dict(per_dose=per_dose, controls=controls, prior_subset=prior_subset,
                base_rate_subset=base_rate_subset, by_prior_bin=by_prior_bin,
                prior_bin_edges=summaries[0].get("prior_bin_edges", PRIOR_BIN_EDGES),
                lesson_per_dose=lesson_per_dose,
                banks=[s["bank"] for s in summaries], lam=summaries[0].get("lam", 1.0),
                adapter_meta=summaries[0].get("adapter_meta") or {})


def evaluate_gates(s: dict, retention: float | None = None, th: dict = GATES, seed: int = 0) -> dict:
    """Section 2.4 engineering gates at dose 16, held-out paraphrases, no
    observation in context. Each gate: value, threshold, pass (None = not
    evaluable)."""
    d16, d4, d1 = s["per_dose"][16], s["per_dose"][4], s["per_dose"][1]
    c = s["controls"]
    boot = paired_bootstrap(d16["I_d_values"], seed=seed)
    g = {}
    g["G1_p_on"] = dict(value=d16["p_on"], threshold=th["p_on"], passed=d16["p_on"] is not None and d16["p_on"] >= th["p_on"])
    g["G1_d_p"] = dict(value=d16["d_p"], threshold=th["d_p"], passed=d16["d_p"] is not None and d16["d_p"] >= th["d_p"])
    # G2: the literal 0.6 -> 0.9 calibration. Natural 0.55-0.65 OFF-prior subset first; when it is
    # too small, the memo's fallback: the explicit fleet base-rate prompt (which names the base
    # colour by design), accepted as a 0.6 prior only if its OFF prior really sits in the window.
    ps, brs = s["prior_subset"], s["base_rate_subset"]
    lo, hi = th["prior_window"]
    if ps["n"] >= th["min_prior_subset"]:
        g["G2_prior_subset"] = dict(value=ps["p_on"], n=ps["n"], p_off=ps["p_off"], subset="natural",
                                    threshold=th["prior_p_on"], passed=ps["p_on"] >= th["prior_p_on"],
                                    note="natural 0.55-0.65 OFF-prior subset (pre-registered)")
    elif brs["n"] >= th["min_prior_subset"] and brs["p_off"] is not None:
        in_window = lo <= brs["p_off"] <= hi
        g["G2_prior_subset"] = dict(value=brs["p_on"], n=brs["n"], p_off=brs["p_off"], subset="base_rate",
                                    threshold=th["prior_p_on"],
                                    passed=(brs["p_on"] >= th["prior_p_on"]) if in_window else None,
                                    note=("natural subset n=%d < %d; fallback = explicit fleet base-rate prompt "
                                          "(names the base colour by design); prompt OFF prior %.3f %s [%.2f, %.2f]%s"
                                          % (ps["n"], th["min_prior_subset"], brs["p_off"],
                                             "inside" if in_window else "OUTSIDE", lo, hi,
                                             "" if in_window else " -> not a literal 0.6->0.9 calibration; not gated")))
    else:
        g["G2_prior_subset"] = dict(value=ps["p_on"], n=ps["n"], p_off=ps["p_off"], subset=None,
                                    threshold=th["prior_p_on"], passed=None,
                                    note="neither the natural 0.55-0.65 subset nor the base-rate subset is populated")
    g["G3_trigger_nats"] = dict(value=d16["term1"], threshold=th["trigger_nats"], passed=d16["term1"] is not None and d16["term1"] >= th["trigger_nats"])
    g["G4_I_d_ci"] = dict(value=boot["mean"], lo=boot["lo"], hi=boot["hi"], n=boot["n"], threshold=0.0,
                          passed=boot["lo"] is not None and boot["lo"] > 0)
    g["G5_unrelated"] = dict(value=c["unrelated_shift"], threshold=th["unrelated"],
                             passed=c["unrelated_shift"] is not None and c["unrelated_shift"] <= th["unrelated"],
                             parts=dict(unexposed=c["unexposed_abs_d_p"], similar=c["similar_abs_d_p"],
                                        bicycle=c["bicycle_abs_d_p"], generic=c["generic_abs_d_p"]))
    ctx_on, ctx_off = d16["ctx_on"], d16["ctx_off"]
    g["G6_in_context"] = dict(value=ctx_on, off=ctx_off, threshold=th["ctx_on"],
                              passed=ctx_on is not None and ctx_on >= th["ctx_on"] and ctx_on >= ctx_off - th["ctx_degrade"])
    rp_on, rp_off = d16["repaint_on"], d16["repaint_off"]
    g["G6_repaint"] = dict(value=rp_on, off=rp_off, threshold=th["ctx_on"],
                           passed=rp_on is not None and rp_on >= th["ctx_on"] and rp_on >= rp_off - th["ctx_degrade"])
    g["G7_retention"] = dict(value=retention, threshold=th["retention"],
                             passed=(None if retention is None else retention >= th["retention"]))
    sat = d4["p_on"] is not None and d4["p_on"] >= th["saturation"]
    step_ok = (d16["d_p"] is not None and d4["d_p"] is not None and (sat or d16["d_p"] >= d4["d_p"] + th["dose_step"]))
    trend = (d16["d_p"] is not None and d1["d_p"] is not None and d16["d_p"] > d1["d_p"] and d16["d_p"] >= s["per_dose"][0]["d_p"])
    g["G8_dose_trend"] = dict(value=dict(d0=s["per_dose"][0]["d_p"], d1=d1["d_p"], d4=d4["d_p"], d16=d16["d_p"]),
                              saturated_at_4=sat, passed=bool(step_ok and trend))
    # G9 (memo: 'verify that raw candidate-set mass has not collapsed'): pooled dose-16 mass ON
    # >= mass_ratio x mass OFF and >= an absolute floor; the per-owner minimum is reported.
    m_on, m_off = d16["mass_on"], d16["mass_off"]
    g["G9_mass"] = dict(value=m_on, off=m_off, min_owner=d16.get("mass_on_min"),
                        threshold=f">= {th['mass_ratio']:g} x OFF and >= {th['mass_floor']:g}",
                        passed=(None if (m_on is None or m_off is None)
                                else bool(m_on >= th["mass_ratio"] * m_off and m_on >= th["mass_floor"])))
    g["passed"] = [k for k, v in g.items() if isinstance(v, dict) and v.get("passed") is True]
    g["failed"] = [k for k, v in g.items() if isinstance(v, dict) and v.get("passed") is False]
    return g


def interpret(s: dict, g: dict, th: dict = GATES) -> dict:
    """Pre-registered reading (memo 2.4): guide / rewrite-habit / nothing /
    surface-binding-only, plus mass-collapse (candidate-set mass gate G9
    failed: the normalized probabilities are not trustworthy, so 'guide' is
    withheld). High confidence alone is not a rewrite; specificity and
    revisability decide. A large training-text fit gain with I_d ~ 0 is
    flagged as storage-without-extraction (memo section 1)."""
    d16 = s["per_dose"][16]
    c = s["controls"]
    gain = d16["d_p"] if d16["d_p"] is not None else 0.0
    exact_gain = max(x for x in [d16.get("exact_short_d_p") or 0.0, d16.get("exact_ante_d_p") or 0.0])
    textfit = max(x for x in [d16.get("textfit_short_gain") or 0.0, d16.get("textfit_ante_gain") or 0.0])
    reasons = []
    ctx_broken = (d16["ctx_off"] is not None and d16["ctx_off"] >= th["ctx_on"]
                  and d16["ctx_on"] is not None and d16["ctx_on"] < d16["ctx_off"] - th["ctx_degrade"])
    revisable = g["G6_repaint"]["passed"] is not False or (d16["repaint_on"] is not None and d16["repaint_off"] is not None
                                                          and d16["repaint_on"] >= d16["repaint_off"] - th["ctx_degrade"])
    spill = c["unrelated_shift"] is not None and c["unrelated_shift"] > th["unrelated"]
    swapped = c["swapped_d_p"] is not None and c["swapped_d_p"] > th["swapped_d_p"]
    mass_ok = g.get("G9_mass", {}).get("passed")
    if mass_ok is False:
        label = "mass-collapse"
        reasons.append(f"candidate-set mass collapsed: ON {d16['mass_on']:.3f} vs OFF {d16['mass_off']:.3f} "
                       f"(gate {g['G9_mass']['threshold']}); normalized P not interpretable")
    elif ctx_broken:
        label = "rewrite-habit"
        reasons.append("adapter degrades in-context answering below OFF")
    elif gain < th["min_gain"]:
        if exact_gain >= th["exact_gain"]:
            label = "surface-binding-only"
            reasons.append(f"exact cue gain {exact_gain:.2f} but paraphrase gain {gain:.2f}")
        else:
            label = "nothing"
            reasons.append(f"paraphrase gain {gain:.2f} < {th['min_gain']}")
        if textfit >= th["textfit_storage"]:
            reasons.append(f"storage-without-extraction: training-text fit gain {textfit:.2f} nats/token "
                           f"with I_d {_fmt(d16.get('I_d'))} (training-text fit, not retrievable memory)")
    elif spill or (not revisable) or swapped:
        label = "rewrite-habit"
        if spill:
            reasons.append(f"unrelated shift {c['unrelated_shift']:.3f} > {th['unrelated']}")
        if not revisable:
            reasons.append("old memory overrides the explicit repaint")
        if swapped:
            reasons.append(f"owner's colour bleeds onto the partner's cue: swapped dP {c['swapped_d_p']:.3f} > {th['swapped_d_p']}")
    else:
        label = "guide"
        if not g["G8_dose_trend"]["passed"]:
            reasons.append("dose trend not positive/saturating as required")
        unmet = [k for k in g["failed"] if k not in ("G7_retention", "G2_prior_subset")]
        if unmet:
            reasons.append("gates not met: " + ", ".join(unmet))
    return dict(label=label, reasons=reasons, gain=gain, exact_gain=exact_gain, textfit_gain=textfit,
                unrelated_shift=c["unrelated_shift"], revisable=bool(revisable), mass_ok=mass_ok,
                gates_passed=g["passed"], gates_failed=g["failed"])

# ---------------------------------------------------------------------------
# report: markdown per arm, gates, interpretation, trajectories, finalist
# ---------------------------------------------------------------------------
def _fmt(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, (int, float)):
        return f"{x:.{nd}f}" if isinstance(x, float) else str(x)
    return str(x)


def parse_tag(tag: str) -> dict:
    m = re.match(r"bank(\d+)__(\w+?)__(within|across)__sleep(\d+)__r(\d+)", tag)
    if not m:
        return {}
    return dict(bank=int(m.group(1)), cell=m.group(2), arm=m.group(3), sleep=int(m.group(4)),
                rank=int(m.group(5)))


def load_evals(run_dir: str) -> list[dict]:
    d = os.path.join(run_dir, "eval")
    if not os.path.isdir(d):
        return []
    out = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            ev = read_json(os.path.join(d, f))
            meta = dict(parse_tag(ev.get("tag", "")))
            meta.update({k: v for k, v in (ev.get("meta") or {}).items() if v is not None})
            if "cell" not in meta:
                continue
            ev["meta"] = meta
            out.append(ev)
    return out


def _md_table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(_fmt(x) for x in r) + " |")
    return "\n".join(out)


def _cell_label(cell: str) -> str:
    w, r, sh = CELLS.get(cell, (cell, "", False))
    return f"{cell} ({w} x {r}{', scrambled-binding control' if sh else ''})"


def _ci(values: list[float]) -> str:
    bs = paired_bootstrap(values)
    return f"{_fmt(bs['mean'])} [{_fmt(bs['lo'])}, {_fmt(bs['hi'])}]" if bs["n"] else "-"


def render_arm_markdown(cell: str, arm: str, rank: int, lam: float, by_sleep: dict,
                        ref_sleep: int, gates: dict, interp: dict, retention: dict | None,
                        notes: list[str] | None = None) -> str:
    ref = by_sleep[ref_sleep]
    am = ref["pooled"].get("adapter_meta") or {}
    L = [f"# Memory dose test -- cell {_cell_label(cell)}, arm {arm}, rank {rank}, lambda {lam:g}",
         "", SYNTHETIC_NOTE, "",
         "Primary endpoint: held-out paraphrases (p1-p3), no observation in context. "
         "term1 = ON-OFF log-odds(a vs b) at the owner's cue; term2 = the same at the matched "
         "non-trigger (unseen similar id, same a and b); I_d = term1 - term2; b = the strongest "
         "alternative colour under OFF. P = candidate-normalized over the four colours; P raw = the "
         "model's raw probability of the planted colour (all surface variants); mass = raw probability "
         "of the four colours together. 95% CIs: paired bootstrap over owners, per bank and pooled.", ""]
    L += [f"- corpus ordering: **{am.get('ordering') or 'unknown'}** "
          + ("(prior-first session order as compile_sleep + train_adapter.py; the within-session and "
             "across-sleep arms hold the same item set in a different order and were fitted separately)"
             if am.get("ordering") == "chronological" else
             "(content-derived shuffle: identical item sets give byte-identical corpora, so the "
             "within/across sleep-4 identity holds BY CONSTRUCTION, not as a measurement)"
             if am.get("ordering") == "content" else "(not recorded in the adapter's train_meta.json)")]
    for n in (notes or []):
        L.append(f"- {n}")
    L += ["", f"## Dose response after sleep {ref_sleep}", ""]
    rows = []
    for b, s in sorted(ref["banks"].items()):
        for d in DOSES:
            r = s["per_dose"][d]
            rows.append([f"bank{b}", d, r["n"], f"{_fmt(r['p_raw_off'])}/{_fmt(r['p_raw_on'])}",
                         r["p_off"], r["p_on"], r["d_p"], r["term1"], r["term2"],
                         _ci(r["I_d_values"]) if d > 0 else "-", f"{_fmt(r['mass_off'])}/{_fmt(r['mass_on'])}",
                         r["exact_short_d_p"], r["exact_ante_d_p"]])
    for d in DOSES:
        r = ref["pooled"]["per_dose"][d]
        rows.append(["pooled", d, r["n"], f"{_fmt(r['p_raw_off'])}/{_fmt(r['p_raw_on'])}",
                     r["p_off"], r["p_on"], r["d_p"], r["term1"], r["term2"],
                     _ci(r["I_d_values"]) if d > 0 else "-",
                     f"{_fmt(r['mass_off'])}/{_fmt(r['mass_on'])}", r["exact_short_d_p"], r["exact_ante_d_p"]])
    L.append(_md_table(["bank", "dose", "n", "P raw OFF/ON", "P OFF", "P ON", "dP", "term1 (nats)", "term2 (nats)",
                        "I_d [95% CI]", "mass OFF/ON", "exact-short dP", "exact-ante dP"], rows))
    edges = ref["pooled"].get("prior_bin_edges", PRIOR_BIN_EDGES)
    L += ["", f"## By pre-registered OFF-prior bin (dose 16; bin = stored pre-assignment OFF prior of the "
          f"assigned colour, edges {edges}; assignment was {'prior-matched' if am.get('prior_match') else 'random balanced'})", ""]
    rows = []
    for b, s in sorted(ref["banks"].items()):
        for lab, r in s.get("by_prior_bin", {}).get("dose16", {}).items():
            rows.append([f"bank{b}", lab, r["n"], f"{_fmt(r['p_raw_off'])}/{_fmt(r['p_raw_on'])}",
                         r["p_off"], r["p_on"], r["d_p"], _ci(r["values"].get("I_d", []))])
    for lab, r in ref["pooled"].get("by_prior_bin", {}).get("dose16", {}).items():
        rows.append(["pooled", lab, r["n"], f"{_fmt(r['p_raw_off'])}/{_fmt(r['p_raw_on'])}",
                     r["p_off"], r["p_on"], r["d_p"], _ci(r["values"].get("I_d", []))])
    L.append(_md_table(["bank", "OFF-prior bin", "n", "P raw OFF/ON", "P OFF", "P ON", "dP", "I_d [95% CI]"], rows))
    L += ["", "## Controls (exposed owners; absolute normalized-probability shifts)", "",
          "swapped id = the partner's own fact cue (same dose, different colour) re-read for the OWNER's colour: "
          "dP > 0 means the owner's colour bleeds onto another exposed owner's cue (habit signal, gate "
          f"{GATES['swapped_d_p']}); its log-odds(a vs b) is dominated by the partner's own learning and is shown only.", ""]
    rows = []
    for b, s in sorted(ref["banks"].items()):
        c = s["controls"]
        rows.append([f"bank{b}", c["unexposed_abs_d_p"], c["similar_abs_d_p"], c["bicycle_abs_d_p"],
                     c["generic_abs_d_p"], c["swapped_d_p"], c["swapped_d_logodds"], c["unrelated_shift"]])
    c = ref["pooled"]["controls"]
    rows.append(["pooled", c["unexposed_abs_d_p"], c["similar_abs_d_p"], c["bicycle_abs_d_p"],
                 c["generic_abs_d_p"], c["swapped_d_p"], c["swapped_d_logodds"], c["unrelated_shift"]])
    L.append(_md_table(["bank", "unexposed |dP|", "similar id |dP|", "bicycle |dP|", "generic car |dP|",
                        "swapped dP (owner colour at partner cue)", "swapped dlog-odds (shown only)", "unrelated shift"], rows))
    L += ["", "## I_d by matched non-trigger type (dose 16; term1 minus the ON-OFF log-odds of the same a vs b at the control cue)", ""]
    rows = []
    for b, s in sorted(ref["banks"].items()):
        r = s["per_dose"][16]
        rows.append([f"bank{b}", r["term1"], r["I_d"], r["I_d_unexposed"], r["I_d_bicycle"], r["I_d_generic"]])
    r = ref["pooled"]["per_dose"][16]
    rows.append(["pooled", r["term1"], r["I_d"], r["I_d_unexposed"], r["I_d_bicycle"], r["I_d_generic"]])
    L.append(_md_table(["bank", "term1 (trigger)", "I_d vs similar id (primary)", "vs unexposed owner", "vs bicycle",
                        "vs generic car"], rows))
    L += ["", "## Training-text fit vs I_d (memo section 1: a large text-fit gain with I_d ~ 0 is storage without extraction)", "",
          "text-fit gain = per-token log-likelihood gain ON-OFF (nats/token) of the owner's exact training text: "
          "the A/B short piece (header + child target) and the C/D antecedent piece (observation -> child target). "
          "This is training-text fit, not evidence of retrievable episodic memory.", ""]
    rows = []
    for b, s in sorted(ref["banks"].items()):
        for d in DOSES:
            r = s["per_dose"][d]
            rows.append([f"bank{b}", d, r.get("textfit_short_nll_off"), r.get("textfit_short_gain"),
                         r.get("textfit_ante_nll_off"), r.get("textfit_ante_gain"), r["I_d"], r["d_p"]])
    for d in DOSES:
        r = ref["pooled"]["per_dose"][d]
        rows.append(["pooled", d, r.get("textfit_short_nll_off"), r.get("textfit_short_gain"),
                     r.get("textfit_ante_nll_off"), r.get("textfit_ante_gain"), r["I_d"], r["d_p"]])
    L.append(_md_table(["bank", "dose", "short NLL OFF (nats/tok)", "short text-fit gain", "antecedent NLL OFF",
                        "antecedent text-fit gain", "I_d", "dP"], rows))
    L += ["", "## Observation in context (before the ~1,024-token distractor; adjacent on a subset; explicit repaint override)", ""]
    rows = []
    for b, s in sorted(ref["banks"].items()):
        for d in DOSES:
            r = s["per_dose"][d]
            rows.append([f"bank{b}", d, r["ctx_off"], r["ctx_on"], f"{_fmt(r['adj_off'])}/{_fmt(r['adj_on'])}",
                         r["repaint_off"], r["repaint_on"], r["repaint_old_on"]])
    for d in DOSES:
        r = ref["pooled"]["per_dose"][d]
        rows.append(["pooled", d, r["ctx_off"], r["ctx_on"], f"{_fmt(r['adj_off'])}/{_fmt(r['adj_on'])}",
                     r["repaint_off"], r["repaint_on"], r["repaint_old_on"]])
    L.append(_md_table(["bank", "dose", "ctx P OFF", "ctx P ON", "adjacent OFF/ON", "repaint P(new) OFF",
                        "repaint P(new) ON", "repaint P(old) ON"], rows))
    ps, bs_ = ref["pooled"]["prior_subset"], ref["pooled"]["base_rate_subset"]
    g2 = gates.get("G2_prior_subset", {})
    L += ["", "## Calibration subsets (dose 16; the literal 0.6 -> 0.9 test)", "",
          f"- natural 0.55-0.65 OFF-prior subset (pre-registered from the stored OFF distribution): "
          f"n={ps['n']}, P OFF={_fmt(ps['p_off'])}, P ON={_fmt(ps['p_on'])}",
          f"- base-rate prompt subset (dose-16 owners planted with the base colour): n={bs_['n']}, "
          f"P OFF={_fmt(bs_['p_off'])}, P ON={_fmt(bs_['p_on'])}. The fleet base-rate prompt NAMES the base colour "
          f"by design (memo fallback: an explicit prior, not a held-out cue); it counts as a 0.6 prior only if its "
          f"OFF prior sits in [{GATES['prior_window'][0]}, {GATES['prior_window'][1]}].",
          f"- G2 evaluated on: **{g2.get('subset') or 'none'}** -- {g2.get('note', '')}", ""]
    L += ["## Conditional lessons (nonce tool: action A in mode X, B in mode Y; a=A, b=B; cue ends before the action)", ""]
    rows = []
    for b, s in sorted(ref["banks"].items()):
        for d in DOSES:
            r = s["lesson_per_dose"][d]
            rows.append([f"bank{b}", d, r["n"], r["trigger"], r["notrigger"], r["reversed"], r["interaction"],
                         r["selectivity"], r["exact"], f"{_fmt(r['p_off_trigger'])}/{_fmt(r['p_on_trigger'])}"])
    for d in DOSES:
        r = ref["pooled"]["lesson_per_dose"][d]
        rows.append(["pooled", d, r["n"], r["trigger"], r["notrigger"], r["reversed"], r["interaction"],
                     r["selectivity"], r["exact"], f"{_fmt(r['p_off_trigger'])}/{_fmt(r['p_on_trigger'])}"])
    L.append(_md_table(["bank", "dose", "n", "trigger dlo", "no-trigger dlo", "reversed dlo",
                        "interaction (trig-notrig)", "selectivity (trig-rev)", "exact-cue dlo",
                        "P(A|trigger) OFF/ON"], rows))
    L += ["", f"## Gates (memo 2.4; pooled banks, sleep {ref_sleep}, dose 16, paraphrases, no context)", ""]
    rows = []
    for k, v in gates.items():
        if not isinstance(v, dict):
            continue
        extra = ""
        if k == "G4_I_d_ci":
            extra = f"CI [{_fmt(v['lo'])}, {_fmt(v['hi'])}], n={v['n']}"
        elif k == "G5_unrelated":
            extra = ", ".join(f"{a}={_fmt(b)}" for a, b in v["parts"].items())
        elif k in ("G6_in_context", "G6_repaint"):
            extra = f"OFF={_fmt(v['off'])}"
        elif k == "G8_dose_trend":
            extra = ", ".join(f"{a}={_fmt(b)}" for a, b in v["value"].items()) + f", saturated_at_4={v['saturated_at_4']}"
        elif k == "G2_prior_subset":
            extra = f"subset={v.get('subset')}, n={v['n']}, P OFF={_fmt(v.get('p_off'))}; {v.get('note', '')}"
        elif k == "G9_mass":
            extra = f"OFF={_fmt(v['off'])}, min per-owner ON={_fmt(v.get('min_owner'))}"
        val = v["value"] if not isinstance(v["value"], dict) else ""
        rows.append([k, val, v.get("threshold"), "PASS" if v["passed"] else ("FAIL" if v["passed"] is False else "n/a"), extra])
    L.append(_md_table(["gate", "value", "threshold", "result", "detail"], rows))
    L += ["", f"## Interpretation: **{interp['label']}**", ""]
    L += [f"- {r}" for r in interp["reasons"]] or ["- all specificity and revisability conditions met"]
    L += [f"- paraphrase gain (dose 16 dP) {_fmt(interp['gain'])}; exact-cue gain {_fmt(interp['exact_gain'])}; "
          f"training-text fit gain {_fmt(interp.get('textfit_gain'))} nats/token; "
          f"unrelated shift {_fmt(interp['unrelated_shift'])}; revisable by present evidence: {interp['revisable']}; "
          f"candidate mass intact: {interp.get('mass_ok')}"]
    if len(by_sleep) > 1:
        L += ["", "## Trajectory (dose 16, paraphrases, no context; pooled banks)", ""]
        rows = []
        for k in sorted(by_sleep):
            r = by_sleep[k]["pooled"]["per_dose"][16]
            rows.append([k, f"{_fmt(r['p_raw_off'])}/{_fmt(r['p_raw_on'])}", r["p_off"], r["p_on"], r["d_p"],
                         _ci(r["I_d_values"]), f"{_fmt(r['mass_off'])}/{_fmt(r['mass_on'])}",
                         by_sleep[k]["pooled"]["controls"]["unrelated_shift"], by_sleep[k]["pooled"]["per_dose"][16]["repaint_on"]])
        L.append(_md_table(["sleep", "P raw OFF/ON", "P OFF", "P ON", "dP", "I_d [95% CI]", "mass OFF/ON",
                            "unrelated shift", "repaint P(new) ON"], rows))
        if retention:
            L += ["", f"- retention after two interference sleeps: dP sleep {retention['from']} = {_fmt(retention['gain_ref'])}, "
                  f"sleep {retention['to']} = {_fmt(retention['gain_late'])}, retained fraction = {_fmt(retention['fraction'])} "
                  f"(gate >= {GATES['retention']})"]
    return "\n".join(L) + "\n"


def report_command(run_dir: str, seed: int = 0) -> dict:
    root = set_write_root(run_dir)
    manifest = read_json(os.path.join(root, "manifest.json"))
    banks = {b: read_json(os.path.join(root, "banks", f"bank{b}.json")) for b in range(manifest["n_banks"])}
    evals = load_evals(root)
    groups: dict = {}
    for ev in evals:
        m = ev["meta"]
        key = (m["cell"], m["arm"], int(m["rank"]), float(ev.get("lam", 1.0)))
        groups.setdefault(key, {}).setdefault(int(m["sleep"]), {})[int(ev["bank"])] = summarize_eval(ev, banks[int(ev["bank"])])
    results, summary_rows, lam_rows = {}, [], []
    notes = [f"colour assignment: {manifest.get('assignment', 'random balanced, after the OFF measurement')}"
             f" (prior_match={manifest.get('prior_match', False)}); OFF-prior bin edges {manifest.get('prior_bin_edges', PRIOR_BIN_EDGES)}"]
    for (cell, arm, rank, lam), by_sleep in sorted(groups.items()):
        for k, bs in by_sleep.items():
            by_sleep[k] = dict(banks=bs, pooled=pool([bs[b] for b in sorted(bs)]))
            by_sleep[k]["pooled"]["adapter_meta"]["prior_match"] = manifest.get("prior_match", False)
        cands = [k for k in by_sleep if k <= N_SLEEPS_EXPOSURE]
        ref_sleep = N_SLEEPS_EXPOSURE if N_SLEEPS_EXPOSURE in by_sleep else (max(cands) if cands else min(by_sleep))
        retention = None
        late = [k for k in by_sleep if k > N_SLEEPS_EXPOSURE]
        if N_SLEEPS_EXPOSURE in by_sleep and late:
            g4 = by_sleep[N_SLEEPS_EXPOSURE]["pooled"]["per_dose"][16]["d_p"]
            g6 = by_sleep[max(late)]["pooled"]["per_dose"][16]["d_p"]
            frac = (g6 / g4) if (g4 is not None and g6 is not None and g4 > GATES["min_gain"]) else None
            retention = {"from": N_SLEEPS_EXPOSURE, "to": max(late), "gain_ref": g4, "gain_late": g6, "fraction": frac}
        pooled = by_sleep[ref_sleep]["pooled"]
        gates = evaluate_gates(pooled, retention["fraction"] if retention else None, seed=seed)
        interp = interpret(pooled, gates)
        per_bank = {b: dict(gates=evaluate_gates(s, seed=seed), interpretation=interpret(s, evaluate_gates(s, seed=seed)))
                    for b, s in by_sleep[ref_sleep]["banks"].items()}
        name = f"{cell}__{arm}__r{rank}__lam{lam:g}"
        md = render_arm_markdown(cell, arm, rank, lam, by_sleep, ref_sleep, gates, interp, retention, notes=notes)
        write_text(os.path.join(root, "report", name + ".md"), md)
        d16 = pooled["per_dose"][16]
        results[name] = dict(cell=cell, arm=arm, rank=rank, lam=lam, ref_sleep=ref_sleep, sleeps=sorted(by_sleep),
                             banks=sorted(by_sleep[ref_sleep]["banks"]), gates=gates, interpretation=interp,
                             retention=retention, per_bank=per_bank, adapter_meta=pooled.get("adapter_meta"),
                             by_prior_bin=pooled.get("by_prior_bin", {}).get("dose16"),
                             headline=dict(p_off=d16["p_off"], p_on=d16["p_on"], d_p=d16["d_p"],
                                           p_raw_off=d16["p_raw_off"], p_raw_on=d16["p_raw_on"],
                                           mass_off=d16["mass_off"], mass_on=d16["mass_on"], term1=d16["term1"],
                                           term2=d16["term2"], I_d=d16["I_d"], I_d_ci=[gates["G4_I_d_ci"]["lo"], gates["G4_I_d_ci"]["hi"]],
                                           unrelated=pooled["controls"]["unrelated_shift"], ctx_on=d16["ctx_on"],
                                           repaint_on=d16["repaint_on"], lesson_interaction=pooled["lesson_per_dose"][16]["interaction"],
                                           textfit_short_gain=d16.get("textfit_short_gain"),
                                           textfit_ante_gain=d16.get("textfit_ante_gain")),
                             dose_curve={d: pooled["per_dose"][d]["d_p"] for d in DOSES},
                             lesson_curve={d: pooled["lesson_per_dose"][d]["interaction"] for d in DOSES})
        h = results[name]["headline"]
        summary_rows.append([name, ref_sleep, len(results[name]["banks"]), f"{_fmt(h['p_raw_off'])}/{_fmt(h['p_raw_on'])}",
                             h["p_off"], h["p_on"], h["d_p"], h["term1"],
                             f"{_fmt(h['I_d'])} [{_fmt(h['I_d_ci'][0])}, {_fmt(h['I_d_ci'][1])}]",
                             f"{_fmt(h['mass_off'])}/{_fmt(h['mass_on'])}", h["unrelated"],
                             h["ctx_on"], h["repaint_on"], h["lesson_interaction"],
                             f"{_fmt(h['textfit_short_gain'])}/{_fmt(h['textfit_ante_gain'])}",
                             f"{len(gates['passed'])}/{len(gates['passed']) + len(gates['failed'])}", interp["label"]])
        if lam != 1.0 or any(k2[:3] == (cell, arm, rank) and k2[3] != 1.0 for k2 in groups):
            lam_rows.append([cell, arm, rank, lam, h["d_p"], h["I_d"], h["unrelated"], h["repaint_on"], h["ctx_on"]])
    # finalist: rank 8, sleep 4, lambda 1, non-shuffled writer cells; must not spill; largest pooled I_d
    fin = None
    pool_c = [(n, r) for n, r in results.items() if r["rank"] == LORA_RANK and r["lam"] == 1.0
              and r["ref_sleep"] == N_SLEEPS_EXPOSURE and not CELLS.get(r["cell"], (0, 0, True))[2]]
    ok = [(n, r) for n, r in pool_c if r["gates"]["G5_unrelated"]["passed"]
          and r["interpretation"]["label"] not in ("rewrite-habit", "mass-collapse")
          and r["headline"]["I_d"] is not None]
    src, fallback = (ok, False) if ok else (pool_c, True)
    if src:
        n, r = max(src, key=lambda nr: (nr[1]["headline"]["I_d"] or -1e9))
        fin = dict(cell=r["cell"], arm=r["arm"], writer=CELLS[r["cell"]][0], representation=CELLS[r["cell"]][1],
                   I_d=r["headline"]["I_d"], d_p=r["headline"]["d_p"], label=r["interpretation"]["label"],
                   ordering=(r.get("adapter_meta") or {}).get("ordering"),
                   fallback=fallback, rule=("largest pooled dose-16 I_d among rank-8 sleep-4 non-scrambled cells with "
                                            "unrelated shift <= 0.03, candidate mass intact and no rewrite-habit reading; "
                                            "fallback = largest I_d"))
        write_json(os.path.join(root, "report", "finalist.json"), fin)
    orderings = sorted({(r.get("adapter_meta") or {}).get("ordering") or "unknown" for r in results.values()})
    L = ["# Memory dose test -- summary", "", SYNTHETIC_NOTE, "",
         f"Model {manifest['model']}; seed {manifest['seed']}; token budget {manifest['token_budget']}; "
         f"banks {manifest['n_banks']}; evaluated checkpoints {len(evals)}; corpus ordering {orderings}; "
         f"colour assignment {manifest.get('assignment', 'random balanced, after the OFF measurement')} "
         f"(prior_match={manifest.get('prior_match', False)}).", "",
         "## Cells at their reference sleep (dose 16, paraphrases, no context; pooled banks)", "",
         _md_table(["cell__arm__rank__lambda", "sleep", "banks", "P raw OFF/ON", "P OFF", "P ON", "dP", "term1",
                    "I_d [95% CI]", "mass OFF/ON", "unrelated", "ctx ON", "repaint ON", "lesson interaction",
                    "text-fit gain short/ante", "gates", "reading"], summary_rows)]
    if lam_rows:
        L += ["", "## Adapter-strength sweep (no retraining; lambda scales every LoRA delta)", "",
              _md_table(["cell", "arm", "rank", "lambda", "dP d16", "I_d", "unrelated", "repaint ON", "ctx ON"], lam_rows)]
    if fin:
        L += ["", f"## Finalist: cell {fin['cell']} ({fin['writer']} x {fin['representation']}), I_d={_fmt(fin['I_d'])}, "
              f"reading {fin['label']}{' (FALLBACK: no cell passed the spill gate)' if fin['fallback'] else ''}"]
    # exposure-arm comparison at sleep 4: same item set, different order (chronological) -> two fits
    arm_rows = []
    for (cell, rank, lam) in sorted({(r["cell"], r["rank"], r["lam"]) for r in results.values()}):
        w = results.get(f"{cell}__within__r{rank}__lam{lam:g}")
        a = results.get(f"{cell}__across__r{rank}__lam{lam:g}")
        if w and a and w["ref_sleep"] == N_SLEEPS_EXPOSURE and a["ref_sleep"] == N_SLEEPS_EXPOSURE:
            hw, ha = w["headline"], a["headline"]
            arm_rows.append([cell, rank, lam, hw["d_p"], ha["d_p"], hw["I_d"], ha["I_d"],
                             (hw["I_d"] - ha["I_d"]) if (hw["I_d"] is not None and ha["I_d"] is not None) else None,
                             (w.get("adapter_meta") or {}).get("ordering"),
                             (w.get("adapter_meta") or {}).get("corpus_sha") == (a.get("adapter_meta") or {}).get("corpus_sha")])
    if arm_rows:
        L += ["", "## Exposure arms at sleep 4 (within-session vs across-sleep; the memo's identity prediction)", "",
              "Both arms hold the same supervised item set after sleep 4. Under chronological ordering they differ in "
              "ORDER (within: the dose-16 pieces all sit in the session-4 block; across: spread over sessions 1-4) and "
              "were fitted separately, so a difference here is an ordering/recency effect of today's in-order trainer; "
              "under content ordering the corpora are byte-identical and the fit is reused (identity by construction).", "",
              _md_table(["cell", "rank", "lambda", "dP within", "dP across", "I_d within", "I_d across", "I_d within-across",
                         "ordering", "same corpus sha"], arm_rows)]
    ident = None
    ip = os.path.join(root, "corpora", "index.json")
    if os.path.exists(ip):
        idx_json = read_json(ip)
        ident = idx_json.get("identity_check")
        if ident:
            L += ["", f"## Corpus identity check (sleep 4, within vs across; ordering {idx_json.get('ordering', 'unknown')})", "",
                  "identical items = same multiset of supervised items (true by construction for every cell); "
                  "identical sha = same corpus including order (by construction only under content ordering).", "",
                  _md_table(["bank", "cell", "sleep", "within sha", "across sha", "identical items", "identical sha"],
                            [[i["bank"], i["cell"], i["sleep"], i["within"], i["across"],
                              i.get("identical_items"), i.get("identical_sha", i.get("identical"))] for i in ident])]
    write_text(os.path.join(root, "report", "summary.md"), "\n".join(L) + "\n")
    write_json(os.path.join(root, "report", "report.json"),
               dict(results=results, finalist=fin, n_evals=len(evals), identity_check=ident,
                    exposure_arms_sleep4=arm_rows, orderings=orderings,
                    prior_match=manifest.get("prior_match", False), gates_thresholds={k: (list(v) if isinstance(v, tuple) else v) for k, v in GATES.items()}))
    print(f"REPORT_DONE cells={len(results)} finalist={fin['cell'] if fin else None}", flush=True)
    return dict(results=results, finalist=fin)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _counter_for(args) -> TokenCounter:
    mode = getattr(args, "counter", "auto")
    if mode == "auto":
        mode = "hf" if getattr(args, "model", "mock") == "hf" else "approx"
    return TokenCounter(mode)


def main(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--run-dir", required=True)
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("--model", choices=["mock", "hf"], default="mock")
    g.add_argument("--banks", type=int, default=3)
    g.add_argument("--token-budget", type=int, default=65536)
    g.add_argument("--counter", choices=["auto", "approx", "hf"], default="auto")
    g.add_argument("--independent-owners", action="store_true",
                   help="fresh owner ids per bank (default: shared ids, counterbalanced colours)")
    g.add_argument("--n-interference", type=int, default=32)
    g.add_argument("--vary-situations", action="store_true")
    g.add_argument("--base-colour", default="red")
    g.add_argument("--distractor-tokens", type=int, default=1024)
    g.add_argument("--batch-size", type=int, default=16)
    g.add_argument("--prior-match", action="store_true",
                   help="opt-in: prior-matched balanced assignment instead of random balanced (recorded)")
    c = sub.add_parser("corpus")
    c.add_argument("--run-dir", required=True)
    c.add_argument("--bank", type=int, required=True)
    c.add_argument("--cell", default=None, help="A|B|C|D|Dshuf|Bw|Dw (or give --writer/--representation)")
    c.add_argument("--writer", choices=WRITERS, default=None)
    c.add_argument("--representation", choices=REPRESENTATIONS, default=None)
    c.add_argument("--shuffled", action="store_true")
    c.add_argument("--arm", choices=ARMS, required=True)
    c.add_argument("--sleep", type=int, required=True)
    c.add_argument("--counter", choices=["auto", "approx", "hf"], default="auto")
    c.add_argument("--model", choices=["mock", "hf"], default="mock", help="only selects the token counter")
    c.add_argument("--token-budget", type=int, default=None)
    c.add_argument("--ordering", choices=ORDERINGS, default=DEFAULT_ORDERING)
    c.add_argument("--allow-over-budget", action="store_true")
    ca = sub.add_parser("corpus-all")
    ca.add_argument("--run-dir", required=True)
    ca.add_argument("--cells", default="A,B,C,D,Dshuf")
    ca.add_argument("--arms", default=",".join(ARMS))
    ca.add_argument("--sleeps", default="1,2,3,4,5,6")
    ca.add_argument("--counter", choices=["auto", "approx", "hf"], default="auto")
    ca.add_argument("--model", choices=["mock", "hf"], default="mock", help="only selects the token counter")
    ca.add_argument("--token-budget", type=int, default=None)
    ca.add_argument("--ordering", choices=ORDERINGS, default=DEFAULT_ORDERING)
    ca.add_argument("--allow-over-budget", action="store_true")
    t = sub.add_parser("train")
    t.add_argument("--run-dir", required=True)
    t.add_argument("--corpus", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--model", choices=["mock", "hf"], default="hf")
    t.add_argument("--rank", type=int, default=LORA_RANK)
    t.add_argument("--epochs", type=int, default=TRAIN_EPOCHS)
    t.add_argument("--lr", type=float, default=TRAIN_LR)
    t.add_argument("--seed", type=int, default=0)
    t.add_argument("--max-steps", type=int, default=None)
    t.add_argument("--measure-only", action="store_true", help="stop after the throughput probe; no adapter saved")
    t.add_argument("--grad-checkpoint", action="store_true")
    t.add_argument("--mock-profile", default="guide", choices=["guide", "habit", "nothing", "surface"])
    t.add_argument("--no-reuse", action="store_true")
    e = sub.add_parser("evaluate")
    e.add_argument("--run-dir", required=True)
    e.add_argument("--bank", type=int, required=True)
    e.add_argument("--adapter", default=None, help="adapter dir, or 'none' for the frozen model only")
    e.add_argument("--tag", required=True, help="e.g. bank0__D__across__sleep4__r8")
    e.add_argument("--model", choices=["mock", "hf"], default="mock")
    e.add_argument("--lambdas", default="1", help="comma list; 0 must reproduce OFF")
    e.add_argument("--adjacent-subset", type=int, default=4)
    e.add_argument("--batch-size", type=int, default=16)
    e.add_argument("--seed", type=int, default=0)
    for k in ("cell", "arm"):
        e.add_argument(f"--{k}", default=None)
    e.add_argument("--sleep", type=int, default=None)
    e.add_argument("--rank", type=int, default=None)
    r = sub.add_parser("report")
    r.add_argument("--run-dir", required=True)
    r.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    if args.cmd == "generate":
        scorer = load_scorer(args.model, None, batch_size=args.batch_size, seed=args.seed)
        out = generate_run(args.run_dir, args.seed, scorer, _counter_for(args), n_banks=args.banks,
                           shared_owners=not args.independent_owners, token_budget=args.token_budget,
                           n_interference=args.n_interference, vary_situations=args.vary_situations,
                           base_colour=args.base_colour, distractor_tokens=args.distractor_tokens,
                           prior_match=args.prior_match)
        print(f"GENERATE_DONE banks={len(out['banks'])} run_dir={args.run_dir} prior_match={args.prior_match}")
    elif args.cmd == "corpus":
        root = set_write_root(args.run_dir)
        manifest = read_json(os.path.join(root, "manifest.json"))
        bank = read_json(os.path.join(root, "banks", f"bank{args.bank}.json"))
        if args.cell:
            writer, rep, shuf = CELLS[args.cell]
            cell = args.cell
        else:
            writer, rep, shuf = args.writer, args.representation, args.shuffled
            cell = f"{writer}-{rep}{'-shuf' if shuf else ''}"
        cp = build_corpus(bank, args.arm, args.sleep, writer, rep, _counter_for(args),
                          args.token_budget or manifest["token_budget"], shuffled=shuf, ordering=args.ordering)
        if cp["stats"]["over_budget"] and not args.allow_over_budget:
            print(f"CORPUS_OVER_BUDGET content_tokens={cp['stats']['content_tokens']} budget={cp['token_budget']}")
            sys.exit(4)
        p = write_json(os.path.join(cell_dir(root, args.bank, cell, args.arm, args.sleep), "corpus.json"), cp)
        print(f"CORPUS_DONE {p} items={cp['stats']['n_items']} tokens={cp['stats']['n_tokens']} sha={cp['sha']} "
              f"items_sha={cp['items_sha']} ordering={cp['ordering']}")
    elif args.cmd == "corpus-all":
        try:
            out = corpus_all(args.run_dir, _counter_for(args), cells=args.cells.split(","),
                             arms=args.arms.split(","), sleeps=[int(x) for x in args.sleeps.split(",")],
                             token_budget=args.token_budget, ordering=args.ordering,
                             strict_budget=not args.allow_over_budget)
        except RuntimeError as exc:
            print(f"CORPUS_ALL_FAILED {exc}")
            sys.exit(4)
        n_items = sum(1 for i in out["identity_check"] if i["identical_items"])
        n_sha = sum(1 for i in out["identity_check"] if i["identical_sha"])
        budget = read_json(os.path.join(os.path.expanduser(args.run_dir), "corpora", "index.json"))["token_budget"]
        print(f"CORPUS_ALL_DONE corpora={len(out['index'])} ordering={out['ordering']} "
              f"sleep4_identical_items={n_items}/{len(out['identity_check'])} "
              f"sleep4_identical_sha={n_sha}/{len(out['identity_check'])} "
              f"max_content_tokens={out['max_content_tokens']} budget={budget} over_budget={len(out['over_budget'])}")
    elif args.cmd == "train":
        train_command(args.run_dir, args.corpus, args.out, model=args.model, rank=args.rank, epochs=args.epochs,
                      lr=args.lr, seed=args.seed, max_steps=args.max_steps, measure_only=args.measure_only,
                      grad_checkpoint=args.grad_checkpoint, mock_profile=args.mock_profile, no_reuse=args.no_reuse)
    elif args.cmd == "evaluate":
        lams = [float(x) for x in args.lambdas.split(",") if x != ""]
        meta = dict(cell=args.cell, arm=args.arm, sleep=args.sleep, rank=args.rank)
        evaluate_command(args.run_dir, args.bank, args.adapter, args.tag, model=args.model, lambdas=lams,
                         adjacent_subset=args.adjacent_subset, batch_size=args.batch_size, seed=args.seed, meta=meta)
    elif args.cmd == "report":
        report_command(args.run_dir, seed=args.seed)


if __name__ == "__main__":
    main()
