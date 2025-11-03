"""Simple persistent FAISS vector store."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np


class FaissVectorStore:
    """Thread-safe wrapper around a disk-backed FAISS index."""

    def __init__(self, index_path: Path):
        self.index_path = index_path
        self._lock = threading.RLock()
        self._index: faiss.IndexIDMap | None = None
        self._dimension: int | None = None
        self._load()

    def _load(self) -> None:
        if self.index_path.exists():
            index = faiss.read_index(str(self.index_path))
            if not isinstance(index, faiss.IndexIDMap):
                index = faiss.IndexIDMap(index)
            self._index = index
            self._dimension = index.d

    def _ensure_index(self, dimension: int) -> None:
        if self._index is not None:
            return
        base_index = faiss.IndexFlatIP(dimension)
        self._index = faiss.IndexIDMap(base_index)
        self._dimension = dimension

    def add(self, ids: np.ndarray, vectors: np.ndarray) -> None:
        """Add vectors and persist the updated index."""

        if vectors.ndim != 2:
            raise ValueError("Vectors must be a 2D array.")

        ids = np.asarray(ids, dtype="int64")
        vectors = np.atleast_2d(np.asarray(vectors, dtype="float32"))

        with self._lock:
            self._ensure_index(vectors.shape[1])
            assert self._index is not None  # For type-checkers
            self._index.add_with_ids(vectors, ids)
            self._persist()

    def search(self, vector: np.ndarray, top_k: int) -> List[Tuple[int, float]]:
        """Return (document_id, score) pairs for the closest vectors."""

        with self._lock:
            if self._index is None or self._index.ntotal == 0:
                return []

            vector = np.asarray(vector, dtype="float32").reshape(1, -1)
            distances, ids = self._index.search(vector, top_k)
            results: List[Tuple[int, float]] = []
            for doc_id, score in zip(ids[0], distances[0]):
                if doc_id == -1:
                    continue
                results.append((int(doc_id), float(score)))
            return results

    def _persist(self) -> None:
        assert self._index is not None
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self.index_path))
