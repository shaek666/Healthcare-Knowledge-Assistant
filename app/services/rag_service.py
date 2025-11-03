"""High-level service orchestrating ingestion, retrieval, and generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
from app.config import Settings, get_settings
from app.models import DocumentMatch, SourceDocument
from app.services.document_store import DocumentRecord, DocumentStore
from app.services.embedding import embed_text
from app.services.language_detection import detect_language
from app.services.translation import TranslationService
from app.services.vector_store import FaissVectorStore


@dataclass
class RetrievalResult:
    """Container holding retrieval metadata."""

    query_language: str
    matches: List[DocumentMatch]


@dataclass
class GenerationResult:
    """Container for generation output."""

    query_language: str
    output_language: str
    response: str
    sources: List[SourceDocument]


class RAGService:
    """Coordinate the RAG pipeline components."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        data_dir = self.settings.data_dir

        self.document_store = DocumentStore(data_dir / "documents.json")
        self.vector_store = FaissVectorStore(data_dir / "index.faiss")
        self.translation_service = TranslationService(self.settings)

    def ingest(self, filename: str, content: str) -> DocumentRecord:
        """Detect language, embed, and persist the document."""

        language = detect_language(content)
        record = self.document_store.add_document(filename=filename, language=language, content=content)

        embedding = embed_text(content)
        self.vector_store.add(ids=np.array([record.id], dtype="int64"), vectors=np.array([embedding], dtype="float32"))

        return record

    def retrieve(self, query: str, top_k: int) -> RetrievalResult:
        """Return vector search results for the provided query."""

        query_language = detect_language(query)
        query_embedding = embed_text(query)
        results = self.vector_store.search(query_embedding, top_k)

        matches: List[DocumentMatch] = []
        for doc_id, score in results:
            record = self.document_store.get_document(doc_id)
            if record is None:
                continue
            matches.append(
                DocumentMatch(
                    document_id=record.id,
                    language=record.language,
                    score=_cosine_to_unit(score),
                    content=record.content,
                    filename=record.filename,
                )
            )

        return RetrievalResult(query_language=query_language, matches=matches)

    def generate(self, query: str, top_k: int, output_language: str | None = None) -> GenerationResult:
        """Produce a mock LLM response grounded on retrieved documents."""

        retrieval = self.retrieve(query, top_k)
        query_language = retrieval.query_language
        target_language = output_language or query_language

        if not retrieval.matches:
            base_response = (
                "No relevant documents were found for your request. "
                "Please ingest guidelines or research summaries before querying the assistant."
            )
            generated = self._translate_if_needed(base_response, source_language="en", target_language=target_language)
            return GenerationResult(
                query_language=query_language,
                output_language=target_language,
                response=generated,
                sources=[],
            )

        base_response = self._compose_response(query, retrieval.matches)
        generated = self._translate_if_needed(
            base_response,
            source_language="en",
            target_language=target_language,
        )

        sources = [
            SourceDocument(
                document_id=match.document_id,
                language=match.language,
                score=match.score,
                content_preview=_preview(match.content),
                filename=match.filename,
            )
            for match in retrieval.matches
        ]

        return GenerationResult(
            query_language=query_language,
            output_language=target_language,
            response=generated,
            sources=sources,
        )

    def _compose_response(self, query: str, matches: List[DocumentMatch]) -> str:
        bullet_points = []
        for idx, match in enumerate(matches, start=1):
            snippet = _preview(match.content, limit=320).replace("\n", " ")
            bullet_points.append(f"{idx}. {snippet}")

        bullet_text = "\n".join(f"- {point}" for point in bullet_points)
        response = (
            f"Query: {query}\n\n"
            "Key supporting evidence from retrieved documents:\n"
            f"{bullet_text}\n\n"
            "This is a heuristic synthesis. Please verify against the source guidelines before clinical use."
        )
        return response

    def _translate_if_needed(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == target_language:
            return text
        return self.translation_service.translate(text, source_language=source_language, target_language=target_language)


def _cosine_to_unit(value: float) -> float:
    """Convert cosine similarity (-1..1) to 0..1 for readability."""

    clipped = max(min(value, 1.0), -1.0)
    return (clipped + 1.0) / 2.0


def _preview(text: str, limit: int = 200) -> str:
    snippet = text.strip()
    if len(snippet) <= limit:
        return snippet
    return snippet[:limit].rstrip() + "..."
