"""v6 sleep: the experience compiler (DESIGN.md section 4; menu i+ii+iii).

Support-gated (v5's law: nothing unverified enters training):
  i   verified improvements  -> state->action exemplars
  ii  contrast pairs          -> fail->recover, slow->fast
  iii principle synthesis     -> "when X do Y because measured Z",
                                 requires support from >=2 distinct episodes
Plus the DREAMED BOOTSTRAP: sleep also emits a waking brief that becomes
the head-of-context for the next wake (the birth prompt is wake #0's brief).
THINK-calls (the same model) do all restatement — no learned sleeper.
Training: cumulative LoRA from CLEAN BASE over all compiled data to date.

2026-09-10 (gym protocol): the exemplar and THINK-prompt templates take their
nouns from a VOCABULARY (Gym.compile_vocab()) so a childhood life in a trait
gym compiles with zero deployment-gym (compiler) content — "Puzzle rg/...",
"which attempt scores best?", "solving these puzzles". The default vocabulary
is the compiler's, byte-identical to the strings this module always had
(tests/test_compiler_golden.py). Rows stamped with a `gym` field (pooled clone
ledgers, ProvenanceLedger lives) resolve their vocabulary per row through
`vocab_by_gym`; the THINK prompts of a mixed pool use NEUTRAL_VOCAB.
Pooled rows also carry `clone_id`: wins, pathways, recoveries and contrasts
are grouped by (clone_id, episode_id), so one clone's thinking is never
compiled as the pathway to another clone's action (provenance as hygiene,
not attribution: the corpus text stays unlabelled).
"""
from __future__ import annotations
import json
import os
import re


_MD_MARK = re.compile(
    r"^\s*(?:#{1,6}\s*|[-*]\s+|\*\*|>\s*)+\s*(PREDICT|ACT|NOTE|RECALL|DONE)\b\**:?\**\s*",
    re.MULTILINE)


# --- vocabularies -----------------------------------------------------------------
# noun: the situation noun as it opens an exemplar; plural: in the THINK
# prompts; did: what the child did to them; action_slot: the PRINCIPLE line's
# action placeholder; id_tag: the bracket tag of the principle's support ids
# (the principle parser accepts it in singular and plural); domain: the brief
# prompt's subject; win_question: the Q of a win exemplar.
COMPILER_VOCAB = dict(
    noun="Program", plural="programs", did="you optimized",
    action_slot="action/pass choice", id_tag="programs",
    domain="optimizing these programs", win_question="which passes improve it?")
NEUTRAL_VOCAB = dict(
    noun="Situation", plural="situations", did="you worked through",
    action_slot="action choice", id_tag="situations",
    domain="handling these situations", win_question="which action improves it?")
_VOCAB_KEYS = tuple(COMPILER_VOCAB)


def _full_vocab(v: dict | None) -> dict:
    """A complete vocabulary: missing keys fall back to the compiler's (the
    historical strings), so a partial dict never breaks a template."""
    out = dict(COMPILER_VOCAB)
    if v:
        out.update({k: str(v[k]) for k in _VOCAB_KEYS if v.get(k)})
    return out


def canonicalize_dialect(text: str) -> str:
    """Strip Markdown decoration from marker lines so the training corpus is
    always in the canonical dialect ("ACT: ..." at line start). Measured
    necessity (2026-09-07): base Qwen-7B emits "### ACT:" ~30% of the time;
    a first sleep that captures those locks Markdown in for life."""
    return _MD_MARK.sub(lambda m: m.group(1) + ": ", text)


def _group_key(row: dict):
    """Rows of one life carry no clone_id (None): grouping by episode_id, as
    always. Pooled rows are grouped per clone as well."""
    return (row.get("clone_id"), row["episode_id"])


