"""Level-3 "preschool for records" machinery (THESIS_v2 section 7; Astra memo q14,
2026-09-12). EVERYTHING here is reached only through run_life_v2 flags that
default OFF; a life launched without them is byte-identical to before
(tests/test_preschool_flags.py::test_flags_off_byte_identical against the
compiler golden).

Four pieces, in the order the loop meets them:

  1. PostOutcomeSlot  -- the post-outcome turn (--note-after). After every
     ACT whose outcome has been measured the child is shown Astra's block
     (program, tick, execution id, the passes actually executed, instruction
     count before / after, measured reduction, execution status) ending in
     "NOTE_AFTER:" and writes ONE short generation (--note-after-max-tokens).
     Ledger row kind="note_after" tied to the execution id; generation wall
     time and characters recorded per row so the extra turn can be budgeted.
     The same class, with label "Scratchpad", is the neutral field of the
     H1 probes (item 4). Slot-only mode adds exactly one sentence to the head
     of context: SLOT_SENTENCE. No example, no schema, no minimum, no retry.
  2. The artifact lesson (--artifact-lesson lesson|lesson10): the parent's
     paragraph that names the deliverable (a MEASURED ACTION RECORD) plus
     three explicitly synthetic examples whose OUTCOMES vary (improvement, no
     change, regression), delivered in the head of context before episode 1;
     a one-line refresher with ONE new example after sleeps 1, 2 and 3 (after
     the post-sleep probe); nothing from sleep 4 on. lesson10 appends the
     numbered-baseline paragraph. Content is fixed across lives
     (LESSON_VERSION); it never contains a score. Deliveries are logged to
     <life>/lesson_deliveries.jsonl.
  3. The articulation gate at sleep (--articulation-gate shadow|enforce):
     every new note_after row is judged with the SAME functions as the
     retrospective audit (research_notes/analysis/articulation_gate_audit.py,
     imported by path: G grounding, N numbers, F first-person record, D
     duplicate-in-64, P practice-only), against the execution's own measured
     facts (strict: not the episode's other visits). Per sleep the counts of
     Astra's section 3 go to <life>/sleep_XXXX/articulation_shadow.json.
     shadow: the corpus is untouched. enforce: the corpus becomes the
     admitted records to date, each as
         Program <id>.\\nMy measured action record: <verbatim NOTE_AFTER>
     (the harness "So I did:" line and every non-admitted legacy item are
     dropped; the compiled legacy corpus is kept beside it as
     corpus_legacy.json); fewer than --gate-min-items admitted items => the
     sleep's training is SKIPPED (marker SLEEP_SKIPPED_INSUFFICIENT_RECORDS)
     and the current adapter stays. A note is never rewritten.
  4. Neutral probes (--neutral-probes): one probe episode immediately before
     and one immediately after each sleep, on the SAME held-out program
     (pair k for sleep k, from --neutral-probe-panel or NEUTRAL_PANEL_DEFAULT),
     fresh context (the birth prompt only: no briefing, no lesson, no
     refresher), ordinary instructions, measurements visible, the optional
     post-result field "Scratchpad:"; a separate ledger file, so nothing of it
     is harvested at sleep or seen by a parent. Results (raw texts and their
     articulation scores) go to <life>/neutral_probe_<pre|post>_<sleep>.json
     with the adapter path and sha256 in force, so the sleep-destruction
     replay (pre-sleep adapter on the post-sleep probe) is possible later.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import time
import unicodedata
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# --------------------------------------------------------------------------- constants
LESSON_VERSION = "q14-v1-2026-09-12"
NOTE_AFTER_LABEL = "NOTE_AFTER"
SCRATCHPAD_LABEL = "Scratchpad"
SLOT_SENTENCE = "This field is available after the execution result."

# Astra memo q14 section 1(b), verbatim.
LESSON_PARAGRAPH = (
    "A useful thing to leave yourself is a measured action record. It says what you actually tried "
    "and what you actually observed, in your own voice. An expectation is not yet a result. After a "
    "run, you can write: what I did, what happened, and—if useful—what this makes me want to "
    "test next. A poor result can still make a good record. Keep observations separate from guesses. "
    "Here are examples of the kind of memory I mean, not passes you must use.")
# Astra's three synthetic examples with the gym's real pass vocabulary in place of A/B; the OUTCOMES vary
# (improvement, no change, regression), the numbers are invented and say so in the header line.
LESSON_EXAMPLES = (
    "I ran -mem2reg and -sroa. The instruction count went from 1,000 to 800, a 20% reduction. "
    "I had expected 55%, so I overestimated the reduction.",
    "I tried -licm. I measured 600 instructions before and 600 afterward. This attempt made no "
    "further reduction; I would test another pass next.",
    "I ran -mem2reg then -loop-unroll. Instructions increased from 400 to 420. I would test "
    "-mem2reg alone next; that comparison is not yet measured.",
)
EXAMPLES_HEADER = "(Illustrative, invented examples — not measurements from this workshop.)"
REFRESHER_LINE = ("A reminder from your parent: a measured action record says what you actually "
                  "tried and what you actually observed, in your own voice. One more invented example:")
REFRESHER_EXAMPLES = (
    "I ran -gvn after -simplifycfg. The count went from 2,300 to 2,150, a 6.5% reduction; smaller than the first pass gave.",
    "I tried -instcombine on its own. 910 instructions before, 910 after. Nothing changed here.",
    "I ran -early-cse then -dce. Instructions rose from 1,480 to 1,500. I would drop -dce next time.",
)
# Astra memo q14 section 1(c), verbatim (cell C only).
BASELINE10_PARAGRAPH = (
    "For a starting practice, aim to write 10 measured action records per episode, after 10 of your "
    "actual runs. This is practice, not a requirement to invent something interesting or successful. "
    "Adjust as you learn what is useful.")
# The ACTIVE SHAM (Codex reconciliation audit 2026-09-11, blocker 1: "Cell A has no parent while B/C
# receive parent text, examples, context occupancy, and refreshers"): the same delivery schedule, the
# same warm register and the same length (word count within 5 % per delivery, asserted by
# tests/test_preschool_flags.py) as the artifact lesson, but NO artifact content -- nothing about
# records, writing after the result, first person, measured outcomes, or expectations versus results.
# Generic remarks about the optimisation task instead. `sham - none` is the parent PACKAGE
# (tokens, occupancy, refreshers); `lesson - sham` is the artifact content.
SHAM_VERSION = "sham-v1-2026-09-12"
SHAM_PARAGRAPH = (
    "Compiler passes interact, and the order in which they run matters. Some programs respond to "
    "memory-to-register promotion, others to loop transforms, and many gain little from either. "
    "Consider what you know about a program's structure before choosing a sequence: how many "
    "functions it has, whether it is loop-heavy, whether it moves its data through memory, or "
    "whether a few hot functions dominate it. Small programs and large programs often favour "
    "different passes. Here are some general remarks about programs, not passes you must use.")
SHAM_EXAMPLES = (
    "Programs built from many small functions carry call overhead, and inlining can remove some "
    "of it, while numeric kernels are dominated by their inner loops instead.",
    "Bit-manipulation routines tend to be short and branchy, so simplifying the control flow "
    "matters more there than any loop transform would.",
    "Codecs and compression programs mix table lookups with tight loops, so a sequence that helps "
    "one part can leave the other part unchanged.",
)
SHAM_EXAMPLES_HEADER = "(Illustrative, general remarks — not findings from this workshop.)"
SHAM_REFRESHER_LINE = ("A reminder from your parent: compiler passes interact and their order matters, so "
                       "think about the program's structure when you choose a sequence. One more general remark:")
SHAM_REFRESHER_EXAMPLES = (
    "Loop-heavy numeric code usually gains from invariant code motion and unrolling, while "
    "control-heavy code with few loops rarely does in practice.",
    "Dead-code elimination matters most after other passes have exposed the dead code to it.",
    "Programs that keep a lot of global state often carry more instructions than their size alone suggests.",
)
LESSON_MODES = ("none", "lesson", "lesson10", "sham")
GATE_MODES = ("off", "shadow", "enforce")
REFRESHER_SLEEPS = (1, 2, 3)
NEUTRAL_PANEL_DEFAULT = ["benchmark://npb-v0/10", "benchmark://npb-v0/25",
                         "benchmark://blas-v0/10", "benchmark://opencv-v0/60"]
SKIP_MARKER = "SLEEP_SKIPPED_INSUFFICIENT_RECORDS"
RECORD_ITEM = "Program {eid}.\nMy measured action record: {text}"

_OUTCOME = re.compile(r"instructions\s+(\d+)\s*->\s*(\d+)\s*\((-?\d+(?:\.\d+)?)%\s*reduction\)")


def parse_outcome(outcome: str) -> dict:
    """The measured facts of one execution from the gym's outcome string."""
    m = _OUTCOME.search(outcome or "")
    if m:
        return dict(before=int(m.group(1)), after=int(m.group(2)), reduction=float(m.group(3)),
                    status="success", error="")
    err = (outcome or "").strip()
    if err.upper().startswith("INVALID:"):
        err = err[len("INVALID:"):].strip()
    return dict(before=None, after=None, reduction=None, status="failure", error=err[:300])


