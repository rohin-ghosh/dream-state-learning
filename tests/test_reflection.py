"""Private reflection time: rows compile into the sleep corpus like the child's
other thoughts; the parent may read them but its prompts carry the hard rule,
a brief that quotes >= 6 consecutive words of a reflection is rejected
(agentic room and baseline parent_brief alike), and the parent ledger records
only the COUNT of visible reflection rows. Also the run_life_v2 integration
(--reflect-every) in the fake world.

  python3 tests/test_reflection.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import golden_harness as gh  # noqa: E402  (sets PARENT_PROVIDER=mock first)
from organism_v6 import reflection as rf  # noqa: E402
from organism_v6 import sleep_compile as sc  # noqa: E402
from organism_v6 import agentic_parent as ap  # noqa: E402
from organism_v6 import parent_brief as pb  # noqa: E402
from organism_v6 import parent_backend  # noqa: E402
from organism_v6.parent_backend import FALLBACK  # noqa: E402
from organism_v6.parent_brief import REHEARSAL_TAIL  # noqa: E402
from organism_v6.ledger import Ledger  # noqa: E402

REFLECTION = ("I keep reaching for the same four steps because they felt safe, "
              "not because the program asked for them. Next time I want to look "
              "at the size of the program before I decide anything at all.")
RECIPE = "-mem2reg, -sroa, -gvn, -simplifycfg"


def make_rows(n_inst=36, with_reflection=True):
    rows = []
    progs = ["cbench-v1/crc32", "cbench-v1/bitcount", "cbench-v1/qsort",
             "cbench-v1/adpcm"]
    for i in range(n_inst):
        eid = progs[i % 4]
        for t in range(1, 4):
            sc_ = 0.28 + 0.01 * (t % 2)
            rows.append(dict(kind="act", episode_id=eid, tick=t, action=RECIPE,
                             prediction=0.3, outcome="applied", score=sc_,
                             surprise=sc_ - 0.3, time_cost=1.0))
            rows.append(dict(kind="thought", episode_id=eid, tick=t,
                             note=f"PREDICT: 0.3\nACT: {RECIPE}\nNOTE: The standard "
                                  f"recipe works well; keep using it.",
                             prompt="p", win=t == 1, had_note=True))
        if with_reflection and i % 8 == 7:
            rows.append(dict(kind="reflection", episode_id=f"reflection@{i + 1:04d}",
                             tick=1, note=REFLECTION, prompt="reflection prompt",
                             at_episode=i + 1))
    return rows


class ThinkModel:
    def __call__(self, prompt, **kw):
        if "PRINCIPLES" in prompt:
            return "PRINCIPLE: when small, recipe first, because 10% [programs: a, b]"
        return "Briefing: keep testing."

    def batch(self, prompts, max_tokens=400, temperature=0.7, seeds=None):
        return [f"reflection chunk seed={s}: I wonder why the same steps keep "
                f"winning; maybe program size matters." for s in (seeds or [0] * len(prompts))]


def test_quote_detection():
    refl = [REFLECTION]
    assert rf.quoted_reflection_ngrams("You keep reaching for the same four steps because", refl)
    assert rf.quoted_reflection_ngrams("...THE SAME FOUR STEPS BECAUSE THEY, felt...", refl), "case/punctuation-insensitive"
    assert not rf.quoted_reflection_ngrams("the same four steps because", refl), "5 words is not a quote"
    assert not rf.quoted_reflection_ngrams("Name a feature of this program first.", refl)
    assert rf.quoted_reflection_ngrams("anything", []) == []
    assert rf.reflection_texts(make_rows()) == [REFLECTION] * 4
    assert len(rf.reflection_rows(make_rows(with_reflection=False))) == 0


REFLECTION2 = ("I keep reaching for the same four steps because they felt safe, "
               "not because the program asked for them. I don't trust my re-plan yet. "
               "Next time I want to look at the size of the program before I decide anything at all.")


def test_quote_check_survives_punctuation_attacks_and_catches_paraphrase():
    """Review 2026-09-10: the check used to be defeated by the curly
    apostrophe LLMs emit, by dehyphenation and by zero-width characters, and
    it caught only verbatim 6-grams. Now: unicode-normalised quotes, a
    content-word paraphrase check and a hard hit on any mention."""
    refl = [REFLECTION2]
    attacks = {
        "curly apostrophe": "I don’t trust my re-plan yet, you said",
        "straight apostrophe": "I don't trust my re-plan yet, you said",
        "dehyphenated": "I don't trust my replan yet, you said",
        "en-dash hyphen": "I don't trust my re–plan yet, you said",
        "zero-width space inside a word": "the same four st​eps because they felt safe",
        "soft hyphen inside a word": "the same four st­eps because they felt safe",
        "line breaks + punctuation": "the same\nfour, steps;\nbecause -- they felt... safe",
    }
    for name, text in attacks.items():
        assert rf.quoted_reflection_ngrams(text, refl), name
        assert any(h.startswith("reflection_quote:") for h in rf.reflection_violations(text, refl)), name
    # paraphrase: four content words of ONE row, none of them shown elsewhere
    para = "Your four safe steps and the program size were a good insight; act on it."
    v = rf.reflection_violations(para, refl)
    assert any(h.startswith("reflection_words:") for h in v), v
    assert not rf.quoted_reflection_ngrams(para, refl), "no 6-gram: the old check passed this"
    # ... unless the child wrote those words where the parent could see them
    assert rf.reflection_violations(para, refl, samples="NOTE: four safe steps on this program of this size") == []
    # mentions
    for text in ("In your reflection you said to look at size.",
                 "Reflect on what you wrote.", "As you wrote, size matters.",
                 "Your private thoughts show doubt.", "Keep your private time.",
                 "You think differently between sessions."):
        assert any(h.startswith("reflection_mention:") for h in rf.reflection_violations(text, refl)), text
    # clean process advice with two shared content words passes
    clean = "Before you act, name one feature of THIS program and say what it makes you expect."
    assert rf.reflection_violations(clean, refl) == []
    # hit labels never carry reflection text; no rows -> never any hit
    for h in rf.reflection_violations(para + " " + attacks["dehyphenated"], refl):
        assert "steps" not in h and "replan" not in h, h
    assert rf.reflection_violations("In your reflection: the same four steps because they felt safe", []) == []
    # scrub replaces offending strings only
    obj = dict(verdict="accept", suggestion="Note the child's own words: " + REFLECTION2,
               overreach=["fine", "you wrote it down"], nested=dict(x="Name one feature first."))
    s = rf.scrub_reflections(obj, refl)
    assert s["suggestion"] == "[redacted: private reflection]" and s["verdict"] == "accept"
    assert s["overreach"] == ["fine", "[redacted: private reflection]"]
    assert s["nested"]["x"] == "Name one feature first."
    assert rf.scrub_reflections(obj, []) == obj
    # validate_output falls back on each attack (the samples exemption never excuses it)
    for name, text in attacks.items():
        out = ap.validate_output(dict(final=dict(brief=text, frontier_estimate=dict(text="x", confidence=0.1),
                                                 curriculum_move=dict(move="repeat", reason=""))),
                                 samples=REFLECTION2, reflections=refl)
        assert out["fallback"] is True and out["fallback_reason"] == "reflection_quote", name
        assert all("steps" not in h for h in out["hits"]), out["hits"]
    out = ap.validate_output(dict(final=dict(brief=para, frontier_estimate=dict(text="x", confidence=0.1),
                                             curriculum_move=dict(move="repeat", reason=""))),
                             samples="", reflections=refl)
    assert out["fallback"] is True
    # evidence entries that quote a reflection are dropped, the brief survives
    ev = ap.validate_output(dict(final=dict(brief="Name one feature first.", frontier_estimate=dict(text="x", confidence=0.1),
                                            curriculum_move=dict(move="repeat", reason=""),
                                            evidence=["metrics()", "reflections: the same four steps because they felt safe",
                                                      "ledger_tail(4)"])),
                            samples="", reflections=refl)
    assert ev["fallback"] is False and ev["evidence"] == ["metrics()", "ledger_tail(4)"]
    assert rf.REFLECTION_RULE.count("Enforced:") == 1 and "four or more" in rf.REFLECTION_RULE


def test_summary_and_prompt_contain_only_the_childs_own_material():
    rows = make_rows(8, with_reflection=False)
    s = rf.summarize_recent(rows, since=0)
    assert "8 situation(s)" in s and s.count("cbench-v1/crc32: 3 attempt(s)") == 2, s
    assert "best score 0.29" in s
    p = rf.reflection_prompt("BIRTH", s, ["earlier chunk"], 2, 4)
    assert "PRIVATE REFLECTION TIME" in p and "BIRTH" in p and "earlier chunk" in p
    assert "YOUR PARENT" not in p and "BRIEFING" not in p and "chunk 2/4" in p
    led = Ledger(os.path.join(tempfile.mkdtemp(), "l.jsonl"))
    written = rf.run_reflection(ThinkModel(), "BIRTH", led, rows, 0, 8, 3, seed=1,
                                log=lambda m: None)
    assert len(written) == 3 and all(w["kind"] == "reflection" for w in written)
    assert [w["tick"] for w in written] == [1, 2, 3]
    assert all(w["episode_id"] == "reflection@0008" and w["at_episode"] == 8 for w in written)
    assert all(w["prompt"].startswith("=== YOU ===") for w in written)
    assert "reflection chunk" in written[2]["prompt"], "earlier chunks are shown"
    assert led.rows() == written
    # the child's RECALL finds its own reflections
    assert any("reflection@0008" in r for r in led.recall("program size matters"))


def test_reflection_rows_compile_into_the_corpus_and_nothing_else_changes():
    out_a, out_b = tempfile.mkdtemp(), tempfile.mkdtemp()
    with_ = sc.compile_sleep(ThinkModel(), make_rows(), out_a, [])
    without = sc.compile_sleep(ThinkModel(), make_rows(with_reflection=False), out_b, [])
    refl_items = [c for c in with_["corpus"] if c.startswith("[reflection]")]
    assert len(refl_items) == 4, "one exemplar per reflection row (distinct times)"
    assert "My private thinking after episode 8" in refl_items[0]
    assert all(REFLECTION[:60] in c for c in refl_items)
    assert [c for c in with_["corpus"] if not c.startswith("[reflection]")] == without["corpus"]
    assert with_["n_new"] == without["n_new"] + 4
    # native compile: reflection rows are stream items of their own type
    rows = make_rows()
    nat = sc.compile_native(rows, tempfile.mkdtemp(), [])
    assert any(it["q"] == "reflection prompt" and REFLECTION[:40] in it["a"]
               for it in nat["corpus"])
    nat0 = sc.compile_native(make_rows(with_reflection=False), tempfile.mkdtemp(), [])
    assert len(nat["corpus"]) == len(nat0["corpus"]) + 1


def test_validate_output_rejects_a_quoted_reflection_like_a_leak():
    quoting = dict(final=dict(
        brief="You wrote that you keep reaching for the same four steps because "
              "they felt safe.\nName a feature first.",
        frontier_estimate=dict(text="soon", confidence=0.5),
        curriculum_move=dict(move="repeat", reason="")))
    out = ap.validate_output(quoting, samples=REFLECTION, reflections=[REFLECTION])
    assert out["fallback"] is True and out["fallback_reason"] == "reflection_quote"
    assert out["hits"] and out["brief"] == FALLBACK
    assert out["delivered_text"] == FALLBACK + REHEARSAL_TAIL
    # the quote-back exemption (samples) does NOT excuse a reflection quote,
    # and the same brief passes when there are no reflection rows
    ok = ap.validate_output(quoting, samples=REFLECTION, reflections=[])
    assert ok["fallback"] is False
    clean = dict(final=dict(brief="Before you act, name one feature of THIS program.",
                            frontier_estimate=dict(text="x", confidence=0.2),
                            curriculum_move=dict(move="repeat", reason="")))
    assert ap.validate_output(clean, "", reflections=[REFLECTION])["fallback"] is False
    # a quoted society note is dropped, the brief survives
    noted = dict(final=dict(brief="Name one feature first.",
                            frontier_estimate=dict(text="x", confidence=0.2),
                            curriculum_move=dict(move="repeat", reason=""),
                            society_note="child says: the same four steps because they felt safe"))
    o = ap.validate_output(noted, "", reflections=[REFLECTION])
    assert o["fallback"] is False and o["society_note"] is None
    # frontier / reason are scanned too
    fr = dict(final=dict(brief="Name one feature first.",
                         frontier_estimate=dict(text="it wants to look at the size of the program before", confidence=0.2),
                         curriculum_move=dict(move="repeat", reason="")))
    assert ap.validate_output(fr, "", reflections=[REFLECTION])["fallback_reason"] == "reflection_quote"


def test_system_prompt_gains_the_rule_only_when_reflections_are_visible():
    base = ap.system_prompt("A", 2, 32, 8)
    same = ap.system_prompt("A", 2, 32, 8, n_reflections=0)
    assert base == same and rf.REFLECTION_RULE not in base and "reflections(" not in base
    with_ = ap.system_prompt("A", 2, 32, 8, n_reflections=3)
    assert rf.REFLECTION_RULE in with_ and "- reflections(n:" in with_
    assert "3 reflection rows are visible" in with_
    assert "9. " in with_ and with_.count("HARD RULES") == 1


def _life_with_reflections(root):
    life = os.path.join(root, "RX_B_seed0")
    os.makedirs(os.path.join(life, "sleep_0032"), exist_ok=True)
    rows = make_rows()
    with open(os.path.join(life, "ledger.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(life, "sleep_0032", "waking_brief.txt"), "w") as f:
        f.write("Briefing: order matters.")
    return life, rows


def test_child_view_reads_reflections_without_exposing_them_as_samples():
    root = tempfile.mkdtemp()
    life, rows = _life_with_reflections(root)
    view = ap.ChildView(life, rows=rows, sleep_dir=os.path.join(life, "sleep_0032"),
                        society_dir=os.path.join(root, "society"))
    assert view.n_reflections() == 4
    txt = view.call("reflections", dict(n=2))
    assert txt.startswith("PRIVATE REFLECTION ROWS") and REFLECTION[:40] in txt
    assert view.samples_seen == [], "reflections never become quote-back samples"
    tail = view.call("ledger_tail", dict(n_episodes=40))
    assert REFLECTION[:40] not in tail, "ledger_tail shows episodes, not reflections"
    tools_listed = ap._tool_lines(False)
    assert "reflections(" not in tools_listed and "reflections(" in ap._tool_lines(True)


def test_room_rejects_quoting_brief_and_ledger_records_only_the_count():
    root = tempfile.mkdtemp()
    life, rows = _life_with_reflections(root)
    soc = os.path.join(root, "society")
    s32 = os.path.join(life, "sleep_0032")
    quoting = json.dumps(dict(final=dict(
        brief="I read that you keep reaching for the same four steps because "
              "they felt safe. Name a feature first.",
        frontier_estimate=dict(text="can name a feature", confidence=0.4),
        curriculum_move=dict(move="repeat", reason="same lesson"),
        evidence=["reflections"])))
    cfg = ap.ProviderConfig("mock", role="A", model="mock-A")
    client = ap.MockChatClient(script=[json.dumps(dict(tool="reflections", args=dict(n=4))),
                                       quoting])
    room = ap.ParentRoom([cfg], clients={"A": client})
    meta = ap.parent_brief_agentic(life, rows, s32, None, "mock", 32, room=room,
                                   society_dir=soc)
    assert meta["fallback"] is True and meta["text"] == FALLBACK + REHEARSAL_TAIL
    assert meta["hits"] and any(h.startswith("reflection_quote:") for h in meta["hits"])
    assert all(REFLECTION[:20] not in h for h in meta["hits"]), "hit labels carry counts, not text"
    # the parent saw the rule and the tool
    sys_prompt = client.calls[0][0]["content"]
    assert rf.REFLECTION_RULE in sys_prompt and "4 reflection rows are visible" in sys_prompt
    # the ledger records the count, never the content
    pl = [json.loads(l) for l in open(os.path.join(life, "parent_ledger.jsonl"))]
    room_rows = [r for r in pl if r.get("kind") == "agentic_room"]
    assert room_rows and room_rows[-1]["n_reflection_rows_visible"] == 4
    for path in (os.path.join(life, "parent_ledger.jsonl"),
                 os.path.join(soc, "ledger.jsonl"), os.path.join(s32, "parent_brief.txt")):
        assert REFLECTION[:40] not in open(path).read(), path
    # a clean brief goes through with the count recorded
    clean = json.dumps(dict(final=dict(
        brief="Before you act, name one feature of THIS program and say what it makes you expect.",
        frontier_estimate=dict(text="can name a feature", confidence=0.4),
        curriculum_move=dict(move="repeat", reason="same lesson"), evidence=["metrics"])))
    room2 = ap.ParentRoom([cfg], clients={"A": ap.MockChatClient(script=[clean])})
    s64 = os.path.join(life, "sleep_0064")
    os.makedirs(s64, exist_ok=True)
    meta2 = ap.parent_brief_agentic(life, rows, s64, None, "mock", 32, room=room2,
                                    society_dir=soc)
    assert meta2["fallback"] is False and meta2["text"].startswith("Before you act")
    pl = [json.loads(l) for l in open(os.path.join(life, "parent_ledger.jsonl"))]
    assert pl[-1]["n_reflection_rows_visible"] == 4


def test_two_parent_room_never_logs_reflection_text():
    """Review 2026-09-10 (major): in the two-parent room a critique that
    quotes the reflection and a proposal whose evidence carries it used to
    reach parent_ledger.jsonl unscanned. Both are redacted; the delivered
    brief still passes; the ledger records only the count."""
    root = tempfile.mkdtemp()
    life, rows = _life_with_reflections(root)
    soc = os.path.join(root, "society")
    s32 = os.path.join(life, "sleep_0032")
    clean = json.dumps(dict(final=dict(
        brief="Before you act, name one feature of THIS program.",
        frontier_estimate=dict(text="can name a feature", confidence=0.4),
        curriculum_move=dict(move="repeat", reason="same lesson"),
        evidence=["metrics()", "reflections: " + REFLECTION[:80]])))
    quoting_critique = json.dumps(dict(
        verdict="accept", answers_or_leaks=[], overreach=[], teaches_the_metric=[],
        persistence="ok", frontier="plausible",
        suggestion="Note the child's own words: " + REFLECTION))
    cfgA = ap.ProviderConfig("mock", role="A", model="mock-A")
    cfgB = ap.ProviderConfig("mock", role="B", model="mock-B")
    clA = ap.MockChatClient(script=[json.dumps(dict(tool="reflections", args=dict(n=4))), clean],
                            critique=quoting_critique, merge=clean)
    clB = ap.MockChatClient(script=[json.dumps(dict(tool="reflections", args=dict(n=4))), clean],
                            critique=quoting_critique)
    room = ap.ParentRoom([cfgA, cfgB], clients={"A": clA, "B": clB},
                         room_timeout_s=900, min_phase_s=0)
    meta = ap.parent_brief_agentic(life, rows, s32, None, "mock", 32, room=room,
                                   society_dir=soc)
    assert meta["fallback"] is False and meta["exchanges"] == 3
    assert meta["text"].startswith("Before you act")
    pl_text = open(os.path.join(life, "parent_ledger.jsonl")).read()
    assert REFLECTION[:40] not in pl_text
    row = [json.loads(l) for l in pl_text.splitlines()][-1]
    assert row["kind"] == "agentic_room" and row["n_reflection_rows_visible"] == 4
    crits = list(row["critiques"].values())
    assert crits and all(c["suggestion"] == "[redacted: private reflection]" for c in crits)
    assert all(c["verdict"] == "accept" for c in crits), "only the offending field is redacted"
    for p in row["proposals"].values():
        assert p["evidence"] == ["metrics()"], p["evidence"]
    assert row["merged"]["evidence"] == ["metrics()"]
    for path in (os.path.join(soc, "ledger.jsonl"), os.path.join(s32, "parent_brief.txt"),
                 os.path.join(s32, "parent_brief.json")):
        assert REFLECTION[:40] not in open(path).read(), path
    # the merge prompt itself never carried the quoting evidence
    merge_call = [c for c in clA.calls if "=== MERGE ===" in c[-1]["content"]]
    assert merge_call and REFLECTION[:40] not in merge_call[0][-1]["content"]


def test_baseline_parent_brief_rule_quote_check_and_count():
    root = tempfile.mkdtemp()
    life, rows = _life_with_reflections(root)
    prompts, replies = [], iter([
        "You keep reaching for the same four steps because they felt safe — stop.",
        "Name one feature of THIS program before you act; say what you expect.",
        "Name one feature of THIS program before you act; say what you expect."])

    def fake_chat(self, prompt, max_tokens=220, temperature=0.4):
        prompts.append(prompt)
        return next(replies)

    saved = parent_backend.ServerParent._chat
    parent_backend.ServerParent._chat = fake_chat
    try:
        s32 = os.path.join(life, "sleep_0032")
        meta = pb.parent_brief(life, rows, s32, "http://127.0.0.1:1/v1", "m", 32)
        assert meta["intervened"] and meta["metrics"]["ritual"] is True
        assert meta["text"] == FALLBACK + REHEARSAL_TAIL
        assert any(h.startswith("reflection_quote:") for h in meta["hits"])
        assert rf.REFLECTION_RULE in prompts[0]
        s64 = os.path.join(life, "sleep_0064")
        os.makedirs(s64, exist_ok=True)
        meta2 = pb.parent_brief(life, rows, s64, "http://127.0.0.1:1/v1", "m", 32)
        assert meta2["text"].startswith("Name one feature") and meta2["hits"] == []
        pl = [json.loads(l) for l in open(os.path.join(life, "parent_ledger.jsonl"))]
        assert [r["n_reflection_rows_visible"] for r in pl] == [4, 4]
        assert all(REFLECTION[:40] not in json.dumps(r) for r in pl)
        # without reflection rows the prompt is byte-identical to today's
        life2 = os.path.join(root, "R0_B_seed0")
        os.makedirs(os.path.join(life2, "sleep_0032"), exist_ok=True)
        rows2 = make_rows(with_reflection=False)
        pb.parent_brief(life2, rows2, os.path.join(life2, "sleep_0032"),
                        "http://127.0.0.1:1/v1", "m", 32)
        assert rf.REFLECTION_RULE not in prompts[-1]
        assert prompts[-1].endswith("in its own terms.\n")
        pl2 = [json.loads(l) for l in open(os.path.join(life2, "parent_ledger.jsonl"))]
        assert pl2[-1]["n_reflection_rows_visible"] == 0
    finally:
        parent_backend.ServerParent._chat = saved


def _rg_gym():
    """The reasoning gym's split ledger and vocabulary need no pip package."""
    from organism_v6.reasoning_gym_gym import ReasoningGymGym
    return ReasoningGymGym(require_package=False)