def select(ledger_rows: list[dict], since_tick_by_ep: dict | None = None,
           top_surprise: int = 12) -> dict:
    acts = [r for r in ledger_rows if r.get("kind") == "act"]
    wins, recoveries, contrasts = [], [], []
    by_ep: dict[str, list] = {}       # evidence lines: per episode id
    by_group: dict = {}               # wins/pathways: per (clone, episode id)
    for a in acts:
        by_ep.setdefault(a["episode_id"], []).append(a)
        by_group.setdefault(_group_key(a), []).append(a)
    for _key, rows in by_group.items():
        best = 0.0
        last_fail = None
        for a in rows:
            s = a.get("score") or 0.0
            if s > best + 1e-9:
                wins.append(a)
                if last_fail is not None:
                    recoveries.append((last_fail, a))
                best = s
            if (not a.get("outcome", "").startswith("INVALID")
                    and s < best - 1e-9) or a.get("outcome", "").startswith("INVALID"):
                last_fail = a
        good = [a for a in rows if (a.get("score") or 0) > 0]
        if len(good) >= 2:
            good.sort(key=lambda a: (-(a.get("score") or 0), len(a["action"])))
            slow, fast = good[-1], good[0]
            if fast is not slow and (fast.get("score") or 0) >= (slow.get("score") or 0):
                contrasts.append((slow, fast))
    surprises = sorted((a for a in acts if a.get("surprise") is not None),
                       key=lambda a: -abs(a["surprise"]))[:top_surprise]
    return dict(wins=wins, recoveries=recoveries, contrasts=contrasts,
                surprises=surprises, by_ep=by_ep)


_PRINCIPLE_PROMPT = """You are consolidating your own experience while asleep.
Below are verified results from {n} different {plural} {did}.
Write up to {k} PRINCIPLES you can justify from at least TWO different
{plural}. Format each as exactly one line:
PRINCIPLE: when <situation>, <{action_slot}>, because <measured effect> [{id_tag}: <id1>, <id2>]
Only claim what the data shows. If fewer than {k} are justified, write fewer.

{evidence}
"""

_BRIEF_PROMPT = """You are waking up. Summarize, from the evidence below, a
short briefing to your waking self (max 8 lines): what you now know about
{domain}, what tends to work, what to try first, what to
avoid, and one thing you are unsure about. Write it as notes to yourself.

{evidence}
"""


def _id_tag_re(id_tag: str) -> str:
    """'programs' -> 'programs?' (the historical parser accepted the tag in
    singular and plural); any other tag likewise."""
    t = str(id_tag)
    return re.escape(t[:-1]) + "s?" if t.endswith("s") else re.escape(t)


def _pathway(ledger_rows: list[dict], win: dict, n_thoughts: int = 2,
             noun: str = "Program") -> str:
    """Sleep-v2 (Rohin's ruling): compile the PATHWAY — the thinking that
    preceded a verified win — not just the winning action. Thoughts are taken
    from the SAME clone's rows only (pooled ledgers)."""
    pre = [r for r in ledger_rows
           if r.get("kind") == "thought"
           and r.get("episode_id") == win["episode_id"]
           and r.get("clone_id") == win.get("clone_id")
           and r.get("tick", 0) <= win.get("tick", 0)]
    thoughts = " ... ".join(canonicalize_dialect(r.get("note", ""))[:400]
                            for r in pre[-n_thoughts:])
    return (f"{noun} {win['episode_id']}. My thinking: {thoughts}\n"
            f"So I did: {win['action']} -> {win['outcome']}")


def _reflection_exemplar(r: dict) -> str:
    at = r.get("at_episode")
    when = f"after episode {at}" if at is not None else str(r.get("episode_id", ""))
    return (f"[reflection] My private thinking {when}: "
            f"{canonicalize_dialect(r.get('note', ''))[:1200]}")


