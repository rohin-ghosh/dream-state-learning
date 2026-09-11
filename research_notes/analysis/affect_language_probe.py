#!/usr/bin/env python3
"""Affect-language probe (Rohin's "cheap first test" for an appraisal gym, 2026-09-11).

Question: does affect/appraisal language the child ALREADY writes in its thought stream
predict a change in its next action?  Correlational, lexicon-based, CPU only.

Run on the compute node (no scipy there; Fisher's exact test is implemented below):
    ~/v2/venv/bin/python affect_language_probe.py --root ~/v6_out --out ~/analysis_affect
Reads every  {R2,R3,R4,RP}_B_seed*/ledger.jsonl  under --root.

Ledger facts this script relies on (verified against organism_v6/batch_loop.py, 2026-09-11):
  * kinds are exactly "act", "note", "thought" (no outcome/predict/recall rows).
  * 8 episodes run in lockstep per wake batch; `tick` is the chunk index 1..16 of one
    episode INSTANCE.  `episode_id` is the benchmark name and is revisited many times per
    life, so instances are re-segmented here: a record at tick 1 that follows that
    benchmark's previous *thought* row starts a new instance (the thought row is always
    the last row written for a tick).
  * thought.note = the child's raw generation for that chunk, truncated to 2000 chars.  The
    harness never injects text into it: every "[OUTCOME] ...", "OPEN SURPRISES" or
    "RECALLED EXPERIENCE" block inside a thought is the child ECHOING harness format.
    Such harness-shaped lines are stripped before lexicon matching, so the word "surprise"
    in an echoed "OPEN SURPRISES" header is never counted.
  * every line matching ^ACT\\s*:?  in the chunk is executed, in order, and written as an
    "act" row at the same tick (so one thought can carry several acts; markdown-decorated
    "**ACT:**" lines are NOT executed).  Act rows are the ground truth for actions.
Two units of analysis are reported:
  (A) thought-level, as specified in the brief: for the thought at tick t, "action changed"
      = the first act at tick >= t differs from the last act at tick < t in the same instance.
  (B) act-aligned: for each executed act, the child's text since the previous executed act
      (across chunk boundaries) is the "thought"; changed = this act != previous act.
"""
from __future__ import annotations
import argparse
import collections
import glob
import json
import math
import os
import random
import re

# ----------------------------------------------------------------------------- lexicon
NEGATIVE = [
    ("stuck", r"\bstuck\b"),
    ("frustrat*", r"\bfrustrat\w*"),
    ("not working", r"\b(?:is\s*not|isn't|isn\W?t|not|doesn't|does\s*not|didn't|did\s*not|hasn't|has\s*not|"
                    r"wasn't|was\s*not|aren't|won't|will\s*not|never|no\s+longer)\s+(?:seem(?:s|ed)?\s+to\s+)?"
                    r"(?:be\s+)?(?:really\s+|actually\s+|quite\s+)?work(?:ing|ed|s)?\b"),
    ("fail*", r"\bfail\w*"),
    ("worse", r"\bworse\b"),
    ("wrong", r"\bwrong\b"),
    ("confus*", r"\bconfus\w*"),
    ("unsure", r"\bunsure\b"),
    ("worried", r"\bworr(?:ied|y|ying|ies|isome)\b"),
    ("hopeless", r"\bhopeless\w*"),
    ("give up", r"\b(?:give|giving|gave|given)\s+up\b"),
    ("disappoint*", r"\bdisappoint\w*"),
    ("unexpected", r"\bunexpected(?:ly)?\b"),
]
SURPRISE = [("surpris*", r"\bsurpris\w*")]
POSITIVE = [
    ("good progress", r"\bgood\s+progress\b"),
    ("better", r"\bbetter\b"),
    ("works/worked", r"\bwork(?:s|ed)\b"),
    ("confident", r"\bconfident(?:ly)?\b"),
    ("promising", r"\bpromising\b"),
    ("excited", r"\bexcit(?:ed|ing)\b"),
    ("great", r"\bgreat\b"),
    ("improv*", r"\bimprov\w*"),
    ("success*", r"\bsuccess\w*"),
]
# Explicit change announcements. NOT pooled into "affect": reported separately as a positive
# control (if even these do not predict a change, language and action are disconnected).
CHANGE_INTENT = [
    ("try something different/new", r"\btry(?:ing)?\s+(?:out\s+)?(?:something|a)\s+(?:completely\s+|totally\s+)?(?:different|new)\b"),
    ("different approach/strategy/set", r"\bdifferent\s+(?:approach|strategy|set|combination|tack|passes|pass)\b"),
    ("switch to", r"\bswitch(?:ing)?\s+to\b"),
    ("instead", r"\binstead\b"),
    ("change approach/strategy", r"\bchang(?:e|ing)\s+(?:my\s+|the\s+|our\s+)?(?:approach|strategy|tack|course)\b"),
]
# Neutral control: frequent domain words with no appraisal content.
NEUTRAL = [
    ("passes", r"\bpasses\b"), ("program", r"\bprogram\b"), ("instruction*", r"\binstruction\w*"),
    ("loop*", r"\bloop\w*"), ("benchmark", r"\bbenchmark\b"), ("reduction", r"\breduction\b"),
    ("memory", r"\bmemory\b"), ("score", r"\bscore\b"), ("apply/applied", r"\bappl(?:y|ied|ying|ies)\b"),
    ("further", r"\bfurther\b"),
]
# A positive word preceded (within 3 tokens on the same line) by one of these is re-tagged
# NEGATIVE as "neg(<phrase>)"  e.g. "no improvement", "didn't work", "not better".
NEGATORS = {"no", "not", "n't", "never", "without", "didn't", "doesn't", "don't", "hasn't", "haven't",
            "isn't", "wasn't", "weren't", "aren't", "won't", "cannot", "can't", "couldn't", "little",
            "lack", "lacks", "lacking", "hardly", "barely", "nor", "neither"}

