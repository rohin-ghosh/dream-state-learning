"""Private reflection time (Rohin, 2026-09-10 night — the fourth kind of time
in a gym cycle): between sessions the child receives a short summary of its
own recent ledger and writes freely for a few chunks — no task, no score, no
parent. Rows go to ledger.jsonl with kind="reflection" and enter the sleep
corpus like any other thought of the child's (sleep_compile). The parent
harness may read them (ChildView reads the ledger) but must never quote,
grade, mention or respond to them. What is ENFORCED IN CODE (the prompts say
exactly this, REFLECTION_RULE):
  - a quote: >= QUOTE_WORDS consecutive words of a reflection, compared after
    unicode normalisation (NFKC, curly quotes -> ', zero-width and soft-hyphen
    characters stripped, in-word hyphens dropped: "re-plan" == "replan");
  - a paraphrase: >= OVERLAP_WORDS content words of ONE reflection row reused
    in the parent's text that the child has not written anywhere the parent
    was shown (its sampled thinking / waking brief);
  - a mention: "reflection", "reflect...", "you wrote", "your private",
    "private time", "between sessions" while reflection rows are visible.
Any of these in a brief (or the frontier estimate / move reason) discards the
brief and delivers the fixed fallback; in a critique, a proposal's evidence or
a society note the offending string is redacted before it is logged. The
parent ledger records only HOW MANY reflection rows were visible; hit strings
carry counts, never reflection text.

Default off: run_life_v2 --reflect-every N (episodes) turns it on.
"""
from __future__ import annotations
import re
import unicodedata

REFLECTION_KIND = "reflection"
QUOTE_WORDS = 6
OVERLAP_WORDS = 4
REFLECTION_RULE = (
    "PRIVATE REFLECTION (hard rule, enforced in code): this child's ledger "
    "contains rows of kind 'reflection' — its private thinking between "
    "sessions, written with no task, no score and no one to answer to. You may "
    "read them to understand the child. You must NEVER quote, grade, mention, "
    "evaluate or respond to them, in the brief or anywhere else, and never let "
    "the child know that anyone reads them. Enforced: a brief that quotes six "
    "or more consecutive words of a reflection (punctuation, quotes and hyphens "
    "normalised), that reuses four or more of one reflection's content words "
    "the child has not written elsewhere, or that mentions reflection at all "
    "('reflection', 'reflect', 'you wrote', 'your private', 'private time', "
    "'between sessions') is discarded and replaced by the fixed fallback; the "
    "same text in a critique or in evidence is redacted before it is logged. A "
    "paraphrase that escapes these checks is still a violation: the other "
    "parent's critique and the audit look for it.")

_WORD = re.compile(r"[a-z0-9']+")
# zero-width space/non-joiner/joiner, word joiner, BOM, soft hyphen
_ZERO_WIDTH = re.compile("[\u200b\u200c\u200d\u2060\ufeff\u00ad]")
_QUOTES = {"\u2018": "'", "\u2019": "'", "\u201b": "'", "\u2032": "'",
           "\u201c": '"', "\u201d": '"'}
# ASCII hyphen, non-breaking/figure/en/em dashes between word characters
_INWORD_HYPHEN = re.compile("(?<=\\w)[-\u2010\u2011\u2012\u2013\u2014](?=\\w)")
_MENTION = [
    ("reflection_mention:reflect", re.compile(r"\breflect\w*", re.I)),
    ("reflection_mention:you_wrote", re.compile(r"\byou wrote\b", re.I)),
    ("reflection_mention:your_private", re.compile(r"\byour private\b", re.I)),
    ("reflection_mention:private_time", re.compile(r"\bprivate time\b", re.I)),
    ("reflection_mention:between_sessions",
     re.compile(r"\bbetween sessions\b", re.I)),
]
_CONTENT_STOP = {
    "the", "and", "are", "for", "with", "than", "that", "this", "its", "all",
    "any", "two", "one", "most", "least", "not", "but", "you", "your", "yours",
    "was", "were", "have", "has", "had", "will", "would", "can", "could",
    "should", "may", "might", "from", "into", "about", "what", "when", "where",
    "which", "who", "how", "why", "there", "here", "then", "them", "they",
    "their", "our", "out", "own", "did", "does", "doing", "done", "just",
    "very", "also", "more", "some", "such", "each", "every", "because",
    "before", "after", "again", "next", "time", "keep", "same", "still",
    "yet", "now", "too", "much", "many", "want", "like", "think", "thing",
    "things", "something", "anything", "nothing", "make", "made", "take",
    "took", "get", "got", "let", "say", "said", "see", "saw", "look", "try",
    "first", "last", "well", "way", "ways", "over", "under", "off", "only",
    "even", "ever", "never", "always", "once", "these", "those", "being",
    "been", "myself", "itself", "himself", "herself",
}


