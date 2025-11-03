"""Integration tests for the Healthcare Knowledge Assistant API."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import dependencies
from app.config import Settings
from app.dependencies import get_app_settings, get_rag_service
from app.main import app
from app.services import rag_service


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Return a TestClient wired to temporary storage and lightweight embeddings."""

    dependencies.get_rag_service.cache_clear()

    settings = Settings(api_key="test-key", data_dir=tmp_path / "data")

    def override_settings() -> Settings:
        return settings

    def fake_embed_text(text: str) -> np.ndarray:
        vec = np.array([float(len(text)), float(sum(ord(c) for c in text) % 997)], dtype="float32")
        norm = np.linalg.norm(vec)
        if norm == 0:
            return np.array([1.0, 0.0], dtype="float32")
        return vec / norm

    monkeypatch.setattr(rag_service, "embed_text", fake_embed_text)

    rag = rag_service.RAGService(settings)
    monkeypatch.setattr(rag.translation_service, "translate", lambda text, **_: text)

    def override_rag_service() -> rag_service.RAGService:
        return rag

    app.dependency_overrides[get_app_settings] = override_settings
    app.dependency_overrides[get_rag_service] = override_rag_service

    yield TestClient(app)

    app.dependency_overrides.clear()
    dependencies.get_rag_service.cache_clear()


def test_ingest_retrieve_and_generate(client: TestClient) -> None:
    payload = "This guideline covers Type 2 diabetes management with emphasis on lifestyle."
    headers = {"X-API-Key": "test-key"}

    ingest_response = client.post(
        "/ingest",
        headers=headers,
        files={"file": ("guideline.txt", payload, "text/plain")},
    )

    assert ingest_response.status_code == 200
    document_id = ingest_response.json()["document_id"]
    assert document_id == 1

    retrieve_response = client.post(
        "/retrieve",
        headers=headers,
        json={"query": "Type 2 diabetes recommendations", "top_k": 3},
    )

    assert retrieve_response.status_code == 200
    body = retrieve_response.json()
    assert body["query_language"] == "en"
    assert body["matches"]
    assert body["matches"][0]["document_id"] == document_id

    generate_response = client.post(
        "/generate",
        headers=headers,
        json={"query": "Type 2 diabetes recommendations", "top_k": 3},
    )
    assert generate_response.status_code == 200
    generation = generate_response.json()
    assert generation["query_language"] == "en"
    assert generation["output_language"] == "en"
    assert generation["sources"]
    assert "Type 2 diabetes" in generation["response"]

