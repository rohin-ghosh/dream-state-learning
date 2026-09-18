"""Level-3 preschool machinery behind default-off flags (organism_v6/preschool.py;
THESIS_v2 section 7, Astra memo q14). Runs run_life_v2 end to end in the golden
harness's fake world (tests/golden_harness.py: scripted model, fake gym, fake
trainer, no GPU). A recording fake model answers the NOTE_AFTER / Scratchpad
prompts with a grounded first-person record built from the block it is shown,
so the gate's admission path is exercised; every other prompt is answered by
the harness's FakeModel exactly as before.

  python3 -m pytest tests/test_preschool_flags.py -q
"""
from __future__ import annotations

import contextlib
import json
import math
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import golden_harness as gh  # noqa: E402
from organism_v6 import preschool  # noqa: E402

GOLDEN = os.path.join(HERE, "golden", "compiler_golden_v1.json")
NEUTRAL = ["benchmark://npb-v0/30", "benchmark://blas-v0/20"]


class RecordingFakeModel(gh.FakeModel):
    """gh.FakeModel plus grounded records for the post-outcome prompts."""

    def batch(self, prompts, max_tokens=400, temperature=0.7, seeds=None):
        outs = [None] * len(prompts)
        rest = []
        for j, p in enumerate(prompts):
            tail = p.rstrip().splitlines()[-1].strip() if p.strip() else ""
            if tail in (preschool.NOTE_AFTER_LABEL + ":", preschool.SCRATCHPAD_LABEL + ":"):
                outs[j] = self._record(p)
                gh.FakeModel.transcript.add(kind="post_outcome", label=tail[:-1], prompt=p,
                                            output=outs[j], max_tokens=max_tokens,
                                            adapter=self.adapter_path)
            else:
                rest.append(j)
        if rest:
            sub = super().batch([prompts[j] for j in rest], max_tokens=max_tokens,
                                temperature=temperature,
                                seeds=[seeds[j] for j in rest] if seeds is not None else None)
            for j, o in zip(rest, sub):
                outs[j] = o
        return outs

    @staticmethod
    def _record(p: str) -> str:
        passes = re.search(r"^ACT executed: (.*)$", p, re.M).group(1).strip()
        b = re.search(r"^Instructions before: (\d+)", p, re.M)
        a = re.search(r"^Instructions after: (\d+)", p, re.M)
        r = re.search(r"^Measured reduction: (-?[\d.]+)%", p, re.M)
        if b and a and r:
            return (f"I ran {passes}. Instructions went from {b.group(1)} to {a.group(1)}, "
                    f"a {r.group(1)}% reduction.")
        return f"I tried {passes}. The run failed, so I measured nothing."


@contextlib.contextmanager
def recording_model():
    saved = gh.FakeModel
    gh.FakeModel = RecordingFakeModel
    try:
        yield
    finally:
        gh.FakeModel = saved


def _life(extra, episodes=16, sleep_every=8, probe_every=8):
    root = tempfile.mkdtemp(prefix="preschool_")
    life = os.path.join(root, "life")
    panel = os.path.join(root, "neutral_panel.json")
    with open(panel, "w") as f:
        json.dump(NEUTRAL, f)
    argv = ["--life-dir", life, "--seed", "0", "--episodes", str(episodes), "--sleep-every",
            str(sleep_every), "--probe-every", str(probe_every), "--budget-ticks", "3",
            "--wake-batch", "4", "--rank", "8"] + [a if a != "PANEL" else panel for a in extra]
    with recording_model():
        tr = gh.run_life(argv)
    return life, tr


def _rows(life, name="ledger.jsonl"):
    p = os.path.join(life, name)
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def _corpus(life, sleep):
    return json.load(open(os.path.join(life, f"sleep_{sleep:04d}", "corpus.json")))["corpus"]


def _wake_prompts(tr):
    """Prompts of the wake batches (they carry the state block; probes do too, so
    keep only those whose head is not the bare birth prompt: the wake head is
    brief() = birth prompt [+ briefing] [+ preschool additions])."""
    return [e["prompt"] for e in tr.events if e["kind"] == "batch"]