LEXICON = {"NEGATIVE": NEGATIVE, "SURPRISE": SURPRISE, "POSITIVE": POSITIVE,
           "CHANGE_INTENT": CHANGE_INTENT, "NEUTRAL": NEUTRAL}
COMPILED = {cat: [(lab, re.compile(pat, re.I)) for lab, pat in lst] for cat, lst in LEXICON.items()}

# ----------------------------------------------------------------------------- text cleaning
# The writer's marker regex (organism_v6/batch_loop.py::_MARK); ACT matches are executed acts.
_MARK = re.compile(r"^(PREDICT|ACT|NOTE|RECALL|DONE)\s*:?\s*(.*)$", re.M)
# Lines the child copies from the harness (never counted as thought), plus marker lines.
_DROP_LINE = re.compile(
    r"^\W{0,4}(?:\[OUTCOME\]|OUTCOME\W{0,2}:|CLOCK\b|===|GOAL:|METRIC:|BEST SCORE THIS EPISODE|LAST OUTCOME|"
    r"OPEN SURPRISES|YOUR NOTES|RECALLED EXPERIENCE|YOUR THINKING|PREDICT\b|ACT\b\W{0,3}:|ACT\W{0,3}:|"
    r"DONE\W*$|MARKER\W*:)", re.I)
_SURPRISE_ITEM = re.compile(r"^\W{0,6}predicted\s+-?[\d.]+,?\s+got\s+-?[\d.]+", re.I)
_MARK_PREFIX = re.compile(r"^\W{0,4}(?:NOTE|RECALL)\W{0,4}:?\s*", re.I)
_TOKEN = re.compile(r"[a-z']+")


def clean_text(raw: str) -> str:
    """Child's own prose from a chunk: drop marker/harness-shaped lines, keep NOTE/RECALL bodies."""
    out = []
    for line in raw.split("\n"):
        s = line.strip()
        if not s:
            continue
        if _DROP_LINE.match(s) or _SURPRISE_ITEM.match(s):
            continue
        s = _MARK_PREFIX.sub("", s)
        if s:
            out.append(s)
    return "\n".join(out)


def harness_echo(raw: str) -> bool:
    return bool(re.search(r"^\W{0,4}(?:\[OUTCOME\]|CLOCK:|=== |GOAL:|METRIC:|OPEN SURPRISES|RECALLED EXPERIENCE)", raw, re.M | re.I))


def norm_action(a: str) -> str:
    return re.sub(r"\s+", "", (a or "")).lower()


def action_set(a: str) -> frozenset:
    return frozenset(p for p in re.split(r"[,\s]+", (a or "").strip().lower()) if p)


_PASS = re.compile(r"-[a-z][\w-]*", re.I)
_REDUCTION = re.compile(r"\((-?[\d.]+)%\s*reduction\)")


def length_bin(n: int) -> str:
    """Cleaned-prose length bins (chars) used to control for 'more text -> more of every keyword'."""
    if n == 0:
        return "0"
    if n <= 200:
        return "1-200"
    if n <= 500:
        return "201-500"
    if n <= 1000:
        return "501-1000"
    return ">1000"


def act_was_bad(a: dict) -> bool:
    """Previous act gave no incremental progress: INVALID, or its own '(x% reduction)' <= 0.
    (The ledger 'score' is cumulative for the instance, so it cannot be used for this.)"""
    out = str(a.get("outcome") or "")
    if out.upper().startswith("INVALID"):
        return True
    m = _REDUCTION.search(out)
    if m:
        try:
            return float(m.group(1)) <= 0.0
        except ValueError:
            return True
    return not (a.get("score") or 0) > 0


def context_key(text: str, start: int, end: int) -> str:
    """Normalised sentence containing the match (digits -> #, pass names -> <pass>), <= 140 chars."""
    lo = max(text.rfind(".", 0, start), text.rfind("!", 0, start), text.rfind("?", 0, start), text.rfind("\n", 0, start))
    his = [i for i in (text.find(".", end), text.find("!", end), text.find("?", end), text.find("\n", end)) if i != -1]
    hi = min(his) if his else len(text)
    sent = text[lo + 1:hi].lower()
    sent = _PASS.sub("<pass>", sent)
    sent = re.sub(r"\d+(?:\.\d+)?", "#", sent)
    sent = re.sub(r"\s+", " ", sent).strip()
    return sent[:140]


