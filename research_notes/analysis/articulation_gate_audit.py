#!/usr/bin/env python3
"""ARTICULATION GATE -- retrospective measurement over the lives' sleep corpora (Astra memo q13 section 2 and 4,
2026-09-11; THESIS_v2 section 3; SEQ-051). Analysis only: nothing here touches a write path. CPU only; reads
<life>/ledger.jsonl and <life>/sleep_*/corpus.json.

Unit = one child-authored NOTE segment (every NOTE segment of a "thinking" item, before the harness "So I did:" line),
taken from the items NEW at each sleep (the delta against the preceding sleep on disk, as in corpus_register_audit; for
the first sleep on disk every item is new). Each note gets six tests, each True / False / None (None = cannot be judged):

  G  episode grounding    a sentence asserts >= 1 pass that this episode's ledger acts actually RAN, and a non-prediction
                          clause in the same or an adjacent sentence carries a number from those acts' measured outcomes
                          (an instruction count a or b of "instructions a -> b", their difference, or the printed / computed
                          percentage). "I expected 55%" and a bare pass list fail. None when the episode has no act rows.
  N  numerical agreement  every RESULT number the note asserts (integers >= 2 digits and percentages outside prediction
                          clauses and outside ranges like "55-65%") matches an act of this episode: integers exactly
                          (a, b or a-b), percentages within rounding of 100(b-a)/b at the precision printed, or the printed
                          percentage of the outcome. None when the note asserts no result number.
  F  first-person record  "I / I've / my" grammatically owns a completed action or observation ("I ran", "I measured",
                          "my measured count"); "I will", "I expect", "I need", "I should" do not qualify.
  D  recent duplication   the canonical form (lower case; punctuation and whitespace collapsed; episode id and program
                          name blanked; passes and numbers kept) equals one of the previous 64 raw notes of the life, in
                          corpus order across sleeps (rejected notes included).
  T  template collapse    (measured only) passes -> <PASS>, numbers / percentages -> <NUM>; per sleep, the share of new
                          notes covered by the single most frequent template, and the share whose token 5-gram Jaccard to
                          any of the previous 64 notes is >= 0.8.
  P  practice-only        no qualifying action-result assertion (G is not True) AND a clause matching the versioned list
                          PRACTICE_PHRASES (bootstrap / parent instructions repeated as slogans).

Admission (Astra's initial rule) = G and N and not D; the articulation rate A_s = share of new raw notes with F and G and N.
Both are reported as a pair of bounds: "hi" treats N = None (no result numbers asserted) as a pass, "lo" as a fail.

LEDGER SCOPE (lenient, as in corpus_provenance_audit): episode order is not recoverable from the ledger (ticks are per
chunk, ~8 episodes interleave), so "this episode's acts" = ALL act rows with that episode_id over the whole life. A note
can therefore be grounded by an outcome measured in a later visit of the same program; a note judged ungrounded is
ungrounded under the most generous reading.

Usage:
  python3 articulation_gate_audit.py ROOT [--sleeps 0032,1024] [--lives R2_B_seed0,...] [--all-sleeps] [--out [DIR]]
  --out DIR   writes DIR/<life>.json (per-sleep records with example notes per rejection reason) and DIR/summary.csv
              (default DIR when given without a value: research_notes/analysis/out/articulation/)
Stdout: one row per life (articulation in the final four sleeps, life admission rate, fraction of the final cumulative
corpus that survives the gate, top rejection reasons) and a per-arm, note-weighted pool."""
from __future__ import annotations

import argparse
import csv
import glob
import importlib.util
import json
import os
import re
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reg = _load("corpus_register_audit")
prov = _load("corpus_provenance_audit")
PASS, PCT, NUM = reg.PASS, prov.PCT, prov.NUM
DEFAULT_OUT = os.path.join(_HERE, "out", "articulation")
WINDOW = 64                      # previous raw notes compared for D and T
NEAR_DUP_JACCARD = 0.8

