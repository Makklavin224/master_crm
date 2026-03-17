from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env from project root (parent of backend/)
_env_file = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_file) if _env_file.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    debug: bool = False
    app_name: str = "Master CRM"

    # Database (owner role -- used by Alembic for migrations)
    database_url: str  # postgresql+asyncpg://mastercrm_owner:password@db:5432/mastercrm

    # Database (app role -- used by FastAPI at runtime for RLS enforcement)
    database_app_url: str  # postgresql+asyncpg://app_user:password@db:5432/mastercrm

    db_echo: bool = False

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Telegram
    tg_bot_token: str = ""
    tg_webhook_secret: str = ""
    mini_app_url: str = ""
    base_webhook_url: str = ""

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
