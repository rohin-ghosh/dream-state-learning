"""Sleep compile v3 — three write variants over the SAME ledger rows, each a
corpus.json the v3 trainer (organism_v6/train_adapter_v3.py) accepts.

  python -m organism_v6.sleep_compile_v3 --ledger <life>/ledger.jsonl \
      --out <dir> --variants A,B,C [--gym compiler] [--max-episodes 512] \
      [--recorded-a <life>/sleep_0512/corpus.json] [--think none] \
      [--tokenizer auto|none|<name>] [--max-seq-tokens 7168] [--views both|episode|local] \
      [--cell-name B_match --token-budget N]

  A  today's write: sleep_compile.compile_sleep is CALLED (never copied) —
     success-filtered, THINK-restated pieces plus PRINCIPLE lines — and its
     string corpus is wrapped as whole-text targets. It is the legacy
     comparator of pretest P1 (W0); its targets are NOT child-only text (the
     restater's and the principles' words are in the loss), which the
     manifest says in so many words. With --recorded-a the corpus recorded
     by the life itself is used instead of re-running the THINK calls; the
     recorded exemplars are filtered for held-out ids and the filtered v1-shaped
     corpus is written to <out>/A/legacy/corpus.json for the frozen v1 trainer.
  B  the two-scale + neighbourhood write of Astra memo 1 section 2.2 and
     CHILD_MECHANISM_v7 section 2.2:
       episode view  — the chronological transcript of one episode instance
                       (goal/metric head, intro, then chunk, its [OUTCOME]
                       lines, next chunk, ...); harness text is context with
                       zero loss, every child chunk is a target; causal order
                       so no pre-action thought sees its own outcome;
                       overlapping windows for long episodes SIZED IN TOKENS
                       (head + overlap + body <= --max-seq-tokens minus a
                       reserve, so the trainer never truncates them), each
                       target scored exactly once, truncation logged;
       local view    — ONE child chunk as the target with its REAL antecedent
                       context: the task text (GOAL/METRIC as stored in the
                       prompt the child saw), then a bounded window of the
                       actual transcript before it (last outcome, last action,
                       earlier chunks); no fabricated header, no parent
                       hindsight;
       reflection    — private reflection rows are their own episode-view
                       items (the harness summary masked, the child's chunks
                       targets);
     --views episode gives scale 1 alone (P1's W1s cell), --views local the
     short windows alone. 50:50 supervised-token budget between the views by
     construction (every chunk is a target once per view); --view-ratio /
     --token-budget subsample to another split and log what was dropped; no
     dedup, no caps on repeats; a stable neighbourhood key per item (`group`:
     gym + family/program) so the trainer packs related items with attention
     isolation and shuffles group blocks per epoch; target-token mass logged
     by category (boilerplate / action / revision / repeat / unexecuted_act /
     thought / reflection), by view, by gym and by episode length, plus the
     mass of child text that echoes harness lines (harness_echo), truncation
     counts, per-row exposures (a chunk is a target in both views), and the
     head / intro conditioning that was actually available.
  C  TMEM-aligned (Ren et al., arXiv 2606.04536, Fig. 1 / Sec. 5.1): the
     supervision is a JSON array of {"instruction": <question>, "output":
     <answer>} pairs "parsed into instruction–answer pairs and used for
     online SFT". TMEM's extraction is MODEL-WRITTEN (the agent itself, under
     prompt d). The thinker/compiler line forbids a compile-time restater
     from writing targets, so the extraction is rewritten as a DETERMINISTIC
     script over the child's own rows: the instruction is a harness-written
     question built only from the ledger's real fields (task text, episode
     id, turn, the last outcome), the output is VERBATIM child text — a NOTE
     the child wrote, a move the harness EXECUTED (from the act rows, never
     from a regex over the text: a Markdown-decorated ACT line the harness
     never ran is not a move that was tried), or a private-reflection chunk.
     The trainer applies the model's chat template to these pairs
     (--chat-template) and puts the loss on the answer only; whether TMEM did
     either is NOT FOUND in the paper (the manifest records both choices and
     every other deviation of the C_tmem cell from the paper's recipe).

Token counts: with --tokenizer (auto = $V6_MODEL from the local HF cache) every
span is measured with the real tokenizer exactly as the trainer encodes it
(per span, no special tokens), so compile-time masses and the trainer's
counts agree; without one, counts are chars/3 ESTIMATES (measured 3.23
chars/token on a 480-episode compiler ledger; pass lists tokenize denser),
and the manifest says which was used (token_measure).

Row hygiene: act rows are attached to their thought row by the writer's
order (batch_loop appends the acts BEFORE the tick's thought row, loop.py
after; detected per ledger by majority vote, overridable with --act-order);
acts whose thought row never arrived are dropped and counted, never glued to
an earlier episode. Parent rows (kind 'parent') are STRIPPED by default
(CHILD_MECHANISM_v7 2.1); --parent-as-context keeps them as zero-loss
context. Every corpus is leak-scanned (context included) for '[PARENT]',
'YOUR PARENTS', the brief headers and the life's own brief texts; a hit
refuses the write (LEAK_REFUSED marker) unless --allow-leak-markers.

Corpus item (all variants):
  {"spans": [[text, loss(bool), category], ...], "group": str, "view": str,
   "category": str, "order": int, "meta": {...}}
Only spans with loss=true carry gradient; for B and C every such span is
verbatim child text (after canonicalize_dialect, which only strips Markdown
decoration from marker lines — measured necessity, sleep_compile).

Nothing here touches the existing compilers: compile_sleep is called for A;
compile_native is untouched; tests/test_compiler_golden.py stays as it is.
"""
from __future__ import annotations
import argparse
import collections
import glob
import hashlib
import json
import os
import random
import re
import time

from .sleep_compile import canonicalize_dialect, compile_sleep, COMPILER_VOCAB

RECIPES = {"A": "v3_A_legacy_compile_sleep",
           "B": "v3_B_two_scale_neighbourhood",
           "C": "v3_C_tmem_qa_deterministic"}
# v7 harness rows (nudge / harness) — forward-looking: no module writes them
# today (kinds written: thought, act, note, reflection, parent, ...); they are
# zero-loss context when they appear.
HARNESS_KINDS = ("nudge", "harness")
# classroom_round / nursery_dialogue parent rows: stripped by default.
PARENT_KINDS = ("parent",)
CATEGORIES = ("boilerplate", "action", "revision", "repeat", "unexecuted_act",
              "thought", "reflection", "legacy", "tmem_qa")
CHARS_PER_TOKEN = 3.0          # conservative compile-time estimate (see module docstring)
LEAK_MARKERS = ("[PARENT]", "YOUR PARENTS", "YOUR BRIEFING FROM LAST SLEEP",
                "YOUR PARENT, ON HOW YOU HAVE BEEN THINKING")
STATE_MARK = "=== STATE ==="
DEFAULT_MAX_SEQ_TOKENS = 7168      # P1 / CHILD_MECHANISM_v7 2.2
DEFAULT_RESERVE_TOKENS = 16        # EOS + margin the trainer adds per item

_ACT = re.compile(r"^ACT:\s*(.+)$", re.M)
_NOTE = re.compile(r"^NOTE:\s*(.+)$", re.M)
_RG_ID = re.compile(r"^rg/([a-z0-9_]+)/(\d+)$")
_HARNESS_ECHO = re.compile(r"^(?:\[OUTCOME\]|CLOCK:|=== |GOAL:|METRIC:)", re.M)


class LeakError(RuntimeError):
    """The compiled corpus contains parent/brief text (CHILD_MECHANISM_v7 2.1)."""


# ---------------------------------------------------------------------------
# 0. token measurement
# ---------------------------------------------------------------------------
class TokenMeasure:
    """Length of a text in tokens. Exact with a tokenizer (the trainer encodes
    every span separately with add_special_tokens=False, so per-span counts
    add up to its exact count); otherwise chars / CHARS_PER_TOKEN."""

    def __init__(self, tok=None, chars_per_token: float = CHARS_PER_TOKEN, name=None):
        self.tok = tok
        self.cpt = float(chars_per_token)
        self.name = name
        self._cache: dict = {}

    @property
    def kind(self) -> str:
        return "exact" if self.tok is not None else "estimate"

    def describe(self) -> str:
        return f"exact ({self.name})" if self.tok is not None else f"estimate chars/{self.cpt:g}"

    def __call__(self, text) -> int:
        text = text or ""
        if self.tok is None:
            return int(round(len(text) / self.cpt))
        n = self._cache.get(text)
        if n is None:
            n = len(self.tok.encode(text, add_special_tokens=False))
            if len(self._cache) < 300000:
                self._cache[text] = n
        return n


DEFAULT_MEASURE = TokenMeasure()


