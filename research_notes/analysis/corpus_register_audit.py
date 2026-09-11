#!/usr/bin/env python3
"""Register audit of the lives' sleep corpora (Rohin's formalisation 2026-09-12, THESIS_v2 section 3: the LoRA needs
FIRST-PERSON PROCEDURAL records with outcomes; pretraining supplies third-person descriptions; "reflection without
articulation" would show as notes that plan or generalise instead of recording what happened). CPU only; reads
<life>/sleep_*/corpus.json (the list under the "corpus" key).

Item kinds (the corpus mixes what the child wrote with harness-generated records):
  thinking   "Program <id>. My thinking: <child text>\\nSo I did: <ACT> -> <outcome>"  -- the only kind scored
  qa         "Program <id>. Q: which passes improve it?\\nA: <ACT> -> <outcome>"      (harness; counted, not scored)
  episodic   "[episodic] On <id> I predicted ... and measured: ..."                     (harness; counted, not scored)
  reflection "[reflection] My private thinking ..."  principle "PRINCIPLE: when ..."     other  anything else
For every thinking item the NOTE text (between 'NOTE:' and the next 'ACT:' / 'PREDICT:' / 'CLOCK:' / 'RECALL:' / 'So I did:')
is classified by crude word markers:
  first_person  'I' 'my' 'me' "I'm" "I've" "I'll"           generic   'generally' 'typically' 'usually' 'known to' 'tend to' 'are effective' 'often'
  prospective   'I expect' 'I will' "I'll" 'should' 'likely' 'plan to' 'I want' 'let me' 'I am going'
  retrospective 'reduced' 'got' 'gave' 'resulted' 'improved' 'worked' "didn't" 'did not' 'was' 'were' 'previous' 'last time' 'earlier' 'saw' 'noticed' 'turned out' 'led to'
  specific      a digit, a pass name ('-mem2reg' style) or the program's own name in the note
The item wrapper ("My thinking: ... So I did: ACT -> outcome") is added by the harness and is not scored: what is scored
is what the child itself wrote (the first NOTE segment, as in SEQ-050).

Cumulative corpora: the sleep-k corpus is (in every life inspected) a superset of the sleep-(k-1) corpus, so the rates
over ALL items are life-to-date averages. When the immediately preceding sleep directory exists on disk the audit
checks the superset property and ALSO reports the rates on the NEW items only (the delta since the previous sleep) --
that is the child's register at that age. `cumulative` is null when there is no previous sleep to compare with.

Usage:
  python3 corpus_register_audit.py ROOT [--sleeps 0032,1024] [--lives R2_B_seed0,...]      table for the listed sleeps (default: first and final)
  python3 corpus_register_audit.py ROOT --all-sleeps [--out DIR]                            every sleep_XXXX present
  --out DIR   writes DIR/<life>.json (per-sleep records: all-items rates, cumulative flag, new-items rates) and DIR/summary.csv
              (default DIR when --out is given without a value: research_notes/analysis/out/register/)
The stdout table (one row per life per sleep; then a per-arm, note-weighted pool) is unchanged from the SEQ-050 version."""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
from collections import defaultdict

RX = dict(first_person=re.compile(r"\b(I|my|me|I'm|I've|I'll)\b"),
          generic=re.compile(r"\b(generally|typically|usually|known to|tend to|are effective|is effective|often)\b", re.I),
          prospective=re.compile(r"\b(I expect|I will|I'll|should|likely|plan to|I want|let me|I am going)\b", re.I),
          retrospective=re.compile(r"\b(reduced|got|gave|resulted|improved|worked|didn't|did not|was|were|previous|last time|earlier|saw|noticed|turned out|led to)\b", re.I))