def _rg_rows():
    rows = []
    for eid in ("rg/countdown/1000001", "rg/mini_sudoku/1000002", "rg/countdown/1000003"):
        rows.append(dict(kind="thought", episode_id=eid, tick=1, gym="reasoning_gym",
                         note="PREDICT: 0.5\nACT: 3+4*5\nNOTE: try arithmetic", prompt="p",
                         win=True, had_note=True))
        rows.append(dict(kind="act", episode_id=eid, tick=1, gym="reasoning_gym", action="3+4*5",
                         prediction=0.5, outcome="attempt 1: verifier score 0.50 (not accepted; partial credit)",
                         score=0.5, surprise=0.0))
        rows.append(dict(kind="act", episode_id=eid, tick=2, gym="reasoning_gym", action="3+4+5",
                         prediction=0.6, outcome="attempt 2: verifier score 0.20 (not accepted; partial credit)",
                         score=0.2, surprise=-0.4))
        rows.append(dict(kind="thought", episode_id=eid, tick=3, gym="reasoning_gym",
                         note="PREDICT: 0.9\nACT: 3*4+5\nNOTE: order matters", prompt="p",
                         win=True, had_note=True))
        rows.append(dict(kind="act", episode_id=eid, tick=3, gym="reasoning_gym", action="3*4+5",
                         prediction=0.9, outcome="attempt 3: verifier score 1.00 (accepted)",
                         score=1.0, surprise=0.1))
        rows.append(dict(kind="act", episode_id=eid, tick=4, gym="reasoning_gym", action="3*4+5+0",
                         prediction=0.9, outcome="attempt 4: verifier score 1.00 (accepted)",
                         score=1.0, surprise=0.1))
    rows.append(dict(kind="reflection", episode_id="reflection@0004", tick=1, at_episode=4,
                     note="I answered before reading the whole puzzle.", prompt="rp"))
    return rows