def est_tokens(text: str, measure: TokenMeasure = None) -> int:
    return (measure or DEFAULT_MEASURE)(text)


def load_measure(spec: str, log=print) -> TokenMeasure:
    """--tokenizer none | auto | <HF name or path>. auto = $V6_MODEL (default
    Qwen/Qwen2.5-7B-Instruct) from the local cache. Falls back to the
    estimate and says so (the manifest records token_measure)."""
    if not spec or spec == "none":
        return TokenMeasure()
    name = os.environ.get("V6_MODEL", "Qwen/Qwen2.5-7B-Instruct") if spec == "auto" else spec
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(os.path.expanduser(name))
        return TokenMeasure(tok, name=name)
    except Exception as e:  # noqa: BLE001 — a missing tokenizer is a logged fallback
        log(f"[compile-v3] tokenizer {name!r} unavailable ({type(e).__name__}): "
            f"token counts are chars/{CHARS_PER_TOKEN:g} ESTIMATES")
        return TokenMeasure()


def _tick(r: dict) -> int:
    try:
        return int(r.get("tick", 0))
    except (TypeError, ValueError):
        return 0


def _sha256_file(path: str):
    if not path or not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 1. ledger -> episode instances (chunks with their acts and harness lines)
# ---------------------------------------------------------------------------
def detect_act_order(rows: list) -> str:
    """'acts_first' (batch_loop.EpisodeDriver.consume appends the act rows
    BEFORE the tick's thought row) or 'thought_first' (loop.py appended them
    after). Majority vote over act rows: an act row that arrives when the
    last thought row of its (clone, episode) has the same tick votes
    thought_first, otherwise acts_first. (A one-chunk episode followed by a
    replay of the same program at tick 1 casts one wrong vote in acts_first
    ledgers — 3% of instances on the measured ledger — which the majority
    absorbs.)"""
    last_thought: dict = {}
    votes: collections.Counter = collections.Counter()
    for r in rows:
        k = r.get("kind")
        ck = (r.get("clone_id"), r.get("episode_id"))
        if k == "thought" and r.get("note"):
            last_thought[ck] = _tick(r)
        elif k == "act":
            votes["thought_first" if last_thought.get(ck) == _tick(r) else "acts_first"] += 1
    if not votes:
        return "acts_first"
    return votes.most_common(1)[0][0]


def build_instances(rows: list, order: str = "auto", parent_as_context: bool = False,
                    log: dict = None) -> list:
    """Episode INSTANCES in ledger order. The gym replays the same program
    many times, so a new instance of (clone, episode_id) starts when its tick
    does not increase (parent_brief.episode_instances' rule). Act rows are
    attached by the writer's order (detect_act_order): acts_first -> an act
    waits for the NEXT thought row of its key with the same tick;
    thought_first -> an act joins the LAST chunk of its key. An act whose
    thought row never arrives (a horizon cut, a killed life) is dropped and
    counted (log['acts_orphaned']) — never glued to an earlier episode.
    first_row is the earliest ledger row of the instance (its first act /
    note rows included in acts_first order) so the horizon cut is clean.
    Parent rows are stripped by default (counted); harness rows (v7) attach
    after the last chunk seen. Note rows duplicate NOTE: lines and are
    skipped; reflection rows are handled by reflection_groups()."""
    log = log if log is not None else {}
    if order == "auto":
        order = detect_act_order(rows)
    log["act_row_order"] = order

    def _stat(k, n=1):
        log[k] = log.get(k, 0) + n

    inst: "collections.OrderedDict" = collections.OrderedDict()
    last_tick: dict = {}
    count: dict = collections.Counter()
    pending: dict = collections.defaultdict(list)
    first_since: dict = {}          # ck -> first act/note row since its last thought row
    for idx, r in enumerate(rows):
        k = r.get("kind")
        e = r.get("episode_id")
        ck = (r.get("clone_id"), e)
        if k in ("act", "note"):
            first_since.setdefault(ck, idx)
        if k == "act":
            a = dict(r)
            a["_row"] = idx
            if order == "thought_first":
                d = inst.get((ck, count[ck]))
                if d is not None and d["chunks"]:
                    d["chunks"][-1]["acts"].append(a)
                    if d["chunks"][-1]["tick"] != _tick(a):
                        _stat("acts_tick_mismatch")
                else:
                    _stat("acts_orphaned")
            else:
                pending[ck].append(a)
            continue
        if k in PARENT_KINDS and not parent_as_context:
            _stat("parent_rows_stripped")
            continue
        if k in HARNESS_KINDS or k in PARENT_KINDS:
            d = inst.get((ck, count[ck]))
            text = str(r.get("text") or r.get("note") or "").strip()
            if d is not None and text:
                (d["chunks"][-1]["after"] if d["chunks"] else d["pre"]).append(text)
                _stat("harness_rows_as_context")
            continue
        if k != "thought" or not r.get("note"):
            continue
        t = _tick(r)
        mine = [a for a in pending.get(ck, []) if _tick(a) == t]
        other = [a for a in pending.get(ck, []) if _tick(a) != t]
        if other:
            _stat("acts_orphaned", len(other))
        pending[ck] = []
        if ck not in last_tick or t <= last_tick[ck]:
            count[ck] += 1
            first_row = min([idx] + [a["_row"] for a in mine]
                            + ([first_since[ck]] if order == "acts_first" and ck in first_since else []))
            inst[(ck, count[ck])] = dict(eid=e, k=count[ck], gym=r.get("gym"),
                                         clone_id=r.get("clone_id"), chunks=[],
                                         pre=[], first_row=first_row, last_row=idx)
        last_tick[ck] = t
        first_since.pop(ck, None)
        d = inst[(ck, count[ck])]
        d["last_row"] = idx
        d["chunks"].append(dict(tick=t, note=str(r.get("note")), prompt=r.get("prompt") or "",
                                row=idx, acts=mine, after=[]))
    for ck, acts in pending.items():        # acts whose thought row never arrived
        if acts:
            _stat("acts_orphaned", len(acts))
    return list(inst.values())


def reflection_groups(rows: list) -> list:
    """Reflection rows grouped by their episode_id ('reflection@0032'), in
    tick order, with the harness summary extracted from the first prompt."""
    groups: "collections.OrderedDict" = collections.OrderedDict()
    for idx, r in enumerate(rows):
        if r.get("kind") != "reflection" or not r.get("note"):
            continue
        key = (r.get("clone_id"), r.get("episode_id"))
        g = groups.setdefault(key, dict(eid=r.get("episode_id"), gym=r.get("gym"),
                                        clone_id=r.get("clone_id"),
                                        at_episode=r.get("at_episode"),
                                        chunks=[], first_row=idx))
        g["chunks"].append(dict(tick=_tick(r), note=str(r["note"]),
                                prompt=r.get("prompt") or "", row=idx))
    for g in groups.values():
        g["chunks"].sort(key=lambda c: (c["tick"], c["row"]))
        g["summary"] = extract_reflection_summary(g["chunks"][0]["prompt"])
    return list(groups.values())


# ---------------------------------------------------------------------------
# 2. what the child actually saw: head (task text), intro, summary
# ---------------------------------------------------------------------------
def extract_head(prompt: str) -> dict:
    """GOAL / METRIC (multi-line: a puzzle's goal spans lines) and, at tick 1,
    the intro line from the stored context render (state.render_context)."""
    out = dict(goal=None, metric=None, intro=None)
    if not prompt:
        return out
    m = re.search(r"^GOAL: (.*?)(?=\nMETRIC: |\nCLOCK: |\n=== )", prompt, re.S | re.M)
    if m:
        out["goal"] = m.group(1).strip()
    m = re.search(r"^METRIC: (.*?)(?=\nCLOCK: |\n=== )", prompt, re.S | re.M)
    if m:
        out["metric"] = m.group(1).strip()
    marker = "=== YOUR THINKING (continues) ===\n"
    i = prompt.rfind(marker)
    if i >= 0:
        tail = prompt[i + len(marker):].strip()
        if tail and "\n" not in tail.strip():
            out["intro"] = tail.strip()
    return out


def extract_reflection_summary(prompt: str) -> str:
    if not prompt:
        return ""
    a = "=== WHAT YOU RECENTLY LIVED ===\n"
    b = "\n=== YOUR REFLECTION (continues) ==="
    i = prompt.find(a)
    j = prompt.find(b)
    if i < 0 or j < 0 or j < i:
        return ""
    return prompt[i + len(a):j].strip()


def strip_you_block(prompt: str) -> str:
    """The stored prompt begins with '=== YOU ===' + the bootstrap (birth
    brief, waking brief, parent brief). Training sequences begin at the gym's
    state (CHILD_MECHANISM_v7 2.1): everything before '=== STATE ===' goes."""
    i = (prompt or "").find(STATE_MARK)
    return prompt[i:] if i >= 0 else (prompt or "")