PRACTICE_PHRASES_VERSION = "v1-2026-09-11"
PRACTICE_PHRASES = [re.compile(p, re.I) for p in (
    r"\bform(?:ing|ed)?\s+(?:an?\s+|my\s+|specific\s+)?expectations?\b",
    r"\bwrite\s+down\s+what\s+i\s+learn",
    r"\blearn\s+from\s+(?:the\s+|my\s+)?(?:outcome|reality|it)\b",
    r"\bbe\s+concrete\b",
    r"\badjust\s+(?:my\s+|the\s+)?strategy\b",
    r"\breality\s+will\s+surprise\s+me\b",
    r"\bstick\s+to\s+(?:the|my|it)\b",
)]
PREDICTION = re.compile(r"\b(expect\w*|predict\w*|will|would|should|likely|anticipat\w*|aim\w*|hope\w*|estimat\w*|"
                        r"target\w*|goal|plan(?:s|ned|ning)?|probably|might|may|initial\s+expectation|expectation)\b", re.I)
FIRST_PERSON_RECORD = re.compile(
    r"\b(?:I|I've|I\s+have|I\s+had|my)\s+(?:then\s+|just\s+|also\s+|first\s+)?"
    r"(?:ran|applied|tried|used|measured|observed|saw|got|reduced|found|noticed|did|checked|compared|tested|recorded)\b"
    r"|\bmy\s+(?:measured|result|results|count|outcome|attempt)\b")
RANGE_PCT = re.compile(r"\d+(?:\.\d+)?\s*(?:-|–|to)\s*\d+(?:\.\d+)?\s*%")
SENT_SPLIT = re.compile(r"(?<=[.!?;])\s+|\n+")
CLAUSE_SPLIT = re.compile(r"\s*[,;:]\s+|\s+-\s+|\s+--\s+|\s+—\s+")
AB = re.compile(r"(\d+)\s*(?:->|→|to)\s*(\d+)")


# --------------------------------------------------------------------------- ledger --------------------------------------
def episode_acts(rows: list) -> dict:
    """episode_id -> dict(passes=set, ints=set, pcts=set, pairs=[(a,b)...]) over every act row of the life."""
    idx = defaultdict(lambda: dict(passes=set(), ints=set(), pcts=set(), pairs=[]))
    for r in rows:
        if r.get("kind") != "act" or not r.get("episode_id"):
            continue
        d = idx[r["episode_id"]]
        d["passes"].update(m.group(0).rstrip("-") for m in PASS.finditer(r.get("action") or ""))
        out = str(r.get("outcome") or "")
        for m in AB.finditer(out):
            a, b = int(m.group(1)), int(m.group(2))
            d["pairs"].append((a, b)); d["ints"].update({str(a), str(b), str(abs(a - b))})
        d["pcts"].update(m.group(0) for m in PCT.finditer(out))
        d["ints"].update(m.group(0) for m in NUM.finditer(PCT.sub(" ", out)))
    return idx


def pct_matches(tok: str, acts: dict) -> bool:
    """Printed percentage equal, or within rounding at the printed precision of 100(b-a)/b for some a -> b (b > 0)."""
    if tok in acts["pcts"]:
        return True
    val = float(tok.rstrip("%"))
    decimals = len(tok.rstrip("%").split(".")[1]) if "." in tok else 0
    tol = 0.5 * 10 ** (-decimals) + 1e-9
    for a, b in acts["pairs"]:
        if b > 0 and abs(val - 100.0 * (b - a) / b) <= tol:
            return True
        if a > 0 and abs(val - 100.0 * (a - b) / a) <= tol:      # "reduction" is usually relative to the start count
            return True
    return False


# --------------------------------------------------------------------------- note parsing --------------------------------
def _blank_names(text: str, names) -> str:
    for n in sorted({x for x in names if x}, key=len, reverse=True):
        text = text.replace(n, " ")
    return text


