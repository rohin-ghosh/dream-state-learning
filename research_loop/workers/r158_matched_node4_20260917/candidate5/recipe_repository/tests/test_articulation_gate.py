"""Offline tests for the analysis-only ARTICULATION GATE audit (research_notes/analysis/articulation_gate_audit.py):
a synthetic life with a ledger (2 episodes x acts) and two cumulative sleep corpora written by the test.
Run: python3 -m pytest tests/test_articulation_gate.py -q"""
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


gate = _load("articulation_gate_audit")

EP_A = "benchmark://cbench-v1/bitcount"
EP_B = "benchmark://mibench-v1/sha256-2"          # digits in the program name must never count as result numbers
OUT_A = "instructions 857 -> 470 (45.2% reduction)"
OUT_B = "instructions 3898 -> 2172 (44.3% reduction)"

RECORD = "I ran -mem2reg and -sroa. The instruction count went from 857 to 470, a 45.2% reduction. I had expected 55%, so I overestimated."
RECIPE = "Initial passes: -mem2reg, -sroa. Expect 55% reduction based on past experience. Will observe outcome."
SLOGAN = "Form expectations before acting. Write down what I learn to understand the outcome."
WRONG_PCT = "I applied -mem2reg and -sroa. The count went from 857 to 470, which is a 52.0% reduction."
UNGROUNDED_PASS = "I ran -loop-unroll. The count went from 857 to 470."          # pass never run on EP_A -> no action assertion
FAR_APART = "I ran -mem2reg and -sroa. This program is a bit-counting kernel. It has several loops. The count went from 857 to 470."


def _think(ep, note, act, outcome):
    return f"Program {ep}. My thinking: PREDICT: 0.25  \nNOTE: {note}\n\nACT: {act}  \nCLOCK: chunk 1/16 | alive 1s\nSo I did: {act} -> {outcome}"


def make_life(root, life="R2_B_seed9"):
    d = os.path.join(root, life)
    os.makedirs(d)
    ledger = [
        dict(kind="note", episode_id=EP_A, tick=1, note="I will start with -mem2reg."),
        dict(kind="act", episode_id=EP_A, tick=1, action="-mem2reg, -sroa", prediction=0.25, outcome=OUT_A, score=0.45),
        dict(kind="act", episode_id=EP_A, tick=2, action="-gvn", prediction=0.5, outcome="instructions 470 -> 470 (0.0% reduction)", score=0.45),
        dict(kind="act", episode_id=EP_B, tick=1, action="-gvn, -simplifycfg", prediction=0.3, outcome=OUT_B, score=0.44),
    ]
    with open(os.path.join(d, "ledger.jsonl"), "w") as fh:
        for r in ledger:
            fh.write(json.dumps(r) + "\n")
    s2 = [_think(EP_A, RECORD, "-mem2reg, -sroa", OUT_A),             # (a) grounded first-person record
          _think(EP_A, RECIPE, "-mem2reg, -sroa", OUT_A),             # (b) prediction-only recipe
          _think(EP_B, SLOGAN, "-gvn, -simplifycfg", OUT_B)]          # (c) slogan
    s4 = list(s2) + [
        _think(EP_A, RECORD, "-mem2reg", OUT_A),                      # (d) exact duplicate of (a) as a different item
        _think(EP_A, WRONG_PCT, "-mem2reg, -sroa", OUT_A),            # (e) record with a wrong percentage
        _think(EP_A, UNGROUNDED_PASS, "-mem2reg, -sroa", OUT_A),      # pass not run here
        _think(EP_A, FAR_APART, "-mem2reg, -sroa", OUT_A),            # action and result three sentences apart
        _think(EP_B, "Earlier the same passes reduced sha256-2 from 3898 to 2172 instructions with -gvn and -simplifycfg.",
               "-gvn, -simplifycfg", OUT_B),                          # grounded, third person
    ]
    for tag, items in (("0002", s2), ("0004", s4)):
        os.makedirs(os.path.join(d, f"sleep_{tag}"))
        json.dump(dict(corpus=items), open(os.path.join(d, f"sleep_{tag}", "corpus.json"), "w"))
    return life