def outcome_line(a: dict) -> str:
    """Exactly the harness line the child saw (batch_loop.EpisodeDriver)."""
    try:
        s = float(a.get("score") or 0.0)
    except (TypeError, ValueError):
        s = 0.0
    return f"[OUTCOME] {a.get('outcome', '')} (score {s:.4f})"


def family_of(eid: str) -> str:
    m = _RG_ID.match(eid or "")
    if m:
        return f"rg/{m.group(1)}"
    return str(eid)


def group_key(eid: str, gym) -> str:
    """Stable neighbourhood key: within a gym the same puzzle family / the
    same program is adjacent (CHILD_MECHANISM_v7 2.2)."""
    return f"{gym or 'gym'}:{family_of(eid)}"


# ---------------------------------------------------------------------------
# 3. transcript elements and categories
# ---------------------------------------------------------------------------
def transcript(inst: dict, canonicalize: bool = True, measure: TokenMeasure = None) -> list:
    """Chronological elements of one instance: dict(role, text, chunk, tick,
    part, ntok). role 'harness' = context (zero loss); role 'child' = target.
    The head (GOAL/METRIC) comes from the prompt the child saw; with no
    stored prompt the only real fact available — the episode id — stands in
    and is counted (inst.head_missing; aggregated in the manifest). Each
    element ends with a newline so spans concatenate into the stream the
    child lived in."""
    measure = measure or DEFAULT_MEASURE
    els = []

    def add(role, text, chunk, tick, part):
        els.append(dict(role=role, text=text, chunk=chunk, tick=tick, part=part, ntok=measure(text)))

    head = extract_head(inst["chunks"][0]["prompt"]) if inst["chunks"] else {}
    if head.get("goal"):
        text = f"GOAL: {head['goal']}\n"
        if head.get("metric"):
            text += f"METRIC: {head['metric']}\n"
        add("harness", text, None, 0, "head")
        inst["head_missing"] = False
    else:
        add("harness", f"EPISODE: {inst['eid']}\n", None, 0, "head")
        inst["head_missing"] = True
    starts_at_one = bool(inst["chunks"]) and inst["chunks"][0]["tick"] <= 1
    if head.get("intro") and starts_at_one:
        add("harness", head["intro"] + "\n", None, 0, "intro")
        inst["intro_missing"] = False
    else:
        inst["intro_missing"] = starts_at_one
    for h in inst.get("pre", []):
        add("harness", h + "\n", None, 0, "harness")
    for ci, c in enumerate(inst["chunks"]):
        note = canonicalize_dialect(c["note"]) if canonicalize else c["note"]
        c["text"] = note.strip()
        c["harness_echo"] = bool(_HARNESS_ECHO.search(c["text"]))
        add("child", c["text"] + "\n", ci, c["tick"], "chunk")
        for a in c["acts"]:
            add("harness", outcome_line(a) + "\n", None, c["tick"], "outcome")
        for h in c["after"]:
            add("harness", h + "\n", None, c["tick"], "harness")
    return els


def _boilerplate_key(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())[:160]


def _move_key(action) -> str:
    return re.sub(r"\s+", "", str(action or ""))


def categorize(instances: list, min_instances: int = 3) -> dict:
    """Primary category per chunk (partition of the target mass) plus flags.
    Moves are the harness's EXECUTED acts (c['acts']), not a regex over the
    text: boilerplate: the chunk's normalized first 160 chars recur in >=
    min_instances DISTINCT episode instances (sleep_compile.dedup's key);
    revision: an executed move after feedback that differs from the previous
    executed move; repeat: an executed move after feedback, same move;
    action: an executed move with no prior feedback in the instance;
    unexecuted_act: an 'ACT:' line the harness never ran (Markdown-decorated
    in life; canonicalised here) and no executed move; thought: none of
    these. Boilerplate wins ties so templated actions are counted as what
    they are. flags.harness_echo: the child's text contains a line shaped
    like a harness line ([OUTCOME], CLOCK:, === , GOAL:, METRIC:)."""
    seen: dict = collections.defaultdict(set)
    for ii, inst in enumerate(instances):
        for c in inst["chunks"]:
            seen[_boilerplate_key(c.get("text") or c["note"])].add(ii)
    stats = collections.Counter()
    for inst in instances:
        prev_action = None
        had_feedback = False
        for c in inst["chunks"]:
            text = c.get("text") or canonicalize_dialect(c["note"]).strip()
            act_lines = _ACT.findall(text)
            moves = [_move_key(a.get("action")) for a in c["acts"]]
            first = moves[0] if moves else None
            flags = dict(has_act=bool(act_lines), executed=bool(moves), n_acts=len(moves),
                         after_feedback=had_feedback,
                         changed_action=bool(first is not None and prev_action is not None
                                             and first != prev_action),
                         boilerplate=len(seen[_boilerplate_key(text)]) >= min_instances,
                         repeats_in_ledger=len(seen[_boilerplate_key(text)]),
                         harness_echo=bool(c.get("harness_echo", _HARNESS_ECHO.search(text))))
            if flags["boilerplate"]:
                cat = "boilerplate"
            elif moves and had_feedback and first != prev_action:
                cat = "revision"
            elif moves and had_feedback:
                cat = "repeat"
            elif moves:
                cat = "action"
            elif act_lines:
                cat = "unexecuted_act"
            else:
                cat = "thought"
            c["category"], c["flags"] = cat, flags
            stats[cat] += 1
            if moves:
                prev_action = moves[-1]
            if c["acts"]:
                had_feedback = True
    return dict(stats)


def length_bucket(n_chunks: int) -> str:
    if n_chunks <= 4:
        return "1-4"
    if n_chunks <= 8:
        return "5-8"
    if n_chunks <= 16:
        return "9-16"
    return "17+"


def _ntok(e: dict) -> int:
    n = e.get("ntok")
    return n if n is not None else est_tokens(e["text"])


# ---------------------------------------------------------------------------
# 4. variant B: episode view (windows), local view, reflections
# ---------------------------------------------------------------------------
def episode_view_items(inst: dict, els: list, window_tokens: int, overlap_tokens: int,
                       log: dict) -> list:
    """Windows over the transcript, sized in TOKENS: every child element is a
    target in exactly one window; a window opens with the head (task text)
    and up to overlap_tokens of the preceding transcript as context
    (already-scored child text included, loss off), then runs forward while
    head + overlap + body <= window_tokens. A single chunk larger than the
    window is emitted alone and counted (oversize_chunks)."""
    items = []
    child_idx = [i for i, e in enumerate(els) if e["role"] == "child"]
    if not child_idx:
        return items
    head = els[0]
    head_n = _ntok(head)
    n_win = 0
    i = 1                       # first element not yet emitted (0 = head)
    while True:
        remaining = [j for j in child_idx if j >= i]
        if not remaining:
            break
        ctx, used = [], 0
        j = i - 1
        while j >= 1 and used + _ntok(els[j]) <= overlap_tokens:
            ctx.insert(0, els[j])
            used += _ntok(els[j])
            j -= 1
        spans = [[head["text"], False, "context"]]
        for e in ctx:
            spans.append([e["text"], False, "context"])
        total = head_n + used
        end = i
        n_targets = 0
        target_rows = []
        while end < len(els):
            e = els[end]
            n = _ntok(e)
            if total + n > window_tokens and n_targets > 0:
                break
            if e["role"] == "child":
                if total + n > window_tokens:
                    log["oversize_chunks"] = log.get("oversize_chunks", 0) + 1
                c = inst["chunks"][e["chunk"]]
                spans.append([e["text"], True, c["category"]])
                n_targets += 1
                target_rows.append(c["row"])
            else:
                spans.append([e["text"], False, "context"])
            total += n
            end += 1
        if n_targets == 0:      # cannot happen, defensive
            break
        items.append(dict(spans=spans, view="episode",
                          group=group_key(inst["eid"], inst.get("gym")),
                          category="mixed", order=target_rows[0],
                          meta=dict(eid=inst["eid"], instance=inst["k"], window=n_win,
                                    n_targets=n_targets, overlap_tokens=used, tokens=total,
                                    target_rows=target_rows, n_chunks=len(inst["chunks"]),
                                    head_missing=inst.get("head_missing", False),
                                    intro_missing=inst.get("intro_missing", False),
                                    gym=inst.get("gym"), clone_id=inst.get("clone_id"))))
        n_win += 1
        i = end
    for it in items:
        it["meta"]["n_windows"] = n_win
    if n_win > 1:
        log["episodes_windowed"] = log.get("episodes_windowed", 0) + 1
        log["windows_total"] = log.get("windows_total", 0) + n_win
    return items