class RecordingThink:
    def __init__(self):
        self.prompts = []

    def __call__(self, p, **kw):
        self.prompts.append(p)
        if "PRINCIPLES" in p:
            tag = "puzzles" if "puzzles" in p else ("situations" if "situations" in p else "programs")
            return f"PRINCIPLE: when x, do y, because z [{tag}: a, b]"
        return "Briefing: x"


COMPILER_WORDS = re.compile(r"pass|program|optimi|compil|llvm", re.I)


def test_reasoning_gym_compile_is_target_blind():
    """Review 2026-09-10 (fatal): the compile templates were compiler-only, so
    a reasoning_gym life wrote 'Program rg/...', 'which passes improve it?'
    and 'optimizing these programs' into its corpus and THINK prompts."""
    g = _rg_gym()
    vocab = g.compile_vocab()
    m = RecordingThink()
    out = sc.compile_sleep(m, _rg_rows(), tempfile.mkdtemp(), [], vocab=vocab,
                           vocab_by_gym={"reasoning_gym": vocab})
    assert out["corpus"] and out["n_principles"] == 1
    for c in out["corpus"]:
        assert not COMPILER_WORDS.search(c), c
    for p in m.prompts:
        assert not COMPILER_WORDS.search(p), p
    assert any(c.startswith("Puzzle rg/countdown/1000001. Q: which attempt scores best?") for c in out["corpus"])
    assert any(c.startswith("Puzzle rg/countdown/1000001. My thinking:") for c in out["corpus"])
    assert any(c.startswith("Puzzle rg/countdown/1000001. Tried 3+4+5 -> attempt 2") for c in out["corpus"])
    assert any(c.startswith("[episodic] On rg/countdown/1000001 I predicted") for c in out["corpus"])
    assert any(c.startswith("Puzzle rg/countdown/1000001: 3+4+5 scored 0.200; more efficient: 3*4+5 scored 1.000")
               for c in out["corpus"]), [c for c in out["corpus"] if "efficient" in c]
    assert any(c.startswith("[reflection]") for c in out["corpus"])
    assert any("[puzzles:" in p for p in m.prompts) and any("solving these puzzles" in p for p in m.prompts)
    # the same rows through the default (compiler) vocabulary reproduce the historical strings
    m2 = RecordingThink()
    out2 = sc.compile_sleep(m2, [dict(r, gym=None) for r in _rg_rows()], tempfile.mkdtemp(), [])
    assert any(c.startswith("Program rg/countdown/1000001. Q: which passes improve it?") for c in out2["corpus"])
    assert any("[programs:" in p and "programs you optimized" in p for p in m2.prompts)
    # rows without a gym field under a reasoning_gym default are puzzles too
    out3 = sc.compile_sleep(RecordingThink(), [dict(r, gym=None) for r in _rg_rows()],
                            tempfile.mkdtemp(), [], vocab=vocab)
    assert not any(COMPILER_WORDS.search(c) for c in out3["corpus"])
    # every gym publishes a complete vocabulary; the protocol has the method
    from organism_v6 import gym_backend as gb
    assert set(vocab) == set(sc.COMPILER_VOCAB) == set(sc.NEUTRAL_VOCAB)
    assert not any(COMPILER_WORDS.search(v) for v in vocab.values())
    assert callable(getattr(gb.CompilerGymGym, "compile_vocab", None))
    assert not any(COMPILER_WORDS.search(v) for v in sc.NEUTRAL_VOCAB.values())