# --------------------------------------------------------------------------- 1. the post-outcome slot
class PostOutcomeSlot:
    """Configuration and the extra generation round of the post-outcome field.
    label: the field name shown ("NOTE_AFTER" or "Scratchpad"); kind: the ledger
    row kind ("note_after" or "scratchpad"); seed_salt keeps the extra round's
    seeds distinct from the tick seeds under common-random generation."""

    def __init__(self, label: str = NOTE_AFTER_LABEL, kind: str = "note_after",
                 max_tokens: int = 100, seed_salt: int = 0x5A5A, log=None):
        self.label = label
        self.kind = kind
        self.max_tokens = int(max_tokens)
        self.seed_salt = seed_salt
        self.log = log
        self.n_calls = 0
        self.n_generations = 0
        self.total_seconds = 0.0
        self.total_chars = 0

    @staticmethod
    def execution_id(eid: str, tick: int, n: int,
                     occurrence_id: str | None = None) -> str:
        return f"{occurrence_id or eid}#t{tick}a{n}"

    def reserve_occurrences(self, drivers, ledger) -> None:
        """Persist unique visit reservations before any slot-enabled generation."""
        import fcntl
        with open(ledger.path, "a+") as locked:
            fcntl.flock(locked, fcntl.LOCK_EX)
            rows = ledger.rows()
            indices = [row["occurrence_index"] for row in rows
                       if "occurrence_index" in row]
            if any(type(index) is not int or index < 1 for index in indices):
                raise RuntimeError("invalid occurrence index in append-only ledger")
            next_index = max(indices, default=0) + 1
            for driver in drivers:
                occurrence_id = f"{driver.ep.eid}#occ{next_index}"
                ledger.append(dict(kind="episode_occurrence", episode_id=driver.ep.eid,
                                   occurrence_id=occurrence_id, occurrence_index=next_index,
                                   slot_kind=self.kind))
                driver.occurrence_id = occurrence_id
                driver.occurrence_index = next_index
                next_index += 1
            os.fsync(locked.fileno())

    def block(self, eid: str, tick: int, exec_id: str, action: str, facts: dict) -> str:
        """Astra's block: measurement first, the child's record second."""
        lines = [f"Program: {eid}    Tick: {tick}    Execution: {exec_id}",
                 f"ACT executed: {action}"]
        if facts["status"] == "success":
            lines += [f"Instructions before: {facts['before']}",
                      f"Instructions after: {facts['after']}",
                      f"Measured reduction: {facts['reduction']:.1f}%",
                      "Execution status: success"]
        else:
            lines += ["Instructions before: unavailable",
                      "Instructions after: unavailable",
                      "Measured reduction: unavailable",
                      f"Execution status: failure ({facts['error'] or 'no measurement'})"]
        lines += ["", f"{self.label}:"]
        return "\n".join(lines)

    def run_round(self, model, drivers, ledger, gen_seed) -> int:
        """Generate the field for every pending execution of the active drivers
        (one batched call), append one ledger row per execution, clear the
        pending lists. Returns the number of records written."""
        reqs = []
        for d in drivers:
            for p in d.pending_after:
                ctx = d._last_prompt if hasattr(d, "_last_prompt") else ""
                prompt = ctx.rstrip("\n") + "\n\n" + self.block(p["episode_id"], p["tick"],
                                                                p["execution_id"], p["action"],
                                                                p["facts"])
                reqs.append((d, p, prompt))
            d.pending_after = []
        if not reqs:
            return 0
        seeds = None
        if gen_seed is not None:
            seeds = [(zlib.crc32(f"{p['execution_id']}".encode()) ^ gen_seed ^ self.seed_salt) & 0x7fffffff
                     for _d, p, _pr in reqs]
        t0 = time.time()
        outs = model.batch([pr for _d, _p, pr in reqs], max_tokens=self.max_tokens, seeds=seeds)
        dt = time.time() - t0
        self.n_calls += 1
        per = dt / max(1, len(reqs))
        for (d, p, _pr), text in zip(reqs, outs):
            text = (text or "").strip()
            f = p["facts"]
            ledger.append(dict(kind=self.kind, episode_id=p["episode_id"], tick=p["tick"],
                               occurrence_id=p["occurrence_id"], occurrence_index=p["occurrence_index"],
                               execution_id=p["execution_id"], label=self.label, action=p["action"],
                               outcome=p["outcome"], before=f["before"], after=f["after"],
                               reduction=f["reduction"], status=f["status"], text=text[:2000],
                               gen_seconds=round(per, 3), n_chars=len(text)))
            self.n_generations += 1
            self.total_chars += len(text)
        self.total_seconds += dt
        return len(reqs)

    def stats(self) -> dict:
        return dict(label=self.label, kind=self.kind, max_tokens=self.max_tokens,
                    n_batch_calls=self.n_calls, n_generations=self.n_generations,
                    total_seconds=round(self.total_seconds, 2), total_chars=self.total_chars)


