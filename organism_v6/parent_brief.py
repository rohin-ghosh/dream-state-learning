"""Parent the thinking pattern (Rohin, 2026-09-08): "if you see uninteresting
thinking patterns, parent something better."

At each sleep the harness measures how ritualized the child's recent thinking
has become (same ACT recipe, same PREDICT value, near-identical NOTEs across
episodes). If it is templated, a stronger parent model is shown the metrics
and a few raw chunks and asked for a short, concrete, richer THINKING PATTERN
(process only; leak-scanned so it cannot hand over pass names or answers).
The result is appended to the waking brief the child reads at the next wake,
and logged with provenance to the life's parent ledger.

Default-off: `run_life_v2 --parent-url` enables it; R2 lives are untouched.
"""
from __future__ import annotations
import collections
import json
import os
import re
import statistics

from .parent_backend import PARENT_BOOT, ParentLedger, ServerParent, \
    leak_scan, FALLBACK

_ACT = re.compile(r"^ACT:\s*(.+)$", re.M)
_PRED = re.compile(r"^PREDICT:\s*([0-9.]+)", re.M)
_NOTE = re.compile(r"^NOTE:\s*(.+)$", re.M)
_RECALL = re.compile(r"^RECALL:\s*(.+)$", re.M)


def _toks(s: str) -> set:
    return set(re.findall(r"[a-z]{3,}", s.lower()))


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 1.0


def episode_instances(thought_rows: list[dict]) -> "collections.OrderedDict":
    """Group thought rows into EPISODE INSTANCES. The gym re-plays the same
    ~67 programs many times, so episode_id alone conflates repeats (found
    2026-09-09: 67 ids vs ~400 instances). A new instance of a program starts
    when its tick does not increase (wake batches interleave programs, so
    track the last tick per program, not globally)."""
    inst = collections.OrderedDict()
    last_tick, count = {}, collections.Counter()
    for r in thought_rows:
        e = r.get("episode_id")
        try:
            t = int(r.get("tick", 0))
        except (TypeError, ValueError):
            t = 0
        if e not in last_tick or t <= last_tick[e]:
            count[e] += 1
        last_tick[e] = t
        inst.setdefault((e, count[e]), []).append(r["note"])
    return inst


def ritual_metrics(rows: list[dict], last_episodes: int = 32,
                   brief_text: str = "") -> dict:
    """Ritual = low variety across EPISODES (not within one).
    Rehearsal-aware (Rohin 2026-09-10, "repetition is key"): a first NOTE
    that restates the parent's brief is the child doing what it was asked,
    not ritual — it is skipped when judging templated notes."""
    th = [r for r in rows if r.get("kind") == "thought" and r.get("note")]
    eps = list(episode_instances(th).items())[-last_episodes:]
    bt = _toks(brief_text) if brief_text else set()
    if len(eps) < 4:
        return dict(n_episodes=len(eps), ritual=False, reason="too few")
    first_acts, preds, first_notes, recalls = [], [], [], []
    for eid, notes in eps:
        text = "\n".join(notes)
        a = _ACT.findall(text)
        if a:
            first_acts.append(re.sub(r"\s+", "", a[0]))
        preds += [float(x) for x in _PRED.findall(text) if x.count(".") <= 1]
        n = _NOTE.findall(text)
        if bt:                                   # drop rehearsal notes
            n = [x for x in n if len(_toks(x) & bt) < 4]
        if n:
            first_notes.append(_toks(n[0]))
        recalls += [q.strip().lower() for q in _RECALL.findall(text)]
    modal_share = (collections.Counter(first_acts).most_common(1)[0][1]
                   / len(first_acts)) if first_acts else 0.0
    pred_sd = statistics.pstdev(preds) if len(preds) > 1 else 0.0
    pred_distinct = len(set(round(p, 2) for p in preds))
    note_sim = statistics.mean(
        _jaccard(first_notes[i], first_notes[i + 1])
        for i in range(len(first_notes) - 1)) if len(first_notes) > 1 else 0.0
    recall_modal = (collections.Counter(recalls).most_common(1)[0][1]
                    / len(recalls)) if recalls else 0.0
    m = dict(n_episodes=len(eps), modal_first_act_share=round(modal_share, 3),
             predict_sd=round(pred_sd, 3), predict_distinct=pred_distinct,
             note_consecutive_jaccard=round(note_sim, 3),
             recall_modal_share=round(recall_modal, 3))
    # thresholds are deliberately simple and written down; tune via Codex
    flags = []
    if modal_share >= 0.7:
        flags.append("same_recipe")
    if pred_sd < 0.05 and len(preds) >= 8:
        flags.append("flat_predictions")
    if note_sim >= 0.5:
        flags.append("templated_notes")
    if recall_modal >= 0.7 and len(recalls) >= 8:
        flags.append("same_recall")
    m["flags"] = flags
    m["ritual"] = len(flags) >= 2
    return m


