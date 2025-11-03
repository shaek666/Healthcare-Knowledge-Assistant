# Healthcare Knowledge Assistant

FastAPI backend for a bilingual (English/Japanese) healthcare retrieval-augmented generation assistant. The service ingests medical guidelines, indexes them with FAISS, secures endpoints with API keys, and returns mock grounded responses.

## Prerequisites
- Python 3.13.9 (required)
- Windows PowerShell or another shell
- Recommended: virtual environment named `.venv`

## Local Setup
1. Create the virtual environment and install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Define your API key (set an environment variable or add it to `.env`):
   ```powershell
   setx HKA_API_KEY "your-secret-key"
   ```
3. Run the API:
   ```powershell
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## API Endpoints
All endpoints require the header `X-API-Key` matching `HKA_API_KEY`.

- `POST /ingest` – upload `.txt` documents (English or Japanese). The service detects language, embeds text, and stores vectors in FAISS.
- `POST /retrieve` – run a multilingual semantic search that returns the top matches with cosine similarity scores.
- `POST /generate` – synthesise a mock LLM response using retrieved passages. Optional `output_language` (`"en"` or `"ja"`) controls translation.

## Testing
```powershell
.\.venv\Scripts\python.exe -m pytest
```
Tests use dependency overrides to avoid large model downloads and keep execution fast.

## Docker
Build and run the containerised API (Python 3.13.9 slim image):
```powershell
docker build -t healthcare-knowledge-assistant .
docker run -e HKA_API_KEY=your-secret-key -p 8000:8000 healthcare-knowledge-assistant
```
Persistent FAISS index files are created under `/app/data`; mount a volume if you need to retain state between runs.

## CI/CD
`.github/workflows/ci.yml` sets up GitHub Actions to install dependencies, execute the pytest suite, and build the Docker image on every push or pull request targeting `main`.

## Design Notes
Scalability comes from keeping the serving layer stateless: document metadata and FAISS artifacts live under `data/`, making it straightforward to replicate via shared storage or object buckets. The service layer wraps embeddings, storage, and translation behind cohesive classes so you can swap them for managed offerings (e.g., external vector databases, production translators) without touching the FastAPI routes. For higher throughput, embeddings and FAISS writes can be offloaded to background workers or batched queues while the API stays responsive.

Modularity and future improvements were prioritised. The rule-based translator demonstrates the interface wiring but can be replaced with a production-ready model that speaks both directions; tests already isolate the component. Similarly, the persistence layer currently uses JSON plus FAISS on disk. Replacing this with PostgreSQL + pgvector or a managed Pinecone index only requires updating `DocumentStore` and `FaissVectorStore`. Adding streaming responses or auditable logging hooks can happen inside `RAGService` without breaking the REST contract.

## Project Layout
- `app/` – FastAPI app, configuration, and services.
- `data/` – runtime state (FAISS index, document metadata).
- `tests/` – pytest suite with dependency overrides.
- `Dockerfile` – container definition.
- `.github/workflows/ci.yml` – CI pipeline.