# --------------------------------------------------------------------------- 2. the artifact lesson
def lesson_block(mode: str, sleeps_done: int) -> str | None:
    """The text appended to the head of context for this phase, or None.
    sleeps_done = 0 before episode 1 (the full lesson); 1..3 = the refresher
    with ONE new example each; 4+ = nothing (the lesson is gone)."""
    if mode not in LESSON_MODES or mode == "none":
        return None
    sham = mode == "sham"
    para, header, examples = ((SHAM_PARAGRAPH, SHAM_EXAMPLES_HEADER, SHAM_EXAMPLES) if sham
                              else (LESSON_PARAGRAPH, EXAMPLES_HEADER, LESSON_EXAMPLES))
    ref_line, ref_examples = ((SHAM_REFRESHER_LINE, SHAM_REFRESHER_EXAMPLES) if sham
                              else (REFRESHER_LINE, REFRESHER_EXAMPLES))
    if sleeps_done == 0:
        body = [para, header] + [f"- {e}" for e in examples]
        if mode == "lesson10":
            body.append(BASELINE10_PARAGRAPH)
        return "=== A NOTE FROM YOUR PARENT ===\n" + "\n".join(body)
    if sleeps_done in REFRESHER_SLEEPS:
        ex = ref_examples[(sleeps_done - 1) % len(ref_examples)]
        return "=== A NOTE FROM YOUR PARENT ===\n" + ref_line + f"\n- {ex}"
    return None


