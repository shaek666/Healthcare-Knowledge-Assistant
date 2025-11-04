from dataclasses import dataclass
from typing import List
import numpy as np
from app.config import Settings, getSettings
from app.models import DocumentMatch, SourceDocument
from app.services.documentStorage import DocumentRecord, DocumentStore
from app.services.embeddings import embedText
from app.services.languageDetection import detectLanguage
from app.services.translation import TranslationService
from app.services.vectorStorage import FaissVectorStore

@dataclass
class RetrievalResult:
    queryLanguage: str
    matches: List[DocumentMatch]

@dataclass
class GenerationResult:
    queryLanguage: str
    outputLanguage: str
    response: str
    sources: List[SourceDocument]

class RAGService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or getSettings()
        dataDirectory = self.settings.dataDir
        self.documentStore = DocumentStore(dataDirectory / "documents.json")
        self.vectorStore = FaissVectorStore(dataDirectory / "index.faiss")
        self.translationService = TranslationService(self.settings)

    def ingestDocument(self, filename: str, content: str) -> DocumentRecord:
        languageCode = detectLanguage(content)
        record = self.documentStore.addDocument(filename=filename, language=languageCode, content=content)
        embeddingVector = embedText(content)
        self.vectorStore.add(ids=np.array([record.id], dtype="int64"), vectors=np.array([embeddingVector], dtype="float32"))
        return record

    def retrieveMatches(self, query: str, topK: int) -> RetrievalResult:
        queryLanguage = detectLanguage(query)
        queryEmbedding = embedText(query)
        results = self.vectorStore.search(queryEmbedding, topK)
        matches: List[DocumentMatch] = []
        for documentId, scoreValue in results:
            record = self.documentStore.getDocument(documentId)
            if record is None:
                continue
            matches.append(
                DocumentMatch(
                    documentId=record.id,
                    language=record.language,
                    score=convertCosineToUnit(scoreValue),
                    content=record.content,
                    filename=record.filename,
                )
            )
        return RetrievalResult(queryLanguage=queryLanguage, matches=matches)

    def generateResponse(self, query: str, topK: int, outputLanguage: str | None = None) -> GenerationResult:
        retrievalResult = self.retrieveMatches(query, topK)
        queryLanguage = retrievalResult.queryLanguage
        targetLanguage = outputLanguage or queryLanguage
        if not retrievalResult.matches:
            baseResponse = (
                "No relevant documents were found for your request. "
                "Please ingest guidelines or research summaries before querying the assistant."
            )
            generatedText = self.applyTranslationIfNeeded(baseResponse, sourceLanguage="en", targetLanguage=targetLanguage)
            return GenerationResult(
                queryLanguage=queryLanguage,
                outputLanguage=targetLanguage,
                response=generatedText,
                sources=[],
            )

        baseResponse = self.composeResponse(query, retrievalResult.matches)
        generatedText = self.applyTranslationIfNeeded(
            baseResponse,
            sourceLanguage="en",
            targetLanguage=targetLanguage,
        )

        sources = [
            SourceDocument(
                documentId=match.documentId,
                language=match.language,
                score=match.score,
                contentPreview=buildPreview(match.content),
                filename=match.filename,
            )
            for match in retrievalResult.matches
        ]

        return GenerationResult(
            queryLanguage=queryLanguage,
            outputLanguage=targetLanguage,
            response=generatedText,
            sources=sources,
        )

    def composeResponse(self, query: str, matches: List[DocumentMatch]) -> str:
        bulletPoints = []
        for indexValue, match in enumerate(matches, start=1):
            snippet = buildPreview(match.content, limitValue=320).replace("\n", " ")
            bulletPoints.append(f"{indexValue}. {snippet}")

        bulletText = "\n".join(f"- {point}" for point in bulletPoints)
        responseText = (
            f"Query: {query}\n\n"
            "Key supporting evidence from retrieved documents:\n"
            f"{bulletText}\n\n"
            "This is a heuristic synthesis. Please verify against the source guidelines before clinical use."
        )
        return responseText

    def applyTranslationIfNeeded(self, text: str, sourceLanguage: str, targetLanguage: str) -> str:
        if sourceLanguage == targetLanguage:
            return text
        return self.translationService.translate(text, sourceLanguage=sourceLanguage, targetLanguage=targetLanguage)

def convertCosineToUnit(value: float) -> float:
    clippedValue = max(min(value, 1.0), -1.0)
    return (clippedValue + 1.0) / 2.0

def buildPreview(text: str, limitValue: int = 200) -> str:
    snippet = text.strip()
    if len(snippet) <= limitValue:
        return snippet
    return snippet[:limitValue].rstrip() + "..."