PROMPT_VERSION = "v3-2026-09-10-repetition"
# v3 (Rohin: "repetition is key"): the parent keeps the SAME core lesson
# across sleeps (it sees its previous brief), reports whether the child has
# begun rehearsing it, and every brief ends by asking the child to restate
# the lesson as its first NOTE of each episode until it is how it thinks.
REHEARSAL_TAIL = ("\n\nRepeat after me, every episode, in your own words, as "
                  "your first NOTE before you act: what the ritual was and "
                  "what you do instead. Keep repeating it until it is simply "
                  "how you think.")


def rehearsal_rate(rows: list[dict], brief_text: str,
                   last_episodes: int = 32) -> float:
    """Fraction of recent episodes whose FIRST NOTE shares >= 4 content
    words with the brief — did the child start repeating the lesson?"""
    if not brief_text:
        return 0.0
    bt = _toks(brief_text)
    th = [r for r in rows if r.get("kind") == "thought" and r.get("note")]
    eps = list(episode_instances(th).items())[-last_episodes:]
    hit = n = 0
    for _k, notes in eps:
        m = _NOTE.findall("\n".join(notes))
        if not m:
            continue
        n += 1
        if len(_toks(m[0]) & bt) >= 4:
            hit += 1
    return hit / n if n else 0.0
# v1 produced generic advice ("vary your expected outcomes"), which is wrong:
# a prediction must follow from the situation, not be varied for variety.
# v2 asks for a pattern grounded in the situation's features and in contrast.
_PROMPT = (PARENT_BOOT + "\n\n=== WHY YOU ARE BEING CALLED ===\nYour child's "
           "thinking has become ritualized. Measured over its last {n} "
           "episodes: {metrics}\n\n=== RAW SAMPLES OF ITS THINKING ===\n{samples}"
           "\n=== END ===\nWrite a BRIEF for your child (max 8 lines). Line 1: "
           "name the ritual you see, quoting a phrase it keeps repeating. Then "
           "prescribe a richer thinking pattern with SUBSTANCE, not variety for "
           "its own sake:\n"
           "- PREDICT must be a consequence of a named feature of THIS situation "
           "(what the child observed about this case), stated with a reason and a "
           "range; the same prediction is fine when the situations are alike, but "
           "the child must say why they are alike.\n"
           "- NOTE must contain a contrast: this case versus a specific earlier "
           "case, what differed, and a scope (when this lesson applies and when it "
           "does not). A NOTE that could be pasted into any episode is worthless.\n"
           "- RECALL must be a specific query about similar situations, not a "
           "restatement of the plan.\n"
           "- When the child has repeated the same first action for many episodes, "
           "it should run ONE deliberate deviation per episode and predict its "
           "effect before seeing it; a surprise means a belief is wrong — name "
           "which one.\n"
           "Process only. Never name specific actions, tools, passes, options, or "
           "answers. Speak to the child directly, concretely, in its own terms.\n"
           "{previous}")

