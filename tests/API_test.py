import pytest, numpy as np
from pathlib import Path
from typing import Iterator
from fastapi.testclient import TestClient
from app import dependencies
from app.config import Settings
from app.dependencies import getAppSettings, getRagService
from app.main import app
from app.services import ragService

@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    dependencies.getRagService.cache_clear()

    settings = Settings(apiKey="test-key", dataDir=tmp_path / "data")

    def overrideSettings() -> Settings:
        return settings

    def fakeEmbedText(text: str) -> np.ndarray:
        vector = np.array([float(len(text)), float(sum(ord(char) for char in text) % 997)], dtype="float32")
        normValue = np.linalg.norm(vector)
        if normValue == 0:
            return np.array([1.0, 0.0], dtype="float32")
        return vector / normValue

    monkeypatch.setattr(ragService, "embedText", fakeEmbedText)

    ragInstance = ragService.RAGService(settings)
    monkeypatch.setattr(ragInstance.translationService, "translate", lambda text, **_: text)

    def overrideRagService() -> ragService.RAGService:
        return ragInstance

    app.dependency_overrides[getAppSettings] = overrideSettings
    app.dependency_overrides[getRagService] = overrideRagService

    yield TestClient(app)

    app.dependency_overrides.clear()
    dependencies.getRagService.cache_clear()


def testIngestRetrieveAndGenerate(client: TestClient) -> None:
    payload = "This guideline covers Type 2 diabetes management with emphasis on lifestyle."
    headers = {"X-API-Key": "test-key"}

    ingestResponse = client.post(
        "/ingest",
        headers=headers,
        files={"file": ("guideline.txt", payload, "text/plain")},
    )

    assert ingestResponse.status_code == 200
    documentId = ingestResponse.json()["documentId"]
    assert documentId == 1

    retrieveResponse = client.post(
        "/retrieve",
        headers=headers,
        json={"query": "Type 2 diabetes recommendations", "topK": 3},
    )

    assert retrieveResponse.status_code == 200
    body = retrieveResponse.json()
    assert body["queryLanguage"] == "en"
    assert body["matches"]
    assert body["matches"][0]["documentId"] == documentId

    generateResponse = client.post(
        "/generate",
        headers=headers,
        json={"query": "Type 2 diabetes recommendations", "topK": 3},
    )
    assert generateResponse.status_code == 200
    generation = generateResponse.json()
    assert generation["queryLanguage"] == "en"
    assert generation["outputLanguage"] == "en"
    assert generation["sources"]
    assert "Type 2 diabetes" in generation["response"]