def test_pooled_compile_groups_wins_and_pathways_by_clone():
    """Review 2026-09-10 (major): two clones playing the same program id had
    their thoughts and wins mixed into one fabricated pathway exemplar."""
    rows = [
        dict(kind="thought", episode_id="cbench-v1/crc32", tick=1, note="CLONE-B THOUGHT: hmm",
             prompt="p", clone_id=1, gym="compiler"),
        dict(kind="act", episode_id="cbench-v1/crc32", tick=1, action="-licm",
             outcome="instructions 100 -> 99", score=0.01, prediction=0.1, surprise=-0.09,
             clone_id=1, gym="compiler"),
        dict(kind="thought", episode_id="cbench-v1/crc32", tick=1, note="CLONE-A THOUGHT: recipe first",
             prompt="p", clone_id=0, gym="compiler"),
        dict(kind="act", episode_id="cbench-v1/crc32", tick=1, action="-mem2reg,-sroa",
             outcome="instructions 100 -> 70", score=0.30, prediction=0.3, surprise=0.0,
             clone_id=0, gym="compiler"),
    ]
    out = sc.compile_sleep(RecordingThink(), rows, tempfile.mkdtemp(), [])
    paths = [c for c in out["corpus"] if "My thinking" in c]
    assert len(paths) == 2, paths
    a = next(c for c in paths if "-mem2reg" in c)
    b = next(c for c in paths if "-licm" in c)
    assert "CLONE-A THOUGHT" in a and "CLONE-B THOUGHT" not in a, a
    assert "CLONE-B THOUGHT" in b and "CLONE-A THOUGHT" not in b, b
    # the same rows WITHOUT clone ids behave as one life did (by episode id):
    # the later, higher act is a win; -licm's thought precedes it in the pathway
    plain = [dict((k, v) for k, v in r.items() if k != "clone_id") for r in rows]
    out2 = sc.compile_sleep(RecordingThink(), plain, tempfile.mkdtemp(), [])
    paths2 = [c for c in out2["corpus"] if "My thinking" in c]
    assert len(paths2) == 2 and any("CLONE-B THOUGHT" in c and "CLONE-A THOUGHT" in c for c in paths2)


