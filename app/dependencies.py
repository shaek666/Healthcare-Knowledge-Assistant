from functools import lru_cache
from app.config import Settings, getSettings
from app.services.ragService import RAGService

@lru_cache(maxsize=1)
def getRagService() -> RAGService:
    settings = getSettings()
    return RAGService(settings)

def getAppSettings() -> Settings:
    return getSettings()