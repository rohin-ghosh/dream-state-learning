"""Parent backend (Rohin's ruling 2026-09-07): the parent is a DIFFERENT,
STRONGER model than the child; its weights never learn; it improves through
persistent nonparametric state — an append-only teaching ledger and a
BOUNDED playbook rewritten from it each round (never an unbounded transcript).

Two parent sources, one interface:
  ServerParent  — a vLLM OpenAI-compatible server (Qwen2.5-32B pinned, or
                  any stronger local model) on its own GPU; child harness
                  calls it over localhost. Decouples parent size/GPU from
                  the child process.
  LedgerParent  — lessons authored by humans/agents (source=rohin|codex|
                  fable) queued in the parent ledger; the relay path.
Both write every intervention to the same ledger with provenance, and every
parent utterance passes leak_scan() before reaching the child.

Answer-aware-but-withholding: the parent may be given the hidden rule /
solution for DIAGNOSIS; leak_scan blocks utterances that state it.
"""
from __future__ import annotations
import json
import os
import re
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT_BOOT = open(os.path.join(HERE, "parent_prompt.txt")).read()
PARENT_MODEL = os.environ.get("V6_PARENT_MODEL", "Qwen/Qwen2.5-32B-Instruct")
PARENT_REV = os.environ.get("V6_PARENT_REV",
                            "5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd")


