"""FastAPI application entry point."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from app.config import Settings
from app.dependencies import get_app_settings, get_rag_service
from app.models import GenerateRequest, GenerateResponse, IngestResponse, RetrieveRequest, RetrieveResponse
from app.services.rag_service import RAGService

app = FastAPI(
    title="Healthcare Knowledge Assistant",
    version="0.1.0",
    description="RAG-powered bilingual assistant for clinicians.",
)

# Basic CORS to simplify local integration; tighten in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(
    api_key: str | None = Depends(api_key_scheme), settings: Settings = Depends(get_app_settings)
) -> str:
    if api_key is None or api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key.")
    return api_key


@app.post("/ingest", response_model=IngestResponse, summary="Ingest a medical document.")
async def ingest_document(
    file: UploadFile = File(...),
    _: str = Depends(verify_api_key),
    service: RAGService = Depends(get_rag_service),
) -> IngestResponse:
    filename = file.filename or "uploaded.txt"
    if Path(filename).suffix.lower() != ".txt":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .txt documents are supported.")

    raw_content = await file.read()
    text = _decode_text(raw_content)
    if not text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded document is empty.")

    record = service.ingest(filename=filename, content=text)

    return IngestResponse(
        document_id=record.id,
        filename=record.filename,
        language=record.language,
        characters=len(text),
        ingested_at=datetime.fromisoformat(record.ingested_at),
    )


@app.post("/retrieve", response_model=RetrieveResponse, summary="Retrieve relevant documents.")
async def retrieve_documents(
    payload: RetrieveRequest,
    _: str = Depends(verify_api_key),
    service: RAGService = Depends(get_rag_service),
) -> RetrieveResponse:
    result = service.retrieve(query=payload.query, top_k=payload.top_k)
    return RetrieveResponse(query_language=result.query_language, matches=result.matches)


@app.post("/generate", response_model=GenerateResponse, summary="Generate a grounded response.")
async def generate_response(
    payload: GenerateRequest,
    _: str = Depends(verify_api_key),
    service: RAGService = Depends(get_rag_service),
) -> GenerateResponse:
    generation = service.generate(query=payload.query, top_k=payload.top_k, output_language=payload.output_language)
    return GenerateResponse(
        query_language=generation.query_language,
        output_language=generation.output_language,
        response=generation.response,
        sources=generation.sources,
    )


def _decode_text(raw: bytes) -> str:
    """Attempt to decode uploaded bytes into text."""

    if not raw:
        return ""

    candidates = ("utf-8", "utf-8-sig", "shift_jis", "cp932")
    for encoding in candidates:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unable to decode file with supported encodings: {', '.join(candidates)}.",
    )
