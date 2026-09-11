#!/usr/bin/env python3
"""Register audit of the lives' sleep corpora (Rohin's formalisation 2026-09-12: the LoRA needs FIRST-PERSON PROCEDURAL
records with outcomes; pretraining supplies third-person descriptions; "reflection without articulation" would show as
notes that plan or generalise instead of recording what happened). CPU only; reads <life>/sleep_*/corpus.json.
For every item the NOTE text (between 'NOTE:' and the next 'ACT:' / 'PREDICT:' / end) is classified by crude markers:
  first_person  'I ' / 'my ' / 'me '                      generic   'generally' 'typically' 'usually' 'known to' 'tend to' 'are effective'
  prospective   'I expect' 'I will' "I'll" 'should' 'likely' 'plan to'
  retrospective 'reduced' 'got' 'gave' 'resulted' 'improved' 'worked' "didn't" 'did not' 'was' 'were' 'previous' 'last time' 'earlier' 'saw'
  specific      a digit, a pass name ('-mem2reg' style) or the program's own name in the note
The item wrapper ("My thinking: ... So I did: ACT -> outcome") is added by the harness and is not scored: what is scored
is what the child itself wrote. Prints one row per life per sleep (first and final by default) and a per-arm pool.
Usage: python3 corpus_register_audit.py ~/v6_out [--sleeps 0032,1024] [--lives R2_B_seed0,...]"""
import argparse, glob, json, os, re, sys
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("root"); ap.add_argument("--sleeps", default="0032,1024"); ap.add_argument("--lives", default="")
a = ap.parse_args()
sleeps = a.sleeps.split(",")
lives = a.lives.split(",") if a.lives else sorted(os.path.basename(p) for p in glob.glob(os.path.join(a.root, "R*_B_seed*")) if os.path.isdir(p))

RX = dict(first_person=re.compile(r"\b(I|my|me|I'm|I've|I'll)\b"),
          generic=re.compile(r"\b(generally|typically|usually|known to|tend to|are effective|is effective|often)\b", re.I),
          prospective=re.compile(r"\b(I expect|I will|I'll|should|likely|plan to|I want|let me|I am going)\b", re.I),
          retrospective=re.compile(r"\b(reduced|got|gave|resulted|improved|worked|didn't|did not|was|were|previous|last time|earlier|saw|noticed|turned out|led to)\b", re.I))
PASS = re.compile(r"(?<![A-Za-z])-[a-z][a-z0-9\-]{2,}")
NOTE = re.compile(r"NOTE:\s*(.*?)(?=\n?\s*(?:ACT:|PREDICT:|CLOCK:|RECALL:|So I did:)|\Z)", re.S)


def note_of(item: str) -> str:
    m = NOTE.search(item)
    return (m.group(1) if m else "").strip()


def prog_of(item: str) -> str:
    m = re.match(r"Program\s+(\S+)", item)
    return m.group(1).split("/")[-1].rstrip(".") if m else ""


rows, pool = [], defaultdict(lambda: defaultdict(float))
print("life sleep items notes first_person prospective retrospective generic specific mean_note_words")
for life in lives:
    arm = life.split("_")[0]
    for s in sleeps:
        p = os.path.join(a.root, life, f"sleep_{s}", "corpus.json")
        if not os.path.exists(p):
            continue
        c = json.load(open(p)); items = c["corpus"] if isinstance(c, dict) else c
        notes = [(note_of(it), prog_of(it)) for it in items if isinstance(it, str)]
        notes = [(n, pr) for n, pr in notes if n]
        n = len(notes)
        if not n:
            print(f"{life} {s} {len(items)} 0 - - - - - -"); continue
        cnt = defaultdict(int); words = 0
        for note, pr in notes:
            for k, rx in RX.items():
                cnt[k] += bool(rx.search(note))
            cnt["specific"] += bool(re.search(r"\d", note) or PASS.search(note) or (pr and pr.lower() in note.lower()))
            words += len(note.split())
        vals = {k: cnt[k] / n for k in ("first_person", "prospective", "retrospective", "generic", "specific")}
        print(f"{life} {s} {len(items)} {n} " + " ".join(f"{vals[k]:.3f}" for k in vals) + f" {words/n:.1f}")
        key = (arm, s)
        pool[key]["n"] += n; pool[key]["lives"] += 1
        for k, v in vals.items():
            pool[key][k] += v * n
print("--- pooled by arm and sleep (note-weighted) ---")
print("arm sleep lives notes first_person prospective retrospective generic specific")
for (arm, s), d in sorted(pool.items()):
    n = d["n"]
    print(f"{arm} {s} {int(d['lives'])} {int(n)} " + " ".join(f"{d[k]/n:.3f}" for k in ("first_person", "prospective", "retrospective", "generic", "specific")))