PASS = re.compile(r"(?<![A-Za-z])-[a-z][a-z0-9\-]{2,}")
NOTE = re.compile(r"NOTE:\s*(.*?)(?=\n?\s*(?:ACT:|PREDICT:|CLOCK:|RECALL:|So I did:)|\Z)", re.S)
RATE_KEYS = ("first_person", "prospective", "retrospective", "generic", "specific")
KINDS = ("thinking", "qa", "episodic", "reflection", "principle", "other")
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "register")


def note_of(item: str) -> str:
    """The first NOTE segment of the child's text (what SEQ-050 scored)."""
    m = NOTE.search(item)
    return (m.group(1) if m else "").strip()


def notes_of(item: str) -> list:
    """Every NOTE segment of the child's text (an item can carry two thoughts joined by ' ... ')."""
    return [m.group(1).strip() for m in NOTE.finditer(item) if m.group(1).strip()]


def episode_of(item: str) -> str:
    """The full episode id from the 'Program <id>.' prefix ('' when absent)."""
    m = re.match(r"Program\s+(\S+?)\.?(?:\s|$)", item)
    return m.group(1) if m else ""


def prog_of(item: str) -> str:
    """The program's short name (last path component of the episode id)."""
    e = episode_of(item)
    return e.split("/")[-1].rstrip(".") if e else ""


def item_kind(item: str) -> str:
    if not isinstance(item, str):
        return "other"
    if item.startswith("[episodic]"):
        return "episodic"
    if item.startswith("[reflection]"):
        return "reflection"
    if item.startswith("PRINCIPLE:"):
        return "principle"
    if "\nA: " in item or ". Q: " in item:
        return "qa"
    if "My thinking:" in item:
        return "thinking"
    return "other"


def load_items(path: str) -> list:
    c = json.load(open(path))
    items = c["corpus"] if isinstance(c, dict) else c
    return [it for it in items if isinstance(it, str)]


def sleep_dirs(root: str, life: str) -> dict:
    """{'0032': path_to_corpus.json, ...} for every sleep_XXXX/corpus.json present, ascending."""
    out = {}
    for p in sorted(glob.glob(os.path.join(root, life, "sleep_*", "corpus.json"))):
        s = os.path.basename(os.path.dirname(p))[len("sleep_"):]
        out[s] = p
    return out


def register_rates(items: list) -> dict:
    """Kind counts and the register rates over the thinking items that carry a NOTE."""
    kinds = {k: 0 for k in KINDS}
    notes = []
    for it in items:
        k = item_kind(it)
        kinds[k] += 1
        if k == "thinking":
            n = note_of(it)
            if n:
                notes.append((n, prog_of(it)))
    out = dict(n_items=len(items), n_notes=len(notes))
    out.update({f"n_{k}": v for k, v in kinds.items()})
    if not notes:
        out.update({k: None for k in RATE_KEYS}); out["mean_note_words"] = None
        return out
    cnt = defaultdict(int); words = 0
    for note, pr in notes:
        for k, rx in RX.items():
            cnt[k] += bool(rx.search(note))
        cnt["specific"] += bool(re.search(r"\d", note) or PASS.search(note) or (pr and pr.lower() in note.lower()))
        words += len(note.split())
    out.update({k: cnt[k] / len(notes) for k in RATE_KEYS})
    out["mean_note_words"] = words / len(notes)
    return out


def audit_life(root: str, life: str, sleeps=None) -> list:
    """One record per sleep: rates over all items, and -- when the preceding sleep on disk exists -- the superset check
    and the rates over the NEW items only. `sleeps` = list of sleep tags to report (default: every sleep present)."""
    dirs = sleep_dirs(root, life)
    order = list(dirs)
    want = order if sleeps is None else [s for s in sleeps if s in dirs]
    arm = life.split("_")[0]
    recs = []
    for s in want:
        items = load_items(dirs[s])
        rec = dict(life=life, arm=arm, sleep=s, path=dirs[s])
        rec.update(register_rates(items))
        i = order.index(s)
        if i > 0:
            prev = load_items(dirs[order[i - 1]])
            prev_set, cur_set = set(prev), set(items)
            new = [it for it in items if it not in prev_set]
            rec.update(prev_sleep=order[i - 1], cumulative=prev_set <= cur_set, n_new=len(new),
                       n_dropped=len(prev_set - cur_set))
            rec["new"] = register_rates(new)
        else:
            rec.update(prev_sleep=None, cumulative=None, n_new=None, n_dropped=None, new=None)
        recs.append(rec)
    return recs


