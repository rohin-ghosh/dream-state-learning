#!/usr/bin/env python3
"""Provenance audit of the lives' sleep corpora (THESIS_v2 section 2: "the model distills, it does not originate" -- a
memory with no traceable external source is confabulated). CPU only; reads <life>/ledger.jsonl and <life>/sleep_*/corpus.json.

For every THINKING item ("Program <id>. My thinking: ... So I did: ACT -> outcome") the child's own NOTE text (every NOTE
segment; the harness wrapper is not scored) is scanned for FACTUAL TOKENS:
  number   an integer of >= 2 digits (not part of a decimal fraction)      pct   a percentage such as 45.2%
  pass     an LLVM pass name, '-[a-z][a-z0-9-]{2,}' ('-mem2reg', '-loop-unroll', ...)
after the program's own name (full episode id and its last path component) has been removed from the note, so the
program is never counted as a fact. A token is SOURCED when it appears in the episode's own ledger record:
  pass    -> in the 'action' of any act row with that episode_id      (conservative: acts only, as specified)
  number  -> the same digit string in any act 'outcome' or any note/thought 'note' with that episode_id
  pct     -> the same percentage string in any act outcome or note/thought text with that episode_id
A second, looser column, sourced_any_episode, asks whether the token appears anywhere in the life's ledger (any program):
an unsourced-here-but-sourced-elsewhere token is a CROSS-REFERENCE (the child cited another program's result), not an
invention; a token unsourced anywhere is the confabulation candidate.

ORDERING CAVEAT (read this before quoting the numbers). The ledger has kinds act / note / thought with episode_id and
tick only -- no episode counter, no sleep marker. Ticks are per chunk and rows of the ~8 concurrently running episodes
interleave, so a tick-reset heuristic finds ~47,000 "episodes" in a 1,024-episode life (RP_B_seed402): episode order is
NOT recoverable from the ledger alone. The source set for an item is therefore ALL ledger rows with that episode_id over
the whole life, not only those before the sleep in which the item appears. This is lenient (a later outcome can "source"
an earlier note), so a token reported unsourced is unsourced under the most generous reading; the per-sleep rows group
items by the corpus they appear in, nothing more. Corpora are cumulative; with --all-sleeps the new items of each sleep
are also reported separately (the register-audit delta).

Per life per sleep: n_thinking, factual tokens by type, share sourced (this episode), share sourced anywhere in the life,
items with >= 1 unsourced token (the confabulation-rate candidate, both readings), and the 10 most frequent unsourced
tokens with counts (so one can see whether they are invented pass names, invented numbers or matcher artefacts).

Usage:
  python3 corpus_provenance_audit.py ROOT [--sleeps 0032,1024] [--lives R2_B_seed0,...] [--all-sleeps] [--out DIR]
  --out DIR   writes DIR/<life>.json and DIR/summary.csv (default DIR when given without a value:
              research_notes/analysis/out/provenance/)"""
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