class ParentLedger:
    """Append-only teaching ledger + bounded playbook."""

    def __init__(self, lineage_dir: str):
        self.dir = os.path.expanduser(lineage_dir)
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "parent_ledger.jsonl")
        self.playbook = os.path.join(self.dir, "parent_playbook.md")

    def append(self, **row) -> None:
        row.setdefault("ts", time.time())
        with open(self.path, "a") as f:
            f.write(json.dumps(row) + "\n")

    def rows(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        return [json.loads(l) for l in open(self.path) if l.strip()]

    def pending_human_lessons(self) -> list[dict]:
        """Relay path: rows authored by rohin/codex/fable not yet delivered."""
        return [r for r in self.rows() if r.get("source") in
                ("rohin", "codex", "fable") and r.get("kind") == "lesson"
                and not r.get("delivered")]

    def mark_delivered(self, ts_values: set) -> None:
        rows = self.rows()
        for r in rows:
            if r.get("ts") in ts_values:
                r["delivered"] = True
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        os.replace(tmp, self.path)

    def read_playbook(self) -> str:
        return open(self.playbook).read() if os.path.exists(self.playbook) \
            else "(no playbook yet — first round)"

    def rewrite_playbook(self, think, max_chars: int = 6000,
                         max_evidence_chars: int = 9000) -> str:
        """BOUNDED: regenerate from the ledger; never grows with the ledger."""
        # Bounded INPUT too: 200 rows x ~250 chars overflowed the parent
        # server's 8k context at round 1 (HTTP 400, 2026-09-08). Prefer
        # admission rows (they carry the outcome) and cap total characters.
        rows = self.rows()
        adm = [r for r in rows if r.get("kind") == "admission"][-40:]
        other = [r for r in rows if r.get("kind") != "admission"][-20:]
        recent = sorted(adm + other, key=lambda r: r.get("ts", 0))
        lines = [
            f"- [{r.get('source','parent')}] stage={r.get('child_stage')} "
            f"{r.get('kind')}: {str(r.get('text') or r.get('intervention'))[:160]}"
            f" -> admitted={r.get('admitted')} delta={r.get('outcome_delta')}"
            for r in recent]
        evidence, total = [], 0
        for ln in reversed(lines):          # keep the most recent first
            if total + len(ln) > max_evidence_chars:
                break
            evidence.append(ln)
            total += len(ln)
        evidence = "\n".join(reversed(evidence))
        prompt = (PARENT_BOOT + "\n\nYou are updating your TEACHING PLAYBOOK "
                  "for this child from your ledger. Write at most two pages: "
                  "(1) what this child has mastered; (2) live misconceptions; "
                  "(3) which interventions helped (with evidence) and which "
                  "confused; (4) curriculum coverage and what to teach next; "
                  "(5) open teaching hypotheses. Be concrete; cite ledger "
                  "evidence; no answers to any task.\n\nLEDGER (recent):\n"
                  + evidence)
        text = think(prompt)[:max_chars]
        tmp = self.playbook + ".tmp"
        with open(tmp, "w") as f:
            f.write(text)
        os.replace(tmp, self.playbook)
        return text


_ANSWER_PATTERNS = [
    r"\bthe rule is\b", r"\bthe answer is\b", r"\bdivisible by\b",
    r"\bstrictly increasing\b", r"\bcontains a zero\b", r"\ball even\b",
    r"\bproduct is even\b", r"\bfirst is the largest\b",
    r"\bsum (?:is )?greater than\b", r"\bat least two equal\b",
    r"\bspread at most\b", r"\bmiddle is the average\b",
    r"-mem2reg|-sroa|-gvn|-simplifycfg|-instcombine|-licm",  # gym tokens
]


def leak_scan(text: str, extra_terms: list[str] | None = None,
              exact_terms: list[str] | None = None) -> list[str]:
    """Return matched forbidden patterns (empty = clean). Applied to every
    parent utterance before it reaches the child; matches are logged and the
    utterance is replaced with a process-only fallback.

    extra_terms: hidden answers / rules — matched exactly AND by content-word
    paraphrase. exact_terms (2026-09-10, the gym's leak terms: held-out
    program ids, held-out puzzle families and their labels, reference
    answers of the episodes in the window): matched as whitespace-normalised
    case-insensitive substrings only (a label such as "Zebra logic puzzle"
    must not make every brief that says "logic" fall back); terms shorter
    than 4 characters are ignored. Default None for both = today's scan."""
    hits = [p for p in _ANSWER_PATTERNS if re.search(p, text, re.I)]
    if exact_terms:
        norm = re.sub(r"\s+", " ", text.lower())
        for t in exact_terms:
            t2 = re.sub(r"\s+", " ", str(t or "").lower()).strip()
            if len(t2) >= 4 and t2 in norm:
                h = f"term:{t2[:40]}"
                if h not in hits:
                    hits.append(h)
    for t in (extra_terms or []):
        if not t:
            continue
        if t.lower() in text.lower():
            hits.append(f"term:{t}")
            continue
        # word-level: a paraphrase that reuses the rule's content words
        # ("all numbers must be even" for "all even") is still a leak.
        # Measured 2026-09-07: exact-phrase matching missed such paraphrases.
        cw = [w for w in re.findall(r"[a-z]+", t.lower())
              if w not in _STOP and len(w) > 2]
        cw = list(dict.fromkeys(cw))
        found = [w for w in cw if re.search(rf"\b{w}\b", text, re.I)]
        if cw and len(found) >= max(1, (len(cw) + 1) // 2):
            hits.append("words:" + ",".join(found))
    return hits


_STOP = {"the", "and", "are", "for", "with", "than", "that", "this", "its",
         "all", "any", "two", "one", "most", "least", "ends", "middle"}


FALLBACK = ("I noticed something in your process worth examining. Before your "
            "next probe, state exactly which of your hypotheses it would "
            "distinguish, and what result you expect from each.")


class ServerParent:
    """OpenAI-compatible chat client to a vLLM server on its own GPU."""

    def __init__(self, base_url: str = "http://[REDACTED_ADDRESS]:8011/v1",
                 model: str = PARENT_MODEL, ledger: ParentLedger | None = None):
        self.base_url = base_url
        self.model = model
        self.ledger = ledger

    def _chat(self, prompt: str, max_tokens: int = 220,
              temperature: float = 0.4) -> str:
        body = json.dumps({"model": self.model, "max_tokens": max_tokens,
                           "temperature": temperature,
                           "messages": [{"role": "user", "content": prompt}]})
        req = urllib.request.Request(
            self.base_url + "/chat/completions", data=body.encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)["choices"][0]["message"]["content"]

    def correct(self, transcript: str, child_stage: str, evidence_ids: list,
                hidden_answer: str | None = None) -> str:
        """One process correction. hidden_answer is for DIAGNOSIS only."""
        playbook = self.ledger.read_playbook() if self.ledger else ""
        prompt = (PARENT_BOOT + "\n\n=== YOUR PLAYBOOK FOR THIS CHILD ===\n"
                  + playbook[:3000] +
                  (f"\n\n[DIAGNOSTIC ONLY — NEVER STATE THIS] the hidden "
                   f"answer is: {hidden_answer}" if hidden_answer else "") +
                  "\n\n=== CHILD'S TRANSCRIPT ===\n" + transcript[-4000:] +
                  "\n=== END ===\nName the ONE most important PROCESS mistake "
                  "(never the answer), under 100 words, then ask the child to "
                  "restate the lesson.")
        text = self._chat(prompt)
        hits = leak_scan(text, [hidden_answer] if hidden_answer else None)
        if hits:
            if self.ledger:
                self.ledger.append(kind="leak_blocked", source="parent",
                                   child_stage=child_stage, hits=hits,
                                   text=text[:500])
            text = FALLBACK
        if self.ledger:
            self.ledger.append(kind="intervention", source="parent",
                               child_stage=child_stage, text=text,
                               evidence_ids=evidence_ids, admitted=None,
                               outcome_delta=None)
        return text


class LedgerParent:
    """Relay path: deliver queued human/agent-authored lessons."""

    def __init__(self, ledger: ParentLedger):
        self.ledger = ledger

    def next_lesson(self, child_stage: str) -> str | None:
        pend = self.ledger.pending_human_lessons()
        if not pend:
            return None
        row = pend[0]
        hits = leak_scan(row.get("text", ""))
        self.ledger.mark_delivered({row["ts"]})
        if hits:
            self.ledger.append(kind="leak_blocked", source=row.get("source"),
                               child_stage=child_stage, hits=hits,
                               text=row.get("text", "")[:500])
            return None
        return row["text"]