CSV_COLS = (["life", "arm", "sleep", "n_items", "n_thinking", "n_qa", "n_episodic", "n_reflection", "n_principle", "n_other",
             "n_notes"] + list(RATE_KEYS) + ["mean_note_words", "prev_sleep", "cumulative", "n_new", "n_dropped", "new_n_notes"]
            + [f"new_{k}" for k in RATE_KEYS] + ["new_mean_note_words"])


def csv_row(rec: dict) -> dict:
    row = {c: rec.get(c) for c in CSV_COLS if not c.startswith("new_")}
    new = rec.get("new") or {}
    row["new_n_notes"] = new.get("n_notes")
    for k in RATE_KEYS:
        row[f"new_{k}"] = new.get(k)
    row["new_mean_note_words"] = new.get("mean_note_words")
    return row


def write_outputs(out_dir: str, by_life: dict) -> str:
    os.makedirs(out_dir, exist_ok=True)
    for life, recs in by_life.items():
        json.dump(recs, open(os.path.join(out_dir, f"{life}.json"), "w"), indent=1)
    csv_path = os.path.join(out_dir, "summary.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS)
        w.writeheader()
        for recs in by_life.values():
            for r in recs:
                w.writerow(csv_row(r))
    return csv_path


def _f(v) -> str:
    return "-" if v is None else f"{v:.3f}"


def print_table(by_life: dict) -> None:
    pool = defaultdict(lambda: defaultdict(float))
    print("life sleep items notes first_person prospective retrospective generic specific mean_note_words")
    for life, recs in by_life.items():
        for r in recs:
            n = r["n_notes"]
            if not n:
                print(f"{life} {r['sleep']} {r['n_items']} 0 - - - - - -"); continue
            print(f"{life} {r['sleep']} {r['n_items']} {n} " + " ".join(_f(r[k]) for k in RATE_KEYS) + f" {r['mean_note_words']:.1f}")
            key = (r["arm"], r["sleep"])
            pool[key]["n"] += n; pool[key]["lives"] += 1
            for k in RATE_KEYS:
                pool[key][k] += r[k] * n
    print("--- pooled by arm and sleep (note-weighted) ---")
    print("arm sleep lives notes first_person prospective retrospective generic specific")
    for (arm, s), d in sorted(pool.items()):
        n = d["n"]
        print(f"{arm} {s} {int(d['lives'])} {int(n)} " + " ".join(f"{d[k]/n:.3f}" for k in RATE_KEYS))


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root"); ap.add_argument("--sleeps", default="0032,1024"); ap.add_argument("--lives", default="")
    ap.add_argument("--all-sleeps", action="store_true", help="every sleep_XXXX present (overrides --sleeps)")
    ap.add_argument("--out", nargs="?", const=DEFAULT_OUT, default=None, help="write per-life JSON and summary.csv under DIR")
    a = ap.parse_args(argv)
    sleeps = None if a.all_sleeps else a.sleeps.split(",")
    lives = a.lives.split(",") if a.lives else sorted(os.path.basename(p) for p in glob.glob(os.path.join(a.root, "R*_B_seed*"))
                                                    if os.path.isdir(p))
    by_life = {}
    for life in lives:
        recs = audit_life(a.root, life, sleeps)
        if recs:
            by_life[life] = recs
    print_table(by_life)
    if a.out:
        p = write_outputs(a.out, by_life)
        print(f"wrote {len(by_life)} life JSON files and {p}")
    return by_life


if __name__ == "__main__":
    main()