def fit_tail(text: str, budget_tokens: int, measure: TokenMeasure) -> tuple:
    """Keep the END of text within budget_tokens (the recent stream is the
    end). Returns (kept_text, chars_dropped)."""
    if measure(text) <= budget_tokens:
        return text, 0
    keep = text
    for _ in range(6):
        n = measure(keep)
        if n <= budget_tokens:
            break
        frac = budget_tokens / max(1, n)
        keep = keep[-max(1, int(len(keep) * frac * 0.97)):]
    return keep, len(text) - len(keep)


def local_view_items(inst: dict, els: list, context_tokens: int, log: dict,
                     mode: str = "window", measure: TokenMeasure = None,
                     item_cap_tokens: int = 0) -> list:
    """One chunk as the target; its real antecedent context: the head (task
    text) plus a bounded window (in tokens) of the transcript right before
    it (most recent first until the budget). mode='stored' uses the exact
    prompt the child saw with its '=== YOU ===' block (birth brief, waking
    brief, parent brief) STRIPPED, left-truncated to the budget (its END is
    the recent stream)."""
    measure = measure or DEFAULT_MEASURE
    items = []
    head = els[0]
    head_n = _ntok(head)
    for j, e in enumerate(els):
        if e["role"] != "child":
            continue
        c = inst["chunks"][e["chunk"]]
        if mode == "stored" and c.get("prompt"):
            raw = c["prompt"]
            ctx_text = strip_you_block(raw)
            if len(ctx_text) < len(raw):
                log["stored_you_blocks_stripped"] = log.get("stored_you_blocks_stripped", 0) + 1
            ctx_text, dropped = fit_tail(ctx_text, context_tokens, measure)
            if dropped:
                log["local_truncated"] = log.get("local_truncated", 0) + 1
                log["local_chars_dropped"] = log.get("local_chars_dropped", 0) + dropped
            if not ctx_text.endswith("\n"):
                ctx_text += "\n"
            spans = [[ctx_text, False, "context"], [e["text"], True, c["category"]]]
            n_ctx = 1
            total = measure(ctx_text) + _ntok(e)
        else:
            ctx, used = [], 0
            k = j - 1
            dropped_els = 0
            while k >= 1:
                if used + _ntok(els[k]) <= context_tokens:
                    ctx.insert(0, els[k])
                    used += _ntok(els[k])
                else:
                    dropped_els += 1
                k -= 1
            if dropped_els:
                log["local_truncated"] = log.get("local_truncated", 0) + 1
                log["local_elements_dropped"] = log.get("local_elements_dropped", 0) + dropped_els
            spans = [[head["text"], False, "context"]]
            for x in ctx:
                spans.append([x["text"], False, "context"])
            spans.append([e["text"], True, c["category"]])
            n_ctx = len(ctx)
            total = head_n + used + _ntok(e)
        if item_cap_tokens and total > item_cap_tokens:
            log["local_oversize_items"] = log.get("local_oversize_items", 0) + 1
        items.append(dict(spans=spans, view="local",
                          group=group_key(inst["eid"], inst.get("gym")),
                          category=c["category"], order=c["row"],
                          meta=dict(eid=inst["eid"], instance=inst["k"], tick=c["tick"],
                                    n_context_elements=n_ctx, tokens=total,
                                    target_rows=[c["row"]],
                                    flags=c["flags"], n_chunks=len(inst["chunks"]),
                                    head_missing=inst.get("head_missing", False),
                                    intro_missing=inst.get("intro_missing", False),
                                    gym=inst.get("gym"), clone_id=inst.get("clone_id"))))
    return items


def reflection_items(groups: list, canonicalize: bool = True, measure: TokenMeasure = None) -> list:
    measure = measure or DEFAULT_MEASURE
    items = []
    for g in groups:
        spans = []
        total = 0
        if g.get("summary"):
            spans.append([g["summary"] + "\n", False, "context"])
            total += measure(spans[-1][0])
        rows = []
        for c in g["chunks"]:
            text = canonicalize_dialect(c["note"]) if canonicalize else c["note"]
            spans.append([text.strip() + "\n", True, "reflection"])
            total += measure(spans[-1][0])
            rows.append(c["row"])
        items.append(dict(spans=spans, view="episode", group=f"{g.get('gym') or 'gym'}:reflection",
                          category="reflection", order=g["chunks"][0]["row"],
                          meta=dict(eid=g["eid"], at_episode=g.get("at_episode"),
                                    n_targets=len(g["chunks"]), target_rows=rows, tokens=total,
                                    summary_missing=not g.get("summary"),
                                    gym=g.get("gym"), clone_id=g.get("clone_id"))))
    return items


def item_masses(item: dict, measure: TokenMeasure = None) -> tuple:
    measure = measure or DEFAULT_MEASURE
    tgt = sum(measure(s[0]) for s in item["spans"] if s[1])
    ctx = sum(measure(s[0]) for s in item["spans"] if not s[1])
    return tgt, ctx


def select_under_budget(items: list, budget_tokens: int, newest_frac: float,
                        rng: random.Random, log: dict, label: str,
                        measure: TokenMeasure = None) -> list:
    """CHILD_MECHANISM_v7 2.3: the newest rows in full up to newest_frac of
    the budget, the rest drawn uniformly over the older items. Nothing is
    deduplicated; only how much of the past is re-read at this write."""
    if budget_tokens <= 0:
        return items
    ordered = sorted(items, key=lambda it: -it["order"])     # newest first
    keep, used = [], 0
    rest = []
    for it in ordered:
        t = item_masses(it, measure)[0]
        if used + t <= budget_tokens * newest_frac:
            keep.append(it)
            used += t
        else:
            rest.append(it)
    rng.shuffle(rest)
    for it in rest:
        t = item_masses(it, measure)[0]
        if used + t <= budget_tokens:
            keep.append(it)
            used += t
    dropped = len(items) - len(keep)
    log[f"{label}_items_dropped_by_budget"] = dropped
    log[f"{label}_target_tokens_kept"] = used
    return sorted(keep, key=lambda it: it["order"])


# ---------------------------------------------------------------------------
# 4b. leak scan (CHILD_MECHANISM_v7 2.1 / Appendix C item 6)
# ---------------------------------------------------------------------------
def load_brief_texts(life_dir: str) -> dict:
    """Brief texts under <life>/sleep_*/ by ORIGIN: 'waking' = the child's own
    sleep-time summary (child/sleep origin — never a leak; its echoes are the
    rehearsal Rohin wants and are only counted), 'parent' = parent_brief.txt
    (parent origin — a verbatim line in a TRAINING TARGET is a leak)."""
    out = {"waking": [], "parent": []}
    if not life_dir or not os.path.isdir(life_dir):
        return out
    for key, pat in (("waking", "sleep_*/waking_brief.txt"), ("parent", "sleep_*/parent_brief.txt")):
        for p in sorted(glob.glob(os.path.join(life_dir, pat))):
            try:
                t = open(p).read()
            except OSError:
                continue
            if t.strip():
                out[key].append(t)
    return out


def _lines(texts, min_line_chars):
    s = set()
    for t in texts or []:
        for ln in t.splitlines():
            ln = ln.strip()
            if len(ln) >= min_line_chars:
                s.add(ln)
    return s


def leak_scan(items: list, brief_texts=None, min_line_chars: int = 40) -> list:
    """Leak = parent-origin text where the loss is. Rules (thinker/compiler
    line; CHILD_MECHANISM_v7 2.1; Rohin 2026-09-10: the child's restatements
    are its own): (1) a hard marker ('[PARENT]', ...) inside a TARGET span is a
    leak; (2) a verbatim parent_brief line (>= min_line_chars) inside a TARGET
    span is a leak ('parent_line'); (3) context spans (zero loss) are never a
    leak — they are what the child saw; (4) waking-brief lines are never a
    leak (child origin) — echoes are counted as 'waking_echo' in the log, not
    returned as hits. brief_texts may be the dict from load_brief_texts or a
    legacy flat list (then treated as parent-origin)."""
    if isinstance(brief_texts, dict):
        parent_lines = _lines(brief_texts.get("parent"), min_line_chars)
        waking_lines = _lines(brief_texts.get("waking"), min_line_chars)
    else:
        parent_lines = _lines(brief_texts, min_line_chars); waking_lines = set()
    hits = []
    echo = 0
    seen: dict = {}
    for ii, it in enumerate(items):
        for si, s in enumerate(it["spans"]):
            text, is_target = s[0], bool(s[1])
            key = (text, is_target)
            found = seen.get(key)
            if found is None:
                # hard markers are refused wherever they appear (strict default until Rohin
                # rules on parent text as zero-loss context — NEXT_EXPERIMENT_DESIGN_v2_ASTRA §10)
                found = [m for m in LEAK_MARKERS if m in text]
                # a verbatim parent-brief line is a leak only where the loss is
                if is_target and any(ln in text for ln in parent_lines):
                    found.append("parent_line")
                seen[key] = found
            if is_target and waking_lines and any(ln in text for ln in waking_lines):
                echo += 1
            for m in found:
                hits.append(dict(item=ii, span=si, marker=m, loss=is_target,
                                 view=it.get("view"), sample=text[:120]))
    leak_scan.last_waking_echo = echo
    return hits


