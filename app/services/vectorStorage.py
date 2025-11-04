import threading
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np


class FaissVectorStore:
    def __init__(self, indexPath: Path):
        self.indexPath = indexPath
        self.lockInstance = threading.RLock()
        self.indexInstance: faiss.IndexIDMap | None = None
        self.dimension: int | None = None
        self.loadIndex()

    def loadIndex(self) -> None:
        if self.indexPath.exists():
            indexObject = faiss.read_index(str(self.indexPath))
            if not isinstance(indexObject, faiss.IndexIDMap):
                indexObject = faiss.IndexIDMap(indexObject)
            self.indexInstance = indexObject
            self.dimension = indexObject.d

    def ensureIndex(self, dimension: int) -> None:
        if self.indexInstance is not None:
            return
        baseIndex = faiss.IndexFlatIP(dimension)
        self.indexInstance = faiss.IndexIDMap(baseIndex)
        self.dimension = dimension

    def add(self, ids: np.ndarray, vectors: np.ndarray) -> None:
        if vectors.ndim != 2:
            raise ValueError("Vectors must be a 2D array.")
        idsArray = np.asarray(ids, dtype="int64")
        vectorsArray = np.atleast_2d(np.asarray(vectors, dtype="float32"))
        with self.lockInstance:
            self.ensureIndex(vectorsArray.shape[1])
            if self.indexInstance is None:
                raise RuntimeError("Index failed to initialize.")
            self.indexInstance.add_with_ids(vectorsArray, idsArray)
            self.persist()

    def search(self, vector: np.ndarray, topK: int) -> List[Tuple[int, float]]:
        with self.lockInstance:
            if self.indexInstance is None or self.indexInstance.ntotal == 0:
                return []
            vectorArray = np.asarray(vector, dtype="float32").reshape(1, -1)
            distances, ids = self.indexInstance.search(vectorArray, topK)
            results: List[Tuple[int, float]] = []
            for documentId, score in zip(ids[0], distances[0]):
                if documentId == -1:
                    continue
                results.append((int(documentId), float(score)))
            return results

    def persist(self) -> None:
        if self.indexInstance is None:
            return
        self.indexPath.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.indexInstance, str(self.indexPath))