def lesson_variant(mode: str) -> str:
    """'artifact' (lesson / lesson10), 'sham' (the active control) or 'none'."""
    return "none" if mode == "none" else ("sham" if mode == "sham" else "artifact")


def deliver_lesson(life: str, mode: str, sleeps_done: int, log=None) -> str | None:
    """lesson_block for the phase, logged once per phase to
    <life>/lesson_deliveries.jsonl (resume-safe). Never contains a score."""
    text = lesson_block(mode, sleeps_done)
    if text is None:
        return None
    path = os.path.join(life, "lesson_deliveries.jsonl")
    seen = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                seen.add(json.loads(line).get("sleeps_done"))
            except ValueError:
                continue
    if sleeps_done not in seen:
        with open(path, "a") as f:
            f.write(json.dumps(dict(version=SHAM_VERSION if mode == "sham" else LESSON_VERSION,
                                    mode=mode, variant=lesson_variant(mode), sleeps_done=sleeps_done,
                                    phase="lesson" if sleeps_done == 0 else "refresher",
                                    n_words=len(text.split()), text=text)) + "\n")
        if log:
            log(f"[preschool] lesson {mode} delivered (phase sleeps_done={sleeps_done}, "
                f"{len(text)} chars)")
    return text


# --------------------------------------------------------------------------- 3. the gate at sleep
_GATE_MOD = {}


def gate_module():
    """research_notes/analysis/articulation_gate_audit.py imported by path (the
    one implementation of G / N / F / D / P; nothing is duplicated here)."""
    if "m" not in _GATE_MOD:
        p = os.path.join(ROOT, "research_notes", "analysis", "articulation_gate_audit.py")
        spec = importlib.util.spec_from_file_location("articulation_gate_audit", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _GATE_MOD["m"] = mod
    return _GATE_MOD["m"]


def execution_facts(row: dict) -> dict | None:
    """The strict grounding set of ONE execution: the passes it ran and the
    numbers it measured (via the audit's own act indexer on a one-row ledger)."""
    g = gate_module()
    if row.get("status") != "success" or not row.get("outcome"):
        return None
    idx = g.episode_acts([dict(kind="act", episode_id=row["episode_id"], action=row.get("action") or "",
                               outcome=row.get("outcome") or "")])
    return idx.get(row["episode_id"])


def judge_record(row: dict, state) -> dict:
    """G/N/F/P/D and the admission / articulation flags of one note_after (or
    scratchpad) row against its own execution facts. `state` = the audit's
    LifeState (running duplicate window) or None."""
    g = gate_module()
    eid = row.get("episode_id") or ""
    names = (eid, eid.split("/")[-1]) if eid else ()
    text = (row.get("text") or "").strip()
    acts = execution_facts(row)
    if not text:
        j = dict(G=None, N=None, F=False, P=False, reason="empty")
    elif acts is None:
        # a failed execution measured nothing: a record of it cannot be grounded in a
        # number; judged neither admitted nor rejected for content (not in A_s's denominator)
        j = dict(G=None, N=None, F=bool(g.FIRST_PERSON_RECORD.search(text)),
                 P=any(p.search(text) for p in g.PRACTICE_PHRASES), reason="no-measurement")
    else:
        j = g.judge(text, acts, names)
    canon = g.canonical(text, names) if text else ""
    D = bool(canon) and state is not None and canon in state.canon
    if state is not None and canon:
        state.see(canon)
    reason = j["reason"]
    if reason == "admitted" and D:
        reason = "duplicate"
    adm_hi = bool(j["G"]) and (j["N"] is not False) and not D
    adm_lo = bool(j["G"]) and (j["N"] is True) and not D
    art_hi = bool(j["F"]) and bool(j["G"]) and (j["N"] is not False)
    art_lo = bool(j["F"]) and bool(j["G"]) and (j["N"] is True)
    return dict(execution_id=row.get("execution_id"), episode_id=eid, tick=row.get("tick"),
                status=row.get("status"), text=text[:400], G=j["G"], N=j["N"], F=j["F"], P=j["P"], D=D,
                reason=reason, admit_hi=adm_hi, admit_lo=adm_lo, artic_hi=art_hi, artic_lo=art_lo,
                n_chars=len(text), n_words=len(text.split()))


def _state_path(life: str) -> str:
    return os.path.join(life, "articulation_state.json")


def _load_state(life: str) -> dict:
    p = _state_path(life)
    if os.path.exists(p):
        return json.load(open(p))
    return dict(rows_seen=0, canon=[], admitted=[])


def _save_state(life: str, st: dict) -> None:
    tmp = _state_path(life) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f)
    os.rename(tmp, _state_path(life))


