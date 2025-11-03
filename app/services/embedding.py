"""Sentence embedding utilities."""

from __future__ import annotations

import threading
from typing import Iterable, List

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings

_model: SentenceTransformer | None = None
_lock = threading.Lock()


def _load_model() -> SentenceTransformer:
    """Lazy-load and memoize the sentence transformer model."""

    global _model

    if _model is None:
        with _lock:
            if _model is None:
                settings = get_settings()
                _model = SentenceTransformer(settings.embedding_model_name)
    return _model


def embed_texts(texts: Iterable[str]) -> np.ndarray:
    """Embed a sequence of texts into L2-normalized vectors."""

    model = _load_model()
    embeddings = model.encode(
        list(texts),
        convert_to_numpy=True,
        normalize_embeddings=True,
        device=None,
        show_progress_bar=False,
    )
    # Ensure float32 dtype for FAISS compatibility.
    return np.asarray(embeddings, dtype="float32")


def embed_text(text: str) -> np.ndarray:
    """Helper for embedding a single string."""

    return embed_texts([text])[0]

