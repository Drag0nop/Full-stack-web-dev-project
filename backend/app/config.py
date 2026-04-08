from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Autonomous Codebase Documenter"
    api_prefix: str = "/api"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./documentor.db"
    gemini_api_key: str | None = None
    max_upload_size_mb: int = 50
    model_config = SettingsConfigDict(env_file=(".config", ".env"), env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