def _rate(vals) -> float | None:
    vals = list(vals)
    return (sum(1 for v in vals if v) / len(vals)) if vals else None


def _copy_normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", text)
    return " ".join(re.findall(r"\w+", text))


def _delivered_payloads(life: str) -> list[str]:
    path = os.path.join(life, "lesson_deliveries.jsonl")
    if not os.path.exists(path):
        return []
    payloads = []
    with open(path) as source:
        for line in source:
            if not line.strip():
                continue
            receipt = json.loads(line)
            text = receipt.get("text")
            if not isinstance(text, str) or not text.strip():
                raise RuntimeError("lesson delivery lacks text provenance")
            payloads.append(_copy_normalize(text))
            payloads.extend(_copy_normalize(part.removeprefix("- "))
                            for part in text.splitlines() if not part.startswith("==="))
    return [text for text in payloads if len(text.split()) >= 8]


def _record_provenance(row: dict, executions: dict, notes: dict,
                       lesson_payloads: list[str], row_positions=None) -> str | None:
    execution_id = row.get("execution_id")
    matches = executions.get(execution_id, [])
    if not execution_id or not matches:
        return "provenance-orphan"
    if len(matches) != 1:
        return "provenance-ambiguous-execution"
    if len(notes.get(execution_id, [])) != 1:
        return "provenance-ambiguous-record"
    action = matches[0]
    if row_positions is not None and row_positions[id(action)] >= row_positions[id(row)]:
        return "provenance-pre-outcome-record"
    for field in ("occurrence_id", "occurrence_index"):
        if field in row or field in action:
            if field not in row or field not in action or row[field] != action[field]:
                return "provenance-mismatch-" + field
    for field in ("episode_id", "tick", "action", "outcome"):
        if field not in row or field not in action or row[field] != action[field]:
            return "provenance-mismatch-" + field
    facts = parse_outcome(action["outcome"])
    for field in ("status", "before", "after", "reduction"):
        if field not in row or row[field] != facts[field]:
            return "provenance-mismatch-" + field
    normalized = " " + _copy_normalize(row.get("text") or "") + " "
    if any(" " + payload + " " in normalized for payload in lesson_payloads):
        return "provenance-lesson-echo"
    return None