def _refuse_on_leak(out_dir: str, hits: list, allow: bool, log: dict, recipe: str):
    log["leak_hits"] = len(hits)
    log["leak_markers"] = dict(collections.Counter(h["marker"] for h in hits))
    log["waking_echo_targets"] = getattr(leak_scan, "last_waking_echo", 0)  # child restating its own brief: counted, never refused
    flag = os.path.join(out_dir, "LEAK_REFUSED")
    if hits and not allow:
        with open(flag, "w") as f:
            json.dump(dict(recipe=recipe, hits=hits[:50], n_hits=len(hits)), f, indent=1)
        for p in ("corpus.json", "compile_manifest.json"):
            if os.path.exists(os.path.join(out_dir, p)):
                os.remove(os.path.join(out_dir, p))
        raise LeakError(f"{recipe}: {len(hits)} parent/brief leak hit(s) in the compiled spans "
                        f"({log['leak_markers']}); corpus NOT written ({flag})")
    if os.path.exists(flag):
        os.remove(flag)
    if hits:
        log["leak_markers_allowed"] = True


# ---------------------------------------------------------------------------
# 4c. variant B
# ---------------------------------------------------------------------------
def compile_two_scale(rows: list, out_dir: str, *, max_seq_tokens: int = DEFAULT_MAX_SEQ_TOKENS,
                      window_overlap_tokens: int = 1024, local_context_tokens: int = 768,
                      local_context: str = "window", views: str = "both", view_ratio: float = 0.5,
                      token_budget: int = 0, boilerplate_min_instances: int = 3,
                      canonicalize: bool = True, seed: int = 0, measure: TokenMeasure = None,
                      act_order: str = "auto", parent_as_context: bool = False,
                      brief_texts=None, allow_leak_markers: bool = False,
                      reserve_tokens: int = DEFAULT_RESERVE_TOKENS, extra_meta=None) -> dict:
    """Variant B. Writes <out_dir>/corpus.json and compile_manifest.json;
    returns the manifest. EMPTY_CORPUS marker when there is no child text;
    LeakError (LEAK_REFUSED marker, no corpus) on a parent/brief leak."""
    if views not in ("both", "episode", "local"):
        raise ValueError("views must be both|episode|local")
    measure = measure or DEFAULT_MEASURE
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    log: dict = {}
    window_tokens = max(64, max_seq_tokens - reserve_tokens)
    instances = build_instances(rows, act_order, parent_as_context, log)
    for inst in instances:
        inst["els"] = transcript(inst, canonicalize, measure)
    cat_counts = categorize(instances, boilerplate_min_instances)
    episode, local = [], []
    for inst in instances:
        if views in ("both", "episode"):
            episode += episode_view_items(inst, inst["els"], window_tokens,
                                          window_overlap_tokens, log)
        if views in ("both", "local"):
            local += local_view_items(inst, inst["els"], local_context_tokens, log,
                                      mode=local_context, measure=measure,
                                      item_cap_tokens=window_tokens)
    if views in ("both", "episode"):
        episode += reflection_items(reflection_groups(rows), canonicalize, measure)
    rng = random.Random(seed)
    if token_budget > 0:
        ep_share = view_ratio if views == "both" else (1.0 if views == "episode" else 0.0)
        if episode:
            episode = select_under_budget(episode, int(token_budget * ep_share), 0.5, rng, log,
                                          "episode", measure)
        if local:
            local = select_under_budget(local, int(token_budget * (1 - ep_share)), 0.5, rng, log,
                                        "local", measure)
    items = sorted(episode + local, key=lambda it: (it["order"], it["view"]))
    hits = leak_scan(items, brief_texts)
    _refuse_on_leak(out_dir, hits, allow_leak_markers, log, RECIPES["B"])
    manifest = _manifest_for(items, instances, rows, log, cat_counts, extra_meta,
                             recipe=RECIPES["B"], measure=measure,
                             params=dict(max_seq_tokens=max_seq_tokens, reserve_tokens=reserve_tokens,
                                         window_tokens=window_tokens,
                                         window_overlap_tokens=window_overlap_tokens,
                                         local_context_tokens=local_context_tokens,
                                         local_context=local_context, views=views,
                                         view_ratio=view_ratio, token_budget=token_budget,
                                         boilerplate_min_instances=boilerplate_min_instances,
                                         canonicalize=canonicalize, seed=seed,
                                         act_order=act_order, parent_as_context=parent_as_context))
    manifest["seconds"] = round(time.time() - t0, 2)
    _write_corpus(out_dir, items, manifest)
    return manifest


# ---------------------------------------------------------------------------
# 5. variant C: TMEM-format QA pairs, deterministic extraction, child outputs
# ---------------------------------------------------------------------------
def tmem_pairs(rows: list, canonicalize: bool = True, goal_chars: int = 600,
               act_order: str = "auto", log: dict = None) -> list:
    """JSON-array items {"instruction", "output", "type", ...}: the output is
    verbatim child text (a NOTE, an EXECUTED move, a reflection chunk); the
    instruction is a harness-written question over real ledger fields only.
    Moves come from the act rows (what the harness ran and scored); the
    condition is the last outcome the child had SEEN before the chunk (the
    k-th move of a multi-move chunk was written before the first one's
    outcome, so all moves of a chunk share the pre-chunk condition and are
    numbered as attempts). 'ACT:' lines the harness never executed
    (Markdown-decorated in life) yield no action pair and are counted.
    Adaptive quantity including zero (Fig. 1: 'return an empty JSON array')."""
    log = log if log is not None else {}
    pairs = []
    instances = build_instances(rows, act_order, False, log)
    unexecuted = empty_moves = 0
    for inst in instances:
        head = extract_head(inst["chunks"][0]["prompt"]) if inst["chunks"] else {}
        goal = (head.get("goal") or "")[:goal_chars]
        task = f"Task: {goal}\n" if goal else f"Task: episode {inst['eid']}\n"
        last_outcome = None
        for c in inst["chunks"]:
            text = canonicalize_dialect(c["note"]) if canonicalize else c["note"]
            notes = _NOTE.findall(text)
            if _ACT.search(text) and not c["acts"]:
                unexecuted += 1
            n_moves = len(c["acts"])
            for k, a in enumerate(c["acts"], 1):
                move = str(a.get("action") or "").strip()
                if not move:                  # 'ACT:' with nothing after it: scored INVALID, no move to learn
                    empty_moves += 1
                    continue
                where = f"{inst['eid']} (turn {c['tick']}" + (f", attempt {k})" if n_moves > 1 else ")")
                q = task + (f"After the outcome \"{last_outcome}\", what did you try next on {where}?"
                            if last_outcome else
                            f"With no attempts made yet on {where}, what did you try first?")
                pairs.append(dict(instruction=q, output=move, type="action", executed=True,
                                  eid=inst["eid"], instance=inst["k"], tick=c["tick"],
                                  row=c["row"], group=group_key(inst["eid"], inst.get("gym"))))
            for n in notes:
                n = n.strip()
                if n:
                    q = task + (f"What did you note to yourself while working on {inst['eid']} "
                                f"(turn {c['tick']})?")
                    pairs.append(dict(instruction=q, output=n, type="note",
                                      eid=inst["eid"], instance=inst["k"], tick=c["tick"],
                                      row=c["row"], group=group_key(inst["eid"], inst.get("gym"))))
            if c["acts"]:
                last_outcome = c["acts"][-1].get("outcome", "")
    for g in reflection_groups(rows):
        for c in g["chunks"]:
            text = (canonicalize_dialect(c["note"]) if canonicalize else c["note"]).strip()
            if not text:
                continue
            at = g.get("at_episode")
            q = (f"In your private reflection after episode {at}, part {c['tick']}, what did you write?"
                 if at is not None else f"In your private reflection {g['eid']}, part {c['tick']}, what did you write?")
            pairs.append(dict(instruction=q, output=text, type="reflection", eid=g["eid"],
                              instance=0, tick=c["tick"], row=c["row"],
                              group=f"{g.get('gym') or 'gym'}:reflection"))
    pairs.sort(key=lambda p: (p["row"], p["type"]))
    log["chunks_with_unexecuted_act_lines"] = unexecuted
    log["acts_with_empty_move_skipped"] = empty_moves
    return pairs