def sentences(note: str) -> list:
    return [s.strip() for s in SENT_SPLIT.split(note) if s and s.strip()]


def clauses(sentence: str) -> list:
    return [c.strip() for c in CLAUSE_SPLIT.split(sentence) if c and c.strip()]


def result_numbers(clause: str) -> list:
    """[(kind, token)] asserted as RESULTS in a clause: none if the clause is a prediction; ranges are blanked."""
    if PREDICTION.search(clause):
        return []
    text = RANGE_PCT.sub(" ", clause)
    out = [("pct", m.group(0)) for m in PCT.finditer(text)]
    text = PCT.sub(" ", text)
    out += [("int", m.group(0)) for m in NUM.finditer(text)]
    return out


def _num_ok(kind: str, tok: str, acts: dict) -> bool:
    return pct_matches(tok, acts) if kind == "pct" else tok in acts["ints"]


def judge(note: str, acts: dict | None, names=()) -> dict:
    """G, N, F, P and the rejection reason of one note against this episode's acts (None acts = episode unknown)."""
    text = _blank_names(note, names)
    F = bool(FIRST_PERSON_RECORD.search(text))
    if acts is None or not acts["passes"] and not acts["pairs"] and not acts["ints"]:
        practice = any(p.search(text) for p in PRACTICE_PHRASES)
        return dict(G=None, N=None, F=F, P=practice, reason="unknown-episode")
    sents = sentences(text)
    action_idx = [i for i, s in enumerate(sents) if any(m.group(0).rstrip("-") in acts["passes"] for m in PASS.finditer(s))]
    result_idx, asserted, mismatched = [], [], []
    for i, s in enumerate(sents):
        for c in clauses(s):
            nums = result_numbers(c)
            if not nums:
                continue
            asserted += nums
            ok = [_num_ok(k, t, acts) for k, t in nums]
            mismatched += [t for (k, t), o in zip(nums, ok) if not o]
            if any(ok):
                result_idx.append(i)
    G = any(abs(i - j) <= 1 for i in action_idx for j in result_idx)
    N = None if not asserted else not mismatched
    practice = (not G) and any(p.search(text) for p in PRACTICE_PHRASES)
    if G and (N is None or N):
        reason = "admitted"
    elif G:
        reason = "N-mismatch"
    elif practice:
        reason = "practice-only"
    elif not action_idx and not asserted:
        reason = "no-pass-run-here" if PASS.search(text) else "no-content"
    elif not action_idx:
        reason = "no-pass-run-here"
    elif not asserted:
        reason = "prediction-only" if PREDICTION.search(text) and (PCT.search(text) or NUM.search(text)) else "no-result-number"
    elif not result_idx:
        reason = "result-numbers-unmatched"
    else:
        reason = "not-adjacent"
    return dict(G=G, N=N, F=F, P=practice, reason=reason)


def canonical(note: str, names=()) -> str:
    t = _blank_names(note.lower(), [n.lower() for n in names])
    t = re.sub(r"[^a-z0-9%\-\s]", " ", t)
    t = re.sub(r"(?<![a-z0-9])-(?![a-z])", " ", t)      # keep '-mem2reg', drop stray dashes
    return re.sub(r"\s+", " ", t).strip()


def template(canon: str) -> str:
    t = PASS.sub("<PASS>", canon)
    t = PCT.sub("<NUM>", t)
    t = re.sub(r"(?<![a-z<])\d+(?:\.\d+)?", "<NUM>", t)
    return re.sub(r"\s+", " ", t).strip()


def _ngrams(canon: str, n: int = 5) -> set:
    toks = canon.split()
    if len(toks) < n:
        return {tuple(toks)} if toks else set()
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 1.0