_PREV_BLOCK = ("=== YOUR PREVIOUS BRIEF TO THIS CHILD ===\n{prev}\n=== END ===\n"
               "Since that brief, the child restated your lesson at the start of "
               "{rate:.0%} of its episodes. Keep the SAME core lesson — repetition "
               "is how it will take. Do not switch to a new lesson; sharpen the "
               "same one, acknowledge what the child has started doing, and "
               "insist on the rest.")


def _already_childs(hit: str, text: str, samples: str) -> bool:
    """True if every match of this leak pattern in the parent's text already
    appears verbatim in the child's own sampled thinking (quoting back)."""
    if hit.startswith("words:") or hit.startswith("term:"):
        return False                      # rule-content leaks are never ok
    try:
        found = re.findall(hit, text, re.I)
    except re.error:
        return False
    if not found:
        return False
    low = samples.lower()
    return all(str(f).lower() in low for f in found)


def parent_brief(life_dir: str, rows: list[dict], sleep_dir: str,
                 parent_url: str, model_name: str,
                 last_episodes: int = 32) -> dict:
    """Measure ritual; if flagged, ask the parent for a better pattern and
    write it to <sleep_dir>/parent_brief.txt. Idempotent per sleep."""
    out = os.path.join(sleep_dir, "parent_brief.txt")
    meta_p = os.path.join(sleep_dir, "parent_brief.json")
    if os.path.exists(meta_p):
        return json.load(open(meta_p))
    ledger = ParentLedger(life_dir)
    # the most recent brief from any earlier sleep (repetition, consistency)
    prev_text = ""
    for d in sorted(os.listdir(life_dir), reverse=True):
        pb = os.path.join(life_dir, d, "parent_brief.txt")
        if d.startswith("sleep_") and d != os.path.basename(sleep_dir) \
                and os.path.exists(pb):
            prev_text = open(pb).read().strip()
            if prev_text:
                break
    m = ritual_metrics(rows, last_episodes, brief_text=prev_text)
    m["rehearsal_rate"] = round(rehearsal_rate(rows, prev_text,
                                               last_episodes), 3)
    meta = dict(metrics=m, intervened=False, text=None, hits=None,
                prompt_version=PROMPT_VERSION)
    if m.get("ritual"):
        th = [r["note"] for r in rows if r.get("kind") == "thought"
              and r.get("note")][-400:]
        step = max(1, len(th) // 4)
        samples = "\n---\n".join(t[:600] for t in th[::step][:4])
        parent = ServerParent(base_url=parent_url, model=model_name,
                              ledger=ledger)
        previous = _PREV_BLOCK.format(prev=prev_text[:1200],
                                      rate=m["rehearsal_rate"]) \
            if prev_text else ""
        text = parent._chat(_PROMPT.format(n=m["n_episodes"],
                                           metrics=json.dumps(m),
                                           samples=samples,
                                           previous=previous),
                            max_tokens=320, temperature=0.4)
        # A term the child ALREADY uses in its own sampled thinking is not a
        # leak when the parent quotes it back (the gym-token pattern otherwise
        # blocks every brief that names the child's own ritual recipe —
        # observed 2026-09-10: v3 briefs on the gym fell back).
        hits = [h for h in leak_scan(text)
                if not _already_childs(h, text, samples)]
        if hits:
            text = FALLBACK
        text = text.strip() + REHEARSAL_TAIL
        meta.update(intervened=True, text=text, hits=hits,
                    prompt_version=PROMPT_VERSION, parent_model=model_name)
        with open(out, "w") as f:
            f.write(text.strip()[:1900])
        ledger.append(kind="thinking_pattern", source="parent",
                      child_stage=os.path.basename(sleep_dir),
                      metrics=m, hits=hits, text=text[:1900],
                      prompt_version=PROMPT_VERSION, parent_model=model_name)
    else:
        ledger.append(kind="ritual_check", source="harness",
                      child_stage=os.path.basename(sleep_dir), metrics=m)
    with open(meta_p, "w") as f:
        json.dump(meta, f, indent=1)
    return meta
