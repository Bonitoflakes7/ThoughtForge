from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ThoughtForge API"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./thoughtforge.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "development-only-secret"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