# --------------------------------------------------------------------------- per life ------------------------------------
REASONS = ("admitted", "duplicate", "practice-only", "no-pass-run-here", "no-content", "prediction-only", "no-result-number",
           "result-numbers-unmatched", "not-adjacent", "N-mismatch", "unknown-episode")


class LifeState:
    """Running window of the previous WINDOW raw notes (canonical forms and 5-gram sets), across sleeps in order."""

    def __init__(self):
        self.canon: list = []
        self.grams: list = []

    def see(self, canon: str):
        self.canon.append(canon); self.grams.append(_ngrams(canon))
        if len(self.canon) > WINDOW:
            del self.canon[0]; del self.grams[0]


def gate_notes(items: list, idx: dict, state: LifeState) -> tuple:
    """Judge every NOTE segment of the thinking items (in order). Returns (per-note records, per-item admitted flags)."""
    notes, item_flags = [], []
    for it in items:
        if reg.item_kind(it) != "thinking":
            continue
        e = reg.episode_of(it)
        names = (e, e.split("/")[-1]) if e else ()
        acts = idx.get(e)
        admitted_any = False
        for note in reg.notes_of(it):
            j = judge(note, acts, names)
            canon = canonical(note, names)
            D = canon in state.canon
            grams = _ngrams(canon)
            near = any(_jaccard(grams, g) >= NEAR_DUP_JACCARD for g in state.grams)
            state.see(canon)
            reason = j["reason"]
            if reason == "admitted" and D:
                reason = "duplicate"
            adm_hi = bool(j["G"]) and (j["N"] is not False) and not D
            adm_lo = bool(j["G"]) and (j["N"] is True) and not D
            art_hi = j["F"] and bool(j["G"]) and (j["N"] is not False)
            art_lo = j["F"] and bool(j["G"]) and (j["N"] is True)
            admitted_any |= adm_hi
            notes.append(dict(episode=e, text=note[:240], G=j["G"], N=j["N"], F=j["F"], D=D, P=j["P"], near_dup=near,
                              template=template(canon), reason=reason, admit_hi=adm_hi, admit_lo=adm_lo,
                              artic_hi=art_hi, artic_lo=art_lo))
        item_flags.append(admitted_any)
    return notes, item_flags


def _rate(vals) -> float | None:
    vals = list(vals)
    return (sum(1 for v in vals if v) / len(vals)) if vals else None


def summarise(notes: list) -> dict:
    n = len(notes)
    out = dict(n_new_notes=n)
    if not n:
        out.update({k: None for k in ("unknown_share", "G_rate", "N_rate", "N_none_share", "F_rate", "D_rate", "P_rate",
                                       "T_top_template_share", "T_near_dup_share", "admission_hi", "admission_lo",
                                       "articulation_hi", "articulation_lo")})
        out.update(top_reasons=[], top_template="", examples={})
        return out
    known = [x for x in notes if x["G"] is not None]
    n_known = [x for x in notes if x["N"] is not None]
    out["unknown_share"] = 1 - len(known) / n
    out["G_rate"] = _rate(x["G"] for x in known)
    out["N_rate"] = _rate(x["N"] for x in n_known)
    out["N_none_share"] = 1 - len(n_known) / n
    out["F_rate"] = _rate(x["F"] for x in notes)
    out["D_rate"] = _rate(x["D"] for x in notes)
    out["P_rate"] = _rate(x["P"] for x in notes)
    tmpl = Counter(x["template"] for x in notes)
    top_t, top_c = tmpl.most_common(1)[0]
    out["T_top_template_share"] = top_c / n
    out["top_template"] = top_t[:160]
    out["T_near_dup_share"] = _rate(x["near_dup"] for x in notes)
    out["admission_hi"] = _rate(x["admit_hi"] for x in notes)
    out["admission_lo"] = _rate(x["admit_lo"] for x in notes)
    out["articulation_hi"] = _rate(x["artic_hi"] for x in notes)
    out["articulation_lo"] = _rate(x["artic_lo"] for x in notes)
    reasons = Counter(x["reason"] for x in notes if x["reason"] != "admitted")
    out["top_reasons"] = reasons.most_common(5)
    ex = defaultdict(list)
    for x in notes:
        if len(ex[x["reason"]]) < 2:
            ex[x["reason"]].append(x["text"][:200])
    out["examples"] = dict(ex)
    return out


