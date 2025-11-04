# Healthcare Knowledge Assistant

Backend service for the Acme AI Sr. LLM assignment. The app ingests English or Japanese clinical guidance, stores sentence embeddings in FAISS, and serves retrieval plus bilingual mock generation over FastAPI. Every endpoint is protected with an `X-API-Key` header.

## Prerequisites
- Python 3.13.9
- Git and PowerShell (or another terminal)
- Docker Desktop (optional, for container runs)

## Local Development
1. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Provide an API key (environment variable or `.env` file):
   ```powershell
   setx HKA_API_KEY "your-secret-key"
   ```
4. Start the server:
   ```powershell
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## API Overview
Every request must include `X-API-Key: <your-secret-key>`.

| Endpoint | Method | Description |
| --- | --- | --- |
| `/ingest` | POST (multipart) | Accepts `.txt` documents. Detects language (`en` or `ja`), embeds the text with Sentence Transformers, and writes to FAISS plus JSON metadata. |
| `/retrieve` | POST (JSON) | Accepts a query in English or Japanese. Returns the top matches with cosine similarity scores and raw content. |
| `/generate` | POST (JSON) | Combines the query with retrieved passages to produce a mock LLM answer. Supports optional `outputLanguage` (`"en"` or `"ja"`) for translation. |

Uploaded documents are decoded with UTF-8 or common Japanese encodings. Responses include detected language, similarity scores, and document identifiers for traceability.

## Testing
Run the integration test suite:
```powershell
python -m pytest
```
`tests/API_test.py` uses dependency overrides to avoid large model downloads while exercising ingest, retrieval, and generation.

## Docker Usage
Build and run locally:
```powershell
docker build -t healthcare-knowledge-assistant .
docker run -e HKA_API_KEY=your-secret-key -p 8000:8000 healthcare-knowledge-assistant
```
The server writes FAISS artifacts to `/app/data`. Mount a volume if you need persistence between container runs:
```powershell
docker run -e HKA_API_KEY=your-secret-key -p 8000:8000 -v ${PWD}/data:/app/data healthcare-knowledge-assistant
```

### GitHub Container Registry
Images are published automatically to `ghcr.io/shaek666/healthcare-knowledge-assistant:latest`. Pull after a successful workflow run:
```powershell
docker login ghcr.io -u <ghcr-username>
docker pull ghcr.io/shaek666/healthcare-knowledge-assistant:latest
```
> **Why torch CPU wheels?** The pinned first two lines of `requirements.txt` pull PyTorch from the official CPU wheel index. This keeps installs lightweight and avoids the multi-gigabyte CUDA dependency chain during CI builds and Docker image creation.

## CI/CD
`.github/workflows/ci.yml` runs on every push and pull request to `main`:
1. Install dependencies.
2. Execute `pytest`.
3. Build the Docker image.
4. Log in to GitHub Container Registry and push the tagged image.

## Design Notes
**Scalability.** The FastAPI layer remains stateless; document text and FAISS index files sit under `data/`. In production, that directory can be replaced with shared storage or an external vector database without altering the API surface. Sentence embedding is memoised to avoid repeated model loads, and FAISS operations are guarded with locks to keep concurrent ingest safe.

**Modularity.** Services are separated by responsibility (`documentStorage`, `vectorStorage`, `ragService`, `translation`). Swapping components is straightforward: for example, replacing the rule-based translator with a managed service or upgrading persistence to PostgreSQL plus pgvector only requires editing the relevant service module.

**Future improvements.** Chunk large documents before embedding, add background workers for heavy ingestion, and integrate a real translation model when deployment constraints allow. Additional safeguards such as audit logging, rate limiting, or redaction filters can plug into the service layer without changing the public endpoints.

## Project Layout
```
Healthcare-Knowledge-Assistant/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── dependencies.py
│   ├── main.py
│   └── services/
│       ├── documentStorage.py
│       ├── embeddings.py
│       ├── languageDetection.py
│       ├── ragService.py
│       ├── translation.py
│       └── vectorStorage.py
├── data/
│   └── (runtime index files created at runtime)
├── tests/
│   └── API_test.py
├── .dockerignore
├── .gitignore
├── Dockerfile
└── requirements.txt
```