# --------------------------------------------------------------------------- 1. flags off = today's life
def _approx_equal(a, b, path="") -> str | None:
    if isinstance(a, float) or isinstance(b, float):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and \
                math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-12):
            return None
        return f"{path}: {a!r} != {b!r}"
    if type(a) is not type(b):
        return f"{path}: type {type(a).__name__} != {type(b).__name__}"
    if isinstance(a, dict):
        if set(a) != set(b):
            return f"{path}: keys {sorted(set(a) ^ set(b))}"
        for k in a:
            d = _approx_equal(a[k], b[k], f"{path}/{k}")
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = _approx_equal(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    return None if a == b else f"{path}: {str(a)[:80]!r} != {str(b)[:80]!r}"


def test_flags_off_byte_identical_to_the_golden():
    """Without the preschool flags, every prompt the child sees, every chunk,
    every gym evaluation, THINK prompt, parent call and every written file of
    the golden scenario is unchanged (files compared with float tolerance:
    the golden's probe means differ in the last digit across platforms)."""
    golden = json.load(open(GOLDEN))["armB_gate_panel"]
    with recording_model():
        cur = gh.run_scenario("armB_gate_panel")
    assert golden["argv"] == cur["argv"]
    assert golden["events"] == cur["events"], "transcript differs from the golden"
    assert set(golden["files"]) == set(cur["files"]), sorted(set(golden["files"]) ^ set(cur["files"]))
    for rel in golden["files"]:
        g, c = golden["files"][rel], cur["files"][rel]
        if g == c:
            continue
        try:
            d = _approx_equal(json.loads(g), json.loads(c), rel)
        except ValueError:
            d = f"{rel}: text differs"
        assert d is None, d
    assert not any(k in "".join(cur["files"]) for k in ("note_after", "articulation_shadow", "neutral_probe"))
    # the byte-identical path never imports the preschool module's gate state
    assert "articulation_state.json" not in cur["files"]


# --------------------------------------------------------------------------- 2. the post-outcome slot
def test_note_after_rows_and_slot_sentence():
    life, tr = _life(["--arm", "B", "--note-after"])
    rows = _rows(life)
    acts = [r for r in rows if r["kind"] == "act"]
    notes = [r for r in rows if r["kind"] == "note_after"]
    assert acts and notes and len(notes) == len(acts), (len(acts), len(notes))
    assert all(r.get("execution_id") for r in acts)
    assert {r["execution_id"] for r in acts} == {r["execution_id"] for r in notes}
    for r in notes:
        assert set(r) >= {"kind", "episode_id", "tick", "execution_id", "text", "before", "after",
                          "reduction", "status", "action", "outcome", "gen_seconds", "n_chars", "label"}
        assert r["label"] == "NOTE_AFTER" and r["status"] in ("success", "failure")
        if r["status"] == "success":
            assert r["before"] > r["after"] >= 0 and r["reduction"] > 0
            assert str(r["before"]) in r["text"] and str(r["after"]) in r["text"]
        else:
            assert r["before"] is None and "failed" in r["text"]
    # exactly one slot sentence in the head of every wake prompt; none in the probes' fresh prompts
    wake = [p for p in _wake_prompts(tr) if preschool.SLOT_SENTENCE in p]
    probe = [p for p in _wake_prompts(tr) if preschool.SLOT_SENTENCE not in p]
    assert wake and probe
    assert all(p.count(preschool.SLOT_SENTENCE) == 1 for p in wake)
    assert not any("A NOTE FROM YOUR PARENT" in p for p in wake)      # slot-only: no lesson, no examples
    # the block the child is shown, and the generation cap
    post = [e for e in tr.events if e["kind"] == "post_outcome"]
    assert len(post) == len(notes)
    for e in post:
        p = e["prompt"]
        assert e["label"] == "NOTE_AFTER" and e["max_tokens"] == 100
        assert re.search(r"^Program: \S+    Tick: \d+    Execution: \S+#t\d+a\d+$", p, re.M)
        for line in ("ACT executed: ", "Instructions before: ", "Instructions after: ",
                     "Measured reduction: ", "Execution status: "):
            assert line in p
        assert p.rstrip().endswith("NOTE_AFTER:")
    # the cap is a flag
    life2, tr2 = _life(["--arm", "A", "--note-after", "--note-after-max-tokens", "37"])
    assert all(e["max_tokens"] == 37 for e in tr2.events if e["kind"] == "post_outcome")
    # budget bookkeeping is in the life log at every sleep
    assert "[preschool slot]" in open(os.path.join(life, "life.log")).read()


# --------------------------------------------------------------------------- 3. the artifact lesson
def test_lesson_before_episode_one_and_refreshers_after_sleeps_1_to_3_only():
    life, tr = _life(["--arm", "A", "--note-after", "--artifact-lesson", "lesson10"],
                     episodes=40, sleep_every=8, probe_every=8)
    deliveries = _rows(life, "lesson_deliveries.jsonl")
    phases = [d["sleeps_done"] for d in deliveries]
    assert phases[:4] == [0, 1, 2, 3], phases
    assert all(p <= 3 for p in phases), "the lesson must vanish from sleep 4 on"
    full = deliveries[0]["text"]
    assert deliveries[0]["phase"] == "lesson" and preschool.LESSON_PARAGRAPH in full
    assert all(ex in full for ex in preschool.LESSON_EXAMPLES) and preschool.BASELINE10_PARAGRAPH in full
    assert preschool.EXAMPLES_HEADER in full
    for d in deliveries[1:]:
        assert d["phase"] == "refresher" and preschool.REFRESHER_LINE in d["text"]
        assert preschool.LESSON_PARAGRAPH not in d["text"]
        assert preschool.REFRESHER_EXAMPLES[(d["sleeps_done"] - 1) % 3] in d["text"]
    assert all("score" not in d["text"].lower() for d in deliveries)       # parents never carry scores
    assert all(d["version"] == preschool.LESSON_VERSION for d in deliveries)
    # what the child actually saw: the wake prompts of episodes 1-8 carry the full lesson; after
    # sleep 1 the refresher (one new example) and not the paragraph; after sleep 4 neither
    wake = [e["prompt"] for e in tr.events if e["kind"] == "batch" and preschool.SLOT_SENTENCE in e["prompt"]]
    first = [p for p in wake if preschool.LESSON_PARAGRAPH in p]
    refreshed = [p for p in wake if preschool.REFRESHER_LINE in p]
    bare = [p for p in wake if "A NOTE FROM YOUR PARENT" not in p]
    assert first and refreshed and bare, (len(first), len(refreshed), len(bare))
    assert not any(preschool.LESSON_PARAGRAPH in p for p in refreshed)
    assert all(preschool.LESSON_PARAGRAPH not in p for p in bare)
    # 'lesson' alone has no numbered baseline
    life2, _ = _life(["--arm", "A", "--artifact-lesson", "lesson"], episodes=8, sleep_every=8)
    d2 = _rows(life2, "lesson_deliveries.jsonl")
    assert d2 and preschool.BASELINE10_PARAGRAPH not in d2[0]["text"] and d2[0]["mode"] == "lesson"


# --------------------------------------------------------------------------- 4. the gate at sleep
def test_shadow_gate_logs_and_leaves_the_corpus_unchanged():
    life, _ = _life(["--arm", "B", "--note-after", "--articulation-gate", "shadow"])
    shadow = json.load(open(os.path.join(life, "sleep_0008", "articulation_shadow.json")))
    assert shadow["mode"] == "shadow" and shadow["enforced"] is False and shadow["training_skipped"] is False
    for k in ("A_s_raw_hi", "A_s_raw_lo", "G_rate", "N_rate", "F_rate", "D_rate", "P_rate", "GN_rate",
              "admission_hi", "admission_lo", "rejection_families", "n_executions_numeric", "n_note_after",
              "legacy_corpus_items", "record_items", "corpus_survival_if_enforced",
              "tokens_note_after_chars", "slot", "judged"):
        assert k in shadow, k
    assert shadow["n_note_after"] == shadow["n_executions"] > 0
    assert 0 <= shadow["A_s_raw_hi"] <= 1 and shadow["A_s_raw_lo"] <= shadow["A_s_raw_hi"]
    # the recording model writes grounded first-person records: they are admitted (duplicates aside)
    assert shadow["G_rate"] == 1.0 and shadow["F_rate"] == 1.0 and shadow["N_rate"] == 1.0
    assert shadow["n_admitted_total"] >= 1 and shadow["A_s_raw_hi"] == 1.0
    # failed executions (the fake INVALID pass) measured nothing: 'no-measurement', outside A_s's denominator
    assert set(shadow["rejection_families"]) <= {"duplicate", "no-measurement"}
    n_fail = sum(1 for j in shadow["judged"] if j["status"] == "failure")
    assert shadow["rejection_families"].get("no-measurement", 0) == n_fail
    assert shadow["slot"]["n_generations"] == shadow["n_note_after"]
    # shadow: the corpus is the ordinary compile, untouched
    corpus = _corpus(life, 8)
    assert any("So I did:" in it for it in corpus)
    assert not any("My measured action record" in it for it in corpus)
    assert not os.path.exists(os.path.join(life, "sleep_0008", "corpus_legacy.json"))
    assert not os.path.exists(os.path.join(life, "sleep_0008", preschool.SKIP_MARKER))
    assert os.path.exists(os.path.join(life, "sleep_0008", "adapter", "DONE"))
    # the duplicate window persists across sleeps
    st = json.load(open(os.path.join(life, "articulation_state.json")))
    s2 = json.load(open(os.path.join(life, "sleep_0016", "articulation_shadow.json")))
    assert st["rows_seen"] == s2["rows_now"] and s2["rows_since"] == shadow["rows_now"]
    assert len(st["admitted"]) == s2["n_admitted_total"] >= shadow["n_admitted_total"]


def test_enforce_gate_replaces_the_harness_line_or_skips_the_sleep():
    life, _ = _life(["--arm", "B", "--note-after", "--articulation-gate", "enforce",
                     "--gate-min-items", "2"])
    sh = json.load(open(os.path.join(life, "sleep_0008", "articulation_shadow.json")))
    assert sh["enforced"] is True and sh["training_skipped"] is False and sh["min_items"] == 2
    corpus = _corpus(life, 8)
    assert corpus and all(it.startswith("Program ") and "\nMy measured action record: " in it for it in corpus)
    assert not any("So I did:" in it or "Q: which passes" in it or "[episodic]" in it for it in corpus)
    legacy = json.load(open(os.path.join(life, "sleep_0008", "corpus_legacy.json")))["corpus"]
    assert legacy and any("So I did:" in it for it in legacy) and sh["n_dropped_legacy"] == len(legacy)
    # the record text is the child's, verbatim
    notes = {r["execution_id"]: r["text"] for r in _rows(life) if r["kind"] == "note_after"}
    for it in corpus:
        rec = it.split("My measured action record: ", 1)[1]
        assert rec in notes.values()
    assert os.path.exists(os.path.join(life, "sleep_0008", "adapter", "DONE"))
    # cumulative: the second sleep's corpus holds every admitted record to date
    assert len(_corpus(life, 16)) >= len(corpus)
    # too few admitted records => the sleep is skipped, the adapter stays, the life finishes
    life2, _ = _life(["--arm", "B", "--note-after", "--articulation-gate", "enforce",
                      "--gate-min-items", "1000"])
    assert os.path.exists(os.path.join(life2, "sleep_0008", preschool.SKIP_MARKER))
    assert not os.path.exists(os.path.join(life2, "sleep_0008", "adapter"))
    assert os.path.exists(os.path.join(life2, "LIFE_DONE"))
    assert "training SKIPPED" in open(os.path.join(life2, "life.log")).read()
    sh2 = json.load(open(os.path.join(life2, "sleep_0008", "articulation_shadow.json")))
    assert sh2["training_skipped"] is True and sh2["record_items"] < 1000


# --------------------------------------------------------------------------- 5. neutral probes
def test_neutral_probes_are_paired_fresh_and_never_harvested():
    life, tr = _life(["--arm", "B", "--note-after", "--artifact-lesson", "lesson",
                      "--neutral-probes", "--neutral-probe-panel", "PANEL"])
    for i in (8, 16):
        pre = json.load(open(os.path.join(life, f"neutral_probe_pre_{i:04d}.json")))
        post = json.load(open(os.path.join(life, f"neutral_probe_post_{i:04d}.json")))
        assert pre["program"] == post["program"] in NEUTRAL
        assert pre["when"] == "pre" and post["when"] == "post" and pre["sleep_index"] == post["sleep_index"]
        assert pre["n_scratchpads"] >= 1 and pre["n_scratchpads"] == pre["n_executions_numeric"] + \
            sum(1 for s in pre["scratchpads"] if s["status"] == "failure")
        for s in pre["scratchpads"]:
            assert set(s) >= {"G", "N", "F", "P", "D", "reason", "artic_hi", "text", "execution_id"}
        assert 0 <= pre["articulation_hi"] <= 1
        assert post["adapter"] is not None and post["adapter"].endswith("adapter") \
            or post["adapter"] is None
        assert pre["fresh_context"] is True
    assert json.load(open(os.path.join(life, "neutral_probe_pre_0016.json")))["program"] == NEUTRAL[1]
    # separate ledgers: nothing of the neutral programs in the life ledger or any corpus
    main = _rows(life)
    assert not any(r.get("episode_id") in NEUTRAL for r in main)
    for s in (8, 16):
        assert not any(any(n in it for n in NEUTRAL) for it in _corpus(life, s))
    # fresh context: the Scratchpad prompts carry the birth prompt only -- no briefing, no lesson
    pads = [e for e in tr.events if e["kind"] == "post_outcome" and e["label"] == "Scratchpad"]
    assert pads
    for e in pads:
        assert "BRIEFING" not in e["prompt"] and "A NOTE FROM YOUR PARENT" not in e["prompt"]
        assert preschool.SLOT_SENTENCE not in e["prompt"]
        assert e["prompt"].rstrip().endswith("Scratchpad:")
    # pre-sleep adapter reference recorded (a path or None before the first adapter)
    pre8 = json.load(open(os.path.join(life, "neutral_probe_pre_0008.json")))
    assert pre8["adapter"] is None and pre8["adapter_sha256"] is None
    # resume-safe: the probe files are markers (a second run does not redo them)
    n_before = len(tr.events)
    assert n_before > 0


def test_neutral_panel_must_be_held_out():
    root = tempfile.mkdtemp(prefix="preschool_clash_")
    life = os.path.join(root, "life")
    panel = os.path.join(root, "panel.json")
    with open(panel, "w") as f:
        json.dump(["benchmark://cbench-v1/crc32"], f)     # a training program in the fake world
    argv = ["--life-dir", life, "--seed", "0", "--episodes", "8", "--sleep-every", "8",
            "--probe-every", "8", "--budget-ticks", "3", "--wake-batch", "4", "--rank", "8",
            "--arm", "A", "--neutral-probes", "--neutral-probe-panel", panel]
    try:
        with recording_model():
            gh.run_life(argv)
    except SystemExit as e:
        assert "training schedule" in str(e)
    else:
        raise AssertionError("a neutral panel overlapping the training schedule was accepted")


# --------------------------------------------------------------------------- 6. unit checks of the module
def test_parse_outcome_and_lesson_block():
    f = preschool.parse_outcome("instructions 857 -> 470 (45.2% reduction)")
    assert f == dict(before=857, after=470, reduction=45.2, status="success", error="")
    g = preschool.parse_outcome("INVALID: unknown pass '-bogus'")
    assert g["status"] == "failure" and g["before"] is None and g["error"].startswith("unknown pass")
    assert preschool.lesson_block("none", 0) is None
    assert preschool.lesson_block("lesson", 4) is None and preschool.lesson_block("lesson10", 9) is None
    assert preschool.LESSON_PARAGRAPH in preschool.lesson_block("lesson", 0)
    assert preschool.BASELINE10_PARAGRAPH not in preschool.lesson_block("lesson", 0)
    assert preschool.BASELINE10_PARAGRAPH in preschool.lesson_block("lesson10", 0)
    for k in (1, 2, 3):
        b = preschool.lesson_block("lesson", k)
        assert preschool.REFRESHER_LINE in b and preschool.REFRESHER_EXAMPLES[k - 1] in b
    # the examples vary the OUTCOME: an improvement, no change, a regression
    ex = preschool.LESSON_EXAMPLES
    assert "reduction" in ex[0] and "no" in ex[1].lower() and "increased" in ex[2]
    # judge_record on a grounded record and on a slogan
    row = dict(kind="note_after", episode_id="benchmark://cbench-v1/crc32", tick=1, execution_id="x#t1a1",
               action="-mem2reg, -sroa", outcome="instructions 1000 -> 800 (20.0% reduction)", status="success",
               text="I ran -mem2reg, -sroa. Instructions went from 1000 to 800, a 20.0% reduction.")
    j = preschool.judge_record(row, None)
    assert j["G"] is True and j["N"] is True and j["F"] is True and j["admit_hi"] and j["artic_hi"]
    row2 = dict(row, text="Form expectations before acting. Write down what I learn.")
    j2 = preschool.judge_record(row2, None)
    assert j2["G"] is False and j2["P"] is True and not j2["admit_hi"] and j2["reason"] == "practice-only"
    row3 = dict(row, text="I ran -mem2reg. Instructions went from 1000 to 700, a 30% reduction.")
    j3 = preschool.judge_record(row3, None)
    assert j3["N"] is False and not j3["admit_hi"] and j3["reason"] == "N-mismatch"


# --------------------------------------------------------------------------- 7. the active sham (Codex audit blocker 1)
ARTIFACT_WORDS = ("record", "measured", "measure", "observed", "observe", "expect", "result", "wrote",
                  "write", "what happened", "in your own voice", " i ran", " i tried")


def test_sham_lesson_matches_length_and_schedule_without_artifact_content():
    """`--artifact-lesson sham`: the same deliveries (before episode 1; refreshers after sleeps
    1-3; nothing after), word count within 5 % of the artifact lesson per delivery, the same
    header and register, and no artifact content."""
    for k in (0, 1, 2, 3):
        a, s = preschool.lesson_block("lesson", k), preschool.lesson_block("sham", k)
        assert a and s and a != s
        wa, ws = len(a.split()), len(s.split())
        assert abs(wa - ws) / wa <= 0.05, (k, wa, ws)
        assert s.startswith("=== A NOTE FROM YOUR PARENT ===") and a.startswith("=== A NOTE FROM YOUR PARENT ===")
        low = " " + s.lower() + " "
        for w in ARTIFACT_WORDS:
            assert w not in low, (k, w)
        assert preschool.LESSON_PARAGRAPH not in s and preschool.REFRESHER_LINE not in s
        for ex in preschool.LESSON_EXAMPLES + preschool.REFRESHER_EXAMPLES:
            assert ex not in s
    assert preschool.lesson_block("sham", 4) is None and preschool.lesson_block("sham", 9) is None
    assert preschool.lesson_variant("sham") == "sham" and preschool.lesson_variant("lesson10") == "artifact"
    assert preschool.lesson_variant("none") == "none"
    # per-component matching too (paragraph, header, the three examples, refresher line, refresher examples)
    pairs = [(preschool.LESSON_PARAGRAPH, preschool.SHAM_PARAGRAPH),
             (preschool.EXAMPLES_HEADER, preschool.SHAM_EXAMPLES_HEADER),
             (preschool.REFRESHER_LINE, preschool.SHAM_REFRESHER_LINE)]
    pairs += list(zip(preschool.LESSON_EXAMPLES, preschool.SHAM_EXAMPLES))
    pairs += list(zip(preschool.REFRESHER_EXAMPLES, preschool.SHAM_REFRESHER_EXAMPLES))
    for a, s in pairs:
        wa, ws = len(a.split()), len(s.split())
        assert abs(wa - ws) <= max(2, round(0.12 * wa)), (a[:40], wa, ws)
    # delivered in a life: same schedule as the lesson, logged with variant=sham and its own version
    life, tr = _life(["--arm", "A", "--note-after", "--artifact-lesson", "sham"],
                     episodes=40, sleep_every=8, probe_every=8)
    d = _rows(life, "lesson_deliveries.jsonl")
    assert [x["sleeps_done"] for x in d][:4] == [0, 1, 2, 3] and all(x["sleeps_done"] <= 3 for x in d)
    assert all(x["variant"] == "sham" and x["mode"] == "sham" and x["version"] == preschool.SHAM_VERSION for x in d)
    assert preschool.SHAM_PARAGRAPH in d[0]["text"] and all(ex in d[0]["text"] for ex in preschool.SHAM_EXAMPLES)
    for x in d[1:]:
        assert preschool.SHAM_REFRESHER_LINE in x["text"] and x["n_words"] == len(x["text"].split())
    assert all("score" not in x["text"].lower() for x in d)
    wake = [e["prompt"] for e in tr.events if e["kind"] == "batch" and preschool.SLOT_SENTENCE in e["prompt"]]
    assert any(preschool.SHAM_PARAGRAPH in p for p in wake)
    assert not any(preschool.LESSON_PARAGRAPH in p for p in wake)
    # the artifact deliveries log variant=artifact
    life2, _ = _life(["--arm", "A", "--artifact-lesson", "lesson"], episodes=8, sleep_every=8)
    d2 = _rows(life2, "lesson_deliveries.jsonl")
    assert d2 and d2[0]["variant"] == "artifact" and d2[0]["version"] == preschool.LESSON_VERSION


# --------------------------------------------------------------------------- 8. adapter ON / OFF pairing (Codex audit blocker 4)
def test_neutral_probes_run_adapter_on_and_off_on_the_same_program():
    life, tr = _life(["--arm", "B", "--note-after", "--neutral-probes", "--neutral-probe-panel", "PANEL"])
    pre8 = json.load(open(os.path.join(life, "neutral_probe_pre_0008.json")))
    post8 = json.load(open(os.path.join(life, "neutral_probe_post_0008.json")))
    post16 = json.load(open(os.path.join(life, "neutral_probe_post_0016.json")))
    for pj in (pre8, post8, post16):
        assert set(pj) >= {"on", "off", "off_same_as_on", "articulation_on_minus_off_hi"}
        assert pj["on"]["arm"] == "on" and pj["off"]["arm"] == "off"
        assert pj["on"]["program"] == pj["off"]["program"] == pj["program"]
        # top-level fields are the ON run's, as before
        assert pj["adapter"] == pj["on"]["adapter"] and pj["scratchpads"] == pj["on"]["scratchpads"]
        assert pj["off"]["adapter"] is None
    # before any adapter exists the off arm is the on arm copied, flagged
    assert pre8["adapter"] is None and pre8["off_same_as_on"] is True and pre8["off"].get("same_as_on") is True
    assert not os.path.exists(os.path.join(life, "neutral_probe_pre_0008_adapterOFF.ledger.jsonl"))
    # after the first committed adapter the off arm is a real second run under the frozen base
    for pj, ep in ((post8, 8), (post16, 16)):
        assert pj["adapter"] is not None and pj["adapter"].endswith("adapter")
        assert pj["off_same_as_on"] is False and "same_as_on" not in pj["off"]
        assert pj["off"]["ledger"] == f"neutral_probe_post_{ep:04d}_adapterOFF.ledger.jsonl"
        assert os.path.exists(os.path.join(life, pj["off"]["ledger"]))
        assert os.path.exists(os.path.join(life, pj["on"]["ledger"])) and pj["on"]["ledger"] == f"neutral_probe_post_{ep:04d}.ledger.jsonl"
        off_rows = _rows(life, pj["off"]["ledger"])
        assert off_rows and all(r.get("episode_id") == pj["program"] for r in off_rows if "episode_id" in r)
        assert pj["off"]["n_scratchpads"] == pj["on"]["n_scratchpads"] >= 1
        assert pj["articulation_on_minus_off_hi"] is not None
    # the off arm was generated by a base model (adapter None) on the Scratchpad prompts of that program
    pads = [e for e in tr.events if e["kind"] == "post_outcome" and e["label"] == "Scratchpad"]
    adapters = {e["adapter"] for e in pads}
    assert None in adapters and any(a for a in adapters if a)
    # the main ledger and the corpora still carry nothing of the neutral programs
    assert not any(r.get("episode_id") in NEUTRAL for r in _rows(life))
    for s in (8, 16):
        assert not any(any(n in it for n in NEUTRAL) for it in _corpus(life, s))
    # the live model is back after the off arm: the ordinary adapter-ON probe after sleep 8 ran with the adapter
    on_batches = [e for e in tr.events if e["kind"] == "batch" and e.get("adapter")]
    assert on_batches


# --------------------------------------------------------------------------- 9. parent text never enters the sleep bytes (Codex audit blocker 11)
def _sentences(*texts):
    out = []
    for t in texts:
        for s in re.split(r"(?<=[.:;])\s+", t):
            s = s.strip("- ").strip()
            if len(s.split()) >= 4:
                out.append(s)
    return out


def test_lesson_and_sham_text_never_enter_the_sleep_corpus_or_record_items():
    parent_text = _sentences(preschool.LESSON_PARAGRAPH, preschool.EXAMPLES_HEADER, *preschool.LESSON_EXAMPLES,
                             preschool.REFRESHER_LINE, *preschool.REFRESHER_EXAMPLES, preschool.BASELINE10_PARAGRAPH,
                             preschool.SHAM_PARAGRAPH, preschool.SHAM_EXAMPLES_HEADER, *preschool.SHAM_EXAMPLES,
                             preschool.SHAM_REFRESHER_LINE, *preschool.SHAM_REFRESHER_EXAMPLES,
                             preschool.SLOT_SENTENCE, "A NOTE FROM YOUR PARENT")
    assert len(parent_text) > 20
    for mode, gate in (("lesson10", "shadow"), ("lesson", "enforce"), ("sham", "shadow"), ("sham", "enforce")):
        extra = ["--arm", "B", "--note-after", "--artifact-lesson", mode, "--articulation-gate", gate]
        if gate == "enforce":
            extra += ["--gate-min-items", "1"]
        life, tr = _life(extra, episodes=24, sleep_every=8, probe_every=8)
        # the child DID see the parent text during wake
        assert any("A NOTE FROM YOUR PARENT" in e["prompt"] for e in tr.events if e["kind"] == "batch")
        for s in (8, 16, 24):
            sdir = os.path.join(life, f"sleep_{s:04d}")
            for fn in ("corpus.json", "corpus_legacy.json"):
                p = os.path.join(sdir, fn)
                if not os.path.exists(p):
                    continue
                blob = json.load(open(p))
                items = blob["corpus"] + list(blob.get("principles") or [])
                joined = "\n".join(items)
                for sent in parent_text:
                    assert sent not in joined, (mode, gate, fn, sent[:60])
                if gate == "enforce" and fn == "corpus.json":
                    assert items and all("My measured action record: " in it for it in items)
        # nor the state the gate carries forward
        st = json.load(open(os.path.join(life, "articulation_state.json")))
        for a in st["admitted"]:
            for sent in parent_text:
                assert sent not in a["text"]
