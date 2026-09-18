"""Offline tests for the two analysis-only corpus audits (research_notes/analysis/corpus_register_audit.py and
corpus_provenance_audit.py): a synthetic life with a ledger and two CUMULATIVE sleep corpora is written by the test.
Run: python3 -m pytest tests/test_corpus_audits.py -q"""
import csv
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.join(HERE, "..", "research_notes", "analysis")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ANALYSIS, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reg = _load("corpus_register_audit")
prov = _load("corpus_provenance_audit")

EP_A = "benchmark://cbench-v1/bitcount"
EP_B = "benchmark://mibench-v1/sha256-2"          # digits in the program name must never count as facts


def _think(ep, note, act, outcome):
    return f"Program {ep}. My thinking: PREDICT: 0.25  \nNOTE: {note}\n\nACT: {act}  \nCLOCK: chunk 1/16 | alive 1s\nSo I did: {act} -> {outcome}"


def _qa(ep, act, outcome):
    return f"Program {ep}. Q: which passes improve it?\nA: {act} -> {outcome}"


def make_life(root, life="R2_B_seed9"):
    d = os.path.join(root, life)
    os.makedirs(d)
    ledger = [
        dict(kind="note", episode_id=EP_A, tick=1, note="I will start with -mem2reg since it usually helps."),
        dict(kind="act", episode_id=EP_A, tick=1, action="-mem2reg, -sroa", prediction=0.25,
             outcome="instructions 857 -> 470 (45.2% reduction)", score=0.45, surprise=0.2, time_cost=8.9),
        dict(kind="thought", episode_id=EP_A, tick=1, note="PREDICT: 0.25\nNOTE: I will start with -mem2reg.\nACT: -mem2reg, -sroa"),
        dict(kind="act", episode_id=EP_B, tick=1, action="-gvn, -simplifycfg", prediction=0.3,
             outcome="instructions 3898 -> 2172 (44.3% reduction)", score=0.44, surprise=0.1, time_cost=5.0),
    ]
    with open(os.path.join(d, "ledger.jsonl"), "w") as fh:
        for r in ledger:
            fh.write(json.dumps(r) + "\n")
    # sleep 2: two thinking items (first person / prospective; one retrospective), one QA item
    s2 = [_think(EP_A, "I expect -mem2reg to reduce the count; I will apply it first.", "-mem2reg, -sroa",
                 "instructions 857 -> 470 (45.2% reduction)"),
          _think(EP_B, "Earlier the same passes reduced sha256-2 from 3898 to 2172 instructions.", "-gvn, -simplifycfg",
                 "instructions 3898 -> 2172 (44.3% reduction)"),
          _qa(EP_A, "-mem2reg, -sroa", "instructions 857 -> 470 (45.2% reduction)")]
    # sleep 4: cumulative superset + two NEW items: a bare recipe (no person, no outcome) and a planted UNSOURCED number
    s4 = list(s2) + [
        _think(EP_A, "Apply -mem2reg, -sroa, -gvn, -simplifycfg.", "-mem2reg, -sroa", "instructions 857 -> 470 (45.2% reduction)"),
        _think(EP_B, "This cut 999 instructions with -loop-unroll, about 88.8%.", "-gvn, -simplifycfg",
               "instructions 3898 -> 2172 (44.3% reduction)"),
        "[episodic] On " + EP_A + " I predicted 0.25 for -mem2reg, -sroa and measured: instructions 857 -> 470 (45.2% reduction).",
    ]
    for tag, items in (("0002", s2), ("0004", s4)):
        os.makedirs(os.path.join(d, f"sleep_{tag}"))
        json.dump(dict(corpus=items, n_new=len(items)), open(os.path.join(d, f"sleep_{tag}", "corpus.json"), "w"))
    return life


def test_item_kinds_and_note_extraction():
    assert reg.item_kind(_qa(EP_A, "-sroa", "x")) == "qa"
    assert reg.item_kind(_think(EP_A, "n", "-sroa", "x")) == "thinking"
    assert reg.item_kind("[episodic] On p I predicted 0.1 for -x and measured: y") == "episodic"
    assert reg.item_kind("[reflection] My private thinking after episode 3: ...") == "reflection"
    assert reg.item_kind("PRINCIPLE: when x, do y") == "principle"
    it = _think(EP_B, "Earlier it reduced 3898 to 2172.", "-gvn", "o")
    assert reg.note_of(it) == "Earlier it reduced 3898 to 2172." and reg.notes_of(it) == [reg.note_of(it)]
    assert reg.episode_of(it) == EP_B and reg.prog_of(it) == "sha256-2"