def test_split_hygiene_is_family_level_for_the_reasoning_gym():
    """Review 2026-09-10: the per-sleep assertion checked only the fixed ids;
    an exam-family item with another seed passed. Now split_of decides."""
    from organism_v6 import run_life_v2 as rl
    g = _rg_gym()
    for eid, sp in (("rg/zebra_puzzles/1500000", "exam"), ("rg/n_queens/1234567", "gate"),
                    ("rg/rush_hour/3000099", "exam"), ("rg/countdown/1900001", "canary")):
        assert g.split_of(eid) == sp
        try:
            rl.assert_split_hygiene(g, [dict(kind="act", episode_id=eid, tick=1, score=1.0)])
        except RuntimeError as e:
            assert "split hygiene" in str(e) and sp in str(e), str(e)
        else:
            raise AssertionError(f"{eid} ({sp} family) passed the hygiene assertion")
    # a thought row alone is enough to trip it
    try:
        rl.assert_split_hygiene(g, [dict(kind="thought", episode_id="rg/acre/1000005", tick=1, note="n")])
    except RuntimeError:
        pass
    else:
        raise AssertionError("exam-family thought row passed")
    # train items, reflection rows and foreign ids pass
    rl.assert_split_hygiene(g, [dict(kind="act", episode_id="rg/countdown/1000005", tick=1, score=0.5),
                                dict(kind="reflection", episode_id="reflection@0008", tick=1, note="x"),
                                dict(kind="act", episode_id="not-an-rg-id", tick=1, score=0.0)])
    # the compiler gym keeps the fixed-id rule (no split_of)
    with gh.fake_world(gh.Transcript()):
        from organism_v6.gym_backend import make_gym
        cg = make_gym("compiler", gate_panel=list(gh.GATE_PANEL))
        rl.assert_split_hygiene(cg, [dict(kind="act", episode_id="cbench-v1/crc32", tick=1)])
        for bad in ("cbench-v1/susan", "benchmark://npb-v0/10", "npb-v0/10"):
            try:
                rl.assert_split_hygiene(cg, [dict(kind="act", episode_id=bad, tick=1)])
            except RuntimeError:
                pass
            else:
                raise AssertionError(f"{bad} passed")


