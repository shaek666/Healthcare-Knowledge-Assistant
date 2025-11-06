from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="HKA_",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )

    apiKey: str = Field(default="dev-local-key", alias="API_KEY")
    dataDir: Path = Path("data")
    embeddingModelName: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

@lru_cache(maxsize=1)
def getSettings() -> Settings:
    settings = Settings()
    settings.dataDir.mkdir(parents=True, exist_ok=True)
    return settings