def normalize(text: str) -> str:
    """Unicode-normalised lowercase text for comparison: NFKC, curly quotes
    straightened, zero-width and soft-hyphen characters removed, hyphens
    inside words dropped (re-plan == replan)."""
    t = unicodedata.normalize("NFKC", str(text or ""))
    t = _ZERO_WIDTH.sub("", t)
    for k, v in _QUOTES.items():
        t = t.replace(k, v)
    t = _INWORD_HYPHEN.sub("", t)
    return t.lower()


def reflection_rows(rows: list) -> list:
    return [r for r in rows if isinstance(r, dict)
            and r.get("kind") == REFLECTION_KIND and r.get("note")]


def reflection_texts(rows: list) -> list:
    return [str(r["note"]) for r in reflection_rows(rows)]


def _words(text: str) -> list:
    return _WORD.findall(normalize(text))


def content_words(text: str) -> set:
    return {w for w in _words(text) if len(w) >= 3 and w not in _CONTENT_STOP
            and not w.isdigit()}


def quoted_reflection_ngrams(text: str, reflections: list,
                             n: int = QUOTE_WORDS) -> list:
    """The n-word runs of `text` that appear verbatim (case-, punctuation-,
    quote- and hyphen-insensitive) in any reflection. Empty = no quote."""
    if not text or not reflections:
        return []
    bank = set()
    for r in reflections:
        w = _words(r)
        for i in range(len(w) - n + 1):
            bank.add(tuple(w[i:i + n]))
    if not bank:
        return []
    w = _words(text)
    hits = []
    for i in range(len(w) - n + 1):
        g = tuple(w[i:i + n])
        if g in bank:
            hits.append(" ".join(g))
            if len(hits) >= 3:
                break
    return hits


def reflection_word_overlap(text: str, reflections: list, samples: str = "",
                            min_words: int = OVERLAP_WORDS) -> int:
    """The largest number of content words of ONE reflection row that `text`
    reuses and that do not occur in `samples` (the child's own text the
    parent was legitimately shown). 0 when below `min_words`."""
    if not text or not reflections:
        return 0
    tw = content_words(text)
    if not tw:
        return 0
    shown = content_words(samples) if samples else set()
    best = 0
    for r in reflections:
        ov = (content_words(r) & tw) - shown
        best = max(best, len(ov))
    return best if best >= min_words else 0


def reflection_mentions(text: str) -> list:
    return [name for name, pat in _MENTION if pat.search(text or "")]


def reflection_violations(text: str, reflections: list,
                          samples: str = "") -> list:
    """Every enforced violation of the private-reflection rule in `text`,
    as hit labels that carry COUNTS, never reflection content. Empty when
    there are no reflection rows (lives without --reflect-every are never
    affected) or the text is clean."""
    if not reflections or not text:
        return []
    hits = []
    q = quoted_reflection_ngrams(text, reflections)
    if q:
        hits.append(f"reflection_quote:{len(q)}")
    ov = reflection_word_overlap(text, reflections, samples)
    if ov:
        hits.append(f"reflection_words:{ov}")
    hits += reflection_mentions(text)
    return hits