def gate_sleep(rows: list, life: str, sdir: str, mode: str, min_items: int = 64, log=None,
               slot_stats: dict | None = None) -> dict:
    """The articulation gate at one sleep (Astra q14 section 3 log; section 4 item
    format). Judges the note_after rows NEW since the previous gated sleep,
    writes <sdir>/articulation_shadow.json and, in enforce mode, rewrites
    <sdir>/corpus.json to the admitted records to date (legacy corpus kept as
    corpus_legacy.json) or marks the sleep SKIPPED when they are too few."""
    if mode not in GATE_MODES or mode == "off":
        return {}
    g = gate_module()
    st = _load_state(life)
    state = g.LifeState()
    for c in st["canon"]:
        state.see(c)
    since = int(st.get("rows_seen", 0))
    if since > len(rows):
        raise RuntimeError("articulation ledger shrank; provenance requires inspection")
    executions, records = {}, {}
    row_positions = {id(row): position for position, row in enumerate(rows)}
    for row in rows:
        index = executions if row.get("kind") == "act" else records if row.get("kind") == "note_after" else None
        if index is not None:
            index.setdefault(row.get("execution_id"), []).append(row)
    lesson_payloads = _delivered_payloads(life)
    new_rows = rows[since:]
    execs = [r for r in new_rows if r.get("kind") == "act"]
    numeric = [r for r in execs if _OUTCOME.search(str(r.get("outcome") or ""))]
    notes = [r for r in new_rows if r.get("kind") == "note_after"]
    judged = [judge_record(r, state) for r in notes]
    for row, judgement in zip(notes, judged):
        rejection = _record_provenance(row, executions, records, lesson_payloads, row_positions)
        if rejection:
            judgement.update(reason=rejection, admit_hi=False, admit_lo=False,
                             artic_hi=False, artic_lo=False, G=False)
    qualifying = {j["execution_id"] for j in judged if j["artic_hi"]}
    qualifying_lo = {j["execution_id"] for j in judged if j["artic_lo"]}
    # act rows written with --note-after carry the execution id; A_s^raw = executions returning a
    # numerical result that carry a qualifying record / executions returning a numerical result
    numeric_ids = {r.get("execution_id") for r in numeric if r.get("execution_id")}
    n_num = len(numeric)
    a_hi = (len(qualifying & numeric_ids) / n_num) if n_num else None
    a_lo = (len(qualifying_lo & numeric_ids) / n_num) if n_num else None
    reasons: dict = {}
    for j in judged:
        if j["reason"] != "admitted":
            reasons[j["reason"]] = reasons.get(j["reason"], 0) + 1
    admitted_new = [dict(episode_id=j["episode_id"], execution_id=j["execution_id"],
                         text=(r.get("text") or "").strip())      # verbatim, never rewritten
                    for j, r in zip(judged, notes) if j["admit_hi"]]
    admitted_prior = []
    prior_rejections = {}
    for admitted in st["admitted"]:
        matches = records.get(admitted.get("execution_id"), [])
        rejection = "provenance-stale-admission"
        if (len(matches) == 1 and matches[0].get("episode_id") == admitted.get("episode_id")
                and (matches[0].get("text") or "").strip() == admitted.get("text")):
            rejection = _record_provenance(matches[0], executions, records, lesson_payloads, row_positions)
            if rejection is None and not judge_record(matches[0], None)["admit_hi"]:
                rejection = "provenance-invalid-prior-record"
        if rejection:
            prior_rejections[rejection] = prior_rejections.get(rejection, 0) + 1
        else:
            admitted_prior.append(admitted)
    admitted_all = admitted_prior + admitted_new
    corpus_path = os.path.join(sdir, "corpus.json")
    legacy_items = json.load(open(corpus_path))["corpus"] if os.path.exists(corpus_path) else []
    record_items = _dedup([RECORD_ITEM.format(eid=a["episode_id"], text=a["text"]) for a in admitted_all])
    rec = dict(mode=mode, sleep_dir=os.path.basename(sdir), rows_since=since, rows_now=len(rows),
               n_executions=len(execs), n_executions_numeric=n_num, n_note_after=len(notes),
               A_s_raw_hi=a_hi, A_s_raw_lo=a_lo,
               G_rate=_rate(j["G"] for j in judged if j["G"] is not None),
               N_rate=_rate(j["N"] for j in judged if j["N"] is not None),
               N_none_share=(sum(1 for j in judged if j["N"] is None) / len(judged)) if judged else None,
               F_rate=_rate(j["F"] for j in judged), D_rate=_rate(j["D"] for j in judged),
               P_rate=_rate(j["P"] for j in judged),
               GN_rate=_rate(bool(j["G"]) and j["N"] is not False for j in judged),
               admission_hi=_rate(j["admit_hi"] for j in judged), admission_lo=_rate(j["admit_lo"] for j in judged),
               n_admitted_new=len(admitted_new), n_admitted_total=len(admitted_all),
               rejection_families=reasons,
               prior_provenance_rejections=prior_rejections,
               legacy_corpus_items=len(legacy_items), record_items=len(record_items),
               corpus_survival_if_enforced=(len(record_items) / len(legacy_items)) if legacy_items else None,
               tokens_note_after_chars=sum(j["n_chars"] for j in judged),
               tokens_note_after_words=sum(j["n_words"] for j in judged),
               gate_version=g.PRACTICE_PHRASES_VERSION, window=g.WINDOW,
               grounding="strict: each record against its own execution's measured facts",
               slot=slot_stats,
               examples={k: [j["text"][:200] for j in judged if j["reason"] == k][:2] for k in reasons},
               judged=judged)
    enforced = mode == "enforce"
    if enforced:
        if not os.path.exists(os.path.join(sdir, "corpus_legacy.json")) and os.path.exists(corpus_path):
            os.replace(corpus_path, os.path.join(sdir, "corpus_legacy.json"))
        skipped = len(record_items) < int(min_items)
        rec.update(enforced=True, min_items=int(min_items), training_skipped=skipped,
                   n_dropped_legacy=len(legacy_items))
        tmp = corpus_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(dict(corpus=record_items, n_new=len(admitted_new), principles=[],
                           recipe="preschool_records_v1", n_dropped_legacy=len(legacy_items)), f, indent=1)
        os.rename(tmp, corpus_path)
        if skipped:
            with open(os.path.join(sdir, SKIP_MARKER), "w") as f:
                f.write(f"{len(record_items)} admitted records < {min_items}\n")
    else:
        rec.update(enforced=False, training_skipped=False)
    tmp = os.path.join(sdir, "articulation_shadow.json.tmp")
    with open(tmp, "w") as f:
        json.dump(rec, f, indent=1)
    os.rename(tmp, os.path.join(sdir, "articulation_shadow.json"))
    st.update(rows_seen=len(rows), canon=list(state.canon), admitted=admitted_all)
    _save_state(life, st)
    if log:
        log(f"[preschool gate {mode}] notes={len(notes)} numeric_execs={n_num} "
            f"A_s_raw={_fmt(a_lo)}-{_fmt(a_hi)} admission={_fmt(rec['admission_lo'])}-{_fmt(rec['admission_hi'])} "
            f"admitted_total={len(admitted_all)} reasons={reasons}"
            + (f" TRAINING SKIPPED ({len(record_items)} < {min_items})" if rec.get("training_skipped") else ""))
    return rec