def _load_register():
    spec = importlib.util.spec_from_file_location("corpus_register_audit", os.path.join(_HERE, "corpus_register_audit.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reg = _load_register()
PASS = reg.PASS
NUM = re.compile(r"(?<![\d.])\d{2,}(?![\d.]\d)")    # >= 2 digits; not inside 0.4515 or 12.5; '857' in '857 -> 470' ok
PCT = re.compile(r"\d+(?:\.\d+)?%")
DEFAULT_OUT = os.path.join(_HERE, "out", "provenance")
TOKEN_TYPES = ("number", "pct", "pass")


def factual_tokens(note: str, program_names=(), with_pos: bool = False) -> list:
    """[(type, token), ...] in the note after the program's own names are blanked; percentages are taken first and
    blanked so their digits are not also counted as numbers. with_pos=True appends a third field: True when the token
    ends the note (the compile truncates each thought at 400 characters, so a pass name cut mid-token ends the note)."""
    text = note
    for name in sorted({n for n in program_names if n}, key=len, reverse=True):
        text = text.replace(name, " ")
    end = len(text.rstrip(" .…"))
    out = []
    for m in PCT.finditer(text):
        out.append(("pct", m.group(0), m.end() >= end))
    text = PCT.sub(" ", text)
    out += [("number", m.group(0), m.end() >= end) for m in NUM.finditer(text)]
    out += [("pass", m.group(0).rstrip("-"), m.end() >= end) for m in PASS.finditer(text)]
    return out if with_pos else [(t, tok) for t, tok, _ in out]


def _truncated_pass(tok: str, src: dict) -> bool:
    """An unsourced pass token that ENDS the note and is a strict prefix of a pass the episode actually ran is the
    400-character truncation of the compile, not an invention ('-simpl' for '-simplifycfg')."""
    return any(p != tok and p.startswith(tok) for p in src["passes"])


def load_ledger(path: str) -> list:
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def source_index(rows: list) -> dict:
    """episode_id -> dict(passes=set, numbers=set, pcts=set) over the whole life, plus '*' for the union."""
    idx = defaultdict(lambda: dict(passes=set(), numbers=set(), pcts=set()))
    for r in rows:
        e = r.get("episode_id")
        if not e:
            continue
        k = r.get("kind")
        if k == "act":
            act = r.get("action") or ""
            idx[e]["passes"].update(m.group(0).rstrip("-") for m in PASS.finditer(act))
            txt = str(r.get("outcome") or "")
        elif k in ("note", "thought"):
            txt = str(r.get("note") or "")
        else:
            continue
        idx[e]["pcts"].update(m.group(0) for m in PCT.finditer(txt))
        idx[e]["numbers"].update(m.group(0) for m in NUM.finditer(PCT.sub(" ", txt)))
    union = dict(passes=set(), numbers=set(), pcts=set())
    for d in idx.values():
        for key in union:
            union[key] |= d[key]
    idx["*"] = union
    return idx


def _sourced(tok_type: str, tok: str, src: dict) -> bool:
    if tok_type == "pass":
        return tok in src["passes"]
    if tok_type == "pct":
        return tok in src["pcts"]
    return tok in src["numbers"]


def provenance_rates(items: list, idx: dict) -> dict:
    """Token- and item-level provenance over the thinking items of one corpus."""
    n_think = 0; n_missing_ep = 0; n_truncated = 0
    tok_n = Counter(); tok_src = Counter(); tok_src_any = Counter()
    items_unsourced = 0; items_unsourced_any = 0
    unsourced = Counter(); unsourced_any = Counter()
    empty = dict(passes=set(), numbers=set(), pcts=set())
    for it in items:
        if reg.item_kind(it) != "thinking":
            continue
        n_think += 1
        e = reg.episode_of(it)
        names = (e, e.split("/")[-1]) if e else ()
        src = idx.get(e)
        if src is None:
            n_missing_ep += 1
            src = empty
        toks = []
        for note in reg.notes_of(it):
            toks += factual_tokens(note, names, with_pos=True)
        bad_here = bad_any = False
        for t, tok, at_end in toks:
            if t == "pass" and at_end and not _sourced(t, tok, src) and _truncated_pass(tok, src):
                n_truncated += 1            # the compile's 400-char cut, not a fact: excluded from every rate
                continue
            tok_n[t] += 1
            here = _sourced(t, tok, src)
            anyw = here or _sourced(t, tok, idx["*"])
            tok_src[t] += here; tok_src_any[t] += anyw
            if not here:
                bad_here = True; unsourced[f"{t}:{tok}"] += 1
            if not anyw:
                bad_any = True; unsourced_any[f"{t}:{tok}"] += 1
        items_unsourced += bad_here; items_unsourced_any += bad_any
    n_tok = sum(tok_n.values())
    out = dict(n_thinking=n_think, n_thinking_without_ledger_episode=n_missing_ep, n_tokens=n_tok, n_truncated_pass=n_truncated)
    for t in TOKEN_TYPES:
        out[f"n_{t}"] = tok_n[t]
        out[f"sourced_{t}"] = (tok_src[t] / tok_n[t]) if tok_n[t] else None
    out["share_sourced"] = (sum(tok_src.values()) / n_tok) if n_tok else None
    out["share_sourced_any_episode"] = (sum(tok_src_any.values()) / n_tok) if n_tok else None
    out["items_with_unsourced"] = items_unsourced
    out["confabulation_rate"] = (items_unsourced / n_think) if n_think else None
    out["items_with_unsourced_any_episode"] = items_unsourced_any
    out["confabulation_rate_any_episode"] = (items_unsourced_any / n_think) if n_think else None
    out["top_unsourced"] = unsourced.most_common(10)
    out["top_unsourced_any_episode"] = unsourced_any.most_common(10)
    return out


def audit_life(root: str, life: str, sleeps=None) -> list:
    ledger = os.path.join(root, life, "ledger.jsonl")
    if not os.path.exists(ledger):
        return []
    idx = source_index(load_ledger(ledger))
    dirs = reg.sleep_dirs(root, life)
    order = list(dirs)
    want = order if sleeps is None else [s for s in sleeps if s in dirs]
    arm = life.split("_")[0]
    recs = []
    for s in want:
        items = reg.load_items(dirs[s])
        rec = dict(life=life, arm=arm, sleep=s, n_items=len(items), source_scope="all ledger rows of the episode_id, whole life")
        rec.update(provenance_rates(items, idx))
        i = order.index(s)
        if i > 0:
            prev = set(reg.load_items(dirs[order[i - 1]]))
            new = [it for it in items if it not in prev]
            rec.update(prev_sleep=order[i - 1], n_new=len(new), new=provenance_rates(new, idx))
        else:
            rec.update(prev_sleep=None, n_new=None, new=None)
        recs.append(rec)
    return recs


CSV_COLS = (["life", "arm", "sleep", "n_items", "n_thinking", "n_tokens", "n_truncated_pass", "n_number", "n_pct", "n_pass", "sourced_number", "sourced_pct",
             "sourced_pass", "share_sourced", "share_sourced_any_episode", "items_with_unsourced", "confabulation_rate",
             "confabulation_rate_any_episode", "n_thinking_without_ledger_episode", "top_unsourced", "prev_sleep", "n_new",
             "new_n_thinking", "new_share_sourced", "new_confabulation_rate", "new_confabulation_rate_any_episode"])


def csv_row(rec: dict) -> dict:
    row = {c: rec.get(c) for c in CSV_COLS if not c.startswith("new_")}
    row["top_unsourced"] = "; ".join(f"{t}={c}" for t, c in rec.get("top_unsourced") or [])
    new = rec.get("new") or {}
    row["new_n_thinking"] = new.get("n_thinking"); row["new_share_sourced"] = new.get("share_sourced")
    row["new_confabulation_rate"] = new.get("confabulation_rate")
    row["new_confabulation_rate_any_episode"] = new.get("confabulation_rate_any_episode")
    return row


def write_outputs(out_dir: str, by_life: dict) -> str:
    os.makedirs(out_dir, exist_ok=True)
    for life, recs in by_life.items():
        json.dump(recs, open(os.path.join(out_dir, f"{life}.json"), "w"), indent=1)
    p = os.path.join(out_dir, "summary.csv")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS); w.writeheader()
        for recs in by_life.values():
            for r in recs:
                w.writerow(csv_row(r))
    return p


def _f(v) -> str:
    return "-" if v is None else f"{v:.3f}"


def print_table(by_life: dict) -> None:
    print("life sleep thinking tokens(num/pct/pass) truncated sourced_here sourced_anywhere confab_rate confab_rate_anywhere top_unsourced")
    for life, recs in by_life.items():
        for r in recs:
            top = ", ".join(f"{t}x{c}" for t, c in r["top_unsourced"][:5])
            print(f"{life} {r['sleep']} {r['n_thinking']} {r['n_tokens']}({r['n_number']}/{r['n_pct']}/{r['n_pass']}) {r['n_truncated_pass']} "
                  f"{_f(r['share_sourced'])} {_f(r['share_sourced_any_episode'])} {_f(r['confabulation_rate'])} "
                  f"{_f(r['confabulation_rate_any_episode'])} {top}")


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root"); ap.add_argument("--sleeps", default="0032,1024"); ap.add_argument("--lives", default="")
    ap.add_argument("--all-sleeps", action="store_true"); ap.add_argument("--out", nargs="?", const=DEFAULT_OUT, default=None)
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
        print(f"wrote {len(by_life)} life JSON files and {write_outputs(a.out, by_life)}")
    return by_life


if __name__ == "__main__":
    main()
