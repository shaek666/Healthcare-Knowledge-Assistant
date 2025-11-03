"""FastAPI dependency wiring helpers."""

from functools import lru_cache

from app.config import Settings, get_settings
from app.services.rag_service import RAGService


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    """Return singleton RAG service instance."""

    settings = get_settings()
    return RAGService(settings)


def get_app_settings() -> Settings:
    """Expose settings as a dependency."""

    return get_settings()

