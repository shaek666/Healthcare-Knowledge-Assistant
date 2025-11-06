from functools import lru_cache
from os import getenv
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="HKA_",
        env_file_encoding="utf-8",
    )

    apiKey: str = Field(default_factory=lambda: getenv("HKA_API_KEY", "dev-local-key"))
    dataDir: Path = Path("data")
    embeddingModelName: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

@lru_cache(maxsize=1)
def getSettings() -> Settings:
    settings = Settings()
    settings.dataDir.mkdir(parents=True, exist_ok=True)
    return settings