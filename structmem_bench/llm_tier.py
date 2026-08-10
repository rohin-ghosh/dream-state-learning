"""LLM-in-the-loop tier (M3) — GPU/API-ready scaffold.

Bridges the abstract benchmark to a real agent: an LLM plays crafting-sim episodes
with a pluggable MEMORY BACKEND, then we probe the memory for retained STRUCTURE
(dependency edges) vs DETAIL and score against the sim's ground-truth DAG.

This module is a SCAFFOLD: the plumbing (episode loop, probing, scoring) is CPU-
testable via MockLLM; the real backend (HF transformers) needs a GPU and is guarded
so importing this file never requires torch. Run the real tier on the cluster.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Optional

# NOTE: intentionally NO top-level torch/transformers import — keeps CPU import clean.


# ------------------------------- interfaces -------------------------------
class LLM(Protocol):
    def generate(self, prompt: str) -> str: ...


class MemoryBackend(Protocol):
    """A memory a method under test provides. write() during/after episodes;
    query() to retrieve; probe_fact() returns whether a specific fact/edge is
    recoverable (for scoring against ground truth)."""
    def write(self, episode_text: str, meta: dict) -> None: ...
    def query(self, cue: str, budget_tokens: int) -> str: ...
    def probe_fact(self, fact: str) -> bool: ...


# ------------------------------- backends -------------------------------
@dataclass
class NoMemory:
    def write(self, episode_text, meta): pass
    def query(self, cue, budget_tokens): return ""
    def probe_fact(self, fact): return False


@dataclass
class FullContextMemory:
    """Truncated-recency context at a fixed token budget (the 'just stuff the window'
    baseline). Stores raw episode text; query returns the most recent within budget."""
    buffer: list = field(default_factory=list)
    def write(self, episode_text, meta): self.buffer.append(episode_text)
    def query(self, cue, budget_tokens):
        out, used = [], 0
        for t in reversed(self.buffer):
            used += len(t.split())
            if used > budget_tokens: break
            out.append(t)
        return "\n".join(reversed(out))
    def probe_fact(self, fact):
        return any(fact.lower() in t.lower() for t in self.buffer)


@dataclass
class RAGMemory:
    """Embedding-retrieval baseline. Requires a sentence embedder at run time; stubbed
    to substring match if none provided (keeps CPU tests running)."""
    embedder: Optional[object] = None
    store: list = field(default_factory=list)
    def write(self, episode_text, meta): self.store.append(episode_text)
    def query(self, cue, budget_tokens):
        # real impl: embed cue, top-k by cosine within budget. Stub: substring.
        hits = [t for t in self.store if any(w in t.lower() for w in cue.lower().split())]
        return "\n".join(hits[:5])
    def probe_fact(self, fact):
        return any(fact.lower() in t.lower() for t in self.store)


# Parametric backend (ATLAS-style + value-weighted write) lives here for the real
# tier — imports torch lazily so this module stays CPU-importable.
def make_parametric_backend(*args, **kwargs):
    """Factory for the parametric fast-weight memory (GPU). Deferred import."""
    raise NotImplementedError(
        "Parametric backend requires the GPU tier: import torch + the ATLAS-style "
        "MLP memory here. Scaffolded intentionally — run on cluster.")


# ------------------------------- mock LLM -------------------------------
@dataclass
class MockLLM:
    """Deterministic stand-in so the episode loop + scoring are CPU-testable without
    a GPU. Echoes a canned action; NOT a real policy."""
    def generate(self, prompt: str) -> str:
        return "THOUGHT: (mock)\nACTION: inspect"


# ------------------------------- runner -------------------------------
@dataclass
class LLMTierResult:
    n_episodes: int
    structural_recoverable: float   # fraction of ground-truth edges probe-recoverable
    detail_recoverable: float       # fraction of ground-truth details probe-recoverable
    diagonal: float
    backend: str


def run_llm_tier(llm: LLM, backend: MemoryBackend, episodes: list,
                 ground_truth_edges: list, ground_truth_details: list,
                 budget_tokens: int = 512) -> LLMTierResult:
    """Play episodes writing to `backend`, then probe recoverability of ground-truth
    structural edges vs episodic details. Backend-agnostic; works with the mock LLM
    for plumbing tests and a real LLM on GPU.

    episodes: list of dict {text, meta}. ground_truth_edges/details: list[str] of the
    canonical fact strings the sim knows are structural vs detail for these episodes.
    """
    for ep in episodes:
        # (real tier: run the ReAct loop with llm + backend.query for context)
        backend.write(ep["text"], ep.get("meta", {}))

    def frac(items):
        return sum(1 for f in items if backend.probe_fact(f)) / max(1, len(items))

    sr = frac(ground_truth_edges)
    dr = frac(ground_truth_details)
    return LLMTierResult(
        n_episodes=len(episodes), structural_recoverable=sr,
        detail_recoverable=dr, diagonal=sr - dr,
        backend=type(backend).__name__)


# quick CPU self-test of the plumbing (no GPU): mock episodes, full-context backend
def _selftest():
    eps = [{"text": "to craft planks you need wood. the wood was red.", "meta": {}}]
    edges = ["planks you need wood"]           # structural
    details = ["the wood was red"]             # detail
    r = run_llm_tier(MockLLM(), FullContextMemory(), eps, edges, details)
    assert r.structural_recoverable == 1.0 and r.detail_recoverable == 1.0
    r2 = run_llm_tier(MockLLM(), NoMemory(), eps, edges, details)
    assert r2.structural_recoverable == 0.0
    return "llm_tier plumbing OK"


if __name__ == "__main__":
    print(_selftest())