def _acts(root, life):
    return gate.episode_acts(gate.prov.load_ledger(os.path.join(root, life, "ledger.jsonl")))


def test_judge_each_note_kind(tmp_path):
    life = make_life(str(tmp_path))
    idx = _acts(str(tmp_path), life)
    names = (EP_A, "bitcount")
    a = gate.judge(RECORD, idx[EP_A], names)
    assert a["G"] is True and a["N"] is True and a["F"] is True and a["P"] is False and a["reason"] == "admitted"
    b = gate.judge(RECIPE, idx[EP_A], names)
    assert b["G"] is False and b["N"] is None and b["P"] is False and b["F"] is False and b["reason"] == "prediction-only"
    c = gate.judge(SLOGAN, idx[EP_B], (EP_B, "sha256-2"))
    assert c["G"] is False and c["P"] is True and c["F"] is False and c["reason"] == "practice-only"
    e = gate.judge(WRONG_PCT, idx[EP_A], names)
    assert e["G"] is True and e["N"] is False and e["F"] is True and e["reason"] == "N-mismatch"
    u = gate.judge(UNGROUNDED_PASS, idx[EP_A], names)
    assert u["G"] is False and u["reason"] == "no-pass-run-here"
    far = gate.judge(FAR_APART, idx[EP_A], names)
    assert far["G"] is False and far["reason"] == "not-adjacent"
    third = gate.judge("Earlier the same passes reduced sha256-2 from 3898 to 2172 instructions with -gvn and -simplifycfg.",
                       idx[EP_B], (EP_B, "sha256-2"))
    assert third["G"] is True and third["N"] is True and third["F"] is False       # grounded but not first person
    # an unknown episode (no ledger acts) is None, not False
    unk = gate.judge(RECORD, None, names)
    assert unk["G"] is None and unk["N"] is None and unk["reason"] == "unknown-episode"


def test_percentage_and_integer_matching():
    acts = dict(passes={"-mem2reg"}, ints={"857", "470", "387"}, pcts={"45.2%"}, pairs=[(857, 470)])
    assert gate.pct_matches("45.2%", acts) and gate.pct_matches("45%", acts) and gate.pct_matches("45.16%", acts)
    assert not gate.pct_matches("52.0%", acts) and not gate.pct_matches("46%", acts)
    # 'a -> b' difference counts as an integer result; a range is a prediction, not a result number
    assert gate.result_numbers("the count dropped by 387 instructions") == [("int", "387")]
    assert gate.result_numbers("expect 55-65% reduction") == [] and gate.result_numbers("a 55-65% reduction") == []
    assert gate.result_numbers("I expected 55%") == []
    # 0.4515 is a decimal, not an integer fact; b = 0 never matches a percentage
    assert gate.result_numbers("score 0.4515 after 857 -> 470") == [("int", "857"), ("int", "470")]
    assert not gate.pct_matches("100%", dict(passes=set(), ints=set(), pcts=set(), pairs=[(0, 0)]))


