"""Pydantic request and response models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    """Response returned after document ingestion."""

    document_id: int = Field(..., description="Numeric identifier assigned to the stored document.")
    filename: str = Field(..., description="Original uploaded filename.")
    language: str = Field(..., description="Detected ISO language code (en or ja).")
    characters: int = Field(..., description="Document character count.")
    ingested_at: datetime = Field(..., description="Timestamp when the document was stored.")


class RetrieveRequest(BaseModel):
    """Request payload for /retrieve."""

    query: str = Field(..., description="Search query in English or Japanese.")
    top_k: int = Field(3, ge=1, le=10, description="Number of matches to return.")


class DocumentMatch(BaseModel):
    """Single vector search match."""

    document_id: int = Field(..., description="Identifier of the source document.")
    language: str = Field(..., description="Stored language code.")
    score: float = Field(..., description="Cosine similarity score between 0 and 1.")
    content: str = Field(..., description="Relevant textual content.")
    filename: Optional[str] = Field(None, description="Original filename, if available.")


class RetrieveResponse(BaseModel):
    """Response payload for /retrieve."""

    query_language: str = Field(..., description="Detected ISO language code for the query.")
    matches: List[DocumentMatch] = Field(default_factory=list, description="Ranked results.")


class GenerateRequest(BaseModel):
    """Request payload for /generate."""

    query: str = Field(..., description="Prompt in English or Japanese.")
    top_k: int = Field(3, ge=1, le=10, description="Number of documents to ground the response.")
    output_language: Optional[str] = Field(
        None,
        description="Desired output language code (en or ja). Defaults to detected query language.",
    )


class SourceDocument(BaseModel):
    """Metadata about a document used for generation."""

    document_id: int
    language: str
    score: float
    content_preview: str
    filename: Optional[str] = None


class GenerateResponse(BaseModel):
    """Response payload for /generate."""

    query_language: str
    output_language: str
    response: str
    sources: List[SourceDocument]