class _Vocab:
    """Per-row vocabulary resolution: a row's `gym` field selects from
    vocab_by_gym; rows without one (or with an unknown gym) use the default.
    The THINK prompts use the single vocabulary in play, else NEUTRAL."""

    def __init__(self, vocab=None, vocab_by_gym=None):
        self.default = _full_vocab(vocab)
        self.by_gym = {k: _full_vocab(v) for k, v in (vocab_by_gym or {}).items()}
        self.seen: list = []

    def of(self, row: dict) -> dict:
        v = self.by_gym.get(row.get("gym")) if row.get("gym") else None
        v = v or self.default
        if v not in self.seen:
            self.seen.append(v)
        return v

    def prompt_vocab(self, rows) -> dict:
        for r in rows:
            self.of(r)
        if len(self.seen) == 1:
            return self.seen[0]
        return dict(NEUTRAL_VOCAB) if self.seen else self.default


def transform(model, sel: dict, k_principles: int = 6,
              ledger_rows: list[dict] | None = None,
              n_anchors: int = 8, vocab: dict | None = None,
              vocab_by_gym: dict | None = None) -> dict:
    """THINK-calls restate selections into training texts + principles + brief.
    Sleep-v2: pathway exemplars (situation+thinking+action+outcome) and
    verbatim episodic ANCHORS (node retention — not fully lossy, so
    generalization stays bounded to experience)."""
    vb = _Vocab(vocab, vocab_by_gym)
    exemplars = []
    for a in sel["wins"]:
        v = vb.of(a)
        if ledger_rows:
            exemplars.append(_pathway(ledger_rows, a, noun=v["noun"]))
        exemplars.append(
            f"{v['noun']} {a['episode_id']}. Q: {v['win_question']}\n"
            f"A: {a['action']} -> {a['outcome']}")
    # episodic anchors: raw verbatim events, highest-surprise first
    for a in (sel.get("surprises") or [])[:n_anchors]:
        exemplars.append(
            f"[episodic] On {a['episode_id']} I predicted "
            f"{a.get('prediction')} for {a['action']} and measured: "
            f"{a['outcome']}.")
    for bad, good in sel["recoveries"]:
        v = vb.of(bad)
        exemplars.append(
            f"{v['noun']} {bad['episode_id']}. Tried {bad['action']} -> "
            f"{bad['outcome']}. Better: {good['action']} -> {good['outcome']}")
    for slow, fast in sel["contrasts"]:
        v = vb.of(slow)
        exemplars.append(
            f"{v['noun']} {slow['episode_id']}: {slow['action']} scored "
            f"{slow.get('score', 0):.3f}; more efficient: {fast['action']} "
            f"scored {fast.get('score', 0):.3f}.")
    # private reflection rows (2026-09-10): the child's own thinking between
    # sessions enters the corpus like any other thought of its own. Nothing
    # is added when there are none (lives without --reflect-every compile
    # byte-identically).
    for r in (ledger_rows or []):
        if r.get("kind") == "reflection" and r.get("note"):
            exemplars.append(_reflection_exemplar(r))

    ev_lines = []
    for ep, rows in sel["by_ep"].items():
        good = [a for a in rows if (a.get("score") or 0) > 0]
        good.sort(key=lambda a: -(a.get("score") or 0))
        for a in good[:3]:
            ev_lines.append(f"[{ep}] {a['action']} -> {a['outcome']}")
    evidence = "\n".join(ev_lines[-80:]) or "(no verified wins yet)"

    pv = vb.prompt_vocab(a for rows in sel["by_ep"].values() for a in rows)
    principles = []
    if len(sel["by_ep"]) >= 2 and ev_lines:
        out = model(_PRINCIPLE_PROMPT.format(
            n=len(sel["by_ep"]), k=k_principles, evidence=evidence, **pv))
        tag = _id_tag_re(pv["id_tag"])
        for line in out.splitlines():
            m = re.match(r"\s*PRINCIPLE:\s*(.+)", line)
            if m and re.search(rf"{tag}:\s*\S+.*,", m.group(1)):
                principles.append(m.group(1).strip())
    brief = model(_BRIEF_PROMPT.format(evidence=evidence, **pv)).strip()[:2000] \
        if ev_lines else ""
    return dict(exemplars=exemplars, principles=principles, brief=brief)


