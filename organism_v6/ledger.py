"""v6 append-only experience ledger (the surprise ledger).

One JSON line per event; harness-written, never edited. Retrieval is
verbatim keyword/pass-name matching (the entity-keyed lesson from gold
control) — generation never substitutes for lookup.
"""
from __future__ import annotations
import json
import os
import re

_TOKEN = re.compile(r"[a-zA-Z_][a-zA-Z0-9_-]{2,}")


class Ledger:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def append(self, rec: dict) -> dict:
        with open(self.path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        return dict(rec)

    def rows(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def recall(self, query: str, k: int = 6) -> list[str]:
        """Verbatim keyword-overlap retrieval over action/outcome/note text."""
        q = set(t.lower() for t in _TOKEN.findall(query))
        scored = []
        for r in self.rows():
            text = " ".join(str(r.get(f, "")) for f in
                            ("action", "outcome", "note", "principle", "focus"))
            toks = set(t.lower() for t in _TOKEN.findall(text))
            ov = len(q & toks)
            if ov:
                scored.append((ov, r))
        scored.sort(key=lambda x: -x[0])
        out = []
        for _, r in scored[:k]:
            kind = r.get("kind", "event")
            ep = r.get("episode_id", "?")
            if kind == "act":
                out.append(f"[{ep}] tried {r['action']} -> {r['outcome']}"
                           f" (predicted {r.get('prediction')}, "
                           f"surprise {r.get('surprise'):+.3f})"
                           if r.get("surprise") is not None else
                           f"[{ep}] tried {r['action']} -> {r['outcome']}")
            else:
                out.append(f"[{ep}] {r.get('note') or r.get('principle') or ''}")
        return out