def find_matches(text: str) -> list[dict]:
    """All lexicon hits in cleaned text: dicts with cat, phrase, span, ctx. Positive hits inside a
    negative span are dropped; negated positives are re-tagged NEGATIVE as neg(<phrase>)."""
    hits = []
    neg_spans = []
    for cat in ("NEGATIVE", "SURPRISE"):
        for lab, rx in COMPILED[cat]:
            for m in rx.finditer(text):
                hits.append(dict(cat=cat, phrase=lab, span=(m.start(), m.end()), ctx=context_key(text, m.start(), m.end())))
                if cat == "NEGATIVE":
                    neg_spans.append((m.start(), m.end()))
    for lab, rx in COMPILED["POSITIVE"]:
        for m in rx.finditer(text):
            if any(a <= m.start() < b for a, b in neg_spans):
                continue
            line_start = text.rfind("\n", 0, m.start()) + 1
            before = _TOKEN.findall(text[line_start:m.start()].lower())[-3:]
            if any(t in NEGATORS or t.endswith("n't") for t in before):
                hits.append(dict(cat="NEGATIVE", phrase=f"neg({lab})", span=(m.start(), m.end()), ctx=context_key(text, m.start(), m.end())))
            else:
                hits.append(dict(cat="POSITIVE", phrase=lab, span=(m.start(), m.end()), ctx=context_key(text, m.start(), m.end())))
    for cat in ("CHANGE_INTENT", "NEUTRAL"):
        for lab, rx in COMPILED[cat]:
            for m in rx.finditer(text):
                hits.append(dict(cat=cat, phrase=lab, span=(m.start(), m.end()), ctx=context_key(text, m.start(), m.end())))
    return hits