def audit_life(root: str, life: str, sleeps=None) -> list:
    """One record per requested sleep. The gate is evaluated on EVERY sleep in order (the duplication window needs the
    whole history), then only the requested sleeps are returned. Records carry the per-sleep summary of the new notes, the
    cumulative admission so far, and -- on the last sleep on disk -- the fraction of that final corpus's thinking items
    that survive the gate (an item survives if any of its notes is admitted under the hi rule)."""
    ledger = os.path.join(root, life, "ledger.jsonl")
    if not os.path.exists(ledger):
        return []
    idx = episode_acts(prov.load_ledger(ledger))
    dirs = reg.sleep_dirs(root, life)
    order = list(dirs)
    if not order:
        return []
    arm = life.split("_")[0]
    state = LifeState()
    prev_set: set = set()
    recs, all_notes, item_admit = [], [], {}
    for i, s in enumerate(order):
        items = reg.load_items(dirs[s])
        new = [it for it in items if it not in prev_set]
        notes, flags = gate_notes(new, idx, state)
        for it, fl in zip([it for it in new if reg.item_kind(it) == "thinking"], flags):
            item_admit[it] = fl
        all_notes += notes
        rec = dict(life=life, arm=arm, sleep=s, prev_sleep=order[i - 1] if i else None, n_new_items=len(new),
                   n_thinking_new=sum(1 for it in new if reg.item_kind(it) == "thinking"))
        rec.update(summarise(notes))
        rec["life_admission_hi_so_far"] = _rate(x["admit_hi"] for x in all_notes)
        rec["life_admission_lo_so_far"] = _rate(x["admit_lo"] for x in all_notes)
        if i == len(order) - 1:
            think = [it for it in items if reg.item_kind(it) == "thinking"]
            rec["final_corpus_thinking_items"] = len(think)
            rec["final_corpus_survive_share"] = (sum(1 for it in think if item_admit.get(it)) / len(think)) if think else None
        recs.append(rec)
        prev_set = set(items)
    want = None if sleeps is None else set(sleeps)
    return [r for r in recs if want is None or r["sleep"] in want]


def life_summary(recs_all: list) -> dict:
    """A_s over the final four sleeps (mean of hi and lo), life admission, final-corpus survival, pooled top reasons."""
    last4 = recs_all[-4:]
    def mean(key):
        v = [r[key] for r in last4 if r.get(key) is not None]
        return sum(v) / len(v) if v else None
    reasons = Counter()
    for r in recs_all:
        for t, c in r.get("top_reasons") or []:
            reasons[t] += c
    fin = recs_all[-1]
    return dict(life=fin["life"], arm=fin["arm"], n_sleeps=len(recs_all), n_notes=sum(r["n_new_notes"] for r in recs_all),
                A_final4_hi=mean("articulation_hi"), A_final4_lo=mean("articulation_lo"),
                admission_hi=fin["life_admission_hi_so_far"], admission_lo=fin["life_admission_lo_so_far"],
                survive_final=fin.get("final_corpus_survive_share"), top_reasons=reasons.most_common(5))


CSV_COLS = ["life", "arm", "sleep", "prev_sleep", "n_new_items", "n_thinking_new", "n_new_notes", "unknown_share", "G_rate", "N_rate",
            "N_none_share", "F_rate", "D_rate", "P_rate", "T_top_template_share", "T_near_dup_share", "admission_hi", "admission_lo",
            "articulation_hi", "articulation_lo", "life_admission_hi_so_far", "life_admission_lo_so_far",
            "final_corpus_thinking_items", "final_corpus_survive_share", "top_reasons", "top_template"]


