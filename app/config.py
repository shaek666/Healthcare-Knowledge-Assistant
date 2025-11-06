from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    apiKey: str = "dev-local-key"
    dataDir: Path = Path("data")
    embeddingModelName: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

setattr(Settings, "model_config", SettingsConfigDict(env_file=".env", env_prefix="HKA_", env_file_encoding="utf-8"))

@lru_cache(maxsize=1)
def getSettings() -> Settings:
    settings = Settings()
    settings.dataDir.mkdir(parents=True, exist_ok=True)
    return settings