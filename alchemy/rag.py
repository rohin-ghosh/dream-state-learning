"""Naive-RAG arm: TF-IDF retrieval over memory lines (numpy only).
Honest-tuning hook: k is a parameter, swept for the baseline's benefit.
(A-Mem lands later as the strong published baseline.)"""

from __future__ import annotations

import re
from collections import Counter

import numpy as np


def _toks(s: str) -> list:
    return re.findall(r"[a-z0-9-]+", s.lower())


class TfidfIndex:
    def __init__(self, lines: list):
        self.lines = lines
        self.doc_toks = [Counter(_toks(l)) for l in lines]
        df = Counter()
        for d in self.doc_toks:
            df.update(d.keys())
        n = max(len(lines), 1)
        self.idf = {t: np.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
        self.norms = np.array([
            np.sqrt(sum((cnt * self.idf.get(t, 0.0)) ** 2
                        for t, cnt in d.items())) or 1.0
            for d in self.doc_toks])

    def topk(self, query: str, k: int = 12) -> list:
        q = Counter(_toks(query))
        qw = {t: c * self.idf.get(t, 0.0) for t, c in q.items()}
        scores = np.array([
            sum(qw[t] * d.get(t, 0) * self.idf.get(t, 0.0) for t in qw)
            for d in self.doc_toks]) / self.norms
        order = np.argsort(-scores)[:k]
        return [self.lines[i] for i in order if scores[i] > 0]


def memory_block(index: TfidfIndex, query: str, k: int) -> str:
    hits = index.topk(query, k)
    if not hits:
        return "(no relevant memories)"
    return "\n".join(f"- {h}" for h in hits)