TMEM_DEVIATIONS = [
    "extraction: deterministic script over the child's own rows (TMEM: model-written under prompt d; "
    "the thinker/compiler line forbids a restater)",
    "instruction_author: harness (real ledger fields only); output_author: child (verbatim NOTE / "
    "executed move / reflection)",
    "loss: answer only (TMEM: NOT FOUND); template: model chat template via trainer --chat-template "
    "(TMEM: NOT FOUND); eos_as_target: the trainer appends EOS as a target token (our choice)",
    "schedule: ONE offline pass of E epochs over all pairs of the horizon (TMEM: per-trigger online "
    "SFT on the current chunk's pairs, cumulative within an episode, ~10 steps)",
    "lora: alpha = r (scaling 1.0, Delta = B A as eq. 7), dropout 0 — write_ab.sh passes --alpha 6 "
    "--dropout 0 for C_tmem; max-len 2048 and the training seed are ours",
]


def compile_tmem_qa(rows: list, out_dir: str, *, canonicalize: bool = True,
                    measure: TokenMeasure = None, act_order: str = "auto", brief_texts=None,
                    allow_leak_markers: bool = False, extra_meta=None) -> dict:
    measure = measure or DEFAULT_MEASURE
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    log: dict = {}
    pairs = tmem_pairs(rows, canonicalize, act_order=act_order, log=log)
    items = [dict(spans=[[p["instruction"], False, "context"], [p["output"], True, "tmem_qa"]],
                  view="tmem_qa", group=p["group"], category="tmem_qa", order=p["row"],
                  meta=dict(eid=p["eid"], instance=p["instance"], tick=p["tick"],
                            pair_type=p["type"], executed=p.get("executed"), target_rows=[p["row"]],
                            chat=True))
             for p in pairs]
    hits = leak_scan(items, brief_texts)
    _refuse_on_leak(out_dir, hits, allow_leak_markers, log, RECIPES["C"])
    with open(os.path.join(out_dir, "tmem_pairs.json"), "w") as f:
        json.dump([{"instruction": p["instruction"], "output": p["output"]} for p in pairs],
                  f, indent=1)
    log["pairs_by_type"] = dict(collections.Counter(p["type"] for p in pairs))
    manifest = _manifest_for(items, build_instances(rows, act_order, False, {}), rows, log, {},
                             extra_meta, recipe=RECIPES["C"], measure=measure,
                             params=dict(canonicalize=canonicalize, act_order=act_order,
                                         extraction="deterministic script over the child's own rows "
                                                    "(TMEM's is model-written under prompt d; the "
                                                    "thinker/compiler line forbids a restater)",
                                         instruction_author="harness (real ledger fields only)",
                                         output_author="child (verbatim NOTE / executed move / reflection)",
                                         moves_from="act rows (executed and scored by the harness)",
                                         loss="answer only (TMEM: NOT FOUND)",
                                         template="model chat template via trainer --chat-template "
                                                  "(TMEM: NOT FOUND)",
                                         tmem_deviations=list(TMEM_DEVIATIONS)))
    manifest["seconds"] = round(time.time() - t0, 2)
    _write_corpus(out_dir, items, manifest)
    return manifest


# ---------------------------------------------------------------------------
# 6. variant A: today's compile_sleep, called
# ---------------------------------------------------------------------------
def _null_think(prompt: str) -> str:
    """--think none: the THINK calls return nothing (no principles, empty
    brief); the exemplars themselves need no model."""
    return ""


_LEGACY_ID = re.compile(r"^(?:Program|Situation|Puzzle) (\S+?)\.(?:\s|$)")


def legacy_items(corpus: list) -> list:
    items = []
    for i, c in enumerate(corpus):
        if isinstance(c, str):
            spans = [[c, True, "legacy"]]
            eid = None
            m = _LEGACY_ID.match(c)      # 'Program benchmark://chstone-v0/mips. My thinking: ...'
            if m:
                eid = m.group(1)
            items.append(dict(spans=spans, view="legacy",
                              group=group_key(eid, None) if eid else "legacy",
                              category="legacy", order=i,
                              meta=dict(principle=c.startswith("Principle: "),
                                        reflection=c.startswith("[reflection]"), target_rows=[])))
        elif isinstance(c, dict) and c.get("a"):
            items.append(dict(spans=[[str(c.get("q", "")), False, "context"], [str(c["a"]), True, "legacy"]],
                              view="legacy", group="legacy", category="legacy", order=i,
                              meta=dict(native=True, target_rows=[])))
    return items


def mentions_heldout(text: str, ids) -> bool:
    """A held-out id appears in the text as a whole identifier (so
    'cbench-v1/sha' does not match 'cbench-v1/sha_clones')."""
    for x in ids or ():
        x = str(x).replace("benchmark://", "")
        if x and re.search(re.escape(x) + r"(?![\w/-])", text or ""):
            return True
    return False


def compile_legacy(rows: list, out_dir: str, *, model=None, vocab=None,
                   recorded_corpus=None, held_out_ids=None, brief_texts=None,
                   allow_leak_markers: bool = False, measure: TokenMeasure = None,
                   extra_meta=None) -> dict:
    """Variant A: sleep_compile.compile_sleep is CALLED on the rows (its own
    corpus.json + waking_brief.txt land in <out_dir>/legacy/), or the
    recorded corpus of the life is loaded, filtered for held-out ids (the
    life's compile never excluded them) and written v1-shaped to
    <out_dir>/legacy/corpus.json for the frozen v1 trainer. The strings
    become whole-text targets — the legacy write as it was trained
    (train_adapter.py's bare-text loss over each exemplar)."""
    measure = measure or DEFAULT_MEASURE
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    source = None
    log: dict = {}
    if recorded_corpus:
        corpus = json.load(open(recorded_corpus))["corpus"]
        n_total = len(corpus)
        kept = []
        for c in corpus:
            text = c if isinstance(c, str) else json.dumps(c)
            if mentions_heldout(text, held_out_ids):
                continue
            kept.append(c)
        log["recorded_exemplars_total"] = n_total
        log["recorded_exemplars_heldout_excluded"] = n_total - len(kept)
        corpus = kept
        sub = os.path.join(out_dir, "legacy")
        os.makedirs(sub, exist_ok=True)
        with open(os.path.join(sub, "corpus.json"), "w") as f:
            json.dump(dict(corpus=corpus, source="recorded, held-out ids filtered",
                           recorded=os.path.basename(recorded_corpus)), f)
        source = dict(recorded=os.path.basename(recorded_corpus),
                      sha256=_sha256_file(recorded_corpus),
                      filtered_for_v1=os.path.join("legacy", "corpus.json"))
    else:
        sub = os.path.join(out_dir, "legacy")
        res = compile_sleep(model or _null_think, rows, sub, prior_corpus=[],
                            vocab=vocab or dict(COMPILER_VOCAB))
        corpus = res["corpus"]
        source = dict(compiled=True, n_new=res["n_new"], n_principles=res["n_principles"],
                      think="model" if model is not None else "none")
    items = legacy_items(corpus)
    hits = leak_scan(items, brief_texts)
    _refuse_on_leak(out_dir, hits, allow_leak_markers, log, RECIPES["A"])
    log.update(source=source,
               n_principles=sum(1 for it in items if it["meta"].get("principle")),
               targets_child_only=False,
               note="A's targets include THINK-restated pathway text and PRINCIPLE lines "
                    "(the legacy write); quarantined from the target-blind lineage")
    manifest = _manifest_for(items, build_instances(rows, "auto", False, {}), rows, log, {},
                             extra_meta, recipe=RECIPES["A"], measure=measure,
                             params=dict(recorded=bool(recorded_corpus)))
    manifest["seconds"] = round(time.time() - t0, 2)
    _write_corpus(out_dir, items, manifest)
    return manifest


# ---------------------------------------------------------------------------
# 7. manifest and writing
# ---------------------------------------------------------------------------
def _is_budget_key(k: str) -> bool:
    return "budget" in k or k.endswith("_kept")


def _is_trunc_key(k: str) -> bool:
    return (not _is_budget_key(k)) and ("trunc" in k or "dropped" in k or "window" in k
                                        or "oversize" in k or "orphan" in k or "stripped" in k)