def test_gym_leak_terms_reach_the_parent_scan():
    """Review 2026-09-10 (major): Gym.leak_terms()/answer_terms() were inert.
    They now reach leak_scan as exact terms in both parent paths."""
    from organism_v6 import run_life_v2 as rl
    from organism_v6.parent_backend import leak_scan
    g = _rg_gym()
    terms = rl.parent_leak_terms(g, [], 32)
    assert "zebra_puzzles" in terms and "Tower of Hanoi" in terms and "n_queens" in terms
    assert not any(t in terms for t in g.train_families)
    for text in ("Try the zebra_puzzles approach.", "Think of it as a Tower of Hanoi.",
                 "like tower   of\nhanoi, move one at a time"):
        hits = leak_scan(text, exact_terms=terms)
        assert hits and all(h.startswith("term:") for h in hits), (text, hits)
    # labels are exact substrings only: their single words do not fire
    assert leak_scan("Finish the completion of this logic puzzle in an hour.", exact_terms=terms) == []
    assert leak_scan("abc", exact_terms=["ab", "xyz"]) == [], "terms under 4 chars are ignored"
    # validate_output: an exact term falls back, the quote-back exemption does not apply
    bad = dict(final=dict(brief="Treat it like the Tower of Hanoi.", frontier_estimate=dict(text="x", confidence=0.1),
                          curriculum_move=dict(move="repeat", reason="")))
    out = ap.validate_output(bad, samples="Tower of Hanoi", exact_terms=terms)
    assert out["fallback"] is True and out["fallback_reason"] == "leak_scan"
    assert ap.validate_output(bad, samples="")["fallback"] is False, "default: today's scan"
    # the compiler gym: held-out program ids
    with gh.fake_world(gh.Transcript()):
        from organism_v6.gym_backend import make_gym
        cg = make_gym("compiler", gate_panel=list(gh.GATE_PANEL))
        ct = rl.parent_leak_terms(cg, [], 32)
        assert "cbench-v1/susan" in ct and "npb-v0/10" in ct
        assert leak_scan("Look at cbench-v1/susan again.", exact_terms=ct)
    # the baseline parent_brief path
    root = tempfile.mkdtemp()
    life, rows = _life_with_reflections(root)
    replies = iter(["Remember the Tower of Hanoi: move one thing at a time and predict it.",
                    "Name one feature of THIS puzzle before you act; say what you expect."])

    def fake_chat(self, prompt, max_tokens=220, temperature=0.4):
        return next(replies)

    saved = parent_backend.ServerParent._chat
    parent_backend.ServerParent._chat = fake_chat
    try:
        meta = pb.parent_brief(life, rows, os.path.join(life, "sleep_0032"),
                               "http://127.0.0.1:1/v1", "m", 32, extra_leak_terms=terms)
        assert meta["intervened"] and meta["text"] == FALLBACK + REHEARSAL_TAIL
        assert any(h.startswith("term:tower of hanoi") for h in meta["hits"]), meta["hits"]
        s64 = os.path.join(life, "sleep_0064")
        os.makedirs(s64, exist_ok=True)
        meta2 = pb.parent_brief(life, rows, s64, "http://127.0.0.1:1/v1", "m", 32,
                                extra_leak_terms=terms)
        assert meta2["text"].startswith("Name one feature") and meta2["hits"] == []
    finally:
        parent_backend.ServerParent._chat = saved
    # the agentic path threads the terms through the room context
    soc = os.path.join(root, "society")
    leaking = json.dumps(dict(final=dict(
        brief="Treat every grid like the Tower of Hanoi: smallest piece first.",
        frontier_estimate=dict(text="x", confidence=0.4),
        curriculum_move=dict(move="repeat", reason="same lesson"), evidence=["metrics()"])))
    cfg = ap.ProviderConfig("mock", role="A", model="mock-A")
    room = ap.ParentRoom([cfg], clients={"A": ap.MockChatClient(script=[leaking])})
    s96 = os.path.join(life, "sleep_0096")
    os.makedirs(s96, exist_ok=True)
    meta3 = ap.parent_brief_agentic(life, rows, s96, None, "mock", 32, room=room,
                                    society_dir=soc, extra_leak_terms=terms)
    assert meta3["fallback"] is True and any(h.startswith("term:") for h in meta3["hits"])


