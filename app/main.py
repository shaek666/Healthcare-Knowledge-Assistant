from datetime import datetime
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from app.config import Settings
from app.dependencies import getAppSettings, getRagService
from app.models import GenerateRequest, GenerateResponse, IngestResponse, RetrieveRequest, RetrieveResponse
from app.services.ragService import RAGService

app = FastAPI(
    title="Healthcare Knowledge Assistant",
    version="0.1.0",
    description="RAG-powered bilingual assistant for clinicians.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

apiKeyScheme = APIKeyHeader(name="X-API-Key", auto_error=False)

def verifyApiKey(
    apiKey: str | None = Depends(apiKeyScheme), settings: Settings = Depends(getAppSettings)
) -> str:
    if apiKey is None or apiKey != settings.apiKey:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key.")
    return apiKey

@app.post("/ingest", response_model=IngestResponse, summary="Ingest a medical document.")
async def ingestDocument(
    file: UploadFile = File(...),
    _: str = Depends(verifyApiKey),
    service: RAGService = Depends(getRagService),
) -> IngestResponse:
    filename = file.filename or "uploaded.txt"
    if Path(filename).suffix.lower() != ".txt":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .txt documents are supported.")
    rawContent = await file.read()
    textContent = decodeText(rawContent)
    if not textContent.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded document is empty.")
    record = service.ingestDocument(filename=filename, content=textContent)
    return IngestResponse(
        documentId=record.id,
        filename=record.filename,
        language=record.language,
        characters=len(textContent),
        ingestedAt=datetime.fromisoformat(record.ingestedAt),
    )

@app.post("/retrieve", response_model=RetrieveResponse, summary="Retrieve relevant documents.")
async def retrieveDocuments(
    payload: RetrieveRequest,
    _: str = Depends(verifyApiKey),
    service: RAGService = Depends(getRagService),
) -> RetrieveResponse:
    result = service.retrieveMatches(query=payload.query, topK=payload.topK)
    return RetrieveResponse(queryLanguage=result.queryLanguage, matches=result.matches)

@app.post("/generate", response_model=GenerateResponse, summary="Generate a grounded response.")
async def generateResponse(
    payload: GenerateRequest,
    _: str = Depends(verifyApiKey),
    service: RAGService = Depends(getRagService),
) -> GenerateResponse:
    generation = service.generateResponse(query=payload.query, topK=payload.topK, outputLanguage=payload.outputLanguage)
    return GenerateResponse(
        queryLanguage=generation.queryLanguage,
        outputLanguage=generation.outputLanguage,
        response=generation.response,
        sources=generation.sources,
    )

def decodeText(raw: bytes) -> str:
    if not raw:
        return ""
    encodingCandidates = ("utf-8", "utf-8-sig", "shift_jis", "cp932")
    for encodingName in encodingCandidates:
        decodedText = raw.decode(encodingName, errors="ignore")
        reEncodedText = decodedText.encode(encodingName, errors="ignore")
        if len(reEncodedText) == len(raw):
            return decodedText
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unable to decode file with supported encodings: {', '.join(encodingCandidates)}.",
    )