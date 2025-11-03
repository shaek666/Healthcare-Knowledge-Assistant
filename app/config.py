"""Application configuration and dependency helpers."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings."""

    api_key: str = "dev-local-key"
    data_dir: Path = Path("data")
    embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    translation_model_en_to_ja: str = "Helsinki-NLP/opus-mt-en-jap"
    translation_model_ja_to_en: str = "Helsinki-NLP/opus-mt-ja-en"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="HKA_", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings

