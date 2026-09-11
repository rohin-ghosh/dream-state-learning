"""Synthetic ledgers and mocks for the v3 write tests (CPU only).

The ledger imitates batch_loop.EpisodeDriver exactly: for every tick the
act rows are appended BEFORE the tick's thought row; the thought row stores
the rendered context (state.render_context layout) the child saw; note rows
duplicate NOTE: lines; the tail carries "[OUTCOME] ... (score s)" lines.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

BIRTH = "You are an agent living inside an optimization workshop. Think freely."
RECIPE = "-mem2reg, -sroa"
BOILER = "PREDICT: 0.3\nACT: -mem2reg, -sroa\nNOTE: start with the recipe"
REFLECTION_SUMMARY = ("Since your last reflection you worked on 3 situation(s).\n"
                      "- cbench-v1/crc32: 3 attempt(s), best score 0.25")
REFLECTION_TEXT = ["I notice I reach for the recipe before reading the program.",
                   "Next time I want to look at the size first and say why."]


def render(goal: str, metric: str, tick: int, tail: list) -> str:
    head = ["=== YOU ===", BIRTH, "=== STATE ===", f"GOAL: {goal}", f"METRIC: {metric}",
            f"CLOCK: chunk {tick}/16 | alive 0s | chunks since last progress: 0",
            "BEST SCORE THIS EPISODE: 0.0000", "LAST OUTCOME: (no actions taken yet)",
            "=== RECALLED EXPERIENCE ===", "(nothing recalled)",
            "=== YOUR THINKING (continues) ==="]
    return "\n".join(head + [t[:1200] for t in tail[-14:]]) + "\n"


class LedgerBuilder:
    """order='acts_first' imitates batch_loop.EpisodeDriver.consume (act and
    note rows BEFORE the tick's thought row); order='thought_first' imitates
    loop.py (the thought row first, then its acts and notes)."""

    def __init__(self, order: str = "acts_first", with_prompt: bool = True):
        self.rows = []
        self.order = order
        self.with_prompt = with_prompt

    def episode(self, eid: str, chunks: list, clone_id=None, gym=None, goal=None,
                metric="score = (base - after) / base.", intro=None, start_tick: int = 1):
        """chunks: list of (note, [(action, outcome, score), ...])."""
        prov = {}
        if clone_id is not None:
            prov["clone_id"] = clone_id
        if gym is not None:
            prov["gym"] = gym
        goal = goal or f"Optimize program '{eid}': choose LLVM optimization passes that minimize its IR instruction count."
        tail = [intro or f"New program: {eid}. I should form an expectation before acting, and write down what I learn."]
        t = start_tick
        out = []
        for note, acts in chunks:
            prompt = render(goal, metric, t, tail)
            act_rows = [dict(kind="act", episode_id=eid, tick=t, action=a, prediction=0.3, outcome=o,
                             score=s, surprise=None, time_cost=1.0, **prov) for a, o, s in acts]
            note_rows = [dict(kind="note", episode_id=eid, tick=t, note=line[5:].strip(), **prov)
                         for line in note.splitlines() if line.startswith("NOTE:")]
            th = dict(kind="thought", episode_id=eid, tick=t, note=note[:2000],
                      win=False, had_note="NOTE:" in note, **prov)
            if self.with_prompt:
                th["prompt"] = prompt[:24000]
            if self.order == "thought_first":
                self.rows += [th] + act_rows + note_rows
            else:
                self.rows += act_rows + note_rows + [th]
            out += act_rows + [th]
            tail.append(note.strip())
            for a, o, s in acts:
                tail.append(f"[OUTCOME] {o} (score {s:.4f})")
            t += 1
        return out

    def parent(self, eid: str, tick: int, text: str):
        """A classroom / nursery parent row (kind='parent')."""
        self.rows.append(dict(kind="parent", episode_id=eid, tick=tick, text=text))

    def reflection(self, at_episode: int, texts: list, summary: str = REFLECTION_SUMMARY, gym=None):
        eid = f"reflection@{at_episode:04d}"
        chunks = []
        for t, text in enumerate(texts, 1):
            prompt = ("=== YOU ===\n" + BIRTH + "\n=== PRIVATE REFLECTION TIME ===\nyour own time\n"
                      f"CLOCK: reflection chunk {t}/{len(texts)}\n=== WHAT YOU RECENTLY LIVED ===\n"
                      + summary + "\n=== YOUR REFLECTION (continues) ===\n" + "\n".join(chunks) + "\n")
            row = dict(kind="reflection", episode_id=eid, tick=t, note=text, prompt=prompt,
                       at_episode=at_episode)
            if gym:
                row["gym"] = gym
            self.rows.append(row)
            chunks.append(text)


def long_chunk(k: int, n: int = 1800) -> str:
    base = (f"Turn {k}: I compare the last outcome with what I expected and reason about "
            f"loop structure, memory access and dead code in this program. ")
    s = (base * (n // len(base) + 1))[:n - 40]
    return s + f"\nPREDICT: 0.{k % 9 + 1}\nACT: -pass{k}, -gvn"


def make_replay_rows(order: str = "acts_first") -> list:
    """The ambiguous shape: a ONE-chunk episode (DONE at tick 1) followed by
    a replay of the same program starting at tick 1, then an unrelated
    episode. In acts_first order the replay's tick-1 act row sits right
    after the first instance's only thought row."""
    b = LedgerBuilder(order=order)
    b.episode("cbench-v1/one", [("one-chunk episode\nACT: -a\nDONE", [("-a", "o-first", 0.1)])])
    b.episode("cbench-v1/one", [("replay first chunk\nACT: -b", [("-b", "o-replay-1", 0.2)]),
                                ("replay second\nACT: -c", [("-c", "o-replay-2", 0.3)])])
    b.episode("cbench-v1/other", [("other program\nACT: -z", [("-z", "REPLAY-OUTCOME", 0.9)])])
    return b.rows


def make_rows(with_heldout: bool = True, with_clones: bool = True, long_episode: bool = True,
              with_reflection: bool = True, with_rg: bool = True, order: str = "acts_first",
              with_prompt: bool = True) -> list:
    b = LedgerBuilder(order=order, with_prompt=with_prompt)
    # crc32 instance 1: revision, then a repeat in Markdown dialect
    b.episode("cbench-v1/crc32", [
        (BOILER, [(RECIPE, "instructions 100 -> 80 (20.0% reduction)", 0.2)]),
        ("The recipe gave 20%. Let me add gvn.\nPREDICT: 0.25\nACT: -mem2reg, -sroa, -gvn",
         [("-mem2reg, -sroa, -gvn", "instructions 100 -> 75 (25.0% reduction)", 0.25)]),
        ("### ACT: -mem2reg, -sroa, -gvn\n**NOTE:** same again to confirm",
         [("-mem2reg, -sroa, -gvn", "instructions 100 -> 75 (25.0% reduction)", 0.25)]),
    ])
    # qsort: a pure thought, then an INVALID move
    b.episode("cbench-v1/qsort", [
        ("Let me think about this program first. It sorts; loops dominate.", []),
        ("PREDICT: 0.1\nACT: -bogus", [("-bogus", "INVALID: unknown pass '-bogus'", 0.0)]),
    ])
    # bitcount and a crc32 REPLAY share the boilerplate opening (3 distinct instances)
    b.episode("cbench-v1/bitcount", [(BOILER, [(RECIPE, "instructions 50 -> 40 (20.0% reduction)", 0.2)])])
    b.episode("cbench-v1/crc32", [
        (BOILER, [(RECIPE, "instructions 100 -> 80 (20.0% reduction)", 0.2)]),
        ("Same as before; nothing new.\nACT: -mem2reg, -sroa",
         [(RECIPE, "instructions 100 -> 80 (20.0% reduction)", 0.2)]),
    ])
    if with_clones:   # two clones on the same program, interleaved tick by tick
        prov0 = dict(clone_id=0, gym="compiler")
        prov1 = dict(clone_id=1, gym="compiler")
        tails = {0: ["New program: cbench-v1/sha."], 1: ["New program: cbench-v1/sha."]}
        for t in (1, 2):
            for cid, prov in ((0, prov0), (1, prov1)):
                note = f"clone {cid} turn {t}\nACT: -licm{cid}"
                act = dict(kind="act", episode_id="cbench-v1/sha_clones", tick=t, action=f"-licm{cid}",
                           prediction=None, outcome=f"instructions 10 -> {9 - cid} (x)", score=0.1 * (cid + 1),
                           surprise=None, time_cost=1.0, **prov)
                th = dict(kind="thought", episode_id="cbench-v1/sha_clones", tick=t, note=note,
                          win=False, had_note=False, **prov)
                if with_prompt:
                    th["prompt"] = render("Optimize program 'cbench-v1/sha_clones'.", "score", t, tails[cid])
                b.rows += [th, act] if order == "thought_first" else [act, th]
                tails[cid].append(note)
    if long_episode:
        b.episode("cbench-v1/adpcm", [(long_chunk(k), [(f"-pass{k}, -gvn", f"instructions 900 -> {900 - 10 * k} (r)", 0.01 * k)])
                                      for k in range(1, 13)])
    if with_heldout:
        b.episode("cbench-v1/susan", [("held-out report program\nACT: -gvn", [("-gvn", "x", 0.1)])])
        b.episode("benchmark://npb-v0/10", [("held-out disjoint program\nACT: -gvn", [("-gvn", "x", 0.1)])])
    if with_rg:
        b.episode("rg/countdown/1000001", [
            ("PREDICT: 0.5\nACT: 3+4*5\nNOTE: try the obvious combination",
             [("3+4*5", "attempt 1: verifier score 0.00 (not accepted)", 0.0)]),
            ("Not it. Reorder.\nPREDICT: 0.6\nACT: (3+4)*5",
             [("(3+4)*5", "attempt 2: verifier score 1.00 (accepted)", 1.0)]),
        ], gym="reasoning_gym",
            goal="Countdown arithmetic puzzle. Submit an answer the verifier scores 1.0.\nUse 3, 4, 5 to reach 35.\nWrite each attempt on one ACT: line.",
            intro="New puzzle (Countdown arithmetic). I should read the rules, form an expectation, attempt, and learn from the score.")
    if with_reflection:
        b.reflection(8, REFLECTION_TEXT)
    return b.rows


class MockTok:
    """Char-level tokenizer: ids 3..252, eos 1, pad 0, bos 2 (unused)."""
    eos_token_id = 1
    pad_token_id = 0
    bos_token_id = 2

    def encode(self, text, add_special_tokens=False):
        return [3 + (ord(ch) % 250) for ch in text]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "<|user|>\n" + messages[0]["content"] + "\n<|assistant|>\n"


class WordTok(MockTok):
    """Whitespace-word tokenizer (one id per word, punctuation kept): a
    coarser, content-dependent count, so char-based estimates and exact
    counts disagree the way they do for a real BPE tokenizer."""

    def encode(self, text, add_special_tokens=False):
        return [3 + (hash(w) % 250) for w in text.replace("\n", " \n ").split(" ") if w]


def spans_text(item: dict) -> str:
    return "".join(s[0] for s in item["spans"])
