from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class IngestResponse(BaseModel):
    documentId: int = Field(...)
    filename: str = Field(...)
    language: str = Field(...)
    characters: int = Field(...)
    ingestedAt: datetime = Field(...)

class RetrieveRequest(BaseModel):
    query: str = Field(...)
    topK: int = Field(3, ge=1, le=10)

class DocumentMatch(BaseModel):
    documentId: int = Field(...)
    language: str = Field(...)
    score: float = Field(...)
    content: str = Field(...)
    filename: Optional[str] = Field(default=None)

class RetrieveResponse(BaseModel):
    queryLanguage: str = Field(...)
    matches: List[DocumentMatch] = Field(default_factory=list)

class GenerateRequest(BaseModel):
    query: str = Field(...)
    topK: int = Field(3, ge=1, le=10)
    outputLanguage: Optional[str] = Field(default=None)

class SourceDocument(BaseModel):
    documentId: int
    language: str
    score: float
    contentPreview: str
    filename: Optional[str] = None

class GenerateResponse(BaseModel):
    queryLanguage: str
    outputLanguage: str
    response: str
    sources: List[SourceDocument]