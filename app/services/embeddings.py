import numpy as np
from functools import lru_cache
from typing import Iterable
from sentence_transformers import SentenceTransformer
from app.config import getSettings

@lru_cache(maxsize=1)
def loadModel() -> SentenceTransformer:
    settings = getSettings()
    return SentenceTransformer(settings.embeddingModelName)

def embedTexts(texts: Iterable[str]) -> np.ndarray:
    model = loadModel()
    embeddings = model.encode(
        list(texts),
        convert_to_numpy=True,
        normalize_embeddings=True,
        device=None,
        show_progress_bar=False,
    )
    return np.asarray(embeddings, dtype="float32")

def embedText(text: str) -> np.ndarray:
    return embedTexts([text])[0]