def write_outputs(out_dir: str, by_life: dict, summaries: list) -> str:
    os.makedirs(out_dir, exist_ok=True)
    for life, recs in by_life.items():
        json.dump(recs, open(os.path.join(out_dir, f"{life}.json"), "w"), indent=1)
    json.dump(dict(practice_phrases_version=PRACTICE_PHRASES_VERSION, window=WINDOW, near_dup_jaccard=NEAR_DUP_JACCARD,
                   lives=summaries), open(os.path.join(out_dir, "lives_summary.json"), "w"), indent=1)
    p = os.path.join(out_dir, "summary.csv")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS); w.writeheader()
        for recs in by_life.values():
            for r in recs:
                row = {c: r.get(c) for c in CSV_COLS}
                row["top_reasons"] = "; ".join(f"{t}={c}" for t, c in r.get("top_reasons") or [])
                w.writerow(row)
    return p


def _f(v) -> str:
    return "-" if v is None else f"{v:.3f}"


def _pair(lo, hi) -> str:
    return f"{_f(lo)}-{_f(hi)}"


def print_table(summaries: list) -> None:
    print("life arm sleeps notes A_final4[lo-hi] admission[lo-hi] survive_final top_reasons")
    pool = defaultdict(lambda: defaultdict(float))
    for s in summaries:
        top = ", ".join(f"{t}x{c}" for t, c in s["top_reasons"][:4])
        print(f"{s['life']} {s['arm']} {s['n_sleeps']} {s['n_notes']} {_pair(s['A_final4_lo'], s['A_final4_hi'])} "
              f"{_pair(s['admission_lo'], s['admission_hi'])} {_f(s['survive_final'])} {top}")
        n = s["n_notes"]
        if not n:
            continue
        d = pool[s["arm"]]; d["n"] += n; d["lives"] += 1
        for k in ("A_final4_hi", "A_final4_lo", "admission_hi", "admission_lo", "survive_final"):
            if s[k] is not None:
                d[k] += s[k] * n; d[k + "_n"] += n
    print("--- pooled by arm (note-weighted) ---")
    print("arm lives notes A_final4[lo-hi] admission[lo-hi] survive_final")
    for arm, d in sorted(pool.items()):
        def m(k):
            return (d[k] / d[k + "_n"]) if d[k + "_n"] else None
        print(f"{arm} {int(d['lives'])} {int(d['n'])} {_pair(m('A_final4_lo'), m('A_final4_hi'))} "
              f"{_pair(m('admission_lo'), m('admission_hi'))} {_f(m('survive_final'))}")
    print(f"(practice phrases {PRACTICE_PHRASES_VERSION}; window {WINDOW}; ledger scope = all acts of the episode over the life)")


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root"); ap.add_argument("--sleeps", default="0032,1024"); ap.add_argument("--lives", default="")
    ap.add_argument("--all-sleeps", action="store_true"); ap.add_argument("--out", nargs="?", const=DEFAULT_OUT, default=None)
    a = ap.parse_args(argv)
    sleeps = None if a.all_sleeps else a.sleeps.split(",")
    lives = a.lives.split(",") if a.lives else sorted(os.path.basename(p) for p in glob.glob(os.path.join(a.root, "R*_B_seed*"))
                                                    if os.path.isdir(p))
    by_life, summaries = {}, []
    for life in lives:
        recs_all = audit_life(a.root, life, None)       # every sleep: the window and the life summary need the history
        if not recs_all:
            continue
        summaries.append(life_summary(recs_all))
        by_life[life] = recs_all if sleeps is None else [r for r in recs_all if r["sleep"] in set(sleeps)]
    print_table(summaries)
    if a.out:
        print(f"wrote {len(by_life)} life JSON files and {write_outputs(a.out, by_life, summaries)}")
    return by_life


if __name__ == "__main__":
    main()
