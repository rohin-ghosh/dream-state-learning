"""
Semantic memory store for the Dream-State Learning system.

Stores LLM-distilled procedure summaries indexed by task type and subtask,
backed by SQLite for persistence and FAISS for fast vector retrieval.
"""

from __future__ import annotations

import io
import json
import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


@dataclass
class SemanticEntry:
    entry_id: str
    task_type: str
    subtask_name: str
    procedure_text: str
    embedding: bytes           # np.ndarray serialized with np.save to bytes
    source_episode_ids: list[str]
    confidence: float
    created_at: float          # unix timestamp
    update_count: int = 0


def _ndarray_to_bytes(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.save(buf, arr)
    return buf.getvalue()


def _bytes_to_ndarray(data: bytes) -> np.ndarray:
    buf = io.BytesIO(data)
    return np.load(buf)


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS semantic_entries (
    entry_id            TEXT PRIMARY KEY,
    task_type           TEXT NOT NULL,
    subtask_name        TEXT NOT NULL,
    procedure_text      TEXT NOT NULL,
    embedding           BLOB NOT NULL,
    source_episode_ids  TEXT NOT NULL,   -- JSON-encoded list[str]
    confidence          REAL NOT NULL,
    created_at          REAL NOT NULL,
    update_count        INTEGER NOT NULL DEFAULT 0,
    UNIQUE (task_type, subtask_name)
)
"""


class SemanticMemory:
    """SQLite-backed semantic memory with in-memory FAISS cosine index."""

    def __init__(
        self,
        db_path: str,
        embed_model_name: str,
        device: str = "cuda",
    ) -> None:
        self.db_path = db_path
        self.device = device

        logger.info("Loading sentence-transformer model: %s on %s", embed_model_name, device)
        self.embed_model = SentenceTransformer(embed_model_name, device=device)
        self._embed_dim: int = self.embed_model.get_sentence_embedding_dimension()

        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_CREATE_TABLE_SQL)
        self._conn.commit()

        # FAISS inner-product index over L2-normalised vectors == cosine similarity
        self._index = faiss.IndexFlatIP(self._embed_dim)
        # Mapping: FAISS positional index -> entry_id
        self._index_id_map: list[str] = []

        self._rebuild_index()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _encode(self, text: str) -> np.ndarray:
        vec = self.embed_model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return vec.astype(np.float32)

    def _rebuild_index(self) -> None:
        """Reload FAISS index from current DB contents."""
        self._index.reset()
        self._index_id_map = []

        rows = self._conn.execute(
            "SELECT entry_id, embedding FROM semantic_entries ORDER BY rowid"
        ).fetchall()

        if not rows:
            return

        vectors = []
        for row in rows:
            vec = _bytes_to_ndarray(row["embedding"]).astype(np.float32)
            vectors.append(vec)
            self._index_id_map.append(row["entry_id"])

        matrix = np.vstack(vectors)
        self._index.add(matrix)

    def _row_to_entry(self, row: sqlite3.Row) -> SemanticEntry:
        return SemanticEntry(
            entry_id=row["entry_id"],
            task_type=row["task_type"],
            subtask_name=row["subtask_name"],
            procedure_text=row["procedure_text"],
            embedding=row["embedding"],
            source_episode_ids=json.loads(row["source_episode_ids"]),
            confidence=row["confidence"],
            created_at=row["created_at"],
            update_count=row["update_count"],
        )

    def _add_vector_to_index(self, entry_id: str, vec: np.ndarray) -> None:
        self._index.add(vec.reshape(1, -1))
        self._index_id_map.append(entry_id)

    def _replace_vector_in_index(self, entry_id: str, vec: np.ndarray) -> None:
        """Replace the vector for an existing entry by rebuilding the index."""
        # Find the positional slot and update; simplest correct approach is rebuild.
        self._rebuild_index()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_or_update(
        self,
        task_type: str,
        subtask_name: str,
        procedure_text: str,
        source_episode_ids: list[str],
        confidence: float,
    ) -> str:
        existing = self._conn.execute(
            "SELECT * FROM semantic_entries WHERE task_type=? AND subtask_name=?",
            (task_type, subtask_name),
        ).fetchone()

        vec = self._encode(procedure_text)
        emb_bytes = _ndarray_to_bytes(vec)

        if existing is not None:
            if confidence < existing["confidence"]:
                logger.debug(
                    "Skipping update for (%s, %s): new confidence %.3f < existing %.3f",
                    task_type,
                    subtask_name,
                    confidence,
                    existing["confidence"],
                )
                return existing["entry_id"]

            merged_ids = list(
                dict.fromkeys(
                    json.loads(existing["source_episode_ids"]) + source_episode_ids
                )
            )
            self._conn.execute(
                """
                UPDATE semantic_entries
                SET procedure_text=?, embedding=?, source_episode_ids=?,
                    confidence=?, update_count=update_count+1
                WHERE entry_id=?
                """,
                (
                    procedure_text,
                    emb_bytes,
                    json.dumps(merged_ids),
                    confidence,
                    existing["entry_id"],
                ),
            )
            self._conn.commit()
            self._replace_vector_in_index(existing["entry_id"], vec)
            logger.debug("Updated semantic entry %s", existing["entry_id"])
            return existing["entry_id"]

        entry_id = str(uuid.uuid4())
        self._conn.execute(
            """
            INSERT INTO semantic_entries
                (entry_id, task_type, subtask_name, procedure_text, embedding,
                 source_episode_ids, confidence, created_at, update_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                entry_id,
                task_type,
                subtask_name,
                procedure_text,
                emb_bytes,
                json.dumps(source_episode_ids),
                confidence,
                time.time(),
            ),
        )
        self._conn.commit()
        self._add_vector_to_index(entry_id, vec)
        logger.debug("Inserted new semantic entry %s", entry_id)
        return entry_id

    def retrieve(
        self,
        query: str,
        k: int = 3,
        task_type_filter: Optional[str] = None,
    ) -> list[SemanticEntry]:
        if self._index.ntotal == 0:
            return []

        query_vec = self._encode(query).reshape(1, -1)

        search_k = min(self._index.ntotal, max(k * 10, 50)) if task_type_filter else k
        distances, indices = self._index.search(query_vec, search_k)

        results: list[SemanticEntry] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._index_id_map):
                continue
            entry_id = self._index_id_map[idx]
            row = self._conn.execute(
                "SELECT * FROM semantic_entries WHERE entry_id=?", (entry_id,)
            ).fetchone()
            if row is None:
                continue
            if task_type_filter and row["task_type"] != task_type_filter:
                continue
            results.append(self._row_to_entry(row))
            if len(results) >= k:
                break

        return results

    def distill_from_episodes(
        self,
        llm_fn: Callable[[str], str],
        episodes: list,
        task_type: str,
    ) -> list[SemanticEntry]:
        """
        Distil procedural summaries from a list of EpisodicEntry objects.

        Parameters
        ----------
        llm_fn:
            Callable that accepts a prompt string and returns a response string.
        episodes:
            List of EpisodicEntry objects (must expose .to_dict() or be dataclasses).
        task_type:
            The task category being distilled.

        Returns
        -------
        List of SemanticEntry objects that were created or updated.
        """
        if not episodes:
            logger.warning("distill_from_episodes called with empty episodes list")
            return []

        # Summarise episodes into text for the prompt
        episode_lines: list[str] = []
        for i, ep in enumerate(episodes, start=1):
            if hasattr(ep, "to_dict"):
                ep_dict = ep.to_dict()
            elif hasattr(ep, "__dataclass_fields__"):
                import dataclasses
                ep_dict = dataclasses.asdict(ep)
            else:
                ep_dict = vars(ep)
            episode_lines.append(f"Episode {i}: {json.dumps(ep_dict, default=str)}")

        episodes_text = "\n".join(episode_lines)

        prompt = (
            f"Given these successful task episodes for task type [{task_type}],\n"
            "extract 2-3 reusable procedural summaries. For each, provide:\n"
            "- subtask_name: brief label\n"
            "- procedure: step-by-step action template\n"
            "Format as JSON list.\n\n"
            f"Episodes:\n{episodes_text}\n\n"
            "Respond ONLY with a JSON array like:\n"
            '[{"subtask_name": "...", "procedure": "..."}, ...]'
        )

        logger.debug("Calling LLM for distillation of task_type=%s", task_type)
        raw_response = llm_fn(prompt)

        try:
            # Strip markdown code fences if present
            clean = raw_response.strip()
            if clean.startswith("```"):
                clean = clean.split("```", 2)[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.rsplit("```", 1)[0]
            summaries = json.loads(clean.strip())
        except (json.JSONDecodeError, IndexError) as exc:
            logger.error("Failed to parse LLM distillation response: %s", exc)
            logger.debug("Raw LLM response: %s", raw_response)
            return []

        source_ids = []
        for ep in episodes:
            ep_id = getattr(ep, "episode_id", None) or getattr(ep, "id", None)
            if ep_id:
                source_ids.append(str(ep_id))

        created_or_updated: list[SemanticEntry] = []
        for item in summaries:
            subtask_name = item.get("subtask_name", "").strip()
            procedure_text = item.get("procedure", "").strip()
            if not subtask_name or not procedure_text:
                logger.warning("Skipping distilled item with missing fields: %s", item)
                continue

            entry_id = self.add_or_update(
                task_type=task_type,
                subtask_name=subtask_name,
                procedure_text=procedure_text,
                source_episode_ids=source_ids,
                confidence=0.8,
            )
            row = self._conn.execute(
                "SELECT * FROM semantic_entries WHERE entry_id=?", (entry_id,)
            ).fetchone()
            if row:
                created_or_updated.append(self._row_to_entry(row))

        return created_or_updated

    def format_for_context(self, entries: list[SemanticEntry]) -> str:
        """Return a human-readable string for LLM context injection."""
        lines = [
            f"[{entry.subtask_name}]: {entry.procedure_text}" for entry in entries
        ]
        return "\n".join(lines)

    def get_all_by_type(self, task_type: str) -> list[SemanticEntry]:
        rows = self._conn.execute(
            "SELECT * FROM semantic_entries WHERE task_type=? ORDER BY created_at",
            (task_type,),
        ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def save_index(self, path: str) -> None:
        """Persist the FAISS index to disk."""
        faiss.write_index(self._index, path)
        # Also save the id map alongside
        id_map_path = path + ".ids.json"
        with open(id_map_path, "w", encoding="utf-8") as fh:
            json.dump(self._index_id_map, fh)
        logger.info("FAISS index saved to %s (id map: %s)", path, id_map_path)

    def load_index(self, path: str) -> None:
        """Load a previously saved FAISS index from disk."""
        self._index = faiss.read_index(path)
        id_map_path = path + ".ids.json"
        with open(id_map_path, "r", encoding="utf-8") as fh:
            self._index_id_map = json.load(fh)
        logger.info(
            "FAISS index loaded from %s (%d vectors)", path, self._index.ntotal
        )

    def close(self) -> None:
        """Close the SQLite connection."""
        self._conn.close()

    def __enter__(self) -> "SemanticMemory":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