# ----------------------------------------------------------------------------- statistics
def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for [[a,b],[c,d]] (sum of hypergeometric probabilities <= observed)."""
    n = a + b + c + d
    if n == 0 or (a + b) == 0 or (c + d) == 0 or (a + c) == 0 or (b + d) == 0:
        return 1.0
    r1, c1 = a + b, a + c
    lg = math.lgamma
    const = lg(r1 + 1) + lg(n - r1 + 1) + lg(c1 + 1) + lg(n - c1 + 1) - lg(n + 1)

    def logp(x):
        return const - lg(x + 1) - lg(r1 - x + 1) - lg(c1 - x + 1) - lg(n - r1 - c1 + x + 1)

    lo, hi = max(0, r1 + c1 - n), min(r1, c1)
    obs = logp(a)
    p = 0.0
    for x in range(lo, hi + 1):
        lp = logp(x)
        if lp <= obs + 1e-9:
            p += math.exp(lp)
    return min(1.0, p)


def chi2_p(a: int, b: int, c: int, d: int) -> float:
    n = a + b + c + d
    r1, r2, c1, c2 = a + b, c + d, a + c, b + d
    if min(r1, r2, c1, c2) == 0:
        return 1.0
    chi = n * (a * d - b * c) ** 2 / (r1 * r2 * c1 * c2)
    return math.erfc(math.sqrt(chi / 2.0))


def table(changed_x: int, n_x: int, changed_y: int, n_y: int) -> dict:
    """x = with keyword, y = without. Returns rates, difference with Wald 95% CI, odds ratio, p-values."""
    a, b, c, d = changed_x, n_x - changed_x, changed_y, n_y - changed_y
    px = a / n_x if n_x else float("nan")
    py = c / n_y if n_y else float("nan")
    diff = px - py if n_x and n_y else float("nan")
    se = math.sqrt(px * (1 - px) / n_x + py * (1 - py) / n_y) if n_x and n_y else float("nan")
    orr = (a * d) / (b * c) if b and c else float("inf") if a and d else float("nan")
    return dict(n_with=n_x, changed_with=a, p_with=px, n_without=n_y, changed_without=c, p_without=py,
                diff=diff, diff_ci95=[diff - 1.96 * se, diff + 1.96 * se] if se == se else None,
                odds_ratio=orr, fisher_p=fisher_exact(a, b, c, d), chi2_p=chi2_p(a, b, c, d))


# ----------------------------------------------------------------------------- ledger -> instances
def load_instances(path: str) -> tuple[list[dict], dict]:
    instances, cur, last_kind = [], {}, {}
    n_rows = 0
    kinds = collections.Counter()
    with open(path) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            n_rows += 1
            k, eid, t = r.get("kind"), r.get("episode_id"), r.get("tick")
            kinds[k] += 1
            if k not in ("act", "note", "thought"):
                continue
            if eid not in cur or (t == 1 and last_kind.get(eid) == "thought"):
                inst = dict(eid=eid, start_row=i, idx=len(instances), ticks={}, extra_thought=0)
                instances.append(inst)
                cur[eid] = inst
            inst = cur[eid]
            tk = inst["ticks"].setdefault(t, dict(acts=[], thought=None))
            if k == "act":
                tk["acts"].append(dict(action=r.get("action", ""), score=r.get("score"), outcome=r.get("outcome", ""),
                                       prediction=r.get("prediction"), tick=t))
            elif k == "thought":
                if tk["thought"] is not None:
                    inst["extra_thought"] += 1
                tk["thought"] = dict(note=r.get("note") or r.get("text") or "", tick=t, win=r.get("win"))
            last_kind[eid] = k
    # validity: ticks must be 1..T consecutive
    bad = 0
    for inst in instances:
        ts = sorted(inst["ticks"])
        inst["valid"] = (ts == list(range(1, len(ts) + 1))) and inst["extra_thought"] == 0
        bad += not inst["valid"]
    meta = dict(rows=n_rows, kinds=dict(kinds), instances=len(instances), invalid_instances=bad,
                distinct_episode_ids=len(cur))
    return instances, meta


# ----------------------------------------------------------------------------- per-life analysis
def cats_of(hits):
    return {h["cat"] for h in hits}


def new_cell():
    return dict(n=0, changed=0, approach_changed=0)


def add(cell, changed, approach):
    cell["n"] += 1
    cell["changed"] += int(changed)
    cell["approach_changed"] += int(approach)


def analyse_life(path: str, life: str, rng: random.Random, global_phrase: dict) -> dict:
    instances, meta = load_instances(path)
    arm = life.split("_")[0]
    # groupings for 2x2 tables: key -> {"with": cell, "without": cell}
    A = collections.defaultdict(lambda: dict(w=new_cell(), wo=new_cell()))   # thought-level
    B = collections.defaultdict(lambda: dict(w=new_cell(), wo=new_cell()))   # act-aligned
    A_strat = collections.defaultdict(lambda: dict(w=new_cell(), wo=new_cell()))  # (stratum, key)
    phrase = collections.defaultdict(lambda: dict(n=0, ctx=collections.Counter(), cat=None))
    windows = collections.defaultdict(lambda: dict(thoughts=0, affect=0, neg=0, pos=0, sur=0, intent=0, matches=0,
                                                   repeat_ctx=0, changed_aff=0, n_aff_elig=0, changed_non=0, n_non_elig=0))
    seen_ctx = set()
    samples = []
    n_thoughts = n_eligible = n_next_same_tick = n_next_later = n_no_next = 0
    n_trunc = n_echo = n_affect_thoughts = 0
    seg_stats = collections.Counter()
    per_window_n = 32

    for inst in instances:
        if not inst["valid"]:
            continue
        w = inst["idx"] // per_window_n
        ticks = sorted(inst["ticks"])
        # all acts in order (ground truth), with their tick
        acts_by_tick = {t: inst["ticks"][t]["acts"] for t in ticks}
        prev_last = None          # last executed act before tick t (thought-level)
        carry = ""                # act-aligned: child's text since the previous executed act
        prev_act_B = None
        for t in ticks:
            th = inst["ticks"][t]["thought"]
            acts = acts_by_tick[t]
            if th is None:
                # acts without a thought row (should not happen); keep the action chain honest
                for a in acts:
                    prev_act_B = a
                if acts:
                    prev_last = acts[-1]
                continue
            raw = th["note"]
            n_thoughts += 1
            if len(raw) >= 2000:
                n_trunc += 1
            if harness_echo(raw):
                n_echo += 1
            text = clean_text(raw)
            hits = find_matches(text)
            cats = cats_of(hits)
            affect = bool(cats & {"NEGATIVE", "POSITIVE", "SURPRISE"})
            n_affect_thoughts += affect
            # ---- window / ritual bookkeeping
            W = windows[w]
            W["thoughts"] += 1
            W["affect"] += affect
            W["neg"] += "NEGATIVE" in cats
            W["pos"] += "POSITIVE" in cats
            W["sur"] += "SURPRISE" in cats
            W["intent"] += "CHANGE_INTENT" in cats
            for h in hits:
                if h["cat"] in ("NEGATIVE", "POSITIVE", "SURPRISE"):
                    W["matches"] += 1
                    key = (h["phrase"], h["ctx"])
                    if key in seen_ctx:
                        W["repeat_ctx"] += 1
                    seen_ctx.add(key)
                    P = phrase[h["phrase"]]
                    P["n"] += 1
                    P["cat"] = h["cat"]
                    P["ctx"][h["ctx"]] += 1
                    G = global_phrase.setdefault(h["phrase"], dict(n=0, cat=h["cat"], ctx=collections.Counter(), lives=set()))
                    G["n"] += 1
                    G["ctx"][h["ctx"]] += 1
                    G["lives"].add(life)
                    if rng.random() < 0.002 and len(samples) < 60:
                        samples.append(dict(life=life, cat=h["cat"], phrase=h["phrase"], ctx=h["ctx"]))
            # ---- (A) thought-level, as specified
            if prev_last is not None:
                if acts:
                    nxt = acts[0]
                    n_next_same_tick += 1
                else:
                    nxt = None
                    for t2 in ticks:
                        if t2 > t and acts_by_tick[t2]:
                            nxt = acts_by_tick[t2][0]
                            break
                    if nxt is not None:
                        n_next_later += 1
                if nxt is None:
                    n_no_next += 1
                else:
                    n_eligible += 1
                    changed = norm_action(nxt["action"]) != norm_action(prev_last["action"])
                    approach = action_set(nxt["action"]) != action_set(prev_last["action"])
                    strata = ["prev_act_bad" if act_was_bad(prev_last) else "prev_act_ok", "len:" + length_bin(len(text))]
                    non_affect = not affect
                    keys = [("AFFECT_ANY", affect), ("NEGATIVE", "NEGATIVE" in cats), ("POSITIVE", "POSITIVE" in cats),
                            ("SURPRISE", "SURPRISE" in cats), ("CHANGE_INTENT", "CHANGE_INTENT" in cats),
                            ("NEUTRAL_ANY", "NEUTRAL" in cats)]
                    for lab, rx in COMPILED["NEUTRAL"]:
                        keys.append((f"NEUTRAL:{lab}", any(h["phrase"] == lab and h["cat"] == "NEUTRAL" for h in hits)))
                    for lab, _ in NEGATIVE + SURPRISE + POSITIVE:
                        keys.append((f"PHRASE:{lab}", any(h["phrase"] == lab for h in hits)))
                    for key, flag in keys:
                        if flag:
                            add(A[key]["w"], changed, approach)
                            for s in strata:
                                add(A_strat[(s, key)]["w"], changed, approach)
                        elif key in ("AFFECT_ANY", "NEGATIVE", "POSITIVE", "SURPRISE") or key.startswith("PHRASE:"):
                            # baseline for affect splits = thoughts with NO affect at all
                            if non_affect:
                                add(A[key]["wo"], changed, approach)
                                for s in strata:
                                    add(A_strat[(s, key)]["wo"], changed, approach)
                        else:
                            add(A[key]["wo"], changed, approach)
                            for s in strata:
                                add(A_strat[(s, key)]["wo"], changed, approach)
                    if affect:
                        W["n_aff_elig"] += 1
                        W["changed_aff"] += changed
                    else:
                        W["n_non_elig"] += 1
                        W["changed_non"] += changed
            # ---- (B) act-aligned segments
            marks = [m for m in _MARK.finditer(raw) if m.group(1) == "ACT"]
            k, m_ = len(marks), len(acts)
            seg_stats["ticks"] += 1
            if k == m_:
                seg_stats["aligned"] += 1
            elif k < m_:
                seg_stats["text_truncated(k<m)"] += 1
            else:
                seg_stats["more_ACT_lines_than_acts(k>m)"] += 1
            pos = 0
            for i, a in enumerate(acts):
                if i < k:
                    seg_text = (carry + "\n" + clean_text(raw[pos:marks[i].start()])).strip()
                    pos = marks[i].end()
                    carry = ""
                else:
                    seg_text = None   # act executed from text beyond the 2000-char truncation
                if prev_act_B is not None and seg_text is not None:
                    shits = find_matches(seg_text)
                    scats = cats_of(shits)
                    saff = bool(scats & {"NEGATIVE", "POSITIVE", "SURPRISE"})
                    changed = norm_action(a["action"]) != norm_action(prev_act_B["action"])
                    approach = action_set(a["action"]) != action_set(prev_act_B["action"])
                    keysB = [("AFFECT_ANY", saff), ("NEGATIVE", "NEGATIVE" in scats), ("POSITIVE", "POSITIVE" in scats),
                             ("SURPRISE", "SURPRISE" in scats), ("CHANGE_INTENT", "CHANGE_INTENT" in scats),
                             ("NEUTRAL_ANY", "NEUTRAL" in scats), ("EMPTY_TEXT", not seg_text)]
                    for key, flag in keysB:
                        if flag:
                            add(B[key]["w"], changed, approach)
                        elif key in ("AFFECT_ANY", "NEGATIVE", "POSITIVE", "SURPRISE"):
                            if not saff:
                                add(B[key]["wo"], changed, approach)
                        else:
                            add(B[key]["wo"], changed, approach)
                    seg_stats["acts_scored"] += 1
                elif prev_act_B is None:
                    seg_stats["acts_first_in_instance"] += 1
                else:
                    seg_stats["acts_text_unavailable"] += 1
                prev_act_B = a
            if k < m_:
                carry = ""   # acts ran from text beyond the 2000-char cut: what preceded the next act is unknowable
            else:
                end = marks[m_ - 1].end() if m_ else 0
                carry = (carry + "\n" + clean_text(raw[end:])).strip()
            if acts:
                prev_last = acts[-1]

    def finalize(D):
        out = {}
        for key, cells in D.items():
            w, wo = cells["w"], cells["wo"]
            out[key] = dict(order=table(w["changed"], w["n"], wo["changed"], wo["n"]),
                            approach=table(w["approach_changed"], w["n"], wo["approach_changed"], wo["n"]))
        return out

    strat = collections.defaultdict(dict)
    for (s, key), cells in A_strat.items():
        strat[s][key] = dict(order=table(cells["w"]["changed"], cells["w"]["n"], cells["wo"]["changed"], cells["wo"]["n"]))

    phrases = []
    for ph, P in phrase.items():
        top_ctx, top_n = P["ctx"].most_common(1)[0]
        phrases.append(dict(phrase=ph, cat=P["cat"], n=P["n"], distinct_contexts=len(P["ctx"]),
                            top_context=top_ctx, top_context_n=top_n))
    phrases.sort(key=lambda d: -d["n"])
    win_list = []
    for w in sorted(windows):
        W = windows[w]
        win_list.append(dict(window=w, episodes=f"{w * per_window_n}-{(w + 1) * per_window_n - 1}", **W,
                             affect_rate=W["affect"] / W["thoughts"] if W["thoughts"] else None,
                             repeat_ctx_frac=W["repeat_ctx"] / W["matches"] if W["matches"] else None))
    return dict(life=life, arm=arm, meta=meta, n_thoughts=n_thoughts, n_affect_thoughts=n_affect_thoughts,
                n_thoughts_truncated_2000=n_trunc, n_thoughts_with_harness_echo=n_echo,
                thought_level=dict(eligible=n_eligible, next_act_same_tick=n_next_same_tick,
                                   next_act_later_tick=n_next_later, no_next_act=n_no_next, tables=finalize(A),
                                   stratified=strat),
                act_aligned=dict(seg_stats=dict(seg_stats), tables=finalize(B)),
                windows=win_list, phrases=phrases, samples=samples)


# ----------------------------------------------------------------------------- pooling
def pool_tables(lives: list[dict], which: str) -> dict:
    agg = collections.defaultdict(lambda: dict(w=new_cell(), wo=new_cell()))
    for L in lives:
        for key, tabs in L[which]["tables"].items():
            for side, sk in (("w", "with"), ("wo", "without")):
                o, ap = tabs["order"], tabs["approach"]
                agg[key][side]["n"] += o[f"n_{sk}"]
                agg[key][side]["changed"] += o[f"changed_{sk}"]
                agg[key][side]["approach_changed"] += ap[f"changed_{sk}"]
    out = {}
    for key, cells in agg.items():
        w, wo = cells["w"], cells["wo"]
        out[key] = dict(order=table(w["changed"], w["n"], wo["changed"], wo["n"]),
                        approach=table(w["approach_changed"], w["n"], wo["approach_changed"], wo["n"]))
    return out


def pool_strat(lives):
    agg = collections.defaultdict(lambda: collections.defaultdict(lambda: dict(w=new_cell(), wo=new_cell())))
    for L in lives:
        for s, D in L["thought_level"]["stratified"].items():
            for key, tabs in D.items():
                o = tabs["order"]
                agg[s][key]["w"]["n"] += o["n_with"]; agg[s][key]["w"]["changed"] += o["changed_with"]
                agg[s][key]["wo"]["n"] += o["n_without"]; agg[s][key]["wo"]["changed"] += o["changed_without"]
    return {s: {key: dict(order=table(c["w"]["changed"], c["w"]["n"], c["wo"]["changed"], c["wo"]["n"]))
                for key, c in D.items()} for s, D in agg.items()}


def pool_phrases(global_phrase: dict, top=15):
    """Exact pooled counts: distinct (phrase, normalised sentence) contexts across all lives."""
    rows = []
    for ph, P in global_phrase.items():
        tc, tn = P["ctx"].most_common(1)[0]
        top3 = [[c, n] for c, n in P["ctx"].most_common(3)]
        rows.append(dict(phrase=ph, cat=P["cat"], n=P["n"], distinct_contexts=len(P["ctx"]),
                         top_context=tc, top_context_n=tn, top3_contexts=top3, n_lives=len(P["lives"])))
    rows.sort(key=lambda d: -d["n"])
    return rows[:top]


# ----------------------------------------------------------------------------- markdown tables
def fmt_tab(name, T, unit="thoughts"):
    o = T["order"]
    ci = o["diff_ci95"]
    cis = f"[{ci[0]:+.3f}, {ci[1]:+.3f}]" if ci else "n/a"
    ap = T.get("approach")
    aps = f"{ap['p_with']:.3f} vs {ap['p_without']:.3f}" if ap and ap["n_with"] and ap["n_without"] else "n/a"
    return (f"| {name} | {o['changed_with']}/{o['n_with']} = {o['p_with']:.3f} | "
            f"{o['changed_without']}/{o['n_without']} = {o['p_without']:.3f} | {o['diff']:+.3f} {cis} | "
            f"{o['odds_ratio']:.2f} | {o['fisher_p']:.2g} | {aps} |")


TAB_HEAD = ("| keyword class | P(change \\| present) | P(change \\| absent) | diff [95% CI] | OR | Fisher p | approach-change (order-insensitive) present vs absent |\n"
            "|---|---|---|---|---|---|---|")


def render_md(res: dict) -> str:
    L = []
    L.append("## Auto-generated tables (affect_language_probe.py)\n")
    L.append("### Data covered\n")
    L.append("| life | arm | ledger rows | instances (invalid) | thoughts | thoughts w/ affect | eligible (A) | acts scored (B) | truncated@2000 | harness-echo thoughts |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for x in res["lives"]:
        m = x["meta"]
        L.append(f"| {x['life']} | {x['arm']} | {m['rows']} | {m['instances']} ({m['invalid_instances']}) | {x['n_thoughts']} | "
                 f"{x['n_affect_thoughts']} | {x['thought_level']['eligible']} | {x['act_aligned']['seg_stats'].get('acts_scored', 0)} | "
                 f"{x['n_thoughts_truncated_2000']} | {x['n_thoughts_with_harness_echo']} |")
    tot = res["totals"]
    L.append(f"| **pooled** | all | {tot['rows']} | {tot['instances']} ({tot['invalid_instances']}) | {tot['thoughts']} | {tot['affect_thoughts']} | "
             f"{tot['eligible_A']} | {tot['acts_scored_B']} | {tot['truncated']} | {tot['echo']} |\n")
    keys_main = ["AFFECT_ANY", "NEGATIVE", "POSITIVE", "SURPRISE", "CHANGE_INTENT", "NEUTRAL_ANY"]
    for which, title in (("thought_level", "(A) Thought-level (brief's definition): next act at tick >= t vs last act at tick < t"),
                         ("act_aligned", "(B) Act-aligned: text since the previous executed act vs. that act")):
        L.append(f"### {title}\n")
        L.append("Pooled over all 11 lives. For AFFECT_ANY/NEGATIVE/POSITIVE/SURPRISE the 'absent' column is thoughts with no affect hit of any class; for CHANGE_INTENT/NEUTRAL it is thoughts without that class.\n")
        L.append(TAB_HEAD)
        for k in keys_main:
            if k in res["pooled"][which]:
                L.append(fmt_tab(k, res["pooled"][which][k]))
        L.append("")
        L.append("Per arm (order-sensitive action change):\n")
        L.append("| arm | class | P(change \\| present) | P(change \\| absent) | diff | Fisher p |")
        L.append("|---|---|---|---|---|---|")
        for arm in sorted(res["per_arm"]):
            for k in ("AFFECT_ANY", "NEGATIVE", "POSITIVE", "SURPRISE", "CHANGE_INTENT", "NEUTRAL_ANY"):
                T = res["per_arm"][arm][which].get(k)
                if T:
                    o = T["order"]
                    L.append(f"| {arm} | {k} | {o['changed_with']}/{o['n_with']} = {o['p_with']:.3f} | {o['changed_without']}/{o['n_without']} = {o['p_without']:.3f} | {o['diff']:+.3f} | {o['fisher_p']:.2g} |")
        L.append("")
        L.append("Per life (AFFECT_ANY, order-sensitive):\n")
        L.append("| life | P(change \\| affect) | P(change \\| non-affect) | diff | Fisher p |")
        L.append("|---|---|---|---|---|")
        for x in res["lives"]:
            T = x[which]["tables"].get("AFFECT_ANY")
            if T:
                o = T["order"]
                L.append(f"| {x['life']} | {o['changed_with']}/{o['n_with']} = {o['p_with']:.3f} | {o['changed_without']}/{o['n_without']} = {o['p_without']:.3f} | {o['diff']:+.3f} | {o['fisher_p']:.2g} |")
        L.append("")
    L.append("### (A) stratified by the previous act's outcome and by cleaned-prose length (pooled)\n")
    L.append("prev_act_bad = previous executed act was INVALID or its own '(x% reduction)' <= 0; prev_act_ok otherwise. "
             "len:* = characters of the child's cleaned prose in the thought (controls for 'longer text carries more of every keyword').\n")
    L.append("| stratum | class | P(change \\| present) | P(change \\| absent) | diff | Fisher p |")
    L.append("|---|---|---|---|---|---|")
    for s in sorted(res["pooled"]["stratified"]):
        for k in ("AFFECT_ANY", "NEGATIVE", "POSITIVE", "SURPRISE", "CHANGE_INTENT", "NEUTRAL_ANY"):
            T = res["pooled"]["stratified"][s].get(k)
            if T:
                o = T["order"]
                L.append(f"| {s} | {k} | {o['changed_with']}/{o['n_with']} = {o['p_with']:.3f} | {o['changed_without']}/{o['n_without']} = {o['p_without']:.3f} | {o['diff']:+.3f} | {o['fisher_p']:.2g} |")
    L.append("")
    L.append("### Control: individual neutral words (A, pooled)\n")
    L.append(TAB_HEAD)
    for lab, _ in NEUTRAL:
        k = f"NEUTRAL:{lab}"
        if k in res["pooled"]["thought_level"]:
            L.append(fmt_tab(k, res["pooled"]["thought_level"][k]))
    L.append("")
    L.append("### Per-phrase (A, pooled; 'absent' = no affect of any class)\n")
    L.append(TAB_HEAD)
    for lab, _ in NEGATIVE + SURPRISE + POSITIVE:
        k = f"PHRASE:{lab}"
        if k in res["pooled"]["thought_level"] and res["pooled"]["thought_level"][k]["order"]["n_with"] > 0:
            L.append(fmt_tab(k, res["pooled"]["thought_level"][k]))
    L.append("")
    L.append("### Top 15 affect phrases (pooled) with templating exposure\n")
    L.append("| phrase | class | n hits | lives | distinct normalised sentences | most common sentence (n) |")
    L.append("|---|---|---|---|---|---|")
    for p in res["pooled"]["top_phrases"]:
        L.append(f"| {p['phrase']} | {p['cat']} | {p['n']} | {p['n_lives']} | {p['distinct_contexts']} | `{p['top_context'][:110]}` ({p['top_context_n']}) |")
    L.append("")
    L.append("### Affect rate per 32-episode window, per life\n")
    L.append("affect_rate = thoughts with any affect hit / thoughts in the window; repeat_ctx = fraction of affect hits whose (phrase, normalised sentence) had already appeared earlier in the life.\n")
    for x in res["lives"]:
        L.append(f"**{x['life']}**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)\n")
        L.append("| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\\|aff) | P(chg\\|non) |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for W in x["windows"]:
            ar = f"{W['affect_rate']:.3f}" if W["affect_rate"] is not None else "n/a"
            rc = f"{W['repeat_ctx_frac']:.2f}" if W["repeat_ctx_frac"] is not None else "n/a"
            pa = f"{W['changed_aff']}/{W['n_aff_elig']}" if W["n_aff_elig"] else "0/0"
            pn = f"{W['changed_non']}/{W['n_non_elig']}" if W["n_non_elig"] else "0/0"
            L.append(f"| {W['window']} | {W['episodes']} | {W['thoughts']} | {ar} | {W['neg']} | {W['pos']} | {W['sur']} | {W['intent']} | {rc} | {pa} | {pn} |")
        L.append("")
    return "\n".join(L)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.expanduser("~/v6_out"))
    ap.add_argument("--out", default=os.path.expanduser("~/analysis_affect"))
    ap.add_argument("--only", default=None, help="regex on life name (debug)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    rng = random.Random(0)
    paths = sorted(p for p in glob.glob(os.path.join(os.path.expanduser(args.root), "*_B_seed*", "ledger.jsonl"))
                   if re.match(r"(R2|R3|R4|RP)_B_seed\d+$", os.path.basename(os.path.dirname(p))))
    if args.only:
        paths = [p for p in paths if re.search(args.only, p)]
    lives = []
    global_phrase: dict = {}
    for p in paths:
        life = os.path.basename(os.path.dirname(p))
        print(f"[{life}] loading ...", flush=True)
        L = analyse_life(p, life, rng, global_phrase)
        m = L["meta"]
        print(f"[{life}] rows={m['rows']} kinds={m['kinds']} instances={m['instances']} invalid={m['invalid_instances']} "
              f"thoughts={L['n_thoughts']} affect={L['n_affect_thoughts']} eligibleA={L['thought_level']['eligible']} "
              f"segB={L['act_aligned']['seg_stats']}", flush=True)
        T = L["thought_level"]["tables"].get("AFFECT_ANY")
        if T:
            o = T["order"]
            print(f"[{life}] A: P(chg|affect)={o['changed_with']}/{o['n_with']}={o['p_with']:.3f} "
                  f"P(chg|non)={o['changed_without']}/{o['n_without']}={o['p_without']:.3f} fisher={o['fisher_p']:.3g}", flush=True)
        lives.append(L)
    arms = collections.defaultdict(list)
    for L in lives:
        arms[L["arm"]].append(L)
    res = dict(
        generated="2026-09-11", script="research_notes/analysis/affect_language_probe.py",
        lexicon={cat: [[lab, pat] for lab, pat in lst] for cat, lst in LEXICON.items()},
        negators=sorted(NEGATORS),
        definitions=dict(
            thought_level="for the thought at tick t of an episode instance: changed = first act at tick>=t != last act at tick<t (normalised: whitespace stripped, lowercase, order kept); approach = set of passes differs; thoughts with no previous act are skipped",
            act_aligned="for each executed act after the first in an instance: text = child's cleaned prose since the previous executed act; changed = this act != previous act",
            cleaning="lines matching harness/marker shapes ([OUTCOME], CLOCK:, ===, GOAL:, METRIC:, BEST SCORE, LAST OUTCOME, OPEN SURPRISES, YOUR NOTES, RECALLED EXPERIENCE, PREDICT, ACT, DONE, 'predicted X, got Y' items) dropped; NOTE:/RECALL: prefixes removed, bodies kept",
            baseline="for AFFECT_ANY/NEGATIVE/POSITIVE/SURPRISE and PHRASE:* the 'absent' group is thoughts with no NEGATIVE/POSITIVE/SURPRISE hit at all; for CHANGE_INTENT/NEUTRAL* it is thoughts without that keyword class",
            fisher="two-sided Fisher exact test implemented with lgamma (sum of hypergeometric probabilities <= observed); chi2_p is Pearson chi-square (1 df) via erfc; thoughts are autocorrelated within an episode so both are anti-conservative"),
        lives=lives,
        per_arm={arm: dict(thought_level=pool_tables(ls, "thought_level"), act_aligned=pool_tables(ls, "act_aligned"),
                           lives=[l["life"] for l in ls]) for arm, ls in arms.items()},
        pooled=dict(thought_level=pool_tables(lives, "thought_level"), act_aligned=pool_tables(lives, "act_aligned"),
                    stratified=pool_strat(lives), top_phrases=pool_phrases(global_phrase)),
        totals=dict(rows=sum(l["meta"]["rows"] for l in lives), instances=sum(l["meta"]["instances"] for l in lives),
                    invalid_instances=sum(l["meta"]["invalid_instances"] for l in lives),
                    thoughts=sum(l["n_thoughts"] for l in lives), affect_thoughts=sum(l["n_affect_thoughts"] for l in lives),
                    eligible_A=sum(l["thought_level"]["eligible"] for l in lives),
                    acts_scored_B=sum(l["act_aligned"]["seg_stats"].get("acts_scored", 0) for l in lives),
                    truncated=sum(l["n_thoughts_truncated_2000"] for l in lives),
                    echo=sum(l["n_thoughts_with_harness_echo"] for l in lives)),
    )
    with open(os.path.join(args.out, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    md = render_md(res)
    with open(os.path.join(args.out, "tables.md"), "w") as f:
        f.write(md)
    print(md)


if __name__ == "__main__":
    main()