def test_register_trajectory_cumulative_delta_and_qa_exclusion(tmp_path):
    life = make_life(str(tmp_path))
    recs = reg.audit_life(str(tmp_path), life)          # all sleeps
    assert [r["sleep"] for r in recs] == ["0002", "0004"]
    r2, r4 = recs
    # kinds: QA and episodic items are counted, not scored
    assert r2["n_items"] == 3 and r2["n_thinking"] == 2 and r2["n_qa"] == 1 and r2["n_notes"] == 2
    assert r4["n_items"] == 6 and r4["n_thinking"] == 4 and r4["n_qa"] == 1 and r4["n_episodic"] == 1 and r4["n_notes"] == 4
    # sleep 2 rates: item 1 first person + prospective; item 2 retrospective ('Earlier', 'reduced') + specific
    assert r2["first_person"] == 0.5 and r2["prospective"] == 0.5 and r2["retrospective"] == 0.5 and r2["specific"] == 1.0
    assert r2["cumulative"] is None and r2["new"] is None
    # sleep 4 is a superset of sleep 2 -> cumulative, 3 new items, no drops
    assert r4["cumulative"] is True and r4["prev_sleep"] == "0002" and r4["n_new"] == 3 and r4["n_dropped"] == 0
    # life-to-date rates dilute; the NEW-items rates show the register at that age: no first person, no prospective
    assert r4["first_person"] == 0.25 and r4["prospective"] == 0.25
    new = r4["new"]
    assert new["n_items"] == 3 and new["n_thinking"] == 2 and new["n_episodic"] == 1 and new["n_notes"] == 2
    assert new["first_person"] == 0.0 and new["prospective"] == 0.0 and new["specific"] == 1.0
    assert new["retrospective"] == 0.0                  # 'cut' is not a marker: the new items record nothing that happened
    # a non-cumulative corpus is detected as such
    s3 = os.path.join(str(tmp_path), life, "sleep_0003")
    os.makedirs(s3)
    json.dump(dict(corpus=[_think(EP_A, "n", "-sroa", "o")]), open(os.path.join(s3, "corpus.json"), "w"))
    recs = reg.audit_life(str(tmp_path), life, sleeps=["0003", "0004"])
    assert recs[0]["cumulative"] is False and recs[0]["n_dropped"] == 3 and recs[0]["n_new"] == 1
    assert recs[1]["prev_sleep"] == "0003" and recs[1]["cumulative"] is False


def test_provenance_flags_planted_number_not_sourced_pass(tmp_path):
    life = make_life(str(tmp_path))
    recs = prov.audit_life(str(tmp_path), life)
    r2, r4 = recs
    # sleep 2: tokens 3898, 2172 (sourced in EP_B's outcome); pass -mem2reg in item 1 (sourced in EP_A's act)
    assert r2["n_thinking"] == 2 and r2["n_pass"] == 1 and r2["n_number"] == 2 and r2["n_pct"] == 0
    assert r2["share_sourced"] == 1.0 and r2["confabulation_rate"] == 0.0 and r2["top_unsourced"] == []
    # the program name 'sha256-2' contributed no token (no '256')
    assert all(not t.endswith(":256") for t, _ in r4["top_unsourced"])
    # sleep 4 new items: the recipe item has 4 sourced passes (-gvn and -simplifycfg are EP_B's acts, not EP_A's!)
    new = r4["new"]
    assert new["n_thinking"] == 2
    unsourced = dict(new["top_unsourced"])
    assert unsourced.get("number:999") == 1 and unsourced.get("pct:88.8%") == 1 and unsourced.get("pass:-loop-unroll") == 1
    assert "pass:-mem2reg" not in unsourced and "pass:-sroa" not in unsourced
    # -gvn / -simplifycfg were run on EP_B, never on EP_A: unsourced HERE but sourced ELSEWHERE in the life (cross-reference)
    assert unsourced.get("pass:-gvn") == 1 and unsourced.get("pass:-simplifycfg") == 1
    any_unsourced = dict(new["top_unsourced_any_episode"])
    assert "pass:-gvn" not in any_unsourced and any_unsourced.get("number:999") == 1
    assert new["confabulation_rate"] == 1.0 and new["confabulation_rate_any_episode"] == 0.5
    assert r4["confabulation_rate_any_episode"] == 0.25          # 1 of 4 thinking items invents facts
    assert r4["share_sourced_any_episode"] > r4["share_sourced"]
    # a truncated pass name ending the note is excluded, not flagged
    life2 = "R2_B_seed10"
    d = os.path.join(str(tmp_path), life2); os.makedirs(os.path.join(d, "sleep_0002"))
    with open(os.path.join(d, "ledger.jsonl"), "w") as fh:
        fh.write(json.dumps(dict(kind="act", episode_id=EP_A, tick=1, action="-simplifycfg", outcome="instructions 10 -> 9")) + "\n")
    json.dump(dict(corpus=[_think(EP_A, "I will run -simplifycfg first, then maybe -simpl", "-simplifycfg", "instructions 10 -> 9")]),
              open(os.path.join(d, "sleep_0002", "corpus.json"), "w"))
    (r,) = prov.audit_life(str(tmp_path), life2)
    assert r["n_truncated_pass"] == 1 and r["n_pass"] == 1 and r["share_sourced"] == 1.0 and r["confabulation_rate"] == 0.0