def training_skipped(sdir: str) -> bool:
    return os.path.exists(os.path.join(sdir, SKIP_MARKER))


def _dedup(texts: list) -> list:
    seen, out = set(), []
    for t in texts:
        k = re.sub(r"\s+", " ", t.lower())
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out


def _fmt(v) -> str:
    return "-" if v is None else f"{v:.3f}"


# --------------------------------------------------------------------------- 4. neutral probes
def neutral_panel(path: str | None) -> list:
    if path:
        return list(json.load(open(os.path.expanduser(path))))
    return list(NEUTRAL_PANEL_DEFAULT)


def _adapter_sha(adapter_dir: str | None) -> str | None:
    if not adapter_dir:
        return None
    for fn in ("adapter_model.safetensors", "adapter_model.bin"):
        p = os.path.join(adapter_dir, fn)
        if os.path.exists(p):
            h = hashlib.sha256()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            return h.hexdigest()
    return None


def neutral_probe_path(life: str, when: str, episode_index: int) -> str:
    return os.path.join(life, f"neutral_probe_{when}_{episode_index:04d}.json")


def neutral_probe_run(model, gym, life: str, when: str, episode_index: int, sleep_index: int,
                      panel: list, budget_ticks: int, log, adapter_path: str | None,
                      arm: str = "on", max_tokens: int = 100, driver_cls=None) -> dict:
    """ONE held-out episode with a fresh context and the Scratchpad field, under
    the model given: arm "on" = the live model (the committed adapter, or the
    base before the first adapter), arm "off" = the frozen base opened by the
    caller exactly as run_life_v2 opens it for the ordinary probe_ep*_adapterOFF
    (VLLMBackend(adapter_path=None) after the live model is closed). The same
    program and the SAME generation seeds for the pair and for both arms.
    Separate ledger (suffix _adapterOFF for the off arm); never harvested."""
    from .batch_loop import run_episodes_batch, EpisodeDriver
    from .ledger import Ledger
    prog = panel[(sleep_index - 1) % len(panel)]
    suffix = "" if arm == "on" else "_adapterOFF"
    led_path = os.path.join(life, f"neutral_probe_{when}_{episode_index:04d}{suffix}.ledger.jsonl")
    if os.path.exists(led_path):
        raise RuntimeError("partial neutral probe ledger exists; preserve evidence and use a new probe")
    led = Ledger(led_path)
    slot = PostOutcomeSlot(label=SCRATCHPAD_LABEL, kind="scratchpad", max_tokens=max_tokens,
                           seed_salt=0x3C3C, log=log)
    res = run_episodes_batch(model, gym, [gym.episode_from_id(prog, budget_ticks)],
                             gym.birth_prompt(), led, budget_ticks, log,
                             gen_seed=9000 + sleep_index, driver_cls=driver_cls or EpisodeDriver,
                             note_after=slot)
    rows = led.rows()
    pads = [r for r in rows if r.get("kind") == "scratchpad"]
    numeric = [r for r in rows if r.get("kind") == "act" and _OUTCOME.search(str(r.get("outcome") or ""))]
    judged = [judge_record(r, None) for r in pads]
    n_num = len(numeric)
    q_hi = {j["execution_id"] for j in judged if j["artic_hi"]}
    q_lo = {j["execution_id"] for j in judged if j["artic_lo"]}
    return dict(arm=arm, program=prog, adapter=adapter_path, adapter_sha256=_adapter_sha(adapter_path),
                ledger=os.path.basename(led_path),
                best_score=res[0]["best_score"] if res else None, n_acts=res[0]["n_acts"] if res else 0,
                n_executions_numeric=n_num, n_scratchpads=len(pads),
                articulation_hi=(len(q_hi) / n_num) if n_num else None,
                articulation_lo=(len(q_lo) / n_num) if n_num else None,
                scratchpads=judged, slot=slot.stats())


