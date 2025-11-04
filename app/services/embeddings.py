import threading
from typing import Iterable
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import getSettings

modelInstance: SentenceTransformer | None = None
modelLock = threading.Lock()

def loadModel() -> SentenceTransformer:
    global modelInstance
    if modelInstance is None:
        with modelLock:
            if modelInstance is None:
                settings = getSettings()
                modelInstance = SentenceTransformer(settings.embeddingModelName)
    return modelInstance

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