def test_factual_tokens_matcher_edges():
    toks = prov.factual_tokens("Expected 40-70% reduction; PREDICT 0.55 is my guess; 857 -> 470; try -mem2reg and -O3.",
                               ("benchmark://cbench-v1/bitcount", "bitcount"))
    d = dict((t, k) for k, t in toks)
    assert d["70%"] == "pct" and d["40"] == "number" and d["857"] == "number" and d["470"] == "number"
    assert "55" not in d and "0.55" not in d                     # decimal fraction is not an integer fact
    assert d["-mem2reg"] == "pass" and "-O3" not in d
    # the program's own name is blanked before tokenising
    assert prov.factual_tokens("sha256-2 improved by 3898.", ("benchmark://mibench-v1/sha256-2", "sha256-2")) == [("number", "3898")]
    # with_pos marks the token that ends the note (the compile's 400-character cut)
    toks = prov.factual_tokens("I ran -mem2reg then -simpl", (), with_pos=True)
    assert toks == [("pass", "-mem2reg", False), ("pass", "-simpl", True)]
    src = dict(passes={"-mem2reg", "-simplifycfg"}, numbers=set(), pcts=set())
    assert prov._truncated_pass("-simpl", src) and not prov._truncated_pass("-gvn", src) and not prov._truncated_pass("-mem2reg", src)


def test_cli_writes_json_and_csv(tmp_path):
    life = make_life(str(tmp_path))
    out_r = str(tmp_path / "out_reg"); out_p = str(tmp_path / "out_prov")
    for script, out in (("corpus_register_audit.py", out_r), ("corpus_provenance_audit.py", out_p)):
        res = subprocess.run([sys.executable, os.path.join(ANALYSIS, script), str(tmp_path), "--all-sleeps", "--out", out],
                             capture_output=True, text=True)
        assert res.returncode == 0, res.stderr
        assert os.path.exists(os.path.join(out, f"{life}.json")) and os.path.exists(os.path.join(out, "summary.csv"))
        rows = list(csv.DictReader(open(os.path.join(out, "summary.csv"))))
        assert [r["sleep"] for r in rows] == ["0002", "0004"] and rows[1]["n_new"] == "3"
        assert res.stdout.splitlines()[0].startswith("life sleep ")
    reg_rows = list(csv.DictReader(open(os.path.join(out_r, "summary.csv"))))
    assert reg_rows[1]["cumulative"] == "True" and reg_rows[1]["new_first_person"] == "0.0"
    prov_rows = list(csv.DictReader(open(os.path.join(out_p, "summary.csv"))))
    assert "number:999=1" in prov_rows[1]["top_unsourced"]
    # default (legacy) mode: first and final sleep table, unchanged header, pooled section present
    res = subprocess.run([sys.executable, os.path.join(ANALYSIS, "corpus_register_audit.py"), str(tmp_path), "--sleeps", "0002,0004"],
                         capture_output=True, text=True)
    lines = res.stdout.splitlines()
    assert lines[0] == "life sleep items notes first_person prospective retrospective generic specific mean_note_words"
    assert lines[1].startswith(f"{life} 0002 3 2 0.500 0.500 0.500") and "--- pooled by arm and sleep (note-weighted) ---" in lines