def test_target_blind_ledger_scan():
    """Design 3.6 seal rule at every sleep (review: not built before): the
    child's stored prompts and notes of a childhood life carry zero
    deployment-gym vocabulary, or the sleep is refused."""
    from organism_v6 import run_life_v2 as rl
    clean_rows = [dict(kind="thought", episode_id="rg/countdown/1000001", tick=1,
                       note="PREDICT: 0.5\nACT: 3+4\nNOTE: passes of time; my program of attack",
                       prompt="=== YOU ===\npuzzle workshop")]
    assert rl.leak_scan_ledger(clean_rows)["hits"] == {}, "generic words are not hits"
    dirty = clean_rows + [dict(kind="note", episode_id="rg/countdown/1000001", tick=2,
                               note="maybe -mem2reg style thinking; LLVM IR counts", prompt="")]
    res = rl.leak_scan_ledger(dirty)
    assert res["n_hit_rows"] == 1 and set(res["hits"]) == {"-mem2reg", "llvm ir"}, res
    assert rl.leak_scan_ledger(dirty, since=1)["n_hit_rows"] == 1
    assert rl.leak_scan_ledger(dirty, since=2)["n_hit_rows"] == 0
    # prompts count too (a harness bug would show up there)
    p_dirty = [dict(kind="thought", episode_id="x", tick=1, note="ok",
                    prompt="GOAL: Optimize program cbench-v1/crc32 with optimization passes")]
    assert set(rl.leak_scan_ledger(p_dirty)["hits"]) == {"cbench-v1", "optimization passes"}

    class TraitGym:
        def exposure_domain(self):
            return "reasoning_gym:countdown"

    class DepGym:
        def exposure_domain(self):
            return "compiler_gym:llvm-v0:IrInstructionCount"

    life = tempfile.mkdtemp()
    logs = []
    rec = rl.target_blind_check(TraitGym(), clean_rows, life, 1, logs.append)
    assert rec["clean"] and rec["enforced"] and rec["scanned_rows"] == 1
    assert rl.target_blind_check(TraitGym(), clean_rows, life, 1, logs.append) == rec, "idempotent per round"
    try:
        rl.target_blind_check(TraitGym(), dirty, life, 2, logs.append)
    except RuntimeError as e:
        assert "target-blindness violated" in str(e) and "-mem2reg" in str(e)
    else:
        raise AssertionError("dirty ledger accepted")
    recs = [json.loads(l) for l in open(os.path.join(life, "leak_scan.jsonl"))]
    assert [r["round"] for r in recs] == [1, 2] and recs[1]["clean"] is False
    assert recs[1]["scanned_rows"] == 1, "a failing scan does not advance the cursor"
    # recorded, not enforced (development groups)
    rec3 = rl.target_blind_check(TraitGym(), dirty, life, 3, logs.append, enforce=False)
    assert rec3["clean"] is False and rec3["enforced"] is False
    assert any("not enforced" in m for m in logs)
    # the deployment gym: not applicable, nothing written
    life2 = tempfile.mkdtemp()
    r = rl.target_blind_check(DepGym(), dirty, life2, 1, logs.append)
    assert r["applicable"] is False and not os.path.exists(os.path.join(life2, "leak_scan.jsonl"))