def scrub_reflections(obj, reflections: list, samples: str = "",
                      marker: str = "[redacted: private reflection]"):
    """Replace every string VALUE of a JSON-like structure that violates the
    rule with `marker` (used on critiques, evidence and society notes before
    they are logged)."""
    if not reflections:
        return obj
    if isinstance(obj, str):
        return marker if reflection_violations(obj, reflections, samples) else obj
    if isinstance(obj, dict):
        return {k: scrub_reflections(v, reflections, samples, marker)
                for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [scrub_reflections(v, reflections, samples, marker) for v in obj]
    return obj


def summarize_recent(rows: list, since: int = 0, max_episodes: int = 12,
                     max_notes: int = 3, max_chars: int = 1500) -> str:
    """A short, harness-written summary of the child's own recent rows
    (attempts, best scores, its last notes). Contains only what the child
    itself did and wrote."""
    recent = rows[since:]
    # situations = episode INSTANCES: the same program is replayed many
    # times, so a new instance starts when a program's tick goes backwards
    eps: dict = {}
    order: list = []
    last_tick: dict = {}
    count: dict = {}
    for r in recent:
        if r.get("kind") != "act":
            continue
        e = r.get("episode_id", "?")
        try:
            t = int(r.get("tick", 0))
        except (TypeError, ValueError):
            t = 0
        if e not in last_tick or t < last_tick[e]:
            count[e] = count.get(e, 0) + 1
        last_tick[e] = t
        key = (e, count[e])
        if key not in eps:
            eps[key] = dict(n=0, best=0.0, invalid=0)
            order.append(key)
        d = eps[key]
        d["n"] += 1
        s = r.get("score") or 0.0
        d["best"] = max(d["best"], float(s))
        if str(r.get("outcome", "")).startswith("INVALID"):
            d["invalid"] += 1
    lines = [f"Since your last reflection you worked on {len(order)} "
             f"situation(s)."]
    for key in order[-max_episodes:]:
        d = eps[key]
        lines.append(f"- {key[0]}: {d['n']} attempt(s), best score {d['best']:.2f}"
                     + (f", {d['invalid']} invalid" if d["invalid"] else ""))
    notes = [r.get("note", "") for r in recent if r.get("kind") == "note"
             and r.get("note")]
    if notes:
        lines.append("Your last notes to yourself:")
        lines += [f"- {n[:200]}" for n in notes[-max_notes:]]
    if not order and not notes:
        lines.append("(no attempts or notes since the last reflection)")
    return "\n".join(lines)[:max_chars]


def reflection_prompt(birth_prompt: str, summary: str, chunks: list,
                      tick: int, ticks: int) -> str:
    head = [
        "=== YOU ===", birth_prompt.strip(),
        "=== PRIVATE REFLECTION TIME ===",
        "This is your own time between sessions. There is no task, no score "
        "and no one to answer to; nothing you write here is judged. Think "
        "freely about what you have lived through: what you noticed, what "
        "puzzled you, what you believe now, what you want to try next time. "
        "Markers are not needed here.",
        f"CLOCK: reflection chunk {tick}/{ticks}",
        "=== WHAT YOU RECENTLY LIVED ===", summary,
        "=== YOUR REFLECTION (continues) ===",
    ]
    return "\n".join(head + [c[:1200] for c in chunks[-6:]]) + "\n"


def run_reflection(model, birth_prompt: str, ledger, rows: list, since: int,
                   at_episode: int, ticks: int, seed: int = 0,
                   log=print) -> list:
    """Generate up to `ticks` reflection chunks and append them to the ledger.
    Returns the rows written. Seeds derive from (reflection id, tick, seed)
    like every other chunk (batch_loop._seed_for)."""
    from .batch_loop import _seed_for
    eid = f"reflection@{at_episode:04d}"
    summary = summarize_recent(rows, since)
    chunks, written = [], []
    for t in range(1, int(ticks) + 1):
        prompt = reflection_prompt(birth_prompt, summary, chunks, t, ticks)
        out = model.batch([prompt], seeds=[_seed_for(eid, t, seed)])[0]
        chunk = (out or "").strip()
        chunks.append(chunk)
        row = dict(kind=REFLECTION_KIND, episode_id=eid, tick=t,
                   note=chunk[:2000], prompt=prompt[:24000],
                   at_episode=at_episode)
        ledger.append(row)
        written.append(row)
    log(f"[reflect {at_episode}] chunks={len(written)} "
        f"chars={sum(len(c) for c in chunks)}")
    return written
