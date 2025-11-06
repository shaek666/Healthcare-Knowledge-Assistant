# Healthcare Knowledge Assistant

This repository contains the solution for the Acme AI Sr. LLM / Backend Engineer assignment. It ships a FastAPI backend that can ingest English and Japanese guideline documents, store embeddings in FAISS, and serve retrieval-augmented responses. Every endpoint expects an `X-API-Key` header so the service stays locked down.

## What you need
- Python 3.13.9
- Docker Desktop with the `docker` CLI

## Quick start with Docker (Windows PowerShell)
1. Clone the repository and switch into the project folder:
   ```powershell
   git clone https://github.com/shaek666/Healthcare-Knowledge-Assistant.git
   Set-Location Healthcare-Knowledge-Assistant
   ```
2. Pick an API key and export it before running the container:
   ```powershell
   $env:HKA_API_KEY = "your-secret-key"
   ```
3. Build the image. Dependencies are handled inside the Docker build, so no virtualenv is necessary:
   ```powershell
   docker build -t healthcare-knowledge-assistant .
   ```
4. Launch the backend:
   ```powershell
   docker run -e HKA_API_KEY=$env:HKA_API_KEY -p 8000:8000 healthcare-knowledge-assistant
   ```
   FAISS artifacts land in `/app/data`. Mount a volume if you want those vectors to survive container restarts:
   ```powershell
   docker run -e HKA_API_KEY=$env:HKA_API_KEY -p 8000:8000 -v "${PWD}/data:/app/data" healthcare-knowledge-assistant
   ```

### Pulling the published image
Skip the local build by pulling the image that CI publishes:
```powershell
echo "your-ghcr-token" | docker login ghcr.io -u <ghcr-username> --password-stdin
docker pull ghcr.io/shaek666/healthcare-knowledge-assistant:latest
```
> **Why torch CPU wheels?** The pinned first two lines of `requirements.txt` pull PyTorch from the official CPU wheel index. This keeps installs lightweight and avoids the multi-gigabyte CUDA dependency chain during CI builds and Docker image creation.

## API guide
All requests must send `X-API-Key: <your-secret-key>`.

| Endpoint | Method | Description |
| --- | --- | --- |
| `/ingest` | POST (multipart) | Accepts `.txt` files (English or Japanese). Detects language, creates embeddings, and stores metadata plus vectors. |
| `/retrieve` | POST (JSON) | Processes a free-form query and returns top matches with cosine similarity scores and raw snippets. |
| `/generate` | POST (JSON) | Produces a mock summary grounded in retrieved passages. Add `outputLanguage` (`"en"` or `"ja"`) to control the response language. |

Uploads are decoded with UTF-8 plus a couple of Japanese fallbacks, and responses echo the detected language so you can verify what the system saw.

## Running the tests
The integration suite touches all three endpoints. Run it inside a container to ensure parity with CI:
```powershell
docker run --rm ghcr.io/shaek666/healthcare-knowledge-assistant:latest python -m pytest
```
`tests/API_test.py` swaps in lightweight fakes for embeddings and translation, so the test run is quick.

## CI/CD process
`.github/workflows/ci.yml` triggers on every push or PR to `main`. The workflow installs dependencies, runs pytest, builds the Docker image, and pushes it to GitHub Container Registry using the `GHCR_USERNAME` and `GHCR_TOKEN` secrets.

## Design notes
**Scalability.** The serving layer is stateless so a single container can handle traffic bursts without coordination. FAISS indexes, metadata, and uploads get saved in `data/`, which makes it easy to swap persistent storage (S3, blob volumes, or a managed vector database). Simple locks guard long-running work like embedding generation, and the footprint stays small because the CPU-only torch wheel avoids GPU bloat, which is a big advantage in my opinion. This setup keeps the pipeline fast for local tests but still maps cleanly to cloud deployments.

**Modularity.** I tried to keep the whole code base as lightweight and bloat free as possible. For this version, v0.1.0-alpha, Key behaviors lies inside `app/services/`. `translation.py` handles bilingual translations, `documentStorage.py` deals with metadata, and `vectorStorage.py` holds FAISS persistence. Swapping anything, such as replacing the translation module with a production model or plugging in an external vector store, only touches that module. FastAPI routers stay light-weight and simply delegate to the service layer, which keeps the codebase easy to maintain.

**Future improvements.** Upcoming iterations will add PDF and DOCX ingestion by dropping a text extraction layer ahead of embeddings. They could also chunk large documents before embedding so guideline docs stay manageable. Background workers (Celery or simple RQ) would make ingestion run asynchronously while the API stays responsive. Additional items such as auditable response logs, rate limiting, and a real translation bridge for Japanese-to-English could be implemented. These additions would make the backend a realistic foundation for clinical knowledge assistants.

## Project map
```
Healthcare-Knowledge-Assistant/
|-- .github/
|   |-- workflows/
|   |   `-- ci.yml
|-- app/
|   |-- __init__.py
|   |-- config.py
|   |-- dependencies.py
|   |-- main.py
|   `-- services/
|       |-- documentStorage.py
|       |-- embeddings.py
|       |-- languageDetection.py
|       |-- ragService.py
|       |-- translation.py
|       `-- vectorStorage.py
|-- data/
|   `-- (runtime index files created at runtime)
|-- tests/
|   `-- API_test.py
|-- .dockerignore
|-- .gitignore
|-- Dockerfile
`-- requirements.txt
```