def _manifest_for(items: list, instances: list, rows: list, log: dict, cat_counts: dict,
                  extra_meta, *, recipe: str, params: dict, measure: TokenMeasure = None) -> dict:
    measure = measure or DEFAULT_MEASURE
    by_view = collections.defaultdict(lambda: dict(items=0, target_tokens=0, context_tokens=0))
    by_cat = collections.Counter()
    by_gym = collections.Counter()
    by_len = collections.Counter()
    echo_by_view = collections.Counter()
    echo_by_cat = collections.Counter()
    exposures_target = collections.Counter()      # chunk row -> times it is a target
    echo_texts = {c["text"] + "\n" for i in instances for c in i["chunks"]
                  if c.get("harness_echo") and c.get("text") is not None}
    items_head_missing = items_intro_missing = 0
    max_item_tokens = 0
    for it in items:
        tgt, ctx = item_masses(it, measure)
        v = by_view[it["view"]]
        v["items"] += 1
        v["target_tokens"] += tgt
        v["context_tokens"] += ctx
        max_item_tokens = max(max_item_tokens, tgt + ctx)
        for s in it["spans"]:
            if s[1]:
                n = measure(s[0])
                by_cat[s[2]] += n
                if s[0] in echo_texts:
                    echo_by_view[it["view"]] += n
                    echo_by_cat[s[2]] += n
        by_gym[str(it["meta"].get("gym"))] += tgt
        if "n_chunks" in it["meta"]:
            by_len[length_bucket(it["meta"]["n_chunks"])] += tgt
        for r in it["meta"].get("target_rows") or []:
            exposures_target[r] += 1
        items_head_missing += int(bool(it["meta"].get("head_missing")))
        items_intro_missing += int(bool(it["meta"].get("intro_missing")))
    total_t = sum(v["target_tokens"] for v in by_view.values())
    total_c = sum(v["context_tokens"] for v in by_view.values())
    n_chunks = sum(len(i["chunks"]) for i in instances)
    n_child_rows = n_chunks + sum(1 for r in rows if r.get("kind") == "reflection" and r.get("note"))
    child_mass = sum(measure((c.get("text") or canonicalize_dialect(c["note"]).strip()) + "\n")
                     for i in instances for c in i["chunks"])
    hist = collections.Counter(exposures_target.values())
    m = dict(recipe=recipe, created=time.strftime("%Y-%m-%d %H:%M:%S"),
             n_items=len(items), n_rows=len(rows), n_instances=len(instances),
             n_chunks=n_chunks, n_child_rows=n_child_rows,
             n_reflection_rows=sum(1 for r in rows if r.get("kind") == "reflection"),
             est_target_tokens=total_t, est_context_tokens=total_c,
             est_tokens_total=total_t + total_c, max_item_tokens=max_item_tokens,
             token_measure=measure.describe(), token_measure_kind=measure.kind,
             view_share={k: (round(v["target_tokens"] / total_t, 4) if total_t else 0.0)
                         for k, v in by_view.items()},
             by_view=dict(by_view), target_tokens_by_category=dict(by_cat),
             target_tokens_by_gym=dict(by_gym), target_tokens_by_episode_length=dict(by_len),
             target_tokens_harness_echo=dict(total=sum(echo_by_view.values()),
                                             by_view=dict(echo_by_view), by_category=dict(echo_by_cat),
                                             chunks=sum(1 for i in instances for c in i["chunks"]
                                                        if c.get("harness_echo")),
                                             note="child text containing a harness-shaped line "
                                                  "([OUTCOME]/CLOCK:/=== /GOAL:/METRIC:); trained as "
                                                  "child text — whether to mask it is a decision, stated"),
             chunk_categories=cat_counts,
             conditioning=dict(items_head_missing=items_head_missing,
                               items_intro_missing=items_intro_missing,
                               instances_head_missing=sum(1 for i in instances if i.get("head_missing")),
                               instances_intro_missing=sum(1 for i in instances if i.get("intro_missing")),
                               instances_with_stored_prompt=sum(1 for i in instances
                                                                if i["chunks"] and i["chunks"][0].get("prompt"))),
             effective_exposures=dict(
                 mean_targets_per_child_row=round(total_t / child_mass, 3) if child_mass else 0.0,
                 rows_as_target_once=hist.get(1, 0),
                 rows_as_target_twice=sum(v for k, v in hist.items() if k >= 2),
                 exposure_histogram={str(k): v for k, v in sorted(hist.items())}),
             truncation={k: v for k, v in log.items() if _is_trunc_key(k)},
             budget={k: v for k, v in log.items() if _is_budget_key(k)},
             log={k: v for k, v in log.items() if not (_is_trunc_key(k) or _is_budget_key(k))},
             params=params,
             token_estimate=("exact per-span counts with the trainer's tokenizer"
                             if measure.kind == "exact" else
                             f"chars/{measure.cpt:g} (trainer logs exact counts)"),
             empty=(total_t == 0))
    if extra_meta:
        m.update(extra_meta)
    return m