def write_neutral_probe(life: str, when: str, episode_index: int, sleep_index: int,
                        on: dict, off: dict, log=None, cache_identity=None) -> dict:
    """The pair's JSON: the top-level fields are the ON run (the live model, as
    before); `on` and `off` hold both arms so the adapter-mediation contrast
    (Codex reconciliation audit, blocker 4: the H1 estimand is
    (P_on - P_off) - (S_on - S_off)) can be computed later; `off_same_as_on`
    marks the pairs taken before any adapter existed, where the off arm is the
    on arm copied, not rerun."""
    payload = dict(when=when, sleep_index=sleep_index, at_episode=episode_index, program=on["program"],
                   adapter=on["adapter"], adapter_sha256=on["adapter_sha256"],
                   best_score=on["best_score"], n_acts=on["n_acts"],
                   n_executions_numeric=on["n_executions_numeric"], n_scratchpads=on["n_scratchpads"],
                   articulation_hi=on["articulation_hi"], articulation_lo=on["articulation_lo"],
                   scratchpads=on["scratchpads"], slot=on["slot"], fresh_context=True,
                   on=on, off=off, off_same_as_on=bool(off.get("same_as_on")),
                   articulation_on_minus_off_hi=(None if on["articulation_hi"] is None or off["articulation_hi"] is None
                                                 else on["articulation_hi"] - off["articulation_hi"]),
                   note="held-out program; birth prompt only; separate ledgers; not harvested; "
                        "on = live model, off = frozen base with the same seeds")
    out_path = neutral_probe_path(life, when, episode_index)
    if cache_identity is not None:
        payload["cache_identity"] = cache_identity
    tmp = out_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=1)
    os.rename(tmp, out_path)
    if log:
        log(f"[neutral probe {when} sleep {sleep_index}] {on['program']} best_on={on['best_score']} "
            f"best_off={off['best_score']} articulation_on={_fmt(on['articulation_lo'])}-{_fmt(on['articulation_hi'])} "
            f"off={_fmt(off['articulation_lo'])}-{_fmt(off['articulation_hi'])} adapter={on['adapter']}"
            + (" (off = on: no adapter loaded)" if payload["off_same_as_on"] else ""))
    return payload


def _neutral_identity(gym, panel, budget_ticks, max_tokens, driver_cls,
                      adapter_path, when, episode_index, sleep_index):
    from .batch_loop import EpisodeDriver
    from .model_backend import MODEL
    adapter_hash = _adapter_sha(adapter_path)
    config_hash = None
    if adapter_path:
        config_path = os.path.join(adapter_path, "adapter_config.json")
        if adapter_hash is None or not os.path.isfile(config_path):
            raise RuntimeError("neutral probe adapter lacks weights/config provenance")
        with open(config_path, "rb") as source:
            config_hash = hashlib.sha256(source.read()).hexdigest()
    driver = driver_cls or EpisodeDriver
    return dict(version=1, model=MODEL, gym=gym.name,
                birth_sha256=hashlib.sha256(gym.birth_prompt().encode()).hexdigest(),
                panel=list(panel), budget_ticks=budget_ticks, max_tokens=max_tokens,
                driver=driver.__module__ + "." + driver.__qualname__,
                adapter=os.path.realpath(adapter_path) if adapter_path else None,
                adapter_sha256=adapter_hash, adapter_config_sha256=config_hash,
                when=when, episode_index=episode_index, sleep_index=sleep_index,
                generation_seed=9000 + sleep_index)


def neutral_probe(model, gym, life: str, when: str, episode_index: int, sleep_index: int,
                  panel: list, budget_ticks: int, log, adapter_path: str | None,
                  max_tokens: int = 100, driver_cls=None, open_base=None, close_base=None) -> dict | None:
    """The pre- or post-sleep neutral probe as an adapter ON / OFF PAIR on the
    same held-out program with the same seeds. `open_base()` must close the
    live model and return the frozen base backend; `close_base(base)` must
    close it and return the reloaded live model -- both supplied by
    run_life_v2 so the OFF arm uses exactly the path of the ordinary
    probe_ep*_adapterOFF. Without an adapter loaded (before the first sleep,
    or an arm-A life) the off arm is the on arm copied, flagged
    `same_as_on`. Resume-safe (marker = the JSON). Returns (payload, model):
    the live model may have been reloaded."""
    out_path = neutral_probe_path(life, when, episode_index)
    identity = _neutral_identity(gym, panel, budget_ticks, max_tokens, driver_cls,
                                 adapter_path, when, episode_index, sleep_index)
    if os.path.exists(out_path):
        with open(out_path) as source:
            cached = json.load(source)
        if cached.get("cache_identity") != identity:
            raise RuntimeError("neutral probe cache provenance mismatch; preserve evidence and use a new probe")
        return cached, model
    on = neutral_probe_run(model, gym, life, when, episode_index, sleep_index, panel, budget_ticks, log,
                           adapter_path, arm="on", max_tokens=max_tokens, driver_cls=driver_cls)
    if adapter_path and open_base is not None and close_base is not None:
        base = open_base()
        off = neutral_probe_run(base, gym, life, when, episode_index, sleep_index, panel, budget_ticks, log,
                                None, arm="off", max_tokens=max_tokens, driver_cls=driver_cls)
        model = close_base(base)
    else:
        off = dict(on, arm="off", same_as_on=True, ledger=on["ledger"])
    if identity != _neutral_identity(gym, panel, budget_ticks, max_tokens, driver_cls,
                                     adapter_path, when, episode_index, sleep_index):
        raise RuntimeError("neutral probe adapter/config changed during measurement")
    return write_neutral_probe(life, when, episode_index, sleep_index, on, off, log,
                               cache_identity=identity), model