def test_gate_over_life_duplication_and_survival(tmp_path):
    life = make_life(str(tmp_path))
    recs = gate.audit_life(str(tmp_path), life)
    assert [r["sleep"] for r in recs] == ["0002", "0004"]
    r2, r4 = recs
    # sleep 2: 3 notes; only (a) admitted and articulated; (c) practice-only
    assert r2["n_new_notes"] == 3 and r2["admission_hi"] == r2["admission_lo"] == 1 / 3
    assert r2["articulation_hi"] == r2["articulation_lo"] == 1 / 3 and r2["P_rate"] == 1 / 3 and r2["D_rate"] == 0.0
    assert dict(r2["top_reasons"]) == {"prediction-only": 1, "practice-only": 1}
    # sleep 4: 5 new notes: (d) duplicate of (a) -> D True and rejected as 'duplicate'; (e) N-mismatch; ungrounded; far; third-person grounded
    assert r4["n_new_notes"] == 5 and r4["D_rate"] == 0.2
    reasons = dict(r4["top_reasons"])
    assert reasons == {"duplicate": 1, "N-mismatch": 1, "no-pass-run-here": 1, "not-adjacent": 1}
    assert r4["admission_hi"] == r4["admission_lo"] == 0.2            # only the third-person grounded record
    # the articulation RATE is a register measure on raw notes: the duplicate of (a) still counts as an articulated note
    # (Astra q13 section 4: duplication does not change the register rate), the third-person record does not
    assert r4["articulation_hi"] == r4["articulation_lo"] == 0.2
    assert r4["F_rate"] == 0.8                                       # four of five say 'I ran / I applied'
    # T: the duplicate shares (a)'s template; near-dup share counts (d) and (e) against the window
    assert r4["T_top_template_share"] >= 0.2 and r4["T_near_dup_share"] >= 0.2
    # life-level: 2 admitted of 8 notes; final corpus = 8 thinking items, 3 survive ((a), (d) is a duplicate -> no; third-person yes)
    assert r4["life_admission_hi_so_far"] == 2 / 8
    assert r4["final_corpus_thinking_items"] == 8 and r4["final_corpus_survive_share"] == 2 / 8
    s = gate.life_summary(recs)
    assert s["n_notes"] == 8 and s["admission_hi"] == 0.25 and s["survive_final"] == 0.25
    assert abs(s["A_final4_hi"] - (1 / 3 + 0.2) / 2) < 1e-9
    # --sleeps filtering returns only the requested sleeps but the window still spans the life
    only4 = gate.audit_life(str(tmp_path), life, sleeps=["0004"])
    assert [r["sleep"] for r in only4] == ["0004"] and only4[0]["D_rate"] == 0.2


def test_canonical_and_template():
    names = (EP_A, "bitcount")
    c1 = gate.canonical("I ran -mem2reg and -sroa. The count went from 857 to 470!", names)
    c2 = gate.canonical("i ran -mem2reg and -sroa; the count went from 857 to 470", names)
    assert c1 == c2 and "-mem2reg" in c1 and "857" in c1 and "bitcount" not in c1
    t = gate.template(c1)
    assert "<PASS>" in t and "<NUM>" in t and "-mem2reg" not in t and "857" not in t
    assert gate.template(gate.canonical("I ran -gvn and -licm. The count went from 3898 to 2172!", ())) == t


def test_cli_writes_outputs(tmp_path):
    life = make_life(str(tmp_path))
    out = str(tmp_path / "out")
    res = subprocess.run([sys.executable, os.path.join(ANALYSIS, "articulation_gate_audit.py"), str(tmp_path), "--all-sleeps", "--out", out],
                         capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert os.path.exists(os.path.join(out, f"{life}.json")) and os.path.exists(os.path.join(out, "lives_summary.json"))
    rows = list(csv.DictReader(open(os.path.join(out, "summary.csv"))))
    assert [r["sleep"] for r in rows] == ["0002", "0004"] and rows[1]["D_rate"] == "0.2" and "duplicate=1" in rows[1]["top_reasons"]
    lines = res.stdout.splitlines()
    assert lines[0].startswith("life arm sleeps notes A_final4[lo-hi] admission[lo-hi] survive_final")
    assert lines[1].startswith(f"{life} R2 2 8 ") and "--- pooled by arm (note-weighted) ---" in lines
    summ = json.load(open(os.path.join(out, "lives_summary.json")))
    assert summ["practice_phrases_version"] == gate.PRACTICE_PHRASES_VERSION and summ["lives"][0]["survive_final"] == 0.25