def _write_corpus(out_dir: str, items: list, manifest: dict) -> None:
    tmp = os.path.join(out_dir, ".corpus.tmp")
    with open(tmp, "w") as f:
        json.dump(dict(recipe=manifest["recipe"], format="v3_spans", corpus=items,
                       n_items=len(items)), f)
    os.replace(tmp, os.path.join(out_dir, "corpus.json"))
    with open(os.path.join(out_dir, "compile_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1, default=str)
    flag = os.path.join(out_dir, "EMPTY_CORPUS")
    if manifest.get("empty"):
        with open(flag, "w") as f:
            f.write("no child text to write\n")
    elif os.path.exists(flag):
        os.remove(flag)


# ---------------------------------------------------------------------------
# 8. row selection: horizon and held-out exclusion
# ---------------------------------------------------------------------------
def cut_rows_at_episodes(rows: list, max_episodes: int, act_order: str = "auto") -> list:
    """Rows up to the FIRST row of episode instance number max_episodes + 1
    (instances counted in ledger order over all clones; in acts_first
    ledgers the instance's tick-1 act/note rows precede its thought row and
    are cut with it, so no foreign outcome is left for an earlier episode)."""
    if not max_episodes or max_episodes <= 0:
        return rows
    inst = build_instances(rows, act_order, False, {})
    if len(inst) <= max_episodes:
        return rows
    cut = inst[max_episodes]["first_row"]
    return rows[:cut]


def default_exclusions(gym_name: str) -> set:
    """Held-out ids by identifier (compiler: the 8 report programs and
    disjoint panel v1); the reasoning gym is excluded by FAMILY through
    exclude_rows(split_of=...)."""
    ids = set()
    if gym_name == "compiler":
        from .run_life import PROBES
        ids |= {p.replace("benchmark://", "") for p in PROBES}
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        p = os.path.join(here, "research_notes", "disjoint_panel_v1.json")
        if os.path.exists(p):
            ids |= {x.replace("benchmark://", "") for x in json.load(open(p))["panel"]}
    return ids


def _rg_split_of(log=print):
    try:
        from .reasoning_gym_gym import ReasoningGymGym
        return ReasoningGymGym(require_package=False).split_of
    except Exception as e:  # noqa: BLE001
        log(f"[compile-v3] reasoning gym split_of unavailable: {e}")
        return None


def exclusion_rules(default_gym: str, extra_ids=None, log=print) -> dict:
    """Per-gym held-out rule for every registered gym: {gym: (ids, split_of)}.
    A row is judged by ITS OWN r['gym'] when it carries one (pooled ledgers),
    else by default_gym."""
    rules = {"compiler": (default_exclusions("compiler") | set(extra_ids or ()), None),
             "reasoning_gym": (set(extra_ids or ()), _rg_split_of(log))}
    if default_gym not in rules and default_gym not in (None, "none"):
        rules[default_gym] = (set(extra_ids or ()), None)
    return rules


def exclude_rows(rows: list, ids=None, split_of=None, by_gym: dict = None,
                 default_gym: str = None) -> tuple:
    """Drop every row of a held-out episode (gate/exam/canary). With by_gym
    ({gym: (ids, split_of)}) each row is judged by its own gym field (or
    default_gym); otherwise by ids / split_of. Returns (kept_rows,
    n_excluded, excluded_ids)."""
    ids = {str(x).replace("benchmark://", "") for x in (ids or [])}
    kept, gone = [], collections.Counter()
    for r in rows:
        e = str(r.get("episode_id") or "")
        c = e.replace("benchmark://", "")
        r_ids, r_split = ids, split_of
        if by_gym is not None:
            g = r.get("gym") or default_gym
            r_ids, r_split = by_gym.get(g, (set(), None))
            r_ids = {str(x).replace("benchmark://", "") for x in (r_ids or [])} | ids
            r_split = r_split or split_of
        bad = c in r_ids
        if not bad and r_split is not None and e:
            try:
                bad = r_split(e) in ("gate", "exam", "canary")
            except ValueError:
                bad = False
        if bad:
            gone[c] += 1
        else:
            kept.append(r)
    return kept, sum(gone.values()), sorted(gone)


def load_rows(path: str) -> list:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--variants", default="A,B,C")
    ap.add_argument("--cell-name", default=None,
                    help="output subdirectory for a SINGLE variant (e.g. --variants B --cell-name B_match)")
    ap.add_argument("--gym", default="compiler", choices=["compiler", "reasoning_gym", "none"],
                    help="the ledger's gym for rows without a gym field; rows WITH one are judged by it")
    ap.add_argument("--exclude-ids", default=None,
                    help="JSON list file or comma list of held-out episode ids, added to the defaults")
    ap.add_argument("--exclude-panels", default="default", choices=["default", "none"])
    ap.add_argument("--max-episodes", type=int, default=0,
                    help="corpus horizon: rows up to the first row of instance N+1 (P1: 512)")
    ap.add_argument("--rows-upto", type=int, default=0)
    ap.add_argument("--recorded-a", default=None,
                    help="variant A from the life's recorded corpus.json instead of THINK calls")
    ap.add_argument("--think", default="none", choices=["none", "vllm"],
                    help="A's THINK model when compiling (vllm = VLLMBackend on this GPU)")
    ap.add_argument("--tokenizer", default="auto",
                    help="none | auto ($V6_MODEL from the local cache) | HF name/path: exact token sizing")
    ap.add_argument("--max-seq-tokens", type=int, default=DEFAULT_MAX_SEQ_TOKENS,
                    help="the trainer's --max-len: every B item fits in it (head + overlap + body + reserve)")
    ap.add_argument("--reserve-tokens", type=int, default=DEFAULT_RESERVE_TOKENS)
    ap.add_argument("--window-overlap-tokens", type=int, default=1024)
    ap.add_argument("--local-context-tokens", type=int, default=768)
    # deprecated char-sized knobs (converted at CHARS_PER_TOKEN); the token knobs win when both are given
    ap.add_argument("--episode-window-chars", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--window-overlap-chars", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--local-context-chars", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--local-context", default="window", choices=["window", "stored"])
    ap.add_argument("--views", default="both", choices=["both", "episode", "local"],
                    help="B: both scales (default), episode = scale 1 alone (P1 W1s), local = scale 2 alone")
    ap.add_argument("--view-ratio", type=float, default=0.5)
    ap.add_argument("--token-budget", type=int, default=0)
    ap.add_argument("--boilerplate-min-instances", type=int, default=3)
    ap.add_argument("--no-canonicalize", action="store_true")
    ap.add_argument("--act-order", default="auto", choices=["auto", "acts_first", "thought_first"])
    ap.add_argument("--parent-as-context", action="store_true",
                    help="keep kind='parent' rows as zero-loss context (default: stripped, counted)")
    ap.add_argument("--life-dir", default=None,
                    help="life directory whose sleep_*/waking_brief.txt + parent_brief.txt feed the leak scan "
                         "(default: the ledger's directory)")
    ap.add_argument("--allow-leak-markers", action="store_true",
                    help="write the corpus even when the leak scan hits (logged); default refuses")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    if args.episode_window_chars and args.max_seq_tokens == DEFAULT_MAX_SEQ_TOKENS:
        args.max_seq_tokens = int(args.episode_window_chars / CHARS_PER_TOKEN) + args.reserve_tokens
    if args.window_overlap_chars:
        args.window_overlap_tokens = int(args.window_overlap_chars / CHARS_PER_TOKEN)
    if args.local_context_chars:
        args.local_context_tokens = int(args.local_context_chars / CHARS_PER_TOKEN)
    variants = [x.strip().upper() for x in args.variants.split(",") if x.strip()]
    if args.cell_name and len(variants) != 1:
        raise SystemExit("--cell-name needs exactly one variant")

    measure = load_measure(args.tokenizer)
    print(f"[compile-v3] token measure: {measure.describe()}")
    ledger = os.path.expanduser(args.ledger)
    rows = load_rows(ledger)
    n_raw = len(rows)
    if args.rows_upto:
        rows = rows[:args.rows_upto]
    rows = cut_rows_at_episodes(rows, args.max_episodes, args.act_order)
    extra_ids = set()
    if args.exclude_ids:
        p = os.path.expanduser(args.exclude_ids)
        extra_ids |= set(json.load(open(p))) if os.path.exists(p) else \
            {x.strip() for x in args.exclude_ids.split(",") if x.strip()}
    if args.exclude_panels == "default":
        rules = exclusion_rules(args.gym, extra_ids)
    else:
        rules = {g: (set(extra_ids), None) for g in ("compiler", "reasoning_gym", args.gym)}
    rows, n_excl, excl_ids = exclude_rows(rows, by_gym=rules,
                                          default_gym=None if args.gym == "none" else args.gym)
    all_ids = set()
    for ids, _s in rules.values():
        all_ids |= set(ids or ())
    life_dir = os.path.expanduser(args.life_dir) if args.life_dir else os.path.dirname(ledger)
    brief_texts = load_brief_texts(life_dir)
    extra = dict(ledger=os.path.basename(args.ledger), ledger_sha256=_sha256_file(ledger),
                 rows_raw=n_raw, rows_after_horizon_and_exclusion=len(rows),
                 rows_excluded_heldout=n_excl, excluded_ids=excl_ids[:64],
                 max_episodes=args.max_episodes, gym=args.gym,
                 exclusion_by_row_gym=True,
                 brief_texts_scanned=sum(len(v) for v in brief_texts.values()),
                 brief_texts_by_origin={k: len(v) for k, v in brief_texts.items()},
                 leak_scan="refuse" if not args.allow_leak_markers else "allow (logged)")
    out = os.path.expanduser(args.out)
    results = {}
    failures = {}
    for v in variants:
        d = os.path.join(out, args.cell_name or v)
        try:
            if v == "A":
                model = None
                if args.think == "vllm" and not args.recorded_a:
                    from .model_backend import VLLMBackend
                    model = VLLMBackend(adapter_path=None)
                vocab = dict(COMPILER_VOCAB)
                if args.gym == "reasoning_gym":
                    from .reasoning_gym_gym import ReasoningGymGym
                    vocab = ReasoningGymGym(require_package=False).compile_vocab()
                results[v] = compile_legacy(rows, d, model=model, vocab=vocab,
                                            recorded_corpus=os.path.expanduser(args.recorded_a)
                                            if args.recorded_a else None, held_out_ids=all_ids,
                                            brief_texts=brief_texts,
                                            allow_leak_markers=args.allow_leak_markers,
                                            measure=measure, extra_meta=extra)
            elif v == "B":
                results[v] = compile_two_scale(
                    rows, d, max_seq_tokens=args.max_seq_tokens, reserve_tokens=args.reserve_tokens,
                    window_overlap_tokens=args.window_overlap_tokens,
                    local_context_tokens=args.local_context_tokens, local_context=args.local_context,
                    views=args.views, view_ratio=args.view_ratio, token_budget=args.token_budget,
                    boilerplate_min_instances=args.boilerplate_min_instances,
                    canonicalize=not args.no_canonicalize, seed=args.seed, measure=measure,
                    act_order=args.act_order, parent_as_context=args.parent_as_context,
                    brief_texts=brief_texts, allow_leak_markers=args.allow_leak_markers,
                    extra_meta=extra)
            elif v == "C":
                results[v] = compile_tmem_qa(rows, d, canonicalize=not args.no_canonicalize,
                                             measure=measure, act_order=args.act_order,
                                             brief_texts=brief_texts,
                                             allow_leak_markers=args.allow_leak_markers,
                                             extra_meta=extra)
            else:
                raise SystemExit(f"unknown variant {v!r}")
        except LeakError as e:
            failures[v] = str(e)
            print(f"[compile-v3 {v}] LEAK_REFUSED: {e}")
            continue
        m = results[v]
        cond = m.get("conditioning", {})
        print(f"[compile-v3 {v}] items={m['n_items']} est_target_tokens={m['est_target_tokens']} "
              f"est_tokens_total={m['est_tokens_total']} max_item_tokens={m['max_item_tokens']} "
              f"views={m['view_share']} token_measure={m['token_measure']} empty={m['empty']} -> {d}")
        if cond.get("items_head_missing"):
            print(f"[compile-v3 {v}] WARNING head_missing items={cond['items_head_missing']} "
                  f"instances={cond['instances_head_missing']} (no stored prompt: the local view "
                  f"has no GOAL/METRIC conditioning)")
        if m.get("truncation"):
            print(f"[compile-v3 {v}] truncation/log: {m['truncation']}")
    summary = {(args.cell_name or v): {k: m.get(k) for k in
                                       ("recipe", "n_items", "est_target_tokens", "est_tokens_total",
                                        "max_item_tokens", "token_measure", "view_share",
                                        "target_tokens_by_category", "target_tokens_harness_echo",
                                        "conditioning", "effective_exposures", "truncation", "empty")}
               for v, m in results.items()}
    if failures:
        summary["LEAK_REFUSED"] = failures
    sp = os.path.join(out, "compile_summary.json")
    prev = json.load(open(sp)) if os.path.exists(sp) and args.cell_name else {}
    prev.update(summary)
    with open(sp, "w") as f:
        json.dump(prev, f, indent=1, default=str)
    if failures:
        raise SystemExit(2)
    print("COMPILE_V3_DONE")


if __name__ == "__main__":
    main()
