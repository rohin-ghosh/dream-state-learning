"""
FAISS-backed episodic memory buffer for the Dream-State Learning system.

Stores agent trajectories and supports weighted retrieval by recency,
utility, and semantic similarity.
"""

from __future__ import annotations

import math
import os
import pickle
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class EpisodicEntry:
    """A single stored trajectory in episodic memory."""

    entry_id: str
    task_type: str
    success: bool
    utility_score: float
    trajectory_text: str
    embedding: np.ndarray  # shape [D]
    timestamp: int  # global step counter at insertion time
    retrieval_count: int = 0


class EpisodicMemory:
    """
    FAISS-backed episodic memory buffer.

    Entries are scored for retrieval by a weighted combination of:
        - Cosine similarity to the query (40 %)
        - Utility score stored at insertion time (30 %)
        - Recency (30 %)

    When the buffer is full, the entry with the lowest eviction score
    (utility × exp(-decay × age)) is dropped before a new one is added.
    """

    _EVICTION_DECAY: float = 0.01
    _RECENCY_DECAY: float = 0.01

    def __init__(
        self,
        capacity: int,
        embed_dim: int,
        embed_model_name: str,
        device: str = "cuda",
    ) -> None:
        self.capacity = capacity
        self.embed_dim = embed_dim
        self.device = device
        self.global_step: int = 0

        # Sentence-transformer embedding model
        self.embed_model = SentenceTransformer(embed_model_name, device=device)

        # FAISS index: inner product on L2-normalised vectors = cosine similarity
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(embed_dim)

        # Ordered list of entries; position mirrors the FAISS internal id
        self.entries: List[EpisodicEntry] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _encode(self, text: str) -> np.ndarray:
        """Return a unit-normalised embedding vector for *text*."""
        vec = self.embed_model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True
        )
        return vec.astype(np.float32)

    def _eviction_score(self, entry: EpisodicEntry) -> float:
        age = self.global_step - entry.timestamp
        return entry.utility_score * math.exp(-self._EVICTION_DECAY * age)

    def _recency_score(self, entry: EpisodicEntry) -> float:
        age = self.global_step - entry.timestamp
        return math.exp(-self._RECENCY_DECAY * age)

    def _rebuild_index(self) -> None:
        """Rebuild the FAISS index from self.entries (used after eviction)."""
        self.index.reset()
        if self.entries:
            matrix = np.stack([e.embedding for e in self.entries]).astype(np.float32)
            self.index.add(matrix)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(
        self,
        trajectory_text: str,
        task_type: str,
        success: bool,
        utility_score: float,
    ) -> str:
        """
        Encode *trajectory_text*, optionally evict the lowest-scoring entry,
        then store the new entry.

        Returns the new entry's entry_id.
        """
        self.global_step += 1
        embedding = self._encode(trajectory_text)

        # Evict if at capacity
        if len(self.entries) >= self.capacity:
            scores = [self._eviction_score(e) for e in self.entries]
            evict_idx = int(np.argmin(scores))
            self.entries.pop(evict_idx)
            self._rebuild_index()

        entry = EpisodicEntry(
            entry_id=str(uuid.uuid4()),
            task_type=task_type,
            success=success,
            utility_score=float(utility_score),
            trajectory_text=trajectory_text,
            embedding=embedding,
            timestamp=self.global_step,
        )

        self.entries.append(entry)
        self.index.add(embedding.reshape(1, -1))

        return entry.entry_id

    def retrieve(
        self,
        query: str,
        k: int = 3,
        task_type_filter: Optional[str] = None,
    ) -> List[EpisodicEntry]:
        """
        Return the top-k entries most relevant to *query*.

        Scoring:
            score = 0.4 * cosine_sim + 0.3 * utility_score + 0.3 * recency_score

        recency_score values are max-normalised across the candidate set so they
        live in [0, 1] alongside the other terms.
        """
        if not self.entries:
            return []

        query_vec = self._encode(query).reshape(1, -1)

        # Fetch up to 2 k candidates from FAISS
        n_candidates = min(2 * k, len(self.entries))
        similarities, faiss_indices = self.index.search(query_vec, n_candidates)

        similarities = similarities[0]       # shape [n_candidates]
        faiss_indices = faiss_indices[0]     # shape [n_candidates]

        # Build candidate list, applying optional task-type filter
        candidates = []
        raw_cosine = []
        for sim, idx in zip(similarities, faiss_indices):
            if idx < 0 or idx >= len(self.entries):
                continue
            entry = self.entries[idx]
            if task_type_filter is not None and entry.task_type != task_type_filter:
                continue
            candidates.append((idx, entry, float(sim)))
            raw_cosine.append(float(sim))

        if not candidates:
            return []

        # Compute raw recency scores and normalise to [0, 1]
        raw_recency = [self._recency_score(e) for _, e, _ in candidates]
        max_recency = max(raw_recency) if raw_recency else 1.0
        if max_recency == 0.0:
            max_recency = 1.0

        # Combined score and sort
        scored = []
        for (idx, entry, cosine_sim), recency in zip(candidates, raw_recency):
            combined = (
                0.4 * cosine_sim
                + 0.3 * entry.utility_score
                + 0.3 * (recency / max_recency)
            )
            scored.append((combined, idx, entry))

        scored.sort(key=lambda t: t[0], reverse=True)
        top_k = scored[:k]

        results = []
        for _, idx, entry in top_k:
            entry.retrieval_count += 1
            results.append(entry)

        return results

    def format_for_context(self, entries: List[EpisodicEntry]) -> str:
        """
        Return a human-readable context string for the given entries.

        Each entry is formatted as:
            Task [<task_type>]: <first 200 chars of trajectory_text>...
        """
        lines = []
        for entry in entries:
            snippet = entry.trajectory_text[:200]
            if len(entry.trajectory_text) > 200:
                snippet += "..."
            lines.append(f"Task [{entry.task_type}]: {snippet}")
        return "\n".join(lines)

    def save(self, path: str) -> None:
        """
        Persist the memory buffer to *path*.

        Saves two files:
            <path>.pkl  — Python pickle of entries + global_step
            <path>.faiss — FAISS index binary
        """
        pkl_path = path + ".pkl"
        faiss_path = path + ".faiss"

        with open(pkl_path, "wb") as fh:
            pickle.dump(
                {"entries": self.entries, "global_step": self.global_step},
                fh,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        faiss.write_index(self.index, faiss_path)

    def load(self, path: str) -> None:
        """
        Restore memory from a previously saved state at *path*.

        Expects:
            <path>.pkl   — produced by :meth:`save`
            <path>.faiss — produced by :meth:`save`
        """
        pkl_path = path + ".pkl"
        faiss_path = path + ".faiss"

        with open(pkl_path, "rb") as fh:
            state = pickle.load(fh)

        self.entries = state["entries"]
        self.global_step = state["global_step"]
        self.index = faiss.read_index(faiss_path)

    def __len__(self) -> int:
        return len(self.entries)