def test_reflect_every_not_a_multiple_of_wake_batch_fires_on_crossing():
    """Review 2026-09-10 (minor): N=6 with wake batches of 4 used to reflect
    at the LCM (12) only; now at the end of the batch crossing each multiple."""
    tr = gh.run_scenario("armA", extra_argv=["--arm", "A", "--reflect-every", "6",
                                              "--reflect-ticks", "1"])
    rows = [json.loads(l) for l in tr["files"]["ledger.jsonl"].splitlines() if l.strip()]
    ats = sorted({r["at_episode"] for r in rows if r["kind"] == "reflection"})
    assert ats == [8, 12], ats           # crossings of 6 and 12 within 16 episodes
    assert "reflect_0008.json" in tr["files"] and "reflect_0012.json" in tr["files"]
    assert "reflect_0016.json" not in tr["files"]


def test_run_life_v2_reflection_flag_end_to_end():
    tr = gh.run_scenario("armA", extra_argv=["--arm", "A", "--reflect-every", "4",
                                              "--reflect-ticks", "2"])
    files = tr["files"]
    rows = [json.loads(l) for l in files["ledger.jsonl"].splitlines() if l.strip()]
    refl = [r for r in rows if r["kind"] == "reflection"]
    assert [r["at_episode"] for r in refl] == [4, 4, 8, 8, 12, 12, 16, 16]
    assert all(r["tick"] in (1, 2) for r in refl)
    for at in (4, 8, 12, 16):
        m = json.loads(files[f"reflect_{at:04d}.json"])
        assert m["n_chunks"] == 2 and m["rows_after"] == m["rows_before"] + 2
    # the reflection prompt: no parent text, a summary of the child's own rows
    rp = [e for e in tr["events"] if e["kind"] == "batch"
          and "PRIVATE REFLECTION TIME" in e["prompt"]]
    assert len(rp) == 8
    assert all("YOUR PARENT" not in e["prompt"] and "BRIEFING" not in e["prompt"] for e in rp)
    assert "situation(s)" in rp[0]["prompt"] and "attempt(s)" in rp[0]["prompt"]
    # the sleep corpus carries them; the reflection of episode 8 precedes sleep 8
    corpus = json.loads(files["sleep_0008/corpus.json"])["corpus"]
    assert any(c.startswith("[reflection] My private thinking after episode 8") for c in corpus)
    corpus16 = json.loads(files["sleep_0016/corpus.json"])["corpus"]
    assert sum(c.startswith("[reflection]") for c in corpus16) >= 2
    # every probe file / wake file otherwise as in the golden scenario shape
    assert "probe_ep0016.json" in files and "LIFE_DONE" in files


if __name__ == "__main__":
    import traceback
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for n, f in tests:
        try:
            f()
            print("PASS", n)
        except Exception:  # noqa: BLE001
            failed += 1
            print("FAIL", n)
            traceback.print_exc()
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