def dedup(texts: list[str]) -> list[str]:
    seen, out = set(), []
    for t in texts:
        key = re.sub(r"\s+", " ", t.lower())[:160]
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out


def compile_sleep(model, ledger_rows: list[dict], out_dir: str,
                  prior_corpus: list[str], vocab: dict | None = None,
                  vocab_by_gym: dict | None = None) -> dict:
    """Full compile. Returns {corpus, brief}; corpus is CUMULATIVE
    (old interleaved with new — CLS law), atomically written.
    vocab: the gym's compile vocabulary (Gym.compile_vocab(); None = the
    compiler's, unchanged); vocab_by_gym: {gym name: vocabulary} for rows
    that carry a `gym` field (pooled clone ledgers)."""
    os.makedirs(out_dir, exist_ok=True)
    sel = select(ledger_rows)
    tr = transform(model, sel, ledger_rows=ledger_rows, vocab=vocab,
                   vocab_by_gym=vocab_by_gym)
    new_texts = dedup(tr["exemplars"] + [f"Principle: {p}" for p in tr["principles"]])
    corpus = dedup(list(prior_corpus) + new_texts)
    tmp = os.path.join(out_dir, ".corpus.tmp")
    with open(tmp, "w") as f:
        json.dump(dict(corpus=corpus, n_new=len(new_texts),
                       principles=tr["principles"]), f, indent=1)
    os.rename(tmp, os.path.join(out_dir, "corpus.json"))
    with open(os.path.join(out_dir, "waking_brief.txt"), "w") as f:
        f.write(tr["brief"])
    return dict(corpus=corpus, brief=tr["brief"], n_new=len(new_texts),
                n_principles=len(tr["principles"]))


def compile_native(ledger_rows: list[dict], out_dir: str,
                   prior_corpus: list, recall_mix: float = 0.3,
                   model=None) -> dict:
    """Sleep-v2.2: DIALECT-MATCHED compile (Codex's correction). Exemplars
    are (stored context render -> the agent's own successful continuation):
    win chunks and NOTE chunks, teacher-forced in the native marker stream.
    Scoped recall Q->A pairs stay as a minority mix (facts still stored)."""
    import os as _os
    _os.makedirs(out_dir, exist_ok=True)
    stream = []
    for r in ledger_rows:
        if r.get("kind") != "thought" or not r.get("prompt"):
            continue
        if r.get("win") or r.get("had_note"):
            stream.append({"q": r["prompt"],
                           "a": canonicalize_dialect(r["note"]),
                           "type": "stream"})
    for r in ledger_rows:          # private reflection rows (see transform)
        if r.get("kind") == "reflection" and r.get("prompt") and r.get("note"):
            stream.append({"q": r["prompt"],
                           "a": canonicalize_dialect(r["note"]),
                           "type": "reflection"})
    notes = [r for r in ledger_rows if r.get("kind") == "note"]
    n_recall = max(1, int(len(stream) * recall_mix)) if stream else len(notes)
    recall = [{"q": f"What have you learned that applies to "
                    f"{n.get('episode_id', 'your work')}? Answer with scope.",
               "a": n.get("note", ""), "type": "recall"}
              for n in notes[-n_recall:] if n.get("note")]
    seen, corpus = set(), []
    for it in list(prior_corpus) + stream + recall:
        if not isinstance(it, dict):
            continue
        key = (it["a"][:120]).lower()
        if key not in seen:
            seen.add(key)
            corpus.append({"q": it["q"], "a": it["a"]})
    tmp = _os.path.join(out_dir, ".corpus.tmp")
    with open(tmp, "w") as f:
        json.dump(dict(corpus=corpus, recipe="v2.2_native",
                       n_stream=len(stream), n_recall=len(recall)), f)
    _os.rename(tmp, _os.path.join(out_dir, "corpus.json"))
    return dict(corpus=corpus, n_stream=len(stream), n_recall=len(recall))
